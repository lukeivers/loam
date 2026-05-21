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

"""Bundle A.1 — workspace-sync just-behind fast-path tests.

Covers AC.JBC.{1, 2, 3} against the standalone
``is_just_behind`` module. AC.JBC.4 (integration with the CLI
resolver flow) lives in ``test_just_behind_integration.py``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam.workspace_sync.just_behind_check import is_just_behind


def _git(args: list[str], *, cwd: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _git_init(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(root)], check=True
    )
    _git(["config", "user.email", "t@t"], cwd=root)
    _git(["config", "user.name", "t"], cwd=root)
    _git(["config", "commit.gpgsign", "false"], cwd=root)


def _write_and_commit(
    root: Path, rel: str, content: str | bytes, *, message: str
) -> str:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        target.write_bytes(content)
    else:
        target.write_text(content)
    _git(["add", "-A"], cwd=root)
    _git(["commit", "-q", "-m", message], cwd=root)
    return _git(["rev-parse", "HEAD"], cwd=root)


# ---- AC.JBC.1 — true-positive --------------------------------------


def test_AC_JBC_1_workspace_content_matches_ancestor_returns_true(
    tmp_path: Path,
):
    """When workspace_content byte-equals an ancestor commit's blob,
    ``is_just_behind`` returns ``(True, ancestor_sha)``."""
    repo = tmp_path / "repo"
    _git_init(repo)
    sha_v1 = _write_and_commit(
        repo, "src/foo.py", "x = 1\n", message="v1"
    )
    _write_and_commit(repo, "src/foo.py", "x = 2\n", message="v2")
    head_sha = _write_and_commit(
        repo, "src/foo.py", "x = 3\n", message="v3"
    )

    # Workspace content equals v1's bytes — that's an ancestor of HEAD.
    matched, ancestor = is_just_behind(
        repo, "src/foo.py", b"x = 1\n", head_sha
    )
    assert matched is True
    assert ancestor == sha_v1


def test_AC_JBC_1_match_at_head_itself_returns_true(tmp_path: Path):
    """Match at the head commit also counts (degenerate ancestor —
    HEAD is reachable from HEAD)."""
    repo = tmp_path / "repo"
    _git_init(repo)
    _write_and_commit(repo, "src/foo.py", "x = 1\n", message="v1")
    head_sha = _write_and_commit(
        repo, "src/foo.py", "x = 2\n", message="v2"
    )

    matched, ancestor = is_just_behind(
        repo, "src/foo.py", b"x = 2\n", head_sha
    )
    assert matched is True
    assert ancestor == head_sha


def test_AC_JBC_1_binary_content_matches_via_bytes_compare(
    tmp_path: Path,
):
    """Byte-level comparison is encoding-agnostic: a NUL-containing
    payload that matches an ancestor blob still returns True."""
    repo = tmp_path / "repo"
    _git_init(repo)
    binary_payload = b"\x00\x01\x02\x03 mixed \xff payload\n"
    sha_v1 = _write_and_commit(
        repo, "data.bin", binary_payload, message="v1"
    )
    head_sha = _write_and_commit(
        repo, "data.bin", b"different\x00bytes\n", message="v2"
    )

    matched, ancestor = is_just_behind(
        repo, "data.bin", binary_payload, head_sha
    )
    assert matched is True
    assert ancestor == sha_v1


# ---- AC.JBC.2 — true-negative --------------------------------------


def test_AC_JBC_2_workspace_content_matches_nothing_returns_false(
    tmp_path: Path,
):
    """When the workspace content equals nothing in canonical's
    history for the file, ``is_just_behind`` returns ``(False, None)``."""
    repo = tmp_path / "repo"
    _git_init(repo)
    _write_and_commit(repo, "src/foo.py", "x = 1\n", message="v1")
    head_sha = _write_and_commit(
        repo, "src/foo.py", "x = 2\n", message="v2"
    )

    # "x = 999\n" was never canonical content.
    matched, ancestor = is_just_behind(
        repo, "src/foo.py", b"x = 999  # workspace-divergent\n", head_sha
    )
    assert matched is False
    assert ancestor is None


def test_AC_JBC_2_file_never_in_canonical_history_returns_false(
    tmp_path: Path,
):
    """When the file path never appeared in canonical's history (e.g.,
    it's a workspace-only artefact), ``is_just_behind`` returns False."""
    repo = tmp_path / "repo"
    _git_init(repo)
    head_sha = _write_and_commit(
        repo, "README.md", "# repo\n", message="seed"
    )

    matched, ancestor = is_just_behind(
        repo, "workspace-only/never-seen.txt", b"anything\n", head_sha
    )
    assert matched is False
    assert ancestor is None


