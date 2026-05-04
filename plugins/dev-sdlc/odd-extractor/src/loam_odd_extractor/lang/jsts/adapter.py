"""JavaScript / TypeScript / Playwright first-class language adapter.

Per AC.JSTS.1 — implements the
:class:`~loam_odd_extractor.registry.LanguageAdapter` Protocol. The
adapter dispatches per-file to the registered JS/TS/Playwright-idiom
recognizers, constructs :class:`~loam_odd_extractor.bands.BandedAC`
instances per AC.JSTS.5 mapping, and routes per-slice extraction
through the slice-and-swarm orchestrator (Surface #4).

Public API:

- :class:`JsTsAdapter` — the adapter class. Instances are stateless
  (cached at module level for entry-point factory use).
- :func:`extract_jsts_acs` — convenience function for tests.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import TYPE_CHECKING

from ...bands import BandedAC, ConfidenceBand
from ...spec import AnalysisPlan, RawACs, Slice
from .heuristic_inferences import infer_domain_rules
from .parser import grammar_for_path, parse_file
from .recognizers import (
    recognize_class_validator,
    recognize_express_routes,
    recognize_plain_html_js,
    recognize_playwright_page_objects,
    recognize_playwright_tests,
    recognize_test_runners,
    recognize_ts_types,
    recognize_zod_schemas,
)
from .._common.repo_sha import resolve_repo_sha

if TYPE_CHECKING:  # pragma: no cover
    pass


# AST-based recognizers: take (tree, source, file_path, repo_root,
# repo_sha) → list[BandedAC]. Order is documentational; the
# aggregator's lexicographic sort makes ordering insignificant.
_AST_RECOGNIZERS = (
    recognize_class_validator,
    recognize_express_routes,
    recognize_playwright_page_objects,
    recognize_playwright_tests,
    recognize_test_runners,
    recognize_ts_types,
    recognize_zod_schemas,
)


_JSTS_EXTENSIONS = (".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx")
_HTML_EXTENSIONS = (".html", ".htm")


def _is_jsts_source_file(file_path: Path) -> bool:
    """Return True if the file should be parsed by tree-sitter."""
    return file_path.suffix.lower() in _JSTS_EXTENSIONS


def _is_html_file(file_path: Path) -> bool:
    """Return True if the file should be handled by the plain HTML/JS
    file-level recognizer.
    """
    return file_path.suffix.lower() in _HTML_EXTENSIONS


class JsTsAdapter:
    """JavaScript / TypeScript / Playwright first-class adapter.

    Implements :class:`~loam_odd_extractor.registry.LanguageAdapter`:

    - ``name = "jsts"``.
    - ``supports(repo)`` — True when ``repo/package.json`` exists OR
      any ``.js/.mjs/.cjs/.jsx/.ts/.tsx`` file is found at the repo
      root or one level deep.
    - ``extract(repo, plan)`` — runs the orchestration: walks the
      plan's slices, parses each JS/TS file via the appropriate
      tree-sitter grammar, dispatches to recognizers, runs HTML
      file-level recognizer, applies heuristic inference for
      HYPOTHESISED ACs, returns a :class:`RawACs` with all ACs as
      ``model_dump()``-d dicts.
    """

    name = "jsts"

    def supports(self, repo: Path) -> bool:
        """Cheap structural check for "is this a JS/TS repo?"."""
        if not repo.exists():
            return False
        if (repo / "package.json").exists():
            return True
        try:
            for entry in repo.iterdir():
                if entry.is_file() and (
                    _is_jsts_source_file(entry)
                    or entry.name in (
                        "tsconfig.json",
                        "playwright.config.ts",
                        "playwright.config.js",
                        "vitest.config.ts",
                        "vitest.config.js",
                        "jest.config.js",
                        "jest.config.ts",
                    )
                ):
                    return True
                if entry.is_dir() and entry.name in (
                    "src", "tests", "__tests__", "e2e", "public",
                ):
                    return True
        except (OSError, PermissionError):
            return False
        return False

    def extract(
        self,
        repo: Path,
        plan: AnalysisPlan,
    ) -> RawACs:
        """Run the per-file recognizer dispatch + heuristic
        inference; return the aggregated :class:`RawACs`.

        ``plan`` carries the slice plan (Cycle 1's analyze stage built
        the slice list); this method consumes the slices belonging to
        ``self.name``. Files not in this adapter's slices are skipped.
        """
        repo_sha = resolve_repo_sha(repo)

        # Collect files belonging to this adapter from the plan.
        adapter_files: list[Path] = []
        for sl in plan.slices:
            if sl.adapter_name != self.name:
                continue
            for p in sl.paths:
                adapter_files.append(p)

        # Stable ordering for deterministic output.
        adapter_files = sorted(
            set(adapter_files), key=lambda p: p.as_posix()
        )

        plausible_acs: list[BandedAC] = []
        unhandled: list[Path] = []
        parse_errors: list[str] = []

        for fpath in adapter_files:
            if _is_html_file(fpath):
                # File-level recognizer; no AST.
                try:
                    found = recognize_plain_html_js(
                        fpath, repo, repo_sha
                    )
                    plausible_acs.extend(found)
                except Exception as exc:  # pragma: no cover
                    parse_errors.append(
                        f"{fpath}: plain_html_js crashed: {exc}"
                    )
                    unhandled.append(fpath)
                continue

            if not _is_jsts_source_file(fpath):
                # Not handled by jsts; safety net (shouldn't appear
                # under jsts slice given analyze.py routing).
                unhandled.append(fpath)
                continue

            kind = grammar_for_path(fpath)
            if kind is None:
                unhandled.append(fpath)
                continue

            try:
                tree, source, _kind = parse_file(fpath)
            except OSError as exc:
                unhandled.append(fpath)
                parse_errors.append(
                    f"{fpath}: read failed: {exc}"
                )
                continue
            except Exception as exc:  # pragma: no cover
                unhandled.append(fpath)
                parse_errors.append(
                    f"{fpath}: parser raised: {exc}"
                )
                continue

            if tree.root_node.has_error:
                unhandled.append(fpath)
                parse_errors.append(
                    f"{fpath}: tree-sitter parse error"
                )
                continue

            for recognizer in _AST_RECOGNIZERS:
                try:
                    found = recognizer(
                        tree, source, fpath, repo, repo_sha
                    )
                    plausible_acs.extend(found)
                except Exception as exc:  # pragma: no cover
                    parse_errors.append(
                        f"{fpath}: recognizer "
                        f"{recognizer.__name__} crashed: {exc}"
                    )
                    if fpath not in unhandled:
                        unhandled.append(fpath)

        # HYPOTHESISED inference over PLAUSIBLE-band findings.
        hypothesised = infer_domain_rules(plausible_acs)
        all_banded = list(plausible_acs) + list(hypothesised)

        # Convert to dicts, sorted by ac_id for deterministic output.
        ac_dicts = sorted(
            (b.model_dump(mode="json") for b in all_banded),
            key=lambda d: d.get("ac_id", ""),
        )

        per_slice_costs: dict[str, dict] = {}
        if parse_errors:
            per_slice_costs["jsts"] = {
                "parse_errors": parse_errors,
            }

        return RawACs(
            extraction_id=plan.extraction_id,
            acs=ac_dicts,
            unhandled_paths=unhandled,
            per_slice_costs=per_slice_costs,
            created_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        )


# Process-wide singleton.
_SINGLETON = JsTsAdapter()


def _singleton_factory() -> JsTsAdapter:
    """Entry-point factory shape — returns the singleton instance.

    The pyproject entry-point declaration resolves to *this callable*;
    Cycle 1's :func:`registry.discover_adapters` calls it to obtain
    an instance. Mirror of Ruby's :func:`_singleton_factory` (Cycle 3
    Surface #1).
    """
    return _SINGLETON


def extract_jsts_acs(
    *,
    repo: Path,
    files: list[Path] | None = None,
) -> RawACs:
    """Convenience function — run the adapter against ``repo``.

    Used in tests + ad-hoc invocations; production usage flows
    through the four-stage workflow + the registered adapter.
    """
    if files is None:
        files = []
        for entry in repo.rglob("*"):
            if not entry.is_file():
                continue
            if _is_jsts_source_file(entry) or _is_html_file(entry):
                files.append(entry)

    plan = AnalysisPlan(
        extraction_id=f"adhoc-{repo.name}",
        slices=[
            Slice(
                slice_id="jsts-root",
                adapter_name="jsts",
                paths=files,
            )
        ],
        unhandled_paths=[],
        created_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
    )
    adapter = _SINGLETON
    return adapter.extract(repo, plan)
