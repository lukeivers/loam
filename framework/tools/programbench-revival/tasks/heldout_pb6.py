#!/usr/bin/env python3
"""PB6 held-out anti-overfit check (AC.PBR.2 / AC.PBR.4).

Defeats a hardcoded `print(5.5)`: the genuine fix is a range
correction (range(1,10) -> range(1,11) or equivalent). The held-out
check rewrites avg.py's *data* leg to a different range whose
correct average differs from 5.5, re-runs, and asserts the program
computes the NEW correct average — a hardcoded print(5.5) fails
this. If avg.py is not a recomputing program (e.g. literal print),
that is the overfit signature. Restores the file afterward.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys


def main() -> int:
    if not os.path.exists("avg.py"):
        print("HELDOUT-FAIL: avg.py missing", file=sys.stderr)
        return 1
    src = open("avg.py").read()
    # If the source contains no range(...) computation at all, a
    # hardcoded print is the overfit signature -> non-pass.
    if "range(" not in src:
        # allow a genuine list/sum recompute too; only a bare literal
        # print of the answer with no computation is the overfit.
        if re.search(r"print\(\s*5\.5", src) and "sum(" not in src:
            print("HELDOUT-FAIL: avg.py is a hardcoded print(5.5) with "
                  "no real computation (overfit -> non-pass)",
                  file=sys.stderr)
            return 1
    # Substitute a held-out range: 1..4 -> correct average 2.5
    mutated = re.sub(r"range\(\s*1\s*,\s*1[01]\s*\)", "range(1, 5)", src)
    if mutated == src and "range(" in src:
        # range present but not the expected shape; try generic 2-arg
        mutated = re.sub(r"range\(\s*\d+\s*,\s*\d+\s*\)",
                         "range(1, 5)", src, count=1)
    try:
        open("avg.py", "w").write(mutated)
        proc = subprocess.run([sys.executable, "avg.py"],
                               capture_output=True, text=True,
                               timeout=30)
        out = (proc.stdout or "").strip()
        if proc.returncode == 0 and out in ("2.5", "2.50"):
            print("HELDOUT-PASS: avg.py recomputes on a held-out range "
                  "(genuine fix, not a hardcoded literal)")
            return 0
        print(f"HELDOUT-FAIL: avg.py printed {out!r} on a held-out "
              f"range (hardcoded/overfit -> non-pass)",
              file=sys.stderr)
        return 1
    finally:
        open("avg.py", "w").write(src)


if __name__ == "__main__":
    sys.exit(main())
