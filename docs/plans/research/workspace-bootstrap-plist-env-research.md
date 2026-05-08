# Research — workspace-bootstrap plist env vars (D5)

**Research cycle:** D5.
**Governing research plan:** `docs/plans/research/workspace-bootstrap-plist-env-research-plan.md` (Q1–Q5, halt triggers §4).
**Authored:** 2026-04-24 in a read-only background agent against the canonical `/Users/lukeivers/ivers-corp-pos-v2/` tree. Empirical probes used unique sandbox labels (`com.loam-research.plist-env-probe-*`) with bootout-in-teardown; no mutation of currently-registered services.
**Host probed:** Darwin 25.3.0 (kernel `xnu-12377.81.4~5`), macOS 26.3 (build 25D125), arm64, uid 501, launchctl managername `Aqua` (gui domain).
**Halts:** none fired. The four halt triggers (second sealed component, method-in-AC forced, launchd-inheritance as root cause, ODD break) were evaluated and none applies. See §6 for the halt-check narrative.

---

## Executive summary

1. Only **PATH** is materially missing from the scaffold-emitted plist on macOS 26.3 Tahoe. Probes A and C confirm `USER`, `HOME`, `LOGNAME`, `SHELL`, `TMPDIR` are injected into the spawned process's live `environ` by launchd's gui-domain session context even when the plist omits them.
2. `launchctl print`'s `environment =` block misleads: it shows plist-declared `EnvironmentVariables` plus launchd-internal vars (OSLogRateLimit, XPC_SERVICE_NAME) — it does NOT show the session-injected USER/HOME/LOGNAME/SHELL/TMPDIR that the process actually sees. The research plan's §1 framing ("launchctl print showed inherited environment = { }") reflects that display artefact, not the process-actual env.
3. Probe B (PATH+USER+HOME) and Probe C (PATH alone) both resolve `claude` and execute `claude --version`. Supplying only PATH is functionally sufficient.
4. Both scaffold-emitted plists (memory-graphiti AND orchestrator) share the same emission template shape — same gap, same candidate fix. But the orchestrator has no verified end-to-end requirement for `claude` on its PATH; its need is unverified-but-likely.
5. D5 composes with D4. D4 widens the env-scrubber allowlist (USER) so the parent env's USER survives into the `claude -p` subprocess; D5 widens what the plist emits (PATH) so the parent has a usable PATH. The union of both is what makes `/health` → 200 end-to-end. Either alone fails in a distinguishable way.
6. **Candidate amendment shape surfaced for owner ruling:** narrow PATH-only plist widening with an inline helper `_launchd_path()` that returns the scaffold-resolved PATH string, plus a single end-to-end seal test that loads the emitted plist via `launchctl` in a sandboxed gui domain and polls `/health`. Broader alternatives (also emitting USER/HOME/LOGNAME "defensively," or a more elaborate integration-test harness) are listed in Q4 with trade-offs.

---

## Q1 — Minimum env vars the plist must emit

### Claim

On macOS 26.3 Tahoe under launchd's `gui/<uid>` domain, the plist must emit **only PATH** (in addition to the existing `PYTHONUNBUFFERED=1`) to satisfy memory-graphiti's end-to-end `/health` → 200 contract. `USER`, `HOME`, `LOGNAME`, `SHELL`, `TMPDIR` are supplied by launchd's session context and need not be emitted. `TMPDIR` and `LANG` are unneeded by any current code path; neither was observed as a requirement.

### Evidence

**Probe A — minimal plist (matches current scaffold emission exactly).** Plist declared `EnvironmentVariables = { PYTHONUNBUFFERED: 1 }`. Spawned process ran `env; command -v claude`. Live process env:

```
PYTHONUNBUFFERED=1
USER=lukeivers
SSH_AUTH_SOCK=/private/tmp/com.apple.launchd.pxsLdVDFLI/Listeners
PATH=/usr/bin:/bin:/usr/sbin:/sbin
HOME=/Users/lukeivers
LOGNAME=lukeivers
SHELL=/bin/zsh
TMPDIR=/var/folders/.../T/
XPC_FLAGS=0x0
XPC_SERVICE_NAME=0
OSLogRateLimit=64
claude_path=                      ← empty; `claude` not resolvable
```

