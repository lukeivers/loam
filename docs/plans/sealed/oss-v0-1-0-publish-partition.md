# OSS v0.1.0 publish — M2 — publish-mode partition manifest + synthesis tool extension — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme master:** `docs/plans/oss-v0-1-0-publish.md` (master plan §5 M2 row + §6 sequencing rule #2).
**Series predecessor:** M1.rename programme — sealed M1a..M1g 2026-04-29 (M1g seal `f6c22fd`; §14 backfill `d5b8dcd`).

**Authority documents:**
- Master plan §5 M2 row + §6 sequencing rule #2 (M2 gates M9/M11).
- Programme AC: AC.OSS.3 (no dev-discipline machinery in public synthesis output) — `docs/plans/oss-v0-1-0-publish.md` §3.
- OSS-readiness audit §1.3 + §2 D3 + §4.1–§4.7 — partition recommendations.
  Path: `.scratch/claude-output/oss-readiness-audit.md`.
- Feature-usage audit (which features are dev-only vs runtime-public).
  Path: `.scratch/claude-output/feature-usage-audit.md`.
- Synthesis tool target: `framework/tools/pos-publish-framework-only/`.
- VALUE_PROPOSITION (prime objective hook): `docs/VALUE_PROPOSITION.md`.

---

## 1. Summary / TLDR

**M2 extends the synthesis tool to be MANIFEST-DRIVEN.**

Today, `pos-publish-framework-only.synth` decides what ships in the
`framework-only` synthetic branch via two hardcoded constants
(`FRAMEWORK_PREFIX = "framework"` + `TOP_LEVEL_DOCS = ("CLAUDE.md",
"CLAUDE.dev.md", "README.md", "docs")`). The synthesis is correct
for D-architecture's "promote `framework/<entry>` to root" goal but
ships **everything** under `framework/` and **everything** under
`docs/` — including dev-discipline machinery (`docs/rebuild/`,
`framework/tools/loam/` (the renamed pos-amend), `framework/tools/
loam-mode/`, A1–A4 PreToolUse gates, ODD long-form docs,
`CLAUDE.dev.md`, etc.). AC.OSS.3 forbids those in the public
artefact.

**M2 introduces `publish-mode-manifest.yaml`** at the tool's canonical
location. The manifest partitions every workspace path into one of
four classes:

