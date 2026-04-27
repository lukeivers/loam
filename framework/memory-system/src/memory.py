"""MemoryAPI — wired-ready memory surface for the new pOS.

Wires together:

  D5  Ephemerality filter          (src/ephemerality.py)
  D6  Scope-of-work mapper         (src/scope.py)          — mock source
  D7  Observability emission       (src/observability.py)
  D8  Temporal-filter wrapper      (src/temporal.py)
  D10 Retention-class tagger       (src/retention.py)

Not wired here (they live in separate modules that import this):
  D9  Upgrade-fidelity harness     (src/upgrade.py)        — operates OVER memory
  D11 Process-of-arrival receiver  (src/process_of_arrival.py) — calls memory.ingest
  D12 Chaos-durability tests       (scripts/chaos_durability.py)

Public surface (stable; downstream primitives depend on this shape):

    MemoryAPI.ingest(body, *, name, source, reference_time, scope_id,
                     retention_class, ...)                       -> IngestResult
    MemoryAPI.search(query, *, scope_ids, anchor_node_uuid,
                     at_time, num_results, ...)                  -> list[SearchHit]
    MemoryAPI.list_scope(scope_id)                               -> list[ScopeSlice]
    MemoryAPI.list_by_retention(cls)                             -> list[EpisodeRef]

The interface accepts a ScopeSource by injection, so the mock scope
source is replaced by the real scope-of-work primitive at one wiring
site when that primitive lands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

from . import ephemerality, retention, temporal
from .observability import (
    default_emitter,
    record_audit,
    record_llm_usage,
)
from .scope import MockScopeSource, ScopeRecord, ScopeSource


# ---- DTOs ---------------------------------------------------------------


@dataclass
class IngestResult:
    episode_uuid: str | None
    ephemeral: bool
    ephemeral_rule: str | None
    retention_class: str
    scope_id: str
    nodes_created: int = 0
    edges_created: int = 0


@dataclass
class SearchHit:
    fact: str
    edge_uuid: str
    source_node_uuid: str
    target_node_uuid: str
    valid_at: datetime | None
    invalid_at: datetime | None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class EpisodeRef:
    uuid: str
    name: str
    created_at: Any
    retention_class: str | None = None


# ---- cost-snapshot helper (amendment #11 §F3) -------------------------


def _subscription_cost_snapshot(llm_client: Any) -> float | None:
    """Return the current ``cost_tracker.total_usd`` if the LLM client
    is a ``ClaudePrintLLMClient`` (exposes a ``cost_tracker`` with a
    ``total_usd`` float). Returns ``None`` otherwise so callers can
    short-circuit the span attribute emission.

    Probing for the attribute keeps this helper client-agnostic — a
    test that injects a test-double LLM client (or graphiti's own
    base class) won't trip on a missing field.
    """
    tracker = getattr(llm_client, "cost_tracker", None)
    if tracker is None:
        return None
    total = getattr(tracker, "total_usd", None)
    if total is None:
        return None
    try:
        return float(total)
    except (TypeError, ValueError):
        return None


# ---- MemoryAPI ---------------------------------------------------------


class MemoryAPI:
    """Stable memory surface with every D5–D11 layer wired in.

    Construction is intentionally small: the only required dependency is
    a ready `Graphiti` instance. Tests or chaos scenarios inject their
    own ScopeSource / emitter; production wiring uses defaults.
    """

    def __init__(
        self,
        graphiti: Graphiti,
        *,
        scope_source: ScopeSource | None = None,
        emitter=None,
    ) -> None:
        self._graphiti = graphiti
        self._scopes: ScopeSource = scope_source or MockScopeSource()
        self._emitter = emitter or default_emitter()

    @property
    def graphiti(self) -> Graphiti:
        return self._graphiti

    @property
    def scopes(self) -> ScopeSource:
        return self._scopes

    # -------- ingest --------

    async def ingest(
        self,
        body: str,
        *,
        name: str,
        source: str = "text",
        source_description: str = "memory ingest",
        reference_time: datetime | None = None,
        scope_id: str | None = None,
        retention_class: str | retention.RetentionClass | None = None,
    ) -> IngestResult:
        """Ingest an episode through the full D5–D10 pipeline.

        Returns an IngestResult including the ephemerality and retention
        decisions. Every call emits an OTel span to the observability
        sink (D7).
        """
        # D5 — ephemerality gate.
        verdict = ephemerality.classify(
            source=source,
            source_description=source_description,
            body=body,
        )

        # D6 — scope attribution (auto-registered if mock permits).
        scope_rec: ScopeRecord
        if isinstance(self._scopes, MockScopeSource):
            scope_rec = self._scopes.ensure(scope_id)
        else:
            got = self._scopes.get_scope(scope_id or "")
            if got is None:
                raise KeyError(
                    f"scope_id {scope_id!r} is not registered in the "
                    "scope-of-work primitive"
                )
            scope_rec = got

        # D10 — retention plan.
        plan = retention.resolve(retention_class)

        # Observability span wraps everything below.
        with self._emitter.span(
            "memory.ingest",
            attributes={
                "name": name,
                "source": source,
                "scope_id": scope_rec.scope_id,
                "retention_class": plan.cls.value,
                "ephemerality.rule": verdict.rule_name,
                "ephemerality.is_ephemeral": verdict.is_ephemeral,
                "body_chars": len(body),
            },
        ) as span:
            if verdict.is_ephemeral:
                record_audit(
                    operation="memory.ingest.discarded",
                    actor="memory-system",
                    scope_id=scope_rec.scope_id,
                    subject_uuid=None,
                    rationale=verdict.reason,
                    extras={"ephemerality_rule": verdict.rule_name, "name": name},
                    emitter=self._emitter,
                )
                span.set_attr("outcome", "discarded")
                return IngestResult(
                    episode_uuid=None,
                    ephemeral=True,
                    ephemeral_rule=verdict.rule_name,
                    retention_class=plan.cls.value,
                    scope_id=scope_rec.scope_id,
                )

            if plan.cls is retention.RetentionClass.EPHEMERAL:
                # Extract facts in-turn, do NOT persist.
                # We fabricate a minimal non-persisted result: graphiti's
                # add_episode is the persistence path. For ephemeral we
                # skip it entirely and return immediately; the caller
                # already has the body for in-turn use.
                record_audit(
                    operation="memory.ingest.ephemeral_retention",
                    actor="memory-system",
                    scope_id=scope_rec.scope_id,
                    subject_uuid=None,
                    rationale="retention_class=ephemeral; not persisted",
                    extras={"name": name},
                    emitter=self._emitter,
                )
                span.set_attr("outcome", "ephemeral_retention")
                return IngestResult(
                    episode_uuid=None,
                    ephemeral=False,  # NOT the D5 path; this is a retention choice
                    ephemeral_rule=None,
                    retention_class=plan.cls.value,
                    scope_id=scope_rec.scope_id,
                )

            # Normal or derived-only path — real Graphiti ingest.
            ref_time = reference_time or datetime.now(timezone.utc)
            if ref_time.tzinfo is None:
                ref_time = ref_time.replace(tzinfo=timezone.utc)
            ep_type = _EPISODE_TYPES.get(source, EpisodeType.text)
            # Amendment #11 audit-closure §F3: snapshot the subscription
            # cost before the ingest so we can emit the per-ingest delta
            # as a span attribute. The ClaudePrintLLMClient accumulates
            # ``total_cost_usd`` from each ``claude -p`` JSON envelope
            # into ``cost_tracker.total_usd``; Max-subscription calls
            # typically report 0.0 but Anthropic still reports an
            # equivalent-cost estimate useful for subscription-usage
            # budgeting. The llm_client may not be a
            # ClaudePrintLLMClient in every test context, so we probe
            # for the attribute defensively.
            cost_before = _subscription_cost_snapshot(self._graphiti.llm_client)
            result = await self._graphiti.add_episode(
                name=name,
                episode_body=body,
                source_description=source_description,
                reference_time=ref_time,
                source=ep_type,
                group_id=scope_rec.scope_id,
            )
            cost_after = _subscription_cost_snapshot(self._graphiti.llm_client)
            # D10 — apply retention plan (tag + optional content scrub).
            await retention.apply_plan(
                self._graphiti.driver,
                episode_uuid=result.episode.uuid,
                plan=plan,
            )

            # Observability: emit per-prompt token rows from graphiti's
            # tracker. We emit the DELTA relative to last snapshot so
            # one row per ingest is produced.
            self._record_delta_tokens(scope_id=scope_rec.scope_id, trace_id=span.trace_id, span_id=span.span_id)

            span.set_attr("outcome", "ingested")
            span.set_attr("episode_uuid", result.episode.uuid)
            span.set_attr("nodes_created", len(result.nodes))
            span.set_attr("edges_created", len(result.edges))
            if cost_before is not None and cost_after is not None:
                span.set_attr(
                    "claude.equivalent_cost_usd", cost_after - cost_before
                )

            return IngestResult(
                episode_uuid=result.episode.uuid,
                ephemeral=False,
                ephemeral_rule=None,
                retention_class=plan.cls.value,
                scope_id=scope_rec.scope_id,
                nodes_created=len(result.nodes),
                edges_created=len(result.edges),
            )

    def _record_delta_tokens(
        self,
        *,
        scope_id: str,
        trace_id: str,
        span_id: str,
    ) -> None:
        """Emit token rows for LLM calls that happened during this ingest.

        Graphiti's TokenUsageTracker is cumulative; we snapshot the
        per-prompt totals across calls and emit the DELTA since the
        previous snapshot. The snapshot lives on self (an attribute
        keyed by prompt name).
        """
        tracker = self._graphiti.llm_client.token_tracker
        current = tracker.get_usage() or {}
        last = getattr(self, "_last_token_snapshot", {})
        model = self._graphiti.llm_client.model
        delta: dict[str, tuple[int, int, int]] = {}
        for prompt_name, usage in current.items():
            prev = last.get(prompt_name, (0, 0, 0))
            d_in = usage.total_input_tokens - prev[0]
            d_out = usage.total_output_tokens - prev[1]
            d_calls = usage.call_count - prev[2]
            if d_in or d_out or d_calls:
                delta[prompt_name] = (d_in, d_out, d_calls)
            last[prompt_name] = (
                usage.total_input_tokens,
                usage.total_output_tokens,
                usage.call_count,
            )
        self._last_token_snapshot = last

        for prompt_name, (d_in, d_out, d_calls) in delta.items():
            record_llm_usage(
                prompt_name=prompt_name,
                model=model,
                input_tokens=d_in,
                output_tokens=d_out,
                call_count=d_calls,
                scope_id=scope_id,
                trace_id=trace_id,
                span_id=span_id,
                emitter=self._emitter,
            )

    # -------- search --------

    async def search(
        self,
        query: str,
        *,
        scope_ids: Sequence[str] | None = None,
        anchor_node_uuid: str | None = None,
        at_time: datetime | None = None,
        num_results: int = 10,
    ) -> list[SearchHit]:
        """Retrieve edges matching the query.

        Four retrieval modes supported via the same API surface:

          semantic      — omit anchor and at_time; default hybrid search.
          multi_hop     — default hybrid search with enough results to
                          traverse the graph (graphiti's search walks
                          edges internally).
          context_aware — pass anchor_node_uuid; results rerank by graph
                          distance.
          temporal      — pass at_time; the D8 wrapper translates that
                          into the Kuzu-compatible SearchFilter shape.
        """
        sf = temporal.active_at(at_time) if at_time is not None else None
        scope_list = list(scope_ids) if scope_ids else None

        with self._emitter.span(
            "memory.search",
            attributes={
                "query": query,
                "scope_ids": scope_list,
                "anchor_node_uuid": anchor_node_uuid,
                "at_time": at_time.isoformat() if at_time else None,
                "num_results": num_results,
                "temporal_wrapper": at_time is not None,
            },
        ) as span:
            edges = await self._graphiti.search(
                query=query,
                center_node_uuid=anchor_node_uuid,
                group_ids=scope_list,
                num_results=num_results,
                search_filter=sf,
            )
            hits = [
                SearchHit(
                    fact=edge.fact,
                    edge_uuid=edge.uuid,
                    source_node_uuid=edge.source_node_uuid,
                    target_node_uuid=edge.target_node_uuid,
                    valid_at=edge.valid_at,
                    invalid_at=edge.invalid_at,
                )
                for edge in edges
            ]
            span.set_attr("results_count", len(hits))
            return hits

    # -------- enumerate --------

    async def list_scope(self, scope_id: str) -> list[EpisodeRef]:
        """Enumerate episodes attributed to a scope."""
        cql = (
            "MATCH (ep:Episodic) WHERE ep.group_id = $scope_id "
            "RETURN ep.uuid AS uuid, ep.name AS name, "
            "ep.created_at AS created_at, ep.retention_class AS retention_class"
        )
        rows, _, _ = await self._graphiti.driver.execute_query(
            cql, scope_id=scope_id
        )
        return [
            EpisodeRef(
                uuid=r["uuid"],
                name=r["name"],
                created_at=r["created_at"],
                retention_class=r.get("retention_class"),
            )
            for r in (rows or [])
        ]

    async def list_by_retention(self, cls: str) -> list[EpisodeRef]:
        rows = await retention.list_by_class(self._graphiti.driver, retention.RetentionClass(cls))
        return [
            EpisodeRef(
                uuid=r["uuid"],
                name=r["name"],
                created_at=r["created_at"],
                retention_class=cls,
            )
            for r in rows
        ]

    async def retention_class_of(self, episode_uuid: str) -> str | None:
        return await retention.query_retention_class(
            self._graphiti.driver, episode_uuid
        )


_EPISODE_TYPES = {t.value: t for t in EpisodeType}
