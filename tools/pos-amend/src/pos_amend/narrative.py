"""Append narrative-block content to a ``seals/SEAL_COMMIT.*`` file.

T12 requires: append the body to the target with a single blank line
between the existing trailing content and the new block.
"""

from __future__ import annotations

from pathlib import Path


def append_narrative(target: Path, body: str) -> bool:
    """Append *body* to *target* with one blank-line separator.

    Returns True if the file was modified. Creates the file if absent.
    """
    body = body.rstrip() + "\n"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        return True
    existing = target.read_text(encoding="utf-8")
    # Idempotency: if the body already appears verbatim at the end, skip.
    if existing.endswith(body):
        return False
    # Ensure exactly one blank line between existing content and body.
    trimmed = existing.rstrip("\n")
    new_text = trimmed + "\n\n" + body
    target.write_text(new_text, encoding="utf-8")
    return True
