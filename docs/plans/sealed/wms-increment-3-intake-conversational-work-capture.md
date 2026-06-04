# WMS Increment 3 — INTAKE: conversational work-capture (light-default, propose-and-confirm)

Per `docs/plans/wms-increment-3-intake-conversational-work-capture.md` and the parent
architecture `docs/design/work-management-system-architecture.md` (roadmap item 3 —
intake; §4a + §6.1 intake-is-conversation-not-a-form; WMS-D4 intake-aggressiveness-is-
per-user, light default). Owner-greenlit "build it all the way through" (Luke 13704);
WMS elevated to MAJOR sub-component (13656). SINGLE-component amendment on the SEALED
`primary-persona` (a new keep-pace `intake.py` turn contributor). Stacks on
`build/wms-increment-2` (the work-item store surface intake creates into lives only
there). Composes on the #56 LLM intent-extraction seam + the #34 interaction-model +
the keep-pace turn loop + the increment-2 store (Lens-1: compose, don't duplicate).

INTAKE is the translation-IN pillar of the work-management system: the user states
intent in natural language ("I also need to get the rental paperwork going", "the
launch waits on Eric's review") and a work item appears, correctly placed, without the
user ever touching a tracker or holding an ID. The capture is LIGHT by default —
detect-and-PROPOSE (one plain-language "want me to track this?"), never silent auto-
create, never nag. A detected item is a real work item created in the store's
`proposed` (surfaced-not-committed) lifecycle state with `origin: conversation`
provenance + a candidate stream/project; a plain-language confirm promotes it to
`active`, a dismiss abandons it, an ignored proposal does not re-nag.

The aggressiveness — how readily a turn becomes a proposal — is a per-user preference
cell in the #34 interaction-model (`work-tracking`/`intake-aggressiveness`, default
LIGHT; `off`/`light`/`eager`). A power user who wants aggressive capture dials eager;
a non-tech user who wants quiet keeps light or dials off; loam can learn the preference
from repeated dismissals (`apply_override`). Detection composes the #56 `IntentExtractor`
Protocol + its spawn-isolation + fail-soft discipline with a WORK-SHAPED prompt
(reusing the MECHANISM, not the onboarding stop/start prompt); on extractor-decline
intake surfaces NO proposal (silence is the safe failure mode for a quality-LIFT layer,
the don't-nag-aligned default). Dedup against open work items is CONSERVATIVE — suppress
only a high-confidence near-duplicate (a re-mention of an already-tracked thing yields
one item, not a pile), propose when unsure (a visible dismissable duplicate beats a
silently-dropped new item — the false-merge asymmetry, plan §10 RF #3).

The objective-tracker store is CONSUMED via its existing `create`/transition API, NOT
modified — increment 3 is single-component on `primary-persona`. If the build discovers
a needed store-side change, it HALTS rather than opening a second sealed-store amendment
(plan §8 #2). The outcome-altitude AC (AC.INTK.LIVE.1) exercises the live production
turn-path with no pre-arranged state: one real work-mentioning turn yields exactly one
correctly-placed `proposed` item in the live store, and a chatter turn yields zero.

Out of scope (later increments): the multi-signal derived-priority weighting + the
relational-graph self-heal (incr-4); the goals/plate/waiting-on lenses (incr-5); full
lens-CHOICE wiring beyond the single aggressiveness cell (incr-6); analytics (incr-7).
