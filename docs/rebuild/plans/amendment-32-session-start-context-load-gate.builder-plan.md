# Builder plan — Amendment #32 session-start context-load gate (D8)

**Amendment number:** 32 (next sequential after #31 workspace-bootstrap-plist-path).
**BASELINE (pre-amendment tip):** `3844f2f92f44a244ae31b44cd969ecc6fbf31430` — the #31 seal commit.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-24 (build dispatch).
**Plan ref:** `docs/rebuild/plans/amendment-32-session-start-context-load-gate.md` (authored spec).
**Research doc:** `docs/rebuild/plans/research/session-start-context-load-gate-research.md`.

This builder plan maps every planned file/test to an explicit AC ID
(D8.1–D8.5 or D8.S) per the plan's §3 constraint 7 (ODD §2.5 bidirectional
audit). It does not author ACs — those live in the amendment plan doc.

---

## 1. Pre-amendment preparation (bookkeeping only)

1. Rename the plan file to include the assigned amendment number:
   `amendment-session-start-context-load-gate.md` →
   `amendment-32-session-start-context-load-gate.md`. (Already done.)
2. Capture BASELINE SHA (see header). No code edits yet.
3. Run `primary-persona/` full pytest to confirm pre-touch green.
4. Establish the primary-persona seal sidecar surface inside the
   primary-persona fence per plan §8 + D7's noted sidecar absence:
   - Create `primary-persona/tests/test_no_sealed_amendments.py` with
     `BASELINE = "3844f2f92f44a244ae31b44cd969ecc6fbf31430"`,
     `SEAL_COMMIT_PATH`, `_seal_commit()`, `allowed_prefixes` tuple,
     `allowed_files` set — mirrors the sealed-component pattern.
   - Create `primary-persona/tests/SEAL_COMMIT` holding BASELINE for
     the empty-diff-window on amendment commit.
   - Create `primary-persona/seals/` directory for the narrative target.
   These land in the primary-persona fence and are admitted by plan §3
   constraint 1 + plan §8 "the builder establishes the sidecar surface
   inside primary-persona/ itself — this remains inside the §3
   constraint-2 fence."

---

## 2. Source implementation map

All new source lives under `primary-persona/src/`. No edits to existing
source files except the package `__init__.py` to export the new primitive.

| New file | ACs satisfied | Purpose |
|---|---|---|
| `primary-persona/src/context_composer.py` | D8.1, D8.2, D8.3, D8.5 | The `ComposedContextPayload` primitive — Pydantic model, `on_session_start` / `on_user_prompt_submit` entry points, contributor-registration surface, 10 k-char cap enforcement at construction. |
| `primary-persona/src/session_start_gate.py` | D8.1, D8.2 | The session-level payload assembly logic — corpus-path listing from `CLAUDE.md`, in-flight amendment discovery, service-state probe, cost-headroom lookup, `corpus_gate_state` sentinel computation. Degrades gracefully: `loaded` / `partial` / `missing` sentinel + structured-diagnostic block. |

The composer enforces the 10 k-char cap **at construction** — the
Pydantic `model_validator(mode="after")` raises if the serialised
`additionalContext` string exceeds 10,000 characters. Per plan §3
constraint 4.

Both entry points return a payload whose `.additional_context_text`
attribute is the str emitted to Claude Code. The hook script is not
authored here (supervisor composition is out of scope per plan §6).

---

## 3. AC-test file map (strict 1:1)

Each AC gets its own test module. Test functions inside each module
are named `test_D8_<n>_<slug>`. The six ACs map to six files:

| File | ACs |
|---|---|
| `primary-persona/tests/test_D8_1_session_start_emission.py` | D8.1 — baseline emission fields |
| `primary-persona/tests/test_D8_2_graceful_refusal.py` | D8.2 — missing corpus, sentinel + diagnostic, session proceeds |
| `primary-persona/tests/test_D8_3_user_prompt_submit_dispatch.py` | D8.3 — turn entry point, construction-refusal when no session payload, contributor registration |
| `primary-persona/tests/test_D8_4_cold_start_budget.py` | D8.4 — p95 ≤ 500 ms over 10 runs warm; single-shot under 20 s on forced timeout |
| `primary-persona/tests/test_D8_5_shared_composer_contract.py` | D8.5 — two entry points, 10 k-char cap structural at construction, synthetic contributor observable end-to-end |
| `primary-persona/tests/test_no_sealed_amendments.py` | D8.S — seal-diff discipline (also the sidecar-pattern test per B23) |

