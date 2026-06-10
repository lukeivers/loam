# frame-kernel — stop-judge objective from the agent transcript

Third corrective in the frame-kernel real-envelope lineage
(c39de619 envelope-cwd, 9eeef654 memory-tier task-text): the
SubagentStop frame-judge now judges each finished subagent against
that subagent's ACTUAL dispatched objective.

THE LIVE BUG (Tier-0, 2026-06-10): the judge prompt's stated
-objective block carried the PARENT session's first user message —
an owner channel message from the previous day — while judging a
different subagent's result. The judge (correctly, given garbage
inputs) flagged OFF_FRAME, and the bare flag reached the owner with
no provenance. Mechanism: read_subagent_result loaded the
envelope's transcript_path, which points at the PARENT transcript.

THE EVIDENCE (n=2 fresh probe captures, the 9eeef654 technique —
real claude -p runs via loam-spawn-isolation, each dispatching a
Task subagent under a SubagentStop capture hook; Claude Code
2.1.170): the real envelope carries agent_transcript_path — the
subagent's OWN complete transcript whose FIRST user message is the
literal dispatch prompt — plus agent_id/agent_type and
last_assistant_message (the subagent's final output; the agent
transcript's final assistant text is not reliably flushed at fire
time, so the envelope field keeps result priority).

THE FIX (D-FJO.1/2/3): agent_transcript_path is the SOLE
transcript source for the judge path — objective (first user
message), result tail-fallback, and the consequential cue (which
had been counting the PARENT session's writes as the subagent's).
The parent transcript is never loaded for the seed; an envelope
without agent_transcript_path degrades fail-soft to a silent no-op
rather than approximating from parent-message heuristics — no
advisory is strictly better than a wrong advisory. The off-frame
flag now self-identifies: "frame-judge advisory on dispatch
<agent_type> <id>" + a first-line excerpt of the judged objective,
readable out of context.

AC.FJO.1 — objective/cue/result sources + envelope-field priority
+ degraded modes. AC.FJO.2 — advisory provenance. AC.FJO.S
(outcome-altitude) — the production hook entry-point with the real
captured envelope shape: the planted dispatch prompt reaches the
judge prompt's objective block; the planted channel-shaped parent
message does NOT.

Unchanged: fail-soft exit-0 (AC.SSFC.5); the non-blocking surface
shape (AC.SSFC.4); bundle.py and all SubagentStart surfaces; all
existing frame-kernel tests pass under the corrected (real)
envelope fixture shape.
