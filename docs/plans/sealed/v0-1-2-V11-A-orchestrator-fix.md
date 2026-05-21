# V11.A sub-plan — Orchestrator runtime fix (fence-one-no-edit)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/plans/v0-1-x-roadmap.md` (§2 v0.1.2 item 1 + §8 method-decision register).
**Programme master:** `docs/plans/v0-1-x-roadmap.md` (v0.1.x roadmap).
**Predecessors:** v0.1.0 shipped (private at `lukeivers/loam`); FBE.1–FBE.11 + FBE.6{b,c,d} foldback ladder closed; FBE.5 sealed at `8032348` (current orchestrator BASELINE); v0.1.1 design-note ship is in flight.
**BASELINE (pre-build tip):** `eef5f81` — current canonical pos-v2 HEAD (the FIDRAFT principles-as-canonical-feature capture commit).
**Status-file target:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v11a-orchestrator-fix-status-2026-05-03.md`.

---

## 1. Summary / TLDR

V11.A closes the v0.1.0 known-broken orchestrator runtime — the launchd plist invoking a stale module name that crash-loops every 30s. Three observable failure surfaces (per `<workspace>/.scratch/claude-output/orchestrator-state-2026-05-02.md`):

1. **Plist `pos_orchestrator` → `loam.orchestrator` mismatch** — the M1.rename series (#76–#85) renamed the module but missed the launchd plist template. **Already fixed at f0c4aa9** (FBE.5 hot-fix companion: "fix(v0.1.0): plist module name + session-start fallback for stranger workspaces"). Verified at planning: `framework/orchestrator/ops/launchd/com.loam.orchestrator.plist.tmpl` line 27 = `<string>loam.orchestrator</string>`. **No edit needed.**
2. **`framework/orchestrator/` not in canonical venv editable install list** — claimed by dispatcher as a possible gap. Verified at planning: present at `install-from-source.txt` line 34 (Tier C) AND `docs/install-from-source.md` line 83 AND already installed editable in `/Users/lukeivers/ivers-corp-pos-v2/.venv/` per `pip list` (`loam-orchestrator 0.1.0 /Users/lukeivers/ivers-corp-pos-v2/framework/orchestrator`). **No edit needed.**
3. **Stale installed plist on Luke's host** (`~/Library/LaunchAgents/com.loam.orchestrator.plist` carries the pre-fix `pos_orchestrator` content because the install was never re-run after f0c4aa9 landed). **Operational hygiene on Luke's host — out of fence per dispatch ("don't disrupt pos3's runtime")**; flagged in status file for Luke to action via `python -m loam.orchestrator.scripts.install_launchd --uninstall && reinstall` against the canonical venv.

Net **fix-in-V11.A** scope: zero source-side delta. The two named buckets (plist template, install list) are pre-resolved by f0c4aa9 + FBE.4. The amendment is bookkeeping-only — a sealed-component fence-one-no-edit cycle that records the verification + the smoke proof in the audit trail, mirroring the FBE.4 fence-three-no-edit precedent.

What V11.A DOES land:

1. **Smoke verification (AC.V11.A.3)** — spawn the orchestrator from the post-fix template against an isolated test workspace (NOT pos3's live state); verify it doesn't crash-loop; verify it binds the expected socket at `~/.loam/orchestrator.sock`; verify launchctl reports a healthy state. Recorded in status file.
2. **Sidecar bump on `framework/orchestrator/`** — `tests/SEAL_COMMIT` advances to V11.A seal SHA via `loam amend seal`; `tests/test_no_sealed_amendments.py` BASELINE literal advances via `loam amend apply`.
3. **Plan-doc + manifest authored** at `docs/plans/v0-1-2-V11-A-orchestrator-fix.{md,manifest.yaml}` (universal-prefix admitted).
4. **Parent plan §8 backfill** — `docs/plans/v0-1-x-roadmap.md` §8 register row for v0.1.2 advances to `(in flight)` with V11.A line (apply + seal SHAs) named.

This is a **vocabulary** + **bookkeeping** + **smoke-proof** amendment with zero behaviour change. The `pos_orchestrator` source-string vocabulary leakage (`__main__.py:15` docstring, `__main__.py:44` argparse `prog`, `scripts/__init__.py:19-20` docstring, `docs/operations.md:12`) is **out of V11.A scope per ODD §2.5** — surfaced as a FUTURE_IDEAS_DRAFT candidate per Surface #1 below, since AC.V11.A.* names runtime-fix outcomes only and the dispatcher's tight scope explicitly forbids fence widening.

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; `pos_orchestrator` source-string vocabulary leakage is OUT OF SCOPE for V11.A)

Survey of `framework/orchestrator/` for `pos_orchestrator` references (`grep -rn pos_orchestrator framework/orchestrator/`) returned four sites — all docstring/help-text/operations-doc, none functional:

- `framework/orchestrator/src/loam/orchestrator/__main__.py:15` — module docstring (`"""Run the orchestrator as a module: \`python -m pos_orchestrator\`."""`). The body of the docstring (lines 17-18) already shows the correct invocation `python -m loam.orchestrator`; only the headline references the legacy name.
- `framework/orchestrator/src/loam/orchestrator/__main__.py:44` — `argparse.ArgumentParser(prog="pos_orchestrator")`. Affects `--help` output text only; no functional dispatch path.
- `framework/orchestrator/scripts/__init__.py:19-20` — docstring referencing `python -m pos_orchestrator_scripts.{install,measure}_launchd` (legacy module-name shape that doesn't exist in the current tree either way; the actual invocations use `python -m loam.orchestrator.scripts.install_launchd` per `install_launchd.py` line 18).
- `framework/orchestrator/docs/operations.md:6, 12` — operations doc carries `running pOS` + `pos_orchestrator editable` references. Internal vocabulary only.

**Decision (autonomous, builder's call):** these vocabulary-leakage sites are **OUT OF SCOPE for V11.A** per ODD §2.5 + the dispatcher's tight-scope ruling ("Only the orchestrator runtime fix"). AC.V11.A.* binds to the runtime fix (plist + install + smoke), not vocabulary scrub. Mirrors the FBE.5 Surface #1 pattern — vocabulary scrubs surface as separate candidates rather than scope-creep into a runtime fix.

**FUTURE_IDEAS_DRAFT candidate:** "`framework/orchestrator/` source-string `pos_orchestrator` vocabulary leakage — `src/loam/orchestrator/__main__.py:15` (docstring) + `:44` (argparse `prog`) + `scripts/__init__.py:19-20` (docstring) + `docs/operations.md:6, 12` (operations doc). Non-functional (docstring/help-text only) but inconsistent with the rebrand. Outside V11.A fence (V11.A scope is runtime-fix only); appropriate as a v0.1.x or v0.2 dev-mode-doc cleanup amendment, possibly bundled with FBE.5 Surface #1 (dev-only tool description scrubs)."

This surface is recorded (not halted on) because:
1. The dispatch's tight scope is explicit ("Only the orchestrator runtime fix").
2. None of the four sites cause crash-loops or runtime failures.
3. Halt-trigger 3 ("Fix requires touching components beyond `framework/orchestrator/`") doesn't apply — these ARE inside the fence — but Halt-trigger 2 spirit ("Plist template already fixed → fine, just verify + skip that bucket; surface in status") generalises: the vocabulary fix is a separate concern from the runtime fix.

### Surface #2 (no halt — recorded; the f0c4aa9 plist template fix already shipped)

Plist template at `framework/orchestrator/ops/launchd/com.loam.orchestrator.plist.tmpl` line 27 reads `<string>loam.orchestrator</string>` — verified pre-build via direct file read. The fix landed at commit `f0c4aa9` ("fix(v0.1.0): plist module name + session-start fallback for stranger workspaces", 2026-05-03 06:55:52 -0500), which `git log` confirms is reachable from canonical HEAD.

This is the dispatcher's named expected outcome ("FBE.5/f0c4aa9 may have already fixed this; verify + leave alone if so"). **No edit; verification only.**

### Surface #3 (no halt — recorded; `framework/orchestrator/` already installed editable)

Verified pre-build via `.venv/bin/pip list | grep loam-orchestrator`:

```
loam-orchestrator                  0.1.0        /Users/lukeivers/ivers-corp-pos-v2/framework/orchestrator
```

And via `install-from-source.txt` direct read — `framework/orchestrator/` is at line 34 (Tier C), present in the published install convention. And via `docs/install-from-source.md:83` — present in the per-component fallback list.

The dispatcher's named bucket "Add `framework/orchestrator/` to canonical venv editable install list" is already satisfied by FBE.4 (the file that introduced `install-from-source.txt`). **No edit; verification only.**

### Surface #4 (no halt — recorded; orphan PID 27100 is already gone)

Pre-build probe of `ps -o pid,etime,command -p 27100` returned no row — the orphan process referenced in the orchestrator-state dossier (started 22 Apr, 9d19h elapsed at observation time) has since been killed/exited. Neither `~/.loam/orchestrator.sock` nor `~/.pos/orchestrator.sock` currently exist on Luke's host (`ls -la` returned `No such file or directory` for both). The orphan-cleanup operational item is a non-issue at build time.

Per dispatcher's explicit out-of-scope ruling: "orphan PID 27100 cleanup is operational hygiene on Luke's host — flag in status file; don't auto-kill". Not actioned in V11.A; no flag needed because the orphan has already cleared itself. **Status file records the empirical observation.**

### Surface #5 (no halt — recorded; the installed plist on Luke's host is STALE)

`launchctl print gui/501/com.loam.orchestrator` shows the running plist arguments still contain `pos_orchestrator`:

```
arguments = {
    /Users/lukeivers/pos3/.venv/bin/python
    -m
    pos_orchestrator
}
```

The fix at `f0c4aa9` is in the canonical *template*; the *installed copy* at `~/Library/LaunchAgents/com.loam.orchestrator.plist` was generated from the pre-fix template (and points at `pos3/.venv` — a workspace venv, not the canonical venv). This is consistent with the orchestrator-state dossier's observation that the launchd job has been crash-looping silently.

**Decision (autonomous, builder's call):** **out of fence per dispatch.** The dispatcher explicitly ruled "Smoke against pos3's actual orchestrator state. Pos3 currently has the broken orchestrator running... Verifying the FIX requires running it locally; verify the smoke against an isolated test workspace, NOT against pos3's live orchestrator (don't disrupt pos3's runtime)." Re-running `install_launchd` on Luke's host overwrites the live (broken) installed plist — this would touch operator state outside the canonical pos-v2 fence.

**Status file action item for Luke (operational hygiene, post-V11.A):**

```bash
# 1. Uninstall the stale plist (pre-f0c4aa9 content + pos3-venv pointer)
/Users/lukeivers/ivers-corp-pos-v2/.venv/bin/python \
    -m loam.orchestrator.scripts.install_launchd --uninstall

