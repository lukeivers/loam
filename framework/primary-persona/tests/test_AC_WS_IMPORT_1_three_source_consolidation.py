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

"""AC.WS.IMPORT.1 — after the consolidation pass the register indexes the
backlog from all three sources (FIDRAFT graduated items, persona task
list, dev-queue ws-* items) grouped by stream; the dev-queue items
resolve UNDER the loam stream and the register header documents the
ws-*-vs-cross-cutting-stream distinction (the naming collision,
resolved-not-silent)."""

from __future__ import annotations

from loam.primary_persona.keep_pace import work_streams as ws


def test_AC_WS_IMPORT_1_three_sources_indexed() -> None:
    text = ws.render_register(ws.SEEDED_WORK_STREAMS)
    # All three backlog sources are named in the register (the header note
    # plus per-stream backlog entries).
    assert "FIDRAFT" in text or "fidraft" in text
    assert "task list" in text or "task-list" in text
    assert "workstream-queue.yaml" in text or "dev-queue" in text


def test_AC_WS_IMPORT_1_backlog_grouped_by_stream() -> None:
    by_slug = {s.slug: s for s in ws.SEEDED_WORK_STREAMS}
    # Each real stream carries a backlog index (grouped by stream).
    assert by_slug["loam"].backlog
    assert by_slug["litrpg"].backlog
    assert by_slug["money"].backlog


def test_AC_WS_IMPORT_1_dev_queue_under_loam() -> None:
    by_slug = {s.slug: s for s in ws.SEEDED_WORK_STREAMS}
    loam_backlog = " ".join(by_slug["loam"].backlog).lower()
    assert "dev-queue items" in loam_backlog, (
        "the dev-queue ws-* items must map UNDER the loam stream as "
        "'dev-queue items'"
    )
    assert "workstream-queue.yaml" in loam_backlog


def test_AC_WS_IMPORT_1_ws_star_collision_documented() -> None:
    text = ws.render_register(ws.SEEDED_WORK_STREAMS)
    # The ws-* naming collision is documented resolved-not-silent: the
    # header names the distinction between the dev BUILD queue and a
    # cross-cutting attention stream, and states no file rename.
    assert "ws-*" in text
    assert "no file rename" in text.lower() or "no file move" in text.lower()
    assert "cross-cutting" in text.lower()
