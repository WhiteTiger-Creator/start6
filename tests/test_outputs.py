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
POLICY_PATH = Path("/app/data/retention_policy.json")
PIN_REGISTRY_PATH = Path("/app/data/pin_registry.json")
SPEC_PATH = Path("/app/docs/report_spec.json")
LOG_PATH = Path("/app/incident/retention_governance_log.md")
EXPECTED_FIXTURE = Path("/tests/fixtures/expected_report.json")
ALT_INPUT = Path("/tests/fixtures/alt_snapshots.json")

TIER_ORDER = ["daily", "weekly", "monthly", "yearly"]
DECISION_ORDER = ["keep", "prune", "defer"]
CLASS_RANK = {"prune": 0, "defer": 1, "keep": 2}

FIXTURE = json.loads(EXPECTED_FIXTURE.read_text())
SPEC = json.loads(SPEC_PATH.read_text())

POLICY_FIELDS = ("cap_daily", "cap_weekly", "cap_monthly", "cap_yearly", "quota_cap", "prune_cap")
BASELINE = {
    "cap_daily": 7, "cap_weekly": 4, "cap_monthly": 6, "cap_yearly": 2,
    "quota_cap": 100000, "prune_cap": 3,
}
SNAPSHOT_FIELDS = ("snapshot_id", "repo", "vault", "ts", "size_bytes", "pinned", "note")

DECISION_KEYS = set(SPEC["retention_decisions_jsonl"]["required_fields"])
STATE_KEYS = set(SPEC["retention_state_json"]["required_fields"])
SUMMARY_KEYS = set(SPEC["summary_json"]["required_fields"])


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
_RUN_TIMEOUT = 300

# The submitted program gets a minimal explicit environment rather than inheriting the verifier's
# (PATH/PYTHONPATH/CI variables and any other grader context).
_CANDIDATE_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/candidate-work", "LANG": "C.UTF-8"}


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


# --------------------------------------------------------------------------
# Step 1: the truncated snapshot inventory must be recovered in place
# --------------------------------------------------------------------------
def _naive_concatenation() -> list[dict]:
    """The superseded draft merge: catalogue then journal, bookkeeping fields left on."""
    inventory = [dict(r) for r in _load_json(CATALOGUE_PATH)]
    inventory.extend(dict(e) for e in _load_json(JOURNAL_PATH))
    return inventory


def test_recovery_sources_are_intact():
    assert _load_json(CATALOGUE_PATH) == FIXTURE["catalogue"]
    assert _load_json(JOURNAL_PATH) == FIXTURE["journal"]


def test_snapshot_inventory_recovered():
    """/app/data/snapshots.json shipped truncated; it must hold the recovered inventory."""
    recovered = _load_json(DEFAULT_INPUT)
    assert isinstance(recovered, list)
    assert recovered == FIXTURE["recovered_inventory"]


def test_recovered_records_carry_no_journal_bookkeeping():
    for record in _load_json(DEFAULT_INPUT):
        assert set(record) == set(SNAPSHOT_FIELDS)


def test_shipped_and_naive_inventories_differ_from_the_recovered_one():
    """The recovery is real work: neither the truncated file nor the draft merge match."""
    expected = FIXTURE["recovered_inventory"]
    assert FIXTURE["shipped_truncated_inventory"] != expected
    assert _load_json(CATALOGUE_PATH) != expected
    assert _naive_concatenation() != expected


def test_reconciler_output_depends_on_the_recovered_inventory(tmp_path: Path):
    """Even a correctly repaired reconciler emits wrong artifacts on a wrongly merged inventory."""
    for label, inventory in (
        ("truncated", FIXTURE["shipped_truncated_inventory"]),
        ("catalogue_only", _load_json(CATALOGUE_PATH)),
        ("naive_concatenation", _naive_concatenation()),
    ):
        bad_input = tmp_path / f"{label}.json"
        _write_json(bad_input, inventory)
        _, summary, state, decisions = _run_pipeline(tmp_path / label, input_path=bad_input)
        assert summary != FIXTURE["primary"]["summary"], label
        assert (state, decisions) != (
            FIXTURE["primary"]["state"], FIXTURE["primary"]["decisions"]
        ), label


# --------------------------------------------------------------------------
# Step 2: the reconciler output contract
# --------------------------------------------------------------------------
def test_cli_exists():
    assert WORKFLOW_PATH.exists()


def test_output_dir_contains_exactly_three_files(primary_outputs):
    out_dir, _, _, _ = primary_outputs
    names = sorted(p.name for p in out_dir.iterdir() if p.is_file())
    assert names == ["retention_decisions.jsonl", "retention_state.json", "summary.json"]


def test_primary_summary_matches_fixture(primary_outputs):
    _, summary, _, _ = primary_outputs
    assert summary == FIXTURE["primary"]["summary"]


def test_primary_state_matches_fixture(primary_outputs):
    _, _, state, _ = primary_outputs
    assert state == FIXTURE["primary"]["state"]


def test_primary_decisions_matches_fixture(primary_outputs):
    _, _, _, decisions = primary_outputs
    assert decisions == FIXTURE["primary"]["decisions"]


