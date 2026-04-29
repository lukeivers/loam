"""AC40.3 — Graceful failure on tracker unavailability.

If the tracker DB cannot be read (simulated via permissions, missing
file, schema-version mismatch, or any other read-side failure), the
contributor:

- does NOT raise into the registry's invocation path,
- emits a structured diagnostic via the existing observability
  surface naming the failure class,
- contributes either an empty block or a graceful-degradation marker
  block.

The session's other contributors continue to fire normally.

Maps to: primary-persona context-composer error-isolation (amendment
#32 D8) + amendment #33 D7 graceful-degradation precedent → AC.PO.1.

Plan: docs/rebuild/plans/amendment-40-primary-persona-tracker-context-contributor.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loam.primary_persona.context_composer import ComposedContextPayload, TriggerKind
from loam.primary_persona.session_start_gate import compose_session_fields
from loam.primary_persona.tracker_context import register_tracker_context

from _helpers_d40 import FakeTrackerClient
from _helpers_d7 import seed_baseline_workspace


def test_AC40_3_tracker_open_failure_does_not_raise(
    tmp_path: Path, span_exporter_clean: Any
) -> None:
    """``tracker_factory`` raises on open. The contributor must not
    propagate the exception out of the composer's invocation path.
    """
    workspace_root = tmp_path / "ws-ac40-3"
    seed_baseline_workspace(workspace_root)

    def factory_that_raises():
        raise OSError("simulated permission denied")

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=factory_that_raises,
    )

    # Must NOT raise.
    payload = composer.on_session_start(workspace_root)
    outputs = dict(payload.contributor_outputs)
    # The contributor MAY emit empty contribution; it MUST NOT emit
    # the existing composer's "[contributor X raised: ...]" sentinel
    # which would indicate the inner exception propagated.
    block = outputs.get("tracker-context", "")
    assert "[contributor tracker-context raised:" not in block, (
        "AC40.3 — tracker-side exception must be caught by the contributor, "
        "NOT by the composer's outer sandbox"
    )

    # Structured diagnostic emitted with the failure class.
    spans = span_exporter_clean.get_finished_spans()
    matching = [s for s in spans if s.name == "loam.persona.tracker_context.unavailable"]
    assert matching, (
        "AC40.3 — tracker_context_unavailable_event must fire on open failure"
    )
    # Failure class on the event attributes.
    found_failure_class = False
    found_detail = False
    for span in matching:
        for ev in span.events:
            attrs = dict(ev.attributes or {})
            if attrs.get("loam.persona.tracker_context.failure_class") == "OSError":
                found_failure_class = True
            if attrs.get("loam.persona.tracker_context.detail") == "tracker_open_failed":
                found_detail = True
    assert found_failure_class, "AC40.3 — failure_class attr must name OSError"
    assert found_detail, "AC40.3 — detail must name tracker_open_failed"


def test_AC40_3_query_failure_does_not_raise(
    tmp_path: Path, span_exporter_clean: Any
) -> None:
    """The tracker opens but ``query_projection_view`` raises (e.g.,
    schema-version mismatch on a partially-corrupted DB)."""
    workspace_root = tmp_path / "ws-ac40-3b"
    seed_baseline_workspace(workspace_root)

    client = FakeTrackerClient(query_raises=RuntimeError("schema mismatch"))

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
    )

    payload = composer.on_session_start(workspace_root)
    block = dict(payload.contributor_outputs).get("tracker-context", "")
    assert "[contributor tracker-context raised:" not in block, (
        "AC40.3 — query-side exception must be handled inside the contributor"
    )

    spans = span_exporter_clean.get_finished_spans()
    matching = [s for s in spans if s.name == "loam.persona.tracker_context.unavailable"]
    assert matching, (
        "AC40.3 — tracker_context_unavailable_event must fire on query failure"
    )

    # Per AC: read-only access; close MUST still be called even on
    # query failure (resource hygiene).
    assert client.close_calls, (
        "AC40.3 — tracker.close() must be called even when query raises"
    )


def test_AC40_3_other_contributors_still_fire(tmp_path: Path) -> None:
    """The session's other contributors continue to fire when the
    tracker-context contributor degrades. AC40.3 names this contract
    explicitly."""
    workspace_root = tmp_path / "ws-ac40-3c"
    seed_baseline_workspace(workspace_root)

    def factory_that_raises():
        raise OSError("simulated")

    composer = ComposedContextPayload(session_builder=compose_session_fields)

    # Other session-level contributor — stand-in for any unrelated
    # registered surface.
    def sibling(ctx: dict) -> str:
        return "SIBLING-CONTRIB-FIRED"

    composer.register(name="sibling", trigger_kind=TriggerKind.session, fn=sibling)

    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=factory_that_raises,
    )

    payload = composer.on_session_start(workspace_root)
    outputs = dict(payload.contributor_outputs)
    assert outputs.get("sibling") == "SIBLING-CONTRIB-FIRED", (
        "AC40.3 — sibling contributors must fire regardless of tracker-context degradation"
    )
