# OSS Dev-Architecture Survey + loam Migration Plan

Authored: 2026-05-04. Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`.

## Executive summary (plain English)

You are right that the current loam dev architecture is "wildly against standard practice." After surveying 10 reference Python OSS projects (Poetry, Flask, FastAPI, Black, Ruff, pre-commit, attrs, swarms, LangChain, llm) plus Anthropic's own `claude-code` plugin layout, **none of them maintain a separate private dev repo that is then synthesised into a public release repo by a custom tool.** The dominant pattern is brutally simple: one public repo, work happens on `main`, tags drive PyPI publishes, and "dev internals" either live in `docs/` next to user-facing material or are deleted from the repo entirely (kept as personal/local notes that never get committed).

The one comparator that does what loam currently does — Carlos Santillana's "open source code from a private monorepo" article (DEV.to, 2024) — describes a **company-internal tool** that exposes pieces of a closed-source proprietary monorepo, not a project meant to be developed entirely in the open. That use case does not apply to loam, which is intended to be a published OSS framework.

**The current loam architecture appears to have been built solving an imaginary problem.** The "hide dev internals from strangers" premise that motivated the `dev_only` partition class, the synthesis tool, the partition manifest, and the dual-ref push mechanism is not a problem standard OSS projects solve. They show their dev internals — `CONTRIBUTING.md`, design notes, RFCs in `docs/dev/`, planning material in GitHub issues / discussions / wikis. **Visible dev internals are a contributor-attraction feature, not a leak.** What actually needs to be hidden is secrets, host-specific paths, and runtime state — and that's solved with `.gitignore`, not a synthesis pipeline.

The cost of this mistake to date is significant and quantified below: **~153 commits out of 313 in the 2026-04-30 → 2026-05-04 window (≈48%)** were FBE-foldback / OSS-publish pipeline work — i.e. roughly half of all dev-cycle effort in the past five days went into making a synthesis pipeline that standard practice doesn't need. The synthesis tool itself is **1,431 LOC of source + 2,468 LOC of tests** (3,899 total), and the partition manifest (now ~250+ lines of YAML) imposes a per-amendment classification tax on every new path.

The recommendation: **collapse to a single public repo (`lukeivers/loam`), publish via tag-on-`main` to PyPI, treat `lukeivers/ivers-corp` as legacy / archive it after a one-shot history transfer, deprecate the synthesis tool entirely, and demote the partition manifest's role from "publish gate" to "directory convention + `.gitignore`".** Migration is feasible in 1–2 days of AI-time + ~1 hour of Luke-time (decisions + GitHub-side public-class actions). It is fully reversible at every step until the legacy repo is archived. **Five public-class decisions** are escalated at the bottom.

This recommendation explicitly applies F2 ruthless feedback and locked-design-not-license. The synthesis pipeline is a locked design whose outcomes have been bad: 11 FBE foldback amendments, repeated stranger-clone breakage, repeated "publish-side branch-name divergence" BLOCKERs (FBE6c.1, FBE6b.1, FBE9.1, FBE10), each costing a full amendment cycle to surface and close. Locked design is not license to keep paying that cost.

---

## Section 1 — Survey of standard OSS dev architecture

10 reference projects + 1 ecosystem comparator. Each verified via WebFetch on 2026-05-04.

### 1.1 — python-poetry/poetry

- **Repo shape:** single repo, default branch `main`.
- **Where dev happens:** trunk-based on `main` via PRs from feature branches; no separate `dev` branch.
- **Dev internals:** `CONTRIBUTING.md` at root; contributing docs published to `python-poetry.org/docs/contributing`. No `docs/dev/`, no separate RFC tree.
- **`docs/`:** end-user (user guide, CLI ref); built by Sphinx via Read-the-Docs.
- **Releases:** GitHub Release event (`on: release: types: [published]`) → `.github/workflows/release.yaml` builds + uploads to PyPI via OIDC trusted publishing (no API tokens).
- **Changelog:** `CHANGELOG.md`, manually written, no "Unreleased" section (entries go straight under the new version heading at release time).
- **Source:** [github.com/python-poetry/poetry](https://github.com/python-poetry/poetry); [release.yaml](https://raw.githubusercontent.com/python-poetry/poetry/main/.github/workflows/release.yaml).

### 1.2 — pallets/flask

- **Repo shape:** single repo, default `main`.
- **Where dev happens:** trunk-based on `main`.
- **Dev internals:** contributing docs at `palletsprojects.com/contributing/` (Pallets-org-wide); `.devcontainer/` for env setup. No in-repo `docs/dev/`.
- **`docs/`:** end-user only.
- **Releases:** **tag push** (`on: push: tags: ['*']`) → `.github/workflows/publish.yaml`: builds → creates draft GitHub Release with artefacts → publishes to PyPI via OIDC.
- **Changelog:** `CHANGES.rst`, **manually written**, **uses an "Unreleased" section** (next-version heading + "Unreleased" until tag).
- **Source:** [github.com/pallets/flask](https://github.com/pallets/flask).

### 1.3 — tiangolo/fastapi

- **Repo shape:** single repo, default `master` (legacy).
- **Where dev happens:** `master` is the default; PRs from forks.
- **Dev internals:** `CONTRIBUTING.md` at root; substantial contributor scripts under `scripts/`; **no `docs/dev/`** — the project deliberately combines internal-author + end-user content in `docs_src/` and `docs/`. Translation contributors interact with the same tree.
- **`docs/`:** end-user multi-language (rendered to `fastapi.tiangolo.com`).
- **Releases:** **GitHub Release event** (`on: release: types: [created]`) → `publish.yml` runs `uv build` + `uv publish` to PyPI. **`latest-changes.yml`** is a bot workflow that opens PRs to update the in-repo release-notes doc as PRs merge — semi-automated changelog.
- **Source:** [github.com/tiangolo/fastapi](https://github.com/tiangolo/fastapi).

### 1.4 — psf/black

- **Repo shape:** single repo, default `main`.
- **Where dev happens:** trunk on `main`.
- **Dev internals:** `CONTRIBUTING.md` at root; full contributor docs at `black.readthedocs.io/en/latest/contributing/` rendered from `docs/contributing/` in-repo. **Dev internals are publicly published as part of the docs site.**
- **`docs/`:** mixed end-user + contributor (the `contributing/` subtree is in the same Sphinx build).
- **Releases:** standard tag-driven via Read-the-Docs config (`.readthedocs.yaml`) + PyPI workflow.
- **Changelog:** `CHANGES.md`, **manually written**, **has "Unreleased" section** with PR-author guidance comments inline ("PR authors: Please include the PR number in the changelog entry").
- **Source:** [github.com/psf/black](https://github.com/psf/black).

### 1.5 — astral-sh/ruff

- **Repo shape:** Cargo-based **monorepo** under `crates/` + Python bindings under `python/`, default `main`.
- **Where dev happens:** trunk on `main`; high-velocity small PRs.
- **Dev internals:** `CONTRIBUTING.md`, **`CLAUDE.md` at root** (Astral committed Claude-specific dev guidance into the public OSS repo — strong precedent for loam), `docs/` includes contributor sections.
- **`docs/`:** mixed end-user + dev (rendered to `docs.astral.sh/ruff/`).
- **Releases:** `release.yml` orchestrates via `cargo-dist`; `publish-pypi.yml` is invoked as a `workflow_call` subworkflow from the parent release flow. Releases ship platform binaries (`build-binaries.yml`), Docker images, WASM. Multi-artefact release pipeline, but all triggered by the same release.yml entry.
- **Changelog:** `CHANGES.md` at root.
- **Source:** [github.com/astral-sh/ruff](https://github.com/astral-sh/ruff); [.github/workflows/](https://github.com/astral-sh/ruff/tree/main/.github/workflows).

### 1.6 — pre-commit/pre-commit

- **Repo shape:** single repo, default `main`.
- **Where dev happens:** trunk.
- **Dev internals:** `CONTRIBUTING.md`. **No in-repo `docs/`** — docs at pre-commit.com are a separate site repo.
- **Releases:** standard PyPI publish via GitHub Actions on tag push.
- **Source:** [github.com/pre-commit/pre-commit](https://github.com/pre-commit/pre-commit).

### 1.7 — python-attrs/attrs

- **Repo shape:** single repo, default `main`.
- **Where dev happens:** trunk.
- **Dev internals:** `.github/CONTRIBUTING.md`. End-user docs at attrs.org built from in-repo `docs/`.
- **Releases:** tag-driven PyPI publish.
- **Source:** [github.com/python-attrs/attrs](https://github.com/python-attrs/attrs).

### 1.8 — kyegomez/swarms

- **Repo shape:** single repo, default `master`.
- **Where dev happens:** trunk on `master`.
- **Dev internals:** `CONTRIBUTING.md`, **`CLAUDE.md` at root**, `CODE_OF_CONDUCT.md`, `SECURITY.md`. Dev guides live inside `docs/` alongside end-user.
- **`docs/`:** mixed (rendered to `docs.swarms.world`).
- **Releases:** standard PyPI.
- **Source:** [github.com/kyegomez/swarms](https://github.com/kyegomez/swarms).

### 1.9 — langchain-ai/langchain

- **Repo shape:** **monorepo** under `libs/` (`core/`, `langchain/`, `langchain_v1/`, `partners/`, `standard-tests/`, `text-splitters/`), default `master`.
- **Where dev happens:** trunk on `master`; per-library publishes.
- **Dev internals:** contributing guide at `docs.langchain.com/oss/python/contributing/`; **no separate private repo**.
- **`docs/`:** docs hosted externally; minimal in-repo doc tree.
- **Releases:** per-package on PyPI; CI under `.github/workflows/`.
- **Source:** [github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain).

### 1.10 — simonw/llm

- **Repo shape:** single repo, default `main`.
- **Where dev happens:** trunk.
- **Dev internals:** `CONTRIBUTING.md` referenced; `Justfile` for dev tasks.
- **`docs/`:** end-user via Read-the-Docs (`.readthedocs.yaml`).
- **Releases:** standard PyPI.
- **Source:** [github.com/simonw/llm](https://github.com/simonw/llm).

### 1.11 — anthropics/claude-code (ecosystem comparator)

- **Repo shape:** single repo, default `main`.
- **Plugin layout:** `plugins/<name>/{agents,commands,skills,.claude-plugin,README.md}` — each plugin is a directory containing **only the runtime artefacts** users install.
- **Dev internals:** **no separate private repo for plugin development.** The published plugins (e.g. `plugin-dev`, `feature-dev`, `code-review`) are committed directly. Design rationale embedded in the `README.md` of each plugin, not in a separate `docs/dev/` tree.
- **Releases:** plugin marketplace install (`/plugin install <name>@claude-code-marketplace`); no PyPI involved.
- **Source:** [github.com/anthropics/claude-code/tree/main/plugins](https://github.com/anthropics/claude-code/tree/main/plugins).

### 1.12 — Carlos Santillana, "How to open source code from a private monorepo" (the one comparator that *is* like loam)

- **Setup:** company has private monorepo with proprietary code; needs to open-source specific packages tagged `openSource: true`.
- **Tooling:** `git-filter-repo` to rewrite history, `pnpm` workspace filtering to identify package dependency closure, custom Node scripts, GitHub Actions for automation.
- **Sync direction:** uni-directional (private → public).
- **Acknowledged costs:** "significant initial setup complexity," "cognitive overhead managing two repositories," "potential risks from history rewrites."
- **Stated outcome:** "We've not touched this pipeline since putting it in place" (i.e. amortised over years).
- **Why this case is different from loam:** the private monorepo contains proprietary code that *must* stay private (other paying products). loam has no such constraint — there is no "proprietary side" to protect. The synthesis is solving a problem loam doesn't have.
- **Source:** [dev.to/carlossantillana/how-to-open-source-code-from-a-private-monorepo-262o](https://dev.to/carlossantillana/how-to-open-source-code-from-a-private-monorepo-262o).

---

## Section 2 — Pattern analysis

### 2.1 — Dominant pattern (10/10 of the comparable projects)

```
single public repo
├── default branch: main (or master for legacy)
├── trunk-based development; PRs from feature branches or forks
├── dev internals visible in-repo:
│   ├── CONTRIBUTING.md at root
│   ├── CLAUDE.md (some — Astral, swarms)
│   ├── docs/ contains both end-user AND contributor docs
│   └── design notes / RFCs either in-repo or in GitHub Discussions
├── releases driven by either:
│   - tag push  → PyPI publish (Flask, attrs, llm, pre-commit)
│   - GitHub Release event → PyPI publish (Poetry, FastAPI, ruff via cargo-dist)
└── changelog manually authored, often with "Unreleased" section
```

### 2.2 — Variations and the conditions that justify them

| Variation | Conditions that justify it | Examples |
|---|---|---|
| Tag-push trigger vs. Release-event trigger | Personal preference; tag-push is slightly faster, Release-event allows draft + curated release notes | Flask (tag), Poetry/FastAPI (Release) |
| Monorepo of multiple packages | When packages share build infrastructure / version together (LangChain, ruff) | LangChain `libs/`, ruff `crates/` |
| OIDC trusted publishing | Security best practice; no PyPI tokens to manage | All modern projects (Poetry, Flask) |
| Bot-driven changelog (latest-changes.yml) | High PR volume, want automation-curated release notes | FastAPI |
| External docs site repo | Project wants doc site separately versioned | pre-commit |

### 2.3 — Variations that are NOT in any comparable project

- **Private dev repo + public release repo with a custom synthesis tool** that strips dev material at publish time. Carlos Santillana's pattern is the closest, and it explicitly serves a different need (protecting proprietary code that must NOT be published). This pattern does not appear in any of the 10 OSS comparators — including the closest peer (Anthropic's own claude-code plugin layout), which commits plugins directly with their dev material visible.
- **A partition manifest classifying every workspace path into publish-classes.** No comparator does this. The standard mechanism is `.gitignore` (for paths that never enter VCS) + `MANIFEST.in` / `pyproject.toml.tool.setuptools.packages.find` (for paths that don't enter the PyPI sdist).
- **Dual-ref push** (pushing the same SHA to two refs on the public remote). Standard projects have one default branch; the PyPI publish uses sdist/wheel, not branch material.

### 2.4 — Why standard practice converges on visible dev material

Synthesised from the corpus:

1. **Contributor attraction.** A would-be contributor who can read the project's design rationale, RFCs, and planning material in-repo is much more likely to file a meaningful PR than one who can only see the released code.
2. **Onboarding.** New maintainers (and sometimes new versions of yourself) recover context from in-repo dev material; hiding it costs context every onboarding cycle.
3. **No actual leak.** "Dev internals" are not secrets. Design rationale, planning state, half-finished thoughts, internal disagreements — none of these are confidential. Hiding them is a category error: confidentiality is for credentials, customer data, vulnerability research; design notes are pre-publication knowledge that becomes a contributor asset post-publication.
4. **Maintenance cost of synthesis.** Every variant of "two trees, sync between them" carries permanent overhead (commit-attribution mismatch, history-rewrite risk, branch-name divergence, content-drift between dev and published). Standard practice has decided this overhead exceeds the value of hiding pre-publication knowledge.

---

## Section 3 — Honest assessment of current loam architecture (F2)

Applying ruthless feedback. This section evaluates the loam dev architecture as currently implemented.

### 3.1 — Two-repo split (`lukeivers/ivers-corp` for dev + `lukeivers/loam` for published)

**Verdict: not justified. The premise is wrong.**

- The motivating premise ("hide dev internals from strangers") does not match standard OSS practice. None of the 10 surveyed projects hide dev internals; several actively publish them as a contributor asset (Black's `docs/contributing/`, ruff's `CLAUDE.md`, swarms's mixed docs).
- The repo names compound the problem: `lukeivers/ivers-corp` is a personal/company-named repo that does not describe the product. A stranger landing on `lukeivers/ivers-corp` cannot tell what it is. A stranger landing on `lukeivers/loam` (the published one) cannot find the source of truth for issues, contributions, or roadmap discussion.
- The two-repo shape forces every contributor (currently just Luke + agents) to remember which repo a given operation belongs to. This is the cognitive overhead the Santillana article warns about — and Santillana's case had a real reason for paying it (proprietary code). loam does not.
- **Empirical evidence of cost:** the FBE foldback ladder (FBE.6, .6b, .6c, .6d, .8, .9, .10, .11) — 8 sub-amendments, each closing a BLOCKER caused by the synthesis pipeline misbehaving (`framework-only` ref not present in stranger clones, `loam init` syntax mismatches between dev and published docs, etc.). Each BLOCKER would not exist in a single-repo architecture because there would be no synthesis at all.

### 3.2 — Synthesis tool (`framework/tools/pos-publish-framework-only/`)

**Verdict: solving an imaginary problem. Should be deprecated.**

- 1,431 LOC source + 2,468 LOC tests = 3,899 total. This is a substantial system to maintain.
- Its only function is to read canonical's `pos-v2` HEAD, apply the partition manifest, and emit a `framework-only` branch with `dev_only` and `excluded_from_publish` paths removed. **The substitution module (`substitution.py`, 202 LOC)** additionally performs string replacements (e.g. injecting version tokens) — which standard projects do via `setuptools_scm` / `setuptools-git-versioning` / `pyproject.toml` `dynamic = ["version"]`, not a custom synthesizer.
- Standard practice for "don't ship file X to PyPI": (a) put it in `.gitignore` so it never enters the repo, OR (b) put it in `MANIFEST.in` `exclude` so it doesn't enter the sdist, OR (c) put it under a top-level dir excluded by `[tool.setuptools.packages.find].exclude`. None of these require a custom tool.
- Standard practice for "don't show file X to GitHub strangers": you can't, and you shouldn't try. If it's in the repo, it's public.
- The synthesis tool's existence creates a permanent class of bugs (FBE6c.1: stranger-clone breakage from branch-name divergence; FBE9.1: bootstrap can't find `framework-only` as a local branch; FBE10: local-path mode of bootstrap). These bugs are the system fighting itself.

### 3.3 — Partition manifest (`publish-mode-manifest.yaml`)

**Verdict: deprecate as publish-gate. Possibly retain as directory convention.**

- As a publish gate (its current role): not justified — see §3.2.
- As a directory convention (a manifest documenting "this directory is dev-only, this one ships"): **possibly useful** as a `.gitignore`-shaped overlay for derived tools (e.g. `loam init` knows which directories to materialise in a stranger workspace). But this is a much smaller role: 30 lines of `.gitignore` syntax, not a 250+ line YAML schema with first-match-wins precedence + glob exclusions + audit-roots validation.
- A future workspace-bootstrap could use a simpler convention: paths matching `**/dev/**` or `docs/rebuild/plans/**` are dev-internal; paths under `framework/<component>/src/` are runtime; paths under `framework/<component>/tests/` are test material. No manifest file required.

### 3.4 — FBE foldback ladder cost

**Verdict: the engineering investment was not worth it given the underlying premise was wrong.**

Empirical counts from the canonical repo:

- **34 plan files** with FBE in the filename (`docs/rebuild/plans/*FBE*`).
- **104 commits** with `FBE.` in the commit message (across all branches).
- **153 commits** matching `oss-v0-1-0|oss-publish|publish-framework|fbe|partition` patterns in the past 5 days (out of 313 total commits in the same window) → **48.9% of all dev-cycle activity**.
- Every FBE.{6, 6b, 6c, 6d, 9, 10, 11} amendment closed a BLOCKER caused by the synthesis pipeline. None of those BLOCKERs would exist in the recommended single-repo architecture.
- The dispatch-cycle cost (research → plan → build → seal → narrative) for each FBE iteration was a full amendment cycle. Conservatively, each FBE iteration was 1–3 hours of AI-time + 5–15 minutes of Luke gate-review time. The 11+ FBE amendments alone represent 11–33 hours of AI-time and ~2 hours of Luke-time.

This is the tangible cost. The intangible cost is the context-noise: the foldback ladder dominated session attention for days, displacing higher-leverage work.

### 3.5 — `ivers-corp` repo name

**Verdict: indefensible for an OSS project.**

- The repo name does not match the product. A stranger asking "where do I file a loam issue?" lands on `lukeivers/loam` (the right product name) and finds it has no issues, no PRs, no discussions — because all of that activity is on `lukeivers/ivers-corp`, an unrelated-looking name.
- Standard OSS practice: the dev repo and the product have the same name. `pallets/flask`, `python-poetry/poetry`, `astral-sh/ruff`, `kyegomez/swarms`. The repo name is a contributor-attraction signal.
- Keeping `ivers-corp` as a private dev mirror would still be defensible if the synthesis pipeline justified it — but §3.2 says it doesn't. So the name has no defensible role.

### 3.6 — What was actually right about the current architecture

Steelman, applying critical-thinking-on-deviations:

- **The `workspace/` ↔ `framework/` split inside the canonical repo is actually a good idea.** It cleanly separates per-user runtime state (`workspace/`) from the framework source (`framework/`). This split should be **kept** in the recommended architecture; it just doesn't need to be the boundary between two different repos.
- **The `dev_only` partition class encoded a real intuition** — that some material is for builders and not for users. That intuition is correct. The mistake was implementing it as a publish-time gate rather than as a directory convention + `.gitignore`. The intuition can survive without the synthesis pipeline.
- **The substitution module's version-injection role is a real need** — a published artefact needs a version. The standard solution is `setuptools_scm` (auto-derive version from `git describe`); the bespoke synthesis-time substitution can be replaced with that.
- **Workflow discipline (sealed amendments, plans before code, ODD)** is independent of the publish architecture. None of the recommended changes require touching the amendment process.

---

## Section 4 — Recommended target architecture

### 4.1 — One-line summary

**Single public GitHub repo `lukeivers/loam`. Trunk-based development on `main`. Releases via tag push to PyPI with OIDC trusted publishing. Dev internals live in-repo. Synthesis tool deprecated.**

### 4.2 — Specific answers to the dispatch's six questions

| Question | Answer |
|---|---|
| One repo or two? | **One.** `lukeivers/loam` (the published name). |
| Where does dev happen? | **`main` branch of `lukeivers/loam`.** Trunk-based; PRs from feature branches if/when external contributors arrive. |
| How are releases made? | **Tag push** (`git tag v0.1.0 && git push origin v0.1.0`) → GitHub Actions workflow `.github/workflows/publish.yml` → PyPI publish via OIDC. Optionally also create a GitHub Release with notes pulled from `CHANGELOG.md`'s "Unreleased" section. |
| Where do dev internals live? | **In-repo, visible.** `docs/rebuild/plans/` stays where it is. `CLAUDE.md` + `CLAUDE.dev.md` stay at root (Astral/swarms precedent). `CONTRIBUTING.md` describes the contribution flow. The amendment-narrative commit messages stay (they are valuable and not embarrassing). |
| What about the synthesis tool? | **Deprecate.** Remove `framework/tools/pos-publish-framework-only/` from active code; archive its source under `docs/rebuild/archive/synthesis-tool-2026-05-04/` for historical context. Replace its version-substitution role with `setuptools_scm`. |
| What about the partition manifest? | **Demote.** Remove its publish-gate role. Either (a) delete it entirely and use `.gitignore` + `MANIFEST.in` for the small set of paths that genuinely shouldn't ship, or (b) keep a much smaller directory-convention manifest used by `loam init` to decide what to materialise in a stranger workspace. **Recommendation: (a) for simplicity; (b) only if `loam init`'s materialisation logic genuinely needs a manifest.** |
| How does Luke's local workspace interact? | **Same as today minus the `framework-only` branch.** Luke's local clone of `lukeivers/loam` *is* the dev workspace. The `workspace/` subtree (per-user runtime state) is `.gitignore`'d at the appropriate level so Luke's `workspace/` data doesn't pollute the public repo's content. PRs and tags go to `lukeivers/loam` directly. |

### 4.3 — Repo layout post-migration

```
lukeivers/loam   (public, default branch: main)
├── README.md                    # user-facing, install + getting started
├── CLAUDE.md                    # always-on agent instructions
├── CLAUDE.dev.md                # dev-mode-only agent instructions (auto-loaded in dev workspaces)
├── CONTRIBUTING.md              # how to contribute
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── LICENSE
├── CHANGELOG.md                 # manual, with "Unreleased" section
├── pyproject.toml               # build + setuptools_scm version + entry points
├── install-from-source.txt
├── .gitignore                   # ignore workspace/, .scratch/, *.log, etc.
├── docs/                        # end-user + contributor (mixed, like Black)
│   ├── getting-started.md
│   ├── install-from-source.md
│   ├── concepts/
│   ├── reference/
│   └── rebuild/                 # dev-internal planning + RFCs (visible)
│       ├── plans/
│       ├── components/
│       ├── spec/
│       └── VALUE_PROPOSITION.md
├── framework/                   # product source (unchanged shape)
│   ├── primary-persona/
│   ├── workspace-bootstrap/
│   ├── memory-system/
│   ├── ...
│   └── tools/                   # dev-tooling (loam-amend, etc.) — STILL ships, like ruff's tooling
├── plugins/
│   └── dev-sdlc/                # the dev-sdlc plugin
├── tests/                       # repo-wide cross-component tests
├── .github/
│   └── workflows/
│       ├── tests.yml            # on every PR + push
│       ├── publish.yml          # on tag push: build + PyPI via OIDC
│       └── docs.yml             # on push to main: build docs (if applicable)
└── workspace/                   # GITIGNORED — Luke's per-user runtime state
```

Key points:

1. `framework/` keeps its current shape. The renaming pivot (`pos-publish-framework-only` → `loam.publish_framework_only`) was already done; we just delete that tool entirely now.
2. `workspace/` becomes gitignored. The current `workspace/` content (Luke's data, sync state, scratch outputs) does not enter the public repo. This replaces the partition manifest's `excluded_from_publish` class.
3. `docs/rebuild/` (plans, components, spec, VALUE_PROPOSITION) is **visible**. This is the single biggest mental shift. Standard OSS practice says: this material attracts contributors. The amendment-narrative commit messages, plan files, and design rationale are exactly what contributors need to onboard.
4. `framework/tools/` keeps its existing dev-tools (the loam-amend tool, etc.) — these ship publicly because they're how anyone (Luke or future contributors) builds loam. ruff ships its dev tooling; so does Poetry. The synthesis tool is the one tool we're deleting.

### 4.4 — Versioning + release mechanics

- **Version source:** `setuptools_scm` reads `git describe --tags` and derives the package version. No version-file substitution needed.
- **Release flow:**
  1. Author CHANGELOG entry under `## Unreleased`.
  2. Decide version (semver: `v0.1.1`, `v0.2.0`, `v1.0.0`).
  3. Move "Unreleased" entries under the new version heading + date.
  4. Commit + push.
  5. `git tag v0.X.Y && git push origin v0.X.Y`.
  6. GitHub Actions `publish.yml` triggers; builds sdist + wheel; publishes to PyPI via OIDC.
  7. Optionally: create GitHub Release with auto-populated body from CHANGELOG.
- **Pre-releases:** standard PEP 440 `0.2.0a1`, `0.2.0rc1` — published to PyPI as pre-releases (visible only with `pip install --pre`).

### 4.5 — How the recommendation answers Lens 1–5

- **Lens 1 (Claude-leverage-first):** the recommendation reduces the amount of bespoke loam plumbing, leaving more bandwidth for Claude-native composition (skills, plugins, hooks). Specifically: removing the synthesis pipeline frees the `framework/tools/` slot for tools that *do* compose with Claude primitives.
- **Lens 2 (harness + persona value):** removing the partition-manifest cognitive load is a translation-burden reduction for the primary persona; every dispatch currently needs to know which partition class new files belong to.
- **Lens 3 (ODD authoring):** the migration plan in §5 is itself ODD-shaped — objective + ACs + reversibility, no method prescription beyond what's necessary.
- **Lens 4 (scope ↔ confidence):** confidence in this recommendation is **moderate-high** — the survey is unambiguous, but the exact migration order has tradeoffs Luke should rule on (§7). Scope-of-recommendation is therefore tight at the architecture level + loose at the migration-step level.
- **Lens 5 (swarming):** §5 is decomposable — research is done, plan is here, the build steps are independent and can be parallelised by an agent swarm if Luke wants to move fast.

---

## Section 5 — Migration plan

### 5.1 — Order of operations

Six phases. Each phase is reversible until phase 6.

| Phase | Operation | AI-time | Luke-time | Reversibility |
|---|---|---|---|---|
| **1** | Create `lukeivers/loam` GitHub repo (public or private-then-public). Push canonical `pos-v2` HEAD as `main`. | 5 min | 5 min (create repo) | Fully reversible (delete repo) |
| **2** | Add `.github/workflows/publish.yml` (OIDC PyPI publish on tag push) + `.github/workflows/tests.yml`. Configure PyPI trusted-publisher for the new repo. Tag `v0.1.0` to validate end-to-end. | 30–60 min | 10 min (PyPI trusted-publisher config) | Reversible (delete tag, yank PyPI release) |
| **3** | `.gitignore` `workspace/`, `*.log`, `.scratch/`, `data/memory-system/`, etc. Verify a stranger clone produces a tree without per-user state. | 15–30 min | 0 | Fully reversible (revert .gitignore commit) |
| **4** | Delete `framework/tools/pos-publish-framework-only/`. Replace any version-substitution callsites with `setuptools_scm`. Remove `publish-mode-manifest.yaml` (or move to `docs/rebuild/archive/`). Update `framework-only` branch tracking — drop the branch from all remotes. | 30–90 min | 5 min (decide whether to archive vs. delete the synthesis tool source) | Reversible until phase 6 |
| **5** | Update `README.md`, `CONTRIBUTING.md`, `docs/getting-started.md`, `docs/install-from-source.md` to reference `lukeivers/loam` (not `lukeivers/ivers-corp`, not the dual-ref push, not `framework-only`). Update CLAUDE.dev.md amendment workflow if it references the synthesis tool. | 60–120 min | 5 min (review) | Reversible (revert doc commits) |
| **6** | Archive `lukeivers/ivers-corp` on GitHub (read-only, with a top-level note pointing at `lukeivers/loam`). | 5 min | 5 min (archive action) | **Reversible** (GitHub allows un-archive) but socially sticky. |

**Total: ~3–5 hours AI-time + ~30 minutes Luke-time + ~30 minutes Luke gate-review across phases.**

### 5.2 — Risks per phase + mitigations

| Phase | Risk | Mitigation |
|---|---|---|
| 1 | New repo loses commit history if pushed wrong | Push the full canonical `pos-v2` history (`git push lukeivers/loam pos-v2:main`) — preserves all SHAs |
| 1 | Public repo accidentally exposes secrets in history | Pre-flight: `git log --all -p` scan + `git secrets`/`gitleaks` on canonical history before phase 1; halt if any hits |
| 2 | PyPI trusted-publisher misconfigured → publish fails | Use `lukeivers/loam-staging` (already exists per FBE.6d) as a dry-run target first |
| 3 | `.gitignore` either too aggressive (drops needed runtime files) or too loose (leaks per-user state) | Iterate via `git status` after `.gitignore` edit; the partition manifest's `excluded_from_publish` list is the answer key |
| 4 | Removing synthesis tool breaks an in-flight dispatch that depends on it | Pre-flight: `grep -r 'pos-publish-framework-only\|publish_framework_only\|framework-only' framework/ docs/rebuild/plans/` and audit. The amendment workflow does not depend on this tool — only the (deprecated) M11/M12 publish path does. |
| 5 | Doc drift creates a window where docs reference both old and new repo | Do all doc updates in one commit; review as a single PR-equivalent before pushing |
| 6 | Existing GitHub issue/PR references in commits become stale | Acceptable; archived repo's links still resolve. Optionally add a `404.md` / repo description pointer. |

### 5.3 — Reversibility map

- **Phases 1–5 are reversible to a clean revert.** Each phase commits self-contained changes; `git revert` undoes them.
- **Phase 6 is reversible** in GitHub's UI (unarchive), but the social signal is sticky — once strangers see the archive notice, they may have linked to it from elsewhere.
- **The non-reversible event** is publishing to PyPI. **PyPI does not allow re-using a yanked version number.** This means: do phase 2's tag-validation against a pre-release version (`v0.0.1rc1` or similar) so the canonical `v0.1.0` slot stays available.

### 5.4 — What gets deprecated / deleted / archived

| Artefact | Action | Rationale |
|---|---|---|
| `framework/tools/pos-publish-framework-only/` (source + tests) | **Delete from `main`**, archive copy to `docs/rebuild/archive/synthesis-tool-2026-05-04/` | Solving an imaginary problem (§3.2) |
| `publish-mode-manifest.yaml` | **Delete** (or archive alongside the tool) | No publish gate remains |
| `framework-only` local + remote branch | **Delete** | No synthesis output to push |
| Dual-ref push step list (in `oss-v0-1-0-publish-dry-run.md` etc.) | **Mark deprecated** in plan files (do not delete plan history — it's part of the audit trail) | Operator instruction obsoleted |
| `lukeivers/ivers-corp` GitHub repo | **Archive** with redirect notice | Wrong name, replaced by `lukeivers/loam` |
| `loam-publish-framework-only` PyPI package (if ever published) | **Yank** if published; never publish if not | Tool deprecated |

### 5.5 — What gets kept / renamed / restructured

| Artefact | Action |
|---|---|
| `framework/<component>/` source trees | **Kept verbatim** |
| `docs/rebuild/plans/`, `docs/rebuild/components/`, `docs/rebuild/spec/`, `VALUE_PROPOSITION.md` | **Kept verbatim** in new repo |
| `CLAUDE.md`, `CLAUDE.dev.md` | **Kept verbatim** (`CLAUDE.dev.md` references will need a small update — drop synthesis-tool mentions) |
| Sealed-amendment commit history | **Preserved via push of full history** (phase 1) |
| `loam-amend` tool | **Kept** — internal dev tool, ships with the repo (Poetry/ruff precedent) |
| `workspace/` | **Gitignored** in the new repo; Luke's local content stays local |
| Plugin layout (`plugins/dev-sdlc/`) | **Kept verbatim** |

### 5.6 — Specific Luke-decisions required (escalations) — full list in §7

(See Section 7 below; 5 items.)

### 5.7 — Specific public-class actions required

These are the operations that touch outside-the-repo state — Luke's GitHub account, PyPI, or external links:

1. **Create `lukeivers/loam` GitHub repo** (visibility: private at first, public later, OR public from day one — Luke decision §7.1).
2. **Configure PyPI trusted-publisher** for `lukeivers/loam` to allow OIDC publish from GitHub Actions.
3. **Push canonical history** to `lukeivers/loam:main`.
4. **Tag `v0.0.1rc1`** as a publish-flow validation, then `v0.1.0` as the real first release.
5. **Archive `lukeivers/ivers-corp`** with redirect notice.
6. **Update any external links** Luke has shared (Telegram messages, FUTURE_IDEAS_DRAFT references) — low-priority, can be deferred.

---

## Section 6 — Honest doubts + F2 RF on this recommendation

Where I might be wrong:

### 6.1 — The "private dev repo first, then make public" intermediate

If Luke's actual concern is "I'm not ready for strangers to see the dev material yet" — i.e. a *temporal* hiding rather than a permanent one — then keeping the repo private during the v0.1.x → v0.4.x development period is a valid intermediate. None of the surveyed projects did this *and stayed private*; some (FastAPI early on, attrs early on) had short private periods before going public. **This doesn't change the recommended architecture** (still single repo, still trunk-based, still tag-driven); it changes only the public/private toggle on `lukeivers/loam`. This is the simplest steelman of the current architecture.

### 6.2 — The `excluded_from_publish` class is real

The partition manifest's `excluded_from_publish` class genuinely covers paths that must not ship: host-specific paths (`/Users/lukeivers/...` in some files), credential-adjacent material, runtime state files. **This is real.** The recommendation handles it via `.gitignore` + a one-time history scan. The doubt: if the canonical `pos-v2` history *already contains* secrets that were committed and never removed (even if they're now `.gitignore`'d), `git push canonical:main` will leak them. **Phase 1 mitigation (history scan) is mandatory** and might surface "we cannot push the full history" as a finding — in which case we'd need `git filter-repo` to clean history before push, which adds AI-time and risk.

### 6.3 — The dev-mode auto-load partition

CLAUDE.dev.md is auto-loaded in dev workspaces but not in normal-use workspaces. This works today via the partition manifest's `dev_only` class on `CLAUDE.dev.md` — strangers don't see CLAUDE.dev.md content because it's stripped. **In the recommended architecture, CLAUDE.dev.md is in the public repo.** Strangers see it. Does this break the dev-mode partition?

Answer: no. The "auto-load in dev workspaces only" is enforced by `loam init`'s workspace bootstrapper, not by file presence. A stranger's `loam init` produces a normal-use workspace; CLAUDE.dev.md is in the source repo but not symlinked into the stranger's workspace. The file's *visibility* in the public repo is fine; what matters is whether `loam init` materialises it. So this concern dissolves on inspection — but it's worth verifying in phase 5.

### 6.4 — The amendment-narrative commit messages contain personal commentary

Some commit messages in the canonical history are quite verbose and personal in tone (citing FBE BLOCKERs, methodology debates, internal disagreements). Strangers reading the commit log would see these. **Is this embarrassing?** Steelman of "yes": some messages are mid-process thinking, not polished. Counter: ruff's history is similar; Poetry's is similar; Black's is similar. Verbose, opinionated commit messages are an OSS norm. The amendment narrative is a feature, not a bug.

### 6.5 — The synthesis tool is being deprecated mid-flight (M12 publish-flip is the gating step)

Per the FBE.6d seal narrative, "M12 publish-flip is the next dispatch." That dispatch is the one that would have flipped `lukeivers/loam:main` to track `framework-only` content via the synthesis tool. **If we adopt this recommendation, M12 is cancelled.** Luke should explicitly rule on whether the FBE foldback ladder is closed (yes — by deprecating the destination), or whether some FBE finding was independently valuable and worth retaining in some other form. My read: the FBE findings were entirely about the synthesis pipeline's edge cases; with the pipeline gone, the findings are obsolete. But Luke owns the call.

### 6.6 — What the recommendation might be wrong about

- **If loam ever needs a closed-source commercial offering** (a paid harness with proprietary plugins) and an open-source core, the Santillana pattern becomes relevant. Today this is not the case; in the future it might be. **Insurance:** the recommendation does not preclude reintroducing a synthesis pipeline later if a real proprietary-vs-public split emerges. The synthesis tool's source can be archived for re-use.
- **If a contributor objects to the visibility of half-finished plan files** (e.g. "I PRed something that contradicts a plan in `docs/rebuild/plans/` that I didn't know existed"), there's a small UX cost. **Mitigation:** `CONTRIBUTING.md` explicitly says "plans in `docs/rebuild/plans/` reflect the maintainer's current thinking; if you disagree, file an issue."

---

## Section 7 — Open items for Luke (escalations)

Tight list. Five public-class / architectural decisions only.

### 7.1 — Public repo from day one, or private-then-public?

- **Option A (public day one):** maximum standard-practice fit. Strangers can find, fork, contribute immediately.
- **Option B (private through some milestone, then public):** lower social pressure during the "this is messy" phase. Default GitHub setting is private; can flip to public later. **No code change required to flip.**
- **Recommendation:** **B** — start private through v0.4.x or whatever Luke's "ready for strangers" threshold is, then flip. Gives all the architectural benefits without the social cost of strangers landing on a half-built thing.

### 7.2 — Repo name: `lukeivers/loam` or `loam-org/loam` (new GitHub org)?

- **Option A:** `lukeivers/loam` — uses Luke's personal account, matches current `lukeivers/loam` published repo.
- **Option B:** create a new GitHub org (`loam-dev`, `loam-org`, `getloam`, etc.) for `loam-org/loam` — gives the project an org-level identity, cleaner for future contributor-promotion + ownership transfer.
- **Recommendation:** **A** for v0.1.x–v0.4.x; consider B at v1.0.0 or first external maintainer. Org-creation now is premature.

### 7.3 — Delete the synthesis tool source, or archive it?

- **Option A (delete):** `git rm framework/tools/pos-publish-framework-only/`. Source recoverable from git history.
- **Option B (archive):** move to `docs/rebuild/archive/synthesis-tool-2026-05-04/` for future-Luke discoverability.
- **Recommendation:** **B** with a `README.md` in the archive dir noting "deprecated 2026-05-04 per `oss-dev-architecture-survey-and-migration-2026-05-04.md`." 1 hour of marginal cost; high context-recovery value if a future need arises.

### 7.4 — Migrate via clean push or via history rewrite (`git filter-repo`)?

- **Option A (clean push of full history):** preserves all SHAs, all amendment narrative, all FBE foldback artefacts. Risk: any historic secret in the history leaks.
- **Option B (filter-repo to clean specific paths/blobs from history before push):** cleaner public-facing history, but breaks SHA references in plan files / commit messages / the audit trail. High effort.
- **Recommendation:** **A**, **gated on** a pre-flight `gitleaks` / `truffleHog` scan. If scan is clean, push as-is. If scan flags anything, halt + decide per-finding.

### 7.5 — Cancel the FBE foldback / M12 publish-flip dispatch entirely?

The FBE.6d seal narrative says "M12 publish-flip is the next dispatch." If we adopt this recommendation, M12 is replaced by phase 1–6 of the migration plan above.

- **Option A:** cancel M12 explicitly; mark FBE foldback as "superseded by oss-dev-architecture-survey-and-migration-2026-05-04.md" in the foldback parent register.
- **Option B:** complete M12 first (as defensive insurance — get one working publish via the old pipeline), then migrate.
- **Recommendation:** **A**. Completing M12 first costs 1–3 hours of AI-time on a system being deprecated. The migration plan in §5 phase 2 *is* the equivalent of M12 in the new architecture — there is no insurance gap.

---

## Sources

OSS reference projects (verified 2026-05-04):

- [github.com/python-poetry/poetry](https://github.com/python-poetry/poetry) and [release.yaml](https://raw.githubusercontent.com/python-poetry/poetry/main/.github/workflows/release.yaml)
- [github.com/pallets/flask](https://github.com/pallets/flask) and [CHANGES.rst](https://raw.githubusercontent.com/pallets/flask/main/CHANGES.rst)
- [github.com/tiangolo/fastapi](https://github.com/tiangolo/fastapi)
- [github.com/psf/black](https://github.com/psf/black) and [CHANGES.md](https://raw.githubusercontent.com/psf/black/main/CHANGES.md)
- [github.com/astral-sh/ruff](https://github.com/astral-sh/ruff)
- [github.com/pre-commit/pre-commit](https://github.com/pre-commit/pre-commit)
- [github.com/python-attrs/attrs](https://github.com/python-attrs/attrs)
- [github.com/kyegomez/swarms](https://github.com/kyegomez/swarms)
- [github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain)
- [github.com/simonw/llm](https://github.com/simonw/llm)
- [github.com/anthropics/claude-code/tree/main/plugins](https://github.com/anthropics/claude-code/tree/main/plugins)

Comparator article:

- [Carlos Santillana, "How to open source code from a private monorepo," dev.to](https://dev.to/carlossantillana/how-to-open-source-code-from-a-private-monorepo-262o)

Standards material:

- [Trunk-Based Development](https://trunkbaseddevelopment.com/)
- [Atlassian — Trunk-based Development](https://www.atlassian.com/continuous-delivery/continuous-integration/trunk-based-development)
- [PyPA — Publishing package distribution releases using GitHub Actions CI/CD workflows](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

Internal cost evidence:

- 153 / 313 commits in 2026-04-30 → 2026-05-04 window matched OSS-publish/FBE patterns (`git log --oneline --since=2026-04-30 --until=2026-05-04 | grep -iE 'oss-v0-1-0|oss-publish|publish-framework|fbe|partition' | wc -l`).
- 34 plan files with `FBE` in filename under `docs/rebuild/plans/`.
- Synthesis tool: 1,431 LOC source + 2,468 LOC tests in `framework/tools/pos-publish-framework-only/`.
