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

"""AC.SURFACE.4 — a resolver/registration error fails OPEN to the old default.

Plan §6 AC.SURFACE.4 / §8 #3: a resolver/registration error fails OPEN to
the current always-on default-set (work-streams + projects + relational),
NOT to zero blocks — the choice-aware path never regresses a user to a
blank per-turn surface.
"""

from __future__ import annotations

import pytest

from loam.primary_persona.context_composer import (
    ComposedContextPayload,
    TriggerKind,
)
from loam.primary_persona.session_start_gate import compose_session_fields
from loam.primary_persona.keep_pace import lens_choice as lc


def _turn_block_names(composer: ComposedContextPayload) -> set[str]:
    return {c.name for c in composer.contributors(TriggerKind.turn)}


def test_AC_SURFACE_4_default_set_is_the_inc4_trio() -> None:
    # The named fail-open floor IS the current always-on trio — non-empty
    # by construction (the anti-regression contract).
    assert set(lc.DEFAULT_ALWAYS_ON_SET) == {
        lc.LENS_STREAMS,
        lc.LENS_PROJECTS,
        lc.LENS_RELATIONAL,
    }
    assert lc.DEFAULT_ALWAYS_ON_SET, "the fail-open default-set is EMPTY"


def test_AC_SURFACE_4_resolver_blowup_falls_open_to_trio(monkeypatch) -> None:
    # Force the resolver itself to raise mid-registration. The
    # registration must still register the always-on trio (fail-open to
    # the OLD default), never zero blocks.
    def _boom(*_a, **_k):
        raise RuntimeError("resolver exploded")

    monkeypatch.setattr(lc, "resolve_lens_set", _boom)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    lc.register_chosen_lenses(composer)
    names = _turn_block_names(composer)
    assert names, "registration regressed to ZERO turn blocks on resolver error"
    assert lc.LENS_STREAMS in names
    assert lc.LENS_PROJECTS in names
    assert lc.LENS_RELATIONAL in names


def test_AC_SURFACE_4_never_empty_even_when_resolver_returns_empty(
    monkeypatch,
) -> None:
    # Defence-in-depth: even if some future resolver bug returned an empty
    # set, the registration must not surface zero blocks — it falls open
    # to the trio.
    monkeypatch.setattr(lc, "resolve_lens_set", lambda *a, **k: ())
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    lc.register_chosen_lenses(composer)
    assert _turn_block_names(composer), "empty resolved set surfaced zero blocks"
