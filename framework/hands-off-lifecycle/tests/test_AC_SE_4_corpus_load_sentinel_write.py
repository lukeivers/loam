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

"""AC.SE.4 — corpus-load sentinel write contract.

Per the locked plan-doc §4 AC.SE.4: a SessionStart inner-hook entry
writes ``<workspace>/.pos/session-state/<session_id>.json`` carrying
``session_id``, ``corpus_paths_required``, ``corpus_paths_loaded``,
``state``, ``created_at``. The CLI completes within the 5s
SessionStart inner-hook budget and exits 0 on every path.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from corpus_load_sentinel import (  # noqa: E402
    read_corpus_load_sentinel,
    session_state_path,
    write_corpus_load_sentinel,
)


def test_AC_SE_4_writes_sentinel_with_required_fields(
    tmp_path: Path,
) -> None:
    result = write_corpus_load_sentinel(
        tmp_path, session_id="sess-1", mode="normal-use"
    )
    assert result.wrote is True
    target = session_state_path(tmp_path, "sess-1")
    assert target.exists()
    on_disk = json.loads(target.read_text())
    assert on_disk["session_id"] == "sess-1"
    assert "corpus_paths_required" in on_disk
    assert isinstance(on_disk["corpus_paths_required"], list)
    assert on_disk["corpus_paths_loaded"] == []
    assert on_disk["state"] in ("loaded", "partial", "missing")
    assert "created_at" in on_disk and on_disk["created_at"]


def test_AC_SE_4_state_is_missing_when_no_paths_present(
    tmp_path: Path,
) -> None:
    """Empty workspace → no required paths exist → state = missing."""
    result = write_corpus_load_sentinel(
        tmp_path, session_id="sess-2", mode="normal-use"
    )
    assert result.wrote is True
    target = session_state_path(tmp_path, "sess-2")
    on_disk = json.loads(target.read_text())
    assert on_disk["state"] == "missing"


def test_AC_SE_4_per_session_id_path(tmp_path: Path) -> None:
    """Two different session_ids produce two distinct sentinel files."""
    write_corpus_load_sentinel(tmp_path, session_id="a", mode="normal-use")
    write_corpus_load_sentinel(tmp_path, session_id="b", mode="normal-use")
    files = list((tmp_path / "workspace" / ".pos" / "session-state").iterdir())
    names = sorted(f.name for f in files)
    assert names == ["a.json", "b.json"]


def test_AC_SE_4_atomic_via_tmp_then_rename(tmp_path: Path) -> None:
    """The writer must use a `.tmp` sibling + os.rename so concurrent
    readers see either prior or new content. Asserted structurally
    by inspecting the writer's source for the canonical pattern."""
    src = (
        REPO_ROOT
        / "framework" / "hands-off-lifecycle"
        / "hooks"
        / "corpus_load_sentinel.py"
    ).read_text()
    assert ".tmp" in src
    assert "os.replace" in src or "os.rename" in src


def test_AC_SE_4_cli_exits_zero_on_empty_stdin(tmp_path: Path) -> None:
    """The CLI must exit 0 even when stdin is empty."""
    cli = HOOKS_DIR / "corpus_load_session_start.py"
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    result = subprocess.run(
        [str(venv_python), "-u", str(cli)],
        input="",
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0


def test_AC_SE_4_cli_exits_zero_on_malformed_json(tmp_path: Path) -> None:
    """The CLI must exit 0 on malformed stdin (graceful degradation)."""
    cli = HOOKS_DIR / "corpus_load_session_start.py"
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    result = subprocess.run(
        [str(venv_python), "-u", str(cli)],
        input="not { json",
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0


def test_AC_SE_4_cli_writes_sentinel_on_well_formed_envelope(
    tmp_path: Path,
) -> None:
    """The CLI parses the SessionStart envelope and writes the
    sentinel for the (workspace, session_id) pair."""
    cli = HOOKS_DIR / "corpus_load_session_start.py"
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    envelope = json.dumps(
        {
            "session_id": "sess-cli-test",
            "workspace": {"project_dir": str(tmp_path)},
        }
    )
    result = subprocess.run(
        [str(venv_python), "-u", str(cli)],
        input=envelope,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    sentinel = read_corpus_load_sentinel(tmp_path, "sess-cli-test")
    assert sentinel is not None
    assert sentinel.session_id == "sess-cli-test"


def test_AC_SE_4_cli_completes_under_5s_budget(tmp_path: Path) -> None:
    """The hook completes within the 5s SessionStart inner-hook
    budget. Run end-to-end (CLI invocation under the workspace
    venv) and assert wall-clock is well under 5s."""
    cli = HOOKS_DIR / "corpus_load_session_start.py"
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    envelope = json.dumps(
        {
            "session_id": "sess-budget",
            "workspace": {"project_dir": str(tmp_path)},
        }
    )
    start = time.perf_counter()
    result = subprocess.run(
        [str(venv_python), "-u", str(cli)],
        input=envelope,
        capture_output=True,
        text=True,
        timeout=5,
    )
    elapsed = time.perf_counter() - start
    assert result.returncode == 0
    assert elapsed < 5.0, f"corpus-load hook exceeded 5s budget: {elapsed:.2f}s"


def test_AC_SE_4_empty_session_id_returns_failed_result(
    tmp_path: Path,
) -> None:
    """Defensive: an empty session_id is structurally invalid; the
    library returns a failed-* result without raising."""
    result = write_corpus_load_sentinel(tmp_path, session_id="")
    assert result.wrote is False
    assert result.reason == "failed-empty-session-id"
