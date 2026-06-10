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

"""AC.EVX.2 — power-law activation contributes a neutral factor by
default; the named ``LOAM_FBM_ACTIVATION`` switch re-enables it with
NO code change; default-off is verifiable from production
configuration (the FIX-not-kill half of the June-7 verdict — the
machinery stays, gated on a live-access-log re-measurement).

Memory recall cycle, Slice 1.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.access_log import append_access_event
from loam.primary_persona.file_memory import (
    ACTIVATION_FLAG_ENV,
    FileMemoryStore,
    activation_enabled,
)


def _seeded_store(tmp_path: Path) -> tuple[FileMemoryStore, Path]:
    """Two files where activation (if live) flips the BM25 order."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)
    store.write_episode(
        name="turn/moderate",
        body="alpha beta amid unrelated scheduling noise",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    store.write_episode(
        name="turn/strong",
        body=" ".join(["alpha beta"] * 12) + " extra content",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    mod_path = next((memory_dir / "episodes" / "ws").rglob("moderate.md"))
    for i in range(20):
        append_access_event(
            memory_dir,
            file=str(mod_path),
            ts=now - timedelta(seconds=i * 30),
            op="read",
        )
    return store, memory_dir


def test_AC_EVX_2_default_off_is_verifiable(monkeypatch) -> None:
    """Production configuration (env unset) reports activation OFF;
    the named switch reports ON — the verifiable default."""
    monkeypatch.delenv(ACTIVATION_FLAG_ENV, raising=False)
    assert activation_enabled() is False, (
        "AC.EVX.2: activation must be OFF in default production config"
    )
    monkeypatch.setenv(ACTIVATION_FLAG_ENV, "1")
    assert activation_enabled() is True
    monkeypatch.setenv(ACTIVATION_FLAG_ENV, "off")
    assert activation_enabled() is False


def test_AC_EVX_2_neutral_by_default_reenabled_by_switch(
    tmp_path: Path, monkeypatch
) -> None:
    """Default: heavy recent access contributes a neutral factor (BM25
    order holds). Flag ON: the same store re-orders on activation —
    re-enable with no code change."""
    store, _memory_dir = _seeded_store(tmp_path)

    monkeypatch.delenv(ACTIVATION_FLAG_ENV, raising=False)
    off = store.search(query="alpha beta", group_ids=["ws"], num_results=2)
    off_names = [e["name"] for e in off["episodes"]]
    assert off_names[0] == "turn/strong", (
        f"AC.EVX.2: default-off must rank on pure BM25; got {off_names}"
    )

    monkeypatch.setenv(ACTIVATION_FLAG_ENV, "1")
    on = store.search(query="alpha beta", group_ids=["ws"], num_results=2)
    on_names = [e["name"] for e in on["episodes"]]
    assert on_names[0] == "turn/moderate", (
        f"AC.EVX.2: the named switch must re-enable the activation "
        f"re-order with no code change; got {on_names}"
    )
