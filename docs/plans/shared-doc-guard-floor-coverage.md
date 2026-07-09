# Shared-doc guard-floor coverage (release-seal near-miss audit, Class C — cycle 2 of 3)

**WD:** `/Users/lukeivers/loam` (canonical). **Doc class:** amendment plan-doc (plan-before-code gate). **Component fence:** `dev-sdlc` (the new coverage logic + test land under `plugins/dev-sdlc/tools/loam-amend/`; the registry edit is universally-admitted `docs/plans/guard-floor.yaml`). **Program:** 3-cycle fix off `workspace/.scratch/claude-output/release-seal-near-miss-audit-2026-07-08.md` (pos3). Cycle 1 (`release-cli-tag-target-and-cut-hardening`, Classes D/A/B) sealed at `c074dc18`. This cycle lands **Class C only**. Class E is a separate later cycle.

## §1 — Objective (Class C: seal blast-radius exceeds seal test scope)

Close the cross-component seal-blast-radius gap: a seal that edits a doc **shared across components** must not be able to breach another component's content-guard unseen. This is the v1.11.0 failure (audit §2 Class C, VERIFIED): the recall cycle (component `primary-persona`) edited the shared `plugins/dev-sdlc/docs/odd-methodology.md`, whose line-count guard `test_AC_KDOC_1` lives in `dev-sdlc` and is neither a fence test nor a `guard-floor.yaml` member. The recall seal ran recall's tests + fences + registered sweeps — none touched KDOC — so every seal gate passed; only the once-per-minor HARD smoke caught the collision.

Two composing outcomes, **reusing the existing guard-floor mechanism** (this is registry completeness, not new machinery):

1. **Register the cross-component-shared-doc guards in the floor** (`docs/plans/guard-floor.yaml`), so every seal's guard-floor sweep runs them regardless of which component sealed.
2. **A shared-doc-coverage meta-check** that FAILS when a shared doc has a content-guard test that is not a floor member — so the registry cannot silently rot as new shared-doc guards appear. The meta-check is itself floored, so it runs at every seal.

The audit names `odd-methodology.md` as the exemplar and instructs: enumerate the rest, don't assume KDOC is the only one. Enumeration below (§3) is Tier-0 — computed from the repo, not assumed.

## §2 — Named decisions (surfaced; the dispatcher rules only if a reasonable person would weigh them differently)

The brief's halt-trigger flags one genuine definitional call: *what is a "shared / cross-component doc," mechanically?* It has a clean answer for the SURFACE and a bounded answer for the DOC→GUARD mapping. Both are recorded here with evidence.

- **D-SDC.SURFACE — the shared-doc surface = FILE-level `universal_paths.files`, union over current + sealed manifests, threshold-free (≥1).** These are exactly the specific docs a manifest admits ANY cycle to edit — the seal-blast-radius admission set the failure lives in (VERIFIED: `apply.py:125-126`, `dry_run.py:201-202` union `manifest.universal_paths` into the admitted set). `odd-methodology.md` is declared in 185 manifests. Union over current + sealed (not current-only) because current-only shrinks as manifests archive — a doc silently dropping off the surface is surface-rot (advisor-flagged). Threshold-free: any manifest granting universal edit to a doc creates the cross-component-edit path; a ≥2 cutoff would be a magic number (the exact brittleness `feedback_loose_AC_text_fix_AC_not_implementation` / Class E warns against).
- **D-SDC.PREFIX-EXCLUDED — PREFIX admissions (`universal_paths.prefixes`, e.g. `docs/plans/`, `docs/design/`) are OUT of the surface.** They are broad working spaces, not specific shared docs; including them would (a) make the surface volatile to a single broad-prefix manifest (`PREFIX:docs/` appears once and would sweep nearly everything) and (b) over-broaden the floor far past the audit's cross-component-shared-DOC failure. **Surfaced limitation:** a doc that is guarded and cross-component-editable *only* via a prefix admission is not covered by this meta-check. Given the audit's failure is a file-level shared doc and the prefix spaces are overwhelmingly guard-free plan/design docs, file-level is the defensible scope. Recorded, not silently narrowed.
- **D-SDC.SUBST — the one known dev-mode relocation is normalized.** Manifests declare the normal-use path `docs/odd-methodology.md`; the dev-mode/canonical file is `plugins/dev-sdlc/docs/odd-methodology.md` (post-M6b.0). The surface membership test normalizes `plugins/dev-sdlc/docs/<X>` ↔ `docs/<X>` so a guard reading the real path matches the declared surface entry. (Belt-and-suspenders: the real path is *also* directly declared in 7 manifests, so odd-methodology is on the surface even without the normalization.) A future relocation would need the map extended; the meta-check's own coverage would surface the resulting gap.
- **D-SDC.GUARD-SHAPE — a "content guard" = a test with a module-level `Path` constant that resolves (repo-root-anchored, following intra-module constant refs) EXACTLY to a tracked doc file, whose content is read (`.read_text`/`.splitlines`/`.read_bytes`) via that constant.** This is the precise signature of the KDOC-class failure (a per-doc structural pin). It deliberately excludes: (a) fence/seal-diff tests that list a doc path as a *string* in an allow-list (no constant, no read), (b) on-demand-pointer tests that `write_text` a `tmp_path` fixture, and (c) corpus-wide `rglob` sweeps (e.g. `test_AC_KDOC_2/_S` read many docs via glob — a different guard class, not a per-doc pin). A loose "basename appears + read_text appears" grep over-matched 13-14 files; the exact-resolution detector returns zero false positives on the current tree (VERIFIED, §3). **Surfaced limitation:** a per-doc guard that resolves its root via a non-`parents[N]` idiom (e.g. chained `.parent.parent`) is handled by the detector where cheap, but an exotic path-construction idiom could be missed; every one of the current 6 docs' guards uses `parents[N]` (VERIFIED).
- **D-SDC.MEMBERSHIP — "is floored" reuses `discover_guard_floor` / `_resolve_pattern`, never exact-string match.** A guard already covered by a directory pattern (e.g. class-10 `framework/protection-matrix/tests/`) must count as floored. Resolution is fnmatch + dir-prefix, identical to the seal-time sweep.
- **D-SDC.META-FLOORED — the meta-check is itself a registered floor member.** Otherwise it could not catch a guard added during a component's cycle whose fence excludes it — the whole point. This is the anti-rot closure.

