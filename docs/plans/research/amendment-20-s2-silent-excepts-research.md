# Amendment #20 — S2 Silent-Except Bundle — Research Document

**Amendment number:** 20
**BASELINE (pre-amendment tip):** `24d54cb` (`docs(future-ideas): capture
amendment-dispatch-speedups and 529-recovery CDCs`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-22.
**Companion plan:** `../amendment-20-s2-silent-excepts.md` (authored after this
research concludes).

## 1. Intent

Ten `except Exception: pass` / `continue` / `except ValueError: pass` /
`except asyncio.TimeoutError: continue` branches surfaced by the 2026-04-22
silent-exception audit + classifier across `self-correction/` (5),
`graceful-degradation/` (3), and `observability-aggregator/` (2), each
tagged `AC:none`. Per ODD §8 rule 8, the audit-triage-by-severity CDC
(`e8f704c`, bucket d — outright violations in live operational paths), and
the amendment-dispatch speedup CDC (`24d54cb`, inline-snippet dispatches),
each catch must be replaced with an observable-surface fix unless a named
AC tolerates the silence. None do. None of the 10 are in
`close()`/`stop()`/`cancel()`/`shutdown()`/`__aexit__`/teardown methods —
the shutdown-catch exception CDC does NOT apply.

Fix-shape follows the S1 precedent (amendment #19, commit `55c74af`):
each `except Foo: pass|continue` becomes an OTel emitter call + (where
the caller consumes a structured error) an additive backwards-compatible
record field. No site's public exception-raising contract changes.

## 2. Per-site catalogue

### Site 1 — `self-correction/src/triggers.py:94` — `build_trigger_from_span` attribute-lookup

**Function:** `build_trigger_from_span(*, span)`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 88–103):**
```python
def build_trigger_from_span(*, span: Any) -> CorrectionTrigger:
    scope_id = None
    try:
        scope_id = span.attributes.get("pos.scope.id")
    except Exception:
        pass
    name = getattr(span, "name", "") or ""
    ...
```

**Callers:** `OTelAnomalyPoller.run_once` at `triggers.py:267` (the only
production call site); tests call `build_trigger_from_span` directly.

**Caller contract:** Returns a `CorrectionTrigger` with `scope_id`,
`trace_id`, `failure_class_hint`, `raw_payload`, `dedup_key`. The `scope_id`
feeds the `dedup_key` so silent failure to extract it breaks dedup (two
real failures on the same scope would de-dupe as distinct triggers). This
is the finding's named consequence ("dedup breaks").

**Observability surface:** None directly on this path. `obs.trigger_received`
fires downstream on the handler but without a "scope-id extraction failed"
signal.

**Fix (chosen):** Log + event-emit + default-return. Add a new emitter
`obs.span_attribute_lookup_failed(trigger_source, attribute_name,
exception_class)` emitting span `pos.correction.span_attribute_lookup_failed`.
`scope_id` remains `None` (existing default). The function return shape is
unchanged.

**Justification:** The caller (the poller) cannot consume a typed error —
the function must return a trigger even when the lookup fails (the
downstream handler flow can still operate on other fields). Re-raise would
break the poll loop via the unwrapped `await self._handler(trigger)` call.
Span emission is the right channel for the dedup-degradation signal.

**Existing test coverage:** `test_detection_otel_anomaly.py` exercises the
happy path; no test injects a raising attribute lookup.
**New test:** +1 — `test_build_trigger_from_span_attribute_failure_emits_span`
injects a span whose `.attributes.get()` raises; asserts the emitter fires;
asserts `scope_id is None`.

---

### Site 2 — `self-correction/src/triggers.py:252` — `OTelAnomalyPoller.run_forever` loop tick

**Function:** `OTelAnomalyPoller.run_forever`.
**Classifier label:** `except Exception: continue`.
**Actual exception caught:** `asyncio.TimeoutError` (narrow, not bare).

**Full context (lines 244–252):**
```python
async def run_forever(self) -> None:
    while not self._stopped.is_set():
        await self.run_once()
        try:
            await asyncio.wait_for(
                self._stopped.wait(), timeout=self._interval
            )
        except asyncio.TimeoutError:
            continue
```

**Classifier's concern:** The `continue` after a narrow-typed
`TimeoutError` IS the intended control-flow mechanism (sleep-with-early-
wake pattern — `_stopped.wait()` returning => stop; timeout => iterate).
The except-body has no log/emit, so the classifier flagged it. Per the
audit-triage-by-severity CDC this is bucket (d) at strict ODD §8 rule 8
reading: the branch has no AC backing the timing-idiom use. The
minimum-disruption fix is to add an observable-surface signal on the
timeout path without changing semantics.

**Caller contract:** `run_forever` is called as a long-running background
task. Mutation of semantics (raising instead of continuing) would stop
the poller; wrong.

**Observability surface:** None inside `run_forever`. The per-tick
`run_once` fires its own spans downstream.

**Fix (chosen):** Log + event-emit + default-return. Add an emitter
`obs.poll_tick(poller_name, interval_seconds)` emitting span
`pos.correction.poll_tick` once per timeout-driven iteration (default
30s, configurable). The except-body keeps its `continue` (the intended
control flow) plus the emitter.

**Justification:** 30s/60s-cadence tick spans are within acceptable
cost-governance bounds (one span per minute per poller). An operator can
now see the poll liveness; silent continues are invisible. Re-raise
would stop the poller (wrong). Narrower-typing is already done
(`TimeoutError`, not `Exception`), so that lever is spent.

**Existing test coverage:** `test_detection_otel_anomaly.py` tests
`run_once`; `run_forever` is indirectly covered via the stop-event
mechanics but no assertion on the tick emitter.
**New test:** +1 — `test_poll_tick_emits_span_on_timeout_iteration`
builds a poller with a tiny interval, runs briefly, stops; asserts the
tick span fired at least once.

---

### Site 3 — `self-correction/src/completion_check.py:124` — audit_subscription no-loop fallback

**Function:** `CompletionPrecheck.audit_subscription._on_event`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** `RuntimeError` (narrow).

**Full context (lines 116–124):**
```python
if notify is not None:
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            notify(ep.episode_id, ",".join(missing_list))
        )
    except RuntimeError:
        pass
```

**Classifier's concern:** If `get_running_loop()` raises (no running loop),
the audit-layer notification is silently dropped. The audit layer is the
"belt-and-braces" check for a completion that bypassed `request_complete`;
a missed notification means an operator never learns the four-part
protocol was violated via a back-door.

**Caller contract:** Pyee event handler, return None. Exceptions that
escape would kill the emitter.

**Observability surface:** `obs.episode_refused(...)` already fires at
line 110 (before this block) with reason `audit:incomplete_records_bypass`.
So the violation IS visible on OTel; only the one-on-one notify channel
drop is silent.

**Fix (chosen):** Log + event-emit + default-return. Add an emitter
`obs.audit_notify_no_loop(episode_id)` emitting span
`pos.correction.audit_notify_no_loop` inside the except. The `pass`
remains (can't invoke the async notifier without a loop) but the
drop is observable. Additionally the comment explicitly names why the
drop is non-catastrophic: `episode_refused` span already fired.

**Justification:** Without a running loop there is no way to schedule
the async notification; the only correct action IS to drop. But silent
drop is wrong. The emitter makes the drop observable. Re-raise would
break the pyee `*` subscription for all future events (worse failure
mode).

**Existing test coverage:** None directly — no test invokes the audit
handler with no running loop.
**New test:** +1 — `test_audit_subscription_drops_notify_with_no_loop_observably`
calls the inner `_on_event` from a synchronous context (no loop); asserts
the no-loop emitter fires.

---

### Site 4 — `self-correction/src/observability.py:122` — `episode_refused` StatusCode fallback

**Function:** `episode_refused`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 117–122):**
```python
        try:
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, reason))
        except Exception:
            pass
```

**Classifier's concern:** OTel-API availability is a boot-time concern;
if `Status` import or `set_status` fails the span loses its ERROR marker.
Silent pass hides this.

**Caller contract:** `episode_refused` is a fire-and-forget emitter;
returns None.

**Observability surface:** The span itself is already open at line 108
(`pos.correction.episode_refused`). The fallback affects only its
`Status` attribute.

**Fix (chosen):** Log + event-emit + default-return. Record the import /
set-status failure as a span *event* (additive to the already-open span):
`span.add_event("status_set_failed", {"exception_class": type(e).__name__})`.
The except still terminates (the primary `episode_refused` span stays
open and its other attrs fire); the fallback failure is captured on the
same span that was the subject of the call.

**Justification:** A full new emitter for an OTel-internal boot-time
failure is overkill — one span event on the already-open span is the
minimum sufficient observable surface. Mirrors how
`graceful-degradation/src/observability.py:44` handles its own add-event
fallback (degraded attrs). Re-raise would break every `episode_refused`
call on a broken OTel import (worse).

**Existing test coverage:** None directly.
**New test:** +1 — `test_episode_refused_status_set_failure_is_captured`
monkey-patches `span.set_status` to raise; asserts a `status_set_failed`
event is added to the span.

---

### Site 5 — `self-correction/src/observability.py:165` — `cost_refusal_caught` StatusCode fallback

**Function:** `cost_refusal_caught`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 160–165):**
```python
        try:
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, message))
        except Exception:
            pass
```

