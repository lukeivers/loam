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

"""AC.RVL.9 — a seeded situational rule fires on an ``authoring-plan``
situation directing floor+budget over count caps, provenance-anchored to
this artifact; the ``authoring-plan`` trigger detects a plan-authoring turn
and stays SILENT on ambiguous input (the under-fire bias, AC.RSR.3 parity).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import rules_store as rs
from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    detect_situation,
    retrieve,
)


def _cfg(tmp_path: Path, store: Path) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=None,
        claude_homes=(),
        objectives_home=tmp_path / "no-obj",
        rules_memory_dir=store,
    )


def test_AC_RVL_9_trigger_fires_on_plan_authoring_turns() -> None:
    for prompt in (
        "authoring a plan-doc for the recall reshape cycle",
        "let me write the sub-plan before any code",
        "time to author the plan for the next amendment",
        "this is a plan-doc; run the plan-before-code gate",
    ):
        assert "authoring-plan" in detect_situation(prompt), (
            f"the plan-authoring turn must fire the trigger; prompt={prompt!r}"
        )


def test_AC_RVL_9_trigger_silent_on_ambiguous_input() -> None:
    for prompt in (
        "let me plan my day around the errands",
        "what is the plan for dinner tonight",
        "continue the build",
        "",
    ):
        assert "authoring-plan" not in detect_situation(prompt), (
            f"an ambiguous turn must NOT fire the trigger (under-fire bias); "
            f"prompt={prompt!r}"
        )


def test_AC_RVL_9_seeded_rule_is_provenance_anchored() -> None:
    specs = [s for s in rs.SEEDED_RULES if "authoring-plan" in s["situation"]]
    assert len(specs) == 1, "exactly one seeded authoring-plan rule"
    spec = specs[0]
    assert spec["provenance"], "the seeded rule must carry >=1 provenance pointer"
    # Provenance anchored to this artifact's decision record + audit.
    prov = " ".join(spec["provenance"])
    assert "2026-07-08" in prov
    assert "cap-bias" in spec["directive"].lower() or "count cap" in spec["directive"].lower()


def test_AC_RVL_9_seeded_rule_surfaces_on_a_plan_authoring_turn(
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    store.mkdir()
    rs.seed_starter_rules(store)
    block = retrieve(
        prompt="authoring a plan-doc for the next amendment cycle",
        config=_cfg(tmp_path, store),
    )
    assert "numeric limit" in block.lower(), (
        f"the seeded cap-bias directive must surface on a plan-authoring turn; "
        f"got {block!r}"
    )
    assert "floor" in block.lower() and "budget" in block.lower()
