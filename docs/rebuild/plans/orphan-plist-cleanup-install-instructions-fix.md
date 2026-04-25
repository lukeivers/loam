# orphan-plist-cleanup install-instructions fix — plan

Dev-discipline fix. NOT a sealed-component amendment. No `pos-amend`
manifest, no SEAL_COMMIT bump, no seal commit. Plan-before-code per
the dev CDC; a single new commit lands the change.

Companion to `docs/rebuild/plans/orphan-plist-cleanup-tool.md` (the
plan that originally landed the tool at commit `8846908`).

## Summary

The tool's README tells users to run `pip install -e
tools/orphan-plist-cleanup/`. On a typical pos-v2 user's machine, the
default `pip` resolves against a Python that fails the package's
`requires-python = ">=3.11"` constraint, and the install fails. The
README is the only user-facing surface that emits the install
instruction; the fix is a documentation rewrite.

## Reproduction (from a fresh shell on the canonical tree)

```
$ which python3 pip3
/Users/lukeivers/.pyenv/shims/python3
/Users/lukeivers/.pyenv/shims/pip3
$ python3 --version
Python 3.9.17
$ pip3 install -e tools/orphan-plist-cleanup/
…
ERROR: Package 'orphan-plist-cleanup' requires a different Python:
       3.9.17 not in '>=3.11'
