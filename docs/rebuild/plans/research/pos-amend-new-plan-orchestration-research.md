# pos-amend `new-plan` orchestration + plan-doc skeleton template — research-implementation companion

Companion to: `docs/rebuild/plans/pos-amend-new-plan-orchestration.md`.
Authored: 2026-04-26.
Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`.

This doc inducts the plan-doc skeleton's section shape from the existing corpus, fixes per-section default content, marks each variable as `{{var}}` vs static text, locates the skeleton on disk (the existing template-engine machinery is reused unchanged), and specifies the `pos-amend new-plan <slug>` orchestration's CLI shape, slug→path resolution, and vars-file format.

The scope is purely additive to `tools/pos-amend/`: one new template file under `tools/pos-amend/templates/plan/` (or a renamed/extended version of the existing `dev-discipline.md` skeleton — D-2), and one new CLI entry point that scaffolds an empty vars-file at a predictable path. No engine changes; no new dependency; no sealed-component edits.

---

## 1. Source corpus surveyed

The "13-section shape" is induced from the following recent plans (all under `docs/rebuild/plans/`):

- `memory-system-live-client-and-stop-hook-write.md` — sealed-component, primary-persona + hands-off-lifecycle, 15 numbered sections (§1–§15).
- `primary-persona-conversational-onboarding-and-default-archetype.md` — sealed-component, 14 sections (§1–§14).
- `bootstrap-progress-statusline.md` — sealed-component, 14 sections (§1–§14).
- `dispatch-prompt-template-extension.md` — dev-discipline (sibling of this plan), 14 sections (§1–§14).
- `pos-amend-seal-automation-extension.md` — dev-discipline, 14 sections (§1–§14).
- `pos-amend-tracker-integration.md` — dev-discipline, similar shape.
- `amendment-33-memory-consumer-wiring-primary-persona.md` — sealed-component, 12 sections (older shape; the §11/§12 split-decisions convention had not yet stabilised).
- The existing `tools/pos-amend/templates/plan/dev-discipline.md` template (the precedent skeleton this plan iterates).

The shape stabilised around dispatch-prompt-template-extension and pos-amend-seal-automation-extension (both authored in the past two weeks). Earlier plans are 12–13 sections (older shape); recent plans are 13–15 sections (the §14 method-decision register and the §11 named-decisions / §12 owner-summary split arrived together via the seal-automation plan and the §14 plan-SHA-backfill machinery).

The induced shape — **13 always-on sections plus §14 method-decision register placeholder** — matches the FUTURE_IDEAS_DRAFT entry's "~13-section" estimate exactly when §14 is counted as the post-build register and §15 is treated as references (always-on but flat). Plans that show 14 or 15 sections are §1–§13 plus §14 register plus optional §15 references; plans that show 12 sections are pre-stabilisation.

The 13-section induction is robust. (If a build agent finds the count actually resolves to 8 or 25, that's a halt-trigger condition per the parent-plan halt-and-surface — but the corpus survey here makes 13 the load-bearing answer.)

---

## 2. The 13-section shape — induced section-by-section

For each section: title, default body content (static text in the skeleton vs `{{var}}` substitution), required-or-optional classification, and notes on when the section's content varies enough to warrant a `{{var}}`.

The classification rule: a section's body is a `{{var}}` when its content is genuinely per-plan; the section's heading is always static. Where a section has multiple semi-deterministic subsections (e.g. §5 behaviour-count table heading is static; the rows are per-plan), the body is one `{{var}}` and the plan author authors the body verbatim — no nested templating.

### §1. Summary / TLDR — required

- Heading: `## 1. Summary / TLDR` (static).
- Body: `{{TLDR}}` (required `{{var}}`).
- Default content: empty (the plan author's primary input).
- Notes: every plan in the corpus has §1 as a TLDR; the heading wording is uniform. Plan-author writes 1–4 paragraphs naming the work + the headline outcome. CLAUDE.md output-conventions §"Owner reads from §6 / §11 first" framing means §1 may name "owner reads from §<n> for decisions" inline.

### §2. Spec-objective placement (per CLAUDE.md §2.5) — required

- Heading: `## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)` (static).
- Body: `{{SPEC_PLACEMENT}}` (required `{{var}}`).
- Default content: empty.
- Notes: in dev-discipline plans this section names "no single spec objective" and explains why the work is dev-discipline territory (CLAUDE.md, docs, CDCs, `tools/`). In sealed-component plans this section names the v1.0 / v1.1 / v1.2 spec objective(s) the amendment satisfies and the AC.PO.1 + AC.PO.2 ladder. The section's body is genuinely per-plan; no static prose to bake in beyond the CLAUDE.md §2.5 quotation (which, since it is a citation rather than per-plan content, the skeleton MAY include as static prose at the section's head).

