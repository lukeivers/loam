# Amendment #19 — S1 Silent-Except Bundle — Research Document

**Amendment number:** 19
**BASELINE (pre-amendment tip):** `f1ff28b` (`chore(seals): delete-method-in-brief-dispatch-docs seal — ... at 8bdf194`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-22.
**Companion plan:** `../amendment-19-s1-silent-excepts.md` (authored after this
research concludes).

## 1. Intent

Eight `except Exception: pass` / `continue` branches across `safety-layer/`
and `orchestrator/` (the hands-off-lifecycle surface) were surfaced by the
2026-04-22 silent-exception audit + classifier run, each tagged `AC:none`
(no acceptance criterion names the path as intentionally silent). Per ODD
§8 rule 8, code paths that handle cases not named in the acceptance criteria
must re-extend up with a named criterion plus test, or the silent catch
must be replaced with an observable-surface fix.

The just-landed **audit-triage-by-severity** CDC (`e8f704c`) names the
triage: bucket (d) — outright silent-except violations in live operational
paths — is fixed outright. The **shutdown-catch exception** CDC (also at
`e8f704c`) does NOT apply here: all eight sites live in live operational
paths (kill-engine, ask-gate dispatch, escalation notify). None are in
teardown methods (`close()` / `stop()` / `cancel()`). The shutdown-catch
exemption is inapplicable.

This research doc catalogues each site with enough context to author the
amendment-19 plan.

## 2. Per-site catalogue

### Site 1 — `safety-layer/src/kill.py:90` — `kill_session` pause_activation

**Function:** `KillEngine.kill_session`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 83–103):**
```python
async def kill_session(
    self, *, reason: str, source: KillSource
) -> KillEventRecord:
    """Pause activation, cancel every non-terminal scope."""
    # Pause first so new scopes cannot activate while we iterate.
    try:
        self.orchestrator.pause_activation(f"safety:session_kill:{reason}")
    except Exception:
        pass

    active_ids = await self._list_non_terminal_scope_ids()
    cancelled: list[str] = []
    ...
```

**Callers:**
- `safety-layer/src/ipc_wiring.py:69` — IPC handler `safety.kill_session`.
  Returns `{"ok": True, "level": ..., "cancelled": [...]}` to the caller
  on the other end of the Unix socket.
- `safety-layer/src/cli.py:91` — CLI dispatches the same IPC method; it
  json-prints the response.
- `safety-layer/tests/test_kill_session.py`, `test_safety_beats_degradation.py`
  — call `engine.kill_session(...)` directly and assert both the record
  shape and the fake-orchestrator's `pause_log` list.

**Caller contract:** callers expect a `KillEventRecord` back. Today, if
`pause_activation` throws, cancellation still proceeds; the record says
the session kill succeeded even though activation was not actually
paused — and `fake_orchestrator.is_paused` in test would be False, which
is precisely the hidden defect the test **cannot** detect because the
real orchestrator's `pause_activation` never throws today. The "silence"
reveals itself only on a real-orchestrator regression.

**Observability surface already in scope:** `obs.session_kill(...)` at
line 113 and `operation_span(...)` context manager in observability.py,
plus the kill-event `record_kill` persists an audit row. There is no
existing pause-failure surface.

**Fix (chosen):** **Option C — Log + event-emit + default-return** via a
new observability emitter `pause_activation_failed(level, reason, source,
exception_class)`. The audit record's `reason` field additionally
incorporates the failure so the persisted audit row is honest:
`reason=f"{reason} (pause_failed:{type(e).__name__})"`. The kill continues
(cancellation still runs) so a user-issued session kill is not blocked
by a transient pause-activation error. This preserves the contract
"returns a KillEventRecord on any issued session-kill" while surfacing
the pause failure to the audit log + OTel span.

**Justification:** the caller's contract is a record return; there is no
signal in the record shape for "pause failed but cancellation ran." Adding
a new OTel emitter + reason-suffix surfaces the failure to the exact
channels the safety layer already uses; callers don't need to change. A
re-raise would block user-initiated kills on transient issues, the opposite
of the fail-safe direction.

**Existing test exercising the swallow:** none directly. The fake
orchestrator's `pause_activation` never raises. Amendment adds one new
test that injects a raising stub and asserts the audit row's reason
contains the failure class name + the OTel emitter fired.

---

### Site 2 — `safety-layer/src/kill.py:157` — `kill_system` pause_activation