```

Same failure shape applies on any macOS where the user's bare
`python3`/`pip3` is the system Python (3.9.x on stock macOS) or any
pyenv-managed older Python.

## Root cause

The README composes two assumptions that don't hold together on
default-PATH macOS:

1. The tool's `pyproject.toml` sets `requires-python = ">=3.11"`.
2. The README's install instruction is `pip install -e
   tools/orphan-plist-cleanup/`, with no Python-version guidance.

When the user's default `pip` is bound to a Python below 3.11, pip
refuses the install per the metadata constraint. The README never
tells the user how to ensure the right Python is used.

The metadata is correct — `>=3.11` is a real constraint of the package
and pos-v2 itself ships against Python 3.13+ (`first-run-inventory.yaml`
declares `python_version: ">=3.13"`). The instructions are wrong.

## What other surfaces emit this string?

`grep -rn "orphan-plist-cleanup"` across the tree:

- `tools/orphan-plist-cleanup/README.md` — the surface that fails.
- `tools/orphan-plist-cleanup/pyproject.toml` — package metadata; not
  a user-facing instruction.
- `tools/orphan-plist-cleanup/src/orphan_plist_cleanup/{__init__,cli}.py`
  — internal program text (`prog=` argparse name, etc.); not install
  instructions.
- `docs/rebuild/plans/orphan-plist-cleanup-tool.md` — the original
  build plan; mentions `pip install -e`-ability as a validation
  criterion, not as an instruction to a user.
- `tools/orphan-plist-cleanup/tests/conftest.py` — test fixture; no
  instruction text.

No first-run helper, no diagnostic emitter, no service-supervisor
banner, no test that pins the README's install string. **The README
is the entire fix surface.**

## Decisions (with recommendations)

### Decision A — which Python should the instructions name?

**Options:**

A1. Tell the user to use `/opt/homebrew/bin/python3.13` directly.
A2. Tell the user to use the workspace's `.venv/` (`./.venv/bin/...`).
A3. Tell the user to use `pipx`.
A4. Relax `requires-python` to `>=3.9` to match stock macOS Python.

**Recommendation: A1, with A2 as a fallback note for users who
already have the workspace venv populated.**

Rationale:

- pos-v2 itself requires Python 3.13+ (`first-run-inventory.yaml`).
  Any user with a working pos-v2 install already has Python 3.13
  installed somewhere — typically Homebrew's `python@3.13` formula at
  `/opt/homebrew/bin/python3.13`. Naming this path is not a new
  prerequisite; it is the existing prerequisite made explicit.
- A2 (workspace venv) works on machines where first-run has run, but
  this tool is a *remediation* tool that may run before/around
  first-run (the orphan it fixes blocks first-run health probes). It
  is fragile to require a populated `.venv/`.
- A3 (`pipx`) requires the user to install `pipx` first — which has
  the same bootstrap problem as the tool itself. Reject.
- A4 (relax metadata) widens the test matrix to 3.9, which the
  package was never validated on. The package uses `from __future__
  import annotations` so the syntax surface is portable, but
  validating 3.9 compatibility is engineering work outside this
  fix's scope. Reject.

### Decision B — install-based or no-install invocation?

**Options:**

B1. Editable install (`pip install -e`), then call console script.
B2. No-install: invoke the source directly via `python -m
    orphan_plist_cleanup` with `PYTHONPATH` pointing at the source.
B3. Both — document B2 as the primary path, leave B1 as an optional
    follow-up for users who want the console script.

**Recommendation: B3, with B2 as primary.**

Rationale:

- The tool is **stdlib-only** (`dependencies = []`). There is no
  reason to require an install for a one-shot remediation.
- B2 leaves no trace. The user does not pollute the chosen Python's
  site-packages with a tool they will run once.
- Empirically verified on the canonical tree:

  ```
  $ PYTHONPATH=tools/orphan-plist-cleanup/src \
      /opt/homebrew/bin/python3.13 -m orphan_plist_cleanup --dry-run
  /Users/lukeivers/Library/LaunchAgents/com.pos.orchestrator.plist
  ```

  Exit 0, real orphan detected, no install performed.
- B1 (editable install) remains useful for someone who wants a
  PATH-resolvable `orphan-plist-cleanup` shim. Documenting it as a
  "if you'd rather have the console script" footnote preserves the
  option without front-loading the failure.

### Decision C — where do the corrected instructions live?

**Options:**

C1. README only.
C2. README plus a runtime banner emitted by some pos-v2 surface.

**Recommendation: C1.**

Rationale:

- No other code surface emits the install string today (verified by
  grep). Adding a runtime banner would be new feature work, not a
  fix to a broken instruction.
- Per CLAUDE.md §2.5, code that no objective names is forbidden.
  This fix's objective is "the documented install path works." That
  doesn't require new emission code.

## Plan

1. Rewrite `tools/orphan-plist-cleanup/README.md`'s **Install** /
   **Run** sections to:
   - Lead with the no-install one-liner using `python3.13` from the
     workspace root.
   - Include numbered steps a non-technical user can paste verbatim,
     each step labelled with a wall-clock estimate.
   - Add a "if you want the console script on PATH" optional section
     describing the editable-install path with explicit Python.
   - Note macOS + Python 3.13 prerequisite once, near the top, and
     do not assume the user knows which `python3` is which.
2. Verify `tools/orphan-plist-cleanup/tests/` still pass against the
   canonical tree (the README change does not touch code, but run
   the suite as a regression sanity check).
3. Single new git commit. No `--amend`. No SEAL_COMMIT bump.
4. Verify the user-facing path works end-to-end from a fresh shell
   whose bare `python3`/`pip3` is the system / pyenv 3.9 (the
   reproducer's shell).

## Acceptance criteria

**AC1 — A non-technical user, on a macOS host where pos-v2's
prerequisites are met, can paste the README's primary instructions
verbatim into a terminal and `--dry-run` reports orphans (or the
empty-orphan-set success path).**

Verified by manually executing the README's numbered steps on the
canonical tree from a fresh shell.

**AC2 — Existing tests still pass.**

`pytest tools/orphan-plist-cleanup/tests/ -q` is green at the
post-fix tree. (No code is changed, so this is a regression check.)

**AC3 — The README explicitly tells the user how to ensure the
right Python is used.**

The instructions name `python3.13` (not bare `python3` / `pip3`). A
verbatim grep confirms `pip install -e` no longer appears as the
primary path; if it appears at all, it appears in an explicitly
optional section that also names `python3.13`.

## Halt triggers

1. If the README's pre-fix install string turns out to be emitted
   from sealed-component code (it isn't, per the grep — but if a
   future read finds otherwise), halt — that is an amendment cycle,
   not dev-discipline.
2. If the no-install invocation fails on the canonical tree (it
   doesn't, per reproduction above — but if surface conditions
   change), halt and reconsider Decision B.
3. If the fix surface grows beyond the README (more than three
   files, excluding this plan), halt — that is a scope smell.

## Halt-and-surface (cross-tool finding for the owner to rule on)

`tools/pos-amend/README.md` carries the same problem class:
`requires-python = ">=3.11"` plus a `pip install -e tools/pos-amend/`
instruction with no Python-version guidance. Reproduced under the
same shell:

```
$ pip3 install -e tools/pos-amend/
ERROR: Package 'pos-amend' requires a different Python:
       3.9.17 not in '>=3.11'
```

Per the brief's scope rule, this fix does **not** touch
`tools/pos-amend/`. Surfacing for the owner to scope as a separate
follow-up if desired.

## Outcome match check (run at completion)

- This plan exists at the path above.
- README at `tools/orphan-plist-cleanup/README.md` rewritten per
  Decision A1+A2/B3/C1.
- `pytest tools/orphan-plist-cleanup/tests/ -q` is green.
- A fresh-shell run of the README's primary path on the canonical
  tree exits 0 and either lists orphans or reports none.
- Single new commit lands the change. No `--amend`. No
  SEAL_COMMIT bump. No `pos-amend` manifest.
