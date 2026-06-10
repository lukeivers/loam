"""AC.KDOC.S — outcome-altitude cold walk (KEEL adoption program Phase 1).

Against the live repo with no pre-arranged state, a scripted honesty
sweep (grep-class, production doc paths) finds ZERO live-doc claims of:
(a) ODD novelty, (b) active write-time gating, (c) VERIFIED-without-run,
(d) Outcomes-equivalence — and finds Charter #0 + AC.PO.1/2 resolvable
from docs/charter.md and docs/VALUE_PROPOSITION.md alone.

outcome-altitude: true — the sweep walks the real docs tree as shipped;
nothing is staged, mocked, or pre-arranged. Plan:
docs/plans/keel-adoption-program.md §5 (and §10.2 names the honest
limitation: this is the strongest MECHANICAL outcome check available
for a docs-only amendment; prose quality is owner-gate-reviewed).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXCLUDED_PREFIXES = ("docs/archive/", "docs/plans/sealed/")

FOUNDING_INTENT = (
    "Make a harness which can run entirely off of the Claude Max "
    "subscription whose purpose is to make a tool for people to more "
    "effectively be hands-off while an AI does the development for them."
)


def _live_docs() -> list[Path]:
    files = list((REPO_ROOT / "docs").rglob("*.md"))
    files += list((REPO_ROOT / "plugins").glob("*/docs/**/*.md"))
    files += list((REPO_ROOT / "plugins").glob("*/odd-extractor/docs/**/*.md"))
    return [
        p
        for p in files
        if not p.relative_to(REPO_ROOT).as_posix().startswith(
            EXCLUDED_PREFIXES
        )
    ]


def _doctrine_docs() -> list[Path]:
    """Doctrine surfaces for the write-time-gating leg (the AC's
    'doctrine half'): docs root + docs/design + plugins/*/docs."""
    out: list[Path] = list((REPO_ROOT / "docs").glob("*.md"))
    out += list((REPO_ROOT / "docs" / "design").rglob("*.md"))
    out += list((REPO_ROOT / "plugins").glob("*/docs/**/*.md"))
    return out


def _offenders(files: list[Path], pattern: re.Pattern) -> list[str]:
    hits = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in pattern.finditer(text):
            rel = p.relative_to(REPO_ROOT).as_posix()
            hits.append(f"{rel}: {m.group(0)[:60]}")
    return hits


def test_sweep_a_zero_odd_novelty_claims() -> None:
    pats = [
        re.compile(r"ODD is genuinely new"),
        re.compile(r"not in (?:my|the) training data", re.I),
        re.compile(
            r"(?:ODD|Objective-Driven Design) (?:is|was)"
            r"[^.\n]{0,40}unprecedented",
            re.I,
        ),
    ]
    hits = [h for pat in pats for h in _offenders(_live_docs(), pat)]
    assert hits == [], f"novelty claims live: {hits}"


def test_sweep_b_zero_active_write_time_gating_claims() -> None:
    pat = re.compile(r"objective_binding_gate|tdd_guard")
    hits = _offenders(_doctrine_docs(), pat)
    assert hits == [], f"doctrine references archived write-time gates: {hits}"


def test_sweep_c_zero_verified_without_run_claims() -> None:
    """Any live doc carrying the test-pass-assumption phrasing must
    also carry the ASSERTED mapping (the doctrine §6 honesty rule)."""
    pat = re.compile(
        r"assumption that (?:the )?tests? (?:in the repo were )?"
        r"pass(?:ed|ing)|grants `VERIFIED`"
    )
    offenders = []
    for p in _live_docs():
        text = p.read_text(encoding="utf-8", errors="ignore")
        if pat.search(text) and "ASSERTED" not in text:
            offenders.append(p.relative_to(REPO_ROOT).as_posix())
    assert offenders == [], (
        f"VERIFIED-without-run claims without the ASSERTED mapping: "
        f"{offenders}"
    )


def test_sweep_d_zero_outcomes_equivalence_claims() -> None:
    # Lookbehind excludes quoted mentions of the retracted wording.
    pat = re.compile(r'(?<!["“])equivalent (?:or stronger )?guarantees')
    hits = _offenders(_live_docs(), pat)
    assert hits == [], f"Outcomes-equivalence overclaims live: {hits}"


def test_charter_0_resolvable_from_charter_file_alone() -> None:
    charter = (REPO_ROOT / "docs" / "charter.md").read_text(encoding="utf-8")
    assert "## Entry #0" in charter
    assert FOUNDING_INTENT in charter
    m = re.search(r"content-sha256:\*\*\s*`([0-9a-f]{64})`", charter)
    assert m, "entry #0 content hash missing"
    assert m.group(1) == hashlib.sha256(
        FOUNDING_INTENT.encode("utf-8")
    ).hexdigest()


def test_ac_po_resolvable_from_value_proposition_alone() -> None:
    vp = (REPO_ROOT / "docs" / "VALUE_PROPOSITION.md").read_text(
        encoding="utf-8"
    )
    assert re.search(r"### AC\.PO\.1", vp), "AC.PO.1 not resolvable"
    assert re.search(r"### AC\.PO\.2", vp), "AC.PO.2 not resolvable"
    assert "Charter entry #0" in vp, (
        "AC.PO derivation from Charter #0 not stated"
    )
