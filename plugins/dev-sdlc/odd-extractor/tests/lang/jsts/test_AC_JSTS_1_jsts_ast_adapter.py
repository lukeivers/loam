"""AC.JSTS.1 — JS/TS AST adapter via tree-sitter (multi-grammar).

Verifies:

- :class:`JsTsAdapter` is :class:`LanguageAdapter`-Protocol-compliant
  via the registry's ``_validate_adapter`` (manual).
- ``supports()`` returns True for ``package.json``-bearing fixtures,
  False for empty dirs.
- Multi-grammar parser routes ``.js/.mjs/.cjs/.jsx`` → JS,
  ``.ts`` → TypeScript, ``.tsx`` → TSX.
- Both ESM (``import``/``export``) and CommonJS (``require``/
  ``module.exports``) parse without error.
- Entry-point factory returns a working singleton instance.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor.lang.jsts import JsTsAdapter
from loam_odd_extractor.lang.jsts.adapter import _singleton_factory
from loam_odd_extractor.lang.jsts.parser import (
    GrammarKind,
    grammar_for_path,
    get_parser,
    parse_file,
    parse_source,
)
from loam_odd_extractor.registry import _validate_adapter


def test_adapter_protocol_compliant() -> None:
    adapter = JsTsAdapter()
    # Should not raise.
    _validate_adapter(adapter)
    assert adapter.name == "jsts"


def test_supports_package_json(jsts_playwright_app_repo: Path) -> None:
    adapter = JsTsAdapter()
    assert adapter.supports(jsts_playwright_app_repo)


def test_supports_empty_dir_false(tmp_path: Path) -> None:
    adapter = JsTsAdapter()
    assert not adapter.supports(tmp_path)


def test_supports_nonexistent_path_false(tmp_path: Path) -> None:
    adapter = JsTsAdapter()
    assert not adapter.supports(tmp_path / "does-not-exist")


def test_grammar_routing() -> None:
    """Per Surface #1 — extension → grammar routing table."""
    cases: list[tuple[str, GrammarKind]] = [
        ("foo.js", "javascript"),
        ("foo.mjs", "javascript"),
        ("foo.cjs", "javascript"),
        ("foo.jsx", "javascript"),
        ("foo.ts", "typescript"),
        ("foo.tsx", "tsx"),
    ]
    for name, expected in cases:
        kind = grammar_for_path(Path(name))
        assert kind == expected, f"{name} → {kind} (expected {expected})"

    # Unrecognized → None.
    assert grammar_for_path(Path("foo.py")) is None
    assert grammar_for_path(Path("foo.rb")) is None
    assert grammar_for_path(Path("foo.html")) is None


def test_parser_loads_each_grammar() -> None:
    """All three grammars must load + return a parser instance."""
    for kind in ("javascript", "typescript", "tsx"):
        parser = get_parser(kind)
        assert parser is not None


def test_parse_esm_javascript() -> None:
    """ESM JS file parses cleanly (per AC.JSTS.1)."""
    src = b"import { foo } from './bar.js';\nexport const x = 1;"
    tree = parse_source(src, "javascript")
    assert not tree.root_node.has_error


def test_parse_commonjs_javascript() -> None:
    """CommonJS JS file parses cleanly (per AC.JSTS.1)."""
    src = (
        b"const express = require('express');\n"
        b"module.exports = { x: 1 };"
    )
    tree = parse_source(src, "javascript")
    assert not tree.root_node.has_error


def test_parse_typescript() -> None:
    """TS file parses cleanly via typescript grammar."""
    src = (
        b"interface User { email: string }\n"
        b"export const x: number = 1;\n"
        b"function foo<T>(): T { return null as any; }"
    )
    tree = parse_source(src, "typescript")
    assert not tree.root_node.has_error


def test_parse_tsx() -> None:
    """TSX file parses cleanly via tsx grammar."""
    src = (
        b"export const App = () => <div>hello</div>;\n"
        b"interface Props { name: string }"
    )
    tree = parse_source(src, "tsx")
    assert not tree.root_node.has_error


def test_parse_file_routes_by_extension(tmp_path: Path) -> None:
    """parse_file picks the right grammar from the file extension."""
    js_file = tmp_path / "x.js"
    js_file.write_text("const x = 1;")
    _tree, _src, kind = parse_file(js_file)
    assert kind == "javascript"

    ts_file = tmp_path / "x.ts"
    ts_file.write_text("const x: number = 1;")
    _tree, _src, kind = parse_file(ts_file)
    assert kind == "typescript"

    tsx_file = tmp_path / "x.tsx"
    tsx_file.write_text("const x = <div />;")
    _tree, _src, kind = parse_file(tsx_file)
    assert kind == "tsx"


def test_parse_file_unrecognized_extension_raises(
    tmp_path: Path,
) -> None:
    not_jsts = tmp_path / "x.py"
    not_jsts.write_text("x = 1")
    with pytest.raises(ValueError):
        parse_file(not_jsts)


def test_singleton_factory_returns_adapter() -> None:
    instance = _singleton_factory()
    assert isinstance(instance, JsTsAdapter)
    # Same instance on repeated calls.
    assert _singleton_factory() is instance


def test_extract_against_fixture_round_trips(
    jsts_playwright_app_repo: Path,
) -> None:
    """End-to-end: extract from fixture; result has no errors and
    every dict in :attr:`RawACs.acs` round-trips through
    :meth:`BandedAC.model_validate`.
    """
    from loam_odd_extractor.bands import BandedAC
    from loam_odd_extractor.lang.jsts import extract_jsts_acs

    result = extract_jsts_acs(repo=jsts_playwright_app_repo)
    assert len(result.acs) > 0, "fixture should produce at least one AC"
    for ac_dict in result.acs:
        # Round-trips cleanly.
        BandedAC.model_validate(ac_dict)
