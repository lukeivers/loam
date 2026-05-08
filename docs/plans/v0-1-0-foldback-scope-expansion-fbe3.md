# FBE.3 sub-plan — Partition split-admit `plugins/dev-sdlc/**` (plugin source ships, dev-discipline doesn't)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/plans/v0-1-0-foldback-scope-expansion.md` §4 FBE.3 + §3 Decision B.2 (B.alt = SHIP).
**Programme master:** `docs/plans/oss-v0-1-0-publish.md`.
**Predecessors:**
- FBE.1 sealed at `21b9480` (loam-init NEW component).
- FBE.2 sealed at `8d2b770` (loam-cli reclassified dev_only→dev_and_public).
- FBE.7 sealed at `a102bde` (graphiti dropped from v0.1.0 first-run shape).
**BASELINE:** `88d4ebe` — current canonical pos-v2 HEAD pre-FBE.3 (the FBE.7 §8 backfill commit).

---

## 1. Summary / TLDR

Per parent plan §3 Decision B.2 + Decision B.alt (ruled SHIP at v0.1.0
because the contribution-protocol demo matters more than text-only
reference): split the partition admission for `plugins/dev-sdlc/`
into two parts.

- **`dev_and_public` (ships):** `plugins/dev-sdlc/src/**`,
  `plugins/dev-sdlc/pyproject.toml`, `plugins/dev-sdlc/README.md`.
- **`dev_only` (stays):** `plugins/dev-sdlc/docs/**`,
  `plugins/dev-sdlc/hooks/**`, `plugins/dev-sdlc/templates/**`,
  `plugins/dev-sdlc/tools/**`, `plugins/dev-sdlc/dev-mode-manifest.yaml`.
  - `plugins/dev-sdlc/seals/**` already covered by `**/seals/**`.
  - `plugins/dev-sdlc/tests/**` already covered by `**/tests/**`.

The pre-existing universal `**/seals/**` and `**/tests/**` precedence
rules (manifest precedence rule #2 — `dev_only` checked before
`dev_and_public`) continue to win for the `seals/` + `tests/`
subtrees of the plugin without any new entries needed.

`plugins/dev-sdlc/` is ALREADY a sealed component (existing
sidecar at `plugins/dev-sdlc/tests/SEAL_COMMIT`, existing fence test
at `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`). FBE.3
bumps both via `loam amend apply` + `loam amend seal` per the
standard sealed-component cycle — no new sidecar shape needed.

Closes BLOCKER 2 (the dev-sdlc plugin half) of the v0.1.0 reviewer
foldback. Pairs with FBE.2 (CLI binary half).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 — Plugin's `src/` has zero dev-only imports (HALT TRIGGER VERIFIED BENIGN)

Dispatch halt-trigger #1: "Plugin's `src/` imports modules from
`tools/loam-amend/` or other dev-only paths → halt + surface".

Verified at planning via `grep -rE "from loam|import loam"
plugins/dev-sdlc/src/`:

- `plugins/dev-sdlc/src/loam/plugins/dev_sdlc/api.py`:
  imports from `loam.scope_of_work.spec` + `loam.objective_tracker.spec`.
- `plugins/dev-sdlc/src/loam/plugins/dev_sdlc/contribution.py`:
  imports from `loam.workspace_bootstrap.spec`.

All three target packages are `dev_and_public` runtime components
(verified in canonical manifest) — `framework/scope-of-work/`,
`framework/objective-tracker/`, `framework/workspace-bootstrap/`. Zero
imports of `loam_amend`, `loam_mode`, or anything under
`plugins/dev-sdlc/tools/`. The plugin's `src/` is cleanly separable
from its dev-discipline subtree. No ODD §2.5 violation surfaced.

### Surface #2 — Plugin's `pyproject.toml` `package-dir` survives the dev-discipline subtree dropping (HALT TRIGGER VERIFIED BENIGN)

Dispatch halt-trigger #2: "Plugin's `pyproject.toml`'s package-dir
layout breaks when dev-discipline subtree disappears → halt".

Verified at planning by reading
`plugins/dev-sdlc/pyproject.toml:39-45`:

```toml
[tool.setuptools]
package-dir = {"loam.plugins.dev_sdlc" = "src/loam/plugins/dev_sdlc"}
packages = ["loam.plugins.dev_sdlc"]
include-package-data = true

[tool.setuptools.package-data]
"loam.plugins.dev_sdlc" = ["templates/*.md"]
```

The package-dir resolves to `src/loam/plugins/dev_sdlc` only — does
NOT reach into `docs/`, `hooks/`, `templates/` (top-level), `tools/`,
or `dev-mode-manifest.yaml`. The `templates/*.md` package-data glob
is RELATIVE TO THE PACKAGE (resolves to
`src/loam/plugins/dev_sdlc/templates/*.md` — the 5 ODD-stage
templates physically nested inside the package, NOT to the top-level
`plugins/dev-sdlc/templates/` dispatch/plan/component templates).
Verified via `find plugins/dev-sdlc/src/loam/plugins/dev_sdlc/templates/
-name '*.md'` — 5 odd-*.md files exist there. `pip install -e
plugins/dev-sdlc` post-FBE.3 will resolve cleanly.

