"""D5 — authored_by provenance.

Acceptance (brief §D5):
- Every objective carries authored_by.
- Field accepts either "user" or any persona-handle string.
- list(authored_by=...) queries return exactly the set of objectives
  matching.
- Orphan-root check (D2) reads this field.
"""

from __future__ import annotations

import pytest

from loam.objective_tracker.errors import OrphanRootError
from tests.conftest import make_child_spec, make_user_root_spec


async def test_user_authored_objective(tracker):
    proj = await tracker.create(make_user_root_spec(goal="luke"))
    assert proj.authored_by == "user"


async def test_persona_authored_objective(tracker):
    root = await tracker.create(make_user_root_spec())
    proj = await tracker.create(
        make_child_spec(parent_id=root.objective_id, authored_by="mara")
    )
    assert proj.authored_by == "mara"


async def test_list_by_authored_by_user(tracker):
    r1 = await tracker.create(make_user_root_spec(goal="u1"))
    r2 = await tracker.create(make_user_root_spec(goal="u2"))
    # A persona-authored sub.
    await tracker.create(
        make_child_spec(parent_id=r1.objective_id, authored_by="mara")
    )
    user_objs = tracker.list(authored_by="user")
    assert {p.objective_id for p in user_objs} == {r1.objective_id, r2.objective_id}


async def test_list_by_persona_handle(tracker):
    root = await tracker.create(make_user_root_spec())
    m1 = await tracker.create(
        make_child_spec(parent_id=root.objective_id, goal="m1", authored_by="mara")
    )
    m2 = await tracker.create(
        make_child_spec(parent_id=root.objective_id, goal="m2", authored_by="mara")
    )
    await tracker.create(
        make_child_spec(parent_id=root.objective_id, goal="k", authored_by="kai")
    )
    mara_objs = tracker.list(authored_by="mara")
    assert {p.objective_id for p in mara_objs} == {m1.objective_id, m2.objective_id}


async def test_authored_by_is_arbitrary_string_no_registry_validation(tracker):
    """Tracker does NOT cross-check handles against any persona registry.

    A deliberately unusual "authored_by" value is accepted.
    """
    root = await tracker.create(make_user_root_spec())
    sub = await tracker.create(
        make_child_spec(
            parent_id=root.objective_id, authored_by="some-new-agent-42"
        )
    )
    assert sub.authored_by == "some-new-agent-42"


async def test_orphan_root_check_reads_authored_by(tracker):
    """Per D5 acceptance: the orphan-root check reads this field, not
    an is_user-shaped flag.
    """
    # Root authored "mara" — not user.
    spec = make_user_root_spec().model_copy(update={"authored_by": "mara"})
    root = await tracker.create(spec)
    # Bind attempt should fail.
    with pytest.raises(OrphanRootError):
        await tracker.bind_scope("scope-x", root.objective_id)


async def test_list_by_authored_by_empty_returns_empty(tracker):
    await tracker.create(make_user_root_spec())
    result = tracker.list(authored_by="nobody")
    assert result == []
