# v0.4.0 Cycle 5 — Release-level smoke gate + STATE.md SHIPPED rollup (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-4-0-cycle-5-release-level-smoke-gate-and-ship`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-4-0-master-plan.md` §3 Cycle 5.
**Predecessor cycles:** C1 + C2 + C3 + C4 sealed.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

v0.4.0 SHIPPED sealing event. Master plan §3 entry collapses into `docs/STATE.md` SHIPPED record per release-roadmap §7 protocol; release-roadmap §3 → §2 collapse with seal anchor. Mirrors v0.3.0 Cycle 7 ceremony shape.

C5 is bookkeeping-shaped — light AI-time, but the release-ratification ceremony is load-bearing: aggregate cycle count + tests-green count + smoke verdict are named once at this surface. v0.5.0 plan-author dispatches against a stable v0.4.0 baseline only if C5 lands cleanly.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective → v0.4.0 §3 outcome (loam ships working code from extracted objectives) → C5 sealing ceremony (the ratification event that makes the SHIPPED state canonical).

## §3 — Component fence

PRIMARY: `docs/release-roadmap.md` (§3 v0.4.0 → §2 collapse).

Secondary: `docs/STATE.md` (SHIPPED narrative-paragraph append per v0.2.5.1 / v0.3.0 precedent).

Universal admissions: master plan §11 SHA register full backfill (Apply / Seal SHAs per cycle).

Read-only: all C1–C4 sealed surface.

## §4 — AC family seed `AC.SHIP-V040.*`

- `AC.SHIP-V040.1` — `docs/release-roadmap.md` §3 v0.4.0 entry collapses to §2 with seal SHA + apply SHA per cycle. Mirrors v0.3.0 collapse shape (one-line pointer; full detail moves to §2). `outcome-altitude: false`.
- `AC.SHIP-V040.2` — `docs/STATE.md` SHIPPED rollup row added — objective sentence (verbatim from §3) + seal anchor (final cycle's seal SHA). Append-paragraph shape per v0.2.5.1 / v0.3.0 precedent. `outcome-altitude: false`.
- `AC.SHIP-V040.3` — Aggregate cycle count = 5 named explicitly. `outcome-altitude: false`.
- `AC.SHIP-V040.4` — Aggregate tests-green count summarized. Per-cycle counts named with peak-aggregate (mirrors v0.3.0 C7's framing methodology). `outcome-altitude: false`.
- `AC.SHIP-V040.5` — Aggregate smoke verdict named — single sentence summarizing C1–C4 smoke outcomes. `outcome-altitude: false`.
- `AC.SHIP-V040.6` — Master plan §11 SHA register fully backfilled; release-roadmap §2 + STATE.md SHIPPED row + master plan §11 all resolve to the same set of seal SHAs. `outcome-altitude: true` (cross-source SHA consistency is the verifiable release-readiness outcome).

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- v0.4.0 tag push (`git tag v0.4.0`) — owner action separate per `docs/release-versioning-policy.md` §Tagging.
- GitHub Releases marked `--latest` — owner action separate.
- Public-remote push to `lukeivers/loam` — owner action separate.
- v0.5.0 master plan authoring — happens in next planning cycle, not C5.
- Methodology paper / arXiv preprint (harness-landscape EV.2; v0.5.0/v0.6.0 candidate; surfaced for owner ruling separate from C5).
- Public walkthrough video (harness-landscape EV.3; v0.6.0 companion candidate).
- SWE-bench Pro submission (harness-landscape RR.3; v0.4.0 successor candidate; surfaced for owner ruling).

## §10 — F2 RF gaps to surface at dispatch

- STATE.md location — confirm `docs/STATE.md` is canonical post-v0.3.0 (Cycle 1 RBC migration moved it from `docs/rebuild/STATE.md` to `docs/STATE.md`).
- Aggregate tests-green count methodology — per-cycle counts named with peak-aggregate (matches v0.3.0 C7 precedent) vs single repo-wide pytest invocation count. Per `feedback_specific_claims_verified_or_marked_guess`, per-cycle counts are the verifiable claim.
- Smoke verdict format — single-sentence summary vs structured ride-along bullets. Per v0.3.0 C7 precedent: single sentence + structured ride-along bullets in STATE.md row.
- v0.4.0 successor experiments (RR.3 SWE-bench Pro submission, EV.2 paper, EV.3 video) — surface to owner at C5 ratification time as separate ratification gates, not C5 commits.

## §11 — Provenance trail

Master plan §3 Cycle 5; release-roadmap §3 v0.4.0 (the entry being collapsed); `docs/release-versioning-policy.md` §Tagging (tag-push policy); v0.3.0 Cycle 7 (`docs/plans/v0-3-0-cycle-7-release-level-smoke-gate-and-ship.md`) for ceremony precedent.

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Method-decision record finalized at C5 plan-doc dispatch time. Mirrors v0.3.0 C7 precedent (canonical-cycle-count framing, aggregate tests-green count framing, smoke verdict format, STATE.md row format, release-roadmap §3 collapse shape, C5 SHA backfill timing, HARD HALT before public actions).

### Post-seal SHA register

| Commit | SHA |
|---|---|
| Plan-doc commit | `586a5ec3` (v0.4.0 master plan + 5 cycle stubs, 2026-05-08) |
| Source-edit commit (BASELINE) | `adf9977f` |
| Manifest commit | `5a4d94a6` |
| Manifest-trim corrective | `c072df39` |
| C2 §14 backfill (carried) | `acc26537` |
| Apply commit | `1733a7df` |
| Seal commit | `7787a226` |
| §14 backfill commit | (this commit) |
