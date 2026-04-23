# Amendment #20 — S2 silent-except bundle

**Amendment number:** 20
**BASELINE (pre-amendment tip):** `24d54cb`.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-22.
**Research doc:** `research/amendment-20-s2-silent-excepts-research.md`.
**Pre-dispatch skills:** research-before-plan CDC, audit-triage-by-severity
CDC, amendment-dispatch speedup CDC, scope-only-dispatch CDC,
plan-before-code CDC.

## 1. Intent

Fix the ten `except Foo: pass|continue` sites surfaced by the 2026-04-22
audit + classifier with `AC:none` across `self-correction/` (5),
`graceful-degradation/` (3), and `observability-aggregator/` (2). Each
fix replaces the silent branch with an observable-surface fix (span
emit or span-event on already-open span). None change public exception-
raising contracts. None are in teardown paths (shutdown-catch CDC
does not apply).

## 2. Files edited per site

| Site | File | Fix |
|------|------|-----|
| 1 | `self-correction/src/triggers.py:94` | emit `span_attribute_lookup_failed`, preserve `scope_id=None` default |
| 2 | `self-correction/src/triggers.py:252` | emit `poll_tick` on timeout iteration; keep `continue` |
| 3 | `self-correction/src/completion_check.py:124` | emit `audit_notify_no_loop`; keep drop |
| 4 | `self-correction/src/observability.py:122` | `span.add_event("status_set_failed", ...)` on already-open span |
| 5 | `self-correction/src/observability.py:165` | `span.add_event("status_set_failed", ...)` on already-open span |
| 6 | `graceful-degradation/src/component.py:443` | emit `scope_lookup_failed`; keep `continue` |
| 7 | `graceful-degradation/src/component.py:513` | emit `reconcile_restore_failed`; keep `pass` |
| 8 | `graceful-degradation/src/observability.py:144` | `span.add_event("paused_scope_ids_attr_failed", ...)` on already-open span |
| 9 | `observability-aggregator/src/nl_path.py:387` | `span.add_event("llm_translate_failed", ...)` on already-open span |
| 10 | `observability-aggregator/src/nl_path.py:426` | `span.add_event("llm_format_failed", ...)` on already-open span |

## 3. Source-code changes

### 3.1 `self-correction/src/observability.py`

Add three new emitters (same tracer, same `_set` helper):

- `span_attribute_lookup_failed(*, trigger_source, attribute_name,
  exception_class)` — span `pos.correction.span_attribute_lookup_failed`.
- `poll_tick(*, poller_name, interval_seconds)` — span
  `pos.correction.poll_tick`.
- `audit_notify_no_loop(*, episode_id)` — span
  `pos.correction.audit_notify_no_loop`.

Sites 4, 5: in-place amendments — replace `except Exception: pass` with
`except Exception as e: span.add_event("status_set_failed",
{"exception_class": type(e).__name__})`. No emitter; the enclosing span
is in scope.

### 3.2 `self-correction/src/triggers.py`

Site 1: replace silent catch with:
```python
scope_id = None
try:
    scope_id = span.attributes.get("pos.scope.id")
except Exception as e:
    obs.span_attribute_lookup_failed(
        trigger_source=TriggerSource.otel_anomaly.value,
        attribute_name="pos.scope.id",
        exception_class=type(e).__name__,
    )
```

Site 2: replace silent continue with:
```python
try:
    await asyncio.wait_for(
        self._stopped.wait(), timeout=self._interval
    )
except asyncio.TimeoutError:
    obs.poll_tick(
        poller_name="otel_anomaly",
        interval_seconds=self._interval,
    )
    continue
```
(Imports at module level: the emitter call module-imports
`self_correction.observability` — already imported via `_handler`'s
downstream; verify import form at implementation time.)

### 3.3 `self-correction/src/completion_check.py`

Site 3: replace silent catch with:
```python
if notify is not None:
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            notify(ep.episode_id, ",".join(missing_list))
        )
    except RuntimeError:
        obs.audit_notify_no_loop(episode_id=ep.episode_id)
```
(The `obs` import already exists at module top — line 28.)

### 3.4 `graceful-degradation/src/observability.py`

Add two new emitters:

- `scope_lookup_failed(*, episode_id, scope_id, exception_class)` — span
  `pos.degradation.scope_lookup_failed`.
- `reconcile_restore_failed(*, episode_id, mode_value, policy_value,
  exception_class)` — span
  `pos.degradation.reconcile_restore_failed`.

Site 8: in-place — replace `except Exception: pass` with
`except Exception as e: span.add_event(
"paused_scope_ids_attr_failed", {"exception_class": type(e).__name__,
"count": len(paused_scope_ids)})`.

### 3.5 `graceful-degradation/src/component.py`

Site 6: replace silent continue with:
```python
def _any_paused_scope_user_relevant(self, ep: ActiveEpisode) -> bool:
    for sid in ep.paused_scope_ids:
        scope = None
        try:
            scope = self.scope_runtime.get(sid)
        except Exception as e:
            obs.scope_lookup_failed(
                episode_id=ep.episode_id,
                scope_id=sid,
                exception_class=type(e).__name__,
            )
            continue
        if scope is not None and scope_has_user_relevant_escalation(scope):
            return True
    return False
```
(`obs` module import already exists.)

Site 7: replace silent ValueError-pass with:
```python
try:
    mode = DegradationMode(ep_row.mode)
    policy = Policy(ep_row.policy)
    self.active_episodes[mode] = ActiveEpisode(...)
except ValueError as e:
    obs.reconcile_restore_failed(
        episode_id=ep_row.episode_id,
        mode_value=ep_row.mode,
        policy_value=ep_row.policy,
        exception_class=type(e).__name__,
    )
```

