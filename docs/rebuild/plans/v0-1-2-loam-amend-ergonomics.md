# v0.1.2 item 6 sub-plan — loam-amend ergonomics sweep

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-x-roadmap.md` (§2 v0.1.2 item 6 + §8 method-decision register).
**Predecessors:** v0.1.0 shipped; V11.A `9d58062`; V11.E `7d19a7e`; ack-first `32ff67d`; §8 backfill `bda2ced`.
**BASELINE (pre-build tip):** `bda2ced` — current canonical pos-v2 HEAD.
**Status-file target:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-amend-ergonomics-status-2026-05-03.md`.

---

## 1. Summary / TLDR

v0.1.2 item 6 lands three captured loam-amend tooling ergonomic improvements as a single sealed amendment. All three are observed pain points hit by every recent FBE.x and V11.x build agent. Bundled because (a) all three live in the same component (`plugins/dev-sdlc/tools/loam-amend/`), (b) all three are tooling-ergonomic improvements with no semantic change to amendment shape.

**The three improvements (verbatim from v0.1.x roadmap §2 item 6):**

1. **(a) auto-commit on `loam amend apply`** — after a successful (non-dry-run) apply, the tool stages the touched paths (sidecars + seal-test BASELINE literals + manifest-derived widening edits) and creates a conventional `chore(amend): <description> apply — <summary>` commit. Decision (locked by dispatcher per FIDRAFT note + roadmap §2): **implement auto-commit** rather than print-only-message.
2. **(b) `loam amend seal --allow-untracked-globs <pattern>` flag** — admits paths matching the named glob pattern when the seal step computes clean-tree status (i.e. those paths are no longer counted as "unrelated dirty state" that aborts the seal). Repeatable; multi-flag supported. Common case: dirty `docs/rebuild/FUTURE_IDEAS_DRAFT.md` from in-flight capture.
3. **(c) partner-prefix derivation from `seal_test`** — `apply.py` currently derives partner-prefix admissions for cross-component widening from each component's `name` field (assumes `framework/<name>/` + bare `<name>/` shapes). Latent bug: `plugins/<name>/`-located components surface as wrong-shape admissions. Fix derives the partner-prefix from the manifest's `seal_test` path (the canonical shape-discriminator).

