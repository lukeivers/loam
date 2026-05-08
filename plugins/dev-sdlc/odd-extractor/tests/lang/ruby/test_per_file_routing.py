"""Per-file routing in analyze.py (Surface #6).

Verifies the analyze stage routes files to adapters by language hint
(file extension / filename), not by all-or-nothing claim. Cycle 1's
stale all-or-nothing behaviour was a documented Cycle-3 refinement;
this test pins the new per-file routing.
"""

from __future__ import annotations

from pathlib import Path


from loam_odd_extractor.analyze import analyze_repo
from loam_odd_extractor.init import init_extraction
from loam_odd_extractor.budget import default_budget
from loam_odd_extractor.registry import (
    register_adapter,
)


class _StubPythonAdapter:
    """Stub Python adapter — claims any repo, but the routing table
    only assigns ``.py`` files to it."""

    name = "python"

    def supports(self, repo: Path) -> bool:
        return True

    def extract(self, repo, plan):  # pragma: no cover (unused)
        from loam_odd_extractor.spec import RawACs
        return RawACs(
            extraction_id="x",
            acs=[],
            unhandled_paths=[],
            per_slice_costs={},
            created_at="2026-05-04T00:00:00+00:00",
        )


def test_per_file_routing_partitions_rb_and_py(
    tmp_path: Path,
) -> None:
    """A repo with .rb + .py + .txt routes correctly: .rb → ruby
    slice, .py → python slice, .txt → unhandled.
    """
    repo = tmp_path / "mixed"
    repo.mkdir()
    (repo / "Gemfile").write_text("source 'rg'\n", encoding="utf-8")
    (repo / "main.rb").write_text("class A; end\n", encoding="utf-8")
    (repo / "tool.py").write_text("print('hello')\n", encoding="utf-8")
    (repo / "notes.txt").write_text("plain\n", encoding="utf-8")

    workspace = tmp_path / "ws"
    workspace.mkdir()

    register_adapter(_StubPythonAdapter())

    config = init_extraction(
        repo_path=repo,
        workspace_root=workspace,
        budget=default_budget(),
        dry_run=True,
    )
    plan = analyze_repo(config=config)

    # Two slices expected: ruby-root + python-root.
    slice_names = {s.adapter_name for s in plan.slices}
    assert "ruby" in slice_names
    assert "python" in slice_names

    # .rb / Gemfile / Rakefile → ruby slice; .py → python slice.
    # Gemfile is name-routed (no suffix).
    ruby_slice = next(s for s in plan.slices if s.adapter_name == "ruby")
    py_slice = next(
        s for s in plan.slices if s.adapter_name == "python"
    )
    ruby_keys = {(p.suffix, p.name) for p in ruby_slice.paths}
    assert any(p.suffix == ".rb" for p in ruby_slice.paths)
    # Every ruby-slice file has either .rb / .rake / .gemspec
    # suffix OR is one of the named-Ruby files.
    for p in ruby_slice.paths:
        assert p.suffix in (".rb", ".rake", ".gemspec") or p.name in (
            "Gemfile",
            "Rakefile",
            "config.ru",
        )
    assert any(p.suffix == ".py" for p in py_slice.paths)
    for p in py_slice.paths:
        assert p.suffix == ".py"

    # .txt → unhandled.
    unhandled_suffixes = {p.suffix for p in plan.unhandled_paths}
    assert ".txt" in unhandled_suffixes


def test_routing_handles_gemfile_and_rakefile(tmp_path: Path) -> None:
    """Filename-based hints route Gemfile + Rakefile + .gemspec to ruby."""
    repo = tmp_path / "rb-named"
    repo.mkdir()
    (repo / "Gemfile").write_text("source 'rg'\n", encoding="utf-8")
    (repo / "Rakefile").write_text("task :default\n", encoding="utf-8")
    (repo / "lib.gemspec").write_text(
        "Gem::Specification.new\n", encoding="utf-8"
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()

    config = init_extraction(
        repo_path=repo,
        workspace_root=workspace,
        budget=default_budget(),
        dry_run=True,
    )
    plan = analyze_repo(config=config)

    ruby_slice = next(
        (s for s in plan.slices if s.adapter_name == "ruby"), None
    )
    assert ruby_slice is not None
    names = {p.name for p in ruby_slice.paths}
    assert "Gemfile" in names
    assert "Rakefile" in names
    assert "lib.gemspec" in names


def test_no_supports_means_no_slice(tmp_path: Path) -> None:
    """An adapter that returns False for supports() doesn't get
    files routed to it (and doesn't appear in the slice list).
    """
    class _NoSupportAdapter:
        name = "nosupport"

        def supports(self, repo):
            return False

        def extract(self, repo, plan):  # pragma: no cover
            from loam_odd_extractor.spec import RawACs
            return RawACs(
                extraction_id="x", acs=[], unhandled_paths=[],
                per_slice_costs={},
                created_at="2026-05-04T00:00:00+00:00",
            )

    repo = tmp_path / "py-only"
    repo.mkdir()
    (repo / "main.py").write_text("print(1)\n", encoding="utf-8")
    workspace = tmp_path / "ws"
    workspace.mkdir()

    register_adapter(_NoSupportAdapter())

    config = init_extraction(
        repo_path=repo,
        workspace_root=workspace,
        budget=default_budget(),
        dry_run=True,
    )
    plan = analyze_repo(config=config)
    # No slice for nosupport.
    assert all(s.adapter_name != "nosupport" for s in plan.slices)
