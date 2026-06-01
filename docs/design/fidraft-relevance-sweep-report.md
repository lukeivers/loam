# FUTURE_IDEAS_DRAFT relevance sweep — 2026-06-01

Owner directive (Telegram 13409): review `docs/FUTURE_IDEAS_DRAFT.md`, remove
entries that are (a) already DONE or (b) OBSOLETE; keep relevant + surface the
ambiguous. Careful-prune discipline: verify-before-remove, cite evidence,
bias to keep, surface ambiguous.

Branch: `chore/fidraft-relevance-sweep` off `main` @ `044251d8`.

## Counts

| | |
|---|---|
| Total top-level entries before sweep | 152 (+ 8 audit-trail bullets) |
| Kept (relevant / open) | 122 |
| Removed — DONE (terminal-RESOLVED, self-evidenced) | 22 |
| Removed — audit-trail bullets (collapsed to one note) | 8 |
| Removed — OBSOLETE | 0 |
| Surfaced for owner relevance call | 4 (see below) |

The build-day hypothesis in the dispatch ("≈20 amendments today → many entries
likely DONE") did **not** map onto open FIDRAFT entries. The N1–N4, doctrine-
enshrinement, migration-engine, defined-workflow, deep-role-research, failure-
mode-matrix, self-recovery, work-visibility, foundation-polish, and intake/
onboarding builds were **roadmap-driven, not FIDRAFT-capture-driven** — no
`capture-only` FIDRAFT entry names them as its objective, so none were closed by
today's work. The DONE removals are the **pre-existing terminal-RESOLVED
entries** (the v0.7.x–v0.10.x release-CLI / backfill / seal-tool arc + the
session-clear-safety + legacy-name sweeps), each of which already carried an
explicit `**Status:** RESOLVED …` line with seal SHA + plan-doc + AC verdicts.
The sweep removed those self-evidenced done entries plus the audit-trail block
the file's own convention says clears "at next review."

## Removed — DONE (each entry's own Status line cited terminal resolution; spot-checked against the git ref graph)

| Entry | Resolution evidence (from the entry + verified) |
|---|---|
| AC.DBT propagated-principle coverage in v0.1.7 personas | RESOLVED 2026-05-09, v0.5.0 corrective `a95dfb9d`; AC.V050.5 GREEN |
| v0.7.3 auto-backfill spec incomplete (4 residual gaps) | RESOLVED v0.7.4, AC.BACKFL2.{1-6,S}, `docs/plans/v0-7-4-auto-backfill-completeness.md` |
| Post-publish state-staleness (SHIPPED-LOCAL→PUBLIC backfill) | RESOLVED v0.7.3, AC.BACKFL.{1-6,S}, `post_publish_backfill.py` |
| `loam release` acs-verified gate parser scoping | RESOLVED v0.7.2, AC.READYP.{1-4,S} |
| F-RETIRE-MIGRATE-TOOLS | RESOLVED 2026-05-14 v0.10.8 PATCH `retire-m1-…`; seal verified `9bd56842` (also the partial-OBSOLETE-framing case — terminal-resolved) |
| F-FUNC-1 (leading-title date variant) | RESOLVED v0.10.2, AC.SMLTV.{1-4,S} |
| F-FUNC-2 (interim-sentence removal) | RESOLVED v0.10.3, AC.RBHCB.1 |
| F-FUNC-3 (placeholder narrative-safety) | RESOLVED v0.10.3, AC.RBHCB.3 |
| F-TF-1 (workspace-sync retired-tool path) | RESOLVED v0.10.7, AC.WSP.1 |
| F-OTEL-VERSION-BUMP | RESOLVED v0.10.4, AC.OTVH.{1-4,S} |
| F-WALKER-1 (pipe-in-description robustness) | RESOLVED v0.10.3, AC.RBHCB.2 |
| F-PCV-1 (per-component pyproject patch bumps) | RESOLVED 2026-05-23, Option C ratified, `test_AC_PCVR_…` |
| F-NFCLEAN-FOLLOWON | RESOLVED-BY-COMPOSITION 2026-05-14 (v0.10.1 + v0.7.4 + v0.10.3) |
| F-NEXT-SCOPE-EMPTY-§4 | RESOLVED v0.10.5, AC.NSWP.{1-4,S}; seal verified `da53584f` |
| F-PAPER-HTML-REGEN | RESOLVED v0.10.6, AC.PHRG.{1-4,S}; seal verified `276e0d57` |
| F-REMOVED-VERDICT-GATE | RESOLVED v0.8.3, AC.RVG.4 |
| F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN | RESOLVED-BY-INSPECTION v0.10.7, AC.WSP.2 (pin in place since `0d599bb`) |
| F-FBM-SESSION-CLEAR-SAFETY | RESOLVED 2026-05-18, R2/R1/G sealed (`de475aa`/`9709172`/`0c93774`) |
| F-LEGACY-POS-AMEND-NAME-IN-DOCS-CORPUS | RESOLVED 2026-05-21 amendment #137; corpus sweep verified in git log |
| F-SEAL-PLUGINS-TESTS-SKIPPED | RESOLVED 2026-05-21 amendment #140 (seal `8a41e7b`) |
| F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE | RESOLVED 2026-05-21 amendment #140 (seal `8a41e7b`) |
| F-DEV-SDLC-MANIFEST-DRIFT-VS-TEST-CORPUS | RESOLVED 2026-05-21 amendment #139 (seal `1f3d8d7e`) |

**Audit-trail block (8 bullets)** — collapsed into one note. The file's own
convention: "Audit-trail entries clear at next review." This sweep is that
review. The 8 bullets (dispatch-template #25, plan-doc skeleton #51, `loam amend
new-plan` #51, Telegram watchdog refix, C-closure graphiti, first-run-sync-α.1,
LLM-classifier-meta-pattern Idea 20, SDLC objective-extraction Idea 3) were all
already confirmed-landed records; full text preserved in git history.

## OBSOLETE removals

None. No entry was removed on obsolescence grounds. (F-RETIRE-MIGRATE-TOOLS
carried a partial OBSOLETE framing — its original "6 one-time scripts" premise
was empirically falsified — but it reached a terminal RESOLVED status, so it
removes as DONE, not OBSOLETE.)

## SURFACED for owner relevance call (kept in file — judgment calls)

1. **F-USER-INTERACTIVITY-ADAPTIVE-SCOPE-DIAL** (the adaptive interaction-model /
   scope-dial). **Partially done.** Today's N4 build (`a177971c feat(N4): MVP
   user-model`) shipped the read+inject path, BUT the N4 plan explicitly fences
   "the full behavioural engine (AIM-4..8) is the LATER remainder, explicitly
   OUT." So the entry's full objective is NOT complete. Kept. Owner call: does
   the entry want a status update to "MVP shipped; behavioural engine remainder
   open," or is it fine as-is?

2. **F-AGENT-EMPIRICAL-RECHECK-BEFORE-HALT.** Its body says the memory rule
   graduated (DONE), but its `**Status:** capture-only` refers to a still-open
   structural-enforcement-hook follow-on. Kept as partial. Owner call: keep the
   hook follow-on open, or close the entry now that the rule shipped?

3. **`loam-amend-cycle` SKILL doc drift on `apply --plan-doc`** (Tooling section).
   The original claim was "SKILL says `loam amend apply --plan-doc` but the CLI
   takes positional manifest only / `--plan-doc` is seal-time only." The current
   SKILL + today's commits use `loam amend apply --plan-doc` consistently and the
   CLI appears to support it now — so the entry may be obsolete. I could NOT
   confirm the flag's apply-time behaviour without running it, so per careful-
   prune I kept it. Owner call: worth a 1-line CLI check to confirm-and-remove.

4. **F-MSC3-WORKTREE-COUPLING / F-V025-C1-VESTIGIAL-STUB** (Cosmetic section,
   opportunistic test-hygiene captures). Likely still latent; not verified
   resolved by any commit. Kept. Low-priority; flagged only so they're on the
   radar for the next test-isolation pass.

## Ruthless-feedback notes on file structure

- **The file is dominated by terminal-RESOLVED entries kept as inline audit
  trail.** This is by the file's own design ("kept as audit trail until next
  review") but it makes the live/open signal hard to see — 122 of the remaining
  entries are still mostly long resolved-arc records vs genuinely-open captures.
  A future review could move terminal-RESOLVED entries to a dedicated archive
  doc (git already preserves them) so the DRAFT surfaces only open work. Not
  done here — out of this sweep's remove-done/obsolete scope.
- **Several `capture-only` entries are now multi-cycle stale** (e.g. the v0.4.3
  BM25 deferred items, the swarms-research v0.1.x candidates) — relevant but
  unlikely near-term. Kept; flagged as graduate-or-defer candidates for a future
  rigor review.
