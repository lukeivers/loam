"""AC.SE.6 — objective-manifest table accepts well-formed rows.

Per the locked plan-doc
``docs/rebuild/plans/structural-enforcement-a1-substrate.md`` §4
AC.SE.6: a new table inside the existing ``objective-tracker``
SQLite store accepts rows of shape ``(component, ac_id,
source_path_glob)`` with appropriate uniqueness on the row tuple.
The public API exposes insert + the three documented query shapes.
Schema is forward-compatible (additive widening allowed in future
amendments).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.runtime import ObjectiveTracker


@pytest.fixture
def store(tmp_path: Path) -> ObjectiveTracker:
    db = tmp_path / "manifest_test.db"
    rt = ObjectiveTracker(db_path=db)
    yield rt
    rt.close()


def test_AC_SE_6_register_one_row_then_list_for_component(
    store: ObjectiveTracker,
) -> None:
    """Insert a single well-formed row; reading by component returns
    exactly that row."""
    store.register_source_binding(
        component="safety-layer",
        ac_id="A1",
        source_path_glob="safety-layer/src/kill_switch.py",
    )

    rows = store.manifest_rows_for_component("safety-layer")
    assert len(rows) == 1
    row = rows[0]
    assert row["component"] == "safety-layer"
    assert row["ac_id"] == "A1"
    assert row["source_path_glob"] == "safety-layer/src/kill_switch.py"
    assert "created_at" in row and row["created_at"]


def test_AC_SE_6_list_for_component_returns_only_matching(
    store: ObjectiveTracker,
) -> None:
    """A component's row list excludes rows from other components."""
    store.register_source_binding(
        component="safety-layer", ac_id="A1",
        source_path_glob="safety-layer/src/a.py",
    )
    store.register_source_binding(
        component="cost-governance", ac_id="C1",
        source_path_glob="cost-governance/src/b.py",
    )

    rows = store.manifest_rows_for_component("safety-layer")
    assert len(rows) == 1
    assert rows[0]["component"] == "safety-layer"


def test_AC_SE_6_list_for_ac_returns_all_globs_for_that_ac(
    store: ObjectiveTracker,
) -> None:
    """An AC may map to multiple source-path globs (one AC, multiple
    files)."""
    store.register_source_binding(
        component="safety-layer", ac_id="A20",
        source_path_glob="safety-layer/src/safety_v_degradation.py",
    )
    store.register_source_binding(
        component="safety-layer", ac_id="A20",
        source_path_glob="safety-layer/tests/test_safety_beats_degradation.py",
    )
    store.register_source_binding(
        component="safety-layer", ac_id="A1",
        source_path_glob="safety-layer/src/kill_switch.py",
    )

    rows = store.manifest_rows_for_ac("safety-layer", "A20")
    assert len(rows) == 2
    assert all(r["ac_id"] == "A20" for r in rows)
    globs = {r["source_path_glob"] for r in rows}
    assert globs == {
        "safety-layer/src/safety_v_degradation.py",
        "safety-layer/tests/test_safety_beats_degradation.py",
    }


def test_AC_SE_6_list_matching_source_path_uses_glob(
    store: ObjectiveTracker,
) -> None:
    """The path-matching query uses fnmatch over the glob column."""
    store.register_source_binding(
        component="safety-layer", ac_id="A1",
        source_path_glob="safety-layer/src/*.py",
    )
    store.register_source_binding(
        component="cost-governance", ac_id="C14",
        source_path_glob="cost-governance/src/throttle.py",
    )

    rows = store.manifest_rows_matching_source_path(
        "safety-layer/src/kill_switch.py"
    )
    assert len(rows) == 1
    assert rows[0]["component"] == "safety-layer"
    assert rows[0]["ac_id"] == "A1"


def test_AC_SE_6_list_matching_source_path_no_match_returns_empty(
    store: ObjectiveTracker,
) -> None:
    """A path that no glob matches returns the empty list, not an error."""
    store.register_source_binding(
        component="safety-layer", ac_id="A1",
        source_path_glob="safety-layer/src/a.py",
    )
    rows = store.manifest_rows_matching_source_path(
        "cost-governance/src/elsewhere.py"
    )
    assert rows == []


def test_AC_SE_6_register_idempotent_on_duplicate(
    store: ObjectiveTracker,
) -> None:
    """Re-inserting an identical (component, ac_id, source_path_glob)
    row is a no-op (PRIMARY KEY conflict resolved as INSERT OR IGNORE).
    The row count stays at 1 after a second register call."""
    store.register_source_binding(
        component="safety-layer", ac_id="A1",
        source_path_glob="safety-layer/src/a.py",
    )
    store.register_source_binding(
        component="safety-layer", ac_id="A1",
        source_path_glob="safety-layer/src/a.py",
    )
    rows = store.manifest_rows_for_component("safety-layer")
    assert len(rows) == 1


def test_AC_SE_6_schema_forward_compat_additive_column(
    tmp_path: Path,
) -> None:
    """Adding a hypothetical optional column to ``objective_manifest``
    in a future amendment must not require rewriting existing rows.

    Asserted structurally: SQLite's ``ALTER TABLE ... ADD COLUMN``
    semantics on the existing table accept a new optional column with
    a default; existing rows fill the default. This is the same
    mechanism amendment #38 used for ``lifted_from_json`` and the
    plan-doc names it as the forward-compat shape.
    """
    db = tmp_path / "fwd.db"
    rt = ObjectiveTracker(db_path=db)
    try:
        rt.register_source_binding(
            component="safety-layer", ac_id="A1",
            source_path_glob="safety-layer/src/a.py",
        )

        # Reach into the underlying connection (test-only) to add a
        # hypothetical future column with a default value.
        rt.store._conn.execute(
            "ALTER TABLE objective_manifest "
            "ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal'"
        )
        cur = rt.store._conn.execute(
            "SELECT priority FROM objective_manifest "
            "WHERE component='safety-layer' AND ac_id='A1'"
        )
        row = cur.fetchone()
        assert row is not None
        assert row["priority"] == "normal"
    finally:
        rt.close()
