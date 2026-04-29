"""AC.M.10 — Live client failure during write: fail-soft + diagnostic.

Outcome (per locked plan §5): given the memory-graphiti service is
unreachable when the detached write subprocess attempts
``add_episode``, the subprocess exits cleanly (no zombie), surfaces
a structured diagnostic to a workspace-local log file, and does not
affect the main session in any way (no state change to settings.json,
no persona contract mutation, no orchestrator surface touched).

D8 diagnostic log: ``<workspace>/.pos/memory-writes.log``, NDJSON.
"""

from __future__ import annotations

import json
from pathlib import Path

from _helpers_d7 import FakeMemoryClient


def _read_log_lines(workspace: Path) -> list[dict]:
    log = workspace / "workspace" / ".pos" / "memory-writes.log"
    if not log.exists():
        return []
    return [
        json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]


def test_AC_M_10_add_episode_raises_writes_error_diag_returns_zero(
    tmp_path: Path, monkeypatch
) -> None:
    """When the live client's ``add_episode`` raises, the detached
    subprocess catches, logs a structured ``write-error`` entry,
    and exits 0."""
    fake = FakeMemoryClient()
    fake.add_episode_raises = ConnectionRefusedError("memory unreachable")
    import loam.primary_persona.mcp_memory_client as mmc

    monkeypatch.setattr(
        mmc, "build_live_mcp_memory_client", lambda root: fake
    )
    from loam.primary_persona.stop_emitter import cli_memory_write

    rc = cli_memory_write(
        workspace_root=tmp_path,
        turn_id="s1:abcdef000000",
        session_id="s1",
        user_message="u",
        assistant_reply="a",
    )
    assert rc == 0
    entries = _read_log_lines(tmp_path)
    assert any(
        e.get("kind") == "write-error" and "ConnectionRefusedError" in str(e.get("error", ""))
        for e in entries
    ), f"expected write-error diagnostic, got {entries}"


def test_AC_M_10_no_live_client_logs_skip_returns_zero(
    tmp_path: Path, monkeypatch
) -> None:
    """When the live client builder returns None, the child logs
    ``write-skip`` reason ``no-live-client`` and exits 0."""
    import loam.primary_persona.mcp_memory_client as mmc

    monkeypatch.setattr(
        mmc, "build_live_mcp_memory_client", lambda root: None
    )
    from loam.primary_persona.stop_emitter import cli_memory_write

    rc = cli_memory_write(
        workspace_root=tmp_path,
        turn_id="s1:000000000000",
        session_id="s1",
        user_message="u",
        assistant_reply="a",
    )
    assert rc == 0
    entries = _read_log_lines(tmp_path)
    assert any(
        e.get("kind") == "write-skip" and e.get("reason") == "no-live-client"
        for e in entries
    )


def test_AC_M_10_successful_write_logs_write_ok(
    tmp_path: Path, monkeypatch
) -> None:
    """Happy path also lands a structured diagnostic — the operator
    can verify writes are happening by tailing the log."""
    fake = FakeMemoryClient()
    import loam.primary_persona.mcp_memory_client as mmc

    monkeypatch.setattr(
        mmc, "build_live_mcp_memory_client", lambda root: fake
    )
    from loam.primary_persona.stop_emitter import cli_memory_write

    rc = cli_memory_write(
        workspace_root=tmp_path,
        turn_id="s1:cafe00000000",
        session_id="s1",
        user_message="u",
        assistant_reply="a",
    )
    assert rc == 0
    entries = _read_log_lines(tmp_path)
    assert any(e.get("kind") == "write-ok" for e in entries)
