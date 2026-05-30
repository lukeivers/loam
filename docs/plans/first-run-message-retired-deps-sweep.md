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
