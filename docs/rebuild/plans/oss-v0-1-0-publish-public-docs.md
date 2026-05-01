# OSS v0.1.0 publish — public-docs lane (M7) — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-05-01.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2 / future loam).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 row M7; this sub-plan owns the documentary lane referenced as `oss-v0-1-0-publish-public-docs.md`.
**Target lane in §6:** Lane B — parallel-safe with Lane A's serial amendment chain (M1–M6 + M-FBM); blocks M11 dry-run via AC.OSS.5 sweep.

**Authority documents:**

- Programme master: `docs/rebuild/plans/oss-v0-1-0-publish.md` — §3 prime ACs (AC.OSS.1 stranger-bootable / AC.OSS.3 no-dev-machinery / AC.OSS.5 documentary-rebrand / AC.OSS.6 plugin-pattern); §5 work-decomposition row M7; §6 sequencing rule 5; §13 D-Q.OSS.* register.
- Memory-pivot precedent (recent landed sub-plan; format reference): `docs/rebuild/plans/oss-v0-1-0-publish-memory-pivot.md`.
- VALUE_PROPOSITION: `docs/rebuild/VALUE_PROPOSITION.md` — AC.PO.1 + AC.PO.2.
- CLAUDE.md design lenses: `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md` §1.
- STATE.md: `docs/rebuild/STATE.md` — components inventory + governing rules.
- Partition manifest (shipping-set ground truth): `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- Long-form ODD (condensation source): `plugins/dev-sdlc/docs/odd-methodology.md` (794 lines) + `plugins/dev-sdlc/docs/odd-in-loam.md` (1058 lines).
- Existing pre-publish docs (rewrite-not-greenfield posture): `docs/positioning.md` (121 lines), `docs/design/odd.md` (259 lines), `README.md` (138 lines).

---

## 1. Summary / TL;DR

**Documentary lane authoring the public docs scaffold v0.1.0 ships
with.** Dispatched as parallel background agents per
`feedback_background_default_for_authoring`. Eight outcome-shape AC
families (`AC.M7.positioning`, `getting-started`, `architecture`,
`components`, `odd`, `readme`, `cross-refs`, plus `AC.M7.S` programme
seal) cover six top-level docs + 15 component-reference files. Lane
is parallel-safe with Lane A's M1–M6 + M-FBM serial chain and blocks
M11 dry-run via AC.OSS.5 sweep.

**Discovery during plan authoring:** `docs/positioning.md` (121
lines), `docs/design/odd.md` (259 lines), and `README.md` (138
lines) **already exist** at high quality. M7 is partial-greenfield —
verify-first, rewrite-only-on-fail; author the missing pieces
(`getting-started.md`, `architecture.md`, `components/<name>.md`
×15, `plugins/dev-sdlc.md`).

**Estimated AI-time:** 90–180 min wall-clock (parallel agents;
re-priced from master plan §5 row M7 30–60 min, which pre-dated
per-component fan-out). **Sequencing:** parallel with M-FBM + M6
builds; lands with or before M8; before M11.

---

## 2. Owner ruling captured

(none yet — this plan-doc surfaces decisions for owner ruling at §11
before build dispatch)

---

## 3. Spec-objective placement (per CLAUDE.md §2.5)

Lane binds to programme prime ACs:

- **AC.OSS.1 (stranger-bootable).** `getting-started.md` IS the
  stranger walkthrough; `positioning.md` IS the "why am I here"
  surface; `README.md` IS the GitHub-landing entry point.
- **AC.OSS.3 (no dev machinery public).** Docs introduce loam
  concepts without referencing pos-amend / ODD-seal-tests /
  amendment-numbering / FUTURE_IDEAS / per-amendment-plan
  vocabulary. Condensed `docs/design/odd.md` ships methodology in
  user-shaped form.
- **AC.OSS.5 (documentary rebrand).** All M7 docs read `loam` not
  `pos-v2` / `pOS v2` / `POS_V2_*` / `pos-amend`. M11 grep
  verifies.
- **AC.OSS.6 (plugin demo).** `architecture.md` introduces plugin-
  extension protocol; `docs/plugins/dev-sdlc.md` (per D-Q.M7.6)
  demonstrates plugin composition.
- **AC.PO.1 (translation-burden).** Stranger path (positioning →
  README → getting-started → architecture) absorbs intent-to-
  session translation. Per-component refs are stable answer
  surfaces.
- **AC.PO.2 (toolkit-primitive).** Docs corpus IS a discoverable
  toolkit surface for plugin authors / contributors / persona.

**ODD §2.5 reverse-direction commitment.** Every section traces to
a named AC; non-objective passages justify or get removed.

---

## 4. Three-lens analysis (per CLAUDE.md design lenses)

- **Lens 1 (Claude leverage).** Every M7 doc composes against Claude-
  Code primitives: `getting-started.md` walks `git clone` → `loam
  init` → `claude` (no bespoke installer); `architecture.md`
  introduces the harness as composing against hooks (PreToolUse /
  SessionStart / UserPromptSubmit / Stop) + MCP + skills + plugins +
  settings.json hierarchy; per-component refs name the Claude-native
  invocation surface (which hook / CLI verb / skill / session
  primitive); `positioning.md` + `README.md` lead with "loam attaches
  to Claude" — no parallel AI substrate. **Pass.**
- **Lens 2 (harness + primary-persona).** **Primary-persona test:**
  stranger reads README → positioning → decides to clone; post-clone
  reaches first session via getting-started; asks persona "what is
  X?" → persona points at `docs/components/<X>.md` (stable URL).
  Zero pos-v2-internal vocabulary required. **Harness test:** docs
  corpus IS a toolkit primitive — discoverable surface plugin
  authors / contributors / persona itself cite by stable path; ODD
  doc packages a methodology primitive; architecture.md packages
  the plugin-composition pattern. **Pass on both.**
- **Lens 3 (ODD authoring).** Each AC outcome-shape (reads coherently
  / fits length budget / no unintroduced vocabulary / cross-refs
  resolve), not method-shape (section order, sentence structure,
  code-fence languages). Method-shape is per-doc builder's call.
  **Pass.**

---

## 5. Acceptance criteria (lane-level invariants)

Outcome-shape only. Each AC carries deterministic verification.
Cross-doc consistency lives at AC.M7.cross-refs; each individual doc
carries its own per-doc AC family.

### AC.M7.positioning.1 — `docs/positioning.md` reads coherently to a stranger

`docs/positioning.md` opens with one paragraph (≤6 sentences) stating
who loam is for and what claim it makes; subsequent sections introduce
the harness's composition pattern, the primary-persona role, and the
non-claims (what loam is **not**). Total length ≤500 lines. No
`pos-v2` / `pOS v2` / `POS_V2_*` strings appear (post-M1 rebrand
verified). Every internal-vocabulary term (e.g. "primary persona",
"workspace", "harness") has prior introduction in the same doc OR is
a Claude-Code term assumed familiar.

**Verification.** `wc -l docs/positioning.md` ≤500. `grep -E
'pos-v2|pOS v2|POS_V2_|pos-amend|pos\.v2|com\.pos-v2'
docs/positioning.md` returns zero. Stranger-readability heuristic:
introduction-before-use grep — every term in the loam-vocabulary set
(`primary persona`, `harness`, `workspace`, `plugin`, `component`,
`scope`) appears with an explanatory sentence on first occurrence.

### AC.M7.getting-started.1 — `docs/getting-started.md` walks clone→init→first-session in <300 lines

`docs/getting-started.md` exists; opens with the prerequisite list
(Claude Code installed; macOS or Linux; Python 3.11+); presents the
clone → init → first-session sequence as runnable shell commands; ends
with a "what now?" pointer to `docs/positioning.md` and
`docs/architecture.md`. Every shell command is copy-pasteable. No
internal-vocabulary terms unintroduced.

**Verification.** `wc -l docs/getting-started.md` ≤300. Every fenced
code block tagged `bash` / `sh` parses as valid shell. No grep matches
for pre-rebrand strings. Stranger-runnability spot-check: builder
runs the sequence on a fresh user account or container and reaches
first useful primary-persona session.

### AC.M7.architecture.1 — `docs/architecture.md` covers harness composition + lifecycle + plugin protocol in <600 lines

`docs/architecture.md` exists; explains the harness as a composition
of Claude-native primitives + loam-specific components; covers the
session lifecycle (clone → init → SessionStart → turn → Stop →
background work → next session); introduces the plugin-extension
protocol with the Dev/SDLC plugin as the canonical example; cross-
references `docs/components/<name>.md` for per-component detail.
Length ≤600 lines.

**Verification.** `wc -l docs/architecture.md` ≤600. Cross-references
to `docs/components/<name>.md` resolve (link-integrity check). The
five Claude-native primitives loam composes against (hooks, MCP,
skills, plugins, settings.json) each appear with at least one
mention naming a loam component that uses them. No grep matches for
pre-rebrand strings.

### AC.M7.components.<name>.1 — Each per-component reference doc is <300 lines and covers what+how+observable-surface

For each component in the v0.1.0 shipping set per the partition
manifest's `public_only` / `dev_and_public` glob list (verified at
build-time, currently 15 components: `cost-governance`, `dormancy`,
`hands-off-lifecycle`, `objective-tracker`, `observability-aggregator`,
`orchestrator`, `primary-persona`, `reversibility-primitive`,
`safety-layer`, `scope-of-work`, `self-correction`, `self-upgrade`,
`telegram-interface`, `workspace-bootstrap`, `workspace-sync`), a
file `docs/components/<name>.md` exists containing:

- a one-paragraph statement of what the component does (intent +
  outcome),
- how-to-invoke (which Claude-native hook event / CLI verb / skill /
  MCP tool surfaces it; or "internal — composed by other components"
  if the component has no user-facing surface),
- observable surface (which OTel events / files / SQLite tables /
  artefacts the component writes; what the user can `tail` / `cat` /
  `grep` to see it working).

Length ≤300 lines per doc. No pre-rebrand strings.

**Verification.** For each component in the shipping set, `wc -l
docs/components/<name>.md` ≤300. Each doc contains the three named
sections (regex-detectable headers). No grep matches for
`pos-v2|pOS v2|POS_V2_|pos-amend`. Memory-system handling per
D-Q.M7.1 ruling (omit / stub / link-only).

### AC.M7.odd.1 — `docs/design/odd.md` is a ~200-line condensation of the long-form methodology

`docs/design/odd.md` carries the ODD methodology in user-shaped form:

- the three principles (objective + constraints + acceptance
  criteria; method is the builder's call),
- the no-non-objective-code rule (ODD §2.5: every line / branch /
  test maps to a named AC),
- the plan-before-code rule (every build writes a plan before
  source edits),
- the halt-and-surface rule (builders halt on ODD violations rather
  than silently extending),
- worked example showing how to read or author one acceptance
  criterion.

Length 150–250 lines (rough ~200-line target; tightness matters more
than exact count). Preserves authority of long-form via a single
"For full detail see [long-form]" pointer **only if the long-form
ships**; if long-form stays dev-only, `odd.md` carries authority
itself with no broken back-pointer (this is the public methodology
surface). The current 259-line `docs/design/odd.md` is a strong
starting point and may already pass — verification check first
before rewrite.

**Verification.** `wc -l docs/design/odd.md` 150–280 (allow upper
slack for worked-example expansion). Each of the four named structural
rules appears with a regex-detectable heading. No back-references to
dev-only docs unless those docs ship in the public partition (M2
manifest decides; if dev-only, no link).

### AC.M7.readme.1 — `README.md` is the stranger-clone-bootable entry point

`README.md` opens with one-line value prop + paragraph context;
provides quickstart (3–5 commands maximum); links to
`docs/positioning.md` for the long story, `docs/getting-started.md`
for the install, `docs/architecture.md` for the design,
`docs/design/odd.md` for the methodology, and `LICENSE` for the
license; ends with a one-paragraph contributor-pointer. Length ≤200
lines. The existing 138-line README is a strong starting point;
verification first before rewrite.

**Verification.** `wc -l README.md` ≤200. `docs/positioning.md` +
`docs/getting-started.md` + `docs/architecture.md` + `docs/design/
odd.md` + `LICENSE` are all linked (link-integrity check). No
pre-rebrand strings.

### AC.M7.cross-refs.1 — All cross-document links resolve

Every `[text](path)` link inside any of the M7 docs resolves to a
file present in the public synthesis partition (post-M2 partition
manifest application). Anchors (e.g. `#section-name`) match
generated-from-headings.

