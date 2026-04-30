# Core Development Convention — Run all execution work through background agents / subagents

> **All build, commit, edit, test, and probe work in pos-v2 runs through background agents or subagents. The main conversational session is an interactive channel reserved for conversation, reading files for direct answers, memory writes, plan writes, and tool calls that directly answer an owner question. Everything else goes to background. There is no "short work is fine in foreground" carve-out.**

Rationale. The main session between the owner and the primary-persona-layer assistant is an interactive channel. Every tool call issued in the main session blocks that channel until it returns — the owner cannot redirect, interject, or halt the work mid-flight without waiting for the call to complete. Background agents (and subagents dispatched from the main session) do not block the channel: while they run, the owner retains full interactive control and the main session can continue listening, replying, and re-routing. That property is unconditional — it holds for one-second calls and one-hour calls alike — which is why the rule does not admit a "short work is fine" exception. A softening along those lines surfaced and slipped within the same session that established the "plan before code, always" CDC, which is why this companion rule is being codified explicitly rather than left as a preference.

Rule:

- Execution work — building, editing source, running tests, running scripted probes, committing, anything that produces a side-effect on the repo or its environment — dispatches to a background agent or subagent.
- Main session operations that remain in-channel: conversation with the owner, reading files (for direct answers or context assembly), writing memory / preference files, writing plan files, and tool calls whose output is the direct answer the owner just asked for.
- Everything outside that list goes to background. No length-based carve-out; a three-second edit blocks the channel for three seconds that the owner might have needed to redirect.

Relationship to the "plan before code, always" CDC: that CDC's Subagent flow subsection is now the default path, not one option among several. Plans are written in the main session (plan writes are on the main-session allowlist above); execution against those plans happens in background.

Applied immediately to all work from 2026-04-22 forward.