## §3 — Enumeration (Tier-0; computed from the repo at plan-authoring)

File-level universal-admitted docs that carry a constant-anchored content guard, and each guard's current floor status. All guards VERIFIED green (`.venv/bin/pytest`, run separately to avoid cross-conftest collisions). None currently floored (VERIFIED against the 20 existing `guard-floor.yaml` patterns; audit §2 Class C confirms "no KDOC entry").

| Shared doc (surface) | Content-guard test(s) | Guard's component | Floored now? |
|---|---|---|---|
| `plugins/dev-sdlc/docs/odd-methodology.md` | `test_AC_KDOC_1`, `test_AC_KDOC_3`, `test_AC_KDOC_5`, `test_AC_MSLB_1` | dev-sdlc | no |
| `plugins/dev-sdlc/docs/odd-methodology.md` | `test_AC_RVL_8_cap_bias_checklist_line` | **primary-persona (cross-component!)** | no |
| `docs/VALUE_PROPOSITION.md` | `test_AC_CH0_2_value_prop_po_labels` | dev-sdlc | no |
| `docs/charter.md` | `test_AC_CH0_1_charter_genesis` | dev-sdlc | no |
| `docs/CLAUDE_CAPABILITIES.md` | `test_AC_CLP_CUR_1_2_reference_surface` | capability-refresh | no |
| `CLAUDE.dev.md` | `test_AC_OGP_3_claudedev_references_lean_grounding` | hands-off-lifecycle | no |
| `docs/implementation-tiers.md` | `test_AC_NTU_7_implementation_tier_picker` | primary-persona | no |

The `RVL_8` row is the clearest proof of the gap: a guard on the shared methodology doc living in a DIFFERENT component from KDOC, unfloored — a cross-component seal editing that line breaches it unseen exactly as KDOC was breached.

## §4 — Acceptance criteria (outcome-shape; method is the builder's call)

### SDG — register shared-doc guards in the floor
- **AC.SDG.1** — `docs/plans/guard-floor.yaml` gains sweep pattern(s) that resolve, at seal time, to every content-guard test in §3 (the 8 tests across 6 docs). Every new pattern resolves to ≥1 tracked test (no pattern is stale, per AC.GFLOOR.3).
- **AC.SDG.2 (outcome-altitude:true)** — `discover_guard_floor` invoked against the real repo (production entry point, no pre-set state) returns a floor whose `sweep_targets` include BOTH `test_AC_KDOC_1_methodology_rewrite.py` (the exact guard the v1.11.0 recall seal bypassed) AND the cross-component `test_AC_RVL_8_cap_bias_checklist_line.py`. A seal's guard-sweep now executes the bypassed guard.

