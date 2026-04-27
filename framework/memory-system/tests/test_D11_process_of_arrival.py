"""D11 — process-of-arrival capture ingestion tests (amendment #15).

D11's acceptance criterion (docs/rebuild/components/memory-system/
brief-full-build.md §D11, lines ~102-109):

    Objective: background dispatches' stream-of-consciousness logs
    are summarised and ingested alongside outcomes.

    Acceptance:
    - A representative background dispatch (mocked, since the
      dispatch primitive is not yet built) produces a stream log
      during execution; the log is summarised (by Claude via Max)
      and ingested.
    - A retrieval query returns both the outcome and the reasoning
      path when either is queried.
    - Soft dependency: the dispatch primitive is not yet built. This
      deliverable ships as a receiver with a mock producer.

D11's AC text explicitly declares the mocked path is the full proof
("*mocked, since dispatch primitive not yet built*"). No real-dispatch
integration test is planned, dormant, or skipif'd here — that belongs
to a future dispatch-primitive component's own scope.

Each test below maps 1:1 to a named sub-behaviour under D11; every
name starts with ``test_D11_`` so grepping by the AC code finds the
full cluster (ODD §8.2 rule 9 — one test per named AC sub-behaviour).

Mocking strategy: the receiver's two injection points — ``memory_ingest``
(a callable) and ``llm_client`` (a Graphiti LLM client) — are both
documented public constructor parameters on ``ProcessOfArrivalReceiver``.
Tests substitute an async-callable capture for the former and a fake
client exposing ``async generate_response(...)`` for the latter. No
real subprocess, no real Graphiti, no network, no real DB.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.observability import Emitter, reset_default_emitter
from src.process_of_arrival import (
    MockStreamLogProducer,
    ProcessOfArrivalReceiver,
    make_mock_log,
)
from src.retention import RetentionClass


# ---- fixtures -------------------------------------------------------


class _FakeLLMClient:
    """Test double for the ``llm_client`` injection point.

    Matches the ``async generate_response(messages, response_model,
    max_tokens, prompt_name)`` signature that ``ProcessOfArrivalReceiver.
    _summarise`` calls. Returns a fixed validated payload shaped like
    the receiver's private ``_StreamSummary`` pydantic model. Records
    each call's kwargs for inspection.
    """

    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self.payload = payload or {
            "objective": "Decide Velmar's first Latin America market.",
            "decisions": [
                "Candidates narrowed to Brazil, Chile, Argentina, Uruguay.",
                "Brazil selected on market size + partner availability.",
            ],
            "reasoning": (
                "Brazil dominated raw volume (~3x Chile); ANVISA complexity "
                "is medium; Lente Pampero is a viable partner."
            ),
            "tools_used": ["market-sizing table", "ANVISA registry"],
            "conclusion": "Brazil first, secondary sweep after 12 months.",
        }
        self.calls: list[dict[str, Any]] = []

    async def generate_response(
        self,
        messages: list[Any],
        response_model: Any = None,
        max_tokens: int = 0,
        prompt_name: str | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "messages": messages,
                "response_model": response_model,
                "max_tokens": max_tokens,
                "prompt_name": prompt_name,
            }
        )
        return self.payload


class _IngestCapture:
    """Test double for the ``memory_ingest`` injection point.

    Records every keyword-argument set the receiver passes to the
    ingest callable; returns a deterministic synthetic UUID per call
    so the two episodes are distinguishable.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def __call__(self, **kwargs: Any) -> str:
        self.calls.append(kwargs)
        return f"uuid-{len(self.calls)}"


def _make_receiver(
    *,
    ingest: _IngestCapture | None = None,
    llm: _FakeLLMClient | None = None,
) -> tuple[ProcessOfArrivalReceiver, _IngestCapture, _FakeLLMClient]:
    ing = ingest or _IngestCapture()
    llm_client = llm or _FakeLLMClient()
    receiver = ProcessOfArrivalReceiver(
        memory_ingest=ing,
        llm_client=llm_client,
    )
    return receiver, ing, llm_client


