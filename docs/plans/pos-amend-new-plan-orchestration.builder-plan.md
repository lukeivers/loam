# pos-amend new-plan orchestration — builder-plan

Companion to: `docs/plans/pos-amend-new-plan-orchestration.md`.
Builder-plan author: build agent.
Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`.
Pre-amendment baseline: 106 tests in `tools/pos-amend/tests/` green.

## Method choices (D-build.x)

### D-build.1 — Skeleton template extension shape (D-2 → method)

Extend `tools/pos-amend/templates/plan/dev-discipline.md` IN PLACE per locked D-2.

**Frontmatter changes:**
- `required:` grows from current 13 entries (TITLE, TLDR, AC_PREFIX, SPEC_PLACEMENT, LENS_ANALYSIS, ACCEPTANCE_CRITERIA, BEHAVIOUR_COUNT, HARD_CONSTRAINTS, OUT_OF_SCOPE, IMPLEMENTATION_ORDER, HALT_TRIGGERS, DECISIONS_SUMMARY, HALT_FINDINGS) to 15 (add SECTION_9_HEADING, SECTION_9_BODY).
- `DECISIONS_DETAIL` was previously OPTIONAL; promote to REQUIRED so research §3 inventory's "16 required" matches. Net new required: SECTION_9_HEADING, SECTION_9_BODY, DECISIONS_DETAIL → required count = 16. (Backward-compat: any pre-extension caller would have to supply these to render. The currently-bundled plan template has not been used in anger yet — only its self-test fixture. The self-test in `test_template_engine.py` `test_AC_D_tpl_7_bundled_plan_renders_against_fixture_vars` supplies the 13 originals — must be updated to supply the new 3. That update is a test data change, not a behaviour change of the engine; AC.D-tpl.7 fixture is part of the same dev-discipline tree.)
- `optional:` grows from current 4 (COMPANIONS, ANCESTOR_RECORD, IMPACT_BLOCK, DECISIONS_DETAIL) to 7 entries: COMPANIONS, ANCESTOR_RECORD, REFERENCES (new, default = stub), STATUS_LINE (new, default empty — orchestration fills), RESEARCH_PATH (new, default empty — orchestration fills), WORKING_DIRECTORY (new, default = standard repo path). Drop IMPACT_BLOCK (its content folded into SECTION_9_BODY); drop DECISIONS_DETAIL from optional (promoted to required).
  - Net optional count: 6 not 7. Re-check research §3: "COMPANIONS, ANCESTOR_RECORD, IMPACT_BLOCK, REFERENCES, WORKING_DIRECTORY, STATUS_LINE, RESEARCH_PATH" = 7, but research §3 says IMPACT_BLOCK is REMOVED. So 6 optional. Acceptable; AC.D-np.5 fixture exercises all of them.

**Body changes:**
- §0 frontmatter line: add `**Status:** {{STATUS_LINE}}` and `**Working directory:** {{WORKING_DIRECTORY}}` and `**Research:** {{RESEARCH_PATH}}` lines (all optional with sensible defaults; `STATUS_LINE` empty default emits an empty status line — acceptable).
- §9 heading becomes `## 9. {{SECTION_9_HEADING}}` and body becomes `{{SECTION_9_BODY}}`.
- §11 body uses `{{DECISIONS_DETAIL}}` (already true today; promotes to required).
- §15 References: append a new section `## 15. References` with `{{REFERENCES}}` (optional with default = standard refs stub).
- §14 scaffold: PRESERVE byte-identical (locked AC.D-np.7) — the existing §14 heading + subsections (`### D-build.x`, `### Test breakdown`, `### Backwards-compat verification`, `### Commit SHAs`, `### Dependents cleared to dispatch`). Note: current skeleton has DUPLICATE `### Commit SHAs` — that's a pre-existing typo. Per the §14-scaffold-byte-identical constraint, leave as-is (preserving the duplicate); AC.D-np.7 is about preservation, not correction. Surface this finding (asymmetric finding for owner).

### D-build.2 — Default-stub content for HARD_CONSTRAINTS / IMPLEMENTATION_ORDER / HALT_TRIGGERS (D-4)

