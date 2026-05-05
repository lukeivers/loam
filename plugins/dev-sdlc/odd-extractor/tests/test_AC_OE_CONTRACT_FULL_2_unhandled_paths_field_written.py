"""AC.OE.CONTRACT-FULL.2 — verify_contract() writes
``unhandled_paths:`` field into ``contract-draft.yaml``.

v0.2.1 corrective F1 (smoke evidence at /Users/lukeivers/pos3/workspace
/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-04.md). The
sidecar must carry the unhandled-paths list so pr-safety's
``read_contract`` can populate :attr:`BandedContract.unhandled_paths`
for novel-detection logic.
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


FIXED_TS = "2026-05-04T12:00:00+00:00"


def test_unhandled_paths_field_written_as_list_of_strings(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """``contract-draft.yaml`` carries an ``unhandled_paths`` list of
    strings (Path objects coerced to str so YAML safe_dump succeeds).
    Length matches input.
    """
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    unhandled_input = [
        Path(".gitignore"),
        Path(".github/workflows/ci.yml"),
        Path("Dockerfile"),
        Path("package-lock.json"),
        Path("README.md"),
        Path("docs/setup.md"),
    ]
    raw = RawACs(
        extraction_id=config.repo_id,
        acs=[],
        unhandled_paths=unhandled_input,
        per_slice_costs={},
        created_at=FIXED_TS,
    )

    draft = verify_contract(config=config, raw=raw, timestamp=FIXED_TS)

    sidecar = draft.sidecar_path
    assert sidecar.exists()
    payload = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)

    # unhandled_paths field present, list-shaped, length matches input.
    assert "unhandled_paths" in payload, (
        "contract-draft.yaml must carry top-level `unhandled_paths` "
        "field per AC.OE.CONTRACT-FULL.2"
    )
    assert isinstance(payload["unhandled_paths"], list)
    assert len(payload["unhandled_paths"]) == len(unhandled_input)

    # All entries are strings (Path round-trip via str()).
    for entry in payload["unhandled_paths"]:
        assert isinstance(entry, str), (
            "unhandled_paths entries must be string-coerced; "
            "Path objects don't survive yaml.safe_dump"
        )

    # Set-equality (order may not be guaranteed across Python versions
    # but lists are stable; keep exact-list check).
    assert payload["unhandled_paths"] == [
        str(p) for p in unhandled_input
    ]

    # unhandled_count summary still aligned with the new list-field.
    assert payload["unhandled_count"] == len(unhandled_input)


def test_empty_unhandled_paths_round_trips_as_empty_list(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Zero-unhandled case — synthetic banded fixture shape — still
    produces an empty list (not absent / not None).
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
    assert payload["unhandled_paths"] == []
    assert payload["unhandled_count"] == 0
