# v0.1.7 sub-plan — subagent personas + per-project PM + decision-surfacing + layered-skill discovery

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-04.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/plans/eric-final-delivery-plan-2026-05-04.md` (§2 v0.1.7 row).
**Predecessors:**
- `f04e925` — v0.1.3 SKILL.md packages bundle (5 base SKILLs sealed).
- `3f1d237` — v0.1.6 Cycle 1 seal (production-safety + bug fixes — `.claude/skills/.gitkeep` pre-create + loam-skills enrollment hint).
- `88674cb` — v0.1.6 Cycle 2 seal (3 new base SKILLs).
- `c3fa366` — current canonical pos-v2 HEAD; BASELINE candidate.

**BASELINE (pre-build tip):** `c3fa366`.
**Status-file target:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-7-status-2026-05-04.md`.
**Quality bar:** WOW Eric. No partial features. All 6 smoke dimensions exercised. SOFT smoke gate per Decision R; quality bar still applies.

---

## §1. Summary / TL;DR

v0.1.7 ships **four amendment cycles** (serialized per `feedback_serialize_amendment_builds`), addressing the four dispatcher-named bundles:

**Cycle 1 — 5 subagent personas + symlink registration** (multi-component fence):
- `plugins/dev-sdlc/agents/` (NEW directory) — 5 persona `.md` files (`loam-builder`, `loam-plan-author`, `loam-researcher`, `loam-reviewer`, `loam-documenter`). Each is a Claude-Code-discoverable subagent file (frontmatter: `name`, `description`, `model`, `tools`).
- `framework/workspace-bootstrap/` — first-run scaffold extends to symlink `plugins/dev-sdlc/agents/` → `<workspace>/.claude/agents/<name>.md` so Claude Code's project-agent discovery finds them.

**Cycle 2 — Per-project PM persona (NEW component)** (single-component fence — NEW):
- `framework/per-project-pm/` (NEW component) — PM-shape: contract dataclass + workspace-state loader + decision-surfacing API surface + persona-prompt template.
- Workspace-state lives at `<workspace>/.loam/pms/<pm-name>/` (state.yaml + decision-queue.yaml + audit-log/).

**Cycle 3 — Layered-skill discovery mechanism** (single-component fence):
- `framework/workspace-bootstrap/` — extends first-run scaffold to symlink plugin-tier skills (`plugins/<plugin>/skills/<name>/SKILL.md` → `<workspace>/.claude/skills/<name>/SKILL.md`); collision-handling rules; smoke-test fixture for workspace-local discovery.
- Note: workspace-bootstrap is also touched in Cycle 1; per the dispatcher fence, **Cycle 3 is serialized strictly after Cycle 1** seals (no parallel apply).

**Cycle 4 — Decision-surfacing + one-question-at-a-time** (single-component fence — extends Cycle 2):
- `framework/per-project-pm/` — extends Cycle 2 with: question-batching state, single-question-per-turn surfacing protocol, onboarding-mode flag, audit log of surfaced questions.

**Decisions baked at synthesis time:**
- Decision Q (one-question-at-a-time PM-enforced) — RESOLVED YES per parent §3. Cycle 4 implements structurally.
- Decision I (workspace-local skills under Anthropic-native `.claude/skills/`, not `.loam/pms/<pm>/skills/`) — RESOLVED YES per parent §3. PM references the skill set; doesn't own it.
- Decision H (PM as auto-creation driver) — primary persona for now; revisit at v0.2.0 (auto-creation MVP). Out of v0.1.7 scope.

**F2 Ruthless Feedback on scope realism (surfaced this turn):**

Synthesis estimate at parent §2 is 22–34 h for v0.1.7 with quality-bar absorption. This sub-plan is the largest non-extractor amendment build in pos-v2 history (4 cycles, 1 NEW component, 5 new persona files, registration mechanism, decision-surfacing protocol, all 6 smoke dimensions per cycle). The realistic high band is 30–45 h. Halt-trigger from dispatch: "Single cycle exceeds 5 hours wall-clock → halt with partial findings; consider further decomposition." Cycle 2 (NEW component) is the highest-risk cycle — research-grade plan-doc time required even within the sub-plan; PM-shape is unknown until designed. **Mitigation:** the sub-plan splits Cycle 2 explicitly into a design-note-first sub-step (`framework/per-project-pm/docs/design.md` lands BEFORE any source code in Cycle 2) so PM-shape contradictions surface before code is written. If Cycle 2 design contradicts M-FBM workspace-state shape, halt-and-surface per dispatcher trigger.

---

## §2. Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| 5 subagent personas (`loam-builder`, etc.) | `plugins/dev-sdlc/agents/<name>.md` (NEW directory) | Per parent §2 v0.1.7 row + Decision C (Eric synthesis): subagents are dev-flavored helpers; source in dev-sdlc plugin per partition rule. |
| Subagent registration (workspace symlink at first-run) | `framework/workspace-bootstrap/` | Workspace-bootstrap owns first-run scaffold; symlinking discovered plugin agent files into `<workspace>/.claude/agents/` is a scaffold concern. |
| Per-project PM-shape (contract, loader, registry, runtime) | `framework/per-project-pm/` (NEW component) | Per Eric synthesis §3 G5: PM-shape is harness-general, not dev-specific. A hypothetical writer's PM uses the same machinery. |
| Decision-surfacing API (PM-side question batching + single-question-per-turn) | `framework/per-project-pm/` | PM is the question owner; surfacing protocol is PM-internal. |
| Workspace-local PM state (instance) | `<workspace>/.loam/pms/<pm-name>/` | Per FIDRAFT entry: PM lives in workspace state directory. Composes with M-FBM workspace-state pattern. |
| Plugin-tier skill auto-symlinking at first-run | `framework/workspace-bootstrap/` | Workspace-bootstrap owns first-run scaffold. Symlinking `plugins/<plugin>/skills/` → `<workspace>/.claude/skills/` makes plugin skills discoverable via Anthropic-native project-skill discovery. |
| Workspace-local skill discovery + collision rules | `framework/workspace-bootstrap/` (the rules) + `<workspace>/.claude/skills/` (the surface) | Discovery rules are scaffold-level; the surface is Anthropic-native per Decision I. |
| Layered-skill design-note (3-tier, override semantics, lifecycle) | `framework/per-project-pm/docs/` for PM-side composition; `docs/design/layered-skill-architecture.md` for the architecture itself | Architecture doc is harness-general; not component-scoped. |
| One-question-at-a-time enforcement | `framework/per-project-pm/` | PM-mediated per Decision Q resolution; structural enforcement, not convention. |