### §3. Three-lens analysis (per CLAUDE.md design lenses) — required

- Heading: `## 3. Three-lens analysis (per CLAUDE.md design lenses)` (static).
- Body: `{{LENS_ANALYSIS}}` (required `{{var}}`).
- Default content: empty; the body is structured by three subsection headings the plan author authors verbatim:
  - `### Lens 1 — Claude leverage`
  - `### Lens 2 — Harness + primary-persona value`
  - `### Lens 3 — ODD authoring`
- Notes: every plan in the corpus follows the same three-lens shape. The skeleton MAY pre-author the three subsection headings as a scaffold inside `{{LENS_ANALYSIS}}` to absorb that one decision (decision D-3 below).

### §4. Acceptance criteria ({{AC_PREFIX}}) — required

- Heading: `## 4. Acceptance criteria ({{AC_PREFIX}})` (template substitutes `{{AC_PREFIX}}` into the heading itself; engine supports this — placeholders work in headings).
- Body: `{{ACCEPTANCE_CRITERIA}}` (required `{{var}}`).
- Default content: empty.
- Notes: AC prefix examples — `AC.M.x` for memory-system live-client, `AC.D-tpl.x` for dispatch-template, `AC.D-sa.x` for seal-automation, `AC.D-np.x` for new-plan (this plan), `AC<NN>.x` for sealed-component-numbered plans. The `--ac-prefix` CLI arg in `pos-amend new-plan` pre-fills this var (see §5).

### §5. Behaviour-count check (ODD §3.3 forward) — required

- Heading: `## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)` (static; the parenthetical adapts in sealed-component plans to drop "applied as dev-discipline check" — D-3 below).
- Body: `{{BEHAVIOUR_COUNT}}` (required `{{var}}`).
- Default content: empty; plan author writes a `| # | Declared behaviour | AC |` markdown table.
- Notes: behaviour-count is universal; the table's row count varies per-plan.

### §6. Hard constraints — required

- Heading: `## 6. Hard constraints` (static).
- Body: `{{HARD_CONSTRAINTS}}` (required `{{var}}`).
- Default content: a stub of recurring constraints (no `--amend`, scope-fence, plan-before-code, no new dep, backward-compat preserved, CDC adherence) that plan-author edits/extends. This is the highest-leverage default-content section: ~6 of the 10–13 hard constraints in any plan are universal.
- Notes: the skeleton SHOULD ship a default constraint list (D-4 below), authored as a numbered list inside `{{HARD_CONSTRAINTS}}`'s default value (frontmatter `optional:` mapping). Plan author overrides with concrete-per-plan content.

### §7. Out of scope (explicit) — required

- Heading: `## 7. Out of scope (explicit)` (static).
- Body: `{{OUT_OF_SCOPE}}` (required `{{var}}`).
- Default content: empty.
- Notes: ODD §2.5 named-out-of-scope. Always per-plan.

### §8. Implementation order (suggested — builder's call to refine) — required

- Heading: `## 8. Implementation order (suggested — builder's call to refine)` (static).
- Body: `{{IMPLEMENTATION_ORDER}}` (required `{{var}}`).
- Default content: a numbered-list stub (read session-start corpus, read this plan + companions, write builder-plan, land core, run tests, conventional commits) that plan-author edits.
- Notes: see D-4 — same as §6, the skeleton ships a default authored as the var's optional default.

