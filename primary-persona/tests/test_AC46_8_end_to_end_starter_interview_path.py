"""AC46.8 — End-to-end starter interview path.

Outcome: a test scenario where:
  (i) the contract has ``is_starter=True``
  (ii) the SessionStart CLI is invoked
  (iii) its stdout is parsed for the question list
  (iv) a synthetic transcript is constructed with non-empty answers
       for every required question
  (v) ``persist_elicitation_transcript`` is called
  (vi) the contract's ``is_starter`` is now False AND the answer
       fields appear on the contract.

The framework path closes — no persona-prompt customisation needed.
The persona, on a future SessionStart, would read the additionalContext
written by this amendment and (with appropriate prompting) execute the
full elicitation; this test substitutes the persona's "ask + capture"
with a deterministic transcript-construction step.
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

from src.contract import load_contract
from src.loader import LoadedPersona, PersonaLoader
from src.onboarding import (
    ONBOARDING_QUESTIONS,
    persist_elicitation_transcript,
)
from src.session_start_emitter import emit_session_start_context


def _seed_starter_workspace(root: Path) -> Path:
    """Workspace with a starter-flagged primary persona contract.
    Returns the contract path."""
    (root / "CLAUDE.md").write_text(
        "## Session-start discipline\n- `docs/odd-methodology.md`\n"
    )
    (root / "docs").mkdir()
    (root / "docs" / "odd-methodology.md").write_text("x")

    personas = root / "personas"
    personas.mkdir()
    primary = personas / "primary"
    primary.mkdir()
    contract_path = primary / "contract.yaml"
    contract_path.write_text(
        "handle: primary\n"
        "given_name: Example\n"
        "contract_version: 1.0.0\n"
        "responsibilities:\n"
        "  single_point_of_contact: Coordinator.\n"
        "  context_holder: Holds context.\n"
        "  escalation_judge: Decides surfacing.\n"
        "authority_boundary:\n"
        "  tier_a: defer\n"
        "  tier_b: defer\n"
        "  tier_c: execute\n"
        "  tier_d: execute\n"
        "escalation_taxonomy:\n"
        "  categories: [x]\n"
        "severity_vocabulary:\n"
        "  labels: [a, b]\n"
        "is_primary: true\n"
        "is_starter: true\n"
        "dev_intent: unanswered\n"
    )
    (primary / "prompt.md").write_text("# example\n")
    return contract_path


def _parse_question_ids_from_payload(payload: str) -> list[str]:
    """Extract the question ids the body lists. Body shape includes
    ``- id=<id> required=<bool> prompt=<text>`` lines."""
    pattern = re.compile(r"id=(\w[\w-]*)")
    seen: list[str] = []
    for m in pattern.finditer(payload):
        ident = m.group(1)
        if ident not in seen:
            seen.append(ident)
    return seen


def test_AC46_8_end_to_end_starter_interview_path(tmp_path: Path) -> None:
    """Full E2E: starter contract → SessionStart payload → parse
    questions → write transcript → persist → contract reflects
    answers + is_starter flips False."""
    contract_path = _seed_starter_workspace(tmp_path)

    # (i) + (ii): emit the SessionStart additionalContext payload.
    payload = emit_session_start_context(tmp_path)
    assert payload, "starter workspace produced empty SessionStart payload"

    # (iii): parse the question ids out of the payload.
    parsed_ids = _parse_question_ids_from_payload(payload)
    canonical_ids = [q.id for q in ONBOARDING_QUESTIONS]
    for cid in canonical_ids:
        assert cid in parsed_ids, (
            f"canonical question id {cid!r} missing from emitted payload; "
            f"parsed={parsed_ids}"
        )

    # (iv): construct a synthetic transcript with non-empty answers.
    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris",
        "domain_focus": "personal-life operations and workspace continuity",
        "dev_intent": "no",
    }

    # Load the persona via the canonical loader so the write-back has
    # a real LoadedPersona to mutate (mirrors the production path).
    loader = PersonaLoader(tmp_path, enforce_no_personas_in_core=False)
    loaded = loader.primary()

    # (v): persist the transcript.
    new_contract = persist_elicitation_transcript(
        loaded_persona=loaded,
        transcript=transcript,
        contract_path=contract_path,
    )

    # (vi): assert the contract reflects the answers + is_starter is
    # False.
    assert new_contract.is_starter is False
    assert new_contract.given_name == "Iris"
    assert (
        new_contract.responsibilities.single_point_of_contact
        == "personal-life operations and workspace continuity"
    )
    assert new_contract.dev_intent == "no"

    # Disk reflects the same shape (round-trip).
    on_disk = load_contract(contract_path)
    assert on_disk.is_starter is False
    assert on_disk.given_name == "Iris"


def test_AC46_8_questions_extractable_from_payload_post_widening(
    tmp_path: Path,
) -> None:
    """The question-id parsing surface AC46.8 relies on is exposed by
    the AC46.7 body widening; this test isolates the parse-back
    contract so a future body-format change re-validates the contract."""
    _seed_starter_workspace(tmp_path)
    payload = emit_session_start_context(tmp_path)
    parsed = _parse_question_ids_from_payload(payload)
    # Every canonical question id is present in parsed.
    for q in ONBOARDING_QUESTIONS:
        assert q.id in parsed
