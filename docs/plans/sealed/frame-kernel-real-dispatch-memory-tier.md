# frame-kernel — real-dispatch memory tier

Follow-on to the envelope cwd-fallback corrective (sealed c39de619):
that cycle made the microkernel tier populate on real dispatches;
THIS cycle makes the MEMORY tier populate on them too.

THE GAP (Tier-0, probe captures 2026-06-10): real SubagentStart
envelopes carry only the documented common six fields — no
prompt/task/description — so `parse_envelope`'s task_text was empty
by construction, no memory query ever ran, and every real dispatch
saw `[memory unavailable — no live store or query]`.

THE EVIDENCE (two real `claude -p` runs, isolated via
loam-spawn-isolation, each dispatching a Task subagent under a
SubagentStart capture hook snapshotting the transcript at fire
time): the envelope's transcript_path points at the PARENT
session's transcript; at fire time it already contains the
dispatching turn's real user message; the in-flight Task tool_use
is NOT yet flushed (so a tool_use scan would read nothing — or,
worse, a PREVIOUS dispatch's prompt once one flushes).

THE FIX, layered (D-RDM.1 / D-RDM.2):

(a) task-text derivation — `parse_envelope` falls back from the
envelope fields (kept as first priority, forward-compat) to the
transcript's LAST REAL USER MESSAGE: the current ask the dispatch
serves, the same seed the parent's own per-turn retrieval uses.
Tail-bounded read; record parsing reused from frame_judge. The
derived text feeds the EXISTING gated retrieval unchanged.

(b) standing decision floor — when no task text is derivable at
all, the memory tier injects the workspace's open + recent ruled
decision records WHOLE (sealed decision_ledger read surface),
newest-first, within the existing injection budget — dispatches
always carry the load-bearing rulings even without relevance
matching. With no ledger the tier degrades byte-identically to the
pre-cycle markers.

AC.RDM.1 — derivation + envelope-field priority + synthetic-record
skips + fail-soft. AC.RDM.2 — the floor, whole records, budget,
byte-identical no-ledger degradation. AC.RDM.S (outcome-altitude) —
the production hook entry-point as a subprocess, real-shape
envelope + real-shape transcript fixture, a planted RULED record
relevant to the fixture's user message reaches the injected
memory tier.

Unchanged: fail-soft exit-0 (AC.SACH.4); the workstream tier (its
real-dispatch placeholder is an absent-state-file condition, not an
envelope bug — triaged in plan §2); frame_judge.py; the hook
script; primary-persona (imported read-only); all existing
frame-kernel tests pass untouched.
