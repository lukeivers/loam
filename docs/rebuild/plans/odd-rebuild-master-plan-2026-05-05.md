# ODD rebuild master plan — v0.2.2 → v0.2.5 path

**Status:** master plan; plan-before-code per `feedback_plan_before_code`. Authored 2026-05-05.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Predecessor:** v0.2.1 SHIPPED rollup at `6d66a2e`. Eric ship paused per Luke 2026-05-05 ("ignore eric, he's busy at his real job. we'll ship again when we're ready").

**Always-load grounding:** `docs/odd-llm-grounding.lean.md` (committed `d37c623`). Every dispatch + every session-start in this build path loads it; v0.2.2 makes the auto-load structural.

---

## §1 — Why this path exists

The v0.1.8 odd-extractor labels its outputs "AC" but extracts implementation facts (Express route exists at file:line), not objectives (operators can file refund disputes against merchant portals). This is the wrong altitude per ODD methodology — work flows from observable outcomes, not facts about how the system is built.

The v0.2.1 HARD smoke against rd-automation surfaced this concretely: 131 outputs, all symbol-level structural. Eric (or any user) asking "what should I build next?" gets nothing useful from that output.

This path rebuilds the extractor to operate at outcome altitude, layers a completeness interview + gap analysis on top, adds negative-alignment detection, and re-ships to Eric.

---

## §2 — End-state shipped at v0.2.5

A loam user installed on their codebase can ask: **"what should I build next?"**

The system answers using:

- **Objectives** — what outcomes the system delivers (extracted from README + design docs + tests + user-survey + code patterns; banded V/P/H).
- **Constraints** — bounds on the solution space (compliance, infra, language, security, domain).
- **Capabilities** — features that ladder to objectives.
- **Backing-implementation map** — which code paths back which objectives (the v0.1.8 structural extraction becomes derivative evidence rows here).
- **Augmented objective set** — extracted objectives + completeness-interview-with-user adds objectives that should be present but aren't (e.g., real-money app with no security-shaped objective surfaced for confirmation).
- **Gap inventory** — objectives without VERIFIED backing; implementation orphans (code without a named objective ladder); negative-alignment cases (objective says X, implementation does opposite/inverse).
- **Build-next recommendations** — derived from the gap inventory + user-stated priorities (first-task / pain-points from survey).

PR-safety, continuous-watch, and ratification flow all operate at objective altitude after this path lands.

---

## §3 — Release sequence

### v0.2.2 — ODD grounding propagation (foundation)

**Theme.** Make `docs/odd-llm-grounding.lean.md` auto-load before every ODD-shaped agent task. Without this, the rebuild work below drifts back to implementation-altitude on the first dispatch.

**Primary work:**
- Add `docs/odd-llm-grounding.lean.md` to the session-start corpus paths list (mechanism lives in `framework/hands-off-lifecycle/hooks/corpus_load_session_start.py` — sibling of existing entries CLAUDE.md / odd-methodology.md / odd-in-loam.md / VALUE_PROPOSITION.md / STATE.md).
- Reference from `framework/CLAUDE.md` so dispatched agents inherit the load.
- Bake reference into dispatch-brief templates for ODD-shaped tasks (`feedback_agent_prompts_scope_only` discipline + the existing "Principles to apply at turn-start" pattern).

**AI-time band.** 2-4 h. Quick foundation ship.

**Why first.** Every subsequent release authoring will keep producing wrong-altitude output without this. Foundation-altitude correctness is prerequisite.

### v0.2.3 — Objective-first extractor (replaces v0.1.8 extraction logic)

**Theme.** Rebuild the actual extraction logic to produce objectives at outcome altitude. Repurpose v0.1.8 substrate (banding, audit-log, ratification flow, four-stage workflow) but rebuild the extraction itself.

**Primary work:**
- Multi-source input pipeline: README + design docs + tests + user-survey context + code patterns (the LLM synthesizes from all sources, not just symbol-tree walking).
- Output: objectives (outcome-altitude, banded V/P/H), constraints (bounds on solution space), capabilities (features serving objectives).
- Backing-implementation map: objectives → code paths. The v0.1.8 structural extraction becomes evidence-rows mapping objectives to backing implementation.
- Rename surface: no more `AC.JSTS.express.get.<route>` labels for primary output. ACs are objectives.
- Update ratification flow to ratify objectives (PLAUSIBLE → VERIFIED on the OBJECTIVE, not on the symbol).
- Update PR-safety to consume objectives + backing-map (gate triggers when a change touches code backing a VERIFIED objective).

