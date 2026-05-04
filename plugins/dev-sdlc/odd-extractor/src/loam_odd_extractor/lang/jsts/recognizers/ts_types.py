"""TypeScript types/interfaces recognizer.

Per AC.JSTS.2 — detects:

- ``interface X { ... }`` declarations.
- ``type X = ...`` type aliases.

Each type/interface emits one PLAUSIBLE-band :class:`BandedAC` per
AC.JSTS.5. Skipped on JS/MJS/CJS/JSX files (no TS types in JS).

Note: tree-sitter-typescript exposes BOTH a TypeScript grammar and
a TSX grammar; this recognizer is invoked on either grammar's tree
since both surface ``interface_declaration`` + ``type_alias_declaration``
node types.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from ..._common.slugs import file_slug, slugify
from .._ast_utils import (
    find_interface_declarations,
    find_type_alias_declarations,
    interface_name,
    type_alias_name,
)
from ..parser import node_line

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


def recognize_ts_types(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for every interface + type alias.

    Returns ``[]`` for JS files (no TS types). The recognizer's
    detection is grammar-driven: TS/TSX trees contain
    ``interface_declaration`` / ``type_alias_declaration`` nodes;
    JS trees do not.
    """
    if file_path.suffix.lower() not in (".ts", ".tsx"):
        return []

    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for interface_node in find_interface_declarations(tree.root_node):
        iname = interface_name(interface_node, source)
        if iname is None:
            continue
        line = node_line(interface_node)
        out.append(
            BandedAC(
                ac_id=(
                    f"AC.JSTS.ts_interface.{slugify(iname)}.{fslug}"
                ),
                text=(
                    f"TypeScript interface: {iname}"
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

    for type_node in find_type_alias_declarations(tree.root_node):
        tname = type_alias_name(type_node, source)
        if tname is None:
            continue
        line = node_line(type_node)
        out.append(
            BandedAC(
                ac_id=(
                    f"AC.JSTS.ts_type.{slugify(tname)}.{fslug}"
                ),
                text=(
                    f"TypeScript type alias: {tname}"
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
