"""Paths resolution tests."""

from __future__ import annotations

import os
from pathlib import Path

from loam.self_upgrade.paths import Paths


def test_env_override(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    assert p.base == tmp_path.resolve()
    assert p.framework == tmp_path / "framework"
    assert p.current_link == tmp_path / "framework" / "current"
    assert p.releases == tmp_path / "framework" / "releases"
    assert p.staging == tmp_path / "framework" / "staging"
    assert p.history == tmp_path / "framework" / "history"
    assert p.upgrade_config == tmp_path / "upgrade-config.yaml"


def test_tag_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    tag = "pos-v2-v0.2.0"
    assert p.history_dir_pre(tag).name == f"{tag}-pre"
    assert p.conflicts_yaml(tag).name == f"{tag}-conflicts.yaml"
    assert p.accepted_json(tag).name == f"{tag}-accepted.json"
    assert p.pre_probe_json(tag) == p.history_dir_pre(tag) / "pre-probe.json"


def test_ensure_history(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    p.ensure_history("pos-v2-v0.2.0")
    assert p.history_dir_pre("pos-v2-v0.2.0").is_dir()
