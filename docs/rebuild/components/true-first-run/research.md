# Research — True First-Run

**Status:** DRAFT — awaiting owner G2 approval.
**Authored by:** Research Agent on Eve's behalf.
**Date:** 2026-04-22.
**Plan:** `research-plan.md` in this directory (approved at G1).

---

## 0. Framing (what this research produced against)

This document answers the eleven question groups in the research plan §5, with dispositions for the §4 central tension, concrete mechanics for the four gaps surfaced in §1, and a named amendment inventory for §11. Readings grounded in:

- `/Users/lukeivers/ivers-corp-pos-v2/hands-off-lifecycle/hooks/settings.json.fragment` — the sealed hook shape.
- `/Users/lukeivers/ivers-corp-pos-v2/orchestrator/scripts/pos_session_start.py` — the helper the hook invokes.
- `/Users/lukeivers/ivers-corp-pos-v2/workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` — the in-process scaffold already shipped by hands-off-lifecycle Amendment 4.
- `/Users/lukeivers/ivers-corp-pos-v2/memory-system/launchd/com.pos-v2.memory-graphiti.plist` — hardcoded-path plist (not a `.tmpl`).
- `/Users/lukeivers/ivers-corp-pos-v2/orchestrator/ops/launchd/com.pos.orchestrator.plist.tmpl` — `.tmpl` form.
- `/Users/lukeivers/ivers-corp-pos-v2/orchestrator/ops/systemd/pos-orchestrator.service.tmpl` and `/Users/lukeivers/ivers-corp-pos-v2/memory-system/systemd/pos-v2-memory-graphiti.service.tmpl` — Linux counterparts.
- All twelve component `requirements.txt` / `pyproject.toml` files.
- Claude Code hooks documentation at `https://code.claude.com/docs/en/hooks` (fetched 2026-04-22).

**Honest observation from the pos-v2 tree:** Amendment 4 of hands-off-lifecycle (`first_run_scaffold.py`) already implements a surprising amount of what this component needs — the scaffold writes plists, bootstraps services, emits the confirmation sentence. What it does *not* do is (a) author `.claude/settings.json`, (b) create the `.venv/`s, (c) install dependencies, (d) handle the chicken-and-egg of running before the venv exists. The true-first-run component fills those four gaps and delegates to the existing scaffold where possible. This substantially narrows scope from the plan's framing.

Critical correction to a plan assumption: the plan says "the hands-off-lifecycle hook currently references `${POS_V2_REPO}/.venv/bin/python`". Confirmed — `settings.json.fragment` literally contains that string. On a fresh clone, that path does not exist. First-run must be upstream of that hook firing meaningfully. This is the crux.

---

## 1. Survey of existing patterns

Five concrete precedents from developer-tooling space. Each is evaluated for what it contributes to the pos-v2 decision and what it explicitly is not.

### 1.1 Homebrew first-run

On `brew install` for the first time, Homebrew's `install.sh` script (curl-piped) downloads a tarball, places it, creates `/opt/homebrew`, and chowns. The script is **POSIX shell** (not bash-specific), checks prerequisites (macOS version, Xcode Command Line Tools presence), and fails loudly on any gap. Subsequent `brew` invocations use a Ruby entry point that requires the Ruby already bootstrapped by macOS. **Relevance:** Homebrew's shell-first boot of a higher-level runtime is directly analogous. The pattern is "shell does the irreducible minimum; language runtime takes over after."

### 1.2 pyenv init

`pyenv init` is evaluated in a shell rc file: `eval "$(pyenv init -)"`. This is a **lazy shell integration**, not a first-run installer. The installer itself (git clone, or `curl | bash`) is separate. **Relevance:** pyenv demonstrates the clean separation between (a) one-time installation and (b) per-shell initialization. pos-v2's analog: first-run creates `.venv/`s and installs services once; the `SessionStart` hook is the equivalent of the shell rc — it runs every session and assumes installation is done.

### 1.3 pre-commit install-on-first-use

pre-commit has two installation paths: `pre-commit install` (writes `.git/hooks/pre-commit`) and `pre-commit install --install-hooks` (same, plus eagerly creates each hook's environment). When `--install-hooks` is omitted, each hook's environment is created **on first use** — the first time the hook needs it. `pre-commit run` auto-bootstraps missing environments. **Relevance:** strong precedent for lazy-but-automatic environment creation. The user never runs a separate setup command; the tool just does it on first invocation. This is the shape pos-v2 wants.

### 1.4 Docker Desktop first-run

First `docker` command after install prompts for root (to install the helper), then writes state to `~/.docker/`, seeds default config, starts the daemon. GUI-first onboarding is not directly translatable — but the **write-everything-into-`~/.docker`-and-assume-it-exists-next-time** pattern is exactly the shape first_run_scaffold already uses (`~/.pos/`).

### 1.5 VS Code extension activation

VS Code extensions declare `activationEvents` in `package.json`. On first match (file opened, command invoked, etc.), the extension host runs `activate()`. The extension author writes "assume I'm uninitialized; do what I need; next time activate() is called, do the cheap-noop check first." **Relevance:** the `SessionStart` hook is VS Code's `activate`. The correct shape for pos-v2 is "SessionStart does a cheap state-check; on fresh state, run first-run; on initialized state, no-op."

### Synthesis for pos-v2

- **POSIX shell for the irreducible minimum** (Homebrew pattern).
- **Cheap state check, fresh-state branch** (VS Code / pre-commit pattern).
- **Write state to a stable location; trust it on subsequent runs** (Docker pattern).
- **Clean separation between install-once and per-session-init** (pyenv pattern).

---

## 2. Recommended bootstrap shape — **Shape A (shell-first), refined**

**Ruling:** Shape A as drafted in the plan, with one refinement: a second Python helper script that runs *inside the just-created venv* to do the Python-appropriate work (per-component venvs, pip installs that benefit from structured error handling). The shell script is the irreducible-minimum wrapper that exists to create the venv; once the venv exists, Python does the rest.

### 2.1 Why A over B and C

**Shape B (Python with inline bootstrap venv)** fails on the chicken-and-egg even harder than the plan suggests. The hook currently invokes `${POS_V2_REPO}/.venv/bin/python`. That path does not exist. If first-run is a Python script, *something outside the hook* has to invoke it with system Python — which means the hook has to change to reference system Python, which means hands-off-lifecycle's hook fragment amendment is unavoidable. Shape A avoids this by keeping the hook invoking a POSIX shell script that shells out to whatever Python is right (system on first run, venv Python on subsequent runs — the shell script's job is to know which).

