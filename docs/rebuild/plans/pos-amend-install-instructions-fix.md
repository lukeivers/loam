# pos-amend install-instructions fix — plan

Dev-discipline fix. NOT a sealed-component amendment. No `pos-amend`
manifest, no SEAL_COMMIT bump, no seal commit. Plan-before-code per
the dev CDC; a single new commit lands the change.

Companion to `docs/rebuild/plans/orphan-plist-cleanup-install-
instructions-fix.md` (the prior fix at commit `741263e`, which
surfaced `tools/pos-amend/` as carrying the same problem class). The
two fixes share root cause but diverge on remedy because the two
tools' runtime contexts differ (see Decision A below).

## Summary

`tools/pos-amend/README.md` tells users to run
`pip install -e tools/pos-amend/`. On a typical pos-v2 user's
machine, the default `pip3` resolves against a Python that fails the
package's `requires-python = ">=3.11"` constraint, and the install
fails. The README is the only user-facing surface that emits the
install instruction; the fix is a documentation rewrite.

## Reproduction (from a fresh `env -i` shell on the canonical tree)

Pyenv-shimmed default (3.9.17):

```
$ pip3 install -e tools/pos-amend/
ERROR: Package 'pos-amend' requires a different Python:
       3.9.17 not in '>=3.11'
```

Stock macOS system Python (3.9.6, no pyenv on PATH):

```
$ pip3 install -e tools/pos-amend/
ERROR: File "setup.py" or "setup.cfg" not found. Directory cannot
be installed in editable mode: …/tools/pos-amend
(A "pyproject.toml" file was found, but editable mode currently
requires a setuptools-based build.)
```

Different error message, same problem class: bare `pip3` against the
default macOS Python (system or pyenv-shimmed) cannot install the
tool. The user is told to run a command that does not work.

## Root cause

Confirmed identical in shape to the orphan-plist case:

