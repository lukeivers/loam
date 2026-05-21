"""FIDRAFT cleanup-on-seal surfacing hook (AC.FBMT1.FCS family).

Post-``loam amend seal`` hook that reads the just-sealed plan-doc,
scans ``docs/FUTURE_IDEAS_DRAFT.md`` for entries whose slug-overlap
with the plan-doc's slug exceeds a confidence threshold, and emits
a structured surfacing payload asking the operator "did you mark
this actioned?". The hook NEVER writes to FIDRAFT — owner-gated edit
by design (AC.FBMT1.FCS.2).

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.FCS family + §14 D-T1.3.MATCH (slug-overlap with loose
~30% token threshold; operator triages false positives).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


# AC.FBMT1.FCS family — slug-overlap heuristic parameters per §14
# D-T1.3.MATCH. Loose threshold optimizes for the cheap-false-
# positive / expensive-false-negative cost asymmetry (the owner-
# gated surface means a false positive costs one "no, that's not
# it" click; a false negative leaves FIDRAFT stale).
SLUG_OVERLAP_THRESHOLD = 0.30

# Stopwords stripped before computing token-overlap. Tokens
# specific to the amendment-lifecycle vocabulary that would
# otherwise inflate overlap across every plan-doc vs every FIDRAFT
# entry. Kept short — every word here is a deliberate noise filter.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "amendment",
        "the",
        "a",
        "an",
        "of",
        "to",
        "in",
        "on",
        "for",
        "at",
        "by",
        "is",
        "and",
        "or",
        "plan",
        "doc",
        "spec",
        "test",
        "tests",
        "loam",
        "pos",
        "v1",
        "v2",
        "v0",
    }
)

# Tokenization: split on non-alphanumeric, lowercase, drop short /
# stop tokens. Mirrors the (deliberately simple) tokenizer in
# ``file_memory._tokenize_for_fts`` — both serve the same lexical-
# overlap shape but in different surfaces.
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Reduce ``text`` to a list of overlap-worthy tokens.

    Per §14 D-T1.3.MATCH: split on ``-_<whitespace>``, lowercase,
    drop tokens shorter than 3 chars, drop stopwords. Returns in
    first-occurrence order with duplicates preserved (so a slug
    that mentions ``memory`` twice contributes twice to the
    overlap count — this matches operator intuition that a FIDRAFT
    entry harping on the same theme as the plan-doc is a stronger
    candidate than one that touches it once in passing).
    """
    out: list[str] = []
    for run in _TOKEN_RE.findall(text):
        tok = run.lower()
        if len(tok) < 3:
            continue
        if tok in _STOPWORDS:
            continue
        out.append(tok)
    return out


def _token_overlap_ratio(plan_tokens: set[str], entry_tokens: set[str]) -> float:
    """Jaccard-style overlap on de-duped token SETS.

    Per §14 D-T1.3.MATCH: "30% token threshold" is the loose
    intersection-over-smaller-set ratio — favours short FIDRAFT
    entries whose every meaningful word also appears in the plan-
    doc slug (a strong signal) over long FIDRAFT entries with one
    shared word out of dozens (a weak signal).

    Returns ``0.0`` when either set is empty (no signal); otherwise
    ``|A ∩ B| / min(|A|, |B|)`` so an entry whose every meaningful
    token is in the slug scores 1.0 regardless of slug length.
    """
    if not plan_tokens or not entry_tokens:
        return 0.0
    intersection = plan_tokens & entry_tokens
    denominator = min(len(plan_tokens), len(entry_tokens))
    return len(intersection) / denominator


@dataclass
class FidraftMatch:
    """One FIDRAFT entry above the overlap threshold.

    ``entry_text`` is the verbatim bullet / paragraph from FIDRAFT
    so the surface payload can quote it; ``score`` is the overlap
    ratio so the operator can prioritise the surface; ``line_no``
    is the 1-indexed line in FIDRAFT for direct lookup.
    """

    entry_text: str
    score: float
    line_no: int


