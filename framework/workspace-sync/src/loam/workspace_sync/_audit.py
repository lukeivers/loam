# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Operator-facing audit summary helpers (D-migration D.3 shape).

D-migration D.3 (amendment #64) — under the git-merge architecture,
the operator's "what did this sync do?" briefing splits between:

  - ``git log <prev>..<new> --oneline`` — the canonical-side commits
    that landed (the CLI emits this directly from ``cli.py``).
  - This module's ``summarize_resolver_runs`` — the LLM-resolver
    fallback verdicts (only emitted on the rare-conflict path).

Pre-D.3 this module rendered ``ConflictReport`` shapes; post-D.3
it renders ``list[(rel_path, MergeVerdict)]`` (the result type of
``cli._resolve_conflicts_via_llm``).
"""

from __future__ import annotations

import sys

from .merge_resolver import MergeVerdict


def summarize_resolver_runs(
    results: list[tuple[str, MergeVerdict]],
) -> str:
    """Render a short summary of the LLM-resolver fallback verdicts.

    Returns a string suitable for non-TTY output, sorted low-confidence
    first so a reviewer scanning the summary sees the most-uncertain
    verdicts at the top.
    """
    if not results:
        return "(no LLM-resolver verdicts; merge auto-resolved by git)"

    sorted_results = sorted(results, key=lambda rv: (rv[1].confidence, rv[0]))
    lines: list[str] = [
        f"LLM-resolver fallback fired ({len(results)} "
        f"conflict{'s' if len(results) != 1 else ''}, low-confidence first):",
    ]
    for rel_path, verdict in sorted_results:
        first_rationale_line = (verdict.rationale or "").splitlines()[0][:120]
        lines.append(
            f"  [{verdict.confidence:.2f}] {verdict.resolution} "
            f"{rel_path}: {first_rationale_line}"
        )
    return "\n".join(lines)


def confirmed_by_operator(
    summary: str,
    *,
    auto_accept: bool,
    all_confidences_meet_floor: bool,
    interactive: bool | None = None,
) -> bool:
    """Return True if the operator (or auto-accept gate) authorises apply.

    Auto-accept is opt-in: ``auto_accept`` flag must be True AND
    every verdict's confidence must meet the floor before the auto
    path applies. Otherwise interactive confirmation is required;
    non-TTY (``interactive=False``) produces False (no apply,
    fail-closed).

    The summary is printed to stderr so stdout remains the
    machine-parseable surface.
    """
    if auto_accept and all_confidences_meet_floor:
        return True

    if interactive is None:
        interactive = sys.stdin.isatty() and sys.stderr.isatty()

    if not interactive:
        # Non-TTY: do not prompt. Treat as no-confirm; the caller
        # aborts the merge (fail-closed).
        print(summary, file=sys.stderr)
        print(
            "[workspace-sync] non-TTY invocation; auto-accept not "
            "enabled or confidence floor not met. Aborting merge.",
            file=sys.stderr,
        )
        return False

    print(summary, file=sys.stderr)
    print("", file=sys.stderr)
    print(
        "[workspace-sync] Apply LLM-resolver verdicts (commit merge)? "
        "Type 'yes' to commit, anything else to abort:",
        file=sys.stderr,
        flush=True,
    )
    try:
        answer = input().strip().lower()
    except EOFError:
        return False
    return answer == "yes"
