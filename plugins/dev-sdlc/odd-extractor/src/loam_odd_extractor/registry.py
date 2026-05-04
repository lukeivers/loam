"""Language-adapter registry.

Per AC.OREK.4 — adapters plug into the four-stage workflow's Stage 3
(generate) via a Protocol-based contract. Cycle 1 ships zero adapters;
the registry is the deliverable.

Adapters can register via two mechanisms:

1. **Manual registration** — call :func:`register_adapter`.
2. **Entry-point discovery** — declare an entry point under group
   ``loam.odd_extractor.language_adapters`` on the adapter package's
   pyproject. Cycle 3 (Ruby) and Cycle 4 (Python) register this way.

Both mechanisms validate the adapter satisfies the
:class:`LanguageAdapter` Protocol structurally before accepting it.
Validation failures raise :class:`RegistryError` (manual) or log a
warning + skip (entry-point). The skip-on-discovery-failure mirrors
the ``loam.cli.subcommands`` discovery shape (loam_cli/cli.py
``_discover_subcommand_builders``).
"""

from __future__ import annotations

import importlib.metadata
import logging
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .errors import RegistryError
from .spec import AnalysisPlan, RawACs


_LOGGER = logging.getLogger(__name__)
_ENTRYPOINT_GROUP = "loam.odd_extractor.language_adapters"


@runtime_checkable
class LanguageAdapter(Protocol):
    """Per-language extraction adapter.

    Cycle 1 ships zero adapters; Cycles 3 (Ruby) and 4 (Python)
    populate. The Protocol is intentionally minimal — Cycle 2's bands
    + Cycle 3+4's per-language idiom recognisers extend per-adapter.

    Implementations declare:

    - ``name`` — the adapter's identifier (e.g., ``"ruby"``,
      ``"python"``). Used in :class:`Slice.adapter_name`.
    - ``supports(repo)`` — does this repo contain code this adapter
      handles? Cheap structural check (e.g., presence of
      ``Gemfile``, ``pyproject.toml``).
    - ``extract(repo, plan)`` — given an analysis plan, run the
      adapter's extraction and produce :class:`RawACs`.
    """

    name: str

    def supports(self, repo: Path) -> bool: ...

    def extract(self, repo: Path, plan: AnalysisPlan) -> RawACs: ...


# ---- in-memory registry --------------------------------------------


# Manual-registration adapter list, keyed by name. Module-level
# (process-wide) so tests can register stub adapters and have them
# discovered alongside entry-point ones. Tests call
# ``clear_manual_registry()`` to reset between tests.
_MANUAL_REGISTRY: dict[str, LanguageAdapter] = {}


def clear_manual_registry() -> None:
    """Test-only — clear the manual-registration list."""
    _MANUAL_REGISTRY.clear()


def _validate_adapter(candidate: Any) -> None:
    """Structurally validate ``candidate`` is a :class:`LanguageAdapter`.

    Per Protocol's runtime-check semantics + explicit attribute /
    method shape inspection. Raises :class:`RegistryError` with a
    diagnostic message naming the missing attribute when invalid.
    """
    # Protocol's isinstance check is loose (presence-only). Tighten
    # by explicitly probing the three required surfaces.
    name = getattr(candidate, "name", None)
    if not isinstance(name, str) or not name:
        raise RegistryError(
            f"adapter {candidate!r} is missing a non-empty 'name' "
            "string attribute"
        )
    supports = getattr(candidate, "supports", None)
    if not callable(supports):
        raise RegistryError(
            f"adapter {name!r} is missing a callable 'supports' method"
        )
    extract = getattr(candidate, "extract", None)
    if not callable(extract):
        raise RegistryError(
            f"adapter {name!r} is missing a callable 'extract' method"
        )


def register_adapter(adapter: LanguageAdapter) -> None:
    """Register ``adapter`` for manual lookup.

    Validates Protocol compliance. Raises :class:`RegistryError` on
    invalid adapter or name collision (an adapter with the same
    ``.name`` is already registered).
    """
    _validate_adapter(adapter)
    if adapter.name in _MANUAL_REGISTRY:
        raise RegistryError(
            f"adapter {adapter.name!r} already registered"
        )
    _MANUAL_REGISTRY[adapter.name] = adapter


def discover_adapters() -> list[LanguageAdapter]:
    """Return the union of manual + entry-point-discovered adapters.

    Entry-point discovery loads each entry-point lazily; load failures
    log at WARNING and skip (mirror of ``loam_cli`` subcommand
    discovery). The returned list preserves manual-then-entry-point
    order; callers should not assume stability beyond that.

    Cycle 1 ships zero adapters via entry-point. Cycle 3 (Ruby) and
    Cycle 4 (Python) populate.
    """
    out: list[LanguageAdapter] = list(_MANUAL_REGISTRY.values())

    try:
        eps = importlib.metadata.entry_points(group=_ENTRYPOINT_GROUP)
    except Exception as exc:  # pragma: no cover — defensive
        _LOGGER.warning(
            "loam_odd_extractor: entry-point lookup failed for "
            "group %r: %s",
            _ENTRYPOINT_GROUP,
            exc,
        )
        return out

    for ep in eps:
        try:
            target = ep.load()
        except Exception as exc:
            _LOGGER.warning(
                "loam_odd_extractor: entry-point %r failed to load: %s",
                ep.name,
                exc,
            )
            continue
        # Entry-points may resolve to either an adapter instance or
        # a factory callable (both are common). Try the value first;
        # if it's callable but not Protocol-compliant, try calling it.
        candidate: Any = target
        try:
            _validate_adapter(candidate)
        except RegistryError:
            if callable(target):
                try:
                    candidate = target()
                except Exception as exc:
                    _LOGGER.warning(
                        "loam_odd_extractor: entry-point %r factory "
                        "raised: %s",
                        ep.name,
                        exc,
                    )
                    continue
                try:
                    _validate_adapter(candidate)
                except RegistryError as inner_exc:
                    _LOGGER.warning(
                        "loam_odd_extractor: entry-point %r factory "
                        "produced invalid adapter: %s",
                        ep.name,
                        inner_exc,
                    )
                    continue
            else:
                _LOGGER.warning(
                    "loam_odd_extractor: entry-point %r is neither a "
                    "valid adapter nor a callable factory",
                    ep.name,
                )
                continue
        out.append(candidate)
    return out