**Shape C (two-phase hook with state-branch)** is equivalent to shape A in effect but requires the hook to express branching. The settings.json hook-registration format does not express branching; it would require a wrapper script anyway. Shape A collapses to "the shell script is the wrapper; inside the wrapper, state-check selects one path or the other." Same outcome, less surface area, one script to maintain.

**Shape A (shell-first)** — the shell script is the hook command. It detects state, creates the venv on first run, delegates to a Python helper for structured work, writes completion markers, and on subsequent runs finds the markers and hands off to the existing `pos_session_start.py` (unchanged — which answers the chicken-and-egg: the hook's command changes, but `pos_session_start.py` itself does not need to move).

### 2.2 Refinement — two scripts, one hook command

```
.claude/settings.json    {hooks.SessionStart.command → first-run.sh}
hooks/first-run.sh       POSIX shell, ~200 lines, handles state-check + venv creation
                         + delegates to:
hooks/first-run.py       Python stdlib-only, ~300 lines, handles pip installs,
                         settings.json authorship, plist-template substitution
                         (runs *inside* the just-created venv on first run, or
                         inside the existing venv on subsequent runs)
                         Then calls into orchestrator/scripts/pos_session_start.py
                         for the routine supervisor-probe path.
```

**Crucially:** `pos_session_start.py` remains a library importable from the first-run helper *and* callable from the hook command chain. Its body does not change. This is the path that avoids amending the sealed hands-off-lifecycle hook fragment — see §8.

### 2.3 Failure-mode catalogue for shape A

| Failure | Detection | Disposition |
|---------|-----------|------------|
| No system Python ≥3.13 | `python3.13 --version` or `python3 -c 'import sys; assert sys.version_info >= (3,13)'` | Exit 0 from hook, print diagnostic to stdout (becomes additionalContext) — user sees "pos v2 first-run: Python 3.13 required — install python 3.13 (e.g. `brew install python@3.13`) and reopen this workspace." |
| `python -m venv` fails | Non-zero return from shell command | Diagnostic with the stderr captured. |
| `pip install` network failure | Non-zero return from pip | Write `~/.pos/first-run-state.yaml` with `state: partial_deps` and the remaining install list; next session resumes from the list. |
| `pip install` unresolvable dep | Non-zero return from pip, distinguishable from network by exit code + stderr pattern | Escalate — write `~/.pos/first-run-state.yaml` with `state: blocked_dep`, named dep, full stderr. Hook emits a single-line diagnostic. |
| `launchctl bootstrap` refused (plist syntax, already loaded) | Non-zero return from `launchctl` | Captured warning; services may still come up on retry; supervisor handles ongoing probing. Same path the existing `pos_session_start.py` already takes. |
| Partial completion from interrupted prior run | Markers present but not all final | Resume — §9 resume state model. |
| shell script crashes partway | Hook returns non-zero | Exit 0 with stdout diagnostic; `~/.pos/first-run-state.yaml` left in whatever state was reached; next session retries. |

---

## 3. System-Python detection + version gate

### 3.1 Target version

**Python 3.13+** per pos-v2 convention (`docs/rebuild/STATE.md` + root `README.md`). Minimum enforced: `sys.version_info >= (3, 13)`.

### 3.2 Detection order (in shell)

```
1. If $POS_V2_PYTHON is set, use it (escape hatch for CI / dev override).
2. Try python3.13 on PATH.
3. Try /opt/homebrew/bin/python3.13 (macOS Homebrew ARM default).
4. Try /usr/local/bin/python3.13 (macOS Homebrew Intel / Linux).
5. Try python3 on PATH, then verify sys.version_info >= (3,13).
6. Fail with diagnostic.
```

### 3.3 Distributions shipping 3.13 today (Q2 2026)

- **macOS:** not in system Python (still 3.9). Must install (Homebrew, python.org, pyenv).
- **Ubuntu 24.04 LTS:** ships 3.12; 3.13 via deadsnakes PPA or `python3.13` package depending on minor update.
- **Ubuntu 25.04+:** ships 3.13 as `python3`.
- **Fedora 40+:** ships 3.13.
- **Debian 13 (trixie):** ships 3.13.
- **Arch:** rolling, ships latest.

**Expected early-user fraction with 3.13 pre-installed:** ~40-60% on macOS (anyone using Homebrew and python@3.13 tap); ~30-50% on Linux (distribution-dependent). The version-gate failure message must be helpful and distribution-aware.

### 3.4 Failure-message wording (locked)

```
pos v2 first-run: Python 3.13 is required to run pos-v2. Detected: <version-or-none>.

Install Python 3.13:
  macOS (Homebrew):     brew install python@3.13
  macOS (python.org):   https://www.python.org/downloads/
  Ubuntu 24.04:         sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.13 python3.13-venv
  Ubuntu 25.04+:        sudo apt install python3.13 python3.13-venv
  Fedora 40+:           already installed; your python3 should work
  Other:                pyenv install 3.13

Reopen this workspace in Claude Code after installing. First-run will pick up.
```

Written as the hook's stdout (becomes additionalContext); hook returns exit 0 so Claude Code surfaces the text cleanly (exit 2 also shows stderr but does not block SessionStart — either works; 0 is simpler).

### 3.5 python3-venv package on Debian/Ubuntu

A quiet gotcha: `apt install python3.13` does not always bring `python3.13-venv`. The shell detection must verify `python -m venv --help` returns non-zero after Python detection and surface a separate "install python3.13-venv" diagnostic if the venv module is missing. This is a named failure mode distinct from "no Python."

---

## 4. Per-component venv discovery protocol

### 4.1 What exists today

- `.venv/` at pos-v2 root (observed in the current tree; will not exist on fresh clone).
- `memory-system/.venv/` — the memory sidecar's dedicated venv (required because Graphiti deps are heavy and segregated).
- No other per-component venvs.

### 4.2 Recommended convention — `needs_dedicated_venv` marker in a top-level inventory

Define `first-run-inventory.yaml` at the pos-v2 root. This is **new**, authored by true-first-run, not an amendment to any sealed component:

```yaml
# first-run-inventory.yaml — components the first-run setup installs.
# Ordered. Each component declares whether it wants its own venv or
# shares the root .venv/.
shared_venv:
  path: .venv
  python_version: ">=3.13"
  components:
    - orchestrator          # has requirements.txt; installable editable
    - scope-of-work
    - objective-tracker
    - primary-persona
    - safety-layer
    - reversibility-primitive
    - cost-governance
    - self-correction
    - self-upgrade
    - graceful-degradation
    - observability-aggregator
    - workspace-bootstrap
dedicated_venvs:
  - component: memory-system
    venv_path: memory-system/.venv
    python_version: ">=3.13"
    rationale: "Graphiti + Kuzu are heavy and segregated from core."
```

### 4.3 Why this shape over alternatives

- **Per-component marker file (`.needs-venv`)** — requires amending twelve component directories. Every new component silently inherits "shared venv" unless it adds a marker. Decision is distributed; the shape of the workspace is not visible in one place.
- **Convention from `pyproject.toml`** — reading each component's `pyproject.toml` to discover venv preference requires a declared field that doesn't exist today and would require amendments.
- **Top-level inventory** — one file, one place to reason about the workspace shape, no amendments to sealed components. The inventory is itself a test artifact: the first-run shell script reads it, installs in the order it specifies, and surfaces a clean error if a listed component is missing a `requirements.txt`.

### 4.4 Install strategy

For each component in `shared_venv.components`: if a `requirements.txt` exists, `pip install -r <component>/requirements.txt`. If a `pyproject.toml` exists with no `requirements.txt`, `pip install -e <component>/`. The orchestrator's `requirements.txt` notes this explicitly ("In-workspace editable installs") — the first-run helper honors that.

For `memory-system`: create `memory-system/.venv/` separately, `pip install -r memory-system/requirements.txt` into it.

### 4.5 Install order

1. Create shared `.venv/` with `python -m venv .venv` (stdlib only).
2. Install shared components into it in dependency order: scope-of-work → objective-tracker → primary-persona → orchestrator → the remaining eight. Order matters because several components declare workspace-relative deps.
3. Create `memory-system/.venv/` separately.
4. Install memory-system into its own venv.

---

## 5. Dependency-install error-handling catalogue

| Failure mode | Named code | Detection | Disposition |
|---|---|---|---|
| Network timeout during pip install | `DEP_NETWORK` | pip exit 1 + stderr contains `Could not fetch` / `Read timed out` | Write partial state; exit with diagnostic "network unavailable — next session will retry from <component>". |
| Unresolvable version constraint | `DEP_RESOLVE` | pip exit 1 + stderr contains `Cannot find a version` / `ResolutionImpossible` | Write blocked state with named package. Diagnostic "dependency <name> cannot resolve — escalating; manual intervention required." |
| Package installs but post-install script fails | `DEP_POST` | pip exit 0 but import of the package fails | Write partial state, retry on next session, escalate on second failure. |
| Disk full | `DEP_DISK` | pip exit 1 + stderr contains `No space left` | Write partial state, diagnostic "insufficient disk — free space and retry." |
| Pip itself missing | `DEP_PIP` | `ensurepip` failed during `python -m venv` creation | Diagnostic "venv created without pip — install `python3.13-venv` (Debian/Ubuntu) or reinstall Python." |
| Graphiti install fails (common — heavy deps) | `DEP_MEMORY_HEAVY` | specialisation of above for the memory-system venv | Single retry, then escalate with the full package name and pip log tail. |
| Editable install unable to resolve sibling (e.g. `pos_orchestrator` requires `scope_of_work`) | `DEP_SIBLING` | pip exit 1 + missing-module in stderr | Re-check install order; if order correct, surface as internal-inconsistency diagnostic. |

All failure modes follow the same shape: `~/.pos/first-run-state.yaml` gets `state: blocked` with the named code, the diagnostic is emitted as hook stdout, and the supervisor does not start (because services cannot). The next session-start finds the blocked state and surfaces the same diagnostic until the user intervenes — no silent retry loop.

**Retry policy:** only `DEP_NETWORK` and `DEP_POST` retry automatically (once, on the next session). All others require human intervention.

---

## 6. `.claude/settings.json` authorship strategy

### 6.1 Claude Code settings merge behaviour (fetched from docs)

- Settings files merge hierarchically. All matching hooks from all scope levels (managed policy / user / project / local / plugin) fire.
- Duplicate handlers dedupe by command string.
- `disableAllHooks` applies per-scope (managed overrides user).

**Implication:** writing `.claude/settings.json` from a hook is safe — if the user already had their own `.claude/settings.json` with their own hooks, adding ours does not overwrite theirs, as long as we merge rather than replace.

### 6.2 Authorship rule — merge, never overwrite

On first run, the shell bootstrap:

1. Reads existing `.claude/settings.json` if present (JSON-parse it).
2. Merges the pos-v2 SessionStart hook entry into `hooks.SessionStart` (append, dedupe by exact command string).
3. Merges any other pos-v2-required settings keys under separate paths (`env`, etc.) non-destructively.
4. Writes the merged result back atomically (write to `settings.json.tmp`, rename).

### 6.3 The hook entry authored

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "${POS_V2_REPO}/hands-off-lifecycle/hooks/first-run.sh",
        "async": false,
        "timeout": 120000
      }
    ]
  }
}
```

Note: **this is a DIFFERENT command from the existing sealed fragment.** The sealed fragment references `${POS_V2_REPO}/.venv/bin/python ${POS_V2_REPO}/orchestrator/scripts/pos_session_start.py`. Our new entry references the shell script. They co-exist (Claude Code fires both) — the shell script is responsible for eventually invoking the same underlying `pos_session_start.py` work so the user does not see both run or see the second one fail on a fresh clone.

See §8 for the precise resolution — this is the crux of the chicken-and-egg.

### 6.4 Timeout

120s (120000 ms) for first-run because a `pip install` of Graphiti + Kuzu can take 60-90s on a slow connection. On subsequent runs the shell script state-checks and exits in milliseconds, so the 120s timeout is cost-free. Claude Code's default hook timeout is 600000 ms (10 minutes) — we set lower explicitly because a first-run that hangs past 2 minutes likely has a real problem worth surfacing.

### 6.5 What true-first-run also writes to settings.json

Only the SessionStart hook. Other Claude Code conveniences (allowedTools, env, etc.) are workspace-policy decisions the user owns, not framework setup. First-run does not opine.

### 6.6 ${POS_V2_REPO} resolution

First-run resolves it at authorship time — writes the absolute path of the workspace root into the settings.json, not the literal `${POS_V2_REPO}` string. The settings.json ends up with the absolute path baked in. This is correct: the workspace is already cloned to a specific location; the hook needs that location; the user is not going to move the workspace.

The sealed hook fragment uses `${POS_V2_REPO}` as a templated placeholder because it is documentation showing what to merge; the actual settings.json authored on first run has the resolved path.

---

## 7. Plist-template substitution spec

### 7.1 Templates already in pos-v2

- `orchestrator/ops/launchd/com.pos.orchestrator.plist.tmpl` — uses `${LABEL}`, `${PYTHON}`, `${WORKING_DIR}`, `${STDOUT_LOG}`, `${STDERR_LOG}`, `${THROTTLE_SECS}`.
- `orchestrator/ops/systemd/pos-orchestrator.service.tmpl` — uses `${PYTHON}`, `${WORKING_DIR}`, `${THROTTLE_SECS}`.
- `memory-system/systemd/pos-v2-memory-graphiti.service.tmpl` — uses `${WORKSPACE}`.
- `memory-system/launchd/com.pos-v2.memory-graphiti.plist` — **not a `.tmpl`**; has hardcoded paths to `/Users/lukeivers/ivers-corp-pos-v2/memory-system/...`. **This is amendment territory** — see §10.

### 7.2 Template engine

Python's `string.Template.substitute()` — stdlib, already used by `orchestrator/scripts/install_launchd.py`. No Jinja2, no envsubst dependency. Substitution by variable name with `${...}` syntax.

### 7.3 Variables resolved on first run

| Variable | Source | Example |
|---|---|---|
| `LABEL` | Hardcoded per service | `com.pos.orchestrator`, `com.pos-v2.memory-graphiti` |
| `WORKSPACE` / `WORKING_DIR` | Shell `pwd` at hook invocation | `/Users/luke/pos-v2` |
| `PYTHON` | For shared venv: `{WORKSPACE}/.venv/bin/python`. For memory venv: `{WORKSPACE}/memory-system/.venv/bin/python` | — |
| `STDOUT_LOG` / `STDERR_LOG` | `~/.pos/logs/<service>.out`, `~/.pos/logs/<service>.err` (mkdir -p) | — |
| `THROTTLE_SECS` | `30` for orchestrator, `10` for memory (matches existing defaults) | — |

### 7.4 Destinations

- **macOS:** `~/Library/LaunchAgents/<LABEL>.plist` (same as `first_run_scaffold.py` already uses).
- **Linux:** `~/.config/systemd/user/<LABEL>.service` (same).

### 7.5 Conflict handling

If a plist already exists at the destination path:

1. Read it. If its `Label` matches the expected pos-v2 label AND the path it references is the current workspace — no-op, leave in place.
2. If its `Label` matches but the path is a different workspace — surface diagnostic `plist_foreign_workspace:<label>:<other-path>`. The user has a pos-v2 install at a different path; this is a halt condition because `launchctl bootstrap` will fail on duplicate labels. Human decision required.
3. If the file exists but is malformed or not a plist — back up to `<path>.pre-pos-v2` and write fresh.

### 7.6 Cleanup on re-run

First-run never "cleans up" — re-run detects completed state and no-ops. Explicit cleanup (for workspace relocation, uninstall, etc.) is out of scope for first-run. A separate `bin/pos-uninstall` is future work.

### 7.7 Service-bootstrap

After templates are written, `launchctl bootstrap gui/<uid> <plist-path>` (macOS) or `systemctl --user daemon-reload && systemctl --user start <label>` (Linux) — exactly the same commands `pos_session_start.py` already issues. First-run's bootstrap is additional only because the services did not exist before.

---

## 8. Chicken-and-egg resolution — the crux

### 8.1 Statement of the problem

The sealed hands-off-lifecycle hook fragment invokes `${POS_V2_REPO}/.venv/bin/python ${POS_V2_REPO}/orchestrator/scripts/pos_session_start.py`. On a fresh clone, `${POS_V2_REPO}/.venv/bin/python` does not exist. The hook fires with an invalid command. Claude Code treats the failure as a non-blocking error; the user sees nothing helpful; no services come up.

### 8.2 Four candidate resolutions

**Resolution A — author a second hook entry, order them so ours runs first.** The merge semantics fire *all* matching hooks; the docs are unclear on ordering within a single SessionStart event. **Eliminated:** ordering is implementation-defined; we cannot guarantee our shell script runs before the sealed fragment. If the sealed fragment runs first and fails, the user sees an error before ours runs.

**Resolution B — our shell bootstrap creates the .venv *before* the sealed fragment's command is even evaluated.** This requires the shell bootstrap to block until the venv exists, and for Claude Code to evaluate the sealed fragment's command string *after* the shell bootstrap returns. **Eliminated:** command strings in settings.json are fixed at config-load time; Claude Code is unlikely to re-resolve `${POS_V2_REPO}/.venv/bin/python` on each hook firing. The path resolves at hook-fire time via the shell, but the venv still must exist *by the time the sealed fragment's command executes*. Given we cannot guarantee our hook runs first, we cannot guarantee the venv exists when the sealed fragment fires.

**Resolution C — our first-run script creates the venv atomically AND populates `.venv/bin/python` BEFORE authoring the sealed fragment's settings.json entry.** Concrete shape: our hook authors `.claude/settings.json` on first run *including the sealed fragment's entry*, but only after the venv exists. On a truly fresh clone, `.claude/settings.json` does not exist yet; neither hook entry exists yet; only our shell script is invoked (somehow — see 8.3). Our script creates the venv, then authors settings.json with both entries. Future sessions fire both, venv exists, both succeed. **Viable, but hinges on 8.3.**

**Resolution D — amend the sealed fragment to be bootstrap-tolerant.** Change the command from `${POS_V2_REPO}/.venv/bin/python ...` to a wrapper script that falls back to a no-op when the venv does not exist. **This is the amendment case** the plan flagged.

### 8.3 The missing piece — how does our script run if `.claude/settings.json` doesn't exist yet?

On a fresh clone, there is NO `.claude/settings.json`. The sealed hook fragment is **documentation** at `hands-off-lifecycle/hooks/settings.json.fragment` — a blob the user or a setup process merges into their real settings.json. Until merged, **neither hook fires**.

This is the critical insight: **on a fresh clone, the sealed fragment's command string never runs, because the fragment is not yet installed.** The user opens Claude Code in the workspace, no SessionStart hook fires at all, and nothing happens. This is a worse failure mode than the one the plan described, but it admits a cleaner fix.

### 8.4 Recommended resolution — **Resolution C, repackaged as "true-first-run authors settings.json from scratch"**

Since no settings.json exists on fresh clone, no hook fires. Which means the user cannot auto-install either hook. Which means **something must fire on fresh clone when settings.json is absent.**

Claude Code's behavior in this case: no SessionStart hook → nothing happens, session starts normally. The user gets a functional Claude Code session with no pos-v2 integration.

**The way out:** pos-v2 ships `.claude/settings.json` **in the repository**, authored at commit time, containing only the first-run shell-script hook entry:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "${POS_V2_REPO}/hands-off-lifecycle/hooks/first-run.sh",
        "async": false,
        "timeout": 120000
      }
    ]
  }
}
```

