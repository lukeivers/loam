# Two-modes + multi-workspace — master plan

**Status:** authored 2026-04-25. Research-and-planning only. NO CODE,
NO COMMITS produced from this artefact. Plan-before-code per dev CDC.
Plans-only authoring; sub-plans below ladder to specific spec
objectives or are explicitly framed as dev-discipline (§2.5).

**Working directory (canonical):** `/Users/lukeivers/ivers-corp-pos-v2/`.

**Companion artefacts:**
- `FUTURE_IDEAS_DRAFT.md` — captured the originating concern + the
  path-mismatch finding (entries titled "System-design concern: shipped
  runtime vs dev-time machinery — TWO MODES" and "Path-mismatch (#39 ↔
  #40) fix direction").
- `/tmp/pos3-integration-test-report-20260425T163453Z.md` — the
  integration-test report whose Finding-2 hypothesis was a methodology
  artefact, not a real bug; surfaced the dead `classify_workspace`
  heuristic.
- `docs/rebuild/components/objective-tracker/` (post-#38),
  `workspace-bootstrap/` (post-#36/#39), `primary-persona/`
  (post-#33/#35/#40), `hands-off-lifecycle/` (post-#28/#37) — sealed
  components whose surfaces this programme amends.
- Recent amendments forming the workspace-identity family: #6 (slug-
  namespaced launchd labels), #28 (workspace-locality for first-run
  state), #29 (per-workspace memory-port via memory.yaml seam + AC29.5
  workspace-identity-bearing /health), #31 (plist-path), #32
  (session-start context-load gate), #33 (memory-consumer wiring), #36
  (persona scaffold), #37 (default-agent wiring), #38 (tracker schema
  widening), #39 (tracker-seed at first-run), #40 (tracker-context
  contributor). The programme below extends this family with locked
  owner rulings 1–6 (recorded 2026-04-25).

---

## 1. Summary / TLDR

The owner has ruled 2026-04-25 that pos-v2 ships as a single
GitHub-distributed repository serving both end users and contributors.
Two operating modes (NORMAL USE / DEV MODE) live in the same clone;
a workspace-local persona-onboarding answer is the authoritative dev-
intent signal; multi-workspace concurrency is a v1 requirement, which
forces all currently-host-global state to move workspace-local. Six
entangled work items follow from those rulings; this master plan
scopes them, surfaces decisions across them, and links to one sub-plan
per work item. Each sub-plan ladders its acceptance criteria to a
specific spec objective (where one applies) or frames itself as
dev-discipline §2.5 work.

The high-level dependency graph (one-line summary):

> A (persona-onboarding question) → C (state-file migration) → E
> (`classify_workspace` replacement); D (per-workspace memory-port
> auto-allocation) is parallel to A/C/E; B (mode-loading mechanism) +
> F (auto-load partition) compose on E's signal. Across the programme:
> A is structurally upstream of E and B/F; C is parallel to A but
> mutually unblocked once any single sealed-component amendment in the
> set lands; D is independent.

The six work items and their sub-plans:

| Code | Topic | Sub-plan |
|------|-------|----------|
| **A** | Persona-onboarding dev-intent question + workspace-local storage of the answer | `A-onboarding-dev-intent.md` |
| **B** | Two-mode loading mechanism (NORMAL vs DEV; CLAUDE.md / settings / hook surface) | `B-mode-loading.md` |
| **C** | Multi-workspace state-file migration: every host-global `~/.pos/` SQLite + YAML moves workspace-local | `C-state-file-migration.md` |
| **D** | Per-workspace memory-graphiti port auto-allocation (collision-free at scaffold time) | `D-memory-port-auto-allocation.md` |
| **E** | `classify_workspace` replacement: read the dev-intent answer instead of `VALUE_PROPOSITION.md` presence | `E-classify-workspace-replacement.md` |
| **F** | Dev-mode auto-load partition (precise file/dir/tool list per mode + circular-dependency check) | `F-auto-load-partition.md` |

Recommended landing order (rationale in §6 below):

