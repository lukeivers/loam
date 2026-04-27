"""Operator-facing audit summary helpers.

Authored fresh. Renders a short audit summary the CLI shows the
operator before the apply/reject gate (AC.WS.7). Composable by the
future ``/sync`` slash-command (Lens 1) so the same rendering is
reusable in non-CLI surfaces.
"""

from __future__ import annotations

import sys

from .conflict_report import ConflictEntry, ConflictReport, Resolution


def summarize_audit_for_operator(report: ConflictReport) -> str:
    """Render a short summary of resolutions, low-confidence first.

    The returned string is suitable for non-TTY output (grep-friendly,
    one-line-per-conflict). The persona can layer richer rendering
    (e.g. natural-language summaries via the LLM) on top; this is
    the deterministic fallback.
    """
    sorted_entries = report.sorted_low_confidence_first()
    lines: list[str] = [
        f"sync_ref:    {report.sync_ref}",
        f"detected_at: {report.detected_at}",
        f"total:       {len(report.conflicts)}",
    ]

    inferred = [c for c in sorted_entries if c.resolution in (
        Resolution.INFERRED_ACCEPT_CANONICAL,
        Resolution.INFERRED_ACCEPT_WORKSPACE,
        Resolution.INFERRED_MERGED,
    )]
    if inferred:
        lines.append("")
        lines.append("Inferred resolutions (low-confidence first):")
        for c in inferred:
            conf = c.confidence if c.confidence is not None else 0.0
            lines.append(
                f"  [{conf:.2f}] {c.resolution.value} {c.path}: "
                f"{(c.rationale or '').splitlines()[0][:120]}"
            )

    structural = [c for c in sorted_entries if c.resolution in (
        Resolution.KEEP_LOCAL,
        Resolution.ACCEPT_UPSTREAM,
        Resolution.AUTO_ACCEPT_LOCAL_MATCHES_UPSTREAM,
    )]
    if structural:
        lines.append("")
        lines.append("Class-A/B / auto-resolved:")
        for c in structural:
            lines.append(f"  {c.resolution.value} {c.path}")

    pending = [c for c in sorted_entries if c.resolution is Resolution.PENDING]
    if pending:
        lines.append("")
        lines.append(f"PENDING ({len(pending)}):")
        for c in pending:
            lines.append(f"  {c.path}")

    return "\n".join(lines)


def confirmed_by_operator(
    summary: str,
    *,
    auto_accept: bool,
    all_confidences_meet_floor: bool,
    interactive: bool | None = None,
) -> bool:
    """Return True if the operator (or auto-accept gate) authorises apply.

    Auto-accept is opt-in (Hard Constraint #8): ``auto_accept`` flag
    must be True AND every inferred verdict's confidence must meet
    the floor before the auto path applies. Otherwise, interactive
    confirmation is required; non-TTY (``interactive=False``)
    produces False (no apply, fail-closed).

    The summary is printed to stderr so stdout remains the
    machine-parseable surface.
    """
    if auto_accept and all_confidences_meet_floor:
        return True

    if interactive is None:
        interactive = sys.stdin.isatty() and sys.stderr.isatty()

    if not interactive:
        # Non-TTY: do not prompt. Treat as no-confirm; the caller
        # discards staging.
        print(summary, file=sys.stderr)
        print(
            "[workspace-sync] non-TTY invocation; auto-accept not enabled "
            "or confidence floor not met. Discarding staging.",
            file=sys.stderr,
        )
        return False

    print(summary, file=sys.stderr)
    print("", file=sys.stderr)
    print(
        "[workspace-sync] Apply staging to workspace? "
        "Type 'yes' to apply, anything else to discard:",
        file=sys.stderr,
        flush=True,
    )
    try:
        answer = input().strip().lower()
    except EOFError:
        return False
    return answer == "yes"
