"""Read/write the ``tests/SEAL_COMMIT`` sidecar file.

The sidecar is a plain text file holding a single SHA (or the literal
``HEAD`` during build). Writing it does not commit; the amendment-cycle
ritual commits the sidecar separately.

T6 requires that ``write_sidecar`` overwrites the file with the given
SHA + a trailing newline, matching the hand-authored shape.
T11 (seal) uses the same write path.
"""

from __future__ import annotations

from pathlib import Path


def read_sidecar(path: Path) -> str:
    """Return the trimmed sidecar contents; empty string if absent."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def write_sidecar(path: Path, sha: str) -> bool:
    """Write *sha* + newline to *path*. Returns True if the content changed."""
    current = read_sidecar(path)
    if current == sha.strip():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{sha.strip()}\n", encoding="utf-8")
    return True
