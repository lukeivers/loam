"""Ruby/Rails first-class language adapter.

Per AC.RAILS.1 — implements the
:class:`~loam_odd_extractor.registry.LanguageAdapter` Protocol. The
adapter dispatches per-file to the registered Rails-idiom recognizers,
constructs :class:`~loam_odd_extractor.bands.BandedAC` instances per
AC.RAILS.6 mapping, and routes per-slice extraction through the
slice-and-swarm orchestrator (Surface #2).

Public API:

- :class:`RubyAdapter` — the adapter class. Instances are stateless
  (cached at module level for entry-point factory use).
- :func:`extract_rails_acs` — convenience function that runs the
  full extraction against a single repo path; mostly used in tests.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import TYPE_CHECKING

from ...bands import BandedAC, ConfidenceBand
from ...spec import AnalysisPlan, RawACs
from .heuristic_inferences import infer_domain_rules
from .parser import parse_file
from .recognizers import (
    recognize_active_record_models,
    recognize_callbacks,
    recognize_concerns,
    recognize_jobs,
    recognize_migrations,
    recognize_minitest_tests,
    recognize_polymorphic_associations,
    recognize_routes,
    recognize_rspec_tests,
)
from .._common.repo_sha import resolve_repo_sha

if TYPE_CHECKING:  # pragma: no cover
    pass


# Recognizers that take (tree, source, file_path, repo_root, repo_sha)
# and emit BandedACs. In display order; sorting by ac_id at aggregate
# time guarantees deterministic output regardless of iteration order.
_AST_RECOGNIZERS = (
    recognize_active_record_models,
    recognize_callbacks,
    recognize_concerns,
    recognize_jobs,
    recognize_migrations,
    recognize_minitest_tests,
    recognize_polymorphic_associations,
    recognize_routes,
    recognize_rspec_tests,
)


def _is_ruby_file(file_path: Path) -> bool:
    """Return True if a file should be parsed as Ruby."""
    if file_path.suffix == ".rb":
        return True
    # Ruby-flavoured filenames without ``.rb`` extension.
    if file_path.name in (
        "Rakefile",
        "Gemfile",
        "Gemfile.lock",
        "config.ru",
    ):
        return file_path.name not in ("Gemfile.lock",)
    if file_path.suffix in (".rake", ".gemspec"):
        return True
    return False


class RubyAdapter:
    """Ruby/Rails first-class language adapter.

    Implements :class:`~loam_odd_extractor.registry.LanguageAdapter`:

    - ``name = "ruby"``.
    - ``supports(repo)`` — True when ``repo/Gemfile`` exists OR any
      ``.rb`` file is found at the repo root or one level deep.
    - ``extract(repo, plan)`` — runs the orchestration: walks the
      plan's slices, parses each Ruby file via tree-sitter,
      dispatches to recognizers, applies heuristic inference for
      HYPOTHESISED ACs, returns a :class:`RawACs` with all ACs as
      ``model_dump()``-d dicts.
    """

    name = "ruby"

    def supports(self, repo: Path) -> bool:
        """Cheap structural check for "is this a Ruby/Rails repo?"."""
        if not repo.exists():
            return False
        if (repo / "Gemfile").exists():
            return True
        # Single-level rb-file scan as a fallback.
        try:
            for entry in repo.iterdir():
                if entry.is_file() and _is_ruby_file(entry):
                    return True
                if entry.is_dir() and entry.name in (
                    "app", "config", "db", "lib", "spec", "test"
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
        ``self.name``. Files not in any slice (or not in this
        adapter's slices) are skipped.
        """
        repo_sha = resolve_repo_sha(repo)
        ruby_files: list[Path] = []
        for sl in plan.slices:
            if sl.adapter_name != self.name:
                continue
            for p in sl.paths:
                if _is_ruby_file(p):
                    ruby_files.append(p)

        # Stable ordering for deterministic output.
        ruby_files = sorted(set(ruby_files), key=lambda p: p.as_posix())

        plausible_acs: list[BandedAC] = []
        unhandled: list[Path] = []
        # Track parse-error files separately so the audit log can
        # surface them (the adapter writes one notes entry per
        # parse error via the per-slice cost dict).
        parse_errors: list[str] = []

        for ruby_file in ruby_files:
            try:
                tree, source = parse_file(ruby_file)
            except OSError as exc:
                unhandled.append(ruby_file)
                parse_errors.append(
                    f"{ruby_file}: read failed: {exc}"
                )
                continue

            if tree.root_node.has_error:
                # Skip files that don't parse cleanly; record as
                # unhandled so the verify stage can surface them.
                unhandled.append(ruby_file)
                parse_errors.append(
                    f"{ruby_file}: tree-sitter parse error"
                )
                continue

            for recognizer in _AST_RECOGNIZERS:
                try:
                    found = recognizer(
                        tree, source, ruby_file, repo, repo_sha
                    )
                    plausible_acs.extend(found)
                except Exception as exc:  # pragma: no cover
                    # Defensive: a recognizer crash shouldn't take
                    # down the whole extraction. The file is recorded
                    # as unhandled.
                    parse_errors.append(
                        f"{ruby_file}: recognizer "
                        f"{recognizer.__name__} crashed: {exc}"
                    )
                    if ruby_file not in unhandled:
                        unhandled.append(ruby_file)

        # HYPOTHESISED inference over PLAUSIBLE-band findings.
        hypothesised = infer_domain_rules(plausible_acs)
        all_banded = list(plausible_acs) + list(hypothesised)

        # Convert to dicts for the dict-typed RawACs.acs field.
        # Sort by ac_id for deterministic output (D2 idempotency).
        ac_dicts = sorted(
            (b.model_dump(mode="json") for b in all_banded),
            key=lambda d: d.get("ac_id", ""),
        )

        per_slice_costs = {}
        if parse_errors:
            per_slice_costs["ruby"] = {
                "parse_errors": parse_errors,
            }

        # extraction_id + created_at supplied by the caller (the
        # generate stage). We populate placeholder values that the
        # caller can replace.
        return RawACs(
            extraction_id=plan.extraction_id,
            acs=ac_dicts,
            unhandled_paths=unhandled,
            per_slice_costs=per_slice_costs,
            created_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        )


