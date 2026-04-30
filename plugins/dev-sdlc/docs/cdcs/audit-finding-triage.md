# Core Development Convention — audit-finding triage by severity

> **Audit findings where no named acceptance criterion backs the code in question (`AC:none`) are triaged by risk severity rather than treated as uniformly mandatory fixes. Outright silent-except violations (no observable surface, no typed-result conversion, no teardown-path exception per the shutdown-path CDC) are fixed. Patterns recognised as legitimate engineering practice are codified as CDC exceptions (like the shutdown-path CDC). Borderline cases (e.g. missing-file fallbacks) graduate by adding AC backing, promoting to violations, or codifying as accepted.**

Rationale. Strict §2.5 read demands every line of production code map to a named AC. Realistically, some patterns are universal engineering invariants (teardown-path cleanup, structured-error return types, optional-config defaults) that don't require per-component AC authorship and would only be ceremony if required. Pragmatism requires a triage scheme. This CDC records the scheme explicitly so future audits don't re-raise already-resolved patterns, and so the boundary between "fix it" and "codify the exception" has a procedure rather than being re-negotiated per audit.

How to apply. When an audit turns up a finding with `AC:none`, ask:

1. Is this a pattern already codified as a CDC exception? If yes, skip.
2. Is the exception observably surfaced to the caller (typed result, log, event emission)? If yes, likely legit — categorise as exception-to-result conversion, skip.
3. Is this a recognised engineering-universal pattern worth codifying as a new CDC? If yes, propose the CDC first, then skip.
4. Is this a genuine silent swallow with no observable surface? Fix it — promote to a violation, amend.

The amendment that fixes (4) findings can batch them by risk profile (safety-critical paths first, user-visible next, internal/observability third).

Applied immediately to all audit triage from 2026-04-22 forward.
