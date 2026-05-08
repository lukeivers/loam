# Leverage Discipline — How loam Stays on the Highest-Leverage Development Path

Authored 2026-05-08. Methodology-tier doc, peer to ODD methodology +
release-versioning policy + ODD-SemVer pinning + personas methodology.
Authority above: `docs/rebuild/VALUE_PROPOSITION.md`. Authority below:
`docs/release-roadmap.md` and any specific re-rank output.

This doc answers a single question: **how does loam decide what to
build next, and how does it know when to stop building something it
already started in favour of something with more leverage?** It names
the inputs the persona and Luke watch, the decisions those inputs
drive, the cadence on which they're reviewed, the measures that count
as "leverage," and the rubric the persona walks before committing a
work item to a version.

Specific roadmap re-ranks are out of scope. The first application of
this discipline — consuming the harness-landscape research dispatch
and re-ranking v0.4.0+ accordingly — is named in
`docs/plans/research/harness-landscape-and-roadmap-rerank-plan.md` and
is a separate work item.

---

## §1 What "leverage" means in loam

Leverage is the ratio between the **value-prop advancement a unit of
work delivers** and the **token + maintainer cost it consumes.**
Loam's value proposition has two tests, both load-bearing
(`docs/rebuild/VALUE_PROPOSITION.md` §The test for any future
feature):

1. **Primary-persona test** — does the work reduce translation burden
   between the user's natural-language intent and AI-effective
   execution?
2. **Harness test** — does the work add to the toolkit the primary
   persona can draw from?

Work that fails both tests fails leverage even if it looks productive,
and work that scores high on both is high-leverage even if the
artefact is small. The value-prop tests are the load-bearing measure.

**External-attention work is the second axis.** Visibility (GitHub
stars, releases adopted, mentions, real users running loam past
install) is a legitimate leverage axis distinct from value-prop
advancement, for two reasons:

- **Bus-factor-1 mitigation.** loam is a one-person foundation
  authored against a health context that is explicitly in-scope
  (`docs/rebuild/FUTURE_IDEAS.md` Idea 12 risk block). External
  attention recruits co-maintainers, which is risk reduction not
  vanity.
- **Real-user calibration.** The codebase generates synthetic
  benchmarks; only real users generate the calibration data that
  exposes whether the value-prop tests still match reality. Without
  external users loam optimises against a model of itself.

The two axes are not interchangeable. Value-prop advancement is the
prime objective; external attention is a leverage axis of the same
methodology tier but a lower priority when they conflict — see §6 on
the F2 RF tension.

**Architectural commitments are constraints on leverage, not
inputs.** Subscription-only via `claude -p`, no Anthropic API key
required, Claude-Code-attached harness — these are non-negotiable for
this project. Industry trends incompatible with them are noted but
don't pull rank order; they get logged in FUTURE_IDEAS for later
re-evaluation if the architecture itself ever revisits.

---

## §2 Inputs we monitor

Eight inputs feed leverage decisions. Each carries a capture mechanism
and a surfacing path so the input becomes actionable rather than
decorative.

### 2.1 Industry research

Frameworks (LangChain, Mastra, swarms, AutoGPT successors), agent
products (Devin-class, Cursor-class, Replit Agent), and recent papers
(arxiv on agent architectures, judge patterns, swarm coordination).

- **Capture:** weekly Friday-morning scan; the persona drafts a
  one-page brief with the top 3-5 items and what each tells loam.
- **Surface:** `docs/rebuild/FUTURE_IDEAS_DRAFT.md` for items worth
  capturing; direct mention in chat for items that warrant immediate
  re-rank consideration.
- **Acts on:** Luke (rank-order rulings); persona (drafts options +
  recommendations).

### 2.2 Real-user feedback

