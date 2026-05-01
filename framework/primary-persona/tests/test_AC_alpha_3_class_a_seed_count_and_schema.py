# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.α.3 — ≥ 5 seed Class A docs covering highest-leverage primitives.

Per plan §4 AC.α.3, at least five files exist under
``docs/rebuild/capability-corpus/claude-code/`` and/or
``docs/rebuild/capability-corpus/harness/``, each satisfying the
Class A schema from AC.α.2:

  - Surface
  - Inputs/outputs
  - Composition notes
  - [user-intent phrasings]  (≥ 3 phrasings)
  - Source  (with source_url + source_fetch_ts populated, non-empty,
    non-placeholder)
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CORPUS_ROOT = REPO_ROOT / "docs" / "rebuild" / "capability-corpus"
CLASS_A_DIRS = (
    CORPUS_ROOT / "claude-code",
    CORPUS_ROOT / "harness",
)


def _class_a_docs() -> list[Path]:
    docs: list[Path] = []
    for d in CLASS_A_DIRS:
        if d.is_dir():
            docs.extend(sorted(d.glob("*.md")))
    return docs


def test_AC_alpha_3_class_a_seed_count_at_least_five():
    docs = _class_a_docs()
    assert len(docs) >= 5, (
        f"AC.α.3 requires ≥ 5 seed Class A docs across "
        f"claude-code/ + harness/; found {len(docs)}: "
        f"{[d.name for d in docs]}"
    )


def test_AC_alpha_3_each_class_a_doc_has_required_sections():
    """Every Class A doc carries the named structural sections."""
    docs = _class_a_docs()
    required_markers = (
        "## Surface",
        "## Inputs/outputs",
        "## Composition notes",
        "## [user-intent phrasings]",
        "## Source",
    )
    for doc in docs:
        body = doc.read_text()
        for marker in required_markers:
            assert marker in body, (
                f"{doc.name}: Class A schema marker {marker!r} missing"
            )


def test_AC_alpha_3_each_class_a_doc_has_three_or_more_phrasings():
    """Each [user-intent phrasings] section carries ≥ 3 bullet
    entries."""
    docs = _class_a_docs()
    for doc in docs:
        body = doc.read_text()
        idx = body.index("## [user-intent phrasings]")
        # Read until next ## heading.
        next_idx = body.find("\n## ", idx + 5)
        if next_idx < 0:
            next_idx = len(body)
        phrasings_section = body[idx:next_idx]
        # Count "- " bullet lines (markdown unordered list items).
        bullets = [
            ln for ln in phrasings_section.splitlines()
            if ln.strip().startswith("- ")
        ]
        assert len(bullets) >= 3, (
            f"{doc.name}: [user-intent phrasings] must list ≥ 3 "
            f"phrasings; found {len(bullets)}"
        )


def test_AC_alpha_3_each_class_a_doc_has_populated_source_block():
    """Each Source block carries non-empty source_url and
    source_fetch_ts fields. Non-placeholder values only — the
    placeholder ``<deferred-to-δ-projection>`` literal is rejected
    per D-OWNER.3 (a) ruling."""
    docs = _class_a_docs()
    placeholder_re = re.compile(r"<\s*deferred-to-")
    for doc in docs:
        body = doc.read_text()
        # Find the Source section.
        idx = body.index("## Source")
        next_idx = body.find("\n## ", idx + 5)
        if next_idx < 0:
            next_idx = len(body)
        src_section = body[idx:next_idx]
        # source_url and source_fetch_ts non-empty + non-placeholder.
        url_match = re.search(r"source_url:\s*(\S.*?)(?:\n|$)", src_section)
        ts_match = re.search(
            r"source_fetch_ts:\s*(\S.*?)(?:\n|$)", src_section
        )
        assert url_match, f"{doc.name}: source_url field missing or empty"
        assert ts_match, f"{doc.name}: source_fetch_ts field missing or empty"
        assert not placeholder_re.search(url_match.group(1)), (
            f"{doc.name}: source_url is placeholder ({url_match.group(1)!r})"
        )
        assert not placeholder_re.search(ts_match.group(1)), (
            f"{doc.name}: source_fetch_ts is placeholder "
            f"({ts_match.group(1)!r})"
        )
        # Timestamp is ISO-8601 (loose check: contains a T and a Z or
        # a digit+colon time component).
        ts = ts_match.group(1).strip()
        assert "T" in ts and ("Z" in ts or "+" in ts or ":" in ts), (
            f"{doc.name}: source_fetch_ts not ISO-8601 ({ts!r})"
        )
