# Duration estimation rubric for AI-driven loam tasks

**Purpose.** Help Claude agents (and any AI-driven builder) predict
wall-clock time for work on loam — doc edits, amendment builds, new
components, investigations. This rubric replaces uncalibrated
human-developer intuition, which tends to run 10-50x too long for
AI-driven work.

**Status.** Calibrated against observed background-agent completions.
Append a row to §2 after each completion so the calibration tightens
over time.

---

## Why this exists

The 2026-04-23 session surfaced two related failures. First, a
"several weeks" estimate for a Claude-capability map cycle was wrong
by ~two orders of magnitude (actual ~15 minutes of agent time).
Second, the starting heuristic "~1 minute per tool call" is a
reasonable upper bound for complex calls (test runs, heavy LLM
thinks, subagent dispatches) but a 6-10x overestimate for the average.
Without calibration, both over- and underestimates degrade
agent-to-owner trust and distort scope rulings.

---

## 1. How to use

### Step 1 — Categorize by task shape

| Shape | Wall-clock | Tool calls |
|---|---|---|
| Tiny docs edit (≤3 files, no code, no tests) | 1-3 min | 5-20 |
| Medium docs creation (1 new 500-1500-line MD, with research) | 10-30 min | 30-80 |
| Amendment build (single sealed component, source + tests + seal) | 10-20 min | 60-120 |
| Amendment build (multi-component or heavy refactor) | 20-45 min | 120-250 |
| New component full five-gate cycle (research plan → research → proposal → brief → build → seal) | 60-180 min | 250-600 |
| Debugging / investigation (exploratory, no commits) | 5-20 min | 20-80 |

If the task doesn't fit a category cleanly, pick the nearest two and span them.

### Step 2 — Baseline formula (sanity check)

`wall_clock_minutes ≈ tool_calls × 0.09-0.22`

That's 5-13 sec/call on observed data. Floor: ~30 sec for any agent
dispatch (spinup + context load).

Adjust **up** if:
- Test suites run inside the agent (each full pytest run ≈ 30-60 sec)
- WebFetch calls dominate (each ≈ 5-15 sec)
- Subagent dispatches (each ≈ 30-60 sec)
- Large file reads/writes (>1000 lines)
- Compaction or context pressure forces retries

### Step 3 — Parallelization factor

When N agents run concurrently on disjoint work, wall-clock ≈
max(agent_times), not sum. Only claim the benefit when the agents
genuinely touch disjoint file sets — otherwise git index races and
merge steps erode savings.

### Step 4 — Report as a range, never a point

"~15-25 min, likely ~20" — not "~20 min." Always own uncertainty.
Novel task shapes get ±50% widening.

### Step 5 — Log actuals; calibrate forward

Each background-agent completion reports `duration_ms`, `tool_uses`,
and `total_tokens`. Add a row to §2 below after each completion.
Every 5 new rows, review the category ranges: tighten if actuals
cluster at one end, widen if they span widely.

---

## 2. Calibration data points

| Date | Task | Shape | Predicted wall | Actual wall | Predicted calls | Actual calls | Tokens | Notes |
|---|---|---|---|---|---|---|---|---|
| 2026-04-23 | CLAUDE.md edit + amendment #29 retraction | Tiny docs edit | 10-20 min | 1.2 min | ~20 | 14 | 27,433 | Pre-rubric estimate; 8-17x too high. |
| 2026-04-23 | Amendment #28 — workspace-identity-routed first-run | Single-component amendment build | 80-120 min | 13.9 min | 80-120 | 95 | 154,601 | Pre-rubric estimate; 6-9x too high. Used amendment-dispatch CDC speedups. |
| 2026-04-23 | Amendment #12 (session) — CLAUDE.md Operational cautions | Tiny docs edit | 1-3 min | 0.7 min | 5-20 | 8 | — | Rubric-based prediction; inside range. 5.1 sec/call — consistent with earlier tiny-docs rate. |
| 2026-04-23 | CLAUDE_CAPABILITIES.md initial authoring (11 commits, incremental-write strategy) | Medium docs creation | 10-30 min | 15 min | 30-80 | 69 | 180,446 | Rubric-based prediction; inside range. 13 sec/call — higher because of 15 WebFetch calls. Incremental-write recovered a prior stall. |

---

## 3. Reflexes to apply next time

1. **Start from the category table, not human-developer intuition.** Human build velocities are the wrong anchor for AI-driven work.
2. **Cross-validate with the formula.** If the category and the formula disagree by more than 2x, recategorize — the category is probably wrong.
3. **Tokens measure work done, not wall-clock.** Wall-clock follows tool calls × per-call latency. A 300k-token response with 40 tool calls is faster than a 50k-token response with 150 tool calls.
4. **Parallel dispatches save only critical-path time.** Two agents running in parallel (15 min and 90 min) complete in 90 min wall-clock, not 105 (serial) and not 15 (parallel). Don't oversell parallelism.
5. **Owner-gate reviews are owner-time, not AI-time.** Five-gate cycles have human-in-the-loop serialization at G1/G3/G4. Schedule owner review in parallel with agent work when possible.

---

## 4. Refresh cadence

- **Every completion:** append a row to §2.
- **Every 5 new rows:** review the category ranges in §1 Step 1. Tighten if actuals cluster at one end of a range; widen if they span it.
- **On framework-major-version changes (Claude Code, Claude Agent SDK, the agent runtime):** expect calibration drift. Plan a bulk refresh and flag prior rows with a version marker.

---

*Maintained alongside the ODD methodology + worked-examples docs and
the dev-mode CDC catalogue (all DEV MODE only) as durable
builder-discipline reference.*
