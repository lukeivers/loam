"""AC.COMPINT.7 — Persistence at canonical workspace path.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.7:

- Persisted at ``<extraction_dir>/augmented-objectives.yaml``
  (mirrors v0.2.3 backing-map.yaml convention).
- Atomic tmp+rename.
- Round-trip via ``model_dump`` / ``model_validate``.
- Idempotent on no-change (re-write produces same content).
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import yaml

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
    augmented_objectives_path,
    load_augmented_objectives,
    save_augmented_objectives,
)


def _make_obj(idx: int = 1) -> Objective:
    return Objective(
        objective_id=f"O.dispute-flow.{idx}",
        text=f"Operators file refund disputes against merchant portals (variant {idx}).",
        confidence=ConfidenceBand.PLAUSIBLE,
        domain="dispute-flow",
        evidence=ObjectiveEvidence(
            readme_excerpts=["File refunds at scale"],
        ),
    )


def _set(ext_dir: Path, objs: list[Objective]) -> AugmentedObjectiveSet:
    return AugmentedObjectiveSet(
        extraction_id="repo-1",
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=objs,
    )


def test_save_writes_to_canonical_path(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    aug = _set(ext_dir, [_make_obj(1)])
    written = save_augmented_objectives(aug, ext_dir)
    expected = ext_dir / "augmented-objectives.yaml"
    assert written == expected
    assert expected.exists()


def test_augmented_objectives_path_helper_mirrors_save_path(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    assert augmented_objectives_path(ext_dir) == ext_dir / "augmented-objectives.yaml"


def test_round_trip_via_load(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    aug = _set(ext_dir, [_make_obj(1), _make_obj(2)])
    save_augmented_objectives(aug, ext_dir)
    loaded = load_augmented_objectives(ext_dir)
    assert loaded is not None
    assert loaded.extraction_id == "repo-1"
    assert len(loaded.objectives) == 2
    assert loaded.objectives[0].objective_id == "O.dispute-flow.1"


def test_load_returns_none_when_file_absent(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    assert load_augmented_objectives(ext_dir) is None


def test_save_does_not_leave_tmp_files_on_success(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    aug = _set(ext_dir, [_make_obj(1)])
    save_augmented_objectives(aug, ext_dir)
    leftover = list(ext_dir.glob("augmented-objectives.yaml.*.tmp"))
    assert leftover == []


def test_idempotent_no_change_yields_same_content(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    aug = _set(ext_dir, [_make_obj(1)])
    save_augmented_objectives(aug, ext_dir)
    first = (ext_dir / "augmented-objectives.yaml").read_text(encoding="utf-8")
    # Save again with same data + same augmented_at → byte-identical.
    save_augmented_objectives(aug, ext_dir)
    second = (ext_dir / "augmented-objectives.yaml").read_text(encoding="utf-8")
    assert first == second


def test_persisted_yaml_carries_schema_version(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    aug = _set(ext_dir, [_make_obj(1)])
    save_augmented_objectives(aug, ext_dir)
    raw = yaml.safe_load(
        (ext_dir / "augmented-objectives.yaml").read_text(encoding="utf-8")
    )
    assert raw["schema_version"] == 1
    assert "extraction_id" in raw
    assert "augmented_at" in raw
    assert "interview_audit_path" in raw
    assert isinstance(raw["objectives"], list)
