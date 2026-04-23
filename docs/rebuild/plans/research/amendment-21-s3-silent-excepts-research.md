# Amendment #21 — S3 Silent-Except Bundle — Research Document

**Amendment number:** 21
**BASELINE (pre-amendment tip):** `3b128c3` (pyyaml-reachability seal at
`9b4bcd3`, per the re-dispatch note in the amendment prompt).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-22.
**Companion plan:** `../amendment-21-s3-silent-excepts.md` (authored
after this research concludes).

## 1. Intent

The 2026-04-22 silent-exception audit + classifier surfaced six more
`except ...: pass | continue` branches tagged `AC:none` that the S1 + S2
bundles did not clear. A prior dispatch of this amendment halted
correctly on a former Site 3 (`telegram-interface/src/availability.py:
213`) inside `stop_background()` — a teardown method; shutdown-catch
CDC bucket (b) — so that site was dropped; the amendment prompt delivers
6 findings.

Per ODD §8 rule 8 and the audit-triage-by-severity CDC, each catch must
be replaced with an observable-surface fix unless (a) the exception is
already an exception-to-result conversion (observable surface IS the
return type); or (b) the catch is in a teardown method. Per the prompt,
sites 4 and 5 require special scrutiny as potential bucket-(a)
candidates.

Fix-shape follows the S1 precedent (amendment #19, commit `55c74af`) and
S2 precedent (amendment #20, commit `1c25a70`): each remaining catch
becomes an OTel emitter call + log event, or `span.add_event` on an
already-open span, or (for the memory-system JSONL-only observability
module) a `record_audit(...)` call. No method begins raising a new
exception class. No existing return shape changes.

## 2. Per-site catalogue (research re-verification)

### Site 1 — `scope-of-work/src/triggers.py:65` — `active_seconds_elapsed` silent parse error

**Enclosing function:** `active_seconds_elapsed`.
**Teardown status:** NOT teardown — live budget-evaluation helper. Called
by `remaining_for_axis` (time-axis budget remaining), which is read by
trigger-evaluation and the safety-layer's kill-engine budget checks.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception` (covers
`datetime.fromisoformat` → `ValueError`, `TypeError` on a non-string
timestamp, and the arithmetic’s `TypeError` on a mismatched tz).

**Full context (lines 55–67):**
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
        except Exception:
            pass
    return elapsed
```

**Callers:** `remaining_for_axis(...)` at `triggers.py:50` on the time
axis; that function is called by `is_stuck` / `evaluate_trigger` and by
the primitive's budget-exhaustion gate. `active_seconds_elapsed` is
also re-implemented inline in `runtime.py` (search confirms no other
direct callers). There is a nearly-identical pattern at `triggers.py:83`
inside `seconds_since_first_activation` — but that one returns `None`
on parse failure, which IS an exception-to-result conversion (bucket a)
and is not in the classifier's 6-finding list.

**Caller contract:** Returns `int`. On parse failure today the function
returns `proj.active_cumulative_seconds` without the current-span delta
— a stale value silently masquerading as correct. Callers cannot
distinguish a stale value from a fresh one.

**Bucket classification:** **(d) outright violation.** Not (a) because
the return type is `int` and there is no sentinel the caller can
distinguish. Not (b) because this is not a teardown method. The
exception is genuinely unexpected (a malformed ISO timestamp in the
projection’s stored `active_started_at` is a data-integrity bug); the
silent swallow hides it.

**Observability surface:** `scope-of-work/src/observability.py` exposes
`get_tracer()` + emitter helpers (start_invoke_scope_span,
emit_chat_span, fail_span, etc.); no existing emitter covers a
projection-parse failure.

**Fix (chosen):** Log + event-emit + default-return. Add a new emitter
function `emit_projection_parse_failure(scope_id, field, exception_class)`
to `scope-of-work/src/observability.py` that opens a short-lived span
`pos.scope.projection_parse_failed`. The call site in
`active_seconds_elapsed` emits the span inside the except; the
`return elapsed` at end-of-function remains unchanged (the stale
value is still returned — no public-contract change). Mirrors the
S1 per-site-emitter pattern.

**Justification:** The function is a read-side projection query, not a
fire-and-forget emitter with its own enclosing span — so
`span.add_event` on an already-open span (the observability pattern
used at Sites 4, 5, 8 of S2) is not available. A new short-lived span
is the minimum surface. Re-raise would propagate to `remaining_for_axis`
and break time-axis budget evaluation on any data-integrity bug (wrong
— budget eval should degrade, not crash).

**Existing test coverage:** `test_d2_budget_ledger.py` exercises the
time axis with well-formed timestamps; no test injects a malformed
`active_started_at`.
**New test:** +1 — `test_active_seconds_elapsed_surfaces_parse_failure`
in a new file `scope-of-work/tests/test_s3_silent_excepts.py`. Sets
`proj.active_started_at = "not-a-timestamp"`; asserts the emitter
span fires; asserts the function returns `proj.active_cumulative_seconds`
(existing behaviour preserved).

---

### Site 2 — `scope-of-work/src/projection.py:150` — `apply_event` silent parse error

**Enclosing function:** `apply_event(proj, event)`.
**Teardown status:** NOT teardown — core event-log projector; runs on
every event applied to the scope projection at runtime.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception` (`_as_dt` calls
`datetime.fromisoformat`; all failure modes are `ValueError` / `TypeError`
— a broad bare `Exception` is over-broad but functionally covers both).

**Full context (lines 142–152):**
```python
if isinstance(event, StateTransitioned):
    # Time accounting: when leaving active, accumulate seconds.
    if event.from_state == ScopeState.active and proj.active_started_at:
        try:
            started = _as_dt(proj.active_started_at)
            ended = _as_dt(event.created_at)
            delta = max(0, int((ended - started).total_seconds()))
            proj.active_cumulative_seconds += delta
        except Exception:
            pass
        proj.active_started_at = None
```

**Callers:** `project(scope_id, events)` at `projection.py:245` iterates
every event through `apply_event`. `apply_event` is also called
directly by `ScopeRuntime` on each new event (confirmed by a grep of
`runtime.py`).

**Caller contract:** Returns `None`; mutates `proj` in place.

**Bucket classification:** **(d) outright violation.** Not (a) — the
return is None, no surface communicates failure. Not (b) — this is a
live projection-replay path, not teardown. The `proj.active_started_at
= None` assignment AFTER the except body (outside the try) means the
projection continues advancing state even when the delta was lost — the
scope moves on with under-counted cumulative seconds and no diagnostic.

**Observability surface:** `scope-of-work/src/observability.py`'s new
`emit_projection_parse_failure` emitter (added for Site 1) is the
natural home for this site too.

**Fix (chosen):** Log + event-emit + default-return. Re-use the
`emit_projection_parse_failure` emitter introduced for Site 1. Call it
from inside this except body with
`field="StateTransitioned.active_started_at_or_created_at"` and the
exception class. The `proj.active_started_at = None` assignment remains
outside the try (existing behaviour preserved: projection still advances
past the bad event).

**Justification:** Identical reasoning to Site 1. A single shared
emitter covers both sites; each site names its own field. Re-raise
would propagate to `project()`, breaking the upgrade-fidelity
semantic round-trip (v1.1 R1) on any single bad-timestamp event —
wrong (project must degrade on bad historical streams, not crash).

**Existing test coverage:** `test_d7_upgrade_fidelity.py` exercises
projection round-trips with well-formed streams; no test injects a
malformed `created_at`.
**New test:** +1 — `test_apply_event_state_transitioned_surfaces_parse_failure`
in `test_s3_silent_excepts.py`. Builds a projection, applies a
`StateTransitioned` with `created_at = "not-a-ts"`; asserts emitter
fires; asserts `proj.active_started_at is None` after (existing
post-fallback behaviour preserved); asserts `proj.state ==
ScopeState.<new state>` (projection continues advancing).

---

### Site 3 — `telegram-interface/src/allowlist.py:150` — `identities()` loop-skip silent

**Enclosing function:** `AccessFile.identities()`.
**Teardown status:** NOT teardown — live identity-lookup read path.
Called by `AccessFile.lookup(user_id)` (auth-check on inbound message)
and `AccessFile.owner()` (owner identity resolution).
**Classifier label:** `except (KeyError, TypeError): continue`.
**Actual exception caught:** `KeyError` (missing `user_id` /
`display_name` / `authority_class` / `added_at` in a stored record) or
`TypeError` (record is not a mapping, e.g. `None` or a scalar).

**Full context (lines 137–151):**
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
        except (KeyError, TypeError):
            continue
    return out
```

**Callers:** `AccessFile.lookup`, `AccessFile.owner`, and indirect
callers downstream in `telegram-interface/src/adapter.py` for inbound
authority-class resolution.

**Caller contract:** Returns `dict[str, Identity]`. A skipped record
today is invisible — `lookup` returns `None` (treated as "not in
allowlist"), `owner` may mistakenly fall through to the `allowFrom[0]`
inference path.

**Bucket classification:** **(d) outright violation.** Not (a) — the
return type is `dict[str, Identity]`; callers cannot tell "record
corrupt" from "user unknown." Not (b) — live read path. An operator
sees a silent denial-of-service on a malformed record; authority
decisions are made against a partial dict.

**Observability surface:**
`telegram-interface/src/observability.py` has rich span emitters
(`inbound_rejected`, `allowlist_modified`, etc.). No existing emitter
covers the allowlist-record-parse-failure case.

**Fix (chosen):** Log + event-emit + default-return. Add new emitter
`allowlist_record_malformed(user_id, exception_class, missing_key)` in
`telegram-interface/src/observability.py` that opens span
`pos.telegram.allowlist_record_malformed`. Call from the except body;
`continue` remains (no recovery is possible for a record missing
required fields). Include `uid` in the attrs so an operator can
locate the bad record.

**Justification:** Re-raise would propagate to `lookup` / `owner`
callers and break the first inbound message after a record is
corrupted (wrong — the receive loop should stay live; the
malformation is a maintenance concern, not a hot-path failure).
Mirrors S2 Site 6's (`_any_paused_scope_user_relevant`) emit-and-
continue shape precisely.

**Existing test coverage:** `test_multi_identity.py` exercises
well-formed records; no test injects a malformed record.
**New test:** +1 — `test_identities_surfaces_malformed_record`
in a new file `telegram-interface/tests/test_s3_silent_excepts.py`.
Writes an access.json with one valid record and one missing
`authority_class`; asserts the emitter span fires with
`missing_key="authority_class"`; asserts the valid record IS in the
returned dict; asserts the malformed record ID is NOT.

---

### Site 4 — `hands-off-lifecycle/hooks/first_run_inventory.py:110` — `_parse_scalar` int fall-through

**Enclosing function:** `_parse_scalar(raw, line_no)`.
**Teardown status:** NOT teardown — parse helper used at workspace-
bootstrap scaffold time to read the first-run inventory YAML subset.

**Classifier label:** `except ValueError: pass`.
**Actual exception caught:** `ValueError` raised by `int(s)` when the
token is not a valid integer.

**Full context (lines 74–116):** The function docstring reads
`"""Parse a scalar value: null, bool, int, float, or string."""`.
The fall-through order is: null/true/false → quoted-string →
`int(s)` → `float(s)` → raw string. Sites 4 and 5 are the
int-ValueError and float-ValueError fall-throughs.

```python
# Try numerics.
try:
    if "." not in s and "e" not in s and "E" not in s:
        return int(s)
except ValueError:
    pass
try:
    return float(s)
except ValueError:
    pass
return s
```

**Bucket classification:** **(a) exception-to-result conversion.**

**Justification for reclassification:**
- The function's documented contract is a typed union return:
  `None | bool | int | float | str`.
- The `int(s)` call is an idiomatic Python duck-typed-parse probe.
  `ValueError` is the *designed* branch signal for "this token is not
  an integer; try the next parse rule."
- The observable surface IS the return value's type. A caller that
  receives `"3.14"` gets back `float(3.14)`; a caller that receives
  `"hello"` gets back `str("hello")`. The type discriminates which
  parse branch was taken.
- No downstream caller treats the fall-through as an error. The
  inventory validator (`validate_inventory`) type-checks final values,
  not how they were parsed.
- This is the textbook parse-dispatch pattern called out in the
  amendment prompt ("`int(x) → ValueError → fall through to float`").

**Outcome:** Drop from scope. No fix needed. No test added.

---

### Site 5 — `hands-off-lifecycle/hooks/first_run_inventory.py:114` — `_parse_scalar` float fall-through

**Enclosing function:** `_parse_scalar` (same function as Site 4).
**Teardown status:** NOT teardown.
**Classifier label:** `except ValueError: pass`.
**Actual exception caught:** `ValueError` raised by `float(s)` when the
token is not a valid float.

**Bucket classification:** **(a) exception-to-result conversion.**

**Justification:** Identical to Site 4. The `float(s)` → `ValueError`
→ `return s` chain is the same parse-dispatch pattern; the return
type (`str` vs `float`) IS the observable surface. Dropping.

**Outcome:** Drop from scope. No fix needed. No test added.

---

### Site 6 — `memory-system/src/observability.py:239` — `_read_jsonl` malformed-line skip

**Enclosing function:** `_read_jsonl(path)` (module-level helper).
**Teardown status:** NOT teardown — live query surface. Called by
`Emitter.read_spans`, `read_tokens`, `read_audit`, and transitively
`per_prompt_cost` (the R12 per-prompt-type cost-attribution query).

**Classifier label:** `except json.JSONDecodeError: continue`.
**Actual exception caught:** `json.JSONDecodeError`.

**Full context (lines 228–241):**
```python
def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows
```

**Callers:** `Emitter.read_spans`, `Emitter.read_tokens`,
`Emitter.read_audit` (source callers); scripts
`memory-system/scripts/eval_full_system.py` (cost-baseline runs) and
`memory-system/scripts/cost_baseline_full.py`; tests
`test_observability.py`, `test_D11_process_of_arrival.py`,
`test_claude_print_client.py`.

**Caller contract:** Returns `list[dict[str, Any]]`. A skipped line
today is invisible — the caller sees a shorter list with no
indication of truncation.

**Bucket classification:** **(d) outright violation.** Not (a) — the
return type is `list[dict]`; no sentinel differentiates "N records
present" from "N records present + M corrupt lines skipped." Not (b) —
live read path. A truncated list feeding `per_prompt_cost` silently
under-reports spend (R12 violation).

**Observability surface:** The `memory-system/src/observability.py`
module itself IS the observability surface; it does NOT depend on
the `opentelemetry` SDK (durable JSONL-sink pattern per docstring).
Emission goes through `record_audit(...)` at module level.

**Fix (chosen):** Log + audit-emit + default-return. On
`json.JSONDecodeError`, emit a `record_audit(...)` call with
`operation="observability.jsonl_line_malformed"`, `actor="memory-
system"`, `rationale=f"JSONDecodeError parsing line {line_no} of
{path.name}"`, `extras={"path": str(path), "line_no": line_no,
"exception_class": "JSONDecodeError"}`. The `continue` remains.

**Justification:** Within `memory-system`'s own observability module,
using its own `record_audit` is the right channel — the module
explicitly does NOT pull in the OTel SDK (docstring lines 20–30).
The audit sink is durable, operator-readable, and consumer-free per
the D7 contract. Re-raise would break every `read_spans` /
`read_tokens` / `per_prompt_cost` call on a single corrupt line —
wrong (robustness IS the designed behaviour; only the silence is
wrong).

**Caveat:** `_read_jsonl` is also called by the `Emitter`'s own
`read_audit` method. An audit-write during an audit-read risks
re-entry (the same file read mid-iteration). Mitigation: write to
the audit sink ONLY if `path != self._audit_file`. Simpler
alternative (chosen): `_read_jsonl` is a module-level helper that
doesn't know which sink it's reading. Pass `path` to `record_audit`
as a context field and rely on the `default_emitter()` singleton —
the audit write lands on the *audit* file, which may be the file
currently being read. But the file handle is already iterating over
cached buffered reads; a concurrent append (via the lock) to the
audit file will land AFTER the current read's EOF. The Emitter's
`_append` acquires its lock; the read here does not. The read's
buffered `for line in fh` iterator will NOT see the appended record
mid-iteration (file-iterator buffering + separate open). Safe.

Additional mitigation: detect and skip self-recursion by passing the
`path.name` through the extras only (no new emitter, no new span) —
the audit-write cost is one extra JSONL row per malformed line,
bounded by the size of the input. Accept.

**Existing test coverage:** `test_observability.py` has round-trip
tests with well-formed JSONL; no test injects a malformed line.
**New test:** +1 —
`test_read_jsonl_surfaces_malformed_line_in_audit`
in a new file `memory-system/tests/test_s3_silent_excepts.py`.
Writes a spans.jsonl with two valid records and one malformed line
(`{broken`). Calls `emitter.read_spans()`; asserts the returned
list has length 2. Calls `emitter.read_audit()`; asserts an audit
entry with `operation="observability.jsonl_line_malformed"` AND
`extras["line_no"]` pointing to the malformed line was recorded.

---

## 3. Cross-cutting notes

### 3.1 Finding-list after research

- Site 1 — `scope-of-work/src/triggers.py:65` — fix (bucket d).
- Site 2 — `scope-of-work/src/projection.py:150` — fix (bucket d).
- Site 3 — `telegram-interface/src/allowlist.py:150` — fix (bucket d).
- Site 4 — `first_run_inventory.py:110` — **drop (bucket a)**.
- Site 5 — `first_run_inventory.py:114` — **drop (bucket a)**.
- Site 6 — `memory-system/src/observability.py:239` — fix (bucket d).

**4 of 6 remain for fix.** Amendment is non-empty; proceed.

### 3.2 New observability surfaces

- `scope-of-work/src/observability.py`:
  - New emitter `emit_projection_parse_failure(scope_id, field,
    exception_class)` — covers Sites 1, 2.
- `telegram-interface/src/observability.py`:
  - New emitter `allowlist_record_malformed(user_id, exception_class,
    missing_key)` — covers Site 3.
- `memory-system/src/observability.py`:
  - No new emitter. Re-use existing `record_audit(...)` with
    `operation="observability.jsonl_line_malformed"` — covers Site 6.

All new emitters (scope-of-work, telegram-interface) use
`trace.get_tracer(...)` — no TracerProvider construction. No
`opentelemetry` SDK import in `memory-system/src/observability.py`
(unchanged — still JSONL-only).

### 3.3 Public API shape

- NO new record-field additions.
- NO method begins raising a new exception class.
- NO existing return-type shape changes. Sites 1, 2, 3, 6 all keep
  their current return contracts.

Halt trigger "A fix requires changing a public exception contract" is
CLEAR.

### 3.4 Scope: three amendment components + hands-off-lifecycle

- `scope-of-work/` — Sites 1, 2. **Unsealed** (11th component; no
  `SEAL_COMMIT` sidecar; no `test_no_sealed_amendments.py`). Needs
  admission to the H19 allowed set in
  `hands-off-lifecycle/tests/test_cross_cutting.py`.
- `telegram-interface/` — Site 3. Sealed. BASELINE advance in
  `telegram-interface/tests/test_no_sealed_amendments.py` from
  `b9e1f96` → `3b128c3`. SEAL_COMMIT sidecar refresh at seal time.
  `test_AC7_no_telegram_interface_src_edits`: the BASELINE advance
  re-pins the diff window so the AC7 invariant (src/ untouched from
  amendment-#9's sealing moment) continues to hold for its original
  scope; this amendment's src/ edits live AFTER the new BASELINE.
- `memory-system/` — Site 6. Sealed. BASELINE advance in
  `memory-system/tests/test_no_sealed_amendments.py` from `1b144f6`
  → `3b128c3`. SEAL_COMMIT sidecar refresh at seal time.
- `hands-off-lifecycle/` — BASELINE advance in
  `hands-off-lifecycle/tests/test_cross_cutting.py` from `24d54cb` →
  `3b128c3`; admit `scope-of-work` to H19 allowed set
  (`telegram-interface` and `memory-system` already present); add
  an amendment-cycle narrative stanza at the bottom of the BASELINE
  narrative comment; refresh `SEAL_COMMIT` sidecar at seal time;
  append to `seals/SEAL_COMMIT.true-first-run` narrative.

No 5th sealed component touched. Halt trigger cleared.

### 3.5 Allowed-prefix tuple check per speedup CDC

- `telegram-interface/tests/test_no_sealed_amendments.py` — current
  `allowed_prefixes = ("telegram-interface/", "data/",
  "docs/rebuild/components/telegram-interface/",
  "docs/rebuild/components/telegram-interface-framework-integration/",
  "docs/rebuild/plans/", "workspace-bootstrap/",
  "hands-off-lifecycle/")`. Amendment diff touches
  `scope-of-work/` (Sites 1, 2), `memory-system/` (Site 6), plus its
  own allowed prefixes. Needs `scope-of-work/` and `memory-system/`
  added to the tuple.
- `memory-system/tests/test_no_sealed_amendments.py` — current
  `allowed_prefixes = ("memory-system/", "hands-off-lifecycle/",
  "docs/rebuild/components/memory-system-subscription-routed-llm/",
  "docs/rebuild/components/memory-system-gliner2-expansion/",
  "docs/rebuild/plans/", "data/")`. Needs `scope-of-work/` and
  `telegram-interface/` admitted.
- Other 8 sealed components' seal-diff tests diff their own frozen
  BASELINE..SEAL ranges that predate this amendment — their diffs
  remain empty. No tuple changes needed.

### 3.6 BASELINE advance target

All BASELINE advances land at `3b128c3` — the current tip per the
amendment prompt.

## 4. Halt-trigger pre-check

- **Site-actually-in-teardown:** All 4 remaining sites verified live:
  `active_seconds_elapsed` (budget helper); `apply_event` (projector
  core); `identities()` (read path); `_read_jsonl` (read path). The
  former Site 3 in `availability.py:213` dropped per re-dispatch note.
- **Site-actually-bucket-(a):** Sites 4, 5 confirmed as parse-dispatch
  duck-typed numeric parse — dropped from scope. Other 4 sites
  verified as bucket-(d).
- **Amendment empty after re-classification:** 4 of 6 remain; proceed.
- **Fix requires changing a public exception-raising contract:**
  NONE — all fixes are emit-and-keep-existing-return. No method
  begins raising a new exception class.
- **Fix requires touching a 5th sealed component:** NO — three sealed
  components named (telegram-interface, memory-system, hands-off-
  lifecycle) plus one unsealed (scope-of-work). scope-of-work is NOT
  a sealed component — no SEAL_COMMIT sidecar, no BASELINE-diff test
  — so touching it doesn't consume a sealed-component slot. It DOES
  need H19 allowed-set admission (see §3.4).
- **Test break outside the 4 touched components:** Predicted: none;
  the other 7 sealed components' seal-diff BASELINEs are frozen at
  prior amendment windows and their allowed-prefix tuples already
  admit their amendment's own surfaces.

All halt triggers clear. Proceeding to plan.
