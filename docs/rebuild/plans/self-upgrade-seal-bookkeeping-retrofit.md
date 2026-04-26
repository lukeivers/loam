# Self-upgrade seal-bookkeeping retrofit — plan

Dev-discipline territory per CLAUDE.md §2.5 — no v1.x spec objective; pure seal-bookkeeping infrastructure parity work. **Hybrid shape:** uses a `pos-amend` manifest + seal ritual (this is the retrofit that bootstraps self-upgrade INTO the seal-bookkeeping pipeline) but advances no product surface. Plan-before-code per the dev CDC; corrective new commits land the change. Mirrors the memory-system retrofit (amendment #8) and the graceful-degradation + observability-aggregator retrofit (`7d462e3`, 2026-04-22).

**Status:** plan (pre-dispatch). 2026-04-26.
**Working directory:** /Users/lukeivers/ivers-corp-pos-v2/
**Companions:** - `memory-system/tests/test_no_sealed_amendments.py` (the precedent pattern)
- `docs/rebuild/plans/seal-retrofit-graceful-degradation-observability-aggregator.md`
  (the previous retrofit precedent)

**Ancestor record:** - **Self-upgrade phase-2 sealing** — `STATE.md` records seal time
  `2026-04-19 14:12`. Last commit touching `self-upgrade/` at that
  time was `9e15379` (D10 bundled docs); subsequent commits
  `7711249` (cross-suite pytest fix) and `9373444` (linux removal,
  amendment #10) also touched the surface.
- **Memory-system retrofit** (amendment #8, 2026-04-22) — the
  canonical pattern this retrofit mirrors.
- **Graceful-degradation + observability-aggregator retrofit**
  (chore commit `7d462e3`, 2026-04-22) — the same-shape precedent
  for components sealed without bookkeeping.
- **Foundation-audit F2** (commit `af99046`) — earliest precedent;
  cost-governance + reversibility-primitive retrofit.
- **Previous-BB attempt** — clause-(h) BB-build halted before code,
  leaving untracked
  `docs/rebuild/plans/self-upgrade-clause-h-llm-merge.{md,builder-plan.md,vars.yaml}`.
  Surfaced halt state: self-upgrade has no seal-bookkeeping
  infrastructure; Luke ruled 2026-04-26 to split (option 2) —
  retrofit-alone-first lands as this amendment, clause-(h) BB-feat
  re-dispatches against post-retrofit tip.

**Research:** (no separate research doc — pattern fully prescribed by precedent
artefacts named in §15)


---

## 1. Summary / TLDR

self-upgrade was sealed 2026-04-19 14:12 (per `docs/rebuild/STATE.md`)
but the seal-ritual never landed the bookkeeping infrastructure that
every other sealed component carries. Today self-upgrade has no
`tests/SEAL_COMMIT` sidecar, no `tests/test_no_sealed_amendments.py`
diff-scope guard, and no `seals/` narrative directory — so a future
amendment touching `self-upgrade/` cannot be enforced through the
standard seal-diff window the other 12 sealed components rely on.

This amendment retrofits that infrastructure exactly per the memory-
system precedent (amendment #8) and the
graceful-degradation/observability-aggregator precedent
(`7d462e3`, 2026-04-22). It adds three artefacts:

1. `self-upgrade/tests/test_no_sealed_amendments.py` — mirrors
   memory-system's pattern (B23 pinning + B20 diff-scope test).
2. `self-upgrade/tests/SEAL_COMMIT` — sidecar carrying the
   authoritative seal SHA.
3. `self-upgrade/seals/.gitkeep` — narrative directory for future
   `pos-amend seal` runs to write `SEAL_COMMIT.<slug>` files into.

No source edits to `self-upgrade/src/`. This is a retrofit, not a
feature change — and explicitly NOT clause-(h) LLM-merge work, which
is the BB-feat amendment that gets dispatched after this lands.
Amendment #53.


---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

This amendment has **no v1.x spec objective**. Per CLAUDE.md §2.5
"dev-discipline territory" carve-out, seal-bookkeeping infrastructure
is tooling that supports the sealed-amendment CDC; it does not advance
any v1.x acceptance criterion. Its purpose is mechanical: bring
self-upgrade up to parity with the other 12 sealed components so the
next functional amendment touching `self-upgrade/` (BB-feat, clause-
(h) LLM-merge) can be enforced through the standard seal-diff
pipeline.

Precedent for spec-objective-free seal-bookkeeping retrofits:
- foundation-audit F2 (commit `af99046`) — retrofitted
  cost-governance + reversibility-primitive.
- chore commit `7d462e3` (2026-04-22) — retrofitted
  graceful-degradation + observability-aggregator.
- chore commit `5c59e9a` and follow-ons across amendments #19+ —
  BASELINE bumps land as part of every amendment cycle now.

This amendment is the same shape: pure infrastructure parity, no
product surface change.


---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

This is meta-work on the harness's own enforcement substrate; no
Claude-native primitive composes here. The seal-diff test is a
pytest-driven `git diff` invocation — same infrastructure all peer
components already use. `pos-amend apply` and `pos-amend seal`
(the harness CLI added in amendment #22) are the Claude-aware
primitives this composes on; this retrofit unblocks their use
against the `self-upgrade/` surface.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test (AC.PO.1):** indirect — once retrofitted,
  persona-issued amendments touching `self-upgrade/` get the
  deterministic seal-diff scope guard the persona relies on for
  every other sealed component. The persona's "did this amendment
  stay in scope?" question becomes uniformly answerable across all
  14 sealed components instead of 13.
- **Harness test (AC.PO.2):** direct — `pos-amend apply` and
  `pos-amend seal` are toolkit surfaces the persona invokes; this
  retrofit makes them productive against `self-upgrade/` for the
  first time.

### Lens 3 — ODD authoring

ACs are outcome-shaped (the artefacts exist + the diff window is
enforceable + the existing self-upgrade test suite stays green).
No method prescribed in AC text. Behaviour count = 3 (one per
artefact); each maps to one AC.


---

## 4. Acceptance criteria (SU-sb — dev-discipline plan)

- **AC.SU-sb.1** — `self-upgrade/tests/test_no_sealed_amendments.py`
  exists, mirrors the memory-system / graceful-degradation pattern
  (B23 pattern-pinning test + B20 diff-scope test routing through
  `_seal_commit()`), and passes under
  `cd self-upgrade && ../.venv/bin/pytest tests/test_no_sealed_amendments.py -v`.

- **AC.SU-sb.2** — `self-upgrade/tests/SEAL_COMMIT` exists as a
  sidecar carrying the authoritative seal SHA (initial value = the
  pre-amendment tip; advanced to the seal commit SHA by
  `pos-amend seal`).

- **AC.SU-sb.3** — `self-upgrade/seals/` exists as a directory
  (placeholder `.gitkeep` initially) ready to receive
  `SEAL_COMMIT.<slug>` narrative files written by future
  `pos-amend seal` runs (per the pattern established at
  `primary-persona/seals/`, `workspace-bootstrap/seals/`,
  `objective-tracker/seals/`, `telegram-interface/seals/`,
  `hands-off-lifecycle/seals/`).

- **AC.SU-sb.S** — full self-upgrade test suite remains green
  (`cd self-upgrade && ../.venv/bin/pytest tests/ -q` — 120 tests
  pre-amendment + 2 new tests = 122 tests post-amendment, all
  passing). Cross-component sweep across all 14 sealed components
  stays green post-seal.


---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | self-upgrade ships test_no_sealed_amendments.py mirroring the memory-system pattern | AC.SU-sb.1 |
| 2 | self-upgrade ships tests/SEAL_COMMIT sidecar with authoritative seal SHA | AC.SU-sb.2 |
| 3 | self-upgrade ships seals/ narrative directory ready for future pos-amend seal writes | AC.SU-sb.3 |
| (S) | suite stay-green sentinel | AC.SU-sb.S |


---

## 6. Hard constraints

1. **No `git commit --amend`.** Corrective new commits only — per
   `feedback_no_amend_in_agent_dispatches`.
2. **Scope fence: `self-upgrade/tests/` and `self-upgrade/seals/`
   ONLY.** Zero edits to `self-upgrade/src/` — this is retrofit-only,
   not a feature change. The `seals/` directory creation lives
   under the same component umbrella.
3. **No clause-(h) work.** Clause-(h) LLM-merge is BB-feat, the
   SEPARATE amendment dispatched after this lands. Any clause-(h)
   authoring (plan-doc edits, source edits, test edits) belongs to
   that amendment, not this one.
4. **Plan-before-code.** This plan exists; builder writes a
   builder-plan to
   `docs/rebuild/plans/self-upgrade-seal-bookkeeping-retrofit.builder-plan.md`
   before any code lands.
5. **No new third-party dependency.** Stdlib only — the test file
   uses `subprocess` + `pathlib`, identical to memory-system's
   pattern.
6. **Mirror the memory-system pattern exactly.** B23 (BASELINE
   constant + SEAL_COMMIT sidecar + diff routes via
   `_seal_commit()` helper, never hardcoded HEAD). Do not introduce
   a new shape.
7. **Stale clause-h artefacts are out of scope.** The previous-BB
   untracked files
   (`docs/rebuild/plans/self-upgrade-clause-h-llm-merge.{md,builder-plan.md,vars.yaml}`)
   stay untracked; this amendment does NOT include them in any
   commit.


---

## 7. Out of scope (explicit)

- Clause-(h) LLM-merge implementation (BB-feat, separate amendment).
- Any source edits to `self-upgrade/src/`.
- Reviving / editing the previous-BB stale clause-h plan-doc and
  builder-plan (untracked from the prior attempt; left for
  BB-feat dispatch to resolve).
- Adding seal narrative content beyond the `.gitkeep` placeholder
  (the first real `SEAL_COMMIT.<slug>` narrative lands with the
  first functional amendment touching `self-upgrade/` — i.e.
  BB-feat / clause-(h) — written by `pos-amend seal` automatically).
- Cross-component allowed-prefix widening beyond `self-upgrade/`
  (this amendment's seal-diff window is exactly self-upgrade/ +
  universal admissions).


---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md (already done at plan
   authoring).
2. Read memory-system retrofit precedent
   (`memory-system/tests/test_no_sealed_amendments.py` lines 1-22 +
   `memory-system/tests/SEAL_COMMIT` contents) plus
   `seal-retrofit-graceful-degradation-observability-aggregator.md`.
3. Author this plan-doc + manifest YAML + builder-plan.
4. Verify pre-amendment narrow-scope test count
   (`cd self-upgrade && ../.venv/bin/pytest tests/ -q`).
5. Land the three retrofit artefacts (test file, SEAL_COMMIT
   sidecar, seals/.gitkeep).
6. Run `pos-amend apply --dry-run docs/rebuild/plans/self-upgrade-seal-bookkeeping-retrofit.manifest.yaml`
   — green gate before commit.
7. Conventional amendment commit
   (`feat(self-upgrade): seal-bookkeeping retrofit (amendment #53,
   AC.SU-sb.1–AC.SU-sb.S)`). No `--amend`.
8. Post-amendment narrow-scope tests (now 122 tests).
9. `pos-amend seal --plan-doc docs/rebuild/plans/self-upgrade-seal-bookkeeping-retrofit.md`
   — runs touched-component + cross-component sweep, advances
   sidecar to seal SHA, creates deterministic seal commit, verifies
   post-seal `apply --dry-run` green, appends Commit-SHAs subsection
   to plan §14.
10. Cross-component seal-diff sweep across all 14 sealed components
    stays green.


---

## 9. Bookkeeping surface

This is a sealed-component retrofit (component being retrofitted
into the seal-bookkeeping pipeline for the first time). Manifest:
`docs/rebuild/plans/self-upgrade-seal-bookkeeping-retrofit.manifest.yaml`.

Manifest sketch:

```yaml
schema_version: 1
amendment:
  number: 53
  slug: self-upgrade-seal-bookkeeping-retrofit
  title: "self-upgrade seal-bookkeeping retrofit"
baseline: edf6429   # current HEAD = pre-amendment tip
plan: docs/rebuild/plans/self-upgrade-seal-bookkeeping-retrofit.md
seal_description: "self-upgrade seal-bookkeeping retrofit"
components:
  - name: self-upgrade
    seal_test: self-upgrade/tests/test_no_sealed_amendments.py
    sidecar: self-upgrade/tests/SEAL_COMMIT
    frozen_baseline: false
universal_paths:
  prefixes:
    - docs/rebuild/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md
narrative:
  target: self-upgrade/seals/SEAL_COMMIT.seal-bookkeeping-retrofit
  body: |
    # Amendment #53 — self-upgrade seal-bookkeeping retrofit
    ...
```

BASELINE in the new test file initializes at `edf6429` (the
pre-amendment tip — current HEAD at plan authoring). SEAL_COMMIT
sidecar starts at `edf6429`; `pos-amend seal` advances both per
the standard ritual. Initial diff window
`edf6429..edf6429` is empty — passes trivially. After the
amendment commit lands, `apply --dry-run` widens the in-test
BASELINE only; SEAL_COMMIT advances at seal time.


---

## 10. Halt triggers (builder halts + signals owner)

1. Cross-component scope expansion beyond `self-upgrade/tests/` +
   `self-upgrade/seals/` + universal admissions. Halt.
2. Any source file under `self-upgrade/src/` is touched. Halt
   immediately — this is retrofit-only.
3. `pos-amend apply --dry-run` reports a missing admission or
   unexpected diff content. Halt; inspect.
4. Existing self-upgrade test fails post-amendment. Halt; diagnose
   before proceeding.
5. Cross-component seal-diff sweep RED post-seal on a sealed
   component this amendment did not touch. Halt; surface.
6. Wall-time exceeds 90 minutes. Halt with current state.
7. ODD violation observed in surrounding code/docs (per
   `feedback_subagent_odd_violation_halt`). Halt; do NOT extend a
   violating surface.
8. The previous-BB clause-h artefacts get accidentally staged
   (plan-doc, builder-plan, vars). Halt — they're explicitly stale
   for THIS dispatch.


---

## 11. Decisions remaining for the owner to rule on

No genuinely uncertain decisions. The shape is mechanically
prescribed by:

- **D-1 (locked):** mirror memory-system's
  `test_no_sealed_amendments.py` pattern exactly (B23 + B20).
  Precedent: every retrofit since 2026-04-22 (`7d462e3`).
- **D-2 (locked):** BASELINE initial = current HEAD `edf6429`
  (pre-amendment tip). Same pattern as agent-dispatch-as-scope-
  wrapper manifest baseline.
- **D-3 (locked):** allowed_prefixes minimal = `("self-upgrade/",
  "data/", "docs/rebuild/plans/")` plus universal admissions
  via `pos-amend apply`. Mirror the memory-system shape;
  additional prefixes get added later by future amendments touching
  self-upgrade as cross-component partners.
- **D-4 (locked):** seals directory placeholder = `.gitkeep`. Same
  pattern peer components use.
- **D-5 (locked):** seal_description = "self-upgrade seal-
  bookkeeping retrofit". The seal commit message template uses
  this string.


---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| (none — all method choices mechanically prescribed by precedent) | | |


---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface any
ODD violation observed in surrounding code/docs.

**(none observed during plan authoring.)** The previous-BB stale
artefacts (clause-h plan + builder-plan + vars) are noted for the
reader but not violations — the dispatcher's directive explicitly
leaves them out-of-scope for this amendment.


---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.x method choices to the builder within the
ACs' outcome bounds. This section is populated post-build.

### D-build.x — (placeholder for the build agent's method choices)

### Test breakdown

(placeholder)

### Backwards-compat verification

(placeholder)

### Commit SHAs

- Amendment commit: `636549fc025d007ce0a9c29205a0dd05dba80946` —
  `feat(self-upgrade): seal-bookkeeping retrofit (amendment #53, AC.SU-sb.1–AC.SU-sb.S)`
- Seal commit: `10961758722efd4099fe1a6f31e5d4a0f1f85af5` —
  `chore(seals): self-upgrade seal-bookkeeping retrofit — self-upgrade at 636549f`
### Commit SHAs

(populated by `pos-amend seal --plan-doc <this-file> ...` after build, or appended manually for dev-discipline plans)

### Dependents cleared to dispatch

(placeholder)

---

## 15. References

- CLAUDE.md (project + global) — §2.5 dev-discipline carve-out;
  output conventions; design lenses.
- `docs/odd-methodology.md`, `docs/odd-in-pos.md` — outcome-shaped
  AC authoring + behaviour-count discipline.
- `docs/rebuild/STATE.md` — self-upgrade seal time.
- `docs/rebuild/VALUE_PROPOSITION.md` — AC.PO.1 / AC.PO.2 trace.
- `docs/rebuild/FUTURE_IDEAS.md` — none added; out of scope.
- `memory-system/tests/test_no_sealed_amendments.py` — precedent.
- `memory-system/tests/SEAL_COMMIT` — precedent sidecar shape.
- `docs/rebuild/plans/seal-retrofit-graceful-degradation-observability-aggregator.md`
  — earlier retrofit precedent.
- `docs/rebuild/plans/agent-dispatch-as-scope-wrapper.manifest.yaml`
  — current manifest YAML shape this amendment's manifest mirrors.

