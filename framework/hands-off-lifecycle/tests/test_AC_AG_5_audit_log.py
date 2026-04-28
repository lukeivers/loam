"""AC.AG.5 — Every Agent gate fire is observable through a
deterministic audit surface.

Per the locked plan-doc §4 AC.AG.5: each PreToolUse Task fire (allow
+ deny + no-op + error) is recorded in a workspace-local audit
surface (separate from AC.BAG.7's Bash-gate log). Mirrors AC.BAG.7's
contract.

Per ODD §8.2.14 byte-content verification.
"""

from __future__ import annotations

import io
import json
import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


def _stub_modules(monkeypatch, *, mode: str):
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)


def test_AC_AG_5_audit_log_at_workspace_state_path(tmp_path) -> None:
    """The audit log lives at ``<workspace>/workspace/.pos/
    agent-guard.log`` per locked plan §6 D-A4.9 + hard constraint 16."""
    import agent_guard

    expected = tmp_path / "workspace" / ".pos" / "agent-guard.log"
    assert agent_guard._audit_log_path(tmp_path) == expected


def test_AC_AG_5_deny_writes_one_ndjson_line(
    tmp_path, monkeypatch
) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    envelope = {
        "session_id": "s1",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Task",
        "tool_input": {
            "prompt": "Update docs/rebuild/plans/foo.md.",
            "subagent_type": "general-purpose",
        },
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    rc = agent_guard.main([])
    assert rc == 0

    log_path = tmp_path / "workspace" / ".pos" / "agent-guard.log"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    for field in (
        "ts",
        "tool",
        "prompt_length",
        "cwd",
        "mode",
        "decision",
        "failure_class",
        "matched",
        "reason",
    ):
        assert field in payload, f"missing field {field!r}"
    assert payload["tool"] == "Task"
    assert payload["mode"] == "dev-mode"
    assert payload["decision"] == "deny"
    assert payload["failure_class"] == "wrong-wd"
    assert isinstance(payload["reason"], str) and payload["reason"]


def test_AC_AG_5_no_op_writes_one_line(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="normal-use")
    import agent_guard

    envelope = {
        "session_id": "s1",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Task",
        "tool_input": {"prompt": "anything"},
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    rc = agent_guard.main([])
    assert rc == 0

    log_path = tmp_path / "workspace" / ".pos" / "agent-guard.log"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["decision"] == "no-op"
    assert payload["mode"] == "normal-use"


def test_AC_AG_5_two_fires_append_atomically(
    tmp_path, monkeypatch
) -> None:
    _stub_modules(monkeypatch, mode="normal-use")
    import agent_guard

    log_path = tmp_path / "workspace" / ".pos" / "agent-guard.log"

    for i in range(2):
        envelope = {
            "session_id": f"s{i}",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "Task",
            "tool_input": {"prompt": f"task {i}"},
        }
        monkeypatch.setattr(
            sys, "stdin", io.StringIO(json.dumps(envelope))
        )
        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdout", captured)
        agent_guard.main([])

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    payloads = [json.loads(line) for line in lines]
    assert payloads[0]["prompt_length"] == len("task 0")
    assert payloads[1]["prompt_length"] == len("task 1")


def test_AC_AG_5_prompt_text_not_recorded(
    tmp_path, monkeypatch
) -> None:
    """Privacy: the audit log records prompt_length, NOT the full
    prompt text. Per the agent_guard module-doc convention."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    secret_token = "SHHHH-SECRET-TOKEN-12345"
    envelope = {
        "session_id": "s1",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Task",
        "tool_input": {"prompt": f"Search for {secret_token}."},
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    agent_guard.main([])

    log_path = tmp_path / "workspace" / ".pos" / "agent-guard.log"
    contents = log_path.read_text(encoding="utf-8")
    # The prompt text — including the secret token — should NOT be
    # in the audit log.
    assert secret_token not in contents
