"""AC D8.1 — SessionStart additionalContext emission.

Outcome (from amendment plan §4 D8.1): on a workspace whose baseline
corpus is present, a single invocation of the persona-layer
session-start composer returns an ``additionalContext``-shaped payload
whose serialised form contains (a) baseline corpus paths + present
indicator, (b) in-flight ``amendment-*.md`` paths, (c) service-state
fields for memory + orchestrator, (d) cost-governance MTD/headroom,
(e) a ``corpus_gate_state`` sentinel with value loaded/partial/missing,
and (f) a recent-first-run-completion timestamp + generation marker.
The serialised payload's byte length is strictly less than 10,000
characters in the baseline workspace shape.

One test function per sub-requirement, all named ``test_D8_1_*``.
Test fixtures synthesise a baseline workspace — the AC is workspace-
shape-agnostic and must be testable without depending on the live
pos-v2 tree.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.primary_persona.context_composer import (
    ADDITIONAL_CONTEXT_CAP,
    ComposedContextPayload,
    CorpusGateState,
)
from loam.primary_persona.session_start_gate import compose_session_fields


def _seed_baseline_workspace(root: Path) -> None:
    """Write the baseline corpus + in-flight amendment + service
    sidecars into *root*. Mirrors the CLAUDE.md session-start
    discipline section's named paths."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(
        "# test workspace\n\n"
        "## Session-start discipline\n\n"
        "Before acting, read:\n\n"
        "- `docs/odd-methodology.md`\n"
        "- `docs/odd-in-loam.md`\n"
        "- `docs/rebuild/VALUE_PROPOSITION.md`\n"
        "- `docs/rebuild/STATE.md`\n"
        "- `docs/rebuild/FUTURE_IDEAS.md`\n"
        "\n---\n\n"
    )
    (root / "docs").mkdir()
    (root / "docs" / "odd-methodology.md").write_text("odd")
    (root / "docs" / "odd-in-loam.md").write_text("in-pos")
    (root / "docs" / "rebuild").mkdir()
    (root / "docs" / "rebuild" / "VALUE_PROPOSITION.md").write_text("vp")
    (root / "docs" / "rebuild" / "STATE.md").write_text("state")
    (root / "docs" / "rebuild" / "FUTURE_IDEAS.md").write_text("ideas")
    (root / "docs" / "rebuild" / "plans").mkdir()
    # Two in-flight amendments; enumerated by glob.
    (root / "docs" / "rebuild" / "plans" / "amendment-one.md").write_text("#1")
    (root / "docs" / "rebuild" / "plans" / "amendment-two.md").write_text("#2")
    # First-run state with a completed_at timestamp. D-migration D.2
    # (amendment #63): workspace-state under <ws>/workspace/.pos/
    # post-D.2.
    pos = root / "workspace" / ".pos"
    pos.mkdir(parents=True)
    (pos / "first-run.state").write_text(
        json.dumps({"completed_at": "2026-04-24T00:00:00Z"})
    )
    (pos / "cost-headroom.json").write_text(
        json.dumps({"mtd_spend_usd": "12.34", "ceiling_usd": "500.00"})
    )


def test_D8_1_corpus_paths_with_present_indicator(tmp_path: Path) -> None:
    """(a) Baseline corpus paths each carry a file-present indicator."""
    _seed_baseline_workspace(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    payload = composer.on_session_start(tmp_path)

    paths = {p: present for p, present in payload.corpus_paths}
    assert "CLAUDE.md" in paths
    assert "docs/odd-methodology.md" in paths
    assert "docs/odd-in-loam.md" in paths
    assert "docs/rebuild/VALUE_PROPOSITION.md" in paths
    assert "docs/rebuild/STATE.md" in paths
    assert "docs/rebuild/FUTURE_IDEAS.md" in paths
    # Every present-indicator is True on a complete workspace.
    assert all(present for present in paths.values())


def test_D8_1_amendments_in_flight_enumerated(tmp_path: Path) -> None:
    """(b) In-flight ``amendment-*.md`` paths under
    ``docs/rebuild/plans/`` are listed."""
    _seed_baseline_workspace(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    payload = composer.on_session_start(tmp_path)

    assert "docs/rebuild/plans/amendment-one.md" in payload.amendments_in_flight
    assert "docs/rebuild/plans/amendment-two.md" in payload.amendments_in_flight


def test_D8_1_service_state_fields_present(tmp_path: Path) -> None:
    """(c) Service-state fields for the memory sidecar and
    orchestrator exist in the payload."""
    _seed_baseline_workspace(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    payload = composer.on_session_start(tmp_path)

    assert "memory" in payload.service_state
    assert "orchestrator" in payload.service_state
    # Values are short status strings per the gate's contract.
    assert payload.service_state["memory"] in {"up", "down", "unknown"}
    assert payload.service_state["orchestrator"] in {"up", "down", "unknown"}


def test_D8_1_cost_headroom_exposed(tmp_path: Path) -> None:
    """(d) Cost-governance MTD spend + ceiling headroom are surfaced
    when the sidecar is present."""
    _seed_baseline_workspace(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    payload = composer.on_session_start(tmp_path)

    assert "mtd_spend_usd" in payload.cost_headroom
    assert "ceiling_usd" in payload.cost_headroom


def test_D8_1_corpus_gate_state_sentinel_loaded(tmp_path: Path) -> None:
    """(e) Sentinel has value ``loaded`` when every baseline path is
    present."""
    _seed_baseline_workspace(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    payload = composer.on_session_start(tmp_path)

    assert payload.corpus_gate_state == CorpusGateState.loaded


def test_D8_1_first_run_and_generation_marker(tmp_path: Path) -> None:
    """(f) Recent first-run completion timestamp + generation marker
    are present."""
    _seed_baseline_workspace(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    payload = composer.on_session_start(tmp_path)

    assert payload.first_run_completion == "2026-04-24T00:00:00Z"
    assert payload.generation_marker


def test_D8_1_serialised_length_under_cap(tmp_path: Path) -> None:
    """The serialised payload's byte length is strictly less than
    10,000 characters in the baseline workspace shape."""
    _seed_baseline_workspace(tmp_path)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    payload = composer.on_session_start(tmp_path)

    assert len(payload.additional_context_text) < ADDITIONAL_CONTEXT_CAP
