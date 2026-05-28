# keep-pace MVP Cycle 2 — KP5 register + KP1 work-anchored retrieval — apply ladder

2026-05-28. keep-pace MVP Cycle 2 per
`docs/plans/keep-pace-with-user-mvp.md` §6 Cycle 2, executing the
`docs/design/keep-pace-with-user.md` §3 MVP table KP5 + KP1 rows.
KP1 is the load-bearing MVP piece (§4 of the design): it fixes
tonight's failure by retrieving against the live WORK, not the
typed prompt.

Scope (per sub-plan §6 Cycle 2, single-component fence on
primary-persona):
  - KP5 (first): OBJECTIVES.md schema/template + seed of the two
    real objectives (fiction pipeline, revenue push), both active;
    loader distinguishes the owner-gated `status` field (Surface
    #3 PROPOSE-AND-SURFACE ruling at the schema level) from the
    soft-auto `last-touched`/`cadence` fields; header names the
    register `user-objectives`, distinct from dev-ODD (Surface #6).
    User-scope per Surface #5 (owner-ruled) — the live file is a
    runtime write; the schema/template is sealed source.
  - KP1: BM25/FTS5 index over the markdown corpus (feedback_*.md +
    CLAUDE.md hierarchy + OBJECTIVES.md) — NO embeddings, NO API
    key (feedback_no_anthropic_api_key, Surface #1). A
    UserPromptSubmit retrieval hook scoring the WORK-ANCHORED key
    (prompt + active-objective + active-subgoal + last-turn topic),
    injecting top-N <=5 as additionalContext, silent on no-match,
    skipping trivial prompts, fresh read each turn.

AC families:
  - AC.KP5.1 — OBJECTIVES.md exists at user-scope with the
    index/detail schema (slug/status/last-touched/cadence/text+
    completion-criterion/subgoal/detail-path).
  - AC.KP5.2 — fiction-pipeline + revenue-push seeded active.
  - AC.KP5.3 — register loads within the hot byte-budget
    (~20KB headroom target; detail in the detail-path, not inlined).
  - AC.KP5.4 — `status` owner-gated-write; `last-touched`/`cadence`
    soft-auto-write (field-class distinction in the loader).
  - AC.KP5.5 — KP1's anchor reads the active-objective text.
  - AC.KP1.1 — FTS5 index builds + updates single-digit-ms on write.
  - AC.KP1.2 — work-anchored key (all four components contribute;
    degrades gracefully when one is absent).
  - AC.KP1.3 — top-N <=5 injected as additionalContext.
  - AC.KP1.4 — silent on no-match; trivial prompts skipped.
  - AC.KP1.5 — fresh read each turn (mid-session corpus write seen
    next turn, no restart).
  - AC.KP1.6 — OUTCOME-ALTITUDE: production retrieval entry-point,
    NO pre-arranged state, vague "continue" + active fiction
    objective -> litrpg canon pointer surfaces via the objective
    anchor (the direct test of tonight's failure; no fixture
    pre-loads the canon pointer).
  - AC.KP.S.1 — fence confined to primary-persona + universal paths.

Method-level choices (builder's call per ODD §1.1):
  - Exact module layout for the index builder + retrieval hook +
    OBJECTIVES loader under primary-persona.
  - Work-anchored key term-weighting (Surface #7: objective term
    weighted EQUALLY with the other three unless objective-term
    over-domination is observed in smoke, then down-weight +
    record; `w_s` rotation-capping is a post-MVP KP4 concern).
  - The runtime .scratch/ index-file location (gitignored).

Out of scope (per sub-plan §7): KP9 (Cycle 3), KP7 (Cycle 4); all
post-MVP KP2 (dark-launch log-only this cycle, steer later) /
KP3/KP4/KP6/KP8/KP10; the memory-architecture M1-M5 storage cycle.
OBJECTIVES.md is added to M2's audited-surface list (Surface #6)
for when M2 lands.

Residual named (RF-2): injecting a pointer != the model attending
to it; this raises the probability, KP9 Layer C (Cycle 3) closes
more of the gap. Substantial improvement, not a guarantee.

Predecessor: Cycle 1 (KP0) seal — this cycle's pre-build tip.
Serialized after KP0 per feedback_serialize_amendment_builds.
BASELINE = Cycle 1 seal SHA (re-confirm + advance to source-edit
commit at apply). Single-component fence on primary-persona.
