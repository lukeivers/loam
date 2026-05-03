# Install from source — loam v0.1.0

This guide covers installing loam from a fresh clone of the source
repository. It is the **v0.1.0 install path** — for v0.2 onward, the
loam component family will publish to PyPI and the canonical install
becomes a single `pip install loam-cli loam-init loam-workspace-bootstrap loam-plugin-dev-sdlc`
without needing this requirements file.

The README's `loam init` flow is the **headline path** — the install
described here is the precondition. Once installed, follow the README's
quickstart to scaffold a workspace and open Claude Code.

---

## Prereqs

- **Python 3.13.** Required by every loam component
  (`requires-python = ">=3.13"` in each pyproject). If you have a
  different Python on PATH, use a Python 3.13 venv explicitly (below).
- **A fresh virtualenv.** Strongly recommended to keep loam's
  components isolated from your system Python.
- **pip 23 or newer.** Editable installs (`pip install -e .`) and
  in-flight resolution from a requirements file rely on pip's modern
  resolver. Most current Python distributions ship a recent pip.

---

## The one-command path

From a fresh clone of this repository:

```bash
# 1. Create + activate a Python 3.13 venv.
python3.13 -m venv .venv
source .venv/bin/activate

# 2. Upgrade pip inside the venv (recommended).
pip install --upgrade pip

# 3. Install every loam component in one walk.
pip install -r install-from-source.txt
```

The `install-from-source.txt` file at the repository root carries
ordered `-e ./<path>` lines covering every component a stranger
needs to install for fresh-clone v0.1.0 to work end-to-end.
Pip walks the file in declaration order; each editable install
registers the package's name (`loam-orchestrator`,
`loam-workspace-bootstrap`, etc.) so later components' bare-name
inter-component deps hit the just-installed wheels rather than
attempting a PyPI lookup.

After the install completes, the `loam` console-script is on your
PATH (assuming the venv is active). Continue with the README:

```bash
loam init ~/loam-workspace
```

---

## Per-component fallback (manual install order)

If the one-command path fails — or if you want to install only a
subset of components — here is the same topological order broken out
into discrete `pip install -e <path>` invocations. The order matters:
each component's bare-name inter-component deps are satisfied by the
earlier installs.

```bash
# Tier A — leaf components (no inter-component deps).
pip install -e ./framework/scope-of-work
pip install -e ./framework/objective-tracker
pip install -e ./framework/observability-aggregator
pip install -e ./framework/safety-layer
pip install -e ./framework/self-upgrade
pip install -e ./framework/workspace-sync

# Tier B — depends only on Tier A.
pip install -e ./framework/primary-persona

# Tier C — depends on Tier A + Tier B.
pip install -e ./framework/orchestrator
pip install -e ./framework/telegram-interface

# Tier D — depends on Tier A through Tier C.
pip install -e ./framework/reversibility-primitive
pip install -e ./framework/dormancy

# Tier E — depends on Tier A through Tier D.
pip install -e ./framework/cost-governance

# Tier F — depends on Tier A through Tier E.
pip install -e ./framework/self-correction

# Tier G — composer.
pip install -e ./framework/workspace-bootstrap

# Tier H — user-facing CLI binary (no inter-component deps).
pip install -e ./framework/tools/loam

# Tier I — `loam init` subcommand (depends on workspace-bootstrap).
pip install -e ./framework/loam-init

# Tier J — Dev/SDLC plugin (depends on Tier A leaves + Tier G composer).
pip install -e ./plugins/dev-sdlc
```

---

## Troubleshooting

### `Could not find a version that satisfies the requirement loam-<X>`

The most common cause is **install order**. If you ran a single
`pip install -e ./framework/workspace-bootstrap` from a fresh venv
without first installing the components workspace-bootstrap depends
on, pip looks for `loam-orchestrator` (and the others) on PyPI — and
they are not published in v0.1.0.

**Fix:** use either the one-command path
(`pip install -r install-from-source.txt`) or the per-component
fallback above. The order matters.

### `loam: command not found` after install

The `loam` console-script is created during the `loam-cli`
editable install. Two common causes:

1. **The venv is not active.** `source .venv/bin/activate` (or invoke
   `.venv/bin/loam` directly).
2. **Tier H was skipped.** If you ran a partial subset of the
   per-component fallback and skipped `framework/tools/loam`, the
   `loam` script does not exist. Run
   `pip install -e ./framework/tools/loam` to add it.

### `error: subprocess-exited-with-error` during build

Each component declares `requires-python = ">=3.13"`. Verify your
venv's Python:

```bash
.venv/bin/python --version
```

If it reports `Python 3.13.x`, the build environment is correct. If
it reports a lower version, recreate the venv with `python3.13 -m venv .venv`
explicitly.

### Why is bare-name dep resolution v0.1.0-only?

In v0.1.0, the loam component family is published source-only via
this repository. The bare-name PyPI references in each component's
`pyproject.toml` (e.g. `loam-orchestrator` in workspace-bootstrap's
`dependencies`) describe the eventual PyPI identifiers; they resolve
in v0.1.0 only because pip's `-r requirements.txt` walk installs the
in-flight wheels before subsequent dependent components reach for them.

In v0.2 the components publish to PyPI and the bare-name references
become true PyPI lookups. At that point this requirements file is
optional and the canonical install becomes:

```bash
pip install loam-cli loam-init loam-workspace-bootstrap loam-plugin-dev-sdlc
```

---

## Reference

- Headline install path (post-install): see [README.md](../README.md) §
  Quickstart and the `loam init` flow.
- Component-by-component reference docs: see
  [docs/components/](components/).
- Dev/SDLC plugin user-facing reference: see
  [docs/plugins/dev-sdlc.md](plugins/dev-sdlc.md).
- Architecture map (composition + extension protocol): see
  [docs/architecture.md](architecture.md).
