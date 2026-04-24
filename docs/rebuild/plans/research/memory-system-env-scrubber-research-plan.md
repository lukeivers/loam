# Research plan — memory-system env-scrubber (D4)

**Status:** research-plan for the D4 amendment cycle. Authored 2026-04-24 in the pos3 session that surfaced the underlying defect. Expected next artefact: a research doc at `docs/rebuild/plans/research/memory-system-env-scrubber-research.md` answering the questions below, from which a plan-to-amend is authored.

**Session-start corpus:** research agent reads the five mandatory paths in `CLAUDE.md`'s session-start-discipline section before answering any question below. Component-scoped reads: `docs/rebuild/components/memory-system/`.

---

## 1. Context

The 2026-04-23 pos3 session bisected empirically that `claude -p` on macOS under launchd's scrubbed env requires `USER` to resolve OAuth via the keychain. `memory-system/src/claude_print_client.py::_ENV_ALLOWED_VARS = ("PATH", "HOME")` drops `USER`; every LLM call from memory-system returns `"Not logged in · Please run /login"` under launchd. The fix *appears* trivial — add `USER` to the allowlist. The reason this is a research cycle rather than a one-line patch is the question of **test-shape** — the existing tests mocked at the subprocess boundary, so two amendment seals passed while the real external-surface defect shipped. The research is about closing that class of gap, not just the specific one.

## 2. Questions for the research agent

1. **Beyond `USER`, what other env vars does `claude -p` require** under (a) macOS launchd gui domain, (b) macOS launchd aqua domain, (c) non-interactive login shells, (d) future-reasonable execution surfaces the pos-v2 roadmap will touch? Empirical bisection acceptable.
2. **What test-shape would have caught the USER-missing defect at seal time?** Concretely: describe a test fixture that a memory-system seal test can run as part of its normal pytest invocation. Candidates include (builder-surfaced, not prescribed): launchd-simulator via `env -i`; a subprocess harness that invokes the real `claude -p` binary with a controlled env; a pure-Python fake-claude that validates the env it receives. The research ruling is between these, not a foregone conclusion.
3. **What's the scope of the allowlist widening?** `USER` is confirmed. Should `LOGNAME` also ride along (Linux precedent, even though pos-v2 is macOS-only today)? Should `__CF_USER_TEXT_ENCODING` or `TMPDIR` be included (session proved they are NOT required for OAuth, but may be needed for other claude-CLI paths the service doesn't yet exercise)? Name every candidate and rule it in or out with evidence.
4. **Is there a broader pattern to codify?** Does pos-v2 already have (or should it grow) a test-harness convention for "component spawns a subprocess with a scrubbed env"? The session surfaced this pattern (entry #3 in `POST_FIRST_RUN_REVIEW.md`) but the generalisation is a downstream decision — the research flags whether it belongs inside D4 or as a separate initiative.

## 3. Scope

- Read-only research. No source edits.
- Working directory `/Users/lukeivers/ivers-corp-pos-v2/`.
- Research agent may run `env -i ... claude -p ...` bisection locally (the pos3 session already did this; agent verifies the result in the canonical tree's environment).
- Research doc caps at ~400 lines, sized proportionate to the question.

## 4. Halt triggers

1. **Research reveals cross-component implications** (e.g., other components also spawn scrubbed-env subprocesses and share the same allowlist pattern). Halt and signal with the component list; owner decides whether D4 scope widens or the pattern gets a separate initiative.
2. **No test shape is verifiable without a method-prescription violation** (i.e., every candidate test-shape requires saying "the test uses X" in the AC). Halt and signal; owner rules on whether to accept the method-bound test or restructure the AC.
3. **Empirical bisection on claude CLI env requirements yields non-deterministic results** across runs. Halt; owner rules on whether to escalate to Anthropic claude-CLI maintainers or accept the empirical majority.
4. **ODD break detected as strongly required** (any kind). Halt and signal.

## 5. Acceptance (for this research-plan gate — not for the amendment)

A research document at the expected path answering questions §2.1–§2.4 with evidence-grounded answers (not inference). Each answer carries: (a) the claim, (b) the evidence (command output, test log, code reference), (c) the implication for the amendment plan.

## 6. CDC adherence

- **Plan-before-code:** this research plan exists; it unblocks the research step. When research completes, a plan document (not a research plan) is authored before any amendment commits.
- **Research-before-plan:** this IS the research step; it precedes the amendment plan authoring.
- **Scope-only dispatch:** this plan carries scope (question set, boundaries, halt triggers). It does NOT prescribe which test framework to use, which file to edit, or what the amendment-plan's ACs will look like — those are downstream judgments.
- **Background-agent-default:** the research step dispatches to a background agent with the brief derived from this plan.
