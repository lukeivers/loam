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

"""AC.KP1.2 — the work-anchored retrieval key is composed of
prompt + active-objective text + active-subgoal + last-turn topic
(NOT the typed prompt alone). All four contribute when present; the
query degrades gracefully when a component is absent."""

from __future__ import annotations

from loam.primary_persona.keep_pace.work_anchor import WorkAnchor


def test_AC_KP1_2_all_four_components_contribute() -> None:
    anchor = WorkAnchor(
        prompt="continue the batch",
        objective_texts=["produce the LitRPG series Patch Notes for Reality"],
        subgoals=["canon-consistency-across-the-series"],
        last_topic="chapter five drafting",
    )
    present = anchor.components_present()
    assert present == {
        "prompt": True,
        "objective": True,
        "subgoal": True,
        "last_topic": True,
    }
    tokens = anchor.query_tokens()
    # A token from each component is present in the merged key.
    assert "batch" in tokens  # prompt
    assert "litrpg" in tokens  # objective
    assert "canon" in tokens  # subgoal (hyphen-split)
    assert "chapter" in tokens  # last_topic


def test_AC_KP1_2_not_prompt_alone() -> None:
    # The work-anchored key must carry MORE than the bare prompt tokens
    # when objective/subgoal/last-topic are present — this is the
    # correction that fixes tonight's failure.
    bare = WorkAnchor(prompt="continue")
    anchored = WorkAnchor(
        prompt="continue",
        objective_texts=["LitRPG production pipeline canon"],
    )
    assert set(anchored.query_tokens()) > set(bare.query_tokens())


def test_AC_KP1_2_degrades_gracefully_missing_components() -> None:
    # Absent last_topic (first turn) + absent subgoals: the key still
    # functions from prompt + objective.
    anchor = WorkAnchor(
        prompt="keep going",
        objective_texts=["revenue independence passive assets"],
        subgoals=[],
        last_topic="",
    )
    present = anchor.components_present()
    assert present["objective"] is True
    assert present["subgoal"] is False
    assert present["last_topic"] is False
    tokens = anchor.query_tokens()
    assert tokens  # still a usable query
    assert "revenue" in tokens


def test_AC_KP1_2_empty_when_all_absent() -> None:
    # A fully-empty anchor (a prompt that tokenizes to nothing —
    # stopwords/punctuation only — with no objective/subgoal/last-topic)
    # produces no tokens; the caller then injects nothing.
    anchor = WorkAnchor(
        prompt="the is of ...", objective_texts=[], subgoals=[], last_topic=""
    )
    assert anchor.query_tokens() == []
