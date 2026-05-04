---
description: Author a NEW component scaffold in the loam codebase from the standard template — `pyproject.toml` + `src/<package>/__init__.py` + `tests/` + `seals/` + `tests/SEAL_COMMIT` sidecar + README.md + first-run AC tests. Sealed-component readiness from the first commit (no retrofit later). Components live at `framework/<name>/` (canonical sealed components) or `plugins/<plugin>/` (plugin sub-packages); this skill captures both shapes. Use when adding a NEW sealed component or a NEW plugin sub-package; rare event but high cost-of-getting-wrong (sidecar shape + manifest schema + frozen-baseline policy must be right from the start).
---

# component-scaffold-author

New components are rare events in loam (the v0.1.x release
cadence has averaged ~1 NEW sealed component per release).
But the cost of getting the scaffold wrong is high: the
sidecar shape pins what `loam amend seal` writes; the
`frozen_baseline` policy decides whether the component takes
sweep tests at every seal; the README.md establishes the
component's external-facing contract.

A new-component scaffold authored half-assed — missing
sidecar, no first-run AC tests, README absent — fails the
sealed-component invariants the first time `loam amend
apply` runs against it. Recovery means a follow-on
amendment that authors the missing pieces, doubling the
work. This skill captures the standard template so the
scaffold lands right the first time.

## What this skill captures

The new-component scaffold layout (sealed component shape):

```
framework/<name>/
├── README.md                    # External-facing contract.
├── pyproject.toml               # Standalone Python package
│                                # (versioned 0.1.0 at scaffold).
├── seals/                       # Per-amendment narrative dir.
│   └── (empty until first seal)
├── src/
│   └── <package_name>/          # Importable Python package
│       │                        # name = <name> with hyphens
│       │                        # → underscores.
│       └── __init__.py          # Public API surface.
└── tests/
    ├── SEAL_COMMIT              # Sidecar — current sealed SHA.
    │                            # Initialized to BASELINE at
    │                            # scaffold time; advanced by
    │                            # `loam amend seal`.
    ├── SEAL_COMMIT.notes        # Optional human-readable notes
    │                            # paired with SEAL_COMMIT.
    ├── test_no_sealed_amendments.py
    │                            # Sealed-invariant test —
    │                            # required for every component.
    └── test_AC_<FAMILY>_*.py    # First-run AC tests.
```

Plugin sub-package shape (slightly different):

```
plugins/<plugin>/
├── ... (existing plugin files)
└── <subpackage>/
    ├── README.md
    ├── pyproject.toml
    ├── seals/
    ├── src/loam_<subpackage>/
    │   └── __init__.py
    └── tests/
        ├── SEAL_COMMIT
        └── test_AC_*.py
```

The required parts:

1. **`pyproject.toml`.** Standalone Python package config.
   Required: `[project]` with `name`, `version` (start at
   `0.1.0`), `description`, `requires-python`,
   `dependencies` list. `[build-system]` block with the
   project's standard backend (e.g., `setuptools`).
   Optional: `[project.scripts]` if the component exposes a
   CLI entry point.
2. **`src/<package_name>/__init__.py`.** Public API surface.
   Imports + re-exports the component's stable surface.
   Hyphens in component name → underscores in package name
   (e.g., `framework/workspace-bootstrap/` →
   `src/loam/workspace_bootstrap/`).
3. **`tests/SEAL_COMMIT` sidecar.** Single-line file
   carrying the current sealed SHA. At scaffold time, write
   `<scaffold-baseline-SHA>` (the source-edit feat commit
   creating the component). `loam amend seal` advances this
   file at every cycle.
4. **`tests/test_no_sealed_amendments.py`.** Sealed-invariant
   test — verifies the working tree's `<component>/` content
   matches the sidecar SHA's blob. Required for every sealed
   component; mirrors existing components' shape (e.g.,
   `framework/memory-system/tests/test_no_sealed_
   amendments.py`).
5. **`tests/test_AC_<FAMILY>_*.py`.** First-run AC tests
   covering the component's initial AC family (the family
   named in the scaffold cycle's plan-doc §4). One test
   file per AC, mirroring the dev-sdlc convention.
