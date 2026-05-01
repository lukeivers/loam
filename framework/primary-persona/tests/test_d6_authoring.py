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

"""D6 — autonomous authoring pipeline.

Acceptance (brief D6):
- Pipeline runs inside an authoring scope-of-work with declared budget.
- Four steps in order: style-harvest → domain-research →
  contract-synthesis → self-review.
- Max two review iterations; third failure terminates with a failure
  record.
- Newly-authored persona passes D1 validation by construction.
- Cost per authored persona is measurable via per-prompt cost view.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from loam.scope_of_work.runtime import ScopeRuntime
from loam.scope_of_work.spec import (
    Budget,
    ReversibilityClass,
    ScopeSpec,
    SuccessCriterion,
)

from loam.primary_persona.authoring import (
    AuthoringOutcome,
    AuthoringPipeline,
    AuthoringResult,
    LLMResult,
    SelfReviewDimension,
)
from loam.primary_persona.contract import load_contract
from loam.primary_persona.creation_triggers import TriggerSignal
from loam.primary_persona.loader import PersonaLoader

from tests.conftest import VALID_CONTRACT_YAML, write_persona_dir


# ---- helpers ---------------------------------------------------------


def make_synthesis_output(handle: str = "sip", given_name: str = "Sip") -> str:
    contract = {
        "handle": handle,
        "given_name": given_name,
        "contract_version": "1.0.0",
        "responsibilities": {
            "single_point_of_contact": f"Sole contact for {handle} domain.",
            "context_holder": f"Carries {handle} context across sessions.",
            "escalation_judge": f"Decides when to surface {handle} matters.",
        },
        "authority_boundary": {
            "tier_a": "defer",
            "tier_b": "defer",
            "tier_c": "execute",
            "tier_d": "execute",
        },
        "escalation_taxonomy": {"categories": ["external-purchase"]},
        "severity_vocabulary": {
            "labels": ["urgent", "material", "advisory"]
        },
        "home_persona_for": [handle],
        "voice_markers": ["dry", "precise"],
        "is_primary": False,
    }
    prompt = (
        "# Sip — scotch, beer, wine, cannabis, cigars curator\n\n"
        "Sip is dry, precise, and has strong opinions about peat.\n"
    )
    return json.dumps(contract) + "\n---PROMPT---\n" + prompt


def make_review_output(all_pass: bool = True, issues: list[str] | None = None) -> str:
    return json.dumps(
        {
            "voice_distinctiveness": all_pass,
            "scope_fit": all_pass,
            "redundancy": all_pass,
            "contract_correctness": all_pass,
            "issues": issues or [],
        }
    )


@dataclass
class FakeLLM:
    """A fake LLM callable that returns canned responses in order.

    `script` maps prompt_name → LLMResult. Call ordering is enforced
    loosely — each name can be called multiple times (e.g. self-review
    iterations). Calls to an unmapped name raise.
    """

    script: dict[str, list[LLMResult]] = field(default_factory=dict)
    calls: list[tuple[str, str]] = field(default_factory=list)

    def queue(self, prompt_name: str, result: LLMResult) -> None:
        self.script.setdefault(prompt_name, []).append(result)

    async def __call__(self, prompt_name: str, prompt_text: str) -> LLMResult:
        self.calls.append((prompt_name, prompt_text))
        if prompt_name not in self.script or not self.script[prompt_name]:
            # Match self_review_iter_N with just "self_review" script.
            if prompt_name.startswith("self_review_iter_"):
                base = "self_review"
                if base in self.script and self.script[base]:
                    return self.script[base].pop(0)
            raise AssertionError(f"no canned response for {prompt_name!r}")
        return self.script[prompt_name].pop(0)


@pytest.fixture
async def runtime(tmp_path: Path):
    rt = ScopeRuntime(db_path=tmp_path / "scope.db")
    yield rt
    rt.close()


@pytest.fixture
async def authoring_scope(runtime):
    """Create an authoring scope with explicit budget so debits land
    against something."""
    spec = ScopeSpec(
        goal="author new persona",
        constraints=(),
        budget=Budget(tokens=100_000, money_cents=10_000, time_seconds=600),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(SuccessCriterion(criterion_id="c1", description="d"),),
        observers=(),
        escalation_triggers=(),
    )
    await runtime.create(spec, scope_id="authoring-scope")
    await runtime.start("authoring-scope")
    return "authoring-scope"


# ---- happy-path --------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_produces_valid_persona_dir(
    workspace_with_primary: Path, runtime, authoring_scope
):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    existing = loader.load()

    llm = FakeLLM()
    llm.queue("style_harvest", LLMResult(text="punchy, first-principles voice"))
    llm.queue("domain_research", LLMResult(text="- scotch aging\n- beer lautering"))
    llm.queue("contract_synthesis", LLMResult(text=make_synthesis_output()))
    llm.queue("self_review", LLMResult(text=make_review_output(all_pass=True)))

    pipeline = AuthoringPipeline(
        llm=llm,
        runtime=runtime,
        workspace_root=workspace_with_primary,
    )

    result = await pipeline.author(
        trigger_signal=TriggerSignal.explicit_user_mention,
        domain="drinks",
        existing_personas=existing,
        authoring_scope_id=authoring_scope,
    )

    assert result.outcome == AuthoringOutcome.persisted
    assert result.handle == "sip"
    assert result.persona_dir is not None
    assert result.persona_dir.exists()
    # Validates against the D1 contract:
    contract = load_contract(result.persona_dir / "contract.yaml")
    assert contract.handle == "sip"
    # Persisted with pending_introduction + non-addressable by default.
    assert contract.pending_introduction is True
    assert contract.is_addressable is False


# ---- ordering ---------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_runs_four_steps_in_order(
    workspace_with_primary: Path, runtime, authoring_scope
):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    llm = FakeLLM()
    llm.queue("style_harvest", LLMResult(text="voice"))
    llm.queue("domain_research", LLMResult(text="notes"))
    llm.queue("contract_synthesis", LLMResult(text=make_synthesis_output()))
    llm.queue("self_review", LLMResult(text=make_review_output(True)))

    pipeline = AuthoringPipeline(
        llm=llm,
        runtime=runtime,
        workspace_root=workspace_with_primary,
    )
    await pipeline.author(
        trigger_signal=TriggerSignal.explicit_user_mention,
        domain="drinks",
        existing_personas=loader.load(),
        authoring_scope_id=authoring_scope,
    )

    names = [c[0] for c in llm.calls]
    assert names[0] == "style_harvest"
    assert names[1] == "domain_research"
    assert names[2] == "contract_synthesis"
    assert names[3].startswith("self_review")


# ---- retry / rejection -----------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_retries_then_passes(
    workspace_with_primary: Path, runtime, authoring_scope
):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    llm = FakeLLM()
    llm.queue("style_harvest", LLMResult(text="v"))
    llm.queue("domain_research", LLMResult(text="r"))
    # Two synthesis calls (first failed review triggers a retry).
    llm.queue("contract_synthesis", LLMResult(text=make_synthesis_output()))
    llm.queue("contract_synthesis", LLMResult(text=make_synthesis_output()))
    # First review fails, second passes.
    llm.queue(
        "self_review",
        LLMResult(text=make_review_output(all_pass=False, issues=["voice too generic"])),
    )
    llm.queue("self_review", LLMResult(text=make_review_output(all_pass=True)))

    pipeline = AuthoringPipeline(
        llm=llm,
        runtime=runtime,
        workspace_root=workspace_with_primary,
    )

    result = await pipeline.author(
        trigger_signal=TriggerSignal.request_decline,
        domain="drinks",
        existing_personas=loader.load(),
        authoring_scope_id=authoring_scope,
    )
    assert result.outcome == AuthoringOutcome.persisted
    assert result.iterations == 2
    assert result.verdicts[0].passed is False
    assert result.verdicts[1].passed is True


@pytest.mark.asyncio
async def test_pipeline_rejects_after_max_review_iterations(
    workspace_with_primary: Path, runtime, authoring_scope
):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    llm = FakeLLM()
    llm.queue("style_harvest", LLMResult(text="v"))
    llm.queue("domain_research", LLMResult(text="r"))
    # Three synthesis calls (initial + 2 retries).
    for _ in range(3):
        llm.queue("contract_synthesis", LLMResult(text=make_synthesis_output()))
        llm.queue(
            "self_review",
            LLMResult(
                text=make_review_output(all_pass=False, issues=["still generic"])
            ),
        )

    pipeline = AuthoringPipeline(
        llm=llm,
        runtime=runtime,
        workspace_root=workspace_with_primary,
        max_review_iterations=2,
    )

    result = await pipeline.author(
        trigger_signal=TriggerSignal.request_decline,
        domain="drinks",
        existing_personas=loader.load(),
        authoring_scope_id=authoring_scope,
    )
    assert result.outcome == AuthoringOutcome.rejected_after_retries
    assert result.iterations == 3
    assert all(not v.passed for v in result.verdicts)


# ---- cost measurement -------------------------------------------------


@pytest.mark.asyncio
async def test_per_prompt_cost_view_includes_authoring_calls(
    workspace_with_primary: Path, runtime, authoring_scope
):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    llm = FakeLLM()
    llm.queue(
        "style_harvest",
        LLMResult(text="v", input_tokens=20, output_tokens=10, money_cents=1),
    )
    llm.queue(
        "domain_research",
        LLMResult(text="r", input_tokens=30, output_tokens=15, money_cents=2),
    )
    llm.queue(
        "contract_synthesis",
        LLMResult(
            text=make_synthesis_output(),
            input_tokens=100,
            output_tokens=80,
            money_cents=10,
        ),
    )
    llm.queue(
        "self_review",
        LLMResult(
            text=make_review_output(True),
            input_tokens=50,
            output_tokens=20,
            money_cents=3,
        ),
    )

    pipeline = AuthoringPipeline(
        llm=llm,
        runtime=runtime,
        workspace_root=workspace_with_primary,
    )
    await pipeline.author(
        trigger_signal=TriggerSignal.request_decline,
        domain="drinks",
        existing_personas=loader.load(),
        authoring_scope_id=authoring_scope,
    )
    rows = runtime.per_prompt_costs()
    prompt_names = {r["prompt_name"] for r in rows}
    assert "style_harvest" in prompt_names
    assert "domain_research" in prompt_names
    assert "contract_synthesis" in prompt_names
    # self_review_iter_1 or self_review_iter_N
    assert any(p.startswith("self_review") for p in prompt_names)


# ---- invalid contract from LLM --------------------------------------


@pytest.mark.asyncio
async def test_synthesis_output_missing_delimiter_fails(
    workspace_with_primary: Path, runtime, authoring_scope
):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    llm = FakeLLM()
    llm.queue("style_harvest", LLMResult(text="v"))
    llm.queue("domain_research", LLMResult(text="r"))
    llm.queue("contract_synthesis", LLMResult(text="no delimiter here"))

    pipeline = AuthoringPipeline(
        llm=llm, runtime=runtime, workspace_root=workspace_with_primary
    )
    result = await pipeline.author(
        trigger_signal=TriggerSignal.request_decline,
        domain="x",
        existing_personas=loader.load(),
        authoring_scope_id=authoring_scope,
    )
    assert result.outcome == AuthoringOutcome.failed
    assert "delimiter" in (result.reason or "").lower()
