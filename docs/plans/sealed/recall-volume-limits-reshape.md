# Recall volume-limits reshape (cycle 1) — floor + byte budget replace the count caps

Per `docs/plans/recall-volume-limits-reshape.md` (build-ready pending owner
nod on the §3 budget-derivation call) and the ratified rulings
`workspace/.loam/memory/decisions/2026-07-08-memory-recall-volume-limits-fable-review-rulings.md`
(owner accepted items 1/2/4/5; item 3 refined + pending) + the Fable audit
`workspace/strategy/memory-recall-volume-limits-and-cap-bias-2026-07-08.md`.
Single-component amendment on the EXISTING `framework/primary-persona/`
component; advances the sidecar. Composes on S2 (relevance-threshold recall)
and S4 (situational rules store + trigger seam).

Tier-0 finding pinned at plan-authoring (finishes S2's half-landed
conversion): the count still silently determines the discovered set on three
surfaces the S2 threshold change never reached — the corpus SQL candidate
window `candidate_limit = max(num_results*5, num_results)` (`corpus_index.py`)
AND the `rest_out[:num_results]` truncation (a DOUBLE count gate on the corpus
path), the episode fetch bound `num_results=config.top_n` (`retrieval.py`
`_episode_hits`), and the post-merge `combined[:top_n]` truncation. This cycle
makes the relevance floor + the byte budget the only two volume controls in
the scored recall path, matching the human-memory north star.

Deltas:

  - Corpus + episode fetch de-count: both count gates on the corpus path and
    the episode fetch bound + post-merge truncation defer to the floor
    (`MIN_RELEVANCE_SCORE` / `RELEVANCE_THRESHOLD`, both already present) and
    the byte budget; all floor-clearing records reach the merge.
  - `DEFAULT_TOP_N` + post-merge count become a NAMED backstop carrying a
    telemetry-measurable retirement trigger; a no-op on normal-volume turns.
  - `SITUATIONAL_RULE_CAP` (count) dropped; the byte sub-budget alone bounds
    the rules block — a matched behavioral directive is never dropped by count.
  - Byte budgets (`INJECTION_CHAR_CAP`, `SITUATIONAL_RULE_CHAR_CAP`) re-anchored
    to a named resource per the owner's §3 ruling (recommended: fractions of
    `ADDITIONAL_CONTEXT_CAP` = 10,000, the enforced structural ceiling in
    `context_composer.py`).
  - Structural cap-bias catch: a plan-review/reviewer checklist line + a
    seeded situational rule on a NEW `authoring-plan` situation trigger
    (`SITUATION_TRIGGERS` + `SEEDED_RULES`), provenance-anchored to the
    2026-07-08 decision record + the audit.

All levers are NAMED and reversible: restoring the legacy count values
(DEFAULT_TOP_N as set-determiner, SITUATIONAL_RULE_CAP=3) reproduces pre-cycle
recall byte-for-byte. Recall-only — no data migration; the `.scratch/` index +
on-disk episodes/corpus untouched. Pinned hard-floor (AC-FBM-W-2) + lone-sparse-
episode rescue (AC-FBM-RN-2) preserved.

  - AC.RVL.1 — corpus discovered set is floor-determined, not count-determined
    (BOTH corpus count gates converted).
  - AC.RVL.2 — episode discovered set is floor-determined, not fetch-count-bounded.
  - AC.RVL.3 — the injected set is bounded only by the byte budget.
  - AC.RVL.4 — DEFAULT_TOP_N/post-merge count survive only as a retirement-
    triggered backstop, no-op on normal turns.
  - AC.RVL.5 — a matched situational rule is never dropped by a count.
  - AC.RVL.6 — every byte budget names its resource in-source.
  - AC.RVL.7 (outcome-altitude) — production retrieve(), no pre-arranged state:
    >5 floor-clearing records inject, cut by the byte budget not at 5; a
    floorless-only cue surfaces empty.
  - AC.RVL.8 — the cap-bias checklist line is present + reviewer-enforced.
  - AC.RVL.9 — the seeded authoring-plan rule fires on plan-authoring turns,
    silent on ambiguous input.

Owner gate (plan §3): byte-budget derivation is owner-pending; the byte-anchor
step records the ruling before landing. No ODD violation in surrounding code;
changes are named tunable levers consumed at the fetch + merge, no defensive
code for unnamed cases. Iterative associative recall (AC.IAR.*) deferred to
cycle 2.
