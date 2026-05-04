"""JavaScript / TypeScript / Playwright idiom recognizers
(v0.1.8 Cycle 4a).

Per AC.JSTS.2 — eight idioms recognized; each lives in its own
module under this package. Per AC.JSTS.3 — Playwright + Jest +
Mocha + Vitest recognizers emit VERIFIED-band ACs; the rest emit
PLAUSIBLE.

Public API:

- ``ALL_RECOGNIZERS`` — list of recognizer callables the adapter
  iterates. Each callable accepts ``(tree, source, file_path,
  repo_root, repo_sha)`` and returns ``list[BandedAC]``. The
  ``plain_html_js`` recognizer is file-only (no AST input) and is
  invoked separately by the adapter for HTML files.
- The eight idiom recognizers as named submodules.

Per Surface #2 — per-JS/TS/Playwright-idiom file split. Each
recognizer has a matching test file at
``tests/lang/jsts/test_AC_JSTS_<n>_<slug>.py``.
"""

from __future__ import annotations

from .class_validator import recognize_class_validator
from .express_routes import recognize_express_routes
from .plain_html_js import recognize_plain_html_js
from .playwright_page_objects import recognize_playwright_page_objects
from .playwright_tests import recognize_playwright_tests
from .test_runners import recognize_test_runners
from .ts_types import recognize_ts_types
from .zod_schemas import recognize_zod_schemas

__all__ = [
    "recognize_class_validator",
    "recognize_express_routes",
    "recognize_plain_html_js",
    "recognize_playwright_page_objects",
    "recognize_playwright_tests",
    "recognize_test_runners",
    "recognize_ts_types",
    "recognize_zod_schemas",
]
