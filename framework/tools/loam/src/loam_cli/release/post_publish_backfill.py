"""Post-publish state backfill (AC.BACKFL.{1,2,3,4} + AC.BACKFL2.{1,2,3,4}).

After ``loam release`` pushes branch + tag, the version's rows in
``docs/STATE.md`` and ``docs/release-roadmap.md`` need to flip from
"SHIPPED LOCAL — owner gates publish" → "SHIPPED PUBLIC at tag <name>
(annotated <SHA>)" so downstream agents reading STATE.md see ground
truth instead of a stale-claim. Prior to v0.7.3 this was a manual
backfill commit per publish (recurring miss at v0.6.0 / v0.7.0 /
v0.7.1 / v0.7.2). v0.7.3 closes the obvious surface by wiring this
module into :mod:`loam_cli.release.runner` between the tag-push step
and the post-ship review step.

v0.7.4 closes the 4 residual gaps surfaced by v0.7.3's own publish
dogfood (commit ``88964cb``): the leading bolded title in STATE.md
(``**vX.Y.Z PATCH SHIPPED LOCAL**``) was never flipped to
``**...SHIPPED PUBLIC**``; STATE.md ``seal TBD-AT-SEAL`` was left
untouched (only the roadmap row got the TBD-AT-* backfill);
``TBD-AT-COMMIT`` and ``TBD-AT-APPLY`` were left manual because
v0.7.3 D-BACKFL.1.b deferred them as not-discoverable-from-runner-
inputs. v0.7.4 adds a leading-title flip, mirrors the TBD-AT-*
backfill to STATE.md, and discovers source-edit + apply SHAs by
walking the commit graph from the seal commit (path-B per
AC.BACKFL2.3 ruling).

Public callable: :func:`apply_backfill`. Returns a
:class:`BackfillResult` carrying the edits-applied count + the
files-touched list + the idempotent-noop flag (True when the rows
already carry the SHIPPED-PUBLIC marker for this version + no
residual TBD-AT-* placeholders + no residual SHIPPED-LOCAL
title).
"""

from __future__ import annotations

import datetime as _dt
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from loam_cli.release import gates


# --------------------------------------------------------------------
# Result dataclass.
# --------------------------------------------------------------------


@dataclass(frozen=True)
class BackfillResult:
    """Aggregated result of one :func:`apply_backfill` call.

    ``edits_applied`` is the count of distinct edits made (STATE.md
    trailing-claim flip + roadmap row marker append + summary line
    update + §3 entry append, summed). ``files_touched`` lists the
    paths the call wrote. ``idempotent_noop`` is True iff the call
    detected already-current state for both files + made no edits.
    ``state_md_edit`` and ``roadmap_edit`` carry human-readable
    before/after summaries used by ``--dry-run`` previews + the
    post-publish stdout report.
    """

    edits_applied: int
    files_touched: list[Path] = field(default_factory=list)
    idempotent_noop: bool = False
    state_md_edit: str | None = None
    roadmap_edit: str | None = None
    summary_edit: str | None = None
    section_3_edit: str | None = None
    hints: list[str] = field(default_factory=list)


# --------------------------------------------------------------------
# STATE.md trailing-claim flip (AC.BACKFL.1 part 1).
# --------------------------------------------------------------------


def _shipped_local_pattern(version: str) -> re.Pattern[str]:
    """Match the canonical ``<version> SHIPPED LOCAL — owner gates
    publish.`` trailing-claim sentence (and its em-dash / hyphen
    variants) anywhere in the STATE.md bullet body.

    Per D-BACKFL.1.a — verified shape from ``f0ae00c`` diff
    (the v0.7.2 post-publish backfill commit).
    """
    return re.compile(
        r"\b"
        + re.escape(version)
        + r"\s+SHIPPED LOCAL\s*[—\-]\s*[^.\n]+\."
    )


def _already_public_in_state_md(body: str, version: str) -> bool:
    """True iff *body* carries a ``**<version> SHIPPED PUBLIC`` marker
    (the post-backfill shape this module emits).
    """
    pattern = re.compile(
        r"\*\*"
        + re.escape(version)
        + r"\s+SHIPPED PUBLIC\b"
    )
    return pattern.search(body) is not None


def _format_state_md_replacement(
    version: str, today: _dt.date, tag: str, sha7: str
) -> str:
    """Build the ``**<version> SHIPPED PUBLIC ... **.`` replacement
    sentence in the canonical shape verified at f0ae00c.
    """
    return (
        f"**{version} SHIPPED PUBLIC {today.isoformat()} at tag "
        f"`{tag}` (annotated `{sha7}`)**."
    )


def _remove_stale_interim_sentence(
    body: str, version: str
) -> tuple[str, str | None]:
    """When the SHIPPED-PUBLIC marker for *version* is already present
    AND a stale ``<version> SHIPPED LOCAL — owner gates publish.``
    trailing sentence still lingers, remove the stale sentence (plus
    any single preceding whitespace character) so the row reads
    coherently.

    Per AC.RBHCB.1 (F-FUNC-2 closure) — v0.5.0's row at v0.8.0
    AC.HONEST.5 needed this manually; the v0.7.4 helper's
    idempotence-by-skip path correctly avoided double-flipping but
    didn't clean up the stale interim sentence left over from when
    the public-marker landed manually before v0.7.3's auto-backfill
    existed.

    Returns ``(new_body, edit_summary)``; *edit_summary* is None if
    the trigger condition didn't fire (no stale sentence present).
    The caller is expected to have already verified
    :func:`_already_public_in_state_md` returned True.
    """
    pattern = _shipped_local_pattern(version)
    match = pattern.search(body)
    if match is None:
        return body, None
    start = match.start()
    end = match.end()
    # Trim a single preceding whitespace character (typically the
    # space separating the stale sentence from the prior sentence)
    # so the row reads coherently after removal. Defensive: only
    # trim if the prior char is whitespace (' ' / '\t'); never
    # trim a newline (would join two list items).
    if start > 0 and body[start - 1] in (" ", "\t"):
        start -= 1
    new_body = body[:start] + body[end:]
    edit_summary = (
        f"STATE.md: removed stale interim sentence "
        f"{match.group(0)!r} (SHIPPED-PUBLIC marker already present)"
    )
    return new_body, edit_summary


