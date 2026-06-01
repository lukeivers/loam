# Deep role-research provider — the real `ResearchProvider` (N3 fast-follow / D-5)

**Status:** sub-plan-doc, PLAN-ONLY (plan-before-code). **Research-grade** —
this is the fast-follow slice the N3 onboarding intake left as a seam (N3's
fork D-5 = (a): "the deep role-research is its own fast-follow slice; N3 baseline
ships ONLY the featherlight opt-in SEAM"). It implements the REAL provider behind
that seam. The slice carries two genuine forks-with-recommendations (the research
PRIMITIVE and the budget/depth shape) because confidence in a single correct
outcome there is medium, not high — surfaced for an owner ruling, NOT locked
unilaterally.
**Working directory:** `/Users/lukeivers/loam/`.
**Worktree (plan authoring):** `/Users/lukeivers/loam-wt-deepresearch` on branch
`plan/deep-role-research` (this plan-doc is committed there; no code).
**Parent plans:**
- `docs/plans/n3-onboarding-init-flow-translate-in-intake.md` — the N3 baseline
  plan; **fork D-5 (a)** (§11, RATIFIED 2026-05-31) declared this slice; **§7
  Out-of-scope** explicitly deferred "the deep role-research PASS itself
  (web-research + synthesis) — a FAST-FOLLOW SLICE"; **AC.ONDEEP.2** is the AC
  this slice fills (the baseline only proved the seam is callable + degrades
  gracefully).
- `docs/plans/loam-roadmap.md` §4 row **N3** (this is the fast-follow on the N3
  critical-path kernel; it does NOT block N4 — N4 adapts the seeded state, which
  the baseline already produces).

**Predecessors (load-bearing prior seals + artefacts, Tier-0 on disk 2026-05-31):**
- `96aae8a` — **N3 onboarding SEAL** (the seam this slice fills): the
  `ResearchProvider` Protocol + `StubResearchProvider` + `RoleResearchResult`
  dataclass + `default_research_provider()` resolver, all in
  `framework/workspace-bootstrap/src/loam/workspace_bootstrap/deep_role_research.py`;
  the idea-vacuum opt-in path in `translate_in_intake.py`
  (`_run_fallback_ladder` → `provider.research_role(role)`). **This slice
  REGISTERS a real provider behind `default_research_provider()`; it does NOT
  touch the intake's gating logic — the featherlight invariant (AC.ONDEEP.1) is
  already sealed and stays sealed.**
- `f1f6116` — **`main` HEAD** (the branch base; carries the N3 seal). **BASELINE
  candidate** (re-check at build time — if another slice seals first, the
  builder advances it).
- The **interface contract the provider must satisfy** (Tier-0, read at plan
  time): `research_role(self, role: str) -> RoleResearchResult` where
  `RoleResearchResult` carries `role`, `effectiveness`, `promotion_criteria`,
  `existing_ai_tools`, `is_stub: bool`, and an `as_leverage_ideas()` fold-back.
  **The real provider returns `is_stub=False`** — that flip is the observable
  "real not stub" signal the outcome-altitude AC asserts.
- `docs/CLAUDE_CAPABILITIES.md` §6.2 (forked-context skills `context: fork`,
  line ~601 — "research-shaped work that shouldn't contaminate the main
  conversation"), §7 (the Agent tool / subagent dispatch; `background: true`,
  line ~704; `WebSearch`/`WebFetch` in the Agent toolset, line ~218). **The
  Lens-1 primitive this slice composes on; see fork D-RES-1 for the real
  availability constraint that primitive carries inside framework Python.**
- The **enshrined doctrine** (`docs/design/loam-doctrine.md`) — the operating
  loop's **over-reach guard** (lines 65–69: "Do not meet every 'do this once'
  with 'shouldn't this be a recurring automated framework?' … keep the elaborate
  version an opt-in suggestion") and the prime directive (leverage **FOR THEM**,
  not data collection). **The synthesis is the point of this slice — NOT the
  research; the over-reach guard applies twice over to a user who was ALREADY
  overwhelmed (the only user who reaches this seam).**
- The **synthesis-pattern + no-API-key precedent**:
  `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/claude_print_synthesis_client.py`
  (the subscription-routed `claude -p` shim — "NO Anthropic SDK, NO
  `ANTHROPIC_API_KEY`") and `framework/memory-system/.../claude_print_client.py`
  (the reference shape). **Tier-0 verified: every loam LLM call routes through
  `claude -p` subprocess, never the Anthropic SDK** (per
  `feedback_no_anthropic_api_key`). This is load-bearing for fork D-RES-1 — the
  raw-research and synthesis steps must obey it.

**BASELINE (pre-build tip):** `f1f6116` (current branch base / `main` HEAD;
re-check at build time).
**Status-file target:** `<workspace>/.scratch/claude-output/deep-role-research-status.md`
(builder writes build progress here).
**Quality bar:** a **real provider run** on a sample role (e.g. "registered
nurse"), invoked **through the real seam** (`provider.research_role(role)` reached
via the actual idea-vacuum opt-in intake path, OR `default_research_provider()`
returning the real provider), produces a **short, person-specific, synthesized
set of leverage ideas** addressing the three axes — `is_stub=False`, bounded to a
small fixed research budget, never a research dump. The output is something a
**user who was already overwhelmed** can act on, not a wall of citations.

**Scope-tightness (F4):** TIGHT where N3 + the doctrine already settled it (the
interface contract is sealed and fixed; the three axes are named; the featherlight
opt-in gate is sealed and untouched; the synthesis-not-dump constraint is a hard
over-reach-guard application; persistence — if any — lands in-home, gate 9).
FORKED-with-recommendation where it is genuinely an owner/architecture call (the
research PRIMITIVE shape given the no-API-key + in-process constraints — D-RES-1;
the research budget/depth + how-many-ideas-to-surface — D-RES-2; sync-vs-async —
D-RES-3). Method stays the builder's call; this plan does not prescribe files or
symbols beyond the sealed interface it must satisfy.

---

## §1. Summary / TL;DR

This slice implements the **real `ResearchProvider`** behind the seam N3 sealed.
Given a user's **role** + their explicit **opt-in** (both already established by
the sealed intake — this slice never re-gates), it **researches three axes**:
(i) what makes someone **EFFECTIVE** at the role, (ii) what gets people
**PROMOTED** to the next level, (iii) which **existing AI solutions** loam could
wrap or take ideas from to rebuild for the user — then **synthesizes** the raw
research into a **SHORT, person-specific, actionable set of leverage ideas** and
returns it through the sealed `RoleResearchResult` shape (`is_stub=False`), which
the intake folds back into its demonstrate-leverage close.

