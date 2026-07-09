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

"""AC.PAGE.1 (outcome-altitude).

From fixture collector JSON + a stubbed decision queue + a stub cost map,
the production entry point (``generate_page``) WRITES an HTML file showing
the live-agent table (status / liveness / elapsed / cost), a
recent-outcomes strip, and the decision queue; the document carries both
themes and guards horizontal overflow.

Drives the real entry point ``generate_page`` (no test-only path)."""

from __future__ import annotations

import re

from conftest import fixture_fleet, stub_cost_rows, stub_decisions
from loam.fleet_page import generate_page


def _write(tmp_path):
    out = tmp_path / "fleet.html"
    written = generate_page(
        out,
        fleet_source=fixture_fleet,
        cost_source=stub_cost_rows,
        decisions_source=stub_decisions,
    )
    assert written == out
    assert out.exists()
    return out.read_text(encoding="utf-8")


def test_AC_PAGE_1_file_is_written_and_is_a_full_html_document(tmp_path):
    html = _write(tmp_path)
    assert html.startswith("<!doctype html>")
    assert "</html>" in html


def test_AC_PAGE_1_live_agent_table_has_status_liveness_elapsed_cost(tmp_path):
    html = _write(tmp_path)
    # Panel present and leads (live feed first, §5 ordering).
    assert "<h2>Live agents" in html
    assert html.index("Live agents") < html.index("Recent outcomes")
    # The four named columns.
    for col in ("Status", "Liveness", "Elapsed", "Cost"):
        assert f"<th>{col}</th>" in html
    # The live run's real values are rendered.
    assert "building" in html          # status/stage
    assert ">live<" in html            # liveness badge
    assert "4m 5s" in html             # elapsed of 245s
    # Honest cost: the live run has no cost_usd → its cost_source, never $0.
    assert "absent" in html
    assert "$0.00" not in html


def test_AC_PAGE_1_recent_outcomes_strip_present(tmp_path):
    html = _write(tmp_path)
    assert "Recent outcomes" in html
    assert "Build a CSV-to-JSON converter" in html   # the finished run
    assert "$0.42" in html                            # its real cost


def test_AC_PAGE_1_decision_queue_present(tmp_path):
    html = _write(tmp_path)
    assert "Needs a human" in html
    assert "Ratify the launchd default interval" in html


def test_AC_PAGE_1_both_themes_declared(tmp_path):
    html = _write(tmp_path)
    # Light defaults in :root plus an explicit dark override.
    assert ":root{" in html
    assert "@media (prefers-color-scheme:dark)" in html


def test_AC_PAGE_1_no_horizontal_overflow_guards(tmp_path):
    html = _write(tmp_path)
    # Wide content scrolls inside its own container, not the body.
    assert "overflow-x:auto" in html
    # The long objective cell wraps rather than forcing body width.
    assert "overflow-wrap:anywhere" in html
    # No element declares a fixed OR minimum px width wider than a narrow
    # phone viewport (~360px) — the actual overflow culprit the AC guards.
    # `max-width` is excluded: it CAPS width and shrinks on narrow screens,
    # so it never forces horizontal overflow.
    wide = [int(w) for w in re.findall(r"(?<!max-)width:\s*(\d+)px", html)]
    assert not any(w > 360 for w in wide), f"fixed wide width(s): {wide}"


def _cost_strip(html: str) -> str:
    """The cost-strip <section> only (from its heading to the next
    </section>)."""
    start = html.index("This week's cost")
    end = html.index("</section>", start)
    return html[start:end]


def test_AC_PAGE_1_cost_strip_is_token_proxy_not_dollars(tmp_path):
    html = _write(tmp_path)
    # The cost strip reports token counts, labeled a proxy — never a
    # dollar figure (isolated agents meter no per-call dollars).
    assert "token proxy" in html
    assert "120,000" in html      # planner input tokens, thousands-formatted
    # No dollar figure inside the cost strip itself (a $ there would be
    # invented — the live table's real cost_usd lives in a different panel).
    assert "$" not in _cost_strip(html)