**Verification.** A link-integrity sweep over the M7 doc set (all
six top-level docs + per-component refs) returns zero broken links.
Tool: builder's call (`markdown-link-check` or hand-grep + verify).
Sweep runs against the synthetic v0.1.0 tree, not just canonical
(catches partition-stripped target leaks).

### AC.M7.S — Programme-level seal

After all per-doc ACs pass, the synthetic v0.1.0 tree (post-M2
partition + post-M9 substitution) ships exactly the M7 doc set;
AC.OSS.5 grep verification (no `pos-v2` / `pOS v2` / `POS_V2_` /
`pos-amend` matches in user-facing prose) passes for the M7 corpus.

**Verification.** Synth canonical HEAD via the M2-extended pipeline;
`find synthetic/docs synthetic/README.md -type f` returns the
expected M7 file list (no extras, no missing); grep for pre-rebrand
strings returns zero in the M7 corpus.

---

## 6. Sequencing — slot proposal in master plan §6

Master plan §6 already names M7 parallel-safe with the M1–M6 serial
chain. Refinement:

1. **M7 dispatches alongside M-FBM** (or any M5+ build). File sets
   disjoint; trees don't race.
2. **M7 completes before M11 dry-run.** AC.OSS.5 sweep at M11 reads
   M7's output; otherwise wasteful re-runs.
