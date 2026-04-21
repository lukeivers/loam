# Research Plan — Foundation Audit

**Component:** Foundation Audit — an end-to-end verification of the rebuilt pOS on `pos-v2` against the initial objectives spec (v1.0 + v1.1 + v1.2), every sub-objective generated since (component-level acceptance criteria + lifecycle rulings), and the accumulated BACKLOG. Output is a gap report classifying every promise as delivered, deviated, or missing.
**Status:** DRAFT — awaiting owner's approval before research begins.

**Phase 4 second component (post-migration-bypass).**

---

## Objective this research must serve

Produce a single comprehensive gap report that, for every objective authored across the entire pOS-v2 lifecycle, states whether the promise was delivered, deviated from, or missed — cross-referenced to the actual source, tests, and/or BACKLOG entries where each lives. The report must be usable by the owner as a direct disposition surface: each gap gets a fix / defer / accept decision in the proposal stage.

The research does not fix anything. It audits. No code is authored; no commits are made. Every finding is observation + citation.

## Starting position

- **Twelve sealed components on `pos-v2`** at commit `aab5800`: memory-system, scope-of-work, primary-persona, objective-tracker, orchestrator, graceful-degradation, observability-aggregator, self-upgrade, safety-layer, reversibility-primitive, cost-governance, self-correction, workspace-bootstrap. 794 tests green across all.
- **Initial objectives spec** at `docs/rebuild/spec/pos-v2-objectives-spec.md` — v1.0 Foundational layer + v1.1 R1–R13 memory addendum + v1.2 R14–R16 primary-persona addendum.
- **Per-component artifacts** at `docs/rebuild/components/<name>/`: each carries research-plan.md, research.md, proposal.md, brief.md, component.md (lifecycle history). Every component's acceptance criteria are enumerated in the proposal.
- **Accumulated BACKLOG** at `docs/rebuild/BACKLOG.md`: follow-ons deferred during builds. Each entry has a trigger condition.
- **Governing STATE** at `docs/rebuild/STATE.md`: component state machine, governing rules, current phase posture.
- **pOS-v2 workspace** at `pos-v2/`: the actual source tree to audit.

## Questions the research must answer

### 1. Spec v1.0 coverage

1. For every clause in spec v1.0's Foundational layer, where does the delivering component live on `pos-v2`? Cite source file(s) + test(s). Classify: GREEN (delivered + tested + matches spec), YELLOW (delivered + tested, minor deviation noted), RED (not delivered, not tested, or doesn't match).
2. For every acceptance criterion in spec v1.0 (every "Acceptance:" bullet), find the test that proves it. If no test exists, classify RED.
3. Are there spec clauses that appear in no component's acceptance criteria? (Promises made in the spec that nobody claimed to deliver.)

### 2. Spec v1.1 + v1.2 addendum coverage

4. For each of R1–R13 (v1.1 memory addendum), cite delivery + test. Particular attention to R1 (semantic round-trip upgrade acceptance), R11 (OpenTelemetry emission), R12 (per-prompt cost aggregation), R13 (channel-agnostic interaction).
5. For each of R14–R16 (v1.2 primary-persona addendum), cite delivery + test. Particular attention to R14 (autonomous persona authoring), R15 (mandatory user-introduction before first persona message), R16 (framework-not-content).
6. Are the addenda internally consistent with each other and with v1.0? Any case where one ruling contradicts another?

### 3. Component-level acceptance criteria coverage

For each of the twelve sealed components, enumerate every acceptance criterion from its proposal and verify against the actual source + tests:

7. **memory-system** — R1–R13 (inherited from v1.1).
8. **scope-of-work** — proposal's acceptance criteria; any D0 amendment handling.
9. **primary-persona-layer** — D1–D7 + R14–R16 (inherited from v1.2).
10. **objective-tracker** — proposal's criteria.
11. **session-resilient-orchestrator** — proposal's criteria, including the `~/.pos/bootstrap.py` loader contract.
12. **graceful-degradation** — proposal's criteria, memory detection blind-spot disposition.
13. **observability-aggregator** — proposal's criteria, A1 correction (tracer-get pattern).
14. **self-upgrade-framework** — D1–D10 + clauses (a)–(g), including the clause-(g) no-silent-skip structural defence.
15. **safety-layer** — A1–A20, including the A20 safety-beats-degradation re-extension.
16. **reversibility-primitive** — R1–R26, compensation-path contract + rollback FSM.
17. **cost-governance** — C1–C28, ceiling enforcement + throttle + rollups + retention.
18. **self-correction-loop** — CR1–CR24, four-part structural enforcement + recursion bounds.
19. **workspace-bootstrap** — B1–B24, extension protocol + foundational-adapter bundle + B18 acid test.

### 4. Rulings made during lifecycles

20. Every component's `component.md` history carries rulings the owner made during the cycle (e.g. safety-layer's five rulings, reversibility's four, cost's three, self-correction's four, bootstrap's five). For each ruling, verify the rule was actually implemented — not just captured in prose but reflected in code + tests.
21. Particular attention to rulings that set foundational patterns (no-new-wrap for self-correction; innermost-cost for cost-governance; IPC-convention for review-verdict triggers; fail-closed on channel absence).

### 5. BACKLOG subsumption

22. For each BACKLOG entry, is it a real gap, a stale entry, or a deliberate deferral? Classify each:
    - **Still valid deferral** — trigger hasn't arrived; keep.
    - **Stale / resolved** — the condition has changed; retire.
    - **Gap surfaced** — should be a fix-item in this audit's proposal.
23. Are there gaps the audit finds that BACKLOG doesn't contain? (Things nobody tracked during the build.)

