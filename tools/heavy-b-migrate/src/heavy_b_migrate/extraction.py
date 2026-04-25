"""Markdown / regex helpers shared across Phase β / γ extractors.

The extractors are deliberately regex-based, not full markdown parsers.
The corpus they target (proposal.md + amendment-*.md) is hand-authored
markdown with predictable shapes per the post-#22 plan template; a
parser is overkill, and a parser-driven approach would fail just as
hard on the pre-#22 plans the placeholder convention exists to handle.

The shape they recognise:

- A "## ACX.Y" / "### ACX.Y" header (or "AC.X.Y" / "ACX.Y - title")
  introduces an acceptance-criterion block; the body until the next
  header at the same or higher level is the criterion text.
- A bullet of the form "- **AC.D-pa.1 — name.**" or "**AC1: title.**"
  may also count as an AC anchor for plans that lay out ACs as
  bullets rather than headers.

When neither shape matches, the extractor returns an empty list and
the caller falls back to a placeholder record per AC.D-mig.5.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedAC:
    """One acceptance criterion lifted from a markdown source.

    ``ac_id`` — the AC label as written (e.g. "AC29.1", "D1", "AC.D-pa.2").
    ``title`` — the short header / first-line summary.
    ``body`` — the prose body of the criterion (may be empty).
    """

    ac_id: str
    title: str
    body: str


# Match AC anchors of several shapes seen across the corpus:
#   "## ACX.Y — name" / "### ACX.Y — name"
#   "## AC.X.Y — name"
#   "## AC.D-pa.1 — name"
#   "## ACX.Y: name"
# Components proposals also use plain "D1." / "A20." numbering as
# shorthand; they appear as bullets in the proposal headers section.
_HEADER_AC_RE = re.compile(
    r"^(?P<hashes>#{2,4})\s+"
    r"(?P<label>(?:AC[\.\-]?[A-Za-z0-9\.\-]+|[A-Z]\d{1,3}))"
    r"\s*[—\-:.]+\s*"
    r"(?P<title>.+?)\s*$",
    re.MULTILINE,
)

# Bullet-form AC anchor:
#   "- **AC.D-pa.1 — name.**"
#   "* **D1.** - description"
_BULLET_AC_RE = re.compile(
    r"^\s*[-*]\s+\*\*"
    r"(?P<label>(?:AC[\.\-]?[A-Za-z0-9\.\-]+|[A-Z]\d{1,3}))"
    r"\s*[—\-:.]+\s*(?P<title>.+?)\.?\s*\*\*",
    re.MULTILINE,
)


def extract_acs_from_markdown(text: str) -> list[ExtractedAC]:
    """Return every parseable AC anchor inside the markdown text.

    Tries header-form first (most common for amendment plans); if no
    header-form ACs are found, tries bullet-form (older proposal
    layouts). Returns the list in document order.

    The function is deterministic + side-effect-free; callers wrap the
    result with their own placeholder-fallback logic.
    """
    found: list[ExtractedAC] = []

    # Header-form pass.
    matches = list(_HEADER_AC_RE.finditer(text))
    if matches:
        for i, m in enumerate(matches):
            label = m.group("label").strip()
            if not _looks_like_ac_label(label):
                continue
            title = m.group("title").strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            found.append(ExtractedAC(ac_id=label, title=title, body=body))
        if found:
            return found

    # Bullet-form fallback.
    for m in _BULLET_AC_RE.finditer(text):
        label = m.group("label").strip()
        if not _looks_like_ac_label(label):
            continue
        title = m.group("title").strip()
        # Bullet-form rarely has a long body; just capture the line.
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        if line_end == -1:
            line_end = len(text)
        body = text[line_start:line_end].strip()
        found.append(ExtractedAC(ac_id=label, title=title, body=body))

    return found


# A label looks like an AC if it contains a digit (so "Definitions" or
# similar header tokens drop out). Single-letter-plus-digit ("D1", "A20")
# qualifies; "AC29.1", "AC.D-pa.2", and "AC.PO.1" all qualify.
_HAS_DIGIT_RE = re.compile(r"\d")


def _looks_like_ac_label(label: str) -> bool:
    if not _HAS_DIGIT_RE.search(label):
        return False
    # Reject labels that obviously aren't AC-shaped (too long, contains
    # spaces).
    if " " in label or len(label) > 32:
        return False
    return True


def truncate_for_goal(text: str, max_len: int = 200) -> str:
    """Single-line summary for the goal field. Strips markdown markers,
    collapses whitespace, truncates."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = cleaned.lstrip("# *-").strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[: max_len - 3].rstrip() + "..."
    if not cleaned:
        cleaned = "(no extractable summary)"
    return cleaned
