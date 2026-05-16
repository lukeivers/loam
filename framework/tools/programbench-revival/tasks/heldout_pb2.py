#!/usr/bin/env python3
"""PB2 held-out anti-overfit check (inputs in NO prompt).

Substitutes a held-out users.json the arm never saw, re-runs the
produced program, and asserts emails.txt now holds the HELD-OUT
addresses — defeating a hardcoded emails.txt. Restores original
state afterward.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

HELD_OUT = ('[{"name": "Di", "email": "di@held.test"}, '
            '{"name": "Ev", "email": "ev@held.test"}]')
HELD_OUT_SET = {"di@held.test", "ev@held.test"}


def _programs() -> list[list[str]]:
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
    if not os.path.exists("users.json"):
        print("HELDOUT-FAIL: no users.json to substitute",
              file=sys.stderr)
        return 1
    orig_users = open("users.json").read()
    orig_emails = (open("emails.txt").read()
                   if os.path.exists("emails.txt") else None)
    try:
        open("users.json", "w").write(HELD_OUT)
        if os.path.exists("emails.txt"):
            os.remove("emails.txt")
        for argv in _programs():
            try:
                subprocess.run(argv, capture_output=True, text=True,
                               timeout=30)
            except Exception:
                continue
            if os.path.exists("emails.txt"):
                got = {ln.strip() for ln in
                       open("emails.txt").read().splitlines()
                       if ln.strip()}
                if got == HELD_OUT_SET:
                    print("HELDOUT-PASS: re-extracted held-out addresses")
                    return 0
        print("HELDOUT-FAIL: produced program did not re-extract on a "
              "held-out input (overfit/hardcoded -> non-pass)",
              file=sys.stderr)
        return 1
    finally:
        open("users.json", "w").write(orig_users)
        if orig_emails is not None:
            open("emails.txt", "w").write(orig_emails)
        elif os.path.exists("emails.txt"):
            os.remove("emails.txt")


if __name__ == "__main__":
    sys.exit(main())
