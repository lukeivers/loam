"""AC.RAILS.1 — Ruby AST adapter via tree-sitter.

Verifies:

- :class:`RubyAdapter` implements the
  :class:`~loam_odd_extractor.registry.LanguageAdapter` Protocol.
- ``supports()`` returns True for Gemfile-bearing repos; False
  otherwise.
- ``parse_file()`` round-trips a Ruby snippet (no parse errors).
- The adapter is discoverable via the
  ``loam.odd_extractor.language_adapters`` entry-point group.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor.lang.ruby import RubyAdapter
from loam_odd_extractor.lang.ruby.parser import (
    get_parser,
    parse_file,
    parse_source,
)
from loam_odd_extractor.registry import (
    LanguageAdapter,
    _validate_adapter,
    discover_adapters,
)


def test_ruby_adapter_validates_as_language_adapter() -> None:
    """RubyAdapter satisfies the LanguageAdapter Protocol."""
    adapter = RubyAdapter()
    # Both runtime-checkable Protocol + explicit validator must
    # accept the adapter.
    assert isinstance(adapter, LanguageAdapter)
    _validate_adapter(adapter)
    assert adapter.name == "ruby"


def test_supports_true_for_gemfile_repo(
    synthetic_rails_repo: Path,
) -> None:
    """Gemfile-bearing repo → supports() True."""
    adapter = RubyAdapter()
    assert adapter.supports(synthetic_rails_repo) is True


def test_supports_false_for_empty_dir(tmp_path: Path) -> None:
    """No Gemfile + no .rb files → supports() False."""
    empty = tmp_path / "empty"
    empty.mkdir()
    adapter = RubyAdapter()
    assert adapter.supports(empty) is False


def test_supports_false_for_missing_dir(tmp_path: Path) -> None:
    """Non-existent path → supports() False."""
    adapter = RubyAdapter()
    assert adapter.supports(tmp_path / "missing") is False


def test_parse_source_roundtrip() -> None:
    """parse_source() returns a tree with no errors for valid Ruby."""
    src = b"class Foo; def bar; end; end\n"
    tree = parse_source(src)
    assert tree.root_node.type == "program"
    assert tree.root_node.has_error is False


def test_parse_file_returns_tree_and_source(tmp_path: Path) -> None:
    """parse_file() returns (tree, source) with matching byte content."""
    rb = tmp_path / "x.rb"
    rb.write_text("class A; end\n", encoding="utf-8")
    tree, src = parse_file(rb)
    assert tree.root_node.type == "program"
    assert tree.root_node.has_error is False
    assert src == b"class A; end\n"


def test_get_parser_caches() -> None:
    """get_parser() returns the same instance across calls."""
    p1 = get_parser()
    p2 = get_parser()
    assert p1 is p2


def test_ruby_adapter_in_entry_point_discovery() -> None:
    """The Ruby adapter is wired via entry-points in the canonical
    pos-v2 install.

    Per AC.RAILS.1 — the pyproject's entry-point declaration
    ``ruby = "loam_odd_extractor.lang.ruby:RubyAdapter"`` registers
    the class as the factory; ``discover_adapters()`` resolves it
    (Cycle 1's registry handles the callable-factory shape).
    """
    found = discover_adapters()
    names = [a.name for a in found]
    assert "ruby" in names, (
        "RubyAdapter not discovered via entry-points; check pyproject "
        "[project.entry-points.\"loam.odd_extractor.language_adapters\"] "
        "declaration"
    )


def test_parse_error_returns_partial_tree(tmp_path: Path) -> None:
    """A file with bad Ruby syntax still returns a tree (with errors)."""
    bad = tmp_path / "bad.rb"
    # ``class X` (unclosed) — tree-sitter will mark errors.
    bad.write_text("class X\n", encoding="utf-8")
    tree, src = parse_file(bad)
    # Tree-sitter is forgiving — it produces a tree even for partials,
    # marking has_error or returning a structure with errors.
    assert tree.root_node is not None
    # Adapter behaviour is to mark such files as unhandled; that's
    # exercised in test_AC_RAILS_8_synthetic_snippets.py.
