# v0.3.0.1 PATCH — workflow chain UX + doc gap-fill

**Cycle class:** PATCH (defect against shipped v0.3.0). Single-cycle.
Bookkeeping owner: `dev-sdlc` (cross-cutting; same precedent as v0.3.0
C1–C7).

**Predecessor:** v0.3.0 SHIP at `3c6fdd5e`. v0.4.0 master plan in
flight (untouched by this patch).

**Authority chain:**
- Investigation report at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-extract-dropoff-investigation.md` — root cause + recommended fix paths + version-fit ratification (v0.3.0.1 PATCH selected).
- Eric real-user feedback (Telegram 10375): "it didn't naturally progress to the interview, the gap analysis, the build next, etc. it stopped after generating the objectives."
- Dispatcher brief: v0.3.0.1 PATCH directive. This plan-doc + brief + investigation report together constitute the cycle's authoritative spec.

---

## §1 — Objective

Close the empirical user-experience drop-off observed after `loam
odd-extract` completes by:

1. (Path A) Adding stdout next-step hints to every chain stage.
2. (Path B) Documenting the workflow chain in user-facing docs +
   the onboarding ritual.
3. (Bundle b) Surfacing a `--live` hint when default-dry-run produces
   zero ACs.

Path C (SKILL persona-pull) is **deferred to v0.4.0 plan-time**
pending post-A+B observation per
`feedback_locked_design_not_license_for_bad_outcomes` (revisit on
new data, not first failure).

Bundle item (a) — `loam project new` / `loam project advance`
register-vs-strip — closed empirically as **already-registered via
entry-point group `loam.cli.subcommands`**; the current user-side
gap is plugin-not-installed-locally, not a design honesty miss.
Documented in §6 halt-and-surface; no code change required for
AC.V031.7.

Bundle item (c) — design-intent-vs-user-outcome audit altitude
gap — **deferred to v0.4.0 master plan §6 methodology
amendments** per the dispatcher brief (NOT this patch).

---

## §2 — Constraints

- ODD §2.5: every line of code maps to a named AC; no defensive
  branches for unnamed cases.
- No `--amend`. NEW corrective commits only if a miss is found.
- No `git push`, no `git tag v0.3.0.1`, no `gh release create` —
  all three are owner-action-separate per release-versioning
  policy.
- Subscription-only architecture preserved (no Anthropic SDK
  surface change).
- Sonnet (token-efficient).
- Strict autonomy: plan ratified by investigation + dispatcher
  brief; execution proceeds without per-step ratification.

---

## §3 — Architectural shape

**Path A — stdout next-step hints.** Each of four success-paths in
`plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py` gains
ONE additional `print()` call appending a chain-pointer line.
Strictly additive; no abstractions; no flow change. The four
locations (verified empirically against HEAD):

| Stage                        | cli.py line | Next-step pointer                                                |
|------------------------------|------------:|------------------------------------------------------------------|
| `--verify` (default)         |        ~237 | run `loam odd-extract <repo> --interview` to confirm objectives. |
| `--interview`                |        ~509 | run `loam odd-extract <repo> --gaps` to find unbacked objectives.|
| `--gaps`                     |        ~646 | run `loam odd-extract <repo> --build-next` for ranked candidates.|
| `--build-next`               |        ~819 | implement, then re-run the chain to refine objectives.           |

JSON paths (`if args.json:`) are NOT modified — JSON output is
machine-consumed and the hint is human-targeted.

**Path B — doc gap-fill.** A "Workflow chain" section is appended
to:

- `README.md`
- `docs/getting-started.md` (also extends Q4 of the onboarding
  ritual with a chain-pointer follow-on)
- `docs/dev-mode-getting-started.md`

The Eric onboarding ritual SKILL — at
`docs/getting-started.md` §4½ Q4 — gets the Q4-follow-on naming
the chain (per AC.V031.6).

**Bundle (b) — dry-run AC count hint.** In the `--verify`
success path, after the four existing `print()` lines, when
`args.live is False` and `draft.ac_count == 0`, emit a single
hint line: `(Dry-run mode — pass \`--live\` to invoke synthesis
and produce real ACs.)` Then the Path A next-step line.

---

## §4 — Acceptance Criteria

| AC ID         | Verifiable claim                                                                                                                      | Outcome-altitude |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------|------------------|
| `AC.V031.1`   | `loam odd-extract --verify` (default) success-path stdout contains `Next: run \`loam odd-extract <repo> --interview\``.                | impl             |
| `AC.V031.2`   | `loam odd-extract --interview` success-path stdout contains `Next: run \`loam odd-extract <repo> --gaps\``.                            | impl             |
| `AC.V031.3`   | `loam odd-extract --gaps` success-path stdout contains `Next: run \`loam odd-extract <repo> --build-next\``.                           | impl             |
| `AC.V031.4`   | `loam odd-extract --build-next` success-path stdout contains a chain-closing hint (`implement` + `re-run the chain`).                  | impl             |
| `AC.V031.5`   | README.md, docs/getting-started.md, docs/dev-mode-getting-started.md each contain a "Workflow chain" section heading.                  | impl             |
| `AC.V031.6`   | `docs/getting-started.md` §4½ Q4 follow-on names the chain (extract → interview → gap-analysis → build-next).                          | impl             |
| `AC.V031.7`   | `loam project new` + `loam project advance` are registered via entry-point (verified by reading pyproject.toml + plugin tests).        | impl             |
| `AC.V031.8`   | Default-dry-run with `draft.ac_count == 0` emits a `--live` hint to stdout.                                                            | impl             |
| `AC.V031.9`   | Cold-run extract → interview → gap-analysis → build-next chain on rd-automation produces stdout at every stage that an unprimed user can use to find the next command without docs. Verified by automated stdout-grep test invoking the production CLI entry-points. | **outcome**      |

AC.V031.7 closure note: the verbs already register in
`plugins/dev-sdlc/pyproject.toml` under
`[project.entry-points."loam.cli.subcommands"]` and are exercised
by `plugins/dev-sdlc/tests/test_AC_OSS_M6_6_loam_project_subcommand_registered.py`.
The `start-project.md` SKILL accurately documents them. No code
change required; verified-as-shipped.

---

## §5 — Method (builder's call inside the constraint envelope)

1. **Source edit (BASELINE).** Single feat commit:
   - `cli.py` — four `print()` additions + dry-run hint.
   - `README.md` + `docs/getting-started.md` +
     `docs/dev-mode-getting-started.md` — "Workflow chain" sections.
   - New tests:
     `plugins/dev-sdlc/odd-extractor/tests/test_AC_V031_chain_ux.py`
     covering AC.V031.{1,2,3,4,8,9} via stdout-grep against the
     real CLI entry-points (no mocked subprocess).
2. **Manifest commit.** Schema v3 minimal-component manifest with
   `dev-sdlc` as bookkeeping owner (`frozen_baseline: false` —
   bundle (b) edits cli.py which IS sealed-component code under
   dev-sdlc); broad `universal_paths` for docs.
3. **`loam amend apply`.** Single apply commit.
4. **`loam amend seal --plan-doc <abs-path>`.** Single seal commit
   + post-seal §14 backfill.
5. **Halt before public actions.** No push, no tag, no release.

---

## §6 — Halt-and-surface findings

- **(a) `loam project` already registered.** The dev-sdlc plugin
  registers it correctly via entry-point group
  `loam.cli.subcommands` in pyproject.toml; the tests at
  `plugins/dev-sdlc/tests/test_AC_OSS_M6_6_loam_project_subcommand_registered.py`
  exercise the registration end-to-end. The local environment's
  `loam project --help` returning "invalid choice" reflects a
  plugin-not-installed-locally state, not a registration miss.
  No code action; AC.V031.7 satisfied as-shipped.

- **(c) Audit altitude gap deferred to v0.4.0** per dispatcher
  brief.

---

## 14. Method-decisions (filled at seal time §14 backfill)

Plan-doc uses the AC.D-sa.7-required `## 14.` heading; this PATCH
cycle's plan-doc is intentionally short so prior numbered sections
read as `§1`-`§6`. The §14 record below is the canonical
method-decisions ledger consumed by `loam amend seal --plan-doc`.

### Method decisions (recorded at plan-author time)

1. **Bundle item (a) closure: verify-as-shipped, no code change.**
   Empirical evidence in `plugins/dev-sdlc/pyproject.toml` +
   `plugins/dev-sdlc/tests/test_AC_OSS_M6_6_loam_project_subcommand_registered.py`
   shows `loam project new` / `loam project advance` are registered
   via entry-point group `loam.cli.subcommands` and exercised by an
   AC-altitude test. The local-env "invalid choice" reflects the
   plugin not being pip-installed in the active venv, not a
   registration miss. Decision: AC.V031.7 closes by verification,
   not edit.

2. **Path C deferred per LOCKED-DESIGN-NOT-LICENSE.** v0.2.4 §6.3
   ruled the persona-pull contract was documentation-only. Eric's
   data is the first empirical disproof. Per the principle: revisit
   when outcomes are bad WITH new data — A + B addresses the
   visible symptom; if the persona still doesn't pull after, revisit
   C at v0.4.0 plan-time (when the new code-gen step is added and
   the chain extends to five steps anyway).

3. **Bundle item (c) audit altitude gap deferred.** Brief explicit:
   v0.4.0 master plan §6 methodology amendments. Not in this PATCH.

4. **JSON paths NOT modified.** All four next-step `print()`
   additions land on the human-readable success-paths only;
   `if args.json:` branches are machine-consumed and remain
   stable. (Avoids breaking machine-pipeline consumers.)

5. **`repo_id` interpolated into hint string.** Each next-step
   pointer interpolates the actual `repo_id` so the user can
   copy-paste the exact next command — no placeholder text. The
   stdout-grep test in AC.V031.{1,3,9} checks for the literal
   `repo_id` to enforce this.

6. **`frozen_baseline: false` in manifest.** Bundle (b) edits
   `cli.py` directly — sealed-component code under
   dev-sdlc/odd-extractor. The cycle is NOT doc-only from
   dev-sdlc's perspective (precedent v0.3.0 C1-C7 used
   `frozen_baseline: true` because those WERE doc-only). This is
   the v0.3.0.1 PATCH-shape variant.

7. **Outcome-altitude AC explicit.** AC.V031.9 follows
   `feedback_test_outcome_altitude_required` — a stdout-grep
   regression contract for Eric's "it stopped" report. Eric is
   real-world user data, not a synthetic fixture; the outcome the
   AC verifies is the cold-run user-experience progression.

8. **Plan-doc heading style.** Sections are numbered `§1`-`§6` for
   readability; `## 14.` is the AC.D-sa.7-required heading that
   `loam amend seal --plan-doc` consumes for SHA backfill. The
   numerical gap is intentional — short PATCH cycles don't need
   sections 7-13 of a full feature plan-doc.

### Commit SHAs

| Commit | SHA |
|---|---|
| Source-edit BASELINE (cli.py + tests + 3 user-facing docs + plan-doc) | `a137906c` |
| Manifest commit | `fa294a1f` |
| `loam amend apply` commit | `634b3f1f` |
| `loam amend seal` commit | `8569b727` |
| §14 SHA backfill commit (this) | (this commit) |