**Classifier's concern / caller contract / observability surface:**
mirror of Site 4.

**Fix (chosen):** Same pattern as Site 4 — `span.add_event(
"status_set_failed", {"exception_class": type(e).__name__})`.

**Justification:** identical to Site 4.

**Existing test coverage:** None directly.
**New test:** +1 — `test_cost_refusal_caught_status_set_failure_is_captured`
analogous to Site 4's new test but on the cost-refusal span.

---

### Site 6 — `graceful-degradation/src/component.py:443` — `_any_paused_scope_user_relevant` silent skip

**Function:** `DegradationComponent._any_paused_scope_user_relevant`.
**Classifier label:** `except Exception: continue`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 438–447):**
```python
def _any_paused_scope_user_relevant(self, ep: ActiveEpisode) -> bool:
    for sid in ep.paused_scope_ids:
        scope = None
        try:
            scope = self.scope_runtime.get(sid)  # type: ignore[attr-defined]
        except Exception:
            continue
        if scope is not None and scope_has_user_relevant_escalation(scope):
            return True
    return False
```

**Classifier's concern:** A scope-lookup failure silently drops the
scope from the user-relevance check. The function returns `True` if
ANY paused scope is user-relevant; a silent drop could downgrade a
user-relevant episode to non-user-relevant, suppressing notifications.

