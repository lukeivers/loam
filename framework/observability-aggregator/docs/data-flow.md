# Data Flow — Representative Session

This document traces a representative pOS session end-to-end through the aggregator: what records get written, what citations the user sees when they ask "show me why."

## Setup

- Workspace bootstrap (`~/.pos/bootstrap.py`) calls `install_for_workspace(AggregatorConfig())` at orchestrator startup.
- The aggregator installs a global TracerProvider; `IngestionPipeline.start()` launches the spool drainer + three memory tailers as daemon threads.
- A user opens a Claude desktop session and asks the primary persona to summarise their reading list.

## What the components emit

1. **Primary persona** opens its monitor turn:
   - tracer `pos_v2.primary_persona`
   - span `pos.persona.monitor.tick` with `pos.session.id="sess_2026-04-19-12:30"`
   - on dispatch: span `pos.persona.dispatch.scope_invoke`

2. **Orchestrator** receives a bind_scope IPC call:
   - tracer `pos.orchestrator`
   - span `pos.orchestrator.bind_scope` with `pos.scope.id="scope_001"`, `pos.objective.id="obj_reading"`
   - state-changed event on the span when the scope flips active.

3. **Scope-of-work** runs the dispatched scope:
   - tracer `pos.scope_of_work`
   - parent span `invoke_scope` with `pos.scope.id="scope_001"`, `pos.scope.budget.tokens.remaining=10000`
   - state-changed events on each FSM transition
   - per LLM call, a child span `chat claude-sonnet` with `gen_ai.usage.input_tokens=400`, `gen_ai.usage.output_tokens=120`, `pos.prompt.type=summarise_reading_list`

4. **Memory-system** ingests one or two facts the scope produced:
   - JSONL row in `spans.jsonl`: `name="memory.ingest"`, `attributes.pos.retention.class="normal"`
   - JSONL row in `tokens.jsonl`: `prompt_name="extract_facts"`, `model="claude-haiku"`, `input_tokens=200`, `output_tokens=80`, `scope_id="scope_001"`
   - JSONL row in `audit.jsonl` if the ingest produced a supersession decision: `operation="supersession_inferred"`, `actor="memory_system"`, `rationale="newer entry contradicts..."`

5. **Objective-tracker** records the bind:
   - tracer `pos.objective_tracker`
   - span `pos.objective.bind_scope` with `pos.scope.id="scope_001"`, `pos.objective.id="obj_reading"`

## What the aggregator writes

Within ~1-2 seconds (the BatchSpanProcessor's `schedule_delay_millis=2000` plus the spool drainer's `poll_interval_seconds=1.0`), the spool drains and the store has:

- 5+ rows in `spans` covering the persona turn, the orchestrator bind, the scope invoke, the LLM call, the memory ingest, and the objective bind.
- Per-span events in `span_events` for state transitions and similar.
- 1-2 rows in `tokens` (one for the scope's `chat claude-sonnet`, one for memory's extract).
- 0-1 rows in `audit` if memory produced a supersession decision.

Each `spans` row's `attributes` JSON column is shaped by the source span's retention class. For this session, all spans are `normal` so payloads are preserved.

## What "show me why" returns

User asks: *"Why did memory mark Alice's address as superseded?"*

- The primary persona calls `nl.answer(question)`.
- `NLPath.translate(question)` emits `pos.aggregator.nl_translate` (tagged `pos.prompt.type=obs-nl-translate`); returns `NLTranslation(mode="audit", audit_actor="memory_system", audit_operation="supersession_inferred")`.
- `QueryAPI.audit_search(operation="supersession_inferred", actor="memory_system")` returns the matching audit rows.
- `NLPath` emits `pos.aggregator.nl_format` (tagged `pos.prompt.type=obs-nl-format`); returns `CitedAnswer(summary="...", citations=[...], cited_span_ids=[])`.
- The persona renders the cited answer in its voice; the citations carry through.

Both NL spans are filtered at exporter (their tracer is `pos.aggregator.nl`); they are visible in the spool log for diagnosis but not stored. They are tagged with their `pos.prompt.type` so the aggregator's own LLM cost shows up in the same `cost_by_prompt` view it serves — reflexive R12 attribution.

## What's in the store after one day at typical volume

- ~500 spans
- ~1500 events
- ~50 token rows
- ~20 audit entries

Storage footprint: ~1-2 MB raw, well within DuckDB's columnar compression efficiency. The retention job runs once daily, leaving the day's data raw under the 7-day full-fidelity tier.

## What ingestion looks like during aggregator downtime

- Six OTel components: their spans accumulate in `~/.pos/spool.jsonl`. No data is lost; the BatchSpanProcessor still flushes to the exporter, which still writes to disk.
- Memory-system: writes to its JSONL files independently. The aggregator's tailers will pick up the accumulated lines on next start.
- On aggregator restart, the spool drainer reads from its persisted byte-offset cursor and drains everything new; the JSONL tailers do the same.

## What the user can drill into

Every cited span ID is a query handle. The user can run `pos obs get-span <span_id>` for the raw row, `pos obs get-trace <trace_id>` for the full tree, or compose further NL queries that reference specific spans by ID. Anti-deskilling principle: the citations are a learning surface, not just a footnote.
