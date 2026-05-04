"""Minitest test recognizer.

Per AC.RAILS.3 — every passing Minitest test → candidate VERIFIED AC.

Detects:

- ``test '...' do ... end`` (Rails ActiveSupport::TestCase idiom).
- ``def test_<name>`` (raw Minitest::Test method-naming idiom).

Each test method emits one VERIFIED BandedAC; downgrades to
PLAUSIBLE when ``repo_sha`` is None per AC.BANDS.2.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from ..._common.slugs import file_slug, slugify
from .._ast_utils import (
    call_first_arg,
    call_method_name,
    find_calls,
    walk_nodes,
)
from ..parser import node_line, node_text

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


def _is_test_file(file_path: Path) -> bool:
    """Return True if ``file_path`` is a Minitest test file (under
    ``test/`` directory or ending with ``_test.rb``).
    """
    if file_path.suffix != ".rb":
        return False
    if file_path.name.endswith("_test.rb"):
        return True
    return "test" in file_path.parts


def _make_ac(
    *,
    ac_id: str,
    text: str,
    file_rel: str,
    line: int,
    citation: str,
    repo_sha: str | None,
) -> BandedAC:
    """Construct a VERIFIED BandedAC, downgrading to PLAUSIBLE when
    ``repo_sha`` is None.
    """
    if repo_sha is None:
        return BandedAC(
            ac_id=ac_id,
            text=text,
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(
                kind="source",
                citations=[citation],
                repo_sha=None,
            ),
            backing_files=[file_rel],
        )
    return BandedAC(
        ac_id=ac_id,
        text=text,
        confidence=ConfidenceBand.VERIFIED,
        evidence=Evidence(
            kind="test",
            citations=[citation],
            repo_sha=repo_sha,
        ),
        backing_files=[file_rel],
    )


def recognize_minitest_tests(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return VERIFIED BandedACs for every Minitest test."""
    if not _is_test_file(file_path):
        return []

    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    # ``test '...' do`` form — surfaces as a method call.
    for call_node in find_calls(tree.root_node):
        method = call_method_name(call_node, source)
        if method != "test":
            continue
        # The test() method takes a string description.
        first_arg = call_first_arg(call_node, source)
        if first_arg is None:
            continue
        # Heuristic: treat ``test`` calls in ``.rb`` files under
        # ``test/`` as Minitest tests; production calls to ``test``
        # are uncommon outside Rails-test contexts.
        clean = first_arg.strip("'\"")
        line = node_line(call_node)
        ac_id = f"AC.RAILS.test.minitest.test.{slugify(clean)}.{fslug}"
        text = f"Minitest — test '{clean}'"
        citation = (
            f"{file_rel}:{line}:minitest:test:{clean}"
        )
        out.append(
            _make_ac(
                ac_id=ac_id,
                text=text,
                file_rel=file_rel,
                line=line,
                citation=citation,
                repo_sha=repo_sha,
            )
        )

    # ``def test_<name>`` form — surfaces as a method def with a
    # name starting with ``test_``.
    for node in walk_nodes(tree.root_node):
        if node.type != "method":
            continue
        # The first identifier child is the method name.
        for child in node.children:
            if child.type == "identifier":
                name = node_text(child, source)
                if not name.startswith("test_"):
                    break
                line = node_line(node)
                ac_id = (
                    f"AC.RAILS.test.minitest.def.{slugify(name)}.{fslug}"
                )
                text = f"Minitest — def {name}"
                citation = (
                    f"{file_rel}:{line}:minitest:def:{name}"
                )
                out.append(
                    _make_ac(
                        ac_id=ac_id,
                        text=text,
                        file_rel=file_rel,
                        line=line,
                        citation=citation,
                        repo_sha=repo_sha,
                    )
                )
                break

    return out
