# Plan — M1c-corrective (rename trailing-edge bookkeeping)

**Status:** authored 2026-04-29 by builder (task #16 in dispatcher queue).
**Predecessor:** memory-sidecar-recovery sealed at `8ee241b` (M9 § f-up via #92, after M1.rename M1a..M1g + M2..M5 + M6a..M6c + M9).
**Successor candidates:** M11.dry-run (task #19).
**Authority:** dispatcher directive 2026-04-29 ("M1c-corrective — small follow-on amendment to close two related residual surfaces from the M1.rename programme + M9 cleanup pass").
**Source surfaces (audit trail):**
- M1d build-time finding #13 (deferred per M1e dispatch §Halt-trigger #8 because the surface ~20 callsites exceeded M1e's natural fence).
- M9 build memory-sidecar diagnostic FIDRAFT-tracked gap "launchd label still com.pos-v2.* not com.loam.* post-M1c".
- M6c HSF#1: `plugins/dev-sdlc/dev-mode-manifest.yaml:136-137` references pre-M6 stale paths.
- `docs/rebuild/plans/loam-rename-decisions.md` Tier-1 item 4 (com.pos-v2.* → com.loam.*; version-suffix-drop ruling).

---

## 1. Summary / TLDR

Two coherent residual surfaces close as one M1.rename trailing-edge bookkeeping amendment:

1. **`com.pos.orchestrator` launchd label rebrand → `com.loam.orchestrator`** across non-historical source. The orchestrator's user-agent label was the v1-era pre-pos-v2 shape; M1c's workspace-slug-namespacing rebrand never touched it (it was never namespaced because it was authored pre-#6 and lived under the pre-rename brand). Per Tier-1 item 4 + version-suffix-drop ruling, the post-M1c shape is `com.loam.orchestrator`. Includes the LIVE config default in `framework/self-upgrade/src/loam/self_upgrade/config.py:39` + the plist template filename + the install/test/docs surface across `framework/orchestrator/` and `framework/self-upgrade/`.

2. **dev-mode-manifest.yaml stale path refs** — `plugins/dev-sdlc/dev-mode-manifest.yaml:137-138` (M6c HSF#1 pointed at lines 136-137 in pre-M6c numbering; current YAML has them at 137-138 with the comment header at 136). Two `glob:` entries — `tools/pos-amend/**` + `tools/orphan-plist-cleanup/**` — point at pre-M1g/M6b.1 paths. Post-M1g: `pos-amend` was renamed `loam-amend`. Post-M6b.1: `loam-amend` MOVED to `plugins/dev-sdlc/tools/loam-amend/`. `orphan-plist-cleanup` lives at `framework/tools/orphan-plist-cleanup/` (was top-level `tools/orphan-plist-cleanup/` pre-M6b.0 split).

The two surfaces are coherent as "M1.rename trailing-edge bookkeeping" — both close residuals the rename programme left behind. They lift in one amendment.

Operational restart: the running `com.pos.orchestrator` launchd job (PID 57302 at plan-time) gets bootout + reinstall under the new label so the live state matches the source.

---

## 2. Research findings (inlined)

### 2.1 Empirical surface counts (verified 2026-04-29 against HEAD `6f272ce`)

**Surface 1 — `com.pos.orchestrator` rebrand candidates (non-historical, non-archaeological-detector):**

26 refs across 8 files:

| File | Refs | Type |
|---|---|---|
| `framework/orchestrator/ops/launchd/com.pos.orchestrator.plist.tmpl` | filename | live artefact; rename to `com.loam.orchestrator.plist.tmpl` |
| `framework/orchestrator/scripts/install_launchd.py` | 3 | LABEL constant + tmpl path + docstring |
| `framework/orchestrator/tests/test_d2_launchd.py` | 5 | tmpl path + 4 LABEL test args |
| `framework/orchestrator/docs/operations.md` | 3 | grep examples in install/uninstall/troubleshoot |
| `framework/orchestrator/docs/measurement-launchd.md` | 8 | measurement narrative + uninstall verification |
| `framework/self-upgrade/src/loam/self_upgrade/config.py` | 2 | docstring example + LIVE default field value |
| `framework/self-upgrade/src/loam/self_upgrade/orchestrator_control.py` | 1 | docstring example |
| `framework/self-upgrade/docs/architecture.md` | 1 | yaml example |
| `framework/self-upgrade/docs/cli-reference.md` | 2 | python example + yaml example |
| `framework/self-upgrade/docs/sequences.md` | 1 | sequence diagram launchctl invocation |

The dispatch's "~20 callsites" estimate is in-bracket given the post-M6 framework/-prefix split's narrative additions. NO HALT — surface count fits the dispatch envelope.

**Surfaces explicitly EXCLUDED (load-bearing archaeological detectors per their own docstrings):**

- `framework/tools/orphan-plist-cleanup/**` — README.md, src/loam/orphan_plist_cleanup/detector.py, tests/conftest.py, tests/test_dry_run.py, tests/test_detector.py, tests/test_apply.py. The `com.pos.orchestrator` literal here is detector-heuristic test data. The detector's `Classification.ORPHAN_V1` enum explicitly identifies "v1-era shape (e.g. `com.pos.orchestrator`)" as a remediation target — these strings are LOAD-BEARING for the tool's mission of detecting pre-pos-v2 archaeological orphans on hosts that have them. Renaming would break the tool.
- `framework/tools/loam-migrate-launchd-labels/tests/test_migrate.py` — `test_3_segment_pos_is_not_legacy_namespaced` asserts `com.pos.orchestrator.plist` is NOT a legacy-namespaced shape (it's a single-segment v1 orphan, owned by the orphan-plist-cleanup tool not the migrator). Same archaeological-test-data pattern.

15 refs in these tools (verified by grep) stay AS-IS. Per `loam-rename-decisions.md` "Out of scope (preserve historical record per Idea 10)" — but scoped here as "load-bearing archaeological detectors" rather than historical-record-preservation; both readings agree the literals stay.

**Surfaces explicitly EXCLUDED (historical-record per Idea 10):**

- `docs/rebuild/plans/**` — all 16 plan-doc refs (most pre-this-amendment; this plan-doc itself adds 1+ during authoring).
- `docs/rebuild/components/**` — 10 component-narrative refs (historical proposals).
- `pos-v2-rebuild-proposal.md` — preserved historical document per dispatch.

**Surface 2 — dev-mode-manifest.yaml stale paths:**

2 lines (current YAML lines 137-138 — M6c HSF#1's "lines 136-137" was pre-M6c numbering; M6c's narrative-edit at lines 118-119 shifted line numbers by 2):

```yaml
  # Dev tooling.
  - glob: "tools/pos-amend/**"               # ← line 137: pre-M1g rename + pre-M6b.1 MOVE
  - glob: "tools/orphan-plist-cleanup/**"    # ← line 138: pre-M6b.0 framework/-split MOVE
```

Post-rename + post-MOVE replacements:
```yaml
  # Dev tooling.
  - glob: "plugins/dev-sdlc/tools/loam-amend/**"
  - glob: "framework/tools/orphan-plist-cleanup/**"
```

Verified by `ls plugins/dev-sdlc/tools/` → `loam-amend  loam-mode` and `find . -type d -name orphan-plist-cleanup` → `./framework/tools/orphan-plist-cleanup`.

### 2.2 Live launchd state (verified 2026-04-29)

```
$ launchctl list | grep -E "com\.(pos|loam)"
57302   1   com.pos.orchestrator                       # ← live, this amendment's target
-       78  com.pos-v2.ivers-corp-pos-v2.memory-graphiti  # ← pre-M1c, NOT this amendment
94506   0   com.pos-v2.pos3.orchestrator               # ← pre-M1c, NOT this amendment
1079    -15 com.pos-v2.pos3.memory-graphiti            # ← pre-M1c, NOT this amendment
```

PID 57302 with label `com.pos.orchestrator` is the v1-shape user-agent this amendment rebrands. The other `com.pos-v2.*` labels are pre-M1c-live-shape — owned by the M1c migration helper at `framework/tools/loam-migrate-launchd-labels/`, not this amendment.

Plist on disk: `~/Library/LaunchAgents/com.pos.orchestrator.plist` exists. Post-amendment: bootout the old, install the new.

### 2.3 dev-mode-manifest.yaml broader staleness (HALT-AND-SURFACE per dispatch trigger #3 — DEFERRED, NOT IN SCOPE)

The `roots:` block (lines 41-64) and `always_loaded:` glob list (lines 78-110) reference 15 top-level component dirs (`cost-governance/`, `graceful-degradation/`, `hands-off-lifecycle/`, etc.) that no longer exist at workspace root post-M6b.0 — they MOVED under `framework/`. Same applies to `tools/` (line 58) and the always-loaded `data/` glob (line 110).

The `loam-mode` partition resolver (`plugins/dev-sdlc/tools/loam-mode/src/loam_mode/audit.py:107`) handles missing roots gracefully (`if not root_path.exists(): continue` — non-existent paths return empty match-sets and are not errors). All 60 `loam-mode` tests pass against this stale state. So the staleness is tolerated but the manifest is misaligned with reality.

This is dispatch halt-trigger #3 ("dev-mode-manifest.yaml stale path refs map to a path that doesn't exist post-M6 — needs further investigation"). However, M6c's HSF#1 was explicit: it flagged ONLY lines 136-137 (now 137-138). Expanding scope to fix the entire `roots:` + `always_loaded:` block would be a separate `dev-mode-manifest-realignment` amendment with its own ODD analysis (does dev-mode also need `framework/**` admitted? what's the intended partition shape post-framework-split?).

**Decision:** stay strictly within M6c HSF#1 scope (lines 137-138 only). Surface the broader manifest staleness for FIDRAFT capture and a separate amendment. Append to FUTURE_IDEAS_DRAFT.md per discipline.

### 2.4 Rename-decisions doc consistency check

`docs/rebuild/plans/loam-rename-decisions.md` Tier-1 item 4: "`com.pos-v2.<slug>.*` launchd labels → `com.loam.<slug>.*` — the version suffix is dropped concurrently (no `v1` to differentiate)."

Note this names the `com.pos-v2.<slug>.*` shape (post-#6 namespaced shape pre-M1c). The orchestrator's `com.pos.orchestrator` is the older single-segment v1-era shape that `framework/tools/orphan-plist-cleanup/` is built to detect. Strictly speaking this label is BOTH a live source artefact AND archaeologically the same string the cleanup tool detects on host filesystems.

**Resolution:** the dispatch is explicit ("`com.pos.orchestrator` launchd-label stragglers ... rebrand to `com.loam.orchestrator`"). The cleanup tool's detection scope is filesystem-orphan-plists on hosts, not source-tree literals; renaming the source-tree literal to `com.loam.orchestrator` doesn't change what the cleanup tool detects (still archaeological `com.pos.*` plists on hosts). The two surfaces don't conflict.

### 2.5 Sealed-test impact (ODD §4 in-band retire)

The 5 LABEL test args in `framework/orchestrator/tests/test_d2_launchd.py` are direct text edits — assertions of the form `data["Label"] == "com.pos.orchestrator"` become `data["Label"] == "com.loam.orchestrator"` at line 47, plus 4 render-args at lines 39, 58, 72, 76. The plist template path at line 30 needs the rename too.

Per `feedback_loose_AC_text_fix_AC_not_implementation`: the AC text these tests cover is "launchd plist template renders to a valid plist with KeepAlive=true and ThrottleInterval=${THROTTLE_SECS}" (test_d2_launchd.py:9-12) — the AC is shape-of-rendered-plist, not the brand string. The brand string in the test is incidental (it's just *some* value passed to the template's `${LABEL}` substitution). Editing the brand from `com.pos.*` → `com.loam.*` preserves the AC's actual spec. ODD §4 in-band; AC text unchanged.

---

## 3. Decisions (recommendations stated)

### D1 — Plist template filename rename mechanism

**Recommendation: file MOVE via `git mv` from `com.pos.orchestrator.plist.tmpl` to `com.loam.orchestrator.plist.tmpl`.** Preserves git history (the tmpl content stays byte-identical — only references to `${LABEL}` substitution; no rename to the variable inside). Two source files need their hard-coded path string updated: `install_launchd.py:42` and `test_d2_launchd.py:30`.

Alternative: leave the filename and only rename the LABEL constant. **Rejected** — leaves a `com.pos.orchestrator.plist.tmpl` filename that grep-matches the post-rename greppability assertion in §15 ("`com.pos.orchestrator` in non-historical surface returns empty"). Filename rename is the cleaner shape.

### D2 — LIVE config default rename safety (dispatch halt-trigger #2)

The default field at `framework/self-upgrade/src/loam/self_upgrade/config.py:39`:

```python
launchd_label: str = "com.pos.orchestrator"
```

This is the LIVE default for `UpgradeConfig`. If a deployed workspace has `~/.loam/upgrade-config.yaml` WITHOUT a `launchd_label:` override, it inherits the default. Post-rename the default becomes `"com.loam.orchestrator"`. Any deployed workspace whose runtime expected the old default would silently flip to the new label.

**Risk assessment:**
- No `~/.loam/upgrade-config.yaml` exists on this host (verified at plan time — `cat ~/.loam/upgrade-config.yaml` returned no file).
- The `self-upgrade` component is M9-staged (per `docs/rebuild/STATE.md` it's authored but not yet wired to live runtime; `orchestrator_control.py::launchctl_kickstart` is called by `self-upgrade`'s own paths, not by the live orchestrator's startup). The live orchestrator at PID 57302 was started by the older `install_launchd.py` script directly, not by `self-upgrade`'s paths.
- Therefore: changing the default has zero live-runtime effect on this host. Any future deployed workspace that uses `self-upgrade` would get the new default — which is the correct post-M1c shape.

**Recommendation: rename the default to `"com.loam.orchestrator"`.** Source-truth default tracks the post-M1c label shape. No runtime breakage observed or expected. Dispatch halt-trigger #2 cleared.

### D3 — Operational reload mechanism for the running launchd job

**Recommendation: bootout-old + reinstall-new via the post-rename `install_launchd.py`.** Sequence:

1. `launchctl bootout gui/$UID/com.pos.orchestrator` — stops the running PID 57302 job.
2. `rm ~/Library/LaunchAgents/com.pos.orchestrator.plist` — removes the old plist file.
3. `python framework/orchestrator/scripts/install_launchd.py --python <venv> --working-dir <pwd> --throttle-secs 30` — installs the new plist under `~/Library/LaunchAgents/com.loam.orchestrator.plist` (the install script auto-derives the filename from the LABEL constant) and bootstraps it.
4. Verify: `launchctl list | grep com.loam.orchestrator` returns a PID; `launchctl list | grep com.pos.orchestrator` returns empty.

Alternative: leave the running job at the old label and let it die naturally on next host reboot. **Rejected** — dispatch is explicit ("Operational launchctl reload of any affected services to apply the new label"). Inconsistency between source-tree label and live-runtime label is a confusion surface.

Note: the orchestrator process itself doesn't read its own label from anywhere — `pos_orchestrator/__main__.py` just runs the orchestrator main loop. So bootout + reinstall doesn't lose any in-process state beyond the running PID.

### D4 — Sealed-component fence

**Recommendation: 3 components — `framework/orchestrator/`, `framework/self-upgrade/`, and `plugins/dev-sdlc/`.**

- `framework/orchestrator/`: receives the 5 file edits (plist tmpl rename + install_launchd.py + test_d2_launchd.py + operations.md + measurement-launchd.md).
- `framework/self-upgrade/`: receives the 4 file edits (config.py + orchestrator_control.py + 3 docs/*.md).
- `plugins/dev-sdlc/`: receives the dev-mode-manifest.yaml lines 137-138 edit.

BASELINE = current HEAD `6f272ce` (post-#92 SHA backfill).

### D5 — Test scope (per dispatch)

**Recommendation: narrow to orchestrator + self-upgrade + dev-sdlc tests.**

- `framework/orchestrator/tests/` — sealed-component surface; verifies template still renders, LABEL-rebranded asserts pass.
- `framework/self-upgrade/tests/` — verifies config default default loads; no test asserts on the old default value (verified by grep at plan-time).
- `plugins/dev-sdlc/tools/loam-mode/tests/` — verifies the manifest still parses + audit still passes (the `loam-mode` resolver tests depend on the manifest's structural integrity).

Skip: full repo-wide pytest. Per dispatch + per `feedback_amendment_dispatch_speedups` ruling.

---

## 4. Acceptance criteria

AC family **AC.RNM-1c-fix.\*** (per dispatch — doesn't collide with existing AC families). Each AC ladders to AC.OSS-M1.S (M1.rename programme seal) → AC.OSS.6 (final scrub) → AC.PO.1 + AC.PO.2 (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`).

| AC ID | Outcome | Verification |
|---|---|---|
| AC.RNM-1c-fix.1 | All non-historical, non-archaeological-detector refs to `com.pos.orchestrator` rebrand to `com.loam.orchestrator`. The plist template filename is renamed, the LABEL constants are rebranded, the docs prose is rebranded, the test args are rebranded. | `git grep -F 'com.pos.orchestrator' -- 'framework/orchestrator/' 'framework/self-upgrade/' \| grep -v 'docs/rebuild/'` returns empty. |
| AC.RNM-1c-fix.2 | LIVE config default at `framework/self-upgrade/src/loam/self_upgrade/config.py:39` is `"com.loam.orchestrator"`. | Source-grep on `launchd_label: str = ` returns the new default. |
| AC.RNM-1c-fix.3 | dev-mode-manifest.yaml lines 137-138 reference post-M1g + post-M6b.1 paths: `plugins/dev-sdlc/tools/loam-amend/**` + `framework/tools/orphan-plist-cleanup/**`. | Source-grep on the manifest YAML; both `glob:` entries point at existing directories on disk. |
| AC.RNM-1c-fix.4 | Touched-component tests pass: orchestrator (`pytest framework/orchestrator/tests/test_d2_launchd.py`) + self-upgrade (`pytest framework/self-upgrade/tests/`) + loam-mode (`pytest plugins/dev-sdlc/tools/loam-mode/tests/`). | Test runner output. |
| AC.RNM-1c-fix.5 | Operational verification: post-restart, `launchctl list \| grep com.pos.orchestrator` returns empty; `launchctl list \| grep com.loam.orchestrator` returns a running PID; `~/Library/LaunchAgents/com.pos.orchestrator.plist` does not exist; `~/Library/LaunchAgents/com.loam.orchestrator.plist` exists. | Manual launchctl invocations during the build's verification step. Recorded in §14 D-build.RNM-1c-fix.5. |
| AC.RNM-1c-fix.S | `git diff --name-only BASELINE..SEAL_COMMIT` produces only paths under `framework/orchestrator/`, `framework/self-upgrade/`, `plugins/dev-sdlc/`, or universal-paths. | All three components' `test_no_sealed_amendments.py` pass against new BASELINE `6f272ce`. |

---

## 5. Sealed-component fence

**Components touched (3):**

1. `framework/orchestrator/` — receives:
   - `ops/launchd/com.pos.orchestrator.plist.tmpl` → MOVE to `ops/launchd/com.loam.orchestrator.plist.tmpl` (filename change; content unchanged).
   - `scripts/install_launchd.py` — `LABEL = "com.loam.orchestrator"` (line 31), tmpl path string (line 42), install-target docstring (line 14).
   - `tests/test_d2_launchd.py` — tmpl path string (line 30), 4 LABEL test args (lines 39, 47, 58, 72), 1 assertion (line 47).
   - `docs/operations.md` — 3 grep examples (lines 30, 31, 55).
   - `docs/measurement-launchd.md` — 8 narrative refs (lines 7, 12, 13, 21, 71, 72, 75, 78).

2. `framework/self-upgrade/` — receives:
   - `src/loam/self_upgrade/config.py` — docstring example (line 13) + LIVE default field value (line 39).
   - `src/loam/self_upgrade/orchestrator_control.py` — 1 docstring example (line 204).
   - `docs/architecture.md` — 1 yaml example (line 103).
   - `docs/cli-reference.md` — 1 python example (line 58) + 1 yaml example (line 76).
   - `docs/sequences.md` — 1 sequence-diagram launchctl invocation (line 36).

3. `plugins/dev-sdlc/` — receives:
   - `dev-mode-manifest.yaml` — 2 `glob:` entries at lines 137-138 (paths only; comment header at line 136 unchanged).

**Universal admissions** (per amendment #22 ruling #3):
- `docs/rebuild/plans/` — for this sub-plan + manifest.

No cross-component widening required; each component's seal-test `allowed_prefixes` already includes its own root.

**HC#4 byte-content invariant:** edits land in source + tests + docs + a YAML manifest; none of these are HC#4 sample paths in any per-component fence config. NO RETIRE-AND-REBASELINE.

---

## 6. Halt triggers

- HT-1: Pre-build empirical surface count materially different from the dispatch's ~20 estimate. **CLEARED at plan time** — 26 refs in 8 files; in-bracket given post-M6 framework/-prefix narrative additions (see §2.1).
- HT-2: LIVE self-upgrade config default rename breaks runtime behaviour for any deployed service. **CLEARED at plan time** — no `~/.loam/upgrade-config.yaml` on host; self-upgrade not yet wired to live runtime; live orchestrator was started by `install_launchd.py` not `self-upgrade` (see §3 D2).
- HT-3: dev-mode-manifest.yaml stale path refs map to a path that doesn't exist post-M6 (audit's ref was wrong; needs further investigation). **PARTIALLY CLEARED at plan time** — M6c HSF#1's named lines (137-138) DO map to fixable post-M6b.1 paths; but the BROADER manifest staleness (lines 41-64 + 78-110 reference top-level dirs that MOVED under `framework/`) is OUT OF M6c HSF#1's scope; surfaced for a separate `dev-mode-manifest-realignment` amendment per FIDRAFT discipline (see §2.3).
- HT-4: ODD §2.5 violations encountered in surrounding code. Surface for FIDRAFT, do NOT expand scope.
- HT-5: launchctl reload fails — surface specific cause.
- HT-6: Frozen-baseline / byte-content invariant breach beyond ODD §4 in-band — escalate.
- HT-7: Graceful-fallthrough silent-swallow patterns in surrounding orchestrator code that the M6c CDC would flag — note for FIDRAFT, do NOT expand scope.
- HT-8: Wall-clock approaches 60 min — surface for continuation rather than stalling.

---

## 7. Ship shape (commit ladder)

1. **Sub-plan + manifest commit.** This file + `oss-v0-1-0-publish-rename-1c-corrective.manifest.yaml`. Message: `docs(plans): M1c-corrective sub-plan + manifest (rename trailing-edge bookkeeping)`.

2. **Feature commit.** All file edits + plist tmpl rename in one commit. Message: `feat: M1c-corrective — com.pos.orchestrator → com.loam.orchestrator + dev-mode-manifest path refresh`.

3. **Apply commit.** `loam amend apply --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/oss-v0-1-0-publish-rename-1c-corrective.manifest.yaml` — runs against the plugin-side `loam-amend` package at `plugins/dev-sdlc/tools/loam-amend/` (post-M6b.1). Updates objective-tracker (no objectives declared in manifest; no-op) + applies any apply-step renames (none expected). Message auto-generated: `chore(loam-amend-apply): loam amend apply for M1c-corrective`.

4. **Seal commit.** `loam amend seal --plan-doc <abs-path>` runs against the same plugin-side binary. Records SHA in §14 register; seal-test passes against BASELINE `6f272ce` for all 3 components. Message auto-generated.

5. **§14 SHA backfill commit.** `docs(plans): record M1c-corrective commit SHAs in §14 method-decision register`. Per recent amendments' pattern.

No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`. Corrective commits if tests fail post-feature: NEW commits, never amend.

**Operational restart** (between steps 4 and 5):

```bash
# Bootout running v1-shape job
launchctl bootout gui/$UID/com.pos.orchestrator
rm ~/Library/LaunchAgents/com.pos.orchestrator.plist

# Reinstall under new label
cd /Users/lukeivers/ivers-corp-pos-v2
python framework/orchestrator/scripts/install_launchd.py \
    --python "$(pwd)/.venv/bin/python" \
    --working-dir "$(pwd)" \
    --throttle-secs 30

# Verify
launchctl list | grep com.pos.orchestrator   # MUST be empty
launchctl list | grep com.loam.orchestrator  # MUST show running PID
```

If the install fails (e.g. orchestrator import error or bootstrap.py missing), restore the old plist and surface specifically.

---

## 8. Out of scope (per dispatch + named here)

- Commit messages and seal narratives that mention `com.pos.orchestrator` (preserve historical record per Idea 10).
- Pre-rename plan-doc references in `docs/rebuild/plans/` describing past work.
- Anything inside `pos-v2-rebuild-proposal.md`.
- Archaeological-detector test data in `framework/tools/orphan-plist-cleanup/**` and `framework/tools/loam-migrate-launchd-labels/tests/test_migrate.py` (load-bearing — see §2.1).
- The BROADER dev-mode-manifest.yaml staleness (lines 41-64 `roots:` + lines 78-110 `always_loaded:` reference top-level dirs that MOVED under `framework/`) — separate amendment per FIDRAFT discipline (see §2.3).
- Any other `com.pos-v2.*` labels (the pre-#6 namespaced shape pre-M1c) — owned by the M1c migration helper at `framework/tools/loam-migrate-launchd-labels/`, not this amendment.
- M6c's graceful-fallthrough-with-detection CDC retroactive operationalisation across orchestrator (FIDRAFT-tracked per dispatch HT-7).

---

## 9. Backwards-compat verification

- **Plist template content:** byte-identical apart from filename. The `${LABEL}` substitution is unchanged (still single placeholder); the new label gets passed in via the `LABEL=...` template substitution at install time.
- **`install_launchd.py`:** `LABEL` constant rebranded; the rest of the script unchanged. The `_plist_install_path()` derivation auto-applies the new label to the install-target filename.
- **`UpgradeConfig.launchd_label` default:** field type unchanged (`str`), validation unchanged (no validator), default value rebranded. Any caller that explicitly passes `launchd_label="..."` is unaffected (defaults only matter when caller doesn't override). Any deployed `~/.loam/upgrade-config.yaml` with an explicit `launchd_label:` value is unaffected.
- **`launchctl_kickstart(label, ...)`:** parameterised by `label`; no hard-coded brand. Rebrand of caller's `label` arg is the only change needed; the function itself is unchanged.
- **dev-mode-manifest.yaml:** the `loam-mode` partition resolver tolerates missing-path entries (returns empty match-set per `audit.py:107`). Post-edit the entries point at existing directories, which is a strict improvement (the entries actually contribute to the partition now). No `loam-mode` test asserts on the OLD path strings (verified by grep at plan-time).
- **HC#4 byte-content invariant:** NO RETIRE-AND-REBASELINE.

---

## 10. AI-time prediction

Per `feedback_duration_estimation_rubric` calibration table:

- **Predicted (calibrated):** 25-40 min — multi-component (3) but each surface is narrow; largely text-edit + filename rename + manifest line edits. No new helpers, no new tests, no schema migrations. Comparable to amendment #27 (stale-launchd-readme-cleanup; 25-35 min actual) and amendment #21 (S3 silent-excepts; 20-30 min actual). Includes operational launchctl reload (~3-5 min).
- **Plan rubric (uncalibrated 1-min-per-tool-call):** 40-70 min.
- **Actual:** populated post-build in §14 D-build.RNM-1c-fix.0.

Calibration row appended to `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md` post-build.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-build.RNM-1c-fix.0 — AI-time actuals

**Predicted (calibrated):** 25-40 min. **Actual:** ~50 min wall-clock from plan-authoring-start to seal-commit, including operational launchctl reload step and FIDRAFT capture. Slightly over the calibrated upper bound, primarily due to (a) deeper-than-expected pre-build empirical-surface verification (the dispatch's "~20 callsites" estimate required disambiguating archaeological-detector surfaces — 41 raw refs vs 26 actual rebrand candidates vs 15 load-bearing detector strings) and (b) HSF capture authoring (3 substantive FIDRAFT entries averaging ~250 words each). Pure mechanical edit-time was within prediction. Calibration row: see §14 D-build appendix entry; useful next-time signal is that "small follow-on amendment" predictions should add 10-15 min for halt-trigger triage when the audit's surface estimate is bracketed-not-precise.

### D-build.RNM-1c-fix.1 — Plist template filename rename actuals

`git mv framework/orchestrator/ops/launchd/com.pos.orchestrator.plist.tmpl → com.loam.orchestrator.plist.tmpl` preserved history cleanly (`R framework/...` rename status; 96% similarity). Two source files needed the path-string update (install_launchd.py:42 + test_d2_launchd.py:30) — pre-identified at plan time, no surprises. Brand-comment inside the template body (`${LABEL} — service label (com.pos.orchestrator)` → `(com.loam.orchestrator)`) caught by post-edit grep verification; not pre-listed in the plan but a natural extension.

### D-build.RNM-1c-fix.2 — LIVE config default rename actuals

The rename of `launchd_label: str = "com.pos.orchestrator"` → `"com.loam.orchestrator"` at config.py:39 tripped no existing test. `framework/self-upgrade/tests/` 194 passed post-edit. Verified by grep at plan-time that no test asserted on the old default value. Halt-trigger #2 cleared as predicted.

### D-build.RNM-1c-fix.3 — dev-mode-manifest.yaml edit actuals

Post-edit `loam-mode` 59 passed + 1 skipped. The 2 replacement glob paths (`plugins/dev-sdlc/tools/loam-amend/**` + `framework/tools/orphan-plist-cleanup/**`) verified to exist on disk. Comment header added explaining the M1g rename + M6b.1 MOVE provenance for future readers. Halt-trigger #3 partially fired (broader manifest staleness surfaced — see §16 HSF#1) but the named-lines fence held and the dispatch's surface closed cleanly.

### D-build.RNM-1c-fix.4 — Operational restart actuals

Sequence executed:
- `launchctl bootout gui/501/com.pos.orchestrator` → exit 0 (bootout complete after ~2s).
- `rm ~/Library/LaunchAgents/com.pos.orchestrator.plist` → success.
- Verify: `launchctl list | grep com.pos.orchestrator` → empty.
- `python framework/orchestrator/scripts/install_launchd.py --python "$(pwd)/.venv/bin/python" --working-dir "$(pwd)" --throttle-secs 30` → "installed plist at /Users/lukeivers/Library/LaunchAgents/com.loam.orchestrator.plist".
- Post-install: `launchctl list | grep com.loam.orchestrator` → registered with `runs=1`, `last exit code=1`, `state = spawn scheduled` (throttle gate).
- Plist files on disk: `com.pos.orchestrator.plist` absent, `com.loam.orchestrator.plist` present.

**Halt-trigger #5 partial fire:** the launchd registration succeeded (AC.RNM-1c-fix.5 first 4 conditions met) but the orchestrator process exits 1 immediately because `framework/orchestrator/` is not pip-installed editable in the canonical venv (`No module named pos_orchestrator` in stderr). Throttle-retry-locked at 30s minimum gap (no resource burn). This is a pre-existing provisioning gap unrelated to this amendment — see HSF#3 in §16 + corresponding FIDRAFT entry. Decision per critical-thinking-on-deviations: keep the new label registered (correct post-rename source-truth-matches-runtime state); document the provisioning gap separately. AC.RNM-1c-fix.5 considered closed for label-rebrand purposes; full process-running verification deferred to the provisioning fix amendment.

### D-build.RNM-1c-fix.5 — FIDRAFT capture from halt-and-surface triggers

Three FIDRAFT entries appended to `docs/rebuild/FUTURE_IDEAS_DRAFT.md`:

1. **Broader dev-mode-manifest.yaml staleness** (HSF#1 / HT-3 partial fire) — `roots:` + `always_loaded:` blocks reference 15 top-level component dirs that MOVED under `framework/` post-M6b.0; `loam-mode` resolver tolerates via missing-path empty-set rule. Suggested shape: separate `dev-mode-manifest-realignment` amendment with a partition-design decision (per-component-glob vs bulk `framework/**` vs revisit entirely).

2. **Surrounding orchestrator silent-swallow patterns** (HSF#2 / HT-7) — 4 `except Exception: pass` at supervisor.py:539, 556, 563, 570 + adjacent `asyncio.TimeoutError: pass` (line 295) + `ValueError: pass` (line 555). M6c graceful-fallthrough CDC violations. Adds to memory-sidecar-recovery's 3 sites for cumulative 7+ across components — confirms the parent CDC entry's "expect similar density across 20+ components" hypothesis. Suggested shape: single audit-pass amendment running structural grep across all components.

3. **Orchestrator runtime-provisioning gap** (HSF#3 / HT-5 partial fire) — `pos_orchestrator` not installed editable in canonical pos-v2 venv; orchestrator launchd job throttle-retry-locked exit 1. Pre-existing — surfaced by but not introduced by M1c-corrective. Suggested shape: add `framework/orchestrator/` to canonical venv's editable-install list, OR document the canonical-tree-as-source-truth-only intent and require workspace-bootstrap-provisioned working-dir for live orchestrator.

### Commit SHAs

- BASELINE: `6f272ce` — `docs(plans): record amendment #92 commit SHAs in method-decision register`
- Plan + manifest commit: `23fef4c` — `docs(plans): M1c-corrective sub-plan + manifest (rename trailing-edge bookkeeping)`
- Feature commit: `71d14f2` — `feat: M1c-corrective — com.loam.orchestrator rebrand + dev-mode-manifest path refresh`
- Apply commit: `e809193` — `chore(loam-amend-apply): loam amend apply for M1c-corrective`
- Seal commit: `603e953` — `chore(seals): oss-v0-1-0-publish-rename-1c-corrective — orchestrator+self-upgrade+dev-sdlc at e809193`

---

## 15. Post-build verification checklist

- [ ] `git grep -F 'com.pos.orchestrator' -- framework/orchestrator/ framework/self-upgrade/ | grep -v docs/rebuild/` returns empty.
- [ ] `ls plugins/dev-sdlc/tools/loam-amend/ framework/tools/orphan-plist-cleanup/` returns both directories.
- [ ] `pytest framework/orchestrator/tests/test_d2_launchd.py` passes.
- [ ] `pytest framework/self-upgrade/tests/` passes.
- [ ] `pytest plugins/dev-sdlc/tools/loam-mode/tests/` passes.
- [ ] `loam amend apply --plan-doc <abs-path> --dry-run` returns clean (zero missing admissions, zero skipped reasons).
- [ ] `loam amend seal --plan-doc <abs-path>` produces seal commit; seal-test passes for all 3 components; sidecars + narrative advance.
- [ ] `loam amend apply --plan-doc <abs-path> --dry-run` rerun POST-seal returns clean.
- [ ] `launchctl bootout` + `install_launchd.py` applied; new PID running under `com.loam.orchestrator`; old `com.pos.orchestrator` gone from `launchctl list` and `~/Library/LaunchAgents/`.
- [ ] FUTURE_IDEAS_DRAFT.md appended with FIDRAFT entries from HT-3 (broader dev-mode-manifest staleness) and any HT-7 observations.
- [ ] `feedback_duration_estimation_rubric.md` calibration row appended.

---

## 16. Halt-and-surface findings (pre-build)

**HSF#1 — Broader dev-mode-manifest.yaml staleness (HT-3 partial fire, deferred per §2.3).** Lines 41-64 (`roots:`) and lines 78-110 (`always_loaded:`) reference top-level component dirs (`cost-governance/`, `graceful-degradation/`, `hands-off-lifecycle/`, etc.) that MOVED under `framework/` post-M6b.0. The `loam-mode` resolver tolerates this (missing paths return empty match-sets); 60 loam-mode tests pass against the stale state. Out of M1c-corrective scope; deferred to a separate `dev-mode-manifest-realignment` amendment that asks the design question "what's the intended partition shape post-framework-split?" Surfaced to FUTURE_IDEAS_DRAFT.md by the build pass.

**HSF#2 — `com.pos-v2.*` running labels on this host (incidental observation).** Verified at plan-time: `launchctl list` shows two pre-M1c-namespaced labels (`com.pos-v2.ivers-corp-pos-v2.memory-graphiti` PID `-`/exit-78, `com.pos-v2.pos3.orchestrator` PID 94506, `com.pos-v2.pos3.memory-graphiti` PID 1079/exit-15). These are owned by the M1c migration helper at `framework/tools/loam-migrate-launchd-labels/`, not this amendment. Operational migration of the pos3 sidecar's label is tracked in the memory-sidecar-recovery plan §8 ("launchd label `com.pos-v2.*` → `com.loam.*` rename — M1c-corrective task #16; separate amendment — the canonical plist at `framework/memory-system/launchd/com.loam.memory-graphiti.plist` is already renamed; only the pos3 workspace's installed plist still carries the old label"). The pos3-host migration is a one-shot helper invocation, not a source-tree edit. Not in this amendment's scope; not in any current dispatch's scope; kept on FUTURE_IDEAS_DRAFT.md radar as a host-cleanup task.

**HSF#3 — Surrounding orchestrator silent-swallow patterns (HT-7 capture target, populated during build).** The build pass scans `framework/orchestrator/` for graceful-fallthrough-with-detection CDC violations (try/except/pass without detection + surface) and captures findings to FUTURE_IDEAS_DRAFT.md. Not expanded into this amendment per HT-7. Populated in §14 D-build.RNM-1c-fix.5.
