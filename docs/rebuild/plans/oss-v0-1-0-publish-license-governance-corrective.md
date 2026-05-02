# Plan — M8-corrective (HC#4 byte-content rebaseline post-Apache-header insertion)

**Status:** authored 2026-05-01 by builder.
**Predecessor:** M7-partition-fix halt at `f09a261` (post-HT-4 §14 commit; apply commit `4291971` already landed; seal blocked by pre-existing M8 regression on `b1dc662`).
**Successor candidates:** M7-partition-fix re-seal (Phase B of this dispatch); thereafter M11a re-dispatch.
**Authority:** dispatcher directive 2026-05-01 (Path A clean-closure recommended by M7-partition-fix dispatch agent + locked by main session per autonomy directive).
**Source surfaces (audit trail):**
- M7-partition-fix halt narrative `<workspace>/.scratch/claude-output/m7-partition-fix-halt-ht4-surface.md` (HSF#1).
- M7-partition-fix plan-doc §16 HSF#1 + §14 D-build.M7-fix.3.
- M8 commit `6bef03b` ("feat(public): M8 license-governance — Apache headers on runtime .py + SECURITY.md tightening") inserted Apache-2.0 license headers across 700 runtime .py files.
- HOL byte-content invariant `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` HC#4 captures pinned SHA-256 for 15 representative files (5 each from primary-persona / workspace-bootstrap / scope-of-work).

---

## 1. Summary / TLDR

ODD §4 in-band retire-and-rebaseline of HC#4 byte-content invariant. M8 (`6bef03b`) inserted a 14-line Apache-2.0 header at the top of every runtime .py file across 15 dev_and_public components — a legitimate byte-content change driven by AC.OSS.4 (license-governance scaffold) — but did NOT perform the corresponding HC#4 retire-and-rebaseline of the captured SHAs in HOL's `test_d1_byte_content_match.py`. 13 of the test's 15 sample files (all the .py samples; the 2 pyproject.toml samples were unchanged) now diverge.

The fix: recompute SHA-256 for the 13 .py samples on current HEAD, update the constants in the test file, and add narrative comments naming M8 Apache-header insertion as the legitimate rebaseline source. Per `feedback_loose_AC_text_fix_AC_not_implementation` analog: when the implementation matches AC intent (Apache-header insertion was the AC.OSS.4 directive) and the test's pinned bytes diverge for a legitimate reason, rebaseline the test, not re-author the impl.

Lands BEFORE M7-partition-fix re-seal (Phase B of this dispatch).

---

## 2. Owner ruling capture

Dispatcher directive 2026-05-01 locked the decision before this dispatch: **Path A clean-closure** — author M8-corrective amendment (single-component fence: `framework/hands-off-lifecycle/`), then re-attempt M7-partition-fix's seal commit. No design ambiguity — the rebaseline is mechanical bookkeeping that M8 should have included but didn't (single-amendment scope, not a multi-decision research deliverable). No decisions register entries — see §11.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.OSS.4** (license-governance scaffold — Apache headers on runtime .py files). M8 satisfied AC.OSS.4 byte-shape; this corrective closes the missed HC#4 retire that should have ridden along.
- **AC.OSS-M9.S** (HOL byte-content invariant continuity post-D-migration). HC#4 is the regression target this corrective preserves.

**Ladders to:** AC.OSS.4 → AC.OSS.6 (final scrub) → AC.PO.1 + AC.PO.2 (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`).

---

## 4. Three-lens analysis

### Lens 1 — Claude-leverage-first
N/A — pure test-constant rebaseline; no Claude-native primitive in scope. The HC#4 invariant itself is bookkeeping.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** unchanged. The HC#4 invariant continues to bind the harness's structural promise that `git mv` + intentional-edits-only changes don't silently corrupt content. Rebaseline preserves the binding's health.
- **Harness test:** the rebaseline keeps HC#4 functional as a regression target for future content-edits during pure-rename windows. Without rebaseline, the test stays red and loses signal value (a noisy test gets ignored).

### Lens 3 — ODD authoring
Outcome-shape ACs only. AC.M8-corrective.1: SHA-256 constants for the 13 .py samples match current bytes. AC.M8-corrective.2: HOL's `test_d1_byte_content_match.py` runs green. AC.M8-corrective.S: sealed-component fence held. Method (recompute via `hashlib.sha256` and edit constants) is builder's call within the locked decision.

---

## 5. Acceptance criteria

AC family **AC.M8-corrective.\*** (collision-safe — neither M8 nor M-FBM uses this prefix; verified via `grep -rE "AC\.M8-corrective" docs/`). Each AC ladders to AC.OSS.4 + AC.OSS-M9.S → AC.OSS.6 → AC.PO.1 + AC.PO.2.

| AC ID | Outcome | Verification |
|---|---|---|
| AC.M8-corrective.1 | The 13 .py-sample SHA-256 constants in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py::_SAMPLE_FILES` match the current bytes of those files post-M8. | Per-file recomputation: `python -c "import hashlib;print(hashlib.sha256(open('<path>','rb').read()).hexdigest())"` matches the new constant. |
| AC.M8-corrective.2 | `pytest framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` passes 15/15 (13 parameterised cases + the 2 unchanged pyproject.toml entries + the structural ≥15-samples check). | Direct pytest invocation. |
| AC.M8-corrective.S | Sealed-component fence held: `git diff --name-only BASELINE..SEAL_COMMIT` produces only paths under `framework/hands-off-lifecycle/` + universal-paths. | HOL's seal-test invariant verified post-seal. |

---

## 6. Sequencing

1. Plan-doc commit (this file) — sub-plan only; manifest commits separately.
2. Feature commit — edit `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` (13 SHA-256 constants + ODD §4 in-band retire-and-rebaseline comment naming M8).
3. Amendment manifest commit (`oss-v0-1-0-publish-license-governance-corrective.manifest.yaml`).
4. `loam amend apply` commit.
5. Seal commit.

Lands BEFORE M7-partition-fix re-seal (Phase B of dispatch). Phase B re-runs `loam amend seal` against the existing M7-partition-fix apply `4291971`; the HOL byte-content test will pass cleanly post-Phase-A.

---

## 7. Hard constraints

- Single sealed-component fence: `framework/hands-off-lifecycle/` (HOL is its own anchor here — the byte-content test IS HOL's; not a no-op narrative anchor pattern).
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.M8-corrective.*` (collision-safe; verified).
- Auto-memory MEMORY.md NOT touched.
- ODD §4 in-band retire-and-rebaseline narrative MUST appear in: this plan-doc, the feature commit message, AND the test file's docstring/inline comments (per `feedback_loose_AC_text_fix_AC_not_implementation` analog: when the implementation matches AC intent and the test's pinned bytes diverge for a legitimate reason — Apache-header insertion driven by AC.OSS.4 — rebaseline the test, not re-author the impl). Reference precedent: M-FBM rebaselined the same file's primary-persona constants (in-place inline comments naming the rebaseline source).
- HOL `frozen_baseline: true` per amendment #23 H19 pin — preserved unchanged in this manifest.

---

## 8. Out of scope

- Re-running the M8 Apache-header script (M8 already executed it across 700 files; the bytes are correct).
- Re-baselining the 2 pyproject.toml samples (their bytes were not touched by M8 and their SHAs still match — verified during plan-authoring).
- Edits to other HOL test files (only `test_d1_byte_content_match.py` is affected).
- Touching M8's commit (`6bef03b` stays in audit trail; this corrective is an additive followup commit chain).
- M7-partition-fix re-seal — handled in Phase B of this dispatch as a separate seal command.
- Surfacing M8 as ODD-violation for retire (M8's structural intent satisfied AC.OSS.4; the omission was the missed HC#4 retire, which this corrective closes).

---

## 9. Halt-and-surface

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not silently extend) on:

- HT-1: Phase A SHA-256 recomputation finds files among the 13 with bytes that DIDN'T change post-M8 (would mean M8-regression diagnosis was wrong; investigate root cause before continuing).
- HT-2: Phase A reveals MORE than 13 byte-content mismatches (additional cross-component invariant drift the original surfacing missed).
- HT-3: Any pre-existing test outside the named 13 fails post-Phase-A (means the rebaseline introduced unintended drift or there's another latent regression).
- HT-4: An ODD §2.5 violation appears in surrounding code/docs encountered during research. Surface for FIDRAFT; do NOT expand scope.
- HT-5: Phase B re-seal mechanism doesn't accept re-running against old apply `4291971` — surface for dispatcher ruling.
- HT-6: Wall-time exceeds estimate by >50% (30 min midpoint → halt at ~45 min). Surface progress; let dispatcher rule continuation.

---

## 10. Risks

- **SHA recomputation drift between plan-author and feature commit.** Risk: someone edits a sampled file between recomputation and constant-write. Mitigation: recompute and edit in the same commit window; verify post-commit pytest passes.
- **Hidden cross-component invariant drift.** If other tests outside HOL's `test_d1_byte_content_match.py` also captured SHAs of M8-touched files, those would fail under different invariants. Mitigation: cross-component seal-diff sweep at seal-time will catch any such regressions; HT-3 covers it explicitly.
- **YAML manifest indentation errors** — addressed by `loam amend validate` pre-apply.

---

## 11. Decisions register

None — all decisions locked by dispatcher directive (see §2). The single locked decision (recompute the 13 SHAs, update constants, add ODD §4 in-band retire-and-rebaseline narrative naming M8) is captured in §5 AC.M8-corrective.1.

---

## 12. Halt-and-surface findings during plan authoring

**HSF-author#1 — pyproject.toml samples unaffected (resolved at plan-author-time).** The HC#4 sample list contains 15 entries; M8 did NOT add Apache headers to `pyproject.toml` files (those carry `[build-system]` as line 1, no header inserted). Empirical verification at plan-author-time: `framework/primary-persona/pyproject.toml` SHA `0181ab99319a19bd70f262d030d60f0fe74ab325d833706ba33c1bc656cb1ca2` matches the pinned constant (M1e bump, no further change); `framework/scope-of-work/pyproject.toml` SHA `1f97cf7a380d1876b416b8a88f06264398296ae176c797ccb0695d8bc6f481cc` likewise matches. Confirms the dispatch's "13 files" claim and bounds the rebaseline scope.

**HSF-author#2 — exactly 13 .py mismatches; no additional drift surfaced.** Empirical pytest run at plan-author-time: `13 failed, 3 passed`. Failures match the 13 named .py samples exactly. The 3 passes = 2 pyproject.toml samples + the structural ≥15-samples check. Bounds confirmed; HT-2 not fired.

Findings encountered during build land in §14 method-decision register.

---

## 13. References

- M7-partition-fix halt narrative: `<workspace>/.scratch/claude-output/m7-partition-fix-halt-ht4-surface.md`.
- M7-partition-fix plan-doc (precedent shape): `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-partition-fix.md`.
- M8 commit (Apache-header insertion source): `6bef03b` ("feat(public): M8 license-governance — Apache headers on runtime .py + SECURITY.md tightening").
- M-FBM precedent (same file rebaselined for primary-persona/__init__.py + session_start_emitter.py): `docs/rebuild/plans/oss-v0-1-0-publish-memory-pivot.md` + commit `5db5db4`.
- M1c-corrective precedent (similar small-scope corrective): `docs/rebuild/plans/oss-v0-1-0-publish-rename-1c-corrective.md`.
- HC#4 invariant test: `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py`.
- ODD §4 retire-and-rebaseline pattern: `docs/odd-methodology.md`.
- `feedback_loose_AC_text_fix_AC_not_implementation` (rebaseline-not-reauthor pattern).
- Programme master plan: `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 row M8.

---

## 14. Method-decision register (post-build)

### D-build.M8c.0 — AI-time actuals

(populated post-build)

### Commit SHAs

- Amendment commit: `9159ffd291f91a51254bcac06f6fe17a5ac55988` —
  `chore(loam-amend-apply): loam amend apply for M8-corrective`
- Seal commit: `527109139519b8c8c18ecb19b314977754b12cda` —
  `chore(seals): oss-v0-1-0-publish-license-governance-corrective — hands-off-lifecycle at 9159ffd`
