"""AC.OBJRAT.6 — Substrate preservation: extend, do NOT replace.

- v1 → v2 migration on read with atomic .v1.bak backup.
- Fresh-write v2 has no backup.
- v0.1.8 BandedAC apply path still calls load/save cleanly.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    BandedAC,
    ConfidenceBand,
    Evidence,
    PendingTarget,
    RatificationStateV2,
    apply_ratification_action,
    initialise_ratification_state,
    load_ratification_state,
    promote,
    save_ratification_state,
)


def _write_v1_state(extraction_dir: Path) -> Path:
    """Write a synthetic v0.1.8 (schema_version=1) state file."""
    extraction_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "extraction_id": "legacy-extraction",
        "draft_path": "contract-draft.md",
        "pm_handle": "legacy-pm",
        "pending_acs": ["AC.LEGACY.1", "AC.LEGACY.2"],
        "in_flight_action": None,
        "completed_actions": [],
        "created_at": "2026-04-01T00:00:00+00:00",
        "last_updated_at": "2026-04-01T00:00:00+00:00",
    }
    p = extraction_dir / "ratification-state.yaml"
    p.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return p


def test_v1_load_migrates_with_backup(tmp_path: Path) -> None:
    extraction_dir = tmp_path / "ext"
    state_path = _write_v1_state(extraction_dir)

    state = load_ratification_state(extraction_dir)
    assert state is not None
    assert isinstance(state, RatificationStateV2)
    # Migration populates altitude_index + pending_targets with banded_ac.
    assert state.altitude_index == {
        "AC.LEGACY.1": "banded_ac",
        "AC.LEGACY.2": "banded_ac",
    }
    targets = {pt.target_id: pt.altitude for pt in state.pending_targets}
    assert targets == {
        "AC.LEGACY.1": "banded_ac",
        "AC.LEGACY.2": "banded_ac",
    }
    # Backup written.
    backup = state_path.with_suffix(".yaml.v1.bak")
    assert backup.exists()
    backup_payload = yaml.safe_load(backup.read_text(encoding="utf-8"))
    assert backup_payload["schema_version"] == 1
    # Re-loaded payload is now v2.
    re_payload = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert re_payload["schema_version"] == 2


def test_fresh_v2_write_no_backup(tmp_path: Path) -> None:
    extraction_dir = tmp_path / "ext"
    state = initialise_ratification_state(
        extraction_dir,
        extraction_id="fresh",
        draft_path="contract-draft.md",
        pm_handle="fresh-pm",
        pending_acs=["AC.NEW.1"],
    )
    assert isinstance(state, RatificationStateV2)
    # No .v1.bak when fresh-writing v2.
    backup = extraction_dir / "ratification-state.yaml.v1.bak"
    assert not backup.exists()


def test_v1_apply_path_after_migration(tmp_path: Path) -> None:
    extraction_dir = tmp_path / ".loam" / "extractions" / "legacy"
    _write_v1_state(extraction_dir)
    # Now migrate via load.
    load_ratification_state(extraction_dir)

    # v1 apply path through promote() factory still works.
    banded = [
        BandedAC(
            ac_id="AC.LEGACY.1",
            text="legacy",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="r"),
        )
    ]
    apply_ratification_action(
        promote(
            ac_id="AC.LEGACY.1",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        ),
        banded_acs=banded,
        workspace_root=tmp_path,
        repo_id="legacy",
    )
    # Reload — AC.LEGACY.1 dropped from pending.
    state = load_ratification_state(extraction_dir)
    assert state is not None
    assert "AC.LEGACY.1" not in state.pending_acs
    assert "AC.LEGACY.1" not in [pt.target_id for pt in state.pending_targets]
    # AC.LEGACY.2 still present at banded_ac altitude.
    assert "AC.LEGACY.2" in [pt.target_id for pt in state.pending_targets]


def test_v2_round_trip_preserves_altitude_tags(tmp_path: Path) -> None:
    extraction_dir = tmp_path / "ext"
    extraction_dir.mkdir(parents=True)
    state = RatificationStateV2(
        extraction_id="t",
        draft_path="contract-draft.md",
        pm_handle="pm",
        pending_acs=[],
        in_flight_action=None,
        completed_actions=[],
        altitude_index={
            "O.alpha.1": "objective",
            "K.alpha.1": "constraint",
        },
        pending_targets=[
            PendingTarget(target_id="O.alpha.1", altitude="objective"),
            PendingTarget(target_id="K.alpha.1", altitude="constraint"),
        ],
        in_flight_target=None,
    )
    save_ratification_state(extraction_dir, state)
    loaded = load_ratification_state(extraction_dir)
    assert loaded is not None
    assert loaded.altitude_index["O.alpha.1"] == "objective"
    assert loaded.altitude_index["K.alpha.1"] == "constraint"
