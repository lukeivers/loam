# Research — memory-system env-scrubber (D4)

**Status:** research for the D4 amendment cycle. Produced 2026-04-23 under
the research plan at
`docs/plans/research/memory-system-env-scrubber-research-plan.md`.
Downstream: an amendment plan document is authored from this research; the
research does not itself prescribe method or AC wording.

---

## Executive summary

1. `USER` is the single additional env var required for `claude -p` OAuth
   under any surface pos-v2 realistically touches. Empirical bisection
   confirms PATH+USER suffices; HOME, LOGNAME, TMPDIR, __CF_USER_TEXT_ENCODING
   are not required for the OAuth path. The value must match the real login
   name — an empty or mismatched `USER` reproduces "Not logged in".
2. macOS launchd gui-domain (pos-v2's only target today) injects
   USER/HOME/LOGNAME/TMPDIR/__CF_USER_TEXT_ENCODING into every agent-spawned
   process despite `launchctl getenv` returning empty for them — verified
   against the live `com.pos-v2.pos3.memory-graphiti` service pid. The vars
   are therefore *available in* `os.environ` at scrubber time; they just
   need to be on the allowlist.
3. The USER-missing defect slipped two seals because AC2's test asserts
   API-key absence and PATH presence but never positive-presence of USER,
   and every test mocks `asyncio.create_subprocess_exec` so no test crosses
   the real-subprocess boundary. This is §8.2.10's "tests that mock the
   thing the objective actually promises to work with" pattern.
4. Test-shape candidates that would have caught the defect: (a) an `env -i`
   shell probe driving the real `claude` binary behind a skip-if-missing
   guard; (b) a pure-Python fake-claude that validates the inbound env
   against the login-user's expected identity; (c) a construction-time
   structural check that verifies the scrubbed-env dict contains USER
   before the first subprocess call. All three are viable without ODD
   method-prescription if the AC is shaped against outcomes.
5. No other pos-v2 component applies an env scrubber. Hands-off-lifecycle's
   `first_run_dispatch.py` uses `os.environ.copy()` (full passthrough);
   workspace-bootstrap's memory_system adapter spawns children without
   touching env; orchestrator scripts spawn unscrubbed. D4 has no
   cross-component blast radius. No halt under §4.1.

**Top candidate amendment-shape surfaced for owner ruling** — a two-AC
amendment on memory-system: (i) an allowlist-widening AC that promotes
USER to an objective-backed member of the scrubber's contract (with AC2's
test extended to positive-assert USER presence under a monkeypatched parent
env), and (ii) a test-shape AC that verifies the scrubbed-env dict at
subprocess-spawn time contains the login user's USER value, achievable
without any real `claude` subprocess. The §4.2 halt trigger is not tripped
because all three candidate shapes can be stated outcome-first. Option (c)
in §Q2 is the lowest-ceremony shape and is the recommended default for the
plan author, with the owner's ruling invited if a heavier end-to-end
integration test is preferred.

---

## Q1 — Beyond USER, what other env vars does `claude -p` require?

### Q1 claim