def _fresh_log(
    *,
    dispatch_id: str = "velmar-market-analysis-2029-01-03",
    scope_id: str = "velmar_entry_decision",
    persona: str | None = "rho-quant",
    lines: list[str] | None = None,
    outcome: str | None = None,
):
    now = datetime.now(timezone.utc)
    return make_mock_log(
        dispatch_id=dispatch_id,
        scope_id=scope_id,
        persona=persona,
        started_at=now - timedelta(minutes=3),
        ended_at=now,
        outcome=outcome
        or (
            "Recommendation: enter Brazil first. Rationale: 3x market "
            "size, partner available, comparable regulatory friction."
        ),
        lines=lines,
    )


# ---- tests ----------------------------------------------------------


@pytest.mark.asyncio
async def test_D11_mock_producer_log_is_summarised_and_ingested_as_two_episodes(
    tmp_path,
) -> None:
    """AC sub-behaviour #1 + #3 — a mocked background dispatch produces
    a stream log; the log is summarised (via the injected LLM client,
    standing in for Claude-via-Max) and ingested as two linked episodes
    (outcome + reasoning summary).

    Exercised through the ``MockStreamLogProducer`` → ``receiver.receive``
    path, which is the same flow a real dispatch primitive will invoke
    once it lands (the receiver's public API is what the primitive will
    call in production).
    """
    reset_default_emitter(Emitter(sink_dir=tmp_path))
    receiver, ingest, llm = _make_receiver()

    log = _fresh_log()
    producer = MockStreamLogProducer(logs=[log])
    next_log = await producer.next_log()
    assert next_log is log, "mock producer should emit the log we fed it"

    result = await receiver.receive(next_log)

    # Two episodes were ingested, with distinct UUIDs.
    assert result.outcome_episode_uuid != result.summary_episode_uuid
    assert len(ingest.calls) == 2

    # The LLM was invoked once for summarisation; the summary text is
    # non-empty and contains the structured headings the receiver
    # formats from the summariser response (objective / decisions /
    # reasoning / tools used / conclusion).
    assert len(llm.calls) == 1
    assert llm.calls[0]["prompt_name"] == "process_of_arrival.summarise"
    assert result.summary_text
    for heading in ("Objective:", "Decisions:", "Reasoning:", "Conclusion:"):
        assert heading in result.summary_text

    # Result links back to the input log's dispatch id.
    assert result.dispatch_id == log.dispatch_id


@pytest.mark.asyncio
async def test_D11_both_episodes_share_scope_id_and_dispatch_linkage(
    tmp_path,
) -> None:
    """AC sub-behaviour #2 (ingest-side precondition) — both episodes
    carry the same ``scope_id`` and their names encode the dispatch id,
    so a retrieval-by-scope or retrieval-by-dispatch-id returns both.

    The receiver does not own the retrieval engine (MemoryAPI does);
    the receiver's contract is the ingest-boundary invariant that makes
    the retrieval guarantee possible. Asserting at the ingest boundary
    is where the receiver's responsibility ends.
    """
    reset_default_emitter(Emitter(sink_dir=tmp_path))
    receiver, ingest, _ = _make_receiver()

    log = _fresh_log(
        dispatch_id="dispatch-xyz",
        scope_id="some-scope-abc",
    )
    await receiver.receive(log)

    outcome_call, summary_call = ingest.calls

    # Both episodes are tagged with the log's scope_id — the anchor
    # retrieval-by-scope uses.
    assert outcome_call["scope_id"] == log.scope_id
    assert summary_call["scope_id"] == log.scope_id

    # Episode names encode dispatch id + role, so a query on either
    # half can reach the other by name-prefix.
    assert outcome_call["name"] == f"dispatch:{log.dispatch_id}:outcome"
    assert summary_call["name"] == f"dispatch:{log.dispatch_id}:reasoning"

    # The reasoning body carries an explicit cross-reference back to
    # the outcome episode, so traversal from the reasoning side can
    # reach the outcome.
    assert f"dispatch:{log.dispatch_id}:outcome" in summary_call["body"]


