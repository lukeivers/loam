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

