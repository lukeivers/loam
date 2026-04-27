"""D10 measurement addendum — Garbage-detector false-positive rate.

Acceptance (brief): measure the Garbage detector's false-positive rate
against a synthetic corpus of known-good Claude outputs.

The research suggests the threshold should yield precision ≥ 0.85
(false-positive rate ≤ 0.15). Below that, raise the threshold or add
an appeal step.

The "synthetic corpus" is built in-file: a set of responses that a
well-functioning Claude would plausibly produce for a range of pOS
prompt types (memory extraction, persona authoring, monitor
stuck-reason, general question-answering, structured JSON outputs).
These are all "good" — the measurement asks: how many does the
garbage pipeline wrongly flag?
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from graceful_degradation.detection import (
    GarbageDetectionRequest,
    GarbagePipeline,
)


# ---- synthetic known-good corpus --------------------------------------

# Each entry: (text, prompt_name, expected_model-or-None, min_chars)
CORPUS: list[tuple[str, str, type[BaseModel] | None, int]] = [
    # 1. Memory-extraction style: a plausible extracted-entity JSON.
    (
        '{"entities": [{"name": "Luke Ivers", "kind": "person"}, '
        '{"name": "pOS", "kind": "project"}]}',
        "memory.extract_entities",
        None,
        1,
    ),
    # 2. Plain-prose answer
    (
        "The capital of France is Paris, a major European cultural "
        "and commercial centre.",
        "general.qa",
        None,
        1,
    ),
    # 3. Short acknowledgment (legitimate)
    (
        "Acknowledged.",
        "ack.simple",
        None,
        1,
    ),
    # 4. Stuck-reason with domain jargon
    (
        "Scope has been paused pending budget extension; the time axis "
        "reached its declared cap before the remaining work could "
        "complete. Recommend extending time_seconds by 600.",
        "monitor.stuck_reason",
        None,
        1,
    ),
    # 5. Persona-authoring draft
    (
        "Persona: Mara (financial-advisor)\n"
        "Domain: personal finances, debt, runway, insurance\n"
        "Reports to: Luke (founder) and Eli (velta CFO) dotted\n"
        "Voice: warm, pragmatic, direct — no jargon.",
        "persona.drafting",
        None,
        1,
    ),
    # 6. Code-like structured output
    (
        "```python\ndef sum(a, b):\n    return a + b\n```",
        "code.generate",
        None,
        1,
    ),
    # 7. Narrative paragraph
    (
        "Graceful degradation is the policy layer that detects Claude-"
        "upstream failure modes and calls pause/resume hooks. It tracks "
        "six failure modes through FSMs.",
        "doc.narrative",
        None,
        1,
    ),
    # 8. Structured decision output
    (
        '{"decision": "proceed", "confidence": 0.82, '
        '"recommendation": "ship with feature flag"}',
        "decision.extract",
        None,
        1,
    ),
    # 9. Instruction-following
    (
        "Step 1: open ~/.pos/degradation-config.yaml.\n"
        "Step 2: set modes.garbage.judge_budget_per_hour to 10.\n"
        "Step 3: restart the orchestrator.",
        "instructions.generate",
        None,
        1,
    ),
    # 10. Polite clarification (legitimate — asks a question, not refusal)
    (
        "Could you clarify whether the scope owner was pre-declared or "
        "assigned by the orchestrator at bind time?",
        "clarify",
        None,
        1,
    ),
    # 11. List
    (
        "The six modes are:\n- Down\n- Overloaded\n- Rate-limited\n"
        "- Garbage\n- Auth-broken\n- Latency-sustained",
        "list.generate",
        None,
        1,
    ),
    # 12. Single-word OK (probe-style)
    (
        "OK",
        "degradation-probe",
        None,
        1,
    ),
    # 13. Longer technical explanation
    (
        "The ClaudeClient adapter passively observes Anthropic SDK "
        "typed exceptions and retry-after headers. It does not issue "
        "active probes during normal operation; probes fire only when "
        "a mode FSM has entered half-open after its dwell expired.",
        "doc.technical",
        None,
        1,
    ),
    # 14. Contrastive answer
    (
        "The research recommends passive detection because active "
        "heartbeats introduce a second failure mode (the heartbeat "
        "itself can fail, producing ambiguous signal).",
        "rationale.explain",
        None,
        1,
    ),
    # 15. Pure JSON (no surrounding text)
    (
        '{"fields": ["goal", "constraints", "budget", '
        '"reversibility_class", "success_criteria", "observers", '
        '"escalation_triggers"]}',
        "schema.describe",
        None,
        1,
    ),
    # 16. Short correct answer
    (
        "Tier 2.",
        "tier.classify",
        None,
        1,
    ),
    # 17. Multi-paragraph prose
    (
        "The first paragraph introduces the topic. The second paragraph "
        "develops the argument with supporting evidence. A concluding "
        "sentence ties them together.\n\n"
        "Key point: the structure exists to make the reasoning "
        "inspectable.",
        "doc.essay",
        None,
        1,
    ),
    # 18. Structured diagnostic
    (
        "Diagnosis:\n- Root cause: retry-after header missed\n"
        "- Instance fix: patch adapter's header extraction\n"
        "- Systemic cause: no test coverage for non-integer values\n"
        "- Structural remedy: add regression test and CI check",
        "diagnostic",
        None,
        1,
    ),
    # 19. Question posed back to user
    (
        "Two options read equally safe here: (a) auto-resume for "
        "garbage mode after 2 probe successes, or (b) require user "
        "confirmation. Which do you prefer?",
        "options.present",
        None,
        1,
    ),
    # 20. Technical specification (matches a pydantic model)
    (
        '{"mode": "rate_limited", "policy": "pause_llm_only", '
        '"dwell_seconds": 60}',
        "spec.emit",
        None,
        1,
    ),
]


# ---- measurement ------------------------------------------------------


async def test_garbage_false_positive_rate_on_known_good_corpus() -> None:
    """Run the corpus through the garbage pipeline; count false
    positives.

    Acceptance: false-positive rate ≤ 0.15 (precision ≥ 0.85). If the
    rate is above that, the test surfaces the measurement as a halt
    signal per the brief.
    """
    pipe = GarbagePipeline(
        judge=None,  # no LLM judge — measure the deterministic tiers.
        judge_budget_per_hour=0,
    )

    total = len(CORPUS)
    false_positives = 0
    flagged: list[str] = []

    for text, prompt, model, min_chars in CORPUS:
        req = GarbageDetectionRequest(
            text=text,
            prompt_name=prompt,
            expected_model=model,
            min_chars=min_chars,
        )
        is_garbage = await pipe.is_garbage(req)
        if is_garbage:
            false_positives += 1
            flagged.append(f"{prompt}: {text[:60]!r}")

    fpr = false_positives / total
    print(
        f"\nGARBAGE FALSE-POSITIVE RATE: {false_positives}/{total} = {fpr:.2%}"
    )
    if flagged:
        print("Flagged (false positives):")
        for f in flagged:
            print(f"  - {f}")
    # Hard gate: rate must be <= 0.15 per research.
    assert fpr <= 0.15, (
        f"False-positive rate {fpr:.2%} exceeds 0.15 threshold. "
        f"Flagged={flagged}"
    )


async def test_garbage_true_positive_rate_on_known_bad_corpus() -> None:
    """Sanity-check the other direction: bad responses should be
    caught. Not formally part of the measurement addendum but needed
    to ensure the detector isn't trivially under-flagging."""
    bad_corpus = [
        ("", "x"),  # empty
        ("   \n\n   ", "x"),  # whitespace
        ("I can't help with that.", "x"),
        ("I cannot help with that request.", "x"),
        ("I'm sorry, but I'm unable to assist with this.", "x"),
    ]
    pipe = GarbagePipeline(judge=None, judge_budget_per_hour=0)
    caught = 0
    for text, prompt in bad_corpus:
        req = GarbageDetectionRequest(text=text, prompt_name=prompt)
        if await pipe.is_garbage(req):
            caught += 1
    # Expect all 5 caught by deterministic tiers.
    assert caught == len(bad_corpus), f"Only caught {caught}/{len(bad_corpus)}"
