"""AC.A4.settings_merge — Multi-contributor merge admits A2+A3+A4_bash
+A4_task.

Per the locked plan-doc §4 AC.A4.settings_merge: given A2's stanza +
A3's stanza + A4_bash's stanza + A4_task's stanza:
``merge_pre_tool_use(new_entries=[a2, a3, a4_bash, a4_task])`` writes
the four-element outer list under ``hooks.PreToolUse``. Re-merge
over a pos-v2-owned four-element outer list does not back up. User-
authored stanzas continue to be preserved via the
``_USER_AUTHORED`` backup convention (regression contract for A2's
existing settings-merge tests + A3's multi-contributor extension).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import merge_pre_tool_use  # noqa: E402


def _a2_stanza(pos_v2_root: Path) -> dict:
    script = (
        pos_v2_root
        / "framework"
        / "hands-off-lifecycle"
        / "hooks"
        / "objective_binding_gate.py"
    )
    return {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
            {
                "type": "command",
                "command": f"{sys.executable} {script}",
                "async": False,
                "timeout": 5,
            }
        ],
    }


def _a3_stanza(pos_v2_root: Path) -> dict:
    script = (
        pos_v2_root
        / "framework"
        / "hands-off-lifecycle"
        / "hooks"
        / "tdd_guard.py"
    )
    return {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
            {
                "type": "command",
                "command": f"{sys.executable} {script}",
                "async": False,
                "timeout": 5,
            }
        ],
    }


def _a4_bash_stanza(pos_v2_root: Path) -> dict:
    script = (
        pos_v2_root
        / "framework"
        / "hands-off-lifecycle"
        / "hooks"
        / "bash_guard.py"
    )
    return {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": f"{sys.executable} {script}",
                "async": False,
                "timeout": 5,
            }
        ],
    }


def _a4_task_stanza(pos_v2_root: Path) -> dict:
    script = (
        pos_v2_root
        / "framework"
        / "hands-off-lifecycle"
        / "hooks"
        / "agent_guard.py"
    )
    return {
        "matcher": "Task",
        "hooks": [
            {
                "type": "command",
                "command": f"{sys.executable} {script}",
                "async": False,
                "timeout": 5,
            }
        ],
    }


def test_AC_A4_settings_merge_first_write_four_stanzas(
    tmp_path: Path,
) -> None:
    """First write with new_entries=[a2, a3, a4_bash, a4_task] produces
    all four stanzas in order under hooks.PreToolUse."""
    settings_path = tmp_path / "settings.json"
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _a2_stanza(tmp_path),
            _a3_stanza(tmp_path),
            _a4_bash_stanza(tmp_path),
            _a4_task_stanza(tmp_path),
        ],
    )
    assert result.wrote is True
    assert result.backup_path is None
    data = json.loads(settings_path.read_text())
    pte = data["hooks"]["PreToolUse"]
    assert len(pte) == 4
    assert "objective_binding_gate.py" in pte[0]["hooks"][0]["command"]
    assert "tdd_guard.py" in pte[1]["hooks"][0]["command"]
    assert "bash_guard.py" in pte[2]["hooks"][0]["command"]
    assert "agent_guard.py" in pte[3]["hooks"][0]["command"]
    assert pte[2]["matcher"] == "Bash"
    assert pte[3]["matcher"] == "Task"


def test_AC_A4_settings_merge_re_merge_no_backup(
    tmp_path: Path,
) -> None:
    """Re-merge over a four-element pos-v2 list (every inner-hook
    command matches a recognised marker) does NOT create a backup."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _a2_stanza(tmp_path),
            _a3_stanza(tmp_path),
            _a4_bash_stanza(tmp_path),
            _a4_task_stanza(tmp_path),
        ],
    )
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _a2_stanza(tmp_path),
            _a3_stanza(tmp_path),
            _a4_bash_stanza(tmp_path),
            _a4_task_stanza(tmp_path),
        ],
    )
    assert result.wrote is True
    assert result.backup_path is None


