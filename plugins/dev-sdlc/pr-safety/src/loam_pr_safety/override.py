"""Override-commit recognition + ratification flow for loam-pr-safety.

Per AC.PRSG.5 — recognises override-shaped commits and runs the
override-ratification flow through the per-project-pm batch API.

Recognition:

  An override is recognised when ALL of:

    1. The commit at ``to_sha`` (default: ``HEAD``) has EITHER:
       - Subject matching ``^contract-update:`` (case-sensitive prefix), OR
       - Body containing a ``Loam-Override: <rationale>`` trailer
         (RFC-822-style; rationale must be non-empty after stripping
         whitespace).
    2. The gate is invoked with ``--override`` flag.

  Per Decision I default-no — both signals required; commit-shape
  alone is not sufficient.

Application strategy (Surface #4): approved overrides are recorded as
**additive overlays** at
``<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml``
rather than mutating the odd-extractor's contract sidecar in-place.
The next ``read_contract`` call composes overlays on top.
"""

from __future__ import annotations

import datetime as _dt
import re
import subprocess
from pathlib import Path

import yaml

from loam_odd_extractor.bands import (
    BandedAC,
    ConfidenceBand,
    Evidence,
)
from loam.per_project_pm import (
    PMRuntime,
    RatificationBatch,
    PendingResponseError,
)

from loam_pr_safety.audit import write_audit_entry
from loam_pr_safety.errors import (
    GateError,
    OverrideRejectedError,
)
from loam_pr_safety.spec import (
    BandedContract,
    ClassificationResult,
    OverrideRequest,
    TouchedAC,
)
from loam_pr_safety.state import overrides_dir


_LOAM_OVERRIDE_TRAILER_RE = re.compile(
    r"^Loam-Override:\s*(?P<rationale>.+)$",
    re.MULTILINE,
)
_CONTRACT_UPDATE_PREFIX_RE = re.compile(
    r"^contract-update:\s*(?P<rest>.*)$"
)


