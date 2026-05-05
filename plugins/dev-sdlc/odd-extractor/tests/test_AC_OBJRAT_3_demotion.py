"""AC.OBJRAT.3 — V→P demotion: single explicit action; no
backing-evidence requirement.

- demote_objective(V→P / V→H / P→H) accepted with no explicit_yes.
- Same-band + upward refused.
- Demotion records prior backing-citations in audit-log informationally.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_odd_extractor import (
    BackingMap,
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
    RatificationRefusedError,
    apply_objective_ratification_action,
    demote_objective,
)
from loam_odd_extractor.observability import list_entries


def _verified_objective() -> Objective:
    return Objective(
        objective_id="O.dispute.1",
        text="Operators file refund disputes through the merchant portal",
        confidence=ConfidenceBand.VERIFIED,
        evidence=ObjectiveEvidence(
            test_name_refs=["tests/dispute.spec.ts::operator files dispute"],
            readme_excerpts=["dispute"],
            repo_sha="abc123def4567890",
        ),
        domain="dispute",
    )


def test_demote_v_to_p_accepted(tmp_path: Path) -> None:
    obj = _verified_objective()
    action = demote_objective(
        target_id="O.dispute.1",
        from_band=ConfidenceBand.VERIFIED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    out = apply_objective_ratification_action(
        action,
        objectives=[obj],
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["objectives"][0].confidence is ConfidenceBand.PLAUSIBLE


def test_demote_p_to_h_accepted(tmp_path: Path) -> None:
    obj = Objective(
        objective_id="O.x.1",
        text="Some plausible-band outcome that is observable from outside",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=ObjectiveEvidence(readme_excerpts=["x"]),
        domain="x",
    )
    action = demote_objective(
        target_id="O.x.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.HYPOTHESISED,
    )
    out = apply_objective_ratification_action(
        action,
        objectives=[obj],
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["objectives"][0].confidence is ConfidenceBand.HYPOTHESISED


def test_demote_v_to_h_accepted(tmp_path: Path) -> None:
    obj = _verified_objective()
    action = demote_objective(
        target_id="O.dispute.1",
        from_band=ConfidenceBand.VERIFIED,
        to_band=ConfidenceBand.HYPOTHESISED,
    )
    out = apply_objective_ratification_action(
        action,
        objectives=[obj],
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["objectives"][0].confidence is ConfidenceBand.HYPOTHESISED


def test_demote_same_band_refused() -> None:
    with pytest.raises(RatificationRefusedError):
        demote_objective(
            target_id="O.x.1",
            from_band=ConfidenceBand.VERIFIED,
            to_band=ConfidenceBand.VERIFIED,
        )


def test_demote_upward_refused() -> None:
    with pytest.raises(RatificationRefusedError):
        demote_objective(
            target_id="O.x.1",
            from_band=ConfidenceBand.PLAUSIBLE,
            to_band=ConfidenceBand.VERIFIED,
        )


def test_demote_records_in_audit_log(tmp_path: Path) -> None:
    obj = _verified_objective()
    action = demote_objective(
        target_id="O.dispute.1",
        from_band=ConfidenceBand.VERIFIED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    apply_objective_ratification_action(
        action,
        objectives=[obj],
        workspace_root=tmp_path,
        repo_id="t",
    )
    ext_dir = tmp_path / ".loam" / "extractions" / "t"
    entries = list_entries(ext_dir)
    payload = yaml.safe_load(entries[0].read_text(encoding="utf-8"))
    assert payload["event_kind"] == "ratification_objective_demote"
    assert payload["estimate"]["band_before"] == "VERIFIED"
    assert payload["estimate"]["band_after"] == "PLAUSIBLE"