**AI-time band.** 12-22 h. Heavy cycle. Likely 3-4 sub-cycles (extraction logic / backing-map / ratification reframe / PR-safety reframe).

**Why second.** The core capability rebuild. v0.2.4 + v0.2.5 layer above.

### v0.2.4 — Completeness interview + gap analysis

**Theme.** After extraction lands, the persona interviews the user about the extracted objective set; gap analysis runs on the augmented set.

**Primary work:**
- Completeness interview: persona presents extracted objectives + flags missing-but-expected ones (e.g., "real-money app with no security-shaped objective"). User confirms / adjusts / adds via PM batch API one-question-at-a-time.
- Gap analysis: compare augmented objective set against backing-implementation map. Surface objectives without VERIFIED backing + implementation orphans (no objective ladder) + (subset) negative-alignment cases — see v0.2.5 for the full negative-alignment work.
- "What should I build next?" output: derived from gap inventory + user-stated priorities (first-task / pain-points from survey).

**AI-time band.** 6-12 h. Medium cycle. Likely 2-3 sub-cycles (completeness-interview / gap-analysis / build-next-recommendation).

**Why third.** Depends on extractor producing objectives at the right altitude.

### v0.2.5 — Negative-alignment detection + Eric re-ship

**Theme.** Hardest layer + ship gate.

**Primary work:**
- Negative-alignment detection: where an objective says X and implementation does the opposite or inverse. Eric's auth-bypass finding is the canonical example — objective O2 ("audit trail identifies who initiated each action") vs implementation that trusts client-controlled Referer header + accepts arbitrary `runner_email` query param. The system says it does X; the code does ¬X.
- HARD smoke gate against rd-automation end-to-end: extraction → completeness interview → gap analysis → "what to build next" → negative-alignment surfacing.
- Push pos-v2 → lukeivers/loam:main; tag v0.2.5; Eric installs (or upgrades). Gate the tag-push on Luke's ship-to-Eric ruling per master plan policy.

**AI-time band.** 6-12 h. Likely 2 sub-cycles (negative-alignment detection / Eric re-ship gate).

**Why fourth.** Hardest layer; needs all prior layers landed. Eric ship gates here.

---

## §4 — Aggregate AI-time band

