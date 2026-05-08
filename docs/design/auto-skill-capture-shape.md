# Auto-skill-capture shape

**Status:** authored 2026-05-04 as part of v0.2.0 Cycle 2.

**Audience:** loam contributors and harness operators who need to
understand how the persona-driven skill-capture mechanism works,
why it ships in three triggers (not six), and where it goes next.

**References:**
- `plugins/loam-skills/skills/skill-capture-proposal/SKILL.md` — the
  SKILL package that codifies the persona's auto-capture workflow.
- `docs/plans/v0-2-0-cycle-2-auto-skill-creation.md` — the
  sub-plan that ships this design note + the SKILL + the manifest
  flag.
- `docs/plans/v0-2-0-master-plan.md` — the master plan
  (committed `7c0f87b`) that locks the cycle's scope.
- `docs/plans/layered-skill-story-research-2026-05-04.md`
  — the research pass that grounds this design (especially §3 on
  auto-creation + §3.6 on universal-tier framing).
- `docs/design/layered-skill-architecture.md` — the three-layer
  architecture this mechanism plugs into (workspace-local SKILLs
  are the materialization target).
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py`
  — the `enable_auto_skill_capture` workspace-config flag.
- `framework/per-project-pm/src/loam/per_project_pm/runtime.py` —
  the PM batch API the ratification gate composes on.

---

## §1 — Architecture

### 1.1 — Universal-tier scope

The auto-skill-capture mechanism is **universal across loam
workflows** — any user benefits, dev or non-dev. Per layered-skill
research §3.6 + Luke's 2026-05-04 universal-scope clarification
(messages 9951 + 9953):

- **Auto-creation as a primitive** is harness-general. The persona's
  bidirectional translation extends to "this pattern recurs; make
  it explicit and invokable." Not dev-specific.
- **Especially valuable for non-dev users.** Writers capturing
  reusable rhetorical structures; researchers capturing
  methodology checklists; ops people capturing runbooks. These
  patterns rarely fit dev-tooling shapes; without auto-capture
  they stay tacit.
- **The mechanism lives in `framework/`** (every loam user
  benefits): the `enable_auto_skill_capture` config flag in
  `framework/workspace-bootstrap/`; the layered-skill discovery
  in `framework/` (per v0.1.7 Cycle 3 `bcf699a`).
- **The SKILL itself is base-loam** (`plugins/loam-skills/skills/
  skill-capture-proposal/SKILL.md`) — it ships with the loam-
  skills plugin every workspace gets.
- **The promotion rubric is dev-scoped** (deferred to v0.2.1 in
  `plugins/dev-sdlc/skills/skill-promotion-review/`) — only
  loam-devs and plugin-devs need to graduate workspace-local
  SKILLs upward.

### 1.2 — User-ratifies, never silent

Silent skill-write is a known anti-pattern (per layered-skill
research §3.1). A persona that auto-creates SKILLs every time the
user does something twice will bloat workspace-local skills until
the discovery surface becomes noisy and Claude's auto-load
misfires.

The structural defence is the **user-ratification gate via PM
batch API**:

1. Persona detects a trigger pattern.
2. Persona drafts SKILL.md to `<workspace>/.scratch/claude-output/skill-draft-<slug>.md` (NOT yet `.claude/skills/`).
3. Persona surfaces a one-line decision-question via
   `PMRuntime.enqueue_decision` + `surface_next_questions_batch(n=1)`
   (one-question-at-a-time per Decision Q + AC.QSURF.1 from v0.1.7
   Cycle 4).
4. User responds Y / N / R(evise).
5. On `Y`, persona materializes the draft to
   `<workspace>/.claude/skills/<slug>/SKILL.md` via the `Write`
   tool. Anthropic's native filesystem-walk discovery picks it up
   on the next relevant turn.

The gate is **structural**, not advisory. The persona MUST write
to `.scratch/` first; the `Write`-to-`.claude/skills/` step
happens ONLY after a `Y` response is recorded via PM's
`record_response`. Eric, Luke, and any other loam user can audit
the entire chain via the PM audit-log + the skill-capture audit-
log.

### 1.3 — Workflow-flag-only gating

The mechanism is gated by a **single workflow-level flag**:
`enable_auto_skill_capture` in `bootstrap.yaml` (default `false`).
Per layered-skill research §3.6 Decision E:

- A fresh workspace shouldn't immediately start proposing skills.
  The user opts in by flipping the flag when they're ready.
- When `false`, the SKILL's "When to use" gate is closed; the
  persona MUST NOT propose. Graceful degradation back to
  pre-Cycle-2 behavior.
- When `true`, the persona MAY propose per the trigger
  heuristics, subject to cool-down + budget + hard-cap suppression
  gates.

The flag is **not** dev-mode-gated. Per the universal-tier
clarification, any user (dev or non-dev) can opt in. The single
flag is the only workflow-level gate; no separate dev-only override
exists.

---

## §2 — Triggers

Three triggers ship at v0.2.0 MVP. Three deferred to v0.2.x. The
3-of-6 lock is per Decision N (parent §2 + master plan §3 Cycle 2)
and is a quality-bar move (ship 3 complete rather than 6 half-
implemented).

### 2.1 — MVP triggers (3)

**Trigger 1 — Explicit request.** Highest-precision; near-zero
false-positive. Phrase-list match on user phrasing:

- "remember this"
- "make this a thing" / "make this a skill" / "make this reusable"
- "let's codify this" / "let's capture this"
- "capture this as a skill" / "save this as a skill"
- "remember this pattern" / "add this to my skills"

On match → proposal-draft mode immediately. No threshold; no
cool-down check (explicit user intent overrides cool-down).

**Trigger 2 — Repeated invocation.** The canonical "auto-creation"
use case from Luke's framing — same multi-step procedure 3+ times
within a session window. Tool-call sequence + structural overlap
≥70% across invocations. **Session-scoped at MVP** — detection
in conversation memory, NOT M-FBM episode-store reads (deferred
to v0.2.x; see §6 forward path).

**Trigger 3 — Ask-and-answer pattern.** User asks the persona how
to do X 3+ times in a session AND the answer text stabilizes.
Question-text similarity ≥70% AND answer-text similarity ≥80%
across the 3 stabilized exchanges. Especially valuable for non-
dev users whose patterns are rhetorical / methodological
recurrences. **Session-scoped at MVP** — same scope as Trigger 2.

### 2.2 — Deferred triggers (3)

Named here so the v0.2.x forward path is visible at v0.2.0 ship-
time. Each requires component-side instrumentation OR is
dev-mode-only — incompatible with v0.2.0's MVP scope.

**Deferred Trigger A — CLAUDE.md drift detection.** A CLAUDE.md
section has grown to look like a procedure (Anthropic's own
auto-prompt: *"a section of CLAUDE.md has grown into a procedure
rather than a fact"*). Extract the procedure as a skill; thin the
CLAUDE.md. Why deferred: requires a CLAUDE.md parser + drift
heuristic + cross-session reading; incompatible with the MVP's
session-scoped framing.

**Deferred Trigger B — Memory-recall hit pattern.** When the
persona's M-FBM retrieval lands the same prior-turn episode 3+
times in a week as relevant prior context, the pattern in that
episode is a skill candidate. Why deferred: requires M-FBM API
extension (a "find episodes that landed N times" query primitive
not yet provided); cross-session by definition.

**Deferred Trigger C — Hook-trigger pattern.** When a hook fires
the same warning (e.g., "you didn't run plan-before-code")
repeatedly across sessions, the corrective behavior is a skill
candidate. Why deferred: dev-mode-only (hooks are dev-shape);
requires hook-event subscription primitive not yet exposed.

---

## §3 — Workflow

The five-step capture workflow. Detail in
`plugins/loam-skills/skills/skill-capture-proposal/SKILL.md` §"How
the persona applies it".

1. **Detect + draft.** Persona detects trigger; writes draft to
   `<workspace>/.scratch/claude-output/skill-draft-<slug>.md`
   using the 6-section template (What / When / How / Graceful
   degradation / Composition / Out of scope). Draft includes a
   header with trigger-name + evidence + ISO timestamp.
2. **Audit-log the trigger fire.** Write
   `skill_capture_trigger_fired` entry to
   `<workspace>/.loam/skill-capture/audit-log/<YYYY-MM-DD>-<NNNN>.yaml`.
3. **Surface ratification question via PM.** Use
   `PMRuntime.enqueue_decision` + `surface_next_questions_batch(n=1)`.
   Question text: "I noticed [pattern-summary] N times in this
   session. Capture as workspace-local skill '<slug>'? Draft at
   <path>. Y / N / R(evise)."
4. **Ratify (Y / N / R).**
   - **Y → Materialize.** Move draft to
     `<workspace>/.claude/skills/<slug>/SKILL.md` via `Write`;
     write `skill_capture_ratified` audit entry.
   - **N → Reject + cool-down.** Append to
     `cooldowns.yaml`; write `skill_capture_rejected` audit entry.
   - **R → Revise.** Iterate; write `skill_capture_revised` audit
     entry per iteration.
5. **Per-week budget + hard-cap gates.** Read `budget.yaml` (≤3
   proposals/rolling-7-day window) + walk `<workspace>/.claude/
   skills/<*>/SKILL.md` for hard-cap (20 skills). On hit, no-op +
   surface a one-line note about promotion-rubric review (v0.2.1
   forward).

The user-ratification gate is at Step 4. The persona MUST NOT
write to `.claude/skills/` before recording a `Y` response via
PM's `record_response`. This is structural — the workflow encodes
it as a hard ordering, NOT advisory.

---

## §4 — Cool-down + budget + hard-cap

Three suppression gates defend against fatigue + bloat. Each has
durable state under `<workspace>/.loam/skill-capture/`.

### 4.1 — Cool-down (14 days post-rejection)

**Purpose:** prevent the same trigger-pattern from re-proposing
immediately after the user rejected it. Per layered-skill
research §3.5 #1.

**State path:** `<workspace>/.loam/skill-capture/cooldowns.yaml`.

**Shape:**

```yaml
schema_version: 1
cooldowns:
  - trigger_pattern_hash: <sha256 of canonical pattern signature>
    rejection_iso: <ISO 8601 UTC of N response>
    cooldown_until_iso: <rejection + 14 days>
    rejected_slug: <slug of the proposed but rejected skill>
