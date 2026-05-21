"""Shared plan-doc / manifest locator helpers (amendment #143 Scope B).

Walks BOTH ``docs/plans/*.md`` (in-flight) and ``docs/plans/sealed/*.md``
(archived) so every downstream consumer can find plan-docs regardless
of whether they have been swept into the sealed archive.

Companion to ``plan_archive.py`` (sweep mechanism); cohesion with that
module per D-T1RS.GLOB-LOCATION ruling. The cross-tree import from
``loam_cli.release.gates`` + ``loam.heavy_b_migrate.amendment_acs`` +
``loam.primary_persona.session_start_gate`` + ``dev-sdlc/hooks/
bash_guard.py`` is precedented by heavy-b-migrate already importing
from ``loam_amend``.

Per plan-doc ``amendment-143-tier1-retroactive-sweep-followup.md``
§3 Scope B + §14 D-T1RS.GLOB-LOCATION + D-T1RS.GLOB-PRIORITY:
- Three helpers cover the four downstream consumer shapes.
- ``find_plan_doc_by_slug_glob`` returns sealed-FIRST when both a
  sealed and a live copy of the same slug exist (transition-window
  semantics; sealed is the canonical shipped artefact).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path


_PLANS_DIR_REL = ("docs", "plans")
_SEALED_DIR_REL = ("docs", "plans", "sealed")


def _plans_dir(repo_root: Path) -> Path:
    return Path(repo_root, *_PLANS_DIR_REL)


def _sealed_dir(repo_root: Path) -> Path:
    return Path(repo_root, *_SEALED_DIR_REL)


def iter_all_plan_docs(
    repo_root: Path,
    *,
    include_sealed: bool = True,
) -> Iterator[Path]:
    """Yield every plan-doc (``*.md``) under ``docs/plans/`` (and
    optionally ``docs/plans/sealed/``), deterministic order.

    AC.T1RS.GLOB.2: ``include_sealed=False`` returns only the
    live-tree plan-docs; ``include_sealed=True`` returns the union.
    Each path is yielded at most once; if the same filename exists
    in both directories (transition-window), both are yielded so the
    caller can disambiguate (consumers that need a single answer
    should use ``find_plan_doc_by_slug_glob`` instead).

    Direct children only: no recursion into sub-dirs other than
    ``sealed/`` (mirrors ``plan_archive.py`` semantics).
    """
    plans_dir = _plans_dir(repo_root)
    if plans_dir.is_dir():
        for child in sorted(plans_dir.iterdir()):
            if child.is_file() and child.suffix == ".md":
                yield child
    if include_sealed:
        sealed_dir = _sealed_dir(repo_root)
        if sealed_dir.is_dir():
            for child in sorted(sealed_dir.iterdir()):
                if child.is_file() and child.suffix == ".md":
                    yield child


def iter_all_manifests(
    repo_root: Path,
    *,
    include_sealed: bool = True,
) -> Iterator[Path]:
    """Yield every manifest (``*.manifest.yaml``) under ``docs/plans/``
    (and optionally ``docs/plans/sealed/``), deterministic order.

    AC.T1RS.GLOB.3: bash-guard dry-run probe iterates manifests from
    either location; sealed manifests remain valid manifest YAML and
    the dry-run can still operate on them.
    """
    plans_dir = _plans_dir(repo_root)
    if plans_dir.is_dir():
        for child in sorted(plans_dir.iterdir()):
            if child.is_file() and child.name.endswith(".manifest.yaml"):
                yield child
    if include_sealed:
        sealed_dir = _sealed_dir(repo_root)
        if sealed_dir.is_dir():
            for child in sorted(sealed_dir.iterdir()):
                if child.is_file() and child.name.endswith(".manifest.yaml"):
                    yield child


def find_plan_doc_by_slug_glob(
    repo_root: Path,
    slug_prefix: str,
) -> Path | None:
    """Return the best-match plan-doc whose stem starts with
    ``slug_prefix``, walking sealed-FIRST then live-tree.

    AC.T1RS.GLOB.1: replicates the ``gates.py`` semantics of
    ``glob(f"{slug}-*.md") + glob(f"{slug}.md")`` across BOTH
    ``docs/plans/sealed/`` and ``docs/plans/``. Sealed-first per
    D-T1RS.GLOB-PRIORITY: sealed is the canonical shipped artefact
    when both versions exist during the transition window.

    Returns ``None`` if no match is found in either location.
    """
    for base in (_sealed_dir(repo_root), _plans_dir(repo_root)):
        if not base.is_dir():
            continue
        matches = sorted(base.glob(f"{slug_prefix}-*.md")) + sorted(
            base.glob(f"{slug_prefix}.md")
        )
        if matches:
            return matches[0]
    return None