`USER` is the only additional env var required beyond PATH for
`claude -p`'s OAuth path to resolve under every execution surface pos-v2
will touch. HOME is not strictly required for OAuth; LOGNAME does not
substitute for USER; __CF_USER_TEXT_ENCODING and TMPDIR do not contribute
to the OAuth success path. macOS gui-domain launchd (pos-v2's only target)
injects USER into spawned-agent processes automatically, so the
requirement reduces to an allowlist-widening, not an env-injection.

### Q1 evidence — empirical bisection of `env -i ...`

Performed on the canonical tree's host 2026-04-23 against
`claude 2.1.119 (Claude Code)` at `/Users/lukeivers/.local/bin/claude`.
Every probe invokes:

    env -i <vars> claude -p --no-session-persistence \
        --output-format json --model claude-haiku-4-5 "reply with OK"

and inspects `is_error` and `result` fields on the emitted JSON envelope.

| # | Env set                                   | is_error | result                                  |
|---|-------------------------------------------|----------|-----------------------------------------|
| 1 | PATH                                      | true     | "Not logged in · Please run /login"     |
| 2 | PATH + HOME                               | true     | "Not logged in · Please run /login"     |
| 3 | PATH + HOME + USER                        | **false**| **"OK"**                                |
| 4 | PATH + USER (no HOME)                     | **false**| **"OK"**                                |
| 5 | USER + HOME (no PATH)                     | —        | `env: claude: No such file or directory`|
| 6 | PATH + LOGNAME (no USER)                  | true     | "Not logged in · Please run /login"     |
| 7 | PATH + HOME + __CF_USER_TEXT_ENCODING     | true     | "Not logged in · Please run /login"     |
| 8 | PATH + USER + TMPDIR                      | false    | "OK"                                    |
| 9 | PATH + USER + SHELL + LANG                | false    | "OK"                                    |
|10 | PATH + USER=someotheruser                 | true     | "Not logged in · Please run /login"     |
|11 | PATH + USER= (empty)                      | true     | "Not logged in · Please run /login"     |

Probes 3, 4, 8, 9 all succeed; 4 pins the minimum at `PATH + USER`. Probes
10, 11 pin that USER must match the real login name (keychain lookup
identity); it is not a presence-only signal. Probe 6 rules out LOGNAME as
a substitute. Probe 7 rules out __CF_USER_TEXT_ENCODING. Probe 5 confirms
PATH is still required — for binary resolution, not OAuth — so the minimum
allowlist is **PATH + USER**.

### Q1 evidence — launchd domain analysis

The research plan separates Q1(a) launchd gui domain, Q1(b) launchd aqua
domain, Q1(c) non-interactive login shells. The separation collapses on
modern macOS:

- `launchctl print user/$(id -u)` returns `type = user`, with the
  `gui/501` bootstrap subdomain as the only agent-spawning context. "Aqua"
  was the legacy alias for this domain on pre-launchd-`bsexec` macOS; no
  separate Aqua-vs-gui split exists on the host under test.
- `launchctl getenv USER / HOME / PATH / LOGNAME` all return empty at the
  gui-domain level, yet `ps eww -p <pid>` against the live
  `com.pos-v2.pos3.memory-graphiti` service pid 73151 shows the process
  has inherited USER=lukeivers, HOME=/Users/lukeivers, LOGNAME=lukeivers,
  TMPDIR=.../, __CF_USER_TEXT_ENCODING=0x1F5:0x0:0x0, plus
  PATH=/Users/lukeivers/.local/bin:/opt/homebrew/bin:..., PYTHONUNBUFFERED=1,
  XPC_SERVICE_NAME, XPC_FLAGS. Launchd's loginwindow session exports these
  at process-spawn from the user's session-context, independent of what
  `launchctl print`'s `environment` dict shows. (The `environment` dict only
  lists vars explicitly declared in the plist.)
- Non-interactive shells invoked under the same user session
  (`/bin/bash -c 'env'`) also surface USER/HOME/LOGNAME/PATH/TMPDIR,
  matching the gui-domain inheritance.

Consequence: the scrubber does NOT need to synthesise USER. It needs to
whitelist USER so it survives the `os.environ` → `child_env` pass.

### Q1 implication

- The D4 amendment plan adds exactly one var — USER — to
  `_ENV_ALLOWED_VARS`.
- LOGNAME is explicitly NOT added. It does not substitute for USER on
  macOS and pos-v2 is macOS-only today per STATE.md and §2.5's
  Linux-removal history (amendment #10).
- __CF_USER_TEXT_ENCODING and TMPDIR are NOT added. They do not
  contribute to the OAuth path; adding them would be §2.5
  code-for-cases-no-objective-names.
- HOME retains membership. Even though PATH+USER suffices today for
  OAuth, HOME is load-bearing for any claude-CLI code path that reads
  `~/.claude/*` config (skills, settings.json, plugins, permissions).
  Removing HOME now would re-introduce a similar class of silent
  failure if any future claude-CLI invocation expands to a
  config-reading path.

---

## Q2 — What test-shape would have caught the USER-missing defect?

### Q2 claim

Three viable test-shapes exist; none requires method-in-AC prescription
if the AC is shaped against outcome. The lowest-ceremony shape is a
construction-time assertion on the scrubbed-env dict's contents,
exercisable without any real `claude` subprocess and extending the
existing AC2 test pattern directly. An `env -i` real-subprocess probe
(behind a skip-if-binary-missing guard) is the most faithful to the
external surface but costs a skip-under-CI dependency the owner may or
may not want to accept.

### Q2 evidence — candidate shapes examined

**Candidate A — construction-time scrubbed-env assertion.**

Shape: AC-level statement is *"the scrubbed env passed to every
`claude -p` subprocess contains the login user's USER value when USER is
present in the parent env."* Test mocks `asyncio.create_subprocess_exec`
(as AC2 already does) and inspects the `env` kwarg's `call_args`
post-invocation. Extends the existing AC2 test pattern by one positive
assertion; no new infrastructure. The subprocess is still mocked, but the
failure mode the test catches — USER dropped from the allowlist — is
structural, not behavioural, and does not require a real subprocess to
detect. Satisfies §5.3's structural-over-advisory preference (the failure
mode becomes a missing dict key, not a runtime "Not logged in" message).
The test-shape-as-stated is outcome-shaped: the **state** being asserted is
"env dict contains USER=<login-user>," not any specific method by which
the dict was constructed.

