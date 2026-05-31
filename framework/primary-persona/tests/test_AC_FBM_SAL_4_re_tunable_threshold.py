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

"""AC-FBM-SAL-4 (RE-TUNABLE — load-bearing, outcome-altitude) — B3.

Lowering ``salience_threshold`` re-admits the previously-filtered junk episode
into the ``retrieve()`` surface — proving the gate is REVERSIBLE and nothing
was lost. The same junk episode that is suppressed at the default threshold
re-appears when the threshold drops below its salience, because it was never
removed from disk (AC-FBM-SAL-3), only gated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import (
    SALIENCE_THRESHOLD,
    RetrievalConfig,
    retrieve,
)


SHARED_TOKEN = "reglobbertwist"

_JUNK_BODY = (
    "[user]\n"
    "<task-notification>\n"
    "<task-id>retune7</task-id>\n"
    "<status>completed</status>\n"
    f"<result>{SHARED_TOKEN} {SHARED_TOKEN} {SHARED_TOKEN} done.</result>\n"
    "</task-notification>\n"
    "\n"
    "[assistant]\n"
    f"Finished the {SHARED_TOKEN} work.\n"
)


def _cfg(tmp_path: Path, episode_dir: Path) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=None,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=episode_dir,
        episode_group_ids=("pos3",),
        top_n=5,
    )


def test_AC_FBM_SAL_4_lowering_threshold_re_admits_junk(tmp_path: Path) -> None:
    """At the default threshold the junk is gated; lowering it re-admits."""
    episode_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=episode_dir)
    store.write_episode(
        name="turn/junk-retune",
        body=_JUNK_BODY,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    cfg = _cfg(tmp_path, episode_dir)
    prompt = f"tell me about {SHARED_TOKEN}"

    # Default threshold: the junk episode is GATED (does not surface).
    gated = retrieve(prompt=prompt, config=cfg, salience_threshold=SALIENCE_THRESHOLD)
    assert SHARED_TOKEN not in gated, (
        f"at the default threshold the junk must be gated; block={gated!r}"
    )

    # Lower the threshold below the junk's salience (0.0): it RE-ADMITS,
    # proving the gate is reversible and the episode was never removed.
    readmitted = retrieve(prompt=prompt, config=cfg, salience_threshold=-1.0)
    assert SHARED_TOKEN in readmitted, (
        "lowering the salience threshold must re-admit the previously-gated "
        f"junk episode (reversible, nothing lost); block={readmitted!r}"
    )
