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

"""The fail-closed egress release gate — the single audited choke point.

This is the heart of the never-leak guarantee and the prime AC. It is the
SAME posture loam already uses to refuse an irreversible op without a
recoverable binding: a deterministic, no-LLM, fail-closed gate that refuses
BEFORE any side effect (here, before any socket opens), modelled directly on
the reversibility ``ActivationGate`` (``-32050`` raised before ``activate``
runs) and the safety-layer content-identity binding (``structural_hash`` —
any mutation invalidates an approval).

**The structural guarantee (plan §4.3):**

1. **Single choke point.** The ONLY function in this component that performs
   an off-machine send is :meth:`EgressReleaseGate.release` (and the
   module-level :func:`release` that wraps it). There is no other
   network-egress call site for user content (AC.EG-CORE.3, grep-verified).

2. **Fail-closed dispatch** (deterministic, no LLM):

       state != APPROVED              -> REFUSE (nothing approved yet)
       approval_binding absent        -> REFUSE (no recorded approval)
       binding != hash(current set)   -> REFUSE (mutated after approval)
       any item still pending         -> REFUSE (unreviewed item present)
       destination not allow-listed   -> REFUSE (unknown endpoint)
       else                           -> PASS -> send approved/redacted ONLY

   The refusal RAISES (``EgressRefused``) before the transport is ever
   called — identical posture to the reversibility gate raising ``-32050``
   before the orchestrator's ``activate`` runs.

3. **No transport without the gate.** The gate is constructed with the
   send transport; the transport is invoked ONLY on the single PASS path,
   ONLY with the approved/redacted bytes. There is no gate-skip path — like
   the reversibility gate having no resolver-absent bypass, this gate
   fail-closes instead of offering a gate-absent door.
"""

from __future__ import annotations

from typing import Callable

from .binding import binding_matches
from .bundle import BundleState, EgressBundle, ItemDecision

#: A send transport: takes (endpoint, payload-bytes-per-item) and performs the
#: actual off-machine send. Injected into the gate so the gate stays
#: deterministic + testable; the transport is the ONLY thing that touches the
#: network and it is invoked ONLY on the gate's single PASS path.
SendTransport = Callable[[str, tuple[bytes, ...]], None]


class EgressRefused(RuntimeError):
    """The release gate refused to release a bundle — fail-closed.

    Carries the machine reason (one of the five refusal conditions) so the
    refusal is auditable. Raised BEFORE any transport call: a refused release
    sends nothing.
    """

    def __init__(self, reason: str, bundle_id: str) -> None:
        self.reason = reason
        self.bundle_id = bundle_id
        super().__init__(f"egress refused for bundle {bundle_id!r}: {reason}")


# The five fail-closed refusal reasons (plan §4.3). Named so tests + audits
# reference the condition, not a string literal.
REASON_NOT_APPROVED = "state_not_approved"
REASON_BINDING_ABSENT = "approval_binding_absent"
REASON_BINDING_MISMATCH = "approval_binding_mismatch_post_mutation"
REASON_PENDING_ITEM = "pending_unreviewed_item_present"
REASON_UNKNOWN_DESTINATION = "destination_not_allow_listed"


class EgressReleaseGate:
    """The single fail-closed choke point for off-machine sends.

    Constructed with the destination allow-list + the send transport. Every
    release runs :meth:`check` (pure, deterministic) first; only a PASS
    invokes the transport. There is no method that sends without checking.
    """

    def __init__(
        self,
        *,
        allowed_endpoints: frozenset[str] | set[str] | tuple[str, ...],
        transport: SendTransport,
    ) -> None:
        self._allowed = frozenset(allowed_endpoints)
        self._transport = transport

    def check(self, bundle: EgressBundle) -> None:
        """Raise ``EgressRefused`` unless the bundle is releasable.

        Pure + deterministic — no side effects, no network. The order is
        deliberate: cheapest-and-most-fundamental refusals first, so the
        reason returned is the most specific true cause.
        """
        # 1. Must be in APPROVED. Every other state is a no-egress state.
        if bundle.state != BundleState.APPROVED:
            raise EgressRefused(REASON_NOT_APPROVED, bundle.bundle_id)

        # 2. An approval binding must have been recorded.
        if bundle.approval_binding is None:
            raise EgressRefused(REASON_BINDING_ABSENT, bundle.bundle_id)

        # 3. No item may still be pending (unreviewed = uncertainty).
        if bundle.has_pending:
            raise EgressRefused(REASON_PENDING_ITEM, bundle.bundle_id)

        # 4. The recorded binding must still describe the current set:
        #    any mutation after approval invalidates it (AC.EG-CORE.4).
        if not binding_matches(bundle):
            raise EgressRefused(REASON_BINDING_MISMATCH, bundle.bundle_id)

        # 5. The destination must be on the allow-list (unknown endpoint =
        #    refuse — we do not send user content to an unvetted sink).
        if bundle.destination_endpoint not in self._allowed:
            raise EgressRefused(
                REASON_UNKNOWN_DESTINATION, bundle.bundle_id
            )

    def release(self, bundle: EgressBundle) -> EgressBundle:
        """Check then send the approved/redacted set ONLY. Returns RELEASED.

        On any refusal, raises ``EgressRefused`` and sends NOTHING. On a PASS,
        the transport is invoked exactly once with the shippable bytes (the
        approved-or-redacted set; declined + pending items are not in the
        payload), and the bundle transitions to RELEASED.

        Defence-in-depth: even past the gate, the payload is built ONLY from
        ``is_shippable`` items — a declined item's bytes cannot reach the
        transport because they are never assembled into the payload.
        """
        self.check(bundle)
        shippable = bundle.shippable_items
        payload = tuple(it.shipped_bytes for it in shippable)
        # The single send. Nothing else in the component opens a socket for
        # user content (AC.EG-CORE.3).
        self._transport(bundle.destination_endpoint, payload)
        return bundle.to_released()


def release(
    bundle: EgressBundle,
    *,
    allowed_endpoints: frozenset[str] | set[str] | tuple[str, ...],
    transport: SendTransport,
) -> EgressBundle:
    """Convenience wrapper: construct the gate + release in one call.

    The same single choke point — there is no path to a send that does not
    construct a gate and call :meth:`EgressReleaseGate.release`.
    """
    gate = EgressReleaseGate(
        allowed_endpoints=allowed_endpoints, transport=transport
    )
    return gate.release(bundle)