3. **M7 lands with or before M8 (license-governance).** README.md
   references `LICENSE`; recommend dispatching M8 alongside M7 in
   same calendar window (M8 ~10–20 min trivial-shape).
4. **M7 lands AFTER M-FBM partition-manifest update.** AC.M7.cross-
   refs.1 + AC.M7.S sweep against synthetic tree which reads the
   partition manifest; D-Q.M7.1 (memory-system handling) needs
   M-FBM's reclassification landed.
5. **M7 lands AFTER M1.rename-series complete.** Pre-rebrand strings
   in M7 docs would fail AC.OSS.5 sweep at M11. Verify M1c–M1g
   sealed pre-dispatch.
6. **Per-doc agents parallel-safe with each other** (disjoint
   files). Per `feedback_serialize_amendment_builds`, the single-
   tree git-index-lock race applies to *amendment builds* (which
   run pos-amend / tests / sealed fences); M7 docs are plain-git
   commits without that machinery — coordinator-serialised commits
   (D-Q.M7.4) is the safe shape.

**Master plan §6 unchanged**; this sub-plan refines §6 rule 5 with
per-doc-agent-fan-out detail.

---

## 7. Hard constraints (lane-wide)

- **No new external runtime deps.** M7 is pure docs authoring; no
  Python imports added; no MCP tools added; no settings.json edits.
  Constraint matches programme master HC analogue.
