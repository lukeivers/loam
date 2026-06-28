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

"""AC.VOL.2 — write-side interval birth.

A HARD-volatile turn written through the production ``write_episode``
carries a ``volatile_until`` close (= reference_time + VOLATILE_WINDOW)
and a ``volatility`` class field; a DURABLE turn carries no close (born
open). Verified through the SAME interval reader the read side uses
(``_supersession_interval``) — not by parsing frontmatter by hand.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    VOLATILE_WINDOW,
    FileMemoryStore,
    _supersession_interval,
)


def _write(store: FileMemoryStore, *, name: str, body: str, now: datetime) -> str:
    res = store.write_episode(
        name=f"turn/{name}",
        body=body,
        source_description="test seed",
        reference_time=now,
        source="message",
        group_id="pos3",
    )
    return str(res["path"])


def test_AC_VOL_2_hard_born_closed_durable_born_open(tmp_path: Path) -> None:
    store = FileMemoryStore(memory_dir=tmp_path / "episodes-store")
    now = datetime.now(timezone.utc)

    hard_path = _write(
        store,
        name="hard",
        body="[user]\nis the deploy shim ok\n\n[assistant]\nthe deploy shim is broken right now\n",
        now=now,
    )
    durable_path = _write(
        store,
        name="durable",
        body="[user]\nwhat is our llm policy\n\n[assistant]\nwe decided every call goes through claude -p\n",
        now=now,
    )

    hard_from, hard_to = _supersession_interval(hard_path)
    durable_from, durable_to = _supersession_interval(durable_path)

    # HARD — closed interval, close exactly one window past valid_from.
    assert hard_to is not None, "HARD-volatile must be born with a closed interval"
    assert hard_from is not None
    assert hard_to == hard_from + VOLATILE_WINDOW

    # The frontmatter carries the class + close keys (transparency).
    hard_text = Path(hard_path).read_text(encoding="utf-8")
    assert "volatility: volatile-hard" in hard_text
    assert "volatile_until:" in hard_text

    # DURABLE — open interval (no close); class field present, no close key.
    assert durable_to is None, "DURABLE must be born open (no interval close)"
    durable_text = Path(durable_path).read_text(encoding="utf-8")
    assert "volatility: durable" in durable_text
    assert "volatile_until:" not in durable_text