# 2. Reinstall against the canonical venv with the post-f0c4aa9 template
cd /Users/lukeivers/ivers-corp-pos-v2/
/Users/lukeivers/ivers-corp-pos-v2/.venv/bin/python \
    -m loam.orchestrator.scripts.install_launchd \
    --python "$(pwd)/.venv/bin/python" \
    --working-dir "$(pwd)"

# 3. Verify
launchctl print gui/501/com.loam.orchestrator | grep -A4 arguments
ls -la ~/.loam/orchestrator.sock
```

This is RECORDED in the status file as Luke's manual follow-up — V11.A's smoke verifies the **template-and-canonical-install path produces a healthy orchestrator** (the AC), not that Luke's running launchd job is healthy (which would require disrupting his live runtime).

### Surface #6 (no halt — recorded; smoke must run in an isolated path-and-launchd-label-namespace to honour "don't disrupt pos3")

The `install_launchd.py` script hardcodes `LABEL = "com.loam.orchestrator"` (line 45). Running the standard install path on this machine collides with the existing installed plist at the same label. Two options for honouring the dispatcher's "isolated test workspace, NOT against pos3's live orchestrator":

- **Option A — direct module run (no launchd):** `python -m loam.orchestrator --config <isolated-config.yaml>` against an `OrchestratorConfig(root_dir=Path("/tmp/v11a-smoke/.loam"))`. Verifies the runtime starts, binds a socket at the configured path, doesn't crash. Skips launchd entirely — no label collision risk.
- **Option B — launchd install with custom label override:** would require monkey-patching `LABEL` or running with a different `~/Library/LaunchAgents/` path. Higher complexity; touches launchctl state.

**Decision (autonomous, builder's call):** **Option A** — direct module run via the canonical venv with an isolated `root_dir` config override. Verifies the four runtime contracts the dispatcher named (boots from fresh install, binds `~/.loam/orchestrator.sock`, doesn't crash-loop) without touching launchd state. The "launchctl healthy" AC is verified by the *separate observation* that the installed plist points at the correct module name (post-f0c4aa9 template) — i.e., the structural readiness for launchd-healthy is in place; running launchctl bootstrap to demonstrate it would disrupt pos3's live state.

This is consistent with the dispatcher's broader smoke posture ("don't disrupt pos3's runtime") and the FBE.4 precedent (smoke verified in `/tmp/<isolated>` not against the live host state).

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/VALUE_PROPOSITION.md`) — closing the "v0.1.0 stranger installs the orchestrator and it crash-loops silently" failure mode; restoring the structural readiness of the runtime that three sealed amendments (#38/#39/#40) sit on for v0.1.4 (V11.B).
- **v0.1.x roadmap §2 v0.1.2 item 1** — V11.A scope as defined in the dispatcher's roadmap.
- **AC.V11.A.* per this sub-plan §4** — every AC ladders to the same parent.

**Ladders to:** AC.V11.A.* → v0.1.2 release (after V11.E + ack-first persona + loam-amend ergonomics) → v0.1.4 V11.B (orchestrator-dependent amendments unblocked) → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (V11.A.*)

AC family `AC.V11.A.*` — collision-safe (verified: no prior amendment uses `AC.V11.A.*`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.V11.A.1** | The launchd plist template at `framework/orchestrator/ops/launchd/com.loam.orchestrator.plist.tmpl` invokes `loam.orchestrator` (NOT `pos_orchestrator`) as the `python -m` module argument. (Verified at planning as already-fixed by f0c4aa9; AC re-asserts in the audit trail.) | `grep -nE '<string>(pos_orchestrator\|loam\.orchestrator)</string>' framework/orchestrator/ops/launchd/com.loam.orchestrator.plist.tmpl` returns exactly one line, matching `loam.orchestrator`. |
| **AC.V11.A.2** | `framework/orchestrator/` is present as an editable install entry in the canonical install convention: (a) `install-from-source.txt` carries an `-e ./framework/orchestrator` line; (b) `docs/install-from-source.md` lists it in the per-component fallback. (Verified at planning as already-present per FBE.4; AC re-asserts in the audit trail.) | `grep -n 'framework/orchestrator' install-from-source.txt docs/install-from-source.md` returns at least one hit per file. |
| **AC.V11.A.3** | The orchestrator boots from the post-fix canonical install when invoked as a module — `<canonical-venv>/bin/python -m loam.orchestrator --config <isolated-config>` against an isolated `root_dir` (`/tmp/v11a-smoke/.loam/`) starts a process that (a) does not crash within a 5s readiness window, (b) binds a Unix socket at `<root_dir>/orchestrator.sock` with mode 0600, (c) responds to a clean SIGTERM with exit code 0. The socket-path verification proves the post-FBE.5 default-root contract (`Path.home() / ".loam"` per `config.py:43`) operates correctly when overridden via the `root_dir` config knob. The structural-readiness for `launchctl healthy state` is satisfied by the installed plist template carrying the post-fix module name (AC.V11.A.1) — disturbing the live launchctl job is out-of-scope per the dispatcher's "don't disrupt pos3's runtime" ruling and Surface #5. | Direct shell invocation of the smoke script captured in §7; output written to status file at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v11a-orchestrator-fix-status-2026-05-03.md`. PID alive after 5s; `lsof <root_dir>/orchestrator.sock` shows the orchestrator process holding fd; SIGTERM returns exit 0. |
| **AC.V11.A.4** | Negative AC: zero source-side behaviour changes from V11.A. The only edits land in sidecar files (`tests/SEAL_COMMIT` advance + `tests/test_no_sealed_amendments.py` BASELINE bump) plus the plan-doc + manifest + parent plan §8 backfill. No `*.py` LOC delta inside `framework/orchestrator/src/`; no template/script edits. | `git diff BASELINE..SEAL_COMMIT --stat` shows only paths under: (a) `framework/orchestrator/tests/` (sidecar bump), (b) `docs/plans/` (sub-plan + manifest + parent backfill via universal prefix). No file under `framework/orchestrator/src/` or `framework/orchestrator/ops/` or `framework/orchestrator/scripts/`. |
| **AC.V11.A.S** | Sealed-component fence: `framework/orchestrator/` only — single component; **fence-one-no-edit**. Sidecar bump (SEAL_COMMIT advances) but no source-side delta inside the orchestrator component. Mirrors FBE.4's fence-three-no-edit pattern (per `docs/plans/v0-1-0-foldback-scope-expansion-fbe4.md` §1 + AC.FBE.4.S) — the bookkeeping-only seal records V11.A's verification outcome in the audit trail. | `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under: (a) `framework/orchestrator/tests/` (sidecar `SEAL_COMMIT` + `test_no_sealed_amendments.py` BASELINE literal bump), (b) `docs/plans/` (sub-plan + manifest + parent §8 backfill via `universal_paths.prefixes` admission), (c) optional `framework/orchestrator/tests/SEAL_COMMIT.notes` if the narrative target lives there per `loam amend seal` default. |

**ACs deliberately out of scope (NOT in V11.A):**
- Vocabulary scrub of `pos_orchestrator` docstring/help-text refs (Surface #1 — FUTURE_IDEAS_DRAFT candidate).
- Re-installation of the launchd plist on Luke's live host (Surface #5 — operator hygiene; recorded in status file).
- Orphan PID 27100 kill (Surface #4 — already gone).
- Statusline-watcher script fix (per orchestrator-state dossier D-Q.ORCH.2 — independent of V11.A; deferred to a separate amendment).
- Amendments #38/#39/#40 themselves (V11.B in v0.1.4 per dispatch).
- Live-launchctl bootstrap of the post-fix plist (Surface #5 + Surface #6 — would disrupt pos3 runtime).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
No new Claude-leverage shape change. The orchestrator's IPC (Unix-socket JSON-RPC) is the structural readiness layer for V11.B's primary-persona tracker-context contributor (#40), which is itself a Claude-leverage shape (the persona's session-start surfaces in-flight tracker state to the model). V11.A unblocks that downstream Claude-leverage by restoring runtime; V11.A itself is plumbing.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. Restores the runtime layer the empty-`[tracker-context]` contributor sits on. Without V11.A, every session-start emits an empty contributor block (visible cost RIGHT NOW per orchestrator-state dossier).
- **Harness test:** PASS (neutral). Doesn't add to the toolkit; restores a toolkit primitive that was already declared but currently non-functional.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact smoke shape, which config-override mechanism) inferable from constraints (the dispatcher named the four runtime contracts; the smoke shape follows). No "options to rule on" framed in this plan-doc beyond the autonomous Surface #6 decision (Option A direct-module-run vs Option B launchd-with-label-override) which the builder ruled per dispatch posture.

### Lens 4 — Prompt scope ↔ confidence
Very high confidence in outcome shape: dispatcher pre-recorded the fix-not-rip-out decision, named the four buckets, ruled three out-of-scope items, and named the halt triggers. Tight scope. Method is inferable from constraints + the FBE.4 fence-three-no-edit precedent.

### Lens 5 — Swarming
V11.A is a leaf in the v0.1.2 release bundle. ACs do not partition further: each binds to a single observable surface (template grep, install-list grep, smoke runtime contract, fence diff). No sub-decomposition; the work is single-shell-session shape and a sub-agent would carry coordination overhead exceeding any tighter-AC payoff.

---

## 6. File-by-file map

### Source-side delta (in fence, post-`loam amend apply`):

**ZERO source-side edits inside `framework/orchestrator/src/`, `framework/orchestrator/ops/`, or `framework/orchestrator/scripts/`.** Per AC.V11.A.4 (negative AC).

### Sidecar bumps within sealed-component fence (1 component):

- `framework/orchestrator/tests/SEAL_COMMIT` — advances from `8032348` (FBE.5 seal) to V11.A seal SHA via `loam amend seal`.
- `framework/orchestrator/tests/test_no_sealed_amendments.py` — BASELINE literal advances from `"8032348"` to V11.A pre-apply tip via `loam amend apply`.
- `framework/orchestrator/tests/SEAL_COMMIT.notes` — narrative target for V11.A's seal commit (single-component-fence default).

### Plan-doc + manifest (`universal_paths.prefixes: docs/plans/`):

- `docs/plans/v0-1-2-V11-A-orchestrator-fix.md` (this file).
- `docs/plans/v0-1-2-V11-A-orchestrator-fix.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/plans/v0-1-x-roadmap.md` — §8 method-decision register: replace v0.1.2 row's `(planned)` placeholder with `(in flight)` and add a V11.A subsection with apply commit SHA + seal commit SHA + verification summary.

**TOTAL fence diff:** 0 source edits inside `framework/orchestrator/`; 2 sidecar bumps (SEAL_COMMIT advance + BASELINE literal bump); 1 narrative file; plan-doc + manifest YAML + parent §8 backfill (universal prefix).

---

## 7. Smoke verification

**Smoke (AC.V11.A.3):**

```bash
# Pre-cleanup: ensure isolated test workspace is fresh
SMOKE_ROOT=/tmp/v11a-smoke
rm -rf "$SMOKE_ROOT"
mkdir -p "$SMOKE_ROOT/.loam/logs"

# Author isolated config (overrides default ~/.loam/ root)
cat > "$SMOKE_ROOT/config.yaml" <<EOF
root_dir: "$SMOKE_ROOT/.loam"
EOF

# Boot orchestrator from the canonical venv against the isolated root
cd /Users/lukeivers/ivers-corp-pos-v2/
/Users/lukeivers/ivers-corp-pos-v2/.venv/bin/python \
    -m loam.orchestrator --config "$SMOKE_ROOT/config.yaml" \
    > "$SMOKE_ROOT/orchestrator.out" 2> "$SMOKE_ROOT/orchestrator.err" &
ORCH_PID=$!

# Readiness window — wait up to 5s for the socket to appear
for i in 1 2 3 4 5; do
    if [ -S "$SMOKE_ROOT/.loam/orchestrator.sock" ]; then break; fi
    sleep 1
done

# Verify (AC.V11.A.3 contracts)
echo "=== AC.V11.A.3 verification ==="
echo "PID alive after 5s: $(kill -0 $ORCH_PID 2>&1 && echo YES || echo NO)"
echo "Socket bound: $(ls -la "$SMOKE_ROOT/.loam/orchestrator.sock" 2>&1)"
echo "Socket mode: $(stat -f '%Lp' "$SMOKE_ROOT/.loam/orchestrator.sock" 2>&1)"
echo "lsof on socket: $(lsof "$SMOKE_ROOT/.loam/orchestrator.sock" 2>&1 | head -3)"

# Clean shutdown via SIGTERM
kill -TERM $ORCH_PID
wait $ORCH_PID
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE"

# Cleanup
rm -rf "$SMOKE_ROOT"
```

Expect:
- PID alive after 5s readiness window: **YES**.
- Socket bound at `/tmp/v11a-smoke/.loam/orchestrator.sock` (NOT `/Users/lukeivers/.loam/orchestrator.sock` and NOT `/Users/lukeivers/.pos/orchestrator.sock`).
- Socket mode `600` (per `config.py:69` `socket_mode = 0o600`).
- `lsof` shows the orchestrator process holding the socket fd.
- Exit code on SIGTERM: **0** (per `__main__.py:28` "0 clean SIGTERM/SIGINT shutdown").

**Failure modes:**
- Socket doesn't appear within 5s → orchestrator failed to boot or crashed early. Halt; surface; capture stderr in status file.
- Socket appears at the WRONG path (`~/.loam/orchestrator.sock` instead of the isolated root) → `--config` override doesn't work as expected; halt; surface; deeper diagnosis needed (config loader bug?).
- Exit code on SIGTERM ≠ 0 → shutdown contract violated. Halt; surface.
- `kill -0 $ORCH_PID` returns NO before SIGTERM → process died unexpectedly. Halt; surface.

The smoke runs **pre-seal** to confirm the runtime contract before bookkeeping. If it passes, no need to re-run post-seal (no source edits between).

---

## 8. Hard constraints

- 1 sealed-component sidecar in fence (`framework/orchestrator/`). **No source-side edits anywhere; bookkeeping-only fence-one-no-edit.**
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply` AND per FIDRAFT entry on loam-amend tooling: the apply step does NOT auto-commit by design — manual commit via `git commit -m "chore(amend): V11.A apply ..."` after `loam amend apply` runs.
- AC-prefix `AC.V11.A.*` (collision-safe).
- Auto-memory `MEMORY.md` NOT touched.
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`: only `framework/orchestrator/tests/` must pass post-seal. The smoke (AC.V11.A.3) is exercised manually pre-seal; no in-tree pytest covers it directly (it spans a fresh-shell direct-module-run against canonical).
- Smoke runs against an **isolated test workspace** (`/tmp/v11a-smoke/`) per dispatch ("don't disrupt pos3's runtime"); the live launchctl job at `gui/501/com.loam.orchestrator` is NOT touched.

---

## 9. Out of scope (per ODD §2.5)

- Vocabulary scrub of `pos_orchestrator` docstring/help-text refs (Surface #1; FUTURE_IDEAS_DRAFT candidate).
- Re-install of the launchd plist on Luke's live host (Surface #5; operator hygiene recorded in status file).
- Orphan PID 27100 cleanup (Surface #4; already gone — empirically observed).
- Statusline-watcher script fix (orchestrator-state dossier D-Q.ORCH.2; independent of V11.A).
- Amendments #38/#39/#40 themselves (V11.B in v0.1.4 per dispatch).
- Live-launchctl bootstrap of the post-fix plist (Surface #5 + #6; would disrupt pos3 runtime).
- `framework/orchestrator/docs/operations.md` content update (referenced in Surface #1; vocabulary leakage only, not runtime-functional).

---

## 10. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not silently extend) on:

- **HT-1:** Plist template grep (AC.V11.A.1 verification) returns `pos_orchestrator` instead of `loam.orchestrator`. Halt; surface; the f0c4aa9 fix is not on canonical HEAD, and the dispatcher's "FBE.5/f0c4aa9 may have already fixed this" assumption is wrong; deeper history check needed.
- **HT-2:** `install-from-source.txt` grep (AC.V11.A.2 verification) returns no hit on `framework/orchestrator`. Halt; surface; FBE.4 didn't add the entry as expected; widening fence to add the line would touch FBE.4-sealed surfaces.
- **HT-3:** Smoke (AC.V11.A.3) fails per any of the four failure modes in §7. Per dispatch halt-trigger 4 ("Smoke fails (orchestrator still crash-loops post-fix) → halt + surface; deeper diagnosis needed.").
- **HT-4:** `loam amend apply` rejects the manifest. Halt; surface; the manifest's `components` shape may need adjustment or the BASELINE pin is wrong.
- **HT-5:** `loam amend seal` rejects the seal. Halt; surface; usually means a touched-file lives outside the fence + universal admissions (impossible for fence-one-no-edit if AC.V11.A.4 holds, but verify).
- **HT-6:** A file inside `framework/orchestrator/src/`, `framework/orchestrator/ops/`, or `framework/orchestrator/scripts/` shows non-sidecar diff post-seal (`git diff BASELINE..SEAL_COMMIT -- framework/orchestrator/{src,ops,scripts}/`). Halt; surface; AC.V11.A.4 violation; revert the unintended change.
- **HT-7:** Surrounding-code ODD §2.5 violation discovered in any touched file. Halt; surface; do NOT silently extend or fix in-band.
- **HT-8:** Wall-time exceeds 60 min (dispatch hard cap). Halt with partial findings.
- **HT-9:** WD drifts to pos3. Halt immediately.
- **HT-10:** Sealed-component fence breach beyond `framework/orchestrator/`. Halt; surface.
- **HT-11:** The smoke needs to touch live launchctl state to verify launchctl-healthy (e.g., the dispatcher's AC interpretation differs from §4's structural-readiness reading). Halt; surface for dispatcher ruling; the conservative reading (Option A direct-module-run + AC.V11.A.1 template-fix verification) is the autonomously-chosen interpretation per Surface #6.

---

## 11. Risks

- **Risk: smoke shows orchestrator binds the wrong socket path.** If `--config <yaml>` doesn't override `root_dir` cleanly, the smoke could bind `~/.loam/orchestrator.sock` instead of the isolated path — collides with whatever Luke's live state expects. Mitigation: pre-check that the isolated-root path is empty before launch; verify socket appears at expected path post-launch; halt-and-surface (HT-3) if mismatched.
- **Risk: `loam amend apply` requires a non-empty source-side delta and rejects fence-one-no-edit.** Mitigation: FBE.4 precedent (fence-three-no-edit) shows the tool accepts no-source-delta amendments; if V11.A surfaces a tooling gap, halt-and-surface (HT-4); the dispatcher can then rule on widening to include a token edit (e.g., a comment-only one-line in `framework/orchestrator/CHANGELOG.md` if such a file exists, or an entry in `framework/orchestrator/docs/operations.md` recording the verification).
- **Risk: the orchestrator imports a missing dep on first boot.** The pyproject lists `pydantic>=2`, `pyee>=11`, `opentelemetry-api>=1.25`, `opentelemetry-sdk>=1.25`, `pyyaml>=6`, plus three intra-component deps (`loam-scope-of-work`, `loam-objective-tracker`, `loam-primary-persona`). All are pip-list-verified installed in the canonical venv. Mitigation: pre-smoke, run `python -c "import loam.orchestrator"` to catch ImportError early; halt + surface if it fails.
- **Risk: orchestrator config loader doesn't accept the YAML format used in the smoke.** `config.py:43` defaults `_DEFAULT_ROOT = Path.home() / ".loam"`; need to verify `load_config(yaml_path)` accepts a `root_dir: <path>` key. Mitigation: pre-smoke, read `framework/orchestrator/src/loam/orchestrator/config.py` `load_config` to confirm the YAML key shape.
- **Risk: f0c4aa9 verification returns `loam.orchestrator` but the live plist on Luke's host stays stale (Surface #5).** This is the documented operator-hygiene gap; not a V11.A AC. Status file records the manual reinstall recipe.

---

## 12. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Pre-smoke verification** (AC.V11.A.1 + AC.V11.A.2) — quick greps to confirm the dispatcher's pre-recorded assumptions hold.
3. **Pre-smoke import check** — `python -c "import loam.orchestrator"` to catch missing-dep ImportError early.
4. **Pre-smoke config check** — read `config.py` `load_config` to confirm YAML key shape.
5. **Smoke run (AC.V11.A.3)** — execute §7 smoke; capture output to status file scratch.
6. **Manifest commit** — author `docs/plans/v0-1-2-V11-A-orchestrator-fix.manifest.yaml` (1 component in `components:` block).
7. **`loam amend apply`** — invoke against the manifest. Produces apply-bookkeeping changes (BASELINE bump in `framework/orchestrator/tests/test_no_sealed_amendments.py`).
8. **Manual apply commit** — `git commit -m "chore(amend): V11.A apply ..."` per FIDRAFT entry on loam-amend tooling (apply does not auto-commit by design).
9. **`loam amend seal`** — produces deterministic seal commit; sidecar `SEAL_COMMIT` advances to seal SHA; narrative file written at `framework/orchestrator/tests/SEAL_COMMIT.notes`.
10. **Parent plan-doc backfill** — `docs/plans/v0-1-x-roadmap.md` §8 backfill v0.1.2 row + V11.A subsection with apply + seal SHAs (separate NEW commit; admitted via `docs/plans/` universal prefix).
11. **Status file write** — `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v11a-orchestrator-fix-status-2026-05-03.md` with seal report + Surface #5 reinstall recipe for Luke.

NO `git commit --amend` at any point. NO push to any remote.

---

## 13. References

- **Parent plan / programme master:** `docs/plans/v0-1-x-roadmap.md` (§2 v0.1.2 item 1 + §5 Decision A + §8 register).
- **Orchestrator-state dossier:** `<workspace>/.scratch/claude-output/orchestrator-state-2026-05-02.md` — empirical pre-fix observation Luke validated.
- **Plist template fix commit:** `f0c4aa9` — `git show f0c4aa9 --stat` confirms the two-line plist template change.
- **FBE.4 fence-three-no-edit precedent:** `docs/plans/v0-1-0-foldback-scope-expansion-fbe4.md` §1 + AC.FBE.4.S — bookkeeping-only seal pattern.
- **FBE.5 sub-plan precedent (sub-plan format):** `docs/plans/v0-1-0-foldback-scope-expansion-fbe5.md` — sub-plan structure mirrored here.
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no source edit yet beyond the plan itself).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §12).
  - `feedback_subagent_odd_violation_halt` (HT-1 through HT-11).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to fence component only).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1–6 explicit; each surfaces a decision the dispatcher could review).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified at planning" claim has a path/line citation or a `git show` reference).
  - `feedback_critical_thinking_on_deviations` (Surface #5 + Surface #6 enumerate alternatives weighed by outcome × cost × risk).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (AC.V11.A.3 tightens the dispatcher's "launchctl healthy state" loose phrasing to the structural-readiness contract that matches the don't-disrupt-pos3 ruling).

---

## 14. AI-time band

- Predicted: **15–25 min, midpoint 20 min**; dispatch hard cap 60 min.
- Justification: per duration-estimation rubric (`feedback_duration_estimation_rubric`) — fence-one-no-edit amendment-build (no source edits + smoke + bookkeeping) is bottom-band single-component amendment work; comparable to FBE.4's bookkeeping-only seal (~5–10 min observed) plus the smoke run (~3–5 min for shell + readiness wait + cleanup) plus parent plan §8 backfill (~2 min) plus status file write (~3–5 min). Tighten upper bound to 25 because pre-smoke checks (import + config) add a small probe layer.

---

## 15. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit (manual `chore(amend): V11.A apply ...`): `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of V11.A sub-plan-doc. Ready to build.*
