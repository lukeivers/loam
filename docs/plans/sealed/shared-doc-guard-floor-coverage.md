# Shared-doc guard-floor coverage — apply ladder

Cycle 2 of the 3-cycle fix program off the 2026-07-08 release-seal
near-miss audit (`workspace/.scratch/claude-output/release-seal-near-miss-audit-2026-07-08.md`,
pos3). Cycle 1 (`release-cli-tag-target-and-cut-hardening`, Classes
D/A/B) sealed at c074dc18. This cycle lands **Class C only** — the
cross-component seal-blast-radius gap. Class E is a separate later cycle.

Root (audit §2 Class C, VERIFIED): the recall cycle (component
primary-persona) edited the shared `plugins/dev-sdlc/docs/odd-methodology.md`,
whose line-count guard `test_AC_KDOC_1` lives in dev-sdlc and is neither
a fence test nor a `guard-floor.yaml` member. The recall seal ran only
recall's tests + fences + registered sweeps — none touched KDOC — so
every seal gate passed and only the once-per-minor HARD smoke caught the
collision. The fix is registry completeness over the EXISTING guard-floor
mechanism, not new machinery.

This amendment (single dev-sdlc fence, NO public action):
  1. (SDG) Registers in `docs/plans/guard-floor.yaml` every
     constant-anchored content-guard that protects a file-level
     universal-admitted doc — the 8 guards across 6 docs enumerated
     Tier-0 in plan §3, none previously floored (audit confirms "no KDOC
     entry"). After registration each such guard runs at EVERY seal via
     the guard-floor sweep, regardless of the sealing component's fence.
     The clearest gap closed: `test_AC_RVL_8` — a guard on the shared
     methodology doc living in a DIFFERENT component (primary-persona)
     from KDOC, previously unfloored. Outcome-altitude AC.SDG.2:
     `discover_guard_floor` on the real repo now includes the KDOC_1
     guard the recall seal bypassed + the cross-component RVL_8.
  2. (SDC) Adds `shared_doc_coverage.py` + a floored meta-check test
     that FAILS when a file-level universal-admitted doc carries a
     constant-anchored content-guard not resolvable to a floor member —
     so the registry cannot silently fall behind as new shared-doc
     guards appear. It reuses `discover_guard_floor`/`_resolve_pattern`
     for the "is floored" test (never exact-string), and names the doc +
     guard + corrective registry pattern on a violation. The meta-check
     is itself a registered floor member (anti-rot closure — it runs at
     every seal). Outcome-altitude AC.SDC.2: a surface doc with an
     unfloored guard → named violation + corrective hint.

Named definitional decisions (plan §2, surfaced): the shared-doc SURFACE
= FILE-level `universal_paths.files` union over current+sealed manifests,
threshold-free (D-SDC.SURFACE); PREFIX admissions excluded as broad
working spaces (D-SDC.PREFIX-EXCLUDED, a recorded limitation); the
dev-mode `docs/` ↔ `plugins/dev-sdlc/docs/` relocation normalized
(D-SDC.SUBST); a "content guard" is the exact-resolution per-doc read
signature, excluding string-allow-lists, tmp fixtures, and rglob sweeps
(D-SDC.GUARD-SHAPE). Zero false positives on the current tree is a hard
gate — the meta-check is floored, so a false positive would break every
seal.

STOP at sealed-local. Does NOT run `loam release`, does NOT tag, does
NOT push — the eventual single published cut is the dispatcher's action
AFTER all three cycles seal.

BASELINE 51879b04 — HEAD of main at plan-authoring (post cycle-1 seal +
#195 tidy); confirm at apply time. Counter 196 next free; confirm at
apply time. Single-component dev-sdlc fence; the registry edit is
universally admitted; NO other component's source or runtime behavior
changes.
