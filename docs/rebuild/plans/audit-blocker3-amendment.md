# Plan: Audit Blocker 3 (memory-system-subscription-routed-llm) amendment

Scope: the in-flight amendment #8 against session-established rules. Read-only.

## What I'm auditing
1. Proposal: `docs/rebuild/components/memory-system-subscription-routed-llm/proposal.md`
2. Preserved-research: `docs/rebuild/components/memory-system-gliner2-expansion/research.md`
3. Code: `memory-system/src/claude_print_client.py` (new),
   `memory-system/src/factory.py` (modified),
   `memory-system/src/process_of_arrival.py` (modified),
   `hands-off-lifecycle/README.md` (modified),
   `hands-off-lifecycle/tests/test_cross_cutting.py` (modified).
4. Tests: `memory-system/tests/test_claude_print_client.py` (new),
   `memory-system/tests/test_no_sealed_amendments.py` (new),
   `memory-system/tests/SEAL_COMMIT` (modified).

## Rules
- ODD §2.5 (no non-objective code)
- ODD §8 13-item reviewer checklist
- plan-before-code CDC (retro-check)
- all-work-through-background-agents (meta-check)
- scope-only-dispatch (meta-check)

## Method
1. Read proposal; extract ACs and their exact behaviour-shapes.
2. Read each touched file; map code surfaces to ACs.
3. Read each test; verify each test asserts AC outcome (not method).
4. Look for: dead defensive branches, silent except, platform branches, unused config, method-in-AC, argv structure assertions.
5. Verify AC7 (error-code-block discipline) test is structural, AC8 (reranker-no-bill) test counts zero OpenAI calls during ingest.
6. Check env-scrub / subprocess failure / JSON-parse paths in claude_print_client for silent swallowing without AC coverage.
7. Check no new plan file pre-exists for the amendment itself (plan-before-code retro).

## Halt triggers
- Proposal ACs unmeasurable against disk state -> halt, report.
- Step 4 commit lands mid-audit and changes the audited surface -> halt, report both states.

## Output
Concise audit report (findings, severity, recommendations) grouped by rule category; overall verdict.
