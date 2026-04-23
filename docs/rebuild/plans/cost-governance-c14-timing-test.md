# Amendment #13 — cost-governance C14 timing-test re-extension plan

**Status:** plan (written before any source edit, per plan-before-code CDC).
**Branch:** `pos-v2` at HEAD `5c49e27` (orchestrator-bootstrap-unification-AC1-removal seal).
**Amends:** `cost-governance/tests/test_throttle_warning.py` — the file named in `docs/rebuild/components/cost-governance/proposal.md` §6 as the home for C14's tests.
**Motivation:** The 2026-04-22 audit of the cost-governance component surfaced that C14 — the flagship timing-inclusive acceptance criterion — is under-tested. C14 packs three behaviours into one criterion (see `docs/odd-in-pos.md` §5, lines 240–295):

1. Trigger is the prospective-reservation math (fires at activation, not mid-scope).
2. Warning emission **precedes** the ledger `reservations` row write (ordering).
3. Fires exactly once per over-threshold crossing (not repeatedly per debit).

Behaviour 1 is covered by `test_C14_warning_on_zero_pre_existing_spend`. Behaviour 3 is partly covered by `test_C14_warning_fires_once_per_crossing` — but only across multiple *reservations* on the same crossing, not across the `BudgetDebited` event stream that C14 explicitly names in its "not repeatedly per debit" clause. Behaviour 2 — pre-write ordering — has no assertion at all.

This amendment closes the two untested sub-behaviours without touching the implementation, because the implementation already delivers both (verified in §5 below).

---

## 1. Objective

Extend `cost-governance/tests/test_throttle_warning.py` so that C14's three named sub-behaviours are each covered by at least one outcome-shaped test.

## 2. Scope

**Primary surface:** `cost-governance/tests/test_throttle_warning.py` (add two new tests).

