# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.2 (P1) — the critic seed contains artifact + objective + methodology
+ protocol ONLY, and EXCLUDES the author's world (self-assessment,
enthusiasm, provenance)."""
from __future__ import annotations

from adversarial_review.seed import (
    BLOCK_ARTIFACT,
    BLOCK_METHODOLOGY,
    BLOCK_OBJECTIVE,
    BLOCK_PROTOCOL,
    ReviewInputs,
    derive_seed,
    diff_seed,
    strip_provenance,
)


def _inputs(artifact: str) -> ReviewInputs:
    return ReviewInputs(
        artifact=artifact,
        objective="ship a correct thing",
        methodology="the failure taxonomy",
        protocol="premortem stance",
    )


def test_AC_AR_2_seed_has_the_four_allowlisted_blocks():
    inputs = _inputs("artifact body line one")
    # The protocol block is seeded in the derive phase; objective +
    # methodology + artifact in the diff phase. Together the four
    # allow-listed blocks are the ONLY seed sources.
    dseed = derive_seed(inputs)
    fseed = diff_seed(inputs, "derived spec")
    assert BLOCK_PROTOCOL in dseed
    assert BLOCK_OBJECTIVE in fseed
    assert BLOCK_METHODOLOGY in fseed
    assert BLOCK_ARTIFACT in fseed


def test_AC_AR_2_provenance_and_enthusiasm_stripped():
    artifact = (
        "Author: Jane Doe\n"
        "The team is really excited about this proposal.\n"
        "Self-assessment: we think this is our best work.\n"
        "The actual substantive claim is that revenue grows 12%.\n"
    )
    seed = diff_seed(_inputs(artifact), "spec")
    # The author's world is gone...
    assert "Jane Doe" not in seed
    assert "really excited" not in seed
    assert "best work" not in seed
    # ...but the substance is preserved.
    assert "revenue grows 12%" in seed


def test_AC_AR_2_strip_provenance_keeps_substance():
    text = "we are proud of this\nthe load calc uses g=9.81\n"
    stripped = strip_provenance(text)
    assert "proud" not in stripped
    assert "g=9.81" in stripped
