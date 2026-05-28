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

"""AC.KP9.3 — the gate routes EVERY user-facing surface.

The gate fires on persona free-text, drift proposals, the SessionStart
summary, and any miss-recovery — every outbound user-facing surface, not
just persona free-text. A non-free-text surface carrying a leak is
blocked too.

Method is the builder's call (ODD §1.1): the same leak is run through
every declared surface kind and asserted to block in each, and the
STAGED PreToolUse-chain contributor is asserted to route a draft pulled
from a user-facing tool envelope.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
KEEP_PACE_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
sys.path.insert(0, str(KEEP_PACE_DIR))

from draft_gate import (  # noqa: E402
    SURFACE_KINDS,
    build_draft_gate_contributor,
    gate,
)


@pytest.mark.parametrize("surface_kind", sorted(SURFACE_KINDS))
def test_AC_KP9_3_leak_blocked_on_every_surface_kind(surface_kind: str) -> None:
    """A leak on ANY user-facing surface kind is blocked — not just
    persona free-text (a session-start summary string with a leak is
    blocked too)."""
    leaky = "Last session you were on retrieval.py; next likely the next file."
    result = gate(leaky, surface_kind=surface_kind)
    assert result.blocked(), (
        f"leak on surface {surface_kind!r} should block: {result.verdict}"
    )


def test_AC_KP9_3_session_start_summary_string_gated() -> None:
    """The session-start summary (a non-free-text surface) carrying a
    leak is blocked (AC.KP9.3 explicit example)."""
    summary = "Last session you were on AC.KP9.1; next likely AC.KP9.2."
    result = gate(summary, surface_kind="session-start-summary")
    assert result.blocked()


def test_AC_KP9_3_drift_proposal_surface_gated() -> None:
    """A drift-proposal surface is routed through the same gate."""
    proposal = "I propose marking the §3 objective dormant."
    result = gate(proposal, surface_kind="drift-proposal")
    assert result.blocked()  # the §3 doc-pointer leaks


def test_AC_KP9_3_contributor_routes_user_facing_tool_draft() -> None:
    """The STAGED PreToolUse-chain contributor extracts the draft from a
    user-facing tool envelope and routes it through the gate."""
    contributor = build_draft_gate_contributor()
    envelope = {
        "tool_name": "mcp__plugin_telegram_telegram__reply",
        "tool_input": {"message": "The fix is in retrieval.py for you."},
    }
    report = contributor(envelope)
    assert report is not None, "a leaky user-facing draft should yield a report"
    assert "BLOCK" in report


def test_AC_KP9_3_contributor_silent_on_non_user_facing_tool() -> None:
    """A tool that is not a user-facing send surface yields no report
    (the gate only routes outbound user-facing drafts)."""
    contributor = build_draft_gate_contributor()
    envelope = {
        "tool_name": "Bash",
        "tool_input": {"command": "cat retrieval.py"},
    }
    assert contributor(envelope) is None


def test_AC_KP9_3_contributor_silent_on_clean_user_facing_draft() -> None:
    """A clean user-facing draft passes → the contributor stays silent."""
    contributor = build_draft_gate_contributor()
    envelope = {
        "tool_name": "mcp__plugin_telegram_telegram__reply",
        "tool_input": {"message": "Done — your fiction batch is queued."},
    }
    assert contributor(envelope) is None
