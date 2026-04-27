"""Pre-install conflict detection tests (clause g operational path)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from self_upgrade.conflict_detection import detect_conflicts
from self_upgrade.conflict_report import (
    ConflictChangeKind,
    Resolution,
)
from self_upgrade.manifest import Manifest


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _build_manifest(files: list[dict], tag: str = "pos-v2-v0.2.0") -> Manifest:
    return Manifest.model_validate(
        {"release_tag": tag, "commit_sha": "abcdef1", "files": files}
    )


def test_clean_new_file_goes_to_will_update_cleanly(tmp_path: Path) -> None:
    live = tmp_path / "live"
    live.mkdir()
    content = b"new file\n"
    m = _build_manifest([
        {
            "path": "framework/new.py",
            "expected_pre_sha": None,
            "expected_post_sha": _sha(content),
            "change_kind": "new",
        }
    ])
    report = detect_conflicts(m, live)
    assert report.summary.will_update_cleanly == 1
    assert report.summary.conflicts_requiring_resolution == 0


def test_auto_accept_when_local_matches_upstream_new(tmp_path: Path) -> None:
    live = tmp_path / "live"
    (live / "framework").mkdir(parents=True)
    content = b"already matches\n"
    (live / "framework" / "new.py").write_bytes(content)
    m = _build_manifest([
        {
            "path": "framework/new.py",
            "expected_pre_sha": None,
            "expected_post_sha": _sha(content),
            "change_kind": "new",
        }
    ])
    report = detect_conflicts(m, live)
    assert report.summary.auto_resolved == 1
    assert report.conflicts[0].resolution is Resolution.AUTO_ACCEPT_LOCAL_MATCHES_UPSTREAM


def test_local_modified_triggers_pending_conflict(tmp_path: Path) -> None:
    live = tmp_path / "live"
    (live / "framework").mkdir(parents=True)
    pre = b"prior release\n"
    upstream = b"upstream new\n"
    local = b"local edit\n"
    (live / "framework" / "a.py").write_bytes(local)
    m = _build_manifest([
        {
            "path": "framework/a.py",
            "expected_pre_sha": _sha(pre),
            "expected_post_sha": _sha(upstream),
            "change_kind": "modified",
        }
    ])
    report = detect_conflicts(m, live)
    assert report.summary.conflicts_requiring_resolution == 1
    c = report.conflicts[0]
    assert c.resolution is Resolution.PENDING
    assert c.change_kind is ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED


def test_local_modified_matching_upstream_auto_resolves(tmp_path: Path) -> None:
    live = tmp_path / "live"
    (live / "framework").mkdir(parents=True)
    pre = b"prior release\n"
    upstream = b"upstream new\n"
    (live / "framework" / "a.py").write_bytes(upstream)
    m = _build_manifest([
        {
            "path": "framework/a.py",
            "expected_pre_sha": _sha(pre),
            "expected_post_sha": _sha(upstream),
            "change_kind": "modified",
        }
    ])
    report = detect_conflicts(m, live)
    assert report.summary.auto_resolved == 1
    assert report.conflicts[0].resolution is Resolution.AUTO_ACCEPT_LOCAL_MATCHES_UPSTREAM


def test_modified_matching_pre_is_clean_update(tmp_path: Path) -> None:
    live = tmp_path / "live"
    (live / "framework").mkdir(parents=True)
    pre = b"prior release\n"
    upstream = b"upstream new\n"
    (live / "framework" / "a.py").write_bytes(pre)
    m = _build_manifest([
        {
            "path": "framework/a.py",
            "expected_pre_sha": _sha(pre),
            "expected_post_sha": _sha(upstream),
            "change_kind": "modified",
        }
    ])
    report = detect_conflicts(m, live)
    assert report.summary.will_update_cleanly == 1
    assert report.summary.conflicts_requiring_resolution == 0


def test_deleted_file_still_present_with_local_edit(tmp_path: Path) -> None:
    live = tmp_path / "live"
    (live / "framework").mkdir(parents=True)
    pre = b"old\n"
    local = b"user kept this file with edits\n"
    (live / "framework" / "gone.py").write_bytes(local)
    m = _build_manifest([
        {
            "path": "framework/gone.py",
            "expected_pre_sha": _sha(pre),
            "expected_post_sha": None,
            "change_kind": "deleted",
        }
    ])
    report = detect_conflicts(m, live)
    assert report.summary.conflicts_requiring_resolution == 1
    assert report.conflicts[0].resolution is Resolution.PENDING


def test_unchanged_file_with_local_edit_is_conflict(tmp_path: Path) -> None:
    live = tmp_path / "live"
    (live / "framework").mkdir(parents=True)
    orig = b"unchanged between releases\n"
    local = b"but user edited it\n"
    (live / "framework" / "a.py").write_bytes(local)
    m = _build_manifest([
        {
            "path": "framework/a.py",
            "expected_pre_sha": _sha(orig),
            "expected_post_sha": _sha(orig),
            "change_kind": "unchanged",
        }
    ])
    report = detect_conflicts(m, live)
    assert report.summary.conflicts_requiring_resolution == 1
    assert report.conflicts[0].change_kind is ConflictChangeKind.LOCAL_MODIFIED_ONLY
