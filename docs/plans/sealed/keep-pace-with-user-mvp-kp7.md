# keep-pace MVP Cycle 4 — KP7 SessionStart objective + last-state surface — apply ladder

2026-05-28. keep-pace MVP Cycle 4 (final MVP cycle) per
`docs/plans/keep-pace-with-user-mvp.md` §6 Cycle 4, executing the
`docs/design/keep-pace-with-user.md` §3 MVP table KP7 row.

Scope (per sub-plan §6 Cycle 4, single-component fence on
orchestrator): a NEW surfacing step on
framework/orchestrator/scripts/pos_session_start.py (a real
existing SessionStart hook):
  - On session start, surface "last session you were on X; next
    likely Y" in plain language (active objectives + last subgoal +
    likely-next-action), routed THROUGH KP9's gate so no
    file-names/IDs leak.
  - Re-assert via the first UserPromptSubmit after a compaction so
    a compaction (incl. the #15174 SessionStart-compact bug, if
    live per AC.KP0.3's recorded behaviour) cannot evaporate it.
  - When the surface describes the memory system's OWN behaviour,
    it uses plain words ("keeping your fiction work close at
    hand"), never internal terms ("ARC-promoted", "w_s",
    "objective-match").
  - The existing service-health probing behaviour of
    pos_session_start.py is PRESERVED (KP7 adds a step, does not
    replace the probe).

AC families:
  - AC.KP7.1 — session opens with a plain-language last-state
    surface, routed through KP9's gate (passes the lint).
  - AC.KP7.2 — survives one compaction via UserPromptSubmit
    re-assert (the #15174 mitigation).
  - AC.KP7.3 — self-description uses plain words (no internal
    jargon; composes with AC.KP9.1).
  - AC.KP.S.1 — fence confined to orchestrator + universal paths.

Method-level choices (builder's call per ODD §1.1):
  - The surface-step placement within pos_session_start.py and the
    #15174 re-assert route (the route is confirmed by AC.KP0.3's
    recorded probe outcome).

Out of scope (per sub-plan §7): all post-MVP KP2/KP3/KP4/KP6/KP8/
KP10; the memory-architecture M1-M5 storage cycle. The compactor /
journal-fold (Surface #2 SessionStart-fold cadence) is post-MVP
(KP3/KP4) — KP7's SessionStart step is authored so the later fold
composes onto the same event.

Predecessor: Cycle 3 (KP9) seal — this cycle's pre-build tip.
Serialized after Cycle 3 per feedback_serialize_amendment_builds.
BASELINE = Cycle 3 seal SHA. Single-component fence on orchestrator.

On Cycle 4 seal: the keep-pace MVP is complete (KP0/KP5/KP1/KP9/
KP7). Backfill docs/release-roadmap.md + docs/STATE.md per sub-plan
§9; record all VERIFY-FIRST probe outcomes (load-bearing for the
post-MVP phases). Publish gate remains owner-asked.
