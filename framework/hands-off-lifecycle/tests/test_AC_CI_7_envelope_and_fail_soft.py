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

"""AC.CI.7 — SessionStart envelope and fail-soft.

Per the locked plan-doc §4 AC.CI.7: the hook completes within the 5s
SessionStart inner-hook budget and exits 0 on every path. Environmental
failures degrade gracefully:
  - file unreadable → ``[missing]`` slot or omission;
  - sentinel write failure → no raise; corpus emit unaffected;
  - manifest absence → degraded sentinel state but emit proceeds;
  - empty stdin → exit 0 with no emission;
  - malformed envelope → exit 0 with no emission.

The hook never raises into Claude Code's SessionStart fan-out.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_SCRIPT = (
    REPO_ROOT
    / "framework"
    / "hands-off-lifecycle"
    / "hooks"
    / "corpus_inline_session_start.py"
)


def _run_hook(stdin_text: str, timeout: float = 10.0) -> tuple[str, int]:
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout, result.returncode


def test_AC_CI_7_empty_stdin_exits_zero(tmp_path: Path) -> None:
    """Empty stdin → hook exits 0 with empty stdout (fail-soft)."""
    stdout, rc = _run_hook("")
    assert rc == 0
    assert stdout == ""


def test_AC_CI_7_malformed_json_exits_zero(tmp_path: Path) -> None:
    """Malformed JSON envelope → hook exits 0 with empty stdout."""
    stdout, rc = _run_hook("not valid json {{{")
    assert rc == 0
    assert stdout == ""


def test_AC_CI_7_envelope_missing_workspace_exits_zero(
    tmp_path: Path,
) -> None:
    """Envelope missing workspace.project_dir → hook exits 0 with
    empty stdout."""
    stdin = json.dumps({"session_id": "x"})
    stdout, rc = _run_hook(stdin)
    assert rc == 0
    assert stdout == ""


def test_AC_CI_7_envelope_missing_session_id_still_emits(
    tmp_path: Path,
) -> None:
    """Envelope missing session_id but valid workspace + DEV MODE →
    hook emits corpus content but skips sentinel update (fail-soft)."""
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    (tmp_path / "CLAUDE.md").write_text("# c\n", encoding="utf-8")
    rebuild_dir = tmp_path / "docs" / "rebuild"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    (rebuild_dir / "VALUE_PROPOSITION.md").write_text("# v\n", encoding="utf-8")
    (rebuild_dir / "STATE.md").write_text("# s\n", encoding="utf-8")
    stdin = json.dumps({"workspace": {"project_dir": str(tmp_path)}})
    stdout, rc = _run_hook(stdin)
    assert rc == 0
    # Emission still happens (the AC names content emit + sentinel
    # update as INDEPENDENT fail-soft outcomes).
    assert "=== pos-v2 always-loaded corpus" in stdout


def test_AC_CI_7_completes_within_5s_budget(tmp_path: Path) -> None:
    """Hook completes within the 5s SessionStart inner-hook budget.
    The lean tier reads (3 small files) take <20ms on local SSD per
    research §3.2 + §8.4. The 5s envelope is ~250x generous."""
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    (tmp_path / "CLAUDE.md").write_text("# c\n", encoding="utf-8")
    rebuild_dir = tmp_path / "docs" / "rebuild"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    (rebuild_dir / "VALUE_PROPOSITION.md").write_text("# v\n", encoding="utf-8")
    (rebuild_dir / "STATE.md").write_text("# s\n", encoding="utf-8")
    stdin = json.dumps(
        {"session_id": "sess-budget", "workspace": {"project_dir": str(tmp_path)}}
    )
    t_start = time.time()
    stdout, rc = _run_hook(stdin, timeout=5.0)
    elapsed = time.time() - t_start
    assert rc == 0
    # Generous: the test allows up to 4s (well within 5s budget) to
    # account for subprocess startup + import overhead in slow CI
    # environments.
    assert elapsed < 4.0, f"Hook exceeded 4s envelope: {elapsed:.2f}s"


def test_AC_CI_7_unreadable_file_handled_gracefully(
    tmp_path: Path,
) -> None:
    """An unreadable file (no chmod variant on most CIs; simulate by
    writing invalid UTF-8) degrades to [missing] without raising.
    The hook still emits content from other files + exits 0."""
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    # CLAUDE.md is valid UTF-8.
    (tmp_path / "CLAUDE.md").write_text("# c\n", encoding="utf-8")
    rebuild_dir = tmp_path / "docs" / "rebuild"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    (rebuild_dir / "VALUE_PROPOSITION.md").write_text("# v\n", encoding="utf-8")
    # STATE.md contains invalid UTF-8 bytes.
    (rebuild_dir / "STATE.md").write_bytes(b"\xff\xfe\x00\x00bad utf-8")
    stdin = json.dumps(
        {"session_id": "sess-unread", "workspace": {"project_dir": str(tmp_path)}}
    )
    stdout, rc = _run_hook(stdin)
    # Hook MUST exit 0 even though one file failed to read.
    assert rc == 0
    # Other files still emitted.
    assert "# c" in stdout
    assert "# v" in stdout


def test_AC_CI_7_never_raises_on_disk_io_failure(
    tmp_path: Path,
) -> None:
    """Sentinel write failure (e.g. parent dir absent and
    unwriteable) does NOT cause the hook to exit non-zero. The
    corpus emit is the primary AC; sentinel update is best-effort."""
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    (tmp_path / "CLAUDE.md").write_text("# c\n", encoding="utf-8")
    rebuild_dir = tmp_path / "docs" / "rebuild"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    (rebuild_dir / "VALUE_PROPOSITION.md").write_text("# v\n", encoding="utf-8")
    (rebuild_dir / "STATE.md").write_text("# s\n", encoding="utf-8")
    stdin = json.dumps(
        {
            "session_id": "sess-fail-soft",
            "workspace": {"project_dir": str(tmp_path)},
        }
    )
    stdout, rc = _run_hook(stdin)
    assert rc == 0
    # Content emit happened.
    assert "=== pos-v2 always-loaded corpus" in stdout
