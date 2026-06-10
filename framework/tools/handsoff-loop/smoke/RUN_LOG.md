# Build-from-intent honest run log (S6 — AC.SMK.*)

Unfiltered log of general-path proof runs. Contract: every run is
logged whatever its result (fails included); every number carries its
run-of-origin (the entry it appears in names the ask verbatim, the
workspace, the loam commit, and the timestamp); any logged run is
reproducible from the documented command inside its entry.

All archetypes — the back-office trio AND every off-vertical probe —
flow through the IDENTICAL underlying command (it is printed in each
entry; the harness has no per-archetype branching). To run one more
case from a prompt no builder has seen:

```
python3.13 framework/tools/handsoff-loop/smoke/run_smoke.py \
    --archetype off-vertical --prompt-file <sealed-prompt-file>
```

---
## 2026-06-10 00:25:14 — app1-reconciliation — terminal: **done**

- run-of-origin: this entry (loam commit `cc394548`, workspace `/var/folders/j3/0dgy1nsj045crxwt4t_h05m80000gn/T/bfi-smoke-app1-reconciliation-mk_77g5b`, started 2026-06-10 00:25:14)
- ask (verbatim): every month I get a bank statement export and a list of the invoices we sent, and I have to match them up by hand to find what hasn't been paid. the statement is a csv with a date, an amount, and a reference column that usually has the invoice number somewhere in it, and the invoice list is a csv with invoice number, customer, and amount. can you build me something that does the matching for me and gives me a clear list of what's still unpaid and anything on the statement it couldn't place
- wall-clock: 891.7s [this run]
- result: done — fails included by contract; an honest negative is logged exactly like a pass
- grounding: grounded=True | live-verified citations=6 | dropped=0 [this run]
- gate criteria: 8 total, 8 traceable to practitioner norms [this run]
- convergence: stop_reason=done | refine_attempts=0 | timed_out=False | timeout_retries=0 [this run]
- progress audit: user-visible updates=19 | max gap=120.0s (monotonic clock; wall 120.0s) | within heartbeat bound=True | unverifiable claims=0 [this run]
- human gates fired this run:
  - question (unanswered): When a statement entry's reference column contains an invoice number and the amounts match, do you consider it paid — or do you want to flag amount mismatches separately (e.g. partial payments)?
  - question (unanswered): Should the output go into a new CSV file, or is a readable text/markdown report in the terminal enough?
  - expert-gate flag: Partial-payment handling: the research identifies partial payments and batch payments (one bank entry covering multiple invoices) as real practitioner scenarios, but the build objective specifies single-amount matching. Whether the CLI should handle these cases — or explicitly flag them as out of scope — is a product decision that requires owner input before implementation.
  - expert-gate flag: Materiality threshold configuration: practitioners set organisation-specific tolerance thresholds (e.g. £20 or 1%) before automating. The research could not settle what default, if any, is appropriate for a general-purpose CLI; an accountant or the tool's intended user should specify the default and whether it should be configurable at runtime.
- reproduce this run:
  ```
  PYTHONPATH=/Users/lukeivers/loam/framework/tools/handsoff-loop/src python3.13 -m handsoff_loop.cli build-from-intent --ask "every month I get a bank statement export and a list of the invoices we sent, and I have to match them up by hand to find what hasn't been paid. the statement is a csv with a date, an amount, and a reference column that usually has the invoice number somewhere in it, and the invoice list is a csv with invoice number, customer, and amount. can you build me something that does the matching for me and gives me a clear list of what's still unpaid and anything on the statement it couldn't place" --workspace /var/folders/j3/0dgy1nsj045crxwt4t_h05m80000gn/T/bfi-smoke-app1-reconciliation-mk_77g5b --yes
  ```

## 2026-06-10 00:40:49 — app3-customer-dedupe — terminal: **done**