def _backfill_state_md(
    body: str, version: str, today: _dt.date, tag: str, tag_sha: str
) -> tuple[str, str | None]:
    """Apply the SHIPPED-LOCAL → SHIPPED-PUBLIC trailing-claim flip
    to *body*. Returns ``(new_body, edit_summary)`` where
    *edit_summary* is None if the body was unchanged (already public
    AND no stale interim sentence; OR pattern not matched).

    Two paths:

    1. **Pre-public** — no SHIPPED-PUBLIC marker yet for *version*:
       flip the SHIPPED-LOCAL trailing-claim sentence to the
       SHIPPED-PUBLIC marker (canonical v0.7.3 behavior).
    2. **Already-public + stale interim** — SHIPPED-PUBLIC marker
       already present AND the stale ``<version> SHIPPED LOCAL —
       owner gates publish.`` interim sentence still lingers: remove
       the stale sentence (per AC.RBHCB.1 / F-FUNC-2 closure).

    Idempotent across both paths: re-run on a fully-cleaned body is
    a no-op (no public-marker-yet path: still no match; already-public
    + cleaned: the interim-removal helper finds no match either).
    """
    if _already_public_in_state_md(body, version):
        # AC.RBHCB.1 — clean up any stale interim sentence left from
        # a manually-landed public marker (v0.5.0 / v0.8.0 AC.HONEST.5
        # pattern). Idempotent when no stale sentence remains.
        return _remove_stale_interim_sentence(body, version)
    pattern = _shipped_local_pattern(version)
    match = pattern.search(body)
    if match is None:
        return body, None
    sha7 = tag_sha[:7]
    replacement = _format_state_md_replacement(version, today, tag, sha7)
    new_body = body[: match.start()] + replacement + body[match.end():]
    edit_summary = (
        f"STATE.md: replaced {match.group(0)!r} → {replacement!r}"
    )
    return new_body, edit_summary


# --------------------------------------------------------------------
# v0.7.4 — STATE.md leading-title flip (AC.BACKFL2.1).
# --------------------------------------------------------------------


def _leading_title_pattern(version: str) -> re.Pattern[str]:
    """Match the bolded leading title in a STATE.md row.

    Two recognized shapes:

    1. **Canonical form** (v0.7.4 AC.BACKFL2.1): ``**<version>
       <CLASS> SHIPPED LOCAL**`` where ``<CLASS>`` is ``MINOR`` /
       ``PATCH`` / ``minor`` / ``patch`` (case-insensitive —
       historical rows use both casings; v0.7.3 uses ``PATCH``,
       v0.5.0 uses ``minor``).

    2. **Date-in-title variant** (v0.10.2 AC.SMLTV.1): ``**<version>
       SHIPPED LOCAL <YYYY-MM-DD>**`` (date in bolded title; no
       class keyword between version and SHIPPED). Historical
       v0.4.2 STATE.md row uses this shape; F-FUNC-1 capture
       (2026-05-10) framed the extension.

    Per D-BACKFL2.1.a + D-SMLTV.2 — the regex uses alternation so
    one match yields either a CLASS keyword (canonical) or a date
    (variant); the replacement preserves whichever is matched.
    """
    return re.compile(
        r"\*\*"
        + re.escape(version)
        + r"(?:"
        + r"\s+(?P<cls>MINOR|PATCH|minor|patch)\s+SHIPPED LOCAL"
        + r"|"
        + r"\s+SHIPPED LOCAL\s+(?P<date>\d{4}-\d{2}-\d{2})"
        + r")"
        + r"\*\*"
    )


def _state_md_title_already_public(body: str, version: str) -> bool:
    """True iff the STATE.md leading title is already
    ``**<version> <CLASS> SHIPPED PUBLIC**`` (canonical) OR
    ``**<version> SHIPPED PUBLIC <YYYY-MM-DD>**`` (date-in-title
    variant per AC.SMLTV.3).
    """
    pattern = re.compile(
        r"\*\*"
        + re.escape(version)
        + r"(?:"
        + r"\s+(?:MINOR|PATCH|minor|patch)\s+SHIPPED PUBLIC"
        + r"|"
        + r"\s+SHIPPED PUBLIC\s+\d{4}-\d{2}-\d{2}"
        + r")"
        + r"\*\*"
    )
    return pattern.search(body) is not None


