# first-run message — retired-deps accuracy sweep (v0.14.0 sub-fix)

**Slug:** `first-run-message-retired-deps-sweep`
**Class:** PATCH (defect closure — user-visible factual correction).
**Rides into:** v0.14.0 (MINOR) as a named sub-fix; user-visible subset of task #19.
**Working directory:** `/Users/lukeivers/loam` (canonical loam).
**Authoring date:** 2026-05-29.

---

## 1. Objective

A fresh user, on first run, is told the install pulls **graphiti-core,
neo4j, and kuzu**. That dependency set was **RETIRED at v0.1.0**
(AC.MFBM.7 — file-based memory is the v0.1.0 default substrate; the
graphiti-service launchd plist + dedicated venv + Kuzu/Ollama
provisioning dropped). The message tells a factual lie about what the
install does. It is user-visible and would ship in the v0.14.0 publish.

Objective: the first-run fresh-start message states current install
reality — file-based memory, **no** graphiti / neo4j / kuzu — so a
fresh user is not told heavy deps install that no longer install.

## 2. Evidence (Tier-0)

- `framework/hands-off-lifecycle/hooks/first_run_dispatch.py:102` —
  `_msg_fresh_start` returns text claiming "the memory-system component
  alone pulls graphiti-core, neo4j, and kuzu — slow on a cold pip
  cache." This is the live, shipping, user-visible string.
- `framework/first-run-inventory.yaml:60-72` — AC.MFBM.7 comment
  confirms the graphiti/neo4j/kuzu memory-system retired at v0.1.0;
  `dedicated_venvs:` is empty; file-based memory
  (`primary_persona/file_memory.py`) is the default substrate.
  (This comment is accurate documentation, not a user-visible lie — it
  is NOT edited by this cycle.)
- `docs/design/publish-assessment-2026-05-29.md` §5 B1 — names this as
  the user-visible publish blocker.

## 3. Halt-and-surface (before build)

