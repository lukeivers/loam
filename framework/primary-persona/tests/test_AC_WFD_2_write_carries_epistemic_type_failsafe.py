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

"""AC.WFD.2 — every store-(b) write carries a deterministic epistemic type,
fail-safe to fact.

A record written to store (b) carries a machine-readable ``epistemic:``
frontmatter field assigned at write time with no LLM/API call. A clear
event/state/finding body is typed fact; a clear opinion body is typed
non-fact; an ambiguous body AND any classifier error yield fact (the
never-suppress direction).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from loam.primary_persona import file_memory as fm
from loam.primary_persona.file_memory import (
    EPISTEMIC_FACT,
    EPISTEMIC_NON_FACT,
    FileMemoryStore,
)


def _write(store: FileMemoryStore, *, name: str, body: str) -> Path:
    res = store.write_episode(
        name=f"turn/{name}",
        body=body,
        source_description="session capture",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    return Path(res["path"])


def _epistemic_field(path: Path) -> str:
    front, _ = fm._split_frontmatter(path.read_text(encoding="utf-8"))
    return str(front.get("epistemic", ""))


def test_AC_WFD_2_clear_fact_typed_fact(tmp_path: Path) -> None:
    store = FileMemoryStore(memory_dir=tmp_path / "store")
    p = _write(
        store,
        name="fact",
        body="we merged the PR and the CI run passed on 2026-07-08",
    )
    assert _epistemic_field(p) == EPISTEMIC_FACT


def test_AC_WFD_2_clear_opinion_typed_non_fact(tmp_path: Path) -> None:
    store = FileMemoryStore(memory_dir=tmp_path / "store")
    p = _write(store, name="op", body="honestly this whole design is gorgeous")
    assert _epistemic_field(p) == EPISTEMIC_NON_FACT


def test_AC_WFD_2_ambiguous_body_resolves_fact(tmp_path: Path) -> None:
    store = FileMemoryStore(memory_dir=tmp_path / "store")
    p = _write(store, name="amb", body="the classifier handles the edge case")
    # Ambiguity (no affirmative non-fact tell) => fact, the never-suppress
    # direction.
    assert _epistemic_field(p) == EPISTEMIC_FACT


def test_AC_WFD_2_classifier_error_resolves_fact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = FileMemoryStore(memory_dir=tmp_path / "store")

    # Force the classifier's internals to raise; the write must still
    # complete and the record must be typed fact (fail-safe / never break
    # the turn).
    def _boom(_text: str) -> bool:  # noqa: ANN001
        raise RuntimeError("classifier fault")

    monkeypatch.setattr(fm, "_has_durable_fact_signal", _boom)
    p = _write(store, name="err", body="the design is elegant")
    assert _epistemic_field(p) == EPISTEMIC_FACT
    assert p.exists(), "the write must complete even when the classifier faults"
