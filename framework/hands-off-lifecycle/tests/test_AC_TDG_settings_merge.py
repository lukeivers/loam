"""``merge_pre_tool_use`` writes both A2's gate AND A3's TDD-guard as
pos-v2-owned PreToolUse stanzas — multi-contributor settings-merge
contract for the structural-enforcement A3 amendment.

Mirrors AC.OBG.settings_merge byte-for-byte for the single-contributor
case (regression), and adds multi-contributor coverage:

  * A3 supplies new_entries=[a2_stanza, a3_stanza]; result has both
    inner-hook commands recognised as pos-v2-owned.
  * Re-merge over a stanza pos-v2 wrote does NOT create a backup.
  * Re-merge over a user-authored stanza creates a backup AND
    preserves the prior bytes.
  * Single-contributor (legacy A2 call shape) byte-equivalent.

Settings-merge is the support surface for AC.TDG.S (seal-diff fence)
and AC.TDG.8 (helper-library equivalence) — the new merge function
shape MUST preserve A2's existing AC.OBG.settings_merge tests
byte-for-byte.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import merge_pre_tool_use  # noqa: E402


def _a2_stanza(loam_root: Path) -> dict:
    script = (
        loam_root
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


def _a3_stanza(loam_root: Path) -> dict:
    script = (
        loam_root
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


def test_first_write_creates_multi_contributor_pre_tool_use_stanza(
    tmp_path: Path,
) -> None:
    """First write with new_entries=[a2, a3] produces both stanzas in
    order under hooks.PreToolUse."""
    settings_path = tmp_path / "settings.json"
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[_a2_stanza(tmp_path), _a3_stanza(tmp_path)],
    )
    assert result.wrote is True
    assert result.backup_path is None
    data = json.loads(settings_path.read_text())
    pte = data["hooks"]["PreToolUse"]
    assert len(pte) == 2
    assert "objective_binding_gate.py" in pte[0]["hooks"][0]["command"]
    assert "tdd_guard.py" in pte[1]["hooks"][0]["command"]


def test_re_merge_over_pos_v2_owned_multi_no_backup(tmp_path: Path) -> None:
    """Re-merge over a multi-contributor pos-v2 stanza (both A2 and A3
    markers present) does NOT create a backup."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[_a2_stanza(tmp_path), _a3_stanza(tmp_path)],
    )
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[_a2_stanza(tmp_path), _a3_stanza(tmp_path)],
    )
    assert result.wrote is True
    assert result.backup_path is None


def test_re_merge_over_legacy_single_contributor_no_backup(
    tmp_path: Path,
) -> None:
    """A pre-A3 settings.json carries ONLY A2's stanza. Re-merging
    with both A2 + A3 must NOT trigger the backup path — the prior
    stanza is pos-v2-owned (A2 marker recognised)."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path,
        new_entry=_a2_stanza(tmp_path),
    )
    # Now upgrade to multi-contributor.
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[_a2_stanza(tmp_path), _a3_stanza(tmp_path)],
    )
    assert result.wrote is True
    assert result.backup_path is None
    data = json.loads(settings_path.read_text())
    pte = data["hooks"]["PreToolUse"]
    assert len(pte) == 2


def test_re_merge_over_user_authored_creates_backup(tmp_path: Path) -> None:
    """Re-merge over a user-authored PreToolUse stanza (whose inner-
    hook commands don't match pos-v2 markers) creates a timestamped
    backup AND preserves the prior stanza inside the backup."""
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
        new_entries=[_a2_stanza(tmp_path), _a3_stanza(tmp_path)],
        now_iso="20260428T120000Z",
    )
    assert result.wrote is True
    assert result.backup_path is not None
    assert result.backup_path.exists()

    backup_data = json.loads(result.backup_path.read_text())
    assert (
        backup_data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        == "/usr/local/bin/my-bash-guard"
    )

    data = json.loads(settings_path.read_text())
    assert data.get("user_key") == "preserved"
    pte = data["hooks"]["PreToolUse"]
    assert len(pte) == 2
    assert "objective_binding_gate.py" in pte[0]["hooks"][0]["command"]
    assert "tdd_guard.py" in pte[1]["hooks"][0]["command"]


def test_single_contributor_call_shape_byte_compat(tmp_path: Path) -> None:
    """The legacy A2 single-contributor call (new_entry=, not
    new_entries=) continues to write exactly [new_entry] under
    hooks.PreToolUse — byte-equivalent to pre-A3 behaviour. This is
    the regression-protection for AC.OBG.settings_merge."""
    settings_path = tmp_path / "settings.json"
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entry=_a2_stanza(tmp_path),
    )
    assert result.wrote is True
    data = json.loads(settings_path.read_text())
    assert len(data["hooks"]["PreToolUse"]) == 1
    assert (
        "objective_binding_gate.py"
        in data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    )


def test_pre_tool_use_merge_preserves_orthogonal_stanzas(tmp_path: Path) -> None:
    """Multi-contributor PreToolUse merge does NOT touch a pre-existing
    SessionStart / UserPromptSubmit / Stop / statusLine entry."""
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
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "X -m loam.primary_persona Y",
                                    "async": False,
                                    "timeout": 5,
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
        new_entries=[_a2_stanza(tmp_path), _a3_stanza(tmp_path)],
    )

    data = json.loads(settings_path.read_text())
    assert (
        "first-run.sh"
        in data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    )
    assert (
        "primary_persona"
        in data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    )
    assert "statusline.py" in data["statusLine"]["command"]
    assert len(data["hooks"]["PreToolUse"]) == 2
