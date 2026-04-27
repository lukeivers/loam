"""AC.WSα.3 + AC.WSα.4 + AC.WSα.5 — α.2 classifier + deterministic
primitives + verifier.

Plus the rubber-stamp prevention validator (Hard Constraint #8) and
idempotency property test for the deterministic primitives.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from workspace_sync.merge_primitives import (
    MergeClassDeclined,
    MergeClassification,
    MergeVerification,
    PrimitiveTrace,
    classify_file,
    merge_append_only_list,
    merge_log,
    merge_tracker_table,
    run_primitive,
    verify_merge,
)
from workspace_sync.merge_resolver import ResolverFailure


# ----------------------------------------------------------------------
# Hard Constraint #8 — class_mismatch model_validator
# ----------------------------------------------------------------------


def test_verify_class_mismatch_forces_failure() -> None:
    """Hard Constraint #8: class_mismatch=True with passed=True is a ValidationError."""
    with pytest.raises(ValidationError):
        MergeVerification(
            passed=True,
            class_mismatch=True,
            confidence=0.9,
        )


def test_verify_class_mismatch_with_passed_false_is_valid() -> None:
    v = MergeVerification(
        passed=False,
        class_mismatch=True,
        concerns="not actually an append-only-list",
        confidence=0.8,
    )
    assert v.class_mismatch is True
    assert v.passed is False


# ----------------------------------------------------------------------
# Append-only-list primitive (AC.WSα.4)
# ----------------------------------------------------------------------


def test_append_only_list_canonical_first_then_workspace_extras() -> None:
    canonical = "# Heading\n\n- a\n- b\n"
    workspace = "# Heading\n\n- a\n- b\n- c\n- d\n"
    merged, trace = merge_append_only_list(canonical, workspace)
    # Canonical bullets first, workspace-only bullets appended.
    assert "- a\n" in merged
    assert "- b\n" in merged
    assert "- c\n" in merged
    assert "- d\n" in merged
    assert merged.index("- c") > merged.index("- b")
    assert trace.operation.startswith("append-only-list")
    assert trace.canonical_sha256 != trace.merged_sha256


def test_append_only_list_dedupes_workspace_overlap() -> None:
    canonical = "- a\n- b\n"
    workspace = "- a\n- c\n"
    merged, _trace = merge_append_only_list(canonical, workspace)
    # 'a' should appear once (deduped), 'b' from canonical, 'c' from workspace.
    assert merged.count("- a") == 1
    assert "- b" in merged
    assert "- c" in merged


def test_append_only_list_prefix_mismatch_declines() -> None:
    canonical = "# H1\n\n- a\n"
    workspace = "# H2\n\n- a\n"  # different heading prefix
    with pytest.raises(MergeClassDeclined):
        merge_append_only_list(canonical, workspace)


def test_append_only_list_no_bullets_declines() -> None:
    canonical = "no bullets here\n"
    workspace = "no bullets here\n"
    with pytest.raises(MergeClassDeclined):
        merge_append_only_list(canonical, workspace)


def test_append_only_list_idempotent() -> None:
    """Property: merge(merge(c, w), w) == merge(c, w)."""
    canonical = "- alpha\n- beta\n"
    workspace = "- alpha\n- gamma\n"
    once, _ = merge_append_only_list(canonical, workspace)
    twice, _ = merge_append_only_list(once, workspace)
    assert once == twice


# ----------------------------------------------------------------------
# Log primitive (AC.WSα.4)
# ----------------------------------------------------------------------


def test_log_canonical_first_then_workspace_lines() -> None:
    canonical = "line1\nline2\n"
    workspace = "line1\nline2\nline3\n"
    merged, trace = merge_log(canonical, workspace)
    assert merged == "line1\nline2\nline3\n"
    assert trace.operation == "log:line-union"


def test_log_dedupes_workspace_overlap() -> None:
    canonical = "a\nb\n"
    workspace = "a\nc\n"
    merged, _trace = merge_log(canonical, workspace)
    assert merged == "a\nb\nc\n"


def test_log_idempotent() -> None:
    canonical = "x\ny\n"
    workspace = "x\nz\n"
    once, _ = merge_log(canonical, workspace)
    twice, _ = merge_log(once, workspace)
    assert once == twice


# ----------------------------------------------------------------------
# Tracker-table primitive (AC.WSα.4)
# ----------------------------------------------------------------------


def test_tracker_table_canonical_first_then_workspace_rows() -> None:
    canonical = (
        "| col1 | col2 |\n"
        "| --- | --- |\n"
        "| a | 1 |\n"
        "| b | 2 |\n"
    )
    workspace = (
        "| col1 | col2 |\n"
        "| --- | --- |\n"
        "| a | 1 |\n"
        "| c | 3 |\n"
    )
    merged, trace = merge_tracker_table(canonical, workspace)
    assert "| a | 1 |" in merged
    assert "| b | 2 |" in merged
    assert "| c | 3 |" in merged
    assert trace.operation == "tracker-table:row-union"


def test_tracker_table_header_mismatch_declines() -> None:
    canonical = (
        "| col1 | col2 |\n"
        "| --- | --- |\n"
        "| a | 1 |\n"
    )
    workspace = (
        "| col1 | col3 |\n"  # different header
        "| --- | --- |\n"
        "| a | x |\n"
    )
    with pytest.raises(MergeClassDeclined):
        merge_tracker_table(canonical, workspace)


