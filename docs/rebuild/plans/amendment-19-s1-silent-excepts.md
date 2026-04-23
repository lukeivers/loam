# Amendment #19 — S1 silent-except bundle

**Amendment number:** 19
**BASELINE (pre-amendment tip):** `f1ff28b` (`chore(seals):
delete-method-in-brief-dispatch-docs seal — ... at 8bdf194`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-22.
**Research doc:** `research/amendment-19-s1-silent-excepts-research.md`.
**Pre-dispatch skills:** research-before-plan CDC, audit-triage-by-severity
CDC, scope-only-dispatch CDC, plan-before-code CDC.

## 1. Intent

Fix the eight silent-except sites (`except Exception: pass|continue`
with `AC:none`) surfaced by the 2026-04-22 audit + classifier. Each fix
surfaces the exception observably (log + event-emit + default-return or
typed-result extension). None use `raise` — each site's caller contract
forbids re-raise (fail-closed + loop-safety invariants). Per the
audit-triage-by-severity CDC, bucket (d) outright silent-except violations
are fixed outright. Shutdown-catch exception CDC does NOT apply (no
teardown paths in scope).

## 2. Files edited per site

Per the research doc's per-site catalogue:

| Site | File | Fix |
|------|------|-----|
| 1 | `safety-layer/src/kill.py:90` | emit `pause_activation_failed`, suffix reason on record |
| 2 | `safety-layer/src/kill.py:157` | emit `pause_activation_failed`, suffix reason on record |
| 3 | `safety-layer/src/kill.py:166` | emit `scope_cancel_failed_during_kill`, collect `failed_scope_ids`, include in `KillEventRecord` |
| 4 | `safety-layer/src/kill.py:190` | emit `request_stop_failed` |
| 5 | `safety-layer/src/controller.py:297` | emit `persona_render_failed`, preserve un-rendered text |
| 6 | `safety-layer/src/controller.py:316` | emit `persona_render_failed`, preserve un-rendered text |
| 7 | `orchestrator/src/supervisor.py:431` | emit `supervisor.notify_failed` span (phase="open"), bump `EscalationRecord.notification_failures` |
| 8 | `orchestrator/src/supervisor.py:458` | emit `supervisor.notify_failed` span (phase="close") |

## 3. Source-code changes

### 3.1 `safety-layer/src/observability.py`

Add four new emitters:

- `pause_activation_failed(*, level, reason, source, exception_class)`
  — span `pos.safety.pause_activation_failed` with attrs
  `pos.safety.level`, `pos.safety.reason`, `pos.safety.source`,
  `pos.safety.exception_class`.
- `scope_cancel_failed_during_kill(*, level, scope_id, reason,
  exception_class)` — span
  `pos.safety.scope_cancel_failed_during_kill` with matching attrs.
- `request_stop_failed(*, reason, exception_class)` — span
  `pos.safety.request_stop_failed`.
- `persona_render_failed(*, kind, exception_class)` — span
  `pos.safety.persona_render_failed`.

All follow the existing emitter shape (context-manager span, attr
setters, no TracerProvider construction — A16).

### 3.2 `safety-layer/src/events.py`

Extend `KillEventRecord` with one new optional field:

```python
failed_scope_ids: tuple[str, ...] = ()
```

Pydantic `ConfigDict(extra="forbid", frozen=True)` tolerates declared
additions. Existing callers reading `cancelled_scope_ids` / other fields
unchanged.

### 3.3 `safety-layer/src/kill.py`

Site 1 (`kill_session`): replace the silent catch with:
```python
pause_failure = None
try:
    self.orchestrator.pause_activation(f"safety:session_kill:{reason}")
except Exception as e:
    pause_failure = type(e).__name__
    obs.pause_activation_failed(
        level="session", reason=reason, source=source,
        exception_class=pause_failure,
    )
```
The `pause_failure` variable feeds a reason-suffix when building the
record: `reason=(f"{reason} (pause_failed:{pause_failure})" if
pause_failure else reason)`.

Site 2 (`kill_system` pause): same shape, `level="system"`.

Site 3 (`kill_system` cancel-loop): replace silent-continue with:
```python
cancelled: list[str] = []
failed: list[str] = []
for sid in active_ids:
    try:
        await self.scope_runtime.cancel(sid, reason=f"safety:system_kill:{reason}")
        cancelled.append(sid)
    except Exception as e:
        failed.append(sid)
        obs.scope_cancel_failed_during_kill(
            level="system", scope_id=sid, reason=reason,
            exception_class=type(e).__name__,
        )
```
Record construction adds `failed_scope_ids=tuple(failed)`.

Site 4 (`kill_system` request_stop): replace silent catch with:
```python
try:
    self.orchestrator.request_stop()
except Exception as e:
    obs.request_stop_failed(
        reason=reason, exception_class=type(e).__name__,
    )
```

### 3.4 `safety-layer/src/controller.py`

Sites 5 + 6: replace silent catches with:
```python
if self.persona_render is not None:
    try:
        text = await self.persona_render(text)
    except Exception as e:
        obs.persona_render_failed(
            kind="ask_gate",  # or "dangerous_op"
            exception_class=type(e).__name__,
        )
```
The send still proceeds with un-rendered text (current behaviour).

### 3.5 `orchestrator/src/supervisor.py`

Add field to `EscalationRecord` dataclass:
```python
notification_failures: int = 0
```
Update `to_dict` / `from_dict` in lockstep:
- `to_dict`: add `"notification_failures": self.notification_failures`.
- `from_dict`: add `notification_failures=int(d.get(
  "notification_failures", 0) or 0)`.

Site 7 (`_open_escalation`): replace silent catch at line 431 with:
```python
try:
    await self._notify(cls, text, attrs)
    self._current_escalation.notifications_sent += 1
    self._current_escalation.last_notified_at = now_iso
except Exception as e:
    # Loop-safety invariant: never kill the probe loop on notifier
    # failure. Amendment #19 adds observability surface.
    if self._current_escalation is not None:
        self._current_escalation.notification_failures += 1
    with _TRACER.start_as_current_span(
        "pos.hands_off_lifecycle.supervisor.notify_failed"
    ) as span:
        span.set_attribute("escalation.class", cls.value)
        span.set_attribute("exception.class", type(e).__name__)
        span.set_attribute("phase", "open")
```

Site 8 (`_close_escalation`): replace silent catch at line 458 with:
```python
try:
    await self._notify(prior_cls, text, {"reason": reason})
except Exception as e:
    with _TRACER.start_as_current_span(
        "pos.hands_off_lifecycle.supervisor.notify_failed"
    ) as span:
        span.set_attribute("escalation.class", prior_cls.value)
        span.set_attribute("exception.class", type(e).__name__)
        span.set_attribute("close_reason", reason)
        span.set_attribute("phase", "close")
```

## 4. Test additions

Per the research doc, +6 tests in safety-layer, +2 in orchestrator,
+0 in hands-off-lifecycle.

### 4.1 `safety-layer/tests/test_kill_session.py` — +1 test

`test_A2_session_kill_pause_failure_is_surfaced` — builds a fake
orchestrator whose `pause_activation` raises `RuntimeError("boom")`;
asserts:
- `record.reason` contains `"pause_failed:RuntimeError"`.
- Cancellation still ran (the rest of the session-kill record is
  correct).

### 4.2 `safety-layer/tests/test_kill_system.py` — +3 tests

`test_A3_system_kill_pause_failure_is_surfaced` — analogous to 4.1.

`test_A3_system_kill_cancel_failure_records_failed_scope_ids` — fake
scope-runtime whose `cancel(sid=...)` raises for a named scope; asserts
`record.failed_scope_ids == (sid,)` and `cancelled_scope_ids` contains
only the successful ids.

`test_A3_system_kill_request_stop_failure_is_surfaced_and_record_returned`
— fake orchestrator whose `request_stop` raises; asserts `record` still
returned, `safety_store.active_system_kill()` is not None (state row
persisted), `fake_orchestrator.stop_requested` is still False (failure
correctly did not flip the flag in the fake).

### 4.3 `safety-layer/tests/test_ask_gate_persona_render_failure.py` — new file, +2 tests

`test_ask_gate_persona_render_failure_falls_back_to_unrendered_text` —
fake `persona_render` raises; assert the `SafetyNotification` was sent
with the un-rendered text, no exception surfaced past `check_gates`.

`test_dangerous_op_persona_render_failure_falls_back_to_unrendered_text`
— same pattern for the dangerous-op path.

### 4.4 `orchestrator/tests/test_supervisor.py` — +2 tests

`test_S1_open_escalation_notify_failure_emits_span_and_bumps_counter` —
passes a notifier that raises `RuntimeError` on every call; after three
fails the supervisor escalates; assert `supervisor.state is
SupervisorState.escalated`, `attention.md` exists (file-write is outside
the notifier try-block), `current_escalation.notification_failures == 1`.

`test_S1_close_escalation_notify_failure_does_not_stall_recovery` —
notifier that raises on the close call only; trigger escalate-then-
recover sequence; assert `supervisor.state is SupervisorState.normal`,
`current_escalation is None`, `attention.md` does not exist (clear-path
ran despite notifier failure).

## 5. BASELINE + SEAL advances

### 5.1 Amendment commit

1. `orchestrator/tests/test_no_sealed_amendments.py` — advance `BASELINE
   = "f1ff28b"` (was `"e8f704c"`). Add history comment naming
   amendment #19. Extend `allowed_prefixes` to admit `safety-layer/`
   (new multi-component partner).
2. `hands-off-lifecycle/tests/test_cross_cutting.py` — advance
   `BASELINE = "f1ff28b"`. Add history comment. Extend the `allowed`
   top-level set in `test_H19_diff_scope_covers_only_approved_surfaces`
   to include `"safety-layer"`.
3. `safety-layer/tests/test_no_sealed_amendments.py` — no BASELINE
   present (this file is a monkey-patch / import guard only, not a
   seal-diff test). No edit.
4. Other sealed components with seal-diff tests (cost-governance,
   graceful-degradation, memory-system, observability-aggregator,
   reversibility-primitive, self-correction, telegram-interface,
   workspace-bootstrap) — per the diff-scope-allowlist-widening cycle:
   if any ships its seal-diff test with an `allowed_prefixes` tuple
   that does NOT admit `safety-layer/` OR `orchestrator/` OR
   `hands-off-lifecycle/`, they must be extended. Audit at
   implementation time (plan captures the check; actual tuple edits
   per-file).

### 5.2 Seal commit (separate — no `--amend`)

After amendment commit lands green on all suites:

1. `orchestrator/tests/SEAL_COMMIT` — overwrite with amendment SHA.
2. `hands-off-lifecycle/tests/SEAL_COMMIT` — overwrite with amendment
   SHA.
3. `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — append
   amendment #19 narrative block.
4. `safety-layer/` — NO seal sidecar exists; no bump.

## 6. Test-suite counts

| Suite | Before | After |
|-------|--------|-------|
| safety-layer | 64 | 70 (+6) |
| orchestrator | 73 | 75 (+2) |
| hands-off-lifecycle | 66 | 66 (0) |

Other sealed components: 0 behavioural change. If an allowed-prefix
tuple widens, those suites' own tests still pass.

## 7. Commit messages

**Amendment commit (shape, authored at landing):**
```
fix(safety-layer, orchestrator, hands-off-lifecycle): S1 silent-except bundle — surface 8 AC:none violations (amendment #19)

Per the 2026-04-22 audit + classifier run, eight `except Exception: pass`
or `continue` branches with no AC backing live in live operational paths
across the safety-layer and orchestrator supervisor. Per ODD §8 rule 8
and the audit-triage-by-severity CDC (bucket d — outright violations),
the fix is outright required. The shutdown-catch CDC does not apply:
none of these are teardown methods.

[... per-site bullets ...]
```

**Seal commit (shape):**
```
chore(seals): s1-silent-excepts seal — safety-layer + orchestrator + hands-off-lifecycle at <amendment-sha>
```

## 8. Halt triggers

- Research reveals an AC naming the silent-catch as intentional — flag
  `AC:none` tagging as wrong.
- A fix requires changing a public API shape (raise new exception from
  a method that didn't) — halt.
- A fix requires touching a 4th sealed component — halt.
- Test count changes unexpectedly (existing tests break in a way the
  plan didn't predict) — halt.

All four cleared at research time (see research doc §4). Re-checked at
landing.

## 9. ODD compliance check (per plan-before-code CDC)

For each added branch / test / dependency, point at the AC it satisfies:

- Sites 1, 2, 4 fixes: map to a new AC in the amendment-19 scope —
  "live operational silent-except violations in the kill engine must
  surface to OTel; no state-damaging behaviour change." The audit-
  triage-by-severity CDC's bucket-(d) entry IS the backing rule.
- Site 3 fix: same AC. The `failed_scope_ids` field is the observable
  surface by which callers can distinguish "nothing to cancel" from
  "cancellation failed."
- Sites 5, 6 fixes: same AC, plus the pre-existing "notifications must
  go out regardless of LLM availability" (fail-closed direction of the
  ask-gate + dangerous-op gate contracts).
- Sites 7, 8 fixes: same AC; supervisor's "loop must not crash on
  transient errors" is preserved (the current code's design intent,
  already implicit in the H-criteria's loop-safety invariant).

`kill_session` line 99 silent-continue is NOT touched (research §3.1) —
it is not in the classifier's 8-finding set, and its inline comment names
a §8-style intentional-silence case. Re-classifying narrow exception
subclasses there is future work, out of this amendment's scope.
