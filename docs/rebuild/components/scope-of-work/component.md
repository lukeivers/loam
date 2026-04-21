# Component — Scope-of-Work Primitive

**Created:** 2026-04-18 12:09 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-18 14:27 CDT** (+ D0 amendment landed 2026-04-18 ~17:44 CDT as part of primary-persona layer build). D1–D8 shipped on `pos-v2`; 63 original tests green; memory's `MockScopeSource` retired. D0 amendment added `expected_duration_seconds: float | None = None` to `ScopeSpec` plus `is_stuck` trigger for the monitor's stuck-detection — commit `abe9863`, 14 new tests green (77 total on scope-of-work), zero regressions.

---

## Parent objective (from spec v1.0)

> *Autonomous scope of work:* goal, constraints, budget (time/tokens/money), reversibility class, success criteria, observers, escalation triggers.

Full acceptance criteria at behaviour level — see objectives spec v1.0, "Core primitives" section:
- Every scope declares all seven fields at creation; missing any field rejects scope creation.

v1.1 revisions that touch this primitive indirectly: R11 (OTel observability — scopes emit their lifecycle events), R12 (per-prompt cost attribution — scope budgets reference this).

## Why this component is next

1. **Foundational dependency for every downstream component.** Scope-of-work is the unit of things pOS does. Every other component (primary persona, objective tracker, observability consumer, cost governance, safety layer, reversibility primitive) references it.
2. **Memory's `MockScopeSource` retires when this lands.** The first soft-dependency mock goes away the moment scope-of-work is real.
3. **Objective tracker and primary persona loader both require scope semantics.** Before designing either, we need the shape of scope.

## Artifacts

- `research-plan.md` — drafted 2026-04-18; awaiting owner's approval
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-18 12:09 CDT — component created; research plan drafted; awaiting owner's approval before research begins.
- 2026-04-18 12:14 CDT — owner flagged current-pOS leaks in the plan (references to "orchestrator" and "event log" as named future-component labels). Revised: Starting-position section, budget-enforcement question (Q6), persistence question (Q11), and deliverable dependency-map section all now use objective-level terms (session-resilience, observability consumption, cost governance, safety layer) instead of current-pOS implementation names.
- 2026-04-18 12:33 CDT — owner clarified: "orchestrator" and "event log" are legitimate names for new-pOS components, not current-pOS leaks. Guardrail revised: the concern is not the words but importing structural assumptions (JSONL file shape, specific API, bin/orch conventions) from the current pOS implementation before the new-pOS structure is designed. Research plan stays in its generic-language form (no churn since the owner has read it); rebuild proposal can continue using those names as phase labels. Research plan approved ("move forward"); general-purpose Agent dispatched.
- 2026-04-18 ~12:41 CDT — Agent returned after ~8 minutes of research. No halts. Recommended design shape: event-sourced FSM (`proposed → active → {paused → active}* → {completed | failed | cancelled | escalated}`), strict-tree hierarchy with Temporal-style parent-close policies, SQLite WAL as persistence (stdlib sqlite3), three-axis budget (time/tokens/money) with per-LLM-call debit, pyee AsyncIOEventEmitter + Pydantic discriminated-union trigger predicates, OTel-native with GenAI semantic conventions. Every spec criterion satisfiable; two criteria noted as partially out-of-primitive-scope (reversible-preference selection, four-part correction class-closure) because those are policy decisions belonging to the future safety/correction layer — the primitive surfaces the fields/triggers, consistent with A1. Memory-mock retirement path: 10-line adapter + one wiring line + one integration test; no memory-side rewrite. Complexity estimate: 265–440 AI-minutes for the full build.
- 2026-04-18 13:13 CDT — owner approved research recommendations including pyee ("move forward. keep me updated as you go").
- 2026-04-18 13:18 CDT — Proposal drafted at `proposal.md`. Eight deliverables (D1 core primitive + D2 budget ledger + D3 observers/triggers + D4 hierarchy + D5 OTel emission + D6 memory-mock retirement + D7 upgrade-fidelity harness + D8 bundled docs). Three open questions for the owner: prototype-first or fold-in, default exhaustion policy, default parent-close policy. Awaiting ruling recorded.
- 2026-04-18 13:34 CDT — owner asked for the three questions to be restated plainly (terminology-heavy phrasing too jargon-y); the primary persona re-posed with concrete real-world scenarios and plain language.
- 2026-04-18 13:39 CDT — owner answered: (1) fold-in, (2) **request-extension** as the default exhaustion policy across all three axes (overriding recommendation of halt-and-signal), (3) TERMINATE as default parent-close. Proposal updated to reflect; one consequence noted — the primitive needs a user-notification channel for extension requests, and default timeout is indefinite pending response recorded (ADHD-friendly silence-by-choice posture).
- 2026-04-18 13:42 CDT — Handoff brief drafted at `brief.md`. Covers D1–D8; hard constraints name the three the owner decisions explicitly; three the primary persona inferences flagged at the bottom (default extension timeout, extension-request surfacing channels, synthetic test fixtures reusing the Aldermere world). Awaiting owner's review before dispatch.
- 2026-04-18 13:51 CDT — the owner surfaced a cross-component principle: *the primary persona must never lose track of background work* — every dispatch must be monitor-visible. Captured as STATE.md rule #7, rebuild-proposal Phase 1 addition (background-work monitor alongside persona loader), and primary persona's memory. Scope-of-work brief's D1 extended with one bullet making the query surface's monitor-feeder role explicit; no structural changes to D1–D8 needed, because the API and emission surface already support it.
- 2026-04-18 13:57 CDT — owner approved brief ("approve to dispatch"). General-purpose Agent dispatched for the full D1–D8 build.
- 2026-04-18 ~14:23 CDT — Agent returned after ~25 minutes. All D1–D8 complete, no halts, 63 scope-of-work tests passing + 6 memory regressions green. Three commits on `pos-v2`: `8c7bd31` (D1–D5 core), `98422fd` (D1–D7 acceptance suite), `485ebc0` (D8 docs + retire memory mock). Memory's `MockScopeSource` retired via `RealScopeSourceAdapter`. the owner's three decisions (request-extension default, TERMINATE parent-close, fold-in design priorities) all honoured. Two mid-build judgment calls flagged for ruling recorded: (a) pytest + pytest-asyncio added as test-only infrastructure without halting (argued test-infra ≠ runtime-deps); (b) several src files exceed the workspace-global 200-line rule from the current-pOS CLAUDE.md, agent extracted four modules (898→~700 lines) and documented the residual as a cohesion tradeoff in `docs/file-size-note.md`.
