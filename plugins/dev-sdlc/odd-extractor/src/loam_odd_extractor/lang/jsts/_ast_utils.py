"""Shared AST-traversal helpers used by the JS/TS recognizers.

Mirror of ``lang/ruby/_ast_utils.py`` (Cycle 3) — same shape, JS/TS-
specific node types. Per Surface #2 — recognizer modules share these
helpers (DRY); each recognizer focuses on idiom-specific pattern
detection while delegating tree-walking + slug derivation here.

Per AC.DRY.{2, 4} (v0.1.8 Cycle 4b) — :func:`slugify` and
:func:`file_slug` were factored into ``loam_odd_extractor.lang._common.slugs``
(closing Cycle 4a §10 RF #6). This module retains them as a
compat-shim re-export so external callers (and any historical import
sites) continue to work; new recognizer code imports from
``.._common.slugs`` directly.
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
    """Pre-order iterator over a tree-sitter subtree."""
    yield node
    for child in node.children:
        yield from walk_nodes(child)


# ---- node-type finders -------------------------------------------


def find_call_expressions(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``call_expression`` node under ``root``.

    JS/TS uses ``call_expression`` for both `foo()` and `foo.bar()`;
    the callee can be an ``identifier`` or a ``member_expression``.
    """
    return [n for n in walk_nodes(root) if n.type == "call_expression"]


