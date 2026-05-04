"""Concern-definition + concern-usage recognizer.

Per AC.RAILS.2 — detects:

- **Concern definitions** — ``module X; extend ActiveSupport::Concern;
  ...; end`` (typically under ``app/models/concerns/`` or
  ``app/controllers/concerns/``).
- **Concern usage** — ``include X`` declarations inside model /
  controller classes.

Each emits one PLAUSIBLE BandedAC.
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
    find_modules,
    module_name,
    walk_nodes,
)
from ..parser import node_line, node_text

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


def _is_active_support_concern(
    module_node: "tree_sitter.Node", source: bytes
) -> bool:
    """Return True if the module body has ``extend
    ActiveSupport::Concern``.
    """
    for call_node in find_calls(module_node):
        method = call_method_name(call_node, source)
        if method != "extend":
            continue
        # First arg must be ``ActiveSupport::Concern``. Tree-sitter
        # typically renders this as a ``scope_resolution`` node.
        for child in call_node.children:
            if child.type != "argument_list":
                continue
            for arg in child.children:
                txt = node_text(arg, source)
                if txt == "ActiveSupport::Concern":
                    return True
    return False


def recognize_concerns(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for concern definitions + usages."""
    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    # Concern definitions — at module level.
    for module_node in find_modules(tree.root_node):
        if not _is_active_support_concern(module_node, source):
            continue
        mname = module_name(module_node, source)
        if mname is None:
            continue
        mline = node_line(module_node)
        out.append(
            BandedAC(
                ac_id=(
                    f"AC.RAILS.concerns.definition."
                    f"{mname.lower()}.{fslug}"
                ),
                text=(
                    f"{mname} is an ActiveSupport::Concern (concern "
                    f"definition)"
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

    # Concern usages — ``include Foo`` inside class bodies. We only
    # surface usages with capitalised constant args (concerns are
    # named with constants); ``include Module1, Module2`` produces
    # one AC per module.
    for class_node in find_classes(tree.root_node):
        cname = class_name(class_node, source)
        if cname is None:
            continue
        for call_node in find_calls(class_node):
            method = call_method_name(call_node, source)
            if method != "include":
                continue
            # Walk the argument list — multiple constants possible.
            for child in call_node.children:
                if child.type != "argument_list":
                    continue
                for arg in child.children:
                    if arg.type != "constant":
                        continue
                    inc_name = node_text(arg, source)
                    iline = node_line(arg)
                    out.append(
                        BandedAC(
                            ac_id=(
                                f"AC.RAILS.concerns.usage."
                                f"{cname.lower()}.{inc_name.lower()}."
                                f"{fslug}"
                            ),
                            text=(
                                f"{cname} includes {inc_name} "
                                f"(concern usage)"
                            ),
                            confidence=ConfidenceBand.PLAUSIBLE,
                            evidence=Evidence(
                                kind="source",
                                citations=[f"{file_rel}:{iline}"],
                                repo_sha=repo_sha,
                            ),
                            backing_files=[file_rel],
                        )
                    )

    return out
