"""JavaScript / TypeScript / Playwright first-class language adapter
(v0.1.8 Cycle 4a).

Per AC.JSTS.{1..5} + AC.FIXTURES.{1, 3-jsts} — second adapter under
the ``loam.odd_extractor.language_adapters`` entry-point group.
Handles BOTH JavaScript (ESM + CommonJS) and TypeScript (with TSX
variant) source files via tree-sitter; understands Express routes,
Playwright tests + page objects, TypeScript types/interfaces, Zod
+ class-validator schemas, Jest/Mocha/Vitest test runners, and
plain HTML/JS file-level surface.

Public API:

- :class:`JsTsAdapter` — the adapter class; ``LanguageAdapter``
  Protocol-compliant.
- :func:`extract_jsts_acs` — convenience function for tests.
"""

from __future__ import annotations

from .adapter import JsTsAdapter, _singleton_factory, extract_jsts_acs

__all__ = [
    "JsTsAdapter",
    "_singleton_factory",
    "extract_jsts_acs",
]
