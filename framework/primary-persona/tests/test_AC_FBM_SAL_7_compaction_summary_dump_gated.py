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

"""AC-FBM-SAL-7/-8/-9 — compaction-summary context-dump gated.

A compaction-summary turn — a user half OPENING with the continuation marker
"This session is being continued from a previous conversation that ran out of
context", followed by a multi-thousand-word summary naming every active
objective — was the single worst recall polluter on the live episode store
(loam-fbm-relevance-assessment §1.3: 19 such episodes; each matched none of
the four prior junk shapes, so it rode at full salience and BM25-dominated
almost every work-anchored query). The 5th signature in ``compute_salience``
tags it junk so it stops surfacing.

  * AC-FBM-SAL-7 — the dump's user half is tagged ``SALIENCE_JUNK``.
  * AC-FBM-SAL-8 — a real Luke turn that merely MENTIONS a continuation in
    prose stays ``SALIENCE_FULL`` (no false positive; protect-real-messages).
  * AC-FBM-SAL-9 (outcome-altitude) — proven end-to-end through the production
    write -> search -> merge ``retrieve()`` path, no pre-arranged retrieval
    state: the dump does NOT surface; a genuinely-relevant episode does.
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


# A distinctive token the dump AND the query share, so without the salience
# gate the dump would rank and surface on it.
SHARED_TOKEN = "flooblezormp"

# A compaction-summary dump body: the user half OPENS with the continuation
# marker, then a summary that (as the live dumps do) names every objective and
# carries the shared token — a strong lexical match on any work-anchored query.
_DUMP_BODY = (
    "[user]\n"
    "This session is being continued from a previous conversation that ran "
    "out of context. The conversation is summarized below:\n"
    f"Analysis: the user was working on the {SHARED_TOKEN} {SHARED_TOKEN} "
    f"objective, plus LitRPG, the memory system, Telegram, and revenue. "
    f"Every active objective touched the {SHARED_TOKEN} work.\n"
    "\n"
    "[assistant]\n"
    f"Continuing the {SHARED_TOKEN} work from the summary.\n"
)

# A GENUINE Luke turn that only MENTIONS a continuation in prose — must stay
# full salience (the no-false-positive / protect-real-messages side).
_REAL_MENTION = (
    "Continuing from where we left off in the previous conversation: please "
    "wire the salience gate's fifth signature and add the regression test."
)


def test_AC_FBM_SAL_7_compaction_summary_dump_tagged_junk() -> None:
    """The 5th signature tags a compaction-summary dump user half as junk."""
    user_half = (
        _DUMP_BODY.split("[assistant]")[0].replace("[user]\n", "", 1).strip()
    )
    assert compute_salience(user_half) == SALIENCE_JUNK


def test_AC_FBM_SAL_8_real_continuation_mention_stays_full() -> None:
    """A real turn that merely mentions a continuation is NOT mis-classified."""
    assert compute_salience(_REAL_MENTION) == SALIENCE_FULL


def test_AC_FBM_SAL_9_dump_does_not_surface_relevant_does(tmp_path: Path) -> None:
    """Outcome-altitude: real retrieve() — the dump is gated, the real hit wins.

    No pre-arranged retrieval state: both episodes are ingested through the
    production ``write_episode`` path (which computes + stores salience), then
    a real ``retrieve()`` call merges + ranks them.
    """
    episode_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=episode_dir)
    now = datetime.now(timezone.utc)

    # The compaction-summary dump — a strong lexical match on SHARED_TOKEN.
    store.write_episode(
        name="turn/compaction-summary-dump",
        body=_DUMP_BODY,
        source_description="test seed",
        reference_time=now,
        source="message",
        group_id="pos3",
    )
    # A genuinely-relevant real turn that also carries the shared token, so the
    # query has a real, non-junk episode to surface instead of the dump.
    real_body = (
        "[user]\n"
        f"How does the {SHARED_TOKEN} salience gate decide what to drop?\n"
        "\n"
        "[assistant]\n"
        f"The {SHARED_TOKEN} gate keys on structural junk signatures.\n"
    )
    store.write_episode(
        name="turn/real-relevant",
        body=real_body,
        source_description="test seed",
        reference_time=now,
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
    block = retrieve(prompt=f"tell me about the {SHARED_TOKEN} gate", config=cfg)

    # The dump's signature opening must NOT surface.
    assert "This session is being continued" not in block, (
        f"the compaction-summary dump must NOT surface; block={block!r}"
    )
    # The genuinely-relevant episode DOES surface in its place (its user-half
    # question is rendered; the dump is gated out).
    assert "decide what to drop" in block, (
        f"the genuinely-relevant episode must surface in its place; "
        f"block={block!r}"
    )
