"""AC.V040C1.2 — Per-commit ``objectives:`` block populated per
amendment #38 ``LiftedFrom`` schema.

Per cycle-1 plan-doc §4 AC.V040C1.2: each emitted commit in the
produced diff carries an ``objectives:`` block populated with the
amendment #38 ``LiftedFrom`` schema fields (``source_doc``,
``source_ac``, ``source_commit``). The block round-trips through
Pydantic ``LiftedFrom.model_validate`` cleanly.

Per D-build.3 (b): the carrier is the delimited body section
(``---objectives---`` / ``---objectives-end---``).

Per D-build.2 (a): ``source_commit`` is omitted at code-gen time
(``LiftedFrom.source_commit = None``). C2 may explore post-write
rewrite to populate after the commit SHA exists.
"""

from __future__ import annotations

import pytest
import yaml

from loam.objective_tracker.spec import LiftedFrom

from loam_odd_extractor.code_gen import (
    extract_objectives_block,
    persist_diff,
    load_diff,
)
from loam_odd_extractor.code_gen_spec import (
    CodeGenCommit,
    CodeGenDiff,
    CodeGenRequest,
)


def _make_commit(
    *,
    source_doc: str = "objectives.yaml#O.test.1",
    source_ac: str = "G.BACKING.o-test-1",
    source_commit: str | None = None,
    subject: str = "feat: test commit",
) -> CodeGenCommit:
    return CodeGenCommit(
        message_subject=subject,
        message_body="Body line.",
        diff_text="--- a/x\n+++ b/x\n@@ +1 @@\n+x\n",
        lifted_from=LiftedFrom(
            source_doc=source_doc,
            source_ac=source_ac,
            source_commit=source_commit,
        ),
    )


def test_AC_V040C1_2_render_full_message_contains_objectives_delim() -> None:
    """Rendered commit message contains the
    ``---objectives---`` / ``---objectives-end---`` delimiters."""
    c = _make_commit()
    msg = c.render_full_message()
    assert "---objectives---" in msg, (
        "AC.V040C1.2 — commit message must carry "
        "`---objectives---` opening delimiter"
    )
    assert "---objectives-end---" in msg, (
        "AC.V040C1.2 — commit message must carry "
        "`---objectives-end---` closing delimiter"
    )


def test_AC_V040C1_2_block_yaml_round_trip() -> None:
    """The ``objectives:`` block content parses as YAML and
    constructs a valid ``LiftedFrom`` via ``model_validate``."""
    c = _make_commit(
        source_doc="docs/plans/x.md",
        source_ac="AC.X.1",
        source_commit=None,
    )
    msg = c.render_full_message()
    lf = extract_objectives_block(msg)
    assert isinstance(lf, LiftedFrom), (
        "extract_objectives_block must return a LiftedFrom instance"
    )
    assert lf.source_doc == "docs/plans/x.md"
    assert lf.source_ac == "AC.X.1"
    assert lf.source_commit is None


def test_AC_V040C1_2_source_commit_null_per_d_build_2() -> None:
    """Per D-build.2 (a): ``source_commit`` is omitted at code-gen
    time; rendered as YAML scalar ``null``; round-trips as None."""
    c = _make_commit(source_commit=None)
    msg = c.render_full_message()
    assert "source_commit: null" in msg, (
        "D-build.2 (a) requires source_commit rendered as YAML null"
    )
    lf = extract_objectives_block(msg)
    assert lf.source_commit is None, (
        "round-trip must preserve None for source_commit"
    )


def test_AC_V040C1_2_round_trip_via_persist_diff(tmp_path) -> None:
    """End-to-end round-trip: persist_diff → load_diff preserves the
    LiftedFrom payload."""
    c = _make_commit()
    req = CodeGenRequest(
        extraction_id="t",
        extraction_dir=str(tmp_path),
        selected_candidate_gap_id="G.BACKING.o-test-1",
    )
    diff = CodeGenDiff(extraction_id="t", request=req, commits=(c,))
    persist_diff(diff, tmp_path)
    loaded = load_diff(tmp_path)
    assert loaded.commits[0].lifted_from == c.lifted_from


def test_AC_V040C1_2_block_validation_rejects_malformed() -> None:
    """A malformed ``objectives:`` block raises an error (not
    silently absorbed)."""
    from loam_odd_extractor.errors import StageError

    bad_msg = (
        "feat: x\n\n"
        "---objectives---\n"
        "source_doc: ''\n"  # empty source_doc — LiftedFrom rejects
        "source_ac: AC.X.1\n"
        "source_commit: null\n"
        "---objectives-end---\n"
    )
    with pytest.raises(Exception):
        extract_objectives_block(bad_msg)


def test_AC_V040C1_2_block_missing_raises() -> None:
    """A commit message without an ``objectives:`` block raises a
    StageError (the block is required per AC.V040C1.2)."""
    from loam_odd_extractor.errors import StageError

    missing_msg = "feat: x\n\nBody without an objectives block."
    with pytest.raises(StageError):
        extract_objectives_block(missing_msg)
