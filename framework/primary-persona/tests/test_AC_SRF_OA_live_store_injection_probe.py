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

"""AC.SRF.OA (outcome-altitude: true) — through the production
user-prompt-submit entry point against the LIVE store with NO
pre-arranged state, a work-anchored query yields an injected block of
>=3 substantive lines, each carrying a path, with zero lines beginning
with a channel or task-notification envelope.

This is Plan A's live injection probe (the 2026-06-09 surfacing leg of
the $750k failure), replayed as a standing test. Production entry
point: the KP0-chain contributor (`build_keep_pace_contributor`) — the
exact callable the live UserPromptSubmit wiring registers — fed a live
envelope. The store + corpus are read-only here; skips (does not fail)
when the live machine state is absent (CI / fresh machine).

Memory recall cycle, Slice 2.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    build_keep_pace_contributor,
)


LIVE_EPISODE_DIR = Path.home() / "pos3" / "workspace" / ".loam" / "memory"
LIVE_CORPUS_DIR = (
    Path.home() / ".claude" / "projects" / "-Users-lukeivers-pos3" / "memory"
)


@pytest.mark.skipif(
    not (
        (LIVE_EPISODE_DIR / "episodes").is_dir() and LIVE_CORPUS_DIR.is_dir()
    ),
    reason="live workspace store/corpus absent (CI / fresh machine)",
)
def test_AC_SRF_OA_live_injection_block_substantive_paths_no_envelopes(
    tmp_path: Path,
) -> None:
    # Production contributor with the live config shape — corpus dir +
    # claude home + episode store all the real machine state; only the
    # index scratch dir is workspace-rooted (tmp keeps the probe from
    # touching the repo's own scratch).
    config = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=LIVE_CORPUS_DIR,
        claude_homes=(Path.home() / ".claude",),
        objectives_home=Path.home() / ".claude",
        episode_memory_dir=LIVE_EPISODE_DIR,
    )
    contributor = build_keep_pace_contributor(config)
    block = contributor(
        {
            "prompt": (
                "where do we stand on loam memory retrieval and the "
                "decision ledger build"
            ),
            "workspace": {"project_dir": str(tmp_path)},
        }
    )
    assert block, "AC.SRF.OA: a work-anchored query must inject a block"

    content_lines = [
        ln
        for ln in block.splitlines()
        if ln.strip().startswith(("- ", "=== record:"))
    ]
    assert len(content_lines) >= 3, (
        f"AC.SRF.OA: expected >=3 substantive lines, got "
        f"{len(content_lines)}: {block!r}"
    )
    for ln in content_lines:
        stripped = ln.strip()
        assert not stripped.startswith("<channel"), f"envelope line: {ln!r}"
        assert not stripped.startswith("<task-notification"), (
            f"notification line: {ln!r}"
        )
        if stripped.startswith("- "):
            assert "[source: " in stripped and "/" in stripped, (
                f"AC.SRF.OA: pointer line missing a followable path: {ln!r}"
            )