def test_summary_schema(primary_outputs):
    _, summary, _, _ = primary_outputs
    assert set(summary) == SUMMARY_KEYS
    assert summary["schema_version"] == SPEC["summary_json"]["schema_version"]
    assert list(summary["decision_counts"]) == DECISION_ORDER


def test_state_schema_and_sorting(primary_outputs):
    _, _, state, _ = primary_outputs
    assert list(state) == sorted(state)
    for entry in state.values():
        assert set(entry) == STATE_KEYS
        for key in (*TIER_ORDER, "pinned"):
            assert entry[key] == sorted(entry[key])
        assert isinstance(entry["kept_count"], int)
        assert isinstance(entry["quota_used"], int)


def test_decisions_required_fields_and_compact(primary_outputs):
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
    _, _, _, decisions = primary_outputs
    assert decisions == sorted(
        decisions,
        key=lambda r: (
            CLASS_RANK[r["decision"]], -r["size_bytes"], r["ts"], r["repo"], r["snapshot_id"]
        ),
    )


def test_decision_counts_enumerate_all_three(primary_outputs):
    _, summary, _, decisions = primary_outputs
    counts = {d: 0 for d in DECISION_ORDER}
    for row in decisions:
        counts[row["decision"]] += 1
    assert summary["decision_counts"] == counts
    assert set(summary["decision_counts"]) == set(DECISION_ORDER)
    assert counts["keep"] > 0 and counts["prune"] > 0 and counts["defer"] > 0


def test_summary_math_consistency(primary_outputs):
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
def test_original_snapshot_preserved():
    assert ORIGINAL_WORKFLOW_PATH.exists()
    digest = hashlib.sha256(ORIGINAL_WORKFLOW_PATH.read_bytes()).hexdigest()
    assert digest == FIXTURE["broken_pipeline_sha256"]


def test_broken_snapshot_is_wrong(tmp_path: Path):
    # Assert only that the frozen broken snapshot DIFFERS from the reference; its
    # exact output is intentionally never pinned.
    _, broken_summary, broken_state, broken_decisions = _run_pipeline(
        tmp_path, script_path=ORIGINAL_WORKFLOW_PATH
    )
    assert broken_summary != FIXTURE["primary"]["summary"]
    assert broken_decisions != FIXTURE["primary"]["decisions"]
    assert broken_state != FIXTURE["primary"]["state"]


# --------------------------------------------------------------------------
# Generalization / idempotency / CLI
# --------------------------------------------------------------------------
def test_pipeline_rerun_idempotent(tmp_path: Path):
    _, sa, sta, da = _run_pipeline(tmp_path / "a")
    _, sb, stb, db = _run_pipeline(tmp_path / "b")
    assert (sa, sta, da) == (sb, stb, db)


def test_pipeline_supports_alternate_input(tmp_path: Path):
    _, summary, state, decisions = _run_pipeline(tmp_path, input_path=ALT_INPUT)
    assert summary == FIXTURE["alternate"]["summary"]
    assert state == FIXTURE["alternate"]["state"]
    assert decisions == FIXTURE["alternate"]["decisions"]


def test_cli_defaults_work_and_match_explicit_run(tmp_path: Path):
    _, explicit_summary, _, _ = _run_pipeline(tmp_path)
    # The no-argument run writes to the default /app/output; clear any root-owned artifacts from
    # solve.sh and make the dir candidate-writable so the unprivileged program can populate it.
    default_out = Path("/app/output")
    shutil.rmtree(default_out, ignore_errors=True)
    default_out.mkdir(parents=True, exist_ok=True)
    os.chmod(default_out, 0o777)
    _run_agent([sys.executable, str(WORKFLOW_PATH)], cwd=_candidate_dir())
    assert _load_json(default_out / "summary.json") == explicit_summary


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
# Anti-delegation: static AST ban on dataframe / date-library engines
# --------------------------------------------------------------------------
def test_reconciler_does_not_import_banned_engines():
    tree = ast.parse(WORKFLOW_PATH.read_text(encoding="utf-8"))
    banned = set(SPEC["workflow_repair"]["prohibited_imports"])
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    offending = banned & found
    assert not offending, f"reconciler must not delegate to a dataframe/date engine: {offending}"


def test_ast_check_catches_datetime_importing_engine(tmp_path: Path):
    """The AST ban is real: a datetime-importing calendar delegate is detected."""
    shim = tmp_path / "delegating_engine.py"
    shim.write_text("import datetime\n\n\ndef run(a, b):\n    return datetime.datetime.utcfromtimestamp(a)\n")
    tree = ast.parse(shim.read_text())
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "datetime" in imported
    assert "datetime" in set(SPEC["workflow_repair"]["prohibited_imports"])


# --------------------------------------------------------------------------
# Sources stay operational
# --------------------------------------------------------------------------
def test_governance_log_present():
    assert LOG_PATH.exists() and LOG_PATH.stat().st_size > 0


def test_pipeline_does_not_reference_test_artifacts():
    code = WORKFLOW_PATH.read_text(encoding="utf-8")
    for token in ("/tests", "expected_report.json", "alt_snapshots.json"):
        assert token not in code
