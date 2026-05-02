# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC40.7 — No tracker projection prose shipped from primary-persona/.

Source under ``primary-persona/src/`` does not contain literal prose
from any seeded tracker record (e.g., no copy of VALUE_PROPOSITION.md's
prime statement, no spec-clause text). The contributor composes its
output at runtime from the tracker query result; the tracker's content
is workspace-supplied (per amendment #39's framework-not-content
invariant on tracker seeding).

Maps to: v1.2 R16 framework-not-content (extended to tracker
projection) → AC.PO.2 (toolkit purity).

Plan: docs/rebuild/plans/amendment-40-primary-persona-tracker-context-contributor.md
"""

from __future__ import annotations

from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src" / "loam" / "primary_persona"


# Unique-prose markers from the canonical VALUE_PROPOSITION.md. If
# any of these appears in primary-persona/src/, the framework-not-
# content invariant has been violated — workspace-supplied content
# leaked into framework source.
_VP_PROSE_MARKERS: tuple[str, ...] = (
    # H1 of the value-prop doc
    "pOS v2 — Value Proposition of the Harness and the Primary Persona",
    # Distinct phrase from §17 ("translation layer")
    "translation layer between the user's natural-language intent",
    # Distinct phrase from §36 ("toolkit")
    "toolkit the primary persona draws from",
    # Distinct phrase from §57 (the AC.PO.1 specific test prose)
    "reduce the translation burden between the user's natural-language",
    # Distinct phrase from §63 (the AC.PO.2 specific test prose)
    "add to the toolkit the primary persona can draw from",
)


# Spec-doc unique-prose markers — the spec text the tracker's seeded
# spec-tier descendants reference at their LiftedFrom.source_doc.
# If any of this leaked into primary-persona source, the framework-
# not-content invariant has been violated.
_SPEC_PROSE_MARKERS: tuple[str, ...] = (
    # The architectural-layer Objective-based clause (line 161)
    "three behaviours (required above threshold, hierarchical with parentage,",
    "alignment is re-checked at every scope boundary",
)


def _iter_python_sources():
    for p in SRC_DIR.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        yield p


def test_AC40_7_no_value_prop_prose_in_primary_persona_src() -> None:
    """Sweep every .py file under primary-persona/src/ for unique-prose
    markers from VALUE_PROPOSITION.md. Zero matches expected — the
    contributor reads tracker records at runtime; the prose lives in
    docs/, not in source."""
    offending: list[tuple[Path, str]] = []
    for src in _iter_python_sources():
        text = src.read_text(encoding="utf-8")
        for marker in _VP_PROSE_MARKERS:
            if marker in text:
                offending.append((src, marker))
    assert offending == [], (
        f"AC40.7 — value-prop prose leaked into primary-persona/src/: {offending}"
    )


def test_AC40_7_no_spec_prose_in_primary_persona_src() -> None:
    """Same scan against spec-doc unique-prose markers."""
    offending: list[tuple[Path, str]] = []
    for src in _iter_python_sources():
        text = src.read_text(encoding="utf-8")
        for marker in _SPEC_PROSE_MARKERS:
            if marker in text:
                offending.append((src, marker))
    assert offending == [], (
        f"AC40.7 — spec-doc prose leaked into primary-persona/src/: {offending}"
    )


def test_AC40_7_tracker_context_source_composes_at_runtime() -> None:
    """The tracker_context.py source structurally references the
    tracker's runtime API (``query_projection_view``, ``trace_to_root``)
    and the projection's ``goal`` attribute — composition signals — and
    does NOT carry any concrete value-prop content as a constant."""
    src_path = SRC_DIR / "tracker_context.py"
    text = src_path.read_text(encoding="utf-8")
    # Composition signals (verified against full source).
    assert "query_projection_view" in text
    assert "trace_to_root" in text
    assert ".goal" in text or "goal" in text
    # Strip the Apache-2.0 license header (M8-corrective `6bef03b`
    # injected ``Luke Ivers`` as copyright owner; that's build-
    # metadata, not workspace-supplied content). AC.40.7 is about
    # value-prop content leak, not about the license header. Per
    # `feedback_loose_AC_text_fix_AC_not_implementation`: ODD §4
    # in-band rebaseline at C2-prime.
    text_for_content_check = _strip_apache_header(text)
    # Negative: no concrete-content constants. The renderer composes
    # from projection fields at runtime; no hard-coded goal-text
    # constant is permitted.
    forbidden_substrings = (
        "primary persona",  # any prose from VP doc body
        "Luke",
        "ivers",
        "personal-life operations",
    )
    for token in forbidden_substrings:
        assert token.lower() not in text_for_content_check.lower(), (
            f"AC40.7 — tracker_context.py contains content-shaped token "
            f"{token!r}; source must compose from runtime data"
        )


def _strip_apache_header(text: str) -> str:
    """Drop the leading Apache-2.0 license header (M8-corrective
    `6bef03b` injected). The header is a 14-line block ending at
    ``# limitations under the License.``; everything after that
    line is the source proper.
    """
    sentinel = "# limitations under the License."
    idx = text.find(sentinel)
    if idx < 0:
        return text
    return text[idx + len(sentinel):]
