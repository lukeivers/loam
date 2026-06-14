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

"""AC.PFSE.2★ (outcome-altitude) — a dispatch/edit that violates an
ENFORCED declared principle triggers the observable mechanical check
through the production hook path, with no pre-arranged state.

The enforced principle exercised here: the permission-ask check
(AC.PFSE.4), which is declared `enforced` in the principle-manifest. The
production entry-point is the persona CLI's ``stop`` subcommand reading a
Claude Code Stop envelope from stdin — exactly as Claude Code invokes the
Stop hook. This test runs that CLI AS A SUBPROCESS (the real fire
surface), feeds it a hand-authored transcript whose assistant reply
closes with a permission-ask on authorized work, and observes the
``systemMessage`` advisory on stdout + rc 0.

NO production state is pre-arranged: the only setup is a transcript file
the Stop hook reads (the production input) + a workspace dir. The
observable is the production Stop-output payload, not an internal helper
called with arranged arguments (feedback_test_outcome_altitude_required).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "framework" / "primary-persona" / "src"
_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
PYTHON = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else sys.executable


def _write_transcript(path: Path, *, user: str, assistant: str) -> None:
    """Write a minimal Claude Code JSONL transcript (current nested
    message shape) carrying one user + one assistant turn."""
    lines = [
        {
            "type": "user",
            "message": {"role": "user", "content": user},
        },
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": assistant}],
            },
        },
    ]
    path.write_text(
        "\n".join(json.dumps(o) for o in lines) + "\n",
        encoding="utf-8",
    )


def _run_stop_cli(workspace: Path, envelope: dict) -> subprocess.CompletedProcess:
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "PYTHONPATH": str(SRC),
        "HOME": str(workspace),
    }
    return subprocess.run(
        [
            PYTHON,
            "-m",
            "loam.primary_persona.cli",
            "stop",
            "--workspace",
            str(workspace),
        ],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        cwd=str(workspace),
        env=env,
    )


def test_AC_PFSE_2_star_permission_ask_fires_on_production_stop_path(
    tmp_path,
) -> None:
    """A turn whose outbound reply closes with a permission-ask, fed
    through the real Stop CLI subprocess, yields a ``systemMessage``
    advisory naming the permission-ask check + rc 0. No pre-arranged
    production state (only the transcript the hook reads)."""
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(
        transcript,
        user="do the next slice",
        assistant=(
            "Did the work and the build is green.\n\n"
            "Want me to dispatch the next slice?"
        ),
    )
    envelope = {
        "session_id": "oa-sess",
        "transcript_path": str(transcript),
        "stop_hook_active": False,
    }
    proc = _run_stop_cli(tmp_path, envelope)

    assert proc.returncode == 0, (
        f"Stop hook must exit 0 (got {proc.returncode}); stderr:\n"
        f"{proc.stderr}"
    )
    assert proc.stdout.strip(), (
        "the enforced permission-ask check must emit an observable "
        "advisory on the production Stop path for a permission-ask reply"
    )
    payload = json.loads(proc.stdout)
    assert "systemMessage" in payload
    assert "permission-ask" in payload["systemMessage"].lower()
    # Advisory, NEVER blocking — the turn closes normally.
    assert "decision" not in payload


def test_AC_PFSE_2_star_clean_reply_emits_nothing_on_production_path(
    tmp_path,
) -> None:
    """A clean reply (decision stated, no permission-ask, no false
    SHA-claim) through the real Stop CLI emits EMPTY stdout — the turn
    closes with no advisory (no false positive)."""
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(
        transcript,
        user="do the next slice",
        assistant="Dispatching the next slice now. Build is green.",
    )
    envelope = {
        "session_id": "oa-sess-clean",
        "transcript_path": str(transcript),
        "stop_hook_active": False,
    }
    proc = _run_stop_cli(tmp_path, envelope)
    assert proc.returncode == 0
    assert proc.stdout.strip() == "", (
        f"a clean reply must emit empty stdout; got: {proc.stdout!r}"
    )
