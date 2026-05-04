# v0.1.3 item 1 sub-plan — SKILL.md packages bundle

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-04.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-x-roadmap.md` (§2 v0.1.3 item 1 + §5 Decision D + §8 method-decision register).
**Predecessors:** v0.1.2 close-out — V11.A `9d58062`; V11.E `7d19a7e`; ack-first `32ff67d`; loam-amend ergonomics `2c32c1b`. v0.1.3 R.5 design note 1 sealed at `7ae346d`. Roadmap §2 relabel landed at `ce58521`.
**BASELINE (pre-build tip):** `ce58521` — current canonical pos-v2 HEAD.
**Status-file target:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-3-skill-packages-status-2026-05-04.md`.

---

## 1. Summary / TL;DR

v0.1.3 item 1 lands 5 SKILL.md packages as a new plugin component `plugins/loam-skills/`. Each package captures one of loam's load-bearing translation patterns and is independently usable from raw Claude Code (no full-harness install required). Per Roadmap §5 Decision D: ship 5; drop to 3 if AI-time overruns.

**The 5 packages (final set, per dispatcher's suggested set with the naming retained):**

1. **`memory-recall`** — file-based memory retrieval pattern; degrades gracefully when no loam workspace is present.
2. **`scope-decompose`** — codifies F3 swarming stopping criterion; "is this actually decomposable?" check before single-agent loop.
3. **`dispatch-with-gates`** — codifies scope-only dispatch + halt-and-surface; never enumerate files/symbols/ACs in dispatch prompts.
4. **`onboarding-conversation`** — codifies primary-persona greeting / context-restoration shape for fresh sessions.
5. **`session-handoff`** — codifies durable-capture rule (FIDRAFT-like surfaces) before session close.

Sealed-component fence: **single new component — `plugins/loam-skills/`** (the new plugin's own seal-test fences `plugins/loam-skills/skills/<name>/SKILL.md` along with the rest of the plugin). Plus `docs/rebuild/plans/` via universal-prefix admission for sub-plan-doc + manifest.

---

## 2. Placement decision

**Decision:** ship as `plugins/loam-skills/` (NEW plugin component). Mirrors `plugins/dev-sdlc/` precedent.

**Rationale:**

- **Lens 1.** SKILL.md is a Claude-native primitive (per `https://code.claude.com/docs/en/skills`). Loam contributes via the primitive — composes on top, doesn't re-implement. Plugin shape is purest Lens-1 expression: an external user with raw Claude Code can `pip install -e ./plugins/loam-skills` and gain loam's translation patterns without committing to the full harness.
- **Lens 2 — harness toolkit.** Each SKILL.md adds to the toolkit the primary persona can draw from. Ships as a plugin so the persona can use the same `disable-model-invocation: false` discovery surface that Claude Code provides natively.
- **Plugin shape mirrors `plugins/dev-sdlc/`.** The plugin protocol established at v0.1.0 M6a (entry-point group `loam.bootstrap.contributions`) is reused. Independent versionability — a Claude Code SKILL schema change bumps the plugin's version, not the framework.
- **Why NOT `framework/loam-skills/`.** Framework components are runtime-load-bearing for loam's harness. SKILL packages are user-facing additions that compose with raw Claude Code. They're not in the workspace-bootstrap composer's contribution graph.
- **Why NOT alongside `plugins/dev-sdlc/skills/start-project.md` (existing flat skill).** The flat-file shape pre-dates the modern Anthropic SKILL.md schema (skills/<name>/SKILL.md with optional supporting-files siblings). New packages adopt the modern shape; the existing flat skill stays as v0.1.0 surface (untouched — out of fence). A v0.2+ amendment can migrate the flat skill into the new shape if desired.

**Component layout:**

```
plugins/loam-skills/
├── pyproject.toml             # editable-installable package metadata
├── README.md                  # stranger-facing overview + install snippet
├── dev-mode-manifest.yaml     # NOT authored at this amendment (out-of-fence;
│                              # plugins/dev-sdlc/dev-mode-manifest.yaml owns
│                              # partition-membership; no edits there from this
│                              # dispatch — plugins/ tree falls outside roots:
│                              # by default, same as plugins/dev-sdlc/)
├── skills/
│   ├── memory-recall/SKILL.md
│   ├── scope-decompose/SKILL.md
│   ├── dispatch-with-gates/SKILL.md
│   ├── onboarding-conversation/SKILL.md
│   └── session-handoff/SKILL.md
└── tests/
    ├── SEAL_COMMIT             # sidecar (initial; bumped at apply step)
    ├── SEAL_COMMIT.notes       # narrative (authored at seal step)
    ├── test_AC_LSK_1_skill_packages_present.py
    ├── test_AC_LSK_2_frontmatter_well_formed.py
    ├── test_AC_LSK_3_body_content_shape.py
    └── test_no_sealed_amendments.py
```

**Plugin minimal `pyproject.toml`:** name `loam-plugin-loam-skills`, version `0.1.0`, `requires-python = ">=3.13"`. No runtime dependencies (the plugin ships static markdown — no Python code is invoked). Dev-only test dep `pytest>=8.0`. Single-package include via `setuptools.package-data` for the markdown files. NOT contributed via `loam.bootstrap.contributions` entry-point — these skills are discovered by Claude Code natively (filesystem walk over `plugins/<plugin>/skills/<name>/SKILL.md`) per Anthropic SKILL docs. No bootstrap-time wiring required.

---

## 3. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; SKILL.md schema selection)

Anthropic's published schema (`https://code.claude.com/docs/en/skills` fetched 2026-05-04) names two skill-content types: **reference content** (knowledge applied alongside conversation) and **task content** (step-by-step actions, often `disable-model-invocation: true`). All 5 packages are **reference content** style — they teach the persona a pattern to apply, not a step-by-step action. None set `disable-model-invocation`. The dispatcher's lean is correct: these are skills the persona triggers based on description match.

**Decision (autonomous):** all 5 SKILL.md frontmatters set `description` only (Anthropic's "recommended" minimum). `name` defaults to directory name per the schema. No `disable-model-invocation`, no `allowed-tools`, no `argument-hint` — these are reference-content skills, not task skills with side-effects.

### Surface #2 (no halt — recorded; skill-name format)

Anthropic schema: lowercase letters, numbers, and hyphens only; max 64 chars. All 5 chosen names are kebab-case + within the limit. No collisions with bundled skills (`/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api`) or the existing `start-project` / `memory-search` / `memory-archive` flat skills.

### Surface #3 (no halt — recorded; existing flat skills untouched)

`plugins/dev-sdlc/skills/start-project.md` (flat file) and `framework/primary-persona/skills/{memory-search,memory-archive}.md` (flat files) are pre-modern-schema shape — they pre-date the directory-per-skill convention. **Decision (autonomous):** leave them untouched. They're outside this amendment's fence; a v0.2+ migration can convert them to the modern shape if Anthropic's SKILL discovery starts requiring the directory-per-skill form. The existing flat-file skill discovery code paths in primary-persona's prompt template continue working.

### Surface #4 (no halt — recorded; no entry-point wiring)

Skills are discovered by Claude Code via filesystem walk (`<plugin>/skills/<skill-name>/SKILL.md` per the schema's "where skills live" table). No `loam.bootstrap.contributions` entry-point, no Python init, no module export. The `pyproject.toml` exists solely to make `pip install -e ./plugins/loam-skills` work as a recognised editable package (so it shows up in `pip list` and the install-from-source flow can include it). The package contributes nothing to the loam harness's runtime graph — only static markdown that Claude Code reads.

### Surface #5 (no halt — recorded; install-from-source.txt update IS in-fence)

The install-from-source.txt file at the repo root is a **universal-admission-prefix path** (sits in `docs/rebuild/plans/`'s sibling top-level zone). However, it's at the literal repo root — not under `docs/rebuild/plans/`. The path sits outside the partition's `roots:` declaration AND outside `plugins/loam-skills/`. **Decision:** the manifest declares an `extra_allowed_files` admission for `install-from-source.txt` so the new "Tier K — Loam Skills plugin" line can land alongside the new component. `docs/install-from-source.md` mirrors the same line; same admission shape.

### Surface #6 (no halt — recorded; smoke-verification approach)

Anthropic's "skill discovery" mechanism in Claude Code is the live `claude` binary's session walk over `<workspace>/.claude/skills/` + `<plugin>/skills/`. **Decision (autonomous):** the smoke verification is **NOT** an end-to-end Claude Code session probe (would require booting the binary in a test fixture; out-of-scope for amendment-cycle smoke). Instead: a static-shape probe — for each of the 5 packages, the test reads `SKILL.md`, parses YAML frontmatter, asserts `description` field is non-empty + ≤1536 chars (the schema's combined-cap), asserts directory name is kebab-case + ≤64 chars, asserts body has at least one `## ` section, asserts SKILL.md is valid markdown (no broken frontmatter delimiters). This matches the pattern in the existing `test_AC_OSS_M6_9_start_project_skill_shipped.py`.

### Surface #7 (no halt — recorded; loam amend apply auto-commit lands as commit subject `chore(amend): v0-1-3-skill-packages apply ...`)

Per v0.1.2 item 6 (`2c32c1b`), `loam amend apply` now auto-commits. This amendment is the FIRST v0.1.3 amendment to use the auto-commit feature for real. No special handling — the apply step lands its commit deterministically. Status file records the auto-commit SHA distinctly from the manual commits.

---

## 4. Spec-objective placement

**Binds to:**

- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — translation-burden reduction for the primary persona's pattern application. Each SKILL.md captures a translation pattern that's currently re-derived in-prompt every time it's needed.
- **v0.1.x roadmap §2 v0.1.3 item 1** — 3-5 SKILL.md packages per Decision D (ship 5; drop to 3 if AI-time overruns).
- **AC.LSK.* per this sub-plan §5** — every AC ladders to the same parent.
- **Composes with:** R.5 design note 1 (`primary-persona-shape.md`) — the SKILL packages externalize patterns that the design note defends. The two reinforce: design note explains WHY the persona has this shape; SKILL packages let strangers benefit from the patterns without buying into the full shape.
- **Composes with:** v0.1.5 D-1 (progressive-disclosure) — `memory-recall` skill's body references the eventual L1/L2/L3 surface; today's text describes the file-based store directly.
- **Composes with:** v0.1.4 V2.B (subagent personas) — the personas will inherit fluency in the same patterns the SKILL packages capture; redundancy is intentional (skills are user-facing, personas are dispatch-internal).

**Ladders to:** AC.LSK.* → v0.1.3 item 1 (largest closing item alongside V11.C ODD-RE) → v0.1.4 + onward (every future SKILL package inherits this plugin's shape) → AC.PO.1 + AC.PO.2.

---

## 5. Acceptance criteria (LSK.*)

**AC family:** `AC.LSK.*` (Loam Skills). Pre-grep verified zero collisions in framework/, plugins/, tests/, docs/.

### AC.LSK.1 — five SKILL.md packages present and well-formed

Five SKILL.md files exist at the canonical paths:

```
plugins/loam-skills/skills/memory-recall/SKILL.md
plugins/loam-skills/skills/scope-decompose/SKILL.md
plugins/loam-skills/skills/dispatch-with-gates/SKILL.md
plugins/loam-skills/skills/onboarding-conversation/SKILL.md
plugins/loam-skills/skills/session-handoff/SKILL.md
```

Each file:
1. Starts with valid YAML frontmatter delimited by `---` lines.
2. Frontmatter parses without error and is a mapping.
3. Carries a non-empty `description` field (string, ≤1536 chars per Anthropic's combined-cap).
4. Body (post-frontmatter) is non-empty markdown.

**Verified by:** `tests/test_AC_LSK_1_skill_packages_present.py` (5 paths × shape assertions).

### AC.LSK.2 — frontmatter follows Anthropic SKILL.md schema

For each of the 5 packages:
1. The skill's directory name is the canonical name (kebab-case; lowercase letters/numbers/hyphens only; ≤64 chars).
2. If `name` field is present in frontmatter, it matches the directory name.
3. `description` field is present and informs Claude when to apply the skill (contains a "use when" or trigger-phrase clause).
4. No unknown frontmatter fields (the only fields used in v0.1.3 are `name` (optional) and `description` — keeps surface minimal).

**Verified by:** `tests/test_AC_LSK_2_frontmatter_well_formed.py` (5 packages × frontmatter assertions).

### AC.LSK.3 — body content shape

For each of the 5 packages, the markdown body:
1. Has at least one `## ` header section.
2. Carries a "When to use" or equivalent description-mirror that names the trigger.
3. Names the underlying loam pattern that the skill captures (the body must reference loam's CLAUDE.md, F3, ODD, M-FBM, FIDRAFT, or equivalent — establishing provenance for the pattern).
4. Includes a "Composition" or "Out of scope" section that names the boundary (graceful-degradation for raw Claude Code).

**Verified by:** `tests/test_AC_LSK_3_body_content_shape.py` (5 packages × body-shape assertions).

### AC.LSK.S — sealed-component fence: `plugins/loam-skills/`

Single-component fence on `plugins/loam-skills/` (the new plugin's own seal-test fences `plugins/loam-skills/skills/` along with the rest of the plugin). Sidecar advance: `plugins/loam-skills/tests/SEAL_COMMIT`. No edits outside `plugins/loam-skills/` permitted, plus the universal `docs/rebuild/plans/` admission for the sub-plan + manifest, plus an explicit `extra_allowed_files: [install-from-source.txt, docs/install-from-source.md]` admission for adding the Tier K install line.

**Verified by:** post-seal `git diff <BASELINE>..<seal_sha> --name-only` confined to `plugins/loam-skills/` + `docs/rebuild/plans/` (universal-admitted) + `install-from-source.txt` + `docs/install-from-source.md` (admitted via `extra_allowed_files`).

---

## 6. Method-level choices (builder's call per ODD §1.1)

- **Frontmatter minimalism.** Only `description` (Anthropic-recommended). Skip `name` (defaults to directory). Skip `disable-model-invocation` / `allowed-tools` / `argument-hint` / `paths` / etc — none warranted for reference-content skills.
- **Body section shape (each SKILL.md):** intro paragraph; `## What this skill captures`; `## When to use`; `## How the persona applies it`; `## Graceful degradation` (raw-Claude-Code path); `## Composition` (which loam patterns this overlaps with); `## Out of scope`. Mirrors the existing flat-skill body shape (`memory-search.md`, `start-project.md`) for cross-skill reading consistency.
- **Plugin pyproject.toml shape.** Mirror `plugins/dev-sdlc/pyproject.toml`'s top-level fields. NO `loam.bootstrap.contributions` entry-point (skills are filesystem-discovered by Claude Code, not by loam's bootstrap). NO `loam.cli.subcommands`. Only `package-data` for the markdown files so editable install includes them. `name = "loam-plugin-loam-skills"`. `version = "0.1.0"`.
- **install-from-source.txt update.** Append a "Tier K — Loam Skills plugin" section after Tier J (dev-sdlc); single line `-e ./plugins/loam-skills`. Mirror the same in `docs/install-from-source.md`'s "Per-component fallback" snippet.
- **Plugin README minimum.** ~30-50 lines: what the plugin contains; how skills are discovered (Claude Code reads them); per-skill one-line summary; install snippet; link to Anthropic SKILL.md docs.
- **Test file shape.** Three test files mirror the AC structure (LSK.1, LSK.2, LSK.3). `test_no_sealed_amendments.py` is the standard sealed-component partner test that fences cross-component changes (mirror `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`).
- **Smoke verification.** Three smokes (one per AC + a fence-clean check). Smokes run against the actual `plugins/loam-skills/skills/` tree, not a tmp fixture (the markdown files ARE the artefact; nothing to fixturise).

---

## 7. Apply commit ladder

```
ce58521 (canonical pos-v2 HEAD pre-build)
  │
  ▼
<plan-doc commit> — this sub-plan-doc + AC.LSK family pre-grep notes
  │
  ▼
<source edit commit> — plugins/loam-skills/ component:
  │   - pyproject.toml + README.md
  │   - 5 × skills/<name>/SKILL.md
  │   - tests/test_AC_LSK_{1,2,3}_*.py
  │   - tests/test_no_sealed_amendments.py
  │   - tests/SEAL_COMMIT (initial seed)
  │   + install-from-source.txt (Tier K append)
  │   + docs/install-from-source.md (Tier K append in fallback section)
  │  (this commit becomes the BASELINE for the manifest)
  │
  ▼
<manifest commit> — manifest.yaml authoring; baseline pinned at the source-edit commit
  │
  ▼
<chore(amend): apply commit> — auto-committed by `loam amend apply`
  │  per v0.1.2 item 6 (auto-commit lands sidecar bumps)
  │
  ▼
<chore(seals): seal commit> — deterministic seal commit from `loam amend seal`
  │
  ▼
<docs(plans): §8 backfill commit> — manual edit to roadmap §8 v0.1.3 row + add v0.1.3 item 1 sub-section
                                    (NOT via --plan-doc; the §8 row + sub-section pattern matches the v0.1.2 amendments which used manual backfill)
```

---

## 8. Smoke verification protocol

Three smoke scenarios (one per AC.LSK + a fence-clean cross-check):

### Smoke A (AC.LSK.1 + AC.LSK.2 — discoverability + frontmatter)

For each of the 5 packages, run a Python one-liner that imports `yaml`, opens the SKILL.md, splits on `---` to extract frontmatter, parses with `yaml.safe_load`, asserts `description` is present + non-empty + ≤1536 chars. Print the per-skill description preview (first 80 chars) for visual confirmation.

### Smoke B (AC.LSK.3 — body content shape)

For each of the 5 packages, grep the body for the required section markers (`## What`, `## When to use`, `## How`, `## Graceful degradation`, `## Composition`, `## Out of scope`) + assert each is present. Verify the body references at least one named loam pattern (CLAUDE.md, F3, ODD, M-FBM, FIDRAFT) per AC.LSK.3 #3.

### Smoke C (claude-code skill discovery — pip install editable + filesystem-walk dry-run)

Run `pip install -e ./plugins/loam-skills` against the canonical venv at `.venv/bin/python`. Assert `pip show loam-plugin-loam-skills` returns version 0.1.0. Then walk the on-disk filesystem at `plugins/loam-skills/skills/*/SKILL.md` to confirm Claude Code's discovery walk would find all 5 files (the schema's discovery rule is filesystem walk; we replicate the walk + assert 5 files match).

NOTE: a true "claude binary discovers the skill" smoke would require booting `claude` in a fixture context. Out of scope per Surface #6; static-walk smoke is sufficient verification at amendment-cycle level.

### Smoke D (post-seal fence-clean cross-check)

After seal, run `git diff <BASELINE>..<seal_sha> --name-only` and verify all paths fall in: `plugins/loam-skills/` + `docs/rebuild/plans/` + `install-from-source.txt` + `docs/install-from-source.md`. Zero paths outside.

### Smoke E (touched-only test pass)

Run `pytest plugins/loam-skills/tests/` and verify all new tests pass (~12 tests across 3 AC.LSK files + `test_no_sealed_amendments.py`).

---

## 9. Out of scope

- **Migration of existing flat-shape skills** (`plugins/dev-sdlc/skills/start-project.md`, `framework/primary-persona/skills/memory-search.md`, `framework/primary-persona/skills/memory-archive.md`) to the modern directory-per-skill shape — out of fence; v0.2+ amendment if Anthropic's discovery starts requiring it.
- **`loam.bootstrap.contributions` entry-point for loam-skills** — none required; skills are filesystem-discovered by Claude Code per the Anthropic schema. If a future contribution shape (e.g. a runtime skill registry) is needed, it lands as a follow-on amendment.
- **Live `claude` binary discovery smoke** — out of fence per Surface #6; static-walk smoke is sufficient at the amendment-cycle level. A "boot claude in a test fixture and assert the skill list contains the 5 names" smoke can land in v0.2 if regression coverage is desired.
- **dev-mode-manifest update for `plugins/loam-skills/`** — no edit to `plugins/dev-sdlc/dev-mode-manifest.yaml`. The `roots:` block declares only top-level audited zones; `plugins/dev-sdlc/` itself is not in roots, so `plugins/loam-skills/` doesn't change the partition's audit scope. If dev-mode loading wants to surface `plugins/loam-skills/` to the persona at session-start, that's a follow-on dev-mode-manifest amendment outside this fence.
- **PyPI publishing of `loam-plugin-loam-skills`** — deferred to v0.2 per the broader PyPI publish gate. The plugin installs from source via `install-from-source.txt`'s Tier K line at v0.1.3.
- **A 6th SKILL package or beyond** — Decision D locks at 5; subsequent packages are v0.1.4+ work.
- **Reference scripts inside the SKILL packages** — none in v0.1.3. The dispatcher said "1-3 reference scripts each as needed". After authoring, all 5 packages are pure-markdown reference content; no scripts add load-bearing value at v0.1.3. Can extend in v0.1.4 if specific patterns benefit.
- **Updating primary-persona's prompt template to reference the new skills by name** — out of fence; the persona discovers skills generically (Claude Code's slash-command surface). Persona-side awareness lands in v0.1.4 V2.B subagent personas if useful.

---

## 10. Test plan

Three new test files under `plugins/loam-skills/tests/` (one per AC.LSK, mirroring the LAE.* shape):

- `test_AC_LSK_1_skill_packages_present.py` — 5 tests (one per package): file exists; frontmatter delimited; frontmatter parses as dict; description present + non-empty + ≤1536 chars; body non-empty.
- `test_AC_LSK_2_frontmatter_well_formed.py` — 5 tests (one per package): directory name kebab-case + ≤64 chars; if `name` field present, matches directory; description has trigger-phrase clause; no unknown frontmatter fields.
- `test_AC_LSK_3_body_content_shape.py` — 5 tests (one per package): required sections present; body references a loam pattern; graceful-degradation section names raw-Claude-Code path.

Plus the standard `test_no_sealed_amendments.py` (sealed-component partner; mirrors `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`) — confirms no in-fence sealed-amendment violations.

Touched-only test scope (per amendment-dispatch-speedup CDC): `pytest plugins/loam-skills/tests/`.

Cross-component sweep: scoped sweep on `plugins/loam-skills/` only (single-component fence). Pre-existing seal-discovery globs `framework/*/tests/SEAL_COMMIT`; sweep on plugins-located components is verified manually + via the touched-only run (per the v0.1.2 item 6 status note about plugins-discovery limitation).

---

## 11. ODD §2.5 mapping

Every line of the source edit maps to a named AC:

- 5 × `skills/<name>/SKILL.md` files → AC.LSK.1, AC.LSK.2, AC.LSK.3 (each file verified across all three).
- `plugins/loam-skills/pyproject.toml` → AC.LSK.S (component metadata; nothing else binds to it).
- `plugins/loam-skills/README.md` → AC.LSK.S (component README; standard component shape; no AC binds to its content beyond fence-existence).
- `plugins/loam-skills/tests/test_AC_LSK_{1,2,3}_*.py` → AC.LSK.1, AC.LSK.2, AC.LSK.3 respectively.
- `plugins/loam-skills/tests/test_no_sealed_amendments.py` → AC.LSK.S.
- `plugins/loam-skills/tests/SEAL_COMMIT` → AC.LSK.S (sidecar; standard).
- `install-from-source.txt` Tier K append → AC.LSK.S (component is installable; verifies via `pip install -e ./plugins/loam-skills` smoke).
- `docs/install-from-source.md` Tier K append → AC.LSK.S (mirror of the requirements-file change in the prose guide).
- Manifest + sub-plan-doc → AC.LSK.S (fence + provenance).

No silent fall-throughs. No method-in-acceptance smuggling.

---

## 12. Predecessor commits

- `9d58062` — V11.A seal (orchestrator runtime fix).
- `7d19a7e` — V11.E seal (graphiti probe graceful-skip).
- `32ff67d` — ack-first persona contract seal.
- `2c32c1b` — loam-amend ergonomics sweep seal (auto-commit + --allow-untracked-globs + partner-prefix fix).
- `7ae346d` — v0.1.3 R.5 design note 1 (`primary-persona-shape.md`) seal.
- `ce58521` — v0.1.x roadmap §2 relabel commit (canonical pos-v2 HEAD pre-this-build).

---

## 13. Status file outline

`/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-3-skill-packages-status-2026-05-04.md` will record:

- BASELINE + plan-doc + source-edit + manifest + apply (auto-commit) + seal + §8-backfill commit SHAs.
- Per-AC verification (test names + smoke scenario outputs).
- Surfaces 1-7 status (each marked resolved-in-band or deferred).
- Per-package preview block (description + first body section per skill).
- Smoke C output (pip install editable + filesystem walk verification).
- Backwards-compat: confirmation that existing flat-shape skills (`start-project.md`, `memory-search.md`, `memory-archive.md`) still work post-seal (out-of-fence; verified via grep).

---

## 14. Method-decision register — placeholder

Reserved for the deterministic record of:

- Plan-doc commit SHA
- Source-edit commit SHA
- Manifest commit SHA
- Apply commit SHA (auto-committed by `loam amend apply`)
- Seal commit SHA (deterministic seal)
- §8 backfill commit SHA (manual edit to roadmap §8)

Backfilled into the parent roadmap §8 post-seal. The §8 v0.1.3 row currently reads `(planned)`; this amendment populates it with the first sub-section (`### v0.1.3 — item 1 (SKILL.md packages bundle) — sealed 2026-05-04`).

---

*End of v0.1.3 item 1 sub-plan.*
