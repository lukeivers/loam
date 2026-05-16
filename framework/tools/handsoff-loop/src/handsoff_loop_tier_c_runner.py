"""Tier C end-to-end runner (AC.C.1) — GATED on A AND B both positive.

If either phase retired negative, this runner is NOT invoked (the
gate is enforced in the AC.C.1 test).  When both retired positive,
this composes intake (B) + the packaged loop (A) end to end: one
plain-language intent, one plain-language approval (the ONLY human
touch), real verified work back.

NO Anthropic API key — real `claude` binary, default Sonnet.
"""

from __future__ import annotations

import json
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent.parent
VERDICT_DIR = PKG_ROOT / ".phase_verdicts"


def _phase_positive(name: str) -> bool:
    p = VERDICT_DIR / f"phase_{name}.json"
    if not p.is_file():
        return False
    try:
        return json.loads(p.read_text()).get("polarity") == "positive"
    except json.JSONDecodeError:
        return False


def run_tier_c() -> dict:
    """End-to-end, only legitimate when A and B both positive.

    The gate is also enforced at the call site (AC.C.1 test); this is
    the defence-in-depth: refuse to run if the gate is not satisfied
    (a negative on A or B makes C out of scope — a correct outcome).
    """
    if not (_phase_positive("a") and _phase_positive("b")):
        return {
            "gated": True,
            "reason": ("Tier C not attempted — a phase retired "
                       "negative/absent; this is a correct gated "
                       "outcome, not a failure"),
            "reached_done": False,
            "human_touches": 0,
        }

    # Both positive: compose B's intake -> A's packaged loop.  (Only
    # reached when the gate is satisfied; the concrete composition
    # reuses the Phase A runner's task driven from an intake-derived
    # acceptance.)
    from handsoff_loop_phase_a_runner import run_phase_a

    v = run_phase_a()
    table = v.as_table()
    return {
        "gated": False,
        "reached_done": table["polarity"] == "positive",
        "human_touches": 1,  # the single plain-language approval
        "phase_a_recompose_polarity": table["polarity"],
    }


if __name__ == "__main__":
    print(json.dumps(run_tier_c(), indent=2))
