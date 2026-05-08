"""Override-commit recognition + ratification flow for loam-pr-safety.

Per AC.PRGATE.4 (v0.2.3 Cycle 3) — recognises override-shaped commits
and runs the override-ratification flow at OBJECTIVE altitude.

Recognition:

  An override is recognised when ALL of:

    1. The commit at ``to_sha`` (default: ``HEAD``) has EITHER:
       - Subject matching ``^contract-update:`` (case-sensitive prefix), OR
       - Body containing a ``Loam-Override: <rationale>`` trailer
         (RFC-822-style; rationale must be non-empty after stripping
         whitespace).
    2. The gate is invoked with ``--override`` flag.

  Per Decision I default-no — both signals required.

Application strategy: approved overrides are recorded as additive
overlays at
``<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml``.
Cycle 3 overlay shape:

    schema_version: 2
    kind: replace_verified_objective
    original_objective_id: <id>
    replacement_objective: <Objective dict>

Cycle 3 simplification: VERIFIED-objective-touched override demotes
the objective to PLAUSIBLE preserving objective_id + text + domain +
multi-source evidence. Novel diffs at this cycle do NOT promote to
objectives — Cycle 3 records audit-only; v0.2.4 gap-analysis owns
novel→objective promotion.
"""

from __future__ import annotations

import datetime as _dt
import re
import subprocess
from pathlib import Path