### 3.6 `observability-aggregator/src/nl_path.py`

Sites 9, 10: in-place — replace `except Exception: pass` with
`except Exception as e: span.add_event("llm_translate_failed",
{"exception.class": type(e).__name__, "fallback": "rule_based"})` (and
`llm_format_failed` for Site 10). Span is already open in the enclosing
`with`.

## 4. Test additions (+10 total)

Per the research doc §2. +5 in self-correction, +3 in graceful-
degradation, +2 in observability-aggregator.

### 4.1 `self-correction/tests/` — +5 tests

- `test_detection_otel_anomaly.py` — +2:
  - `test_build_trigger_from_span_attribute_failure_emits_span`.
  - `test_poll_tick_emits_span_on_timeout_iteration`.
- `test_four_part_enforcement.py` — +1:
  - `test_audit_subscription_drops_notify_with_no_loop_observably`.
- `test_observability_routing.py` — +2:
  - `test_episode_refused_status_set_failure_is_captured`.
  - `test_cost_refusal_caught_status_set_failure_is_captured`.

### 4.2 `graceful-degradation/tests/` — +3 tests

- `test_d5_notification.py` — +1:
  - `test_any_paused_scope_user_relevant_surfaces_lookup_failures`.
- `test_d8_state.py` — +1:
  - `test_reconcile_on_startup_surfaces_invalid_stored_enum_values`.
- `test_d9_observability.py` — +1:
  - `test_episode_started_surfaces_paused_scope_ids_attr_failure`.

### 4.3 `observability-aggregator/tests/` — +2 tests

- `test_d5_nl_path.py` — +2:
  - `test_nl_translate_surfaces_llm_failure_on_fallback`.
  - `test_nl_answer_surfaces_llm_failure_on_fallback`.

## 5. BASELINE + SEAL advances

### 5.1 Amendment commit

1. `graceful-degradation/tests/test_no_sealed_amendments.py` — advance
   `BASELINE = "e8f704c"` → `"24d54cb"`. Admit `self-correction/`
   +  `observability-aggregator/` to `allowed_prefixes` if not present,
   plus `docs/rebuild/plans/` (research + plan docs).
2. `observability-aggregator/tests/test_no_sealed_amendments.py` —
   advance `BASELINE = "e8f704c"` → `"24d54cb"`. Admit `self-correction/`
   if not present; `docs/rebuild/plans/` if not present.
3. `self-correction/tests/test_no_sealed_amendments.py` — keep
   `BASELINE = "f94d602"` unless self-correction diff leaks outside
   `self-correction/` + `data/`. Predicted: this amendment leaves
   self-correction diff strictly within its own tree. If not, amend to
   `"24d54cb"` + admit the peer components.
4. `hands-off-lifecycle/tests/test_cross_cutting.py` — advance
   `BASELINE = "f1ff28b"` → `"24d54cb"`. Admit the three amended
   components to the H19 allowed top-level set (most already present
   from prior amendments; verify + extend history comment).

### 5.2 Seal commit (separate — no `--amend`)

After amendment commit lands green on all four touched suites + seal-
diff on the 6 untouched sealed components:

1. `self-correction/tests/SEAL_COMMIT` — overwrite with amendment SHA.
2. `graceful-degradation/tests/SEAL_COMMIT` — overwrite with amendment SHA.
3. `observability-aggregator/tests/SEAL_COMMIT` — overwrite with amendment SHA.
4. `hands-off-lifecycle/tests/SEAL_COMMIT` — overwrite with amendment SHA.
5. `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — append
   amendment #20 narrative block.

## 6. Test-suite counts

| Suite | Before | After |
|-------|--------|-------|
| self-correction | 77 | 82 (+5) |
| graceful-degradation | 101 | 104 (+3) |
| observability-aggregator | 62 | 64 (+2) |
| hands-off-lifecycle | 66 | 66 (0) |

The 6 untouched sealed components (cost-governance, memory-system,
reversibility-primitive, telegram-interface, workspace-bootstrap,
orchestrator, safety-layer, primary-persona) — seal-diff tests only
per the amendment-dispatch speedup CDC. Their BASELINEs are frozen.

Note: `safety-layer/tests/test_no_sealed_amendments.py` can show a
pre-existing `ModuleNotFoundError: primary_persona` in some envs — not
this amendment's bug.

## 7. Commit messages

**Amendment commit:**
```
fix(self-correction, graceful-degradation, observability-aggregator, hands-off-lifecycle): S2 silent-except bundle — surface 10 AC:none violations (amendment #20)

[per-site bullets — same shape as amendment #19]
```

**Seal commit:**
```
chore(seals): s2-silent-excepts seal — self-correction + graceful-degradation + observability-aggregator + hands-off-lifecycle at <amendment-sha>
```

## 8. Halt triggers

- Research reveals an AC naming the silent-catch as intentional — halt.
- A fix requires changing a method's public exception-raising contract
  — halt.
- A fix requires touching a 5th sealed component — halt.
- Test break outside the 4 touched components — halt.

All four cleared at research time (research doc §4).

## 9. ODD compliance check

For each fix, point at the AC it satisfies:
- All 10 fixes map to the `audit-triage-by-severity` CDC's bucket (d)
  — outright silent-except violations in live operational paths are
  fixed outright per ODD §8 rule 8. The fix surface (OTel span or
  span-event) is the observable surface that re-extends the system
  behaviour up with an observable branch.
- No site introduces code for an AC the objectives do not name. Each
  emit is the minimal observable surface that the classifier's named
  concern implies.
- No site changes a public exception-raising contract; no site adds a
  record field; no existing caller breaks.
