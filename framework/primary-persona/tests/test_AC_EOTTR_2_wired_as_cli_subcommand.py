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

"""AC.EOTTR.2 — Trait-reflection contributor is wired as a new CLI
subcommand on ``loam.primary_persona.cli``.

Outcome: ``primary-persona`` CLI exposes a ``trait-reflection-stop``
subparser whose ``args.func`` runs the contributor. Invokable as
``python -m loam.primary_persona.cli trait-reflection-stop``.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path


def test_AC_EOTTR_2_subcommand_registered_in_cli(tmp_path: Path) -> None:
    """The persona CLI argparse parser exposes a
    ``trait-reflection-stop`` subcommand."""
    from loam.primary_persona.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(
        ["trait-reflection-stop", "--workspace", str(tmp_path)]
    )
    assert args.command == "trait-reflection-stop"
    assert callable(args.func)


def test_AC_EOTTR_2_subcommand_dispatches_to_cli_trait_reflection_stop(
    tmp_path: Path, monkeypatch
) -> None:
    """``args.func(args)`` reaches the documented
    ``cli_trait_reflection_stop`` entry point."""
    from loam.primary_persona.cli import build_parser

    captured: dict = {}
    import loam.primary_persona.cli as cli_mod

    def _spy(*, workspace_root):
        captured["workspace_root"] = workspace_root
        return 0

    monkeypatch.setattr(cli_mod, "cli_trait_reflection_stop", _spy)

    parser = build_parser()
    args = parser.parse_args(
        ["trait-reflection-stop", "--workspace", str(tmp_path)]
    )
    rc = args.func(args)
    assert rc == 0
    assert captured["workspace_root"].resolve() == tmp_path.resolve()


def test_AC_EOTTR_2_python_m_invocation_runs_subcommand(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """``python -m loam.primary_persona.cli trait-reflection-stop ...``
    runs the contributor and exits 0 even on empty stdin."""
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    from loam.primary_persona.cli import main

    rc = main(["trait-reflection-stop", "--workspace", str(tmp_path)])
    assert rc == 0
    captured = capsys.readouterr()
    # Plan §7 constraint 12 analogue: Stop-hook stdout is debug-log
    # only; the success path leaves stdout silent.
    assert captured.out == ""


def test_AC_EOTTR_2_subcommand_runs_against_real_transcript(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """End-to-end: a well-formed Stop envelope + transcript produces
    one log line under
    ``<workspace>/workspace/.pos/trait-reflection/<session>.jsonl``."""
    # Build a minimal transcript.
    transcript = tmp_path / "tx.jsonl"
    transcript.write_text(
        json.dumps({"role": "user", "content": "do the thing"})
        + "\n"
        + json.dumps({"role": "assistant", "content": "dispatching now."})
        + "\n",
        encoding="utf-8",
    )
    envelope = json.dumps(
        {
            "session_id": "s-eottr-2",
            "transcript_path": str(transcript),
            "stop_hook_active": False,
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))

    from loam.primary_persona.cli import main

    rc = main(["trait-reflection-stop", "--workspace", str(tmp_path)])
    assert rc == 0

    log_path = (
        tmp_path
        / "workspace"
        / ".pos"
        / "trait-reflection"
        / "s-eottr-2.jsonl"
    )
    assert log_path.exists(), f"expected log at {log_path}"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["session_id"] == "s-eottr-2"
    assert isinstance(entry["verdicts"], list)
    assert len(entry["verdicts"]) == 7
