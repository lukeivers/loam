# v0.3.0 Cycle 7 — Release-level smoke gate + STATE.md SHIPPED rollup (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-7-release-level-smoke-gate-and-ship`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 7.
**Predecessor cycles:** Cycles 1–6 (sealed).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

v0.3.0 SHIPPED sealing event. Master plan §3 entry collapses into STATE.md §2 (or post-Cycle-1 equivalent path) with seal anchor; `docs/release-roadmap.md` updated. v0.4.0 plan-author can dispatch against a stable v0.3.0 baseline.

Cycle 7 is bookkeeping-shaped — light AI-time, but the release-ratification ceremony is load-bearing: aggregate cycle count + tests-green count + smoke verdict are named once at this surface.

## §3 — Component fence

PRIMARY: `docs/release-roadmap.md` (§3 v0.3.0 → §2 collapse).

Secondary: `docs/STATE.md` (or post-Cycle-1 equivalent path; if Cycle 1 moved STATE.md to `docs/STATE.md`, that's the path). Cycle 1's RBC migration plan determines this.

Universal admissions: master plan §11 SHA register backfill.

## §4 — AC family seed — `AC.SHIP.*`

Load-bearing concerns to be tightened at dispatch time:

- `docs/release-roadmap.md` §3 v0.3.0 entry collapses to §2 with seal SHA + apply SHA per cycle.
- STATE.md SHIPPED rollup row added — objective sentence (verbatim from §3) + seal anchor (final cycle's seal SHA).
- Aggregate cycle count = 7 named explicitly.
- Aggregate tests-green count summarized.
- Aggregate smoke verdict named.
- Master plan §11 SHA register fully backfilled.
- An outcome-altitude AC — release-roadmap §2 + STATE.md SHIPPED row + master plan §11 SHA register all resolve to the same set of seal SHAs.

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- v0.3.0 tag push — owner action separate.
- GitHub Releases marked `--latest` — owner action separate.
- Public-remote push to `lukeivers/loam` — owner action separate.
- v0.4.0 master plan authoring — happens in next planning cycle, not this one.

## §10 — F2 RF gaps to surface at dispatch

- STATE.md location post-Cycle-1 — depends on Cycle 1's path migration choice; surface to dispatch for read-from-Cycle-1-plan-doc.
- Aggregate tests-green count — methodology for counting (per-cycle test counts summed, or repo-wide `pytest` final invocation count). Surface for clarity.
- Smoke verdict format — single-sentence vs structured-table; precedent from prior STATE.md SHIPPED rows.

## §11 — Provenance trail

Master plan §3 Cycle 7; release-roadmap §3 v0.3.0 (the entry being collapsed); `docs/release-versioning-policy.md` §Tagging (tag-push policy).

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

| Decision | Choice | Rationale |
|---|---|---|
| Canonical cycle-count framing | "Seven cycles + one in-cycle audit-corrective sub-cycle (C6.1)" | Master plan §3 names 7 cycles; C6.1 was unscheduled at master-plan landing — added in-cycle to close FHA findings #1 + #2 (audit deliverable's own correctives) per AUTONOMY (recommendation IS the decision). C6.1 is not a separate cycle by master-plan ordinal but is a sealed sub-cycle in §11. F2 RF: framing as "7+C6.1" honors both — owner sees both the locked plan structure and the actual sealed-component history. |
| Aggregate tests-green count framing | Per-cycle counts named with peak-aggregate (1202 at C4) + framework-side breakdown (C6) + smoke ride-along (825 odd-extractor at HEAD `bfe55cf`) | No single repo-wide pytest invocation produces a canonical aggregate because each cycle touched a different fence; per-cycle counts are the verifiable claim per `feedback_specific_claims_verified_or_marked_guess`. Reporting C4's 1202 as the highest aggregate name + C6's framework-side 888 + smoke ride-along 825 lets reader trace each number to its source. |
| Smoke verdict format | Single sentence + structured ride-along bullets in STATE.md row | Mirrors v0.2.5.1 STATE.md narrative-paragraph precedent (single dense paragraph append; no separate table row exists in STATE.md for shipped versions). The release-roadmap §2 row separately captures objective + anchor in tabular form. |
| STATE.md row format | Append `**v0.3.0 SHIPPED YYYY-MM-DD**` paragraph to §1 narrative line, mirroring v0.2.5.1's append shape | STATE.md §1 carries the canonical SHIPPED record as one running paragraph. Adding a separate component-table row would break that precedent; the SHIPPED rollup is the dense narrative append. |
| Release-roadmap §3 collapse shape | §3 v0.3.0 entry deleted; §3 header retained as pointer to v0.4.0 in §4 (active version pointer) | Per release-roadmap §7 protocol: "When a minor ships, its §3-or-§4 entry collapses into §2 with the seal anchor." v0.3.0's §3 entry collapsed to a one-line pointer; v0.4.0's full entry remains in §4 (it has not yet been promoted to §3 active — that is v0.4.0 plan-author's responsibility). |
| C7 SHA backfill timing | Apply / Seal SHAs land in §11 + STATE.md after seal commit lands; this plan-doc commits before the seal | Standard C1–C6 pattern: source-edit → manifest → apply → seal → §14 backfill (separate commit). C7's plan-doc edits land before seal; SHAs backfilled in the §14 backfill commit per `feedback_no_amend_in_agent_dispatches`. |
| HARD HALT before public actions | Held — no `git push lukeivers/loam`, no `git tag v0.3.0`, no GitHub Release | Per Cycle 7 dispatch brief explicit halt list. Tag push + GitHub Release + remote push are owner-action-separate per `docs/release-versioning-policy.md` §Tagging. |

### Post-seal SHA register

| Commit | SHA |
|---|---|
| Source-edit doc-bundle (release-roadmap §3→§2, STATE.md SHIPPED row, master plan §11 backfill, this §14) | `7892818` |
| Manifest commit | `7a80b5a` |
| Manifest smoke_outcome trim corrective (1st) | `d44cd47` |
| Manifest smoke_outcome trim corrective (2nd; landed under 200-char limit) | `c67b27d` |
| `loam amend apply` commit | `d849aee` |
| `loam amend seal` commit | `3c6fdd5` |
| §14 SHA backfill commit (this) | (this commit) |