- run-of-origin: this entry (loam commit `06e7aa4e`, workspace `/var/folders/j3/0dgy1nsj045crxwt4t_h05m80000gn/T/bfi-smoke-app3-customer-dedupe-tddgkdca`, started 2026-06-10 00:40:49)
- ask (verbatim): we merged with another company and now we have two customer lists that overlap a lot. both are csv files with name, email, and phone, but the same person is often spelled a bit differently in each or missing a phone in one. I need one clean combined list where each customer appears only once, and I want to see which rows it merged so I can spot-check it didn't combine two different people
- wall-clock: 654.9s [this run]
- result: done — fails included by contract; an honest negative is logged exactly like a pass
- grounding: grounded=True | live-verified citations=6 | dropped=0 [this run]
- gate criteria: 8 total, 6 traceable to practitioner norms [this run]
- convergence: stop_reason=done | refine_attempts=0 | timed_out=False | timeout_retries=0 [this run]
- progress audit: user-visible updates=17 | max gap=120.0s (monotonic clock; wall 120.0s) | within heartbeat bound=True | unverifiable claims=0 [this run]
- human gates fired this run:
  - question (unanswered): When the same person appears in both files with different phone numbers (not just one missing), which should win — the first file, the second file, or should both be kept and flagged for you to decide?
  - question (unanswered): How strict should the name matching be — for example, should 'Bob Smith' and 'Robert Smith' be considered the same person, or only clearly typoed versions like 'Bob Smtih' and 'Bob Smith'?
  - expert-gate flag: The correct similarity threshold for the middle 'flag for review' band is dataset-dependent — the literature consistently states 'there is no magical number' and the right cutoff requires empirical testing against labeled sample pairs from the actual data; a human familiar with the data should set or validate this threshold before the tool is used in production.
  - expert-gate flag: Phone number normalization (international prefixes, formatting variants) is not addressed in the retrieved sources — a practitioner familiar with the expected phone number formats in these specific CSVs should specify the normalization rules.
- reproduce this run:
  ```
  PYTHONPATH=/Users/lukeivers/loam/framework/tools/handsoff-loop/src python3.13 -m handsoff_loop.cli build-from-intent --ask "we merged with another company and now we have two customer lists that overlap a lot. both are csv files with name, email, and phone, but the same person is often spelled a bit differently in each or missing a phone in one. I need one clean combined list where each customer appears only once, and I want to see which rows it merged so I can spot-check it didn't combine two different people" --workspace /var/folders/j3/0dgy1nsj045crxwt4t_h05m80000gn/T/bfi-smoke-app3-customer-dedupe-tddgkdca --yes
  ```

## 2026-06-10 00:52:19 — app2-books-migration — terminal: **done**

- run-of-origin: this entry (loam commit `00f7e044`, workspace `/var/folders/j3/0dgy1nsj045crxwt4t_h05m80000gn/T/bfi-smoke-app2-books-migration-aivhx4yb`, started 2026-06-10 00:52:19)
- ask (verbatim): we're moving our bookkeeping to a new system and the export from the old one uses category names that don't line up with the new system's categories. I have the old export as a csv with date, description, amount, and old category, and a small csv that maps old category names to new ones. I need something that converts the old file into the new format using that mapping and gives me a list of any entries it couldn't map so a person can decide those
- wall-clock: 443.3s [this run]
- result: done — fails included by contract; an honest negative is logged exactly like a pass
- grounding: grounded=True | live-verified citations=5 | dropped=0 [this run]
- gate criteria: 5 total, 4 traceable to practitioner norms [this run]
- convergence: stop_reason=done | refine_attempts=0 | timed_out=False | timeout_retries=0 [this run]
- progress audit: user-visible updates=13 | max gap=120.0s (monotonic clock; wall 120.0s) | within heartbeat bound=True | unverifiable claims=0 [this run]
- human gates fired this run:
  - expert-gate flag: The exact format of the unmapped-rows output file is not settled by practitioner convention — whether it should carry extra columns (e.g. an 'error reason' column), use the same header schema as the main output, or differ in structure is a judgment call for the owner.
  - expert-gate flag: Whether category matching should be exact-string-only or should tolerate minor variations (case, whitespace, common abbreviations) depends on how messy the real export data is — this requires a human familiar with the specific bookkeeping software's export behavior to decide.
  - expert-gate flag: What to do when the same source category maps to multiple target categories (a one-to-many ambiguity in the mapping CSV) is not addressed by any source retrieved; a human expert should specify the desired behavior before implementation.
