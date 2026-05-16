#!/usr/bin/env python3
"""PB5 held-out anti-overfit check (inputs in NO prompt).

Writes a held-out file with a different line count the arm never
saw, runs `wc_lines` against it, and asserts it prints the NEW
count — defeating a hardcoded 4 / argument-ignoring program.
"""
from __future__ import annotations

import os
import subprocess
import sys

HELD_OUT = "one\ntwo\nthree\nfour\nfive\nsix\nseven\n"  # 7 lines


def _find_wc_lines() -> str | None:
    for root, _dirs, files in os.walk("."):
        for f in files:
            if f == "wc_lines":
                return os.path.join(root, f)
    return None


def main() -> int:
    path = _find_wc_lines()
    if path is None:
        print("HELDOUT-FAIL: wc_lines not produced", file=sys.stderr)
        return 1
    if not os.access(path, os.X_OK):
        try:
            os.chmod(path, 0o755)
        except Exception:
            pass
    held = "_heldout_pb5_input.txt"
    open(held, "w").write(HELD_OUT)
    try:
        proc = subprocess.run([os.path.abspath(path), held],
                               capture_output=True, text=True,
                               timeout=30)
        out = (proc.stdout or "").strip()
        if proc.returncode == 0 and out == "7":
            print("HELDOUT-PASS: wc_lines counted a held-out file")
            return 0
        print(f"HELDOUT-FAIL: wc_lines printed {out!r} on a held-out "
              f"7-line file (hardcoded/arg-ignoring -> non-pass)",
              file=sys.stderr)
        return 1
    finally:
        if os.path.exists(held):
            os.remove(held)


if __name__ == "__main__":
    sys.exit(main())
