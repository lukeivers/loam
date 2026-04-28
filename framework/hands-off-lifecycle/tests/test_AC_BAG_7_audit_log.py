"""AC.BAG.7 — Every Bash gate fire is observable through a
deterministic audit surface.

Per the locked plan-doc §4 AC.BAG.7: each PreToolUse Bash fire (allow
+ deny + no-op + error) is recorded in a workspace-local audit
surface that a downstream consumer can read deterministically. The
surface is append-only; concurrent fires across processes do not
corrupt each other (atomicity guarantee).

Per ODD §8.2.14 byte-content verification: the test reads the on-disk
NDJSON file and asserts schema.
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


def test_AC_BAG_7_audit_log_at_workspace_state_path(tmp_path) -> None:
    """The audit log lives at ``<workspace>/workspace/.pos/
    bash-guard.log`` per locked plan §6 D-A4.9 + hard constraint 16."""
    import bash_guard

    expected = tmp_path / "workspace" / ".pos" / "bash-guard.log"
    assert bash_guard._audit_log_path(tmp_path) == expected


def test_AC_BAG_7_deny_writes_one_ndjson_line(
    tmp_path, monkeypatch
) -> None:
    """A deny decision invoked through main() appends one JSON object
    line to the audit log; schema (byte-content per ODD §8.2.14)."""
    _stub_modules(monkeypatch, mode="normal-use")
    import bash_guard

    envelope = {
        "session_id": "s1",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git add .env"},
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    rc = bash_guard.main([])
    assert rc == 0

    log_path = tmp_path / "workspace" / ".pos" / "bash-guard.log"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    for field in (
        "ts",
        "tool",
        "command",
        "mode",
        "sentinel_state",
        "decision",
        "failure_class",
        "matched",
        "reason",
    ):
        assert field in payload, f"missing field {field!r}"
    assert payload["tool"] == "Bash"
    assert payload["command"] == "git add .env"
    assert payload["decision"] == "deny"
    assert payload["failure_class"] == "secret-commit"
    assert isinstance(payload["reason"], str) and payload["reason"]


def test_AC_BAG_7_no_op_writes_one_line(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import bash_guard

    envelope = {
        "session_id": "s1",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",  # non-Bash → no-op
        "tool_input": {"file_path": "/tmp/x"},
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    rc = bash_guard.main([])
    assert rc == 0

    log_path = tmp_path / "workspace" / ".pos" / "bash-guard.log"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["decision"] == "no-op"


def test_AC_BAG_7_two_fires_append_atomically(
    tmp_path, monkeypatch
) -> None:
    _stub_modules(monkeypatch, mode="normal-use")
    import bash_guard

    log_path = tmp_path / "workspace" / ".pos" / "bash-guard.log"

    for i in range(2):
        envelope = {
            "session_id": f"s{i}",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": f"echo {i}"},
        }
        monkeypatch.setattr(
            sys, "stdin", io.StringIO(json.dumps(envelope))
        )
        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdout", captured)
        bash_guard.main([])

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    payloads = [json.loads(line) for line in lines]
    assert payloads[0]["command"] == "echo 0"
    assert payloads[1]["command"] == "echo 1"
