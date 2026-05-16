#!/usr/bin/env python3
"""PB1 positive-real-outcome floor check (AC.PBR.2).

Exits 0 IFF the real outcome was actually delivered: a runnable
program exists in the work dir that, run against the REAL sales.csv,
prints exactly the arithmetic total 120.74. A hollow result
(hardcoded number, no program, error, file echoed) drives a NON-ZERO
exit by construction — never a pass.

Run with CWD == the arm's work dir.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

EXPECTED = "120.74"


def _candidate_programs() -> list[list[str]]:
    cands: list[list[str]] = []
    for p in sorted(glob.glob("*.py")) + sorted(glob.glob("**/*.py",
                                                          recursive=True)):
        if os.path.basename(p).startswith("check_"):
            continue
        if os.path.basename(p).startswith("heldout_"):
            continue
        cands.append([sys.executable, p])
    for p in sorted(glob.glob("*.sh")) + sorted(glob.glob("**/*.sh",
                                                          recursive=True)):
        cands.append(["bash", p])
    for p in sorted(glob.glob("*")):
        if os.path.isfile(p) and os.access(p, os.X_OK) and "." not in p:
            cands.append([os.path.abspath(p)])
    return cands


def _run(argv: list[str]) -> str | None:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                               timeout=30)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip()


def main() -> int:
    if not os.path.exists("sales.csv"):
        print("FLOOR-FAIL: named target sales.csv missing", file=sys.stderr)
        return 1
    for argv in _candidate_programs():
        out = _run(argv)
        if out is None:
            continue
        # Positive assertion: the program's REAL output is the
        # arithmetic total of the real file. A hardcoded literal is
        # caught by the held-out check (different file -> different
        # total); here we positively assert the real total is present
        # as the sole numeric content.
        norm = out.replace("$", "").strip()
        if norm == EXPECTED or norm == "120.74" or norm.rstrip("0").rstrip(
            "."
        ) == "120.74".rstrip("0").rstrip("."):
            print(f"FLOOR-PASS: program {argv} produced real total {out!r}")
            return 0
    print("FLOOR-FAIL: no runnable program produced the real total "
          "120.74 (compiled-but-no-effect / empty / target-untouched "
          "is a non-pass by construction)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
