"""RSpec test recognizer.

Per AC.RAILS.3 — every passing RSpec test → candidate VERIFIED AC.

Detects:

- ``RSpec.describe X do ... end`` (top-level describes).
- ``describe '...' do ... end`` (nested describes).
- ``it '...' do ... end`` (the spec assertion-as-spec idiom).
- ``context '...' do ... end`` (used as a describe alias for
  describe-block hierarchy).

Each ``it`` block emits one VERIFIED BandedAC. The test is granted
VERIFIED on the assumption it passed at the resolved ``repo_sha``;
ratification is the human verification step (RF gap §10 #2).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from ..._common.slugs import file_slug
from .._ast_utils import (
    call_first_arg,
    call_method_name,
    find_calls,
)
from ..parser import node_line

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


def _is_spec_file(file_path: Path) -> bool:
    """Return True if ``file_path`` is an RSpec spec file."""
    if file_path.suffix != ".rb":
        return False
    if file_path.name.endswith("_spec.rb"):
        return True
    return "spec" in file_path.parts


def _enclosing_describe(
    it_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Walk up from an ``it`` call until we find an enclosing
    ``describe`` / ``RSpec.describe`` / ``context``; return the
    describe target text.
    """
    n = it_node.parent
    while n is not None:
        if n.type == "call":
            method = call_method_name(n, source)
            if method in ("describe", "context"):
                arg = call_first_arg(n, source)
                if arg is not None:
                    return arg
        n = n.parent
    return None


def recognize_rspec_tests(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return VERIFIED BandedACs for every ``it`` block.

    When ``repo_sha`` is None, downgrades to PLAUSIBLE per
    AC.BANDS.2 (VERIFIED requires non-null repo_sha).

    Returns ``[]`` for non-spec files.
    """
    if not _is_spec_file(file_path):
        return []

    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for call_node in find_calls(tree.root_node):
        method = call_method_name(call_node, source)
        if method != "it":
            continue
        it_text = call_first_arg(call_node, source) or "(no description)"
        # Strip surrounding quotes for cleaner display.
        it_clean = it_text.strip("'\"")
        describe = _enclosing_describe(call_node, source) or "(root)"
        describe_clean = describe.strip("'\"").strip(":")
        line = node_line(call_node)

        # Slug components must be deterministic + non-empty.
        from ..._common.slugs import slugify

        ac_id = (
            f"AC.RAILS.test.rspec.{slugify(describe_clean)}."
            f"{slugify(it_clean)}.{fslug}"
        )

        if repo_sha is None:
            # Downgrade per AC.BANDS.2 — VERIFIED requires repo_sha.
            out.append(
                BandedAC(
                    ac_id=ac_id,
                    text=(
                        f"RSpec — {describe_clean}: {it_clean}"
                    ),
                    confidence=ConfidenceBand.PLAUSIBLE,
                    evidence=Evidence(
                        kind="source",
                        citations=[
                            f"{file_rel}:{line}:rspec:"
                            f"{describe_clean}#{it_clean}"
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
                        f"RSpec — {describe_clean}: {it_clean}"
                    ),
                    confidence=ConfidenceBand.VERIFIED,
                    evidence=Evidence(
                        kind="test",
                        citations=[
                            f"{file_rel}:{line}:rspec:"
                            f"{describe_clean}#{it_clean}"
                        ],
                        repo_sha=repo_sha,
                    ),
                    backing_files=[file_rel],
                )
            )

    return out
