# Intake LLM intent-extraction seam + leg-4 adjustment

Working directory: `/Users/lukeivers/loam-wt-seam` (isolated worktree, branch
`plan/intake-llm-intent-seam`, off `main` at `b8817c71` — the merged intake
leverage-close redesign cluster, amendments #166-#171).

## 1. Source of the work

The loam 1.0 acceptance smoke has had its EXTRACTION layer driven clean over six
regex-hardening rounds (amendments #166-#171). The SEVENTH re-run
(`docs/experiments/loam-1.0-acceptance-smoke-rerun7.md`, top-line
**READY-WITH-GAPS**) shows the strongest grid yet — every deterministic + most
soft dimensions PASS — but ONE soft dimension is still PARTIAL across ALL THREE
variants:

  - `four-step-loop-ran` — **PARTIAL on A, B, and C.** Legs 1-3 (infer → propose
    → surface-and-check) are present and clean. **Leg 4 — adjust from the answer
    — is absent.** After the user confirms, loam delivers a closing pitch
    IDENTICAL to the proposal rather than refining/extending from what the
    confirmation revealed. On variant C this also trips `protection-floor-held`
    FAIL: the paralegal raised a concrete doubt ("does it actually know how to
    read a Bluebook citation?") and the close ignored it, implying an unverified
    capability.

The rerun6 seal narrative already surfaced this to the owner as the ONLY
remaining clear-direction gap and named its two non-regex facets:
(1) leg 4 (loam ADJUSTS from a hedged/embedded-correction answer or a post-close
follow-up); (2) the judge's standing wish that the proposal NAME a DEEPER
inferred end-intent than the literal ask. Both want a richer conversational
close than deterministic regex distillation can produce on novel free-form
phrasing — six rounds of regex hardening on novel phrasings are diminishing
returns.

The owner RATIFIED the fix (Telegram 13398, "Agree with you"): BUILD a scoped,
spawn-isolated, FAIL-SOFT LLM intent-extraction seam that replaces the brittle
regex distillation as the PRIMARY path AND enables leg-4 adjustment; HOLD the
1.0 label until the acceptance smoke reads clean-READY.

This is NOT an open design fork. The TARGET behaviour is the owner's
already-specified four-step loop (infer → surface-and-check → adjust; close on
ONE thing; no interrogation; don't over-engineer; featherlight). This cycle
makes leg 4 real and dissolves the recurring extraction misses with a scoped
model call, adds an AC + test per behaviour, then RE-RUNS the smoke to verify
`four-step-loop-ran` flips PARTIAL → PASS across A/B/C and the verdict reaches
READY.

## 2. Fence (single component — declared single-component)

**workspace-bootstrap** — entirely within
`framework/workspace-bootstrap/src/loam/workspace_bootstrap/`:

  - NEW module `intent_extract.py` — the LLM intent-extraction seam (Protocol +
    real spawn-isolated `ClaudeIntentExtractor` + a disabled-by-default stub +
    register/reset seam), mirroring the proven `deep_role_research.py` /
    `deep_role_research_provider.py` shape (clean interface + injectable default
    + graceful degradation).
  - `translate_in_intake.py` — distillation calls the extractor FIRST (fail-soft
    to the existing regex `_distill_intent`); leg-4 adjustment turn added after
    the confirm/check gate on every confirmed path.
  - tests: NEW AC test files (AC.INTENT.*) + the outcome-altitude cold walk.

Seal-test: `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`.
Sidecar: `framework/workspace-bootstrap/tests/SEAL_COMMIT`.

The re-run EXECUTES the smoke harness (`framework/tools/loam-acceptance-smoke/`)
unchanged; the smoke runner is widened ONLY to REGISTER the real intent-extractor
for the role-play walk (the same way it wires the real research provider) — and
that one-line wiring is its own universal-admitted touch IF it falls inside the
smoke component, OR is surfaced as a second fence if it requires editing the
smoke component's sealed source. The updated run-report lands at
`docs/experiments/` (universal-admitted).

## 3. Halt-and-surface BEFORE / DURING build

- A genuine design fork in the seam (reasonable people differ) → surface,
  don't guess.
- A change needing a component beyond workspace-bootstrap (e.g. the smoke
  registration must edit the smoke component's sealed source) → surface as a
  second fence rather than silently widening.
- Any `claude -p` that cannot be spawn-isolated → HALT (never spawn un-isolated).
- An ODD violation in the seam or surrounding code → halt + surface.
- The smoke not reaching READY after the seam + a clear-direction follow-up →
  surface the honest state (never manufacture READY).

## 4. Named decisions (builder's call, recorded)

- **D-SEAM-1 — the extractor is an injectable Protocol with a DISABLED default.**
  `default_intent_extractor()` resolves to a `DisabledIntentExtractor` that
  always declines (returns no extraction) so the DEFAULT distillation path stays
  pure regex — no spawn, no network, existing distillation suite unaffected. The
  real `ClaudeIntentExtractor` is registered explicitly (by the smoke runner /
  the production CLI). Mirrors `register_research_provider`. Rationale: keeps the
  baseline featherlight + offline-clean; the model call is opt-in at the seam,
  exactly the owner's "one small call per onboarding" bound.

- **D-SEAM-2 — fail-soft is layered at the call site.** `_distill_intent` gains a
  wrapper (`_distill_intent_via_seam`) that tries the extractor, and on ANY
  failure (unavailable / timeout / non-zero exit / unparseable / empty) falls
  back to the existing deterministic `_distill_intent`. The regex path is the
  fallback, never deleted. Bounded: the extractor is consulted at most ONCE per
  distillation; the leg-4 adjustment reuses the SAME single extraction (no second
  round-trip). Rationale: onboarding must never break/hang on a model failure.

- **D-SEAM-3 — the spawn mirrors the proven research-subagent dispatch.**
  `ClaudeIntentExtractor` lazy-imports `loam_spawn_isolation.spawn_isolated_claude`,
  dispatches `claude -p <prompt> --model sonnet --output-format json
  --permission-mode bypassPermissions` with a HARD timeout, parses the
  `{"result": ...}` envelope, and raises an `IntentExtractUnavailableError`
  sentinel the caller catches. No Anthropic SDK / API key path. Mirrors
  `ClaudeSubagentResearchSource` exactly. Rationale: reuse the sealed isolation
  primitive verbatim — the Telegram-slot protection is non-negotiable.

- **D-SEAM-4 — leg 4 is a visible adjustment turn on every confirmed path.**
  After the verify gate, loam reads (via the SAME single extraction or the user's
  confirmation text) the DETAIL or DOUBT the confirmation added, and emits ONE
  adjustment turn that reflects it — folded into the close so the close is no
  longer a verbatim restatement. On a follow-up DOUBT (variant C shape) the
  adjustment ADDRESSES the doubt honestly (does not invent capability →
  protects the protection-floor). Bounded: ONE adjustment turn, no extra model
  round-trip, no interrogation (it is a statement, not a new question).
  Rationale: this IS the loop's learn step made real; bounded + cheap per the
  owner's ratification.

## 5. Acceptance criteria (each behaviour → a NAMED AC + a test)

New AC family **AC.INTENT.\*** (the LLM intent-extraction seam + leg-4
adjustment; ladders up from AC.INTAKE-ECHO.1 (distillation quality) and
AC.ONCLOSE.1/.4 (surface-and-check + person-specific close) — these add the
PRIMARY LLM path + the loop's fourth leg):

- **AC.INTENT.1 — LLM extraction is the PRIMARY distillation path when enabled.**
  When a real intent-extractor is registered, the distillation consults it FIRST
  on the raw reply, and a usable extraction is used as the distilled intent
  (preferred over the regex result). Test: with a stub extractor that returns a
  fixed marker intent for a free-form reply the regex would distill differently,
  the proposal/close carries the EXTRACTOR's intent, not the regex's.

- **AC.INTENT.2 — fail-soft fallback to the regex path.** On extractor
  unavailable / timeout / error / empty / unparseable, distillation FALLS BACK to
  the existing deterministic `_distill_intent`; `run_translate_in_intake` never
  raises and never hangs. The extractor is consulted at most ONCE per
  distillation. With NO extractor registered (the default), the path is pure
  regex (no spawn). Test: (a) an extractor that raises → the regex distillation
  result is used + the run completes; (b) the default (disabled) extractor → the
  existing regex distillation output is byte-identical to pre-seam.

- **AC.INTENT.3 — spawn-isolation + no API key (the real extractor).** The real
  `ClaudeIntentExtractor` dispatches its one bounded call EXCLUSIVELY through
  `loam_spawn_isolation.spawn_isolated_claude` (argv-injected `--strict-mcp-config`
  + empty mcpServers; ANTHROPIC_API_KEY + TELEGRAM_BOT_TOKEN scrubbed) with a hard
  timeout; it imports no Anthropic SDK and reads no API key. Test: with
  `spawn_isolated_claude` monkeypatched to a recording fake, the extractor's argv
  passes `assert_loam_spawn_isolated`, a timeout is passed, and the module imports
  no `anthropic`.

- **AC.INTENT.4 — leg 4 (adjust-from-the-answer) is visible on every confirmed
  path.** After the verify gate, the transcript/close contains an adjustment turn
  that reflects detail or addresses a doubt the confirmation raised — the close is
  NOT a verbatim restatement of the pre-confirmation proposal. On a follow-up
  doubt about capability, the adjustment ADDRESSES the doubt honestly (no invented
  capability). Test: a scripted confirm that adds detail → the close text reflects
  the added detail; a scripted confirm that raises a capability doubt → the close
  acknowledges/answers the doubt and makes no unqualified capability claim.

- **AC.INTENT.S — outcome-altitude cold walk (the four-step loop, real
  entry-point).** `marked outcome-altitude:true.` Driving the REAL
  `run_first_run_intake` (no pre-arranged state, isolated throwaway home) with a
  scripted role-play answerer whose confirmation adds detail AND raises a doubt
  produces a terminal `IntakeResult` whose transcript makes ALL FOUR legs visible
  (infer / surface-and-check / confirm / adjust) and whose close addresses the
  doubt. Test: the cold walk asserts the four legs are present in the transcript
  + the close references the added detail / answers the doubt, with no STUB
  pre-arranged distillation.

## 6. Build steps (order)

1. NEW `intent_extract.py`: `ExtractedIntent` dataclass, `IntentExtractor`
   Protocol, `IntentExtractUnavailableError`, `DisabledIntentExtractor` (default),
   `ClaudeIntentExtractor` (real spawn-isolated), `default_intent_extractor()` /
   `register_intent_extractor()` / `reset_intent_extractor()`.
2. `translate_in_intake.py`: `_distill_intent_via_seam(raw)` wrapper (extractor
   first, fail-soft to `_distill_intent`); route the three distillation callsites
   through it; add the leg-4 adjustment turn after the verify gate on every
   confirmed path (CLEAR/PARTIAL + the ladder); thread an optional
   `intent_extractor` parameter through `run_translate_in_intake` defaulting to
   `default_intent_extractor()`.
3. Thread `intent_extractor` through `run_first_run_intake` (default the disabled
   extractor; the smoke registers the real one).
4. AC tests: AC.INTENT.1 / .2 / .3 / .4 / .S (one file each).
5. Run the touched tests + the existing distillation suite (must stay green —
   the default path is byte-identical regex).
6. `loam amend validate` → `loam amend apply` → `loam amend seal`.
7. Backfill STATE + roadmap §8.
8. RE-RUN the acceptance smoke (the real role-play walk wires the real extractor),
   verify `four-step-loop-ran` PASS across A/B/C + verdict READY, write the
   run-report, surface.

## 7. Out of fence

- Editing the sealed `loam-init/` component, `deep_role_research*.py` gating, the
  seed-writer, or `docs/spec/`.
- Pushing or merging — owner-gated; the dispatcher handles merge-on-seal + the
  READY surface.
