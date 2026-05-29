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

"""AC.FBMW.3 — after the caller-side fix, a post-fix write does NOT
create or append under the doubled-``workspace`` shadow path.

The regression guard: with the corrected caller resolving the repo root,
no write ever lands under ``<repo>/workspace/workspace/.pos/`` again.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import cli
from loam.primary_persona.memory_write_queue import enqueue


def test_AC_FBMW_3_post_fix_write_avoids_shadow(monkeypatch, tmp_path):
    repo_root = tmp_path / "pos3"
    operator_ws = repo_root / "workspace"
    operator_ws.mkdir(parents=True)
    monkeypatch.delenv("LOAM_WORKSPACE_ROOT", raising=False)
    monkeypatch.chdir(operator_ws)

    resolved = cli._resolve_workspace(None)
    enqueue(
        workspace_root=resolved,
        turn_id="sess:postfix",
        session_id="sess",
        user_message="u",
        assistant_reply="a",
    )

    shadow = repo_root / "workspace" / "workspace"
    assert not shadow.exists(), (
        f"a post-fix write created the dead doubled shadow at {shadow}"
    )
    # The write landed in the single-workspace live queue instead.
    live_q = repo_root / "workspace" / ".pos" / "memory-write-queue"
    assert any(live_q.glob("*.json"))
