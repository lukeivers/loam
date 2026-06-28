# Deploy-safety FLOOR — adopt the shared fail-policy primitive (cleanup micro-cycle)

## 1. Objective

Have the deploy-safety-floor PreToolUse gate
(`framework/deploy-safety-floor/hooks/deploy_safety_floor_guard.py`) adopt
the shared per-gate fail-policy primitive
(`framework/safety-layer/hooks/_fail_policy.py`, sealed in Sub-cycle B at
`828de228`) as its **single source** of fail-closed-on-fault behaviour,
removing the local ad-hoc duplicate. This is the named, owner-gated
follow-up the Sub-cycle B manifest recorded ("having it ADOPT the shared
primitive is a named, owner-gated follow-up — no functionality is lost by
deferring it").

**Strictly behaviour-preserving.** The floor gate must still DENY on a
fault (raise / malformed input) against a destructive candidate under every
permission mode, exactly as today, and still fail OPEN on a non-candidate
fault. This is a refactor, not a behaviour change.

## 2. Scope (one line)

Replace the floor gate's local fail-closed enactment (`_emit_deny` + the
candidate-branch in the fault handler) with the shared
`_fail_policy.apply_fault_policy` / `emit_deny`, declaring
`FAIL_POLICY = FailPolicy.FAIL_CLOSED`; the floor-specific destructive-
candidate classifier (`_floor_should_fail_closed`) is RETAINED — it supplies
the primitive's `is_destructive_candidate` input and is not a duplicate.

## 3. Halt-and-surface (BEFORE / DURING build)

- HALT if the refactor would CHANGE observable fail-closed behaviour in any
  case (not purely behaviour-preserving) — do not ship a behaviour change
  under a cleanup label.
- HALT if the fence touches a sealed component with no manifest entry. (The
  gate now READS safety-layer's `_fail_policy` at runtime — a read, not an
  edit; the manifest declares safety-layer as a read-partner, not a sealed
  edit. No safety-layer source moves.)
- HALT if any AC can only ship partial.
- HALT on an ODD violation in this work or in surrounding sealed code.

## 4. Fence

- Sealed component edited: `framework/deploy-safety-floor/` (existing-component
  extend; prior seal `51761a8`).
- Reads (no edit): `framework/safety-layer/hooks/_fail_policy.py` (sealed
  Sub-cycle B). Runtime import via the documented stdlib-only sibling pattern,
  the same coupling every framework-sibling component already assumes (the
  floor tree and safety-layer tree ship together as one framework unit).
- Universal-admitted partners: `docs/plans/` (plan-doc + manifest),
  `docs/STATE.md` (dispatcher-side §-backfill at close).
- Seal-test BASELINE advances to this cycle's plan-doc commit (house HEAD~1
  pattern) so the diff window carries only this cycle's changes. (Leaving it
  at Sub-cycle A's `f27bbd66` baseline would pull Sub-cycle B's safety-layer
  edits into the window and fail the fence — the advance is required.)

## 5. Acceptance criteria

**AC.DSF.8 — floor gate adopts the shared fail-policy primitive
(behaviour-preserving).**

Outcome shape (method is the builder's call):

1. The floor gate's on-fault decision is **sourced from** the shared
   `_fail_policy` primitive: the module declares
   `FAIL_POLICY = FailPolicy.FAIL_CLOSED` and routes its top-level fault
   handler through `apply_fault_policy(...)`; the local ad-hoc fail-closed
   enactment (`_emit_deny`) is removed (both deny-emit call sites route
   through the primitive's `emit_deny` / `apply_fault_policy`).
2. Observable fail-closed behaviour is **unchanged** — the existing
   Sub-cycle A outcome-altitude test
   (`test_AC_DSF_7_outcome_altitude.py`) still passes unchanged: a real
   destructive command against an unattested prod target still denies; the
   same entry-point on a corrupt-attestations fault still denies
   (fail-closed); a benign read still allows; bypass mode still returns
   deny. The emitted deny envelope is byte-identical (the primitive's
   `deny_payload` is the same shape the local `_emit_deny` wrote).
3. The log audit-label is unchanged: `deny-fail-closed` on a candidate
   fault, `fail-open-non-candidate` on a non-candidate fault (the
   primitive's `FaultDecision.label` is byte-identical to the labels the
   ad-hoc handler wrote).

**No regression:** the deploy-safety-floor suite + the safety-layer suite
stay green.

This cycle adds **no new failure-mode coverage** and **no new gate** — it is
a de-duplication only, so no AC.COV catalogue change.

## 6. Build steps

1. Plan-doc commit (this file) → BASELINE.
2. Edit `deploy_safety_floor_guard.py`: add the sibling import of
   `FailPolicy, apply_fault_policy, emit_deny`; declare
   `FAIL_POLICY = FailPolicy.FAIL_CLOSED`; rewrite the fault handler to call
   `apply_fault_policy(FAIL_POLICY, is_destructive_candidate=_floor_should_fail_closed(...), deny_reason=destructive_fail_closed_message(...))`
   and log `fault.label`; route the normal policy-deny path through the
   primitive's `emit_deny`; delete the local `_emit_deny`; refresh the
   module docstring's fail-policy paragraph to name the adoption.
3. New test `test_AC_DSF_8_fail_policy_adoption.py`: structural (declares
   FAIL_CLOSED; no local `_emit_deny`; binds the primitive's
   `apply_fault_policy`/`emit_deny`) + behavioural parity at the real
   subprocess entry-point (fail-closed deny on corrupt attestations).
4. Bump the floor seal-test BASELINE constant to the plan-doc commit SHA.
5. Run the new test + `test_AC_DSF_7_outcome_altitude.py` + the floor suite
   + the safety-layer suite locally.
6. Commit `feat(deploy-safety-floor): adopt shared fail-policy primitive`.
7. Author manifest; `loam amend validate` → `apply` → `seal`.
8. Backfill STATE / roadmap with apply + seal SHAs.

## 7. Named decisions

- **D1 — keep `_floor_should_fail_closed`.** It classifies a destructive
  candidate (uses `classify_destructive` + `_is_local_config_file`) — that is
  the floor's domain knowledge, supplied as the primitive's
  `is_destructive_candidate` argument. The primitive does NOT subsume it. Only
  the fail-closed *enactment* (emit + branch + label) is the duplicate, and
  only that is removed.
- **D2 — remove `_emit_deny` entirely** (both call sites, fault + normal
  policy-deny, route through the primitive's `emit_deny`). The primitive's
  `deny_payload` is byte-identical to the local envelope, so this fully
  removes the duplicate with zero observable change — the cleaner long-term
  shape over leaving a one-line local wrapper alive.
- **D3 — hard import at module load** (mirrors the existing `_SRC` package
  import the gate already does). If the sibling primitive cannot be imported
  the hook fails to load — the same module-load exposure the gate already has
  for its own `loam.deploy_safety_floor` package; the fail-closed contract has
  always been conditioned on the module loading. The plan accepts this as
  consistent with the existing risk posture rather than wrapping the import in
  a fallback that would re-introduce the duplicate.

## 8. In-flight halt triggers

- WD drift from `/Users/lukeivers/loam`.
- Seal fails for a reason unrelated to these edits (a pre-existing fence
  breach surfaced by the baseline advance).
- Behaviour parity test fails — STOP, do not loosen the test.