**Candidate B — launchd-simulator `env -i` probe driving real claude.**

Shape: AC-level statement is *"under a parent env containing only the
allowlisted vars, `claude -p` resolves OAuth and returns a non-error
response."* Test launches a real `claude` subprocess with an
`env -i PATH=<path> USER=<user> HOME=<home>` parent to mimic the
fully-scrubbed surface. This directly asserts the behaviour pos-v2 relies
on at production. Costs: (i) every CI / dev workstation running the test
needs `claude` installed AND authenticated (running `claude /login` once);
(ii) the test consumes a Max-subscription call per run; (iii) auth state
drift (token expiry on a CI runner) becomes test flake. Skippable via
pytest.importorskip-style guard on `shutil.which('claude')` + probe, but
the skip itself weakens the seal if CI always skips.

**Candidate C — pure-Python fake-claude subprocess.**

Shape: a small Python test-only helper at a well-known path (e.g.
`tests/_fake_claude.py`) that, when invoked as a subprocess, reads its
env, writes a synthetic `claude -p --output-format json` envelope whose
`result` encodes whether USER was present and matched the expected login.
The AC-level statement is *"when the scrubber spawns a binary matching
the `claude -p` call contract, the binary observes USER in its inbound
env."* The test patches `shutil.which` to return the fake-claude path;
spawns through the real `asyncio.create_subprocess_exec` (no mock); reads
the synthetic envelope back and asserts `result` encodes a success. This
is an end-to-end subprocess test *without* a real claude dependency.
Higher setup cost than (A) (one helper file to maintain) but lower ongoing
cost than (B).

### Q2 evidence — existing AC2 test coverage gap

`memory-system/tests/test_claude_print_client.py::test_AC2_subprocess_argv_and_env_scrubbed`
asserts:

