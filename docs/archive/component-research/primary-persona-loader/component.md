# Component — Primary-Persona Layer (Loader + Monitor + Autonomous Authoring)

**Created:** 2026-04-18 14:28 CDT. **Scope expanded:** 2026-04-18 14:37 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-18 18:43 CDT.** All D0–D10 landed on `pos-v2`; 115 new tests green; zero regressions; v1.2 spec addendum landed with three revisions (R14 autonomous authoring, R15 mandatory introduction, R16 framework-not-content).

Scope now covers three tightly-coupled halves, all sharing the persona contract as their common artifact:

1. **Loader + validator.** Contract definition; workspace-persona validation; rejection on non-conformance; build-time check that pOS core ships zero personas.
2. **Background-work monitor.** Subscribes to scope-of-work emission; keeps the primary persona continuously aware; STATE.md rule #7 delivered structurally.
3. **Autonomous authoring.** Primary persona can evaluate when a new persona is warranted, author it from a canonical template using a research paradigm, quality-check the result, and introduce the new persona to the user before any message from that persona lands. (the owner's direction 2026-04-18 14:37 CDT.)

---

## Parent objectives (from spec v1.0 + v1.1)

Two objectives land in this one component, tightly coupled:

**(i) Primary-persona primitive (v1.0 Core primitives):**
> *Primary persona:* a contract defining the trust-and-coordination layer that every workspace must supply. A valid primary persona is the single point of contact between user and system, holds ongoing context across sessions, and judges escalation at the authority boundary. pOS supplies the contract, the loader, and the validation; the workspace supplies the persona.
>
> Acceptance:
> - Contract is formally specified; a workspace persona either conforms or is rejected at load time.
> - No pOS-shipped persona content exists in the core repo — enforced by a build-time check that fails on any persona file in pOS paths.
> - A workspace with no primary persona cannot start a session; failure mode is clear and immediate.

**(ii) Background-work monitor (STATE.md rule #7; rebuild-proposal Phase 1 addition):**
> An interactive session must never lose awareness of active background work and let the system go fallow. The monitor subscribes to scope-of-work's emission and query surface and keeps the primary persona continuously aware of active, stuck, finished, and needs-review work.

## Why these two are one component

They are inseparable at the design level: the persona is the thing the monitor feeds, and the monitor is the mechanism by which the persona maintains continuous awareness. Designing them separately would commit to an interface boundary before we know what the persona needs from the monitor.

## Artifacts

- `research-plan.md` — drafted 2026-04-18; awaiting owner's approval
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-18 14:28 CDT — component created as paired loader + monitor; research plan drafted; awaiting owner's approval before research begins.
- 2026-04-18 14:37 CDT — the owner expanded scope to include autonomous persona-authoring: primary persona can evaluate when a new persona is warranted and author one without user pre-approval if it meaningfully improves output, provided the user is introduced to the new persona BEFORE receiving any message from that persona. pOS core ships no personas but ships the *framework* for authoring them — template, research paradigm, quality-assurance, introduction protocol. Research plan revised with five new question groups (8–12) covering the authoring half.
- 2026-04-18 14:41 CDT — owner approved the expanded research plan ("approved"). General-purpose Agent dispatched.
- 2026-04-18 ~14:50 CDT — Agent returned after ~9 minutes. Research doc at `research.md` (853 lines). Recommended design: directory-based persona layout (`contract.yaml` + `prompt.md`), Pydantic-validated YAML, stateless loader, fail-closed on missing/invalid; long-lived asyncio monitor subscribed to scope-of-work's pyee emitter plus 30-sec stuck-detection tick, injects ~1k-token awareness block every UserPromptSubmit; five-signal deterministic detector → Claude-via-Max authoring pipeline with self-review, max 2 iterations; replay-from-authoritative-sources for compaction survival (clean divergence from current pOS snapshot-restore); introduction protocol gates new persona's `is_addressable` until user's next non-retire message. No spec-criterion halts. Three structural halt signals awaiting the owner: (1) scope-of-work needs an `expected_duration_seconds` field on ScopeSpec for stuck detection; (2) Python Agent SDK lacks PostCompact hook, workaround is flag-and-detect in UserPromptSubmit; (3) introductions on group channels arguably speak to third parties — recommend restricting to one-on-one. Complexity estimate: ~620 AI-minutes (inside 450–700 projection).
- 2026-04-18 17:07 CDT — ruling recorded on all three halt signals: agreed with all three the primary persona leans. Scope-of-work amendment (D0) added to proposal; flag-and-detect compaction workaround accepted; introductions restricted to one-on-one channels.
- 2026-04-18 17:11 CDT — Proposal drafted at `proposal.md`. Eleven deliverables D0–D10: D0 scope-of-work amendment (add `expected_duration_seconds` field), D1 persona contract + template, D2 loader + validator, D3 background-work monitor, D4 compaction survival, D5 creation-trigger detector, D6 autonomous authoring pipeline, D7 introduction protocol, D8 retirement, D9 OTel emission, D10 bundled docs. Three staged v1.2 spec revisions mapped to deliverables. Three minor open questions with the primary persona leans. Awaiting ruling recorded.
- 2026-04-18 17:13 CDT — owner approved ("proposal fine. lets go") with all three open questions going to the primary persona's leans: `expected_duration_seconds` default = None; group-channel introductions strictly forbidden (no edge-case override); retire-window indefinite.
- 2026-04-18 17:16 CDT — Handoff brief drafted at `brief.md`. Covers D0–D10; hard constraints name the owner's five baked-in decisions; three the primary persona inferences flagged (PyYAML permission, zero-channel introduction queueing, creation-trigger threshold defaults). Awaiting owner's review before dispatch.
- 2026-04-18 17:18 CDT — owner approved brief ("lets do it"). General-purpose Agent dispatched for the full D0–D10 build.
- 2026-04-18 ~17:44 CDT — Agent returned after ~26 minutes (substantially under the ~620-minute estimate). All D0–D10 complete. Two commits on `pos-v2`: `abe9863` (D0 scope-of-work amendment) and `e3cb20a` (D1–D10 primary-persona build). 115 new tests green (14 D0 + 101 D1–D10); scope-of-work's 63 pre-existing tests still pass; zero regressions. Three concrete v1.2 spec-revision wording proposals returned — autonomous authoring clause, mandatory-introduction clause, framework-not-content strengthening — awaiting owner's approval to land as v1.2 addendum.
