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

"""AC.EOTTR.5 — Graceful behaviour on absent content.

Outcome: when the assistant text is empty, whitespace-only, or
unrecoverable from the transcript:

  - ``run_trait_reflection`` does not crash; emits ``CONCERN:
    missing content`` for every one of the seven traits.
  - ``cli_trait_reflection_stop`` exits 0 unconditionally —
    including on empty stdin, malformed JSON stdin, missing
    transcript file, and any internal exception. No traceback
    reaches stdout or stderr.
"""

from __future__ import annotations

import io
import json
from pathlib import Path


def test_AC_EOTTR_5_empty_text_yields_concern_missing_for_all_traits(
    tmp_path: Path,
) -> None:
    """``run_trait_reflection(assistant_text='')`` returns seven
    CONCERN verdicts."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        run_trait_reflection,
    )

    result = run_trait_reflection(
        workspace_root=tmp_path,
        session_id="s-empty",
        assistant_text="",
    )
    assert len(result["verdicts"]) == 7
    for v in result["verdicts"]:
        assert v["verdict"] == "CONCERN"
        assert v["reason"] == "missing content"


def test_AC_EOTTR_5_whitespace_only_text_yields_concern_missing_for_all_traits(
    tmp_path: Path,
) -> None:
    """Whitespace-only assistant text is treated identically to empty."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        run_trait_reflection,
    )

    result = run_trait_reflection(
        workspace_root=tmp_path,
        session_id="s-ws",
        assistant_text="   \n\t  \n",
    )
    for v in result["verdicts"]:
        assert v["verdict"] == "CONCERN"
        assert v["reason"] == "missing content"


def _run_cli(monkeypatch, capsys, stdin_text: str, workspace: Path) -> tuple[int, str, str]:
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    from loam.primary_persona.end_of_turn_trait_reflection import (
        cli_trait_reflection_stop,
    )

    rc = cli_trait_reflection_stop(workspace_root=workspace)
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def test_AC_EOTTR_5_empty_stdin_exits_zero_no_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    rc, out, err = _run_cli(monkeypatch, capsys, "", tmp_path)
    assert rc == 0
    assert out == ""
    assert err == ""


def test_AC_EOTTR_5_non_json_stdin_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    rc, out, err = _run_cli(monkeypatch, capsys, "not json", tmp_path)
    assert rc == 0
    assert out == ""
    assert err == ""


def test_AC_EOTTR_5_missing_transcript_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Envelope's ``transcript_path`` points at a non-existent file —
    the recovery branch returns ('', ''), AC.EOTTR.5 emits 7 CONCERN
    verdicts, cli exits 0."""
    envelope = json.dumps(
        {
            "session_id": "s-no-tx",
            "transcript_path": str(tmp_path / "missing.jsonl"),
        }
    )
    rc, out, err = _run_cli(monkeypatch, capsys, envelope, tmp_path)
    assert rc == 0
    assert out == ""
    assert err == ""
    # And the log records the seven CONCERN verdicts.
    log_path = (
        tmp_path
        / "workspace"
        / ".pos"
        / "trait-reflection"
        / "s-no-tx.jsonl"
    )
    assert log_path.exists()
    entry = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert all(v["verdict"] == "CONCERN" for v in entry["verdicts"])


def test_AC_EOTTR_5_internal_exception_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """When ``handle_stop_envelope`` raises, ``cli`` catches and exits 0."""
    import loam.primary_persona.end_of_turn_trait_reflection as mod

    def _explode(*a, **kw):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(mod, "handle_stop_envelope", _explode)
    envelope = json.dumps(
        {
            "session_id": "s-explode",
            "transcript_path": str(tmp_path / "missing.jsonl"),
        }
    )
    rc, out, err = _run_cli(monkeypatch, capsys, envelope, tmp_path)
    assert rc == 0
    assert out == ""
    assert "Traceback" not in err


def test_AC_EOTTR_5_stdin_read_failure_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A stdin object whose ``.read()`` raises is absorbed."""
    class _BadStdin:
        def read(self):
            raise OSError("synthetic stdin failure")

    monkeypatch.setattr("sys.stdin", _BadStdin())
    from loam.primary_persona.end_of_turn_trait_reflection import (
        cli_trait_reflection_stop,
    )

    rc = cli_trait_reflection_stop(workspace_root=tmp_path)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
