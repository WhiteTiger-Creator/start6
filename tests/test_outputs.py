"""Verifier tests for the backup / storage retention reconciler task."""

from __future__ import annotations

import ast
import hashlib
import itertools
import json
import os
import shutil
import stat
import subprocess
import tempfile
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


def _file_sha256(path: Path) -> str:
    """Digest of a file's raw bytes.

    instruction.md promises the operational inputs come back *byte*-identical, so
    a parsed-content comparison is not enough: it would accept a reformat or a key
    reorder that the sentence rules out.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


RUNTIME_BUDGET_SECONDS = 120
# Documented wall-clock budget for one full run on the graded inventory.
# instruction.md and report_spec.json state the same number. The reference reads
# each protection-window overlap off ordered endpoints and finishes in a few
# seconds; comparing every pair inside a repository is quadratic in its size and
# cannot finish. Kept as a literal here (never read from the mutable /app spec)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path):
    """Read a contracted JSONL artifact, taking every line as written.

    Skipping blank lines here softened a contract that says one compact object
    per line: a run that padded its output with empty lines read back the same
    as a clean one and scored full marks. A blank line is a malformed line and
    is read as one.
    """
    text = Path(path).read_text(encoding="utf-8")
    if not text:
        return []
    assert text.endswith("\n"), f"{Path(path).name} has no trailing newline"
    lines = text.split("\n")[:-1]
    for number, line in enumerate(lines, start=1):
        assert line.strip(), f"{Path(path).name} line {number} is blank"
    return [json.loads(line) for line in lines]


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


# --- verifier execution isolation -------------------------------------------------
# The submitted /app/workflow/reconcile_retention.py is untrusted once the separate verifier runs
# it. We execute it under an unprivileged UID (65534 / nobody) via setpriv, so it cannot write the
# reward path, read the held-out fixtures under /tests, or interfere with the verifier. Inputs are
# staged into a candidate-writable work area; policy files under /app keep their fixed paths.
_CWORK = Path("/candidate-work")
_run_ctr = itertools.count()
CANDIDATE_UID = 65534
def _setpriv_prefix(base: list) -> list:
    """The strictest setpriv invocation this image actually supports.

    Dropping the uid is not the whole of it: a candidate that kept inheritable
    or bounding-set capabilities could regain privilege across an exec. The two
    flags are probed rather than assumed, because a util-linux without them
    would make every run fail on the flag rather than on the task.
    """
    strict = base + ["--inh-caps=-all", "--bounding-set=-all"]
    try:
        probe = subprocess.run(strict + ["/bin/true"], capture_output=True, timeout=30)
        if probe.returncode == 0:
            return strict
    except (OSError, subprocess.SubprocessError):
        pass
    return base


# Resource ceilings for anything run as the candidate. Deliberately not
# RLIMIT_AS or RLIMIT_DATA: a language runtime that reserves a large virtual
# arena at start-up dies under those, so they would kill a correct program
# rather than a runaway one. These bound the failure modes that actually escape
# a process group -- forking without end, filling the disk, dumping core.
_CANDIDATE_NPROC = 512
_CANDIDATE_FSIZE = 512 * 1024 * 1024
_CANDIDATE_NOFILE = 1024


def _apply_rlimits() -> None:
    """Run in the child between fork and exec: own session, plus ceilings."""
    import resource

    for what, limit in (
        (resource.RLIMIT_NPROC, _CANDIDATE_NPROC),
        (resource.RLIMIT_FSIZE, _CANDIDATE_FSIZE),
        (resource.RLIMIT_NOFILE, _CANDIDATE_NOFILE),
        (resource.RLIMIT_CORE, 0),
    ):
        try:
            _soft, hard = resource.getrlimit(what)
            ceiling = limit if hard == resource.RLIM_INFINITY else min(limit, hard)
            resource.setrlimit(what, (ceiling, ceiling))
        except (ValueError, OSError):
            continue
    os.setsid()


def _pids_owned_by(uid: int) -> list:
    """Every live pid whose owner is `uid`, read from /proc."""
    pids = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            if os.stat("/proc/" + entry).st_uid == uid:
                pids.append(int(entry))
        except OSError:
            continue
    return pids


def reap_candidate_uid(uid: int = CANDIDATE_UID) -> None:
    """Kill everything still running as the candidate, whatever group it is in.

    Killing the process group is not enough on its own: a submitted program can
    call setsid and leave its own group, and would then survive into later tests
    -- holding the staged inputs of the next run, or still writing into an
    output directory being read. Ownership is the property that cannot be
    escaped, so the sweep is by owner.
    """
    import signal as _signal
    import time as _time

    for _ in range(50):
        pids = _pids_owned_by(uid)
        if not pids:
            return
        for pid in pids:
            try:
                os.kill(pid, _signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                continue
        for pid in pids:
            try:
                os.waitpid(pid, os.WNOHANG)
            except (ChildProcessError, OSError):
                continue
        _time.sleep(0.02)


_SETPRIV = _setpriv_prefix(["setpriv", "--reuid=65534", "--regid=65534", "--clear-groups", "--no-new-privs"])
# The contract's own budget, enforced rather than documented: a run that
# compares protection windows pairwise on these repos does not come back
# inside it, and a timeout here is a failure exactly as the contract says.

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
        # Never chmod through a link. The agent writes under /app/data, so a link
        # planted there would otherwise have root widen its TARGET -- and a link
        # pointing into /tests would reopen the sealed fixtures to the uid the
        # graded program runs as, handing it the expected answers. is_symlink()
        # stats the link itself; os.chmod's follow_symlinks=False is not available
        # on Linux, which has no lchmod, and raises NotImplementedError instead.
        if path.is_symlink():
            continue
        try:
            os.chmod(path, 0o755 if path.is_dir() else 0o644)
        except OSError:
            pass
    if not DATA_DIR.is_symlink():
        try:
            os.chmod(DATA_DIR, 0o755)
        except OSError:
            pass
    # The reconciler itself is agent-produced too, and the graded run reads it as
    # uid 65534. An atomic write leaves it mode 0600 and owned by root --
    # tempfile.mkstemp creates exactly that -- so without this a correct solution
    # that installed its program the careful way would be unreadable at grade time
    # and fail every test for a reason nothing in the task states.
    for path in (WORKFLOW_PATH.parent, WORKFLOW_PATH):
        if path.is_symlink():
            continue
        try:
            os.chmod(path, 0o755 if path.is_dir() else 0o644)
        except OSError:
            pass


def test_no_cleanup_in_this_suite_sits_after_a_return():
    """A statement after a return never runs, and one such slip hid a real gap.

    The owner-wide reap in _run_agent was written after its return, so it never
    executed and processes a candidate left behind survived between runs. This
    walks the suite's own parse tree so the same slip cannot come back quietly.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    stranded = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for index, statement in enumerate(node.body[:-1]):
            if isinstance(statement, (ast.Return, ast.Raise)):
                after = node.body[index + 1]
                stranded.append(f"{node.name}() line {after.lineno}")
    assert not stranded, f"unreachable statements: {stranded}"