@pytest.mark.asyncio
async def test_D11_reasoning_episode_is_tagged_derived_only_and_outcome_is_normal(
    tmp_path,
) -> None:
    """The receiver's retention-class contract (per D11 brief +
    receiver docstring): raw stream is NOT persisted, summary IS.

    The outcome episode carries ``RetentionClass.NORMAL`` (its raw text
    — the outcome — is preserved). The reasoning episode carries
    ``RetentionClass.DERIVED_ONLY`` (its raw text — the summary prose
    — is scrubbed post-extraction; only the structured facts persist
    in the graph). This is the necessary-and-sufficient precondition
    for the "raw stream not persisted" guarantee.
    """
    reset_default_emitter(Emitter(sink_dir=tmp_path))
    receiver, ingest, _ = _make_receiver()

    await receiver.receive(_fresh_log())

    outcome_call, summary_call = ingest.calls
    assert outcome_call["retention_class"] == RetentionClass.NORMAL
    assert summary_call["retention_class"] == RetentionClass.DERIVED_ONLY


@pytest.mark.asyncio
async def test_D11_audit_record_captures_the_process_of_arrival_ingest(
    tmp_path,
) -> None:
    """D7 observability contract for D11: an audit entry is written
    when the receiver ingests a process-of-arrival capture, naming the
    dispatch_id + both episode UUIDs + the retention decision. Without
    this audit record, a later reader cannot reconstruct that the raw
    stream was intentionally not persisted — D7's "reconstructible
    without a consumer" guarantee would fail for D11's flow.
    """
    emitter = Emitter(sink_dir=tmp_path)
    reset_default_emitter(emitter)
    receiver, _, _ = _make_receiver()

    log = _fresh_log(dispatch_id="audit-target-dispatch")
    result = await receiver.receive(log)

    audit_entries = emitter.read_audit()
    poa_entries = [
        a for a in audit_entries if a["operation"] == "process_of_arrival.ingest"
    ]
    assert len(poa_entries) == 1, (
        f"expected exactly one process_of_arrival.ingest audit entry, "
        f"got {len(poa_entries)}"
    )
    entry = poa_entries[0]
    assert entry["scope_id"] == log.scope_id
    assert entry["extras"]["dispatch_id"] == log.dispatch_id
    assert entry["extras"]["outcome_episode_uuid"] == result.outcome_episode_uuid
    assert entry["extras"]["summary_episode_uuid"] == result.summary_episode_uuid
    # The rationale names the retention-class decision — this is the
    # human-readable surface that records "raw stream NOT persisted".
    assert "derived-only" in entry["rationale"]


@pytest.mark.asyncio
async def test_D11_oversized_stream_is_truncated_before_summarisation(
    tmp_path,
) -> None:
    """Receiver invariant (``ProcessOfArrivalReceiver.receive`` lines
    126-128, backed by config §process_of_arrival.max_stream_chars):
    oversized logs are truncated before the summariser sees them. The
    cap defaults to 24000 chars. The truncation marker is embedded in
    the excerpt so the summariser knows content was elided.
    """
    reset_default_emitter(Emitter(sink_dir=tmp_path))
    receiver, _, llm = _make_receiver()

    # Build a log whose raw_stream_text exceeds the cap by a known
    # amount. The receiver reads max_stream_chars from config at
    # construction time, so we read it from the receiver directly to
    # stay resilient to config edits (the invariant is "truncated at
    # the configured cap", not "truncated at 24000 specifically").
    cap = receiver._max_stream_chars  # noqa: SLF001 — reading to keep the assertion calibrated; not asserting on it
    overflow = 500
    big_line = "x" * (cap + overflow)
    log = _fresh_log(lines=[big_line])
    assert len(log.raw_stream_text) > cap

    await receiver.receive(log)

    # The fake LLM captured the exact user_content the summariser sent.
    assert len(llm.calls) == 1
    user_content = llm.calls[0]["messages"][1].content
    # The truncation marker appears in the excerpt. The marker format
    # is documented in receiver.receive: "[truncated: N chars elided]".
    assert "[truncated:" in user_content
    assert "chars elided]" in user_content
    # The stream excerpt (before the marker) is exactly cap chars of
    # 'x' — the truncation happened at the documented boundary.
    stream_header_marker = "STREAM:\n"
    stream_start = user_content.index(stream_header_marker) + len(stream_header_marker)
    truncation_start = user_content.index("\n\n[truncated:")
    excerpt = user_content[stream_start:truncation_start]
    assert len(excerpt) == cap
    assert set(excerpt) == {"x"}
