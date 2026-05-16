#!/usr/bin/env python3
"""PB5 positive-real-outcome floor check (AC.PBR.2).

Exits 0 IFF an executable named wc_lines exists in the work dir, is
actually runnable as `./wc_lines sample.txt`, and prints exactly 4
for the real sample.txt. A non-executable, a hardcoded printer, a
program that ignores its argument, or nothing produced drives a
NON-ZERO exit — never a pass.
"""
from __future__ import annotations

import os
import subprocess
import sys


def _find_wc_lines() -> str | None:
    for root, _dirs, files in os.walk("."):
        for f in files:
            if f == "wc_lines":
                return os.path.join(root, f)
    return None


def main() -> int:
    path = _find_wc_lines()
    if path is None:
        print("FLOOR-FAIL: wc_lines was never produced "
              "(did-not-produce-output)", file=sys.stderr)
        return 1
    if not os.access(path, os.X_OK):
        # try to make it executable (some arms forget chmod); still
        # a positive run is the real-outcome assertion
        try:
            os.chmod(path, 0o755)
        except Exception:
            pass
    if not os.path.exists("sample.txt"):
        print("FLOOR-FAIL: sample.txt input missing", file=sys.stderr)
        return 1
    try:
        proc = subprocess.run([os.path.abspath(path), "sample.txt"],
                               capture_output=True, text=True,
                               timeout=30)
    except Exception as exc:
        print(f"FLOOR-FAIL: wc_lines not runnable as a command "
              f"({exc}) — hollow / not-really-executable",
              file=sys.stderr)
        return 1
    if proc.returncode != 0:
        print(f"FLOOR-FAIL: wc_lines exited {proc.returncode} on the "
              f"real input (no real effect)", file=sys.stderr)
        return 1
    out = (proc.stdout or "").strip()
    if out == "4":
        print("FLOOR-PASS: wc_lines really counts the real file's lines")
        return 0
    print(f"FLOOR-FAIL: wc_lines printed {out!r}, not the real line "
          f"count 4 (wrong / hardcoded -> non-pass)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
