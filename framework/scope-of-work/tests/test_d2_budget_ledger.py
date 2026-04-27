"""D2 — budget ledger with extension-request default.

Acceptance (brief D2):
- Ingesting a synthetic LLM-call sequence produces accurate
  budget-remaining at any point.
- A refund event corrects a prior debit.
- The per-prompt-name SQL view returns per-prompt costs matching a
  hand-calculated ground truth.
- Exceeding any budget axis (with default policy) transitions the
  scope to `paused` with reason `pending_extension_request`, emits an
  extension-request event, and waits for response.
- `extend()` resumes with the new budget; `reject()` transitions to
  `completed` (or `cancelled` if the scope had not produced a result).
- Per-scope override to halt-and-signal or throttle works correctly
  per axis.
"""

from __future__ import annotations

import json

import pytest

from src.events import (
    BudgetDebited,
    BudgetExtended,
    BudgetRefunded,
    ExtensionRejected,
    ExtensionRequested,
)
from src.spec import (
    Budget,
    BudgetAxis,
    BudgetExhaustionPolicy,
    ScopeState,
)
from tests.conftest import make_spec


async def test_synthetic_llm_call_sequence_accurate_remaining(runtime):
    spec = make_spec(budget=Budget(tokens=1000))
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    p = await runtime.debit(sid, input_tokens=100, output_tokens=50, prompt_name="p1")
    assert p.budget_tokens_remaining == 1000 - 150
    p = await runtime.debit(sid, input_tokens=200, output_tokens=80, prompt_name="p2")
    assert p.budget_tokens_remaining == 1000 - 150 - 280
    p = await runtime.debit(sid, input_tokens=10, output_tokens=5, prompt_name="p1")
    assert p.budget_tokens_remaining == 1000 - 150 - 280 - 15


async def test_refund_corrects_a_prior_debit(runtime):
    spec = make_spec(budget=Budget(tokens=1000))
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    after_debit = await runtime.debit(
        sid, input_tokens=300, output_tokens=200, call_id="call-1"
    )
    assert after_debit.budget_tokens_remaining == 500
    after_refund = await runtime.refund(sid, "call-1", reason="llm timed out")
    assert after_refund.budget_tokens_remaining == 1000  # full refund


async def test_partial_refund_smaller_than_debit(runtime):
    spec = make_spec(budget=Budget(tokens=1000))
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    await runtime.debit(sid, input_tokens=300, output_tokens=200, call_id="c1")
    p = await runtime.refund(
        sid, "c1", input_tokens=100, output_tokens=0, reason="partial"
    )
    # Original 500 consumed - 100 refunded = 400 consumed.
    assert p.budget_tokens_remaining == 600


async def test_refund_unknown_call_raises(runtime):
    proj = await runtime.create(make_spec())
    await runtime.start(proj.scope_id)
    with pytest.raises(KeyError):
        await runtime.refund(proj.scope_id, "no-such-call")


async def test_per_prompt_name_view_matches_hand_calculation(runtime):
    spec = make_spec(budget=Budget(tokens=10000))
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    # Three calls under p1, one under p2; one of p1 partly refunded.
    await runtime.debit(sid, input_tokens=100, output_tokens=50, prompt_name="p1", call_id="a")
    await runtime.debit(sid, input_tokens=200, output_tokens=80, prompt_name="p1", call_id="b")
    await runtime.debit(sid, input_tokens=10, output_tokens=5, prompt_name="p1", call_id="c")
    await runtime.debit(sid, input_tokens=500, output_tokens=200, prompt_name="p2", call_id="d")
    # Refund call b fully.
    await runtime.refund(sid, "b", reason="failed")

    rows = runtime.per_prompt_costs()
    # Build expected hand-calculation:
    # p1 calls: a (150) + c (15) - b refunded (280 net 0) ⇒ 165 net tokens
    # p2 calls: d (700)
    by_name = {r["prompt_name"]: r for r in rows}
    assert by_name["p1"]["input_tokens"] == 100 + 10  # b refunded
    assert by_name["p1"]["output_tokens"] == 50 + 5
    assert by_name["p1"]["call_count"] == 3  # COUNT DISTINCT debits
    assert by_name["p2"]["input_tokens"] == 500
    assert by_name["p2"]["output_tokens"] == 200


# ---- exhaustion / extension default ---------------------------------


async def test_exhaustion_default_pauses_with_extension_request(runtime):
    spec = make_spec(budget=Budget(tokens=100))
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    p = await runtime.debit(sid, input_tokens=120)  # over budget
    assert p.state == ScopeState.paused
    assert p.pending_extension_axis == BudgetAxis.tokens
    # Pending-extension file written for human-readable surfacing.
    assert runtime.pending_extension_path(sid).exists()
    # Event log carries the extension request.
    events = runtime.store.events_for(sid)
    assert any(isinstance(e, ExtensionRequested) for e in events)


async def test_extend_resumes_paused_scope(runtime):
    spec = make_spec(budget=Budget(tokens=100))
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    await runtime.debit(sid, input_tokens=120)
    assert runtime.get(sid).state == ScopeState.paused
    p = await runtime.extend(sid, BudgetAxis.tokens, 200)
    assert p.state == ScopeState.active
    assert p.budget_tokens_remaining == 100 + 200 - 120  # cap+ext-consumed
    assert not runtime.pending_extension_path(sid).exists()


async def test_reject_after_results_completes(runtime):
    spec = make_spec(budget=Budget(tokens=100))
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    await runtime.evaluate_success_criterion(
        sid, criterion_id="c1", result="met", note="pre-exhaust"
    )
    await runtime.debit(sid, input_tokens=120)
    p = await runtime.reject(sid)
    assert p.state == ScopeState.completed
    events = runtime.store.events_for(sid)
    assert any(isinstance(e, ExtensionRejected) for e in events)


async def test_reject_without_results_cancels(runtime):
    spec = make_spec(budget=Budget(tokens=100))
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    await runtime.debit(sid, input_tokens=120)
    p = await runtime.reject(sid)
    assert p.state == ScopeState.cancelled


# ---- per-axis override ------------------------------------------------


async def test_halt_and_signal_policy_escalates(runtime):
    spec = make_spec(
        budget=Budget(tokens=50, tokens_policy=BudgetExhaustionPolicy.halt_and_signal)
    )
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    p = await runtime.debit(sid, input_tokens=80)
    assert p.state == ScopeState.escalated


async def test_throttle_policy_pauses_without_extension_request(runtime):
    spec = make_spec(
        budget=Budget(tokens=50, tokens_policy=BudgetExhaustionPolicy.throttle)
    )
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    p = await runtime.debit(sid, input_tokens=80)
    assert p.state == ScopeState.paused
    assert p.pending_extension_axis is None  # throttle does NOT request


async def test_per_axis_overrides_independent(runtime):
    """Tokens use halt_and_signal; money uses default request_extension."""
    spec = make_spec(
        budget=Budget(
            tokens=10000,
            money_cents=10,  # tiny money cap
            tokens_policy=BudgetExhaustionPolicy.halt_and_signal,
            money_policy=BudgetExhaustionPolicy.request_extension,
        )
    )
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    p = await runtime.debit(sid, input_tokens=100, money_cents=20)
    assert p.state == ScopeState.paused
    assert p.pending_extension_axis == BudgetAxis.money
