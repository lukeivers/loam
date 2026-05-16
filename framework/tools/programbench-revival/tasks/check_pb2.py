#!/usr/bin/env python3
"""PB2 positive-real-outcome floor check (AC.PBR.2).

Exits 0 IFF emails.txt actually exists in the work dir and contains
exactly the three real extracted addresses, one per line. An empty
emails.txt, a missing file, names instead of emails, or extra junk
drives a NON-ZERO exit (the empty/vacuous-extraction false-success
class) — never a pass.
"""
from __future__ import annotations

import os
import sys

EXPECTED = {"ada@example.com", "bo@example.net", "cy@example.org"}


def main() -> int:
    if not os.path.exists("emails.txt"):
        print("FLOOR-FAIL: emails.txt was never produced "
              "(did-not-produce-output)", file=sys.stderr)
        return 1
    body = open("emails.txt").read().strip()
    if not body:
        print("FLOOR-FAIL: emails.txt is EMPTY (vacuous extraction "
              "is a non-pass by construction)", file=sys.stderr)
        return 1
    lines = {ln.strip() for ln in body.splitlines() if ln.strip()}
    if lines == EXPECTED:
        print("FLOOR-PASS: emails.txt holds exactly the real extracted "
              "addresses")
        return 0
    print(f"FLOOR-FAIL: emails.txt content {sorted(lines)} != the real "
          f"extracted addresses {sorted(EXPECTED)} (wrong / hollow "
          f"extraction -> non-pass)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