Wait — `${POS_V2_REPO}` is not a standard environment variable. Claude Code does not do automatic repo-root substitution in hook commands. Check the docs.

**Re-checking the docs:** The Claude Code hooks docs show hook commands as literal shell commands. Environment variable expansion happens via the shell at execution time. `${POS_V2_REPO}` works only if it is set. Claude Code provides `$CLAUDE_PROJECT_DIR` as the workspace root (standard Claude Code env var).

**Revised hook command:**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/hands-off-lifecycle/hooks/first-run.sh",
        "async": false,
        "timeout": 120000
      }
    ]
  }
}
```

This is portable, resolves per-user at execution time, requires no first-run step to author the path, and works on a truly fresh clone. (Note: the exact env var name should be verified at build time — the docs excerpt returned by WebFetch did not explicitly name `$CLAUDE_PROJECT_DIR`; a live prototype test is required. If Claude Code exports a different var or none, the shell script can resolve its own directory via `$(dirname "$(readlink -f "$0")")/..` — the script's own location determines the repo root.)

### 8.5 Consequence for the sealed hands-off-lifecycle fragment

The sealed fragment (`hands-off-lifecycle/hooks/settings.json.fragment`) is **documentation** — a snippet a hypothetical setup script was supposed to merge into settings.json. The sealed component's source of truth is that fragment file. True-first-run does NOT modify the fragment file and does NOT merge it into settings.json.

**Instead,** true-first-run ships a different settings.json entry (the shell-script entry), and the shell script itself eventually calls `pos_session_start.py` with the correct venv-resolved Python — folding the sealed fragment's *intent* into the shell-script's execution path.

**No amendment to hands-off-lifecycle is strictly required for the hook to work correctly.** But the `settings.json.fragment` file becomes stale documentation — it describes a path (user-merges-this-blob-into-settings.json) that true-first-run obsoletes. That is a documentation amendment, not a behavior amendment, and is surfaced in §10 as a fifth-amendment candidate on the documentation surface only.

### 8.6 Summary ruling on the crux

- **Behavior-level amendment to hands-off-lifecycle's hook fragment: NOT REQUIRED.** The sealed fragment's command path is preserved by having the shell script invoke `pos_session_start.py` with the venv's Python once the venv exists. The fragment's *intent* is honored through a different mechanism.
- **Documentation-level amendment to hands-off-lifecycle's README: RECOMMENDED.** The README currently says "See `hooks/settings.json.fragment` for the exact hook stanza to merge into a workspace's `.claude/settings.json`." Once true-first-run is live, no user merges this blob — true-first-run ships the settings.json directly. The README should be updated to note that the fragment is reference-only for the ongoing-operation path; first-run handles installation. This is the low-stakes amendment case.
- **New file: `.claude/settings.json` committed to the pos-v2 repo.** This is new content, not a sealed-component amendment.

---

## 9. Idempotent re-run state model

### 9.1 State markers

Single source of truth: `~/.pos/first-run-state.yaml`. Schema:

```yaml
# ~/.pos/first-run-state.yaml — first-run progress and outcome.
# Authored by hands-off-lifecycle/hooks/first-run.sh + first-run.py.
schema_version: 1
workspace_path: /Users/luke/pos-v2
started_at: 2026-04-22T14:00:00Z
completed_at: 2026-04-22T14:02:15Z      # null if incomplete
python_version: "3.13.2"
python_path: /opt/homebrew/bin/python3.13
shared_venv: .venv
memory_venv: memory-system/.venv
state: complete                          # pending | partial | complete | blocked
phases:
  system_python_check: complete
  shared_venv_create: complete
  shared_deps_install: complete
  memory_venv_create: complete
  memory_deps_install: complete
  plist_substitution: complete
  service_bootstrap: complete
  settings_json_author: complete
