# Loam Release Roadmap

**Effective:** 2026-05-08.
**Status:** Forward-looking; ratified versions land here as `STATE.md` rollups when they ship.
**Composes with:** `docs/release-versioning-policy.md` (SemVer commitment), `docs/odd-semver-pinning.md` (ODD ↔ SemVer pinning), `docs/VALUE_PROPOSITION.md` (prime objective), `docs/odd-llm-grounding.lean.md` (methodology).

This file replaces the prior per-release master plans (the v0.1.x roadmap fragments and the ODD-rebuild master plan). The canonical forward-looking artefact is one file.

---

## §1 Framing

### Versions are objective targets, not feature lists

Every minor version is named by a single sentence — what a user can newly do with loam that they could not do before. Multiple ideas, fixes, and components roll up under that sentence. Anything that does not ladder up to the version's objective gets pushed to a later minor or to backlog.

The sentence is the version's identity. Acceptance criteria and constraints follow. This file does not enumerate features against versions; it enumerates outcomes against versions and lets the source items ladder up.

### Loam's prime objective shapes every entry

Loam exists to help people use LLMs to **build software** (`docs/VALUE_PROPOSITION.md`). The Dev/SDLC plugin is "Software Development Life Cycle" — `extraction is a scaffold` that places initial boundaries on what gets built; **working code is the deliverable**, not the extracted contract. Roadmap entries from v0.4.0 onward are framed against that deliverable shape.

### Architectural constraints (apply to every entry)

These are non-negotiable across the roadmap unless the policy doc itself changes:

- **No Anthropic API key anywhere in loam.** All LLM-routed paths use `claude -p` against the user's Claude Max OAuth keychain (memory rule `feedback_no_anthropic_api_key.md`, captured 2026-05-05 after the v0.2.5 C4-pivot ruling). Features that would require API-key access do not land in loam — they go to backlog.
- **`claude -p` invocations carry `--strict-mcp-config` + empty MCP config tempfile** (precedent: workspace-sync resolver client; v0.2.5 corrective C5 propagation; AC.WSα.8). Every loam subprocess that forks `claude -p` MUST scrub MCPs to avoid killing the parent's Telegram bot or other MCP servers.
- **ODD §2.5 — every line of code/branch/test maps to a named AC.** Methodology constraint. Every roadmap entry produces ACs, not vague "improvements."
- **SemVer commitment** (`docs/release-versioning-policy.md`). MAJOR=breaking, MINOR=new outcome shape, PATCH=defect closure within the most-recent minor's outcome.
- **Subscription-only (Claude Max OAuth)** is loam's distribution shape. Multi-LLM via OpenRouter or any API-keyed router is incompatible with this constraint and stays in backlog.

### How this composes with ODD-SemVer pinning

`docs/odd-semver-pinning.md` defines how ACs (the ODD acceptance-criterion units) bind to SemVer digits — VERIFIED-banded ACs in the public surface are MINOR-stable; PLAUSIBLE/HYPOTHESISED ACs are MINOR-unstable; band promotions/demotions are MINOR bumps. This roadmap document supplies the **objective sentence** for each minor; the pinning document supplies the **stability contract** within each minor.

---

## §2 Shipped (concise summary, v0.1.0 → v0.4.0)

Pulled from `docs/STATE.md`. Each entry is the minor's objective sentence + the seal anchor.

