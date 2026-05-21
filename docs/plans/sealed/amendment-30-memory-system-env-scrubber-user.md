# Plan — Amendment: memory-system env-scrubber USER widening (D4)

**Status:** authored 2026-04-24. Amendment number assigned at
build-dispatch time per owner ruling 2026-04-24 — the filename carries
the slug only.
**Research plan:** `docs/plans/research/memory-system-env-scrubber-research-plan.md`.
**Research:** `docs/plans/research/memory-system-env-scrubber-research.md`.

**Owner rulings (2026-04-24):** test-shape is option (c) — a
construction-time / pre-spawn structural check that the scrubbed-env
dict contains the real login user's `USER` value, achievable without a
real `claude` subprocess. AC scope is two ACs: AC-i widens the
allowlist to include `USER` (AC2's existing test extended to
positive-assert `USER` presence under a monkeypatched parent env);
AC-ii adds the structural-check on the scrubbed-env dict at spawn
time. Component scope is memory-system only — research §5 confirmed
zero cross-component blast radius. ODD-outcome-shape is required for
every AC.

---

## 1. Objective

The scrubbed child env passed to every `claude -p` subprocess spawned
by memory-system contains the real login user's `USER` value whenever
the parent process's env contains `USER`. The missing-`USER` defect
that shipped through two prior seals is closed structurally — regression
surfaces as a failing deterministic test on a dict invariant, not as a
runtime "Not logged in · Please run /login" message in production.

Two behaviours; AC count = 2 (§5).

---

## 2. Hard constraints

1. **Dependency fence.** memory-system source + tests only. No sealed
   component outside memory-system may be touched. Research §5 confirms
   the fence is achievable. If the build would require editing another
   component's source, halt.
2. **Reversibility.** Fully reversible. Allowlist widening adds one
   tuple element; reverting removes it. No migration, no persisted
   state, no plist change.
3. **Authority bound.** Owner has ruled AC shape (two ACs, option-c
   test-shape, USER-only widening). Builder owns method — test
   framework specifics, monkeypatch target choice, fixture layout,
   exact assertion wording.
4. **Budget.** Small amendment. One source-file edit
   (`claude_print_client.py`) plus test-file extension
   (`test_claude_print_client.py`). No new runtime deps. Scope cap: if
   the surface exceeds one source file plus one test file, halt.
5. **Fail-closed direction.** When the parent env lacks `USER` at
   construction time, the scrubbed dict simply omits it — no synthesis,
   no fallback value.
6. **No `--amend`.** Corrective commits only
   (`feedback_no_amend_in_agent_dispatches.md`).
7. **Amendment-dispatch CDC speedups apply** per
   `feedback_amendment_dispatch_speedups.md`: (a) full suites only for
   memory-system; other sealed components get
   `test_no_sealed_amendments.py` only. (b) Skip pre-seal full rerun;
   seal-diff-only suffices for the sidecar-only seal commit. (c)
   Methodology excerpts inlined in the build-dispatch prompt rather
   than re-reading full source docs.
