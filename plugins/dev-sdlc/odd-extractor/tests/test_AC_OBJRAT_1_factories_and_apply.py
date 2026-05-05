"""AC.OBJRAT.1 — Objective-altitude factory functions + apply path.

- promote_objective / demote_objective / edit_objective / reject_objective.
- Same set parallel for constraint + capability.
- ObjectiveRatificationAction frozen-dataclass round-trip.
- apply_objective_ratification_action mutates typed lists.
- v1 BandedAC apply path still callable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor import (
    ConfidenceBand,
    Capability,
    CapabilityEvidence,
    Constraint,
    ConstraintEvidence,
    Objective,
    ObjectiveEvidence,
    ObjectiveRatificationAction,
    RatificationRefusedError,
    apply_objective_ratification_action,
    demote_capability,
    demote_constraint,
    demote_objective,
    edit_capability,
    edit_constraint,
    edit_objective,
    promote_capability,
    promote_constraint,
    promote_objective,
    reject_capability,
    reject_constraint,
    reject_objective,
)


def _plausible_objective(oid: str = "O.alpha.1") -> Objective:
    return Objective(
        objective_id=oid,
        text="Operators see results displayed in the dashboard",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=ObjectiveEvidence(readme_excerpts=["x"]),
        domain="dashboard",
    )


def _plausible_constraint(cid: str = "K.alpha.1") -> Constraint:
    return Constraint(
        constraint_id=cid,
        text="System SOC-2 compliant",
        bounds_kind="compliance",
        evidence=ConstraintEvidence(readme_excerpts=["soc2"]),
    )


def _plausible_capability(
    cid: str = "C.alpha.1", serves: list[str] | None = None
) -> Capability:
    return Capability(
        capability_id=cid,
        text="CSV upload pipeline",
        serves=serves or ["O.alpha.1"],
        evidence=CapabilityEvidence(readme_excerpts=["upload"]),
    )


# ---- Construction --------------------------------------------------


def test_promote_objective_factory_basic() -> None:
    a = promote_objective(
        target_id="O.alpha.1",
        from_band=ConfidenceBand.HYPOTHESISED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    assert a.kind == "promote"
    assert a.altitude == "objective"
    assert a.target_id == "O.alpha.1"
    assert a.from_band is ConfidenceBand.HYPOTHESISED
    assert a.to_band is ConfidenceBand.PLAUSIBLE


def test_promote_constraint_factory_basic() -> None:
    a = promote_constraint(
        target_id="K.alpha.1",
        from_band=ConfidenceBand.HYPOTHESISED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    assert a.altitude == "constraint"


def test_promote_capability_factory_basic() -> None:
    a = promote_capability(
        target_id="C.alpha.1",
        from_band=ConfidenceBand.HYPOTHESISED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    assert a.altitude == "capability"


def test_demote_factories_basic() -> None:
    assert demote_objective(
        target_id="O.alpha.1",
        from_band=ConfidenceBand.VERIFIED,
        to_band=ConfidenceBand.PLAUSIBLE,
    ).kind == "demote"
    assert demote_constraint(
        target_id="K.alpha.1",
        from_band=ConfidenceBand.VERIFIED,
        to_band=ConfidenceBand.PLAUSIBLE,
    ).kind == "demote"
    assert demote_capability(
        target_id="C.alpha.1",
        from_band=ConfidenceBand.VERIFIED,
        to_band=ConfidenceBand.PLAUSIBLE,
    ).kind == "demote"


def test_edit_factories_basic() -> None:
    assert edit_objective(
        target_id="O.alpha.1", edit_text="new"
    ).edit_text == "new"
    assert edit_constraint(
        target_id="K.alpha.1", edit_text="new"
    ).edit_text == "new"
    assert edit_capability(
        target_id="C.alpha.1", edit_text="new"
    ).edit_text == "new"


def test_reject_factories_basic() -> None:
    assert reject_objective(
        target_id="O.alpha.1", reject_reason="x"
    ).reject_reason == "x"
    assert reject_constraint(
        target_id="K.alpha.1", reject_reason="x"
    ).reject_reason == "x"
    assert reject_capability(
        target_id="C.alpha.1", reject_reason="x"
    ).reject_reason == "x"


def test_factory_rejects_empty_target_id() -> None:
    with pytest.raises(RatificationRefusedError):
        promote_objective(
            target_id="",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        )


def test_factory_rejects_downward_promote() -> None:
    with pytest.raises(RatificationRefusedError):
        promote_objective(
            target_id="O.x.1",
            from_band=ConfidenceBand.VERIFIED,
            to_band=ConfidenceBand.PLAUSIBLE,
        )


# ---- Apply path ----------------------------------------------------


def test_apply_promote_objective_round_trip(tmp_path: Path) -> None:
    obj = _plausible_objective()
    action = promote_objective(
        target_id="O.alpha.1",
        from_band=ConfidenceBand.HYPOTHESISED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    out = apply_objective_ratification_action(
        action,
        objectives=[obj],
        workspace_root=tmp_path,
        repo_id="t",
    )
    # PLAUSIBLE → already plausible, but the band field is stamped.
    assert out["objectives"][0].confidence is ConfidenceBand.PLAUSIBLE


def test_apply_edit_objective(tmp_path: Path) -> None:
    obj = _plausible_objective()
    action = edit_objective(
        target_id="O.alpha.1",
        edit_text="Operators get a brand-new outcome statement here ok",
    )
    out = apply_objective_ratification_action(
        action,
        objectives=[obj],
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["objectives"][0].text.startswith("Operators get a brand-new")


def test_apply_reject_objective(tmp_path: Path) -> None:
    obj = _plausible_objective()
    action = reject_objective(
        target_id="O.alpha.1", reject_reason="duplicate"
    )
    out = apply_objective_ratification_action(
        action,
        objectives=[obj],
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["objectives"] == []


def test_apply_refuses_unknown_target(tmp_path: Path) -> None:
    action = edit_objective(
        target_id="O.does-not-exist.1", edit_text="new text"
    )
    with pytest.raises(RatificationRefusedError):
        apply_objective_ratification_action(
            action,
            objectives=[_plausible_objective()],
            workspace_root=tmp_path,
            repo_id="t",
        )


def test_v1_apply_path_still_callable(tmp_path: Path) -> None:
    """The v0.1.8 BandedAC apply path is preserved (parallel paths)."""
    from loam_odd_extractor import (
        BandedAC,
        Evidence,
        apply_ratification_action,
        promote,
    )

    banded = [
        BandedAC(
            ac_id="AC.X.1",
            text="x",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="r"),
        )
    ]
    out = apply_ratification_action(
        promote(
            ac_id="AC.X.1",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        ),
        banded_acs=banded,
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out[0].confidence is ConfidenceBand.PLAUSIBLE


def test_objective_ratification_action_is_frozen() -> None:
    action = promote_objective(
        target_id="O.alpha.1",
        from_band=ConfidenceBand.HYPOTHESISED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    with pytest.raises(Exception):
        action.kind = "demote"  # type: ignore[misc]


def test_constraint_apply_edit(tmp_path: Path) -> None:
    cons = _plausible_constraint()
    action = edit_constraint(
        target_id="K.alpha.1", edit_text="updated constraint"
    )
    out = apply_objective_ratification_action(
        action,
        constraints=[cons],
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["constraints"][0].text == "updated constraint"


def test_capability_apply_edit(tmp_path: Path) -> None:
    cap = _plausible_capability()
    action = edit_capability(
        target_id="C.alpha.1", edit_text="updated capability"
    )
    out = apply_objective_ratification_action(
        action,
        objectives=[_plausible_objective()],
        capabilities=[cap],
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["capabilities"][0].text == "updated capability"
