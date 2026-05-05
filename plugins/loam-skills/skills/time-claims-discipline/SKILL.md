---
description: Verify every time-related claim before stating it — current time / elapsed duration / expected duration. Two failure modes: (1) estimating elapsed time from memory of when something started instead of running `date` to compute precisely; (2) parroting a master-plan / human-developer time band as the expected duration without translating to AI-time per the rubric (AI is 10-50× faster). Use when authoring any reply that includes a timestamp, "started X minutes ago," "elapsed N hours," "estimated band Yh," or any other temporal claim. Composes with translation-discipline (this is translation applied to time) + specific-claims-verified-or-marked-guess (this is specific-claims applied to durations).
---

# time-claims-discipline

Time claims are the highest-frequency specific-claim type in operational
status reports. They're also the easiest to get wrong from memory — wall-
clock drifts; "I started this 30 minutes ago" feels like 60 minutes; master-
plan bands are written in human-developer-hours and look like AI wall-
clock if you don't translate. Every time-claim that escapes verification
is a small lie, and Luke notices.

## Two failure modes this skill catches

### Failure 1 — estimating elapsed time from memory

You glance at when something started, glance at the current time in your
head, subtract, and report the difference. The mental arithmetic carries
~50% error. If you said "60 minutes elapsed" and the actual was 27, that's
not "close enough" — it's a fabricated specific claim.

**Fix:** for any "elapsed X" claim, run `date` first to verify current
wall-clock, then compute against the verified start time. If you don't have
a verified start time, say so explicitly ("started ~13:00 per my memory of
when I dispatched; current is ...").

### Failure 2 — parroting human-developer-time as AI-time

Master plans, sub-plan-docs, and synthesis docs frequently carry "AI-time"
bands written in human-developer-hours (e.g., "5-10h" for a build cycle).
These are NOT what the AI agent will actually take in wall-clock.

Per the AI-time rubric (`~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`):
**AI-driven background-agent work is 10-50× faster than human-developer
estimates.** Wall-clock minutes ≈ tool_calls × 0.1-0.15.

**Fix:** when citing an expected duration, NEVER pass through the master-
plan band raw. Translate to AI-time at the moment of citation:
- A "5-10h" master-plan band → ~30-60 min AI wall-clock at typical tool-
  call density.
- A "12-22h" aggregate path → ~1.2-3 h AI wall-clock if dispatched
  serially.
- Cite both if the user might want the human-developer reference, but make
  AI-time the headline figure when reporting to the user.

## When this skill applies

ANY time-related claim in user-facing output. Includes:

- "Started X minutes ago" / "X minutes elapsed"
- "Should take Y hours" / "Estimated wall-clock Z minutes"
- "It's been Q time since ..."
- "Expected band: H to K hours"
- Master-plan band citations
- Sub-plan-doc band citations
- Status reports including timing
- Audit reports including timing

Does NOT apply to:

- Internal thinking-block reasoning (where speculative time bands inform
  decisions but don't get reported). Run `date` if a decision turns on
  precise elapsed; otherwise reason at band level.
- Test fixture timestamps (where the timestamp is content, not a claim).

## How to apply

1. **Before any time-claim,** run `date` (or equivalent: `git log --format=%ci`
   for commit timestamps, file mtime, agent dispatch timestamps from the
   task notification metadata).
2. **For elapsed claims,** compute against a verified start time, not a
   remembered one. If start time isn't verifiable, mark the claim as
   estimate ("~30 min based on my memory of when I dispatched").
3. **For expected-duration claims** that come from master-plan / sub-plan-
   doc bands: translate to AI-time per the rubric. Cite the AI-time figure
   as headline; the human-developer band can appear in parentheses.
4. **After completion,** log actuals (wall-clock + tool-call count) for
   forward calibration. The rubric's accuracy improves with each logged
   data point.

## Graceful degradation

If `date` is unavailable (e.g., a sandbox without shell access), use the
nearest verifiable proxy (file mtime, message timestamp from the
conversation, agent dispatch metadata) and explicitly mark the claim as
"per <proxy>, ~X minutes" rather than asserting precise elapsed.

If a master plan's band is genuinely unbounded (a research dispatch with
no prior calibration), state the rubric-based AI-time band you can predict
plus the explicit "wide variance — first run; will calibrate" qualifier.

## Composition with other skills + memory rules

- **translation-discipline** (sibling SKILL): outbound communication
  shape. This is translation applied to the time axis.
- **`feedback_specific_claims_verified_or_marked_guess.md`** (memory
  rule): every specific claim verified or marked guess. This is the
  duration-specific instantiation.
- **`feedback_duration_estimation_rubric.md`** (memory rule): the canonical
  AI-time rubric + calibration table. This skill references it; doesn't
  replace it.
- **audit-block-on-telegram** (sibling SKILL): when audit catches a time-
  claim ✗, surface in the body's audit line per the audit rule.

## Out of scope

This skill does NOT cover:

- General specific-claims discipline (counts, SHAs, line numbers) —
  covered by the broader `feedback_specific_claims_verified_or_marked_guess.md`
  memory rule.
- Time-zone handling — assume the local time-zone of the operator unless
  explicitly stated otherwise.
- Real-time scheduling decisions (cron cadences, retry backoffs) — those
  are component-level decisions, not user-facing claims.
