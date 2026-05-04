"""Constructor helper for HYPOTHESISED-band ACs (cross-language shared).

Per AC.DRY.3 (v0.1.8 Cycle 4b) — the single canonical constructor
for HYPOTHESISED-band BandedAC instances derived from a source
PLAUSIBLE AC. Pre-4b each per-language ``heuristic_inferences.py``
(``lang/ruby/`` and ``lang/jsts/``) hand-rolled the constructor:

    BandedAC(
        ac_id=...,
        text=...,
        confidence=ConfidenceBand.HYPOTHESISED,
        evidence=Evidence(
            kind="inference",
            citations=list(source_ac.evidence.citations),
            rationale=...,
        ),
        backing_files=...,
    )

Cycle 4b factors the boilerplate (confidence + kind="inference" +
citations-derivation + backing-files-derivation) into this helper;
per-language regex tables + heuristic firing logic stay in their
respective ``heuristic_inferences.py`` modules.

Per Cycle 4b §10 RF #2 — the helper's signature constrains future
shape (one PLAUSIBLE source AC → one HYPOTHESISED inferred AC). If
multi-source inference is needed (Cycle 5+ LLM-driven heuristics),
extend the helper with a ``source_acs: list[BandedAC]`` variant
under the same module.
"""

from __future__ import annotations

from typing import Sequence

from ...bands import BandedAC, ConfidenceBand, Evidence


def make_inferred_banded_ac(
    *,
    ac_id: str,
    text: str,
    rationale: str,
    source_ac: BandedAC,
    backing_files: Sequence[str] | None = None,
) -> BandedAC:
    """Construct a HYPOTHESISED-band ``BandedAC`` derived from one
    source ``PLAUSIBLE`` AC.

    Parameters:

    - ``ac_id`` — the deterministic AC ID string (caller derives;
      typically prefixed ``AC.<LANG>.inferred.<heuristic>.<slug>``).
    - ``text`` — descriptive prose for the inferred AC.
    - ``rationale`` — non-empty rationale string capturing the
      heuristic's provenance + (typically) the source AC's
      ``ac_id``. Required by ``AC.BANDS.2`` for HYPOTHESISED-band
      ACs.
    - ``source_ac`` — the PLAUSIBLE-band AC the inference fired
      from. Citations are forwarded from ``source_ac.evidence.citations``;
      ``backing_files`` defaults to ``source_ac.backing_files``.
    - ``backing_files`` — optional override for the inferred AC's
      backing files. Defaults to the source AC's backing files.

    Returns a fully-constructed ``BandedAC`` with
    ``confidence=HYPOTHESISED``, ``evidence.kind="inference"``,
    citations forwarded from the source AC.

    Notes:

    - The helper does NOT enforce that ``source_ac.confidence ==
      PLAUSIBLE`` — orchestration in the per-language
      ``infer_domain_rules()`` enforces that gate (today). Cycle
      4b §10 RF #5 surfaces the question of helper-level
      enforcement; deferred (future inference shapes may want
      VERIFIED → HYPOTHESISED inference too).
    - The helper does NOT validate the rationale string format;
      callers are encouraged to include the source AC ID for
      traceability (existing per-language pattern).
    """
    citations = (
        list(source_ac.evidence.citations)
        if source_ac.evidence and source_ac.evidence.citations
        else []
    )
    derived_backing = (
        list(backing_files)
        if backing_files is not None
        else list(source_ac.backing_files)
    )
    return BandedAC(
        ac_id=ac_id,
        text=text,
        confidence=ConfidenceBand.HYPOTHESISED,
        evidence=Evidence(
            kind="inference",
            citations=citations,
            rationale=rationale,
        ),
        backing_files=derived_backing,
    )
