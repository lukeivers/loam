"""AC.COMPINT.2 — Missing-objective LLM-as-judge.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.2:

- Stub Anthropic with canned responses (no real API calls).
- Cap-of-5 enforced on 8-candidate response (post-validation truncation
  preserving priority + input order).
- ValidationError on malformed candidates surfaced as :class:`StageError`.
- Prompt structure verified: lean grounding §self-checks injected into
  system prompt; existing-objectives + heuristic priors + multi-source
  bundle present in user prompt.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from loam_odd_extractor import (
    ConfidenceBand,
    FlaggedMissing,
    HeuristicPrior,
    MAX_FLAGGED_CANDIDATES,
    MultiSourceBundle,
    Objective,
    ObjectiveEvidence,
    StageError,
    flag_missing_objectives,
)


# ---- Stub Anthropic client (mirrors test_AC_OBJX_5) ----------------


class _StubBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _StubResponse:
    def __init__(self, text: str, input_tokens: int = 80, output_tokens: int = 60):
        self.content = [_StubBlock(text)]
        self.usage = type(
            "Usage",
            (),
            {"input_tokens": input_tokens, "output_tokens": output_tokens},
        )()


class StubMessages:
    def __init__(self, response_json: dict[str, Any], capture_calls: list | None = None):
        self._response_json = response_json
        self.capture_calls = (
            capture_calls if capture_calls is not None else []
        )

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self.capture_calls.append(kwargs)
        return _StubResponse(json.dumps(self._response_json))


class StubClient:
    def __init__(self, response_json: dict[str, Any]):
        self.capture_calls: list[dict[str, Any]] = []
        self.messages = StubMessages(response_json, self.capture_calls)


def _bundle() -> MultiSourceBundle:
    return MultiSourceBundle(
        repo_id="test-repo",
        repo_path="/tmp/test-repo",
        repo_sha="abc1234",
        readme_text="# DisputeApp\n\nFile refunds at scale; SOC-2 audit trail.",
        readme_truncated=False,
        design_docs=[],
        test_assertions=[],
        user_survey={
            "source_path": "~/loam-onboarding-survey.md",
            "parsed": {"production_use": "Yes"},
            "raw_text": "Q4 production_use: Yes\nQ5 SOC-2 audit-trail",
        },
        code_patterns=[],
        total_token_estimate=200,
    )


def _objs() -> list[Objective]:
    return [
        Objective(
            objective_id="O.dispute-flow.1",
            text="Operators file refund disputes against merchant portals at scale.",
            confidence=ConfidenceBand.PLAUSIBLE,
            domain="dispute-flow",
            evidence=ObjectiveEvidence(
                readme_excerpts=["File refunds at scale"],
            ),
        )
    ]


def _good_response_one() -> dict[str, Any]:
    return {
        "flagged": [
            {
                "candidate_text": (
                    "Audit trail identifies who initiated each dispute "
                    "filing for SOC-2 CC6 compliance."
                ),
                "reasoning": (
                    "Survey mentions SOC-2 + production-stake; no "
                    "audit-domain objective in the extracted set."
                ),
                "evidence_refs": ["survey:Q5"],
                "priority": "high",
                "domain": "audit",
            }
        ]
    }


def test_llm_judge_parses_canned_response_into_typed_rows() -> None:
    client = StubClient(_good_response_one())
    rows = flag_missing_objectives(
        _objs(),
        multi_source_bundle=_bundle(),
        anthropic_client=client,
        priors=[],
    )
    assert len(rows) == 1
    assert isinstance(rows[0], FlaggedMissing)
    assert rows[0].priority == "high"
    assert rows[0].domain == "audit"


def test_llm_judge_caps_at_five_candidates() -> None:
    """8 returned → cap-of-5 enforced; high-priority preserved first."""
    eight = {
        "flagged": [
            {
                "candidate_text": f"Candidate objective number {i} delivers value to operators.",
                "reasoning": f"Reasoning for candidate {i}",
                "evidence_refs": [],
                "priority": "low" if i % 2 == 0 else "high",
                "domain": "dispute-flow",
            }
            for i in range(8)
        ]
    }
    client = StubClient(eight)
    rows = flag_missing_objectives(
        _objs(),
        multi_source_bundle=_bundle(),
        anthropic_client=client,
        priors=[],
    )
    assert len(rows) == MAX_FLAGGED_CANDIDATES == 5
    # All four high-priority entries (i=1,3,5,7) should be in the kept set.
    high_count = sum(1 for r in rows if r.priority == "high")
    assert high_count == 4


def test_llm_judge_raises_on_malformed_json() -> None:
    class GarbageClient:
        class _M:
            @staticmethod
            def create(**kwargs):
                return _StubResponse("this is not json {{{")
        messages = _M()

    with pytest.raises(StageError) as exc:
        flag_missing_objectives(
            _objs(),
            multi_source_bundle=_bundle(),
            anthropic_client=GarbageClient(),
            priors=[],
        )
    assert "JSON" in str(exc.value)


def test_llm_judge_raises_stage_error_on_invalid_candidate() -> None:
    bad = {
        "flagged": [
            {
                "candidate_text": "x",  # < 20 chars → ValidationError
                "reasoning": "too short",
                "priority": "high",
                "evidence_refs": [],
                "domain": "audit",
            }
        ]
    }
    client = StubClient(bad)
    with pytest.raises(StageError) as exc:
        flag_missing_objectives(
            _objs(),
            multi_source_bundle=_bundle(),
            anthropic_client=client,
            priors=[],
        )
    assert "ValidationError" in str(exc.value)


def test_llm_judge_raises_when_no_client_provided() -> None:
    with pytest.raises(StageError) as exc:
        flag_missing_objectives(
            _objs(),
            multi_source_bundle=_bundle(),
            anthropic_client=None,
            priors=[],
        )
    assert "anthropic_client" in str(exc.value)


def test_llm_judge_system_prompt_carries_self_checks() -> None:
    client = StubClient(_good_response_one())
    flag_missing_objectives(
        _objs(),
        multi_source_bundle=_bundle(),
        anthropic_client=client,
        priors=[],
    )
    call = client.capture_calls[0]
    sys_prompt = call.get("system")
    if isinstance(sys_prompt, list):
        text = " ".join(
            block.get("text", "") for block in sys_prompt
            if isinstance(block, dict)
        )
    else:
        text = str(sys_prompt)
    assert "Outcome-or-fact" in text
    assert "Implementation-swap" in text
    assert "CAP" in text or "AT MOST 5" in text


def test_llm_judge_user_prompt_carries_priors_and_existing() -> None:
    client = StubClient(_good_response_one())
    priors = [
        HeuristicPrior(
            pattern_id="production-stake-no-security-objective",
            prior_text="Repo is production-stake but lacks security objective.",
            priority="high",
            evidence_refs=["survey:Q4"],
        )
    ]
    flag_missing_objectives(
        _objs(),
        multi_source_bundle=_bundle(),
        anthropic_client=client,
        priors=priors,
    )
    call = client.capture_calls[0]
    user_msg = call["messages"][0]["content"]
    assert "EXISTING OBJECTIVES" in user_msg
    assert "HEURISTIC PRIORS" in user_msg
    assert "production-stake-no-security-objective" in user_msg
    assert "DisputeApp" in user_msg


def test_llm_judge_handles_code_fenced_response() -> None:
    fenced = "```json\n" + json.dumps(_good_response_one()) + "\n```"

    class FencedClient:
        class _M:
            @staticmethod
            def create(**kwargs):
                return _StubResponse(fenced)
        messages = _M()

    rows = flag_missing_objectives(
        _objs(),
        multi_source_bundle=_bundle(),
        anthropic_client=FencedClient(),
        priors=[],
    )
    assert len(rows) == 1


def test_llm_judge_default_priors_runs_heuristic_pre_pass() -> None:
    """When ``priors`` is None, heuristic_priors is auto-invoked.

    The bundle here triggers heuristic-1 (production_use=Yes; no
    security objective). The user prompt should carry the
    pattern_id from the heuristic.
    """
    client = StubClient(_good_response_one())
    flag_missing_objectives(
        _objs(),
        multi_source_bundle=_bundle(),
        anthropic_client=client,
        # no priors arg → auto-invoke heuristic_priors
    )
    call = client.capture_calls[0]
    user_msg = call["messages"][0]["content"]
    assert "production-stake-no-security-objective" in user_msg
