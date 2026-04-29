# loam-mode

Sub-plan F (two-modes-and-multi-workspace programme) data layer:
declares + audits the dev-mode auto-load partition.

The partition lives at `docs/rebuild/dev-mode-manifest.yaml` (workspace-
relative). `loam-mode` parses it, exposes a `select_corpus(mode)`
selector for sub-plan B's mechanism to consume, and ships a
`loam-mode audit` CLI that walks the workspace tree and reports
orphans / overlaps / cross-mode references.

## Install

```
pip install -e tools/loam-mode/
```

(Mirrors `tools/loam/`'s install convention.)

## CLI

```
loam-mode audit [--workspace <path>] [--manifest <path>]
```

- Exits 0 when the partition is consistent (no orphans, no overlap,
  no cross-mode markdown references in always-loaded artefacts).
- Exits non-zero with a structured diagnostic naming each violation
  otherwise.

## Programmatic surface

```python
from pathlib import Path
from loam_mode.manifest import load_manifest
from loam_mode.selector import select_corpus

m = load_manifest(Path("docs/rebuild/dev-mode-manifest.yaml"),
                  workspace_root=Path("."))
paths = select_corpus(m, workspace_root=Path("."), mode="user")
# paths is a sorted list[str] of workspace-relative paths to auto-load.
```

## Acceptance-criteria coverage

- AC.F1 — disjoint check (`tests/test_partition_manifest.py`).
- AC.F2 — selector returns mode-correct paths
  (`tests/test_selector_partition.py`).
- AC.F3 — markdown references in always-loaded artefacts do not
  resolve to dev-only paths
  (`tests/test_partition_references.py`).
- AC.F4 — glob+exclude shape (`tests/test_partition_manifest.py`).
- AC.F5 — audit catches orphans (`tests/test_partition_audit.py`).
- AC.F.S — F's amendment touches no sealed-component path
  (`tests/test_F_S_seal_diff.py`).

## Method-level choices

- Glob library: stdlib `fnmatch` + a tiny `**` recursive walker built
  on `os.walk`. No external `pathspec`/`globre`/`wcmatch` dependency.
- Manifest model: small dataclasses; YAML parses to plain dicts/lists
  via `PyYAML`.
- Audit walks `roots`, applies `audit_excludes`, then classifies each
  surviving path against `always_loaded` / `dev_only`. Orphans / overlap
  emit non-zero exit.
- Reference scanner regex matches backtick-wrapped `*.md`/`*.yaml`/
  paths and Markdown link targets; URL-shaped targets (with scheme)
  are skipped.