def test_tracker_table_idempotent() -> None:
    canonical = (
        "| h1 | h2 |\n"
        "| - | - |\n"
        "| a | 1 |\n"
    )
    workspace = (
        "| h1 | h2 |\n"
        "| - | - |\n"
        "| b | 2 |\n"
    )
    once, _ = merge_tracker_table(canonical, workspace)
    twice, _ = merge_tracker_table(once, workspace)
    assert once == twice


# ----------------------------------------------------------------------
# run_primitive dispatch + free-prose / unknown decline (AC.WSα.4)
# ----------------------------------------------------------------------


def test_run_primitive_dispatches_to_correct_primitive() -> None:
    canonical = "- a\n"
    workspace = "- a\n- b\n"
    merged, trace = run_primitive("append-only-list", canonical, workspace)
    assert trace.operation.startswith("append-only-list")


def test_run_primitive_free_prose_declines() -> None:
    with pytest.raises(MergeClassDeclined):
        run_primitive("free-prose", "any", "any")


def test_run_primitive_unknown_declines() -> None:
    with pytest.raises(MergeClassDeclined):
        run_primitive("unknown", "any", "any")


# ----------------------------------------------------------------------
# Classify-call (AC.WSα.3)
# ----------------------------------------------------------------------


class _ClassifyStub:
    def __init__(self, response: MergeClassification, tokens: int = 50) -> None:
        self.response = response
        self.tokens = tokens
        self.last_prompt: str | None = None

    def invoke(self, prompt, response_model):
        self.last_prompt = prompt
        return self.response, self.tokens


def test_classify_file_returns_typed_classification() -> None:
    """AC.WSα.3: classify_file returns Pydantic-validated MergeClassification."""
    canonical = "- a\n- b\n"
    workspace = "- a\n- b\n- c\n"
    expected = MergeClassification(
        merge_class="append-only-list", confidence=0.95, reasoning="bullets"
    )
    stub = _ClassifyStub(expected)
    out, tokens = classify_file(
        llm_client=stub,
        path="x.md",
        canonical_text=canonical,
        workspace_text=workspace,
    )
    assert out.merge_class == "append-only-list"
    assert out.confidence == 0.95
    assert tokens == 50


def test_classify_file_truncates_long_inputs() -> None:
    """D-2 LOCKED: classify includes 50-first + 10-last lines per side."""
    canonical = "\n".join(f"line {i}" for i in range(200)) + "\n"
    workspace = "\n".join(f"line {i}" for i in range(200)) + "\n"
    stub = _ClassifyStub(
        MergeClassification(merge_class="log", confidence=0.7, reasoning="r")
    )
    classify_file(
        llm_client=stub,
        path="x.log",
        canonical_text=canonical,
        workspace_text=workspace,
    )
    prompt = stub.last_prompt or ""
    # The truncation marker MUST appear (the file is way longer than 60 lines).
    assert "<middle truncated" in prompt


# ----------------------------------------------------------------------
# Verify-call (AC.WSα.5 + Hard Constraint #8)
# ----------------------------------------------------------------------


class _VerifyStub:
    def __init__(self, response: MergeVerification, tokens: int = 100) -> None:
        self.response = response
        self.tokens = tokens
        self.last_prompt: str | None = None

    def invoke(self, prompt, response_model):
        self.last_prompt = prompt
        return self.response, self.tokens


def test_verify_merge_returns_typed_verification() -> None:
    """AC.WSα.5: verify_merge returns MergeVerification with passed/concerns/confidence."""
    canonical = "- a\n"
    workspace = "- a\n- b\n"
    candidate = "- a\n- b\n"
    expected = MergeVerification(
        passed=True, class_mismatch=False, concerns=None, confidence=0.9
    )
    stub = _VerifyStub(expected)
    classification = MergeClassification(
        merge_class="append-only-list", confidence=0.9, reasoning="r"
    )
    trace = PrimitiveTrace(
        operation="append-only-list:concat-dedup",
        canonical_sha256="a" * 64,
        workspace_sha256="b" * 64,
        merged_sha256="c" * 64,
    )
    out, tokens = verify_merge(
        llm_client=stub,
        path="x.md",
        canonical_text=canonical,
        workspace_text=workspace,
        candidate_merged_text=candidate,
        classification=classification,
        primitive_trace=trace,
    )
    assert out.passed is True
    assert tokens == 100


def test_verify_merge_prompt_includes_named_class() -> None:
    """Hard Constraint #8: the verifier's prompt MUST name the class as input."""
    expected = MergeVerification(
        passed=False, class_mismatch=False, concerns="x", confidence=0.5
    )
    stub = _VerifyStub(expected)
    classification = MergeClassification(
        merge_class="tracker-table", confidence=0.9, reasoning="r"
    )
    trace = PrimitiveTrace(
        operation="tracker-table:row-union",
        canonical_sha256="a" * 64,
        workspace_sha256="b" * 64,
        merged_sha256="c" * 64,
    )
    verify_merge(
        llm_client=stub,
        path="x.md",
        canonical_text="| a | 1 |",
        workspace_text="| a | 1 |",
        candidate_merged_text="| a | 1 |",
        classification=classification,
        primitive_trace=trace,
    )
    prompt = stub.last_prompt or ""
    assert "tracker-table" in prompt
    # Hard Constraint #8: the prompt MUST ask "is this actually
    # structurally a {class}?" as the first verification step.
    assert (
        "Are they actually structurally" in prompt
        or "actually structurally" in prompt
    )
    # And the class_mismatch concept MUST appear so the LLM knows
    # the failure mode.
    assert "class_mismatch" in prompt
