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

"""AC.EG-CORE.1 — default is no-egress.

A bundle assembled but never explicitly approved-and-released emits nothing
off-machine. Every non-APPROVED state is a no-egress state; the gate will not
release from any of them.
"""

from __future__ import annotations

from loam.egress_consent import (
    EgressBundle,
    EgressItem,
    ItemDecision,
    ItemKind,
)
from loam.egress_consent.bundle import NO_EGRESS_STATES, BundleState
from loam.egress_consent.gate import EgressRefused, release


def _bundle(state: BundleState) -> EgressBundle:
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(
            EgressItem.new(
                kind=ItemKind.freeform_text,
                plain_summary="A note describing what went wrong",
                exact_bytes=b"it broke",
                decision=ItemDecision.approved,
            ),
        ),
    )
    # Drive into the requested non-APPROVED state via the public FSM.
    return EgressBundle(**{**b.__dict__, "state": state})


def test_freshly_assembled_bundle_defaults_to_drafting() -> None:
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
    )
    assert b.state == BundleState.DRAFTING
    assert b.state in NO_EGRESS_STATES
    assert b.approval_binding is None


def test_no_release_from_any_non_approved_state(transport) -> None:
    """A bundle in any no-egress state cannot release — transport never runs."""
    for state in NO_EGRESS_STATES:
        b = _bundle(state)
        try:
            release(
                b,
                allowed_endpoints={"loam-feedback-intake"},
                transport=transport,
            )
            assert False, f"released from no-egress state {state}"
        except EgressRefused:
            pass
    assert transport.sends == [], "egress occurred from a no-egress state"


def test_abandoned_review_emits_nothing(transport) -> None:
    """Assemble, move to review, then walk away — nothing leaves."""
    b = EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(
            EgressItem.new(
                kind=ItemKind.freeform_text,
                plain_summary="A note describing what went wrong",
                exact_bytes=b"it broke",
                decision=ItemDecision.pending,
            ),
        ),
    ).to_awaiting_review()
    # The session ends here. No approval, no release call. Assert no egress.
    assert transport.sends == []
    assert b.state in NO_EGRESS_STATES
