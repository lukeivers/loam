"""``loam amend sweep-archive`` — run the retroactive plan-doc archive
against the canonical tree, producing one ``chore(retroactive-sweep):``
commit per real run.

Amendment #143 Scope C + D-T1RS.LIVE-SWEEP-MECHANISM:
- ``--dry-run`` (default-explicit: callers MUST opt into one or the
  other; the function REFUSES to run when neither flag is set, so an
  operator typing ``loam amend sweep-archive`` accidentally never
  modifies the tree). The dry-run shape is the same as
  ``sweep_sealed_plan_docs(repo_root, dry_run=True)``.
- Real run: invokes the sweep, then ``git commit`` with the canonical
  ``chore(retroactive-sweep): live archive of plan-docs with single-
  match seal commits — N moved, M ambiguous, K in-flight (per
  amendment #143 Scope C)`` subject, body grouped by strategy
  (narrow / body / amendment-n).

Halt discipline (plan-doc §6 halt-trigger #3): the operator runs
``--dry-run`` first to surface the count; the real run is the second
invocation. The CLI does NOT auto-confirm.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from loam_amend.plan_archive import SweepResult, sweep_sealed_plan_docs


# Canonical subject prefix; the live-sweep commit's subject IS this
# string + the count summary, per D-T1RS.LIVE-SWEEP-MECHANISM.
SWEEP_COMMIT_SUBJECT_PREFIX = "chore(retroactive-sweep):"


def _format_dry_run_report(result: SweepResult) -> str:
    """Render the dry-run preview as human-readable text.

    Lists moves grouped by attribution strategy; counts ambiguous +
    in-flight separately.
    """
    lines: list[str] = []
    # Count moved plan-docs (NOT manifest siblings — they ride with
    # their plan-doc). The sweep's ``moved_by_strategy`` map is the
    # authoritative per-strategy enumeration.
    n_moved_plan_docs = sum(
        len(v) for v in result.moved_by_strategy.values()
    )
    n_moved_total = len(result.moved)  # plan-docs + sibling manifests
    n_ambiguous = len(result.ambiguous)
    n_in_flight = len(result.in_flight)
    lines.append(
        f"dry-run: would move {n_moved_plan_docs} plan-doc(s) "
        f"(+ {n_moved_total - n_moved_plan_docs} sibling manifest(s)); "
        f"ambiguous: {n_ambiguous}; in-flight: {n_in_flight}"
    )
    for strategy in sorted(result.moved_by_strategy):
        files = result.moved_by_strategy[strategy]
        lines.append(f"  strategy={strategy} ({len(files)}):")
        for name in sorted(files):
            lines.append(f"    {name}")
    if result.ambiguous:
        lines.append(f"  ambiguous ({n_ambiguous}) — stay in docs/plans/:")
        for p in sorted(result.ambiguous, key=lambda x: x.name):
            lines.append(f"    {p.name}")
    return "\n".join(lines)


def _commit_subject(result: SweepResult) -> str:
    """Build the canonical commit subject for a real-run sweep.

    Per D-T1RS.LIVE-SWEEP-MECHANISM: the subject names the move/
    ambiguous/in-flight counts inline so a reader can see the sweep's
    scale without expanding the body.
    """
    n_moved_plan_docs = sum(
        len(v) for v in result.moved_by_strategy.values()
    )
    n_ambiguous = len(result.ambiguous)
    n_in_flight = len(result.in_flight)
    return (
        f"{SWEEP_COMMIT_SUBJECT_PREFIX} live archive of plan-docs with "
        f"single-match seal commits — {n_moved_plan_docs} moved, "
        f"{n_ambiguous} ambiguous, {n_in_flight} in-flight "
        f"(per amendment #143 Scope C)"
    )


def _commit_body(result: SweepResult) -> str:
    """Build the commit body grouping moved plan-docs by strategy.

    Sibling manifests are NOT enumerated separately — they ride with
    their plan-doc in the same ``git mv`` op.
    """
    lines: list[str] = []
    lines.append(
        "Live retroactive sweep of plan-docs with attributable seal "
        "commits into docs/plans/sealed/. Amendment #143 Scope C "
        "real-run; closes amendment #134 §16 finding #6."
    )
    lines.append("")
    lines.append("Moves grouped by attribution strategy:")
    for strategy in sorted(result.moved_by_strategy):
        files = result.moved_by_strategy[strategy]
        lines.append(f"  {strategy} ({len(files)}):")
        for name in sorted(files):
            lines.append(f"    {name}")
    if result.ambiguous:
        lines.append("")
        lines.append(
            f"Ambiguous (multi-match in winning strategy) — left in "
            f"docs/plans/ per §134 halt-trigger #5 contract "
            f"({len(result.ambiguous)}):"
        )
        for p in sorted(result.ambiguous, key=lambda x: x.name):
            lines.append(f"  {p.name}")
    return "\n".join(lines)


def run(repo_root: Path, *, dry_run: bool) -> int:
    """Execute the sweep against ``repo_root``.

    ``dry_run=True`` prints the preview report; ``dry_run=False`` runs
    the sweep + creates the ``chore(retroactive-sweep):`` commit.

    Returns exit code (0 = ok; non-0 = no-op or error). On a real run
    with zero moves, returns 0 + prints "nothing to sweep" (no commit
    is created — the empty commit would be noise).
    """
    repo_root = repo_root.resolve()
    result = sweep_sealed_plan_docs(repo_root, dry_run=dry_run)
    if dry_run:
        print(_format_dry_run_report(result))
        return 0

    # Real run.
    n_moved_plan_docs = sum(
        len(v) for v in result.moved_by_strategy.values()
    )
    if n_moved_plan_docs == 0:
        print(
            "sweep: nothing to archive "
            f"(ambiguous={len(result.ambiguous)}, in_flight={len(result.in_flight)})"
        )
        return 0

    # Stage the moves. The sweep itself ran ``git mv`` per move, so
    # the index is already staged; we just commit.
    subject = _commit_subject(result)
    body = _commit_body(result)
    message = f"{subject}\n\n{body}\n"
    try:
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(
            f"sweep: git commit failed: {exc.stderr or exc.stdout}\n"
        )
        return 1
    print(f"sweep: committed {n_moved_plan_docs} plan-doc moves.")
    print(f"  subject: {subject}")
    return 0
