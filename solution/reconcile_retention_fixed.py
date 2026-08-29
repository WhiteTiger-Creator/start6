#!/usr/bin/env python3
"""Backup / storage retention reconciler (governance dialect).

Replays a snapshot-creation event stream and applies the storage governance
board's tiered grandfather-father-son (GFS) RETENTION policy, emitting per
snapshot keep/prune/defer decisions and the final retention state per repo.

Every retention rule here -- the governance calendar (day/week/month/year
boundary conventions), the per-bucket representative selection, the per-tier
caps, the pinned-hold exemption, the cross-tier promotion overlap, the stateful
per-repo quota ledger and the prune ordering / per-repo prune cap -- is the
governance board's own dialect and deliberately DEVIATES from a standard,
age-based GFS ("keep the last N per period"). It is reconstructed from
/app/incident/retention_governance_log.md, the operational data, and
/app/docs/report_spec.json (output contract only).

Standard-library only, integer epoch-second calendar math done by hand. There
is deliberately NO date library and NO dataframe engine: pandas/numpy or a date
oracle (dateutil/arrow/pendulum, even datetime/calendar) would either be a wrong
calendar dialect or an unnecessary delegation, and are rejected by the verifier.
"""

from __future__ import annotations

import argparse
import bisect
import json
from pathlib import Path

# Fixed absolute operational-input paths. --input selects the snapshot stream
# only; the scoped policy and pin-registry files never become relative to it.
DEFAULT_INPUT = "/app/data/snapshots.json"
DEFAULT_OUTPUT_DIR = "/app/output"
POLICY_PATH = "/app/data/retention_policy.json"
PIN_REGISTRY_PATH = "/app/data/pin_registry.json"

SCHEMA_VERSION = "retention-gfs-v1"
TIER_ORDER = ["daily", "weekly", "monthly", "yearly"]
DECISION_ORDER = ["keep", "prune", "defer"]

# --- Governance calendar constants (final decisions; see log in comments) ---
SECONDS_PER_DAY = 86400     # fixed
DAY_CUT = 14400             # #RET-7104: retention day rolls at 04:00 (not midnight)
WEEK_PHASE = 3              # #RET-7182 (restoring #RET-7104): week starts Sunday, not ISO Monday
MONTH_LEN = 30             # #RET-7104: fixed 30-day retention month (not calendar month)
YEAR_LEN = 360            # #RET-7104: fixed 360-day retention year (not 365/366)

# --- Ledger constants (final decisions) ---
RESET_GAP = 2592000         # #RET-7116: quota resets when idle gap exceeds 30 days
DECAY_DIV = 86400           # #RET-7160: idle-gap decay divisor, CEIL
QUOTA_QUANTUM = 1048576     # #RET-7162: bytes per quota unit (MiB), size_mb = CEIL

# Baseline retention policy (#RET-7150). Any field the policy file omits keeps
# these values; the policy file may override per default and per repo.
POLICY_FIELDS = (
    "protection_days",
    "cap_daily",
    "cap_weekly",
    "cap_monthly",
    "cap_yearly",
    "quota_cap",
    "prune_cap",
)
POLICY_BASELINE = {
    "protection_days": 21,
    "cap_daily": 7,
    "cap_weekly": 4,
    "cap_monthly": 6,
    "cap_yearly": 2,
    "quota_cap": 100000,
    "prune_cap": 300,
}

RECOGNIZED_HOLDS = ("compliance", "legal", "manual")  # #RET-7124


