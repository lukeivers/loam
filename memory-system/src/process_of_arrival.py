"""D11 — Process-of-arrival capture ingestion.


Background dispatches emit stream-of-consciousness logs during
execution. Those logs are summarised (by Claude via Max) and ingested
alongside the dispatch's outcome, so memory records the reasoning
path, not only the final output.

**Soft dependency:** the dispatch primitive is not yet built. This
module ships as a receiver with a mock producer — the receiver is
the live code that summarises + ingests; the producer is a test-only
stand-in until the real dispatch primitive lands.

Interface:

    StreamLogProducer (Protocol) — emits `StreamLog` records during
                                   a dispatch. Any real dispatch
                                   runtime must conform to this.

    ProcessOfArrivalReceiver   — takes a StreamLog, summarises it
                                 via Claude, and ingests the summary
                                 alongside the dispatch outcome as
                                 linked episodes with retention-class
                                 `derived-only` (the raw stream is not
                                 persisted; the summary is).

The ingest pattern: two episodes per dispatch.
  - One for the final outcome (retention class = NORMAL by default).
  - One for the summary of the reasoning path (retention class =
    DERIVED_ONLY by default, since the raw stream doesn't persist).

Both are tagged with the dispatch's `scope_id` so retrieval-by-scope
returns both episodes; a query for either the outcome or the reasoning
returns both, satisfying the spec acceptance criterion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from .config import section
from .observability import default_emitter, record_audit
from .retention import RetentionClass


@dataclass
class StreamLog:
    """A dispatch's stream-of-consciousness log.

    `lines` is the raw stream; `outcome` is the final output; `metadata`
    carries dispatch_id, scope_id, persona (when known), start/end times.
    The dispatch primitive is expected to hand this to the receiver at
    completion.
    """

    dispatch_id: str
    scope_id: str
    persona: str | None
    started_at: datetime
    ended_at: datetime
    outcome: str
    lines: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def raw_stream_text(self) -> str:
        return "\n".join(self.lines)


class StreamLogProducer(Protocol):
    """Contract any dispatch runtime must conform to.

    For now, only tests / mocks implement this. The real dispatch
    primitive, when built, implements it by collecting its own
    stream-of-consciousness output.
    """

    async def next_log(self) -> StreamLog | None: ...


# ----- receiver -------------------------------------------------------


@dataclass
class ProcessOfArrivalResult:
    dispatch_id: str
    outcome_episode_uuid: str
    summary_episode_uuid: str
    summary_text: str


class ProcessOfArrivalReceiver:
    """Summarises a StreamLog and ingests it alongside the outcome.

    `memory_ingest` is the memory-level ingest function, a callable
    taking kwargs `(name, body, source_description, reference_time,
    scope_id, retention_class)` and returning an episode UUID. Injected
    so this class does not depend on the full MemoryAPI construction
    path — tests substitute a fake ingest.

    `llm_client` is a Graphiti AnthropicClient (or equivalent); we use
    it to produce a summary. The brief requires Claude via Max; this
    injection keeps that single-source rule.
    """

    def __init__(
        self,
        *,
        memory_ingest,  # callable
        llm_client,
    ) -> None:
        self._ingest = memory_ingest
        self._llm = llm_client
        cfg = section("process_of_arrival")
        self._max_stream_chars: int = int(cfg.get("max_stream_chars", 24000))
        self._summary_target_tokens: int = int(cfg.get("summary_target_tokens", 500))
        self._retention_class = RetentionClass(cfg.get("retention_class", "derived-only"))

    async def receive(self, log: StreamLog) -> ProcessOfArrivalResult:
        stream_excerpt = log.raw_stream_text[: self._max_stream_chars]
        if len(log.raw_stream_text) > self._max_stream_chars:
            stream_excerpt += f"\n\n[truncated: {len(log.raw_stream_text) - self._max_stream_chars} chars elided]"
        summary = await self._summarise(stream_excerpt, log)

        emitter = default_emitter()
        with emitter.span(
            "process_of_arrival.ingest",
            attributes={
                "dispatch_id": log.dispatch_id,
                "scope_id": log.scope_id,
                "persona": log.persona,
                "stream_chars": len(log.raw_stream_text),
                "summary_chars": len(summary),
            },
        ) as span:
            outcome_uuid = await self._ingest(
                name=f"dispatch:{log.dispatch_id}:outcome",
                body=log.outcome,
                source_description=f"background dispatch outcome — {log.persona or 'unknown'}",
                reference_time=log.ended_at,
                scope_id=log.scope_id,
                retention_class=RetentionClass.NORMAL,
            )
            summary_uuid = await self._ingest(
                name=f"dispatch:{log.dispatch_id}:reasoning",
                body=(
                    f"Reasoning summary for dispatch {log.dispatch_id} "
                    f"(persona={log.persona or 'unknown'}):\n\n{summary}\n\n"
                    f"Outcome episode: dispatch:{log.dispatch_id}:outcome"
                ),
                source_description=f"background dispatch reasoning path — {log.persona or 'unknown'}",
                reference_time=log.ended_at,
                scope_id=log.scope_id,
                retention_class=self._retention_class,
            )
            span.set_attr("outcome_episode_uuid", outcome_uuid)
            span.set_attr("summary_episode_uuid", summary_uuid)

        record_audit(
            operation="process_of_arrival.ingest",
            actor="memory-system",
            scope_id=log.scope_id,
            subject_uuid=summary_uuid,
            rationale=(
                f"Summarised {len(log.lines)}-line stream from dispatch "
                f"{log.dispatch_id}; raw stream NOT persisted (retention={self._retention_class.value})."
            ),
            extras={
                "dispatch_id": log.dispatch_id,
                "outcome_episode_uuid": outcome_uuid,
                "summary_episode_uuid": summary_uuid,
            },
        )
        return ProcessOfArrivalResult(
            dispatch_id=log.dispatch_id,
            outcome_episode_uuid=outcome_uuid,
            summary_episode_uuid=summary_uuid,
            summary_text=summary,
        )

    async def _summarise(self, stream: str, log: StreamLog) -> str:
        """Claude-via-Max summary of the stream-of-consciousness log.

        Kept narrow: target ~500 tokens, preserve decision points and
        the path of reasoning rather than the exhaustive transcript.
        """
        from graphiti_core.prompts.models import Message
        from pydantic import BaseModel, Field

        class _StreamSummary(BaseModel):
            objective: str = Field(description="the dispatch's stated objective")
            decisions: list[str] = Field(description="key decision points in order")
            reasoning: str = Field(description="the reasoning path that led to each decision")
            tools_used: list[str] = Field(
                default_factory=list,
                description="tools called or external lookups performed",
            )
            conclusion: str = Field(description="the conclusion the dispatch reached")

        system = (
            "You are summarising a background dispatch's stream-of-"
            "consciousness log so its reasoning path can be recalled "
            "later alongside its outcome. Be concise; preserve the path "
            "of reasoning, not the entire transcript."
        )
        user_content = (
            f"Dispatch id: {log.dispatch_id}\n"
            f"Persona: {log.persona or 'unknown'}\n"
            f"Scope: {log.scope_id}\n"
            f"Duration: {(log.ended_at - log.started_at).total_seconds():.1f}s\n\n"
            "STREAM:\n"
            f"{stream}"
        )
        resp = await self._llm.generate_response(
            [
                Message(role="system", content=system),
                Message(role="user", content=user_content),
            ],
            response_model=_StreamSummary,
            max_tokens=self._summary_target_tokens * 2,
            prompt_name="process_of_arrival.summarise",
        )
        # resp is the validated tool-use output as a dict.
        summary = _StreamSummary(**resp)
        decisions_md = "\n".join(f"  - {d}" for d in summary.decisions) or "  (none recorded)"
        tools_md = "\n".join(f"  - {t}" for t in summary.tools_used) or "  (none recorded)"
        return (
            f"Objective: {summary.objective}\n\n"
            f"Decisions:\n{decisions_md}\n\n"
            f"Reasoning: {summary.reasoning}\n\n"
            f"Tools used:\n{tools_md}\n\n"
            f"Conclusion: {summary.conclusion}"
        )


# ----- mock producer (used by tests until dispatch primitive lands) --


@dataclass
class MockStreamLogProducer:
    """Test producer emitting a fixed list of StreamLog records."""

    logs: list[StreamLog]
    _cursor: int = 0

    async def next_log(self) -> StreamLog | None:
        if self._cursor >= len(self.logs):
            return None
        log = self.logs[self._cursor]
        self._cursor += 1
        return log


def make_mock_log(
    *,
    dispatch_id: str,
    scope_id: str,
    persona: str | None = "sample-persona",
    outcome: str = "The analysis concluded that entering Brazil first was optimal.",
    lines: list[str] | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
) -> StreamLog:
    """Helper used by tests to fabricate a StreamLog."""
    now = datetime.now(timezone.utc)
    if lines is None:
        lines = [
            "Considering Brazil vs Chile vs Argentina for Velmar entry.",
            "Pulled market sizing: Brazil ~3x Chile; regulatory friction comparable.",
            "Ran sensitivity: Brazil wins under 80% of scenarios.",
            "Checked partner availability: Lente Pampero is promising.",
            "Concluded Brazil is the recommended first market.",
        ]
    return StreamLog(
        dispatch_id=dispatch_id,
        scope_id=scope_id,
        persona=persona,
        started_at=started_at or now,
        ended_at=ended_at or now,
        outcome=outcome,
        lines=lines,
    )
