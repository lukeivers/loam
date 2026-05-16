#!/usr/bin/env python3
"""PB3 held-out anti-overfit check (inputs in NO prompt).

Substitutes a held-out words.txt the arm never saw, re-runs the
produced program, and asserts unique.txt is the HELD-OUT first-seen
dedupe — defeating a hardcoded unique.txt. Restores state afterward.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

HELD_OUT_WORDS = "zed\nyak\nzed\nyak\nwen\nzed\n"
HELD_OUT_DEDUPE = ["zed", "yak", "wen"]


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
    if not os.path.exists("words.txt"):
        print("HELDOUT-FAIL: no words.txt to substitute",
              file=sys.stderr)
        return 1
    orig_words = open("words.txt").read()
    orig_unique = (open("unique.txt").read()
                   if os.path.exists("unique.txt") else None)
    try:
        open("words.txt", "w").write(HELD_OUT_WORDS)
        if os.path.exists("unique.txt"):
            os.remove("unique.txt")
        for argv in _programs():
            try:
                subprocess.run(argv, capture_output=True, text=True,
                               timeout=30)
            except Exception:
                continue
            if os.path.exists("unique.txt"):
                got = [ln.strip() for ln in
                       open("unique.txt").read().splitlines()
                       if ln.strip()]
                if got == HELD_OUT_DEDUPE:
                    print("HELDOUT-PASS: re-deduped held-out input")
                    return 0
        print("HELDOUT-FAIL: produced program did not re-dedupe on a "
              "held-out input (overfit -> non-pass)", file=sys.stderr)
        return 1
    finally:
        open("words.txt", "w").write(orig_words)
        if orig_unique is not None:
            open("unique.txt", "w").write(orig_unique)
        elif os.path.exists("unique.txt"):
            os.remove("unique.txt")


if __name__ == "__main__":
    sys.exit(main())
