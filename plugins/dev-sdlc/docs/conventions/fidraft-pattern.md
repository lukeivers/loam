# FIDRAFT pattern — no-overhead capture for future ideas

> **`FUTURE_IDEAS_DRAFT.md` is the no-overhead capture surface for every improvement idea about pos-v2 — the owner's, agents', or anyone's. Ideas land at point-of-occurrence. Daily rigor reviews graduate the keepers. Agents surface ideas to chat; the parent appends. The full Idea numbering + structure of `FUTURE_IDEAS.md` is reserved for graduated ideas; FIDRAFT is a draft surface so the act of capture has zero overhead.**

This document is the concise codification of the FIDRAFT pattern. The exhaustive history of why this pattern exists lives in commit narratives + amendment seal files for amendments that introduced specific FIDRAFT mechanics.

## 1. The two surfaces

- **`docs/FUTURE_IDEAS_DRAFT.md`** — workspace-side draft surface. Bullet-list of ideas captured at point-of-occurrence. Each bullet:
  - Names a concrete improvement / observation / follow-up.
  - Carries a date stamp.
  - Carries the originating session / agent / source.
  - Is short — a paragraph or two; no Idea numbering; no formal structure.

- **`docs/FUTURE_IDEAS.md`** — graduated catalogue. Each entry has a numbered Idea identifier (`Idea N`) + structured shape (rationale + sequencing + sub-features + status). Ideas graduate from the draft when they prove durable + earn a structural slot.

## 2. The capture mechanic

- **Point-of-occurrence.** When an improvement idea surfaces during a session, agent dispatch, or audit, the idea lands in FIDRAFT immediately. No structural authoring overhead.
- **Agents surface; parents append.** A dispatched agent that observes an FIDRAFT-worthy idea SURFACES it in its summary report. The parent session appends the bullet to FIDRAFT (the parent has authority on the workspace's primary tree; agents have authority on their dispatched subtree).
- **Multiple drafts allowed.** During a long session, the FIDRAFT surface may accumulate dozens of bullets. That's expected — each is preserved until daily review.

## 3. The graduation mechanic

- **Daily rigor reviews.** The owner (or a scheduled review session) walks FIDRAFT, classifying each bullet as: (a) graduate to numbered Idea, (b) defer to a future review, (c) retire (no longer relevant), (d) merge into an existing Idea.
- **Graduation is structural.** A graduated idea gets a numbered slot in `FUTURE_IDEAS.md`, a rationale section, and a sequencing note (relative to other Ideas). The graduation commit removes the bullet from FIDRAFT.
- **Retirement leaves a gravestone.** Retired bullets are removed from FIDRAFT but the retirement reason is captured in the commit message (so a future search for the bullet's terms surfaces the retirement narrative).

## 4. Cross-references

- `FUTURE_IDEAS_DRAFT.md` itself — the live draft surface (STAYS at canonical; not migrated by M6b.0).
- `FUTURE_IDEAS.md` — the graduated catalogue (STAYS at canonical; pre-M6b.0 hosted the dev-CDC corpus, which migrated to `../cdcs/`).
- CDC corpus: `../cdcs/` (especially `plan-before-code.md` — graduated FIDRAFT entries that became sealed conventions live there).

## 5. Applied-immediately footer

This pattern is the canonical capture mechanism for pos-v2 dev-discipline ideas from 2026-04-22 forward. The pattern is what the plugin teaches; the actual `FUTURE_IDEAS_DRAFT.md` instance lives at canonical loam's project tree.
