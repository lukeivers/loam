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

"""AC.WBM2M.1 — constant rename + 3 callsite flips to main.

OSS dev-architecture migration follow-up (2026-05-04). Verifies the
module-level constant rename + the 3 production callsites all
reference the new constant. Assertions are scoped to the active code
surface (string literals); historical narrative in module-level
docstrings/comments is intentionally retained as audit trail.
"""

from __future__ import annotations

import ast
from pathlib import Path

from loam.workspace_bootstrap import new_workspace


def _new_workspace_source_path() -> Path:
    return Path(new_workspace.__file__)


def test_AC_WBM2M_1_canonical_branch_constant_present_with_main():
    """The module exposes ``CANONICAL_BRANCH = "main"`` at module
    level; the legacy ``FRAMEWORK_ONLY_BRANCH`` is gone.
    """
    assert hasattr(new_workspace, "CANONICAL_BRANCH"), (
        "AC.WBM2M.1: new_workspace must export CANONICAL_BRANCH"
    )
    assert new_workspace.CANONICAL_BRANCH == "main", (
        f"AC.WBM2M.1: CANONICAL_BRANCH should be 'main'; "
        f"got {new_workspace.CANONICAL_BRANCH!r}"
    )
    assert not hasattr(new_workspace, "FRAMEWORK_ONLY_BRANCH"), (
        "AC.WBM2M.1: FRAMEWORK_ONLY_BRANCH must be gone post-migration"
    )


def test_AC_WBM2M_1_no_framework_only_string_literal_in_source():
    """Active code in ``new_workspace.py`` carries no ``"framework-only"``
    string literal (only docstrings/comments may reference the term
    as historical narrative).

    Walks the AST + extracts every ``Constant`` of type ``str``
    (excluding the module docstring + function docstrings which appear
    as the first ``Expr`` in their containing scope's ``body``).
    """
    src = _new_workspace_source_path().read_text(encoding="utf-8")
    tree = ast.parse(src)

    # Collect docstring node IDs so we can exclude them — those are
    # historical narrative, not active code.
    docstring_ids: set[int] = set()

    def _collect_docstring(node: ast.AST) -> None:
        body = getattr(node, "body", None)
        if not body:
            return
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            if isinstance(first.value.value, str):
                docstring_ids.add(id(first.value))

    _collect_docstring(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            _collect_docstring(node)

    offending: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in docstring_ids:
                continue
            if "framework-only" in node.value:
                offending.append(node.value)

    assert not offending, (
        "AC.WBM2M.1: active source string literals must not contain "
        f"'framework-only'; found: {offending!r}"
    )


def test_AC_WBM2M_1_helper_renamed_to_canonical_branch():
    """The materialise helper is now ``_materialise_canonical_branch``;
    the legacy ``_materialise_framework_only_branch`` is gone.
    """
    assert hasattr(new_workspace, "_materialise_canonical_branch"), (
        "AC.WBM2M.1: _materialise_canonical_branch must exist"
    )
    assert not hasattr(new_workspace, "_materialise_framework_only_branch"), (
        "AC.WBM2M.1: _materialise_framework_only_branch must be gone "
        "post-migration"
    )


def test_AC_WBM2M_1_clone_canonical_default_branch_is_main():
    """The ``_clone_canonical`` function's ``branch`` default kwarg
    now resolves to ``"main"``.
    """
    import inspect

    sig = inspect.signature(new_workspace._clone_canonical)
    branch_param = sig.parameters.get("branch")
    assert branch_param is not None, (
        "AC.WBM2M.1: _clone_canonical must accept a 'branch' kwarg"
    )
    assert branch_param.default == "main", (
        f"AC.WBM2M.1: _clone_canonical's branch default should be "
        f"'main'; got {branch_param.default!r}"
    )
