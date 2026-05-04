"""Shared AST-traversal helpers used by the recognizers.

Per Surface #1 — recognizer modules share these helpers (DRY); each
recognizer focuses on idiom-specific pattern detection while
delegating tree-walking + slug derivation here.

Per AC.DRY.{2, 4} (v0.1.8 Cycle 4b) — :func:`slugify` and
:func:`file_slug` were factored into ``loam_odd_extractor.lang._common.slugs``.
This module retains them as a compat-shim re-export so external
callers (and any historical import sites) continue to work; new
recognizer code imports from ``.._common.slugs`` directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

# Compat-shim re-export per AC.DRY.{2, 4} — canonical home is
# loam_odd_extractor.lang._common.slugs.
from .._common.slugs import file_slug, slugify  # noqa: F401

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


def walk_nodes(
    node: "tree_sitter.Node",
) -> Iterator["tree_sitter.Node"]:
    """Pre-order iterator over a tree-sitter subtree.

    Tree-sitter does not ship a built-in walker (the ``cursor`` API
    is verbose); this helper is the standard pre-order walk.
    """
    yield node
    for child in node.children:
        yield from walk_nodes(child)


def find_classes(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``class ...`` node under ``root``."""
    return [n for n in walk_nodes(root) if n.type == "class"]


def find_modules(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``module ...`` node under ``root``."""
    return [n for n in walk_nodes(root) if n.type == "module"]


def find_calls(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every method-call node under ``root``."""
    # Tree-sitter Ruby uses node type "call" for method dispatches.
    return [n for n in walk_nodes(root) if n.type == "call"]


def class_name(class_node: "tree_sitter.Node", source: bytes) -> str | None:
    """Return the class name (e.g., ``Payment``) or ``None`` if
    unparseable.

    Searches the class node's children for the identifier-like child
    that follows the ``class`` keyword.
    """
    for child in class_node.children:
        if child.type == "constant":
            return source[child.start_byte:child.end_byte].decode(
                "utf-8", errors="replace"
            )
    return None


def module_name(
    module_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return the module name; mirror of :func:`class_name`."""
    for child in module_node.children:
        if child.type == "constant":
            return source[child.start_byte:child.end_byte].decode(
                "utf-8", errors="replace"
            )
    return None


def superclass_name(
    class_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return the superclass name (e.g., ``ApplicationRecord``) or
    ``None`` if the class has no explicit superclass.

    Handles both ``class X < Y`` (constant superclass) and
    ``class X < A::B`` (scoped constant via ``scope_resolution``).
    """
    for child in class_node.children:
        if child.type == "superclass":
            for sub in child.children:
                if sub.type in ("constant", "scope_resolution"):
                    return source[sub.start_byte:sub.end_byte].decode(
                        "utf-8", errors="replace"
                    )
    return None


def call_method_name(
    call_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return the method-name identifier of a call node, or ``None``.

    A call node's first child is typically the ``identifier`` (e.g.,
    ``before_save``, ``validates``, ``include``). Method calls with
    explicit receivers (``foo.bar``) put the method as the
    ``method`` field; we surface both via tree walk.
    """
    for child in call_node.children:
        if child.type == "identifier":
            return source[child.start_byte:child.end_byte].decode(
                "utf-8", errors="replace"
            )
    # Try the method field for receiver-style calls.
    method_field = call_node.child_by_field_name("method")
    if method_field is not None:
        return source[
            method_field.start_byte:method_field.end_byte
        ].decode("utf-8", errors="replace")
    return None


def call_first_arg(
    call_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return the first argument's text (e.g., the ``:foo`` symbol
    in ``before_save :foo``) or ``None`` if no arguments.

    Returns the text verbatim (including leading colon for symbols).
    """
    for child in call_node.children:
        if child.type == "argument_list":
            for arg in child.children:
                if arg.type in (
                    "simple_symbol",
                    "string",
                    "string_array",
                    "constant",
                    "identifier",
                    "instance_variable",
                ):
                    return source[arg.start_byte:arg.end_byte].decode(
                        "utf-8", errors="replace"
                    )
    return None


def call_has_keyword_arg(
    call_node: "tree_sitter.Node", source: bytes, keyword: str
) -> bool:
    """Return True if the call has a ``keyword: true`` keyword arg.

    Detects ``foo :bar, polymorphic: true`` (the common Rails idiom
    for polymorphic associations + create_table options).
    """
    for child in call_node.children:
        if child.type != "argument_list":
            continue
        for arg in child.children:
            if arg.type != "pair":
                continue
            # A pair has the shape: (hash_key_symbol, ":", value)
            for sub in arg.children:
                if sub.type == "hash_key_symbol":
                    text = source[
                        sub.start_byte:sub.end_byte
                    ].decode("utf-8", errors="replace")
                    if text == keyword:
                        # Now check the corresponding value.
                        # Tree-sitter Ruby pair: hash_key_symbol, then
                        # ":" delimiter, then a value node.
                        idx = arg.children.index(sub)
                        for value in arg.children[idx + 1:]:
                            if value.type == "true":
                                return True
                            if value.type in ("false", "nil"):
                                return False
                        return False
    return False


def call_keyword_arg_value(
    call_node: "tree_sitter.Node", source: bytes, keyword: str
) -> str | None:
    """Return the literal text of a ``keyword: <value>`` keyword arg
    or ``None`` if not present.
    """
    for child in call_node.children:
        if child.type != "argument_list":
            continue
        for arg in child.children:
            if arg.type != "pair":
                continue
            for sub in arg.children:
                if sub.type == "hash_key_symbol":
                    text = source[
                        sub.start_byte:sub.end_byte
                    ].decode("utf-8", errors="replace")
                    if text == keyword:
                        idx = arg.children.index(sub)
                        for value in arg.children[idx + 1:]:
                            if value.type == ":":
                                continue
                            return source[
                                value.start_byte:value.end_byte
                            ].decode("utf-8", errors="replace")
    return None
