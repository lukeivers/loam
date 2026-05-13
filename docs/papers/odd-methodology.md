# Objective-Driven Design: Methodology Description and Case-Study Observations from LLM-Authored Software

*v19 draft — 2026-05-12*

---

## On this artefact

This is a **case-study report**, not a venue-submitted methodology paper. The intended reader is a technically-fluent reviewer who is willing to evaluate research-in-progress on its own terms: what the methodology proposes, what was observed in the cases we ran, what the case data does and does not support, and what would be needed to convert the case-study observations into population-level methodology claims.

We frame the artefact this way for two reasons. First, the empirical surface is small — n=4 on the target task plus n=1 cross-task on four other tasks. This is a real constraint imposed by token-cost economics rather than by methodology design; we report what we could afford to measure, and we name the experiments we did not run explicitly so the reader is not invited to draw conclusions the data cannot support. Second, the methodology itself is still under active development; some of its mechanisms (drift-halt at §3.1, the build-next stage at §3.4) are specified but not exercised in the reported runs. The honest framing is "here is the methodology, here is what we observed when we applied it at the volume we could afford, here is what we still need to measure" — and that framing maps to case-study, not venue methodology paper.

The artefact is intentionally dual-audience: human reviewers reading it as a case-study report, and AI agents that may read it as a methodology source when implementing the methodology in their own toolchains. Most sections (§1–§5, §7, §8) carry the methodology framing plus case observations. Two sections are explicitly NOT extractable as structural rules: §4.3 (risk-band classifier) is builder-discipline guidance for human or human-in-the-loop application rather than an automatic rule, and §6 (toolchain composition) is descriptive composition mapping at architectural altitude with operational specifics (record schemas, retrieval procedures, budget bounds) deferred to the implementation distribution. The framing is made explicit so reviewers can apply the lens that fits each section.

---

## Abstract

Test-driven and behaviour-driven methodologies assume the test author and the implementation author share context. LLM-authored software breaks that assumption: the agent rarely shares the human author's mental model, and standard methodologies produce specifications at the wrong altitude — implementation facts mislabelled as objectives, methods baked into acceptance criteria, code paths shipped without a contract naming them. This case-study report describes Objective-Driven Design (ODD) — four altitudes (objective, constraint, capability, implementation); a strict mapping rule with re-extension as a first-class affordance; an outcome-altitude acceptance requirement; and multi-channel objective extraction — and reports observations from applying ODD against two cases: a motivating example on a production TypeScript application (the worked case the methodology was developed against; explicitly non-validating) and a case study on five tasks drawn from ProgramBench (test-suite-hidden during generation; n=4 target-task replication out of 5 attempts; n=1 cross-task regression-check on four other tasks). The empirical volume is small by design — limited by token-cost economics rather than by methodology — and the report's findings are reported at case-study altitude: directional observations from the specific reps we ran, with the comparisons that would convert them into population-level claims explicitly named as future work.

**Key observed findings.** The case study traces three configurations on yj. Under Layer A alone (multi-channel extraction; no iteration substrate), n=3 reps all compile-failed and scored 0% — submissions did not survive ProgramBench's compile gate. Under a pre-substrate configuration that added an engineering retry layer (compile-loop) and a methodology-derived extract-empty-loop, the four scored reps (5 attempted, 1 DNF) reached mean 23.06%, with two reps near 40% and two reps with near-floor pass rates (5.33% and 8.24%; binaries compiled cleanly but produced little useful runtime output across the test corpus). Under the 4-layer substrate that added two further methodology-derived layers (README-self-test, behavioral-equivalence), the four scored reps (5 attempted, 1 DNF) reached mean 47.09%, with all four in the 44.48–50.91% band.

