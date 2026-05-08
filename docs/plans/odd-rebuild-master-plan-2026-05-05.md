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

### v0.2.3 — Objective-first extractor (replaces v0.1.8 extraction logic) — **SHIPPED 2026-05-05** (local; tag deferred)

**Theme.** Rebuild the actual extraction logic to produce objectives at outcome altitude. Repurpose v0.1.8 substrate (banding, audit-log, ratification flow, four-stage workflow) but rebuild the extraction itself.

**Primary work shipped:**
- Multi-source input pipeline: README + design docs + tests + user-survey context + code patterns (the LLM synthesizes from all sources, not just symbol-tree walking).
- Output: objectives (outcome-altitude, banded V/P/H), constraints (bounds on solution space), capabilities (features serving objectives).
- Backing-implementation map: objectives → code paths. The v0.1.8 structural extraction repurposed as evidence-rows mapping objectives to backing implementation.
- Rename surface: no more `AC.JSTS.express.get.<route>` labels for primary output. ACs are objectives.
- Ratification flow ratifies objectives (PLAUSIBLE → VERIFIED on the OBJECTIVE).
- PR-safety consumes objectives + backing-map (gate triggers when a change touches code backing a VERIFIED objective).
- Continuous-watch operates at objective altitude.
- Legacy `acs:` field retired.

**Cycle SHAs (sealed):**
- Cycle 1 — Multi-source objective synthesis: seal `9b9f87c`; §14 `66de327`.
- Cycle 2 — Backing-implementation map + ratification reframe: seal `857749c`; §14 `5a6ddd2`.
- Cycle 3 — PR-safety + continuous-watch reframe + SOFT smoke: seal `f78bb36`; §14 `f2174ed`.
- SOFT smoke evidence: `<pos3>/workspace/.scratch/claude-output/v0-2-3-soft-smoke-2026-05-05.md`.
- 871 total tests green at v0.2.3 close (pr-safety 93 + odd-extractor 583 + cost-governance 71 + per-project-pm 124).

**AI-time actuals (per AI-time rubric `wall_clock_minutes ≈ tool_calls × 0.1-0.15`):** Cycle 1 ~30 min / 95 calls; Cycle 2 ~27 min / 75 calls; Cycle 3 ~36 min / 190 calls. Aggregate ~93 min wall-clock (vs 12-22h human-developer band — ~10× faster, per rubric).

**Why second.** The core capability rebuild. v0.2.4 + v0.2.5 layer above.

### v0.2.4 — Completeness interview + gap analysis — **SHIPPED 2026-05-05** (local; tag deferred)

**Theme.** After extraction lands, the persona interviews the user about the extracted objective set; gap analysis runs on the augmented set; the system produces a "what should I build next?" output the user can act on. Negative-alignment carved out to v0.2.6+ per Luke 2026-05-05 ruling.

**Cycle SHAs (sealed):**
- Cycle 1 — Completeness interview: seal `d42ace9`; §14 `afdbcde`. 11 ACs AC.COMPINT.1-11.
- Cycle 2 — Gap analysis: seal `9d15333`; §14 `b67c0bb`. 9 ACs AC.GAPAN.1-9.
- Cycle 3 — Build-next + persona surface + SOFT smoke (closes v0.2.4): seal `064cc2e`; §14 `38a0473`. 13 ACs AC.BLDNXT.1-9 + AC.PERSONA-PULL.1-4.
- 1421 total tests green at v0.2.4 close (813 odd-extractor + 73 cost-governance + 124 per-project-pm + 411 workspace-bootstrap).
- SOFT release smoke against canonical jsts-playwright-app fixture: ALL 6 dimensions exercised; §self-checks ≥90% gate passed.

**AI-time actuals:** Cycle 1 ~15 min / 130 calls; Cycle 2 ~14 min / 70 calls; Cycle 3 ~24 min / 110 calls. Aggregate ~53 min wall-clock (vs 6-12h human-developer band — ~10× faster, per rubric).

**Why third.** Depends on extractor producing objectives at the right altitude.

### v0.2.5 — Eric re-ship (HARD smoke gate) — SHIPPED 2026-05-06

**Theme.** Ship gate. Negative-alignment detection carved out per Luke 2026-05-05 ruling and pushed to v0.2.6+ (see below); v0.2.5 was Eric-re-ship-only and effectively became a v0.2.4.1 stabilization release.

**SHIPPED ARTEFACTS:**
- HEAD `7f41ed0` pushed to `lukeivers/loam:main` 2026-05-06 (93 commits covering v0.2.2 → v0.2.5).
- Tag `v0.2.5` pushed to `lukeivers/loam` 2026-05-06.
- Eric outreach explicitly held per owner directive 2026-05-05; v0.2.5 sits as published-and-tagged release awaiting re-engagement.