# Process-wide singleton; entry-point factory uses this to avoid
# re-instantiating the parser cache.
_SINGLETON = RubyAdapter()


def _singleton_factory() -> RubyAdapter:
    """Entry-point factory shape — returns the singleton instance.

    The pyproject entry-point declaration resolves to *this callable*;
    Cycle 1's :func:`registry.discover_adapters` calls it to obtain an
    instance. Per Surface #1 — the instance is stateless; the
    singleton avoids re-instantiating the parser cache on every
    discover call.
    """
    return _SINGLETON


def extract_rails_acs(
    *,
    repo: Path,
    files: list[Path] | None = None,
) -> RawACs:
    """Convenience function — run the adapter against ``repo``
    (using ``files`` as the file list, or auto-discovering from the
    repo). Returns the :class:`RawACs` produced by the adapter.

    Used in tests + ad-hoc invocations; production usage flows
    through the four-stage workflow + the registered adapter.
    """
    if files is None:
        files = []
        for entry in repo.rglob("*"):
            if entry.is_file() and _is_ruby_file(entry):
                files.append(entry)

    plan = AnalysisPlan(
        extraction_id=f"adhoc-{repo.name}",
        slices=[],
        unhandled_paths=[],
        created_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
    )
    # Inject a single all-files ruby slice.
    from ...spec import Slice
    plan = AnalysisPlan(
        extraction_id=plan.extraction_id,
        slices=[
            Slice(
                slice_id="ruby-root",
                adapter_name="ruby",
                paths=files,
            )
        ],
        unhandled_paths=[],
        created_at=plan.created_at,
    )
    adapter = _SINGLETON
    return adapter.extract(repo, plan)
