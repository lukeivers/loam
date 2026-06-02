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

"""AC.EG-CORE.5 — per-item approve/redact/decline.

The released payload contains EXACTLY the approved + redacted items and
structurally excludes declined items; a redacted item ships its replacement
bytes, never the original.
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
from loam.egress_consent.review import apply_decision

ALLOWED = {"loam-feedback-intake"}


def _bundle():
    return EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(
            EgressItem.new(
                kind=ItemKind.freeform_text,
                plain_summary="A note",
                exact_bytes=b"approved-note",
                decision=ItemDecision.pending,
                item_id="note",
            ),
            EgressItem.new(
                kind=ItemKind.file,
                plain_summary="A file with a name in it",
                exact_bytes=b"my name is Jane Doe",
                decision=ItemDecision.pending,
                item_id="file",
            ),
            EgressItem.new(
                kind=ItemKind.log_line,
                plain_summary="A private log",
                exact_bytes=b"PRIVATE-DECLINED",
                decision=ItemDecision.pending,
                item_id="log",
            ),
        ),
    ).to_awaiting_review()


def test_declined_item_structurally_excluded_from_payload(transport) -> None:
    b = _bundle()
    b = apply_decision(b, "note", ItemDecision.approved)
    b = apply_decision(b, "file", ItemDecision.redacted, redaction=b"my name is [removed]")
    b = apply_decision(b, "log", ItemDecision.declined)

    approved = b.approve(approval_binding(b))
    EgressReleaseGate(allowed_endpoints=ALLOWED, transport=transport).release(approved)

    payload = transport.last_payload_bytes
    # Approved note present.
    assert b"approved-note" in payload
    # Redacted file ships the REPLACEMENT, never the original.
    assert b"my name is [removed]" in payload
    assert b"Jane Doe" not in payload
    # Declined log is NOT in the payload at all.
    assert b"PRIVATE-DECLINED" not in payload


def test_shippable_set_is_exactly_approved_plus_redacted() -> None:
    b = _bundle()
    b = apply_decision(b, "note", ItemDecision.approved)
    b = apply_decision(b, "file", ItemDecision.redacted, redaction=b"clean")
    b = apply_decision(b, "log", ItemDecision.declined)
    ship_ids = {it.item_id for it in b.shippable_items}
    assert ship_ids == {"note", "file"}


def test_redacted_item_ships_replacement_not_original() -> None:
    b = _bundle()
    b = apply_decision(b, "file", ItemDecision.redacted, redaction=b"REPLACEMENT")
    item = b.item("file")
    assert item.shipped_bytes == b"REPLACEMENT"
    assert item.exact_bytes == b"my name is Jane Doe"  # original retained, not shipped
