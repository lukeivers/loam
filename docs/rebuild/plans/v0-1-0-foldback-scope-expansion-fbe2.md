# FBE.2 sub-plan — Partition admit `framework/tools/loam/**` (CLI binary ships)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §4 FBE.2.
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessor:** FBE.1 sealed at `21b9480` (9/9 ACs). FBE.1 status:
`<workspace>/.scratch/claude-output/fbe1-status-2026-05-03.md`.
**BASELINE:** `715cde7` — current canonical pos-v2 HEAD pre-FBE.2.

---

## 1. Summary / TLDR

Reclassify `framework/tools/loam/**` from `dev_only` to
`dev_and_public` so the unified `loam` CLI binary actually ships in
the synthesised public tree. Keep the legitimately-dev tools
(`heavy-b-migrate/`, `orphan-plist-cleanup/`,
`upgrade-merge-resolver/`, `pos-publish-framework-only/`,
`loam-migrate-host-config/`, `loam-migrate-launchd-labels/`,
`loam-migrate-dormancy-config/`, `loam-memory-inspect/`) classified
as `dev_only`.

Establishes `framework/tools/loam/` as a NEW sealed component
(component anchor + `tests/SEAL_COMMIT` sidecar +
`tests/test_no_sealed_amendments.py` invariant), mirroring FBE.1's
loam-init pattern. The sidecar bump per the
dev_only→dev_and_public reclassification convention is the
mechanical way the partition status of a component is encoded into
the seal trail.

Closes BLOCKER 2-related synth-omission for the CLI binary itself
(BLOCKER 2 in the reviewer foldback; FBE.3 closes the dev-sdlc
plugin half).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt; recorded — Risk #7 verified BENIGN for FBE.2)

**Synth pipeline DOES strip the `framework/` prefix on shipped
paths** — `framework/tools/pos-publish-framework-only/src/loam/
publish_framework_only/synth.py` lines 302-312:

```python
framework_prefix = f"{FRAMEWORK_PREFIX}/"  # "framework/"
if source_path.startswith(framework_prefix):
    synthetic_path = source_path[len(framework_prefix):]
    saw_framework_leaf = True
```

So `framework/tools/loam/pyproject.toml` will land at
`tools/loam/pyproject.toml` in the synth tree (NOT
`framework/tools/loam/pyproject.toml`). This is the SAME treatment
FBE.1's `framework/loam-init/` already received without halt
(`framework/loam-init/**` → `loam-init/**` at synth root). Decision
D in the parent plan §3 calls for fixing the synth (preserve the
prefix) — but Decision D is OUT OF SCOPE for FBE.2. Documented as
expected behaviour; FBE.2 proceeds with manifest-only edits. AC.FBE.2.4
asserts on `tools/loam/` in the synth tree (the post-strip path),
mirroring how FBE.1 verified `loam-init/` at root.

### Surface #2 (no halt; recorded — sealed-component shape required)

`framework/tools/loam/` does NOT have a `tests/SEAL_COMMIT` sidecar
or `tests/test_no_sealed_amendments.py` invariant today (verified
`ls framework/tools/loam/tests/` — only carries `__init__.py` +
`test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py`). Reclassifying
to `dev_and_public` per the parent dispatch's "sidecar bump per
dev_only→dev_and_public reclassification convention" requires
establishing those sidecar files at FBE.2 — same shape FBE.1 used
for the NEW loam-init component. The component name in the manifest
will be `loam-cli` (matches the pyproject `name = "loam-cli"`).

This is structural-only — the CLI source (`cli.py` etc.) is NOT
edited (AC.FBE.2.6 negative AC).

### Surface #3 (no halt; recorded — `loam_cli/` has zero inter-component deps)

`framework/tools/loam/pyproject.toml:10` declares
`dependencies = ["PyYAML>=6"]` — only PyYAML, no
loam-* siblings. `loam_amend` is discovered via
`importlib.metadata.entry_points(group="loam.cli.subcommands")` (per
`loam_cli/cli.py:50-99`), NOT direct import. So the FBE.2 halt
trigger about `loam_cli/` depending on dev-only modules is
**resolved BENIGN at planning** — there is no dep cycle.

### Surface #4 (admit; explained — touched test fixture needs update)

