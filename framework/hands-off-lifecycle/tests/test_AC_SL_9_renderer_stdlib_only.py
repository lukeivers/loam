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

"""AC.SL.9 — renderer's runtime dependencies are stdlib only.

Outcome (per locked plan §4 / D4 ruling 2026-04-26): the renderer
script's runtime dependencies are limited to the Python standard
library (no ``pip install`` required to run it).

Static check via ``ast``: walk every top-level + nested import in
``hands-off-lifecycle/hooks/statusline.py``, normalise to the root
module name, and assert each is in ``sys.stdlib_module_names`` or is
the renderer's sibling-module convention (``first_run_state``).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RENDERER_PATH = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "statusline.py"
)


_HOOKS_SIBLINGS = {
    # Sibling modules that live in the same hooks/ directory and are
    # themselves stdlib-only by the same constraint. The amendment
    # touches only `first_run_state` — its import audit lives in the
    # original detachment-amendment test suite.
    "first_run_state",
}


def _collect_root_imports(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and not node.module:
                # Pure relative (e.g. `from . import foo`) — skip; no
                # third-party dep is implied.
                continue
            if node.module:
                roots.add(node.module.split(".", 1)[0])
    return roots


def test_AC_SL_9_renderer_imports_stdlib_only() -> None:
    roots = _collect_root_imports(RENDERER_PATH)
    stdlib = set(sys.stdlib_module_names)
    non_stdlib = {
        m for m in roots if m not in stdlib and m not in _HOOKS_SIBLINGS
    }
    assert not non_stdlib, (
        f"renderer imports non-stdlib modules: {sorted(non_stdlib)} — "
        "AC.SL.9 forbids pip-install dependencies."
    )
