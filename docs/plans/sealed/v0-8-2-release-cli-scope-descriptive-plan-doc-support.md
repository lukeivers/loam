# v0.8.2 PATCH — `loam release` accepts scope-descriptive plan-doc paths

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`.
**Slug:** `v0-8-2-release-cli-scope-descriptive-plan-doc-support`. Version-named slug — this PATCH itself precedes the scope-descriptive-slug capability it ships, so the predecessor convention applies to its own publish. Future plan-docs (starting with the paper publish's downstream consumer flow) use scope-descriptive slugs per `feedback_version_numbers_at_release_time`.
**Date authored:** 2026-05-13.
**Class:** **PATCH** per `docs/release-versioning-policy.md` — defect-closure on the v0.6.0 release-process outcome shape (gates assumed version-named plan-doc and hard-smoke filenames; scope-descriptive-slug discipline is the new world post-`feedback_version_numbers_at_release_time`). No new outcome capability; tightens the existing `loam release` surface to support the new naming convention without regressing version-named-file support.
**Predecessor:** v0.8.1 SHIPPED PUBLIC 2026-05-10 (tag `v0.8.1`, annotated `bdc2e81`; seal `9411061`). HEAD also carries v0.9.0 SHIPPED LOCAL (seal `4a4535f`, awaiting owner-gated publish per ASK-FIRST); v0.8.2 builds-forward per `feedback_build_forward_on_publish_pending` and lands on top of the v0.9.0 seal.
**Working directory:** `/Users/lukeivers/loam/`.
**Owner authorization:** dispatcher-issued 2026-05-13 (current dispatch brief). Build authorization covers plan-doc + source-edit + apply + seal + HARD smoke. Publish remains owner-asked per ASK-FIRST.

---

## §1 — Outcome shape (the "why")

The v0.6.0 `loam release` CLI gates were authored against a then-universal convention: plan-doc filenames started with the version slug (e.g., `v0-6-0-release-process.md`), and HARD smoke writeups were named `<version-slug>-hard-smoke.md`. The two gates that read these files (`check_acs_verified` and `check_hard_smoke`) infer their paths by globbing on the version slug:

- `check_acs_verified` calls `_find_plan_doc(repo_root, version)` → `docs/plans/<slug>-*.md` glob.
- `check_hard_smoke` constructs `docs/experiments/<slug>-hard-smoke.md` directly.

`feedback_version_numbers_at_release_time` (captured 2026-05-13) reverses that convention: plan-doc filenames are now scope-descriptive (the slug describes the work, no version pre-baked) and version derives at release-time from `(current_published, class)`. The first downstream consumer is the ODD paper publish, whose plan-doc lives at `docs/plans/odd-paper-methodology-publish.md` and whose HARD smoke writeup lives at `docs/experiments/odd-paper-methodology-publish-hard-smoke.md`. Run `loam release v0.9.0 --dry-run` against that artefact today and:

- `check_hard_smoke` looks for `docs/experiments/v0-9-0-hard-smoke.md` — doesn't exist → RED with "missing HARD smoke writeup" hint.
- `check_acs_verified` globs `docs/plans/v0-9-0-*.md` and `docs/plans/v0-9-0.md` — nothing matches → RED with "no plan-doc found" hint.

The gates are working correctly against the old convention; they just don't know about the new one. The fix is a single new flag — `--plan-doc <path>` — that overrides both inferences when set. When the operator provides the flag:

- `check_acs_verified` reads the named plan-doc directly.
- `check_hard_smoke` reads `docs/experiments/<plan-doc-stem>-hard-smoke.md`, where `<plan-doc-stem>` is `Path(plan_doc).stem` (the basename without `.md`).

When the flag is absent, every existing version-slug-glob path is preserved verbatim (backward-compat for v0.6.0 / v0.7.x / v0.8.x plan-docs that already followed the version-named convention).

The PATCH closes the defect surfaced by the paper publish's pending release: the release-CLI cannot dogfood its first scope-descriptive-slug downstream consumer without this fix. Same defect class as v0.7.2 (`AC.READYP.1` — fixed `check_acs_verified` to scope AC-ID scan to §4 only) — both are gates that ship a behavioural assumption baked into the v0.6.0 minor and need PATCH-class follow-ons as new conventions land.

**Why PATCH (not MINOR).** No new outcome capability: `loam release` already publishes versions; this just unblocks the publish path for one new artefact-naming convention. The capability `feedback_version_numbers_at_release_time` ships in is the convention itself — captured as a feedback memory + applied to future plan-docs. This PATCH is the smallest possible defect-closure that makes the v0.6.0 release-CLI's existing capability work against the new convention. Defect-closure within already-shipped outcome = PATCH per `docs/release-versioning-policy.md`.

**Why now (build-forward sequencing).** v0.9.0 is SHIPPED LOCAL pending owner publish. The owner can publish v0.9.0 today via the manual fallback path; the publish gate's machinery is what's blocked. v0.8.2 lands on top of v0.9.0's seal (`4a4535f`) so when v0.9.0 is eventually published, the publish flow has working gates for scope-descriptive-slug plan-docs going forward. Build-forward per `feedback_build_forward_on_publish_pending`: don't stall the build queue on owner-gate availability.

---

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ harness toolkit ships working primitives — `loam release`
           is one of those primitives; it must work for the conventions
           the harness now requires (scope-descriptive plan-doc slugs)
             └─ AC.SDPD.1 (`--plan-doc` flag accepted by argparse with
                            helpful help text)
             └─ AC.SDPD.2 (when flag provided, `check_acs_verified`
                            reads the named plan-doc; RED with hint on
                            missing path; GREEN behaviour preserved
                            when flag absent)
             └─ AC.SDPD.3 (when flag provided, `check_hard_smoke` reads
                            `docs/experiments/<plan-doc-stem>-hard-smoke.md`;
                            stem extraction via `Path.stem`)
             └─ AC.SDPD.4 (outcome-altitude dogfood — run release CLI
                            against the live paper-publish artefacts;
                            verify `acs-verified` + `hard-smoke` gates
                            return what they should against real
                            scope-descriptive inputs)
             └─ AC.SDPD.S (seal-diff discipline — changes only under
                            named fence)
```

