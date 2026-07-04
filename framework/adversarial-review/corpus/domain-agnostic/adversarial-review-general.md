# Adversarial review — how the discipline works (general methodology)

**Status: KEPT, reusable methodology. Researched 2026-07-03 (WebSearch + WebFetch, live).**
Every claim below is cited to a real source; where a point is this workspace's own
synthesis rather than established practice, it is marked **[SYNTHESIS]**.

This document answers: what do the fields that practice unrelenting critique
professionally — military red teams, intelligence analysis, software inspection,
experimental psychology — actually know about making critique find real flaws
instead of performing skepticism?

---

## 1. The core findings, compressed

1. **Assumed failure outperforms invited criticism.** Asking "what might go wrong?"
   produces politeness; asking "it HAS failed — write the postmortem" produces flaws.
   (Klein's premortem, §2.)
2. **Assigned contrarianism is weaker than genuine dissent.** A critic role-played
   into disagreement produces less divergent thinking than a critic who independently
   holds a different position. (Nemeth, §3.) This is the single most important
   structural fact for AI review: "act brutal" prompts buy tone, not findings.
3. **Checklists and structure beat vibes.** Formal inspection with defined roles,
   preparation, and defect checklists finds defects at rates informal review never
   matches. (Fagan, §4.)
4. **The mindset generalizes; the standing team does not.** The UK MOD's third-edition
   doctrine explicitly moved from "maintain a red team" to "apply a red-team mindset
   with named techniques at decision points." (§5.)
5. **Adversaries are most productive under an agreed protocol with an arbiter.**
   Adversarial collaboration works because both sides pre-commit to what evidence
   would settle the question. (Kahneman/Mellers, §6.)

---

## 2. The premortem — prospective hindsight

**Source:** Gary Klein, "Performing a Project Premortem," *Harvard Business Review*,
September 2007. https://hbr.org/2007/09/performing-a-project-premortem

The premortem inverts critique: the team is told the project **has already failed**,
and each member independently writes the reasons for its death. Klein grounds this in
the "prospective hindsight" research of Mitchell, Russo & Pennington (1989, *Journal
of Behavioral Decision Making* — cited here secondhand via Klein/HBR), which found
that imagining an event as having already occurred improves the ability to identify
reasons for future outcomes by ~30%.

Why it matters for review design:

- The frame change ("it failed; why?") licenses criticism that the normal frame
  ("any concerns?") socially suppresses — and, for an AI critic, escapes the
  agreement-prior that "evaluate this" invokes.
- Reasons are generated **independently first, then pooled** — no anchoring on the
  first speaker.
- It counters overconfidence at exactly the moment (post-plan, pre-ship) when a team
  is most bought-in.

**Transplant to artifact review [SYNTHESIS]:** frame the reviewer's objective as
"this artifact shipped and failed / was publicly torn apart — reconstruct why," not
"assess this artifact." The falsification stance is the objective, not a tone note.

---

## 3. Devil's advocacy — and why the assigned version underperforms

**Source:** Charlan Nemeth, Keith Brown & John Rogers, "Devil's advocate versus
authentic dissent: stimulating quantity and quality," *European Journal of Social
Psychology* 31(6), 2001. https://onlinelibrary.wiley.com/doi/abs/10.1002/ejsp.58

Nemeth's experiments compared groups exposed to an **assigned** devil's advocate with
groups exposed to **authentic** dissent (a participant who genuinely held the minority
view). Findings:

- Authentic dissent stimulated more, and more creative, divergent thinking.
- Assigned devil's advocacy tended to produce **cognitive bolstering of the original
  position** — participants generated more reasons they were right, having "heard the
  other side."
- No role-playing technique matched genuine disagreement.

Implication: a critique ritual that everyone knows is a ritual **inoculates** the
work against real criticism — worse than none, because it manufactures assurance.
This is the human-team version of exactly the failure the AI-side research finds in
rubber-stamp LLM review (see the companion doc).

**Transplant [SYNTHESIS]:** an AI critic must be structured to hold an *authentic*
independent position, not an assigned pose. The practical mechanism: have the critic
**derive its own expectation of what a correct artifact would look like** (from the
objective + domain methodology, before reading the artifact), then diff the artifact
against that derivation. Disagreements found this way are genuinely held — they come
from the critic's own construction, not from an instruction to disagree.

---

## 4. Formal inspection — structure, roles, checklists, measured yield

**Source:** Michael E. Fagan, "Design and Code Inspections to Reduce Errors in
Program Development," *IBM Systems Journal* 15(3), pp. 182–211, 1976.
https://dl.acm.org/doi/10.1147/sj.153.0182

Fagan formalized peer review into inspections with defined roles (moderator, author,
reader, tester), a preparation phase, defect **checklists per artifact type**, and
recorded defect statistics. Reported yield on the IBM system studied: inspection found
**38 defects/KLOC vs 8 defects/KLOC found by unit test**, and accounted for **82% of
all defects found** in the released product (figures as reported in the paper and the
SEI teaching materials, https://www.sei.cmu.edu/documents/1561/1993_011_001_16127.pdf).

Durable lessons:

- **Per-artifact-class defect checklists are the highest-yield tool.** The checklist
  encodes the domain's known failure taxonomy so each review doesn't rediscover it.
- **Separation of roles**: the author never moderates their own inspection.
- **Measure the inspection itself**: defects-found rates were tracked, so a
  low-yield inspection was itself a visible anomaly — inspection effectiveness was
  an object of measurement, not an article of faith.

The modern descendants — OWASP's secure code review guidance, Google's engineering
code-review practices (https://google.github.io/eng-practices/review/) — keep the
same skeleton: structured pass, named focus areas, author ≠ approver.

---

## 5. Red teaming — the mindset doctrine

**Sources:**
- UK Ministry of Defence (DCDC), *Red Teaming Handbook*, 3rd Edition, June 2021.
  https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1027158/20210625-Red_Teaming_Handbook.pdf
- US CIA, *A Tradecraft Primer: Structured Analytic Techniques for Improving
  Intelligence Analysis*, 2009.
  https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf

The MOD handbook's third edition is notable for an explicit doctrinal shift: away
from standing red **teams** toward a red-team **mindset** — a portable set of critical-
thinking techniques applied by whoever is at the decision point. Red teaming there is
defined as using structured techniques to challenge assumptions, expose biases, and
stress-test plans from an adversary's perspective.

The CIA Tradecraft Primer catalogs the named techniques, three of which are directly
reusable for artifact review:

- **Key Assumptions Check** — enumerate every assumption the product rests on; attack
  each ("what if this is false? how would we know?").
- **Devil's Advocacy** — build the best possible case *against* the consensus
  judgment (the primer positions this for challenging a strongly-held consensus, with
  the known limits from §3).
- **Team A / Team B** — two teams argue competing interpretations of the same
  evidence before a decision-maker; the value is in forcing both cases to be made
  fully, not in the theater.

AI-safety red teaming inherits this frame: Ganguli et al. (Anthropic), "Red Teaming
Language Models to Reduce Harms" (arXiv:2209.07858, 2022) treats red teaming as
*discover → measure → reduce*, and Perez et al., "Red Teaming Language Models with
Language Models" (arXiv:2202.03286, 2022) established that the attacker itself can be
automated — the direct ancestor of using an LLM as the adversary against produced
artifacts.

**Durable lesson:** red teaming is a *stance plus named techniques applied at
decision points*, not a department. For loam: a standing review **stage**, not a
standing review **team**.

---

## 6. Adversarial collaboration — protocol over rhetoric

**Sources:**
- Barbara Mellers, Ralph Hertwig & Daniel Kahneman, "Do Frequency Representations
  Eliminate Conjunction Effects? An Exercise in Adversarial Collaboration,"
  *Psychological Science* 12(4), 2001.
  https://journals.sagepub.com/doi/abs/10.1111/1467-9280.00350
- Daniel Kahneman, "Adversarial Collaboration," Edge lecture.
  https://www.edge.org/adversarial-collaboration-daniel-kahneman

Kahneman's protocol for resolving scientific disputes: the two adversaries jointly
design the test **before** running it, pre-committing to what evidence would move
them, with a neutral arbiter. The relevant transferable elements:

- **Pre-committed decision criteria.** What counts as a real flaw, and what evidence
  settles it, is fixed before the critique begins — so the argument is about the
  artifact, not about the standards.
- **An arbiter distinct from both sides.** The judge who weighs critic vs author is
  neither of them.
- Disagreement is treated as *productive input to a procedure*, not noise to smooth.

---

## 7. Synthesis — the seven properties of a real adversarial review [SYNTHESIS]

Everything above compresses to seven structural properties. A review process that has
them finds flaws; one that lacks them performs finding flaws.

1. **Failure is assumed, not invited** (premortem stance — §2).
2. **The critic's position is authentically derived, not assigned** (Nemeth — §3):
   independent derivation of "what correct looks like," then diff.
3. **Domain failure taxonomy in hand before the pass** (Fagan checklists — §4;
   this is what the domain-research-pull step exists to supply).
4. **Named techniques, applied at a defined decision point** (MOD/CIA — §5), with
   the verdict wired to a gate that can actually stop the artifact.
5. **Author ≠ reviewer ≠ arbiter** (Fagan roles, Kahneman arbiter — §§4, 6).
6. **Standards pre-committed** (adversarial collaboration — §6): severity taxonomy
   and evidence bar fixed before the review, so harshness can't be negotiated down
   artifact-by-artifact.
7. **The review process is itself measured** (Fagan defect statistics — §4): yield
   is tracked, and a zero-findings review of a nontrivial artifact is an anomaly to
   investigate, not a clean bill to celebrate.

Companion doc: `ai-as-critic-and-failure-modes.md` — what changes (and what breaks)
when the critic is an LLM.
