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

"""AC.M.4 — Stop-hook subcommand exists, exits 0 on every path.

Outcome (per locked plan §5): a ``stop`` subcommand exists on
``primary_persona.cli`` that reads Claude Code's Stop envelope from
stdin (JSON shape per Claude Code Stop-hook contract) and exits 0
unconditionally — including on stdin-read failure, JSON parse
failure, transcript-read failure, and any internal exception. No
traceback reaches stdout or stderr.

Also asserts plan §7 constraint 12 (Stop-hook stdout is not
load-bearing) — the success-path leaves stdout silent.
"""

from __future__ import annotations

import io
import json
from pathlib import Path


def _run_cli_stop(monkeypatch, capsys, stdin_text: str, workspace: Path) -> tuple[int, str, str]:
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    from loam.primary_persona.stop_emitter import cli_stop

    rc = cli_stop(workspace_root=workspace)
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def test_AC_M_4_subcommand_registered_in_cli(tmp_path: Path) -> None:
    """The persona CLI argparse parser exposes a ``stop`` subcommand."""
    from loam.primary_persona.cli import build_parser

    parser = build_parser()
    # Probe by parsing; argparse raises SystemExit on unknown.
    args = parser.parse_args(["stop", "--workspace", str(tmp_path)])
    assert args.command == "stop"
    assert callable(args.func)


def test_AC_M_4_empty_stdin_exits_zero(tmp_path: Path, monkeypatch, capsys) -> None:
    rc, out, err = _run_cli_stop(monkeypatch, capsys, "", tmp_path)
    assert rc == 0
    assert out == ""
    assert err == ""


def test_AC_M_4_non_json_stdin_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    rc, out, err = _run_cli_stop(monkeypatch, capsys, "not json at all", tmp_path)
    assert rc == 0
    assert out == ""
    assert err == ""


def test_AC_M_4_json_missing_required_fields_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    rc, out, err = _run_cli_stop(
        monkeypatch,
        capsys,
        json.dumps({"unrelated": "value"}),
        tmp_path,
    )
    assert rc == 0
    assert out == ""
    assert err == ""


def test_AC_M_4_missing_transcript_path_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Envelope's transcript_path points at a non-existent file —
    handle_stop_envelope's recover branch returns ("", "") and the
    AC.M.9 graceful-no-op branch fires; cli_stop exits 0."""
    envelope = json.dumps(
        {
            "session_id": "s1",
            "transcript_path": str(tmp_path / "missing.jsonl"),
            "stop_hook_active": False,
        }
    )
    rc, out, err = _run_cli_stop(monkeypatch, capsys, envelope, tmp_path)
    assert rc == 0
    assert out == ""
    assert err == ""


def test_AC_M_4_internal_exception_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """When ``handle_stop_envelope`` raises unexpectedly, ``cli_stop``
    catches and exits 0 (the diagnostic surface is the workspace-local
    log, not Claude Code's debug log)."""
    import loam.primary_persona.stop_emitter as se

    def _explode(*a, **kw):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(se, "handle_stop_envelope", _explode)
    envelope = json.dumps(
        {
            "session_id": "s1",
            "transcript_path": str(tmp_path / "missing.jsonl"),
        }
    )
    rc, out, err = _run_cli_stop(monkeypatch, capsys, envelope, tmp_path)
    assert rc == 0
    assert out == ""
    # No traceback reaches stderr.
    assert "Traceback" not in err


def test_AC_M_4_stdin_read_failure_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A stdin object whose ``.read()`` raises is absorbed."""
    class _BadStdin:
        def read(self):
            raise OSError("synthetic stdin failure")

    monkeypatch.setattr("sys.stdin", _BadStdin())
    from loam.primary_persona.stop_emitter import cli_stop

    rc = cli_stop(workspace_root=tmp_path)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
