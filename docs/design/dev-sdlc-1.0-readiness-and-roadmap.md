> **OWNER-DIRECTIVE SUPERSEDES THE AUDIENCE FORK (Telegram 13383–13386, 2026-06-01).**
> This review (below) assessed dev-sdlc as it exists today and recommended **Audience A
> (internal build-machinery)** with high confidence. Luke's directive overrides that target:
> dev-sdlc 1.0 is to become **the build-and-publish substrate the loam primary persona relies
> on to make + ship the things it does for the END USER** — at every scale (scripts, widgets,
> small tools, not just big Python builds), with the shared-artefact quality floors
> (`docs/design/shared-artefact-quality-catalogue.md`) baked in. So dev-sdlc 1.0 now has TWO
> layers: **Layer 1** = the internal-machinery correctness/hygiene fixes this review found
> (necessary foundation — accurate as-is); **Layer 2** = the GENERALIZATION of dev-sdlc's good-
> build principles + seal/publish discipline into the persona's engine for building +
> publishing arbitrary end-user artefacts. This review is Layer 1; Layer 2 is designed in the
> follow-on `dev-sdlc-build-publish-substrate-and-plugin-strategy` pass. The review's
> "don't invent an external goal" caution is answered: the owner is deliberately declaring the
> bigger goal, eyes open.

---

# dev-sdlc → 1.0: Readiness Assessment + Roadmap

**Authored:** 2026-06-01 · **WD:** /Users/lukeivers/loam (main / loam-1.0-candidate)
**Doc class:** research + roadmap (no code, no amend)
**Trigger:** Owner directive TG 13381 — loam-main is 1.0; what does dev-sdlc need to reach a clean, integrated 1.0?