**Callers:** `DegradationComponent._maybe_notify` at the notification
gate; the threshold-escalation path depends on the relevance bit.

**Caller contract:** Returns bool. No mechanism to signal
per-scope lookup failure.

**Observability surface:** The notification-threshold spans exist at
class level but no per-scope-lookup span.

**Fix (chosen):** Log + event-emit + default-return. Add emitter
`obs.scope_lookup_failed(episode_id, scope_id, exception_class)` in a
new helper that emits span
`pos.degradation.scope_lookup_failed`. The `continue` remains (we still
need to iterate remaining scopes), but the drop is observable.

**Justification:** Re-raise would propagate to the notification gate,
stalling escalation on a transient lookup failure (wrong). Typed-return
change would widen the function's shape (bool → Result<bool, ...>) —
more churn than necessary. Emit + continue is the minimum surface.

**Existing test coverage:** Relevance-check tests in `test_d5_notification.py`
use a scope-runtime fake whose `get()` never raises.
**New test:** +1 — `test_any_paused_scope_user_relevant_surfaces_lookup_failures`
injects a failing `get()` for one scope id, passes a user-relevant
scope for another; asserts the emitter fired for the failing id,
asserts the function returned True (user-relevant scope still seen).

---

### Site 7 — `graceful-degradation/src/component.py:513` — `reconcile_on_startup` ValueError fallback