**Primary-persona test:** the flag reduces translation burden by removing a hard step (rename the plan-doc to version-named just before publish, then rename back / not at all). Before this PATCH, the persona had to either: (a) rename `docs/plans/odd-paper-methodology-publish.md` → `docs/plans/v0-9-0-odd-paper-methodology-publish.md` immediately before publish (then leave it renamed, breaking the new convention), or (b) document the publish step as "manual fallback only for scope-descriptive plan-docs" (operating fork). The flag lets the persona name the plan-doc once and use it directly through the release flow.

**Harness test:** the flag adds an option to the toolkit the primary persona draws from. `loam release <version> --plan-doc <path>` is a strict superset of `loam release <version>`: every existing invocation continues to work; new convention has a clean path through.

## §3 — Component fence

**Single-component PATCH.** Touched component: `framework/tools/loam/` (release CLI runner + gates + tests).

**PRIMARY (source edits):**
- `framework/tools/loam/src/loam_cli/release/gates.py`:
  - Add optional `plan_doc: Path | None = None` parameter to `_find_plan_doc` (when provided + path exists, return it; when provided + path missing, return `None` with caller responsible for the hint; when absent, fall back to version-slug glob).
  - Add optional `plan_doc: Path | None = None` parameter to `check_acs_verified` (forwarded to `_find_plan_doc`; on missing-provided-path, return RED with hint naming the path).
  - Add optional `plan_doc: Path | None = None` parameter to `check_hard_smoke` (when provided, construct `repo_root / "docs" / "experiments" / f"{plan_doc.stem}-hard-smoke.md"`; when absent, fall back to `<version-slug>-hard-smoke.md`).
  - `ALL_GATES` tuple unchanged (function signatures stay compatible because new parameters are keyword-only with defaults); `run_all(repo_root, version, plan_doc=None)` accepts the optional forwarded kwarg and routes it to the two relevant gates only.
- `framework/tools/loam/src/loam_cli/release/runner.py`:
  - `run(repo_root, version, *, dry_run=False, create_release=False, plan_doc=None)` — accept the new keyword; forward to `gates.run_all(repo_root, version, plan_doc=plan_doc)`.
- `framework/tools/loam/src/loam_cli/release/cli.py`:
  - Add `--plan-doc <path>` argument (`type=Path`, default `None`) to the release subcommand. Help text: "explicit plan-doc path (for scope-descriptive-slug plan-docs that don't follow the version-glob convention). When omitted, the gate infers the path from the version slug."
  - `dispatch` passes `plan_doc=args.plan_doc` to `runner.run`.

**PRIMARY (tests):**
- `framework/tools/loam/tests/test_AC_SDPD_plan_doc_flag.py` — new file. At least 4 tests (one per AC.SDPD.{1,2,3,4-like}):
  - `test_plan_doc_flag_accepted_by_argparse` — invoke the release parser with `--plan-doc /tmp/x.md`; assert `args.plan_doc == Path('/tmp/x.md')` + `--help` output contains "scope-descriptive" or "plan-doc" prose.
  - `test_acs_verified_reads_named_plan_doc_when_flag_provided` — create a scope-descriptive plan-doc in the staged repo (e.g., `docs/plans/scope-descriptive-slug.md` with §4 + §13 GREEN matrix); invoke `check_acs_verified(repo_root, version, plan_doc=path)`; assert GREEN.
  - `test_acs_verified_red_with_hint_when_provided_plan_doc_missing` — invoke with a path that doesn't exist; assert RED + hint contains the missing path string.
  - `test_hard_smoke_reads_stem_derived_path_when_flag_provided` — create `docs/experiments/scope-descriptive-slug-hard-smoke.md` (GREEN); invoke with `plan_doc=docs/plans/scope-descriptive-slug.md`; assert GREEN. Also test the negative: when `plan_doc` set but corresponding `<stem>-hard-smoke.md` missing, RED with hint naming the stem-derived path.

**PRIMARY (admin docs):**
- `docs/STATE.md` — v0.8.2 SHIPPED LOCAL row at end-of-build.
- `docs/release-roadmap.md` — v0.8.2 §2 row (under v0.9.0 — chronological order; v0.9.0 is sealed-local-pending-publish, v0.8.2 built after).
- `docs/experiments/v0-8-2-hard-smoke.md` — HARD smoke writeup (per AC.SDPD.4 dogfood probe + general HARD smoke). Note: this build's smoke writeup uses the **version-named convention** (`v0-8-2-hard-smoke.md`) because the gates haven't been patched against this PATCH's own version yet — the gate will look for the version-named writeup. Future post-v0.8.2 builds following scope-descriptive naming use the new convention.

