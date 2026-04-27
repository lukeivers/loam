"""Partition manifest loader + entry expansion.

The manifest YAML at ``docs/rebuild/dev-mode-manifest.yaml`` declares
two disjoint sets (``always_loaded`` and ``dev_only``) plus the
audit roots and exclusion patterns. This module loads the YAML,
validates the structural shape, expands glob+exclude entries against
the workspace tree, and exposes a small dataclass surface.

Entry shape (per AC.F4):

  - ``{path: <workspace-relative path>}`` — single concrete path.
    Tested for existence at expansion time (an entry pointing at a
    missing path is allowed; expansion returns an empty match-set
    and the audit reports that as an orphan-class diagnostic only
    if the path collides with an actual file later — i.e. the
    declaration is forward-looking).
  - ``{glob: <pattern>, exclude: [<patterns>]}`` — recursive glob
    when the pattern contains ``**``, plain ``fnmatch`` otherwise.
    ``exclude`` (optional) is a list of subtractive patterns.

Manifest fields:

  - ``roots`` — list of top-level paths the audit walks.
  - ``audit_excludes`` — list of patterns excluded from the walk.
  - ``always_loaded`` — list of entries.
  - ``dev_only`` — list of entries.

Per AC.F1, the path-resolved match-sets of ``always_loaded`` and
``dev_only`` must be disjoint. The expansion functions here surface
the resolved sets; the disjoint check itself runs in
``loam_mode.audit``.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml


@dataclass(frozen=True)
class ManifestEntry:
    """A single ``always_loaded`` or ``dev_only`` entry.

    Exactly one of ``path`` or ``glob`` is set. ``exclude`` is empty
    unless ``glob`` is set and the YAML provided exclusions.
    """

    path: str | None = None
    glob: str | None = None
    exclude: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (self.path is None) == (self.glob is None):
            raise ValueError(
                "ManifestEntry must set exactly one of path / glob"
            )
        if self.path is not None and self.exclude:
            raise ValueError(
                "ManifestEntry: exclude is only valid with glob"
            )


@dataclass(frozen=True)
class Manifest:
    """Parsed dev-mode partition manifest."""

    roots: tuple[str, ...]
    audit_excludes: tuple[str, ...]
    always_loaded: tuple[ManifestEntry, ...]
    dev_only: tuple[ManifestEntry, ...]


def _coerce_entry(raw: object, where: str) -> ManifestEntry:
    if not isinstance(raw, dict):
        raise ValueError(
            f"{where}: entry must be a mapping; got {type(raw).__name__}"
        )
    if "path" in raw and "glob" in raw:
        raise ValueError(
            f"{where}: entry sets both path and glob; pick one"
        )
    if "path" in raw:
        path = raw["path"]
        if not isinstance(path, str) or not path:
            raise ValueError(f"{where}: path must be a non-empty string")
        return ManifestEntry(path=path)
    if "glob" in raw:
        glob = raw["glob"]
        if not isinstance(glob, str) or not glob:
            raise ValueError(f"{where}: glob must be a non-empty string")
        exclude_raw = raw.get("exclude", [])
        if not isinstance(exclude_raw, list):
            raise ValueError(f"{where}: exclude must be a list")
        excludes: list[str] = []
        for ex in exclude_raw:
            if not isinstance(ex, str) or not ex:
                raise ValueError(
                    f"{where}: each exclude pattern must be a non-empty string"
                )
            excludes.append(ex)
        return ManifestEntry(glob=glob, exclude=tuple(excludes))
    raise ValueError(f"{where}: entry needs either path or glob")


def load_manifest(manifest_path: Path) -> Manifest:
    """Load + validate the partition manifest YAML.

    ``manifest_path`` is the path to the YAML file. Returns a parsed
    ``Manifest``; raises ``ValueError`` on structural problems and
    ``FileNotFoundError`` when the path is missing.
    """
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(
            f"manifest root must be a mapping; got {type(raw).__name__}"
        )
    for key in ("roots", "always_loaded", "dev_only"):
        if key not in raw:
            raise ValueError(f"manifest missing required key: {key}")
        if not isinstance(raw[key], list):
            raise ValueError(f"manifest.{key} must be a list")
    audit_excludes_raw = raw.get("audit_excludes", [])
    if not isinstance(audit_excludes_raw, list):
        raise ValueError("manifest.audit_excludes must be a list")
    roots = tuple(_coerce_root(r, "manifest.roots") for r in raw["roots"])
    audit_excludes = tuple(
        _coerce_pattern(p, "manifest.audit_excludes")
        for p in audit_excludes_raw
    )
    always_loaded = tuple(
        _coerce_entry(e, f"manifest.always_loaded[{i}]")
        for i, e in enumerate(raw["always_loaded"])
    )
    dev_only = tuple(
        _coerce_entry(e, f"manifest.dev_only[{i}]")
        for i, e in enumerate(raw["dev_only"])
    )
    return Manifest(
        roots=roots,
        audit_excludes=audit_excludes,
        always_loaded=always_loaded,
        dev_only=dev_only,
    )


def _coerce_root(raw: object, where: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{where}: root must be a non-empty string")
    return raw


def _coerce_pattern(raw: object, where: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{where}: pattern must be a non-empty string")
    return raw


def _glob_match(pattern: str, posix_path: str) -> bool:
    """Match ``posix_path`` against ``pattern`` with shell-glob
    semantics.

    - ``**`` matches zero or more path segments (recursive — crosses
      ``/`` boundaries).
    - ``*`` matches any character EXCEPT ``/`` (single-segment).
    - ``?`` matches any single character except ``/``.
    - Character classes (``[abc]``) match per ``fnmatch`` rules.

    Examples::

      _glob_match("*.md", "a.md")        == True
      _glob_match("*.md", "sub/a.md")    == False  # * does not cross /
      _glob_match("**/*.md", "sub/a.md") == True
      _glob_match("docs/**", "docs/x")   == True
      _glob_match("docs/**", "docs/sub/y") == True

    Note: ``docs/**`` does NOT match the bare ``docs`` path (one
    segment short). The audit walks files only, so this is academic
    — bare directory paths never appear as candidates. If callers
    need to match the bare directory, they should add a ``path:
    docs/`` entry.
    """
    import re

    # Translate to regex segment-by-segment. The escape rules:
    #   **  -> .*        (cross /)
    #   *   -> [^/]*     (single-segment)
    #   ?   -> [^/]
    #   [..]-> char class as-is
    #   other -> re.escape
    out: list[str] = []
    i = 0
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                # Skip a following '/' to match docs/** == docs (the
                # bare directory) AND docs/anything.
                if i < n and pattern[i] == "/":
                    i += 1
                    # Make the slash optional if ** swallowed nothing.
                    # Easier: emit the / as optional in the regex.
                    out.append("/?")
                continue
            out.append("[^/]*")
            i += 1
            continue
        if c == "?":
            out.append("[^/]")
            i += 1
            continue
        if c == "[":
            # Pass through character class up to closing ].
            j = pattern.find("]", i)
            if j == -1:
                out.append(re.escape(c))
                i += 1
                continue
            out.append(pattern[i : j + 1])
            i = j + 1
            continue
        out.append(re.escape(c))
        i += 1
    regex = "^" + "".join(out) + "$"
    return re.match(regex, posix_path) is not None


def expand_entry(
    entry: ManifestEntry,
    workspace_root: Path,
    candidate_paths: Iterable[str] | None = None,
) -> set[str]:
    """Resolve an entry against the workspace tree.

    Returns the set of workspace-relative POSIX paths matched by the
    entry. ``candidate_paths`` (if given) is the universe of paths to
    test against — passing the audit's pre-walked path list avoids
    re-walking the tree per entry. When ``candidate_paths`` is None,
    walks the tree from ``workspace_root`` for path-shaped entries
    (single existence check) or uses ``Path.glob`` for glob-shaped
    entries.
    """
    if entry.path is not None:
        # Path entries match exactly that path if it exists OR if it
        # appears in the candidate set (declaration-time semantics).
        # Forward-looking declarations (CLAUDE.dev.md before B lands)
        # are allowed: they resolve to {path} regardless of fs state.
        return {entry.path}
    assert entry.glob is not None
    pattern = entry.glob
    excludes = entry.exclude
    if candidate_paths is not None:
        matches = {
            p for p in candidate_paths if _glob_match(pattern, p)
        }
    else:
        matches = set()
        for path_obj in _walk_workspace(workspace_root):
            rel = path_obj.relative_to(workspace_root).as_posix()
            if _glob_match(pattern, rel):
                matches.add(rel)
    if excludes:
        kept = set()
        for m in matches:
            if any(_glob_match(ex, m) for ex in excludes):
                continue
            kept.add(m)
        matches = kept
    return matches


def _walk_workspace(workspace_root: Path) -> Iterable[Path]:
    """Yield every file path under ``workspace_root``.

    Follows the same pruning rules used by audit (`.git`, `.venv`,
    `.pytest_cache`, `__pycache__`, `*.egg-info`, `.scratch`) so the
    walker is cheap even on a populated repo. Audit-level exclusions
    are applied separately by the audit module.
    """
    pruned_dirs = {
        ".git",
        ".venv",
        ".pytest_cache",
        "__pycache__",
        ".scratch",
    }
    for dirpath, dirnames, filenames in os.walk(workspace_root):
        # Mutate dirnames in place to prune.
        dirnames[:] = [
            d
            for d in dirnames
            if d not in pruned_dirs and not d.endswith(".egg-info")
        ]
        for fname in filenames:
            yield Path(dirpath) / fname
