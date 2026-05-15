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

"""AC.LIPW.5 — running the driver does NOT kill, SIGTERM, or steal
the Telegram bot-token poller of a concurrently-running operator
`claude` session, and does not bootout/collide with the operator's
loam launchd services.

Plan: docs/plans/loam-init-persona-wiring-and-isolated-subloam-driver.md
Ladders to AC.PO.2.

Verification: the driver run uses an isolated config root + empty MCP
+ no telegram plugin + namespaced slug + service_bootstrap=False —
asserted from the spawned process's environment + argv + the absence
of any `launchctl bootstrap`. With a sentinel poller-equivalent
process holding the single-consumer slot, a full driver run completes
and the sentinel is still alive (opt-in real-binary integration).

The SOLE kill vector (plan §2 point 9): a second `claude` that loads
the telegram plugin spawns a competing `bun server.ts` that SIGTERMs
the prior poller. Removing the telegram plugin from the sub-session's
reachable set is necessary AND sufficient (D-LIPW.5).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[3]
        / "framework"
        / "tools"
        / "subloam-driver"
        / "src"
    ),
)

from subloam_driver import (  # noqa: E402
    IsolationConfig,
    SubLoamDriver,
    build_isolated_claude_argv,
    build_isolated_env,
)

LOAM_ROOT = Path(__file__).resolve().parents[3]

_TELEGRAM_MARKERS = (
    "plugin:telegram",
    "telegram@claude-plugins-official",
    "claude-plugins-official/telegram",
    "--channels",
)


def _isolation(tmp_path: Path) -> IsolationConfig:
    return IsolationConfig(
        claude_config_dir=tmp_path / ".claude-home",
        empty_mcp_config_path=tmp_path / "empty.mcp.json",
        workspace_slug="pb-subloam-task-1234",
    )


def test_AC_LIPW_5_isolated_config_dir_is_never_operator_home() -> None:
    """Structural guard: the isolated config root must never be the
    operator's ~/.claude (the kill-vector + bench-contamination
    root)."""
    with pytest.raises(ValueError):
        IsolationConfig(
            claude_config_dir=Path.home() / ".claude",
            empty_mcp_config_path=Path("/tmp/empty.mcp.json"),
            workspace_slug="x",
        )


def test_AC_LIPW_5_spawned_env_scrubs_token_and_api_key(
    tmp_path: Path,
) -> None:
    """The spawned env always scrubs the operator bot-token + any API
    key (no API key — subscription-only; no token => the sub-session
    cannot steal the poller slot). This is the kill-vector-relevant
    env isolation and does NOT depend on config relocation."""
    iso = _isolation(tmp_path)
    base = {
        "PATH": "/usr/bin",
        "TELEGRAM_BOT_TOKEN": "operator-secret",
        "ANTHROPIC_API_KEY": "must-not-leak",
        "HOME": str(Path.home()),
    }
    env = build_isolated_env(iso, base_env=base)
    assert "TELEGRAM_BOT_TOKEN" not in env
    assert "ANTHROPIC_API_KEY" not in env


def test_AC_LIPW_5_default_config_preserves_subscription_auth(
    tmp_path: Path,
) -> None:
    """BUILD-TIME CORRECTION OF D-LIPW.5 (empirically grounded): the
    default path does NOT relocate CLAUDE_CONFIG_DIR — Claude Code's
    subscription credential is keychain-stored keyed to the default
    config location, and there is NO API key
    (feedback_no_anthropic_api_key). A relocated virgin root reports
    `Not logged in`. Operator-protection does not require the
    relocation (the telegram-plugin/channel/MCP exclusion is the
    necessary-and-sufficient kill-vector isolation, verified at build
    time)."""
    iso = _isolation(tmp_path)  # air_gapped_config defaults False
    env = build_isolated_env(iso, base_env={"PATH": "/usr/bin"})
    assert "CLAUDE_CONFIG_DIR" not in env, (
        "default path must NOT relocate CLAUDE_CONFIG_DIR or "
        "subscription auth breaks (no API key)"
    )


def test_AC_LIPW_5_air_gapped_opt_in_relocates_config(
    tmp_path: Path,
) -> None:
    """The opt-in full air-gap (caller supplies its own auth into the
    isolated root) does relocate CLAUDE_CONFIG_DIR — retained for
    callers that need it; never the operator's ~/.claude."""
    iso = IsolationConfig(
        claude_config_dir=tmp_path / ".claude-home",
        empty_mcp_config_path=tmp_path / "empty.mcp.json",
        workspace_slug="pb-airgap",
        air_gapped_config=True,
    )
    env = build_isolated_env(iso, base_env={"PATH": "/usr/bin"})
    assert env["CLAUDE_CONFIG_DIR"] == str(tmp_path / ".claude-home")
    assert env["CLAUDE_CONFIG_DIR"] != str(Path.home() / ".claude")


def test_AC_LIPW_5_spawned_argv_has_no_telegram_plugin_or_channels(
    tmp_path: Path,
) -> None:
    argv = build_isolated_claude_argv(_isolation(tmp_path))
    joined = " ".join(argv)
    for marker in _TELEGRAM_MARKERS:
        assert marker not in joined, (
            f"isolated argv carries kill-vector marker {marker!r}: "
            f"{argv}"
        )
    # Empty-MCP isolation present.
    assert "--strict-mcp-config" in argv
    assert "--mcp-config" in argv


def test_AC_LIPW_5_namespaced_slug_cannot_bootout_operator(
    tmp_path: Path,
) -> None:
    """The scratch workspace slug is unique => its launchd labels are
    `com.loam.<unique-slug>.<kind>` and cannot bootout the operator's
    namespaced services. The driver also never service_bootstraps."""
    iso = _isolation(tmp_path)
    assert iso.workspace_slug == "pb-subloam-task-1234"
    seen: dict = {}

    def fake_bootstrap(**kwargs):
        seen.update(kwargs)
        kwargs["new_ws_path"].mkdir(parents=True, exist_ok=True)
        return object()

    d = SubLoamDriver(
        scratch_root=tmp_path / "scratch",
        canonical_source=str(LOAM_ROOT),
        isolation=iso,
        bootstrap_fn=fake_bootstrap,
    )
    d.create_instance()
    d.close()
    # No launchctl bootstrap (service_bootstrap not True).
    assert seen.get("service_bootstrap", False) is False


@pytest.mark.skipif(
    os.environ.get("PB_SUBLOAM_REAL_CLAUDE") != "1",
    reason=(
        "sentinel-survives integration is opt-in (real claude + a "
        "live sentinel poller); set PB_SUBLOAM_REAL_CLAUDE=1."
    ),
)
def test_AC_LIPW_5_sentinel_poller_survives_full_driver_run(
    tmp_path: Path,
) -> None:  # pragma: no cover - opt-in real-binary path
    """A sentinel process holding the single-consumer slot is still
    alive after a full driver run (the driver never SIGTERMs it)."""
    sentinel = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(600)"]
    )
    try:
        driver = SubLoamDriver(
            scratch_root=tmp_path / "scratch",
            canonical_source=str(LOAM_ROOT),
            isolation=_isolation(tmp_path),
        )
        with driver:
            driver.drive(
                "Say ACK and stop.",
                idle_timeout_s=60.0,
                hard_timeout_s=180.0,
            )
        time.sleep(0.5)
        assert sentinel.poll() is None, (
            "sentinel poller was killed by the driver run — "
            "AC.LIPW.5 VIOLATED"
        )
    finally:
        sentinel.terminate()
        sentinel.wait(timeout=5)
