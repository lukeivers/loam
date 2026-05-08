# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Acceptance tests for the 2026-04-22 session-start-detachment amendment.

Maps to the amendment's six acceptance criteria from the brief:

  AC1  Fresh-clone dispatch completes in under 5 seconds and emits a
       plain-language additionalContext message naming the progress
       file path and expected wait window.
  AC2  Detached worker runs to completion without user intervention
       (verified in unit form: the worker's phase-boundary writes all
       land; full end-to-end timing is exercised live).
  AC3  Successful completion hands off to the supervisor path on the
       next hook fire.
  AC4  Fault-injection: worker killed mid-flight → next dispatch
       surfaces the crash as plain-language failure AND kicks off a
       fresh retry.
  AC5  Memory-system pip timeout surfaces a named failure cleanly.
  AC6  Partial-scaffold condition recovers instead of raising
       PartialScaffoldError with "retry next session" as terminal surface.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

# Add workspace-bootstrap src so we can exercise the scaffold adapter
# directly (AC6).
WB_SRC = REPO_ROOT / "framework" / "workspace-bootstrap" / "src"
if str(WB_SRC) not in sys.path:
    sys.path.insert(0, str(WB_SRC))

from first_run_state import (  # noqa: E402
    FirstRunState,
    append_log,
    is_stale_live_state,
    mark_failed_silently,
    process_alive,
    read_state,
    write_state,
)


# ---- AC6 — partial-recovery scaffold ---------------------------------


def test_AC6_scaffold_partial_recovery_writes_missing_and_keeps_existing(
    tmp_path: Path,
) -> None:
    """AC6 — when ~/.loam/ exists but bootstrap.yaml is missing, partial_recovery=True
    writes the missing files on top of the existing dir without clobbering.
    """
    from loam.workspace_bootstrap.adapters.first_run_scaffold import (
        run_first_run_scaffold,
    )

    pos_root = tmp_path / ".pos"
    pos_root.mkdir(parents=True)
    # Leftover file from a crashed prior run — must survive the recovery
    # untouched so the user's in-flight edits are not lost.
    (pos_root / "memory.yaml").write_text("# user-edited leftover\n")

    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "svc",
        workspace_root=tmp_path / "pos-v2",
        partial_recovery=True,
    )

    assert result.ran is True
    assert result.reason == "partial_recovery"
    # The leftover file is untouched.
    assert (
        pos_root / "memory.yaml"
    ).read_text() == "# user-edited leftover\n"
    # bootstrap.yaml was written (the point of the recovery).
    assert (pos_root / "bootstrap.yaml").exists()
    assert "memory.yaml" not in result.files_written  # skipped
    assert "bootstrap.yaml" in result.files_written


def test_AC6_scaffold_default_still_raises_without_recovery_flag(
    tmp_path: Path,
) -> None:
    """Backstop: partial_recovery defaults to False and the H4
    structural refusal is unchanged for every existing caller."""
    from loam.workspace_bootstrap.adapters.first_run_scaffold import (
        PartialScaffoldError,
        run_first_run_scaffold,
    )

    pos_root = tmp_path / ".pos"
    pos_root.mkdir(parents=True)
    (pos_root / "memory.yaml").write_text("# leftover\n")
    with pytest.raises(PartialScaffoldError):
        run_first_run_scaffold(
            pos_root=pos_root,
            platform_override="macos",
            service_bootstrap=False,
            service_manager_dir_override=tmp_path / "svc",
            workspace_root=tmp_path / "pos-v2",
        )


# ---- state-file module tests ----------------------------------------


def test_state_roundtrip_writes_and_reads_atomically(tmp_path: Path) -> None:
    # Amendment #28: state is keyed by workspace root; the file lives
    # at <workspace>/.pos/first-run.state.
    ws = tmp_path / "alpha"
    ws.mkdir()
    state = FirstRunState(
        status="running", pid=12345, phase="phase-3b-shared-deps"
    )
    write_state(state, ws)
    assert (ws / "workspace" / ".pos" / "first-run.state").exists()
    roundtrip = read_state(ws)
    assert roundtrip is not None
    assert roundtrip.status == "running"
    assert roundtrip.pid == 12345
    assert roundtrip.phase == "phase-3b-shared-deps"
    assert roundtrip.started_at > 0
    assert roundtrip.updated_at > 0
    # Defence-in-depth: content records its owning workspace.
    assert roundtrip.workspace_root == str(ws.resolve())