### §9. Impact / motivation OR Bookkeeping surface — required, but content-shape varies

- Heading: `## 9. {{SECTION_9_HEADING}}` — heading itself is `{{var}}`.
- Body: `{{SECTION_9_BODY}}` (required `{{var}}`).
- Default content: empty.
- Notes: this section's body and heading both vary by plan-class. In sealed-component plans this is "Bookkeeping surface (`pos-amend` manifest sketch)" with a YAML stub. In dev-discipline plans this is "Dispatch-prompt impact" / "Impact / motivation" / "Adoption notes." Two `{{var}}`s rather than one because the heading is part of what varies.

### §10. Halt triggers (builder halts + signals owner) — required

- Heading: `## 10. Halt triggers (builder halts + signals owner)` (static).
- Body: `{{HALT_TRIGGERS}}` (required `{{var}}`).
- Default content: a numbered-list stub of recurring halts (cross-component scope expansion, backward-compat fail, ODD-violating shape, new dep, wall-time exceeds N min) that plan-author edits.
- Notes: see D-4. About 50% of any plan's halt triggers are universal.

### §11. Decisions remaining for the owner to rule on — required

- Heading: `## 11. Decisions remaining for the owner to rule on` (static).
- Body: `{{DECISIONS_DETAIL}}` (required `{{var}}`).
- Default content: a single placeholder line ("(no genuinely uncertain decisions — confirm or replace)") so a plan with no §11 decisions doesn't render an empty section.
- Notes: per `feedback_summarize_and_surface_decisions`, decisions go in §11 in detail; §12 is the owner-readable summary table. Some plans have zero §11 decisions (everything was ruled at brief-time); the skeleton's default text covers that case.

### §12. Summary of named decisions (owner-readable) — required

- Heading: `## 12. Summary of named decisions (owner-readable)` (static).
- Body: `{{DECISIONS_SUMMARY}}` (required `{{var}}`).
- Default content: a markdown-table header (`| Decision | Recommendation | Why it matters |`) with one placeholder row.
- Notes: every plan with §11 decisions also has §12. When §11 has no decisions, §12 reads "n/a — no §11 decisions."

### §13. Halt-and-surface findings encountered during plan authoring — required

- Heading: `## 13. Halt-and-surface findings encountered during plan authoring` (static).
- Body: `{{HALT_FINDINGS}}` (required `{{var}}`).
- Default content: a stub naming the `feedback_subagent_odd_violation_halt` and `feedback_asymmetric_problem_solving` references plus an "(none observed)" placeholder.
- Notes: per `feedback_subagent_odd_violation_halt`, every plan author must explicitly state whether they encountered ODD violations during plan authoring. Default is "none."

### §14. Method-decision record (builder, post-build) — required-but-prefilled

- Heading: `## 14. Method-decision record (builder, post-build)` (static).
- Body: prefilled with subsection scaffold:
  - `### D-build.x — (placeholder for the build agent's method choices)`
  - `### Test breakdown` — (placeholder)
  - `### Backwards-compat verification` — (placeholder)
  - `### Commit SHAs` — (placeholder; auto-filled by `pos-amend seal --plan-doc <ABSOLUTE PATH>`)
  - `### Dependents cleared to dispatch` — (placeholder)
- Default content: the above scaffold is STATIC in the skeleton (no `{{var}}`). The §14 heading must exist verbatim so `pos-amend seal --plan-doc` can locate it; the subsection scaffold is convention from amendment #33 / #46 onward.
- Notes: the existing `dev-discipline.md` already has this section. Keep that scaffold byte-identical (so `pos-amend seal --plan-doc` keeps working).

### §15. References — optional

- Heading: `## 15. References` (static).
- Body: `{{REFERENCES}}` (optional `{{var}}`; default = the research-doc path + companions).
- Default content: an authored-by-default stub citing the research doc path (which the orchestration knows from the slug), CLAUDE.md, ODD methodology, VALUE_PROPOSITION, STATE/FUTURE_IDEAS, the pos-amend tools tree.
- Notes: §15 is universal but trivial; treating it as optional with a sensible default reduces the plan-author's manual editing surface to zero in most cases.

