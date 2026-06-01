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

"""AC.FMG-LIVE.1 — the catalogue refresh re-derives the companion on the
existing recurring cadence.

The refresh is a `loam guards --refresh` invocation: it re-derives the
catalogue + gap status from ground truth and regenerates the human-readable
companion (never hand-edited). It composes on loam's EXISTING recurring
maintenance/pruning cadence (it is one item that flow runs), NOT a net-new
scheduler — so this AC verifies the refresh ITEM exists + is idempotent +
generated-not-hand-maintained, the property the cadence relies on.
"""

from __future__ import annotations

from pathlib import Path

from loam.protection_matrix.check import (
    render_companion_doc,
    run_coverage_check,
)
from loam_cli.cli import main as loam_main


def test_refresh_regenerates_the_companion_from_the_catalogue(
    tmp_path: Path,
) -> None:
    """`loam guards --refresh --out` regenerates the companion doc; exit 0."""
    out = tmp_path / "protection-matrix.md"
    rc = loam_main(["guards", "--refresh", "--out", str(out)])
    assert rc == 0
    assert out.is_file()
    body = out.read_text(encoding="utf-8")
    assert "GENERATED" in body  # the do-not-hand-edit banner.
    assert "DO NOT hand-edit" in body
    # The gaps are carried into the generated companion (the actionable
    # output is exposed in plain language).
    assert "## The gaps" in body


def test_refresh_is_idempotent_regenerating_yields_identical_bodies(
    tmp_path: Path,
) -> None:
    """Re-running the refresh on an unchanged catalogue yields identical text.

    The cadence relies on this: a generated-not-hand-maintained companion has
    no second drift surface, so a refresh is a pure re-derivation.
    """
    report = run_coverage_check()
    a = render_companion_doc(report)
    b = render_companion_doc(report)
    assert a == b


def test_companion_is_generated_not_hand_maintained() -> None:
    """The shipped companion carries the generated banner (no hand-edit)."""
    report = run_coverage_check()
    companion = report.repo_root / "docs" / "design" / "protection-matrix.md"
    assert companion.is_file(), (
        "the generated companion must be committed at "
        "docs/design/protection-matrix.md"
    )
    text = companion.read_text(encoding="utf-8")
    assert "GENERATED" in text
    assert "DO NOT hand-edit" in text
