"""AC.OSS-M4.6 — Hook is fail-soft on substrate failures + emits
structured NDJSON.

Per the locked plan-doc §4 AC.OSS-M4.6: tracker unavailable, sentinel
write fails, stub write fails — each emits one NDJSON line to
``<workspace>/workspace/.pos/dispatch-setup-hook.log`` and the dispatch
is allowed to proceed (hook exits 0, stdout empty). The non-failed
steps continue (e.g. sentinel still fires when the tracker is
unavailable).
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


def _stub_corpus_load_sentinel(monkeypatch, *, mode: str) -> None:
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _wr: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)


_PROMPT = (
    "<AC-MANIFEST>\n"
    "primary-persona,AC.X.1,framework/primary-persona/src/foo.py\n"
    "</AC-MANIFEST>\n"
)


def _read_log(workspace_root: Path) -> list[dict]:
    log_path = (
        workspace_root / "workspace" / ".pos" / "dispatch-setup-hook.log"
    )
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines]


def test_AC_OSS_M4_6_tracker_unavailable_fail_soft(
    tmp_path: Path, monkeypatch
) -> None:
    """Tracker open returns None → manifest step records
    ``failed-tracker-unavailable`` + sentinel/stubs still fire +
    decision is ``setup-fired``."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")
    import dispatch_setup_hook

    monkeypatch.setattr(
        dispatch_setup_hook,
        "_open_tracker",
        lambda _wr: None,
    )

    decision = dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": _PROMPT},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "setup-fired"
    # Sentinel still fired.
    assert (
        tmp_path / "workspace" / ".pos" / "active-scope.json"
    ).exists()
    # Stub still authored.
    stub = (
        tmp_path
        / "framework"
        / "primary-persona"
        / "tests"
        / "test_AC_X_1_placeholder.py"
    )
    assert stub.exists()
    # Manifest step recorded the failure.
    manifest_steps = [
        s for s in decision.step_outcomes
        if s.get("step") == "manifest"
    ]
    assert len(manifest_steps) == 1
    assert manifest_steps[0]["outcome"] == "failed-tracker-unavailable"
    # Audit log carries it.
    log = _read_log(tmp_path)
    failed_lines = [
        ln for ln in log
        if ln.get("step") == "manifest"
        and ln.get("outcome") == "failed-tracker-unavailable"
    ]
    assert len(failed_lines) == 1


def test_AC_OSS_M4_6_tracker_register_raises_fail_soft(
    tmp_path: Path, monkeypatch
) -> None:
    """Tracker register_source_binding raises → ``failed-exception``
    outcome on the manifest step + other steps continue."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")

    class _RaisingTracker:
        def register_source_binding(
            self, *, component, ac_id, source_path_glob
        ):
            raise RuntimeError("simulated tracker failure")

    import dispatch_setup_hook

    monkeypatch.setattr(
        dispatch_setup_hook,
        "_open_tracker",
        lambda _wr: _RaisingTracker(),
    )

    decision = dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": _PROMPT},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "setup-fired"
    manifest_steps = [
        s for s in decision.step_outcomes
        if s.get("step") == "manifest"
    ]
    assert manifest_steps[0]["outcome"] == "failed-exception"
    assert "simulated tracker failure" in manifest_steps[0].get(
        "error_detail", ""
    )


def test_AC_OSS_M4_6_main_exits_zero_on_evaluate_exception(
    tmp_path: Path, monkeypatch
) -> None:
    """Last-resort fail-soft: an unhandled exception in evaluate()
    must NOT propagate; main() still emits empty stdout + exits 0."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")
    import dispatch_setup_hook

    def _raising_evaluate(**_kwargs):
        raise RuntimeError("evaluate exploded")

    monkeypatch.setattr(
        dispatch_setup_hook,
        "evaluate",
        _raising_evaluate,
    )

    envelope = {
        "session_id": "s1",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Task",
        "tool_input": {"prompt": _PROMPT},
    }

    class _StringIO:
        def __init__(self, content):
            self._content = content

        def read(self):
            return self._content

    monkeypatch.setattr(
        "sys.stdin", _StringIO(json.dumps(envelope))
    )

    rc = dispatch_setup_hook.main([])
    assert rc == 0


def test_AC_OSS_M4_6_audit_log_ndjson_shape(
    tmp_path: Path, monkeypatch
) -> None:
    """Each audit line is one NDJSON object with the expected schema
    (ts, event, tool, prompt_length, cwd, mode, ...step-specific...)."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")

    class _FakeTracker:
        def register_source_binding(
            self, *, component, ac_id, source_path_glob
        ):
            return None

    import dispatch_setup_hook

    monkeypatch.setattr(
        dispatch_setup_hook,
        "_open_tracker",
        lambda _wr: _FakeTracker(),
    )

    dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": _PROMPT},
        envelope_cwd=str(tmp_path),
    )
    log = _read_log(tmp_path)
    assert len(log) >= 4
    for line in log:
        assert "ts" in line
        assert line.get("event") == "dispatch-setup-hook"
        assert line.get("tool") == "Task"
        assert "prompt_length" in line
        assert "cwd" in line
        assert line.get("mode") == "dev-mode"


def test_AC_OSS_M4_6_full_prompt_not_recorded(
    tmp_path: Path, monkeypatch
) -> None:
    """The full prompt body is NOT recorded — privacy + size per
    plan-doc §4 AC.OSS-M4.6 schema. Only ``prompt_length``, AC
    declarations, and per-step outcomes are."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")

    class _FakeTracker:
        def register_source_binding(
            self, *, component, ac_id, source_path_glob
        ):
            return None

    import dispatch_setup_hook

    monkeypatch.setattr(
        dispatch_setup_hook,
        "_open_tracker",
        lambda _wr: _FakeTracker(),
    )

    secret_token = "PRIVATE_TOKEN_DO_NOT_LEAK_42"
    prompt = (
        f"This prompt mentions {secret_token} as user content.\n"
        "<AC-MANIFEST>\n"
        "primary-persona,AC.X.1,framework/primary-persona/src/foo.py\n"
        "</AC-MANIFEST>\n"
    )
    dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": prompt},
        envelope_cwd=str(tmp_path),
    )
    log_text = (
        tmp_path / "workspace" / ".pos" / "dispatch-setup-hook.log"
    ).read_text(encoding="utf-8")
    assert secret_token not in log_text