`framework/tools/pos-publish-framework-only/tests/
test_AC_OSS_3_default_partition_complete.py:146` has
`framework/tools/loam/pyproject.toml` listed under
`sample_dev_only_paths` for the spot-check
`test_default_partition_classifies_dev_tools_dev_only`. After
FBE.2 reclassification this assertion will FAIL. The fix is
mechanical: move the literal from `sample_dev_only_paths` (line ~144)
into `sample_runtime_paths` (line ~114) of the symmetric spot-check
`test_default_partition_classifies_runtime_components_dev_and_public`.

Per partition-precedence rule #2, this fixture edit lands in
`framework/tools/pos-publish-framework-only/tests/` which classifies
`dev_only` via `**/tests/**` glob — so the fixture edit doesn't
affect the synth output. The edit is admitted within the FBE.2
sealed-component fence of `pos-publish-framework-only` (manifest-
owner fence already includes its own `tests/`).

### Surface #5 (no halt; recorded — Risk #4 dispatcher pragmas remain M6c)

`framework/tools/loam/src/loam_cli/cli.py:74,84,92,128` carries 4
`# pragma: no cover — defensive` exception branches that emit
`_LOGGER.warning(...)`. Per parent plan §6 Risk 4 + FBE.1 surface
#3, these are M6c graceful-fallthrough-with-detection — NOT ODD §2.5
violations. Reading the source confirms each branch logs explicitly
before continuing/returning. FBE.2 does NOT touch these; they ship
as-is. Documented for the corpus so a downstream agent doesn't
re-surface.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per
  `docs/rebuild/VALUE_PROPOSITION.md`) — making the documented
  `pip install -e framework/tools/loam` command in the README
  actually find a shipping component is a prerequisite for the
  harness's "stranger can install" promise.
- **Reviewer foldback BLOCKER 2 / 3 / HIGH 1** — the CLI binary
  not shipping is a foundational gap; FBE.2 closes the binary half
  (FBE.3 closes the plugin half).
- **AC.OSS-M6.5 / AC.OSS-M6.6** — entry-point-discovery dispatcher
  pattern; FBE.2 makes the dispatcher itself reachable in the
  public tree so registered subcommands (FBE.1's `loam init`) have
  an executable to dispatch through.

**Ladders to:** AC.FBE.2.* → AC.OSS-M11a.* (FBE.6 reviewer GO) →
M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.2.*)

