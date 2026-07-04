# Seeded-flaw calibration result — REAL isolated-critic run

**Tier-0 evidence (a real subscription `claude -p` run via the sealed `spawn_isolated_claude`, NOT a stub).** This is the harshness proof (P8 / AC.AR.10) the owner gates on before using manual mode on a real external deliverable.

- run at: 2026-07-03 12:13 
- against build: `7f20b07`
- tier: STANDARD (one two-phase falsification critic + validation)
- critic model: sonnet (default; via isolated spawn)
- wall-clock: 197s (two isolated spawns: derive + diff)
- review ran: **True**

## Catch rate

**CATCH RATE: 1.00 (3/3 seeded flaws caught)**

| seeded flaw | anchor | caught? |
|---|---|---|
| ARITHMETIC — 12 x $350K = $4.2M, not the stated $3.6M — arithmetic error | `$3.6M` | YES |
| CONTRADICTION — claims 'pre-revenue' in stage but '$2M ARR' in traction — internal contradiction | `$2M ARR` | YES |
| UNSOURCED — the $50B TAM is 'sourced' only to an internal estimate — unsupported market claim | `$50B` | YES |

Plus **6 additional finding(s)** the critic surfaced beyond the seeded set (real flaws it was not planted to find).

## Raw critic findings (post-validation, as surfaced)

Verdict: **BLOCK** (methodology: domain-agnostic)

### Finding 1 — VALIDATED / CRITICAL (BLOCKING)
- location: "Traction" — "$2M ARR" and "Revenue projection" — "$3.6M"
- scenario: No revenue recognition basis is stated. Is the $2M ARR recognized revenue, contracted ARR, or cash-collected? Is the $3.6M projection recognized on delivery or contracted? If the design-partner agreements are multi-year contracts recognized ratably, the two figures are on different bases and cannot be compared. FA2 is a mandatory requirement; its absence makes both numbers ambiguous on arrival.
- validation: deterministic: cited anchor present in artifact

### Finding 2 — VALIDATED / HIGH (BLOCKING)
- location: "Revenue projection" — entire section
- scenario: No assumption register exists. The projection rests on entirely unstated assumptions: outreach-to-close conversion rate, sales cycle length, pricing basis ($350K flat, per-seat, or tiered), and implied sales capacity. Without an enumerable assumption set, no single assumption can be stress-tested and the investor has no way to determine which input failure collapses the thesis. FA4 is a mandatory requirement.
- validation: deterministic: cited anchor present in artifact

### Finding 3 — VALIDATED / HIGH (BLOCKING)
- location: "Traction" and "Revenue projection" — no churn or retention figure anywhere
- scenario: The $2M design-partner ARR is implied to persist, but no renewal rate, churn rate, or net revenue retention figure is stated. Design-partner agreements commonly lapse or reprice when a product formally launches. If the three design partners churn, the year-one starting ARR is $0, not $2M — a scenario the memo makes no provision for. Without a stated retention assumption, the revenue trajectory is underdetermined. FA5 is a mandatory requirement.
- validation: deterministic: cited anchor present in artifact

### Finding 4 — HYPOTHESIZED / MEDIUM (non-blocking)
- location: Entire document — no CAC, LTV, gross margin, or payback period
- scenario: Zero unit economics appear. At $350K ACV with no stated CAC, an investor cannot determine whether the business is economically viable — a $350K ACV with a $500K CAC is value-destroying. Without gross margin, the revenue figure cannot be mapped to gross profit, making the capital requirement for the $6M raise unintelligible. FA8 is a mandatory requirement.
- validation: no executable anchor; quarantined pending validation

### Finding 5 — VALIDATED / HIGH (BLOCKING)
- location: "Revenue projection" — "We will onboard 12 enterprise customers in year one"
- scenario: No go-to-market mechanism is named. The projection assumes 12 enterprise closings with no stated sales motion, channel, or pipeline. At typical enterprise win rates (5–15% from qualified pipeline), 12 closings require 80–240 qualified opportunities. The memo provides no basis for this pipeline existing. O2 requires a named GTM path that could plausibly produce the stated capture rate; its absence makes the 12-customer number unsupported.
- validation: deterministic: cited anchor present in artifact

### Finding 6 — VALIDATED / HIGH (BLOCKING)
- location: "Company stage" — "product ships next quarter" vs. "Revenue projection" — 12 enterprise customers in year one
- scenario: Enterprise sales cycles typically run 6–12 months. If the product ships one quarter into year one, closing 12 enterprise deals within the remaining 2–3 quarters requires roughly 24 simultaneous in-flight deals at or before launch — from a company with no product in market. The memo does not acknowledge this temporal constraint, making the year-one customer count internally inconsistent with the company's own stated launch timeline. F3 requires this cross-check; it is not addressed.
- validation: deterministic: cited anchor present in artifact

### Finding 7 — VALIDATED / MEDIUM (non-blocking)
- location: "Market" section — only TAM provided; no SAM or SOM
- scenario: The memo provides a $50B TAM with no SAM or SOM. Without the SAM, the penetration read is distorted: $4.2M against a $2B SAM (enterprise, North America) is 0.21% penetration — a different story than 0.0084% of the $50B TAM. F5 and S3 require this distinction; its absence means an investor cannot determine whether the projected revenue represents a credible or implausible market-capture rate.
- validation: deterministic: cited anchor present in artifact

### Finding 8 — VALIDATED / MEDIUM (non-blocking)
- location: "Market" — $50B TAM, no vintage date on the estimate
- scenario: The TAM carries no publication year. S3 requires market-size data ≤3 years from memo date, or acknowledged staleness. An undated internal estimate at $50B could be built on pre-current assumptions or a market that has since subdivided. This compounds the already-critical sourcing problem: the number has no external author and no date.
- validation: deterministic: cited anchor present in artifact

## Interpretation

A catch rate at/above the calibration bar with the planted flaws named by location is the evidence the reviewer is genuinely harsh — not a rubber stamp. A DECLINING catch rate on this cadence is a defect IN THE REVIEW STAGE and is fixed at the stage, never waved off (D9).
