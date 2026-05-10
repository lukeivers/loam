# loam — public-surface manifest

**Status:** v0.7.1 first-publish; the v1.0 contract surface as currently understood.
**Authority:** `docs/release-versioning-policy.md` §1.0.0 — the 6-month backwards-compat commitment loam will honor from 1.0.0 ship date. `docs/release-roadmap.md` v1.0 entry — outcome shape.
**Composes with:** `docs/architecture.md` ("plugin extension protocol"), `docs/release-process.md` (publish gates), `docs/plugins/dev-sdlc.md` (the reference plugin demonstrating the contract).
**Scope:** lists every public surface that loam commits to preserving for at least 6 months from the 1.0.0 ship date. Anything in this manifest is a contract; anything explicitly out-of-scope or unlisted may change without notice. Breaking changes after the 6-month window bump to 2.0.0 with deprecation warnings shipped in the prior minor (per `docs/release-versioning-policy.md`).

---

## §1 — Why this manifest exists

The v1.0-readiness audit at `workspace/.scratch/claude-output/v1-0-readiness-verification-2026-05-10.md` §3 named the structural prerequisite for the 6-month commitment to be realistic (not aspirational): a public-surface manifest naming exactly what's frozen at 1.0. Without that manifest, "we won't break anything for 6 months" reduces to "trust us"; with it, third parties (plugin authors, downstream embedders, integrators) can build against named surfaces with structural confidence.

The manifest is the v0.7.1 deliverable. Structural enforcement — a CI test that fails if any listed surface drifts — is captured for v0.8.0+ per the audit's recommended close path; v0.7.1 ships the manifest itself as the authoring deliverable. The manifest is informative until structural enforcement lands; it is normative for owner-visible review at every release.

---

## §2 — Public surfaces (commitments)

### §2.1 — CLI verbs (`loam <verb>`)

The following top-level CLI verbs are public; their argparse signature (subcommand name, required positional args, named flag names + types) will not break-change for 6 months from 1.0.0. New flags + new sub-verbs may be ADDED (additive change is non-breaking); existing flags + sub-verbs will not be removed or renamed without bumping major.

| Verb | Source-of-truth | What's frozen |
|---|---|---|
| `loam init <path>` | `framework/loam-init/` | The verb name + the positional `<path>` argument + the canonical contract that the post-init workspace is operational against the documented quickstart. Added flags (`--from`, `--init-existing`, `--persona-handle`) are also frozen at their current shape. |
| `loam release <version>` | `framework/tools/loam/src/loam_cli/release/` | The verb name + positional `<version>` + flags `--dry-run`, `--release`, `--repo-root`. Pre-publish gates table at `docs/release-process.md` §1 is the contract surface; gates may be ADDED but not removed in 6-month window. |
| `loam onboard [<path>]` | `framework/loam-init/` (entry-point) | The verb name + optional positional `<path>` + the documented env-var seams (`LOAM_ONBOARDING_SKIP=1`, `LOAM_ONBOARDING_SURVEY=<path>`). Question-set is informally stable; question-text changes are non-breaking; question removal is breaking. |
| `loam odd-extract` | `plugins/dev-sdlc/odd-extractor/` | The verb name + the documented chain-stage flags (`--interview`, `--gaps`, `--build-next`) + `--live`, `--budget-cents`, `--synthesis-timeout`, `--budget-override`. Output schema TBD; current output stability is best-effort until the chain-stage AC family seals. |
| `loam project <subverb>` | `plugins/dev-sdlc/` | The verb name + sub-verbs `new`, `status`, `advance`, `list`, `gate`. Each sub-verb's argparse signature stable; sub-verb addition non-breaking. |
| `loam amend <subverb>` | `plugins/dev-sdlc/tools/loam-amend/` | The verb name + sub-verbs `validate`, `apply`, `seal`, `template`, `new-plan`, `new-memory`. The amend manifest YAML schema is part of the public contract — see §2.4. |
| `loam pr-safety <subverb>` | `plugins/dev-sdlc/pr-safety/` | The verb name + sub-verbs `gate`, `install`, `hook-fire`. CI-template surface (GitHub Actions / GitLab CI / CircleCI templates) is part of the contract. |

**Not in this list = not committed.** The presence of a CLI verb in the codebase that isn't listed here means it's internal / experimental / not committed for backwards-compat. Two examples currently: any `loam <verb>` registered via plugin entry-point but NOT listed above is third-party-territory; the harness commits to the entry-point group's stability (§2.2), not to the verb's own surface.

