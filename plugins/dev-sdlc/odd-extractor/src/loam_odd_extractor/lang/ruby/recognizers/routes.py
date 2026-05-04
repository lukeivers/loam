"""Routes-file recognizer.

Per AC.RAILS.2 — detects route declarations in ``config/routes.rb``:
``resources :foo``, ``get '/path', to: 'controller#action'``,
``namespace :api``, ``scope :v1``, ``root to: '...'``. Each
declaration emits one PLAUSIBLE BandedAC.
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


_ROUTE_VERBS = frozenset(
    {"get", "post", "put", "patch", "delete", "match", "root"}
)
_ROUTE_GROUPERS = frozenset(
    {"resources", "resource", "namespace", "scope", "constraints"}
)


def is_routes_file(file_path: Path) -> bool:
    """Return True if ``file_path`` is ``config/routes.rb``."""
    parts = file_path.parts
    if file_path.name != "routes.rb":
        return False
    return "config" in parts


def recognize_routes(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for every route declaration.

    Returns ``[]`` for files that aren't ``config/routes.rb``.
    """
    if not is_routes_file(file_path):
        return []

    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for call_node in find_calls(tree.root_node):
        method = call_method_name(call_node, source)
        if method not in _ROUTE_VERBS and method not in _ROUTE_GROUPERS:
            continue

        target = call_first_arg(call_node, source) or "(root)"
        line = node_line(call_node)
        category = (
            "verb" if method in _ROUTE_VERBS else "grouper"
        )
        out.append(
            BandedAC(
                ac_id=(
                    f"AC.RAILS.routes.{method}.{target.strip(':').strip(chr(39))}."
                    f"line_{line}.{fslug}"
                ),
                text=(
                    f"Route {category}: {method} {target}"
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
