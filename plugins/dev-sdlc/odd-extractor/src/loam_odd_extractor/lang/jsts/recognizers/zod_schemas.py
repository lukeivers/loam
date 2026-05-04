"""Zod-schema recognizer.

Per AC.JSTS.2 + Surface #5 — detects Zod schema constructions:

- Top-level ``z.object({ ... })`` calls (the primary schema
  constructor).
- Field-level ``z.string()``, ``z.number()``, ``z.boolean()``,
  ``z.array()``, ``z.enum()``, ``z.date()`` calls.

Each top-level ``z.object({...})`` call emits one PLAUSIBLE-band
:class:`BandedAC` naming the schema (derived from the assignment
target — e.g., ``userSchema = z.object(...)`` → AC names ``user``).
Each field-level constructor inside the object's pair list emits
one PLAUSIBLE AC per field (capturing the field name + Zod
constructor for downstream heuristic inference).

Recognized in both TS and JS files.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from .._ast_utils import (
    call_callee_object,
    call_callee_text,
    file_slug,
    find_call_expressions,
    slugify,
    walk_nodes,
)
from ..parser import node_line, node_text

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


_ZOD_TOP_CONSTRUCTORS = frozenset(
    {"object", "array", "union", "intersection", "discriminatedUnion"}
)


def _schema_name_from_assignment(
    call_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Walk up from a ``z.object(...)`` call to find the binding
    name (e.g., ``userSchema`` in ``const userSchema = z.object(...)``).
    """
    n = call_node.parent
    while n is not None:
        if n.type == "variable_declarator":
            for sub in n.children:
                if sub.type == "identifier":
                    return source[
                        sub.start_byte:sub.end_byte
                    ].decode("utf-8", errors="replace")
            return None
        n = n.parent
    return None


def _object_pair_fields(
    call_node: "tree_sitter.Node", source: bytes
) -> list[tuple[str, str, "tree_sitter.Node"]]:
    """For a ``z.object({ field: z.string()...})`` call, return
    ``[(field_name, zod_chain_text, field_node), ...]``.

    Walks the first argument (an ``object`` literal) and for each
    ``pair`` extracts the property identifier + the Zod chain
    expression text.
    """
    out: list[tuple[str, str, "tree_sitter.Node"]] = []
    args_node: "tree_sitter.Node | None" = None
    for child in call_node.children:
        if child.type == "arguments":
            args_node = child
            break
    if args_node is None:
        return out

    obj_node: "tree_sitter.Node | None" = None
    for child in args_node.children:
        if child.type == "object":
            obj_node = child
            break
    if obj_node is None:
        return out

    for member in obj_node.children:
        if member.type != "pair":
            continue
        prop_name: str | None = None
        value_text: str | None = None
        value_node: "tree_sitter.Node | None" = None
        seen_colon = False
        for sub in member.children:
            if sub.type == "property_identifier" and prop_name is None:
                prop_name = source[
                    sub.start_byte:sub.end_byte
                ].decode("utf-8", errors="replace")
            elif sub.type == ":":
                seen_colon = True
            elif seen_colon and value_text is None:
                value_text = source[
                    sub.start_byte:sub.end_byte
                ].decode("utf-8", errors="replace")
                value_node = sub
        if prop_name is not None and value_text is not None and value_node is not None:
            out.append((prop_name, value_text, value_node))
    return out


def recognize_zod_schemas(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for every Zod schema + each of its
    fields.

    Detection: ``z.<top_constructor>(...)`` where ``top_constructor``
    is one of ``object``, ``array``, ``union``, ``intersection``,
    ``discriminatedUnion``. Field-level extraction happens for
    ``z.object(...)``-style calls only.
    """
    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    seen: set[str] = set()

    for call_node in find_call_expressions(tree.root_node):
        obj, prop = call_callee_object(call_node, source)
        if obj != "z" or prop is None:
            continue
        if prop not in _ZOD_TOP_CONSTRUCTORS:
            continue

        line = node_line(call_node)
        # Schema name from binding; fallback to file slug + line.
        schema_name = _schema_name_from_assignment(call_node, source)
        if schema_name is None:
            schema_name = f"anonymous_{line}"

        ac_id = (
            f"AC.JSTS.zod.{slugify(schema_name)}.{fslug}"
        )
        if ac_id in seen:
            continue
        seen.add(ac_id)

        out.append(
            BandedAC(
                ac_id=ac_id,
                text=(
                    f"Zod schema: {schema_name} (z.{prop}(...))"
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

        # Field-level extraction (only for z.object).
        if prop != "object":
            continue
        for field_name, value_text, value_node in _object_pair_fields(
            call_node, source
        ):
            field_line = node_line(value_node)
            field_ac_id = (
                f"AC.JSTS.zod.{slugify(schema_name)}."
                f"{slugify(field_name)}.{fslug}"
            )
            # Truncate the chain text for readability.
            chain_preview = value_text.replace("\n", " ")[:80]
            out.append(
                BandedAC(
                    ac_id=field_ac_id,
                    text=(
                        f"Zod {schema_name}.{field_name}: "
                        f"{chain_preview}"
                    ),
                    confidence=ConfidenceBand.PLAUSIBLE,
                    evidence=Evidence(
                        kind="source",
                        citations=[f"{file_rel}:{field_line}"],
                        repo_sha=repo_sha,
                    ),
                    backing_files=[file_rel],
                )
            )

    return out
