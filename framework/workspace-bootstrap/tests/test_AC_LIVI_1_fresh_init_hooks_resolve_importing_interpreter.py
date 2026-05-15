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

"""AC.LIVI.1 — after the documented-Quickstart ``loam init <ws>`` (NO
manual venv-build or hook-fix step inside ``<ws>``), the SessionStart
hook commands written into ``<ws>/.claude/settings.json`` resolve to an
interpreter under which ``loam.primary_persona`` AND the orchestrator
``pos_session_start.py`` are importable — running each hook command
exits 0 (NOT 127) and emits its session-start context.

Plan: docs/plans/loam-init-framework-venv-or-robust-interpreter.md
Ladders to AC.PO.1 (translation-burden — a fresh-init workspace whose
session-start enrichment silently exits 127 is a degraded translation
layer: identity but no memory continuity on turn one).

Verification (outcome-shape; method is the builder's call): drive the
REAL ``bootstrap_new_workspace`` production path against a REAL
canonical clone (the documented-Quickstart clone+install topology — a
stripped fixture canonical cannot satisfy "loam.primary_persona
importable"); extract each SessionStart hook ``command`` from
``<ws>/.claude/settings.json``; run each command; assert exit 0 (NOT
127) and a non-empty session-start emission. No mocks — the predecessor
sealed GREEN against a mocked/stripped topology while the real
fresh-init hooks were dead; this test exercises the real surface so
that cannot recur.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

# The real canonical loam root (this checkout): parents[3] of a tests/
# file == the repo root. The documented Quickstart clones THIS tree;
# bootstrapping `--from` it reproduces the real clone+install topology.
LOAM_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def fresh_init_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Bootstrap one real workspace from real canonical and reuse it
    across the AC.LIVI family (the real bootstrap + venv install is the
    heavy step ~tens of seconds; module scope amortises it).

    Mirrors the documented Quickstart exactly: ``bootstrap_new_workspace
    --from <real canonical>`` with NO manual venv-build or hook-fix step
    inside the workspace (``service_bootstrap=False`` = the default
    fresh-init path)."""
    from loam.workspace_bootstrap.new_workspace import (
        bootstrap_new_workspace,
    )

    base = tmp_path_factory.mktemp("livi")
    ws = base / "ws"
    bootstrap_new_workspace(
        new_ws_path=ws,
        canonical_source=str(LOAM_ROOT),
        service_bootstrap=False,
        service_manager_dir_override=base / "LaunchAgents",
    )
    return ws


def _session_start_commands(ws: Path) -> list[str]:
    settings = json.loads(
        (ws / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    return [
        h["command"]
        for entry in settings["hooks"]["SessionStart"]
        for h in entry["hooks"]
    ]


def test_AC_LIVI_1_framework_venv_built_by_loam_init(
    fresh_init_workspace: Path,
) -> None:
    """The fix's load-bearing precondition: ``loam init`` itself builds
    ``<ws>/framework/.venv`` — NO manual venv step inside the
    workspace. Before the fix this venv never existed (the documented
    Quickstart builds a venv only in the disposable install clone)."""
    venv_python = (
        fresh_init_workspace / "framework" / ".venv" / "bin" / "python"
    )
    assert venv_python.is_file(), (
        f"{venv_python} absent — loam init did not provision the "
        "per-workspace framework venv; the scaffolded hooks would "
        "resolve to a non-existent interpreter (exit 127)."
    )


def test_AC_LIVI_1_hook_commands_target_the_provisioned_venv(
    fresh_init_workspace: Path,
) -> None:
    """Both scaffolded SessionStart hook commands invoke the venv
    interpreter that ``loam init`` now builds — the stanza builders are
    UNCHANGED (their ``loam_root/.venv/bin/python`` is now correct
    because the venv exists)."""
    cmds = _session_start_commands(fresh_init_workspace)
    venv_python = str(
        fresh_init_workspace / "framework" / ".venv" / "bin" / "python"
    )
    assert cmds, "no SessionStart hook commands scaffolded"
    for c in cmds:
        assert c.startswith(venv_python), (
            f"hook command does not target the provisioned venv: {c!r} "
            f"(expected to start with {venv_python!r})"
        )
    # Both load-bearing emitters are wired: the orchestrator script +
    # the persona session-start CLI.
    joined = " || ".join(cmds)
    assert "pos_session_start.py" in joined, (
        f"orchestrator session-start hook missing; cmds={cmds}"
    )
    assert "primary_persona.cli session-start" in joined, (
        f"persona session-start hook missing; cmds={cmds}"
    )


def test_AC_LIVI_1_each_hook_command_exits_0_not_127_and_emits(
    fresh_init_workspace: Path,
) -> None:
    """The outcome AC.LIVI.1 pins: running each REAL scaffolded hook
    command exits 0 (NOT 127 — the silent-dead defect this amendment
    closes) and emits a non-empty session-start context."""
    cmds = _session_start_commands(fresh_init_workspace)
    for c in cmds:
        proc = subprocess.run(  # noqa: S602 — scaffolded command, test
            c,
            shell=True,
            cwd=str(fresh_init_workspace),
            capture_output=True,
            text=True,
            timeout=90,
        )
        assert proc.returncode != 127, (
            f"hook command exited 127 (interpreter/entrypoint not "
            f"resolvable) — the exact fresh-init defect this amendment "
            f"closes. cmd={c!r} stderr={proc.stderr.strip()[-500:]!r}"
        )
        assert proc.returncode == 0, (
            f"hook command exited {proc.returncode} (expected 0). "
            f"cmd={c!r} stderr={proc.stderr.strip()[-500:]!r}"
        )
        assert proc.stdout.strip(), (
            f"hook command exited 0 but emitted no session-start "
            f"context. cmd={c!r}"
        )


def test_AC_LIVI_1_persona_session_start_emits_real_continuity_context(
    fresh_init_workspace: Path,
) -> None:
    """The persona session-start emit is the sealed
    memory-session-continuity substrate this amendment makes
    REACHABLE: its emission carries the session-start context shape
    (not an empty / error stub)."""
    cmds = _session_start_commands(fresh_init_workspace)
    persona_cmd = next(
        c for c in cmds if "primary_persona.cli session-start" in c
    )
    proc = subprocess.run(  # noqa: S602 — scaffolded command, test
        persona_cmd,
        shell=True,
        cwd=str(fresh_init_workspace),
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert proc.returncode == 0, (
        f"persona session-start exited {proc.returncode}; "
        f"stderr={proc.stderr.strip()[-500:]!r}"
    )
    out = proc.stdout
    assert "session-start" in out, (
        f"persona emit lacks the session-start context shape; "
        f"got head={out[:300]!r}"
    )