- reproduce this run:
  ```
  PYTHONPATH=/Users/lukeivers/loam/framework/tools/handsoff-loop/src python3.13 -m handsoff_loop.cli build-from-intent --ask "we're moving our bookkeeping to a new system and the export from the old one uses category names that don't line up with the new system's categories. I have the old export as a csv with date, description, amount, and old category, and a small csv that maps old category names to new ones. I need something that converts the old file into the new format using that mapping and gives me a list of any entries it couldn't map so a person can decide those" --workspace /var/folders/j3/0dgy1nsj045crxwt4t_h05m80000gn/T/bfi-smoke-app2-books-migration-aivhx4yb --yes
  ```

## 2026-06-10 01:47:51 — off-vertical — terminal: **done**

- run-of-origin: this entry (loam commit `a3f58a21`, workspace `/var/folders/j3/0dgy1nsj045crxwt4t_h05m80000gn/T/bfi-smoke-off-vertical-cjq274k9`, started 2026-06-10 01:47:51)
- ask (verbatim): I help run a small rec soccer league for kids and the scheduling is killing me.
We've got 12 teams this fall and 3 fields we can use on Saturdays. I end up
doing the whole season schedule in a spreadsheet by hand every year and someone
always ends up mad — some team gets the early morning slot four times, some
team plays the same opponent twice before they've played everyone once. Can you
make me something that builds a fair season schedule and actually shows me it's
fair? I'm not technical so it needs to just work.
- wall-clock: 1435.7s [this run]
- result: done — fails included by contract; an honest negative is logged exactly like a pass
- grounding: grounded=True | live-verified citations=6 | dropped=0 [this run]
- gate criteria: 8 total, 8 traceable to practitioner norms [this run]
- convergence: stop_reason=done | refine_attempts=0 | timed_out=False | timeout_retries=0 [this run]
- progress audit: user-visible updates=24 | max gap=120.0s (monotonic clock; wall 120.0s) | within heartbeat bound=True | unverifiable claims=0 [this run]
- human gates fired this run:
  - question (unanswered): How many Saturdays long is the season, and how many games does each team play? (For example: 10 weeks, each team plays once per week?)
  - question (unanswered): What are the time slots available each Saturday — for example, 8 AM, 10 AM, noon — and is 'early morning' just the first slot of the day, or are there specific slots you're trying to keep fair?
  - expert-gate flag: Whether to run a single round-robin (each pair plays once, 11 rounds) or a double round-robin (each pair plays twice, 22 rounds) is a season-length policy decision that depends on the league's intended number of weeks and cannot be resolved by scheduling standards alone — a league organizer must decide.
  - expert-gate flag: How to rank or weight time slots as 'prime' versus 'non-prime' (e.g., whether 10 AM is preferable to 8 AM, or whether a late afternoon slot is desirable) is league- and participant-specific; research did not surface a universal rec-league standard for this ranking, so the league operator should specify slot preferences before the fairness metric is computed.
  - expert-gate flag: Whether 'field fairness' means each team plays an equal number of games on each of the 3 fields, or simply avoids over-concentration on one field, is an implementation choice with real schedule-feasibility trade-offs for 12 teams across 11 rounds that a human organizer should decide up front.
- reproduce this run:
  ```
  PYTHONPATH=/Users/lukeivers/loam/framework/tools/handsoff-loop/src python3.13 -m handsoff_loop.cli build-from-intent --ask "I help run a small rec soccer league for kids and the scheduling is killing me.\nWe've got 12 teams this fall and 3 fields we can use on Saturdays. I end up\ndoing the whole season schedule in a spreadsheet by hand every year and someone\nalways ends up mad — some team gets the early morning slot four times, some\nteam plays the same opponent twice before they've played everyone once. Can you\nmake me something that builds a fair season schedule and actually shows me it's\nfair? I'm not technical so it needs to just work." --workspace /var/folders/j3/0dgy1nsj045crxwt4t_h05m80000gn/T/bfi-smoke-off-vertical-cjq274k9 --yes
  ```

