# FBE.2b sub-plan — Synth pipeline preserves `framework/` prefix on shipped paths

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §3 Decision D + §4 (newly-inserted FBE.2b row).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.1 sealed at `21b9480`; FBE.2 sealed at `8d2b770`; FBE.3 sealed at `becf183`; FBE.4 sealed at `99c03a6`; FBE.5 sealed at `bc56f0d`; FBE.7 sealed at `a102bde`. FBE.2 status: `<workspace>/.scratch/claude-output/fbe2-status-2026-05-03.md` (Surface #1 — strip-rationale documented as deferred to "FBE.2 expansion or new amendment"; FBE.2b is that amendment).
**BASELINE (pre-build tip):** `8f3538a` — current canonical pos-v2 HEAD (FBE.5 §8 register backfill commit).

---

## 1. Summary / TLDR

The `pos-publish-framework-only` synth pipeline currently strips the
`framework/` prefix on shipping paths (`synth.py` lines 302-312:
`synthetic_path = source_path[len("framework/"):]`). Every doc in the
canonical tree references `framework/<comp>/...` paths (15+ files
verified at parent plan §2.4); the synth ships those same components
at bare `<comp>/...` and `tools/<tool>/...` at synth-tree root, so
the documented `pip install -e framework/tools/loam` command in the
README does not actually find anything in a framework-only checkout.

Decision D in the parent foldback plan §3 locked: **fix the synth
pipeline to preserve the `framework/` prefix**, not rewrite the
docs. FBE.2b is that fix.

The edit is targeted: drop the prefix-strip rewrite + the
`saw_framework_leaf` guard's strip-coupled language, update the
synth.py module docstring + the cli.py `--help` description's
"`framework/<entry>` to root" / "`framework/framework/<comp>/`
doubling" rationale (which becomes obsolete), and update the four
existing partition + synthesis tests inside the manifest-owner fence
(`pos-publish-framework-only/tests/`) that assert on the strip-shape
synth-tree paths to assert on the prefix-preserved paths.

After FBE.2b lands, `git ls-tree framework-only | head` shows
`framework/tools/loam/`, `framework/workspace-bootstrap/`,
`framework/loam-init/`, etc. — matching the docs.

This is a **single sealed-component fence** amendment:
`framework/tools/pos-publish-framework-only/` (the manifest owner +
synth pipeline owner). Establishes the component's `tests/SEAL_COMMIT`
sidecar + `test_no_sealed_amendments.py` invariant at FBE.2b — same
shape FBE.2 used for `framework/tools/loam/` (no pre-existing sidecar
on `pos-publish-framework-only/` per FBE.2 §7 verification —
historically rode universal-paths admission alone; FBE.2b establishes
the seal anchor).

Closes the synth-shape side of HIGH 1 (parent plan §2.4 — "docs
reference `framework/<comp>/`, synth ships top-level"). FBE.6's
extended smoke (AC.FBE.6.3) requires this fix so
`pip install -e framework/tools/loam` against a framework-only
checkout actually finds the package.

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt; recorded — strip rationale `framework/framework/<comp>/` doubling is reversible)

The cli.py description text at line 37 carries the historical
rationale: "eliminating the `framework/framework/<comp>/` doubling
failure class." This referred to a pre-FBE.1 workspace-bootstrap
shape where workspaces clone into a directory and the bootstrap then
moved files. The current shape (per FBE.1 + verified FBE.5 smoke)
has `bootstrap_new_workspace` clone canonical into
`<workspace>/framework/` directly — preserving `framework/<comp>/`
in the workspace shape. The doubling failure class no longer
applies; the synth's strip is now NET-NEGATIVE (it makes the
documented install path wrong without removing any failure).

This is the empirical anchor for Decision D's "fix the synth, not
the docs." Verified by reading
`framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:415-470`
(clone-into-`<workspace>/framework/` shape; matches docs).

### Surface #2 (no halt; recorded — sealed-component sidecar shape required)

`framework/tools/pos-publish-framework-only/` does NOT have a
`tests/SEAL_COMMIT` sidecar or `tests/test_no_sealed_amendments.py`
invariant today. FBE.2 verified this at planning-time (sub-plan §7
note); FBE.2 itself rode universal-paths admission of
`framework/tools/pos-publish-framework-only/` alone, never
establishing the sidecar.

