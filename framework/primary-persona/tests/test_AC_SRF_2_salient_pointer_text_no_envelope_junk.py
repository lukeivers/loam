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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.SRF.2 — surfaced pointer text is substantive: derived from salient
content, never a channel envelope, task-notification header, or
structural-metadata prefix — on both render surfaces.

Memory recall cycle, Slice 2.
"""

from __future__ import annotations

import pytest

from loam.primary_persona.keep_pace.retrieval import _episode_pointer
from loam.primary_persona.memory_consumer import (
    _render_retrieval,
    salient_snippet,
)

# A realistic recorded-turn body whose first lines are pure transport
# envelope — the junk shape the pre-cycle render surfaced verbatim.
_ENVELOPED_TURN = """[user]
<task-notification agent="abc123" status="completed">
<channel source="telegram" chat_id="642727620">
The Tilth raise was ruled at seven hundred fifty thousand dollars.
[persona]
Acknowledged and recorded.
"""


@pytest.mark.parametrize(
    "body,expected_substance",
    [
        (_ENVELOPED_TURN, "Tilth raise was ruled"),
        (
            "<channel source='discord'>Ship the budget fix tomorrow.",
            "Ship the budget fix tomorrow.",
        ),
        ("---\nname: turn/x\n---\nReal substance line.", "Real substance"),
    ],
)
def test_AC_SRF_2_salient_snippet_skips_envelope_junk(
    body: str, expected_substance: str
) -> None:
    snippet = salient_snippet(body)
    assert expected_substance in snippet
    assert not snippet.startswith("<")
    assert not snippet.startswith("[user]")
    assert not snippet.startswith("---")


def test_AC_SRF_2_salient_snippet_empty_when_nothing_substantive() -> None:
    assert salient_snippet("[user]\n<channel source='x'>\n   \n") == ""
    assert salient_snippet("") == ""


def test_AC_SRF_2_dispatch_render_preview_is_substance_not_envelope() -> None:
    out = _render_retrieval(
        {
            "query": "tilth",
            "results": [],
            "episodes": [
                {
                    "episode_uuid": "ep-1",
                    "name": "enveloped-ep",
                    "content": _ENVELOPED_TURN,
                    "group_id": "g",
                    "valid_at": None,
                    "path": "/m/e.md",
                },
            ],
        },
        cap=5000,
    )
    line = next(ln for ln in out.splitlines() if ln.startswith("- [episode]"))
    assert "Tilth raise was ruled" in line, (
        f"AC.SRF.2: preview must be the substantive line: {line!r}"
    )
    assert "<task-notification" not in out
    assert "<channel" not in out


def test_AC_SRF_2_keep_pace_episode_pointer_is_substance_not_envelope() -> None:
    pointer = _episode_pointer(
        {"name": "turn/abc", "content": _ENVELOPED_TURN}
    )
    assert "Tilth raise was ruled" in pointer, (
        f"AC.SRF.2: keep-pace pointer must surface the substance: "
        f"{pointer!r}"
    )
    assert "<task-notification" not in pointer
    assert "<channel" not in pointer
    assert "[user]" not in pointer


def test_AC_SRF_2_keep_pace_pointer_empty_on_pure_junk_body() -> None:
    # A body that is ALL envelope degrades to no pointer (the hit is
    # dropped) rather than surfacing junk — and the opaque turn/<id>
    # name never leaks as a fallback.
    pointer = _episode_pointer(
        {"name": "turn/abc", "content": "<channel source='telegram'>\n[user]\n"}
    )
    assert pointer == ""