**Universal-admission docs:**
- `docs/plans/v0-8-2-release-cli-scope-descriptive-plan-doc-support.md` (this file).
- `docs/plans/v0-8-2-release-cli-scope-descriptive-plan-doc-support.manifest.yaml`.
- `docs/FUTURE_IDEAS_DRAFT.md` — only if new FIDRAFT entries surface.

**Untouched:**
- `docs/release-process.md` (the runbook reads correctly with the new flag — flag is optional, default unchanged); FIDRAFT entry candidate if a doc update is warranted post-build.
- `docs/release-versioning-policy.md` — policy unchanged; this PATCH ships against it.
- All other framework/plugin components.
- pyproject.toml versions stay at 0.8.0 (v0.8.2 is PATCH; PATCHes ride predecessor MINOR per AC.HONEST.1 / D-NFCLEAN.4 precedent established in v0.8.1).
- Paper-publish artefacts (`docs/papers/`, paper plan-doc, paper experiments writeup) — out of scope.

## §4 — Acceptance criteria

Four primary ACs plus seal-diff. AC IDs use scope-descriptive `AC.SDPD.*` family (Scope-Descriptive Plan-Doc) per `feedback_scope_descriptive_ac_ids`.

### AC.SDPD.1 — `--plan-doc` flag accepted by `loam release` argparse

**What:** The `release` subcommand's argparse parser accepts `--plan-doc <path>` (with `type=Path`, default `None`). `loam release --help` output mentions the flag with help text describing the scope-descriptive use case.

**Acceptance:**
- The release subparser built by `build_release_subcommand` declares `--plan-doc` with `type=Path` + a help string referencing scope-descriptive plan-docs.
- Invoking the parser with `["release", "v0.8.2", "--plan-doc", "/tmp/x.md"]` produces `args.plan_doc == Path("/tmp/x.md")`.
- Invoking the parser without `--plan-doc` produces `args.plan_doc is None`.
- `loam release --help` output contains the substring `--plan-doc` AND a help-prose mention of "scope-descriptive" or "plan-doc" (verified by capturing stderr / stdout from `argparse.ArgumentParser.format_help()`).

`outcome-altitude: false` — implementation-altitude AC (argparse wiring verified by test invocation).

### AC.SDPD.2 — `check_acs_verified` reads the named plan-doc when `--plan-doc` is provided

**What:** When `check_acs_verified(repo_root, version, plan_doc=path)` is invoked with `plan_doc` set:
- If `path` is a real file, the gate reads it as the plan-doc (skips the version-slug glob lookup entirely).
- If `path` does not exist, the gate returns RED with a hint naming the missing path explicitly (not the version-slug-glob default).
- If `plan_doc=None` (or omitted), pre-PATCH behaviour is preserved — version-slug glob through `_find_plan_doc(repo_root, version)`.

**Acceptance:**
- Three new tests in `test_AC_SDPD_plan_doc_flag.py`:
  - `test_acs_verified_reads_named_plan_doc_when_flag_provided` — create `docs/plans/scope-descriptive-slug.md` (with §4 + §13 GREEN matrix on a single AC); invoke gate with `plan_doc=<that path>` + arbitrary version (e.g., `v9.9.9` that has no version-glob match); assert GREEN.
  - `test_acs_verified_red_with_hint_when_provided_plan_doc_missing` — invoke with `plan_doc=Path("docs/plans/does-not-exist.md")`; assert RED + `r.message` contains `"does-not-exist.md"` AND `"plan-doc"` substring.
  - Backward-compat: existing `test_acs_verified_green_when_status_marks_each_ac_green` (and other tests in `test_AC_V060_2_pre_publish_gates.py`) continue to pass without modification — the flag defaults to `None` and the old code path fires.

`outcome-altitude: false` — implementation-altitude (gate behaviour verified by test).

### AC.SDPD.3 — `check_hard_smoke` reads `docs/experiments/<plan-doc-stem>-hard-smoke.md` when `--plan-doc` is provided

**What:** When `check_hard_smoke(repo_root, version, plan_doc=path)` is invoked with `plan_doc` set:
- The gate constructs `repo_root / "docs" / "experiments" / f"{path.stem}-hard-smoke.md"` (stem = filename without `.md`).
- If that file exists + contains the `GREEN` token, the gate returns GREEN.
- If the file is missing OR lacks the `GREEN` token, the gate returns RED with hint naming the expected stem-derived path.
- When `plan_doc=None`, pre-PATCH behaviour preserved (version-slug-derived `<version-slug>-hard-smoke.md`).

**Acceptance:**
- One positive test (`test_hard_smoke_reads_stem_derived_path_when_flag_provided`): create `docs/experiments/scope-descriptive-slug-hard-smoke.md` with body containing `GREEN`; invoke `check_hard_smoke(repo_root, "v9.9.9", plan_doc=Path("docs/plans/scope-descriptive-slug.md"))`; assert GREEN.
- One negative test (`test_hard_smoke_red_when_stem_derived_path_missing`): invoke with `plan_doc=Path("docs/plans/nonexistent-slug.md")`; assert RED + hint mentions `"nonexistent-slug-hard-smoke.md"`.
- Backward-compat: existing hard-smoke tests in `test_AC_V060_2_pre_publish_gates.py` continue to pass.

