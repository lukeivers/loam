"""AC.MSLB.1 — the methodology-spec line budget admits the cap-bias checklist.

Amendment dev-sdlc-kdoc-methodology-line-budget-raise (rides the v1.11.0 cut).

The recall-volume reshape's AC.RVL.8 seats a required cap-bias checklist
(§7.6 numeric-limit resource check + reviewer checklist item 15) in
plugins/dev-sdlc/docs/odd-methodology.md. That legitimately-required content
grew the spec past the old KDOC ≤360 line guard (to 373). Per
feedback_loose_AC_text_fix_AC_not_implementation the numeric bound is the
too-tight AC — not the content — so it was raised 360 → 380.

This test pins the raise so it is ODD §2.5-traceable: the guard bound is now
380 (the raise happened), it is not left unbounded (still catches real bloat),
and the doc carries the §7.6 cap-bias anchor that justified the raise (the raise
is content-driven, not a blanket loosening).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KDOC_TEST = (
    REPO_ROOT
    / "plugins"
    / "dev-sdlc"
    / "tests"
    / "test_AC_KDOC_1_methodology_rewrite.py"
)
SPEC = REPO_ROOT / "plugins" / "dev-sdlc" / "docs" / "odd-methodology.md"


def test_kdoc_line_budget_raised_to_380() -> None:
    """The KDOC guard asserts ≤ 380 — the raise landed; the old 360 bound is gone."""
    src = KDOC_TEST.read_text(encoding="utf-8")
    assert re.search(r"n\s*<=\s*380\b", src), (
        "KDOC line-count guard should assert `n <= 380` after the AC.MSLB.1 raise"
    )
    assert not re.search(r"assert\s+n\s*<=\s*360\b", src), (
        "the old `assert n <= 360` bound must be replaced, not left alongside"
    )


def test_budget_still_catches_real_bloat() -> None:
    """The raise is bounded — not unbounded. 380 stays tight enough to catch
    real (dozens-of-lines) return of the dropped 8-lens sprawl."""
    src = KDOC_TEST.read_text(encoding="utf-8")
    m = re.search(r"n\s*<=\s*(\d+)\b", src)
    assert m is not None, "no numeric line-count bound found in the KDOC guard"
    bound = int(m.group(1))
    assert 360 < bound <= 400, (
        f"line budget {bound} should be a small headroom raise over 360, "
        f"not an effectively-unbounded loosening"
    )


def test_raise_is_justified_by_the_cap_bias_checklist() -> None:
    """The §7.6 cap-bias checklist (AC.RVL.8) — the content that necessitated
    the raise — is present in the spec, and the spec is now in the (360, 380]
    band the raise was made for (so the raise was necessary and sufficient)."""
    spec = SPEC.read_text(encoding="utf-8")
    flat = re.sub(r"\s+", " ", spec)
    assert "§7.6 The numeric-limit resource check (cap-bias catch)" in flat, (
        "the AC.RVL.8 cap-bias checklist §7.6 anchor should be present — it is "
        "the content that justified raising the budget"
    )
    n = len(spec.splitlines())
    assert 360 < n <= 380, (
        f"spec is {n} lines — the raise targets the (360, 380] band; if the spec "
        f"is ≤360 the raise was unnecessary, if >380 the guard should catch it"
    )