1. **A** lands first (sealed-component amendment to primary-persona;
   establishes the workspace-local signal storage).
2. **C** lands second (sealed-component amendments touching every
   component that currently writes to `~/.pos/`; orthogonal to A but
   easier with A's storage location settled).
3. **E** lands third (sealed-component amendment to workspace-bootstrap
   adapters/tracker_seed; reads A's answer; consumes C's workspace-local
   storage location convention).
4. **D** can land in parallel with A/C/E (independent surface — memory.yaml
   port-allocation logic).
5. **B** + **F** land last (dev-discipline — `tools/`, `CLAUDE.md`, the
   `.claude/settings.json` hook surface). Dev-discipline because no
   spec v1.x objective names "two-mode CLAUDE.md loading" — the loading
   shape composes on Claude-Code's own settings/hook primitives. §2.5
   clarifies this is not a sealed-component cycle.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

§2.5 reads: *"Before scoping anything as a sealed-component amendment,
name the specific spec objective (v1.0/v1.1/v1.2) the code will
satisfy. If I can't name one, the work is dev-discipline (CLAUDE.md,
docs, CDCs, tools/), not a sealed-component cycle."*

Per-sub-plan placement (sub-plans repeat their own §2 framings, summarised here):

- **A** — sealed-component amendment to `primary-persona`. Spec
  objective: **v1.1 — first-run conversational elicitation extends to
  carry the dev-intent answer alongside the existing user_name /
  persona_given_name / domain_focus questions** (re-extension of the
  amendment-#35 surface). The answer is workspace-supplied content;
  ODD §2.5 forward — the new question + write-back are
  AC-backed; reverse — every code path traces back to the new ACs.
- **C** — multi-component sealed-component amendments. Spec objective
  varies by component: workspace-bootstrap (v1.0/v1.1 — "first-run
  scaffold lays workspace-local state" extends amendment #28's
  workspace-locality finding); objective-tracker, scope-of-work,
  orchestrator (v1.x — store-path resolution from workspace identity;
  re-extension under FUTURE_IDEAS Idea 9 — workspace-locality of state
  is the ground rule per amendment #28). Each component-touching
  amendment in C names its own spec objective in its sub-plan.
- **D** — sealed-component amendment to `workspace-bootstrap` (adapter
  for memory-system port allocation) + `memory-system` if a
  port-binding diagnostic surface needs the seam. Spec objective:
  re-extension under FUTURE_IDEAS Idea 9 + amendment #29's surface
  (which named the manual-edit shape; this amendment automates it).
  No spec v1.x amendment.
- **E** — sealed-component amendment to `workspace-bootstrap`
  (`adapters/tracker_seed.classify_workspace`). Spec objective:
  re-extension of amendment #39's contract (the dev-marker contract is
  unchanged in shape; the source-of-truth for "is this a dev workspace"
  changes from `VALUE_PROPOSITION.md`-presence to the workspace-local
  dev-intent answer A stores). Re-extension under FUTURE_IDEAS Idea 9.
- **B** + **F** — dev-discipline. **No spec v1.x objective names
  "CLAUDE.md two-mode auto-load."** The work is operational developer-
  tooling: it composes on Claude-Code's settings/hook surface and on
  workspace-bootstrap's existing scaffold. Dev-discipline territory by
  every property §2.5 names — lives under `tools/` and `.claude/`,
  no sealed-component source changes (B may add a new
  `tools/loam-mode/` CLI; F is a partition declaration committed to
  CLAUDE.md / a sidecar). Recovery: if B/F end up requiring sealed-
  component edits at design time, halt and surface — the design
  itself is wrong.

§2.5 forward+reverse audit will be run on every sub-plan before its
ACs are dispatched.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

Each sub-plan repeats this analysis at finer grain; the master-plan
view captures the cross-cutting answer.

### Lens 1 — Claude-leverage

The programme leans on three Claude primitives:

1. **Claude Code settings + SessionStart hooks** (B + F). Two-mode
   CLAUDE.md loading composes on `.claude/settings.json` (per the
   `update-config` skill area) and SessionStart hooks. We do not
   re-implement a hook framework; we register one that selects the
   right CLAUDE.md fragment based on the dev-intent answer (or the
   absence of one). This is the same composition shape amendment
   #37's first-run-default-agent-wiring took (settings.json fragment,
   hook payload).
