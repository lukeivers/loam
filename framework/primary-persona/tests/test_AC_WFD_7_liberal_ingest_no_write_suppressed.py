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

"""AC.WFD.7 (liberal-ingest preservation) — no write is suppressed.

The set of records WRITTEN to disk for a given candidate is IDENTICAL with
the discipline active (lever on) vs off — paths + bodies modulo the added
``epistemic:`` frontmatter line. The discipline ADDS a tag; it never
rejects, drops, gates, or re-routes a write away from disk. The #1 F2
tension (provable-only vs LIBERAL ingest) is resolved structurally: LIBERAL
governs VOLUME, provable-only governs CONTENT-KIND.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona import file_memory as fm
from loam.primary_persona.file_memory import FileMemoryStore


# A candidate set spanning fact + non-fact + a pure-scaffolding (cold-tier)
# turn — every one must write to disk under BOTH lever states.
CANDIDATES = [
    ("fact", "we merged the PR and the CI run passed on 2026-07-08"),
    ("opinion", "honestly the whole design is gorgeous"),
    ("prediction", "the funding will probably come through next quarter"),
    ("plan", "the plan is to rework the ranker tonight"),
    # Pure-scaffolding user half => SALIENCE_JUNK => cold tier; still WRITTEN
    # (never dropped) — the liberal-ingest tier already in code.
    ("cold", "[user]\nok\n\n[assistant]\ngot it\n"),
]


def _write_all(store: FileMemoryStore, now: datetime) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for name, body in CANDIDATES:
        res = store.write_episode(
            name=f"turn/{name}",
            body=body,
            source_description="session capture",
            reference_time=now,
            source="message",
            group_id="pos3",
        )
        out[name] = Path(res["path"])
    return out


def _strip_epistemic(content: str) -> str:
    # Remove exactly the one added ``epistemic: <val>\n`` line, preserving
    # every other byte (including the trailing newline).
    return re.sub(r"epistemic: [^\n]*\n", "", content, count=1)


def test_AC_WFD_7_write_set_identical_lever_on_vs_off(
    tmp_path: Path, monkeypatch
) -> None:
    now = datetime.now(timezone.utc)

    # Lever ON.
    monkeypatch.setattr(fm, "EPISTEMIC_TYPING_ENABLED", True)
    on_dir = tmp_path / "on"
    on_paths = _write_all(FileMemoryStore(memory_dir=on_dir), now)

    # Lever OFF.
    monkeypatch.setattr(fm, "EPISTEMIC_TYPING_ENABLED", False)
    off_dir = tmp_path / "off"
    off_paths = _write_all(FileMemoryStore(memory_dir=off_dir), now)

    # Same candidate keys wrote in both regimes — none suppressed.
    assert set(on_paths) == set(off_paths) == {c[0] for c in CANDIDATES}

    for name in on_paths:
        on_p, off_p = on_paths[name], off_paths[name]
        # Same RELATIVE path (tier + dirs + stem) — no re-routing.
        assert on_p.relative_to(on_dir) == off_p.relative_to(off_dir), (
            f"{name}: the write was re-routed by the discipline"
        )
        on_content = on_p.read_text(encoding="utf-8")
        off_content = off_p.read_text(encoding="utf-8")
        # Lever-off carries NO epistemic tag; lever-on carries exactly one.
        assert "epistemic:" not in off_content
        assert on_content.count("epistemic:") == 1
        # Modulo the added tag line, the files are byte-identical (same
        # body, same every-other-field).
        assert _strip_epistemic(on_content) == off_content, (
            f"{name}: files differ beyond the added epistemic tag"
        )
