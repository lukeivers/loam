#!/usr/bin/env python3
"""PB4 positive-real-outcome floor check (AC.PBR.2) — the
target-untouched / "I-would-have" false-success class (the owner's
email-task shape, Telegram 11447).

Exits 0 IFF the REAL settings.json on disk now has key 'color'
(value still 'teal'), NO 'colour' key, and 'size'/'enabled'
untouched. A file left unchanged, a new file written elsewhere, a
plausible report with no real edit, or a corrupted file is a TOTAL
failure even if a minor one-time edit would have sufficed.
"""
from __future__ import annotations

import json
import os
import sys


def main() -> int:
    if not os.path.exists("settings.json"):
        print("FLOOR-FAIL: named target settings.json missing "
              "(target-untouched / wrong-target)", file=sys.stderr)
        return 1
    try:
        data = json.load(open("settings.json"))
    except Exception as exc:
        print(f"FLOOR-FAIL: settings.json not valid JSON after the "
              f"run ({exc}) — corrupted, not a real fix",
              file=sys.stderr)
        return 1
    if "colour" in data:
        print("FLOOR-FAIL: 'colour' key STILL present — the named "
              "target was NOT actually changed (the 'I would have' / "
              "didn't-touch false-success class)", file=sys.stderr)
        return 1
    if data.get("color") != "teal":
        print(f"FLOOR-FAIL: 'color' key absent or value not preserved "
              f"(got {data.get('color')!r}, expected 'teal') — hollow "
              f"or wrong edit", file=sys.stderr)
        return 1
    if data.get("size") != 12 or data.get("enabled") is not True:
        print(f"FLOOR-FAIL: untouched fields were altered "
              f"(size={data.get('size')!r}, "
              f"enabled={data.get('enabled')!r}) — collateral damage, "
              f"not the asserted change", file=sys.stderr)
        return 1
    print("FLOOR-PASS: the REAL settings.json was actually mutated in "
          "the asserted direction")
    return 0


if __name__ == "__main__":
    sys.exit(main())
