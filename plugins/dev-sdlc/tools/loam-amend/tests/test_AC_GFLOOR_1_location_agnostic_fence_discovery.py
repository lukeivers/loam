"""AC.GFLOOR.1 — location-agnostic fence-class discovery.

Per ``docs/plans/seal-guard-sweep-floor.md`` §4: the seal's
cross-component sweep covers every TRACKED fence test
(``*/tests/test_no_sealed_amendments.py`` +
``*/tests/test_cross_cutting.py``) regardless of tree location
(``framework/*``, ``framework/tools/*``, ``plugins/*``), excluding
``docs/archive/``. The pre-floor ``_discover_sealed_components``
globbed only ``framework/*/tests/SEAL_COMMIT`` — 6 of 26 sealed
components (framework/tools/* + plugins/*) were never swept; that
gap is the disease this AC cures.

Fixture: a synthetic repo carrying fence tests in all three tree
shapes plus (a) a ``docs/archive/`` decoy and (b) an UNTRACKED fence
test, both of which would FAIL if ever run — a green seal is proof
they are not floor members.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from loam_amend.cli import main as cli_main
from loam_amend.guard_floor import discover_guard_floor

from test_seal import (  # noqa: F401 — sealed_repo unused here, helpers used
    _git,
    _make_amendment_commit,
    _write_manifest,
)


def _make_component_at(
    repo: Path, comp_rel: str, *, passing: bool = True
) -> None:
    """Create a fence-test-carrying component at *comp_rel*
    (repo-relative dir, e.g. ``framework/tools/beta``)."""
    comp_dir = repo / comp_rel
    (comp_dir / "tests").mkdir(parents=True, exist_ok=True)
    (comp_dir / "tests" / "SEAL_COMMIT").write_text(
        "0000000000000000000000000000000000000000\n", encoding="utf-8"
    )
    header = textwrap.dedent(
        f"""
        # Fixture seal-diff test at {comp_rel}.
        allowed_prefixes = (
            "{comp_rel}/",
            "docs/plans/",
        )
        allowed_files = (
            "CLAUDE.md",
        )
        """
    ).lstrip()
    if passing:
        body = header + "def test_seal_diff_ok():\n    assert True\n"
    else:
        body = header + (
            "def test_seal_diff_fails():\n"
            "    assert False, 'decoy fence test must never run'\n"
        )
    (comp_dir / "tests" / "test_no_sealed_amendments.py").write_text(
        body, encoding="utf-8"
    )


def _three_tree_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "workspace"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "loam amend test")
    # ``framework/untracked-comp/`` is gitignored — the analogue of
    # the real workspace's gitignored ``.scratch/`` smoke trees,
    # which a filesystem glob WOULD find and tracked-only discovery
    # must not.
    (repo / ".gitignore").write_text(
        "__pycache__/\n*.pyc\nframework/untracked-comp/\n",
        encoding="utf-8",
    )
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    # All three live tree shapes the real workspace uses.
    _make_component_at(repo, "framework/alpha")
    _make_component_at(repo, "framework/tools/beta")
    _make_component_at(repo, "plugins/gamma")
    # Also give alpha an ordinary suite + src dir so the manifest
    # component's step-(d) run and amendment commit have a home.
    (repo / "framework/alpha/src").mkdir(parents=True, exist_ok=True)
    (repo / "framework/alpha/src/__init__.py").write_text(
        "\n", encoding="utf-8"
    )
    # docs/archive/ decoy — tracked but EXCLUDED from the floor;
    # would fail if run.
    _make_component_at(repo, "docs/archive/old-tool", passing=False)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: three-tree components")
    # Gitignored (untracked) fence test — would fail if run;
    # tracked-only discovery must not see it.
    _make_component_at(repo, "framework/untracked-comp", passing=False)
    return repo


def test_AC_GFLOOR_1_discovery_covers_all_tree_shapes(tmp_path: Path) -> None:
    """Direct discovery: all three tree shapes found; archive decoy
    and untracked fence test excluded."""
    repo = _three_tree_repo(tmp_path)
    floor = discover_guard_floor(repo)
    assert sorted(str(p) for p in floor.fence_targets) == [
        "framework/alpha/tests/test_no_sealed_amendments.py",
        "framework/tools/beta/tests/test_no_sealed_amendments.py",
        "plugins/gamma/tests/test_no_sealed_amendments.py",
    ]
    assert not floor.registry_present
    assert floor.stale_patterns == []


def test_AC_GFLOOR_1_seal_sweeps_all_three_and_skips_decoys(
    tmp_path: Path,
) -> None:
    """Production seal: the floor runs all three fence tests (summary
    counts them) and never runs the failing archive/untracked decoys
    (the seal is green — a decoy run would red it)."""
    repo = _three_tree_repo(tmp_path)
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=930,
        slug="gfloor-1",
        seal_description="gfloor-1",
    )
    _make_amendment_commit(repo, "alpha", payload="gfloor1")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc == 0
    body = _git(repo, "log", "-1", "--format=%B").stdout
    assert "guard floor 3 targets green (3 fence + 0 sweep-class)" in body
