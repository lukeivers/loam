"""C26: zero imports from current-gen Ruby pOS or other legacy surfaces.

The primitive consumes only: stdlib, pydantic, pyee, OTel, PyYAML,
loam.scope_of_work, loam.primary_persona, loam.orchestrator,
loam.safety_layer, loam.reversibility_primitive.
"""

from __future__ import annotations

import pathlib
import re


ALLOWED_TOP_LEVEL_IMPORTS = {
    # stdlib — partial enumeration; sys.stdlib_module_names handles the rest.
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
    "math",
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
    import loam.cost_governance as cg

    pkg_dir = pathlib.Path(cg.__file__).parent
    return list(pkg_dir.rglob("*.py"))


_IMPORT = re.compile(
    r"^(?:from\s+([A-Za-z_][\w]*)(?:\.[A-Za-z_][\w]*)*\s+import\s+|"
    r"import\s+([A-Za-z_][\w]*))"
)


def _extract_root(match: re.Match[str]) -> str:
    return match.group(1) or match.group(2)


def test_C26_only_allowed_top_level_imports() -> None:
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
    assert bad == [], f"Imports from a non-allowed top-level package: {bad}"


def _is_stdlib(name: str) -> bool:
    import sys

    names = getattr(sys, "stdlib_module_names", None)
    if names is not None:
        return name in names
    return False