### Surface #3 — Synth strips only `framework/` prefix; `plugins/` paths land at `plugins/...` (NO HALT, RECORDED)

Per FBE.2 sub-plan §2 Surface #1: `synth.py:302-312` strips
`framework/` prefix only. Verified at planning via `grep -nE
"plugins/dev-sdlc|^FRAMEWORK_PREFIX|frame.*prefix"
framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py`:
the strip targets `FRAMEWORK_PREFIX = "framework"` exclusively. The
`plugins/...` tree is NOT subject to any prefix-stripping. Post-FBE.3,
the plugin will land at the synth path `plugins/dev-sdlc/{src,
pyproject.toml, README.md}` — directly mirrors the canonical layout.
This is different from FBE.2's `tools/loam/` synth path (which DID get
the prefix stripped from `framework/tools/loam/`) — so the install
command in synth-tree shape is `pip install -e plugins/dev-sdlc`
(matches what the README and getting-started.md already document).

Decision D in parent plan §3 (preserve `framework/` prefix on
synthesised paths) remains out of FBE.3 scope; this surface is
recorded for downstream awareness only. No FBE.2-style README-vs-synth
shape mismatch on the plugin path.

### Surface #4 — Existing partition tests need 3 spot-check edits (RECORDED)

Verified via `grep -lrE "plugins/dev-sdlc"
framework/tools/pos-publish-framework-only/tests/`:

- **`test_AC_OSS_3_default_partition_complete.py:159-162`** (4 entries
  in `sample_dev_only_paths`): `plugins/dev-sdlc/docs/odd-methodology.md`,
  `plugins/dev-sdlc/docs/odd-in-loam.md`,
  `plugins/dev-sdlc/tools/loam-mode/pyproject.toml`,
  `plugins/dev-sdlc/dev-mode-manifest.yaml`. **All 4 stay dev_only
  post-FBE.3** (every one falls under the new explicit dev_only
  globs). NO edit needed to this test file. The symmetric
  `sample_runtime_paths` block at lines 100-130 ADDS 3 new entries:
  `plugins/dev-sdlc/pyproject.toml`,
  `plugins/dev-sdlc/README.md`,
  `plugins/dev-sdlc/src/loam/plugins/dev_sdlc/api.py` —
  to verify the new dev_and_public admission classifies correctly.

- **`test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py`**: this
  is the test that's most affected. The function
  `test_canonical_manifest_classifies_plugin_files` (lines 86-127)
  iterates EVERY file under `plugins/dev-sdlc/` and asserts each
  classifies as `DEV_ONLY`. Post-FBE.3, this assertion FAILS for
  `src/**`, `pyproject.toml`, `README.md`. Update the assertion logic
  to evaluate the per-subtree classification: `src/` + `pyproject.toml`
  + `README.md` → DEV_AND_PUBLIC; everything else → DEV_ONLY (modulo
  `**/tests/**` + `**/seals/**` precedence which also returns DEV_ONLY).
  The existing inline narrative comments (lines 115-126) that explain
  M6a baseline → M6b.0 reclassification gain a third paragraph
  documenting FBE.3 split-admit per parent plan §3 Decision B.2.
  The test function `test_plugins_dev_sdlc_classifies_dev_and_public`
  (lines 53-83) uses a SYNTHETIC manifest (independent of canonical
  state) — no edit needed.

- **`test_AC_OSS_M9_substitution_smoke.py:50-51`** asserts
  `plugins/dev-sdlc/docs/odd-methodology.md` +
  `plugins/dev-sdlc/docs/odd-in-loam.md` are present in
  `SUBSTITUTION_TABLE` sources. These are substitution-table source
  literals (token replacement targets), NOT classification assertions.
  No edit needed; FBE.3 doesn't touch the substitution table.

All 3 test-touching edits land within the manifest-owner fence at
`framework/tools/pos-publish-framework-only/tests/` — admitted via
`universal_paths.prefixes` at the manifest level (mirrors FBE.1 +
FBE.2's pattern).

### Surface #5 — `plugins/dev-sdlc/` is an EXISTING sealed component (NO HALT, RECORDED)

Unlike FBE.1 (which authored a NEW sealed-component anchor for
loam-init) and FBE.2 (which established a NEW anchor for loam-cli),
the dev-sdlc plugin already has a sealed-component shape from M6a:

- Sidecar: `plugins/dev-sdlc/tests/SEAL_COMMIT` exists (current
  value `54794d7b08080f4e87315a81eadcadf292eb4bb9`).
- Fence test: `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`
  exists with `BASELINE = "699a391"` (M5 §14 backfill).
- 4 historical seal narratives at `plugins/dev-sdlc/seals/SEAL_COMMIT.*`.

FBE.3's `loam amend apply` will bump the sidecar to FBE.3's BASELINE,
then `loam amend seal` advances it to the FBE.3 seal SHA. The fence
test's `BASELINE = "699a391"` constant DOES need to be updated to
FBE.3's BASELINE for the post-seal diff window to be FBE.3-scoped (not
M5-to-FBE.3-scoped). This is a one-line edit inside the
`plugins/dev-sdlc/tests/` directory (within the sealed-component
fence — admitted by definition).