def test_AC_JBC_2_empty_workspace_content_against_nonempty_history(
    tmp_path: Path,
):
    """Empty workspace bytes vs a history of non-empty file versions
    returns False (no degenerate empty-match)."""
    repo = tmp_path / "repo"
    _git_init(repo)
    _write_and_commit(repo, "src/foo.py", "x = 1\n", message="v1")
    head_sha = _write_and_commit(
        repo, "src/foo.py", "x = 2\n", message="v2"
    )

    matched, ancestor = is_just_behind(
        repo, "src/foo.py", b"", head_sha
    )
    assert matched is False
    assert ancestor is None


# ---- AC.JBC.3 — bounded depth --------------------------------------


def test_AC_JBC_3_walk_honors_max_depth(tmp_path: Path):
    """When the file's canonical history is longer than ``max_depth``
    and the matching ancestor is OUTSIDE the bounded window, the walk
    returns ``(False, None)`` rather than walking indefinitely.

    Constructs a 20-commit history of distinct contents; sets
    ``max_depth=5``; targets a match at commit #1 (the oldest). The
    walk inspects only the 5 most-recent commits and reports no
    match within the window.
    """
    repo = tmp_path / "repo"
    _git_init(repo)
    target_payload = b"x = 1  # oldest content\n"
    _write_and_commit(repo, "src/foo.py", target_payload, message="v01")
    for i in range(2, 21):
        head_sha = _write_and_commit(
            repo,
            "src/foo.py",
            f"x = {i}  # v{i:02d}\n",
            message=f"v{i:02d}",
        )

    # Sanity check: with unbounded depth (200 default), the match IS
    # found — confirms the target is reachable, just outside the
    # narrowed window.
    matched_default, _ = is_just_behind(
        repo, "src/foo.py", target_payload, head_sha
    )
    assert matched_default is True

    # With max_depth=5, the walk should NOT reach commit #1.
    matched_narrow, ancestor = is_just_behind(
        repo, "src/foo.py", target_payload, head_sha, max_depth=5
    )
    assert matched_narrow is False
    assert ancestor is None


def test_AC_JBC_3_default_depth_is_200(tmp_path: Path):
    """Default ``max_depth`` is 200; with a 250-commit history, a
    match at commit #1 lies outside the default window and returns
    False unless callers raise the limit."""
    repo = tmp_path / "repo"
    _git_init(repo)
    target_payload = b"target = 'oldest'\n"
    _write_and_commit(repo, "deep.txt", target_payload, message="v001")
    # 249 advancing commits → history of 250 total. Default window
    # of 200 cannot reach commit #1.
    for i in range(2, 251):
        head_sha = _write_and_commit(
            repo,
            "deep.txt",
            f"v{i:03d}\n",
            message=f"v{i:03d}",
        )

    matched, ancestor = is_just_behind(
        repo, "deep.txt", target_payload, head_sha
    )
    assert matched is False
    assert ancestor is None

    # Raising the cap finds it.
    matched_wide, ancestor_wide = is_just_behind(
        repo, "deep.txt", target_payload, head_sha, max_depth=300
    )
    assert matched_wide is True
    assert ancestor_wide is not None


def test_AC_JBC_3_within_depth_finds_recent_match(tmp_path: Path):
    """When the match lies WITHIN the bounded window, the walk
    correctly returns True even when ``max_depth`` is set tight."""
    repo = tmp_path / "repo"
    _git_init(repo)
    _write_and_commit(repo, "src/foo.py", "x = 1\n", message="v1")
    sha_v2 = _write_and_commit(
        repo, "src/foo.py", "x = 2\n", message="v2"
    )
    head_sha = _write_and_commit(
        repo, "src/foo.py", "x = 3\n", message="v3"
    )

    matched, ancestor = is_just_behind(
        repo, "src/foo.py", b"x = 2\n", head_sha, max_depth=2
    )
    assert matched is True
    assert ancestor == sha_v2