def test_data_dir_is_read_only_to_the_graded_reconciler():
    """The reconciler cannot write under /app/data, and says so when it tries.

    _publish_inputs leaves /app/data root-owned before the graded program drops to
    uid 65534, so a reconciler that folds the recovery into its own run and
    rewrites snapshots.json dies on PermissionError. Without this test that
    failure surfaces as a couple of dozen unrelated errors with nothing naming the
    cause; instruction.md states the constraint and this pins it with a readable
    message.
    """
    _publish_inputs()
    probe_dir = Path("/probe-work")
    probe_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(probe_dir, 0o755)
    probe = probe_dir / "write_data.py"
    probe.write_text(
        "import sys\n"
        "try:\n"
        "    open('/app/data/snapshots.json', 'a').close()\n"
        "    print('writable')\n"
        "except PermissionError:\n"
        "    print('refused')\n",
        encoding="utf-8")
    os.chmod(probe, 0o644)
    result = subprocess.run(
        _SETPRIV + [sys.executable, str(probe)],
        capture_output=True, text=True, cwd=str(probe_dir), check=False)
    # the verdict is taken root-side from the directory itself, not from what the
    # probe chose to print: a subprocess's stdout is the wrong place to learn
    # whether a permission holds, since the thing under test could shape it
    mode = DATA_DIR.stat().st_mode
    assert not (mode & stat.S_IWOTH), (
        f"/app/data is world-writable ({stat.filemode(mode)}), so a reconciler "
        "that rebuilds the inventory in its own run would be graded as correct")
    assert DATA_DIR.stat().st_uid == 0, "/app/data is not root-owned"
    for entry in sorted(DATA_DIR.iterdir()):
        emode = entry.stat().st_mode
        assert not (emode & stat.S_IWOTH), (
            f"{entry.name} is world-writable ({stat.filemode(emode)})")
    # The probe corroborates the same boundary from the candidate's own side. It
    # is deliberately NOT an equality against what the probe printed: a value the
    # graded side produces is the wrong thing to decide a permission on, so the
    # stat above is the verdict and this only refuses the one word that would
    # mean the write went through.
    assert result.returncode == 0, result.stderr[-2000:]
    assert "writable" not in result.stdout, (
        "the graded reconciler can write under /app/data, so an engine that "
        "rebuilds the inventory in its own run would be graded as correct "
        f"instead of refused: {result.stdout!r}")


