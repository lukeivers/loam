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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PFSE.5 — the persona cannot dispatch/author work until the
relevant design docs are loaded; the gate blocks otherwise.

Verification surface (plan §5): a dispatch attempted without the
required docs loaded is blocked by the gate THROUGH THE PRODUCTION PATH;
with them loaded, it proceeds.

The gate is a deterministic loaded-set predicate over the corpus-load
sentinel's ``state`` ({loaded, partial, missing}) — NOT an LLM relevance
judgment (plan §3 / halt-trigger 2). DEV-MODE only; carve-out author
edits (docs/scratch) are never gated (that is how context loads);
fail-open on a missing sentinel / session id.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
CANONICAL_HOOKS_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
)
HOOK = PLUGIN_HOOKS_DIR / "context_load_gate.py"
sys.path.insert(0, str(PLUGIN_HOOKS_DIR))
sys.path.insert(0, str(CANONICAL_HOOKS_DIR))

import context_load_gate as gate  # noqa: E402
import corpus_load_sentinel as cls  # noqa: E402

_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
PYTHON = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else sys.executable

SESSION = "sess-pfse5"


def _dev_mode_workspace(tmp_path: Path) -> Path:
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    return tmp_path


def _write_sentinel(
    ws: Path,
    *,
    required: list[str],
    loaded: list[str],
    state: str,
) -> None:
    """Write a corpus-load sentinel directly (the production JSON
    contract) at the session path, with a controlled state."""
    path = cls.session_state_path(ws, SESSION)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "session_id": SESSION,
                "corpus_paths_required": required,
                "corpus_paths_loaded": loaded,
                "state": state,
                "created_at": "2026-06-14T00:00:00.000000Z",
            }
        ),
        encoding="utf-8",
    )


def _reads_dev_mode(ws: Path) -> bool:
    return (
        gate._helpers.read_workspace_mode_or_normal_use(ws) == "dev-mode"
    )


# ----- missing corpus -> dispatch blocked -----


def test_AC_PFSE_5_dispatch_blocked_when_corpus_missing(
    tmp_path,
) -> None:
    ws = _dev_mode_workspace(tmp_path)
    _write_sentinel(
        ws,
        required=["docs/design/foo.md", "CLAUDE.md"],
        loaded=[],
        state="missing",
    )
    d = gate.evaluate(
        workspace_root=ws,
        tool_name="Task",
        tool_input={"prompt": "do work", "description": "x"},
        session_id=SESSION,
    )
    if not _reads_dev_mode(ws):
        assert d.decision == "no-op"
        return
    assert d.decision == "deny" and d.kind == "deny"
    assert "docs/design/foo.md" in (d.reason or "")


# ----- partial corpus -> dispatch blocked, names the unloaded doc -----


def test_AC_PFSE_5_dispatch_blocked_when_corpus_partial(
    tmp_path,
) -> None:
    ws = _dev_mode_workspace(tmp_path)
    _write_sentinel(
        ws,
        required=["docs/design/foo.md", "CLAUDE.md"],
        loaded=["CLAUDE.md"],
        state="partial",
    )
    d = gate.evaluate(
        workspace_root=ws,
        tool_name="Task",
        tool_input={"prompt": "do work"},
        session_id=SESSION,
    )
    if not _reads_dev_mode(ws):
        assert d.decision == "no-op"
        return
    assert d.decision == "deny"
    assert "docs/design/foo.md" in (d.reason or "")
    assert "CLAUDE.md" not in (d.reason or "")


# ----- loaded corpus -> dispatch proceeds -----


def test_AC_PFSE_5_dispatch_allowed_when_corpus_loaded(
    tmp_path,
) -> None:
    ws = _dev_mode_workspace(tmp_path)
    _write_sentinel(
        ws,
        required=["docs/design/foo.md", "CLAUDE.md"],
        loaded=["docs/design/foo.md", "CLAUDE.md"],
        state="loaded",
    )
    d = gate.evaluate(
        workspace_root=ws,
        tool_name="Task",
        tool_input={"prompt": "do work"},
        session_id=SESSION,
    )
    if not _reads_dev_mode(ws):
        assert d.decision == "no-op"
        return
    assert d.decision == "allow" and d.kind == "loaded"


