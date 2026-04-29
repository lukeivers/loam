"""D8 — compaction-survival integration.

Acceptance (from brief D8):
- Session-side compaction hook calls the orchestrator's IPC endpoint
  on PreCompact.
- Orchestrator writes pending_compaction_restore flag to local SQLite.
- On next UserPromptSubmit, the session pulls restoration content;
  the five-item canonical survival list (persona identity, authority
  boundary, current scope context, pending decisions, recent
  corrections) is verifiably present and correctly sourced (persona
  identity from contract.yaml, scope context from scope-of-work, etc.).
- Flag is cleared after successful restoration.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from objective_tracker import ObjectiveSpec, ProseCriterion, TimeBound
from pos_orchestrator import Orchestrator
from pos_orchestrator.ipc import IPCClient
from primary_persona.loader import PersonaLoader

from .conftest import make_scope_spec


_VALID_YAML = dedent(
    """\
    handle: eve
    given_name: Eve
    contract_version: 1.0.0
    responsibilities:
      single_point_of_contact: Sole coordinator for personal-life operations.
      context_holder: Carries ongoing context across sessions.
      escalation_judge: Decides when to surface matters to Luke.
    authority_boundary:
      tier_a: defer
      tier_b: defer
      tier_c: execute
      tier_d: execute
    escalation_taxonomy:
      categories:
        - external-funds-commitment
        - strategy-pivot
    severity_vocabulary:
      labels:
        - crisis
        - urgent
        - material
        - advisory
    delegates_to:
      - financial-advisor
    home_persona_for:
      - personal
    voice_markers:
      - "Lead with the answer."
    is_primary: true
    pending_introduction: false
    is_addressable: true
    """
)


def _write_persona(workspace: Path, handle: str = "eve") -> None:
    # D-migration D.2 (amendment #63): personas live under
    # <workspace>/workspace/personas/, not <workspace>/personas/.
    # The fixture pre-D.2 wrote to the latter; this is the post-D.2
    # path matching primary_persona.loader.personas_dir() resolution.
    personas_dir = workspace / "workspace" / "personas" / handle
    personas_dir.mkdir(parents=True, exist_ok=True)
    yaml = _VALID_YAML
    if handle != "eve":
        yaml = yaml.replace("handle: eve", f"handle: {handle}")
    (personas_dir / "contract.yaml").write_text(yaml)
    (personas_dir / "prompt.md").write_text("# prompt\nHello.\n")


@pytest.fixture
def loaded_persona(tmp_path: Path):
    _write_persona(tmp_path)
    loader = PersonaLoader(tmp_path, enforce_no_personas_in_core=False)
    return loader.primary()


async def _root_objective(orch: Orchestrator, goal: str = "root") -> str:
    assert orch.objective_tracker is not None
    spec = ObjectiveSpec(
        goal=goal,
        parent_id=None,
        acceptance_criteria=(ProseCriterion(criterion_id="c", prose="done"),),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
    )
    proj = await orch.objective_tracker.create(spec)
    return proj.objective_id


@pytest.mark.asyncio
async def test_precompact_via_ipc_sets_flag(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        client = IPCClient(tmp_config.socket_path)
        await client.connect()
        try:
            r = await client.call("mark_precompact", {"session_id": "s-1"})
            assert r["pending"] is True
        finally:
            await client.close()
        # Flag event was written.
        assert o.local_state.count("compaction_flag_set") == 1


@pytest.mark.asyncio
async def test_consume_compaction_returns_five_item_payload(
    tmp_config, loaded_persona
):
    from primary_persona.compaction import SURVIVAL_LIST

    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        # Attach the loaded persona + seed some scope state.
        o.set_loaded_persona(loaded_persona)
        o.set_recent_corrections_provider(
            lambda n: [
                {"at": "2026-04-10", "note": "prefer bullet lists"},
                {"at": "2026-04-11", "note": "no emoji"},
            ][:n]
        )
        oid = await _root_objective(o)
        p_active = await o.scope_runtime.create(make_scope_spec("active one"))
        await o.activate_scope(p_active.scope_id, oid)
        await o.scope_runtime.create(make_scope_spec("still queued"))

        # Session signals PreCompact.
        o.set_compaction_flag(session_id="s-1")
        assert o.compaction_flag_pending()

        # Session's next UserPromptSubmit pulls restoration.
        payload = await o.consume_compaction(session_id="s-1")
        assert payload is not None
        # All five items present.
        for key in SURVIVAL_LIST:
            assert key in payload, f"missing survival list item: {key}"

        # Sourced correctly.
        assert payload["persona_identity"]["handle"] == "eve"
        assert payload["persona_identity"]["given_name"] == "Eve"
        assert payload["authority_boundary"]["tier_a"] == "defer"
        assert payload["authority_boundary"]["tier_c"] == "execute"
        assert any(
            s["scope_id"] == p_active.scope_id
            for s in payload["current_scope_context"]
        )
        assert len(payload["recent_corrections"]) == 2

        # Flag cleared.
        assert not o.compaction_flag_pending()


@pytest.mark.asyncio
async def test_consume_without_flag_returns_none(tmp_config, loaded_persona):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        o.set_loaded_persona(loaded_persona)
        assert not o.compaction_flag_pending()
        payload = await o.consume_compaction()
        assert payload is None


@pytest.mark.asyncio
async def test_repeated_consume_does_not_re_inject(tmp_config, loaded_persona):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        o.set_loaded_persona(loaded_persona)
        o.set_compaction_flag(session_id="s-1")
        first = await o.consume_compaction()
        assert first is not None
        second = await o.consume_compaction()
        assert second is None  # flag cleared; no re-injection


@pytest.mark.asyncio
async def test_consume_compaction_via_ipc(tmp_config, loaded_persona):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        o.set_loaded_persona(loaded_persona)
        client = IPCClient(tmp_config.socket_path)
        await client.connect()
        try:
            await client.call("mark_precompact", {"session_id": "s-1"})
            payload = await client.call(
                "consume_compaction", {"session_id": "s-1"}
            )
            assert payload is not None
            assert "persona_identity" in payload
            # After consumption, next call returns a pending:False shape.
            pending_after = await client.call("consume_compaction", {})
            assert pending_after == {"pending": False}
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_compaction_flag_survives_restart_and_restores(
    tmp_config, loaded_persona
):
    """The most realistic scenario: orchestrator restarts (cron,
    reboot, crash) between PreCompact and UserPromptSubmit. The flag
    in local SQLite must survive and trigger restoration on the next
    orchestrator run."""
    orch1 = Orchestrator(tmp_config)
    async with orch1.running() as o:
        o.set_loaded_persona(loaded_persona)
        o.set_compaction_flag(session_id="s-9")
    orch1.close()

    orch2 = Orchestrator(tmp_config)
    async with orch2.running() as o:
        o.set_loaded_persona(loaded_persona)
        assert o.compaction_flag_pending()
        payload = await o.consume_compaction(session_id="s-9")
        assert payload is not None
        assert payload["persona_identity"]["handle"] == "eve"
    orch2.close()