`claude` is at `/Users/lukeivers/.local/bin/claude` on this host (`command -v claude` from the interactive session). Not on launchd's default `PATH`; `command -v` fails.

**Probe B — plist with PATH+USER+HOME (the pos3 manual mitigation).** Same probe script, plist-declared EnvironmentVariables adds PATH (user's expanded), USER, HOME. Live process env has user PATH; `command -v claude` returns `/Users/lukeivers/.local/bin/claude`; `claude --version` returns `2.1.119 (Claude Code)`.

**Probe C — plist with PATH only (no explicit USER/HOME).** Same script. Live process env still shows `USER=lukeivers`, `HOME=/Users/lukeivers`, `LOGNAME=lukeivers`, `SHELL=/bin/zsh`, `TMPDIR=...` — all auto-inherited from launchd gui-domain session context. `command -v claude` returns `/Users/lukeivers/.local/bin/claude`; `claude --version` succeeds. **PATH-only is sufficient.**

**Cross-check — currently-running `com.pos-v2.ivers-corp-pos-v2.orchestrator` service.** Its plist (unedited scaffold output) declares only `PYTHONUNBUFFERED=1`. `ps -E -p <pid>` for PID 99175 returns:

```
PYTHONUNBUFFERED=1
XPC_SERVICE_NAME=com.pos-v2.ivers-corp-pos-v2.orchestrator
PATH=/usr/bin:/bin:/usr/sbin:/sbin       ← launchd default
LOGNAME=lukeivers
USER=lukeivers
HOME=/Users/lukeivers
SHELL=/bin/zsh
TMPDIR=/var/folders/.../T/
```

Same pattern: USER/HOME/LOGNAME/SHELL/TMPDIR inherited from launchd session; only PATH is deficient.

**Chain-of-causation in `ClaudePrintLLMClient.__init__`** (memory-system/src/claude_print_client.py:322): `shutil.which("claude")` runs in the service's parent process (not the scrubbed subprocess). That `shutil.which` searches the parent's `PATH`. Under the current plist, parent `PATH` is launchd's default `/usr/bin:/bin:/usr/sbin:/sbin`; `claude` does not resolve; `ClaudeBinaryMissingError` (-32110) raised at construction; memory-graphiti service fails to reach `/health`.

### Implication for the amendment plan

- The narrow minimum emission is PATH. The amendment may choose to emit only PATH, or to additionally emit USER/HOME/LOGNAME defensively. That choice is a method decision for the plan; both shapes satisfy the end-to-end contract.
- The scaffold needs a resolver for "what PATH string to emit." Options the plan will rule on (not ruled here): freeze a literal based on the scaffold-author's shell (brittle across hosts), read from `$PATH` of the scaffold-invoking process (non-deterministic under the first-run hook that itself runs under scrubbed env), compose a canonical list (`~/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin` or similar) as the scaffold emits, or allow `memory.yaml` to carry a user-overridable PATH. The canonical-list option aligns with both pos3's mitigation and the `ClaudePrintLLMClient._build_child_env` default (`/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin`). A single source of truth for "the PATH the scaffold trusts" is the cleanest composition.
- TMPDIR and LANG were not required; no evidence of a current requirement. Do not emit them in the minimum fix.

---

## Q2 — Env-var gap in the orchestrator plist

### Claim

The orchestrator plist shares the same PATH-only gap as memory-graphiti. But the orchestrator has no verified current code path that requires `claude` on its PATH. The gap is latent, not currently-biting. Whether to fix both plists in one amendment or to scope only memory-graphiti is an owner ruling — the orchestrator's status is "same template, same latent gap, no confirmed failure today."

### Evidence

**Both templates are identical shape.** `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py:488–532` defines `_LAUNCHD_TEMPLATES` as a dict of two templates, both ending with the same `<key>EnvironmentVariables</key><dict><key>PYTHONUNBUFFERED</key><string>1</string></dict>` line (lines 506 and 528). Same gap.

**Orchestrator's current runtime dependencies.** `ProgramArguments` launches `{workspace}/.venv/bin/python -m pos_orchestrator` against `{workspace}` as CWD. The orchestrator module tree does not directly invoke `claude -p` or any binary outside its own venv. Memory-system is the only confirmed consumer of the `claude` binary on the service's own PATH today (amendment #8 `ClaudePrintLLMClient`).

**Orchestrator uses UNIX sockets, not HTTP.** Cross-referenced against research plan §2.2 framing. No `/health` contract to fail against on the orchestrator side — its liveness surface is different (supervisor probe, not HTTP). The research plan's question about whether the orchestrator "may not spawn scrubbed-env subprocesses" is answered: today, no confirmed scrubbed-subprocess spawns from the orchestrator process.

**Future latent paths.** Any future orchestrator adapter that shells out to `claude` (e.g., a future LLM-routed specialist in the orchestrator's own process tree) would hit the same `shutil.which("claude")` failure class. The orchestrator plist's PATH gap is a latent hazard of the same class, not an active failure today.

### Implication for the amendment plan

- Two candidate scopes for the plan to choose between:
  1. **Memory-graphiti only.** Tight scope; fixes the currently-biting defect. Orchestrator remains on latent-gap status; a future amendment closes it if/when an orchestrator-side path trips the same failure.
  2. **Both plists, shared helper.** Factor the env-var emission into a helper that both templates consume. The orchestrator plist gains PATH emission for parity. Slightly wider scope; closes the latent hazard proactively.
- The second option composes cleanly with §2.5 ODD (the helper's output maps 1:1 to an AC that exercises emission for both plists). The first option is narrower and ships faster. Both are ODD-legitimate; the choice is a budget/safety-margin judgement the plan will name.
- Emitting PATH for both services has no side effects on orchestrator's current operation (orchestrator doesn't care about PATH; launchd's default satisfies everything orchestrator currently does) but closes the latent failure class.

---

## Q3 — USER inheritance vs explicit emission

### Claim

The research plan's framing ("`launchctl print` showed `inherited environment = { }`") reflects a display artefact of `launchctl print`, not the spawned process's actual env. On macOS 26.3 Taheahe (and consistent with documented launchd gui-domain behaviour), USER/HOME/LOGNAME/SHELL/TMPDIR ARE inherited from the launchd session context into the spawned process's `environ` even when the plist does not emit them. `inherited environment` in `launchctl print` names a different, narrower concept — the set of env vars launchd forwards from the process that called `launchctl bootstrap`, which is nearly empty (SSH_AUTH_SOCK and similar). Session-context injection is separate and happens later in the exec path.

Explicit emission of USER/HOME/LOGNAME is therefore defensive duplication, not a load-bearing fix. It does no harm (launchd plist values override session defaults when both are set), but it is not required for the memory-graphiti defect as observed.

### Evidence

**`launchctl print` output for `com.pos-v2.ivers-corp-pos-v2.orchestrator`** (plist declares only PYTHONUNBUFFERED):

```
inherited environment = {
    SSH_AUTH_SOCK => /private/tmp/com.apple.launchd.pxsLdVDFLI/Listeners
}
default environment = {
    PATH => /usr/bin:/bin:/usr/sbin:/sbin
}
environment = {
    OSLogRateLimit => 64
    PYTHONUNBUFFERED => 1
    XPC_SERVICE_NAME => com.pos-v2.ivers-corp-pos-v2.orchestrator
}
```

**`ps -E -p 99175`** on the same live service process shows the ACTUAL environ:

```
PYTHONUNBUFFERED=1
XPC_SERVICE_NAME=com.pos-v2.ivers-corp-pos-v2.orchestrator
PATH=/usr/bin:/bin:/usr/sbin:/sbin
LOGNAME=lukeivers
USER=lukeivers
HOME=/Users/lukeivers
SHELL=/bin/zsh
TMPDIR=/var/folders/.../T/
```

The three blocks in `launchctl print` (`inherited environment`, `default environment`, `environment`) partition a narrow view: the `environment =` block is effectively "plist-declared plus launchd-internal." The six session-context vars (USER/HOME/LOGNAME/SHELL/TMPDIR/… via loginwindow) do not appear in any of the three blocks but ARE present in the spawned process's environ. The research plan's §1 observation ("USER was NOT set") is reading from the display surface; the process-actual env has USER.

**Probe C confirms at the isolation boundary.** A freshly-bootstrapped test service with only `PYTHONUNBUFFERED=1` and `PATH=...` in its EnvironmentVariables — with NO USER/HOME declared — shows `USER=lukeivers`, `HOME=/Users/lukeivers`, `LOGNAME=lukeivers`, `SHELL=/bin/zsh` in the spawned process's `env` output.

**Halt-trigger check (research plan §4.3).** The plan's third halt trigger fires if "launchd's inheritance behaviour turns out to be the root cause (i.e., explicit emission is a workaround and the real fix is a launchd config change)." Evaluated: no. Launchd's inheritance behaviour is functioning correctly on this host — USER/HOME DO inherit from session context. The actual gap is PATH, which launchd deliberately does NOT inherit from user-shell context (PATH uses launchd's `default environment` of `/usr/bin:/bin:/usr/sbin:/sbin`). Emitting PATH is not a workaround for a launchd bug; it is the sanctioned mechanism for overriding launchd's intentionally-minimal default PATH. **Halt trigger does not fire.**

### Implication for the amendment plan

- The plan may choose to emit USER/HOME/LOGNAME defensively (belt-and-suspenders against hypothetical future macOS versions where session-context injection changes) or to rely on inheritance (narrow, matches actual current behaviour). Either is ODD-legitimate. The defensive option widens the AC surface without widening the contract's guarantees; the narrow option keeps the AC scope tight.
- Recommend the plan document why it chose narrow-or-defensive. The research's finding is that narrow is currently sufficient; defensive is a risk-tolerance judgement.
- The D4 research cycle's question 2.1 ("what env vars does claude -p require under macOS launchd") may conclude USER is required in the scrubber's allowlist. That is a separate surface — the scrubber runs inside the memory-graphiti service process and reads from its environ. Whether USER arrives in that environ via session-inheritance (as observed) or via plist emission (defensive), D4's USER-allowlist widening is the valid fix at the scrubber surface. D5's plist surface only needs PATH.

---

## Q4 — Test shape for "emitted plist reaches /health OK end-to-end"

### Claim

The test-shape question has three candidates with sharply different ODD profiles. The narrow shape — **plist-shape validator that confirms PATH is present in the emitted EnvironmentVariables dict** — is unit-level and deterministic but does not assert end-to-end `/health` reachability. The strong shape — **B18-equivalent integration test that loads the emitted plist via a real `launchctl bootstrap` in a sandboxed gui domain and polls `/health`** — is end-to-end but requires either a real launchctl (non-portable; macOS-host-only; CI-hostile) or a fake-launchctl harness (method-heavy). A third middle shape — **scaffold-emits-then-parses-back plist + spawn-a-subprocess-directly-with-that-env-and-probe-claude-resolution** — asserts the emission is load-bearing for PATH resolution without invoking launchctl.

Each shape has a clean ODD framing that avoids method-in-AC as long as the AC names the observable outcome (emission contains PATH; claude resolves; /health returns 200) rather than the mechanism (subprocess.run vs launchctl vs python test harness).

### Evidence

**B18 precedent applies structurally, not literally.** The workspace-bootstrap proposal's B18 asserts "Synthetic Phase 4 contribution... framework discovers, validates, orders, and invokes `contribute(host)`" — a test that exercises the real protocol via the public surface. The B18 analogue for D5 would be: scaffold emits the plist, launchctl loads it, the service comes up, /health responds 200. That IS a well-formed ODD AC (outcome: /health → 200 after scaffold emission). The method-in-AC risk lives at the next level down: if the AC prose says "uses launchctl" or "uses subprocess.run" or "parses the plist via xml.etree," that's method leakage. The AC text can be "the emitted plist, when loaded into launchd's gui domain, produces a running service whose /health returns 200 within the configured startup timeout" — outcome-shaped, method-unspecified.

**Current test surface** — `workspace-bootstrap/tests/test_first_run_scaffold.py::test_H1_fresh_first_run_writes_all_yamls` (lines 45–81) asserts plist files exist and their stem-names match expected labels. It does NOT parse the plist content. No current test would have caught the "PATH missing from EnvironmentVariables" defect at seal time. Similarly, `test_AC4_bootout_precedes_bootstrap_on_macos` asserts launchctl invocation order but passes `<plist/>` as a string — no assertion about emitted env vars reaching the service.

**Probe-level evidence that real launchctl in a sandbox is feasible.** Probes A, B, C all ran `launchctl bootstrap gui/$uid <plist>` against unique test labels (`com.loam-research.plist-env-probe-*`), bootout-in-teardown, StdOutPath pointed at a sandbox `/tmp/...` file, 2-second sleep then read log, then bootout. No residue; no collision with currently-registered services. On the developer's own host this takes ~3 seconds per probe. In CI it requires a macOS runner with a gui/aqua session available (GitHub Actions macOS runners typically run in a session that supports `launchctl bootstrap gui/<uid>` — verified as a reasonable assumption, not probed).

**Three candidate test shapes, with ODD profiles:**

| Shape | Outcome asserted | ODD AC text (candidate) | Method-in-AC risk | Portability |
|-------|------------------|-------------------------|-------------------|-------------|
| **Unit: plist-content assertion** | The emitted plist declares PATH in its EnvironmentVariables dict. | "The scaffold's emitted plist, when parsed back from disk, declares a non-empty PATH in its EnvironmentVariables dictionary." | Low (method-agnostic on how parsing happens) | High; pure Python |
| **Mid: subprocess-with-emitted-env** | Given the plist's EnvironmentVariables dict as a Python dict, a subprocess spawned under that env resolves `claude` via `shutil.which`. | "A subprocess spawned with the scaffold-emitted plist's EnvironmentVariables dict as its environ can resolve the `claude` binary via PATH." | Low; the test's HOW is subprocess which is not prescribed by the AC | Medium; requires claude binary on the test host |
| **Strong: real-launchctl integration** | A bootstrap-then-bootout of the emitted plist produces a service whose /health endpoint returns 200 within a timeout. | "Bootstrapping the scaffold-emitted plist into launchd's gui domain brings up a memory-graphiti service that reaches /health → 200 within the memory.yaml startup_timeout_s." | Low if AC prose stays outcome-shaped; high if prose specifies launchctl/bootout/curl | Low; macOS + claude + venv + running service required |

**Method-in-AC halt-trigger check (research plan §4.2).** None of the three shapes forces method-in-AC as the only way to prove emission. All three admit outcome-shaped AC prose. **Halt trigger does not fire.**

### Implication for the amendment plan

The plan will make the shape decision. Research ruling-of-record:

- The **unit shape** is the minimum bar. It catches the specific defect at seal time (PATH missing from EnvironmentVariables would be a failed parse-back) at zero cost. It does NOT prove the emitted PATH is operationally usable.
- The **mid shape** is the best cost/guarantee ratio. It adds ~one test function that uses the plist's declared env to spawn a subprocess, then asserts `shutil.which("claude")` succeeds inside that subprocess. It catches both "PATH missing" and "PATH present but wrong" (e.g., PATH declared but pointing at nonexistent dirs). It does not require launchctl. It requires `claude` to be installed on the test host — acceptable in the canonical-tree test environment; may need a skip-marker for CI hosts without claude.
- The **strong shape** is the B18-equivalent. It catches everything the mid shape does, PLUS proves the full launchd → memory-graphiti → /health path actually works end-to-end. It requires launchctl, a gui-domain session, and the full service stack. Reasonable on the developer host; fragile in CI. Suggest pairing with a pytest marker (`@pytest.mark.integration` or similar) that lets the developer opt-in locally and have CI skip by default.
- A plausible plan: mid shape as the load-bearing seal test; strong shape as an optional marker-gated integration test for local developer assurance. Unit shape subsumed by the mid shape's plist parse-back.

---

## Q5 — Composition with D4 (env-scrubber allowlist widening)

### Claim

D4 and D5 are necessary-but-not-sufficient-alone; their union closes the defect. D4 widens the subprocess scrubber `_ENV_ALLOWED_VARS` to include USER (and possibly LOGNAME) so that `claude -p`'s OAuth keychain lookup resolves. D5 widens the plist's EnvironmentVariables to include PATH so that the memory-graphiti service's `shutil.which("claude")` at construction resolves. These operate on two different surfaces (parent-process env vs subprocess env) and fail at two different points in the chain. The failure modes are distinguishable:

- **D5 alone (no D4):** memory-graphiti service constructs successfully (PATH present → `claude` resolves at `shutil.which`), but every LLM call from the subprocess returns "Not logged in · Please run /login" because the scrubber drops USER before spawning `claude -p`. Failure surface: ingest calls fail at runtime, not at `/health`. `/health` → 200 passes; actual work does not.
- **D4 alone (no D5):** `ClaudePrintLLMClient.__init__` fails at construction with `ClaudeBinaryMissingError` (-32110) because `shutil.which("claude")` returns None under launchd's default PATH. Service process crashes before reaching `/health`. D4's widened allowlist never gets exercised — the process dies upstream.
- **Both D4 and D5:** parent env has PATH (via plist) and USER (via launchd session injection); scrubber passes both through to `claude -p`; OAuth keychain resolves; `/health` → 200; ingest calls succeed.

The composition is structurally tight: both widenings are required. Neither subsumes the other. The amendments can ship in either order — the first to land partially-improves behaviour (D5 first: /health passes but ingest fails with auth error; D4 first: nothing changes because the service still can't construct). Shipping them as sibling amendments in the same cycle is cleaner UX but not mechanically required.

### Evidence

**D4's allowlist surface — `claude_print_client.py:86–89`:**

```python
_ENV_ALLOWED_VARS = (
    "PATH",
    "HOME",
)
```

D4's likely widening (per the D4 research plan §2.1, empirically-bisected claim): add `USER`. The subprocess scrubber at `_build_child_env` (line 200) copies only allow-listed vars from `parent_env` to the `claude -p` subprocess. USER missing from the allowlist → USER missing from the subprocess env → OAuth keychain lookup fails → "Not logged in" marker.

**D5's plist surface — `first_run_scaffold.py:488–532`:**

```
<key>EnvironmentVariables</key><dict><key>PYTHONUNBUFFERED</key><string>1</string></dict>
```

D5's widening (this research's finding): add `PATH`. The plist's EnvironmentVariables populates the SERVICE PROCESS's env. The service process is the parent of the `claude -p` subprocess. Without PATH in the service process, `shutil.which("claude")` at construction returns None.

**Confirmation from pos3's manual mitigation.** The pos3 clone at `/Users/lukeivers/pos3` has its plist manually edited (see `/Users/lukeivers/Library/LaunchAgents/com.pos-v2.pos3.memory-graphiti.plist`, observed) to include PATH+USER+HOME. The pos3 session's `ClaudePrintLLMClient` constructs successfully (PATH → claude resolves). But the `_ENV_ALLOWED_VARS` scrubber still drops USER → every `claude -p` returns "Not logged in." The pos3 session observed this as the bisect signal D4's research plan cites. PATH-fix-alone (D5 without D4) reproduces exactly this pos3 observation.

**Failure mode not obvious from either amendment alone.** A reader of only D4's plan might assume PATH-to-claude is already handled because the scrubber sets `env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin")` at `_build_child_env:215`. But that default applies to the SUBPROCESS's PATH, not the parent process's PATH. The parent's `shutil.which("claude")` runs BEFORE the subprocess is spawned; it reads `os.environ["PATH"]` from the parent. The setdefault does not reach that check.

**Non-launchd contexts (research plan §2.5).** The research plan asks about "users who have non-launchd contexts that invoke the service directly." If a developer runs `python -m src.service` from an interactive terminal, the parent process inherits the terminal's PATH + USER, and neither D4 nor D5 is needed (both surfaces already have what they need). This non-launchd path is already functional today; it is the reason the defect was not caught in developer-laptop testing. The D5 amendment does not regress this path (the plist is only consulted by launchd; an interactive invocation never reads the plist).

### Implication for the amendment plan

- Name the composition explicitly in the D5 plan's §3 context narrative: "D5 fixes the parent-process PATH surface; D4 fixes the subprocess USER surface; the union is required for end-to-end OAuth resolution."
- The D5 amendment plan does not need to block on D4. But the D5 seal test's shape interacts with D4: if the seal test is the **strong shape** (real launchctl + /health poll), it ALSO indirectly exercises whether OAuth calls from the service succeed — which means a D5 seal test could fail even with D5 correctly fixed if D4 has not landed. The mid shape (subprocess spawned with plist env; assert `shutil.which("claude")` resolves) avoids this entanglement by scoping to the PATH surface only.
- If D4 is expected to land first (or concurrently), the strong-shape end-to-end test is fine. If D5 lands first (D4 still pending), the mid-shape is safer to avoid a D5 seal test that red-flickers on the independent D4 defect. The plan should name this sequencing explicitly.
- A separate seal test for "the emission+scrubber union delivers end-to-end ingest success" would naturally live in memory-system's test tree (the component whose contract is "ingest calls succeed via claude -p"), not workspace-bootstrap's. That test is a D4-or-later concern, not a D5 concern.

---

## 6. Halt-trigger review

| Trigger (plan §4) | Evaluated | Fires? |
|---|---|---|
| Second sealed component beyond workspace-bootstrap needs touching | D5 is a workspace-bootstrap-only amendment surface (plist emission lives in `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`). Seal-test placement is workspace-bootstrap. D4 is a separate amendment on memory-system; they do not share source surfaces. | **No.** |
| Method-in-AC required | Q4 identified three test shapes, all admitting outcome-shaped AC prose. No shape forces method-in-AC. | **No.** |
| Launchd inheritance is the root cause (explicit emission is a workaround) | Q3 evidence: launchd inheritance works correctly on macOS 26.3 Tahoe for USER/HOME/LOGNAME/SHELL/TMPDIR. The gap is PATH, which launchd deliberately does not inherit from user shells (intentional default-env behaviour). Explicit PATH emission is the sanctioned mechanism, not a workaround. | **No.** |
| ODD break strongly required | The candidate amendment shapes (Q4) all admit ODD-clean AC framing. No shape requires a §2.4 or §2.5 violation. | **No.** |

All four triggers evaluated; none fires.

---

## 7. Candidate amendment shape (for owner ruling)

Surfaced here as a single candidate shape that honours the ODD framing; the amendment plan commits to a shape once the owner rules.

- **Scope:** D5 is workspace-bootstrap-only. Sealed-component surface touched: `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` (the two `_LAUNCHD_TEMPLATES` entries) plus `workspace-bootstrap/tests/test_first_run_scaffold.py` (new AC test functions). Seal-diff impact: workspace-bootstrap only.
- **Emission shape (narrow):** add `PATH` to both `_LAUNCHD_TEMPLATES` entries. Derive the PATH string from a helper (single source of truth); candidate helper body mirrors `ClaudePrintLLMClient._build_child_env`'s setdefault (`~/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin`) or allows `memory.yaml`-overrides. Method decision for the plan.
- **Test shape (recommended mid):** parse back the emitted plist, extract the `EnvironmentVariables` dict, spawn a subprocess under that env, assert `shutil.which("claude")` resolves. One test function per ACdeclared behaviour. Optionally add a `@pytest.mark.integration` strong-shape end-to-end test for developer-laptop assurance.
- **Composition:** D5 sibling to D4; both land cleanly in either order. Name the composition in the plan's context section.
- **Re-extension check:** the current H1 test in workspace-bootstrap asserts plist existence but not plist content. If the plan adds a new AC for emission-content-correctness, it is a re-extension under ODD §4 — name it as such in the plan.
- **Orchestrator plist scope (open for owner):** include in the same amendment (shared helper, both plists emit PATH) or defer to a future cycle. Research finding: no biting defect on orchestrator today; latent same-class hazard; the symmetric fix via shared helper is low-cost, but the narrower fix-memory-graphiti-only is also ODD-legitimate. Owner rules.

---

*End of research document. ~400 lines, per cap. No source edits, no commits, no mutations to currently-registered launchd services. Sandbox labels `com.loam-research.plist-env-probe-*` used bootout-in-teardown; all test artefacts removed.*
