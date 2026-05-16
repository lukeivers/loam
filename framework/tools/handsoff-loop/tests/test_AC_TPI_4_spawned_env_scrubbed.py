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

"""AC.TPI.4 — the env every §1b site spawns has TELEGRAM_BOT_TOKEN /
CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN / ANTHROPIC_API_KEY absent.

Plan: docs/plans/telegram-poller-isolation-fix.md
Contract: pos3/.../telegram-isolation-fix-plan-2026-05-16.md §3.3
Fast structural assertion.  Mirrors
`test_AC_LIPW_5_spawned_env_scrubs_token_and_api_key`.  Closes the env
half of the kill vector (no bot token => the §1b sub-session cannot
steal the operator's single-consumer poller slot) + honours
`feedback_no_anthropic_api_key` (no API key — subscription-only; the
keychain-stored credential resolves because CLAUDE_CONFIG_DIR is left
unset).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop._isolation import isolated_env  # noqa: E402


def test_AC_TPI_4_isolated_env_scrubs_token_and_api_key() -> None:
    """The §1b spawn env scrubs the operator bot-token spellings + any
    API key.  This is the env half the consumer
    (`orchestrator._dispatch_subagent`) and `intake._claude_json` both
    pass to `subprocess.run`."""
    base = {
        "PATH": "/usr/bin",
        "HOME": str(Path.home()),
        "TELEGRAM_BOT_TOKEN": "operator-secret",
        "CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN": "operator-secret-2",
        "ANTHROPIC_API_KEY": "must-not-leak",
    }
    env = isolated_env(base)
    assert "TELEGRAM_BOT_TOKEN" not in env
    assert "CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN" not in env
    assert "ANTHROPIC_API_KEY" not in env
    # Non-kill-vector env survives (the §1b sites still need PATH/HOME
    # for the real binary to resolve + the keychain credential).
    assert env["PATH"] == "/usr/bin"
    assert env["HOME"] == str(Path.home())


def test_AC_TPI_4_default_path_preserves_subscription_auth() -> None:
    """`feedback_no_anthropic_api_key`: the §1b isolation does NOT
    relocate CLAUDE_CONFIG_DIR (a relocated virgin root reports `Not
    logged in` with no API key).  Operator-protection does not depend
    on the relocation — the telegram-plugin/empty-MCP/env-scrub
    exclusion is the necessary-and-sufficient kill-vector isolation."""
    env = isolated_env({"PATH": "/usr/bin"})
    assert "CLAUDE_CONFIG_DIR" not in env, (
        "the §1b isolation must NOT relocate CLAUDE_CONFIG_DIR or "
        "subscription auth breaks (no API key)"
    )
