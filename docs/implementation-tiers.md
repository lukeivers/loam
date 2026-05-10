# Implementation tiers — a ladder for scoping non-tech user work

> **Five tiers, plain-English, ordered by capability + cost + risk.** Each tier names what the deliverable is, when it fits, what it costs (build time + ongoing time + dollars), and what it costs you when it goes wrong. The persona uses this ladder to have a one-question conversation with the user before authoring anything; the user picks a tier; the persona ships at that tier.

The point: judging the right level of implementation effort is the hardest part of working with non-tech users. Over-build (ship a full SaaS when a one-time script was wanted) wastes time and ships a thing the user didn't ask for. Under-build (ship a one-time script when they expected a recurring system) under-delivers. The tier ladder makes the choice explicit, surfaceable, and reversible.

---

## The five tiers

### Tier 1 — one-time on-thread

**Shape:** the persona generates the output inside the conversation. Nothing persists outside the chat transcript. You read it, copy it if you want to keep it, move on.

**When it fits:** one-off questions. "Summarize this article." "Draft a single email." "What does this regex do?" "Calculate the compound growth on this CD." Anything you want answered once, not repeated.

**Cost:** build time = the conversation itself. Ongoing time = zero (nothing to maintain). Dollars = zero (subscription cost only).

**What it costs you when it goes wrong:** you re-ask. The conversation is the artefact; if it's wrong, the next message corrects it.

---

### Tier 2 — reusable script

**Shape:** a script saved as a file you can re-run. No persistent data; no scheduled execution; you invoke it manually each time. Output goes to your terminal or a temp file.

**When it fits:** something you'll do more than once but on your own schedule. "Pull my December credit-card statement and categorize it." "Generate an invoice from these line items." "Convert these images." "Run this query against my CSV." Recurrence: monthly, weekly, ad-hoc-but-recurring.

**Cost:** build time = 15 minutes to a couple hours per script. Ongoing time = the script may need light maintenance (input format changes). Dollars = zero.

**What it costs you when it goes wrong:** the script errors out, you re-run it or the persona patches it. Output is local; nothing leaks.

---

### Tier 3 — local file-based

**Shape:** a script plus persistent local data files (CSV, SQLite, JSON, etc.). The script reads + writes the data files; state accumulates across runs. You run it manually; the data sticks around.

**When it fits:** anything where you're tracking state over time, but the state is yours alone, on your machine. Personal expense tracker. Reading list. Habit tracker. Simple journal. Local todo list.

**Cost:** build time = a couple hours to a day. Ongoing time = the data file needs occasional cleanup; backups become your responsibility (the persona will surface backup options at build time). Dollars = zero.

**What it costs you when it goes wrong:** your local data file is corrupted or lost. Recovery options depend on whether you're backing up. The blast radius stays on your machine.

---

### Tier 4 — local service-based

**Shape:** a long-running local process (a daemon, a scheduled job via launchd / cron / equivalent, or a local web service you visit at `localhost`). Runs on your machine, not just when you invoke it.

**When it fits:** something that needs to happen even when you're not thinking about it. "Pull my email every morning at 6am and summarize." "Watch this folder and process new files automatically." "Run a local dashboard I can check from my browser." Recurrence: continuous, scheduled, or event-driven.

