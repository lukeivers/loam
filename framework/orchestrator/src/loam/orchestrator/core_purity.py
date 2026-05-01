# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