blocker: null                            # populated on blocked state
  # code: DEP_RESOLVE
  # package: graphiti-core==0.28.2
  # stderr_tail: "..."
```

### 9.2 Resume-or-restart decision tree

On each hook fire, the shell bootstrap reads `~/.pos/first-run-state.yaml`:

1. **File missing** → treat as fresh. Run all phases.
2. **File present, `state: complete`, `workspace_path` matches** → no-op. Exit 0, silent (no stdout). The sealed fragment's supervisor-probe equivalent (`pos_session_start.py`) still runs as part of the shell script's ongoing path.
3. **File present, `state: complete`, `workspace_path` differs** → the user has a completed first-run from a different workspace, but we are running in a new workspace. Treat as fresh for THIS workspace; but the plists already installed will conflict. Surface diagnostic `first_run_workspace_moved:<old>:<new>`; do not auto-relocate. Human decision.
4. **File present, `state: partial`** → resume from first non-complete phase. Log each resumed phase to stdout.
5. **File present, `state: blocked`** → surface the stored blocker diagnostic verbatim. Do not retry automatically (except for `DEP_NETWORK` per §5). If `DEP_NETWORK` or `DEP_POST`: clear blocker, retry the blocked phase.

### 9.3 Partial-completion handling

Each phase writes its own "complete" marker before moving to the next. Phase ordering is total. An interrupted run (SIGKILL, session crash, power loss) leaves some phases complete, one `pending`, remainder untouched. Resume picks up from the first non-complete phase. Phases are designed to be individually idempotent — `python -m venv .venv` is a no-op if `.venv` is already present; `pip install -r requirements.txt` with a partial install leaves requirements-satisfied state and finishes on retry.

### 9.4 Confirmation sentence (first successful completion only)

Exactly the sentence already defined in `first_run_scaffold.py` for YAML scaffolding, extended to include venv + dep state. Locked wording:

```
pos v2 first-run complete: Python 3.13 environment, twelve components installed, memory sidecar and orchestrator launched, ~/.pos/ scaffolded. Edit ~/.pos/*.yaml to adjust any default. Proceeding.
```

Emitted exactly once — at the transition from `partial` to `complete`. Subsequent sessions: silent (or supervisor's "pos v2 ready" from the existing path).

### 9.5 Session-start flow on subsequent sessions

1. Shell bootstrap reads state → `state: complete`, silent.
2. Shell bootstrap invokes `<venv>/bin/python <workspace>/orchestrator/scripts/pos_session_start.py`.
3. `pos_session_start.py` does its existing probe → emits "pos v2 ready" or the partial-services diagnostic.

This preserves the sealed `pos_session_start.py` behavior exactly; its invocation path now comes through the shell script on every session, first or not.

---

## 10. Sealed-component amendment inventory

The crux resolution in §8 avoids a behavior-level amendment to hands-off-lifecycle. The research identifies **two documentation-level and one hardcoded-file concerns** that may qualify as amendments. Each is surfaced here for owner ruling.

### 10.1 hands-off-lifecycle README — documentation amendment (RECOMMENDED)

**Surface:** `hands-off-lifecycle/README.md`, specifically the "SessionStart hook (Claude Code v2.1.87+)" section.
**Change:** Update wording to clarify that the `settings.json.fragment` is *reference documentation*, not the mechanism users invoke. Add one paragraph: "In practice, the `.claude/settings.json` committed to pos-v2 points at `hooks/first-run.sh`, which creates the venv on first run and then invokes `orchestrator/scripts/pos_session_start.py` — the same script the fragment references — on every subsequent run. The fragment above describes what that eventual invocation looks like, not the commit-time settings.json content."
**Rationale:** prevent user confusion when reading `hands-off-lifecycle/README.md` alongside the shipped `.claude/settings.json`. Low-risk: does not change behavior, does not change error codes, does not change tests.

### 10.2 hands-off-lifecycle hook fragment — status clarification (RECOMMENDED)

**Surface:** `hands-off-lifecycle/hooks/settings.json.fragment`, the `_comment` field.
**Change:** Add a note: "On a pos-v2 repo using true-first-run, this fragment's hook is invoked transitively via `hands-off-lifecycle/hooks/first-run.sh` — it is not merged verbatim into the user's settings.json."
**Rationale:** makes the file self-describing so a future reader understands its role. No code change.

### 10.3 memory-system launchd plist — hardcoded path (NOT AN AMENDMENT; NEW WRITE)

**Surface:** `memory-system/launchd/com.pos-v2.memory-graphiti.plist`.
**Observation:** This file has hardcoded `/Users/lukeivers/ivers-corp-pos-v2/memory-system/...` paths — it is **not** a `.tmpl`. On a fresh clone at a different path, the file is not usable as-is.
**Disposition:** True-first-run does **not** edit this file. Instead, true-first-run uses the already-authored in-process plist template inside `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` (lines 353-397) which substitutes `{workspace}` at scaffold time. First-run writes the substituted plist directly to `~/Library/LaunchAgents/`. The hardcoded file in `memory-system/launchd/` is stale development-time content that is already effectively obsoleted by Amendment 4 — it can stay in place as reference; it is not used. **This is not an amendment.** However, a case could be made for converting it to `.tmpl` for consistency — that would be a memory-system documentation amendment. **Recommend: leave as-is**; document in memory-system's README that the authoritative plist generator is first-run (via Amendment 4's templates).

### 10.4 workspace-bootstrap first_run_scaffold.py — scope extension (MAYBE AN AMENDMENT)

**Surface:** `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`.
**Observation:** Amendment 4 already writes YAML defaults, plists, and bootstraps services. It does not create venvs, install deps, or author `.claude/settings.json`. True-first-run adds those three capabilities.
**Disposition options:**
- **Option A:** true-first-run's shell + python helper calls `run_first_run_scaffold()` (Amendment 4's entry point) as one of its phases, then does the venv + dep + settings.json work itself. No amendment required — Amendment 4's API is used as a library. This is cleanest.
- **Option B:** extend `first_run_scaffold.py` to also handle venv + deps + settings.json. This is an amendment to the sealed component.
**Recommendation:** Option A. No amendment. true-first-run's Python helper imports `first_run_scaffold.run_first_run_scaffold` and invokes it between the venv-creation phase and the service-bootstrap phase. This respects the seal and keeps the scope boundaries clean.

### 10.5 Summary — is a fifth amendment required?

**Strict behavior-level amendment count: ZERO.** True-first-run can ship without amending sealed-component behavior.

**Documentation-level amendments: TWO RECOMMENDED** (10.1, 10.2) — low-risk clarifications to hands-off-lifecycle's README and hook-fragment comment that improve system legibility. These are comment-level edits.

**The plan's hypothesis was that the hook fragment's command string would need to change.** The research disconfirms this: the fragment's command string does not change; the fragment itself becomes non-authoritative on a workspace with true-first-run, because `.claude/settings.json` ships already-authored and never has the fragment merged into it.

**If the owner rules that documentation edits to sealed components count as amendments, 10.1 and 10.2 are the amendments and the count is two.** If documentation edits do not count, the count is zero. Eve's read: documentation clarifications that do not change any test, error code, or hook behavior are *not* amendments in the sealed-component sense — the seal protects behavior, not prose. But this is a ruling the owner owns.

---

## 11. Complexity estimate — AI-time calibrated

### 11.1 Scope in scripts

- **`hands-off-lifecycle/hooks/first-run.sh`** — POSIX shell, ~200 lines. Python detection, venv creation, state-file read/write, delegation to first-run.py.
- **`hands-off-lifecycle/hooks/first-run.py`** — Python stdlib only, ~300 lines. Pip invocations with error handling, settings.json authorship (with merge), plist template resolution + write, service bootstrap delegation.
- **`first-run-inventory.yaml`** — ~40 lines of declarative component list.
- **`.claude/settings.json`** — ~15 lines, committed to repo.
- **Tests** — `hands-off-lifecycle/tests/test_first_run.py` + shell script tests. ~15-20 test cases mapped to the ODD criteria this component introduces.
- **README/docs updates** — per §10.1 and §10.2.

### 11.2 AI-time anchors per rule 15 (task-orchestration.md)

Per calibration anchors:
- Multi-file change (3-10 files): 3-10 min.
- New module with tests: 10-20 min.
- Complex cross-cutting feature: 20-45 min.

This component touches 5-7 new files and 2 docs, runs ~15-20 tests, has one cross-cutting concern (settings.json merge) that requires prototyping against live Claude Code. In AI-time: **45-90 minutes wall-clock**. Red line at 120 minutes.

### 11.3 Calendar-minute reality check

The plan anchored to "hands-off-lifecycle's build (170-220 min wall-clock) given scope breadth." That was four sealed-component amendments + a new component. True-first-run is one new component plus zero or two documentation edits. Scope is smaller by roughly a factor of two. Mapping:

- Shell script + Python helper: 25-40 min (primary work).
- Tests: 15-25 min (many small deterministic cases; file + state fixture patterns already established in workspace-bootstrap tests).
- Documentation updates: 5-10 min.
- settings.json prototyping (the one genuine unknown — §12): 10-20 min.

**Honest band: 60-95 minutes wall-clock; red line at 120.** Shorter than hands-off-lifecycle because the foundation (Amendment 4) is already there.

---

## 12. Prototyping priorities — what only a live test can answer

Five items require real Claude Code interaction, not just code reading.

### 12.1 `$CLAUDE_PROJECT_DIR` — does it exist? what's the exact name?

The hooks documentation excerpt did not explicitly enumerate Claude Code env vars available in hook commands. A live test: author a minimal `.claude/settings.json` with a hook that `echo`s `$CLAUDE_PROJECT_DIR`, open a session, read the hook output. If the var does not exist, fall back to `$(dirname "$(readlink -f "$0")")/..` inside the shell script.

### 12.2 SessionStart hook firing on a workspace with NO `.claude/settings.json`

Confirm Claude Code behavior: does it auto-create `.claude/settings.json` on first session? Does it complain? Silently do nothing? This determines whether shipping `.claude/settings.json` in the repo is the right shape, or if we need a different entry point.

### 12.3 Hook stdout visibility on SessionStart

The docs say SessionStart stdout is added as context. A live test: emit stdout from the shell script and verify it appears as context in the session. If it does, the confirmation sentence + blocked-state diagnostics surface naturally.

### 12.4 `pip install` with Graphiti in a fresh venv — actual wall-clock time

The 120s timeout assumes a warm pip cache. Cold cache on a slow connection can push past that. Prototype: create a fresh venv, `pip install -r memory-system/requirements.txt`, time it. If it exceeds 120s regularly, bump the timeout and document. (Do not bump to `600000` — a hung pip install deserves a diagnostic, not a ten-minute hang.)

### 12.5 launchctl bootstrap failure modes

When `launchctl bootstrap` fails (e.g., plist already loaded under a different label, syntax error, system denial), what does it return? The error-handling catalogue in §5 assumes distinguishable failure modes. A live test: intentionally-broken plist, measure return code + stderr. Use results to calibrate the `plist_foreign_workspace:` diagnostic wording.

### 12.6 What the prototype produces

- A working `.claude/settings.json` shape (portable env-var resolution).
- Calibrated timeouts.
- Confirmed failure-mode fingerprints for error-handling catalogue.

The prototype is half a session's work; it happens between G2 approval and G3 proposal — it is input to G3, not part of the build.

---

## Appendix A — Open questions requiring owner ruling at G2

1. **Documentation-level amendments to hands-off-lifecycle (10.1, 10.2) — count as amendments or not?** Research recommends NOT counted; ruling requested.
2. **Confirmation-sentence wording (§9.4).** Currently drafted as an extension of the existing scaffold sentence. Owner may prefer different wording.
3. **120s hook timeout on first-run (§6.4).** Research recommends; prototype may adjust.
4. **Inventory YAML location — pos-v2 root (`first-run-inventory.yaml`) vs `hands-off-lifecycle/first-run-inventory.yaml`.** Recommendation: inside `hands-off-lifecycle/` because it is first-run's data, not generally-consumed workspace config. Owner ruling requested.
5. **`.claude/settings.json` committed to repo — user-overrides behavior.** If a user edits their workspace's settings.json and adds their own hooks, do we try to protect their edits on future first-run re-authorship? Recommendation: first-run only writes on truly-fresh state; subsequent runs trust the settings.json it authored and do not re-merge. User edits are preserved.
6. **Post-success behavior on third-and-later sessions — silent or "pos v2 ready"?** Research recommends: silent for the first-run script's own output, let `pos_session_start.py` emit "pos v2 ready" as it does today. Owner may prefer the first-run script also emits.
7. **Uninstall path — in scope for this component or future `bin/pos-uninstall`?** Recommendation: future work.

---

## Appendix B — Test matrix (to be refined at G3)

| Criterion | Test |
|---|---|
| T1 | Fresh-clone simulation: empty `~/.pos/`, no `.venv/`s; shell bootstrap completes; state `complete`. |
| T2 | Python missing: `POS_V2_PYTHON=/nonexistent` → diagnostic stdout, exit 0. |
| T3 | Python version too low: mock 3.11 → diagnostic stdout with distribution-specific install commands. |
| T4 | Resume from partial: state `partial`, `shared_deps_install: pending` → only re-runs that phase and beyond. |
| T5 | Resume from blocked: state `blocked`, `DEP_RESOLVE` → emits stored diagnostic, does not retry. |
| T6 | Idempotent re-run: state `complete` → shell bootstrap exits < 50ms, no side effects. |
| T7 | settings.json merge: existing settings.json with user's own hook → user's hook preserved, pos-v2 hook added. |
| T8 | Plist conflict: existing foreign-workspace plist → `plist_foreign_workspace:` diagnostic, no overwrite. |
| T9 | Network failure simulation during pip: state `partial`, `DEP_NETWORK` → next run retries. |
| T10 | Unresolvable dep: state `blocked`, `DEP_RESOLVE` → stored blocker persists; no auto-retry. |
| T11 | Confirmation-sentence emission: only on first successful transition to `complete`. |
| T12 | Memory-system venv created separately from shared. |
| T13 | Shared-venv dependency order: scope-of-work installed before orchestrator. |
| T14 | Platform unsupported (Windows) → platform-unsupported diagnostic. |
| T15 | `$CLAUDE_PROJECT_DIR` resolution (prototype-confirmed behavior). |
| T16 | Subsequent-session silence: complete state → no stdout from first-run.sh. |
| T17 | Invocation of `pos_session_start.py` with correct venv Python path. |
| T18 | python3.13-venv missing (Debian/Ubuntu) → distinct diagnostic from "no Python." |

---

## Appendix C — What this component does NOT do

Explicit out-of-scope per plan §3.2 plus research-surfaced items:

- Installing Python 3.13 itself.
- Installing `git`, `claude` CLI, Homebrew.
- Writing user personas, user memory, user workspace-specific config.
- Ongoing supervisor health work (that's hands-off-lifecycle's supervisor).
- Amending `pos_session_start.py`'s probe/bootstrap logic.
- Windows support.
- An uninstall path (future work).
- Editing `memory-system/launchd/com.pos-v2.memory-graphiti.plist` — the authoritative plist generator is Amendment 4 already.

---

## End of research document

Ready for owner G2 review.
