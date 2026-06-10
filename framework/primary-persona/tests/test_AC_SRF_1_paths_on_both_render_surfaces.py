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

"""AC.SRF.1 — model-facing memory injection includes the source path for
every memory pointer it surfaces, on BOTH injection surfaces (the
per-turn keep-pace block and the dispatch-bundle memory tier); the
user-facing prose lint keeps its correct scope (pointer TEXT stays
plain language — paths ride as a structured suffix).

Memory recall cycle, Slice 2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    retrieve,
)
from loam.primary_persona.memory_consumer import _render_retrieval

from _helpers_keep_pace import write_corpus


def _config(tmp_path: Path) -> RetrievalConfig:
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "empty-home",
    )


def test_AC_SRF_1_keep_pace_corpus_pointer_carries_source_path(
    tmp_path: Path,
) -> None:
    cfg = _config(tmp_path)
    block = retrieve(prompt="git safety protocol secrets", config=cfg)
    bullets = [ln for ln in block.splitlines() if ln.strip().startswith("- ")]
    assert bullets, "expected corpus pointer lines"
    for ln in bullets:
        assert "[source: " in ln and ".md" in ln, (
            f"AC.SRF.1: keep-pace pointer line must carry its source "
            f"path: {ln!r}"
        )


def test_AC_SRF_1_keep_pace_episode_pointer_carries_source_path(
    tmp_path: Path,
) -> None:
    # Episode store with one substantive episode matching the prompt.
    ep_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=ep_dir)
    written = store.write_episode(
        name="turn/srf1-episode",
        body=(
            "Decided the quasar telemetry budget question: the answer "
            "is fourteen probes per array."
        ),
        source_description="test turn",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="ws",
    )
    cfg = _config(tmp_path)
    cfg.episode_memory_dir = ep_dir
    block = retrieve(prompt="quasar telemetry probes budget", config=cfg)
    ep_lines = [
        ln
        for ln in block.splitlines()
        if "quasar" in ln.lower() or "fourteen" in ln.lower()
    ]
    assert ep_lines, f"expected the episode hit to surface, got: {block!r}"
    for ln in ep_lines:
        assert f"[source: {written['path']}]" in ln, (
            f"AC.SRF.1: episode pointer must carry its episode-file "
            f"path: {ln!r}"
        )


def test_AC_SRF_1_dispatch_render_episode_line_carries_path() -> None:
    out = _render_retrieval(
        {
            "query": "x",
            "results": [],
            "episodes": [
                {
                    "episode_uuid": "ep-1",
                    "name": "ep-with-path",
                    "content": "A substantive decision about the widget.",
                    "group_id": "g",
                    "valid_at": None,
                    "path": "/ws/.loam/memory/episodes/g/2026-06-09/t1.md",
                },
            ],
        },
        cap=5000,
    )
    line = next(ln for ln in out.splitlines() if ln.startswith("- [episode]"))
    assert "(/ws/.loam/memory/episodes/g/2026-06-09/t1.md)" in line, (
        f"AC.SRF.1: dispatch-tier episode line must carry the source "
        f"path: {line!r}"
    )


def test_AC_SRF_1_dispatch_render_pathless_row_still_renders() -> None:
    # A row with no path renders without a path part (never a fake path,
    # never dropped for missing metadata — fail-soft shape).
    out = _render_retrieval(
        {
            "query": "x",
            "results": [],
            "episodes": [
                {
                    "episode_uuid": "ep-2",
                    "name": "ep-no-path",
                    "content": "Substance without provenance metadata.",
                    "group_id": "g",
                    "valid_at": None,
                },
            ],
        },
        cap=5000,
    )
    line = next(ln for ln in out.splitlines() if ln.startswith("- [episode]"))
    assert "Substance without provenance" in line
    assert "(" not in line.split(":")[0] or "ep-no-path" in line
