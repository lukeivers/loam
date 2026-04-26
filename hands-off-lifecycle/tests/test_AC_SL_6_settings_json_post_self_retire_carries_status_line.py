"""AC.SL.6 — post-self-retire settings.json carries the ``statusLine`` entry.

Outcome (per locked plan §4): after the first-run worker completes
its self-retire on a fresh-clone bootstrap, the workspace's
``.claude/settings.json`` contains a top-level ``statusLine`` entry
whose ``command`` field references the renderer script's absolute
path, whose ``type`` is ``command``, and whose ``refreshInterval``
is 1.

Exercises ``_self_retire`` directly (the existing fixture pattern in
``test_first_run.py`` for AC37 / AC.M.11) since the worker's full
Phase 6 invocation requires real services.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_helper import _self_retire  # noqa: E402


@pytest.fixture
def fresh_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    (ws / "hands-off-lifecycle" / "hooks").mkdir(parents=True)
    (ws / "orchestrator" / "scripts").mkdir(parents=True)
    (ws / "orchestrator" / "scripts" / "pos_session_start.py").write_text(
        "# placeholder\n"
    )
    return ws


def test_AC_SL_6_self_retire_writes_status_line_entry(
    fresh_workspace: Path,
) -> None:
    settings_path = fresh_workspace / ".claude" / "settings.json"

    _self_retire(
        pos_v2_root=fresh_workspace,
        settings_path=settings_path,
    )

    data = json.loads(settings_path.read_text())
    assert "statusLine" in data, (
        f"post-self-retire settings.json missing statusLine: keys="
        f"{sorted(data.keys())}"
    )
    sl = data["statusLine"]
    assert sl.get("type") == "command", f"unexpected statusLine type: {sl!r}"
    assert sl.get("refreshInterval") == 1, (
        f"unexpected refreshInterval: {sl!r}"
    )
    cmd = sl.get("command", "")
    assert "hands-off-lifecycle/hooks/statusline.py" in cmd, (
        f"statusLine.command does not reference renderer script: {cmd!r}"
    )
