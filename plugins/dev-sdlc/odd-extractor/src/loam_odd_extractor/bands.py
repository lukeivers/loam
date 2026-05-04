"""Confidence bands for derived ACs.

Per AC.BANDS.1 + AC.BANDS.2 (v0.1.8 Cycle 2 plan-doc §4) — every
derived AC carries a ``confidence:`` band field with values
``VERIFIED | PLAUSIBLE | HYPOTHESISED`` and a structured
``evidence:`` block whose shape depends on the band.

Composition: this module is the in-memory typed representation;
:class:`~loam_odd_extractor.spec.RawACs` keeps the loose
``acs: list[dict]`` shape so adapter outputs (Cycles 3+4) can produce
dicts before the typed model is constructed. :meth:`BandedAC.model_dump`
round-trips cleanly through that dict shape — no schema migration.

Per AC.BANDS.2, the model_validator enforces per-band evidence rules
structurally (Pydantic ValidationError on construction), not via
advisory documentation. ODD §5.3 — Pydantic + model_validators is
the reach-for default for invariants that must hold "always".
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class ConfidenceBand(str, Enum):
    """Three-band taxonomy for derived AC confidence.

    Per AC.BANDS.1:

    - ``VERIFIED`` — backed by a passing test pinned to a repo SHA.
    - ``PLAUSIBLE`` — backed by source-code citation (file path +
      line numbers); no executable verification yet.
    - ``HYPOTHESISED`` — LLM-derived inference; carries a rationale
      string explaining the inference chain.

    String enum (str-mixin) so YAML/JSON serialization produces the
    band's name verbatim (``"VERIFIED"`` not ``"<ConfidenceBand.VERIFIED: ...>"``).
    """

    VERIFIED = "VERIFIED"
    PLAUSIBLE = "PLAUSIBLE"
    HYPOTHESISED = "HYPOTHESISED"


class Evidence(BaseModel):
    """Evidence block for a banded AC.

    Per AC.BANDS.1 + AC.BANDS.2:

    - ``kind`` — discriminator; matches the band:
      VERIFIED → ``"test"``, PLAUSIBLE → ``"source"``,
      HYPOTHESISED → ``"inference"``.
    - ``citations`` — list of evidence pointers (file paths + line
      numbers + test names). Required non-empty for VERIFIED +
      PLAUSIBLE; may be empty for HYPOTHESISED (pure inference).
    - ``repo_sha`` — repo SHA pinned at evidence-collection time;
      required (non-null) for VERIFIED so the test pin survives
      codebase drift; optional otherwise.
    - ``rationale`` — LLM-derived explanation; required (non-empty)
      for HYPOTHESISED; optional otherwise.

    The per-band invariants are enforced on :class:`BandedAC` (the
    composing type) so the rules are applied to the band+evidence
    pair, not in isolation. :class:`Evidence` itself enforces the
    discriminator literal + structural shape.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["test", "source", "inference"]
    citations: list[str] = Field(default_factory=list)
    repo_sha: str | None = None
    rationale: str | None = None


class BandedAC(BaseModel):
    """A confidence-banded acceptance criterion.

    Per AC.BANDS.1:

    - ``ac_id`` — required, non-empty; the AC's stable identifier
      (e.g., ``"AC.RAILS.3"`` or ``"AC.PYTHON.7"``).
    - ``text`` — required, non-empty; the AC's prose.
    - ``confidence`` — required; one of three bands.
    - ``evidence`` — required; structured evidence block per band.
    - ``backing_files`` — list of file paths the AC backs against.
      Preserves Cycle 1's coverage-check field shape; empty by default.

    Per AC.BANDS.2 (model_validator), the per-band invariants:

    - VERIFIED requires ``evidence.kind == "test"``,
      ``evidence.repo_sha`` non-null, ``evidence.citations`` non-empty.
    - PLAUSIBLE requires ``evidence.kind == "source"``,
      ``evidence.citations`` non-empty.
    - HYPOTHESISED requires ``evidence.kind == "inference"``,
      ``evidence.rationale`` non-empty (and non-whitespace-only).

    All invariants raise :class:`pydantic.ValidationError` on construction;
    no instance can hold a malformed band/evidence pair.

    Round-trip: :meth:`model_dump()` produces a dict that survives
    ``RawACs.acs: list[dict]`` persistence + reconstruction via
    :meth:`model_validate()`. Adapter outputs (Cycles 3+4) can produce
    dicts directly; this typed model is the in-memory authority.
    """

    model_config = ConfigDict(extra="forbid")

    ac_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    confidence: ConfidenceBand
    evidence: Evidence
    backing_files: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _enforce_per_band_evidence_rules(self) -> "BandedAC":
        """Per AC.BANDS.2 — band-specific evidence invariants.

        Each band has a matching ``evidence.kind`` literal and a set
        of required-non-empty fields. Violations raise on construction.
        """
        band = self.confidence
        ev = self.evidence

        if band is ConfidenceBand.VERIFIED:
            if ev.kind != "test":
                raise ValueError(
                    f"BandedAC.evidence: VERIFIED band requires "
                    f"evidence.kind='test'; got {ev.kind!r}"
                )
            if not ev.repo_sha:
                raise ValueError(
                    "BandedAC.evidence: VERIFIED band requires "
                    "non-null evidence.repo_sha (pin the test to a "
                    "repo SHA at evidence-collection time)"
                )
            if not ev.citations:
                raise ValueError(
                    "BandedAC.evidence: VERIFIED band requires "
                    "evidence.citations to be non-empty (test name + "
                    "file path)"
                )
        elif band is ConfidenceBand.PLAUSIBLE:
            if ev.kind != "source":
                raise ValueError(
                    f"BandedAC.evidence: PLAUSIBLE band requires "
                    f"evidence.kind='source'; got {ev.kind!r}"
                )
            if not ev.citations:
                raise ValueError(
                    "BandedAC.evidence: PLAUSIBLE band requires "
                    "evidence.citations to be non-empty (source file "
                    "path + line numbers)"
                )
        elif band is ConfidenceBand.HYPOTHESISED:
            if ev.kind != "inference":
                raise ValueError(
                    f"BandedAC.evidence: HYPOTHESISED band requires "
                    f"evidence.kind='inference'; got {ev.kind!r}"
                )
            if not ev.rationale or not ev.rationale.strip():
                raise ValueError(
                    "BandedAC.evidence: HYPOTHESISED band requires "
                    "non-empty evidence.rationale (LLM-derived "
                    "inference chain explanation)"
                )
        return self
