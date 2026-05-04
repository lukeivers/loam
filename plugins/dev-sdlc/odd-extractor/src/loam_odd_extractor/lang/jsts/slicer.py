"""Slice-and-swarm orchestration for the JS/TS/Playwright adapter.

Per AC.JSTS.4 — when a codebase exceeds the budget envelope, the
slicer partitions JS/TS files by JS/TS-domain (one slice per
``src/playwright/`` cluster, one per ``src/routes/``, etc.); the
aggregator merges per-slice :class:`RawACs` into a deterministic
single payload.

Per Surface #4 — slicing strategy is per-JS/TS-domain. Per Cycle 3
Surface #9 — aggregator sorts merged ACs lexicographically by
``ac_id`` for D2 idempotency. Per Surface #4 + RF §10 #6 — the
aggregator and ``SliceDriftError`` are reused from
``lang/ruby/slicer.py`` to keep DRY tight without coupling
slicing-strategy semantics across languages.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable

# Reuse SliceDriftError + aggregate_slice_results from Ruby's slicer
# per RF §10 #6. The drift-detection contract is language-agnostic;
# the slicing-strategy (which is language-specific) lives below.
from ..ruby.slicer import (  # noqa: F401  (re-exported)
    SliceDriftError,
    aggregate_slice_results,
)
from ...spec import Slice


def _categorize_file(file_path: Path) -> str:
    """Return the slice-domain for a JS/TS file.

    Categories:

    - ``playwright`` — under ``src/playwright/`` or
      ``tests/playwright/`` (page objects + Playwright specs).
    - ``routes`` — under ``src/routes/`` (Express routes).
    - ``controllers`` — under ``src/controllers/``.
    - ``middleware`` — under ``src/middleware/``.
    - ``schemas`` — under ``src/schemas/`` (Zod / class-validator).
    - ``unit_tests`` — under ``tests/unit/`` or matching
      ``*.test.[jt]s``.
    - ``html`` — under ``public/`` (plain HTML/JS surface).
    - ``src_root`` — under ``src/`` (catch-all per module).
    - ``other`` — everything else.
    """
    parts = file_path.parts
    name = file_path.name

    # Playwright (specs + page objects).
    if "playwright" in parts or "e2e" in parts:
        return "playwright"

    # Routes / controllers / middleware / schemas — Express-y
    # backend partitioning.
    if "src" in parts:
        idx = parts.index("src")
        if idx + 1 < len(parts):
            sub = parts[idx + 1]
            if sub == "routes":
                return "routes"
            if sub == "controllers":
                return "controllers"
            if sub == "middleware":
                return "middleware"
            if sub == "schemas":
                return "schemas"

    # Unit tests by location or filename.
    if "tests" in parts and "unit" in parts:
        return "unit_tests"
    if "__tests__" in parts:
        return "unit_tests"
    if (
        name.endswith(".test.js")
        or name.endswith(".test.ts")
        or name.endswith(".test.tsx")
        or name.endswith(".test.jsx")
        or name.endswith(".test.mjs")
        or name.endswith(".spec.js")
        or name.endswith(".spec.ts")
        or name.endswith(".spec.tsx")
        or name.endswith(".spec.jsx")
        or name.endswith(".spec.mjs")
    ):
        return "unit_tests"

    # Plain HTML/JS public dir.
    if "public" in parts or "static" in parts:
        return "html"

    # src/ catch-all.
    if "src" in parts:
        return "src_root"

    return "other"


def slice_repo(
    *,
    files: Iterable[Path],
    estimate_money_cents: int,
    budget_hard_cap_cents: int,
) -> list[Slice]:
    """Return the slice plan for a JS/TS repo.

    When ``estimate_money_cents <= budget_hard_cap_cents``, returns
    a single all-files slice (``adapter_name='jsts'``). Otherwise
    partitions by JS/TS-domain.
    """
    files_list = sorted(files, key=lambda p: p.as_posix())

    # Single-slice fast path.
    if estimate_money_cents <= budget_hard_cap_cents:
        return [
            Slice(
                slice_id="jsts-root",
                adapter_name="jsts",
                paths=files_list,
            )
        ]

    by_domain: dict[str, list[Path]] = defaultdict(list)
    for f in files_list:
        by_domain[_categorize_file(f)].append(f)

    out: list[Slice] = []
    for domain in sorted(by_domain):
        domain_files = by_domain[domain]
        out.append(
            Slice(
                slice_id=f"jsts-{domain}",
                adapter_name="jsts",
                paths=domain_files,
            )
        )
    return out