2. **Claude Code's session-start additionalContext channel** (already
   in use via amendment #32's session-start gate + #33 + #40
   contributors). E reads the dev-intent answer through the same
   workspace-local YAML the persona contract lives in; B's fragment
   selection is read at session-start time with negligible cost.
3. **Slash-commands surface** (F's dev-mode toggle UX). A `/loam mode`
   slash command (or the existing `/effort`-style toggle pattern)
   composes on Claude Code's slash-command primitive rather than
   re-implementing a CLI.

No part of this programme requires changes to Claude Code itself. If
investigation surfaces a need to modify Claude Code, the programme
halts and surfaces the workaround (per halt trigger 4).

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden
between the user's natural-language intent and AI-effective execution?*

Yes — across the whole programme. Today an end user cloning the repo
inherits the developer's `~/.pos/` host-global state surface, the
developer's auto-loaded `pos-amend` and BASELINE conventions, and the
developer's session-start corpus that includes ODD methodology and dev
CDCs. None of those are part of the user's natural-language intent;
they are translation overhead the user pays for the developer's
benefit. The programme:

- A asks the user once at first-run whether they intend to develop on
  pos-v2; the persona translates from "yes / no" into the right session
  shape thereafter.
- B + F honour that answer by loading dev-only artefacts only when DEV
  MODE applies; the user never sees them.
- C + D + E remove host-global state so two users (or one user with
  two workspaces) never collide on shared paths or ports — the
  primary persona never has to translate "which workspace did I write
  state for?" because workspace identity is structural in every path.

Each AC in each sub-plan ladders to AC.PO.1 (translation-burden
reduction) or AC.PO.2 (toolkit-primitive growth) explicitly via Lens-2
trace blocks. Owner ruling per `feedback_value_proposition_as_prime_objective`.

**Harness test.** *Does this add to the toolkit the primary persona
can draw from?*

Yes — A adds `dev_intent` as a contract field the persona reads on
every session; C standardises workspace-local state-file paths the
persona's contributors (memory, scope-of-work, tracker, orchestrator)
already query; D removes a manual-edit step the persona today has to
remind the operator about; E gives the persona a deterministic
dev-marker; B + F give the persona a partition it can name in
dispatches ("DEV MODE: yes; auto-loaded set: …").

### Lens 3 — ODD authoring

Every sub-plan follows the §7.1 authoring order: objective first,
constraints second, ACs third, method last (only as suggestion). No
method-in-acceptance leaks. Behaviour-count check runs before
dispatch. Forward + reverse §2.5 audit on every sub-plan before
the build dispatch goes out.

Halt-and-signal triggers explicit in every sub-plan; halt triggers
specific to the master plan are listed in §6 below.

---

## 4. Cross-cutting acceptance criteria (programme-level invariants)

Each sub-plan owns its detailed ACs. Three programme-level invariants
hold across every sub-plan and are tested in their respective trees:

### AC.PROG.1 — Two pos-v2 workspaces co-exist on one host without state collision

**Outcome:** With two pos-v2 workspaces (`/path/A`, `/path/B`)
scaffolded on one host, no path written by A is read by B and vice
versa for any first-class state file (orchestrator, scope-of-work,
objective-tracker, memory-staging, cost, reversibility, self-correction,
safety, degradation, telegram, persona contract, first-run state). No
listening port bound by A's memory-sidecar collides with B's. No
launchd label registered by A clashes with B's.

**Test shape (cross-component, pos-amend manifest):** integration-test-
level fixture that scaffolds two workspaces on a tmp-fs, runs each
through first-run, then asserts every state path resolves to a
workspace-local location and that the two sets of paths are disjoint
except for documented universal paths (e.g. `~/Library/LaunchAgents`,
which uses the slug-namespaced labels from amendment #6). The test
lives at `<workspace>/tests/integration/test_two_workspace_isolation.py`
or equivalent. Owner ruling pending on test-host (sub-plan C names
this test as part of C's AC suite; the multi-AC fixture is shared
across C, D, E).

**Maps to:** AC.PO.1 (translation burden absorbed: persona never has
to translate "which workspace's state am I touching"), AC.PO.2
(toolkit primitive: workspace-locality is now structural, persona's
contributors compose on it).

### AC.PROG.2 — Dev-only artefacts do not auto-load in NORMAL USE

**Outcome:** On a fresh clone where the user answered "no" to the
dev-intent question, the session-start corpus does NOT include
`docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/STATE.md`,
`docs/rebuild/FUTURE_IDEAS.md`, dev CDCs, `tools/pos-amend/` surfaces,
or `docs/rebuild/plans/`. The session-start corpus DOES include
`VALUE_PROPOSITION.md` (still tracker-root-load-bearing per amendment
#39), end-user-facing help docs, the persona-contract surface, and the
runtime harness composition.

**Test shape:** integration test that bootstraps a fresh-clone fixture
with a non-dev contract, fires `compose_session_fields` (session-start
gate), and asserts the discovered baseline corpus does not contain any
of the dev-only paths. Mirror test for DEV MODE asserts the dev paths
ARE included. Lives in primary-persona's session-start-gate test tree
(amendment #32's home).

**Maps to:** AC.PO.1 (translation burden absorbed: end user never sees
dev artefacts they don't need), AC.PO.2 (toolkit primitive: the
persona's session-start corpus composer becomes mode-aware).

### AC.PROG.3 — `classify_workspace` does not consume `VALUE_PROPOSITION.md` presence

**Outcome:** `workspace_bootstrap.adapters.tracker_seed.classify_workspace`
returns the workspace's classification (dev / non-dev) by reading the
workspace-local dev-intent answer (location decided in sub-plan A);
when the answer is absent, defaults to non-dev (per locked owner ruling
4 — defensive default, "shouldn't happen"). The function does NOT call
`Path.is_file()` on `docs/rebuild/VALUE_PROPOSITION.md` for the
purpose of classification. (`VALUE_PROPOSITION.md` is still read by the
seed's value-prop-loader for dev workspaces — a different surface,
unchanged by E.)

**Test shape:** unit test in workspace-bootstrap's test tree that
constructs a workspace with `VALUE_PROPOSITION.md` present and the
dev-intent answer "no" — `classify_workspace` returns "user". Mirror
test with no `VALUE_PROPOSITION.md` and dev-intent "yes" — returns
"pos-v2-dev". Mirror test with no answer at all (defensive) — returns
"user".

**Maps to:** AC.PO.1 (translation burden absorbed: the dev-marker is
now the user's own statement of intent, not an artefact-presence
heuristic), AC.PO.2 (toolkit primitive: a deterministic source of
truth for dev-mode that B/F can compose on).

---

## 5. Dependency graph (sub-plan ordering rationale)

```
                  ┌────────────────────────────────┐
                  │  A  persona-onboarding         │
                  │     dev-intent question +      │
                  │     workspace-local storage    │
                  └─────────────┬──────────────────┘
                                │ supplies the answer-storage location
                                │ that E reads + B/F gate on
                                ▼
                  ┌────────────────────────────────┐
                  │  E  classify_workspace         │
                  │     replacement                │
                  └─────────────┬──────────────────┘
                                │ supplies the deterministic dev-mode
                                │ signal B/F gate on
                                ▼
        ┌────────────────────┐         ┌────────────────────┐
        │  B  two-mode       │         │  F  auto-load      │
        │     loading        │ ◀──────▶│     partition      │
        │     mechanism      │         │     (declarative)  │
        └────────────────────┘         └────────────────────┘
                                  ▲
                                  │ shared partition declaration
                                  │ (settings/CLAUDE.md fragments)

  Parallel surfaces (independent of A/E/B/F sequencing):
        ┌────────────────────┐         ┌────────────────────┐
        │  C  state-file     │         │  D  memory-port    │
        │     migration      │         │     auto-alloc     │
        │     (multi-comp)   │         │     (workspace-    │
        │                    │         │      bootstrap +   │
        │                    │         │      memory-system)│
        └────────────────────┘         └────────────────────┘
```

Notes on the ordering:

- **A → E** is the load-bearing chain. E reads what A writes; landing
  E before A is impossible.
- **A → B/F** is a soft chain. B/F could land first and read a "TBD"
  default that becomes meaningful once A lands; recommendation is to
  land A first so B/F's first behaviour is correct, not a stub.
- **C** is independent of A/E/B/F by surface (different files, different
  components) but shares programme-level invariant AC.PROG.1 with E
  (both prove workspace-locality). Recommend C lands second so A's
  storage decision is unambiguous (workspace-local, alongside other
  workspace-local state).
- **D** is independent of all others by surface (memory-port allocation
  is its own narrow seam). Can land any time the dispatcher has
  bandwidth.

Per `feedback_serialize_amendment_builds`: amendment-builds in the
canonical tree are serial. Plan-author and research dispatches can
parallel; build dispatches serialise. The recommended order respects
that constraint.

---

## 6. Halt triggers (programme-level)

Per the dispatch brief's halt triggers, the master plan inherits and
adds:

1. **A locked owner ruling appears wrong upon further investigation.**
   Halt and surface. Specifically: if research surfaces that workspace-
   local persona-contract storage cannot carry the dev-intent answer
   without breaking the contract Pydantic schema, surface — A's
   storage location decision needs owner re-ruling.
2. **State-file migration (C) requires breaking changes to existing
   data formats.** Halt and surface migration-strategy options. The
   existing canonical workspace has live data in `~/.pos/`; the
   migration must either (a) move-on-first-boot, (b) read-from-old-on-
   miss-write-to-new, or (c) require operator re-init. Sub-plan C names
   this as its primary decision point.
3. **Dev-mode partition (F) creates a circular dependency** (e.g. dev-
   only files needed for non-dev startup). Halt; the partition is wrong
   and needs revision.
4. **CLAUDE.md conditional-loading mechanism requires changes to
   Claude Code itself** (not the harness). Halt; surface a workaround.
   The expected workaround is two CLAUDE.md fragments composed by a
   SessionStart hook; if that path is blocked, the programme stalls
   until owner rules.
5. **Persona-onboarding question (A) collides with the existing #35
   starter-pending flow** such that AC35.x tests would need
   amendment. Surface — that's a re-extension of #35 that needs owner
   approval.
6. **Multi-workspace integration test (AC.PROG.1) cannot be run on the
   build host** (e.g. launchd / Library/LaunchAgents permissions block
   a two-workspace fixture). Halt; surface alternatives — the test may
   need a `coexistence.sh`-style operator-run shape (per amendment
   #29's heavy-apparatus split).

---

## 7. Out-of-scope (across the programme)

- The `loam` rename (Idea 10). The programme uses pos-v2 names
  throughout; rename is a separate migration.
- The Claude-capability map (Idea 1 Step 1). B/F lean on existing
  Claude primitives only; the structured map can land later without
  reshaping this programme.
- Skill-marketplace integration. Not part of the named work.
- Open-source launch readiness (Idea 12). The programme makes the
  shipped-runtime cleaner but doesn't scope launch artefacts.
- Telegram-channel auth model changes. Telegram config stays
  workspace-local (already is) — no new surface.
- Audit trail for the dev-intent answer (the contract already serialises
  to disk; auditability is inherited).

---

## 8. Asymmetric-leverage observations (beyond the named programme)

Per `feedback_asymmetric_problem_solving` — including the inverse-
asymmetric corollary (drop proposals that are medium/high cost for low
leverage, even if they look nice).

### Asymmetric wins worth surfacing

1. **Workspace-local `<workspace>/.pos/` + a single config-dir convention
   simplifies five sealed-component adapters at once.** Today the
   adapters in `workspace-bootstrap/src/workspace_bootstrap/adapters/`
   read from `host.config_dir`, which already defaults to
   `workspace_root/config` per `manifest.py`. The workspace-bootstrap
   contract is *already* workspace-local; the adapters that point at
   `~/.pos/` are doing so against the contract's intent. Once C lands,
   five adapters' file paths become "the contract said so" rather than
   "we wrote it that way" — the work is structural cleanup more than
   migration. **Effort:** low (one path-resolution edit per adapter).
   **Leverage:** high (closes amendment #28's family of workspace-
   identity bugs at the source).

2. **The dev-intent answer is the same shape as `is_starter`.** A new
   contract field — boolean or enum — written once by onboarding,
   read on every session by E, B, and F. The Pydantic-schema mechanic
   already exists; the field is one-line additive. **Effort:** low.
   **Leverage:** high (consumes for E + B + F + future ideas like
   #2 light-touch education's "expert mode" toggle).

3. **`pos-amend` is the dev-mode anchor.** Anything that auto-loads in
   DEV MODE should reach `tools/pos-amend/` first; from there the rest
   is reachable by convention (BASELINE, SEAL_COMMIT, manifest YAMLs,
   plan docs). The dev-mode auto-load partition (F) can be expressed
   as "everything `pos-amend` reads or writes, plus the methodology
   docs" — a tight, mechanically-checkable rule. **Effort:** low.
   **Leverage:** high (makes F testable rather than declarative-only).

4. **Memory-port auto-allocation can use the OS as the registry.**
   Rather than tracking allocated ports in a sidecar registry,
   first-run can `bind(0)` to discover an unused port at scaffold
   time, write that port into memory.yaml, and rely on the kernel's
   port-table as the source of truth. **Effort:** low (one
   `socket.bind(("127.0.0.1", 0))` call). **Leverage:** medium-high
   (no new state surface, no race-on-cleanup hazard).

### Inverse-asymmetric proposals dropped per the corollary

1. **Cross-workspace dev-intent hint** (owner already ruled it out as
   inverse-asymmetric — medium cost, low leverage). Carried as
   evidence the corollary is already in operation.

2. **A "dev-readiness verifier" that audits dev-mode artefacts at
   session-start.** Tempting because it would catch C-related drift
   (e.g. an adapter still writing to `~/.pos/`) early — but the work
   to author the verifier is medium (a session-start hook, a path-
   schema, error-routing) and the leverage is low (drift is rare;
   the integration test in AC.PROG.1 catches it). Dropped.

3. **A `loam mode dev|user` slash-command top-level CLI.** Tempting
   because a one-command toggle feels clean, but the answer flows
   through onboarding once and rarely changes. The mode-toggle UX is
   low-leverage if onboarding is the read path; a follow-up question
   in the persona ("you've started using pos-amend; do you want me to
   flip your dev-intent answer?") is the better composition with
   light-touch education (Idea 2). The CLI is medium cost, low marginal
   leverage. Dropped from this programme; revisit when Idea 2 lands.

4. **A migration tool that reads `~/.pos/` and copies to
   `<workspace>/.pos/`.** Tempting because it would remove operator
   effort on an existing canonical install. But the canonical install
   is a single host (Luke's), and a one-time `mv ~/.pos/* canonical/.pos/`
   is the same effect with no tool to maintain. Inverse-asymmetric;
   dropped.

---

## 9. Decisions remaining for owner ruling

Per `feedback_summarize_and_surface_decisions`. Each decision below
has a recommendation; owner rules from this summary.

### D-MASTER.1 — Storage shape for the dev-intent answer

**Question:** Where does the dev-intent answer live on disk?

**Options:**
- **(a)** Extend `PersonaContract` with a `dev_intent: Literal["yes", "no"]`
  field (matches `is_starter`'s shape; serialises with the contract;
  contract path is the persona handle's directory under `personas/`).
- **(b)** Separate `<workspace>/.pos/dev_intent.yaml` file (parallels
  amendment #28's first-run.state shape; one source of truth for
  workspace-mode-related config).

**Recommendation:** **(a)**. The contract already loads at session-
start, already extends in starter-pending shape (#35), and the answer
is conceptually "user intent" alongside `user_name`, `persona_given_name`,
`domain_focus`. (b) would duplicate the load mechanism and require a
second YAML schema. (a) is one-field extension. Sub-plan A authors
the AC against (a); if the owner rules (b), A's plan changes shape but
no sub-plan downstream rewrites because they read through a path
resolver, not the contract directly.

### D-MASTER.2 — Migration strategy for existing `~/.pos/` state and the global-vs-workspace partition

**Owner-revised 2026-04-25 (post-research):** the original three options all assumed `~/.pos/` was being deprecated. Owner ruled instead that pos-v2 should mirror Claude Code's own `~/.claude/` (global) + `<workspace>/.claude/` (workspace, overrides global) pattern: keep `~/.pos/` as a global preference store with per-workspace overrides at `<workspace>/.pos/`. This eliminates the migration burden entirely, supports legitimate cross-workspace operator preferences, and matches the user's mental model of how Claude Code handles config.

**Resulting partition:**

| Class | Lives where | Override? |
|-------|-------------|-----------|
| **Workspace state** (tracker DB, orchestrator/scope-of-work SQLite, first-run.state, first-run.log, persona contract under `<workspace>/personas/`) | `<workspace>/.pos/` only | No global form makes sense for these — they describe a specific workspace's run state |
| **Operator preferences** (`memory.yaml`, `cost/`, `safety/`, `degradation-config.yaml`, `reversibility.yaml`, `self-correction.yaml`, `telegram.yaml`, `bootstrap.yaml`) | `~/.pos/` global default | `<workspace>/.pos/<filename>` overrides if present |

**Resolution logic:**
- For state files: always workspace-local; no fallback, no read from `~/.pos/`. (If a state file exists in `~/.pos/`, the new resolver ignores it — those are remnants from the pre-C era.)
- For preference files: the resolver reads `<workspace>/.pos/<filename>` first; if absent, falls back to `~/.pos/<filename>`; if absent there too, uses the scaffold's bundled default.

**Cascading simplifications:**

- C (state-file migration) becomes simpler: no migration code, no halt-and-surface, no operator `mv`. Just: state files always live workspace-local going forward; preference files keep working from `~/.pos/` exactly as before, with the new option of per-workspace override.
- D (memory port auto-allocation) becomes simpler: instead of allocating into shared global, the scaffold writes a per-workspace override at `<workspace>/.pos/memory.yaml` carrying the workspace-specific port. Global default stays 8765 untouched.
- Existing `~/.pos/` content for anyone who already has it (canonical install, multi-workspace dev) keeps Just Working as global defaults — zero migration for the operator.

**Anti-asymmetric drops via this revision:** the migration runner with rollback (option a) — medium cost, low leverage. Confirmed dropped per the inverse-asymmetric corollary in `feedback_asymmetric_problem_solving`.

### D-MASTER.3 — Question phrasing for A

**Question:** What does the persona ask the user?

**Options:**
- **(a)** "Do you intend to develop pos-v2 itself, or just use it?"
  (verbatim from the locked owner ruling 4).
- **(b)** Persona-style rephrasing: "I see you've cloned the pos-v2
  repository. Will you be working *on* pos-v2 (developing the harness
  itself) or *with* it (using it for your own work)?"

**Recommendation:** **(b)** — persona-voice rephrasing while preserving
the ruling's binary semantics. The framework-scaffolding shape per
amendment #35's `OnboardingQuestion` keeps the contract field neutral
(`dev_intent`); the prompt text is workspace-supplied content the
contributor renders. Sub-plan A authors the AC against the contract
field semantic, leaves the surface-prose to the persona template
(workspace-supplied content per STATE.md rule #4).

### D-MASTER.4 — DEV MODE follow-up toggle path

**Question:** Once dev_intent is stored, can the user change it mid-
flight?

**Options:**
- **(a)** No — the answer is one-shot at first-run; changing it
  requires re-running onboarding via a manual edit to the contract.
- **(b)** Yes — a slash command `/loam mode dev|user` (or equivalent)
  flips the answer.
- **(c)** Yes — but only via a re-asking flow the persona triggers
  on a recognised intent signal (e.g. user runs `pos-amend` from a
  non-dev workspace).

**Recommendation:** **(a) for v1**, with **(c) parked for after Idea 2
(light-touch education)** lands. A is the binary that gates B/F; the
expensive-to-change shape is fine because the cost of being wrong is
"re-run onboarding" (cheap). (b) is medium cost (new slash command,
test surface, persona-voice integration); (c) is medium-high cost
(intent detection layer); both can compose later without breaking (a)'s
ACs.

### D-MASTER.5 — Master-plan vs split

**Question:** Does this programme land as one master plan + six sub-plans,
or one consolidated master plan with §-style sub-sections?

**Options:**
- **(a)** Master + six sub-plans, each on its own dispatch, each with
  its own builder-plan + manifest (where applicable).
- **(b)** One consolidated plan with §-style sub-sections, one
  dispatch per workstream split on §-boundaries.

**Recommendation:** **(a)** — already authored that way. The work
items have different sealed surfaces (A: primary-persona; C:
multi-component; D: memory-system + workspace-bootstrap; E:
workspace-bootstrap; B/F: dev-discipline tools). One dispatch per
sub-plan respects the per-component amendment-cycle bookkeeping that
`pos-amend` enforces; (b) would require manual splitting at dispatch
time.

### D-MASTER.6 — Naming convention for the programme's amendments

**Question:** Should the sealed-component amendments born out of this
programme share a naming theme (e.g. "two-modes-N") or use the next-
sequential amendment numbers?

**Options:**
- **(a)** Next-sequential per `pos-amend` convention (amendment-41,
  amendment-42, …). Owner ruling 2026-04-24 already says the number is
  assigned at dispatch time.
- **(b)** A programme-wide tag in the manifest (`programme:
  two-modes-multi-workspace`) so dependencies are mechanically
  visible, while numbers stay sequential.

**Recommendation:** **(a) + manifest-level cross-reference comment**
(in the `pos-amend` manifest YAML's narrative-target sidecar). (b)
adds a new manifest field which is medium cost (manifest schema +
verifier change) for low leverage (the dependency graph is in this
master plan; the field would duplicate it). The cross-reference
comment in each sub-plan's manifest YAML names the master plan's path
and the sub-plan code (A/B/C/D/E/F).

---

## 10. Pointer to sub-plans

- `A-onboarding-dev-intent.md`
- `B-mode-loading.md`
- `C-state-file-migration.md`
- `D-memory-port-auto-allocation.md`
- `E-classify-workspace-replacement.md`
- `F-auto-load-partition.md`

---

## 11. Sub-plan structure

Each sub-plan follows the 13-section structure used by recent dev-
discipline plans (`pos-amend-seal-automation-extension.md`,
`pos-amend-tracker-integration.md`):

1. Summary / TLDR
2. Spec-objective placement (§2.5 framing)
3. Three-lens analysis
4. Acceptance criteria (named ACs)
5. Out of scope
6. Halt triggers
7. Bookkeeping (`pos-amend` manifest where applicable)
8. Dispatch-time additions
9. Lens-2 trace blocks (per AC, mapping to AC.PO.1 and/or AC.PO.2)
10. Decision register (per sub-plan)
11. Builder freedom (method-only notes)
12. Test register (per AC)
13. Asymmetric observations

---

## 12. Closing

This master plan inherits the locked owner rulings (1–6, recorded
2026-04-25), surfaces six entangled work items, links to one sub-plan
per item, names cross-cutting invariants AC.PROG.1–AC.PROG.3, and
ladders every AC trace to AC.PO.1 / AC.PO.2 via Lens-2. Decisions
remaining for owner ruling are explicit in §9 with recommendations.
Halt triggers are explicit in §6.

After owner rules on §9, sub-plan dispatches go out one-by-one (per
recommended order in §1) per `feedback_serialize_amendment_builds`.
