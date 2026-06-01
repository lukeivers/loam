# foundation-polish-cluster-skill-triage — apply ladder

2026-06-01. Sealed-component PATCH amendment — foundation-polish
cluster SUB-ITEM 4 (skill triage, REMAINING scope only). The
autonomous, kernel-independent ride-along of the cluster; does
NOT gate 1a/1b/3 and is not gated by them (cluster plan §6
gating sequence).

Plan: `docs/plans/foundation-polish-cluster.md` (§5 AC.SKTRI.*,
§6 step 4 build shape, §10 item 5 scope fence, §15
backwards-compat).

Scope (per cluster plan §2 / §5 / §10 item 5): single-component
fence on `plugins/loam-skills/` — the two new AC tests
(test_AC_SKTRI_1_triggers_fire_on_intended_shape.py,
test_AC_SKTRI_2_dead_skills_retired.py). Universal admissions:
`docs/plans/` (this plan-doc + manifest + sealed narrative) +
`docs/STATE.md` + `docs/plans/loam-roadmap.md` (the §5b skill-
triage row-move at bookkeeping).

Single-cycle, single-seal ladder.

AC families (full text in cluster plan §5):
  - AC.SKTRI.1 — each retained skill's trigger fires on its
    intended NL shape (deterministic trigger-match against a
    representative-phrasing table mirroring the installed
    surface) OR the skill is removed.
  - AC.SKTRI.2 — dead skills (no working trigger / superseded /
    non-functional) are removed with the removal recorded;
    verified EMPTY on evidence + the live-set invariant enforced
    (every retained skill has >=1 live consumer — the §15
    no-live-consumer gate).

Triage outcome: all 22 installed skills verified-KEPT; zero
retirements (each carries a firing trigger + >=3 live consumers;
none superseded; none non-functional). The installed surface is
already the live set — not an accreting graveyard.

Method-level choices (builder's call per ODD §1.1):
  - D-SKTRI.MATCH — deterministic discriminating-token overlap
    (no live LLM probe; composes on the AC.SKILLCAP substring-
    trigger-match pattern).
  - D-SKTRI.TABLE — phrasing table asserted to exactly mirror
    the installed surface (drift is a failure).
  - D-SKTRI.CONSUMER — git-grep live-consumer scan = the §15
    no-live-consumer gate.
  - D-SKTRI.RETIRE-NONE — zero retirements (evidence does not
    justify any removal).

Halt triggers (cluster plan §8 / §10 item 5): none fired;
stayed in REMAINING scope (verify-triggers + retire-dead); no
ecosystem re-architecture; no adoption-loop work; zero
retirements so no live-consumer breakage.

Predecessor commit:
  - 19a14b91 — foundation-polish-cluster-install (1a) seal
    commit; THIS branch's HEAD + this amendment's BASELINE.

BASELINE — 19a14b91 (canonical-clean pre-this-amendment HEAD of
plan/foundation-polish-skill-triage). Single-component fence on
`plugins/loam-skills/`. Sidecar advances to this amendment's seal
SHA at apply time.