**The central design stance, surfaced for owner ruling:** the **synthesis is the
deliverable, not the research.** The user who reaches this seam is — by the sealed
intake's own routing — at the **bottom of the idea-quality continuum**: an
idea-vacuum user who was overwhelmed, gave a role, and asked for help. The
over-reach guard therefore applies **twice over**: (a) the research itself runs on
a **small fixed budget** (a bounded number of searches/fetches, not an unbounded
agent loop), and (b) the output is a **short, ranked, person-specific set** of a
**few** leverage ideas — never the raw research, never a citation dump, never a
list that re-overwhelms the person the intake just coaxed out of overwhelm.

**The Lens-1 finding that shapes the whole slice (F2 §10.1).** The dispatch names
"the forked-research-subagent over WebSearch/WebFetch" as the primitive to compose
on (per CLAUDE_CAPABILITIES). That is the right primitive **conceptually** — but
**Tier-0 reality:** `WebSearch`/`WebFetch`/the `Agent` tool are **Claude-Code
session tools**, available to an agent *running inside a Claude session* — they are
**NOT importable functions a standalone Python provider (a pytest run, a bare
`claude init-intake` CLI process) can call directly.** Loam's standing constraint
compounds this: **every loam LLM call routes through `claude -p`, never an SDK/API
key** (`feedback_no_anthropic_api_key`, Tier-0 verified in the odd-extractor
synthesis client). So "compose the forked-research-subagent" resolves, in
framework Python, to **`claude -p` dispatching a bounded research-shaped subagent
prompt that itself has WebSearch/WebFetch** — which IS composing on the
Claude-native primitive, not rebuilding orchestration, but the composition
mechanism is the `claude -p` subprocess shim, not a direct tool import. **This is
fork D-RES-1**, surfaced with a recommendation, because how the provider reaches
the primitive (and whether it degrades to stub when `claude` is absent) is a real
architecture call.

**Four AC families:**

