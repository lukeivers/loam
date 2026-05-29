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

"""AC.FBMW.1 — a write through the live caller lands at the single-
``workspace`` live queue location, not the doubled-``workspace`` shadow.

The bug (sweep PART B / B2): the hook callers resolved ``workspace_root``
from ``Path.cwd()``, which in the live session is the operator workspace
``<repo>/workspace/``; the resolver then appends its own ``workspace``
segment, producing ``<repo>/workspace/workspace/.pos/...`` — a dead
shadow the worker never reads. The caller-side fix (AC.FBMW.1) makes the
hook subcommands resolve the REPO ROOT so writer + worker agree on one
queue location.

This test exercises the caller chain (``cli._resolve_workspace`` →
``memory_write_queue.queue_dir``), asserting the resolved path contains
exactly ONE ``workspace`` segment.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from loam.primary_persona import cli
from loam.primary_persona.memory_write_queue import enqueue, queue_dir


def _count_workspace_segments(p: Path) -> int:
    return sum(1 for part in p.parts if part == "workspace")


def test_AC_FBMW_1_env_root_resolves_repo_root(monkeypatch, tmp_path):
    """LOAM_WORKSPACE_ROOT (the worker's canonical repo-root env) is the
    first-priority source; the resolved queue dir doubles nothing."""
    repo_root = tmp_path / "pos3"
    repo_root.mkdir()
    monkeypatch.setenv("LOAM_WORKSPACE_ROOT", str(repo_root))

    resolved = cli._resolve_workspace(None)
    assert resolved == repo_root

    qdir = queue_dir(resolved)
    assert _count_workspace_segments(qdir) == 1, (
        f"expected exactly one 'workspace' segment, got {qdir}"
    )
    assert qdir == repo_root / "workspace" / ".pos" / "memory-write-queue"


def test_AC_FBMW_1_cwd_in_operator_workspace_strips_segment(monkeypatch, tmp_path):
    """When the hook fires from the operator workspace
    ``<repo>/workspace/`` (the live Claude Code cwd) with no env var,
    the caller strips the trailing ``workspace`` segment to recover the
    repo root — so the resolved queue is single-``workspace``."""
    repo_root = tmp_path / "pos3"
    operator_ws = repo_root / "workspace"
    operator_ws.mkdir(parents=True)
    monkeypatch.delenv("LOAM_WORKSPACE_ROOT", raising=False)
    monkeypatch.chdir(operator_ws)

    resolved = cli._resolve_workspace(None)
    assert resolved == repo_root, (
        "cwd in the operator workspace must resolve to the repo root, "
        f"not the operator workspace itself; got {resolved}"
    )
    qdir = queue_dir(resolved)
    assert _count_workspace_segments(qdir) == 1
    # The dead doubled shadow path is NOT produced.
    assert "workspace/workspace" not in str(qdir)


def test_AC_FBMW_1_explicit_flag_wins(monkeypatch, tmp_path):
    """An explicit --workspace (the worker plist path) is honoured
    verbatim and resolves single-``workspace``."""
    repo_root = tmp_path / "pos3"
    repo_root.mkdir()
    monkeypatch.setenv("LOAM_WORKSPACE_ROOT", str(tmp_path / "ignored"))
    resolved = cli._resolve_workspace(repo_root)
    assert resolved == repo_root.resolve()


def test_AC_FBMW_1_live_enqueue_lands_single_workspace(monkeypatch, tmp_path):
    """End-to-end through the production enqueue: a write with the
    caller-resolved repo root lands at the single-``workspace`` live
    queue — exactly one episode file, one ``workspace`` segment."""
    repo_root = tmp_path / "pos3"
    operator_ws = repo_root / "workspace"
    operator_ws.mkdir(parents=True)
    monkeypatch.delenv("LOAM_WORKSPACE_ROOT", raising=False)
    monkeypatch.chdir(operator_ws)

    resolved = cli._resolve_workspace(None)
    written = enqueue(
        workspace_root=resolved,
        turn_id="sess:abc123",
        session_id="sess",
        user_message="u",
        assistant_reply="a",
    )
    assert written.is_file()
    assert _count_workspace_segments(written) == 1
    # The file lives under the SINGLE-workspace live queue.
    assert written.parent == repo_root / "workspace" / ".pos" / "memory-write-queue"
    # The dead doubled shadow dir was NOT created.
    assert not (repo_root / "workspace" / "workspace").exists()
