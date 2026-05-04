# Contract draft — synthetic-fixture (v0.1.8 Cycle 2 test fixture)

**Status:** synthetic — for ratification-workflow tests only.

**Extraction ID:** synthetic-fixture-v0-1-8-c2

---

## Acceptance criteria

<!-- ACS_TABLE_HERE -->

| AC | Band | Evidence kind | Citations |
|----|------|---------------|-----------|
| AC.SYNTH.1 | VERIFIED | test | 2 citation(s) |
| AC.SYNTH.2 | PLAUSIBLE | source | 2 citation(s) |
| AC.SYNTH.3 | HYPOTHESISED | inference | (none) |

### AC.SYNTH.1 — VERIFIED

User authentication flow validates password length >= 8.

- Evidence kind: test
- Citations: tests/test_auth.py::test_password_length_validation, app/auth.py:42-58
- Repo SHA: abc1234567890def

### AC.SYNTH.2 — PLAUSIBLE

Order model has-many LineItems with cascade-delete on order destruction.

- Evidence kind: source
- Citations: app/models/order.rb:12, db/migrate/2024_01_15_create_line_items.rb:8-15

### AC.SYNTH.3 — HYPOTHESISED

Payment gateway retries failed charges up to 3 times with exponential backoff.

- Evidence kind: inference
- Rationale: inferred from a comment + absence of application-level retry code.

---

## Unhandled paths

<!-- COVERAGE_GAPS_HERE -->

_No unhandled paths._

---

## Provenance

- Synthetic fixture for v0.1.8 Cycle 2 ratification tests.
- Plan-doc: `docs/rebuild/plans/v0-1-8-cycle-2-confidence-bands-and-ratification.md`.
