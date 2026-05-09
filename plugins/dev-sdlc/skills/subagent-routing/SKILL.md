---
description: "When the persona is about to dispatch a Task / Agent in a loam dev-mode workspace, recommend the typed `subagent_type: <persona>` that matches the work-shape (build / plan-author / research / review / document) instead of defaulting to `general-purpose` + a hand-rolled priming block. The 5 v0.1.7 personas (loam-builder / loam-plan-author / loam-researcher / loam-reviewer / loam-documenter) each carry the discipline a hand-rolled brief would re-derive; routing through the typed surface lets the brief omit per-cycle re-assertion of that discipline (per `dispatch-brief-authoring` SKILL extension). Use whenever authoring a dispatch brief for any non-trivial sub-task agent."
---

# subagent-routing

The v0.1.7 subagent-personas at `plugins/dev-sdlc/agents/loam-{builder,plan-author,researcher,reviewer,documenter}.md` ship as the tool-restricted, identity-anchored substrate the primary persona dispatches into. The `dispatch-brief-authoring` SKILL (v0.2.2) ships the structural brief shape that any dispatch carries. **What's missing — until this SKILL — is the routing recommendation: which `subagent_type` to pick when authoring a brief.** Today's default is `general-purpose` + a hand-rolled priming block; the typed personas are unused at the production dispatch surface (verified empirically by the v0.4.4 dispatch-site audit at `workspace/.scratch/claude-output/v0-4-4-dispatch-site-audit.md` — 0/13 audited dispatches used `subagent_type: loam-*`).

This SKILL recommends the typed surface. It carries the work-shape → persona rubric, the fall-back-to-general-purpose clause for boundary cases, and the cross-references to `personas-methodology.md` (the rubric authority) + `dispatch-brief-authoring` SKILL (the brief-extension that compresses the brief when typed).

## What this skill captures

The dispatch-time routing rubric, applied at brief-authoring time:

1. **Work-shape classification** — what is the dispatched agent doing?
2. **Persona match** — which v0.1.7 persona's `When to invoke me` section names this work-shape?
3. **Boundary check** — does the work cross persona boundaries (e.g., audit + corrective build in one cycle)?
4. **Tool-surface fit** — does the persona's tool restriction (researcher: read-only; reviewer: read-only-with-git) cover the agent's needs?
5. **Brief-shape implication** — typed dispatch unlocks the brief-extension's omission of the propagated-principle block for principles the persona body carries (per `dispatch-brief-authoring` SKILL §"When subagent_type is not general-purpose").

## The work-shape → persona rubric

Default mappings. Each row's recommendation is the typed `subagent_type` to declare in the Task tool's parameters. Fall-back to `general-purpose` only when the boundary/tool-surface checks below fail.

| Work-shape | Recommended `subagent_type` | Persona's `When to invoke me` anchor |
|---|---|---|
| Sealed-component amendment cycle (source edits + tests + `loam amend apply` + `loam amend seal`) | `loam-builder` | "A sub-plan-doc + manifest exist and the cycle's source edits + tests are ready to author." |
| Authoring a sub-plan-doc + manifest BEFORE a build dispatch (the plan-before-code gate) | `loam-plan-author` | "A new amendment cycle is being authored and needs a plan-doc + manifest." |
| Investigating a question against the codebase / web / feedback-memory corpus to produce a research artefact (no source edits) | `loam-researcher` | "A question needs investigation BEFORE a plan can be authored." |
| Gate-reviewing a sealed amendment cycle (verify ODD §2.5, fence-diff cleanliness, AC-test mapping, halt-and-surface fluency) | `loam-reviewer` | "An amendment cycle has sealed and the next cycle needs a clean gate before starting." |
| Authoring or revising public-facing documentation (README / getting-started / public-API docs / CHANGELOG / positioning copy) | `loam-documenter` | "A README needs revision because a feature changed or a positioning audit named a gap." |
| Single-tool-call in-session work the persona handles itself | (skip the dispatch entirely; no Task tool needed) | n/a |
| Anything else not covered above | `general-purpose` | (no typed persona claims this work-shape) |

The mapping is the same one `personas-methodology.md` §5 + each persona's `When to invoke me` section define. This SKILL is the operational shortcut: brief-authoring time, not requiring the dispatcher to re-walk those sections every cycle.

## When to fall back to `general-purpose`

A typed-persona match is the default when the work-shape rubric returns one. Fall back to `general-purpose` only when one of these boundary conditions fires:

1. **Cross-persona work in a single dispatch.** If the dispatch needs to (a) author a plan-doc AND (b) build the cycle in the same agent invocation, no single typed persona claims the work; default to `general-purpose`. The cleaner alternative is to split the work into two dispatches with typed personas; dispatcher's call.
2. **Tool-surface mismatch.** If the work-shape matches a persona but the persona's tool restriction blocks needed tools (e.g., the work is research-shaped but needs Edit / Write to materialise the artefact in a path the researcher can't write), default to `general-purpose`. The persona body's own `Out of scope` section names this fallback for itself (see `loam-researcher` last paragraph: "If the dispatcher needs a research artefact written to disk and I don't have Write, the dispatcher's path is to ... invoke me for the investigation and then have the persona-side caller write the artefact themselves.").
3. **Persona-constraint override needed.** If the dispatcher needs the agent to override a persona constraint (e.g., builder needs to revise an AC mid-cycle, which `loam-builder` `Out of scope` explicitly forbids), default to `general-purpose` and document the override-rationale in the brief. Surface to the dispatcher's owner if the override is non-trivial — the persona constraint exists for a reason.
4. **Work-shape genuinely doesn't match any persona.** Some dispatches (cross-component reconciliation, novel investigation that mixes research + edits, exploratory tooling) don't map to any of the 5. Default to `general-purpose`. Capture the recurring shape as a FIDRAFT entry if it dispatches ≥3 times — a 6th persona may be warranted (walk `personas-methodology.md` §5 rubric before proposing).

