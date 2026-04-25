# dispatch-prompt template extension — plan

Dev-discipline work. **NOT** a sealed-component amendment. No `pos-amend` manifest, no `SEAL_COMMIT` bump, no seal commit. This plan extends `tools/pos-amend/` (or lands a sibling tool — D-2) with a markdown-driven template engine for high-repetition authored artefacts. Plan-before-code per the dev CDC; corrective new commits land the change.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Companions:** `docs/rebuild/plans/pos-amend-seal-automation-extension.md` (just landed; this plan composes on top), `docs/rebuild/plans/pos-amend-tracker-integration.md` (queued; orthogonal).
**Ancestor record:** `docs/rebuild/FUTURE_IDEAS_DRAFT.md` entries "Dispatch-prompt template family", "Plan-doc skeleton template", "Memory-doc skeleton template", "Commit-message templates per category".

---

## 1. Summary / TLDR

Every agent dispatch the primary persona authors today is 150–300 lines of markdown. ~70–80% of that markdown is boilerplate that repeats verbatim (or near-verbatim) across dispatch *categories* — sealed-component build, dev-discipline build, research+plan, plan-only, AC-tightening, doc-correction, audit, operational unblock, investigation lookup. The variable parts (objective, scope fence, halt triggers specific to this work, AC-prefix, working-directory) are the only content that ought to be authored per dispatch; everything else is rendered from a per-category template by string substitution.

The same shape recurs in three adjacent artefact families:

- **Plan docs** — the ~13-section skeleton (objective, AC list, behaviour-count, hard constraints, out-of-scope, halt triggers, named decisions, summary, halt-findings, §14 register) is propagated by precedent today (each new plan starts by reading the previous one).
- **Memory docs** — frontmatter (name/description/type/originSessionId) + Why + How-to-apply + Durable-record sections.
- **Commit messages** — per-category templates (`feat(<comp>): ... — amendment #N`, `chore(seals): ... — <comp> at <sha>`, `docs(plans): record amendment #N commit SHAs`).

This plan proposes a single markdown-driven template engine, packaged as a new `pos-amend template` subcommand family extending `tools/pos-amend/`, that renders any of these artefacts from a registered template-id plus a small variables dict. Templates live as plain markdown files under `tools/pos-amend/templates/<family>/<id>.md` with `{{variable}}` placeholders; rendering is `string.Template`-style substitution (Python stdlib, no new dependency). The engine is purely additive — every existing `pos-amend` invocation keeps its current shape and exit-code contract.

The proposed shape (recommendation, ruled in §11):