Per locked D-4: pre-stub via the `optional:` defaulting mechanism BUT these vars are required, not optional. Method realisation: the orchestration's vars-file scaffold writes the pre-stubbed content; the template skeleton's required-vars list does NOT carry per-required-var defaults (the engine doesn't support per-required defaults). Pre-stubs live in the orchestration's vars-file scaffold (`new_plan.py` writes them).

This honours the spirit of D-4 (recurring content pre-filled) while respecting the engine's contract (required vars are required). The vars-file IS the surface where pre-stubs live; the template is structurally unchanged.

### D-build.3 — Lens-1/2/3 subsection headings pre-author (D-3)

Same as D-build.2 — the pre-authored subsection headings live inside the vars-file scaffold's `LENS_ANALYSIS` block, not the template body. Engine contract preserved; D-3 honoured.

### D-build.4 — `new_plan.py` module structure

New module: `tools/pos-amend/src/pos_amend/commands/new_plan.py`.

Single `run(...)` entry point with signature:
```python
def run(
    slug: str,
    *,
    title: str | None,
    ac_prefix: str | None,
    vars_out: Path | None,
    plan_out: Path | None,
    render: bool,
    force: bool,
    repo_root: Path | None = None,  # testing hook
) -> int
```

- `repo_root` defaults to git-repo-root resolution (same shape as `seal.py` does).
- Slug validation regex: `^[a-z][a-z0-9-]*$` (locked D-6).
- Default `vars_out`: `<repo_root>/docs/plans/<slug>.vars.yaml` (locked D-1).
- Default `plan_out`: `<repo_root>/docs/plans/<slug>.md`.
- Pre-stubbed vars-file content: hard-coded module-level constant; substitutes `<slug>`, `<title>`, `<ac-prefix>`, `<iso-date>`.
- `--render` path: imports `pos_amend.commands.template.run("render", ...)` and delegates with the just-written vars-file as `vars_file=`. No engine duplication.
- Error mapping (per locked AC.D-np.4 taxonomy):
  - exit 2: invalid slug, missing title parsing, template-render contract failure (any TemplateError raised by delegated render), slug containing `/`.
  - exit 3: refuse-overwrite without `--force`, IO failure (write permission denied).
- Diagnostic emission: `print(f"new-plan error [{class}]: {msg}", file=sys.stderr)`.

### D-build.5 — CLI registration

Add `p_new_plan = sub.add_parser("new-plan", ...)` in `cli.py`. Positional `slug`. Optional `--title`, `--ac-prefix`, `--vars-out`, `--plan-out`, `--render`, `--force`. Dispatch to `new_plan_cmd.run(...)`.

### D-build.6 — Tests (one file per AC)

- `test_AC.D-np.1_scaffold_vars_file.py`
- `test_AC.D-np.2_pre_fill_title_and_ac_prefix.py`
- `test_AC.D-np.3_render_after_scaffold.py`
- `test_AC.D-np.4_failure_modes.py`
- `test_AC.D-np.5_skeleton_renders_clean.py` (uses fixture under `tests/fixtures/plan-skeleton/`)
- `test_AC.D-np.6_backward_compat.py`
- `test_AC.D-np.7_section_14_preserved.py`

Tests use `tmp_path` for repo_root injection; the `repo_root` arg threads through `new_plan.run()` so tests don't need a real git tree.

### D-build.7 — Fixtures for AC.D-np.5

`tools/pos-amend/tests/fixtures/plan-skeleton/vars.yaml` — exercises every required + every optional with non-default values.
`tools/pos-amend/tests/fixtures/plan-skeleton/expected.md` — byte-identical expected render. Authored by hand against the template's actual output (regenerate via `pos-amend template render` once the skeleton is in shape, then commit the result as fixture).

### D-build.8 — README update

Brief paragraph in `tools/pos-amend/README.md` describing `pos-amend new-plan` + the widened skeleton.

### D-build.9 — Existing AC.D-tpl.7 plan-template fixture test update

`test_AC_D_tpl_7_bundled_plan_renders_against_fixture_vars` currently supplies 13 vars; must supply 16 (add SECTION_9_HEADING, SECTION_9_BODY, DECISIONS_DETAIL) so the test stays green with the widened required list. This is a test-data change, not a behaviour change. Backward-compat AC.D-np.6 says "pre-existing test suite passes" — interpreted as: every test still passes (with the test's data updated to reflect the widened contract). The alternative (keep DECISIONS_DETAIL as optional and SECTION_9_HEADING/BODY as optional with sensible defaults) preserves byte-identical existing-test data, but loses the audit-friendliness of those vars being required. **Owner consideration** — but locked D-2 says extend in place; the choice between strict-required vs default-optional for SECTION_9_HEADING/BODY/DECISIONS_DETAIL is METHOD within D-2's bounds.

**Decision:** keep SECTION_9_HEADING / SECTION_9_BODY / DECISIONS_DETAIL as REQUIRED (matching research §3 inventory of 16 required). Update the `test_AC_D_tpl_7_bundled_plan_renders_against_fixture_vars` to supply them. This is the clearest reading and matches the research doc's count.

### D-build.10 — Implementation order

1. Read corpus (done).
2. Pre-amendment test run (done — 106 green).
3. Write builder-plan (this file).
4. Land skeleton extension: edit `dev-discipline.md`. Update `test_AC_D_tpl_7_bundled_plan_renders_against_fixture_vars` accordingly.
5. Run subset of test suite to verify the skeleton change doesn't regress AC.D-tpl.7. If green, proceed.
6. Land `new_plan.py` + CLI registration.
7. Land tests AC.D-np.1–7.
8. Author fixtures (vars.yaml + expected.md) for AC.D-np.5.
9. Run full pos-amend test suite — expect 106 + 7 new = 113+ tests.
10. README update.
11. Verify clean tree state, commit (one feat commit covers the bundle since it's tightly coupled).
12. `pos-amend apply --dry-run` (no manifest changes — should remain a no-op for the existing manifests).
13. Skip seal: dev-discipline plan, no manifest, no SEAL_COMMIT bump.

## Halt-and-surface findings during builder-plan authoring

1. **Pre-existing `## 14.` scaffold has DUPLICATE `### Commit SHAs` heading** in `tools/pos-amend/templates/plan/dev-discipline.md` (lines 125 and 129). Per the §14-byte-identical constraint, I will NOT correct this in the build (correction would break AC.D-np.7 byte-identity). Surface to owner as asymmetric finding.

2. **The plan's research §3 inventory says "16 required."** That count requires promoting DECISIONS_DETAIL from optional to required (currently optional) AND adding SECTION_9_HEADING + SECTION_9_BODY (new). Adopted as the required path; the existing AC.D-tpl.7 fixture-test gets a 3-var data update. The rendered output stays the same shape; AC.D-tpl.6 (no engine behaviour change) holds.

3. **No ODD violations in surrounding code or docs.**

## Commit shape

One feature commit:
- `feat(tools): pos-amend new-plan orchestration + plan-doc skeleton extension (AC.D-np.1–7)`
- Includes: skeleton edit, fixture-test data update, new_plan.py, cli.py registration, 7 new test files, fixtures, README update.

No SEAL_COMMIT bump, no manifest, no seal commit (dev-discipline plan).