### SDC — shared-doc-coverage meta-check (anti-rot)
- **AC.SDC.1** — a coverage function derives from the live repo (a) the file-level universal-admitted doc surface per D-SDC.SURFACE/PREFIX-EXCLUDED/SUBST and (b) for each surface doc, its constant-anchored content-guard tests per D-SDC.GUARD-SHAPE; and returns each such guard test that does not resolve to a floor member per D-SDC.MEMBERSHIP. Given a floor (registry) it evaluates coverage deterministically from tracked files only.
- **AC.SDC.2 (outcome-altitude:true)** — given a surface doc whose guard is NOT covered by the supplied floor (a floor with that guard's pattern absent), the meta-check reports a violation naming the shared doc, the uncovered guard test, and a corrective registry pattern to add. Constructed with the real KDOC guard + a floor missing its pattern → non-empty, named violation.
- **AC.SDC.3** — evaluated against the floor this cycle registers (the real `guard-floor.yaml` resolved on the sealed tree), the meta-check returns ZERO violations. The check is provably green on the current tree, not a false-positive tripwire (hard gate — the meta-check is floored, so a false positive would break every seal).
- **AC.SDC.4** — the meta-check test is itself a registered `guard-floor.yaml` member, so it executes at every seal regardless of the sealing component's fence.

## §5 — Fence

- **Component:** `dev-sdlc` (seal_test `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`, sidecar `plugins/dev-sdlc/tests/SEAL_COMMIT`). loam-amend has no separate fence — it is inside the dev-sdlc sealed surface (VERIFIED: no `plugins/dev-sdlc/tools/loam-amend/tests/test_no_sealed_amendments.py`).
- **New source:** `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/shared_doc_coverage.py` (reuses `guard_floor.discover_guard_floor`/`_resolve_pattern` + `manifest` universal-path parsing).
- **New test:** `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_SDG_*` + `test_AC_SDC_*`.
- **Universally-admitted edit (not fenced):** `docs/plans/guard-floor.yaml` (registry), plan-doc + manifest + narrative under `docs/plans/`, `docs/STATE.md`, `docs/plans/loam-roadmap.md` §backfill.
- **NO edits to** framework/* or other-component source. The registry patterns *point at* other components' tests (yaml only); no other component's source or runtime behavior changes.

## §6 — Build steps

1. Author `shared_doc_coverage.py`: surface derivation (D-SDC.SURFACE/PREFIX-EXCLUDED/SUBST over current+sealed manifests via `git ls-files`), content-guard detection (D-SDC.GUARD-SHAPE, AST), floor-membership via `discover_guard_floor`, and `find_uncovered_shared_doc_guards(repo_root, floor) -> list[violation]` returning `{doc, guard_test, suggested_pattern}`.
2. Register the §3 guards in `guard-floor.yaml` (AC.SDG.1) + the meta-check test pattern (AC.SDC.4).
3. Author tests: `test_AC_SDG_1` (registry resolves to the 8 guards, none stale), `test_AC_SDG_2` (outcome-altitude — `discover_guard_floor` real-repo includes KDOC_1 + RVL_8), `test_AC_SDC_1` (function derives surface+guards+uncovered set), `test_AC_SDC_2` (outcome-altitude — synthetic floor missing KDOC → named violation + hint), `test_AC_SDC_3` (real floor → zero violations), `test_AC_SDC_4` (meta-check test path is a floor member).
4. Run touched tests + the full guard-floor sweep locally (`discover_guard_floor` + each target green, meta-check zero-violation) — the zero-FP gate BEFORE seal.
5. Commit source+tests+registry as `feat(dev-sdlc):` BEFORE `loam amend apply` (apply runs against committed HEAD).
6. `loam amend validate` → `apply` → `seal`. Backfill STATE.md + roadmap + parent register.

## §7 — Halt triggers (return to dispatcher, do NOT silently extend)

- Registering any §3 guard makes some OTHER component's seal newly RED (a latent pre-existing collision surfaced) — that is a real finding to surface, not paper over.
- The meta-check is NOT green on the current tree after registration (a surface doc whose guard genuinely cannot be floored, or a detector false-positive) — HALT; a floored meta-check that false-REDs breaks every seal.
- Any guard in §3 is red/flaky/non-deterministic at flooring time — HALT (do not floor a flaky guard; do not loosen it).
- Any ODD violation in this work OR surrounding code; any brief/audit conflict.
- WD drift from `/Users/lukeivers/loam`.

## §8 — Status

- Plan authored: 2026-07-08 (this doc). Enumeration §3 Tier-0-verified pre-code.
- Build: PENDING.
- Seal: PENDING (STOP at sealed-local; no `loam release`/tag/push — dispatcher's action after all 3 cycles seal).
