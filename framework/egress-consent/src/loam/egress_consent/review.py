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

"""The two-layer review surface (plan §5) — what the user sees before any send.

Resolves the design's one genuine tension (transparency vs non-tech
simplicity):

* **Layer A — plain-language default.** A numbered list, one line per item,
  in the abstraction-first voice: what each item is, in human terms, + its
  current decision + the actions available. ZERO internal vocabulary — the
  rendered text is self-checked with the SAME probe the recovery surface uses
  (``find_internal_vocabulary``); a leak raises rather than shipping
  (AC.EG-REVIEW.1, Lens 1).

* **Layer B — exact-bytes expansion.** :func:`render_exact_bytes` returns the
  literal bytes the gate would send for an item — byte-faithful to
  ``EgressItem.shipped_bytes``, the SAME value the gate transmits
  (AC.EG-REVIEW.2). The plain summary is a label; the exact bytes are the
  contract, and the two cannot disagree because the expansion reads the
  contract directly.

:func:`apply_decision` drives the per-item approve / redact / decline model.
Deterministic, no LLM.
"""

from __future__ import annotations

from loam.self_correction.recovery_surface import find_internal_vocabulary

from .bundle import EgressBundle, EgressItem, ItemDecision


class ReviewSurfaceLeak(RuntimeError):
    """A rendered review surface leaked internal vocabulary — hard failure.

    AC.EG-REVIEW.1 is a hard invariant: the default view must be readable by
    a non-technical user with no internal IDs / paths / SHAs. A render that
    would leak fails loudly (mirrors ``RecoverySurfaceLeak``) rather than
    shipping the leak to the user.
    """


# Plain-language decision labels + per-item actions. No internal vocabulary.
_DECISION_LABEL: dict[ItemDecision, str] = {
    ItemDecision.pending: "not decided yet",
    ItemDecision.approved: "will send",
    ItemDecision.redacted: "will send (edited)",
    ItemDecision.declined: "held back",
}

_DECISION_ACTIONS: dict[ItemDecision, str] = {
    ItemDecision.pending: "show / send this / hold back",
    ItemDecision.approved: "show / hold back",
    ItemDecision.redacted: "show / hold back",
    ItemDecision.declined: "show / send this",
}


def render_review(bundle: EgressBundle) -> str:
    """Render Layer A — the plain-language default review view.

    A non-technical user reads this and acts on it: reply with a number to
    change an item, "send" to send what is marked, or "don't send anything"
    to keep it all on their computer. The rendered text is self-checked for
    internal vocabulary; a leak raises ``ReviewSurfaceLeak``.
    """
    n = len(bundle.items)
    will_send = sum(1 for it in bundle.items if it.is_shippable)
    lines: list[str] = []
    if n == 0:
        lines.append(
            "There is nothing to send. Nothing will leave your computer."
        )
    else:
        thing = "thing" if will_send == 1 else "things"
        lines.append(
            f"loam would send these {will_send} {thing} to "
            f"{bundle.destination_name}. Nothing is sent yet."
        )
        lines.append("")
        for idx, it in enumerate(bundle.items, start=1):
            label = _DECISION_LABEL[it.decision]
            actions = _DECISION_ACTIONS[it.decision]
            lines.append(
                f"  {idx}. {it.plain_summary}   [{label}]   ({actions})"
            )
        lines.append("")
        lines.append(
            'Reply with a number to change it, "send" to send what is '
            'marked, or "don\'t send anything" to keep it all on your '
            "computer."
        )
    text = "\n".join(lines)

    # The hard invariant (AC.EG-REVIEW.1): zero internal vocabulary. The
    # plain_summary fields are user-facing labels, but a careless caller
    # could pass a path / id; the probe is the structural backstop.
    hits = find_internal_vocabulary(text)
    if hits:
        raise ReviewSurfaceLeak(
            "review surface leaked internal vocabulary: "
            f"{[h.matched for h in hits]}"
        )
    return text


def render_exact_bytes(item: EgressItem) -> bytes:
    """Render Layer B — the exact bytes the gate would send for *item*.

    Byte-faithful to what the gate actually transmits: for an approved item
    the original ``exact_bytes``, for a redacted item the replacement bytes,
    via the SAME ``shipped_bytes`` property the gate's payload is built from
    (AC.EG-REVIEW.2). For a pending/declined item — which would NOT ship —
    the expansion shows the ``exact_bytes`` that are currently held, so the
    user can decide on the real content.
    """
    if item.is_shippable:
        return item.shipped_bytes
    # Not shippable in its current decision — show what is held so the user
    # sees the real content they are deciding about.
    return item.exact_bytes


def apply_decision(
    bundle: EgressBundle,
    item_id: str,
    decision: ItemDecision,
    *,
    redaction: bytes | None = None,
) -> EgressBundle:
    """Apply a per-item approve / redact / decline; return the new bundle.

    Redacting requires ``redaction`` bytes (the user-edited replacement).
    Any item change resets a prior approval (the bundle's copy-on-change
    discipline), so a decision made after approval invalidates that approval
    and the user must re-approve the new set — there is no way to slip a
    change past a stale approval (AC.EG-CORE.4 / .5).
    """
    item = bundle.item(item_id)
    if decision == ItemDecision.redacted:
        if redaction is None:
            raise ValueError("redact requires replacement bytes")
        new_item = item.with_redaction(redaction)
    else:
        new_item = item.with_decision(decision)
    return bundle.replace_item(new_item)
