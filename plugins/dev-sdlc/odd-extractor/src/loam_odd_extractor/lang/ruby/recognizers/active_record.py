"""ActiveRecord-model recognizer.

Per AC.RAILS.2 — detects ``class X < ApplicationRecord`` and
``class X < ActiveRecord::Base`` declarations + per-model
``validates`` / ``has_many`` / ``has_one`` / ``belongs_to`` calls.
Each model + each association/validation emits a PLAUSIBLE-band
:class:`BandedAC`.
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


_AR_SUPERCLASSES = ("ApplicationRecord", "ActiveRecord::Base")
_AR_ASSOCIATION_CALLS = frozenset(
    {"has_many", "has_one", "belongs_to", "has_and_belongs_to_many"}
)
_AR_VALIDATION_CALLS = frozenset(
    {"validates", "validate", "validates_presence_of",
     "validates_uniqueness_of", "validates_format_of",
     "validates_length_of", "validates_inclusion_of",
     "validates_numericality_of"}
)


def recognize_active_record_models(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for every ActiveRecord model + its
    associations/validations.
    """
    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)

    for class_node in find_classes(tree.root_node):
        sup = superclass_name(class_node, source)
        if sup not in _AR_SUPERCLASSES:
            continue
        cname = class_name(class_node, source)
        if cname is None:
            continue
        cline = node_line(class_node)
        cslug = f"AC.RAILS.active_record.{cname.lower()}.{fslug}"
        try:
            file_rel = file_path.relative_to(repo_root).as_posix()
        except ValueError:
            file_rel = str(file_path)
        out.append(
            BandedAC(
                ac_id=cslug,
                text=(
                    f"{cname} is an ActiveRecord model "
                    f"(extends {sup})"
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

        for call_node in find_calls(class_node):
            method = call_method_name(call_node, source)
            if method is None:
                continue
            if method in _AR_ASSOCIATION_CALLS:
                target = call_first_arg(call_node, source) or "?"
                aline = node_line(call_node)
                out.append(
                    BandedAC(
                        ac_id=(
                            f"AC.RAILS.active_record.{cname.lower()}."
                            f"{method}.{target.strip(':')}.{fslug}"
                        ),
                        text=(
                            f"{cname} declares {method} {target}"
                        ),
                        confidence=ConfidenceBand.PLAUSIBLE,
                        evidence=Evidence(
                            kind="source",
                            citations=[f"{file_rel}:{aline}"],
                            repo_sha=repo_sha,
                        ),
                        backing_files=[file_rel],
                    )
                )
            elif method in _AR_VALIDATION_CALLS:
                target = call_first_arg(call_node, source) or "?"
                vline = node_line(call_node)
                out.append(
                    BandedAC(
                        ac_id=(
                            f"AC.RAILS.active_record.{cname.lower()}."
                            f"{method}.{target.strip(':')}.{fslug}"
                        ),
                        text=(
                            f"{cname} declares {method} {target}"
                        ),
                        confidence=ConfidenceBand.PLAUSIBLE,
                        evidence=Evidence(
                            kind="source",
                            citations=[f"{file_rel}:{vline}"],
                            repo_sha=repo_sha,
                        ),
                        backing_files=[file_rel],
                    )
                )

    return out
