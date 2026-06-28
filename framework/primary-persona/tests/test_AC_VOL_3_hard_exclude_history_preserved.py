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

"""AC.VOL.3 — read-side hard-exclude, history preserved.

Reusing the sealed ``_filter_by_interval`` (no new filter): under the
DEFAULT current view (``as_of=None``) a HARD-volatile record is filtered
out, while a DURABLE record matching the same query survives. Under an
``as_of`` query inside ``[valid_from, volatile_until)`` the HARD record
is reachable again — filtering is NOT deletion (the AC.SUP.2 property
holds for the volatility close too).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore


SHARED = "quizzlefarn"  # high-IDF anchor both episodes carry + the query.


def _write(store: FileMemoryStore, *, name: str, body: str, now: datetime) -> None:
    store.write_episode(
        name=f"turn/{name}",
        body=body,
        source_description="test seed",
        reference_time=now,
        source="message",
        group_id="pos3",
    )


def _contents(result: dict) -> str:
    return "\n".join(str(e.get("content", "")) for e in result.get("episodes", []))


def test_AC_VOL_3_default_view_excludes_hard_asof_reaches_it(tmp_path: Path) -> None:
    store = FileMemoryStore(memory_dir=tmp_path / "episodes-store")
    now = datetime.now(timezone.utc)

    hard_marker = "HARD-OPERATIONAL-STATUS-MARKER"
    durable_marker = "DURABLE-DECISION-MARKER"

    _write(
        store,
        name="hard",
        body=(
            f"[user]\nis the {SHARED} shim ok\n\n[assistant]\n"
            f"the {SHARED} shim is broken right now {hard_marker}\n"
        ),
        now=now,
    )
    _write(
        store,
        name="durable",
        body=(
            f"[user]\nwhat is our {SHARED} shim approach\n\n[assistant]\n"
            f"we decided the {SHARED} shim path is our standard going forward "
            f"{durable_marker}\n"
        ),
        now=now,
    )

    # DEFAULT current view — HARD filtered, DURABLE survives.
    current = store.search(query=f"{SHARED} shim", group_ids=["pos3"], num_results=5)
    current_text = _contents(current)
    assert durable_marker in current_text, (
        f"the durable decision must survive the current view: {current_text!r}"
    )
    assert hard_marker not in current_text, (
        f"the hard-volatile status must be hard-excluded: {current_text!r}"
    )

    # AS_OF inside the window — the HARD record is reachable (history kept).
    as_of = now + timedelta(minutes=1)
    history = store.search(
        query=f"{SHARED} shim", group_ids=["pos3"], num_results=5, as_of=as_of
    )
    history_text = _contents(history)
    assert hard_marker in history_text, (
        f"an as_of-in-window query must still reach the hard record "
        f"(filtering != deletion): {history_text!r}"
    )
