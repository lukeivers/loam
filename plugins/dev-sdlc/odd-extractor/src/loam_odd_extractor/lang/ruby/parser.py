"""Tree-sitter wrapper for Ruby parsing.

Per AC.RAILS.1 — deterministic AST parsing via the tree-sitter
ecosystem. Per Surface #8 — tree-sitter is a required dependency
declared in the odd-extractor's pyproject; the import is **lazy** at
first parse-call so ``import loam_odd_extractor`` does not pull
tree-sitter into memory unnecessarily.

Public API:

- :func:`parse_file(path)` — parse a Ruby file; return a
  :class:`tree_sitter.Tree`. On parse error returns the tree anyway
  (with ``tree.root_node.has_error == True``); the caller decides
  whether to skip or process partial results.
- :func:`get_parser()` — return the (cached) tree-sitter parser
  instance bound to the Ruby grammar.
- :func:`node_text(node, source)` — utility to extract a node's
  source text as a Python str (decoded UTF-8).

Note: tree-sitter's ``Tree.root_node`` is keyed to the source bytes
that produced it; recognizers need both the tree AND the raw source
bytes to extract text. :func:`parse_file` returns ``(tree, source)``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover — type-only imports
    import tree_sitter


_PARSER = None


def get_parser() -> "tree_sitter.Parser":
    """Return the cached tree-sitter Ruby parser.

    Lazy-imports tree-sitter on first call. Raises
    :class:`ImportError` with a guidance message if either
    ``tree_sitter`` or ``tree_sitter_ruby`` is missing.
    """
    global _PARSER
    if _PARSER is not None:
        return _PARSER
    try:
        import tree_sitter
        import tree_sitter_ruby
    except ImportError as exc:  # pragma: no cover — defensive
        raise ImportError(
            "loam_odd_extractor.lang.ruby requires tree-sitter and "
            "tree-sitter-ruby; install them via `pip install "
            "tree-sitter tree-sitter-ruby` or via the loam-odd-"
            "extractor[ruby] extra"
        ) from exc

    language = tree_sitter.Language(tree_sitter_ruby.language())
    _PARSER = tree_sitter.Parser(language)
    return _PARSER


def parse_file(
    path: Path,
) -> tuple["tree_sitter.Tree", bytes]:
    """Parse a Ruby file; return ``(tree, source_bytes)``.

    Reads bytes (not text) so byte-offsets returned by tree-sitter
    line up exactly with the raw source. A file that fails to read
    raises :class:`OSError` (uncaught — caller handles).

    A file that parses with errors returns the partial tree anyway;
    ``tree.root_node.has_error`` is True. Recognizers in this cycle
    skip files where ``has_error == True`` and emit a ``parse_error``
    audit-log entry via the adapter.
    """
    parser = get_parser()
    src = path.read_bytes()
    tree = parser.parse(src)
    return tree, src


def parse_source(
    source: bytes,
) -> "tree_sitter.Tree":
    """Parse Ruby source bytes; return the tree.

    Mirror of :func:`parse_file` for in-memory snippets (test use).
    """
    parser = get_parser()
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