---

## §3. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; subagent persona file shape)

**Decision (autonomous):** each persona file at `plugins/dev-sdlc/agents/<name>.md` follows Claude Code's documented subagent-file shape (matches `framework/primary-persona/src/loam/primary_persona/agent_md.py` `to_agent_md` precedent):

```
---
name: <handle>
description: <one-line responsibility statement; ≤ 200 chars>
model: inherit
tools: <comma-separated tool list OR omitted to inherit>
---

# Identity anchor (compaction-resilience)

I am <handle>. I serve as <role>. ...

# Persona prompt

## Identity / Role
## Voice
## When to invoke me
## How I compose with the harness
## Out of scope
```

The 5 persona handles + roles per dispatch:

| Handle | Role | tools (proposed) |
|---|---|---|
| `loam-builder` | sealed-component-cycle builder; ODD-fluent; commit-ladder + `loam amend apply` + seal-ritual fluent. | inherit (full tool surface; needs Edit/Write/Bash for code+seal-ritual) |
| `loam-plan-author` | research-grade plan authoring; surfaces named decisions with recommendations; outcome-shape ACs. | inherit (Read/Grep/Glob/WebSearch/Write — no Bash mutations) — but AUTHORS may need Bash for `git log`; defer to inherit |
| `loam-researcher` | Lens-1/2/3 research; web + codebase grep; **read-only** per dispatch. | Read, Grep, Glob, WebFetch, WebSearch (no Edit, Write, Bash) — explicitly restricted |
| `loam-reviewer` | gate-review for sealed amendments; ODD §2.5 verification; halt-and-surface fluent. | Read, Grep, Glob, Bash (read-only commands like `git log`, `git diff`) — no Edit/Write |
| `loam-documenter` | public docs / README / positioning; non-jargon voice; methodology-aware. | inherit (Edit/Write for docs; Read/Grep for source-grounding) |

### Surface #2 (no halt — recorded; subagent registration mechanism)

**Decision (autonomous):** the registration mechanism mirrors the existing `<workspace>/.claude/agents/primary.md` pattern but for plugin-shipped agents. First-run scaffold scans every plugin under `plugins/<name>/agents/*.md` and creates **symlinks** (not copies) at `<workspace>/.claude/agents/<filename>`. Symlinks (not copies) chosen so plugin updates propagate without re-bootstrap. Idempotent: existing symlinks pointing at the correct target are left untouched; existing files (non-symlinks) are NOT overwritten (operator-precedence: a workspace-authored override wins). Halt-and-surface (not silent-overwrite) when a non-symlink file collides with a plugin agent name.

This places agent registration AFTER the v0.1.6 `.claude/skills/.gitkeep` pattern (same `<workspace>/.claude/` directory pre-creation already exists).

### Surface #3 (no halt — recorded; per-project PM workspace-state shape)

**Decision (autonomous, with halt-trigger if M-FBM contradicts):** PM workspace-state at `<workspace>/.loam/pms/<pm-name>/`:

```
<workspace>/.loam/pms/<pm-name>/
  contract.yaml          # PM contract (handle, project_name, project_kind, owner, scope)
  state.yaml             # current PM-held project state (in-flight changes, ratifications pending, audit pointer)
  decision-queue.yaml    # batched questions awaiting surfacing (FIFO; one-at-a-time consumption per Decision Q)
  audit-log/             # append-only event log of surfaced questions, decisions, ratifications
    <YYYY-MM-DD>-<seq>.yaml
```

`<pm-name>` is project-slug derived (e.g., `eric-saas-pm`, `loam-self-pm`). One PM per project; PM activates when persona begins work in that project's workspace. M-FBM owns episode-level memory across all projects; PM owns project-domain decision state. **If during build the PM-state shape collides with an M-FBM convention, halt and surface per dispatcher halt-trigger.**

### Surface #4 (no halt — recorded; PM contract dataclass shape)

**Decision (autonomous):** PM contract is a Pydantic model mirroring the `PersonaContract` shape from `framework/primary-persona/`:

```python
class PMContract(BaseModel):
    handle: str                      # e.g., "eric-saas-pm"
    project_name: str                # e.g., "eric-saas"
    project_kind: Literal["dev", "writing", "research", "ops", "general"]
    owner_name: str                  # owner's preferred name (default substitution token until learned)
    workspace_root: Path             # absolute path the PM is anchored to
    decision_surfacing_policy: DecisionSurfacingPolicy  # see Surface #5
    composes_with_skills: list[str]  # plugin/base skills this PM consumes (e.g., ["dispatch-with-gates"])
    composes_with_agents: list[str]  # subagent handles this PM dispatches to (e.g., ["loam-builder"])
```

Pydantic for shape-validation (matches existing `framework/cost-governance/spec.py` + `framework/safety-layer/` pattern). Contract loaded by PM runtime; runtime owns the workspace-state read/write surface.

### Surface #5 (no halt — recorded; decision-surfacing policy + one-question-at-a-time)

**Decision (autonomous, per Decision Q resolved YES):** PM's question-batching shape:

```python
class DecisionSurfacingPolicy(BaseModel):
    onboarding_mode: bool = False             # when True, hard one-question-per-turn enforcement
    max_questions_per_turn: int = 1           # default 1; tunable post-onboarding
    cool_down_seconds: int = 0                # rate-limiting between surfacings (0 = none)
    require_owner_response: bool = True       # PM blocks on owner ratification at production-stake mode
```

