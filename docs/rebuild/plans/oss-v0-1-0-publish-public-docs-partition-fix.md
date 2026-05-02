# Plan — M7-partition-fix (public-docs partition manifest extension)

**Status:** authored 2026-05-01 by builder.
**Predecessor:** M11a halt at `b1dc662` (post-M11a-halt §14 commit; prior HEAD `47cbea7` was M11a dispatch-1 source-commit).
**Successor candidates:** M11a re-dispatch (foldback target post-fix HEAD).
**Authority:** dispatcher directive 2026-05-01 ("M7-partition-fix — single-amendment corrective adding `docs/plugins/**` glob to M2 partition manifest's `dev_and_public` block; foldback for M11a halt F-M11a.1").
**Source surfaces (audit trail):**
- M11a dispatch-1 halt finding F-M11a.1 (`oss-v0-1-0-publish-dry-run.md` §11 D-Q.M11.4 + §15 entry).
- M7 commit `2fefd8b` ("docs(public): M7 plugins category — Dev/SDLC plugin reference") added `docs/plugins/dev-sdlc.md` per M7 plan-doc D-Q.M7.6 = (c) "separate `docs/plugins/<name>.md` category".
- M2 partition manifest at `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` lines 154-160 carries the public-docs scaffold but does NOT include a `docs/plugins/**` admission.

---

## 1. Summary / TLDR

Single-glob partition manifest edit. M7 authored `docs/plugins/dev-sdlc.md` per the (c) "separate docs/plugins/<name>.md category" decision in M7 plan-doc D-Q.M7.6, but M2's partition manifest was authored before M7 and never extended to admit the new directory. M11a dispatch-1 fired §9.9 (synthesis tool errors on partition incomplete) with the surfaced sample `docs/plugins/dev-sdlc.md`.

The fix: add `- glob: "docs/plugins/**"` to the manifest's `dev_and_public:` block alongside the existing `docs/components/**` glob (M2 manifest line 157). Pre-flight verified by dispatcher: `docs/plugins/dev-sdlc.md` carries ZERO AC.OSS.3 residuals (pos-amend / loam-amend / A1-A4 / loam-mode / docs/rebuild / pos-publish-framework-only / odd-methodology / odd-in-loam / duration-estimation-rubric) and ZERO AC.OSS.5 source-side residuals — the public-plugin-reference shape is clean for ship.

Lands before M11a re-dispatches against post-fix HEAD.

---

## 2. Owner ruling capture

Dispatcher directive 2026-05-01 locked the decision before this dispatch: **add `- glob: "docs/plugins/**"` to the `dev_and_public:` block, alongside `docs/components/**`**. No design ambiguity — the M7 D-Q.M7.6 = (c) ruling already chose the "separate `docs/plugins/<name>.md` category" shape; the fix is mechanical bookkeeping that M7 should have included but didn't (single-amendment scope, not a multi-decision research deliverable). No decisions register entries — see §11.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.OSS.3** (excluded-artefact list — public docs scaffold ships AC.OSS.3-clean). Pre-flight verified `docs/plugins/dev-sdlc.md` has zero residuals.
- **AC.OSS.5** (source-side anonymisation — public-plugin reference reads as "loam" not "rebuild of someone's machine"). Pre-flight verified.
- **AC.OSS.1** (every workspace path classifies — partition manifest completeness).