1. The tool's `pyproject.toml` sets `requires-python = ">=3.11"`.
2. The README's install instruction is `pip install -e
   tools/pos-amend/`, with no Python-version guidance.

When the user's default `pip` is bound to a Python below 3.11, pip
either refuses the install per the metadata constraint (newer pip)
or fails with a setuptools-shape error (older pip). The README
never tells the user how to ensure the right interpreter is used.

The metadata is correct — `>=3.11` is a real constraint, and the
workspace itself ships against Python 3.13+. The instruction is
wrong.

## What other surfaces emit this string?

`grep -rn "pip install -e tools/pos-amend"` across the tree:

- `tools/pos-amend/README.md` — the surface that fails. **Only
  user-facing emission.**
- `docs/rebuild/plans/amendment-22-pos-amend-cli.md` — historical
  authoring plan; mentions `pip install -e` as a validation
  criterion, not as an instruction to a user. Not user-facing.
- `docs/rebuild/plans/orphan-plist-cleanup-install-instructions-
  fix.md` — the prior fix's plan, which surfaced this case. Not an
  instruction.

No first-run helper, no diagnostic emitter, no service-supervisor
banner, no test that pins the README's install string. **The README
is the entire fix surface.**

## Important context (shapes Decision A)

`pos-amend` differs from `orphan-plist-cleanup` in two ways relevant
to the right remedy:

1. **Runtime context.** `pos-amend` is a developer tool for amendment-
   cycle bookkeeping. It is invoked *inside a pos-v2 workspace whose
   first-run has completed* — i.e. the workspace's shared venv at
   `<workspace>/.venv/` exists and has Python 3.13 ready. By contrast,
   `orphan-plist-cleanup` is a remediation tool that may run before
   or around first-run (the orphan it fixes blocks first-run health
   probes), so its README cannot assume `.venv/` is populated.
2. **Runtime dependencies.** `pos-amend`'s `pyproject.toml` declares
   `dependencies = ["PyYAML>=6"]`. A bare
   `/opt/homebrew/bin/python3.13` invocation fails at import time:

   ```
   $ /opt/homebrew/bin/python3.13 -c "import yaml"
   ModuleNotFoundError: No module named 'yaml'
   ```

   `orphan-plist-cleanup`'s `dependencies = []`, so a bare
   `python3.13` was sufficient there. Here it is not.

The workspace venv already has both Python 3.13 and PyYAML:

```
$ .venv/bin/python --version
Python 3.13.12
$ .venv/bin/python -c "import yaml; print(yaml.__version__)"
6.0.3
```

It also already has `pos-amend` installed as a console script (the
editable install was performed during amendment #22 development and
is part of every workspace's post-first-run state):

```
$ ls -la .venv/bin/pos-amend
-rwxr-xr-x  1 lukeivers  staff  199 Apr 23 13:22 .venv/bin/pos-amend
```

This means **no install action is required by the user at all**. The
tool is already installed in the venv that pos-v2 first-run produced.

## Decisions (with recommendations)

### Decision A — which Python should the instructions name?

**Options:**

A1. Workspace venv (`./.venv/bin/python`, `./.venv/bin/pos-amend`).
A2. Bare `/opt/homebrew/bin/python3.13` (the orphan-plist remedy).
A3. `pipx`.
A4. Relax `requires-python` to `>=3.9`.

**Recommendation: A1.**

Rationale:

- `pos-amend` is only ever invoked inside a populated pos-v2
  workspace (it consumes a manifest committed alongside an amendment
  plan; its raison d'être is amendment-cycle bookkeeping). The
  workspace's `.venv/` is guaranteed to exist and to have both Python
  3.13 and PyYAML.
- A2 (bare `python3.13`) needs PyYAML, which the bare interpreter
  does not have. To use A2 the user would have to either pip-install
  PyYAML into the user-site or set up a throwaway venv — both more
  steps than just naming `.venv/bin/...` directly. Reject.
- A3 (`pipx`) requires the user to install `pipx` first, plus a
  separate handling for the workspace-relative path of the
  package. Reject.
- A4 (relax metadata) widens the test matrix to 3.9, which the
  package was never validated on. Out of scope. Reject.

This diverges from the orphan-plist fix (which named
`/opt/homebrew/bin/python3.13`) for the runtime-context and
runtime-dep reasons documented above. Both choices are correct for
their respective tools.

### Decision B — install-based or no-install invocation?

**Options:**

B1. Editable install (`pip install -e`), then call console script.
B2. No-install: `.venv/bin/pos-amend` directly (the console script
    is already in the venv as part of first-run state) and a fallback
    one-liner using `PYTHONPATH=tools/pos-amend/src .venv/bin/python
    -m pos_amend ...` for trees where the editable install is for
    some reason missing.
B3. Reinstall into the venv with `.venv/bin/pip install -e
    tools/pos-amend/` and then call the console script.

**Recommendation: B2.**

Rationale:

- The workspace's `.venv/bin/pos-amend` already exists and is the
  zero-action path. Requiring a reinstall is busywork.
- The `PYTHONPATH` fallback is empirically green:

  ```
  $ PYTHONPATH=tools/pos-amend/src .venv/bin/python -m pos_amend --help
  usage: pos-amend [-h] [--version] {validate,apply,seal} ...
  ```

  It works because `pos_amend` is a standard package
  (`src/pos_amend/__main__.py` exists per the layout) and PyYAML is
  in the venv's site-packages.
- B1 (front-load editable install with explicit Python) duplicates
  what first-run already did; reject as primary path. Document it
  as an optional reinstall path for users on a tree where
  `.venv/bin/pos-amend` is somehow absent (e.g. they cloned but did
  not first-run yet — uncommon for `pos-amend` users but worth a
  one-line note).

### Decision C — where do the corrected instructions live?

**Options:**

C1. README only.
C2. README plus a runtime banner emitted by some pos-v2 surface.

**Recommendation: C1.**

Rationale:

- No other code surface emits the install string today (verified by
  grep). Adding a runtime banner would be new feature work.
- Per CLAUDE.md §2.5, code that no objective names is forbidden.
  This fix's objective is "the documented install path works." That
  doesn't require new emission code.

## Plan

1. Rewrite `tools/pos-amend/README.md`'s **Install** section to:
   - Lead with `.venv/bin/pos-amend` as the primary invocation; no
     install required because first-run already did it.
   - Note macOS + Python 3.13 prerequisite once, near the top.
   - Add a "if `.venv/bin/pos-amend` is missing" optional section
     describing the `.venv/bin/pip install -e tools/pos-amend/`
     reinstall path with explicit interpreter, plus the
     `PYTHONPATH=…` fallback one-liner that does not require any
     install.
   - Numbered, time-estimated, runnable verbatim.
2. Verify `tools/pos-amend/tests/` still pass against the canonical
   tree (the README change does not touch code, but run the suite
   as a regression sanity check).
3. Single new git commit. No `--amend`. No SEAL_COMMIT bump.
4. Verify the user-facing path works end-to-end from a fresh
   `env -i` shell on the canonical tree.

## Acceptance criteria

**AC1 — A non-technical user, on a macOS host where pos-v2's
prerequisites are met and first-run has completed, can paste the
README's primary instruction verbatim into a terminal and
`pos-amend --help` (or `pos-amend validate <some.yaml>`) reports
output.**

Verified by manually executing the README's numbered steps on the
canonical tree from a fresh `env -i` shell.

**AC2 — Existing tests still pass.**

`.venv/bin/python -m pytest tools/pos-amend/tests/ -q` is green at
the post-fix tree. (No code is changed, so this is a regression
check.)

**AC3 — The README explicitly tells the user how to ensure the
right Python is used.**

The instructions name `.venv/bin/python` / `.venv/bin/pos-amend`
(not bare `python3` / `pip3`). A verbatim grep confirms unguarded
`pip install -e tools/pos-amend/` no longer appears as the primary
path; if it appears at all, it appears in an explicitly optional
section that also names a specific interpreter.

## Halt triggers

1. If the README's pre-fix install string turns out to be emitted
   from sealed-component code (it isn't, per the grep — but if a
   future read finds otherwise), halt — that is an amendment cycle.
2. If the no-install invocation fails on the canonical tree (it
   doesn't, per reproduction above — but if surface conditions
   change), halt and reconsider Decision B.
3. If the fix surface grows beyond the README (more than two files
   counting this plan), halt — that is a scope smell.

## Outcome match check (run at completion)

- This plan exists at the path above.
- README at `tools/pos-amend/README.md` rewritten per Decision
  A1/B2/C1.
- `.venv/bin/python -m pytest tools/pos-amend/tests/ -q` is green.
- A fresh-`env -i`-shell run of the README's primary path on the
  canonical tree exits 0.
- Single new commit lands the change. No `--amend`. No
  SEAL_COMMIT bump. No `pos-amend` manifest.
