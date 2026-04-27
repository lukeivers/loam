"""Stable objective-id derivation for Heavy-B migration records.

Stable IDs make idempotency-by-query cheap and deterministic. Every
Heavy-B record's ``objective_id`` is derived from the source-doc-path
and AC-id; re-running the extractor against an already-projected
tracker hits the same ID and is a no-op.

Naming scheme (per builder-plan §5):

- ``value-prop-root`` — value-prop root (already seeded by #39).
- ``spec-v1.0`` / ``spec-v1.1`` / ``spec-v1.2`` — spec phases (already
  seeded by #39).
- ``component-<slug>`` — Phase α component objective.
- ``component-<slug>-ac-<ac_id>`` — Phase β component AC.
- ``component-<slug>-placeholder`` — Phase β placeholder for an
  unparseable proposal.
- ``amendment-<NN>-ac-<ac_id>`` — Phase γ amendment AC.
- ``amendment-<NN>-placeholder`` — Phase γ placeholder.

Slugs are workspace-relative directory names from
``docs/rebuild/components/`` (already lowercase-hyphenated) and
amendment numbers are extracted from the plan-file basename.
"""

from __future__ import annotations

import re


# Sentinel root + spec-tier IDs (must match #39's TrackerSeed).
ROOT_OBJECTIVE_ID = "value-prop-root"
SPEC_V10 = "spec-v1.0"
SPEC_V11 = "spec-v1.1"
SPEC_V12 = "spec-v1.2"


def component_objective_id(component_slug: str) -> str:
    """Stable ID for a Phase α sealed-component objective."""
    return f"component-{component_slug}"


def component_ac_objective_id(component_slug: str, ac_id: str) -> str:
    """Stable ID for a Phase β component-AC objective.

    AC IDs are normalised to lowercase + non-alphanumeric stripped so
    two reasonable spellings of the same AC ("D1" vs "d1") collide
    rather than create duplicates. Tests pin the normalisation.
    """
    norm = _normalise_ac_id(ac_id)
    return f"component-{component_slug}-ac-{norm}"


def component_placeholder_id(component_slug: str) -> str:
    """Stable ID for a Phase β placeholder record."""
    return f"component-{component_slug}-placeholder"


def amendment_ac_objective_id(amendment_number: int, ac_id: str) -> str:
    """Stable ID for a Phase γ amendment-AC objective."""
    norm = _normalise_ac_id(ac_id)
    return f"amendment-{amendment_number}-ac-{norm}"


def amendment_placeholder_id(amendment_number: int) -> str:
    """Stable ID for a Phase γ placeholder record."""
    return f"amendment-{amendment_number}-placeholder"


_AC_NORM_RE = re.compile(r"[^a-z0-9]+")


def _normalise_ac_id(ac_id: str) -> str:
    return _AC_NORM_RE.sub("-", ac_id.strip().lower()).strip("-")
