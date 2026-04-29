"""`rank_alternatives` — pure preference ranking over ScopeSpec variants.

R19–R20: default preference is `fully_reversible > compensatable >
irreversible`; caller-supplied `preference=<class>` overrides it and
emits the `override=True` + `downrank_warning=True` attributes on the
span when the chosen class is strictly less reversible than the best
available alternative.

Eve-inference #4 (proposal §8): default emits a path_chosen span for
every call including one-element lists. Builder's ruling below: when
`alternatives_count == 1`, no span is emitted — a single-element rank
carries no reversibility signal worth recording. This is a deviation
from the Eve inference the brief invited the builder to challenge;
see build report.
"""

from __future__ import annotations

from typing import Sequence

from loam.scope_of_work import ReversibilityClass, ScopeSpec

from . import observability as obs
from .spec import RankedAlternatives


# Lower index == more reversible == more preferred by default.
_PREFERENCE_ORDER = (
    ReversibilityClass.fully_reversible,
    ReversibilityClass.compensatable,
    ReversibilityClass.irreversible,
)
_RANK = {cls: i for i, cls in enumerate(_PREFERENCE_ORDER)}


def rank_alternatives(
    alternatives: Sequence[ScopeSpec],
    *,
    preference: ReversibilityClass | None = None,
) -> RankedAlternatives:
    """Rank a list of alternative specs.

    - Default: return the most reversible (lowest rank index). Ties
      resolve to the first occurrence in the input list (deterministic).
    - `preference` override: select the first alternative whose class
      matches the supplied preference. If no alternative matches, fall
      back to the default preference and emit the span with
      `override=True, downrank_warning=True` only if the fallback class
      is less reversible than the best available.

    Emits `loam.reversibility.path_chosen` except when `len(alternatives)
    == 1` (see module docstring).
    """
    if not alternatives:
        raise ValueError("rank_alternatives: alternatives must be non-empty")

    classes = [a.reversibility_class for a in alternatives]

    # --- override path -------------------------------------------------
    if preference is not None:
        matches = [i for i, c in enumerate(classes) if c == preference]
        if matches:
            chosen_index = matches[0]
            chosen_class = classes[chosen_index]
            reason = "caller_override"
            override = True
            best_available = min(_RANK[c] for c in classes)
            downrank_warning = _RANK[chosen_class] > best_available
            ranked = RankedAlternatives(
                chosen_index=chosen_index,
                chosen_class=chosen_class.value,
                alternatives_count=len(alternatives),
                alternative_classes=tuple(c.value for c in classes),
                reason=reason,
                override=override,
                downrank_warning=downrank_warning,
            )
            _emit_if_meaningful(ranked)
            return ranked
        # Requested preference not available → fall through to default
        # ranking. The path_chosen span still marks override=True so
        # the operator can see the requested class was absent.
        override = True
        reason = "caller_override_unavailable"
    else:
        override = False
        reason = "default_preference"

    # --- default ranking ---------------------------------------------
    best_rank = min(_RANK[c] for c in classes)
    chosen_index = next(
        i for i, c in enumerate(classes) if _RANK[c] == best_rank
    )
    chosen_class = classes[chosen_index]
    # downrank_warning is True only when the chosen class is less
    # reversible than the most-reversible alternative actually present.
    # In the default ranking path, chosen == best; so this is False.
    # In the override path, we've already computed it above. But if
    # the user passed `preference` and we fell through because no match
    # existed, the chosen class is still the best available, and there
    # is no downrank.
    downrank_warning = False
    ranked = RankedAlternatives(
        chosen_index=chosen_index,
        chosen_class=chosen_class.value,
        alternatives_count=len(alternatives),
        alternative_classes=tuple(c.value for c in classes),
        reason=reason,
        override=override,
        downrank_warning=downrank_warning,
    )
    _emit_if_meaningful(ranked)
    return ranked


def _emit_if_meaningful(ranked: RankedAlternatives) -> None:
    if ranked.alternatives_count <= 1:
        return
    obs.path_chosen(
        chosen_class=ranked.chosen_class,
        alternatives_count=ranked.alternatives_count,
        alternative_classes=list(ranked.alternative_classes),
        chosen_index=ranked.chosen_index,
        reason=ranked.reason,
        override=ranked.override,
        downrank_warning=ranked.downrank_warning,
    )
