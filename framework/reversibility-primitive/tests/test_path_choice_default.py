"""R19: default path preference — fully_reversible > compensatable >
irreversible. Emits `path_chosen` with the right attributes."""

from __future__ import annotations

from loam.reversibility_primitive import rank_alternatives
from loam.scope_of_work import ReversibilityClass

from .conftest import make_spec


def test_R19_default_prefers_fully_reversible() -> None:
    irr = make_spec(reversibility=ReversibilityClass.irreversible)
    rev = make_spec(reversibility=ReversibilityClass.fully_reversible)
    ranked = rank_alternatives([irr, rev])
    assert ranked.chosen_class == "fully_reversible"
    assert ranked.chosen_index == 1
    assert ranked.alternatives_count == 2
    assert ranked.alternative_classes == ("irreversible", "fully_reversible")
    assert ranked.reason == "default_preference"
    assert ranked.override is False
    assert ranked.downrank_warning is False


def test_R19_default_picks_first_on_tie() -> None:
    a = make_spec(reversibility=ReversibilityClass.fully_reversible)
    b = make_spec(reversibility=ReversibilityClass.fully_reversible)
    ranked = rank_alternatives([a, b])
    assert ranked.chosen_index == 0


def test_R19_compensatable_beats_irreversible() -> None:
    irr = make_spec(reversibility=ReversibilityClass.irreversible)
    comp = make_spec(reversibility=ReversibilityClass.compensatable)
    ranked = rank_alternatives([irr, comp])
    assert ranked.chosen_class == "compensatable"
    assert ranked.chosen_index == 1
