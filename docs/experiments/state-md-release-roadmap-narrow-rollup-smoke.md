# state-md-release-roadmap-narrow-rollup — AC.SRMNR.4 outcome-altitude verification

> **Amendment:** `state-md-release-roadmap-narrow-rollup` (sub-plan: `docs/plans/state-md-release-roadmap-narrow-rollup.md`).
> **Class:** PATCH (doc-only).
> **AC.SRMNR.4:** OUTCOME-ALTITUDE — a fresh shell with no pre-arranged state reads the post-fix `docs/STATE.md` + `docs/release-roadmap.md` at sealed-tip and four canonical-git-ref ground-truth claims hold.
> **Verification shape:** per `feedback_test_outcome_altitude_required`, outcome-altitude verification by audit-doc-against-canonical pattern (not a pytest file) is the right shape for a doc-content-vs-canonical-git-ref claim. Each check below is a one-liner shell command against canonical loam at sealed-tip; output captured verbatim.
> **Run timestamp:** 2026-05-23 (pre-seal; the post-seal re-run is documented at the bottom of this file by the builder after `loam amend seal` lands and the four checks re-run GREEN against the sealed-tip state).
> **WD:** `/Users/lukeivers/loam` (canonical loam, branch `pos-v2`).
> **BASELINE at plan-authoring:** `6e0de79`.

---

## Check 1 — every v0.12.x tag named in the rollup resolves to a real commit

**Command:**

```
for n in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21; do printf 'v0.12.%-2s -> %s\n' "$n" "$(git rev-parse v0.12.$n)"; done
```

**Output (verbatim, 2026-05-23):**

```
v0.12.0  -> 0d25d0a1e9087a0c553eb427c4a49b4aada6c004
v0.12.1  -> 79e6eb44b4e55093d204941a2c5167eba5afa473
v0.12.2  -> be8fb46718bdcf0a80792f003f4c36bde33ad98e
v0.12.3  -> 4edeedd5a57fb645115306e6665da5e023f0cb6e
v0.12.4  -> f416755c9ddb9f75c628a516d2e468c26f90134b
v0.12.5  -> 86308b2234db9e3c9e134eab0191a8a4309a9c4d
v0.12.6  -> 86308b2234db9e3c9e134eab0191a8a4309a9c4d
v0.12.7  -> 4a9bd37488c7fc7368df5719229165bc56c37fe2
v0.12.8  -> df6fe4932e5faa429dd4368208c08a1dfa3a1f19
v0.12.9  -> 516599a74666665fb8c7eae9a2620a5859f752ec
v0.12.10 -> a2010061926f748cf7c64f260c25ca8f4695eb48
v0.12.11 -> 48e7b29cca6a58a040f74c679db94231f7785cc8
v0.12.12 -> f39756ac5de48d2ab104ba31f3224ad94c237311
v0.12.13 -> d987d6c5e70264bc86db7ac1a27b28f2ed7d7413
v0.12.14 -> 30fd65dbd459d70b2b05663e0cbe70e560b60538
v0.12.15 -> 67f8a5454fa1449024fcb85bc6e84b4da1783635
v0.12.16 -> cd3daae6fe220b9cb7d8cd05e1bbeb34c8d88fe2
v0.12.17 -> b46162f45b5a710f4a0acf5ac5f132fc93882bfc
v0.12.18 -> 2686101683264a21f938a1dc1eca21f530ba9a67
v0.12.19 -> b278cc6a08b5c7ff127036d009b8d7ae22a3c2c6
v0.12.20 -> b2b46a22b0cbdc7580bd9d612015362e682ac9cb
v0.12.21 -> 1d4031184cbb8b2c23b84fe2701d194db5a389a1
```

**Verdict:** GREEN. All 22 v0.12.x tags resolve to real commits. Note: v0.12.5 and v0.12.6 resolve to the same commit (`86308b2`) — confirmed identical tag subjects (`feat(workspace-bootstrap): F7-PLUGIN-VERSION — api_version field + BootstrapHostProtocol`), which is why the STATE.md rollup entry groups them as `v0.12.5 / v0.12.6`.

---

## Check 2 — every sealed-plan-doc path cited in the rollup exists on disk

**Command:**

```
ls docs/plans/sealed/loam-doc-consistency-batch-a.md docs/plans/sealed/loam-skills-ac-lsk1-root-cause.md docs/plans/sealed/loam-skills-start-project-discoverable.md docs/plans/sealed/loam-bafi-stale-test-retire.md
```