---

## 3. Variable inventory (the skeleton's contract)

Required variables (13):

1. `TITLE` — plan title (heading 1).
2. `TLDR` — §1 body.
3. `AC_PREFIX` — used in §4 heading + body references; e.g. `AC.D-np.x`.
4. `SPEC_PLACEMENT` — §2 body.
5. `LENS_ANALYSIS` — §3 body (subsections inside).
6. `ACCEPTANCE_CRITERIA` — §4 body.
7. `BEHAVIOUR_COUNT` — §5 body.
8. `HARD_CONSTRAINTS` — §6 body (default-stubbed via §6 below).
9. `OUT_OF_SCOPE` — §7 body.
10. `IMPLEMENTATION_ORDER` — §8 body (default-stubbed).
11. `SECTION_9_HEADING` — §9 heading suffix.
12. `SECTION_9_BODY` — §9 body.
13. `HALT_TRIGGERS` — §10 body (default-stubbed).
14. `DECISIONS_DETAIL` — §11 body.
15. `DECISIONS_SUMMARY` — §12 body.
16. `HALT_FINDINGS` — §13 body.

That's 16 required variables, not 13. The 13-section count refers to numbered sections; the per-section count of `{{var}}`s is 16 because §4's heading also carries `AC_PREFIX` (one var, two appearances) and §9 splits into heading + body (two vars). The FUTURE_IDEAS_DRAFT entry's "13 required vars" was a low estimate; 16 is the empirical count. (Halt-trigger condition: if the count comes out at 8 or 25 the induction is fundamentally off; 16 is well within range.)

Optional variables (with defaults — all default to empty unless noted):

- `COMPANIONS` — §0 frontmatter line ("Companions: …"); default empty (skeleton emits no Companions line when empty).
- `ANCESTOR_RECORD` — §0 frontmatter line ("Ancestor record: …"); default empty.
- `IMPACT_BLOCK` — currently in `dev-discipline.md` skeleton; merged into `SECTION_9_BODY` per §2 induction (so this var is REMOVED in the new shape — see D-2 migration).
- `REFERENCES` — §15 body; default = stub citing research doc + standard refs.
- `WORKING_DIRECTORY` — `/Users/lukeivers/ivers-corp-pos-v2/`; default = that string.
- `STATUS_LINE` — top-of-doc status; default `"plan (pre-dispatch). <ISO date>."` with the date filled by orchestration at scaffold time.
- `RESEARCH_PATH` — derived from slug: `docs/rebuild/plans/research/<slug>-research.md`; orchestration pre-fills.

That's 7 optional variables. Total surface: 23 variables (16 required, 7 optional). The orchestration's job (§5 below) is to pre-fill the trivial ones and let the plan author focus on the ~13 non-trivial required ones.

---

## 4. Where the skeleton lives + format

