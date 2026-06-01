# loam 1.0 Acceptance Smoke — the non-tech-user end-to-end gate

**Status:** DESIGN CAPTURED — build sequenced AFTER foundation polish (owner
directive, Telegram 13358 + 13359, 2026-05-31). Do NOT build the full harness
until the foundation-polish step (proper install / PyPI #21, migration
auto-detect, skill triage #35) is sealed — the smoke gates against a *finished*
onboarding pipeline; building the measuring stick before the thing it measures
is settled only churns it.

**Owner intent (verbatim, 13358):** *"build a new smoke test for evaluating when
we have completed all the pieces of loam that you're currently building...
operate on a newly instantiated version of loam as a non-tech user... build a
script to follow in your conversation with the newly initialized version of
loam... emulate a non-technical user who picks some sort of white-collar job
that seems plausible to be given an AI and is told to make use of it to automate
and become more efficient in their work. Build out a solid script and make sure
that we get the outcomes that we would anticipate getting from the interview
questions... I want a really thorough test. I'm thinking about calling this 1.0
version for loam and I want to make sure that that's really going to deliver what
it promises."*

---

## 1. Objective

A repeatable, thorough acceptance smoke that answers a single question in the
owner's terms: **does a freshly-instantiated loam deliver its prime-objective
promise — per-user-tuned translation — to a genuinely non-technical white-collar
user who was simply told "use this to automate and get more efficient"?**

The smoke is the 1.0 gate. If it passes, loam earns the 1.0 label; where it
falls short, it names exactly which promised outcome didn't land.

This is NOT a unit test of the onboarding modules (those exist:
`test_AC_ONFIRE_*`, `test_AC_ONINTAKE_*`, `test_AC_ONSEED_*`,
`test_AC_DRR_*`). It is an **outcome-altitude** test (per
`feedback_test_outcome_altitude_required`): it drives the *real* production
entry point — a freshly `loam init`'d workspace + the first-run intake — through
a full role-played conversation, and judges the *end state* against what the
prime objective promises, not against any inner module's return value.

## 2. What "the prime objective promise" means here (the rubric source)

Straight from `docs/VALUE_PROPOSITION.md` — the smoke's pass-criteria are the
acceptance criteria of the prime objective:

1. **The user never had to do translation work.** They spoke in their own
   domain language ("I spend two hours a day on X"); loam owned the *how* (which
   mechanism, what recurrence, what framework). If the transcript shows the user
   being asked to pick mechanisms, understand context windows, or learn syntax —
   FAIL.
2. **loam learned the specific person.** The seed/profile loam writes reflects
   *this* user's actual job, weak spots, and what they want to offload — not a
   generic template. Same opening request from two different role-plays must
   produce two different seeds.
3. **The four-step loop ran.** Infer real end-intent → propose a healthy way to
   enable it (scaled to what this person showed they want) → surface it back to
   check → learn from the answer. The inferred intent appears as a *surfaced
   hypothesis*, never a silently-built assumption.
4. **It did not over-engineer.** The "do this once → shouldn't this be a
   framework?" failure mode is guarded: structure scales to what the person has
   shown they want; the elaborate version stays an opt-in suggestion.
5. **It closed on ONE concrete thing** the user wants to STOP or START (the
   13340/13343 onboarding design close), and it did not feel like an
   interrogation.
6. **The protection floor held.** No invented capability ("loam will email your
   team every morning" when no email is wired), no lost context across the
   conversation, no silent breakage of what it set up.

## 3. The three variants (different end-outcomes, same gate)

Each variant is a fully-scripted role-play of one non-technical white-collar
person. The role is plausibly "handed an AI and told to get more efficient."
The three exercise the three onboarding paths the pipeline was built to handle
(idea-richness descending → loam effort ascending; the 13343 continuum):

- **Variant A — comes in with an idea.** The user has a specific thing they want
  ("I want it to draft my property-listing descriptions so I stop spending my
  evenings on them"). *Anticipated outcome:* loam confirms+sharpens the intent,
  proposes a right-sized mechanism (NOT "let's build a framework"), surfaces it
  to check, closes on that one START. Deep-research is NOT triggered (idea-rich).
  Suggested role: **residential real-estate agent.**

- **Variant B — talks through their day-to-day, intent is derived.** The user
  can't name a project but can describe their day. loam listens, reflects the
  shape back, and *derives* a candidate STOP/START from the day-description —
  without interrogating. *Anticipated outcome:* loam surfaces a derived
  hypothesis ("sounds like the claim-summary write-ups eat your afternoons —
  want to start there?"), checks it, closes on one thing. Deep-research still NOT
  triggered (day-description gave enough signal). Suggested role: **insurance
  claims adjuster** or **office manager.**

- **Variant C — idea-vacuum → deep-research triggered.** The user genuinely
  draws a blank ("I don't know, I just do my job") and the day-description
  doesn't yield enough either. This is the NEED trigger for
  `deep_role_research_provider` — loam researches what makes someone effective in
  that role / what gets people promoted, and brings *ideas to the party* (the
  13343 "the less good ideas the user has, the more effort we bring"). *Anticipated
  outcome:* the idea-vacuum opt-in path fires, the bounded role-research runs
  (≤3 round-trips, ≤3 ideas — the sealed budget caps), and loam closes on one
  researched, person-specific START the user recognizes as relevant. Suggested
  role: **paralegal** or **medical-office front-desk coordinator.**

## 4. Shape of the deliverable (build, post-foundation-polish)

Two halves — the human-readable script AND an executable harness that proves the
outcomes, because "make sure we get the outcomes we'd anticipate" requires
execution + judging, not a script alone:

1. **The role-play scripts** (markdown, human-readable + machine-consumable):
   for each variant — the persona brief (who they are, how they talk, what they
   do/don't know), the turn-by-turn user lines, and the **anticipated-outcome
   assertions** (deterministic where checkable; rubric-scored where soft).

2. **The runner.** Instantiates a *throwaway* fresh loam workspace via the real
   `loam init` into a temp dir, then drives the scripted user turns against the
   real first-run intake using an **isolated** `claude -p` for the role-played
   user side (per `feedback_spawned_claude_must_isolate_telegram_plugin` —
   `--strict-mcp-config` + empty `mcpServers`; protects the Telegram bot slot;
   no Anthropic API key, subscription-only). Captures the full transcript + the
   workspace's resulting seed/profile/config artefacts.

3. **The judge.** Scores each transcript against the §2 rubric on **named
   orthogonal dimensions** (per the swarming `EVAL_DIMENSIONS` pattern — one
   judge per dimension, concurrent, not one yes/no): `no-user-translation-burden`,
   `learned-this-person`, `four-step-loop-ran`, `no-over-engineering`,
   `closed-on-one-thing`, `non-interrogating-feel`, `protection-floor-held`, plus
   the variant-specific dimension (`deep-research-correctly-(not)-triggered`).
   Deterministic checks (did a seed file get written? does its content vary
   between A and B given different inputs? did variant C stay within the ≤3
   research-round-trip budget?) run as plain assertions; the soft dimensions run
   as isolated `claude -p` LLM-as-judge probes.

4. **The 1.0-readiness report.** Per variant × dimension: PASS / PARTIAL / FAIL
   with the transcript evidence. The top-line verdict is the 1.0 recommendation.

## 5. AC ladder (outcome-shape, method left to the builder)

- **AC.SMOKE.1 (outcome-altitude):** running the harness with zero pre-arranged
  workspace state instantiates a real fresh loam and produces, for each variant,
  a scored report — driving the production `loam init` + first-run intake entry
  points, not any inner module.
- **AC.SMOKE.2:** the three variants produce *materially different* seeds/closes
  from each other (proves per-user learning, not a template) — a deterministic
  cross-variant diff assertion.
- **AC.SMOKE.3:** variant C and only variant C triggers the deep-role-research
  path, and its run stays within the sealed budget caps (≤3 round-trips, ≤3
  ideas); variants A and B reach zero research (the featherlight invariant
  AC.DRRSEAM.2 holds end-to-end).
- **AC.SMOKE.4:** every §2 rubric dimension is scored for every variant with
  cited transcript evidence; any FAIL names the specific promised outcome that
  didn't land.
- **AC.SMOKE.5:** the harness is re-runnable and self-cleaning (throwaway temp
  workspace; no residue in the real user homes `~/.claude` / `<ws>/.loam`).

## 6. Forks — ruled (recorded before build, per the build doctrine)

- **F-1 script-only vs runnable harness →** BOTH. The owner asked to "make sure
  we get the outcomes" — that obligates execution + judging, not a static
  script. (Higher value; matches "really thorough.")
- **F-2 who picks the three jobs →** the builder picks three concrete plausible
  non-technical white-collar roles meeting the §3 constraints; the suggested
  roles are defaults, not a cage. Constraint: each role must plausibly be
  "handed an AI and told to automate," be genuinely non-technical, and the three
  together must exercise idea-rich / day-derived / idea-vacuum.
- **F-3 how outcomes are judged →** deterministic checks for the checkable
  (artefact written? cross-variant diff? budget respected?) + isolated
  `claude -p` LLM-as-judge on named dimensions for the soft outcomes. Not a
  single pass/fail blob.
- **F-4 run against current state or wait →** the harness is built and first-run
  AFTER foundation polish (owner 13359), then re-run as the final pieces land;
  it is the measuring stick for the tail of the 1.0 queue, re-runnable each time.
- **F-5 isolation →** the role-played-user `claude -p` and every judge probe
  spawn ONLY through the spawn-isolation primitive (Telegram-slot protection +
  no API key). Non-negotiable.

## 7. Sequencing + dependency

Build order in the 1.0 queue: ... → **foundation polish** (install/PyPI #21,
migration auto-detect, skill triage #35) → **THIS smoke (build + first run)** →
1.0 label decision. The smoke depends on a stable `loam init` (foundation
polish hardens exactly that), which is why the owner placed it last. The other
in-flight builds (defined-workflow #38, self-recovery #31) land before
foundation polish and are themselves surfaced *as outcomes* the variants may
exercise (e.g., a workflow proposed during intake; a recovery path if the
role-play user gets confused).

---

*Captured by the primary persona, 2026-05-31, off Telegram 13358/13359. The
heavy build (full scripts + runner + judge + first run + report) is a dispatched
background build, fired when foundation polish seals — not in-thread, not now.*