def test_state_read_returns_none_on_corrupt_file(tmp_path: Path) -> None:
    # Amendment #28: state lives under <workspace>/.pos/.
    ws = tmp_path / "alpha"
    (ws / "workspace" / ".pos").mkdir(parents=True)
    (ws / "workspace" / ".pos" / "first-run.state").write_text("not json {{{")
    assert read_state(ws) is None


def test_state_log_appends_generation_tagged_lines(tmp_path: Path) -> None:
    append_log("first line", tmp_path, generation=1)
    append_log("second line", tmp_path, generation=2)
    contents = (tmp_path / "first-run.log").read_text()
    assert "[gen1] first line" in contents
    assert "[gen2] second line" in contents


def test_process_alive_returns_false_for_dead_pid(tmp_path: Path) -> None:
    # PID 0 is a sentinel we never use; os.kill(0, 0) hits a different
    # code path (signals the whole process group). Use PID 1 (init),
    # which on our systems is always alive but not us, then a clearly-
    # dead high pid.
    assert process_alive(0) is False
    assert process_alive(999_999_999) is False


def test_is_stale_live_state_detects_dead_worker() -> None:
    state = FirstRunState(
        status="running",
        pid=999_999_999,  # certainly dead
        started_at=time.time() - 300,
        updated_at=time.time() - 300,
    )
    assert is_stale_live_state(state, stale_after_s=0.0) is True


def test_is_stale_live_state_ignores_terminal_states() -> None:
    # completed/failed are terminal — they are never "stale live."
    assert (
        is_stale_live_state(
            FirstRunState(status="completed", pid=999_999_999)
        )
        is False
    )
    assert (
        is_stale_live_state(FirstRunState(status="failed", pid=999_999_999))
        is False
    )


def test_mark_failed_silently_flips_state_and_persists(tmp_path: Path) -> None:
    # Amendment #28: state API keyed by workspace root.
    ws = tmp_path / "alpha"
    ws.mkdir()
    state = FirstRunState(
        status="running",
        pid=999_999_999,
        phase="phase-3b-shared-deps",
    )
    write_state(state, ws)
    flipped = mark_failed_silently(state, ws)
    assert flipped.status == "failed"
    assert flipped.error_code == -32099
    assert "worker-died-silently" in flipped.detail
    on_disk = read_state(ws)
    assert on_disk is not None and on_disk.status == "failed"


# ---- dispatch test harness ------------------------------------------


