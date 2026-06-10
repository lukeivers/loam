# loam glossary

**Status:** canonical reference for the 11 load-bearing terms used across
loam's forward-looking documentation, plans, and SKILLs. Definitions here
are sourced from the authority docs named on each entry's "Authority" line;
the glossary records and cross-links the canonical definition rather than
introducing new semantics.

**Audience:** anyone reading loam docs who hits a term they have not yet
seen — strangers cloning the repo, contributors authoring plans, AI
assistants composing dispatch briefs.

**Term coverage.** The 11 terms divide into three semantic clusters:

- **Loam-metaphor cluster** (substrate, seed, cultivar, growth) — the
  project's identity metaphor.
- **Sealed-component-cycle cluster** (amend, seal) — the operational
  vocabulary of how loam itself is built.
- **ODD cluster** (contract, objective, capability, banded AC,
  ratification) — the methodology vocabulary used across plans, docs,
  and SKILLs.

Terms NOT in this glossary that are nonetheless load-bearing canonical
loam vocabulary: **harness** and **primary persona**. Both have full-doc
canonical definitions (see "See also" lines on the relevant entries
below) and are not double-codified here. **Acceptance criterion (AC)**
is also not a glossary entry; it has an exhaustive definition in
`docs/odd-llm-grounding.lean.md` + `plugins/dev-sdlc/docs/odd-methodology.md`
§3 — the glossary entry "banded AC" cross-references it.

---

## substrate

The enriched medium a Claude-attached agent grows in. The project name
"loam" is itself the substrate metaphor: loam is what the user cultivates
their agent in, and the harness + primary persona + plugin ecosystem
collectively constitute that substrate. The metaphor positions loam as
domain-agnostic infrastructure — the substrate is the same regardless of
what the user grows in it (a developer workflow, a personal-life agent,
a domain-specific cultivar) — and prevents the project from drifting
into a single-vertical shape.

**Authority:** `docs/FUTURE_IDEAS.md` Idea 12 (loam-rename rationale);
`docs/spec/loam-objectives-spec.md` "pOS as a seed" addendum.

**See also:** seed, cultivar, growth (the metaphor cluster); harness
(the substrate's mechanical contribution per `docs/architecture.md`
"The one-line shape").

## seed

The user's natural-language statement of intent. The seed is the input
to the substrate: the user expresses what they want, and the cultivar
grows from that expression as the substrate (harness + primary persona
+ Claude itself) does the work of translating intent into AI-effective
execution. The seed framing is canonical at
`docs/spec/loam-objectives-spec.md` ("pOS as a seed" addendum) and is
preserved in the loam rename — `loam` names the substrate; the
seed / cultivar / growth metaphor in existing narrative is unchanged.

**Authority:** `docs/spec/loam-objectives-spec.md` ("pOS as a seed"
addendum); `docs/FUTURE_IDEAS.md` Idea 12.

**See also:** substrate, cultivar; primary persona (the translation
layer that turns the seed into executable shape per
`docs/VALUE_PROPOSITION.md`).

## cultivar

The grown agent — the specific shape Claude takes inside a particular
loam workspace, shaped by the user's seed plus the substrate's
contribution. "Cultivar" carries the right ambiguity: it is grown
(not built); it is specific to the user's workspace (not generic);
it can be cultivated further (amended, extended, retired). The
cultivar metaphor is what distinguishes loam from a general-purpose
AI tool: the user does not run a generic Claude session; they run
their cultivar.

**Authority:** `docs/FUTURE_IDEAS.md` Idea 12; `docs/spec/loam-objectives-spec.md`
("pOS as a seed" addendum).

**See also:** substrate, seed, growth; primary persona (the cultivar's
voice across sessions per `docs/architecture.md`).

## growth

How the cultivar compounds across sessions, time, and reboots — the
property the harness contributes that raw AI lacks. Growth is what
turns "Claude in a session" into "the cultivar I work with" — memory
accrues, decisions trace, the persona's grasp of the user's context
deepens. Growth is the substrate's job (the harness provides
persistence, observability, audit trail); the seed and cultivar are
the user's. Of the four loam-metaphor terms, "growth" is the most
descriptive (vs. operational): it names a property the substrate
aims at, not a mechanism with a contract.

