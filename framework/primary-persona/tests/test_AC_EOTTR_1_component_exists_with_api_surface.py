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

"""AC.EOTTR.1 — End-of-turn trait-reflection module exists at the
canonical path and exposes the documented API surface.

Outcome: ``loam.primary_persona.end_of_turn_trait_reflection``
imports clean and exposes:

  - ``run_trait_reflection(*, workspace_root, session_id,
    assistant_text, turn_id=None) -> dict``
  - ``evaluate_all_traits(assistant_text) -> list[dict]``
  - ``TRAIT_HEURISTICS`` (the seven-trait keyword table)
  - ``cli_trait_reflection_stop(workspace_root) -> int``
"""

from __future__ import annotations

import inspect
from pathlib import Path


def test_AC_EOTTR_1_module_imports_and_lives_at_canonical_path() -> None:
    """Module imports clean from the canonical package path."""
    import loam.primary_persona.end_of_turn_trait_reflection as mod

    # Sanity: the file is the one we authored.
    assert mod.__file__ is not None
    assert "end_of_turn_trait_reflection.py" in mod.__file__


def test_AC_EOTTR_1_run_trait_reflection_signature_matches_documented_api() -> None:
    """The public ``run_trait_reflection`` callable accepts the
    documented kwargs and returns a dict."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        run_trait_reflection,
    )

    sig = inspect.signature(run_trait_reflection)
    params = sig.parameters
    # Documented kwargs: workspace_root, session_id, assistant_text, turn_id.
    assert "workspace_root" in params
    assert "session_id" in params
    assert "assistant_text" in params
    assert "turn_id" in params
    # All kwargs are keyword-only (per the ``*,`` in the signature).
    for name in ("workspace_root", "session_id", "assistant_text", "turn_id"):
        assert params[name].kind == inspect.Parameter.KEYWORD_ONLY


def test_AC_EOTTR_1_run_trait_reflection_returns_dict_with_documented_keys(
    tmp_path: Path,
) -> None:
    """Calling the public API yields a dict carrying ``session_id``,
    ``turn_id``, ``verdicts``, ``assistant_text_sha256``, ``ts``."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        run_trait_reflection,
    )

    result = run_trait_reflection(
        workspace_root=tmp_path,
        session_id="s-eottr-1",
        assistant_text="dispatching agent now.",
        turn_id="s-eottr-1:abc",
    )
    assert isinstance(result, dict)
    for key in ("session_id", "turn_id", "verdicts", "assistant_text_sha256", "ts"):
        assert key in result
    assert result["session_id"] == "s-eottr-1"
    assert result["turn_id"] == "s-eottr-1:abc"
    assert isinstance(result["verdicts"], list)


def test_AC_EOTTR_1_module_exposes_seven_trait_heuristics_table() -> None:
    """``TRAIT_HEURISTICS`` is a tuple of TraitHeuristic with 7 entries."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        TRAIT_HEURISTICS,
        TraitHeuristic,
    )

    assert isinstance(TRAIT_HEURISTICS, tuple)
    assert len(TRAIT_HEURISTICS) == 7
    for h in TRAIT_HEURISTICS:
        assert isinstance(h, TraitHeuristic)


def test_AC_EOTTR_1_module_exposes_cli_entry_point() -> None:
    """``cli_trait_reflection_stop`` is callable with a keyword
    ``workspace_root`` parameter and returns int."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        cli_trait_reflection_stop,
    )

    sig = inspect.signature(cli_trait_reflection_stop)
    assert "workspace_root" in sig.parameters
