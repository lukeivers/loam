"""Parse + edit the ``BASELINE = "<sha>"`` literal inside a seal-diff test.

The BASELINE constant is a per-component literal the tests use to pin the
diff window. Amendment flow requires advancing it to the pre-amendment tip
each time a new window opens. We rewrite the single-line literal via a
regex anchored at line start — no AST parse, no import-side-effects.

T5 requires that ``set_baseline`` rewrites an existing BASELINE literal
to the target SHA while preserving the rest of the file byte-for-byte.
"""

from __future__ import annotations

import re
from pathlib import Path


_BASELINE_RE = re.compile(
    r'^(?P<prefix>BASELINE\s*=\s*)"(?P<sha>[0-9a-fA-F]{7,40})"(?P<suffix>.*)$',
    re.MULTILINE,
)


class BaselineNotFound(Exception):
    """Raised when the file contains no top-level BASELINE literal."""


class BaselineAmbiguous(Exception):
    """Raised when the file contains multiple BASELINE assignments."""


def read_baseline(path: Path) -> str:
    """Return the current BASELINE SHA from *path*, or raise."""
    text = path.read_text(encoding="utf-8")
    matches = _BASELINE_RE.findall(text)
    if not matches:
        raise BaselineNotFound(f"{path}: no BASELINE literal found")
    if len(matches) > 1:
        raise BaselineAmbiguous(f"{path}: {len(matches)} BASELINE literals found")
    return matches[0][1]


def set_baseline(path: Path, sha: str) -> bool:
    """Rewrite the BASELINE literal in *path* to *sha*.

    Returns True if the file was modified, False if BASELINE was already
    at *sha*. Raises ``BaselineNotFound`` / ``BaselineAmbiguous`` on
    structural mismatch.
    """
    text = path.read_text(encoding="utf-8")
    matches = list(_BASELINE_RE.finditer(text))
    if not matches:
        raise BaselineNotFound(f"{path}: no BASELINE literal found")
    if len(matches) > 1:
        raise BaselineAmbiguous(f"{path}: {len(matches)} BASELINE literals found")
    m = matches[0]
    if m.group("sha") == sha:
        return False
    new_line = f'{m.group("prefix")}"{sha}"{m.group("suffix")}'
    new_text = text[: m.start()] + new_line + text[m.end():]
    path.write_text(new_text, encoding="utf-8")
    return True
