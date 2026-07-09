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

"""AC.RUP.2b — gateway unreachable: the other two sections + a NAMED absence.

A run with the metered-model gateway unreachable emits the cap and token
sections and renders the gateway section as a named absence — never a silent
drop (D-A5-5). Also covers the default gateway source (D1 not signed up).
"""

from __future__ import annotations

from conftest import CapturingNotify, probe_returning, windows_at, write_transcript

from loam.weekly_cost_rollup import (
    GatewaySpend,
    GatewayUnavailable,
    read_gateway_spend,
    read_project_tokens,
    run_rollup,
)


def test_AC_RUP_2b_gateway_unreachable_names_absence_keeps_two_sections(tmp_path):
    root = tmp_path / "projects"
    write_transcript(root, "alpha", entries=[{"tokens": 5000}])

    capturing = CapturingNotify()
    message = run_rollup(
        probe=probe_returning(windows_at(30.0)),
        token_source=lambda: read_project_tokens(root=root),
        gateway_source=lambda: GatewayUnavailable(reason="unreachable"),
        notify_fn=capturing,
    )

    # The other two sections are present and real.
    assert "Claude weekly cap (this machine): 30.0% of the enforced limit." in message
    assert "Top Claude-token projects" in message
    assert "1. alpha — 5,000 tokens" in message

    # The gateway section is PRESENT and names its absence — not dropped.
    assert "Metered-model spend (month-to-date):" in message
    assert "unreachable" in message


def test_AC_RUP_2b_default_gateway_source_is_named_not_configured():
    result = read_gateway_spend()
    assert isinstance(result, GatewayUnavailable)
    assert result.reason == "not_configured"
    assert "D1" in result.detail


def test_AC_RUP_2b_configured_gateway_renders_dollars(tmp_path):
    root = tmp_path / "projects"
    write_transcript(root, "alpha", entries=[{"tokens": 5000}])

    capturing = CapturingNotify()
    message = run_rollup(
        probe=probe_returning(windows_at(30.0)),
        token_source=lambda: read_project_tokens(root=root),
        gateway_source=lambda: GatewaySpend(amount_usd=4.20, period="2026-07"),
        notify_fn=capturing,
    )
    assert "Metered-model spend (month-to-date, 2026-07): $4.20." in message
