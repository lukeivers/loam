"""Multi-grammar tree-sitter wrapper for JavaScript + TypeScript.

Per AC.JSTS.1 — deterministic AST parsing for BOTH JavaScript and
TypeScript via the tree-sitter ecosystem. Per Surface #1 — file-to-
grammar routing is by extension:

- ``.js``, ``.mjs``, ``.cjs``, ``.jsx`` → ``tree-sitter-javascript``
  (the JS grammar accepts JSX natively).
- ``.ts``                               → ``tree-sitter-typescript``
                                          ``language_typescript()``.
- ``.tsx``                              → ``tree-sitter-typescript``
                                          ``language_tsx()``.

Per Surface #11 — tree-sitter is a required dependency declared in
the odd-extractor's pyproject; the import is **lazy** at first
parse-call so ``import loam_odd_extractor`` does not pull tree-sitter
into memory unnecessarily.

Public API:

- :func:`parse_file(path)` — parse a JS/TS/TSX file; return
  ``(tree, source_bytes, grammar_kind)``.
- :func:`parse_source(source, kind)` — parse in-memory bytes with
  the named grammar.
- :func:`get_parser(kind)` — return the (cached) parser instance
  bound to the named grammar.
- :func:`grammar_for_path(path)` — return the grammar kind for a
  path (extension-based).

Note: tree-sitter's ``Tree.root_node`` is keyed to the source bytes
that produced it; recognizers need both the tree AND the raw source
bytes to extract text.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:  # pragma: no cover — type-only imports
    import tree_sitter


GrammarKind = Literal["javascript", "typescript", "tsx"]


# Per-kind parser cache. Keyed by grammar kind; populated lazily on
# first parse-call for each kind. Process-wide.
_PARSER_CACHE: dict[str, "tree_sitter.Parser"] = {}


# Extension-to-grammar routing table (Surface #1). Lower-case
# extensions; tilted toward most-common first (JS) for readability.
_EXTENSION_TO_KIND: dict[str, GrammarKind] = {
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}


def grammar_for_path(path: Path) -> GrammarKind | None:
    """Return the :class:`GrammarKind` for ``path`` based on its
    extension, or ``None`` for non-JS/TS files.
    """
    return _EXTENSION_TO_KIND.get(path.suffix.lower())


def get_parser(kind: GrammarKind) -> "tree_sitter.Parser":
    """Return the cached tree-sitter parser for ``kind``.

    Lazy-imports tree-sitter + tree-sitter-javascript /
    tree-sitter-typescript on first call. Raises :class:`ImportError`
    with a guidance message if the relevant package is missing.
    """
    cached = _PARSER_CACHE.get(kind)
    if cached is not None:
        return cached
    try:
        import tree_sitter
    except ImportError as exc:  # pragma: no cover — defensive
        raise ImportError(
            "loam_odd_extractor.lang.jsts requires tree-sitter; "
            "install via `pip install tree-sitter`"
        ) from exc

    if kind == "javascript":
        try:
            import tree_sitter_javascript
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "loam_odd_extractor.lang.jsts requires "
                "tree-sitter-javascript; install via "
                "`pip install tree-sitter-javascript`"
            ) from exc
        language = tree_sitter.Language(tree_sitter_javascript.language())
    elif kind == "typescript":
        try:
            import tree_sitter_typescript
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "loam_odd_extractor.lang.jsts requires "
                "tree-sitter-typescript; install via "
                "`pip install tree-sitter-typescript`"
            ) from exc
        language = tree_sitter.Language(
            tree_sitter_typescript.language_typescript()
        )
    elif kind == "tsx":
        try:
            import tree_sitter_typescript
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "loam_odd_extractor.lang.jsts requires "
                "tree-sitter-typescript; install via "
                "`pip install tree-sitter-typescript`"
            ) from exc
        language = tree_sitter.Language(
            tree_sitter_typescript.language_tsx()
        )
    else:  # pragma: no cover — Literal exhausts the cases
        raise ValueError(f"unknown grammar kind: {kind!r}")

    parser = tree_sitter.Parser(language)
    _PARSER_CACHE[kind] = parser
    return parser


def parse_file(
    path: Path,
) -> tuple["tree_sitter.Tree", bytes, GrammarKind]:
    """Parse a JS/TS file; return ``(tree, source_bytes, kind)``.

    Routes by extension via :func:`grammar_for_path`. Reads bytes
    (not text) so byte-offsets line up exactly with the raw source.

    A file with an unknown extension raises :class:`ValueError`
    (caller should pre-filter via :func:`grammar_for_path`). A file
    that fails to read raises :class:`OSError` (uncaught — caller
    handles).

    A file that parses with errors returns the partial tree anyway;
    ``tree.root_node.has_error`` is True. Recognizers in this cycle
    skip files where ``has_error == True`` and emit a ``parse_error``
    audit-log entry via the adapter.
    """
    kind = grammar_for_path(path)
    if kind is None:
        raise ValueError(
            f"unrecognized JS/TS extension: {path.suffix!r} for "
            f"{path}"
        )
    parser = get_parser(kind)
    src = path.read_bytes()
    tree = parser.parse(src)
    return tree, src, kind


def parse_source(
    source: bytes,
    kind: GrammarKind = "javascript",
) -> "tree_sitter.Tree":
    """Parse JS/TS source bytes; return the tree.

    Mirror of :func:`parse_file` for in-memory snippets (test use).
    Defaults to JS grammar; pass ``kind="typescript"`` or ``"tsx"``
    explicitly for TS code.
    """
    parser = get_parser(kind)
    return parser.parse(source)


def node_text(node: "tree_sitter.Node", source: bytes) -> str:
    """Decode a node's source slice to UTF-8 str.

    Tree-sitter exposes ``node.text`` as bytes; this helper handles
    the decode + the rare malformed-UTF-8 case (replace with U+FFFD).
    """
    return source[node.start_byte:node.end_byte].decode(
        "utf-8", errors="replace"
    )


def node_line(node: "tree_sitter.Node") -> int:
    """Return the 1-indexed start line of a node."""
    return node.start_point[0] + 1