def read_commit_message(repo_path: Path, sha: str = "HEAD") -> str:
    """Read the commit message at ``sha``.

    Used for override-recognition. Wraps ``git -C <repo> log -1
    --format=%B <sha>``.
    """
    repo_path = repo_path.expanduser().resolve()
    try:
        proc = subprocess.run(  # noqa: S603 — controlled command
            [
                "git",
                "-C",
                str(repo_path),
                "log",
                "-1",
                "--format=%B",
                sha,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GateError(
            "git executable not found on PATH"
        ) from exc
    if proc.returncode != 0:
        raise GateError(
            f"git log failed at {sha}: {proc.stderr.strip()}"
        )
    return proc.stdout


def read_commit_owner(
    repo_path: Path, sha: str = "HEAD"
) -> str:
    """Return the author name + email at ``sha``."""
    repo_path = repo_path.expanduser().resolve()
    try:
        proc = subprocess.run(  # noqa: S603 — controlled command
            [
                "git",
                "-C",
                str(repo_path),
                "log",
                "-1",
                "--format=%an <%ae>",
                sha,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GateError(
            "git executable not found on PATH"
        ) from exc
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def recognise_override(
    commit_message: str,
    *,
    override_flag: bool,
) -> tuple[bool, str]:
    """Detect an override-shaped commit.

    Returns ``(recognised, rationale)``.

    Per Decision I default-no: returns ``(False, "")`` whenever
    ``override_flag`` is ``False``, regardless of commit shape.

    When ``override_flag`` is ``True``:
      - If the body has a ``Loam-Override: <rationale>`` trailer,
        returns ``(True, <rationale>)``.
      - Else if the subject (first line) starts with
        ``contract-update:``, returns ``(True, <prose-after-prefix>)``
        — the prose after the colon is treated as rationale; can
        be empty.
      - Else returns ``(False, "")``.
    """
    if not override_flag:
        return (False, "")
    if not commit_message:
        return (False, "")

    # Trailer recognition first (most-compatible-with-conventional-commits
    # path — Surface #3).
    m_trailer = _LOAM_OVERRIDE_TRAILER_RE.search(commit_message)
    if m_trailer is not None:
        rationale = m_trailer.group("rationale").strip()
        if rationale:
            return (True, rationale)

    # Prefix recognition (ergonomics path — also requires --override).
    first_line = commit_message.splitlines()[0] if commit_message else ""
    m_prefix = _CONTRACT_UPDATE_PREFIX_RE.match(first_line)
    if m_prefix is not None:
        rationale = m_prefix.group("rest").strip()
        return (True, rationale)

    return (False, "")


def _proposed_acs_from_classification(
    classification: ClassificationResult,
    *,
    repo_sha: str,
) -> list[BandedAC]:
    """Build the override-flow's ``proposed_acs`` from a classification.

    Per F2 RF gap #9 — Cycle 1 default: novel candidates promote to
    PLAUSIBLE (most-conservative — PLAUSIBLE-touched is
    SURFACE_DECISION in future runs, not HARD_BLOCK). Reviewer's PM-
    mediated answer can adjust at ratification time.

    For VERIFIED-touched ACs that the override is overriding, the
    proposal is "convert to PLAUSIBLE with the diff's hunks as the
    new evidence citations."
    """
    proposed: list[BandedAC] = []
    # VERIFIED-touched → propose conversion to PLAUSIBLE.
    for touched in classification.touched_acs:
        if touched.ac.confidence is not ConfidenceBand.VERIFIED:
            continue
        # Build new citations from touched hunks (file:start-end).
        new_cites: list[str] = []
        for hunk in touched.touched_hunks:
            if hunk.new_lines > 0:
                end_line = hunk.new_start + hunk.new_lines - 1
                new_cites.append(
                    f"{touched.ac.backing_files[0] if touched.ac.backing_files else 'unknown'}:"
                    f"{hunk.new_start}-{end_line}"
                )
        # Fallback to existing citations if hunks didn't map to ranges.
        if not new_cites:
            new_cites = list(touched.ac.evidence.citations)
        proposed.append(
            BandedAC(
                ac_id=touched.ac.ac_id,
                text=touched.ac.text,
                confidence=ConfidenceBand.PLAUSIBLE,
                evidence=Evidence(
                    kind="source",
                    citations=new_cites or [str(touched.ac.backing_files[0]) if touched.ac.backing_files else "unspecified"],
                    repo_sha=None,
                    rationale=None,
                ),
                backing_files=list(touched.ac.backing_files),
            )
        )
    # Novel candidates → promote to PLAUSIBLE.
    for idx, novel in enumerate(classification.novel):
        novel_cites: list[str] = []
        for hunk in novel.hunks:
            if hunk.new_lines > 0:
                end_line = hunk.new_start + hunk.new_lines - 1
                novel_cites.append(
                    f"{novel.file_path!s}:{hunk.new_start}-{end_line}"
                )
        if not novel_cites:
            novel_cites = [str(novel.file_path)]
        proposed.append(
            BandedAC(
                ac_id=f"AC.NOVEL.{idx + 1}",
                text=(
                    f"Novel candidate from override; "
                    f"file {novel.file_path!s}; "
                    f"covered by override commit"
                ),
                confidence=ConfidenceBand.PLAUSIBLE,
                evidence=Evidence(
                    kind="source",
                    citations=novel_cites,
                    repo_sha=None,
                    rationale=None,
                ),
                backing_files=[str(novel.file_path)],
            )
        )
    return proposed


def build_override_request(
    classification: ClassificationResult,
    *,
    rationale: str,
    owner: str,
    commit_sha: str,
    repo_sha: str,
) -> OverrideRequest:
    """Construct an :class:`OverrideRequest` from a classification.

    Per AC.PRSG.5.
    """
    original_acs = [
        t.ac
        for t in classification.touched_acs
        if t.ac.confidence is ConfidenceBand.VERIFIED
    ]
    proposed_acs = _proposed_acs_from_classification(
        classification, repo_sha=repo_sha
    )
    return OverrideRequest(
        original_acs=original_acs,
        proposed_acs=proposed_acs,
        rationale=rationale,
        owner=owner,
        commit_sha=commit_sha,
        repo_sha=repo_sha,
    )


def _next_overlay_seq(repo_overrides_dir: Path) -> int:
    """Return the next 1-based sequence number for an overlay file."""
    if not repo_overrides_dir.exists():
        return 1
    seen: list[int] = []
    overlay_re = re.compile(r"^override-(\d+)\.yaml$")
    for p in repo_overrides_dir.iterdir():
        m = overlay_re.match(p.name)
        if m:
            seen.append(int(m.group(1)))
    return (max(seen) if seen else 0) + 1


def apply_override(
    request: OverrideRequest,
    *,
    workspace_root: Path,
    repo_id: str,
) -> Path:
    """Write an additive overlay file recording an approved override.

    Per Surface #4 (plan-doc §5) — overlays land at
    ``<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/override-<N>.yaml``.
    Each overlay can either:

      - Replace one VERIFIED AC with a new (lower-band) entry
        (kind=``replace_verified``), OR
      - Promote a novel candidate (kind=``promote_novel``).

    For an :class:`OverrideRequest` with multiple
    ``original_acs``/``proposed_acs``, this function writes ONE
    overlay containing the FIRST original-and-replacement pair (the
    typical case is one VERIFIED AC overridden per commit). Multiple
    pairs are split across multiple overlay files (override-1,
    override-2, ...) — Cycle 1 simplification; Cycle 2+ may
    consolidate.

    Returns the path of the FIRST overlay file written.
    """
    rd = overrides_dir(workspace_root, repo_id)
    rd.mkdir(parents=True, exist_ok=True)
    first_path: Path | None = None

    # Build pair list — for each original_ac (VERIFIED-touched), pair
    # with the same-id proposed AC (the conversion target). Then any
    # remaining proposed ACs are promote_novel.
    original_by_id = {ac.ac_id: ac for ac in request.original_acs}
    paired_proposed_ids: set[str] = set()

    for original in request.original_acs:
        replacement = next(
            (p for p in request.proposed_acs if p.ac_id == original.ac_id),
            None,
        )
        if replacement is None:
            continue
        paired_proposed_ids.add(replacement.ac_id)
        seq = _next_overlay_seq(rd)
        path = rd / f"override-{seq}.yaml"
        path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "kind": "replace_verified",
                    "original_ac_id": original.ac_id,
                    "replacement_ac": replacement.model_dump(mode="json"),
                    "rationale": request.rationale,
                    "owner": request.owner,
                    "commit_sha": request.commit_sha,
                    "repo_sha": request.repo_sha,
                    "applied_at": _dt.datetime.now(
                        _dt.timezone.utc
                    ).isoformat(),
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        if first_path is None:
            first_path = path

    # Remaining proposed ACs → promote_novel overlays.
    for proposed in request.proposed_acs:
        if proposed.ac_id in paired_proposed_ids:
            continue
        if proposed.ac_id in original_by_id:
            # original-without-pair edge case; covered above.
            continue
        seq = _next_overlay_seq(rd)
        path = rd / f"override-{seq}.yaml"
        path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "kind": "promote_novel",
                    "replacement_ac": proposed.model_dump(mode="json"),
                    "rationale": request.rationale,
                    "owner": request.owner,
                    "commit_sha": request.commit_sha,
                    "repo_sha": request.repo_sha,
                    "applied_at": _dt.datetime.now(
                        _dt.timezone.utc
                    ).isoformat(),
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        if first_path is None:
            first_path = path

    if first_path is None:
        # No pairs and no novel → nothing applied. Audit-log captures
        # at the caller; we return a synthetic "no-op" path under the
        # overrides_dir so callers can detect.
        first_path = rd / ".no-op"
        first_path.parent.mkdir(parents=True, exist_ok=True)
        first_path.write_text("(no-op override)\n", encoding="utf-8")

    return first_path


def run_override_ratification(
    request: OverrideRequest,
    *,
    pm: PMRuntime,
    workspace_root: Path,
    repo_id: str,
    response_recorder=None,
) -> tuple[bool, str, Path | None]:
    """Surface the override request through the PM batch API and
    apply if approved.

    Per AC.PRSG.5 + Decision Q (one-question-at-a-time).

    Flow:

      1. Build a :class:`RatificationBatch` from the proposed_acs.
      2. Enqueue + ``surface_next_questions_batch(n=1)``.
      3. The caller (CLI) collects the operator's response;
         ``response_recorder`` is a callable (or stub) that returns
         ``(approved: bool, response_text: str)`` — Cycle 1 ships
         a synchronous-prompt stub for tests; Cycle 2 wires the
         persona-side relay.
      4. ``record_response`` clears pending_response_for; if approved,
         :func:`apply_override` writes the overlay; if rejected,
         raises :class:`OverrideRejectedError`.

    Returns ``(approved, response_text, overlay_path_or_None)``.
    """
    batch = RatificationBatch.from_banded_acs(
        extraction_id=request.commit_sha[:8] or "override",
        banded_acs=[ac.model_dump() for ac in request.proposed_acs],
    )
    enqueued = batch.enqueue(pm)
    # surface one (Decision Q one-question-at-a-time).
    try:
        surfaced = pm.surface_next_questions_batch(n=1)
    except PendingResponseError as exc:
        raise GateError(
            f"PM has a pending response from a prior interaction; "
            f"cannot surface override ratification until cleared. "
            f"({exc})"
        ) from exc
    if not surfaced:
        # Empty queue or onboarding-mode forced no surfacing.
        return (False, "(no question surfaced)", None)
    sq = surfaced[0]

    # Collect operator response.
    if response_recorder is None:
        # Default: assume rejection (safe-by-default; Decision I).
        approved = False
        response_text = "(no response recorder; default deny)"
    else:
        approved, response_text = response_recorder(sq)

    # Record the response (clears pending_response_for).
    pm.record_response(sq.audit_path, response_text)

    if approved:
        overlay_path = apply_override(
            request, workspace_root=workspace_root, repo_id=repo_id
        )
        write_audit_entry(
            workspace_root,
            event_kind="override_approved",
            repo_id=repo_id,
            repo_sha=request.repo_sha,
            decision="OVERRIDE_APPROVED",
            requires_ratification=True,
            touched_acs=[ac.ac_id for ac in request.original_acs],
            owner=request.owner,
            rationale=request.rationale,
            reason=f"Override approved; overlay at {overlay_path!s}",
        )
        return (True, response_text, overlay_path)

    write_audit_entry(
        workspace_root,
        event_kind="override_rejected",
        repo_id=repo_id,
        repo_sha=request.repo_sha,
        decision="OVERRIDE_REJECTED",
        requires_ratification=True,
        touched_acs=[ac.ac_id for ac in request.original_acs],
        owner=request.owner,
        rationale=request.rationale,
        reason="Override rejected by reviewer",
    )
    raise OverrideRejectedError(
        f"Override ratification rejected: {response_text}"
    )
