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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.A.2 — frozen unseen done, carried THROUGH the packaging.

Plan: docs/plans/handsoff-loop-real-build.md (§3 AC.A.2)

The acceptance is authored + frozen + hash-pinned BEFORE any
sub-agent and seen by no sub-agent / no per-sub-task judge.  This is
the probe's Tier-0 honesty control, carried forward as a STRUCTURAL
requirement of the packaged mechanism (freeze-before-run + isolation;
not method-bound).

Deterministic.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop.verify import (  # noqa: E402
    FreezeIsolationBreach,
    freeze_acceptance,
)


def test_freeze_pins_hash_and_writes_isolated_path(tmp_path) -> None:
    """freeze_acceptance hash-pins the content + writes a sidecar sha."""
    frozen = freeze_acceptance(
        acceptance_id="acc1",
        content="done when verify_test.py exits 0",
        check_argv=["python3", "verify_test.py"],
        freeze_dir=tmp_path / "_frozen",
    )
    assert frozen.content_sha256
    sidecar = tmp_path / "_frozen" / "acc1.sha256"
    assert sidecar.read_text().strip() == frozen.content_sha256
    # The frozen body is on a dedicated path the orchestrator keeps
    # out of every brief.
    assert Path(frozen.frozen_path).read_text() == frozen.content


def test_leak_into_brief_refuses_not_warns(tmp_path) -> None:
    """If the frozen acceptance leaks into a brief/judge -> refusal.

    A silent pass would be the exact self-report-trust failure the
    probe proved must not happen; refusing is the honest behaviour.
    """
    frozen = freeze_acceptance(
        acceptance_id="acc2",
        content="SECRET-ACCEPTANCE-BODY: rows==3 and avg is float",
        check_argv=["true"],
        freeze_dir=tmp_path / "_frozen",
    )
    leaky_brief = (
        "Build a CSV parser. SECRET-ACCEPTANCE-BODY: rows==3 and avg "
        "is float (so make sure that passes)."
    )
    with pytest.raises(FreezeIsolationBreach):
        frozen.assert_unseen_by(leaky_brief)


def test_clean_briefs_pass_isolation(tmp_path) -> None:
    """Briefs that do NOT contain the frozen body pass the guard."""
    frozen = freeze_acceptance(
        acceptance_id="acc3",
        content="UNSEEN: exact expected aggregate values here",
        check_argv=["true"],
        freeze_dir=tmp_path / "_frozen",
    )
    frozen.assert_unseen_by(
        "Build a correct RFC-4180 CSV parser with type inference.",
        "Sub-task acceptance: quoted-comma field parses correctly.",
    )  # no raise == clean