FBE.2b is a substantive code edit (synth.py + cli.py + tests) inside
the manifest-owner component, not a manifest reclassification — so
the universal-paths-only ride is no longer enough. **FBE.2b
establishes the sealed-component sidecar** (mirroring FBE.2's
loam-cli pattern exactly: `tests/SEAL_COMMIT` + standard
`test_no_sealed_amendments.py` referencing
`framework/tools/pos-publish-framework-only/` as the fence prefix).

The component name in the manifest will be
`pos-publish-framework-only` (matches the pyproject `name =
"pos-publish-framework-only"`).

### Surface #3 (no halt; recorded — three test files inside manifest-owner fence need synth-path-shape updates)

The strip behaviour is asserted in test fixtures inside
`framework/tools/pos-publish-framework-only/tests/`:

1. `test_AC_SFR_2_synthesis_pipeline.py` — three assertions:
   - line 73-75: `cost-governance/__init__.py`, `workspace-bootstrap/src/__init__.py`, `tools/loam-mode/__init__.py` in synth tree
   - line 78-79: NO doubled `framework/cost-governance/...` AND `assert all(not p.startswith("framework/") for p in paths)`
   - line 104-109: HC#4 byte-content match pairs
   - line 166: `cost-governance/added.py` in synth tree (lockstep test)
   - line 263: stranger-clone byte-equality check (read of `framework/cost-governance/__init__.py` on the canonical-side).

2. `test_AC_OSS_3_synthesis_drops_dev_only.py`:
   - line 110-113: ships-paths (`cost-governance/__init__.py`, `CLAUDE.md`, `README.md`, `docs/positioning.md`)
   - line 116: drop-paths (`tools/loam/cli.py`, etc.)
   - line 252-254: `.DS_Store` audit-exclude assertions on `cost-governance/.DS_Store` + `cost-governance/__init__.py`.

3. `test_AC_OSS_M9_substitution_after_partition.py`:
   - line 110: `tools/loam/cli.py` not in tree
   - line 113: `cost-governance/__init__.py` in tree
   - line 169: `cost-governance/__init__.py` SHA preservation.

All three test files live INSIDE the FBE.2b sealed-component fence
(`framework/tools/pos-publish-framework-only/tests/`). All edits are
in-fence (no universal-paths needed for them).

The other M9 test files (`...idempotent.py`, `...binary_safe.py`,
`...smoke.py`) do NOT assert on synth-tree post-strip paths — they
either check blob SHAs without naming the synth-tree path, or test
top-level paths (`docs/assets/logo.png`) which are not affected by
the framework-prefix-strip.

### Surface #4 (no halt; recorded — `_LeafEntry.synthetic_path` docstring + sweep tests in non-fence components are reverse-shape-safe)

The `_LeafEntry` dataclass docstring (synth.py:163-180) describes
the synthetic_path as `framework/<rel>` rewritten to `<rel>` at
root. After FBE.2b: synthetic_path equals source_path verbatim for
framework leaves. Docstring updates accordingly.

The cross-component sweep tests (per FBE.5's seal-time sweep — 14
fence-test files across the framework) do not assert on synth-tree
paths; they assert on `git diff` output between BASELINE and seal
SHA. Those tests stay green for FBE.2b's fence.

The `cli.py:36-38` description string carries the obsolete strip
rationale; updates accordingly.

### Surface #5 (no halt; recorded — `test_synthesis_fails_when_framework_subdir_absent` semantic preserved)

The negative test at `test_AC_SFR_2_synthesis_pipeline.py:270` checks
that a source commit with no `framework/` subdir raises
`SynthesisError` with message containing `"no entries under
framework/"`. The semantic is preserved post-FBE.2b: the synth still
requires at least one `framework/` leaf to operate (the
`saw_framework_leaf` guard stays — it just no longer doubles as a
"saw a leaf we strip-rewrote" signal). The error message stays
identical.

### Surface #6 (no halt; recorded — partition.py / substitution.py are not affected)

Verified by `grep`: only `synth.py` and `cli.py` carry the prefix-
strip / doubling-rationale text. `partition.py` references
`framework/tools/pos-publish-framework-only/` only as the manifest
default location; `substitution.py` carries no framework-prefix
logic. FBE.2b's edit surface is contained to two source files +
three test files within the manifest-owner fence.

### Surface #7 (no halt; recorded — fence-test allowed_prefixes inheritance from FBE.5)

