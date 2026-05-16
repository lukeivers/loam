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
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PBR.2 / AC.PBR.4 — the frozen task-set loader.

The task set + the pass/fail rule + the materially-beats margin are
authored and CONTENT-HASH-PINNED BEFORE any arm runs (the proven
freeze-before-any-sub-agent / contamination spine). This module is
the read path: it loads ``tasks/tasks.json``, computes its sha256,
and exposes an immutable handle. A loader that silently tolerated a
post-freeze content change would destroy the contamination control —
:func:`load_frozen_task_set` pins the hash and the run records it so
the headline is reproducible from the preserved evidence.

HONEST SCOPE (D-PBR-2, recorded in tasks.json _README): the public
ProgramBench leaderboard eval requires a linux/amd64 + Docker harness
and the local upstream clone is an empty skeleton (no dataset, no
harness) on this Darwin/arm64 host — the v0.4.0 C4 host-block recurs
as a no-usable-public-set block (empirically rechecked this build).
This frozen set is a documented honest-scope ProgramBench-CLASS
substitute that PRESERVES the positive-real-outcome-floor property;
it does NOT fake real-leaderboard numbers (plan §3.3 / §8.2).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

TASKS_DIR = Path(__file__).resolve().parents[2] / "tasks"
TASKS_JSON = TASKS_DIR / "tasks.json"


@dataclass(frozen=True)
class FrozenTask:
    """One frozen non-subjective ProgramBench-class task.

    ``statement`` is the ONLY thing either arm receives (the
    non-technical user's plain-language intent — zero-interaction
    parity, AC.PBR.1). ``floor_check`` is the positive-real-outcome
    floor (exits 0 IFF the real outcome was actually delivered;
    hollow ⇒ non-pass by construction — AC.PBR.2). ``held_out_check``
    is the anti-overfit check whose inputs appear in NO prompt
    (AC.PBR.4). ``setup_files`` are written into a fresh per-(arm,
    task) work dir (environment isolation — AC.PBR.1).
    """

    id: str
    statement: str
    setup_files: dict[str, str]
    floor_check: str
    held_out_check: str
    expected_real_outcome: str


@dataclass(frozen=True)
class FrozenTaskSet:
    """The whole frozen set + the pinned content hash.

    ``content_sha256`` pins ``tasks.json`` at freeze time; the run
    records it so re-running the frozen scorer over the preserved
    per-task evidence yields the same verdict (AC.PBR.6
    reproducibility).
    """

    task_set_id: str
    content_sha256: str
    frozen_pass_rule: str
    frozen_failure_taxonomy: tuple[str, ...]
    tasks: tuple[FrozenTask, ...]
    tasks_dir: str

    def task_by_id(self, tid: str) -> FrozenTask:
        for t in self.tasks:
            if t.id == tid:
                return t
        raise KeyError(tid)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_frozen_task_set(
    tasks_json: Path | None = None,
) -> FrozenTaskSet:
    """Load + content-hash-pin the frozen task set (AC.PBR.2/.4).

    The sha is computed over the EXACT bytes on disk; any
    post-freeze edit changes the recorded hash and is therefore
    visible in the evidence (the contamination-prevention property,
    not a silent tolerate).
    """
    path = Path(tasks_json) if tasks_json else TASKS_JSON
    raw = path.read_text(encoding="utf-8")
    sha = _sha256(raw)
    doc = json.loads(raw)
    tasks = tuple(
        FrozenTask(
            id=t["id"],
            statement=t["statement"],
            setup_files=dict(t.get("setup", {}).get("files", {})),
            floor_check=t["floor_check"],
            held_out_check=t["held_out_check"],
            expected_real_outcome=t.get("expected_real_outcome", ""),
        )
        for t in doc["tasks"]
    )
    return FrozenTaskSet(
        task_set_id=doc["task_set_id"],
        content_sha256=sha,
        frozen_pass_rule=doc["frozen_pass_rule"],
        frozen_failure_taxonomy=tuple(doc["frozen_failure_taxonomy"]),
        tasks=tasks,
        tasks_dir=str(path.parent),
    )
