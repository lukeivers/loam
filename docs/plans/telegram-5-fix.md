# Telegram-death-#5 fix — shared, importable, mandated isolation surface

**Plan date:** 2026-05-16
**Status:** Build cycle. Canonical-loam local seal on branch
`amend/loam-init-persona-wiring`. NOT merged / pushed / published /
tagged. The binding contract this builds to:
`pos3/workspace/.scratch/claude-output/telegram-5-fix-plan-2026-05-16.md`
(read fully; ODD-shaped; source-grounded). This canonical plan-doc is
the seal-ritual artifact; the contract is the authoritative scope.

## 0. Headline

The shared-mandate IS a contained change — NOT a re-architecture. The
proven isolation primitive (`build_isolated_claude_argv` /
`build_isolated_env` / `write_empty_mcp_config` / `IsolationConfig`,
sealed under AC.LIPW.5/.6 on subloam-driver) and the proven
handsoff-loop `_isolation.py` adapter pattern (sealed b33c0a8/e0b71cb,
AC.TPI.*) are PROMOTED into ONE shared, importable, mandated surface
any loam-adjacent caller — including a dispatched-agent-authored
`/tmp` test/judge/probe/re-harness — imports in one line. Plus a
structural guard so a loam-adjacent `claude` argv built WITHOUT it
fails loudly, plus the one-line `CLAUDE_PERSONA` belt-and-braces
env-var that independently defangs the kill. No new isolation
mechanism; no spawn-router re-architecture.

**The b33c0a8 fix did NOT fail and was NOT under-scoped for what it
was built for.** It isolates the three §1b handsoff-loop production
launch sites and it holds. Death #5 came through a doorway it was
never positioned to reach: a dispatched-agent-authored throwaway
re-harden harness in `/tmp` (`/private/tmp/phase-b-reharden-2026-05-16/
reharden.py:137-146`) that hand-rolled
`subprocess.run(["claude","-p",...])` with
`ThreadPoolExecutor(max_workers=7)` — up to 7 parallel un-isolated
spawns, each loading the user-enabled telegram plugin → competing
`bun server.ts` → operator poller SIGTERM'd. The fix closes that
doorway *class*, not three more files (there are zero uncovered
in-tree spawn sites — every in-tree spawn is already isolated).

**INERT-WITHOUT-MERGE — load-bearing, not softened.** This fix is
canonical-branch code. The operator's live `pos3/framework` has no
`handsoff-loop` and neither b33c0a8 nor e0b71cb (nor this) in its git
log. Until an owner-gated branch-merge / pos-sync lands it on the
running framework, this protects branch code only — it is INERT on
the operator's live session. This is the §7 owner-gated decision —
NAMED here, NOT enacted.

## 1. Spawn-surface inventory (grounded against canonical source)

- **§1a — already isolated production clients** (subloam-driver
  `driver.py`; upgrade-merge-resolver; workspace-sync resolver
  client; odd-extractor synthesis client): byte-unchanged
  (AC.PROMO.6).
- **§1b — already isolated handsoff-loop launch sites + adapter**
  (`_isolation.py`, `intake.py`, `goal_drive.py`, `orchestrator.py`;
  sealed b33c0a8/e0b71cb, AC.TPI.*): byte-unchanged. The promote
  LIFTS the adapter PATTERN into a new package; it does NOT edit the
  sealed §1b adapter or its launch sites.
- **§1c — non-`claude` subprocess sites** (`first_run_dispatch.py`,
  `first_run_helper.py`, `handsoff_loop/verify.py`): not kill
  vectors; byte-unchanged (AC.PROMO.6).
