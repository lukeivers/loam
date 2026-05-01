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

"""R24: zero imports from current-gen Ruby pOS or other legacy
surfaces. The primitive consumes only: stdlib, pydantic, pyee, OTel,
PyYAML, loam.scope_of_work, loam.primary_persona, loam.orchestrator,
loam.safety_layer.
"""

from __future__ import annotations

import pathlib
import re


ALLOWED_TOP_LEVEL_IMPORTS = {
    # stdlib — partial enumeration; any stdlib module passes.
    "__future__",
    "argparse",
    "asyncio",
    "contextlib",
    "dataclasses",
    "datetime",
    "enum",
    "hashlib",
    "inspect",
    "json",
    "os",
    "pathlib",
    "re",
    "sqlite3",
    "subprocess",
    "sys",
    "threading",
    "typing",
    "uuid",
    # permitted third-party
    "pydantic",
    "pyee",
    "opentelemetry",
    "yaml",
    # loam siblings this primitive is allowed to consume (post-M1e
    # namespace pivot — the top-level root for every framework
    # package is `loam`).
    "loam",
}


def _iter_sources() -> list[pathlib.Path]:
    import loam.reversibility_primitive as rp

    pkg_dir = pathlib.Path(rp.__file__).parent
    return list(pkg_dir.rglob("*.py"))


# Real import lines only. We match two shapes:
#   `from PKG import ...`
#   `import PKG` (possibly `import PKG as X` or `import PKG.sub`)
# Both must be at the start of the line AND contain real import syntax
# so docstring prose like "from the Eve inference" (a sentence
# starting with `from `) does not false-trigger.
_IMPORT = re.compile(
    r"^(?:from\s+([A-Za-z_][\w]*)(?:\.[A-Za-z_][\w]*)*\s+import\s+|"
    r"import\s+([A-Za-z_][\w]*))"
)


def _extract_root(match: re.Match[str]) -> str:
    return match.group(1) or match.group(2)


def test_R24_only_allowed_top_level_imports() -> None:
    bad: list[tuple[str, str]] = []
    for src in _iter_sources():
        for line in src.read_text().splitlines():
            m = _IMPORT.match(line)
            if not m:
                continue
            root = _extract_root(m)
            if root in ALLOWED_TOP_LEVEL_IMPORTS:
                continue
            if _is_stdlib(root):
                continue
            bad.append((str(src), line))
    assert bad == [], (
        f"Imports from a non-allowed top-level package: {bad}"
    )


def _is_stdlib(name: str) -> bool:
    """Conservative stdlib check — true only for names importable with
    no site-packages on the path. We approximate via sys.stdlib_module_names."""
    import sys

    names = getattr(sys, "stdlib_module_names", None)
    if names is not None:
        return name in names
    # Fallback for older pythons (not the case on pos-v2 but safe).
    return False
