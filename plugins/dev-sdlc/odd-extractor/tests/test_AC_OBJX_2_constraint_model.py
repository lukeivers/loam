"""AC.OBJX.2 — Constraint Pydantic model.

- Construction succeeds per ``bounds_kind``.
- ValidationError on empty evidence (≥1 ref kind required).
- ID regex enforcement (``^K\\.[a-z][a-z0-9-]*\\.\\d+$``).
- Round-trip through model_dump / model_validate.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam_odd_extractor import Constraint, ConstraintEvidence


def test_compliance_constraint_with_readme_evidence() -> None:
    k = Constraint(
        constraint_id="K.compliance.1",
        text="System must satisfy SOC-2 audit-trail floor",
        bounds_kind="compliance",
        evidence=ConstraintEvidence(
            readme_excerpts=["soc-2 audit trail required"],
        ),
    )
    assert k.bounds_kind == "compliance"


def test_security_constraint_with_design_doc_ref() -> None:
    k = Constraint(
        constraint_id="K.security.1",
        text="Tokens confidential under transport",
        bounds_kind="security",
        evidence=ConstraintEvidence(
            design_doc_refs=["docs/security.md#tokens"],
        ),
    )
    assert k.bounds_kind == "security"


def test_constraint_rejects_empty_evidence() -> None:
    with pytest.raises(ValidationError) as exc:
        Constraint(
            constraint_id="K.x.1",
            text="bound",
            bounds_kind="domain",
            evidence=ConstraintEvidence(),
        )
    assert "evidence" in str(exc.value)


def test_constraint_id_regex_rejects_wrong_prefix() -> None:
    with pytest.raises(ValidationError):
        Constraint(
            constraint_id="O.x.1",  # wrong prefix
            text="bound",
            bounds_kind="domain",
            evidence=ConstraintEvidence(readme_excerpts=["x"]),
        )


def test_constraint_round_trip() -> None:
    k1 = Constraint(
        constraint_id="K.security.1",
        text="Tokens confidential under transport",
        bounds_kind="security",
        evidence=ConstraintEvidence(design_doc_refs=["docs/x.md"]),
    )
    payload = k1.model_dump(mode="json")
    k2 = Constraint.model_validate(payload)
    assert k1.constraint_id == k2.constraint_id
    assert k1.bounds_kind == k2.bounds_kind


def test_constraint_rejects_invalid_bounds_kind() -> None:
    with pytest.raises(ValidationError):
        Constraint(
            constraint_id="K.x.1",
            text="bound",
            bounds_kind="not-a-kind",  # type: ignore[arg-type]
            evidence=ConstraintEvidence(readme_excerpts=["x"]),
        )