- **No structural changes to component source.** M7 reads component
  source to author per-component-ref docs but writes only to
  `docs/`. No `framework/<comp>/` edits.
- **No `git commit --amend`.** Corrective commits are NEW commits
  per `feedback_no_amend_in_agent_dispatches`.
- **`pos-amend apply` (or post-rename `loam amend apply`) is NOT
  invoked** — M7 docs are not a sealed-component amendment; no
  amendment fence; no manifest entry. Lands as plain doc commits
  (or one squashed doc commit per builder's call) per master plan
  §5 row description ("Multi-artefact authoring → background
  agents").
- **No edits to dev-only artefacts.** M7 docs read `plugins/dev-
  sdlc/docs/odd-methodology.md` + `odd-in-loam.md` for ODD
  condensation source material but does NOT edit them. Long-form
  ODD stays dev-only per master plan §3 AC.OSS.3.
- **No edits to existing high-quality docs unless tightening
  required.** `docs/positioning.md` (121 lines) and `README.md`
  (138 lines) and `docs/design/odd.md` (259 lines) **already
  exist**. M7 verifies first (per-doc AC outcome bound); only
  rewrites if AC fails or the doc fails the AC.OSS.5 grep
  post-rebrand. **Rewrite-only-on-fail posture** to preserve
  existing authoring effort.
- **AC-prefix uniqueness:** M7 uses `AC.M7.*`. No collision with
  M1–M9 / M-FBM / M-GMP per programme convention.
- **Halt-and-surface on ODD §2.5 violations** in any code/doc/
  manifest the builder edits or reads (per
  `feedback_subagent_odd_violation_halt`).

---

## 8. Out of scope (lane-wide; named per ODD §2.5)

- **Long-form `plugins/dev-sdlc/docs/odd-methodology.md` shipping
  publicly** (programme master AC.OSS.3 + audit D5). Long-form
  stays dev-only; condensed `docs/design/odd.md` is the public
  methodology surface.
- **Long-form `plugins/dev-sdlc/docs/odd-in-loam.md` shipping
  publicly.** Same as above.
- **`plugins/dev-sdlc/docs/duration-estimation-rubric.md` shipping
  publicly.** Programme master AC.OSS.3 explicitly excludes.
- **`docs/rebuild/` tree shipping publicly.** Per AC.OSS.3.
- **Per-amendment builder-plan / manifest authoring.** M7 is not a
  sealed-component amendment; no per-amendment artefacts.
- **CLAUDE.md rewrite for stranger-readability.** Out of scope —
  CLAUDE.md ships per AC.OSS.5 rebrand at top-level, but the
  stranger-readability AC family is M7-only on the docs corpus
  (CLAUDE.md is harness-instruction surface, not user-docs).
- **`docs/CLAUDE_CAPABILITIES.md` rewrite.** Existing `docs/
  CLAUDE_CAPABILITIES.md` (already at top of `docs/`) is dev-mode
  reference; out of scope for M7. (Verify partition class at
  build-time; if `dev_only`, strip from public; if `dev_and_public`,
  M7 confirms it doesn't violate AC.OSS.3.)
- **Plugin-author guide.** Future v0.2 work — once second plugin
  (M-GMP) lands, a plugin-author guide synthesises Dev/SDLC + GMP
  patterns. Not v0.1.0 scope.
- **Tutorial-style how-to docs** (e.g. "build your first scope",
  "set up a recurring schedule"). Out of scope for v0.1.0 docs
  scaffold; getting-started.md covers minimal first-session only.
- **Translated docs (non-English).** Not v0.1.0 scope.
- **API reference auto-generation** (e.g. Sphinx). Not v0.1.0
  scope; per-component-ref docs are hand-authored.

---

## 9. Halt-and-surface conditions

Per `feedback_subagent_odd_violation_halt` +
`feedback_critical_thinking_on_deviations`. Builders halt on any of:

1. **A per-component-ref doc would expose dev-discipline machinery
   to public synthesis** (AC.OSS.3 violation surfacing at doc time).
   Owner rules: omit, or extend partition to admit a stub.
2. **ODD condensation can't fit ~200 lines without losing the
   structural rules** (no-non-objective-code / plan-before-code /
   halt-and-surface). Owner rules: widen budget vs accept short
   form (long-form is dev-only per AC.OSS.3, so back-pointer is
   not an option). See D-Q.M7.2.
3. **Positioning text uses internal-vocabulary terms unintroduced**
   (AC.M7.positioning.1). Tighten in-band.
4. **Cross-references between docs break** (AC.M7.cross-refs.1).
   Tighten in-band.
5. **A shipping-set component has no user-facing surface to
   document** (purely internal-composed). Surface as "do we
   document this?" decision.
6. **D-Q.M7.1 / D-Q.M7.6 unruled at dispatch.** Halt at first M7
   dispatch.
7. **ODD §2.5 violation surfaces in surrounding code/docs during
   M7 research.** Per the global rule.
8. **Pre-rebrand strings in existing docs** (positioning.md /
   README.md / odd.md) that M1.rename-series M1a missed. Fold into
   M7 corrective rewrite as part of AC.OSS.5 sweep.
9. **Wall-time exceeds estimate by >50%** (programme master §8
   trigger 8).
10. **Per-component-ref drift risk** (D-Q.M7.7 default rec is
    "no edits to `framework/<comp>/README.md`"; if a builder finds
    the user-facing answer LIVES in the internal README and
    wholesale-restating in `docs/components/<name>.md` is
    duplication-heavy, halt and re-rule).
11. **`getting-started.md` cannot stay <300 lines** while covering
    the chosen audience (D-Q.M7.3). Split into
    `docs/getting-started/<audience>.md` or pick narrower scope.

---

## 10. Risks (lane-level)

1. **Partial-greenfield posture (rewrite-vs-tighten ambiguity).**
   Mitigation: per-doc AC verification gate before rewrite; rewrite
   only on AC fail.
2. **Per-component-ref fan-out (15 docs) blows estimate.**
   Mitigation: per-component AC loose enough (≤300 lines, three
   named sections) for fast authoring; if rigour required for one,
   others independent in parallel.
3. **ODD condensation loses fidelity.** Mitigation: halt trigger
   §9.2; owner rules budget-vs-fidelity.
4. **Cross-refs break when M2 partition reclassifies a target.**
   Mitigation: §6 rule 4 (M7 lands after M-FBM); sweep runs against
   synthetic tree.
5. **Builder rewrites passing docs anyway (wasted work).**
   Mitigation: §7 "rewrite-only-on-fail" HC; pre-dispatch verify.
6. **Plugin-pattern conflict** between `docs/architecture.md` and
   `plugins/dev-sdlc/README.md`. Mitigation: architecture.md owns
   abstract pattern; plugin README owns plugin-specific detail;
   cross-link.

---

## 11. Decisions remaining for owner ruling

Per `feedback_summarize_and_surface_decisions` — six named decisions
with recommendations. Owner rules from this summary; M7 build agents
inherit the rulings.

### D-Q.M7.1 — Memory-system component-reference doc

**Q.** Memory-system is reclassified `dev_only` post-M-FBM. Options:
(a) omit entirely from `docs/components/`; (b) stub pointing at
post-M-GMP plugin path (link broken at v0.1.0 since M-GMP is post-
v0.1.0); (c) document file-based memory only as
`docs/components/memory.md`, no graphiti reference at v0.1.0.

**Rec. (c).** v0.1.0 ships file-based memory; user-facing concept
is "memory" (singular); graphiti is a v0.1.x plugin not visible in
v0.1.0 docs. Doc-name divergence from source-dirname is acceptable
at AC outcome bound. Doc references the file-based memory
contributor inside `framework/primary-persona/` per AC.MFBM.1+2+5.

### D-Q.M7.2 — ODD condensation: vocabulary fidelity vs simplification

**Q.** Condense 1852 lines of long-form ODD into ~200 lines.
(a) preserve methodology vocabulary fully (ODD, objective,
constraint, AC, outcome-shape / method-shape, no-non-objective-code,
plan-before-code, halt-and-surface, five-gate); or (b) simplify to
user-shaped language ("outcome-shape testing", etc.) shedding
vocabulary.

**Rec. (a).** Reasons: AC.OSS.6 (Dev/SDLC plugin demo) makes ODD-
vocabulary the plugin's surface anyway; `docs/design/odd.md` is the
*methodology* surface, vocabulary fidelity is its job; existing
259-line file already preserves vocabulary at high quality.
Caveat: introduce each term with a one-sentence gloss on first
occurrence (stranger-readability AC stays satisfied).

### D-Q.M7.3 — `getting-started.md` audience

**Q.** (a) Claude Code user only; (b) generic Claude user
(Claude.app / API); (c) both, two paths.

**Rec. (a) Claude Code user only.** loam's composition surface IS
Claude Code (hooks / settings / plugins / MCP); shape (b) requires
faking parity that doesn't yet exist. v0.1.0 audience is
developer-leaning (per Dev/SDLC must-ship + R2 ruling). Keeps
getting-started.md <300 lines. v0.2+ may add a generic path.

### D-Q.M7.4 — Per-doc agent commit strategy

**Q.** Multiple parallel agents fanning out: (a) each agent commits
directly with pull-rebase-retry; (b) each agent emits a patch,
coordinator commits in sequence; (c) each agent on own branch,
coordinator merges at end.

**Rec. (b) coordinator-serialised commits.** Matches
`feedback_serialize_amendment_builds` spirit; coordinator can run
cross-doc sweeps before committing; simplest rollback if one
agent's output fails verification. Cost: parent-session attention
during agent runs (mitigated by natural pacing as agents finish).

### D-Q.M7.5 — Per-component-ref doc shape

**Q.** 15 components fan-out: (a) per-component
`docs/components/<name>.md` ×15; (b) grouped by phase (×4);
(c) grouped by user-facing-vs-internal (×2); (d) single
`docs/components.md` with N sections.

**Rec. (a) Per-component refs.** Stable URL per component is a
toolkit primitive (Lens 2 harness test) — persona points user at
one URL; parallel-agent fan-out fits cleanly; per-component AC
verifies independently. `docs/components/index.md` ties them with
a one-line summary table.

### D-Q.M7.6 — Dev/SDLC plugin reference placement

**Q.** (a) link to plugin's own README from architecture.md only;
(b) include as `docs/components/dev-sdlc.md`; (c) separate
`docs/plugins/<name>.md` category.

**Rec. (c) Separate `docs/plugins/` category.** Establishes
plugins-doc-pattern at v0.1.0 (mirrors programme D-Q.OSS.5);
Dev/SDLC plugin is the canonical example; component-vs-plugin
distinction stays clean (components are sealed-fence stable;
plugins are extension-protocol shape). v0.1.0 ships
`docs/plugins/dev-sdlc.md` only; M-GMP adds graphiti-memory.md
post-v0.1.0.

### D-Q.M7.7 — Per-component-readme vs `docs/components/<name>.md` overlap

**Q.** Several `framework/<comp>/README.md` files exist (component-
internal). Risk of drift; touching internal README triggers
seal-test fence.

**Rec.** `docs/components/<name>.md` is the canonical *user-facing*
reference; `framework/<comp>/README.md` stays as *contributor-
facing* (no edits — out of M7 fence). Cross-link once at end:
"For internal implementation detail see [framework/<name>/
README.md]". Drift is a pre-existing risk owned by per-component
amendments, not introduced by M7.

---

## 12. Halt-and-surface findings encountered during plan authoring

**Findings (none triggers a halt):**

1. **Significant discovery (not a halt).** `docs/positioning.md`
   (121 lines), `docs/design/odd.md` (259 lines), and `README.md`
   (138 lines) **already exist** at high quality. M7 is partial-
   greenfield. ACs accommodate via "verify first, rewrite-only-
   on-fail" posture (§7 HC).
2. **No methodology breach.** ACs outcome-shape; partition /
   sealed-fence machinery not bypassed.
3. **No surrounding-code ODD violation** surfaced during research.
4. **Master plan §5 estimate observation.** Row M7 30–60 min was
   pre-fan-out; re-priced 90–180 min at §13. Out-of-band master-
   plan update at next dispatch.
5. **Sequencing dependency on M-FBM verified.** §6 rule 4
   requires M-FBM partition update before AC.M7.S sweep;
   dispatcher verifies at M7 dispatch.
6. **Sequencing dependency on M1.rename-series verified.** M1a–M1b
   sealed; M1c–M1g state checked at M7 dispatch.
7. **Asymmetric opportunity** (per
   `feedback_asymmetric_problem_solving`): if existing docs pass
   verification-first, build cost collapses to "author missing
   only" (18 new files, 0 rewrites) — estimate skews to lower
   bound. High-leverage: verification pass FIRST.
8. **Name divergence surfaced for D-Q.M7.1.** Source `memory-
   system` vs doc-name `memory.md`. Acceptable at AC outcome
   bound; D-Q.M7.1 names the convention explicitly.

**Halt summary.** None. Plan authorised pending owner sign-off
on §11 D-Q.M7.1..7.

---

## 13. AI-time estimate (re-priced)

Master plan §5 row M7 estimated 30–60 min before per-component
fan-out was concrete. Re-priced:

- **Verification-first pass:** read existing positioning.md /
  odd.md / README.md; run per-doc AC checks. **5–15 min**.
- **New-doc authoring (parallel agents):** getting-started.md +
  architecture.md + components/<name>.md ×15 + plugins/dev-sdlc.md
  = 18 new files. Per-doc agent ~10–25 min midpoint ~15 min
  (rubric "medium docs create 10–30 min"). Sum agent-time ~270
  min midpoint; **parallelism critical-path ~25–40 min** (4–8
  agents simultaneously).
- **Coordinator-serialised commits** (D-Q.M7.4): review patch +
  cross-ref + grep + commit; ~30–60 min on top of agent
  critical-path.
- **Rewrite-of-existing contingency:** 0–90 min if 0–3 existing
  docs fail verification.
- **AC.M7.cross-refs sweep + AC.M7.S synth-and-grep:** 10–20 min.

**Wall-clock midpoint:** **90–180 min midpoint ~120 min**. Lower
bound: existing docs pass verification; parallel agents smooth;
commits clean. Upper bound: two existing docs need rewrite; one
component-ref needs research dive; cross-ref sweep finds breaks.

**Master plan §5 update needed** (out-of-band doc-only commit
mirroring M-FBM's §13 protocol): row M7 30–60 min → 90–180 min
midpoint 120 min.

---

## 14. Method-decision register (post-build)

Filled by agent / coordinator post-build (precedent: D-build.M9.* in
scrub; D-build.M-FBM.* in memory-pivot).

### M7 — OSS-build.M7.x — (post-build)

- **D-build.M7.1..7:** Per D-Q.M7.1..7 owner rulings (memory-system
  ref handling / ODD vocabulary / getting-started audience / commit
  strategy / per-component-ref shape / Dev-SDLC placement /
  per-component-readme overlap).
- **D-build.M7.8..N:** Agent-discovered method decisions (section
  ordering inside getting-started.md; link-check tool selection;
  existing-doc rewrite-vs-tighten choice per file).

### Commit SHAs (post-build)

- M7 per-doc commits: `<TBD>` ×N
- M7 cross-ref sweep + AC.M7.S corrective: `<TBD>`
- Master-plan §5 row M7 estimate-update commit: `<TBD>`

---

## 15. Backwards-compat verification (post-build)

- All pre-existing tests pass (M7 doesn't touch source).
- Cross-ref integrity verified (AC.M7.cross-refs.1).
- Synth + grep sweep verified (AC.M7.S).
- No `--amend`; corrective commits are NEW commits.
- No `pos-amend` invocation (M7 is not a sealed-component fence).

---

## 16. References

- **Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
- **Memory-pivot precedent:** `docs/rebuild/plans/oss-v0-1-0-publish-memory-pivot.md`.
- **VALUE_PROPOSITION:** `docs/rebuild/VALUE_PROPOSITION.md`.
- **CLAUDE.md design lenses:** `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md`.
- **STATE.md:** `docs/rebuild/STATE.md`.
- **Partition manifest:** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- **Long-form ODD (condensation source; dev-only):**
  `plugins/dev-sdlc/docs/odd-methodology.md` (794 lines);
  `plugins/dev-sdlc/docs/odd-in-loam.md` (1058 lines).
- **Existing pre-publish docs:** `docs/positioning.md` (121 lines),
  `docs/design/odd.md` (259 lines), `README.md` (138 lines).
- **Dev/SDLC plugin (M6 output):** `plugins/dev-sdlc/`.
- **Memory bullets carried forward:** `feedback_plan_before_code`,
  `feedback_subagent_odd_violation_halt`,
  `feedback_summarize_and_surface_decisions`,
  `feedback_critical_thinking_on_deviations`,
  `feedback_serialize_amendment_builds`,
  `feedback_no_amend_in_agent_dispatches`,
  `feedback_background_default_for_authoring`,
  `feedback_value_proposition_as_prime_objective`,
  `feedback_duration_estimation_rubric`,
  `feedback_loose_AC_text_fix_AC_not_implementation`,
  `feedback_asymmetric_problem_solving`.

---

*End of plan.*
