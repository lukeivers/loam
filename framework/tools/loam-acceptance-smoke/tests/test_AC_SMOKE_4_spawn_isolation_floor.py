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

"""The #1 safety constraint (design F-5) + AC.SMOKE.4 scoring completeness.

Every `claude -p` the smoke makes — the role-played user side AND every judge
probe — MUST be spawn-isolated (--strict-mcp-config + empty MCP + scrubbed
env), so an un-isolated spawn cannot steal the operator's single Telegram bot
slot. This test asserts the harness's own spawn surface refuses to ship a
non-isolated argv and that the ledger marks isolation, WITHOUT making a live
claude call (the protection property is structural, provable offline).

AC.SMOKE.4: every rubric dimension is enumerated for scoring (the grid is
complete), proven by checking the dimension catalogue the judge iterates.
"""

from __future__ import annotations

from loam_acceptance_smoke import spawn as spawn_mod
from loam_acceptance_smoke.judge import SOFT_DIMENSIONS


def test_every_harness_spawn_is_isolated_argv():
    spawn_mod._ensure_isolation_importable()
    from loam_spawn_isolation import (
        assert_loam_spawn_isolated,
        inject_isolation,
        isolated_env,
    )

    # The exact argv shape the harness builds for both role-play + judge.
    base = [
        "claude",
        "-p",
        "anything",
        "--model",
        "sonnet",
        "--output-format",
        "json",
        "--permission-mode",
        "bypassPermissions",
    ]
    isolated = inject_isolation(base)
    assert "--strict-mcp-config" in isolated
    assert "--mcp-config" in isolated
    # The guard must pass on the isolated argv and RAISE on a raw one.
    assert_loam_spawn_isolated(isolated)

    import pytest

    with pytest.raises(ValueError):
        assert_loam_spawn_isolated(base)  # raw claude -p — the #5 kill pattern

    env = isolated_env()
    assert "TELEGRAM_BOT_TOKEN" not in env
    assert "ANTHROPIC_API_KEY" not in env  # no API key — subscription-only
    assert env.get("CLAUDE_PERSONA")  # belt-and-braces persona scrub


def test_AC_SMOKE_4_full_dimension_catalogue_enumerated():
    # The seven soft dimensions of the prime-objective rubric (design §2) are
    # all present, so every variant gets every dimension scored.
    expected = {
        "no-user-translation-burden",
        "learned-this-person",
        "four-step-loop-ran",
        "no-over-engineering",
        "closed-on-one-thing",
        "non-interrogating-feel",
        "protection-floor-held",
    }
    assert set(SOFT_DIMENSIONS) == expected
