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

"""AC.SECHK.6 — Three new safety-layer hook entries land in
<workspace>/.claude/settings.json at first-run scaffold AND on
re-merge. Idempotent. User-authored stanzas preserved.

Multi-contributor settings-merge contract for the Wave 1 ECC
absorption security-hooks-bundle amendment.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import (  # noqa: E402
    build_config_write_guard_stanza,
    build_dangerous_flag_guard_stanza,
    build_safety_layer_stanzas,
    build_secret_pattern_guard_stanza,
    merge_pre_tool_use,
)


def _a2_stanza(loam_root: Path) -> dict:
    """Existing A2 objective-binding-gate stanza for re-merge
    coexistence tests."""
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


def test_AC_SECHK_6_first_write_lands_three_safety_layer_hooks(
    tmp_path: Path,
) -> None:
    """Fresh settings.json scaffold — three safety-layer stanzas
    land under hooks.PreToolUse in registration order."""
    settings_path = tmp_path / "settings.json"
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=build_safety_layer_stanzas(tmp_path),
    )
    assert result.wrote
    assert result.backup_path is None
    data = json.loads(settings_path.read_text())
    pte = data["hooks"]["PreToolUse"]
    assert len(pte) == 3
    assert "secret_pattern_guard.py" in pte[0]["hooks"][0]["command"]
    assert "dangerous_flag_guard.py" in pte[1]["hooks"][0]["command"]
    assert "config_write_guard.py" in pte[2]["hooks"][0]["command"]


def test_AC_SECHK_6_matchers_correct_per_hook(tmp_path: Path) -> None:
    """secret_pattern_guard fires on Bash + Edit + Write + MultiEdit;
    dangerous_flag_guard fires on Bash only; config_write_guard on
    Edit + Write + MultiEdit only."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=build_safety_layer_stanzas(tmp_path),
    )
    data = json.loads(settings_path.read_text())
    pte = data["hooks"]["PreToolUse"]
    matchers = [stanza["matcher"] for stanza in pte]
    assert matchers[0] == "Bash|Edit|Write|MultiEdit"
    assert matchers[1] == "Bash"
    assert matchers[2] == "Edit|Write|MultiEdit"


def test_AC_SECHK_6_re_merge_idempotent_no_backup(tmp_path: Path) -> None:
    """Re-running the merge over a settings.json we wrote does NOT
    create a backup (every inner-hook command matches a recognised
    pos-v2 marker)."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=build_safety_layer_stanzas(tmp_path),
    )
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=build_safety_layer_stanzas(tmp_path),
    )
    assert result.wrote
    assert result.backup_path is None


def test_AC_SECHK_6_compose_with_a2_no_backup(tmp_path: Path) -> None:
    """A pre-existing pos-v2 stanza (A2 only) re-merged with A2 +
    safety-layer stanzas — no backup."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path,
        new_entry=_a2_stanza(tmp_path),
    )
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[_a2_stanza(tmp_path)]
        + build_safety_layer_stanzas(tmp_path),
    )
    assert result.wrote
    assert result.backup_path is None
    data = json.loads(settings_path.read_text())
    pte = data["hooks"]["PreToolUse"]
    assert len(pte) == 4
    assert "objective_binding_gate.py" in pte[0]["hooks"][0]["command"]


def test_AC_SECHK_6_user_authored_pretooluse_triggers_backup(
    tmp_path: Path,
) -> None:
    """User-authored PreToolUse stanza is preserved via backup
    when the safety-layer stanzas land."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "/some/user/hook.sh",
                                }
                            ],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=build_safety_layer_stanzas(tmp_path),
    )
    assert result.wrote
    assert result.backup_path is not None
    assert result.backup_path.is_file()
    backup = json.loads(result.backup_path.read_text())
    assert "/some/user/hook.sh" in (
        backup["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    )


def test_AC_SECHK_6_individual_stanza_shapes(tmp_path: Path) -> None:
    """Individual builders return a well-formed Claude Code hook
    stanza envelope."""
    for builder in (
        build_secret_pattern_guard_stanza,
        build_dangerous_flag_guard_stanza,
        build_config_write_guard_stanza,
    ):
        stanza = builder(tmp_path)
        assert "matcher" in stanza
        assert "hooks" in stanza
        assert isinstance(stanza["hooks"], list)
        assert len(stanza["hooks"]) == 1
        inner = stanza["hooks"][0]
        assert inner["type"] == "command"
        assert "command" in inner
        assert inner["async"] is False
        assert isinstance(inner["timeout"], int)
