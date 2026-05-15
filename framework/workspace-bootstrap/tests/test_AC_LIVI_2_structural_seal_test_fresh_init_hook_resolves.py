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

"""AC.LIVI.2 — a seal-test drives the REAL scaffolded SessionStart hook
command against a freshly-bootstrapped workspace and fails RED if
either hook resolves to a non-existent / non-importing interpreter — so
a future regression that re-breaks fresh-init hook resolution is caught
by the seal suite, NOT by a downstream spike.

Plan: docs/plans/loam-init-framework-venv-or-robust-interpreter.md
Ladders to AC.PO.2 (harness toolkit — "the scaffolded hooks actually
work on a fresh init" becomes a CI-caught invariant, not a thing
discovered by a downstream spike).

Quality bar (structural over advisory): the gap ALREADY silently
regressed once — the predecessor amendment sealed GREEN while the
fresh-init hooks were dead, because its seal-test verified IDENTITY
binding (loam_root == the canonical repo, which has a .venv), not hook
interpreter resolution on a documented-Quickstart fresh-clone topology
(where <ws>/framework/.venv did not exist). This test closes that
exact regression vector:
  - the POSITIVE guarantee: a real fresh bootstrap's scaffolded hook
    command runs (exit 0, non-empty emission);
  - the RED-ON-REGRESSION proof: a deliberately-broken-interpreter
    mutation of the scaffolded command makes the SAME assertion RED —
    demonstrating the guard actually catches the regression rather
    than passing vacuously.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

LOAM_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def sealed_fresh_workspace(
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    """A real fresh bootstrap from real canonical (documented-Quickstart
    topology). Module-scoped: the real venv install is the heavy step;
    amortise it across this file's assertions."""
    from loam.workspace_bootstrap.new_workspace import (
        bootstrap_new_workspace,
    )

    base = tmp_path_factory.mktemp("livi2")
    ws = base / "ws"
    bootstrap_new_workspace(
        new_ws_path=ws,
        canonical_source=str(LOAM_ROOT),
        service_bootstrap=False,
        service_manager_dir_override=base / "LaunchAgents",
    )
    return ws


def _scaffolded_hook_commands(ws: Path) -> list[str]:
    settings = json.loads(
        (ws / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    cmds = [
        h["command"]
        for entry in settings["hooks"]["SessionStart"]
        for h in entry["hooks"]
    ]
    assert cmds, "no SessionStart hook commands scaffolded"
    return cmds


def _run_hook(command: str, *, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(  # noqa: S602 — scaffolded command, test
        command,
        shell=True,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=90,
    )


def _hook_resolves(command: str, *, cwd: Path) -> bool:
    """The structural predicate the seal-test enforces: a scaffolded
    hook command 'resolves' iff it does NOT exit 127 (interpreter /
    entrypoint not found) AND emits a non-empty session-start
    context. This is the EXACT predicate that was silently false on a
    fresh init before this amendment."""
    proc = _run_hook(command, cwd=cwd)
    return proc.returncode != 127 and bool(proc.stdout.strip())


def test_AC_LIVI_2_structural_guard_passes_on_a_real_fresh_init(
    sealed_fresh_workspace: Path,
) -> None:
    """POSITIVE guarantee: every scaffolded SessionStart hook command on
    a real fresh-init workspace resolves (NOT 127, non-empty emit)."""
    for cmd in _scaffolded_hook_commands(sealed_fresh_workspace):
        proc = _run_hook(cmd, cwd=sealed_fresh_workspace)
        assert proc.returncode != 127, (
            f"REGRESSION: fresh-init hook resolves to a non-existent / "
            f"non-importing interpreter (exit 127). cmd={cmd!r} "
            f"stderr={proc.stderr.strip()[-500:]!r}"
        )
        assert proc.returncode == 0 and proc.stdout.strip(), (
            f"fresh-init hook did not emit session-start context "
            f"(exit {proc.returncode}). cmd={cmd!r} "
            f"stderr={proc.stderr.strip()[-500:]!r}"
        )


def test_AC_LIVI_2_red_on_regression_broken_interpreter_mutation(
    sealed_fresh_workspace: Path,
) -> None:
    """RED-ON-REGRESSION proof (the structural-guarantee proof per plan
    §4): mutate the scaffolded hook command so its interpreter points
    at a non-existent venv python — the SAME ``_hook_resolves``
    predicate the positive guard uses must go FALSE. This proves the
    guard catches the regression rather than passing vacuously (a
    guard that cannot fail is advisory, not structural)."""
    cmds = _scaffolded_hook_commands(sealed_fresh_workspace)

    # Sanity: unmutated command resolves (the guard's TRUE branch).
    assert _hook_resolves(cmds[0], cwd=sealed_fresh_workspace), (
        "precondition: the unmutated scaffolded hook must resolve"
    )

    # Mutate: swap the real venv python for a non-existent interpreter
    # path — exactly the shape the pre-amendment fresh-init produced
    # (a hook command naming <ws>/framework/.venv/bin/python that does
    # not exist).
    real_venv_python = str(
        sealed_fresh_workspace / "framework" / ".venv" / "bin" / "python"
    )
    broken_python = str(
        sealed_fresh_workspace
        / "framework"
        / ".venv-does-not-exist"
        / "bin"
        / "python"
    )
    mutated = cmds[0].replace(real_venv_python, broken_python, 1)
    assert mutated != cmds[0], (
        "mutation precondition: the scaffolded command must reference "
        f"the venv python {real_venv_python!r} so it can be broken"
    )

    # The guard MUST go RED (False) on the broken interpreter.
    assert not _hook_resolves(mutated, cwd=sealed_fresh_workspace), (
        "the structural guard passed on a deliberately-broken "
        "interpreter — it is advisory, not structural, and cannot "
        "catch the regression it exists to catch"
    )


def test_AC_LIVI_2_guard_is_the_real_hook_command_not_a_proxy(
    sealed_fresh_workspace: Path,
) -> None:
    """The guard executes the REAL ``command`` string Claude Code would
    run from settings.json — not a re-derived/proxy invocation. This is
    why the predecessor's seal-test missed the gap (it asserted on the
    envelope shape + identity, never executing the hook command on a
    fresh-clone topology)."""
    settings_path = (
        sealed_fresh_workspace / ".claude" / "settings.json"
    )
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    raw_commands = [
        h["command"]
        for entry in settings["hooks"]["SessionStart"]
        for h in entry["hooks"]
    ]
    # The commands executed by the guard are byte-identical to what
    # Claude Code reads out of settings.json (no test-side rewriting).
    for cmd in raw_commands:
        proc = _run_hook(cmd, cwd=sealed_fresh_workspace)
        assert proc.returncode == 0, (
            f"the literal settings.json hook command failed "
            f"(exit {proc.returncode}): {cmd!r}"
        )
