"""AC.M.6 — Stop-hook write path persists exactly one episode per turn.

Outcome (per locked plan §5): for a given Stop event with recoverable
user message + assistant reply, exactly one ``add_episode`` call
lands at the memory service for that turn — not zero, not two, not
per-message. The episode body contains both the user message and
the assistant reply. The episode's ``group_id`` equals the
workspace slug.

This test exercises the detached-child entry point
``cli_memory_write`` directly (the Stop subprocess's only job is to
spawn this child; AC.M.6 is the child's contract).

We monkeypatch ``build_live_mcp_memory_client`` so it returns a
``FakeMemoryClient`` instead of opening a real MCP transport — the
behaviour under test is the write-path's call count + body
composition, not the wire format (AC.M.1's responsibility).
"""

from __future__ import annotations

from pathlib import Path

from _helpers_d7 import FakeMemoryClient


def test_AC_M_6_cli_memory_write_drives_one_add_episode(
    tmp_path: Path, monkeypatch
) -> None:
    """``cli_memory_write`` calls ``add_episode`` exactly once,
    body contains both halves, group_id is the workspace slug."""
    fake = FakeMemoryClient()
    import src.mcp_memory_client as mmc
    import src.stop_emitter as se

    monkeypatch.setattr(
        mmc, "build_live_mcp_memory_client", lambda root: fake
    )
    # se.cli_memory_write does its own lazy import; patch its module
    # too in case the lazy-import grabbed a different reference.
    monkeypatch.setattr(
        se, "build_live_mcp_memory_client", None, raising=False
    )

    rc = se.cli_memory_write(
        workspace_root=tmp_path,
        turn_id="s1:deadbeef0000",
        session_id="s1",
        user_message="what's deterministic?",
        assistant_reply="exactly one episode per turn.",
    )
    assert rc == 0
    assert len(fake.add_episode_calls) == 1
    call = fake.add_episode_calls[0]
    assert "what's deterministic?" in call.body
    assert "exactly one episode per turn." in call.body
    # AC.M.6 + AC-D7.4: group_id is the workspace slug (sanitised
    # workspace basename).
    from src.memory_consumer import resolve_workspace_slug

    assert call.group_id == resolve_workspace_slug(tmp_path)
    # Episode name encodes the turn id (matches TurnAggregator
    # semantics from amendment #33).
    assert "s1:deadbeef0000" in call.name
    # Source is "message" (the labelled-block episode body shape).
    assert call.source == "message"


def test_AC_M_6_no_live_client_means_no_write_but_still_exit_zero(
    tmp_path: Path, monkeypatch
) -> None:
    """When the live client builder returns None (substrate not
    ready), cli_memory_write logs and exits 0 without invoking
    add_episode."""
    fake = FakeMemoryClient()
    import src.mcp_memory_client as mmc

    monkeypatch.setattr(
        mmc, "build_live_mcp_memory_client", lambda root: None
    )
    from src.stop_emitter import cli_memory_write

    rc = cli_memory_write(
        workspace_root=tmp_path,
        turn_id="s1:deadbeef0000",
        session_id="s1",
        user_message="u",
        assistant_reply="a",
    )
    assert rc == 0
    assert fake.add_episode_calls == []
