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

"""AC.O.4 — ``persist_grounding`` regenerates prompt.md and
``.claude/agents/<handle>.md`` alongside contract.yaml.

In addition to writing ``contract.yaml``, ``persist_grounding``
writes:

  - ``<workspace>/personas/<handle>/prompt.md`` with the framework
    template's body and the two substitution tokens replaced;
  - ``<workspace>/.claude/agents/<handle>.md`` rendered via
    ``to_agent_md(contract, prompt_text=<rendered prompt body>)``.

After the call: opening ``prompt.md`` finds the user's preferred
names interpolated; opening ``.claude/agents/<handle>.md`` finds an
identity-anchor block naming the captured ``given_name``. A second
``persist_grounding`` call with a different ``persona_given_name``
regenerates both files with the new name (no caching shadows the
change).

Plan: docs/plans/primary-persona-conversational-onboarding-and-default-archetype.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loam.primary_persona.contract import PersonaContract
from loam.primary_persona.onboarding import GroundingCapture, persist_grounding


def _starter_contract_dict() -> dict:
    return {
        "handle": "iris",
        "given_name": "Iris",
        "contract_version": "1.0.0",
        "responsibilities": {
            "single_point_of_contact": "Default starter SPOC.",
            "context_holder": "Carries ongoing context.",
            "escalation_judge": "Decides surfacing.",
        },
        "authority_boundary": {
            "tier_a": "defer",
            "tier_b": "defer",
            "tier_c": "execute",
            "tier_d": "defer",
        },
        "escalation_taxonomy": {"categories": ["x"]},
        "severity_vocabulary": {"labels": ["a", "b"]},
        "is_starter": True,
    }


@dataclass
class _FakeLoadedPersona:
    contract: PersonaContract
    directory: Path | None = None


def _seed(tmp_path: Path) -> tuple[_FakeLoadedPersona, Path]:  # noqa: D401
    # D-migration D.2 (amendment #63): personas live under
    # <ws>/workspace/personas/ post-D.2.
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona_dir = tmp_path / "workspace" / "personas" / "iris"
    persona_dir.mkdir(parents=True)
    contract_path = persona_dir / "contract.yaml"
    contract_path.write_text(contract.to_yaml())
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    return _FakeLoadedPersona(contract=contract, directory=persona_dir), contract_path


def _grounding(*, user_name: str = "Luke", given_name: str = "Mara") -> GroundingCapture:
    return GroundingCapture(
        user_preferred_name=user_name,
        persona_given_name=given_name,
        single_point_of_contact="Coordinator for daily ops.",
        context_holder="Holds cross-session context.",
        escalation_judge="Routes irreversible moves.",
        dev_intent="no",
        captured_summary=("Heard about the day-walkthrough.",),
    )


def test_AC_O_4_writes_prompt_md_with_substituted_names(tmp_path: Path):
    """After persist_grounding the workspace prompt.md contains
    the user's preferred names and no leftover token literal."""
    persona, contract_path = _seed(tmp_path)
    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(user_name="Luke", given_name="Mara"),
        contract_path=contract_path,
    )

    prompt_path = contract_path.parent / "prompt.md"
    assert prompt_path.is_file()
    body = prompt_path.read_text()
    assert "Luke" in body
    assert "Mara" in body
    assert "{user_preferred_name}" not in body
    assert "{persona_given_name}" not in body


def test_AC_O_4_writes_agent_file_with_captured_given_name(tmp_path: Path):
    """The .claude/agents/<handle>.md file is written and contains
    the captured given_name (in the identity-anchor block)."""
    persona, contract_path = _seed(tmp_path)
    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(user_name="Luke", given_name="Mara"),
        contract_path=contract_path,
    )

    agent_path = tmp_path / ".claude" / "agents" / "iris.md"
    assert agent_path.is_file()
    body = agent_path.read_text()
    assert "Mara" in body
    # The identity-anchor block uses the captured given_name + the
    # contract's handle.
    assert "iris" in body  # handle reference


def test_AC_O_4_second_call_regenerates_with_new_name(tmp_path: Path):
    """A second persist_grounding with a different persona_given_name
    regenerates both files; the new name is present, the old name
    is gone (no caching shadow)."""
    persona, contract_path = _seed(tmp_path)
    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(user_name="Luke", given_name="Mara"),
        contract_path=contract_path,
    )

    # Refresh the loaded persona's contract reference (mirrors the
    # production path where the loader is re-invoked between calls).
    from loam.primary_persona.contract import load_contract

    persona.contract = load_contract(contract_path)

    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(user_name="Luke", given_name="Aria"),
        contract_path=contract_path,
    )

    prompt_body = (contract_path.parent / "prompt.md").read_text()
    agent_body = (tmp_path / ".claude" / "agents" / "iris.md").read_text()
    assert "Aria" in prompt_body
    assert "Aria" in agent_body
    assert "Mara" not in prompt_body
    assert "Mara" not in agent_body


def test_AC_O_4_creates_claude_agents_dir_if_absent(tmp_path: Path):
    """If the workspace's .claude/agents/ directory does not
    pre-exist, persist_grounding creates it (mkdir parents=True)."""
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona_dir = tmp_path / "workspace" / "personas" / "iris"
    persona_dir.mkdir(parents=True)
    contract_path = persona_dir / "contract.yaml"
    contract_path.write_text(contract.to_yaml())
    # No .claude/ pre-created.
    persona = _FakeLoadedPersona(contract=contract, directory=persona_dir)

    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(),
        contract_path=contract_path,
    )

    assert (tmp_path / ".claude" / "agents" / "iris.md").is_file()
