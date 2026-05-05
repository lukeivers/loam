"""AC.OBJX.3 — Capability Pydantic model.

- Construction succeeds with non-empty ``serves`` list.
- ValidationError on empty ``serves`` / malformed reference.
- ID regex enforcement (``^C\\.[a-z][a-z0-9-]*\\.\\d+$``).
- Round-trip through model_dump / model_validate.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam_odd_extractor import Capability, CapabilityEvidence


def test_capability_with_single_objective_reference() -> None:
    c = Capability(
        capability_id="C.csv-upload.1",
        text="CSV upload + validation pipeline",
        serves=["O.dispute-flow.1"],
        evidence=CapabilityEvidence(
            readme_excerpts=["csv upload"],
        ),
    )
    assert c.serves == ["O.dispute-flow.1"]


def test_capability_with_multiple_objective_references() -> None:
    c = Capability(
        capability_id="C.csv-upload.1",
        text="CSV upload + validation pipeline",
        serves=["O.dispute-flow.1", "O.bulk-ops.1"],
        evidence=CapabilityEvidence(readme_excerpts=["csv upload"]),
    )
    assert len(c.serves) == 2


def test_capability_rejects_empty_serves() -> None:
    with pytest.raises(ValidationError) as exc:
        Capability(
            capability_id="C.x.1",
            text="x",
            serves=[],
            evidence=CapabilityEvidence(readme_excerpts=["x"]),
        )
    assert "serves" in str(exc.value)


def test_capability_rejects_malformed_objective_ref() -> None:
    with pytest.raises(ValidationError) as exc:
        Capability(
            capability_id="C.x.1",
            text="x",
            serves=["X.bad-ref.1"],  # wrong prefix
            evidence=CapabilityEvidence(readme_excerpts=["x"]),
        )
    assert "serves" in str(exc.value)


def test_capability_id_regex_rejects_wrong_prefix() -> None:
    with pytest.raises(ValidationError):
        Capability(
            capability_id="O.x.1",  # wrong prefix
            text="x",
            serves=["O.x.1"],
            evidence=CapabilityEvidence(readme_excerpts=["x"]),
        )


def test_capability_round_trip() -> None:
    c1 = Capability(
        capability_id="C.csv-upload.1",
        text="CSV upload pipeline",
        serves=["O.dispute-flow.1"],
        evidence=CapabilityEvidence(readme_excerpts=["csv"]),
    )
    payload = c1.model_dump(mode="json")
    c2 = Capability.model_validate(payload)
    assert c1.capability_id == c2.capability_id
    assert c1.serves == c2.serves