6. **`README.md`.** External-facing contract. Sections:
   - **What this component is** (1–3 paragraphs).
   - **Public API** (the `__init__.py` re-exports).
   - **Stake profile** (production-stake / dev-only /
     research-only — applies the `feedback_strict_
     autonomy` profile distinction).
   - **Sealed-component policy** (the file is part of a
     sealed-amendment cycle; see `loam-amend-cycle`).
   - **Composition** (other components / plugins this
     composes with).
7. **`seals/` directory.** Empty at scaffold time.
   `loam amend seal` writes per-cycle narrative files at
   `seals/SEAL_COMMIT.<slug>` for each amendment cycle.
8. **Manifest's `components:` block** (for the scaffold
   cycle's manifest):
   ```yaml
   components:
     - name: <name>
       seal_test: <component>/tests/test_no_sealed_amendments.py
       sidecar: <component>/tests/SEAL_COMMIT
       frozen_baseline: false  # or true if the component should
                                # NOT take sweep tests at every seal
       extra_allowed_prefixes: []
   ```

## When to use

Trigger conditions:

- Adding a NEW sealed component to `framework/<name>/`.
- Adding a NEW plugin sub-package to `plugins/<plugin>/
  <subpackage>/`.
- Reviewing a draft scaffold for sealed-component readiness
  (verify all 8 required parts present before the scaffold
  commit lands).
- Repairing a partial scaffold authored without this skill
  (e.g., sidecar missing, no `test_no_sealed_amendments.py`).
  Different from a regular amendment cycle: the repair has
  to retrofit sealed-component readiness.

Skip when:

- The change is to an EXISTING component — different shape;
  use `loam-amend-cycle` skill for the amendment.
- The change is to a workspace-local file or a non-package
  Python module (no `pyproject.toml` / `tests/` / `seals/`
  needed).
- The change adds a CLI entry point to an existing component
  (use the existing component's `pyproject.toml`'s
  `[project.scripts]` section; no new component scaffold
  needed).

## How the persona applies it

1. **Verify the working directory.** `pwd` confirms canonical
   pos-v2 (or the appropriate dev-mode workspace).
2. **Confirm the component name follows convention.** Hyphens
   in directory name; underscores in package name. The package
   name is what `import` statements use.
3. **Decide the stake profile.** Production-stake (gates on
   contract violations; default for `framework/`),
   dev-stake (more permissive; default for `plugins/dev-
   sdlc/`), or research-stake (lowest gates; for
   exploratory `plugins/<research>/`). Profile lives in
   the README and shapes downstream gating.
4. **Author the plan-doc per `plan-docs-author` skill.** The
   scaffold cycle is a normal sealed-component amendment; the
   plan-doc names §3 fence (the new component path), §4 ACs
   (initial AC family), §11 provenance (master plan / parent
   feature ask), and §14 method-decision register.
5. **Author the manifest per schema v3.** `components:`
   block points at the new component; `frozen_baseline:`
   default `false` (the component starts mutable and tightens
   later if needed).
6. **Author `pyproject.toml`** with the standard fields.
   Reference an existing component's `pyproject.toml` as a
   template (e.g., `framework/workspace-bootstrap/pyproject.
   toml` for sealed-component shape; `plugins/dev-sdlc/pr-
   safety/pyproject.toml` for plugin sub-package shape).
7. **Author `src/<package>/__init__.py`** with empty/minimal
   content + a docstring naming the component's purpose.
   Public re-exports come as the cycle's source-edit commits
   land.
8. **Author `tests/test_no_sealed_amendments.py`** by
   copying an existing component's version + adjusting the
   component-path constants. The test verifies the working
   tree matches the sidecar SHA.
9. **Author `tests/SEAL_COMMIT` sidecar** with the placeholder
   `<set-by-build-agent-post-source-commit>`. The
   `loam amend seal` command writes the actual SHA at first
   seal.
10. **Author the first-run AC tests** per the plan-doc §4 AC
    family. One test file per AC; per-AC granularity per
    `feedback_dispatch_brief_authoring`.
11. **Author `README.md`** covering the 5 sections (what / API
    / stake / sealed-component policy / composition).
12. **Initialize `seals/` as empty directory.** Add a
    `.gitkeep` if the project's git config strips empty
    directories; otherwise skip.
13. **Run `loam amend validate`** against the manifest —
    catches schema errors (missing component fields, invalid
    sidecar paths) before the apply.