AC family **`AC.FBE.2.*`** — collision-safe (verified: `grep -rE
"AC\.FBE\.2" docs/` returns only the parent foldback plan-doc).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.2.1** | `publish-mode-manifest.yaml`'s `dev_only:` block REMOVES the `glob: "framework/tools/loam/**"` entry (currently at line 203) + adds a 4-line provenance comment naming FBE.2 + the foldback parent plan-doc above the removal. | `grep -A1 'framework/tools/loam' framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` returns the entry only under `dev_and_public:`. |
| **AC.FBE.2.2** | `dev_and_public:` block ADDS `glob: "framework/tools/loam/**"` with a 4-line provenance comment naming FBE.2 + the foldback parent plan-doc. | Direct `grep` + `pytest test_AC_OSS_3_partition_classifier.py` (existing passes; the synthetic fixtures inside the test file are independent). |
| **AC.FBE.2.3** | `dev_only:` retains the 8 legitimately-dev tools: `framework/tools/heavy-b-migrate/**`, `framework/tools/orphan-plist-cleanup/**`, `framework/tools/upgrade-merge-resolver/**`, `framework/tools/pos-publish-framework-only/**`, `framework/tools/loam-migrate-host-config/**`, `framework/tools/loam-migrate-launchd-labels/**`, `framework/tools/loam-migrate-dormancy-config/**`, `framework/tools/loam-memory-inspect/**`. (No reclassification beyond `framework/tools/loam/` itself.) | `grep -E 'framework/tools/(heavy-b-migrate\|orphan-plist-cleanup\|upgrade-merge-resolver\|pos-publish-framework-only\|loam-migrate-\|loam-memory-inspect)' framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` returns 8 entries all under `dev_only:`. |
| **AC.FBE.2.4** | Synth re-run from canonical pos-v2 HEAD (post-FBE.2-seal) produces a `framework-only` tree containing `tools/loam/{pyproject.toml,src/loam_cli/cli.py,src/loam_cli/__init__.py,src/loam_cli/__main__.py,README.md}` (5 files; `tests/` correctly drops via the universal `**/tests/**` precedence). The post-strip path shape `tools/loam/...` matches Surface #1's documented synth behaviour (parent plan Decision D is out of scope; the prefix-strip is intentional today). | Run `loam publish framework-only` (or invoke `synthesise_framework_only` directly) post-seal; `git ls-tree -r --name-only framework-only \| grep -E '^tools/loam/'` returns the 5 expected leaves. |
| **AC.FBE.2.5** | The audit-completeness test `test_AC_OSS_3_default_partition_complete.py` continues to pass for canonical pos-v2 HEAD post-FBE.2 reclassification. The spot-check `test_default_partition_classifies_dev_tools_dev_only` updated to remove `framework/tools/loam/pyproject.toml` from `sample_dev_only_paths`; the symmetric spot-check `test_default_partition_classifies_runtime_components_dev_and_public` updated to add `framework/tools/loam/pyproject.toml` to `sample_runtime_paths`. | `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py` returns 3/3 pass. |
| **AC.FBE.2.6** | Negative AC: zero changes to `framework/tools/loam/src/loam_cli/cli.py` source (description scrub of M1g / loam-rename-decisions.md / pos-amend / etc. references in the docstring is FBE.5's scope per parent plan §4 FBE.5.3). Zero changes to `framework/tools/loam/pyproject.toml` `description` field (also FBE.5). | `git diff BASELINE..SEAL_COMMIT -- framework/tools/loam/src/loam_cli/ framework/tools/loam/pyproject.toml` returns only NEW files (sidecar shape) — no edits to existing source/pyproject. |
| **AC.FBE.2.7** | NEW sealed-component sidecar files exist: `framework/tools/loam/tests/SEAL_COMMIT` (sidecar) + `framework/tools/loam/tests/test_no_sealed_amendments.py` (the structural-fence invariant; mirrors FBE.1's loam-init shape). | `ls framework/tools/loam/tests/{SEAL_COMMIT,test_no_sealed_amendments.py}` succeeds. The fence-test passes against the FBE.2 BASELINE post-seal. |
| **AC.FBE.2.S** | Sealed-component fence: `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under `framework/tools/loam/` (the sealed component) + `framework/tools/pos-publish-framework-only/` (manifest owner: the partition-manifest 2-line edit + the test fixture spot-check edit) + `docs/rebuild/plans/` (universal_paths.prefixes; sub-plan + manifest YAML + parent backfill). | `framework/tools/loam/tests/test_no_sealed_amendments.py` invariant + manual `git diff --name-only` check at seal time. |

**ACs deliberately out of scope (NOT in FBE.2):**
- Source edits to `loam_cli/cli.py` (FBE.5's docstring scrub).
- Pyproject `description` field scrub (FBE.5).
- Synth pipeline path-rewrite fix (parent Decision D; not in any
  FBE.x amendment today; deferred).
- Path-spec dep rewrite (FBE.4 — and `loam-cli` has no inter-component
  deps anyway, so FBE.4 doesn't visit it).
- Any edits to the legitimately-dev tools' pyproject / source.

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
Pure manifest reclassification + standard sealed-component sidecar
shape; no Claude-native primitive in scope. Composes on the
established partition-shape pattern (M2 manifest-driven synth) and
the standard sealed-component anchor (M11a Class A globs +
`**/tests/**` precedence rule).

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The CLI binary IS the primary-
  persona-toolkit binary. Without the CLI in the synth tree, every
  documented `loam <verb>` invocation is unreachable. FBE.2 makes
  the unified CLI shippable.
- **Harness test:** PASS. The harness *is* the CLI dispatcher +
  registered subcommands. Admitting the dispatcher to ship is the
  most direct possible "add to the toolkit the primary persona
  draws from" delta.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which YAML lines move where, which
sidecar shape is used) is builder's call, but inferable from the
FBE.1 loam-init precedent without being prescribed. No "options to
rule on" framed inside this plan-doc.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape (parent plan locks Decision B.1;
FBE.1 established the partition-admit pattern at sealed-time; the
synth-side strip behaviour is verified). Tight scope. ACs name
observable outputs; method is inferable from the loam-init
precedent.

### Lens 5 — Swarming
FBE.2 is one of six FBE.* amendments (parent's planner-output). The
FBE.2 ACs do not partition further — every AC binds to a single
observable surface (manifest line removal, manifest line addition,
test fixture edit, sidecar files, synth-tree shape, fence diff).
Each is leaf-scoped. No sub-decomposition.

---

## 6. File-by-file map

### NEW files under sealed-component fence (`framework/tools/loam/`):

```
framework/tools/loam/
└── tests/
    ├── SEAL_COMMIT                                         # sidecar; written at apply-time
    └── test_no_sealed_amendments.py                        # AC.FBE.2.7 + AC.FBE.2.S; standard structural fence
```

(Pre-existing: `pyproject.toml`, `README.md`, `src/loam_cli/{__init__.py,__main__.py,cli.py}`, `tests/__init__.py`, `tests/test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py` — all unchanged.)

### Edits within manifest-owner fence (`framework/tools/pos-publish-framework-only/`):

- `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`:
  - REMOVE `- glob: "framework/tools/loam/**"` from `dev_only:` (currently line 203).
  - ADD `- glob: "framework/tools/loam/**"` to `dev_and_public:` (insert in alphabetic position; with provenance comment).
  - ADD provenance comments at both edit sites naming FBE.2 + parent plan.
- `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py`:
  - In `sample_dev_only_paths` (line ~144): REMOVE `"framework/tools/loam/pyproject.toml"`.
  - In `sample_runtime_paths` (line ~114): ADD `"framework/tools/loam/pyproject.toml"`.

### Plan-doc + manifest (universal_paths.prefixes: `docs/rebuild/plans/`):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2.md` (this file).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` — §8
  method-decision register entries: apply commit SHA + seal commit
  SHA for FBE.2.

**TOTAL fence diff:** 2 new files under `framework/tools/loam/tests/`
+ 2-line manifest YAML edit + ~2-line test fixture edit (within
manifest-owner fence) + plan-doc + manifest YAML (universal-admitted)
+ parent plan-doc backfill (universal-admitted).

---

## 7. Hard constraints

- Two sealed-component fence: `framework/tools/loam/` (the moved-class
  component, NEW seal anchor) + `framework/tools/pos-publish-framework-only/`
  (manifest owner; pre-existing seal anchor at
  `framework/tools/pos-publish-framework-only/tests/SEAL_COMMIT` —
  wait, this needs verification at build-time; `pos-publish-framework-only`
  did not appear in my earlier `find SEAL_COMMIT` sweep, so it may
  ride universal_paths.prefixes alone, same pattern as FBE.1 used).
- No new external runtime deps (CLI keeps PyYAML-only).
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.2.*` (collision-safe; verified).
- Auto-memory `MEMORY.md` NOT touched.
- Zero edits to `framework/tools/loam/src/loam_cli/cli.py` (AC.FBE.2.6 forbids; FBE.5's scope).
- Zero edits to `framework/tools/loam/pyproject.toml` (AC.FBE.2.6 forbids; FBE.5's scope).
- Zero edits to other `framework/tools/<comp>/` components (AC.FBE.2.3 negative).
- Component-scoped test rerun only per `feedback_amendment_dispatch_speedups`:
  `framework/tools/loam/tests/` + `framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py`
  (audit-completeness + spot-checks). NOT the full canonical sweep.

---

## 8. Out of scope (per ODD §2.5)

- Source edits to `loam_cli/cli.py` (description / docstring scrub —
  FBE.5).
- Pyproject `description` field scrub — FBE.5.
- Synth pipeline path-rewrite fix to preserve `framework/<comp>/`
  shape — parent Decision D; not currently in any FBE.x; deferred.
- Path-spec dep rewrite — FBE.4 doesn't visit `loam-cli` (no inter-
  component deps).
- Any edits to the 8 legitimately-dev tools.
- Touching the `**/seals/**` or `**/tests/**` precedence rules
  (those are pre-existing M11a Class A/B locks and stay).

---

## 9. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not
silently extend) on:

- **HT-1:** Synth pipeline path-rewrite logic differs from what
  Surface #1 verified (e.g. it strips `framework/tools/` not just
  `framework/`). Mitigation: verified at planning that the strip is
  exclusively `framework/` (single segment). Should not trigger.
- **HT-2:** `loam_cli/` package depends on a dev-only module via
  direct import (not entry-point discovery). Mitigation: verified at
  planning — pyproject deps = `["PyYAML>=6"]` only; cli.py uses
  `importlib.metadata.entry_points` for plugin discovery. Should
  not trigger.
- **HT-3:** Audit-completeness test fails post-reclassification with
  a leaf path that was previously absorbed by the broad
  `framework/tools/loam/**` dev_only glob and now lacks a
  classification (impossible because the dev_and_public version of
  the same glob covers identical paths — but verify empirically).
  Surface; the manifest is mis-shaped.
- **HT-4:** A NEW spot-check test in `test_AC_OSS_3_default_partition_complete.py`
  beyond the two named (`...dev_tools_dev_only`,
  `...runtime_components_dev_and_public`) references
  `framework/tools/loam/...` and silently breaks. Mitigation: at
  build time, run the full `test_AC_OSS_3_default_partition_complete.py`
  and read all assertions; verified at planning that only those two
  spot-checks reference the path.
- **HT-5:** `loam amend apply` against the FBE.2 manifest fails
  with a fence breach diagnostic. Surface; the manifest's
  `extra_allowed_files` / `universal_paths` block needs adjustment.
- **HT-6:** `framework/tools/pos-publish-framework-only/` requires
  its OWN sidecar bump for the seal-anchor pattern (i.e., it's a
  pre-existing sealed component in its own right). Surface; either
  bring it into the components list as a frozen_baseline component
  or admit via universal_paths only (FBE.1's pattern).
- **HT-7:** Wall-time exceeds 50 min (parent plan band 15–30 min,
  midpoint 22 min; 50 min is the dispatch-imposed hard cap).
  Surface partial findings + named what's left.
- **HT-8:** A surrounding-code ODD §2.5 violation discovered in
  `loam_cli/cli.py` or `pos-publish-framework-only/` source during
  the build. Surface; do NOT silently extend or fix in-band.
- **HT-9:** Synth re-run for AC.FBE.2.4 fails (e.g. partition mis-
  shape causes SynthesisError). Surface; the manifest edit is
  invalid.
- **HT-10:** WD drifts to pos3. Halt immediately.

---

## 10. Risks

- **Risk: post-FBE.2 the CLI ships at `tools/loam/` (not `framework/tools/loam/`).**
  README references `pip install -e framework/tools/loam` per
  `2081771` (verified). After FBE.2 the synth tree has `tools/loam/`
  not `framework/tools/loam/`. **FBE.5's docstring scrub +
  description scrub will likely surface this as a doc/synth
  mismatch, OR FBE.6's extended smoke will fail when the install
  command can't find the path.** Mitigation: surface here; the path
  shape mismatch is a Decision D concern (parent plan); FBE.5 or
  FBE.6 can choose to either (a) rewrite the README to drop the
  `framework/` prefix, OR (b) escalate Decision D to a sibling
  amendment (FBE.2b — synth pipeline preserves the prefix). FBE.2
  itself is not the right place to fix; documenting for downstream.
- **Risk: post-FBE.2 a stranger doing `pip install -e framework/tools/loam`
  in the dev tree gets a CLI without `loam init` available unless
  they ALSO `pip install -e framework/loam-init` (FBE.1's
  component) AND `pip install -e framework/workspace-bootstrap`.**
  Mitigation: known multi-step install order; AC.FBE.4.7 owns the
  documented install order; AC.FBE.6.3 owns the smoke verification.
- **Risk: `framework/tools/pos-publish-framework-only/` doesn't have
  a SEAL_COMMIT sidecar today, so listing it as a `components:`
  entry in the manifest will fail.** Mitigation: at build time,
  verify whether `pos-publish-framework-only` has a sidecar; if not,
  use universal_paths.prefixes to admit the manifest + test fixture
  edits (same pattern FBE.1 used). The `components:` list will then
  have only `loam-cli` (the new sealed component being established).

---

## 11. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Sidecar-shape commit** — author `framework/tools/loam/tests/SEAL_COMMIT`
   (placeholder content `HEAD`) + `framework/tools/loam/tests/test_no_sealed_amendments.py`
   (mirrors FBE.1's loam-init shape; BASELINE literal = the partition
   admission commit SHA from step 3 — **deferred to step 4 BASELINE
   bump via `loam amend apply`**, so initial value can be plan-doc
   commit SHA from step 1, same pattern as FBE.1).
3. **Partition-admission commit** — edit `publish-mode-manifest.yaml`
   (move the glob from `dev_only:` to `dev_and_public:` + provenance
   comments) + edit `test_AC_OSS_3_default_partition_complete.py`
   (move the literal from `sample_dev_only_paths` to
   `sample_runtime_paths`). Verify `pytest test_AC_OSS_3_default_partition_complete.py`
   passes 3/3.
4. **Manifest commit** — author `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2.manifest.yaml`.
5. **`loam amend apply`** — invoke against the manifest. Produces
   the apply-bookkeeping commit (BASELINE bump in
   `test_no_sealed_amendments.py`, sidecar bump in `SEAL_COMMIT`).
6. **`loam amend seal`** — produces the deterministic seal commit;
   sidecar `SEAL_COMMIT` advances to the seal SHA; narrative file
   created at `tests/SEAL_COMMIT.notes`.
7. **Parent plan-doc backfill** — `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md`
   §8 FBE.2 entries get the apply + seal SHAs (separate NEW commit;
   admitted via `docs/rebuild/plans/` universal prefix).
8. **Status file** — write `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe2-status-2026-05-03.md`
   (outside canonical tree; the dispatcher reads it).

NO `git commit --amend` at any point. NO push to any remote.

---

## 12. References

- **Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §4 FBE.2.
- **Reviewer foldback dossier:** `<workspace>/.scratch/claude-output/loam-user-review-2026-05-03.md` BLOCKERs + HIGHs.
- **FBE.1 status (precedent):** `<workspace>/.scratch/claude-output/fbe1-status-2026-05-03.md`.
- **FBE.1 sub-plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe1.md`.
- **FBE.1 manifest YAML (shape precedent):** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe1.manifest.yaml`.
- **CLI dispatcher source (READ ONLY at FBE.2):** `framework/tools/loam/src/loam_cli/cli.py`.
- **CLI pyproject (READ ONLY at FBE.2):** `framework/tools/loam/pyproject.toml`.
- **Synth pipeline source (READ ONLY at FBE.2):** `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py`.
- **Partition manifest:** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- **Universal-paths-admission precedent:** `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-partition-fix.manifest.yaml` (M7-partition-fix amendment #98) + FBE.1 manifest.
- **Sealed-component invariant precedent:** `framework/loam-init/tests/test_no_sealed_amendments.py` (FBE.1).
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (parent AC.FBE.2.4 tightened — explicit `tools/loam/...` post-strip path shape; no loose "framework-only branch tree includes" text).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §11).
  - `feedback_subagent_odd_violation_halt` (HT-8 covers ODD violations in surrounding code).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to touched-only).
  - `feedback_summarize_and_surface_decisions` (surfaces 1–5 explicit in §2).
  - `feedback_principle_conflict_resolution_multi_signal` (Surface #1 + Surface #2 apply scope-confidence + reversibility signals).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified at planning" claim has a path/line citation; line ~144 / line ~114 noted as approximate ("~") for the test-fixture line numbers since they shift with edit position).

---

## 13. AI-time band

- Predicted (parent plan §4 FBE.2 + this sub-plan): **15–30 min,
  midpoint 22 min**; dispatch hard cap 50 min.
- Justification: tiny manifest 2-line edit + small test-fixture
  edit + sidecar establishment (2 new files, mostly copy-from-loam-init)
  + manifest authoring (mirrors FBE.1) + apply + seal + backfill +
  status. Parent plan's category match: amendment-build (manifest +
  small edits + sidecar) per rubric — formula `wall_clock_minutes
  ≈ 0.1–0.15 × tool_calls` predicts ~6–12 min for ~60–80 tool calls;
  widen to 15–30 for the new-sidecar overhead + the apply/seal cycle
  itself.

---

## 14. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Sidecar-shape commit: `<TBD>`.
- Partition-admission commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.2 sub-plan-doc. Ready to build.*
