# self-upgrade BB-feat #54 follow-on bugfix — clause-(h) audit + state.yaml + workspace-local audit-path — plan

Sealed-component amendment to `self-upgrade/` (follow-on bugfix to amendment #54). Carries a `pos-amend` manifest at `docs/plans/self-upgrade-bb-feat-bugfix.manifest.yaml`; advances `self-upgrade/tests/SEAL_COMMIT` sidecar; lands a deterministic seal commit per `pos-amend seal`. Plan-before-code per the dev CDC. Per amendment #54 / #53 precedent.

**Status:** plan (pre-dispatch). 2026-04-26.
**Working directory:** /Users/lukeivers/ivers-corp-pos-v2/
**Companions:** - **#54 plan:** `docs/plans/self-upgrade-clause-h-llm-merge.md`
  (the amendment whose ACs this bugfix is closing).
- **#54 manifest:** `docs/plans/self-upgrade-clause-h-llm-merge.manifest.yaml`
  (BASELINE + universal paths + narrative shape precedent).
- **CC synthetic-validation test plan:**
  `docs/plans/research/bb-feat-synthetic-validation-plan.md`
  (the halt-and-surface block names the 3 bugs; commit `90246dc`
  landed the test file).
- **CC test file:**
  `self-upgrade/tests/test_bb_feat_synthetic_validation.py`
  (carries 11 tests; 2 halt-surface markers + 1 path-assertion
  flip on bug 3 — the test file is edited as part of this
  amendment, not added to).
- **Existing self-upgrade artefacts:**
  `self-upgrade/src/self_upgrade/cli.py` (audit-write site),
  `clause_checks.py` (`resolve_clause_h_inferred` —
  helper-level write site for the new in-helper audit + state),
  `conflict_report.py` (audit YAML schema),
  `paths.py` (legacy `conflicts_yaml(tag)` path stays
  intact for `--staging-dir`).
- **#28 precedent for state.yaml.** Amendment #28 introduced
  the persistent-state pattern (per the assistant's session-
  start corpus); composing on the same shape.

**Ancestor record:** - **#54 (clause-(h) LLM-merge gate)** at commit `0737e7c`
  (amendment) + `1fd826a` (seal) + `83d830c` (SHA-record),
  2026-04-26. Landed clause-(h) but diverged from plan §2 +
  §4 on three audit/state surfaces.
- **CC's BB-feat synthetic validation** at commit `90246dc`,
  2026-04-26. Landed 11 integration tests across 6 milestone
  areas; surfaced 2 halt-and-surface markers + 1 documented
  path-divergence note; deferred ruling on whether a follow-on
  amendment is needed.
- **Owner ruling 2026-04-26 (this dispatch).** Yes — fix all
  three. They are #54 AC violations the build did not satisfy,
  not new spec scope.

**Research:** docs/plans/research/bb-feat-synthetic-validation-plan.md

---

## 1. Summary / TLDR

Follow-on sealed-component amendment to `self-upgrade/` that closes
three AC gaps surfaced by the BB-feat (#54, clause-(h)) synthetic
validation suite (commit `90246dc`). Each gap maps to a #54 AC the
build did not actually satisfy:

1. **AC.H.5 audit on success path.** `cmd_upgrade` only saved the
   conflict-report on `BudgetExhausted`, `ResolverFailure`, or
   `report.has_pending()`. A clean clause-(h) pass that resolved
   every conflict produced **no** on-disk audit. Spec text: "Every
   clause-(h) upgrade writes audit ... regardless of pass/fail
   outcome." Fix writes the audit unconditionally on every
   clause-(h) execution.

2. **AC.H.8 state.yaml absent.** No code under
   `self-upgrade/src/` ever wrote `<workspace>/.pos/upgrade/state.yaml`,
   so cross-invocation idempotency depended on the operator passing
   `--conflicts-from <prior-yaml>` by hand. Fix lands a
   `state.py` writer + auto-discovery on the next clause-(h)
   invocation, mirroring amendment-#28's persistent-state pattern.

3. **Audit-path divergence.** Plan §2 (#54) named
   `<workspace>/.pos/upgrade/<tag>/audit.yaml` as the audit target;
   implementation wrote `~/.pos/framework/history/<tag>-conflicts.yaml`
   (global, not workspace-local). Fix moves the clause-(h) audit
   write to the workspace-local path. Legacy `--staging-dir`
   non-clause-(h) flow keeps writing to `paths.conflicts_yaml(tag)`
   (backward-compat).

Each fix flips a halt-and-surface marker test pinned at commit
`90246dc` (CC's BB-feat synthetic validation). Sealed-component
fence: `self-upgrade/` only, same fence as #54. No `pos-v2-spec`
changes; this is amendment of the implementation to match the
AC text already locked in #54.


---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

This is a follow-on bugfix to amendment #54
(`docs/plans/self-upgrade-clause-h-llm-merge.md`). Each
AC.HFX.* below names the #54 AC the bugfix is satisfying — the
implementation diverged from #54's plan §4 acceptance criteria,
not from any new spec. Per CLAUDE.md §2.5: every AC in this plan
ladders up to a #54 AC that ladders up to v1.0 self-upgrade
objective (line 81 of `docs/spec/pos-v2-objectives-spec.md`).

- **AC.HFX.1 ↔ AC.H.5** (audit-on-every-clause-(h)-pass).
- **AC.HFX.2 ↔ AC.H.8** (state.yaml convergent idempotency).
- **AC.HFX.3 ↔ AC.H.5 path text in plan §2** (workspace-local
  audit path).

No new top-level v1.x objective. No new clause-letter. Bugfix on
#54's surface, fence-identical to #54.

**Reverse trace per CLAUDE.md §2.5.** Each AC traces to AC.PO.1
(translation-burden reduction) and/or AC.PO.2 (toolkit-primitive
growth):

- **AC.HFX.1 → AC.PO.1.** Without the audit on the success path,
  the persona has no artefact to summarise post-upgrade. The
  user's natural-language question "what did the resolver decide
  in this upgrade?" has no machine-readable answer until the
  audit lands. Fix restores the persona's read-on-demand surface.
- **AC.HFX.2 → AC.PO.1 + AC.PO.2.** State.yaml means re-runs
  auto-discover prior state — the persona never needs the user
  to remember the prior `--conflicts-from` path. Toolkit
  primitive: a known location for upgrade-state introspection.
- **AC.HFX.3 → AC.PO.2.** Workspace-local audit path means the
  audit lives next to the workspace's persona/MCP/`.pos`
  artefacts, not in a global `~/.pos/framework/history/` mixed
  bag. Toolkit primitive: predictable workspace-relative path
  the persona composes against (`<workspace>/.pos/upgrade/<tag>/`).


---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

No new Claude SDK surface. The fixes compose on existing
primitives:

1. **Pydantic-validated state.** `StateRecord` is a Pydantic model
   in the same shape as `ConflictReport` / `SyncProtected` /
   `MergeVerdict` / `ResolverBudget`. Reach-for default per
   `odd-methodology.md` §5.3. No new validator framework.
2. **YAML round-trip.** State + audit write through the same
   `yaml.safe_dump` / `model_dump(mode="json")` pattern the rest
   of self-upgrade uses. No new serialization surface.
3. **OTel spans.** No new spans; existing
   `pos.upgrade.merge_gate.summary` already records resolved /
   deferred / cumulative-tokens.

No new MCP server, no new hook, no new slash-command.
Claude-leverage answer: **composition only — no new surface needed.**

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** All three fixes reduce translation
burden:

- AC.HFX.1: persona can answer "what did the resolver decide?"
  by reading the audit; pre-fix, the answer was "I cannot — no
  audit was written on success."
- AC.HFX.2: persona answers "did this upgrade already run?"
  by reading state.yaml; pre-fix, the user has to remember and
  re-pass `--conflicts-from`.
- AC.HFX.3: persona reads the audit at a workspace-relative
  path (one `<workspace>/.pos/upgrade/<tag>/audit.yaml`),
  not a global mixed-history dir.

**Harness test.** All three fixes complete toolkit primitives
#54 named in plan §2 but did not deliver:

- `<workspace>/.pos/upgrade/<tag>/audit.yaml` — NOW lands here
  on every clause-(h) execution.
- `<workspace>/.pos/upgrade/state.yaml` — NEW primitive,
  enables persona introspection of upgrade-state without
  requiring the operator to thread paths.

Both tests **pass.**

### Lens 3 — ODD authoring

ACs §4 are outcome-shaped: each names a state of the world the
fix must make true, with a deterministic test shape (the CC
halt-surface marker test or a flipped/added assertion in the
same file). No method-in-AC: the AC does not name `state.py`,
does not name "Pydantic schema", does not name "in finally
block". Method choices (where in the helper vs CLI to write,
schema field set, auto-discovery shape) are the builder's call
inside §9.x's bookkeeping notes.

Behaviour-count check: §5. ODD §2.5 reverse trace is the
builder's pre-seal check captured in the builder-plan.


---

## 4. Acceptance criteria (AC.HFX — dev-discipline plan)

Three outcome-shaped acceptance criteria, plus the seal-diff
invariant. Each carries the deterministic test shape the CC
synthetic-validation suite already encodes; the same file
(`self-upgrade/tests/test_bb_feat_synthetic_validation.py`)
carries the test, with halt-surface assertions flipped to assert
the spec'd behaviour.

**AC.HFX.1 — Audit written on every clause-(h) execution.**
Every clause-(h) execution (pre-stage helper run via
`resolve_clause_h_inferred`, regardless of clean-pass /
budget-exhausted / resolver-failure terminus) leaves a
Pydantic-loadable audit YAML at the workspace-local path
(per AC.HFX.3). The audit reflects the in-memory ConflictReport
state at the helper's terminal point. Verified by an integration
fixture that runs the helper to clean-pass and asserts the
audit YAML exists + round-trips. Closes the gap surfaced by
the halt-surface marker
`test_halt_surface_audit_not_written_on_clean_clause_h_pass`
at commit `90246dc`.

**AC.HFX.2 — Convergent-idempotency state.yaml at workspace
path.** Every clause-(h) execution writes
`<workspace>/.pos/upgrade/state.yaml`. The file's schema
(Pydantic-validated on every load) carries fields naming:
upgrade tag, ISO-8601 timestamp, the conflicts-yaml path
(audit reference), counts (resolved / deferred / total),
cumulative resolver tokens used, and a status enum
(`success` / `failure` / `partial`). On the next clause-(h)
execution against the same workspace, the CLI auto-discovers
the prior state.yaml (no `--conflicts-from` required) and
resumes by treating the prior audit's already-resolved entries
as the starting state. Verified by: (a) state.yaml exists +
round-trips after a helper run, (b) re-running the CLI against
the same workspace + canonical does NOT re-invoke the resolver
(call-count assertion equals zero on second run). Closes the
halt-surface marker `test_halt_surface_state_yaml_not_implemented`.

**AC.HFX.3 — Workspace-local audit path.** The clause-(h)
audit is written to
`<workspace>/.pos/upgrade/<tag>/audit.yaml` whenever the
upgrade was invoked through the `--canonical` CLI surface
(clause-(h)-eligible mode). When invoked through the legacy
`--staging-dir` surface (no clause-(h) eligibility), the
audit continues to land at `paths.conflicts_yaml(tag)` —
backward-compat per #54 Hard Constraint #5. Verified by a
CLI fixture that uses `--canonical` and asserts the audit
lands at the workspace-local path; an existing legacy fixture
(`test_cli_staging_dir_only_no_clause_h_path`) keeps asserting
the global path and stays passing.

**AC.HFX.S — Seal-diff invariant.** Diff between BASELINE and
SEAL_COMMIT is confined to `self-upgrade/` plus
amendment-universal admissions
(`docs/plans/`, `CLAUDE.md` if needed,
`docs/FUTURE_IDEAS.md` if needed,
`docs/odd-*.md` if needed). Verified by
`self-upgrade/tests/test_no_sealed_amendments.py` at
the new BASELINE.


---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

Three declared behaviours; three outcome-shaped ACs; one
seal-invariant. Match.

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Audit written on every clause-(h) execution (success and failure paths) | AC.HFX.1 |
| 2 | state.yaml records upgrade-state at workspace-local path; auto-discovery on re-run | AC.HFX.2 |
| 3 | clause-(h) audit lives at `<workspace>/.pos/upgrade/<tag>/audit.yaml`; legacy unchanged | AC.HFX.3 |
| S | Seal-diff invariant: only `self-upgrade/` + universal paths | AC.HFX.S |

Forward direction (every behaviour → AC) verified above.
Reverse direction (every code path → AC) is the builder's
pre-seal check captured in the builder-plan.


---

## 6. Hard constraints

1. **Sealed-component fence: `self-upgrade/` only** (plus
   universal-paths admissions). Same fence as #54.
2. **No new third-party dependency.** Stdlib + Pydantic + PyYAML
   (already direct deps).
3. **No `--amend`.** Corrective new commits only per
   `feedback_no_amend_in_agent_dispatches`.
4. **Plan-before-code.** This plan exists; the builder writes a
   builder-plan at
   `docs/plans/self-upgrade-bb-feat-bugfix.builder-plan.md`
   before any source edit.
5. **Backward-compat preserved unconditionally.** A `pos upgrade
   <tag> --staging-dir <path>` invocation without `--canonical`
   produces byte-identical behaviour to pre-amendment HEAD —
   same audit-path (`paths.conflicts_yaml(tag)`), same exit
   codes, same conflict-report shape. The 8 non-halt-surface
   CC synthetic-validation tests remain passing. The full
   pre-amendment `self-upgrade/` test suite (186 tests as of
   `90246dc`) remains passing.
6. **No deviation from #54's locked decisions.** D-1 budget
   ceiling 100k cumulative / 5k per-conflict; D-2 confidence
   0.90; AA D-2 through D-7 all locked. No tunable defaults
   change.
7. **No method-in-AC, no non-objective-backed code.** Per ODD
   §2.4 + §2.5. Every code path lands under an AC.HFX.* trace.
8. **Halt-and-surface on ODD violation in surrounding code.** Per
   `feedback_subagent_odd_violation_halt`: if the build surfaces
   an ODD violation in `self-upgrade/src/` or its surrounding
   plan, halt and surface; do NOT extend the violation.
9. **CDC adherence.** scope-only-dispatch CDC; standard
   pos-amend manifest discipline; `pos-amend seal --plan-doc
   <abs-path>` backfills §14.


---

## 7. Out of scope (explicit)

Per ODD §2.5 — strict bugfix on the three named #54 ACs:

- **No new clause letters.** Clause (h) stays clause (h);
  no clause (i).
- **No new spec objective.** Bugfix on existing v1.0 self-upgrade
  objective + #54's AC.H.5 + AC.H.8 text.
- **No tunable-default changes.** Resolver budget defaults stay
  100k / 5k (D-1); confidence stays 0.90 (D-2). Workspace-tunable
  surface unchanged.
- **No #54 surface re-shaping.** `MergeVerdict`,
  `ResolverBudget`, `SyncProtected`, `ConflictEntry`, the
  Resolution enum extensions — all unchanged.
- **No legacy `--staging-dir` audit path change.** Per Hard
  Constraint #5 + AC.HFX.3, legacy mode keeps writing to
  `paths.conflicts_yaml(tag)`. No backward-compat break.
- **No persona-invokable `/sync` slash-command.** Future
  composition (per #54 §7).
- **No `--canonical <git-url>` remote-fetch.** Future
  composition (per #54 §7).
- **No background-scope mode.** Future composition (per #54 §7).
- **No live LLM call against the resolver.** All clause-(h)
  integration testing stays under stub resolvers per the
  existing `_StubLLM` pattern.


---

## 8. Implementation order (suggested — builder's call to refine)

Suggested order — builder's call to refine in the builder-plan:

1. **Read session-start corpus + this plan + #54's plan
   (`self-upgrade-clause-h-llm-merge.md`) + the CC test plan
   (`research/bb-feat-synthetic-validation-plan.md`).** The 3
   halt-and-surface findings in CC's test-plan §"Halt-and-surface
   findings" map 1:1 to AC.HFX.1/2/3.
2. **Author builder-plan** at
   `docs/plans/self-upgrade-bb-feat-bugfix.builder-plan.md`
   before any source edit. Builder-plan captures D-build.x
   method choices and the ODD §2.5 reverse-direction trace
   (one row per code path → AC).
3. **Verify resolution surface against #54's existing modules.**
   Read `clause_checks.py:resolve_clause_h_inferred`, `cli.py:
   cmd_upgrade`, `paths.py`, `conflict_report.py`,
   `sync_protected.py`. Halt-and-surface (§10 trigger 6) if a
   fix surface conflicts with a #54 invariant.
4. **Land state.yaml schema first** — `StateRecord` Pydantic
   model + read/write helpers + workspace-relative path
   resolution. Tests for round-trip, missing-fields refusal,
   status-enum coverage.
5. **Land audit-path resolution** — workspace-local
   `audit.yaml` path helper for clause-(h) mode; legacy
   `paths.conflicts_yaml(tag)` for `--staging-dir` mode. Test
   fixture in CC's synthetic-validation file flips to assert
   workspace-local path.
6. **Land helper-level audit + state writer** — extend
   `resolve_clause_h_inferred` to write audit + state on every
   execution path (clean pass, BudgetExhausted, ResolverFailure).
   The `finally` block ensures the writes fire on exception
   paths too. Tests for each terminus.
7. **Land CLI auto-discovery** — `cmd_upgrade` reads prior
   state.yaml at clause-(h) mode entry, treats the prior
   audit's resolved entries as starting state. Test for
   re-run convergence (resolver call-count = 0 on the second
   invocation against unchanged inputs).
8. **Flip halt-surface assertions in CC's test file.** Two
   halt-surface markers
   (`test_halt_surface_audit_not_written_on_clean_clause_h_pass`,
   `test_halt_surface_state_yaml_not_implemented`) get their
   assertions inverted/added to assert the spec'd behaviour.
   One CLI test (`test_cli_canonical_pending_writes_audit_yaml`,
   `test_cli_canonical_without_merge_resolver_module_skips_clause_h`)
   gets the audit-path assertion swapped from
   `paths.conflicts_yaml(tag)` to the workspace-local path.
9. **Run touched-component suite then `pos-amend apply
   --dry-run`.** Then amendment commit; then `pos-amend seal
   --plan-doc <abs-path>`.
10. **Verify backward-compat** — legacy `--staging-dir` test
    stays passing without modification. Non-halt-surface CC
    tests stay passing without modification.


---

## 9. Bookkeeping surface

Sealed-component amendment against the post-#54 (clause-(h)
LLM-merge) tip + the post-`90246dc` test-validation tip.
self-upgrade carries the seal-bookkeeping infrastructure
(retrofitted in #53); this amendment composes onto it.

`pos-amend` manifest sketch (builder finalises in
`<slug>.manifest.yaml`):

```yaml
schema_version: 1
amendment:
  number: 55  # next free amendment number at dispatch time
  slug: self-upgrade-bb-feat-bugfix
  title: "self-upgrade BB-feat #54 follow-on bugfix — clause-(h) audit + state.yaml + workspace-local audit-path"

# BASELINE: 90246dc — current HEAD at amendment-commit time
# (the commit that landed CC's synthetic-validation tests).
# BASELINE-as-HEAD~1 pattern per #29 / #34-#54.
baseline: 90246dc4dafa953c1f5ad5d97819e24d97a761a7

plan: docs/plans/self-upgrade-bb-feat-bugfix.md

components:
  - name: self-upgrade
    seal_test: self-upgrade/tests/test_no_sealed_amendments.py
    sidecar: self-upgrade/tests/SEAL_COMMIT
    frozen_baseline: false

universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/FUTURE_IDEAS.md

narrative:
  target: self-upgrade/seals/SEAL_COMMIT.bb-feat-bugfix
  body: |
    # Amendment #55 — self-upgrade BB-feat #54 follow-on bugfix
    <builder finalises body — see #54 + #53 narratives for shape>
```

**Frozen-baseline:** `false`. self-upgrade is not the frozen
component.

**Test-fixture admissions** (extra_allowed_prefixes): none
required — all source + test edits land under `self-upgrade/`.

**Universal admissions** match #54's pattern.


---

## 10. Halt triggers (builder halts + signals owner)

Builder halts and signals owner if any of the following fire.
Each carries a specific surface check; the builder does NOT
silently extend a violation per
`feedback_subagent_odd_violation_halt`.

1. **Required source-edit outside `self-upgrade/`.** Halt and
   surface. Bug 3 (audit-path) does NOT require any
   non-`self-upgrade/` edit.
2. **A bug fix surfaces backwards-incompat with #54 existing
   tests.** Halt — the fix may not break the 175 #54 tests or
   the 11 CC validation tests. Specifically: the legacy
   `--staging-dir` audit-path remains at `paths.conflicts_yaml(tag)`;
   `MergeVerdict` / `ConflictEntry` schemas unchanged; resolver
   budget defaults unchanged.
3. **The 3 bugs aren't actually 3 bugs.** If on close read of
   the #54 plan §2 + §4 it turns out one of the named gaps is
   intended behaviour per text the dispatch missed, halt and
   surface. (Lower-likelihood — CC test plan already cited
   each AC.)
4. **Fix scope expands beyond the 3 ACs.** If the build
   surfaces a fourth latent bug in #54's clause-(h) surface,
   halt and surface — file an addendum, do not silently widen
   this amendment's diff.
5. **ODD violation observed in surrounding code/docs.** Per
   `feedback_subagent_odd_violation_halt`. Halt; do NOT extend
   a violating surface.
6. **A new top-level objective surfaces.** Per #54 halt-trigger
   1 + Hard Constraint 6: bugfix is composition, not an
   objective amendment.
7. **Wall-time exceeds projected 60-90 minutes.** Halt with
   current-state report; owner triages whether to continue or
   split.


---

## 11. Decisions remaining for the owner to rule on

No genuinely uncertain decisions remain at plan-author time.
All design choices are constrained by:

- #54's locked AA D-2 through D-7 (composition decisions).
- #54's D-1 (budget 100k / 5k) and D-2 (confidence 0.90).
- This plan's Hard Constraint 6 (no deviation from #54 locks).
- Plan §2 of #54 naming the audit path (`<workspace>/.pos/upgrade/<tag>/audit.yaml`).
- The CC synthetic-validation test plan's halt-surface findings
  naming the gaps 1:1 with AC.HFX.1/2/3.

D-build.x method choices (state.yaml schema field set,
whether the writer is in-helper or in-CLI, auto-discovery
trigger shape) are the builder's call inside the builder-plan;
AC text remains outcome-shaped per ODD §2.4 + §2.5.


---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| (no genuinely uncertain decisions) | — | All design choices constrained by #54 locks + plan §2 audit-path text + CC halt-surface findings |


---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface any
ODD violation observed in surrounding code/docs.

Plan-authoring scope (read-only audit of `self-upgrade/src/`,
the #54 plan + manifest, the CC synthetic-validation test plan,
recent amendment plans):

- **None observed in `self-upgrade/src/`'s existing surface.**
  The `Resolution` enum's structural exclusion of `skipped`,
  the `ConflictEntry` model_validator's structural-refusal-by-
  default, the `MergeVerdict` Literal-constrained resolution
  field, the `SyncProtected` framework-floor validator — all
  intact and exemplary.
- **None observed in #54 plan §4 (AC text).** AC.H.5 and
  AC.H.8 text is outcome-shaped; the implementation simply
  diverged. AC.HFX.1/2/3 align the implementation to the AC
  text without changing the AC text.
- **None observed in CC synthetic-validation test plan.** The
  halt-and-surface findings are cleanly numbered, each cites
  the #54 AC the bug violates, and explicitly defers ruling
  to owner — exactly the halt-surface pattern.

**Note on the third bug (audit-path divergence).** The CC test
plan flags this as "Not a bug per the implementation contract,
but a divergence from the plan text." The dispatch resolves
this as "fix the implementation to match plan §2 text" —
consistent with `feedback_loose_AC_text_fix_AC_not_implementation`
inverted: when the implementation diverges from a precise AC
text, fix the implementation. AC.HFX.3 captures this with no
AC-text change.


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

- Amendment commit: `4da967edcb3926e5cbb7dfb776fc54aa9609e253` —
  `feat(self-upgrade): clause-(h) audit + state.yaml + workspace-local audit-path bugfix (amendment #55, AC.HFX.1–AC.HFX.3 + AC.HFX.S)`
- Seal commit: `670cfab6e68cb029982cf4b1c2fad32eeb1bbf40` —
  `chore(seals): self-upgrade BB-feat #54 follow-on bugfix — clause-(h) audit + state.yaml + workspace-local audit-path — self-upgrade at 4da967e`
### Commit SHAs

(populated by `pos-amend seal --plan-doc <this-file> ...` after build, or appended manually for dev-discipline plans)

### Dependents cleared to dispatch

(placeholder)

---

## 15. References

- CLAUDE.md (project + global)
- `docs/odd-methodology.md` §2.4 (loose-AC-fix discipline) + §2.5
  (no non-objective code) + §5.3 (Pydantic reach-for default)
- `docs/odd-in-pos.md`
- `docs/VALUE_PROPOSITION.md` (AC.PO.1 + AC.PO.2)
- `docs/STATE.md`, `docs/FUTURE_IDEAS.md`
- `docs/spec/pos-v2-objectives-spec.md` (line 81 — v1.0
  self-upgrade objective)
- `docs/plans/self-upgrade-clause-h-llm-merge.md` (#54
  plan; AC.H.5 + AC.H.8 text + §2 audit-path text)
- `docs/plans/self-upgrade-clause-h-llm-merge.manifest.yaml`
  (#54 manifest pattern)
- `docs/plans/research/bb-feat-synthetic-validation-plan.md`
  (CC validation plan; halt-and-surface findings)
- `self-upgrade/src/self_upgrade/cli.py` (audit-write site to
  extend)
- `self-upgrade/src/self_upgrade/clause_checks.py`
  (`resolve_clause_h_inferred` — helper-level write site)
- `self-upgrade/src/self_upgrade/conflict_report.py` (audit
  YAML schema)
- `self-upgrade/src/self_upgrade/paths.py` (legacy path stays
  intact)
- `self-upgrade/tests/test_bb_feat_synthetic_validation.py`
  (test surface to flip)

