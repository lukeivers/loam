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

"""Shared helpers for the AC.RTEL retrieval-telemetry suite.

Seeds an episode on a given topic + reads the appended JSONL telemetry
records back, so each AC test drives the real ``retrieve`` entry-point
and inspects the on-disk log the recorder wrote.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore


def seed_episode(
    memory_dir: Path, *, group_id: str, name: str, body: str
) -> None:
    """Write one episode into a FileMemoryStore at ``memory_dir``."""
    store = FileMemoryStore(memory_dir=memory_dir)
    store.write_episode(
        name=f"turn/{name}",
        body=body,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id=group_id,
    )


def read_records(telemetry_dir: Path) -> list[dict]:
    """Parse every JSONL record under ``telemetry_dir`` (all day files),
    in file+line order."""
    records: list[dict] = []
    for path in sorted(Path(telemetry_dir).glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
