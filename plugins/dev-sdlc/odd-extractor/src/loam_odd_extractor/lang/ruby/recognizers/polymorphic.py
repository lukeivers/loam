"""Polymorphic-association recognizer.

Per AC.RAILS.2 — detects ``belongs_to :owner, polymorphic: true``
on the model side. Migration-side polymorphic references
(``add_reference :payments, :owner, polymorphic: true``) are picked
up by :mod:`migrations` (file-pattern recognizer over ``db/migrate/``).
Each polymorphic association emits one PLAUSIBLE BandedAC.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from ..._common.slugs import file_slug
from .._ast_utils import (
    call_first_arg,
    call_has_keyword_arg,
    call_method_name,
    class_name,
    find_calls,
    find_classes,
)
from ..parser import node_line

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


def recognize_polymorphic_associations(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for polymorphic association
    declarations on the model side.
    """
    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for class_node in find_classes(tree.root_node):
        cname = class_name(class_node, source)
        if cname is None:
            continue
        for call_node in find_calls(class_node):
            method = call_method_name(call_node, source)
            if method != "belongs_to":
                continue
            if not call_has_keyword_arg(call_node, source, "polymorphic"):
                continue
            target = call_first_arg(call_node, source) or "?"
            line = node_line(call_node)
            out.append(
                BandedAC(
                    ac_id=(
                        f"AC.RAILS.polymorphic.{cname.lower()}."
                        f"{target.strip(':')}.{fslug}"
                    ),
                    text=(
                        f"{cname} has polymorphic belongs_to "
                        f"{target}"
                    ),
                    confidence=ConfidenceBand.PLAUSIBLE,
                    evidence=Evidence(
                        kind="source",
                        citations=[f"{file_rel}:{line}"],
                        repo_sha=repo_sha,
                    ),
                    backing_files=[file_rel],
                )
            )

    return out