def find_function_declarations(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``function_declaration`` node under ``root``."""
    return [
        n for n in walk_nodes(root)
        if n.type == "function_declaration"
    ]


def find_class_declarations(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``class_declaration`` node under ``root``.

    JS uses both ``class`` (anonymous) and ``class_declaration``
    (named); we only collect the latter (named classes are the
    ones that produce ACs).
    """
    return [
        n for n in walk_nodes(root) if n.type == "class_declaration"
    ]


def find_method_definitions(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``method_definition`` node under ``root``."""
    return [
        n for n in walk_nodes(root) if n.type == "method_definition"
    ]


def find_interface_declarations(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``interface_declaration`` node (TS/TSX only).

    Returns empty list on JS trees (no interfaces).
    """
    return [
        n for n in walk_nodes(root)
        if n.type == "interface_declaration"
    ]


def find_type_alias_declarations(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``type_alias_declaration`` node (TS/TSX only)."""
    return [
        n for n in walk_nodes(root)
        if n.type == "type_alias_declaration"
    ]


def find_export_statements(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``export_statement`` node under ``root``."""
    return [
        n for n in walk_nodes(root) if n.type == "export_statement"
    ]


def find_import_statements(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``import_statement`` node under ``root``.

    ESM-only — CommonJS ``require()`` calls show as
    ``call_expression`` and are detected via :func:`find_call_expressions`.
    """
    return [
        n for n in walk_nodes(root) if n.type == "import_statement"
    ]


def find_decorators(
    root: "tree_sitter.Node",
) -> list["tree_sitter.Node"]:
    """Return every ``decorator`` node under ``root`` (TS/TSX only).

    Decorators apply to class fields and methods; the parent of a
    decorator is typically a ``public_field_definition`` or a
    ``method_definition``.
    """
    return [n for n in walk_nodes(root) if n.type == "decorator"]


# ---- name extractors ---------------------------------------------


def class_name(
    class_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return the class name (e.g., ``LoginPage``) or ``None``.

    Tree-sitter JS/TS represents the class name as an ``identifier``
    (JS) or ``type_identifier`` (TS) immediately after the ``class``
    keyword.
    """
    for child in class_node.children:
        if child.type in ("identifier", "type_identifier"):
            return source[child.start_byte:child.end_byte].decode(
                "utf-8", errors="replace"
            )
    return None


def class_extends(
    class_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return the heritage clause's superclass identifier or
    ``None`` if no ``extends`` clause.

    Tree-sitter exposes the heritage via the ``class_heritage``
    node; we extract the first ``identifier``/``type_identifier``
    that follows the ``extends`` keyword.
    """
    for child in class_node.children:
        if child.type == "class_heritage":
            seen_extends = False
            for sub in child.children:
                if sub.type == "extends":
                    seen_extends = True
                    continue
                if seen_extends and sub.type in (
                    "identifier", "type_identifier", "member_expression"
                ):
                    return source[
                        sub.start_byte:sub.end_byte
                    ].decode("utf-8", errors="replace")
    return None


def function_name(
    function_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return a function declaration's name."""
    for child in function_node.children:
        if child.type == "identifier":
            return source[child.start_byte:child.end_byte].decode(
                "utf-8", errors="replace"
            )
    return None


def method_name(
    method_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return a method definition's name."""
    for child in method_node.children:
        if child.type == "property_identifier":
            return source[child.start_byte:child.end_byte].decode(
                "utf-8", errors="replace"
            )
    return None


def interface_name(
    interface_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return an interface declaration's name."""
    for child in interface_node.children:
        if child.type == "type_identifier":
            return source[child.start_byte:child.end_byte].decode(
                "utf-8", errors="replace"
            )
    return None


def type_alias_name(
    type_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return a type alias declaration's name."""
    for child in type_node.children:
        if child.type == "type_identifier":
            return source[child.start_byte:child.end_byte].decode(
                "utf-8", errors="replace"
            )
    return None


# ---- call-expression helpers -------------------------------------


def call_callee_text(
    call_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return the callee text of a ``call_expression``.

    For ``foo()`` returns ``"foo"``; for ``app.get('/x')`` returns
    ``"app.get"``; for ``test.describe('...')`` returns
    ``"test.describe"``. Strips internal whitespace.
    """
    if not call_node.children:
        return None
    callee = call_node.children[0]
    if callee.type in ("identifier", "member_expression"):
        return source[callee.start_byte:callee.end_byte].decode(
            "utf-8", errors="replace"
        )
    return None


def call_callee_object(
    call_node: "tree_sitter.Node", source: bytes
) -> tuple[str | None, str | None]:
    """Split a member-expression callee into ``(object, property)``.

    For ``app.get(...)`` returns ``("app", "get")``; for ``router.post(...)``
    returns ``("router", "post")``; for non-member-expression callees
    returns ``(None, name)`` (e.g., ``test(...)`` → ``(None, "test")``).
    """
    if not call_node.children:
        return (None, None)
    callee = call_node.children[0]
    if callee.type == "identifier":
        return (
            None,
            source[callee.start_byte:callee.end_byte].decode(
                "utf-8", errors="replace"
            ),
        )
    if callee.type == "member_expression":
        # Walk the member_expression: object . property
        obj_text = None
        prop_text = None
        for child in callee.children:
            if child.type in (
                "identifier", "this", "member_expression",
            ) and obj_text is None:
                obj_text = source[
                    child.start_byte:child.end_byte
                ].decode("utf-8", errors="replace")
            elif child.type == "property_identifier":
                prop_text = source[
                    child.start_byte:child.end_byte
                ].decode("utf-8", errors="replace")
        return (obj_text, prop_text)
    return (None, None)


def call_arguments(
    call_node: "tree_sitter.Node", source: bytes
) -> list[str]:
    """Return the call's argument text strings (verbatim).

    Strips ``(`` and ``)`` and `,` separator nodes. Useful for
    extracting the route-path string from
    ``router.get('/users', ...)``.
    """
    out: list[str] = []
    for child in call_node.children:
        if child.type == "arguments":
            for arg in child.children:
                if arg.type in ("(", ")", ","):
                    continue
                out.append(
                    source[arg.start_byte:arg.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                )
    return out


def call_first_arg_string(
    call_node: "tree_sitter.Node", source: bytes
) -> str | None:
    """Return the first argument as a clean string (with quotes
    stripped), or ``None`` if no string argument.

    Useful for extracting `'/users'` from `router.get('/users', ...)`.
    Returns the literal text between the quotes (single or double).
    """
    args = call_arguments(call_node, source)
    if not args:
        return None
    first = args[0]
    # Strip surrounding quotes if present.
    if len(first) >= 2 and first[0] == first[-1] and first[0] in (
        "'", '"', "`",
    ):
        return first[1:-1]
    return first


def file_imports(
    tree: "tree_sitter.Tree", source: bytes
) -> set[str]:
    """Return the set of source-modules imported by a file.

    Covers BOTH ESM (``import ... from 'pkg'``) and CommonJS
    (``const x = require('pkg')``). Returns the package names
    (the part inside the quotes); useful for runner-identity
    detection in test files.
    """
    out: set[str] = set()
    for n in walk_nodes(tree.root_node):
        # ESM: import { x } from 'pkg';
        if n.type == "import_statement":
            for child in n.children:
                if child.type == "string":
                    text = source[
                        child.start_byte:child.end_byte
                    ].decode("utf-8", errors="replace")
                    if len(text) >= 2 and text[0] == text[-1] and text[0] in (
                        "'", '"',
                    ):
                        out.add(text[1:-1])
        # CommonJS: require('pkg')
        if n.type == "call_expression":
            obj, prop = call_callee_object(n, source)
            callee = call_callee_text(n, source)
            if callee == "require":
                first = call_first_arg_string(n, source)
                if first is not None:
                    out.add(first)
    return out


def class_field_decorators(
    class_node: "tree_sitter.Node", source: bytes
) -> list[tuple[str, str, "tree_sitter.Node"]]:
    """Return ``[(field_name, decorator_text, decorator_node), ...]``
    for fields decorated with class-validator-style decorators.

    Decorator text is verbatim (e.g., ``"@IsEmail()"``). Includes
    methods + public fields decorated.
    """
    out: list[tuple[str, str, "tree_sitter.Node"]] = []
    body = None
    for child in class_node.children:
        if child.type == "class_body":
            body = child
            break
    if body is None:
        return out

    for member in body.children:
        if member.type not in (
            "public_field_definition",
            "method_definition",
        ):
            continue
        # Collect leading decorators from siblings (decorator nodes
        # are children of class_body, immediately preceding the
        # field/method node in tree-sitter's representation).
        # Tree-sitter actually places decorators as children of
        # the public_field_definition / method_definition itself.
        decorators_here: list[tuple[str, "tree_sitter.Node"]] = []
        member_name: str | None = None
        for sub in member.children:
            if sub.type == "decorator":
                dec_text = source[
                    sub.start_byte:sub.end_byte
                ].decode("utf-8", errors="replace")
                decorators_here.append((dec_text, sub))
            elif sub.type == "property_identifier" and member_name is None:
                member_name = source[
                    sub.start_byte:sub.end_byte
                ].decode("utf-8", errors="replace")
        if member_name is None:
            continue
        for dec_text, dec_node in decorators_here:
            out.append((member_name, dec_text, dec_node))

    return out
