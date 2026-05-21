# Amendment #21 — S3 silent-except bundle

**Amendment number:** 21
**BASELINE (pre-amendment tip):** `3b128c3`.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-22.
**Research doc:** `research/amendment-21-s3-silent-excepts-research.md`.
**Pre-dispatch skills:** research-before-plan CDC, audit-triage-by-
severity CDC, amendment-dispatch speedup CDC, scope-only-dispatch CDC,
plan-before-code CDC.

## 1. Intent

Fix the four remaining `except ...: pass | continue` sites surfaced by
the 2026-04-22 audit + classifier with `AC:none`, after re-verification
dropped Sites 4 and 5 (`first_run_inventory.py:_parse_scalar`) as
bucket-(a) duck-typed numeric parse-dispatch (the exception IS the
branch signal; the return type IS the observable surface) and dropped
the former Site 3 (`telegram-interface/src/availability.py:213` in
`stop_background()`) as bucket-(b) teardown-catch.

Four fixes remain:

- Site 1 — `scope-of-work/src/triggers.py:65` — `active_seconds_elapsed`.
- Site 2 — `scope-of-work/src/projection.py:150` — `apply_event`.
- Site 3 — `telegram-interface/src/allowlist.py:150` — `identities()`.
- Site 6 — `memory-system/src/observability.py:239` — `_read_jsonl`.

Each fix replaces the silent catch with an observable surface (new
OTel span emitter, re-used for two sites in scope-of-work; new OTel
span emitter in telegram-interface; re-use of the existing
`record_audit` channel in memory-system's JSONL-only observability
module). No method begins raising a new exception class. No existing
return-type shape changes.

## 2. Files edited per site

| Site | File | Fix |
|------|------|-----|
| 1 | `scope-of-work/src/triggers.py:65` | new `emit_projection_parse_failure(scope_id, field, exception_class)` in scope-of-work/src/observability.py; call from except body; preserve `return elapsed` |
| 2 | `scope-of-work/src/projection.py:150` | re-use `emit_projection_parse_failure`; call from except body; preserve `proj.active_started_at = None` post-except |
| 3 | `telegram-interface/src/allowlist.py:150` | new `allowlist_record_malformed(user_id, exception_class, missing_key)` in telegram-interface/src/observability.py; call from except body; keep `continue` |
| 6 | `memory-system/src/observability.py:239` | call `record_audit(operation="observability.jsonl_line_malformed", ...)` from except body; keep `continue` |

## 3. Source-code changes

### 3.1 `scope-of-work/src/observability.py`

Add a new emitter at module level (after the existing emitters, near
the end of the file before the `span_ids` helper block):

```python
def emit_projection_parse_failure(
    *,
    scope_id: str,
    field: str,
    exception_class: str,
) -> None:
    """Fire-and-forget span for a projection-parse failure.

    Covers both `active_seconds_elapsed`'s ISO-timestamp parse
    (triggers.py:65) and `apply_event`'s StateTransitioned time-
    accounting parse (projection.py:150). `field` distinguishes the
    two call sites so an operator can filter by site.
    """
    tracer = get_tracer()
    if tracer is None:
        return
    span = tracer.start_span(
        "pos.scope.projection_parse_failed",
        kind=SpanKind.INTERNAL,
        attributes={
            "pos.scope.id": scope_id,
            "pos.scope.projection_field": field,
            "exception.class": exception_class,
        },
    )
    span.set_status(Status(StatusCode.ERROR, "projection parse failed"))
    span.end()
```

### 3.2 `scope-of-work/src/triggers.py` (Site 1)

Replace the current body:

```python
def active_seconds_elapsed(
    proj: ScopeProjectionData, *, now: datetime | None = None
) -> int:
    """Cumulative active-seconds including the current active span."""
    elapsed = proj.active_cumulative_seconds
    if proj.state == ScopeState.active and proj.active_started_at:
        try:
            started = datetime.fromisoformat(proj.active_started_at)
            current = now or datetime.now(tz=started.tzinfo)
            elapsed += max(0, int((current - started).total_seconds()))
        except Exception as exc:
            from .observability import emit_projection_parse_failure
            emit_projection_parse_failure(
                scope_id=proj.scope_id,
                field="active_started_at",
                exception_class=type(exc).__name__,
            )
    return elapsed
```

The `return elapsed` stays; callers see the same `int` they would
have seen under the silent-pass behaviour. Observable surface is the
new span.

