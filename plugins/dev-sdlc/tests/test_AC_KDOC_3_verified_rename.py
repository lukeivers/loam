"""AC.KDOC.3 — VERIFIED rename in doctrine (KEEL adoption program Phase 1).

Doctrine defines VERIFIED = ran green at a known SHA; ASSERTED =
assumed-green; the extractor mapping note is present (D4 — the code
enum rename is deferred; the doctrine carries the binding mapping).
Plan: docs/plans/keel-adoption-program.md §5.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC = REPO_ROOT / "plugins" / "dev-sdlc" / "docs" / "odd-methodology.md"


def _flat() -> str:
    return re.sub(r"\s+", " ", SPEC.read_text(encoding="utf-8"))


def test_verified_defined_as_ran_green_at_known_sha() -> None:
    flat = _flat()
    assert "**VERIFIED** — *the check ran green at a known SHA.*" in flat, (
        "doctrine must define VERIFIED = ran green at a known SHA"
    )
    assert "Nothing else earns this word" in flat


def test_asserted_defined_as_assumed_green() -> None:
    assert "**ASSERTED** — assumed-green" in _flat(), (
        "doctrine must define ASSERTED = assumed-green"
    )


def test_extractor_mapping_note_present() -> None:
    flat = _flat()
    assert (
        "the extractor's `VERIFIED` band = the ASSERTED evidence grade"
        in flat
    ), "extractor mapping note (D4) missing from doctrine"
    # The mapping is mirrored where the extractor mechanics now live.
    adapter_doc = (
        REPO_ROOT
        / "plugins" / "dev-sdlc" / "odd-extractor" / "docs"
        / "adapter-conventions.md"
    )
    assert adapter_doc.exists(), "adapter-conventions.md missing"
    assert "ASSERTED" in adapter_doc.read_text(encoding="utf-8"), (
        "adapter-conventions.md must carry the ASSERTED mapping note"
    )
