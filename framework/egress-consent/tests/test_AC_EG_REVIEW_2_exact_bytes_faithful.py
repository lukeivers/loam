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

"""AC.EG-REVIEW.2 — exact-bytes faithfulness.

The exact-bytes expansion for an item is byte-faithful to what the gate would
actually send for that item — the label cannot lie about the contract. Both
the expansion AND the gate's payload read the SAME ``shipped_bytes`` property,
so they cannot diverge.
"""

from __future__ import annotations

from loam.egress_consent import (
    EgressBundle,
    EgressItem,
    ItemDecision,
    ItemKind,
)
from loam.egress_consent.binding import approval_binding
from loam.egress_consent.gate import EgressReleaseGate
from loam.egress_consent.review import render_exact_bytes

ALLOWED = {"loam-feedback-intake"}


def test_approved_item_expansion_equals_gate_payload(transport) -> None:
    item = EgressItem.new(
        kind=ItemKind.freeform_text,
        plain_summary="A note",
        exact_bytes=b"the exact message that ships",
        decision=ItemDecision.approved,
        item_id="a",
    )
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(item,),
    )
    # The expansion the user sees:
    shown = render_exact_bytes(item)
    # What the gate actually sends:
    approved = b.approve(approval_binding(b))
    EgressReleaseGate(allowed_endpoints=ALLOWED, transport=transport).release(approved)
    sent = transport.last_payload_bytes
    assert shown == sent == b"the exact message that ships"


def test_redacted_item_expansion_shows_replacement_matches_sent(transport) -> None:
    item = EgressItem.new(
        kind=ItemKind.file,
        plain_summary="A file",
        exact_bytes=b"my secret name is Jane",
        decision=ItemDecision.pending,
        item_id="a",
    ).with_redaction(b"my name is [removed]")
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(item,),
    )
    shown = render_exact_bytes(item)
    approved = b.approve(approval_binding(b))
    EgressReleaseGate(allowed_endpoints=ALLOWED, transport=transport).release(approved)
    sent = transport.last_payload_bytes
    # The expansion shows the REPLACEMENT, exactly what is sent; never the original.
    assert shown == sent == b"my name is [removed]"
    assert b"Jane" not in shown