The fence test's existing `allowed_prefixes` tuple is M6a-flavoured
and admits a wide set of cross-component partner prefixes (every
framework component) — generous enough that FBE.3's narrow change
(within the plugin + manifest-owner) will not trip it.

### Surface #6 — Pre-existing dirty `docs/FUTURE_IDEAS_DRAFT.md` may block `loam amend seal` (RECORDED)

Per dispatch and per FBE.2/FBE.7 status reports: at dispatch start the
working tree shows `docs/FUTURE_IDEAS_DRAFT.md` as modified
(parent-session edit, unrelated to FBE.3). Both FBE.2 and FBE.7
stash-then-pop'd around it cleanly. FBE.3 mirrors the pattern if
`loam amend seal` complains about a dirty tree.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per
  `docs/VALUE_PROPOSITION.md`) — the dev-sdlc plugin is the
  flagship demo of loam's contribution-protocol; without it shipping,
  the protocol is text-only and the harness's "primary persona +
  contributable plugins" claim is unverifiable by a stranger.
- **Reviewer foldback BLOCKER 2** (parent §2.2): "`dev-sdlc` plugin
  doesn't ship". FBE.3 closes the plugin half (FBE.2 closed the CLI
  binary half).
- **AC.OSS-M6.1 + AC.OSS-M6.6** — the plugin's
  `loam.bootstrap.contributions` + `loam.cli.subcommands` entry-point
  registrations are the live demo of the contribution-protocol; both
  are exposed by the plugin's `pyproject.toml` (which now ships) +
  `src/` (which now ships).

**Ladders to:** AC.FBE.3.* → AC.OSS-M11a.* (FBE.6 reviewer GO) → M12
publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.3.*)

