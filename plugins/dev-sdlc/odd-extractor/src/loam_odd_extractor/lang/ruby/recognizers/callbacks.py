"""Rails-callback recognizer.

Per AC.RAILS.2 — detects the full Rails ActiveRecord callback set
(before_save, after_create, etc.) inside ActiveRecord-model classes.
Each callback declaration emits one PLAUSIBLE BandedAC.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from ..._common.slugs import file_slug
from .._ast_utils import (
    call_first_arg,
    call_method_name,
    class_name,
    find_calls,
    find_classes,
    superclass_name,
)
from ..parser import node_line

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


# Rails ActiveRecord callback list (Rails 7 docs); per AC.RAILS.2
# table.
_RAILS_CALLBACKS = frozenset(
    {
        "before_validation",
        "after_validation",
        "before_save",
        "around_save",
        "after_save",
        "before_create",
        "around_create",
        "after_create",
        "before_update",
        "around_update",
        "after_update",
        "before_destroy",
        "around_destroy",
        "after_destroy",
        "after_commit",
        "after_rollback",
        "after_initialize",
        "after_find",
        "after_touch",
    }
)

_AR_SUPERCLASSES = ("ApplicationRecord", "ActiveRecord::Base")


def recognize_callbacks(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for every callback declaration."""
    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for class_node in find_classes(tree.root_node):
        sup = superclass_name(class_node, source)
        # Only fire on ActiveRecord-model classes; controller-level
        # callbacks (before_action etc.) are a different recognizer
        # surface (deferred per RF gap §10 #3).
        if sup not in _AR_SUPERCLASSES:
            continue
        cname = class_name(class_node, source)
        if cname is None:
            continue

        for call_node in find_calls(class_node):
            method = call_method_name(call_node, source)
            if method not in _RAILS_CALLBACKS:
                continue
            target = call_first_arg(call_node, source) or "(block)"
            cline = node_line(call_node)
            out.append(
                BandedAC(
                    ac_id=(
                        f"AC.RAILS.callbacks.{cname.lower()}."
                        f"{method}.{target.strip(':')}.{fslug}"
                    ),
                    text=(
                        f"{cname} has {method} {target}"
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

    return out
