"""D1 — manifest schema + round-trip tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from loam.self_upgrade.manifest import (
    BreakingChange,
    ChangeKind,
    ComponentSchema,
    FileEntry,
    Manifest,
    Migration,
    load_manifest,
    save_manifest,
    sha256_of_bytes,
    sha256_of_file,
    verify_file_against,
)


def test_manifest_round_trip_yaml(tmp_path: Path, sample_manifest_dict: dict) -> None:
    m = Manifest.model_validate(sample_manifest_dict)
    p = tmp_path / "pos-release.yml"
    save_manifest(m, p)
    reloaded = load_manifest(p)
    assert reloaded == m
    assert reloaded.release_tag == "pos-v2-v0.2.0"
    assert len(reloaded.files) == 4


def test_manifest_rejects_malformed_tag(sample_manifest_dict: dict) -> None:
    sample_manifest_dict["release_tag"] = "v1.0.0"
    with pytest.raises(ValidationError):
        Manifest.model_validate(sample_manifest_dict)


def test_file_entry_rejects_inconsistent_new(sample_manifest_dict: dict) -> None:
    sample_manifest_dict["files"][1]["expected_pre_sha"] = "a" * 64
    with pytest.raises(ValidationError):
        Manifest.model_validate(sample_manifest_dict)


def test_file_entry_rejects_inconsistent_modified(sample_manifest_dict: dict) -> None:
    # MODIFIED with equal pre/post shas is rejected
    sample_manifest_dict["files"][0]["expected_post_sha"] = "a" * 64
    with pytest.raises(ValidationError):
        Manifest.model_validate(sample_manifest_dict)


def test_file_entry_rejects_bad_sha(sample_manifest_dict: dict) -> None:
    sample_manifest_dict["files"][0]["expected_pre_sha"] = "xyz"
    with pytest.raises(ValidationError):
        Manifest.model_validate(sample_manifest_dict)


def test_silent_schema_bump_detected(sample_manifest_dict: dict) -> None:
    # Bump memory schema but do not declare a breaking change
    sample_manifest_dict["component_schemas"][0]["version_post"] = 4
    m = Manifest.model_validate(sample_manifest_dict)
    assert m.silent_schema_bumps() == ["memory"]


def test_declared_schema_bump_not_silent(sample_manifest_dict: dict) -> None:
    sample_manifest_dict["component_schemas"][0]["version_post"] = 4
    sample_manifest_dict["breaking_changes"] = [
        {
            "id": "mem-v4",
            "component": "memory",
            "description": "node identity normalisation",
            "migration_path": "framework/memory_system/migrations/v3_to_v4.py",
        }
    ]
    m = Manifest.model_validate(sample_manifest_dict)
    assert m.silent_schema_bumps() == []


def test_migration_duplicate_order_rejected(sample_manifest_dict: dict) -> None:
    sample_manifest_dict["migrations"] = [
        {
            "id": "m1",
            "component": "memory",
            "order": 1,
            "entry": "pkg.mod:fn",
        },
        {
            "id": "m2",
            "component": "memory",
            "order": 1,
            "entry": "pkg.mod:fn2",
        },
    ]
    with pytest.raises(ValidationError):
        Manifest.model_validate(sample_manifest_dict)


def test_sha256_of_file(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    p.write_bytes(b"hello world\n")
    assert sha256_of_file(p) == sha256_of_bytes(b"hello world\n")


def test_verify_file_against_match(tmp_path: Path, write_file_sha) -> None:
    root = tmp_path / "live"
    sha = write_file_sha(root / "framework/a.py", b"print('hi')\n")
    entry = FileEntry(
        path="framework/a.py",
        expected_pre_sha=None,
        expected_post_sha=sha,
        change_kind=ChangeKind.NEW,
    )
    matches, actual = verify_file_against(entry, root)
    assert matches is True
    assert actual == sha


def test_verify_file_against_mismatch(tmp_path: Path, write_file_sha) -> None:
    root = tmp_path / "live"
    write_file_sha(root / "framework/a.py", b"different\n")
    entry = FileEntry(
        path="framework/a.py",
        expected_pre_sha=None,
        expected_post_sha="a" * 64,
        change_kind=ChangeKind.NEW,
    )
    matches, actual = verify_file_against(entry, root)
    assert matches is False
    assert actual is not None
    assert actual != "a" * 64


def test_verify_file_against_deleted_absent(tmp_path: Path) -> None:
    root = tmp_path / "live"
    root.mkdir()
    entry = FileEntry(
        path="framework/gone.py",
        expected_pre_sha="a" * 64,
        expected_post_sha=None,
        change_kind=ChangeKind.DELETED,
    )
    matches, actual = verify_file_against(entry, root)
    assert matches is True
    assert actual is None


def test_file_by_path_lookup(sample_manifest_dict: dict) -> None:
    m = Manifest.model_validate(sample_manifest_dict)
    assert m.file_by_path("framework/self_upgrade/cli.py") is not None
    assert m.file_by_path("framework/nonexistent.py") is None
