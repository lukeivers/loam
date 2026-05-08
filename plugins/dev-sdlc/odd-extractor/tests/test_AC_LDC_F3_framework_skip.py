# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.LDC.F3 — odd-extractor analyze step skips ``framework/``.

Per v0.3.0 Cycle 4 plan-doc §4 AC.LDC.F3: cross-component-skip
discipline. The odd-extractor's ``analyze._walk_repo`` skips
``framework/`` so loam-tree self-extraction doesn't leak harness
scaffolding into evidence rows. Mirrors the v0.2.1 corrective F2
fix that added ``framework`` to ``language_detection._SKIPPED_DIRS``.

Per FIDRAFT v0.2.5 yellow finding F3 (captured 2026-05-05).
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.analyze import _SKIP_DIR_NAMES, _walk_repo


def test_framework_in_skip_dir_names() -> None:
    """``framework`` is in the static skip-set."""
    assert "framework" in _SKIP_DIR_NAMES


def test_framework_subdir_files_are_skipped(tmp_path: Path) -> None:
    """Files under ``framework/`` are NOT yielded by ``_walk_repo``.

    Construct a tiny repo with one top-level src file and a
    framework/ subtree carrying loam-internal fixtures. The walker
    must skip framework/ so its contents don't leak into the
    candidate list.
    """
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("# app\n")

    framework_dir = tmp_path / "framework"
    framework_dir.mkdir()
    (framework_dir / "loam-internal.py").write_text("# harness\n")
    (framework_dir / "Gemfile").write_text("source 'rubygems'\n")
    fixtures = framework_dir / "fixtures" / "jsts-playwright-app"
    fixtures.mkdir(parents=True)
    (fixtures / "package.json").write_text("{}\n")

    paths = _walk_repo(tmp_path)
    rels = {p.relative_to(tmp_path).as_posix() for p in paths}

    assert "src/app.py" in rels
    # No path under framework/ should appear
    framework_leaks = {r for r in rels if r.startswith("framework/")}
    assert framework_leaks == set(), (
        f"framework/ files leaked into walk: {sorted(framework_leaks)}"
    )


def test_framework_skip_does_not_break_extra_skip_dir_names(
    tmp_path: Path,
) -> None:
    """``extra_skip_dir_names`` still unions correctly with framework
    in the static set."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("# app\n")
    (tmp_path / "framework").mkdir()
    (tmp_path / "framework" / "x.py").write_text("# harness\n")
    (tmp_path / "html-output").mkdir()
    (tmp_path / "html-output" / "y.html").write_text("<html/>\n")
    (tmp_path / "private").mkdir()
    (tmp_path / "private" / "z.txt").write_text("secret\n")

    paths = _walk_repo(
        tmp_path, extra_skip_dir_names=frozenset({"private"})
    )
    rels = {p.relative_to(tmp_path).as_posix() for p in paths}

    assert "src/app.py" in rels
    assert not any(r.startswith("framework/") for r in rels)
    assert not any(r.startswith("html-output/") for r in rels)
    assert not any(r.startswith("private/") for r in rels)