def _ceil_div(numer: int, denom: int) -> int:
    """Integer ceil for non-negative numer; ceil(x/n) == -(-x // n)."""
    return -(-numer // denom)


def canon_name(value: object) -> str:
    text = str(value).strip().lower()
    return text if text else "unassigned"


def collapse_ws(value: object) -> str:
    return " ".join(str(value).split())


def coerce_int(value: object) -> int:
    if isinstance(value, bool):
        # The contract's chain has no boolean case, and running a bool through it
        # fails twice: int("True") raises and int(float("True")) raises, so the
        # documented answer is 0. Returning int(value) here gave 1 instead, which
        # is the one place the reference disagreed with report_spec.json.
        return 0
    if isinstance(value, int):
        return value
    text = str(value).strip()
    try:
        return int(text)
    except ValueError:
        try:
            return int(float(text))
        except (ValueError, OverflowError):
            # "on failure 0" covers both ways the second conversion fails: "n/a"
            # raises ValueError, while "1e999" parses as inf and raises Overflow.
            return 0


def coerce_flag(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "pinned"}
    return bool(value)


# --------------------------------------------------------------------------
# Stage 1-2: canonicalize + deduplicate by snapshot_id (#RET-7101, #RET-7102/#RET-7142)
# --------------------------------------------------------------------------
def canonicalize(raw_rows: list[dict]) -> list[dict]:
    canon = []
    for row in raw_rows:
        canon.append(
            {
                # #RET-7101 lists coercions for repo, vault, note, size_bytes, ts and
                # pinned, and pointedly not for snapshot_id, which report_spec.json
                # carries as a plain string. Collapsing it here would have merged two
                # contract-valid ids that differ only in their spacing.
                "snapshot_id": str(row.get("snapshot_id", "")),
                "repo": canon_name(row.get("repo", "")),
                "vault": canon_name(row.get("vault", row.get("tier", ""))),
                "ts": coerce_int(row.get("ts", 0)),
                "size_bytes": coerce_int(row.get("size_bytes", 0)),
                "pinned": coerce_flag(row.get("pinned", False)),
                "note": collapse_ws(row.get("note", "")),
            }
        )
    return canon


def deduplicate(canon_rows: list[dict]) -> list[dict]:
    # #RET-7102 chain, with the #RET-7142 reversal on the size tie-break:
    # keep the HIGHEST ts; on a ts tie keep the LOWER size_bytes; then longer
    # note; then lexicographically larger repo; then first-seen input order.
    best: dict[str, tuple] = {}
    order: dict[str, int] = {}
    for idx, row in enumerate(canon_rows):
        sid = row["snapshot_id"]
        key = (row["ts"], -row["size_bytes"], len(row["note"]), row["repo"], -idx)
        if sid not in best or key > best[sid]:
            best[sid] = key
            order[sid] = idx
    keep_idx = set(order.values())
    return [row for idx, row in enumerate(canon_rows) if idx in keep_idx]


# --------------------------------------------------------------------------
# Stage 3: governance calendar bucket assignment (#RET-7104)
# All integer epoch-second math; deviates from ISO week / calendar month.
# --------------------------------------------------------------------------
def gday(ts: int) -> int:
    return (ts - DAY_CUT) // SECONDS_PER_DAY


def bucket_ids(ts: int) -> dict[str, int]:
    d = gday(ts)
    return {
        "daily": d,
        "weekly": (d - WEEK_PHASE) // 7,
        "monthly": d // MONTH_LEN,
        "yearly": d // YEAR_LEN,
    }


# --------------------------------------------------------------------------
# Stage 4: representatives, per-tier caps, pins, cross-tier promotion
# (#RET-7106, #RET-7120, #RET-7124, #RET-7122)
# --------------------------------------------------------------------------
def load_holds(pin_rows: list[dict]) -> dict[tuple[str, str], str]:
    holds: dict[tuple[str, str], str] = {}
    for row in pin_rows:
        repo = canon_name(row.get("repo", ""))
        sid = str(row.get("snapshot_id", ""))
        hold = str(row.get("hold", "")).strip().lower()
        if hold not in RECOGNIZED_HOLDS:
            continue
        key = (repo, sid)
        # #RET-7124: the strictest recognized hold is the one reported, and
        # compliance/legal/manual rank in that order, which is their own.
        if key not in holds or hold < holds[key]:
            holds[key] = hold
    return holds


def representative_key(row: dict) -> tuple:
    # #RET-7106: representative of a bucket = EARLIEST ts (the sealed period
    # marker, deviating from standard GFS which keeps the LATEST); tie-break by
    # LARGER size_bytes, then snapshot_id ascending.
    return (row["ts"], -row["size_bytes"], row["snapshot_id"])


def select_kept(repo_rows: list[dict], policy: dict) -> dict[str, dict]:
    """Return {snapshot_id: kept_info} for one repo.

    kept_info = {"roles": [tiers... in TIER_ORDER], "held": bool, "hold": str}
    """
    caps = {
        "daily": policy["cap_daily"],
        "weekly": policy["cap_weekly"],
        "monthly": policy["cap_monthly"],
        "yearly": policy["cap_yearly"],
    }
    # per-tier: group by bucket id, pick representative, select most-recent caps.
    tier_reps: dict[str, dict] = {tier: {} for tier in TIER_ORDER}
    for tier in TIER_ORDER:
        buckets: dict[int, dict] = {}
        for row in repo_rows:
            bid = row["_buckets"][tier]
            cur = buckets.get(bid)
            if cur is None or representative_key(row) < representative_key(cur):
                buckets[bid] = row
        # select the C most-recent buckets (largest bucket id).
        selected = sorted(buckets, reverse=True)[: max(caps[tier], 0)]
        for bid in selected:
            tier_reps[tier][buckets[bid]["snapshot_id"]] = buckets[bid]

    kept: dict[str, dict] = {}
    for tier in TIER_ORDER:
        for sid in tier_reps[tier]:
            info = kept.setdefault(sid, {"roles": [], "held": False, "hold": ""})
            info["roles"].append(tier)
    # #RET-7124 pinned-hold exemption: an event-pinned snapshot, or one named in
    # the pin registry, is ALWAYS kept regardless of caps (deviates from GFS).
    for row in repo_rows:
        if row["_held"]:
            info = kept.setdefault(
                row["snapshot_id"], {"roles": [], "held": False, "hold": ""}
            )
            info["held"] = True
            info["hold"] = row["_hold"]
    # #RET-7122 cross-tier promotion: a single kept snapshot that represents
    # several tiers carries all those roles (its role list is the union), so a
    # kept daily also satisfies the weekly/monthly/yearly slot it marks -- the
    # kept set is the UNION, not the sum, of the per-tier selections.
    for sid, info in kept.items():
        info["roles"] = [t for t in TIER_ORDER if t in info["roles"]]
    return kept


# --------------------------------------------------------------------------
# Stage 5: stateful per-repo quota ledger (#RET-7116, #RET-7160, #RET-7162)
# --------------------------------------------------------------------------
def apply_ledger(kept_rows: list[dict], quota_cap: int) -> None:
    # kept_rows: one repo's kept snapshots sorted by (ts, snapshot_id).
    prev_ts = None
    prev_quota = 0
    for row in kept_rows:
        size_mb = _ceil_div(max(row["size_bytes"], 0), QUOTA_QUANTUM)
        if prev_ts is None:
            idle_gap = 0
            carry_in = 0
        else:
            idle_gap = max(row["ts"] - prev_ts, 0)
            if idle_gap > RESET_GAP:
                carry_in = 0
            else:
                carry_in = max(prev_quota - _ceil_div(idle_gap, DECAY_DIV), 0)
        used_quota = min(carry_in + size_mb, quota_cap)
        row["_size_mb"] = size_mb
        row["_idle_gap"] = idle_gap
        row["_carry_in"] = carry_in
        row["_used_quota"] = used_quota
        prev_ts = row["ts"]
        prev_quota = used_quota


# --------------------------------------------------------------------------
# Policy resolution (#RET-7150, #RET-7152)
# --------------------------------------------------------------------------
def overlap_counts(repo_rows: list[dict], protection_days: int) -> dict[str, int]:
    """#RET-7172: how many other snapshots of this repo hold an intersecting
    protection window.

    Window ends are sorted once and each snapshot's count is read off by
    position, so the whole repo costs O(n log n). Comparing every pair inside a
    repo is quadratic in the repo's size and cannot meet the runtime budget.
    """
    span = protection_days * 86400
    starts = sorted(r["ts"] for r in repo_rows)
    ends = sorted(r["ts"] + span for r in repo_rows)
    counts: dict[str, int] = {}
    for row in repo_rows:
        start = row["ts"]
        end = start + span
        # windows are [ts, ts + span] inclusive: j intersects i when
        # start_j <= end_i and end_j >= start_i
        began_by_end = bisect.bisect_right(starts, end)
        ended_before = bisect.bisect_left(ends, start)
        counts[row["snapshot_id"]] = began_by_end - ended_before - 1
    return counts


def peak_depths(repo_rows: list[dict], protection_days: int) -> dict[str, int]:
    """#RET-7180: the busiest instant inside each snapshot's own window.

    The count of live protection windows only changes where one opens or
    closes, so the repo's protection depth is a step function over those
    boundaries. It is built once by sweeping the boundaries in order, and a
    sparse table over the steps answers each snapshot's window with two
    lookups. Re-deriving the depth per snapshot walks the whole repo again and
    is quadratic in the repo's size.
    """
    span = protection_days * 86400
    events: list[tuple[int, int]] = []
    for row in repo_rows:
        events.append((row["ts"], 1))
        events.append((row["ts"] + span + 1, -1))
    events.sort()

    # bound[k] is where step k begins; depth[k] is how many windows are live
    # from there until the next boundary.
    bound: list[int] = []
    depth: list[int] = []
    live = 0
    index = 0
    while index < len(events):
        position = events[index][0]
        while index < len(events) and events[index][0] == position:
            live += events[index][1]
            index += 1
        bound.append(position)
        depth.append(live)

    # sparse table for range maxima over the steps
    levels = max(1, len(depth).bit_length())
    table = [depth]
    width = 1
    while width * 2 <= len(depth):
        previous = table[-1]
        table.append([
            max(previous[i], previous[i + width])
            for i in range(len(depth) - width * 2 + 1)
        ])
        width *= 2
    del levels

    def range_max(lo: int, hi: int) -> int:
        """Largest depth over steps lo..hi inclusive."""
        size = hi - lo + 1
        level = size.bit_length() - 1
        row = table[level]
        return max(row[lo], row[hi - (1 << level) + 1])

    peaks: dict[str, int] = {}
    for row in repo_rows:
        start = row["ts"]
        end = start + span
        lo = bisect.bisect_right(bound, start) - 1
        hi = bisect.bisect_right(bound, end) - 1
        peaks[row["snapshot_id"]] = range_max(lo, hi)
    return peaks


def chain_segments(repo_rows: list[dict], kept_ids: set) -> list[list[dict]]:
    """The prunable runs of one repo, in the order the tie-break walks them.

    Inside a vault the snapshots are one incremental chain in time order, and a
    kept snapshot re-anchors it. So the candidates between two kept snapshots
    form a run whose members can only be dropped from the newest end backwards:
    deleting a snapshot that a later one still builds on would leave the later
    one unrestorable.
    """
    by_vault: dict[str, list[dict]] = {}
    for row in repo_rows:
        by_vault.setdefault(row["vault"], []).append(row)

    segments: list[list[dict]] = []
    for vault in sorted(by_vault):
        run: list[dict] = []
        for row in sorted(by_vault[vault], key=lambda r: (r["ts"], r["snapshot_id"])):
            if row["snapshot_id"] in kept_ids:
                if run:
                    segments.append(run)
                    run = []
            else:
                run.append(row)
        if run:
            segments.append(run)
    segments.sort(key=lambda seg: (seg[0]["vault"], seg[0]["ts"], seg[0]["snapshot_id"]))
    return segments


def select_pruned(segments: list[list[dict]], cap: int) -> set:
    """#RET-7184: the most bytes the cap can reclaim without breaking a chain.

    Each run contributes a suffix of itself, so the cycle is choosing how deep
    to cut into each of them at once rather than picking snapshots one by one.
    Taking the largest candidates wherever they sit breaks the chains, and
    taking whole runs in order of bytes per snapshot stays legal but stops
    short of what the cap could have reclaimed. The choice is made once over
    every run together, maximising reclaimed bytes, then the fewest snapshots,
    with the earliest run giving way first where two plans are still level.
    """
    if cap <= 0 or not segments:
        return set()

    # suffix_bytes[i][j] is what dropping the newest j of run i reclaims.
    suffix_bytes: list[list[int]] = []
    for segment in segments:
        running, sums = 0, [0]
        for row in reversed(segment):
            running += int(row["size_bytes"])
            sums.append(running)
        suffix_bytes.append(sums)

    # Reclaimed bytes dominate; the snapshot count breaks a tie by being
    # smaller, so both keys ride in one integer and the search stays exact.
    unit = cap + 1
    rows: list[list[int]] = [[0] * (cap + 1) for _ in range(len(segments) + 1)]
    for index in range(len(segments) - 1, -1, -1):
        sums = suffix_bytes[index]
        here, nxt = rows[index], rows[index + 1]
        reach = len(sums) - 1
        for capacity in range(cap + 1):
            best = nxt[capacity]
            limit = min(capacity, reach)
            for take in range(1, limit + 1):
                value = nxt[capacity - take] + sums[take] * unit - take
                best = max(best, value)
            here[capacity] = best

    pruned: set = set()
    capacity = cap
    for index, segment in enumerate(segments):
        sums = suffix_bytes[index]
        reach = len(sums) - 1
        limit = min(capacity, reach)
        target = rows[index][capacity]
        # #RET-7184: where two selections are level, THE EARLIER RUN GIVES WAY
        # FIRST. Runs are walked in that order, so a positive cut here is tried
        # before skipping: the previous form checked skipping first and only
        # searched when skipping missed the target, which pushed the cut into a
        # later run and did the opposite of the rule it cited.
        # ...and giving way first means giving up as much as the tie allows, so
        # the DEEPEST cut that still reaches the target wins. Walking upwards
        # took the shallowest one instead, which left the same bytes and the
        # same count to be found in a later run -- the opposite of the rule.
        chosen = 0
        for take in range(limit, 0, -1):
            if rows[index + 1][capacity - take] + sums[take] * unit - take == target:
                chosen = take
                break
        if chosen:
            for row in segment[len(segment) - chosen:]:
                pruned.add(row["snapshot_id"])
            capacity -= chosen
    return pruned


def resolve_policy(repo: str, policy_data: dict) -> dict:
    resolved = dict(POLICY_BASELINE)
    for field, val in policy_data.get("default", {}).items():
        if field in resolved:
            resolved[field] = coerce_int(val)
    override = policy_data.get("repo_overrides", {}).get(repo)
    if isinstance(override, dict):
        for field, val in override.items():
            if field in resolved:
                resolved[field] = coerce_int(val)
    return resolved


DECISION_FIELDS = (
    "snapshot_id", "repo", "vault", "ts", "size_bytes", "size_mb", "pinned", "held",
    "hold", "daily_bucket", "weekly_bucket", "monthly_bucket", "yearly_bucket",
    "roles", "decision", "idle_gap", "carry_in", "used_quota", "overlap_count",
    "peak_depth",
)


def run(input_path: str, output_dir: str) -> None:
    raw_rows = json.loads(Path(input_path).read_text(encoding="utf-8"))
    policy_data = json.loads(Path(POLICY_PATH).read_text(encoding="utf-8"))
    pin_rows = json.loads(Path(PIN_REGISTRY_PATH).read_text(encoding="utf-8"))

    canon_rows = deduplicate(canonicalize(raw_rows))
    holds = load_holds(pin_rows)

    for row in canon_rows:
        row["_buckets"] = bucket_ids(row["ts"])
        held = bool(row["pinned"]) or (row["repo"], row["snapshot_id"]) in holds
        row["_held"] = held
        if row["pinned"]:
            row["_hold"] = "flag"
        elif (row["repo"], row["snapshot_id"]) in holds:
            row["_hold"] = holds[(row["repo"], row["snapshot_id"])]
        else:
            row["_hold"] = ""

    by_repo: dict[str, list[dict]] = {}
    for row in canon_rows:
        by_repo.setdefault(row["repo"], []).append(row)

    kept_rows: list[dict] = []
    keep_meta: dict[str, dict] = {}
    selected_bucket_count = 0
    for repo in sorted(by_repo):
        policy = resolve_policy(repo, policy_data)
        kept = select_kept(by_repo[repo], policy)
        for sid, info in kept.items():
            keep_meta[sid] = info
        repo_kept = [r for r in by_repo[repo] if r["snapshot_id"] in kept]
        repo_kept.sort(key=lambda r: (r["ts"], r["snapshot_id"]))
        apply_ledger(repo_kept, policy["quota_cap"])
        kept_rows.extend(repo_kept)
        for info in kept.values():
            selected_bucket_count += len(info["roles"])

    kept_ids = set(keep_meta)

    # --- protection-window overlap per repo (#RET-7172) ---
    overlap_lookup: dict[str, int] = {}
    depth_lookup: dict[str, int] = {}
    for repo in sorted(by_repo):
        policy = resolve_policy(repo, policy_data)
        overlap_lookup.update(overlap_counts(by_repo[repo], policy["protection_days"]))
        depth_lookup.update(peak_depths(by_repo[repo], policy["protection_days"]))

    # --- Stage 6: chain-closed prune selection (#RET-7184, cap from #RET-7146) ---
    prune_decision: dict[str, str] = {}
    for repo in sorted(by_repo):
        policy = resolve_policy(repo, policy_data)
        segments = chain_segments(by_repo[repo], kept_ids)
        pruned = select_pruned(segments, max(policy["prune_cap"], 0))
        for segment in segments:
            for row in segment:
                sid = row["snapshot_id"]
                prune_decision[sid] = "prune" if sid in pruned else "defer"

    # --- assemble one decision record per canonical snapshot ---
    ledger_lookup = {r["snapshot_id"]: r for r in kept_rows}
    decisions: list[dict] = []
    for row in canon_rows:
        sid = row["snapshot_id"]
        if sid in kept_ids:
            info = keep_meta[sid]
            roles = list(info["roles"])
            if info["held"]:
                roles = roles + ["pinned"]
            decision = "keep"
            lrow = ledger_lookup[sid]
            idle_gap = lrow["_idle_gap"]
            carry_in = lrow["_carry_in"]
            used_quota = lrow["_used_quota"]
            size_mb = lrow["_size_mb"]
        else:
            roles = []
            decision = prune_decision[sid]
            idle_gap = 0
            carry_in = 0
            used_quota = 0
            size_mb = _ceil_div(max(row["size_bytes"], 0), QUOTA_QUANTUM)
        rec = {
            "snapshot_id": sid,
            "repo": row["repo"],
            "vault": row["vault"],
            "ts": row["ts"],
            "size_bytes": row["size_bytes"],
            "size_mb": size_mb,
            "pinned": bool(row["pinned"]),
            "held": bool(row["_held"]),
            "hold": row["_hold"],
            "daily_bucket": row["_buckets"]["daily"],
            "weekly_bucket": row["_buckets"]["weekly"],
            "monthly_bucket": row["_buckets"]["monthly"],
            "yearly_bucket": row["_buckets"]["yearly"],
            "roles": roles,
            "decision": decision,
            "idle_gap": idle_gap,
            "carry_in": carry_in,
            "used_quota": used_quota,
            "overlap_count": overlap_lookup[row["snapshot_id"]],
            "peak_depth": depth_lookup[row["snapshot_id"]],
        }
        decisions.append(rec)

    # --- decisions emission order (#RET-7145) ---
    class_rank = {"prune": 0, "defer": 1, "keep": 2}
    decisions.sort(
        key=lambda r: (
            class_rank[r["decision"]], -r["size_bytes"], r["ts"], r["repo"], r["snapshot_id"]
        )
    )

    decision_counts = {name: 0 for name in DECISION_ORDER}
    for rec in decisions:
        decision_counts[rec["decision"]] += 1

    kept_size = sum(r["size_bytes"] for r in decisions if r["decision"] == "keep")
    pruned_size = sum(r["size_bytes"] for r in decisions if r["decision"] == "prune")
    deferred_size = sum(r["size_bytes"] for r in decisions if r["decision"] == "defer")
    max_quota = max((r["_used_quota"] for r in kept_rows), default=0)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "raw_snapshot_count": len(raw_rows),
        "unique_snapshot_ids": len({collapse_ws(r.get("snapshot_id", "")) for r in raw_rows}),
        "canonical_snapshot_count": len(canon_rows),
        "repo_count": len(by_repo),
        "held_count": sum(1 for r in canon_rows if r["_held"]),
        "decision_counts": decision_counts,
        "kept_count": decision_counts["keep"],
        "pruned_count": decision_counts["prune"],
        "deferred_count": decision_counts["defer"],
        "selected_bucket_count": selected_bucket_count,
        "total_size_bytes": sum(r["size_bytes"] for r in canon_rows),
        "kept_size_bytes": kept_size,
        "reclaimed_size_bytes": pruned_size,
        "deferred_size_bytes": deferred_size,
        "max_quota_used": max_quota,
        "max_overlap_count": max((d["overlap_count"] for d in decisions), default=0),
        "max_peak_depth": max((d["peak_depth"] for d in decisions), default=0),
    }

    # --- retention_state.json: object keyed by repo ---
    state: dict[str, dict] = {}
    for repo in sorted(by_repo):
        repo_kept = [r for r in kept_rows if r["repo"] == repo]
        entry = {tier: [] for tier in TIER_ORDER}
        entry["pinned"] = []
        for r in repo_kept:
            info = keep_meta[r["snapshot_id"]]
            for tier in info["roles"]:
                entry[tier].append(r["snapshot_id"])
            if info["held"]:
                entry["pinned"].append(r["snapshot_id"])
        for key in list(entry):
            entry[key] = sorted(entry[key])
        entry["kept_count"] = len(repo_kept)
        entry["quota_used"] = max((r["_used_quota"] for r in repo_kept), default=0)
        state[repo] = entry

    out_decisions = [{f: rec[f] for f in DECISION_FIELDS} for rec in decisions]

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out / "retention_state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    with (out / "retention_decisions.jsonl").open("w", encoding="utf-8") as fh:
        for rec in out_decisions:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup / storage retention reconciler")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    run(args.input, args.output_dir)


if __name__ == "__main__":
    main()