**Function:** `KillEngine.kill_system`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 147–167):**
```python
if source == "ipc":
    if nonce is None or not self._check_nonce(nonce):
        raise ValueError(...)

# Pause activation so nothing new starts.
try:
    self.orchestrator.pause_activation(f"safety:system_kill:{reason}")
except Exception:
    pass

active_ids = await self._list_non_terminal_scope_ids()
cancelled: list[str] = []
for sid in active_ids:
    try:
        await self.scope_runtime.cancel(sid, reason=f"safety:system_kill:{reason}")
        cancelled.append(sid)
    except Exception:
        continue
```

**Callers:** mirror of Site 1 — IPC handler `safety.kill_system` at
`ipc_wiring.py:87`, CLI at `cli.py:103`, tests at `test_kill_system.py`
+ `test_safety_beats_degradation.py` + `test_system_kill_clean_exit.py`.

**Caller contract:** same as Site 1, plus `record_system_kill` persists a
terminal system-kill state row the next bootstrap reads.

**Observability surface:** `obs.system_kill(...)` at line 183, plus the
new `pause_activation_failed(...)` emitter introduced for Site 1. Same
emitter covers both call sites — it takes a `level` kwarg naming which
level fired.

**Fix (chosen):** **Option C — Log + event-emit + default-return**, same
pattern as Site 1. Reason suffix added to the record.

**Justification:** identical to Site 1. A user-issued system kill must
not be blocked by a transient pause failure; the audit trail + OTel span
must nonetheless show it happened.

**Existing test:** none; add one asserting the emitter fires + the audit
reason is suffixed.

---

### Site 3 — `safety-layer/src/kill.py:166` — `kill_system` cancel loop

**Function:** `KillEngine.kill_system`.
**Classifier label:** `except Exception: continue`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 160–167):**
```python
active_ids = await self._list_non_terminal_scope_ids()
cancelled: list[str] = []
for sid in active_ids:
    try:
        await self.scope_runtime.cancel(sid, reason=f"safety:system_kill:{reason}")
        cancelled.append(sid)
    except Exception:
        continue
```

**Classifier's concern:** callers infer from `record.cancelled_scope_ids`
which scopes were killed. A scope that raises during `cancel()` is silently
dropped — the caller sees a shorter list than `active_ids` but no signal
that the missing scopes failed-to-kill vs. were already terminal.

**Caller contract:** `KillEventRecord.cancelled_scope_ids` is currently
advertised as "the scopes that were cancelled by this kill." Scopes that
failed-to-kill should NOT appear in this list today (correct) but the
caller has no way to distinguish "nothing to kill" from "kill failed."

**Observability surface:** `obs.system_kill(reason, source, cancelled_count)`
already emits the cancelled count. No failed-kill surface.

**Fix (chosen):** **Option C — Log + event-emit + default-return** via a
new observability emitter `scope_cancel_failed_during_kill(level,
scope_id, reason, exception_class)`. The kill loop records per-scope
failures (scope_id + exception class) and surfaces them in a new
`KillEventRecord.failed_scope_ids: tuple[str, ...]` field, alongside the
existing `cancelled_scope_ids`. The event is stored + the OTel emitter
fires once per failure.

**Public API shape:** adding a field to `KillEventRecord` is a model
change. The existing field-set is `level, reason, source, scope_id,
issued_at, cancelled_scope_ids`. Adding a NEW field with a default-empty
tuple is a backwards-compatible extension — existing callers reading
`cancelled_scope_ids` continue to work. Pydantic `ConfigDict(extra="forbid",
frozen=True)` permits new declared fields. Mirror the same addition in
`kill_session` (Site 1 loop at line 99–102 — the same silent-continue
pattern, though the comment there explicitly names the "terminal between
list and cancel" intent; we preserve that explicit case by classifying
exceptions). See §3 below.

**Justification:** this is the case the proposal specifically flagged —
"caller thinks scope was killed when it wasn't." The typed-result addition
(structured error in return value) is the correct pattern from the
principles §Per-site fix principles. Re-raise would block the whole kill
on a single scope failure (wrong). Log-only loses the per-caller signal.

**Existing test:** `test_A3_system_kill_cancels_all_and_calls_request_stop`
+ `test_A2_session_kill_pauses_activation_and_cancels_all` assert that
`record.cancelled_scope_ids` equals the active-set. These tests pass
today because no cancellation actually fails. New test injects a failing
cancel and asserts `failed_scope_ids` contains the offending id, the
emitter fired, and `cancelled_scope_ids` does NOT contain the failed
id (unchanged behaviour for that field).

---