8. **`pos-amend apply --dry-run` green is a hard prereq** for the
   amendment commit (amendment #22 convention).
9. **Preserve existing AC2 invariants.** `ANTHROPIC_API_KEY` /
   `OPENAI_API_KEY` forbidden-absence and `PATH` presence assertions
   remain load-bearing. This amendment only extends the positive-
   presence side of the env contract.

---

## 3. Acceptance criteria

Each AC maps 1:1 to a test function. Criterion IDs use the amendment
slug; numeric IDs finalised when the amendment number is assigned.

### AC-i — scrubbed env contract admits `USER`

**Outcome.** When `USER` is present in the parent process's env at the
moment the scrubbed child env is constructed, the constructed child env
for every `claude -p` subprocess invocation contains `USER` bound to
the same value the parent env carried.

**Deterministic check.** Under a parent env monkeypatched to contain
`USER=<controlled-value>`, the child-env dict produced for a `claude -p`
invocation has `env["USER"] == <controlled-value>`. Extends the
existing AC2 test's env invariants with a positive-presence clause on
`USER`. Forbidden-key absence assertions unchanged.

### AC-ii — scrubbed-env dict at spawn time contains the login user's `USER`

**Outcome.** At the moment memory-system is about to spawn a `claude
-p` subprocess, the dict that will be handed to the OS as the child's
env contains `USER` bound to the login user's value, determined at
construction time from the parent process's env.

**Deterministic check.** A pre-spawn structural inspection of the
constructed child-env dict (captured without a real subprocess ever
executing) asserts `USER` is present and equal to the login user's
value (the value the parent-env monkeypatch installed). Structural
invariant on the scrubber's output — not a behavioural observation of
a real `claude` process.

---

## 4. Implementation order (suggested; builder refines in its own plan)

1. Build agent authors its own plan at a path under
   `docs/plans/` (plan-before-code CDC — separate from this
   amendment plan; may encode the assigned amendment number).
2. Build agent produces the pos-amend manifest alongside its plan.
3. Pre-amendment verification: `memory-system/` full suite green at
   the pre-amendment tip; seal-diff-only tests green across other
   sealed components.
4. Widen `_ENV_ALLOWED_VARS` in
   `memory-system/src/claude_print_client.py` to admit `USER`. Update
   the docstring to name `USER`'s role under launchd's scrubbed env.
5. Extend `memory-system/tests/test_claude_print_client.py` with AC-i
   and AC-ii test functions.
6. `pos-amend apply --dry-run` — must exit 0.
7. Amendment commit.
8. `pos-amend seal` — advance sidecars, append narrative.
9. Seal commit (sidecar + narrative only).
10. Post-seal: seal-diff-only tests across all sealed components.

---

## 5. Behaviour-count check

| Behaviour | Covered by |
|-----------|------------|
| Scrubbed-env contract admits `USER` when parent env carries it | AC-i |
| Pre-spawn structural invariant: child-env dict contains login user's `USER` | AC-ii |

Two behaviours; two ACs (odd-methodology.md §2.3 / §3.3).

---

## 6. Out of scope

- `LOGNAME`, `__CF_USER_TEXT_ENCODING`, `TMPDIR`, `SHELL`, `LANG`, and
  every other candidate surveyed in research §Q3. Each ruled out with
  evidence; adding any would be §2.5 code-for-cases-no-objective-names.
- Removal of `HOME` from the existing allowlist. Research §Q3 flags
  `HOME` load-bearing for future `~/.claude/*` reads; removal needs its
  own objective.
- Real-`claude`-binary test fixtures (research §Q2 candidate B) —
  excluded by owner ruling (c).
- Fake-claude subprocess fixtures (research §Q2 candidate C) —
  excluded by owner ruling (c).
- Any cross-component generalisation of the "scrubbed-env subprocess"
  test-harness pattern. Research §Q4 recommends a FUTURE_IDEAS entry,
  not an AC here.
- `POST_FIRST_RUN_REVIEW.md` register updates from research §Q4 — may
  be carried separately or deferred; not an AC of this amendment.
- Any change to launchd plist, adapter wiring, or memory-system MCP
  transport surface.

---

## 7. Halt triggers

1. Any AC would require editing a sealed component outside
   memory-system — halt.
2. An AC cannot be written as a deterministic outcome-shaped test
   (method-in-acceptance strongly required) — halt and signal. Research
   concluded candidate (c) can be stated outcome-first; if the builder
   discovers otherwise, ODD-break signal is mandatory.
3. `pos-amend apply --dry-run` fails — halt.
4. Pre-amendment `memory-system/` full suite is not green at the
   assigned pre-amendment tip — halt.
5. An AC test requires invoking a real `claude` binary, real OAuth, or
   a real subprocess to assert its outcome — halt. Owner ruling is
   (c); escalation needs a fresh ruling.
6. Existing AC2 invariants (forbidden-key absence, PATH presence, argv
   shape) would be weakened — halt.
7. Any ODD break seems strongly required for any reason — halt and
   signal; do not silently apply.

---

## 8. Bookkeeping surface

Single-component amendment. Normal floating `BASELINE`; memory-system
is not a frozen-baseline component (per amendment #25 manifest,
`frozen_baseline: true` does NOT apply).

Manifest (builder authors at dispatch time at
`docs/plans/amendment-<N>-memory-system-env-scrubber-user.manifest.yaml`):

- `schema_version: 1`
- `amendment.number: <assigned>`, `slug: memory-system-env-scrubber-user`
- `baseline: <pre-amendment-tip>` (captured at dispatch time)
- `plan: docs/plans/amendment-30-memory-system-env-scrubber-user.md`
- `components:` — one entry:
  - `name: memory-system`
  - `seal_test: memory-system/tests/test_no_sealed_amendments.py`
  - `sidecar: memory-system/tests/SEAL_COMMIT`
  - No `extra_allowed_prefixes` unless the builder discovers a new
    path bucket; `memory-system/` and
    `docs/archive/component-research/memory-system/` are admitted already.
- `universal_paths.prefixes: [docs/plans/]`
- `universal_paths.files: [CLAUDE.md, docs/odd-in-pos.md,
  docs/odd-methodology.md, docs/FUTURE_IDEAS.md]`
- `narrative.target: memory-system/tests/SEAL_COMMIT.notes` (append).
- `narrative.body` names the USER widening, cites the research doc,
  and records the §Q3 "every other candidate ruled out with evidence"
  disposition for future inheritance.

H19 (hands-off-lifecycle frozen-BASELINE cross-cutting test) is NOT
touched — no manifest entry, no sidecar bump.

---

## 9. Dispatch-time CDC adherence note

Build-dispatch for this amendment observes:

1. **Working directory** — `/Users/lukeivers/ivers-corp-pos-v2/`
   (canonical tree). Main-session CWD is ephemeral; specify WD
   explicitly (`feedback_always_specify_wd_in_dispatches.md`).
2. **Session-start corpus** — the dispatched build agent reads the
   CLAUDE.md session-start corpus before editing, or works from
   inlined methodology excerpts per the dispatch-CDC speedup rule.
3. **Plan before code** — build agent writes its own plan BEFORE any
   source edit. This plan authors scope; build agent authors method.
4. **Scope-only downstream dispatches** — sub-dispatches carry scope
   only, not method (`feedback_agent_prompts_scope_only.md`).
5. **No `--amend`** — corrective commits only
   (`feedback_no_amend_in_agent_dispatches.md`).
6. **Background-agent default** — build runs in a background agent
   (`feedback_background_agents.md` + amendment-dispatch CDC).
7. **Amendment-dispatch speedups** per §2 constraint 7.

---

## 10. ODD compliance summary

- §2.3 — Each AC is a deterministic outcome-shaped check.
- §2.4 — No method-in-acceptance. Method (monkeypatch target, fixture
  composition, test framework specifics) is the builder's call.
- §2.5 — Every line of new code maps to AC-i or AC-ii. The
  `"USER"` tuple entry satisfies AC-i; the AC-ii test function
  exercises the structural invariant. No code for cases the objectives
  do not name.
- §3.3 — Two behaviours, two criteria (§5).
- §4 — Re-extension pattern applied: the "Not logged in" defect
  discovered during post-seal review is promoted to named ACs rather
  than buried as a silent tuple edit.
- §5.1 — Structural over advisory: USER-presence becomes a testable
  dict invariant at construction time, not a runtime behavioural
  observation. Future regression surfaces as a failing deterministic
  test, not a production identity error.
