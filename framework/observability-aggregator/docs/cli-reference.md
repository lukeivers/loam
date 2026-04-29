# `pos obs` CLI Reference

Thin wrapper over the structured Pydantic API. One subcommand per method, plus `pos obs why "..."` for the NL path.

## Global options

```
--db PATH                Override DB path (default ~/.loam/observability.db)
--substrate {duckdb,sqlite}
--raw                    Single-line JSON output
```

## Commands

### find-spans

```
pos obs find-spans [--component C] [--name N] [--status OK|ERROR|UNSET]
                   [--scope-id SID] [--since 7d|1h|ISO]
                   [--retention-class normal|derived-only|ephemeral]
                   [--limit N]
```

Examples:
```
pos obs find-spans --component scope_of_work --status ERROR --since 1h
pos obs find-spans --scope-id scope_42
pos obs find-spans --retention-class derived-only --limit 5
```

### get-trace

```
pos obs get-trace TRACE_ID
```

### get-span

```
pos obs get-span SPAN_ID
```

### cost-by-prompt

```
pos obs cost-by-prompt [--since 7d|1h|ISO] [--component C ...]
```

Aggregates tokens by `prompt_name` across all components. v1.1 R12 surface.

### audit-search

```
pos obs audit-search [--operation OP] [--actor ACTOR]
                     [--scope-id SID] [--since 7d|1h|ISO]
                     [--limit N]
```

### replay-session / replay-scope / replay-objective

```
pos obs replay-session SESSION_ID
pos obs replay-scope   SCOPE_ID
pos obs replay-objective OBJECTIVE_ID
```

Returns the structured replay shape (Reading A — read-only playback). Output cites span IDs throughout.

### why

```
pos obs why "QUESTION"
```

Invokes the NL path. Returns a `CitedAnswer` shape — summary, cited_span_ids, citations, rows_returned. The CLI does not chain to a Claude-via-Max call by default; it uses the rule-based translator + format-cited-answer locally. To chain Claude-via-Max, the workspace's bootstrap can register an `NLPath` with `llm_translate` / `llm_format` callables and the CLI inherits.

## Output format

All output is JSON. Pretty-printed by default (indent=2); `--raw` for single-line.

Pydantic models are dumped via `.model_dump(mode="json")`.

## Examples (representative)

```
$ pos obs find-spans --component memory_system --since 1h --limit 3
[
  {
    "trace_id": "...",
    "span_id": "...",
    "name": "memory.ingest",
    "component": "memory_system",
    ...
  },
  ...
]

$ pos obs cost-by-prompt --since 7d
{
  "extract_facts": {
    "prompt_name": "extract_facts",
    "input_tokens": 12450,
    "output_tokens": 5210,
    "call_count": 47,
    "estimated_usd": 0.0
  },
  "summarise_reading_list": { ... }
}

$ pos obs why "why did memory mark Alice's address as superseded?"
{
  "question": "...",
  "summary": "...",
  "cited_span_ids": [...],
  "citations": [...],
  "rows_returned": 1
}
```
