# Claude-leverage program Slice 3 — NAMED ADOPTIONS — apply ladder

Third of four slices under the master plan
`docs/plans/claude-leverage-program.md`. Delivers the owner-named
instance of the Slice-2 prefer-the-primitive doctrine (sealed
f308b398): `/goal` and `/loop` in consistent, observable use. Consumes
the Slice-2 dispatch-time guard (`primitive_check_guard.py` +
`primitive_check_matchers.py` ROWS) and the Slice-1 currency corpus
(`docs/capability-corpus/`) as the surfaces it extends.

This amendment:
  1. RULES D-ADOPT.1 (the master's D-CLP.2 made precise):
     native-`/goal` vs bespoke `autonomy_continuation.py` →
     KEEP-BOTH-SCOPED. Read off the actual pos3 hook 2026-06-14, it is a
     Stop-event idle-recovery queue dispatcher over a durable
     cross-turn workstream-queue (token-delta + task-count safety caps),
     NOT a single-task drive-to-goal mechanism. `/goal` is the inverse
     shape (single-task, checkable completion, autonomous halt) and is
     ALREADY the keep-going leg of `handsoff-loop`. The two do not
     overlap on the load-bearing axis; `/goal` becomes the default
     keep-going leg for single-task work, the bespoke hook is retained
     for queue-dispatch with the retention reason recorded, and NO pos3
     edit is triggered (the pos3 file is out of this canonical fence —
     plan §3 boundary note; halt trigger 2 guards a retire-misread).
     (AC.CLP-ADOPT.1)
  2. Closes the doctrine-check coverage gap: adds ONE `goal.md`-keyed
     matcher row to `primitive_check_matchers.py` (build-verb +
     keep-going-shape proximity, two-tier deny/warn per the Slice-2
     sibling rows) so a bespoke keep-going dispatch is caught on the
     production PreToolUse path — the slice as the doctrine's worked
     example. The Slice-2 bidirectional corpus↔matcher coverage guard
     keeps the new `goal.md` from drifting uncovered. (AC.CLP-ADOPT.5 ★)
  3. Authors the Class B corpus entry the corpus lacks:
     `docs/capability-corpus/claude-code/goal.md` (sibling
     disambiguation `/goal` vs `/loop` vs `/schedule` vs
     background-agents), matching the existing entry shape; adds the
     reciprocal `/goal` disambiguation to the existing `loop.md`
     (currently absent). Both refresh-kept by Slice-1 machinery
     thereafter. (AC.CLP-ADOPT.4)
  4. Demonstrates observable use:
     - ★ AC.CLP-ADOPT.2: a keep-going fixture through the production
       `handsoff-loop` flow drives via `/goal` on a real task with NO
       pre-arranged state, halting at goal-met. Real `claude -p` leg,
       default Sonnet, NO Anthropic API key, `--bare` never used.
     - AC.CLP-ADOPT.3: a cadence-shaped in-session request routes to
       `/loop` per the catalogue (`loop-command` SKILL + `loop.md`),
       observable in the record. No new `/loop` mechanism — its
       adoption is already structurally guarded (Slice-2 row) +
       catalogued (D-ADOPT.3).
  5. Back-reference SKILL alignment (if needed): `handsoff-loop` /
     `goal-command` / `loop-command` gain a pointer to the D-ADOPT.1
     record. The SKILLs already name `/goal` as the keep-going leg;
     likely a reference edit, not a behavior change.

Out with named handoffs: `autonomy_continuation.py` retirement is NOT
triggered (D-ADOPT.1 keeps it; were a future owner ruling to flip to
replace, the pos3 edit is a tracked workspace chore, master §7.6); the
runtime/persona-path doctrine check for NORMAL-USE workspaces (master §2
row 4 "second" — own cycle); wider gap-table primitive adoptions
(master §7.4); nothing graduates from pos3 to loam-proper in this slice
(D-ADOPT.4).

NO public-action steps; LOCAL only; NO Anthropic API key anywhere.
`/goal` + `/loop` adopted as native primitives, never forked. BASELINE
HEAD 8e91b429 at sub-plan authoring; counter 186 next free; builder
confirms both at apply time (concurrent sibling plan-authors may advance
main between authoring and apply).