Sealed-component fence: **single component — `plugins/dev-sdlc/`** (the dev-sdlc plugin's own seal-test, which fences `plugins/dev-sdlc/tools/loam-amend/` along with the rest of the plugin).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; auto-commit shape consistency with seal-commit shape)

The seal step (`commands/seal.py:_build_commit_message`) uses `chore(seals): <description> — <comp1>[+<comp2>...] at <sha-short>` as the subject; multi-section body (Amendment number, Bumped sidecars, Narrative target, Diff window, Cross-component sweep). Auto-commit's apply commit should adopt the **same family** of subject + body shape so future agents see a consistent audit trail.

**Decision (autonomous, builder's call):** apply auto-commit subject = `chore(amend): <description> apply — <comp1>[+<comp2>...] BASELINE+sidecar bump to <baseline-short>`. Body sections: amendment-number + per-component change list (BASELINE / sidecar bump). The new shape mirrors the manual apply commit Luke / agents have been writing (`8cbab6a` is the most recent example) so existing reviewers + dispatch prompts read it without re-learning.

### Surface #2 (no halt — recorded; backwards-compat for existing dispatch prompts)

Several in-flight dispatch prompts (e.g. v0.1.3 R.x SKILL packages, v0.1.4 personas) explicitly say "manually create the apply commit (`chore(amend): <name> apply ...`)". Once auto-commit lands, those prompts become slightly stale: the agent will create a `chore(amend): ... apply` commit, then re-stage and create another. Two outcomes possible:

- **Outcome A (most likely):** the second `git commit` finds nothing staged (auto-commit already staged + committed everything) and either errors or no-ops. No harm; agent surfaces the no-op and moves on.
- **Outcome B (less likely):** agent's manual apply commit lands on top of an already-clean tree as an empty commit. Also harmless but noisy.

**Decision (autonomous):** ship the auto-commit; document the backwards-compat note in the status file. Existing dispatch prompts are not updated as part of this amendment (out-of-fence; opportunistic cleanup at the next dispatch authoring touch).

### Surface #3 (no halt — recorded; `--allow-untracked-globs` semantics)

The current dirty-tree check (`commands/seal.py:_working_tree_dirty`) ignores paths in `expected_writes` (sidecars + narrative target). The new flag widens the ignore-set: each `<pattern>` is matched against each dirty path with `fnmatch.fnmatchcase` (case-sensitive shell-style globs).

**Open sub-decision (autonomous):** anchor patterns at the repo root (path equals `pattern` per `fnmatch.fnmatchcase`) — no implicit trailing `*`. This means `docs/rebuild/FUTURE_IDEAS_DRAFT.md` matches the file literally; `docs/rebuild/*` matches direct children of `docs/rebuild/` only; `docs/**/*` is the recursive-match form. Mirrors POSIX-shell glob semantics; minimal magic; documented in the `--help` text.

The flag is repeatable: `--allow-untracked-globs A --allow-untracked-globs B`. Each invocation appends to the admit-set. Patterns admitted via the flag bypass the dirty-state check; they are **not** auto-staged or committed (the seal step still only stages declared sidecars + narrative + plan-doc per existing logic).

### Surface #4 (no halt — recorded; partner-prefix derivation new shape)

Current code (`apply.py:93-96`):

```python
partner_prefixes: set[str] = set()
for _c in manifest.components:
    partner_prefixes.add(f"framework/{_c.name}/")
    partner_prefixes.add(f"{_c.name}/")
```

Fix derives from `seal_test` instead. The canonical shape: `<base>/<name>/tests/test_no_sealed_amendments.py` (or `test_cross_cutting.py` for hands-off-lifecycle). `<base>/<name>/` is the partner-prefix.

**Decision (autonomous):** replace the body-of-loop with:

```python
# Derive partner prefix from seal_test path (canonical shape-discriminator).
# Convention: <base>/<name>/tests/test_*.py — first two segments are
# the partner-prefix root. Falls back to name-derived shapes if the
# seal_test path isn't long enough.
seal_test_parts = Path(_c.seal_test).parts
if len(seal_test_parts) >= 2 and seal_test_parts[-2] == "tests":
    partner_prefixes.add(f"{seal_test_parts[0]}/{seal_test_parts[1]}/")
else:
    # Defensive fallback (shouldn't trigger on canonical manifests).
    partner_prefixes.add(f"framework/{_c.name}/")
    partner_prefixes.add(f"{_c.name}/")
```

Backwards-compat: existing manifests with `seal_test: framework/<name>/tests/...` produce the same `framework/<name>/` admission they had before (the old `<name>/` bare admission is dropped because post-D.1 nothing is bare-located; if a manifest specifies a bare-`<name>/` seal_test it falls through to the defensive branch). Plugins-located manifests (`plugins/<name>/tests/...`) now produce the correct `plugins/<name>/` admission.

**Cross-component widening side-effect:** the partner-set used to admit the cross-component partner-paths excluding self. The exclusion logic must update to use the new derivation:

```python
self_prefix = f"{seal_test_parts[0]}/{seal_test_parts[1]}/"
partners = sorted(partner_prefixes - {self_prefix})
```

Both call sites (cleanup-protected branch + standard branch) update in lock-step.

### Surface #5 (no halt — recorded; auto-commit failure semantics)

If the auto-commit step fails (git not configured, no staged changes, etc.), apply must surface the failure and exit non-zero rather than silently dropping the commit. Mirror seal.py's `_FailureCheckpoint` pattern (already present in apply.py for tracker errors): emit `HALT: apply-commit-failed` + diagnostic + return code 3.

**Decision (autonomous):** when auto-commit fails, leave the staged + working-tree changes in place (they were the legitimate apply work) and exit 3 with operator-actionable diagnostic. The operator can then `git commit` manually and re-invoke seal — same fallback as the pre-extension behaviour.

**Sub-decision: skip the auto-commit if no changes to commit.** The "no changes (idempotent re-run)" path already prints + returns 0; preserve that — no auto-commit fires when there's nothing to stage. Output text continues to read "no changes (idempotent re-run); skipping commit".

### Surface #6 (no halt — recorded; manifest-level admission for `--allow-untracked-globs`)

The FIDRAFT entry mentioned admitting patterns at the manifest level so the amendment author opts in. **Decision (autonomous):** ship the CLI flag only; defer manifest-level admission to a follow-on. Rationale: the CLI flag covers the immediate workflow (operator invokes `loam amend seal --allow-untracked-globs docs/rebuild/FUTURE_IDEAS_DRAFT.md ...`); manifest-level admission adds schema work (manifest field + test + parser update + interaction with `extra_allowed_files`) that is a non-trivial widening. CLI flag = minimum viable; manifest field can land later if observed pain-point recurs.

### Surface #7 (no halt — recorded; meta-recursive auto-commit on this amendment)

This amendment **adds** auto-commit to `apply.py`. The auto-commit fires from the next invocation of `loam amend apply` onward. For this amendment's own apply step, the dispatcher's instruction "manually create the apply commit (`chore(amend): loam-amend ergonomics apply ...`)" applies — the auto-commit code path is in the new `apply.py` but the apply step here predates the seal of this amendment. Safe by sequence; documented in the status file.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — translation-burden reduction for the primary persona's amendment ritual. Auto-commit removes a cognitive-overhead step; `--allow-untracked-globs` removes a stash-then-pop friction loop; partner-prefix fix removes a class of false-fence-failure that requires hand-corrective.
- **v0.1.x roadmap §2 v0.1.2 item 6** — three loam-amend tooling ergonomic improvements as defined by the dispatcher.
- **AC.LAE.* per this sub-plan §4** — every AC ladders to the same parent.
- **Composes with:** the ack-first persona contract amendment (`32ff67d`) — both reduce in-session friction; the loam-amend ergonomics make subsequent amendment-cycle work less painful for the persona who just acknowledged a multi-file build dispatch.

**Ladders to:** AC.LAE.* → v0.1.2 release (closing item; last v0.1.2 amendment) → v0.1.3 + onward (every future amendment-cycle inherits the ergonomic improvements) → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (LAE.*)

**AC family:** `AC.LAE.*` (Loam Amend Ergonomics). Pre-grep verified zero collisions in framework/, plugins/, tests/, docs/.

### AC.LAE.1 — auto-commit on `loam amend apply` (non-dry-run)

After a successful non-dry-run apply that produced changes, the tool:
1. Stages every modified path under the manifest's component fences (each component's `seal_test` + `sidecar` + any widened-binding edits) — `git add -A` scoped to repo-root is acceptable provided dirty-tree pre-check guarantees no unrelated paths picked up.
2. Creates a commit with subject `chore(amend): <description> apply — <comp-list> BASELINE+sidecar bump to <baseline-short>`. `<description>` = `manifest.seal_description or manifest.slug`. `<comp-list>` = `+`-joined component names. `<baseline-short>` = first 7 chars of `manifest.baseline`.
3. Body carries (a) Amendment-number reference, (b) per-component change list (BASELINE / sidecar bumps + widening), (c) sub-plan reference. Co-Authored-By trailer when running under a Claude env (mirror seal.py's existing `_claude_environment()`).
4. On apply with no changes ("idempotent re-run"), no commit is created; existing "no changes" message is preserved verbatim.
5. On `git commit` failure, emits `HALT: apply-commit-failed` + diagnostic + returns 3; staged changes are left in place.

**Verified by:** `tests/test_AC_LAE_1_apply_auto_commit.py` (new file; ~5 tests covering the success path, idempotent-re-run no-commit path, commit-failure path, multi-component subject shape, Co-Authored-By trailer behaviour).

### AC.LAE.2 — `loam amend seal --allow-untracked-globs <pattern>`

The seal subcommand accepts a repeatable `--allow-untracked-globs <pattern>` flag. Each `<pattern>` is matched against each repo-relative dirty path via `fnmatch.fnmatchcase`. Matches are admitted into the dirty-state ignore-set (alongside the existing `expected_writes` set). The seal proceeds when all dirty paths are accounted for via `expected_writes` ∪ glob-matched. Patterns are NOT staged or committed by the seal step — admission is dirty-check-only.

**Verified by:** `tests/test_AC_LAE_2_seal_allow_untracked_globs.py` (new file; ~4 tests: single pattern admits a literal path, glob pattern admits a directory, multiple --allow-untracked-globs flags compose, dirty-path NOT matched still aborts).

### AC.LAE.3 — `loam amend apply` partner-prefix derivation from `seal_test`

`apply.py` derives partner-prefix admissions for cross-component widening from each component's `seal_test` path (first two path segments) rather than from the `name` field. The exclude-self computation uses the same derivation. Backwards-compat: framework-located manifests produce the same `framework/<name>/` admission as before (modulo the dropped bare-`<name>/` admission, which was D.1 vestigial). Plugins-located components produce `plugins/<name>/` admissions correctly.

**Verified by:** `tests/test_AC_LAE_3_partner_prefix_from_seal_test.py` (new file; ~4 tests: framework-located parses to framework-prefix, plugins-located parses to plugins-prefix, mixed-fence amendment admits both correctly, defensive fallback for non-canonical seal_test paths).

### AC.LAE.S — sealed-component fence: `plugins/dev-sdlc/`

Single-component fence on `plugins/dev-sdlc/` (the dev-sdlc plugin's own seal-test fences `plugins/dev-sdlc/tools/loam-amend/` along with the rest of the plugin). Sidecar advance: `plugins/dev-sdlc/tests/SEAL_COMMIT`. No edits outside `plugins/dev-sdlc/` permitted, plus the universal `docs/rebuild/plans/` admission for the sub-plan + manifest landing here.

**Verified by:** post-seal `git diff <BASELINE>..<seal_sha> --name-only` confined to `plugins/dev-sdlc/` + `docs/rebuild/plans/` (universal-admitted).

---

## 5. Method-level choices (builder's call per ODD §1.1)

- **Auto-commit staging strategy.** Stage explicitly the per-component `seal_test` + `sidecar` paths from the manifest. Avoid `git add -A` (could pick up unrelated dirty state if the operator's tree is dirty). Mirrors the seal step's `paths_to_stage` pattern.
- **Auto-commit body shape.** Multi-section like seal-commit but tuned to apply's mutation set: Amendment number + per-component bump list + sub-plan reference. Co-Authored-By via the existing `_claude_environment()` helper (re-import or duplicate constants — code duplication acceptable here since seal already exposes the helper as module-private; expose at module level if the test file needs it, else duplicate).
- **`fnmatch.fnmatchcase` for glob matching.** Standard library, no shape-magic. Each pattern matches against the porcelain output's path segment. Patterns are case-sensitive by default (POSIX-shell convention).
- **Partner-prefix derivation tolerates missing `tests` segment.** Defensive branch falls back to old name-derivation if the seal_test path doesn't end in `/tests/<file>.py`. Should never trigger in practice but prevents crashes on hand-authored test fixtures.
- **Exclude-self in partner widening.** The exclude-self set must use the new derivation source (the seal_test-derived prefix, not `framework/<name>/` literal). Both branches (cleanup-protected + standard) update in lock-step.
- **CLI flag naming.** `--allow-untracked-globs` (plural; matches the repeatable nature). `<pattern>` is a single glob per flag instance; patterns aggregate across multiple `--allow-untracked-globs` flags. Help text names common usage: `--allow-untracked-globs docs/rebuild/FUTURE_IDEAS_DRAFT.md`.

---

## 6. Apply commit ladder

```
bda2ced (canonical pos-v2 HEAD pre-build)
  │
  ▼
<plan-doc commit> — this sub-plan-doc + AC family pre-grep notes
  │
  ▼
<source edit commit> — apply.py auto-commit + partner-prefix fix; seal.py + cli.py allow-untracked-globs flag; new tests
  │  (this commit becomes the BASELINE for the manifest)
  │
  ▼
<manifest commit> — manifest.yaml authoring; baseline pinned at the source-edit commit
  │
  ▼
<chore(amend): apply commit> — manual (per dispatcher; this amendment predates the auto-commit it ships)
  │
  ▼
<chore(seals): seal commit> — deterministic seal commit from `loam amend seal`
  │
  ▼
<docs(plans): §8 backfill commit> — `loam amend seal --plan-doc` writes §8 backfill into v0-1-x-roadmap.md
```

---

## 7. Smoke verification protocol

Three smoke scenarios per dispatcher:

### Smoke A (AC.LAE.1 — auto-commit)

Build a tmp scratch repo via `scratch_repo` fixture. Author a tiny manifest pointing to a stub component. Run `apply_run(manifest_path, dry_run=False)`. Assert: HEAD changed (new commit landed); subject matches `chore(amend): ... apply — <comp> BASELINE+sidecar bump to ...`; tree clean post-apply.

### Smoke B (AC.LAE.2 — allow-untracked-globs)

Build a tmp scratch repo. Author a manifest. Apply (manual commit). Touch an unrelated file `docs/rebuild/FUTURE_IDEAS_DRAFT.md` (without staging). Run `seal_run(manifest_path, scoped_sweep=True, allow_untracked_globs=("docs/rebuild/FUTURE_IDEAS_DRAFT.md",))`. Assert: seal proceeds (no `dirty-working-tree` halt); the unrelated file remains untracked + uncommitted post-seal.

### Smoke C (AC.LAE.3 — partner-prefix derivation)

Build a tmp scratch repo with two components: one at `framework/alpha/` and one at `plugins/beta/`. Author a manifest listing both. Run apply. Assert: alpha's seal-test admits `plugins/beta/` (the partner derived from `plugins/beta/tests/test_*.py`); beta's seal-test admits `framework/alpha/`. Neither admission carries the wrong-shape `beta/` bare admission for the plugins-located component.

---

## 8. Out of scope

- **Manifest-level `allow_untracked_globs` admission** — deferred per Surface #6.
- **Auto-commit for `loam amend seal --plan-doc` backfill** — already auto-commits; no change here.
- **Migrating prior manifests' `extra_allowed_prefixes` to drop now-redundant `<name>/` bare admissions** — out of fence (would touch every sealed component's manifest); opportunistic.
- **Backwards-update of in-flight dispatch prompts that say "manually create the apply commit"** — out of fence; documented in status file as the operator-noted backwards-compat note.
- **`--allow-untracked-globs` for the `apply` step's own dirty-tree assumption** — apply doesn't currently dirty-check (only seal does); no parallel surface to widen.

---

## 9. Test plan

Three new test files (one per AC.LAE.*) under `plugins/dev-sdlc/tools/loam-amend/tests/`:

- `test_AC_LAE_1_apply_auto_commit.py` — 5 tests: success-path commit lands, subject shape verified, idempotent-re-run skips commit, commit-failure surfaces HALT + exit 3, Co-Authored-By trailer behaviour under env-var.
- `test_AC_LAE_2_seal_allow_untracked_globs.py` — 4 tests: single literal pattern admits, glob pattern admits, multi-flag compose, non-matching dirt still aborts.
- `test_AC_LAE_3_partner_prefix_from_seal_test.py` — 4 tests: framework-located, plugins-located, mixed fence, defensive fallback.

Touched-only test scope (per amendment-dispatch-speedup CDC): `pytest plugins/dev-sdlc/tools/loam-amend/tests/`.

Cross-component sweep: scoped sweep on `plugins/dev-sdlc/` only (single-component fence; the canonical-pos-v2 sweep risk is `_run_pytest` invocations on plugins/dev-sdlc/tools/loam-amend/tests/ via the seal step itself).

---

## 10. ODD §2.5 mapping

Every line of the source edit maps to a named AC:
- `apply.py` auto-commit block → AC.LAE.1
- `apply.py` partner-prefix derivation → AC.LAE.3
- `seal.py` `--allow-untracked-globs` widen → AC.LAE.2
- `cli.py` `--allow-untracked-globs` argparse → AC.LAE.2
- `cli.py` apply auto-commit no surface change (apply CLI flag remains `--dry-run`)
- New test files → AC.LAE.1, AC.LAE.2, AC.LAE.3
- Manifest + sub-plan-doc → AC.LAE.S (fence + provenance)

No silent fall-throughs. No method-in-acceptance smuggling.

---

## 11. Predecessor commits

- `9d58062` — V11.A seal (orchestrator runtime fix).
- `7d19a7e` — V11.E seal (graphiti probe graceful-skip).
- `32ff67d` — ack-first persona contract seal.
- `bda2ced` — v0-1-x roadmap §8 backfill (canonical pos-v2 HEAD pre-this-build).

---

## 12. Method-decision register backfill target

After seal, `loam amend seal --plan-doc docs/rebuild/plans/v0-1-x-roadmap.md` writes the §8 entry. **The §8 row already declares this is item-6**; the auto-backfill targets §14 by default. **The roadmap doc has §8 not §14** — same shape as the prior v0.1.2 amendments which also used §8. The seal-step's `--plan-doc` regex matches `^## 14[.\s]` and would not match §8.

**Decision (autonomous):** do NOT pass `--plan-doc` to the seal step for this amendment. Manually backfill §8 via a follow-on `docs(plans): record amendment #N commit SHAs ...` commit (mirrors the pattern used at `bda2ced` for item 5). Reads cleanly with the rest of the §8 entries. Same shape; same authorship.

---

## 13. Status file outline

`/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-amend-ergonomics-status-2026-05-03.md` will record:
- BASELINE + apply commit + seal commit + §8-backfill commit SHAs
- Per-AC verification (test names + smoke scenario outputs)
- Surfaces 1-7 status (each marked resolved-in-band or deferred)
- Backwards-compat note for in-flight dispatch prompts (Surface #2 / Outcome A)
- `loam amend apply` behaviour transition: prior-art (manual commit) vs new (auto-commit) — table

---

## 14. Method-decision register — placeholder

Reserved for the deterministic record of:
- Plan-doc commit SHA
- Source-edit commit SHA
- Manifest commit SHA
- Apply commit SHA (manual; pre-fix)
- Seal commit SHA (deterministic seal)
- §8 backfill commit SHA (manual)

Backfilled into the parent roadmap §8 post-seal.

---

*End of v0.1.2 item 6 sub-plan.*