## Principles applied
Lens 1 (Claude-leverage) · Lens 2 (translation + harness) · Lens 3 (ODD self-held) ·
Lens 7 (Ruthless Feedback — findings #3/#4 corrected against dispatch framing) ·
claim-or-cite (every tool-behavior claim verified against code) · information-trust-ordering.

## Executive summary (non-technical)
dev-sdlc is the internal toolkit that governs how loam builds itself: the methodology
(ODD), the amendment-cycle ritual, and the `loam amend` seal/apply tooling that keeps
every change to a "sealed" component fenced and auditable. As internal machinery it is in
good shape: coherent methodology, tooling that holds itself to the same ODD standard it
enforces, real end-to-end (not stubbed) tests, fence pinned green. The honest internal-1.0
gap is small: two genuine correctness bugs in the seal machinery plus one fence that has
accreted so many exceptions it no longer protects anything. (Per the header, the owner's
1.0 target is bigger than internal machinery — see the Layer-2 follow-on.)

## The framing fork (review's recommendation: A internal — SUPERSEDED by owner, see header)
**A — internal build-machinery.** Behind the dev-mode partition (`dev-mode-manifest.yaml:142-181`);
docs addressed to loam contributors (`docs/odd-in-loam.md:4`); no external-onboarding surface;
not published to any index. The review recommended A. The owner (13383-386) overrides to the
build-publish-substrate target; A remains the accurate description of *today's* artefact and
the foundation Layer 2 generalizes from.

## §2 The four folded-in findings — verified dispositions
### #1 Seal-fence + partition-audit blind to git-tracked status — VERIFIED, systemic, MUST-FIX
`test_no_sealed_amendments.py:74-78` runs `git diff --name-only BASELINE..seal` and checks
prefix membership only — never `git ls-files`. `loam_mode/audit.py:121` walks `os.walk`
on-disk regardless of tracked status. A gitignored runtime-required source file appears in
neither → passes seal, fails on clone. Fix: add a `git ls-files` set-membership assertion to
the seal-test pattern + the partition audit. Size S. **HIGHEST LEVERAGE.**

### #2 Install-integration validates against origin/main, not commit-under-seal — VERIFIED, MUST-FIX
`new_workspace.py:213,355` re-point to `origin/main`; `test_AC_LIVI_1…py:50,69` bootstraps
`--from LOAM_ROOT` then lands on published HEAD. Any amendment fixing the install recipe is
circular. Fix: parametrize bootstrap source-ref to the commit-under-test. Size S-M.

### #3 Seal ref "un-advanced" — MISCHARACTERIZED; real gap narrower, SHOULD-FIX
The seal commit IS created and HEAD IS advanced (`seal.py:920-944` commits then reads
`seal_sha` from new HEAD; `test_seal.py:730` asserts it). The actual gap: no explicit
`assert post_seal_HEAD == seal_sha` invariant inside `seal.py` production code (trusts
`git commit` exit code; invariant only in tests). Add the production self-check. Size S.
(Note: this corrects the dispatcher's finding #3 — the ref DID advance on the live seal this
session; the manual ff was belt-and-suspenders, not a required recovery.)

### #4 Parallel-build number collision — LARGELY OBSOLETE, NICE-TO-HAVE (doc-note)
Amendment numbers are deprecated in schema v3: `manifest.number` is optional + operator-
supplied (`manifest.py:159-165`). No tool codepath computes "next number," so no tool-level
collision. Residual risk is the operator-side walk-forward BASELINE convention only.
(Note: this re-frames the dispatcher's finding #4 — the #162 collision this session was an
operator-convention artifact, not a tool defect; the renumber-to-#163 was the right manual fix.)

## §3 New findings (not in the dispatch)
- **Seal-fence prefix bloat → non-fence (MUST-FIX).** `allowed_prefixes` has ~75 entries incl.
  bare `"framework/"`, `"plugins/"`, `"docs/"` (`test_no_sealed_amendments.py:120,143-144`).
  The fence admits ~the whole tree; its protection is largely illusory. Root cause: the
  widening tool (`seal_diff.py:widen_binding`) is append-only with no pruning. Size M.
- **Stale line-refs (SHOULD-FIX).** `amendment-cycle.md:14` + `loam-amend-cycle/SKILL.md:57`
  cite `apply.py:158`; the binding is at `apply.py:269`. Docs-match-behavior drift.
- **Narrative count drift (SHOULD-FIX).** "thirteen sealed components" (`odd-in-loam.md:31`,
  SKILL:9) vs 15 in `dev-mode-manifest.yaml:57-71`.
- **Version-coherence (SHOULD-FIX for a 1.0 cut).** Plugin 0.14.0 vs sub-packages 0.1.8/0.1.9;
  a 1.0 needs an explicit versioning story across the plugin + its sub-packages.

## §4 Closeable autonomy-queue items (already shipped — verified)
- "Commit source edits before apply" methodology step: SHIPPED (`amendment-cycle.md:14` + SKILL
  step 4; enforced as a soft warning by `apply.py:_unstaged_outside_partition`).
- "Tier-1 retroactive plan-doc sweep hardening": SHIPPED (`test_AC_T1RS_SWEEP.py` green).

## §5 Prioritized roadmap to internal-1.0 (Layer 1)
**(a) Must-fix:** 1. tracked-status assertion in seal-fence + audit (#1, ~S, highest leverage);
2. install-test source-ref parametrization (#2, ~S-M); 3. prune the bloated seal-fence to a
real fence (~M). **(b) Should-fix:** 4. `post_seal_HEAD == seal_sha` production assertion (~S);
5. fix stale `apply.py:158` line-refs (~XS); 6. reconcile "thirteen"→15 (~XS); 7. version-
coherence story (~S). **(c) Nice-to-have/post-1.0:** 8. Lens-1: compose the tracked-status +
partition check as a Claude Code pre-seal hook (tool-time, not pytest-only); 9. doc-note the
operator-side BASELINE-collision convention.

## §6 Honest doubts (F2)
- Fence-prune size (#3-new) is PLAUSIBLE-banded: the edit is simple but determining the
  *minimal* correct prefix set requires replaying which amendments legitimately needed each
  entry — that analysis is the real cost.
- The review did not execute the suite (read-only). "Fence pinned green" / "outcome-altitude
  smokes present" are VERIFIED by reading the pinned SEAL_COMMIT + test bodies, not a fresh run.
  A HARD-smoke run is the confirming step before the 1.0 cut.

## §7 Inventory corrections
`per-project-pm` is a FRAMEWORK-tree tool (`framework/per-project-pm/`), not a dev-sdlc plugin
tool. `odd-extractor`/`pr-safety` are plugin sub-packages (top-level under `plugins/dev-sdlc/`),
not under `tools/`.

## §8 Provenance
seal.py (920-944), apply.py (213, 269), test_no_sealed_amendments.py (74-78, 120, 143-144),
loam_mode/audit.py (121), new_workspace.py (213, 355), test_AC_LIVI_1 (50, 69), manifest.py
(159-165), amendment-cycle.md (14), loam-amend-cycle/SKILL.md (9, 57), odd-in-loam.md (4, 31),
dev-mode-manifest.yaml (57-71, 142-181), pyproject.toml (7), tests/SEAL_COMMIT, README.md
(74-93). All read 2026-06-01.
