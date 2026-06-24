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

"""AC.SUP.3 — the write that creates A' closes A's validity interval
AT CREATION, durably + machine-readably, without deleting A's content.

The production marking entry point (:func:`supersession.mark_superseded`)
writes ``superseded-by`` + ``superseded-date`` — the marker IS the
interval close. The validity-interval reader
(:func:`file_memory._supersession_interval`) then reads A's interval as
``[A.valid_from, A.valid_to)`` with ``A.valid_to`` == the close instant.
Content beyond the marker lines is preserved byte-for-byte (the AC.SUP.3
annotate-not-delete precedent).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import _supersession_interval
from loam.primary_persona.supersession import mark_superseded, read_supersession


def _write_a(path: Path) -> str:
    original = (
        "---\n"
        "name: turn/decision-a\n"
        "reference_time: 2026-05-01T00:00:00+00:00\n"
        "group_id: g\n"
        "---\n"
        "The original ruling body. Line one.\nLine two.\nLine three.\n"
    )
    path.write_text(original, encoding="utf-8")
    return original


def test_AC_SUP_3_close_at_creation_sets_valid_to(tmp_path: Path):
    a = tmp_path / "decision-a.md"
    _write_a(a)
    # Before A' is created, A's interval is OPEN (valid_to is None).
    vf, vt = _supersession_interval(str(a))
    assert vf == datetime(2026, 5, 1, tzinfo=timezone.utc)
    assert vt is None, "A's interval must be open before A' closes it"

    # Creating A' closes A's interval at the close instant (AT CREATION).
    close = "2026-06-01T00:00:00+00:00"
    mark_superseded(a, "./decision-a-prime.md", date=close)

    vf2, vt2 = _supersession_interval(str(a))
    assert vf2 == datetime(2026, 5, 1, tzinfo=timezone.utc)
    assert vt2 == datetime(2026, 6, 1, tzinfo=timezone.utc), (
        "A.valid_to must be set to the close instant at A' creation"
    )


def test_AC_SUP_3_machine_readable_round_trip(tmp_path: Path):
    a = tmp_path / "decision-a.md"
    _write_a(a)
    mark_superseded(a, "./decision-a-prime.md", date="2026-06-01")
    mark = read_supersession(a)
    assert mark is not None
    assert mark["superseded-by"] == "./decision-a-prime.md"
    assert mark["superseded-date"] == "2026-06-01"


def test_AC_SUP_3_content_preserved_byte_for_byte(tmp_path: Path):
    a = tmp_path / "decision-a.md"
    original = _write_a(a)
    body_original = original.split("---\n", 2)[2]
    mark_superseded(a, "./decision-a-prime.md", date="2026-06-01")
    after = a.read_text(encoding="utf-8")
    body_after = after.split("---\n", 2)[2]
    assert body_after == body_original, (
        "the document body beyond the marker must be preserved "
        "byte-for-byte (annotate-not-delete)"
    )