### Site 4 — `safety-layer/src/kill.py:190` — `kill_system` request_stop

**Function:** `KillEngine.kill_system`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 187–192):**
```python
# Clean exit: trigger orchestrator's stop event.
try:
    self.orchestrator.request_stop()
except Exception:
    pass
return record
```

**Callers:** same as Sites 1–3 (system-kill IPC, CLI, tests).

**Caller contract:** `kill_system` must return a `KillEventRecord`; the
state row is already persisted (line 172, before this try-block) so a
`request_stop` failure does NOT corrupt the next-bootstrap contract.
Ruling #2 says the orchestrator exits 0 via `request_stop`; a failure
here means the orchestrator does NOT exit — operationally serious but
not data-damaging.

**Observability surface:** `obs.system_kill(...)` fires BEFORE the
request_stop try-block. No request-stop surface.

**Fix (chosen):** **Option C — Log + event-emit + default-return** via a
new observability emitter `request_stop_failed(reason, exception_class)`.
The audit record's reason is NOT mutated here (different from Sites 1–2
where the audit precedes the stop) — instead the emitter surfaces the
failure to OTel. The reason is preserved as-is on the existing record;
a new emitter captures the stop-failure independently.

**Justification:** the audit row and the persisted system-kill state
both already landed. The only observability gap is that `request_stop`
silently failed. A new emitter surfaces it without breaking the
"returns a KillEventRecord" contract. Re-raise would violate the
"state row must already exist if we get past line 172" invariant (A4);
the caller would see a ValueError and might retry the whole kill,
double-writing the state.

**Existing test:** `test_A3_system_kill_cancels_all_and_calls_request_stop`
asserts `fake_orchestrator.stop_requested` is True. New test injects a
raising `request_stop` and asserts the emitter fired + the record was
still returned + the state row is still present.

---

### Site 5 — `safety-layer/src/controller.py:297` — `_dispatch_ask_notification` persona_render

**Function:** `SafetyController._dispatch_ask_notification`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 294–301):**
```python
if self.persona_render is not None:
    try:
        text = await self.persona_render(text)
    except Exception:
        pass
await self.notifier.send(
    SafetyNotification(kind="ask_gate", text=text, scope_id=scope_id)
)
```

**Callers:** `SafetyController.check_gates` at `controller.py:156`,
which fires when the ask gate blocks.

**Caller contract:** `_dispatch_ask_notification` returns None; it is
called for its side effect (sending the notification). The outer
`check_gates` raises `ApplicationError` after this dispatch. `persona_render`
is an optional LLM-mediated adaptation of the notification text — if it
fails, the un-rendered text is still a valid notification.

**Observability surface:** `obs.ask_gate_fired(...)` fires BEFORE the
dispatch. `obs.notification_dispatched(...)` exists in observability.py
but is not called here today — worth surfacing. No persona-render failure
surface.

**Fix (chosen):** **Option C — Log + event-emit + default-return** via a
new observability emitter `persona_render_failed(kind, exception_class)`.
The dispatcher proceeds with the un-rendered text (today's behaviour,
preserved — the un-rendered text is still complete + correct). Emitter
surfaces the failure to OTel; the send happens regardless.

**Justification:** the safety notification MUST go out regardless of
LLM availability — that's the fail-closed guarantee. Re-raising would
turn a cosmetic LLM issue into a gate-failure; the user's safety
notification would disappear. Structured-error return has no caller to
consume it (the function returns None). Log + emit is the right surface.

**Existing test:** none specifically. The ask-gate tests exercise the
dispatch path but `persona_render` is None in fixtures. New test sets a
raising `persona_render`, asserts the emitter fires, and asserts the
notification was still sent.

---

### Site 6 — `safety-layer/src/controller.py:316` — `_dispatch_dangerous_op_notification` persona_render

**Function:** `SafetyController._dispatch_dangerous_op_notification`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 313–320):**
```python
if self.persona_render is not None:
    try:
        text = await self.persona_render(text)
    except Exception:
        pass
await self.notifier.send(
    SafetyNotification(kind="dangerous_op", text=text, scope_id=scope_id)
)
```

**Callers:** `SafetyController.check_gates` at `controller.py:196`.

**Caller contract:** mirror of Site 5.

**Observability surface:** `obs.dangerous_op_gate_fired(...)` fires
before the dispatch. Same `persona_render_failed` emitter covers both
sites — emitter takes a `kind` kwarg ("ask_gate" | "dangerous_op").

**Fix (chosen):** **Option C — Log + event-emit + default-return**, same
emitter as Site 5.

