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
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""The loam arm's loop-internal STRUCTURAL done-signal — NOT the
scoring authority.

AC.RPB.1 / AC.RPB.3 / AC.RPB.4 ground-truth isolation: the REAL
positive-real-outcome floor + held-out anti-overfit signal IS the
REAL upstream ``programbench eval`` test suite (the deterministic
graded signal) + the INDEPENDENT held-out judge — applied EXTERNALLY,
AFTER the arm produces its work dir, NEVER seen by either arm. The
real upstream eval is also far too wall-clock-heavy (8-33 min/task
under amd64 emulation, F2 §10.3) to run inside the loop's iteration,
and running it inside would leak ground truth into the loop.

So the loop's ``--frozen check_argv`` (the loop EXECUTES this via
verify.py to decide "done") is this lightweight STRUCTURAL floor: did
the arm actually produce a submission shaped like a real ProgramBench
reverse-engineering attempt — a ``compile.sh`` plus at least one
real source file? It exits 0 ONLY if a real submission scaffold
exists; an empty work dir / a report-only / "I would do X" produces a
non-zero exit so the loop does NOT report a hollow done. This is
deliberately structural, not behavioural: the BEHAVIOURAL truth (does
it actually pass the real upstream tests) is the REAL upstream eval +
the independent judge, the EXTERNAL scoring authority — exactly the
v2 verify.py:213-215 both-must-pass spine, real-PB-bound. A submission
that clears this structural floor but fails the real upstream eval is
``produced-but-no-real-effect`` / ``produced-but-wrong`` by
construction (AC.RPB.6 taxonomy).

Run as: ``python realpb_structural_floor.py`` with CWD = the arm's
work dir. The arm NEVER sees this file or its path (it is passed only
into the loop's frozen spec, kept UNSEEN by the sub-task brief —
FrozenAcceptance.assert_unseen_by, AC.RPB.1).
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    wd = Path.cwd()
    compile_sh = wd / "compile.sh"
    if not compile_sh.is_file():
        print("STRUCTURAL-FLOOR FAIL: no compile.sh produced "
              "(no real reverse-engineering submission scaffold)")
        return 1
    if compile_sh.stat().st_size == 0:
        print("STRUCTURAL-FLOOR FAIL: compile.sh is empty")
        return 1
    # At least one real source file beyond compile.sh (a report-only
    # or empty-scaffold submission is a non-pass by construction).
    source_like = [
        p for p in wd.rglob("*")
        if p.is_file()
        and p.name != "compile.sh"
        and ".git" not in p.parts
        and p.stat().st_size > 0
        and p.suffix.lower() in (
            ".rs", ".go", ".c", ".h", ".cpp", ".cc", ".py", ".js",
            ".ts", ".java", ".zig", ".sh", ".mk", ".toml", ".mod",
            ".cargo", ".lock", ".txt", ".md", ".yaml", ".yml",
            ".json", ".am", ".ac", ".in", ".cmake",
        )
        or p.name in ("Makefile", "makefile", "CMakeLists.txt",
                      "Cargo.toml", "go.mod", "build.sh")
    ]
    if not source_like:
        print("STRUCTURAL-FLOOR FAIL: compile.sh present but no "
              "real source files (report-only / empty scaffold)")
        return 1
    print(f"STRUCTURAL-FLOOR OK: compile.sh + {len(source_like)} "
          f"source file(s) — a real submission scaffold exists "
          f"(the REAL upstream programbench eval + the independent "
          f"held-out judge are the EXTERNAL scoring authority)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