| Version | Objective sentence | Anchor |
|---|---|---|
| v0.1.0 | Loam ships publicly at `lukeivers/loam` with the Dev/SDLC plugin as the only v1 plugin, dormancy-renamed pre-launch, all pre-publish blockers closed (memory pipeline, M9 substitution, fastmcp filter, M1c-corrective). | 2026-05-01 cross-session memory probe gate; M11 dry-run gate. |
| v0.1.6 | Loam workspaces declare a `safety_profile` field with non-tunable production-stake floors and a cost-governance dry-run primitive. | seal `3f1d237`, `88674cb` |
| v0.1.7 | Loam personas, per-project PM, and layered-skill architecture move coordination machinery off the persona's user-visible surface. | seals `3aa20dd`, `73505f0`, `bcf699a`, `122a7c8` |
| v0.1.8 | Loam reverse-extracts ODD contracts (banded ACs + ratification) from Ruby/Rails and JS/TS/Playwright codebases; first 6 dev-sdlc SKILLs auto-discoverable. | seals `c1abda1` … `e4512b9` |
| v0.1.9 | Loam's PR-safety gate engine + override workflow + hook installers + 3 CI templates close the gap between contract drift and merge-time enforcement. | seals `790807d`, `0dc557e`, `3284087` |
| v0.2.0 | Loam keeps the contract alive (continuous codebase-watch + scheduling) and captures user-driven SKILLs (auto-skill-capture MVP, 3 of 6 triggers). | seals `6fef2f1`, `549fe88` |
| v0.2.1 | Loam install-time onboarding ritual hardens the first-run experience and the promotion-rubric mechanism makes SKILL graduation/demotion observable. | seals `55640b1`, `298172e`, plus correctives `ad42314`, `d82a43b` |
| v0.2.2 | Loam's ODD grounding doc auto-loads at every fresh DEV-mode session; dispatch-brief authoring SKILL propagates 5 principles to sub-agents. | seal `5eda09d` |
| v0.2.3 | Loam extracts contracts at the **objective altitude** rather than the symbol altitude (multi-source synthesis: README + design docs + tests + survey + code patterns). | seals `9b9f87c`, `857749c`, `f78bb36` |
| v0.2.4 | Loam runs a completeness interview, computes a gap analysis, and produces a "what should I build next?" output ranked against extracted objectives. | seals `d42ace9`, `9d15333`, `064cc2e` |
| v0.2.5 | Loam's reverse-ODD pipeline runs HARD smoke-clean against a real-world codebase (`rd-automation`); the `claude -p` synthesis client replaces the Anthropic SDK; subscription-only architecture verified. | seal `7f41ed0`; tag `v0.2.5` pushed 2026-05-06 |
| v0.2.5.1 | Loam respects user-declared off-limits zones, exposes a configurable synthesis timeout, and cascades capability drops when their target objectives are guarded out. | seals `b1d5f1e` (apply), `7a06034` (§14 backfill) — closes Eric's three F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN findings |
| v0.3.0 | Loam's documented features work as advertised AND loam's terminology is consistent across forward-looking surface — `docs/rebuild/` collapsed (~5300 refs scrubbed); graphiti rip-out + FBE.7 file-backed memory canonical; foundation-docs gap-fill (CLAUDE.md Lens 6/7 + principle-derivation-map port); lint pass clean (`ruff` + F821 sweep); `KNOWN_CROSS_MODE_DEBT` shrinks 1 → 0; F3 + F4 closures; `docs/glossary.md` published (12 canonical terms); feature-honesty audit 100% match post-C6.1; `claude -p --strict-mcp-config` invariant verified 3/3 production sources; ODD-conformance allowlist published (18 entries); HARD smoke GREEN against rd-automation. | Cycles 1–7 + C6.1: apply `e80437b` / seal `459c7fc` (C1); apply `39094ea` / seal `013553e` (C2); apply `ad12cc1` / seal `be48b34` (C3); apply `46fd2a7` / seal `7afb648` (C4); apply `dddaf8d` / seal `542b939` (C5); apply `f8beeaa` / seal `0734ea9` (C6); apply `9864b0a` / seal `58da132` (C6.1); apply `d849aee` / seal `3c6fdd5` (C7) |
| v0.4.0 | Loam ships a code-gen surface (`loam odd-extract <repo> --code-gen`) optimised for **extending an existing repo** — consumes objectives.yaml + gap-inventory.yaml + build-next.yaml + emits a unified diff against the source tree with each commit's `objectives:` block populated (amendment #38 `lifted_from` schema reused); `jsts-playwright-app` outcome-altitude verified end-to-end against real `claude -p` subprocess; substrate composition on Claude Code Routines (`feedback_routines_runtime_layer.md` + 1 example plan-doc) + Code Review (plan-author SKILL section + 1 example) + Outcomes-pattern ADR (`docs/design/odd-vs-outcomes.md` documenting API-key-vs-subscription divergence). **F-DESIGN-1 confirmed empirically at C4 ProgramBench v0 baseline:** Variant A (docs-only feeder → reverse-ODD → ODD-grounded code-gen) **56% (9/16)** vs direct `claude -p` baseline **100% (16/16)** on 3 small tasks; the v0.4.0 surface does NOT (yet) ship cold-start docs-only multi-file code-gen — that surface extension is named in §6 as the v0.4.1 closure path. **NOTE on scope:** "ProgramBench v0" is an internal experiment with 3 hand-authored toy tasks (calculator, jsonpp, wcclone), NOT the public ProgramBench leaderboard at programbench.com (where major providers score 0–3% on hundreds of much-harder tasks). Real-benchmark eval blocked at C4 by Docker daemon issue on dev host; deferred to v0.5.0. | Cycles 1–5: apply `a7d1182` / seal `cc2efbb` (C1 code-gen-core, SOFT smoke); apply `b358646` / seal `f031c89` (C2 outcome-altitude verification on jsts-playwright-app); apply `f977185` / seal `2d1e7f0` (C3 substrate composition); apply `fdbdc91` / seal `e5c6246` (C4 ProgramBench v0 docs-only baseline); apply `1733a7d` / seal `7787a22` (C5 release-level smoke gate + ship rollup) |
| v0.4.1 | Loam closes F-DESIGN-1 with three additive sub-fixes inside `plugins/dev-sdlc/odd-extractor/`: **multi-commit-per-task emission** (LLM responses with `===COMMIT===` delimiters yield multiple `CodeGenCommit` records; single-commit responses backward-compat); **from-scratch prompt mode** (auto-detect via `_detect_from_scratch` traversal + explicit `--from-scratch` / `--no-from-scratch` CLI flags; instructs `--- /dev/null` source-side framing + encourages multi-file submissions); **build-next tie-breaker beyond alphabetical** (cluster-size desc + objective-text-length desc inserted between confidence-rank and lex fallback in `_tiebreak_key`). All three sub-fixes verified working in production via the v0.4.1 ProgramBench v0 re-run on the same 3 tasks (calculator + jsonpp + wcclone): all tasks emitted 3 commits each; all diffs use `--- /dev/null` framing; **the C4 jsonpp failure case is closed** — tie-breaker correctly ranked `formatting` over `error-handling` (vs alphabetical's wrong choice in C4); aggregate Variant A pass-rate 62.5% (10/16) RELAXED vs C4's 56%. **NOTE on scope:** these percentages are on the 3 internal toy tasks (calculator, jsonpp, wcclone), NOT the public ProgramBench leaderboard. Real-benchmark eval remains deferred to v0.5.0. **F-DESIGN-2 surfaced** (smaller-scope follow-on; `compile.sh` missing in 3/3 runs because the SPEC's "Test interface" section isn't passed into the prompt) — closed at v0.4.2 (row below). HARD smoke GREEN against rd-automation (267s Stage 1 wall-clock; 12.57¢ synthesis cost; F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-along all GREEN; subscription-only invariant preserved). | Single-cycle PATCH: plan-doc `0b2a890` + manifest baseline-update `a10350e`; sub-fix 1 (multi-commit) `1b7160c`; sub-fix 2 (from-scratch + CLI) `c27c711`; sub-fix 3 (tie-breaker) `bb62f86`; experiments doc append `946424d`; apply `450c787`; seal `7b8e22e0` |
| v0.4.2 | Loam closes F-DESIGN-2 with two additive sub-fixes inside `plugins/dev-sdlc/odd-extractor/`: **Test-interface section as load-bearing context in from-scratch prompt** (`_extract_test_interface_excerpt` walks SPEC.md/README.md/etc for a "Test interface" / "Tests" / "Behavior" / "Interface" section; falls back to full doc body capped at 4000 chars; injects under canonical `Test interface from SPEC:` heading; system prompt instructs authoring `compile.sh`/`executable` as first-class commits + matching SPEC's CLI form EXACTLY); **Py-version compatibility** (instruction-side: prompt names Python 3.9-compat + no PEP-604 unions + no match/case; post-process-side: `_lower_pep604_unions` + `_rewrite_pep604_in_line` defensively rewrite `X | Y` → `Union[X, Y]` / `Optional[X]` in `+++ b/*.py` hunks, auto-injecting `from typing import Optional, Union`; belt-and-suspenders so stochastic LLM regressions get caught). v0.4.2 ProgramBench v0 re-run shows full F-DESIGN-2 closure: aggregate Variant A pass-rate **100% (16/16) STRICT** vs v0.4.1's 62.5% (10/16) RELAXED + 0% STRICT. **NOTE on scope:** "100% (16/16) STRICT" is on the 3 internal toy tasks (calculator, jsonpp, wcclone), NOT the public ProgramBench leaderboard at programbench.com (major providers at 0–3% on hundreds of much-harder tasks). Real-benchmark eval remains deferred to v0.5.0; this validates the architectural mechanism on toy fixtures, NOT loam's real-world program-synthesis performance. **wcclone fully recovered** 0/6 → 6/6; calculator + jsonpp tied at 3/3 + 7/7 (now STRICT — compile.sh authored OR executable matches SPEC exactly). HARD smoke GREEN against rd-automation (230s Stage 1 wall-clock; 22¢ synthesis cost; F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-along all GREEN; subscription-only invariant preserved). | Single-cycle PATCH: plan-doc `7403d2d`; sub-fix 1 (test-interface load-bearing) `28229eb`; sub-fix 2 (py-version-compat tests) `70e6ba7`; experiments doc append `5cdea12`; apply TBD-AT-APPLY; seal TBD-AT-SEAL |
| v0.4.3 | Loam fixes the file-based memory retrieval defect (FBE.7 surface) that bypassed BM25 on natural-language UPS prompts and let giant compaction-summary episodes win every common-stop-word query. Three fixes inside `framework/primary-persona/`: **token-sanitized FTS5 + OR-of-tokens** (`_fts_search` replaces line-504 phrase-wrap with `_tokenize_for_fts`: whitespace split → alnum/_ run extraction → lowercase → drop <2-char tokens → drop the in-tree 20-stopword set → dedup-preserving-order → join with `OR`; FTS5 BM25 ranker now ranks by relevance across any-token-matches); **length-normalized `_grep_search`** (raw `score = sum(...)` swapped for `score = raw_score / max(len(content), 1)` linear normalization per builder ruling D-V043.2 — sqrt path (a) was empirically insufficient against the AC-spec fixture; linear (path b-shaped, BM25 `b=1` extreme without avgdoclen precomputation) closes the gap; stdlib-only); **cosmetic `episode_uuid → path` worker-log fix** (`memory_write_worker.py:284` swaps the hard-coded graphiti-era `episode_uuid` field for the file-based store's actual return field `path`; restores diagnostic signal). AC.V043.5 live-store probe **10/10 GREEN** vs investigation baseline 1/6 = 17% (10 natural-language probes against the live `~/pos3/workspace/.loam/memory/` corpus of 457 episodes; all probes returned a relevant top-3 episode). HARD smoke GREEN against rd-automation (335s Stage 1 wall-clock; ~38¢ synthesis cost; F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-along all GREEN; subscription-only invariant preserved; cold-venv import of `_tokenize_for_fts` + `worker-ok` log shape both verified). 554 framework/primary-persona/tests pass + 1 skipped (live-store probe, opt-in only); no regression. | Single-cycle PATCH: plan-doc + manifest `c00e7cc8`; source-edit (FTS token-sanitization + grep length-norm + worker-log fix) `a254f2c0`; corrective sqrt → linear `cd3b9778`; tests `a89a8e94`; experiments doc (probe writeup) `bf3178e0`; experiments doc (HARD smoke) `7bff3817`; apply TBD-AT-APPLY; seal TBD-AT-SEAL |
| v0.5.0 | Loam closes the dispatch-time consumption gap on the v0.1.7 subagent-personas substrate — production dispatch sites (13/13 audited plan-docs across v0.3.x + v0.4.x) all default to `subagent_type: general-purpose` despite mapping cleanly to one of the 5 v0.1.7 typed personas (loam-builder / loam-plan-author / loam-researcher / loam-reviewer / loam-documenter). Two SKILL surfaces inside `plugins/dev-sdlc/skills/`: **new `subagent-routing` SKILL** (work-shape → typed-persona rubric; recommends `subagent_type: <persona>` at brief-authoring time; fall-back-to-general-purpose clause for cross-persona / tool-surface-mismatch / persona-constraint-override / no-match boundary cases); **`dispatch-brief-authoring` SKILL extension** (§"When subagent_type is not general-purpose" — partial-omission table per AC.DBT principle × persona; AC.DBT.{3,5,6} + TIME-CLAIMS-DISCIPLINE still propagate for every typed dispatch because the v0.1.7 persona bodies don't carry them; AC.DBT.{2,4} have per-persona OMIT-OK rows only where the persona body explicitly carries the discipline; backward-compat preserved when `subagent_type == general-purpose`). AC.V050.1 audit verdict GREEN (100% / 13 of 13 dispatch-shape sites map to a typed persona). AC.V050.5 outcome-altitude probe verdict YELLOW (-22.9% brief-length reduction at initial measurement; below the GREEN ≥30% target). **Post-seal priming-gap corrective landed 2026-05-09** (`fix(personas): close AC.V050.5 priming gap`): each of the 5 typed personas at `plugins/dev-sdlc/agents/loam-{builder,plan-author,researcher,reviewer,documenter}.md` gained a §"Reporting + escalation discipline" section covering AC.DBT.{3,5,6} + TIME-CLAIMS-DISCIPLINE; the cross-walk table flipped 4 of 6 propagated-principle rows from "propagate" to "OMIT-OK" for every typed persona. Post-corrective + AC-tighten 2026-05-09 AC.V050.5 verdict: GREEN (-22.0% midpoint / -22.9% floor; meets the corrected ≥20% threshold). Original ≥30% target was set against an idealized "all 6 propagated principles fully omittable" assumption that the post-corrective audit invalidated. The 84-line typed-brief floor is set by non-AC.DBT brief structure (mission + authorization + fence + ACs + halt triggers + bookkeeping + model rationale). Quality-preservation projected GREEN; live-cycle verdict pending next typed dispatch. Halt-and-surface (per F2 RUTHLESS FEEDBACK): two paths for owner ruling at `workspace/.scratch/claude-output/v0-5-0-routing-probe.md` — Path 1 (tune AC band to ≥20% to match achievable ceiling; recommended per `feedback_loose_AC_text_fix_AC_not_implementation`) or Path 2 (v0.5.0+ follow-on consolidating non-AC.DBT brief structure; estimated 60-90 min AI-time). Pre-existing test failure cleared as part of AC.V050.4 no-regression closure: `odd-test-altitude-discipline` SKILL (orphan from prior shipping cycle) admitted into the AC.SKILLS-DSDLC2.7 expected-skills registry. | Single-cycle MINOR (reclassified per Q3 2026-05-09): plan-doc + manifest `7c8b0f57`; new `subagent-routing` SKILL + extended `dispatch-brief-authoring` SKILL + AC.V050.* test family + audit/probe artefacts + FIDRAFT v0.5.0 deferred items + roadmap §2 row + STATE.md row; apply TBD-AT-APPLY; seal TBD-AT-SEAL; tag `v0.5.0` (annotated, `c48895e6`) pushed to `origin` 2026-05-09 |
| v0.5.1 | Loam's split-worktrees migration retires the prior `pos-v2` branch + collapses the dual-tree `ivers-corp-pos-v2` + `pos3` layout into a single canonical clone at `~/loam/`, plus a Phase 1 first-impression cleanse rebrand (Tier-1 docs scrubbed of `ivers-corp-pos-v2` references → `loam` canonical paths; workspace-sync docstrings corrective). The migration retires the obsolete dual-tree + branch shape that confused first-time readers. | Single-cycle PATCH: branch rename + first-impression cleanse `85d29ce`; path fixup `7363cfb`; Tier-1 cleanse `e34f84a`; workspace-sync corrective `4740d62`; tag `v0.5.1` (annotated, `e84807c4`) pushed to `origin` 2026-05-09 |
| v0.6.0 | Loam ships a concrete release process: `loam release <version>` CLI verb (subcommand under `loam` top-level; sibling to `loam amend`) + six structural pre-publish gates (HARD smoke GREEN, ACs verified per plan-doc §status, STATE.md updated, clean tree, branch == main, seal commit reachable from HEAD) + annotated tag at the seal commit + `git push origin main` + `git push origin <tag>` + optional `gh release create` with auto-generated notes (plan-doc §1 outcome shape + §status verdicts + commit log between previous seal and this seal, with chore-prefix noise filter when log is dense) + post-ship review block (next-scope proposal from `release-roadmap.md` §4 priority queue + recent `FUTURE_IDEAS_DRAFT.md` captures + pre-1.0-vs-post-1.0 major-release eval). New runbook at `docs/release-process.md` (six sections: pre-publish gates table, `loam release` invocation + flags, post-publish state + things-to-check-next, manual fallback, composes-with, cross-references). 40 new tests at `framework/tools/loam/tests/test_AC_V060_*.py` cover AC.V060.{1,2,3,4,6} GREEN; AC.V060.7 dogfood deferred to dispatcher publish action per ASK-FIRST. Closes the figured-out-as-I-went publish workflow that bit on the v0.4.3 publish (Telegram 10547 owner directive). Architectural-orthogonality argument: the v0.6.0 surface does not touch the rd-automation pathway / synthesis client / memory retrieval / subagent-personas routing / amendment-dispatch tooling, so no Eric-workflow regression risk; HARD smoke shape adapts (full test suite GREEN + live `--dry-run` against canonical) per the v0.5.0 / v0.5.1 precedent of rd-automation-orthogonal minors. | Single-cycle MINOR (re-derived from v0.4.5 PATCH at build-start per Q2 ratification): plan-doc revision `c05ce45`; source-edit + 5-module subpackage + 40 tests + runbook `d1a6027`; pre-apply admin (STATE + roadmap + §13 + HARD smoke writeup) `5067797`; apply `8125117`; seal `eaf8f24` |
| v0.7.0 | Loam ships the non-tech-user surface: a non-technical user with a fresh `git clone lukeivers/loam`, a working Claude Code install, and no prior knowledge of ODD / objectives / acceptance criteria can run a single setup command, answer plain-English onboarding questions, ask for what they want in natural language, and receive working software output without ever being asked "what's your acceptance criterion." Seven ACs across four components: light-touch-narration SKILL (modality / specialist / tier / data-model decision categories trigger one-sentence narration with calibrated lead phrases; verbosity-tunable per `education_verbosity`); workspace-bootstrap manifest gains `primary_channel: telegram | terminal` runtime-routing slot with migration default from legacy `channel_preference`; channel-routing policy at `framework/primary-persona/src/loam/primary_persona/channel_routing.py` covering the four AC-named cells (D-NTU.2.c — Stop-hook integration deferred per build-time decision); workspace-corpus-overrides doc + household-finance reference override at `docs/examples/corpus-overrides/`; memory-doc skeleton template + `loam amend new-memory <slug>` orchestration parallel to `new-plan` (D-NTU.4 — switched to loam-amend; parallelism load-bearing); reference session-transcript at `docs/examples/non-tech-user-session-transcript.md` (synthetic-proxy capture per Q2 = SYNTHETIC PROXY ratification — real-user shipping reserved for v1.0 criterion #2 event); outcome-altitude stranger-clone probe at `framework/workspace-bootstrap/tests/test_AC_NTU_6_outcome_altitude_stranger_clone.py` (real-execution probe; verifies user-visible surface contains zero ODD vocabulary; surfaced + scrubbed an ODD-vocabulary leak in onboarding Q4 — substrate "ODD extractor" replaced with "scan this codebase for design patterns"; deeper F-DESIGN finding deferred to follow-on amendment); implementation-tier-picker SKILL + tier-ladder doc at `docs/implementation-tiers.md` (five tiers; tier-5 risk-surfacing template — Q3 = FOLD IN ratification). 62 new NTU.* tests across four components GREEN; no regressions. v0.7.0 makes the v1.0 quality-bar criterion #2 ("one real user has shipped real software with loam") empirically reachable for the first time. | Single-cycle MINOR (Q1 = MONOLITH ratification): plan-doc rename `6c4bf55`; source-edit + 62 tests + 2 SKILLs + 1 module + 4 docs `eb0a4d3`; pre-apply admin `6f0e0e9`; apply `5312469`; seal `1e6fc76` |
| v0.7.4 | auto-backfill completeness PATCH (defect-closure for v0.7.3's spec gaps surfaced at v0.7.3's own publish dogfood). Closes the 4 residual gaps in v0.7.3's auto-backfill spec that the v0.7.3 runner missed at commit `88964cb`: leading row-title `**vX.Y.Z PATCH SHIPPED LOCAL**` was never flipped (only the trailing sentence got the flip); STATE.md row's `seal `7b9c14e`` was untouched (only roadmap §2 row got TBD-AT-* backfill); ``84496f3`` (source-edit SHA) + ``9ba3bcf`` (apply SHA) left manual per v0.7.3 D-BACKFL.1.b deferral. Manual touch-up at `cb71ca5` + `5c3f7ac` closed the gaps for v0.7.3; v0.7.4 makes them structural. Three new helpers in `post_publish_backfill.py`: `_backfill_state_md_leading_title` flips the bolded title (CLASS casing preserved across MINOR/PATCH/minor/patch); `_backfill_state_md_placeholders` mirrors v0.7.3's roadmap-row TBD-AT-* helper to STATE.md; `_discover_source_edit_and_apply_shas(repo_root, seal_sha)` walks the seal commit's git log message to find the apply commit (`chore(seals): <slug> — ... at <apply-sha>` canonical form) + extracts source-edit SHA from the apply commit's message (`chore(amend): <slug> manifest+apply — ... BASELINE+sidecar bump to <source-edit-sha>` canonical form). Path-B ruling per AC.BACKFL2.3 (single-component release-CLI extension; path-A — extend `loam amend seal` contract — declined as cross-component). Idempotence preserved: all 11 v0.7.3 BACKFL tests continue to pass without modification (graceful-degradation through D-BACKFL2.3.b). Six ACs (AC.BACKFL2.{1-6} plus AC.BACKFL2.S); 8 new tests at `framework/tools/loam/tests/test_AC_BACKFL.py` cover positive (title-flip, STATE.md seal-backfill, commit-graph discovery against real-git fixture, integration with full v0.7.4 pre-image), negative (already-public no-op), graceful-degradation (non-canonical message form). AC.BACKFL2.6 outcome-altitude probe runs `apply_backfill` against the live `/Users/lukeivers/loam/` state for v0.7.3 — verifies all 4 v0.7.3 gap-edits are correctly identified + commit-graph walk discovers the real apply (`527698b`) + source-edit (`01e0883`) SHAs; documented in `docs/experiments/v0-7-4-hard-smoke.md`. After v0.7.4 lands, `loam release vX.Y.Z` against a freshly-sealed version with the canonical pre-publish state needs zero manual follow-on commits to reach a fully-current SHIPPED-PUBLIC state. | Single-cycle PATCH: plan-doc + manifest `10376d7`; source-edit (helpers + 8 tests + release-process update + FIDRAFT capture-and-resolve + STATE/roadmap admin + HARD smoke writeup) `84496f3`; apply `9ba3bcf`; seal `7b9c14e`; **SHIPPED PUBLIC 2026-05-10 at tag `v0.7.4` (annotated `1cc50bf`)** |
| v0.7.3 | release-CLI post-publish auto-backfill PATCH (defect-closure for v0.6.0's release-process). Closes the recurring SHIPPED-LOCAL → SHIPPED-PUBLIC manual-backfill defect that bit at every loam publish since v0.6.0 (commits `5c0d272` v0.6.0, `0f0d4b3` v0.7.0, `af73a69` v0.7.1, `f0ae00c` v0.7.2). New module `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` exports `apply_backfill(repo_root, version, tag, tag_sha, *, dry_run=False) → BackfillResult` wired into `runner.run` between step 4 (push branch + tag) and step 6 (post-ship review). The function flips the STATE.md trailing `<version> SHIPPED LOCAL — owner gates publish.` sentence to `**<version> SHIPPED PUBLIC YYYY-MM-DD at tag \`<tag>\` (annotated \`<sha7>\`)**.`; appends the SHIPPED-PUBLIC marker to the §2 row's third pipe-cell; backfills ``39170e6`` / ``72de0da`` placeholders from known SHAs (`TBD-AT-COMMIT` / `TBD-AT-APPLY` not discoverable from runner inputs); updates the `**Total shipped:**` aggregate-count summary line via §2-row walk; appends a new bold entry to §3 Active version. Commits as `docs(release): vX.Y.Z post-publish backfill — SHIPPED PUBLIC` and pushes. Idempotent on re-run (no commit if no edits). Six ACs (AC.BACKFL.{1-6} plus AC.BACKFL.S); 11 new tests at `framework/tools/loam/tests/test_AC_BACKFL.py` cover positive/negative/idempotence/dry-run/runner-integration. AC.BACKFL.6 outcome-altitude probe runs `loam release v0.7.3 --dry-run` against this very plan-doc — output includes `DRY-RUN: would apply post-publish backfill` summary block naming the file edits; documented in `docs/experiments/v0-7-3-hard-smoke.md`. Closes the v0.6.0 documented-vs-enforced gate gap (the gates table claims "STATE.md updated" — true at publish-time but stale post-publish until a human ran the manual backfill). | Single-cycle PATCH: plan-doc + manifest `1c777ed`; source-edit (auto-backfill module + runner wiring + 11 tests + release-process gates table extension + FIDRAFT capture-and-resolve + STATE/roadmap admin + HARD smoke writeup) `01e0883`; apply `527698b`; seal `39170e6`; post-seal corrective `59c3b24`; **SHIPPED PUBLIC 2026-05-10 at tag `v0.7.3` (annotated `72de0da`)** |
| v0.7.2 | release-CLI `acs-verified` gate parser-scoping fix PATCH (defect-closure for v0.6.0's shipped release-CLI substrate). Closes the cross-reference-AC-ID parser-scoping defect captured at `docs/FUTURE_IDEAS_DRAFT.md` line 232 (v0.7.1 publish-time finding). AC.READYP.1 restricts the `check_acs_verified` AC-ID scan to the plan-doc `## §4 — Acceptance criteria` section body (between the §4 heading and the next `## §<n>` boundary); cross-references in §6 (out-of-scope) / §8 (dependencies) / §11 (authority chain) / §13 (§status) are no longer flagged as missing-from-§status. Heading-recognition is permissive across the three observed forms (em-dash / period / space separators across 88 plan-docs). Absent §4 returns RED with corrective hint (no fall-back to whole-doc scan — that would silently re-introduce the defect). AC.READYP.2 reverts the two prose rewrites in v0.7.1 plan-doc that worked around the defect: §6 line restores `AC.NTU.6 deeper F-DESIGN finding`; §8 line restores `per AC.V060.7 dogfood`. AC.READYP.3 extends `framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py` with three new tests covering the scoped scan (positive ignore-cross-refs in §6 + §8; negative names-only-§4-ACs when §status incomplete; negative §4-heading-absent); 21/21 gate tests GREEN (18 existing + 3 new). AC.READYP.4 outcome-altitude probe runs `loam release v0.7.2 --dry-run` against this very plan-doc — the `acs-verified` gate returns GREEN naming 5 in-scope ACs (AC.READYP.{1-4,S}); probe documented in `docs/experiments/v0-7-2-hard-smoke.md`. Closes the second instance of the release-CLI parser-too-literal family (first was v0.7.0's §13 §status heading literal-form). | Single-cycle PATCH: plan-doc + manifest `4ab40e8`; source-edit (parser + tests + v0.7.1 plan-doc revert + FIDRAFT mark-resolved + admin) `68b7716`; apply `925e773`; seal `91ee1fe`; §status backfill + AC.READYP.4 corrective `dececf8`; publish-prep `2e91485`; **SHIPPED PUBLIC 2026-05-10 at tag `v0.7.2` (annotated `0e67135`)** |
| v0.7.1 | v1.0-readiness cleanup PATCH (defect-closure for v0.7.0's shipped outcome shape). Closes the v1.0-readiness audit at `workspace/.scratch/claude-output/v1-0-readiness-verification-2026-05-10.md`: AC.READY.1 reinstalls system `loam` binary on dispatcher's machine (RED-1 fix — every dependent loam package was editable-installed against the deleted `ivers-corp-pos-v2/` tree post-v0.5.1 split-worktrees migration); AC.READY.2 adds four missing `-e` entries to `install-from-source.txt` (`loam-amend`, `loam-pr-safety`, `loam-mode`, `per-project-pm` — RED-2 + YELLOW-3 fix at install layer; cold-venv probe verifies all 7 documented `loam <verb>` subcommands now register on a fresh install); AC.READY.3 updates STATE.md + release-roadmap.md to mark v0.6.0 + v0.7.0 SHIPPED PUBLIC with seal+tag SHAs (RED-3 fix); AC.READY.4 reconciles component count to 18 across `README.md` + `docs/architecture.md` + `docs/components/index.md` (YELLOW-1 fix — architecture.md:270 "all 15 components" → "all 18 components"); AC.READY.5 verifies `docs/components/memory.md` already clean of Graphiti residue at HEAD (YELLOW-2 was over-stated by audit; F2 surface honestly); AC.READY.6 adds `loam pr-safety` to `docs/components/index.md` (YELLOW-3 fix at doc layer); AC.READY.7 extends `docs/release-process.md` §1 pre-publish gates table with `system-binary-operational` gate (YELLOW-4 + RED-1 structural enforcement; would have caught RED-1; structural CLI implementation deferred to v0.8.0+ per FUTURE_IDEAS_DRAFT capture); AC.READY.8 outcome-altitude stranger-clone probe at `docs/experiments/v0-7-1-hard-smoke.md` (cold-clone + cold-venv + iterate every documented `loam <verb> --help`); AC.READY.9 publishes `docs/public-surface-manifest.md` (closes audit §3 forward-commitment-realism gap; lists CLI verbs + plugin entry-point groups + manifest fields + on-disk conventions + hook contracts that v1.0 commits to preserving for 6 months minimum). v0.7.1 closes the gap between "documented" and "operational" on v0.7.0's shipped surface; aggregate effect is a stranger with a fresh `git clone lukeivers/loam` can run the documented quickstart and reach every documented surface cleanly. | Single-cycle PATCH: plan-doc + manifest `7ea5fad`; source-edit (install-from-source + STATE/roadmap + architecture + components/index + release-process + public-surface-manifest + HARD smoke writeup + FUTURE_IDEAS_DRAFT capture) `d9cf905`; apply `5332f1a`; seal `cdae8ed`; §status backfill `f99cb98`; publish-prep `af73a69` + `cb93a95`; **SHIPPED PUBLIC 2026-05-10 at tag `v0.7.1` (annotated `1d08a40`)** |

**Total shipped:** 18 minor + 8 patches. v0.1.0 → v0.7.2 published. v0.3.0 ships META-FRAMEWORK foundation; v0.4.0 ships code-gen-from-objectives optimised for extend-existing-repo; v0.4.1 closes F-DESIGN-1 (multi-commit + from-scratch + tie-breaker); v0.4.2 closes F-DESIGN-2 (Test-interface load-bearing + Py-version-compat); v0.4.3 closes the FBE.7 file-based memory retrieval BM25-bypass + grep-length-bias; v0.5.0 closes the v0.1.7 subagent-personas consumption-gap on the dispatch-time surface; v0.5.1 retires the dual-tree `ivers-corp-pos-v2` + `pos-v2` branch shape via split-worktrees migration + Phase 1 first-impression cleanse rebrand; v0.6.0 ships the concrete release process (`loam release` CLI + runbook + post-ship review); v0.7.0 ships the non-tech-user surface (narration + tier picker + channel slot + memory template + corpus overrides) making v1.0 criterion #2 reachable.

**Historical SemVer mis-classification footnote (Q3 2026-05-09 ratification):** v0.4.1 + v0.4.2 were numbered as patches but ship new outcome shapes per the SemVer policy (v0.4.1: from-scratch prompt mode + multi-commit emission + tie-breaker; v0.4.2: test-interface load-bearing context + Py-version compat). Correct number for that work shape would have been v0.5.0 + v0.5.1 (or similar minor sequence). Both tags are PUBLISHED to the loam remote; renaming would force-push and break OSS consumers. Live-with the historical numbering; apply the discipline going forward (Q2 ratification: class is suggestive on roadmap; plan-author rules at build-time). v0.4.3 was correctly numbered patch (defect closure on shipped retrieval surface). v0.4.4 was numbered patch but should have been minor (renamed to v0.5.0 in this ratification — sealed local; not published; rename safe).

---

## §3 Active version

v0.4.0 + v0.4.1 + v0.4.2 + v0.4.3 ALL SHIPPED PUBLIC 2026-05-09 (loam/main advanced from `299290d8` → `15694329`; v0.4.3 tag pushed). v0.5.0 SHIPPED PUBLIC 2026-05-09 (tag `v0.5.0`, annotated `c48895e6`; subagent-personas routing + priming consumption-gap closure live). v0.5.1 SHIPPED PUBLIC 2026-05-09 (tag `v0.5.1`, annotated `e84807c4`; split-worktrees migration + Phase 1 first-impression cleanse). **v0.6.0 minor (concrete release process — `loam release` CLI verb + runbook + post-ship review) SHIPPED PUBLIC 2026-05-09** (tag `v0.6.0`, annotated `81443ef`; seal `eaf8f24`). **v0.7.0 minor (non-tech-user surface — narration + tier picker + channel slot + memory template + corpus overrides; AC.NTU.{1-7}) SHIPPED PUBLIC 2026-05-09** (tag `v0.7.0`, annotated `03060ef`; seal `1e6fc76`). v0.7.0 makes the v1.0 quality-bar criterion #2 ("one real user has shipped real software with loam") empirically reachable for the first time. **v0.7.1 PATCH (v1.0-readiness cleanup — defect-closure for v0.7.0's shipped outcome shape; closes the v1.0-readiness audit RED + YELLOW gaps) SHIPPED PUBLIC 2026-05-10** (tag `v0.7.1`, annotated `1d08a40`; seal `cdae8ed`). The §4 binary-usage observation harness (currently labeled v0.7.0 below — label-conflict; will renumber via the priority-queue restructure plan-doc). F-DESIGN-1 + F-DESIGN-2 both CLOSED at §6; FBE.7 retrieval defect CLOSED at v0.4.3; v0.1.7 subagent-personas consumption-gap CLOSED at v0.5.0; figured-out-as-I-went-publish-workflow CLOSED at v0.6.0; non-tech-user-flow-blocker CLOSED at v0.7.0; v1.0-readiness audit gaps CLOSED at v0.7.1.

---

**v0.7.3 PATCH (release-CLI post-publish auto-backfill PATCH (defect-closure for v0.6.0's release-process).) SHIPPED PUBLIC 2026-05-10** (tag `v0.7.3`, annotated `72de0da`; seal `39170e6`).

**v0.7.4 PATCH (auto-backfill completeness PATCH (defect-closure for v0.7.3's spec gaps surfaced at v0.7.3's own publish dogfood).) SHIPPED PUBLIC 2026-05-10** (tag `v0.7.4`, annotated `1cc50bf`; seal `7b9c14e`).

## §4 Mapped versions (next → v1.0.0)

**Note (2026-05-09 Q3 ratification):** the v0.5.0 label below (binary-usage observation harness) is now in conflict with the just-shipped v0.5.0 (subagent-personas routing — see §2). The §4 entries below retain their original labels pending the priority-queue restructure plan-doc (`docs/plans/release-roadmap-priority-queue-restructure.md`, uncommitted) which removes pre-assigned numbers entirely + derives them at build-commence-time per class. Until that restructure ships, the §4 numbers are placeholder; final assignment happens when each plan-doc dispatches.

**Note (2026-05-09 v0.6.0 ship):** the prior v0.4.5 entry (concrete release process) is REMOVED from §4 — work shipped at v0.6.0. The next §4 entry below was previously labeled v0.5.0 (binary-usage observation harness) and is now likely v0.7.0 final, deferred until the priority-queue restructure runs the renumbering.

---

### v0.7.0 (placeholder; was labeled v0.5.0 below) — Loam builds software from minimal input

#### Objective

> **Loam can take a binary + documentation as input, observe the binary's behavior, reverse-engineer objectives + capabilities + constraints, and produce working source code that passes a behavioral test suite.** The cold-start case — minimal inputs — is the version's deliverable.

**Class:** END-USER

This is loam against ProgramBench's full input shape: binary + docs, no source. The new component is the binary-usage observation harness.

#### Constraints

- Binary-usage observation harness sandboxes execution (Docker-shaped or equivalent safety boundary). Per programbench-loam-benchmark-v0.md §"What this is NOT" — non-trivial.
- mini-SWE-agent harness compatibility — loam's code-gen pipeline produces output compatible with ProgramBench's evaluation harness.
- ProgramBench leaderboard submission is **the action of submitting**, not a UI feature. Submission constitutes evidence of v0.5.0's outcome.

#### Acceptance criteria

- **AC.V050.1 — Binary-usage observation harness.** New component (likely under `framework/` or as a dev-sdlc plugin extension): runs binary with sample inputs, captures stdin/stdout/exit codes/file effects/network behavior, produces structured evidence-row-equivalents for the reverse-ODD pipeline. Sandboxed.
- **AC.V050.2 — Binary-feeder mode for odd-extractor.** odd-extractor accepts evidence rows from the binary harness as a third input source alongside source-files + docs.
- **AC.V050.3 — mini-SWE-agent compatibility.** Loam's code-gen output is consumable by mini-SWE-agent's evaluation harness without manual intervention.
- **AC.V050.4 — ProgramBench v0.5 submission (Variant B).** Run docs+binary feeder → reverse-ODD → ODD-grounded code-gen on 3-5 ProgramBench tasks. Score: behavioral test pass rate. Submitted to ProgramBench leaderboard. Report at `docs/experiments/programbench-v0-5-submission.md`.
- **AC.V050.5 — Outcomes-pattern stack documentation.** When users have both `claude -p` subscription AND API-keyed Outcomes access, the pattern document names how to stack ODD authoring + Outcomes runtime grading.

#### Source items

- ProgramBench × loam v0 Variant B (docs + binary-usage feeder)
- Binary-usage observation harness (programbench-loam-benchmark-v0.md §3)
- Outcomes-pattern stacking (claude conference features research)

#### Estimated AI-time

- Binary-usage observation harness: 3-6 hours (sandboxed; new component)
- mini-SWE-agent compatibility surface: 60-120 min
- ProgramBench v0 Variant B run on 3-5 tasks: 75-150 min
- Score aggregation + report + leaderboard submission: 15-30 min

**Total v0.5.0 AI-time: 5-10 hours**, midpoint **~7 hours**.

#### Dependencies

- v0.4.0 (code-gen-from-objectives wired; ProgramBench docs-only baseline established as comparison).

---

### v0.6.0 — Loam is usable by a non-technical user from fresh install through working software

#### Objective

> **A non-technical user with a fresh install can describe what they want to build, answer light-touch onboarding questions, and reach working software output without invoking technical concepts (objectives / capabilities / acceptance criteria) directly.** The translation layer (per VALUE_PROPOSITION.md) handles the methodology shape internally.

**Class:** END-USER

This is the version where loam's value proposition (helping non-tech users use AI to build software) becomes empirically demonstrable. One real non-technical user shipping real software is a 1.0.0 gate — v0.6.0 makes it possible.

#### Constraints

- No technical-concept exposure required from the user surface (user never has to type "objective" or "AC"). Internal model stays ODD-shaped per Idea 6.
- Onboarding flow scales from 8-question survey (Eric-style) to 15-question full ritual (per AC.ONBOARD.1-15) per user signal.
- Channel config (`primary_channel` slot per Idea 25) is a workspace-level setting honored by every persona reply.
- Workspace-specific corpus overrides (Idea 26) supported by all reader paths via the `_resolve_corpus_path` fall-through.

#### Acceptance criteria

- **AC.V060.1 — Light-touch education flow.** Idea 2 — ambient narration of decisions ("I made this a scheduled task because…"); user-survey-tunable verbosity; structural-not-advisory.
- **AC.V060.2 — Channel config slot.** Idea 25 — `<workspace>/.pos/channel.json` (or persona contract field); Stop-hook contributor refuses terminal-reply when `primary_channel = telegram` and the message is a user-reply.
- **AC.V060.3 — Workspace corpus override pattern.** Idea 26 — documented; one reference override (e.g., a domain-specific persona prompt) shipped as canonical example.
- **AC.V060.4 — Memory-doc skeleton template.** Idea 22 — third member of the template family (dispatch-template + plan-doc-template + memory-doc-template); `loam new-memory <slug>` orchestration parallel to `loam new-plan <slug>`.
- **AC.V060.5 — Real session-transcript demo.** TaskList item #30 — reference transcript captured + published; demonstrates a non-tech user (or proxy) reaching working software output through the V060.1 flow.
- **AC.V060.6 — Outcome-altitude AC for non-tech user flow.** End-to-end test: stranger-clone → onboarding → request → working output, no technical concepts exposed in the user surface.

#### Source items

- Idea 2 — light-touch education
- Idea 25 — workspace-level default-conversation-channel config slot
- Idea 26 — workspace-specific corpus overrides via reader fall-through
- Idea 22 — memory-doc skeleton template
- TaskList item #30 — real session-transcript demo

#### Estimated AI-time

- Idea 2 light-touch education flow: 2-4 hours
- Idea 25 channel config + Stop-hook contributor: 60-120 min
- Idea 26 documentation + canonical reference override: 30-60 min
- Idea 22 memory-doc template + new-memory orchestration: 60-90 min
- Real session-transcript capture + publish: 90-180 min (depends on user-availability)
- Outcome-altitude AC verification: 30-60 min

**Total v0.6.0 AI-time: 5-10 hours**, midpoint **~7 hours**.

#### Dependencies

- v0.5.0 (working-software output is a precondition for non-tech-user reaching working-software output).

---

### v0.7.0 — Loam's principle foundation is named and structurally enforced

#### Objective

> **Loam's design principles (the three Lenses, plus the canonical principle map at `framework/docs/design/principle-derivation-map.md`) are named primitives in the codebase, structurally enforced via hooks/skills/Stop-hook contributors, not advisory prose.** Drift from declared principles becomes a mechanical violation, not a discipline ask.

**Class:** META-FRAMEWORK

This is the structural-enforcement substrate — A1 expanded.

#### Acceptance criteria

- **AC.V070.1 — FR.1 / FR.2 / FR.3 named primitives.** TaskList items #34 / #35 / #36 (research → plan → first implementation): the three frame-rules are declared in code, not documents-only.
- **AC.V070.2 — F6 enforcement substrate.** TaskList #37 — the lens-conflict resolution four-step process becomes a Stop-hook contributor (or equivalent structural surface).
- **AC.V070.3 — Idea 1 Step 3 enforcement mechanism.** Research-plan template requires all four research questions; gate refuses to advance if any is empty.
- **AC.V070.4 — Idea 21 persona own-behaviour structural enforcement.** Stop-hook contributor scans outbound replies for permission-asking patterns + rewrites or halts.
- **AC.V070.5 — Idea 8 structural context-load gate.** Mechanical: the primary persona cannot dispatch until relevant design docs are loaded.
- **AC.V070.6 — Idea 9 workspace-slug collision detection.** Install-time + bootstrap-time checks; disambiguation knob.
- **AC.V070.7 — Design notes #26 (terminology drift detection).** Stop-hook contributor warns on dossier-claims that disagree with git log / plan-doc §14 / manifest.
- **AC.V070.8 — Meta-decision-haiku SKILL.** A SKILL that invokes Haiku as an impartial third-party decision-maker for borderline rule-application calls (plan-doc-needed; dispatch-background-vs-inline; smoke-required-or-skippable). Tightly scoped trigger list to avoid death-by-latency. Composes with the structural-enforcement substrate as the "rule applies here?" arbiter for cases too borderline for strict rubrics yet too biased for unaided persona judgment. Captured 2026-05-08 per Luke's framing — primary persona alone tends to bypass when it thinks bypass will please the owner; Haiku has no skin in the game.

#### Source items

- TaskList #34 (FR.1), #35 (FR.2), #36 (FR.3), #37 (F6)
- Idea 1 Step 3 (three-lens enforcement programme)
- Idea 21 (persona own-behaviour structural enforcement — already 4+ documented failure modes)
- Idea 8 (structural context-load gate)
- Idea 9 (workspace-slug collision detection)
- FIDRAFT structural-enforcement candidates (default-action-verb rewrite, dossier dedup, end-of-turn trait reflection)
- Meta-decision-haiku SKILL (per Luke 2026-05-08; composes with claude_print_client primitive; ~30-60 min AI-time for the SKILL build, plus calibration of the trigger list)

#### Estimated AI-time

- FR.1 / FR.2 / FR.3 / F6 (4 named-primitive amendments): 4-8 hours total
- Idea 1 Step 3 mechanism: 60-120 min
- Idea 21 Stop-hook contributor: 90-180 min
- Idea 8 structural gate: 90-180 min
- Idea 9 collision detection: 60-120 min
- Misc structural enforcement candidates: 60-120 min

**Total v0.7.0 AI-time: 9-17 hours**, midpoint **~13 hours**. Largest minor in the roadmap; structural-enforcement work touches many surfaces.

#### Dependencies

- v0.6.0 (non-tech user surface stable enough to add structural enforcement on top of).

---

### v0.8.0 — Loam catches code that contradicts its own contract

#### Objective

> **Negative-alignment detection ships: when generated or edited code drifts from the declared objective, loam surfaces the drift before the user (or CI) sees it as a defect.** Carved out of v0.2.5; deferred until calibration data exists.

**Class:** END-USER

#### Acceptance criteria

- **AC.V080.1 — Negative-alignment detection primitive.** New component (or odd-extractor extension): given a contract + a diff, classify the diff as objective-aligned / objective-orthogonal / objective-contradicting / objective-ambiguous.
- **AC.V080.2 — Calibration data.** ≥50 real-world examples (from rd-automation, jsts-playwright-app, Eric's repos, loam itself) with ground-truth labels.
- **AC.V080.3 — PR-safety gate composition.** Negative-alignment output integrates as a band-tunable signal in the PR-safety gate; production-stake profiles HARD_BLOCK on objective-contradicting; dev profile WARN.
- **AC.V080.4 — Outcome-altitude AC.** End-to-end test against real PR diffs.

#### Source items

- v0.2.6+ negative-alignment detection (deferred-from-v0.2.5)

#### Estimated AI-time

- Detection primitive: 4-8 hours
- Calibration data collection + labeling: 90-180 min
- PR-safety integration: 60-120 min
- Outcome-altitude AC: 60-120 min

**Total v0.8.0 AI-time: 7-13 hours**, midpoint **~10 hours**.

#### Dependencies

- v0.7.0 (structural enforcement substrate provides the hook surface).
- Calibration data depends on real-world repo usage (Eric, ProgramBench experiments, loam itself).

---

### v0.9.0 — Loam's deep personalization through interaction capture

#### Objective

> **Loam captures interaction patterns over time and synthesizes them into a durable user-profile artefact that informs persona behavior — without requiring the user to teach the system anything explicitly.** Per VALUE_PROPOSITION's "trust compounds in one relationship."

**Class:** END-USER

#### Acceptance criteria

- **AC.V090.1 — Interaction capture surface.** Per Idea 4 — session transcripts (or decision-relevant subset), preferences (stated or inferred), patterns observed, reactions to system outputs.
- **AC.V090.2 — Synthesis layer (separate from raw memory).** Periodic update of a structured user-profile artefact at a stable workspace path.
- **AC.V090.3 — Privacy + audit + deletion controls.** Per Idea 4's required guarantee — every interaction visible on request; user can delete.
- **AC.V090.4 — Proactive-suggestion primitive.** Per Idea 5 — surface 1-3 suggestions per week (frequency-tunable); each dismissable without cost.
- **AC.V090.5 — GLiNER2 evaluation under volume data** (CONTINGENT). Per Idea 7 — graphiti-class re-implementation with local NER for high-volume paths; scope **only if volume data justifies**.

#### Source items

- Idea 4 (deep personalization through interaction capture)
- Idea 5 (proactive suggestions grounded in user profile)
- Idea 7 (GLiNER2 — contingent on volume data; may stay backlog)

#### Estimated AI-time

- Interaction capture surface: 3-6 hours
- Synthesis layer: 2-4 hours
- Privacy + audit + deletion: 60-120 min
- Proactive-suggestion primitive: 2-4 hours
- GLiNER2 (CONTINGENT): 4-8 hours **OR backlog**

**Total v0.9.0 AI-time: 8-14 hours non-contingent**; midpoint **~11 hours**. +4-8 hours if GLiNER2 activates.

#### Dependencies

- v0.8.0 (memory FBE.7 stable + production usage long enough to have interaction volume).

---

### v0.10.0+ — Plugin suite expansion (one minor per plugin)

#### Objective shape

> **Loam's plugin ecosystem grows beyond Dev/SDLC.** Each new plugin gets its own minor version with its own objective sentence and ACs.

**Class:** END-USER

Per Idea 3 — the plugin candidates are: project/task management overlay, communications plugin, knowledge management, finance/household-ops, creative/long-form, health/habit tracking, trading/quant research, legal/compliance.

**Plugin selection discipline (per Idea 3):** do not ship all eight. Pick two or three that maximise early loam-v2 value AND prove the plugin ecosystem; let the community build the rest.

**Sequencing: highest-leverage first.** Per Luke's prior directive, project/task management overlay (the owner's named example) and communications plugin (Gmail + Calendar MCP composition) are likely candidates for v0.10.0 and v0.11.0. Final selection happens at v0.10.0 plan time, not now.

#### Estimated AI-time per plugin minor

- 8-15 hours per plugin (range per Idea 3 per-candidate complexity; some plugins like communications compose on existing MCP surface and run cheaper).

#### Dependencies

- v0.9.0 (deep-personalization surface gives plugins a richer user model to compose on).

---

### v1.0.0 — Loam is stable

#### Objective

> **All loam-documented features work as advertised; one real non-technical user has shipped real software with loam; backwards-compatibility committed for 6 months minimum; plugin contract is stable.**

**Class:** MIXED

Per `docs/release-versioning-policy.md` §"When 1.0.0 ships." This is a quality-bar event, not a calendar event.

#### Acceptance criteria (the four named criteria from the policy)

- **AC.V100.1 — All documented features work as advertised.** Stranger-clone audit.
- **AC.V100.2 — One real user has shipped real software with loam.** Not a fixture; a real maintenance-burden codebase.
- **AC.V100.3 — Backwards-compatibility commitment.** No breaking changes for 6 months minimum from 1.0.0 ship date.
- **AC.V100.4 — Plugin contract is stable.** Third-party plugins authored against 1.0.0 work through the 0.x compatibility window.

#### Estimated AI-time

- Audit + verification + tag dance: 4-8 hours.
- Real-user-shipped-real-software is **out-of-roadmap** time (depends on adoption + user availability; not AI-time).

#### Dependencies

- v0.10.0+ to whichever-version-stabilizes-the-plugin-contract.
- Real-user adoption (external dependency, not an AI-time line).

---

## §5 Backlog reference

The `maybe-someday` list. Items here are not committed to any version; they activate when their named trigger fires (or stay deferred indefinitely).

**Authoritative source:** `docs/FUTURE_IDEAS.md` (collapses to `docs/FUTURE_IDEAS.md` per v0.3.0 AC.V030.8) + `docs/BACKLOG.md`.

### Items explicitly in backlog (not roadmap)

- **Graphiti re-implementation** (Luke's explicit ruling 2026-05-08). Graphiti rip-out is roadmap (v0.3.0); re-implementation is backlog. Trigger: if FBE.7 file-backed approach proves operationally inadequate at production-stake usage.
- **Idea 7 GLiNER2** — depends on volume data; conditionally folded into v0.9.0 above. If volume data does not materialize, stays backlog.
- **Multi-LLM via OpenRouter** (formerly TaskList #52, completed as research). Contradicts the Claude Max subscription-only architecture. Backlog. Trigger: only if loam's distribution model itself changes.
- **Idea 13 sub-plan G — M-GMP plugin-shaped graphiti.** Graphiti class. Backlog with the broader graphiti category.
- **Idea 11 — amendment-chain reseal convention.** Deferred; no concrete trigger. Trigger: when a component's amendment chain feels unwieldy.
- **Idea 14 — path-mismatch comprehensive resolver.** Deferred under Idea 13's multi-workspace umbrella. Trigger: sub-plan C reactivation (multi-workspace cycle).
- **Idea 15 — `pos_paths` helper.** Folds into Idea 14 if/when activated. Trigger: a fourth consumer of `TRACKER_DB_FILENAME` arrives, OR sub-plan C reactivation, OR a third hard-coded sibling constant.
- **Idea 16 — tracker public API for source-commit rewriting.** Deferred. Trigger: a fourth tracker SQLite consumer OR the next tracker amendment touching `lifted_from`'s shape.
- **Idea 17 — dispatch-template ↔ persona-tracker composition.** Stretch. Trigger: when both surfaces stabilize AND a concrete dispatch shape benefits.
- **Idea 18 — reusable integration-test harness extraction.** Trigger: a second integration-test pattern surfaces.
- **Idea 19 — scaffold-runner observability.** Small. Trigger: sub-plan E activation OR a second silent-failure investigation OR a future scaffold-runner amendment.
- **Idea 23 — research-dispatches scope-fence pre-filter.** Trigger: next non-trivial research-then-build amendment cycle (could fold opportunistically into v0.7.0).
- **Idea 24 — Bash-tool eval-wrapper hazards.** Trigger: third Bash-tool quirk OR structural-enforcement programme adds a fifth A-amendment slot.
- **Apply FBE.7 to pos3** (TaskList #22). Operational, not loam-codebase. Backlog as operational-task; not a version line.
- **Workspace-sync follow-on Bundle α + β residuals** (post-#56 FIDRAFT entries that weren't graduated). Trigger: workspace-sync cost re-emerges as a real bottleneck.
- **BACKLOG.md "held for post-first-release" decay-retention patches.** Six items, per `decay-retention-analysis.md`. Trigger: explicit prioritization vs roadmap items.

### Borderline classifications surfaced for owner review (judgment calls; F2 RF)

These items I classified differently than the original sketch, or where the sketch didn't speak — surfaced for ruling rather than silently committed.

1. **Idea 20 (LLM-as-classifier+verifier meta-pattern).** Already operationalized in workspace-sync Bundle α.2 + memory rules. **My call: NOT a roadmap entry.** It's a meta-pattern, not a feature. Should compose into every v0.4.0+ entry that involves LLM-routed transformations. **Surfacing:** ruling needed if you want this elevated to a named v0.X primitive (a "classifier+verifier" framework component) — currently absent from the roadmap.
2. **Idea 6 (ODD as default framing inside conversations).** Already operational via v0.2.2 ODD grounding propagation foundation. **My call: NOT a separate roadmap entry; subsumed.**
3. **Idea 12 (OSS launch).** Already shipped as v0.1.0+. **My call: shipped, not roadmap.**
4. **Idea 13 (two modes + multi-workspace umbrella).** Active part shipped (sub-plans A/E/B/F); deferred parts (C/D/G) fold under multi-workspace umbrella. **My call:** the deferred parts go to backlog under the "Workspace-sync / multi-workspace" trigger. If multi-workspace becomes a stated objective for any future minor, those re-activate. Currently no minor names multi-workspace; surfacing for ruling.
5. **Idea 10 (Project rename to loam).** Already shipped. **My call: shipped, not roadmap.** Loam-aligned-name terminology consistency pass (v0.3.0 AC.V030.7) is the residual.
6. **TaskList items #8, #9, #10, #11.** I do not have the explicit text for these; they are referenced in the dispatch brief by number alone. Best-effort reading: if these correspond to FUTURE_IDEAS Ideas 8, 9, 10, 11 — they are mapped in this roadmap (#8 → v0.7.0; #9 → v0.7.0; #10 → shipped via Idea 10; #11 → backlog). **Surfacing:** if the TaskList numbers reference different items, the mapping needs correction at owner-review time.
7. **TaskList items #55, #34-37.** #55 is referenced in the dispatch brief as a discussion item; I have not seen its explicit text. #34-37 → v0.7.0 (FR.1/FR.2/FR.3/F6 named primitives). **Surfacing:** #55 needs explicit text to classify.
8. **`KNOWN_CROSS_MODE_DEBT` shrinkage.** Sketch placed it in v0.3.0; I agreed and kept it there. F2 RF signal: this is technically debt, not a forward-looking outcome — could equally well live as a perpetual lint-pass item (composes with v0.3.0 AC.V030.6). I left it as AC.V030.10 because the discrete shrinkage event is observable; alternative is to fold into AC.V030.6 lint pass. **Surfacing:** structural choice; either resolution is fine.

---

## §6 External actions (non-version work)

These items are real work but do not name a version's outcome shape. They live here so the roadmap is complete, not just version-shaped.

| Action | Trigger | Notes |
|---|---|---|
| **Boris paper push** | Captured as session-discussion item; calibration anchor (13min wall-clock at ~76 tool calls per duration-estimation rubric). | Owner-action; not AI-routed in the version path. |
| **Eric re-engagement** | Owner directive 2026-05-06 ("ignore eric, he's busy at his real job"). v0.2.5.1 closes Eric's three findings. Re-engagement is owner-driven, not version-gated. | Surface for ruling: should v0.6.0 (non-tech user) wait on Eric re-engagement, or proceed against a synthetic non-tech-user proxy? |
| **ProgramBench leaderboard submission** | v0.5.0 AC.V050.4. The act of submitting is the action. | Submission is what makes v0.5.0's outcome public. |
| **Public-remote tag pushes** | Each minor's tag push is owner-gated. v0.2.1 / v0.2.2 / v0.2.3 / v0.2.4 / v0.1.7 / v0.1.8 / v0.1.9 / v0.2.0 currently sit as local releases per their respective STATE.md entries. | Tag push is a per-minor owner action, not a roadmap line. The roadmap names what each minor delivers; the policy doc names tag dance shape. |
| **GitHub Releases marked --latest** | Per `docs/release-versioning-policy.md` §Tagging. | Per-minor; not a roadmap line. |
| **Dispatcher-side smoke verifications** | Some ACs (V025.4 outcome-altitude, V025.5 telegram-MCP isolation outcome-altitude) require parent-session verification not visible from sub-agents. | Per-minor; documented in each minor's plan-doc. |
| **Docker-equivalent / fresh-machine FBE.7 stranger-clone verification** | v0.3.0 Cycle 6 audit (`docs/v0-3-0-feature-honesty-audit.md` §4 + §9.3) closed production-CLI altitude via `framework/primary-persona/tests/test_AC_FHA_6_stranger_clone_fbe7_outcome.py`; cross-process / fresh-install / fresh-user-account altitude verification still pending. Trigger: owner brings Docker Desktop up OR runs probe on a fresh machine. | On positive verdict, AC.FHA.2 lifts from PASS-WITH-OWNER-ACTION-LINE to PASS; on negative verdict, in-cycle fix triggers at the version then active. |
| ~~**F-DESIGN-1 closure (cold-start docs-only multi-file code-gen)**~~ **CLOSED at v0.4.1** | ~~v0.4.0 Cycle 4 ProgramBench v0 baseline confirmed empirically that the v0.4.0 code-gen surface is shaped for *"extend an existing repo"*, NOT *"write from scratch given only docs"* — Variant A 56% (9/16) vs baseline 100% (16/16).~~ **Closed by v0.4.1 patch** (sealed 2026-05-09): three sub-fixes landed (multi-commit-per-task; from-scratch prompt mode with auto-detect + explicit flags; build-next tie-breaker beyond alphabetical via cluster-size + text-length signals). v0.4.1 ProgramBench re-run on the same 3 tasks shows all three structural mechanisms working in production (3 commits per task; `--- /dev/null` framing across all diffs; `formatting` correctly ranked above `error-handling` for the C4 jsonpp failure case). Aggregate Variant A pass-rate 62.5% (10/16) RELAXED vs C4's 56%. **NOTE on scope:** "ProgramBench v0" here refers to an internal experiment with 3 hand-authored toy tasks (calculator, jsonpp, wcclone). It is NOT the public ProgramBench leaderboard at programbench.com (which scores against hundreds of much-harder tasks; major providers are at 0–3% on that). The real-benchmark eval was blocked at v0.4.0 C4 (Docker daemon issue on the dev host) and is deferred to v0.5.0. This internal experiment validates the architectural mechanism on toy tasks; it does NOT establish loam's performance on real-world program-synthesis tasks. Residual gap surfaces as F-DESIGN-2 (smaller-scope; row below). | F-DESIGN-1 architectural mechanism resolved at v0.4.1. See §2 v0.4.1 row + `docs/experiments/programbench-v0-docs-only.md` v0.4.1 re-run section. |
| ~~**F-DESIGN-2 closure (compile.sh / SPEC test-interface load-bearing in from-scratch prompt)**~~ **CLOSED at v0.4.2** | ~~v0.4.1 patch's ProgramBench re-run confirmed all three F-DESIGN-1 sub-fixes work as intended in production, BUT the LLM in 3/3 v0.4.1 runs did NOT author `compile.sh` + did NOT consistently match the SPEC's CLI shape.~~ **Closed by v0.4.2 patch** (sealed 2026-05-09 LOCAL): two sub-fixes landed (Test-interface section as load-bearing context in from-scratch prompt via `_extract_test_interface_excerpt` + canonical `Test interface from SPEC:` heading + system-prompt instructions to author named build artefacts; Py-version-compat instruction-side prompt + post-process `_lower_pep604_unions` rewriting PEP-604 to `typing.Union`/`Optional`). v0.4.2 ProgramBench re-run on the same 3 tasks shows full structural closure: aggregate Variant A pass-rate 100% (16/16) STRICT vs v0.4.1's 62.5% (10/16) RELAXED + 0% STRICT. wcclone recovered 0/6 → 6/6; calculator + jsonpp tied at 3/3 + 7/7 (now STRICT). **NOTE on scope:** "ProgramBench v0" here refers to an internal experiment with 3 hand-authored toy tasks (calculator, jsonpp, wcclone). It is NOT the public ProgramBench leaderboard at programbench.com (which scores against hundreds of much-harder tasks; major providers are at 0–3% on that). The real-benchmark eval was blocked at v0.4.0 C4 (Docker daemon issue on the dev host) and is deferred to v0.5.0. This internal experiment validates the architectural mechanism on toy tasks; it does NOT establish loam's performance on real-world program-synthesis tasks. | F-DESIGN-2 architectural mechanism resolved at v0.4.2. See §2 v0.4.2 row + `docs/experiments/programbench-v0-docs-only.md` v0.4.2 re-run section. |

---

## §7 Authority + change protocol

This file overrides any prior planning doc that names a version's contents, **except** `docs/release-versioning-policy.md` (the policy doc takes precedence for versioning-rule disputes — this roadmap obeys the policy).

Updates land via amendment-cycle (the same loam amend mechanism used for all sealed components when this roadmap is tracking shipped state). Adding/removing/refining versions requires a plan-doc + manifest, not a doc-only edit, when the roadmap is being treated as a contract. Pre-v0.3.0, edits are prose-only.

When a minor ships, its §3-or-§4 entry collapses into §2 with the seal anchor. That collapse is part of the minor's seal ritual.

---

*Maintained alongside `docs/release-versioning-policy.md` and `docs/odd-semver-pinning.md` as the three durable policy + plan artefacts for loam.*