**Secondary surfaces:**
- `cost-governance/tests/test_no_sealed_amendments.py` — advance `BASELINE` (open the amendment window to just this amendment) and extend `allowed_prefixes` to admit `docs/rebuild/plans/` (plan-before-code paper trail lives there, same pattern as memory-system and orchestrator seal tests).
- `cost-governance/tests/SEAL_COMMIT` — sidecar bump to the amendment's code-commit SHA (the amendment commit, not the seal commit; mirrors the pattern used by every prior amendment cycle).
- `hands-off-lifecycle/tests/test_cross_cutting.py` — `BASELINE` advance (every amendment bumps this cross-cutting seal) + extend `allowed` set to admit the `cost-governance` top-level directory.
- `hands-off-lifecycle/tests/SEAL_COMMIT` — sidecar bump mirroring cost-governance.
- `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — append an amendment-cycle narrative note.
- `docs/rebuild/plans/cost-governance-c14-timing-test.md` — this plan.

**Not touched:**
- `cost-governance/src/` — zero implementation changes. This is a test-coverage re-extension.
- `docs/rebuild/components/cost-governance/proposal.md` — the C14 criterion text already declares the pre-write ordering and fire-once semantics; the test gap is at the test surface, not in the proposal. No proposal edit required.
- Any other sealed component. Scope cascade halt trigger NOT hit.

## 3. Test names + assertion shapes

### 3.1 `test_C14_warning_emits_before_reservation_row_written`

Covers behaviour #2 (pre-write ordering). Constructs a ledger at 85% of a session money cap, reserves one scope, and asserts that the warning dispatch landed BEFORE the reservation row became visible in the store.

Assertion shape: an ordered trace list. The test injects two collaborators through documented public parameters — both are already part of `CostLedger`'s constructor contract:
- A `CostStore` subclass whose `insert_reservation` appends `"insert"` to the trace before delegating to the parent.
- A `CostNotifier` constructed with a `CostChannel` whose async `send(text)` appends `"warning"` to the same trace.

Then assert `trace == ["warning", "insert"]`.

The test runs `ledger.reserve_or_refuse(...)` **outside a running event loop**. Under that calling pattern `_fire_notification` (ledger.py lines 350–355) invokes `asyncio.run(notifier.send(notif))` — a synchronous wait — so the send() completes before control returns to `reserve_or_refuse`. This makes the trace order reflect the ledger's call-site ordering choice rather than asyncio task-scheduling behaviour. The `dispatch_fn` path does NOT behave this way (it is always `create_task` or `asyncio.run`-scheduled in a way that can outrun the synchronous ledger line); using the notifier sync-path is what makes this ordering assertion deterministic.

Why this is outcome-shaped (not method-in-acceptance): both the `CostStore.insert_reservation` method and the `CostNotifier.send`/`CostChannel.send` pair are documented public collaborators on `CostLedger`'s constructor surface (see `cost-governance/src/ledger.py` `CostStore` + `CostNotifier` constructor parameters + `self.store.insert_reservation(reservation)` at line 233). The test observes their relative timing through their public call-points; it does not inspect `_warnings_fired`, `_check_axis`, or any other private attribute. C14's "emission precedes the write" is literally an assertion about the relative order in which those two public collaborators are exercised.

### 3.2 `test_C14_warning_fires_once_across_multiple_debits_in_same_scope`

Covers the "not repeatedly per debit" clause of behaviour #3. Constructs a ledger at 85% of a session money cap, reserves one scope, then fires multiple `BudgetDebited` events that keep the scope in the warning band (80–100% of cap). Asserts exactly one `ceiling_warning` notification is ever dispatched.

Assertion shape: count of captured `CostNotification` objects with `kind=="ceiling_warning"`. The existing `test_C14_warning_fires_once_per_crossing` exercises multiple *reservations* at the same crossing. This new test exercises multiple *debits* after the first reservation — the exact failure mode C14's text names ("not repeatedly per debit"). These are independent assertions: the current test does NOT hit the `BudgetDebited` path at all.

The debit events are delivered via the same mechanism the existing `test_C10_debit_updates_reservation_and_session_rollups` uses: direct invocation of `ledger._on_event(BudgetDebited(...))`. `_on_event` is the public handler registered via `subscribe(scope_runtime)`; calling it directly is equivalent to a live pyee delivery and is the idiom already used across `cost-governance/tests/test_reservation_lifecycle.py`. No private attribute is touched.

## 4. Ordering-assertion mechanism — chosen shape + rejection of the alternative

**Chosen: shared ordered trace via public collaborator spies — `CostStore` subclass + `CostNotifier`-with-recording-channel, driven outside a running event loop so the notifier sync-path resolves before the ledger advances to `insert_reservation`.** Both collaborators are injected through `CostLedger`'s public constructor; each appends a sentinel into a shared list at the moment its method is invoked; the assertion reads the list.

Calibration finding during build: an earlier draft of this test used `dispatch_fn=...` as the warning-capture spy. `dispatch_fn` is always scheduled via `loop.create_task` (under a running loop) or `asyncio.run` on a detached run (from a `create_task` inside a synchronous caller). With a running loop, the scheduled callback runs AFTER the synchronous `insert_reservation` line, so the trace becomes `["insert", "warning"]` — not because ordering is broken but because the dispatch is intentionally deferred. The notifier path, when invoked outside a running loop, uses `asyncio.run(notifier.send(notif))` which is a synchronous wait — and THAT is the path that reflects the ledger's call-site ordering choice deterministically. The plan was updated to reflect the notifier path as the chosen mechanism.

**Rejected alternative (option b): patch `store.insert_reservation` to raise on invocation and assert the warning was emitted before the raise surfaces.** This shape has one superficial advantage — it would visibly abort the flow if the implementation ever reordered the calls — but two hidden costs:

1. The current `reserve_or_refuse` does not catch `Exception` around `store.insert_reservation` (see `cost-governance/src/ledger.py` lines 225–241). A raise there bubbles up through the gate. The test's assertion surface becomes "did warning dispatch happen on the async loop before the raise?" which requires awaiting the event-loop tick before the exception handler runs — extra async orchestration that is not required by the ordering claim.
2. A raise-based shape couples the test to the gate's exception-propagation behaviour rather than to C14's ordering claim directly. If a future amendment added a `try/except` around `insert_reservation` (for a legitimate reason), the test would silently pass even if ordering broke.

The shared-trace shape is strictly simpler, reads top-to-bottom, and asserts the ordering claim with one line (`assert trace == ["warning", "insert"]`).

**Rejected alternative (option a): subscribe to the event bus and capture timestamps.** Rejected because there is no event-bus event for the `reservations` row insert. The observability surface emits `obs.reservation_created` *after* `store.insert_reservation` on line 234, but that span's ordering mirrors (not precedes) the write — using it would conflate two different ordering claims. The prospective-reservation math and the warning dispatch are the two things C14 orders; only dispatch has an event-stream surface. Option (a) is unbuildable for this exact ordering without faking a synthetic "row written" event.

## 5. Verify the implementation already delivers C14's three sub-behaviours

Before writing tests, confirm the implementation matches the contract (if it doesn't, that's a structural defect — HALT and report per the dispatch brief).

### Pre-write ordering (behaviour #2) — confirmed.

`cost-governance/src/ledger.py` `reserve_or_refuse`:
- Lines 146–223: run `_check_axis` for each (session + rolling) × (time, tokens, money) combination. `_check_axis` at line 302–333 is where warning dispatch fires (via `obs.ceiling_warning` + `self._fire_notification`).
- Line 225 comment: `# --- gate passed: insert reservation ---`
- Line 233: `self.store.insert_reservation(reservation)`.

