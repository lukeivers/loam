# Non-tech user session — annotated transcript

> **Reference artefact for v0.7.0 AC.NTU.5.** Captured via the synthetic-proxy probe ratified per Q2 (Telegram 10648 — the dispatcher executes a stranger-clone-shaped session simulating a non-tech user; real-user validation reserved for the v1.0 quality-bar event). This transcript is illustrative — it shows what the persona's reply shape looks like for a non-tech user, with the four moments (onboarding question-set, natural-language ask, tier-conversation + structural-decision narration, working-software output).

## Setup

- **User:** synthetic non-tech user (a household-finance proxy; no prior loam exposure; no software-engineering background).
- **Workspace:** fresh `git clone lukeivers/loam` followed by the published quickstart command (see README §Quickstart). The workspace's `CLAUDE.md` is overridden with the household-finance reference at `docs/examples/corpus-overrides/household-finance-CLAUDE.md` (per the workspace-corpus-overrides pattern at `docs/workspace-corpus-overrides.md`).
- **Channel:** the user picked "CLI-only" at the onboarding question; replies stream to the terminal.

---

## Moment 1 — Onboarding question-set (the first 90 seconds)

The quickstart command runs the onboarding ritual. The user sees six plain-English questions, one at a time:

> **Q1:** I detected this looks like a household-finance workspace. Continue? (1) Yes (2) No, it's: \<free-form>
>
> **You:** 1
>
> **Q2:** Where do you want async pings when work completes? (1) Telegram (2) CLI-only (3) Skip for now
>
> **You:** 2
>
> **Q3:** Safety profile? (1) production-stake (2) dev (3) research
>
> **You:** 2
>
> **Q4:** Run the ODD extractor against this codebase now? (1) Yes — fire now (2) Defer — I'll run `loam odd-extract` later (3) Never — disable extractor for this workspace
>
> **You:** 3
>
> **Q5:** Enable continuous codebase-watch (auto re-extract when commits land)? (1) Yes (2) Defer [default] (3) No
>
> **You:** 3
>
> **Q6:** Auto-skill capture: when you do something repeatable, may I propose saving the steps as a re-usable skill? (1) Yes (2) Default-no [recommended for first-runs]
>
> **You:** 2

> *Onboarding complete. Summary written to `<workspace>/.loam/onboarding-summary.md`. Channel: CLI. Safety: dev. Run `claude` to begin a session with your primary persona.*

**Notes on the surface.** The questions use ordinary words — "where do you want pings," "safety profile," "auto-skill capture." There are no `objective`, `acceptance criterion`, `ODD`, `methodology`, or `AC.*` references in the user-facing question text. Q4 + Q5 mention an "extractor" (a domain-specific term for the ODD-extraction pipeline), but they're framed in terms of what the user does ("run it now" / "I'll run later" / "never") not what the substrate is.

---

## Moment 2 — The natural-language ask (the user's first real request)

The user opens a Claude Code session in the workspace. The primary persona greets them based on the household-finance corpus override:

> **Persona:** Hey — fresh workspace, household-finance shape. What's the first thing you want help with?
>
> **You:** I want to keep track of my monthly expenses going forward.

The ask is ambiguous between several implementation tiers. The persona surfaces the tier conversation per the implementation-tier-picker SKILL.

---

## Moment 3 — Tier conversation + structural-decision narration

> **Persona:** Three shapes fit this. Tier 2 is a script you run each month against your statement download — quick to build, you do the categorization re-merge yourself each month. Tier 3 keeps a running local spreadsheet of your expenses across months — your data accumulates in one place you can analyze; you'd back up the file periodically. Tier 4 is a daemon that auto-pulls statements and updates the spreadsheet — fully hands-off but it's a service running on your machine, so if your laptop reboots, the daemon restarts; if a dependency updates, it might break silently. I'd recommend tier 3 for this; your data accumulates in one place you can analyze, and the cost is a few hours up front plus a backup discipline. Want to go with tier 3, or pick tier 2 or 4?
>
> **You:** Tier 3.
>
> **Persona:** Got it. Building this as a local spreadsheet you'll re-run monthly because that's the tier-3 shape — your data accumulates in one file across months. Drop your December statement (CSV or PDF) in `~/loam-finance/statements/` and tell me when it's there.

**Notes on the surface.** The tier conversation uses the user's language ("script you run," "spreadsheet of your expenses," "daemon that auto-pulls"). The persona's narration of the structural decision ("Building this as a local spreadsheet because that's the tier-3 shape — your data accumulates in one file across months") is one sentence with the named lead-phrase pattern from the light-touch-narration SKILL. No ODD vocabulary.

---

## Moment 4 — Working-software output

The user drops their December credit-card statement at the agreed path. The persona builds the tier-3 deliverable:

- A Python script at `~/loam-finance/categorize.py` that reads a CSV statement, categorizes each transaction by simple keyword rules + a fall-through "uncategorized" bucket, appends rows to a master `~/loam-finance/expenses.csv`.
- A small README at `~/loam-finance/README.md` explaining the monthly run + how to back up the master CSV.
- The first run already done: December 2025 transactions categorized, appended to `expenses.csv`, summary surfaced in the chat.

> **Persona:** December categorized + appended. Top three categories: Groceries $612 (38 transactions), Restaurants $284 (19 transactions), Subscriptions $147 (8 recurring charges). Two charges fell through to "uncategorized" (an Amazon transaction with no merchant name, and a $42 charge from "PAYPAL TRANSFER"). Want to add keyword rules for those, or leave them uncategorized?

The deliverable is real software (executable Python script). The output is real data (categorized December transactions). The exchange used zero ODD vocabulary; the user got tier-3 working software end-to-end via natural-language conversation only.

---

## Reference artefacts produced

The synthetic proxy run produces the following workspace state:

- `<workspace>/.pos/bootstrap.yaml` — onboarding state (channel_preference=cli; primary_channel=terminal; safety_profile=dev; per AC.NTU.2).
- `<workspace>/.loam/onboarding-summary.md` — onboarding completion summary (per AC.ONBOARD.9).
- `~/loam-finance/categorize.py` — the tier-3 deliverable (illustrative path; the actual location depends on the user's home dir + the persona's pick).
- `~/loam-finance/expenses.csv` — the persistent local data file.
- `~/loam-finance/README.md` — runbook for the monthly run.

These artefacts are NOT shipped in the loam repo (they're per-user, per-run); the test at `framework/workspace-bootstrap/tests/test_AC_NTU_6_outcome_altitude_stranger_clone.py` exercises the substrate that produces them.

---

## What this transcript IS NOT

- **Not a live capture from a real session.** The synthetic proxy is the dispatcher's stipulated stand-in per Q2 ratification. Real-user shipping (the v1.0 criterion #2 event) is a separate next-stage milestone.
- **Not a script the persona reads.** The persona reads its skills + corpus, not this doc; the transcript is documentation for builders + reviewers showing what the v0.7.0 surface produces.
- **Not exhaustive.** Only the four named moments are shown — the realistic session has more turns (e.g., the user asking about backup options, the persona surfacing the keyword-rule extension when the second uncategorized charge comes in next month).

---

## Authority

- Plan-doc: `docs/plans/v0-7-0-non-tech-user-surface.md` AC.NTU.5.
- Q2 ratification: synthetic proxy as the v0.7.0 ship probe; real-user shipping reserved for v1.0 criterion #2 event (Telegram 10648).
- Outcome-altitude probe: `framework/workspace-bootstrap/tests/test_AC_NTU_6_outcome_altitude_stranger_clone.py`.
