# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.CLE.HOOK.4 — generalised ``merge_user_prompt_submit`` with
``extra_inner_hooks=[intent_classifier_entry]`` writes a settings.json
whose ``hooks.UserPromptSubmit[0].hooks`` array contains BOTH the
persona's user-prompt-submit entry AND the intent-classifier entry,
in that order.

Per amendment #144 Scope A (closes AC46.6 deferred multi-contributor
generalisation): the empty-extras default returns byte-identical
single-contributor output (AC46.5 backwards-compat); non-empty extras
append after the base entry so Claude Code's UserPromptSubmit fan-out
invokes the persona's existing contributor BEFORE the intent
classifier.

Composes alongside the existing AC46.5 single-contributor test
(``test_AC46_5_settings_json_carries_user_prompt_submit_hook.py``)
which must still pass — the empty-extras default to the generalised
function returns the same shape.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import merge_user_prompt_submit  # noqa: E402


def _persona_inner_hook(loam_root: Path) -> dict:
    """The persona's user-prompt-submit inner-hook entry (the base
    contributor)."""
    return {
        "type": "command",
        "command": (
            f"{loam_root}/.venv/bin/python "
            "-m loam.primary_persona.cli user-prompt-submit"
        ),
        "async": False,
        "timeout": 5,
    }


def _intent_classifier_inner_hook(loam_root: Path) -> dict:
    """The intent-classifier inner-hook entry (the additional
    contributor amendment #144 introduces)."""
    return {
        "type": "command",
        "command": (
            f"{loam_root}/.venv/bin/python "
            "-m loam.primary_persona.cli intent-classifier"
        ),
        "async": False,
        "timeout": 5,
    }


def _persona_envelope(loam_root: Path) -> dict:
    return {
        "matcher": "",
        "hooks": [_persona_inner_hook(loam_root)],
    }


def test_AC_CLE_HOOK_4_extra_inner_hooks_composes_after_base(
    tmp_path: Path,
) -> None:
    """``extra_inner_hooks=[intent_classifier]`` → the resulting
    settings.json carries both inner hooks in order."""
    settings_path = tmp_path / "settings.json"
    result = merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
        extra_inner_hooks=[_intent_classifier_inner_hook(tmp_path)],
    )
    assert result.wrote is True
    data = json.loads(settings_path.read_text())

    ups = data["hooks"]["UserPromptSubmit"]
    assert len(ups) == 1  # one outer envelope
    inner_hooks = ups[0]["hooks"]
    assert len(inner_hooks) == 2  # two inner contributors

    # Order: persona user-prompt-submit BEFORE intent-classifier.
    assert "primary_persona.cli user-prompt-submit" in inner_hooks[0]["command"]
    assert "primary_persona.cli intent-classifier" in inner_hooks[1]["command"]


def test_AC_CLE_HOOK_4_empty_extras_default_preserves_AC46_5_shape(
    tmp_path: Path,
) -> None:
    """``extra_inner_hooks=None`` (the default) → byte-identical to
    pre-amendment-#144 single-contributor shape. Defends AC46.5
    backwards-compat."""
    settings_path = tmp_path / "settings.json"
    result = merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
    )
    assert result.wrote is True
    data = json.loads(settings_path.read_text())
    inner_hooks = data["hooks"]["UserPromptSubmit"][0]["hooks"]
    assert len(inner_hooks) == 1
    assert "primary_persona.cli user-prompt-submit" in inner_hooks[0]["command"]


def test_AC_CLE_HOOK_4_extras_empty_list_preserves_AC46_5_shape(
    tmp_path: Path,
) -> None:
    """``extra_inner_hooks=[]`` (explicit empty list) is equivalent to
    None — single-contributor shape preserved."""
    settings_path = tmp_path / "settings.json"
    merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
        extra_inner_hooks=[],
    )
    data = json.loads(settings_path.read_text())
    inner_hooks = data["hooks"]["UserPromptSubmit"][0]["hooks"]
    assert len(inner_hooks) == 1


def test_AC_CLE_HOOK_4_re_merge_over_pos_v2_owned_stanza_with_extras(
    tmp_path: Path,
) -> None:
    """Re-merging with extras over a previously-written pos-v2 stanza
    does NOT create a backup — the marker set extended to recognise
    the intent-classifier substring marks the prior stanza as
    pos-v2-owned even when both contributors are present."""
    settings_path = tmp_path / "settings.json"
    # First write — single contributor.
    merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
    )
    # Re-merge — same envelope plus extras.
    result = merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
        extra_inner_hooks=[_intent_classifier_inner_hook(tmp_path)],
    )
    assert result.wrote is True
    assert result.backup_path is None
    assert result.prior_session_start_displaced is False
    data = json.loads(settings_path.read_text())
    assert len(data["hooks"]["UserPromptSubmit"][0]["hooks"]) == 2


def test_AC_CLE_HOOK_4_caller_supplied_new_entry_not_mutated(
    tmp_path: Path,
) -> None:
    """The merger MUST NOT mutate the caller's ``new_entry`` dict —
    the extras composition is done via a defensive copy."""
    settings_path = tmp_path / "settings.json"
    envelope = _persona_envelope(tmp_path)
    original_hook_count = len(envelope["hooks"])
    merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=envelope,
        extra_inner_hooks=[_intent_classifier_inner_hook(tmp_path)],
    )
    # The caller's envelope still has only the base inner hook.
    assert len(envelope["hooks"]) == original_hook_count == 1