**Cycle ladder (6 corrective rounds + 1 methodology amendment + 4 HARD smoke runs):**
- C1+C2 (corrective) — CLI synthesis client wire-through + interview ValueError → OddExtractorError; absorbed under methodology-amendment seal `a9bc524` due to F-RACE incident (parallel dispatch in same WD; per `feedback_serialize_amendment_builds`).
- ODD test-altitude procedural fix (methodology) — outcome-altitude AC requirement + new SKILL `odd-test-altitude-discipline` (with Luke's L3-conditional risk-band classifier per Telegram 10188) + memory rule `feedback_test_outcome_altitude_required.md`. Seal `a9bc524`.
- C3 (corrective) — install-from-source synthesis extra + outcome-altitude AC C3.3 (first worked instance of the new SKILL). Seal `89f97c6`. C3.3 caught F8 (LLM banding violation) on first live run — validation case for the procedural rule.
- C4-pivot (corrective) — MAJOR DIRECTION CHANGE per owner ruling Telegram 10194: rip Anthropic SDK; replace with `claude -p` subscription auth via NEW `claude_print_synthesis_client.py` mirroring memory-system precedent. F8 fix folded in (prompt + two-pass demotion-guard). Seal `76e5a8f`.
- C5 (corrective) — `--strict-mcp-config` + empty MCP config tempfile in claude -p subprocess invocations (memory-system + odd-extractor) so spawned `claude` processes don't kill the parent session's telegram MCP via PID-file-stomp dedup. Seal `6d2052d`.
- C6 (corrective) — fixture-PM smoke + extraction-dir resolution to target `<repo>` + `.loam/` gitignore + error message references valid command. Seal `5138dd7`.

**HARD smoke trajectory (against rd-automation real-world):** RED → RED → RED → GREEN. Each RED excavated layered F1+F2+F5+F8+F-DESIGN-1/2/3 production-path bugs that v0.2.3 + v0.2.4's SOFT smokes never exercised.

**HARD smoke 4th run GREEN 2026-05-06:** 6 outcome-altitude objectives extracted from rd-automation; §self-checks 13/15 = 87% pass (above 80% threshold); 6/6 backing-map coverage with VERIFIED or PLAUSIBLE evidence rows; 3 gaps in `gap-inventory.yaml`; 3 ranked candidates in `build-next.yaml` with rationale referencing specific gaps; stages 1-4 all exit 0; no Python tracebacks; loam tree + rd-automation tree clean (extraction redirected to `<repo>/.loam/` per C6 fix); telegram MCP stayed up under real-world synthesis load (C5 verified). 3 yellow non-blockers carried forward.

**AI-time actuals:** ~5-7 h aggregate wall-clock across all corrective rounds + 4 HARD smoke runs. Initial band of "12-30 min AI wall-clock" was for the planned smoke-execution-only scope; the actual cycle was 10× larger because of the layered production-path gaps surfaced.

**Architectural constraint locked-in:** subscription-only via `claude -p`; NO Anthropic API key anywhere in loam (memory rule `feedback_no_anthropic_api_key.md`).

### v0.2.6+ — Negative-alignment detection (carved out from v0.2.5; post-Eric)

**Theme.** Hardest layer; defer to post-calibration-data shipment.

**Primary work:**
- Negative-alignment detection: where an objective says X and implementation does the opposite or inverse. Eric's auth-bypass finding is the canonical example — objective O2 ("audit trail identifies who initiated each action") vs implementation that trusts client-controlled Referer header + accepts arbitrary `runner_email` query param. The system says it does X; the code does ¬X.

**Why carved out (per Luke 2026-05-05 ruling):**
- 25%+ false-positive risk per master plan §7.5; shipping unverified judgment-class output to a high-quality-bar user is a risk multiplier, not a quality WOW.
- No real-world calibration data exists for the heuristic. Better to ship after we have data, not before.
- Eric's auth-bypass case is something he flagged himself in survey Q5; gap analysis + his stated security priority will surface it via the existing v0.2.4 pipeline. Negative-alignment isn't required to deliver "the system found this."
- v0.2.3 + v0.2.4 IS the complete "what should I build next?" capability; negative-alignment is a marginal demo-cleanliness enhancement, not a load-bearing capability.

**AI-time band.** 4-8 h human-developer → ~25-50 min AI wall-clock per the rubric. Standalone release post-Eric once we have field calibration data on which to tune the false-positive rate.

**Why later.** Speculative + needs calibration data; shipping it before Eric installs adds risk without adding load-bearing capability.

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
