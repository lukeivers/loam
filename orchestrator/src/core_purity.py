"""Core-purity assertion.

pOS core ships zero personas. The orchestrator is framework code only.
If any file under the orchestrator package matches persona shapes
(a `contract.yaml`, a `prompt.md`, or a directory literally named
`personas/`), the build fails.

This assertion runs at package import time; the test suite runs it
explicitly as well for belt-and-braces.
"""

from __future__ import annotations

from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent


_FORBIDDEN_FILENAMES = {"contract.yaml", "prompt.md"}
_FORBIDDEN_DIRNAMES = {"personas"}


def assert_core_purity(package_root: Path | None = None) -> None:
    """Raise RuntimeError if any persona content is present inside the
    orchestrator package."""
    root = Path(package_root) if package_root is not None else _PKG_ROOT
    offences: list[str] = []
    for entry in root.rglob("*"):
        if entry.is_dir() and entry.name in _FORBIDDEN_DIRNAMES:
            offences.append(f"persona directory: {entry}")
        if entry.is_file() and entry.name in _FORBIDDEN_FILENAMES:
            offences.append(f"persona file: {entry}")
    if offences:
        raise RuntimeError(
            "core purity violated — pOS orchestrator must not ship personas:\n"
            + "\n".join(offences)
        )


# Enforce on import. Keep this call cheap — rglob on the small src
# tree is microseconds.
assert_core_purity()
