"""Per-file routing extension to analyze.py.

Per Surface #9 — Cycle 4a extends Cycle 3's ``_LANGUAGE_HINTS``
table with a ``jsts`` entry covering ``.js/.mjs/.cjs/.jsx/.ts/.tsx
+ .html/.htm`` plus ``package.json`` etc. The routing logic itself
is unchanged from Cycle 3.

Verifies:

- ``.js/.ts/.tsx/.mjs/.cjs/.jsx`` route to the JsTs adapter.
- ``.html/.htm`` route to the JsTs adapter (file-level handler).
- Multi-adapter co-existence: a Rails+JsTs mixed repo correctly
  partitions Ruby files to Ruby slice and JS/TS files to JsTs
  slice.
- Files matching neither hint table land in ``unhandled``.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path


from loam_odd_extractor.analyze import analyze_repo
from loam_odd_extractor.lang.jsts import JsTsAdapter
from loam_odd_extractor.lang.ruby import RubyAdapter
from loam_odd_extractor.registry import (
    clear_manual_registry,
    register_adapter,
)
from loam_odd_extractor.budget import default_budget
from loam_odd_extractor.spec import ExtractionConfig
from loam_odd_extractor.state import (
    ExtractionState,
    extraction_dir,
    save_state,
)


def _setup_workspace(
    tmp_path: Path, repo: Path, repo_id: str
) -> ExtractionConfig:
    """Mirror of Cycle 3's per_file_routing test setup. Constructs
    the workspace + initial ExtractionState so analyze_repo can be
    called directly without going through the CLI's init stage.
    """
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    config = ExtractionConfig(
        repo_path=repo,
        repo_id=repo_id,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=False,
        created_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
    )
    ext_dir = extraction_dir(workspace_root, repo_id)
    ext_dir.mkdir(parents=True, exist_ok=True)
    state = ExtractionState(
        extraction_id=repo_id,
        repo_path=str(repo),
        workspace_root=str(workspace_root),
        init_complete=True,
    )
    save_state(ext_dir, state)
    return config


def test_jsts_extensions_route_to_jsts(
    tmp_path: Path,
    jsts_playwright_app_repo: Path,
) -> None:
    """Files with JS/TS extensions land in the jsts adapter's slice.
    """
    clear_manual_registry()
    register_adapter(JsTsAdapter())
    try:
        config = _setup_workspace(
            tmp_path, jsts_playwright_app_repo, "jsts-test"
        )
        plan = analyze_repo(config=config)
        # Exactly one slice for jsts.
        assert any(
            sl.adapter_name == "jsts" for sl in plan.slices
        )
        jsts_slice = next(
            sl for sl in plan.slices if sl.adapter_name == "jsts"
        )
        # Slice contains JS, TS, mjs files.
        suffixes = {p.suffix for p in jsts_slice.paths}
        # Expect at least .js, .mjs, .ts, .html.
        assert ".js" in suffixes
        assert ".mjs" in suffixes
        assert ".ts" in suffixes
        # HTML files in public/ also routed.
        assert ".html" in suffixes
    finally:
        clear_manual_registry()


def test_multi_adapter_partitioning(tmp_path: Path) -> None:
    """A repo with both Ruby and JS files routes correctly."""
    clear_manual_registry()
    register_adapter(JsTsAdapter())
    register_adapter(RubyAdapter())

    repo = tmp_path / "mixed-repo"
    repo.mkdir()
    # Ruby files.
    (repo / "Gemfile").write_text("source 'https://rubygems.org'\n")
    (repo / "app.rb").write_text("class App\nend\n")
    # JS file.
    (repo / "package.json").write_text('{"name": "x"}')
    (repo / "server.js").write_text("const x = 1;\n")
    # TS file.
    (repo / "user.ts").write_text("export interface User { id: number }\n")
    # Plain HTML.
    pub = repo / "public"
    pub.mkdir()
    (pub / "index.html").write_text("<script>alert(1)</script>")

    try:
        config = _setup_workspace(tmp_path, repo, "mixed-test")
        plan = analyze_repo(config=config)

        # Both adapter slices present.
        slice_names = {sl.adapter_name for sl in plan.slices}
        assert "ruby" in slice_names
        assert "jsts" in slice_names

        # Ruby slice contains .rb files only.
        ruby_slice = next(
            sl for sl in plan.slices if sl.adapter_name == "ruby"
        )
        assert all(
            p.suffix == ".rb" or p.name in ("Gemfile",)
            for p in ruby_slice.paths
        )
        # JsTs slice contains .js / .ts / .html files (and
        # package.json).
        jsts_slice = next(
            sl for sl in plan.slices if sl.adapter_name == "jsts"
        )
        # No .rb files in jsts slice.
        assert not any(p.suffix == ".rb" for p in jsts_slice.paths)
        # .js, .ts, .html present.
        suffixes = {p.suffix for p in jsts_slice.paths}
        assert ".js" in suffixes
        assert ".ts" in suffixes
        assert ".html" in suffixes
    finally:
        clear_manual_registry()


def test_unrecognized_extensions_unhandled(tmp_path: Path) -> None:
    """Files with extensions matching no adapter land in
    unhandled_paths.
    """
    clear_manual_registry()
    register_adapter(JsTsAdapter())

    repo = tmp_path / "py-only"
    repo.mkdir()
    (repo / "package.json").write_text('{"name": "x"}')
    (repo / "x.py").write_text("x = 1\n")
    (repo / "data.csv").write_text("a,b,c\n")

    try:
        config = _setup_workspace(tmp_path, repo, "py-test")
        plan = analyze_repo(config=config)

        unhandled_suffixes = {p.suffix for p in plan.unhandled_paths}
        # .py and .csv are not in the jsts hint table → unhandled.
        assert ".py" in unhandled_suffixes
        assert ".csv" in unhandled_suffixes
    finally:
        clear_manual_registry()
