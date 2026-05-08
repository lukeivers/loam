"""AC.BANDS.6 — audit log per ratification action (SOC-2 floor).

Every apply_ratification_action call writes one audit-log entry under
``<workspace>/.loam/extractions/<repo-id>/audit-log/`` with
``event_kind="ratification_<kind>"``.

Tests:
- promote / demote / edit / reject each write one entry.
- Entries carry schema_version=1, timestamp, extraction_id, event_kind.
- Sequence is monotonic (filename pattern <NNNN>.yaml).
- pm_audit_path field is included on the entries' notes when supplied.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_odd_extractor import (
    BandedAC,
    ConfidenceBand,
    Evidence,
    apply_ratification_action,
    demote,
    edit,
    promote,
    reject,
)
from loam_odd_extractor.observability import list_entries
from loam_odd_extractor.ratification_state import (
    initialise_ratification_state,
)
from loam_odd_extractor.state import extraction_dir


@pytest.fixture
def workspace_with_state(tmp_path: Path) -> tuple[Path, str, list[BandedAC]]:
    """Pre-built workspace with an extraction-dir + ratification-state
    listing 4 ACs to exercise all 4 action variants."""
    ws = tmp_path / "ws"
    ws.mkdir()
    repo_id = "test-repo-1234"
    ext_dir = extraction_dir(ws, repo_id)
    ext_dir.mkdir(parents=True)

    banded_acs = [
        BandedAC(
            ac_id="AC.PROMOTE",
            text="will be promoted",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="initial"),
        ),
        BandedAC(
            ac_id="AC.DEMOTE",
            text="will be demoted",
            confidence=ConfidenceBand.VERIFIED,
            evidence=Evidence(
                kind="test",
                citations=["t.py::x"],
                repo_sha="abc1234",
            ),
        ),
        BandedAC(
            ac_id="AC.EDIT",
            text="original text",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(kind="source", citations=["src.py:1"]),
        ),
        BandedAC(
            ac_id="AC.REJECT",
            text="will be rejected",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="will be removed"),
        ),
    ]

    initialise_ratification_state(
        ext_dir,
        extraction_id=repo_id,
        draft_path="contract-draft.md",
        pm_handle="test-pm",
        pending_acs=[ac.ac_id for ac in banded_acs],
    )
    return ws, repo_id, banded_acs


def _read_entry(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_promote_writes_one_entry(
    workspace_with_state: tuple[Path, str, list[BandedAC]],
) -> None:
    ws, repo_id, banded_acs = workspace_with_state
    ext_dir = extraction_dir(ws, repo_id)
    before = len(list_entries(ext_dir))

    action = promote(
        ac_id="AC.PROMOTE",
        from_band=ConfidenceBand.HYPOTHESISED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    apply_ratification_action(
        action,
        banded_acs=banded_acs,
        workspace_root=ws,
        repo_id=repo_id,
    )
    entries = list_entries(ext_dir)
    assert len(entries) == before + 1
    payload = _read_entry(entries[-1])
    assert payload["event_kind"] == "ratification_promote"
    assert payload["extraction_id"] == repo_id
    assert payload["schema_version"] == 1


def test_demote_writes_one_entry(
    workspace_with_state: tuple[Path, str, list[BandedAC]],
) -> None:
    ws, repo_id, banded_acs = workspace_with_state
    ext_dir = extraction_dir(ws, repo_id)

    action = demote(
        ac_id="AC.DEMOTE",
        from_band=ConfidenceBand.VERIFIED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    apply_ratification_action(
        action,
        banded_acs=banded_acs,
        workspace_root=ws,
        repo_id=repo_id,
    )
    entries = list_entries(ext_dir)
    payload = _read_entry(entries[-1])
    assert payload["event_kind"] == "ratification_demote"


def test_edit_writes_one_entry(
    workspace_with_state: tuple[Path, str, list[BandedAC]],
) -> None:
    ws, repo_id, banded_acs = workspace_with_state
    ext_dir = extraction_dir(ws, repo_id)

    action = edit(
        ac_id="AC.EDIT",
        edit_text="new text",
    )
    apply_ratification_action(
        action,
        banded_acs=banded_acs,
        workspace_root=ws,
        repo_id=repo_id,
    )
    entries = list_entries(ext_dir)
    payload = _read_entry(entries[-1])
    assert payload["event_kind"] == "ratification_edit"


def test_reject_writes_one_entry(
    workspace_with_state: tuple[Path, str, list[BandedAC]],
) -> None:
    ws, repo_id, banded_acs = workspace_with_state
    ext_dir = extraction_dir(ws, repo_id)

    action = reject(
        ac_id="AC.REJECT",
        reject_reason="codebase doesn't actually exhibit this",
    )
    apply_ratification_action(
        action,
        banded_acs=banded_acs,
        workspace_root=ws,
        repo_id=repo_id,
    )
    entries = list_entries(ext_dir)
    payload = _read_entry(entries[-1])
    assert payload["event_kind"] == "ratification_reject"
    assert "codebase doesn't actually exhibit this" in payload["notes"]


def test_pm_audit_path_appears_in_notes(
    workspace_with_state: tuple[Path, str, list[BandedAC]],
) -> None:
    ws, repo_id, banded_acs = workspace_with_state
    ext_dir = extraction_dir(ws, repo_id)

    action = promote(
        ac_id="AC.PROMOTE",
        from_band=ConfidenceBand.HYPOTHESISED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    apply_ratification_action(
        action,
        banded_acs=banded_acs,
        workspace_root=ws,
        repo_id=repo_id,
        pm_audit_path="audit-log/2026-05-04-0003.yaml",
    )
    entries = list_entries(ext_dir)
    payload = _read_entry(entries[-1])
    assert "pm_audit_path=audit-log/2026-05-04-0003.yaml" in payload["notes"]


def test_audit_log_filenames_monotonic(
    workspace_with_state: tuple[Path, str, list[BandedAC]],
) -> None:
    """4 ratification actions in sequence → filenames 0001..0004
    (monotonic; no gaps)."""
    ws, repo_id, banded_acs = workspace_with_state

    actions = [
        promote(
            ac_id="AC.PROMOTE",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        ),
        demote(
            ac_id="AC.DEMOTE",
            from_band=ConfidenceBand.VERIFIED,
            to_band=ConfidenceBand.PLAUSIBLE,
        ),
        edit(ac_id="AC.EDIT", edit_text="new text"),
        reject(
            ac_id="AC.REJECT", reject_reason="not exhibited"
        ),
    ]
    for a in actions:
        apply_ratification_action(
            a,
            banded_acs=banded_acs,
            workspace_root=ws,
            repo_id=repo_id,
        )

    ext_dir = extraction_dir(ws, repo_id)
    entries = list_entries(ext_dir)
    # 4 ratification entries; filenames 0001..0004 contiguous (no
    # earlier entries since the fixture didn't run an extraction).
    assert len(entries) == 4
    for idx, p in enumerate(entries, start=1):
        assert p.name == f"{idx:04d}.yaml"


def test_explicit_yes_appears_in_notes(
    workspace_with_state: tuple[Path, str, list[BandedAC]],
) -> None:
    ws, repo_id, banded_acs = workspace_with_state
    # AC.EDIT is currently PLAUSIBLE — promote it to VERIFIED with
    # explicit_yes=True so the audit-log records the explicit-yes.
    action = promote(
        ac_id="AC.EDIT",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
    )
    apply_ratification_action(
        action,
        banded_acs=banded_acs,
        workspace_root=ws,
        repo_id=repo_id,
    )
    ext_dir = extraction_dir(ws, repo_id)
    entries = list_entries(ext_dir)
    payload = _read_entry(entries[-1])
    assert "explicit_yes=true" in payload["notes"]
