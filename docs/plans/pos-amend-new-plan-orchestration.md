# pos-amend `new-plan` orchestration + plan-doc skeleton template — plan

Dev-discipline work. **NOT** a sealed-component amendment. No `pos-amend` manifest, no `SEAL_COMMIT` bump, no seal commit. `tools/pos-amend/` lives outside the sealed-component fence (per CLAUDE.md operational caution §2.5 — `tools/` is dev-discipline territory). Plan-before-code per the dev CDC; corrective new commits land the change.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Companions:** `docs/plans/dispatch-prompt-template-extension.md` (engine landed at commit `dbabd37` — this plan composes on top), `docs/plans/pos-amend-seal-automation-extension.md` (the §14 `### Commit SHAs` subsection scaffold this plan must preserve byte-identical).
**Ancestor record:** `docs/FUTURE_IDEAS_DRAFT.md` entries "Plan-doc skeleton template" (line 25), "`pos-amend new-plan <slug>` orchestration" (line 57), and the §14 / one-test-file-per-AC lessons (lines 71–72, 80).
**Research:** `docs/plans/research/pos-amend-new-plan-orchestration-research.md`.

---

## 1. Summary / TLDR

Every amendment plan today is authored from precedent — the plan author opens the most recent plan, copies its 13-section structure, and rewrites the contents. That precedent-by-copy mechanism is the same failure shape that the dispatch-prompt-template-extension already fixed for dispatch prompts: shape propagated by hand, drift accumulating, every plan author re-deriving the same scaffold.

This plan extends `tools/pos-amend/` with two purely additive pieces:

1. **Plan-doc skeleton template** — extends the existing `tools/pos-amend/templates/plan/dev-discipline.md` (already present after `dbabd37`) so it carries the full 13-section plan-doc shape with sensible defaults baked into the recurring sections (hard-constraints stub, halt-triggers stub, implementation-order stub, §14 method-decision register scaffold). The frontmatter contract grows from 13 required vars to 16 required + 7 optional vars (per the research-doc inventory). The existing `pos-amend template render plan/dev-discipline --vars-file …` invocation continues to work; no engine code changes.
2. **`pos-amend new-plan <slug>` orchestration** — new CLI subcommand that, given a slug, scaffolds an empty-but-pre-stubbed vars-file at a predictable path (`<repo>/docs/plans/<slug>.vars.yaml`), pre-fills `TITLE` / `AC_PREFIX` from optional CLI args, fills `RESEARCH_PATH` and `STATUS_LINE` from the slug + current date, and (with `--render`) immediately renders the plan-doc to `<repo>/docs/plans/<slug>.md`. Leverages the existing `pos-amend template render` engine — no engine change.

The §14 method-decision register heading is pre-authored verbatim in the skeleton (matching the existing `dev-discipline.md` scaffold) so `pos-amend seal --plan-doc <abs-path>` continues to backfill the `### Commit SHAs` subsection without modification. The one-test-file-per-AC convention is observed for the new orchestration's tests.

The plan author's authoring burden when starting a new plan collapses from "open the most recent plan, copy + rewrite 13 sections by hand" to "run `pos-amend new-plan <slug> --title "…" --ac-prefix AC.X.x`, edit the scaffolded vars-file, run `pos-amend template render plan/dev-discipline --vars-file <path> --out <plan> --force`."

Per CLAUDE.md output conventions, owner reads from §11 (decisions for owner) — every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

§2.5 reads: *"Before scoping anything as a sealed-component amendment, name the specific spec objective (v1.0/v1.1/v1.2) the code will satisfy. If I can't name one, the work is dev-discipline (CLAUDE.md, docs, CDCs, tools/), not a sealed-component cycle."*

**No single spec objective names "pos-amend scaffolds plan-doc vars-files."** The work is operational developer-tooling: it speeds primary-persona translation work (plan-author authoring) by collapsing the "copy the most-recent plan and rewrite" precedent-by-copy mechanism into a templated scaffold. That is dev-discipline territory by every property §2.5 names:

- pos-amend lives under `tools/`.
- pos-amend has no spec objective; its load-bearing-ness is operational.
- The extension is internal to `tools/pos-amend/` plus one template file under `tools/pos-amend/templates/plan/`; no sealed component's source changes.
- This is the same §2.5 framing used by `dispatch-prompt-template-extension.md`, `pos-amend-seal-automation-extension.md`, `pos-amend-tracker-integration.md`, and `pos-amend-install-instructions-fix.md`.

**Tiered determinism + non-tech users + meta-discipline framing.** Per CLAUDE.md §2.5 reverse-direction observation: this work increases determinism in plan authoring (the same skeleton renders byte-identically every time), reduces translation burden for the persona at plan-author time (one less precedent to load and one less shape to re-derive), and lives in `tools/` where dev-discipline tooling for the build harness belongs. The work ladders to the prime objective AC.PO.1 (translation absorbed in the template-rendering layer, plan-author burden shrinks) and AC.PO.2 (the `new-plan` orchestration becomes a toolkit primitive future plan-author tools compose against).

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

**What Claude capability does this lean on or extend?**

Two surfaces, both already in use by the dispatch-prompt-template-extension:

1. **The existing `pos-amend template` engine** (landed at `dbabd37`). The engine reads markdown files with `{{var}}` placeholders and YAML frontmatter declaring the variables contract; substitution is deterministic; `\{{` / `\}}` escape literal braces. The plan-doc skeleton plugs into this engine unchanged — the new template is just one more `<family>/<id>.md` file under the existing `templates/` tree. The orchestration is sugar over `pos-amend template render`. Claude leverage: no new engine, no new format, no new dispatch shape. Reuses the engine 1-to-1.
2. **Claude Code skills (D-3c follow-up shape).** Per the dispatch-prompt-template-extension's D-3 ruling, each registered template can be wrapped as a `.claude/skills/<family>-<id>/` skill that the persona invokes by skill-name. The same shape applies here: `new-plan` itself can be a skill (`.claude/skills/new-plan/`) that wraps `pos-amend new-plan <slug>`, allowing the primary persona to invoke "scaffold a new plan called X with AC-prefix Y" by skill-name rather than CLI invocation. Per the dispatch-template plan §11 D-3, skills wiring is a small follow-up commit AFTER the engine/orchestration lands; out of scope for this plan's build but unlocked by it.

