"""Post-publish state backfill (AC.BACKFL.{1,2,3,4}).

After ``loam release`` pushes branch + tag, the version's rows in
``docs/STATE.md`` and ``docs/release-roadmap.md`` need to flip from
"SHIPPED LOCAL — owner gates publish" → "SHIPPED PUBLIC at tag <name>
(annotated <SHA>)" so downstream agents reading STATE.md see ground
truth instead of a stale-claim. Prior to v0.7.3 this was a manual
backfill commit per publish (recurring miss at v0.6.0 / v0.7.0 /
v0.7.1 / v0.7.2). v0.7.3 closes the defect by wiring this module
into :mod:`loam_cli.release.runner` between the tag-push step and
the post-ship review step.

Public callable: :func:`apply_backfill`. Returns a
:class:`BackfillResult` carrying the edits-applied count + the
files-touched list + the idempotent-noop flag (True when the rows
already carry the SHIPPED-PUBLIC marker for this version).
"""

from __future__ import annotations

import datetime as _dt
import re
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


def _backfill_state_md(
    body: str, version: str, today: _dt.date, tag: str, tag_sha: str
) -> tuple[str, str | None]:
    """Apply the SHIPPED-LOCAL → SHIPPED-PUBLIC trailing-claim flip
    to *body*. Returns ``(new_body, edit_summary)`` where
    *edit_summary* is None if the body was unchanged (already public
    OR pattern not matched).
    """
    if _already_public_in_state_md(body, version):
        return body, None
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


def _backfill_tbd_placeholders(
    row: str, tag: str, tag_sha: str, seal_sha: str | None
) -> tuple[str, list[str]]:
    """Replace TBD-AT-TAG / TBD-AT-SEAL in *row* with known SHAs.

    Per D-BACKFL.1.b: TBD-AT-COMMIT / TBD-AT-APPLY are NOT
    discoverable from runner inputs and are left alone (operator
    surface). Returns the (possibly-modified) row + a list of the
    placeholders backfilled (for the human-readable hint).
    """
    backfilled: list[str] = []
    new_row = row
    if seal_sha and "TBD-AT-SEAL" in new_row:
        new_row = new_row.replace("TBD-AT-SEAL", f"`{seal_sha[:7]}`")
        backfilled.append("TBD-AT-SEAL")
    if tag_sha and "TBD-AT-TAG" in new_row:
        new_row = new_row.replace("TBD-AT-TAG", f"`{tag_sha[:7]}`")
        backfilled.append("TBD-AT-TAG")
    return new_row, backfilled


def _backfill_roadmap_row(
    body: str,
    version: str,
    today: _dt.date,
    tag: str,
    tag_sha: str,
    seal_sha: str | None,
) -> tuple[str, str | None]:
    """Apply the SHIPPED-PUBLIC marker append + TBD-AT-* SHA backfill
    to the §2 row for *version*. Returns ``(new_body, edit_summary)``.
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
        new_row, tag, tag_sha, seal_sha
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
    r"v[\d.]+\s+published\.",
    re.MULTILINE,
)


def _classify_row(row: str) -> str:
    """Return ``"MINOR"`` if the §2 row's third cell carries
    ``MINOR`` keyword (Single-cycle MINOR / similar); else ``"PATCH"``.
    """
    third_cell_split = row.split("|")
    if len(third_cell_split) < 4:
        return "PATCH"
    third = third_cell_split[3]
    if "MINOR" in third:
        return "MINOR"
    return "PATCH"


def _count_published_versions(
    body: str,
) -> tuple[int, int]:
    """Walk §2 table rows + count those that carry a
    ``SHIPPED PUBLIC at tag`` marker. Returns ``(minor_count,
    patch_count)``. Used to recompute the aggregate-count summary
    after this cycle's edit lands.
    """
    minor = 0
    patch = 0
    # A §2 row starts with `| v` and includes the marker.
    row_pattern = re.compile(
        r"^\|\s*v[\d.]+\s*\|.*\*\*SHIPPED PUBLIC[^*]*at tag\s+`v[\d.]+`.*$",
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
    """
    parts = row.split("|")
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

    # STATE.md edit.
    state_md_edit: str | None = None
    if state_md_path.exists():
        body = state_md_path.read_text(encoding="utf-8")
        new_body, edit = _backfill_state_md(body, version, today, tag, tag_sha)
        if edit is not None:
            state_md_edit = edit
            edits += 1
            if not dry_run:
                state_md_path.write_text(new_body, encoding="utf-8")
                files_touched.append(state_md_path)
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
    else:
        hints.append(f"STATE.md not found at {state_md_path}")

    # release-roadmap.md edits — three orthogonal: row, summary, §3.
    roadmap_edit: str | None = None
    summary_edit: str | None = None
    section_3_edit: str | None = None
    if roadmap_path.exists():
        body = roadmap_path.read_text(encoding="utf-8")
        seal_sha = gates._extract_seal_sha(body, version)
        if seal_sha is None:
            hints.append(
                f"roadmap §2 row for {version}: seal SHA not extractable; "
                f"§3 entry's seal-cite will read '?' (TBD-AT-SEAL backfill "
                f"also skipped)"
            )
        # Row marker append + TBD-AT-* backfill.
        new_body, re_edit = _backfill_roadmap_row(
            body, version, today, tag, tag_sha, seal_sha
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
