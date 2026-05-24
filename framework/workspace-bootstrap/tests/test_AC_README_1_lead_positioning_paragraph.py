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

"""AC.README.1 — Lead positioning paragraph + italicised pitch present.

Per docs/plans/readme-restructure-decision-doc-positioning.md §6:
the README's content between the H1 title and the first H2 is a
single paragraph between 55 and 80 words inclusive, followed by an
italicised blockquote one-line pitch.

Structural shape test (STUB-class per the AC ladder; outcome-altitude
coverage is AC.README.3). Method-in-AC test passed: multiple
phrasings of the lead within the word budget satisfy the AC.

Companion seal-test (test_no_sealed_amendments.py) admits README.md
as a universal-file in the workspace-bootstrap fence; this test
co-locates with the FBE / CLE / E family AC tests in the same
component anchor per the readme-restructure manifest fence decision.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
README = REPO_ROOT / "README.md"


def _lead_region_lines() -> list[str]:
    """Return README lines between H1 (`# loam`) and the first H2."""
    lines = README.read_text().split("\n")
    h1_idx = next(
        (i for i, line in enumerate(lines) if line.startswith("# ")), None
    )
    h2_idx = next(
        (i for i, line in enumerate(lines) if line.startswith("## ")), None
    )
    assert h1_idx is not None, "README.md missing H1 heading"
    assert h2_idx is not None, "README.md missing any H2 heading"
    assert h1_idx < h2_idx, "first H2 must follow H1"
    return lines[h1_idx + 1 : h2_idx]


def _lead_paragraph_text(region: list[str]) -> str:
    """Return the first non-blockquote paragraph as a single string."""
    para_lines: list[str] = []
    in_para = False
    for line in region:
        if line.startswith("> "):
            continue
        if line.strip() == "":
            if in_para:
                break
            continue
        para_lines.append(line.strip())
        in_para = True
    return " ".join(para_lines)


def test_lead_paragraph_word_count_in_budget() -> None:
    """The lead positioning paragraph carries 55-80 words inclusive."""
    region = _lead_region_lines()
    para = _lead_paragraph_text(region)
    word_count = len(para.split())
    assert 55 <= word_count <= 80, (
        f"AC.README.1: lead paragraph word count {word_count} outside "
        f"[55, 80] budget per D-README.LEAD ratification. Lead text: "
        f"{para[:120]}..."
    )


def test_lead_region_contains_italicised_pitch_blockquote() -> None:
    """The H1-to-first-H2 region contains an italicised blockquote pitch.

    The italicised one-line pitch (current `> **One-line pitch:** ...`)
    is preserved verbatim as the post-paragraph anchor per Surface #1.
    Test: the lead region contains at least one blockquote line
    (lines starting with `> `).
    """
    region = _lead_region_lines()
    blockquote_lines = [line for line in region if line.startswith("> ")]
    assert len(blockquote_lines) >= 1, (
        "AC.README.1: lead region must contain an italicised pitch "
        "blockquote (line starting with `> `). Found 0 blockquote "
        "lines in the H1-to-first-H2 region."
    )
