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

"""AC-FBM-SAL-1 (JUNK-FILTERED — load-bearing, outcome-altitude) — B3.

A scaffolding episode (a ``<task-notification>`` turn) is tagged near-zero
salience AT INGEST and does NOT surface in ``retrieve()`` even when it shares
tokens with the query — the live-store recall-pollution complaint reproduced
and killed. Proven end-to-end through the production write→search→merge path
with no pre-arranged retrieval state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    SALIENCE_FULL,
    SALIENCE_JUNK,
    FileMemoryStore,
    compute_salience,
)
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve


# A distinctive token the junk turn AND the query share, so without the
# salience gate the junk turn would rank and surface on it.
SHARED_TOKEN = "flooblezormp"

# A task-notification body that carries the shared token (so it is a strong
# lexical match) yet is pure scaffolding on its user half.
_TASK_NOTIF_BODY = (
    "[user]\n"
    "<task-notification>\n"
    "<task-id>a58636f21a3d43459</task-id>\n"
    "<tool-use-id>toolu_01JYci2nPBHvvpNeguMS7UTV</tool-use-id>\n"
    "<status>completed</status>\n"
    f"<summary>Agent finished the {SHARED_TOKEN} {SHARED_TOKEN} task</summary>\n"
    f"<result>Done with {SHARED_TOKEN} {SHARED_TOKEN} {SHARED_TOKEN}.</result>\n"
    "</task-notification>\n"
    "\n"
    "[assistant]\n"
    f"Owned and corrected the {SHARED_TOKEN} work.\n"
)


def test_compute_salience_tags_task_notification_junk() -> None:
    """The structural scorer tags a task-notification user half as junk."""
    user_half = (
        _TASK_NOTIF_BODY.split("[assistant]")[0]
        .replace("[user]\n", "", 1)
        .strip()
    )
    assert compute_salience(user_half) == SALIENCE_JUNK
    # A substantive user half is full salience (the no-false-positive side).
    assert compute_salience(
        "Build the episode salience gate now please, with a re-tunable threshold"
    ) == SALIENCE_FULL


def test_AC_FBM_SAL_1_junk_episode_does_not_surface(tmp_path: Path) -> None:
    """A task-notification episode sharing the query token does NOT surface."""
    episode_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=episode_dir)
    # Ingest the junk turn through the production write path (which computes
    # + stores salience).
    store.write_episode(
        name="turn/junk-task-notif",
        body=_TASK_NOTIF_BODY,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )

    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=None,  # no corpus — isolate the episode-gate behaviour
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=episode_dir,
        episode_group_ids=("pos3",),
        top_n=5,
    )
    # Query carries the shared token + objective-free anchor; the junk turn is
    # the only episode and is a strong lexical match — yet salience gates it.
    block = retrieve(prompt=f"tell me about {SHARED_TOKEN}", config=cfg)
    assert SHARED_TOKEN not in block, (
        "the task-notification junk episode must NOT surface even though it "
        f"shares the query token; block={block!r}"
    )
    # The token boilerplate from the user half must not leak either.
    assert "task-id" not in block and "tool-use-id" not in block
