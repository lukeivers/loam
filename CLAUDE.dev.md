# pOS v2 — CLAUDE.dev.md (dev-extension fragment)

This file is the **dev-extension** of `CLAUDE.md` for the pOS v2
codebase. It loads only in DEV MODE workspaces (sub-plan B's
SessionStart mechanism delivers this fragment as `additionalContext`
when the workspace is classified `pos-v2-dev`). NORMAL USE workspaces
never see this content.

The partition that drives the user-vs-dev split is declared in
`docs/rebuild/dev-mode-manifest.yaml` (sub-plan F).

---

## Session-start discipline

Before acting on any non-trivial pos-v2 work — planning, proposing,
editing code, dispatching agents, ruling on designs — read:

- `docs/odd-llm-grounding.lean.md` (load FIRST for any ODD-shaped task —
  extraction, ratification, plan-authoring, AC-tightening, gap-analysis;
  hold §altitudes + §drift-modes + §self-checks in working memory; run
  §self-checks on every output declared "objective," "AC," "constraint,"
  or "capability"). Verbose derivation at
  `docs/odd-llm-grounding-derivation.md` is read on-demand for depth.
- `plugins/dev-sdlc/docs/odd-methodology.md` (normative; this governs)
- `plugins/dev-sdlc/docs/odd-in-loam.md` (worked examples)
- `docs/rebuild/VALUE_PROPOSITION.md`
- `docs/rebuild/STATE.md`
- `docs/duration-estimation-rubric.md` (AI-build wall-time estimation rubric)
- `docs/rebuild/FUTURE_IDEAS.md` (CDCs live here; they apply to every build)
- Any `docs/rebuild/plans/amendment-*.md` whose amendment is in-flight

Component-scoped work additionally reads that component's
`docs/rebuild/components/<name>/` artefacts (proposal, research,
seal narrative) before editing or proposing.

Proceeding without those loaded is how past sessions produced
ODD-violating proposals, misnamed mechanics, and work that had to
be thrown out. Purely conversational / informational turns do not
require the read. If in doubt, read.

### Operational cautions (distilled from observed failure modes)

- §2.5 applies to proposals I author, not only to code I review. Before
  scoping anything as a sealed-component amendment, name the specific
  spec objective (v1.0/v1.1/v1.2) the code will satisfy. If I can't
  name one, the work is dev-discipline (CLAUDE.md, docs, CDCs, tools/),
  not a sealed-component cycle.
- Memory content points at answers; it is not itself the answer. When
  a memory seems to explain an unexpected observation, verify
  empirically before acting on the explanation.
- Delegate production work (generating output someone else consumes);
  read myself when the purpose is to inform my own judgment.
- When a task is deleted or redirected, walk its dependency graph and
  re-examine dependents before dispatching any of them.

---

## Where dev-mode guidance lives

- `plugins/dev-sdlc/docs/odd-methodology.md` — the ODD methodology itself.
- `plugins/dev-sdlc/docs/odd-in-loam.md` — ODD applied to pOS v2 specifically, including
  worked examples.
- `docs/rebuild/FUTURE_IDEAS.md` — future ideas (including the Dev/SDLC
  plugin at Idea 3) and the currently-parked dev CDCs. The CDCs are
  temporary residents of that file; when the Dev/SDLC plugin lands, they
  migrate there.
- `docs/rebuild/FUTURE_IDEAS_DRAFT.md` — no-overhead capture surface for
  improvement ideas (companion to FUTURE_IDEAS.md). Every improvement
  idea (Luke's or assistant's) lands here at point-of-occurrence; daily
  rigor (post-initial-phase) reviews and graduates entries to
  FUTURE_IDEAS.md or drops them. Agents surface to chat; parent appends.
- `docs/rebuild/plans/` — per-amendment and per-scope plan docs
  (plan-before-code artefacts).
- `docs/rebuild/components/` — proposal + seal narratives per sealed
  component.
- `docs/rebuild/dev-mode-manifest.yaml` — the user-vs-dev auto-load
  partition (sub-plan F). `tools/loam-mode/` parses + audits it.
- `tools/pos-amend/` — amendment-dispatch tooling. The `pos-amend` CLI
  mechanises sealed-component amendment-cycle bookkeeping (BASELINE
  advances, allowed_prefixes/allowed_files widening, SEAL_COMMIT sidecar
  bumps, narrative appends) driven by a per-amendment YAML manifest
  committed alongside the plan doc. Per the pos-amend convention
  (amendment #22), `pos-amend apply --dry-run` green is a hard
  prereq for amendment commits.

---

## Lens enforcement timing (dev-mode reminder)

The three design lenses (Lens 1 — Claude-leverage-first; Lens 2 —
harness + primary-persona value; Lens 3 — ODD authoring) are captured
as design principles in the always-loaded `CLAUDE.md`. The execution
programme to *mechanically enforce* them in future research plans
(see `docs/rebuild/FUTURE_IDEAS.md` Idea 1) does not start until the
new pOS v2 copy is being tested in a live evaluation workspace. Until
enforcement lands, feature authors apply the lenses by discipline;
once enforcement lands, a research plan missing an answer to any lens
fails its gate.
