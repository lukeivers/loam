# V11.E sub-plan — graphiti probe graceful-skip (Resolution A)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-x-roadmap.md` (§2 v0.1.2 item 2 + §8 method-decision register).
**Programme master:** `docs/rebuild/plans/v0-1-x-roadmap.md` (v0.1.x roadmap).
**Predecessors:** v0.1.0 shipped; FBE.1–FBE.11 + FBE.6{b,c,d} foldback ladder closed; V11.A sealed at `9d58062` (orchestrator runtime fix); items (a) and (c) of V11.E verified already-fixed at f0c4aa9 per prior V11.E status. Bug-investigation template landed at `4cfeae4`.
**BASELINE (pre-build tip):** `4cfeae4` — current canonical pos-v2 HEAD (the bug-investigation template commit).
**Status-file target:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v11e-graphiti-probe-skip-status-2026-05-03.md`.

---

## 1. Summary / TLDR

V11.E (item-(b)-only) closes the v0.1.0 known-friction "session-start memory probe reports `memory: down` on M-FBM-only stranger workspaces" hazard. The session-start memory probe currently runs unconditionally; on workspaces where the graphiti sidecar is not installed (no `com.loam.memory-graphiti.plist` at the canonical launchd location), the probe times out with `memory: down` and the supervisor escalates loudly. This is a false alarm — the workspace is healthy; it just doesn't run graphiti.

**Resolution A locked by dispatcher:** plist-existence-as-detection-signal. Both probe sites check whether `com.loam.memory-graphiti.plist` exists at the canonical launchd location BEFORE attempting their HTTP/TCP probe; absent → graceful skip with a distinct status (`not_expected` / equivalent), no false `memory: down`. Present → probe runs as today.

Predecessor verification: prior V11.E status file (`<pos3>/workspace/.scratch/claude-output/v11e-followon-hazards-status-2026-05-03.md`) enumerated four resolutions with cost × risk × reversibility weighing; Resolution A chosen (minimum surface; uses existing source-of-truth — the warning text in `ask_service_manager_to_start` already inspects the same plist; self-correcting for the future M-GMP scenario where graphiti ships as a plugin and the user installs it — the plist appears, probing re-engages naturally with no further code change).

Items (a) corpus_gate fallback paths and (c) plist template module name from the original V11.E scope are **already-fixed at f0c4aa9** per the prior status file. This sub-plan covers item (b) only.

What V11.E lands:

1. **Source change in `framework/orchestrator/scripts/pos_session_start.py`** (AC.V11.E.1): a new `_is_memory_expected(launch_agents_dir, label)` helper that returns `True` iff the plist file exists. The `run_session_start` function consults it before invoking `probe_memory_fn`; when not expected, treats memory as "skipped" (effectively `m_ok=True` for the up/down logic; explicit `memory_expected: False` in the result dict; omitted from the `additional_context` services-down warning text).
2. **Source change in `framework/primary-persona/src/loam/primary_persona/session_start_gate.py`** (AC.V11.E.2): `_probe_memory` checks plist existence first and returns the sentinel `"not_expected"` instead of `"down"` when the plist is absent. The string passes through `service_state` dict and is rendered by `context_composer.py:165` as a string value (no schema change required).
3. **Two new tests** (AC.V11.E.3): one per touched file, covering the plist-absent branch returning the new sentinel/skip behaviour.
4. **Smoke (AC.V11.E.4):** two scenarios — (i) plist absent → `memory: not_expected` (gate) + `memory_expected: False` + `status: ready` if orchestrator is up (pos_session_start); (ii) plist present (synthesised) → probe runs, reports up/down per HTTP/TCP outcome.
5. **Sidecar bumps + seal commits** for both fence components.
6. **Parent plan §8 backfill** with V11.E apply + seal SHAs.

Sealed-component fence: **two components — `framework/orchestrator/` + `framework/primary-persona/`**. Per prior status file's owner-ruling matrix recommendation. Both probe sites need the gate.

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; bug confirmed pre-build via direct invocation)

Pre-build smoke against `pos_session_start.run_session_start` with simulated plist-absent + memory-down state:

```
status: partial
memory_up: False
exit_code: 3
additional_context: pos v2 session-start: services did not come up within 0s
    (memory_up=False, orchestrator_up=True). Supervisor will escalate loudly
    on start. Warnings: com.loam.memory-graphiti.plist not installed at
    /tmp/v11e-empty-launchagents/com.loam.memory-graphiti.plist, ...