- **Path:** `tools/pos-amend/templates/plan/dev-discipline.md` is renamed/replaced by the new shape. Two viable approaches:
  - D-2a (recommended): EXTEND the existing `dev-discipline.md` skeleton in place, growing its required-variable list from 13 to 16 and adding `SECTION_9_HEADING` / `SECTION_9_BODY` / `REFERENCES` / `STATUS_LINE` / `RESEARCH_PATH`. Existing callers (none today — the skeleton has not been used in anger yet) remain compatible; the dev-discipline plan family is the only consumer.
  - D-2b: ADD a new `tools/pos-amend/templates/plan/full-skeleton.md` alongside the existing `dev-discipline.md`, and let plan authors choose. Doubles the surface; rejected.
  - D-2c: ADD a new sealed-component-plan template (e.g. `tools/pos-amend/templates/plan/sealed-component.md`) and keep `dev-discipline.md` as the dev-discipline-only variant. Defensible (sealed-component plans have §10 bookkeeping with a manifest YAML stub that dev-discipline plans don't), but the §9 split-heading-and-body pattern handles that variation — both classes of plan use the same 16-var skeleton.

Recommendation: D-2a. One skeleton; `SECTION_9_HEADING` / `SECTION_9_BODY` absorb the dev/sealed split.

- **Format:** YAML frontmatter declaring `description:` + `required:` + `optional:` per the existing template-engine contract (see `tools/pos-amend/src/pos_amend/template_engine.py`). Body is markdown with `{{KEY}}` placeholders; `\{{` / `\}}` escape literal braces. No new format; no engine change.

- **Engine reuse:** `pos-amend template render plan/dev-discipline --vars-file <path>` already works today. The `new-plan` orchestration is sugar over this invocation: scaffold the vars-file, then optionally invoke the renderer. The engine itself is unchanged.

---

## 5. `pos-amend new-plan <slug>` orchestration — CLI shape

### 5.1 Surface

```
pos-amend new-plan <slug>
  [--title <title-string>]
  [--ac-prefix <prefix-string>]
  [--vars-out <path>]
  [--plan-out <path>]
  [--render]
  [--force]
```

- Positional `<slug>` — the plan's filename slug, e.g. `pos-amend-new-plan-orchestration`. Used for: vars-file path resolution, plan-doc path resolution, research-doc path inference, `RESEARCH_PATH` var pre-fill.
- `--title <title-string>` — pre-fills the `TITLE` variable in the scaffolded vars-file. Default: empty (plan author fills in by hand).
- `--ac-prefix <prefix-string>` — pre-fills the `AC_PREFIX` variable. Default: empty (plan author chooses).
- `--vars-out <path>` — where the scaffolded vars-file is written. Default: `<repo-root>/docs/rebuild/plans/<slug>.vars.yaml` — see §5.2 for the path-resolution decision.
- `--plan-out <path>` — where the rendered plan markdown is written if `--render` is passed. Default: `<repo-root>/docs/rebuild/plans/<slug>.md`.
- `--render` — after scaffolding the vars-file, immediately render the plan-doc skeleton to `--plan-out` (against the vars-file's empty-but-present values). Default: no render (the user will edit the vars-file before rendering).
- `--force` — overwrite an existing `--vars-out` (or `--plan-out` when `--render`). Default: refuse-overwrite.

### 5.2 Slug → path resolution (D-1)

Three viable predictable paths for the vars-file:

- D-1a (recommended): `<repo-root>/docs/rebuild/plans/<slug>.vars.yaml` — sibling of where the rendered plan lands. Predictable; co-located with the plan-doc; matches the convention that all plan-related artefacts live under `docs/rebuild/plans/`.
- D-1b: `<repo-root>/.scratch/pos-amend/new-plan/<slug>.vars.yaml` — ephemeral-by-design (`.scratch/` is gitignored). Avoids checking vars-files into git. But the vars-file IS the canonical record of the plan's contract values; gitignoring it loses audit value.
- D-1c: `<repo-root>/tools/pos-amend/scratch/<slug>.vars.yaml` — under the tool's own tree. Awkward; mixes tool internals with per-plan state.

Recommendation: D-1a. Vars-files commit to git alongside their plan-docs; the vars-file becomes a small but authoritative record of "what variables the plan was rendered against," which is itself useful audit information. The `.vars.yaml` extension makes filtering/finding vars-files straightforward (`ls docs/rebuild/plans/*.vars.yaml`).

The slug resolves only to filenames, never to subdirectories. Slugs containing `/` are rejected with a structured diagnostic. Slugs are validated against `^[a-z][a-z0-9-]*$` (lowercase + hyphens only); other characters reject with a structured diagnostic.

### 5.3 Vars-file format (D-5)

Two viable formats:

- D-5a (recommended): YAML mapping (matches the existing `--vars-file` contract for `pos-amend template render`). Multi-line strings use YAML block scalars (`|`); short values inline. Parsed by `yaml.safe_load`. Reuses the engine's `_load_vars_file` helper unchanged.
- D-5b: TOML mapping. Off-pattern; `pos-amend template render` already accepts YAML, not TOML.
- D-5c: Markdown frontmatter. Fragile for multi-line values; off-pattern.

Recommendation: D-5a. Matches the dispatch-template family's vars-file format byte-for-byte, so a plan author who learns one format learns both.

### 5.4 Scaffolded vars-file content

The scaffolded file is a YAML mapping with one entry per required variable, plus the optional variables that were pre-fillable:

```yaml
# pos-amend new-plan scaffold for <slug>
# Required vars (16):
TITLE: "<title-from-cli-or-empty>"
TLDR: |
  <empty — plan author fills in §1 body>
AC_PREFIX: "<from-cli-or-empty>"
SPEC_PLACEMENT: |
  <empty — §2 body>
LENS_ANALYSIS: |
  ### Lens 1 — Claude leverage

  <…>

  ### Lens 2 — Harness + primary-persona value

  <…>

  ### Lens 3 — ODD authoring

  <…>
ACCEPTANCE_CRITERIA: |
  <empty — §4 body>
BEHAVIOUR_COUNT: |
  | # | Declared behaviour | AC |
  |---|--------------------|-----|
  | 1 | … | <ac-id> |
HARD_CONSTRAINTS: |
  1. **No `--amend`.** Corrective new commits only.
  2. **Scope fence.** <plan-author edits>.
  3. <plan-author adds more>.
OUT_OF_SCOPE: |
  - <plan-author lists>
IMPLEMENTATION_ORDER: |
  1. Read session-start corpus per CLAUDE.md.
  2. Read this plan + companions.
  3. <…>
SECTION_9_HEADING: "Impact / motivation"   # or "Bookkeeping surface" for sealed-component
SECTION_9_BODY: |
  <empty>
HALT_TRIGGERS: |
  1. Cross-component scope expansion. Halt.
  2. <plan-author adds more>.
DECISIONS_DETAIL: |
  (no genuinely uncertain decisions — confirm or replace)
DECISIONS_SUMMARY: |
  | Decision | Recommendation | Why it matters |
  |---|---|---|
  | (placeholder) | | |
HALT_FINDINGS: |
  Per `feedback_subagent_odd_violation_halt`: halt and surface any
  ODD violation observed in surrounding code/docs.

  **(none observed during plan authoring.)**

# Optional vars (7) — defaults already in the template; uncomment + fill to override:
# COMPANIONS: ""
# ANCESTOR_RECORD: ""
# REFERENCES: |
#   <override the default research-doc + standard-refs stub>
# STATUS_LINE: "plan (pre-dispatch). <ISO date>."
# RESEARCH_PATH: "docs/rebuild/plans/research/<slug>-research.md"   # auto-filled
# WORKING_DIRECTORY: "/Users/lukeivers/ivers-corp-pos-v2/"          # default
```

The orchestration writes this skeleton with `<slug>` replaced; `<title-from-cli-or-empty>` and `<from-cli-or-empty>` filled from `--title` / `--ac-prefix` if provided; ISO date filled from current `date +%Y-%m-%d`.

### 5.5 Module location + integration with the existing CLI

- New module `tools/pos-amend/src/pos_amend/commands/new_plan.py` carrying `run(slug, title, ac_prefix, vars_out, plan_out, render, force) -> int` entry point.
- New subparser `pos-amend new-plan <slug>` registered in `tools/pos-amend/src/pos_amend/cli.py` alongside the existing `validate` / `apply` / `seal` / `template` subcommands.
- The `--render` path delegates to the existing `pos_amend.commands.template.run("render", ...)` — no engine duplication.
- Exit-code mapping (within existing pos-amend taxonomy 0/2/3):
  - 0 — vars-file (and plan-file when `--render`) successfully scaffolded.
  - 2 — invalid slug, malformed `--title` / `--ac-prefix`, slug→path resolution failure, template-render contract failure (when `--render`).
  - 3 — IO failure (refuse-overwrite without `--force`, write failure).

### 5.6 Tests (per ODD §2.5 + dev CDC test convention)

One test file per AC (per `feedback_*` convention), under `tools/pos-amend/tests/`:

- `test_AC.D-np.1_scaffold_vars_file.py` — happy-path scaffold.
- `test_AC.D-np.2_pre_fill_title_and_ac_prefix.py` — `--title` / `--ac-prefix` pre-fill behaviour.
- `test_AC.D-np.3_render_after_scaffold.py` — `--render` end-to-end shape.
- `test_AC.D-np.4_failure_modes.py` — slug-validation, refuse-overwrite, malformed args.
- `test_AC.D-np.5_skeleton_renders_clean.py` — fixture vars-file + template render produces fixture-expected output (re-uses `pos-amend template render` against the new skeleton).
- `test_AC.D-np.6_backward_compat.py` — pre-existing pos-amend CLI surface unchanged.

(Builder may consolidate or split as method-call within the AC outcomes.)

---

## 6. Composition with sibling work

### 6.1 dispatch-prompt-template-extension

This plan composes ON TOP OF the dispatch-prompt-template-extension (already landed at commit `dbabd37`). The template engine, the YAML frontmatter contract, the `--vars-file` flag, the `description:` + `required:` + `optional:` parser, the registry-discovery walker, the failure-class taxonomy — all reused unchanged. No engine code is touched; only one new template file (or one renamed/extended template) and one new CLI subcommand land.

### 6.2 pos-amend-seal-automation-extension

The §14 `### Commit SHAs` subsection that `pos-amend seal --plan-doc <abs-path>` backfills MUST exist verbatim in the rendered plan-doc. The skeleton's §14 scaffold (per §2 §14 above) preserves this byte-identical to the existing `dev-discipline.md` skeleton's §14, so seal-automation continues to work without any change. This is verifiable as a test (render the skeleton + grep for the §14 heading; assert the seal-automation invocation finds it).

### 6.3 Idea 17 (dispatch-template ↔ persona-tracker composition)

Idea 17 is sibling work — composing the dispatch-template engine with the persona-tracker context to auto-fill template variables from workspace state. The `new-plan` orchestration here is on the same composition arc but for plan-docs rather than dispatches. Idea 17's "trigger to activate" rule (engine + tracker both stable) suggests `new-plan` is a fair early test of the composition pattern: if `new-plan` proves the orchestration shape works, dispatch-template ↔ tracker becomes a smaller incremental step.

---

## 7. Cycle-mechanics lessons from the dispatch-template (commit `a17f1f7`) — relevant subset

The dispatch-template was extended at `a17f1f7` to carry "Cycle mechanics" lessons (workflow ordering, abs-path on `--plan-doc`, H19 admission debt, one-test-file-per-AC). For the plan-doc skeleton, the relevant subset is:

- **§14 method-decision register heading is pre-authored** — already in the existing `dev-discipline.md` skeleton; preserved in the extension. Load-bearing for `pos-amend seal --plan-doc`.
- **One test file per AC** — convention applies to the new tests for `pos-amend new-plan` (§5.6 above). Already standard in the corpus from AC35.x onward.
- **Workflow ordering / `pos-amend apply` BEFORE commit / abs-path on `--plan-doc`** — these are sealed-component-amendment cycle mechanics that don't apply to dev-discipline plans. The plan-doc skeleton itself doesn't carry them; they remain in the dispatch template (where they belong).

---

## 8. Halt-and-surface findings during research authoring

Per `feedback_subagent_odd_violation_halt`:

**No ODD violations identified in surrounding code or docs during research authoring.** The pos-amend codebase post-template-engine (post-`dbabd37`) is clean under §2.5. The existing `dev-discipline.md` skeleton at `tools/pos-amend/templates/plan/dev-discipline.md` is internally consistent with the engine's contract and with the corpus's actual plan shape; the gap is that 13 vars are not 16 (i.e. the skeleton is somewhat under-specified vs. the corpus, not over-specified).

**Asymmetric findings (per `feedback_asymmetric_problem_solving`):**

1. **The vars-file IS a small audit artefact.** Committing vars-files alongside plan-docs (D-1a) makes it possible to diff "what changed between two plan revisions" at the vars-level, not the rendered-markdown level. Useful when a plan is amended and re-rendered.
2. **`--render` makes `new-plan` a one-shot end-to-end command.** A plan author with `--title` + `--ac-prefix` + a willingness to fill the vars-file in their editor can `pos-amend new-plan <slug> --title "…" --ac-prefix AC.X.x --render` and have BOTH the vars-file AND a (skeleton-shaped) plan-doc on disk in one invocation. Editing the vars-file then re-running `pos-amend template render plan/dev-discipline --vars-file <path> --out <plan> --force` re-renders.
3. **Memory-doc skeleton + commit-message templates** (named in FUTURE_IDEAS_DRAFT) are direct generalisations of the same `new-<artefact-class>` orchestration shape. If `pos-amend new-plan` proves out, `pos-amend new-memory <slug>` and `pos-amend new-commit <kind>` are mechanical follow-ups.

---

## 9. Decisions for the parent plan to surface for owner ruling

The research surfaces five decisions of genuine interest that feed into the parent plan's §11. (Decisions D-1, D-2, D-3, D-4, D-5 referenced inline above.)

- **D-1 — Vars-file path:** `<repo>/docs/rebuild/plans/<slug>.vars.yaml` (recommended) vs `.scratch/` ephemeral vs `tools/pos-amend/scratch/`.
- **D-2 — Skeleton placement:** extend the existing `dev-discipline.md` (recommended) vs new `full-skeleton.md` alongside vs split into dev/sealed-component variants.
- **D-3 — Pre-author the three Lens-1/2/3 subsection headings** inside `LENS_ANALYSIS`'s default value (recommended; absorbs one decision).
- **D-4 — Pre-stub `HARD_CONSTRAINTS` / `IMPLEMENTATION_ORDER` / `HALT_TRIGGERS`** with default content authored as the variable's optional default (recommended; absorbs ~50% of recurring content).
- **D-5 — Vars-file format:** YAML (recommended; matches `--vars-file`) vs TOML vs frontmatter.

The parent plan's §11 lifts these into owner-readable form with recommendations.

---

## 10. References

- Existing template engine: `tools/pos-amend/src/pos_amend/template_engine.py`, `tools/pos-amend/src/pos_amend/commands/template.py`, `tools/pos-amend/src/pos_amend/cli.py`.
- Existing dev-discipline plan-doc skeleton: `tools/pos-amend/templates/plan/dev-discipline.md`.
- Existing dispatch template: `tools/pos-amend/templates/dispatch/sealed-component-build.md`.
- Sibling plan (engine ancestor): `docs/rebuild/plans/dispatch-prompt-template-extension.md`.
- Sibling plan (seal-automation ancestor for `--plan-doc`): `docs/rebuild/plans/pos-amend-seal-automation-extension.md`.
- Source FUTURE_IDEAS_DRAFT entries: `docs/rebuild/FUTURE_IDEAS_DRAFT.md` lines 25, 31, 57, 71–72, 80.
- Idea 17 (composition stretch): `docs/rebuild/FUTURE_IDEAS.md` "Idea 17 — Dispatch-template ↔ persona-tracker composition (stretch)".
- Plan corpus surveyed: `docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.md`, `docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.md`, `docs/rebuild/plans/bootstrap-progress-statusline.md`, `docs/rebuild/plans/dispatch-prompt-template-extension.md`, `docs/rebuild/plans/pos-amend-seal-automation-extension.md`, `docs/rebuild/plans/pos-amend-tracker-integration.md`, `docs/rebuild/plans/amendment-33-memory-consumer-wiring-primary-persona.md`.
- VALUE_PROPOSITION (prime objective AC.PO.1 + AC.PO.2): `docs/rebuild/VALUE_PROPOSITION.md`.
- ODD methodology: `docs/odd-methodology.md`, `docs/odd-in-pos.md`.
- Feedback corpus referenced: `feedback_summarize_and_surface_decisions`, `feedback_subagent_odd_violation_halt`, `feedback_asymmetric_problem_solving`, `feedback_amendment_dispatch_speedups`, `feedback_no_amend_in_agent_dispatches`, `feedback_always_specify_wd_in_dispatches`.