`outcome-altitude: false` — implementation-altitude (gate behaviour verified by test).

### AC.SDPD.4 — Outcome-altitude dogfood: real release CLI against live paper-publish artefacts

**What:** Run `loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run` from `/Users/lukeivers/loam/` against the live paper-publish artefacts that already exist on HEAD:
- Plan-doc at `docs/plans/odd-paper-methodology-publish.md` (v0.9.0 SHIPPED LOCAL plan-doc; sealed `4a4535f`).
- HARD smoke writeup at `docs/experiments/odd-paper-methodology-publish-hard-smoke.md` (already GREEN-marked).

The probe is the production entry-point invoked with realistic inputs — not a synthetic stub. Per `feedback_test_outcome_altitude_required`, at least one AC must verify against the real production surface; AC.SDPD.4 is that AC.

**Acceptance:**
- `loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run` (invoked from the canonical loam working tree, post-source-edit + post-apply + post-seal) **resolves the `hard-smoke` gate to GREEN** — the patch reads `docs/experiments/odd-paper-methodology-publish-hard-smoke.md`, which exists and contains the `GREEN` token. Verbatim gate output recorded in `docs/experiments/v0-8-2-hard-smoke.md`.
- The `acs-verified` gate's read-target shifts from "no plan-doc found" RED to "actually reads `docs/plans/odd-paper-methodology-publish.md`" — verified by the gate's verdict message naming the paper plan-doc path. **NOTE:** the paper plan-doc's §13 marks `AC.ODDPAPER.3` as `REMOVED` (not GREEN). Per the current gate logic (`AC.<...>.<x>` within 240 chars of `GREEN`), the gate will return RED for `AC.ODDPAPER.3` because no GREEN token is within 240 chars of that AC ID. **This is a separate, known defect of the gate's §status verdict-matrix parsing — REMOVED is a valid build-time verdict but the gate doesn't recognize it.** Out of scope for v0.8.2 per dispatch brief HARD HALT #2 ("if AC.SDPD.4 dogfood probe surfaces gates other than `acs-verified` + `hard-smoke` failing, surface them but DO NOT extend scope"). Surface as F-REMOVED-VERDICT-GATE FIDRAFT entry. The AC.SDPD.4 dogfood verdict is **GREEN** for the targeted-gate behaviour (reads the correct plan-doc) even if the `acs-verified` gate's overall verdict is RED on the unrelated REMOVED-verdict issue.
- Other gates' verdicts (state-shipped, clean-tree, branch-main, seal-reachable) are reported but NOT in-scope for this PATCH's AC.SDPD.4. Verbatim output preserved in the smoke writeup.

`outcome-altitude: true` — outcome-altitude AC (real production entry-point against real artefacts).

### AC.SDPD.S — Seal-diff discipline

