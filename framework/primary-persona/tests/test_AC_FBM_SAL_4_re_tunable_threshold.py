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

"""AC-FBM-SAL-4 (REVERSIBLE / NOTHING-LOST — load-bearing, outcome-altitude) — B3.

The gate is REVERSIBLE and nothing is lost: a turn the gate classifies as junk is
recoverable in full, so a mis-judged junk turn can be re-admitted.

Post fbm-write-time-salience-gate-cold-tier (Slice A) the REVERSIBILITY MECHANISM
moved. Before Slice A, junk was written to the hot FTS index and suppressed only
at retrieval, so lowering ``salience_threshold`` re-surfaced it. After Slice A,
the write gate diverts junk to the COLD tier at ingest — it never enters the hot
index, so threshold-lowering cannot (and must not) re-surface it. Reversibility
now reads through the cold tier: the junk turn is on disk verbatim and the
re-admit path is a direct cold-tier read (a future operator re-write into the hot
tier). The PROPERTY the AC protects — nothing is lost, the gate is reversible — is
unchanged; only the re-admit mechanism is the cold-tier re-read rather than a
retrieval-threshold knob. (Default-threshold gating of pre-Slice-A hot-tier junk
is still covered by AC-FBM-SAL-1/-7's read-side gate.)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    COLD_SUBDIR,
    EPISODES_SUBDIR,
    FileMemoryStore,
)
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


def test_AC_FBM_SAL_4_junk_gated_but_recoverable_from_cold_tier(
    tmp_path: Path,
) -> None:
    """The junk turn never surfaces through ``retrieve()`` (it is diverted to
    the cold tier at write, not in the hot index) — AND it is fully recoverable
    from the cold tier, proving the gate is reversible and nothing was lost."""
    episode_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=episode_dir)
    result = store.write_episode(
        name="turn/junk-retune",
        body=_JUNK_BODY,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    # The junk went cold (never entered the hot index).
    assert COLD_SUBDIR in Path(result["path"]).parts
    assert not (episode_dir / EPISODES_SUBDIR).exists() or not list(
        (episode_dir / EPISODES_SUBDIR).rglob("*.md")
    ), "junk must not be in the hot episodes tier"

    cfg = _cfg(tmp_path, episode_dir)
    prompt = f"tell me about {SHARED_TOKEN}"

    # The junk is NOT in the hot index, so it does not surface — and lowering the
    # retrieval threshold cannot re-surface it (it was never indexed). The
    # surfacing gate and the storage tier are now distinct concerns.
    gated = retrieve(prompt=prompt, config=cfg, salience_threshold=SALIENCE_THRESHOLD)
    assert SHARED_TOKEN not in gated, (
        f"the cold-tier junk must not surface through retrieve(); block={gated!r}"
    )
    floored = retrieve(prompt=prompt, config=cfg, salience_threshold=-1.0)
    assert SHARED_TOKEN not in floored, (
        "even with the threshold floored, cold-tier junk does not re-surface "
        f"through retrieve() — it was never indexed; block={floored!r}"
    )

    # REVERSIBLE / nothing-lost: the junk turn is recoverable in full from the
    # cold tier (the re-admit path). This is the property AC-FBM-SAL-4 protects.
    cold_files = list((episode_dir / COLD_SUBDIR).rglob("*junk-retune*.md"))
    assert len(cold_files) == 1, (
        f"the junk turn must be recoverable from the cold tier; {cold_files}"
    )
    assert SHARED_TOKEN in cold_files[0].read_text(encoding="utf-8"), (
        "the cold-tier turn must carry its full body verbatim (nothing lost)"
    )