### §2.2 — Plugin entry-point groups

The following Python entry-point group names are public; loam commits to discovering plugins via these groups. The group names themselves will not change for 6 months from 1.0.0; the discovery mechanism (Python `importlib.metadata.entry_points()`) is the contract.

| Entry-point group | Discovered by | What plugins contribute |
|---|---|---|
| `loam.bootstrap.contributions` | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/discovery.py` (constant `_ENTRYPOINT_GROUP`) | Hook handlers, settings fragments, components, skills — composed into the workspace's effective configuration during `loam init`. |
| `loam.cli.subcommands` | `framework/tools/loam/src/loam_cli/cli.py` | Top-level `loam <verb>` subcommands, registered as `<verb> = <module>:<build_callable>`. The build-callable contract is `def build_<verb>_subcommand(subparsers) -> argparse.ArgumentParser`. |

The build-callable contract for `loam.cli.subcommands` (`build_<verb>_subcommand`) is part of the public surface — third-party plugin authors writing CLI verbs follow this exact callable shape. Reference implementations: `loam_amend.cli:build_amend_subcommand`, `loam_pr_safety.cli:build_pr_safety_subcommand`.

### §2.3 — workspace-bootstrap manifest schema (`<workspace>/.pos/manifest.yaml`)

The following manifest fields are public. New fields may be ADDED at minor versions (additive); field renames or removals require major version bump (subject to the 6-month commitment).

| Field | Type | Source-of-truth | What's frozen |
|---|---|---|---|
| `primary_channel` | string (`telegram` \| `terminal`) | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` | Field name + value enum + migration default from `channel_preference` for pre-v0.7.0 workspaces. |
| `safety_profile` | string (`exploratory` \| `production-stake`) | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` | Field name + value enum. `production-stake` floors are SOC-2 non-tunable; floor schema is part of the contract. |
| `channel_preference` | string | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` | LEGACY field (predates `primary_channel`); kept for backwards-compat; new code reads `primary_channel` with migration default from this field. Will not be removed in 6-month window. |
| `dev_intent` | string (`yes` \| `no`) | `<workspace>/personas/primary/contract.yaml` (field) | Field name + value enum. Used by dev-mode auto-load partition; non-tech-user workspaces resolve to `dev_intent: no`. |
| `education_verbosity` | string (`terse` \| `default` \| `richer`) | survey field; consumed by `framework/primary-persona/skills/light-touch-narration.md` | Field name + value enum. Toggles narration sentence-budget. |

Other fields exist in onboarding-written manifests; they are NOT in the public contract unless listed here. Plugin authors who depend on additional fields should opt-in via the contribution shape (§2.2), not by reading manifest.yaml directly.

### §2.4 — Amendment manifest YAML schema (`docs/plans/<slug>.manifest.yaml`)

The amendment manifest is the contract `loam amend apply <manifest>` consumes. The following top-level keys are public. New keys may be ADDED; existing keys + their value shapes are frozen.

| Top-level key | Value shape | What's frozen |
|---|---|---|
| `schema_version` | integer (currently `3`) | The integer is the migration handle; bumps follow the documented migration path. |
| `amendment.slug` | string | Slug shape (lowercase + hyphens + version prefix) is informally stable; canonical slug shape published in templates. |
| `amendment.title` | string | Free-text; not contract-shaped. |
| `baseline` | string (commit SHA) | Captured at apply-time; the SHA is the BASELINE the diff measures against. |
| `plan` / `plan_doc_ref` | string (path) | The plan-doc the §status / §13 backfill writes to. |
| `ac_count` | integer | Total AC count; informational. |
| `smoke_outcome` | string | One-paragraph outcome summary; informational. |
| `components` | list of {`name`, `seal_test`, `sidecar`, `frozen_baseline`, `extra_allowed_prefixes`} | Each component fence's seal-test invariant location. The 5-field shape is frozen. |
| `universal_paths` | {`prefixes`: [string], `files`: [string]} | Universal-admission allowed paths beyond the component fence. The 2-key shape is frozen. |
| `narrative.target` / `narrative.body` | string / multi-line string | The seal-commit sidecar narrative. Frozen shape. |

**Plan-doc structure** (consumed by `loam release` gate `acs-verified`): the plan-doc `## §13 — §status` heading is the canonical AC-verification surface. The literal heading text `## §13 — §status` is part of the contract — gate parsing depends on this exact form (per the v0.7.0 publish-gate failure with `## §12 — §status`).

