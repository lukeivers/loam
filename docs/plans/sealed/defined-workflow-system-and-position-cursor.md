# Defined-workflow system + position cursor + pause-if-lost (P2.3) — apply ladder

2026-05-31. Roadmap P2.3 per
`docs/plans/defined-workflow-system-and-position-cursor-plan.md`.
Builds the structural answer to the FM.PROCESS-DRIFT failure class
(process-deviation-under-pressure): a real multi-step process is
written as a FLOW with an explicit current-POSITION cursor that
survives a context-loss event, and "if you cannot say where you are,
PAUSE" becomes a positive-resolution gate rather than prose.

Four forks ruled (built to the plan's recommended options, NOT
re-opened):
  A1 = cursor block as additive context on SessionStart(compact) +
       PreCompact + UserPromptSubmit; the PreToolUse arm is ADVISORY
       (surfaces the pause directive as context the agent must honour;
       never a hard tool block). A blocking mode is an owner-gated
       follow-on.
  B1 = single-active-flow, no nesting/concurrency. The dogfood is one
       build flow; concurrency is the named first downstream follow-on.
  C1 = AC.FLOWDEF.4 — a flat action-list (below the step floor, no
       branch points, no gates) is rejected as not-a-flow (the owner's
       anti-ceremony constraint). The OUTCOME is the AC; the step-count
       heuristic stays in the validator, not the AC (no method-in-AC).
  D1 = the cursor's authoritative home is a small tracked YAML file per
       flow (docs/flows/<flow>.cursor.yaml for methodology; .loam/flows/
       for user-state instances) — matches the build-cursor.md
       precedent; no FBM coupling for cut one.

The load-bearing F2 carried (plan §10 doubt 1): STALENESS is the real
risk, not absence. A cursor that confidently names a wrong position is
WORSE than no cursor — it defeats the pause-check. So the cursor
resolves against its flow definition and resolves UNRESOLVED (never a
false position) when its step has vanished from a mutated flow; the
pause-check is positive-resolution (lost is the DEFAULT until position
is positively re-established).

ARCHITECTURE NOTE (builder's placement call, plan left method to the
builder; surfaced to the dispatcher): the plan's §2/D3 name the pos3
instance hook `compaction_discipline_reinject.py` as the thing to
"extend." That file is a pos3 INSTANCE hook outside any sealed
framework component and outside this worktree — it cannot be a sealed
amendment target. The plan's Lens-1 INTENT (compose on the existing
re-injection mechanism, author no new engine) is honoured by building
the cursor re-injection as a framework-tracked hook entry-point
(`loam_cli.flows.reinject`) that uses the SAME envelope-on-stdin →
additionalContext-on-stdout pattern the framework's SessionStart-family
hooks already ship. The pos3 instance hook is the DEPLOYMENT of that
pattern; the framework owns the reusable mechanism. AC.REINJECT.1's
"real entry-point" is satisfied identically — a real hook CLI invoked
with a real stdin envelope reading a real on-disk cursor. Wiring the
framework hook into a live instance's settings.json (the additive
UserPromptSubmit/PreToolUse registration) is an instance-config step,
owner-gated like G3, outside this sealed cycle's fence.

What landed (all under framework/tools/loam/ — the loam-cli fence):
  - `loam_cli/flows/format.py` — the flow-definition format (D1):
    `parse_flow_definition` / `validate_flow_definition` over
    YAML-frontmatter + Markdown; a walkable node graph (reachability +
    transition-target validation) + the not-a-flow ceremony floor
    (AC.FLOWDEF.1/2/3/4).
  - `loam_cli/flows/cursor.py` — the persisted position cursor
    (AC.CURSOR.1/2/3/4): write / advance (explicit, validated) /
    resolve (positive-resolution against the flow) / stale-detect
    (vanished-step → UNRESOLVED, never false); tracked vs .loam/ homes.
  - `loam_cli/flows/pause.py` — the pause-if-lost positive-resolution
    gate (AC.PAUSE.1/2/3): a resolved cursor surfaces position +
    directive; an unresolved one surfaces PAUSE; lost is the default.
  - `loam_cli/flows/reinject.py` — the re-injection hook entry-point
    (★ AC.REINJECT.1 / D3 / A1): reads the envelope on stdin, reads the
    cursor from disk, emits the position block or the PAUSE directive
    on stdout; PreToolUse advisory; fail-safe exit 0.
  - `loam_cli/flows/cli.py` + the `flow` entry-point in pyproject — the
    `loam flow validate` / `loam flow position` verb (the production
    operator entry-point).
  - docs/flows/loam-vnext-build.flow.md + .cursor.yaml — the dogfood
    flow definition + persisted cursor (AC.DOGFOOD.1; resolves to the
    same position the manual build-cursor.md names today).
  - docs/conventions/flow-definition.md — the format + cursor +
    pause-if-lost convention.

Proven: AC.FLOWDEF.{1,2,3,4} (both-halves + build-workflow round-trip +
malformed-rejected + flat-list-rejected), AC.CURSOR.{1,2,3,4}
(definite-position + advance + STALE-unresolved + tracked-vs-.loam
homes against the real .gitignore), AC.PAUSE.{1,2,3} (surface-on-
resolved + pause-on-unresolved + lost-is-default), AC.DOGFOOD.1 (the
build-workflow validates + its cursor resolves to the manual block's
position), and ★ AC.REINJECT.1 (outcome-altitude: the REAL re-injection
hook, a real envelope on stdin, a real on-disk cursor in a fresh
subprocess, re-establishes flow + step + branch-state + the directive —
and emits PAUSE on a corrupted cursor — NOT a stub). loam-cli component
suite: 159 passed.