1. **`public_only`** — ships in the public synthesis output and
   ONLY there (rare; reserved for future use such as a public
   `README.md` that differs from canonical's dev-flavoured `README`).
2. **`dev_and_public`** — ships in the public synthesis output AND
   remains in the dev tree (most runtime artefacts).
3. **`dev_only`** — stays in the dev tree, NEVER ships publicly.
4. **`excluded_from_publish`** — explicitly excluded for safety
   reasons (host-specific paths, secrets-adjacent, runtime state).
   Different from `dev_only` semantically: `excluded` means MUST
   NOT ship publicly under any condition; `dev_only` means ships
   only in dev mode.

**Synthesis tool extension.** `synth.py` becomes manifest-driven:
the manifest is the single source of truth for which framework
entries promote to root and which top-level docs overlay. Every
candidate path under canonical's `pos-v2` tree is classified; paths
in `dev_only` or `excluded_from_publish` are dropped before
`mktree`. The tool errors if any path is unclassified — the default
partition is COMPLETE.

**Hard cutover.** No transitional manifest-vs-hardcode dual mode
(per dispatch §Constraints). `FRAMEWORK_PREFIX` + `TOP_LEVEL_DOCS`
constants retire; the manifest is the only source of partition
truth post-M2.

**Items in M2:**

1. **Item 1 — Author the partition manifest YAML** at
   `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
   Schema: four sections (`public_only`, `dev_and_public`,
   `dev_only`, `excluded_from_publish`), each a list of entries.
   Each entry is either `{path: <workspace-relative path>}` or
   `{glob: <pattern>, exclude: [<patterns>]}` (matching dev-mode-
   manifest's entry shape). Plus `audit_roots` (list of top-level
   dirs/files the manifest classifies) and `audit_excludes` (glob
   patterns for transient state — `.git/`, `.scratch/`,
   `__pycache__/`, etc. — never classified, never shipped).

2. **Item 2 — Manifest loader + classifier module** at
   `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/partition.py`.
   Public surface: `load_manifest(path)` + `classify_path(manifest,
   workspace_relative_path) -> PartitionClass` + `partition_complete(
   manifest, candidate_paths) -> CompletenessReport`. Coercion
   patterns mirror `loam_mode.manifest` for shape consistency
   (no third-party dep beyond `pyyaml` which is already in the
   tool's surface — verify in §11 finding #2).

3. **Item 3 — Extend `synth.py` to consume the manifest.** New
   parameter `manifest_path: Path` on `synthesise_framework_only`
   (with default resolution: caller may pass explicit path; for
   the in-canonical CLI invocation the default points at
   `<repo>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`).
   The function:
   - Loads the manifest; raises `SynthesisError` on schema
     problems.
   - Walks the source commit's tree (top-level entries via
     `git ls-tree`); for each top-level entry, recurses into
     paths that need finer-grained classification (e.g.
     `framework/tools/loam/` is `dev_only` while
     `framework/cost-governance/` is `dev_and_public`, even
     though both sit under `framework/`).
   - For each leaf path, classifies via `classify_path`.
   - Builds the synthetic tree entries from `public_only ∪
     dev_and_public` paths only. Promotes `framework/<entry>` to
     root (existing logic preserved); top-level docs overlay
     verbatim.
   - Errors with `SynthesisError("partition incomplete: <N>
     unclassified paths: <first-3>...")` if any candidate path
     isn't classified.

4. **Item 4 — Default partition assignment.** Per dispatch §3
   (default partition):
   - **`dev_and_public`** — the runtime framework component dirs
     (cost-governance, dormancy, hands-off-lifecycle's runtime
     surface excluding A1-A4 gates if separable [see §11
     finding #1], memory-system, objective-tracker,
     observability-aggregator, orchestrator, primary-persona,
     reversibility-primitive, safety-layer, scope-of-work,
     self-correction, self-upgrade, telegram-interface,
     workspace-bootstrap, workspace-sync), per-component
     pyproject.toml + README.md, the public top-level docs
     (`LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
     `SECURITY.md`, `README.md`, `docs/positioning.md`,
     `docs/design/odd.md` — note the public-facing files
     authored by M5/M7/M8 don't yet exist; the manifest declares
     forward-looking entries for them).
   - **`dev_only`** — `framework/tools/loam/` (loam amend CLI
     itself), `framework/tools/loam-mode/` (dev-mode auto-load
     selector), `framework/tools/heavy-b-migrate/`,
     `framework/tools/orphan-plist-cleanup/`,
     `framework/tools/upgrade-merge-resolver/`,
     `framework/tools/pos-publish-framework-only/` (the synth
     tool itself — its OUTPUT ships, not the tool),
     `framework/tools/loam-migrate-host-config/`,
     `framework/tools/loam-migrate-launchd-labels/`,
     `framework/tools/loam-migrate-dormancy-config/`,
     `framework/hands-off-lifecycle/hooks/` (A1–A4 gates IF the
     hooks dir is separable; see §11 finding #1),
     `docs/rebuild/` (the entire dir — plans, components, FUTURE_IDEAS,
     STATE, BACKLOG, dev-mode-manifest, capability-corpus authoring
     shape, decay-retention-analysis, spec/),
     `docs/odd-methodology.md`, `docs/odd-in-loam.md`,
     `docs/duration-estimation-rubric.md` (if present;
     audit's recommendation), `CLAUDE.dev.md`, `FUTURE_IDEAS_DRAFT.md`
     (workspace-side; not framework-side, but defensive
     classification).
   - **`excluded_from_publish`** — `.git/`, `.scratch/`, `.pos/`,
     `data/` runtime state, `workspace/` workspace-side state,
     `personas/` (untracked workspace-side), editable-install
     `*.egg-info/`, `__pycache__/`, `.pytest_cache/`, `.venv/`,
     `*.pth` files in site-packages (these are `.gitignore`'d
     anyway but we declare excluded for audit-completeness),
     `.env` files, `.DS_Store`. **NOTE:** these are double-
     defended — `.gitignore` keeps them out of the source commit
     so `git ls-tree` never sees them; the manifest entry is
     belt-and-braces audit-completeness.
   - **`public_only`** — empty at M2 (reserved for future
     diverging public-only artefacts; e.g. M11 dry-run may
     introduce a public `README.md` that differs from canonical's
     dev-flavoured one — that lands at M11, not here).

5. **Item 5 — Migration: retire the hardcoded constants.** Remove
   `FRAMEWORK_PREFIX` + `TOP_LEVEL_DOCS` from `synth.py` (or keep
   them as documentation-only string-constants referenced by the
   manifest — builder's call). The manifest is the only source
   of partition truth post-M2. Hard cutover per dispatch.

6. **Item 6 — CLI surface extension.** `cli.py` adds an optional
   `--manifest-path <path>` argument with default
   `<repo>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
   For programmatic callers (workspace-bootstrap's
   `test_AC_SFR_4_pos_sync_composition.py`, pos-new-workspace's
   bootstrap path) the function signature accepts an explicit
   `manifest_path` parameter; existing fixture-canonical tests
   pass an in-fixture minimal manifest (§13 below).

7. **Item 7 — Tests.** Three new test files (or new tests added
   to the existing `test_AC_SFR_2_synthesis_pipeline.py` —
   builder's call):
   - `test_AC_OSS_3_partition_manifest_load.py` — schema-shape
     coverage (well-formed manifest loads; missing section, bad
     entry, partition incompleteness raise).
   - `test_AC_OSS_3_partition_classifier.py` — classification
     correctness (canonical paths classify into the expected
     bucket; first-match-wins ordering when an entry overlaps).
   - `test_AC_OSS_3_synthesis_drops_dev_only.py` — extends the
     existing `test_AC_SFR_2_synthesis_pipeline.py` fixture-
     canonical pattern: builds a fixture canonical that contains
     `framework/cost-governance/__init__.py` (dev_and_public),
     `framework/tools/loam/cli.py` (dev_only), `CLAUDE.md`
     (dev_and_public), `CLAUDE.dev.md` (dev_only),
     `docs/STATE.md` (dev_only), `docs/positioning.md`
     (dev_and_public). Synthesises with a fixture manifest;
     asserts the synthetic tree contains the dev_and_public
     paths and does NOT contain the dev_only paths.

8. **Item 8 — Backwards-compat for existing tests.** The
   existing `test_AC_SFR_2_synthesis_pipeline.py` fixture-canonical
   tests use a minimal canonical (only ~5 paths). Their fixture
   `make_fixture_canonical` (in conftest.py) needs to either (a)
   author a fixture-local manifest that classifies the fixture's
   paths; OR (b) accept a `manifest` parameter that the test
   passes through to `synthesise_framework_only`. Recommendation:
   option (a) — extend `make_fixture_canonical` to also write a
   `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`
   into the fixture canonical that classifies the fixture's
   paths. Keeps existing tests passing without new public API.

**Estimate:** 25–45 min AI-time per the duration rubric (per
master plan §5 M2 row; single-component sealed amendment;
manifest-authoring + synth.py extension + tests). Halt-trigger §8
fires at 70 min (1.5× upper bound).

**Sealed-component fence:** TOOLS-TREE-ONLY. No HOL anchor needed
(this work touches no cross-cutting hooks or seal-test allowlists
outside the tools-tree). No cross-component allowlist edits
needed (the 8 components with `framework/tools/loam/` allowlist
entries don't gate on `framework/tools/pos-publish-framework-only/`;
workspace-bootstrap admits `framework/tools/` broadly per §11
finding #3). The fence is `framework/tools/pos-publish-framework-only/`
+ the new plan-doc + manifest YAML.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this amendment satisfies:**

- **AC.OSS.3** (`oss-v0-1-0-publish.md` §3) — *"No dev-discipline
  machinery visible in the public synthesis output."* M2 is the
  mechanism that delivers this AC. Verification (per AC.OSS.3
  text): synthesise canonical HEAD via the M2-extended pipeline;
  grep the synthetic tree for excluded artefacts; count of
  expected exclusions == count of actual exclusions. M2 itself
  doesn't run that verification (M11 does); M2 lands the
  manifest-driven mechanism.
- **AC.PO.2** (VALUE_PROPOSITION harness test) — the partition
  manifest is a queryable harness primitive ("what ships? what
  doesn't?"). Future features (e.g. a workspace-bootstrap
  contribution that surfaces "this artefact is dev_only") can
  read the manifest. M2 grows the harness toolkit by one
  primitive.

**Sealed-component fence (preliminary — see §4 ACs + §11 surface
inventory):** **Tools-tree-only fence** — the entire change set
sits under `framework/tools/pos-publish-framework-only/` plus the
sub-plan-doc + manifest YAML under `docs/plans/`.

**ODD §2.5 reverse-direction commitment.** Every line of code/
test/manifest-content/doc-prose changed in M2's diff traces back
to AC.OSS-M2.1 .. AC.OSS-M2.S below. Mechanical extension of the
existing synthesis tool — manifest-loading, manifest-driven path
classification, replacement of two hardcoded constants with
manifest reads. No behaviour changes beyond the AC-named ones;
no defensive-`if` admissions beyond named §11 findings.

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage-first

The synthesis tool is pure git plumbing — no LLM in the loop;
M2 preserves that. The manifest is YAML — Claude can read,
diff, and edit it directly via Read/Edit tools. The four
partition classes are queryable (a future hook event can read
the manifest at SessionStart to surface "this workspace ships X
when synthesised" diagnostics — that's a Lens-1 leverage point
for downstream features). No new MCP server, no new hook event;
the manifest composes on the existing partition primitive
pattern (mirrors `dev-mode-manifest.yaml` for `loam-mode`).
**Pass.**

### Lens 2 — Harness + primary-persona value

- **Primary-persona test** (translation burden): the persona's
  user-facing vocabulary doesn't change; the manifest is
  internal infrastructure. PASS-NEUTRAL.
- **Harness test** (toolkit primitive): YES — the manifest is a
  new queryable surface ("what ships in the public artefact?")
  that future features compose against. AC.OSS.3 (M2's prime
  AC) is the harness primitive itself. **Pass.**

### Lens 3 — ODD authoring

Each AC is outcome-shape, observable, deterministic. Behaviour-
count check at end of §4. Method-shape choices (exact path of
the manifest file, exact module decomposition of the
classifier, exact test-file split between extending vs adding)
are the builder's call inside the AC outcome bound — captured
in §10 + §14 method-decision register.

---

## 4. Acceptance criteria — AC.OSS-M2.*

Outcome-shaped. Behaviour-count check at end of section.

### AC.OSS-M2.1 — Partition manifest YAML authored at canonical location

The on-disk shape post-M2 is:

```
framework/tools/pos-publish-framework-only/
├── publish-mode-manifest.yaml    # NEW — authored by M2
├── pyproject.toml
├── src/
│   └── loam/
│       └── publish_framework_only/
│           ├── __init__.py
│           ├── cli.py
│           ├── synth.py          # extended by M2
│           └── partition.py      # NEW — manifest loader + classifier
└── tests/
    ├── conftest.py               # extended by M2 (fixture writes a fixture manifest)
    ├── test_AC_SFR_2_synthesis_pipeline.py  # existing — passes post-M2
    ├── test_AC_OSS_3_partition_manifest_load.py     # NEW (or merged)
    ├── test_AC_OSS_3_partition_classifier.py        # NEW (or merged)
    └── test_AC_OSS_3_synthesis_drops_dev_only.py    # NEW (or merged)
```

Manifest top-level shape (exact key names builder's call within
the AC outcome bound; recommendation per §10 D-build.M2.1):

```yaml
schema_version: 1

# Top-level paths the partition classifies. Anything outside
# audit_roots is excluded by audit (and synthesis errors if a
# git ls-tree leaf path is encountered that isn't covered).
audit_roots:
  - framework/
  - docs/
  - CLAUDE.md
  - CLAUDE.dev.md
  - README.md
  - LICENSE                  # forward-looking — authored at M5
  - CONTRIBUTING.md          # forward-looking — authored at M5
  - CODE_OF_CONDUCT.md       # forward-looking — authored at M5
  - SECURITY.md              # forward-looking — authored at M5
  - first-run-inventory.yaml
  - personas/                # untracked workspace-side; defensive
  - data/                    # gitignored runtime state; defensive
  - workspace/               # gitignored workspace state; defensive
  - .pos/                    # gitignored sentinel state
  - .scratch/                # gitignored ephemeral
  - .mcp.json                # gitignored
  - .gitignore

# Glob patterns excluded from any classification consideration.
audit_excludes:
  - "**/.git/**"
  - "**/.venv/**"
  - "**/.pytest_cache/**"
  - "**/__pycache__/**"
  - "**/*.egg-info/**"
  - "**/.DS_Store"
  - "**/*.pth"

public_only: []

dev_and_public:
  # Runtime framework components.
  - glob: "framework/cost-governance/**"
  - glob: "framework/dormancy/**"
  - glob: "framework/hands-off-lifecycle/**"   # see §11 finding #1
  - glob: "framework/memory-system/**"
  - glob: "framework/objective-tracker/**"
  - glob: "framework/observability-aggregator/**"
  - glob: "framework/orchestrator/**"
  - glob: "framework/primary-persona/**"
  - glob: "framework/reversibility-primitive/**"
  - glob: "framework/safety-layer/**"
  - glob: "framework/scope-of-work/**"
  - glob: "framework/self-correction/**"
  - glob: "framework/self-upgrade/**"
  - glob: "framework/telegram-interface/**"
  - glob: "framework/workspace-bootstrap/**"
  - glob: "framework/workspace-sync/**"
  - path: framework/first-run-inventory.yaml
  # Top-level public-facing docs (forward-looking — authored M5/M7).
  - path: README.md
  - path: CLAUDE.md
  - path: LICENSE
  - path: CONTRIBUTING.md
  - path: CODE_OF_CONDUCT.md
  - path: SECURITY.md
  # Public docs scaffold (forward-looking — authored M7).
  - path: docs/positioning.md
  - path: docs/getting-started.md
  - path: docs/architecture.md
  - glob: "docs/components/**"
  - glob: "docs/design/**"
  - path: docs/CLAUDE_CAPABILITIES.md

dev_only:
  # Dev-discipline tools.
  - glob: "framework/tools/loam/**"               # loam amend CLI
  - glob: "framework/tools/loam-mode/**"
  - glob: "framework/tools/heavy-b-migrate/**"
  - glob: "framework/tools/orphan-plist-cleanup/**"
  - glob: "framework/tools/upgrade-merge-resolver/**"
  - glob: "framework/tools/pos-publish-framework-only/**"
  - glob: "framework/tools/loam-migrate-host-config/**"
  - glob: "framework/tools/loam-migrate-launchd-labels/**"
  - glob: "framework/tools/loam-migrate-dormancy-config/**"
  # Internal docs tree.
  - glob: "docs/rebuild/**"
  - path: docs/odd-methodology.md
  - path: docs/odd-in-loam.md
  # Dev-mode-only top-level fragment.
  - path: CLAUDE.dev.md

excluded_from_publish:
  - glob: ".git/**"
  - glob: ".scratch/**"
  - glob: ".pos/**"
  - glob: "data/**"
  - glob: "workspace/**"
  - glob: "personas/**"
  - path: .mcp.json
  - path: .gitignore       # framework's gitignore is workspace-level
  - glob: "**/*.egg-info/**"
  - glob: "**/__pycache__/**"
  - glob: "**/.pytest_cache/**"
  - glob: "**/.venv/**"
  - glob: "**/*.pth"
  - glob: "**/.DS_Store"
  - glob: "**/.env"
```

**Outcome:**
- `ls framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` exists.
- `python -c "import yaml; yaml.safe_load(open('framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml'))"` exit 0 (well-formed YAML).
- The four partition sections (`public_only`, `dev_and_public`,
  `dev_only`, `excluded_from_publish`) are present and disjoint.

### AC.OSS-M2.2 — Manifest loader + classifier module

`framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/partition.py` exists with the public surface:

```python
class PartitionClass(StrEnum):
    PUBLIC_ONLY = "public_only"
    DEV_AND_PUBLIC = "dev_and_public"
    DEV_ONLY = "dev_only"
    EXCLUDED_FROM_PUBLISH = "excluded_from_publish"

@dataclass(frozen=True)
class PartitionManifest:
    schema_version: int
    audit_roots: tuple[str, ...]
    audit_excludes: tuple[str, ...]
    public_only: tuple[ManifestEntry, ...]
    dev_and_public: tuple[ManifestEntry, ...]
    dev_only: tuple[ManifestEntry, ...]
    excluded_from_publish: tuple[ManifestEntry, ...]

class ManifestError(Exception): ...

def load_manifest(path: Path) -> PartitionManifest: ...

def classify_path(
    manifest: PartitionManifest,
    workspace_relative_path: str,
) -> PartitionClass | None: ...

def is_publishable(klass: PartitionClass | None) -> bool:
    """True iff klass in {PUBLIC_ONLY, DEV_AND_PUBLIC}; False for
    DEV_ONLY, EXCLUDED_FROM_PUBLISH, or None (unclassified)."""
```

Schema validation behaviour:
- Missing required key (`schema_version`, `audit_roots`,
  `public_only`, `dev_and_public`, `dev_only`,
  `excluded_from_publish`) → `ManifestError`.
- Unknown top-level key → `ManifestError` (forward-strict).
- Non-list value where list expected → `ManifestError`.
- Entry is neither `{path: str}` nor `{glob: str, exclude?:
  list[str]}` → `ManifestError`.
- Entry sets both `path` and `glob` → `ManifestError`.
- `schema_version != 1` → `ManifestError` (forward-compat
  signal).

Classification semantics:
- First-match-wins precedence: `excluded_from_publish` checked
  first, then `dev_only`, then `public_only`, then
  `dev_and_public`. Rationale: `excluded` is the safety class
  (must-not-ship); checking it first prevents an accidental
  overlap from leaking. `dev_only` checked next so dev-tools
  can't be accidentally promoted by a broader `dev_and_public`
  glob. (D-build.M2.3 captures the precedence rule.)
- Glob semantics match `loam_mode.manifest._glob_match`: `**`
  crosses path separators; `*` is single-segment; `?` is
  single-character.
- A path that audit_excludes matches → returns None (the
  classifier excludes it from any partition class — it's
  audit-out-of-scope).

**Outcome:**
- `python -c "from loam.publish_framework_only.partition import load_manifest, classify_path, PartitionClass"` succeeds.
- `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_partition_manifest_load.py` passes (schema-shape tests).
- `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_partition_classifier.py` passes (classification correctness + precedence).

### AC.OSS-M2.3 — Synthesis tool consumes the manifest

`synth.py`'s `synthesise_framework_only` function gains a new
parameter `manifest_path: Path` (with no `None` default — the
parameter is required for callers that need partition behaviour;
the CLI default-resolves it from the canonical layout). The
function:

1. Loads the manifest via `partition.load_manifest`.
2. Walks the source commit's tree recursively (via
   `git ls-tree -r <source-sha>`) to enumerate every leaf path.
3. For each leaf path, classifies via `partition.classify_path`.
4. Errors with `SynthesisError("partition incomplete: <N>
   unclassified paths: <first-3>...")` if any leaf path that
   isn't audit-excluded returns `None` (unclassified is a build
   error — the manifest must cover every shipping path).
5. Builds the synthetic tree from `public_only ∪ dev_and_public`
   leaves, applying the existing promotion logic
   (`framework/<entry>` promoted to root, top-level entries
   verbatim).
6. `mktree` + `commit-tree` + `update-ref` per existing
   semantics (idempotent re-run, parent-chained advance).

The hardcoded constants `FRAMEWORK_PREFIX` and `TOP_LEVEL_DOCS`
RETIRE (or convert to documentation-only string literals
documenting the historical D-architecture-promote-framework
behaviour; builder's call per §10 D-build.M2.5).

**Outcome:**
- `pytest framework/tools/pos-publish-framework-only/tests/test_AC_SFR_2_synthesis_pipeline.py` passes (existing behaviour preserved against fixture-supplied manifest).
- `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_synthesis_drops_dev_only.py` passes (the new test verifies dev_only paths drop).
- The synthesised tree, when run against canonical HEAD, contains every `dev_and_public` path and contains NO `dev_only` path. (Full canonical-HEAD verification is M11's job; M2 verifies via fixture canonical only.)

### AC.OSS-M2.4 — Default partition is COMPLETE for canonical HEAD

The default partition assignment in
`publish-mode-manifest.yaml` covers EVERY path under canonical
HEAD's `pos-v2` branch (modulo audit_excludes). Verification:

- A test (`test_AC_OSS_3_default_partition_complete.py` or merged
  into the load test — builder's call) runs `git ls-tree -r
  HEAD` against the canonical repo (the test's working repo —
  `Path(__file__).resolve().parents[5]` per the test's repo-root
  convention), filters by audit_excludes, and asserts every
  remaining path classifies into one of the four buckets.
- Path-coverage check: for every top-level entry that exists
  on canonical HEAD's `pos-v2` branch, at least one manifest
  entry matches it.

**Outcome:**
- `pytest framework/tools/pos-publish-framework-only/tests/test_AC_OSS_3_default_partition_complete.py` passes (or whatever the builder names this test).

### AC.OSS-M2.5 — CLI surface accepts manifest path

`pos-publish-framework-only` console script grows an optional
flag `--manifest-path <path>`:

```
$ pos-publish-framework-only --help
usage: pos-publish-framework-only [-h] [--repo REPO] [--source SOURCE]
                                  [--target-ref TARGET_REF]
                                  [--manifest-path MANIFEST_PATH]
                                  [--quiet]
```

Default: `<repo>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`
(resolved relative to `--repo`).

**Outcome:**
- `pos-publish-framework-only --help` lists `--manifest-path`.
- Invocation against a canonical with the default manifest in
  place succeeds.
- Invocation with `--manifest-path <bad-path>` returns non-zero
  with a clear `manifest not found` error.

### AC.OSS-M2.6 — Hard cutover; no dual-mode

`FRAMEWORK_PREFIX` and `TOP_LEVEL_DOCS` constants no longer
drive any synthesis decision post-M2. They either retire
entirely (deletion) or remain as documentation-only literals
that no live code reads.

**Outcome:**
- `grep -nE "FRAMEWORK_PREFIX|TOP_LEVEL_DOCS" framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/*.py` returns either ZERO matches (full removal) OR matches only in inert documentation positions (string literals not referenced by any function body) — verifiable by `git grep -nE "FRAMEWORK_PREFIX|TOP_LEVEL_DOCS"` on the post-build tree.

### AC.OSS-M2.S — Sealed-component fence: HOL no-op anchor + tools-tree fence

The amendment manifest YAML lists:

- 1 sealed component in the seal-test anchor: hands-off-
  lifecycle (HOL — narrative anchor + meta-seal H19 verification
  via `test_cross_cutting.py`). HOL's diff is intentionally
  trivial (SEAL_COMMIT sidecar bump + new SEAL_COMMIT.oss-
  v0-1-0-publish-partition narrative file); no behaviour edits
  to HOL hooks or tests. This matches the M1c..M1g precedent
  (HOL is the conventional meta-anchor for tools-tree-only
  amendments).
- Tools-tree fence: `framework/tools/pos-publish-framework-only/`
  (the structural fence). The tool sealed under #67 via HOL's
  anchor + the tool-tree fence; no per-tool seal-diff invariant
  of its own per §11 finding #5.

The `seal_diff` `allowed_prefixes` admit:
- `framework/tools/pos-publish-framework-only/` (the entire
  subtree given M2's structural extension).
- The plan-doc + manifest YAML under `docs/plans/`
  (universal admission per amendment #22 ruling #3).

**Per-component touched-test scope:** narrow to
`framework/tools/pos-publish-framework-only/tests/`. Per
`feedback_amendment_dispatch_speedups`, M2 skips pre-seal
full-suite rerun.

The seal commit follows the established M1f/M1g pattern: a
single `chore(seals): ...` commit naming the AC family + the
fence + the deferred items (§5 below). HOL's
`test_cross_cutting.py` (H19) PASSES without retire-and-rebaseline
(no new top-level surfaces; everything sits under `framework/tools/`
which H19 admits).

**Outcome:**
- `git log --oneline | head -3` shows feature-commit + apply-commit + seal-commit triple per repo convention.
- HOL `test_cross_cutting.py` PASSES.
- `pytest framework/tools/pos-publish-framework-only/tests/` PASSES.

### AC.OSS-M2.7 — No work outside the named surfaces (negative AC)

The amendment's git-diff includes ZERO touches outside:

- `framework/tools/pos-publish-framework-only/...` (the entire
  subtree).
- `docs/plans/oss-v0-1-0-publish-partition.md` (this
  plan-doc).
- `docs/plans/oss-v0-1-0-publish-partition.manifest.yaml`
  (the amendment manifest YAML for `loam amend apply`).

**Permitted ZERO surfaces (no edits expected):**

- No HOL changes — M2 is tools-tree-only.
- No component seal-test allowlist edits — M2's surface doesn't
  cross `framework/<comp>/` for any sealed runtime component.
- No CLAUDE.md / CLAUDE.dev.md / STATE.md / odd-* / VALUE_PROPOSITION
  edits.
- No env-var / launchd / OTel / namespace changes.
- No path-string `/Users/lukeivers/ivers-corp-pos-v2/...` rewrites.
- No `framework/<comp>/seals/SEAL_COMMIT.*` edits (this is a
  sealed-component amendment for `pos-publish-framework-only`,
  but that tool has no `seals/` subdir per §11 finding #5; the
  HOL anchor is not invoked).
- No HC#4 byte-content sample SHA changes.

**Outcome:** `git diff <baseline>..<feature-commit-tip> --stat`
shows changes only in the named surfaces above.

### Behaviour-count check (ODD §3.3 forward)

Six outcome-named behaviours (manifest YAML authored, manifest
loader+classifier module, synth.py manifest consumption, default
partition completeness, CLI accepts manifest path, hard cutover)
→ six positive ACs (AC.OSS-M2.1..AC.OSS-M2.6). Plus the seal-
fence AC (AC.OSS-M2.S) and the negative-scope AC (AC.OSS-M2.7).
Match.

ODD §2.5 reverse direction (every diff line traces to a named
AC) is the builder's pre-seal audit; surfaced explicitly as
halt trigger §8.4.

---

## 5. Hard constraints (M2-specific)

- **Plan-before-code.** This plan-doc + the amendment manifest
  YAML committed before any source edit, per the dev CDC.
- **AC.OSS.3 fence.** Every AC assertion is path-shape, not
  content-shape. The synthesis tool decides what ships by path;
  the manifest is the path-classification source. Content-shape
  scrubs (path-substitution, fixture-name refactors) are M9, not
  M2.
- **Hard cutover.** No transitional dual-mode (manifest +
  hardcoded fallback). The hardcoded constants retire as part
  of M2.
- **Test scope is narrow.** Per
  `feedback_amendment_dispatch_speedups`, M2 skips pre-seal
  full-suite rerun. Touched-test rerun under
  `framework/tools/pos-publish-framework-only/tests/` is the
  methodology-aligned narrow verification. Plus a smoke check
  on the cross-tree consumer (`framework/workspace-bootstrap/
  tests/test_AC_SFR_4_pos_sync_composition.py`) since it imports
  the synth function — the new required `manifest_path` parameter
  could break it if not handled (§13 below).
- **`loam amend apply` runs BEFORE the seal commit** per
  `feedback_dispatch_explicit_pos_amend_apply` (post-M1g shape:
  `loam amend apply`, not `pos-amend apply`).
- **No `git commit --amend`** per
  `feedback_no_amend_in_agent_dispatches`. Corrective commits
  are NEW commits.
- **No new third-party deps.** `pyyaml` is already in the
  publish-tool's surface (verify in §11 finding #2). The
  classifier uses stdlib only otherwise.
- **AC.PO.1 + AC.PO.2 ladder-up.** M2 is harness-primitive
  growth (AC.PO.2). Persona-translation-burden (AC.PO.1) is
  unchanged at M2; the manifest is internal infrastructure.
- **Halt-and-surface conditions per §8 below.** Builder MUST
  halt on any of them; do NOT silently extend.

---

## 6. Out of scope (named explicitly per ODD §2.5)

- **Running the synthesis dry-run against canonical HEAD.** M11.
- **Path / personal-info scrub at synthesis time.** M9.
- **Publishing destination changes (M12).**
- **Public docs authoring** (`docs/positioning.md`,
  `docs/getting-started.md`, `docs/architecture.md`,
  `docs/components/<name>.md`, `docs/design/odd.md`). M7.
  M2's manifest declares forward-looking entries for these
  paths in `dev_and_public`; the files don't yet exist.
- **License + governance scaffold** (`LICENSE`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`). M8.
  Same forward-looking declaration as above.
- **`docs/CLAUDE_CAPABILITIES.md` rebrand / relocation** —
  out of M2 scope; the file currently lives at that path and
  M2's manifest classifies it as `dev_and_public`. If M7
  re-locates it, M2's manifest will need a follow-up edit.
- **Conditional partitioning** (e.g. "publish-only-when-X").
  M2's manifest is path-shape only; conditional rules are M9
  or M11 deferral if needed.
- **Per-component fine-grained partition** (e.g. "ship
  `framework/cost-governance/src/` but not
  `framework/cost-governance/tests/`"). M2's defaults are
  whole-component-glob; if downstream review wants to drop
  test directories from the public surface, that's a future
  follow-on amendment (FIDRAFT-tracked at §11 finding #6).
- **Shipping the dev-mode-manifest.yaml itself.** The dev-mode
  partition manifest at `docs/rebuild/dev-mode-manifest.yaml`
  is `dev_only` per the `docs/rebuild/**` glob. Correct: the
  audit's recommendation hides the entire `docs/rebuild/`
  tree.
- **`framework/tools/pos-publish-framework-only/` itself
  shipping in the public artefact.** The tool is `dev_only`
  per dispatch §3 + audit §4.4 (the tool's OUTPUT ships, not
  the tool itself).
- **Synthesis-time substitution for path scrubbing** (M9).
  The substitution table for personal-info scrub lands at M9;
  M2 doesn't introduce text rewrite at synth time.

---

## 7. Implementation order (suggested — builder's call to refine)

1. **Pre-flight verification.** `pwd` returns `/Users/lukeivers/
   ivers-corp-pos-v2`; `git rev-parse --abbrev-ref HEAD` returns
   `pos-v2`; `git status --short` shows working tree clean (only
   the pre-existing `personas/` untracked item remains). Verify
   `loam amend --help` works; verify
   `pos-publish-framework-only --help` works; verify
   `pytest framework/tools/pos-publish-framework-only/tests/`
   passes pre-build. Halt-and-surface if any check fires.

2. **BASELINE pin.** Pin to M1g's §14 backfill commit `d5b8dcd`
   (or HEAD if subsequent doc-only commits land first; verify
   by `git log --oneline | head -5`).

3. **Plan + manifest commit.** Commit this plan-doc + a manifest
   YAML at `docs/plans/oss-v0-1-0-publish-partition.manifest.yaml`
   per the established M1a..M1g precedent shape. Schema-version
   1 amendment manifest carrying baseline, plan path, seal_description,
   components (none), universal_paths admissions, narrative target.

4. **Phase A — Author the partition manifest YAML.** Write
   `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`
   per AC.OSS-M2.1's shape. Include the four sections + the
   default partition (per dispatch §3 + §4.1–§4.4 of the audit).
   Verify YAML is well-formed via `python -c "import yaml;
   yaml.safe_load(open('<path>'))"`.

5. **Phase B — Author the partition module.** Write
   `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/partition.py`
   per AC.OSS-M2.2's surface. Compose loader (mirror
   `loam_mode.manifest`'s shape and validation patterns) +
   classifier with first-match-wins precedence + `is_publishable`
   helper. Update `__init__.py` to export the new public surface
   (`load_manifest`, `classify_path`, `PartitionClass`,
   `PartitionManifest`, `ManifestError`).

6. **Phase C — Extend `synth.py`.** Add `manifest_path: Path`
   parameter to `synthesise_framework_only`. Replace the
   hardcoded `FRAMEWORK_PREFIX` + `TOP_LEVEL_DOCS` walk with a
   manifest-driven walk:
   - Use `git ls-tree -r <source-sha>` to enumerate every leaf
     path under canonical's tree (single git call; cheaper than
     per-entry ls-tree).
   - For each leaf, audit-exclude check first; then classify;
     fail with `SynthesisError` if any non-audit-excluded leaf
     returns None.
   - Build the synthetic tree by:
     (a) collecting `public_only ∪ dev_and_public` leaves
     (b) splitting them into "framework/<rel>" entries (rename
         to `<rel>` at root) vs "<rel>" entries (top-level
         overlay)
     (c) collision-detect (existing logic preserved)
     (d) `git mktree` with the assembled entry list
   - Retire `FRAMEWORK_PREFIX` + `TOP_LEVEL_DOCS` (delete or
     keep as inert string literals — D-build.M2.5 captures the
     decision).

7. **Phase D — Extend `cli.py`.** Add the `--manifest-path` CLI
   flag with default-resolution `<args.repo>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
   Pass it through to `synthesise_framework_only`.

8. **Phase E — Extend the test fixture (`conftest.py`).**
   `make_fixture_canonical` writes a fixture manifest into the
   fixture canonical at the expected path
   (`<canonical>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`)
   that classifies the fixture's paths. Minimal manifest:
   `dev_and_public` covers the fixture's framework entries +
   top-level docs; `dev_only` covers any fixture path explicitly
   meant to be excluded; `excluded_from_publish` and
   `public_only` empty. The fixture is the smallest manifest
   that satisfies completeness for the fixture's path set.

9. **Phase F — Author new tests.** Per §13:
   - `test_AC_OSS_3_partition_manifest_load.py` — schema-shape
     coverage.
   - `test_AC_OSS_3_partition_classifier.py` — classification
     correctness + first-match-wins precedence.
   - `test_AC_OSS_3_synthesis_drops_dev_only.py` — fixture
     canonical with both `framework/cost-governance/__init__.py`
     and `framework/tools/loam/cli.py`; assert post-synthesis
     tree contains the former and not the latter.
   - `test_AC_OSS_3_default_partition_complete.py` — runs against
     canonical HEAD; asserts every path under HEAD's `pos-v2`
     tree (modulo audit_excludes) classifies. (Builder's call:
     this could be merged into one of the above tests or kept
     standalone.)

10. **Phase G — Test sweep.** Run `pytest framework/tools/pos-publish-framework-only/tests/`. Halt-trigger §8.5 fires on
    non-zero. Plus run `pytest framework/workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py`
    to verify the cross-tree consumer still works (it imports
    `synthesise_framework_only`; if M2 made `manifest_path`
    required AND that test calls without it, it'll fail —
    builder's call to either pass an explicit `manifest_path`
    in the test OR provide a sensible default. Recommendation
    per §10 D-build.M2.4: keep `manifest_path` as a required
    parameter and update the cross-tree consumer to pass an
    explicit fixture-manifest path. The cross-tree consumer
    edit is admitted as a universal-style cross-tree-consumer
    rebrand under the same precedent as M1g.)

11. **Phase H — Feature commit.** Single feature commit carrying
    all of Phases A–G. Commit message names the M2 slug, the AC
    family (AC.OSS-M2.1..AC.OSS-M2.S), the tools-tree-only
    fence, and the master-plan pointer.

12. **Phase I — `loam amend apply`.** Run `loam amend apply
    docs/plans/oss-v0-1-0-publish-partition.manifest.yaml`.
    Verify clean apply.

13. **Phase J — Apply commit.** The apply commit (sidecars +
    seal-narrative scaffold) per `loam amend apply` convention.

14. **Phase K — Seal-diff fence verification.** AC.OSS-M2.S +
    AC.OSS-M2.7 — verify `git diff <baseline>..HEAD --stat`
    shows ONLY `framework/tools/pos-publish-framework-only/`
    + `docs/plans/oss-v0-1-0-publish-partition.{md,manifest.yaml}`.
    Verify `pytest framework/tools/pos-publish-framework-only/tests/`
    PASSES; HOL `test_cross_cutting.py` PASSES (no new top-level
    surfaces; existing admissions cover the diff).

15. **Phase L — `loam amend seal --plan-doc <abs-path>`.**
    Backfills §14 SHA register (this plan's §14 below). The
    seal commit narrative cites the AC family, the tools-tree
    fence, the manifest's default-partition shape, the deferred
    items (M9 scrub, M11 dry-run, etc.).

Phases A–B are pure authoring (manifest + module). Phases C–D
extend the existing surface. Phase E updates the fixture.
Phase F adds the new test surface. Phases G–L are test +
commit + seal mechanics.

---

## 8. Halt triggers (M2-specific)

Per the dispatch's halt-and-surface clause + dispatch-named §Halt-
and-surface enumeration:

1. **Audit's recommended partition contradicts actual feature
   wiring.** Per dispatch §Halt-and-surface #1: e.g. the audit
   recommends X is public but X is wired only in dev-mode hooks.
   Pre-build verification at plan-authoring (§11 below) checked
   the recommendation against the feature-usage audit's
   wired-vs-dormant matrix; no contradiction surfaced. Halt-
   trigger fires only if implementation reveals a NEW conflict.

2. **The synthesis tool's existing structure resists manifest-
   driven extension.** Surface specific structural concern.
   Pre-build verification (§11 below) confirms `synth.py`'s
   structure (single function, two hardcoded constants,
   git-plumbing-only) is straightforward to manifest-drive.
   Halt-trigger fires on a NEW structural blocker.

3. **A path can't be classified cleanly into the four classes.**
   E.g. a path that's "ship sometimes, depending on workspace
   contribution config." Surface the specific case. Pre-build
   verification: every path under canonical HEAD's `pos-v2`
   classifies cleanly per the dispatch §3 default partition.
   Halt-trigger fires only if a NEW such path emerges.

4. **The manifest needs to express conditional partitioning**
   (e.g. "publish-only-when-X"). Per dispatch §Halt-and-surface
   #5: flag as M9 or M11 deferral. Halt-trigger fires only if
   M2's default partition reveals a conditional-rule need.

5. **ODD §2.5 violations encountered in surrounding code.**
   Halt; do NOT silently extend. Surface for owner ruling on
   whether to fix in-band, defer, or reshape M2's scope. Per
   `feedback_subagent_odd_violation_halt`.

6. **Pre-existing test fails post-extension.** Halt; the manifest-
   driven extension has hit a non-mechanical change. Surface
   failing test + diagnosis. Per `feedback_amendment_dispatch_speedups`,
   the touched-test scope is `framework/tools/pos-publish-framework-only/tests/`
   + cross-tree consumer `framework/workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py`;
   any other component's pytest is out-of-scope per the
   amendment-build-narrowing speedup.

7. **Default partition not COMPLETE for canonical HEAD.** A
   `git ls-tree -r HEAD` leaf path doesn't classify into any
   of the four buckets (and isn't audit-excluded). Halt; the
   manifest needs more entries OR a class definition needs
   adjustment. This is `AC.OSS-M2.4`'s test asserting; if it
   fails during build, halt and amend the manifest.

8. **Wall-clock exceeds 70 min** (M2 is master-plan-priced
   25–45 min midpoint 35 min; halt-trigger fires at 1.5×
   upper bound). Halt with current-state report; dispatcher
   triages continue / split-further / pause.

9. **Cross-tree consumer break.** If the new required
   `manifest_path` parameter breaks
   `framework/workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py`
   in a way that requires more than a single-line update at
   the call site, halt — the API extension shape is wrong.
   Pre-build verification (§11 finding #7): the test calls
   `synthesise_framework_only(canonical)` once with no
   manifest_path; a single line update in the test passes a
   fixture manifest. Halt-trigger fires only if a deeper
   integration emerges.

10. **A `dev_only` glob accidentally swallows a `dev_and_public`
    path.** E.g. `framework/tools/loam/**` is `dev_only` and
    `framework/cost-governance/**` is `dev_and_public`; if a
    manifest-author error accidentally writes
    `framework/**` under `dev_only`, the runtime components
    misclassify. Mitigation: AC.OSS-M2.4's completeness test
    runs over canonical HEAD and would fail-loud (every
    runtime component's path now classifies as dev_only,
    which is wrong). Halt + amend manifest.

11. **Workspace-bootstrap or any other sealed component's
    seal-test regresses.** Pre-build verification: the
    workspace-bootstrap seal-test allowlist doesn't gate on
    `framework/tools/pos-publish-framework-only/`; the cross-
    tree consumer `test_AC_SFR_4_pos_sync_composition.py` does
    import `synthesise_framework_only` but its test-only edit
    is admitted under universal admissions per §11 finding #7.
    Halt-trigger fires only if a NEW seal-test gate surfaces.

12. **Hard-cutover violation.** Builder accidentally introduces
    a fallback to the hardcoded `FRAMEWORK_PREFIX` /
    `TOP_LEVEL_DOCS` constants. Halt; remove the fallback.

---

## 9. Risks (M2-specific)

1. **Cross-tree consumer break.** The
   `framework/workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py`
   imports `synthesise_framework_only` and calls it directly.
   If M2 makes `manifest_path` a required parameter, that test
   breaks. Mitigation: D-build.M2.4 — keep parameter required
   and update the call site to pass a fixture manifest path.
   The fixture-canonical has its own minimal manifest written
   by `make_fixture_canonical` per Phase E; the test's call
   needs `manifest_path=<canonical>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
   Single-line update.

2. **Default-partition completeness failure on canonical HEAD.**
   A leaf path the manifest author didn't anticipate (e.g. a
   newly-added top-level file from a recent amendment) returns
   None from `classify_path`. Mitigation: AC.OSS-M2.4 test
   runs `git ls-tree -r HEAD` and asserts completeness —
   fail-loud at build time. Phase G test sweep catches this;
   manifest amends with the missing entry.

3. **First-match-wins precedence subtlety.** A `dev_and_public`
   glob that's broader than a `dev_only` glob (or vice versa)
   produces the wrong classification under the wrong
   precedence rule. Mitigation: D-build.M2.3 fixes the
   precedence as `excluded_from_publish > dev_only >
   public_only > dev_and_public`. Test
   `test_AC_OSS_3_partition_classifier.py` covers overlapping
   entries explicitly.

4. **`pyyaml` may not yet be in the publish tool's pyproject.**
   Mitigation: §11 finding #2 verifies — `pyyaml` is already
   on the workspace's import path via several other components
   (loam-mode, hands-off-lifecycle, etc.) but the publish-tool's
   own `pyproject.toml` may not declare it. Builder verifies
   pre-Phase-B; if missing, adds `dependencies = ["pyyaml"]`
   to the publish-tool's pyproject (single-line edit; no new
   third-party dep at the workspace level).

5. **Wall-clock blow-out.** Plan-priced 25–45 min midpoint 35
   min. Principal source of variance is the test surface
   (4 new tests including the canonical-HEAD completeness
   test). Mitigation: §8 halt-trigger §8 fires at 70 min.

6. **Hardcoded-constants retire breaks an unobserved consumer.**
   Pre-build verification: `grep -rE "FRAMEWORK_PREFIX|TOP_LEVEL_DOCS"
   framework/ docs/`. Per §11 finding #8: only
   `synth.py` references these constants live; no other
   component imports them. Hard cutover is safe.

7. **Manifest authoring error.** A typo in a glob pattern
   misclassifies. Mitigation: AC.OSS-M2.4 + the
   `test_AC_OSS_3_synthesis_drops_dev_only.py` fixture-canonical
   test catch class-confusion; AC.OSS-M2.5 + manifest YAML
   load-time validation catches schema-shape issues.

---

## 10. Decisions remaining for owner ruling

**None** at the dispatcher level. Per master plan §13, all D1–
D12 + R1–R3 + D-1/D-2/D-3 rulings are LOCKED. M2's scope is
fully named in the dispatch.

**Builder's calls within ACs (NOT requiring owner ruling):**

- **D-build.M2.1 — Manifest top-level shape.** Builder's call
  within AC.OSS-M2.1: exact key names (`audit_roots` vs `roots`;
  `audit_excludes` vs `excludes`; etc.) and ordering. Recommendation:
  match `dev-mode-manifest.yaml`'s shape where possible
  (`roots`, `audit_excludes`, four partition-class keys);
  use `audit_roots` only if there's a naming conflict with
  the inherited `roots`. Plan-author recommendation: `audit_roots`
  (clearer than bare `roots` for a partition-style manifest).

- **D-build.M2.2 — Module decomposition.** Builder's call
  within AC.OSS-M2.2: single `partition.py` module vs split
  into `partition/manifest.py` + `partition/classifier.py`.
  Recommendation: single `partition.py` — matches
  `loam_mode/manifest.py`'s pattern (single module covers
  load + entry-shape + glob-match); minimal LOC; the module
  is bounded.

- **D-build.M2.3 — Classification precedence.** Builder's call
  within AC.OSS-M2.2: when an entry overlaps multiple classes,
  which class wins? Recommendation:
  `excluded_from_publish > dev_only > public_only > dev_and_public`.
  Rationale: `excluded` is the must-not-ship safety class
  (must be checked first to prevent leak); `dev_only` is the
  next-strictest (dev-tools must not accidentally promote);
  `public_only` and `dev_and_public` are the ship classes
  (overlap between them is benign, both ship). The
  classifier's first-match-wins iteration order is fixed in
  code, not in YAML.

- **D-build.M2.4 — Cross-tree consumer update strategy.**
  Builder's call within AC.OSS-M2.5 + AC.OSS-M2.7:
  `manifest_path` parameter required vs optional with default.
  Recommendation: required parameter — forces callers to
  decide. The cross-tree consumer
  (`workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py`)
  updates with a single line passing the fixture's manifest
  path. The CLI (`cli.py`) defaults the value from `<repo>/`
  (so end-user CLI usage is unchanged).

- **D-build.M2.5 — Hardcoded constants retire vs preserve as
  documentation.** Builder's call within AC.OSS-M2.6: delete
  `FRAMEWORK_PREFIX` + `TOP_LEVEL_DOCS` entirely vs keep them
  as inert documentation-only string literals. Recommendation:
  delete. Reason: ODD §2.5 reverse-direction ("every line
  traces to a backing AC") — preserving them as documentation
  is a residual ODD-noise; the manifest IS the documentation
  now.

- **D-build.M2.6 — Test-file split.** Builder's call within
  AC.OSS-M2.1..AC.OSS-M2.4: extend the existing
  `test_AC_SFR_2_synthesis_pipeline.py` vs author 3–4 new test
  files. Recommendation: 3–4 new test files (one per AC of
  the new partition-load + classify + drop + completeness
  surface) — matches the existing `test_AC_*.py` naming
  convention and keeps each test file scoped to one AC.

---

## 11. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit-
recommendation conflict with sealed-component invariants,
methodology breaches, or surrounding-code/-doc ODD violations.

**Findings during plan authoring:**

1. **(`framework/hands-off-lifecycle/hooks/` separation —
    needs builder verification.)** The audit (§4.3) recommends
    splitting HOL into "SessionStart hook + supervisor + first-
    run scaffold" (ships) vs "A1–A4 PreToolUse gates" (dev-
    only). M2's default partition assigns
    `framework/hands-off-lifecycle/**` to `dev_and_public`
    (whole-component glob). The audit's split is finer-
    grained: it would separately partition `hooks/` (hosting
    A1–A4 gates + bash_guard + agent_guard) as dev_only.
    **Plan-time decision (D-build.M2.7):** ship the whole HOL
    component at M2 — finer-grained partition is a future
    follow-on amendment (FIDRAFT-tracked at finding #6 below).
    Reason: HOL's hooks are LIVE in the runtime surface (per
    M1g `_loam_amend_dry_run` in bash_guard, `_LOAM_SURFACE_PATTERNS`
    in agent_guard); separating them out cleanly requires
    structural work beyond M2's scope. **Implication:** the
    public artefact at M2-time would carry HOL hooks; M11
    dry-run review will surface whether that's acceptable or
    whether a follow-on partition refinement is needed before
    public flip. M2 keeps the simpler default; if M11 finds
    "still looks like a rebuild because A1–A4 gates are
    present", that triggers a follow-on amendment. Surface to
    owner: this is a deliberate scope-conservatism call, not
    a halt.

2. **(`pyyaml` dependency on the publish tool's pyproject —
    needs verification.)** Pre-build verification at plan-
    authoring time: the publish-tool's
    `framework/tools/pos-publish-framework-only/pyproject.toml`
    declares no `dependencies` block. The tool currently
    composes git plumbing only (no YAML reads pre-M2).
    M2's manifest-load adds a `pyyaml` import. Pre-build
    builder verification: confirm `pyyaml` is import-resolvable
    in the publish-tool's editable install (it's available
    workspace-wide via `loam-mode` + `loam-cli` + others);
    if the publish-tool's pyproject needs an explicit
    `dependencies = ["pyyaml"]` declaration, add it (single-
    line edit; not a new workspace-level third-party dep —
    the workspace already requires pyyaml).

3. **(workspace-bootstrap admits `framework/tools/` broadly
    in its seal-test allowlist.)** Pre-build verification:
    `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py:274`
    admits `framework/tools/` (broad prefix); admits
    `tools/` (broad prefix); admits specific
    `framework/tools/loam-mode/` and
    `framework/tools/loam-migrate-dormancy-config/`. M2's
    edits sit under `framework/tools/pos-publish-framework-only/`
    which is already covered by the broad `framework/tools/`
    admission. NO seal-test regression risk.

4. **(No other component's `test_no_sealed_amendments.py`
    references `pos-publish-framework-only` or `publish-mode-manifest`.)**
    Pre-build verification:
    `grep -nE "pos-publish-framework-only|publish-mode-manifest"
    framework/*/tests/test_no_sealed_amendments.py` returns
    ZERO matches. Plus
    `grep -nE "publish-framework|publish_framework" framework/
    --include=test_no_sealed_amendments.py` returns ZERO outside
    workspace-bootstrap (which carries the cross-tree consumer
    test). NO cross-component allowlist edit needed at M2.

5. **(`pos-publish-framework-only` does NOT have its own
    `test_no_sealed_amendments.py` or `seals/` subdir.)**
    Pre-build verification: `find framework/tools/pos-publish-framework-only
    -name "test_no_sealed*" -o -name "SEAL*"` returns ZERO. The
    tool was sealed under #67 (single-framework-restructure)
    via HOL's anchor + the tool-tree fence; not a per-tool
    seal-diff invariant of its own. M2's seal commit therefore
    follows the same pattern as M1c..M1g: HOL is the meta-
    anchor (its `test_cross_cutting.py` H19 verifies no new top-
    level surface emerged + carries the seal narrative sidecar);
    the tools-tree fence is the structural fence. **Plan-time
    decision (D-build.M2.8):** register HOL as the no-op
    narrative anchor in the amendment manifest YAML
    (`components: [hands-off-lifecycle]`). Pre-build verification
    of `loam amend`'s manifest schema: `components` must be a
    non-empty list (`framework/tools/loam/src/loam_cli/amend/
    manifest.py:358`); empty `components: []` would fail
    schema-load. The HOL no-op anchor admits the SEAL_COMMIT
    sidecar bump + a SEAL_COMMIT.oss-v0-1-0-publish-partition
    narrative file under HOL's `seals/` subdir. The HOL diff is
    intentionally trivial (only the sidecar bump + the new seal
    narrative file) — no behaviour edits to HOL hooks or tests.

6. **(FIDRAFT capture: HOL hooks/ finer-grained partition.)**
    Per finding #1 above: a future FIDRAFT entry should track
    "HOL `hooks/` finer-grained partition for OSS publish —
    A1–A4 gates + bash_guard + agent_guard are dev-discipline
    machinery and should be `dev_only` at finer granularity
    than the whole-HOL-component glob in M2's default
    partition. Estimate ≈10-callsite cleanup amendment; out
    of M2 per scope-conservatism." Builder may surface to
    `FUTURE_IDEAS_DRAFT.md` per
    `feedback_future_ideas_draft_workflow`.

7. **(Cross-tree consumer enumeration.)** Pre-build
   verification: only `framework/workspace-bootstrap/tests/
   test_AC_SFR_4_pos_sync_composition.py` and
   `framework/workspace-bootstrap/tests/conftest.py` import
   from `loam.publish_framework_only.synth`. Per §11 finding
   #3, the workspace-bootstrap allowlist already admits
   `framework/tools/` broadly — no allowlist edit needed.
   The test edit (passing `manifest_path=...` to the
   `synthesise_framework_only` call) is admitted under
   universal admissions per the same precedent as M1g (the
   amendment manifest YAML's `universal_paths.files` block
   names the two test files explicitly). The sole call-site
   in `test_AC_SFR_4_pos_sync_composition.py:97` is line 97
   per pre-build grep.

8. **(`FRAMEWORK_PREFIX` / `TOP_LEVEL_DOCS` consumers.)** Pre-
   build verification: `grep -rE "FRAMEWORK_PREFIX|TOP_LEVEL_DOCS"
   framework/ docs/`. Only
   `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/synth.py`
   references these constants. NO cross-tree consumer; hard
   cutover via deletion is safe.

9. **(`framework/first-run-inventory.yaml` placement.)** Pre-
   build verification: this file lives at
   `framework/first-run-inventory.yaml`, not at workspace root.
   M2's manifest classifies it as `dev_and_public` (it's a
   workspace-bootstrap input that's used at runtime — confirmed
   by audit §4.3 + M1f's edit to the file). Correct.

10. **(`personas/` is workspace-side, not framework-side.)** Pre-
    build verification: `personas/` exists at workspace root
    (currently as untracked content per `git status`). It's
    referenced in `dev-mode-manifest.yaml`'s `audit_excludes`
    as `personas/**` ("untracked / pre-amendment-cleanup, not
    a partition member"). M2's manifest classifies it as
    `excluded_from_publish` defensively — the file is gitignored
    so `git ls-tree` won't see it, but the manifest declares
    intent.

11. **(No methodology breach; no surrounding-code ODD violation
    surfaced.)** Plan authoring did not encounter any ODD §2.5
    violation in the publish-tool's existing surface. The
    synth.py + cli.py + tests/ are clean.

---

## 12. Method-decision register (placeholder)

The method-decision content for M2 lives in §14 below per the
`loam amend seal --plan-doc` convention (which expects §14 as
the SHA-backfill anchor). Content moved to §14 to avoid
duplication.

§14 anchored from authoring per M1c..M1g locked precedent (avoid
post-seal restructure).

---

## 13. Test breakdown (post-build)

Per AC, the touched test files plus the cross-cutting verification:

- **AC.OSS-M2.1 (manifest YAML authored):** verified by
  YAML-load smoke (`python -c "import yaml; yaml.safe_load(...)"`)
  + `test_AC_OSS_3_partition_manifest_load.py` shape coverage
  (well-formed; missing section; bad entry; partition
  incompleteness).
- **AC.OSS-M2.2 (loader + classifier module):** verified by
  `test_AC_OSS_3_partition_manifest_load.py` (load) +
  `test_AC_OSS_3_partition_classifier.py` (classify with
  precedence cases — overlapping entries between
  dev_and_public + dev_only resolve to dev_only;
  excluded_from_publish wins over everything; audit_excludes
  yields None).
- **AC.OSS-M2.3 (synth.py consumes manifest):** verified by
  `test_AC_OSS_3_synthesis_drops_dev_only.py` — fixture
  canonical with mixed framework/cost-governance/ +
  framework/tools/loam/ + CLAUDE.md + CLAUDE.dev.md +
  docs/STATE.md + docs/positioning.md; assert post-
  synthesis `framework-only` tree contains the dev_and_public
  paths and does NOT contain the dev_only paths.
- **AC.OSS-M2.4 (default partition complete):** verified by
  `test_AC_OSS_3_default_partition_complete.py` — `git ls-tree
  -r HEAD` against the test's working repo;
  audit-exclude-filter; assert every remaining path classifies.
  (May be merged into one of the above tests.)
- **AC.OSS-M2.5 (CLI surface):** verified by
  `pos-publish-framework-only --help` returning `--manifest-path`
  in usage; subprocess invocation against fixture canonical
  with explicit `--manifest-path` returns 0.
- **AC.OSS-M2.6 (hard cutover):** verified by
  `git grep -nE "FRAMEWORK_PREFIX|TOP_LEVEL_DOCS"
  framework/tools/pos-publish-framework-only/src/` returning 0
  (full removal) or matches only in inert positions.
- **AC.OSS-M2.S (seal commit):** verified by HOL
  `test_cross_cutting.py` PASSING (no new top-level surface)
  + `pytest framework/tools/pos-publish-framework-only/tests/`
  PASSING.
- **AC.OSS-M2.7 (negative scope):** verified by `git diff
  <baseline>..HEAD --stat` showing only the named surfaces.

### Cross-tree verification

- `pytest framework/workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py`
  passes — the cross-tree consumer of `synthesise_framework_only`.
  M2 updates the call site (single-line edit per §11 finding #7
  + D-build.M2.4).

### Backwards-compat verification

- `pytest framework/tools/pos-publish-framework-only/tests/test_AC_SFR_2_synthesis_pipeline.py`
  passes — the existing synthesis-pipeline test suite. Phase E
  fixture extension makes this work without breaking changes
  to existing tests.

### HC#4 byte-content sample status

**No retire-and-rebaseline expected.** M2's edits sit entirely
under `framework/tools/pos-publish-framework-only/` plus the
plan-doc + manifest YAML; no HC#4 sample-file paths under
those subtrees per pre-build verification.

### Dependents cleared to dispatch (post-M2)

- **M9 (scrub)** cleared to dispatch — partition manifest is
  the contract M9's path-substitution + scrub tests read
  (per master plan §6 sequencing rule #2 + §6 sequencing rule
  #7).
- **M11 (dry-run)** cleared to dispatch — synthesis dry-run
  reads the manifest at M11 to produce the public artefact
  for review (per master plan §6 sequencing rule #2 + §6
  sequencing rule #8).

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-
backfill; method-decision narratives populated by builder during
build.)

### D-build.M2.1 — Manifest top-level shape

(Populated at build time. Recommendation per §10 D-build.M2.1:
`audit_roots` + `audit_excludes` + four partition-class keys;
schema_version = 1; each entry is `{path: ...}` or `{glob: ...,
exclude: [...]}`. Builder records exact key names actually used.)

### D-build.M2.2 — Module decomposition

(Populated at build time. Recommendation per §10 D-build.M2.2:
single `partition.py` module covering load + entry-shape +
glob-match + classify. Builder records actual module shape.)

### D-build.M2.3 — Classification precedence

(Populated at build time. Recommendation per §10 D-build.M2.3:
`excluded_from_publish > dev_only > public_only > dev_and_public`
first-match-wins. Builder records actual precedence + any
overlap-resolution edge case encountered.)

### D-build.M2.4 — Cross-tree consumer update strategy

(Populated at build time. Recommendation per §10 D-build.M2.4:
required `manifest_path` parameter; CLI defaults from `--repo`.
Cross-tree consumer (`workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py`)
updates with a single line passing the fixture's manifest
path. Builder records actual update + any other cross-tree
break encountered.)

### D-build.M2.5 — Hardcoded constants retire vs preserve

(Populated at build time. Recommendation per §10 D-build.M2.5:
delete entirely. Builder records actual outcome + reason if
preserved.)

### D-build.M2.6 — Test-file split

(Populated at build time. Recommendation per §10 D-build.M2.6:
3–4 new test files matching the existing `test_AC_*.py` naming
convention. Builder records actual test-file layout.)

### D-build.M2.7 — HOL hooks/ partition granularity

(Populated at build time. Recommendation per §11 finding #1:
ship whole HOL at M2 (whole-component glob); finer-grained
partition for `hooks/` is a FIDRAFT-tracked follow-on. Builder
records actual decision + FIDRAFT capture if appropriate.)

### D-build.M2.8 — Sealed-component fence: HOL no-op narrative anchor

(Populated at build time. Recommendation per §11 finding #5:
HOL no-op narrative anchor — `loam amend`'s manifest schema
requires `components` non-empty (`manifest.py:358`); HOL is
the conventional meta-anchor for tools-tree amendments per
M1c..M1g precedent. HOL diff is intentionally trivial
(SEAL_COMMIT sidecar bump + new SEAL_COMMIT.oss-v0-1-0-publish-
partition narrative file). Builder records actual outcome +
any deviation.)

### Commit SHAs

- Amendment commit: `41892e59f532aab94a54442c71ef8c1bdef2fe99` —
  `chore(partition-apply): loam amend apply for amendment #83 (M2 publish-mode partition manifest + synthesis tool extension)`
- Seal commit: `4cda805f138c878b8544cc31568b32ace6e9ac0e` —
  `chore(seals): M2 publish-mode partition manifest + synthesis tool extension — author publish-mode-manifest.yaml at framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml partitioning every workspace path into public_only / dev_and_public / dev_only / excluded_from_publish (four partition classes; default partition COMPLETE for canonical HEAD with first-match-wins precedence excluded_from_publish > dev_only > public_only > dev_and_public per plan §10 D-build.M2.3) + new partition.py module under framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/ (PartitionClass StrEnum + PartitionManifest dataclass + ManifestEntry dataclass + load_manifest + classify_path + is_publishable + glob-match semantics mirroring loam_mode.manifest._glob_match) + extend synth.py to consume the manifest (new manifest_path: Path required parameter on synthesise_framework_only; per-leaf classification via git ls-tree -r; SynthesisError on partition incomplete; hardcoded FRAMEWORK_PREFIX + TOP_LEVEL_DOCS constants RETIRE per hard cutover D-RNM.3-equivalent + plan §10 D-build.M2.5) + extend cli.py with --manifest-path flag (default <args.repo>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml) + extend tests/conftest.py make_fixture_canonical to write a fixture manifest into the fixture canonical at the same canonical path so existing AC.SFR.2 tests continue passing without test-side change + 4 new test files (test_AC_OSS_3_partition_manifest_load.py schema-shape coverage + test_AC_OSS_3_partition_classifier.py classification correctness + first-match-wins precedence + test_AC_OSS_3_synthesis_drops_dev_only.py fixture canonical with mixed framework/cost-governance/ + framework/tools/loam/ classification + test_AC_OSS_3_default_partition_complete.py canonical-HEAD ls-tree completeness check) + 1-line cross-tree consumer update in framework/workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py:97 passing fixture manifest_path. Hard cutover per plan §5 + master plan §6 — no transitional manifest-vs-hardcode dual mode. AC.OSS.3 (no dev-discipline machinery in public synthesis output) — M2 lands the manifest-driven mechanism; verification of AC.OSS.3 against canonical HEAD is M11's job. M2 gates M9 (scrub) + M11 (dry-run) per master plan §6 sequencing rule #2. Sealed-component fence: HOL no-op narrative anchor (per plan §11 finding #5 + D-build.M2.8 — loam amend manifest.py:358 requires components non-empty; HOL is the conventional meta-anchor for tools-tree amendments per M1c..M1g precedent; HOL diff is sidecar bump + new SEAL_COMMIT narrative file only) + structural fence framework/tools/pos-publish-framework-only/ (the structural surface). HC#4 byte-content sample status: NO RETIRE-AND-REBASELINE (no HC#4 sample paths under framework/tools/pos-publish-framework-only/; verified at plan-authoring per plan §13 HC#4 status). — hands-off-lifecycle at 41892e5`
## 15. References

- **Programme master plan:** `docs/plans/oss-v0-1-0-publish.md`
  (M2 row in §5; sequencing rule #2 in §6; AC.OSS.3 in §3).
- **Series predecessor:** `docs/plans/oss-v0-1-0-publish-rename.md`
  (M1.rename master) + sub-plans `oss-v0-1-0-publish-rename-1{a,b,c,d,e,f,g}.md`
  (sealed M1a..M1g 2026-04-29).
- **Authority documents (inherited from programme master):**
  - `.scratch/claude-output/oss-readiness-audit.md` §1.3, §2 D3, §4.1–§4.7 (partition recommendations).
  - `.scratch/claude-output/feature-usage-audit.md` (wired-vs-dormant matrix).
  - `.scratch/claude-output/oss-publish-master-dossier.md`.
- **Synthesis tool target:** `framework/tools/pos-publish-framework-only/`.
- **Schema-shape reference:** `docs/rebuild/dev-mode-manifest.yaml`
  + `framework/tools/loam-mode/src/loam_mode/manifest.py`
  (loader/coercion patterns the partition module mirrors).
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-loam:** `docs/odd-methodology.md`,
  `docs/odd-in-loam.md`.
- **VALUE_PROPOSITION:** `docs/VALUE_PROPOSITION.md`.
- **CLAUDE.md** + `~/.claude/CLAUDE.md` + `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`.
- **Memory bullets carried forward:**
  - `feedback_no_amend_in_agent_dispatches`.
  - `feedback_dispatch_explicit_pos_amend_apply` (post-M1g
    shape: `loam amend apply`).
  - `feedback_subagent_odd_violation_halt`.
  - `feedback_amendment_dispatch_speedups`.
  - `feedback_summarize_and_surface_decisions`.
  - `feedback_serialize_amendment_builds`.
  - `feedback_always_specify_wd_in_dispatches`.
  - `feedback_verify_post_amendment_state`.
  - `feedback_duration_estimation_rubric`.
  - `feedback_loose_AC_text_fix_AC_not_implementation`.
  - `feedback_critical_thinking_on_deviations`.
  - `feedback_strict_autonomy_no_pause_for_authorized_work`.
  - `feedback_future_ideas_draft_workflow`.
  - `feedback_value_proposition_as_prime_objective`.
- **Precedent single-component sealed-amendment manifests:**
  - `docs/plans/oss-v0-1-0-publish-rename-1c.manifest.yaml` (M1c launchd labels — comparable single-narrative-anchor shape).
  - `docs/plans/oss-v0-1-0-publish-rename-1g.manifest.yaml` (M1g — for the universal-admissions block precedent).
