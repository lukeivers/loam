# Builder plan — Amendment #30: memory-system env-scrubber USER widening + pre-spawn structural check

**Amendment number resolved:** 30 (next sequential after amendment #29
"per-workspace memory-sidecar port + workspace-identity health probe",
sealed at `a010686`).

**BASELINE (pre-amendment tip):** `a010686798e99d8a3e045cf5581909105ba615db`
(chore(seals): per-workspace-memory-port seal — memory-system +
workspace-bootstrap + hands-off-lifecycle at b35e0c0).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

**Binding amendment plan:**
`docs/rebuild/plans/amendment-30-memory-system-env-scrubber-user.md`
(AC-i, AC-ii are authoritative).

**Research:**
`docs/rebuild/plans/research/memory-system-env-scrubber-research.md`.

This builder-plan enumerates the files, symbols, and test names I will
touch. Every entry maps 1:1 to AC-i or AC-ii. The builder-plan itself
does not widen the ACs.

---

## 1. AC-to-file-and-symbol map

| AC | File(s) touched | Symbol(s) added/changed | Test name(s) |
|----|-----------------|-------------------------|--------------|
| AC-i | `memory-system/src/claude_print_client.py` (widen `_ENV_ALLOWED_VARS`; update docstring) + `memory-system/tests/test_claude_print_client.py` (extend `test_AC2_subprocess_argv_and_env_scrubbed` with positive USER-presence clause). | `_ENV_ALLOWED_VARS` gains `"USER"`; AC2 test seeds parent env with `USER=<controlled-value>` and asserts child env carries it. | `memory-system/tests/test_claude_print_client.py::test_AC2_subprocess_argv_and_env_scrubbed` (extended) |
| AC-ii | `memory-system/tests/test_claude_print_client.py` (new pre-spawn structural-inspection test). | New test function + minimal fixture that captures the `_child_env` dict produced at `ClaudePrintLLMClient` construction time and asserts USER present + equal to the monkeypatched login-user value. No source change beyond AC-i's `_ENV_ALLOWED_VARS` edit. | `memory-system/tests/test_claude_print_client.py::test_AC30_child_env_contains_login_user_at_spawn_time` |

§2.5 forward+reverse check:

- Forward: each behaviour in the amendment plan §1 objective (scrubbed
  env admits USER; pre-spawn structural invariant) + each AC has at
  least one test.
- Reverse: every edit in every file above is cited against a specific
  AC above; no incidental edits. The `_ENV_ALLOWED_VARS` tuple gains
  exactly one element. The docstring update above the tuple names
  USER's role (research §Q3 implication). No other symbol in
  `claude_print_client.py` changes.

---

## 2. File-by-file edit enumeration

### 2.1 `memory-system/src/claude_print_client.py` (AC-i)

Edit summary:

- `_ENV_ALLOWED_VARS`: tuple gains `"USER"` as a third element. Order
  stable: `("PATH", "HOME", "USER")`. Adds exactly one element;
  reverting removes it.
- Docstring above `_ENV_ALLOWED_VARS`: name USER's role (keychain
  identity required for OAuth resolution on macOS, where launchd's
  gui-domain session injects USER into agent-spawned processes per
  research §Q1 evidence). Preserve the existing "If a runtime failure
  later shows `claude -p` needs another var, add it together with a
  concrete AC extension naming the failure observed" line (amendment
  #11 §F5 ruling).
- Module-level module-docstring (lines 35-46) stays unchanged — the
  empirical subprocess shape and subscription-routing contract still
  hold verbatim.
- No changes to `_build_child_env`, `_probe_claude_authenticated`,
  `ClaudePrintLLMClient.__init__`, or any other symbol. The tuple edit
  is the entire source-change surface.

### 2.2 `memory-system/tests/test_claude_print_client.py` (AC-i + AC-ii)

Edit summary:

- Extend `test_AC2_subprocess_argv_and_env_scrubbed` (existing
  function, AC-i): add `monkeypatch.setenv("USER", <controlled-value>)`
  alongside the existing API-key monkeypatches; after the subprocess
  mock assertions, add `assert env["USER"] == <controlled-value>`.
  Preserve every existing assertion verbatim: forbidden-key absence
  for `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`; PATH presence;
  argv-shape (--bare absent, --no-session-persistence present, etc).