14. **Run `loam amend apply --plan-doc <abs path> <manifest>`**
    — lands the manifest+apply merged commit. The new
    component now has its first apply commit.
15. **Run `loam amend seal --plan-doc <abs path> <manifest>`**
    — sweep tests run; sidecar advances; first seal commit
    lands. The component is now sealed-amendment-ready.
16. **Backfill §14 method-decision register** + master-plan
    §9 row per `loam-amend-cycle` skill step 9.

## Graceful degradation

When raw Claude Code without loam dev-sdlc plugin:

- The 8 required parts apply to any new Python package in
  any project. Substitute `loam amend apply` / `seal` with
  manual sidecar bookkeeping (a `VERSION` file or
  `CHANGELOG.md` rollup commit).
- The sealed-component invariants are loam-specific; in a
  generic project, the equivalent is "every test passes
  against the latest commit on main"; the `test_no_sealed_
  amendments.py` becomes a CI-run-on-main job.
- README's "stake profile" section is loam-specific
  (production-stake / dev-stake / research-stake); in a
  generic project, substitute with whatever stability tier
  the project uses.
- Detection on fallback: if a new component is being added
  WITHOUT a tests/ directory or WITHOUT a README, the
  scaffold is incomplete. Surface the gap inline. See
  `graceful-fallthrough-with-detection`.

## Composition

- **`loam-amend-cycle` skill** — the wider cycle ladder.
  Component scaffold IS a sealed-component amendment;
  steps 1–5 of the loam-amend-cycle ladder apply. This
  skill drills into step 5's source-edit-feat content
  for the new-component case.
- **`plan-docs-author` skill** — the plan-doc for the
  scaffold cycle. §3 fence names the new component; §4
  ACs name the initial AC family.
- **`seal-narrative-writer` skill** — the seal narrative
  for the scaffold cycle's first seal commit. Same
  short-form shape applies.
- **`feedback_no_amend_in_agent_dispatches`** — if the
  scaffold misses a piece (e.g., README forgotten), author
  a NEW corrective commit, never `git commit --amend`.
- **`audit-finding-triage` skill** — if a build agent
  surfaces a halt-and-surface finding ("scaffold missing
  test_no_sealed_amendments.py"), the triage routes the
  recovery.
- **Existing components as reference** — `framework/
  workspace-bootstrap/`, `framework/memory-system/`, and
  `framework/workspace-sync/` are reference scaffolds.
  Match their shape unless the new component has a clear
  reason to deviate.
- **Plugin sub-packages as reference** — `plugins/dev-
  sdlc/odd-extractor/`, `plugins/dev-sdlc/pr-safety/`,
  `plugins/dev-sdlc/tools/loam-mode/` are reference
  shapes for the plugin sub-package case.
- **`feedback_critical_thinking_on_deviations`** — if the
  new component has a reason to deviate from the standard
  scaffold (e.g., `frozen_baseline: true` from day 1, or
  no `__init__.py` because it's not a Python package),
  enumerate the deviation + name the rationale in §14.

## Out of scope

- Migration of an EXISTING non-sealed package to sealed
  status — different shape; the migration cycle authors
  the missing parts as a retrofit, not a from-scratch
  scaffold.
- Component decommissioning / removal — different ritual;
  see future `component-decommission` SKILL (not yet
  authored; FIDRAFT-shape if the need surfaces).
- Plugin scaffolding (a NEW plugin, not a new sub-package
  inside an existing plugin) — different shape (plugin
  manifest, plugin-level `pyproject.toml`); future SKILL.
- The pyproject.toml schema itself — lives in PEP-621 +
  the project's standard build backend; this skill
  references the required fields but doesn't enumerate
  PEP-621.
- The `frozen_baseline: true` policy — applies when a
  component should NOT take sweep tests at every seal
  (e.g., a large frozen reference dataset); decision
  carries to §14 method-decision register.
- Stake-profile design rationale — lives in
  `feedback_strict_autonomy` + production-stake docs;
  this skill references stake profiles but doesn't
  justify their existence.
- The first-cycle initial-AC family choice — application
  decision; the plan-doc §4 captures the choice; this
  skill names that the first-run tests must exist, but
  doesn't enumerate which ACs.