```

**Check:** persona reads at Step 1 (Detect + draft). On hit and
`now < cooldown_until_iso`, no-op + write
`skill_capture_cooldown_active` audit entry. Skip the proposal.

**Override:** Trigger 1 (explicit-request) overrides cool-down —
explicit user intent wins per the multi-signal conflict-resolution
discipline (see §5).

### 4.2 — Per-week budget (≤3 proposals)

**Purpose:** prevent ratification fatigue. Per layered-skill
research §3.5 #3.

**State path:** `<workspace>/.loam/skill-capture/budget.yaml`.

**Shape:**

```yaml
schema_version: 1
budget:
  weekly_cap: 3
  events:
    - proposed_at_iso: <ISO 8601 UTC>
      slug: <slug>
      outcome: <pending | ratified | rejected | revised | budget_exhausted>
```

**Check:** persona counts events with `proposed_at_iso > (now -
7d)`; if count ≥ `weekly_cap`, no-op until oldest event ages out
(rolling-window reset). Configurable via `weekly_cap`; MVP
default is 3.

### 4.3 — Hard-cap (20 workspace-local SKILLs)

**Purpose:** prevent workspace-skill bloat. Anthropic's
description-budget eventually misfires when the SKILL count grows
unbounded. Per layered-skill research §3.5 #1.

**Check:** walk `<workspace>/.claude/skills/<*>/SKILL.md` (the
filesystem-discovery primitive Anthropic uses). If count ≥ 20,
no-op + surface: "Workspace-local skill count at hard-cap (20).
Consider reviewing via the v0.2.1 skill-promotion-review surface
to retire stale skills before proposing new ones."

The hard-cap is **not configurable at v0.2.0 MVP** — promotion-
rubric review (v0.2.1) is the documented escape valve.

---

## §5 — Failure modes

| # | Failure | Mitigation |
|---|---|---|
| 1 | Skill bloat (auto-load misfires; description budget exceeded) | Cool-down (14d post-rejection); v0.2.1 promotion-rubric retirement; hard-cap at 20 |
| 2 | Domain-noise mistaken for pattern | Trigger requires text+structural overlap; user-ratification gate; revised-via-R can correct misframings |
| 3 | User-ratification fatigue | Per-week budget (3 default); cool-down; "decline-all-this-session" via repeated N responses extending cool-down |
| 4 | Workspace-local shadows future plugin name | Convention: workspace-prefix when ambiguous (`pos3-<slug>`, `eric-<slug>`); v0.2.1 promotion-rubric review catches |
| 5 | Method-in-skill smuggling (skill body states HOW, not WHAT) | 6-section template enforces "What captures" + "When to use" sections; v0.2.1 promotion-rubric quality signal catches |
| 6 | Auto-creation fires before user is ready | Single gate: `enable_auto_skill_capture` flag default false; user opts in when ready |
| 7 | Silent skill write bypasses ratification | Structural: persona MUST write to `.scratch/` first; `.claude/skills/` write happens ONLY after `Y` recorded via PM `record_response`. Audit-log catches violations. |
| 8 | Trigger 1 (explicit) re-fires inside cool-down | Resolved per multi-signal conflict-resolution discipline: explicit-user-intent overrides cool-down. The persona surfaces a one-line note ("explicit-request override active; cool-down on this pattern was scheduled until <date>") so the override is visible. |

---

## §6 — Composition

This mechanism composes with:

- **`enable_auto_skill_capture` workspace-config flag** at
  `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py`.
  Single workflow-level gate; default false; bool-only;
  fail-closed via `MissingConfigError` on non-bool.
- **`framework/per-project-pm/` PM batch API** (v0.1.7 Cycle 4
  `122a7c8`). `enqueue_decision` + `surface_next_questions_batch(n=1)`
  + `record_response` is the ratification surface. One-question-
  at-a-time enforced structurally per Decision Q + AC.QSURF.1.
- **Anthropic's SKILL.md schema + native discovery** (verified
  2026-05-04). Plugin SKILLs at `plugins/loam-skills/skills/`;
  workspace-local SKILLs at `<workspace>/.claude/skills/<slug>/`.
  Discovery is filesystem-walk at session-start (verified at
  v0.1.7 Cycle 3 `bcf699a`).
- **`framework/workspace-bootstrap/`** (the manifest loader).
  `Manifest.enable_auto_skill_capture: bool` field accessible
  via `loam.workspace_bootstrap.load_manifest(...)`.
- **The 8 sealed loam-skills + the new `skill-capture-proposal`**
  (9 SKILLs total at v0.2.0 close). The new SKILL composes on
  top of the 8 by following the same body-shape template (the
  SKILL it generates also follows the 6-section template).
- **`docs/design/layered-skill-architecture.md`** (v0.1.7 Cycle 3).
  This design note's universal-tier framing is the natural
  extension of the three-layer architecture documented there;
  workspace-local SKILLs are the auto-capture target layer.
- **CLAUDE.md design lenses.** Lens 1 (Claude-leverage-first; the
  mechanism leans on Anthropic's discovery primitive + Claude's
  Write tool + per-project-pm primitives), Lens 2 (harness +
  persona value; invokable from any loam-driven workflow),
  Lens 4 (HIGH-confidence shape; mirrors 8 existing reference
  SKILLs), Lens 5 (stopping criterion; the design note co-ships
  with the SKILL because separating them would be coordination
  overhead).
- **F2 RUTHLESS FEEDBACK.** The user-ratification gate IS the
  feedback channel; the user names disagreements (N response or
  R revision) immediately, and the persona learns the pattern.
- **M5 multi-signal conflict resolution.** When triggers conflict
  with cool-downs (e.g., explicit-request fires inside an active
  cool-down for the same pattern), the conflict is resolved with
  signals named (user-intent vs cool-down vs trigger-precedence)
  rather than silently. Explicit-request wins per signal weight.
- **SOC-2 audit-trail floor (Decision P).** Six event-kinds at
  `<workspace>/.loam/skill-capture/audit-log/<YYYY-MM-DD>-<NNNN>.yaml`:
  `skill_capture_trigger_fired`, `skill_capture_proposal_drafted`,
  `skill_capture_ratified`, `skill_capture_rejected`,
  `skill_capture_revised`, `skill_capture_cooldown_active`.

---

## §7 — Forward path (v0.2.x and v0.2.1)

What lands AFTER v0.2.0 closes.

### 7.1 — v0.2.1 deliverables

- **Promotion rubric** (`plugins/dev-sdlc/skills/skill-promotion-review/`).
  Six signals (reusability / quality / test coverage / usage /
  conflict / namespace) per layered-skill research §4. Workspace-
  local SKILLs accumulate; this rubric is the disciplined
  evaluation surface for graduation to plugin or base.
- **Demotion path** for retired SKILLs. Symmetric with the
  promotion rubric.
- **Eric onboarding hardening.** Fresh-user-smoke against Eric's
  workspace; cool-down + budget + hard-cap calibration based on
  observed usage.
- **Per-week budget recalibration.** The MVP default of 3
  proposals/week is a guess; v0.2.1's Eric-feedback drives
  recalibration.

### 7.2 — v0.2.x deliverables (post-Eric)

- **Three deferred triggers** (CLAUDE.md drift / memory-recall
  hit pattern / hook-trigger pattern). Each requires the
  associated component-side instrumentation:
  - CLAUDE.md drift → CLAUDE.md parser + drift heuristic +
    cross-session reading.
  - Memory-recall hit → M-FBM API extension ("find episodes that
    landed N times" query primitive).
  - Hook-trigger → hook-event subscription primitive.
- **Cross-session trigger detection.** Triggers 2 + 3 are
  session-scoped at MVP. v0.2.x extends them to read M-FBM
  episode-store for cross-session detection. Per master plan
  §7.3 risk surface.
- **Mode 2 structured fill-in-blanks UI** (per Decision D +
  layered-skill research §3.4). MVP uses Mode 1 (persona drafts
  + user reviews); Mode 2 is the alternative for users who want
  named-section prompts.
- **Python runtime detector module** (`loam_skill_capture`).
  Triggers ship as persona-side discipline at MVP; if reuse
  pressure emerges (e.g., a Python helper extracts trigger-
  detection from the SKILL body), v0.2.x extracts the module.

### 7.3 — Forward-path stability

The four mechanisms named here (promotion rubric, demotion path,
Eric onboarding, recalibration) are **v0.2.1**. The four
mechanisms named at §7.2 are **v0.2.x post-Eric** — not v0.2.1.
This split is per master plan §1 + parent eric-final-delivery
§2 v0.2.0 row + Decision N's MVP framing.

---

## §8 — Eric grounding

A concrete example for why this mechanism matters.

Eric runs a Rails SaaS (payment-handling, accounting, integrations,
typed front-end). When loam attaches to his repo at v0.2.0:

1. Eric flips `enable_auto_skill_capture: true` in his
   workspace's `bootstrap.yaml`.
2. Eric asks the persona to "review this PR for payment-handling
   correctness; check the refund path; verify the audit-log
   coverage." The persona walks through three Rails files,
   inspects the ActiveRecord callbacks, surfaces three concerns.
3. Eric asks the same shape of review on a different PR
   (different file; same pattern). The persona walks through
   it.
4. On the third PR with the same review-shape, the persona's
   ask-and-answer trigger fires (3 exchanges; same question
   shape; stable answer text — review walk-through).
5. Persona drafts a `payment-handling-pr-review` SKILL to
   `<eric-workspace>/.scratch/claude-output/skill-draft-payment-
   handling-pr-review.md`.
6. Persona surfaces via PM: "I noticed payment-handling PR
   reviews 3 times in this session with stable structure. Capture
   as workspace-local skill 'payment-handling-pr-review'? Y / N
   / R."
7. Eric responds Y. SKILL writes to `<eric-workspace>/.claude/
   skills/payment-handling-pr-review/SKILL.md`.
8. On the fourth PR, the persona auto-loads the SKILL via
   Anthropic's filesystem-walk discovery. Eric says "review this
   PR" — the persona reads the SKILL, applies the captured walk-
   through structure, surfaces concerns in the same shape Eric
   has come to expect.
9. Audit-log under `<eric-workspace>/.loam/skill-capture/audit-
   log/` carries the full trail (trigger fired, proposal drafted,
   ratified, materialized) for SOC-2 compliance.

This is the **Eric-patterns-captured** half of v0.2.0. The
**contract-stays-alive** half (v0.2.0 Cycle 1) keeps Eric's
v0.1.8 banded contract synchronised as his code evolves; this
half (Cycle 2) keeps Eric's recurring patterns invokable as
SKILLs the persona auto-loads.

Both halves compose at the release-level SOFT smoke gate (master
plan §5).

---

## §9 — What this design note does NOT cover

- Implementation method (which sha256 library; which YAML parser;
  which conversation-memory query primitive). Method is the
  builder's call within the constraints.
- Per-trigger detection heuristic at code-time (the SKILL body
  names them; the persona reads from the SKILL).
- Cross-workspace skill sharing (not on roadmap).
- Pricing / cost-governance integration (skills are static
  markdown; no per-fire cost beyond the persona's reasoning).
- Telemetry beyond the SOC-2 audit-trail floor (six event-kinds
  named at §6 + per-project-pm's standard surface_question +
  record_response audit chain).

These are explicitly out-of-scope. Future docs may extend them.
