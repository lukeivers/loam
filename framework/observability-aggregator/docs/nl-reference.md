# NL Path Reference — "show me why"

Two-LLM-call pattern: translate the user's question into a structured filter, execute the filter against the structured API, format the rows into a cited natural-language answer.

## Use

```python
from pos_observability_aggregator.api import QueryAPI
from pos_observability_aggregator.nl_path import NLPath

api = QueryAPI(store)
nl = NLPath(api)

answer = nl.answer("Why did memory mark Alice's address as superseded?")
print(answer.summary)
print("Cited:", answer.cited_span_ids)
for c in answer.citations:
    print(" -", c)
```

## Two LLM calls

### Call 1 — translate

Input: the natural-language question + (in production) a schema description.
Output: an `NLTranslation` Pydantic model — exactly one of `mode in {spans, events, cost, audit, replay_session, replay_scope, replay_objective}`.

The translate call is emitted as `loam.aggregator.nl_translate` with `loam.prompt.type=obs-nl-translate` so it appears in `cost_by_prompt` — reflexive R12.

### Call 2 — format

Input: the question and the executed result rows.
Output: a `CitedAnswer` Pydantic model with `summary`, `cited_span_ids`, `citations` (one per row), `rows_returned`.

The format call is emitted as `loam.aggregator.nl_format` with `loam.prompt.type=obs-nl-format`.

## Wiring to Claude-via-Max

```python
def my_translate(question: str) -> NLTranslation:
    # Call Claude via Max with the question + schema; parse JSON.
    # Return NLTranslation(...).
    ...

def my_format(question: str, rows: list) -> CitedAnswer:
    # Call Claude via Max with the question + rows; parse cited prose.
    # Return CitedAnswer(...).
    ...

nl = NLPath(api, llm_translate=my_translate, llm_format=my_format)
```

If `llm_translate` raises or returns a non-`NLTranslation`, NLPath falls back to the rule-based translator deterministically. Same for `llm_format`.

## Default — rule-based translator

`rule_based_translate(question)` is the deterministic default. It handles:
- Cost intent — words like "cost", "spend", "tokens", "expensive", "money".
- Audit intent — words like "supersede", "supersession", "retention class", "audit", "decision".
- Replay intent — phrases like "replay session", "replay scope", "replay objective".
- Span query intent — default; uses `name_pattern` heuristics for verbs (ingest, rollup, bind, narrate).
- Component synonyms — "scope", "persona", "objective", "orchestrator", "memory", "dormancy", "graceful degradation", "outage".
- Time windows — "last 7 days", "in the past hour", "today", "yesterday", "the last week".
- Scope/objective/session/trace IDs by pattern matching.

## Accuracy

The rule-based translator is evaluated against `nl_corpus.CORPUS` — 25 representative questions with ground-truth filter outputs. Acceptance: ≥80% accuracy. Current measured: 100%.

To run the evaluation:

```python
from pos_observability_aggregator.nl_corpus import evaluate_corpus
from pos_observability_aggregator.nl_path import rule_based_translate

result = evaluate_corpus(rule_based_translate)
print(f"accuracy: {result['accuracy']:.0%} ({result['correct']}/{result['total']})")
```

## Format guarantees

- Every NL answer with rows includes `cited_span_ids`.
- Every citation row includes a `span_id` field.
- An NL answer with zero rows returns an empty `cited_span_ids` and a "no records matched" summary — never an uncited fabrication.
- Anti-deskilling principle (v1.0) — citations always carry through, never just narrative.

## No infinite-loop guarantee

The aggregator's NL spans (`loam.aggregator.nl_translate`, `loam.aggregator.nl_format`) are filtered at the spool exporter and at the spool drainer using the configured `self_namespace_prefix` (default `loam.aggregator`). Without this filter, every NL query would emit two spans which would be ingested which would generate two more spans on the next NL query — quickly degenerating into an unbounded log. The filter is verified by `test_self_observation_no_infinite_loop`.