Per FBE.4 + FBE.5 partner-prefix gap (FUTURE_IDEAS_DRAFT-tracked):
`loam amend apply` derives partner_prefixes assuming `framework/<name>/`
for every fence component. For `pos-publish-framework-only` (which
lives at `framework/tools/pos-publish-framework-only/`), the apply
tool may admit `pos-publish-framework-only/` and
`framework/pos-publish-framework-only/` (both wrong shapes) and miss
`framework/tools/pos-publish-framework-only/`. **Build-time
strategy:** run `loam amend apply` first; if `loam amend seal` fails
on the fence test with offending paths under the missing
`framework/tools/pos-publish-framework-only/` prefix, apply a
corrective hand-admit per FBE.4/FBE.5 precedent.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per
  `docs/rebuild/VALUE_PROPOSITION.md`) — making the documented
  install path (`pip install -e framework/tools/loam`) actually
  work in the synth tree is a prerequisite for the harness's
  "stranger reads docs and installs" promise.
- **Reviewer foldback HIGH 1** (per parent plan §2.4) — docs
  reference `framework/<comp>/` paths consistently; synth ships
  top-level. Decision D locked: fix synth, not docs. FBE.2b
  delivers Decision D.
- **AC.FBE.6.3** — FBE.6's extended smoke needs the documented
  install path to actually find files at that path in a synth-tree
  checkout.

**Ladders to:** AC.FBE.2b.* → AC.FBE.6.3 → AC.OSS-M11a.* (FBE.6
reviewer GO) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.2b.*)

