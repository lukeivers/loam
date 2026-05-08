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

"""AC.SE.7 — objective-manifest table refuses malformed rows
structurally.

Per the locked plan-doc
``docs/plans/structural-enforcement-a1-substrate.md`` §4
AC.SE.7: insertion of a row with empty ``component``, empty
``ac_id``, or empty ``source_path_glob`` is refused at the API
boundary with a structured error. Insertion of a row whose
``source_path_glob`` is not a valid fnmatch pattern is refused
(validation at write time, not at query time). The refusal is
observable to the caller without leaking a SQLite exception.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.objective_tracker.errors import ManifestRowError
from loam.objective_tracker.runtime import ObjectiveTracker


@pytest.fixture
def store(tmp_path: Path) -> ObjectiveTracker:
    db = tmp_path / "refusal_test.db"
    rt = ObjectiveTracker(db_path=db)
    yield rt
    rt.close()


def test_AC_SE_7_refuses_empty_component(store: ObjectiveTracker) -> None:
    with pytest.raises(ManifestRowError) as info:
        store.register_source_binding(
            component="",
            ac_id="A1",
            source_path_glob="safety-layer/src/a.py",
        )
    assert info.value.field == "component"


def test_AC_SE_7_refuses_empty_ac_id(store: ObjectiveTracker) -> None:
    with pytest.raises(ManifestRowError) as info:
        store.register_source_binding(
            component="safety-layer",
            ac_id="",
            source_path_glob="safety-layer/src/a.py",
        )
    assert info.value.field == "ac_id"


def test_AC_SE_7_refuses_empty_source_path_glob(
    store: ObjectiveTracker,
) -> None:
    with pytest.raises(ManifestRowError) as info:
        store.register_source_binding(
            component="safety-layer",
            ac_id="A1",
            source_path_glob="",
        )
    assert info.value.field == "source_path_glob"


def test_AC_SE_7_refuses_invalid_fnmatch_pattern(
    store: ObjectiveTracker,
) -> None:
    """A pattern with an unbalanced bracket is not a valid fnmatch
    pattern; the API refuses at write time, not at query time."""
    with pytest.raises(ManifestRowError) as info:
        store.register_source_binding(
            component="safety-layer",
            ac_id="A1",
            source_path_glob="safety-layer/src/[abc.py",
        )
    assert info.value.field == "source_path_glob"
    assert "fnmatch" in info.value.reason.lower() or (
        "bracket" in info.value.reason.lower()
    )


def test_AC_SE_7_refusal_does_not_partially_insert(
    store: ObjectiveTracker,
) -> None:
    """A refused write must not leave a partial row in the table."""
    with pytest.raises(ManifestRowError):
        store.register_source_binding(
            component="safety-layer",
            ac_id="",
            source_path_glob="safety-layer/src/a.py",
        )
    # Nothing should be persisted.
    rows = store.manifest_rows_for_component("safety-layer")
    assert rows == []


def test_AC_SE_7_refusal_is_typed_not_sqlite_exception(
    store: ObjectiveTracker,
) -> None:
    """The caller catches ``ManifestRowError`` (or its parent
    ``ObjectiveTrackerError``); a raw SQLite IntegrityError must not
    leak through."""
    import sqlite3 as _sqlite3

    try:
        store.register_source_binding(
            component="safety-layer", ac_id="", source_path_glob="x",
        )
    except _sqlite3.IntegrityError:
        pytest.fail("raw sqlite3.IntegrityError leaked through API")
    except ManifestRowError:
        pass
    else:
        pytest.fail("expected ManifestRowError")
