"""AC38.1 — `lifted_from` field exists on `ObjectiveSpec` and validates.

Plan: docs/rebuild/plans/amendment-38-objective-tracker-schema-widening.md
§4 AC38.1.

Outcome (paraphrased from the AC):

  - Optional structured field `lifted_from` defaults to `None`.
  - When set, validates `source_doc` (non-empty), `source_ac`
    (non-empty), `source_commit` (optional non-empty).
  - `lifted_from: null` round-trips through `model_validate` →
    serialisation → `model_validate` to an equivalent record.
  - Omission validates with `lifted_from is None`.
  - Malformed `lifted_from` (missing required keys, wrong types,
    extra keys per `extra="forbid"`, non-dict scalars) rejects.
  - Existing D1 contract tests keep passing — covered by
    AC38.5's reference to the unchanged baseline suite.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam.objective_tracker.spec import (
    LiftedFrom,
    ObjectiveSpec,
    ProseCriterion,
    TimeBound,
)
from tests.conftest import make_user_root_spec


# ---- LiftedFrom construction gates -----------------------------------


def test_AC38_1_lifted_from_all_three_keys_validates() -> None:
    lf = LiftedFrom(
        source_doc="docs/rebuild/VALUE_PROPOSITION.md",
        source_ac="AC.PO.1",
        source_commit="5ad573d",
    )
    assert lf.source_doc == "docs/rebuild/VALUE_PROPOSITION.md"
    assert lf.source_ac == "AC.PO.1"
    assert lf.source_commit == "5ad573d"


def test_AC38_1_lifted_from_without_source_commit_validates() -> None:
    lf = LiftedFrom(
        source_doc="docs/rebuild/VALUE_PROPOSITION.md",
        source_ac="AC.PO.2",
    )
    assert lf.source_commit is None


def test_AC38_1_lifted_from_empty_source_doc_rejects() -> None:
    with pytest.raises(ValidationError):
        LiftedFrom(source_doc="", source_ac="AC.PO.1")


def test_AC38_1_lifted_from_empty_source_ac_rejects() -> None:
    with pytest.raises(ValidationError):
        LiftedFrom(source_doc="x", source_ac="")


def test_AC38_1_lifted_from_empty_source_commit_rejects() -> None:
    with pytest.raises(ValidationError):
        LiftedFrom(
            source_doc="x", source_ac="AC.PO.1", source_commit="   "
        )


def test_AC38_1_lifted_from_extra_key_rejects() -> None:
    with pytest.raises(ValidationError):
        LiftedFrom.model_validate(
            {
                "source_doc": "x",
                "source_ac": "AC.PO.1",
                "extra": "boom",
            }
        )


def test_AC38_1_lifted_from_missing_required_key_rejects() -> None:
    with pytest.raises(ValidationError):
        LiftedFrom.model_validate({"source_doc": "x"})


def test_AC38_1_lifted_from_wrong_type_rejects() -> None:
    with pytest.raises(ValidationError):
        LiftedFrom.model_validate(
            {"source_doc": 1, "source_ac": "AC.PO.1"}
        )


# ---- ObjectiveSpec integration ---------------------------------------


def test_AC38_1_objective_spec_default_is_none() -> None:
    """Omitting `lifted_from` leaves it None — pre-widening behaviour."""
    spec = make_user_root_spec()
    assert spec.lifted_from is None


def test_AC38_1_objective_spec_explicit_null_is_none() -> None:
    """`lifted_from: null` (explicit) round-trips to None."""
    spec = ObjectiveSpec(
        goal="x",
        parent_id=None,
        acceptance_criteria=(ProseCriterion(criterion_id="c", prose="x"),),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
        lifted_from=None,
    )
    assert spec.lifted_from is None


def test_AC38_1_objective_spec_with_populated_lifted_from() -> None:
    lf = LiftedFrom(
        source_doc="docs/rebuild/plans/amendment-38.md",
        source_ac="AC38.1",
        source_commit="HEAD",
    )
    spec = ObjectiveSpec(
        goal="ship widening",
        parent_id=None,
        acceptance_criteria=(ProseCriterion(criterion_id="c", prose="x"),),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
        lifted_from=lf,
    )
    assert spec.lifted_from == lf
    assert spec.lifted_from.source_doc == "docs/rebuild/plans/amendment-38.md"


def test_AC38_1_objective_spec_round_trip_preserves_lifted_from() -> None:
    """Serialise → validate produces an equivalent ObjectiveSpec."""
    lf = LiftedFrom(
        source_doc="docs/rebuild/VALUE_PROPOSITION.md",
        source_ac="AC.PO.1",
    )
    original = ObjectiveSpec(
        goal="x",
        parent_id=None,
        acceptance_criteria=(ProseCriterion(criterion_id="c", prose="x"),),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
        lifted_from=lf,
    )
    dumped = original.model_dump(mode="json")
    rebuilt = ObjectiveSpec.model_validate(dumped)
    assert rebuilt == original
    assert rebuilt.lifted_from == lf


def test_AC38_1_objective_spec_round_trip_none_lifted_from() -> None:
    """A spec with no provenance round-trips with `lifted_from is None`."""
    original = make_user_root_spec()
    assert original.lifted_from is None
    dumped = original.model_dump(mode="json")
    rebuilt = ObjectiveSpec.model_validate(dumped)
    assert rebuilt.lifted_from is None


def test_AC38_1_objective_spec_extra_top_level_key_still_rejects() -> None:
    """`extra="forbid"` at the parent level is preserved post-widening."""
    with pytest.raises(ValidationError):
        ObjectiveSpec.model_validate(
            {
                "goal": "x",
                "parent_id": None,
                "acceptance_criteria": (
                    {"kind": "prose", "criterion_id": "c", "prose": "x"},
                ),
                "time_bound": {"evergreen": True},
                "authored_by": "user",
                "lifted_from": None,
                "rogue_field": "boom",
            }
        )


def test_AC38_1_lifted_from_malformed_in_spec_rejects() -> None:
    """A malformed `lifted_from` payload rejects at spec construction."""
    with pytest.raises(ValidationError):
        ObjectiveSpec.model_validate(
            {
                "goal": "x",
                "parent_id": None,
                "acceptance_criteria": (
                    {"kind": "prose", "criterion_id": "c", "prose": "x"},
                ),
                "time_bound": {"evergreen": True},
                "authored_by": "user",
                "lifted_from": {"source_doc": "x"},  # missing source_ac
            }
        )


def test_AC38_1_lifted_from_non_dict_scalar_rejects() -> None:
    with pytest.raises(ValidationError):
        ObjectiveSpec.model_validate(
            {
                "goal": "x",
                "parent_id": None,
                "acceptance_criteria": (
                    {"kind": "prose", "criterion_id": "c", "prose": "x"},
                ),
                "time_bound": {"evergreen": True},
                "authored_by": "user",
                "lifted_from": "not-a-dict",
            }
        )


def test_AC38_1_lifted_from_is_frozen() -> None:
    """`LiftedFrom` is frozen — same invariant `TimeBound` carries."""
    lf = LiftedFrom(source_doc="x", source_ac="AC.PO.1")
    with pytest.raises(ValidationError):
        lf.source_doc = "mutated"  # type: ignore[misc]
