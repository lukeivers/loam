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

"""AC.WFD.8 (reversibility) — a named lever reverts to byte-identical
pre-stage writes + recall.

With ``EPISTEMIC_TYPING_ENABLED`` off: fact writes carry no ``epistemic:``
tag and the read side renders byte-identical to pre-stage; nothing on disk
is migrated or deleted; a tagless legacy record reads back fail-safe as a
fact. Flipping the lever on re-applies typing to NEW writes only and leaves
existing files untouched.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona import file_memory as fm
from loam.primary_persona.file_memory import (
    EPISTEMIC_NON_FACT_ANNOTATION,
    FileMemoryStore,
)
from loam.primary_persona.keep_pace.retrieval import _episode_pointer


def _write(store: FileMemoryStore, name: str, body: str, now: datetime) -> Path:
    res = store.write_episode(
        name=f"turn/{name}",
        body=body,
        source_description="session capture",
        reference_time=now,
        source="message",
        group_id="pos3",
    )
    return Path(res["path"])


def test_AC_WFD_8_lever_off_write_carries_no_tag(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(fm, "EPISTEMIC_TYPING_ENABLED", False)
    store = FileMemoryStore(memory_dir=tmp_path / "store")
    p = _write(store, "op", "the design is elegant", datetime.now(timezone.utc))
    assert "epistemic:" not in p.read_text(encoding="utf-8")


def test_AC_WFD_8_lever_off_recall_is_unmarked(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(fm, "EPISTEMIC_TYPING_ENABLED", False)
    # A bare-opinion body that, lever-ON, would be annotated. Lever-OFF the
    # read side renders it byte-identical to pre-stage: the stored tag is
    # IGNORED, so the pointer is identical to the same episode with no tag
    # at all (the pre-stage shape).
    content = "[user]\nthoughts on it\n\n[assistant]\nthe ranker design is elegant\n"
    tagged_ep = {"content": content, "name": "turn/op1", "epistemic": "non-fact"}
    untagged_ep = {"content": content, "name": "turn/op1"}
    pointer = _episode_pointer(tagged_ep)
    assert EPISTEMIC_NON_FACT_ANNOTATION not in pointer
    assert pointer == _episode_pointer(untagged_ep), (
        f"lever-off recall must ignore the tag (byte-identical to pre-stage): {pointer!r}"
    )


def test_AC_WFD_8_tagless_legacy_record_reads_as_fact(tmp_path: Path) -> None:
    # Lever ON (default). A hand-crafted legacy file with NO epistemic field
    # (as pre-stage records are) reads back as a fact — never annotated.
    legacy = tmp_path / "legacy.md"
    legacy.write_text(
        "---\n"
        "name: turn/legacy\n"
        "reference_time: 2026-01-01T00:00:00+00:00\n"
        "group_id: pos3\n"
        "---\n"
        "the design is elegant and gorgeous\n",
        encoding="utf-8",
    )
    ep = {
        "content": "the design is elegant and gorgeous",
        "name": "turn/legacy",
        "path": str(legacy),
    }
    pointer = _episode_pointer(ep)
    assert EPISTEMIC_NON_FACT_ANNOTATION not in pointer, (
        f"a tagless legacy record must read as a fact: {pointer!r}"
    )


def test_AC_WFD_8_flip_on_types_new_writes_only_and_leaves_old_untouched(
    tmp_path: Path, monkeypatch
) -> None:
    store = FileMemoryStore(memory_dir=tmp_path / "store")
    now = datetime.now(timezone.utc)

    # Write while OFF — no tag.
    monkeypatch.setattr(fm, "EPISTEMIC_TYPING_ENABLED", False)
    old = _write(store, "old", "the design is elegant", now)
    old_bytes = old.read_bytes()

    # Flip ON — a NEW write is typed; the OLD file is byte-for-byte untouched
    # (no migration).
    monkeypatch.setattr(fm, "EPISTEMIC_TYPING_ENABLED", True)
    new = _write(store, "new", "honestly this design is gorgeous", now)
    assert "epistemic: non-fact" in new.read_text(encoding="utf-8")
    assert old.read_bytes() == old_bytes, "the flip must not migrate an old record"
    assert "epistemic:" not in old.read_text(encoding="utf-8")