AC family **`AC.FBE.2b.*`** — collision-safe (verified: no prior
amendment uses `AC.FBE.2b.*`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.2b.1** | `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py` no longer rewrites `framework/<rel>` → `<rel>` for shipping paths. The `_build_synthetic_tree` function's per-leaf path-shaping branch (currently lines 302-312) sets `synthetic_path = source_path` unconditionally for shipping leaves. The `saw_framework_leaf` guard tracks "at least one framework/-prefixed leaf was emitted" semantics (preserved unchanged); the bare-`framework` safety branch (currently `elif source_path == FRAMEWORK_PREFIX`) is dropped (collapsed into the unconditional pass-through). | `grep -n "source_path\[len(framework_prefix)" framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py` returns zero hits; `grep -n "synthetic_path = source_path" framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py` returns one hit inside `_build_synthetic_tree`. |
| **AC.FBE.2b.2** | `synth.py` module docstring (lines 1-50) + `_LeafEntry.synthetic_path` docstring (lines 163-180) + `_build_synthetic_tree` docstring (lines 269-287) updated to describe the prefix-preserving behaviour. The "promote `framework/<entry>` to root" / "rewrites `framework/<rel>` → `<rel>`" language is replaced with "preserve canonical's `framework/<entry>` shape verbatim in the synthetic tree." | `grep -E "promote.*to root\|rewrites.*framework/<rel>\|<rel> at root" framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py` returns zero hits in the docstring sections. |
| **AC.FBE.2b.3** | `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/cli.py` `--help` description (lines 28-39) updated: drop "promotes `framework/<entry>` to root" + "eliminating the `framework/framework/<comp>/` doubling failure class" — replace with one-sentence description that the synthetic tree mirrors canonical's `framework/<comp>/` layout under the publish-mode partition manifest. | `grep -E "promotes \`framework/<entry>\`\|framework/framework/<comp>/\|doubling failure class" framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/cli.py` returns zero hits. |
| **AC.FBE.2b.4** | Synth re-run from canonical pos-v2 HEAD (post-FBE.2b-seal) produces a `framework-only` tree where the leaves promoted under `framework/` retain their canonical paths. Specifically: `git ls-tree -r --name-only framework-only` returns paths `framework/tools/loam/pyproject.toml`, `framework/tools/loam/src/loam_cli/cli.py`, `framework/workspace-bootstrap/pyproject.toml`, `framework/loam-init/pyproject.toml`, etc. — NOT `tools/loam/pyproject.toml` / `workspace-bootstrap/pyproject.toml`. Top-level files (`CLAUDE.md`, `README.md`, `docs/...`) STAY at top-level (unchanged). | Direct `synthesise_framework_only` invocation against canonical post-seal HEAD; `git ls-tree -r --name-only framework-only \| grep -cE '^framework/'` returns ≥ 5 (one per shipping framework component); same grep for `'^tools/'` returns 0; `'^workspace-bootstrap/'` returns 0. |
| **AC.FBE.2b.5** | `test_AC_SFR_2_synthesis_pipeline.py` updated: synth-tree-shape assertions reflect the prefix-preserving paths. Specifically: (a) `cost-governance/__init__.py` → `framework/cost-governance/__init__.py`, `workspace-bootstrap/src/__init__.py` → `framework/workspace-bootstrap/src/__init__.py`, `tools/loam-mode/__init__.py` → `framework/tools/loam-mode/__init__.py` in the post-synth tree-listing assertions; (b) the "no doubled framework/ prefix" assertion (`assert all(not p.startswith("framework/") for p in paths)`) flipped to its negation (at-least-one-framework-prefixed-leaf for shipping components); (c) HC#4 byte-content match pairs updated so source and synth paths are equal for framework leaves; (d) lockstep test's `cost-governance/added.py` → `framework/cost-governance/added.py`. | `pytest framework/tools/pos-publish-framework-only/tests/test_AC_SFR_2_synthesis_pipeline.py` returns 6/6 pass. |
| **AC.FBE.2b.6** | `test_AC_OSS_3_synthesis_drops_dev_only.py` updated: ships-paths assertions name `framework/cost-governance/__init__.py` (not `cost-governance/__init__.py`); drops-paths assertions name `framework/tools/loam/cli.py` (not `tools/loam/cli.py`); audit-excludes test names `framework/cost-governance/.DS_Store` (not `cost-governance/.DS_Store`). | `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_synthesis_drops_dev_only.py` returns 5/5 pass. |
| **AC.FBE.2b.7** | `test_AC_OSS_M9_substitution_after_partition.py` updated: tree-entry path assertions name `framework/cost-governance/__init__.py` and `framework/tools/loam/cli.py` (not the post-strip variants). | `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_M9_substitution_after_partition.py` returns 2/2 pass. |
| **AC.FBE.2b.8** | The four partition tests + the substitution-pipeline tests inside `framework/tools/pos-publish-framework-only/tests/` that do NOT assert on synth-tree post-strip paths (`test_AC_OSS_3_default_partition_complete.py`, `test_AC_OSS_3_partition_classifier.py`, `test_AC_OSS_3_partition_manifest_load.py`, `test_AC_OSS_M9_substitution_idempotent.py`, `test_AC_OSS_M9_substitution_binary_safe.py`, `test_AC_OSS_M9_substitution_smoke.py`, `test_AC_PMR_1_gate_tests_dev_only.py`, `test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py`) continue to pass byte-identically (no test edits to these files). | `pytest framework/tools/pos-publish-framework-only/tests/` returns 70/70 pass (15+ test files pass — same count as FBE.2 status reported). |
| **AC.FBE.2b.9** | NEW sealed-component sidecar files exist: `framework/tools/pos-publish-framework-only/tests/SEAL_COMMIT` + `framework/tools/pos-publish-framework-only/tests/test_no_sealed_amendments.py`. Mirrors FBE.2's loam-cli sidecar shape exactly (REPO_ROOT depth 5; same allowed_prefixes admission shape; standard `_seal_commit` sidecar-file resolver). | `ls framework/tools/pos-publish-framework-only/tests/{SEAL_COMMIT,test_no_sealed_amendments.py}` succeeds; the fence-test passes against the FBE.2b BASELINE post-seal. |
| **AC.FBE.2b.10** | Negative AC: zero changes to `partition.py`, `substitution.py`, the `publish-mode-manifest.yaml` content, or any component outside `framework/tools/pos-publish-framework-only/`. The canonical pos-v2 tree's leaves continue to classify identically (this is a path-shaping-only edit; classification is unchanged). | `git diff BASELINE..SEAL_COMMIT --stat -- framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/partition.py framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/substitution.py framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` returns empty. |
| **AC.FBE.2b.S** | Sealed-component fence: `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under `framework/tools/pos-publish-framework-only/` (the fence) + `docs/rebuild/plans/` (universal_paths.prefixes; sub-plan + manifest YAML + parent backfill). | `framework/tools/pos-publish-framework-only/tests/test_no_sealed_amendments.py` invariant + manual `git diff --name-only` check at seal time. |

**ACs deliberately out of scope (NOT in FBE.2b):**
- Partition manifest content edits (no reclassification — this is a
  path-shaping fix, not a classification change).
- Edits to `partition.py` or `substitution.py` (no logic change in
  either; AC.FBE.2b.10 negative).
- Edits to other components (FBE.2b is a single-component
  amendment).
- Re-staging/re-pushing the synth to remote (FBE.6's job; no premature
  push per dispatch).
- README / getting-started / `docs/install-from-source.md` rewrites
  (already use `framework/<comp>/` paths consistently — verified at
  FBE.2 + FBE.5).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
Pure synth-pipeline path-shaping fix; no Claude-native primitive in
scope. Composes with FBE.6's reviewer-agent re-run (a Claude-leveraged
operation) by removing the doc-vs-synth path-shape divergence the
reviewer would otherwise re-flag.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The documented install path
  (`pip install -e framework/tools/loam`) is what the primary persona
  surfaces to the user when explaining "how do I get the loam CLI
  running from this checkout?" Without FBE.2b, that surface is
  internally inconsistent (docs say one path, synth ships at
  another). FBE.2b removes the translation burden the persona would
  otherwise have to add.
- **Harness test:** PASS (neutral). Doesn't add to the toolkit;
  doesn't remove from it. Aligns shipping shape with documented
  shape.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which lines of `synth.py` to edit,
which test assertions to flip) is the builder's call but constrained
tight by the AC set. No "options to rule on" framed inside this
plan-doc.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape: dispatcher named the AC family,
the sealed-component fence, and the verification path. The strip
location (synth.py:302-312) is empirically pin-pointed by FBE.2's
status file. Tight scope. Method is inferable from the constraints.

### Lens 5 — Swarming
FBE.2b is a leaf in the foldback ladder. ACs do not partition
further: each binds to a single observable surface (synth source
edit, synth re-run output shape, individual test-file pass). No
sub-decomposition; the three test-file edits aren't worth
dispatching as parallel sub-agents (each is a single Edit pass;
coordination overhead exceeds tighter-AC payoff).

---

## 6. File-by-file map

### Source edits within sealed-component fence (`framework/tools/pos-publish-framework-only/`):

- `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py`:
  - Module docstring (lines 1-50): replace "promote `framework/<entry>` paths to root" language with "preserve canonical's `framework/<entry>` shape verbatim" language.
  - `_LeafEntry.synthetic_path` docstring (lines 163-180): replace "rewritten to `<rel>` at root" with "preserved verbatim from `source_path` for framework + top-level leaves alike."
  - `_build_synthetic_tree` docstring (lines 269-287): replace "rewrites `framework/<rel>` → `<rel>` at root" with "preserves the source path shape verbatim under the partition manifest."
  - Per-leaf path-shaping branch (currently lines 302-312): drop the `framework_prefix = f"{FRAMEWORK_PREFIX}/"` assignment, the `if source_path.startswith(framework_prefix)` strip branch, and the `elif source_path == FRAMEWORK_PREFIX` safety branch; replace with `synthetic_path = source_path` + a `saw_framework_leaf = saw_framework_leaf or source_path.startswith(f"{FRAMEWORK_PREFIX}/")` tracking line that preserves the existing "at least one framework/ leaf was emitted" semantic.
  - Comment update: the surrounding comment "Promote framework/<rel> to root; top-level entries verbatim." is replaced with "Preserve canonical's path shape; flag if at least one framework/ leaf is emitted (validation per saw_framework_leaf below)."
- `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/cli.py`:
  - `build_parser()` description string (lines 28-39): drop "promotes `framework/<entry>` to root" and "eliminating the `framework/framework/<comp>/` doubling failure class" — replace with single-clause description that the synthetic tree mirrors canonical's `framework/<comp>/` layout under the publish-mode partition manifest. Behaviour-relevant text (manifest path default, `pos-new-workspace --from <canonical>` workflow note) STAYS in adjusted form.

### Test edits within sealed-component fence (`framework/tools/pos-publish-framework-only/tests/`):

- `framework/tools/pos-publish-framework-only/tests/test_AC_SFR_2_synthesis_pipeline.py`:
  - Lines 73-75: `cost-governance/__init__.py` → `framework/cost-governance/__init__.py`; `workspace-bootstrap/src/__init__.py` → `framework/workspace-bootstrap/src/__init__.py`; `tools/loam-mode/__init__.py` → `framework/tools/loam-mode/__init__.py`.
  - Line 78-79: invert the "no doubled framework/ prefix" assertions — assert AT LEAST one `framework/`-prefixed leaf appears (positive shape check) AND no leaf starts with `framework/framework/` (collision-prevention check).
  - Lines 104-109 (HC#4 pairs): change the synth-side path in each pair to equal the source path verbatim (5 framework pairs become same-path pairs; 3 top-level pairs stay same-path as before).
  - Line 166: `cost-governance/added.py` → `framework/cost-governance/added.py`.
  - Line 263: stranger-clone byte-equality check stays unchanged (it reads canonical-side `framework/cost-governance/__init__.py` only).
  - The `test_synthesis_fails_when_framework_subdir_absent` test stays unchanged (the no-framework-leaves error path is preserved).
- `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_synthesis_drops_dev_only.py`:
  - Line 110-113: ships-paths assertions: `cost-governance/__init__.py` → `framework/cost-governance/__init__.py`; `CLAUDE.md`, `README.md`, `docs/positioning.md` STAY (top-level).
  - Line 116: `tools/loam/cli.py` → `framework/tools/loam/cli.py` in the drops-paths assertion.
  - Line 252-254: `.DS_Store` audit-exclude assertions: `cost-governance/.DS_Store` → `framework/cost-governance/.DS_Store`; `cost-governance/__init__.py` → `framework/cost-governance/__init__.py`.
- `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_M9_substitution_after_partition.py`:
  - Line 110: `tools/loam/cli.py` → `framework/tools/loam/cli.py` in the not-in-tree assertion.
  - Line 113: `cost-governance/__init__.py` → `framework/cost-governance/__init__.py` in the in-tree assertion.
  - Line 114: `tree_entries["cost-governance/__init__.py"]` → `tree_entries["framework/cost-governance/__init__.py"]`.

### NEW files under sealed-component fence (`framework/tools/pos-publish-framework-only/tests/`):

```
framework/tools/pos-publish-framework-only/
└── tests/
    ├── SEAL_COMMIT                                     # sidecar; written at apply-time
    └── test_no_sealed_amendments.py                    # AC.FBE.2b.9 + AC.FBE.2b.S; standard structural fence (mirrors FBE.2's loam-cli shape)
```

(Pre-existing: every `test_AC_*.py` file in `tests/` PLUS `conftest.py`, `__init__.py` (if any) STAY unchanged except for the three named AC test files above. Source under `src/loam/publish_framework_only/` STAYS unchanged except for `synth.py` + `cli.py`.)

### Plan-doc + manifest (universal_paths.prefixes: `docs/rebuild/plans/`):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2b.md` (this file).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2b.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` — §8
  method-decision register: NEW `### FBE.2b` entry with apply commit
  SHA + seal commit SHA + verification summary (between the existing
  FBE.5 and FBE.6 entries, or appended after FBE.7 — match the
  pattern parent uses).

**TOTAL fence diff:** 2 source-file edits (synth.py + cli.py) + 3
test-file edits (test_AC_SFR_2_synthesis_pipeline.py +
test_AC_OSS_3_synthesis_drops_dev_only.py +
test_AC_OSS_M9_substitution_after_partition.py) + 2 NEW sidecar
files (SEAL_COMMIT + test_no_sealed_amendments.py) — all within
`framework/tools/pos-publish-framework-only/`. Plan-doc + manifest
YAML + parent backfill ride via `docs/rebuild/plans/`
universal-paths.

---

## 7. Hard constraints

- Single sealed-component fence: `framework/tools/pos-publish-framework-only/`.
- The component's sidecar (`tests/SEAL_COMMIT` +
  `tests/test_no_sealed_amendments.py`) is established at FBE.2b
  (NEW seal anchor; mirrors FBE.2's loam-cli pattern).
- No partition manifest edits (AC.FBE.2b.10 negative).
- No edits outside the manifest-owner fence (no doc rewrites, no
  classifier edits, no other component touches).
- The synth still requires at least one `framework/` leaf
  (`saw_framework_leaf` semantic preserved; error message
  unchanged).
- `pos-amend` is the bookkeeping tool; `loam amend apply` runs once
  to advance sidecars + bump BASELINEs; corrective hand-admit if
  partner-prefix gap recurs (FBE.4/FBE.5 precedent).
- No `--amend` (per `feedback_no_amend_in_agent_dispatches` — new
  corrective commit if needed).
- No premature push (per dispatch — staging push is FBE.6's job).

---

## 8. Out of scope (per ODD §2.5)

- README / `docs/getting-started.md` / `docs/install-from-source.md`
  edits (already use `framework/<comp>/` paths; FBE.2b's purpose IS
  to align synth with these docs, not to modify docs).
- Any partition manifest content edits (path-shaping only).
- Re-staging the synth to a remote (FBE.6's job).
- Other components' descriptions / sources / tests.
- `partition.py` / `substitution.py` source edits.
- `pyproject.toml` edits to any component (no dependency / metadata
  changes).
- Establishing sidecars for other components that lack them
  (FBE.2b's fence is `pos-publish-framework-only/` only).

---

## 9. Halt-and-surface (during build)

- **Synth.py edit requires touching components beyond
  `pos-publish-framework-only/`** → halt + surface; that's a fence
  breach indicating the architecture isn't quite what the parent
  plan assumed.
- **Synth re-run fails after edit** → halt + surface; don't paper
  over.
- **Existing tests outside the named three fail post-edit** → halt
  + surface what tests + why (the named three are explicitly
  expected to need updates per AC.FBE.2b.5/6/7; surprises beyond
  these are halts).
- **Partner-prefix derivation gap recurs** → apply hand-corrective
  per FBE.4/FBE.5 precedent (FIDRAFT-tracked latent bug).
- **Build cycle exceeds 50 min wall-clock** → halt with partial
  findings.
- **WD drift to pos3** → halt immediately.
- **`saw_framework_leaf` semantic accidentally broken** (e.g.
  `test_synthesis_fails_when_framework_subdir_absent` starts failing
  or starts passing for the wrong reason) → halt; the negative test
  is the canary for the guard semantic.

---

## 10. Risks

1. **Cross-component sweep test sensitivity.** Other components'
   `test_no_sealed_amendments.py` files do NOT depend on synth-tree
   path shapes; FBE.2b's edit surface is purely inside the manifest-
   owner fence. Risk: low. Verified by spot-check: each fence-test
   asserts on `git diff --name-only` between BASELINE and SEAL_COMMIT
   — a path-shape-independent surface.
2. **`saw_framework_leaf` rewrite mistake.** The original guard was
   set inside the strip branch (`if source_path.startswith(framework_prefix): saw_framework_leaf = True`).
   The new code must preserve the "at least one framework/ leaf was
   emitted" check OUTSIDE the (now-removed) strip branch. Mitigation:
   set `saw_framework_leaf` inline alongside the unconditional
   `synthetic_path = source_path` assignment, with a `startswith(framework_prefix)` check for the truth value.
3. **Test-file edit drift.** The three test-file edits are mechanical
   path-string replacements — but the `test_AC_SFR_2_synthesis_pipeline.py`
   file's "no doubled framework/" assertion at line 78-79 needs
   inversion (not just replacement). Mitigation: read the assertion
   carefully + flip to "no `framework/framework/` doubling +
   at-least-one-framework/-prefixed-leaf." Spot-check all three test
   files post-edit via direct `pytest` per AC.FBE.2b.5/6/7.
4. **Partner-prefix gap recurs.** Per Surface #7. Mitigation: known
   pattern; corrective hand-admit per FBE.4/FBE.5 precedent.
5. **Apply-tool BASELINE bump on a NEW sidecar.** The
   `tests/SEAL_COMMIT` is established at FBE.2b (no prior value to
   bump from). The apply tool should write the BASELINE value
   (`<commit before apply>`) on first establishment, mirroring
   FBE.1/FBE.2's NEW-sidecar pattern. Mitigation: verify by reading
   FBE.2's apply commit + FBE.2's `test_no_sealed_amendments.py`
   `BASELINE = "8032348"` line shape.

---

## 11. Sequencing (commit ladder)

Pre-build state: canonical pos-v2 HEAD `8f3538a` (FBE.5 §8 register
backfill commit). Working tree clean per build-start verification.

1. **FBE.2b sub-plan-doc commit** (this file) — NEW commit (`docs(plans):`).
   Lands first per `feedback_plan_before_code`.
2. **FBE.2b source + test edit commit** — single combined commit
   carrying:
   - `synth.py` edit (drop strip + update docstrings + comment).
   - `cli.py` edit (drop description rationale).
   - `test_AC_SFR_2_synthesis_pipeline.py` edit (path-shape assertion updates + invert no-doubled-prefix assertion).
   - `test_AC_OSS_3_synthesis_drops_dev_only.py` edit (path-shape assertion updates).
   - `test_AC_OSS_M9_substitution_after_partition.py` edit (path-shape assertion updates).
   - NEW `tests/test_no_sealed_amendments.py` invariant.
   - NEW `tests/SEAL_COMMIT` sidecar (placeholder text per FBE.2 precedent — `loam amend apply` advances it).
   Subject: `feat(pos-publish-framework-only): FBE.2b — synth preserves framework/ prefix on shipped paths`.
3. **FBE.2b manifest commit** — NEW commit (`docs(plans):`)
   carrying the manifest YAML for amendment dispatch.
4. **`loam amend apply` commit** — bookkeeping commit advancing
   `tests/SEAL_COMMIT` sidecar from placeholder text to BASELINE
   (the pre-apply tip — i.e. the manifest commit's SHA) +
   `test_no_sealed_amendments.py` BASELINE literal bump if needed.
5. **Optional corrective hand-admit commit** (per Surface #7) — IFF
   `loam amend seal` fails on partner-prefix gap; admit
   `framework/tools/pos-publish-framework-only/` in the relevant
   `allowed_prefixes` list; subject: `fix(pos-publish-framework-only):
   FBE.2b — admit framework/tools/pos-publish-framework-only/ in
   fence-test allowed_prefixes`.
6. **`loam amend seal` commit** — deterministic; advances
   `tests/SEAL_COMMIT` sidecar to the seal SHA + runs touched-tests
   + cross-component sweep + post-seal `apply --dry-run` validation.
   Subject (auto): `chore(seals): v0-1-0-foldback-scope-expansion-fbe2b
   — pos-publish-framework-only at <BASELINE>`.
7. **Verification: synth re-run from canonical post-seal HEAD** —
   per AC.FBE.2b.4. Direct `synthesise_framework_only` invocation
   into a worktree at `/tmp/fbe2b-synth-verify/` (or in-place ref
   bump after backing up the prior `framework-only` ref) verifying
   `git ls-tree -r --name-only framework-only | head -20` shows
   `framework/`-prefixed paths.
8. **Parent plan-doc §8 backfill commit** — `docs(plans):`; appends
   FBE.2b apply + seal SHAs to the §8 method-decision register.
9. **Status file at
   `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe2b-status-2026-05-03.md`**
   — written outside canonical (mirrors FBE.{1,2,3,4,5,7} status-file
   shape).

---

## 12. References

- Parent plan: `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §3 Decision D + §4 register.
- FBE.2 status (Surface #1 + Risk #7 — synth strip rationale): `<workspace>/.scratch/claude-output/fbe2-status-2026-05-03.md`.
- FBE.2 sub-plan (sealed-component sidecar shape mirror): `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2.md`.
- FBE.2 manifest (universal-paths admission shape mirror): `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2.manifest.yaml`.
- FBE.2 sealed-component fence test (shape mirror for FBE.2b's NEW invariant): `framework/tools/loam/tests/test_no_sealed_amendments.py`.
- FBE.4 status (partner-prefix gap precedent — Surface #5): `<workspace>/.scratch/claude-output/fbe4-status-2026-05-03.md`.
- FBE.5 status (corrective hand-admit precedent + cross-component sweep): `<workspace>/.scratch/claude-output/fbe5-status-2026-05-03.md`.
- ODD methodology (no non-objective code): `docs/odd-methodology.md`.
- Reviewer dossier (HIGH 1 origin): `<workspace>/.scratch/claude-output/loam-user-review-2026-05-03.md`.
- Synth source (edit target): `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py`.
- Synth CLI (edit target): `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/cli.py`.

---

## 13. AI-time band

**Predicted: 25–45 min, midpoint 35 min.** Justification: single
sealed-component fence with both source and test edits; ~6 file
edits (2 source + 3 test + 1 sub-plan + 1 manifest + 2 NEW sidecar
files = 9 file touches) + a synth re-run verification + partner-
prefix corrective if needed. Per rubric "single-component amendment
10–20 min" + "establishment of NEW sidecar component anchor +
rebuild + re-run" pushes upper-bound. ~80–130 tool calls. Formula
`wall_clock_minutes ≈ 0.1–0.15 × tool_calls` predicts 8–20 min from
tool-call count; widen to 25–45 min for the synth-re-run + corrective
hand-admit overhead. Hard cap (per dispatch): 50 min.

---

## 14. Method-decision register (post-build)

(Populated post-seal — apply commit SHA + seal commit SHA + ACs satisfied + halt-and-surface notes for the dispatcher.)