- **`pos-amend template list`** — list registered templates by family + id.
- **`pos-amend template render <family>/<id> --var KEY=VALUE...`** — render the named template to stdout with substituted variables.
- **`pos-amend template render <family>/<id> --vars-file <path.yaml>`** — render with a YAML-driven variables file (for templates with many variables; dispatch templates will use this).
- **`pos-amend template validate <family>/<id>`** — confirm the template parses and lists its required + optional variables (so authors can author a `--vars-file` against the template's contract).

The engine opens a Claude-leverage path: each template can be exposed as a `.claude/skills/<family>-<id>` skill that wraps the `pos-amend template render` invocation, so the primary persona can invoke a template by skill-name from inside Claude Code (D-3 ruling).

The dispatch-prompt impact: a sealed-component build dispatch that today renders ~250 lines of markdown by hand collapses to ~20–40 lines of variable definitions plus one CLI invocation (or skill call) to render the rest.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

§2.5 reads: *"Before scoping anything as a sealed-component amendment, name the specific spec objective (v1.0/v1.1/v1.2) the code will satisfy. If I can't name one, the work is dev-discipline (CLAUDE.md, docs, CDCs, tools/), not a sealed-component cycle."*

**No single spec objective names "pos-amend renders markdown templates."** The work is operational developer-tooling: it speeds primary-persona translation work (every dispatch authoring) by collapsing repeated boilerplate into a rendered template, and reduces dispatch-to-dispatch drift (e.g. forgetting `pos-amend apply` instruction in one dispatch). That is dev-discipline territory by every property §2.5 names:

- pos-amend lives under `tools/`.
- pos-amend has no spec objective; its load-bearing-ness is operational.
- The extension is internal to `tools/pos-amend/`; no sealed component's source changes.

Same §2.5 framing as `pos-amend-seal-automation-extension.md`, `pos-amend-tracker-integration.md`, and `pos-amend-install-instructions-fix.md`.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

Two surfaces, both load-bearing for this design:

1. **Claude Code skills.** The primary persona invokes skills by name; a skill is a thin wrapper around any executable. Each registered template can be exposed as a skill (`.claude/skills/dispatch-sealed-component-build/`, `.claude/skills/plan-dev-discipline/`, etc.) whose body invokes `pos-amend template render <family>/<id> --vars-file <path>`. The persona then "calls the skill" to render a dispatch prompt rather than authoring it from scratch. This is the same shape `feedback_amendment_dispatch_speedups` recommends for pos-amend itself — the persona names a primitive instead of recalling a procedure. (D-3 records the skill-wrapping decision.)
2. **Markdown is the native format Claude Code reads and writes.** The decision to template in markdown (not Python, not Jinja-with-control-flow) is forced by the constraint: the artefacts being templated ARE markdown that Claude reads. A template engine that requires Python authorship would defeat the purpose; a template engine whose templates are themselves markdown files with `{{var}}` holes preserves the medium. This is also the shape Claude Code's own slash-command surface uses for argument substitution.

The CLI shape (`pos-amend template render ...`) is invocable from any Claude tool surface (Bash, skills, hooks, slash-commands) without further integration.

The engine does NOT lean on hooks, MCP, or background-tasks. Those remain available for future composition (e.g. a SessionStart hook that renders a dispatch from current state) but are out of scope here — the CLI shape is sufficient.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

Yes — the persona's translation burden when authoring a dispatch shrinks from "write 250 lines of markdown rendering this category's boilerplate" to "fill 20–40 lines of variable definitions and call the template." The user's translation burden was never load-bearing here (the user said "build amendment N"; the persona translated to a 250-line dispatch); but the persona's own translation burden compounds — one less place per dispatch where the persona has to recall the shape, one less risk of dispatch-to-dispatch drift (e.g. a CDC update that doesn't propagate to every category's prompt because the propagation is manual).

**AC-trace to AC.PO.1 (every AC traces explicitly):**

- **AC.D-tpl.1 → AC.PO.1.** A dispatch authored from a registered template has its boilerplate rendered deterministically. Translation burden absorbed in the template-rendering layer.
- **AC.D-tpl.2 → AC.PO.1.** Variable-substitution is `string.Template`-style with explicit required/optional declaration; the persona authors a `--vars-file` against a known contract instead of recalling the template's shape from memory. Translation burden absorbed in the variables-contract layer.
- **AC.D-tpl.3 → AC.PO.1.** Templates render to stdout (or to a file via `--out`); the persona pipes or attaches the output without intermediate copy-paste, eliminating one transcription step.
- **AC.D-tpl.4 → AC.PO.1.** A `validate` subcommand reports a template's required + optional variables; the persona discovers a template's contract by tool-introspection rather than reading the template's source. Translation burden absorbed at the discovery layer.
- **AC.D-tpl.5 → AC.PO.1.** Halt-and-surface — when a required variable is missing or a template-id is unknown, the engine emits a structured diagnostic naming the missing variable + the template's contract; no silent rendering with `{{undefined}}` strings escaping into the rendered prompt.
- **AC.D-tpl.6 → AC.PO.1.** Backward-compat — every pre-existing pos-amend invocation is byte-identical; introduction of `pos-amend template` does not regress any pre-extension test.
- **AC.D-tpl.7 → AC.PO.1.** Initial template registry (one dispatch family, one plan-doc family) ships with the engine; subsequent families (memory-doc, commit-message) land via small follow-up edits without engine changes. Translation burden absorbed at ship-day for the highest-frequency artefacts.

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — `pos-amend template` becomes a load-bearing automation primitive the primary persona can name by skill-id. Future tooling composes:

- A SessionStart hook that pre-renders a dispatch shell when the persona starts authoring a new amendment.
- A slash-command (`/dispatch <category>`) that calls the template engine and inserts the rendered prompt into the current context.
- A `pos-amend new-amendment <slug>` orchestration that combines template-rendering of the plan doc + the manifest YAML + the initial dispatch prompt into a single invocation.

**AC-trace to AC.PO.2 (every AC traces explicitly):**

- **AC.D-tpl.1 + AC.D-tpl.2 + AC.D-tpl.3 → AC.PO.2.** Rendering primitive, variables-contract primitive, output primitive — all toolkit-shaped.
- **AC.D-tpl.4 → AC.PO.2.** Template-introspection primitive (any future tool needing to discover a template's contract — e.g. a vars-file scaffolder — composes against `template validate`).
- **AC.D-tpl.5 → AC.PO.2.** Failure-mode primitive (composable: a future hook can rely on the structured-diagnostic exit code).
- **AC.D-tpl.6 → AC.PO.2.** Opt-in (templating is invoked only when `template` subcommand is named) — explicit escape-shape preserves all pre-extension callers.
- **AC.D-tpl.7 → AC.PO.2.** The initial template registry IS the toolkit primitive — every shipped template adds to the persona's reach.

### Lens 3 — ODD authoring

The plan authors seven outcome-shaped acceptance criteria (§4) under §2.5 framing. Each AC names what must be true; method (the exact Python module layout, whether the engine is a single file or a sub-package, the precise glob shape for template discovery, the precise YAML schema for `--vars-file`, the exact substitution-syntax preserved-against-collision rules — `string.Template` allows `${var}` and `$var` shapes, and the builder picks one) is the builder's call.

ODD §2.5 reverse-direction check: every new code path traces back to AC.D-tpl.1–AC.D-tpl.7. No platform branches, no "useful later" knobs. The initial template registry contents (which families ship at v1, which don't) are scoped explicitly in §7 (out-of-scope).

---

## 4. Acceptance criteria (AC.D-tpl.x — dev-discipline plan, prefix distinguishes from sealed-amendment ACs and from sibling pos-amend dev-discipline plans)

Each AC maps to at least one test function in `tools/pos-amend/tests/`.

### AC.D-tpl.1 — `pos-amend template render <family>/<id>` deterministically renders a registered template

Invoking `pos-amend template render <family>/<id> --var KEY=VALUE...` (or `--vars-file <path>`) reads the template at `tools/pos-amend/templates/<family>/<id>.md`, substitutes every `{{KEY}}` placeholder in the template body with the corresponding variable value, and emits the rendered markdown to stdout. The substitution is deterministic — same template + same variables produces byte-identical output every invocation. Template files are plain UTF-8 markdown; `{{variable}}` is the substitution syntax; `\{{not-a-var\}}` (or whatever escape the builder picks) preserves a literal `{{`.

**Test shape:** in a tmpfs fixture with a registered template `dispatch/sealed-component-build.md` containing two `{{var}}` slots, invoke `pos-amend template render dispatch/sealed-component-build --var COMP=alpha --var AC_PREFIX=AC.A.x`; assert stdout matches a fixture-defined expected rendering byte-for-byte.

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.D-tpl.2 — Each template declares its required + optional variables in a frontmatter block; rendering enforces the contract

A template file at `tools/pos-amend/templates/<family>/<id>.md` carries a YAML frontmatter block at the top declaring `required:` (list of variable names that must be provided at render time) and `optional:` (list of variable names with default values). An attempt to render with a missing required variable halts with a non-zero exit and a structured diagnostic naming the template-id + the missing variable. Optional variables not provided at render time are substituted with their declared default. Variables provided at render time but not declared in the template's frontmatter contract halt with a non-zero exit and a diagnostic naming the unrecognised variable (so typos surface).

**Test shape:** fixture template with `required: [COMP]` and `optional: [AC_PREFIX: AC.X.x]`; invoke render without `--var COMP=...`; assert non-zero exit + diagnostic. Invoke render with COMP only; assert AC_PREFIX defaults to `AC.X.x`. Invoke with an unknown variable; assert non-zero exit + typo diagnostic.

**Maps to:** AC.PO.1 + AC.PO.2 (variables-contract primitive, halt-and-surface).

### AC.D-tpl.3 — Templates render via stdout or `--out <path>`, not via in-place edit

The default render mode is to stdout (the caller pipes or redirects). An optional `--out <path>` flag writes the rendered output to the named path (creating parent directories as needed; refusing to overwrite an existing file unless `--force` is passed). The engine never edits any template file in place; templates are read-only from the engine's perspective.

**Test shape:** invoke `pos-amend template render <id>` without `--out`; assert stdout carries the rendering, no file written. Invoke with `--out <new-path>`; assert file written. Invoke with `--out <existing-path>`; assert non-zero exit + refuse-overwrite diagnostic. Invoke with `--out <existing-path> --force`; assert overwrite succeeds.

**Maps to:** AC.PO.1 + AC.PO.2 (output primitive; the persona picks where the rendered artefact lands).

### AC.D-tpl.4 — `pos-amend template list` and `pos-amend template validate <id>` introspect the registry

`pos-amend template list` enumerates every template under `tools/pos-amend/templates/`, grouped by family, with each entry carrying the template-id and a one-line description (sourced from a `description:` frontmatter field). Output is human-readable to stdout; exit is 0.

`pos-amend template validate <family>/<id>` confirms the named template parses (frontmatter is well-formed YAML, body contains no unmatched `{{` placeholders), reports the template's required + optional variables, and exits 0 on success. On parse failure, exits non-zero with a structured diagnostic.

**Test shape:** fixture registry with three templates across two families; `list` output names all three with families. `validate` against a well-formed template reports its variables list; against a malformed one, exits non-zero.

**Maps to:** AC.PO.1 + AC.PO.2 (introspection primitive).

### AC.D-tpl.5 — Failure modes halt with structured diagnostics; no silent rendering

When `pos-amend template render` encounters one of:

- (a) an unknown template-id (no file at `tools/pos-amend/templates/<family>/<id>.md`),
- (b) a missing required variable,
- (c) an unrecognised variable in the caller's vars,
- (d) a malformed template (frontmatter parse error, body with unmatched delimiters),
- (e) `--out` with an existing file and no `--force`,

it (1) halts before any output is emitted to the destination (stdout for default; the file for `--out`), (2) emits a structured diagnostic to stderr naming the failure class + the specific identifier involved, (3) exits non-zero in the existing 1/2/3 taxonomy `pos-amend` already uses (no new exit code introduced — class (a)–(d) map to one of the existing meanings; the builder picks the mapping in `cli.py`).

**Test shape:** fixture-inject each failure class; assert non-zero exit; assert diagnostic on stderr; assert no partial output to stdout or `--out` target.

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.D-tpl.6 — Pre-existing `pos-amend` behaviour is byte-identical

The full pre-extension `tools/pos-amend/tests/` suite passes against the post-extension tree without modification. `pos-amend validate`, `pos-amend apply [--dry-run]`, `pos-amend seal [--no-finalize|--scoped-sweep|--plan-doc]` exit-code semantics, output formats, and side effects are byte-identical to pre-extension behaviour. The `template` subcommand family is purely additive — no existing subcommand sees behaviour change. No new third-party dependency on `tools/pos-amend/pyproject.toml`.

**Test shape:** run the full pre-existing `tools/pos-amend/tests/` suite at the post-extension tree; assert green. Verify `pos-amend apply --dry-run` against representative in-tree manifests exits 0.

**Maps to:** the pos-amend backward-compat invariant; AC.PO.2 (no-regression preserves all pre-existing toolkit primitives).

### AC.D-tpl.7 — Initial template registry ships with two families: `dispatch/` and `plan/`

The post-extension tree contains at least two registered templates:

- `tools/pos-amend/templates/dispatch/sealed-component-build.md` — the boilerplate-heavy sealed-component-build dispatch (objective, scope-fence, halt-triggers, ODD-check, output-conventions, post-amendment-commit pos-amend invocation, etc.) with `{{COMPONENT}}`, `{{AMENDMENT_NUMBER}}`, `{{OBJECTIVE}}`, `{{SCOPE_FENCE}}`, `{{AC_PREFIX}}` and similar variables; required/optional declared in the frontmatter.
- `tools/pos-amend/templates/plan/dev-discipline.md` — the ~13-section dev-discipline plan-doc skeleton (objective, AC list, behaviour-count, hard constraints, out-of-scope, halt triggers, named decisions, summary, halt-findings, §14 register placeholder) with `{{TITLE}}`, `{{TLDR}}`, `{{AC_PREFIX}}` and similar variables.

Each shipped template renders against a fixture vars-file to produce byte-identical fixture output (the test fixture proves the template is rendering-clean, not a placeholder). The other artefact families (memory-doc skeleton, commit-message templates per category, sealed-component plan-doc skeleton) are explicitly NOT shipped at v1 — they land via small follow-up edits without engine changes per §7.

**Test shape:** fixture vars-file for each shipped template; render produces fixture-expected output byte-for-byte. `pos-amend template list` enumerates both families' templates with descriptions.

**Maps to:** AC.PO.1 + AC.PO.2 (initial registry IS the toolkit primitive at ship; high-frequency artefacts absorb translation burden on day one).

---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

| Behaviour (§1) | Criterion/criteria |
|---|---|
| 1. Render a template with variable substitution | AC.D-tpl.1 |
| 2. Required + optional variables enforced via frontmatter | AC.D-tpl.2 |
| 3. Stdout default; `--out <path>` opt-in (with overwrite refusal) | AC.D-tpl.3 |
| 4. Registry introspection (`list`, `validate`) | AC.D-tpl.4 |
| 5. Failure-mode halt + structured diagnostic | AC.D-tpl.5 |
| 6. Pre-existing pos-amend behaviour byte-identical | AC.D-tpl.6 |
| 7. Initial registry: dispatch + plan families ship | AC.D-tpl.7 |

Seven declared behaviours; seven ACs cover them. No method-in-AC. Dev-discipline plan; no seal-diff ACs.

---

## 6. Hard constraints

1. **No `--amend`.** Corrective new commits only.
2. **Scope fence — `tools/pos-amend/` only.** Engine source under `tools/pos-amend/src/pos_amend/`. Templates under `tools/pos-amend/templates/`. Tests under `tools/pos-amend/tests/`. README at `tools/pos-amend/README.md`. Any source edit outside these paths is a halt.
3. **No edit to any sealed component.** No sealed-component-test invocation either; the template engine is independent of the seal subcommand and does not touch any sealed component.
4. **Markdown templates only.** Templates are markdown files with `{{var}}` holes, optionally with a YAML frontmatter for the variables contract. Templates MAY NOT be Python files, Jinja files with control-flow, or any other format. The constraint is design-load-bearing per the dispatch brief and §3 Lens 1: the artefacts being templated ARE markdown the persona reads and Claude renders.
5. **No new pos-amend runtime deps.** The existing `PyYAML>=6` plus stdlib is sufficient (PyYAML for frontmatter parsing; `string.Template` or a 30-line custom regex substitution for `{{var}}` — the builder picks; argparse for CLI; pathlib for filesystem). No new third-party dep.
6. **Backward-compat preserved unconditionally.** AC.D-tpl.6 enforces this. A failure is a halt.
7. **Authority bound.** Builder may refine: substitution-engine choice (`string.Template` adapted vs. custom regex; the constraint is `{{var}}` syntax, not the regex implementation); template-discovery glob shape; vars-file YAML schema; failure-class → exit-code mapping within the existing taxonomy; module/file layout under `src/pos_amend/`; whether `template` is a single subcommand with `list/render/validate` modes or three flat subcommands. Builder may NOT relax the markdown-only constraint, the no-new-dep constraint, or the backward-compat invariant.
8. **CDC adherence.** Plan-before-code, background-agent default (single long-running build → background), scope-only dispatch. No SEAL_COMMIT bump, no manifest, no seal commit. Conventional `feat(tools)` / `chore(tools)` commits.
9. **No retrofit of past dispatches.** Existing dispatches stay as-is. The engine starts being used for NEW dispatches after it lands. (D-6 ruling — confirmed in §11.)
10. **No Claude-skills wiring in this plan's build commit.** The skill files (`.claude/skills/<family>-<id>/`) wrapping the engine are a small follow-up edit per §11 D-3, not bundled into the engine build commit.

---

## 7. Out of scope (explicit)

- **Memory-doc template family.** Future small follow-up; no engine changes needed, just a new `memory/` subdirectory under `tools/pos-amend/templates/`.
- **Commit-message template family.** Future small follow-up; same shape as above.
- **Sealed-component plan-doc skeleton template** (separate from `dev-discipline.md`). Future small follow-up — sealed-component plans have additional sections (manifest references, seal-diff invariants) that warrant a separate template-id.
- **Skills wiring.** `.claude/skills/<family>-<id>/` skill files that wrap `pos-amend template render` are a follow-up doc-level edit per D-3. Engine build is independent.
- **Render-time validation of the OUTPUT.** Per D-7, validation that the rendered markdown carries required sections (e.g. plan doc has §14 heading, dispatch has halt-triggers section) is future work. The v1 engine validates the TEMPLATE (frontmatter, placeholder syntax) and the VARIABLES (required/optional contract), not the rendered output's structural shape.
- **Hook/MCP integration.** The CLI shape is sufficient. SessionStart hooks, slash-commands, and other Claude harness wiring compose against the CLI surface but are not required for v1.
- **Auto-versioning of templates.** Templates evolve; D-4 ruling is "manual edits, no semver, just update the file." Versioning machinery is out of scope.
- **Auto-population of variables from external state.** The vars-file is the contract; the persona authors it. A future hook can pre-populate (e.g. read the current amendment's manifest to fill `{{COMPONENT}}`), but that's downstream.
- **Retrofitting past dispatches.** Per D-6, the engine starts being used for new dispatches; old dispatches stay as-is.
- **Method-decision register for completed builds.** The dev-discipline plan template ships a §14 PLACEHOLDER (heading + format); the §14 prose itself remains the builder's authorship per the seal-automation plan's §7.

---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md.
2. Read this plan + `tools/pos-amend/README.md` + `tools/pos-amend/src/pos_amend/cli.py` (existing CLI surface — the new `template` subcommand registers here).
3. Write builder-plan to `docs/rebuild/plans/dispatch-prompt-template-extension.builder-plan.md` naming specific files + symbols expected to be touched.
4. Land the engine module first (template parsing + variable substitution + failure-mode emission). Tests for AC.D-tpl.1, AC.D-tpl.2, AC.D-tpl.5 land alongside.
5. Land the CLI subcommand (`pos-amend template render|list|validate`). Tests for AC.D-tpl.3, AC.D-tpl.4 land alongside.
6. Author the two initial templates: `dispatch/sealed-component-build.md` and `plan/dev-discipline.md`. The dispatch template is sourced from a recent representative dispatch (the persona has examples in transcripts; the builder reads the seal-automation extension's §9 boilerplate-shrinkage block + the dev-discipline-plan precedents to extract the boilerplate). The plan-doc template is sourced from the seal-automation plan's structure (this plan and its precedents share the same skeleton).
7. Author fixture vars-files + fixture expected outputs for each template (AC.D-tpl.7 test).
8. Run the full `tools/pos-amend/tests/` suite. Verify no regression (AC.D-tpl.6).
9. Update `tools/pos-amend/README.md` to describe the `template` subcommand family + the two initial templates + how to add new templates.
10. Conventional commits land the changes (no `--amend`, no SEAL_COMMIT bump, no seal commit).

---

## 9. Dispatch-prompt impact (after this lands)

Authoring a sealed-component-build dispatch today:

```
[~250 lines of markdown the persona writes by hand: WD, session-start corpus,
 owner-ruled scope, decisions you must surface, constraints, halt triggers,
 acceptance shape, deliverable, ODD-check, output conventions, etc.]
```

…shrinks to authoring a vars-file (~25–40 lines) plus one CLI/skill invocation:

```yaml
# Vars-file the persona authors; the boilerplate is rendered.
COMPONENT: alpha
AMENDMENT_NUMBER: 41
AC_PREFIX: AC.A.x
OBJECTIVE: |
  <one-paragraph objective specific to this dispatch>
SCOPE_FENCE: |
  <one-block scope fence specific to this dispatch>
HALT_TRIGGERS_EXTRA: |
  <the 1-3 dispatch-specific halt triggers; the standard ones are baked in>
```

Then either:

```
.venv/bin/pos-amend template render dispatch/sealed-component-build \
  --vars-file <path-to-vars.yaml>
```

…or, after the D-3 follow-up, a Claude skill `dispatch-sealed-component-build` that wraps the same call.

The CDC on `feedback_amendment_dispatch_speedups` continues to hold — the speedups become BAKED INTO the templates rather than separately remembered.

---

## 10. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `tools/pos-amend/`.** Halt.
2. **Backward-compat cannot be preserved.** AC.D-tpl.6 fails → halt.
3. **The markdown-only constraint cannot be honoured** (e.g. a critical template needs control-flow that pure substitution can't express). Halt — that's a re-scope; control-flow is method-in-template that the constraint forbids.
4. **A new third-party dependency becomes required.** Halt — design relies on stdlib + PyYAML.
5. **The initial template authoring (AC.D-tpl.7) reveals the boilerplate ISN'T as repetitive as estimated** (e.g. the dispatch template needs >15 variables and most of the body is variable). Halt — the assumption that boilerplate is ~70–80% may be wrong; surface for owner to rule on whether the engine is still worth shipping.
6. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective-backed code path, silent exception that no AC backs). Halt; owner rules.
7. **Pos-amend's existing structure has to be refactored** (e.g. `cli.py` rewriting, manifest module restructure) to land the new subcommand. Halt — scope-creep beyond extension into refactor.
8. **Wall-time exceeds 90 minutes.** Halt with current state. Owner rules on split vs push-through.

---

## 11. Decisions remaining for the owner to rule on

The following items are owner-level decisions that shape the build dispatch brief. All carry recommendations.

### D-1 — Scope of templating engine (v1 ship)

**Options:**

- **D-1a. Dispatch-prompts only at v1.** Ship the engine + the dispatch family only. Plan-doc / memory-doc / commit-message templates land later as separate small efforts.
- **D-1b. Dispatch + plan-doc at v1 (RECOMMENDED).** Ship the engine + two families' initial templates. Memory-doc / commit-message templates land later as small follow-ups (just markdown file additions, no engine work).
- **D-1c. All four families at v1.** Dispatch + plan-doc + memory-doc + commit-message all ship at v1.

**Recommendation: D-1b.** The engine's load-bearing work is the engine itself + at least one shipping family that exercises every AC — single-family ships would technically prove the engine but leave the asymmetric "broader-applicability" finding stranded. Two families ship together (dispatch is highest-frequency, plan-doc is second-highest, both are >100-line artefacts). Memory-docs (~30 lines each, lower frequency) and commit-messages (3–5 lines, deterministic enough to not need a full template engine — could ship as a one-pager helper) are lower-leverage; deferring keeps v1 ship-scope tight. D-1c risks delay-by-inflation; D-1a leaves engine generality un-exercised at ship.

### D-2 — Where the engine lives

**Options:**

- **D-2a. Extend `tools/pos-amend/`** with a `template` subcommand (RECOMMENDED).
- **D-2b. New `tools/template/` subtree** as a sibling tool (separate package, separate CLI).
- **D-2c. Live as a `.claude/skills/` skill** with shell-only logic (no Python tool).
- **D-2d. Live as plain markdown files with the dispatcher running `Read`-and-substitute inline** (no tool at all).

**Recommendation: D-2a.** The dispatch brief explicitly leans this direction; the asymmetric reasoning holds: pos-amend is already the dev-discipline tool the persona reaches for, has a CLI shape the persona is fluent in, has a packaging story (`pyproject.toml`, `pip install -e .` already in operator hands), and has tests + CI muscle-memory. Adding a `template` subcommand reuses all of that. D-2b doubles the package overhead for what is the same class of work (dev-discipline tooling). D-2c is too thin — it can't enforce frontmatter contracts or variable validation without re-implementing those in shell. D-2d is what we have today (precedent-by-copy); the failure mode the plan exists to fix.

### D-3 — Composability with `pos-amend` (and Claude skills)

**Options:**

- **D-3a. Engine is independent of the rest of pos-amend** — `template` doesn't read manifests or invoke other subcommands; vars-files are authored by the persona (RECOMMENDED).
- **D-3b. Engine pulls variables from manifests** — when a `--manifest <path>` flag is set, dispatch-template variables auto-populate from the manifest (`{{COMPONENT}}`, `{{AMENDMENT_NUMBER}}`).
- **D-3c. Engine is wrapped by Claude skills** — each registered template ships a corresponding `.claude/skills/<family>-<id>/` skill file that wraps the render invocation; persona invokes skills directly.

**Recommendation: D-3a for v1; D-3c as a SMALL FOLLOW-UP (separate commit after the engine lands).** Independence (D-3a) keeps v1 simple — the engine reads templates and substitutes vars, full stop. D-3c is cheap to add post-v1 (each skill is a 5-line wrapper file) and unlocks Claude-leverage at low cost; it's already named as out-of-scope in §6 constraint #10. D-3b is a future feature: useful, but ties templating to pos-amend internals and loses generality (a non-amendment dispatch can't compose). Defer to a future small effort once the engine has settled.

### D-4 — Maintenance shape

**Options:**

- **D-4a. Manual edits, no versioning, just-update-the-file** (RECOMMENDED).
- **D-4b. Semver on each template, with a `--template-version` flag for pinning.**
- **D-4c. Shared template-version on the registry as a whole.**

**Recommendation: D-4a.** Templates evolve as the dispatch/plan shape evolves; pinning would freeze the very thing this engine exists to keep current. The repo's git history is the version trail; pos-amend's tests verify the current rendering against current fixtures (so a breaking template edit fails tests at refactor time, not at use time). Versioning machinery is gold-plating for an artefact set with maybe 4–6 templates total. D-4b/c are the gold-plated path; reject.

### D-5 — Adoption path

**Options:**

- **D-5a. New dispatches use the engine immediately; old dispatches don't get retrofitted** (RECOMMENDED — confirmed by dispatch brief).
- **D-5b. Retrofit recent dispatches as a one-time backfill effort.**
- **D-5c. Wait for engine to bake in before any persona uses it (ship + park for one cycle, then adopt).**

**Recommendation: D-5a.** Confirmed by the dispatch brief. D-5b is busywork — old dispatches served their purpose; their templating provides no value. D-5c is the kind of unjustified ceremony §3 Lens 2's primary-persona test argues against — the engine works or doesn't; either way adoption matches that fact.

### D-6 — Validation of rendered output

**Options:**

- **D-6a. Engine validates only the TEMPLATE (parse, vars-contract) at v1; rendered-output validation is future work** (RECOMMENDED).
- **D-6b. Engine validates rendered output against a per-template structural schema** (e.g. dispatch templates must produce output containing `## Halt triggers`, plan templates must produce output containing `## 14.`).
- **D-6c. No validation at all; trust the renderer.**

**Recommendation: D-6a.** Schema-validation of the rendered output is genuinely useful but adds substantial scope: each template needs a schema declaration, the validator needs a schema-language (YAML? regex? markdown-headings-list?), and the failure modes need their own diagnostics. v1 ships with template+vars validation, which catches the load-bearing failure modes (missing variable, malformed template). Output-schema validation is a small future plan when usage shows where false-renderings actually escape. D-6c is the engineering-debt path; reject.

### D-7 — Plan-doc skeleton template inclusion (broader-applicability question)

**Options:**

- **D-7a. Ship the plan-doc skeleton at v1 alongside the dispatch template** (i.e. AC.D-tpl.7 names two families; engine ships proven against two artefact-shapes) — RECOMMENDED.
- **D-7b. Ship dispatch-only at v1; plan-doc skeleton ships in a follow-up effort.**
- **D-7c. Don't ship a plan-doc skeleton at all — plan-by-precedent has been working.**

**Recommendation: D-7a.** Same shape as D-1b's reasoning. The engine's generality is exercised by shipping against two artefact-shapes; plan-doc is the second-highest-frequency authored artefact (every amendment plus every dev-discipline effort produces one). The plan-doc skeleton authoring is bounded — the seal-automation plan and this plan share the same 13-section shape; extracting a template is a 30-minute reading effort. D-7b lengthens the path-to-adoption by one cycle for no engine-design reason. D-7c is the precedent-by-copy failure mode this plan exists to fix.

---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-1 | v1 ships dispatch + plan-doc families (D-1b) | Two families exercises engine generality; defers low-frequency families |
| D-2 | Extend `tools/pos-amend/` with `template` subcommand (D-2a) | Reuses existing tool muscle-memory + packaging |
| D-3 | Engine independent of rest of pos-amend at v1; skills wiring as small follow-up (D-3a + D-3c later) | Simplest engine; Claude-leverage at low cost post-v1 |
| D-4 | Manual edits, no versioning (D-4a) | Templates ARE the version; git history is the trail |
| D-5 | New dispatches use engine; old dispatches stay (D-5a) | Confirmed by dispatch brief; no retrofit busywork |
| D-6 | Validate template + vars at v1; rendered-output validation is future work (D-6a) | Catches load-bearing failures; defers schema-language scope |
| D-7 | Ship plan-doc skeleton at v1 alongside dispatch (D-7a) | Two-family ship exercises engine generality; plan-doc is high-frequency |

Owner rules from this table without reading the plan body. Any "no, change to X" on a decision flips one row; the rest stay.

---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface any ODD violation observed in the work or surrounding code/docs.

**No ODD violations identified in surrounding code or docs during plan authoring.** The pos-amend codebase post-seal-automation is clean under §2.5 (the seal-automation plan's §13 confirmed this). The two adjacent dev-discipline plans (`pos-amend-tracker-integration.md`, `pos-amend-seal-automation-extension.md`) compose cleanly with this engine — the engine doesn't touch their surface.

**Asymmetric findings to surface to parent (per `feedback_asymmetric_problem_solving`):**

1. **The dispatch-template engine is itself a meta-asymmetric finding:** the broader-applicability scan revealed the same `boilerplate + variable substitution` shape across four artefact families (dispatch, plan, memory, commit). Shipping one engine that handles all four (eventually) is more leverage than shipping four bespoke tools.
2. **Skills-wrapping (D-3c) is a force-multiplier follow-up:** wrapping each template as a Claude skill collapses "render a template via CLI" to "invoke a skill by name." Cost: ~10 minutes of YAML authoring per template. Leverage: every dispatch authoring eliminates one CLI invocation step.
3. **Pre-render hook composition (deferred per §7) is the next asymmetric step after v1:** a SessionStart hook that pre-fills a vars-file from the current amendment's manifest collapses dispatch authoring further (the persona only authors the `OBJECTIVE` block; everything else auto-populates). Worth surfacing as a future-ideas-draft entry once the v1 engine is in use.
4. **Memory-doc family templates (D-1b deferred) carry a smaller but real asymmetric win:** every memory file currently follows a near-identical shape; a template + skill would mechanise the write-feedback-now workflow Luke uses across sessions. Surface to FUTURE_IDEAS_DRAFT once v1 lands.

If an ODD violation is discovered during the *build* of this plan, the builder re-extends per ODD §4 and surfaces to the owner. Halt-trigger #6 enforces this.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.x method choices to the builder within the
ACs' outcome bounds. This section is populated post-build.

### D-build.1 — Engine module layout

Single module `tools/pos-amend/src/pos_amend/template_engine.py`
(parsing + substitution + diagnostics + registry discovery) plus a
single command module `tools/pos-amend/src/pos_amend/commands/template.py`
(CLI handlers + diagnostic formatting). Constraint #2's scope-fence
held; no sub-package shape needed for ~340 lines of code total.
Method bound by AC.D-tpl.1 + AC.D-tpl.5 (engine boundaries).

### D-build.2 — Substitution engine

Custom regex `(?<!\\)\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}` (not
`string.Template`, since the constraint syntax is `{{var}}` not
`${var}`). Single-pass substitution; defaults are NOT recursively
expanded (a recursive shape would be method-not-in-AC and unbounded).
Escape: `\{{` and `\}}` decode to literal `{{` / `}}` after
substitution. Method bound by AC.D-tpl.1.

### D-build.3 — Frontmatter format

YAML frontmatter between `---` fences at file start
(`description: str`, `required: list[str]`, `optional: dict[str, str]`).
Variables declared in both `required` and `optional` reject as
malformed; an undeclared placeholder in the body also rejects as
malformed (so a typo in the template surfaces at parse time).
Method bound by AC.D-tpl.2 + AC.D-tpl.4.

### D-build.4 — CLI shape

Single `template` subcommand with nested subparsers for
`list` / `render` / `validate`. `--templates-root` lives on the
parent `template` parser so every mode picks it up; tests inject an
alternate root via this flag, normal use defaults to the bundled
`tools/pos-amend/templates/`. Method bound by AC.D-tpl.4.

### D-build.5 — Exit-code mapping (within existing pos-amend taxonomy)

- 0 — success.
- 2 — template/vars contract failure (unknown id, malformed template,
  missing required variable, unrecognised variable, malformed
  `--var` flag, malformed `--vars-file`).
- 3 — IO error (`--out` overwrite refusal, write failure).

No new exit codes introduced (constraint #6, AC.D-tpl.5).

### D-build.6 — Diagnostic shape

Every `TemplateError` subclass carries a `failure_class` string slug
(`template-not-found`, `template-malformed`, `missing-required-variable`,
`unrecognised-variable`). Diagnostics emit as
`template error [<slug>]: <detail>` to stderr; the CLI never partial-writes
stdout or the `--out` target on failure. Method bound by AC.D-tpl.5.

### D-build.7 — Initial template authoring

`templates/dispatch/sealed-component-build.md` (~70 lines, 6 required
+ 5 optional vars). `templates/plan/dev-discipline.md` (~110 lines,
13 required + 4 optional vars). The dispatch template captures the
session-start corpus reference, scope-fence, halt-trigger framing,
prime-objective framing, and deliverable shape; per-amendment specifics
arrive via vars. The plan template captures the 13 sections plus the
§14 method-decision register placeholder. Method bound by AC.D-tpl.7.

### Test breakdown

`tools/pos-amend/tests/test_template_engine.py` — 32 tests covering
every AC:

- 3 tests for AC.D-tpl.1 (substitution, determinism, escape).
- 4 tests for AC.D-tpl.2 (required missing, optional default,
  unrecognised, required/optional overlap).
- 4 tests for AC.D-tpl.3 (stdout default, `--out` writes, refuse-overwrite,
  `--force`).
- 3 tests for AC.D-tpl.4 (`list` enumerates, `validate` reports vars,
  validate-malformed-exits-nonzero).
- 9 tests for AC.D-tpl.5 (unknown id, malformed frontmatter, unmatched
  braces, undeclared placeholder, no-partial-stdout-on-failure,
  no-partial-file-on-failure, malformed `--var`, malformed `--vars-file`,
  plus 3 engine-level unit checks).
- 2 tests for AC.D-tpl.6 (existing help intact, console script intact).
- 5 tests for AC.D-tpl.7 (bundled root populated, dispatch validates,
  plan validates, dispatch renders against fixture vars, plan renders
  against fixture vars with every section heading present).

### Backwards-compat verification

Pre-extension baseline: 73 / 73 green at HEAD `9e91a21` (and again
at the commit immediately before this build's first commit). Post-
extension: 105 / 105 green (73 baseline + 32 new). `validate`,
`apply [--dry-run]`, `seal [--no-finalize|--scoped-sweep|--plan-doc]`
exit-code semantics, output formats, and side effects unchanged.
No new third-party dep (`PyYAML>=6` was already a dep). AC.D-tpl.6
satisfied.

### Commit SHAs

(populated post-commit; see git log for the build commit hash)

### Dependents cleared to dispatch

Phase migration (#17) cleared — the `pos-amend template` surface is
stable (CLI shape locked: `list` / `render --var/--vars-file/--out/--force` /
`validate`; exit-code mapping locked at 0/2/3 within the existing
taxonomy; `templates/<family>/<id>.md` discovery locked).
The Claude-skills-wrapping follow-up (D-3c) is a separate small
commit and does not block #17.
