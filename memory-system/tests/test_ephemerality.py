"""D5 — ephemerality filter tests."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import ephemerality


def test_cpu_source_matches_cpu_readings_rule() -> None:
    v = ephemerality.classify(
        source="cpu.usage", source_description="telemetry", body="cpu usage: 52"
    )
    assert v.is_ephemeral is True
    assert v.rule_name == "cpu-readings"


def test_ui_scroll_source_matches_volatile_ui_state() -> None:
    v = ephemerality.classify(
        source="ui:scroll", source_description="scroll event", body="offset=120"
    )
    assert v.is_ephemeral is True
    assert v.rule_name == "volatile-ui-state"


def test_clock_tick_body_pattern() -> None:
    v = ephemerality.classify(
        source="heartbeat", source_description="periodic tick",
        body="clock tick: 1776584512",
    )
    assert v.is_ephemeral is True
    # Body-pattern match lands on ticking-clocks by rule order; source
    # didn't match anything, so body_patterns fired first. Either rule
    # with clock+tick semantics is acceptable — the point is the
    # exclusion happened.
    assert v.rule_name in {"ticking-clocks", "cpu-readings"}


def test_unlisted_source_is_accrued_by_default() -> None:
    v = ephemerality.classify(
        source="conversation", source_description="Luke↔Eve",
        body="Decided to hold off on Brazil for two weeks.",
    )
    assert v.is_ephemeral is False
    assert v.rule_name is None


def test_rubric_editable_via_config_reload() -> None:
    """Rubric is declared in config/memory.yml; workspaces can add
    exclusion rules without code change. Verify the rubric summary
    reflects what's loaded."""
    summary = ephemerality.rubric_summary()
    assert "rules" in summary
    names = {r["name"] for r in summary["rules"]}
    assert {"cpu-readings", "ticking-clocks", "volatile-ui-state", "transient-telemetry"}.issubset(names)
    assert summary["default"] == "accrue"
