# SLICE 1b — SubagentStop out-of-band frame-consistency check (the OUT-guarantee)

loam-realignment SLICE 1b. EXTENDS the sealed `frame-kernel`
component. Sealed local; awaiting dispatcher dogfood publish per
ASK-FIRST.

The OUT-side guarantee that pairs with 1a's IN-handoff: when a
CONSEQUENTIAL dispatched subagent FINISHES, a `SubagentStop` hook
evaluates its result OUT-OF-BAND — a fresh evaluation seeded with
ONLY the microkernel + the subagent's stated objective + its result,
explicitly NOT the polluted parent conversation — judging
frame-consistency. Off-frame → a non-blocking flag SURFACES to the
dispatcher (never silently passes); on-frame → silent no-op. Lifts
the previously-UNUSED `SubagentStop` primitive (zero subagent-stop
matchers in any loam settings.json before this amendment). This is
component J from the integrated design instantiated at the
persona→subagent FINISH boundary — the structural enforcement a
drifted doer cannot give itself (a fresh-context judge IS the
unknown-verdict audience; Lerner & Tetlock 1999).

AC.SSFC.1 (structural-cue trigger) — the hook evaluates a
CONSEQUENTIAL subagent (wrote a deliverable / mutated state, a
structural cue read off the transcript) and does NOT spawn a judge
for a trivial read-only finish. The cue SHAPE is pinned; the exact
cue list is the build-time-empirical knob (integrated-design §6-Q1).

AC.SSFC.2 (fresh-context seed) — the judge is seeded with the
microkernel prime-marker + the subagent's stated objective + its
result, and the parent-conversation transcript is ABSENT from the
seed (the load-bearing fresh-context guarantee).

AC.SSFC.3 (isolated judge) — the judge runs as an isolated
subscription `claude -p`: the spawned argv carries the
spawn-isolation flags (`--strict-mcp-config` + empty MCP config) and
the scrubbed env (no Telegram bot-token, no `ANTHROPIC_API_KEY`),
via the SEALED `spawn_isolated_claude` entry-point — never a bare
un-isolated spawn (the PROVEN Telegram-drop kill-vector).

AC.SSFC.4 (off-frame surfaces, on-frame silent) — an off-frame
verdict surfaces a flag naming the subagent + the inconsistency +
the reason; an on-frame verdict surfaces nothing. Off-frame is never
silently passed.

AC.SSFC.5 (fail-soft, non-blocking) — absent/unreadable kernel,
unreadable transcript, judge-spawn failure/timeout, malformed
verdict: the hook exits cleanly with the subagent's return
UN-blocked; and the off-frame surface is a non-blocking flag, not a
hard block, for v1. Mirrors 1a's AC.SACH.4 exit-0 contract.

AC.SSFC.6 (portable fragment) — `settings.fragment.json` declares a
`SubagentStop` matcher block (beside 1a's `SubagentStart` block)
invoking the hook under the workspace venv Python with the
`${LOAM_REPO}` placeholder; any loam workspace can compose it with
no per-workspace hand-authoring. (Live merge into a workspace's
`.claude/settings.json` is the same gated hand-merge step — out of
scope per plan §7-4.)

AC.SSFC.S (outcome-altitude) — a REAL subagent finishing with an
off-frame result, exercised through the production hook entry-point
with no pre-arranged in-test verdict + the REAL on-disk kernel,
causes the hook to FLAG it (an on-frame control is not flagged). The
probe exercises the REAL hook + trigger-gate + seed-assembly +
`spawn_isolated_claude` argv/env construction end-to-end; the live
model-verdict leg may be stubbed at the spawn boundary if a live
in-test `claude -p` is infeasible in CI (the 1a AC.SACH.S posture),
and the test SAYS SO. n=1 architectural verdict (does SubagentStop
deliver a readable result AT ALL?) per
`feedback_n1_architectural_vs_n3_statistical`. This IS the build's
feasibility de-risking act — if it comes back unable to read the
off-frame result, the build HALTS per plan §8 trigger #1.

D-SSFC.1 ruled EXTEND the sealed `frame-kernel` component (not a new
component) — IN + OUT are one matched mechanism on one boundary;
`frozen_baseline: false` advances the frame-kernel seal baseline.

D-SSFC.2 ruled the judge runs as an isolated subscription `claude -p`
via the SEALED `spawn_isolated_claude` entry-point — spawn-isolation
is a HARD constraint (PROVEN Telegram kill-vector + no-API-key
reality), composed on the sealed isolation surface (Lens 1).

D-SSFC.3 ruled the trigger fires on STRUCTURAL cues (consequential
subagents only — wrote-deliverable / mutated-state), not every
finish; the exact cue list is the build-time-empirical knob.

D-SSFC.4 ruled the off-frame action is a NON-BLOCKING surface to the
dispatcher for v1 (judge fallibility; hard-block deferred pending
verdict-reliability measurement) — off-frame always surfaces.

D-SSFC.5 ruled the judge's seed is the microkernel + stated objective
+ result ONLY (the fresh-context guarantee) — the parent conversation
is explicitly EXCLUDED.

EXTENDS the `frame-kernel` fence (frozen_baseline: false); the
spawn-isolation surface is IMPORTED, never edited; no other sealed
component's fence widens; no live hook wiring changes (the fragment
block is authored + tested, not merged into any live
`.claude/settings.json`).

Plan-doc + manifest authored by loam-plan-author; source-edit batch
(frame_judge module + SubagentStop hook + fragment extension + tests)
+ apply + seal TBD-AT-BUILD.