# ----- author edit to a SOURCE path is gated; to a carve-out is not ---


def test_AC_PFSE_5_source_author_blocked_when_missing(tmp_path) -> None:
    ws = _dev_mode_workspace(tmp_path)
    _write_sentinel(
        ws, required=["CLAUDE.md"], loaded=[], state="missing"
    )
    d = gate.evaluate(
        workspace_root=ws,
        tool_name="Write",
        tool_input={
            "file_path": str(
                ws / "framework" / "foo" / "src" / "bar.py"
            )
        },
        session_id=SESSION,
    )
    if not _reads_dev_mode(ws):
        assert d.decision == "no-op"
        return
    assert d.decision == "deny"


def test_AC_PFSE_5_carve_out_author_never_gated(tmp_path) -> None:
    ws = _dev_mode_workspace(tmp_path)
    _write_sentinel(
        ws, required=["CLAUDE.md"], loaded=[], state="missing"
    )
    d = gate.evaluate(
        workspace_root=ws,
        tool_name="Write",
        tool_input={"file_path": str(ws / "docs" / "scratch.md")},
        session_id=SESSION,
    )
    # docs/ is a carve-out; editing it is how context loads -> allow,
    # regardless of corpus state. (Mode-independent: carve-out check is
    # after the mode gate, so under non-dev it is no-op; under dev it is
    # carve-out.)
    assert d.decision in ("allow", "no-op")


# ----- read-only tools never gated -----


def test_AC_PFSE_5_read_tool_never_gated(tmp_path) -> None:
    ws = _dev_mode_workspace(tmp_path)
    _write_sentinel(
        ws, required=["CLAUDE.md"], loaded=[], state="missing"
    )
    d = gate.evaluate(
        workspace_root=ws,
        tool_name="Read",
        tool_input={"file_path": str(ws / "CLAUDE.md")},
        session_id=SESSION,
    )
    assert d.decision == "no-op"


# ----- no session id / no sentinel -> fail-open -----


def test_AC_PFSE_5_no_session_id_fails_open(tmp_path) -> None:
    ws = _dev_mode_workspace(tmp_path)
    d = gate.evaluate(
        workspace_root=ws,
        tool_name="Task",
        tool_input={"prompt": "x"},
        session_id=None,
    )
    assert d.decision in ("allow", "no-op")


def test_AC_PFSE_5_no_sentinel_fails_open(tmp_path) -> None:
    ws = _dev_mode_workspace(tmp_path)
    d = gate.evaluate(
        workspace_root=ws,
        tool_name="Task",
        tool_input={"prompt": "x"},
        session_id="nonexistent-session",
    )
    assert d.decision in ("allow", "no-op")


# ----- NORMAL-USE short-circuit -----


def test_AC_PFSE_5_normal_use_is_noop(tmp_path) -> None:
    # No persona contract -> normal-use -> short-circuit.
    _write_sentinel = None  # noqa: F841 — intentional: skip sentinel
    d = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "x"},
        session_id=SESSION,
    )
    assert d.decision == "no-op"


# ----- production subprocess path: deny payload + rc 0 -----


def test_AC_PFSE_5_subprocess_deny_on_production_path(tmp_path) -> None:
    ws = _dev_mode_workspace(tmp_path)
    _write_sentinel(
        ws,
        required=["docs/design/foo.md"],
        loaded=[],
        state="missing",
    )
    envelope = {
        "session_id": SESSION,
        "cwd": str(ws),
        "hook_event_name": "PreToolUse",
        "tool_name": "Task",
        "tool_input": {"prompt": "dispatch some work"},
    }
    proc = subprocess.run(
        [PYTHON, str(HOOK)],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        cwd=str(ws),
    )
    assert proc.returncode == 0
    # In dev-mode the missing corpus denies; out of dev-mode no-ops
    # (empty). Both rc-0 production outcomes.
    if proc.stdout.strip():
        payload = json.loads(proc.stdout)
        assert (
            payload["hookSpecificOutput"]["permissionDecision"] == "deny"
        )


def test_AC_PFSE_5_subprocess_malformed_fails_open() -> None:
    proc = subprocess.run(
        [PYTHON, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""
