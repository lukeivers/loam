"""Playwright page-object recognizer.

Per AC.JSTS.2 — detects classes encapsulating page interactions.

Detection signals:

- File path under ``src/playwright/`` (or matching common page-object
  filename patterns: ``*-page.ts``, ``*Page.ts``, ``*.page.ts``).
- Class declaration whose method bodies contain at least one
  ``page.locator(...)``, ``page.goto(...)``, or ``page.<x>(...)``
  call.

Each page-object class emits one PLAUSIBLE-band :class:`BandedAC`
naming the class; each navigable action method (a method whose body
contains a ``page.locator/goto`` call) emits an additional PLAUSIBLE
AC. The auth-related-method heuristic (``login*``, ``signIn*``,
``signUp*``) is consumed by :mod:`heuristic_inferences`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from ..._common.slugs import file_slug, slugify
from .._ast_utils import (
    call_callee_object,
    class_name,
    find_call_expressions,
    find_class_declarations,
    find_method_definitions,
    method_name,
)
from ..parser import node_line

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


def _is_page_object_file(file_path: Path) -> bool:
    """Return True if ``file_path`` looks like a page-object
    location.
    """
    parts = file_path.parts
    if "playwright" in parts:
        return True
    name = file_path.stem
    if name.endswith("-page") or name.endswith("Page"):
        return True
    if name.endswith(".page"):
        return True
    return False


def _has_page_call(
    method_node: "tree_sitter.Node", source: bytes
) -> bool:
    """Return True if any descendant call_expression has a callee
    of the form ``X.page.<method>(...)`` or ``page.<method>(...)``
    or ``this.page.<method>(...)``.
    """
    for call_node in find_call_expressions(method_node):
        obj, _prop = call_callee_object(call_node, source)
        if obj is None:
            continue
        # Case: page.locator(), page.goto()
        if obj == "page":
            return True
        # Case: this.page.locator() — obj is the full `this.page`
        # member-expression text.
        if obj.endswith(".page") or obj.endswith("page"):
            return True
    return False


def recognize_playwright_page_objects(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for every page-object class +
    each of its navigable action methods.

    Returns ``[]`` for non-page-object files.
    """
    if not _is_page_object_file(file_path):
        return []

    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for class_node in find_class_declarations(tree.root_node):
        cname = class_name(class_node, source)
        if cname is None:
            continue

        # Verify at least one method body has a `page.<x>` call.
        methods_with_page: list[tuple[str, "tree_sitter.Node"]] = []
        for method in find_method_definitions(class_node):
            if _has_page_call(method, source):
                mname = method_name(method, source)
                if mname is not None:
                    methods_with_page.append((mname, method))

        if not methods_with_page:
            # Class doesn't use `page.*` — not a page object.
            continue

        cline = node_line(class_node)
        out.append(
            BandedAC(
                ac_id=(
                    f"AC.JSTS.playwright_page.{slugify(cname)}.{fslug}"
                ),
                text=(
                    f"Playwright page object: {cname} "
                    f"(encapsulates page interactions)"
                ),
                confidence=ConfidenceBand.PLAUSIBLE,
                evidence=Evidence(
                    kind="source",
                    citations=[f"{file_rel}:{cline}"],
                    repo_sha=repo_sha,
                ),
                backing_files=[file_rel],
            )
        )

        for mname, mnode in methods_with_page:
            mline = node_line(mnode)
            out.append(
                BandedAC(
                    ac_id=(
                        f"AC.JSTS.playwright_page.{slugify(cname)}."
                        f"{slugify(mname)}.{fslug}"
                    ),
                    text=(
                        f"{cname}#{mname}: page-interaction method"
                    ),
                    confidence=ConfidenceBand.PLAUSIBLE,
                    evidence=Evidence(
                        kind="source",
                        citations=[f"{file_rel}:{mline}"],
                        repo_sha=repo_sha,
                    ),
                    backing_files=[file_rel],
                )
            )

    return out
