"""Deterministic slug derivation for AC IDs (cross-language shared).

Per AC.DRY.2 (v0.1.8 Cycle 4b) — the single canonical home for
:func:`slugify` + :func:`file_slug` helpers. Pre-4b these were
duplicated byte-identical at ``lang/ruby/_ast_utils.py`` and
``lang/jsts/_ast_utils.py``; Cycle 4b consolidates them here while
retaining a compat-shim re-export at the per-adapter ``_ast_utils``
modules so external callers (and the recognizer modules' historical
import sites) continue to work.

Per AC.DRY.4 — recognizer modules under ``lang/{ruby,jsts}/recognizers/``
are migrated in Cycle 4b to import from this canonical path directly
(``from .._common.slugs import slugify, file_slug``); the per-adapter
``_ast_utils`` re-export remains as a compat shim only.
"""

from __future__ import annotations

import re
from pathlib import Path


_SLUG_RE = re.compile(r"[^a-zA-Z0-9]+")


def slugify(text: str) -> str:
    """Lowercase + non-alphanumeric → underscore + strip.

    Used to derive deterministic AC IDs from arbitrary text. Empty
    inputs return ``""``; the caller must guard against that if
    required.
    """
    return _SLUG_RE.sub("_", text).strip("_").lower()


def file_slug(file_path: Path, repo_root: Path) -> str:
    """A path-relative slug used as the suffix of cross-slice-unique
    ``ac_id`` values.

    Per Cycle 3 Surface #9 / Cycle 4 RF §10 #9 — slugs extended with
    file-relative-path suffix to mitigate cross-slice ``ac_id``
    collisions.
    """
    try:
        rel = file_path.relative_to(repo_root)
    except ValueError:
        rel = Path(file_path.name)
    return slugify(rel.as_posix())