### 3.3 `scope-of-work/src/projection.py` (Site 2)

Replace the current body of the `StateTransitioned` time-accounting
block:

```python
if isinstance(event, StateTransitioned):
    # Time accounting: when leaving active, accumulate seconds.
    if event.from_state == ScopeState.active and proj.active_started_at:
        try:
            started = _as_dt(proj.active_started_at)
            ended = _as_dt(event.created_at)
            delta = max(0, int((ended - started).total_seconds()))
            proj.active_cumulative_seconds += delta
        except Exception as exc:
            from .observability import emit_projection_parse_failure
            emit_projection_parse_failure(
                scope_id=proj.scope_id,
                field="StateTransitioned.active_started_at_or_created_at",
                exception_class=type(exc).__name__,
            )
        proj.active_started_at = None
    # ... (rest of StateTransitioned branch unchanged)
```

The `proj.active_started_at = None` stays outside the try (existing
post-fallback behaviour preserved). Projection continues advancing.

### 3.4 `telegram-interface/src/observability.py`

Add a new emitter at module level (after the existing `allowlist_modified`
emitter, which it sits adjacent to thematically):

```python
def allowlist_record_malformed(
    *, user_id: str, exception_class: str, missing_key: str | None
) -> None:
    with _TRACER.start_as_current_span(
        "pos.telegram.allowlist_record_malformed"
    ) as span:
        _set(
            span,
            {
                "pos.telegram.user_id": user_id,
                "exception.class": exception_class,
                "pos.telegram.malformed_key": missing_key or "<unknown>",
            },
        )
```

### 3.5 `telegram-interface/src/allowlist.py` (Site 3)

Replace the `identities()` loop body:

```python
def identities(self) -> dict[str, Identity]:
    out: dict[str, Identity] = {}
    for uid, rec in (self.data.get("pos_identities") or {}).items():
        try:
            out[str(uid)] = Identity(
                user_id=str(rec["user_id"]),
                display_name=rec["display_name"],
                relationship=rec.get("relationship", "unknown"),
                authority_class=rec["authority_class"],
                added_at=rec["added_at"],
                blocked_at=rec.get("blocked_at"),
            )
        except (KeyError, TypeError) as exc:
            missing_key = exc.args[0] if isinstance(exc, KeyError) and exc.args else None
            obs.allowlist_record_malformed(
                user_id=str(uid),
                exception_class=type(exc).__name__,
                missing_key=str(missing_key) if missing_key is not None else None,
            )
            continue
    return out
```

The `continue` stays (no recovery is possible for a record missing
required fields). `lookup` and `owner` return shapes are unchanged.

### 3.6 `memory-system/src/observability.py` (Site 6)

Replace the `_read_jsonl` body:

```python
def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("rt", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                record_audit(
                    operation="observability.jsonl_line_malformed",
                    actor="memory-system",
                    rationale=(
                        f"JSONDecodeError parsing line {line_no} of "
                        f"{path.name}"
                    ),
                    extras={
                        "path": str(path),
                        "line_no": line_no,
                        "exception_class": type(exc).__name__,
                        "message": str(exc),
                    },
                )
                continue
    return rows
```

`record_audit` is the module's existing durable emission channel
(no OTel SDK dep — matches the module docstring's JSONL-sink
contract). The audit entry may be written to `audit.jsonl` even while
we are reading a different sink; concurrency is protected by
`Emitter._lock` on the write side, and the read-side `for line in fh`
iterator works against a buffered read that will not observe the
post-read append.

## 4. Test plan

### 4.1 New tests (one per remaining site)

- `scope-of-work/tests/test_s3_silent_excepts.py` (new file):
  - `test_active_seconds_elapsed_surfaces_parse_failure` — injects
    `proj.active_started_at = "not-a-ts"`; asserts a span named
    `pos.scope.projection_parse_failed` with
    `pos.scope.projection_field = "active_started_at"` appears;
    asserts the function returns `proj.active_cumulative_seconds`.
  - `test_apply_event_state_transitioned_surfaces_parse_failure` —
    applies a `StateTransitioned(from_state=active, to_state=done,
    created_at="not-a-ts")` to a projection whose `active_started_at`
    is set; asserts a span with
    `pos.scope.projection_field = "StateTransitioned.active_started_at_or_created_at"`
    appears; asserts `proj.active_started_at is None` after;
    asserts `proj.state == ScopeState.done`.