- Add `test_AC30_child_env_contains_login_user_at_spawn_time` (new
  function, AC-ii): construct a `ClaudePrintLLMClient` under a
  monkeypatched parent env with `USER=<controlled-value>`; the test
  mocks `shutil.which` + `asyncio.create_subprocess_exec` so no real
  subprocess spawns. After construction, the test inspects
  `client._child_env` directly (pre-spawn structural check on the
  dict) and asserts `client._child_env["USER"] == <controlled-value>`.
  Structural invariant on the scrubber's output — not a behavioural
  observation of a real claude process.

No other test function changes. No fixture changes. The existing
`_FakeProc`, `_make_exec_mock`, `_envelope`, `_SmallResponse`
fixtures are reused verbatim by the extended AC2 test.

### 2.3 `docs/rebuild/plans/` — universal-admissions under the manifest

This builder-plan, the manifest, and the amendment plan land under
`docs/rebuild/plans/` which is universally admitted via the manifest's
`universal_paths.prefixes`. No additional prefix-widening required.

---

## 3. Test scope

Amendment-dispatch speedups (CDC: `feedback_amendment_dispatch_speedups`):

- Pre-amendment: `memory-system/` full suite must be green at BASELINE.
  Already verified at dispatch — 86 passed / 1 deselected (slow marker).
- Post-amendment (amendment commit): `memory-system/` full suite
  green. Other sealed components — seal-diff-only
  (`test_no_sealed_amendments.py` / `test_cross_cutting.py`) — green
  because this amendment's diff stays under `memory-system/` +
  universal paths only.
- Post-seal: seal-diff-only tests across all sealed components green
  (the SEAL_COMMIT sidecars advance but no source changes land in the
  seal commit, so each component's seal-diff still passes).

Pre-seal full-suite rerun skipped per the amendment-dispatch CDC
speedup rule; seal-diff-only suffices for the sidecar-only seal commit.

---

## 4. Commit shape

Two commits — the standard amendment pattern:

1. **Amendment commit** (source + test + plan + manifest + builder
   plan). Message:
   `fix(memory-system): env-scrubber admits USER + pre-spawn structural check — amendment #30`
2. **Seal commit** (sidecar advance + narrative append only). Message:
   `chore(seals): memory-system-env-scrubber-user seal — memory-system at <sha>`.

No `git commit --amend`. Corrective commits only per
`feedback_no_amend_in_agent_dispatches`.

---

## 5. Halt-trigger pre-checks (amendment plan §7)

1. **AC requires editing a sealed component outside memory-system.**
   Not triggered. All edits are under `memory-system/src/` or
   `memory-system/tests/`, plus universally-admitted
   `docs/rebuild/plans/` for plan + manifest.
2. **AC cannot be written as deterministic outcome-shape.** Not
   triggered. Both ACs are dict-invariant assertions — deterministic
   and outcome-shaped.
3. **`pos-amend apply --dry-run` fails.** Not triggered — green at
   dispatch (confirmed pre-edit).
4. **Pre-amendment memory-system suite not green at BASELINE.** Not
   triggered — 86 passed at BASELINE a010686.
5. **AC test requires invoking a real `claude` binary / real OAuth /
   real subprocess.** Not triggered. Both tests mock
   `asyncio.create_subprocess_exec` and `shutil.which`; `_child_env`
   is inspected directly as a Python dict attribute.
6. **Existing AC2 invariants would weaken.** Not triggered. AC2's
   forbidden-key absence, PATH presence, and argv-shape assertions
   are preserved verbatim; the USER-presence clause is a strict
   addition.
7. **ODD break strongly required.** Not triggered. The edit is a
   one-line tuple widening plus two test-function additions, each
   mapped 1:1 to a named AC.

---

## 6. ODD compliance summary

- §2.3 — Each AC is a deterministic outcome-shaped dict-invariant check.
- §2.4 — No method-in-acceptance. The AC wording specifies "scrubbed
  child env contains USER"; the method (monkeypatch target, fixture
  composition, direct `_child_env` inspection) is authored in this
  builder plan, not the amendment plan.
- §2.5 — Forward+reverse check above confirms 1:1 code-to-AC mapping.
  The `"USER"` tuple element satisfies AC-i; the AC-ii test exercises
  the pre-spawn structural invariant. No code-for-cases-no-objective-
  names.
- §3.3 — Two behaviours, two ACs, two test functions.
- §4 — Re-extension pattern applied (the USER-missing defect found
  during post-amendment #8/#11 operational review is promoted to
  named ACs).
- §5.1 — Structural over advisory: USER-presence becomes a testable
  dict invariant at construction time, not a runtime behavioural
  observation.