- WD must be `/Users/lukeivers/loam`. Halt on drift.
- BASELINE candidate = current loam HEAD `f23deda` (pre-build tip),
  re-confirmed + advanced to the source-edit commit at apply (per the
  #149/KP0 BASELINE pattern). Last sealed amendment = **#154** at
  `4b258218`; this is amendment **#155**.
- Out-of-fence drift discovered mid-edit → halt and surface.

## 4. Fence (single-component)

- **hands-off-lifecycle** — `_msg_fresh_start` text lives here; the
  source edit + its test land here.
  - seal-test: `framework/hands-off-lifecycle/tests/test_cross_cutting.py`
  - sidecar: `framework/hands-off-lifecycle/tests/SEAL_COMMIT`
  - frozen_baseline: true (H19, pinned at project-start per amendment #23)
- Universal admissions: `docs/plans/`, `docs/STATE.md`,
  `docs/release-roadmap.md` (backfill), and standard universal files.

## 5. Acceptance criteria

New AC family **AC.FRMSG** (first-run message accuracy):

- **AC.FRMSG.1** — the fresh-start first-run message contains NO
  reference to `graphiti`, `neo4j`, or `kuzu` (case-insensitive). The
  retired-dependency claim is gone.
- **AC.FRMSG.2** — the fresh-start first-run message states the current
  install reality: it names that memory is **file-based** and that no
  external memory store / heavy memory deps are pulled. The user reads
  an accurate description of what installs.
- **AC.FRMSG.S** (outcome-altitude, `outcome-altitude: true`) — invoking
  the production message-builder entry point `_msg_fresh_start(log,
  helper_version)` with no pre-arranged state returns text that (a)
  contains no retired-dep name and (b) names file-based memory — i.e.
  the actual string a fresh user sees is accurate. No fixture-seeded
  message; the real production function is called.

Out of AC scope (surfaced, NOT fixed this cycle): the `pos-v2`
product-name residue in `_msg_fresh_start` and the other first-run
messages. That is the broader task-#19 rename and is NOT the
user-visible *false-dependency* blocker the publish assessment named.
Folding it in would extend scope past the named blocker. Surfaced per
Lens 7; left for a separate task-#19 cycle.

## 6. Build steps (order)

1. Edit `_msg_fresh_start` in `first_run_dispatch.py:96-111`: replace
   the graphiti/neo4j/kuzu sentence with an accurate file-based-memory
   description. Preserve the rest of the message shape (timing guidance,
   live-progress log path, close-and-reopen instruction). Keep the
   `pos-v2` name untouched (out of this fence's scope).
2. Author `test_AC_FRMSG_first_run_message_retired_deps.py` in
   `framework/hands-off-lifecycle/tests/` — parametrized over the three
   ACs (FRMSG.1 / FRMSG.2 / FRMSG.S), importing `first_run_dispatch`
   from the hooks dir via the established `sys.path` shim.
3. Run touched tests: `pytest framework/hands-off-lifecycle/tests/test_AC_FRMSG_*.py`.
4. `loam amend validate <manifest>`.
5. `loam amend apply <manifest>`.
6. `loam amend seal <manifest>`.
7. Re-grep the first-run path for any user-visible graphiti/neo4j/kuzu
   string; confirm none remains.
8. Backfill STATE.md + roadmap + register with apply + seal SHAs.

## 7. Out of scope

- The `pos-v2` → `loam` product-name rename in first-run messages
  (task #19 proper; separate cycle).
- The inventory-comment text (accurate documentation, not user-visible).
- Any non-first-run graphiti reference (tests asserting retirement;
  archive/seal records — intentional).

## 8. In-flight halt triggers

- Seal-test (`test_cross_cutting.py`) fails for reasons unrelated to
  this edit → a pre-existing fence breach surfaced → halt + surface.
- Any surrounding-code ODD violation surfaces → halt + surface.
- 5-hour wall-clock ceiling.

# first-run message — retired-deps accuracy sweep — apply ladder

2026-05-29. PATCH-class defect closure (user-visible factual
correction), riding into v0.14.0 as a named sub-fix; the
user-visible subset of task #19. Per
`docs/plans/first-run-message-retired-deps-sweep.md`.

Scope: the fresh-start first-run message
(`first_run_dispatch.py:_msg_fresh_start`) told a fresh user the
install "pulls graphiti-core, neo4j, and kuzu." That dependency set
RETIRED at v0.1.0 (AC.MFBM.7 — file-based memory is the default
substrate). The message lied about what installs. This cycle
replaces the retired-dep sentence with an accurate file-based-memory
description and proves it via AC.FRMSG.

AC families:
  - AC.FRMSG.1 — no graphiti/neo4j/kuzu reference in the fresh-start
    message (the retired-dependency claim is gone).
  - AC.FRMSG.2 — the message states current install reality
    (file-based memory; no external memory store / heavy memory
    deps).
  - AC.FRMSG.S — outcome-altitude: the production message-builder
    `_msg_fresh_start(log, helper_version)`, called with no
    pre-arranged state, returns accurate text (no retired-dep name;
    names file-based memory).

Method-level choices (builder's call per ODD §1.1):
  - The exact replacement wording for the file-based-memory sentence.
  - The test layout (one parametrized AC.FRMSG file).

Out of scope (surfaced, NOT fixed): the `pos-v2` product-name
residue in the first-run messages (task #19 proper, separate cycle);
the inventory-comment text (accurate documentation, not
user-visible); non-first-run graphiti references (intentional —
retirement assertions, archive/seal records).

Predecessor commits:
  - 4b258218 — last sealed amendment (#154) seal.
  - f23deda  — current loam HEAD (#154 STATE backfill tip).

BASELINE f23deda — re-confirm + advance to the source-edit commit
at apply. Single-component fence on hands-off-lifecycle.

## 14. Method-decision record

Amendment **#155** — first-run-message-retired-deps-sweep.
Single-component fence on **hands-off-lifecycle**. BASELINE
advanced f23deda → 2a019c3 (the D.1 re-baseline corrective; new
sidecar value).

Method-level choices (builder's call per ODD §1.1):
  - Replacement wording: the retired-dep sentence
    (graphiti-core / neo4j / kuzu) was replaced with an accurate
    file-based-memory description; no external memory store / heavy
    memory deps named.
  - Test layout: one parametrized AC.FRMSG file
    (`test_AC_FRMSG_first_run_message_retired_deps.py`) over
    AC.FRMSG.{1,2,S}.

In-flight finding (F2, surfaced + ruled at seal): the
hands-off-lifecycle full-sweep at seal surfaced a pre-existing
stale-RED D.1 byte-content frozen hash for
`framework/primary-persona/src/loam/primary_persona/cli.py`. cli.py
was legitimately content-edited by amendment **#154** (FBM Cycle 1
fix-write-path, sealed `fd5fe6a`); #154 sealed on the
primary-persona fence and never ran this hands-off-lifecycle D.1
test, so the frozen SHA (`8c128307…`) went stale-RED at HEAD
`f23deda` — NOT introduced by #155. Blast radius = 1 of 16 samples;
the git-mv-corruption guard stayed intact for the other 15. Ruled
YES (in-fence ODD §4 in-band retire-and-rebaseline per the test's
own docstring direction for intentionally-edited files): re-baseline
`8c128307…` → `260c580308bc0a3bc4a53e2608d88b8912e607c696e8e2105e131f2df5920ac0`
(the recomputed sha256 of the sealed cli.py) as a NEW corrective
commit. The §14 SHA subsection below was authored by hand because the
plan-doc carried no `## 14.` heading at seal-time (the seal's
`--plan-doc` finalize HALTed on plan-doc-missing-section-14; the seal
commit itself landed clean).

### Commit SHAs

- plan + manifest:   `2a15c4d`
- source edit:       `2edf2f4`
- apply:             `71215e1`
- D.1 re-baseline corrective (in-fence, #154-edit driven): `2a019c3`
- seal:              `e0ff5bd`
