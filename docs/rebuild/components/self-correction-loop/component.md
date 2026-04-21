# Component — Self-Correction Loop

**Created:** 2026-04-20 10:50 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-20 12:21 CDT.** Commit `65acb97` on `pos-v2`; 77/77 self-correction tests passing; zero sealed-component deltas; all ten sealed-component regression suites green (737 tests total). 16 min wall-clock (well under 28–35 band). **Phase 3 closed on this seal — the Foundational layer is complete.**

---

## Parent objective (from spec v1.0 Foundational layer)

> **Self-correction.** When the system detects its own error — via failed-scope signal, OTel anomaly, verdict from a review scope, or user correction — it opens a correction scope that (a) identifies the failure class, (b) fixes the specific instance, (c) diagnoses the systemic cause, (d) applies a structural remedy that closes the class. The correction loop honours safety, reversibility, and cost ceilings — a retry that would blow the session cap is refused by cost governance; a correction scope that would commit an irreversible action without a compensation path is refused by reversibility.
>
> Acceptance:
> - Detection surfaces produce typed correction-trigger events (failed scope, anomaly, verdict, user correction).
> - On each trigger, the loop opens a correction scope following the four-part structural-remedy contract.
> - Correction scopes compose with safety, reversibility, and cost gates; no bypass paths exist.
> - Correction activity is OTel-visible as first-class spans with the trigger source and the remedy applied.
> - A cascading correction failure (correction of correction of correction) is bounded — the loop detects recursion depth and escalates to the user.

## Why this component is next (and final) in Phase 3

1. **It depends on all three prior Phase 3 components.** Safety's ask-gate is how corrections that touch user approvals compose; reversibility's compensation path is how a correction unwinds prior wrong work; cost governance's ceilings are what prevent runaway correction loops from burning budget.
2. **Phase 3 closes on it.** After self-correction ships, the Foundational layer's "autonomous but governed" promise is complete. Remaining work moves into Phase 4 and beyond (user-facing layer, onboarding, domain workspaces).
3. **The four-part structural-remedy protocol is already the primary-persona's operating rule.** This component is what structurally enforces it rather than leaving it as advisory prose in `prime.md`.
4. **Sidecar/wrap precedent is now quadruply established** — safety, reversibility, cost-governance, plus objective-tracker. Self-correction emulates without ceremony.

## Artifacts

- `research-plan.md` — drafted 2026-04-20; awaiting owner's approval
- `research.md` — produced 2026-04-20 11:06; ruling recorded on 4 questions 11:16
- `proposal.md` — drafted 2026-04-20 11:17; approved 11:23 ("approve")
- `brief.md` — drafted 2026-04-20 11:24; approved 11:32 ("approve")
- `outputs/` — empty

## History

- 2026-04-20 10:50 CDT — component created (fourth and final Phase 3 component, follows sealed safety / reversibility / cost-governance); research plan drafted; awaiting owner's approval before research begins.
- 2026-04-20 10:59 CDT — owner approved plan ("approve"). Background research agent dispatched with explicit "no new activation wrap" rule, seal-test pattern (pin to own-seal) mandatory, and five precedents cited (objective-tracker sidecar, safety's structural-impossibility, reversibility FSM, cost-governance pyee multi-source, observability aggregator query surface).
- 2026-04-20 11:06 CDT — research agent returned after ~7 min wall-clock. **Sidecar-only (no-wrap) pattern HELD throughout** — self-correction is the first pure consumer of the gate chain, not a gate on it. One halt signal surfaced and resolved in-doc: review-scopes as a first-class scope-of-work concept do not exist (only `SelfReviewVerdict` in primary-persona/authoring.py); researcher's alternative makes trigger #3 an IPC call (`correction.report_review_verdict`) that any reviewer can invoke — needs ruling recorded to accept or defer trigger #3 to Phase 4. Minor factual tidy: the composition is a three-wrap chain (safety + reversibility + cost) over `orig_activate`, not four wraps. Calibrated build: 28–35 min wall-clock, anchor ~32 min (under plan's 40-min red-line). Four proposal-stage rulings surfaced.
- 2026-04-20 11:16 CDT — ruling recorded on all four questions ("approve"). (1) Review-verdict trigger: IPC convention. (2) OTel-anomaly: simplest first (`status==ERROR` AND `retention_class==high`); defer P99. (3) Budget scale 0.5 with floors 60s / 2000 tokens. (4) `correction.user_reported` IPC scoped to primary-persona callers only for v1.
- 2026-04-20 11:17 CDT — proposal drafted at `proposal.md`. Encodes rulings as locked inputs, enumerates 24 ODD acceptance criteria (CR1–CR24), flags 8 primary-persona inferences for the builder to challenge, locks no-new-wrap + `-32070..-32079` error-code range + seal-test-pattern-mandatory. Awaiting owner's approval.
- 2026-04-20 11:23 CDT — owner approved proposal ("approve").
- 2026-04-20 11:24 CDT — handoff brief drafted at `brief.md`. Points builder at proposal as authoritative; verify-against-code discipline names four surfaces; gate-refusal exclusion prefixes flagged as primary-persona inference to verify against actual gate sources; seal-test pattern mandatory (baseline `04951b6`, never `..HEAD`); halt-at-40-min with two named scope-creep classes (anomaly P99 detection, in-component intent parsing). Awaiting owner's review before dispatch.
- 2026-04-20 11:32 CDT — owner approved brief ("approve"). Background build agent dispatched against the brief with the proposal as binding contract.
- 2026-04-20 11:53 CDT — Agent returned after ~16 min wall-clock (well under 28–35 band). Commit `65acb97` on `pos-v2`: single cohesive commit, 37 files, all within `self-correction/` (plus pre-existing `data/observability/spans.jsonl` as runtime test output). 77/77 tests passing in 1.49s. Three builder judgement calls: (1) primary-persona inference #1 remapped — my ruling #2's `retention_class="high"` doesn't exist; actual enum is `NORMAL|DERIVED_ONLY|EPHEMERAL`; builder mapped to `NORMAL` preserving intent recorded ("full-fidelity ERROR spans worth investigating"). (2) Gate-refusal exclusion regex kept as defensive-only after verifying gate refusals never emit `StateTransitioned(failed)`. (3) SEAL_COMMIT sidecar-file pattern (`tests/SEAL_COMMIT` written at seal time) — cleaner than reversibility/cost's hardcoded constant, avoids post-seal test amendment round-trip. Zero halt signals.
- 2026-04-20 12:21 CDT — owner sealed ("seal"). **Phase 3 closed** — four components (safety, reversibility, cost-governance, self-correction) all sealed; Foundational layer autonomous-but-governed promise complete. Ten sealed components on `pos-v2` total.