### §2.5 — File-based memory contract (`<workspace>/.loam/memory/`)

The file-based memory substrate (FBE.7 canonical at v0.5.0+) exposes the following on-disk contract:

| Surface | What's frozen |
|---|---|
| `<workspace>/.loam/memory/` directory | The memory store location. Resolved by `memory_dir_for_workspace()` in `framework/primary-persona/src/loam/primary_persona/file_memory.py`. |
| Episode file shape | One markdown file per turn; named with timestamp + scope id; YAML frontmatter (timestamp, scope, tags, optional embedding) followed by the episode body. The frontmatter key set (`timestamp`, `scope`, `tags`) is frozen; additional keys may be added. |
| Memory write queue | Stop-hook writes are queued to `<workspace>/.loam/memory-write-queue/` first; drained to the episode store by a worker. The queue location + the queue-file format (one episode per file) are frozen for plugin-author memory-substrate replacements. |
| Diagnostic log | `<workspace>/.pos/memory-writes.log` — failure-soft inspection surface. Path is frozen; log line shape is informally stable. |

**`MemoryProvider` Protocol** (`framework/primary-persona/src/loam/primary_persona/file_memory.py`): plugin authors writing alternative memory substrates implement this Protocol + contribute through the workspace-bootstrap entry-point. The Protocol method signatures are part of the public contract.

### §2.6 — Hook contracts (Claude Code lifecycle integration)

loam contributes to the following Claude Code lifecycle hooks. Each hook's emitter location + the JSON shape it returns are public.

| Hook | Emitter | Frozen surface |
|---|---|---|
| `SessionStart` | `framework/primary-persona/src/loam/primary_persona/session_start_emitter.py` | The greeting + memory-load JSON shape. Memory-load entries surface as the persona's at-session-start context. |
| `UserPromptSubmit` | `framework/primary-persona/src/loam/primary_persona/file_memory.py` (read path) | Memory retrieval shape — BM25 + grep length-normalization (per v0.4.3 fix). The retrieval signature (input prompt, output ranked episodes) is frozen. |
| `Stop` | `framework/primary-persona/src/loam/primary_persona/stop_emitter.py` | The episode-write JSON shape. Episode entries written to the queue per §2.5. |

### §2.7 — On-disk workspace conventions

Beyond the memory contract (§2.5), the following workspace paths are part of the public contract:

| Path | Purpose | What's frozen |
|---|---|---|
| `<workspace>/.loam/` | loam's per-workspace state directory (memory, corpus overrides, contributions discovery cache). Convention-frozen. |
| `<workspace>/.pos/` | Per-workspace persistence (manifest.yaml, memory-writes.log, sync state, audit log). Path + directory structure frozen. |
| `<workspace>/personas/primary/contract.yaml` | The primary-persona's per-workspace contract (dev-intent, education-verbosity, channel-preference). Field names per §2.3. |
| `<workspace>/.claude/settings.json` | Claude Code settings; loam writes the workspace-level fragment during `loam init` (idempotent). The hooks loam registers + the settings keys it writes are frozen. |
| `<workspace>/.claude/skills/` | Plugin-contributed SKILL packages. Discovery + registration shape is frozen (Claude Code-native discovery). |

### §2.8 — Release-process gates contract

The release-process gates table at `docs/release-process.md` §1 is the public contract for what `loam release <version>` checks. Each gate's name + its check-description + the source-of-truth file it reads are frozen for the 6-month commitment.

Currently 7 gates: `hard-smoke`, `acs-verified`, `state-shipped`, `clean-tree`, `branch-main`, `seal-reachable`, `system-binary-operational`. New gates may be ADDED at minor versions; gates may not be removed without major bump.

The CLI exit-code shape (0 = all gates GREEN; non-zero = at least one RED) is part of the contract.

---

## §3 — Explicitly NOT public surfaces

The following are NOT covered by the 6-month backwards-compat commitment. Changes here are non-breaking from a SemVer perspective:

- **All Python module names + function signatures NOT listed above.** Internal modules under `framework/<component>/src/loam/<component>/` are NOT public unless explicitly listed in §2 (e.g., the `MemoryProvider` Protocol IS listed; helper functions inside `file_memory.py` are NOT). Plugin authors should consume the documented entry-points + Protocols, not internal modules.
- **All test-suite internals.** `tests/` directories under any component or plugin are NOT public. Test fixtures, conftest helpers, parametrize IDs may change at any time.
- **Internal CLI argparse internals.** The argparse `Namespace` shape returned to internal subcommand handlers is NOT public; only the user-facing argparse signature (verb name + positional + flag names + flag types as documented in `--help`) is public.
- **Editable-install paths in `install-from-source.txt`.** The file's tier ordering + comments are informally stable but not contract-shaped. The contract is "after `pip install -r install-from-source.txt`, every documented `loam <verb>` works." HOW that's wired internally may change.
- **The `framework/` ↔ `<workspace>/framework/` workspace-sync layout.** The workspace-sync internal layout is NOT public. The workspace-bootstrap composition output IS public (the `.claude/settings.json` written, the hook contracts wired up); how the bootstrap reads from `framework/` to produce that output is not.
- **Component package organisation.** Whether a component lives under `framework/` or `plugins/dev-sdlc/tools/` (e.g., the `loam-amend` MOVE from `framework/tools/loam/src/loam_cli/amend/` to `plugins/dev-sdlc/tools/loam-amend/` at M6b.1) is NOT public. The `loam <verb>` user surface IS public; where the verb's source code lives may change.
- **Memory backend choice.** v0.7.1 ships file-backed-episode memory (FBE.7) as canonical. Future minors may add alternative substrates (graphiti-class re-implementation per release-roadmap.md backlog) discoverable via plugin contributions. The `MemoryProvider` Protocol contract is public; the default substrate's internal implementation may change.
- **Internal data-flow primitives (scope-of-work envelope, objective-tracker forest, observability-aggregator schema).** These compose with each other; their internal contracts may evolve. External consumers should use the per-component CLI surfaces (where exposed).
- **Synthesis routing.** The `claude -p --strict-mcp-config` invocation shape is an internal architectural constraint, not a public-API commitment. v0.7.1 routes all LLM calls this way; future minors may extend (e.g., parallel-shape variants) without breaking existing consumption.
- **Plugin-suite organisation.** What plugins ship in the canonical install vs need third-party authoring may change. The `loam.bootstrap.contributions` + `loam.cli.subcommands` discovery mechanisms are public; which plugins are auto-installed is not.

---

## §4 — Contract-evolution mechanics

The mechanics by which loam evolves the contract:

1. **Additive changes are always non-breaking.** New CLI verbs, new manifest fields, new hook handlers, new gates — all may ship at any minor version.
2. **Renames of public surfaces require deprecation in the prior minor.** A field rename ships first as `<old> + <new>` aliased; the old name is retired in the next major bump.
3. **Removals of public surfaces require major bump + deprecation in the prior minor.** v1.0 commits to no removals for 6 months minimum from ship.
4. **Schema-version bumps follow the documented migration path.** `schema_version: 3` is the v0.7.0 + v0.7.1 amendment manifest version; bumps require migration documentation.
5. **Entry-point group renames are major-bump only.** The two entry-point group names listed in §2.2 are the most stable surface; their renaming would break every plugin in the wild.
6. **What this manifest commits to is INFORMATIVE until structural enforcement lands.** A CI test that fails on drift between this manifest and the actual exposed surface is the v0.8.0+ candidate per the v1.0-readiness audit §5 step 8. Until that lands, this manifest is owner-reviewed at every release per the post-ship review block.

---

## §5 — Authority chain + composition

- `docs/release-versioning-policy.md` §1.0.0 — defines the 6-month commitment that this manifest operationalises.
- `docs/release-roadmap.md` v1.0 entry — names the v1.0 outcome shape.
- `docs/architecture.md` "plugin extension protocol" — names the structural contract surface; this manifest's §2.2 quotes it.
- `docs/release-process.md` §1 — the 7-gate release-process table; this manifest's §2.8 quotes it.
- `docs/plugins/dev-sdlc.md` — the reference plugin demonstrating §2.2 contract; this manifest does not duplicate plugin author guidance, only names what's contract-frozen.
- `workspace/.scratch/claude-output/v1-0-readiness-verification-2026-05-10.md` — the audit that surfaced the need for this manifest.

This manifest composes with `feedback_locked_design_not_license_for_bad_outcomes` — surfaces named here as "frozen" are committed but revisitable when their outcomes turn out bad; revisit triggers a major bump conversation, not a silent change. The 6-month commitment is operational, not absolute.
