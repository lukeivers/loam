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

"""Amendment #28 acceptance tests — workspace-identity-routed first-run.

Each test maps 1:1 to an acceptance criterion in the amendment plan
(docs/rebuild/plans/amendment-28-workspace-identity-routed-first-run.md,
§4). AC10 is the re-extension of amendment #6's AC6 per ODD §4; AC11–14
close the related behaviours the plan objective names.

Test shape mirrors ``test_detachment.py``:

- Workspace trees are ephemeral fixtures under ``tmp_path``.
- ``_run_dispatch`` invokes ``first_run_dispatch.py`` as a real subprocess
  so the file-as-IPC contract (state file read/write, additionalContext
  via stdout) is exercised end to end.
- Fake helpers simulate worker behaviour without running the real
  first-run flow.

The original ``~/.loam/first-run.state`` at amendment #28 moved to
``<workspace>/.pos/first-run.state`` — structural routing by path;
the ``workspace_root`` field in the state content is defence in
depth against a state file being moved or copied by an admin.
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

from first_run_state import (  # noqa: E402
    FirstRunState,
    read_state,
    state_path,
    write_state,
)


# ---- helpers (match test_detachment.py conventions) ----------------


def _fresh_workspace(root: Path, name: str) -> Path:
    """Create an empty workspace fixture with the conventional layout."""
    ws = root / name
    (ws / ".claude").mkdir(parents=True)
    return ws


def _run_dispatch(
    *,
    loam_root: Path,
    pos_root: Path,
    helper: Path,
    python: str = sys.executable,
) -> subprocess.CompletedProcess[str]:
    dispatch = HOOKS_DIR / "first_run_dispatch.py"
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
    )


def _noop_helper(tmp_path: Path) -> Path:
    """A fake worker that exits immediately without touching state.

    Used in tests that need a helper argument but whose assertions do
    not depend on the worker's behaviour — the thing under test is the
    dispatcher's decision, not the worker's action.
    """
    helper = tmp_path / "fake_helper_noop.py"
    helper.write_text(
        "import sys\n"
        "sys.exit(0)\n"
    )
    helper.chmod(0o755)
    return helper


def _recording_helper(tmp_path: Path, log_name: str = "helper_spawn.log") -> Path:
    """A fake worker that records its ``--loam-root`` argument to a file.

    AC10 asserts the dispatcher spawned the worker with the correct
    workspace; reading the recorded argv is the deterministic way to
    verify that in a subprocess context.
    """
    helper = tmp_path / "fake_helper_recording.py"
    log = tmp_path / log_name
    helper.write_text(
        "import sys, argparse\n"
        "from pathlib import Path\n"
        "p = argparse.ArgumentParser()\n"
        "p.add_argument('--loam-root')\n"
        "p.add_argument('--mode')\n"
        "p.add_argument('--pos-root')\n"
        "p.add_argument('--generation', type=int, default=1)\n"
        "a, _ = p.parse_known_args()\n"
        f"log = Path({str(log)!r})\n"
        "with log.open('a') as fh:\n"
        "    fh.write(a.loam_root + '\\n')\n"
    )
    helper.chmod(0o755)
    return helper


def _wait_for_file(path: Path, timeout_s: float = 3.0) -> bool:
    """Poll until *path* exists or the timeout elapses."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if path.exists():
            return True
        time.sleep(0.05)
    return path.exists()


# ---- AC10 — end-to-end multi-workspace dispatch ---------------------


