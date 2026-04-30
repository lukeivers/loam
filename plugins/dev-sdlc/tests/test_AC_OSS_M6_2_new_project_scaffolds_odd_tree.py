"""AC.OSS-M6.2 — `loam project new <slug>` scaffolds an ODD-shaped
project tree.

Per plan §4 AC.OSS-M6.2: the project tree contains the per-stage
subdirectories + the SQLite row records the project at
`current_stage=research`.
"""

from __future__ import annotations

from pathlib import Path

from loam.plugins.dev_sdlc import api, store


def test_start_project_creates_project_tree(tmp_path: Path) -> None:
    handle = api.start_project(slug="my-project", workspace_root=tmp_path)
    proj_root = tmp_path / "projects" / "my-project"
    assert proj_root.is_dir()
    for st in ("research", "spec", "plan", "build", "review"):
        assert (proj_root / st).is_dir(), f"missing stage dir: {st}"
    assert handle.slug == "my-project"
    assert handle.methodology == "odd"
    assert handle.current_stage == "research"
    assert handle.project_root == proj_root


def test_start_project_writes_yaml_mirror(tmp_path: Path) -> None:
    api.start_project(slug="my-project", workspace_root=tmp_path)
    mirror = tmp_path / "projects" / "my-project" / ".dev-sdlc.yaml"
    assert mirror.is_file()
    text = mirror.read_text(encoding="utf-8")
    assert "slug: my-project" in text
    assert "methodology: odd" in text
    assert "current_stage: research" in text


def test_start_project_writes_sqlite_row(tmp_path: Path) -> None:
    api.start_project(slug="alpha", workspace_root=tmp_path)
    db = tmp_path / ".loam" / "dev-sdlc.sqlite"
    assert db.is_file()
    with store.open_store(tmp_path) as conn:
        row = store.get_project(conn, "alpha")
    assert row is not None
    assert row.slug == "alpha"
    assert row.methodology == "odd"
    assert row.current_stage == "research"