```

Confirms the bug exactly as the prior V11.E status enumerated. The warning text already names the detection signal Resolution A leverages: **plist-installed-or-not is the ground-truth signal** for "is graphiti expected on this host."

### Surface #2 (no halt — recorded; the gate's `_probe_memory` value flows untouched through `context_composer`)

Verified by reading `session_start_gate.py:189–192` (`probe_service_state` returns `dict[str, str]`) and noting the docstring says "Returns a dict with string values: 'up' / 'down' / 'unknown'." The schema admits arbitrary string values. The new `not_expected` sentinel passes through without breaking any consumer that expected `up`/`down`/`unknown` (consumers either render the string verbatim or check `== "up"`). No schema change required; existing tests that assert `== "down"` need to be inspected (only `test_AC_M_3_*` is the proximity area; verified pre-build that no test pins the `memory` field's `_probe_memory` direct return value to `down`).

### Surface #3 (no halt — recorded; `pos_session_start` `additional_context` text shape change is a deliberate UX improvement per Resolution A)

The `additional_context` string currently includes `memory_up=...` even when memory is not expected. Resolution A's recommended sentinel handling per prior status file owner-ruling matrix: **omit-from-dict** for `pos_session_start`'s `additional_context`. This means when memory is not expected, the `additional_context` warning string drops the `memory_up=...` token (or replaces it with `memory_expected=False`). This is observable change — doc-noted in the status file + the seal narrative.

### Surface #4 (no halt — recorded; the `ask_service_manager_to_start` warning about `com.loam.memory-graphiti.plist not installed` is now redundant when memory is not expected)

When `_is_memory_expected` returns `False`, calling `ask_service_manager_to_start` for the `memory_label` is wasted work AND surfaces a misleading warning ("plist not installed") that is in fact the expected state. The fix should also gate the service-manager call: when memory is not expected, only the orchestrator label is requested. This narrows the warning surface to actual problems.

**Decision (autonomous, builder's call):** include the service-manager-call gating in V11.E. The cost is minimal (a single `if` in `ask_service_manager_to_start` or a parameter narrowing in `run_session_start`); the benefit is the warning text becoming honest. Per ODD §2.5 — this is part of AC.V11.E.1's outcome (the probe doesn't false-alarm on M-FBM workspaces); the warning text is part of the false-alarm surface.

### Surface #5 (no halt — recorded; `_probe_memory` in `session_start_gate.py` uses TCP probe not HTTP)

The orchestrator's `pos_session_start.probe_memory` uses `urllib.request.urlopen("http://127.0.0.1:8765/health")`. The persona's `session_start_gate._probe_memory` uses raw `socket.connect(("127.0.0.1", port))`. Both gate the same logical service (graphiti memory sidecar). Plist-existence-check is the right gate for both — they share the load-bearing assumption (graphiti listens on a port; if the plist is absent, no graphiti, no port to probe). The sentinel string differs by probe type but the gate logic is identical.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — closing the "v0.1.0 stranger session-starts and gets a `memory: down` false-alarm because they don't run graphiti" friction. Stranger experience is part of the harness's surface area.
- **v0.1.x roadmap §2 v0.1.2 item 2** — V11.E scope as defined in the dispatcher's roadmap.
- **AC.V11.E.* per this sub-plan §4** — every AC ladders to the same parent.
- **Composes with M-FBM (file-based memory; v0.1.0 default)** — M-FBM is now the production memory substrate; graphiti is opt-in via plist install. Resolution A acknowledges this via the plist-existence signal.

**Ladders to:** AC.V11.E.* → v0.1.2 release (alongside V11.A done + ack-first persona pending + loam-amend ergonomics pending) → v0.1.5 D-3 protocol widening (Resolution A's plist-existence sentinel composes with D-3's `MemoryProvider` Protocol surface) → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (V11.E.*)

AC family `AC.V11.E.*` — collision-safe (verified: no prior amendment uses `AC.V11.E.*`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.V11.E.1** | `framework/orchestrator/scripts/pos_session_start.py` consults `~/Library/LaunchAgents/com.loam.memory-graphiti.plist` before invoking `probe_memory_fn`; when the plist is absent, `run_session_start` treats memory as not-expected (does NOT call `probe_memory_fn` for memory; does NOT record `memory_up=False`; the result dict carries `memory_expected: False`; `additional_context` does not include `memory_up=...` in the warning string for the not-expected case). When the plist is present, the probe runs as today. | New unit test in `framework/orchestrator/tests/test_pos_session_start.py` covering both branches. Smoke per §7 scenario (i) shows `memory_expected: False` + `status: ready` when orchestrator-up + plist-absent + memory-down (pre-fix would report `partial`/exit_code=3). |
| **AC.V11.E.2** | `framework/primary-persona/src/loam/primary_persona/session_start_gate.py:_probe_memory` checks `~/Library/LaunchAgents/com.loam.memory-graphiti.plist` existence before TCP-probing; when absent, returns the sentinel `"not_expected"` instead of `"down"`; when present, probes as today. The `service_state` dict's `memory` key admits the new sentinel value (no schema change; the existing `dict[str, str]` accepts arbitrary string values). | New unit test in `framework/primary-persona/tests/` covering both branches. Smoke per §7 scenario (i) shows `service_state["memory"] == "not_expected"`. |
| **AC.V11.E.3** | Plist-existence-check uses the SAME canonical location both probe sites use today: `Path.home() / "Library" / "LaunchAgents" / "com.loam.memory-graphiti.plist"`. Both files share a small helper or apply the same logic so the detection signal is consistent. The location is parameterisable for test purposes (existing precedent: `ask_service_manager_to_start` accepts `launch_agents_dir`). | Direct read of both touched files post-fix. The hardcoded path matches the path used in `pos_session_start.ask_service_manager_to_start` line 160 (`Path.home() / "Library" / "LaunchAgents"`). |
| **AC.V11.E.4** | Negative AC: V11.E does not change behaviour when the plist IS present. Both probe sites' existing-test coverage (where present) continues to pass without modification; the plist-present scenario in §7 reports the same outcome as pre-fix (memory-up if HTTP/TCP succeeds; memory-down if HTTP/TCP fails). | All existing tests in both fence components pass post-apply. Smoke per §7 scenario (ii) shows the same `up`/`down` outcome the pre-fix code produced for the same HTTP/TCP state. |
| **AC.V11.E.S** | Sealed-component fence: `framework/orchestrator/` + `framework/primary-persona/` — two components. Sidecar bumps + new tests + source edits within fence. Plan-doc + manifest under `docs/rebuild/plans/` (universal prefix). No edits outside fence. | `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under: (a) `framework/orchestrator/`, (b) `framework/primary-persona/`, (c) `docs/rebuild/plans/`. No file outside these prefixes. |

