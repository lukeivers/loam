# OSS v0.1.0 publish — M3 — wire per-component CLIs as `[project.scripts]` console-script entries — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (master plan §5 M3 row + §6 sequencing rule #3).
**Programme predecessor:** M1.rename programme (sealed M1a..M1g 2026-04-29; M1g seal `f6c22fd`; §14 backfill `d5b8dcd`) + M2.partition (sealed `4cda805` + §14 backfill `bb3574c`).

**Authority documents:**
- Master plan §5 M3 row + §6 sequencing rule #3 (M3 cheapest of M3/M4/M5; recommended first).
- Programme AC: AC.OSS.2 (D-3) — `docs/rebuild/plans/oss-v0-1-0-publish.md` §3.
- Feature-usage audit D-3 — per-component CLIs are authored but unregistered.
  Path: `.scratch/claude-output/feature-usage-audit.md` §D-3 (line 430).
- VALUE_PROPOSITION (prime objective hook): `docs/rebuild/VALUE_PROPOSITION.md`.
- Existing `[project.scripts]` precedent: `framework/observability-aggregator/pyproject.toml` (`pos-obs = "loam.observability_aggregator.cli:main"`), `framework/workspace-bootstrap/pyproject.toml`, `framework/workspace-sync/pyproject.toml`, `framework/self-upgrade/pyproject.toml`, `framework/tools/loam/pyproject.toml` (`loam = "loam_cli.cli:main"` — the M1g rebrand's binary).

---

## 1. Summary / TLDR

**M3 registers five console-scripts that already have authored `main()` callables but no `[project.scripts]` entry.**

Today, an operator who runs `loam-kill scope <id>`, `loam-cost
status`, `loam-correction status`, `loam-reversibility bind …`, or
`loam-rollback scope <id>` gets `command not found`. The CLI handlers
exist (`loam.safety_layer.cli`, `loam.cost_governance.cli`,
`loam.self_correction.cli`, `loam.reversibility_primitive.cli`) and
each ships a working argparse parser, but no pyproject.toml registers
them under `[project.scripts]`. Per the feature-usage audit D-3
recommendation, the lowest-cost remediation is to add the
registrations.

**Five entries across four components:**

| Binary | Component | Entry-point target |
|---|---|---|
| `loam-kill` | safety-layer | `loam.safety_layer.cli:main` |
| `loam-cost` | cost-governance | `loam.cost_governance.cli:main` |
| `loam-correction` | self-correction | `loam.self_correction.cli:main` |
| `loam-reversibility` | reversibility-primitive | `loam.reversibility_primitive.cli:main_reversibility` |
| `loam-rollback` | reversibility-primitive | `loam.reversibility_primitive.cli:main_rollback` |

**Naming.** The `loam-*` prefix matches the post-M1g rebranded
identity (per master plan §5 row). It deviates from the audit's
in-text suggestion of `pos-*` (audit pre-dates M1g brand pivot;
master plan + dispatch are authoritative). The five existing
already-shipped CLI binaries (`pos-obs`, `pos-bootstrap`, `pos-sync`,
`pos-workspace-sync`, `pos`) STAY on the `pos-*` prefix per M1g's
FIDRAFT-deferral ruling — those are out of M3's named scope.

**Halt-and-surface findings encountered at plan-authoring time:**

The four `cli.py` modules do not have uniform `main()` signatures.
Three are entry-point-compatible as-authored:

- `loam.safety_layer.cli.main(argv: list[str] | None = None) -> int` — zero-arg, builds IPCClient internally from `--socket`/`POS_SOCKET_PATH`. Compatible.
- `loam.cost_governance.cli.main(argv: list[str] | None = None) -> int` — zero-arg, opens SQLite store directly (no IPC). Compatible.
- `loam.self_correction.cli.main(argv: list[str] | None = None) -> int` — zero-arg, opens CorrectionStore directly. Compatible.

One is **not** entry-point-compatible:

- `loam.reversibility_primitive.cli.main(call: CliCall, argv: list[str] | None = None) -> int` — REQUIRES a positional `CliCall` arg (an `IPCClient.call`-shaped async callable). The docstring at `cli.py:12-13` says *"production wiring is a thin wrapper in the workspace bootstrap"* — but no such wrapper is shipped. This is the actual M3 design point.

**M3's response (preserves the constraint "no change to the `main()` function itself"):** add **two new public functions** to `loam.reversibility_primitive.cli` — `main_reversibility(argv=None)` and `main_rollback(argv=None)` — each builds an `IPCClient` from `--socket`/`POS_SOCKET_PATH` (mirroring the `loam.safety_layer.cli` pattern), wraps `client.call` as a `CliCall` lambda, and dispatches via the existing module's parser+dispatch surface scoped to its own subtree. The existing `main(call, argv)` function is preserved untouched (kept for back-compat with any future workspace-bootstrap wrapper that wants to inject a `CliCall` directly). See decision §10 D-build.M3.1.

**Editable-install refresh.** Each of the four affected components needs `pip install -e .` re-run after pyproject changes so the binaries become bootable from the venv's `bin/`. The shared venv lives at `<repo>/.venv/`; M3 refreshes it for the 4 components.

**Tests.** Five `importlib.metadata.entry_points`-based assertions verify each `loam-*` binary is registered and points at the expected callable. No actual shell invocation (per dispatch constraint "test scope: narrow"); the assertion is registration, not behaviour.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Prime objective:** VALUE_PROPOSITION's two tests
(harness-test + primary-persona-test).

**Programme objective:** AC.OSS.2 — wired-feature-density —
"All authored features have at least one production caller path
OR are explicitly marked dormant in `oss-launch-decisions.md`."

**M3-specific scope:** AC.OSS.2 (D-3) — per-component CLIs are
authored but unregistered. M3 lands the registrations; the
production caller path is the operator typing `loam-kill scope <id>`
(etc.) into a shell.

**Lens 1 — Claude-leverage-first:** N/A direct (mechanical
pyproject.toml change). The downstream value is that an operator
working through Claude Code can ask "kill scope X" and Claude can
emit `loam-kill scope <id>` to a Bash tool call — today that fails;
post-M3 it succeeds. M3 enables a Claude-tool-call path that doesn't
exist today.

**Lens 2 — Harness + primary-persona test:**

- *Primary-persona test:* yes — the persona's translation from
  natural-language intent ("kill that scope") to AI-effective
  execution gains a callable shell verb. Pre-M3 the persona either
  has to author IPC code inline or call `python -m
  loam.safety_layer.cli kill scope …`, which is verbose and
  error-prone.
- *Harness test:* yes — adds five new operator-callable verbs to
  the harness's toolkit per the audit D-3 recommendation.

**Lens 3 — ODD authoring:** ODD §2.5 enforced — every changed
line maps to an explicit AC under AC.OSS-M3.1..AC.OSS-M3.6 (see §4).
No "while we're here" edits.

---

## 3. Three-lens analysis

(Condensed — see §2 for the per-lens answers.)

### Lens 1 — Claude-leverage-first

The five new binaries are operator-typeable verbs that Claude can
emit via Bash tool calls. Pre-M3 the persona can only invoke the
CLI surfaces via `python -m loam.<comp>.cli …`; post-M3 the
short-form binaries match the established `pos-obs` / `pos-sync` /
`loam` precedent.

### Lens 2 — Harness + primary-persona value

Five new operator-callable verbs, each closing the audit-D-3
gap. The translation burden between user intent and shell command
shrinks for each of the five subject domains (kill, cost,
correction, reversibility, rollback).

### Lens 3 — ODD authoring

ODD §2.5 enforced. Every line in the diff maps to one of the
six ACs. No code added beyond the named entries + reversibility
shims + tests.

---

## 4. Acceptance criteria — AC.OSS-M3.*

### AC.OSS-M3.1 — `loam-kill` registered

`framework/safety-layer/pyproject.toml` gains a `[project.scripts]`
table containing exactly:

```toml
[project.scripts]
loam-kill = "loam.safety_layer.cli:main"
```

**Verification (post-build):** `importlib.metadata.entry_points(group="console_scripts")` contains an entry `loam-kill` whose value is `loam.safety_layer.cli:main`.

**Test:** `framework/safety-layer/tests/test_AC_OSS_M3_loam_kill_registered.py` (new).

### AC.OSS-M3.2 — `loam-cost` registered

`framework/cost-governance/pyproject.toml` gains a `[project.scripts]`
table containing exactly:

```toml
[project.scripts]
loam-cost = "loam.cost_governance.cli:main"
```

**Verification:** `importlib.metadata.entry_points(group="console_scripts")` contains `loam-cost` → `loam.cost_governance.cli:main`.

**Test:** `framework/cost-governance/tests/test_AC_OSS_M3_loam_cost_registered.py` (new).

### AC.OSS-M3.3 — `loam-correction` registered

`framework/self-correction/pyproject.toml` gains a `[project.scripts]`
table containing exactly:

```toml
[project.scripts]
loam-correction = "loam.self_correction.cli:main"
```

**Verification:** `importlib.metadata.entry_points(group="console_scripts")` contains `loam-correction` → `loam.self_correction.cli:main`.

**Test:** `framework/self-correction/tests/test_AC_OSS_M3_loam_correction_registered.py` (new).

### AC.OSS-M3.4 — `loam-reversibility` + `loam-rollback` registered + entry-point shims authored

`framework/reversibility-primitive/pyproject.toml` gains a
`[project.scripts]` table containing exactly:

```toml
[project.scripts]
loam-reversibility = "loam.reversibility_primitive.cli:main_reversibility"
loam-rollback = "loam.reversibility_primitive.cli:main_rollback"
```

`framework/reversibility-primitive/src/loam/reversibility_primitive/cli.py`
gains two NEW public functions (existing `main(call, argv)` is
preserved untouched per dispatch constraint "no change to the
`main()` function itself"):

```python
def main_reversibility(argv: list[str] | None = None) -> int:
    """`loam-reversibility` console-script entry. Builds IPCClient
    from --socket / POS_SOCKET_PATH; invokes the reversibility
    subtree of the existing parser+dispatch surface."""
    ...

def main_rollback(argv: list[str] | None = None) -> int:
    """`loam-rollback` console-script entry. Builds IPCClient
    from --socket / POS_SOCKET_PATH; invokes the rollback subtree
    of the existing parser+dispatch surface."""
    ...
```

Each shim:
1. Builds its own argparse parser exposing only its own subtree
   (`reversibility {bind, handlers}` for `main_reversibility`;
   `rollback {scope, status}` for `main_rollback`). The argparse
   `prog` is set to `loam-reversibility` / `loam-rollback`
   respectively.
2. Reads `--socket` / `POS_SOCKET_PATH` to resolve the orchestrator
   IPC socket path (mirrors `loam.safety_layer.cli._main_async`
   socket-resolution).
3. Builds an `IPCClient`, connects, wraps `client.call` as a
   `CliCall` lambda.
4. Calls the existing `dispatch(call, args)` function with the
   resolved args (the existing dispatch already routes by
   `args.cmd` / `args.rev_cmd` / `args.rb_cmd`; the per-shim parser
   sets `args.cmd` to the constant `"reversibility"` or
   `"rollback"` respectively so the existing dispatch dispatches
   correctly without modification).
5. Prints the JSON result + returns 0 on success / 1 on exception
   (mirrors the existing `main` body's error handling shape).

The shims add ~40-60 LOC total to `cli.py`. Existing `build_parser`,
`dispatch`, and `main` are preserved.

**Verification:** `importlib.metadata.entry_points(group="console_scripts")` contains `loam-reversibility` → `loam.reversibility_primitive.cli:main_reversibility` AND `loam-rollback` → `loam.reversibility_primitive.cli:main_rollback`.

**Test:** `framework/reversibility-primitive/tests/test_AC_OSS_M3_loam_reversibility_registered.py` (new) — covers BOTH entries (single test file, two assertions).

### AC.OSS-M3.5 — Editable-install refresh

After pyproject.toml changes, `pip install -e .` is re-run inside
the shared venv `<repo>/.venv/` for each of the four affected
components. Post-refresh, `<repo>/.venv/bin/loam-kill`,
`<repo>/.venv/bin/loam-cost`, `<repo>/.venv/bin/loam-correction`,
`<repo>/.venv/bin/loam-reversibility`, and
`<repo>/.venv/bin/loam-rollback` exist as executable shims.

**Verification (operator-side, not test-asserted because shim
existence depends on the venv state of the host running the
test, not on the source tree):** `ls .venv/bin/loam-*` shows the
five new entries plus the existing `loam` (from `loam-cli`).

**Test (source-tree-only):** the registration tests AC.OSS-M3.1..4
assert that `importlib.metadata` reports the entry-point — this
is the source-of-truth check. The `.venv/bin/` shim existence is
a derivative of `pip install -e` and is not test-asserted (mirrors
the existing pattern: no other component tests the `.venv/bin/`
shim layer either).

### AC.OSS-M3.6 — No work outside the named surfaces (negative AC)

The M3 diff is contained to:

- `framework/safety-layer/pyproject.toml` (5-line `[project.scripts]` block addition).
- `framework/cost-governance/pyproject.toml` (5-line `[project.scripts]` block addition).
- `framework/self-correction/pyproject.toml` (5-line `[project.scripts]` block addition).
- `framework/reversibility-primitive/pyproject.toml` (6-line `[project.scripts]` block addition with 2 entries).
- `framework/reversibility-primitive/src/loam/reversibility_primitive/cli.py` (~40-60 LOC added — 2 new shim functions; existing `main` + `build_parser` + `dispatch` preserved).
- `framework/safety-layer/tests/test_AC_OSS_M3_loam_kill_registered.py` (new).
- `framework/cost-governance/tests/test_AC_OSS_M3_loam_cost_registered.py` (new).
- `framework/self-correction/tests/test_AC_OSS_M3_loam_correction_registered.py` (new).
- `framework/reversibility-primitive/tests/test_AC_OSS_M3_loam_reversibility_registered.py` (new).
- `framework/<comp>/tests/SEAL_COMMIT` for each of the 4 components (sidecar bump on seal — automatic via `loam amend seal`).
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.oss-v0-1-0-publish-wire-clis` (new — narrative anchor; convention per M1c..M2 precedent).
- `docs/rebuild/plans/oss-v0-1-0-publish-wire-clis.md` (this plan-doc).
- `docs/rebuild/plans/oss-v0-1-0-publish-wire-clis.manifest.yaml` (the manifest).

No other files are touched.

**Verification:** `git diff BASELINE..HEAD --stat` post-build shows
only the surfaces listed above.

### AC.OSS-M3.S — Sealed-component fence: 4 components

The sealed-component fence covers exactly:

1. `safety-layer`
2. `cost-governance`
3. `self-correction`
4. `reversibility-primitive`

Each component's seal-test (`framework/<comp>/tests/test_no_sealed_amendments.py`)
runs as part of the per-component sweep. The sidecar bump
(`framework/<comp>/tests/SEAL_COMMIT`) for each of the 4 happens at
seal time via `loam amend seal`.

`hands-off-lifecycle` is NOT in the components fence — M3 doesn't
touch HOL behaviourally. HOL appears only as the **narrative
anchor target** (per M1c..M2 precedent: HOL hosts the
`SEAL_COMMIT.oss-v0-1-0-publish-wire-clis` narrative file at
`framework/hands-off-lifecycle/seals/`). HOL's diff is intentionally
trivial: a new narrative file, no behaviour change. **HOL is NOT
listed in `components:`** because its sidecar/seal-test does not
need bumping for an M3 narrative-only addition (the convention is to
add a narrative file under HOL for the audit trail; the sidecar
mechanism is component-fence specific).

**Note:** the precedent M2.partition manifest used HOL as the
**components anchor** because M2 was tools-tree-only (and `loam
amend manifest.py:358` requires components non-empty). M3 has 4
real component anchors, so HOL is unneeded as a components anchor.
HOL appears as the narrative-target file only.

### Behaviour-count check (ODD §3.3 forward)

**6 ACs (M3.1–M3.6) + 1 sealed-component AC (M3.S) = 7 named
acceptance points.** Each maps to a unique change in the diff. No
behaviour without a named AC.

---

## 5. Hard constraints (M3-specific)

1. **Plan-before-code.** This plan-doc is committed before any
   pyproject.toml edit. Sub-plan §14 anchor lives in this doc.
2. **`loam amend apply` runs BEFORE seal commit.** No exceptions.
3. **No `git commit --amend`.** Corrective commits are NEW commits
   (per `feedback_no_amend_in_agent_dispatches`).
4. **AC.OSS.2 fence — every assertion is "this binary is
   registered and dispatches to the expected callable."** No
   behaviour assertions about what `loam-kill` *does*; only that
   it dispatches.
5. **Editable installs refreshed for the 4 components.** The
   build agent runs `pip install -e framework/<comp>/` for each.
6. **Test scope narrow** — 4 new test files (1 per component;
   reversibility-primitive's covers both entries). No regression
   re-runs of the full per-component test suites beyond what
   `loam amend seal --scoped-sweep` does automatically.
7. **Halt and surface** if the build agent encounters:
   - a CLI `main()` doesn't exist or has the wrong signature
     (already surfaced for reversibility-primitive — handled
     via the `main_reversibility` / `main_rollback` shims);
   - a pyproject.toml structural concern (missing `[project]`
     table — verified at plan-authoring all four have `[project]`);
   - naming collision with an existing entry-point (verified at
     plan-authoring time — none of `loam-kill`, `loam-cost`,
     `loam-correction`, `loam-reversibility`, `loam-rollback`
     exist anywhere in the tree's pyproject.toml files);
   - ODD §2.5 violations (any "while we're here" edit triggers
     halt);
   - the console-script naming convention deviates from the
     master plan §5 row in an unanticipated way.
8. **Strict autonomy.** The build agent does not pause on
   authorized work. The five entries + reversibility shims +
   four tests + four pyproject edits + editable-install refresh
   + seal flow are all in-scope and authorized; the agent
   completes them autonomously.

---

## 6. Out of scope (named explicitly per ODD §2.5)

- Any change to the existing `main()` functions in the four
  `cli.py` modules (only NEW `main_reversibility` / `main_rollback`
  shims are added in `reversibility_primitive.cli`).
- Any change to other CLI surfaces (`pos-obs`, `pos-bootstrap`,
  `pos-sync`, `pos-workspace-sync`, `pos`, `loam`, `loam-mode`,
  `heavy-b-migrate`, `pos-publish-framework-only`,
  `orphan-plist-cleanup`, `loam-migrate-launchd-labels`,
  `loam-migrate-host-config`).
- Any rename of the existing `pos-*` CLIs to `loam-*` (FIDRAFT-
  deferred per M1g — out of M3's named scope).
- Any addition of new IPC methods on the orchestrator (the shims
  call existing `reversibility.register_compensation` /
  `reversibility.list_handlers` / `reversibility.rollback_scope` /
  `reversibility.rollback_status` IPC methods only).
- Any documentation update beyond this plan-doc + the SEAL_COMMIT
  narrative (CLAUDE.md, README, getting-started, etc. — those
  belong to M7's docs lane).
- M4 / M5 / M6 / M7 / M8 / M9 / M10 / M11 / M12.

---

## 7. Implementation order (suggested — builder's call to refine)

The build agent's exact ordering is its call. Suggested order
(designed to keep the tree in a passing state at each step):

1. **Author the manifest.** `docs/rebuild/plans/oss-v0-1-0-publish-wire-clis.manifest.yaml`.
2. **Add `[project.scripts]` to `framework/safety-layer/pyproject.toml`** (5-line block). `pip install -e framework/safety-layer/`.
3. **Add `[project.scripts]` to `framework/cost-governance/pyproject.toml`** (5-line block). `pip install -e framework/cost-governance/`.
4. **Add `[project.scripts]` to `framework/self-correction/pyproject.toml`** (5-line block). `pip install -e framework/self-correction/`.
5. **Author the two reversibility shims** in `framework/reversibility-primitive/src/loam/reversibility_primitive/cli.py` (NEW `main_reversibility` + `main_rollback`; existing `main` + `build_parser` + `dispatch` preserved).
6. **Add `[project.scripts]` to `framework/reversibility-primitive/pyproject.toml`** (6-line block, 2 entries). `pip install -e framework/reversibility-primitive/`.
7. **Author 4 test files.** Each is a single-file `importlib.metadata.entry_points`-based registration assertion. Test files:
   - `framework/safety-layer/tests/test_AC_OSS_M3_loam_kill_registered.py`
   - `framework/cost-governance/tests/test_AC_OSS_M3_loam_cost_registered.py`
   - `framework/self-correction/tests/test_AC_OSS_M3_loam_correction_registered.py`
   - `framework/reversibility-primitive/tests/test_AC_OSS_M3_loam_reversibility_registered.py` (covers both entries)
8. **Run the 4 new tests** — confirm green.
9. **Run touched-component tests** — `pytest framework/{safety-layer,cost-governance,self-correction,reversibility-primitive}/tests/` — confirm no regressions (the shim addition is additive; existing tests don't import the new shims).
10. **Feature commit.** `feat(wire-clis): M3 wire per-component CLIs as [project.scripts] console-script entries`.
11. **`loam amend apply`** with the M3 manifest. Verify it produces the expected sidecar bumps + narrative file.
12. **Apply commit.** `chore(wire-clis-apply): loam amend apply for amendment #84 (M3 wire per-component CLIs)`.
13. **`loam amend seal`** — runs touched + sweep tests + writes deterministic seal commit + verifies post-seal `apply --dry-run`.
14. **Post-seal:** §14 method-decision register filled in this plan-doc with actual SHAs; §14 backfill commit per M2 precedent.

---

## 8. Halt triggers (M3-specific)

The build agent halts and surfaces if any of these occur:

1. **A `main()` function doesn't exist or has an unexpected signature.**
   Pre-verified at plan-authoring: `safety_layer.cli.main`,
   `cost_governance.cli.main`, `self_correction.cli.main` all are
   `main(argv: list[str] | None = None) -> int`. `reversibility_primitive.cli.main`
   is `main(call: CliCall, argv: list[str] | None = None) -> int`
   — handled via shims per AC.OSS-M3.4. If at build time any of
   the three "compatible" mains turn out NOT compatible (e.g. M2
   landing changed something), HALT.
2. **A pyproject.toml lacks a `[project]` table** or has an
   incompatible build-backend. Pre-verified: all four use
   `[build-system]` + `[project]` per the standard layout.
3. **Naming collision with an existing entry-point.** Pre-verified
   at plan-authoring: `grep -rn "loam-kill\|loam-cost\|loam-correction\|loam-reversibility\|loam-rollback" framework/**/pyproject.toml` returns no matches.
4. **ODD §2.5 violation discovered in the touched code.** Surface
   the specific case; do not silently extend.
5. **The console-script naming convention deviates from this plan
   in an unanticipated way** (e.g. an entry-point group other than
   `console_scripts` is required, or hyphen vs underscore in the
   key name conflicts with PEP 621). PEP 621 requires the key be
   a valid Python identifier OR a hyphenated string per setuptools'
   acceptance — `loam-kill` (etc.) is hyphenated, which is the
   established pos-v2 convention (see `pos-obs`, `pos-bootstrap`).
6. **`pip install -e` fails for any of the 4 components** —
   surface the failure; common cause would be a transitive
   dependency conflict from the pyproject change.
7. **`loam amend apply` rejects the manifest** for any reason —
   surface and resolve before proceeding.
8. **Seal-test failure on any of the 4 components after the
   `[project.scripts]` addition** — the test_no_sealed_amendments
   tests don't inspect pyproject.toml, so this is unexpected;
   surface if it happens.

---

## 9. Risks (M3-specific)

1. **Editable-install staleness.** If the venv has the old metadata
   cached (no `[project.scripts]`), the new binaries won't appear
   until `pip install -e` re-runs. Mitigation: per AC.OSS-M3.5, the
   build agent re-runs `pip install -e` for each touched component.
   A test that asserts entry-point registration via
   `importlib.metadata` reads the freshly-installed metadata, so
   this is self-checking.
2. **Reversibility shim divergence from existing dispatch.** The
   new `main_reversibility` / `main_rollback` shims must construct
   parsed-args that the existing `dispatch(call, args)` function
   accepts. Mitigation: each shim's parser sets `args.cmd` to the
   constant value (`"reversibility"` or `"rollback"`) the existing
   dispatch checks for; sub-args mirror the existing sub-parser
   structure verbatim. Test asserts only registration; no behaviour
   regression test is needed because the new code path is additive.
3. **`POS_SOCKET_PATH` env var name (not `LOAM_SOCKET_PATH`).** The
   existing `loam.safety_layer.cli` reads `POS_SOCKET_PATH` (line
   74). The new reversibility shims should read the SAME variable
   name (`POS_SOCKET_PATH`), not coin a `LOAM_SOCKET_PATH` —
   M1b's env-var rename did NOT include `POS_SOCKET_PATH` (verify
   at build time by greppin `POS_SOCKET_PATH` across the tree;
   if M1b renamed it, use the rebrand name; if not, keep
   `POS_SOCKET_PATH` for consistency with the safety CLI). This
   is a small risk: M3 should NOT introduce env-var asymmetry.
   Builder verifies + records in §14 D-build.M3.2.
4. **`loam amend seal` failing scoped-sweep.** Unlikely — the
   addition is additive and isolated. If it fails, surface the
   failing test; do not silently bypass.

---

## 10. Decisions remaining for owner ruling

**None requiring owner ruling.** The plan resolves every design
decision via dispatch authority (master plan §5 + dispatch
constraints) + plan-side recommendations. Decisions are recorded
below for the §14 register.

### D-build.M3.1 — Reversibility-primitive shim shape

**Decision:** add two NEW public functions `main_reversibility(argv)`
and `main_rollback(argv)` to `loam.reversibility_primitive.cli`,
each scoped to its respective subtree of the existing parser. The
existing `main(call, argv)` is preserved untouched.

**Why this shape over alternatives:**

- **Alternative: refactor `main` to be zero-arg + lazy-build IPC.**
  Rejected — violates dispatch constraint "no change to the `main()`
  function itself" + breaks any future workspace-bootstrap wrapper
  that wants to inject a `CliCall` directly.
- **Alternative: register a single `loam-reversibility` entry that
  dispatches both subtrees by argv-prefix-injection.** Rejected —
  the master plan §5 row explicitly names FIVE binaries, two from
  reversibility-primitive (`loam-reversibility` and `loam-rollback`).
  Using one binary would deviate from the named scope.
- **Alternative: add a single `main_entry()` helper that parses
  `sys.argv[0]` to dispatch by binary name.** Rejected — fragile
  (depends on basename), opaque, harder to test, no benefit.

**Surface:** ~40-60 LOC added in two new functions.

### D-build.M3.2 — Socket env-var name in reversibility shims

**Decision (recommended):** read `POS_SOCKET_PATH` to match
`loam.safety_layer.cli`. If at build time the env-var has been
renamed to `LOAM_SOCKET_PATH` by M1b, use the renamed name. Builder
verifies via `grep -rn "POS_SOCKET_PATH\|LOAM_SOCKET_PATH" framework/`
and records the actual name used.

### D-build.M3.3 — Test layout: one file per component vs one consolidated

**Decision (recommended):** one test file per affected component
(matches per-component test ownership; reversibility-primitive's
single test file covers both entries). Total: 4 new test files. Each
is ~20-30 LOC.

### D-build.M3.4 — Sealed-component fence membership

**Decision:** the 4 components — `safety-layer`, `cost-governance`,
`self-correction`, `reversibility-primitive`. HOL is NOT in
`components:` (M3 doesn't bump HOL's sidecar). HOL is the narrative
target only (`framework/hands-off-lifecycle/seals/SEAL_COMMIT.oss-v0-1-0-publish-wire-clis`).

### D-build.M3.5 — Console-script binary names: `loam-*` vs `pos-*`

**Decision:** `loam-*` per master plan §5 row + dispatch. The
audit's in-text `pos-*` suggestion is overruled by the master plan
+ the post-M1g rebrand. The five existing `pos-*` binaries
(`pos-obs`, `pos-bootstrap`, `pos-sync`, `pos-workspace-sync`,
`pos`) STAY on the `pos-*` prefix per M1g's FIDRAFT-deferral —
those are out of M3's scope.

### D-build.M3.6 — Editable-install refresh granularity

**Decision:** `pip install -e framework/<comp>/` for each of the
4 components individually (rather than a single `pip install -e .`
at repo root, which there isn't anyway — pos-v2 has no top-level
pyproject.toml; each component is its own pip-installable
distribution).

---

## 11. Halt-and-surface findings encountered during plan authoring

### Finding #1 — `reversibility_primitive.cli.main` is not entry-point compatible

**Surface:** `loam.reversibility_primitive.cli.main(call: CliCall,
argv: list[str] | None = None)` — requires positional `CliCall` arg.
A `[project.scripts]` entry calls the function with zero args.
Direct registration would `TypeError` at first invocation.

**Resolution:** AC.OSS-M3.4 + D-build.M3.1 — add two new public
shim functions `main_reversibility` / `main_rollback` that each
build an `IPCClient` from `--socket`/`POS_SOCKET_PATH`, wrap
`client.call` as a `CliCall`, and invoke the existing module's
parser+dispatch surface scoped to its respective subtree. Existing
`main(call, argv)` preserved untouched.

**Audit consequence:** the audit's D-3 framing
("Mechanical; a one-line addition to each pyproject.toml" /
"Five lines in five pyproject.toml files") is naively-aspirational.
The reality is 4 pyproject.toml edits + 2 new functions in
reversibility-primitive's `cli.py` + 4 test files. Still small
(~100 LOC total), but more than 5 lines.

### Finding #2 — Console-script binary names per master plan are `loam-*` not `pos-*`

**Surface:** the audit document (D-3) suggests `pos-kill`, `pos-cost`,
etc. (matching the existing `pos-obs` / `pos-sync` naming). The
master plan §5 M3 row prescribes `loam-kill`, `loam-cost`, etc.
(matching the post-M1g rebranded identity).

**Resolution:** D-build.M3.5 — use master plan's `loam-*` names.
The audit pre-dates M1g; master plan + dispatch are authoritative.
Recorded in §14.

### Finding #3 — All 4 components have `[project]` tables; no migration needed

**Surface:** verified at plan-authoring via `cat framework/<comp>/pyproject.toml`
for each of the 4 — all use `[build-system]` + `[project]` standard
layout (PEP 621), with `requires = ["setuptools>=68"]` build-system.
No setuptools-config-style migration needed.

**Resolution:** AC.OSS-M3.1..4 add `[project.scripts]` directly.
No structural pyproject migration in M3's scope.

### Finding #4 — Naming-collision check clean

**Surface:** verified at plan-authoring:

```
$ grep -rn "loam-kill\|loam-cost\|loam-correction\|loam-reversibility\|loam-rollback" framework/**/pyproject.toml 2>/dev/null
(no matches)
```

**Resolution:** no collision with existing entry-points. Safe to
register.

### Finding #5 — Env-var name unknown at plan time

**Surface:** the reversibility shims need to read the orchestrator
socket env-var. The safety CLI reads `POS_SOCKET_PATH`. M1b's
env-var rebrand list mentions `POS_V2_*` → `LOAM_*` but the M1b
manifest is what actually authorizes specific renames. Builder
must verify at build time whether `POS_SOCKET_PATH` was renamed by
M1b or stays `POS_SOCKET_PATH` for back-compat.

**Resolution:** D-build.M3.2 — builder greps + records in §14.
Either name is acceptable; the goal is consistency with whatever
the safety CLI reads (so a single env-var configures both kill +
reversibility CLIs).

### Finding #6 — HC#4 byte-content sample status

**Surface:** verified at plan-authoring time — no HC#4 byte-content
sample paths under `framework/safety-layer/`, `framework/cost-governance/`,
`framework/self-correction/`, `framework/reversibility-primitive/`
that would be impacted by the M3 diff (the M3 diff is pyproject
additions + ~50 LOC of new shim functions in reversibility's
`cli.py` + 4 new test files; none of these touch existing HC#4
samples).

**Resolution:** NO RETIRE-AND-REBASELINE. HC#4 invariant expected
to remain GREEN through M3.

---

## 12. Method-decision register (placeholder)

(See §14 for the post-build narratives + commit SHAs.)

---

## 13. Test breakdown (post-build)

Four new test files, total ~80-100 LOC across all four:

1. **`framework/safety-layer/tests/test_AC_OSS_M3_loam_kill_registered.py`** — `importlib.metadata.entry_points(group="console_scripts")` contains `loam-kill` → `loam.safety_layer.cli:main`.
2. **`framework/cost-governance/tests/test_AC_OSS_M3_loam_cost_registered.py`** — `importlib.metadata.entry_points(group="console_scripts")` contains `loam-cost` → `loam.cost_governance.cli:main`.
3. **`framework/self-correction/tests/test_AC_OSS_M3_loam_correction_registered.py`** — `importlib.metadata.entry_points(group="console_scripts")` contains `loam-correction` → `loam.self_correction.cli:main`.
4. **`framework/reversibility-primitive/tests/test_AC_OSS_M3_loam_reversibility_registered.py`** — TWO assertions: `loam-reversibility` → `loam.reversibility_primitive.cli:main_reversibility` AND `loam-rollback` → `loam.reversibility_primitive.cli:main_rollback`.

**No shell-invocation tests.** Per dispatch constraint "test scope
narrow"; the entry-point registration is the AC, not behaviour.

### Cross-tree verification

None. Each component's pyproject.toml is independently consumed; no
cross-tree consumer needs an update.

### Backwards-compat verification

The existing `main(call, argv)` function in
`loam.reversibility_primitive.cli` is preserved. Any future
workspace-bootstrap wrapper that injects a `CliCall` directly
remains supported. No existing import sites change.

### HC#4 byte-content sample status

NO RETIRE-AND-REBASELINE per §11 finding #6.

### Dependents cleared to dispatch (post-M3)

- M4 (wire-dispatch) — independent in scope from M3 (touches
  primary-persona + hands-off-lifecycle, not the 4 M3 components).
  Cleared to dispatch immediately post-M3 seal.
- M5 (wire-dormancy) — independent in scope (touches workspace-
  bootstrap + dormancy + orchestrator). Cleared.
- M6, M7, M8, M9 — not gated on M3.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-
backfill; method-decision narratives populated by builder during
build.)

### D-build.M3.1 — Reversibility-primitive shim shape

(Populated at build time. Recommendation per §10 D-build.M3.1:
two new public functions `main_reversibility(argv)` +
`main_rollback(argv)` in `loam.reversibility_primitive.cli`; each
builds an `IPCClient` from `--socket`/`POS_SOCKET_PATH`, wraps
`client.call` as a `CliCall`, dispatches to the existing
`build_parser` + `dispatch` surface scoped to its subtree.
Existing `main(call, argv)` preserved untouched. Builder records
actual function signatures + LOC delta + any deviation.)

### D-build.M3.2 — Socket env-var name in reversibility shims

(Populated at build time. Recommendation per §10 D-build.M3.2:
read `POS_SOCKET_PATH` to match `loam.safety_layer.cli`. If
M1b rebranded the env-var, use the rebrand name. Builder records
`grep -rn "POS_SOCKET_PATH\|LOAM_SOCKET_PATH" framework/` finding
+ actual env-var name used in the new shims.)

### D-build.M3.3 — Test layout: one file per component vs one consolidated

(Populated at build time. Recommendation per §10 D-build.M3.3:
4 new test files (one per component; reversibility-primitive
covers both entries). Builder records actual layout.)

### D-build.M3.4 — Sealed-component fence membership

(Populated at build time. Recommendation per §10 D-build.M3.4:
4 components — safety-layer, cost-governance, self-correction,
reversibility-primitive. HOL narrative-target only, not in
`components:`. Builder records actual fence + any deviation.)

### D-build.M3.5 — Console-script binary names: `loam-*` vs `pos-*`

(Populated at build time. Recommendation per §10 D-build.M3.5:
`loam-*` per master plan §5 row + dispatch authority. Builder
records actual names used + confirmation that no `pos-*` aliases
were added.)

### D-build.M3.6 — Editable-install refresh granularity

(Populated at build time. Recommendation per §10 D-build.M3.6:
`pip install -e framework/<comp>/` per component. Builder records
actual command(s) run.)

### Commit SHAs

- M3.wire-clis sub-plan commit: `<TBD>` — `docs(plans): author M3 sub-plan + manifest — wire per-component CLIs as [project.scripts] console-script entries`
- M3.wire-clis feature commit: `<TBD>` — `feat(wire-clis): M3 wire per-component CLIs as [project.scripts] console-script entries`
- M3.wire-clis apply commit: `<TBD>` — `chore(wire-clis-apply): loam amend apply for amendment #84 (M3 wire per-component CLIs)`
- M3.wire-clis corrective commit(s): `<TBD or none>`
- M3.wire-clis seal commit: `<TBD>` — `chore(seals): M3 wire per-component CLIs as [project.scripts] console-script entries — …`
- M3.wire-clis §14 SHA-register backfill: `<TBD>` — `docs(plans): record amendment #84 commit SHAs in M3 §14 method-decision register`

---

## 15. References

- **Programme master plan:** `docs/rebuild/plans/oss-v0-1-0-publish.md`
  (M3 row in §5; sequencing rule #3 in §6; AC.OSS.2 in §3).
- **Programme predecessors:**
  - M1.rename series — sealed M1a..M1g 2026-04-29 (M1g seal `f6c22fd`; §14 backfill `d5b8dcd`).
  - M2.partition — sealed `4cda805` 2026-04-29 (§14 backfill `bb3574c`).
- **Authority documents (inherited from programme master):**
  - `.scratch/claude-output/feature-usage-audit.md` D-3 (line 430 — per-component CLIs are authored but unregistered).
- **Existing `[project.scripts]` precedent:**
  - `framework/observability-aggregator/pyproject.toml` (`pos-obs`).
  - `framework/workspace-bootstrap/pyproject.toml` (`pos-bootstrap`).
  - `framework/workspace-sync/pyproject.toml` (`pos-sync`, `pos-workspace-sync`).
  - `framework/self-upgrade/pyproject.toml` (`pos`).
  - `framework/tools/loam/pyproject.toml` (`loam`).
- **Existing CLI module pattern (to mirror for reversibility shims):**
  - `framework/safety-layer/src/loam/safety_layer/cli.py` (`main` + `_main_async` socket-resolution + `IPCClient` build).
- **Reversibility-primitive CLI module (to extend):**
  - `framework/reversibility-primitive/src/loam/reversibility_primitive/cli.py` (`build_parser` + `dispatch` + existing `main(call, argv)` preserved; new `main_reversibility(argv)` + `main_rollback(argv)` added).
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-loam:** `docs/odd-methodology.md`, `docs/odd-in-loam.md`.
- **VALUE_PROPOSITION:** `docs/rebuild/VALUE_PROPOSITION.md`.
- **CLAUDE.md** + `~/.claude/CLAUDE.md` + `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`.
- **Memory bullets carried forward:**
  - `feedback_no_amend_in_agent_dispatches`.
  - `feedback_dispatch_explicit_pos_amend_apply` (post-M1g shape: `loam amend apply`).
  - `feedback_subagent_odd_violation_halt`.
  - `feedback_amendment_dispatch_speedups`.
  - `feedback_summarize_and_surface_decisions`.
  - `feedback_serialize_amendment_builds`.
  - `feedback_always_specify_wd_in_dispatches`.
  - `feedback_verify_post_amendment_state`.
  - `feedback_duration_estimation_rubric`.
  - `feedback_loose_AC_text_fix_AC_not_implementation`.
  - `feedback_critical_thinking_on_deviations`.
  - `feedback_strict_autonomy_no_pause_for_authorized_work`.
  - `feedback_future_ideas_draft_workflow`.
  - `feedback_value_proposition_as_prime_objective`.
- **Precedent multi-component sealed-amendment manifests:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1e.manifest.yaml` (multi-component fence covering reversibility-primitive + safety-layer + cost-governance + self-correction among others).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1d.manifest.yaml` (M1d — multi-component shape).
- **Precedent single-component sealed-amendment manifest:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-partition.manifest.yaml` (M2 — for the universal-admissions block precedent + narrative shape).
