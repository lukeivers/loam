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

"""AC.V044.1 — production dispatch-site audit artefact.

Per ``docs/plans/v0-4-4-subagent-personas-routing-and-priming.md``
§4 AC.V044.1: a fresh empirical audit confirms the consumption gap
before any SKILL authoring. The artefact lives at the canonical
path under ``workspace/.scratch/claude-output/`` and carries (a) a
verdict-band line (GREEN / YELLOW / RED), (b) ≥10 audited rows.

Note on path: the artefact is workspace-scratch and may not exist
in fresh clones of the canonical pos-v2 (the workspace `.scratch`
is gitignored). The test gates on the artefact's existence via an
env var so CI doesn't false-fail when the workspace is fresh; the
v0.4.4 build sets the env var while the artefact is on disk.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


CANONICAL_REPO_ROOT = Path(__file__).resolve().parents[3]
ARTEFACT_PATH = (
    CANONICAL_REPO_ROOT
    / "workspace"
    / ".scratch"
    / "claude-output"
    / "v0-4-4-dispatch-site-audit.md"
)

# The artefact is workspace-scratch and gitignored. The build sets
# this env var when running the test against a workspace where the
# artefact exists; CI without the workspace skips the test gracefully
# (matches the AC.V044.5 outcome-probe gating shape).
ENV_VAR = "LOAM_V044_AUDIT_ARTEFACT_PRESENT"


def _artefact_present() -> bool:
    return ARTEFACT_PATH.is_file()


@pytest.mark.skipif(
    not _artefact_present() and os.environ.get(ENV_VAR) != "1",
    reason=(
        f"audit artefact not present at {ARTEFACT_PATH} and "
        f"{ENV_VAR}!=1; skipping. The build that produces the "
        "artefact runs this test with the artefact on disk."
    ),
)
def test_AC_V044_1_audit_artefact_exists() -> None:
    """The audit artefact exists at the canonical path."""
    assert ARTEFACT_PATH.is_file(), (
        f"AC.V044.1: audit artefact must exist at {ARTEFACT_PATH}"
    )


@pytest.mark.skipif(
    not _artefact_present() and os.environ.get(ENV_VAR) != "1",
    reason=(
        f"audit artefact not present at {ARTEFACT_PATH} and "
        f"{ENV_VAR}!=1; skipping."
    ),
)
def test_AC_V044_1_audit_artefact_has_verdict_band() -> None:
    """The audit artefact carries a verdict-band line (GREEN /
    YELLOW / RED)."""
    text = ARTEFACT_PATH.read_text(encoding="utf-8")
    # Verdict band lives in a top-level "## Verdict" section per the
    # AC.V044.1 spec.
    assert "## Verdict" in text, (
        "AC.V044.1: audit artefact must carry a top-level "
        "'## Verdict' section."
    )
    # The verdict-band keyword (one of GREEN / YELLOW / RED) appears
    # in the body so the band is machine-readable.
    band_present = any(
        band in text for band in ("GREEN", "YELLOW", "RED")
    )
    assert band_present, (
        "AC.V044.1: audit artefact must record a verdict band "
        "(GREEN / YELLOW / RED) explicitly."
    )


@pytest.mark.skipif(
    not _artefact_present() and os.environ.get(ENV_VAR) != "1",
    reason=(
        f"audit artefact not present at {ARTEFACT_PATH} and "
        f"{ENV_VAR}!=1; skipping."
    ),
)
def test_AC_V044_1_audit_artefact_has_minimum_rows() -> None:
    """The audit artefact carries ≥10 audited rows.

    Rows are markdown table rows under the dispatch-shape audit
    section; we count by the table-row pipe pattern (`| <n> |`)
    in lines that look like data rows (start with `| ` and contain
    at least 4 columns).
    """
    text = ARTEFACT_PATH.read_text(encoding="utf-8")
    data_rows = [
        line
        for line in text.splitlines()
        if line.startswith("| ")
        and line.count("|") >= 5  # 4+ columns means 5+ pipes
        # Skip header / separator rows.
        and not line.lstrip("| ").startswith("---")
        and "Plan-doc" not in line
        and "Path" not in line
        and "AC.DBT principle" not in line
        and "Work-shape" not in line
    ]
    assert len(data_rows) >= 10, (
        f"AC.V044.1: audit artefact must carry ≥10 audited rows; "
        f"found {len(data_rows)}. (data rows are markdown table "
        "rows in the audit body.)"
    )
