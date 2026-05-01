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

"""Clause-(h) AC.H.1 — canonical-as-source pull adapter tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from loam.self_upgrade.canonical import (
    CanonicalPullError,
    default_manifest_path,
    resolve_canonical_to_staging,
)
from loam.self_upgrade.cli import build_parser


def _make_canonical(root: Path, tag: str = "pos-v2-v0.2.0") -> Path:
    """Build a minimal canonical tree with a manifest at the conventional
    location: <root>/self-upgrade/manifests/<tag>.yaml"""
    root.mkdir(parents=True, exist_ok=True)
    (root / ".git").mkdir()  # marker for is-git-tree check
    manifest_dir = root / "self-upgrade" / "manifests"
    manifest_dir.mkdir(parents=True)
    manifest_path = manifest_dir / f"{tag}.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "release_tag": tag,
                "commit_sha": "abc1234",
                "files": [],
                "component_schemas": [],
                "breaking_changes": [],
                "migrations": [],
            }
        )
    )
    return root


def test_resolve_canonical_basic(tmp_path: Path) -> None:
    canonical = _make_canonical(tmp_path / "canonical")
    res = resolve_canonical_to_staging(canonical, tag="pos-v2-v0.2.0")
    assert res.staging_dir == canonical
    assert res.manifest.release_tag == "pos-v2-v0.2.0"
    assert res.manifest_path == default_manifest_path(canonical, "pos-v2-v0.2.0")


def test_resolve_canonical_explicit_manifest(tmp_path: Path) -> None:
    canonical = _make_canonical(tmp_path / "canonical")
    # Move the manifest to a custom location.
    custom = tmp_path / "alt-manifest.yaml"
    custom.write_text(
        yaml.safe_dump(
            {
                "release_tag": "pos-v2-v0.3.0",
                "commit_sha": "deadbeef",
                "files": [],
                "component_schemas": [],
                "breaking_changes": [],
                "migrations": [],
            }
        )
    )
    res = resolve_canonical_to_staging(
        canonical, tag="pos-v2-v0.3.0", manifest_path=custom
    )
    assert res.manifest.release_tag == "pos-v2-v0.3.0"


def test_resolve_canonical_missing_path(tmp_path: Path) -> None:
    with pytest.raises(CanonicalPullError, match="does not exist"):
        resolve_canonical_to_staging(
            tmp_path / "nope", tag="pos-v2-v0.2.0"
        )


def test_resolve_canonical_not_git_tree(tmp_path: Path) -> None:
    bare = tmp_path / "no-git"
    bare.mkdir()
    with pytest.raises(CanonicalPullError, match="not a git working tree"):
        resolve_canonical_to_staging(bare, tag="pos-v2-v0.2.0")


def test_resolve_canonical_manifest_missing(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    (canonical / ".git").mkdir()
    with pytest.raises(CanonicalPullError, match="manifest not found"):
        resolve_canonical_to_staging(canonical, tag="pos-v2-v0.2.0")


def test_resolve_canonical_tag_mismatch(tmp_path: Path) -> None:
    """Manifest exists at the requested tag's location but its
    declared release_tag disagrees with the CLI tag."""
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    (canonical / ".git").mkdir()
    manifest_dir = canonical / "self-upgrade" / "manifests"
    manifest_dir.mkdir(parents=True)
    # Write at the location for "pos-v2-v0.9.9" but declare a
    # different release_tag inside.
    (manifest_dir / "pos-v2-v0.9.9.yaml").write_text(
        yaml.safe_dump(
            {
                "release_tag": "pos-v2-v0.2.0",  # disagrees with cli tag
                "commit_sha": "abc1234",
                "files": [],
                "component_schemas": [],
                "breaking_changes": [],
                "migrations": [],
            }
        )
    )
    with pytest.raises(CanonicalPullError, match="disagrees"):
        resolve_canonical_to_staging(canonical, tag="pos-v2-v0.9.9")


def test_argparse_mutex_canonical_xor_staging() -> None:
    """AC.H.1: --canonical and --staging-dir are mutually exclusive."""
    parser = build_parser()
    # Both supplied → error.
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "upgrade",
                "pos-v2-v0.2.0",
                "--canonical",
                "/tmp/x",
                "--staging-dir",
                "/tmp/y",
            ]
        )
    # Neither supplied → error (required=True on the mutex group).
    with pytest.raises(SystemExit):
        parser.parse_args(["upgrade", "pos-v2-v0.2.0"])
    # Just --canonical → ok.
    args = parser.parse_args(
        ["upgrade", "pos-v2-v0.2.0", "--canonical", "/tmp/x"]
    )
    assert args.canonical == "/tmp/x"
    assert args.staging_dir is None
    # Just --staging-dir → ok.
    args = parser.parse_args(
        [
            "upgrade",
            "pos-v2-v0.2.0",
            "--staging-dir",
            "/tmp/s",
            "--manifest",
            "/tmp/m.yaml",
        ]
    )
    assert args.staging_dir == "/tmp/s"
    assert args.canonical is None


def test_argparse_backward_compat_staging_dir_only() -> None:
    """Hard Constraint #5: legacy --staging-dir invocation is unchanged."""
    parser = build_parser()
    args = parser.parse_args(
        [
            "upgrade",
            "pos-v2-v0.2.0",
            "--staging-dir",
            "/tmp/s",
            "--manifest",
            "/tmp/m.yaml",
            "--prior-tag",
            "pos-v2-v0.1.0",
        ]
    )
    assert args.staging_dir == "/tmp/s"
    assert args.manifest == "/tmp/m.yaml"
    assert args.canonical is None
    assert args.merge_resolver_module is None  # opt-in
