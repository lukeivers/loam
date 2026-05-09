# Workspace corpus overrides

> **A loam workspace can override any canonical corpus file by placing a same-named file at the workspace root.** The corpus resolver probes the workspace root first and falls through to the canonical `framework/` copy only when the workspace-root file is absent. The pattern is implemented in `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py` (and duplicated in `framework/primary-persona/src/loam/primary_persona/session_start_gate.py` per the cross-component-boundary lift policy); this doc explains how to use it.

The override pattern is the no-special-flag, no-config-file way to teach the persona about your specific workspace's domain — useful when the canonical defaults assume a software-development context but your work is a different shape (legal research, household finance, household operations, journalism, music production, etc.).

---

## What this enables

The corpus resolver runs at session-start. For every canonical file (e.g. `CLAUDE.md`, `docs/VALUE_PROPOSITION.md`, `docs/STATE.md`, the on-demand pointer set), it asks: does `<workspace_root>/<file>` exist? If yes, that file is loaded into the session. If no, the resolver falls through to `<workspace_root>/framework/<file>` (the canonical-shipped copy).

This means: dropping a file at the workspace root with the same name as a canonical file shadows it. The persona reads the workspace-root version; the canonical version is silently skipped. There is no merge — the workspace-root file replaces the canonical entirely.

Three common use cases:

1. **Domain-specific persona prompt.** Replace `CLAUDE.md` with one tuned to your work (legal research persona; household-CFO persona; restaurant-ops persona; etc.). The canonical CLAUDE.md describes loam itself; a workspace whose persona is "household finance assistant for the Smith family" needs different framing.
2. **Domain-specific value proposition.** Replace `docs/VALUE_PROPOSITION.md` when the user-facing prime objective for *your* workspace is different from loam's general translation-layer framing.
3. **Domain-specific state document.** Replace `docs/STATE.md` when your workspace tracks state at a different cadence or shape (e.g. a research workspace tracking experiments, not software releases).

You can override one file or all of them. The choice is per-file, not per-workspace.

---

## How to author an override

1. Identify the canonical file you want to shadow. It will be at `framework/<relative-path>` in your workspace (e.g. `framework/CLAUDE.md`, `framework/docs/VALUE_PROPOSITION.md`).
2. Create the same path at the workspace root (e.g. `CLAUDE.md`, `docs/VALUE_PROPOSITION.md`). Put your domain-specific content there.
3. That's it. Next session-start, the persona loads your file.

There is no registration step, no config flag, no manifest entry. The resolver discovers the override structurally.

If you want to revert to the canonical, delete the workspace-root file. The resolver falls through automatically.

---

## When NOT to use overrides

The override pattern is for content you genuinely want to *replace*. It is not the right tool for:

- **Adding extra context that should compose with the canonical.** The override replaces; nothing merges. If you want to add a few sentences to the canonical CLAUDE.md, copy the canonical wholesale and append your additions — but understand you now own that copy through any future canonical updates.
- **One-off session context.** Drop one-off context into your messages or scratch files; don't override canonical for a single conversation.
- **Workspace-specific memory rules.** Memory rules live under your project's memory directory (`~/.claude/projects/<project>/memory/feedback_*.md`), not as corpus overrides. Use `loam amend new-memory <slug>` to scaffold a new memory rule.

---

## Reference example

A reference override demonstrating a non-development workspace lives at `docs/examples/corpus-overrides/household-finance-CLAUDE.md`. Copy that file to your workspace root as `CLAUDE.md` to replace the dev-mode CLAUDE.md with a household-finance persona prompt; tune the content to your specific household.

---

## Composes with

- **`loam amend new-memory <slug>`** — for workspace-specific behaviour rules (memory). Memory rules and corpus overrides are different surfaces: memory tunes how the persona learns from conversations; corpus overrides replace the persona's foundational framing documents.
- **`framework/workspace-bootstrap/`** — the onboarding ritual writes a `bootstrap.yaml` manifest at `<workspace>/.pos/bootstrap.yaml`. Manifest fields (channel preference, safety profile, language) are tuned through the onboarding flow; corpus overrides are tuned by file placement. Both surfaces compose without conflict.
- **Per-project memory** — corpus overrides change *what is loaded at session-start*; per-project memory changes *what is recalled per turn*. Both surfaces are workspace-specific; corpus overrides are the higher-trust, more-foundational surface (used sparingly).

---

## Cross-references

- Resolver implementation: `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py:_resolve_corpus_path`.
- Duplicated implementation (per cross-component-boundary lift policy): `framework/primary-persona/src/loam/primary_persona/session_start_gate.py:_resolve_corpus_path`.
- Related plan-doc: `docs/plans/corpus-inlining-session-start-hook.md` (AC.CI.5 — path-resolver fall-through).
- Related test: `framework/hands-off-lifecycle/tests/test_AC_CI_5_path_resolver_fall_through.py`.
