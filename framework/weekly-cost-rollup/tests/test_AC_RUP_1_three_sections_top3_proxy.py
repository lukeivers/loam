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

"""AC.RUP.1 (outcome-altitude) — three-section message, top-3, proxy label.

Drives the REAL production entry point ``run_rollup`` with the REAL transcript
parser pointed at a fixture ``~/.claude/projects``-shaped directory; only the
sealed probe and the gateway boundary are injected. Also proves the two
correctness properties a naive sum would miss (D-A5-1b): per-(message.id,
requestId) DEDUP and the weekly TIMESTAMP window — a wrong ranking is not a
correct one, so both ladder up to "correct top-3 ranking".
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from conftest import CapturingNotify, probe_returning, unavailable, windows_at, write_transcript

from loam.usage_window_guard import UnavailableReason
from loam.weekly_cost_rollup import (
    GatewayUnavailable,
    TokenUsageUnavailable,
    read_project_tokens,
    run_rollup,
)


def _gateway_absent():
    return GatewayUnavailable(reason="not_configured", detail="gateway pending")


def test_AC_RUP_1_three_sections_top3_and_proxy_label(tmp_path):
    root = tmp_path / "projects"
    # Distinct in-window totals so the top-3 ordering is unambiguous.
    write_transcript(root, "alpha", entries=[{"tokens": 5000}])
    write_transcript(root, "beta", entries=[{"tokens": 9000}])
    write_transcript(root, "gamma", entries=[{"tokens": 1000}])
    write_transcript(root, "delta", entries=[{"tokens": 7000}])

    capturing = CapturingNotify()
    # five_hour set high + distinct so we prove the WEEKLY window is read, not it.
    message = run_rollup(
        probe=probe_returning(windows_at(42.0, five_hour_pct=99.0)),
        token_source=lambda: read_project_tokens(root=root),
        gateway_source=_gateway_absent,
        notify_fn=capturing,
    )

    # Always delivers (D-A5-3); returns what it delivered.
    assert capturing.messages == [message]

    # Three sections present.
    assert "Weekly cost roll-up" in message
    assert "Claude weekly cap (this machine): 42.0% of the enforced limit." in message
    assert "Metered-model spend (month-to-date): gateway pending." in message

    # Reads the WEEKLY window, not the 5-hour throttle.
    assert "99.0%" not in message

    # Proxy label mandatory (D-A5-4).
    assert "proxy — ranks consumption, not billing-grade" in message

    # Top-3 ranking correct + descending; the 4th (gamma) is dropped.
    assert "1. beta — 9,000 tokens" in message
    assert "2. delta — 7,000 tokens" in message
    assert "3. alpha — 5,000 tokens" in message
    assert "gamma" not in message
    assert message.index("1. beta") < message.index("2. delta") < message.index("3. alpha")

    # Stays under the ~15-line chat-channel budget (D-A5-7).
    assert message.count("\n") + 1 <= 15


def test_AC_RUP_1_token_source_absent_named_absence_label_survives(tmp_path):
    # A projects root that exists but has no project dirs → no_transcripts.
    empty = tmp_path / "projects"
    empty.mkdir()

    capturing = CapturingNotify()
    message = run_rollup(
        probe=probe_returning(windows_at(30.0)),
        token_source=lambda: read_project_tokens(root=empty),
        gateway_source=_gateway_absent,
        notify_fn=capturing,
    )

    # The token section is PRESENT and names its absence — not dropped (D-A5-5)...
    assert "Top Claude-token projects" in message
    assert "no_transcripts" in message
    # ...the proxy label survives even the empty-ranking path...
    assert "proxy — ranks consumption, not billing-grade" in message
    # ...and the other sections still render.
    assert "Claude weekly cap (this machine): 30.0% of the enforced limit." in message


def test_AC_RUP_1_dedup_counts_a_repeated_message_once(tmp_path):
    root = tmp_path / "projects"
    # Same (message_id, request_id) emitted twice (a resumed/compacted session).
    write_transcript(
        root,
        "resumed",
        entries=[
            {"tokens": 1000, "message_id": "m1", "request_id": "r1"},
            {"tokens": 1000, "message_id": "m1", "request_id": "r1"},
        ],
    )
    result = read_project_tokens(root=root)
    assert not isinstance(result, TokenUsageUnavailable)
    assert len(result) == 1
    # Counted ONCE, not summed to 2000.
    assert result[0].tokens == 1000


def test_AC_RUP_1_windows_out_stale_activity(tmp_path):
    root = tmp_path / "projects"
    old = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    write_transcript(
        root,
        "windowed",
        entries=[
            {"tokens": 1000, "message_id": "recent", "request_id": "r-recent"},
            {"tokens": 999999, "message_id": "old", "request_id": "r-old", "timestamp": old},
        ],
    )
    # Default 7-day window excludes the 10-day-old block.
    result = read_project_tokens(root=root)
    assert not isinstance(result, TokenUsageUnavailable)
    assert result[0].tokens == 1000


def test_AC_RUP_1_cap_unavailable_named_absence_no_number(tmp_path):
    root = tmp_path / "projects"
    write_transcript(root, "alpha", entries=[{"tokens": 5000}])

    capturing = CapturingNotify()
    message = run_rollup(
        probe=probe_returning(unavailable(UnavailableReason.AUTH_REJECTED)),
        token_source=lambda: read_project_tokens(root=root),
        gateway_source=_gateway_absent,
        notify_fn=capturing,
    )

    # Cap section is a NAMED absence carrying the categorical reason...
    assert "auth_rejected" in message
    assert "unavailable" in message
    # ...and NO utilization percentage (the "available" phrase never renders).
    assert "% of the enforced limit" not in message