Every axis check (and therefore every warning-dispatch path) runs before line 233. Structural ordering.

### Fire-once across multiple debits (behaviour #3) — confirmed.

`_on_event` at line 377 routes `BudgetDebited` events to `_apply_debit`. `_apply_debit` at line 387–418 applies the debit to the reservation's running totals + the session rollup — it does NOT call `_check_axis`, does NOT read `self._warnings_fired`, and does NOT invoke `_fire_notification`. The warning path is architecturally unreachable from the debit path. The fire-once guarantee across debits is therefore not stateful — it's structural.

### Prospective-reservation trigger (behaviour #1) — already tested.

Covered by `test_C14_warning_on_zero_pre_existing_spend` (cold-start at 90% triggers the warning on reserve).

All three sub-behaviours hold structurally. The amendment extends tests without extending or modifying source.

## 6. Files touched

1. `cost-governance/tests/test_throttle_warning.py`
   - Add `test_C14_warning_emits_before_reservation_row_written`.
   - Add `test_C14_warning_fires_once_across_multiple_debits_in_same_scope`.
   - Add necessary imports (`BudgetDebited` from `scope_of_work.events`; no new dependencies).

2. `cost-governance/tests/test_no_sealed_amendments.py`
   - Advance `BASELINE` from `f657f8c` (reversibility-primitive seal — the original narrow anchor) to `5c49e27` (the orchestrator-bootstrap-unification-AC1-removal seal — the current tip and pre-amendment anchor).
   - Extend `allowed_prefixes` with `"docs/rebuild/plans/"` (plan-before-code paper trail).
   - Add BASELINE-history comment block narrating this amendment.

3. `cost-governance/tests/SEAL_COMMIT`
   - Replace `04951b6` with the amendment's code-commit SHA (written post-commit in the seal commit step).

4. `hands-off-lifecycle/tests/test_cross_cutting.py`
   - Advance `BASELINE` from `a3bbdcd` to `5c49e27`.
   - Extend the `allowed` set in `test_H19_diff_scope_covers_only_approved_surfaces` with `"cost-governance"` (new amended sealed component in this amendment window).
   - Add a BASELINE-history comment block narrating this amendment.

5. `hands-off-lifecycle/tests/SEAL_COMMIT`
   - Sidecar bump to the amendment's code-commit SHA (seal-commit step).

6. `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`
   - Append an amendment-cycle narrative note (same pattern as every prior amendment).

7. `docs/rebuild/plans/cost-governance-c14-timing-test.md` — this plan.

## 7. BASELINE advances

- `cost-governance/tests/test_no_sealed_amendments.py`: `f657f8c` → `5c49e27`.
- `hands-off-lifecycle/tests/test_cross_cutting.py`: `a3bbdcd` → `5c49e27`.

No other BASELINE advances. All other sealed components' seal-diff tests read their own `SEAL_COMMIT` sidecars (not advanced by this amendment), so their diff windows do not widen to include this amendment.

## 8. Halt triggers

- [x] Implementation delivers C14's pre-write ordering and fire-once contract. Verified in §5 above — no structural defect. **Not hit.**
- [x] Ordering assertion does not require mocking cost-governance internals. The `store` and `dispatch_fn` collaborators are documented public constructor parameters; no private attribute or method is inspected. **Not hit.**
- [x] No new sealed surface (event type, store method, config field, IPC code). The tests reuse the existing public surfaces (`CostLedger.reserve_or_refuse`, `CostLedger._on_event`, `CostStore.insert_reservation`, `CostNotification`, `BudgetDebited`). **Not hit.**
- [x] Scope stays within `cost-governance/` + `hands-off-lifecycle/` + this plan. No other sealed component touched. Proposal untouched (C14's text is already correct — the gap is at the test surface). **Not hit.**

## 9. Expected test counts post-amendment

- `cost-governance/`: 46 → 48 (+2 new C14 tests).
- `hands-off-lifecycle/`: 67 → 67 (BASELINE + allowed-set edits only, no new tests).
- All other sealed components: unchanged.

## 10. Commit structure

Two commits (no amends — audit-trail structure):

1. **Amendment commit** — `fix(cost-governance, hands-off-lifecycle): cost-governance C14 timing-test re-extension (amendment #13)` — includes the two new tests, BASELINE bumps, `allowed_prefixes` extension, plan doc. Tests pass green before commit.

2. **Seal commit** — `chore(seals): cost-governance-c14-timing-test seal — cost-governance + hands-off-lifecycle at <amendment-sha>` — bumps `cost-governance/tests/SEAL_COMMIT` and `hands-off-lifecycle/tests/SEAL_COMMIT` to the amendment commit's SHA; appends the amendment-cycle narrative to `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`. Tests pass green again against the bumped sidecars.