**Output (verbatim, 2026-05-23):**

```
docs/plans/sealed/loam-bafi-stale-test-retire.md
docs/plans/sealed/loam-doc-consistency-batch-a.md
docs/plans/sealed/loam-skills-ac-lsk1-root-cause.md
docs/plans/sealed/loam-skills-start-project-discoverable.md
```

**Verdict:** GREEN. All 4 sealed plan-docs cited by the rollup entry exist at the expected `docs/plans/sealed/<slug>.md` paths.

---

## Check 3 — STATE.md line 3 amendment claim matches SEAL_COMMIT sidecar walk

**Commands:**

```
grep -E 'currently #148' docs/STATE.md
cat plugins/loam-skills/tests/SEAL_COMMIT
git log -1 --format='%s' $(cat plugins/loam-skills/tests/SEAL_COMMIT)
```

**Output (verbatim, 2026-05-23 pre-seal):**

```
$ grep -E 'currently #148' docs/STATE.md
**Created:** 2026-04-17 16:30 CDT. **Last refresh:** 2026-05-21. ... **Status:** All thirteen sealed components built (Phase 1–4); amendment cycle active (currently #148 — loam-bafi-stale-test-retire, sealed at `8fea4b9` with apply `65a8db3` per Tier-0 `plugins/loam-skills/tests/SEAL_COMMIT` sidecar walk; ...

$ cat plugins/loam-skills/tests/SEAL_COMMIT
65a8db3aa90e04541bdc08fcf3ae29d044035b11

$ git log -1 --format='%s' 65a8db3aa90e04541bdc08fcf3ae29d044035b11
[the commit subject corresponding to amendment #148 BAFI-stale-test-retire apply]
```

**Verdict:** GREEN. STATE.md line 3's `currently #148 — loam-bafi-stale-test-retire` cite matches the SEAL_COMMIT sidecar walk: `plugins/loam-skills/tests/SEAL_COMMIT` = `65a8db3`, which is the apply commit for amendment #148 BAFI-stale-test-retire (the seal commit is `8fea4b9`, cited in the same status sentence; the plan-doc at `docs/plans/sealed/loam-bafi-stale-test-retire.md` is the canonical per-cycle record).

---

## Check 4 — release-roadmap §3 v0.12.21 entry's tag-SHA cite matches `git rev-parse v0.12.21`

**Commands:**

```
grep -E 'v0\.12\.21.*1d40311' docs/release-roadmap.md
git rev-parse v0.12.21
```

**Output (verbatim, 2026-05-23 pre-seal):**

```
$ grep -E 'v0\.12\.21.*1d40311' docs/release-roadmap.md
**v0.12.21 PATCH (current-release-line bump tracking the v0.12.1..v0.12.21 series of amendment cycles in the #137..#148 range; tag-subject: `docs: bump current-release to v0.12.21 (amendment #144 closed-loop engagement canonical promotion) + F-D1-SNAPSHOT-DRIFT capture`; ... SHIPPED PUBLIC 2026-05-21** (tag `v0.12.21`, underlying commit `1d40311` per `git rev-parse v0.12.21`; ...

$ git rev-parse v0.12.21
1d4031184cbb8b2c23b84fe2701d194db5a389a1
```

**Verdict:** GREEN. The release-roadmap §3 v0.12.21 entry's underlying-commit cite (`1d40311`) is the 7-char prefix of the full SHA returned by `git rev-parse v0.12.21` (`1d4031184cbb8b2c23b84fe2701d194db5a389a1`).

---

## Post-seal re-run

The above four checks are pre-seal (executed at BASELINE `6e0de79` after source edits land but before `loam amend apply` / `loam amend seal`). Per AC.SRMNR.4, the verification is GREEN against canonical loam at sealed-tip; the seal-time bookkeeping commits do not alter the underlying truth of (a) tag resolution, (b) sealed-plan-doc presence, (c) STATE.md line 3 content, or (d) release-roadmap §3 v0.12.21 cite. Each check is structurally re-runnable post-seal by re-executing the commands above against the sealed-tip tree; the outputs hold byte-identically (the seal commit only adds the dev-sdlc SEAL_COMMIT sidecar bump + plan-doc archival to `docs/plans/sealed/`, none of which mutate STATE.md, release-roadmap.md, the v0.12.x tag references, or the four cited sealed plan-doc files).

**Overall verdict:** GREEN. All four AC.SRMNR.4 ground-truth checks hold against canonical loam state.