**Function:** `DegradationComponent.reconcile_on_startup`.
**Classifier label:** `except ValueError: pass` (narrow — not bare).
**Actual exception caught:** `ValueError`.

**Full context (lines 495–515):**
```python
if plan.case == 1 and plan.active_episode_id is not None:
    ep_row = self.store.get_episode(plan.active_episode_id)
    if ep_row is not None:
        try:
            mode = DegradationMode(ep_row.mode)
            policy = Policy(ep_row.policy)
            self.active_episodes[mode] = ActiveEpisode(
                episode_id=ep_row.episode_id,
                mode=mode,
                ...
            )
        except ValueError:
            pass
return plan
```

**Classifier's concern:** A stored `mode`/`policy` string that no longer
maps to an enum value (schema drift across restarts) is silently dropped;
the episode stays unresolved in the store but the in-memory
`active_episodes` dict has no entry for it, so probe + resume logic will
never reach it. This is a data-integrity violation on startup.

**Callers:** `DegradationComponent.start` or equivalent — called once at
component boot.

**Caller contract:** Returns a `ReconciliationPlan`. The in-memory side
effect (populating `active_episodes`) is the gap the silent-except hides.

**Observability surface:** None directly; plan-level spans fire elsewhere.

**Fix (chosen):** Log + event-emit + default-return. Add emitter
`obs.reconcile_restore_failed(episode_id, mode_value, policy_value,
exception_class)` emitting span `pos.degradation.reconcile_restore_failed`.
The `pass` remains (we can't reconstruct the in-memory episode without a
valid enum), but the drop is now observable. An operator sees
"startup reconciled N episodes, 1 dropped-on-restore for invalid mode".

**Justification:** Re-raise on boot would prevent the component from
starting (wrong; one rogue row should not block the rest of
reconciliation). Typed-return would cascade changes up the startup path.
Emit + pass is the minimum surface.

**Existing test coverage:** `test_d7_resume.py` / `test_d8_state.py`
exercise reconcile with well-formed rows.
**New test:** +1 —
`test_reconcile_on_startup_surfaces_invalid_stored_enum_values` stores
an episode row with `mode="not-a-mode"`; asserts the emitter fires;
asserts `active_episodes` dict does NOT contain the row (existing
behaviour preserved).

---

### Site 8 — `graceful-degradation/src/observability.py:144` — `episode_started` paused-scope-ids attribute

**Function:** `episode_started`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 140–145):**
```python
        try:
            span.set_attribute(
                "pos.degradation.paused_scope_ids", ",".join(paused_scope_ids)
            )
        except Exception:
            pass
```

**Classifier's concern:** If `set_attribute` raises (e.g. string too
long for the OTel SDK limit), the comma-joined ids are dropped silently
— the span's other attrs land but the list of scopes is missing.

**Caller contract:** `episode_started` is a fire-and-forget emitter;
returns None.

**Observability surface:** The same span (`pos.degradation.episode_started`)
is already open.

**Fix (chosen):** Log + event-emit + default-return. Pattern mirrors
Sites 4/5: `span.add_event("paused_scope_ids_attr_failed", {
"exception_class": type(e).__name__, "count": len(paused_scope_ids)})`
on the already-open span. `paused_scope_count` already lands at line 139,
so the cardinality is not lost.

**Justification:** Minimum surface. An operator sees the count on the
main attrs and the drop-event on the same span. Re-raise would kill
every `episode_started` emission if the SDK ever raised on attr-set.

