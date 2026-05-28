# keep-pace MVP Cycle 3 — KP9 abstraction-voice + constraint draft gate — apply ladder

2026-05-28. keep-pace MVP Cycle 3 per
`docs/plans/keep-pace-with-user-mvp.md` §6 Cycle 3, executing the
`docs/design/keep-pace-with-user.md` §3 MVP table KP9 row. KP9 is
KP1's necessary partner: Layer C catches the mid-draft
contradiction the UserPromptSubmit hook structurally cannot see
(design §1 fix #2).

Scope (per sub-plan §6 Cycle 3, single-component fence on
hands-off-lifecycle): a NEW PreToolUse draft-gate hook reusing the
existing translation-discipline jargon logic:
  - Layer 1 — deterministic jargon lint (block on file-name / path /
    AC-ID / un-introduced ALLCAPS leak); immune to attention decay.
  - Layer C — check the draft vs active high-salience
    constraint-memories (seeded canon rules, sealed rulings); flag
    contradiction before send. THE tonight-failure catch.
  - Routes EVERY user-facing surface (persona free-text, drift
    proposals, the SessionStart summary, any miss-recovery).
  - Gate feedback model-facing only (a "your reply was blocked"
    user-visible message is itself a mechanism-leak); fail-open.
  - A deterministic pre-filter hook-point reserved for the post-MVP
    KP10 claude -p register judge (Surface #4: pre-filter-then-
    judge, fail-open, log-to-tune).

AC families:
  - AC.KP9.1 — Layer 1 blocks each leak class; clean draft passes.
  - AC.KP9.2 — Layer C flags draft-vs-active-constraint
    contradiction (litrpg draft contradicting a seeded canon rule
    -> flagged); compliant draft passes.
  - AC.KP9.3 — routes EVERY user-facing surface (a non-free-text
    surface carrying a leak is also blocked).
  - AC.KP9.4 — gate feedback model-facing only; fail-open on
    gate error/timeout (draft sent).
  - AC.KP.S.1 — fence confined to hands-off-lifecycle + universal.

Method-level choices (builder's call per ODD §1.1):
  - jargon-module reuse mechanism (extract a shared module vs
    import from the SKILL surface) — the SKILL is NOT mutated.
  - Layer C active-constraint scope (RF-4 recommendation:
    start NARROW — seeded canon rules + sealed rulings only — and
    expand only when KP10's judge lands; over-flag is fail-open,
    a missed contradiction re-arms tonight's failure).

Out of scope (per sub-plan §7): KP7 (Cycle 4); the post-MVP KP10
Layer-2 judge (this cycle only reserves its pre-filter hook-point);
all other post-MVP items.

Predecessor: Cycle 2 (KP5+KP1) seal — this cycle's pre-build tip.
Serialized after Cycle 2 per feedback_serialize_amendment_builds.
BASELINE = Cycle 2 seal SHA. Single-component fence on
hands-off-lifecycle (frozen_baseline true, H19).
