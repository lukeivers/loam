"""Jest / Mocha / Vitest test-runner recognizer.

Per AC.JSTS.2 + AC.JSTS.3 + Surface #6 — detects test calls in
Jest/Mocha/Vitest test files:

- ``describe('...', () => { ... })`` (test grouping).
- ``it('...', () => { ... })`` (individual assertion-as-spec).
- ``test('...', () => { ... })`` (Jest/Vitest alias for ``it``).

Each ``it(...)`` / ``test(...)`` block emits one VERIFIED-band
:class:`BandedAC` per AC.JSTS.5. The enclosing ``describe(...)``
provides context.

Per Surface #6 — runner identity (Jest vs Mocha vs Vitest) is
detected by the file's import statements (or absence thereof for
Jest globals); recorded in the citation string.

Excluded: files importing from ``@playwright/test`` — those are
handled by :mod:`playwright_tests`. The disjointness avoids
double-counting a Playwright spec.

VERIFIED requires non-null ``repo_sha`` per AC.BANDS.2; when
``repo_sha`` is None, the recognizer downgrades to PLAUSIBLE.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from .._ast_utils import (
    call_callee_object,
    call_first_arg_string,
    file_imports,
    file_slug,
    find_call_expressions,
    slugify,
)
from ..parser import node_line

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


def _detect_runner(
    tree: "tree_sitter.Tree", source: bytes, file_path: Path
) -> str | None:
    """Identify the test runner for ``file_path``.

    Returns one of ``"jest"``, ``"mocha"``, ``"vitest"``,
    ``"unknown"``, or ``None`` (file is not a test file or is a
    Playwright file).
    """
    imports = file_imports(tree, source)
    if "@playwright/test" in imports:
        return None  # handled by playwright_tests recognizer

    # Filename heuristic: must look like a test file.
    name = file_path.name
    parts = file_path.parts
    is_test_file = (
        "tests" in parts
        or "__tests__" in parts
        or name.endswith(".test.js")
        or name.endswith(".test.ts")
        or name.endswith(".test.jsx")
        or name.endswith(".test.tsx")
        or name.endswith(".spec.js")
        or name.endswith(".spec.ts")
        or name.endswith(".spec.jsx")
        or name.endswith(".spec.tsx")
        or name.endswith(".test.mjs")
        or name.endswith(".spec.mjs")
    )
    if not is_test_file:
        return None

    if "vitest" in imports:
        return "vitest"
    if "mocha" in imports:
        return "mocha"
    if "@jest/globals" in imports or "jest" in imports:
        return "jest"
    # No runner-specific import — assume Jest globals (Jest's most
    # common config) but record as unknown for honesty.
    return "unknown"


def _enclosing_describe(
    test_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Walk up from a test call until we find an enclosing
    ``describe(...)``; return the describe target text.
    """
    n = test_node.parent
    while n is not None:
        if n.type == "call_expression":
            obj, prop = call_callee_object(n, source)
            if obj is None and prop == "describe":
                arg = call_first_arg_string(n, source)
                if arg is not None:
                    return arg
        n = n.parent
    return None


def recognize_test_runners(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return VERIFIED BandedACs for every ``it(...)`` / ``test(...)``
    block in a Jest/Mocha/Vitest test file.

    When ``repo_sha`` is None, downgrades to PLAUSIBLE per
    AC.BANDS.2. Returns ``[]`` for non-test or Playwright files.
    """
    runner = _detect_runner(tree, source, file_path)
    if runner is None:
        return []

    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for call_node in find_call_expressions(tree.root_node):
        obj, prop = call_callee_object(call_node, source)
        if obj is not None:
            continue
        if prop not in ("it", "test"):
            continue

        test_text = call_first_arg_string(call_node, source) or "(no description)"
        describe = _enclosing_describe(call_node, source) or "(root)"
        line = node_line(call_node)

        ac_id = (
            f"AC.JSTS.test.{runner}.{slugify(describe)}."
            f"{slugify(test_text)}.{fslug}"
        )

        if repo_sha is None:
            out.append(
                BandedAC(
                    ac_id=ac_id,
                    text=(
                        f"{runner.capitalize()} — {describe}: "
                        f"{test_text}"
                    ),
                    confidence=ConfidenceBand.PLAUSIBLE,
                    evidence=Evidence(
                        kind="source",
                        citations=[
                            f"{file_rel}:{line}:{runner}:"
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
                        f"{runner.capitalize()} — {describe}: "
                        f"{test_text}"
                    ),
                    confidence=ConfidenceBand.VERIFIED,
                    evidence=Evidence(
                        kind="test",
                        citations=[
                            f"{file_rel}:{line}:{runner}:"
                            f"{describe}#{test_text}"
                        ],
                        repo_sha=repo_sha,
                    ),
                    backing_files=[file_rel],
                )
            )

    return out