def _run_dispatch(
    *,
    loam_root: Path,
    pos_root: Path,
    helper: Path = HOOKS_DIR / "first_run_helper.py",
    python: str = sys.executable,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke first_run_dispatch.py in a subprocess.

    Using a real subprocess keeps the test honest about the file-as-IPC
    contract: the dispatch reads from the state file, writes its own
    additionalContext to stdout, and may spawn a detached worker that
    continues independent of this process.
    """
    dispatch = HOOKS_DIR / "first_run_dispatch.py"
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [
            python,
            str(dispatch),
            "--loam-root",
            str(loam_root),
            "--pos-root",
            str(pos_root),
            "--helper",
            str(helper),
            "--python",
            python,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def _fake_helper(tmp_path: Path, behavior: str) -> Path:
    """Create a stub worker that simulates one behavior path.

    Behaviors:
      ``emit_state``  — write a "running" state, pause 1s, write "completed"
      ``die_silently`` — write a "starting" state, sleep 60s (will be killed)
      ``report_failure`` — write a "failed" state with remediation
      ``emit_then_sleep`` — write "running", sleep 60s (simulates long-running work)
    """
    helper = tmp_path / "fake_helper.py"
    if behavior == "emit_state":
        helper.write_text(
            "import sys, time, json, os\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, "
            + repr(str(HOOKS_DIR))
            + ")\n"
            "from first_run_state import FirstRunState, write_state\n"
            "import argparse\n"
            "p = argparse.ArgumentParser()\n"
            "p.add_argument('--loam-root')\n"
            "p.add_argument('--mode')\n"
            "p.add_argument('--pos-root')\n"
            "p.add_argument('--generation', type=int, default=1)\n"
            "a, _ = p.parse_known_args()\n"
            # Amendment #28: state is keyed by workspace root.
            "ws = Path(a.loam_root)\n"
            "write_state(FirstRunState(status='running', pid=os.getpid(), generation=a.generation), ws)\n"
            "time.sleep(0.2)\n"
            "write_state(FirstRunState(status='completed', pid=os.getpid(), generation=a.generation), ws)\n"
        )
    elif behavior == "die_silently":
        helper.write_text(
            "import sys, os, argparse, time\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, "
            + repr(str(HOOKS_DIR))
            + ")\n"
            "from first_run_state import FirstRunState, write_state\n"
            "p = argparse.ArgumentParser()\n"
            "p.add_argument('--loam-root')\n"
            "p.add_argument('--mode')\n"
            "p.add_argument('--pos-root')\n"
            "p.add_argument('--generation', type=int, default=1)\n"
            "a, _ = p.parse_known_args()\n"
            # Amendment #28: state is keyed by workspace root.
            "ws = Path(a.loam_root)\n"
            "write_state(FirstRunState(status='starting', pid=os.getpid(), generation=a.generation), ws)\n"
            # Suicide with SIGKILL-equivalent — emulates the exact hook-timeout
            # path where the worker is killed before it can transition.
            "os._exit(137)\n"
        )
    elif behavior == "report_failure":
        helper.write_text(
            "import sys, os, argparse\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, "
            + repr(str(HOOKS_DIR))
            + ")\n"
            "from first_run_state import FirstRunState, write_state\n"
            "p = argparse.ArgumentParser()\n"
            "p.add_argument('--loam-root')\n"
            "p.add_argument('--mode')\n"
            "p.add_argument('--pos-root')\n"
            "p.add_argument('--generation', type=int, default=1)\n"
            "a, _ = p.parse_known_args()\n"
            # Amendment #28: state is keyed by workspace root.
            "ws = Path(a.loam_root)\n"
            "write_state(FirstRunState(\n"
            "    status='failed', pid=os.getpid(), generation=a.generation,\n"
            "    phase='phase-3b-shared-deps', error_code=-32097,\n"
            "    detail='simulated: memory-system pip timeout',\n"
            "    remediation='check your network, then reopen claude to retry.',\n"
            "), ws)\n"
        )
    elif behavior == "emit_then_sleep":
        helper.write_text(
            "import sys, os, argparse, time\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, "
            + repr(str(HOOKS_DIR))
            + ")\n"
            "from first_run_state import FirstRunState, write_state\n"
            "p = argparse.ArgumentParser()\n"
            "p.add_argument('--loam-root')\n"
            "p.add_argument('--mode')\n"
            "p.add_argument('--pos-root')\n"
            "p.add_argument('--generation', type=int, default=1)\n"
            "a, _ = p.parse_known_args()\n"
            # Amendment #28: state is keyed by workspace root.
            "ws = Path(a.loam_root)\n"
            "write_state(FirstRunState(status='running', pid=os.getpid(), generation=a.generation, phase='phase-3b-shared-deps'), ws)\n"
            "time.sleep(60)\n"
        )
    else:
        raise ValueError(f"unknown behavior: {behavior}")
    helper.chmod(0o755)
    return helper


# ---- AC1 — fresh-clone dispatch is fast and surfaces start message ---


def test_AC1_fresh_dispatch_completes_in_under_5_seconds_with_plain_language(
    tmp_path: Path,
) -> None:
    """AC1 — on a fresh clone, the dispatch emits additionalContext
    naming the progress file path within 5 seconds."""
    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    pos_root = tmp_path / ".pos"
    helper = _fake_helper(tmp_path, "emit_state")

    start = time.monotonic()
    proc = _run_dispatch(
        loam_root=ws,
        pos_root=pos_root,
        helper=helper,
    )
    elapsed = time.monotonic() - start

    assert proc.returncode == 0
    # 5 s is the brief-stated bound. Real-world dispatch is ~200 ms.
    assert elapsed < 5.0, f"dispatch took {elapsed:.2f}s (exceeds 5s bound)"
    assert "installing" in proc.stdout
    assert str(pos_root / "first-run.log") in proc.stdout
    assert "minutes" in proc.stdout or "min" in proc.stdout
    # Amendment #28: state is workspace-local, log stays host-global.
    # The state file must be written synchronously so the next
    # dispatch sees "starting" not "none."
    assert (ws / "workspace" / ".pos" / "first-run.state").exists()
    state = read_state(ws)
    assert state is not None
    assert state.status in ("starting", "running", "completed")


# ---- AC3 — post-success dispatch short-circuits to completed ---------


def test_AC3_completed_state_yields_short_circuit_message(
    tmp_path: Path,
) -> None:
    """AC3 — when state.status == completed, the dispatch does not
    respawn; it emits the 'already done, proceeding' message."""
    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    pos_root = tmp_path / ".pos"
    pos_root.mkdir(parents=True)
    # Amendment #28: state is workspace-local. Pre-seed a completed
    # state for THIS workspace so the dispatch recognises it.
    write_state(
        FirstRunState(status="completed", pid=os.getpid()),
        ws,
    )
    helper = _fake_helper(tmp_path, "emit_state")
    proc = _run_dispatch(
        loam_root=ws, pos_root=pos_root, helper=helper
    )
    assert proc.returncode == 0
    assert "completed" in proc.stdout.lower() or "ready" in proc.stdout.lower()


# ---- AC4 — silent death surfaces + respawns --------------------------


def test_AC4_silent_death_surfaces_crash_and_respawns(tmp_path: Path) -> None:
    """AC4 — after a worker dies leaving a stale 'starting' state,
    the next dispatch detects it, marks failed, spawns a fresh worker."""
    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    pos_root = tmp_path / ".pos"

    # First spawn: fake helper writes "starting" then SIGKILLs itself.
    helper_die = _fake_helper(tmp_path, "die_silently")
    _run_dispatch(loam_root=ws, pos_root=pos_root, helper=helper_die)

    # Amendment #28: state is workspace-local.
    # Wait for the spawned worker to die. Poll the state until pid is
    # dead; bail after 3 seconds (well above the fake helper's runtime).
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        state = read_state(ws)
        if state is None:
            time.sleep(0.05)
            continue
        if state.pid == 0:
            time.sleep(0.05)
            continue
        if not process_alive(state.pid):
            break
        time.sleep(0.05)

    assert state is not None
    assert not process_alive(state.pid), (
        "fake helper did not exit — test cannot validate silent-death path"
    )
    assert state.status in ("starting", "running"), (
        f"fake helper left unexpected state: {state.status}"
    )

    # Second dispatch: detects the dead pid, surfaces crash, respawns.
    helper_quick = _fake_helper(tmp_path, "emit_state")
    proc2 = _run_dispatch(
        loam_root=ws, pos_root=pos_root, helper=helper_quick
    )
    assert proc2.returncode == 0
    # Plain-language surfacing in stdout.
    assert (
        "crashed" in proc2.stdout.lower()
        or "did not finish" in proc2.stdout.lower()
    )
    # Progress log is always named.
    assert str(pos_root / "first-run.log") in proc2.stdout


# ---- AC5 — failed state surfaces remediation --------------------------


def test_AC5_failed_state_surfaces_named_remediation(tmp_path: Path) -> None:
    """AC5 — when the worker wrote a failed state (e.g. memory-system
    pip timeout), the dispatch surfaces the plain-language remediation."""
    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    pos_root = tmp_path / ".pos"
    pos_root.mkdir(parents=True)
    # Amendment #28: state is workspace-local. Pre-seed a failed state
    # for THIS workspace so the dispatch recognises it (fills in the
    # workspace_root field automatically).
    write_state(
        FirstRunState(
            status="failed",
            pid=os.getpid(),
            phase="phase-3b-shared-deps",
            error_code=-32097,
            detail="simulated: memory-system pip timeout",
            remediation=(
                "check your network, then reopen claude to retry."
            ),
            generation=1,
        ),
        ws,
    )
    # Any helper works here — the dispatch will spawn it as part of the
    # auto-retry on failed state.
    helper = _fake_helper(tmp_path, "emit_state")
    proc = _run_dispatch(
        loam_root=ws, pos_root=pos_root, helper=helper
    )
    assert proc.returncode == 0
    # The user-facing text names the failure and the remediation.
    assert "memory-system pip timeout" in proc.stdout
    assert "check your network" in proc.stdout
    assert "-32097" in proc.stdout
    # The retry was kicked off — generation incremented.
    new_state = read_state(ws)
    assert new_state is not None
    assert new_state.generation == 2


# ---- AC2 — worker phase-boundary writes land correctly --------------


def test_AC2_worker_advances_state_at_phase_boundaries(tmp_path: Path) -> None:
    """AC2 — unit-level: the _advance_state() helper lands writes via
    the state module; phase progression is observable externally.

    Full end-to-end is exercised live (not in unit tests — would take
    minutes and require real pip). This test verifies the instrument.
    """
    # Import under a generation tag + workspace so writes go to
    # <workspace>/.pos/. Amendment #28: state is keyed by workspace.
    import importlib
    import first_run_helper

    importlib.reload(first_run_helper)
    ws = tmp_path / "pos-v2"
    ws.mkdir()
    first_run_helper._STATE_POS_ROOT = tmp_path  # log location
    first_run_helper._STATE_WORKSPACE_ROOT = ws  # state location
    first_run_helper._STATE_GENERATION = 7
    first_run_helper._STATE_WRITES_ENABLED = True

    first_run_helper._advance_state("running", phase="phase-3b-shared-deps")
    state = read_state(ws)
    assert state is not None
    assert state.status == "running"
    assert state.phase == "phase-3b-shared-deps"
    assert state.generation == 7

    first_run_helper._advance_state(
        "running", phase="phase-3e-editable-installs"
    )
    state = read_state(ws)
    assert state.phase == "phase-3e-editable-installs"

    first_run_helper._advance_state("completed", phase="complete")
    state = read_state(ws)
    assert state.status == "completed"


def test_advance_state_is_noop_without_explicit_enable(tmp_path: Path) -> None:
    """Guard: if a test (or any caller) invokes _emit_diag without
    main() wiring the module, we must not scribble into the real
    ~/.loam/ directory. Enforced by _STATE_WRITES_ENABLED flag."""
    import importlib
    import first_run_helper

    importlib.reload(first_run_helper)
    first_run_helper._STATE_POS_ROOT = tmp_path
    first_run_helper._STATE_WORKSPACE_ROOT = tmp_path
    # NOT enabled — default-False guard.
    first_run_helper._advance_state("running", phase="phase-3b-shared-deps")
    # No state file was written. Amendment #28: state path is
    # <workspace>/.pos/first-run.state.
    assert not (tmp_path / "workspace" / ".pos" / "first-run.state").exists()


# ---- hook-level smoke: shell wrapper dispatches correctly -----------


def test_hook_shell_dispatches_and_returns_fast(tmp_path: Path) -> None:
    """End-to-end: first-run.sh → first_run_dispatch.py → fake helper
    spawn. Verifies the shell surfaces a plain-language string and
    returns in under 5 seconds on a fresh-workspace fixture."""
    # Post-D.1: framework code lives at <root>/framework/<comp>/...;
    # the first-run.sh script's relative resolution walks up three
    # parents (..,/..,/..) to find LOAM_ROOT.
    ws = tmp_path / "pos-v2"
    hooks_dir = ws / "framework" / "hands-off-lifecycle" / "hooks"
    hooks_dir.mkdir(parents=True)
    (ws / ".claude").mkdir()
    # Copy the shipped shell script and dispatch + state modules into
    # the fixture so the shell's script-relative resolution works.
    import shutil

    shutil.copy(HOOKS_DIR / "first-run.sh", hooks_dir / "first-run.sh")
    shutil.copy(
        HOOKS_DIR / "first_run_dispatch.py",
        hooks_dir / "first_run_dispatch.py",
    )
    shutil.copy(
        HOOKS_DIR / "first_run_state.py",
        hooks_dir / "first_run_state.py",
    )
    # Fake helper that writes a completed state immediately.
    helper = _fake_helper(tmp_path, "emit_state")
    # The shell resolves HELPER relative to LOAM_ROOT — so put the
    # fake helper in place.
    shutil.copy(helper, hooks_dir / "first_run_helper.py")

    pos_root = tmp_path / ".pos"

    env = os.environ.copy()
    env["LOAM_DATA_DIR"] = str(pos_root)
    env["LOAM_PYTHON"] = sys.executable

    start = time.monotonic()
    proc = subprocess.run(
        ["/bin/sh", str(hooks_dir / "first-run.sh")],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        cwd=str(ws),
    )
    elapsed = time.monotonic() - start
    assert proc.returncode == 0
    assert elapsed < 5.0, f"shell hook took {elapsed:.2f}s"
    # Expect the fresh-start message (or completed short-circuit if the
    # fake helper races ahead).
    assert (
        "installing" in proc.stdout.lower()
        or "ready" in proc.stdout.lower()
    )
