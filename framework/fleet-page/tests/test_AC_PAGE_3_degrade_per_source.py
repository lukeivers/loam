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

"""AC.PAGE.3.

With ONE source unavailable (its reader raises), ``generate_page`` still
writes the page: the remaining panels render and the missing one is
labeled "source unavailable" — no blank page, no invented data.

Drives the real entry point ``generate_page`` with one raising source."""

from __future__ import annotations

from conftest import fixture_fleet, stub_cost_rows, stub_decisions
from loam.fleet_page import generate_page


def _raise():
    raise RuntimeError("source down")


def test_AC_PAGE_3_cost_source_down_other_panels_render(tmp_path):
    out = tmp_path / "fleet.html"
    generate_page(
        out,
        fleet_source=fixture_fleet,     # available
        cost_source=_raise,             # DOWN
        decisions_source=stub_decisions,  # available
    )
    html = out.read_text(encoding="utf-8")
    # Page is not blank; the two available panels still render.
    assert "Live agents" in html
    assert "building" in html
    assert "Needs a human" in html
    assert "Ratify the launchd default interval" in html
    # The cost panel is labeled unavailable — NOT invented as $0 / 0 tokens.
    assert "source unavailable" in html
    assert "token proxy" not in html   # the real cost strip did not render
    assert "Input tok" not in html     # no fabricated token table
    assert "No recorded token cost" not in html  # not a false empty state


def test_AC_PAGE_3_decisions_source_down_other_panels_render(tmp_path):
    out = tmp_path / "fleet.html"
    generate_page(
        out,
        fleet_source=fixture_fleet,
        cost_source=stub_cost_rows,
        decisions_source=_raise,        # DOWN
    )
    html = out.read_text(encoding="utf-8")
    assert "Live agents" in html
    assert "token proxy" in html        # cost strip still there
    assert "source unavailable" in html  # the decision panel is labeled
    # It must NOT falsely claim nothing is queued when the source is down.
    assert "Nothing is waiting on you" not in html


def test_AC_PAGE_3_fleet_source_down_labels_both_fleet_panels(tmp_path):
    out = tmp_path / "fleet.html"
    generate_page(
        out,
        fleet_source=_raise,            # DOWN — feeds live + outcomes
        cost_source=stub_cost_rows,
        decisions_source=stub_decisions,
    )
    html = out.read_text(encoding="utf-8")
    # Both fleet-derived panels labeled unavailable; the independent
    # panels still render.
    assert html.count("source unavailable") == 2
    assert "token proxy" in html
    assert "Needs a human" in html
    # No fabricated live/finished rows.
    assert "<tbody>" not in html.split("This week's cost")[0]


def test_AC_PAGE_3_empty_is_not_missing(tmp_path):
    """§5 empty-vs-missing: an EMPTY (present) source renders its own
    empty state, never the "source unavailable" label."""
    out = tmp_path / "fleet.html"
    generate_page(
        out,
        fleet_source=lambda: {"runs": []},   # present, empty
        cost_source=lambda: [],              # present, empty
        decisions_source=lambda: [],         # present, empty
    )
    html = out.read_text(encoding="utf-8")
    assert "source unavailable" not in html          # nothing is MISSING
    assert "No agents are running right now." in html
    assert "Nothing is waiting on you." in html
    assert "No recorded token cost this window." in html