import yaml

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.spec import (
    Objective,
    ObjectiveEvidence,
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
    ClassificationResult,
    OverrideRequest,
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
    """Read the commit message at ``sha``."""
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
    ``override_flag`` is ``False``.

    When ``override_flag`` is ``True``:
      - If the body has a ``Loam-Override: <rationale>`` trailer with
        non-empty rationale, returns ``(True, <rationale>)``.
      - Else if the subject (first line) starts with
        ``contract-update:``, returns ``(True, <prose-after-prefix>)``.
      - Else returns ``(False, "")``.
    """
    if not override_flag:
        return (False, "")
    if not commit_message:
        return (False, "")

    m_trailer = _LOAM_OVERRIDE_TRAILER_RE.search(commit_message)
    if m_trailer is not None:
        rationale = m_trailer.group("rationale").strip()
        if rationale:
            return (True, rationale)

    first_line = commit_message.splitlines()[0] if commit_message else ""
    m_prefix = _CONTRACT_UPDATE_PREFIX_RE.match(first_line)
    if m_prefix is not None:
        rationale = m_prefix.group("rest").strip()
        return (True, rationale)

    return (False, "")


def _proposed_objectives_from_classification(
    classification: ClassificationResult,
    *,
    repo_sha: str,
) -> list[Objective]:
    """Build the override-flow's ``proposed_objectives`` from a
    classification.

    Per AC.PRGATE.4 — Cycle 3 default: VERIFIED-touched objectives
    propose conversion to PLAUSIBLE preserving objective_id + text +
    domain + multi-source evidence (banding rules enforced via
    Pydantic; the multi-source evidence stays valid for PLAUSIBLE).
    Novel diffs do NOT generate objective proposals at this cycle —
    v0.2.4 gap-analysis owns novel→objective promotion.
    """
    proposed: list[Objective] = []
    for touched in classification.touched_objectives:
        if touched.objective.confidence is not ConfidenceBand.VERIFIED:
            continue
        # Proposed = same objective at PLAUSIBLE band.
        # Preserve evidence verbatim (multi-source evidence shape is
        # valid for PLAUSIBLE — the readme/design_doc/survey refs all
        # transfer; the Pydantic per-band validator allows
        # PLAUSIBLE with any of those refs). drop the test_name_refs
        # only if needed — they're additive at PLAUSIBLE.
        original = touched.objective
        # Build PLAUSIBLE-compatible evidence: must have at least one
        # of readme_excerpts / design_doc_refs / survey_line_refs.
        ev = original.evidence
        proposed_ev = ObjectiveEvidence(
            readme_excerpts=list(ev.readme_excerpts),
            design_doc_refs=list(ev.design_doc_refs),
            test_name_refs=list(ev.test_name_refs),
            survey_line_refs=list(ev.survey_line_refs),
            code_pattern_refs=list(ev.code_pattern_refs),
            repo_sha=ev.repo_sha,
            rationale=(
                ev.rationale
                or "VERIFIED→PLAUSIBLE conversion via override flow"
            ),
        )
        # If PLAUSIBLE requires at least one of readme/design/survey
        # refs and none are populated, fall through to keeping the
        # objective (defensive — but we know VERIFIED required
        # readme_excerpts OR design_doc_refs by per-band rule, so
        # PLAUSIBLE rule is satisfied automatically).
        try:
            proposed.append(
                Objective(
                    objective_id=original.objective_id,
                    text=original.text,
                    confidence=ConfidenceBand.PLAUSIBLE,
                    evidence=proposed_ev,
                    domain=original.domain,
                )
            )
        except ValueError:
            # Defensive: if VERIFIED objective somehow lacks
            # PLAUSIBLE-compatible refs, skip rather than blow up
            # the override flow.
            continue
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

    Per AC.PRGATE.4.
    """
    original_objectives = [
        t.objective
        for t in classification.touched_objectives
        if t.objective.confidence is ConfidenceBand.VERIFIED
    ]
    proposed_objectives = _proposed_objectives_from_classification(
        classification, repo_sha=repo_sha
    )
    return OverrideRequest(
        original_objectives=original_objectives,
        proposed_objectives=proposed_objectives,
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

    Per AC.PRGATE.4 — Cycle 3 overlay shape:

        schema_version: 2
        kind: replace_verified_objective
        original_objective_id: <id>
        replacement_objective: <Objective dict>

    Returns the path of the FIRST overlay file written.
    """
    rd = overrides_dir(workspace_root, repo_id)
    rd.mkdir(parents=True, exist_ok=True)
    first_path: Path | None = None

    # Pair each VERIFIED original_objective with its same-id
    # proposed_objective (the conversion target).
    for original in request.original_objectives:
        replacement = next(
            (
                p
                for p in request.proposed_objectives
                if p.objective_id == original.objective_id
            ),
            None,
        )
        if replacement is None:
            continue
        seq = _next_overlay_seq(rd)
        path = rd / f"override-{seq}.yaml"
        path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 2,
                    "kind": "replace_verified_objective",
                    "original_objective_id": original.objective_id,
                    "replacement_objective": replacement.model_dump(
                        mode="json"
                    ),
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
        # No conversion pairs — record an audit-only overlay so the
        # override is preserved on disk for audit even when no
        # objective demotion happened (e.g., novel-diff-only override).
        seq = _next_overlay_seq(rd)
        path = rd / f"override-{seq}.yaml"
        path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 2,
                    "kind": "audit_only",
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
        first_path = path

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

    Per AC.PRGATE.4 + Decision Q (one-question-at-a-time).

    Flow:

      1. Build a :class:`RatificationBatch` from the
         proposed_objectives (model_dump'd as dicts for PM).
      2. Enqueue + ``surface_next_questions_batch(n=1)``.
      3. ``response_recorder`` returns ``(approved, response_text)``.
      4. ``record_response`` clears pending_response_for; if approved,
         :func:`apply_override` writes the overlay; else raises
         :class:`OverrideRejectedError`.

    Returns ``(approved, response_text, overlay_path_or_None)``.
    """
    batch = RatificationBatch.from_banded_acs(
        extraction_id=request.commit_sha[:8] or "override",
        banded_acs=[
            obj.model_dump(mode="json") for obj in request.proposed_objectives
        ],
    )
    enqueued = batch.enqueue(pm)
    try:
        surfaced = pm.surface_next_questions_batch(n=1)
    except PendingResponseError as exc:
        raise GateError(
            f"PM has a pending response from a prior interaction; "
            f"cannot surface override ratification until cleared. "
            f"({exc})"
        ) from exc
    if not surfaced:
        return (False, "(no question surfaced)", None)
    sq = surfaced[0]

    if response_recorder is None:
        approved = False
        response_text = "(no response recorder; default deny)"
    else:
        approved, response_text = response_recorder(sq)

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
            touched_acs=[
                o.objective_id for o in request.original_objectives
            ],
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
        touched_acs=[
            o.objective_id for o in request.original_objectives
        ],
        owner=request.owner,
        rationale=request.rationale,
        reason="Override rejected by reviewer",
    )
    raise OverrideRejectedError(
        f"Override ratification rejected: {response_text}"
    )
