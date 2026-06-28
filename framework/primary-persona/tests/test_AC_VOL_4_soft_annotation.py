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

"""AC.VOL.4 — read-side soft annotation.

A SOFT-volatile episode survives recall (born open) but its surfaced
keep_pace pointer carries the ``[VOLATILE — re-verify before serving]``
prefix; a DURABLE episode's pointer does not. The substance is still
exposed (the summary text remains) — only the re-verify caution is added.
"""

from __future__ import annotations

from loam.primary_persona.file_memory import VOLATILE_SOFT_ANNOTATION
from loam.primary_persona.keep_pace.retrieval import _episode_pointer


def test_AC_VOL_4_soft_episode_pointer_is_annotated() -> None:
    soft_ep = {
        "content": (
            "[user]\nwhat is the corpus state\n\n[assistant]\n"
            "right now the corpus has the freshly punched lens text\n"
        ),
        "name": "turn/soft1",
    }
    pointer = _episode_pointer(soft_ep)
    assert pointer.startswith(f"From an earlier turn: {VOLATILE_SOFT_ANNOTATION}"), (
        f"a soft-volatile pointer must carry the re-verify annotation: {pointer!r}"
    )
    # Substance still exposed — the summary survives alongside the caution.
    assert "corpus" in pointer


def test_AC_VOL_4_durable_episode_pointer_is_not_annotated() -> None:
    durable_ep = {
        "content": (
            "[user]\nwhat is our llm policy\n\n[assistant]\n"
            "we decided every LLM call goes through claude -p\n"
        ),
        "name": "turn/durable1",
    }
    pointer = _episode_pointer(durable_ep)
    assert pointer.startswith("From an earlier turn:")
    assert VOLATILE_SOFT_ANNOTATION not in pointer, (
        f"a durable pointer must NOT be annotated: {pointer!r}"
    )
