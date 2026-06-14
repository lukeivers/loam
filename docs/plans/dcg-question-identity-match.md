# dcg-question-identity-match — the decision-claim gate must match QUESTION IDENTITY, not shared claim-language

PATCH amendment. A correctness fix to the decision-claim contradiction
gate (`framework/hands-off-lifecycle/hooks/keep_pace/claim_guard.py`,
`check_decision_claims` / `_declared_vocab_overlap`). Version derives at
release time (feedback_version_numbers_at_release_time).

Owner ruling **D** (recommendation = law): the gate's
contradiction-detection must require QUESTION-IDENTITY match, not merely
shared claim-language. A genuinely-open question (no ruled record for
its identity) must NOT be flagged as contradicting an unrelated ruled
record that happens to share phrasing. Real same-question
contradictions must STILL be caught (do not over-loosen — that is the
gate's purpose).

---

## §1 — The blocker (Tier-0 reproduced)

The GUARD-SWEEP FLOOR class-6 member
(`framework/hands-off-lifecycle/tests/test_AC_DCG_*.py`, declared in
`docs/plans/guard-floor.yaml`) runs at EVERY seal. One of its tests —
`test_AC_DCG_OA_live_ledger_gate_replay.py::test_AC_DCG_OA_genuinely_open_question_passes_live`
— FAILS, so the floor fails, so every pending seal is blocked.

Reproduced under the project venv
(`.venv/bin/python -m pytest framework/hands-off-lifecycle/tests/test_AC_DCG_OA_live_ledger_gate_replay.py`):
`1 failed, 20 passed`. The failing test derives a genuinely-OPEN
question from the live ledger at test time (Leg A: the on-file record
`2026-06-09-which-model-runs-substantive-loam-build-work...`, whose
status is `superseded` — i.e. not `ruled`, genuinely not-settled), runs
it through the production `gate()`, and the gate FALSE-POSITIVES: it
flags the open question as contradicting the UNRELATED ruled record
`"What happens to the FBM co-citation spread and power-law activation
after the June-7 eval?"`.

### Root cause (Tier-0, instrumented)

`_declared_vocab_overlap` counts EVERY shared declared-vocabulary token.
The open question's subject resolves the FBM ruled record on the tokens
`{and, happens, loam, what}` — pure generic claim-language and one
ubiquitous domain token (`loam` appears in the declared vocabulary of
5 of 7 live ledger records). `>= 2` such tokens cleared the threshold,
so the gate declared a contradiction with a question that shares NO
identity with the open one.

The gate already had the right INTENT (the `>= 2` overlap was meant to
defeat a "one-common-word brush") but the wrong SIGNAL: a count over
ALL declared tokens, including ubiquitous domain tokens and generic
claim-language, does not measure question identity.

---

## §2 — Primitive-check (REQUIRED)

- **Lens 1 (Claude-leverage):** none — this is a deterministic,
  stdlib-only string/regex guard on the send hot path. No LLM, no API
  call (preserves D4 of the parent FBM-correctness cycle: no model call
  anywhere in the send path). A Claude primitive (the reserved KP10
  `claude -p` register judge) is the FUTURE semantic layer; this fix
  stays in the deterministic floor it belongs to.
- **Lens 2 (harness / primary-persona):** the gate IS a primary-persona
  protection surface (it prevents the persona re-opening a settled
  ruling to the user). The fix raises its precision without lowering
  its recall — strictly better translation-protection.
- **Native primitive already doing this?** No. The corpus-frequency
  identity signal is computed from the existing `decision_ledger`
  surface (`iter_decisions` + `memory_dir_for_workspace`) already
  imported by the sibling lazy-query; no new primitive is introduced.

---

## §3 — Decision D-DCGID.1 (the fix mechanism)

**Ruled by the dispatch (recommendation = law): require question-identity,
not shared claim-language.**

Mechanism (builder's call within the ruling): replace the
all-declared-token overlap count with a **distinctive-identity-token**
overlap. A subject↔record overlap token counts toward identity only
when it is BOTH:

1. **not a generic stopword** — a static set of English function words
   + decision-state claim-language (`question`, `undecided`, `open`,
   `happens`, `what`, `which`, `remains`, …). Deterministic, domain-
   agnostic.
2. **not corpus-ubiquitous** — its DECLARED-vocabulary document
   frequency across the FULL live ledger is at or below a ubiquity
   cutoff (≤ 40% of records). This is what drops the ubiquitous domain
   token `loam` WITHOUT hardcoding domain knowledge — the filter learns
   the corpus's ubiquitous tokens at query time and generalizes to any
   workspace's ledger.

The contradiction threshold stays `>= 2` — now over distinctive
identity tokens, not raw shared tokens.

**Why corpus-frequency is load-bearing (Tier-0):** a stopword-only
filter was tested and FAILS — the FP-open question still resolves the
unrelated *memory-north-star* ruled record at overlap 2 on
`{build, loam}` because `loam` is a ubiquitous domain token a static
stopword list cannot anticipate without baking in brittle domain
knowledge. The corpus-frequency cutoff drops `loam` (5/7 records) and
the FP collapses to overlap 1 → PASS.

Corpus frequency is computed over the FULL ledger via a lazy read
(`iter_decisions(memory_dir_for_workspace(cwd))`) — the same
cross-component lazy-import discipline (`D-KP9.1`) the existing
`_default_ledger_query` uses; any failure propagates to the gate's
fail-open envelope (a frequency-read error never blocks a send).

### Validation against real data (Tier-0, pre-build)

| case | required | distinctive overlap (max ruled) | verdict |
|---|---|---|---|
| FP-open `"Which model runs substantive loam build work…"` | PASS | 1 (`build`; `loam` dropped as ubiquitous) | PASS ✓ |
| genuine re-open of the FBM ruled question | FLAG | 7 (`fbm, co, citation, spread, power, law, activation`) | FLAG ✓ |
| genuine re-open of the Tilth raise ruling | FLAG | 2 (`raise, tilth`) | FLAG ✓ |

---

## §4 — Scope / fence

ONE sealed component: **hands-off-lifecycle**. The only source edit is
to `framework/hands-off-lifecycle/hooks/keep_pace/claim_guard.py`. Tests
land in `framework/hands-off-lifecycle/tests/`. No edit outside this
fence. The live ledger (`~/pos3/workspace/.loam/memory/decisions/`) and
the `decision_ledger` module are READ-ONLY ground truth, never edited.

Halt-and-surface if the fix would require an edit outside
hands-off-lifecycle.

---

## §5 — Acceptance criteria (AC.DCGID.*)

- **AC.DCGID.1** — `_declared_vocab_overlap` (or its replacement) counts
  a shared token toward question-identity only when it is neither a
  generic stopword nor corpus-ubiquitous (declared-vocabulary document
  frequency ≤ the ubiquity cutoff over the full ledger). A unit test
  with a synthetic record set asserts: a token shared but ubiquitous
  does NOT count; a distinctive shared token DOES.

- **AC.DCGID.2** — `check_decision_claims`: a genuinely-open question
  whose subject shares ONLY generic claim-language + ubiquitous tokens
  with an unrelated ruled record draws NO steer (synthetic ledger via
  the `ledger_query=` seam — deterministic, no live dependency).

- **AC.DCGID.3** — `check_decision_claims`: a draft that re-opens the
  SAME question as a ruled record (sharing the record's distinctive
  identity tokens) STILL draws the `decision-claim-contradicts-ledger`
  steer (synthetic ledger via the seam). Recall is preserved.

- **AC.DCGID.4** — fail-open preserved: a corpus-frequency read error
  (or any internal error in the identity filter) yields NO steer and
  never raises out of `check_decision_claims` into the send path
  (synthetic seam that raises; assert empty result, no exception).

- **★ AC.DCGID.OA** (outcome-altitude: true) — through the production
  `gate()` entry point against the LIVE ledger with NO pre-arranged
  state, run with the hook's production cwd (`~/pos3`):
  (a) the exact false-positive pair — the genuinely-open
  `"Which model runs substantive loam build work…"` question vs the
  unrelated FBM ruled record sharing claim-language — does NOT produce a
  `decision-claim-contradicts-ledger` reason; AND
  (b) a genuine same-question contradiction (re-opening the FBM ruled
  question, sharing its distinctive identity tokens) DOES produce that
  reason.
  Skips when the live ledger is absent (CI / fresh machine), matching
  the existing DCG.OA live-replay convention.

The existing class-6 floor test
(`test_AC_DCG_OA_genuinely_open_question_passes_live`) returns to GREEN
as a consequence — it is the live-derived instance of AC.DCGID.OA(a).

---

## §6 — Build steps

1. Edit `claim_guard.py`: add the stopword set + corpus-frequency
   ubiquity filter; route `_declared_vocab_overlap` (or a new
   `_identity_overlap`) through it; thread the corpus-frequency source
   as a lazy full-ledger read with fail-open. Map every new line to an
   AC.DCGID.* in a comment.
2. Author `test_AC_DCGID_1_*` … `test_AC_DCGID_4_*` and
   `test_AC_DCGID_OA_*` in `framework/hands-off-lifecycle/tests/`.
3. Run the new tests + the full class-6 floor glob under the venv;
   confirm GREEN (the previously-failing live test now passes).
4. Commit source + tests as `fix(hands-off-lifecycle): …`.
5. `loam amend validate` → `apply` → `seal`.
6. Backfill §14 with the seal SHA.

---

## §14 — Seal register

- plan-doc commit: `f93d07d9`
- source/test commit: `10f1519f`
- apply commit: `4a3bcdc8`
- seal commit: `cb3fd8d4`
- AC.DCGID.1–4 + ★ AC.DCGID.OA: GREEN at seal (10 new tests; the
  previously-failing GUARD-SWEEP FLOOR class-6 live test
  `test_AC_DCG_OA_genuinely_open_question_passes_live` returned to
  GREEN as the live-derived instance of AC.DCGID.OA(a)).
