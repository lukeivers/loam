"""AC.SL.8 — supervisor retrofits ``statusLine`` on existing workspace.

Outcome (per locked plan §4 / D5 ruling 2026-04-26): a workspace that
has already completed first-run before this amendment landed (its
state-file says ``status=completed``, no ``statusLine`` entry in its
``.claude/settings.json``) gains the ``statusLine`` entry on its next
supervisor-path session-start, without re-running first-run.

Exercises ``_maybe_install_status_line`` directly — the supervisor
side's retrofit helper. The helper is fail-soft and idempotent.

The helper imports ``first_run_settings`` from the workspace's
``hands-off-lifecycle/hooks/`` directory; in production that directory
is the real pos-v2 hooks dir. The test points the workspace's hooks
dir at the real one via symlink so the test process imports a single
``first_run_settings`` module (avoiding dataclass-identity surprises
that arise when the same module is loaded twice under different paths).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR_PATH = (
    REPO_ROOT / "orchestrator" / "scripts" / "pos_session_start.py"
)
REAL_HOOKS_DIR = REPO_ROOT / "hands-off-lifecycle" / "hooks"


def _load_supervisor_module():
    """Load orchestrator/scripts/pos_session_start.py as a module.

    Avoids touching the real orchestrator package (which would pull
    third-party deps not on the test path); the script is self-
    contained for the retrofit helper.

    Registers the loaded module in ``sys.modules`` BEFORE executing —
    Python 3.13's dataclass decorator looks up ``cls.__module__`` in
    ``sys.modules`` while processing module-level dataclass
    annotations; an unregistered module yields ``None`` and the
    decorator raises ``AttributeError``. Caching by module name
    additionally avoids repeated load + dataclass-identity churn
    across the test suite.
    """
    name = "pos_session_start_for_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SUPERVISOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def _seed_completed_workspace(workspace: Path) -> None:
    """Mirror the post-first-run on-disk shape: completed state, no statusLine.

    Symlinks the workspace's ``hands-off-lifecycle/hooks/`` at the real
    repo's hooks dir so the retrofit helper imports the single real
    ``first_run_settings`` module rather than a duplicate copy.
    """
    (workspace / ".claude").mkdir(parents=True, exist_ok=True)
    (workspace / "hands-off-lifecycle").mkdir(parents=True, exist_ok=True)
    # Symlink hooks at the real hooks dir.
    (workspace / "hands-off-lifecycle" / "hooks").symlink_to(REAL_HOOKS_DIR)

    # Pre-existing settings.json with hooks but no statusLine.
    settings = {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                f"{workspace}/.venv/bin/python "
                                f"{workspace}/orchestrator/scripts/"
                                "pos_session_start.py"
                            ),
                            "async": False,
                            "timeout": 20,
                        }
                    ],
                }
            ],
        }
    }
    (workspace / ".claude" / "settings.json").write_text(
        json.dumps(settings, indent=2)
    )

    state_dir = workspace / ".pos"
    state_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "status": "completed",
        "pid": 0,
        "started_at": time.time() - 600.0,
        "updated_at": time.time() - 600.0,
        "phase": "complete",
        "detail": "first-run finished; supervisor stanza active",
        "error_code": 0,
        "remediation": "",
        "generation": 1,
        "workspace_root": str(workspace.resolve()),
        "progress_pct": 100,
    }
    (state_dir / "first-run.state").write_text(json.dumps(state))


def test_AC_SL_8_supervisor_installs_status_line_on_completed_workspace(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    _seed_completed_workspace(workspace)

    settings_path = workspace / ".claude" / "settings.json"
    pre_data = json.loads(settings_path.read_text())
    assert "statusLine" not in pre_data, (
        "test fixture invariant: pre-retrofit settings has no statusLine"
    )

    module = _load_supervisor_module()
    module._maybe_install_status_line(workspace)

    post_data = json.loads(settings_path.read_text())
    assert "statusLine" in post_data, (
        f"retrofit failed to install statusLine: keys="
        f"{sorted(post_data.keys())}"
    )
    sl = post_data["statusLine"]
    assert sl.get("type") == "command"
    assert sl.get("refreshInterval") == 1
    assert "hands-off-lifecycle/hooks/statusline.py" in sl.get("command", "")
    # Pre-existing SessionStart preserved.
    assert "pos_session_start.py" in (
        post_data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    )


def test_AC_SL_8_retrofit_is_fail_soft(tmp_path: Path) -> None:
    """An unworkable workspace must not crash the retrofit helper."""
    workspace = tmp_path / "no-such-shape"
    # Don't create the workspace — the directory doesn't exist.
    module = _load_supervisor_module()
    # Should swallow all exceptions, return None.
    module._maybe_install_status_line(workspace)