**Cost:** build time = a day or more. Ongoing time = service occasionally needs attention (it's running on your machine; if your machine reboots, the service restarts; if a dependency updates, the service may break). Dollars = zero.

**What it costs you when it goes wrong:** the service silently fails. You don't notice for a day, a week, a month, depending on how attentive you are. The persona will set up basic monitoring (errors written to a log; failure surfaces in the next conversation), but the cognitive load is real — you've now got a system running on your machine.

---

### Tier 5 — external service

**Shape:** a cloud-deployed application reachable from the internet. You (or other people) interact with it through a URL. Data lives somewhere other than your machine. Authentication, security, ongoing operational liability are all in scope.

**When it fits:** rarely for an individual user. Tier 5 is genuinely the right answer when (a) you need other people to use the thing, OR (b) you need access from devices you don't control, OR (c) the workload genuinely needs more compute than your machine reasonably handles. **Most non-tech users should never need this tier.**

**Cost:** build time = days to weeks. Ongoing time = sustained — security patches, monitoring, paying attention to bills, handling auth changes when third parties update their systems. Dollars = $5/mo to $hundreds/mo depending on traffic and which services back it.

**What it costs you when it goes wrong:** **this is where the risk surfacing matters.** A misconfigured external service can:

- **Expose data publicly** that you thought was private. Customer info, payment details, personal records — anything the service touches. Once exposed, you cannot un-expose; cached scrapers archive it.
- **Get used by attackers** as an open API, sometimes ringing up bills (cloud-compute crypto-mining is a known pattern).
- **Cost you reputationally** if it's a service that other people use and it leaks their data.
- **Trigger compliance obligations** you weren't expecting (GDPR, CCPA, HIPAA depending on what's stored).

Selecting tier 5 requires an explicit conversation about:

1. **What data flows through it.** Anything regulated? Anything that would harm a third party if exposed?
2. **Who can reach it.** Public internet, allowlisted users, behind your VPN, etc.
3. **What auth is in front of it.** Open, basic auth, OAuth, equivalent.
4. **Who notices when it breaks.** You? An on-call rotation? Nobody?
5. **Who pays the bill.** Your card on file; cap on monthly spend; consequences of cap-hit.
6. **Exit plan.** What happens if you stop maintaining it — does it stop, or does it accrue charges?

If any of these questions doesn't have a clear answer the user is comfortable with, **tier 5 is the wrong tier.** Drop down to tier 4 and accept the local-only constraint, or reduce the scope so a lower tier fits.

---

## How the persona uses this ladder

The implementation-tier-picker SKILL (at `framework/primary-persona/skills/implementation-tier-picker.md`) instructs the persona to surface the tier ladder when:

1. The user's ask is ambiguous between tiers (e.g., "I want to track my expenses" — tiers 2, 3, 4 are all reasonable).
2. The user's ask explicitly names a tier the persona thinks is wrong (e.g., user asks "build me a SaaS for X" but tier 2 would solve their problem).
3. The user's ask falls into tier 5 territory (always — tier 5 selection is structural conversation, never implicit).

The conversation is short — the persona names the relevant tiers (usually 2-3 candidates), names the cost / capability / risk shape of each, and asks ONE question: which tier. The user picks; the persona builds at that tier with a one-sentence narration of why it picked the chosen path.

---

## Composes with

- **`light-touch-narration` SKILL** — once a tier is picked, the tier choice is one of the structural decisions that the persona narrates in the action-confirmation reply (per AC.NTU.1).
- **`safety_profile` (workspace-bootstrap manifest)** — production-stake workspaces flip stricter floors at every tier; tier 5 in production-stake mode requires an even harder conversation (auth + audit-trail + retention obligations all become non-tunable floors).
- **Cost governance** — each tier has a different cost shape; the persona surfaces cost-band when discussing the tier (see `framework/cost-governance/`).
- **Workspace-corpus overrides** — workspaces with a specific domain (e.g., the household-finance reference at `docs/examples/corpus-overrides/household-finance-CLAUDE.md`) may specialize the tier conversation in their CLAUDE.md override (e.g., "for this workspace, never tier 5 — household data stays local").

---

## Authority

- Plan-doc: `docs/plans/v0-7-0-non-tech-user-surface.md` AC.NTU.7.
- Source idea: `docs/FUTURE_IDEAS_DRAFT.md` (Telegram 10575 capture, 2026-05-09).
- Composition note: this surface is part of the v0.7.0 non-tech-user end-to-end flow per Q3 = FOLD IN ratification.
