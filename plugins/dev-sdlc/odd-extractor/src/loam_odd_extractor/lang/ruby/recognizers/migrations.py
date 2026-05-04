"""Migration-file recognizer.

Per AC.RAILS.2 — detects schema operations inside ``db/migrate/*.rb``
files: ``create_table``, ``add_column``, ``add_index``,
``add_foreign_key``, ``add_reference :X, :Y, polymorphic: true``.

Migrations are file-pattern-based (caller filters to ``db/migrate/``);
the recognizer parses the file via tree-sitter + walks the call
nodes inside the ``def change`` / ``def up`` / ``def down`` method
bodies.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from .._ast_utils import (
    call_first_arg,
    call_has_keyword_arg,
    call_method_name,
    file_slug,
    find_calls,
)
from ..parser import node_line, node_text

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


_SCHEMA_OPS = frozenset(
    {
        "create_table",
        "drop_table",
        "rename_table",
        "add_column",
        "remove_column",
        "rename_column",
        "change_column",
        "add_index",
        "remove_index",
        "add_foreign_key",
        "remove_foreign_key",
        "add_reference",
        "remove_reference",
        "add_belongs_to",
    }
)


def is_migration_file(file_path: Path) -> bool:
    """Return True if ``file_path`` lives under a ``db/migrate/``
    directory.
    """
    parts = file_path.parts
    for i, p in enumerate(parts):
        if p == "db" and i + 1 < len(parts) and parts[i + 1] == "migrate":
            return True
    return False


def recognize_migrations(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for every schema operation in a
    migration file.

    Returns ``[]`` for files that aren't migrations (allows callers
    to apply this recognizer uniformly across all .rb files; the
    file-path check is the gate).
    """
    if not is_migration_file(file_path):
        return []

    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for call_node in find_calls(tree.root_node):
        method = call_method_name(call_node, source)
        if method not in _SCHEMA_OPS:
            continue
        target = call_first_arg(call_node, source) or "?"
        # Detect polymorphic references for cross-recognizer
        # corroboration.
        is_poly = (
            method in ("add_reference", "add_belongs_to")
            and call_has_keyword_arg(call_node, source, "polymorphic")
        )

        line = node_line(call_node)
        suffix = ".polymorphic" if is_poly else ""
        text_suffix = " (polymorphic)" if is_poly else ""
        out.append(
            BandedAC(
                ac_id=(
                    f"AC.RAILS.migrations.{method}.{target.strip(':')}"
                    f"{suffix}.{fslug}"
                ),
                text=(
                    f"Migration {file_path.name}: {method} "
                    f"{target}{text_suffix}"
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