### 6. Cross-component integration verification

24. Does the three-gate chain actually compose in production-shape code when bootstrap runs? (Not just in the sealed integration tests, but as a runtime behaviour the audit can verify by reading bootstrap's adapters and tracing through.)
25. Does the extension protocol's B18 acid test pattern hold for a hypothetical onboarding / dashboard component? (Read the protocol, author a thought-experiment contribution, verify the protocol accepts it without bootstrap amendment.)
26. Do the sealed components' emitter-subscribed consumers (cost, reversibility, self-correction) cleanly handle each other's events, or are there event-cascade edge cases?

### 7. Code-quality and discipline audit (not just "does it work")

27. Do any components import from sealed modules' internals (`_private`, monkeypatch, reach into non-public surfaces)? This is the structural-violation class safety's `test_no_sealed_amendments.py::test_A15_no_monkeypatching_of_sealed_modules` catches within safety — audit extends it cross-component.
28. Do the `test_no_sealed_amendments.py` files in each component use the correct SEAL_COMMIT pattern (sidecar-file, not inline-constant-plus-HEAD-fallback-that-breaks)? The retrofit on `aab5800` populated self-correction + workspace-bootstrap; what about reversibility + cost-governance (which use the `f94d602` inline-constant pattern)?
29. Is OTel emission uniform across components? Tracer-get pattern (A1 correction) held everywhere, or are any components constructing their own TracerProvider?
30. Seal-time audit tests green across the entire tree? (The 794 test count is a claim, not a verification — the audit re-runs and cites the count.)

### 8. Gap classification + disposition framing

31. For every GREEN finding, one line of citation (source + test). No elaboration.
32. For every YELLOW finding, description of the deviation + why it's acceptable (or, if it isn't, mark RED).
33. For every RED finding, description of the gap + suggested disposition: fix-small (one-commit tidy), fix-large (new component cycle), defer-with-trigger (back to BACKLOG), accept-with-rationale.
34. Summary counts: GREEN / YELLOW / RED per component + across the whole. Aggregate.

## Constraints the research must respect

- **Read-only.** No code changes, no test changes, no BACKLOG rewrites during research. Every finding is observation + citation. The proposal stage disposes; the build stage fixes.
- **Cite everything.** Every claim backed by a file path and line range or a test name. No "I believe X" — "the test at `<path>::test_name` asserts X; I reviewed it and agree."
- **Verify by reading, not by trusting documents.** If a component's proposal claims an acceptance criterion is satisfied and the audit finds no matching test, classify RED regardless of what the proposal says.
- **Do not propose new objectives.** The audit measures against existing objectives; it does not invent new ones to check against.
- **Thorough is the primary constraint; speed is secondary.** The audit's value is in its comprehensiveness. Budget accordingly.
- **Halt-on-deviation still applies** — if a constraint in this plan cannot be honoured, surface it rather than improvise.
- **A1 correction held for the audit itself** — if any audit-produced artifact emits OTel (unlikely; mostly a markdown report), use the tracer-get pattern.

## Deliverable — what the research document must contain

A single comprehensive markdown document at `components/foundation-audit/research.md` with:

1. **Executive summary** — one page. Counts of GREEN/YELLOW/RED per component. Top-10 most-significant findings across the tree. Overall posture assessment.
2. **Spec v1.0 coverage matrix** — clause by clause, with destination component + test + classification.
3. **Spec v1.1 + v1.2 addendum coverage** — R1–R16, with same matrix shape.
4. **Per-component acceptance-criteria audit** — one subsection per sealed component; every acceptance criterion enumerated with source/test citation + classification.
5. **Rulings audit** — every lifecycle ruling verified against implementation.
6. **BACKLOG subsumption** — every BACKLOG entry classified still-valid / stale / gap-surfaced.
7. **Cross-component integration findings** — three-gate chain runtime composition, extension protocol acid-test extensibility, event-cascade behaviour between emitter-subscribed consumers.
8. **Code-quality findings** — monkeypatch/import-internal audit, SEAL_COMMIT pattern uniformity, OTel emission uniformity.
9. **Gap disposition table** — every RED or YELLOW finding with recommended disposition (fix-small / fix-large / defer-with-trigger / accept-with-rationale).
10. **Residual BACKLOG** — the proposed replacement for current `BACKLOG.md` after the audit's findings land: still-valid entries + new entries from gap-surfaced findings.
11. **Limitations and open questions** — any objective the audit could not verify (e.g. clause-(g) self-upgrade clause that requires running a live upgrade to verify); any place where the verifier's judgement is fallible.

## Complexity estimate

Substantial, deliberately. This audit's value is thoroughness.

- **Anchor components read-heavy rather than write-heavy** — no prior component is quite analogous. Closest reference point: the cost-governance research (~10 min wall-clock) was mostly reading across three sealed components + one spec doc + one research plan. This audit reads across twelve sealed components + three spec versions + twelve research docs + twelve proposals + twelve briefs + BACKLOG + STATE.
- **Input volume** is roughly 30–50× a single component's research.
- **Output volume** is one comprehensive report, estimated 1500–3000 lines.
- **Calibrated estimate: 60–90 AI-min wall-clock; red-line 120.** Well above any prior research; reflects the scope honestly.
- **If the agent exceeds 120 min or signals it can't complete thoroughly**, halt and signal — the audit is either (a) too ambitious for one pass and should be decomposed by component, or (b) the agent hit a specific verification blocker worth surfacing.

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent with a large working context. The agent's deliverable is the gap report only; the agent does not make commits or modify source. The proposal stage (after agent return) is where the owner dispositions each gap; the build stage is where fixes land.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
