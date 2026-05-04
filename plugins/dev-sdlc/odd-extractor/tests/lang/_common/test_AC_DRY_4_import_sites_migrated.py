"""AC.DRY.4 (v0.1.8 Cycle 4b) — recognizer import sites migrated to
``.._common.slugs`` (NOT via the ``_ast_utils`` compat shim).

Cycle 4b's plan-doc decision: every recognizer module that imports
``slugify`` or ``file_slug`` does so from
``..._common.slugs`` directly. The compat shim at
``lang/{ruby,jsts}/_ast_utils.py`` re-exports those names for
external/historical callers but is NOT used by the canonical
recognizer code.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import loam_odd_extractor


_PKG_ROOT = Path(loam_odd_extractor.__file__).parent
_RECOGNIZER_GLOBS = [
    _PKG_ROOT / "lang" / "ruby" / "recognizers",
    _PKG_ROOT / "lang" / "jsts" / "recognizers",
]

# Pattern that catches ANY ``slugify``/``file_slug`` import sourced
# from ``.._ast_utils``. Recognizers are 2 levels deep so the
# canonical relative-import depth is ``...`` (three dots), not
# ``..``.
_AST_UTILS_SLUG_IMPORT_RE = re.compile(
    r"from\s+\.\._ast_utils\s+import\b[^\n]*\b(slugify|file_slug)\b"
)
_COMMON_SLUGS_IMPORT_RE = re.compile(
    r"from\s+\.\.\._common\.slugs\s+import\b[^\n]*\b(slugify|file_slug)\b"
)


def _collect_recognizer_files() -> list[Path]:
    """All recognizer modules across both adapters (excluding
    __init__.py).
    """
    files: list[Path] = []
    for d in _RECOGNIZER_GLOBS:
        if d.is_dir():
            files.extend(
                p for p in d.glob("*.py") if p.name != "__init__.py"
            )
    return files


def test_recognizer_files_exist() -> None:
    files = _collect_recognizer_files()
    assert len(files) > 0, (
        f"No recognizer files found at {_RECOGNIZER_GLOBS}"
    )


@pytest.mark.parametrize(
    "recognizer_file", _collect_recognizer_files(), ids=lambda p: p.name,
)
def test_recognizer_does_not_import_slugify_from_ast_utils(
    recognizer_file: Path,
) -> None:
    """No recognizer imports ``slugify`` or ``file_slug`` from the
    ``_ast_utils`` compat shim — canonical path is
    ``..._common.slugs``.
    """
    text = recognizer_file.read_text()
    matches = _AST_UTILS_SLUG_IMPORT_RE.findall(text)
    assert not matches, (
        f"{recognizer_file.name} still imports {matches} from "
        f".._ast_utils (compat shim); should import from "
        f"..._common.slugs (canonical) per AC.DRY.4"
    )


def test_recognizers_imports_from_common_slugs_count_matches() -> None:
    """Every recognizer that needs ``slugify``/``file_slug`` imports
    them from ``..._common.slugs``. Sanity-check: count the migrated
    imports across all recognizer files.
    """
    files = _collect_recognizer_files()
    files_with_common_import = sum(
        1
        for f in files
        if _COMMON_SLUGS_IMPORT_RE.search(f.read_text())
    )
    # Cycle 4b verified at plan-author: 17 recognizer files migrated
    # across both adapters. Floor here is generous (≥10) to allow
    # future cycles to add/remove recognizers without breaking this
    # test.
    assert files_with_common_import >= 10, (
        f"Only {files_with_common_import} recognizer files import "
        f"from ..._common.slugs; expected ≥10 per AC.DRY.4"
    )
