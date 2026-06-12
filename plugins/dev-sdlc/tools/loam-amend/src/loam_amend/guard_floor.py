"""GUARD-SWEEP FLOOR discovery (AC.GFLOOR.* family).

Per ``docs/plans/seal-guard-sweep-floor.md`` D-GFLOOR.1, the floor —
the cross-component protection sweep set that runs at EVERY seal
regardless of the amendment's fence — is discovered at runtime from
two rules:

(a) **Fence class** (AC.GFLOOR.1) — every *tracked* fence test
    (``*/tests/test_no_sealed_amendments.py`` +
    ``*/tests/test_cross_cutting.py``) regardless of tree location
    (``framework/*``, ``framework/tools/*``, ``plugins/*``),
    excluding ``docs/archive/``. Discovery is ``git ls-files``-based:
    tracked-only, so gitignored smoke trees (``.scratch/``) are
    excluded for free, and the rule cannot go stale — a new sealed
    component's fence test is a floor member the moment it is
    tracked.

(b) **Sweep class** (AC.GFLOOR.2) — glob patterns declared in the
    repo-local registry ``docs/plans/guard-floor.yaml``, resolved
    against tracked files at seal time. A pattern resolving to zero
    targets is STALE and recorded for the caller to halt on
    (AC.GFLOOR.3 — staleness is loud, never silent). Patterns ending
    in ``/`` name a directory target (one pytest invocation over the
    whole directory); other patterns are ``fnmatch``-style file
    globs (each matched file is one target).

The registry is REPO-LOCAL data, not tool source: the dev-sdlc
plugin ships to foreign repos where loam-specific guard paths would
be meaningless. A repo without the registry gets the fence-class
floor only, and an empty floor there is legitimate (young / synthetic
repos) — ``registry_present`` tells the seal step whether loud-halt
semantics apply.
"""

from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Repo-relative location of the sweep-class registry. Deliberately
# under ``docs/plans/`` — universally-admitted space in every
# manifest — so future registry edits never breach any fence
# (D-GFLOOR.1).
REGISTRY_RELPATH = Path("docs/plans/guard-floor.yaml")

# Fence-test basenames (AC.GFLOOR.1). ``test_cross_cutting.py`` is
# the hands-off-lifecycle naming per the amendment #22 ruling.
FENCE_BASENAMES = ("test_no_sealed_amendments.py", "test_cross_cutting.py")

# Tree prefixes excluded from fence-class discovery: archived sealed
# history is not part of the active protection floor.
EXCLUDED_PREFIXES = ("docs/archive/",)


class GuardFloorRegistryError(Exception):
    """The registry file exists but cannot be parsed/validated."""


@dataclass
class GuardFloor:
    """The resolved floor for one repo at one moment.

    ``fence_targets`` and ``sweep_targets`` are repo-relative paths
    (files, or directories for ``/``-suffixed registry patterns).
    ``stale_patterns`` carries every registry pattern that resolved
    to zero tracked targets — non-empty means the floor is stale and
    the seal must halt (AC.GFLOOR.3) when ``registry_present``.
    """

    fence_targets: list[Path] = field(default_factory=list)
    sweep_targets: list[Path] = field(default_factory=list)
    registry_present: bool = False
    stale_patterns: list[str] = field(default_factory=list)

    @property
    def targets(self) -> list[Path]:
        """All floor targets, fence class first, exact-path deduped."""
        seen: set[Path] = set()
        out: list[Path] = []
        for t in [*self.fence_targets, *self.sweep_targets]:
            if t in seen:
                continue
            seen.add(t)
            out.append(t)
        return out

    @property
    def empty(self) -> bool:
        return not self.fence_targets and not self.sweep_targets


def _tracked_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [ln for ln in result.stdout.splitlines() if ln.strip()]


def _is_fence_test(rel: str) -> bool:
    if rel.startswith(EXCLUDED_PREFIXES):
        return False
    parts = rel.split("/")
    return (
        len(parts) >= 2
        and parts[-1] in FENCE_BASENAMES
        and parts[-2] == "tests"
    )


def _load_registry_patterns(registry_path: Path) -> list[str]:
    """Return the pattern strings from a registry file.

    Schema (v1)::

        schema_version: 1
        patterns:
          - pattern: "plugins/dev-sdlc/tests/test_AC_PBRET_*.py"
            guard_class: "banned-stem sweep (retired-benchmark references)"

    ``guard_class`` is operator documentation; only ``pattern`` is
    consumed. Raises :class:`GuardFloorRegistryError` on any shape
    problem — a present-but-broken registry must halt the seal, not
    silently degrade to fence-only (AC.GFLOOR.3 spirit).
    """
    try:
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise GuardFloorRegistryError(
            f"{registry_path}: not valid YAML: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise GuardFloorRegistryError(
            f"{registry_path}: top level must be a mapping"
        )
    if data.get("schema_version") != 1:
        raise GuardFloorRegistryError(
            f"{registry_path}: unsupported schema_version "
            f"{data.get('schema_version')!r} (expected 1)"
        )
    raw = data.get("patterns")
    if not isinstance(raw, list) or not raw:
        raise GuardFloorRegistryError(
            f"{registry_path}: 'patterns' must be a non-empty list"
        )
    patterns: list[str] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict) or not isinstance(
            entry.get("pattern"), str
        ):
            raise GuardFloorRegistryError(
                f"{registry_path}: patterns[{i}] must be a mapping "
                "with a string 'pattern' key"
            )
        patterns.append(entry["pattern"])
    return patterns


def _resolve_pattern(
    pattern: str, tracked: list[str]
) -> list[Path]:
    """Resolve one registry pattern against the tracked-file list.

    ``/``-suffixed patterns name a directory: the directory is ONE
    target iff any tracked file lives under it. Other patterns are
    ``fnmatch``-style globs over full repo-relative paths; each match
    is one target.
    """
    if pattern.endswith("/"):
        if any(t.startswith(pattern) for t in tracked):
            return [Path(pattern.rstrip("/"))]
        return []
    return [Path(t) for t in tracked if fnmatch.fnmatchcase(t, pattern)]


def discover_guard_floor(repo_root: Path) -> GuardFloor:
    """Resolve the GUARD-SWEEP FLOOR for *repo_root* (D-GFLOOR.1).

    Raises :class:`GuardFloorRegistryError` when the registry file
    exists but is malformed. Pattern staleness is NOT an exception —
    it is reported via ``stale_patterns`` so the seal step can emit
    its structured halt diagnostic.
    """
    tracked = _tracked_files(repo_root)
    fence_targets = [Path(t) for t in tracked if _is_fence_test(t)]

    registry_path = repo_root / REGISTRY_RELPATH
    registry_present = registry_path.exists()
    sweep_targets: list[Path] = []
    stale_patterns: list[str] = []
    if registry_present:
        for pattern in _load_registry_patterns(registry_path):
            resolved = _resolve_pattern(pattern, tracked)
            if resolved:
                sweep_targets.extend(resolved)
            else:
                stale_patterns.append(pattern)

    return GuardFloor(
        fence_targets=sorted(fence_targets),
        sweep_targets=sweep_targets,
        registry_present=registry_present,
        stale_patterns=stale_patterns,
    )