**Justification:** identical to Site 5.

**Existing test:** none specifically; new test mirrors Site 5's but with
`_dispatch_dangerous_op_notification`.

---

### Site 7 — `orchestrator/src/supervisor.py:431` — `_open_escalation` notifier

**Function:** `MemorySupervisor._open_escalation`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 425–433):**
```python
if need_notify and self._notify is not None:
    text = self._render_alert(cls, attrs)
    try:
        await self._notify(cls, text, attrs)
        self._current_escalation.notifications_sent += 1
        self._current_escalation.last_notified_at = now_iso
    except Exception:
        # Never kill the loop on notifier failure.
        pass
```

**Classifier's concern:** the comment ("Never kill the loop on notifier
failure") is a correct design intent but the silent catch hides the
notifier failure entirely. The user sees NO escalation alert in the
failure case; `attention.md` file-write + the OTel span at 436 still
fire, but the user's push notification never arrives.

**Callers:** `_on_fail` at supervisor.py:351 (escalation-retry-limit
trip) and at supervisor.py:374 (class-change re-notify).

**Caller contract:** `_open_escalation` returns None. The probe loop
MUST not crash on notifier failure (correct design intent — preserved).

**Observability surface:** the span at line 436 (`escalation_opened`)
fires regardless. No notifier-failure span exists. This is inside the
`hands-off-lifecycle` component; the tracer is
`trace.get_tracer("pos.hands_off_lifecycle", "0.1.0")`.

**Fix (chosen):** **Option C — Log + event-emit + default-return**. Add
a span `pos.hands_off_lifecycle.supervisor.notify_failed` (same tracer,
same namespace) inside the except-block with attrs `escalation.class`,
`exception.class`. The comment's invariant ("never kill the loop")
remains — the span is the observable surface that replaces the silent
pass. Additionally, increment a new field
`EscalationRecord.notification_failures: int` so persisted state reflects
that notifications were attempted but failed.

**Justification:** the design intent is correct — crashing the probe
loop on a transient notifier failure would be worse than the silent
case. The fix is observability: emit a span + bump a counter on the
record so an operator can see "escalation opened, but notification
failed N times." The re-raise path would be wrong (breaks the loop
invariant). The typed-result path has no caller to read it (returns
None). Log+span is the right surface.

**Public API shape:** adding a field to `EscalationRecord` with a
default 0 + updating `to_dict`/`from_dict` accordingly. Pydantic-free
dataclass — `@dataclass` — already supports default values. This is a
backwards-compatible extension.

**Existing test:** `test_H16_escalation_notifies_once_then_dedups` and
`test_H17_class_change_re_notifies` — both use a passing notifier that
never raises. New test injects a raising notifier and asserts the
supervisor state stays `escalated` (loop not crashed), `attention.md`
still written, `notification_failures == 1`, and the new span fires.

---

### Site 8 — `orchestrator/src/supervisor.py:458` — `_close_escalation` notifier

**Function:** `MemorySupervisor._close_escalation`.
**Classifier label:** `except Exception: pass`.
**Actual exception caught:** bare `Exception`.

**Full context (lines 455–459):**
```python
text = self._render_resolved(prior_cls, reason)
if self._notify is not None:
    try:
        await self._notify(prior_cls, text, {"reason": reason})
    except Exception:
        pass
```

**Classifier's concern:** user-facing — if the "resolved" notification
fails to send, the user sees stale "pOS v2 needs attention" from a
prior alert and doesn't know the system recovered. This is a correctness
issue on the attention surface.

**Callers:** `_on_ok` at supervisor.py:322 (recovery confirmed), and
`_open_escalation` at supervisor.py:420 (class-change path — closes old
before opening new).

**Caller contract:** `_close_escalation` returns None. Clears
`self._current_escalation`, deletes attention file, persists state.

**Observability surface:** the span at line 460
(`escalation_closed`) fires regardless. No notifier-failure span exists.

**Fix (chosen):** **Option C — Log + event-emit + default-return**. Same
pattern as Site 7 — add a span
`pos.hands_off_lifecycle.supervisor.notify_failed` inside the
except-block with attrs `escalation.class=<prior_cls>`,
`exception.class=<type>`, `close_reason=<reason>`. The `attention.md`
file-delete + `_persist_escalation` calls still fire (they're already
outside the notifier-try-block) so the local state correctly reflects
recovery; the observability surface now captures the send-failure.

