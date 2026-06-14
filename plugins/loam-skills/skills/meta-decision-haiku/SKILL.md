---
description: "When the persona hits a genuinely BORDERLINE rule-application call — a small, bounded set of meta-decisions where reasonable judgment could go either way and the persona's own read might be biased by what it wants to do next — invoke an impartial third-party arbiter: a Haiku model called via `claude -p` (the subscription path, NO API key) that rules on the borderline case from a neutral standpoint. The trigger list is DELIBERATELY BOUNDED (does this need a plan-doc? is this a real principle-conflict needing the M5 four-step process? is this dispatch scope-only or method-smuggling? is this claim Tier-0-verified or a guess? is this work in-scope-authorized or owner-gated?) so the arbiter stays OFF the per-action hot path — it is a borderline-call tiebreaker, not a gate on every action. Use ONLY when the call is genuinely borderline AND on the bounded list; a clear-cut call needs no arbiter."
---

# meta-decision-haiku

An impartial borderline-rule arbiter. When the persona faces a
genuinely borderline meta-decision — one of a small, bounded set
where reasonable judgment could go either way, and where the
persona's own read risks being biased by what it wants to do next —
this skill calls a neutral Haiku model (via `claude -p`, the
subscription path, no API key) to rule on the borderline case from a
standpoint with no stake in the outcome.

This is the operational arbiter for loam's M5 (principle-conflict
resolution) — the one place the candidate puts an LLM deliberately in
the loop, scoped to a bounded borderline-call list and held OFF the
per-action hot path. It is NOT a gate that fires on every action; it
is a tiebreaker invoked only when the call is genuinely borderline.

## What this skill captures

The honest partition (D-PFSE.1): M5's four-step conflict process is
interior cognition with no observable artefact, so it cannot be
mechanically enforced without an LLM judge on every action — which
would collide with the hook-latency budget. The resolution is to NOT
put an LLM on every action, but to provide an impartial arbiter for
the genuinely-borderline subset, invoked by judgment.

The BOUNDED trigger list (the only cases this arbiter is for):

1. **Plan-doc needed?** Is this work large/risky enough to require a
   plan-doc before code, or is it a small surgical edit that does
   not? (Borderline when the work sits near the plan-before-code
   threshold.)
2. **Real principle-conflict?** Do two principles genuinely conflict
   here such that the M5 four-step process is warranted, or is one
   clearly dominant? (Borderline when both principles look live.)
3. **Scope-only or method-smuggling?** Does this dispatch prompt
   carry objective + fence + constraints only, or has method leaked
   into the acceptance? (Borderline when a constraint reads close to
   a method statement.)
4. **Verified or guess?** Is this specific claim (count / SHA /
   timestamp) Tier-0-verified, or must it be marked a guess?
   (Borderline when the persona is moderately but not fully
   confident.)
5. **In-scope-authorized or owner-gated?** Is this action inside
   already-authorized scope (proceed autonomously), or is it
   critical-call / public-action / financial (owner-gated)?
   (Borderline when the action is adjacent to a gated class.)

A call OUTSIDE this list, or a call that is CLEAR-CUT, does NOT use
the arbiter. The bound is the design — an unbounded arbiter would
become a death-by-latency per-action judge, exactly what the
partition forbids.

## When to use

Invoke the arbiter when BOTH hold:

- The decision is one of the five bounded triggers above; AND
- The call is genuinely borderline — the persona's own read is
  uncertain, OR the persona notices its read might be biased toward
  the action it wants to take next (the bias check is the real value;
  an impartial third party has no stake in the next action).

Do NOT invoke when:

- The call is clear-cut (no arbiter needed — decide and move).
- The decision is outside the bounded list (the arbiter has no remit
  there; widening the list is a plan-doc change, not an ad-hoc call).
- The action is on the per-action hot path (the arbiter is a
  judgment-time tiebreaker, never a gate fired on every tool call).

## How the persona applies it

1. **Confirm the call is on the bounded list AND genuinely
   borderline.** If either fails, do not invoke — decide directly.
2. **Frame the borderline case neutrally.** State the decision, both
   plausible answers, and the relevant signals (scope-confidence,
   reversibility, blast radius, audience, time pressure, information
   asymmetry — the M5 signal list) WITHOUT leading toward the answer
   the persona prefers.
3. **Call the arbiter via `claude -p` with the Haiku model.** The
   invocation routes through loam's subscription `claude -p` client
   (the same path loam uses for every LLM call — NO Anthropic API
   key, per `feedback_no_anthropic_api_key`). Haiku is chosen
   deliberately: the arbiter call is a cheap, fast, bounded judgment,
   not a heavy synthesis — Haiku's tier matches the task
   (`model-rationale: haiku — impartial bounded borderline-call
   tiebreaker, cheap + fast, no heavy synthesis`).
4. **Take the verdict as a tiebreaker, not a command.** The arbiter
   surfaces a neutral read; the persona retains the call (CEO/CTO —
   the arbiter is heard, not obeyed). When the arbiter's read
   contradicts the persona's strong prior, that contradiction is M5
   step-4 input — surface it.
5. **Record the borderline resolution when it lands.** If the
   conflict is written down (a plan §-conflict entry or a
   decision-ledger record), it carries the M5 four named steps (name
   conflict / name signals / make call / surface if non-obvious) —
   the recorded-conflict template leg of the partition.

## Graceful degradation

When `claude -p` is unavailable (no subscription session, offline):

1. The arbiter is best-effort — its absence NEVER blocks the
   decision. The persona falls back to running the M5 four-step
   process in-head and recording the resolution.
2. The bias check (the arbiter's real value) is approximated by the
   persona explicitly naming the action it wants to take next and
   asking whether that want is steering the read — the
   self-administered version of the impartial-third-party check.
3. No API-key path is ever used as a fallback — the subscription
   `claude -p` client is the only sanctioned LLM surface.

## Composition

- **Loam's M5 (principle-conflict resolution)** — this skill is M5's
  operational arbiter. M5 ships as a named manifest primitive + this
  arbiter + a recorded-conflict template; the behavioural four-step
  stays advisory (interior cognition), and the arbiter is the
  borderline tiebreaker.
- **Loam's F4 (scope ↔ confidence)** — the "genuinely borderline"
  gate IS a scope-confidence read: invoke the arbiter only when
  confidence in the call is low enough that an impartial read adds
  value.
- **Loam's `feedback_no_anthropic_api_key`** — the arbiter routes
  through `claude -p` (subscription), never the Anthropic SDK + an
  API key.
- **Loam's F3 model-rationale discipline** — the Haiku selection
  carries a `model-rationale` line (cheap + fast bounded tiebreaker),
  the audit trail on a non-default model choice.
- **Loam's coworker-relationship framing** — the arbiter is heard +
  respected but does not override; the persona (CTO) retains the call
  under the owner (CEO).

## Out of scope

- Per-action enforcement of any principle (the arbiter is a
  judgment-time tiebreaker, never a per-action gate — that is the
  whole point of the bounded list).
- Widening the bounded trigger list (a plan-doc change, not an
  ad-hoc call — an unbounded arbiter is a latency-blowing per-action
  judge).
- Heavy synthesis / research (Haiku's tier is for the cheap bounded
  call; research routes through the deep-research surface).
- Replacing the persona's judgment (the arbiter informs; the persona
  decides; the owner has the final word on gated classes).
