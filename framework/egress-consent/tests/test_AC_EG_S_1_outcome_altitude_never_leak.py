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

"""AC.EG-S.1 — outcome-altitude (outcome-altitude: true).

A real end-to-end run at the production entry-point, NO pre-arranged state:
assemble a real bundle from real signals -> render the real review surface ->
user declines one item + redacts one + approves the rest -> release -> assert
(a) the off-machine payload contains EXACTLY the approved/redacted set and NOT
the declined item or its bytes, and (b) an attempt to release a *mutated*
bundle under the prior approval is REFUSED.

No stubbed gate, no pre-seeded payload — the gate runs in full and the
RecordingTransport observes exactly what (if anything) left.

THE NEVER-LEAK GUARANTEE, exercised: this is the test that proves a real
egress attempt with no approval leaks nothing, and that the approved-set-only
payload excludes the declined item byte-for-byte.
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
from loam.egress_consent.gate import EgressRefused, EgressReleaseGate, release
from loam.egress_consent.review import (
    apply_decision,
    render_exact_bytes,
    render_review,
)

ALLOWED = {"loam-feedback-intake"}


def _real_signals_bundle() -> EgressBundle:
    """Assemble a real multi-item bundle — no monkeypatch, no injected state."""
    return EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=(
            EgressItem.new(
                kind=ItemKind.freeform_text,
                plain_summary="A note describing what went wrong",
                exact_bytes=b"the save button did nothing",
                decision=ItemDecision.pending,
                item_id="note",
            ),
            EgressItem.new(
                kind=ItemKind.system_fact,
                plain_summary="Which version of loam you are on",
                exact_bytes=b"1.0.1",
                decision=ItemDecision.pending,
                item_id="version",
            ),
            EgressItem.new(
                kind=ItemKind.file,
                plain_summary="The file you were working on",
                exact_bytes=b"private contents of my file with my name Jane",
                decision=ItemDecision.pending,
                item_id="file",
            ),
            EgressItem.new(
                kind=ItemKind.log_line,
                plain_summary="A recent activity log",
                exact_bytes=b"RAW-LOG-WITH-A-PATH-/Users/jane/secret",
                decision=ItemDecision.pending,
                item_id="log",
            ),
        ),
    ).to_awaiting_review()


def test_real_egress_with_no_approval_leaks_nothing(transport) -> None:
    """The prime never-leak AC: a real release attempt, no approval, no egress."""
    bundle = _real_signals_bundle()
    # The user assembled and abandoned — a real release attempt happens anyway.
    with pytest.raises(EgressRefused):
        release(bundle, allowed_endpoints=ALLOWED, transport=transport)
    assert transport.sends == [], "data left the machine with no approval"


def test_end_to_end_decline_redact_approve_then_release(transport) -> None:
    bundle = _real_signals_bundle()

    # The user sees the REAL review surface (no internal vocabulary).
    surface = render_review(bundle)
    assert "loam would send" in surface

    # Per-item decisions: approve note + version, redact the file (scrub the
    # name), decline the raw log entirely.
    bundle = apply_decision(bundle, "note", ItemDecision.approved)
    bundle = apply_decision(bundle, "version", ItemDecision.approved)
    bundle = apply_decision(
        bundle, "file", ItemDecision.redacted,
        redaction=b"private contents of my file with my name [removed]",
    )
    bundle = apply_decision(bundle, "log", ItemDecision.declined)

    # The exact-bytes expansion the user can inspect for the redacted item is
    # faithful to what will ship.
    redacted_item = bundle.item("file")
    assert b"Jane" not in render_exact_bytes(redacted_item)

    # Approve the exact set, then release through the REAL gate.
    approved = bundle.approve(approval_binding(bundle))
    out = EgressReleaseGate(allowed_endpoints=ALLOWED, transport=transport).release(
        approved
    )

    payload = transport.last_payload_bytes
    # (a) EXACTLY the approved/redacted set leaves.
    assert b"the save button did nothing" in payload  # approved note
    assert b"1.0.1" in payload  # approved version
    assert b"my name [removed]" in payload  # redacted file replacement
    # NOT the declined log, NOT the original file name.
    assert b"RAW-LOG-WITH-A-PATH" not in payload
    assert b"/Users/jane/secret" not in payload
    assert b"my name Jane" not in payload
    assert out.state.value == "RELEASED"


def test_mutated_bundle_under_prior_approval_is_refused(transport) -> None:
    bundle = _real_signals_bundle()
    bundle = apply_decision(bundle, "note", ItemDecision.approved)
    bundle = apply_decision(bundle, "version", ItemDecision.approved)
    bundle = apply_decision(bundle, "file", ItemDecision.declined)
    bundle = apply_decision(bundle, "log", ItemDecision.declined)
    approved = bundle.approve(approval_binding(bundle))

    # (b) Tamper: swap in a new approved item but keep the OLD approval binding.
    tampered_items = approved.items + (
        EgressItem.new(
            kind=ItemKind.file,
            plain_summary="A file the user never approved",
            exact_bytes=b"EXFILTRATED-DATA",
            decision=ItemDecision.approved,
            item_id="sneaky",
        ),
    )
    stale = EgressBundle(**{**approved.__dict__, "items": tampered_items})

    with pytest.raises(EgressRefused) as ei:
        EgressReleaseGate(allowed_endpoints=ALLOWED, transport=transport).release(
            stale
        )
    assert ei.value.reason == "approval_binding_mismatch_post_mutation"
    assert transport.sends == [], "a mutated bundle leaked under a stale approval"
