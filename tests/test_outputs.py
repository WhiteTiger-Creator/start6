"""Verifier tests for the backup / storage retention reconciler task."""

from __future__ import annotations

import ast
import hashlib
import itertools
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

WORKFLOW_PATH = Path("/app/workflow/reconcile_retention.py")
ORIGINAL_WORKFLOW_PATH = Path("/app/workflow/.reconcile_retention.original")
DEFAULT_INPUT = Path("/app/data/snapshots.json")
CATALOGUE_PATH = Path("/app/data/snapshot_catalogue_pre_incident.json")
JOURNAL_PATH = Path("/app/data/snapshot_replay_journal.json")
DATA_DIR = Path("/app/data")
POLICY_PATH = Path("/app/data/retention_policy.json")
PIN_REGISTRY_PATH = Path("/app/data/pin_registry.json")
SPEC_PATH = Path("/app/docs/report_spec.json")
# The contract is golden metadata: the verifier reads it from its own image,
# never from the agent-writable copy under /app.
GOLDEN_CONTRACT_PATH = Path("/tests/fixtures/contract_golden.json")
LOG_PATH = Path("/app/incident/retention_governance_log.md")
EXPECTED_FIXTURE = Path("/tests/fixtures/expected_report.json")
ALT_INPUT = Path("/tests/fixtures/alt_snapshots.json")
# The shipped truncated inventory is overwritten in place by the recovery, so
# the verifier keeps its own copy to prove the reconciler depends on the merge.
TRUNCATED_REFERENCE_PATH = Path("/tests/fixtures/truncated_snapshots.json")

TIER_ORDER = ["daily", "weekly", "monthly", "yearly"]
DECISION_ORDER = ["keep", "prune", "defer"]
CLASS_RANK = {"prune": 0, "defer": 1, "keep": 2}

FIXTURE = json.loads(EXPECTED_FIXTURE.read_text())
SPEC = json.loads(GOLDEN_CONTRACT_PATH.read_text())

POLICY_FIELDS = ("protection_days", "cap_daily", "cap_weekly", "cap_monthly",
                 "cap_yearly", "quota_cap", "prune_cap")
BASELINE = {
    "protection_days": 21,
    "cap_daily": 7, "cap_weekly": 4, "cap_monthly": 6, "cap_yearly": 2,
    "quota_cap": 100000, "prune_cap": 300,
}
SNAPSHOT_FIELDS = ("snapshot_id", "repo", "vault", "ts", "size_bytes", "pinned", "note")

DECISION_KEYS = set(SPEC["retention_decisions_jsonl"]["required_fields"])
STATE_KEYS = set(SPEC["retention_state_json"]["required_fields"])
SUMMARY_KEYS = set(SPEC["summary_json"]["required_fields"])


