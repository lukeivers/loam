"""AC.CH0.1 — Charter genesis (KEEL adoption program Phase 1).

`docs/charter.md` exists; entry #0 carries the founding intent
byte-faithful to the ledger record's verbatim statement, with timestamp
+ source tag + content hash; the genesis/bootstrap exception is
documented in-file. Plan: docs/plans/keel-adoption-program.md §5.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CHARTER = REPO_ROOT / "docs" / "charter.md"

# Verbatim per the ledger record
# 2026-06-10-loam-founding-intent-statement-root-contract.md (pos3
# decisions ledger) — byte-faithful capture is the AC's whole point.
FOUNDING_INTENT = (
    "Make a harness which can run entirely off of the Claude Max "
    "subscription whose purpose is to make a tool for people to more "
    "effectively be hands-off while an AI does the development for them."
)


def test_charter_exists() -> None:
    assert CHARTER.exists(), "docs/charter.md missing (AC.CH0.1)"


def test_entry_0_statement_byte_faithful() -> None:
    text = CHARTER.read_text(encoding="utf-8")
    assert "## Entry #0" in text, "entry #0 heading missing"
    assert FOUNDING_INTENT in text, (
        "founding intent statement is not byte-faithful to the ledger "
        "record's verbatim wording"
    )


def test_entry_0_timestamp_and_source_tag() -> None:
    text = CHARTER.read_text(encoding="utf-8")
    assert "2026-06-10 14:49 CDT" in text, "capture timestamp missing"
    assert "1514355792709685389" in text, (
        "source tag (Discord message id) missing"
    )


def test_entry_0_content_hash_matches_statement() -> None:
    text = CHARTER.read_text(encoding="utf-8")
    m = re.search(r"content-sha256:\*\*\s*`([0-9a-f]{64})`", text)
    assert m, "content-sha256 field missing on entry #0"
    recorded = m.group(1)
    actual = hashlib.sha256(FOUNDING_INTENT.encode("utf-8")).hexdigest()
    assert recorded == actual, (
        f"recorded content hash {recorded} != sha256 of the verbatim "
        f"statement {actual}"
    )


def test_bootstrap_exception_documented() -> None:
    text = CHARTER.read_text(encoding="utf-8")
    assert re.search(r"bootstrap exception", text, re.I), (
        "genesis/bootstrap exception not documented in-file (KEEL b.8.1)"
    )
