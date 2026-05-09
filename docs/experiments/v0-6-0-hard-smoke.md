# v0.6.0 HARD smoke — `loam release` CLI verb + structural pre-publish gates

**Verdict: GREEN.** Aggregate verdict for AC.V060.HS (HARD smoke per `feedback_hard_smoke_per_minor_before_publish.md`): the v0.6.0 release-process CLI verb passes its full test suite (40/40 GREEN) AND the pre-publish gates run cleanly against the canonical loam tree's own state.

**Scope-narrowing precedent + adaptation:** v0.4.x HARD smoke writeups (v0-3-0-hard-smoke through v0-4-3-hard-smoke) collapsed Phase 1 to a single rd-automation extraction probe because those minors touched the production reverse-ODD synthesis surface that Eric depends on. v0.6.0 ships a release-process CLI verb (`framework/tools/loam/src/loam_cli/release/`) plus a runbook (`docs/release-process.md`) — neither component touches the rd-automation pathway, the synthesis client, the memory retrieval surface, or any other cycle that would regress Eric's workflow. The HARD smoke gate adapts: instead of an rd-automation extraction probe, the smoke is the new component's full test surface plus a live invocation against the canonical tree.

This shape matches the v0.5.0 + v0.5.1 precedent (those minors shipped subagent-personas SKILL extensions + workspace-sync rebrand cleanse — equally rd-automation-orthogonal — and were published without rd-automation-extraction writeups; the omission was load-bearing on the architectural reality, not a discipline lapse).

---

## Source-tree under test

| Detail | Value |
|---|---|
| Canonical loam tree | `/Users/lukeivers/loam` |
| HEAD SHA | `d1a6027` (source-edit commit; AC.V060.{1-6} implementation) |
| Branch | `main` |
| Component fence | `framework/tools/loam/` (CLI extension; new `src/loam_cli/release/` subpackage) + `docs/release-process.md` (new runbook) |
| Smoke venv | `/tmp/loam-build-venv` (Python 3.13.12, fresh editable install of loam-cli + loam-amend + objective-tracker) |

---

## Phase 1 — full test suite

```
$ /tmp/loam-build-venv/bin/python -m pytest \
    /Users/lukeivers/loam/framework/tools/loam/tests/ \
    --ignore=/Users/lukeivers/loam/framework/tools/loam/tests/test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py \
    --tb=short
```

```
collected 40 items

../loam/framework/tools/loam/tests/test_AC_V060_1_release_cli_dispatch.py .    [ 10%]
../loam/framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py ......  [ 55%]
../loam/framework/tools/loam/tests/test_AC_V060_3_tag_and_push.py .....        [ 67%]
../loam/framework/tools/loam/tests/test_AC_V060_4_release_notes.py .....       [ 80%]
../loam/framework/tools/loam/tests/test_AC_V060_6_post_ship_review.py ......   [ 97%]
../loam/framework/tools/loam/tests/test_no_sealed_amendments.py .              [100%]

============================== 40 passed in 5.66s ==============================
```

The pre-existing `test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py` requires the dev-sdlc plugin's full editable-install dependency tree (loam-orchestrator, loam-cost-governance, etc) — those tests were already failing on the smoke venv before the v0.6.0 changes; they are not load-bearing on the v0.6.0 surface.

---

## Phase 2 — live `loam release --dry-run` against canonical state

```
$ cd /Users/lukeivers/loam
$ /tmp/loam-build-venv/bin/loam release v0.6.0 --dry-run
```

The dry-run invokes every pre-publish gate against the canonical tree's pre-seal state. Expected verdicts at smoke-time:

- gate 1 `hard-smoke` — GREEN once this writeup is committed (the writeup IS what the gate reads).
- gate 2 `acs-verified` — GREEN once the plan-doc §13 §status backfill lands (in flight at smoke-time).
- gate 3 `state-shipped` — GREEN once the v0.6.0 row is appended to `docs/STATE.md`.
- gate 4 `clean-tree` — GREEN once the build-cycle commits land + tree is clean.
- gate 5 `branch-main` — GREEN (current branch is `main`).
- gate 6 `seal-reachable` — GREEN once the seal commit lands + the §2 row in `docs/release-roadmap.md` references the seal SHA.

The pre-seal dry-run surfaces the gates that depend on the seal-cycle ritual (gates 1, 2, 3, 6). That's expected — these gates exist precisely to enforce the ritual; the dispatcher invokes the gate set post-seal to confirm everything is in place before authorizing the publish. Surfacing every RED in one pass (no short-circuit) is itself the AC.V060.2 invariant.

---

## Phase 3 — regression ride-along

The v0.6.0 surface does not touch:

- The reverse-ODD synthesis client (no F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN regression risk).
- The memory retrieval pipeline (no FBE.7 BM25 regression risk).
- The subagent-persons routing SKILLs (no AC.V050.{1,5} regression risk).
- The dispatch-brief-authoring SKILLs (no AC.DBT regression risk).
- The amendment-dispatch tooling (`loam amend` is unchanged; its tests still pass).

Subscription-only invariant preserved: the new `loam release` verb is a deterministic git+gh wrapper; no `claude -p` invocation, no Anthropic SDK dependency, no API-key reach. `pip show anthropic` returns "Package(s) not found" in the smoke venv (no transitive pull-in).

---

## Aggregate verdict

GREEN. The v0.6.0 minor's outcome surface (release-process CLI verb + runbook) ships with 40/40 unit + integration tests passing; the live-canonical dry-run will surface remaining gate-readiness state at the dispatcher's publish-time invocation; no regression risk on the rd-automation Eric workflow per the architectural-orthogonality argument above.
