"""Playwright-test recognizer.

Per AC.JSTS.2 + AC.JSTS.3 — detects Playwright test calls:

- ``test('...', async ({page}) => { ... })``
- ``test.describe('...', () => { test(...) })``
- ``test.beforeEach/beforeAll/afterEach/afterAll(...)``

Each ``test(...)`` block emits one VERIFIED-band :class:`BandedAC`
(per AC.JSTS.5). The enclosing ``test.describe(...)`` provides
context. Per Surface #6 — runner-identity (Playwright) is detected
by the file's import statement (``@playwright/test``); recorded in
the citation string.

VERIFIED requires non-null ``repo_sha`` per AC.BANDS.2; when
``repo_sha`` is None, the recognizer downgrades to PLAUSIBLE.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from .._ast_utils import (
    call_callee_object,
    call_callee_text,
    call_first_arg_string,
    file_imports,
    file_slug,
    find_call_expressions,
    slugify,
)
from ..parser import node_line

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


_PLAYWRIGHT_PACKAGE = "@playwright/test"


def _is_playwright_file(
    tree: "tree_sitter.Tree", source: bytes, file_path: Path
) -> bool:
    """Return True if the file imports from ``@playwright/test``.

    Falls back to filename heuristic for files lacking explicit
    imports (e.g., module-resolution-via-config — rare).
    """
    imports = file_imports(tree, source)
    if _PLAYWRIGHT_PACKAGE in imports:
        return True
    # Filename heuristic: under tests/playwright/ or e2e/.
    parts = file_path.parts
    if "playwright" in parts or "e2e" in parts:
        return True
    return False


def _enclosing_describe(
    test_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Walk up from a ``test`` call until we find an enclosing
    ``test.describe(...)``; return the describe target text.
    """
    n = test_node.parent
    while n is not None:
        if n.type == "call_expression":
            obj, prop = call_callee_object(n, source)
            if obj == "test" and prop == "describe":
                arg = call_first_arg_string(n, source)
                if arg is not None:
                    return arg
        n = n.parent
    return None


def recognize_playwright_tests(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return VERIFIED BandedACs for every ``test(...)`` block in a
    Playwright spec file.

    When ``repo_sha`` is None, downgrades to PLAUSIBLE per
    AC.BANDS.2 (VERIFIED requires non-null repo_sha).

    Returns ``[]`` for non-Playwright files.
    """
    if not _is_playwright_file(tree, source, file_path):
        return []

    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for call_node in find_call_expressions(tree.root_node):
        obj, prop = call_callee_object(call_node, source)

        # `test(...)` — direct test call (not test.describe etc.)
        is_direct_test = obj is None and prop == "test"
        # `test.only(...)` and `test.skip(...)` are also direct tests.
        is_modifier_test = (
            obj == "test" and prop in ("only", "skip")
        )

        if not (is_direct_test or is_modifier_test):
            continue

        test_text = call_first_arg_string(call_node, source) or "(no description)"
        describe = _enclosing_describe(call_node, source) or "(root)"
        line = node_line(call_node)

        ac_id = (
            f"AC.JSTS.test.playwright.{slugify(describe)}."
            f"{slugify(test_text)}.{fslug}"
        )

        if repo_sha is None:
            out.append(
                BandedAC(
                    ac_id=ac_id,
                    text=(
                        f"Playwright — {describe}: {test_text}"
                    ),
                    confidence=ConfidenceBand.PLAUSIBLE,
                    evidence=Evidence(
                        kind="source",
                        citations=[
                            f"{file_rel}:{line}:playwright:"
                            f"{describe}#{test_text}"
                        ],
                        repo_sha=None,
                    ),
                    backing_files=[file_rel],
                )
            )
        else:
            out.append(
                BandedAC(
                    ac_id=ac_id,
                    text=(
                        f"Playwright — {describe}: {test_text}"
                    ),
                    confidence=ConfidenceBand.VERIFIED,
                    evidence=Evidence(
                        kind="test",
                        citations=[
                            f"{file_rel}:{line}:playwright:"
                            f"{describe}#{test_text}"
                        ],
                        repo_sha=repo_sha,
                    ),
                    backing_files=[file_rel],
                )
            )

    return out
