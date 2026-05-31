"""``loam audit`` argparse builder + dispatcher (AC.SOL-GATE.* verb arm).

The REAL entry-point the ★ outcome-altitude AC (AC.SOL-PLANTED.1)
drives: generate the STATE-OF-LOAM record FRESH from ground truth, then
compare a doc's structured status claims against it and surface any
divergence. Registered with the unified ``loam`` CLI dispatcher's
``loam.cli.subcommands`` entry-point group (sibling to ``release``).

Surface::

    loam audit [--repo-root <path>] [--doc <path>]... [--state]
               [--settings <path>]

  * ``--state`` (or no ``--doc``): render the derived STATE-OF-LOAM
    record (the R-1 always-loadable surface).
  * ``--doc <path>`` (repeatable): audit each named doc's structured
    status claims against the derived record; exit non-zero iff any
    divergence is found.

Exit code: 0 = clean (no divergence / record rendered); 1 = at least
one divergence detected (the verb arm surfaces; the release-gate arm
HARD-BLOCKs — D3).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from loam_cli.audit.comparator import compare_claims, extract_claims_from_doc
from loam_cli.audit.loam_state import default_state_record
from loam_cli.audit.record import render_record


def build_audit_subcommand(sub: argparse._SubParsersAction) -> None:
    """Register the ``audit`` subcommand on *sub*."""
    p = sub.add_parser(
        "audit",
        help=(
            "derive the STATE-OF-LOAM operative-reality record from "
            "ground truth + surface any doc claim that diverges from it"
        ),
        description=(
            "Generate the STATE-OF-LOAM record FRESH from ground truth "
            "(git ref graph + seal sidecars + live config + real "
            "backend probes) and compare a doc's structured status "
            "claims against it. Surfaces a divergence (a doc claiming a "
            "live component is dark, or vice-versa) — the standing "
            "mechanism that catches built-vs-live drift automatically."
        ),
    )
    p.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="repository root override (default: cwd).",
    )
    p.add_argument(
        "--doc",
        type=Path,
        action="append",
        default=None,
        metavar="<path>",
        help=(
            "a doc to audit for structured status claims that diverge "
            "from the derived record (repeatable). When omitted, the "
            "record is rendered (--state behaviour)."
        ),
    )
    p.add_argument(
        "--state",
        action="store_true",
        help="render the derived STATE-OF-LOAM record + exit.",
    )
    p.add_argument(
        "--settings",
        type=Path,
        default=None,
        metavar="<path>",
        help=(
            "live runtime config (settings.json) override for the hook "
            "probe (default: the canonical pos3 settings.json)."
        ),
    )
    p.set_defaults(func=dispatch)


def dispatch(args: argparse.Namespace) -> int:
    """Run the matched ``loam audit`` invocation. Returns the exit code."""
    repo_root = (args.repo_root or Path.cwd()).resolve()
    record = default_state_record(repo_root, settings_path=args.settings)

    docs = args.doc or []
    if args.state or not docs:
        print(render_record(record))
        if not docs:
            return 0

    covered = frozenset(r.name for r in record.components)
    all_divergences = []
    for doc_path in docs:
        if not doc_path.is_file():
            print(f"WARN: doc not found, skipping: {doc_path}")
            continue
        text = doc_path.read_text(encoding="utf-8")
        claims = extract_claims_from_doc(
            text, source=str(doc_path), components=covered
        )
        divergences = compare_claims(claims, record)
        all_divergences.extend(divergences)

    if all_divergences:
        print("== STATE-OF-LOAM substrate audit: DIVERGENCE ==")
        for d in all_divergences:
            print(f"  [DIVERGENCE] {d.source}: {d.detail}")
        print(
            f"\n{len(all_divergences)} divergence(s) detected. A doc claims "
            "a status that contradicts ground truth (refs + live config + "
            "real probe). Correct the stale claim or re-derive the record."
        )
        return 1

    print("== STATE-OF-LOAM substrate audit: CLEAN ==")
    print(
        "  No structured status claim diverges from the derived record "
        "(ground truth agrees)."
    )
    return 0