**Authority:** `docs/FUTURE_IDEAS.md` Idea 12 (the "seed / cultivar /
growth metaphor" naming); `docs/VALUE_PROPOSITION.md` ("Persistence
across sessions" + "Autonomous continuity" toolkit entries).

**See also:** substrate, seed, cultivar; harness (the mechanical
contribution that makes growth possible).

---

## amend

The verb-shape of a sealed-component cycle. To **amend** a sealed
component is to take its current state, propose a tightly-scoped change,
walk the canonical commit ladder (plan-doc → manifest → BASELINE source
edit → `loam amend apply` → `loam amend seal` → §14 backfill), and
land the change as a new amendment with traceable provenance.

The CLI `loam amend apply --plan-doc <plan> <manifest>` lands the
manifest+sidecar bumps in one semantic commit. `loam amend seal`
lands the deterministic short-form seal commit and runs the sealed-
component sweep tests. The amendment cycle is loam's load-bearing
build discipline: nothing changes inside a sealed component without
running through it.

**Authority:** `plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md`
(canonical end-to-end walkthrough); `docs/dev-mode-getting-started.md`
§"Run amendment cycles via `loam amend`".

**See also:** seal (the closing event of an amendment cycle);
contract (what the amendment respects).

## seal

The closing event of an amendment cycle, AND the noun for the
sealed-component fence itself. As a **verb** (`loam amend seal`):
the deterministic short-form commit that lands an amendment, runs
the sealed-component sweep tests, and bumps the component's
SEAL_COMMIT sidecar. As a **noun** ("a sealed component"): a loam
component whose source code can only be modified through the
amendment cycle; direct edits without the cycle are refused.

The seal pattern enforces the sealed-component fence: changes to
sealed code carry traceable provenance back to a plan-doc + manifest +
named acceptance criteria. The pattern is what makes loam's
self-modification disciplined.

**Authority:** `plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md`;
`docs/dev-mode-getting-started.md` §"Run amendment cycles via
`loam amend`".

**See also:** amend (the cycle that culminates in a seal); contract
(the sealed component's contract is what the seal preserves).

---

## contract

A statement about what a system, component, or interface promises —
deterministic, observable, and binding. Contracts appear at multiple
altitudes in loam:

- **Primary-persona contract.** A description of how Claude Code
  behaves inside a loam workspace: greetings, dispatch shape,
  refusal shape, memory shape (`docs/architecture.md`
  §"The primary-persona contract"). Not a system prompt — a contract.
- **Component contract.** What a sealed component promises to its
  callers: API surface, invariants, fail-closed direction.
- **ODD acceptance contract.** The objective + constraints + ACs
  that bind a unit of work; method is the builder's call inside
  the contract (`plugins/dev-sdlc/docs/odd-methodology.md` §1.1).

Across all altitudes, the contract is what code is held against;
behaviour outside the contract is undefined; behaviour inside but
not satisfying the contract is a defect.

**Authority:** `docs/architecture.md` §"The primary-persona contract";
`plugins/dev-sdlc/docs/odd-methodology.md` §1.1 + §2.4–2.5.

**See also:** objective, capability, banded AC; primary persona.

## objective

A state of the world the work is required to make true — stated as
outcome, not as procedure. The first of ODD's three authoring slots
(the other two: constraints, acceptance criteria). An objective
survives implementation rewrite: rewrite the system in a different
language with different libraries, and the objective statement still
describes what the system delivers.

The four-altitude test (`docs/odd-llm-grounding.lean.md`) distinguishes
objectives from constraints (bounds on solution space, not outcomes),
capabilities (one of many possible HOWs), and implementations
(specific symbols/files/lines). Confusing altitudes is the most
common ODD drift mode (see odd-llm-grounding §"7 drift modes").

**Authority:** `docs/odd-llm-grounding.lean.md` §"Four altitudes" +
§"7 drift modes"; `plugins/dev-sdlc/docs/odd-methodology.md`
§1.1 + §2.

**See also:** capability, contract, banded AC; ratification.

## capability

A feature or function serving objectives — one of many possible HOWs
by which an objective can be delivered. Capabilities are below
objectives but above implementations in the four-altitude hierarchy:
"CSV upload + validation pipeline" is a capability serving the
objective "operators file refund disputes at scale"; the specific
Express route at `src/routes/exportRoutes.js:66` is the
implementation backing the capability.

The test for capability altitude: could a different system deliver
the same objectives without this exact thing? If yes, it is a
capability; the objective could be served other ways. If no, the
named thing is itself the objective.

**Authority:** `docs/odd-llm-grounding.lean.md` §"Four altitudes";
`plugins/dev-sdlc/docs/odd-methodology.md` §1.1.

**See also:** objective, contract; implementation (the layer below).

## banded AC

An acceptance criterion derived by the odd-extractor from a foreign
codebase, carrying a confidence band that signals how trustworthy
the derivation is. Three bands:

- **VERIFIED** — backed by a passing test in the foreign codebase
  (test name + file path + repo SHA).
- **PLAUSIBLE** — backed by source-code citations (file path +
  line numbers) but not pinned to a passing test.
- **HYPOTHESISED** — LLM-derived inference; evidence is a rationale
  string explaining the inference chain.

Banding is a trust gradient, not an importance gradient. A
HYPOTHESISED AC may name a load-bearing behaviour; the band only
states how confident the extractor is that the behaviour holds.
Bands are enforced structurally via the `BandedAC` Pydantic model
(`plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/bands.py`).

Hand-authored ACs in plan-docs for new loam work are NOT banded —
they are authored under ODD methodology §2.3 directly. Banding
applies to derived ACs only.

*Doctrine mapping (2026-06-10):* under the evidence grades in
`plugins/dev-sdlc/docs/odd-methodology.md` §6, VERIFIED means *ran
green at a known SHA*; the extractor grants its `VERIFIED` band on a
test-pass assumption without executing the foreign suite, so the
extractor's `VERIFIED` (and `PLAUSIBLE`) bands map to the **ASSERTED**
evidence grade until the enum rename lands.

**Authority:** `plugins/dev-sdlc/docs/odd-methodology.md` §6
(check-kinds + evidence grades); extractor mechanics at
`plugins/dev-sdlc/odd-extractor/docs/adapter-conventions.md`.

**See also:** objective, contract, ratification; acceptance criterion
(plain AC; defined in `docs/odd-llm-grounding.lean.md` +
`plugins/dev-sdlc/docs/odd-methodology.md` §3).

## ratification

The promotion / demotion / edit / reject workflow for banded ACs.
A banded AC's confidence can be **promoted** (HYPOTHESISED →
PLAUSIBLE → VERIFIED) when fresh evidence emerges, or **demoted**
when prior evidence proves wrong, **edited** to refine prose, or
**rejected** entirely. Each action writes one entry to the
extraction's audit log.

Ratification is mediated by the per-project PM's one-question-at-a-time
decision queue. The CLI verb is `loam odd-extract ratify
<contract-draft>`. Promotion has an asymmetric rule per Eric synthesis
Decision I: PLAUSIBLE → VERIFIED requires explicit user confirmation
(default-no on silent promotion); other promotions are default-allow;
demotions are always default-allow.

Silent acceptance of a wrong HYPOTHESISED AC, or silent promotion of
a PLAUSIBLE AC without confirming the test pin, is the violation
ODD methodology §4.4 prohibits. Ratification is the mechanism that
keeps the trust gradient honest.

**Authority:** `plugins/dev-sdlc/docs/odd-methodology.md` §11.3
(Promotion and demotion workflow).

**See also:** banded AC, contract, objective.

---

## Reading guide — when to consult this glossary

- A doc uses a term you have not seen before, or uses it differently
  than you expected → look it up here; the Authority line points to
  the canonical-definition doc.
- You are authoring a plan-doc or dispatch brief and want to use one
  of the canonical terms in its strict sense → consult the entry to
  confirm the operational meaning.
- A new doc proposes a definition that conflicts with an entry here →
  the conflict is the news; surface for owner ruling per F2 Ruthless
  Feedback (`~/.claude/CLAUDE.md` Universal principles).

This glossary is **canonical reference** for the 11 named terms.
Definitions in the authority docs win when they disagree with the
prose here (the glossary records; the authority doc owns).
