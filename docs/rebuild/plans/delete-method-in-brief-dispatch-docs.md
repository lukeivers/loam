# Amendment #18 — Delete method-in-brief dispatch docs + ODD-in-pos §7.4 update

**Amendment number:** 18
**BASELINE (pre-amendment tip):** `e8f704c` (`docs(future-ideas): capture
research-before-plan, shutdown-catch, and audit-triage CDCs`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-22.

## 1. Intent

Seven `brief.md` files live under `docs/rebuild/components/<comp>/` inside
sealed components. They served a one-time purpose at build-time — the
proposal restated for a background agent with dispatch detail (tools,
halt triggers, budget) — and were consumed when the builder picked up
the component. The components shipped and the seals landed. Per ODD §2.5
and the just-landed `research-before-plan` / `scope-only-dispatch` CDCs,
the canonical committed-artifact set going forward is
**proposal + plan + shipped code + seal**. Briefs are just-in-time
dispatch documents, produced and consumed at dispatch time, not
committed canonical artifacts.

This amendment:

1. Deletes the seven historical brief dispatch docs.
2. Rewrites `docs/odd-in-pos.md` §7.4 minimally so the narrative no
   longer frames briefs as a committed canonical artifact in the five-
   gate chain — it names them as a dispatch-time step whose output is
   not retained as a canonical artifact.

Hands-off-lifecycle rides along (BASELINE advance + SEAL_COMMIT sidecar
refresh + narrative line in `seals/SEAL_COMMIT.true-first-run`). No
functional change to any runtime module.

## 2. Files deleted (verified existence first)

All seven exist as of `e8f704c`:

1. `docs/rebuild/components/primary-persona-loader/brief.md` (214 lines)
2. `docs/rebuild/components/session-resilient-orchestrator/brief.md` (209 lines)
3. `docs/rebuild/components/graceful-degradation/brief.md` (212 lines)
4. `docs/rebuild/components/observability-aggregator/brief.md` (198 lines)
5. `docs/rebuild/components/cost-governance/brief.md` (128 lines)
6. `docs/rebuild/components/scope-of-work/brief.md` (175 lines)
7. `docs/rebuild/components/objective-tracker/brief.md` (192 lines)

Total: 1328 lines of dispatch paper, seven files, zero functional
consumers. Proposals at the same path stay — they are the canonical
contract. Every build that remains references the proposal, not the
brief.

If any brief is absent at build-time, skip that file (already deleted);
do not halt unless all seven are absent (would indicate the wrong
BASELINE).

## 3. §7.4 edit (2-4 sentence budget)

### Current text (lines 429–434 of `docs/odd-in-pos.md`)

```
### 7.4 Brief

Eve (or the proposal author) drafts the brief: the proposal restated for
a background agent, with dispatch detail added (tools, halt triggers,
budget). Objectives do not change between proposal and brief. If they do,
the proposal was wrong and should be corrected first.
```

### Proposed new text

```
### 7.4 Brief

Eve (or the proposal author) drafts the brief at dispatch time: the
proposal restated for a background agent, with dispatch detail added
(tools, halt triggers, budget). Objectives do not change between
proposal and brief. If they do, the proposal was wrong and should be
corrected first. The brief is a dispatch-time artifact — produced when a
builder is dispatched, consumed by that builder, not retained as a
committed canonical artifact. The canonical artifact set that lives in
the repo is proposal + plan + shipped code + seal. (This matches the
`scope-only-dispatch` CDC — the dispatch carries objective, scope,
constraints, halt triggers, and ODD-check; the builder's own plan under
`docs/rebuild/plans/` is the paper trail the repo keeps.)
```

Four sentences added, zero sentences deleted. §2's five-gate table
(lines 56–62) and the `research-plan → research → proposal → brief →
build` ASCII chain (line 50) remain unchanged — briefs are still a
*step*, just not a committed artifact. Bigger rewrites of §2 are out of
scope for this amendment.

## 4. Allowed-prefixes / allowed-files tuple widenings

Of the seven brief-owning components, four have a
`tests/test_no_sealed_amendments.py` seal-diff test; three (primary-
persona, scope-of-work, objective-tracker) have no seal-diff enforcement
and therefore need no tuple edits.

The four that need widening:

### 4.1 `cost-governance/tests/test_no_sealed_amendments.py`

Currently: `allowed_prefixes = ("cost-governance/", "data/",
"docs/rebuild/plans/", "hands-off-lifecycle/")`, `allowed_files = set()`.

Add to `allowed_prefixes`:
- `docs/rebuild/components/cost-governance/` (brief.md deletion lives here)

Add to `allowed_files`:
- `docs/odd-in-pos.md`

BASELINE: advance from `5c49e27` to `e8f704c`.

### 4.2 `graceful-degradation/tests/test_no_sealed_amendments.py`

Currently: `allowed_prefixes = ("graceful-degradation/", "data/")`,
`allowed_files = set()`.

Add to `allowed_prefixes`:
- `docs/rebuild/components/graceful-degradation/`
- `docs/rebuild/plans/` (plan-before-code paper trail)
- `hands-off-lifecycle/` (cross-cutting seal counterpart)

Add to `allowed_files`:
- `docs/odd-in-pos.md`

BASELINE: advance from `dab49dd` to `e8f704c`. Update the in-source
self-assertion `assert "BASELINE = \"dab49dd\"" in source` → `assert
"BASELINE = \"e8f704c\"" in source` (the pinning-pattern test references
the literal string).

### 4.3 `observability-aggregator/tests/test_no_sealed_amendments.py`

Currently: `allowed_prefixes = ("observability-aggregator/", "data/")`,
`allowed_files = set()`.

Add to `allowed_prefixes`:
- `docs/rebuild/components/observability-aggregator/`
- `docs/rebuild/plans/`
- `hands-off-lifecycle/`

Add to `allowed_files`:
- `docs/odd-in-pos.md`

BASELINE: advance from `a0906c1` to `e8f704c`. Update the in-source
self-assertion literal string accordingly.

### 4.4 `orchestrator/tests/test_no_sealed_amendments.py`

Currently: `allowed_prefixes` has `orchestrator/`, `hands-off-
lifecycle/`, `workspace-bootstrap/`, `self-upgrade/`, `memory-system/`,
`docs/rebuild/components/orchestrator-bootstrap-unification/`,
`docs/rebuild/components/namespaced-labels-and-bootout/`,
`docs/rebuild/plans/`, `data/`. `allowed_files = {"first-run-inventory.yaml"}`.

Add to `allowed_prefixes`:
- `docs/rebuild/components/session-resilient-orchestrator/` (brief.md
  deletion; session-resilient-orchestrator is this component's doc-
  slug name).

Add to `allowed_files`:
- `docs/odd-in-pos.md`

BASELINE: advance from `a3bbdcd` to `e8f704c`.

### 4.5 Components that do NOT need widening

- `primary-persona/` — no `test_no_sealed_amendments.py`, no SEAL_COMMIT
  sidecar. Brief deletion and §7.4 edit land with no seal-diff test to
  satisfy.
- `scope-of-work/` — same.
- `objective-tracker/` — same.
- `hands-off-lifecycle/` — the H19 seal-diff test allows the top-level
  `docs` prefix already (see `hands-off-lifecycle/tests/test_cross_
  cutting.py` line 262), so brief deletions under `docs/rebuild/
  components/*/` and the `docs/odd-in-pos.md` edit flow through.

### 4.6 Other sealed components (touch-check)

- `self-correction/`, `reversibility-primitive/`, `safety-layer/`,
  `telegram-interface/`, `memory-system/`, `workspace-bootstrap/` —
  these sealed components are NOT modified by this amendment. Their
  seal-diff tests still diff `BASELINE..SEAL_COMMIT`, which are both
  fixed SHAs; this amendment lands *after* their SEAL_COMMIT and does
  not edit their tuple. Their seal-diff tests remain green without any
  tuple change because this amendment's paths do not enter those
  components' diff windows.

If the test runner surfaces one of these components' seal-diff test as
red because of this amendment's diff, HALT — signals the amendment is
cross-cutting in a way not anticipated.

## 5. BASELINE advances summary

| Component | From | To |
|---|---|---|
| cost-governance | 5c49e27 | e8f704c |
| graceful-degradation | dab49dd | e8f704c |
| observability-aggregator | a0906c1 | e8f704c |
| orchestrator | a3bbdcd | e8f704c |
| hands-off-lifecycle (test_cross_cutting.py) | c94e146 | e8f704c |

Workspace-bootstrap is **not** touched by this amendment. Its BASELINE
stays at `c94e146`.

## 6. SEAL_COMMIT sidecar updates (seal commit only)

All ten sealed components' `tests/SEAL_COMMIT` sidecars get bumped to
the amendment-commit SHA in the seal commit. The eight affected
components (the 7 brief-owning + hands-off-lifecycle) also get:

- The four brief-owning components with seal-diff tests: sidecar set to
  the amendment commit.
- The three without seal-diff tests (primary-persona, scope-of-work,
  objective-tracker): no sidecar exists, nothing to bump.
- Hands-off-lifecycle: `tests/SEAL_COMMIT` bumped + narrative
  appended to `seals/SEAL_COMMIT.true-first-run` describing this
  amendment.

The other two components whose sidecars get refreshed for cross-cutting
consistency — workspace-bootstrap, memory-system, self-correction,
reversibility-primitive, safety-layer, telegram-interface — do not
strictly need refreshes for this amendment since it doesn't touch their
trees. Leave them alone (fewer touches, tighter diff).

## 7. Two-commit cycle

Per sealed-component amendment ritual (no --amend):

### Commit 1 — amendment

```
fix(primary-persona-loader, session-resilient-orchestrator, graceful-degradation, observability-aggregator, cost-governance, scope-of-work, objective-tracker, hands-off-lifecycle): delete method-in-brief dispatch docs + update ODD-in-pos §7.4 (amendment #18)
```

Body:
- Cite ODD §2.5, `research-before-plan` CDC, `scope-only-dispatch` CDC.
- List the 7 briefs deleted.
- Quote the §7.4 diff.
- List the 4 tuple widenings.
- Note the hands-off-lifecycle BASELINE advance.
- List narratively: the 3 components with no seal-diff test that need
  no tuple change.

Before committing: all listed test suites green.

### Commit 2 — seal

```
chore(seals): delete-method-in-brief-dispatch-docs seal — primary-persona-loader + session-resilient-orchestrator + graceful-degradation + observability-aggregator + cost-governance + scope-of-work + objective-tracker + hands-off-lifecycle at <amendment-sha>
```

Body:
- Bump all affected `tests/SEAL_COMMIT` sidecars to the amendment SHA.
- Append amendment-cycle narrative to `hands-off-lifecycle/seals/
  SEAL_COMMIT.true-first-run`.

## 8. Test suites that must be green

Before the amendment commit:

1. `cost-governance/` full suite.
2. `graceful-degradation/` full suite.
3. `observability-aggregator/` full suite.
4. `orchestrator/` full suite.
5. `primary-persona/` full suite.
6. `scope-of-work/` full suite.
7. `objective-tracker/` full suite.
8. `hands-off-lifecycle/` full suite.
9. All ten `test_no_sealed_amendments.py` suites (diff-scope check).

Note: `safety-layer/tests/test_no_sealed_amendments.py` is a misnamed
integration-invariants file (A15/A17/A18 checks), not a seal-diff test.
It may fail with `ModuleNotFoundError: primary_persona` if the test
environment lacks the editable install — a pre-existing environmental
issue, not caused by this amendment. Verify predates this amendment if
it fails; do NOT halt unless failure is caused by this amendment's
diff.

Before the seal commit: same suites + confirm the four seal-diff tests
still pass after SEAL_COMMIT sidecars are bumped.

## 9. Halt triggers

- A brief intended for deletion is already absent → skip, note, don't
  halt (unless all seven absent → halt, wrong BASELINE).
- §7.4 rewrite grows beyond 2-4 sentences → halt, flag (methodology
  rewrite is larger than this amendment's scope).
- An 8th component's tuple needs widening → halt, flag scope creep.
- Any test other than the misnamed safety-layer one fails → halt.

## 10. ODD compliance

No functional code changes; no new acceptance criteria introduced; no
existing criteria invalidated. This amendment is documentation-
operational hygiene, ratifying the already-in-effect CDC-driven
artifact discipline. Every deleted brief has zero runtime or test
consumer, verified by the absence of any grep match in the source
trees. The §7.4 rewrite aligns the document with the committed
operational pattern (the last seven sealed components all shipped with
the proposal + plan + code + seal set; no post-build brief was ever
re-read).