No test exercises more than one AC's outcome. A single failure names
exactly one AC. Test-fixture helpers land in `primary-persona/tests/`
(per plan §3 test-fixture-helper admission).

---

## 4. Bookkeeping artefacts

1. `docs/rebuild/plans/amendment-32-session-start-context-load-gate.manifest.yaml`
   — pos-amend manifest:
   - `schema_version: 1`
   - `amendment: {number: 32, slug: session-start-context-load-gate, title: "primary-persona session-start context-load gate (D8)"}`
   - `baseline: 3844f2f92f44a244ae31b44cd969ecc6fbf31430`
   - `plan: docs/rebuild/plans/amendment-32-session-start-context-load-gate.md`
   - `components:` single entry — `primary-persona`, `seal_test: primary-persona/tests/test_no_sealed_amendments.py`, `sidecar: primary-persona/tests/SEAL_COMMIT`, `frozen_baseline: false`.
   - `universal_paths.prefixes: [docs/rebuild/plans/]`
   - `universal_paths.files: [CLAUDE.md, docs/odd-in-pos.md, docs/odd-methodology.md, docs/rebuild/FUTURE_IDEAS.md]`
   - `narrative.target: primary-persona/seals/SEAL_COMMIT.session-start-context-load-gate`
   - `narrative.body:` narrative prose per plan §8.

2. `primary-persona/seals/SEAL_COMMIT.session-start-context-load-gate` —
   created at seal time by `pos-amend seal`.

3. `docs/rebuild/FUTURE_IDEAS.md` Idea 8 forwarding reference
   (per plan §8 retirement note). Performed at seal via narrative body
   or a post-seal edit.

---

## 5. Verification ordering

1. Full `primary-persona/` pytest green after all source + test lands,
   BEFORE `pos-amend apply --dry-run`.
2. `pos-amend apply --dry-run docs/rebuild/plans/amendment-32-…manifest.yaml` → exit 0.
3. Seal-diff-only pytest across every other sealed component (untouched
   discipline per amendment-dispatch CDC speedup).
4. Amendment commit — NEW commit, never `--amend`.
5. `pos-amend seal docs/rebuild/plans/amendment-32-…manifest.yaml` →
   advances sidecar to amendment SHA, appends narrative.
6. Seal commit.
7. Post-seal seal-diff-only pytest across every sealed component
   (amendment-dispatch CDC: post-seal verification is seal-diff-only).
8. Post-seal `pos-amend apply --dry-run` must be exit 0 per amendment #22.

---

## 6. Bidirectional AC audit (ODD §2.5)

Forward — each code path maps to an AC:

- `ComposedContextPayload` Pydantic model → D8.5 (contract), D8.1/D8.2/D8.3 (used by both entry points)
- `on_session_start` → D8.1 (baseline), D8.2 (graceful refusal)
- `on_user_prompt_submit` → D8.3 (dispatch + refusal-on-no-session), D8.5 (contributor bound)
- 10 k-char cap `model_validator` → D8.5 (structural cap)
- Corpus-path discovery (reads `CLAUDE.md` session-start-discipline) → D8.1 (a), D8.2 (missing-file enumeration)
- Amendment-glob discovery (`docs/rebuild/plans/amendment-*.md`) → D8.1 (b)
- Service-state probe → D8.1 (c)
- Cost-headroom readout → D8.1 (d)
- `corpus_gate_state` sentinel → D8.1 (e), D8.2 (sentinel value)
- Recent first-run + generation marker → D8.1 (f)
- Sidecar + seal-test → D8.S

Reverse — each AC maps to specific code paths:

- D8.1 → corpus-path discovery, amendment-glob, service probe, cost readout, sentinel, first-run marker, length assertion
- D8.2 → missing-path enumeration, sentinel transitions to `partial`/`missing`, diagnostic block assembly, turn-proceeds path
- D8.3 → `on_user_prompt_submit`, construction-refusal-without-session, registration mechanism
- D8.4 → p95 loop, forced-timeout single-shot
- D8.5 → dual-entry-point surface, 10 k-char model validator, synthetic contributor round-trip
- D8.S → seal-diff test + sidecar

No orphan code paths. No orphan ACs.

---

## 7. Halt-trigger restatement

Halt if any of plan §7 triggers fire (ODD break, cross-component scope,
owner-ambiguity, budget exceeded, 10k cap breach by realistic baseline,
hook contract drift, pos-amend dry-run failure). Record and surface.
