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

"""AC.EG-CORE.4 — content-identity binding.

An approval bound to item-set X is invalidated by ANY change to the set; the
gate refuses to release a mutated set under a stale approval. Mirrors the
safety-layer ``structural_hash`` semantics — any mutation invalidates.
"""

from __future__ import annotations

from loam.egress_consent import (
    EgressBundle,
    EgressItem,
    ItemDecision,
    ItemKind,
)
from loam.egress_consent.binding import approval_binding, binding_matches


def _item(item_id, body, decision=ItemDecision.approved):
    return EgressItem.new(
        kind=ItemKind.freeform_text,
        plain_summary="A note describing what went wrong",
        exact_bytes=body,
        decision=decision,
        item_id=item_id,
    )


def _bundle(items):
    return EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=items,
    )


def test_binding_matches_the_set_it_was_taken_over() -> None:
    b = _bundle((_item("a", b"one"), _item("b", b"two")))
    approved = b.approve(approval_binding(b))
    assert binding_matches(approved)


def test_added_item_invalidates_binding() -> None:
    b = _bundle((_item("a", b"one"),))
    approved = b.approve(approval_binding(b))
    # Slip in a NEW approved item, keep the stale binding.
    sneaky = EgressBundle(
        **{
            **approved.__dict__,
            "items": approved.items + (_item("c", b"slipped-in"),),
        }
    )
    assert not binding_matches(sneaky), "added item passed a stale approval"


def test_mutated_bytes_invalidate_binding() -> None:
    b = _bundle((_item("a", b"original"),))
    approved = b.approve(approval_binding(b))
    tampered = EgressBundle(
        **{**approved.__dict__, "items": (_item("a", b"TAMPERED"),)}
    )
    assert not binding_matches(tampered)


def test_redaction_change_invalidates_binding() -> None:
    b = _bundle((_item("a", b"has a secret"),))
    approved = b.approve(approval_binding(b))
    redacted = approved.items[0].with_redaction(b"scrubbed")
    changed = EgressBundle(**{**approved.__dict__, "items": (redacted,)})
    assert not binding_matches(changed)


def test_declining_an_item_invalidates_binding() -> None:
    b = _bundle((_item("a", b"one"), _item("b", b"two")))
    approved = b.approve(approval_binding(b))
    # User declines b after approval — the shippable set shrank.
    declined_b = approved.items[1].with_decision(ItemDecision.declined)
    changed = EgressBundle(
        **{**approved.__dict__, "items": (approved.items[0], declined_b)}
    )
    assert not binding_matches(changed)


def test_reordering_does_not_invalidate_binding() -> None:
    """Order is not identity — a reorder of the same set still matches."""
    b = _bundle((_item("a", b"one"), _item("b", b"two")))
    approved = b.approve(approval_binding(b))
    reordered = EgressBundle(
        **{**approved.__dict__, "items": (approved.items[1], approved.items[0])}
    )
    assert binding_matches(reordered)