@dataclass
class FidraftCleanupSurface:
    """Structured surfacing payload (AC.FBMT1.FCS.1 + AC.FBMT1.FCS.3).

    ``plan_slug`` identifies the sealed plan-doc; ``matches`` is
    the (possibly empty) list of FIDRAFT entries above the
    overlap threshold, ranked highest-score first. An empty list
    is the no-false-positive AC.FBMT1.FCS.3 outcome — the hook
    fires but the surface text says "no matching entries; nothing
    to clean up".
    """

    plan_slug: str
    matches: list[FidraftMatch] = field(default_factory=list)

    def render(self) -> str:
        """Return the operator-facing surface text.

        Builder's-call output format (AC.FBMT1.FCS.1's verification
        allows stdout / NDJSON / Telegram-reply payload). Plain
        text on a heading + bullet list per match is the simplest
        shape; the seal step prints it to stdout so the operator
        sees it alongside the seal commit's diagnostic output.
        """
        if not self.matches:
            return (
                f"FIDRAFT cleanup surface for '{self.plan_slug}': "
                "no matching entries above threshold; nothing to "
                "clean up."
            )
        lines = [
            f"FIDRAFT cleanup surface for '{self.plan_slug}' — "
            "did you mark these actioned?",
        ]
        for m in self.matches:
            preview = m.entry_text.strip()
            if len(preview) > 200:
                preview = preview[:200] + "…"
            lines.append(
                f"  - [line {m.line_no}, overlap {m.score:.0%}] {preview}"
            )
        return "\n".join(lines)


def _extract_fidraft_entries(text: str) -> list[tuple[int, str]]:
    """Slice FIDRAFT into entry-shaped chunks.

    Per the FIDRAFT format (markdown with section headers + top-
    level bullets that are paragraph-shaped): an entry is a top-
    level bullet (``- ``-prefixed) plus any indented continuation
    lines. Headers + free prose between bullets are NOT entries
    (they're section dividers / context).

    Returns ``(line_no, entry_text)`` tuples (1-indexed line_no
    pointing at the bullet's first line).
    """
    entries: list[tuple[int, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("- ") or ln.startswith("* "):
            start = i
            buf = [ln]
            j = i + 1
            while j < len(lines):
                child = lines[j]
                # Continuation: indented line, or a blank line
                # immediately followed by an indented line. Anything
                # else closes the entry.
                if child.startswith("  ") or child.startswith("\t"):
                    buf.append(child)
                    j += 1
                    continue
                if child == "" and j + 1 < len(lines) and (
                    lines[j + 1].startswith("  ")
                    or lines[j + 1].startswith("\t")
                ):
                    buf.append(child)
                    j += 1
                    continue
                break
            entries.append((start + 1, "\n".join(buf)))
            i = j
            continue
        i += 1
    return entries


def scan_fidraft(
    *,
    plan_slug: str,
    fidraft_path: Path,
    threshold: float = SLUG_OVERLAP_THRESHOLD,
) -> FidraftCleanupSurface:
    """Scan ``fidraft_path`` for entries matching ``plan_slug``.

    Returns the structured surfacing payload (possibly empty
    matches list). When ``fidraft_path`` does not exist, returns
    an empty-matches surface — a workspace without FIDRAFT
    surfaces no entries (AC.FBMT1.FCS.3 no-false-positive).

    AC.FBMT1.FCS.2 is structurally upheld: this function only
    READS ``fidraft_path``; it never writes.
    """
    surface = FidraftCleanupSurface(plan_slug=plan_slug)
    if not fidraft_path.exists():
        return surface
    plan_tokens = set(_tokenize(plan_slug))
    if not plan_tokens:
        return surface
    try:
        text = fidraft_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return surface
    entries = _extract_fidraft_entries(text)
    for line_no, entry_text in entries:
        entry_tokens = set(_tokenize(entry_text))
        score = _token_overlap_ratio(plan_tokens, entry_tokens)
        if score >= threshold:
            surface.matches.append(
                FidraftMatch(
                    entry_text=entry_text,
                    score=score,
                    line_no=line_no,
                )
            )
    surface.matches.sort(key=lambda m: m.score, reverse=True)
    return surface


def plan_slug_from_path(plan_doc_path: Path) -> str:
    """Extract the plan-slug from a ``docs/plans/<slug>.md`` path.

    The slug is the filename stem; the directory is stripped
    (sealed plan-docs at ``docs/plans/sealed/<slug>.md`` resolve
    to the same slug as in-flight plans at
    ``docs/plans/<slug>.md``).
    """
    return plan_doc_path.stem
