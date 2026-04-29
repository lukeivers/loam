"""R20: caller-supplied preference override emits `override=True` and
`downrank_warning=True` when the chosen class is strictly less
reversible than the best available."""

from __future__ import annotations

from loam.reversibility_primitive import rank_alternatives
from loam.scope_of_work import ReversibilityClass

from .conftest import make_spec


def test_R20_override_to_irreversible_emits_downrank_warning() -> None:
    irr = make_spec(reversibility=ReversibilityClass.irreversible)
    rev = make_spec(reversibility=ReversibilityClass.fully_reversible)
    ranked = rank_alternatives(
        [rev, irr], preference=ReversibilityClass.irreversible
    )
    assert ranked.chosen_class == "irreversible"
    assert ranked.override is True
    assert ranked.downrank_warning is True
    assert ranked.reason == "caller_override"


def test_R20_override_to_same_class_no_downrank() -> None:
    """Overriding to the already-most-reversible class is not a downrank."""
    irr = make_spec(reversibility=ReversibilityClass.irreversible)
    rev = make_spec(reversibility=ReversibilityClass.fully_reversible)
    ranked = rank_alternatives(
        [irr, rev], preference=ReversibilityClass.fully_reversible
    )
    assert ranked.chosen_class == "fully_reversible"
    assert ranked.override is True
    assert ranked.downrank_warning is False


def test_R20_override_unavailable_falls_through() -> None:
    """Requested preference absent → fall back to default ranking but
    mark override=True so operators see the requested class was absent."""
    rev = make_spec(reversibility=ReversibilityClass.fully_reversible)
    ranked = rank_alternatives(
        [rev], preference=ReversibilityClass.irreversible
    )
    # alternatives_count == 1 path — telemetry suppressed but the
    # RankedAlternatives value is returned; verifying the shape.
    assert ranked.chosen_class == "fully_reversible"
    assert ranked.override is True
    assert ranked.reason == "caller_override_unavailable"