The orchestration does NOT lean on hooks, MCP, background-tasks, or the persona-tracker context. (Idea 17's dispatch-template ↔ persona-tracker composition is the closest sibling and is sequenced AFTER this plan + dispatch-template both stabilise — see research §6.3.)

The CLI shape (`pos-amend new-plan <slug>`) is invocable from any Claude tool surface (Bash, skills, hooks, slash-commands) without further integration.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

Yes — load-bearing for the persona's plan-authoring translation work. Today, when the user says "design feature X" and the persona reaches the plan-authoring step, the persona's translation burden includes recalling the 13-section plan shape from memory or from the most-recent precedent. Drift compounds: a CDC update that changes section §6's expected content, or a new feedback rule that wants a §13 framing change, propagates only when the next plan author remembers to apply it. The skeleton template absorbs that translation burden: the shape is rendered from a single source-of-truth file, every plan from now on inherits the current shape, and updates land in one place.

**AC-trace to AC.PO.1 (every AC traces explicitly):**

- **AC.D-np.1 → AC.PO.1.** A vars-file scaffolded by `pos-amend new-plan` carries the plan-doc's full variable contract pre-stubbed; the plan author edits content, not structure. Translation burden absorbed in the scaffold layer.
- **AC.D-np.2 → AC.PO.1.** `--title` / `--ac-prefix` CLI args pre-fill the trivially-known variables; the plan author does not re-author them. Translation burden absorbed at the CLI surface.
- **AC.D-np.3 → AC.PO.1.** `--render` end-to-end produces the plan-doc on disk in one invocation; the plan author proceeds directly to editing the vars-file (which re-renders) rather than juggling two artefacts at scaffold time.
- **AC.D-np.4 → AC.PO.1.** Slug validation + refuse-overwrite + structured diagnostics; no silent-overwrite of a plan-author's prior work. Failure modes absorbed at the boundary.
- **AC.D-np.5 → AC.PO.1.** The skeleton renders cleanly against a fixture vars-file → byte-identical fixture output; the test guarantees the scaffold is rendering-clean every commit, not just at ship.
- **AC.D-np.6 → AC.PO.1.** Backward-compat — every pre-existing pos-amend invocation byte-identical; introduction of `new-plan` does not regress any pre-extension test. Translation burden of "what does pos-amend do today" is preserved.

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — `pos-amend new-plan` becomes a load-bearing toolkit primitive the primary persona can name by skill-id. Future tooling composes:

- A SessionStart hook that invokes `pos-amend new-plan` when the persona starts authoring a new amendment plan (slug derived from the currently-in-flight feature name).
- A slash-command (`/new-plan <slug>`) that wraps the orchestration.
- The Idea 17 dispatch-template ↔ persona-tracker composition reuses the same vars-file scaffold pattern for tracker-driven dispatch authoring.
- The FUTURE_IDEAS_DRAFT-named follow-ups `pos-amend new-memory <slug>` and `pos-amend new-commit <kind>` are mechanical generalisations of `new-plan`'s shape.

**AC-trace to AC.PO.2 (every AC traces explicitly):**

- **AC.D-np.1 + AC.D-np.2 + AC.D-np.3 → AC.PO.2.** Scaffold primitive, CLI-arg-pre-fill primitive, render-end-to-end primitive — all toolkit-shaped.
- **AC.D-np.4 → AC.PO.2.** Failure-mode primitive (composable: a future hook can rely on the structured-diagnostic exit code).
- **AC.D-np.5 → AC.PO.2.** Skeleton-rendering test primitive (every shipped template gets a fixture-clean test; the same shape applies to memory-doc / commit-message families when they land).
- **AC.D-np.6 → AC.PO.2.** Opt-in surface — `new-plan` is invoked only when the user/persona names it; explicit escape-shape preserves all pre-extension callers.
- **AC.D-np.7 → AC.PO.2.** The skeleton template IS the toolkit primitive; every authored plan from the day this lands forward composes against the same shape.

### Lens 3 — ODD authoring

The plan authors seven outcome-shaped acceptance criteria (§4) under §2.5 framing. Each AC names what must be true; method (the exact module layout, whether the orchestration is one file or sub-package, the exact YAML scaffold byte-format, the precise CLI-arg parser shape, whether `--render` calls `pos-amend template render` via subprocess or in-process import, whether the slug regex is `^[a-z][a-z0-9-]*$` or something tighter — all method) is the builder's call.

ODD §2.5 reverse-direction check: every new code path traces back to AC.D-np.1 – AC.D-np.7. No platform branches, no "useful later" knobs. The skeleton's vars-file scaffold contents are scoped explicitly in §7 (out-of-scope) — the memory-doc and commit-message generalisations land later as separate efforts.

---

## 4. Acceptance criteria (AC.D-np.x — dev-discipline plan, prefix distinguishes from sealed-amendment ACs and from sibling pos-amend dev-discipline plans)

Each AC maps to at least one test function in `tools/pos-amend/tests/`. One test file per AC per the convention from AC35.x onward.

### AC.D-np.1 — `pos-amend new-plan <slug>` scaffolds a vars-file at the predictable path

Invoking `pos-amend new-plan <slug>` (with no other flags) writes a YAML vars-file at `<repo-root>/docs/plans/<slug>.vars.yaml`. The file is a YAML mapping carrying one entry per required variable in the plan-doc skeleton's frontmatter contract (the 16 required vars per the research-doc inventory), with each value pre-stubbed (empty string, empty multi-line block, or default authored stub). Optional variables that have sensible defaults (`STATUS_LINE`, `RESEARCH_PATH`, `WORKING_DIRECTORY`) are also written into the vars-file with their default values, commented or uncommented per the builder's call. The file is well-formed YAML — `yaml.safe_load` against it produces a dict whose keys are the declared variable names.

**Test shape:** in a tmpfs-mocked repo, invoke `pos-amend new-plan example-slug`; assert `<repo>/docs/plans/example-slug.vars.yaml` exists; assert `yaml.safe_load(path)` returns a dict; assert every required variable from the skeleton's frontmatter is present as a key; assert no syntax errors when piped to `pos-amend template render plan/dev-discipline --vars-file …`.

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.D-np.2 — `--title` and `--ac-prefix` pre-fill the corresponding vars

Invoking `pos-amend new-plan <slug> --title "Some Title" --ac-prefix AC.X.x` writes a vars-file whose `TITLE` value equals `"Some Title"` and whose `AC_PREFIX` value equals `"AC.X.x"`. Other variables retain their default-stubbed values. `--title` and `--ac-prefix` are independently optional — passing only one pre-fills only that variable.

**Test shape:** invoke with both flags; parse the resulting YAML; assert exact-string equality on `TITLE` and `AC_PREFIX`. Invoke with only `--title`; assert `AC_PREFIX` is its default-stubbed value. Invoke with neither; assert both are default-stubbed.

**Maps to:** AC.PO.1 + AC.PO.2 (CLI-arg-pre-fill primitive).

### AC.D-np.3 — `--render` produces a plan-doc end-to-end

Invoking `pos-amend new-plan <slug> --title "T" --ac-prefix AC.X.x --render` writes BOTH the vars-file at `<repo>/docs/plans/<slug>.vars.yaml` AND a rendered plan-doc at `<repo>/docs/plans/<slug>.md`. The rendered plan-doc carries every section heading from §1 through §14 verbatim (including §14 method-decision register subsection scaffold), the `TITLE` substitution in the heading-1, the `AC_PREFIX` substitution in §4's heading and body references, and the §14 `### Commit SHAs` subsection scaffold (so `pos-amend seal --plan-doc <abs-path>` finds its target verbatim).

**Test shape:** invoke with `--render`; assert both files exist; grep the rendered plan-doc for each of `## 1.`, `## 2.`, …, `## 14.` headings; grep for the title in the heading-1; grep for `AC.X.x` in §4's heading; grep for `### Commit SHAs` under §14.

**Maps to:** AC.PO.1 + AC.PO.2 (render-end-to-end primitive).

### AC.D-np.4 — Failure modes halt with structured diagnostics; no partial output

When `pos-amend new-plan` encounters one of:

- (a) an invalid slug (slug containing `/`, slug not matching `^[a-z][a-z0-9-]*$`, empty slug),
- (b) a vars-file path that already exists and `--force` is not passed,
- (c) a `--plan-out` path that already exists and `--force` is not passed (when `--render`),
- (d) a template-render contract failure (e.g. malformed `--title` content that breaks YAML, the skeleton's frontmatter went missing — pathological cases),
- (e) IO failure (write permission denied, parent directory not writable),

it (1) halts before any partial file is written, (2) emits a structured diagnostic to stderr naming the failure class + the specific identifier involved, (3) exits non-zero in the existing 1/2/3 taxonomy `pos-amend` already uses (no new exit code introduced — class (a)–(d) → 2; class (e) → 3).

**Test shape:** fixture-inject each failure class; assert non-zero exit with the documented mapping; assert diagnostic on stderr; assert no partial vars-file or plan-doc on disk.

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.D-np.5 — The skeleton template renders cleanly against a fixture vars-file

The post-extension `tools/pos-amend/templates/plan/dev-discipline.md` skeleton renders against a fixture vars-file (committed as test data) to produce byte-identical fixture-expected output. The fixture exercises every required variable + every optional variable with non-default values; the output proves the skeleton is rendering-clean (no unmatched placeholders, no missing sections, no malformed substitutions). The §14 scaffold subsections (`### D-build.x`, `### Test breakdown`, `### Backwards-compat verification`, `### Commit SHAs`, `### Dependents cleared to dispatch`) appear verbatim in the rendered output.

**Test shape:** fixture vars-file at `tools/pos-amend/tests/fixtures/plan-skeleton/vars.yaml`; fixture expected-output at `tools/pos-amend/tests/fixtures/plan-skeleton/expected.md`; render via `pos-amend template render plan/dev-discipline --vars-file <fixture>`; assert byte-equal against expected.

**Maps to:** AC.PO.1 + AC.PO.2 (the skeleton IS the primitive; this test is its CI-level proof).

### AC.D-np.6 — Pre-existing `pos-amend` behaviour is byte-identical

The full pre-extension `tools/pos-amend/tests/` suite passes against the post-extension tree without modification. `pos-amend validate`, `pos-amend apply [--dry-run]`, `pos-amend seal [--no-finalize|--scoped-sweep|--plan-doc]`, `pos-amend template list|render|validate` exit-code semantics, output formats, and side effects are byte-identical to pre-extension behaviour. The `new-plan` subcommand is purely additive — no existing subcommand sees behaviour change. No new third-party dependency on `tools/pos-amend/pyproject.toml`.

**Test shape:** run the full pre-existing `tools/pos-amend/tests/` suite at the post-extension tree; assert green. Verify `pos-amend apply --dry-run` against representative in-tree manifests exits 0. Verify `pos-amend template render plan/dev-discipline --vars-file <pre-extension-fixture>` produces output that contains §1–§14 (the skeleton's contract widening from 13 to 16 vars must still accept old vars-files via optional-default fallthrough — see §7 backward-compat note).

**Maps to:** the pos-amend backward-compat invariant; AC.PO.2 (no-regression preserves all pre-existing toolkit primitives).

### AC.D-np.7 — Skeleton's §14 scaffold preserved byte-identical for `pos-amend seal --plan-doc`

A plan-doc rendered from the post-extension skeleton can be the target of `pos-amend seal --plan-doc <abs-path>` exactly as a plan-doc rendered from the pre-extension skeleton was. The §14 heading text (`## 14. Method-decision record (builder, post-build)`) and the `### Commit SHAs` subsection heading are byte-identical between pre- and post-extension renderings.

**Test shape:** render the post-extension skeleton against a fixture vars-file; locate the §14 heading + `### Commit SHAs` subsection; assert byte-equality of those substrings against a pre-extension reference rendering. Optionally: drive `pos-amend seal --plan-doc <rendered-fixture>` against a synthetic manifest and assert the SHA-backfill subsection appears at the expected location.

**Maps to:** the seal-automation backward-compat invariant; AC.PO.2.

---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

| Behaviour (§1) | Criterion |
|---|---|
| 1. Scaffold vars-file at predictable path | AC.D-np.1 |
| 2. `--title` / `--ac-prefix` pre-fill | AC.D-np.2 |
| 3. `--render` produces plan-doc end-to-end | AC.D-np.3 |
| 4. Failure-mode halt + structured diagnostic | AC.D-np.4 |
| 5. Skeleton renders cleanly against fixture | AC.D-np.5 |
| 6. Pre-existing pos-amend behaviour byte-identical | AC.D-np.6 |
| 7. §14 scaffold preserved for `pos-amend seal --plan-doc` | AC.D-np.7 |

Seven declared behaviours; seven ACs cover them. No method-in-AC. Dev-discipline plan; no seal-diff ACs.

---

## 6. Hard constraints

1. **No `--amend`.** Corrective new commits only.
2. **Scope fence — `tools/pos-amend/` only.** Orchestration source under `tools/pos-amend/src/pos_amend/commands/new_plan.py` (or builder-chosen path within `src/pos_amend/`). Skeleton edits under `tools/pos-amend/templates/plan/dev-discipline.md`. Tests under `tools/pos-amend/tests/`. Fixtures under `tools/pos-amend/tests/fixtures/plan-skeleton/`. README at `tools/pos-amend/README.md`. CLI registration in `tools/pos-amend/src/pos_amend/cli.py`. Any source edit outside these paths is a halt.
3. **No edit to any sealed component.** No sealed-component-test invocation either; the `new-plan` orchestration is independent of the seal subcommand and does not touch any sealed component.
4. **Markdown skeleton + YAML vars-file only.** The skeleton is a markdown file with `{{var}}` holes + YAML frontmatter; the vars-file is a YAML mapping. No alternative formats. Constraint is design-load-bearing per §3 Lens 1: the engine is reused unchanged.
5. **No new pos-amend runtime deps.** The existing `PyYAML>=6` plus stdlib is sufficient (PyYAML for YAML read/write; argparse for CLI; pathlib for filesystem; the existing `template_engine.render` for `--render`). No new third-party dep.
6. **Backward-compat preserved unconditionally.** AC.D-np.6 enforces this. A failure is a halt.
7. **§14 scaffold byte-identical with the pre-extension `dev-discipline.md`.** AC.D-np.7 enforces this. The seal-automation extension's `--plan-doc` SHA-backfill must continue to find its target heading verbatim.
8. **CDC adherence.** Plan-before-code (this plan), background-agent default for the build, scope-only dispatch. No SEAL_COMMIT bump, no manifest, no seal commit. Conventional `feat(tools)` / `chore(tools)` commits.
9. **No retrofit of past plans.** Existing plan-docs stay as-is. The skeleton starts being used for NEW plans after it lands. Generalisation of older plans is busywork.
10. **No Claude-skills wiring in this plan's build commit.** `.claude/skills/new-plan/` and `.claude/skills/plan-dev-discipline/` are a small follow-up edit (matches dispatch-prompt-template-extension's D-3 follow-up shape), not bundled into the orchestration commit.
11. **One test file per AC.** Convention from AC35.x onward — `test_AC.D-np.N_<short_name>.py`.
12. **Slug validation strict.** Slugs match `^[a-z][a-z0-9-]*$` only. No subdirectories, no uppercase, no underscores. Method-level which exact regex; the constraint is "strict, opinionated, document-able."
13. **Vars-file path is `<repo>/docs/plans/<slug>.vars.yaml`.** Per D-1 ruling. Predictable. Co-located with plan-doc. Audit-friendly. Not under `.scratch/`.

---

## 7. Out of scope (explicit)

- **Sealed-component-specific plan-doc skeleton variant.** Per D-2 (recommendation: extend `dev-discipline.md` in place; absorb the dev/sealed split via `SECTION_9_HEADING` / `SECTION_9_BODY`). A separate `tools/pos-amend/templates/plan/sealed-component.md` template is NOT shipped at v1.
- **Memory-doc skeleton template + `pos-amend new-memory <slug>` orchestration.** Direct generalisation; future small follow-up; engine + orchestration shape are reusable.
- **Commit-message templates per category + `pos-amend new-commit <kind>` orchestration.** Same shape; future small follow-up.
- **Skills wiring.** `.claude/skills/<family>-<id>/` skill files that wrap `pos-amend new-plan` and `pos-amend template render plan/dev-discipline` are a follow-up doc-level edit. Engine + orchestration build is independent.
- **Tracker integration / Idea 17 composition.** Auto-fill `AC_PREFIX` from the persona-tracker's "what amendment is in flight" query is the sibling Idea 17 composition; sequenced after both this plan and the tracker stabilise.
- **Dispatch-template companion to `new-plan`.** The dispatch-template engine ALREADY shipped a `dispatch/sealed-component-build.md` template; the plan-doc skeleton is the second family. A `pos-amend new-dispatch <kind>` orchestration would be a parallel sibling but is out of scope here.
- **Auto-versioning of templates.** Per dispatch-prompt-template-extension's D-4 ruling: "manual edits, no versioning, just-update-the-file." Same applies here.
- **Auto-population of variables from external state** (tracker, manifests, git). Future composition; out of scope at v1.
- **Pre-render validation that the rendered plan-doc is structurally well-formed beyond `## 14.` heading presence.** Per dispatch-prompt-template-extension's D-6 ruling: validate template + vars at v1; output-schema validation is future work.
- **Retrofit of old plans into the skeleton's variable contract.** Old plans served their purpose; they remain on disk in their original shape. The skeleton applies to plans authored from this commit forward.
- **CLI auto-completion / shell-completion for `pos-amend new-plan`.** Out of scope.
- **Method-decision register prose for completed builds** — the skeleton ships a §14 SCAFFOLD (heading + subsections); the §14 prose itself remains the builder's authorship per the seal-automation plan's §7.

---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md (CLAUDE.md, ODD methodology, VALUE_PROPOSITION, STATE, FUTURE_IDEAS).
2. Read this plan + the research doc + companions (`dispatch-prompt-template-extension.md`, `pos-amend-seal-automation-extension.md`).
3. Read the existing `tools/pos-amend/templates/plan/dev-discipline.md` skeleton + `tools/pos-amend/src/pos_amend/template_engine.py` + `tools/pos-amend/src/pos_amend/commands/template.py` + `tools/pos-amend/src/pos_amend/cli.py` to ground the engine reuse.
4. Write builder-plan to `docs/plans/pos-amend-new-plan-orchestration.builder-plan.md` naming specific files + symbols expected to be touched, including the exact widening of the skeleton's `required:` and `optional:` lists.
5. Land the skeleton extension first: extend `tools/pos-amend/templates/plan/dev-discipline.md` from 13 → 16 required vars + 7 optional vars with default-stubbed bodies for `HARD_CONSTRAINTS` / `IMPLEMENTATION_ORDER` / `HALT_TRIGGERS`. Tests for AC.D-np.5 + AC.D-np.7 land alongside.
6. Land the `new_plan.py` command module + CLI subparser registration. Tests for AC.D-np.1, AC.D-np.2, AC.D-np.3, AC.D-np.4 land alongside.
7. Author the fixture vars-file + fixture expected output for AC.D-np.5.
8. Run the full `tools/pos-amend/tests/` suite. Verify no regression (AC.D-np.6).
9. Update `tools/pos-amend/README.md` to describe `pos-amend new-plan`, the widened skeleton, and how to add new plan-doc templates (e.g. memory-doc family).
10. Conventional commits land the changes (no `--amend`, no SEAL_COMMIT bump, no seal commit). Suggested split: one commit for skeleton extension + fixture, one commit for orchestration + tests + README.

---

## 9. Plan-author impact (after this lands)

Authoring a new plan-doc today:

```
[copy memory-system-live-client-and-stop-hook-write.md or similar]
[delete the old contents of every section]
[rewrite the 13 sections with content for the new plan]
[reach §14 — recall the scaffold; type it from memory]
[check the §14 scaffold matches what `pos-amend seal --plan-doc` expects]
```

…shrinks to:

```
pos-amend new-plan my-new-feature --title "My new feature" --ac-prefix AC.MNF.x --render
[edit docs/plans/my-new-feature.vars.yaml]
[re-render: pos-amend template render plan/dev-discipline --vars-file docs/plans/my-new-feature.vars.yaml --out docs/plans/my-new-feature.md --force]
```

Or, after the skills follow-up (out of scope per §7):

```
[invoke skill `new-plan` with slug, title, ac-prefix]
[edit the vars-file]
[invoke skill `render-plan` to re-render]
```

The CDC on `feedback_summarize_and_surface_decisions` (every plan has a §11 + §12 split with recommendations) and `feedback_subagent_odd_violation_halt` (§13 explicit halt-findings statement) become BAKED INTO the skeleton rather than separately remembered.

---

## 10. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `tools/pos-amend/`.** Halt.
2. **Backward-compat cannot be preserved.** AC.D-np.6 fails → halt.
3. **§14 scaffold cannot be preserved byte-identical.** AC.D-np.7 fails → halt; the seal-automation extension would break.
4. **The 13-section count turns out to be 8 or 25** (i.e., the corpus induction is fundamentally off — surface for refinement). Halt.
5. **A new third-party dependency becomes required.** Halt — design relies on stdlib + PyYAML.
6. **The skeleton's required-vars list grows beyond ~25** (i.e., the section count is right but each section has so many sub-vars that the scaffold becomes unwieldy). Halt — the assumption that 16 required + 7 optional captures the surface may be wrong; surface for owner to rule on whether the orchestration is still worth shipping.
7. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective-backed code path, silent exception that no AC backs). Halt; owner rules.
8. **Pos-amend's existing structure has to be refactored** (e.g. `cli.py` rewriting, manifest module restructure) to land the new subcommand. Halt — scope-creep beyond extension into refactor.
9. **The existing `tools/pos-amend/templates/plan/dev-discipline.md` skeleton's `optional:` defaulting cannot accept the widened vars list backward-compatibly** (i.e., a pre-extension caller passing only the original 13 vars now fails on a missing required var). Halt — the widening must be done via optional-with-default for the new vars, OR the new vars must be required and existing callers must update; the second path breaks AC.D-np.6 and is a halt by definition.
10. **Wall-time exceeds 90 minutes.** Halt with current state. Owner rules on split vs push-through.
11. **An ODD violation is observed in surrounding code or docs during build** (per `feedback_subagent_odd_violation_halt`). Halt; do NOT extend a violating surface.

---

## 11. Decisions remaining for the owner to rule on

The following items are owner-level decisions that shape the build dispatch brief. All carry recommendations from the research doc.

### D-1 — Vars-file path

**Options:**

- **D-1a. `<repo>/docs/plans/<slug>.vars.yaml`** — sibling of the plan-doc, gitted, audit-friendly (RECOMMENDED).
- **D-1b. `<repo>/.scratch/pos-amend/new-plan/<slug>.vars.yaml`** — ephemeral, gitignored.
- **D-1c. `<repo>/tools/pos-amend/scratch/<slug>.vars.yaml`** — under the tool's own tree.

**Recommendation: D-1a.** Vars-files commit alongside their plan-docs; the file becomes a small but authoritative record of "what the plan was rendered against," useful for diffing across plan revisions. The `.vars.yaml` extension makes filtering straightforward. D-1b loses audit value; D-1c mixes tool internals with per-plan state.

### D-2 — Skeleton placement

**Options:**

- **D-2a. EXTEND the existing `tools/pos-amend/templates/plan/dev-discipline.md` skeleton in place** (RECOMMENDED).
- **D-2b. ADD a new `tools/pos-amend/templates/plan/full-skeleton.md` alongside** (let plan authors choose).
- **D-2c. SPLIT into `dev-discipline.md` and `sealed-component.md` variants.**

**Recommendation: D-2a.** One skeleton; `SECTION_9_HEADING` / `SECTION_9_BODY` absorb the dev/sealed-component split (dev plans use "Impact / motivation" or "Plan-author impact"; sealed-component plans use "Bookkeeping surface" with a manifest YAML stub). D-2b doubles the maintenance surface for a split that one variable already handles. D-2c has merit if the dev/sealed split grows beyond §9 (e.g., manifest references in §10 of sealed-component plans), but the corpus survey shows the §9 split absorbs ~all the variation.

### D-3 — Pre-author the three Lens-1/2/3 subsection headings inside `LENS_ANALYSIS`'s default value

**Options:**

- **D-3a. Pre-author** the three subsection headings (`### Lens 1 — Claude leverage`, `### Lens 2 — Harness + primary-persona value`, `### Lens 3 — ODD authoring`) as scaffold inside the default value, leaving plan-author to fill the prose under each (RECOMMENDED).
- **D-3b. Leave `LENS_ANALYSIS` default empty** (plan author authors all three subsections from scratch every time).

**Recommendation: D-3a.** The three-lens shape is universal across the corpus; pre-authoring the subsection headings absorbs one decision per plan. Plan author fills prose; structure is given.

### D-4 — Pre-stub `HARD_CONSTRAINTS` / `IMPLEMENTATION_ORDER` / `HALT_TRIGGERS` with default content

**Options:**

- **D-4a. Pre-stub** all three with the recurring-content defaults (no `--amend`, scope fence, plan-before-code, no new dep, backward-compat — for §6; read corpus, write builder-plan, land core, run tests, conventional commits — for §8; cross-component scope expansion, backward-compat fail, ODD-violating shape, new dep, wall-time — for §10) as the variable's optional default, plan-author overrides per plan (RECOMMENDED).
- **D-4b. Leave all three default-empty.**
- **D-4c. Pre-stub only §6 (constraints), leave §8 + §10 empty.**

**Recommendation: D-4a.** ~50% of any plan's hard constraints, implementation-order steps, and halt triggers are universal across the corpus. Pre-stubbing absorbs the routine recall burden; plan-author edits/extends. D-4b loses the leverage; D-4c is arbitrary (the same logic applies to all three sections).

### D-5 — Vars-file format

**Options:**

- **D-5a. YAML mapping** (RECOMMENDED) — matches existing `--vars-file` for `pos-amend template render`.
- **D-5b. TOML mapping** — off-pattern.
- **D-5c. Markdown frontmatter** — fragile for multi-line values; off-pattern.

**Recommendation: D-5a.** Matches the dispatch-template family's vars-file format byte-for-byte; one format for both families. The existing engine's `_load_vars_file` helper handles it unchanged.

### D-6 — Slug validation regex

**Options:**

- **D-6a. `^[a-z][a-z0-9-]*$`** (RECOMMENDED) — lowercase, hyphens-only, leading-letter-required. Matches the existing plan-doc filename convention.
- **D-6b. Looser** — allow underscores, digits-leading.
- **D-6c. Tighter** — require minimum length, forbid trailing hyphen.

**Recommendation: D-6a.** Tight enough to reject pathological inputs (filenames starting with digits, paths containing `/`); loose enough that every existing plan-doc in the corpus would validate. D-6b allows mixed underscore/hyphen which would create disagreement with the corpus convention; D-6c adds friction without value.

### D-7 — Optional `--render` post-scaffold

**Options:**

- **D-7a. Accept `--render` as a flag** that triggers an immediate render after scaffold (RECOMMENDED).
- **D-7b. Always render** — no flag, render unconditionally.
- **D-7c. Never render** — `new-plan` only scaffolds vars-file; user runs `pos-amend template render` separately.

**Recommendation: D-7a.** Default behaviour (no flag) is "scaffold only" — user edits vars-file, then renders. `--render` is opt-in for the end-to-end path. D-7b forces a near-empty plan-doc on disk every scaffold, which is mostly noise. D-7c forces a second invocation for the common case where the user wants both.

---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-1 | Vars-file at `<repo>/docs/plans/<slug>.vars.yaml` (D-1a) | Predictable, gitted, audit-friendly |
| D-2 | Extend existing `dev-discipline.md` skeleton in place (D-2a) | One skeleton; `SECTION_9_*` absorbs dev/sealed split |
| D-3 | Pre-author Lens-1/2/3 subsection headings in `LENS_ANALYSIS` default (D-3a) | Three-lens shape is universal; absorbs one decision |
| D-4 | Pre-stub HARD_CONSTRAINTS / IMPLEMENTATION_ORDER / HALT_TRIGGERS defaults (D-4a) | ~50% of any plan's content in those sections is universal |
| D-5 | Vars-file format = YAML mapping (D-5a) | Matches existing `--vars-file` contract for `pos-amend template render` |
| D-6 | Slug regex = `^[a-z][a-z0-9-]*$` (D-6a) | Matches corpus filename convention; tight enough, loose enough |
| D-7 | `--render` opt-in flag for end-to-end render (D-7a) | Scaffold-only default; opt-in for combined; minimises noise |

Owner rules from this table without reading the plan body. Any "no, change to X" on a decision flips one row; the rest stay.

---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface any ODD violation observed in the work or surrounding code/docs.

**No ODD violations identified in surrounding code or docs during plan authoring.** The pos-amend codebase post-template-engine (post-`dbabd37`) is clean under §2.5. The two adjacent dev-discipline plans (`dispatch-prompt-template-extension.md`, `pos-amend-seal-automation-extension.md`) compose cleanly with this orchestration — neither's surface is touched. The existing `tools/pos-amend/templates/plan/dev-discipline.md` skeleton at HEAD is internally consistent with the engine contract; the extension widens its variables list without changing its contract shape (still YAML frontmatter + `{{var}}` placeholders).

**Asymmetric findings to surface to parent (per `feedback_asymmetric_problem_solving`):**

1. **`new-plan` is a small primitive that mechanises a recurring authoring shape; the same shape generalises to memory-doc and commit-message families.** Once `new-plan` ships and stabilises, `pos-amend new-memory <slug>` and `pos-amend new-commit <kind>` are mechanical follow-ups. The asymmetric observation: ~80% of the work is "scaffold a vars-file at a predictable path" — the orchestration code is small (~150 lines of Python including tests) and reusable across families.
2. **The vars-file IS a small audit artefact.** Committing vars-files alongside plan-docs makes plan-revision diffing happen at the vars-level, not the rendered-markdown level. This is a future-leverage point: vars-file diffs are smaller, semantically clearer, and easier to review than rendered-markdown diffs.
3. **Skills wrapping (out of scope per §7) is a force-multiplier follow-up.** A `.claude/skills/new-plan/` skill collapses "run `pos-amend new-plan <slug>`" to "invoke skill new-plan" from the persona's perspective. ~10 minutes of skill-file authoring per command. Same pattern as dispatch-prompt-template-extension's D-3c follow-up.
4. **Composition with Idea 17 (dispatch-template ↔ persona-tracker) becomes more concrete after this plan lands.** The vars-file scaffold is the same shape Idea 17 wants for tracker-driven dispatch authoring. Surface to FUTURE_IDEAS_DRAFT once `new-plan` stabilises empirically.

If an ODD violation is discovered during the *build* of this plan, the builder re-extends per ODD §4 and surfaces to the owner. Halt-trigger #11 enforces this.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.x method choices to the builder within the ACs' outcome bounds.

### D-build.1 — Skeleton extension shape (within locked D-2 bounds)

Extended `tools/pos-amend/templates/plan/dev-discipline.md` in place:
- `required:` grew from 13 to 16 entries: added `SECTION_9_HEADING` + `SECTION_9_BODY` (new — absorb dev/sealed §9 split per locked D-2); promoted `DECISIONS_DETAIL` from optional to required (research §3 inventory's "16 required" count).
- `optional:` grew from 4 to 6 entries: kept `COMPANIONS` + `ANCESTOR_RECORD`; dropped `IMPACT_BLOCK` (its content folded into `SECTION_9_BODY`); dropped `DECISIONS_DETAIL` (promoted); added `STATUS_LINE` (default empty), `RESEARCH_PATH` (default empty — orchestration fills), `WORKING_DIRECTORY` (default = standard repo path), `REFERENCES` (default = standard refs stub).
- §0 frontmatter lines: added `**Status:** {{STATUS_LINE}}`, `**Working directory:** {{WORKING_DIRECTORY}}`, `**Research:** {{RESEARCH_PATH}}`.
- §9: heading became `## 9. {{SECTION_9_HEADING}}`, body `{{SECTION_9_BODY}}`.
- §15 References: new section using optional `{{REFERENCES}}` with default-stub content.
- §14 scaffold: byte-identical preserved (locked AC.D-np.7).

### D-build.2 — Default-stubs for HARD_CONSTRAINTS / IMPLEMENTATION_ORDER / HALT_TRIGGERS / Lens scaffold (locked D-3 + D-4)

The engine's `optional:` defaulting only applies to optional vars; the three sections above + the LENS_ANALYSIS subsection-headings are REQUIRED vars in the skeleton. Pre-stubs live one level out — in the orchestration's vars-file scaffold (`new_plan.py:_vars_file_content`). Honours D-3 and D-4 spirit (recurring content pre-filled at the surface the plan author touches) while respecting the engine's contract (required = required).

### D-build.3 — `new_plan.py` module structure

Single `run(slug, *, title, ac_prefix, vars_out, plan_out, render, force, repo_root) -> int` entry point. `repo_root` is a testing hook; default resolution via `git rev-parse --show-toplevel`. Slug validation: locked `^[a-z][a-z0-9-]*$` regex (D-6). Default vars-out: `<repo>/docs/plans/<slug>.vars.yaml` (locked D-1). Default plan-out: `<repo>/docs/plans/<slug>.md`. `--render` delegates to `pos_amend.commands.template.run("render", ...)` — no engine duplication. Refuse-overwrite checks fire before any disk write (AC.D-np.4 no-partial-output invariant).

### D-build.4 — Tests (one file per AC convention)

Seven new test files (one per AC under `AC.D-np.1`–`AC.D-np.7`):
- `test_AC_D_np_1_scaffold_vars_file.py` (6 functions)
- `test_AC_D_np_2_pre_fill_title_and_ac_prefix.py` (5 functions)
- `test_AC_D_np_3_render_after_scaffold.py` (6 functions)
- `test_AC_D_np_4_failure_modes.py` (10 functions, 8 from parametrize)
- `test_AC_D_np_5_skeleton_renders_clean.py` (4 functions)
- `test_AC_D_np_6_backward_compat.py` (6 functions)
- `test_AC_D_np_7_section_14_preserved.py` (3 functions)
Plus 1 fixture-test data update in `test_template_engine.py`'s `test_AC_D_tpl_7_bundled_plan_renders_against_fixture_vars` (supplies the 3 newly-required vars; behaviour unchanged).

### D-build.5 — Fixture authoring (AC.D-np.5)

Fixtures at `tools/pos-amend/tests/fixtures/plan-skeleton/vars.yaml` + `expected.md`. Expected output authored by running `pos-amend template render plan/dev-discipline --vars-file <vars> --out <expected>` against the post-extension skeleton, then committed as test data. Test asserts byte-identity; divergence loudly surfaces structural changes to the skeleton.

### Test breakdown

Pre-amendment baseline: 106 tests green in `tools/pos-amend/tests/`.
Post-amendment: 151 tests green (106 pre-existing + 45 new across 7 new test files + 0 changed; one test-data update inside `test_template_engine.py` for the widened required-vars list).

### Backwards-compat verification

- Pre-existing 106 tests pass byte-identical post-commit (AC.D-np.6).
- `pyproject.toml` dependency list unchanged: still `["PyYAML>=6"]`. No new third-party dependency (test-asserted in `test_AC_D_np_6_backward_compat.py`).
- `pos-amend template list` enumerates both `dispatch/sealed-component-build` and `plan/dev-discipline` (test-asserted).
- `pos-amend --help` lists every pre-existing subcommand (`validate`, `apply`, `seal`, `template`) plus the new `new-plan` (test-asserted).
- The §14 scaffold is byte-identical to the pre-extension reference block (AC.D-np.7 test-asserted; the duplicate `### Commit SHAs` heading typo is preserved per the byte-identity constraint — see findings below).

### Commit SHAs

- Amendment commit: `76a5ea8` — `feat(tools): pos-amend new-plan orchestration + plan-doc skeleton extension (AC.D-np.1–7)`.
- Plan-SHA backfill commit (this commit): records the amendment SHA in §14. Manual append (dev-discipline plan; no manifest; `pos-amend seal --plan-doc` not invoked).

### Dependents cleared to dispatch

The skills-wiring follow-up named in §7 + §10 of the plan can now dispatch (a `.claude/skills/new-plan/` skill wrapping `pos-amend new-plan`). Memory-doc + commit-message generalisations (`pos-amend new-memory <slug>` + `pos-amend new-commit <kind>`) named in FUTURE_IDEAS_DRAFT are now mechanical follow-ups against this orchestration's shape.

### Halt-and-surface findings during build

1. **Pre-existing duplicate `### Commit SHAs` heading.** The pre-extension `tools/pos-amend/templates/plan/dev-discipline.md` had a duplicate `### Commit SHAs` subsection inside §14 (lines 125 and 129 of the pre-extension file). Per the AC.D-np.7 byte-identity constraint, the duplicate is preserved — correcting it would break the seal-automation extension's heading-locator. Surface this for owner ruling: a future small commit could deduplicate the heading once the seal-automation logic is verified to handle either shape. Not blocking; recorded here.

2. **No ODD violations identified in surrounding code or docs during build.** The plan's halt-trigger #11 was not triggered. Working tree carried L-build (amendment #50) stash residue per the dispatch note (modified files in `docs/plans/primary-persona-conversational-onboarding-*` + `docs/FUTURE_IDEAS_DRAFT.md`); these were NOT staged into this amendment commit (they belong to a separate operator action).

3. **Pre-amendment `apply --dry-run`** on amendment #50's manifest reports MISSING_ADMISSION (because my new files exist outside its scope) — exit 0, expected behaviour for a non-applicable manifest. This is NOT a halt for the dev-discipline plan; the dev-discipline plan has no manifest.

---

## 15. References

- Research doc: `docs/plans/research/pos-amend-new-plan-orchestration-research.md`
- Existing template engine: `tools/pos-amend/src/pos_amend/template_engine.py`, `tools/pos-amend/src/pos_amend/commands/template.py`
- Existing CLI registration surface: `tools/pos-amend/src/pos_amend/cli.py`
- Existing dev-discipline plan-doc skeleton (the one this plan extends): `tools/pos-amend/templates/plan/dev-discipline.md`
- Sibling plan (engine ancestor; landed `dbabd37`): `docs/plans/dispatch-prompt-template-extension.md`
- Sibling plan (seal-automation; the §14 SHA-backfill machinery): `docs/plans/pos-amend-seal-automation-extension.md`
- Source FUTURE_IDEAS_DRAFT entries: `docs/FUTURE_IDEAS_DRAFT.md` lines 25, 31, 57, 71–72, 80
- Idea 17 (composition stretch): `docs/FUTURE_IDEAS.md` "Idea 17 — Dispatch-template ↔ persona-tracker composition (stretch)"
- VALUE_PROPOSITION (prime objective AC.PO.1 + AC.PO.2): `docs/VALUE_PROPOSITION.md`
- ODD methodology: `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- STATE / FUTURE_IDEAS: `docs/STATE.md`, `docs/FUTURE_IDEAS.md`
- Feedback corpus referenced: `feedback_summarize_and_surface_decisions`, `feedback_subagent_odd_violation_halt`, `feedback_asymmetric_problem_solving`, `feedback_amendment_dispatch_speedups`, `feedback_no_amend_in_agent_dispatches`, `feedback_always_specify_wd_in_dispatches`, `feedback_plan_before_code`, `feedback_odd_no_non_objective_code`
