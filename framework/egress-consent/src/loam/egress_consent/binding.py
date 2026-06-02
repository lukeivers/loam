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

"""Content-identity binding for an approved item set (AC.EG-CORE.4).

This mirrors the safety-layer's ``structural_hash`` semantics (Lens 1): an
approval binds to the EXACT content-identity of what the user approved, and
ANY mutation of that set (a new item creeps in, bytes change, a redaction
edits) produces a different hash and invalidates the approval. The safety
layer hashes a ScopeSpec; here we hash the approved-or-redacted EgressItem
set — same principle (canonical serialization -> SHA-256), applied to the
egress payload. A non-tech user cannot be tricked into "approving" item 3 and
having item 5 ride along: item 5 was not in the hashed set, so the binding
mismatches and the gate refuses (plan §4.3).

Deterministic, no LLM, no network.
"""

from __future__ import annotations

import hashlib
import json

from .bundle import EgressBundle, EgressItem


def _item_identity(item: EgressItem) -> dict[str, str]:
    """The content-identity fields of ONE shippable item.

    The identity is over what would actually LEAVE — the item id, its kind,
    and the exact bytes that ship (``shipped_bytes``: the original for an
    approved item, the replacement for a redacted one). The plain summary is
    a label and is deliberately NOT part of the identity: the contract is the
    bytes, and the binding must track the bytes.
    """
    return {
        "item_id": item.item_id,
        "kind": item.kind.value,
        "decision": item.decision.value,
        # Bytes -> hex so the JSON is deterministic + faithful to the wire.
        "shipped_bytes_sha256": hashlib.sha256(item.shipped_bytes).hexdigest(),
    }


def approval_binding(bundle: EgressBundle) -> str:
    """Deterministic content-identity hash of the APPROVED-or-redacted set.

    Computed over the shippable items (approved + redacted) ONLY — declined
    and pending items are not part of what the user approved to send and are
    not in the identity. The hash is order-independent (items sorted by id)
    so a reordering is not a spurious mutation, but any change to the set's
    membership or shipped bytes IS.
    """
    identities = sorted(
        (_item_identity(it) for it in bundle.shippable_items),
        key=lambda d: d["item_id"],
    )
    payload = json.dumps(
        {"purpose": bundle.purpose, "items": identities},
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def binding_matches(bundle: EgressBundle) -> bool:
    """True iff the bundle's recorded ``approval_binding`` still describes it.

    The gate calls this at release: it re-derives the binding over the
    CURRENT shippable set and compares to the hash recorded at approval. A
    mismatch means the set changed after approval — the gate refuses
    (AC.EG-CORE.4). A bundle with no recorded binding never matches.
    """
    if bundle.approval_binding is None:
        return False
    return approval_binding(bundle) == bundle.approval_binding
