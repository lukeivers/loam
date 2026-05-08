# Plan-doc + sub-plan + manifest YAML conventions

> **Plan-docs are the durable artefacts that bridge ODD's delegator/builder split. The plan codifies method against scope before code; the manifest YAML drives `loam amend apply` + `loam amend seal`. Each convention named here has been observed in repeated sealed amendments and is now expressed as the canonical authoring shape.**

This document is the concise codification of the plan-doc + manifest authoring conventions. The exhaustive narrative of why these conventions exist lives in `../odd-in-loam.md`. Templates for new plan-docs live at `../../../templates/plan/`.

## 1. Plan-doc shape

A plan-doc is a Markdown file at `docs/plans/<slug>.md`. Each plan has:

- **§1 Objective** — outcome-shaped, single sentence.
- **§2 Predecessors / context** — which sealed amendments this plan composes against.
- **§3 Scope** — explicit in-scope vs out-of-scope items.
- **§4 Acceptance criteria** — table of AC IDs + outcome + verification. Each AC outcome-shaped + deterministic + one-test-per-criterion.
- **§5 Sealed-component fence** — the components this amendment touches.
- **§6 Halt triggers** — conditions under which the builder stops + surfaces.
- **§7 Ship shape** — sub-amendment series shape (if applicable) + commit ladder.
- **§14 Method-decision register** — per-decision narrative, populated post-build.
- **§15 Backwards-compat verification** — what existing tests must still pass.
- **§16 Halt-and-surface findings** — what was raised + ruled at plan-authoring.

Section numbering is convention; insert section gaps where structure changes (e.g. §8-§13 reserved for risks / test scope / ladders that some plans don't need).

## 2. Sub-plan shape

When a master plan splits into sub-amendments (M1.rename's M1a..M1g, M6's M6a/M6b/M6c/M6b.0/M6b.1), each sub-amendment gets its own sub-plan at `docs/plans/<master-slug>-<suffix>.md`. The sub-plan:

- References the master plan-doc + ratifies any owner rulings already issued at master-plan time.
- Declares the sub-amendment's specific scope (subset of master's surface).
- Carries its own AC family (e.g. AC.OSS-M6b0.\* extends the master's AC.OSS-M6.\* family).
- Carries its own halt triggers + ship shape.
- Carries its own §14 register populated at sub-amendment build time.

## 3. Manifest YAML shape

A manifest at `docs/plans/<slug>.manifest.yaml` drives `loam amend apply` + `loam amend seal`. Required fields:

- `schema_version: 1`
- `amendment.number` — global counter; advances per amendment.
- `amendment.slug` — matches the plan-doc filename's stem.
- `amendment.title` — long-form descriptor (one of the most-read surfaces; concise but complete).
- `baseline:` — the SHA the seal-diff window starts at (typically the predecessor's §14 SHA-register backfill commit).
- `plan:` — relative path to the plan-doc.
- `seal_description:` — long-form narrative copied to the seal commit's body.
- `components:` — list of `{name, seal_test, sidecar, frozen_baseline, extra_allowed_prefixes}` entries.
- `universal_paths:` — `{prefixes, files}` admitted across all components per amendment #22 ruling #3.
- `narrative:` — `{target, body}` for the per-amendment seal narrative.

## 4. AC ladder-up

Every AC ladders up to the master plan's outcome ACs, which themselves ladder up to AC.PO.1 + AC.PO.2 (prime objective in `docs/VALUE_PROPOSITION.md`). Per `feedback_value_proposition_as_prime_objective` this is the required reverse-trace.

## 5. §14 method-decision register

Each plan carries §14 that's populated at build time (decisions narrated by the builder) + at seal time (commit SHAs backfilled by `loam amend seal --plan-doc`). The §14 placeholder structure mirrors the plan's D-Q.\* + D-build.\* IDs declared in §10.

## 6. Cross-references

- Long-form ODD methodology: `../odd-methodology.md`.
- Long-form loam application: `../odd-in-loam.md`.
- Plan-doc template: `../../../templates/plan/dev-discipline.md`.
- Manifest reference: `framework/tools/loam/README.md` (the canonical loam amend documentation).
- CDC corpus: `../cdcs/` (especially `plan-before-code.md` + `research-before-plan.md`).

## 7. Applied-immediately footer

This convention is applied to every sealed amendment from M6b.0 forward. Pre-M6b.0 plans were authored against the same conventions expressed by precedent; M6b.0 names + locates them.
