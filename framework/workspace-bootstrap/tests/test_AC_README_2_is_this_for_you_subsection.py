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

"""AC.README.2 — `### Is this for you?` subsection present under Why.

Per docs/plans/readme-restructure-decision-doc-positioning.md §6:
the README contains an H3 `### Is this for you?` heading positioned
immediately after the `## Why` section's lead content and before the
`## Quickstart` H2. The subsection body contains exactly three
bold-led reader-segment blocks; each block contains the strings
"You'll want loam if" AND "You probably won't want loam if"
(case-insensitive, whitespace-normalised — the test handles wrapped
prose where the signal phrase may span a soft line break).

Structural shape test (STUB-class per the AC ladder; outcome-altitude
coverage is AC.README.3). Method-in-AC test passed: alternative
segment cuts and prose satisfy the AC as long as the YES + NO signal
phrases land per block.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
README = REPO_ROOT / "README.md"

H3_HEADING = "### Is this for you?"
WHY_HEADING = "## Why"
QUICKSTART_HEADING = "## Quickstart"
YES_SIGNAL = "you'll want loam if"
NO_SIGNAL = "you probably won't want loam if"


def _readme_lines() -> list[str]:
    return README.read_text().split("\n")


def _heading_line_index(lines: list[str], heading: str) -> int:
    for i, line in enumerate(lines):
        if line.strip() == heading:
            return i
    raise AssertionError(f"README.md missing heading: {heading!r}")


def _subsection_region(lines: list[str]) -> list[str]:
    """Return lines from H3 (exclusive) through the next ## (exclusive)."""
    h3_idx = _heading_line_index(lines, H3_HEADING)
    qs_idx = _heading_line_index(lines, QUICKSTART_HEADING)
    assert h3_idx < qs_idx, (
        f"AC.README.2: `{H3_HEADING}` (line {h3_idx + 1}) must precede "
        f"`{QUICKSTART_HEADING}` (line {qs_idx + 1})."
    )
    return lines[h3_idx + 1 : qs_idx]


def test_h3_subsection_positioned_between_why_and_quickstart() -> None:
    """H3 `### Is this for you?` sits between `## Why` and `## Quickstart`."""
    lines = _readme_lines()
    why_idx = _heading_line_index(lines, WHY_HEADING)
    h3_idx = _heading_line_index(lines, H3_HEADING)
    qs_idx = _heading_line_index(lines, QUICKSTART_HEADING)
    assert why_idx < h3_idx < qs_idx, (
        f"AC.README.2: section order violated. "
        f"## Why at line {why_idx + 1}; "
        f"### Is this for you? at line {h3_idx + 1}; "
        f"## Quickstart at line {qs_idx + 1}. "
        f"Required: ## Why < ### Is this for you? < ## Quickstart."
    )


def test_subsection_contains_three_bold_led_segment_blocks() -> None:
    """The H3 subsection body contains exactly three bold-led blocks."""
    lines = _readme_lines()
    region = _subsection_region(lines)
    bold_block_count = sum(
        1 for line in region if re.match(r"^\*\*[^*]+\*\*", line)
    )
    assert bold_block_count == 3, (
        f"AC.README.2: expected exactly 3 bold-led reader-segment blocks "
        f"in `{H3_HEADING}` subsection, found {bold_block_count}. "
        f"Per D-README.AUDIENCE-SEGMENTS ratification: non-technical / "
        f"Claude Code power-user / contributor-researcher."
    )


def test_subsection_carries_yes_and_no_signal_phrases_three_times_each() -> None:
    """Each segment block carries a YES + NO signal phrase.

    Whitespace-normalised + lowercased to accommodate prose wrapping
    that may split the signal phrase across a soft line break (the AC
    spec explicitly allows case-insensitive matching).
    """
    lines = _readme_lines()
    region = _subsection_region(lines)
    normalised = " ".join("\n".join(region).split()).lower()

    yes_count = normalised.count(YES_SIGNAL)
    no_count = normalised.count(NO_SIGNAL)

    assert yes_count == 3, (
        f"AC.README.2: expected exactly 3 occurrences of YES-signal "
        f"phrase {YES_SIGNAL!r} in `{H3_HEADING}` subsection, "
        f"found {yes_count}. Each of the 3 reader-segment blocks must "
        f"carry a YES signal."
    )
    assert no_count == 3, (
        f"AC.README.2: expected exactly 3 occurrences of NO-signal "
        f"phrase {NO_SIGNAL!r} in `{H3_HEADING}` subsection, "
        f"found {no_count}. Each of the 3 reader-segment blocks must "
        f"carry a NO signal."
    )