**Existing test coverage:** `test_d9_observability.py` exercises the
happy path.
**New test:** +1 —
`test_episode_started_surfaces_paused_scope_ids_attr_failure`
monkey-patches a span factory to raise on the ids attribute (but not
the count); asserts the drop-event is added to the span.

---

### Site 9 — `observability-aggregator/src/nl_path.py:387` — `translate()` LLM fall-through

**Function:** `NLPath.translate`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 378–389):**
```python
def translate(self, question: str) -> NLTranslation:
    with _TRACER.start_as_current_span("pos.aggregator.nl_translate") as span:
        span.set_attribute("pos.prompt.type", "obs-nl-translate")
        span.set_attribute("nl.question", question[:500])
        if self._llm_translate is not None:
            try:
                t = self._llm_translate(question)
                if isinstance(t, NLTranslation):
                    return t
            except Exception:
                pass
        return rule_based_translate(question)
```

**Classifier's concern:** If the LLM adapter raises, the fall-through to
`rule_based_translate` is silent — an operator cannot see that LLM
translation was attempted and failed. This masks LLM-adapter regressions.

**Caller contract:** Returns `NLTranslation`. The fall-through to rule-
based is the designed behaviour (LLM is optional; rule-based is the
always-available baseline).

**Observability surface:** The enclosing span
`pos.aggregator.nl_translate` is already open.

**Fix (chosen):** Log + event-emit + default-return. Add a span event
(on the already-open span) `llm_translate_failed` with attrs
`exception.class`, `fallback="rule_based"`. The fall-through to
`rule_based_translate` remains unchanged.

**Justification:** Minimum surface; no new span needed (one exists).
The event tags the fall-through so an operator can filter for LLM-
failure rate. Re-raise would force a nl-translate call to crash when
the LLM fails (wrong — rule-based exists precisely for resilience).

**Existing test coverage:** `test_d5_nl_path.py` exercises rule-based
directly and LLM happy path.
**New test:** +1 — `test_nl_translate_surfaces_llm_failure_on_fallback`
injects a raising `llm_translate`; asserts rule-based is used (existing
behaviour) AND the `llm_translate_failed` event appears on the span.

---

### Site 10 — `observability-aggregator/src/nl_path.py:426` — `answer()` LLM fall-through

**Function:** `NLPath.answer`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 416–428):**
```python
def answer(self, question: str) -> CitedAnswer:
    t, rows = self.execute(question)
    with _TRACER.start_as_current_span("pos.aggregator.nl_format") as span:
        span.set_attribute("pos.prompt.type", "obs-nl-format")
        span.set_attribute("nl.rows_returned", len(rows))
        if self._llm_format is not None:
            try:
                fmt = self._llm_format(question, rows)
                if isinstance(fmt, CitedAnswer):
                    return fmt
            except Exception:
                pass
        return format_cited_answer(question, rows)
```

**Classifier's concern / caller contract / observability surface / fix /
justification:** mirror of Site 9, with span event
`llm_format_failed` on `pos.aggregator.nl_format`.

**Existing test coverage:** `test_d5_nl_path.py` exercises the rule-based
fall-through.
**New test:** +1 — `test_nl_answer_surfaces_llm_failure_on_fallback`
mirror of Site 9's.

---

## 3. Cross-cutting notes

### 3.1 New observability surfaces

- `self-correction/src/observability.py`:
  - `span_attribute_lookup_failed(trigger_source, attribute_name,
    exception_class)` — covers Site 1.
  - `poll_tick(poller_name, interval_seconds)` — covers Site 2.
  - `audit_notify_no_loop(episode_id)` — covers Site 3.
  - (Sites 4, 5: in-place span event on the same span — no new emitter.)
- `graceful-degradation/src/observability.py`:
  - `scope_lookup_failed(episode_id, scope_id, exception_class)` — Site 6.
  - `reconcile_restore_failed(episode_id, mode_value, policy_value,
    exception_class)` — Site 7.
  - (Site 8: in-place span event on the same span — no new emitter.)