def _digest(value: object) -> str:
    """Content digest of a whole artifact; the graded inventory is far too large
    to embed in a fixture, so equality is asserted over its digest."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


# Documented wall-clock budget for one full run on the graded inventory.
# instruction.md and report_spec.json state the same number. The reference reads
# each protection-window overlap off ordered endpoints and finishes in a few
# seconds; comparing every pair inside a repository is quadratic in its size and
# cannot finish. Kept as a literal here (never read from the mutable /app spec)
# so the budget cannot be relaxed by editing the environment.
RUNTIME_BUDGET_SEC = 120.0


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


# --- verifier execution isolation -------------------------------------------------
# The submitted /app/workflow/reconcile_retention.py is untrusted once the separate verifier runs
# it. We execute it under an unprivileged UID (65534 / nobody) via setpriv, so it cannot write the
# reward path, read the held-out fixtures under /tests, or interfere with the verifier. Inputs are
# staged into a candidate-writable work area; policy files under /app keep their fixed paths.
_CWORK = Path("/candidate-work")
_run_ctr = itertools.count()
_SETPRIV = ["setpriv", "--reuid=65534", "--regid=65534", "--clear-groups", "--no-new-privs"]
# The contract's own budget, enforced rather than documented: a run that
# compares protection windows pairwise on these repos does not come back
# inside it, and a timeout here is a failure exactly as the contract says.
_RUN_TIMEOUT = RUNTIME_BUDGET_SEC

# The submitted program gets a minimal explicit environment rather than inheriting the verifier's
# (PATH/PYTHONPATH/CI variables and any other grader context).
_CANDIDATE_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/candidate-work", "LANG": "C.UTF-8"}


def _publish_inputs() -> None:
    """Open read access on the agent-produced inputs before privileges drop.

    A correct solution may write its recovered inventory atomically, leaving the
    file mode 0600 and owned by root. The verifier then runs the submitted
    program as uid 65534, which could not read it -- so file ownership, not
    correctness, would decide the score. The verifier is root here, so it grants
    read access first.
    """
    for path in sorted(DATA_DIR.rglob("*")):
        try:
            os.chmod(path, 0o755 if path.is_dir() else 0o644)
        except OSError:
            pass
    try:
        os.chmod(DATA_DIR, 0o755)
    except OSError:
        pass


def _candidate_dir() -> Path:
    d = _CWORK / f"run-{next(_run_ctr)}"
    d.mkdir(parents=True, exist_ok=True)
    os.chmod(d, 0o777)
    return d


def _run_agent(argv, cwd: Path):
    """Run the submitted program under the unprivileged candidate UID with a scrubbed environment."""
    return subprocess.run(
        _SETPRIV + argv, check=True, capture_output=True, text=True, cwd=str(cwd),
        env=dict(_CANDIDATE_ENV), timeout=_RUN_TIMEOUT,
    )


def _run_pipeline(tmp_path: Path, script_path: Path = WORKFLOW_PATH, input_path: Path = DEFAULT_INPUT):
    _publish_inputs()
    work = _candidate_dir()
    out_dir = work / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(out_dir, 0o777)
    staged_input = work / "input.json"
    shutil.copy(str(input_path), str(staged_input))
    os.chmod(staged_input, 0o644)
    result = _run_agent(
        [sys.executable, str(script_path), "--input", str(staged_input), "--output-dir", str(out_dir)],
        cwd=work,
    )
    assert result.returncode == 0
    summary = _load_json(out_dir / "summary.json")
    state = _load_json(out_dir / "retention_state.json")
    decisions = _load_jsonl(out_dir / "retention_decisions.jsonl")
    return out_dir, summary, state, decisions


@pytest.fixture(scope="session")
def primary_outputs(tmp_path_factory):
    return _run_pipeline(tmp_path_factory.mktemp("primary"))


def test_runtime_budget_is_stated_in_the_contract():
    """The budget the instruction quotes is the one the output contract carries,
    so the agent is told the same number in both places."""
    assert float(SPEC["runtime_budget_seconds"]) == RUNTIME_BUDGET_SEC


def test_overlap_reported_on_every_decision(primary_outputs):
    """Every decision row carries an overlap count, and the summary's maximum matches the largest of them."""
    _, summary, _, decisions = primary_outputs
    counts = [d["overlap_count"] for d in decisions]
    assert counts
    assert all(c >= 0 for c in counts)
    assert max(counts) == summary["max_overlap_count"]


def test_peak_depth_reported_on_every_decision(primary_outputs):
    """Every row carries a protection depth, bounded by its own overlap count."""
    _, summary, _, decisions = primary_outputs
    depths = [d["peak_depth"] for d in decisions]
    assert depths
    for row in decisions:
        assert isinstance(row["peak_depth"], int) and not isinstance(row["peak_depth"], bool)
        assert 1 <= row["peak_depth"] <= row["overlap_count"] + 1, row["snapshot_id"]
    assert max(depths) == summary["max_peak_depth"]


def test_peak_depth_is_not_the_overlap_count(primary_outputs):
    """The busiest instant is a different figure from the window's total.

    A run that reported the overlap count again under another name would pass
    the bounds check above, so the two are required to disagree in bulk.
    """
    _, _, _, decisions = primary_outputs
    differing = sum(1 for d in decisions if d["peak_depth"] != d["overlap_count"] + 1)
    assert differing > len(decisions) // 10, (
        f"only {differing} of {len(decisions)} rows differ from overlap_count + 1"
    )
    assert len({d["peak_depth"] for d in decisions}) > 20


