#!/usr/bin/env python3
"""Backup / storage retention reconciler (INCIDENT SNAPSHOT -- DO NOT SHIP).

This is the reconciler as it stood after the failed backup-platform rollout. It
still evaluates the retention pipeline against the February draft proposals and
the March interim decisions that the storage governance board later reversed --
it applies a STANDARD age-based GFS (keep the LATEST snapshot per naive calendar
period, tiers independent, pinned holds ignored) with midnight day boundaries
and naive floor-division periods -- so the keep/prune/defer decisions it emits
are wrong. Restore it to the board's final decisions recorded in
/app/incident/retention_governance_log.md.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_INPUT = "/app/data/snapshots.json"
DEFAULT_OUTPUT_DIR = "/app/output"
POLICY_PATH = "/app/data/retention_policy.json"
PIN_REGISTRY_PATH = "/app/data/pin_registry.json"

SCHEMA_VERSION = "retention-gfs-v1"
TIER_ORDER = ["daily", "weekly", "monthly", "yearly"]
DECISION_ORDER = ["keep", "prune", "defer"]

# Draft/interim constants (pre-reversal): naive floor-division calendar.
SECONDS_PER_DAY = 86400
NAIVE_WEEK = 604800          # #RET-7004 draft: naive 7-day floor (Thursday phase)
NAIVE_MONTH = 2592000        # #RET-7004 draft: naive 30-day floor, midnight
NAIVE_YEAR = 31536000        # #RET-7004 draft: 365-day floor
DECAY_DIV = 86400
QUOTA_QUANTUM = 1048576

POLICY_FIELDS = (
    "cap_daily", "cap_weekly", "cap_monthly", "cap_yearly", "quota_cap", "prune_cap",
)
POLICY_BASELINE = {
    "cap_daily": 7, "cap_weekly": 4, "cap_monthly": 6, "cap_yearly": 2,
    "quota_cap": 100000, "prune_cap": 3,
}


def _ceil_div(numer: int, denom: int) -> int:
    return -(-numer // denom)


def canon_name(value: object) -> str:
    text = str(value).strip().lower()
    return text if text else "unassigned"


def collapse_ws(value: object) -> str:
    return " ".join(str(value).split())


def coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    try:
        return int(text)
    except ValueError:
        try:
            return int(float(text))
        except ValueError:
            return 0


def coerce_flag(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "pinned"}
    return bool(value)


def canonicalize(raw_rows: list[dict]) -> list[dict]:
    canon = []
    for row in raw_rows:
        canon.append(
            {
                "snapshot_id": collapse_ws(row.get("snapshot_id", "")),
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
    # #RET-7109 draft: on a ts tie keep the HIGHER size (pre-#RET-7142 reversal).
    best: dict[str, tuple] = {}
    order: dict[str, int] = {}
    for idx, row in enumerate(canon_rows):
        sid = row["snapshot_id"]
        key = (row["ts"], row["size_bytes"], len(row["note"]), row["repo"], -idx)
        if sid not in best or key > best[sid]:
            best[sid] = key
            order[sid] = idx
    keep_idx = set(order.values())
    return [row for idx, row in enumerate(canon_rows) if idx in keep_idx]


def bucket_ids(ts: int) -> dict[str, int]:
    # #RET-7004 draft: naive midnight day boundary and floor-division periods.
    return {
        "daily": ts // SECONDS_PER_DAY,
        "weekly": ts // NAIVE_WEEK,
        "monthly": ts // NAIVE_MONTH,
        "yearly": ts // NAIVE_YEAR,
    }


def load_holds(pin_rows: list[dict]) -> dict[tuple[str, str], str]:
    holds: dict[tuple[str, str], str] = {}
    for row in pin_rows:
        repo = canon_name(row.get("repo", ""))
        sid = collapse_ws(row.get("snapshot_id", ""))
        hold = str(row.get("hold", "")).strip().lower()
        if hold not in ("compliance", "legal", "manual"):
            continue
        key = (repo, sid)
        if key not in holds or hold < holds[key]:
            holds[key] = hold
    return holds


def representative_key(row: dict) -> tuple:
    # #RET-7006 draft: standard GFS keeps the LATEST snapshot per bucket.
    return (-row["ts"], -row["size_bytes"], row["snapshot_id"])


def select_kept(repo_rows: list[dict], policy: dict) -> dict[str, dict]:
    caps = {
        "daily": policy["cap_daily"], "weekly": policy["cap_weekly"],
        "monthly": policy["cap_monthly"], "yearly": policy["cap_yearly"],
    }
    tier_reps: dict[str, dict] = {tier: {} for tier in TIER_ORDER}
    for tier in TIER_ORDER:
        buckets: dict[int, dict] = {}
        for row in repo_rows:
            bid = row["_buckets"][tier]
            cur = buckets.get(bid)
            if cur is None or representative_key(row) < representative_key(cur):
                buckets[bid] = row
        selected = sorted(buckets, reverse=True)[: max(caps[tier], 0)]
        for bid in selected:
            tier_reps[tier][buckets[bid]["snapshot_id"]] = buckets[bid]
    kept: dict[str, dict] = {}
    for tier in TIER_ORDER:
        for sid in tier_reps[tier]:
            info = kept.setdefault(sid, {"roles": [], "held": False, "hold": ""})
            info["roles"].append(tier)
    # #RET-7024 draft: pinned holds are IGNORED (independent-tier standard GFS).
    for sid, info in kept.items():
        info["roles"] = [t for t in TIER_ORDER if t in info["roles"]]
    return kept


def apply_ledger(kept_rows: list[dict], quota_cap: int) -> None:
    # #RET-7115 draft: FLOOR decay and NO reset boundary.
    prev_ts = None
    prev_quota = 0
    for row in kept_rows:
        size_mb = _ceil_div(max(row["size_bytes"], 0), QUOTA_QUANTUM)
        if prev_ts is None:
            idle_gap = 0
            carry_in = 0
        else:
            idle_gap = max(row["ts"] - prev_ts, 0)
            carry_in = max(prev_quota - (idle_gap // DECAY_DIV), 0)
        used_quota = min(carry_in + size_mb, quota_cap)
        row["_size_mb"] = size_mb
        row["_idle_gap"] = idle_gap
        row["_carry_in"] = carry_in
        row["_used_quota"] = used_quota
        prev_ts = row["ts"]
        prev_quota = used_quota


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
    "roles", "decision", "idle_gap", "carry_in", "used_quota",
)


def run(input_path: str, output_dir: str) -> None:
    raw_rows = json.loads(Path(input_path).read_text(encoding="utf-8"))
    policy_data = json.loads(Path(POLICY_PATH).read_text(encoding="utf-8"))
    pin_rows = json.loads(Path(PIN_REGISTRY_PATH).read_text(encoding="utf-8"))

    canon_rows = deduplicate(canonicalize(raw_rows))
    # #RET-7024 draft: registry holds are advisory only and change nothing.
    load_holds(pin_rows)

    for row in canon_rows:
        row["_buckets"] = bucket_ids(row["ts"])
        row["_held"] = False   # draft: holds ignored
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

    # #RET draft: prune everything not kept (no per-repo prune cap / defers).
    prune_decision: dict[str, str] = {}
    for repo in sorted(by_repo):
        candidates = [r for r in by_repo[repo] if r["snapshot_id"] not in kept_ids]
        candidates.sort(key=lambda r: (-r["size_bytes"], r["ts"], r["snapshot_id"]))
        for row in candidates:
            prune_decision[row["snapshot_id"]] = "prune"

    ledger_lookup = {r["snapshot_id"]: r for r in kept_rows}
    decisions: list[dict] = []
    for row in canon_rows:
        sid = row["snapshot_id"]
        if sid in kept_ids:
            info = keep_meta[sid]
            roles = list(info["roles"])
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
            "snapshot_id": sid, "repo": row["repo"], "vault": row["vault"], "ts": row["ts"],
            "size_bytes": row["size_bytes"], "size_mb": size_mb, "pinned": bool(row["pinned"]),
            "held": False, "hold": "", "daily_bucket": row["_buckets"]["daily"],
            "weekly_bucket": row["_buckets"]["weekly"], "monthly_bucket": row["_buckets"]["monthly"],
            "yearly_bucket": row["_buckets"]["yearly"], "roles": roles, "decision": decision,
            "idle_gap": idle_gap, "carry_in": carry_in, "used_quota": used_quota,
        }
        decisions.append(rec)

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
    }

    state: dict[str, dict] = {}
    for repo in sorted(by_repo):
        repo_kept = [r for r in kept_rows if r["repo"] == repo]
        entry = {tier: [] for tier in TIER_ORDER}
        entry["pinned"] = []
        for r in repo_kept:
            info = keep_meta[r["snapshot_id"]]
            for tier in info["roles"]:
                entry[tier].append(r["snapshot_id"])
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