def test_AC10_dispatch_for_second_workspace_spawns_worker_not_completed(
    tmp_path: Path,
) -> None:
    """AC10 — re-extension of AC6.

    Workspace A (``alpha``) has completed first-run; workspace B
    (``beta``) shares the same host pos-root. A fresh dispatch for B
    does NOT emit ``_msg_completed()``; it spawns a worker whose
    ``--loam-root`` argument is B.
    """
    alpha = _fresh_workspace(tmp_path, "alpha")
    beta = _fresh_workspace(tmp_path, "beta")
    pos_root = tmp_path / ".pos"

    # Seed alpha with a completed state.
    write_state(
        FirstRunState(status="completed", pid=os.getpid()),
        alpha,
    )
    # D-migration D.2 (amendment #63): workspace-state under
    # <workspace>/workspace/.pos/ post-D.2.
    assert (alpha / "workspace" / ".pos" / "first-run.state").exists()

    # Dispatch for beta with a recording helper.
    helper = _recording_helper(tmp_path)
    log = tmp_path / "helper_spawn.log"
    proc = _run_dispatch(loam_root=beta, pos_root=pos_root, helper=helper)

    assert proc.returncode == 0
    # Return text is the fresh-start message for beta.
    assert proc.stdout.startswith("Your pos-v2 workspace is installing."), (
        f"dispatch for beta should have been fresh-spawn, got: "
        f"{proc.stdout[:200]!r}"
    )
    # The worker recorded that it was invoked with beta as its
    # --loam-root, not alpha.
    assert _wait_for_file(log), (
        "recording helper never wrote its spawn log — worker was not "
        "spawned for beta"
    )
    recorded = log.read_text().strip().splitlines()
    assert recorded, "recording helper log is empty"
    assert recorded[-1] == str(beta), (
        f"dispatcher spawned worker with the wrong --loam-root: "
        f"expected {beta!s}, got {recorded[-1]!r}"
    )

    # Alpha's state file was not touched by beta's dispatch.
    alpha_state = read_state(alpha)
    assert alpha_state is not None
    assert alpha_state.status == "completed", (
        "beta's dispatch must not modify alpha's state"
    )


# ---- AC11 — state artefact carries workspace identity ---------------


def test_AC11_foreign_workspace_state_is_treated_as_absent(
    tmp_path: Path,
) -> None:
    """AC11 — state whose recorded workspace is foreign is fresh-spawn.

    Construct a state artefact inside beta whose ``workspace_root``
    field names ``alpha`` (simulating a file copied by an admin or
    a path moved after writing). A dispatch for beta must not
    short-circuit via Case 2; the dispatcher's defence-in-depth check
    treats the foreign-content state as absent.
    """
    alpha = _fresh_workspace(tmp_path, "alpha")
    beta = _fresh_workspace(tmp_path, "beta")
    pos_root = tmp_path / ".pos"

    # Write a state file at beta's path but mark its content as belonging
    # to alpha. The write_state helper auto-fills workspace_root with
    # the resolved workspace_root parameter; to simulate the cross-
    # workspace case we post-process the on-disk content.
    write_state(
        FirstRunState(status="completed", pid=os.getpid()),
        beta,
    )
    beta_state_file = state_path(beta)
    content = beta_state_file.read_text()
    # Replace the auto-filled workspace_root with alpha's resolved path.
    import json as _json

    parsed = _json.loads(content)
    parsed["workspace_root"] = str(alpha.resolve())
    beta_state_file.write_text(_json.dumps(parsed, sort_keys=True) + "\n")

    helper = _recording_helper(tmp_path)
    log = tmp_path / "helper_spawn.log"
    proc = _run_dispatch(loam_root=beta, pos_root=pos_root, helper=helper)

    assert proc.returncode == 0
    assert proc.stdout.startswith("Your pos-v2 workspace is installing."), (
        f"foreign-workspace state must be treated as absent; got: "
        f"{proc.stdout[:200]!r}"
    )
    # Worker was spawned for beta.
    assert _wait_for_file(log)
    recorded = log.read_text().strip().splitlines()
    assert recorded[-1] == str(beta)


# ---- AC12 — self-workspace recognition preserved --------------------


