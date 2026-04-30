"""AC.OSS-M4.5 — Hook short-circuits on NORMAL USE workspaces.

Per the locked plan-doc §4 AC.OSS-M4.5: the hook reads workspace mode
via ``corpus_load_sentinel.workspace_mode(workspace_root)`` and
short-circuits to allow (no setup phase, no sentinel, no manifest
rows, no stub authoring) when mode != ``dev-mode``. Mirrors A2/A3/A4's
mode-bit handling exactly — the structural-enforcement gates are
DEV-MODE-only.
"""

from __future__ import annotations

import json
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


def _stub_corpus_load_sentinel(monkeypatch, *, mode: str) -> None:
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _wr: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)


_PROMPT = (
    "<AC-MANIFEST>\n"
    "primary-persona,AC.X.1,framework/primary-persona/src/foo.py\n"
    "</AC-MANIFEST>\n"
)


def test_AC_OSS_M4_5_normal_use_no_setup_fired(
    tmp_path: Path, monkeypatch
) -> None:
    """NORMAL USE mode short-circuits regardless of well-formed AC
    manifest content."""
    _stub_corpus_load_sentinel(monkeypatch, mode="normal-use")
    import dispatch_setup_hook

    decision = dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": _PROMPT},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "short-circuit-normal-use"
    # No sentinel.
    assert not (
        tmp_path / "workspace" / ".pos" / "active-scope.json"
    ).exists()
    # No stubs.
    stub = (
        tmp_path
        / "framework"
        / "primary-persona"
        / "tests"
        / "test_AC_X_1_placeholder.py"
    )
    assert not stub.exists()


def test_AC_OSS_M4_5_audit_log_records_short_circuit(
    tmp_path: Path, monkeypatch
) -> None:
    """Short-circuit fires an audit line so the no-op is observable."""
    _stub_corpus_load_sentinel(monkeypatch, mode="normal-use")
    import dispatch_setup_hook

    dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": _PROMPT},
        envelope_cwd=str(tmp_path),
    )
    log_path = (
        tmp_path / "workspace" / ".pos" / "dispatch-setup-hook.log"
    )
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["decision"] == "short-circuit-normal-use"
    assert parsed["mode"] == "normal-use"


def test_AC_OSS_M4_5_bypass_env_var_short_circuits(
    tmp_path: Path, monkeypatch
) -> None:
    """LOAM_DISPATCH_BYPASS_HOOK=1 short-circuits to allow per
    D-build.M4.4 — recursion bypass for any future
    ``dispatch_with_scope`` wiring that re-fires the Task tool."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")
    import dispatch_setup_hook

    decision = dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": _PROMPT},
        envelope_cwd=str(tmp_path),
        env={"LOAM_DISPATCH_BYPASS_HOOK": "1"},
    )
    assert decision.decision == "short-circuit-bypass-env"
    # No sentinel/stubs/manifest fire.
    assert not (
        tmp_path / "workspace" / ".pos" / "active-scope.json"
    ).exists()


def test_AC_OSS_M4_5_bypass_env_var_disabled_runs_setup(
    tmp_path: Path, monkeypatch
) -> None:
    """env without bypass var still runs setup (negative test)."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")

    class _FakeTracker:
        def __init__(self) -> None:
            self.rows: list[dict] = []

        def register_source_binding(
            self, *, component, ac_id, source_path_glob
        ) -> None:
            self.rows.append(
                {
                    "component": component,
                    "ac_id": ac_id,
                    "source_path_glob": source_path_glob,
                }
            )

    tracker = _FakeTracker()
    import dispatch_setup_hook

    monkeypatch.setattr(
        dispatch_setup_hook,
        "_open_tracker",
        lambda _wr: tracker,
    )

    decision = dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": _PROMPT},
        envelope_cwd=str(tmp_path),
        env={},  # explicit empty env
    )
    assert decision.decision == "setup-fired"
    assert len(tracker.rows) == 1
