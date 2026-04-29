"""AC.OSS-M4.1 — PreToolUse hook on Task performs the disk-side
setup phase.

Per the locked plan-doc §4 AC.OSS-M4.1: given a DEV-MODE workspace +
a Task tool call whose ``tool_input["prompt"]`` contains an
``<AC-MANIFEST>`` block with one or more well-formed CSV rows, the
hook performs the disk-side four gates (sentinel + manifest rows +
test stubs + plan-doc reference via the sentinel) BEFORE allowing
the Task tool to fire.
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


class _FakeTracker:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def register_source_binding(
        self, *, component: str, ac_id: str, source_path_glob: str
    ) -> None:
        self.rows.append(
            {
                "component": component,
                "ac_id": ac_id,
                "source_path_glob": source_path_glob,
            }
        )


def _stub_tracker(monkeypatch, tracker: _FakeTracker) -> None:
    """Patch the dispatch_setup_hook module's tracker opener so the
    hook sees our fake instead of the real ObjectiveTracker."""
    import dispatch_setup_hook

    monkeypatch.setattr(
        dispatch_setup_hook,
        "_open_tracker",
        lambda _wr: tracker,
    )


def _build_envelope_prompt() -> str:
    return (
        "Build amendment per docs/rebuild/plans/foo.md.\n"
        "\n"
        "<AC-MANIFEST>\n"
        "primary-persona,AC.X.1,framework/primary-persona/src/foo.py\n"
        "hands-off-lifecycle,AC.Y.2,framework/hands-off-lifecycle/hooks/bar.py\n"
        "</AC-MANIFEST>\n"
    )


def test_AC_OSS_M4_1_setup_phase_writes_sentinel_and_stubs(
    tmp_path: Path, monkeypatch
) -> None:
    """Well-formed AC manifest fires the four disk-side gates."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")
    tracker = _FakeTracker()
    import dispatch_setup_hook

    _stub_tracker(monkeypatch, tracker)

    decision = dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": _build_envelope_prompt()},
        envelope_cwd=str(tmp_path),
        session_id="session-abc",
    )
    assert decision.decision == "setup-fired"
    assert len(decision.parsed_acs) == 2

    # Gate 1 — sentinel.
    sentinel_path = (
        tmp_path / "workspace" / ".pos" / "active-scope.json"
    )
    assert sentinel_path.exists()
    sentinel = json.loads(sentinel_path.read_text(encoding="utf-8"))
    assert sentinel["plan_path"] == "docs/rebuild/plans/foo.md"
    assert len(sentinel["bindings"]) == 2

    # Gate 2 — manifest rows registered on the tracker.
    assert len(tracker.rows) == 2
    assert tracker.rows[0]["component"] == "primary-persona"
    assert tracker.rows[0]["ac_id"] == "AC.X.1"
    assert tracker.rows[1]["component"] == "hands-off-lifecycle"

    # Gate 3 — test stubs authored at the AC.DSA.2 path.
    stub_pp = (
        tmp_path
        / "framework"
        / "primary-persona"
        / "tests"
        / "test_AC_X_1_placeholder.py"
    )
    stub_hol = (
        tmp_path
        / "framework"
        / "hands-off-lifecycle"
        / "tests"
        / "test_AC_Y_2_placeholder.py"
    )
    assert stub_pp.exists()
    assert stub_hol.exists()

    # Gate 4 — plan-doc reference recorded via the sentinel's
    # plan_path field; outcome enumerated in step_outcomes for
    # traceability per the dispatch's enumeration.
    plan_steps = [
        s for s in decision.step_outcomes
        if s.get("step") == "plan-doc-reference"
    ]
    assert len(plan_steps) == 1
    assert plan_steps[0]["plan_path"] == "docs/rebuild/plans/foo.md"
    assert plan_steps[0]["outcome"] == "recorded-via-sentinel"


def test_AC_OSS_M4_1_main_emits_empty_stdout_allow(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """``main(argv)`` emits empty stdout (allow) on every path."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")
    tracker = _FakeTracker()
    import dispatch_setup_hook

    _stub_tracker(monkeypatch, tracker)

    envelope = {
        "session_id": "s1",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Task",
        "tool_input": {"prompt": _build_envelope_prompt()},
    }
    monkeypatch.setattr(
        "sys.stdin", _StringIO(json.dumps(envelope))
    )

    rc = dispatch_setup_hook.main([])
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_AC_OSS_M4_1_audit_log_appended(
    tmp_path: Path, monkeypatch
) -> None:
    """Each fire appends NDJSON lines to dispatch-setup-hook.log."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")
    tracker = _FakeTracker()
    import dispatch_setup_hook

    _stub_tracker(monkeypatch, tracker)

    dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": _build_envelope_prompt()},
        envelope_cwd=str(tmp_path),
        session_id="s1",
    )
    log_path = (
        tmp_path / "workspace" / ".pos" / "dispatch-setup-hook.log"
    )
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 4  # firing + at least sentinel/manifest/stub/plan
    parsed = [json.loads(line) for line in lines]
    decisions = {p.get("decision") for p in parsed if "decision" in p}
    assert "setup-firing" in decisions


class _StringIO:
    """Minimal stdin-replacement for monkeypatching."""

    def __init__(self, content: str) -> None:
        self._content = content

    def read(self) -> str:
        return self._content