def test_a_reconciler_that_rewrites_the_inventory_fails_readably():
    """Folding the recovery into the reconciler fails, and names why.

    This is the trap the instruction now warns about, exercised end to end: a
    reconciler whose first act is to rewrite /app/data/snapshots.json is run the
    way the graded one is, and must fail with PermissionError naming that path
    rather than producing artifacts.
    """
    _publish_inputs()
    work = _candidate_dir()
    rogue = work / "rewrites_the_inventory.py"
    rogue.write_text(
        "import json, pathlib\n"
        "rows = json.loads(pathlib.Path('/app/data/snapshots.json').read_text())\n"
        "pathlib.Path('/app/data/snapshots.json').write_text(json.dumps(rows))\n"
        "print('rewrote the inventory')\n",
        encoding="utf-8")
    os.chmod(rogue, 0o644)
    result = subprocess.run(
        _SETPRIV + [sys.executable, str(rogue)],
        capture_output=True, text=True, cwd=str(work), check=False)
    assert result.returncode != 0, (
        "a reconciler rewriting /app/data/snapshots.json was allowed to; the "
        "recovery is the first step's write, not the reconciler's")
    assert "PermissionError" in result.stderr, result.stderr[-2000:]
    assert "/app/data/snapshots.json" in result.stderr, result.stderr[-2000:]


def test_publishing_inputs_does_not_chmod_through_a_planted_link():
    """A link under /app/data cannot make root widen what it points at.

    _publish_inputs runs as root over a directory the agent controls, so a link
    planted there and aimed at /tests would otherwise have the sealed fixtures
    opened to the unprivileged uid the graded program runs as. Written as a live
    attempt rather than an inspection of the loop, so it keeps holding if the
    loop is rewritten.
    """
    target = EXPECTED_FIXTURE
    target_dir = target.parent
    before_file = target.stat().st_mode
    before_dir = target_dir.stat().st_mode

    planted_file = DATA_DIR / "planted-link.json"
    planted_dir = DATA_DIR / "planted-dir-link"
    for link in (planted_file, planted_dir):
        if link.is_symlink() or link.exists():
            link.unlink()
    planted_file.symlink_to(target)
    planted_dir.symlink_to(target_dir)
    try:
        _publish_inputs()
        assert target.stat().st_mode == before_file, (
            "root chmod followed a planted link and widened a sealed fixture")
        assert target_dir.stat().st_mode == before_dir, (
            "root chmod followed a planted link and widened the fixture directory")
        assert planted_file.is_symlink() and planted_dir.is_symlink()
    finally:
        for link in (planted_file, planted_dir):
            if link.is_symlink() or link.exists():
                link.unlink()

    # And the fixtures are still out of reach of the uid the graded program uses.
    probe_dir = Path("/probe-work")
    probe_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(probe_dir, 0o755)
    probe = probe_dir / "read_fixture.py"
    probe.write_text(
        "import sys\n"
        "try:\n"
        "    open(sys.argv[1]).read()\n"
        "    print('readable')\n"
        "except OSError:\n"
        "    print('unreadable')\n",
        encoding="utf-8")
    os.chmod(probe, 0o644)
    result = subprocess.run(
        _SETPRIV + [sys.executable, str(probe), str(target)],
        capture_output=True, text=True, cwd=str(probe_dir), check=False)
    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.strip() == "unreadable", (
        f"the sealed fixture is readable to the candidate uid: {result.stdout!r}")


def _candidate_dir() -> Path:
    """A fresh work area for one graded run, created where nothing can pre-empt it.

    /candidate-work is world-writable, so a predictable name here was an opening:
    a submission could plant `run-7` as a symlink to /tests/fixtures and wait. The
    next root-side mkdir(exist_ok=True) would succeed through the link and the
    chmod that follows would open the sealed fixtures to the candidate uid, since
    os.chmod resolves symlinks and Linux offers no lchmod to stop it. mkdtemp
    fixes both halves: the name is unpredictable and the directory is created
    fresh or not at all, never adopted from something already sitting there.
    """
    d = Path(tempfile.mkdtemp(prefix=f"run-{next(_run_ctr)}-", dir=str(_CWORK)))
    assert not d.is_symlink(), d
    os.chmod(d, 0o777)
    return d


def _run_agent(argv, cwd: Path):
    """Run the submitted program under the unprivileged candidate UID with a scrubbed environment.

    The owner-wide reap runs in a finally block. It sat after the return, where
    it never executed, so a candidate that left a process behind was cleared only
    by the sweep test.sh does at the very end rather than between runs.
    """
    try:
        return subprocess.run(
            _SETPRIV + argv, check=True, capture_output=True, text=True, cwd=str(cwd),
            env=dict(_CANDIDATE_ENV),
            preexec_fn=_apply_rlimits,
            # report_spec.json publishes runtime_budget_seconds and the suite never
            # enforced it, so a reconciler comparing protection windows pairwise ran
            # until the whole verifier timed out rather than failing on its own run.
            # This is a hard kill on the budget, not a measurement of elapsed time.
            timeout=RUNTIME_BUDGET_SECONDS,
        )
    finally:
        reap_candidate_uid()


