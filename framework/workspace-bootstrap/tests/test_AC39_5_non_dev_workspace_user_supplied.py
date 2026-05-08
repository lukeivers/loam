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

"""Amendment #39 — AC39.5 — Non-pos-v2-dev workspace seed reads the
workspace user's value-prop content.

Plan §4 AC39.5 outcomes:

- On a workspace NOT classified as pos-v2 dev (no
  ``docs/VALUE_PROPOSITION.md`` at the framework path), the
  seed reads ``<workspace>/value-prop.md`` as the source.
- The root's ``authored_by == "user"``.
- ``lifted_from.source_doc`` points at the workspace-supplied source
  (``"value-prop.md"``), NOT at the framework value-prop doc.
- No pOS-core value-prop content is shipped into the non-dev
  workspace's tree.
- A non-dev workspace WITHOUT a ``value-prop.md`` file completes the
  scaffold without raising and reports the seed as skipped.

Maps to v1.2 R16 framework-not-content extended to tracker seeding
(workspaces supply, framework provides) + owner ruling D-4
(Reading (b) of locked ruling #5) → AC.PO.1 + AC.PO.2.
"""

from __future__ import annotations

from pathlib import Path

from loam.objective_tracker import ObjectiveTracker

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    run_first_run_scaffold,
)
from loam.workspace_bootstrap.adapters.tracker_seed import (
    FRAMEWORK_VALUE_PROP_RELPATH,
    ROOT_OBJECTIVE_ID,
    WORKSPACE_VALUE_PROP_RELPATH,
    classify_workspace,
    tracker_db_path_for,
)


_SAMPLE_USER_VALUE_PROP = """\
# Acme Corp Workspace Value Proposition

Acme is closing the gap between hand-crafted regulatory filings and
machine-assisted compliance research.

## Primary-persona test

Does this reduce the compliance researcher's translation burden?

## Harness test

Does this add to the compliance toolkit our primary persona draws from?
"""


def test_AC39_5_classifier_returns_user_when_framework_doc_absent(
    tmp_path: Path,
) -> None:
    """A workspace that lacks ``docs/VALUE_PROPOSITION.md``
    classifies as ``"user"``, not ``"pos-v2-dev"``."""
    workspace = tmp_path / "ws-user"
    workspace.mkdir()
    assert classify_workspace(workspace) == "user"


def test_AC39_5_user_workspace_with_value_prop_seeds_from_local_file(
    tmp_path: Path,
) -> None:
    """User workspace with ``value-prop.md`` present at the workspace
    root: the seed reads that file and the seeded root carries
    ``lifted_from.source_doc == "value-prop.md"`` and
    ``authored_by == "user"``."""
    workspace = tmp_path / "ws-user-vp"
    workspace.mkdir()
    (workspace / WORKSPACE_VALUE_PROP_RELPATH).write_text(_SAMPLE_USER_VALUE_PROP)
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"

    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )

    assert result.tracker_classification == "user"
    assert result.tracker_seeded is True
    assert result.tracker_seed_reason == "fresh_seed"
    assert result.tracker_value_prop_source == WORKSPACE_VALUE_PROP_RELPATH

    tracker = ObjectiveTracker(tracker_db_path_for(workspace))
    try:
        root = tracker.get(ROOT_OBJECTIVE_ID)
        assert root is not None
        assert root.authored_by == "user"
        assert root.lifted_from is not None
        assert root.lifted_from.source_doc == WORKSPACE_VALUE_PROP_RELPATH
        assert root.lifted_from.source_doc != FRAMEWORK_VALUE_PROP_RELPATH

        # User-supplied content reaches the goal.
        assert "Acme" in root.goal

        # AC.PO.1 + AC.PO.2 still extracted from the user's file
        # (the parser's section regex matches the user's headers).
        criterion_ids = {c.criterion_id for c in root.acceptance_criteria}
        assert "AC.PO.1" in criterion_ids
        assert "AC.PO.2" in criterion_ids

        # The user-section content is the prose source.
        prose_by_id = {
            c.criterion_id: c.prose for c in root.acceptance_criteria
        }
        assert "compliance researcher" in prose_by_id["AC.PO.1"]
        assert "compliance toolkit" in prose_by_id["AC.PO.2"]
    finally:
        tracker.close()


