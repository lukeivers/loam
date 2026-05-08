# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.SFR.3 — primary-persona corpus-discovery readers fall through to
``<workspace>/framework/`` when the workspace-root copy is absent.

Single-framework restructure (amendment #67). After the restructure,
``pos-new-workspace --from <canonical>`` clones canonical's
``framework-only`` branch into ``<workspace>/framework/``. The
synthetic branch carries top-level docs at its root, so workspaces
land them at ``<workspace>/framework/<doc>``. The corpus-discovery
readers probe the workspace-root path first (preserving today's
behaviour for workspaces that scaffold their own workspace-root copy)
and fall through to ``<workspace>/framework/`` when absent.

Two paths exercised:

- workspace-root present → reader returns the workspace-root path.
- workspace-root absent + framework copy present → reader falls
  through; existence/parse uses the framework copy.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.session_start_gate import (
    _resolve_corpus_path,
    compose_session_fields,
    discover_baseline_corpus,
    enumerate_amendments_in_flight,
)


# ---- _resolve_corpus_path ------------------------------------------


def test_resolve_corpus_path_prefers_workspace_root(tmp_path: Path) -> None:
    """When `<workspace>/<rel>` exists, it is returned."""
    workspace_root = tmp_path
    (workspace_root / "CLAUDE.md").write_text("# workspace root copy\n")
    (workspace_root / "framework").mkdir()
    (workspace_root / "framework" / "CLAUDE.md").write_text(
        "# framework copy\n"
    )

    resolved = _resolve_corpus_path(workspace_root, "CLAUDE.md")
    assert resolved == workspace_root / "CLAUDE.md"
    assert resolved.read_text() == "# workspace root copy\n"


def test_resolve_corpus_path_falls_through_to_framework(
    tmp_path: Path,
) -> None:
    """When workspace-root path absent + framework path present, the
    framework path is returned."""
    workspace_root = tmp_path
    (workspace_root / "framework").mkdir()
    (workspace_root / "framework" / "CLAUDE.md").write_text(
        "# framework copy\n"
    )

    resolved = _resolve_corpus_path(workspace_root, "CLAUDE.md")
    assert resolved == workspace_root / "framework" / "CLAUDE.md"
    assert resolved.read_text() == "# framework copy\n"


def test_resolve_corpus_path_returns_workspace_root_when_neither(
    tmp_path: Path,
) -> None:
    """Both absent → returns workspace-root path so callers' existence
    checks surface the absence the standard way."""
    workspace_root = tmp_path
    resolved = _resolve_corpus_path(workspace_root, "CLAUDE.md")
    assert resolved == workspace_root / "CLAUDE.md"
    assert not resolved.exists()


# ---- discover_baseline_corpus --------------------------------------


def test_discover_baseline_corpus_falls_through_to_framework(
    tmp_path: Path,
) -> None:
    """When workspace-root CLAUDE.md is absent, the parser uses
    ``<workspace>/framework/CLAUDE.md``.
    """
    workspace_root = tmp_path
    framework = workspace_root / "framework"
    framework.mkdir()

    # Frame the section the parser looks for + a non-default reference
    # so we can prove the framework copy was parsed (not the fallback).
    framework_claude = framework / "CLAUDE.md"
    framework_claude.write_text(
        "# fixture\n"
        "## Session-start discipline\n"
        "Always read `docs/sentinel-from-framework.md` first.\n"
        "## next\n"
    )

    paths = discover_baseline_corpus(workspace_root)

    assert "CLAUDE.md" in paths
    assert "docs/sentinel-from-framework.md" in paths


def test_discover_baseline_corpus_prefers_workspace_root(
    tmp_path: Path,
) -> None:
    """When `<workspace>/CLAUDE.md` exists, the framework copy is
    ignored.
    """
    workspace_root = tmp_path
    framework = workspace_root / "framework"
    framework.mkdir()

    (workspace_root / "CLAUDE.md").write_text(
        "# workspace-root\n"
        "## Session-start discipline\n"
        "Always read `docs/sentinel-from-workspace-root.md` first.\n"
        "## next\n"
    )
    (framework / "CLAUDE.md").write_text(
        "# framework\n"
        "## Session-start discipline\n"
        "Always read `docs/sentinel-from-framework.md` first.\n"
        "## next\n"
    )

    paths = discover_baseline_corpus(workspace_root)

    assert "docs/sentinel-from-workspace-root.md" in paths
    assert "docs/sentinel-from-framework.md" not in paths


# ---- enumerate_amendments_in_flight --------------------------------


def test_enumerate_amendments_in_flight_falls_through_to_framework(
    tmp_path: Path,
) -> None:
    """When `<workspace>/docs/plans/` is absent, the reader
    walks `<workspace>/framework/docs/plans/` instead.
    """
    workspace_root = tmp_path
    framework_plans = (
        workspace_root / "framework" / "docs" / "plans"
    )
    framework_plans.mkdir(parents=True)
    (framework_plans / "amendment-1-foo.md").write_text("# foo\n")
    (framework_plans / "amendment-2-bar.md").write_text("# bar\n")
    (framework_plans / "not-an-amendment.md").write_text("# skip\n")

    matches = enumerate_amendments_in_flight(workspace_root)
    # Returned paths are workspace-relative against the framework
    # location (callers can read them at <workspace>/<rel>).
    assert "framework/docs/plans/amendment-1-foo.md" in matches
    assert "framework/docs/plans/amendment-2-bar.md" in matches
    assert all(
        "not-an-amendment" not in m for m in matches
    )


def test_enumerate_amendments_in_flight_prefers_workspace_root(
    tmp_path: Path,
) -> None:
    """When `<workspace>/docs/plans/` is present, the reader
    uses it (and ignores any framework-side copy).
    """
    workspace_root = tmp_path
    plans = workspace_root / "docs" / "plans"
    plans.mkdir(parents=True)
    (plans / "amendment-99-from-root.md").write_text("# root\n")

    framework_plans = (
        workspace_root / "framework" / "docs" / "plans"
    )
    framework_plans.mkdir(parents=True)
    (framework_plans / "amendment-99-from-fw.md").write_text("# fw\n")

    matches = enumerate_amendments_in_flight(workspace_root)
    assert matches == ["docs/plans/amendment-99-from-root.md"]


# ---- compose_session_fields end-to-end -----------------------------


def test_compose_session_fields_end_to_end_with_framework_fall_through(
    tmp_path: Path,
) -> None:
    """End-to-end binding: a workspace whose corpus is only at
    ``<workspace>/framework/`` (no workspace-root copies) reports
    ``corpus_gate_state == loaded`` because the existence check
    falls through.
    """
    workspace_root = tmp_path
    framework = workspace_root / "framework"
    framework.mkdir()

    framework_claude = framework / "CLAUDE.md"
    framework_claude.write_text(
        "# fixture\n## Session-start discipline\n"
        "load `docs/odd-methodology.md` and "
        "`docs/VALUE_PROPOSITION.md`.\n## next\n"
    )

    # Fall-through targets must exist for `corpus_gate_state == loaded`.
    (framework / "docs").mkdir()
    (framework / "docs" / "odd-methodology.md").write_text("# odd\n")
    (framework / "docs" / "VALUE_PROPOSITION.md").write_text(
        "# vp\n"
    )

    fields = compose_session_fields(workspace_root)
    # corpus_gate_state is loaded when every probed path is present.
    from loam.primary_persona.context_composer import CorpusGateState

    assert fields["corpus_gate_state"] == CorpusGateState.loaded
    assert fields["missing_paths"] == ()