def test_AC_A4_settings_merge_re_merge_over_legacy_a3_no_backup(
    tmp_path: Path,
) -> None:
    """A pre-A4 settings.json carries A2 + A3 only. Re-merging with
    all four does NOT trigger backup (legacy A2/A3 markers are still
    in the recognised set)."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _a2_stanza(tmp_path),
            _a3_stanza(tmp_path),
        ],
    )
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _a2_stanza(tmp_path),
            _a3_stanza(tmp_path),
            _a4_bash_stanza(tmp_path),
            _a4_task_stanza(tmp_path),
        ],
    )
    assert result.wrote is True
    assert result.backup_path is None
    data = json.loads(settings_path.read_text())
    pte = data["hooks"]["PreToolUse"]
    assert len(pte) == 4


def test_AC_A4_settings_merge_user_authored_creates_backup(
    tmp_path: Path,
) -> None:
    """Re-merge over a user-authored stanza creates a backup AND
    preserves the prior bytes."""
    settings_path = tmp_path / "settings.json"
    user_authored_payload = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "/usr/local/bin/my-bash-guard",
                            "async": False,
                            "timeout": 30,
                        }
                    ],
                }
            ],
        },
        "user_key": "preserved",
    }
    settings_path.write_text(json.dumps(user_authored_payload, indent=2))

    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _a2_stanza(tmp_path),
            _a3_stanza(tmp_path),
            _a4_bash_stanza(tmp_path),
            _a4_task_stanza(tmp_path),
        ],
        now_iso="20260428T120000Z",
    )
    assert result.wrote is True
    assert result.backup_path is not None
    backup_data = json.loads(result.backup_path.read_text())
    assert (
        backup_data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        == "/usr/local/bin/my-bash-guard"
    )
    data = json.loads(settings_path.read_text())
    assert data.get("user_key") == "preserved"
    assert len(data["hooks"]["PreToolUse"]) == 4


def test_AC_A4_settings_merge_orthogonal_stanzas_preserved(
    tmp_path: Path,
) -> None:
    """Multi-contributor PreToolUse merge does NOT touch other
    stanzas (SessionStart, Stop, statusLine)."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "/path/to/first-run.sh",
                                    "async": False,
                                    "timeout": 60,
                                }
                            ],
                        }
                    ],
                },
                "statusLine": {
                    "type": "command",
                    "command": "X hands-off-lifecycle/hooks/statusline.py",
                    "refreshInterval": 1,
                },
            },
            indent=2,
        )
    )

    merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _a2_stanza(tmp_path),
            _a3_stanza(tmp_path),
            _a4_bash_stanza(tmp_path),
            _a4_task_stanza(tmp_path),
        ],
    )

    data = json.loads(settings_path.read_text())
    assert (
        "first-run.sh"
        in data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    )
    assert "statusline.py" in data["statusLine"]["command"]
    assert len(data["hooks"]["PreToolUse"]) == 4


def test_AC_A4_settings_merge_marker_tuple_includes_a4(
    tmp_path: Path,
) -> None:
    """The pos-v2-owned marker tuple includes the A4 hook script
    paths (regression: re-merge admits the A4 stanzas as pos-v2-
    owned without backup)."""
    from first_run_settings import _POS_V2_PRE_TOOL_USE_COMMAND_MARKERS

    assert "objective_binding_gate.py" in _POS_V2_PRE_TOOL_USE_COMMAND_MARKERS
    assert "tdd_guard.py" in _POS_V2_PRE_TOOL_USE_COMMAND_MARKERS
    assert "bash_guard.py" in _POS_V2_PRE_TOOL_USE_COMMAND_MARKERS
    assert "agent_guard.py" in _POS_V2_PRE_TOOL_USE_COMMAND_MARKERS


def test_AC_A4_helper_stanza_builders_present(tmp_path: Path) -> None:
    """``first_run_helper.py`` exposes the new builder functions
    (regression: the four-element list composition is reachable from
    the call site)."""
    from first_run_helper import (
        _objective_binding_gate_stanza,
        _tdd_guard_stanza,
        _bash_guard_stanza,
        _agent_guard_stanza,
    )

    a2 = _objective_binding_gate_stanza(tmp_path)
    a3 = _tdd_guard_stanza(tmp_path)
    a4_bash = _bash_guard_stanza(tmp_path)
    a4_task = _agent_guard_stanza(tmp_path)

    assert "objective_binding_gate.py" in a2["hooks"][0]["command"]
    assert "tdd_guard.py" in a3["hooks"][0]["command"]
    assert "bash_guard.py" in a4_bash["hooks"][0]["command"]
    assert "agent_guard.py" in a4_task["hooks"][0]["command"]
    assert a2["matcher"] == "Edit|Write|MultiEdit"
    assert a3["matcher"] == "Edit|Write|MultiEdit"
    assert a4_bash["matcher"] == "Bash"
    assert a4_task["matcher"] == "Task"