def _backfill_state_md_leading_title(
    body: str, version: str
) -> tuple[str, str | None]:
    """Flip the bolded leading title in STATE.md.

    Two shapes handled:

    - **Canonical** (AC.BACKFL2.1): ``**<version> <CLASS> SHIPPED
      LOCAL**`` → ``**<version> <CLASS> SHIPPED PUBLIC**``
      (preserves CLASS casing).
    - **Date-in-title variant** (AC.SMLTV.1): ``**<version> SHIPPED
      LOCAL <YYYY-MM-DD>**`` → ``**<version> SHIPPED PUBLIC
      <YYYY-MM-DD>**`` (preserves date verbatim).

    Per AC.BACKFL2.1 / AC.SMLTV.1 — the eye-grabbing title-claim
    surfaces. Idempotent for both shapes: re-run on already-flipped
    title is a no-op (AC.BACKFL2.4 / AC.SMLTV.3).
    """
    if _state_md_title_already_public(body, version):
        return body, None
    pattern = _leading_title_pattern(version)
    match = pattern.search(body)
    if match is None:
        return body, None
    old_title = match.group(0)
    cls = match.group("cls")
    date = match.group("date")
    if cls is not None:
        new_title = f"**{version} {cls} SHIPPED PUBLIC**"
    else:
        # Date-in-title variant — preserve the date verbatim.
        new_title = f"**{version} SHIPPED PUBLIC {date}**"
    new_body = body[: match.start()] + new_title + body[match.end():]
    edit_summary = (
        f"STATE.md leading title: {old_title!r} → {new_title!r}"
    )
    return new_body, edit_summary


# --------------------------------------------------------------------
# v0.7.4 — STATE.md TBD-AT-* placeholder backfill (AC.BACKFL2.2).
# --------------------------------------------------------------------


def _state_md_row_pattern(version: str) -> re.Pattern[str]:
    """Match the STATE.md bullet line carrying *version*'s row.

    The canonical shape is ``- **<date>** — **<version> <CLASS>
    SHIPPED LOCAL** — <prose>...`` (single line, terminated by
    newline). Captures the entire bullet so the caller can splice
    edits inline.

    Multiple rows for the same version are unusual but defensible
    — when present, this picks the FIRST match (the most-recently
    written row appears later in the file, so callers iterating
    are encouraged to call once + verify via re-search).
    """
    return re.compile(
        r"^-\s+\*\*[^*]+\*\*\s+—\s+\*\*"
        + re.escape(version)
        + r"\b[^\n]*$",
        re.MULTILINE,
    )


def _backfill_state_md_placeholders(
    body: str,
    version: str,
    tag: str,
    tag_sha: str,
    seal_sha: str | None,
    *,
    source_edit_sha: str | None = None,
    apply_sha: str | None = None,
) -> tuple[str, str | None]:
    """Apply TBD-AT-{TAG,SEAL,COMMIT,APPLY} backfill to the STATE.md
    row body for *version*.

    Per AC.BACKFL2.2 — mirror of the v0.7.3 roadmap-row TBD-AT-*
    backfill. Reuses :func:`_backfill_tbd_placeholders` so the
    replacement form (backtick-wrapped 7-char SHA) is identical
    across both files.

    Returns ``(new_body, edit_summary)``; edit_summary is None when
    no placeholders were present (already-current state).
    """
    pattern = _state_md_row_pattern(version)
    match = pattern.search(body)
    if match is None:
        return body, None
    row = match.group(0)
    new_row, backfilled = _backfill_tbd_placeholders(
        row,
        tag,
        tag_sha,
        seal_sha,
        source_edit_sha=source_edit_sha,
        apply_sha=apply_sha,
    )
    if not backfilled:
        return body, None
    new_body = body[: match.start()] + new_row + body[match.end():]
    edit_summary = (
        f"STATE.md row placeholders: backfilled "
        f"{', '.join(backfilled)}"
    )
    return new_body, edit_summary


# --------------------------------------------------------------------
# v0.7.4 — commit-graph walk for source-edit + apply SHA discovery
# (AC.BACKFL2.3 path-B).
# --------------------------------------------------------------------


_SEAL_MESSAGE_PATTERN = re.compile(
    r"chore\(seals\):\s+\S+\s+—\s+\S+\s+at\s+([0-9a-f]+)"
)
_APPLY_MESSAGE_PATTERN = re.compile(
    r"chore\(amend\):\s+\S+\s+manifest\+apply\s+—\s+.+?"
    r"BASELINE\+sidecar\s+bump\s+to\s+([0-9a-f]+)",
    re.DOTALL,
)


