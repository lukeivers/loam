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

"""AC.GFE.1 / .2 / .4 / .5 — GROUND-FLOOR EXTRACTION (memory redesign Stage 1a).

Carve the always-on constitutional FLOOR (the ``CLAUDE.md`` hierarchy) OUT of
the relevance-ranked per-turn pool. The floor still injects unconditionally via
the SessionStart corpus-inline floor + the subagent microkernel bundle + Claude
Code's native CLAUDE.md load; ranking it in the per-turn pool is redundant and
starves topical facts. The carve is expressed at the LIVE-CONFIG layer (the two
production resolvers), leaving the general ``discover_corpus`` contract + every
direct-config caller unchanged.

  - AC.GFE.1 — the production resolvers do NOT thread the ``~/.claude``
    constitutional home into the ranked corpus (``claude_homes == ()``),
    regardless of prompt.
  - AC.GFE.2 — the constitution is STILL in the SessionStart always-load floor,
    so it injects every session (removed from ranking, retained on the floor).
  - AC.GFE.4 — the general ``discover_corpus`` contract is unchanged: a caller
    that passes ``claude_homes`` still gets ``CLAUDE.md`` (no regression for
    direct-config callers / the omnibus-penalty suite).
  - AC.GFE.5 — the ``RANK_CONSTITUTIONAL_FLOOR`` lever is reversible: flipping it
    ``True`` re-admits the constitution into the ranked pool exactly as before.

The outcome-altitude proof (a freed slot goes to a real topical hit over the
production ``retrieve()`` entry-point) lives in
``test_AC_GFE_3_OA_freed_slot_topical_hit.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.keep_pace import retrieval as _retrieval
from loam.primary_persona.keep_pace.corpus_index import discover_corpus
from loam.primary_persona.keep_pace.retrieval import (
    RANK_CONSTITUTIONAL_FLOOR,
    _resolve_composer_config,
    _resolve_live_config,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FLOOR_HOOK = (
    _REPO_ROOT
    / "framework"
    / "hands-off-lifecycle"
    / "hooks"
    / "corpus_inline_session_start.py"
)


# --- AC.GFE.1 — constitution is not a ranked-corpus source on the live path ---


@pytest.mark.parametrize(
    "prompt",
    [
        "review the widget calibration protocol",  # on-topic-shaped
        "hello",  # off-topic / trivial-shaped
        "",  # empty
    ],
)
def test_AC_GFE_1_live_resolver_omits_constitutional_floor(prompt: str) -> None:
    """The UserPromptSubmit resolver never threads ``~/.claude`` as a ranked
    corpus source — for ANY prompt (``claude_homes`` is prompt-independent, so
    on-topic and off-topic turns alike carry no constitutional hit)."""
    envelope = {"prompt": prompt, "workspace": {"project_dir": "/tmp/gfe-ws"}}
    cfg = _resolve_live_config(envelope)
    assert cfg.claude_homes == ()


def test_AC_GFE_1_composer_resolver_omits_constitutional_floor() -> None:
    """The SessionStart-composer + subagent-bundle resolver (both route through
    ``_resolve_composer_config``) likewise omits the constitutional home."""
    cfg = _resolve_composer_config(Path("/tmp/gfe-ws"), "gfe-slug")
    assert cfg.claude_homes == ()


def test_AC_GFE_1_default_lever_is_off() -> None:
    """The S1a default carves the floor out of ranking."""
    assert RANK_CONSTITUTIONAL_FLOOR is False


# --- AC.GFE.2 — the constitution still injects via the SessionStart floor ------


def test_AC_GFE_2_constitution_retained_in_sessionstart_floor() -> None:
    """The carve removes CLAUDE.md from the RANKED pool only. The always-on
    SessionStart corpus-inline floor must still carry it so the constitution
    injects every session (owner-approved: floored via the existing surfaces,
    not the ranker). Real signal: the floor hook's always-load set still lists
    CLAUDE.md."""
    assert _FLOOR_HOOK.is_file()
    text = _FLOOR_HOOK.read_text(encoding="utf-8")
    assert '"CLAUDE.md"' in text


# --- AC.GFE.4 — the general discover_corpus contract is unchanged --------------


def test_AC_GFE_4_discover_corpus_general_contract_unchanged(
    tmp_path: Path,
) -> None:
    """The carve lives ONLY at the live-config layer. The general
    ``discover_corpus`` — used by direct-config callers and the omnibus-penalty
    suite — is untouched: a caller that passes ``claude_homes`` still gets the
    CLAUDE.md hierarchy (no regression for non-live callers)."""
    home = tmp_path / "home"
    home.mkdir()
    (home / "CLAUDE.md").write_text("# Constitution\n\nAlways rules.\n")
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "feedback_topic.md").write_text("# Topic\n\nWidget notes.\n")

    paths = discover_corpus(memory_dir=memory_dir, claude_homes=(home,))
    names = {p.name for p in paths}
    assert "CLAUDE.md" in names  # general contract preserved
    assert "feedback_topic.md" in names


# --- AC.GFE.5 — the reversibility lever re-admits the constitution -------------


def test_AC_GFE_5_lever_reversibility(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flipping ``RANK_CONSTITUTIONAL_FLOOR`` True re-admits the constitutional
    home into BOTH resolvers' ranked corpus — proving nothing was deleted and
    the carve is a one-line reversible lever."""
    envelope = {"workspace": {"project_dir": "/tmp/gfe-ws"}}

    # Default (carved): no constitutional home threaded.
    assert _resolve_live_config(envelope).claude_homes == ()
    assert _resolve_composer_config(Path("/tmp/gfe-ws"), "s").claude_homes == ()

    # Lever ON: the constitution is re-admitted, exactly as pre-carve.
    monkeypatch.setattr(_retrieval, "RANK_CONSTITUTIONAL_FLOOR", True)
    expected_home = Path.home() / ".claude"
    assert _resolve_live_config(envelope).claude_homes == (expected_home,)
    assert _resolve_composer_config(Path("/tmp/gfe-ws"), "s").claude_homes == (
        expected_home,
    )