- **§1d — THE uncovered class** (the #5 doorway): dispatched-
  agent-authored `/tmp` test/judge/probe/re-harden harnesses that
  hand-roll a raw `subprocess.run(["claude","-p",...])`. Zero
  in-canonical-tree sites; UNBOUNDED-but-PATTERN-SINGULAR doorways.
  The fix is a shared surface + structural guard + env-var, not N
  file patches.

## 2. The proven mechanism — promoted, not re-invented

`subloam-driver` is a sealed pip package exporting the isolation
functions; `handsoff_loop._isolation` proves the import-and-inject
adapter pattern. The promote = lift that adapter pattern out of the
handsoff-loop package into a shared, importable surface. Method
(WHERE the surface lives + HOW the mandate is enforced) is the
builder's call — RESOLVED for this build: a new sibling tool package
`framework/tools/loam-spawn-isolation/` exporting
`spawn_isolated_claude` (mandated entry point) / `inject_isolation` /
`isolated_claude_argv` / `isolated_env` / `assert_loam_spawn_isolated`
(the structural mandate guard) / `canonical_src` (the out-of-tree
reach handle). It wraps the sealed subloam-driver functions verbatim
— zero drift, no new isolation machinery. The guard reuses the
sealed marker-guard discipline AND additionally rejects an argv
missing the empty-strict-MCP flag pair (the literal #5 pattern).

## 3. ODD

### 3.1 Objective

Every loam-adjacent `claude` spawn — explicitly including
dispatched-agent-authored test/judge/probe/re-harden harnesses — is
routable through ONE shared, importable, mandated
telegram-plugin-isolation surface such that no loam-adjacent spawn
(in-tree OR a hand-rolled `/tmp` harness) can SIGTERM a concurrently-
running operator session's Telegram poller; reusing the proven
subloam-driver primitive (no new mechanism), with a structural guard
so a regression that re-introduces an un-isolated spawn fails loudly,
plus the one-line `CLAUDE_PERSONA` belt-and-braces env-var.

Ladders to VALUE_PROPOSITION harness test — a harness that kills the
operator's only user-visible channel while doing background work
fails the harness test. Closing the doorway *class* is the
harness-value-bearing outcome.

### 3.2 Fence

**IN:** the new shared importable surface; the structural mandate
guard; the `CLAUDE_PERSONA` belt-and-braces env-var on it; the
extended acceptance suite incl. the dogfood-recursion closure;
normal canonical-loam build/seal discipline (plan-doc + manifest on
disk before apply, ODD-shaped ACs, one test file per AC).

**OUT (explicit):** §1a/§1b/§1c already-isolated / non-`claude`
sites' internals (AC.PROMO.6 — no churn); the upstream plugin-cache
hardening (owner-gated, separate); any token / `.env` / `access.json`
/ `.mcp.json` / channel / onboarding config change (sub-process-reach
narrowing only); ProgramBench / goal-refinement / reaper / launchd —
orthogonal. **NAMED OWNER-GATED, NOT PLANNED:** the branch-merge /
pos-sync / publish that would activate ANY fix on the operator's live
running framework. This plan does NOT do it.

### 3.3 Acceptance ladder

| AC | Outcome | Maps to |
|---|---|---|
| **AC.PROMO.1** (lead) | Sentinel holding the single-consumer poller slot SURVIVES a real harness-style ≥2-parallel `claude -p` multi-spawn routed through the shared surface (`.poll() is None`). Opt-in real-binary (`PROMO_REAL_CLAUDE=1`). | Operator poller survives the exact #5 spawn class. |
| **AC.PROMO.2** | An argv via the shared surface carries empty-strict-MCP isolation + zero telegram markers; env has token/API-key spellings absent AND `CLAUDE_PERSONA` set. Fast structural. | Structural guarantee + the independent env defense. |
| **AC.PROMO.3** (dogfood-recursion closure — STRUCTURAL, mandatory) | AC.PROMO.1's OWN test module is STATICALLY/AST-asserted to spawn via the shared surface with NO raw `subprocess.<spawn>(["claude",...])` — goes RED before the real-binary path can run. | THE recursion #5 was. Non-negotiable. |
| **AC.PROMO.4** | A loam-adjacent `claude` argv built WITHOUT the shared isolation raises loudly rather than silently shipping a kill-capable invocation. | Durability — the #1..#5 asymmetry cannot silently recur. |
| **AC.PROMO.5** | The surface is one-line importable by an arbitrary out-of-tree (`/tmp`-CWD) caller — verified by a real subprocess whose CWD is outside the canonical tree. If unreachable without re-architecture → §5 Halt-1 honest-negative, stated plainly, NOT papered "contained". | The mandate's teeth — reach the #5 harness class. |
| **AC.PROMO.6** | §1a/§1b/§1c sites byte-unchanged (diff vs manifest BASELINE). | Fence integrity. |

Honest-negative validity: a definite negative on AC.PROMO.1 or
AC.PROMO.5 is a VALID terminal outcome reported straight, NEVER
retried-to-green, NEVER papered as "contained" (F2 /
locked-design-not-license).

## 4. What this does NOT claim

1. Does NOT claim every disconnect cause is closed — closes the
   proactive-SIGTERM-by-unisolated-spawn vector for loam-adjacent
   spawns including the harness class.
2. Does NOT claim the official Telegram plugin is hardened
   (owner-gated upstream).
3. Does NOT claim per-event kill-receipt proof — AC.PROMO.1 proves
   the *outcome* (sentinel survives the harness-class multi-spawn)
   empirically.
4. **Does NOT claim the fix protects the operator's LIVE session.**
   It protects canonical-branch code; INERT live until §7's
   owner-gated merge/sync. Stated plainly, not softened.

## 5. Halt-and-surface log

1. **Halt-1 (mandate-unenforceable-for-/tmp-class):** NOT triggered.
   The new package's `src` is path-resolvable from an arbitrary CWD
   (the same resolution the sealed `_isolation.py` uses); a real
   `/tmp`-CWD subprocess imports it in one line (AC.PROMO.5 GREEN).
2. **Halt-2 (would-need-token/config-change):** NOT triggered. The
   contained argv+env mechanism is necessary-AND-sufficient
   (established by the sealed AC.LIPW.5/.6 + AC.TPI.*; the promote
   reuses the same construction). No token/access/channel/`.mcp.json`
   change.
3. **Halt-3 (fix is INERT without merge/sync):** TRIGGERED —
   load-bearing, surfaced, NOT softened. The operator's live
   framework lacks `handsoff-loop`; this + b33c0a8 + e0b71cb only
   protect canonical-branch code the operator's session does not
   execute. Almost certainly *why Telegram keeps dying despite the
   "fixes."* §7 owner-gated.
4. **Halt-4 (ODD violation in read surfaces):** NONE. §1a/§1b carry
   isolation under their sealed ACs; the harness class's absence of
   isolation is the bug being fixed, not a pre-existing in-tree ODD
   violation.

## 6. The dogfood-recursion — explicit closure

The #5 failure WAS: a harness built to test/re-harden the Telegram
fix spawned un-isolated `claude` and killed Telegram while purporting
to verify Telegram protection. AC.PROMO.1 must itself spawn real
`claude` (empirical poller-survival is the only honest proof).
AC.PROMO.3 makes it STRUCTURALLY IMPOSSIBLE for the fix's own
acceptance test to be the next #5: a static AST check on
AC.PROMO.1's own test module asserts its spawn construction routes
through the shared surface — if it hand-rolls a raw
`["claude","-p",...]`, AC.PROMO.3 goes RED *before* the real-binary
path ever runs. Closed for the verification of the fix itself, not
merely for production code. Encoded as a dedicated AC, not a method
note.

## 7. Named decision (surface to owner)

> The b33c0a8 + e0b71cb + this shared-mandate fix are/will-be
> canonical-branch code. The operator's LIVE pos3 framework has NO
> `handsoff-loop` and none of these commits in its git log. None of
> these fixes protect the owner's live session until a branch-merge
> / pos-sync / publish lands them onto the running framework. That
> merge/sync is owner-gated (substantial canonical change → the
> backup-pos3-before-canonical-affecting-sync discipline applies).
> This plan does NOT do it. It is the gating owner call and is very
> likely the real reason Telegram keeps dying despite the "fixes."

Recommendation: build the shared-mandate fix in canonical (contained,
normal seal class) AND surface the merge/sync as the parallel owner
decision — building the fix is necessary; *activating any fix on the
live session* is the owner-gated step that has been the missing link
across #1–#5.

**No method-level owner decision.** Where the surface lives + how the
mandate is enforced is the builder's call (RESOLVED §2). The fence,
reuse-the-proven-mechanism, the dogfood-recursion closure
(AC.PROMO.3), and local-seal-only are fixed.

## 8. Seal record (backfilled at cycle close)

- Fence anchor: single-component `framework/workspace-bootstrap/`
  (seal_test + sidecar there; admitted prefixes cover
  `framework/tools/` + `docs/plans/`; `docs/STATE.md` universal
  allowed_file). Mirrors the telegram-poller-isolation-fix +
  phase-b-intake-fix precedents on this exact branch tip.
- Seal register (backfilled):
  - manifest BASELINE: `ce9d830` (one commit earlier than the
    source-edit commit — see the method-deviation note below;
    functionally correct, the `ce9d830..SEAL` diff window captures
    exactly this amendment).
  - apply bookkeeping commit (manifest + sidecar + seal-test
    BASELINE bump): `40ba92b`.
  - source-edit commit (package + 6 AC tests + this plan-doc):
    `1c3f7da`.
  - AC.PROMO.6 test-text corrective (admit the amendment-ritual
    bookkeeping surface in the affirmative-side check; load-bearing
    §1a/§1b/§1c fence assertion unchanged): `a7ca729`.
  - deterministic seal commit: `ca7f715`.
- canonical `main` / `origin/main` unchanged across the cycle:
  `f7ccc3d` (== dispatch baseline; nothing pushed/merged/published/
  tagged; no prior commit reverted — b33c0a8/e0b71cb/ceb629b all
  still in history).
- Method-deviation (F2, surfaced not buried): `loam amend apply` was
  run before the source commit, so BASELINE pins `ce9d830` (the
  pre-build branch tip) rather than the source-edit commit's
  immediate predecessor as the prior cycles' convention does. Per
  critical-thinking-on-deviations the resolutions were enumerated
  (commit-source-then-seal vs reset-and-re-apply vs halt-surface);
  commit-source-then-seal was chosen — functionally correct (correct
  diff window, AC.PROMO.6 reads `baseline:` from the manifest, zero
  CDC impact), reversible, zero blast radius, no history rewrite for
  a purely cosmetic gain. Builder-resolvable per
  test-against-operational-objective; not an owner escalation.
- AC.PROMO.1 real-binary result (the load-bearing empirical proof,
  run at sealed HEAD `ca7f715`): 4 parallel real `claude -p` spawns
  through the shared surface all `rc=0` with genuine result
  envelopes; the single-consumer-poller-slot sentinel was ALIVE
  (`.poll() is None`) after the harness-style multi-spawn.
