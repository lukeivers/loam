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

"""The EgressBundle lifecycle — the unit the release gate guards.

The bundle FSM is the structural half of the never-leak guarantee
(plan §4.2): **default-everywhere is a no-egress state.** A bundle that is
never explicitly driven to ``APPROVED`` and then ``RELEASED`` cannot emit.
Crash, timeout, abandoned review, ambiguous input — every non-happy path
leaves the bundle in ``DRAFTING`` / ``AWAITING_REVIEW`` / ``REVIEWED`` /
``NO_EGRESS``, none of which the gate will release.

The only state from which the gate passes is ``APPROVED`` — and reaching it
requires that every item be approved-or-redacted (no item left ``pending``)
AND an ``approval_binding`` recorded over the exact approved set. The model
here makes the illegal states unrepresentable as far as practical and refuses
the transitions that would otherwise leak.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from enum import Enum


class ItemKind(str, Enum):
    """What an egress item is, in machine terms (drives the plain summary)."""

    log_line = "log-line"
    file = "file"
    system_fact = "system-fact"
    freeform_text = "freeform-text"
    metric = "metric"


class ItemDecision(str, Enum):
    """The per-item decision. Default is ``pending`` — an unreviewed item.

    The gate refuses a bundle with ANY ``pending`` item (plan §4.3): an
    unreviewed item is uncertainty, and the gate fail-closes on uncertainty.
    """

    pending = "pending"
    approved = "approved"
    redacted = "redacted"
    declined = "declined"


class BundleState(str, Enum):
    """The bundle FSM. Only ``APPROVED`` is releasable.

    ``RELEASED`` is the post-send terminal; ``NO_EGRESS`` is the
    fallback-taken / declined terminal. Both ``DRAFTING`` and
    ``AWAITING_REVIEW`` and ``REVIEWED`` are no-egress states.
    """

    DRAFTING = "DRAFTING"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    RELEASED = "RELEASED"
    NO_EGRESS = "NO_EGRESS"


#: The states from which NO off-machine send can occur. The gate releases
#: ONLY from ``APPROVED``; everything else here is a no-egress state. Exposed
#: so the never-leak invariant is a checkable constant, not a buried literal.
NO_EGRESS_STATES: frozenset[BundleState] = frozenset(
    {
        BundleState.DRAFTING,
        BundleState.AWAITING_REVIEW,
        BundleState.REVIEWED,
        BundleState.NO_EGRESS,
    }
)


@dataclass(frozen=True)
class EgressItem:
    """One candidate piece of content that *might* leave the machine.

    Frozen: a "change" produces a NEW item (via :func:`with_decision` /
    :func:`with_redaction`), so a stale reference can never silently mutate
    the set an approval was bound to. ``exact_bytes`` is the contract — the
    literal content that would be sent; ``plain_summary`` is the label.
    """

    item_id: str
    kind: ItemKind
    plain_summary: str
    exact_bytes: bytes
    decision: ItemDecision = ItemDecision.pending
    #: When ``decision == redacted``, the user-edited replacement bytes that
    #: ship in place of ``exact_bytes``. The original never leaves.
    redaction: bytes | None = None

    @staticmethod
    def new(
        *,
        kind: ItemKind,
        plain_summary: str,
        exact_bytes: bytes,
        decision: ItemDecision = ItemDecision.pending,
        item_id: str | None = None,
    ) -> "EgressItem":
        return EgressItem(
            item_id=item_id or uuid.uuid4().hex,
            kind=kind,
            plain_summary=plain_summary,
            exact_bytes=exact_bytes,
            decision=decision,
        )

    def with_decision(self, decision: ItemDecision) -> "EgressItem":
        """Return a copy with a new decision (clears redaction unless redacting)."""
        if decision == ItemDecision.redacted:
            return replace(self, decision=decision)
        return replace(self, decision=decision, redaction=None)

    def with_redaction(self, replacement: bytes) -> "EgressItem":
        """Return a copy marked ``redacted`` carrying *replacement* bytes."""
        return replace(
            self, decision=ItemDecision.redacted, redaction=replacement
        )

    @property
    def shipped_bytes(self) -> bytes:
        """The bytes that would actually leave for this item.

        ``approved`` -> ``exact_bytes``; ``redacted`` -> the replacement
        (the original NEVER leaves); anything else -> not shippable, so the
        gate must exclude it. This is the single source of truth the
        exact-bytes review expansion is bound to (AC.EG-REVIEW.2).
        """
        if self.decision == ItemDecision.approved:
            return self.exact_bytes
        if self.decision == ItemDecision.redacted:
            return self.redaction if self.redaction is not None else b""
        raise ValueError(
            f"item {self.item_id!r} with decision {self.decision.value!r} "
            "has no shippable bytes"
        )

    @property
    def is_shippable(self) -> bool:
        """True iff this item is part of the released payload (approved/redacted)."""
        return self.decision in (ItemDecision.approved, ItemDecision.redacted)


@dataclass(frozen=True)
class EgressBundle:
    """A candidate off-machine send. Default state ``DRAFTING`` — no-egress.

    Frozen + copy-on-change: every mutation produces a NEW bundle, so the
    content-identity binding (``approval_binding``) can never be silently
    out-of-date with the items — a mutated set is a *different* bundle and
    re-hashes differently (AC.EG-CORE.4).
    """

    bundle_id: str
    purpose: str
    #: Plain-language destination name + the actual endpoint identifier.
    destination_name: str
    destination_endpoint: str
    items: tuple[EgressItem, ...] = ()
    state: BundleState = BundleState.DRAFTING
    #: The content-identity hash of the APPROVED-or-redacted item set, recorded
    #: at approval time. Absent until the user approves. Re-derived + compared
    #: by the gate at release (plan §4.3).
    approval_binding: str | None = None

    @staticmethod
    def new(
        *,
        purpose: str,
        destination_name: str,
        destination_endpoint: str,
        items: tuple[EgressItem, ...] = (),
        bundle_id: str | None = None,
    ) -> "EgressBundle":
        return EgressBundle(
            bundle_id=bundle_id or uuid.uuid4().hex,
            purpose=purpose,
            destination_name=destination_name,
            destination_endpoint=destination_endpoint,
            items=items,
            state=BundleState.DRAFTING,
        )

    # --- item lookup -----------------------------------------------------

    def item(self, item_id: str) -> EgressItem:
        for it in self.items:
            if it.item_id == item_id:
                return it
        raise KeyError(item_id)

    @property
    def shippable_items(self) -> tuple[EgressItem, ...]:
        """The approved-or-redacted items — the released payload set.

        Declined items are STRUCTURALLY excluded here (not skipped at send
        time): they simply are not in this tuple (AC.EG-CORE.5).
        """
        return tuple(it for it in self.items if it.is_shippable)

    @property
    def has_pending(self) -> bool:
        return any(it.decision == ItemDecision.pending for it in self.items)

    # --- FSM transitions (copy-on-change) --------------------------------

    def with_items(self, items: tuple[EgressItem, ...]) -> "EgressBundle":
        """Replace the item set. Any item change invalidates a prior approval.

        Returning to a pre-approval state is the whole point: if the set
        changes, the recorded ``approval_binding`` no longer describes the
        current set, so the bundle drops back to ``AWAITING_REVIEW`` and the
        binding is cleared. The gate would refuse a stale binding anyway
        (AC.EG-CORE.4); clearing it here makes the model honest.
        """
        new_state = (
            self.state
            if self.state in (BundleState.DRAFTING,)
            else BundleState.AWAITING_REVIEW
        )
        return replace(
            self, items=items, state=new_state, approval_binding=None
        )

    def replace_item(self, item: EgressItem) -> "EgressBundle":
        """Replace one item by id; resets toward review (clears any approval)."""
        new_items = tuple(
            item if it.item_id == item.item_id else it for it in self.items
        )
        return self.with_items(new_items)

    def to_awaiting_review(self) -> "EgressBundle":
        """Move DRAFTING -> AWAITING_REVIEW once assembly is done."""
        return replace(self, state=BundleState.AWAITING_REVIEW)

    def to_no_egress(self) -> "EgressBundle":
        """Terminal no-egress: the user took the local fallback / declined all."""
        return replace(self, state=BundleState.NO_EGRESS)

    def approve(self, binding: str) -> "EgressBundle":
        """Record approval bound to *binding* and move to APPROVED.

        Refuses (raises) if any item is still ``pending`` — an approval can
        only be recorded over a fully-decided set. This is a structural
        guard, not a courtesy: the gate also refuses pending items, but the
        FSM should not even claim APPROVED with an undecided item.
        """
        if self.has_pending:
            raise ValueError(
                "cannot approve a bundle with pending (unreviewed) items"
            )
        return replace(
            self, state=BundleState.APPROVED, approval_binding=binding
        )

    def to_released(self) -> "EgressBundle":
        """Terminal: the gate passed and the approved set was sent."""
        return replace(self, state=BundleState.RELEASED)
