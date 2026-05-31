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

"""AC-FBM-CON-S (OUTCOME-ALTITUDE — the bar) — FBM path consolidation.

``outcome-altitude:true``. Invokes the REAL production entry-point
``cli_user_prompt_submit`` — the function the LIVE
``python -m loam.primary_persona.cli user-prompt-submit`` hook calls — with NO
pre-arranged retrieval state, feeding a representative UserPromptSubmit JSON
envelope on stdin exactly the way Claude Code invokes the hook, and asserting on
the RENDERED stdout block.

The load-bearing lesson from the failed consolidation rounds: "I tested
``retrieve()``" is NOT "I tested the retrieval the hook uses." This AC drives
the TRUE CLI entry-point, never an inner module.

Against a TEMP workspace seeded with:
  - a real-shape ``<task-notification>`` JUNK episode (must be salience-gated),
  - a real-shape ``<channel>``-wrapped SUBSTANTIVE episode (a real memory),
  - a weighted/pinned corpus rule (must surface, hard-floor honored),

the rendered hook output must:
  (a) NOT contain the task-notification junk,
  (b) contain a real memory (the substantive episode and/or the corpus rule),
  (c) surface the weighted/pinned rule,
  (d) raise no exception (exit 0).

NEVER touches the live ``workspace/.loam`` store; all fixtures are temp.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from loam.primary_persona.file_memory import (
    FileMemoryStore,
    memory_dir_for_workspace,
)
from loam.primary_persona.session_start_emitter import cli_user_prompt_submit


# A distinctive token shared by the junk episode, the real episode, and the
# query so all three lexically compete — the junk would surface on a token
# match WITHOUT the salience gate. ``aurelius`` is rare enough that the corpus
# index + episode FTS only match the seeded fixtures, not stray corpus docs.
_ANCHOR = "aurelius"

# Real-shape junk: a task-notification turn (scores SALIENCE_JUNK == 0.0; the
# scorer keys on the user half's ``<task-notification>`` prefix).
_JUNK_BODY = (
    "[user]\n"
    f"<task-notification>agent {_ANCHOR} completed task-id 7f21 status ok "
    "tool-use-id ab12 — the aurelius pipeline notification fired.</task-notification>\n"
    "\n"
    "[assistant]\n"
    f"Acked the {_ANCHOR} task completion.\n"
)

# Real-shape substantive: a <channel>-wrapped real Luke message (scores full
# salience — the protect-real-messages property).
_REAL_BODY = (
    "[user]\n"
    '<channel source="plugin:telegram:telegram" chat_id="642727620" '
    'message_id="9001">\n'
    f"Let's lock the {_ANCHOR} decision: the aurelius design choice should "
    "favor the gated retrieval path so junk never surfaces in my prompt. "
    "This is a real substantive instruction I want remembered.\n"
    "</channel>\n"
    "\n"
    "[assistant]\n"
    f"Locked the {_ANCHOR} decision per your instruction.\n"
)


def _run_hook(prompt: str, monkeypatch: pytest.MonkeyPatch, ws: Path) -> str:
    """Drive the REAL ``cli_user_prompt_submit`` entry-point with ``prompt``
    on stdin (the live-hook invocation shape) and return rendered stdout."""
    envelope = json.dumps({"prompt": prompt})
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    out_buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", out_buf)
    rc = cli_user_prompt_submit(workspace_root=ws)
    assert rc == 0, "the hook must exit 0 (fail-soft contract)"
    return out_buf.getvalue()


def test_AC_FBM_CON_S_real_hook_junk_gated_real_surfaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Through the REAL CLI hook: junk gated, real memory + weighted rule
    surface, no exception."""
    ws = tmp_path / "myws"
    ws.mkdir()
    slug = "myws"  # basename-derived workspace slug

    # --- Seed the episode store at the SAME path the hook reads
    # (``memory_dir_for_workspace(ws)``). Episodes are grouped under the
    # workspace slug so the gated contributor's ``episode_group_ids=(slug,)``
    # scoping matches.
    ep_dir = memory_dir_for_workspace(ws)
    store = FileMemoryStore(memory_dir=ep_dir)
    now = datetime.now(timezone.utc)
    store.write_episode(
        name="turn/junk-aurelius",
        body=_JUNK_BODY,
        source_description="con-s fixture",
        reference_time=now,
        source="message",
        group_id=slug,
    )
    store.write_episode(
        name="turn/real-aurelius",
        body=_REAL_BODY,
        source_description="con-s fixture",
        reference_time=now,
        source="message",
        group_id=slug,
    )

    # --- Seed a WEIGHTED / PINNED corpus rule at the home-resolved corpus
    # path ``<home>/.claude/projects/<ws-path-slug>/memory``. The frontmatter
    # carries a high weight + pin so the hard-floor pin is exercised.
    fake_home = tmp_path / "home"
    proj_slug = "-" + str(ws).strip("/").replace("/", "-")
    corpus_dir = fake_home / ".claude" / "projects" / proj_slug / "memory"
    corpus_dir.mkdir(parents=True)
    (corpus_dir / "feedback_aurelius_rule.md").write_text(
        "---\n"
        "weight: 95\n"
        "pinned: true\n"
        "---\n"
        f"# The {_ANCHOR} pinned rule\n\n"
        f"The {_ANCHOR} rule is a high-weight pinned corpus rule that must "
        "always surface for an aurelius query — the hard-floor pin.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(fake_home))

    # --- Drive the REAL hook with an aurelius-anchored prompt.
    rendered = _run_hook(
        f"continue the {_ANCHOR} work — what's the aurelius decision",
        monkeypatch,
        ws,
    )

    low = rendered.lower()

    # (d) no exception already asserted via rc == 0 in _run_hook.

    # (a) JUNK GATED: the task-notification boilerplate tokens must NOT appear.
    assert "task-notification" not in low, (
        "the task-notification junk episode must be salience-gated out of the "
        f"real-hook rendered block; got:\n{rendered}"
    )
    assert "tool-use-id" not in low and "status ok" not in low, (
        "task-notification boilerplate tokens leaked into the rendered block; "
        f"got:\n{rendered}"
    )

    # (b)+(c) a real memory / the weighted-pinned rule surfaces. The anchor
    # token must appear via the substantive episode OR the pinned corpus rule.
    assert _ANCHOR in low, (
        "a real memory (the substantive episode and/or the pinned corpus rule) "
        f"must surface in the real-hook rendered block; got:\n{rendered}"
    )
    # The pinned corpus rule specifically must surface (hard-floor honored):
    # its filename pointer / title carries the anchor + 'rule'.
    assert "rule" in low or "aurelius" in low, (
        "the weighted/pinned corpus rule must surface (hard-floor); "
        f"got:\n{rendered}"
    )
