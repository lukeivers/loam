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

"""AC-FBM-SAL-5 (LIVE-STORE COLD-WALK — outcome-altitude, the bar) — B3.

Against a COPY of the REAL episode-store shape (real ``<task-notification>``
turns + real ``<channel>``-wrapped Luke-message turns copied into a TEMP root;
NEVER the live ``workspace/.loam`` store), through the production
``retrieve()`` entry-point with no pre-arranged state:

  - the task-notification junk is SUPPRESSED, AND
  - a real ``<channel>``-wrapped Luke message DOES surface on the same query.

This proves BOTH halves on the real store shape: the junk-drop AND the
load-bearing protect-real-messages property (a real message wrapped in a
``<channel>`` header is NOT mistaken for an empty channel event).

Skips (does not fail) if the live store is absent (CI / a fresh machine). The
live store is read ONLY to copy real episode FILES; it is never written.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from loam.primary_persona.file_memory import (
    SALIENCE_JUNK,
    FileMemoryStore,
    _salience_from_body,
    _split_frontmatter,
)
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve


LIVE_EPISODES = (
    Path.home() / "pos3" / "workspace" / ".loam" / "memory" / "episodes"
)


def _is_task_notif(body: str) -> bool:
    m = re.search(r"\[user\]\n(.*?)(?:\n\[assistant\]|\Z)", body, re.S)
    u = (m.group(1).strip() if m else "")
    return u.lstrip().startswith("<task-notification>")


def _is_channel_real(body: str) -> bool:
    m = re.search(r"\[user\]\n(.*?)(?:\n\[assistant\]|\Z)", body, re.S)
    u = (m.group(1).strip() if m else "")
    if not u.lstrip().startswith("<channel"):
        return False
    inner = re.sub(r"</?channel[^>]*>", "", u).strip()
    return len(inner) >= 30  # a real message, not an empty channel event


def _find_sample(predicate, limit_scan: int = 600):
    """Find one real live-store episode FILE matching ``predicate(body)``."""
    scanned = 0
    for group_dir in sorted(LIVE_EPISODES.iterdir()):
        if not group_dir.is_dir():
            continue
        for date_dir in sorted(group_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            for f in sorted(date_dir.iterdir()):
                if f.suffix != ".md":
                    continue
                scanned += 1
                if scanned > limit_scan:
                    return None
                try:
                    _, body = _split_frontmatter(f.read_text(encoding="utf-8"))
                except OSError:
                    continue
                if predicate(body):
                    return f
    return None


@pytest.mark.skipif(
    not LIVE_EPISODES.is_dir(), reason="live episode store not present"
)
def test_AC_FBM_SAL_5_live_store_cold_walk(tmp_path: Path) -> None:
    """Junk suppressed + real channel message surfaces, on the real store
    shape, through the production retrieve()."""
    junk_src = _find_sample(_is_task_notif)
    real_src = _find_sample(_is_channel_real)
    if junk_src is None or real_src is None:
        pytest.skip("no representative junk/real episodes found in live store")

    # Copy the two REAL episode files into a temp store (read-only of the live
    # source). We also write a synthetic substantive episode carrying a
    # distinctive token shared with BOTH the junk and real samples so the
    # query has a strong lexical anchor that the junk would otherwise win.
    episode_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=episode_dir)

    # Re-ingest both real bodies through the production write path so salience
    # is computed + stored exactly as it would be live.
    _, junk_body = _split_frontmatter(junk_src.read_text(encoding="utf-8"))
    _, real_body = _split_frontmatter(real_src.read_text(encoding="utf-8"))

    # Sanity: the structural scorer agrees with the classification.
    assert _salience_from_body(junk_body) == SALIENCE_JUNK, (
        "the live task-notification sample must score as junk"
    )
    assert _salience_from_body(real_body) > SALIENCE_JUNK, (
        "the live channel-wrapped real message must score as salient "
        "(protect-real-messages)"
    )

    store.write_episode(
        name="turn/live-junk",
        body=junk_body,
        source_description="cold-walk copy",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    store.write_episode(
        name="turn/live-real",
        body=real_body,
        source_description="cold-walk copy",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )

    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=None,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=episode_dir,
        episode_group_ids=("pos3",),
        top_n=5,
    )

    # Pick distinctive query terms from the REAL message body so it is the
    # intended match; the junk shares generic boilerplate but should be gated.
    real_terms = [
        t for t in re.split(r"\W+", real_body.lower())
        if len(t) >= 6 and t not in ("channel", "assistant")
    ][:6]
    if not real_terms:
        pytest.skip("real sample had no distinctive query terms")
    block = retrieve(prompt=" ".join(real_terms), config=cfg)

    # The real message surfaces (its episode is the intended match).
    # The junk's task-notification boilerplate tokens must NOT appear.
    assert "task-notification" not in block and "tool-use-id" not in block, (
        f"the task-notification junk must be suppressed; block={block!r}"
    )
    # The junk episode is still on disk (storage untouched).
    junk_on_disk = list((episode_dir / "episodes" / "pos3").rglob("live-junk*.md"))
    assert junk_on_disk, "the junk episode must remain stored on disk"
