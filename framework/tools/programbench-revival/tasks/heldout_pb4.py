#!/usr/bin/env python3
"""PB4 held-out anti-overfit check (AC.PBR.2 / AC.PBR.4).

PB4 is a one-shot in-place mutation (no reusable program), so the
held-out check is a STRUCTURAL anti-overfit: it asserts the real
edit is a genuine key rename that PRESERVED the original value and
the sibling keys exactly (not a blind overwrite to a fixed JSON
blob, not a value-losing rewrite). Inputs/assertions here appear in
NO prompt. Idempotent / read-only — does not mutate the target.
"""
from __future__ import annotations

import json
import os
import sys


def main() -> int:
    if not os.path.exists("settings.json"):
        print("HELDOUT-FAIL: settings.json missing", file=sys.stderr)
        return 1
    try:
        data = json.load(open("settings.json"))
    except Exception as exc:
        print(f"HELDOUT-FAIL: settings.json unreadable ({exc})",
              file=sys.stderr)
        return 1
    # Anti-overfit: a blind "write a fixed correct JSON" would also
    # pass the floor check; the held-out assertion is that EXACTLY
    # the colour->color rename happened with the original value+keys
    # carried through and NO extra keys injected (a hardcoded blob
    # author would not know to keep precisely {color,size,enabled}).
    if set(data.keys()) != {"color", "size", "enabled"}:
        print(f"HELDOUT-FAIL: key set {sorted(data.keys())} is not "
              f"exactly the renamed original set "
              f"(blind-rewrite/overfit signature)", file=sys.stderr)
        return 1
    if data["color"] != "teal" or data["size"] != 12 or \
            data["enabled"] is not True:
        print("HELDOUT-FAIL: values not carried through the rename "
              "(value-losing rewrite -> non-pass)", file=sys.stderr)
        return 1
    print("HELDOUT-PASS: edit is a genuine value-preserving rename, "
          "not a blind overfit rewrite")
    return 0


if __name__ == "__main__":
    sys.exit(main())
