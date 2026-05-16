#!/usr/bin/env python3
"""PB1 held-out anti-overfit check (AC.PBR.2 / AC.PBR.4).

Inputs here appear in NO prompt. Writes a held-out sales.csv whose
real total differs from the one in the task statement, re-runs the
produced program against it, and asserts the program computes the
NEW total — defeating a hardcoded 120.74. Restores the original
file afterward so the floor check (run order independent) still sees
the real input.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

HELD_OUT_CSV = "date,amount\n2026-02-01,3.00\n2026-02-02,4.50\n2026-02-03,2.50\n"
HELD_OUT_TOTAL = "10.0"  # 3.00 + 4.50 + 2.50 = 10.00


def _candidate_programs() -> list[list[str]]:
    cands: list[list[str]] = []
    for p in sorted(glob.glob("*.py")):
        b = os.path.basename(p)
        if b.startswith("check_") or b.startswith("heldout_"):
            continue
        cands.append([sys.executable, p])
    for p in sorted(glob.glob("*.sh")):
        cands.append(["bash", p])
    for p in sorted(glob.glob("*")):
        if os.path.isfile(p) and os.access(p, os.X_OK) and "." not in p:
            cands.append([os.path.abspath(p)])
    return cands


def main() -> int:
    if not glob.glob("sales.csv"):
        print("HELDOUT-FAIL: no sales.csv to substitute", file=sys.stderr)
        return 1
    original = open("sales.csv").read()
    try:
        open("sales.csv", "w").write(HELD_OUT_CSV)
        for argv in _candidate_programs():
            try:
                proc = subprocess.run(argv, capture_output=True,
                                       text=True, timeout=30)
            except Exception:
                continue
            if proc.returncode != 0:
                continue
            out = (proc.stdout or "").strip().replace("$", "")
            if out.rstrip("0").rstrip(".") == "10":
                print(f"HELDOUT-PASS: {argv} recomputed held-out total")
                return 0
        print("HELDOUT-FAIL: program did not recompute on a held-out "
              "input (hardcoded / overfit -> non-pass)", file=sys.stderr)
        return 1
    finally:
        open("sales.csv", "w").write(original)


if __name__ == "__main__":
    sys.exit(main())
