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

"""AC.TFN.2 — manifest insert produces a fixed-width microsecond
``Z``-suffixed timestamp (format γ).

Per the locked plan-doc
``docs/plans/a1-substrate-timestamp-format-normalization.md``
§4 AC.TFN.2: every newly-inserted ``objective_manifest`` row carries
a ``created_at`` byte-conforming to
``^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{6}Z$``.
Pre-amendment-#75 the emitter used
``datetime.now(tz=timezone.utc).isoformat()`` (microsecond
``+00:00`` suffix); the format change aligns the manifest with the
sentinel side so A3's lex-compare is structurally correct.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from loam.objective_tracker.runtime import ObjectiveTracker


_FORMAT_GAMMA_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"
)


@pytest.fixture
def store(tmp_path: Path) -> ObjectiveTracker:
    db = tmp_path / "tfn2.db"
    rt = ObjectiveTracker(db_path=db)
    yield rt
    rt.close()


def test_AC_TFN_2_inserted_row_created_at_matches_format_gamma(
    store: ObjectiveTracker,
) -> None:
    """A registered binding row carries a γ-format ``created_at``."""
    store.register_source_binding(
        component="primary-persona",
        ac_id="AC.TFN.X",
        source_path_glob="framework/primary-persona/src/x.py",
    )
    rows = store.manifest_rows_for_component("primary-persona")
    assert len(rows) == 1
    created_at = rows[0]["created_at"]
    assert _FORMAT_GAMMA_RE.match(created_at), (
        f"manifest created_at does not conform to format γ: {created_at!r}"
    )
    assert len(created_at) == 27


def test_AC_TFN_2_local_helper_emits_format_gamma() -> None:
    """The store-local ``_now_iso_microsecond_z`` helper emits format γ
    directly (covers the source-of-truth side)."""
    from loam.objective_tracker.store import _now_iso_microsecond_z

    ts = _now_iso_microsecond_z()
    assert _FORMAT_GAMMA_RE.match(ts), (
        f"_now_iso_microsecond_z does not conform to format γ: {ts!r}"
    )
    assert len(ts) == 27
