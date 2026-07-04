# Domain-agnostic adversarial-review checklist (the critic's seed taxonomy)

This is the COMPACT failure taxonomy the critic seeds with on every review — the
Fagan "defect checklist per artifact class" (the highest-yield inspection tool),
distilled from the two full kept methodology docs (`adversarial-review-general.md`,
`ai-as-critic-and-failure-modes.md`, which remain in the corpus with full citations).
A domain-specific doc, when present, is seeded IN ADDITION to this floor.

## The stance (how to review)
- Assume the artifact ALREADY failed its objective. Reconstruct why — do not "assess".
- Derive what a correct artifact must contain FIRST (you did this artifact-blind), then
  diff the real artifact against your own derivation.
- Run hot for recall. A separate layer validates; surface suspected flaws, do not withhold.

## The universal defect checklist (attack each)
1. **Objective fulfillment.** Does the artifact actually accomplish its stated
   objective, or an adjacent easier one? Name the gap.
2. **Claim support.** Is every material claim sourced / derived / evidenced? Flag every
   assertion that rests on nothing (an unsourced number, an unbacked "clearly", a cited
   source that does not say what it is cited for).
3. **Arithmetic + internal consistency.** Re-derive every computed number. Cross-check
   every figure that appears twice. Flag contradictions between sections.
4. **Failure modes + edge cases.** What input / condition / adversary breaks it? Which
   stated assumption, if false, collapses the conclusion — and is it stress-tested?
5. **Missing content.** What must a correct artifact of this class contain that is
   simply absent (a safety factor, a limitations section, a threat model, a control)?
6. **Overreach.** Where does the artifact claim more than its evidence licenses?

## Severity (pre-committed — do not negotiate per artifact)
CRITICAL (the artifact fails its core objective / is unsafe to ship) · HIGH (a material
defect that must be fixed before the boundary) · MEDIUM (a real but non-blocking gap) ·
LOW (minor) · NIT (cosmetic). A finding true of ANY artifact of the class ("could be
more robust", "add more tests") is GENERIC and does not count.

## Finding shape (mandatory pins)
location (line/section/quote/symbol) + concrete failure scenario (the specific way it
fails the objective) + severity. Tier confidence: VERIFIED (checked against the
artifact) / INFERRED / HYPOTHESIZED.

## Forbidden
- Predicting how a real audience will react (you are an internal QA lens, not an
  audience model).
- Generic praise or generic caveats.
- A clean bill with no named strongest-surviving-objection + no what-you-could-not-check.
