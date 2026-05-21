# Amendment — workspace-bootstrap plist PATH emission (D5)

**Amendment number:** unassigned (assigned at build-dispatch time per owner
ruling 2026-04-24). BASELINE (pre-amendment tip) pinned at dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-24.
**Research plan:** `docs/plans/research/workspace-bootstrap-plist-env-research-plan.md`.
**Research doc:** `docs/plans/research/workspace-bootstrap-plist-env-research.md`.
**Sibling cycle:** D4 (memory-system env-scrubber allowlist widening) —
disjoint sealed surface; see research Q5 composition narrative.

## Owner-ruling summary (2026-04-24)

1. **PATH-only plist emission.** Narrow. `USER` / `HOME` / `LOGNAME` /
   `SHELL` / `TMPDIR` are injected by launchd gui-domain session
   context even when omitted (research Q1 + Q3); no defensive emission.
2. **Both plists fixed alongside.** `memory-graphiti` and `orchestrator`
   emit from the same template shape (research Q2). Orchestrator has
   no verified `claude` dependency today; the fix is cheap and closes
   the latent same-class gap.
3. **Seal-test shape: B18-pattern end-to-end.** One end-to-end test
   loads the emitted plist via `launchctl` into a sandboxed gui-domain
   label and polls `/health` → 200. The test exercises the protocol,
   not plist XML string equality.