**Justification:** the local state must reconcile to "not escalated"
regardless — `self._current_escalation = None` and `_clear_attention()`
are the local-state invariant that must NOT be conditional on notifier
success. The observability span captures the failure so an operator can
re-send or investigate. Re-raise would abort `_close_escalation` halfway
— state persistence + attention-file clear would not run — which would
be a worse user-facing surface than the silent case we're fixing.

**Note on `notification_failures` counter:** on the close path,
`self._current_escalation` is about to be set to None. A counter bump
here would be lost on close. So the close-path fix is span-only; the
open-path fix is span + counter.

**Existing test:**
`test_H17_recovery_closes_escalation_and_clears_attention` asserts a
"resolved" notification is present. New test injects a raising notifier
ONLY on the close, asserts state resets to `normal`, attention cleared,
the new span emitted.

---

## 3. Cross-cutting notes

### 3.1 `kill_session` loop parallel with Site 3

`kill_session` (lines 95–102) has the same silent-continue pattern as
`kill_system` (Site 3). The classifier's report only names Site 3 — the
session-level loop is arguably in-scope, but the comment there (line
100-101) explicitly names the case: "A scope that went terminal between
list() and cancel() is not a kill failure — record and continue." This
is precisely the `AC:intentional` tagging the audit-triage CDC (e8f704c)
permits. HOWEVER: the except catches bare `Exception`, so a real-failure
kill is swallowed the same way. Per the "classify exceptions" discipline
(FUTURE_IDEAS audit-triage-by-severity → "promote to narrower"), the
safest minimal fix is to distinguish `ScopeNotFoundError`-shaped "already
terminal" from other failures. Since scope-of-work's exception taxonomy
is not named in the research scope and this site is NOT in the
classifier's 8-finding set, we DO NOT touch line 99 in this amendment.
The ODD-compliance verification in §5 will note this deliberately.

### 3.2 New observability emitters

Four new emitters, consolidated:

1. `safety-layer/src/observability.py` — `pause_activation_failed(level,
   reason, source, exception_class)` (covers Sites 1, 2).
2. `safety-layer/src/observability.py` —
   `scope_cancel_failed_during_kill(level, scope_id, reason,
   exception_class)` (covers Site 3).
3. `safety-layer/src/observability.py` — `request_stop_failed(reason,
   exception_class)` (covers Site 4).
4. `safety-layer/src/observability.py` — `persona_render_failed(kind,
   exception_class)` (covers Sites 5, 6).
5. `orchestrator/src/supervisor.py` — inline span emitter (no separate
   module; supervisor already uses `_TRACER.start_as_current_span(...)`
   inline). Single span name
   `pos.hands_off_lifecycle.supervisor.notify_failed` covers Sites 7, 8
   with a `phase` attribute ("open" | "close").

All emitters use the existing `trace.get_tracer(...)` pattern (A16 / H8)
— no TracerProvider construction.

### 3.3 Public API extensions

- `KillEventRecord.failed_scope_ids: tuple[str, ...] = ()` — new field,
  default empty, backwards-compatible (site 3).
- `EscalationRecord.notification_failures: int = 0` — new field, default
  0, backwards-compatible (site 7).

Neither changes an existing return-type's shape; both are additive.
Neither raises a new exception class from a method that didn't previously
raise. This clears the halt trigger "A fix requires changing a public
API shape." The extensions are additions, not shape changes.

### 3.4 Scope: three sealed components

- `safety-layer/` — sites 1–6 (kill.py, controller.py, observability.py,
  events.py).
- `orchestrator/` — sites 7–8 (supervisor.py, events.py/dataclass).
- `hands-off-lifecycle/` — BASELINE + SEAL_COMMIT + cross-cutting
  allowed-set bump. No source code edits.

No 4th sealed component touched. Halt trigger cleared.

## 4. Halt-trigger pre-check

- **Research reveals an AC naming the silent-catch as intentional** —
  NO for all 8 sites. The `_open_escalation` comment at line 432
  ("Never kill the loop on notifier failure") names a loop-safety
  invariant, not an AC-named intentional silence. The fix PRESERVES
  that invariant while adding observability. Classifier's `AC:none`
  tagging stands.
- **A fix requires changing a public API shape** — NO. Two
  backwards-compatible additions only.
- **A fix requires touching a 4th sealed component** — NO. Three named.
- **Test count changes unexpectedly** — predicted: safety-layer +6 tests
  (one per site 1–6 new-behaviour), orchestrator +2 tests (sites 7–8),
  hands-off-lifecycle +0. Plan will enumerate them.

All halt triggers clear. Proceeding to plan doc.