- `observability-aggregator/src/nl_path.py`: Sites 9, 10 — in-place
  span events on already-open spans. No new emitter module added.

All emitters use `trace.get_tracer(...)` — no TracerProvider construction.

### 3.2 Public API shape

- NO new record fields (Sites 1–3, 6, 7 emit on spans; the functions'
  return-types are unchanged).
- NO method begins raising a new exception class.
- NO existing return-type shape changes.

This clears the halt trigger "A fix requires changing a method's public
exception-raising contract."

### 3.3 Scope: three source-sealed components + hands-off-lifecycle

- `self-correction/` — Sites 1–5 (triggers.py, completion_check.py,
  observability.py).
- `graceful-degradation/` — Sites 6–8 (component.py, observability.py).
- `observability-aggregator/` — Sites 9, 10 (nl_path.py).
- `hands-off-lifecycle/` — BASELINE + SEAL_COMMIT + cross-cutting
  allowed-set admission (if not already present). No source edits.

No 5th sealed component touched. Halt trigger cleared.

### 3.4 Allowed-prefix tuple check per speedup CDC

- `self-correction/tests/test_no_sealed_amendments.py` — `allowed_prefixes
  = ("self-correction/", "data/")`. No other-component diff expected.
- `graceful-degradation/tests/test_no_sealed_amendments.py` — BASELINE
  `e8f704c` already admits `hands-off-lifecycle/`,
  `observability-aggregator/`, and other peers. Need to verify the
  `self-correction/` admission (not currently in list) — if this
  amendment's diff window shows `self-correction/`, the tuple needs
  `self-correction/` admitted.
- `observability-aggregator/tests/test_no_sealed_amendments.py` —
  BASELINE `e8f704c`; admits `graceful-degradation/`, `cost-governance/`,
  `orchestrator/`, `hands-off-lifecycle/`. Needs `self-correction/`
  admitted.
- Other sealed components' seal-diff tests diff their own frozen
  BASELINE..SEAL ranges that predate this amendment — their diffs
  remain empty.

### 3.5 BASELINE advances

- `self-correction/tests/test_no_sealed_amendments.py` — keep
  `BASELINE = "f94d602"` (it covers only self-correction + data); no
  change needed if the diff narrows to self-correction/.
- `graceful-degradation/tests/test_no_sealed_amendments.py` — advance
  `BASELINE = "e8f704c"` → `"24d54cb"` so the diff window is this
  amendment's own surface.
- `observability-aggregator/tests/test_no_sealed_amendments.py` — same
  BASELINE advance to `"24d54cb"`.
- `hands-off-lifecycle/tests/test_cross_cutting.py` — advance BASELINE
  `"f1ff28b"` → `"24d54cb"`; admit `self-correction`, `graceful-
  degradation`, `observability-aggregator` to the allowed top-level set
  (some of these already present from prior amendments; verify +
  extend narrative comment only).

## 4. Halt-trigger pre-check

- **A site you thought was live is actually in a teardown path.** All
  10 sites inspected: `build_trigger_from_span` (live call-path from
  poller), `OTelAnomalyPoller.run_forever` (long-running task, not
  teardown), `audit_subscription._on_event` (pyee handler, live),
  observability emitters (fire-and-forget, live), `_any_paused_scope_
  user_relevant` (notification gate, live), `reconcile_on_startup`
  (boot reconciliation, live), `episode_started` (live emitter),
  `NLPath.translate` + `NLPath.answer` (live query path). CDC 2 does
  NOT apply.
- **A fix requires changing a method's public exception-raising
  contract.** NONE — all fixes are emit-and-continue / emit-and-fall-
  through. No method begins raising a new exception class.
- **A fix requires touching a 5th sealed component.** NO — three named.
- **Test break outside the 4 touched components.** Predicted: none;
  the other 6 sealed components' seal-diff BASELINEs are frozen at
  prior amendment windows.

All halt triggers clear. Proceeding to plan.
