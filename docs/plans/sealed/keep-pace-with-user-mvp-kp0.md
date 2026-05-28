# keep-pace MVP Cycle 1 — KP0 hook chain — apply ladder

2026-05-28. keep-pace MVP Cycle 1 per
`docs/plans/keep-pace-with-user-mvp.md` §6 Cycle 1, executing the
`docs/design/keep-pace-with-user.md` §3 MVP table KP0 row.

Scope (per sub-plan §6 Cycle 1): wire the UserPromptSubmit +
PreToolUse hook chain into the settings surface, add a per-turn
total-latency budget, and prove fail-open-whole-chain. There are
currently ZERO wired hooks (global settings.json hooks = {}). The
hook SCRIPTS are sealed under hands-off-lifecycle (the existing
hook home); the ~/.claude/settings.json wiring is a user-scope
live-harness side-effect documented in the status file, not a
committed source edit.

VERIFY-FIRST (runs BEFORE any dependent KP1/KP9 build):
  - AC.KP0.1 — UserPromptSubmit + PreToolUse fire on the installed
    CLI (HALT gate: if either does not fire, the whole MVP halts).
  - AC.KP0.2 — InstructionsLoaded event firing + context-emit
    behaviour recorded (non-firing blocks only post-MVP M2, not
    this MVP; surfaced).
  - AC.KP0.3 — #15174 SessionStart-compact survival recorded;
    KP7's re-assert route (via UserPromptSubmit) confirmed.

AC families:
  - AC.KP0.1/.2/.3 — VERIFY-FIRST probes, status-file recorded.
  - AC.KP0.4 — fail-open-whole-chain: a deliberately-failing hook
    lets the turn proceed; the live session is never broken by a
    memory hook.
  - AC.KP0.5 — per-hook latency observable in the smoke log
    (loam's own numbers; the design's $0/45ms are claude-mem's,
    NOT loam's — RF-5).
  - AC.KP.S.1 — fence confined to hands-off-lifecycle + universal
    paths; fail-open green before the hook is left wired.

Method-level choices (builder's call per ODD §1.1):
  - Exact hook-script module layout under hands-off-lifecycle/hooks/.
  - The per-turn total-latency budget + fail-open wrapper mechanism.
  - The probe's exact shape (~5-line no-op marker hooks).

Out of scope (per sub-plan §7): KP1/KP5 (Cycle 2), KP9 (Cycle 3),
KP7 (Cycle 4); all post-MVP KP2/KP3/KP4/KP6/KP8/KP10; the
memory-architecture M1–M5 storage cycle.

Rides this fence (doc-only): the RF-1 correction to
docs/design/memory-architecture.md §1/§3.5 (graphiti/S3 store is
NOT live; current memory is file-based only) — universal-admission
prefix; dispatch pre-authorized.

Predecessor commits:
  - 8fea4b9 — last sealed amendment (#148).
  - c88bd0b — current loam HEAD (this cycle's pre-build tip).

BASELINE c88bd0b — re-confirm + advance to the source-edit commit
at apply. Single-component fence on hands-off-lifecycle.