**Ladders to:** AC.OSS-M2.4 (every leaf path classifies modulo audit_excludes) → AC.OSS.6 (final scrub) → AC.PO.1 + AC.PO.2 (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`).

---

## 4. Three-lens analysis

### Lens 1 — Claude-leverage-first
N/A — pure manifest bookkeeping; no Claude-native primitive in scope. The synthesis tool itself already composes around `git ls-tree` + the manifest classifier; this fix is a single line in the manifest's authored data.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** the `docs/plugins/<name>.md` category reduces translation burden — a user asking "what plugins ship with loam?" gets a flat browsable catalog at `docs/plugins/`. The manifest fix unblocks shipping that surface; no value reduction.
- **Harness test:** the public synthesis surface gains a documented plugin-catalog shape future v0.x plugins compose into (`docs/plugins/<new-plugin>.md` per M7's chosen pattern).

### Lens 3 — ODD authoring
Outcome-shape AC.M7-fix.1: synthesis tool runs cleanly post-fix; AC.M7-fix.2: `docs/plugins/dev-sdlc.md` appears in synthesis output. Method (single glob entry alongside the existing precedent) is builder's call within the dispatch's locked decision.

---

## 5. Acceptance criteria

AC family **AC.M7-fix.\*** (collision-safe — neither M7 nor M2 uses this prefix; verified via `grep -rE "AC\.M7-fix" docs/`). Each AC ladders to AC.OSS-M2.4 + AC.OSS.1 → AC.OSS.6 → AC.PO.1 + AC.PO.2.

| AC ID | Outcome | Verification |
|---|---|---|
| AC.M7-fix.1 | Partition manifest's `dev_and_public:` block contains `- glob: "docs/plugins/**"` alongside the existing `docs/components/**` glob entry. | `grep -F 'docs/plugins/**' framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` returns the new line under `dev_and_public:`. |
| AC.M7-fix.2 | Synthesis tool runs cleanly against post-fix HEAD (no `SynthesisError`, no `partition incomplete` error); `docs/plugins/dev-sdlc.md` appears in the synthesised tree (i.e. classification works in practice). | Smoke check: `.venv/bin/python -m loam.publish_framework_only.cli --repo /Users/lukeivers/ivers-corp-pos-v2 --source HEAD` exits 0; post-synth `git ls-tree -r refs/heads/framework-only -- docs/plugins/dev-sdlc.md` returns the blob. |
| AC.M7-fix.S | Sealed-component fence held: `git diff --name-only BASELINE..SEAL_COMMIT` produces only paths under `framework/tools/pos-publish-framework-only/` (structural fence; admitted via `universal_paths.prefixes`) + `framework/hands-off-lifecycle/tests/SEAL_COMMIT*` (HOL no-op narrative anchor per M2 + post-m6-partition-realignment precedent — `pos-publish-framework-only` has no `test_no_sealed_amendments.py` so HOL anchors the sealed-component cycle) + universal-paths. | HOL's `test_cross_cutting.py` passes against new BASELINE `b1dc662`; HOL's `frozen_baseline: true` (H19 pin per amendment #23) verified unchanged. |

---

## 6. Sequencing

1. Plan-doc commit (this file + manifest YAML) — sub-plan + amendment manifest in one commit per recent precedent (M1c-corrective shape uses one commit for the plan + amendment-manifest pair; we author them as a single commit too).
2. Feature commit — single-line edit to `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
3. `loam amend apply` commit.
4. Seal commit.
5. §14 SHA backfill (post-seal — populated by builder, not a separate commit).

Lands BEFORE M11a re-dispatch. Post-fix HEAD becomes the M11a-2 source-commit target.

---

## 7. Hard constraints

- Single structural fence: `framework/tools/pos-publish-framework-only/` (admitted via `universal_paths.prefixes` per M2 + post-m6-partition-realignment precedent). HOL anchors the sealed-component cycle as no-op narrative anchor only (sidecar bump + SEAL_COMMIT.notes file; NO behaviour edits to HOL). No other framework components edited.
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.M7-fix.*` (collision-safe; verified).
- Auto-memory MEMORY.md NOT touched.
- Synthesis smoke check post-fix is sanity-only — not part of M11a's full sweep (that's M11a-2's job).

---

## 8. Out of scope

- The full M11a sweep (AC.M11a.1..6) — that re-dispatches against post-fix HEAD per D-Q.M11.4 (no auto-foldback at M11a; foldback amendments authored sealed; M11a re-runs).
- Any other partition gaps that may surface during M11a-2 — separate corrective amendments per D-Q.M11.4.
- Edits to the M7 plan-doc retroactively (the M7 plan-doc's D-Q.M7.6 ruling was correct; the omission was at M2-manifest-extension-time, not M7-design-time).
- `docs/plugins/<future-plugin>.md` entries — the glob admits any future plugin reference under the same pattern; no per-plugin entries needed.
- Edits to `dev-mode-manifest.yaml` (separate manifest, separate concern).

---

## 9. Halt-and-surface

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not silently extend) on:

- HT-1: Synthesis tool still errors after the fix. Means more than one classification gap; halt and surface specific cause.
- HT-2: `docs/plugins/dev-sdlc.md` carries AC.OSS.3 or AC.OSS.5 residuals the dispatcher's pre-flight grep missed (could happen if the pre-flight was too narrow). Halt before sealing; surface findings; expand fix scope or escalate.
- HT-3: Partition manifest edit breaks YAML parsing (e.g. wrong indentation under `dev_and_public:`). Halt; surface YAML error.
- HT-4: Pre-existing test fails post-fix in `framework/tools/pos-publish-framework-only/tests/`. Halt; surface specific failure.
- HT-5: ODD §2.5 violation in surrounding code/docs encountered during research. Surface for FIDRAFT; do NOT expand scope.
- HT-6: Wall-time exceeds estimate by >50% (30 min midpoint → halt at ~45 min). Surface progress; let dispatcher rule continuation.

---

## 10. Risks

- **YAML indentation errors** — addressed by post-edit YAML parse verification before commit (synthesis tool's `partition.load_manifest` parses the YAML; smoke check runs the full pipeline).
- **Glob over-matching** — `docs/plugins/**` admits everything under that directory recursively. Currently only `dev-sdlc.md` exists; future additions inherit the same `dev_and_public` class. This matches the existing `docs/components/**` precedent's semantics; not a new risk.
- **Classification precedence** — `dev_and_public` is checked AFTER `excluded_from_publish`, `dev_only`, and `public_only` per the manifest's documented precedence (lines 46-53). No `dev_only` glob currently shadows `docs/plugins/**`; verified by grep. A future `dev_only` entry over `docs/plugins/**` would correctly take precedence; not a regression.

---

## 11. Decisions register

None — all decisions locked by dispatcher directive (see §2). The single locked decision (add `- glob: "docs/plugins/**"` to `dev_and_public:`) is captured in §5 AC.M7-fix.1.

---

## 12. Halt-and-surface findings during plan authoring

None at plan-authoring time. The dispatcher's pre-flight verified ZERO AC.OSS.3 + AC.OSS.5 residuals against the canonical-on-host source-of-truth set; manifest pattern verified at lines 154-160; M11a halt narrative + RCA verified at `oss-v0-1-0-publish-dry-run.md` §11 + §15. No new findings.

Findings encountered during build land in §14 method-decision register.

---

## 13. References

- M11a dispatch-1 halt narrative: `docs/rebuild/plans/oss-v0-1-0-publish-dry-run.md` §11 D-Q.M11.4 + §15.
- M11a sweep report (full halt narrative): `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md`.
- M7 plan-doc (D-Q.M7.6 = (c) plugin-category ruling): `docs/rebuild/plans/oss-v0-1-0-publish-public-docs.md`.
- M-FBM precedent (sealed-component-cycle amendment shape): `docs/rebuild/plans/oss-v0-1-0-publish-memory-pivot.md`.
- M1c-corrective precedent (similar small-scope corrective): `docs/rebuild/plans/oss-v0-1-0-publish-rename-1c-corrective.md`.
- Programme master plan: `docs/rebuild/plans/oss-v0-1-0-publish.md`.
- Partition manifest under edit: `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- Synthesis tool source: `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/{synth.py,partition.py,substitution.py,cli.py}`.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-build.M7-fix.0 — AI-time actuals

(populated post-build)

### D-build.M7-fix.1 — Manifest edit + synthesis smoke check actuals

(populated post-build)

### Commit SHAs

- BASELINE: `b1dc662` — `docs(plans): M11a dispatch-1 halt — partition manifest gap surfaced`
- Plan + manifest commit: `<TBD>`
- Feature commit: `<TBD>`
- Apply commit: `<TBD>`
- Seal commit: `<TBD>`
