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

"""AC-FBM-CON-1 — the production composer registers the GATED keep-pace
turn contributor, NOT the ungated file-memory contributor.

FBM path consolidation: ``build_session_composer``'s production (client-None)
branch must register the consolidation contributor — the gated
``keep_pace.retrieval.register_keep_pace_turn_contributor`` — under the
``memory-retrieval`` name at ``TriggerKind.turn``, and must NOT register the
retired ungated ``register_file_memory_retrieval``.

This is a wiring AC: it inspects the composer's registered turn contributors
and proves the live registration was repointed.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.context_composer import TriggerKind
from loam.primary_persona.session_start_emitter import build_session_composer


def test_composer_registers_memory_retrieval_turn_contributor(
    tmp_path: Path,
) -> None:
    """The production path registers exactly one ``memory-retrieval``
    turn contributor (the gated keep-pace one)."""
    ws = tmp_path / "myws"
    ws.mkdir()

    # No memory_client_factory => production client-None branch fires.
    composer = build_session_composer(
        ws,
        memory_client_factory=lambda _root: None,
        register_tracker=False,
    )

    turn_contribs = composer.contributors(trigger_kind=TriggerKind.turn)
    names = [c.name for c in turn_contribs]
    assert "memory-retrieval" in names, (
        "the production composer must register a turn-level "
        "memory-retrieval contributor"
    )
    # Exactly one memory-retrieval registration (no double-register).
    assert names.count("memory-retrieval") == 1


def test_gated_contributor_sources_from_keep_pace(tmp_path: Path) -> None:
    """The registered contributor must be the GATED keep-pace one — its
    module is ``keep_pace.retrieval``, not ``file_memory``."""
    ws = tmp_path / "myws"
    ws.mkdir()

    composer = build_session_composer(
        ws,
        memory_client_factory=lambda _root: None,
        register_tracker=False,
    )
    [c] = [
        c
        for c in composer.contributors(trigger_kind=TriggerKind.turn)
        if c.name == "memory-retrieval"
    ]
    # The gated contributor closure is defined inside
    # ``keep_pace.retrieval.register_keep_pace_turn_contributor``. The
    # ungated one is defined in ``file_memory``. Discriminate by the
    # closure's defining module.
    assert "keep_pace" in c.fn.__module__, (
        f"the memory-retrieval contributor must come from the gated "
        f"keep_pace path, not {c.fn.__module__!r}"
    )