- **AC.DRR.\*** — the provider **researches + synthesizes** (the slice's job): a
  real provider, given a role, runs a **bounded** three-axis research pass and
  returns a **person-specific synthesis** addressing all three axes, marked
  `is_stub=False`. The bound is observable (the research budget is fixed and not
  exceeded); the synthesis is short (a few ideas, not a dump); the ideas reference
  the role (person-specific, not generic boilerplate).
- **AC.DRRSEAM.\*** — the real provider **satisfies the sealed seam exactly**: it
  implements the `ResearchProvider` Protocol, returns a `RoleResearchResult` the
  intake's `as_leverage_ideas()` fold-back consumes unchanged, registers behind
  `default_research_provider()`, and the **sealed featherlight invariant
  (AC.ONDEEP.1) still holds** — a baseline (non-idea-vacuum, or declined) run
  STILL never invokes it.
- **AC.DRRGRACE.\*** — **graceful degradation + bound enforcement**: when the
  research primitive is **unavailable** (no `claude` binary, a research failure, a
  timeout, the budget exhausted), the provider degrades to a **clearly-marked
  fallback synthesis** (never raises, never hangs, never silently returns nothing)
  — the same no-interrogation-by-weight protection the baseline relied on, now at
  the real-provider layer.
- **★ AC.DRROUT.\*** — the **outcome-altitude AC**: a **real provider** run on a
  **sample role**, reached **through the real seam** (the production intake's
  idea-vacuum opt-in path, OR `default_research_provider()` resolving to the real
  provider), produces a **synthesized, person-specific set of leverage ideas** —
  `is_stub=False`, addressing the three axes, bounded, folded into the intake's
  close. A STUB-class unit test does NOT satisfy this; it must drive the real
  provider end-to-end.

**Key forks surfaced (the architecture/owner calls — §11):**
1. **D-RES-1 — the research PRIMITIVE shape.** How the in-process Python provider
   reaches the Claude-native research primitive given no-API-key + not-a-session.
   (Recommended: a bounded `claude -p` research-subagent dispatch — composes the
   primitive, obeys the subscription constraint, degrades to fallback when
   `claude` is absent.)
2. **D-RES-2 — research budget + idea count.** How small "small fixed budget" is,
   and how few "a few ideas" is. (Recommended: a hard cap of ~3 search/fetch
   round-trips per axis ceiling, and **3 surfaced leverage ideas** total — one per
   axis at most — over-reach-guard-tight.)
3. **D-RES-3 — sync vs async.** Does the provider block the intake turn, or run in
   the background and surface when ready. (Recommended: **synchronous with a hard
   timeout + a fallback** for this slice — the intake already has the user's
   attention at the opt-in moment; async re-surfacing is a later convenience, a
   fast-follow on this fast-follow.)

**F2 on scope realism:** this slice is **M–L** — the interface + gating is sealed
(no UX surface to design), but the bounded research + synthesis over a `claude -p`
subagent is real net-new work with a soft-to-verify synthesis quality. Two named
scope risks. **(1) The research running unbounded** (§10.2): a research-subagent
with no budget cap is exactly the "unbounded agent" the dispatch forbids and the
over-reach guard rejects — the budget is a HARD constraint (D-RES-2), not a tunable
nicety, and AC.DRR.2 makes exceeding it observable. **(2) The output becoming a
dump** (§10.3): the easiest wrong implementation returns the raw research (or a
long list) — which re-overwhelms the exact user this seam exists to help. The
synthesis-to-a-few-person-specific-ideas constraint is the slice's whole point
(AC.DRR.3 + AC.DRROUT), named so the builder treats "short + person-specific" as
load-bearing, not cosmetic.

---

## §2. Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| The real `ResearchProvider` implementation (3-axis research → synthesis → ideas) | A new module under `framework/workspace-bootstrap/` — the component that owns `deep_role_research.py` (the sealed seam) | Lens 1 / compose-don't-rebuild: the seam, the Protocol, the `RoleResearchResult`, and the `default_research_provider()` resolver all live here. The real provider is a NEW module/class in the SAME component that registers behind the existing resolver. The builder owns the exact module boundary. **Single-component fence: `workspace-bootstrap`.** |
| The bounded research step (reach the Claude-native research primitive) | Same component; a research-client shim that dispatches a **bounded** `claude -p` research-subagent (D-RES-1) — mirrors the odd-extractor `claude_print_synthesis_client.py` shape | Lens 1: composes the forked-research-subagent primitive; the `claude -p` subprocess is the composition mechanism under the no-API-key constraint (`feedback_no_anthropic_api_key`). NOT new orchestration — a thin shim around the Claude-native research dispatch. |
| The synthesis step (raw research → a few person-specific leverage ideas) | Same component; the provider's synthesis method — may itself be a second bounded `claude -p` call OR a deterministic fold over the structured research result (the builder's call within the budget) | The synthesis is the deliverable. It is provider-local logic; the over-reach guard (short + person-specific) is enforced by AC, not by where it lives. Precedent shape: the odd-extractor synthesis layer. |
| Any persisted research output (if the provider caches/records anything) | **ONLY** under `~/.claude/` (global) or `<ws>/.loam/` (workspace-scoped) — gate 9 enforces | **N3's Surface #3 + gate 9 carry forward unchanged.** Whether the provider persists ANYTHING at all is the builder's call (recommend: surface-through-the-seam-only, no persistence in this slice — the leverage ideas reach the user via the intake's close, and the seeded objective the baseline already writes is sufficient). If it DOES persist, it lands in-home or it is a boundary violation. |
| The provider registration (swap the stub for the real provider behind `default_research_provider()`) | Same component; the registration point the sealed `_DEFAULT_PROVIDER` / `default_research_provider()` resolver already declares for exactly this | The N3 seam was built so "the fast-follow slice can register a real provider without the baseline importing it" (sealed docstring). This slice fills that registration seam — it does NOT change the resolver's contract. |
| The intake gating logic (who reaches the seam) | **UNTOUCHED — sealed at `96aae8a`.** The featherlight opt-in invariant (AC.ONDEEP.1) is sealed; this slice does not edit `translate_in_intake.py`'s routing | The "who reaches it" question is the baseline's job and is DONE. This slice only fills "what happens when it IS reached." Editing the gate would re-open a sealed invariant (halt trigger #3). |

---

## §3. Halt-and-surface BEFORE build (decisions recorded at plan-time)

### Surface #1 (no halt — recorded; the seam is SEALED and fixed, this slice fills it)

**Decision (autonomous, Tier-0 verified by reading the sealed `deep_role_research.py`
+ the seam test):** the `ResearchProvider` Protocol, the `RoleResearchResult`
shape, the `as_leverage_ideas()` fold-back, and the `default_research_provider()`
resolver are **sealed at `96aae8a`** and are the **fixed contract** this slice
satisfies. The real provider returns the same `RoleResearchResult` shape with
`is_stub=False`. This slice **adds** a real provider + registers it; it does NOT
change the interface. *Surfaced* because a builder might be tempted to "improve"
the result shape — the shape is sealed; the intake's fold-back depends on it.

### Surface #2 (no halt — recorded; the featherlight gate is SEALED, do not touch it)

**Decision (autonomous, per the N3 seal):** **who reaches this seam** (an
idea-vacuum user who gave real role detail AND opted in — AC.ONDEEP.1) is **sealed
and correct.** This slice does NOT edit the intake's routing. The real provider's
job begins **after** the gate has already decided to invoke it. *Surfaced* because
"make the research available to more users" would re-open the sealed
no-interrogation invariant — that is a separate, owner-gated decision, not this
slice's call (halt trigger #3).

### Surface #3 (no halt — recorded; the over-reach guard applies TWICE to THIS user)

**Decision (autonomous, per the doctrine + the prime directive — a hard constraint,
NOT a tunable choice):** the user who reaches this seam is, by the sealed routing,
**already overwhelmed** (bottom of the idea-quality continuum). The over-reach
guard therefore binds **both** the research (bounded budget — don't run an
expensive unbounded pass on a user who just wants a starting point) **and** the
output (a **few** person-specific ideas — don't hand an overwhelmed person a
research report). The *exact* budget number + idea count are owner product calls
(D-RES-2), but "bounded + short + person-specific" is load-bearing and the ACs make
a dump / unbounded-run an observable violation (AC.DRR.2 bounds the budget;
AC.DRR.3 + AC.DRROUT bound + person-specialize the output). *Surfaced* so the
builder treats it as a constraint, not a preference.

### Surface #4 (HALT-WORTHY but RESOLVED — the primitive is a SESSION tool, not an importable function)

**The tension (Lens 1 / Lens 6 / M5):** the dispatch names "compose the
forked-research-subagent over WebSearch/WebFetch." **Tier-0 finding:**
`WebSearch`/`WebFetch`/the `Agent` tool are **Claude-Code session tools** (per
CLAUDE_CAPABILITIES §7) — an agent *inside a Claude session* has them; a **standalone
Python provider does not** (a pytest run / a bare `claude init-intake` subprocess
is not a Claude session with the Agent toolset). Loam's standing rule compounds
it: **no Anthropic API key — every LLM call goes through `claude -p`**
(`feedback_no_anthropic_api_key`, Tier-0 in the odd-extractor synthesis client).
**Signals (M5 step 2):** Lens-1 compose-don't-rebuild weighs heavy (the answer is
NOT to write a bespoke web-scraper — that rebuilds the primitive); the no-API-key
constraint is a hard locked rule; reversibility of the shim choice is medium (it is
the provider's whole I/O path). **Resolution (M5 step 3 — surfaced as a fork, not
ruled unilaterally, because the owner may have a preference):** the provider reaches
the primitive via a **bounded `claude -p` research-subagent dispatch** — a `claude
-p` subprocess (the subscription path) running a research-shaped prompt that itself
has WebSearch/WebFetch, returning a structured three-axis result the provider then
synthesizes. This **composes** the Claude-native primitive (the subagent does the
web research) without rebuilding orchestration or violating the API-key rule, and
it **degrades to a fallback synthesis when `claude` is absent** (AC.DRRGRACE). This
is **fork D-RES-1**, surfaced for the owner with this as the recommendation. *Why
surfaced not silently ruled:* the owner may prefer a different composition (e.g. a
forked-context SKILL the *interactive persona* invokes, with the provider only
consuming a cached result) — a reasonable alternative that weighs the signals
differently (M5 step 4).

### Surface #5 (no halt — recorded; persistence, if any, lands in-home — gate 9 unchanged)

**Decision (autonomous, per N1 + the sealed boundary):** if the provider persists
anything (a research cache, a record of surfaced ideas), it lands **only** under
the two homes (`~/.claude/`, `<ws>/.loam/`) — gate 9 catches a stray write. The
**recommendation is to persist NOTHING in this slice** (surface the ideas through
the intake's close; the baseline already seeds the objective) — keeping the slice's
boundary footprint zero. *Surfaced* so the builder knows persistence is optional
and, if added, is gate-9-bound.

### Surface #6 (no halt — recorded; the architecture/product forks are owner-facing)

**Decision (per the dispatch + F2):** the research-primitive shape (D-RES-1), the
budget + idea-count (D-RES-2), and sync-vs-async (D-RES-3) are calls where
reasonable people weigh signals differently (M5 / scope↔confidence: confidence in a
single correct shape is medium). Each is a **fork with a recommendation** in §11,
surfaced for an owner ruling. The build does not start until the owner rules the
three forks (or ratifies the recommendations).

---

## §4. Spec-objective placement

**Binds to:**
- **The prime directive — per-user-tuned translation** (`docs/design/loam-doctrine.md`;
  `feedback_loam_prime_directive_user_tuned_translation`). This slice is the
  **leverage-FOR-THEM** payoff at the bottom of the idea-quality continuum: for the
  user who has NO idea what to ask loam for, it **brings them** candidate leverage
  ideas tuned to their role. The synthesis IS the translation made visible.
- **The over-reach guard / proportionality** (same doctrine, lines 65–69): the
  bounded research + short person-specific output is the over-reach guard applied to
  the most-overwhelmed user loam serves.
- **N3's AC.ONDEEP.2** (the seam's "given a role, return the three named axes via a
  clean interface" AC — verified at the SEAM level in N3, **filled at the PASS level
  here**, exactly as the N3 plan's AC.ONDEEP.2 note said: "If D-5 = fast-follow,
  this AC is verified in the fast-follow slice").
- **The protection leg** (ADR-0001 + gate 9): any persisted output lands in-home.

**Ladders up:** AC.DRR.\* + AC.DRRSEAM.\* + AC.DRRGRACE.\* + AC.DRROUT.\* → fills
N3's AC.ONDEEP.2 (the research PASS) → the idea-quality continuum's bottom rung is
now served by a REAL provider, not a stub → the prime directive's
leverage-FOR-THEM pillar (the user who couldn't name an ask is brought
role-tuned ideas). Reverse-trace per `feedback_value_proposition_as_prime_objective`:
every AC traces to AC.PO.\* (the prime objective in VALUE_PROPOSITION) via the
per-user-tuned-translation directive — this slice is that directive serving the
user it is hardest to serve (the idea-vacuum user).

---

## §5. Acceptance criteria

> ODD note: every AC below is **outcome-shape** — it states the observable
> outcome, not the method. Method-in-AC test applied to each: the AC can be
> satisfied by a method other than the one the author has in mind (the research
> could be a `claude -p` subagent, a forked SKILL, or — in a test — an injected
> fake research-source; the synthesis could be a second `claude -p` call or a
> deterministic fold — the AC pins *bounded + synthesized + person-specific +
> real-not-stub*, not the *how*). The exact budget number + idea count resolve
> from the D-RES-2 ruling; pinning them here would be method-in-AC.

### AC.DRR.\* — the provider researches the three axes + synthesizes (the slice's job)

- **AC.DRR.1 (a real provider, given a role, returns a synthesis addressing all
  three axes — `is_stub=False`).** Invoked with a role, the real provider returns a
  `RoleResearchResult` whose `effectiveness`, `promotion_criteria`, and
  `existing_ai_tools` fields each carry a **non-stub, role-derived** synthesis (the
  three named axes: what makes someone effective / what gets them promoted / which
  existing AI tools loam could wrap or rebuild), with `is_stub=False`. *Verified
  by:* a run with the research step exercised (live, or with an injected
  research-source fake) returns a result whose three axes are populated with
  role-specific content and `is_stub is False` — distinguishable from the sealed
  `StubResearchProvider`'s placeholder text.
- **AC.DRR.2 (the research is BOUNDED — a small fixed budget, never unbounded).**
  The research pass runs within a **fixed budget** (the D-RES-2 cap on
  search/fetch round-trips) and **does not exceed it** — there is no unbounded
  agent loop. *Verified by:* a run with an instrumented/faked research-source
  observes the provider make **no more than** the budgeted number of research
  round-trips before synthesizing (the budget is a hard cap, asserted, not a
  hope). (Per D-RES-2.)
- **★ AC.DRR.3 (the output is SHORT + person-specific — a synthesis, never a dump).**
  The returned leverage ideas (via `as_leverage_ideas()` and/or the result the
  intake folds into its close) are **a few** (the D-RES-2 count — not a long list)
  and **reference the user's role** (person-specific, distinguishable from generic
  boilerplate). The provider does NOT return the raw research, a citation dump, or a
  list long enough to re-overwhelm the user. *Verified by:* a run yields **≤ the
  D-RES-2 idea count**, each idea **referencing the role** (a specificity probe, the
  AC.ONINTAKE.6 pattern); two different roles yield two different idea sets (not a
  fixed template). This is the over-reach guard made observable — the slice's whole
  point.

### AC.DRRSEAM.\* — the real provider satisfies the sealed seam exactly

- **AC.DRRSEAM.1 (the real provider IS a `ResearchProvider` and the intake's
  fold-back consumes it unchanged).** The real provider implements the sealed
  `ResearchProvider` Protocol (`research_role(role) -> RoleResearchResult`), and the
  intake's `as_leverage_ideas()` fold-back + demonstrate-leverage close consume its
  result **without any change to `translate_in_intake.py`**. *Verified by:* the real
  provider is type-compatible with the sealed Protocol, and a run through
  `run_translate_in_intake` with the real provider injected produces leverage ideas
  in the intake's close — with the intake code untouched.
- **★ AC.DRRSEAM.2 (the sealed featherlight invariant STILL holds — AC.ONDEEP.1
  regression guard).** With the real provider registered behind
  `default_research_provider()`, a **baseline run** (a user who named a stop/start
  thing directly, OR gave no role detail, OR declined the deepening) **still NEVER
  invokes the research pass.** *Verified by:* re-running the sealed AC.ONDEEP.1
  cases against the real provider registered as default — the spy still records zero
  invocations on every non-(idea-vacuum + role + opt-in) path. (The N3 seal's
  invariant is not regressed by registering a real provider.)

### AC.DRRGRACE.\* — graceful degradation + bound enforcement (the protection floor)

- **AC.DRRGRACE.1 (unavailable primitive → a clearly-marked fallback, never a raise
  / hang).** When the research primitive is **unavailable** (no `claude` binary, a
  dispatch failure, a timeout, the budget exhausted with nothing usable), the
  provider returns a **clearly-marked fallback** `RoleResearchResult` (a graceful
  synthesis naming the three axes, marked so the caller can tell it is a
  degraded-not-real result) — it does **not** raise, hang, or return empty. *Verified
  by:* a run with the research primitive forced unavailable (e.g. a fake that raises
  / times out) returns a usable fallback result and the intake's close still
  surfaces ≥1 leverage idea — the no-interrogation-by-weight protection now at the
  real-provider layer. (This is the same graceful-degradation property the N3
  baseline relied on, preserved when the real provider is present-but-failing.)

### AC.DRROUT.\* — the outcome-altitude AC (a real provider through the real seam)

- **★ AC.DRROUT.1 (OUTCOME-ALTITUDE — a real provider run on a sample role, through
  the real seam, produces synthesized person-specific leverage ideas — NOT a stub).**
  A **real provider** (not the stub) is invoked on a **sample role** (e.g.
  "registered nurse") **through the real seam** — either the production intake's
  idea-vacuum opt-in path (`run_translate_in_intake` reaching
  `provider.research_role`), OR `default_research_provider()` resolving to the real
  provider — and the run ends with: (a) a `RoleResearchResult` with `is_stub=False`,
  (b) the three axes populated with role-derived content, (c) **a few**
  person-specific leverage ideas (≤ the D-RES-2 count, each referencing the role)
  folded into the intake's close, (d) the research having stayed within the budget.
  A STUB-class unit test of an inner function does NOT satisfy this — it must drive
  the **real provider** end-to-end (the cold-walk standard). *Verified by:* the
  outcome-altitude test drives the real provider through the seam on a sample role
  and asserts the four post-conditions; if it exercises the live `claude -p`
  research path it is env-gated (per the live-smoke convention) with a deterministic
  injected-research-source variant that runs every pass.
  - **`outcome-altitude: true`** (per `feedback_test_outcome_altitude_required` —
    invokes the real provider through the production seam with no pre-arranged stub
    result).

---

## §6. Build steps (method-level guidance only — builder's call per ODD §1.1)

> The builder owns method. This is sequence + the bookkeeping mechanism, not
> file-by-file prescription. **The build does not start until the owner rules the
> three §11 forks (D-RES-1..D-RES-3) or ratifies the recommendations** (§5 ACs
> that reference a fork resolve once the fork is ruled).

**This is likely a single cycle** (one component — `workspace-bootstrap` — one
fence): the real provider + the bounded research shim + the synthesis + the
registration. The builder may decompose into (a) the bounded research shim and (b)
the synthesis + registration as sub-cycles with tighter ACs (Lens 5; the builder's
call per the scope-confidence stopping criterion).

1. **Confirm the fork rulings are recorded** in this plan-doc's §11 before any code
   (record-ratification-before-dispatch). The build reads the ruled forks, not a
   conversational memory of them.
2. **Examine the sealed seam FIRST** (do not re-derive): read
   `deep_role_research.py` (the Protocol + `RoleResearchResult` + the
   `default_research_provider()` resolver — the fixed contract), the sealed
   AC.ONDEEP seam test (the invariant to NOT regress), and `translate_in_intake.py`'s
   `_run_fallback_ladder` (the consumer — to confirm the fold-back contract). Read
   the `claude -p` precedent (`claude_print_synthesis_client.py`,
   `claude_print_client.py`) for the no-API-key subprocess shape (per the ruled
   D-RES-1). Confirm the boundary homes via `user-state-homes.yaml`.
3. **Author the outcome-altitude test FIRST** (TDD, dev-mode default): AC.DRROUT.1
   — a real provider on a sample role, through the real seam, the four
   post-conditions (`is_stub=False` / three axes / ≤count person-specific ideas /
   within budget). Author it with a **deterministic injected-research-source** so it
   runs every pass, plus an env-gated live-`claude -p` variant if D-RES-1 ruled the
   subprocess path. Then the budget-bound test (AC.DRR.2) and the
   featherlight-regression test (AC.DRRSEAM.2 — re-run the sealed AC.ONDEEP.1 cases
   against the real provider as default).
4. **Build the bounded research shim** (per the ruled D-RES-1) — reach the
   Claude-native research primitive within the D-RES-2 budget; the three-axis
   research returns a structured intermediate. Hard budget cap (AC.DRR.2); graceful
   on unavailable/timeout (AC.DRRGRACE.1).
5. **Build the synthesis** — raw three-axis research → **a few** person-specific
   leverage ideas (≤ the D-RES-2 count, each referencing the role; AC.DRR.3). The
   over-reach guard is the load-bearing bit: short, person-specific, never a dump.
   Return a `RoleResearchResult` with `is_stub=False` (AC.DRR.1) the sealed
   `as_leverage_ideas()` fold-back consumes unchanged (AC.DRRSEAM.1).
6. **Register the real provider** behind `default_research_provider()` (the sealed
   registration seam) — without editing the intake's routing (AC.DRRSEAM.2 holds).
7. **Run the boundary gate (gate 9)** against a post-run tree if the provider
   persists anything — confirm GREEN (Surface #5). Re-run the **sealed** AC.ONDEEP
   seam test — confirm the registration did not regress the featherlight invariant.
8. **`loam amend apply` / seal** — `workspace-bootstrap` is a **sealed component**
   (Tier-0: ships via amendment cycles; the N3 seal `96aae8a` is on it). The builder
   names `loam amend apply` as the bookkeeping mechanism and verifies against
   `docs/conventions/sealed-component-invariants.md` at build-time
   (`feedback_dispatch_explicit_loam_amend_apply`).
9. **Seal** per the standard ladder; backfill each AC GREEN into this plan-doc's
   §status verdict matrix; **merge the sealed slice to `main`** (the per-slice
   merge); backfill **N3's AC.ONDEEP.2 to PASS** (the seam-deferred PASS is now
   filled).
10. **Bookkeeping** (§9): note in the N3 plan that AC.ONDEEP.2's deferred PASS is
    filled by this slice (SHA); mark the roadmap fast-follow done.

---

## §7. Out of scope (deferred + when)

- **Editing the intake's gating logic (who reaches the seam) — SEALED at `96aae8a`.**
  The featherlight opt-in invariant (AC.ONDEEP.1) is DONE. This slice fills "what
  happens when reached," not "who reaches it." Widening access is a separate,
  owner-gated decision (halt trigger #3).
- **Async / background re-surfacing of research** — deferred (D-RES-3 recommends
  synchronous-with-timeout for this slice). If the research is too slow to run
  synchronously at the opt-in moment, an async "I'll surface ideas when ready" path
  is a **fast-follow on this fast-follow**, not this slice.
- **Persisting a research cache / a per-role knowledge base** — deferred (Surface
  #5 recommends persist-nothing). If the owner wants research cached for reuse, it
  is a later slice that lands the cache in-home (gate 9) with its own AC.
- **Research on non-role axes (company-specific, team-specific, market-specific)** —
  the three named axes (effectiveness / promotion / existing-AI-tools) are the
  sealed contract; broader research surfaces are later slices.
- **The synthesis quality bar as an automated judge** (an LLM-as-judge that scores
  "is this idea GOOD?") — out of scope as a gate; the ACs verify
  *bounded + person-specific + real-not-stub + ≤count*, and deep quality is a
  review/LLM-as-judge concern (§10.4), not a unit assertion in this slice.
- **A general-purpose loam `deep-research` module** — Tier-0: none exists; this
  slice is role-research-specific behind the N3 seam. A general research capability
  (the `deep-research` SKILL composition CLAUDE_CAPABILITIES sketches) is a separate
  larger surface, not this slice.

---

## §8. Halt triggers (in-flight conditions that abort the build)

1. **The forks are not ruled.** If the build starts and D-RES-1..D-RES-3 are not
   recorded in §11, HALT — the architecture shape (how the provider reaches the
   primitive; the budget; sync-vs-async) is unresolved, and building on an
   unconfirmed shape is the silent-inference failure
   (record-ratification-before-dispatch).
2. **The outcome-altitude AC cannot reach real-provider altitude.** If AC.DRROUT.1
   can only be tested by stubbing the provider's internals (the real provider cannot
   be driven through the seam on a sample role without a pre-arranged stub result),
   HALT — the AC is unsatisfiable as written and needs re-framing before code
   (loose-AC → fix the AC, not the implementation).
3. **The fix requires editing the sealed intake gate.** If satisfying any AC seems
   to require changing `translate_in_intake.py`'s routing (who reaches the seam),
   HALT — that re-opens the sealed AC.ONDEEP.1 featherlight invariant; widening
   access is owner-gated, not a build call (Surface #2 / §7).
4. **The research wants to run unbounded.** If the only way to get a usable
   synthesis is to remove the budget cap (the research "needs" more round-trips than
   D-RES-2 allows), HALT and surface — the bound is a HARD over-reach-guard
   constraint, not a tunable; a genuine need for a larger budget is an owner ruling
   on D-RES-2, not a silent widening.
5. **The output cannot be made short + person-specific.** If the synthesis can only
   satisfy the three axes by returning a long list / the raw research, HALT — that
   violates the over-reach guard on the already-overwhelmed user (Surface #3); the
   close is a *few* person-specific ideas, not a report (AC.DRR.3).
6. **The seed / any persisted output cannot be made gate-9-clean.** If the provider
   must persist outside the two homes to be useful, HALT and surface — the boundary
   is locked (N1); a genuine third-location need is an ADR-level decision, not a
   build call.
7. **The no-API-key constraint would be violated.** If the research/synthesis path
   reaches for an Anthropic SDK / `ANTHROPIC_API_KEY` (instead of `claude -p`), HALT
   — `feedback_no_anthropic_api_key` is a hard locked rule; every LLM call routes
   through the subscription `claude -p` path.

---

## §9. Bookkeeping (STATE.md + roadmap + parent-plan backfill)

1. **`docs/plans/n3-onboarding-init-flow-translate-in-intake.md` §13 verdict matrix**
   — backfill **AC.ONDEEP.2 from "SEAM GREEN / PASS deferred" to "✓ PASS"** at seal
   (SHA), noting this slice filled the deferred research PASS.
2. **`docs/plans/loam-roadmap.md` §4** — mark the deep-role-research fast-follow done
   (SHA); note it does NOT re-base the N3 → N4 critical path (N4 was never blocked on
   it — the baseline already seeds).
3. **`docs/STATE.md`** — record the seal (amendment number + SHA) per the standard
   ladder once sealed.
4. **This plan-doc §status / verdict-matrix** — backfill each AC GREEN at seal so
   release gate 2 (`check_acs_verified`) can read it.
5. **The fork rulings (§11)** — record the owner's D-RES-1..D-RES-3 rulings in §11
   BEFORE the build dispatch (record-ratification-before-dispatch).

---

## §10. F2 Ruthless Feedback (honest doubts + named design risks)

1. **THE LOAD-BEARING FINDING — the named primitive is a SESSION tool, not an
   importable function; "compose it" resolves to a `claude -p` subagent dispatch.**
   *The disagreement:* the dispatch says "compose the forked-research-subagent over
   WebSearch/WebFetch" as if the provider can call those tools directly. *The
   evidence:* `docs/CLAUDE_CAPABILITIES.md` §7 — `WebSearch`/`WebFetch`/the `Agent`
   tool are **Claude-Code session tools** available to an agent *inside a session*;
   a standalone Python provider (a pytest run, a bare CLI subprocess) is not such a
   session and cannot import them. Loam's `feedback_no_anthropic_api_key` (Tier-0 in
   `claude_print_synthesis_client.py`) forbids the SDK path that might otherwise
   substitute. *The alternative:* compose the primitive via a **bounded `claude -p`
   research-subagent dispatch** — the subprocess IS a Claude session with the Agent
   toolset, so the web research happens in the Claude-native primitive, while the
   provider stays subscription-routed and SDK-free. This is fork **D-RES-1**,
   surfaced with this as the recommendation so the owner can rule otherwise (e.g. a
   persona-invoked forked SKILL that caches a result the provider consumes). This is
   the #1 architecture risk; named in Surface #4, the placement table, the build
   steps, and halt trigger #7 so it cannot be missed.

2. **Risk: the research runs unbounded — the exact thing the dispatch + the guard
   forbid.** *The evidence:* a research-subagent with no budget cap is an unbounded
   agent loop; the dispatch explicitly says "don't let it run unbounded — a small
   fixed research budget," and the over-reach guard rejects expensive work on an
   already-overwhelmed user. *The alternative / mitigation:* the budget is a **hard
   cap** (D-RES-2), and AC.DRR.2 makes exceeding it an **observable** violation (an
   instrumented run asserts ≤ the budgeted round-trips). Named so the builder treats
   the budget as a hard constraint, not a default to tune later.

3. **Risk: the output becomes a dump — re-overwhelming the user this seam exists to
   help.** *The disagreement:* the naive read of "research three axes" is "return the
   research." *The evidence:* the user who reaches this seam is, by the sealed
   routing, at the **bottom of the idea-quality continuum** — already overwhelmed.
   Handing them a research report is the interrogation-by-weight failure the N3 owner
   forbade, relocated to the output. *The alternative / mitigation:* AC.DRR.3 +
   AC.DRROUT bound the output to **a few** ideas, each **referencing the role**
   (person-specific, not a template), and forbid returning the raw research. The
   synthesis-to-a-few-person-specific-ideas IS the slice's deliverable. Named so the
   builder treats "short + person-specific" as load-bearing.

4. **Risk: synthesis quality (is the idea GOOD?) is soft to verify.** *The
   evidence:* "a good person-specific leverage idea" is a quality the model
   exercises, not a deterministic gate — the same shape as N3's AC.ONINTAKE.6
   leverage-close risk. *The alternative / mitigation:* the ACs verify the
   *enforceable* properties (bounded / real-not-stub / ≤count / references-the-role /
   two-roles-yield-two-sets — a specificity + non-template probe); the deep "is it
   genuinely useful?" judgement is an LLM-as-judge / review concern (§7
   out-of-scope), not a unit assertion. Named so the builder authors the specificity
   + non-template probes, not just an "an idea was returned" assertion.

5. **Risk: a live-`claude -p` research test is non-deterministic + slow + costs
   subscription.** *The evidence:* a research subagent's output varies run-to-run;
   gating it un-conditionally into the pytest suite makes the suite flaky and slow.
   *The alternative / mitigation:* AC.DRROUT.1 is authored with a **deterministic
   injected-research-source** variant that runs every pass (asserts the structural
   post-conditions), plus an **env-gated** live-`claude -p` variant (the
   `LOAM_..._LIVE=1` convention the README AC.3 + onboarding cold-walk already use)
   for the real-altitude smoke. Named so the builder does not put a live
   non-deterministic call in the always-run suite.

6. **The slice is honestly M–L, not S — the seam being sealed hides real work.**
   *The disagreement:* "the interface is sealed, so this is a small fill-in." *The
   evidence:* the bounded research shim (a `claude -p` research-subagent with a
   budget cap + graceful degradation), the synthesis (raw → few person-specific
   ideas), and the deterministic + live test pair are real net-new work with a
   soft-to-verify deliverable. *The alternative:* size it M–L and decompose if the
   research shim + synthesis each earn a tighter AC (Lens 5), rather than treating it
   as a trivial registration. Named so the dispatch carries an honest size.

---

## §11. Named decisions / forks (with recommendations — OWNER/ARCHITECTURE calls)

> These three are the architecture/product decisions this slice surfaces. Each is
> a fork with my recommendation; the owner rules (or ratifies the recommendation)
> BEFORE the build. Recorded here is the durable ratification surface the builder
> Tier-0-reads (record-ratification-before-dispatch).

### ★ RULINGS (owner-ratified 2026-05-31, build-dispatch brief) — recorded BEFORE build

- **D-RES-1 → (a) RULED.** Research primitive = a **bounded `claude -p`
  research-subagent** (the subprocess IS a Claude session with WebSearch/WebFetch;
  subscription-routed; NO Anthropic API key — `feedback_no_anthropic_api_key`).
  **Spawn-isolated** via the mandated `loam_spawn_isolation.spawn_isolated_claude`
  primitive (`--strict-mcp-config` + empty `mcpServers`, token/API-key-scrubbed
  env) — compose the sealed primitive, do NOT hand-roll. Lazy-imported inside the
  dispatch so the provider degrades gracefully (AC.DRRGRACE.1) when the primitive /
  `claude` binary is absent (mirrors the README_3 live-test consumption convention;
  `loam-spawn-isolation` is not a workspace-bootstrap dependency and every consumer
  imports it lazily).
- **D-RES-2 → (a) RULED — TIGHT.** Budget = **~3 round-trips ceiling** + **≤3
  surfaced leverage ideas** total. Over-reach-guard-tight (the only user who reaches
  this seam is already overwhelmed). The budget is a HARD cap, asserted by AC.DRR.2.
- **D-RES-3 → (a) RULED — SYNCHRONOUS.** The provider blocks the intake turn with a
  **hard timeout + graceful fallback** (AC.DRRGRACE.1). Async re-surfacing is a
  fast-follow on this fast-follow (§7, deferred).

### D-RES-1 — the research PRIMITIVE shape (how the in-process provider reaches the Claude-native primitive)

- **(a) Bounded `claude -p` research-subagent dispatch (recommended).** The provider
  reaches the primitive via a `claude -p` subprocess (the subscription path, no
  API key) running a **research-shaped prompt that itself has WebSearch/WebFetch**,
  returning a structured three-axis result the provider then synthesizes. Composes
  the Claude-native forked-research-subagent primitive (the subagent does the web
  research); obeys `feedback_no_anthropic_api_key`; degrades to a fallback synthesis
  when `claude` is absent (AC.DRRGRACE.1). Mirrors the odd-extractor
  `claude_print_synthesis_client.py` subprocess shape.
- **(b) Persona-invoked forked-context SKILL; the provider consumes a cached
  result.** A `context: fork` research SKILL the *interactive persona* invokes (when
  the intake reaches the opt-in), which caches a result the provider reads. Keeps
  the heavy research in the session (where the Agent toolset natively lives) rather
  than a subprocess — but it splits the flow across two surfaces (persona + provider)
  and means the provider alone (a CLI / pytest run) cannot produce a real result
  without the persona having run first. Heavier handoff; worse outcome-altitude
  story.
- **(c) A bespoke in-process web-research client (direct HTTP + an LLM synthesis
  call).** The provider does its own HTTP fetching + a `claude -p` synthesis. Maximal
  control, but it **rebuilds** the web-research primitive the dispatch said to
  compose on (Lens-1 violation), and re-implements ranking/fetching the Claude-native
  research subagent already does well.
- **Recommendation: (a).** It is the composition the dispatch asks for, expressed
  through the one LLM-call mechanism loam allows (`claude -p`): the subprocess IS a
  Claude session with the Agent/WebSearch/WebFetch toolset, so the web research runs
  in the Claude-native primitive, not a rebuilt one (Lens 1), and the provider stays
  SDK-free (no-API-key). (b) is a reasonable owner preference if the owner wants the
  research to run in-session under the persona rather than a subprocess — but it
  weakens the provider's stand-alone outcome-altitude and adds a two-surface handoff.
  (c) is rejected as a Lens-1 rebuild. **Confidence: high on (a) as the
  Lens-1-correct + no-API-key-correct shape; medium on whether the owner prefers the
  in-session (b) split — surfaced because reasonable people weigh "research in a
  subprocess" vs "research in the session" differently (M5).**

### D-RES-2 — the research budget + the surfaced-idea count (how small is "small," how few is "few")

- **(a) Tight: ≤3 research round-trips per axis ceiling + 3 surfaced ideas total
  (recommended).** A hard cap of roughly **3 search/fetch round-trips** as the
  research ceiling (the subagent is told to stay within it), and **3 surfaced
  leverage ideas** total — at most one per axis — folded into the intake's close.
  Over-reach-guard-tight: enough to be useful to an overwhelmed user, short enough
  not to re-overwhelm.
- **(b) Medium: a larger budget (~5–8 round-trips) + 3–5 surfaced ideas.** More
  thorough research, a slightly richer set. More useful per-run, but it edges toward
  the heavyweight first-touch the over-reach guard warns against for THIS user, and
  costs more subscription per opt-in.
- **(c) Owner-configurable budget (a setting), default tight.** Expose the budget +
  count as a `<ws>/.loam/` setting, default to (a). Maximally flexible, but it adds a
  config surface this slice does not need yet (YAGNI — defer the setting to a later
  slice if a real need surfaces).
- **Recommendation: (a).** The user who reaches this seam is the most-overwhelmed
  user loam serves; the over-reach guard applies twice (Surface #3). A tight budget +
  3 ideas is the guard made concrete: useful, short, cheap. (b) is defensible if the
  owner values thoroughness over the proportionality guard for this opt-in path; (c)
  is deferred as premature config. **Confidence: high on the SHAPE (tight, over-reach
  guarded); medium on the exact numbers — the 3/3 is a reasonable owner product call,
  not a derived constant, so it is surfaced for the owner to set.**

### D-RES-3 — synchronous vs asynchronous (does the provider block the intake turn?)

- **(a) Synchronous with a hard timeout + a fallback (recommended for this slice).**
  The provider runs the bounded research synchronously at the opt-in moment and
  returns within a hard timeout; if it times out / fails, AC.DRRGRACE.1's fallback
  synthesis is returned. The intake already has the user's attention at the opt-in;
  a bounded (D-RES-2) research finishes fast enough to keep them.
- **(b) Asynchronous — kick off research, surface ideas when ready.** The provider
  returns immediately with "I'll bring you ideas shortly," runs the research in the
  background, and surfaces when done. Smoother if the research is slow, but it is
  heavier machinery (a background task + a re-surface path), harder to test at
  outcome-altitude, and unnecessary if D-RES-2 keeps the research bounded + fast.
- **Recommendation: (a).** A bounded research pass (D-RES-2) is fast enough to run
  synchronously within a hard timeout, and synchronous keeps the slice simple +
  testable at outcome-altitude. (b) is the right *eventual* shape if the research
  grows (a fast-follow on this fast-follow, §7), but it is over-built for a bounded
  pass now. **Confidence: high — (a) is the simplest shape that meets the bound; (b)
  is the only live alternative and only if the research can't stay fast.**

---

## §12. Provenance trail (load-bearing sources, with refs)

- **The seam this slice fills (the fixed contract):**
  `framework/workspace-bootstrap/src/loam/workspace_bootstrap/deep_role_research.py`
  (the `ResearchProvider` Protocol lines 69–79, `RoleResearchResult` +
  `as_leverage_ideas()` lines 46–66, `StubResearchProvider` lines 82–106,
  `default_research_provider()` resolver lines 114–119, `is_stub` flag the
  real-not-stub signal). Sealed at `96aae8a`.
- **The consumer (the fold-back contract this slice must not break):**
  `framework/workspace-bootstrap/src/loam/workspace_bootstrap/translate_in_intake.py`
  `_run_fallback_ladder` (lines 410–462 — the idea-vacuum opt-in path reaches
  `provider.research_role(role)` and folds `research.as_leverage_ideas()` into the
  close); the idea-quality continuum docstring (lines 24–34 — only the
  idea-vacuum + role + opt-in path reaches the seam).
- **The sealed invariant NOT to regress:**
  `framework/workspace-bootstrap/tests/test_AC_ONDEEP_deep_research_seam.py`
  (AC.ONDEEP.1 — baseline never triggers research; AC.ONDEEP.2 baseline-side — the
  seam is callable + degrades gracefully).
- **The N3 parent plan (the fork that declared this slice + the deferred PASS):**
  `docs/plans/n3-onboarding-init-flow-translate-in-intake.md` §11 D-5 (a) (lines
  771–801, RATIFIED 2026-05-31), §7 out-of-scope (lines 512–519 — the PASS
  deferred), AC.ONDEEP.2 (lines 405–418 — "If D-5 = fast-follow, this AC is
  verified in the fast-follow slice"), §13 verdict matrix (AC.ONDEEP.2 = "SEAM
  GREEN / PASS deferred").
- **The Lens-1 primitive + the session-tool reality:** `docs/CLAUDE_CAPABILITIES.md`
  §6.2 (forked-context skills `context: fork`, ~line 601), §7 (the Agent tool +
  subagent dispatch, `background: true` ~line 704; `WebSearch`/`WebFetch` in the
  Agent toolset, ~line 218) — Tier-0 finding: these are SESSION tools, not
  importable functions (Surface #4 / §10.1).
- **The no-API-key + `claude -p` synthesis precedent:**
  `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/claude_print_synthesis_client.py`
  ("NO Anthropic SDK, NO `ANTHROPIC_API_KEY`"; the subprocess shape;
  `--strict-mcp-config`/env-scrub posture); `feedback_no_anthropic_api_key`;
  `feedback_spawned_claude_must_isolate_telegram_plugin` (any spawned `claude` must
  isolate from the Telegram plugin — the research-subagent dispatch must use the
  isolation wrapper / `--strict-mcp-config`).
- **The over-reach guard + prime directive:** `docs/design/loam-doctrine.md` (the
  operating loop, the over-reach guard lines 65–69 — "keep the elaborate version an
  opt-in suggestion, never the default you build");
  `feedback_loam_prime_directive_user_tuned_translation` (leverage FOR THEM, not
  data collection).
- **The boundary (where any persisted output lands):**
  `docs/design/adr/user-state-homes.yaml` (the two legal homes); ADR-0001; gate 9
  `check_boundary_respected`.
- **Methodology:** `plugins/dev-sdlc/docs/conventions/plan-docs.md` (this plan's
  shape); `feedback_test_outcome_altitude_required` (AC.DRROUT.1, AC.DRR.3);
  `feedback_swarming_recursive_decomposition` (the optional research-shim /
  synthesis sub-cycle split); `feedback_loose_AC_text_fix_AC_not_implementation`
  (halt trigger #2); `feedback_record_owner_ratification_before_dispatch` (the §11
  fork-ruling gate); `feedback_dispatch_explicit_loam_amend_apply` (the sealed
  `workspace-bootstrap` amend mechanism); `feedback_value_proposition_as_prime_objective`
  (the AC ladder-up).

---

*Principles applied at authoring: PRIME DIRECTIVE / Lens 0 (the synthesis is the
point — leverage FOR THEM at the bottom of the idea-quality continuum; the research
is the means, the few person-specific ideas are the deliverable); the over-reach
guard applied TWICE (bounded research + short person-specific output — never a dump
to an already-overwhelmed user; D-RES-2 (a) tight budget + 3 ideas);
compose-don't-rebuild (Lens 1 — reach the forked-research-subagent primitive via
`claude -p`, NOT a bespoke web client; the Tier-0 finding that the primitive is a
session tool not an importable function reshapes HOW it composes — D-RES-1 (a));
bounded scope (a fixed research budget is a HARD constraint, not a tunable —
AC.DRR.2 makes exceeding it observable; halt trigger #4); outcome-altitude at the
real seam (AC.DRROUT.1 — a real provider on a sample role through the real seam,
is_stub=False); ODD authoring (every AC outcome-shape, method-in-AC test passed,
the budget number + idea count deliberately NOT pinned — pinning them would be
method-in-AC); no-API-key (every LLM call via `claude -p`, halt trigger #7);
SEALED-not-license (the featherlight gate + the interface are sealed; this slice
fills the PASS without re-opening them — AC.DRRSEAM.2 guards the invariant);
scope↔confidence (TIGHT where N3 + the doctrine settled it; the THREE
architecture/product calls FORKED with recommendations where confidence in a single
correct shape is medium — owner rules); swarming (the research-shim + synthesis may
split to sub-cycles with tighter ACs); F2 (named the session-tool-vs-importable
finding, the unbounded-research risk, the dump risk, the soft-synthesis-quality
risk, the live-test-nondeterminism risk, the honest M–L size — each with evidence +
an alternative).*

---

## §13 §status — verdict matrix (backfilled at seal)

*Populated at seal time per the standard ladder. Forks D-RES-1..D-RES-3 ruling
recorded in §11 BEFORE the build dispatch.*

| AC | Verdict | Evidence |
|---|---|---|
| AC.DRR.1 (real provider, 3 axes, is_stub=False) | _pending build_ | |
| AC.DRR.2 (research bounded — fixed budget) | _pending build_ | |
| ★ AC.DRR.3 (output short + person-specific — not a dump) | _pending build_ | |
| AC.DRRSEAM.1 (satisfies sealed Protocol; fold-back unchanged) | _pending build_ | |
| ★ AC.DRRSEAM.2 (featherlight invariant AC.ONDEEP.1 still holds) | _pending build_ | |
| AC.DRRGRACE.1 (unavailable → fallback, never raise/hang) | _pending build_ | |
| ★ AC.DRROUT.1 (outcome-altitude — real provider through real seam) | _pending build_ | |
