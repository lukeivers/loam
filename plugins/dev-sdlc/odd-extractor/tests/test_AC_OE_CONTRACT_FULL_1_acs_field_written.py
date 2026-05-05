"""AC.OE.CONTRACT-FULL.1 — verify_contract() writes ``acs:`` field
into ``contract-draft.yaml``.

v0.2.1 corrective F1 (smoke evidence at /Users/lukeivers/pos3/workspace
/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-04.md). Producer-
side single-source-of-truth fix: the sidecar at
``<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml`` carries
the full banded-AC list so :class:`loam_pr_safety.contract.read_contract`
can construct a populated :class:`BandedContract` without separately
reading ``raw-acs.yaml``.

Pre-fix: contract-draft.yaml carried only summary metadata
(schema_version + extraction_id + counts + dry_run + created_at).
Post-fix: also carries ``acs: list[dict]`` (each round-trips through
:meth:`BandedAC.model_validate`) + ``unhandled_paths: list[str]``.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    RawACs,
    default_budget,
    init_extraction,
    verify_contract,
)
from loam_odd_extractor.bands import BandedAC


FIXED_TS = "2026-05-04T12:00:00+00:00"


def _banded_ac_dict(
    *,
    ac_id: str,
    text: str,
    confidence: str,
    kind: str,
    citations: list[str],
    repo_sha: str | None = None,
    rationale: str | None = None,
    backing_files: list[str] | None = None,
) -> dict:
    """Build a banded-AC dict shape matching :class:`BandedAC`."""
    return {
        "ac_id": ac_id,
        "text": text,
        "confidence": confidence,
        "evidence": {
            "kind": kind,
            "citations": citations,
            "repo_sha": repo_sha,
            "rationale": rationale,
        },
        "backing_files": backing_files or [],
    }


def test_acs_field_written_into_contract_draft_yaml(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """``contract-draft.yaml`` carries an ``acs`` list whose length
    matches input + each entry round-trips through
    :meth:`BandedAC.model_validate`.
    """
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    raw = RawACs(
        extraction_id=config.repo_id,
        acs=[
            _banded_ac_dict(
                ac_id="AC.SYNTH.1",
                text="User auth validates password length >= 8.",
                confidence="VERIFIED",
                kind="test",
                citations=[
                    "tests/test_auth.py::test_password_length",
                    "app/auth.py:42-58",
                ],
                repo_sha="abc1234567890def",
                backing_files=["app/auth.py", "tests/test_auth.py"],
            ),
            _banded_ac_dict(
                ac_id="AC.SYNTH.2",
                text="Order has-many LineItems with cascade-delete.",
                confidence="PLAUSIBLE",
                kind="source",
                citations=["app/models/order.rb:12-25"],
                backing_files=["app/models/order.rb"],
            ),
            _banded_ac_dict(
                ac_id="AC.SYNTH.3",
                text=(
                    "Payment gateway retries failed charges 3x "
                    "with exponential backoff."
                ),
                confidence="HYPOTHESISED",
                kind="inference",
                citations=[],
                rationale=(
                    "Inferred from a comment in the Stripe "
                    "integration; no application-level retry "
                    "code visible."
                ),
                backing_files=["app/services/payments.rb"],
            ),
        ],
        unhandled_paths=[],
        per_slice_costs={},
        created_at=FIXED_TS,
    )

    draft = verify_contract(config=config, raw=raw, timestamp=FIXED_TS)

    sidecar = draft.sidecar_path
    assert sidecar.exists()
    payload = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)

    # acs field present, list-shaped, length matches input.
    assert "acs" in payload, (
        "contract-draft.yaml must carry top-level `acs` field per "
        "AC.OE.CONTRACT-FULL.1"
    )
    assert isinstance(payload["acs"], list)
    assert len(payload["acs"]) == 3

    # Each entry round-trips through BandedAC.model_validate.
    for ac_dict in payload["acs"]:
        # Will raise pydantic.ValidationError if shape is wrong.
        BandedAC.model_validate(ac_dict)

    # Specific AC IDs preserved (round-trip identity check).
    ac_ids = [ac["ac_id"] for ac in payload["acs"]]
    assert ac_ids == ["AC.SYNTH.1", "AC.SYNTH.2", "AC.SYNTH.3"]

    # Pre-fix summary fields STILL present (regression guard).
    assert payload["schema_version"] == 1
    assert payload["extraction_id"] == config.repo_id
    assert payload["ac_count"] == 3
    assert payload["dry_run"] is True
    assert payload["created_at"] == FIXED_TS


def test_empty_acs_round_trips_as_empty_list(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Cycle 1's zero-AC case still works post-fix — empty ``acs``
    serialises as an empty list (not absent / not None).
    """
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    raw = RawACs(
        extraction_id=config.repo_id,
        acs=[],
        unhandled_paths=[],
        per_slice_costs={},
        created_at=FIXED_TS,
    )
    draft = verify_contract(config=config, raw=raw, timestamp=FIXED_TS)
    payload = yaml.safe_load(
        draft.sidecar_path.read_text(encoding="utf-8")
    )
    assert payload["acs"] == []
    assert payload["ac_count"] == 0