**Attribution observation, layer-block resolution.** The full 0% → 47% lift on yj is the joint result of four substrate-layer additions over Layer A. Three of those four are methodology-derived (extract-empty-loop, README-self-test, behavioral-equivalence); the fourth (compile-loop) is generic engineering retry. The pre-substrate-to-post-substrate increment of 23.06% → 47.09% adds two methodology-derived layers (README-self-test, behavioral-equivalence) and zero engineering-retry layers — so this increment is attributable to methodology-derived additions at the layer-block level. The Layer-A-to-pre-substrate increment of 0% → 23.06% adds one methodology-derived layer (extract-empty-loop) and one engineering-retry layer (compile-loop), and is jointly attributable to those two; compile-loop is necessary infrastructure here (without it, non-compiling submissions ship to evaluation and score zero by construction, so no methodology layer's contribution would be measurable). The case-study claim the methodology defends — at n=4 case-study altitude, subject to the confounds named in §5B.2 that the within-batch comparison cannot rule out — is that **the second-increment lift (23% → 47%) coincides with methodology-derived layer additions on a substrate where engineering retry was already running**; the first-increment lift involves engineering retry as necessary infrastructure and is not a claim about methodology alone. Population-level attribution awaits the contemporaneous ablation named in §7.2.

This attribution is at the layer-block level only — finer-grained per-layer attribution within the methodology-derived block (which specific layer caught which failure) requires an ablation we have not yet run. The pre/post comparison also has confounds the data cannot exclude: the pre-substrate and post-substrate batches differ in time as well as layers, so model-version drift, prompt-template revisions, retry-budget tuning, or surrounding-harness changes during the development interval are alternative explanations the within-case-study comparison cannot rule out. A controlled contemporaneous ablation against a non-methodology pipeline at comparable n is the experiment that would harden the layer-block attribution into a population claim; we identify it as future work (§7.2). The within-case-study observation is what the case-study data supports; population-level attribution awaits the contemporaneous ablation.

Cross-task results at n=1 (csview/gron/htmlq/figlet) are regression-check altitude and cannot attribute deltas to substrate vs sample noise; the gron −14pp delta is identified as warranting replication. We discuss how ODD composes with primitives LLM-attached harnesses provide.

---

## 1. Introduction

Methodologies that govern human-authored code — TDD [Beck 2002], BDD [North 2006; Wynne & Hellesøy 2012], ATDD [Adzic 2011], design-by-contract [Meyer 1997], user stories [Cohn 2004] — were designed for builders who share the original author's intent. The author writes a test; the builder reads it; both operate against a common mental model. Drift between specification and code is bounded by the small distance between two minds in the same room.

LLM-authored software stretches that distance. The agent has only what the brief, the surrounding code, and its training data tell it. SWE-bench [Jimenez et al. 2024] evaluates language models on real-world GitHub issues and reports model scores against held-out tests; we interpret the substantial gap between in-loop generation success and held-out-test pass rate as consistent with a failure mode where the generated patch is structurally consistent with the brief but semantically misaligned with what the brief was meant to elicit. We treat that interpretation as our framing, not as a finding the cited paper documents in those terms. ProgramBench [Yang et al. 2026] extends the evaluation surface to cleanroom binary reconstruction with hidden test suites; we use ProgramBench as the external benchmark in §5. When the brief is loose or carries the wrong altitude of detail — a function name where an outcome should appear; a library choice where a criterion should appear — the agent may extend the wrong shape faithfully and ship defects that pass implementation-altitude tests; we report observations consistent with this pattern in §5 and present the methodology as the discipline that closes the gap.

Three failure patterns motivated this work. They were observed during the §5A motivating example and are named here as the methodology's targets; §5 reports their incidence in the worked case.

1. **Specification at the wrong altitude.** A spec naming "Express route GET /all-orders returns refunded order data" names an implementation, not an outcome. The objective the route serves — "operators can list refunded orders for review" — is the outcome. Implementation-altitude specs prescribe method, lock the agent into a single shape, and produce tests that assert calls rather than user-observable behaviour.
2. **Acceptance criteria with method baked in.** "The component will reject malformed input via a Pydantic validator" prescribes the validator. The objective is "the component refuses malformed input"; how is the agent's call. Method-in-acceptance couples the test to the implementation and prevents refactor.
3. **Code paths without a contract.** A platform branch no criterion names; a configuration field exercised by no test; a defensive `if/except` for a case the contract says cannot arise. These accumulate silently, lock in behaviours future agents reason against, and propagate violations across iterations.

Objective-Driven Design (ODD) proposes a discipline addressing these gaps: distinguishing four altitudes, requiring every business-logic branch to ladder to a named criterion at the right altitude, and requiring every criterion set to include at least one test that verifies the production code path end-to-end on realistic inputs. Two refinements follow from working the methodology against real systems: the extractor that produces criteria from sparse briefs reads multiple input sources, not just briefing prose; and the verifier that establishes a criterion is satisfied may itself be operationalised as a bounded retry loop when the check is cheap enough that running it multiple times costs less than shipping an unverified result.

The methodology applies wherever software is being authored against under-specified briefs — most directly in agent-authored development, but also in the broader case where the eventual user lacks the vocabulary to specify behaviours in test-shaped form. The non-developer case is a motivating audience; the case study in §5 is an engineered-software case.

---

## 2. ODD Methodology

### 2.1 The four altitudes

| Altitude | Definition | Discriminator |
|---|---|---|
| **objective** | An outcome the system delivers; observable from outside; survives implementation rewrite | If rewritten in a different language with different libraries, would this still describe what the system does? |
| **constraint** | A bound on the solution space; restricts how outcomes are delivered without itself being an outcome | Could the system pass this check while delivering no objectives? If yes, it is a constraint, not an objective. |
| **capability** | A feature serving objectives; one of many possible methods | Could you swap the implementation library inside this capability without changing the objective(s) the capability serves? If yes, this row is capability; if the library *is* the capability (changing the library changes which objective is served), the row is implementation. |
| **implementation** | A specific symbol, file, line, or library | Does this name a specific symbol, file, line, or library that could be replaced without changing the contract above? |

The altitudes are not synonyms. An objective is the outermost statement: what the user gets. A constraint is the perimeter of the solution space — a check the deliverable must pass independent of which objectives it pursues. A capability is one means by which objectives are delivered. An implementation is the specific code.

**Terminology note — outcome-altitude.** Throughout this paper, *outcome-altitude* refers to statements at the **objective** row of this table (we use this term in §4 because the §4 contribution is named for the *outcome* property the methodology requires of acceptance criteria; *outcome-altitude* and *objective-altitude* are synonymous, with *outcome-altitude* preferred for consistency).

**Object relationships.** Each objective carries a *criterion set* containing one or more *acceptance criteria*; each acceptance criterion specifies an observable property the objective's delivery must satisfy. Where this paper says "criterion" without qualifier, the reference is to an acceptance criterion. Where it says "objective," the reference is to the outer statement above the criterion set. The §2.2 mapping rule applies to *individual criteria* (every business-logic branch maps to a named criterion); the §4.1 acceptance requirement applies to *criterion sets* (every criterion set should include at least one outcome-altitude criterion).

**Worked classification on a borderline case.** "Must be accessible via REST" looks like a constraint at first read. Apply the discriminator: the system could fail this check (offering only gRPC) while still delivering its objectives (operators can list refunded orders). REST-availability is therefore a constraint on solution shape, not an objective.

**Worked example on a refund-dispute system.** "Operators can file refund disputes at scale, replacing manual portal clickwork" is an objective. "Every dispute-filing action emits an audit-log entry attributing it to a user" is a constraint. "CSV upload and validation pipeline" is a capability. "Express route POST /process-disputes at src/routes/disputeRoutes.js:120" is an implementation.

### 2.2 The strict mapping rule (with re-extension)

Every business-logic branch, every test, and every functional dependency in a deliverable maps to a named *acceptance criterion* that ladders to a named objective. A branch handling a case, platform, configuration, or concern the objectives do not declare is either a gap in the objectives (the case must be promoted to a named criterion) or a gap in the deliverable (the branch must be removed). Operationally-mandated lines — error handling for OS conditions the runtime semantics demand, logging plumbing, defensive checks the language requires — are not exempt; they are governed by the **re-extension** affordance below, which is part of the rule, not an escape from it.

**Discriminator for borderline branches.** Operationally-redundant = the upstream contract guarantees the case cannot arise (type system, schema validation, prior in-pipeline check). Operationally-mandated = the case can arise and the platform/runtime semantics require handling. Ambiguous cases default to **re-extension** (promote to a criterion); the criterion can then be removed if it lacks backing.

**Worked classification of branch types** (for an agent applying the mapping rule to a diff):

| Branch type | Class | Treatment |
|---|---|---|
| Business-logic branch tied to a named criterion | Mapped | Keep; the criterion is the contract. |
| Defensive null-check on a value the type system already guarantees | Operationally-redundant | Remove (the contract above is sufficient). |
| try/except wrapping a network call where the contract names "user receives an actionable error on network failure" | Mapped | Keep; the criterion names the case. |
| try/except wrapping a network call with no criterion naming network-failure handling | Operationally-mandated → re-extension required | Promote "user receives an actionable error on network failure" to a named criterion; then keep the branch. |
| OS-level error handling (e.g., disk full, permission denied) the platform contract requires | Operationally-mandated → re-extension required | Promote the OS-failure-handling case to a named criterion; then keep. |
| Logging instrumentation tied to an observability-criterion in the objective set | Mapped | Keep. |
| Logging plumbing with no observability criterion | Operationally-mandated → re-extension OR remove | Either promote "the system emits audit-grade log entries for [class of event]" to a named criterion (then keep), or remove if the observability is not actually contracted. |
| Configuration field exercised by no test | Implementation orphan | Either add a criterion that names what the configuration controls (then add a test), or remove. |
| Performance optimisation branch (e.g., fast path for common case) with no perf criterion | Implementation orphan → re-extension required | Promote performance criterion if perf is contracted; otherwise remove. |

The taxonomy is non-exhaustive; novel branch types apply the same rule (is there a named criterion this branch maps back to? if no, re-extension or removal).

**Forward (authoring).** Every declared behaviour in every objective has at least one acceptance criterion. If the objective contains "and", count the conjuncts and verify each has its own criterion.

**Reverse (review).** Every business-logic branch, test, and functional dependency in the diff has an acceptance criterion it maps back to. If you cannot point at one, either promote it to a criterion via re-extension or remove the code.

**Re-extension.** When a builder discovers a case the criterion set does not name — operationally-mandated error handling, an infrastructure concern, a previously-undocumented platform branch — the sanctioned response is to promote the case to a named criterion *with recorded justification*, not to bury it as a silent exception. By "with recorded justification" we mean: at minimum, a short note naming the discovery context and why the case must be handled (the language requirement, the OS condition, the platform contract); ideally a source citation per §3.1's band rules where a source exists. Re-extension is the rule's primary affordance for handling cases the criterion set did not anticipate; the rule's universal-quantifier scope is over *named* criteria, and re-extension is how a case becomes named.

The reverse direction is load-bearing. Forward checks catch under-tested objectives; reverse checks catch the silent accumulation of method that crept in without a contract authorising it. "Might be useful later" is never a backing.

### 2.3 Drift modes

LLM-authored work drifts predictably. The following patterns recurred across the §5A motivating example and the §5B case study; we do not claim the list is exhaustive, and additional patterns may surface in other domains. Each mode is paired with the §2.4 altitude self-check that catches it.

| # | Drift mode | Example | Caught by §2.4 self-check |
|---|------------|---------|---------------------------|
| 1 | Symbol-as-criterion | "Express route GET /all-orders at file:line" labelled a criterion | #2 (implementation-swap fails — a different routing library would not preserve this) |
| 2 | Function-name-as-criterion | "Function processDispute() exists" labelled a criterion | #2 (implementation-swap fails — the function name is implementation) |
| 3 | Feature-as-objective | "App has CSV upload" labelled an objective | #1 (outcome-or-fact fails — CSV upload is a method, not an outcome to a user) |
| 4 | Test-name-as-implementation | A test asserting one function called another | #4 (observable-from-outside fails — internal call patterns are not user-observable) |
| 5 | Gap-as-objective | "Missing test coverage on auth middleware" labelled an objective | #1 (outcome-or-fact fails — absence is a finding, not an outcome) |
| 6 | Constraint-as-objective | "System must be SOC-2-compliant" labelled an objective | #5 (user-purpose fails — SOC-2 is a regulatory constraint, not a user outcome) |
| 7 | Implementation-detail-as-constraint | "Uses RSA-OAEP" labelled a constraint | #2 (implementation-swap fails on the constraint statement — different algorithm satisfies the underlying confidentiality constraint) |

Recognising these at authoring time is cheapest. By review time the drift has often locked in via tests that codify the wrong altitude.

### 2.4 Altitude self-checks

These checks fire at authoring time — applied by the agent producing the candidate, or by the harness reviewing its output before it is declared. They are not deferred to a human reviewer. Before declaring an objective, constraint, capability, or criterion, the producer runs five questions over its own output:

| # | Self-check | Scope |
|---|------------|-------|
| 1 | **Outcome-or-fact?** Outcome the system delivers, or fact about how it is built? | all altitudes |
| 2 | **Implementation-swap.** If rewritten in a different language with different libraries, would the statement still hold true at its altitude? (per-altitude reading: see sub-table below) | all altitudes |
| 3 | **Builder-method.** Could a different builder produce a different shape meeting it? | all altitudes |
| 4 | **Observable-from-outside.** Verifiable from observable behaviour, without reading code? | objective-altitude only |
| 5 | **User-purpose.** Names a purpose, outcome, or value to someone? | objective-altitude only |

**Per-altitude reading for self-check #2 (Implementation-swap):**

| Altitude | Pass condition for check #2 |
|---|---|
| objective | Rewrite still delivers the same outcome to the user. |
| constraint | Rewrite still operates within the same perimeter. |
| capability | Named method is replaceable while preserving the outer objective the capability serves. If replacement also changes which outcome is delivered, the row is misclassified as capability when it is actually an objective. *Applying this row requires access to the criterion-set the candidate belongs to* — agents applying check #2 to a capability candidate in isolation (without the parent objective in context) must first establish the outer-objective context from the criterion-set; check #2 cannot fire correctly on a capability candidate considered alone. |

Self-checks #4 and #5 apply to objective-altitude statements specifically. Constraints and capabilities have their own discriminators (§2.1) and are not required to pass the user-purpose or observable-from-outside checks, since their role is to bound solution space or name a method, not to deliver an outcome to a user.

Any failure indicates the wrong altitude. The fix is to restate, not label loosely.

We refer to these as *altitude self-checks* throughout. The §3.1 drift-halt aggregation runs over the count of altitude self-check applications across candidates; the §5A.1 reported pass rate is also an altitude self-check pass rate. These are the same checks, applied at different points in the pipeline.

### 2.5 Positive framing

Acceptance criteria are stated in the positive: what the system does, not what it must not do. "The component does not crash on malformed input" tests for the bug. "The component refuses malformed input with an actionable error" names the outcome — the rejection is observable, and the error message is the artefact the test asserts on.

ODD takes the position that this converts regressions into objectives: when a defect surfaces, the question is "what objective was missing that allowed this code to ship?", and the answer becomes a positively-stated criterion. The tradeoff is that negative-tested invariants (Given … When … Then NOT …) are widely deployed in BDD practice — Wynne & Hellesøy (2012) document negative-shape scenarios as a routine pattern in BDD scenario design — and are useful for capturing constraints that resist restatement as outcomes. ODD's preference for positive framing is a design choice the methodology defends on the grounds that negative-framed criteria accumulate as regression scaffolding rather than as contracts the agent authors against; constraints remain available as a distinct altitude (§2.1) where they can be stated directly without contortion through criterion shape.

### 2.6 Position relative to adjacent methodologies

ODD operates in a literature occupied by TDD [Beck 2002], BDD [North 2006; Wynne & Hellesøy 2012], ATDD [Adzic 2011], design-by-contract [Meyer 1997], user stories [Cohn 2004], domain-driven design [Evans 2003], and requirements engineering, including Jackson's problem frames [Jackson 2000] and the Zave/Jackson reference model [Zave & Jackson 1997]. The LLM-engineering literature is more recent: code-generation evaluation [Chen et al. 2021; Jimenez et al. 2024; Yang et al. 2026] and agent-scaffolding work [Yang et al. 2024].

ODD's distinguishing claims, stated as our own observations against the prior work we have surveyed rather than as universal negations against the field as a whole:

1. **Strict mapping enforced in both directions.** ATDD literature addresses traceability from criteria to code. Adzic (2011) frames specification-by-example as a writeup discipline where executable specifications grow into "living documentation"; the forward direction (criterion → test → code) is operationalised by Adzic's chapter on collaboration practices and example workshops. Adzic discusses the reverse direction implicitly through the living-documentation lens but does not require every code branch to point back to a named criterion at review time. ODD's reverse direction is more aggressive than the ATDD work we are aware of in that the methodology refuses to ship code that does not map back to a named criterion (re-extension is the only sanctioned response to an unmapped case).
2. **Four altitudes named explicitly.** Jackson's problem frames (2000) distinguish problem-world phenomena from machine-world phenomena and frame requirements as statements relating the two; the Zave/Jackson reference model (1997) formalises the separation between requirements (R), domain knowledge (D), and program (P) via the equation R, D ⊢ P. ODD's four-row table (objective / constraint / capability / implementation) is finer-grained for the LLM-builder case specifically because the capability-vs-implementation split is required to catch the drift mode (§2.3 #3 "feature-as-objective") where features (capability-altitude) are routinely conflated with the libraries that implement them. Jackson's problem-frames decomposition does not separate these two and is not motivated by the LLM-authoring failure mode this paper targets.
3. **Positive framing as design choice.** BDD scenarios accept negative invariants; design-by-contract [Meyer 1997] accepts pre/post conditions stated as negations. ODD prefers positive framing per §2.5, with constraints available at their own altitude. This is a position the methodology defends on accumulated-regression-scaffolding grounds; we acknowledge it as a position rather than as a derived requirement.
4. **LLM-as-builder context as primary.** Yang et al. (2024) address agent-computer interfaces for automated software engineering (SWE-agent) at the agent-environment-interaction level, not at the brief/criterion/test triple level. We are not aware of a methodology in the surveyed literature that takes altitude discipline applied to the spec/implementation/test triple as its primary contribution for the LLM-authored case, with the outcome-altitude acceptance requirement (§4) as the structural enforcement; ODD's contribution is to position altitude discipline as the primary discipline for the LLM-builder workflow rather than as one practice among many.

Where ODD departs from prior methodology, the departure is stated as our observation against the cited work, not against the field exhaustively. A reviewer aware of additional methodology work in the LLM-builder space is invited to point it out; we will engage the specific work rather than maintain an unsupported general negation.

---

## 3. Reverse-Walk Pipeline

A second contribution: extracting outcome-altitude objectives from existing codebases — and, more generally, from whatever input surface the system has access to.

A naive approach feeds the codebase to an LLM and asks for objectives. The output is reliably at the wrong altitude — the training gradient pulls the model toward symbol inventory ("Express route X exists at file:line") and produces structural facts mislabelled as contracts. An earlier single-pass extractor we built labelled 131 outputs as acceptance criteria across the production TypeScript application of §5A. Each output named a structural-extraction tuple — a (file, symbol, kind) triple from the codebase — rather than an outcome-altitude statement about what the system delivers. Applying the §2.4 altitude self-checks to those outputs under conservative rules (any output naming a specific symbol, file path, or library was marked implementation-altitude regardless of surrounding prose) marked 131 of 131 as implementation-altitude. The 100% rate is mechanically determined by the rules-and-substrate pairing: a structural extractor whose outputs by design are (file, symbol, kind) tuples will produce 100% implementation-altitude under any rule that flags symbol-naming as implementation. The informative finding here is therefore not "the prior extractor produced 131/131 wrong outputs" but "the prior extractor's outputs are structural-extraction tuples, not outcome-altitude statements about system delivery." The methodology gap the §3 pipeline closes is real; the 131/131 figure is descriptive of the prior extractor's shape, not a measurement of its quality against a populated outcome-altitude reference.

The reverse-walk pipeline corrects altitude through multi-channel synthesis followed by structural mapping.

### 3.1 Multi-channel input synthesis

The extractor's input surface is multi-channel. Multiple sources contribute — briefing prose, design documents, code under construction, prior tests, and (when present) non-prose artefacts the work operates against. A single-channel extractor that reads only the briefing prose under-fits its source material; the briefing may be silent on a property a different channel pins exactly. The author of the work is not obligated to enumerate every channel; the obligation is to ensure the extractor reaches them.

Five canonical signal sources feed extraction in the codebase case:

1. **README and design documents** — plain-English purpose statements maintainers wrote to explain the system to other humans.
2. **User-supplied context** — the maintainer's own framing.
3. **Test names and assertions** — tests whose names assert outcomes are the closest-to-objective signal in code.
4. **Code-pattern inference** — route shapes, middleware names, subcommand names, flag schemas, page objects, model class names, public-function signatures; domain language carries objective signal across application shapes (web, CLI, library).
5. **Commit messages** — chronological intent; weakest signal, useful for cross-checking.

A sixth channel is conditional, used when reconstructing from a compiled artefact rather than an editable codebase:

6. **(Conditional, compiled-artefact case only) The compiled artefact under reconstruction** — when the target exposes a self-describing interface (help text, version string, embedded strings, observable I/O on probe inputs), each is an extraction channel alongside the prose. §5's case study uses this channel: tasks where the prose briefing was sparse produced no objectives until the compiled-artefact channels were read; the same tasks produced more complete objective sets when they were.

Extraction produces confidence-graded output. Operational definitions:

- **VERIFIED** — at least one of: (a) the candidate objective is the subject of a passing test whose assertion phrases the outcome the objective names (string-similarity check plus LLM semantic-equivalence check, both required); (b) two or more *independent* channels emit the same outcome statement (cross-channel convergence). Two channels count as independent when neither is generated from or transcluded from the other; channels sharing a common source (e.g., `--help` output auto-generated from README annotations; a README that quotes `--help` verbatim) count as one channel for convergence purposes.
- **PLAUSIBLE** — exactly one source citation; no cross-channel convergence; no passing test.
- **HYPOTHESISED** — LLM-inferred from indirect signal (e.g., function-name pattern) with a rationale string explaining the inference path.

Structured form of the band rules:

| Band | Min explicit source citations | Cross-channel convergence | Passing-test condition | Rationale string |
|---|---|---|---|---|
| VERIFIED | ≥1 | OR with passing-test condition | OR with cross-channel convergence | optional |
| PLAUSIBLE | =1 | not required | not required | optional |
| HYPOTHESISED | indirect signal only (0 explicit) | not required | not required | required |

**Band assignment procedure.** Band is determined as follows: (a) if ≥1 explicit source citation present AND (cross-channel convergence OR passing-test condition met), the candidate is VERIFIED; (b) if exactly 1 explicit source citation present and neither cross-channel convergence nor passing-test condition met, PLAUSIBLE; (c) if 0 explicit source citations AND ≥1 indirect signal AND rationale string present, HYPOTHESISED; (d) otherwise the candidate is refused (not emitted). The harness-level verification floor (below) operates on these rules: each emitted candidate is checked against the band-input requirements, and if no band's requirements are met, the candidate is refused. **Convergence rules for mixed and indirect pairs:**

- Two explicit-citation channels converging on the same outcome statement → VERIFIED (the cross-channel sub-clause for VERIFIED applies).
- One explicit-citation channel + one indirect-signal channel converging → VERIFIED. The explicit-citation channel provides the citation; the indirect-signal channel strengthens the rationale; the convergence sub-clause for VERIFIED admits the mixed pair as cross-channel convergence.
- Two indirect-signal channels converging → HYPOTHESISED with strengthened rationale (not VERIFIED). VERIFIED requires explicit-citation backing; indirect-only convergence does not provide it.
- A single explicit-citation channel without convergence and without passing-test → PLAUSIBLE.
- An indirect signal alone with rationale string → HYPOTHESISED.

**Channel-to-band-input mapping.** README and design documents, user-supplied context, test names and assertions, and commit messages are *explicit-citation* channels — a candidate citing one of these can claim ≥1 explicit source citation. Code-pattern inference is an *indirect-signal* channel — patterns observed in code structure produce indirect-signal candidates governed by the rationale-string requirement. The compiled-artefact channel (when present) is explicit-citation for self-describing outputs (help text, version string, embedded strings) and indirect-signal for observed I/O on probe inputs.

Bands enumerate trust, not importance. A HYPOTHESISED objective may name a load-bearing outcome; the band states only how confident the extractor is that it holds.

The synthesis pass invokes an LLM to combine sources into candidate objectives, with altitude self-checks applied programmatically.

**Drift-halt.** The methodology specifies a drift-halt mechanism: the extractor monitors altitude self-check pass rate across the batch of synthesized candidates and halts (rather than completing a diverged chain) when pass rate drops below a calibrated threshold. The threshold is a calibration choice, not a derived constant; in the runs reported in §5 the mechanism is present but did not fire, so its effectiveness is not observed in this work. Implementation details — exact aggregation formula, behaviour on mixed batches with different candidate altitudes, empty-class denominator handling, the checker I/O contract that produces the pass/fail signal — are deferred to the implementation distribution; the methodology requirement is that the extractor halts on observed drift rather than completing a diverged chain.

**Refusal-to-fabricate.** The methodology requires that when the input surface does not support an objective, the extractor refuse to emit fabricated content. Two requirements preserve this property regardless of implementation:

1. The extractor refuses to emit any PLAUSIBLE-or-higher-band candidate without at least one source citation. (HYPOTHESISED-band candidates carry zero explicit citations by definition and are governed by the rationale-string requirement in §3.1's band rules.)
2. The downstream authoring stage treats an empty objective set as a halt condition rather than a generation prompt — an agent receiving zero objectives halts and reports rather than generating code without objectives.

How implementations enforce these (prompt-level, harness-level, or both) is the implementation's choice; the methodology requirement is only that the property holds.

### 3.2 Backing-implementation map

Each extracted objective is mapped bidirectionally to **evidence rows** in the codebase — the route, model, test, or function that contributes to delivering it. An evidence row is a single (file, symbol, kind) triple. Every objective has at least one evidence row; every evidence row is reachable from at least one objective. Where this invariant fails, the failure is itself a finding (orphan, or under-extracted objective).

Three categories of finding emerge:

- **Verified backing.** At least one VERIFIED-band evidence row.
- **Plausible backing.** Source-citation evidence only; the maintainer reads the cited code to confirm.
- **Implementation orphans.** Code paths no extracted objective reaches. Either dead code, or the extraction missed an objective the orphans serve.

Structural extraction that earlier extractors mis-labelled as criteria is repurposed as the backing-map's evidence rows. The mis-labelling was the defect; the inventory itself remains useful.

### 3.3 Gap analysis

Two categories sit on top of the backing map:

1. **Objectives without verified backing** — named objectives backed only by PLAUSIBLE or HYPOTHESISED evidence. Either tests are needed, or the objective is not actually delivered.
2. **Implementation orphans that may indicate missing objectives** — code paths the objectives do not reach. Some orphans are dead code; some surface undocumented outcomes.

### 3.4 Build-next recommendation (exploratory)

The final stage produces a ranked list of candidate next builds, each tied to a gap. Candidates are scored on gap severity, backing confidence, and (when present) operator survey context. Each candidate carries rationale referencing the gap it addresses, the objective it strengthens, and the evidence that shaped the recommendation.

This stage is exploratory in the current work: the §5A motivating example reports that the ranker produced three candidates with prose rationale, but does not evaluate whether the ranking corresponded to operator-preferred build order or correlated with downstream-build outcomes. A future-work item (§7.2) names that evaluation as the load-bearing follow-up before the build-next stage can be claimed as a validated contribution rather than a pipeline component.

---

## 4. The Outcome-Altitude Acceptance Requirement

A criterion is *outcome-altitude* (synonym: *objective-altitude*; the term refers to the **objective** row of §2.1's altitude table) when its verification invokes the production entry-point the user reaches, on realistic inputs, without pre-arrangement that bypasses upstream production stages.

The strict mapping rule (§2.2) catches code paths without a contract. It does not catch contracts at the wrong altitude. The §5A motivating example recorded three sequential integration runs on the same application, each surfacing the same failure shape: a criterion verified against pre-arranged fixtures passes in unit and integration tests; the same criterion verified against the real-world production shape fails at the release-level integration gate.

The pattern. A criterion states "an extraction stage produces objectives." A test invokes the extraction function directly with a stubbed client and asserts on the output shape. The test passes. In production, the CLI never calls the extraction function because the wire-through is missing; it silently falls into an empty-output path. The criterion is satisfied at implementation-altitude (the function works when called); it is not satisfied at outcome-altitude (the user invokes the CLI and gets nothing).

The strict mapping rule does not catch this. It enforces traceability but permits all criteria to live at implementation-altitude.

### 4.1 The rule

Every criterion set should include at least one criterion marked at outcome-altitude, verified by a test that:

1. Invokes the production entry-point the user invokes (CLI, API endpoint, dispatch surface) — not a private helper.
2. Does not pre-arrange state that the production code would normally produce.
3. Produces a real outcome artefact: a file written, a response returned, a side-effect observed.

The first clause prevents the test from asserting on internal helpers the user never reaches. The second is load-bearing: it forbids fixtures that bypass upstream stages by writing those stages' outputs directly.

### 4.2 Pre-arrangement detection

A single primary question discriminates the common case:

> Does this test write state that the production code under test would normally produce?

If yes, the test is **pre-arrangement-class**.

The discriminator admits two refinements:

- **Necessary stubs** are stubs standing in for external systems the test environment cannot reach in practice (third-party APIs requiring credentials; services unreachable from the test environment; paid endpoints the project chooses not to hit per test for engineering reasons of cost or rate-limit). These are not pre-arrangement and do not disqualify a test from outcome-altitude class, provided the stub stands in for an external system and not for an internal production stage. Whether a project counts a paid-but-reachable system as "necessary" is an engineering scheduling decision outside the methodology's scope; the methodology requires only that the production-path wiring be verified somewhere (release-gate test, smoke run, or comparable) when the per-iteration tests use necessary stubs against that system.
- **Pre-arrangement stubs** are stubs standing in for outputs of internal production stages (database state the application would have written, intermediate computation results the production pipeline would have produced). These disqualify the test from outcome-altitude class.

A test is outcome-class when it invokes the production entry-point on realistic-shape inputs, has only necessary-stub class stubs (if any), and asserts on the artefacts the production code produces.

### 4.3 Risk-band classifier (builder-discipline)

The risk-band classifier in this subsection is presented as **builder-discipline**: a list of categories builders apply by judgment to determine whether outcome-altitude verification is required per iteration or deferred to release gate. It is not formalised as a structural check; treat it as guidance for human or human-in-the-loop application rather than an automatically-extractable rule. Formalisation as a structural check is identified as future work (§7.2).

**Per-iteration verification required** when the iteration touches any of: a CLI command or flag; a plugin or extension surface; a user-visible artefact (file, terminal output, error message); a configuration schema; a persistence schema crossing session boundaries. The disjunction is OR: any touched category in this list triggers required-verification, even if the iteration also touches categories in the next list.

**Release-gate verification acceptable** when the iteration touches none of the categories above and is restricted to: internal data structures whose shape is not observed across module boundaries (e.g., a private struct's field reorder, where consumers reach the data only through accessor functions); pure-function refactors; test-only edits; or documentation. Where an internal data structure is observed across module boundaries (e.g., a serialised record's field order is consumed by a downstream parser), that structure is treated as a user-visible artefact for classification purposes.

The classifier composes with the mapping rule: every business-logic branch has a contract; every contract set has at least one production-path probe; production-facing surfaces verify per iteration, internal refactors defer to release.

---

## 5. Motivating Example and Case Study

§5A is a single-application motivating example: the worked case the methodology was developed against, in which the failure patterns §4 was authored to catch were first observed. It is not independent validation. §5B is the case study: an external benchmark study on five cleanroom binary-reconstruction tasks, with the methodology and substrate applied without re-tuning.

### 5A. Playwright TypeScript application (motivating example)

We exercised the methodology against a Playwright TypeScript project of approximately 19,000 lines of TypeScript (production source; excluding tests and generated code; counted via `cloc`-style line-count tool, author estimate from project state at the time of the runs) that automates an external-portal workflow at scale to replace manual operator clickwork. Repository details are omitted to honour operator confidentiality.

**Epistemic scope.** §5A is the worked case the methodology was developed against. The failure patterns it surfaces are the patterns §4 was authored to catch. The case is not independent validation; it is the source from which the methodology's targets were derived. We report what we observed; we do not claim the observations validate the methodology.

#### 5A.1 Four integration runs

The build cycle iterated four end-to-end integration runs against the production code path. Each invoked the four-stage extractor pipeline (extraction, completeness interview, gap analysis, build-next recommendation) against the real codebase with no pre-arrangement.

The progression: failure, failure, failure, end-to-end pipeline completion with no traceback. We use "completion" rather than "pass" because Run 4's success criterion is procedural (pipeline ran, produced outputs of expected shape, internal validators passed at spot-check) rather than outcome-altitude (extracted objectives correspond to maintainer-authored objectives); see §5A.3 for what the Run 4 metrics measure.

- **Run 1.** The CLI's extraction stage produced empty output. Unit tests of the synthesis function passed because they invoked the function directly with a stubbed client. The CLI never wired the client through; the production path silently fell into an empty-extraction branch.
- **Run 2.** The synthesis subprocess used an SDK-based authentication path. The runtime environment did not have the SDK installed. Unit tests passed because they monkey-patched the SDK at import time. The production path tried to import the real SDK and raised.
- **Run 3.** With the SDK replaced, the live LLM returned outputs that violated a banding rule the synthetic fixtures had never produced — outputs claiming the highest confidence band without the multi-source evidence the band required. The validator raised; the user received a stack trace.
- **Run 4.** With upstream stages fixed, the four-stage pipeline ran end-to-end. Six objectives were extracted; all six objectives had backing-map coverage; gap analysis surfaced three objectives without verified backing; build-next produced three ranked candidates with rationale referencing specific gaps. The pipeline's internal altitude self-check validators passed on the spot-checked objectives (procedural detail in §5A.3).

#### 5A.2 The mid-cycle rule shipment

The outcome-altitude acceptance requirement (§4) shipped mid-cycle — after Run 2, with the explicit intent to catch the production-path-bypass failure pattern Runs 1 and 2 exhibited. Run 3 then failed on a different pattern (banding-rule violation, not pre-arrangement). Run 4 passed end-to-end with all four classes of failure addressed. Per the epistemic-scope note above (§5A intro), Run 4's resolution is not validation of the rule — the rule was developed against Runs 1–2 — but the within-case observation that the rule fired on the pattern it targets, and that Run 3 failed on a different pattern the rule does not target (which is the right behavior for a narrowly-scoped rule), remains directly informative about scope and trigger behavior.

The first test authored under the new rule caught a production-path blocker on its first live run — an instance of the failure mode the rule was designed to detect. We resist stronger framings (such as "the rule paid for itself") because a single positive instance is not cost-benefit accounting; the observation is one data point that the rule fires on the pattern it targets. Run 3's failure on a *different* pattern is the more interesting datum: the §4 rule is narrowly targeted at pre-arrangement / production-bypass and does not generalise to all production-path defects, which is consistent with the rule's stated scope.

#### 5A.3 What the metrics measure (and don't)

The pipeline's internal altitude self-check validators were applied to a spot-check of 3 of the 6 extracted objectives at Run 4. The three objectives were selected by the methodology authors during Run 4 readout based on phrasing that the authors flagged *a priori* as potentially borderline (objectives whose surface text contained method-shaped terms like "parallel workers" or implementation-shaped nouns) — not a random sample, and biased toward higher failure rates than a random sample would have produced; the remaining three (which the authors did not flag at readout) were not spot-checked. The 87% figure therefore cannot be generalised to all six extracted objectives and should be read as "the spot-checked-because-suspect three passed self-checks at 87%", not as "extracted objectives pass self-checks at 87%." All three spot-checked items are objective-altitude, so the 5-check rule from §2.4 applies uniformly. With 5 altitude self-checks per objective, this produced 15 total self-check applications. 13 of 15 self-check applications passed (86.7%; reported below as approximately 87%). The 3-spot-check arithmetic: 5 self-checks per spot-checked objective × 3 spot-checked objectives = 15 total applications; 5/5, 5/5, and 3/5 across the three objectives respectively; the third spot-checked objective contained "parallel workers" phrasing that hints at implementation though the outcome it describes — throughput — survives the rewrite test.

This is the pipeline grading its own output against the criteria the pipeline itself was designed to satisfy. The figure is process-altitude, not outcome-altitude: it records that the pipeline's internal validators passed on the spot-checked objectives. It does not measure whether the extracted objectives correspond to objectives a maintainer would author independently, nor whether the gap analysis surfaced gaps a maintainer would judge real. The 80% drift-halt threshold the 87% is reported against (§3.1) is itself uncalibrated; the 87% should not be read as having cleared a validated bar.

The case study's evidential weight rests on the qualitative observation that the four-run sequence surfaced four distinct production-path failures the methodology was designed to predict, not on the Run 4 process numbers as validation. We identify a maintainer-comparison study against this codebase as the load-bearing follow-up in §7.2.

Other Run 4 metrics: full backing-map coverage (one verified, five plausible); three gaps in the inventory; three ranked build-next candidates with prose rationale referencing specific gap identifiers. No tracebacks at Run 4 end-to-end.

#### 5A.4 What the case teaches

Three observations. First, the mapping rule is necessary but not sufficient: it caught none of the four real-world failures because every failing path had a criterion authored against it at the wrong altitude. Second, synthetic-fixture tests cannot substitute for production-path probes — each failure involved an upstream stage the fixtures had pre-populated, bypassing the code the user reaches. Third, the cost of authoring outcome-altitude probes per iteration is bounded — once the fixture exists, it is reused across runs — and rework savings at release-gate are observed but not quantified in the current data; this is consistent with §4.3's framing of outcome-altitude verification as non-trivially costly per iteration, motivating the risk-band classifier.

### 5B. ProgramBench-derivative cleanroom benchmark (case study)

The case study tests the methodology and substrate against an external corpus: five tasks drawn from ProgramBench [Yang et al. 2026] — a benchmark in which the agent receives a compiled binary and its documentation, and must reconstruct the source from scratch. The tasks span Go, Rust, and C; the targets are familiar utilities (yj, gron, csview, htmlq, figlet). All eval runs are test-suite-hidden during generation: the test suite that scores the reconstruction is not visible during generation. The methodology authors had visibility into the binary identities and could review the documentation surfaces; the term "test-suite-hidden" is used in preference to "blind eval" to be explicit about the scope of hiddenness (only the test suite was hidden).

**Scoring rubric.** ProgramBench scores each submission by running a pytest-based test suite (per-task: yj 825 tests, csview 348, gron 233, htmlq 2058, figlet 1044) against the agent-generated binary inside a clean Docker container. The score is the fraction of tests passed; the percentages reported throughout §5B are pass-count / total. The test suite is not visible to the agent during generation; it is loaded into the eval container after the submission lands.

**Base-rate context.** ProgramBench's public leaderboard (programbench.com/leaderboard) reports raw-LLM baseline scores per task. Direct leaderboard-baseline-vs-methodology head-to-head tables are deferred entirely to future work (§7.2) because the leaderboard's baseline configurations vary in ways the case study has not fully harmonised against the internal ablation ladder. The case study's reported numbers are not directly compared to the leaderboard in §5B.

**On data volume — a constraint, not a methodology choice.** The empirical volume reported in §5B is small: n=4 on the target task (yj), n=1 per task on the cross-task replicates, n=3 per cell in §5B.1's Layer A comparison. This is a token-cost-economics constraint rather than a methodology design choice. Each iteration-substrate-augmented rep on yj costs tokens roughly in the range $0.50–$1.00 of model inference plus eval-harness compute (figures are author estimates from observed per-rep token totals at the model's published pricing; we do not exhibit the per-rep token logs in this paper). Downstream: replicating yj at n=10 per arm would cost on the order of $20–40 in inference (same hedge), and a controlled methodology-vs-engineering ablation across all five tasks at n=3 each would cost on the order of $40–80. The author's available cap is sufficient for one or two rounds of those experiments but not for them as a routine part of methodology development against a stream of substrate-layer changes. We report what we could afford to measure; the experiments we did not run are named explicitly. A reader inclined to read "n=4 single-task" as the methodology's evidentiary bar should read it instead as "the volume at which we exercised the methodology under the budget we had"; a higher-budget version of this work would replicate at higher n. The case-study altitude is the consequence of that constraint, and we frame the artefact accordingly.

This setting stresses two properties of the methodology specifically. First, the briefing prose (the upstream README) is sometimes incomplete relative to the test surface — features the binary implements appear in the test suite without being named in the docs. Second, single-shot generation routinely produces code that fails a binary precondition (the program does not compile) — and the unverified output ships to evaluation, where it scores zero. Both failure modes are direct consequences of methodology-application gaps: an extractor reading only one channel under-fits the source, and a harness that ships outputs without a production-path probe lets unverified results reach the user.

**Layer-stack and configurations used in the case study.** Five distinct configurations are reported across §5B.1 and §5B.2. Readers comparing numbers across the two subsections need to know which configuration each table cell draws from. The case study traces the substrate's development over multiple stages; not all cells use the same configuration.

| Configuration | Substrate layers | Reps reported | Where reported |
|---|---|---|---|
| **README-only baseline** | None (no multi-channel extraction; no substrate) | n=3 per task except htmlq at n=1 | §5B.1 first column |
| **Layer A only (multi-channel extraction)** | None (multi-channel extraction but no iteration substrate) | n=3 per task | §5B.1 second column |
| **Layer A + compile-loop** | compile-loop only (1 substrate layer) | n=1 per task | §5B.2 cross-task pre-substrate column (csview/gron/htmlq/figlet) — sourced from the step-4 baseline batch |
| **Layer A + extract-empty + compile-loop** | extract-empty-loop and compile-loop (2 substrate layers) | n=4 (5 attempted, 1 DNF) | §5B.2 yj pre-substrate column — sourced from the topup batch run after extract-empty-loop landed but before README-self-test and behavioral-equivalence |
| **4-layer substrate** | extract-empty-loop, compile-loop, README-self-test, behavioral-equivalence (all 4 substrate layers) | n=4 for yj (5 attempted, 1 DNF); n=1 for each cross-task | §5B.2 post-substrate column |

The configurations differ specifically in **which iteration-substrate layers are present**. Multi-channel extraction (Layer A) is the extraction step that supplies objectives to the substrate; it is present in all configurations except the README-only baseline. The substrate layers (extract-empty, compile, README-self-test, behavioral-equivalence) were built sequentially during the experiment and not all reps used the full stack; the table above maps each reported cell to the substrate layers active during its run.

Two specific consequences for reading the data:

- **§5B.1 yj cell "0.0% (n=3; all compile-failed)" is Layer-A-only.** No compile-loop. Compile failures ship to evaluation and score 0%. The §5B.2 yj n=4 pre-substrate cell uses Layer A + extract-empty + compile-loop, so compile failures get retried until they compile (or exhaust retries); most of those binaries then compile cleanly but produce null-or-poor runtime output. The two yj cells measure different stages of the same task under different substrate configurations.

- **§5B.2 cross-task pre-substrate cells (csview/gron/htmlq/figlet at n=1) use Layer A + compile-loop**, not the same configuration as §5B.2 yj's pre-substrate (which adds extract-empty). The §5B.2 deltas (post-substrate − pre-substrate per row) therefore measure different layer additions per row: for yj the delta is +README-self-test+behavioral-equivalence (2 layers added); for cross-task rows the delta is +extract-empty+README-self-test+behavioral-equivalence (3 layers added). This asymmetry is a feature of the substrate's incremental development rather than a controlled per-layer ablation; we identify a controlled per-layer ablation (run all five tasks at every intermediate configuration) as future work (§7.2).

#### 5B.1 Layer A — Multi-channel extraction

The first refinement reads the compiled binary as an extraction channel alongside the README: invoking `--help`, reading `--version`, and (when needed) scanning the binary's embedded strings for documentation the README omitted. A separate rule unblocks extraction when the briefing prose is below a content threshold but the binary's self-describing surfaces are not.

Per-task results, n=3 reps per cell unless noted:

| Task   | README-only extraction | Multi-channel extraction | Delta |
|--------|------------------------|--------------------------|-------|
| csview | 0.0% (n=3) | 27.2% (n=3, sd 25.3pp; *see footnote 1*) | +27.2pp (directional only) |
| gron   | 25.2% (n=3, sd 23.1pp) | 38.5% (n=3, sd 2.2pp) | +13.3pp; variance reduced ~10× |
| htmlq  | 73.7% (n=1) | 75.4% (n=3, sd 1.5pp) | +1.7pp; *see footnote 2* |
| yj     | 0.0% (n=3; all compile-failed) | 0.0% (n=3; all compile-failed) | unchanged (0.0% in both columns); extraction quality is unobservable at this configuration because all reps fail upstream of the test suite (no compile-loop in either column means non-compiling submissions score zero regardless of extraction quality). See §5B.2 for yj results under configurations that include compile-loop. |
| figlet | 43.6% (n=3, sd 0.4pp) | 39.1% (n=3, sd 7.7pp) | -4.4pp; *see footnote 3* |

*Footnote 1 (csview multi-channel).* The csview multi-channel cell's sd 25.3pp is comparable to its mean (27.2pp); the one-sigma band is [1.9, 52.5]. We report this cell as directional evidence the mechanism helps when the README under-specifies, not as a population-mean estimate. Higher-n replication is identified as future work (§7.2).

*Footnote 2 (htmlq).* README-only htmlq is n=1 (single rep from baseline batch); the +1.7pp delta against an n=3 multi-channel cell with sd 1.5pp is not distinguishable from sample noise at this scale. We report the observation without interpreting it as a saturation result. (Note: "README-only" here refers to the §5B.1 first-column configuration; "pre-substrate" elsewhere in §5B.2 refers to a different configuration — Layer A + compile-loop on cross-task, or Layer A + extract-empty + compile-loop on yj.)

*Footnote 3 (figlet).* Mean drop within plausible n=3 sample variance for the task; the variance widening initially flagged was traced to a downstream behavioural-equivalence-probe environment-variable issue (FIGLET_FONTDIR not set), resolved by env-aware probe support in the substrate after the §5B.1 Layer A runs completed. The §5B.1 figlet Layer A configuration was not re-run after the env-var fix because subsequent runs were substrate-applied; the §5B.2 figlet values are different configurations (Layer A + compile-loop pre-substrate at n=1; 4-layer post-substrate at n=1) and are not a re-measurement of the §5B.1 cell.

**Findings.** First, the largest gains arrive on tasks where the README under-specifies the test surface. csview's briefing prose was nine lines and gave no surface to extract; the binary's `--help` text returned eighty lines of flag definitions and value enumerations that the multi-channel extractor read directly. Under the README-only configuration, the agent produced no scoring output on the three reps (0.0% across n=3); the case study's available logs do not capture per-rep agent behavior in enough detail to distinguish empty submission (the §3.1 multi-component refusal-to-fabricate mechanism firing) from failed-fabrication submission (the agent emitted code that scored zero against all 348 csview tests). The §7.2 single-call-trace logging item names this as a future-work gap. Either way, supplying a real source via multi-channel extraction produced a measurable lift.

Second, on tasks where the README already covers the test surface, multi-channel extraction is a no-op (htmlq, +1.7pp at boundary-noise scale). The mechanism contributes only where it has something to contribute; it does not hurt where it has nothing.

Third, figlet's variance-widening flag was traced to an implementation-level downstream probe issue (environment variable not set), not an extraction-mechanism artefact. The lift mechanism on tasks with documented sparse-prose surfaces (csview, gron) is consistent with the methodology's framing; the figlet observation does not contradict it once the downstream probe was repaired.

A naive-baseline honest-refusal-vs-speculative-fabrication comparison on csview is described as a future experiment in §7.2 rather than as a finding here, because we do not have a comparable naive baseline run on csview with the same multi-channel input surface as the methodology Layer A run; the controlled ablation (naive baseline with multi-channel inputs) is the experiment that would isolate the calibration discipline's contribution from the input-surface contribution.

#### 5B.2 Layer B — Iteration substrate for outcome-altitude verification

The second refinement addresses the post-extraction half. Single-shot generation of compilable code is not deterministic; on the corpus's Go tasks, the model frequently emitted code that failed the strict unused-imports check. The unverified output reached evaluation; the test suite scored zero against a non-compiling binary. More fundamentally, even on tasks where the binary compiles, the agent's output can perform at near-floor levels on the test corpus — the binary runs without crashing but produces little useful output, scoring only on trivial probes (e.g., `--version`-style tests) while substantive behaviour is broken.

This is the methodology gap §4 names. The contract included an outcome-altitude criterion — the submitted program must produce the documented behaviour — that the harness was not actually verifying before shipping.

The fix is harness engineering parameterised by methodology-derived verifiers. When an acceptance criterion names a property the system can mechanically check, the harness checks it before shipping. When the check fails, the harness invokes the generator again with the failure output appended to the brief; when it succeeds, the result ships; when it does not converge within a bounded retry budget, the harness halts and reports.

**Substrate composition and attribution.** The production substrate stacks four verifier layers in sequence, each parameterised by a methodology-derived specification of what the layer checks. The mapping from substrate layers to the §4 sub-clauses they operationalise:

| Layer | What it checks | Methodology dependency | §4 sub-clauses operationalised |
|-------|----------------|------------------------|--------------------------------|
| 1. extract-empty-loop | The extraction stage produced at least one objective | Methodology-derived. The extraction stage exists only because §3.1 factors the pipeline as multi-source objective extraction; a non-methodology harness does not have a discrete extraction stage that could produce zero objectives. | §4.1 clause 3 (real outcome artefact required) applied to the extractor stage's output |
| 2. compile-loop | The submitted source compiles | Generic engineering. Any retry-on-build-failure pipeline works here independent of methodology. | Trivially satisfies §4.1 clause 1 (the compiled binary is the production entry-point); §4 does not motivate this layer's existence — the layer exists because non-compiling submissions score zero, not because the methodology specifies it. |
| 3. README-self-test | Documented examples from the README execute correctly when fed to the generated binary | Methodology-derived. The README is a §3.1 extraction channel; treating its examples as outcome-altitude probes is §4 operationalised. | §4.1 clauses 1+3 (entry-point invocation + real artefact) |
| 4. behavioral-equivalence | Curated probes against the binary's documented capabilities produce expected outputs | Methodology-derived. The probe set is a §4 outcome-altitude verifier; the curation procedure is described below. | §4.1 clauses 1+2+3 (entry-point + no pre-arrangement + real artefact) |

Underneath the substrate sits Layer A (§5B.1), the multi-channel extraction that supplies the objectives the verifiers reference; Layer A is itself methodology-derived (§3.1).

Of the four verifier layers, three (1, 3, 4) and the entire extraction stage (Layer A) exist only because the methodology specifies what to verify and at what altitude. The retry mechanism that composes them is generic engineering. The methodology's contribution to the substrate is the verifier-set design — what verifiers should exist, against what curated inputs, at what altitude. The engineering contribution is the bounded-retry loop that calls them cheaply.

**Probe-set construction (Layer 4) — on possible test-suite leakage.** For each task, the behavioral-equivalence probe set was curated against the binary's documented capabilities (README + `--help` text). The probe-curating agent did not have access to the ProgramBench test suite for any of the five tasks during curation — the test suite lives in the eval container and is loaded only after submission; no per-test inspection of the suite was performed at any point. Two leakage paths nonetheless deserve disclosure honestly: (i) the substrate's development cycle observed aggregate per-rep pass-rate scores from earlier reps, which are weak feedback from the test suite (an aggregate signal of "how much did this submission match the suite"). Substrate design decisions — including the choice to add the behavioral-equivalence layer at all — were informed by observations of the bimodal failure pattern in earlier reps. So while specific probes were not curated from test-suite content, the architecture of the substrate (which layers exist) was responsive to aggregate test-suite feedback. (ii) The binary identities were known to the agent during probe curation; for well-known utilities (yj, gron, csview, htmlq, figlet) the agent's prior training data plausibly contains information about typical use cases for those tools, which could implicitly inform probe choices. We name both paths explicitly because the Layer 4 attribution depends on them. The within-case-study attribution remains coherent: methodology-derived layers caused the lift on the failure mode engineering retry alone could not catch; the probes themselves are curated against documented capabilities, not against the test suite. An external evaluation in which the binary identities are also hidden from the methodology authors would strengthen the claim further; we identify that as future work (§7.2).

**Probe-curation procedure.** The procedure (already characterised above as documented-capabilities-only) consisted of three steps:

1. Enumerate the binary's documented capabilities from the README and `--help` output. Treat each `--help` flag as a capability; treat each example block in the README as a candidate probe input.
2. For each capability, derive at least one input that exercises it and at least one expected-output property the binary's documentation describes. Where the capability has multiple modes or branches, derive at least one probe per mode.
3. Where the binary's behaviour depends on environment (path-discovery, font directories, configuration files), the probe records the necessary environment along with the input.

Per-task probe counts in this study: yj 8 probes, gron 6, htmlq 5, csview 5, figlet 5. The procedure relies on author judgment in steps 1–2: "enumerate documented capabilities" and "derive at least one input that exercises it" admit per-author variation. Another team applying the methodology against the same binaries would produce similar but not identical probes. We acknowledge this as a methodology-level reproducibility limitation in §7.1; making the probe-curation procedure fully agent-extractable is identified as substrate development work in §7.2.

**Replication on yj.** Five reps were run with the 4-layer substrate on yj. Four reps completed end-to-end; one rep (rep2) produced a submission that compiled and passed all four substrate layers but caused the eval's 825-test harness to hang and not produce a recorded score; we report this as DNF and discuss it as a substrate-design counterexample in §5B.3.

Pre-substrate (configuration: Layer A + extract-empty + compile-loop — 2 of the 4 final substrate layers; sourced from the topup batch; 5 reps attempted, n=4 reps where the ProgramBench eval scored end-to-end, 1 rep DNF — eval did not produce a recorded score before substrate-layer development continued). **Note on rep numbering:** rep-ids are scoped per-batch and do NOT carry meaning across batches. The pre-substrate batch's rep1 was the DNF (no recorded score; the pre-substrate eval was not retried before substrate-layer development continued). The post-substrate batch is a separately-numbered set of attempts; the rep2 named as DNF in the post-substrate table below is a different rep from the pre-substrate rep2 listed here.

| Rep | Pass rate |
|-----|-----------|
| rep2 | 39.52% |
| rep3 |  8.24% |
| rep4 | 39.15% |
| rep5 |  5.33% |

Observed mean 23.06% at n=4; observed sample sd 18.83pp (computed from the four listed pass rates above). The pre-substrate distribution shows two reps near 40% (rep2 39.52%, rep4 39.15%) and two reps below 10% (rep3 8.24%, rep5 5.33%). We do not assert this is a statistically-supported bimodality claim — n=4 does not support a formal bimodality test (e.g., bootstrap or bimodality coefficient), and the appearance of two clusters in four samples can arise from sampling variance in some unimodal distributions. The honest observation is: two pre-substrate reps produced sub-10% pass rates. Because the substrate configuration here includes compile-loop, those sub-10% reps' binaries compiled cleanly (compile-loop retried until they did) but produced effectively null runtime output across the test suite — a failure mode the compile-loop layer cannot detect.

Post-substrate (4-layer, n=4 reps that completed):

| Rep | Pass rate |
|-----|-----------|
| rep1 | 50.91% |
| rep3 | 45.82% |
| rep4 | 47.15% |
| rep5 | 44.48% |

Observed mean 47.09% at n=4; observed sd 2.77pp. Under the substrate, no rep produced a pass rate below 40%.

**The within-case-study attribution argument.** Yj's full 0% → 47% lift over Layer A is the joint result of four substrate-layer additions; three of the four are methodology-derived (extract-empty-loop, README-self-test, behavioral-equivalence) and one is engineering retry (compile-loop). We decompose the lift into two increments:

- **First increment: 0% (Layer A only) → 23.06% (pre-substrate).** Two layers added: extract-empty (methodology-derived) + compile-loop (engineering retry). The Layer-A-only configuration produces submissions that fail ProgramBench's compile gate and score zero; without compile-loop, no methodology layer's contribution is measurable because submissions don't survive to the test suite. Compile-loop is therefore *necessary infrastructure* for any non-zero score on yj — not a competing methodology contribution to the lift, but a precondition for measuring methodology contributions. Extract-empty (which exists as a discrete pipeline stage only because the methodology factors extraction as a separate step per §3.1) also contributes here, but we cannot cleanly separate its contribution from compile-loop's in this case-study data. The honest reading of the first increment: 0% → 23% is *what compile-loop and extract-empty jointly achieve*, and at minimum compile-loop is doing substantial necessary work in this range.

- **Second increment: 23.06% (pre-substrate) → 47.09% (post-substrate).** Two layers added: README-self-test (methodology-derived) + behavioral-equivalence (methodology-derived). Zero engineering-retry layers added at this step. The two pre-substrate reps with near-floor pass rates (rep3 8.24%, rep5 5.33%) produced binaries that compiled cleanly — compile-loop did its job, retrying failures until the source compiled — but the binaries produced little useful runtime output across the test corpus, which compile-loop cannot detect by construction. README-self-test and behavioral-equivalence test runtime output against documented capabilities. The post-substrate run produced no reps below 44%. The second increment is therefore attributable to methodology-derived layers operating on a stack where engineering retry was already running; engineering retry's contribution at this increment is zero because no engineering-retry layer was added.

**What the case-study claim commits to.** The methodology's load-bearing within-case-study claim is that the **second increment (23% → 47%) coincides with methodology-derived layer additions** that target a failure mode engineering retry alone cannot catch (compile-loop cannot detect a binary that compiles but produces poor runtime output; README-self-test and behavioral-equivalence test runtime output against documented capabilities). The first increment (0% → 23%) involves engineering retry as necessary infrastructure and is not a claim about methodology alone. A reviewer doing the same arithmetic concludes the methodology contribution in this case study is roughly 24 percentage points on a 47-point empirical surface, scoped to the failure mode where the methodology has structural advantage. We say "coincides with" rather than "is attributable to" because the pre/post comparison cannot rule out the batch-time confounds named earlier; "coincides with" is the verb the data supports at case-study altitude. We do not claim the methodology produced all 47 points or that engineering retry's contribution to the first increment is unimportant.

This is the case study's central attribution observation: **within the case study, the layers responsible for the lift are the methodology-derived ones, not the engineering retry mechanism.** This is a within-case-study layer-block comparison: the pre-substrate and post-substrate batches differ in two layers, with the methodology-derived layers (README-self-test, behavioral-equivalence) being those two. Confounds the comparison cannot rule out include batch-time non-layer differences between the two batches: the pre-substrate (topup) batch was run earlier in the substrate development arc than the post-substrate batch, so any drift in model version, prompt-template revisions, retry-budget tuning, or surrounding-harness changes during the interval between the two batches confounds the strict pre/post comparison. A contemporaneous controlled ablation (running both configurations side-by-side under matched harness conditions at comparable n) would harden the attribution further; we identify that as future work (§7.2). What the case-study data can support — and we report this as the observed finding — is that adding the methodology-derived layers to a stack already running engineering retry coincided with the lift on the failure mode engineering retry alone could not catch, with the layer-block difference being the largest deliberate change between the two batches.

Two further attribution refinements remain for future work: (i) an isolated per-layer ablation distinguishing Layer 4 (behavioral-equivalence) from Layer 3 (README-self-test) on the yj sub-10% reps; (ii) a per-rep trace showing which substrate layer fired on the rep3/rep5 pre-substrate failures specifically. The current data supports the layer-block attribution (methodology layers caused the lift); finer-grained per-layer attribution requires the ablation.

A formal variance-reduction claim — that the population sd is 18.83pp pre-substrate and is 2.77pp post-substrate — is not supported by n=4 each. Population-level claims about variance reduction or mean lift require higher-n replication and formal statistical tests (bootstrap CI on the sd reduction); we identify these as future work (§7.2). A higher-n replication on yj is the load-bearing follow-up for the case study.

**Cross-task regression check (n=1 per task).** The 4-layer substrate was also run at n=1 on the other four tasks. The pre-substrate column in the table below is the **Layer A + compile-loop** configuration (sourced from the step-4 batch — extract-empty-loop, README-self-test, and behavioral-equivalence were not yet built at that time); the post-substrate column is the full 4-layer substrate. Per the layer-stack table at the start of §5B, the cross-task pre-substrate cells use one substrate layer (compile-loop), while the yj n=4 pre-substrate cells use two substrate layers (extract-empty + compile-loop). None of these cells are directly comparable to the §5B.1 Layer-A-only cells for the same tasks — different configurations, different rep counts. The §5B.2 deltas therefore measure different layer additions per task (for yj: +README-self-test+behavioral-equivalence; for cross-task: +extract-empty+README-self-test+behavioral-equivalence).

| Task   | Pre-substrate (Layer A + compile-loop, n=1) | Post-substrate (4-layer, n=1) | Delta |
|--------|-------------------------------|--------------------------------|-------|
| csview | 37.64% | 47.41% | +9.77pp |
| gron   | 49.36% | 35.19% | −14.17pp |
| htmlq  | 79.64% | 74.54% | −5.10pp |
| figlet | 43.31% (n=1) | 44.06% (n=1) | +0.75pp |

The n=1 cross-task results establish *regression-check altitude* evidence, not population-mean altitude. csview's +9.77pp move is in the direction the methodology predicts when the substrate provides verifier coverage Layer A alone does not — but at n=1 against §5B.1's wide csview variance band (Layer A sd 25.3pp on 27.2% mean), and across different configurations (the §5B.2 pre-substrate cell is Layer A + compile-loop, not Layer A only), the +9.77pp move cannot be distinguished from a high-side draw on the underlying high-variance distribution. **The gron −14.17pp drop is the largest cross-task delta; at n=1 it cannot be attributed to substrate-induced regression vs sample noise.** Comparison-point context: §5B.1's gron Layer A n=3 was 38.5% (one-sigma band [36.3, 40.7]); the §5B.2 pre-substrate (Layer A + compile-loop, n=1) value of 49.36% is well outside the Layer A n=3 range. Neither sample supports formal sigma claims (n=3 sample sd is too small a base to compare an n=1 cell against). The two cells are different configurations (Layer A only vs Layer A + compile-loop), so even the range comparison is imperfect evidence; the qualitative observation is that the Layer A + compile-loop n=1 gron value was a high single draw, and the post-substrate value 35.19% is back inside the Layer A range. htmlq's −5.10pp is within historical single-rep variance for the task. figlet's +0.75pp is within noise.

We report these results without claiming "no catastrophic regression observed"; the data at n=1 cannot rule one in or out. The gron delta in particular warrants n≥3 replication before any directional claim.

**Architectural finding from the rep2 DNF.** The 4-layer substrate's probe set covers wrong-output failure modes (the binary produces incorrect output for a given input) but does not cover hang-causing failure modes (the binary enters an infinite loop on a specific input the probe set does not generate). yj rep2's submission passed all four substrate layers — compile, README-self-test, all 8 behavioral-equivalence probes — but the 825-test ProgramBench eval hung at some test input the probe set did not cover, and the eval did not produce a recorded score within a reasonable wall-clock budget.

This is a counterexample to the substrate's verification claim at the methodology's stated bar. §4 requires criteria to be verified before shipping; the substrate verified its four layers; the submission shipped; the production-altitude criterion (the eval test suite passes) was vacuously satisfied because the substrate did not check for termination on adversarial inputs. The methodology's reaction is re-extension (§2.2) applied to the discovered case: the failure mode "binary hangs on adversarial input" is a previously-unnamed case that should be promoted to a named criterion with backing — specifically, a hang-input probe layer with per-probe timeout enforcement. Whether re-extension applied prospectively during authoring would have surfaced the hang-input case before shipping is not demonstrated in this case study; the discovery was post-shipping. We report the case as an honest observation about the substrate's coverage gap and identify the corresponding substrate improvement in §7.2.

**On the within-case-study vs external attribution comparison.** The within-case-study attribution (above) is direct: the §5B.2 yj pre-substrate cell uses Layer A + extract-empty + compile-loop, and the post-substrate adds the two methodology-derived layers (README-self-test, behavioral-equivalence). The lift came from those two layers being added to an engineering-retry stack that was already running. An external ablation (a non-methodology pipeline running compile-loop alone, on the same task set at comparable n) would strengthen the attribution further by ruling out alternative explanations of how an engineering-only pipeline might be configured. We identify the external ablation as future work (§7.2); it is the next experiment we would run if token budget permitted. The case-study reports the within-case-study attribution as the empirical observation we can defend now.

#### 5B.3 What the case teaches

Three observations relevant to ODD's methodology claims.

First, the extractor and the verifier are independent contributions addressing distinct failure modes. Multi-channel extraction lifts performance where the briefing prose is incomplete; the iteration substrate lifts performance where the criterion was unverified. Tasks where neither failure mode is present (htmlq) do not benefit substantially, and the methodology does not claim they should.

Second, on yj — the only task with statistical power above n=1 — the substrate's effect is observable: pre-substrate produced two reps with sub-10% pass rates; post-substrate produced no reps below 40% (n=4 each). The mechanism is that the behavioral-equivalence layer (Layer 4) catches the compile-clean-but-behaviourally-null failure mode that the lower-tail pre-substrate reps exhibited. The variance and mean observations at n=4 are descriptive; population-mean estimates require higher-n replication.

Third, the iteration substrate's value depends on the verifier being cheap. Compile checks are deterministic and complete in seconds; schema validators, format checkers, and existence probes are comparable. Substrates with expensive verifiers (live integration tests against external systems; human-in-the-loop checks) would not exhibit the same cost-amortisation profile and are out of scope for this paper.

---

## 6. Composition with LLM Toolchains

*This section is descriptive composition mapping. It shows how the methodology composes with toolchain primitives at architectural altitude; operational specifics (persisted-violation record schemas, retrieval-match procedures, budget bounds, hook-state semantics) are deferred to the implementation distribution and §6 should not be read as containing extractable invariants. Implementing teams applying the methodology in a different toolchain will need to fill in the operational specifics from the implementation distribution rather than from this section's prose.*

The methodology composes with primitives modern LLM-attached toolchains provide. We name two composition patterns abstractly, each followed by one concrete instance to make the pattern legible. The patterns are general; the toolchain-specific names are exemplars, not requirements.

### 6.1 Pattern A — Persisting methodology corpus across sessions

**Pattern statement.** When a toolchain exposes lifecycle events (session start, session end, message arrival), the methodology's materials — altitudes, mapping rule, drift modes, outcome-altitude requirement — can be loaded as additional context at session-start via a hook that runs once per session, with any methodology-violation observations persisted at session-end and re-loaded by relevance match on subsequent sessions. The agent does not re-derive the methodology each session; the in-context budget is paid only for content that scored above a relevance threshold.

**One concrete instance (illustrative).** A toolchain exposing `SessionStart`, `Stop`, and `UserPromptSubmit` hook events permits a `SessionStart` hook to load the methodology corpus; a `Stop` hook to persist observed violations and fixes; a `UserPromptSubmit` hook to retrieve relevance-matched prior entries.

### 6.2 Pattern B — Iteration substrates for outcome-altitude verifiers

**Pattern statement.** When an acceptance criterion names a property the toolchain can check mechanically — compile success, schema validation, format conformance, exit-code-zero, documented-example execution — the verifier is cheaper to run than the generator. The harness composes the two: it runs the generator, then runs the verifier; on verifier failure, it re-runs the generator with the verifier's diagnostic prepended to the brief; it caps retries to bound cost. The substrate is justified by §4: it is the engineering shape that operationalises the outcome-altitude requirement when the verifier is cheap enough that the cost of running it is dominated by the cost of shipping an unverified result.

**One concrete instance (illustrative).** §5B Layer B's 4-layer substrate stacks four cheap verifiers (extract-empty, compile, README-self-test, behavioral-equivalence) and runs them in sequence before shipping; each layer's failure feeds back into the next generator attempt. The substrate's specifics (probe-set construction, per-task curation) are methodology-parameterised — the engineering shape (retry-on-verifier-failure with bounded budget) is generic.

The substrate is not method-in-acceptance. The acceptance criterion states what must be true; the substrate is one engineering shape for establishing the fact. A different engineering shape — a single generator pass that does its own pre-flight verification internally, say — would be equally valid as long as the criterion is verified before the result ships. The contract names *that* the criterion is checked; the toolchain implements *how*.

In both patterns, ODD leans on a primitive the toolchain provides. The methodology is not a re-implementation; it is a discipline layered on the toolchain's existing surface. Toolchain-specific operational concerns (auth flow, sandboxing, configuration management) are out of scope for this section and are documented in the implementation distribution.

---

## 7. Limitations and Future Work

### 7.1 Limitations

**Negative-alignment detection is deferred.** The methodology catches code without a contract, and contracts at the wrong altitude. It does not catch the case where contract says X and code does not-X — where intent and implementation are inverted rather than misaligned. Detection requires richer objective semantics and calibration data for false-positive control.

**The outcome-altitude probe assumes a callable production entry-point.** A system whose user-facing surface is a UI without an automation surface, or a notification stream without a consumer, has no callable entry-point. The risk-band classifier treats such cases as production-facing, but verification needs project-specific harnesses (browser automation, message-queue consumers) the methodology does not supply.

**Confidence bands' VERIFIED test-pass sub-clause is impl-relaxed in the reference implementation.** The methodology requires that VERIFIED-band claims are made only when the test that pins the objective is passing at the resolved revision. The reference implementation assumes pass-state at the resolved revision rather than executing the tests at extraction time. A codebase whose tests are broken at extraction time will be over-confident on every test-backed objective under the reference implementation. An implementation executing tests at extraction time satisfies the methodology more strictly.

**Drift detection at synthesis is heuristic and unobserved in the reported runs.** The 80% pass / 20% fail threshold (§3.1) is a calibration choice, not a derived constant. False-halt and missed-drift rates are open questions. The mechanism is present in the extractor but did not fire in any §5A or §5B reported run; effectiveness is therefore not observed in this work.

**The §5A motivating example is single-application and non-validating.** The four sequential integration runs and the six extracted objectives are observations from one production codebase that the methodology was developed against. The case informs methodology design and surfaces the failure patterns §4 was authored to catch; it is not independent empirical validation. The §5B benchmark study is the independent validation effort.

**§5A's metrics are largely process metrics.** Self-check pass rate and backing-map coverage measure that the pipeline ran and produced outputs of the expected shape. They do not measure whether the extracted objectives correspond to maintainer-authored objectives. A maintainer-comparison study against the §5A codebase is future work.

**§5A's 131/131 implementation-altitude classification is mechanically determined under the applied rules.** Conservative rules ("any output naming a specific symbol, file path, or library was marked implementation regardless of surrounding prose") applied to a structural extractor whose outputs by design contain (file, symbol, kind) tuples produce 100% by construction. The 131/131 figure is descriptive of the prior extractor's output shape (structural-extraction tuples), not informative as a measurement of the prior extractor's quality against a populated outcome-altitude reference. The methodology gap the §3 pipeline closes is real; the 100% rate is not the evidence that establishes it.

**§5B Layer A's csview result has wide variance.** The mean 27.2% at n=3 is paired with sd 25.3pp; the one-sigma band is [1.9, 52.5]. The result is directional evidence the mechanism helps when the README under-specifies; it is not a tight population-mean estimate.

**§5B Layer A's csview honest-refusal comparison is uncontrolled and deferred to future experiment.** The naive baseline received single-channel input (README only); the methodology Layer A received multi-channel input. The lift over the naive baseline cannot be attributed cleanly to calibration discipline vs additional input surface. The controlled ablation (naive baseline with multi-channel inputs) was not run; see §7.2.

**§5B Layer B's cross-task results are n=1 regression-check altitude.** The yj target task is replicated at n=4 (5 attempted, one DNF); the other four tasks are n=1 cross-task regression checks. They cannot rule catastrophic regression in or out at this scale; the gron −14pp drop specifically warrants n≥3 replication before attribution to substrate vs noise.

**§5B yj rep2 DNF is a counterexample to the substrate's verification claim.** The submission passed all four substrate probes but caused the eval harness to hang on an input the probe set did not cover. The substrate's contract — verify outcome-altitude criteria before shipping — was vacuously satisfied. The methodology's reaction (re-extension to add a hang-input probe layer) is consistent with §2.2's affordance, but the case is a known gap in the substrate's current probe-set design.

**Probe-set construction admits per-author variation.** The behavioral-equivalence probes are curated by humans against documentation surfaces; another team applying the methodology would produce similar but not identical probes. The case study's specific probe counts (yj 8, gron 6, htmlq 5, csview 5, figlet 5) are reproducible at the procedural level but not at the bit-identical level. Making probe-curation fully agent-extractable is named as substrate development work in §7.2.

**Refusal-to-fabricate firing is not directly observed in the case study.** The §3.1 mechanism that produces empty rather than speculative output on sparse-input tasks is a multi-component structural property; the case study's available logs do not capture per-rep agent behavior in enough detail to confirm the mechanism fired in the csview reps where it most plausibly would have. Single-call-trace logging is named in §7.2 as the future-work artefact that would enable direct observation.

**§4.3 risk-band classifier is builder-discipline, not agent-extractable.** The category list and OR-disjunction are presented for human or human-in-the-loop application; agents implementing the methodology should treat the classifier as guidance rather than as a structural rule. Formalisation as a structural check is named as future work in §7.2.

**§6 toolchain composition is descriptive, not measurement.** The two patterns map methodology requirements to toolchain primitives at architectural altitude; operational specifics (record schemas, retrieval procedures, budget bounds) are deferred to the implementation distribution. We do not claim each composition pattern lifts a measured metric.

**The iteration substrate is validated on a few verifiers.** The 4-layer substrate uses extract-empty, compile, README-self-test, and behavioral-equivalence. Other substrate family members — LLM-judge calls, retrieval-relevance checks, behavioural fuzzing — extend the family at different cost points and have not been validated by experiment. Extrapolation to those members is plausible but speculative.

**Statistical claims at n=4 are observation-level, not population-level.** The §5B Layer B replication on yj is n=4 (one DNF). Observations stated as "pre-substrate produced two reps below 10%; post-substrate produced no reps below 40%" are descriptive of the four-rep batches. Population-level claims about variance reduction or mean lift require higher-n replication and formal statistical tests (Hartigan dip; bootstrap CI on the sd reduction). We identify these as future work.

**The methodology is validated on engineered software cases.** The non-developer case — where the user lacks the vocabulary to state objectives at any altitude — is named in §1 as a motivating audience. The methodology's translation to that case is theoretical at the time of writing; empirical work is identified as future scope.

### 7.2 Future work

**Higher-n yj replication.** With n≥10, formal bimodality tests (Hartigan dip), bootstrap confidence intervals on the variance reduction, and population-mean estimates become possible. The current n=4 batches support descriptive observations only.

**n≥3 cross-task replication.** The cross-task results are n=1 regression-check evidence. Replication at n≥3 on each task — especially gron, where the −14pp delta at n=1 is the largest cross-task move — would convert the regression-check verdict into a population-mean estimate.

**Methodology-vs-engineering retry ablation.** A controlled comparison between (a) compile-loop-only retry (engineering-only baseline), (b) the 4-layer substrate (methodology-parameterised), and (c) the 4-layer substrate with the methodology-derived layers replaced by engineering-equivalent alternatives where possible would isolate the methodology's contribution to the §5B Layer B lift from the engineering scaffolding around it.

**Multi-channel naive baseline on csview.** Running a naive baseline (no calibration discipline) with multi-channel inputs (README + binary surfaces) on csview would isolate the methodology's calibration contribution from the input-surface contribution to the headline csview lift.

**Maintainer-comparison study on §5A.** An independent maintainer authors objectives against the same codebase; inter-rater comparison with the methodology's outputs converts §5A's qualitative case into a quantitative claim about extraction fidelity. Pairing this with an independent rater on a random sample of the 131 prior-extractor outputs would address the single-rater limitation in §3.

**ProgramBench leaderboard head-to-head.** Publishing the methodology stack's per-task numbers alongside the public leaderboard's raw-LLM baselines (with the leaderboard's baseline configurations harmonised against our internal ablation ladder) provides external base-rate context the case study does not yet incorporate.

**Probe-curation coverage criteria.** Specifying per-capability coverage criteria (one input per documented capability; per capability at least one input that crosses each documented behavioural boundary) and an output-schema for probe records would make probe-set construction agent-extractable rather than author-judgment-bound.

**Drift-halt observation.** The §3.1 mechanism is present but did not fire in any reported run. A targeted study with deliberately-drifting inputs would establish whether the mechanism functions as designed.

**Refusal-sequence call-trace logging.** Adding single-call-trace logging of the multi-component refusal sequence in §3.1 would make the refusal mechanism reproducible at the agent level rather than describable only as a structural emergent property.

**VERIFIED-band test execution at extraction time.** Moving the reference implementation from "assume test pass-state" to "execute tests" would satisfy the methodology requirement more strictly.

**Risk-band classifier formalisation.** Formalising §4.3 as a structural check (manifest field, dispatch-brief schema requirement) would replace builder-discipline-by-judgment with structural enforcement the harness runs.

**Iteration-substrate family beyond compile.** The 4-layer substrate covers extract-empty, compile, README-self-test, and behavioral-equivalence. Other family members — schema validators, retrieval-relevance LLM-judge calls, deliberate-hang probes — extend the pattern at different cost points. Each warrants independent validation against the failure mode it addresses.

**Hang-input probes for behavioral-equivalence layer.** The §5B yj rep2 finding identifies a probe-design gap: current probes test correctness on representative inputs but not termination on adversarial inputs. Adding per-probe timeout enforcement and deliberate-loop / deeply-nested-structure probes is the substrate improvement re-extension identifies.

**Build-next recommendation evaluation.** §3.4's ranker is exploratory. An operator-rated study or downstream-build correlation study would validate the ranking as a methodology contribution rather than a pipeline component.

**Outcome-altitude probes integrated with cold-start code generation.** The pipeline currently extracts from existing code. The inverse — using extracted objectives as a planning input for new code generation — is a natural next step.

**Negative-alignment detection.** Extending the methodology to catch code contradicting its own contract would close the third class of failure.

**Non-developer application.** The methodology's value depends on objectives being extractable from the input surface. When the user is not a developer and does not provide a developer-shaped briefing, the input surface shifts: screenshots, voice transcripts, error pastes, runtime probes. The multi-channel extraction architecture generalises in principle; empirical work in that direction is the natural continuation.

---

## 8. References

### Adjacent methodologies

- Beck, K. (2002). *Test-Driven Development: By Example.* Addison-Wesley.
- North, D. (2006). Introducing BDD. *Better Software Magazine*, March 2006.
- Wynne, M., & Hellesøy, A. (2012). *The Cucumber Book: Behaviour-Driven Development for Testers and Developers.* Pragmatic Bookshelf.
- Adzic, G. (2011). *Specification by Example: How Successful Teams Deliver the Right Software.* Manning.
- Meyer, B. (1997). *Object-Oriented Software Construction* (2nd ed.). Prentice Hall.
- Cohn, M. (2004). *User Stories Applied: For Agile Software Development.* Addison-Wesley.
- Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software.* Addison-Wesley.
- Jackson, M. (2000). *Problem Frames: Analyzing and Structuring Software Development Problems.* Addison-Wesley.
- Zave, P., & Jackson, M. (1997). Four dark corners of requirements engineering. *ACM Transactions on Software Engineering and Methodology*, 6(1), 1–30.

### LLM code-generation evaluation

- Chen, M., et al. (2021). Evaluating large language models trained on code. *arXiv:2107.03374* (HumanEval).
- Jimenez, C. E., et al. (2024). SWE-bench: Can language models resolve real-world GitHub issues? *ICLR 2024.*
- Yang, J., et al. (2024). SWE-agent: Agent-computer interfaces enable automated software engineering. *NeurIPS 2024.*
- Yang, J., Lieret, K., Ma, J., Thakkar, P., Pedchenko, D., Sootla, S., McMilin, E., Yin, P., Hou, R., Synnaeve, G., Yang, D., & Press, O. (2026). ProgramBench: Can Language Models Rebuild Programs From Scratch? *arXiv:2605.03546*. Benchmark site and leaderboard: programbench.com (accessed 2026-05-12).

### Authors' own materials

- *Objective-Driven Design — Operational Specification.* Mechanics: altitudes, mapping rule, re-extension, structural-vs-advisory enforcement.
- *ODD — LLM Context Prime (lean).* Compact reference loaded at the start of methodology-shaped tasks.
- *ODD — LLM Grounding Derivation.* Long-form derivation walking the adjacent methodologies cited above and the premises producing ODD's shape.

### Implementation and case-study artefacts

- The §5A reference implementation is a TypeScript application of approximately 19,000 lines. Specific repository details are omitted to honour operator confidentiality. An anonymised replication artefact (sanitised codebase summary, dummy data, extractor logs) is identified as future-work scope.
- The §5B benchmark corpus is drawn from ProgramBench (programbench.com), an external test-suite-hidden benchmark. The five tasks used in the case study — yj (Go), gron (Go), csview (Rust), htmlq (Rust), figlet (C) — are publicly available within the benchmark. The harness used to run the methodology against the benchmark is documented separately as part of the implementation distribution.
