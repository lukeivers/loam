#!/usr/bin/env python3
"""PB3 positive-real-outcome floor check (AC.PBR.2).

Exits 0 IFF unique.txt exists and is EXACTLY the first-seen-order
dedupe of the real words.txt. A sorted order, the file copied
verbatim, an empty file, or a missing file drives a NON-ZERO exit —
never a pass.
"""
from __future__ import annotations

import os
import sys

# first-seen order of the real words.txt
EXPECTED = ["pear", "apple", "banana", "fig"]


def main() -> int:
    if not os.path.exists("unique.txt"):
        print("FLOOR-FAIL: unique.txt never produced "
              "(did-not-produce-output)", file=sys.stderr)
        return 1
    body = open("unique.txt").read().strip()
    if not body:
        print("FLOOR-FAIL: unique.txt EMPTY (vacuous -> non-pass)",
              file=sys.stderr)
        return 1
    got = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if got == EXPECTED:
        print("FLOOR-PASS: unique.txt is the real first-seen dedupe")
        return 0
    if sorted(got) == sorted(EXPECTED) and got != EXPECTED:
        print(f"FLOOR-FAIL: unique.txt {got} has the right SET but the "
              f"WRONG order (not first-seen; produced-but-wrong)",
              file=sys.stderr)
        return 1
    print(f"FLOOR-FAIL: unique.txt {got} != real first-seen dedupe "
          f"{EXPECTED} (hollow/verbatim/wrong -> non-pass)",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
