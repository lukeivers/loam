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

"""AC38.3 — `query_projection_view(filter)` returns matching records.

Plan: docs/rebuild/plans/amendment-38-objective-tracker-schema-widening.md
§4 AC38.3.

Outcome (paraphrased from the AC):

  - Accepts an `ObjectiveFilter` covering at minimum `authored_by`
    and `lifted_from.source_doc`.
  - Records lacking `lifted_from` are excluded from any filter that
    names a `lifted_from_source_doc`.
  - Empty filter returns the full record set with deterministic
    ordering across calls.
"""

from __future__ import annotations

import pytest

from loam.objective_tracker.filter import ObjectiveFilter
from loam.objective_tracker.spec import LiftedFrom
from tests.conftest import make_user_root_spec


# ---- helpers ---------------------------------------------------------


VP_DOC = "docs/rebuild/VALUE_PROPOSITION.md"
PLAN_DOC = "docs/rebuild/plans/amendment-38.md"
OTHER_DOC = "docs/rebuild/plans/amendment-39.md"


async def _seed_mixed_population(rt):
    """Seed a population with a deterministic provenance mix:

      - alpha: user, lifted_from(VP_DOC, AC.PO.1)
      - beta:  user, lifted_from(VP_DOC, AC.PO.2)
      - gamma: user, lifted_from(PLAN_DOC, AC38.3)
      - delta: kai,  lifted_from is None
      - epsilon: user, lifted_from is None
    """
    out: dict[str, str] = {}
    out["alpha"] = (
        await rt.create(
            make_user_root_spec(goal="alpha").model_copy(
                update={
                    "lifted_from": LiftedFrom(
                        source_doc=VP_DOC, source_ac="AC.PO.1"
                    )
                }
            )
        )
    ).objective_id
    out["beta"] = (
        await rt.create(
            make_user_root_spec(goal="beta").model_copy(
                update={
                    "lifted_from": LiftedFrom(
                        source_doc=VP_DOC, source_ac="AC.PO.2"
                    )
                }
            )
        )
    ).objective_id
    out["gamma"] = (
        await rt.create(
            make_user_root_spec(goal="gamma").model_copy(
                update={
                    "lifted_from": LiftedFrom(
                        source_doc=PLAN_DOC, source_ac="AC38.3"
                    )
                }
            )
        )
    ).objective_id
    out["delta"] = (
        await rt.create(
            make_user_root_spec(goal="delta").model_copy(
                update={"authored_by": "kai", "lifted_from": None}
            )
        )
    ).objective_id
    out["epsilon"] = (
        await rt.create(
            make_user_root_spec(goal="epsilon").model_copy(
                update={"lifted_from": None}
            )
        )
    ).objective_id
    return out


# ---- AC38.3 verification --------------------------------------------


async def test_AC38_3_empty_filter_returns_full_set(tracker) -> None:
    ids = await _seed_mixed_population(tracker)
    out = tracker.query_projection_view(ObjectiveFilter())
    found = {p.objective_id for p in out}
    assert found == set(ids.values())


async def test_AC38_3_none_filter_returns_full_set(tracker) -> None:
    ids = await _seed_mixed_population(tracker)
    out = tracker.query_projection_view(None)
    found = {p.objective_id for p in out}
    assert found == set(ids.values())


async def test_AC38_3_filter_by_lifted_from_source_doc(tracker) -> None:
    ids = await _seed_mixed_population(tracker)
    out = tracker.query_projection_view(
        ObjectiveFilter(lifted_from_source_doc=VP_DOC)
    )
    found = {p.objective_id for p in out}
    # Only alpha + beta lifted from VP_DOC. delta + epsilon excluded
    # because their `lifted_from is None`. gamma excluded because its
    # source_doc differs.
    assert found == {ids["alpha"], ids["beta"]}


async def test_AC38_3_filter_excludes_records_with_no_lifted_from(
    tracker,
) -> None:
    """Records with `lifted_from is None` are NEVER returned when the
    filter names a `lifted_from_source_doc`."""
    ids = await _seed_mixed_population(tracker)
    out = tracker.query_projection_view(
        ObjectiveFilter(lifted_from_source_doc=PLAN_DOC)
    )
    found = {p.objective_id for p in out}
    assert found == {ids["gamma"]}
    assert ids["delta"] not in found
    assert ids["epsilon"] not in found


async def test_AC38_3_filter_by_authored_by_preserves_existing_semantics(
    tracker,
) -> None:
    ids = await _seed_mixed_population(tracker)
    out = tracker.query_projection_view(
        ObjectiveFilter(authored_by="user")
    )
    found = {p.objective_id for p in out}
    assert ids["delta"] not in found  # authored_by="kai"
    assert {
        ids["alpha"],
        ids["beta"],
        ids["gamma"],
        ids["epsilon"],
    } <= found


async def test_AC38_3_filter_combines_authored_by_and_source_doc(
    tracker,
) -> None:
    """AND across set fields: only records meeting BOTH constraints."""
    ids = await _seed_mixed_population(tracker)
    out = tracker.query_projection_view(
        ObjectiveFilter(authored_by="user", lifted_from_source_doc=VP_DOC)
    )
    found = {p.objective_id for p in out}
    assert found == {ids["alpha"], ids["beta"]}


async def test_AC38_3_filter_no_match_returns_empty(tracker) -> None:
    await _seed_mixed_population(tracker)
    out = tracker.query_projection_view(
        ObjectiveFilter(lifted_from_source_doc="docs/nonexistent.md")
    )
    assert out == ()


async def test_AC38_3_deterministic_ordering(tracker) -> None:
    """Two calls on a stable DB return the same order."""
    await _seed_mixed_population(tracker)
    a = tracker.query_projection_view(ObjectiveFilter())
    b = tracker.query_projection_view(ObjectiveFilter())
    assert [p.objective_id for p in a] == [p.objective_id for p in b]


async def test_AC38_3_returns_tuple(tracker) -> None:
    """The API returns a tuple, not a list — preserves the public
    immutability convention `ObjectiveProjection` already uses."""
    await _seed_mixed_population(tracker)
    out = tracker.query_projection_view(ObjectiveFilter())
    assert isinstance(out, tuple)


def test_AC38_3_filter_rejects_unknown_keys() -> None:
    """`ObjectiveFilter` is `extra="forbid"` — unknown filter keys
    reject at construction. Future filter expressiveness lands as
    new declared fields, not as free-form kwargs."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ObjectiveFilter.model_validate({"rogue": "x"})


def test_AC38_3_filter_is_frozen() -> None:
    flt = ObjectiveFilter(authored_by="user")
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        flt.authored_by = "mara"  # type: ignore[misc]


def test_AC38_3_filter_is_empty_helper() -> None:
    assert ObjectiveFilter().is_empty() is True
    assert ObjectiveFilter(authored_by="user").is_empty() is False
    assert (
        ObjectiveFilter(lifted_from_source_doc="x").is_empty() is False
    )
