# Amendment #27 — stale launchd README cleanup

**Amendment number:** 27
**BASELINE (pre-amendment tip):** `006f5b9` (chore(seals): teardown-
observability-retrofit seal — amendment #26).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-22.
**Motivating audit:** `.scratch/claude-output/pos3-delete-and-canonical-clone-readiness-audit.md`
Part B §3 — the `memory-system/launchd/` directory contains a stale
hardcoded-path plist that is NOT used at runtime (the authoritative
plist generator is the workspace-bootstrap scaffold), but whose
`README.md` still instructs users to `cp` the stale file into
`~/Library/LaunchAgents/`. Harmless (first-run later overwrites it) but
confusing and wrong-looking on a fresh clone.

## 1. Intent

Rewrite `memory-system/launchd/README.md` to mark the directory as
**historical reference material only** and point readers at the real
plist generator: `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`
(templates in `_LAUNCHD_TEMPLATES`, lines 488-509 at tip).

Doc-only edit. Zero source changes. Zero test changes.

## 2. Keep-or-delete decision (builder's call)

**Decision: KEEP the stale plist in place.**

Rationale:
1. Prior true-first-run research (`docs/archive/component-research/true-first-
   run/research.md:505-507`) already ruled "leave as-is; update docs."
   That ruling has not been superseded.
2. The file is a historical reference for the plist shape that shipped
   before amendment #4 moved plist generation into the scaffold. Useful
   as a reading-only artifact for anyone debugging the scaffold's
   template output.
3. Deleting the file would be a slightly larger diff for no runtime
   gain — README-only reframing is the minimum-viable fix.
4. The redirect README makes the stale file non-dangerous: a reader
   following README instructions will now be told explicitly NOT to
   copy it.

If a future cleanup amendment deletes the file outright, that's fine;
this amendment defers that call.

## 3. Files edited

Exactly one file:

- `memory-system/launchd/README.md` — full rewrite. New content makes
  three things clear:
  1. The directory is historical reference only.
  2. The authoritative plist generator is the workspace-bootstrap
     scaffold (pointer to `first_run_scaffold.py`).
  3. Users should NOT `cp` the plist manually — first-run handles it.

## 4. BASELINE + SEAL bookkeeping

### 4.1 Manifest components

One component, floating BASELINE:

- `memory-system` — floating BASELINE → `006f5b9`.

No other component is touched. `memory-system/launchd/README.md` is
admitted under the existing `memory-system/` prefix in memory-system's
seal-diff test (line 155 of `memory-system/tests/test_no_sealed_amendments.py`).
No `extra_allowed_prefixes` needed.

Hands-off-lifecycle gets `frozen_baseline: true` per amendment #23
ruling (H19's BASELINE stays frozen at project-start; sidecar +
narrative only). But this amendment does NOT touch H19 at all — no
narrative append, no sidecar advance. Per scope discipline, H19 stays
out of the manifest entirely.

Correction to the dispatch's note about H19: the dispatch says "Hands-
off-lifecycle: frozen_baseline: true (not touching H19)." Interpreted
as: we are NOT touching H19, so it does NOT appear in the manifest.
If the dispatch intended an H19 sidecar-only advance, that would
require a narrative stanza; this amendment is intentionally too small
for that. Builder's call: omit H19 entirely.

### 4.2 SEAL_COMMIT sidecar

`memory-system/tests/SEAL_COMMIT` advances to the amendment SHA in the
seal commit via `pos-amend seal`.

### 4.3 Universal paths

Standard universal admissions per amendment #22:
- prefix: `docs/plans/`
- files: `CLAUDE.md`, `docs/odd-in-pos.md`, `docs/odd-methodology.md`,
  `docs/FUTURE_IDEAS.md`

## 5. Commit cadence

**Commit 1 (amendment):** via `pos-amend apply`.
```
docs(memory-system): clarify launchd/ as historical reference; authoritative plist generator is workspace-bootstrap scaffold (amendment #27)
```

**Commit 2 (seal):** via `pos-amend seal`.
```
chore(seals): stale-launchd-readme-cleanup seal — memory-system at <amendment-sha>
```

## 6. Tests

### 6.1 Pre-amendment

- Memory-system full suite — should be green at BASELINE `006f5b9`
  (doc-only edit will not affect any test).
- Seal-diff-tests-only for the other 9 components — should be green.

### 6.2 Post-seal

- Seal-diff-tests-only across all 10 components — should be green.

## 7. Halt triggers

1. `memory-system/launchd/` NOT in memory-system's allowed_prefixes →
   would fail seal-diff. **Pre-verified: the existing `memory-system/`
   prefix covers this.** No halt.
2. README edit breaks any test → not expected (README is documentation
   only, no test imports it); halt if contradicted by test run.
3. pos-amend dry-run fails → halt, flag.

## 8. ODD compliance

Doc-hygiene edit on a memory-system-owned file. No code/branch/test
added; no new methodology question. Maps to the audit's Part B §3
residual finding (non-blocking, doc-hygiene). The new README text
describes the real runtime behaviour already governed by existing ACs
(the scaffold-at-first-run ACs in workspace-bootstrap's brief) — it
makes an existing truth readable, does not introduce new scope.
