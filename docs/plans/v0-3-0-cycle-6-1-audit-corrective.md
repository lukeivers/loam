# v0.3.0 Cycle 6.1 — audit-corrective (close audit findings #1+#2 in-cycle, carry #3 to release-roadmap §6)

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-08 (Sonnet, single-agent plan-author + builder).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.3.0 Cycle 6 SEALED — apply `f8beeaa`, seal `0734ea9`, §14 backfill `bfd0671`. Audit at `docs/v0-3-0-feature-honesty-audit.md` surfaced three findings; recommendations were Path A / Path A / Path B. Owner ratified all three recommendations autonomously per AUTONOMY (recommendation IS the decision) + test-against-operational-objective (v0.3.0's outcome IS feature-honesty; in-cycle close honors objective).

**Authority:**
- `docs/v0-3-0-feature-honesty-audit.md` §9 (the three owner-ruling recommendations).
- `docs/plans/v0-3-0-master-plan.md` §3 C7 placeholder (sub-cycle 6.1 inserted between C6 and C7).

**BASELINE (pre-build tip):** to be set to the source-edit feat commit when the build commit lands.

---

## §1 — Outcome shape (the "why")

C6's audit produced 100% capability-vs-reality coverage at named-surface altitude but surfaced three findings that block the audit's own "100% match standard":

1. **Component-count "fifteen" docs-drift** (audit §3.2). README.md / architecture.md / components/index.md all carry "fifteen" wording while the named-capability count is honest under one reading and drifted under another (`memory` documented but no `framework/memory/` directory; `loam-init` + `per-project-pm` real components but no `docs/components/` reference page).
2. **`docs/components/memory.md` post-C2 reframe** (audit §3.3). The doc still references "Graphiti as v0.1.x plugin" — per Luke 2026-05-08, graphiti is post-v0.1.0 backlog (not v0.1.x plugin). FBE.7 file-backed memory is canonical now; doc should reflect that.
3. **Docker-equivalent stranger-clone gap** (audit §4 / §9.3). Tractable substitute closed the production-CLI altitude; three real gaps (cross-process / fresh-install / fresh-user-account) require Docker daemon-up or a fresh machine. Owner ruled Path B — carry as known-gap entry on `docs/release-roadmap.md` §6 owner-action-line.

C6.1 closes all three. C7 then ships clean.

**Why a sub-cycle, not C7:** C7 is reserved in the master plan for the v0.3.0 SHIP cycle (final release-roadmap collapse, STATE.md update, cross-AC confirmation). Folding three doc-corrective findings into C7 inflates SHIP scope; a tight sub-cycle isolates the corrective work and preserves the SHIP cycle's narrow ratify-and-ship shape.

---

## §2 — ACs — `AC.FHA1.*` (locked, 6 ACs)

ODD §2.5: every line of code, every branch, every test maps to a named AC. AC family identifier `FHA1` per the audit's "feature honesty audit corrective #1" framing (FHA = original audit; FHA1 = corrective sub-cycle).

- **AC.FHA1.1 — `docs/components/loam-init.md` exists with the standard shape (What it does / How to invoke / Observable surface / Stable surfaces).**
  - Surface: NEW file `docs/components/loam-init.md`.
  - Content: matches the shape of `docs/components/workspace-bootstrap.md` and `docs/components/orchestrator.md`. Sources: `framework/loam-init/README.md` + `framework/loam-init/pyproject.toml` + `framework/loam-init/src/loam/loam_init/cli.py`.
  - Test: file existence; markdown header structure (`## What it does`, `## How to invoke`, `## Observable surface`, `## Stable surfaces`); `loam init --help` invocation matches the doc's invocation text.

- **AC.FHA1.2 — `docs/components/per-project-pm.md` exists with the standard shape.**
  - Surface: NEW file `docs/components/per-project-pm.md`.
  - Content: same shape match. Sources: `framework/per-project-pm/README.md` + `framework/per-project-pm/pyproject.toml`. The doc reflects the v0.1.7 Cycle 4 surface (state-of-world, decision-queue, surface_next_question, record_response, batch surfacing, M-FBM boundary).
  - Test: file existence; same structural shape as AC.FHA1.1; references resolve.

- **AC.FHA1.3 — Component-count wording resolved across README.md + architecture.md + components/index.md.**
  - Surface: doc edits in three files. Resolution: "sixteen" with `memory`'s location-inside-primary-persona footnote (per audit §3.2 "Path A — DOCS-REWRITE" recommendation, sub-option "rewrite the count to sixteen and add memory's location-inside-primary-persona note").
  - Edits:
    - `README.md` L76: "Fifteen runtime components plus the Dev/SDLC plugin" → "Sixteen runtime components plus the Dev/SDLC plugin" (and L93: "for all fifteen" → "for all sixteen").
    - `docs/components/index.md` L3: "fifteen runtime components" → "sixteen runtime components" + add 2 rows to the table (`loam-init`, `per-project-pm`) + footnote on `memory` row noting "implementation lives inside `primary-persona/`".
    - `docs/architecture.md` L113-115: section heading + body. "The 15 runtime components" → "The 16 runtime components"; "fifteen Python components" → "sixteen Python components"; add `loam-init` + `per-project-pm` to the grouped table (likely under "Composition + lifecycle" since both register CLI subcommands and bootstrap-shape contributions).
  - Test: zero remaining occurrences of "fifteen" or "15 runtime" across the three target files; "sixteen" + memory footnote present; cross-references resolve (every `[name](name.md)` link in components/index.md resolves to a real file).

- **AC.FHA1.4 — `docs/components/memory.md` rewritten — no "Graphiti as v0.1.x plugin" framing; FBE.7 file-backed memory documented as canonical.**
  - Surface: rewrite of the `## What it does` paragraph removing the v0.1.x graphiti-plugin sentence; rewrite of `## Stable surfaces` removing the `MemoryProvider` Protocol mention if it points to graphiti-memory specifically; replace with the production reality (file-backed memory client per AC.MFBM.5; queue/worker/Stop persistence / SessionStart + UPS retrieval).
  - Sources: `framework/primary-persona/src/loam/primary_persona/file_memory.py` + `memory_write_queue.py` + `memory_write_worker.py` + `stop_emitter.py` + `session_start_emitter.py` (all named in audit §3.3 + §3.5).
  - The "graphiti is post-v0.1.0 backlog" reframing should land as: no mention of graphiti as v0.1.x plugin; if graphiti is mentioned at all, it's named explicitly as "post-v0.1.0 backlog" with a release-roadmap reference. Cleanest path is to drop graphiti from the doc entirely; the substrate-pluggability story can name "alternative substrates can be contributed" without naming graphiti specifically.
  - Test: zero occurrences of "v0.1.x plugin" / "graphiti" (case-insensitive) in `docs/components/memory.md`; the doc still names FBE.7 / file-backed memory as canonical; cross-references resolve.

- **AC.FHA1.5 — `docs/release-roadmap.md` §6 has an owner-action-line entry naming the Docker stranger-clone gap.**
  - Surface: append a row to the §6 table (or sub-section if appropriate) naming: "Docker-equivalent or fresh-machine FBE.7 stranger-clone verification — production-CLI altitude substitute passed in C6 (`framework/primary-persona/tests/test_AC_FHA_6_stranger_clone_fbe7_outcome.py`); cross-process / fresh-install / fresh-user-account altitude verification needs Docker daemon up or fresh-machine probe; trigger: owner brings Docker Desktop up OR runs probe on fresh machine; on positive verdict, AC.FHA.2 lifts from PASS-WITH-OWNER-ACTION-LINE to PASS."
  - Test: row present; references resolve (the test path exists in the tree).

- **AC.FHA1.6 (outcome-altitude) — Re-running the audit's named-capability ↔ sealed-surface map produces 100% match.**
  - Outcome-altitude per `feedback_test_outcome_altitude_required`: this AC is the cycle's reviewer-perspective probe.
  - Surface: re-walk every claim in `docs/v0-3-0-feature-honesty-audit.md` §3 against post-C6.1 doc state. Two prior **DOCS-DRIFT** verdicts (component-count + memory.md graphiti framing) become **PASS** post-C6.1. Two prior **PASS** verdicts stay PASS. The §3.2 surfaced gap (`loam-init` + `per-project-pm` undocumented) closes via AC.FHA1.1+.2.
  - The outcome-altitude probe runs against the production docs (no test pre-arrangement). A reviewer reading the docs after C6.1 lands sees no drift between claimed capabilities and reality.
  - Method: an inline checklist in this plan-doc's §6 Smoke — every audit §3 row re-evaluated; if any row stays non-PASS, halt-and-surface (escalates to C6.2 or carry).
  - Test: structural — checklist in §6 executed at seal-time; result captured in build report.

---

## §3 — Build sequence (single-agent, single-cycle)

This corrective amendment is single-agent: plan-author + builder are the same Sonnet run per dispatch. Build sequence:

1. **Source-edit feat commit (BASELINE).** Author the two NEW component docs (`docs/components/loam-init.md` + `docs/components/per-project-pm.md`); update components/index.md + README.md + architecture.md count wording; rewrite memory.md; append Docker-gap row to release-roadmap.md §6. Single commit subject: `docs(v0.3.0): Cycle 6.1 audit-corrective — close FHA findings #1+#2 in-cycle (BASELINE)`.
2. **Manifest+apply commit.** `loam amend apply <this manifest>` produces a single merged commit per AC.DPS1.6 schema-v3.
3. **Seal commit.** `loam amend seal --plan-doc <abs path> <this manifest>` produces deterministic short-form seal commit per AC.DPS2 schema-v3 + a §14 backfill follow-up commit per AC.D-sa.7 if applicable.

**No `git --amend`. No push. Single semantic commit per stage.** Critical: C5 had inadvertent --amend mid-build — recovered. C6 stayed clean. DO NOT regress. If --amend is reached for, STOP — author a NEW corrective commit instead.

---

## §4 — Touched components

**Doc-only cycle.** No source code changes. Touched paths:

- `docs/components/loam-init.md` (NEW)
- `docs/components/per-project-pm.md` (NEW)
- `docs/components/index.md` (UPDATE — count wording + 2 rows + memory footnote)
- `docs/components/memory.md` (REWRITE — drop graphiti framing; document FBE.7 as canonical)
- `README.md` (UPDATE — "fifteen" → "sixteen" in 2 occurrences)
- `docs/architecture.md` (UPDATE — "15"/"fifteen" → "16"/"sixteen" + add 2 components to grouped table)
- `docs/release-roadmap.md` (UPDATE — §6 Docker-gap row appended)
- `docs/plans/v0-3-0-cycle-6-1-audit-corrective.md` (NEW — this plan-doc)
- `docs/plans/v0-3-0-cycle-6-1-audit-corrective.manifest.yaml` (NEW)

**Sealed-component bookkeeping owner:** dev-sdlc (cross-cutting doc cycle; same precedent as C1-C6).

---

## §5 — Halt-and-surface triggers

- WD mismatch — first tool call must be `cd /Users/lukeivers/ivers-corp-pos-v2 && pwd`.
- Cycle scope expansion — anything beyond the 9 touched paths above is out of scope; surface and halt.
- Fourth doc carries the "fifteen" count with different framing not anticipated above — surface for ruling.
- `--amend` reach — STOP, author NEW corrective commit instead.
- Push or tag attempt — out of scope.
- AC.FHA1.6 reviewer perspective surfaces a NEW drift the audit missed — escalate to C6.2 or document as carry.

---

## §6 — Smoke (AC.FHA1.6 outcome-altitude checklist)

Reviewer-perspective re-walk of audit §3 against post-C6.1 state. Each row scored PASS / DEFECT / RESIDUE / DOCS-DRIFT.

| Audit §3 row | Pre-C6.1 verdict | Post-C6.1 expected verdict | Verification |
|---|---|---|---|
| §3.1 CLI verbs (6 entries) | PASS × 5 + DOCS-DRIFT × 1 (`pr-safety` undocumented; benign) | unchanged — out of C6.1 scope (audit marked benign) | grep `pr-safety` in user-facing docs; if still absent, verdict unchanged |
| §3.2 README "Fifteen" | DOCS-DRIFT | **PASS** | grep README L76; expect "Sixteen" |
| §3.2 components/index.md "fifteen" | DOCS-DRIFT + RESIDUE | **PASS** | grep index L3; expect "sixteen" + 2 new rows |
| §3.2 architecture.md "15" / "fifteen" | DOCS-DRIFT | **PASS** | grep architecture.md; expect "16" / "sixteen" |
| §3.3 memory.md "session-bridging substrate" | RESIDUE (resolved by §3.5 honest framing) | unchanged — claim still honest post-rewrite | re-read memory.md after rewrite |
| §3.3 memory.md "Graphiti as v0.1.x plugin" | DOCS-DRIFT | **PASS** | grep memory.md for "graphiti" / "v0.1.x"; expect zero matches |
| §3.4 hook surfaces (4 entries) | PASS × 4 | unchanged | no doc edits in scope |
| §3.5 file-based memory promises (3 entries) | PASS × 3 | unchanged (memory.md rewrite preserves these claims) | re-read memory.md; promises still present |
| §3.6 plugin extension protocol (2 entries) | PASS × 2 | unchanged | no doc edits in scope |
| §3.7 onboarding ritual (2 entries) | PASS × 2 | unchanged | no doc edits in scope |
| §3.8 architecture-doc claims (2 entries) | DOCS-DRIFT × 1 + PASS × 1 | DOCS-DRIFT row → **PASS** (covered by §3.2 fix) | grep architecture.md again |

**Expected post-C6.1 result:** 100% PASS across §3 rows in scope of C6.1, with the one out-of-scope DOCS-DRIFT (§3.1 `pr-safety` benign) noted in the build report as deferred.

If the reviewer-perspective walk surfaces a NEW row not enumerated above (drift the audit missed), halt-and-surface — escalates to C6.2 or recorded as known-gap in release-roadmap §6.

---

## §7 — Authority + change protocol

This plan-doc is sub-cycle 6.1 under v0.3.0; supersedes any informal C7 docs-cleanup expectation. Owner-ratified ahead of dispatch via AUTONOMY (recommendation IS the decision) per the audit §9 recommendations.

When the cycle seals, this plan-doc receives a §14 backfill if applicable (recording apply / seal SHAs).