def test_peak_depth_matches_an_independent_recomputation(primary_outputs):
    """Recomputed here by direct sweep, which shares no code with the pipeline.

    The depth is sampled at every window boundary lying inside each snapshot's
    own window, which is where a step function can change; agreeing with that
    is evidence rather than the same routine run twice.
    """
    _, _, _, decisions = primary_outputs
    by_repo: dict[str, list[dict]] = {}
    for row in decisions:
        by_repo.setdefault(row["repo"], []).append(row)

    repo = min(by_repo, key=lambda name: len(by_repo[name]))
    # protection_days is a resolved policy value, not the baseline: two repos
    # override it, and using the wrong span here would compare two different
    # figures rather than checking the pipeline.
    span = int(_resolve(repo, json.loads(POLICY_PATH.read_text()))["protection_days"]) * 86400
    rows = sorted(by_repo[repo], key=lambda r: r["ts"])
    starts = sorted(r["ts"] for r in rows)
    checked = 0
    for row in rows[:: max(1, len(rows) // 40)][:40]:
        window_start, window_end = row["ts"], row["ts"] + span
        marks = {window_start, window_end}
        marks.update(t for t in starts if window_start <= t <= window_end)
        marks.update(
            t + span for t in starts if window_start <= t + span <= window_end
        )
        best = 0
        for instant in sorted(marks):
            live = sum(1 for r in rows if r["ts"] <= instant <= r["ts"] + span)
            best = max(best, live)
        assert row["peak_depth"] == best, f"{row['snapshot_id']}: {row['peak_depth']} vs {best}"
        checked += 1
    assert checked >= 10


def test_overlap_varies_across_the_inventory(primary_outputs):
    """A constant overlap would mean the protection windows were never compared."""
    counts = {d["overlap_count"] for d in primary_outputs[3]}
    assert len(counts) > 50, f"only {len(counts)} distinct overlap counts"


def test_overlap_is_scoped_to_the_repo(primary_outputs):
    """No snapshot may overlap more windows than its own repo holds."""
    decisions = primary_outputs[3]
    per_repo = {}
    for d in decisions:
        per_repo[d["repo"]] = per_repo.get(d["repo"], 0) + 1
    for d in decisions:
        assert d["overlap_count"] < per_repo[d["repo"]]


# --------------------------------------------------------------------------
# Step 1: the truncated snapshot inventory must be recovered in place
# --------------------------------------------------------------------------
def _naive_concatenation() -> list[dict]:
    """The superseded draft merge: catalogue then journal, bookkeeping fields left on."""
    inventory = [dict(r) for r in _load_json(CATALOGUE_PATH)]
    inventory.extend(dict(e) for e in _load_json(JOURNAL_PATH))
    return inventory


def test_recovery_sources_are_intact():
    """The pre-incident catalogue and the replay journal are left exactly as shipped."""
    assert _digest(_load_json(CATALOGUE_PATH)) == FIXTURE["catalogue_digest"]
    assert _digest(_load_json(JOURNAL_PATH)) == FIXTURE["journal_digest"]


def test_snapshot_inventory_recovered():
    """/app/data/snapshots.json shipped truncated; it must hold the recovered inventory."""
    recovered = _load_json(DEFAULT_INPUT)
    assert isinstance(recovered, list)
    assert len(recovered) == FIXTURE["recovered_count"]
    assert _digest(recovered) == FIXTURE["recovered_digest"]


def test_recovered_records_carry_no_journal_bookkeeping():
    """Recovered records carry only the contracted snapshot fields, never journal_seq or journal_op."""
    for record in _load_json(DEFAULT_INPUT):
        assert set(record) == set(SNAPSHOT_FIELDS)


def test_shipped_and_naive_inventories_differ_from_the_recovered_one():
    """The recovery is real work: neither the truncated file nor the draft merge match."""
    expected = FIXTURE["recovered_digest"]
    assert FIXTURE["shipped_truncated_digest"] != expected
    # both sides must be digests: comparing a parsed list against a digest
    # string is never equal and would pass no matter what the recovery did
    assert _digest(_load_json(CATALOGUE_PATH)) != expected
    assert _digest(_naive_concatenation()) != expected


def test_reconciler_output_depends_on_the_recovered_inventory(tmp_path: Path):
    """Even a correctly repaired reconciler emits wrong artifacts on a wrongly merged inventory."""
    for label, inventory in (
        ("truncated", _load_json(TRUNCATED_REFERENCE_PATH)),
        ("catalogue_only", _load_json(CATALOGUE_PATH)),
        ("naive_concatenation", _naive_concatenation()),
    ):
        bad_input = tmp_path / f"{label}.json"
        _write_json(bad_input, inventory)
        _, summary, state, decisions = _run_pipeline(tmp_path / label, input_path=bad_input)
        assert summary != FIXTURE["primary"]["summary"], label
        assert (_digest(state), _digest(decisions)) != (
            FIXTURE["primary"]["state_digest"], FIXTURE["primary"]["decisions_digest"]
        ), label


# --------------------------------------------------------------------------
# Step 2: the reconciler output contract
# --------------------------------------------------------------------------
def test_cli_exists():
    """The reconciler is present and still accepts its --input and --output-dir options."""
    assert WORKFLOW_PATH.exists()


def test_output_dir_contains_exactly_three_files(primary_outputs):
    """A run writes exactly the three contracted files and nothing else."""
    out_dir, _, _, _ = primary_outputs
    names = sorted(p.name for p in out_dir.iterdir() if p.is_file())
    assert names == ["retention_decisions.jsonl", "retention_state.json", "summary.json"]


def test_primary_summary_matches_fixture(primary_outputs):
    """The summary for the graded inventory matches the sealed reference exactly."""
    _, summary, _, _ = primary_outputs
    assert summary == FIXTURE["primary"]["summary"]


def test_primary_state_matches_fixture(primary_outputs):
    """The retention state for the graded inventory matches the sealed reference exactly."""
    _, _, state, _ = primary_outputs
    assert _digest(state) == FIXTURE["primary"]["state_digest"]


def test_primary_decisions_matches_fixture(primary_outputs):
    """The decision rows for the graded inventory match the sealed reference exactly."""
    _, _, _, decisions = primary_outputs
    assert _digest(decisions) == FIXTURE["primary"]["decisions_digest"]


def _same_scalar_type(got: object, want: object) -> bool:
    """Exact type match. bool subclasses int in Python, so they are separated
    explicitly, and an integer count written as a float is not the same type."""
    if isinstance(got, bool) != isinstance(want, bool):
        return False
    return type(got) is type(want)


def test_summary_field_types_are_exact(primary_outputs):
    """Every summary field carries the contracted scalar type. Equality alone
    would accept a count emitted as 5006.0, because Python compares that equal
    to 5006; the type has to be checked separately."""
    summary = primary_outputs[1]
    expected = FIXTURE["primary"]["summary"]
    for key, want in expected.items():
        got = summary[key]
        assert _same_scalar_type(got, want), (
            f"{key}: contract says {type(want).__name__}, got {type(got).__name__} ({got!r})"
        )


def test_summary_serialises_identically_to_the_contract(primary_outputs):
    """The summary's canonical JSON text matches the sealed one, so a value
    written with a different numeric form is caught even where == would not."""
    assert _digest(primary_outputs[1]) == _digest(FIXTURE["primary"]["summary"])


def test_decision_field_types_are_exact(primary_outputs):
    """Decision rows carry the contracted scalar types, including integer
    counts that must not be emitted as floats and booleans that must not be
    emitted as 0/1."""
    decisions = primary_outputs[3]
    ints = ("ts", "size_bytes", "size_mb", "daily_bucket", "weekly_bucket",
            "monthly_bucket", "yearly_bucket", "idle_gap", "carry_in",
            "used_quota", "overlap_count")
    for row in decisions[:400]:
        for field in ints:
            value = row[field]
            assert isinstance(value, int) and not isinstance(value, bool), (
                f"{field} must be an integer, got {type(value).__name__} ({value!r})"
            )
        for field in ("pinned", "held"):
            assert isinstance(row[field], bool), f"{field} must be a boolean"
        for field in ("snapshot_id", "repo", "vault", "decision"):
            assert isinstance(row[field], str), f"{field} must be a string"


def test_summary_schema(primary_outputs):
    """The summary carries exactly the contracted field set and schema version."""
    _, summary, _, _ = primary_outputs
    assert set(summary) == SUMMARY_KEYS
    assert summary["schema_version"] == SPEC["summary_json"]["schema_version"]
    assert list(summary["decision_counts"]) == DECISION_ORDER


def test_state_schema_and_sorting(primary_outputs):
    """Retention state is an object keyed in ascending order with exactly the contracted fields."""
    _, _, state, _ = primary_outputs
    assert list(state) == sorted(state)
    for entry in state.values():
        assert set(entry) == STATE_KEYS
        for key in (*TIER_ORDER, "pinned"):
            assert entry[key] == sorted(entry[key])
        assert isinstance(entry["kept_count"], int)
        assert isinstance(entry["quota_used"], int)


def test_decisions_required_fields_and_compact(primary_outputs):
    """Decision rows carry exactly the contracted fields and are written as compact JSON lines."""
    out_dir, _, _, decisions = primary_outputs
    role_enum = set(SPEC["field_types"]["roles"]["items"]["enum"])
    hold_enum = set(SPEC["field_types"]["hold"]["enum"])
    for row in decisions:
        assert set(row) == DECISION_KEYS
        assert row["decision"] in CLASS_RANK
        assert set(row["roles"]) <= role_enum
        assert row["hold"] in hold_enum
        if row["decision"] == "keep":
            assert row["roles"], "kept rows carry at least one role"
            if row["held"]:
                assert "pinned" in row["roles"]
        else:
            assert row["roles"] == []
            assert (row["idle_gap"], row["carry_in"], row["used_quota"]) == (0, 0, 0)
    for line in (out_dir / "retention_decisions.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        assert ": " not in line
        assert json.dumps(json.loads(line), separators=(",", ":")) == line


def test_decisions_emission_order(primary_outputs):
    """Decision rows are emitted in the governing order."""
    _, _, _, decisions = primary_outputs
    assert decisions == sorted(
        decisions,
        key=lambda r: (
            CLASS_RANK[r["decision"]], -r["size_bytes"], r["ts"], r["repo"], r["snapshot_id"]
        ),
    )


def test_decision_counts_enumerate_all_three(primary_outputs):
    """The summary enumerates keep, prune and defer, emitting a count for each."""
    _, summary, _, decisions = primary_outputs
    counts = {d: 0 for d in DECISION_ORDER}
    for row in decisions:
        counts[row["decision"]] += 1
    assert summary["decision_counts"] == counts
    assert set(summary["decision_counts"]) == set(DECISION_ORDER)
    assert counts["keep"] > 0 and counts["prune"] > 0 and counts["defer"] > 0


def test_summary_math_consistency(primary_outputs):
    """Summary totals reconcile against the decision rows they aggregate."""
    _, summary, state, decisions = primary_outputs
    kept = [r for r in decisions if r["decision"] == "keep"]
    pruned = [r for r in decisions if r["decision"] == "prune"]
    deferred = [r for r in decisions if r["decision"] == "defer"]
    assert summary["canonical_snapshot_count"] == len(decisions)
    assert summary["kept_count"] == len(kept)
    assert summary["pruned_count"] == len(pruned)
    assert summary["deferred_count"] == len(deferred)
    assert summary["total_size_bytes"] == sum(r["size_bytes"] for r in decisions)
    assert summary["kept_size_bytes"] == sum(r["size_bytes"] for r in kept)
    assert summary["reclaimed_size_bytes"] == sum(r["size_bytes"] for r in pruned)
    assert summary["deferred_size_bytes"] == sum(r["size_bytes"] for r in deferred)
    assert summary["max_quota_used"] == max((r["used_quota"] for r in kept), default=0)
    assert summary["repo_count"] == len(state)
    assert summary["held_count"] == sum(1 for r in decisions if r["held"])
    selected = sum(len(entry[t]) for entry in state.values() for t in TIER_ORDER)
    assert summary["selected_bucket_count"] == selected
    for repo, entry in state.items():
        repo_keep = [r for r in kept if r["repo"] == repo]
        assert entry["kept_count"] == len(repo_keep)
        assert entry["quota_used"] == max((r["used_quota"] for r in repo_keep), default=0)


def test_summary_counts_track_the_recovered_inventory(primary_outputs):
    """Summary counts track the recovered inventory rather than the truncated file."""
    _, summary, _, _ = primary_outputs
    inventory = _load_json(DEFAULT_INPUT)
    assert summary["raw_snapshot_count"] == len(inventory)
    assert summary["unique_snapshot_ids"] == len({r["snapshot_id"] for r in inventory})


def test_promotion_union_present(primary_outputs):
    """Cross-tier promotion: at least one kept snapshot represents >= 2 tiers."""
    _, _, _, decisions = primary_outputs
    multi = [r for r in decisions if r["decision"] == "keep"
             and len([t for t in r["roles"] if t in TIER_ORDER]) >= 2]
    assert multi, "fixture must exercise a snapshot promoted across tiers"


# --------------------------------------------------------------------------
# Original / broken snapshot
# --------------------------------------------------------------------------
def _repo_runs(decisions: list[dict]) -> dict[str, list[list[dict]]]:
    """Rebuild the prunable runs from the graded decision rows.

    A run is the stretch of non-kept snapshots between two kept ones inside a
    vault, oldest first. Derived here from the agent's own output rather than
    from any reference, so these checks stay honest if the reference changes.
    """
    by_repo_vault: dict[tuple[str, str], list[dict]] = {}
    for row in decisions:
        by_repo_vault.setdefault((row["repo"], row["vault"]), []).append(row)
    runs: dict[str, list[list[dict]]] = {}
    for (repo, _vault), rows in by_repo_vault.items():
        rows.sort(key=lambda r: (r["ts"], r["snapshot_id"]))
        current: list[dict] = []
        for row in rows:
            if row["decision"] == "keep":
                if current:
                    runs.setdefault(repo, []).append(current)
                    current = []
            else:
                current.append(row)
        if current:
            runs.setdefault(repo, []).append(current)
    return runs


def test_pruning_never_breaks_an_incremental_chain(primary_outputs):
    """Within a run, what is pruned must be a suffix, newest end first.

    A later snapshot builds on the one before it, so a pruned snapshot with a
    deferred snapshot after it in the same run would leave that one
    unrestorable. This is the constraint the size-ordered selection ignores.
    """
    _, _, _, decisions = primary_outputs
    checked = 0
    for repo, runs in _repo_runs(decisions).items():
        for run in runs:
            flags = [row["decision"] == "prune" for row in run]
            assert flags == sorted(flags), (
                f"{repo}: a pruned snapshot is followed by a deferred one in the same run"
            )
            checked += 1
    assert checked > 100, f"only {checked} runs were examined"


def test_prune_cap_is_respected_per_repo(primary_outputs):
    """No repo prunes more than its resolved cap allows."""
    _, _, _, decisions = primary_outputs
    policy_data = _load_json(POLICY_PATH)
    per_repo: dict[str, int] = {}
    for row in decisions:
        if row["decision"] == "prune":
            per_repo[row["repo"]] = per_repo.get(row["repo"], 0) + 1
    assert per_repo, "nothing was pruned at all"
    for repo, count in per_repo.items():
        assert count <= _resolve(repo, policy_data)["prune_cap"], repo


def _best_reclaim(runs: list[list[dict]], cap: int) -> int:
    """Most bytes the cap can reclaim from these runs, recomputed here.

    A plain forward table over the runs, which is a different formulation from
    anything the pipeline can be doing, so agreement is evidence rather than
    the same routine twice.
    """
    best = [0] * (cap + 1)
    for run in runs:
        sums, running = [0], 0
        for row in reversed(run):
            running += int(row["size_bytes"])
            sums.append(running)
        nxt = list(best)
        for capacity in range(cap + 1):
            for take in range(1, min(len(sums) - 1, capacity) + 1):
                value = best[capacity - take] + sums[take]
                nxt[capacity] = max(nxt[capacity], value)
        best = nxt
    return best[cap]


def test_prune_selection_reclaims_the_most_the_cap_allows(primary_outputs):
    """The reclaimed bytes must equal the attainable optimum, per repo."""
    _, _, _, decisions = primary_outputs
    policy_data = _load_json(POLICY_PATH)
    runs_by_repo = _repo_runs(decisions)
    reclaimed: dict[str, int] = {}
    for row in decisions:
        if row["decision"] == "prune":
            reclaimed[row["repo"]] = reclaimed.get(row["repo"], 0) + int(row["size_bytes"])
    for repo, runs in runs_by_repo.items():
        cap = _resolve(repo, policy_data)["prune_cap"]
        assert reclaimed.get(repo, 0) == _best_reclaim(runs, cap), repo


def test_chain_respecting_greedy_falls_short_of_the_optimum(primary_outputs):
    """A legal greedy really does reclaim less on this inventory.

    If taking whole runs by bytes per snapshot already reached the optimum,
    requiring the optimum would prove nothing here, so the gap is asserted.
    """
    _, _, _, decisions = primary_outputs
    policy_data = _load_json(POLICY_PATH)
    shortfalls = 0
    for repo, runs in _repo_runs(decisions).items():
        cap = _resolve(repo, policy_data)["prune_cap"]
        options = []
        for index, run in enumerate(runs):
            running = 0
            for depth, row in enumerate(reversed(run), start=1):
                running += int(row["size_bytes"])
                options.append((running / depth, depth, running, index))
        options.sort(key=lambda option: -option[0])
        used: set[int] = set()
        remaining, greedy = cap, 0
        for _density, depth, total, index in options:
            if index in used or depth > remaining:
                continue
            used.add(index)
            remaining -= depth
            greedy += total
        if greedy < _best_reclaim(runs, cap):
            shortfalls += 1
    assert shortfalls >= 3, (
        f"the greedy selection matched the optimum on all but {shortfalls} repos"
    )


def test_size_ordered_selection_would_break_chains(primary_outputs):
    """The superseded rule is not merely worse, it is infeasible.

    Taking the largest candidates wherever they sit reports more reclaimed
    bytes than is achievable, which is how a run that ignored the chains
    announces itself.
    """
    _, _, _, decisions = primary_outputs
    policy_data = _load_json(POLICY_PATH)
    for repo, runs in _repo_runs(decisions).items():
        cap = _resolve(repo, policy_data)["prune_cap"]
        everything = sorted(
            (int(row["size_bytes"]) for run in runs for row in run), reverse=True
        )
        assert sum(everything[:cap]) > _best_reclaim(runs, cap), repo


def test_original_snapshot_preserved():
    """The frozen incident snapshot is left byte-identical."""
    assert ORIGINAL_WORKFLOW_PATH.exists()
    digest = hashlib.sha256(ORIGINAL_WORKFLOW_PATH.read_bytes()).hexdigest()
    assert digest == FIXTURE["broken_pipeline_sha256"]


def test_broken_snapshot_is_wrong(tmp_path: Path):
    # Assert only that the frozen broken snapshot DIFFERS from the reference; its
    # exact output is intentionally never pinned.
    """The shipped draft does not reproduce the governed result."""
    _, broken_summary, broken_state, broken_decisions = _run_pipeline(
        tmp_path, script_path=ORIGINAL_WORKFLOW_PATH
    )
    assert broken_summary != FIXTURE["primary"]["summary"]
    assert _digest(broken_decisions) != FIXTURE["primary"]["decisions_digest"]
    assert _digest(broken_state) != FIXTURE["primary"]["state_digest"]


# --------------------------------------------------------------------------
# Generalization / idempotency / CLI
# --------------------------------------------------------------------------
def test_pipeline_rerun_idempotent(tmp_path: Path):
    """Re-running the reconciler on the same inventory produces identical artifacts."""
    _, sa, sta, da = _run_pipeline(tmp_path / "a")
    _, sb, stb, db = _run_pipeline(tmp_path / "b")
    assert (sa, sta, da) == (sb, stb, db)


def test_pipeline_supports_alternate_input(tmp_path: Path):
    """The reconciler generalises to an alternate inventory it has never seen."""
    _, summary, state, decisions = _run_pipeline(tmp_path, input_path=ALT_INPUT)
    assert summary == FIXTURE["alternate"]["summary"]
    assert _digest(state) == FIXTURE["alternate"]["state_digest"]
    assert _digest(decisions) == FIXTURE["alternate"]["decisions_digest"]


def test_cli_defaults_work_and_match_explicit_run(tmp_path: Path):
    """A no-argument run uses the contracted defaults and produces the same summary as an explicit run."""
    _, explicit_summary, _, _ = _run_pipeline(tmp_path)
    # The no-argument run writes to the default /app/output; clear any root-owned artifacts from
    # solve.sh and make the dir candidate-writable so the unprivileged program can populate it.
    default_out = Path("/app/output")
    shutil.rmtree(default_out, ignore_errors=True)
    default_out.mkdir(parents=True, exist_ok=True)
    os.chmod(default_out, 0o777)
    _publish_inputs()
    _run_agent([sys.executable, str(WORKFLOW_PATH)], cwd=_candidate_dir())
    assert sorted(q.name for q in default_out.iterdir()) == [
        "retention_decisions.jsonl", "retention_state.json", "summary.json"]
    _, _, explicit_state, explicit_decisions = _run_pipeline(tmp_path / "again")
    assert _load_json(default_out / "summary.json") == explicit_summary
    assert _digest(_load_json(default_out / "retention_state.json")) == _digest(explicit_state)
    assert _digest(_load_jsonl(default_out / "retention_decisions.jsonl")) == \
        _digest(explicit_decisions)


def test_submitted_program_runs_unprivileged_and_cannot_write_reward(tmp_path: Path):
    """The isolation itself works: code run the way the verifier runs the agent is unprivileged
    (uid 65534) and cannot write the reward path."""
    # Ensure the reward path exists and is root-owned (as it is under test.sh) before probing.
    os.makedirs("/logs/verifier", exist_ok=True)
    reward = Path("/logs/verifier/reward.txt")
    if not reward.exists():
        reward.write_text("0")
    os.chmod("/logs/verifier", 0o755)
    os.chmod(reward, 0o644)
    probe = _candidate_dir() / "probe.py"
    probe.write_text(
        "import os\n"
        "print(os.getuid())\n"
        "open('/logs/verifier/reward.txt', 'w').write('1')\n",
        encoding="utf-8",
    )
    os.chmod(probe, 0o644)
    res = subprocess.run(
        _SETPRIV + [sys.executable, str(probe)],
        capture_output=True, text=True, cwd=str(_CWORK), check=False,
    )
    assert res.stdout.strip().splitlines()[0] == "65534", "submitted program must run as uid 65534"
    assert res.returncode != 0 and "Permission denied" in res.stderr, (
        "unprivileged submitted program must not be able to write the reward path"
    )


# --------------------------------------------------------------------------
# Source-path influence
# --------------------------------------------------------------------------
def test_policy_source_path_affects_output(tmp_path: Path):
    """The retention policy is read from its fixed path at run time, so mutating it changes the output."""
    original = POLICY_PATH.read_text()
    try:
        data = json.loads(original)
        data.setdefault("default", {})
        for field in ("cap_daily", "cap_weekly", "cap_monthly", "cap_yearly"):
            data["default"][field] = 0
        POLICY_PATH.write_text(json.dumps(data, indent=2) + "\n")
        _, summary, _, _ = _run_pipeline(tmp_path / "shifted")
        assert summary != FIXTURE["primary"]["summary"]
        assert summary["kept_count"] < FIXTURE["primary"]["summary"]["kept_count"]
    finally:
        POLICY_PATH.write_text(original)


def test_pin_registry_source_path_affects_output(tmp_path: Path):
    """The pin registry is read from its fixed path at run time, so removing holds changes the output."""
    original = PIN_REGISTRY_PATH.read_text()
    try:
        _, summary_a, _, _ = _run_pipeline(tmp_path / "a")
        PIN_REGISTRY_PATH.write_text("[]\n")
        _, summary_b, _, _ = _run_pipeline(tmp_path / "b")
        assert summary_a["held_count"] > summary_b["held_count"]
        assert summary_b["kept_count"] < summary_a["kept_count"]
    finally:
        PIN_REGISTRY_PATH.write_text(original)


# --------------------------------------------------------------------------
# Policy resolution
# --------------------------------------------------------------------------
def _resolve(repo: str, data: dict) -> dict:
    base = dict(BASELINE)
    base.update({k: int(v) for k, v in data.get("default", {}).items() if k in BASELINE})
    override = data.get("repo_overrides", {}).get(repo)
    if isinstance(override, dict):
        base.update({k: int(v) for k, v in override.items() if k in BASELINE})
    return base


def test_sparse_override_inherits_remaining_fields():
    """A single-field repo override inherits every other field from the baseline."""
    data = json.loads(POLICY_PATH.read_text())
    overrides = data.get("repo_overrides", {})
    sparse = [r for r, o in overrides.items() if len(o) == 1]
    assert sparse, "the shipped policy must exercise a single-field override"
    default_resolved = _resolve("__absent__", data)
    for repo in sparse:
        resolved = _resolve(repo, data)
        named = next(iter(overrides[repo]))
        assert resolved[named] == int(overrides[repo][named])
        for field in POLICY_FIELDS:
            if field != named:
                assert resolved[field] == default_resolved[field]


def test_policy_default_may_omit_fields_and_falls_back_to_baseline():
    """Fields the policy file omits fall back to the governed baseline."""
    data = json.loads(POLICY_PATH.read_text())
    omitted = [f for f in POLICY_FIELDS if f not in data.get("default", {})]
    assert omitted, "the shipped policy must omit at least one field to exercise fallback"
    resolved = _resolve("__absent__", data)
    for field in omitted:
        assert resolved[field] == BASELINE[field]


# --------------------------------------------------------------------------
# Anti-triviality: governance GFS dialect deviates from standard age-based GFS
# --------------------------------------------------------------------------
def _naive_standard_gfs_kept(rows: list[dict], policy: dict) -> set[str]:
    """Standard age-based GFS: keep the LATEST snapshot per naive calendar period
    (midnight day, naive floor weeks/months/years), tiers independent (union),
    pinned holds ignored. This is what a stock GFS scheduler does."""
    caps = {
        "daily": policy["cap_daily"], "weekly": policy["cap_weekly"],
        "monthly": policy["cap_monthly"], "yearly": policy["cap_yearly"],
    }
    periods = {"daily": 86400, "weekly": 604800, "monthly": 2592000, "yearly": 31536000}
    kept: set[str] = set()
    for tier in TIER_ORDER:
        buckets: dict[int, dict] = {}
        for r in rows:
            bid = r["ts"] // periods[tier]
            cur = buckets.get(bid)
            key = (r["ts"], r["size_bytes"], r["snapshot_id"])
            if cur is None or key > (cur["ts"], cur["size_bytes"], cur["snapshot_id"]):
                buckets[bid] = r
        for bid in sorted(buckets, reverse=True)[: max(caps[tier], 0)]:
            kept.add(buckets[bid]["snapshot_id"])
    return kept


def test_standard_gfs_retention_produces_wrong_answers(tmp_path: Path):
    """The governed dialect departs from a textbook grandfather-father-son scheme, so the conventional answer is wrong."""
    rows = [
        {"snapshot_id": "g1", "repo": "gfs-dialect", "vault": "hot",
         "ts": 1735714800, "size_bytes": 3000000000, "pinned": False, "note": "06:00"},
        {"snapshot_id": "g2", "repo": "gfs-dialect", "vault": "hot",
         "ts": 1735725600, "size_bytes": 5000000000, "pinned": False, "note": "10:00"},
        {"snapshot_id": "g3", "repo": "gfs-dialect", "vault": "hot",
         "ts": 1735740000, "size_bytes": 4000000000, "pinned": False, "note": "14:00"},
    ]
    input_path = tmp_path / "gfs.json"
    _write_json(input_path, rows)
    _, _, _, decisions = _run_pipeline(tmp_path / "run", input_path=input_path)
    reconciler_kept = {r["snapshot_id"] for r in decisions if r["decision"] == "keep"}

    policy = _resolve("gfs-dialect", json.loads(POLICY_PATH.read_text()))
    naive_kept = _naive_standard_gfs_kept(rows, policy)

    # The governance dialect keeps the EARLIEST-of-bucket snapshot (g1); a stock
    # keep-latest GFS keeps the LATEST (g3). They must disagree.
    assert reconciler_kept != naive_kept, (
        f"governance retention must deviate from standard GFS "
        f"(reconciler={sorted(reconciler_kept)}, naive={sorted(naive_kept)})"
    )
    assert "g1" in reconciler_kept and "g1" not in naive_kept


# --------------------------------------------------------------------------
# Sources stay operational
# --------------------------------------------------------------------------
def test_governance_log_present():
    """The governance log the rules are reconstructed from is present in the environment."""
    assert LOG_PATH.exists() and LOG_PATH.stat().st_size > 0


def _source_strings(source: str) -> list[str]:
    """Every string literal in the submitted source, read from the parse tree.

    A raw substring scan would reject a correct reconciler that merely mentions
    one of these names in a comment or a docstring.
    """
    tree = ast.parse(source)
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def test_pipeline_does_not_reference_test_artifacts():
    """The reconciler never reads a verifier artifact.

    Only string literals are inspected, so naming one of these in prose is not a
    breach; using one as a path is.
    """
    literals = _source_strings(WORKFLOW_PATH.read_text(encoding="utf-8"))
    for token in ("/tests", "expected_report.json", "alt_snapshots.json"):
        assert not any(token in literal for literal in literals), token


def test_shipped_contract_matches_the_golden_copy():
    """The output contract in the environment is unmodified.

    Field lists, container shapes and sort orders are golden metadata and are read
    from the verifier's own image; this proves the agent's copy still agrees with
    it, so the contract cannot be trimmed to weaken a schema check.
    """
    shipped = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert shipped == json.loads(GOLDEN_CONTRACT_PATH.read_text(encoding="utf-8"))