def _git_log_message(
    repo_root: Path, sha: str
) -> str | None:
    """Return the commit message body for *sha*, or None if the
    git invocation fails (commit not found, git binary missing,
    bad SHA, etc.). Defensive — never raises.
    """
    try:
        proc = subprocess.run(
            ["git", "log", "-1", "--pretty=%B", sha],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _discover_source_edit_and_apply_shas(
    repo_root: Path, seal_sha: str | None
) -> tuple[str | None, str | None]:
    """Walk the commit graph from *seal_sha* to find the apply
    commit + the source-edit commit.

    The canonical message forms (verified across 10+ historical
    cycles at HEAD `88964cb` 2026-05-10):

    - Seal commit: ``chore(seals): <slug> — <component-list> at
      <apply-sha>``
    - Apply commit: ``chore(amend): <slug> manifest+apply —
      <component-list> BASELINE+sidecar bump to <source-edit-sha>``

    Returns ``(source_edit_sha, apply_sha)`` or ``(None, None)``
    when *seal_sha* is None / git fails / the canonical message
    form isn't present. Per D-BACKFL2.3.b — discovery is opt-in;
    failure surfaces via hints + the caller's TBD-AT-COMMIT /
    TBD-AT-APPLY backfill is skipped (graceful degradation).
    """
    if not seal_sha:
        return None, None
    seal_msg = _git_log_message(repo_root, seal_sha)
    if seal_msg is None:
        return None, None
    seal_match = _SEAL_MESSAGE_PATTERN.search(seal_msg)
    if seal_match is None:
        return None, None
    apply_sha = seal_match.group(1)
    apply_msg = _git_log_message(repo_root, apply_sha)
    if apply_msg is None:
        return None, apply_sha
    apply_match = _APPLY_MESSAGE_PATTERN.search(apply_msg)
    if apply_match is None:
        return None, apply_sha
    source_edit_sha = apply_match.group(1)
    return source_edit_sha, apply_sha


# --------------------------------------------------------------------
# release-roadmap.md §2 row marker append + TBD-AT-* backfill
# (AC.BACKFL.1 part 2).
# --------------------------------------------------------------------


def _section_2_row_pattern(version: str) -> re.Pattern[str]:
    """Match a §2 table row whose first pipe-cell starts with
    *version*. Captures the whole line so the caller can splice
    edits inline.
    """
    return re.compile(
        r"^\|\s*" + re.escape(version) + r"\s*\|.*$",
        re.MULTILINE,
    )


def _row_already_marked_public(row: str, version: str) -> bool:
    """True iff the §2 row already carries a SHIPPED-PUBLIC marker
    for *version*.
    """
    pattern = re.compile(
        r"\*\*SHIPPED PUBLIC[^*]*at tag\s+`"
        + re.escape(version)
        + r"`"
    )
    return pattern.search(row) is not None


def _format_row_marker_suffix(
    today: _dt.date, tag: str, sha7: str
) -> str:
    """The marker suffix appended to the §2 row's third pipe-cell."""
    return (
        f"; **SHIPPED PUBLIC {today.isoformat()} at tag "
        f"`{tag}` (annotated `{sha7}`)**"
    )


# v0.10.3 (AC.RBHCB.3 / F-FUNC-3 closure) — narrative-safe TBD-AT-*
# anchor regexes. Each placeholder is matched only when preceded by
# its canonical surrounding token (lookbehind) so prose-narrative
# occurrences inside backtick-wrapped row body descriptions
# (e.g., the v0.7.3 STATE.md row at docs/STATE.md:133, whose body
# literally describes `TBD-AT-SEAL` / `TBD-AT-TAG` placeholders) are
# left untouched. The pre-v0.10.3 shape used `str.replace` which
# corrupted such prose narrative — the v0.10.1 Path-A halt finding.
_TBD_AT_SEAL_ANCHORED = re.compile(r"(?<=seal )TBD-AT-SEAL\b")
_TBD_AT_TAG_ANCHORED = re.compile(r"(?<=tag )TBD-AT-TAG\b")
_TBD_AT_COMMIT_ANCHORED = re.compile(r"(?<=source-edit )TBD-AT-COMMIT\b")
_TBD_AT_APPLY_ANCHORED = re.compile(r"(?<=apply )TBD-AT-APPLY\b")


def _backfill_tbd_placeholders(
    row: str,
    tag: str,
    tag_sha: str,
    seal_sha: str | None,
    *,
    source_edit_sha: str | None = None,
    apply_sha: str | None = None,
) -> tuple[str, list[str]]:
    """Replace TBD-AT-{TAG,SEAL,COMMIT,APPLY} placeholders in *row*
    with known / discovered SHAs.

    v0.7.3 (D-BACKFL.1.b): TBD-AT-COMMIT / TBD-AT-APPLY are NOT
    discoverable from runner inputs and were left alone. v0.7.4
    (AC.BACKFL2.3 path-B) adds opt-in *source_edit_sha* + *apply_sha*
    keyword args; the caller obtains them via
    :func:`_discover_source_edit_and_apply_shas` walking the seal
    commit's git log message. When the keyword args are None
    (discovery failed or not attempted), the v0.7.3 graceful-
    degradation behavior is preserved: the COMMIT / APPLY
    placeholders are left alone + the operator backfills them
    manually.

    v0.10.3 (AC.RBHCB.3 / F-FUNC-3 closure) — narrative-safety
    extension: each placeholder is matched only when preceded by its
    canonical surrounding token (``seal `` / ``tag `` / ``source-edit ``
    / ``apply ``) via positive lookbehind. Prose-narrative
    occurrences inside backtick-wrapped row body descriptions
    (e.g., ``backfills `TBD-AT-SEAL` / `TBD-AT-TAG` placeholders``)
    lack the canonical preceding token and are left untouched.
    Closes the v0.10.1 Path-A halt finding.

    Returns the (possibly-modified) row + a list of the placeholders
    backfilled (for the human-readable hint).
    """
    backfilled: list[str] = []
    new_row = row
    if seal_sha and _TBD_AT_SEAL_ANCHORED.search(new_row):
        new_row = _TBD_AT_SEAL_ANCHORED.sub(
            f"`{seal_sha[:7]}`", new_row
        )
        backfilled.append("TBD-AT-SEAL")
    if tag_sha and _TBD_AT_TAG_ANCHORED.search(new_row):
        new_row = _TBD_AT_TAG_ANCHORED.sub(
            f"`{tag_sha[:7]}`", new_row
        )
        backfilled.append("TBD-AT-TAG")
    if source_edit_sha and _TBD_AT_COMMIT_ANCHORED.search(new_row):
        new_row = _TBD_AT_COMMIT_ANCHORED.sub(
            f"`{source_edit_sha[:7]}`", new_row
        )
        backfilled.append("TBD-AT-COMMIT")
    if apply_sha and _TBD_AT_APPLY_ANCHORED.search(new_row):
        new_row = _TBD_AT_APPLY_ANCHORED.sub(
            f"`{apply_sha[:7]}`", new_row
        )
        backfilled.append("TBD-AT-APPLY")
    return new_row, backfilled


def _backfill_roadmap_row(
    body: str,
    version: str,
    today: _dt.date,
    tag: str,
    tag_sha: str,
    seal_sha: str | None,
    *,
    source_edit_sha: str | None = None,
    apply_sha: str | None = None,
) -> tuple[str, str | None]:
    """Apply the SHIPPED-PUBLIC marker append + TBD-AT-* SHA backfill
    to the §2 row for *version*. Returns ``(new_body, edit_summary)``.

    v0.7.4 (AC.BACKFL2.3): *source_edit_sha* + *apply_sha* are
    discovered SHAs threaded through to
    :func:`_backfill_tbd_placeholders` so TBD-AT-COMMIT / TBD-AT-APPLY
    can be backfilled without manual operator touch-up.
    """
    pattern = _section_2_row_pattern(version)
    match = pattern.search(body)
    if match is None:
        return body, None
    row = match.group(0)
    new_row = row
    edits: list[str] = []
    # TBD-AT-* placeholder backfill first (so the SHIPPED-PUBLIC marker
    # appends to a clean row).
    new_row, backfilled = _backfill_tbd_placeholders(
        new_row,
        tag,
        tag_sha,
        seal_sha,
        source_edit_sha=source_edit_sha,
        apply_sha=apply_sha,
    )
    if backfilled:
        edits.append(f"backfilled placeholders: {', '.join(backfilled)}")
    # SHIPPED-PUBLIC marker append (only if not already present).
    if _row_already_marked_public(new_row, version):
        if not edits:
            return body, None  # fully idempotent.
    else:
        # Append before the trailing `|` (the row's closing pipe).
        # Strip trailing whitespace + closing pipe, append marker, then
        # restore the closing pipe + trailing whitespace.
        stripped = new_row.rstrip()
        if stripped.endswith("|"):
            inner = stripped[:-1].rstrip()
            suffix = _format_row_marker_suffix(today, tag, sha7=tag_sha[:7])
            new_row = inner + suffix + " |"
        else:
            # Defensive — table row without a closing pipe is
            # malformed; append the marker at end + surface a hint
            # via the calling site.
            suffix = _format_row_marker_suffix(today, tag, sha7=tag_sha[:7])
            new_row = stripped + suffix
        edits.append("appended SHIPPED-PUBLIC marker")
    if not edits:
        return body, None
    new_body = body[: match.start()] + new_row + body[match.end():]
    edit_summary = (
        "roadmap §2 row: " + " + ".join(edits)
    )
    return new_body, edit_summary


# --------------------------------------------------------------------
# Aggregate-count summary line (AC.BACKFL.2).
# --------------------------------------------------------------------


_SUMMARY_LINE = re.compile(
    r"^\*\*Total shipped:\*\*\s+(\d+)\s+minor\s+\+\s+(\d+)\s+patch(?:es)?\.\s+"
    r"v[\d.]+(?:\s*→\s*v[\d.]+)?\s+published\.",
    re.MULTILINE,
)


def _split_pipe_row_backtick_aware(row: str) -> list[str]:
    """Split *row* on ``|`` characters, but skip pipes inside paired
    backticks.

    State-machine tokenizer (per AC.RBHCB.2 / D-RBHCB.2 / F-WALKER-1
    closure): walks the row character-by-character, toggles a boolean
    on each backtick (parity tracker), and emits a cell on each ``|``
    only when parity is 0. Matches ``str.split('|')`` semantics for
    cell counting (empty cells preserved as empty strings; leading /
    trailing pipes produce leading / trailing empty cells).

    Pre-fix shape (``row.split('|')``) over-segmented rows whose
    description (cell [2]) contained backtick-wrapped pipes — e.g.,
    v0.4.2's description pattern containing backtick-wrapped pipes
    in type-annotation prose caused the third pipe-cell read to land
    in the SECOND segment of the description rather than the actual
    class cell. The backtick-parity-aware split returns the correct
    cell count for any backtick-pipe-containing row.

    Edge cases:

    - Nested backticks (e.g., `` ``code`` ``) are treated as parity
      toggles — the first pair opens-and-closes, so any further
      backticks toggle independently. This matches markdown
      rendering's behaviour for paired backticks.
    - Unbalanced backticks (odd count) leave parity True at end-of-
      row; remaining pipes after the unmatched backtick are NOT
      treated as cell separators. Defensive: real STATE.md prose
      with unbalanced backticks is malformed; this tokenizer's
      behaviour matches the markdown renderer's "consume until next
      backtick" expectation.
    """
    cells: list[str] = []
    buf: list[str] = []
    in_backtick = False
    for ch in row:
        if ch == "`":
            in_backtick = not in_backtick
            buf.append(ch)
        elif ch == "|" and not in_backtick:
            cells.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    cells.append("".join(buf))
    return cells


def _classify_row(row: str) -> str:
    """Return ``"MINOR"`` or ``"PATCH"`` for the §2 row.

    Classification is hybrid (v0.8.1 AC.NFCLEAN.2 robustness fix +
    v0.10.3 AC.RBHCB.2 tokenizer hardening):

    1. First, check the third pipe-cell for the ``MINOR`` / ``PATCH``
       keyword (Single-cycle MINOR / similar — the post-v0.6.0
       explicit-class convention). Cell extraction uses
       :func:`_split_pipe_row_backtick_aware` so backtick-wrapped
       pipes in the description (cell [2]) don't shift cell [3] to
       the wrong segment (per AC.RBHCB.2 / F-WALKER-1 closure).
    2. If absent, fall back to version-pattern derivation: X.Y.0 form
       (third dotted-component is ``0`` AND no fourth component) is
       MINOR; everything else is PATCH. Per
       ``docs/release-versioning-policy.md`` semver discipline.

    The fallback covers historical rows (pre-v0.6.0) that predate the
    explicit-class convention. Without it, ``_count_published_versions``
    misclassifies all 5 historical MINORs (v0.1.0 / v0.2.0 / v0.3.0 /
    v0.4.0 / v0.7.0) as PATCH because their third pipe-cell is the
    seal-anchor commit-list cell, not a class declaration.
    """
    cells = _split_pipe_row_backtick_aware(row)
    if len(cells) >= 4:
        third = cells[3]
        if "MINOR" in third:
            return "MINOR"
        if "PATCH" in third:
            return "PATCH"
    # Fallback: derive from version-string pattern.
    version_match = re.match(r"^\|\s*v(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?\s*\|", row)
    if version_match is not None:
        major, minor, patch_, fourth = version_match.groups()
        if patch_ == "0" and fourth is None:
            return "MINOR"
    return "PATCH"


def _count_published_versions(
    body: str,
) -> tuple[int, int]:
    """Walk §2 table rows + count ALL version rows (not just rows
    carrying a SHIPPED-PUBLIC marker). Returns ``(minor_count,
    patch_count)``. Used to recompute the aggregate-count summary
    after this cycle's edit lands.

    v0.8.1 (AC.NFCLEAN.2): the previous shape required a SHIPPED-PUBLIC
    marker in every counted row. Pre-v0.7.3 versions (the 18 historical
    rows) shipped before the auto-backfill marker convention existed,
    so they have no marker — the walker undercounted by 18. The §2
    section's semantic is "shipped versions" (per its own header
    `## §2 Shipped`); every row in §2 is a published version
    regardless of marker provenance. Drop the marker requirement.
    """
    minor = 0
    patch = 0
    # A §2 row starts with `| v` (the version cell). Marker
    # provenance not required (per AC.NFCLEAN.2 root-cause fix).
    row_pattern = re.compile(
        r"^\|\s*v[\d.]+\s*\|.*$",
        re.MULTILINE,
    )
    for m in row_pattern.finditer(body):
        cls = _classify_row(m.group(0))
        if cls == "MINOR":
            minor += 1
        else:
            patch += 1
    return minor, patch


def _backfill_summary_line(
    body: str, version: str
) -> tuple[str, str | None]:
    """Update the ``**Total shipped:** N minor + M patches.
    v<prev> published.`` line to reflect the just-published version.

    Idempotent: when the line already names *version* as the latest
    published + counts already match the §2 table, returns body
    unchanged.
    """
    match = _SUMMARY_LINE.search(body)
    if match is None:
        return body, None
    minor, patch = _count_published_versions(body)
    if minor == 0 and patch == 0:
        # No published versions in §2 yet — defer + surface (the
        # table edit may not have landed before this is called).
        return body, None
    # Build the new prefix (keep the trailing prose unchanged).
    plural = "patch" if patch == 1 else "patches"
    new_prefix = (
        f"**Total shipped:** {minor} minor + {patch} {plural}. "
        f"{version} published."
    )
    old_prefix = match.group(0)
    if old_prefix == new_prefix:
        return body, None
    new_body = (
        body[: match.start()] + new_prefix + body[match.end():]
    )
    edit_summary = (
        f"summary line: {old_prefix!r} → {new_prefix!r}"
    )
    return new_body, edit_summary


# --------------------------------------------------------------------
# §3 Active Version section new bold entry (AC.BACKFL.3).
# --------------------------------------------------------------------


def _section_3_already_carries_version(
    body: str, version: str
) -> bool:
    """True iff §3 body already carries a bold entry for *version*."""
    sec_match = re.search(
        r"(?ms)^##\s*§3\b[^\n]*\n(.*?)(?=^##\s|\Z)", body
    )
    if sec_match is None:
        return False
    sec = sec_match.group(1)
    pattern = re.compile(
        r"\*\*"
        + re.escape(version)
        + r"\b[^*]*SHIPPED PUBLIC"
    )
    return pattern.search(sec) is not None


def _extract_objective_sentence(row: str) -> str:
    """Pull the §2 row's second pipe-cell + truncate to the first
    sentence. Sentence boundary = `.` outside backticks AND followed
    by whitespace or end-of-string (so `v0.6.0` mid-sentence doesn't
    trip the truncation). Safety bound: 200 chars.

    v0.10.3 (AC.RBHCB.2 / F-WALKER-1 closure): cell extraction uses
    :func:`_split_pipe_row_backtick_aware` so backtick-wrapped pipes
    in the description don't truncate the cell mid-stream. Pre-fix
    shape (``row.split('|')``) returned only the first segment of
    descriptions containing backtick-wrapped pipes in type-annotation
    prose.
    """
    parts = _split_pipe_row_backtick_aware(row)
    if len(parts) < 3:
        return ""
    sentence = parts[2].strip()
    in_backtick = False
    for i, ch in enumerate(sentence):
        if ch == "`":
            in_backtick = not in_backtick
        elif ch == "." and not in_backtick:
            next_ch = sentence[i + 1] if i + 1 < len(sentence) else ""
            if next_ch == "" or next_ch.isspace():
                sentence = sentence[: i + 1]
                break
    if len(sentence) > 200:
        sentence = sentence[:197].rstrip() + "..."
    return sentence


def _backfill_section_3(
    body: str,
    version: str,
    today: _dt.date,
    tag: str,
    tag_sha: str,
    seal_sha: str | None,
) -> tuple[str, str | None]:
    """Append a new bold ``**vX.Y.Z ... SHIPPED PUBLIC ...**`` entry
    to §3 Active version body if not already present.

    Per D-BACKFL.3.a — insertion-point: end of §3 body, just before
    the next ``## §<n>`` heading boundary OR EOF.
    """
    if _section_3_already_carries_version(body, version):
        return body, None
    sec_match = re.search(
        r"(?ms)^(##\s*§3\b[^\n]*\n)(.*?)(?=^##\s|\Z)", body
    )
    if sec_match is None:
        return body, None
    section_header = sec_match.group(1)
    section_body = sec_match.group(2)
    # Pull §2 row to get class + objective.
    row_match = _section_2_row_pattern(version).search(body)
    if row_match is None:
        return body, None
    row = row_match.group(0)
    cls = _classify_row(row)
    objective = _extract_objective_sentence(row)
    sha7 = tag_sha[:7]
    seal_sha7 = seal_sha[:7] if seal_sha else "?"
    objective_clause = f"({objective})" if objective else ""
    new_entry = (
        f"\n\n**{version} {cls} {objective_clause} SHIPPED PUBLIC "
        f"{today.isoformat()}** (tag `{tag}`, annotated `{sha7}`; "
        f"seal `{seal_sha7}`)."
    )
    # Append at end of section_body (preserve trailing whitespace
    # around the next heading by inserting before that whitespace).
    # Strip trailing newlines / blank lines from section_body first
    # so the insertion is clean.
    body_stripped = section_body.rstrip()
    new_section_body = body_stripped + new_entry + "\n\n"
    # Reconstruct the body.
    new_body = (
        body[: sec_match.start()]
        + section_header
        + new_section_body
        + body[sec_match.start() + len(section_header) + len(section_body):]
    )
    edit_summary = (
        f"§3 Active Version: appended {new_entry.strip()!r}"
    )
    return new_body, edit_summary


# --------------------------------------------------------------------
# Top-level orchestration (AC.BACKFL.{1,2,3,4}).
# --------------------------------------------------------------------


def apply_backfill(
    repo_root: Path,
    version: str,
    tag: str,
    tag_sha: str,
    *,
    seal_sha: str | None = None,
    today: _dt.date | None = None,
    dry_run: bool = False,
) -> BackfillResult:
    """Apply the post-publish state-sync edits for *version*.

    Reads ``docs/STATE.md`` + ``docs/release-roadmap.md``; rewrites
    the SHIPPED-LOCAL trailing claim → SHIPPED-PUBLIC; appends the
    §2 row marker; updates the aggregate-count summary line; appends
    a §3 Active Version bold entry. Idempotent: re-running on
    already-current state returns ``BackfillResult(idempotent_noop=
    True, edits_applied=0)`` + writes nothing.

    *seal_sha* is optional; when None the function falls back to
    :func:`gates.resolve_tag_target` (the dominating-seal resolver)
    against the roadmap body. The
    runner passes the seal SHA explicitly because it has already
    extracted it for tag creation (and the §2 row may carry a
    ``TBD-AT-SEAL`` placeholder that the extractor can't resolve).

    *dry_run* mode returns the result + per-edit human-readable
    summaries (on ``state_md_edit`` / ``roadmap_edit`` /
    ``summary_edit`` / ``section_3_edit``) but does NOT mutate any
    file on disk.
    """
    today = today or _dt.date.today()
    sha7 = tag_sha[:7]
    state_md_path = repo_root / "docs" / "STATE.md"
    roadmap_path = repo_root / "docs" / "release-roadmap.md"
    files_touched: list[Path] = []
    hints: list[str] = []
    edits = 0

    # v0.7.4 (AC.BACKFL2.3): discover source-edit + apply SHAs by
    # walking the commit graph from the seal commit. We need the
    # roadmap body to extract the seal SHA when not passed in;
    # read it eagerly so the discovery can run before either file's
    # edits land.
    discovery_seal_sha = seal_sha
    if discovery_seal_sha is None and roadmap_path.exists():
        roadmap_preview = roadmap_path.read_text(encoding="utf-8")
        discovery_seal_sha = gates.resolve_tag_target(
            repo_root, roadmap_preview, version
        ).sha
    source_edit_sha, apply_sha = _discover_source_edit_and_apply_shas(
        repo_root, discovery_seal_sha
    )
    if discovery_seal_sha is not None and (
        source_edit_sha is None or apply_sha is None
    ):
        hints.append(
            f"commit-graph walk from seal {discovery_seal_sha[:7]}: "
            f"discovered apply={apply_sha[:7] if apply_sha else 'NONE'}, "
            f"source_edit={source_edit_sha[:7] if source_edit_sha else 'NONE'}; "
            f"missing TBD-AT-* placeholders left alone (AC.BACKFL2.3 "
            f"graceful-degradation per D-BACKFL2.3.b)"
        )

    # STATE.md edits — three orthogonal: trailing-sentence flip
    # (v0.7.3 AC.BACKFL.1), leading-title flip (v0.7.4 AC.BACKFL2.1),
    # row TBD-AT-* placeholders (v0.7.4 AC.BACKFL2.2 + .3).
    state_md_edit: str | None = None
    if state_md_path.exists():
        body = state_md_path.read_text(encoding="utf-8")
        edit_summaries: list[str] = []
        # Trailing-sentence flip (v0.7.3).
        new_body, trailing_edit = _backfill_state_md(
            body, version, today, tag, tag_sha
        )
        if trailing_edit is not None:
            edit_summaries.append(trailing_edit)
            body = new_body
            edits += 1
        else:
            if _already_public_in_state_md(body, version):
                hints.append(
                    f"STATE.md already carries SHIPPED-PUBLIC marker for "
                    f"{version}; trailing-claim flip skipped."
                )
            else:
                hints.append(
                    f"STATE.md: no SHIPPED-LOCAL trailing-claim found "
                    f"for {version} (expected canonical pattern "
                    f"'{version} SHIPPED LOCAL — owner gates publish.'); "
                    f"manual edit may be needed."
                )
        # Leading-title flip (v0.7.4 AC.BACKFL2.1).
        new_body, title_edit = _backfill_state_md_leading_title(
            body, version
        )
        if title_edit is not None:
            edit_summaries.append(title_edit)
            body = new_body
            edits += 1
        # Row TBD-AT-* placeholders (v0.7.4 AC.BACKFL2.2 + .3).
        new_body, placeholder_edit = _backfill_state_md_placeholders(
            body,
            version,
            tag,
            tag_sha,
            seal_sha if seal_sha is not None else discovery_seal_sha,
            source_edit_sha=source_edit_sha,
            apply_sha=apply_sha,
        )
        if placeholder_edit is not None:
            edit_summaries.append(placeholder_edit)
            body = new_body
            edits += 1
        # Write + aggregate summary if any edits landed.
        if edit_summaries:
            state_md_edit = "; ".join(edit_summaries)
            if not dry_run:
                state_md_path.write_text(body, encoding="utf-8")
                files_touched.append(state_md_path)
    else:
        hints.append(f"STATE.md not found at {state_md_path}")

    # release-roadmap.md edits — three orthogonal: row, summary, §3.
    roadmap_edit: str | None = None
    summary_edit: str | None = None
    section_3_edit: str | None = None
    if roadmap_path.exists():
        body = roadmap_path.read_text(encoding="utf-8")
        if seal_sha is None:
            seal_sha = gates.resolve_tag_target(
                repo_root, body, version
            ).sha
        if seal_sha is None:
            hints.append(
                f"roadmap §2 row for {version}: seal SHA not extractable; "
                f"§3 entry's seal-cite will read '?' (TBD-AT-SEAL backfill "
                f"also skipped)"
            )
        # Row marker append + TBD-AT-* backfill (v0.7.4: extended to
        # cover TBD-AT-COMMIT + TBD-AT-APPLY via discovered SHAs).
        new_body, re_edit = _backfill_roadmap_row(
            body,
            version,
            today,
            tag,
            tag_sha,
            seal_sha,
            source_edit_sha=source_edit_sha,
            apply_sha=apply_sha,
        )
        if re_edit is not None:
            roadmap_edit = re_edit
            edits += 1
            body = new_body
        # Aggregate-count summary line.
        new_body, sm_edit = _backfill_summary_line(body, version)
        if sm_edit is not None:
            summary_edit = sm_edit
            edits += 1
            body = new_body
        # §3 Active Version new bold entry.
        new_body, s3_edit = _backfill_section_3(
            body, version, today, tag, tag_sha, seal_sha
        )
        if s3_edit is not None:
            section_3_edit = s3_edit
            edits += 1
            body = new_body
        # Write once if any edits landed.
        if (
            roadmap_edit is not None
            or summary_edit is not None
            or section_3_edit is not None
        ):
            if not dry_run:
                roadmap_path.write_text(body, encoding="utf-8")
                files_touched.append(roadmap_path)
    else:
        hints.append(f"release-roadmap.md not found at {roadmap_path}")

    return BackfillResult(
        edits_applied=edits,
        files_touched=files_touched,
        idempotent_noop=(edits == 0),
        state_md_edit=state_md_edit,
        roadmap_edit=roadmap_edit,
        summary_edit=summary_edit,
        section_3_edit=section_3_edit,
        hints=hints,
    )


def format_backfill_preview(result: BackfillResult) -> str:
    """Render a dry-run preview block for the publish-flow stdout."""
    lines: list[str] = []
    if result.idempotent_noop:
        lines.append(
            "DRY-RUN: post-publish backfill — no edits needed (state "
            "already current)."
        )
    else:
        lines.append(
            f"DRY-RUN: would apply post-publish backfill — "
            f"{result.edits_applied} edit(s):"
        )
        if result.state_md_edit:
            lines.append(f"  - {result.state_md_edit}")
        if result.roadmap_edit:
            lines.append(f"  - {result.roadmap_edit}")
        if result.summary_edit:
            lines.append(f"  - {result.summary_edit}")
        if result.section_3_edit:
            lines.append(f"  - {result.section_3_edit}")
    for hint in result.hints:
        lines.append(f"  hint: {hint}")
    return "\n".join(lines)
