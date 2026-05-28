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

"""AC.KP5.5 — KP1's anchor can read the active-objective text from the
register (cross-AC binding; verified at the KP1 layer via
work_anchor)."""

from __future__ import annotations

from loam.primary_persona.keep_pace import objectives as obj
from loam.primary_persona.keep_pace.work_anchor import WorkAnchor


def test_AC_KP5_5_active_objective_texts_extracted() -> None:
    texts = obj.active_objective_texts(obj.SEEDED_OBJECTIVES)
    assert len(texts) == 2  # both seeded objectives are active
    joined = " ".join(texts).lower()
    assert "litrpg" in joined
    assert "passive" in joined or "independence" in joined


def test_AC_KP5_5_dormant_objectives_excluded() -> None:
    objs = [
        obj.Objective(
            slug="paused",
            status="dormant",
            objective="a dormant objective text",
            completion="c",
            detail_path="d",
        ),
        *obj.SEEDED_OBJECTIVES,
    ]
    texts = obj.active_objective_texts(objs)
    assert all("dormant objective text" not in t for t in texts)


def test_AC_KP5_5_anchor_consumes_objective_text() -> None:
    # The KP1 binding: the anchor's query tokens include the
    # active-objective terms read from the register.
    texts = obj.active_objective_texts(obj.SEEDED_OBJECTIVES)
    anchor = WorkAnchor(prompt="continue", objective_texts=texts)
    tokens = anchor.query_tokens()
    assert "litrpg" in tokens, (
        "the active-objective text must contribute its terms to the "
        "work-anchored key"
    )