AC family **`AC.FBE.3.*`** — collision-safe (verified: `grep -rE
"AC\.FBE\.3" docs/` returns only the parent foldback plan-doc).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.3.1** | `publish-mode-manifest.yaml`'s `dev_only:` block REMOVES the broad `glob: "plugins/dev-sdlc/**"` entry (currently the last entry in the block, line ~311) + adds a multi-line provenance comment naming FBE.3 + the foldback parent plan-doc above the removal. | `grep -A1 'plugins/dev-sdlc' framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` returns the broad `**` glob entry NO LONGER under `dev_only:`. |
| **AC.FBE.3.2** | `dev_and_public:` block ADDS THREE entries with provenance comment: `glob: "plugins/dev-sdlc/src/**"` + `path: plugins/dev-sdlc/pyproject.toml` + `path: plugins/dev-sdlc/README.md`. | Direct `grep` for each + `pytest test_AC_OSS_3_partition_classifier.py` (synthetic-fixture tests pass independently). |
| **AC.FBE.3.3** | `dev_only:` block ADDS FIVE explicit subtree entries with provenance comment: `glob: "plugins/dev-sdlc/docs/**"` + `glob: "plugins/dev-sdlc/hooks/**"` + `glob: "plugins/dev-sdlc/templates/**"` + `glob: "plugins/dev-sdlc/tools/**"` + `path: plugins/dev-sdlc/dev-mode-manifest.yaml`. (Pre-existing universal `**/seals/**` + `**/tests/**` continue to cover those two subtrees per partition-precedence rule #2 — no new entries for those.) | Direct `grep`. |
| **AC.FBE.3.4** | Pre-existing universal globs `**/seals/**` + `**/tests/**` continue to win for `plugins/dev-sdlc/seals/**` + `plugins/dev-sdlc/tests/**` per partition-precedence rule #2 (dev_only checked before dev_and_public). | `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_partition_classifier.py` passes; spot-check `classify_path(manifest, "plugins/dev-sdlc/tests/test_AC_OSS_M6_1_contribution_discovers_via_entry_point.py")` returns `DEV_ONLY`. |
| **AC.FBE.3.5** | Synth re-run from canonical pos-v2 HEAD (post-FBE.3-seal) produces a `framework-only` tree containing `plugins/dev-sdlc/{src/**, pyproject.toml, README.md}` and ZERO files under `plugins/dev-sdlc/{docs/**, hooks/**, templates/**, tools/**, seals/**, tests/**, dev-mode-manifest.yaml}`. The post-strip path shape `plugins/dev-sdlc/...` (NO prefix-strip — `synth.py` strips only `framework/`) matches Surface #3's documented synth behaviour. | Run synth via direct `synthesise_framework_only` invocation post-seal; `git ls-tree -r --name-only framework-only \| grep -E '^plugins/dev-sdlc/'` returns: 1 pyproject.toml + 1 README.md + the `src/loam/plugins/dev_sdlc/{__init__,api,cli,contribution,errors,observability,stages,store}.py` files (8 source modules) + 5 `src/loam/plugins/dev_sdlc/templates/odd-*.md` files. **Total expected: 15 leaves.** Negative: zero `docs/`, `hooks/`, `templates/` (top-level), `tools/`, `seals/`, `tests/`, `dev-mode-manifest.yaml`. |
| **AC.FBE.3.6** | The audit-completeness test `test_AC_OSS_3_default_partition_complete.py` continues to pass for canonical pos-v2 HEAD post-FBE.3. The spot-check `test_default_partition_classifies_runtime_components_dev_and_public` UPDATED to add `plugins/dev-sdlc/pyproject.toml` + `plugins/dev-sdlc/README.md` + `plugins/dev-sdlc/src/loam/plugins/dev_sdlc/api.py` to `sample_runtime_paths`; the symmetric `sample_dev_only_paths` block keeps its 4 dev-sdlc entries (all fall under the new explicit dev_only globs and continue to classify dev_only). | `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py` returns 3/3 pass. |
| **AC.FBE.3.7** | The plugin-classification test `test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py::test_canonical_manifest_classifies_plugin_files` UPDATED to evaluate per-subtree expectations (NOT the M6b.0 blanket `dev_only` assertion). Function rewrite: for each plugin file, compute expected class from path prefix (`src/**` + `pyproject.toml` + `README.md` → DEV_AND_PUBLIC; everything else → DEV_ONLY); assert classification matches. The two synthetic-manifest tests in the same file (`test_canonical_manifest_admits_plugins_in_audit_roots` + `test_plugins_dev_sdlc_classifies_dev_and_public`) stay byte-identical (they test invariant manifest properties — `plugins/` in audit_roots + a synthetic dev_and_public manifest classifies plugin paths correctly). | `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py` returns 3/3 pass. |
| **AC.FBE.3.8** | `pip install -e plugins/dev-sdlc` against the canonical pos-v2 tree (with sibling `framework/scope-of-work`, `framework/objective-tracker`, `framework/workspace-bootstrap` already installed) resolves cleanly. The bare-name deps stay bare (FBE.4 will rewrite to path-specs). | At build time, run `.venv/bin/pip install --dry-run -e plugins/dev-sdlc` (or full install in a scratch venv if dry-run unavailable) — exit 0; package-dir resolves to `src/loam/plugins/dev_sdlc` per `pyproject.toml:40`. |
| **AC.FBE.3.9** | Negative AC: zero changes to plugin SOURCE files (`plugins/dev-sdlc/src/**`, `plugins/dev-sdlc/pyproject.toml`, `plugins/dev-sdlc/README.md`). Zero changes to plugin dev-discipline files (`docs/**`, `hooks/**`, `templates/**`, `tools/**`, `dev-mode-manifest.yaml`, `seals/**`). FBE.3 is partition-only + sealed-component cycle bookkeeping. | `git diff BASELINE..SEAL_COMMIT -- plugins/dev-sdlc/src/ plugins/dev-sdlc/pyproject.toml plugins/dev-sdlc/README.md plugins/dev-sdlc/docs/ plugins/dev-sdlc/hooks/ plugins/dev-sdlc/templates/ plugins/dev-sdlc/tools/ plugins/dev-sdlc/dev-mode-manifest.yaml plugins/dev-sdlc/seals/` returns empty. |
| **AC.FBE.3.S** | Sealed-component fence: `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under `plugins/dev-sdlc/` (the sealed component — sidecar bump + fence-test BASELINE bump) + `framework/tools/pos-publish-framework-only/` (manifest owner: 2-section partition-manifest edit + 2 test fixture spot-check edits) + `docs/plans/` (universal_paths.prefixes; sub-plan + manifest YAML + parent plan-doc backfill). | `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` invariant + manual `git diff --name-only` check at seal time. |

**ACs deliberately out of scope (NOT in FBE.3):**
- Path-spec dep rewrite for the plugin's 3 inter-component deps
  (`loam-scope-of-work`, `loam-objective-tracker`,
  `loam-workspace-bootstrap`) — that's FBE.4.
- Plugin pyproject `description` field scrub (`loam project ...` /
  "First plugin" / "v0.2+ plugins" wording is fine but the field
  should be re-read at FBE.5 against the dev-vocabulary scrub list).
  FBE.5's scope.
- Plugin README scrub — FBE.5 sweep.
- `loam amend` console-script shipping — explicitly OUT per parent
  plan §3 Decision B.2 (the tool stays in `plugins/dev-sdlc/tools/`
  which is `dev_only` post-FBE.3).
- Synth pipeline path-rewrite (Decision D) — irrelevant for `plugins/`
  paths anyway (no prefix strip applies).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
Pure manifest reclassification + standard sealed-component cycle; no
Claude-native primitive in scope. Composes on the established
partition-shape pattern (M2 manifest-driven synth) + the sealed-component
sidecar/fence-test pattern (post-amendment-#22 + FBE.1 + FBE.2
precedents).

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The dev-sdlc plugin IS the flagship
  contribution-protocol demo; without it shipping, the harness's
  contributable-plugins claim is text-only. FBE.3 makes the plugin
  reachable in the synth tree.
- **Harness test:** PASS. The plugin adds the `loam project` verb to
  the user-facing CLI dispatcher (registered via
  `loam.cli.subcommands` entry-point). Admitting the plugin to ship
  is a direct toolkit expansion for the primary persona.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which YAML lines move where, which
provenance-comment shape is used) is builder's call, but inferable
from the FBE.1 + FBE.2 precedents without being prescribed. No
"options to rule on" framed inside this plan-doc.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape (parent plan locks Decision B.2 +
B.alt = SHIP; FBE.1 + FBE.2 established the partition-admit pattern at
sealed-time; the sealed-component cycle for an existing component is
mechanical via `loam amend apply` + `loam amend seal`). Tight scope.
ACs name observable outputs; method inferable from the FBE.1/FBE.2
precedents.

### Lens 5 — Swarming
FBE.3 is one of six FBE.* amendments (parent's planner-output). The
FBE.3 ACs do not partition further — every AC binds to a single
observable surface (manifest line removals, manifest line additions,
test fixture edits, sealed-component fence diff, synth-tree shape,
pip install resolution). Each is leaf-scoped. No sub-decomposition.

---

## 6. File-by-file map

### Edits within the sealed-component fence (`plugins/dev-sdlc/`):

- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`:
  - `BASELINE = "699a391"` → `BASELINE = "<FBE.3 BASELINE SHA>"`
    (one-line literal swap — `loam amend apply` updates it
    automatically; the `_seal_commit()` resolution mechanism stays
    byte-identical).
- `plugins/dev-sdlc/tests/SEAL_COMMIT`:
  - Current value `54794d7b08080f4e87315a81eadcadf292eb4bb9` →
    bumped to FBE.3 BASELINE SHA at apply, then to FBE.3 seal SHA at
    seal (standard `loam amend apply` + `loam amend seal` sidecar
    bump pattern).
- `plugins/dev-sdlc/tests/SEAL_COMMIT.notes`:
  - NEW or appended file at `loam amend seal` time with the FBE.3
    narrative body (per `narrative.target` in the manifest YAML).

### Edits within manifest-owner fence (`framework/tools/pos-publish-framework-only/`):

- `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`:
  - REMOVE `- glob: "plugins/dev-sdlc/**"` from `dev_only:` (currently
    the last block entry, ~line 311).
  - REPLACE the M6b.0 dev_only narrative comment block (lines ~297-310)
    with a FBE.3 split-admit narrative (5 explicit dev_only sub-tree
    entries + provenance crumb pointing to the dev_and_public block).
  - ADD to `dev_and_public:` block (insert before the
    `framework/tools/loam/**` entry per alphabetical-ish ordering, OR
    at the end of the block immediately before the M6b.0 block-trailing
    comment; pick whatever reads cleanly):
    - `- glob: "plugins/dev-sdlc/src/**"`
    - `- path: plugins/dev-sdlc/pyproject.toml`
    - `- path: plugins/dev-sdlc/README.md`
    - With a multi-line provenance comment naming FBE.3 + parent
      plan + the split-admit shape per Decision B.2.
  - ADD to `dev_only:` block:
    - `- glob: "plugins/dev-sdlc/docs/**"`
    - `- glob: "plugins/dev-sdlc/hooks/**"`
    - `- glob: "plugins/dev-sdlc/templates/**"`
    - `- glob: "plugins/dev-sdlc/tools/**"`
    - `- path: plugins/dev-sdlc/dev-mode-manifest.yaml`
    - With a multi-line provenance comment naming FBE.3 + parent
      plan + the precedence-rule note (`**/seals/**` + `**/tests/**`
      continue to win for those subtrees per rule #2; not re-listed).

- `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py`:
  - In `test_default_partition_classifies_runtime_components_dev_and_public`'s
    `sample_runtime_paths` list (currently lines 114-124): ADD 3 new
    entries with FBE.3 inline comment:
    - `"plugins/dev-sdlc/pyproject.toml"`
    - `"plugins/dev-sdlc/README.md"`
    - `"plugins/dev-sdlc/src/loam/plugins/dev_sdlc/api.py"`
  - The `sample_dev_only_paths` list keeps its 4 dev-sdlc entries
    (no edit needed; they all classify dev_only post-FBE.3 via the
    new explicit globs).

- `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py`:
  - In `test_canonical_manifest_classifies_plugin_files` (lines 86-127):
    Replace the blanket `assert cls == PartitionClass.DEV_ONLY`
    assertion with per-subtree expected-class logic:
    ```
    if rel == "plugins/dev-sdlc/pyproject.toml" or rel == "plugins/dev-sdlc/README.md" or rel.startswith("plugins/dev-sdlc/src/"):
        expected = PartitionClass.DEV_AND_PUBLIC
    else:
        expected = PartitionClass.DEV_ONLY
    assert cls == expected, ...
    ```
  - Update the inline narrative comment block to add a third paragraph
    documenting FBE.3 split-admit per parent plan §3 Decision B.2.
  - The two other test functions in the file stay byte-identical.

### Plan-doc + manifest (universal_paths.prefixes: `docs/plans/`):

- `docs/plans/v0-1-0-foldback-scope-expansion-fbe3.md` (this file).
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe3.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/plans/v0-1-0-foldback-scope-expansion.md` — §8
  method-decision register entries: apply commit SHA + seal commit
  SHA for FBE.3.

**TOTAL fence diff:** sidecar bump + fence-test BASELINE bump (within
plugin fence) + ~15-line manifest YAML edit + ~5-line test fixture
edit + ~5-line plugin-classification test rewrite (within manifest-
owner fence) + plan-doc + manifest YAML (universal-admitted) + parent
plan-doc backfill (universal-admitted).

---

## 7. Hard constraints

- Two sealed-component fence: `plugins/dev-sdlc/` (the reclassified
  plugin, EXISTING seal anchor — sidecar bump per the
  dev_only→dev_and_public split-reclassification convention) +
  `framework/tools/pos-publish-framework-only/` (manifest owner;
  rides via `universal_paths.prefixes` per FBE.1 + FBE.2 precedent —
  the manifest owner does NOT have its own SEAL_COMMIT sidecar in the
  sense of a frozen seal anchor; it's a runtime-tested component whose
  edits ride universally).
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per
  `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.3.*` (collision-safe; verified).
- Auto-memory `MEMORY.md` NOT touched.
- Zero edits to plugin SOURCE files (AC.FBE.3.9 forbids).
- Zero edits to other plugins' / components' source.
- Component-scoped test rerun only per
  `feedback_amendment_dispatch_speedups`:
  - `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` (the fence
    test).
  - `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py`
    (audit-completeness + spot-checks).
  - `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py`
    (the dev-sdlc-specific classification test — touched).
  - `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_partition_classifier.py`
    (precedence-rule verification — verifies `**/seals/**` +
    `**/tests/**` win over the new dev_and_public src admission).
  NOT the full canonical sweep.

---

## 8. Out of scope (per ODD §2.5)

- Path-spec dep rewrite for plugin's 3 inter-component deps — FBE.4.
- Plugin pyproject `description` scrub — FBE.5.
- Plugin README scrub — FBE.5.
- Plugin source edits — partition-only amendment.
- `loam amend` console-script shipping — explicitly out per parent
  Decision B.2 (stays at `plugins/dev-sdlc/tools/loam-amend/` →
  `plugins/dev-sdlc/tools/**` glob → dev_only).
- Synth pipeline path-rewrite (Decision D) — `plugins/` not affected.
- Touching `**/seals/**` or `**/tests/**` precedence rules (M11a Class
  A/B locks; stay).

---

## 9. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not
silently extend) on:

- **HT-1:** Plugin's `src/` is discovered to import a dev-only module
  during build (e.g. a runtime import not visible to grep). Mitigation:
  verified at planning via grep. Should not trigger.
- **HT-2:** `pip install -e plugins/dev-sdlc` against the canonical
  tree fails. Surface; the package-dir layout is broken or a sibling
  install is missing.
- **HT-3:** Audit-completeness test fails post-reclassification with a
  leaf path that was previously absorbed by the broad
  `plugins/dev-sdlc/**` dev_only glob and now lacks classification
  (impossible because the new explicit `src/`/`docs/`/etc. globs cover
  every subtree the old broad glob did + they're symmetric — but
  verify empirically). Surface; the manifest is mis-shaped.
- **HT-4:** Partition-precedence test fails — i.e. some path under
  `plugins/dev-sdlc/seals/` or `plugins/dev-sdlc/tests/` classifies
  `DEV_AND_PUBLIC` instead of `DEV_ONLY` (would mean `**/seals/**` or
  `**/tests/**` precedence isn't winning, which would be a deeper
  partition-engine bug not introduced by FBE.3). Surface.
- **HT-5:** A NEW spot-check test or an unanticipated assertion
  references a `plugins/dev-sdlc/...` path and silently breaks.
  Mitigation: verified at planning that 3 test files reference the
  path (Surface #4); only the M6_8 test needs assertion-logic update.
  At build time, re-grep + re-read all 3 to confirm.
- **HT-6:** `loam amend apply` against the FBE.3 manifest fails with
  a fence breach diagnostic. Surface; the manifest's
  `extra_allowed_files` / `universal_paths` block needs adjustment
  (or the `extra_allowed_prefixes` for the dev-sdlc component).
- **HT-7:** `loam amend seal` complains about dirty
  `docs/FUTURE_IDEAS_DRAFT.md` (per Surface #6). Mitigation:
  stash-then-pop pattern from FBE.2 + FBE.7; surface as a procedural
  note.
- **HT-8:** Wall-time exceeds 80 min (parent plan band 30–60 min,
  midpoint 45 min; 80 min is the dispatch-imposed hard cap). Surface
  partial findings + named what's left.
- **HT-9:** A surrounding-code ODD §2.5 violation discovered in the
  plugin source or `pos-publish-framework-only/` source during the
  build. Surface; do NOT silently extend or fix in-band.
- **HT-10:** Synth re-run for AC.FBE.3.5 fails (e.g. partition mis-
  shape causes SynthesisError, OR a `plugins/...` path gets the
  `framework/` prefix-strip applied to it surprisingly — would be a
  synth-pipeline bug). Surface; if it's a synth bug, defer to
  FBE.2b territory; do NOT auto-fold into FBE.3.
- **HT-11:** WD drifts to pos3. Halt immediately.
- **HT-12:** Sealed-component fence breach beyond the two named
  components. Halt + surface.

---

## 10. Risks

- **Risk: post-FBE.3 the README's `pip install -e plugins/dev-sdlc`
  command in the synth tree finds the plugin but the bare-name
  `loam-scope-of-work` / `loam-objective-tracker` /
  `loam-workspace-bootstrap` deps don't resolve (PyPI bare names
  unpublished).** Mitigation: known issue — FBE.4 owns the path-spec
  rewrite; FBE.6's extended smoke verifies the install ordering works.
  Document for downstream.
- **Risk: a stranger doing `pip install -e plugins/dev-sdlc` post-
  FBE.3 + FBE.4 successfully imports the plugin but invocation of
  `loam project ...` fails because the loam-cli binary (FBE.2) +
  loam-init (FBE.1) + workspace-bootstrap (FBE.7-modified) all need
  to be installed first.** Mitigation: known multi-step install
  ordering; AC.FBE.4.7 owns the documented install order; AC.FBE.6.3
  owns the smoke verification.
- **Risk: the plugin's
  `src/loam/plugins/dev_sdlc/templates/odd-*.md` are
  package-data per `pyproject.toml:44-45`; if the
  setuptools-package-data resolution mechanism doesn't pick them up
  in synthesised tree (e.g. `MANIFEST.in` missing), `loam project new
  --stage research` would fail to find the template.** Mitigation:
  package-data is declared in `pyproject.toml` itself (modern
  setuptools); no `MANIFEST.in` needed. Verify at build by checking
  the synth tree carries the 5 `templates/odd-*.md` files inside
  `src/`. (Already in AC.FBE.3.5's expected-leaves count.)
- **Risk: the M6_8 test's rewrite of
  `test_canonical_manifest_classifies_plugin_files` introduces a
  subtle bug in the per-subtree expected-class logic that admits a
  bad classification.** Mitigation: review the rewrite in main
  before commit; the logic is 4 lines (early-return on
  `pyproject.toml` / `README.md` / `src/`-prefix → DEV_AND_PUBLIC,
  fallthrough → DEV_ONLY).
- **Risk: dev-sdlc plugin's
  `tests/test_no_sealed_amendments.py` `allowed_prefixes` tuple is
  M6a-flavoured + admits framework component prefixes that don't
  apply to FBE.3's diff (the `framework/cost-governance/`,
  `framework/dormancy/`, etc. lines). FBE.3's actual diff is much
  narrower. The over-permissive admission won't cause a failure but
  is technically a stale shape.** Mitigation: NOT in FBE.3 scope to
  prune; the over-permissive shape is M6a's authoring decision and
  doesn't block FBE.3. Surface for downstream cleanup if/when an
  amendment touches the fence test for substantive reasons.

---

## 11. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Partition-admission commit** — edit `publish-mode-manifest.yaml`
   (REMOVE the broad `dev_only` `plugins/dev-sdlc/**` glob; ADD 3 new
   `dev_and_public` entries; ADD 5 new `dev_only` subtree entries +
   provenance comments at all edit sites) + edit
   `test_AC_OSS_3_default_partition_complete.py` (3 entries added to
   `sample_runtime_paths`) + edit
   `test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py` (per-
   subtree assertion logic for `test_canonical_manifest_classifies_plugin_files`
   + narrative comment update). Verify
   `pytest test_AC_OSS_3_default_partition_complete.py
   test_AC_OSS_M6_8_partition_includes_dev_sdlc_plugin.py
   test_AC_OSS_3_partition_classifier.py` passes.
3. **Manifest commit** — author
   `docs/plans/v0-1-0-foldback-scope-expansion-fbe3.manifest.yaml`.
4. **`loam amend apply`** — invoke against the manifest. Produces
   the apply-bookkeeping commit (BASELINE bump in
   `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`, sidecar bump
   in `plugins/dev-sdlc/tests/SEAL_COMMIT`).
5. **`loam amend seal`** — produces the deterministic seal commit;
   sidecar `SEAL_COMMIT` advances to the seal SHA; narrative file
   updated (or appended) at `tests/SEAL_COMMIT.notes`.
6. **Parent plan-doc backfill** —
   `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 FBE.3
   entries get the apply + seal SHAs (separate NEW commit; admitted
   via `docs/plans/` universal prefix).
7. **Status file** — write
   `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe3-status-2026-05-03.md`
   (outside canonical tree; the dispatcher reads it).

NO `git commit --amend` at any point. NO push to any remote.

---

## 12. References

- **Parent plan:** `docs/plans/v0-1-0-foldback-scope-expansion.md`
  §4 FBE.3 + §3 Decision B.2 + Decision B.alt.
- **Reviewer foldback dossier:**
  `<workspace>/.scratch/claude-output/loam-user-review-2026-05-03.md`
  BLOCKER 2.
- **FBE.1 status (precedent — partition admission for NEW component):**
  `<workspace>/.scratch/claude-output/fbe1-status-2026-05-03.md`.
- **FBE.2 status (precedent — partition reclassification + sidecar
  establishment):**
  `<workspace>/.scratch/claude-output/fbe2-status-2026-05-03.md`.
- **FBE.7 status (precedent — most recent sealed-component cycle):**
  `<workspace>/.scratch/claude-output/fbe7-status-2026-05-03.md`.
- **FBE.1 sub-plan:**
  `docs/plans/v0-1-0-foldback-scope-expansion-fbe1.md`.
- **FBE.2 sub-plan (closest shape):**
  `docs/plans/v0-1-0-foldback-scope-expansion-fbe2.md`.
- **FBE.2 manifest YAML (shape precedent for partition reclassification):**
  `docs/plans/v0-1-0-foldback-scope-expansion-fbe2.manifest.yaml`.
- **Plugin pyproject (READ ONLY at FBE.3):**
  `plugins/dev-sdlc/pyproject.toml`.
- **Plugin source (READ ONLY at FBE.3):**
  `plugins/dev-sdlc/src/loam/plugins/dev_sdlc/`.
- **Synth pipeline source (READ ONLY at FBE.3):**
  `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py`
  (verified `plugins/...` not subject to prefix-strip).
- **Partition manifest:**
  `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- **Dev-sdlc fence test (READ; BASELINE literal updated by `loam amend
  apply`):**
  `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`.
- **Universal-paths-admission precedent:** FBE.1 + FBE.2 manifests +
  M7-partition-fix amendment #98.
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (parent
    AC.FBE.3.5 tightened — explicit 15-leaf count + named negative
    paths).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW
    commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit
    in §11).
  - `feedback_subagent_odd_violation_halt` (HT-9 covers ODD
    violations in surrounding code).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to
    touched-only).
  - `feedback_summarize_and_surface_decisions` (surfaces 1–6 explicit
    in §2).
  - `feedback_principle_conflict_resolution_multi_signal` (Surfaces
    apply scope-confidence + reversibility signals).
  - `feedback_specific_claims_verified_or_marked_guess` (every
    "verified at planning" claim has a path/line citation; line
    numbers noted as approximate ("~") where they shift with edit
    position).

---

## 13. AI-time band

- Predicted (parent plan §4 FBE.3 + this sub-plan): **30–60 min,
  midpoint 45 min**; dispatch hard cap 80 min.
- Justification: 8-glob manifest edit (vs FBE.2's 1-glob single-line)
  + 2 test fixture edits (vs FBE.2's 1) + 1 test rewrite (per-subtree
  assertion logic) + apply + seal + backfill + status. The fixture
  rewrite is mechanically simple but sits on a dev-sdlc-specific test
  file with M6b.0-flavoured narrative comments that need updating
  inline. Parent plan's category match: amendment-build (multi-subtree
  manifest edit + test surface refactor) per rubric — formula
  `wall_clock_minutes ≈ 0.1–0.15 × tool_calls` predicts ~10–15 min for
  ~70–100 tool calls; widen to 30–60 for the test rewrite scope +
  apply/seal cycle + pip install verification.

---

## 14. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Partition-admission commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.3 sub-plan-doc. Ready to build.*
