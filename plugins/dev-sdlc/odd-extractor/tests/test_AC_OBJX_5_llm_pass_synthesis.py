"""AC.OBJX.5 — LLM-pass synthesis.

- Stub Anthropic client with canned responses (no real API calls).
- Correct array parsing into typed Objective / Constraint /
  Capability rows.
- ValidationError on malformed LLM rows surfaced as StageError.
- Prompt structure check (system contains §self-checks; user
  contains README + design docs).
- repo_sha threading into VERIFIED evidence.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from loam_odd_extractor import (
    MultiSourceBundle,
    StageError,
    SynthesisResult,
    synthesize_objectives,
)


# ---- Stub Anthropic client -----------------------------------------


class _StubBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _StubResponse:
    def __init__(self, text: str, input_tokens: int = 100, output_tokens: int = 50):
        self.content = [_StubBlock(text)]
        self.usage = type(
            "Usage", (), {"input_tokens": input_tokens, "output_tokens": output_tokens}
        )()


class StubMessages:
    def __init__(self, response_json: dict[str, Any], capture_calls: list | None = None):
        self._response_json = response_json
        self.capture_calls = capture_calls if capture_calls is not None else []

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self.capture_calls.append(kwargs)
        return _StubResponse(
            json.dumps(self._response_json),
            input_tokens=kwargs.get("_input_tokens", 100),
            output_tokens=kwargs.get("_output_tokens", 50),
        )


class StubAnthropicClient:
    def __init__(self, response_json: dict[str, Any]):
        self.capture_calls: list[dict[str, Any]] = []
        self.messages = StubMessages(response_json, self.capture_calls)


# ---- Fixtures ------------------------------------------------------


def _bundle() -> MultiSourceBundle:
    return MultiSourceBundle(
        repo_id="test-repo",
        repo_path="/tmp/test-repo",
        repo_sha="abc1234",
        readme_text="# DisputeApp\n\nFile refunds at scale.",
        readme_truncated=False,
        design_docs=[
            {
                "path": "docs/architecture.md",
                "heading": "Architecture",
                "text": "# Architecture\n\nServerless dispute pipeline.",
                "truncated": "false",
            }
        ],
        test_assertions=[
            {
                "ac_id": "AC.JSTS.1",
                "text": "files disputes",
                "first_citation": "tests/x.spec.ts::it files",
                "all_citations": "tests/x.spec.ts::it files",
            }
        ],
        user_survey=None,
        code_patterns=[],
        total_token_estimate=500,
    )


def _good_response() -> dict[str, Any]:
    return {
        "objectives": [
            {
                "objective_id": "O.dispute-flow.1",
                "text": (
                    "Operators file refund disputes against merchant "
                    "portals at scale, replacing manual portal clickwork."
                ),
                "confidence": "VERIFIED",
                "domain": "dispute-flow",
                "evidence": {
                    "test_name_refs": ["tests/x.spec.ts::it files"],
                    "readme_excerpts": ["File refunds at scale"],
                    "design_doc_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": "abc1234",
                    "rationale": None,
                },
            }
        ],
        "constraints": [
            {
                "constraint_id": "K.compliance.1",
                "text": "audit trail covers dispute filings",
                "bounds_kind": "compliance",
                "evidence": {
                    "readme_excerpts": ["audit"],
                    "design_doc_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            }
        ],
        "capabilities": [
            {
                "capability_id": "C.csv-upload.1",
                "text": "CSV upload + validation pipeline",
                "serves": ["O.dispute-flow.1"],
                "evidence": {
                    "readme_excerpts": ["csv upload"],
                    "design_doc_refs": [],
                    "test_name_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            }
        ],
    }


# ---- Tests ---------------------------------------------------------


def test_synthesis_parses_canned_response_into_typed_rows() -> None:
    client = StubAnthropicClient(_good_response())
    result = synthesize_objectives(
        _bundle(),
        extraction_id="test-repo",
        repo_sha="abc1234",
        anthropic_client=client,
    )
    assert isinstance(result, SynthesisResult)
    assert len(result.objectives) == 1
    assert result.objectives[0].objective_id == "O.dispute-flow.1"
    assert len(result.constraints) == 1
    assert len(result.capabilities) == 1
    assert result.token_count_input == 100
    assert result.token_count_output == 50


def test_synthesis_threads_repo_sha_into_verified_evidence() -> None:
    """When VERIFIED objective lacks repo_sha, synthesizer threads it."""
    payload = _good_response()
    payload["objectives"][0]["evidence"]["repo_sha"] = None
    client = StubAnthropicClient(payload)
    result = synthesize_objectives(
        _bundle(),
        extraction_id="test-repo",
        repo_sha="def5678",
        anthropic_client=client,
    )
    assert result.objectives[0].evidence.repo_sha == "def5678"


def test_synthesis_raises_on_malformed_json() -> None:
    class GarbageStub:
        class _M:
            @staticmethod
            def create(**kwargs):
                return _StubResponse("this is not json {{{")
        messages = _M()

    with pytest.raises(StageError) as exc:
        synthesize_objectives(
            _bundle(),
            extraction_id="test-repo",
            anthropic_client=GarbageStub(),
        )
    assert "JSON" in str(exc.value)


def test_synthesis_raises_stage_error_on_invalid_objective() -> None:
    bad = _good_response()
    # Make the objective text too short (< 20 chars) — Pydantic rejects.
    bad["objectives"][0]["text"] = "x"
    client = StubAnthropicClient(bad)
    with pytest.raises(StageError) as exc:
        synthesize_objectives(
            _bundle(),
            extraction_id="test-repo",
            anthropic_client=client,
        )
    assert "ValidationError" in str(exc.value)


def test_synthesis_raises_when_no_client_provided() -> None:
    with pytest.raises(StageError) as exc:
        synthesize_objectives(
            _bundle(),
            extraction_id="test-repo",
            anthropic_client=None,
        )
    assert "anthropic_client" in str(exc.value)


def test_synthesis_passes_lean_grounding_into_system_prompt() -> None:
    client = StubAnthropicClient(_good_response())
    synthesize_objectives(
        _bundle(),
        extraction_id="test-repo",
        anthropic_client=client,
    )
    call = client.capture_calls[0]
    system_prompt = call.get("system")
    if isinstance(system_prompt, list):
        # Cache-friendly shape: [{"type":"text","text":...}]
        text = " ".join(
            block.get("text", "") for block in system_prompt
            if isinstance(block, dict)
        )
    else:
        text = str(system_prompt)
    assert "Outcome-or-fact" in text
    assert "Implementation-swap" in text
    assert "VERIFIED" in text


def test_synthesis_user_prompt_includes_readme_and_docs() -> None:
    client = StubAnthropicClient(_good_response())
    synthesize_objectives(
        _bundle(),
        extraction_id="test-repo",
        anthropic_client=client,
    )
    call = client.capture_calls[0]
    user_msg = call["messages"][0]["content"]
    assert "DisputeApp" in user_msg
    assert "Architecture" in user_msg


def test_synthesis_handles_code_fenced_response() -> None:
    """Tolerates ``` fences around JSON despite system instruction."""
    fenced_text = "```json\n" + json.dumps(_good_response()) + "\n```"

    class FencedStub:
        capture_calls: list = []

        class _M:
            @staticmethod
            def create(**kwargs):
                FencedStub.capture_calls.append(kwargs)
                return _StubResponse(fenced_text)
        messages = _M()

    result = synthesize_objectives(
        _bundle(),
        extraction_id="test-repo",
        anthropic_client=FencedStub(),
    )
    assert len(result.objectives) == 1
