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

"""AC.VOL.5 — OUTCOME-ALTITUDE, end-to-end, no pre-arranged state.

The failure this guards is the real one from the field: a volatile
operational claim ("the shim is broken") written in one session is
served back as current in a LATER recall, while the durable decision it
sat next to is the thing that should survive.

Driven through the PRODUCTION entry-points only — ``write_episode`` to
capture, then ``FileMemoryStore.search`` (default current view) to
recall. No interval state is arranged by hand; the store builds its own
index. The query matches BOTH bodies, so the volatile fact's exclusion
is the volatility filter, never a BM25 miss.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore


SHARED = "quizzlefarn"


def _capture(store: FileMemoryStore, *, name: str, body: str, now: datetime) -> None:
    store.write_episode(
        name=f"turn/{name}",
        body=body,
        source_description="session capture",
        reference_time=now,
        source="message",
        group_id="pos3",
    )


def test_AC_VOL_5_volatile_not_recalled_durable_is(tmp_path: Path) -> None:
    store = FileMemoryStore(memory_dir=tmp_path / "episodes-store")
    now = datetime.now(timezone.utc)

    volatile_marker = "STALE-SHIM-STATUS"
    durable_marker = "RATIFIED-SHIM-DECISION"

    # This "session" captures a volatile operational status...
    _capture(
        store,
        name="status",
        body=(
            f"[user]\nis the {SHARED} deploy shim working\n\n[assistant]\n"
            f"the {SHARED} deploy shim is broken right now {volatile_marker}\n"
        ),
        now=now,
    )
    # ...and the durable decision that sits behind it.
    _capture(
        store,
        name="decision",
        body=(
            f"[user]\nwhat is our {SHARED} deploy shim strategy\n\n[assistant]\n"
            f"we decided the {SHARED} deploy shim is the standard path going "
            f"forward {durable_marker}\n"
        ),
        now=now,
    )

    # A LATER recall (the default current view a future session reads).
    result = store.search(
        query=f"{SHARED} deploy shim", group_ids=["pos3"], num_results=5
    )
    recalled = "\n".join(
        str(e.get("content", "")) for e in result.get("episodes", [])
    )

    assert durable_marker in recalled, (
        f"the durable decision behind the status MUST survive recall: {recalled!r}"
    )
    assert volatile_marker not in recalled, (
        f"the volatile status MUST NOT be served as current in a later recall: "
        f"{recalled!r}"
    )
