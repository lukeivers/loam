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

"""AC.WS.1 — canonical-as-source resolver tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_sync.canonical import (
    CanonicalPullError,
    CanonicalResolution,
    resolve_canonical,
)


def test_resolves_head_to_full_sha(make_canonical_repo) -> None:
    canonical = make_canonical_repo({"a.txt": "alpha"})
    res = resolve_canonical(canonical, ref="HEAD")
    assert isinstance(res, CanonicalResolution)
    assert res.canonical_path == canonical
    # rev-parse HEAD returns 40-char SHA.
    assert len(res.ref) == 40
    assert res.ref != "HEAD"


def test_missing_canonical_raises(tmp_path: Path) -> None:
    with pytest.raises(CanonicalPullError, match="does not exist"):
        resolve_canonical(tmp_path / "nope")


def test_canonical_must_be_directory(tmp_path: Path) -> None:
    f = tmp_path / "file"
    f.write_text("x")
    with pytest.raises(CanonicalPullError, match="must be a directory"):
        resolve_canonical(f)


def test_canonical_without_dot_git_rejected(tmp_path: Path) -> None:
    d = tmp_path / "no-git"
    d.mkdir()
    with pytest.raises(CanonicalPullError, match="not a git working tree"):
        resolve_canonical(d)


def test_unknown_ref_rejected(make_canonical_repo) -> None:
    canonical = make_canonical_repo({"a.txt": "alpha"})
    with pytest.raises(CanonicalPullError, match="rev-parse"):
        resolve_canonical(canonical, ref="nonexistent-ref")
