"""Partition audit (AC.F3 + AC.F5).

Three audit checks:

  1. **Disjointness** (AC.F1) — ``always_loaded`` and ``dev_only`` do
     not share any resolved path.
  2. **Orphan coverage** (AC.F5) — every workspace-tree path under
     ``manifest.roots`` (after ``manifest.audit_excludes``) is matched
     by exactly one of the two sets.
  3. **Cross-mode reference integrity** (AC.F3) — for every Markdown
     file in ``always_loaded``, every backtick-quoted path or
     Markdown-link target either resolves to an ``always_loaded`` path,
     or is an external URL, or is not workspace-resolvable. Any link
     that resolves to a ``dev_only`` path is a violation.

The module exposes ``audit_partition`` (full audit) and the
``scan_cross_mode_references`` helper (AC.F3-only) for tests.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from loam_mode.manifest import (
    Manifest,
    _glob_match,
    expand_entry,
)


@dataclass(frozen=True)
class CrossModeReference:
    """A reference inside an always-loaded file that points at a dev-
    only path. Used by AC.F3."""

    source_path: str  # always-loaded artefact carrying the reference
    target_path: str  # the dev-only path being referenced
    line_number: int  # 1-indexed
    snippet: str  # the matched text


@dataclass
class AuditReport:
    """Aggregated audit findings."""

    overlap: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    cross_mode_refs: list[CrossModeReference] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return (
            not self.overlap
            and not self.orphans
            and not self.cross_mode_refs
        )

    def format_diagnostic(self) -> str:
        lines: list[str] = []
        if self.overlap:
            lines.append("Overlap (paths in both sets):")
            for p in sorted(self.overlap):
                lines.append(f"  - {p}")
        if self.orphans:
            lines.append("Orphans (under roots, in neither set):")
            for p in sorted(self.orphans):
                lines.append(f"  - {p}")
        if self.cross_mode_refs:
            lines.append(
                "Cross-mode references "
                "(always-loaded artefact references dev-only path):"
            )
            for ref in self.cross_mode_refs:
                lines.append(
                    f"  - {ref.source_path}:{ref.line_number} -> "
                    f"{ref.target_path} ({ref.snippet!r})"
                )
        if not lines:
            lines.append("partition is clean")
        return "\n".join(lines)


def _walk_audit_tree(
    workspace_root: Path,
    roots: Iterable[str],
    audit_excludes: Iterable[str],
) -> list[str]:
    """Walk the workspace tree under ``roots`` returning workspace-
    relative POSIX paths, with ``audit_excludes`` patterns subtracted
    and the standard transient-dir prune list applied.
    """
    pruned_dirs = {
        ".git",
        ".venv",
        ".pytest_cache",
        "__pycache__",
        ".scratch",
    }
    excludes_list = list(audit_excludes)
    seen: set[str] = set()
    for root_str in roots:
        root_path = workspace_root / root_str
        if not root_path.exists():
            continue
        if root_path.is_file():
            rel = root_path.relative_to(workspace_root).as_posix()
            if not any(_glob_match(ex, rel) for ex in excludes_list):
                seen.add(rel)
            continue
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [
                d
                for d in dirnames
                if d not in pruned_dirs and not d.endswith(".egg-info")
            ]
            for fname in filenames:
                full = Path(dirpath) / fname
                rel = full.relative_to(workspace_root).as_posix()
                if any(_glob_match(ex, rel) for ex in excludes_list):
                    continue
                seen.add(rel)
    return sorted(seen)


def _resolve_set(
    entries: Iterable, workspace_root: Path, candidates: list[str]
) -> set[str]:
    resolved: set[str] = set()
    for entry in entries:
        resolved.update(expand_entry(entry, workspace_root, candidates))
    return resolved


# --- AC.F3 reference scanner -----------------------------------------

# Backtick-quoted token containing a slash or a recognised file
# extension. We match conservatively: tokens must look like
# workspace paths (contain '.' or '/') and end at a whitespace /
# closing backtick.
_BACKTICK_REF_RE = re.compile(r"`([^`\n\s]+)`")
# Markdown-link target: [text](target) — capture target only.
_MD_LINK_RE = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")
_URL_SCHEMES = ("http://", "https://", "mailto:", "ftp://")


def _is_external_url(target: str) -> bool:
    return any(target.startswith(s) for s in _URL_SCHEMES)


def _looks_workspace_path(target: str) -> bool:
    """Heuristic: token looks like a workspace-relative path.

    Must contain a slash OR a dot (extension), must not be a pure
    identifier / inline-code. Anchors (#fragment-only refs) are
    discarded.
    """
    if not target:
        return False
    if target.startswith("#"):
        return False
    if _is_external_url(target):
        return False
    if "://" in target:
        return False
    # Strip trailing punctuation common in prose: . , ; :
    return ("/" in target) or ("." in target)


def _normalise_target(target: str) -> str:
    """Strip Markdown anchors + leading ``./``."""
    # Drop fragments.
    if "#" in target:
        target = target.split("#", 1)[0]
    if target.startswith("./"):
        target = target[2:]
    return target


def _path_in_set(target: str, resolved_set: set[str]) -> bool:
    """Check whether ``target`` resolves to a path in ``resolved_set``.

    Handles the trailing-slash convention (``docs/plans/``
    matches any path under that prefix in the set).
    """
    if target in resolved_set:
        return True
    if target.endswith("/"):
        prefix = target
        return any(p.startswith(prefix) for p in resolved_set)
    return False


def scan_cross_mode_references(
    workspace_root: Path,
    always_loaded_set: set[str],
    dev_only_set: set[str],
) -> list[CrossModeReference]:
    """Scan every Markdown file in ``always_loaded_set`` for refs that
    resolve to ``dev_only_set``. Returns the violations.
    """
    refs: list[CrossModeReference] = []
    for source_rel in sorted(always_loaded_set):
        if not source_rel.endswith(".md"):
            continue
        source_path = workspace_root / source_rel
        if not source_path.is_file():
            continue
        try:
            text = source_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line_idx, line in enumerate(text.splitlines(), start=1):
            for match in _BACKTICK_REF_RE.finditer(line):
                target_raw = match.group(1)
                _maybe_record(
                    refs,
                    source_rel,
                    target_raw,
                    line_idx,
                    line,
                    always_loaded_set,
                    dev_only_set,
                )
            for match in _MD_LINK_RE.finditer(line):
                target_raw = match.group(1)
                _maybe_record(
                    refs,
                    source_rel,
                    target_raw,
                    line_idx,
                    line,
                    always_loaded_set,
                    dev_only_set,
                )
    return refs


def _maybe_record(
    refs: list[CrossModeReference],
    source_rel: str,
    target_raw: str,
    line_idx: int,
    line: str,
    always_loaded_set: set[str],
    dev_only_set: set[str],
) -> None:
    if _is_external_url(target_raw):
        return
    if not _looks_workspace_path(target_raw):
        return
    target = _normalise_target(target_raw)
    if not target:
        return
    # Skip targets that resolve into always-loaded paths.
    if _path_in_set(target, always_loaded_set):
        return
    # Targets that resolve into dev-only paths are violations.
    if _path_in_set(target, dev_only_set):
        refs.append(
            CrossModeReference(
                source_path=source_rel,
                target_path=target,
                line_number=line_idx,
                snippet=line.strip(),
            )
        )
        return
    # Targets that don't resolve to either set are not AC.F3 violations
    # (they're either external-shaped tokens that fooled the heuristic,
    # or out-of-tree paths). Audit doesn't flag them.


# --- Top-level audit -------------------------------------------------


def audit_partition(
    manifest: Manifest, workspace_root: Path
) -> AuditReport:
    """Run the full audit. Returns an ``AuditReport``."""
    candidates = _walk_audit_tree(
        workspace_root, manifest.roots, manifest.audit_excludes
    )
    always_set = _resolve_set(
        manifest.always_loaded, workspace_root, candidates
    )
    dev_set = _resolve_set(
        manifest.dev_only, workspace_root, candidates
    )
    overlap = sorted(always_set & dev_set)
    classified = always_set | dev_set
    orphans = sorted(set(candidates) - classified)
    refs = scan_cross_mode_references(
        workspace_root, always_set, dev_set
    )
    return AuditReport(
        overlap=overlap,
        orphans=orphans,
        cross_mode_refs=refs,
    )