The fall-back to `general-purpose` is NEVER the wrong call when one of these conditions fires; the wrong call is forcing a typed persona where the work-shape doesn't fit.

## How the persona applies it

At dispatch-brief authoring time (`dispatch-brief-authoring` SKILL is also loading):

1. **Classify the work-shape.** What is the dispatched agent producing? An amendment seal? A plan-doc? A research artefact? A gate-review verdict? A README revision?
2. **Look up the rubric row.** Above. If a typed persona matches, that's the default `subagent_type` for this dispatch.
3. **Run the fall-back checks.** Cross-persona work / tool-surface mismatch / persona-constraint override / no-match. Any "yes" → fall back to `general-purpose`.
4. **Author the brief with the chosen `subagent_type`.** When `subagent_type != general-purpose`, the `dispatch-brief-authoring` SKILL's §"When subagent_type is not general-purpose" extension applies — the brief MAY omit the AC.DBT principles the persona body carries (the extension SKILL ships the per-persona table). When `subagent_type == general-purpose`, the brief MUST carry the full AC.DBT.1–6 propagated-principle block (preserved backward-compat).
5. **Verify the chosen persona's `When to invoke me` section names this work-shape.** A two-second sanity check: open the persona file, read the 5–10 line section, confirm the trigger shape matches. The personas list explicit "Do NOT invoke me for" shapes; if the dispatch matches a "Do NOT invoke me for" line, the routing is wrong.
6. **Pass the chosen `subagent_type` to the Task tool literal.** Anthropic's Task tool routes by the literal handle (`loam-builder` / `loam-plan-author` / etc.); the persona file at `<workspace>/.claude/agents/<handle>.md` (symlink to the canonical `plugins/dev-sdlc/agents/<handle>.md`) is loaded at dispatch start.

## Graceful degradation

When raw Claude Code without loam:

- The 5 v0.1.7 personas don't exist in the workspace; routing rubric collapses to "default to `general-purpose`."
- The same brief-shape rules from `dispatch-brief-authoring` apply; the propagated-principle block is preserved unconditionally.
- For non-loam projects, substitute the work-shape rubric with whatever role-shape conventions the project uses (e.g., a custom `code-reviewer` agent for review work). The principle — route to a typed agent when one matches the work-shape; fall back to general-purpose for boundary cases — is the universal contract.

## Composition

- **`personas-methodology.md` §1–§9** — the rubric authority. This SKILL is the operational shortcut for brief-authoring time; the methodology doc is the rubric for proposing new personas, retiring existing ones, and resolving boundary cases. When the boundary check is non-trivial, walk the methodology doc.
- **`dispatch-brief-authoring` SKILL** — composes tightly. The brief-extension §"When subagent_type is not general-purpose" instructs which AC.DBT principles MAY be omitted from the brief when typed. Routing decision is upstream of brief-shape decision.
- **`plugins/dev-sdlc/agents/loam-{builder,plan-author,researcher,reviewer,documenter}.md`** — the 5 typed-persona files. Each ships its own `When to invoke me` and `Do NOT invoke me for` sections; the rubric above is consistent with those sections.
- **`plan-before-code-author` SKILL** — when the routing chooses `loam-plan-author`, the plan-before-code workflow is the persona's primary shape; the brief authors the dispatch against the plan-doc the planner will create.
- **`loam-amend-cycle` SKILL** — when the routing chooses `loam-builder`, the amendment-cycle ladder is the persona's primary shape; the brief references the cycle ladder.
- **`feedback_agent_prompts_scope_only`** — the scope-only-no-method dispatch principle is preserved regardless of routing. Typed dispatches still carry scope-only direction; the persona's identity body handles the method.
- **`feedback_subagent_odd_violation_halt`** — typed dispatches still surface ODD §2.5 violations they discover (the typed personas all carry halt-and-surface explicitly).

## Out of scope

- **Authoring a 6th persona.** This SKILL recommends within the existing 5; new persona proposals walk `personas-methodology.md` §5 rubric. Captured as the methodology's existing surface, not this SKILL's.
- **Per-language sub-builder personas (`loam-builder-python` / `loam-builder-typescript`).** Already analysed at `personas-methodology.md` §6; recommendation was extend `loam-builder` with a language-adapter SKILL bundle, not new sub-personas. Out of scope for this SKILL.
- **Hard enforcement of routing (a hook that REJECTS a Task dispatch with `general-purpose` when work-shape matches a typed persona).** This SKILL is SOFT enforcement (recommends; dispatcher rules); HARD enforcement is v0.7.0 META-FRAMEWORK structural-enforcement substrate work. Captured as FIDRAFT entry "subagent-routing structural-enforcement hook" — activation gate v0.7.0.
- **Per-persona model selection / tool-tier extension.** Each v0.1.7 persona declares `model: inherit`; tool surfaces are set at v0.1.7 (researcher read-only; reviewer read-only-with-git). Adjusting either is a v0.1.7-persona amendment, not this SKILL.
- **The brief-shape itself.** That's `dispatch-brief-authoring` SKILL. This SKILL is upstream — chooses the `subagent_type`; the brief-shape SKILL authors the brief body conditioned on that choice.