- `telegram-interface/tests/test_s3_silent_excepts.py` (new file):
  - `test_identities_surfaces_malformed_record` — writes an
    `access.json` with one valid `pos_identities` record and one
    missing `authority_class`; calls `AccessFile.load(...)
    .identities()`; asserts the emitter span
    `pos.telegram.allowlist_record_malformed` with
    `pos.telegram.malformed_key = "authority_class"` fired;
    asserts the valid record's id IS in the returned dict; asserts
    the malformed record's id is NOT.
- `memory-system/tests/test_s3_silent_excepts.py` (new file):
  - `test_read_jsonl_surfaces_malformed_line_in_audit` — constructs
    an `Emitter` with `sink_dir=tmp_path`; writes a `spans.jsonl`
    with two valid records and one malformed line (e.g. `{broken`);
    calls `emitter.read_spans()`; asserts `len(...) == 2`; calls
    `emitter.read_audit()`; asserts an entry with
    `operation="observability.jsonl_line_malformed"` and
    `extras["line_no"]` pointing to the malformed line appears.

Scope-of-work does not have a `test_no_sealed_amendments.py`
allowed-prefixes tuple; it IS an unsealed surface. Its edits flow
through the hands-off-lifecycle H19 allowed-set admission.

### 4.2 Pre-amendment scoped runs (per speedup CDC)

- Full suite: `scope-of-work`, `telegram-interface`, `memory-system`,
  `hands-off-lifecycle` (the components with source or test edits in
  this amendment).
- Seal-diff-tests-only for the remaining 7 sealed components:
  `cost-governance`, `graceful-degradation`, `observability-aggregator`,
  `orchestrator`, `reversibility-primitive`, `self-correction`,
  `workspace-bootstrap`. Each runs its
  `test_no_sealed_amendments.py`; all must pass (their BASELINEs
  predate this amendment window).

### 4.3 Post-seal scoped runs

- Seal-diff-tests-only across all 10 sealed components. All diffs
  empty.

### 4.4 Environment note

`safety-layer/tests/test_no_sealed_amendments.py` may show
`ModuleNotFoundError: primary_persona` — pre-existing, not this
amendment's bug.

## 5. Test + BASELINE updates

### 5.1 `telegram-interface/tests/test_no_sealed_amendments.py`

- Advance `BASELINE = "b9e1f96"` → `"3b128c3"`.
- Extend `allowed_prefixes` tuple with `"scope-of-work/"`,
  `"memory-system/"`.
- Extend the BASELINE-history narrative comment with an amendment-#21
  stanza.

### 5.2 `memory-system/tests/test_no_sealed_amendments.py`

- Advance `BASELINE = "1b144f6"` → `"3b128c3"`.
- Extend `allowed_prefixes` tuple with `"scope-of-work/"`,
  `"telegram-interface/"`.
- Extend the BASELINE-history narrative comment with an amendment-#21
  stanza.

### 5.3 `hands-off-lifecycle/tests/test_cross_cutting.py`

- Advance `BASELINE = "24d54cb"` → `"3b128c3"`.
- Admit `"scope-of-work"` to the `allowed` set in
  `test_H19_diff_scope_covers_only_approved_surfaces`.
- Extend the BASELINE-history narrative comment with an amendment-#21
  stanza.

## 6. Two-commit cycle

1. **Amendment commit:** `fix(scope-of-work, telegram-interface,
   memory-system, hands-off-lifecycle): S3 silent-except bundle —
   surface 4 AC:none violations (amendment #21)`.
   Lands all code + new tests + BASELINE/allowed-prefix advances + the
   research doc + this plan doc.
2. **Seal commit:** `chore(seals): s3-silent-excepts seal —
   telegram-interface + memory-system + hands-off-lifecycle at
   <amendment-sha>`. Writes the amendment SHA into the three sealed
   components' `tests/SEAL_COMMIT` sidecars and appends a narrative
   entry to `seals/SEAL_COMMIT.true-first-run`.

scope-of-work has no SEAL_COMMIT sidecar (unsealed component) so does
not participate in the seal commit.

## 7. Halt triggers re-verified

- Teardown-status re-verified per-site (§2 of research doc). All 4
  remaining sites are live.
- Bucket-(a) re-verification: Sites 4, 5 confirmed as duck-typed parse-
  dispatch; dropped from scope.
- Zero 5th sealed component.
- Zero public-exception-contract changes.
- Zero out-of-scope sealed-surface diffs.

All clear; proceed to code.
