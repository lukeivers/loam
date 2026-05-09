"""Post-ship review + next-scope decision (AC.V060.6).

Per the post-ship review discipline (Telegram 10577 / 10629 / 10633),
after every successful publish the CLI surfaces a "Next-scope
proposal" block:

1. **Re-evaluate roadmap priorities** — read
   ``docs/release-roadmap.md`` §4 (priority queue) plus recent
   ``docs/FUTURE_IDEAS_DRAFT.md`` captures so the operator sees
   what's queued.
2. **Decide the next scope** — pick the next bounded purpose; name
   what's IN that scope (objective + named ACs / fence + class).
3. **Major-release eval** — pre-1.0 always returns PATCH/MINOR; the
   v1.0 quality-bar event is a separate ratification per
   ``release-versioning-policy.md`` §1.0.0. Post-1.0, scan
   accumulated commits for breaking-change markers + plugin-contract
   revision evidence; surface trigger evidence to operator.
4. **Surface the decision** — emit the proposal block to stdout;
   operator ratifies (or revises) before next cycle's first commit.

The block is deterministic + read-only — it inspects the docs +
emits a summary; it does NOT mutate any file or branch the next
cycle. Operator ratification is the next-cycle's first action,
not this verb's responsibility.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NextScopeProposal:
    """Read-only summary of the post-ship review block.

    ``major_eval`` is one of ``"pre-1.0"`` (no major possible),
    ``"post-1.0-no-trigger"`` (no major-worthy boundary detected),
    or ``"post-1.0-trigger"`` (operator should consider major; full
    evidence in ``major_eval_detail``).
    """

    next_objective: str
    next_class: str
    next_ac_or_fence: str
    queue_excerpt: str
    fidraft_recent: str
    major_eval: str
    major_eval_detail: str


_PRE_1_0_PATTERN = re.compile(r"^v0\.")


def _read_roadmap_priority_queue(repo_root: Path) -> tuple[str, str, str, str]:
    """Return ``(next_objective, next_class, next_fence, queue_excerpt)``.

    Walks ``docs/release-roadmap.md`` §4 (mapped versions) for the
    first entry whose objective sentence is named. The current
    roadmap shape lists entries as ``### v0.X.Y — <objective>``
    headings under ``## §4`` — the first such heading after §4 is
    the next-scope candidate.

    Returns four placeholder strings when the roadmap is absent or
    the §4 section can't be located. The CLI still emits the
    proposal block; the operator notices the placeholder and
    investigates.
    """
    path = repo_root / "docs" / "release-roadmap.md"
    if not path.exists():
        return (
            "(roadmap not found)",
            "(roadmap not found)",
            "(roadmap not found)",
            "(roadmap not found)",
        )
    body = path.read_text(encoding="utf-8")
    sec_match = re.search(
        r"(?ms)^##\s*§4\b[^\n]*\n(.*?)(?=^##\s|\Z)", body
    )
    if sec_match is None:
        return (
            "(no §4 mapped-versions section)",
            "(no §4 mapped-versions section)",
            "(no §4 mapped-versions section)",
            "(no §4 mapped-versions section)",
        )
    sec = sec_match.group(1)
    # First ### heading naming the next entry.
    head_match = re.search(
        r"(?m)^###\s+(v[0-9][0-9.]*)\s*[—-]\s*(.+)$", sec
    )
    if head_match is None:
        return (
            "(no entries in §4)",
            "(no entries in §4)",
            "(no entries in §4)",
            sec[:600],
        )
    next_version = head_match.group(1)
    next_objective = head_match.group(2).strip()
    # Class hint = "MINOR" by default for first §4 entry; operator
    # ratifies. (Per Q2 ratification: class is suggestive on roadmap;
    # plan-author rules at build-time.)
    next_class = "MINOR (plan-author rules at build-time)"
    next_fence = (
        f"see docs/release-roadmap.md §4 entry for {next_version}"
    )
    # Quote first 600 chars of the §4 body as the queue excerpt.
    queue_excerpt = sec[:600].rstrip() + ("\n…" if len(sec) > 600 else "")
    return next_objective, next_class, next_fence, queue_excerpt


def _read_fidraft_recent(repo_root: Path, max_chars: int = 800) -> str:
    """Return the last *max_chars* chars of
    ``docs/FUTURE_IDEAS_DRAFT.md`` so recent captures surface in the
    proposal block.

    Returns a placeholder when the file is missing.
    """
    path = repo_root / "docs" / "FUTURE_IDEAS_DRAFT.md"
    if not path.exists():
        return "(FUTURE_IDEAS_DRAFT.md not found)"
    body = path.read_text(encoding="utf-8")
    if len(body) <= max_chars:
        return body
    # Snip from the last entry boundary (``- **`` is the canonical
    # FIDRAFT entry-start marker).
    tail = body[-max_chars:]
    boundary = tail.find("- **")
    return tail[boundary:] if boundary >= 0 else tail


def _major_release_eval(version: str) -> tuple[str, str]:
    """Return ``(verdict, detail)`` for the major-release eval.

    Pre-1.0 (``v0.*``): always pre-1.0, no major possible.
    Post-1.0: heuristic placeholder (the v1.0 + post-1.0 surface is
    NOT yet shipped; this branch lands when v1.0 ships; a more-
    sophisticated post-1.0 evaluator can replace this stub then).
    """
    if _PRE_1_0_PATTERN.match(version):
        return (
            "pre-1.0",
            (
                "Pre-1.0 release; never cuts major per "
                "`release-versioning-policy.md` §1.0.0. The v1.0 "
                "quality-bar event is a separate ratification, not a "
                "post-publish-trigger event."
            ),
        )
    # Placeholder for post-1.0 evaluation. The post-1.0 evaluator
    # ships when v1.0 itself is in flight; until then, surface the
    # version + invite operator review.
    return (
        "post-1.0-review-needed",
        (
            f"Post-1.0 ({version}); the post-1.0 major-release evaluator "
            "is not yet shipped. Operator review: scan accumulated "
            "commits since the last major for breaking-change markers "
            "+ plugin-contract revision evidence; consider major bump "
            "if cumulative state warrants per "
            "`release-versioning-policy.md`."
        ),
    )


def build_proposal(repo_root: Path, version: str) -> NextScopeProposal:
    """Inspect the docs + assemble the next-scope proposal."""
    next_objective, next_class, next_fence, queue_excerpt = (
        _read_roadmap_priority_queue(repo_root)
    )
    fidraft_recent = _read_fidraft_recent(repo_root)
    major_eval, major_eval_detail = _major_release_eval(version)
    return NextScopeProposal(
        next_objective=next_objective,
        next_class=next_class,
        next_ac_or_fence=next_fence,
        queue_excerpt=queue_excerpt,
        fidraft_recent=fidraft_recent,
        major_eval=major_eval,
        major_eval_detail=major_eval_detail,
    )


def format_proposal(p: NextScopeProposal) -> str:
    """Render the proposal block as a single string for stdout."""
    lines: list[str] = []
    lines.append("== Next-scope proposal ==")
    lines.append("")
    lines.append(f"Next objective: {p.next_objective}")
    lines.append(f"Class hint: {p.next_class}")
    lines.append(f"Fence: {p.next_ac_or_fence}")
    lines.append("")
    lines.append("Major-release eval: " + p.major_eval)
    lines.append("  " + p.major_eval_detail)
    lines.append("")
    lines.append("--- §4 priority queue excerpt ---")
    lines.append(p.queue_excerpt)
    lines.append("")
    lines.append("--- FUTURE_IDEAS_DRAFT.md recent captures ---")
    lines.append(p.fidraft_recent)
    lines.append("")
    lines.append(
        "Operator ratifies (or revises) the next scope BEFORE "
        "the next cycle's first commit."
    )
    return "\n".join(lines)
