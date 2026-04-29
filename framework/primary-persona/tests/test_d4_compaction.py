"""D4 — compaction survival via replay-from-authoritative-sources.

Acceptance (brief D4):
- PreCompact hook writes a flag; UserPromptSubmit checks and triggers
  restoration exactly once.
- Restoration injects from authoritative sources:
    contract (persona identity + authority boundary)
    scope-of-work `list(filter)` (current scope + pending decisions)
    memory (recent corrections via provider)
- Canonical five-item survival list is intact after restoration.
- Simulated compact-and-restore round-trip works end-to-end.
- Flag is cleared after successful restoration; repeated calls do not
  re-inject.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.scope_of_work.runtime import ScopeRuntime
from loam.scope_of_work.spec import (
    Budget,
    ReversibilityClass,
    ScopeSpec,
    ScopeState,
    SuccessCriterion,
)

from loam.primary_persona.compaction import (
    CompactionSurvivor,
    SURVIVAL_LIST,
    build_survival_payload,
    clear_precompact_flag,
    consume_survival_payload,
    mark_precompact,
    precompact_flag_present,
)
from loam.primary_persona.loader import PersonaLoader

from tests.conftest import VALID_CONTRACT_YAML, write_persona_dir


@pytest.fixture
async def loaded_primary(workspace_with_primary: Path):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    return loader.primary()


@pytest.fixture
async def runtime(tmp_path: Path):
    rt = ScopeRuntime(db_path=tmp_path / "scope.db")
    yield rt
    rt.close()


# ---- flag file lifecycle --------------------------------------------


def test_mark_sets_flag(tmp_path: Path):
    path = mark_precompact(tmp_path)
    assert path.exists()
    assert precompact_flag_present(tmp_path)


def test_clear_removes_flag(tmp_path: Path):
    mark_precompact(tmp_path)
    clear_precompact_flag(tmp_path)
    assert not precompact_flag_present(tmp_path)


def test_clear_idempotent(tmp_path: Path):
    # Clearing a non-existent flag does not raise.
    clear_precompact_flag(tmp_path)


# ---- build payload from authoritative sources ----------------------


async def test_build_payload_identity_from_contract(loaded_primary, runtime):
    payload = build_survival_payload(persona=loaded_primary, runtime=runtime)
    assert payload.persona_identity["handle"] == "eve"
    assert payload.persona_identity["given_name"] == "Eve"
    assert payload.persona_identity["contract_version"] == "1.0.0"


async def test_build_payload_authority_from_contract(loaded_primary, runtime):
    payload = build_survival_payload(persona=loaded_primary, runtime=runtime)
    assert payload.authority_boundary == {
        "tier_a": "defer",
        "tier_b": "defer",
        "tier_c": "execute",
        "tier_d": "execute",
    }


async def test_build_payload_current_scope_from_runtime(loaded_primary, runtime):
    spec = ScopeSpec(
        goal="in-flight",
        constraints=(),
        budget=Budget(tokens=1000),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(SuccessCriterion(criterion_id="c1", description="d"),),
        observers=(),
        escalation_triggers=(),
    )
    await runtime.create(spec, scope_id="alpha")
    await runtime.start("alpha")

    payload = build_survival_payload(persona=loaded_primary, runtime=runtime)
    ids = {s["scope_id"] for s in payload.current_scope_context}
    assert "alpha" in ids


async def test_build_payload_pending_decisions_from_runtime(
    loaded_primary, runtime
):
    spec = ScopeSpec(
        goal="tiny",
        constraints=(),
        budget=Budget(tokens=10),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(SuccessCriterion(criterion_id="c1", description="d"),),
        observers=(),
        escalation_triggers=(),
    )
    await runtime.create(spec, scope_id="pending-one")
    await runtime.start("pending-one")
    await runtime.debit("pending-one", input_tokens=50)  # exceeds cap, pauses

    payload = build_survival_payload(persona=loaded_primary, runtime=runtime)
    pending_ids = {s["scope_id"] for s in payload.pending_decisions}
    assert "pending-one" in pending_ids


async def test_build_payload_corrections_via_provider(
    loaded_primary, runtime
):
    sample_corrections = [
        {"when": "2026-04-16T10:00:00Z", "correction": "Use plainer subject lines"},
        {"when": "2026-04-17T10:00:00Z", "correction": "Lead with the answer"},
    ]

    def provider(limit: int) -> list[dict]:
        return sample_corrections[:limit]

    payload = build_survival_payload(
        persona=loaded_primary,
        runtime=runtime,
        recent_corrections_provider=provider,
        corrections_limit=5,
    )
    assert len(payload.recent_corrections) == 2
    assert payload.recent_corrections[0]["correction"] == "Use plainer subject lines"


async def test_build_payload_provider_exception_degrades_gracefully(
    loaded_primary, runtime
):
    def bad_provider(limit: int):
        raise RuntimeError("memory unavailable")

    payload = build_survival_payload(
        persona=loaded_primary,
        runtime=runtime,
        recent_corrections_provider=bad_provider,
    )
    assert payload.recent_corrections == []


# ---- five-item canonical list ---------------------------------------


async def test_survival_list_enumerates_five_items():
    assert len(SURVIVAL_LIST) == 5
    assert "persona_identity" in SURVIVAL_LIST
    assert "authority_boundary" in SURVIVAL_LIST
    assert "current_scope_context" in SURVIVAL_LIST
    assert "pending_decisions" in SURVIVAL_LIST
    assert "recent_corrections" in SURVIVAL_LIST


async def test_payload_to_dict_covers_five_items(loaded_primary, runtime):
    payload = build_survival_payload(persona=loaded_primary, runtime=runtime)
    d = payload.to_dict()
    for item in SURVIVAL_LIST:
        assert item in d


# ---- consume lifecycle ----------------------------------------------


async def test_consume_returns_none_without_flag(
    tmp_path: Path, loaded_primary, runtime
):
    payload = consume_survival_payload(
        flag_dir=tmp_path, persona=loaded_primary, runtime=runtime
    )
    assert payload is None


async def test_consume_returns_payload_and_clears_flag(
    tmp_path: Path, loaded_primary, runtime
):
    mark_precompact(tmp_path)
    assert precompact_flag_present(tmp_path)
    payload = consume_survival_payload(
        flag_dir=tmp_path, persona=loaded_primary, runtime=runtime
    )
    assert payload is not None
    assert not precompact_flag_present(tmp_path)


async def test_consume_does_not_re_inject_on_second_call(
    tmp_path: Path, loaded_primary, runtime
):
    mark_precompact(tmp_path)
    first = consume_survival_payload(
        flag_dir=tmp_path, persona=loaded_primary, runtime=runtime
    )
    assert first is not None
    second = consume_survival_payload(
        flag_dir=tmp_path, persona=loaded_primary, runtime=runtime
    )
    assert second is None


# ---- end-to-end compact-and-restore simulation ---------------------


async def test_simulated_compaction_round_trip_preserves_list(
    tmp_path: Path, loaded_primary, runtime
):
    # Set up some in-flight state.
    spec = ScopeSpec(
        goal="pre-compact work",
        constraints=(),
        budget=Budget(tokens=1000),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(SuccessCriterion(criterion_id="c1", description="d"),),
        observers=(),
        escalation_triggers=(),
    )
    await runtime.create(spec, scope_id="survives")
    await runtime.start("survives")

    corrections = [{"when": "today", "correction": "be specific"}]

    # Simulate compaction event.
    mark_precompact(tmp_path)

    # First post-compaction UserPromptSubmit triggers restoration.
    payload = consume_survival_payload(
        flag_dir=tmp_path,
        persona=loaded_primary,
        runtime=runtime,
        recent_corrections_provider=lambda n: corrections[:n],
    )
    assert payload is not None

    # The five-item list is intact.
    assert payload.persona_identity["handle"] == "eve"
    assert payload.authority_boundary["tier_c"] == "execute"
    assert any(s["scope_id"] == "survives" for s in payload.current_scope_context)
    assert payload.recent_corrections == corrections
    # No flag remains.
    assert not precompact_flag_present(tmp_path)
