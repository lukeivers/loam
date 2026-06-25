# loam v1.7.0 — CHANGELOG

**Class:** MINOR over published v1.6.0 (`next_MINOR(v1.6.0) = v1.7.0`).
**Quality tag:** MIXED — END-USER value for the deliberate-reasoning + memory
halves, with the headline capability shipping **DEFAULT-OFF (proven, opt-in)**.
**Migration:** `no-op` (`docs/state-migrations/v1-7-0-deliberate-reasoning-and-memory-supersession.migration.yaml`).
**Plan-doc:** `docs/plans/release-integration-deliberate-reasoning-and-memory-supersession.md`.

> **Objective sentence —** loam can deliberately reason: a metacognitive gate
> decides per-turn when a task warrants escalated reasoning and runs an
> evidence-bound re-entrant loop, triggered by the situation rather than
> conversation keywords and wired live (default-OFF); and loam's memory keeps
> the current truth current — a superseded ruling is filtered out of recall by
> validity interval while its history stays queryable.

---

## Headline — deliberate-reasoning (NEW component, default-OFF)

`framework/deliberate-reasoning/` is introduced whole in this release (it does
not exist at the v1.6.0 tag). It ships at its own **0.1.0**, OUT of the install
graph and OUT of the lockstep set this cut (mirrors how v1.6.0 shipped
`capability-refresh` / `knowledge-pack` at 0.1.0 — D-LOCK).

**What a user can now do (opt-in):** run the `process_turn` production
entry-point and get an escalate-or-not decision plus an evidence-bound
re-entrant loop, with escalation triggered by the *situation* (the structure of
the pending action + recent results) rather than conversation keywords.

This release ships **slices 1 AND 3** of the deliberate-reasoning sequence —
NOT a complete 1-through-3 run. There is no slice 2 in this window: a self-model
plan (slice 2a) was ratified but never sealed a runtime amendment, and is
explicitly deferred to a future cycle.

- **Slice 1 — metacognitive gate + evidence-bound re-entrant loop.** A
  deterministic, LLM-free per-turn escalate decision (`gate.py`); an adversarial
  evidence-bound re-entrant loop (`loop.py`) with a no-degradation guard that
  returns the original draft when critique finds no evidence-backed improvement;
  a `process_turn` production entry-point under a default-OFF gate (`turn.py`); a
  frozen, pre-registered experiment with a blind judge. (ACs AC.MGRL.{1-5} +
  AC.MGRL.OA.)
- **Slice 3 — situation/behaviour triggers + live PreToolUse wiring.** Replaces
  the conversation-keyword gate substrate with structural situation/behaviour
  triggers (`signals.py`, `escalation.py`) — UNBOUNDED_OP / REPEAT_FAILED /
  MACHINE_IRREVERSIBLE / HIGH_BLAST_RADIUS — and adds a live PreToolUse-shaped
  adapter (`wiring.py`) that composes with the existing guard pattern
  (fail-open, warn/block). A per-turn LLM self-assessment escalation ships
  **designed + default-OFF** behind its own independent switch; the v1 floor is
  LLM-free. The keyword-trigger substrate is retained behind an opt-in
  deprecation path. (ACs AC.TRIG.{1-4} + AC.WIRE.1, with AC.MGRL.OA carried
  forward.)

**Honesty flags (carried per plan §9 / F2):**
- It ships **default-OFF**. The honest END-USER value is "the capability exists
  and is proven, opt-in" — NOT "on by default for every user." Not an always-on
  behaviour change.
- **Slices 1 and 3**, not a complete 1-3 sequence — slice 2 never shipped.
- The pre-registered RCT salience tie-break probe came back **null and was
  dropped** (recorded in the register). That is the falsification discipline
  working — it is NOT listed here as a feature.

---

## memory-supersession + salience-eval (extends sealed primary-persona)

loam's memory now **keeps the current truth current.**

- **Validity-interval supersession (SUP, proven):** recall FILTERS superseded
  records out of current recall (current-over-stale) instead of merely demoting
  them (AC.SUP.1); an explicit `as_of` query returns history (AC.SUP.2); the
  prior record's interval closes at the new record's creation (AC.SUP.3);
  reversible via un-mark (AC.SUP.5).
- **E2E answer-correctness gate (proven):** `framework/primary-persona/eval/
  harness.py` + AC.E2E.{1,2,3} — answer-level correctness, blind-judge, frozen
  QA probe.

**What a user sees:** a superseded ruling no longer surfaces as current recall,
while its history stays queryable `as_of` a past time.

---

## Tilth-side hands-off-loop slices (workspace-bootstrap fence)

Three slices land in `framework/tools/handsoff-loop/` (measurement-class tool at
0.0.0, lockstep-EXCLUDED by policy), sealed under the `workspace-bootstrap`
component fence:

- **Slice DF — design-first front stage:** N candidate designs + a
  user-validation gate before build.
- **Slice HB — build-time progress heartbeat:** channel-aware progress
  heartbeat via an injected `notify_fn`.
- **Slice DF6 — non-tech-user visible candidates (AC.DF.6):** frame candidate
  designs for the user's tech level — default non-tech, never offer CLI/daemon
  to a non-tech user. Directly serves the per-user-translation prime lens.

---

## Release-internal housekeeping (no runtime capability)

- **dev-sdlc pbret-register:** registers two v1.6.0 retirement-record docs as
  justified retirement-sweep keeps + adds a retirement-sweep test. Bookkeeping
  for an already-shipped v1.6.0 dev-tooling retirement (the sealed
  retirement-plan under `docs/plans/sealed/`); zero new user-visible behaviour.
- **dev-sdlc seal-fence BASELINE correctives** — advance interleaved-corrective
  baselines so the slice-1 seal fence is clean. Mechanical, audit-only.
- **§14 register backfills** — per-decision SHA backfills into method-decision
  registers. Doc-only.

---

## Versioning

- Lockstep bump: `docs/ACTIVE_MINOR` 1.6.0 → 1.7.0, the 31 in-scope
  `pyproject.toml` version fields 1.6.0 → 1.7.0, and the meta-package
  `loam --version` literal 1.6.0 → 1.7.0 — in one source-of-truth prep commit.
- Out of lockstep this cut: `deliberate-reasoning` (0.1.0, out-of-graph,
  D-LOCK), `handsoff-loop` (0.0.0, measurement-class, policy-excluded).
- Zero BREAKING changes — deliberate-reasoning is a pure additive default-OFF
  component; memory-supersession composes on existing seals with reversible
  un-mark and preserved history. No public surface removed or changed
  incompatibly.

---

## Standing debt (named, not hidden)

Shipping a new component (`deliberate-reasoning`) OUT of the install graph +
lockstep repeats the v1.6.0 pattern. That is now a standing follow-on for two
consecutive minors' worth of new components — folding them into the install
graph + lockstep is a named future item, not permanent drift.
