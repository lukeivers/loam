"""Heuristic-shaped HYPOTHESISED-band inference.

Per AC.RAILS.6 + Surface #4 — Cycle 3 produces HYPOTHESISED ACs
from heuristic-shaped inferences over already-extracted PLAUSIBLE
ACs (no LLM call). Each heuristic carries a rationale string
capturing its provenance so Cycle 4+ LLM-driven inference can swap
in under the same contract.

Per AC.DRY.3 (v0.1.8 Cycle 4b) — the per-heuristic
``BandedAC(... confidence=HYPOTHESISED, evidence=Evidence(
kind="inference", ...))`` boilerplate is delegated to
:func:`make_inferred_banded_ac` from
``loam_odd_extractor.lang._common.heuristic_helpers``. This module
retains the per-language regex tables + heuristic firing logic.

Heuristic patterns (extensible — Cycle 4+ extends this list):

- ``validates :foo, presence: true`` → "<Model> creation requires
  <foo>" (HYPOTHESISED — validation may be conditional / bypassed).
- ``validates :foo, uniqueness: true`` → "<foo> is unique across
  all <Model> instances" (HYPOTHESISED — same caveat).
- ``belongs_to :owner, polymorphic: true`` → "<Model> can belong
  to multiple owner types" (HYPOTHESISED — polymorphism may be
  unused).
- ``before_save :normalize_X`` → "<X> is normalized before
  persistence" (HYPOTHESISED — callback may have early returns).
- ``after_create :enqueue_X`` → "<X> is enqueued asynchronously
  after creation" (HYPOTHESISED — enqueue may be conditional).
"""

from __future__ import annotations

import re

from ...bands import BandedAC, ConfidenceBand
from .._common.heuristic_helpers import make_inferred_banded_ac


# Regex to extract the model name from active_record AC IDs.
_MODEL_AC_RE = re.compile(
    r"^AC\.RAILS\.active_record\.([a-z0-9_]+)\."
)


def _model_name_from_ac_id(ac_id: str) -> str | None:
    m = _MODEL_AC_RE.match(ac_id)
    if not m:
        return None
    return m.group(1)


def infer_domain_rules(
    banded_acs: list[BandedAC],
) -> list[BandedAC]:
    """Produce HYPOTHESISED BandedACs from already-extracted
    PLAUSIBLE ACs.

    Each heuristic that fires emits one HYPOTHESISED BandedAC with
    ``evidence.kind="inference"`` and a non-empty ``rationale``
    field naming the source heuristic + the source AC's ac_id.
    """
    out: list[BandedAC] = []

    for ac in banded_acs:
        if ac.confidence is not ConfidenceBand.PLAUSIBLE:
            continue
        text = ac.text
        ac_id = ac.ac_id

        # Heuristic 1: validates :foo, presence: true → "<Model>
        # requires <foo> to be created."
        m = re.match(
            r"^(\w+) declares validates :(\w+), presence: true",
            text,
        ) or re.match(
            r"^(\w+) declares validates_presence_of :(\w+)",
            text,
        )
        if m:
            model, attr = m.group(1), m.group(2)
            out.append(
                make_inferred_banded_ac(
                    ac_id=(
                        f"AC.RAILS.inferred.required_on_create."
                        f"{model.lower()}.{attr}"
                    ),
                    text=(
                        f"Inferred: {model} creation requires "
                        f"{attr} to be present"
                    ),
                    rationale=(
                        f"heuristic: presence-validator on "
                        f"{model}.{attr} → infers required-on-"
                        f"create. Source AC: {ac_id}"
                    ),
                    source_ac=ac,
                )
            )
            continue

        # Heuristic 2: validates :foo, uniqueness: true (or
        # validates_uniqueness_of :foo) → uniqueness inference.
        m = re.match(
            r"^(\w+) declares validates :(\w+), uniqueness: true",
            text,
        ) or re.match(
            r"^(\w+) declares validates_uniqueness_of :(\w+)",
            text,
        )
        if m:
            model, attr = m.group(1), m.group(2)
            out.append(
                make_inferred_banded_ac(
                    ac_id=(
                        f"AC.RAILS.inferred.unique."
                        f"{model.lower()}.{attr}"
                    ),
                    text=(
                        f"Inferred: {attr} is unique across all "
                        f"{model} instances"
                    ),
                    rationale=(
                        f"heuristic: uniqueness-validator on "
                        f"{model}.{attr} → infers global-"
                        f"uniqueness. Source AC: {ac_id}"
                    ),
                    source_ac=ac,
                )
            )
            continue

        # Heuristic 3: polymorphic belongs_to → multiple owner types.
        m = re.match(
            r"^(\w+) has polymorphic belongs_to :(\w+)",
            text,
        )
        if m:
            model, assoc = m.group(1), m.group(2)
            out.append(
                make_inferred_banded_ac(
                    ac_id=(
                        f"AC.RAILS.inferred.polymorphic_owner."
                        f"{model.lower()}.{assoc}"
                    ),
                    text=(
                        f"Inferred: {model} can be owned by "
                        f"multiple types via {assoc}"
                    ),
                    rationale=(
                        f"heuristic: polymorphic belongs_to "
                        f"{model}.{assoc} → infers multi-type "
                        f"ownership. Source AC: {ac_id}"
                    ),
                    source_ac=ac,
                )
            )
            continue

        # Heuristic 4: before_save :normalize_X → normalisation.
        m = re.match(
            r"^(\w+) has before_save :normalize_(\w+)",
            text,
        )
        if m:
            model, target = m.group(1), m.group(2)
            out.append(
                make_inferred_banded_ac(
                    ac_id=(
                        f"AC.RAILS.inferred.normalised_before_save."
                        f"{model.lower()}.{target}"
                    ),
                    text=(
                        f"Inferred: {model}.{target} is normalised "
                        f"before persistence"
                    ),
                    rationale=(
                        f"heuristic: before_save :normalize_"
                        f"{target} on {model} → infers "
                        f"pre-persistence normalisation. "
                        f"Source AC: {ac_id}"
                    ),
                    source_ac=ac,
                )
            )
            continue

        # Heuristic 5: after_create :enqueue_X → async enqueue.
        m = re.match(
            r"^(\w+) has after_create :enqueue_(\w+)",
            text,
        )
        if m:
            model, target = m.group(1), m.group(2)
            out.append(
                make_inferred_banded_ac(
                    ac_id=(
                        f"AC.RAILS.inferred.async_after_create."
                        f"{model.lower()}.{target}"
                    ),
                    text=(
                        f"Inferred: {target} is enqueued "
                        f"asynchronously after {model} creation"
                    ),
                    rationale=(
                        f"heuristic: after_create :enqueue_"
                        f"{target} on {model} → infers async "
                        f"enqueue. Source AC: {ac_id}"
                    ),
                    source_ac=ac,
                )
            )

    return out
