# self-upgrade clause-(h) — canonical pull + LLM-mediated semantic-merge gate — plan

Sealed-component amendment to `self-upgrade/`. Carries a `pos-amend` manifest (sketch in §9; builder finalises at `docs/plans/self-upgrade-clause-h-llm-merge.manifest.yaml`); advances `self-upgrade/tests/SEAL_COMMIT` sidecar; lands a deterministic seal commit per the seal-automation extension. Plan-before-code per the dev CDC. Per amendment #46 / #47 precedent.

**Status:** plan (pre-dispatch). 2026-04-26.
**Working directory:** /Users/lukeivers/ivers-corp-pos-v2/
**Companions:** - **AA research:** `docs/plans/research/canonical-to-workspace-sync-research.md`
  (LOCKED reframing 2026-04-26 — D-2 through D-7 compose onto
  self-upgrade, not a parallel component).
- **Spec anchors:** `docs/spec/pos-v2-objectives-spec.md`
  line 81 (v1.0 self-upgrade objective), line 114
  (clause-g + workspace-customisation conflict surfacing),
  line 213 (v1.1 R1 semantic round-trip equivalence).
- **Existing self-upgrade artefacts:**
  `self-upgrade/src/self_upgrade/manifest.py`,
  `conflict_report.py`, `conflict_detection.py`,
  `clause_checks.py`, `upgrade.py`, `cli.py`, `paths.py`,
  `snapshot.py`, `rollback.py`. Read these before
  finalising the builder-plan.
- **ODD references:** `docs/odd-methodology.md` §2.5 (no
  non-objective code), §5.3 (Pydantic + model_validators
  as reach-for default), §10 (per-invariant BASELINE
  convention). `docs/odd-in-pos.md` §4 (clause-g pattern
  as canonical example for clause-h composition).
- **Amendment precedents:** amendment #46 (multi-component
  plan-shape with §14 method-decision register),
  amendment #47 (single-sealed-component manifest +
  plan-doc shape), amendment #50 (primary-persona
  conversational-onboarding — translation-burden
  absorption pattern this plan ladders to).

**Ancestor record:** - **Owner reframing 2026-04-26:** canonical IS the release
  source; self-upgrade IS the right mechanism; the AA
  research-doc's recommended `workspace-sync` parallel
  component is reframed as extending self-upgrade with a
  new clause-(h).
- **AA research-doc (277 lines, 2026-04-26):** named seven
  decisions D-1 through D-7; recommended composition over
  new component; flagged D-1 (new spec objective?) as
  boundary-judgment; halt-triggers 1–4 evaluated, none
  fired.
- **Recent precedent for canonical-pull mechanics:** none
  yet — this is the first canonical-pull amendment.
- **Recent precedent for LLM-mediated structured output in
  pos-v2:** memory-system's Graphiti-mediated supersession
  inference (R6); primary-persona's conversational
  onboarding (#50). Same Claude SDK structured-output
  surface; the builder reads existing usage and composes.

**Research:** docs/plans/research/canonical-to-workspace-sync-research.md

---

## 1. Summary / TLDR

Extends the sealed `self-upgrade` framework with a new clause-(h)
acceptance contract: **inference-mediated conflict resolution** that
preserves workspace-supplied content when canonical changes
collide with workspace customisation. Two compositional additions:

1. **Canonical-as-source pull** — wires `pos upgrade` so the
   manifest+staging pair can be sourced from a local canonical
   repository path (or a future GitHub release pointing at the same
   repo) without rebuilding self-upgrade's execution sequence.
   Today self-upgrade expects a pre-unpacked staging tree at
   `--staging-dir`; this amendment adds a `--canonical <path>`
   mode that resolves to the same staging shape.

2. **Clause-(h) LLM-merge gate** — adds a Resolution-enum
   extension (`inferred-accept-canonical`,
   `inferred-accept-workspace`, `inferred-merged`), a per-conflict
   budgeted scope that calls a Claude SDK structured-output
   resolver, an A/B/C class envelope (workspace-state always
   preserved; operator-prefs override-resolved; framework-code
   LLM-resolved on conflict), a stage-then-atomic-accept gate,
   a Pydantic-validated audit log carrying `inferred_resolution`
   + `rationale` + `confidence` + `user_override`, and a
   convergent-idempotency `state.yaml` so re-runs converge.

Both additions compose ONTO existing self-upgrade primitives —
manifest schema, `ConflictReport`, atomic-rollback, history
layout, OTel observability — without rebuilding any of them.
Clause-(h) is a sibling to clauses (a)–(g): the same upgrade
pipeline gains a new structurally-enforced verifier in the
bundle.

The amendment ships as default-on (Class A protection envelope
validates at load-time; missing → load failure). Non-tech users
inherit safe defaults; the operator never has to hand-edit a
conflicts YAML for the workspace-data-loss class of conflict
because the resolver runs first and records its rationale for
human review/override.

**Seal-bookkeeping precondition.** self-upgrade's seal-bookkeeping
infrastructure (`tests/test_no_sealed_amendments.py` +
`tests/SEAL_COMMIT` sidecar + `seals/` directory) was retrofitted
in amendment #53 (commits `636549f` + `1096175` + `8ae1b82`,
2026-04-26). This clause-(h) amendment dispatches against the
post-retrofit tip; `pos-amend apply` operates cleanly without
any retrofit work bundled here.


---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