def test_AC39_5_user_workspace_without_value_prop_skips_cleanly(
    tmp_path: Path,
) -> None:
    """User workspace WITHOUT ``value-prop.md``: the scaffold
    completes (does not raise), the seed reports
    ``skipped_no_value_prop``, and no tracker DB rows are created."""
    workspace = tmp_path / "ws-user-empty"
    workspace.mkdir()
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"

    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )

    assert result.tracker_classification == "user"
    assert result.tracker_seeded is False
    assert result.tracker_seed_reason == "skipped_no_value_prop"
    assert result.tracker_root_id is None
    assert result.tracker_descendants_seeded == ()
    assert result.tracker_value_prop_source is None

    # Tracker DB may exist as an empty file (sqlite3 connect creates
    # the file) — but no records inside it.
    db_path = tracker_db_path_for(workspace)
    if db_path.exists():
        tracker = ObjectiveTracker(db_path)
        try:
            assert tracker.get(ROOT_OBJECTIVE_ID) is None
        finally:
            tracker.close()


def test_AC39_5_no_framework_content_in_user_workspace_tree(
    tmp_path: Path,
) -> None:
    """A user workspace with its own value-prop.md does NOT inherit
    Luke's framework value-prop content. The seeded root's goal +
    criteria must reference the user's content, not the framework's."""
    workspace = tmp_path / "ws-user-isolation"
    workspace.mkdir()
    user_text = (
        "# My Workspace\n\nI track home renovation projects with "
        "structured AI assistance.\n\n## Primary-persona test\n\n"
        "Does this help me get my hands dirty faster?\n\n"
        "## Harness test\n\nDoes this give me more workshop primitives?\n"
    )
    (workspace / WORKSPACE_VALUE_PROP_RELPATH).write_text(user_text)
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"

    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )

    tracker = ObjectiveTracker(tracker_db_path_for(workspace))
    try:
        root = tracker.get(ROOT_OBJECTIVE_ID)
        assert root is not None
        # Framework content sentinels — must NOT appear in user
        # workspace's tree.
        framework_sentinels = [
            "translation layer",
            "Captured 2026-04-21",
            "12-hour example",
        ]
        haystack = " ".join(
            [root.goal]
            + [c.prose for c in root.acceptance_criteria if c.kind == "prose"]
        )
        for sentinel in framework_sentinels:
            assert sentinel not in haystack, (
                f"framework value-prop sentinel {sentinel!r} leaked into "
                "user workspace's tracker tree — D-4 (b) breach"
            )
        # User content sentinels — must appear (in the goal H1 or
        # in the AC.PO.1 / AC.PO.2 prose extracted from the user's
        # file).
        full_root_text = " ".join(
            [root.goal]
            + [c.prose for c in root.acceptance_criteria if c.kind == "prose"]
        ).lower()
        assert (
            "renovation" in full_root_text
            or "workshop" in full_root_text
            or "hands dirty" in full_root_text
            or "my workspace" in full_root_text
        ), (
            f"user-supplied content not surfaced in seeded root; "
            f"goal={root.goal!r}, prose={[c.prose for c in root.acceptance_criteria]!r}"
        )
    finally:
        tracker.close()


def test_AC39_5_re_run_after_value_prop_supplied_completes_seed(
    tmp_path: Path,
) -> None:
    """A user workspace that initially boots without value-prop.md
    (skipped seed), then has the file supplied, completes the seed
    on the next direct ``seed_tracker`` invocation. Demonstrates the
    'workspace user supplies content' lifecycle isn't a one-shot."""
    import asyncio
    from loam.workspace_bootstrap.adapters.tracker_seed import (
        load_value_prop_source,
        seed_tracker,
    )

    workspace = tmp_path / "ws-supplied-late"
    workspace.mkdir()
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"

    # First scaffold: no value-prop.md → skipped.
    result_pre = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )
    assert result_pre.tracker_seed_reason == "skipped_no_value_prop"

    # User now supplies value-prop.md.
    (workspace / WORKSPACE_VALUE_PROP_RELPATH).write_text(_SAMPLE_USER_VALUE_PROP)

    # Re-invoke seed_tracker directly — scaffold's main path won't
    # re-run (already_scaffolded short-circuit), but the seed runner
    # is callable on its own.
    classification = classify_workspace(workspace)
    vp = load_value_prop_source(workspace, classification)
    db_path = tracker_db_path_for(workspace)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    result_post = asyncio.run(
        seed_tracker(
            workspace_root=workspace,
            tracker_db_path=db_path,
            classification=classification,
            value_prop=vp,
        )
    )
    assert result_post.reason == "fresh_seed"
    assert result_post.value_prop_source == WORKSPACE_VALUE_PROP_RELPATH
