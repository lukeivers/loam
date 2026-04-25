"""Amendment #39 — AC39.2 — Seeded root + every descendant carry
``authored_by == "user"``.

Plan §4 AC39.2 outcomes:

- Every record produced by the seed has ``authored_by == "user"``.
- ``trace_to_root(<any seeded descendant>)`` returns a chain whose
  terminal ancestor is the value-prop root and whose every link's
  ``authored_by == "user"``.
- No record produced by the seed has ``authored_by`` set to any
  other value (no ``"primary-persona"``, no ``"workspace-bootstrap"``).

Maps to objective-tracker D2 (user-authored-root invariant) + D4
(``bind_scope`` enforcement) → AC.PO.1.
"""

from __future__ import annotations

from pathlib import Path

from objective_tracker import ObjectiveTracker

from workspace_bootstrap.adapters.first_run_scaffold import (
    run_first_run_scaffold,
)
from workspace_bootstrap.adapters.tracker_seed import (
    FRAMEWORK_VALUE_PROP_RELPATH,
    ROOT_OBJECTIVE_ID,
    _SPEC_TIER_PHASES,
    tracker_db_path_for,
)


def _seed_dev(tmp_path: Path) -> Path:
    workspace = tmp_path / "ws-auth"
    workspace.mkdir()
    (workspace / "docs" / "rebuild").mkdir(parents=True)
    framework_vp = (
        Path(__file__).resolve().parent.parent.parent
        / "docs"
        / "rebuild"
        / "VALUE_PROPOSITION.md"
    )
    (workspace / FRAMEWORK_VALUE_PROP_RELPATH).write_text(
        framework_vp.read_text()
    )
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )
    return pos_root


def test_AC39_2_every_seeded_record_authored_by_user(tmp_path: Path) -> None:
    """Enumerate every seeded record via the tracker — each carries
    ``authored_by == "user"``."""
    pos_root = _seed_dev(tmp_path)
    tracker = ObjectiveTracker(tracker_db_path_for(pos_root))
    try:
        ids_to_check = [ROOT_OBJECTIVE_ID] + [
            f"spec-{suffix}" for suffix, _, _ in _SPEC_TIER_PHASES
        ]
        for oid in ids_to_check:
            proj = tracker.get(oid)
            assert proj is not None, f"{oid} missing"
            assert proj.authored_by == "user", (
                f"{oid} authored_by = {proj.authored_by!r} (expected 'user')"
            )
    finally:
        tracker.close()


def test_AC39_2_trace_to_root_chain_every_link_user(tmp_path: Path) -> None:
    """For each seeded descendant, the trace_to_root chain terminates
    at the value-prop root and every link is user-authored."""
    pos_root = _seed_dev(tmp_path)
    tracker = ObjectiveTracker(tracker_db_path_for(pos_root))
    try:
        for suffix, _, _ in _SPEC_TIER_PHASES:
            chain = tracker.trace_to_root(f"spec-{suffix}")
            assert chain[-1].objective_id == ROOT_OBJECTIVE_ID
            for link in chain:
                assert link.authored_by == "user", (
                    f"link {link.objective_id} authored_by = "
                    f"{link.authored_by!r}; expected 'user'"
                )
    finally:
        tracker.close()


def test_AC39_2_no_record_has_persona_or_bootstrap_authored_by(
    tmp_path: Path,
) -> None:
    """Cross-check: no seeded record has ``authored_by`` set to any
    persona handle or to ``"workspace-bootstrap"`` — the seed is the
    user's authoring action structurally, not the framework's."""
    pos_root = _seed_dev(tmp_path)
    tracker = ObjectiveTracker(tracker_db_path_for(pos_root))
    try:
        all_recs = tracker.list()
        forbidden = {"primary-persona", "workspace-bootstrap", "primary"}
        for proj in all_recs:
            assert proj.authored_by not in forbidden, (
                f"{proj.objective_id} authored_by = {proj.authored_by!r} "
                f"(forbidden by AC39.2)"
            )
    finally:
        tracker.close()
