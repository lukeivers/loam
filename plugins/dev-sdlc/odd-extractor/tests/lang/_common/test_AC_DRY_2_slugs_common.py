"""AC.DRY.2 (v0.1.8 Cycle 4b) — ``_common/slugs.py`` exposes the
canonical ``slugify`` + ``file_slug`` helpers.

Pre-4b these were duplicated byte-identical at
``lang/ruby/_ast_utils.py`` and ``lang/jsts/_ast_utils.py``; Cycle
4b consolidated them. The per-adapter ``_ast_utils`` modules retain
a compat-shim re-export (verified here via identity comparison).
"""

from __future__ import annotations

from pathlib import Path


def test_common_slugs_module_importable() -> None:
    """``loam_odd_extractor.lang._common.slugs`` is importable."""
    from loam_odd_extractor.lang._common.slugs import (  # noqa: F401
        file_slug,
        slugify,
    )


def test_slugify_basic_cases() -> None:
    """Frozen regression-pin against pre-4b behaviour."""
    from loam_odd_extractor.lang._common.slugs import slugify

    assert slugify("Hello World") == "hello_world"
    assert slugify("FooBar123") == "foobar123"
    assert slugify("a.b.c") == "a_b_c"
    assert slugify("___MULTIPLE___underscores") == "multiple_underscores"
    assert slugify("") == ""
    assert slugify("only-symbols-!@#") == "only_symbols"


def test_file_slug_relative_path() -> None:
    """``file_slug`` derives a relative-path-shaped slug."""
    from loam_odd_extractor.lang._common.slugs import file_slug

    repo_root = Path("/repo")
    file_path = Path("/repo/app/models/payment.rb")
    assert file_slug(file_path, repo_root) == "app_models_payment_rb"


def test_ruby_ast_utils_re_exports_canonical_slugify() -> None:
    """The compat shim at ``lang/ruby/_ast_utils.slugify`` is THE
    SAME OBJECT as ``lang/_common/slugs.slugify`` (re-export
    identity).
    """
    from loam_odd_extractor.lang._common.slugs import (
        file_slug as common_file_slug,
        slugify as common_slugify,
    )
    from loam_odd_extractor.lang.ruby._ast_utils import (
        file_slug as ruby_file_slug,
        slugify as ruby_slugify,
    )

    assert ruby_slugify is common_slugify, (
        "lang/ruby/_ast_utils.slugify is not the canonical "
        "lang/_common.slugs.slugify"
    )
    assert ruby_file_slug is common_file_slug


def test_jsts_ast_utils_re_exports_canonical_slugify() -> None:
    """The compat shim at ``lang/jsts/_ast_utils.slugify`` is THE
    SAME OBJECT as ``lang/_common/slugs.slugify``.
    """
    from loam_odd_extractor.lang._common.slugs import (
        file_slug as common_file_slug,
        slugify as common_slugify,
    )
    from loam_odd_extractor.lang.jsts._ast_utils import (
        file_slug as jsts_file_slug,
        slugify as jsts_slugify,
    )

    assert jsts_slugify is common_slugify
    assert jsts_file_slug is common_file_slug