This amendment binds to **v1.0 self-upgrade objective (line 81 +
Gap-3 acceptance line 114)** and **v1.1 R1 (semantic round-trip
equivalence)**, extending the seven-clause acceptance contract with
a named clause **(h)**. No new top-level objective is required;
the existing self-upgrade objective already names "without
meaningfully disrupting the user's running configuration — their
personas, memory, workflows, projects, plugins, and any
workspace-local customisation" as the property the upgrade must
preserve. Clauses (a)–(g) test that property along seven axes
(active sessions, persona load, memory equivalence, in-flight
tasks, breaking-change surfacing, reversibility, no silent skip).
Clause (h) closes the workspace-customisation-collision axis
the existing seven do not name: when canonical changes a file the
workspace also changed, the resolution is **inference-mediated
with audit and override**, not "the user edits a YAML and decides
blindly."

**Reverse trace per CLAUDE.md §2.5.** Every AC below traces
back to the spec line above + maps forward to AC.PO.1
(translation-burden reduction) and/or AC.PO.2 (toolkit-primitive
growth):

- **AC.PO.1 (translation-burden):** The persona translates "I
  want the latest pos-v2 features in this workspace" or "merge
  canonical updates without losing my personas/state" into
  `pos upgrade --canonical <path>` directly. The user never
  learns the conflict-detection schema, the resolver-prompt
  contract, or the audit-YAML field set. The persona reads the
  audit on the user's behalf and explains low-confidence
  resolutions in natural language. Per amendment #50's primary-
  persona conversational-onboarding precedent (translation
  absorbed in the persona-to-tool layer).
- **AC.PO.2 (toolkit-primitive):** Clause-(h) adds three
  primitives the persona composes against:
  1. **Inferred-resolution audit** — a structured artefact at
     `<workspace>/.pos/upgrade/<tag>/audit.yaml` the persona
     summarises on demand.
  2. **Per-class workspace-data envelope** —
     `sync-protected.yaml` (Pydantic-validated) names which
     workspace paths the framework will never overwrite.
     Future tooling (a workspace-export, a workspace-clone
     primitive) composes against the same envelope.
  3. **LLM-merge-gate scope** — a budgeted scope through the
     four-gate chain. Future plans (memory-system supersession
     inference, plan-doc semantic compare, persona-contract
     merge) compose against the same scope shape.

Self-upgrade is the **right home** because canonical IS the
release source — there is no parallel "workspace-sync"
component, only canonical-as-released-from. The seven-clause
contract scales to clause (h) without structural rebuild
because every clause is a `ClauseResult` returned by a verifier
in the bundle, and clause (h) returns the same shape.


---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

Composes on Claude-native primitives without inventing new ones:

1. **Claude SDK structured-output.** The resolver invokes Claude
   with a Pydantic-typed response shape `{resolution,
   merged_content, rationale, confidence}`. Structured output is
   a Claude-native primitive already used in pos-v2 (memory-
   system's Graphiti-mediated extraction; primary-persona's
   authoring pipeline). No new model surface, no new prompt
   framework.
