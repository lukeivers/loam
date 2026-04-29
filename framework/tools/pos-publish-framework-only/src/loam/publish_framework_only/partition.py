"""Publish-mode partition — manifest loader + path classifier.

Owner-authored partition data lives at
``<repo>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml``.
This module loads the YAML, validates the structural shape, and
classifies workspace-relative paths into one of four partition
classes:

  - ``PUBLIC_ONLY``           ships in the public synthesis output
                              and ONLY there (rare).
  - ``DEV_AND_PUBLIC``        ships in the public synthesis output
                              AND remains in the dev tree.
  - ``DEV_ONLY``              stays in the dev tree, NEVER ships
                              publicly.
  - ``EXCLUDED_FROM_PUBLISH`` MUST NOT ship publicly under any
                              condition.

A path that matches an ``audit_excludes`` glob is unclassified
(``classify_path`` returns ``None``); callers treat unclassified
audit-excluded paths as out-of-scope.

A path that is NOT audit-excluded and matches no entry in any of
the four sections is also unclassified (``classify_path`` returns
``None``). The synthesis tool treats this as a build error —
the manifest must cover every shipping path (AC.OSS-M2.4).

Classification precedence (first-match-wins, applied in this order):

  1. ``EXCLUDED_FROM_PUBLISH`` (safety class — checked first).
  2. ``DEV_ONLY``              (dev-tools must not be promoted by a
                                broader ``dev_and_public`` glob).
  3. ``PUBLIC_ONLY``           (rare; checked before
                                ``dev_and_public``).
  4. ``DEV_AND_PUBLIC``        (default ship class).

Glob semantics mirror ``loam_mode.manifest._glob_match``:

  - ``**``  matches zero or more path segments (recursive — crosses
            ``/`` boundaries).
  - ``*``   matches any character EXCEPT ``/`` (single-segment).
  - ``?``   matches any single character except ``/``.
  - ``[..]`` character class per ``fnmatch`` rules.

Exclusion patterns (the optional ``exclude`` list on a glob entry)
are subtractive — the entry's match-set is the glob's matches MINUS
matches against any exclusion pattern.

Public surface:

  - :class:`PartitionClass`     — StrEnum of the four classes.
  - :class:`ManifestEntry`      — single entry (path or glob+exclude).
  - :class:`PartitionManifest`  — parsed manifest dataclass.
  - :class:`ManifestError`      — raised on schema problems.
  - :func:`load_manifest`       — parse YAML → ``PartitionManifest``.
  - :func:`classify_path`       — classify a workspace-relative path.
  - :func:`is_publishable`      — True iff class is ``PUBLIC_ONLY``
                                   or ``DEV_AND_PUBLIC``.
  - :func:`is_audit_excluded`   — True iff path matches any
                                   ``audit_excludes`` pattern.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml


SCHEMA_VERSION = 1


class PartitionClass(str, Enum):
    """The four publish-mode partition classes."""

    PUBLIC_ONLY = "public_only"
    DEV_AND_PUBLIC = "dev_and_public"
    DEV_ONLY = "dev_only"
    EXCLUDED_FROM_PUBLISH = "excluded_from_publish"


# Classification precedence (first-match-wins). The classifier checks
# entries in this order; the first class whose entries match the path
# wins. Per plan §10 D-build.M2.3.
_PRECEDENCE: tuple[PartitionClass, ...] = (
    PartitionClass.EXCLUDED_FROM_PUBLISH,
    PartitionClass.DEV_ONLY,
    PartitionClass.PUBLIC_ONLY,
    PartitionClass.DEV_AND_PUBLIC,
)


class ManifestError(Exception):
    """Raised on partition-manifest schema problems."""


@dataclass(frozen=True)
class ManifestEntry:
    """A single classification entry.

    Exactly one of ``path`` or ``glob`` is set. ``exclude`` is empty
    unless ``glob`` is set and the YAML provided exclusions.
    """

    path: str | None = None
    glob: str | None = None
    exclude: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (self.path is None) == (self.glob is None):
            raise ManifestError(
                "ManifestEntry must set exactly one of path / glob"
            )
        if self.path is not None and self.exclude:
            raise ManifestError(
                "ManifestEntry: exclude is only valid with glob"
            )


@dataclass(frozen=True)
class PartitionManifest:
    """Parsed publish-mode partition manifest."""

    schema_version: int
    audit_roots: tuple[str, ...]
    audit_excludes: tuple[str, ...]
    public_only: tuple[ManifestEntry, ...]
    dev_and_public: tuple[ManifestEntry, ...]
    dev_only: tuple[ManifestEntry, ...]
    excluded_from_publish: tuple[ManifestEntry, ...]

    def entries_for(self, klass: PartitionClass) -> tuple[ManifestEntry, ...]:
        """Return the entry tuple for a given partition class."""
        if klass is PartitionClass.PUBLIC_ONLY:
            return self.public_only
        if klass is PartitionClass.DEV_AND_PUBLIC:
            return self.dev_and_public
        if klass is PartitionClass.DEV_ONLY:
            return self.dev_only
        if klass is PartitionClass.EXCLUDED_FROM_PUBLISH:
            return self.excluded_from_publish
        raise ManifestError(f"unknown partition class: {klass!r}")


# ---- Glob match (mirrors loam_mode.manifest._glob_match) -------------


def _glob_match(pattern: str, posix_path: str) -> bool:
    """Match ``posix_path`` against ``pattern`` with shell-glob
    semantics.

    - ``**`` matches zero or more path segments (crosses ``/``).
    - ``*``  matches any character EXCEPT ``/``.
    - ``?``  matches any single character except ``/``.
    - ``[..]`` character class as-is.
    """
    out: list[str] = []
    i = 0
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                # ``docs/**`` should match docs/x AND docs (the bare
                # path); make the trailing slash optional.
                if i < n and pattern[i] == "/":
                    i += 1
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


def _entry_matches(entry: ManifestEntry, posix_path: str) -> bool:
    """True iff ``entry`` matches ``posix_path``."""
    if entry.path is not None:
        # Exact match for path entries.
        return entry.path == posix_path
    assert entry.glob is not None
    if not _glob_match(entry.glob, posix_path):
        return False
    for ex in entry.exclude:
        if _glob_match(ex, posix_path):
            return False
    return True


# ---- YAML loader / coercion ------------------------------------------


def _coerce_string(raw: object, where: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ManifestError(f"{where}: must be a non-empty string")
    return raw


def _coerce_entry(raw: object, where: str) -> ManifestEntry:
    if not isinstance(raw, dict):
        raise ManifestError(
            f"{where}: entry must be a mapping; got {type(raw).__name__}"
        )
    if "path" in raw and "glob" in raw:
        raise ManifestError(
            f"{where}: entry sets both path and glob; pick one"
        )
    if "path" in raw:
        path = raw["path"]
        if not isinstance(path, str) or not path:
            raise ManifestError(
                f"{where}: path must be a non-empty string"
            )
        return ManifestEntry(path=path)
    if "glob" in raw:
        glob = raw["glob"]
        if not isinstance(glob, str) or not glob:
            raise ManifestError(
                f"{where}: glob must be a non-empty string"
            )
        exclude_raw = raw.get("exclude", [])
        if not isinstance(exclude_raw, list):
            raise ManifestError(f"{where}: exclude must be a list")
        excludes: list[str] = []
        for ex in exclude_raw:
            if not isinstance(ex, str) or not ex:
                raise ManifestError(
                    f"{where}: each exclude pattern must be "
                    "a non-empty string"
                )
            excludes.append(ex)
        return ManifestEntry(glob=glob, exclude=tuple(excludes))
    # Permitted-keys-only check: forbid unknown keys at entry level.
    if not raw:
        raise ManifestError(
            f"{where}: entry needs either path or glob"
        )
    raise ManifestError(
        f"{where}: entry needs either path or glob"
    )


_REQUIRED_TOP_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "audit_roots",
        "audit_excludes",
        "public_only",
        "dev_and_public",
        "dev_only",
        "excluded_from_publish",
    }
)


def load_manifest(manifest_path: Path) -> PartitionManifest:
    """Load + validate the publish-mode partition manifest YAML.

    Parameters
    ----------
    manifest_path:
        Path to the YAML file.

    Returns
    -------
    PartitionManifest
        Parsed manifest.

    Raises
    ------
    ManifestError
        On any schema-shape problem (missing required key, unknown
        top-level key, non-list value where list expected, malformed
        entry, ``schema_version != 1``).
    FileNotFoundError
        When ``manifest_path`` does not exist.
    """
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"manifest not found: {manifest_path}"
        )
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ManifestError(
            "manifest root must be a mapping; got "
            f"{type(raw).__name__}"
        )
    # Forward-strict: reject unknown top-level keys.
    unknown = set(raw.keys()) - _REQUIRED_TOP_KEYS
    if unknown:
        raise ManifestError(
            f"manifest carries unknown top-level keys: "
            f"{sorted(unknown)!r}"
        )
    # Required keys present.
    missing = _REQUIRED_TOP_KEYS - set(raw.keys())
    if missing:
        raise ManifestError(
            f"manifest missing required keys: {sorted(missing)!r}"
        )
    # schema_version
    if raw["schema_version"] != SCHEMA_VERSION:
        raise ManifestError(
            f"unsupported schema_version: {raw['schema_version']!r} "
            f"(expected {SCHEMA_VERSION})"
        )
    # List-shape checks.
    for key in (
        "audit_roots",
        "audit_excludes",
        "public_only",
        "dev_and_public",
        "dev_only",
        "excluded_from_publish",
    ):
        if not isinstance(raw[key], list):
            raise ManifestError(
                f"manifest.{key} must be a list; got "
                f"{type(raw[key]).__name__}"
            )
    audit_roots = tuple(
        _coerce_string(r, f"manifest.audit_roots[{i}]")
        for i, r in enumerate(raw["audit_roots"])
    )
    audit_excludes = tuple(
        _coerce_string(p, f"manifest.audit_excludes[{i}]")
        for i, p in enumerate(raw["audit_excludes"])
    )
    public_only = tuple(
        _coerce_entry(e, f"manifest.public_only[{i}]")
        for i, e in enumerate(raw["public_only"])
    )
    dev_and_public = tuple(
        _coerce_entry(e, f"manifest.dev_and_public[{i}]")
        for i, e in enumerate(raw["dev_and_public"])
    )
    dev_only = tuple(
        _coerce_entry(e, f"manifest.dev_only[{i}]")
        for i, e in enumerate(raw["dev_only"])
    )
    excluded_from_publish = tuple(
        _coerce_entry(e, f"manifest.excluded_from_publish[{i}]")
        for i, e in enumerate(raw["excluded_from_publish"])
    )
    return PartitionManifest(
        schema_version=int(raw["schema_version"]),
        audit_roots=audit_roots,
        audit_excludes=audit_excludes,
        public_only=public_only,
        dev_and_public=dev_and_public,
        dev_only=dev_only,
        excluded_from_publish=excluded_from_publish,
    )


# ---- Classification --------------------------------------------------


def is_audit_excluded(
    manifest: PartitionManifest, posix_path: str
) -> bool:
    """True iff ``posix_path`` matches any ``audit_excludes`` glob."""
    return any(
        _glob_match(pat, posix_path)
        for pat in manifest.audit_excludes
    )


def classify_path(
    manifest: PartitionManifest, posix_path: str
) -> PartitionClass | None:
    """Classify a workspace-relative POSIX path.

    Returns the partition class if any entry matches; ``None`` if
    the path is audit-excluded OR if no entry matches in any class.

    Precedence: first-match-wins in the order
    ``EXCLUDED_FROM_PUBLISH`` → ``DEV_ONLY`` → ``PUBLIC_ONLY`` →
    ``DEV_AND_PUBLIC``. Per plan §10 D-build.M2.3.
    """
    if is_audit_excluded(manifest, posix_path):
        return None
    for klass in _PRECEDENCE:
        for entry in manifest.entries_for(klass):
            if _entry_matches(entry, posix_path):
                return klass
    return None


def is_publishable(klass: PartitionClass | None) -> bool:
    """True iff ``klass`` is a ship class.

    ``PUBLIC_ONLY`` and ``DEV_AND_PUBLIC`` ship publicly.
    ``DEV_ONLY``, ``EXCLUDED_FROM_PUBLISH``, and ``None``
    (unclassified or audit-excluded) do not.
    """
    return klass in (
        PartitionClass.PUBLIC_ONLY,
        PartitionClass.DEV_AND_PUBLIC,
    )
