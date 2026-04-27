"""Amendment #39 — AC39.6 — No tracker payload content shipped from
``workspace-bootstrap/src/``.

Plan §4 AC39.6 outcomes:

- Source under ``workspace-bootstrap/src/`` does not contain literal
  value-prop prose or spec-clause prose hard-coded as constants.
- The seed reads value-prop content from a framework docs path at
  first-run-time (on pos-v2 dev workspaces) or from a workspace-
  supplied path (on non-dev workspaces).
- A test-fixture scan asserts the source files contain none of the
  unique prose markers from ``docs/rebuild/VALUE_PROPOSITION.md``'s
  primary statement.

Maps to v1.2 R16 framework-not-content (tracker-seeding extension)
→ AC.PO.2 (toolkit purity).
"""

from __future__ import annotations

from pathlib import Path

import pytest


_WB_SRC_ROOT = (
    Path(__file__).resolve().parent.parent / "src" / "workspace_bootstrap"
)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_FRAMEWORK_VP_PATH = _REPO_ROOT / "docs" / "rebuild" / "VALUE_PROPOSITION.md"


# Distinctive sentences from VALUE_PROPOSITION.md — pulled from the
# canonical doc. Each sentence is workspace-content (specific to
# Luke's pOS framing); none of these may appear hard-coded in
# workspace-bootstrap source.
_FORBIDDEN_VP_SENTINELS = [
    # The H1 itself — workspace-content if hard-coded.
    "pOS v2 — Value Proposition of the Harness and the Primary Persona",
    # Distinct opening of "The problem pOS is closing".
    "AI has a usability problem",
    # The 12-hour example's distinctive framing.
    "The 12-hour example",
    "do this thing every 12 hours",
    # The translation-layer framing.
    "primary persona is a translation layer",
    # Workspace-specific motivating observation.
    "25,000 tokens per run",
]


def test_AC39_6_value_prop_sentinels_not_in_workspace_bootstrap_src() -> None:
    """No file under ``workspace-bootstrap/src/`` contains literal
    VALUE_PROPOSITION.md prose — the seed reads the doc from disk
    at runtime, never embeds it."""
    # Cross-check the sentinels actually exist in the canonical doc
    # so the test cannot silently pass when the doc evolves.
    vp_text = _FRAMEWORK_VP_PATH.read_text()
    for sentinel in _FORBIDDEN_VP_SENTINELS:
        assert sentinel in vp_text, (
            f"test fixture: sentinel {sentinel!r} not found in "
            f"{_FRAMEWORK_VP_PATH}; update the test's sentinel set"
        )

    for src_file in _WB_SRC_ROOT.rglob("*.py"):
        text = src_file.read_text()
        for sentinel in _FORBIDDEN_VP_SENTINELS:
            assert sentinel not in text, (
                f"{src_file} contains VALUE_PROPOSITION sentinel "
                f"{sentinel!r} — framework-not-content invariant broken; "
                "the seed must read the doc at first-run-time, not "
                "embed prose constants."
            )


_FORBIDDEN_SPEC_SENTINELS = [
    # Distinctive prose from pos-v2-objectives-spec.md sections that
    # the seed lifts from at first-run time. These must not appear in
    # workspace-bootstrap/src/.
    "alignment is re-checked at every scope boundary",
    "non-tech users",
    "low-friction onboarding",
]


def test_AC39_6_spec_doc_sentinels_not_in_workspace_bootstrap_src() -> None:
    """The spec doc is consumed by the seed (as
    ``LiftedFrom.source_doc`` provenance pointer); its prose must
    not appear hard-coded in source either."""
    spec_doc_path = (
        _REPO_ROOT / "docs" / "rebuild" / "spec" / "pos-v2-objectives-spec.md"
    )
    if not spec_doc_path.exists():
        pytest.skip("spec doc absent in this checkout; sentinel scan moot")

    spec_text = spec_doc_path.read_text()
    relevant = [s for s in _FORBIDDEN_SPEC_SENTINELS if s in spec_text]
    if not relevant:
        pytest.skip("none of the chosen sentinels matched the live spec doc")

    for src_file in _WB_SRC_ROOT.rglob("*.py"):
        text = src_file.read_text()
        for sentinel in relevant:
            assert sentinel not in text, (
                f"{src_file} contains spec-doc sentinel {sentinel!r} — "
                "framework-not-content invariant broken."
            )


def test_AC39_6_seed_module_reads_doc_paths_at_runtime() -> None:
    """Structural evidence the seed reads the doc paths at runtime:
    ``tracker_seed.py`` references the workspace-relative paths but
    does not embed the doc content."""
    seed_module = _WB_SRC_ROOT / "adapters" / "tracker_seed.py"
    text = seed_module.read_text()

    # The module must reference the framework value-prop path constant
    # and use the read_text() pattern (i.e., file IO at runtime).
    assert "VALUE_PROPOSITION.md" in text, (
        "tracker_seed.py must reference the framework value-prop path"
    )
    assert ".read_text()" in text, (
        "tracker_seed.py must read the doc from disk, not embed content"
    )

    # Cross-check: the module does not contain VALUE_PROPOSITION.md's
    # H1 prose verbatim.
    assert (
        "pOS v2 — Value Proposition of the Harness and the Primary Persona"
        not in text
    ), (
        "tracker_seed.py contains the canonical VP H1 — must come from the "
        "doc at runtime"
    )


def test_AC39_6_seed_module_reuses_objective_tracker_lift_from_field() -> None:
    """The seed populates ``LiftedFrom`` with the source-doc path —
    structural evidence that the framework-not-content invariant is
    enforced via the schema (provenance pointer), not via embedding
    content in source."""
    seed_module = _WB_SRC_ROOT / "adapters" / "tracker_seed.py"
    text = seed_module.read_text()
    assert "from objective_tracker import" in text
    assert "LiftedFrom" in text, "seed must compose LiftedFrom from #38's API"
    assert "ObjectiveFilter" in text, (
        "seed must use ObjectiveFilter from #38's API for idempotency-by-query"
    )
