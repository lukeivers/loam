"""Plain HTML/JS surface recognizer (file-level).

Per AC.JSTS.2 + Surface #8 — pass-1 indexes ``<script>``-bearing
HTML files at FILE LEVEL. One PLAUSIBLE-band :class:`BandedAC` per
HTML file containing at least one ``<script>`` tag (named
``f"AC.JSTS.html.{file_slug}"``).

No deep AST parse of inline JS in pass-1. Deep inline-JS analysis
is deferred to v0.2+ per the dispatch brief: "AC noted as
PLAUSIBLE-by-default."

This recognizer is FILE-LEVEL — it does NOT take a tree-sitter
tree as input (HTML is not a JS/TS grammar). It reads the file
contents and looks for the literal ``<script`` substring.
"""

from __future__ import annotations

import re
from pathlib import Path

from ....bands import BandedAC, ConfidenceBand, Evidence
from ..._common.slugs import file_slug, slugify


_SCRIPT_TAG_RE = re.compile(rb"<script\b", re.IGNORECASE)


def recognize_plain_html_js(
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for HTML files containing inline
    or referenced JavaScript via ``<script>`` tags.

    Returns ``[]`` for non-HTML files or HTML files without
    ``<script>`` tags.
    """
    if file_path.suffix.lower() not in (".html", ".htm"):
        return []

    try:
        contents = file_path.read_bytes()
    except OSError:
        return []

    if not _SCRIPT_TAG_RE.search(contents):
        return []

    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    basename = file_path.name
    return [
        BandedAC(
            ac_id=f"AC.JSTS.html.{fslug}",
            text=(
                f"HTML page {basename} contains client-side "
                f"JavaScript (<script> tag)"
            ),
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(
                kind="source",
                citations=[f"{file_rel}:1"],
                repo_sha=repo_sha,
            ),
            backing_files=[file_rel],
        )
    ]