2. **Cost-governance budgeted scope.** Each per-conflict resolver
   call runs as a budgeted scope through the existing four-gate
   chain. Halt-trigger fires structurally on overrun (clause-(h)
   surfaces "K conflicts deferred — bump budget or resolve
   manually"). No new cost surface.
3. **Observability-aggregator OTel spans.** Resolver emits
   `pos.upgrade.merge_gate.*` spans tagged with conflict path,
   model name, token cost, confidence, override flag. Composes
   on the v1.1 R11 OTel discipline.
4. **Slash-command + persona translation.** Future amendment can
   wrap `pos upgrade --canonical ...` as a `/sync` slash-command
   for persona-invokability — out of scope for this amendment but
   unlocked by it.

No new top-level Claude SDK surface. No new MCP server. No new
hook event. Halt trigger 5 (LLM-call surface that doesn't exist)
does not fire — the resolver uses existing structured-output +
cost-governance primitives.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** Reduces translation burden: today, an
operator with a downstream pos-v2 clone (e.g. pos3) has no path
to update from canonical without manual `git merge` plus
understanding which paths are workspace-supplied. Even a
canonical-maintainer running `pos upgrade` against a release
must hand-edit a conflicts YAML when files conflict. The
inference-mediated resolver + Class-A envelope absorb both
translation chores; the persona invokes one verb, summarises
the audit, and surfaces only low-confidence resolutions for
user review. **Pass.**

**Harness test.** Adds three primitives to the persona's
toolkit (audit-YAML, sync-protected envelope, merge-gate
budgeted scope — listed in §2 above). Each is invocable by
the persona; the audit is in a stable workspace-local path
the persona reads to answer "what changed in the last
upgrade and was anything risky?" **Pass.**

Per AC trace:
- **AC.H.1 → AC.PO.1.** `pos upgrade --canonical <path>`
  absorbs the multi-step "fetch + diff + merge + write
  manifest" chore into one invocation. Persona translates
  user's pull-intent into one verb.
- **AC.H.2 + AC.H.3 → AC.PO.1.** Class-A envelope means the
  user never has to translate "which of my files did the
  upgrade overwrite?" — the answer is structural: A-paths
  are never touched.
- **AC.H.4 + AC.H.5 → AC.PO.1.** LLM-mediated merge with
  audit absorbs the translation burden of "what changed and
  why." User reads the persona's plain-English summary of
  the audit, not the YAML.
- **AC.H.6 → AC.PO.2.** Per-conflict budgeted scope
  composes on cost-governance — toolkit primitive future
  callers (semantic-merge in other contexts) compose
  against.
- **AC.H.7 → AC.PO.1 + AC.PO.2.** Stage-then-atomic-accept
  means the user gets one clear "yes/no/review" gate, not
  a partial-state recovery procedure. Toolkit primitive
  extends self-upgrade's existing atomic-rollback to the
  merge-gate path.
- **AC.H.8 → AC.PO.1.** Convergent-idempotency state.yaml
  means re-runs are safe; the persona never has to translate
  "did I already do this?" — the framework knows.
- **AC.H.9 → AC.PO.2.** Audit override → next-run skip-
  re-inference closes the human-in-the-loop circuit. The
  user's override IS persistent toolkit context the persona
  composes against.
- **AC.H.10 → AC.PO.1.** Default-shipping safe envelope means
  non-tech users get protected-by-default behaviour without
  config. Translation burden = zero on first-run.
- **AC.H.11 + AC.H.12 → AC.PO.2.** Observability span +
  rollback-on-merge-failure compose on existing
  observability/rollback primitives — toolkit primitives
  extended, not duplicated.

### Lens 3 — ODD authoring

ACs §4 are outcome-shaped: each names a state of the world the
amendment must make true, with deterministic test shape. No
method-in-AC (no "uses Pydantic validator", no "calls
ClaudeAdapter", no "implements Protocol X"). Method choices
(resolver client, Pydantic schema layout, audit-file
serialization, integration test fixture shape) are the
builder's call inside §9.x's bookkeeping notes; the AC tests
outcome only.

Behaviour-count check applied in §5. ODD §2.5 reverse trace
is the builder's pre-seal check captured in the builder-plan
(one row per code path → AC).

Halt-and-surface triggers per §10; explicit per
`feedback_subagent_odd_violation_halt`.


---

## 4. Acceptance criteria (AC.H — sealed-component amendment)

Twelve outcome-shaped acceptance criteria (AC.H.1–12) plus the
seal-diff invariant. Each carries the deterministic test shape;
method is the builder's call.

**AC.H.1 — Canonical-as-source pull.** Invoking
`pos upgrade <tag> --canonical <repo-path>` against a workspace
resolves the manifest + staging tree from the canonical
repository at `<repo-path>`'s HEAD (or a tag/SHA passed via a
sub-flag) and produces the same staging shape `pos upgrade
--staging-dir <staging>` does today. A canonical-source
pull invocation that ALSO supplies `--staging-dir` halts at
argument-parse time with a clear error (the two flags are
mutually exclusive). When `--canonical` is absent and
`--staging-dir` is present, behaviour is byte-identical to
pre-amendment (backward-compat).

**AC.H.2 — Class A workspace-state preservation.** A workspace
path declared Class A in `<workspace>/.pos/sync-protected.yaml`
is NEVER overwritten by an upgrade — verified by a fixture in
which a Class-A file (e.g. `personas/<handle>/contract.yaml`,
`<workspace>/.pos/objective_tracker.sqlite`,
`<workspace>/.mcp.json`) is modified on both sides between
prior-tag and target-tag. Post-upgrade the workspace-side
content is byte-identical to its pre-upgrade state and the
audit log records `class: A, action: preserved` for that path.

**AC.H.3 — Class B operator-preference resolution.** A
workspace path declared Class B is overwritten by canonical's
value when the workspace has not modified it; preserved when
the workspace has modified it (override resolution). Verified
by a fixture where Class-B file `<workspace>/memory.yaml` is
modified workspace-side; canonical's matching entry is dropped
from the upgrade and the audit records `class: B, action:
workspace-override`.

**AC.H.4 — Class C inference-mediated resolution.** A Class-C
file (framework code under sealed-component paths or `docs/`)
with both-sides changes triggers the LLM-mediated resolver.
The resolver returns a structured verdict; the verdict's
resolution lands one of three Resolution-enum extensions
(`inferred-accept-canonical`, `inferred-accept-workspace`,
`inferred-merged`); the audit log records the path, both-sides
shas, the verdict, the rationale (free-text), the confidence
(0.0–1.0 float), and `user_override: false`.

**AC.H.5 — Audit log shape.** Every clause-(h) upgrade writes
`<workspace>/.pos/upgrade/<tag>/audit.yaml` containing one
entry per resolved conflict. The schema is Pydantic-validated
on every load; missing required fields raise schema error.
The audit is sorted with low-confidence resolutions first
(deterministic ordering test). The schema rejects
`resolution: skipped` at load — clause-(g)'s no-silent-skip
rule extends to clause-(h).

**AC.H.6 — Per-conflict budget ceiling.** Each per-conflict
resolver invocation runs inside a budgeted scope; cumulative
upgrade budget is bounded by a per-upgrade ceiling read from
`~/.pos/upgrade-config.yaml` (default value declared in the
schema, workspace-tunable). When the ceiling is hit, the
upgrade halts before any further resolver calls; staging is
preserved; the audit records resolved-vs-deferred counts
and the operator can re-run with a higher ceiling or
hand-resolve the deferred conflicts via the existing
conflicts-YAML path.

**AC.H.7 — Stage-then-atomic-accept.** When all conflicts
have a resolution (auto or inferred), staging contains the
full post-merge tree. The operator (or auto-accept if
configured + all confidences exceed a tunable threshold)
fires acceptance: the staging tree applies atomically
(existing atomic-symlink-swap path). On reject, staging is
discarded; workspace state is byte-identical to pre-upgrade.

**AC.H.8 — Convergent idempotency.** Re-running the same
upgrade tag against the same workspace state is a no-op
(no resolver calls, no staging mutation, no audit
re-write). State is recorded at
`<workspace>/.pos/upgrade/state.yaml`; a fixture that
perturbs workspace state between runs and re-invokes
produces a converged result equivalent to a clean invocation
from the perturbed start.

**AC.H.9 — User override persistence.** A user-edited
audit entry that flips `user_override: true` and supplies
`override_rationale` is honoured on the next re-run for the
same `(path, both-sides-shas)` triple — the resolver is NOT
re-invoked; the override resolution is applied directly.
Verified by a fixture that overrides one entry and
re-invokes with the same canonical state.

**AC.H.10 — Class-A envelope ships safe by default.** A
workspace with no `sync-protected.yaml` (fresh clone)
receives a default envelope from canonical's
`self-upgrade/templates/sync-protected.default.yaml` (or
equivalent shipped path) on the first upgrade. The default
envelope's Class-A floor — workspace-state DBs, persona
contracts, `.mcp.json`, `.pos/`, `.scratch/` — is
Pydantic-validated as a framework floor (mirroring
safety-layer's `always_ask.yaml` floor): a workspace cannot
remove framework-floor entries without hitting a load-time
refusal. Verified by a fixture that deletes a
framework-floor key from `sync-protected.yaml`; the next
upgrade refuses to start with a structured error.

**AC.H.11 — Observability span.** Every clause-(h)
resolution emits a `pos.upgrade.merge_gate.resolution`
OTel span with attributes for path, both-sides-shas, model
name, token cost, latency, resolution verdict, confidence,
override flag. Aggregated cost per upgrade emitted as
`pos.upgrade.merge_gate.summary` once per run. Verified by
a fixture that captures the in-process span exporter and
asserts one span per resolution + one summary span per run.

**AC.H.12 — Rollback safety on merge-gate failure.** When
the resolver fails (network error, all retries exhausted,
unresolvable conflict) the upgrade rolls back atomically
using existing rollback machinery: workspace state
byte-identical to pre-upgrade; staging discarded; audit
records the failure with the deferred conflicts; no
partial application. Clause-(h) becomes a verifier in
`run_all_clauses`; a clause-(h) failure triggers the same
rollback path as a clause-(g) failure.

**AC.H.S — Seal-diff invariant.** Diff between BASELINE
and SEAL_COMMIT is confined to `self-upgrade/` plus
amendment-universal admissions
(`docs/plans/`, `CLAUDE.md` if needed,
`docs/FUTURE_IDEAS.md` if needed,
`docs/odd-*.md` if needed). Verified by
`self-upgrade/tests/test_no_sealed_amendments.py` and
the cross-component sweep at seal-time.


---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

Twelve declared behaviours (twelve clause-(h) shapes); twelve
outcome-shaped ACs; one seal-invariant. Match.

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Canonical-as-source pull resolves to existing staging shape | AC.H.1 |
| 2 | Class A workspace-state never overwritten | AC.H.2 |
| 3 | Class B operator-preference override resolution | AC.H.3 |
| 4 | Class C LLM-mediated resolution with verdict + audit | AC.H.4 |
| 5 | Audit log Pydantic-validated, low-confidence-first ordering, no `skipped` | AC.H.5 |
| 6 | Per-conflict budget + cumulative ceiling halt | AC.H.6 |
| 7 | Stage-then-atomic-accept (atomic apply or atomic discard) | AC.H.7 |
| 8 | Convergent idempotency on re-run | AC.H.8 |
| 9 | User override persisted across re-runs | AC.H.9 |
| 10 | Class-A envelope ships safe by default; framework-floor refused if removed | AC.H.10 |
| 11 | OTel span per resolution + summary per run | AC.H.11 |
| 12 | Rollback safety on merge-gate failure | AC.H.12 |
| S | Seal-diff invariant: only `self-upgrade/` + universal paths | AC.H.S |

Forward direction (every behaviour → AC) verified above.
Reverse direction (every code path / branch / dependency →
AC) is the builder's pre-seal check captured in the
builder-plan's §5 (per amendment #46/#47 precedent).


---

## 6. Hard constraints

1. **Sealed-component fence: `self-upgrade/` only** (plus
   universal-paths admissions). Any source-edit OUTSIDE
   `self-upgrade/` triggers halt-and-surface (§10 trigger 4).
   **Test-fixture extensions in adjacent components** (e.g.
   a fixture under `safety-layer/tests/fixtures/` that the
   clause-(h) integration test consumes) are permitted as
   test-only additions; they do NOT count as source edits but
   MUST appear in the manifest's `extra_allowed_prefixes` per
   pos-amend convention.
2. **No new third-party runtime dependency.** The resolver
   uses an existing Claude SDK surface already wired into
   pos-v2 (the structured-output adapter from
   memory-system or primary-persona — exact module is the
   builder's call). If the audit reveals NO suitable
   surface exists, halt-and-surface (§10 trigger 5).
3. **No `--amend`.** Corrective new commits only per
   `feedback_no_amend_in_agent_dispatches`.
4. **Plan-before-code.** This plan exists; the builder
   authors a builder-plan at
   `docs/plans/self-upgrade-clause-h-llm-merge.builder-plan.md`
   before editing any source.
5. **Backward-compat preserved unconditionally.** A `pos
   upgrade <tag> --staging-dir <path>` invocation without
   `--canonical` produces byte-identical behaviour to
   pre-amendment HEAD. No prior caller of `execute_upgrade`
   changes shape; the new clause-(h) verifier is opt-in via
   the manifest declaring conflict-resolver enablement.
   A fresh-clone workspace with no `sync-protected.yaml`
   gets a defaults-write on first invocation; pre-existing
   workspaces with hand-authored YAML are left alone (only
   framework-floor refusal applies).
6. **Workspace data loss is structurally impossible.**
   Class-A protection lives in a Pydantic schema with a
   framework-floor validator. The validator is the
   reach-for default (per `odd-methodology.md` §5.3) and
   must refuse construction of a `SyncProtected` instance
   missing any framework-floor key. The Resolution enum
   extension does NOT include any value that authorises
   overwrite of a Class-A path.
7. **Resolver is fail-closed.** When the LLM call fails or
   returns a verdict the schema rejects, the upgrade halts
   and rolls back. The framework MUST NOT silently treat
   a resolver failure as `accept-canonical` or
   `accept-workspace`.
8. **Auto-accept is opt-in, not default.** Default
   behaviour is "operator confirms acceptance after
   audit." Auto-accept on high-confidence requires an
   explicit `~/.pos/upgrade-config.yaml` opt-in plus a
   declared confidence floor; fail-closed if either is
   absent.
9. **CDC adherence.** scope-only-dispatch CDC (the
   dispatch carries objective + scope + halt + ODD-check;
   the builder authors method in the builder-plan).
   Standard pos-amend manifest discipline. `pos-amend
   seal --plan-doc <abs-path>` backfills §14.
10. **No top-level objective added.** Per D-1 of the
    research-doc + owner reframing 2026-04-26: composition
    on the existing self-upgrade objective. If the build
    surfaces a hard need for a new top-level objective,
    halt-and-surface (§10 trigger 1) — do NOT silently
    promote.


---

## 7. Out of scope (explicit)

Per ODD §2.5 and the owner's locked reframing 2026-04-26:

- **Persona-invokable `/sync` slash-command.** Composes on
  this amendment's CLI surface but is a separate amendment
  (Lens 1 future work; the dispatch-template family or a
  targeted persona amendment). Out of scope here.
- **GitHub release distribution.** Canonical IS the release
  source today; a future amendment can wire `--canonical
  <git-url>` to fetch a remote into a tmp worktree. The
  `--canonical <local-path>` path in this amendment is the
  minimum surface needed; the URL form is deferred.
- **Cross-workspace sync between two non-canonical clones.**
  Out of scope — clones pull from canonical, not from each
  other.
- **Background-scope mode.** D-3 of the AA research locked
  background-scope as a future shape; this amendment ships
  foreground (operator runs `pos upgrade`, sees the audit,
  accepts/rejects). Future amendment composes the
  `BackgroundWorkMonitor` integration.
- **Multi-conflict batched LLM call.** Each conflict gets
  its own resolver call (D-5 per-conflict-budget). Future
  amendment may batch low-confidence-only into one call;
  out of scope.
- **Auto-accept by default for non-tech UX.** Locked
  against by Luke's hard requirement "every conflict
  resolution surfaces what was decided + why, so the user
  can review and override." Auto-accept opt-in only.
- **Workspace-clone primitive.** A `pos clone-workspace
  <src> <dst>` primitive — listed in the harness-test
  section but the canonical-pull case does not require it.
  Out of scope; future amendment.
- **Resolver model selection / cost-tier tuning.** The
  resolver uses the harness's existing default Claude
  model (Sonnet for routine, Opus for complex per global
  CLAUDE.md). Per-conflict model choice based on file
  size or class is a future tuning amendment.
- **Telegram-channel surfacing of audit.** `pos.upgrade.*`
  OTel spans flow into observability-aggregator; how the
  persona delivers the audit to the user (Telegram,
  inline-text, etc.) is the persona's call, not this
  amendment.


---

## 8. Implementation order (suggested — builder's call to refine)

Suggested order — builder's call to refine in the builder-plan:

1. **Read session-start corpus + this plan + the AA
   research-doc** at
   `docs/plans/research/canonical-to-workspace-sync-research.md`.
   The AA research D-2 through D-7 decisions are LOCKED for
   this amendment.
2. **Author builder-plan** at
   `docs/plans/self-upgrade-clause-h-llm-merge.builder-plan.md`
   before any source edit. Builder-plan captures D-build.x
   method choices and the §2.5 reverse-direction trace.
3. **Verify canonical-as-source feasibility** by reading
   `self-upgrade/src/self_upgrade/cli.py` + `upgrade.py` +
   `paths.py`. Halt-and-surface (§10 trigger 6) if
   `--canonical` cannot be wired without rebuilding the
   execute_upgrade pipeline.
4. **Verify resolver-surface feasibility** by reading the
   existing structured-output adapter under memory-system
   or primary-persona. Halt-and-surface (§10 trigger 5) if
   no suitable surface exists and pos-v2 needs a new LLM
   surface added.
5. **Land schema additions first** —
   `sync-protected.yaml` schema + framework-floor
   validator; Resolution enum extension; audit-YAML
   schema. Tests for each: fixture refuses missing
   framework-floor; enum rejects `skipped`; audit-YAML
   round-trips.
6. **Land canonical-pull adapter** — argparse `--canonical
   <path>`; staging-dir resolution from a local repo path;
   mutual-exclusion validation with `--staging-dir`. Tests
   for each: fixture pulls from a tmp canonical repo;
   fixture rejects both flags together; backward-compat
   fixture with `--staging-dir` only.
7. **Land class-envelope diff classifier** — for each file
   in the manifest, classify as A/B/C against
   `sync-protected.yaml`; emit per-file `Class` enum.
   Tests for fixtures hitting each class.
8. **Land LLM-merge resolver** — per-conflict budgeted
   scope; structured-output call; verdict validation.
   Tests with a stub resolver for deterministic verdicts;
   one integration test against the real adapter
   (skip-if-no-key gate per existing test convention in
   primary-persona / memory-system).
9. **Land audit-YAML writer + state.yaml updater + clause
   (h) verifier** — wire into `run_all_clauses` so a
   clause-(h) failure triggers existing rollback. Tests
   for audit ordering (low-confidence first); state.yaml
   idempotency; verifier-fail → rollback fixture.
10. **Land OTel span emission** + summary span. Tests
    with the in-process span exporter.
11. **Run touched-component suite** then `pos-amend apply
    --dry-run`; if clean, run amendment commit; then
    `pos-amend seal --plan-doc <abs-path>`.
12. **Verify backward-compat** with the pre-amendment
    `pos upgrade <tag> --staging-dir <path>` invocation
    shape on a fixture; assert byte-identical behaviour.


---

## 9. Bookkeeping surface

Sealed-component amendment against the post-#53 (seal-bookkeeping
retrofit) tip. self-upgrade now carries the B20 / B23 seal-test
infrastructure (`tests/test_no_sealed_amendments.py` +
`tests/SEAL_COMMIT` sidecar + `seals/`); this amendment extends
that infrastructure's `allowed_prefixes` set and writes a new
`seals/SEAL_COMMIT.clause-h-llm-merge` narrative artefact during
the seal cycle. The cross-component sweep already covers all 14
sealed components after #53 sealed.

`pos-amend` manifest sketch (builder finalises in
`<slug>.manifest.yaml`):

```yaml
schema_version: 1
amendment:
  number: <N>  # next free amendment number at dispatch time
  slug: self-upgrade-clause-h-llm-merge
  title: "self-upgrade clause-(h) — canonical pull + LLM-mediated semantic-merge gate"

# BASELINE pinned to HEAD~1 of the amendment commit (per
# amendment #29 / #34 / #35 / #36 / #37 / #38 / #39 / #42 /
# #46 / #47 BASELINE-as-HEAD~1 pattern). Builder fills SHA
# at apply time.
baseline: <HEAD~1 SHA>

plan: docs/plans/self-upgrade-clause-h-llm-merge.md

components:
  - name: self-upgrade
    seal_test: self-upgrade/tests/test_no_sealed_amendments.py
    sidecar: self-upgrade/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []
    # seal_test + sidecar already exist (retrofitted in
    # amendment #53 — commits 636549f + 1096175 + 8ae1b82).
    # This amendment widens the test's allowed_prefixes /
    # allowed_files sets to admit the clause-(h) surface
    # (templates dir, .pos/upgrade/ paths, etc.).
    # If the integration test requires a fixture under
    # another sealed component (e.g. a stub persona under
    # primary-persona/tests/fixtures/), add the path here
    # as test-only admission. Halt-and-surface if source
    # edits become required outside self-upgrade.

universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/FUTURE_IDEAS.md

narrative:
  target: self-upgrade/seals/SEAL_COMMIT.clause-h-llm-merge
  body: |
    # Amendment #<N> — self-upgrade clause-(h)
    #                  canonical pull + LLM-mediated
    #                  semantic-merge gate

    <builder finalises body — see narrative shape in
    amendment-46 + amendment-47 manifests + the
    primary-persona/seals/SEAL_COMMIT.conversational-onboarding
    surface-delta narrative for precedent.>
```

**Dependents cleared at seal:** none in-flight at this
authoring time. Future amendments composing on clause-(h)
(slash-command `/sync`, `--canonical <git-url>` extension,
background-scope mode) become unlocked once this seals.

**Test-fixture admissions** (extra_allowed_prefixes): if
the integration test requires a synthetic canonical-repo
fixture or a stub workspace under another sealed component,
the manifest's `components[].extra_allowed_prefixes` lists
it explicitly. Test-only — no source edits. The
`test_no_sealed_amendments.py` for the touched component
re-runs at seal-time per pos-amend convention.

**Universal admissions** match amendment #47's pattern.

**Frozen-baseline:** `false`. self-upgrade is not the
hands-off-lifecycle frozen-BASELINE component (per ODD §10).


---

## 10. Halt triggers (builder halts + signals owner)

Builder halts and signals owner if any of the following
fire. Each carries a specific surface check; the builder
does NOT silently extend a violation per
`feedback_subagent_odd_violation_halt`.

1. **A required new top-level spec objective surfaces.** The
   research-doc's D-1 named this as boundary-judgment;
   owner reframed 2026-04-26 against (b) composition.
   If during build the work cannot fit under existing
   v1.0 self-upgrade objective + v1.1 R1 + AC.PO.1/2,
   halt and surface to owner.
2. **ODD violation observed in surrounding code/docs.**
   Per `feedback_subagent_odd_violation_halt`, halt and
   surface; do NOT extend a violating surface. Specifically:
   if `self-upgrade/src/`'s existing modules contain
   §2.5 violations (code paths without backing AC), halt
   before extending — the amendment's diff may not
   propagate the violation.
3. **An AC cannot be authored outcome-shaped.** If a
   behaviour the build needs to satisfy can only be tested
   by asserting a method choice (a specific class name, a
   specific module's import), halt — the AC-author
   (owner) must rewrite as outcome.
4. **Required source-edit outside `self-upgrade/`.** Halt
   and surface. Test-fixture admissions in adjacent
   components are permitted via `extra_allowed_prefixes`
   (test-only); source edits are not.
5. **LLM-merge mechanism requires a Claude SDK surface
   pos-v2 doesn't have wired.** Per dispatch §"Halt-and-
   surface": if the resolver-surface audit reveals no
   existing structured-output adapter is composable for
   the per-conflict resolver, halt and surface — pos-v2
   may need an LLM-call-surface amendment first.
6. **Self-upgrade's clause-(a) through clause-(g)
   machinery does not compose cleanly with clause-(h).**
   Per dispatch: if `run_all_clauses` cannot accommodate
   a new verifier without rebuilding the bundle's data
   contract, or if `execute_upgrade` cannot accommodate a
   new pre-stage step without rebuilding the pipeline,
   halt and surface — amendment is structural rather than
   compositional and owner must rule on whether
   self-upgrade rebuild is acceptable.
7. **Workspace data loss can be reproduced under any
   legitimate input combination.** AC.H.2 + AC.H.10 are
   hard requirements. If a fixture the builder authors
   produces a state where a Class-A path was overwritten,
   halt — the structural validator is broken.
8. **Amendment scope expansion crosses sealed-component
   fences beyond test-fixture admissions.** Halt.
9. **Wall-time exceeds projected 4–6 hours of build.**
   Halt with current-state report; owner triages whether
   to continue or split into sub-amendments.


---

## 11. Decisions remaining for the owner to rule on

Most decisions from the AA research-doc are LOCKED by Luke's
reframing 2026-04-26 (D-2 through D-7 compose ONTO
self-upgrade per dispatch §"Locked design constraints").
Two decisions remain genuinely uncertain at plan-author time
and require owner ruling before the builder dispatches.

### D-1. Default per-upgrade resolver budget ceiling

**Question.** What is the default value for the upgrade-
level cumulative resolver-budget ceiling (workspace-tunable
in `~/.pos/upgrade-config.yaml`)?

**Why genuinely uncertain.** Per-conflict budget shape
is locked (D-5 of AA research). The PER-UPGRADE ceiling
default is not — it depends on (a) typical pos-v2 release
diff size (small at canonical-as-source today; could grow
later with external GitHub releases), (b) Sonnet vs Opus
default model, (c) tolerance for halt-and-resume vs
let-it-run.

**Recommendation.** **Default 100k tokens** for the
cumulative ceiling, **5k tokens per-conflict budget**
(gives ~20 conflicts headroom on the cumulative; a
typical pos-v2 amendment touches ≤10 files). Workspace-
tunable. Halt-and-resume on hit per AC.H.6. If owner
prefers a tighter ceiling (e.g. 25k for cost discipline)
or a tighter per-conflict budget (e.g. 2k for
determinism), confirm at dispatch time — value changes
by config-default value only, no AC change.

### D-2. Confidence threshold for auto-accept opt-in

**Question.** When the operator opts into auto-accept
via `~/.pos/upgrade-config.yaml`, what's the default
confidence floor (per AC.H.7's tunable threshold)?

**Why genuinely uncertain.** Auto-accept is opt-in not
default (locked per Hard Constraint 8). The DEFAULT
threshold for the opt-in mode is not locked. Too-low
→ user gets surprised by a resolution they'd have
challenged; too-high → user halts on resolutions the
framework was confident enough about to ship safely.

**Recommendation.** **Default 0.90** (Sonnet-class
resolver should hit ≥0.90 on routine resolutions;
edge-cases drop below). Workspace-tunable. Combined
with the audit-log's low-confidence-first ordering,
this means the operator sees the lowest-confidence
resolutions when reviewing — the threshold determines
which fall ABOVE the auto-accept line, not whether
audit exists. If owner prefers 0.95 (more conservative)
or 0.85 (more permissive), confirm at dispatch time.

### Decisions LOCKED by AA research + Luke 2026-04-26 reframing
(NOT for owner ruling here — captured for builder reference):

- D-AA-2 (CLI surface): both — `pos upgrade --canonical`
  in this amendment; slash-command `/sync` is a future
  composition.
- D-AA-3 (resolver timing): foreground per-conflict in
  this amendment; background-scope is future
  composition.
- D-AA-4 (workspace-data envelope): A/B/C class envelope
  via Pydantic-validated `sync-protected.yaml`,
  framework-floor refused on removal.
- D-AA-5 (per-conflict budget): per-conflict budgeted
  scope through cost-governance; cumulative per-upgrade
  ceiling above (D-1 default).
- D-AA-6 (failure mode): stage-then-atomic-accept
  (D-AA-6 (c) of AA research).
- D-AA-7 (idempotency): convergent via state.yaml.


---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-1. Default per-upgrade resolver budget ceiling | **100k tokens cumulative, 5k per-conflict** (workspace-tunable) | Bounds total upgrade cost; halts on overrun; default chosen for typical ≤10-file pos-v2 release |
| D-2. Default confidence floor for auto-accept opt-in | **0.90** (workspace-tunable) | Determines which resolutions auto-apply when operator opts in; 0.90 = Sonnet routine-confidence; reviewable always via audit |

All other AA-research decisions LOCKED 2026-04-26 by Luke's
reframing. Builder proceeds against locked values.


---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface
any ODD violation observed in surrounding code/docs.

Plan-authoring scope (read-only audit of `self-upgrade/src/`,
the AA research-doc, the spec, recent amendment plans):

- **None observed in `self-upgrade/src/`'s existing surface.**
  The `Resolution` enum's structural exclusion of `skipped`
  is exemplary (clause-g pattern; canonical example in
  `odd-in-pos.md` §4). The `ConflictEntry` model_validator
  is structural-refusal-by-default. The `execute_upgrade`
  pipeline's clause-bundle pattern composes cleanly with a
  new clause-(h) verifier without rebuild.
- **None observed in spec line 81 + line 114 + R1.** The
  self-upgrade objective text is outcome-shaped; the
  clause-(g) line ("when a change cannot be applied due to
  conflict with user customisation, the conflict is
  surfaced with explicit resolution options rather than
  silently dropped") already names the property clause-(h)
  will mechanise — composition, not amendment of the
  contract.
- **None observed in AA research-doc.** Decisions are
  cleanly numbered, each with recommendation. Owner's
  2026-04-26 reframing (compose onto self-upgrade rather
  than parallel `workspace-sync` component) is captured
  in the dispatch + locked here.

**Potential structural-rebuild concern flagged for builder
attention (NOT a halt — verify-then-proceed):** clause-(h)
is the FIRST clause that runs PRE-stage (the resolver must
decide before the manifest's expected-post-shas are
meaningful — workspace-side may have legitimately different
content the resolver merges into the post-sha). Existing
clauses (a)–(g) all run POST-restart. The pipeline's
dataflow may need a new pre-stage hook (or clause-(h) is a
pre-stage gate that mutates the staging tree before the
symlink swap). Halt-trigger 6 fires if this can't compose
cleanly; otherwise the builder authors the pre-stage
position in the builder-plan's D-build.x.

### §4 re-extension register (ODD §2.4)

Per `odd-methodology.md` §2.4 + `feedback_loose_AC_text_fix_AC_not_implementation`:
acceptance-criteria text revisions during plan authoring are
recorded here so the §4 surface has a versioned audit trail.

| # | Date | Driver | Surface | Note |
|---|------|--------|---------|------|
| 1 | 2026-04-26 | Plan-split (BB-feat dispatch after retrofit landed as #53) | §1 TLDR; §4 (AC.H.0 removed); §5 row 0; §6 constraint #11; §9 manifest narrative + retrofit-precedent reference | Original BB plan bundled the seal-bookkeeping retrofit (AC.H.0) into the clause-(h) amendment. The retrofit subsequently landed as its own amendment (#53; commits 636549f + 1096175 + 8ae1b82 on 2026-04-26). The bundled-retrofit text was reverted from this plan-doc; the clause-(h) feat dispatches against the post-#53 tip and operates against existing seal-bookkeeping infrastructure. No clause-(h) AC text changed. |


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

- Amendment commit: `0737e7ccf74caaf6f0defbb759c3952b9bb599f2` —
  `feat(self-upgrade): clause-(h) canonical pull + LLM-mediated semantic-merge gate (amendment #54, AC.H.1–AC.H.12 + AC.H.S)`
- Seal commit: `1fd826afe150327135024dde99d9a7bd4f41fa57` —
  `chore(seals): self-upgrade clause-(h) — canonical pull + LLM-mediated semantic-merge gate — self-upgrade at 0737e7c`
### Commit SHAs

(populated by `pos-amend seal --plan-doc <this-file> ...` after build, or appended manually for dev-discipline plans)

### Dependents cleared to dispatch

(placeholder)

---

## 15. References

- CLAUDE.md (project + global)
- `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- `docs/VALUE_PROPOSITION.md`, `docs/STATE.md`,
  `docs/FUTURE_IDEAS.md`
- `docs/spec/pos-v2-objectives-spec.md` (v1.0 + v1.1
  + v1.2 — self-upgrade objective at line 81; clause-g
  + workspace-customisation conflict surfacing at line 114;
  v1.1 R1 at line 213)
- `docs/plans/research/canonical-to-workspace-sync-research.md`
  (AA research, 277 lines, 2026-04-26; D-1 through D-7
  decisions; locked compositional reframing 2026-04-26)
- `self-upgrade/src/self_upgrade/manifest.py` (manifest
  + FileEntry schema)
- `self-upgrade/src/self_upgrade/conflict_report.py`
  (Resolution enum + ConflictEntry; clause-g structural
  refusal pattern)
- `self-upgrade/src/self_upgrade/conflict_detection.py`
  (sha-comparison structure for conflict classification)
- `self-upgrade/src/self_upgrade/clause_checks.py`
  (ClauseBundle + run_all_clauses — clause-h plugs in here)
- `self-upgrade/src/self_upgrade/upgrade.py`
  (execute_upgrade pipeline — clause-h pre-stage position
  decided by builder)
- `self-upgrade/src/self_upgrade/cli.py` (argparse surface;
  `--canonical` lands here)
- `self-upgrade/docs/architecture.md` (system diagram,
  trust boundaries, failure modes table)

