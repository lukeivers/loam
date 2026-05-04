"""Slice-and-swarm orchestration for the Ruby/Rails adapter.

Per AC.RAILS.4 — when a codebase exceeds the budget envelope, the
slicer partitions Ruby files by Rails-idiom domain (one slice per
``app/models/`` cluster, one per ``db/migrate/`` cohort, etc.); the
aggregator merges per-slice :class:`RawACs` into a deterministic
single payload.

Per Surface #2 — slicing strategy is per-Rails-idiom-domain. Per
Surface #9 — aggregator sorts merged ACs lexicographically by
``ac_id`` for D2 idempotency. Per Surface #1 — slicing logic is a
pure function of repo state + budget; no global state.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable

from ...errors import OddExtractorError
from ...spec import RawACs, Slice


# Migration cohort chunk size (Surface #2).
_MIGRATION_CHUNK = 25


class SliceDriftError(OddExtractorError):
    """Raised when the aggregator detects >50% duplicate ``ac_id``s
    across slices.

    Per AC.RAILS.4 + Lens 5 ``needs_fresh_start`` analog — drift
    between slices indicates the slicing strategy is producing
    incoherent shards. The adapter halts; the dispatcher decides
    whether to re-run with adjusted slicing or surface to the user.
    """


def _slice_id_for(domain: str, suffix: str) -> str:
    """Construct a stable slice id."""
    if not suffix:
        return f"ruby-{domain}"
    return f"ruby-{domain}-{suffix}"


def _categorize_file(file_path: Path) -> str:
    """Return the slice-domain for a Ruby file.

    Categories:
    - ``models`` — under ``app/models/`` (excluding concerns).
    - ``concerns`` — under ``app/models/concerns/`` or
      ``app/controllers/concerns/``.
    - ``migrations`` — under ``db/migrate/``.
    - ``jobs`` — under ``app/jobs/`` or ``app/workers/``.
    - ``controllers`` — under ``app/controllers/``.
    - ``routes`` — ``config/routes.rb`` exactly.
    - ``specs`` — under ``spec/`` or ending in ``_spec.rb``.
    - ``tests`` — under ``test/`` or ending in ``_test.rb``.
    - ``other`` — everything else.
    """
    parts = file_path.parts
    name = file_path.name

    # routes.rb is solo.
    if name == "routes.rb" and "config" in parts:
        return "routes"

    # Concerns under app/.../concerns/.
    if "concerns" in parts and "app" in parts:
        return "concerns"

    # Migrations.
    if "db" in parts:
        idx = parts.index("db")
        if idx + 1 < len(parts) and parts[idx + 1] == "migrate":
            return "migrations"

    # Jobs / workers.
    if "app" in parts and (
        "jobs" in parts or "workers" in parts
    ):
        return "jobs"

    # Controllers.
    if "app" in parts and "controllers" in parts:
        return "controllers"

    # Models.
    if "app" in parts and "models" in parts:
        return "models"

    # Specs / tests.
    if name.endswith("_spec.rb") or "spec" in parts:
        return "specs"
    if name.endswith("_test.rb") or "test" in parts:
        return "tests"

    return "other"


def slice_repo(
    *,
    files: Iterable[Path],
    estimate_money_cents: int,
    budget_hard_cap_cents: int,
) -> list[Slice]:
    """Return the slice plan for a repo.

    When ``estimate_money_cents <= budget_hard_cap_cents``, returns a
    single all-files slice (``adapter_name='ruby'``). Otherwise
    partitions by Rails-idiom domain; large migration cohorts split
    into chunks of ``_MIGRATION_CHUNK`` files.
    """
    files_list = sorted(files, key=lambda p: p.as_posix())

    # Single-slice fast path.
    if estimate_money_cents <= budget_hard_cap_cents:
        return [
            Slice(
                slice_id="ruby-root",
                adapter_name="ruby",
                paths=files_list,
            )
        ]

    # Multi-slice partitioning.
    by_domain: dict[str, list[Path]] = defaultdict(list)
    for f in files_list:
        by_domain[_categorize_file(f)].append(f)

    out: list[Slice] = []
    # Stable iteration order for D2 idempotency.
    for domain in sorted(by_domain):
        domain_files = by_domain[domain]
        if domain == "migrations" and len(domain_files) > _MIGRATION_CHUNK:
            # Split into chunks of N.
            for i in range(0, len(domain_files), _MIGRATION_CHUNK):
                chunk = domain_files[i:i + _MIGRATION_CHUNK]
                out.append(
                    Slice(
                        slice_id=_slice_id_for(
                            domain, f"chunk{i // _MIGRATION_CHUNK:03d}"
                        ),
                        adapter_name="ruby",
                        paths=chunk,
                    )
                )
        else:
            out.append(
                Slice(
                    slice_id=_slice_id_for(domain, ""),
                    adapter_name="ruby",
                    paths=domain_files,
                )
            )
    return out


def aggregate_slice_results(
    slice_results: list[RawACs],
    *,
    drift_threshold: float = 0.5,
) -> tuple[RawACs, list[dict]]:
    """Merge per-slice :class:`RawACs` into a single aggregated payload.

    Returns ``(aggregated, dedup_log)`` where ``dedup_log`` is a list
    of dicts ``{"ac_id": ..., "occurrences": N}`` for any AC IDs
    that appeared in more than one slice.

    Behaviour:
    - Concatenates ``acs`` lists; deduplicates by ``ac_id`` (last-
      write-wins); sorts the merged list lexicographically by
      ``ac_id``.
    - Concatenates ``unhandled_paths``; deduplicates by stringified
      path; sorts lexicographically.
    - Merges ``per_slice_costs`` dicts (slice IDs are unique by
      construction).
    - Raises :class:`SliceDriftError` when the duplicate-ratio
      exceeds ``drift_threshold`` (i.e., >50% of merged ACs were
      duplicates across slices, signalling shard drift).
    """
    if not slice_results:
        return (
            RawACs(
                extraction_id="aggregate",
                acs=[],
                unhandled_paths=[],
                per_slice_costs={},
                created_at="",
            ),
            [],
        )

    # Use the first slice's extraction_id + created_at as the
    # aggregate's identity (callers can override).
    extraction_id = slice_results[0].extraction_id
    created_at = slice_results[0].created_at

    by_ac_id: dict[str, dict] = {}
    occurrences: dict[str, int] = defaultdict(int)
    total_emitted = 0
    unhandled_set: set[str] = set()
    per_slice_costs: dict[str, dict] = {}

    for slice_raw in slice_results:
        per_slice_costs.update(slice_raw.per_slice_costs)
        for ac in slice_raw.acs:
            ac_id = (
                ac.get("ac_id") if isinstance(ac, dict) else None
            )
            if ac_id is None:
                continue  # malformed, skip silently
            occurrences[ac_id] += 1
            total_emitted += 1
            by_ac_id[ac_id] = ac
        for p in slice_raw.unhandled_paths:
            unhandled_set.add(str(p))

    duplicates = sum(1 for k, v in occurrences.items() if v > 1)
    if total_emitted > 0:
        duplicate_ratio = duplicates / max(len(occurrences), 1)
    else:
        duplicate_ratio = 0.0
    if duplicate_ratio > drift_threshold:
        raise SliceDriftError(
            f"slice_drift: duplicate_ratio={duplicate_ratio:.2%} "
            f"exceeds threshold {drift_threshold:.0%} "
            f"(duplicates={duplicates} / unique_acs="
            f"{len(occurrences)}). Slicing strategy is producing "
            f"incoherent shards; restart with adjusted slicing per "
            f"feedback_swarming_recursive_decomposition F3 needs_"
            f"fresh_start pattern."
        )

    sorted_acs = [by_ac_id[k] for k in sorted(by_ac_id)]
    sorted_unhandled = [Path(p) for p in sorted(unhandled_set)]

    dedup_log = [
        {"ac_id": k, "occurrences": v}
        for k, v in sorted(occurrences.items())
        if v > 1
    ]

    return (
        RawACs(
            extraction_id=extraction_id,
            acs=sorted_acs,
            unhandled_paths=sorted_unhandled,
            per_slice_costs=per_slice_costs,
            created_at=created_at,
        ),
        dedup_log,
    )
