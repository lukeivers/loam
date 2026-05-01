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

"""AC.AG.3 — Agent gate denies stale dispatch re-targeting an
already-sealed amendment (DEV-MODE-only).

Per the locked plan-doc §4 AC.AG.3: given workspace-mode = ``dev-
mode``, given a Task tool call whose ``tool_input.prompt`` mentions
an amendment number (matches ``amendment #(\\d+)``) OR an AC ID
(matches ``AC\\.\\w+\\.\\w+``), given the manifest table OR git
history shows the named amendment/AC has already sealed: hook
returns ``permissionDecision: "deny"`` with reason naming (a) the
detected stale reference, (b) the seal commit SHA when known,
(c) at least one repair direction. Fail-closed-to-permissive at the
manifest-import boundary: tracker unreachable → fall through to allow.
NORMAL USE workspaces no-op this check.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
# Post-M6b.0: gate-hook source files MOVED to plugins/dev-sdlc/hooks/.
# Add plugin's hooks dir to sys.path so the test imports resolve to
# the moved gate modules. _gate_helpers.py STAYS at canonical
# (HOOKS_DIR above) and remains importable.
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
if PLUGIN_HOOKS_DIR.exists():
    sys.path.insert(0, str(PLUGIN_HOOKS_DIR))


def _stub_modules(monkeypatch, *, mode: str):
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)


def test_AC_AG_3_amendment_number_sealed_denies(
    tmp_path, monkeypatch
) -> None:
    """Prompt mentions amendment #N + git log finds seal → deny."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    monkeypatch.setattr(
        agent_guard,
        "_amendment_seal_commit_for_number",
        lambda _ws, n: (
            "abcdef0123456789abcdef0123456789abcdef01" if n == 51 else None
        ),
    )
    monkeypatch.setattr(agent_guard, "_open_tracker", lambda _: None)

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "Build amendment #51 substrate."},
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "stale-dispatch"
    assert "AC.AG.3" in decision.reason
    assert "#51" in decision.reason
    assert "abcdef01" in decision.reason


def test_AC_AG_3_ac_id_in_manifest_denies(
    tmp_path, monkeypatch
) -> None:
    """Prompt mentions AC.X.Y + tracker has manifest row → deny."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    class _StubTracker:
        def manifest_rows_for_ac(self, component, ac_id):
            if (
                component == "hands-off-lifecycle"
                and ac_id == "AC.OBG.1"
            ):
                return [{"component": component, "ac_id": ac_id}]
            return []

    monkeypatch.setattr(
        agent_guard, "_open_tracker", lambda _: _StubTracker()
    )
    monkeypatch.setattr(
        agent_guard,
        "_amendment_seal_commit_for_number",
        lambda _ws, _n: None,
    )

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "Re-register AC.OBG.1 for the gate."},
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "stale-dispatch"
    assert "AC.OBG.1" in decision.reason


def test_AC_AG_3_unsealed_amendment_admitted(
    tmp_path, monkeypatch
) -> None:
    """Prompt mentions amendment #N but no seal in history → admitted."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    monkeypatch.setattr(
        agent_guard,
        "_amendment_seal_commit_for_number",
        lambda _ws, _n: None,
    )
    monkeypatch.setattr(agent_guard, "_open_tracker", lambda _: None)

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={
            "prompt": "Build amendment #999 (un-shipped scope)."
        },
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_AG_3_no_amendment_or_ac_mentions_admitted(
    tmp_path, monkeypatch
) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "Search for occurrences of 'foo'."},
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_AG_3_fail_closed_to_permissive_when_tracker_none(
    tmp_path, monkeypatch
) -> None:
    """Tracker unreachable + amendment number not sealed → admitted
    (fail-closed-to-permissive at substrate-import boundary)."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    monkeypatch.setattr(agent_guard, "_open_tracker", lambda _: None)
    monkeypatch.setattr(
        agent_guard,
        "_amendment_seal_commit_for_number",
        lambda _ws, _n: None,
    )

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "Author AC.SOMETHING.NEW for foo."},
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_AG_3_normal_use_no_op(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="normal-use")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "Build amendment #51."},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "no-op"
