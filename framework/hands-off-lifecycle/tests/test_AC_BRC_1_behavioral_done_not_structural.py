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

"""AC.BRC.1 — terminal "done" requires a BEHAVIOURAL self-check, NOT
structural presence and NOT a trivial `true`.

Outcome under test (not method): the loop's in-loop "done" signal,
when behavioural-gated, is a self-constructed FUNCTIONAL check derived
from the plain-language objective that EXERCISES the produced artefact
— such that a submission which is structurally present (a compile.sh +
a source file exist) but does NOT behave as the objective describes is
NOT reported done, and a check satisfied by running `true` / a no-op
does NOT satisfy this AC.  This test is deterministic (no real claude):
it drives the constructed behavioural command against (a) an absent
probe, (b) a no-op probe, (c) a structural-only probe, (d) a probe
that actually exercises the artefact — and asserts the sentinel
polarity is behavioural, not structural.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop.behavioral_selfcheck import (  # noqa: E402
    build_behavioral_check_command,
)
from handsoff_loop.goal_drive import (  # noqa: E402
    DONE_SENTINEL,
    NOT_DONE_SENTINEL,
)


def _run(cmd: str, wd: Path) -> tuple[int, str]:
    p = subprocess.run(
        ["sh", "-c", cmd], cwd=str(wd),
        capture_output=True, text=True, timeout=60,
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def test_AC_BRC_1_behavioural_check_is_derived_from_intent() -> None:
    spec = build_behavioral_check_command(
        objective="produce a script `r.sh` that prints HELLO",
        work_dir="/unused",
    )
    # The directive carries the plain-language objective and the
    # behavioural-evidence requirement (not structural presence).
    d = spec.directive()
    assert "produce a script `r.sh` that prints HELLO" in d
    assert "RUN / EXERCISED" in d
    assert "structurally present" in d  # explicitly insufficient


def test_AC_BRC_1_absent_probe_is_not_done(tmp_path: Path) -> None:
    """Structural absence of behavioural evidence -> NOT done."""
    spec = build_behavioral_check_command(
        objective="anything", work_dir=str(tmp_path))
    rc, out = _run(spec.command(), tmp_path)
    assert rc != 0
    assert NOT_DONE_SENTINEL in out
    assert DONE_SENTINEL not in out


def test_AC_BRC_1_no_op_probe_does_not_satisfy(tmp_path: Path) -> None:
    """A `true` / no-op probe does NOT satisfy AC.BRC.1."""
    for body in ("true\n", ":\n", "exit 0\n", "#!/bin/sh\ntrue\n"):
        (tmp_path / "loam_behavioral_selfcheck.sh").write_text(body)
        spec = build_behavioral_check_command(
            objective="x", work_dir=str(tmp_path))
        rc, out = _run(spec.command(), tmp_path)
        assert rc != 0, f"no-op probe {body!r} wrongly accepted"
        assert NOT_DONE_SENTINEL in out
        assert DONE_SENTINEL not in out


def test_AC_BRC_1_structural_present_but_wrong_is_not_done(
    tmp_path: Path,
) -> None:
    """Structurally present (compile.sh + a source file) but the
    behaviour is wrong -> NOT done (the exact gap closed)."""
    (tmp_path / "compile.sh").write_text("echo build\n")
    (tmp_path / "main.py").write_text("print('WRONG')\n")
    # The behavioural probe exercises the artefact and asserts the
    # OBSERVABLE effect the objective requires (prints RIGHT).
    (tmp_path / "loam_behavioral_selfcheck.sh").write_text(
        "out=$(python3 main.py); [ \"$out\" = RIGHT ]\n"
    )
    spec = build_behavioral_check_command(
        objective="main.py prints RIGHT", work_dir=str(tmp_path))
    rc, out = _run(spec.command(), tmp_path)
    assert rc != 0, "structurally-present-but-wrong wrongly done"
    assert NOT_DONE_SENTINEL in out


def test_AC_BRC_1_behaviourally_correct_is_done(
    tmp_path: Path,
) -> None:
    """The artefact actually behaves as the objective describes ->
    done (positive polarity of the SAME behavioural gate)."""
    (tmp_path / "compile.sh").write_text("echo build\n")
    (tmp_path / "main.py").write_text("print('RIGHT')\n")
    (tmp_path / "loam_behavioral_selfcheck.sh").write_text(
        "out=$(python3 main.py); [ \"$out\" = RIGHT ]\n"
    )
    spec = build_behavioral_check_command(
        objective="main.py prints RIGHT", work_dir=str(tmp_path))
    rc, out = _run(spec.command(), tmp_path)
    assert rc == 0, out
    assert DONE_SENTINEL in out
    assert NOT_DONE_SENTINEL not in out
