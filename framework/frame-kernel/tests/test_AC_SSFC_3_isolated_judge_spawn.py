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

"""AC.SSFC.3 — the judge runs as an ISOLATED subscription ``claude -p``:
the spawned invocation carries the spawn-isolation flags + scrubbed env
(no Telegram bot-token, no API key), never a bare un-isolated spawn.

The test asserts the argv the judge constructs goes through the mandated
``spawn_isolated_claude`` surface: after isolation it carries
``--strict-mcp-config`` + an empty ``--mcp-config``, the sealed
``assert_loam_spawn_isolated`` PASSES on it, and a bare
``["claude","-p",...]`` (the Telegram-death #5 pattern) FAILS the same
guard. The env is the scrubbed/persona-set isolated env (no bot-token, no
``ANTHROPIC_API_KEY``, ``CLAUDE_PERSONA`` set).

Spawn-isolation is the HARD constraint (PROVEN Telegram-drop kill vector
+ no-API-key reality). The judge does NOT hand-roll a raw
``subprocess.run(["claude",...])``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loam.frame_kernel import frame_judge as fj

# The sealed spawn-isolation surface frame_judge composes on. Resolve it
# the same one-line way frame_judge does (it put the src on sys.path at
# import).
_SPAWN_SRC = (
    Path(fj.__file__).resolve().parents[5]
    / "framework"
    / "tools"
    / "loam-spawn-isolation"
    / "src"
)
if str(_SPAWN_SRC) not in sys.path:
    sys.path.insert(0, str(_SPAWN_SRC))

from loam_spawn_isolation import (  # noqa: E402
    ISOLATED_PERSONA_VALUE,
    assert_loam_spawn_isolated,
    inject_isolation,
    isolated_env,
)

import pytest  # noqa: E402


def test_judge_argv_isolated_after_injection() -> None:
    """The judge's base argv, run through the mandated isolation, carries
    the empty-strict-MCP isolation flags + passes the sealed guard."""
    base = fj.build_judge_argv("some prompt")
    isolated = inject_isolation(base)

    assert "--strict-mcp-config" in isolated
    assert "--mcp-config" in isolated
    # The sealed mandate guard PASSES on the isolated argv.
    assert_loam_spawn_isolated(isolated)
    # The caller's -p/json shape is preserved (no reshape).
    assert "-p" in isolated
    assert "json" in isolated


def test_bare_judge_argv_fails_the_isolation_guard() -> None:
    """A bare un-isolated judge spawn (the Telegram-death #5 pattern) is
    REFUSED by the sealed guard — proving the judge MUST go isolated."""
    bare = fj.build_judge_argv("some prompt")  # no isolation injected
    with pytest.raises(ValueError):
        assert_loam_spawn_isolated(bare)


def test_judge_env_scrubs_token_api_key_sets_persona() -> None:
    """The isolated env scrubs the bot-token + API key and sets
    CLAUDE_PERSONA (the belt-and-braces defense)."""
    env = isolated_env(
        {
            "PATH": "/usr/bin",
            "TELEGRAM_BOT_TOKEN": "secret",
            "ANTHROPIC_API_KEY": "must-not-leak",
        }
    )
    assert "TELEGRAM_BOT_TOKEN" not in env
    assert "ANTHROPIC_API_KEY" not in env
    assert env["CLAUDE_PERSONA"] == ISOLATED_PERSONA_VALUE


def test_run_judge_goes_through_spawn_isolated_claude(monkeypatch) -> None:
    """run_judge routes through the SEALED spawn_isolated_claude (NOT a
    hand-rolled subprocess.run): stubbing ONLY subprocess.run inside the
    sealed module, the REAL entry-point still constructs the isolated
    argv + scrubbed env that reach the spawn boundary."""
    import loam_spawn_isolation as iso_mod

    captured: dict = {}

    class _Proc:
        returncode = 0
        stdout = "ok\nON_FRAME"

    def _fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["env"] = kwargs.get("env")
        return _Proc()

    # Stub ONLY the subprocess.run boundary inside the sealed surface —
    # the real spawn_isolated_claude injects isolation + builds the env.
    monkeypatch.setattr(iso_mod.subprocess, "run", _fake_run)

    out = fj.run_judge("a prompt")
    assert out == "ok\nON_FRAME"
    argv = captured["argv"]
    assert argv[0] == "claude"
    assert "--strict-mcp-config" in argv
    assert "--mcp-config" in argv
    # The REAL scrubbed env reached the spawn (not a hand-rolled one).
    env = captured["env"]
    assert env is not None and "ANTHROPIC_API_KEY" not in env
    assert env.get("CLAUDE_PERSONA") == ISOLATED_PERSONA_VALUE