Eric-class signals (one specific user trying to do real work with
loam), ProgramBench scores (loam's external benchmark target), GitHub
issues / PRs once the OSS launch lands.

- **Capture:** every user interaction surfaces a structured note — what
  they tried to do, what loam did, where the translation failed.
- **Surface:** capture into FUTURE_IDEAS_DRAFT immediately; the next
  per-minor retrospective (§3) folds them into the leverage scoring.
- **Acts on:** persona drafts; Luke rules at the retrospective.

### 2.3 Internal feature-honesty audits

Built capabilities the persona doesn't actually invoke; documented
features the build doesn't actually implement; ACs satisfied
mechanically but not in spirit.

- **Capture:** the per-minor retrospective walks every feature shipped
  in that minor and asks "did the persona use this in the wild, in a
  way a real user surfaced naturally?" If no, it's a leverage red
  flag.
- **Surface:** retrospective output names them explicitly; if a
  pattern emerges (e.g. three minors in a row shipping unused
  capability) it triggers a methodology-level look.
- **Acts on:** Luke at retrospective.

### 2.4 Benchmark performance shifts

ProgramBench is the primary external benchmark; internal
fixture-driven tests are the secondary signal.

- **Capture:** ProgramBench runs at every minor release-gate; per-minor
  delta logged.
- **Surface:** the release-roadmap entry for the next minor records
  the baseline; the retrospective records the delta.
- **Acts on:** persona + Luke. A regression that crosses a named
  threshold triggers a roadmap re-rank to prioritise the regressed
  axis.

### 2.5 Value-prop drift / stress-test signals

The two value-prop tests can drift over time. A feature that scored
"reduces translation burden" at v0.2 may stop reducing it at v0.5
because the user's expectations evolved.

- **Capture:** quarterly strategic review (§3) re-applies the two
  tests to the existing capability set with current real-user
  context.
- **Surface:** the review output names features whose value-prop score
  has dropped.
- **Acts on:** Luke at quarterly review. Output is methodology-level
  not roadmap-level — what changed about the user's expectations
  before specific features get re-ranked.

### 2.6 Cost-leverage retrospective per-version

Every shipped minor carries an estimated AI-time + actual AI-time
delta and a value-prop advancement score (qualitative; named in the
retrospective).

- **Capture:** at minor close, the persona drafts a retrospective:
  estimated vs actual cost, what value-prop tests advanced and by how
  much, what the next minor inherits.
- **Surface:** appended to the release-roadmap entry for that minor;
  fed into the next minor's planning.
- **Acts on:** Luke.

### 2.7 Bus-factor-1 vulnerability indicators

The single-maintainer risk has observable signals: external interest
not being capitalised on, contributor pipeline empty, no co-maintainer
candidates surfaced, Luke's energy bottlenecking response on the
public surface.

- **Capture:** quarterly strategic review explicitly walks bus-factor
  signals; per-minor retrospective notes if any landed during that
  cycle.
- **Surface:** named explicitly in retrospective + quarterly outputs.
- **Acts on:** Luke. This input is what makes "external-attention
  work" a legitimate leverage axis rather than vanity (§1).

### 2.8 Maintainer (Luke's) energy + availability

Loam's prime constraint is the maintainer. ADHD, autism, chronic
pain, insomnia are explicit design-in-scope variables, and the
highest-leverage path on a low-energy week is not the same as the
highest-leverage path on a high-energy week.

- **Capture:** Luke surfaces energy state directly; the persona
  notices via interaction patterns (short replies, deferred decisions,
  late-night sessions piling up).
- **Surface:** persona names it when scoping the next work block; "is
  this a high-energy or low-energy week's work?" gets answered before
  dispatch.
- **Acts on:** persona at dispatch-shape; Luke when scoping commits to
  big architectural pushes.

A low-energy week's high-leverage path may be **doc consolidation,
small fixes, retrospective writing, external-attention work** rather
than a deep architectural push — even if the architectural push has
the higher value-prop ceiling. The discipline rewards finishing what
fits the energy budget over starting what won't finish.

---

## §3 Decisions the discipline drives

The eight inputs above feed into eight decision shapes. Each input
doesn't necessarily drive every decision, but every decision draws on
≥2 inputs.

1. **Roadmap re-rank.** Promote a backlog item over a planned minor;
   demote a planned minor to backlog. Drawn from §2.1, §2.2, §2.4,
   §2.7.
2. **Minor-deferral.** A planned minor stays in the roadmap but slips
   one cycle. Drawn from §2.6, §2.8.
3. **Minor-drop-to-backlog.** A planned minor is removed from the
   versioned roadmap entirely; lives in FUTURE_IDEAS until re-promoted
   or retired. Drawn from §2.3, §2.5.
4. **Backlog-promotion.** A FUTURE_IDEAS item is promoted into the
   versioned roadmap. Drawn from §2.1, §2.2, §2.4.
5. **New-version-creation.** A new version slot is created between
   existing versions for a high-leverage item that doesn't fit the
   current minor objectives. Drawn from §2.1, §2.4, §2.7.
6. **Architectural pivot.** A constraint changes (e.g. Claude SDK
   evolves to expose a primitive loam was building separately).
   Drawn from §2.1, §2.5.
7. **Methodology amendment.** ODD authoring, persona authoring, the
   leverage discipline itself, or another methodology doc changes.
   Drawn from §2.3, §2.5, §2.6.
8. **Cycle-allocation.** Whether to spend a cycle on a benchmark
   improvement vs a feature, or external-attention work vs internal
   build. Drawn from §2.4, §2.7, §2.8.

The persona drafts decisions with named recommendations
(per Luke's summarize-and-surface discipline) at each cadence
boundary; Luke rules. The audit trail lives in the release-roadmap
entries + retrospective appendices + FUTURE_IDEAS rulings.

---

## §4 Cadence

Three review cadences; each carries a fixed scope and a forcing
function.

### 4.1 Weekly industry-trend pulse

Friday morning. Lightweight. The persona drafts one page covering
what shipped this week in the agent / framework / Claude-capability
space; what each item tells loam; whether anything warrants immediate
attention. Output goes to the running notes; the per-minor
retrospective folds it.

Forcing function: a calendar trigger Friday morning. If the persona
has nothing to surface, the brief says so explicitly — silence is not
the same as "scanned and clean."

### 4.2 Per-minor-shipment retrospective

At every minor close. The persona drafts: cost-vs-leverage post-mortem
(estimated vs actual AI-time; value-prop tests advanced and by how
much), feature-honesty audit (every feature shipped — was it actually
used?), bus-factor signals observed during the cycle, what the next
minor inherits, what should be re-ranked.

Forcing function: the SemVer release tag itself. A minor cannot be
considered shipped until the retrospective is written and committed.

### 4.3 Quarterly strategic review

Every ~3 months. Multi-version horizon. Re-applies the two value-prop
tests to the entire shipped capability set. Walks bus-factor signals
explicitly. Asks the methodology-level questions: do the tests still
match reality? Are there axes the discipline isn't surfacing? Should
the discipline itself amend?

Forcing function: a calendar trigger; at minimum on quarterly
boundaries, sooner if a per-minor retrospective surfaces a
methodology-level concern that can't wait.

The three cadences compose: weekly catches incoming signal, per-minor
catches per-cycle drift, quarterly catches structural drift.

---

## §5 Measures of leverage

Four measures, distinguished by load-bearing vs informational status.

### 5.1 Load-bearing — value-prop test scores

The two tests from VALUE_PROPOSITION are the load-bearing measure.
Each shipped minor scores qualitatively on:

- **Primary-persona translation-burden delta.** Did this minor make
  the user's natural-language intent translate more directly to
  AI-effective execution? Specific examples in the retrospective —
  e.g. "the user said 'do this every 12 hours' and the persona invoked
  the new scheduled-scope primitive directly without asking."
- **Harness toolkit expansion.** What new options did the persona gain
  for translating user requests? Named explicitly — e.g. "scheduled
  scopes, scoped MCP, scope-of-work composition."

Both scores are mandatory at retrospective. A minor that can't name a
specific delta on either test is a leverage red flag worth surfacing
explicitly, not buried in retrospective prose.

### 5.2 Load-bearing — external-attention metrics

GitHub stars, releases adopted (downloads / install scripts run),
mentions in agent-space discourse (HN, Twitter, blog posts, podcasts).
These are load-bearing because of bus-factor-1 mitigation + real-user
calibration (§1).

Quarterly review records a number; the trajectory matters more than
the absolute level. Sub-threshold stagnation triggers a leverage
question: is the discipline surfacing the right cycle-allocation
balance between deep build and external-attention work?

### 5.3 Load-bearing — user-retention signals

Real users running loam past the one-time install. Distinct from §5.2
because attention without retention is a worse signal than no
attention — it means the value-prop tests aren't actually being met
in the wild.

Captured via OSS-launch telemetry once that ships (opt-in, per loam's
privacy posture); pre-launch via direct user contact.

### 5.4 Informational — methodology export

Loam's methodology ideas (ODD authoring, the lens stack, swarming
patterns, leverage discipline itself) being adopted by other projects
is a strong informational signal that loam is generating durable
intellectual leverage, but it's not load-bearing because the prime
objective is value-prop advancement for loam's own users not
methodology dissemination.

Tracked at the quarterly review; named when observed; never
prioritised against load-bearing measures.

---

## §6 Anti-leverage signals

Five patterns that look productive but aren't. The discipline
explicitly surfaces these because they're the failure modes the
two value-prop tests don't catch on their own.

1. **Capability-build that no user reaches.** A feature ships, the
   persona can invoke it, but no real user surfaces a request that
   touches it. Looks productive (capability shipped) but didn't
   advance the value-prop tests in the wild. Surfaced by §2.3
   feature-honesty audits.
2. **Infrastructure investment without adoption signal.** New plugin
   architecture, new auth scheme, new dispatch pattern — built ahead
   of demand. Looks like leverage (the toolkit expanded) but if no
   work item actually consumes the infrastructure, the harness test
   passed mechanically not in spirit.
3. **Industry-trend chasing that breaks architectural commitments.**
   A new framework or pattern shows up; reproducing it would require
   abandoning subscription-only or Claude-Code-attached architecture.
   The trend gets noted in FUTURE_IDEAS; the chase doesn't pull rank.
4. **Feature-creep without value-prop alignment.** Adjacent
   capabilities accumulate around a shipped feature without each
   addition scoring on the two tests. The first iteration of a
   feature passes the tests; the third iteration is polish. Polish is
   legitimate but it's not high-leverage and shouldn't out-rank
   work that scores on the tests.
5. **Re-doing recently-shipped work for cosmetic-only reasons.**
   Renames, doc consolidations, refactors that don't advance the
   value-prop tests. Acceptable as low-energy-week filler (§2.8) but
   not high-leverage; never out-ranks load-bearing work.

The persona names these explicitly in retrospective + dispatch
framing when observed. Surfacing the anti-pattern is leverage even
when correcting it isn't immediate.

---

## §7 Decision rubric

Six questions the persona / Luke walks before committing a work item
to a minor. Output is GO, DEFER, or DROP.

1. **Value-prop ladder.** Does this work reduce translation burden
   for the user (primary-persona test) OR add to the persona's
   toolkit (harness test)? Name the specific delta. If neither, it's
   DROP unless question 2 saves it.
2. **External-attention ladder.** Does this work advance external
   attention, user retention, or bus-factor-1 mitigation in a
   measurable way? If neither this nor question 1 ladders, it's DROP.
3. **Architectural-commitment check.** Does this work hold
   subscription-only via `claude -p`, no Anthropic API key, and the
   Claude-Code-attached harness shape? If no, it's DROP regardless of
   the leverage score on questions 1-2.
4. **Cost vs leverage.** Estimated AI-time × maintainer-energy
   required vs the named delta. If the leverage / cost ratio is
   visibly worse than the next-best work item, it's DEFER.
5. **Cadence fit.** Does this fit the current cycle's energy budget
   (§2.8) and the current minor's objective? If wrong-cycle, it's
   DEFER.
6. **Anti-leverage check.** Is this any of the five anti-patterns
   from §6? If yes, name which one; the persona surfaces explicitly
   even if Luke rules GO anyway.

GO = ladders to value-prop or external-attention with clear
measurement; passes the architectural check; fits the cycle.
DEFER = right work, wrong cycle. Goes back to FUTURE_IDEAS with the
deferral reason captured.
DROP = doesn't ladder, or breaks an architectural commitment. Captured
in FUTURE_IDEAS with the drop reason so the rejection is visible
rather than silent.

The rubric is fast — under five minutes for a well-scoped item. The
persona walks it as part of dispatch-shape drafting; Luke can
short-circuit on intuition but the rubric remains the audit trail.

---

## §8 Bus-factor-1 mitigation as explicit leverage

The discipline treats external-attention work as a load-bearing
leverage axis (§1, §5.2) specifically because bus-factor-1 is named
risk in `docs/rebuild/FUTURE_IDEAS.md` Idea 12: "loam is a one-person
foundation built against a health context that's explicitly
design-in-scope and equally a maintenance-capacity input."

Concrete consequences:

- A cycle that ships zero external-attention work is not automatically
  leverage-positive even if the value-prop scores are strong. The
  retrospective names the imbalance.
- OSS launch (Idea 12) is a leverage event, not a marketing event. It
  recruits co-maintainer candidates, surfaces real-user calibration
  data, and stress-tests the value-prop tests against an audience
  loam can't construct internally.
- "Doc consolidation" or "external-facing writing" framed as
  external-attention work passes the rubric (question 2 ladder) when
  it makes loam more legible to potential contributors. Same activity
  framed as internal cleanup may not.
- The honest framing: bus-factor-1 mitigation IS leverage. Treating it
  as decoration risks the one-maintainer-incident outcome the discipline
  is built to prevent.

---

## §9 Honest tensions (F2 RF)

Three tensions surface explicitly rather than being collapsed.

### 9.1 External-attention vs deep-build

Both are leverage axes; sometimes pulling opposite directions. A
quarter spent on OSS launch + content + community response is a
quarter not spent on v0.6 architectural objectives. The discipline
names the tension at quarterly review and forces explicit allocation
rather than letting deep-build greedily consume the cycle by default.

**Resolution:** value-prop advancement is prime; external-attention is
sub-prime. When the two pull opposite directions and Luke's energy
forces a choice, deep-build wins UNLESS bus-factor-1 indicators (§2.7)
are signalling acutely — at which point the bus-factor risk
calculation reverses the priority. The persona surfaces the question
explicitly; Luke rules.

### 9.2 Industry-trend-following vs architectural-constraint-defending

A pattern shows up that would require abandoning subscription-only or
Claude-Code-attached architecture. The discipline says the
architectural commitment holds (§1, §7 question 3). But at some point
the architecture itself might be wrong; the constraint might be the
limiter rather than the value-prop guard.

**Resolution:** the constraint holds at the work-item level; revisits
happen at the methodology-amendment level (§3 decision 7), not by
silently bending. If the trend evidence accumulates across multiple
quarters, the quarterly strategic review (§4.3) is the right place
to surface "should we revisit the architectural commitment?" — never
in the heat of a work-item rank.

### 9.3 Luke's-energy as input

When Luke is depleted, the highest-leverage path may not be the
most-productive-looking one. A high-energy week's leverage curve
peaks at deep architectural work; a low-energy week's leverage curve
peaks at retrospective writing, doc consolidation, small fixes,
external-attention work — outputs that compound but don't require a
sustained build push.

**Resolution:** the rubric (§7 question 5) bakes cycle-fit in
explicitly. The persona names energy state at dispatch-shape; Luke's
energy is a load-bearing input not a soft factor. Pretending otherwise
risks the burnout cycle Idea 12 names — which is itself a leverage
loss because a depleted maintainer is a slower maintainer.

---

## §10 Composition with the existing methodology stack

The discipline is the layer **above** ODD methodology, persona
methodology, release-versioning policy, and ODD-SemVer pinning. It
decides which work the other methodologies execute against; it does
not replace any of them.

- **ODD methodology (`docs/odd-llm-grounding.lean.md`,
  `docs/odd-llm-grounding-derivation.md`).** Once leverage discipline
  rules a work item GO, ODD shapes how that work is authored
  mechanically — objective, constraints, ACs, no method
  prescription. Leverage discipline answers "should we build this?";
  ODD answers "if we build this, what's the contract?"
- **Personas methodology (`docs/personas-methodology.md`).** Persona
  shape is ONE class of work item. The leverage discipline rules
  whether a proposed persona belongs in the next minor; the personas
  methodology rubric rules whether the persona shape is correct. The
  two compose: leverage gates entry, personas methodology gates form.
- **Release-versioning policy (`docs/release-versioning-policy.md`).**
  SemVer is the contract loam ships against. Leverage discipline
  decides which work goes in which version slot; release-versioning
  policy decides what counts as a minor vs patch and when 1.0.0
  ships.
- **ODD-SemVer pinning (`docs/odd-semver-pinning.md`).** Each minor is
  an ODD cycle with outcome-altitude ACs. Leverage discipline decides
  which outcomes the next minor's ACs target; ODD-SemVer pinning
  enforces the structural mapping between ODD and SemVer.

The four prior methodology docs answer "given a work item is selected,
how do we author/release/structure it?" Leverage discipline answers
"which work items get selected, on what cadence, and how do we know
when to drop one in favour of another?"

The first application of this discipline is the harness-landscape
research consumption (`docs/plans/research/harness-landscape-and-roadmap-rerank-plan.md`)
followed by a v0.4.0+ re-rank decision. That work is out of scope for
this doc; it's the test of the doc.

---

## §11 What this doc is not

- Not a roadmap. The roadmap (`docs/release-roadmap.md`) is the output
  of applying this discipline; this doc is the framework.
- Not a methodology amendment proposal. Methodology amendments are
  a decision shape (§3.7) the discipline drives, not the discipline
  itself.
- Not a survey of other projects' release discipline. Linux kernel,
  Rust release, and others have their own disciplines; loam's
  discipline is drawn from loam's value-prop, not from comparative
  research.
- Not automated. The cadences are calendar-triggered and persona-
  drafted but Luke-ruled. Cron jobs / automation are a follow-on if
  the discipline beds in and the manual cadence is the bottleneck.
- Not exhaustive. The eight inputs and four measures are the
  discipline's starting set; they evolve at quarterly review when
  the discipline itself amends (§3.7).