4. **Component scope: workspace-bootstrap primary.** If the sandbox-
   launchctl test fixture requires a hands-off-lifecycle helper
   extension, hands-off-lifecycle joins the manifest (frozen BASELINE
   per amendment #23). Builder's call, halt per §8 if larger than a
   test fixture.

## 1. Objective

Fresh-clone first-run scaffolds launchd plists whose spawned services
reach their declared liveness surface end-to-end without manual plist
editing. The `memory-graphiti` service's `/health` endpoint returns 200
under the scaffold-emitted plist; the `orchestrator` plist emits from
the same template shape and closes the latent PATH-resolution hazard
on the shared template surface.

Two behaviours; AC-count maps in §5.

## 2. Hard constraints

1. **Dependency fence.** Amends `workspace-bootstrap/` source + tests.
   Sealed components off-limits: memory-system, orchestrator,
   safety-layer, reversibility-primitive, cost-governance,
   self-correction, graceful-degradation, scope-of-work,
   objective-tracker, primary-persona, observability-aggregator,
   self-upgrade, telegram-interface. `hands-off-lifecycle/` is
   permitted **only** as a test-fixture helper extension (§8 halt
   trigger names the cross into source).
2. **Reversibility.** Fully reversible.
3. **Authority bound.** Owner rulings in §Owner-ruling-summary are
   binding scope. The PATH-string-resolution helper shape, the
   plist parse-back mechanism, and the sandbox-launchctl fixture
   mechanics are method — builder's call.
4. **Fail-closed direction.** A plist omitting `PATH` must not reach
   green in any seal-test path. Marker-gated integration fallback
   triggers §8 halt first.
5. **No `--amend`.** Corrective commits only if something misses.
6. **Amendment-dispatch CDC speedups.** Full suite runs only for
   touched components; untouched get seal-diff-only. No pre-seal
   full rerun. Methodology snippets inline in the dispatch prompt.
7. **`pos-amend apply --dry-run` green** is a hard prereq for the
   amendment commit (amendment #22).
8. **No new runtime deps.** Test deps only.
9. **Preserve existing scaffold contracts.** Label shape, filename
   shape, bootout-before-bootstrap order, KeepAlive/ThrottleInterval/
   StandardOutPath semantics, and `PYTHONUNBUFFERED=1` remain intact.
   The amendment only widens `EnvironmentVariables` to add `PATH`.

## 3. Acceptance criteria

Each criterion maps 1:1 to a test function in the build. Criterion IDs
use the `D5` prefix to distinguish this amendment's new criteria from
workspace-bootstrap's B-series proposal criteria.

### D5.1 — memory-graphiti emitted plist reaches /health end-to-end

Given a fresh scaffold invocation against a sandbox workspace, the
emitted memory-graphiti plist — when loaded into launchd's gui domain
under a sandbox-unique label and started — produces a service whose
`/health` endpoint returns HTTP 200 within the service's configured
startup timeout. Teardown bootouts the sandbox label regardless of
test outcome.

Outcome asserted: end-to-end liveness under scaffold-emitted plist.
Method (launchctl bootstrap, polling shape, timeout value, temp-label
choice) is builder's call.

### D5.2 — orchestrator emitted plist carries the same PATH emission

The scaffold-emitted orchestrator plist's `EnvironmentVariables` dict
declares a non-empty `PATH` string identical in derivation to the
memory-graphiti plist's PATH emission (same helper, same output). The
outcome observable is parse-back equivalence, not XML string equality.

Outcome asserted: both plists carry the same PATH resolution, closing
the latent-same-class hazard named in research Q2.

### D5.3 — env emission surfaces are exactly the amendment-declared sets

After this amendment, each emitted plist's `EnvironmentVariables` dict
contains exactly the keys that prior amendments + this amendment's
widening have authorised — no more, no less. The sets are declared
per-plist because amendment #29 added workspace-identity and
memory-host/port env vars to the memory-graphiti plist only (the
orchestrator plist uses UNIX-socket probes, not HTTP /health with
workspace identity, so it did not receive those additions).

Memory-graphiti plist's `EnvironmentVariables` contains exactly:
`{PYTHONUNBUFFERED, GRAPHITI_SERVICE_HOST, GRAPHITI_SERVICE_PORT,
POS_V2_WORKSPACE_ROOT, PATH}` — five keys. The first four are
established by amendment #29 (AC29.1 port binding + AC29.5 workspace
identity); this amendment adds PATH.

Orchestrator plist's `EnvironmentVariables` contains exactly:
`{PYTHONUNBUFFERED, PATH}` — two keys. Amendment #29 did not extend
orchestrator's env (no workspace-identity need; UNIX-socket probe);
this amendment adds PATH alongside the pre-existing PYTHONUNBUFFERED.

No defensive USER / HOME / LOGNAME / SHELL / TMPDIR emission for
either plist (research Q3 ruling; those vars are injected by launchd
gui-domain session context). Any additional key in either dict
without a named AC in a later amendment triggers this test's fail
branch. This is the structural anti-creep guard.

Outcome asserted: each plist's emission surface is exactly the
amendment-declared set for that plist kind.

### D5:S — seal diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows only paths under
`workspace-bootstrap/`, plus the amendment's plan + manifest +
research docs under `docs/plans/`, plus universal-paths
admissions (`CLAUDE.md`, `docs/odd-in-pos.md`,
`docs/odd-methodology.md`, `docs/FUTURE_IDEAS.md`). If
hands-off-lifecycle joins the manifest (per §Owner-ruling #4),
`hands-off-lifecycle/tests/` fixture paths are also admitted.
Anything outside that set is a halt condition.

## 4. Behaviour-count check

| Behaviour (§1 objective) | Criteria |
|---|---|
| memory-graphiti /health reaches 200 under scaffold-emitted plist | D5.1 |
| orchestrator plist emits from same shape (latent-gap closure) | D5.2 |
| PATH-only widening this amendment (narrow-scope guard; exact per-plist key sets) | D5.3 |
| Seal discipline | D5:S |

Three behaviours in §1 + seal-discipline → four criteria. Every
behaviour covered.

## 5. Implementation order (suggested; builder's call)

1. Manifest: `docs/plans/amendment-<N>-workspace-bootstrap-plist-path.manifest.yaml`.
2. Pre-amendment captures: `workspace-bootstrap/` full suite (and
   hands-off-lifecycle if it joins); seal-diff-only for the rest.
3. Author the PATH-string helper (single source of truth).
4. Widen both `_LAUNCHD_TEMPLATES` `EnvironmentVariables` to include
   `PATH` via the helper.
5. Add three `test_D5_*` functions satisfying D5.1–D5.3.
6. `pos-amend validate` + `pos-amend apply --dry-run`.
7. Post-apply: `workspace-bootstrap/` full suite — PASS delta =
   pre-touch + 3 new D5 tests.
8. Amendment commit: `fix(workspace-bootstrap): plist PATH emission —
   amendment #<N>`.
9. `pos-amend seal` + seal commit.
10. Post-seal: seal-diff-only across all sealed components.

## 6. Out of scope

- D4 (memory-system env-scrubber `_ENV_ALLOWED_VARS` widening) — that
  is a separate amendment on a separate sealed component. Composition
  is described in research Q5; this amendment does not block on D4.
- USER / HOME / LOGNAME / SHELL / TMPDIR defensive emission —
  research Q3 names them as unnecessary; explicitly out of scope to
  prevent well-meaning widening.
- Orchestrator end-to-end liveness probe (no `/health` surface; UNIX
  socket). D5.2 only asserts emission equivalence, not runtime
  liveness.
- `memory.yaml`-override for the PATH string — not required by any AC;
  future amendment if the need surfaces.
- Any changes to label shape, bootout semantics, KeepAlive/
  ThrottleInterval, or stdout/stderr paths.
- D4's subprocess-scrubber surface, amendment #8's
  `ClaudePrintLLMClient` constructor path, or any memory-system
  source. Composition is documented, not executed here.

## 7. Flagged inferences (builder may challenge)

1. **PATH-helper shape defaults to the canonical-list option** from
   research Q1 (`~/.local/bin:/opt/homebrew/bin:/usr/local/bin:
   /usr/bin:/bin:/usr/sbin:/sbin`). Host-adaptive resolution — halt.
2. **D5.1's sandbox-launchctl shape** assumes `launchctl bootstrap
   gui/$uid <plist>` is feasible on the dispatch host (research §Q4).
   If the path turns flaky, §8 halt fires; owner rules on marker-gated
   vs scope redesign.
3. **D5.2's "same derivation"** is parse-back equivalence of the PATH
   string across both plists. Per-service-type PATH differences (not
   currently motivated) would need AC re-negotiation.

## 8. Halt triggers

1. **Cross-component scope expansion beyond workspace-bootstrap +
   hands-off-lifecycle.** If any test or fixture change requires
   amending a sealed component other than those two — halt.
2. **hands-off-lifecycle extension exceeds test-fixture helpers.** If
   the sandbox-launchctl fixture requires changing
   hands-off-lifecycle's `hooks/` runtime surface (not just test
   fixtures) — halt.
3. **Seal-test determinism cannot be achieved.** If D5.1's sandbox-
   launchctl path turns out non-deterministic even with bootout-in-
   teardown and unique labels, and the only remaining path is an
   `@pytest.mark.integration` gated test — halt and signal; the
   owner rules on whether marker-gated suffices or a narrower test
   shape must replace D5.1.
4. **ODD break strongly required.** If the AC surface cannot be
   authored without §2.4 method-in-AC or §2.5 non-objective-code
   leakage — halt and signal.
5. **`pos-amend apply --dry-run` fails.** Halt, flag.
6. **PATH-helper shape contentious.** If the builder's research
   surfaces a shape materially different from the flagged default
   (§7.1) and the choice is load-bearing — halt; owner rules.
7. **Launchd behaviour differs from research findings on the
   dispatch host.** If empirical probing shows `USER` / `HOME` /
   `LOGNAME` NOT inherited from session context on the dispatch
   host's macOS version, the "PATH-only" ruling must be re-examined
   — halt.

## 9. Bookkeeping surface (pos-amend manifest)

**Single-component default (if hands-off-lifecycle not needed):**

- `workspace-bootstrap` — `seal_test: workspace-bootstrap/tests/
  test_no_sealed_amendments.py`, `sidecar: workspace-bootstrap/tests/
  SEAL_COMMIT`, `frozen_baseline: false` (floating BASELINE advance
  per normal workspace-bootstrap convention).

**Two-component fallback (if hands-off-lifecycle test-fixture
extension required per §Owner-ruling #4):**

- `workspace-bootstrap` — as above.
- `hands-off-lifecycle` — `seal_test: hands-off-lifecycle/tests/
  test_cross_cutting.py`, `sidecar: hands-off-lifecycle/tests/
  SEAL_COMMIT`, `frozen_baseline: true` (H19 pinned at project-start
  per amendment #23; sidecar narrative stanza + allowed-prefix tuple
  update only, no BASELINE literal bump).

`universal_paths.prefixes`: `docs/plans/` (universal).
`universal_paths.files`: `CLAUDE.md`, `docs/odd-in-pos.md`,
`docs/odd-methodology.md`, `docs/FUTURE_IDEAS.md` (universal).

`narrative.target`: `workspace-bootstrap/seals/
SEAL_COMMIT.plist-path-emission`. Narrative body describes the D5
research findings summary, the PATH-only ruling rationale, the both-
plists-together ruling rationale, and the B18-pattern seal-test
choice.

## 10. ODD compliance (dispatch-time CDC adherence)

- **§2.4 (no method-in-AC):** D5.1/D5.2/D5.3 name outcome (/health
  200, PATH key present in parse-back, emission surface exactly two
  keys). Method (launchctl surface, parse lib, polling shape) is
  unspecified.
- **§2.5 (no non-objective code):** every new source line (helper,
  two template widenings) maps to D5.1/D5.2/D5.3; every new test maps
  to a D5 criterion. Builder audits the diff in both directions
  before seal.
- **§4 (re-extension):** D5.1/D5.2/D5.3 close a gap the current H1
  scaffold test (plist existence, not content) did not reach. Seal
  narrative names the re-extension.
- **§5 (structural over advisory):** D5.3's "exactly two keys" is
  the structural guard against defensive future widening.
- **Plan-before-code / research-before-plan / scope-only dispatch /
  amendment-dispatch-speedups CDCs:** all honoured — research doc
  landed before this plan; dispatch prompt carries scope only;
  narrow test scope + no pre-seal rerun + inline methodology
  snippets applied at dispatch.