**Total:** 26-50 h AI-time, midpoint ~38 h. Comparable shape to the Eric path (114-189 h human-developer; ~10x faster in AI-time per the rubric at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`).

**Calibration check.** Eric path actuals: v0.2.1 Cycle 1 build (~50 min wall-clock, 85 tool calls); Cycle 2 build (~30 min, 52 tool calls); F1 corrective (~50 min, 50 tool calls); F2 corrective (~25 min, 24 tool calls). Per-cycle wall-clock 25-60 min on average. Path total estimated: ~5-10 h actual wall-clock for the full v0.2.2-v0.2.5 sequence (assuming Sonnet for all cycles; Opus would slow it).

---

## §5 — Composition with existing surfaces

- **v0.1.7 PM batch API** — used by v0.2.4 completeness interview. No PM-side changes.
- **v0.1.8 odd-extractor** — extraction logic rebuilt at v0.2.3; substrate (banding, audit-log, ratification, four-stage workflow) preserved.
- **v0.1.9 PR-safety** — reframed at v0.2.3 to consume objectives + backing-map.
- **v0.2.0 continuous-watch** — operates at objective altitude post-v0.2.3 (flag changes that might affect objective coverage).
- **v0.2.0 auto-skill-capture** — unchanged; SKILL-ratification is independent of extraction altitude.
- **v0.2.1 onboarding** — unchanged; question set is install-time UX, not codebase-analysis.
- **v0.2.1 promotion rubric** — unchanged; SKILL promotion is independent.

---

## §6 — Honest doubts (F2 RF on this decomposition)

**6.1 — v0.2.2 propagation discipline may not be enough.** Auto-loading the lean grounding doc into corpus is structural; baking into dispatch-brief templates is structural. But the agent has to actually USE it. Drift may persist if agents skim the §altitudes table without internalizing. Mitigation: the lean doc itself contains 5 self-checks (§8) that the agent runs over output before declaring an "AC." Enforce-via-checklist not enforce-via-loading.

**6.2 — v0.2.3 multi-source extraction may surface inconsistent signals.** README says one thing; tests say another; commit messages say a third; user survey says a fourth. The synthesis layer has to honestly band uncertainty. Risk: hallucinated reconciliation that papers over real inconsistencies. Mitigation: the banding shape (V/P/H) lets the extractor honestly report uncertainty rather than confabulate. PLAUSIBLE means "consistent with multiple sources, not directly verified by one"; HYPOTHESISED means "pattern-based inference only."

**6.3 — v0.2.3 cost may exceed v0.1.8 by 10-100x.** Heuristic-only extraction is 0 cents. LLM-pass synthesis is dollars. Mitigation: cost band reasoning at v0.2.3 plan-author + production-stake-mode default-flip on cost ceilings. Budget envelope from v0.1.8.

**6.4 — v0.2.4 completeness-interview may bombard the user with too many questions.** Some objectives are obvious; questioning them all is friction. Mitigation: surface only the high-leverage missing-objective candidates (LLM-judged); user can ask for more depth.

**6.5 — v0.2.5 negative-alignment is the hardest layer.** Detecting "code does opposite of stated objective" requires deep semantic understanding. May produce false positives (claiming negative alignment that's actually fine). Mitigation: surface as PLAUSIBLE-class findings; user ratifies; never auto-decide.

**6.6 — v0.2.3 reframes break v0.1.9 PR-safety in transit.** The transition from structural-AC consumption to objective+backing-map consumption is a breaking change for the gate. Mitigation: stage carefully; sub-cycles within v0.2.3 land the new shape AND the gate update together.

**6.7 — Cost of this rebuild on existing canonical extractions.** v0.1.8 ran clean on canonical pos-v2 itself. Will the new extractor still produce useful output on the harness's own codebase? Mitigation: include canonical pos-v2 self-extraction as a smoke fixture at v0.2.3.

---

## §7 — Method-decision register

| Decision | Choice | Rationale |
|---|---|---|
| Master plan altitude | Compact 1-doc; per-version sub-plans follow | Lean overhead vs Eric path's verbose synthesis. |
| First release | v0.2.2 grounding propagation | Foundation-correctness prerequisite. |
| Extractor rebuild approach | Repurpose v0.1.8 substrate (banding/audit/ratification/four-stage); replace extraction logic | Substrate is correct shape; extraction was wrong altitude. |
| LLM-pass extraction | Yes at v0.2.3 (multi-source synthesis); cost-banded | Heuristic-only can't reach outcome-altitude on real codebases. |
| Negative-alignment timing | v0.2.5 (defer; hardest) | Falls out of objective + backing-map cleanly; build atop. |
| Eric ship | v0.2.5 only; no v0.2.1 install | Eric paused per Luke 2026-05-05; no value installing intermediate. |
| PR-safety reframe | Sub-cycle within v0.2.3 | Tightly coupled to extraction output shape; can't lag. |
| Cycle dispatch model | Sonnet default; Opus only for synthesis-heavy plan-author | Per existing precedent + cost. |
| Plan-doc shape per release | Mirror v0.2.1 master-plan / sub-plan-doc convention | Verified working through Eric path. |

---

## §8 — Provenance

- v0.2.1 SHIPPED rollup at `6d66a2e`.
- ODD grounding lean doc at `d37c623`; verbose at `ffd9c95`.
- Eric pause directive: Luke 2026-05-05 ("ignore eric...we'll ship again when we're ready").
- Always-load directive: Luke 2026-05-05 ("make sure the lean grounding doc is always in context. also, it should get added to the session start corpus").
- Layered design proposal (objectives → completeness-interview → gap-analysis → negative-alignment): Luke 2026-05-05 message 10114.
- v0.1.8 mis-altitude diagnosis: Luke 2026-05-05 messages 10110/10112/10114.
- Autonomy restored to full per Luke 2026-05-05 ("after that, though, i want you back to full autonomy").
