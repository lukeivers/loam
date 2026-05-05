"""AC.OE.CONTRACT-FULL.3 — Producer-to-consumer round-trip:
extractor-written ``contract-draft.yaml`` parses cleanly through
pr-safety's ``read_contract`` and produces a populated
:class:`BandedContract`.

v0.2.1 corrective F1 root-cause: pr-safety's contract loader reads
``acs:`` + ``unhandled_paths:`` from the sidecar; pre-fix extractor
wrote neither, so the loader received zero-AC contracts and the gate
classified every diff line as novel. This test pins the round-trip
contract: extractor writes → pr-safety reads → BandedContract is
populated.

Cross-component test (lives under odd-extractor's test surface
because the producer is the regressor; the consumer's contract is
correct as-shipped per smoke evidence).
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor import (
    RawACs,
    default_budget,
    init_extraction,
    verify_contract,
)
from loam_odd_extractor.bands import ConfidenceBand
from loam_pr_safety.contract import read_contract


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


def test_extractor_to_pr_safety_round_trip(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Write a banded contract via the production verify_contract()
    path; load it back via pr-safety's read_contract; assert
    BandedContract.acs is populated + bands match input.
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
                ac_id="AC.RT.1",
                text="Verified AC pinned to a passing test.",
                confidence="VERIFIED",
                kind="test",
                citations=[
                    "tests/test_login.py::test_password_min_length",
                    "src/auth/login.py:10-30",
                ],
                repo_sha="2d9e7056deadbeef",
                backing_files=["src/auth/login.py"],
            ),
            _banded_ac_dict(
                ac_id="AC.RT.2",
                text="Plausible AC backed by source-code citation.",
                confidence="PLAUSIBLE",
                kind="source",
                citations=["src/services/order.py:42"],
                backing_files=["src/services/order.py"],
            ),
            _banded_ac_dict(
                ac_id="AC.RT.3",
                text="Hypothesised AC inferred from comment.",
                confidence="HYPOTHESISED",
                kind="inference",
                citations=[],
                rationale="Inferred from code comment in payment flow.",
                backing_files=["src/services/payments.py"],
            ),
        ],
        unhandled_paths=[
            Path(".gitignore"),
            Path("README.md"),
        ],
        per_slice_costs={},
        created_at=FIXED_TS,
    )

    # Producer side — write via the production verify_contract path.
    verify_contract(config=config, raw=raw, timestamp=FIXED_TS)

    # Consumer side — read via pr-safety's contract loader.
    contract = read_contract(
        repo_id=config.repo_id,
        workspace_root=workspace_root,
    )

    # BandedContract populated post-fix (pre-fix: zero ACs).
    assert len(contract.acs) == 3, (
        "pr-safety read_contract must produce a populated "
        "BandedContract from the extractor's contract-draft.yaml; "
        "received {} ACs".format(len(contract.acs))
    )

    ac_ids = [ac.ac_id for ac in contract.acs]
    assert ac_ids == ["AC.RT.1", "AC.RT.2", "AC.RT.3"]

    # Bands round-trip through the BandedAC validator.
    bands = [ac.confidence for ac in contract.acs]
    assert ConfidenceBand.VERIFIED in bands
    assert ConfidenceBand.PLAUSIBLE in bands
    assert ConfidenceBand.HYPOTHESISED in bands

    # Repo SHA inferred from the first AC that carries one.
    assert contract.repo_sha == "2d9e7056deadbeef"

    # unhandled_paths populated on the consumer side.
    assert len(contract.unhandled_paths) == 2
    unhandled_strs = [str(p) for p in contract.unhandled_paths]
    assert ".gitignore" in unhandled_strs
    assert "README.md" in unhandled_strs

    # Provenance preserved through the round-trip.
    assert contract.extraction_id == config.repo_id
