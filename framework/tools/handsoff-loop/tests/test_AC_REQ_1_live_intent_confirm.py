"""AC.REQ.1 — per-request live intent + plain-language confirm (S1).

A vague build-shaped ask yields — before any build — an inferred
end-intent surfaced back in plain language for confirmation, derived
LIVE from THAT ask, provably non-canned:

  * the verbatim ask reaches the live read (the model sees THIS ask,
    not a template about asks in general);
  * materially different asks produce materially different inferences
    (with a content-sensitive double standing in for the model, the
    output provably flows from the input);
  * the module contains NO canned inference: an inference exists ONLY
    when the live read produced one — a failed read raises, it never
    defaults.

The live-model half of this AC (real rewording-equivalence on real
asks) is exercised by the S1 measured-prediction probe and the
env-gated AC.REQ.OA test (BFI_REAL_CLAUDE=1).

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.request_intent import (  # noqa: E402
    RequestUnderstandingUnavailable,
    build_confirm_text,
    understand_request,
)


def _content_sensitive_llm(prompt: str, *, model: str = "sonnet",
                           timeout: int = 0) -> dict:
    """A deterministic double whose output FLOWS FROM the prompt.

    It extracts the quoted ask out of the prompt and derives every
    field from it — so the test proves the module's output is a pure
    function of the live read of THIS ask (no canned path could pass).
    """
    # The ask is interpolated between triple-quote markers.
    ask = prompt.split('"""')[1]
    import json as _json
    return {"result": _json.dumps({
        "inferred_intent": f"You want a tool that handles: {ask}",
        "objective": f"Build exactly what was asked: {ask}",
        "questions": [],
        "form_factor": "cli",
        "form_factor_plain": f"A small command you run for: {ask}",
    })}


def test_inference_derived_from_this_ask_verbatim():
    ask = "clean up the duplicate rows in our customer spreadsheet"
    intent = understand_request(ask, llm_json_fn=_content_sensitive_llm)
    assert ask in intent.inferred_intent
    assert ask in intent.objective
    confirm = build_confirm_text(intent)
    assert ask in confirm
    assert "Is that what you want?" in confirm


def test_materially_different_asks_produce_different_inferences():
    a = understand_request(
        "match payments in the bank file against our invoices",
        llm_json_fn=_content_sensitive_llm)
    b = understand_request(
        "turn our old ledger export into the new bookkeeping format",
        llm_json_fn=_content_sensitive_llm)
    assert a.inferred_intent != b.inferred_intent
    assert a.objective != b.objective
    assert build_confirm_text(a) != build_confirm_text(b)


def test_no_canned_inference_failed_read_raises_never_defaults():
    def _broken_llm(prompt, *, model="sonnet", timeout=0):
        return {"result": "I had a thought but no JSON"}

    with pytest.raises(RequestUnderstandingUnavailable):
        understand_request("build me a thing", llm_json_fn=_broken_llm)

    def _empty_llm(prompt, *, model="sonnet", timeout=0):
        return {"result": '{"inferred_intent": "", "objective": ""}'}

    with pytest.raises(RequestUnderstandingUnavailable):
        understand_request("build me a thing", llm_json_fn=_empty_llm)

    with pytest.raises(RequestUnderstandingUnavailable):
        understand_request("   ", llm_json_fn=_content_sensitive_llm)


def test_dispatch_failure_is_surfaced_not_absorbed():
    def _crashing_llm(prompt, *, model="sonnet", timeout=0):
        raise OSError("claude binary not found")

    with pytest.raises(RequestUnderstandingUnavailable):
        understand_request("build me a thing", llm_json_fn=_crashing_llm)