def _stage_input(src: Path, dst: Path) -> None:
    """Copy `src` to `dst` as a regular file, never through a link.

    The default input is /app/data/snapshots.json, the one path under /app/data
    the agent is told to replace, and staging runs as root. shutil.copy follows
    the source link, so a submission that left a symlink there instead of a
    rebuilt inventory pointed root at whatever it named -- the sealed fixtures
    under /tests included -- and had the contents laid down at 0644 inside the
    candidate's own work area, where the graded program reads it. O_NOFOLLOW
    refuses the link at the final component and the fstat refuses anything that
    is not a regular file.
    """
    try:
        handle = os.open(str(src), os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise AssertionError(
            f"{src} could not be staged as a regular file: {exc}") from exc
    try:
        info = os.fstat(handle)
        assert stat.S_ISREG(info.st_mode), (
            f"{src} is not a regular file, so it is not staged")
        payload = b""
        while True:
            chunk = os.read(handle, 1 << 20)
            if not chunk:
                break
            payload += chunk
    finally:
        os.close(handle)
    dst.write_bytes(payload)
    os.chmod(dst, 0o644)


def _run_pipeline(tmp_path: Path, script_path: Path = WORKFLOW_PATH, input_path: Path = DEFAULT_INPUT):
    _publish_inputs()
    work = _candidate_dir()
    out_dir = work / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(out_dir, 0o777)
    staged_input = work / "input.json"
    _stage_input(Path(input_path), staged_input)
    result = _run_agent(
        [sys.executable, str(script_path), "--input", str(staged_input), "--output-dir", str(out_dir)],
        cwd=work,
    )
    assert result.returncode == 0, (
        f"the run exited {result.returncode}\n"
        f"stdout: {result.stdout[-2000:]}\nstderr: {result.stderr[-2000:]}")
    summary = _load_json(out_dir / "summary.json")
    state = _load_json(out_dir / "retention_state.json")
    decisions = _load_jsonl(out_dir / "retention_decisions.jsonl")
    return out_dir, summary, state, decisions


@pytest.fixture(scope="session", autouse=True)
def _clear_the_default_output_dir():
    """Empty /app/output before anything is graded.

    solve.sh leaves a correct summary.json, retention_state.json and
    retention_decisions.jsonl sitting at the default path. Every graded run is
    given an explicit --output-dir, so a reconciler that derived nothing could
    copy those three across instead and match the sealed fixtures. Clearing the
    directory up front means there is nothing there to copy: the artifacts a run
    is graded on have to come from the input it was handed. The later
    CLI-defaults test rebuilds the directory for its own no-argument run.
    """
    default_out = Path("/app/output")
    shutil.rmtree(default_out, ignore_errors=True)
    default_out.mkdir(parents=True, exist_ok=True)
    os.chmod(default_out, 0o777)


@pytest.fixture(scope="session")
def primary_outputs(tmp_path_factory):
    return _run_pipeline(tmp_path_factory.mktemp("primary"))


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
    the bounds check above, so the two are required to differ somewhere. How
    often they differ, and how many distinct depths the graded data happens to
    produce, are properties of this inventory rather than of #RET-7180; the
    figure itself is checked against an independent sweep in the test below.
    """
    _, _, _, decisions = primary_outputs
    differing = [d["snapshot_id"] for d in decisions
                 if d["peak_depth"] != d["overlap_count"] + 1]
    assert differing, (
        "peak_depth equals overlap_count + 1 on every row, so the busiest instant "
        "inside each window was never computed")


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

    # the smallest repo alone leaves a bug confined to the larger ones to the
    # digest check; the largest and a middling one are recomputed here too
    ranked = sorted(by_repo, key=lambda name: len(by_repo[name]))
    sampled = {ranked[0], ranked[-1], ranked[len(ranked) // 2]}
    for repo in sorted(sampled):
        # protection_days is a resolved policy value, not the baseline: two repos
        # override it, and using the wrong span here would compare two different
        # figures rather than checking the pipeline.
        span = int(_resolve(repo, json.loads(POLICY_PATH.read_text()))["protection_days"]) * 86400
        rows = sorted(by_repo[repo], key=lambda r: r["ts"])
        starts = sorted(r["ts"] for r in rows)
        checked = 0
        # each sampled row sweeps the whole repo, so the sample shrinks as the
        # repo grows: the point is independent evidence on repos of every size,
        # and the sealed digest already covers every row of every repo
        take = 40 if len(rows) <= 400 else 8
        for row in rows[:: max(1, len(rows) // take)][:take]:
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
        assert checked >= 5


def test_overlap_matches_an_independent_recomputation(primary_outputs):
    """Recounted here pairwise, which shares no code with the pipeline.

    #RET-7172 counts the OTHER canonical snapshots of the same repo whose
    protection window intersects this one, endpoints included. Counting the
    intersections directly on a sampled repo is evidence, where the previous
    form only asked for more than fifty distinct values across the inventory --
    a property of the graded data that no decision states.
    """
    _, _, _, decisions = primary_outputs
    by_repo: dict[str, list[dict]] = {}
    for row in decisions:
        by_repo.setdefault(row["repo"], []).append(row)

    # the smallest repo alone leaves a bug confined to the larger ones to the
    # digest check; the largest and a middling one are recomputed here too
    ranked = sorted(by_repo, key=lambda name: len(by_repo[name]))
    sampled = {ranked[0], ranked[-1], ranked[len(ranked) // 2]}
    for repo in sorted(sampled):
        span = int(_resolve(repo, json.loads(POLICY_PATH.read_text()))["protection_days"]) * 86400
        rows = sorted(by_repo[repo], key=lambda r: r["ts"])
        checked = 0
        for row in rows[:: max(1, len(rows) // 40)][:40]:
            low, high = row["ts"], row["ts"] + span
            expected = sum(
                1 for other in rows
                if other["snapshot_id"] != row["snapshot_id"]
                and other["ts"] <= high and low <= other["ts"] + span
            )
            assert row["overlap_count"] == expected, (
                f"{row['snapshot_id']}: reported {row['overlap_count']}, counted {expected}")
            checked += 1
        assert checked, "no decision was checked"
        # and the figure is not a constant the engine never actually computed
        assert len({d["overlap_count"] for d in decisions}) > 1


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
    """The operational inputs a run reads come back byte-identical.

    instruction.md names the catalogue, the replay journal, the retention policy
    and the pin registry as files a run must leave alone, so all four are checked,
    and checked over their raw bytes rather than their parsed content.
    """
    byte_digests = FIXTURE["input_bytes_sha256"]
    assert _file_sha256(CATALOGUE_PATH) == byte_digests["snapshot_catalogue_pre_incident.json"]
    assert _file_sha256(JOURNAL_PATH) == byte_digests["snapshot_replay_journal.json"]
    assert _file_sha256(POLICY_PATH) == byte_digests["retention_policy.json"]
    assert _file_sha256(PIN_REGISTRY_PATH) == byte_digests["pin_registry.json"]
    # instruction.md names the contract among the files that come back byte for
    # byte unchanged; the golden comparison beside this one is satisfied by any
    # file that merely parses the same, so the raw bytes are checked here too
    assert _file_sha256(SPEC_PATH) == byte_digests["report_spec.json"]
    # The parsed digests stay as a second, redundant reading of the same promise.
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
def test_cli_exists(primary_outputs):
    """The reconciler is present and honours the options it is required to keep.

    Existence alone would pass a program that had dropped either option. The
    graded run is made with an explicit --input and --output-dir, so requiring
    its artifacts to be in that destination rather than the documented default
    shows both options were read.
    """
    assert WORKFLOW_PATH.exists()
    out_dir, _, _, _ = primary_outputs
    assert out_dir != Path("/app/output"), "the graded run must use the directory it was given"
    assert _everything_under(out_dir) == CONTRACT_OUTPUT_NAMES


CONTRACT_OUTPUT_NAMES = [
    "retention_decisions.jsonl", "retention_state.json", "summary.json"]


def _everything_under(out_dir: Path) -> list[str]:
    """Every entry in the output directory, directories included, recursively.

    These checks used to filter on is_file(), which let a run drop an extra
    directory beside the three contracted artifacts and still be graded as
    having written exactly three files. Nothing is filtered here, so a stray
    cache/ or a file hidden inside one is caught.
    """
    return sorted(str(q.relative_to(out_dir)) for q in out_dir.rglob("*"))


def test_output_dir_contains_exactly_three_files(primary_outputs):
    """A run writes exactly the three contracted files and nothing else."""
    out_dir, _, _, _ = primary_outputs
    assert _everything_under(out_dir) == CONTRACT_OUTPUT_NAMES


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


def test_the_artifacts_carry_their_keys_in_the_order_the_contract_states(
        primary_outputs):
    """Key order, read off the raw bytes rather than a parsed structure.

    Every other check here parses first, and parsing throws key order away, so a
    run emitting the right values in any order it liked matched every fixture.
    The contract fixes three orders and none of them is alphabetical, so sorting
    the keys is as wrong as shuffling them.
    """
    out = Path(primary_outputs[0])

    raw = (out / "summary.json").read_text(encoding="utf-8")
    ordered = json.loads(raw, object_pairs_hook=list)
    assert [key for key, _ in ordered] == SPEC["summary_json"]["required_fields"], (
        "summary.json does not carry its keys in the order required_fields lists")
    counts = dict(ordered)["decision_counts"]
    assert [key for key, _ in counts] == SPEC["summary_json"]["decision_counts_key_order"], (
        "decision_counts does not carry its keys in the documented order")
    assert raw.endswith("\n") and not raw.endswith("\n\n")
    assert "\n  \"" in raw, "summary.json is not written at a two-space indent"

    raw = (out / "retention_state.json").read_text(encoding="utf-8")
    ordered = json.loads(raw, object_pairs_hook=list)
    repos = [key for key, _ in ordered]
    assert repos == sorted(repos), "the state's repos are not in ascending order"
    expected = SPEC["retention_state_json"]["required_fields"]
    for repo, entry in ordered:
        assert [key for key, _ in entry] == expected, (
            f"{repo} does not carry its keys in the order required_fields lists")
    assert raw.endswith("\n") and not raw.endswith("\n\n")

    # the rebuilt inventory is the one place the report orders do not apply
    raw = DEFAULT_INPUT.read_text(encoding="utf-8")
    records = json.loads(raw, object_pairs_hook=list)
    # read from the contract rather than repeated here, so the rule the test
    # enforces and the rule the agent can read are the same string
    source_order = SPEC["inventory_source"]["record_field_order"]
    assert source_order == ["snapshot_id", "repo", "vault", "ts", "size_bytes",
                            "pinned", "note"], "the contract's stated order moved"
    # every record, not a leading sample: a run that got the order right for the
    # first two hundred and wrong afterwards passed the old form
    for number, record in enumerate(records, start=1):
        assert [key for key, _ in record] == source_order, (
            f"inventory record {number} does not carry the source field order")

    # inventory_source states the layout too, and nothing asserted it, so an
    # inventory with the right content at the wrong indent passed every check
    stated = SPEC["inventory_source"]["serialisation"]
    assert "two-space indent" in stated and "trailing newline" in stated, stated
    assert raw.endswith("\n") and not raw.endswith("\n\n"), (
        "the rebuilt inventory does not end in exactly one newline")
    assert raw == json.dumps(json.loads(raw), indent=2) + "\n", (
        "the rebuilt inventory is not the two-space indent inventory_source states")


def test_the_contracted_orders_are_not_alphabetical():
    """Otherwise the test above would pass on a run that simply sorted its keys."""
    for listed in (SPEC["summary_json"]["required_fields"],
                   SPEC["summary_json"]["decision_counts_key_order"],
                   SPEC["retention_state_json"]["required_fields"],
                   SPEC["inventory_source"]["record_field_order"]):
        assert listed != sorted(listed), listed


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
        # a blank line is not skipped here: the contract says one compact
        # object per line, so an empty one is a malformed line
        assert line.strip(), "the queue carries a blank line"
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


def _tie_inventory() -> list:
    """One repo, one vault, holding two candidate runs of identical shape.

    Each cluster sits inside a single day, so only its bucket representative is
    kept and the rest become candidates; the two clusters are far enough apart to
    fall in different buckets at every tier, so each run has its own kept anchor.
    The two runs carry the same sizes in the same order, so a cut of any depth
    into one reclaims exactly what the same cut into the other does, with the
    same snapshot count. That is the tie #RET-7184 settles, and the graded
    inventory never produces one.
    """
    rows = []

    def cluster(prefix, first_ts):
        # four snapshots inside one day: the earliest is the representative
        for i, size in enumerate((100_000_000, 500_000_000, 400_000_000, 300_000_000)):
            rows.append({"snapshot_id": f"snap-tie-{prefix}{i}", "repo": "vault/tie",
                         "vault": "hot", "ts": first_ts + i * 3600, "size_bytes": size,
                         "pinned": False, "note": "tie probe"})

    base = 1_780_000_000
    cluster("a", base - 400 * 86400)
    cluster("b", base - 200 * 86400)
    return rows


def test_the_prune_tie_break_decides_which_run_gives_way(tmp_path: Path):
    """#RET-7184: level on bytes and on count, the EARLIER run gives way, deepest first.

    Nothing graded this. Reversing the run order, or taking the shallowest cut
    that still reaches the optimum, reproduced every sealed digest, so the rule
    could be read either way and still pass. Here the two runs are identical in
    shape and the cap admits only one of them, so which snapshots are pruned is
    decided by the tie-break alone.
    """
    original = POLICY_PATH.read_text()
    try:
        data = json.loads(original)
        # a cap that covers one run and not both, so the tie has to be settled
        data.setdefault("repo_overrides", {})["vault/tie"] = {"prune_cap": 3}
        POLICY_PATH.write_text(json.dumps(data, indent=2) + "\n")

        staged = tmp_path / "tie_inventory.json"
        staged.parent.mkdir(parents=True, exist_ok=True)
        _write_json(staged, _tie_inventory())
        os.chmod(staged, 0o644)
        _, _summary, _state, decisions = _run_pipeline(tmp_path / "tie", input_path=staged)
    finally:
        POLICY_PATH.write_text(original)

    pruned = {r["snapshot_id"] for r in decisions if r["decision"] == "prune"}
    assert pruned, "the probe pruned nothing, so the tie-break was never reached"
    assert len(pruned) <= 3, f"the per-repo cap was not applied: {sorted(pruned)}"
    runs = _repo_runs(decisions).get("vault/tie", [])
    assert len(runs) >= 2, f"the probe did not produce two runs to choose between: {runs}"

    earlier = {row["snapshot_id"] for row in runs[0]}
    later = {row["snapshot_id"] for row in runs[1]}
    from_earlier, from_later = len(earlier & pruned), len(later & pruned)
    assert from_earlier > from_later, (
        "the cap was spent on the later run, so the earlier one did not give way "
        f"first: {from_earlier} from the earlier against {from_later} from the later")


def test_chain_respecting_greedy_falls_short_of_the_optimum(primary_outputs):
    """A legal greedy really does reclaim less on this inventory.

    This guards the shipped data rather than the submission: if taking whole
    runs by bytes per snapshot already reached the optimum everywhere, then
    requiring the optimum would prove nothing and the crux would be gone. One
    repo where the greedy falls short is what makes the requirement bite, so
    that is what is asserted -- the previous form demanded three, a count no
    decision states and only true of this particular inventory.
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
    assert shortfalls >= 1, (
        "the chain-respecting greedy reached the optimum on every repo, so requiring "
        "the optimum no longer distinguishes it from a heuristic"
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


def test_a_run_derives_its_artifacts_rather_than_copying_the_delivered_ones(tmp_path: Path):
    """The graded artifacts have to come from the input, not from /app/output.

    solve.sh leaves a correct set of artifacts at the default path, and every
    graded run is given an explicit --output-dir, so copying the three files
    across would have matched every sealed fixture without reconciling anything.
    The session clears that directory before grading; this plants decoys in it
    and requires the run to disagree with them, which fails a copy however it is
    spelled.
    """
    default_out = Path("/app/output")
    decoys = {
        "summary.json": '{"schema_version": "decoy"}\n',
        "retention_state.json": '{"decoy": true}\n',
        "retention_decisions.jsonl": '{"decoy":true}\n',
    }
    try:
        default_out.mkdir(parents=True, exist_ok=True)
        os.chmod(default_out, 0o777)
        for name, body in decoys.items():
            path = default_out / name
            path.write_text(body, encoding="utf-8")
            os.chmod(path, 0o644)

        _, summary, state, decisions = _run_pipeline(tmp_path / "not_a_copy")
        assert summary == FIXTURE["primary"]["summary"], "the run did not reconcile its own summary"
        assert _digest(state) == FIXTURE["primary"]["state_digest"]
        assert _digest(decisions) == FIXTURE["primary"]["decisions_digest"]
        assert summary.get("schema_version") != "decoy"
    finally:
        shutil.rmtree(default_out, ignore_errors=True)
        default_out.mkdir(parents=True, exist_ok=True)
        os.chmod(default_out, 0o777)


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
    assert _everything_under(default_out) == CONTRACT_OUTPUT_NAMES
    _, _, explicit_state, explicit_decisions = _run_pipeline(tmp_path / "again")
    assert _load_json(default_out / "summary.json") == explicit_summary
    assert _digest(_load_json(default_out / "retention_state.json")) == _digest(explicit_state)
    assert _digest(_load_jsonl(default_out / "retention_decisions.jsonl")) == \
        _digest(explicit_decisions)


def test_staging_the_run_input_does_not_follow_a_planted_link():
    """The inventory sits on the one /app/data path the agent replaces, and staging runs as root.

    Every graded run copies /app/data/snapshots.json into the candidate's own
    work area. That copy followed the source link, so a submission that left a
    symlink there instead of a rebuilt inventory pointed root at whatever it
    named -- the sealed fixtures under /tests included -- and had the contents
    laid down at 0644 where the graded program reads them. Staging now refuses
    anything that is not a regular file, and this plants the link to prove it.
    """
    sentinel = Path("/tests/fixtures/expected_report.json")
    if not sentinel.exists():
        sentinel = SPEC_PATH
    original = DEFAULT_INPUT.read_bytes()
    mode = DEFAULT_INPUT.stat().st_mode & 0o7777
    try:
        DEFAULT_INPUT.unlink()
        DEFAULT_INPUT.symlink_to(sentinel)
        staged = _candidate_dir() / "input.json"
        with pytest.raises(AssertionError):
            _stage_input(DEFAULT_INPUT, staged)
        assert not staged.exists(), (
            "the planted link was staged anyway, so its target is now readable "
            "at the path the graded program is handed")
    finally:
        if DEFAULT_INPUT.is_symlink() or DEFAULT_INPUT.exists():
            DEFAULT_INPUT.unlink()
        DEFAULT_INPUT.write_bytes(original)
        os.chmod(DEFAULT_INPUT, mode)
    assert DEFAULT_INPUT.read_bytes() == original


def test_a_run_leaves_its_artifacts_where_it_wrote_them():
    """instruction.md says the three files are left there rather than cleared away.

    Every other check here reads the artifacts straight after the run that made
    them, so a reconciler that wrote them and then tidied up on its way out
    satisfied all of them. This runs once, then looks at the directory again
    after the process has exited and the work area has been swept.
    """
    out_dir, _, _, _ = _run_pipeline(_candidate_dir())
    reap_candidate_uid()
    survivors = sorted(q.name for q in out_dir.iterdir())
    assert survivors == ["retention_decisions.jsonl", "retention_state.json",
                         "summary.json"], (
        f"the run did not leave its three artifacts behind: {survivors}")
    for name in survivors:
        assert (out_dir / name).stat().st_size > 0, f"{name} was left empty"


def test_submitted_program_runs_unprivileged_and_cannot_write_reward(tmp_path: Path):
    """The isolation itself works: code run the way the verifier runs the agent is unprivileged
    (uid 65534) and cannot write the reward path."""
    os.makedirs("/logs/verifier", exist_ok=True)
    reward = Path("/logs/verifier/reward.txt")
    if not reward.exists():
        reward.write_text("0")
    # The channel's modes are left exactly as test.sh set them: this asserts the
    # isolation that is really in force rather than relaxing it to be measured.
    #
    # The probe lives in a root-owned directory the candidate uid can read and
    # execute but not write, so nothing the graded program left behind in the
    # shared work area can stand in for it.
    probe_dir = Path("/probe-work")
    probe_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(probe_dir, 0o755)
    probe = probe_dir / "probe.py"
    probe.write_text(
        "import os\n"
        "print(os.getuid())\n"
        "try:\n"
        "    open('/logs/verifier/reward.txt').read()\n"
        "    print('readable')\n"
        "except OSError:\n"
        "    print('unreadable')\n"
        "try:\n"
        "    open('/logs/verifier/reward.txt', 'w').write('1')\n"
        "    print('writable')\n"
        "except OSError:\n"
        "    print('unwritable')\n",
        encoding="utf-8",
    )
    os.chmod(probe, 0o644)
    res = subprocess.run(
        _SETPRIV + [sys.executable, str(probe)],
        capture_output=True, text=True, cwd=str(probe_dir), check=False,
    )
    assert res.returncode == 0, res.stderr[-2000:]
    assert res.stdout.splitlines() == ["65534", "unreadable", "unwritable"], res.stdout


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
def test_the_runtime_budget_is_published_and_is_what_a_run_is_held_to():
    """report_spec.json states a budget, and nothing tied the suite to it.

    The comments in this file described a budget being enforced while every
    graded run was launched with no deadline at all, so a reconciler comparing
    protection windows pairwise ran until the whole verifier timed out rather
    than failing on its own run. The constant here is the one _run_agent kills
    at, and this pins it to the number the agent can read.
    """
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert spec["runtime_budget_seconds"] == RUNTIME_BUDGET_SECONDS, (
        "the published budget and the one a graded run is held to disagree: "
        f"{spec['runtime_budget_seconds']} against {RUNTIME_BUDGET_SECONDS}")
    assert "runtime_budget_seconds" in spec["runtime_budget_note"], (
        "the note beside the budget does not say a run is held to it")


def test_governance_log_present():
    """The governance log the rules are reconstructed from is present in the environment."""
    assert LOG_PATH.exists() and LOG_PATH.stat().st_size > 0


def test_shipped_contract_matches_the_golden_copy():
    """The output contract in the environment is unmodified.

    Field lists, container shapes and sort orders are golden metadata and are read
    from the verifier's own image; this proves the agent's copy still agrees with
    it, so the contract cannot be trimmed to weaken a schema check.
    """
    assert json.loads(SPEC_PATH.read_text(encoding="utf-8")) == json.loads(
        GOLDEN_CONTRACT_PATH.read_text(encoding="utf-8"))
    # instruction.md promises this file comes back byte-identical too, not merely
    # equal once parsed.
    assert _file_sha256(SPEC_PATH) == _file_sha256(GOLDEN_CONTRACT_PATH)

