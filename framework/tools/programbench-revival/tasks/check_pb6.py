#!/usr/bin/env python3
"""PB6 positive-real-outcome floor check (AC.PBR.2) — the
produced-but-wrong / hollow-fix false-success class.

Exits 0 IFF the REAL avg.py on disk, when executed, prints 5.5. A
file that still prints 4.5, an untouched file, or a new file
elsewhere drives a NON-ZERO exit — never a pass. (The held-out
check separately rejects a hardcoded print(5.5).)
"""
from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    if not os.path.exists("avg.py"):
        print("FLOOR-FAIL: named target avg.py missing "
              "(wrong-target / target-untouched)", file=sys.stderr)
        return 1
    try:
        proc = subprocess.run([sys.executable, "avg.py"],
                               capture_output=True, text=True,
                               timeout=30)
    except Exception as exc:
        print(f"FLOOR-FAIL: avg.py not runnable ({exc})",
              file=sys.stderr)
        return 1
    if proc.returncode != 0:
        print(f"FLOOR-FAIL: avg.py errored ({proc.stderr.strip()[:160]})",
              file=sys.stderr)
        return 1
    out = (proc.stdout or "").strip()
    if out in ("5.5", "5.50"):
        print("FLOOR-PASS: the REAL avg.py now prints the correct "
              "average")
        return 0
    if out in ("4.5", "4.50"):
        print("FLOOR-FAIL: avg.py STILL prints 4.5 — the off-by-one "
              "was NOT actually fixed (target-untouched)",
              file=sys.stderr)
        return 1
    print(f"FLOOR-FAIL: avg.py printed {out!r}, not the correct 5.5 "
          f"(produced-but-wrong -> non-pass)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