**ACs deliberately out of scope (NOT in V11.E):**
- Items (a) corpus_gate fallback + (c) plist template module name (verified already-fixed at f0c4aa9 per prior status; recorded in audit trail only).
- Workspace-config flag for memory provider (Resolution D from prior status; deferred to v0.1.5 D-3 / v0.2 M-GMP).
- Inventory-driven probe set (Resolution B from prior status; rejected as too heavy for v0.1.2).
- Removing memory probe entirely (Resolution C from prior status; rejected — conflicts with v0.1.x story).
- Re-installing the live launchd plist on Luke's host (operator hygiene; out of fence; not relevant for this hazard).
- Renaming `memory_up` → `memory_expected` in the result-dict shape beyond what's needed for the not-expected case (downstream consumers may rely on `memory_up`; additive `memory_expected` field preserves compat).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
No new Claude-leverage shape. The change is internal to the session-start probe pipeline; the Claude-side `additionalContext` content becomes more honest (no false `memory: down` warning) which marginally improves the persona's confidence in its own diagnostic surface. Composes with future M-GMP plugin (v0.2) — when graphiti ships as a plugin and the user installs it, the plist appears, probing re-engages naturally with no further code change.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. Reduces stranger translation burden — strangers don't have to mentally translate "memory: down" into "I don't run graphiti, this is fine."
- **Harness test:** PASS. The probe primitive becomes more honest about its detection signal; the tool the persona draws from carries less false-alarm noise.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact helper signature, which sentinel string, where to gate the service-manager call) inferable from constraints. No "options to rule on" beyond the four resolutions enumerated in the prior status file (Resolution A locked by dispatcher).

