"""AC.J.6 — Pre-warm verification surface.

Outcome (per locked plan §4 + D-1 lock): a read-only diagnostic
surface exposes the workspace's recommended Ollama pre-warm value
+ the live env-var state. The persona reads this on demand (e.g.,
on user-prompt-submit's awareness block) to answer "is the
embedding model resident?" without the user investigating.

The advisory file at
``<workspace>/.pos/ollama-prewarm-recommended.txt`` is authored by
workspace-bootstrap (D-1 surface choice); this test exercises the
persona-side reader (``memory_prewarm.read_prewarm_advisory``) only.
The workspace-bootstrap-side write is exercised in
``workspace-bootstrap/tests/test_AC_J_1_prewarm_advisory_writer.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

from src import memory_prewarm
from src import memory_write_queue as mwq


def _write_advisory(workspace_root: Path, value: str = "24h") -> None:
    """Helper: emit a workspace-bootstrap-shaped advisory file."""
    p = workspace_root / mwq.PREWARM_RECOMMEND_FILENAME
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"OLLAMA_KEEP_ALIVE={value}\n"
        "\n"
        "# Run on the operator's machine to take effect for the\n"
        "# Ollama daemon (server-side env):\n"
        "#   launchctl setenv OLLAMA_KEEP_ALIVE 24h\n"
        "#   brew services restart ollama\n",
        encoding="utf-8",
    )


def test_AC_J_6_missing_advisory_returns_inactive_snapshot(tmp_path: Path) -> None:
    state = memory_prewarm.read_prewarm_advisory(tmp_path)
    assert state.advisory_path is None
    assert state.advisory_value is None
    assert state.recommendation_active is False


def test_AC_J_6_advisory_present_env_unset_recommends(tmp_path: Path, monkeypatch) -> None:
    _write_advisory(tmp_path, value="24h")
    # Ensure env is clean.
    monkeypatch.delenv("OLLAMA_KEEP_ALIVE", raising=False)

    state = memory_prewarm.read_prewarm_advisory(tmp_path)
    assert state.advisory_path == tmp_path / ".pos" / "ollama-prewarm-recommended.txt"
    assert state.advisory_value == "24h"
    assert state.env_value is None
    assert state.recommendation_active is True


def test_AC_J_6_advisory_present_env_set_no_recommendation(tmp_path: Path, monkeypatch) -> None:
    _write_advisory(tmp_path, value="24h")
    monkeypatch.setenv("OLLAMA_KEEP_ALIVE", "24h")

    state = memory_prewarm.read_prewarm_advisory(tmp_path)
    assert state.env_value == "24h"
    assert state.recommendation_active is False


def test_AC_J_6_malformed_advisory_does_not_crash(tmp_path: Path, monkeypatch) -> None:
    p = tmp_path / mwq.PREWARM_RECOMMEND_FILENAME
    p.parent.mkdir(parents=True, exist_ok=True)
    # No OLLAMA_KEEP_ALIVE=... line.
    p.write_text("# random content\nno key\n", encoding="utf-8")
    monkeypatch.delenv("OLLAMA_KEEP_ALIVE", raising=False)
    state = memory_prewarm.read_prewarm_advisory(tmp_path)
    # File exists but value unparseable; recommendation still active
    # because env is unset (the file's mere presence signals the
    # operator hasn't completed the chore).
    assert state.advisory_path is not None
    assert state.advisory_value is None
    assert state.recommendation_active is True


def test_AC_J_6_recommended_value_default_matches_d5_lock() -> None:
    """The persona-side recommended value matches the D-5 lock (24h)."""
    assert memory_prewarm.RECOMMENDED_KEEP_ALIVE_VALUE == "24h"
