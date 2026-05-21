"""AC.T1RS.GLOB.{1,2,3} — shared plan-doc / manifest locator helpers
walk both ``docs/plans/`` and ``docs/plans/sealed/``.

Per amendment #143 Scope B + §14 D-T1RS.GLOB-{LOCATION,PRIORITY,
UPDATE}: the four downstream consumers (release-gate _find_plan_doc,
heavy-b-migrate discover_amendment_plans, primary-persona session-
start enumerate_amendments_in_flight + new sibling
enumerate_sealed_amendments, dev-sdlc bash-guard _candidate_manifests)
all route through these shared helpers so a sealed plan-doc is
findable from any consumer.

ACs verified here:
- AC.T1RS.GLOB.1 — find_plan_doc_by_slug_glob recovers sealed
  plan-docs; sealed-first priority when both exist.
- AC.T1RS.GLOB.2 — iter_all_plan_docs honours include_sealed.
- AC.T1RS.GLOB.3 — iter_all_manifests returns sealed + live manifests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_amend.plan_locator import (
    find_plan_doc_by_slug_glob,
    iter_all_manifests,
    iter_all_plan_docs,
)


def _seed_dirs(tmp_path: Path) -> Path:
    """Build a fixture tree with ``docs/plans/`` + ``docs/plans/sealed/``."""
    repo = tmp_path / "repo"
    (repo / "docs" / "plans" / "sealed").mkdir(parents=True)
    return repo


def test_AC_T1RS_GLOB_1_find_plan_doc_recovers_sealed_only_slug(tmp_path):
    """A sealed plan-doc with NO live copy is findable via the
    slug-glob helper."""
    repo = _seed_dirs(tmp_path)
    (repo / "docs" / "plans" / "sealed" / "amendment-50-bar.md").write_text(
        "# bar\n", encoding="utf-8"
    )
    found = find_plan_doc_by_slug_glob(repo, "amendment-50-bar")
    assert found is not None
    assert found.name == "amendment-50-bar.md"
    # Path is rooted in the sealed/ subdirectory.
    assert "sealed" in found.parts


def test_AC_T1RS_GLOB_1_find_plan_doc_sealed_first_priority(tmp_path):
    """When both sealed AND live copies of the same slug exist, the
    sealed version wins (D-T1RS.GLOB-PRIORITY)."""
    repo = _seed_dirs(tmp_path)
    (repo / "docs" / "plans" / "amendment-50-bar.md").write_text(
        "# live\n", encoding="utf-8"
    )
    (repo / "docs" / "plans" / "sealed" / "amendment-50-bar.md").write_text(
        "# sealed\n", encoding="utf-8"
    )
    found = find_plan_doc_by_slug_glob(repo, "amendment-50-bar")
    assert found is not None
    assert "sealed" in found.parts, (
        "sealed-first priority required during transition window"
    )


def test_AC_T1RS_GLOB_1_find_plan_doc_live_only_works_too(tmp_path):
    """Backward-compat: an in-flight plan-doc (no sealed copy) is
    still findable via the helper."""
    repo = _seed_dirs(tmp_path)
    (repo / "docs" / "plans" / "amendment-99-onlylive.md").write_text(
        "# live\n", encoding="utf-8"
    )
    found = find_plan_doc_by_slug_glob(repo, "amendment-99-onlylive")
    assert found is not None
    assert found.name == "amendment-99-onlylive.md"
    assert "sealed" not in found.parts


def test_AC_T1RS_GLOB_1_find_plan_doc_returns_none_when_absent(tmp_path):
    """No match → ``None``."""
    repo = _seed_dirs(tmp_path)
    assert find_plan_doc_by_slug_glob(repo, "amendment-1-nonexistent") is None


def test_AC_T1RS_GLOB_2_iter_all_plan_docs_include_sealed_false_live_only(
    tmp_path,
):
    """include_sealed=False returns ONLY the live-tree plan-docs."""
    repo = _seed_dirs(tmp_path)
    (repo / "docs" / "plans" / "alpha.md").write_text("# a", encoding="utf-8")
    (repo / "docs" / "plans" / "beta.md").write_text("# b", encoding="utf-8")
    (repo / "docs" / "plans" / "sealed" / "gamma.md").write_text(
        "# g", encoding="utf-8"
    )
    names = sorted(p.name for p in iter_all_plan_docs(repo, include_sealed=False))
    assert names == ["alpha.md", "beta.md"]


def test_AC_T1RS_GLOB_2_iter_all_plan_docs_include_sealed_true_union(tmp_path):
    """include_sealed=True returns the UNION of live + sealed."""
    repo = _seed_dirs(tmp_path)
    (repo / "docs" / "plans" / "alpha.md").write_text("# a", encoding="utf-8")
    (repo / "docs" / "plans" / "sealed" / "gamma.md").write_text(
        "# g", encoding="utf-8"
    )
    names = sorted(p.name for p in iter_all_plan_docs(repo, include_sealed=True))
    assert names == ["alpha.md", "gamma.md"]


def test_AC_T1RS_GLOB_2_iter_all_plan_docs_default_is_include_sealed(tmp_path):
    """Default (no kwarg) is include_sealed=True."""
    repo = _seed_dirs(tmp_path)
    (repo / "docs" / "plans" / "alpha.md").write_text("# a", encoding="utf-8")
    (repo / "docs" / "plans" / "sealed" / "gamma.md").write_text(
        "# g", encoding="utf-8"
    )
    names = sorted(p.name for p in iter_all_plan_docs(repo))
    assert "alpha.md" in names
    assert "gamma.md" in names


def test_AC_T1RS_GLOB_2_iter_all_plan_docs_missing_dir_empty(tmp_path):
    """A workspace without docs/plans/ yields an empty iterator
    (graceful refusal — no exception)."""
    repo = tmp_path / "noplans"
    repo.mkdir()
    assert list(iter_all_plan_docs(repo)) == []


def test_AC_T1RS_GLOB_3_iter_all_manifests_union(tmp_path):
    """iter_all_manifests returns sealed + live ``*.manifest.yaml``
    files; bash-guard's _candidate_manifests semantics preserved
    across both locations."""
    repo = _seed_dirs(tmp_path)
    (repo / "docs" / "plans" / "alpha.manifest.yaml").write_text(
        "schema_version: 1\n", encoding="utf-8"
    )
    (repo / "docs" / "plans" / "sealed" / "beta.manifest.yaml").write_text(
        "schema_version: 1\n", encoding="utf-8"
    )
    # A non-manifest .yaml file is NOT yielded.
    (repo / "docs" / "plans" / "something.yaml").write_text(
        "x: 1\n", encoding="utf-8"
    )
    names = sorted(p.name for p in iter_all_manifests(repo))
    assert names == ["alpha.manifest.yaml", "beta.manifest.yaml"]


def test_AC_T1RS_GLOB_3_iter_all_manifests_include_sealed_false(tmp_path):
    """include_sealed=False restricts to live-tree manifests."""
    repo = _seed_dirs(tmp_path)
    (repo / "docs" / "plans" / "alpha.manifest.yaml").write_text(
        "schema_version: 1\n", encoding="utf-8"
    )
    (repo / "docs" / "plans" / "sealed" / "beta.manifest.yaml").write_text(
        "schema_version: 1\n", encoding="utf-8"
    )
    names = sorted(
        p.name for p in iter_all_manifests(repo, include_sealed=False)
    )
    assert names == ["alpha.manifest.yaml"]