PM's `surface_next_question()` API (the persona invokes when about to address owner):
- consumes the FIFO `decision-queue.yaml`,
- emits exactly ONE question (count gated by `max_questions_per_turn`),
- writes to `audit-log/` with provenance,
- returns the question text + provenance for persona-side relay.

Onboarding-mode test: "user is asked exactly one question per turn during onboarding" — the test dispatches N PM-enqueued questions, verifies exactly 1 is surfaced per `surface_next_question()` call, verifies the queue advances by exactly 1, verifies the audit log records the surfacing.

### Surface #6 (no halt — recorded; layered-skill discovery + plugin auto-symlinking)

**Decision (autonomous, per Decision I + Anthropic SKILL.md verified-2026-05-04):** workspace-bootstrap's first-run scaffold scans every plugin under `plugins/<name>/skills/*/SKILL.md` and creates symlinks at `<workspace>/.claude/skills/<name>/` (skill-directory granularity, not file granularity — Anthropic discovery walks per-directory). Same idempotence rules as Cycle 1 agents: symlinks pointing at the correct target are left untouched; non-symlink directories are NOT overwritten (operator-precedence). Collision (workspace-local skill name shadows a plugin skill name) → **halt-and-surface** at scaffold time per dispatcher's halt-trigger; the operator can either rename the workspace-local skill or accept shadowing explicitly.

Decision tier (per layered-skills research §2.2 + Anthropic precedence rules):
1. **Workspace-local** (operator-authored at `<workspace>/.claude/skills/<name>/SKILL.md`) — overrides plugin (Anthropic-native; operator wins).
2. **Plugin-tier** (auto-symlinked from `plugins/<plugin>/skills/<name>/`) — visible via plugin-namespace `<plugin>:<skill>` invocation; shadowable by workspace-local.
3. **Base-tier** (`plugins/loam-skills/skills/<name>/`) — same shape as plugin-tier; shadowable.

Smoke fixture (per dispatch AC.LAYERED): create `<workspace>/.claude/skills/test-discovery/SKILL.md` in a fresh canonical workspace; verify it appears in `/` menu without restart. **HALT-AND-SURFACE if the Anthropic-native discovery does NOT pick up the file as expected** — per dispatch halt-trigger and §9.3 honest-doubt in the layered-skills research.

### Surface #7 (no halt — recorded; per-project PM as a NEW component)

