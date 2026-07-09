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

"""AC.PSR.7 — per-turn keep-pace shows persona P's episodes only, while
cross-workstream rulings still surface (the D2 split, on the LIVE
per-turn path ``keep_pace/retrieval.py``).

The store INTERLEAVES personas so P's episodes are NOT all in the BM25
candidate window ahead of the other persona's (F2-2): the other
persona's episodes out-rank P's by BM25 and are more numerous than the
top-N. A post-filter-after-top-N method takes the (all-other-persona)
top-N then filters → P's episodic block empties. The in-scan filter
drops the other persona in the SQL WHERE, so P's window survives.

Also asserts the D2 split: a ruling recorded under a DIFFERENT
workstream still surfaces in the same per-turn block (the decision
branch is NOT session-scoped).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.decision_ledger import write_decision
from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    _resolve_composer_config,
    retrieve,
)

from _helpers_keep_pace import write_corpus


def _seed(root: Path) -> tuple[Path, Path]:
    corpus = root / "memory"
    write_corpus(corpus)
    ep = root / "ws-memory"
    store = FileMemoryStore(memory_dir=ep)
    now = datetime.now(timezone.utc)
    # 8 other-persona episodes, HIGHER BM25 (dense repetition of the
    # query term) and more numerous than the top-N.
    for i in range(8):
        store.write_episode(
            name=f"turn/q-{i}",
            body=(
                "kilnbench kilnbench kilnbench telemetry telemetry "
                f"OTHERPERSONA dense run {i}"
            ),
            source_description="t",
            reference_time=now,
            source="message",
            group_id="pos3",
            session_key="loam-dev",
        )
    # 3 persona-P episodes, lower BM25 (sparser).
    for i in range(3):
        store.write_episode(
            name=f"turn/p-{i}",
            body=f"kilnbench telemetry PERSONAP aurora step {i}",
            source_description="t",
            reference_time=now,
            source="message",
            group_id="pos3",
            session_key="master-control",
        )
    # A ruling under a DIFFERENT workstream (semantic — must stay global).
    write_decision(
        ep,
        question="How large is the Tilth raise ask?",
        ruling="$750,000 at $4M post-money",
        reasoning="AI-era raises differ; comp-heavy is fine founder-led.",
        entities=("Tilth", "raise", "valuation"),
        aliases=("the raise",),
        source="telegram message 14053",
        workstream="tilth",
    )
    return corpus, ep


def test_AC_PSR_7_perturn_shows_only_P_and_ruling_still_global(
    tmp_path: Path,
) -> None:
    corpus, ep = _seed(tmp_path)
    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=ep,
        episode_group_ids=("pos3",),
        episode_session_key="master-control",
    )
    block = retrieve(
        prompt="kilnbench telemetry status and the Tilth raise", config=cfg
    )
    assert block, "expected a non-empty per-turn block"
    # Episodic snippets are all P's.
    assert "PERSONAP" in block, "persona P's episodes must surface"
    assert "OTHERPERSONA" not in block, (
        "no other-persona episode may surface (in-scan filter, not "
        "post-top-N)"
    )
    # The cross-workstream ruling still surfaces (D2 — semantic global).
    assert "$750,000" in block, (
        "a ruling from another workstream must still surface — the "
        "decision branch is not session-scoped (AC.PSR.4 / D2)"
    )


def test_AC_PSR_7_no_session_key_is_workspace_global(tmp_path: Path) -> None:
    """With no episode_session_key (single-session), BOTH personas'
    episodes surface — the filter is off (AC.PSR.3 no-op)."""
    corpus, ep = _seed(tmp_path)
    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=ep,
        episode_group_ids=("pos3",),
        episode_session_key=None,
    )
    block = retrieve(prompt="kilnbench telemetry status", config=cfg)
    assert "OTHERPERSONA" in block, (
        "with the filter off, workspace-global behaviour is preserved"
    )


def test_AC_PSR_7_live_resolver_threads_session_key(tmp_path: Path) -> None:
    """The LIVE per-turn config resolver carries the resolved
    session_key onto the episode branch (episode_session_key), not the
    group id — the wiring that scopes the live contributor."""
    cfg = _resolve_composer_config(tmp_path, "pos3", "master-control")
    assert cfg.episode_session_key == "master-control"
    # group_id scoping is unchanged (workspace-global group).
    assert cfg.episode_group_ids == ("pos3",)


async def test_AC_PSR_7_dormant_twin_threads_session_key(
    tmp_path: Path, monkeypatch
) -> None:
    """Dormant-twin consistency (plan §5): the DORMANT memory_consumer
    MCP twin threads session_key into its write so re-enabling the MCP
    path cannot reintroduce the leak. A client that ACCEPTS the kwarg
    receives it."""
    from loam.primary_persona.memory_consumer import TurnAggregator

    monkeypatch.setenv("CLAUDE_PERSONA", "master-control")

    class _RecordingClient:
        def __init__(self) -> None:
            self.add_kwargs: list[dict] = []

        async def add_episode(self, **kwargs):
            self.add_kwargs.append(kwargs)
            return {"episode_uuid": "u1"}

    client = _RecordingClient()
    agg = TurnAggregator(memory_client=client, workspace_slug="pos3")
    await agg.close_turn(
        turn_id="s1:t0", user_message="u", persona_reply="r"
    )
    assert client.add_kwargs, "the dormant twin must call add_episode"
    assert client.add_kwargs[0].get("session_key") == "master-control", (
        "the dormant write must thread the channel-session key when the "
        "client accepts it"
    )


async def test_AC_PSR_7_dormant_twin_legacy_client_still_works(
    tmp_path: Path, monkeypatch
) -> None:
    """A legacy client whose add_episode has NO session_key kwarg is
    retried without it (byte-identical for that client) — no crash."""
    from loam.primary_persona.memory_consumer import TurnAggregator

    monkeypatch.setenv("CLAUDE_PERSONA", "master-control")

    class _LegacyClient:
        def __init__(self) -> None:
            self.calls = 0

        async def add_episode(
            self, *, name, body, source_description, reference_time, source,
            group_id,
        ):
            self.calls += 1
            return {"episode_uuid": "u1"}

    client = _LegacyClient()
    agg = TurnAggregator(memory_client=client, workspace_slug="pos3")
    await agg.close_turn(
        turn_id="s1:t0", user_message="u", persona_reply="r"
    )
    assert client.calls == 1, "legacy client must be retried without the kwarg"
