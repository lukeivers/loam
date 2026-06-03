"""The project registry for per-project STATE derivation (Slice C, P4-1).

The STATE-OF-LOAM record (:mod:`loam_cli.audit.record`) derives a
project's REAL build/sealed/merged status from ground truth (git refs +
markers), never from drift-prone prose. It was wired only to loam's own
markers. This registry generalizes it to ANY registered project: a
project name resolves to its repo root + a fresh-derivation callable,
each keyed to THAT project's real ground-truth markers.

Two projects are registered:

  * ``loam``  → :func:`loam_state.default_state_record` — loam's
    seal-sidecar + hook + backend markers (unchanged).
  * ``cairn`` → :func:`cairn_state.cairn_state_record` — Cairn's
    present-module + merged-introducing-commit markers (Cairn has NO
    seal sidecars; the markers are its own, proving the engine
    generalizes rather than re-hardcoding loam's).

An unregistered name resolves to ``None`` (a clean "not registered"
result), never a crash — the caller decides what to do with an unknown
project.

This is the accuracy anchor: it lets the persona derive ANY registered
project's status from ground truth, instead of describing it from stale
prose (the exact failure that made the persona wrong about Cairn).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from loam_cli.audit.cairn_state import DEFAULT_CAIRN_REPO_ROOT, cairn_state_record
from loam_cli.audit.loam_state import default_state_record
from loam_cli.audit.record import StateOfLoam

#: A project's STATE derivation: takes the repo root, returns a freshly
#: derived :class:`StateOfLoam` record. Each registered project supplies
#: its own, keyed to its real markers.
ProjectDeriveFn = Callable[[Path], StateOfLoam]


@dataclass(frozen=True)
class ProjectStateSpec:
    """One registered project: a name, its repo root, and the callable
    that derives its STATE record FRESH from that repo's ground truth.

    *derive* is keyed to the project's OWN markers (loam's seal sidecars,
    Cairn's present-module + merged-commit ancestry) — so the registry
    is a real generalization of the STATE engine, not a per-project
    hardcode of loam's shape.
    """

    name: str
    repo_root: Path
    derive: ProjectDeriveFn


def _loam_derive(repo_root: Path) -> StateOfLoam:
    return default_state_record(repo_root)


def _cairn_derive(repo_root: Path) -> StateOfLoam:
    return cairn_state_record(repo_root)


#: The default repo root for loam: the canonical checkout. Overridable
#: per resolved spec (tests point at a fixture / their own tree).
DEFAULT_LOAM_REPO_ROOT = Path("/Users/lukeivers/loam")


def _default_registry() -> dict[str, ProjectStateSpec]:
    return {
        "loam": ProjectStateSpec(
            name="loam",
            repo_root=DEFAULT_LOAM_REPO_ROOT,
            derive=_loam_derive,
        ),
        "cairn": ProjectStateSpec(
            name="cairn",
            repo_root=DEFAULT_CAIRN_REPO_ROOT,
            derive=_cairn_derive,
        ),
    }


#: The live project registry. A mapping name → :class:`ProjectStateSpec`.
PROJECT_REGISTRY: dict[str, ProjectStateSpec] = _default_registry()


def resolve_project(
    name: str,
    *,
    registry: dict[str, ProjectStateSpec] | None = None,
) -> ProjectStateSpec | None:
    """Resolve a project name to its :class:`ProjectStateSpec`, or
    ``None`` when the name is not registered.

    Lower-cased + stripped before lookup. An unregistered name is a
    clean ``None`` (not a crash) — the caller chooses how to surface
    "no ground-truth spec for this project".
    """
    reg = registry if registry is not None else PROJECT_REGISTRY
    return reg.get(name.strip().lower())


def registered_project_names(
    *,
    registry: dict[str, ProjectStateSpec] | None = None,
) -> tuple[str, ...]:
    """The names of every registered project (sorted, stable)."""
    reg = registry if registry is not None else PROJECT_REGISTRY
    return tuple(sorted(reg.keys()))


def derive_project_state(
    name: str,
    *,
    repo_root: Path | None = None,
    registry: dict[str, ProjectStateSpec] | None = None,
) -> StateOfLoam | None:
    """Derive a registered project's STATE record FRESH from ground truth.

    Returns the derived :class:`StateOfLoam`, or ``None`` when *name* is
    not registered (clean, not a crash). *repo_root* overrides the
    registered default (tests point at a fixture repo); production uses
    the registered live root.

    The record is generated fresh on every call from the project's real
    markers — never copied from persisted prose — so it cannot have
    drifted. This is the production entry point the persona uses to
    derive a project's REAL status.
    """
    spec = resolve_project(name, registry=registry)
    if spec is None:
        return None
    root = repo_root if repo_root is not None else spec.repo_root
    return spec.derive(root)
