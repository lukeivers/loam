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

"""AC.A.3 — independent + adversarial verification through the packaging.

Plan: docs/plans/handsoff-loop-real-build.md (§3 AC.A.3)

The "done" verdict is an INDEPENDENT tool-executing check on the
produced artefact (sub-agent self-reports NOT trusted) PLUS an
anti-overfit check on inputs absent from every brief + judge.  Both
carried THROUGH the packaging.  Satisfiable by any independent-judge
+ held-out-input design (not method-bound).

Deterministic (the check commands here are trivial stand-ins; the
real-task independent+anti-overfit run is the AC.A.4 phase end-test).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop.verify import freeze_acceptance, verify  # noqa: E402


def test_independent_check_decides_not_self_report(tmp_path) -> None:
    """`done` is the independent check's exit code, never a self-report.

    The sub-agent could claim success; verify() never reads that — it
    runs the check and keys off the exit code only.
    """
    work = tmp_path / "work"
    work.mkdir()
    # Primary check passes (exit 0); no held-out.
    frozen = freeze_acceptance(
        acceptance_id="a3a", content="x",
        check_argv=["true"], freeze_dir=tmp_path / "_f",
    )
    r = verify(frozen, work_dir=work)
    assert r.done is True and r.primary_exit == 0


def test_primary_pass_but_anti_overfit_fail_is_negative(tmp_path) -> None:
    """Both checks must pass; held-out failing -> definite NEGATIVE.

    Guards the overfit-to-fixtures failure: an artefact that passes
    the brief's examples but fails fresh held-out inputs is NOT done.
    """
    work = tmp_path / "work"
    work.mkdir()
    frozen = freeze_acceptance(
        acceptance_id="a3b", content="x",
        check_argv=["true"],            # primary passes
        held_out_argv=["false"],        # anti-overfit FAILS
        freeze_dir=tmp_path / "_f",
    )
    r = verify(frozen, work_dir=work)
    assert r.done is False, "anti-overfit failure must yield NOT done"
    assert r.held_out_exit != 0
    # Evidence is carried (D-NEG-DEPTH: evidence, not root-cause).
    ev = r.as_evidence()
    assert ev["done"] is False and ev["held_out_exit"] != 0


def test_freeze_mutation_after_author_is_refused(tmp_path) -> None:
    """If the frozen acceptance is mutated post-freeze -> refusal.

    Tier-0 integrity: verify() re-reads the on-disk freeze and
    refuses on sha mismatch rather than verifying against a changed
    target.
    """
    import pytest

    from handsoff_loop.verify import FreezeIsolationBreach

    work = tmp_path / "work"
    work.mkdir()
    fdir = tmp_path / "_f"
    frozen = freeze_acceptance(
        acceptance_id="a3c", content="ORIGINAL",
        check_argv=["true"], freeze_dir=fdir,
    )
    # Tamper with the frozen file after authoring.
    (fdir / "a3c.frozen").write_text("TAMPERED")
    with pytest.raises(FreezeIsolationBreach):
        verify(frozen, work_dir=work)