- argv shape (positional args match `claude -p --no-session-persistence --output-format json --model <model>`)
- `--bare` is absent
- `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are NOT in env
- `PATH` IS in env

It does NOT assert:

- USER is in env
- HOME is in env
- the env set is exactly `{PATH, HOME}` / `{PATH, HOME, USER}` / any other
  closed set — the current test only catches drift in the leak direction
  (API keys leaking through) and one presence direction (PATH). The
  opposite drift (USER dropping off, as happened) is invisible to AC2's
  test by construction.

Any of the three candidate shapes closes the coverage gap. Candidate A
closes it cheapest; candidate C closes it against a broader class of
future subprocess-env bugs (anything where the process sees a different
env than the scrubber thinks it assembled).

### Q2 implication

- No §4.2 halt: all three candidate shapes are authorable without
  method-prescription in the AC. The AC wording that makes this work
  is "the scrubbed env contains the login user's USER value" —
  outcome-shaped; the method (dict assertion vs real subprocess vs
  fake-claude) is the builder's call.
- Recommendation to the plan author: candidate A for the D4 amendment's
  minimum viable gap-closure. Candidate C is a strictly-stronger
  alternative the builder may choose during method selection; candidate
  B is not recommended (real-claude auth flake cost > signal).
- The plan author does not need to choose between A/B/C in the plan —
  the AC is stated as outcome; the builder chooses which of A/B/C
  satisfies it when writing the test.

---

## Q3 — Scope of the allowlist widening

### Q3 claim

The final allowlist is `(PATH, HOME, USER)`. LOGNAME,
__CF_USER_TEXT_ENCODING, TMPDIR, SHELL, LANG, and all other candidates
surveyed are ruled OUT with evidence.

### Q3 evidence

| Candidate                   | Ruling | Evidence                                                                                                           |
|-----------------------------|--------|--------------------------------------------------------------------------------------------------------------------|
| `USER`                      | IN     | Q1 probes 3, 4, 8, 9 all succeed when USER present; probes 1, 2, 6, 7, 10, 11 all fail without USER (or with wrong USER). Empirical minimum. |
| `HOME`                      | KEEP   | Currently allowlisted. Not strictly required for OAuth (Q1 probe 4). Load-bearing for any future claude-CLI path that reads `~/.claude/*` (skills, settings, plugins). Removing now is a §2.5 reverse violation — the current AC2 authored HOME into the scrubber; removing it would need its own objective. |
| `PATH`                      | KEEP   | Currently allowlisted. Required for `claude` binary resolution inside the child (Q1 probe 5: child fails with "No such file or directory" when PATH absent even if OAuth env is complete). |
| `LOGNAME`                   | OUT    | Q1 probe 6: PATH + LOGNAME still produces "Not logged in". Does not substitute for USER on macOS. pos-v2 is macOS-only (STATE.md + amendment #10). No Linux-precedent argument applies. |
| `__CF_USER_TEXT_ENCODING`   | OUT    | Q1 probe 7: adding it does not change the OAuth outcome. Known macOS-specific var set by CoreFoundation for text-encoding preferences; no observed claude-CLI dependency. §2.5: code-for-cases-no-objective-names. |
| `TMPDIR`                    | OUT    | Q1 probe 8: PATH + USER + TMPDIR succeeds, but PATH + USER alone (probe 4) already succeeds — TMPDIR adds no OAuth signal. claude-CLI may use /tmp as fallback when TMPDIR is unset; if a future code path surfaces a TMPDIR requirement, re-extend with a named objective. |
| `SHELL`, `LANG`             | OUT    | Q1 probe 9: succeed alongside PATH + USER but redundant with probe 4. No OAuth dependency. |
| `ANTHROPIC_API_KEY`         | OUT (forbidden) | AC2's core intent is to keep this OUT. Whitelisting it would re-enable the billed-API fallthrough AC2 exists to prevent. |
| `OPENAI_API_KEY`, `GEMINI_API_KEY` | OUT (forbidden) | Same reasoning as above — AC8's invariant depends on these being absent from the child env. |
| `CLAUDE_CODE_*`, `CLAUDECODE` | OUT | Present in the pos3 session's parent env because Claude Code is running, but represent "this is nested inside another claude" state. No OAuth contribution; adding would couple child's identity to parent's surface. |
| `XPC_SERVICE_NAME`, `XPC_FLAGS`, `OSLogRateLimit` | OUT | launchd-injected vars that name the parent service; no downstream meaning to `claude -p`. |

### Q3 implication

- The amendment adds exactly one line to `_ENV_ALLOWED_VARS`: `"USER"`.
- The docstring above `_ENV_ALLOWED_VARS` is updated to name USER's
  role (keychain identity for OAuth resolution under launchd's
  scrubbed parent env).
- The "If a runtime failure later shows `claude -p` needs another var"
  line in the existing docstring (amendment #11 §F5 ruling) stays —
  its rule ("add together with a concrete AC extension naming the
  failure observed") is exactly the §4.1 re-extension discipline.
- Every other candidate above is ruled out with evidence; future
  amendments that propose adding one of them must cite a concrete
  empirical failure mode, per the re-extension pattern.

---

## Q4 — Broader pattern to codify?

### Q4 claim

No other pos-v2 component applies an env scrubber today, and no
cross-component blast radius exists for D4. The `POST_FIRST_RUN_REVIEW.md`
entries #2 (env-scrubber allowlist drift) and #3 (AC tests that mock too
close to the component boundary) are genuinely general patterns, but each
has a different home and different natural shape. A generalised
"scrubbed-env subprocess" test harness convention is premature — there is
only one call site to harness against — and belongs in FUTURE_IDEAS /
BACKLOG rather than inside D4's amendment scope. §4.1 halt trigger is NOT
tripped.

### Q4 evidence — subprocess-spawn inventory across the canonical tree

`grep -rnE "subprocess\.(run|Popen|check|call)|create_subprocess"` across
production (non-test, non-script) source:

| Call site | Env treatment |
|-----------|----------------|
| `memory-system/src/claude_print_client.py::_build_child_env` (2 spawns: probe + `_generate_response`) | Scrubbed allowlist. **Only scrubber in the tree.** |
| `hands-off-lifecycle/hooks/first_run_dispatch.py::spawn` | `env = os.environ.copy(); env["PYTHONUNBUFFERED"] = "1"`. Full passthrough + one explicit var. No scrub. |
| `hands-off-lifecycle/hooks/first_run_helper.py` (7 spawns: `launchctl bootstrap/bootout/list/print`, etc.) | No `env=` kwarg — inherits parent env. |
| `workspace-bootstrap/src/.../adapters/memory_system.py::contribute` | `subprocess.Popen(command, stdout=DEVNULL, stderr=DEVNULL)`. No `env=`; inherits. |
| `workspace-bootstrap/src/.../adapters/self_upgrade.py` | No `env=`; inherits. |
| `workspace-bootstrap/src/.../adapters/first_run_scaffold.py` (2 bootout spawns) | No `env=`; inherits. |
| `self-upgrade/src/self_upgrade/orchestrator_control.py` (2 spawns) | No `env=`; inherits. |
| `orchestrator/scripts/install_launchd.py`, `pos_session_start.py`, `measure_launchd.py` | No `env=`; inherits. |
| `tools/pos-amend/src/pos_amend/` (git spawns) | No `env=`; inherits. |

Only memory-system's `claude_print_client.py` applies an env scrubber.
Every other subprocess-spawning call site in production code either
inherits parent env unchanged or adds a single var (PYTHONUNBUFFERED)
without scrubbing. There is no cross-component pattern to generalise.

### Q4 evidence — POST_FIRST_RUN_REVIEW entries #2 and #3

Entry #2 ("env-scrubber allowlist drift") names the specific defect D4
closes and asks the broader question: *"under what other realistic
execution environments (Docker, systemd user services on Linux, containerised
CI) would the current allowlist fail silently?"* This question is forward-
looking against deployment surfaces pos-v2 does not currently target
(Linux is explicitly out-of-scope per amendment #10). Answering it is
speculative until a deployment surface actually lands. Disposition
recommendation per §4 acceptance: note the forward question in D4's
amendment plan but do NOT scope it; leave entry #2's review-trigger in
place for post-launch re-evaluation.

Entry #3 ("AC tests that mock too close to the component boundary")
names a general §8.2.10 anti-pattern family that applies across
*any* pos-v2 component integrating with an external surface (OS
keychain, launchd, Ollama, Kuzu, neo4j, claude CLI, MCP servers,
Telegram API). This is a legitimate cross-cutting pattern — but codifying
it as a pos-v2 convention is larger than D4. Entry #3's own review-trigger
says "flag for an integration-test extension" per-component; the generic
convention belongs in FUTURE_IDEAS as an Idea (analogous to Idea 8's
structural context-load gate) authored from the cross-component
observation set. D4 contributes one data point (the claude-CLI boundary)
to that observation set; it does not author the convention itself.

### Q4 implication

- No §4.1 halt. The cross-component pattern question is genuine but does
  not require D4 to resolve.
- D4's scope stays **memory-system-only**: allowlist widening + test-shape
  gap closure at the AC2-level.
- Two register updates accompany D4's commit (non-blocking on the
  amendment itself, noted for the plan author):
  - `POST_FIRST_RUN_REVIEW.md` entry #2's review-trigger: replace "After
    D4 lands, decide whether to add a launchd-simulator test fixture…"
    with a pointer to D4's landed shape. The "Docker / systemd / CI"
    question stays open in the register pending a real target surface.
  - `POST_FIRST_RUN_REVIEW.md` entry #3's review-trigger: add "memory-
    system / claude-CLI env boundary" as one named instance of the
    general pattern. The generalised-convention authoring is a
    downstream FUTURE_IDEAS entry, not an AC of D4.

---

## §4 halt triggers — assessment

1. **Research reveals cross-component implications.** NO. Q4 confirmed the
   scrubber is memory-system-only. D4 does not widen.
2. **No test shape is verifiable without method-prescription.** NO. Q2
   surfaces three candidate shapes, each of which is authorable with an
   outcome-shaped AC; candidate A is the lowest-ceremony. ODD compliance
   achievable.
3. **Empirical bisection yields non-deterministic results.** NO. The Q1
   bisection table is stable across retries; failure/success conditions
   reproduce deterministically on the canonical host.
4. **ODD break strongly required.** NO. The amendment-shape surfaced in
   the executive summary is fully ODD-compliant: outcome-stated ACs,
   deterministic test-shapes, 1:1 criterion-to-test mapping, structural
   refusal at the scrubber construction boundary.

No halts. Research completes cleanly.

---

## Inputs the plan author inherits

The plan author authoring the D4 amendment plan from this research can
rely on:

1. The final allowlist is `(PATH, HOME, USER)` with evidence in §Q3.
2. AC2 widens to positive-assert USER's presence; AC wording stated as
   outcome (the scrubbed env contains the login user's USER value);
   method (dict assertion vs real-subprocess vs fake-claude) is the
   builder's call per §Q2.
3. Cross-component scope: none. D4 touches only `memory-system/src/`
   and `memory-system/tests/`. No sealed-component amendment elsewhere.
4. Error-code block: no new codes; the amendment extends an existing
   allowlist contract without introducing new failure modes.
5. The §Q4 register updates to `POST_FIRST_RUN_REVIEW.md` are
   optional-but-recommended; scope them into the plan or carry them
   separately at the plan author's discretion.