**Decision (autonomous):** `framework/per-project-pm/` is a NEW component shape (the second post-amendment-#125 NEW component; first was `plugins/loam-skills/`). It follows the existing-component-shape conventions:
- `pyproject.toml` with `loam.bootstrap.contributions` entry-point declaring `PerProjectPMContribution`.
- `src/loam/per_project_pm/` package with: `contract.py`, `runtime.py`, `loader.py`, `surfacing.py`, `errors.py`, `contribution.py`.
- `tests/test_no_sealed_amendments.py` seal-test (BASELINE-aware diff).
- `tests/SEAL_COMMIT` sidecar.
- `docs/design.md` design-note articulating PM/M-FBM boundary.
- `README.md` orienting to the component.

Cycle 2 is split into two sub-steps (per F2 RF + Cycle 2 risk):
1. **Cycle 2.a** — design-note + scaffold + contract.py (no runtime). Land FIRST as part of Cycle 2 BASELINE source-edit commit; design-note is the gate before runtime is authored.
2. **Cycle 2.b** — runtime + loader + integration tests. Lands as the Cycle 2 source-edit commit's runtime portion (still single seal, single manifest).

If Cycle 2.a's design-note surfaces a contradiction with M-FBM workspace-state, halt-and-surface BEFORE Cycle 2.b begins.

### Surface #8 (no halt — recorded; serialization between cycles)

**Decision (autonomous):** Cycles seal sequentially. Cycle 1 + Cycle 3 both touch `framework/workspace-bootstrap/`; per `feedback_serialize_amendment_builds`, Cycle 3 starts STRICTLY AFTER Cycle 1's seal lands. Cycle 2 (per-project-pm NEW component) does not touch workspace-bootstrap; could in principle parallel Cycle 1, but per dispatcher's serial-cycle directive, all four are serialized.

Total: 4 apply commits + 4 seal commits + 4 manifest commits + per-cycle source-edit BASELINE commits (≥ 4) + plan-doc commit (this) = ~13–17 commits across the four cycles.

### Surface #9 (no halt — recorded; out-of-scope items)

**Decision (autonomous, per dispatch out-of-scope):** the following are explicitly OUT of v0.1.7:

- **Auto-creation mechanism.** Per dispatch + parent §2 v0.2.0 row. Workspace-local skill discovery LANDS in v0.1.7 (mechanism), but the persona-driven SKILL-capture workflow lands in v0.2.0.
- **Promotion rubric mechanism.** Per dispatch + parent §2 v0.2.1 row.
- **Heavy reverse-engineering / Rails extractor.** Per dispatch + parent §2 v0.1.8 row.
- **12 dev-sdlc skill-ifications.** Per dispatch + parent §2 v0.1.8 + v0.1.9 rows.
- **Real Eric onboarding ritual.** Per dispatch + parent §2 v0.2.1 row.
- **PM ratification queue mechanics + domain-batched AC surfacing.** Per parent §2 v0.2.0 row.

### Surface #10 (no halt — recorded; layered-skill architecture design-note)

**Decision (autonomous, per parent §2 v0.1.7 row):** the design-note `docs/design/layered-skill-architecture.md` is authored as part of Cycle 3's source edits (not a separate cycle). Doc-only; no code. The 3-layer model + override semantics + lifecycle (per layered-skills research §2) are the body. Universal-admitted path; lands inside Cycle 3's fence.

### Surface #11 (no halt — recorded; tools restriction in researcher persona)

**Decision (autonomous):** per Surface #1, `loam-researcher` persona's frontmatter declares `tools: Read, Grep, Glob, WebFetch, WebSearch` (read-only restriction enforced by Claude Code's subagent tool-restriction surface). This is the dispatch-explicit "tools restricted to read-only." Verified against Claude Code docs: subagent files support `tools: <list>` frontmatter to restrict the tool surface. Test: a `loam-researcher` invocation that attempts `Edit`/`Write`/`Bash` is structurally refused by Claude Code.

### Surface #12 (no halt — recorded; PM does NOT own workspace-local skills)

**Decision (autonomous, per Decision I + dispatcher Bundle 2 description):** Bundle 2 description says "MemoryOwner of project-scoped state". This is interpreted as: PM owns project-domain DECISION + RATIFICATION state (the queue + audit-log), NOT episode-memory (M-FBM owns that) and NOT workspace-local skills (Anthropic-native at `<workspace>/.claude/skills/` per Decision I). The phrase "MemoryOwner" is borrowed terminology; the PM's owner-surface is structured as the workspace-state directory + the `surface_next_question()` API. The tests assert this boundary: PM does not write to M-FBM episode store; PM does not write to `<workspace>/.claude/skills/`.

---

## §4. Spec-objective placement

**Binds to:**

- **AC.PO.1 + AC.PO.2** (prime objective per VALUE_PROPOSITION.md) — subagent personas reduce translation burden (persona dispatches by handle, not by re-deriving methodology); PM absorbs project-domain coordination off persona's user-visible surface (translation-shape returns); layered-skill discovery makes workspace-local skills automatic so the toolkit grows organically.
- **Eric-final-delivery §2 v0.1.7** — coordination machinery off persona's user-visible surface; PM ships; layered-skill mechanism lands.
- **Layered-skills research §1.4 + §2** — workspace-local skill discovery via Anthropic-native primitive; 3-tier architecture (base / plugin / workspace-local); plugin-skill auto-symlinking is the harness-general primitive.
- **Eric synthesis Decision Q (RESOLVED YES)** — one-question-at-a-time PM-enforced; Cycle 4.
- **Eric synthesis Decision I (RESOLVED YES)** — workspace-local skills under Anthropic-native `<workspace>/.claude/skills/`.

**Ladders to:** AC.PERSONAS.* + AC.PPM.* + AC.LAYERED.* + AC.QSURF.* → v0.1.7 → v0.1.8+ (every later release composes against subagent dispatch + PM coordination + workspace-local skill discovery) → AC.PO.

---

## §5. Acceptance criteria

### AC.PERSONAS.* family — 5 subagent personas + registration

- **AC.PERSONAS.1 — `loam-builder` persona file present + frontmatter valid.** File at `plugins/dev-sdlc/agents/loam-builder.md` exists; YAML frontmatter parses; carries `name: loam-builder`, `description` (≤ 200 chars), `model: inherit`. Body has the 5-section shape (Identity anchor / Role / Voice / When to invoke me / How I compose with the harness / Out of scope). Body explicitly references `loam amend apply`, `loam amend seal`, ODD §2.5, plan-before-code rule.
- **AC.PERSONAS.2 — `loam-plan-author` persona file present + frontmatter valid.** Same shape; body references plan-doc shape + named-decisions-with-recommendations + outcome-shape ACs.
- **AC.PERSONAS.3 — `loam-researcher` persona file present + frontmatter valid + tools restricted to read-only.** Same shape; frontmatter `tools: Read, Grep, Glob, WebFetch, WebSearch`; body references Lens 1/2/3 research; halt-and-surface fluent.
- **AC.PERSONAS.4 — `loam-reviewer` persona file present + frontmatter valid + tools limited.** Same shape; frontmatter `tools` excludes Edit/Write but permits read-only Bash; body references gate-review for sealed amendments + ODD §2.5 verification.
- **AC.PERSONAS.5 — `loam-documenter` persona file present + frontmatter valid.** Same shape; body references public-docs voice (non-jargon) + methodology-awareness.
- **AC.PERSONAS.6 — symlink registration into `<workspace>/.claude/agents/` works at first-run.** Tests run `run_first_run_scaffold` against a tmpfs workspace; assert `<workspace>/.claude/agents/loam-builder.md` (and the other 4) exist as symlinks pointing at `plugins/dev-sdlc/agents/<name>.md`. Idempotent (second run does not duplicate or overwrite).
- **AC.PERSONAS.7 — collision-handling on existing non-symlink file.** Tests pre-create `<workspace>/.claude/agents/loam-builder.md` as a regular file; first-run scaffold detects the collision and halts-and-surfaces (does NOT overwrite). Operator-precedence preserved.
- **AC.PERSONAS.8 — discovery in canonical pos-v2 (smoke).** Status-file recorded smoke (live `claude` session in canonical pos-v2 lists all 5 personas via the subagent-discovery surface).

### AC.PPM.* family — per-project PM (Cycle 2)

- **AC.PPM.1 — component scaffold present.** `framework/per-project-pm/` exists with `pyproject.toml` (declares `loam.bootstrap.contributions` entry-point `per_project_pm = "loam.per_project_pm.contribution:PerProjectPMContribution"`), `src/loam/per_project_pm/` package, `tests/test_no_sealed_amendments.py` seal-test, `tests/SEAL_COMMIT` sidecar, `README.md`, `docs/design.md`.
- **AC.PPM.2 — `PMContract` Pydantic model present + validates.** `from loam.per_project_pm.contract import PMContract` resolves; contract carries the 7 fields per Surface #4; pydantic validation rejects malformed contracts (empty handle, invalid project_kind, non-absolute workspace_root).
- **AC.PPM.3 — `DecisionSurfacingPolicy` Pydantic model present + defaults correct.** Default `max_questions_per_turn = 1`; default `onboarding_mode = False`; default `require_owner_response = True`. Validation rejects `max_questions_per_turn < 1`.
- **AC.PPM.4 — `PMRuntime` loader resolves workspace-state.** `PMRuntime.from_workspace(workspace_root, pm_name)` reads `<workspace>/.loam/pms/<pm-name>/contract.yaml` + `state.yaml` + `decision-queue.yaml`. Returns hydrated runtime. Raises `PMNotFoundError` (named exception in `errors.py`) when `contract.yaml` absent. Raises `PMStateCorruptedError` on schema mismatch.
- **AC.PPM.5 — `surface_next_question()` API.** Method on `PMRuntime`. Consumes head of FIFO queue; returns `SurfacedQuestion` (text + provenance + queue_position); writes to `audit-log/<YYYY-MM-DD>-<seq>.yaml` with timestamp + question + queue-state-pre + queue-state-post. Returns `None` when queue empty (not exception — empty is normal).
- **AC.PPM.6 — `enqueue_decision()` API.** Method on `PMRuntime`. Appends to FIFO queue; returns enqueued position. Persists to `decision-queue.yaml` synchronously (no in-memory drift).
- **AC.PPM.7 — PM does NOT write to M-FBM episode store.** Test asserts: a full PM lifecycle (load → enqueue → surface) produces zero writes to `<workspace>/.loam/memory/` (M-FBM workspace-state path) and zero writes to `<workspace>/.claude/skills/`. Per Surface #12 boundary.
- **AC.PPM.8 — `PerProjectPMContribution` registers correctly.** Contribution metadata: `name="per_project_pm"`, `phase=after_orchestrator_ready`, `after=("primary_persona",)`. Test asserts entry-point discovery + host attribute publication (`host.per_project_pm`).
- **AC.PPM.9 — design-note articulates PM/M-FBM boundary.** `framework/per-project-pm/docs/design.md` exists; body explicitly names: PM owns project-domain decision state; M-FBM owns episode memory; workspace-local skills are Anthropic-native; PM references but does not own.

### AC.LAYERED.* family — layered-skill discovery mechanism (Cycle 3)

- **AC.LAYERED.1 — workspace-local skill discoverable via Anthropic-native discovery (smoke).** Status-file recorded smoke: create `<workspace>/.claude/skills/test-discovery/SKILL.md` in a fresh canonical workspace clone; verify it appears in the `/` menu / persona's Skill-tool surface without Claude Code restart. **Halt-and-surface if discovery fails** — per layered-skills §9.3 honest doubt.
- **AC.LAYERED.2 — plugin skills auto-symlinked at first-run.** Tests run `run_first_run_scaffold` against a tmpfs workspace; assert `<workspace>/.claude/skills/translation-discipline/SKILL.md` (and the other 7 — all 8 from v0.1.6 Cycle 2) exist as symlinks pointing at `plugins/loam-skills/skills/<name>/SKILL.md`. Idempotent (second run does not duplicate).
- **AC.LAYERED.3 — collision-handling on workspace-local skill shadowing plugin skill.** Tests pre-create `<workspace>/.claude/skills/translation-discipline/SKILL.md` (operator-authored override); first-run scaffold detects the collision and halts-and-surfaces (does NOT overwrite). Operator-precedence preserved.
- **AC.LAYERED.4 — collision-handling on TWO plugins shipping the same skill name.** Tests construct two plugins each with `<plugin>/skills/foo/SKILL.md`; first-run scaffold detects the cross-plugin collision and halts-and-surfaces. (Defensive — unlikely today; future-proofing.)
- **AC.LAYERED.5 — design-note `docs/design/layered-skill-architecture.md` present.** File articulates the 3-tier model (base / plugin / workspace-local); override semantics; lifecycle; the auto-symlinking mechanism + collision rules; references Anthropic SKILL.md spec.
- **AC.LAYERED.6 — discovery in canonical pos-v2 (smoke).** Status-file recorded smoke: live `claude` session in canonical pos-v2 lists ALL plugin skills (8 base + dev-sdlc plugin's start-project) via the workspace-local `.claude/skills/` surface (not just the plugin-namespace surface). Confirms auto-symlinking is functional end-to-end.

### AC.QSURF.* family — decision-surfacing + one-question-at-a-time (Cycle 4)

- **AC.QSURF.1 — onboarding-mode flag toggles `max_questions_per_turn` enforcement.** Test: PM with `onboarding_mode = True` + `max_questions_per_turn = 1` (default); enqueue 5 questions; call `surface_next_question()` 5 times across 5 separate turns; assert exactly 5 surfacings, 1 per call, queue advances by 1 per call, audit log records 5 entries.
- **AC.QSURF.2 — non-onboarding-mode permits batched surfacing per `max_questions_per_turn`.** Test: PM with `onboarding_mode = False` + `max_questions_per_turn = 3`; enqueue 5 questions; call `surface_next_questions_batch()` (Cycle 4 extension API); assert 3 surfaced in batch, 2 remain queued.
- **AC.QSURF.3 — onboarding-mode hard test (per dispatch wording).** Test fixture simulates onboarding turn: enqueue 3 questions; PM in onboarding-mode; persona-side caller invokes `surface_next_question()` exactly once per turn; after 3 turns, all 3 surfaced; per turn N=1..3, EXACTLY 1 question surfaced (assertion: `len(surfaced_in_turn_N) == 1`).
- **AC.QSURF.4 — `audit-log/` records each surfacing with provenance.** Per surfaced question, audit-log entry carries: timestamp (ISO 8601), question text, queue-position-pre, queue-position-post, surfaced_at_turn (operator-supplied or auto-computed), pm_handle. Schema validated.
- **AC.QSURF.5 — `require_owner_response` blocks subsequent surfacings until prior question is responded.** Test: PM with `require_owner_response = True`; enqueue Q1, Q2; surface Q1; attempt to surface Q2 BEFORE Q1's response is recorded; assert `PendingResponseError` raised. Record Q1's response via `record_response(question_id, response)` API; surface Q2 succeeds.
- **AC.QSURF.6 — `record_response()` API.** Method on `PMRuntime`. Records owner response in audit-log + clears the "blocking" flag for `require_owner_response`. Idempotent on duplicate response (same question_id).
- **AC.QSURF.7 — PM-mediated dispatches log per audit-trail floor (per dispatch D6 + v0.1.6 production-stake).** Test: under production-stake mode, every PM-mediated decision-surfacing produces an audit-log entry. Composes with v0.1.6 SOC-2 floor.

### AC.V0.1.7.S — fence (per-cycle, multi/single-component as named)

- **Cycle 1 fence:** `plugins/dev-sdlc/agents/` (NEW directory under existing component) + `framework/workspace-bootstrap/`, plus `docs/plans/` (universal admission for sub-plan + manifest), plus `CLAUDE.md` if updated.
- **Cycle 2 fence:** `framework/per-project-pm/` (NEW component) only, plus `docs/plans/` for cycle-2 manifest. Plus per-amendment-22 ruling: NEW component lands a SEAL_COMMIT sidecar + `tests/test_no_sealed_amendments.py` seal-test as part of the same amendment cycle.
- **Cycle 3 fence:** `framework/workspace-bootstrap/` (extends Cycle 1) + `docs/design/layered-skill-architecture.md` (universal-admitted) + `docs/plans/` for cycle-3 manifest.
- **Cycle 4 fence:** `framework/per-project-pm/` (extends Cycle 2) + `docs/plans/` for cycle-4 manifest.

---

## §6. Build steps

### Cycle 1 (5 subagent personas + symlink registration) — multi-component fence

1. **Plan-doc** lands (this file + manifest).
2. **Manifest** authored: `docs/plans/v0-1-7-personas-pm-layered-skills-cycle1.manifest.yaml` — multi-component fence (`plugins/dev-sdlc` + `framework/workspace-bootstrap`).
3. **Source edits** (in order):
   - `plugins/dev-sdlc/agents/loam-builder.md` (NEW) — 5-section persona body.
   - `plugins/dev-sdlc/agents/loam-plan-author.md` (NEW).
   - `plugins/dev-sdlc/agents/loam-researcher.md` (NEW; tools-restricted frontmatter).
   - `plugins/dev-sdlc/agents/loam-reviewer.md` (NEW).
   - `plugins/dev-sdlc/agents/loam-documenter.md` (NEW).
   - `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` — extend with `_symlink_plugin_agents(workspace_root)` helper; collision-handling rules (halt + surface on non-symlink collision); idempotence.
4. **Tests** authored:
   - `plugins/dev-sdlc/tests/test_AC_PERSONAS_{1..5}_persona_files.py` — frontmatter parse, body shape, named references.
   - `framework/workspace-bootstrap/tests/test_AC_PERSONAS_6_symlink_registration.py`.
   - `framework/workspace-bootstrap/tests/test_AC_PERSONAS_7_collision_halt.py`.
5. **Touched-tests run** (only the new tests + `plugins/dev-sdlc/tests/` + `framework/workspace-bootstrap/tests/`).
6. **`loam amend apply`** — auto-commit lands (NOT `--amend`).
7. **`loam amend seal`** — deterministic seal commit.
8. **Smoke (D1 cold-state):** fresh workspace → 5 personas symlinked + discoverable via `claude`'s subagent surface.

### Cycle 2 (per-project PM — NEW component) — single-component fence

1. **Manifest** authored: `docs/plans/v0-1-7-personas-pm-layered-skills-cycle2.manifest.yaml` — single-component fence on `framework/per-project-pm/` (NEW).

2. **Source edits — Cycle 2.a (design-note + scaffold; halt before runtime if contradicts M-FBM):**
   - `framework/per-project-pm/pyproject.toml` (NEW).
   - `framework/per-project-pm/README.md` (NEW).
   - `framework/per-project-pm/docs/design.md` (NEW) — articulates PM/M-FBM boundary; review for contradiction with M-FBM workspace-state pattern; halt-and-surface if collision.
   - `framework/per-project-pm/src/loam/per_project_pm/__init__.py` (NEW).
   - `framework/per-project-pm/src/loam/per_project_pm/errors.py` (NEW) — `PMNotFoundError`, `PMStateCorruptedError`, `PendingResponseError`.
   - `framework/per-project-pm/src/loam/per_project_pm/contract.py` (NEW) — `PMContract`, `DecisionSurfacingPolicy` Pydantic models.

3. **Source edits — Cycle 2.b (runtime + integration):**
   - `framework/per-project-pm/src/loam/per_project_pm/loader.py` (NEW) — workspace-state load.
   - `framework/per-project-pm/src/loam/per_project_pm/runtime.py` (NEW) — `PMRuntime` with `enqueue_decision`, `surface_next_question` (basic Cycle 2 form), state persistence.
   - `framework/per-project-pm/src/loam/per_project_pm/contribution.py` (NEW) — `PerProjectPMContribution`.
   - `framework/per-project-pm/tests/test_no_sealed_amendments.py` (NEW) — BASELINE-aware seal-test.
   - `framework/per-project-pm/tests/SEAL_COMMIT` (NEW sidecar; written at apply time per loam-amend convention).

4. **Tests** authored:
   - `framework/per-project-pm/tests/test_AC_PPM_1_scaffold_present.py`.
   - `framework/per-project-pm/tests/test_AC_PPM_2_PMContract_validates.py`.
   - `framework/per-project-pm/tests/test_AC_PPM_3_DecisionSurfacingPolicy.py`.
   - `framework/per-project-pm/tests/test_AC_PPM_4_runtime_loader.py`.
   - `framework/per-project-pm/tests/test_AC_PPM_5_surface_next_question.py`.
   - `framework/per-project-pm/tests/test_AC_PPM_6_enqueue_decision.py`.
   - `framework/per-project-pm/tests/test_AC_PPM_7_boundary_no_mfbm_writes.py`.
   - `framework/per-project-pm/tests/test_AC_PPM_8_contribution_registers.py`.
   - `framework/per-project-pm/tests/test_AC_PPM_9_design_note_present.py`.

5. **Touched-tests run** (`framework/per-project-pm/tests/`).
6. **`loam amend apply`** — auto-commit lands.
7. **`loam amend seal`** — deterministic seal commit.
8. **Smoke (D1 cold-state):** fresh workspace → PM scaffold loads via entry-point; `host.per_project_pm` published.

### Cycle 3 (layered-skill discovery mechanism) — single-component fence

1. **Manifest** authored: `docs/plans/v0-1-7-personas-pm-layered-skills-cycle3.manifest.yaml` — single-component fence on `framework/workspace-bootstrap/`.

2. **Source edits**:
   - `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` — extend with `_symlink_plugin_skills(workspace_root)` helper; mirror agent-symlinking pattern; collision-handling rules.
   - `docs/design/layered-skill-architecture.md` (NEW) — 3-tier architecture, override semantics, lifecycle, auto-symlinking mechanism, references Anthropic SKILL.md spec.

3. **Tests** authored:
   - `framework/workspace-bootstrap/tests/test_AC_LAYERED_2_plugin_skill_symlinks.py`.
   - `framework/workspace-bootstrap/tests/test_AC_LAYERED_3_workspace_local_collision.py`.
   - `framework/workspace-bootstrap/tests/test_AC_LAYERED_4_cross_plugin_collision.py`.
   - `framework/workspace-bootstrap/tests/test_AC_LAYERED_5_design_note_present.py`.

4. **Touched-tests run** (`framework/workspace-bootstrap/tests/`).
5. **`loam amend apply`** — auto-commit lands.
6. **`loam amend seal`** — deterministic seal commit.
7. **Smoke (AC.LAYERED.1 + AC.LAYERED.6):** fresh canonical pos-v2 workspace → drop `<workspace>/.claude/skills/test-discovery/SKILL.md`; verify discovery without restart. ALL 8+1 plugin skills visible via workspace-local discovery.
   **Halt-and-surface trigger:** if Anthropic-native discovery does NOT pick up the workspace-local SKILL — per dispatch + §9.3 honest doubt.

### Cycle 4 (decision-surfacing + one-question-at-a-time) — single-component fence

1. **Manifest** authored: `docs/plans/v0-1-7-personas-pm-layered-skills-cycle4.manifest.yaml` — single-component fence on `framework/per-project-pm/` (extends Cycle 2 component).

2. **Source edits**:
   - `framework/per-project-pm/src/loam/per_project_pm/surfacing.py` (NEW) — extends Cycle 2 runtime with question-batching + `surface_next_questions_batch()` + `record_response()` + `require_owner_response` blocking.
   - `framework/per-project-pm/src/loam/per_project_pm/runtime.py` (extend) — wires surfacing API into runtime.
   - `framework/per-project-pm/docs/design.md` (extend) — append §3 onboarding-mode protocol.

3. **Tests** authored:
   - `framework/per-project-pm/tests/test_AC_QSURF_1_onboarding_mode_one_question.py`.
   - `framework/per-project-pm/tests/test_AC_QSURF_2_batched_surfacing.py`.
   - `framework/per-project-pm/tests/test_AC_QSURF_3_onboarding_hard_test.py`.
   - `framework/per-project-pm/tests/test_AC_QSURF_4_audit_log_provenance.py`.
   - `framework/per-project-pm/tests/test_AC_QSURF_5_require_owner_response_blocks.py`.
   - `framework/per-project-pm/tests/test_AC_QSURF_6_record_response.py`.
   - `framework/per-project-pm/tests/test_AC_QSURF_7_audit_trail_floor.py`.

4. **Touched-tests run** (`framework/per-project-pm/tests/`).
5. **`loam amend apply`** — auto-commit lands.
6. **`loam amend seal`** — deterministic seal commit.

### Smoke (REALISTIC CONDITION — all 6 dimensions per `plugins/dev-sdlc/docs/smoke-test-discipline.md`)

After all four cycles seal:

- **D1 cold-state:** fresh workspace → 5 personas + per-project PM + workspace-local skill discovery functional from session-zero.
- **D2 steady-state:** PM holds project state across 5 dispatches; no skill discovery regression; no persona-file drift.
- **D3 restart:** PM state preserved across pos-v2 process restart; persona files survive (symlinks point at correct target post-restart).
- **D4 reboot:** PM state + persona files + skill symlinks survive simulated equivalent (`launchctl bootout` + `bootstrap` cycle).
- **D5 cross-session:** PM state visible across `/clear`; one-question-at-a-time enforcement persists. (THE ship-test per STATE.md.)
- **D6 telemetry-floor:** PM-mediated dispatches log per audit-trail floor from v0.1.6 production-stake mode.

All 6 outcomes status-file-recorded.

---

## §7. Out of scope (deferred)

- **Auto-creation mechanism** — defer to v0.2.0 (per dispatch + parent §2 v0.2.0 row).
- **Promotion rubric** — defer to v0.2.1 (per dispatch + parent §2 v0.2.1 row).
- **Heavy reverse-engineering / Rails extractor** — defer to v0.1.8.
- **12 dev-sdlc skill-ifications** — defer to v0.1.8 + v0.1.9.
- **Real Eric onboarding ritual** — defer to v0.2.1.
- **PM ratification queue mechanics + domain-batched AC surfacing** — defer to v0.2.0 (per parent §2 v0.2.0 row).
- **Auto-creation of skills by PM** (Decision H) — primary persona for now; revisit at v0.2.0.
- **Workspace-local skill auto-prefix convention** (Decision K) — convention-suggested; structural-enforce only at v0.2.x if collisions observed.
- **Migration of `framework/primary-persona/skills/memory-{search,archive}.md` flat-shape** — out of fence; v0.2+.
- **`plugins/loam-skills/` admission to `dev-mode-manifest.yaml`** — per parent §2 v0.1.7 row this WAS slated for Cycle 3, but per Surface #9 + dispatch out-of-scope (this dispatch's bundles do NOT include dev-mode-manifest edits), DEFER to a follow-on amendment unless surfaced as in-scope by Luke. The layered-skill discovery mechanism (auto-symlinking) makes this admission less load-bearing — workspace-local discovery is the primary surface.

---

## §8. Halt triggers (in-flight)

- WD drifts → halt + surface.
- Plan-doc not authored before code → halt.
- Any AC ships partial → halt + reframe.
- Per-project PM design (Cycle 2.a) surfaces a contradiction with M-FBM workspace-state → halt + surface (PM owns project decision state; M-FBM owns episode memory; if they collide, surface for ruling).
- Anthropic SKILL.md mechanism does NOT actually support workspace-local discovery as expected → halt + surface (per layered-skills §9.3 honest doubt; AC.LAYERED.1 verifies).
- More than 5 in-build decisions need Luke escalation → halt + describe.
- Single cycle exceeds 5 hours wall-clock → halt with partial findings; consider further decomposition.
- 6-dimension smoke fails on D5 cross-session → halt (THE ship-test per STATE.md).
- Cycle 1 seal fails → halt; do NOT start Cycle 2 (per `feedback_serialize_amendment_builds`).
- Cycle N seal fails → halt; do NOT start Cycle N+1.
- Persona file frontmatter fails Claude-Code-discovery validation → halt.

---

## §9. Bookkeeping

- `loam amend apply` per cycle (NOT `git commit --amend`; create NEW corrective commits if a file is missed).
- Single semantic commit message per cycle.
- Backfill `docs/plans/v0-1-x-roadmap.md` §8 method-decision register row for v0.1.7.
- Backfill `docs/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.1.7 table with apply + seal SHAs (per-cycle).
- Update `docs/STATE.md` v0.1.7 row.
- DO NOT push tags until Luke gates the release (per dispatcher).

---

## §10. F2 Ruthless Feedback (additional gaps named this turn)

Beyond the scope-realism F2 in §1:

- **PM/M-FBM boundary is the largest design risk.** Cycle 2.a's design-note is the structural defense. If the design surfaces an unforeseen contradiction (e.g., PM's `audit-log/` collides with M-FBM's episode shape), Cycle 2 halts before runtime is authored. This is named explicitly so the halt-trigger is structural, not optional.
- **Subagent persona handles overlap with primary-persona naming.** Primary persona is `primary` at `<workspace>/.claude/agents/primary.md`. The 5 new persona handles are `loam-builder`, etc. — namespaced by `loam-` prefix so collision is structurally impossible. Confirmed: `loam-` prefix is reserved for plugin-shipped subagents (convention; not enforced today, but documented in the design-note).
- **Tools restriction on `loam-researcher` / `loam-reviewer` is verified against Anthropic's subagent-file documented surface.** The dispatch wording "tools restricted to read-only" is structurally implementable. If Claude Code's tools-restriction mechanism is partial or unreliable, the persona body's first paragraph is the secondary defense (persona explicitly states "I am read-only; I do not Edit/Write/Bash"). Belt + suspenders.
- **Symlinks vs copies trade-off.** Symlinks were chosen so plugin updates propagate without re-bootstrap. If the operator's environment doesn't support symlinks (Windows native, some Docker configs), the scaffold halts-and-surfaces with a named diagnostic. macOS (canonical loam target per `framework/workspace-bootstrap/adapters/first_run_scaffold.py:48`) supports symlinks natively.
- **One-question-at-a-time may slow non-onboarding interactions if `max_questions_per_turn = 1` is the post-onboarding default.** Cycle 4's policy default is `onboarding_mode = False` (so post-onboarding `max_questions_per_turn` is operator-tunable, default 1 with explicit "increase to N for batch ratification" knob). The Cycle 4 design-note appendix names this. The friction-versus-discipline trade-off is operator's call; Cycle 4 doesn't pre-judge.
- **The dispatcher description says "MemoryOwner of project-scoped state".** Per Surface #12, this is interpreted as decision/ratification state, NOT episode memory. If Luke's intent was "PM IS the memory layer for project state, replacing M-FBM workspace-scoping", that's a much larger design contradiction and would invalidate Cycle 2 + force a re-plan. The Cycle 2.a design-note states the boundary explicitly so a contradiction-with-Luke's-intent surfaces for halt-and-surface BEFORE runtime is authored.

---

## §11. Provenance trail

- **Eric final delivery plan §2 v0.1.7 row** — parent plan; coordination machinery off persona surface; PM ships; layered-skill mechanism lands.
- **Eric synthesis Decision Q** (RESOLVED YES) — one-question-at-a-time PM-enforced; Cycle 4 implements structurally.
- **Eric synthesis Decision I** (RESOLVED YES) — workspace-local skills under Anthropic-native location.
- **Eric synthesis Decision C** (RESOLVED) — subagents source in `plugins/dev-sdlc/agents/`; symlink at workspace-bootstrap to `<workspace>/.claude/agents/`.
- **Layered-skills research §1.4** — Anthropic SKILL.md verified-2026-05-04; live change detection; `<workspace>/.claude/skills/<name>/SKILL.md` discovery.
- **Layered-skills research §2** — 3-tier architecture, override semantics, lifecycle.
- **Layered-skills research §6.1 + §6.3** — connection to per-project PM; PM references but doesn't own workspace-local skills.
- **Layered-skills research §9.3** — honest doubt on workspace-local discovery; smoke is the verification gate.
- **`framework/primary-persona/src/loam/primary_persona/agent_md.py:15`** — existing subagent-file projection precedent for Surface #1 shape.
- **`framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:777,999`** — v0.1.6 `.claude/skills/.gitkeep` pre-create + `_write_skills_gitkeep` precedent for the symlink mechanism.
- **`plugins/dev-sdlc/src/loam/plugins/dev_sdlc/contribution.py`** — plugin contribution shape precedent for `PerProjectPMContribution`.
- **FIDRAFT entry on per-project PM** (`docs/FUTURE_IDEAS_DRAFT.md` lines on PM) — the durable capture this builds against.
- **Anthropic SKILL.md spec** (https://code.claude.com/docs/en/skills) — fetched 2026-05-04 per layered-skills §1.4.
- **Anthropic subagent-file spec** (https://docs.claude.com/en/docs/claude-code/sub-agents) — frontmatter shape (`name`, `description`, `model`, `tools`).

---

*End of v0.1.7 sub-plan-doc. AI-time band 22–34 h per parent synthesis (with quality-bar absorption). 4 cycles, serialized.*
