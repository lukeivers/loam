"""AC.MSLB.1 — the methodology spec admits the AC.RVL.8 cap-bias checklist.

Converted, amendment #197 / AC.BVG.1 (2026-07-09, Class E of the 2026-07-08
release-seal near-miss audit). This guard was born as the record of a
magic-number raise: it pinned the KDOC line budget at ``n <= 380`` (a meta-
assertion on the KDOC test source) and pinned the spec itself at
``360 < n <= 380`` — the same brittle exact-value genus, twice over. Its true
underlying intent was never a line count: the AC.RVL.8 recall-volume reshape
seats a required **cap-bias checklist** (the §7.6 numeric-limit resource check)
in plugins/dev-sdlc/docs/odd-methodology.md, and MSLB.1 exists to guarantee
that content is admitted into the spec.

The line-count mechanism is retired (the KDOC leanness guard now asserts
"no return of the dropped 8-lens sprawl" instead of a ceiling, so pinning a
number here would just re-introduce the treadmill). This guard now asserts the
intent directly: the §7.6 cap-bias anchor is present in the spec. It still
reads the shared doc via a module-level Path constant, so cycle-2's AST
shared-doc-coverage meta-check keeps detecting it as a floored shared-doc
content-guard (kept under the ``test_AC_MSLB_1_*.py`` floor pattern — zero
guard-floor.yaml churn). The §7/§8 authoring + reviewer checklist legs of the
cap-bias line are independently guarded by AC.RVL.8.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC = REPO_ROOT / "plugins" / "dev-sdlc" / "docs" / "odd-methodology.md"


def _flat() -> str:
    return re.sub(r"\s+", " ", SPEC.read_text(encoding="utf-8"))


def test_AC_MSLB_1_cap_bias_checklist_admitted_in_spec() -> None:
    """The §7.6 cap-bias checklist — the AC.RVL.8 content this guard exists to
    admit — is present in the methodology spec. Replaces the retired
    ``360 < n <= 380`` line-count pin (AC.BVG.1)."""
    flat = _flat()
    assert "§7.6 The numeric-limit resource check (cap-bias catch)" in flat, (
        "the AC.RVL.8 cap-bias checklist §7.6 anchor must be admitted into the "
        "methodology spec — it is the content MSLB.1 exists to guarantee"
    )