### Lens 4 — Prompt scope ↔ confidence
Very high confidence in outcome shape: dispatcher ruled Resolution A explicitly; prior status file enumerated alternatives + recommendations. Tight scope. Method inferable from constraints + prior FBE.x sub-plan format precedent.

### Lens 5 — Swarming
V11.E is a leaf in the v0.1.2 release bundle. ACs partition lightly into (orchestrator probe site, gate probe site, smoke verification) but each binds to the same observable detection signal (plist existence) and the work is single-shell-session shape. No sub-decomposition; coordination overhead would exceed any tighter-AC payoff.

---

## 6. File-by-file map

### Source-side delta (in fence, post-`loam amend apply`):

**Component 1 — `framework/orchestrator/`:**
- `framework/orchestrator/scripts/pos_session_start.py` (~15–25 LOC):
  - Add `_is_memory_expected(launch_agents_dir, memory_label) -> bool` helper (mirrors `ask_service_manager_to_start`'s plist-check logic at line 162–164).
  - In `run_session_start`: before calling `pm()` for memory, check `_is_memory_expected`. If not expected: skip probe; treat as `m_ok=True`; record `memory_expected: False` in result dict; on the partial-status return, omit `memory_up=...` from `additional_context` and instead include `memory_expected=False`.
  - Optionally: short-circuit `ask_service_manager_to_start` for `memory_label` when not expected (reduces redundant warning text — Surface #4 decision).
- `framework/orchestrator/tests/test_pos_session_start.py` — add test covering the plist-absent branch (uses `tmp_path` for `launch_agents_dir`; injects via existing `service_manager_fn` parameter pattern OR via a new `is_memory_expected_fn` parameter for clean DI).

**Component 2 — `framework/primary-persona/`:**
- `framework/primary-persona/src/loam/primary_persona/session_start_gate.py` (~10–15 LOC):
  - In `_probe_memory(workspace_root)`: at function head, check `Path.home() / "Library" / "LaunchAgents" / "com.loam.memory-graphiti.plist"`. If absent: return `"not_expected"` immediately; skip the TCP-connect.
  - Add minimal docstring update to the function + `probe_service_state` (describe the new sentinel).
- `framework/primary-persona/tests/test_AC_V11_E_2_probe_memory_skips_when_plist_absent.py` — new test file; uses `monkeypatch` to redirect `Path.home` or use a parameterisable launchd dir (the simplest path: monkeypatch the resolved `Path.home() / "Library" / "LaunchAgents"`).

### Sidecar bumps within sealed-component fence (2 components):

- `framework/orchestrator/tests/SEAL_COMMIT` — advances from `1889db6` to V11.E seal SHA via `loam amend seal`.
- `framework/orchestrator/tests/test_no_sealed_amendments.py` — BASELINE literal advances from `"e7e7925"` to V11.E pre-apply tip via `loam amend apply`.
- `framework/orchestrator/tests/SEAL_COMMIT.notes` — narrative target.
- `framework/primary-persona/tests/SEAL_COMMIT` — advances from `8bec8f2` to V11.E seal SHA via `loam amend seal`.
- `framework/primary-persona/tests/test_no_sealed_amendments.py` — BASELINE literal advances from `"f14a5a4"` to V11.E pre-apply tip via `loam amend apply`.
- `framework/primary-persona/tests/SEAL_COMMIT.notes` — narrative target.

### Plan-doc + manifest (`universal_paths.prefixes: docs/rebuild/plans/`):

- `docs/rebuild/plans/v0-1-2-V11-E-graphiti-probe-skip.md` (this file).
- `docs/rebuild/plans/v0-1-2-V11-E-graphiti-probe-skip.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/rebuild/plans/v0-1-x-roadmap.md` — §8 method-decision register: add a V11.E subsection with apply commit SHA + seal commit SHA + verification summary; mark items (a) and (c) as "verified already-fixed at f0c4aa9 — no source delta required" (per prior V11.E status file recommendation).

**TOTAL fence diff:** 2 source edits (one .py per component) + 2 new test files + 4 sidecar bumps + 2 narrative files + plan-doc + manifest YAML + parent §8 backfill (universal prefix).

---

## 7. Smoke verification

**Smoke A — orchestrator probe site (pos_session_start), plist absent (AC.V11.E.1 + AC.V11.E.4):**

```bash
SMOKE_DIR=/tmp/v11e-smoke
rm -rf "$SMOKE_DIR"
mkdir -p "$SMOKE_DIR/empty-launchagents"

cd /Users/lukeivers/ivers-corp-pos-v2/
.venv/bin/python -c "
import sys
sys.path.insert(0, 'framework/orchestrator/scripts')
from pathlib import Path
import pos_session_start as p
def fake_pm(): return False, 0.0, 'ConnectionRefused'  # graphiti down
def fake_po(): return True, None  # orchestrator up
def fake_sm():
    return p.ask_service_manager_to_start(plat='macos', launch_agents_dir=Path('$SMOKE_DIR/empty-launchagents'))
# NEW: pass launch_agents_dir into the not-expected check
r = p.run_session_start(probe_memory_fn=fake_pm, probe_orchestrator_fn=fake_po,
                         service_manager_fn=fake_sm, platform_override='macos',
                         launch_agents_dir=Path('$SMOKE_DIR/empty-launchagents'),
                         bring_up_timeout_s=0.05, bring_up_poll_interval_s=0.01)
print('status:', r['status'])
print('memory_up:', r.get('memory_up'))
print('memory_expected:', r.get('memory_expected'))
print('exit_code:', r['exit_code'])
print('additional_context:', r['additional_context'])
"
```

Expect post-fix:
- `status: ready` (orchestrator up; memory not expected).
- `memory_expected: False`.
- `exit_code: 0` (no false alarm).
- `additional_context: pos v2 ready`.

**Smoke B — orchestrator probe site, plist present (AC.V11.E.4 — preserved behaviour):**

Synthesise plist presence by writing a stub file at `$SMOKE_DIR/present-launchagents/com.loam.memory-graphiti.plist`. Re-run with the same params, expect:
- Probe runs (memory_up=False because `fake_pm` returns False).
- `status: partial` or `ready` per existing logic.
- `additional_context` includes `memory_up=False`.

**Smoke C — gate probe site (session_start_gate), plist absent (AC.V11.E.2):**

```bash
.venv/bin/python -c "
import sys
sys.path.insert(0, 'framework/primary-persona/src')
from pathlib import Path
from unittest.mock import patch
from loam.primary_persona import session_start_gate as g
with patch.object(Path, 'home', return_value=Path('$SMOKE_DIR/empty-home')):
    state = g.probe_service_state(Path('$SMOKE_DIR/empty-home'))
print('memory:', state['memory'])
print('orchestrator:', state['orchestrator'])
"
```

Expect post-fix:
- `memory: not_expected`.

**Smoke D — gate probe site, plist present:**

Touch `$SMOKE_DIR/present-home/Library/LaunchAgents/com.loam.memory-graphiti.plist`; rerun with `Path.home()` returning that root; expect:
- `memory: down` (port 8765 unreachable in smoke env — TCP probe runs as today).

**Failure modes:**
- Smoke A returns `status: partial` post-fix → not-expected branch not engaged; halt + surface.
- Smoke C returns `down` post-fix → gate's plist check missed; halt + surface.
- Smoke B/D break pre-fix-behaviour parity → AC.V11.E.4 violated; halt + surface.

The smoke runs **pre-seal** to confirm the runtime contract before bookkeeping. Re-run post-seal is unnecessary (no source edits between).

---

## 8. Hard constraints

- 2 sealed-component sidecar bumps in fence (`framework/orchestrator/` + `framework/primary-persona/`).
- No new external runtime deps (uses stdlib `Path.exists`).
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply` AND per FIDRAFT entry: the apply step does NOT auto-commit by design — manual commit via `git commit -m "chore(amend): V11.E apply ..."`.
- AC-prefix `AC.V11.E.*` (collision-safe).
- Auto-memory `MEMORY.md` NOT touched.
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`: only `framework/orchestrator/tests/` + `framework/primary-persona/tests/` must pass post-seal.
- Smoke runs against isolated `tmp_path` directories (`/tmp/v11e-smoke/`); no live launchd state mutation; no `~/Library/LaunchAgents/` writes.

---

## 9. Out of scope (per ODD §2.5)

- Items (a) and (c) of original V11.E (verified already-fixed per prior status file).
- Workspace-config flag for memory provider (Resolution D; deferred).
- Inventory-driven probe set (Resolution B; rejected).
- Removing memory probe entirely (Resolution C; rejected).
- Renaming `memory_up` → `memory_expected` everywhere (additive `memory_expected` only).
- Other v0.1.2 items (ack-first persona, loam-amend ergonomics, gh-create→push race docs, two-copies hedge) — sequenced after V11.E per dispatcher.
- Re-installing the live launchd plist on Luke's host (operator hygiene; out of fence).
- Documentation updates beyond doc-comment / docstring on the touched functions.

---

## 10. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not silently extend) on:

- **HT-1:** Touched-files post-fix smoke fails any of §7 scenarios. Halt; surface; capture observation in status file.
- **HT-2:** `loam amend apply` rejects the manifest. Halt; surface; manifest shape may need adjustment or BASELINE pin is wrong.
- **HT-3:** `loam amend seal` rejects the seal. Halt; surface; usually means a touched-file lives outside the fence + universal admissions.
- **HT-4:** A file outside `framework/orchestrator/` + `framework/primary-persona/` + `docs/rebuild/plans/` shows non-sidecar diff post-seal. Halt; surface; AC.V11.E.S violation.
- **HT-5:** Surrounding-code ODD §2.5 violation discovered in any touched file. Halt; surface; do NOT silently extend or fix in-band.
- **HT-6:** Resolution A turns out to require touching components beyond the two named (e.g., `context_composer.py` schema needs a fourth admitted value). Halt; surface; widens fence per dispatcher's halt trigger.
- **HT-7:** Test breakage in either component beyond the touched files (existing test pins `_probe_memory` direct return to one of `up`/`down`/`unknown`). Halt; surface; the loose-AC-fix pattern (tighten the test, not the implementation) may apply but needs dispatcher confirmation.
- **HT-8:** Wall-time exceeds 60 min (dispatch hard cap). Halt with partial findings.
- **HT-9:** WD drifts to pos3. Halt immediately.
- **HT-10:** Sealed-component fence breach beyond the two named. Halt; surface.

---

## 11. Risks

- **Risk: existing test pins `_probe_memory` direct return to `down`/`up`/`unknown` only.** Mitigation: pre-grep `framework/primary-persona/tests/` for tests asserting on `service_state["memory"]` values; verify no test pins to a closed string set. Fallback: tighten the new sentinel to one of the existing accepted values (e.g., return `"unknown"` instead of `"not_expected"`) — but this loses the architectural-state visibility prior status file recommended.
- **Risk: downstream consumer of `pos_session_start` result dict assumes `memory_up` always present.** Mitigation: keep `memory_up: True` (interpret "skipped" as "not blocking") in the result dict for the not-expected case; add `memory_expected: False` as additive new field. Existing consumers see `memory_up: True` and don't false-alarm; new consumers can read `memory_expected` to distinguish.
- **Risk: `Path.home() / "Library" / "LaunchAgents"` is not parameterisable in `_probe_memory` and tests can't override cleanly.** Mitigation: add an optional parameter to `_probe_memory` defaulting to `Path.home() / "Library" / "LaunchAgents"`, OR use `monkeypatch.setattr(Path, "home", ...)` in the test (latter is the cheap path; former is the ODD-clean path).
- **Risk: `additional_context` text shape change breaks a downstream Claude prompt that was conditioning on the exact text.** Mitigation: this is a stranger-friction fix; the prior text was a false alarm; no downstream prompt should be conditioning on `memory_up=False` because that condition itself was wrong. Doc-noted in seal narrative.

---

## 12. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Source edits** in both files (within fence; per §6).
3. **New tests** in both components (within fence; per §6).
4. **Touched-only test rerun** — `pytest framework/orchestrator/tests/test_pos_session_start.py framework/primary-persona/tests/test_AC_V11_E_2_*.py`.
5. **Smoke run** — execute §7 smokes A/B/C/D; capture output to status file scratch.
6. **Source-edit commit** — `feat(v0.1.2): V11.E item (b) — graphiti probe graceful-skip via plist-existence` (or similar).
7. **Manifest commit** — author `docs/rebuild/plans/v0-1-2-V11-E-graphiti-probe-skip.manifest.yaml`.
8. **`loam amend apply`** — invoke against the manifest. Produces apply-bookkeeping changes (BASELINE bump in both `tests/test_no_sealed_amendments.py`).
9. **Manual apply commit** — `git commit -m "chore(amend): V11.E apply ..."`.
10. **`loam amend seal`** — produces deterministic seal commit; sidecar `SEAL_COMMIT` advances; narrative files written.
11. **Parent plan-doc backfill** — `docs/rebuild/plans/v0-1-x-roadmap.md` §8 backfill V11.E subsection (separate NEW commit; admitted via universal prefix).
12. **Status file write** — `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v11e-graphiti-probe-skip-status-2026-05-03.md`.

NO `git commit --amend` at any point. NO push to any remote.

---

## 13. References

- **Parent plan / programme master:** `docs/rebuild/plans/v0-1-x-roadmap.md` (§2 v0.1.2 item 2 + §8 register).
- **Prior V11.E status file (4-option matrix + Resolution A justification):** `<pos3>/workspace/.scratch/claude-output/v11e-followon-hazards-status-2026-05-03.md`.
- **V11.A sub-plan precedent (sub-plan format mirrored here):** `docs/rebuild/plans/v0-1-2-V11-A-orchestrator-fix.md`.
- **f0c4aa9** — predecessor commit closing items (a) and (c) of V11.E (verified pre-build).
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no source edit yet beyond the plan itself).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §12).
  - `feedback_subagent_odd_violation_halt` (HT-1 through HT-10).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to fence components only).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1–5 explicit; each surfaces a decision the dispatcher could review).
  - `feedback_specific_claims_verified_or_marked_guess` (every claim has a path/line citation or pre-build empirical observation).
  - `feedback_critical_thinking_on_deviations` (Surface #4 enumerates alternatives weighed by outcome × cost × risk).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (AC.V11.E.4's preserved-behaviour clause defends against scope creep).
  - `feedback_always_specify_wd_in_dispatches` (WD pinned at top: `/Users/lukeivers/ivers-corp-pos-v2/`).

---

## 14. AI-time band

- Predicted: **20–35 min, midpoint 27 min**; dispatch hard cap 60 min.
- Justification: per duration-estimation rubric — single-component-amendment band lower edge (the change is small + bounded + has direct tests), but spans two fence components which adds bookkeeping overhead. Compare to V11.A (~15 min observed for fence-one-no-edit + smoke) → V11.E adds source edits in both components + two new tests + double sidecar work, so 1.5–2× V11.A's wall-clock.

---

## 15. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Source-edit commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit (manual `chore(amend): V11.E apply ...`): `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of V11.E sub-plan-doc. Ready to build.*
