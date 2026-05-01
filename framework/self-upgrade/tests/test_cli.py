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

"""D2 — CLI surface tests."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from loam.self_upgrade.cli import build_parser, main, refuse_if_invoked_from_live_path
from loam.self_upgrade.conflict_detection import detect_conflicts
from loam.self_upgrade.conflict_report import Resolution, save_conflict_report
from loam.self_upgrade.manifest import Manifest, save_manifest
from loam.self_upgrade.paths import Paths


def _make_manifest(tag: str, live_content: bytes | None = None) -> dict:
    files = []
    if live_content is not None:
        sha = hashlib.sha256(live_content).hexdigest()
        files.append(
            {
                "path": "framework/a.py",
                "expected_pre_sha": None,
                "expected_post_sha": sha,
                "change_kind": "new",
            }
        )
    return {
        "release_tag": tag,
        "commit_sha": "abcdef1234",
        "files": files,
    }


def test_parser_builds() -> None:
    p = build_parser()
    assert p.prog == "pos"


def test_status_runs(tmp_path: Path, capsys) -> None:
    rc = main(["--pos-base-dir", str(tmp_path), "status"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "current" in captured.out


def test_dry_run_prints_plan(tmp_path: Path, capsys) -> None:
    tag = "pos-v2-v0.2.0"
    manifest_path = tmp_path / "pos-release.yml"
    staging = tmp_path / "staging"
    staging.mkdir()

    manifest = Manifest.model_validate(_make_manifest(tag))
    save_manifest(manifest, manifest_path)

    rc = main(
        [
            "--pos-base-dir", str(tmp_path),
            "upgrade", tag,
            "--manifest", str(manifest_path),
            "--staging-dir", str(staging),
            "--dry-run",
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "dry-run" in captured.out
    assert tag in captured.out
    assert "files in manifest" in captured.out


def test_dry_run_warns_on_silent_schema_bump(tmp_path: Path, capsys) -> None:
    tag = "pos-v2-v0.2.0"
    manifest_path = tmp_path / "pos-release.yml"
    staging = tmp_path / "staging"
    staging.mkdir()

    d = _make_manifest(tag)
    d["component_schemas"] = [{"component": "memory", "version_pre": 3, "version_post": 4}]
    manifest = Manifest.model_validate(d)
    save_manifest(manifest, manifest_path)

    rc = main([
        "--pos-base-dir", str(tmp_path),
        "upgrade", tag,
        "--manifest", str(manifest_path),
        "--staging-dir", str(staging),
        "--dry-run",
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "silent schema bump" in captured.out.lower()


def test_tag_mismatch_rejected(tmp_path: Path, capsys) -> None:
    manifest_path = tmp_path / "pos-release.yml"
    staging = tmp_path / "staging"
    staging.mkdir()
    manifest = Manifest.model_validate(_make_manifest("pos-v2-v0.2.0"))
    save_manifest(manifest, manifest_path)

    rc = main([
        "--pos-base-dir", str(tmp_path),
        "upgrade", "pos-v2-v0.9.9",
        "--manifest", str(manifest_path),
        "--staging-dir", str(staging),
    ])
    assert rc == 2
    captured = capsys.readouterr()
    assert "disagrees" in captured.err


def test_conflicts_block_upgrade(tmp_path: Path, capsys) -> None:
    tag = "pos-v2-v0.2.0"
    manifest_path = tmp_path / "pos-release.yml"
    staging = tmp_path / "staging"
    staging.mkdir()

    # Build a live tree with a file whose sha doesn't match the manifest
    import os

    monkeypatch_base = tmp_path
    paths = Paths(tmp_path)
    prior = paths.release_dir("pos-v2-v0.1.0")
    prior.mkdir(parents=True)
    (prior / "framework").mkdir()
    (prior / "framework" / "a.py").write_bytes(b"local edit - not matching upstream\n")
    paths.current_link.parent.mkdir(parents=True, exist_ok=True)
    if paths.current_link.exists() or paths.current_link.is_symlink():
        paths.current_link.unlink()
    os.symlink(str(prior), str(paths.current_link))

    # Manifest says file should have sha of DIFFERENT content
    manifest = Manifest.model_validate(_make_manifest(tag, live_content=b"upstream new\n"))
    save_manifest(manifest, manifest_path)

    rc = main([
        "--pos-base-dir", str(tmp_path),
        "upgrade", tag,
        "--manifest", str(manifest_path),
        "--staging-dir", str(staging),
        "--prior-tag", "pos-v2-v0.1.0",
    ])
    assert rc == 3  # conflicts pending
    captured = capsys.readouterr()
    assert "upgrade blocked" in captured.out
    assert "skipped" in captured.out  # mentions the structural forbid
    # Conflict YAML was written
    assert paths.conflicts_yaml(tag).exists()


def test_refuse_when_invoked_from_live_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    paths = Paths.from_env()
    live = paths.release_dir("pos-v2-v0.1.0")
    live.mkdir(parents=True)
    paths.current_link.parent.mkdir(parents=True, exist_ok=True)
    if paths.current_link.exists() or paths.current_link.is_symlink():
        paths.current_link.unlink()
    os.symlink(str(live), str(paths.current_link))

    # Spoof sys.executable to live
    fake_exec = live / "bin" / "python"
    fake_exec.parent.mkdir(parents=True)
    fake_exec.write_bytes(b"#!/bin/sh\n")
    monkeypatch.setattr("sys.executable", str(fake_exec))

    err = refuse_if_invoked_from_live_path(paths)
    assert err is not None
    assert "live framework path" in err


def test_refuse_passes_when_invoked_externally(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    paths = Paths.from_env()
    live = paths.release_dir("pos-v2-v0.1.0")
    live.mkdir(parents=True)
    paths.current_link.parent.mkdir(parents=True, exist_ok=True)
    if paths.current_link.exists() or paths.current_link.is_symlink():
        paths.current_link.unlink()
    os.symlink(str(live), str(paths.current_link))
    # sys.executable remains the venv python — outside the live tree
    err = refuse_if_invoked_from_live_path(paths)
    assert err is None