**What:** `git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under the AC.SDPD.{1,2,3,4}-allowed paths.

**Acceptance:**
- All paths in the diff are members of:
  - `framework/tools/loam/src/loam_cli/release/` (gates.py + runner.py + cli.py)
  - `framework/tools/loam/tests/` (new `test_AC_SDPD_*.py`)
  - Universal-admission docs (`docs/plans/v0-8-2-*`, `docs/experiments/v0-8-2-*`, `docs/STATE.md`, `docs/release-roadmap.md`, `docs/FUTURE_IDEAS_DRAFT.md` if FIDRAFT entries land).
- No source code changes outside the three release-CLI source files + new test file.
- No pyproject.toml version bumps (PATCH stays at 0.8.0 per D-SDPD.4).

## §5 — Decisions builder rules at build time

- **D-SDPD.1.a (parameter shape on gate functions):** add `plan_doc: Path | None = None` as a keyword-only optional parameter on `check_acs_verified` + `check_hard_smoke` + `_find_plan_doc` + `run_all`. Keyword-only because new parameter; positional would risk silently shifting existing tests' arg order.
- **D-SDPD.1.b (default behaviour when `plan_doc=None`):** preserve verbatim. The version-slug glob path is the production default; any change to that path is out of scope (would be a separate AC). Test backward-compat verified by existing test suite continuing to pass.
- **D-SDPD.2.a (RED-with-hint when provided-plan-doc-missing):** the hint must name the missing path explicitly (`f"plan-doc not found at {plan_doc}"`) AND reference the flag (`"--plan-doc"`) so the operator knows why this path was read instead of the version-glob default. Hint structure mirrors existing `check_acs_verified` "no plan-doc found" hint.
- **D-SDPD.3.a (stem extraction):** use `Path.stem` (Python stdlib; strips the final `.md` extension). The plan-doc path may carry a subdirectory prefix (`docs/plans/foo.md`); `.stem` returns just `foo`. The hard-smoke writeup is constructed as `repo_root / "docs" / "experiments" / f"{stem}-hard-smoke.md"` — the experiments directory is fixed (the convention isn't changing where smoke writeups land, just how their filename derives).
- **D-SDPD.3.b (RED-with-hint when stem-derived path missing):** the hint must name the stem-derived path explicitly + the `--plan-doc` flag's role (operator might have expected version-slug-derived path; the hint clarifies).
- **D-SDPD.4.a (CLI argparse flag shape):** `--plan-doc <path>` with `type=Path`, `default=None`, `metavar="<path>"`. Help text describes the scope-descriptive use case + when to use the flag. Per `feedback_summarize_and_surface_decisions`, the help text reads as actionable English not internal jargon.
- **D-SDPD.4.b (runner.run signature):** add `plan_doc: Path | None = None` as keyword-only optional parameter (matches the gate-function pattern). Forward to `gates.run_all(repo_root, version, plan_doc=plan_doc)`.
- **D-SDPD.5 (smoke writeup convention for v0.8.2's own publish):** use the version-named convention (`docs/experiments/v0-8-2-hard-smoke.md`) for THIS build's HARD smoke writeup. Rationale: v0.8.2's own `loam release v0.8.2 --dry-run` invocation will pass `--plan-doc` flag pointing at this PATCH's version-named plan-doc; with the flag, the gate looks for `<plan-doc-stem>-hard-smoke.md` = `v0-8-2-release-cli-scope-descriptive-plan-doc-support-hard-smoke.md`. That's a longer name and inconsistent with how v0.8.2 will be published (manually, with the flag OR without). The cleanest path is: keep this build's smoke writeup at the version-named path so a publish-without-flag invocation works; the AC.SDPD.4 dogfood happens against the paper publish's artefact (which uses the new convention), not against v0.8.2's own (which uses the old convention because the patch is shipped against its own predecessor's convention).
- **D-SDPD.6 (where in `gates.py` to thread the new parameter through):** the `ALL_GATES` tuple stays a tuple of callables with the original `(repo_root, version)` signature for backward-compat. `run_all` accepts the new `plan_doc` kwarg and routes it to the two affected gates explicitly via per-gate calls (not iteration over the tuple). The tuple-of-callables shape was for the v0.6.0 "six gates iterated uniformly" outcome; v0.8.2's new parameter breaks that uniformity for two gates only. Documented in code with a comment.
- **D-SDPD.7 (FIDRAFT entries):** if AC.SDPD.4 surfaces the REMOVED-verdict issue (it will), capture as `F-REMOVED-VERDICT-GATE` in `docs/FUTURE_IDEAS_DRAFT.md` per `feedback_durable_capture_for_planned_work`. No other FIDRAFTs expected from this build's scope.

## §6 — Out of scope (explicit)

- **REMOVED-verdict gate parser fix.** The `acs-verified` gate's §status verdict-matrix parser only recognizes `GREEN` as a pass token. AC IDs marked `REMOVED` at build-time (legitimate per ODD §4 re-extension) trigger false-positive RED. Out of scope; FIDRAFT `F-REMOVED-VERDICT-GATE`.
- **Renaming any existing version-named plan-doc to scope-descriptive form.** Backward-compat is preserved by keeping the glob path live; historical plan-docs stay named as-is per `feedback_scope_descriptive_ac_ids` historical-row preservation clause.
- **Updating `docs/release-process.md` runbook.** The flag is optional + default unchanged; the runbook continues to read correctly without the new flag documented. If the doc update is warranted post-build (e.g., for the paper-publish's release walkthrough), captured at FIDRAFT for next docs cycle.
- **Restructuring `_find_plan_doc` / `_extract_section_4_body` semantics beyond the parameter addition.** Per HARD HALT #1 below, any significant refactor (>2x current line count) halts and surfaces.
- **`Pre-publish state-update enforcement gate`** — v0.8.x or v0.9.0 work; FIDRAFT entry F-NFCLEAN-FOLLOWON precedent.
- **Anthropic API key paths** (per `feedback_no_anthropic_api_key`, never).

## §7 — HARD HALTs (build-time)

Halt-and-surface to dispatcher — do NOT proceed past — on any of:

1. `_find_plan_doc` or `_extract_section_4_body` semantics need significant refactoring (>2x current line count). That's a bigger change than v0.8.2's PATCH scope; surface and route to v0.8.x or v0.9.0.
2. AC.SDPD.4 dogfood probe surfaces gates other than `acs-verified` + `hard-smoke` failing. Surface them but DO NOT extend scope to fix them — separate concerns (e.g., paper publish's `state-shipped` gate already passed at last dry-run; that should still hold).
3. ODD §2.5 violation in your work OR surrounding code (per `feedback_subagent_odd_violation_halt`).
4. Wrong-tree-write (any edit lands at a path outside `/Users/lukeivers/loam/`).
5. Any reach for ASK-FIRST class actions: `cd` outside `/Users/lukeivers/loam/`, `git push`, `git tag`, `git commit --amend` (per `feedback_no_amend_in_agent_dispatches`). Immediate halt.
6. Wall-clock exceeds upper band (60-120 min midpoint ~75 min per §9) by >2× → 4 hr (matches dispatch brief's surface threshold). Halt with current state.
7. Discovery that the flag-addition breaks any existing test in `test_AC_V060_*` (regression). Halt + surface.
8. Any reach for an Anthropic API key path (per `feedback_no_anthropic_api_key`). Immediate halt.
9. Untracked file at `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` blocks `loam amend seal` dirty-tree check. Stash + re-run seal per dispatch-brief precedent.

## §8 — Dependencies

- **v0.6.0 (release process)** — HARD. v0.8.2 patches the gates that v0.6.0 introduced.
- **v0.7.2 (release CLI parser fix)** — SOFT. AC.SDPD.2 patches the `check_acs_verified` gate v0.7.2 last touched.
- **v0.8.1 (honesty-cleanup follow-on)** — HARD. v0.8.2 is the PATCH immediately following v0.8.1; PATCH numbering derives `next_PATCH(v0.8.1) = v0.8.2`.
- **v0.9.0 (paper publish, SHIPPED LOCAL)** — SOFT. v0.8.2's HEAD includes v0.9.0's seal commit; AC.SDPD.4 dogfood probe runs against v0.9.0's artefacts. v0.9.0's publish is owner-gated and not blocked by v0.8.2.
- **`docs/release-versioning-policy.md`** — SOFT. PATCH-class declaration grounded in the policy.
- **`feedback_version_numbers_at_release_time`** — HARD. The convention this PATCH unblocks.
- **`feedback_scope_descriptive_ac_ids`** — SOFT. Drives the `SDPD` AC ID family choice.
- **`feedback_build_forward_on_publish_pending`** — SOFT. v0.9.0 SHIPPED LOCAL; v0.8.2 dispatched in flight.
- **`feedback_no_amend_in_agent_dispatches`** — HARD. Post-fix commits are NEW commits, never `--amend`.
- **`feedback_test_outcome_altitude_required`** — HARD. AC.SDPD.4 satisfies the requirement.
- **No external service dependencies.**
- **No new Python packages.**

## §9 — Estimated AI-time

Per `feedback_duration_estimation_rubric` — single-component PATCH; tight per-AC scope; extending three existing modules (gates.py + runner.py + cli.py) with optional-parameter additions + one new test file with 4 tests. Defect-closure shape; confidence in outcome shape is high (Lens 4 — tight scope appropriate). v0.7.2 release-CLI-parser-fix actuals calibrate the upper bound; v0.8.2 has comparable scope.

| Stage | Band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring (this file) | 10-15 min | 12 min |
| AC.SDPD.{1,2,3} — gates.py + runner.py + cli.py edits | 12-18 min | 15 min |
| AC.SDPD.{1,2,3} — 4 new tests at `test_AC_SDPD_*.py` | 10-15 min | 12 min |
| AC.SDPD.4 — dogfood probe + HARD smoke writeup | 8-12 min | 10 min |
| FIDRAFT capture (F-REMOVED-VERDICT-GATE) | 2-3 min | 2 min |
| Plan-doc §13 backfill + STATE/roadmap admin + manifest apply + seal | 10-15 min | 12 min |
| **Total v0.8.2 build** | **52-78 min (~0.9-1.3 hr)** | **~63 min (~1.05 hr)** |

Dispatch brief estimates 60-75 min midpoint. Plan-time revision: **52-78 min midpoint ~63 min**. Defensible: 3-file optional-parameter addition + 4 tests + outcome-altitude dogfood is smaller than v0.7.2's similar-shape PATCH (~50 min). Midpoint sits well below the 4-hr HARD HALT threshold.

Owner gate-review separate (publish per ASK-FIRST after seal).

## §11 — Authority chain

- Current dispatch brief (2026-05-13) — scope ratification + AI-time band + AC family declaration + AC IDs + universal-admission docs list. The dispatch authority for v0.8.2.
- `feedback_version_numbers_at_release_time.md` (captured 2026-05-13) — the convention this PATCH closes the gap for.
- `feedback_scope_descriptive_ac_ids.md` — AC ID family scope-descriptive (`AC.SDPD.*` not `AC.V082.*`).
- `feedback_build_forward_on_publish_pending.md` — v0.9.0 publish-pending; v0.8.2 build-forward.
- `docs/release-versioning-policy.md` — PATCH-class declaration ground.
- `framework/tools/loam/src/loam_cli/release/gates.py` (sealed at v0.6.0 + patched at v0.7.2 + v0.8.1) — the surface AC.SDPD.{1,2,3} edits.
- `framework/tools/loam/src/loam_cli/release/runner.py` (sealed at v0.6.0) — the orchestration layer that forwards the new parameter.
- `framework/tools/loam/src/loam_cli/release/cli.py` (sealed at v0.6.0) — the argparse layer that introduces the flag.
- `framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py` — the existing test suite preserved as backward-compat anchor.
- `docs/plans/odd-paper-methodology-publish.md` (v0.9.0 SHIPPED LOCAL plan-doc) — the live artefact AC.SDPD.4 dogfood probes against.
- `docs/experiments/odd-paper-methodology-publish-hard-smoke.md` — the live HARD smoke writeup AC.SDPD.4 dogfood probes against.
- Memory rules: `feedback_plan_before_code.md` (this plan-doc IS the gate), `feedback_no_amend_in_agent_dispatches.md` (HARD HALT #5), `feedback_no_anthropic_api_key.md` (HARD HALT #8), `feedback_subagent_odd_violation_halt.md` (HARD HALT #3), `feedback_duration_estimation_rubric.md` (§9), `feedback_test_outcome_altitude_required.md` (AC.SDPD.4 risk-band), `feedback_locked_design_not_license_for_bad_outcomes.md` (the version-slug-glob convention was correct at v0.6.0; the new convention requires this PATCH rather than living with broken gates for scope-descriptive plan-docs).

## §13 — §status

**Build cycle:** SHIPPED LOCAL 2026-05-13 — owner pre-ratified scope (dispatcher brief 2026-05-13). Awaiting dispatcher dogfood publish per ASK-FIRST.

**Plan-doc commits:** plan-doc + manifest `2832ed2`; source-edit batch (gates.py + runner.py + cli.py + 11 tests + smoke writeup + FIDRAFT entry + STATE/roadmap admin) `6bbac04`; manifest baseline backfill `29e9a00`; apply auto-commit (BASELINE + sidecar bump to `6bbac04`) `46e02dd`; seal commit (deterministic seal) `a54295f`.

### AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.SDPD.1 — `--plan-doc` flag accepted by `loam release` argparse | GREEN | `test_release_parser_accepts_plan_doc_flag` + `test_release_help_mentions_plan_doc_and_scope_descriptive` GREEN. `release_parser.format_help()` output contains `--plan-doc` substring + "scope-descriptive" prose mention. Parser accepts `["release", "v0.8.2", "--plan-doc", "/tmp/x.md"]` → `args.plan_doc == Path("/tmp/x.md")`. Default `None` when flag absent. Source-edit commit `6bbac04`. |
| AC.SDPD.2 — `check_acs_verified` reads named plan-doc when flag set | GREEN | 3 tests GREEN: `test_acs_verified_reads_named_plan_doc_when_flag_provided` (positive: reads scope-descriptive plan-doc; ignores version-glob match), `test_acs_verified_red_with_hint_when_provided_plan_doc_missing` (negative: RED hint names the missing path + `--plan-doc` flag), `test_acs_verified_accepts_relative_plan_doc_path` (relative paths resolved against repo_root per D-SDPD.1.a). AC.SDPD.4 dogfood at sealed state confirms outcome-altitude: `loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run` returns `acs-verified` message naming `docs/plans/odd-paper-methodology-publish.md` (not "no plan-doc found at v0-9-0-*.md"). Backward-compat verified: 21 existing tests in `test_AC_V060_2_pre_publish_gates.py` pass unmodified. Source-edit commit `6bbac04`. |
| AC.SDPD.3 — `check_hard_smoke` reads stem-derived path when flag set | GREEN | 3 tests GREEN: `test_hard_smoke_reads_stem_derived_path_when_flag_provided` (positive: reads `<stem>-hard-smoke.md` correctly), `test_hard_smoke_red_when_stem_derived_path_missing` (negative: RED hint names the stem-derived path), `test_hard_smoke_uses_plan_doc_stem_not_version_slug_when_both_paths_exist` (precedence: stem-derived wins over version-slug when both exist). AC.SDPD.4 dogfood at sealed state confirms outcome-altitude: `hard-smoke` gate flipped from pre-PATCH RED ("missing docs/experiments/v0-9-0-hard-smoke.md") → post-PATCH GREEN ("HARD smoke GREEN at docs/experiments/odd-paper-methodology-publish-hard-smoke.md"). Source-edit commit `6bbac04`. |
| AC.SDPD.4 — Outcome-altitude dogfood probe | GREEN | Real production entry-point `loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run` invoked from `/Users/lukeivers/loam/` at sealed state. Verbatim output (post-seal): `[GREEN] hard-smoke: HARD smoke GREEN at docs/experiments/odd-paper-methodology-publish-hard-smoke.md` + `[GREEN] state-shipped: v0.9.0 marked SHIPPED in docs/STATE.md` + `[GREEN] clean-tree: working tree clean` + `[GREEN] branch-main: on branch main` + `[GREEN] seal-reachable: seal 4a4535f reachable from HEAD`. The `acs-verified` gate verdict line reads `[RED] acs-verified: plan-doc docs/plans/odd-paper-methodology-publish.md §status does not mark these ACs GREEN: AC.ODDPAPER.3.` — RED for the orthogonal REMOVED-verdict-parser issue (the gate reads the correct plan-doc; AC.ODDPAPER.3 is marked REMOVED at build-time per D-ODDPAPER.5.2 Path C, not GREEN). Captured at FIDRAFT F-REMOVED-VERDICT-GATE; out of scope for v0.8.2 per HARD HALT #2. The AC.SDPD.4 targeted-gate behaviour (gates read scope-descriptive paths) is verified GREEN. Probe writeup at `docs/experiments/v0-8-2-hard-smoke.md` §1 Stages 1-4 documents per-stage verification. |
| AC.SDPD.S — Seal-diff discipline | GREEN | `git diff --name-only 2832ed2..a54295f` shows changes only under: `framework/tools/loam/src/loam_cli/release/gates.py` (AC.SDPD.{2,3} edits — `_find_plan_doc` + `check_acs_verified` + `check_hard_smoke` + `run_all` parameter additions + `_display_path` helper); `framework/tools/loam/src/loam_cli/release/runner.py` (AC.SDPD parameter forwarding); `framework/tools/loam/src/loam_cli/release/cli.py` (AC.SDPD.1 argparse flag); `framework/tools/loam/tests/test_AC_SDPD_plan_doc_flag.py` (11 new tests); `docs/experiments/v0-8-2-hard-smoke.md` (smoke writeup); `docs/STATE.md` (v0.8.2 universal-admission row); `docs/release-roadmap.md` (v0.8.2 §2 row + Total-shipped count auto-corrected at next publish); `docs/FUTURE_IDEAS_DRAFT.md` (F-REMOVED-VERDICT-GATE FIDRAFT entry); `docs/plans/v0-8-2-release-cli-scope-descriptive-plan-doc-support.md` (this file); `docs/plans/v0-8-2-release-cli-scope-descriptive-plan-doc-support.manifest.yaml`; `plugins/dev-sdlc/seals/SEAL_COMMIT.v0-8-2-release-cli-scope-descriptive-plan-doc-support` + `plugins/dev-sdlc/tests/SEAL_COMMIT` sidecar (apply + seal auto-commits). All paths in AC.SDPD.S allow-list (`framework/tools/loam/` PRIMARY + universal-admission docs + auto-managed seal sidecar). No source-code changes outside the 3 release-CLI source files + 1 new test file. No pyproject.toml version bumps. |

### AI-time actuals

| Stage | Estimated (plan §9) | Actual |
|---|---|---|
| Plan-doc + manifest authoring | 10-15 min | ~14 min |
| AC.SDPD.{1,2,3} — gates.py + runner.py + cli.py edits | 12-18 min | ~12 min |
| AC.SDPD.{1,2,3} — 11 new tests at `test_AC_SDPD_plan_doc_flag.py` | 10-15 min | ~9 min |
| AC.SDPD.4 — dogfood probe + HARD smoke writeup | 8-12 min | ~7 min |
| FIDRAFT capture (F-REMOVED-VERDICT-GATE) | 2-3 min | ~2 min |
| Plan-doc §13 backfill + STATE/roadmap admin + manifest apply + seal | 10-15 min | ~5 min (admin docs landed in source-edit batch; backfill + apply + seal only) |
| **Total v0.8.2 build** | **52-78 min midpoint ~63 min** | **~49 min** |

In-band — toward the lower end of the estimate. The optional-parameter additions through three modules were mechanical; the new tests reused the existing `staged_repo` fixture cleanly; the AC.SDPD.4 dogfood was a single CLI invocation against existing artefacts. Forward calibration: single-component PATCH cycles that add optional parameters to existing gate functions + new tests compress to ~45-55 min vs new-helper PATCHes (~75-90 min, v0.7.4 actuals).

### Halt-and-surface findings

**F-REMOVED-VERDICT-GATE (FIDRAFT capture; out of scope for v0.8.2).** AC.SDPD.4 dogfood probe surfaced an orthogonal `acs-verified` gate parser defect: the verdict-matrix regex (`re.escape(ac) + r".{0,240}?GREEN"`) recognises only `GREEN` as a pass token. ACs marked `REMOVED` at build-time per legitimate ODD §4 re-extension (e.g., paper publish's AC.ODDPAPER.3, struck via D-ODDPAPER.5.2 Path C) trigger false-positive RED. Per HARD HALT #2 dispatch-brief ruling, surfaced but NOT extended scope; captured at `docs/FUTURE_IDEAS_DRAFT.md` as `F-REMOVED-VERDICT-GATE`. Proposed shape: extend the proximity-pattern to accept `(GREEN | REMOVED.{0,160}?D-<plan-id>.<n> | DEFERRED.{0,160}?F-<FIDRAFT-id>)`. Activation gate: v0.8.3+ release-CLI cycle OR triggered by paper publish needing to ship through `loam release` rather than manual fallback.

**No other halt-and-surface findings.** 82/82 release-CLI tests GREEN at sealed state; backward-compat preserved (21 existing v0.6.0/v0.7.2 tests pass unmodified); AC.SDPD.4 dogfood verified the patch closes the defect that motivated it (hard-smoke gate flipped from RED → GREEN against the paper publish artefacts). Seal-diff discipline verified clean (only the 3 release-CLI source files + 1 new test file + universal-admission docs + seal-sidecar touched).

## §14 — Method decisions

The plan-doc's §5 names the build-time decisions (D-SDPD.1.a parameter shape, D-SDPD.1.b default behaviour, D-SDPD.2.a hint shape, D-SDPD.3.a stem extraction, D-SDPD.3.b hint shape, D-SDPD.4.a CLI flag shape, D-SDPD.4.b runner signature, D-SDPD.5 smoke writeup convention, D-SDPD.6 ALL_GATES tuple, D-SDPD.7 FIDRAFT entries). All builder rulings landed as planned with one minor in-cycle addition (the `_display_path` helper to handle absolute-path explicit `--plan-doc` arguments — bounded ~10 LOC; preserves the existing relative-path display behaviour for the version-glob default).

### Commit SHAs

- Plan-doc + manifest authoring: `2832ed2`
- Source-edit batch (gates.py + runner.py + cli.py + 11 tests + smoke writeup + FIDRAFT entry + STATE/roadmap admin): `6bbac04`
- Manifest baseline backfill: `29e9a00`
- Apply auto-commit (BASELINE + sidecar bump to `6bbac04`): `46e02dd`
- Seal commit (deterministic seal): `a54295f`

### Build-time decision deviations

- **`_display_path` helper added in-cycle.** Not named in §5 D-SDPD.* decisions but bounded ~10 LOC; handles the absolute-path case for explicit `--plan-doc` arguments outside `repo_root` (where `Path.relative_to(repo_root)` would raise `ValueError`). The helper is internal-only; preserves the existing relative-path display behaviour for the version-glob default. Within HARD HALT #1 envelope (not >2x current line count).
- All other D-SDPD.* rulings landed as planned.
