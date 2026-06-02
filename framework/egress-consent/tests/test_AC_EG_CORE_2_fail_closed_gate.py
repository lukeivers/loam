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

"""AC.EG-CORE.2 — fail-closed release gate.

The gate refuses on each of: not-approved, absent binding, binding-mismatch
(post-approval mutation), any pending item, unknown destination. Each refusal
RAISES before any send — a refused release sends nothing.
"""

from __future__ import annotations

import pytest

from loam.egress_consent import (
    EgressBundle,
    EgressItem,
    ItemDecision,
    ItemKind,
)
from loam.egress_consent.binding import approval_binding
from loam.egress_consent.bundle import BundleState
from loam.egress_consent.gate import (
    REASON_BINDING_ABSENT,
    REASON_BINDING_MISMATCH,
    REASON_NOT_APPROVED,
    REASON_PENDING_ITEM,
    REASON_UNKNOWN_DESTINATION,
    EgressRefused,
    EgressReleaseGate,
)

ALLOWED = {"loam-feedback-intake"}


def _item(decision=ItemDecision.approved, item_id="a", body=b"x"):
    return EgressItem.new(
        kind=ItemKind.freeform_text,
        plain_summary="A note describing what went wrong",
        exact_bytes=body,
        decision=decision,
        item_id=item_id,
    )


def _gate(transport):
    return EgressReleaseGate(allowed_endpoints=ALLOWED, transport=transport)


def test_refuse_not_approved(transport) -> None:
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(_item(),),
    ).to_awaiting_review()
    with pytest.raises(EgressRefused) as ei:
        _gate(transport).release(b)
    assert ei.value.reason == REASON_NOT_APPROVED
    assert transport.sends == []


def test_refuse_binding_absent(transport) -> None:
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(_item(),),
    )
    # Force APPROVED state but leave the binding absent (the gate must catch it).
    b = EgressBundle(**{**b.__dict__, "state": BundleState.APPROVED})
    with pytest.raises(EgressRefused) as ei:
        _gate(transport).release(b)
    assert ei.value.reason == REASON_BINDING_ABSENT
    assert transport.sends == []


def test_refuse_pending_item(transport) -> None:
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(_item(ItemDecision.approved, "a"), _item(ItemDecision.pending, "b")),
    )
    # Force APPROVED + a binding, but leave a pending item present.
    b = EgressBundle(
        **{
            **b.__dict__,
            "state": BundleState.APPROVED,
            "approval_binding": approval_binding(b),
        }
    )
    with pytest.raises(EgressRefused) as ei:
        _gate(transport).release(b)
    assert ei.value.reason == REASON_PENDING_ITEM
    assert transport.sends == []


def test_refuse_binding_mismatch_after_mutation(transport) -> None:
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(_item(ItemDecision.approved, "a", b"original"),),
    )
    approved = b.approve(approval_binding(b))
    # Mutate the shipped bytes of the approved item but keep the stale binding.
    mutated_items = (_item(ItemDecision.approved, "a", b"TAMPERED"),)
    stale = EgressBundle(
        **{
            **approved.__dict__,
            "items": mutated_items,
            # state stays APPROVED, binding stays the OLD hash.
        }
    )
    with pytest.raises(EgressRefused) as ei:
        _gate(transport).release(stale)
    assert ei.value.reason == REASON_BINDING_MISMATCH
    assert transport.sends == []


def test_refuse_unknown_destination(transport) -> None:
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="somewhere else",
        destination_endpoint="not-on-the-allow-list",
        items=(_item(),),
    )
    approved = b.approve(approval_binding(b))
    with pytest.raises(EgressRefused) as ei:
        _gate(transport).release(approved)
    assert ei.value.reason == REASON_UNKNOWN_DESTINATION
    assert transport.sends == []


def test_pass_sends_exactly_once(transport) -> None:
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(_item(ItemDecision.approved, "a", b"hello"),),
    )
    approved = b.approve(approval_binding(b))
    out = _gate(transport).release(approved)
    assert out.state == BundleState.RELEASED
    assert len(transport.sends) == 1
    assert transport.last_payload_bytes == b"hello"
