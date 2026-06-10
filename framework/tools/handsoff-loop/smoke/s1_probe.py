#!/usr/bin/env python3.13
"""S1 measured-prediction probe (plan: general-build-from-intent §Build path).

Prediction under test: on a 6-ask labeled probe (3 seeded-ambiguous /
3 clear): >=1 meaningful question on 3/3 ambiguous, zero questions on
3/3 clear; two reworded same-asks confirm equivalent substance,
non-identical strings.

Live `claude -p` calls through the production understanding stage.
Results print as JSON and append to smoke/s1_probe_results.json.
Run: python3.13 framework/tools/handsoff-loop/smoke/s1_probe.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

from handsoff_loop.request_intent import understand_request  # noqa: E402

# Labeled probe set. Ambiguous asks leave a build-shaping decision
# genuinely open; clear asks pin the data, the operation, and the
# output well enough to build from.
ASKS = [
    ("ambiguous", "can you make something to deal with our files"),
    ("ambiguous", "I need help getting our numbers to match up"),
    ("ambiguous", "build me a thing for the customer stuff"),
    ("clear", "make a command-line tool that reads orders.csv, removes "
              "rows whose 'email' column duplicates an earlier row, and "
              "writes the result to orders_deduped.csv"),
    ("clear", "I want a script that takes a folder of .txt meeting notes "
              "and produces one summary.md listing each file's name and "
              "its first line"),
    # Run-1 calibration note (honest, logged in
    # s1_probe_results_run1.json): this ask originally omitted where
    # the files live and what to do when an invoice_id repeats — the
    # model asked exactly those two build-shaping questions, so the
    # "clear" LABEL was wrong, not the discrimination. Run 2 pins both
    # decisions in the ask wording; run 1 is preserved fails-included.
    ("clear", "build a tool that reads payments.csv and invoices.csv "
              "from the current directory, matches each payment to at "
              "most one invoice where amount and invoice_id are both "
              "equal (first match wins if an invoice_id repeats), and "
              "writes unmatched rows to unmatched_payments.csv and "
              "unmatched_invoices.csv"),
]

REWORD_A = ("merge our three customer spreadsheets into one list "
            "without duplicate people in it")
REWORD_B = ("take the three separate spreadsheets of customers we have "
            "and combine them so each person appears only once")


def main() -> int:
    results = {"probe": "S1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "asks": [], "reword": {}}
    ok = True
    for label, ask in ASKS:
        t0 = time.monotonic()
        intent = understand_request(ask)
        dt = round(time.monotonic() - t0, 1)
        row = {"label": label, "ask": ask, "wall_s": dt,
               "n_questions": len(intent.questions),
               "questions": intent.questions,
               "objective": intent.objective}
        passed = (len(intent.questions) >= 1 if label == "ambiguous"
                  else len(intent.questions) == 0)
        row["passed"] = passed
        ok = ok and passed
        results["asks"].append(row)
        print(json.dumps(row), flush=True)

    a = understand_request(REWORD_A)
    b = understand_request(REWORD_B)
    non_identical = (a.inferred_intent != b.inferred_intent
                     or a.objective != b.objective)
    # Equivalent substance: both speak of customers + duplicates/once.
    sub_a = a.inferred_intent.lower() + " " + a.objective.lower()
    sub_b = b.inferred_intent.lower() + " " + b.objective.lower()
    equivalent = all(
        ("customer" in s) and any(t in s for t in
                                  ("duplicate", "dedupe", "once", "merge",
                                   "combine", "unique"))
        for s in (sub_a, sub_b)
    )
    results["reword"] = {
        "ask_a": REWORD_A, "ask_b": REWORD_B,
        "intent_a": a.inferred_intent, "intent_b": b.inferred_intent,
        "objective_a": a.objective, "objective_b": b.objective,
        "non_identical_strings": non_identical,
        "equivalent_substance": equivalent,
        "passed": non_identical and equivalent,
    }
    ok = ok and non_identical and equivalent
    results["prediction_passed"] = ok

    out = Path(__file__).parent / "s1_probe_results.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"prediction_passed": ok, "written": str(out)}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
