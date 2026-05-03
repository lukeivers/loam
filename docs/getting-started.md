# Getting started with loam

This page walks you from `git clone` to your first useful primary-
persona session inside a Claude Code workspace. If you have not read
[`positioning.md`](positioning.md) yet, skim it first to know whether
loam is a fit; come back here when you decide to try it.

**Audience.** This guide assumes you use [Claude
Code](https://docs.claude.com/en/docs/claude-code/) — Anthropic's
CLI for Claude. loam composes against Claude Code's native primitives
(hooks, MCP, skills, plugins, settings hierarchy); a generic
Claude.app or API-only path is not the supported v0.1.0 surface.

---

## Prerequisites

Before you start, confirm:

1. **Claude Code installed and authenticated.** Run `claude --help`
   in a terminal; if you see usage output, you are good. If not,
   follow the [Claude Code install
   guide](https://docs.claude.com/en/docs/claude-code/setup) first.
2. **Operating system.** macOS 13+ or a recent Linux distribution.
   Windows is not supported in v0.1.0 (the launchd-shaped supervisor
   surface assumes a Unix-like host).
3. **Python 3.11 or newer.** loam's runtime components are Python
   packages. Check with `python3 --version`. Use whatever Python
   manager you prefer (system Python, `uv`, `pyenv`, Homebrew); loam
   does not pin one.
4. **Git.** A reasonably recent `git` (2.30+ is fine).
5. **Roughly 500 MB of disk** for the loam framework and the per-host
   config it scaffolds at `~/.loam/`.

You do **not** need: a cloud account, an API key beyond what Claude
Code already manages, a database server, or admin/root privileges
(loam runs entirely in your user account).

---

## Five-step bootstrap

The whole walkthrough is five shell commands. Run them in order.

### 1. Clone loam

`git clone` (no second argument) creates a `loam/` directory in
your current working directory and populates it with the loam
component tree. Pick a parent directory that fits your existing
setup — `~/work`, `~`, whatever — and clone there.

```bash
git clone https://github.com/lukeivers/loam
cd loam
```

You should see the cloned `loam/` directory populated with the loam
component tree (`framework/primary-persona/`, `framework/safety-layer/`,
and so on); `cd loam` puts you at the framework root for the next
step. Your eventual workspace lives elsewhere (step 3 creates it at a
path you choose); the cloned `loam/` is the canonical-source
framework that `loam init` clones from.

### 2. Install loam

The loam CLI plus every framework component installs from the
cloned tree via `install-from-source.txt` at the repo root. The file
lists each component in topological order so pip can walk it in one
pass. Strongly recommended: install into a fresh Python 3.13 venv
to keep loam isolated from system Python.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r install-from-source.txt
```

This installs the `loam` binary plus every component package into
the active venv. If `loam` is not on your PATH after the install,
the venv is not active — `source .venv/bin/activate` again, or
invoke `.venv/bin/loam` directly.

For the prose guide, troubleshooting, and per-component fallback
order, see [`install-from-source.md`](install-from-source.md).

### 3. Bootstrap a fresh workspace

The `loam init` verb scaffolds the per-host config under `~/.loam/`,
clones the framework into the new workspace's `framework/`, scaffolds
the workspace state, and writes the workspace-level Claude Code
settings the harness needs. Pass an out-of-tree path for the new
workspace; `--from` defaults to the current working directory (the
cloned `loam/` tree) when omitted, so no second flag is needed.

```bash
loam init ~/loam-workspace
```

Expect the first run to take 1–3 minutes — installing component
packages and warming the memory primitive accounts for most of it.
Subsequent `loam init` calls reuse the per-host state and finish in
seconds.

### 4. Open Claude Code in the workspace

```bash
cd ~/loam-workspace
claude
```

Claude Code launches; loam's SessionStart hook fires; the primary
persona greets you with a short status snapshot — what is in memory,
whether any background work has finished, whether there is anything
waiting for you to rule on. You did not have to ask for any of that;
the harness surfaced it because that is what the persona does.

### 5. Try a first turn

You are now in a normal Claude Code session, but with the primary-
persona contract on top of the raw Claude turn loop. Try something
that exercises the harness:

```
Remember that the project I'm trying out today is called loam-demo
and the goal is to evaluate whether loam fits my workflow.
```

The persona stores that across sessions. Next time you run `claude`
in the same workspace, the persona's greeting will reflect the
context. If you ask it later "what was I working on?" — it can
answer.

---

## What just happened

Five shell commands; no config to edit; no API key to paste; no
database to provision. You did not learn any loam-internal
vocabulary. The primary persona is the surface; the underlying
toolkit (memory, safety gates, cost governance, observability,
background work) is composed against Claude Code's native primitives
where possible and shipped as loam-specific components otherwise.

The harness is now what you talk to whenever you `claude` in this
workspace. You can:

- ask for work to be done in the background (`go research X for
  the next hour and report back`),
- schedule recurring work (`every Monday morning, look at my open
  issues and surface anything stale`),
- ask the persona to explain itself or its components (`what is the
  reversibility primitive? when does it fire?`),
- run the persona against arbitrary natural-language intent and
  let it pick the execution path (this is the primary value
  proposition).

You can keep using Claude Code exactly as you would without loam;
the harness adds capability without removing any.

---

## Where to go next

- [`positioning.md`](positioning.md) — the longer "why loam, why
  now" essay.
- [`architecture.md`](architecture.md) — how the components compose,
  what hooks loam owns, what the primary persona dispatches.
- [`components/`](components/) — one short reference page per
  component you might want to inspect or extend.
- [`design/odd.md`](design/odd.md) — the methodology loam is built
  with and that the Dev/SDLC plugin defaults new projects to.
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — workflow + acceptance
  criterion conventions if you want to send a patch.

---

## Common first-run problems

**`loam: command not found` after `pip install -r install-from-source.txt`.**
Your venv is not active — run `source .venv/bin/activate`, or
invoke `.venv/bin/loam` directly.

**`claude` does not see the SessionStart hook.** Check that
`.claude/settings.json` exists at the workspace root after `loam
init`. If not, re-run `loam init ~/loam-workspace`; the
workspace-bootstrap component writes it idempotently.

**Memory primitive errors on first session.** The file-based memory
substrate writes under `framework/primary-persona/`'s data area;
confirm the directory is writable. If you cloned into a path that
needs root, move the workspace and start over.

**Anything else.** [`SECURITY.md`](../SECURITY.md) covers reporting
real vulnerabilities; for non-security issues, open a GitHub issue
on `lukeivers/loam` with a copy of the failing command and its
output. Bus factor is honestly one — see
[`positioning.md`](positioning.md) for context.