def test_AC12_self_workspace_completed_state_short_circuits(
    tmp_path: Path,
) -> None:
    """AC12 — regression: when the recorded workspace matches, Case 2
    still fires and emits the completion message.

    This backstops AC11: the defence-in-depth check must not reject
    legitimate self-workspace state.
    """
    alpha = _fresh_workspace(tmp_path, "alpha")
    pos_root = tmp_path / ".pos"

    # Write a completed state for alpha; write_state auto-fills
    # workspace_root with alpha's resolved path.
    write_state(
        FirstRunState(status="completed", pid=os.getpid()),
        alpha,
    )

    helper = _recording_helper(tmp_path)
    log = tmp_path / "helper_spawn.log"
    proc = _run_dispatch(loam_root=alpha, pos_root=pos_root, helper=helper)

    assert proc.returncode == 0
    # The completion message names "completed" or "ready".
    lowered = proc.stdout.lower()
    assert "completed" in lowered or "ready" in lowered, (
        f"self-workspace completed state should short-circuit to the "
        f"completion message; got: {proc.stdout[:200]!r}"
    )
    # And the worker must NOT have been spawned.
    # Small wait window to catch a racing spawn.
    time.sleep(0.3)
    assert not log.exists(), (
        "Case 2 short-circuit must not spawn a worker"
    )


# ---- AC13 — corrupt / unparseable state is fresh-spawn --------------


def test_AC13_corrupt_state_falls_through_to_fresh_spawn(
    tmp_path: Path,
) -> None:
    """AC13 — malformed JSON is treated as absent by the dispatcher.

    The dispatcher's Case 2 must not fire on unparseable bytes; the
    fresh-spawn path runs instead.
    """
    alpha = _fresh_workspace(tmp_path, "alpha")
    pos_root = tmp_path / ".pos"

    # Write garbage to the state path (mkdir parent first because
    # state_path returns <workspace>/.pos/first-run.state).
    state_file = state_path(alpha)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("{not valid json, truncated...")

    helper = _recording_helper(tmp_path)
    log = tmp_path / "helper_spawn.log"
    proc = _run_dispatch(loam_root=alpha, pos_root=pos_root, helper=helper)

    assert proc.returncode == 0
    assert proc.stdout.startswith("Your pos-v2 workspace is installing."), (
        f"corrupt state must be treated as absent; got: "
        f"{proc.stdout[:200]!r}"
    )
    assert _wait_for_file(log)
    recorded = log.read_text().strip().splitlines()
    assert recorded[-1] == str(alpha)


# ---- AC14 — silent-death detection is per workspace -----------------


def test_AC14_silent_death_detection_does_not_cross_workspaces(
    tmp_path: Path,
) -> None:
    """AC14 — dispatch for B does not flip A's state to failed.

    Seed alpha with a stale ``running`` state (dead pid, old
    ``updated_at``). Dispatch for beta. Assert:
      - alpha's state is byte-identical before and after (not
        touched).
      - beta's fresh-spawn path ran (its own worker was launched).
    """
    alpha = _fresh_workspace(tmp_path, "alpha")
    beta = _fresh_workspace(tmp_path, "beta")
    pos_root = tmp_path / ".pos"

    # Seed alpha with a stale 'running' state — pid 0 is guaranteed-
    # dead for the liveness check; updated_at is also stale.
    stale_updated_at = time.time() - 600.0
    alpha_state = FirstRunState(
        status="running",
        pid=0,
        started_at=stale_updated_at,
        updated_at=stale_updated_at,
        phase="phase-3b-shared-deps",
        generation=1,
    )
    write_state(alpha_state, alpha)
    alpha_state_file = state_path(alpha)
    alpha_bytes_before = alpha_state_file.read_bytes()

    helper = _recording_helper(tmp_path)
    log = tmp_path / "helper_spawn.log"
    proc = _run_dispatch(loam_root=beta, pos_root=pos_root, helper=helper)

    assert proc.returncode == 0
    # Beta's dispatch went fresh-spawn.
    assert proc.stdout.startswith("Your pos-v2 workspace is installing."), (
        f"beta's dispatch must go fresh-spawn regardless of alpha's "
        f"stale state; got: {proc.stdout[:200]!r}"
    )
    assert _wait_for_file(log)
    recorded = log.read_text().strip().splitlines()
    assert recorded[-1] == str(beta)

    # Alpha's state file is byte-identical — beta's dispatch must NOT
    # have invoked mark_failed_silently on alpha.
    alpha_bytes_after = alpha_state_file.read_bytes()
    assert alpha_bytes_after == alpha_bytes_before, (
        "alpha's state file was modified by beta's dispatch — silent-"
        "death diagnosis crossed workspace boundaries"
    )
