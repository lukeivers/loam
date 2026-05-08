# Example plan-doc — Code Review composition

**Status:** EXAMPLE / non-load-bearing reference. This plan-doc is illustrative — it demonstrates the composition pattern named in `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` "Compose on Claude Code review primitives" section + `docs/plans/v0-4-0-cycle-3-substrate-composition-routines-codereview-outcomes.md` (cycle plan). Not consumed by `loam amend apply` / `loam amend seal`. NOT a real cycle.
**Date authored:** 2026-05-08 (v0.4.0 Cycle 3).
**Composes on:** the plan-author SKILL's compose-on-claude-code-review section.

---

## §1 — Outcome shape (the example's "why")

This example shows a plan-doc with a **review-as-plan-step** composition — the plan-doc names a verified-live Claude Code review primitive (`claude ultrareview` / `/review` / `/security-review`) as a discrete step in the cycle ladder, rather than reimplementing review prose inside loam. The pattern composes on Claude-native review capability per Lens 1 (Claude-leverage-first); loam's job is to dispatch + sequence, not to reinvent review heuristics.

The example uses a hypothetical "feature-X cycle that ships untrusted-input handling" (a security-sensitive surface). The cycle's review-step composes on `/security-review` SKILL specifically, not generic `/review`, because the AC family includes input-validation + injection-prevention concerns.

## §2 — Verified-live Code Review invocation surface

Per the v0.4.0 C3 verification at HEAD (`claude --version` `2.1.128`):

- **`claude ultrareview` subcommand** — *"Run a cloud-hosted multi-agent code review of the current branch (or a PR number / base branch) and print the findings."* Use for cloud-hosted multi-agent review of a branch or PR.
- **`/review` SKILL** — *"Review a pull request."* Use for in-session PR review.
- **`/security-review` SKILL** — *"Complete a security review of the pending changes on the current branch."* Use for security-specific review of pending changes.
- **`/ultrareview` SKILL** — slash-surface wrapper around the `claude ultrareview` CLI subcommand.

The conference research at `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §1 #5 named the verb as `claude code review` and §1 #7 named the security verb as part of "Security Reviews (Claude Code)". **Neither `claude code` nor `claude code review` exists as a subcommand at HEAD.** This example uses the verified-live `/security-review` SKILL surface for the security-cycle case + `claude ultrareview` for the multi-agent branch-review case; the conference-research naming is documented as divergence and the pattern stands.

## §3 — Example plan-step shape (security-sensitive cycle)

Inside a real plan-doc's §4 AC family, a security-review step would look like this:

```
- AC.UIH.1 — Untrusted-input handling cycle dispatches the
  /security-review SKILL after the source-edit feat commit
  lands and before `loam amend apply`. The review runs
  against the pending changes on the current branch; the
  dispatcher records the SKILL's findings inline in the
  plan-doc's §10 F2 RF section.
- AC.UIH.2 — `claude ultrareview` runs against the cycle's
  branch as a final cross-check. Both SKILL output and
  ultrareview output are captured in the build report; any
  HIGH-severity findings are halt-and-surface conditions
  before seal.
- AC.UIH.3 — Outcome-altitude: the seal commit lands only
  after both review primitives report no HIGH-severity
  findings (or owner ratifies a documented exception).
  Verified by build-report cross-references at seal time.
```

## §4 — Why this composition is correct

Per the plan-author SKILL "Compose on Claude Code review primitives" section's when-to-compose conditions:

- **Review-as-plan-step** (this example): the cycle has a discrete review step in the ladder; the SKILL or CLI runs once at the named position; output feeds the next step.
- **Review-as-cycle**: not used here; would apply if the entire cycle is "review the prior cycle's output" (e.g., a v0.X.Y patch cycle that's purely a review pass).
- **Hand-author review prose**: not used here; would only apply when no Claude-native review surface fits (rare; almost always one of the verified-live surfaces matches).

This example matches review-as-plan-step. The security-review concerns are AC-aligned; the review primitive is dispatched at the right ladder position; output feeds halt-and-surface decisions before seal.

## §5 — Graceful degradation

If `/security-review` SKILL is not available (e.g., older `claude` binary or a stranger running without the security-review plugin), the plan-doc falls back to:

- **`claude ultrareview` only** — the multi-agent CLI subcommand covers a broader surface; security findings surface via the multi-agent output. Less specific than `/security-review`, but available.
- **Hand-author review prose** — last resort. The plan-doc author writes a review-checklist into §10 F2 RF and the build agent self-reviews against it. This is a graceful-fallthrough-with-detection pattern; the plan-doc's pre-build step checks the available-skills list and routes accordingly.

## §6 — Composition with other plan-doc surfaces

- **plan-docs-author SKILL** "Compose on Claude Code review primitives" section — names the rubric this example follows.
- **dispatch-brief-authoring SKILL** — when the cycle's build agent is dispatched, the brief includes the review-step invocation as a named ladder position; the agent runs the review and surfaces findings before proceeding.
- **`feedback_no_anthropic_api_key.md`** — `claude ultrareview` and `/review` / `/security-review` SKILLs run on subscription auth; no API key needed; subscription-only invariant preserved.
- **`feedback_specific_claims_verified_or_marked_guess.md`** — drove the §2 CLI-surface verification step.
- **PR-safety + audit-finding-triage SKILLs** — review findings feed into the audit-finding-triage SKILL for disposition; PR-safety gate runs against the cycle's diff before public push (out of scope at the cycle altitude; v0.4.0 ships local-only).

## §7 — Out of scope (this example)

- Real implementation of an "untrusted-input handling cycle" — illustrative, not a v0.4.0 deliverable.
- Code Review running inside Outcomes-style runtime grader loops — Outcomes is API-only per `feedback_no_anthropic_api_key.md`; documented in `docs/design/odd-vs-outcomes.md`.
- CI Auto-Fix integration — separate substrate per conference research §1 #6; orthogonal to the plan-step composition pattern shown here.

## §8 — Provenance

- `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` "Compose on Claude Code review primitives" section — the SKILL guidance this example illustrates.
- `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §1 #5 + #7 + §3 — Code Review + Security Review as substrate.
- `docs/plans/v0-4-0-cycle-3-substrate-composition-routines-codereview-outcomes.md` §5 — verified-live CLI surface finding.
- `docs/release-roadmap.md` §3 v0.4.0 line 86 + AC.V040.3 — Code Review composition objective.
- `claude --help` empirical verification at HEAD `2.1.128` (2026-05-08).
