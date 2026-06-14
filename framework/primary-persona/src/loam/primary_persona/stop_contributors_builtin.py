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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""The two shipped Stop-hook contributors (principle-foundation-
structural-enforcement, Slice C).

  * ``permission_ask_contributor`` (AC.PFSE.4): scans the turn's
    OUTBOUND reply for a closing-line permission-ask on authorized work
    (``feedback_no_closing_line_permission_asks`` /
    ``feedback_no_closing_line_permission_asks``). The persona should
    state recommendations as decisions on in-scope authorized work, not
    close with "want me to X?". The contributor surfaces the matched
    pattern as an advisory (rewrite to a decision) — it NEVER blocks.

  * ``terminology_drift_contributor`` (AC.PFSE.7): scans the outbound
    reply for a built/sealed/merged/published CLAIM and, when the
    workspace's git ref graph contradicts it, surfaces the drift
    (``feedback_published_state_only_from_git_refs``). PARTIAL
    enforcement: catches the bounded claim-vs-git-fact shape, not
    arbitrary semantic drift.

Both contributors are deterministic (regex over the reply + a bounded
git-read); NO LLM, NO network. Both run on the Stop hot path under the
exit-0-fast contract, so both are cheap + fail-soft (the registry
swallows a raising contributor).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from .stop_contributor import StopAdvisory


# =====================================================================
# AC.PFSE.4 — permission-ask contributor
# =====================================================================

# Closing-line permission-ask patterns. The persona, on authorized
# in-scope work, should state the recommendation as a decision
# ("Dispatching X now") rather than ask permission ("Want me to dispatch
# X?"). These patterns match the ask shapes; the contributor flags a
# match in the reply's CLOSING region (the last few lines — a
# permission-ask is a closing-line phenomenon).
_PERMISSION_ASK_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\bwant me to\b[^.?!]*\?", re.IGNORECASE),
    re.compile(r"\bshall i\b[^.?!]*\?", re.IGNORECASE),
    re.compile(
        r"\bshould i\b[^.?!]*\b(?:proceed|go ahead|start|dispatch|"
        r"continue|run|build)\b[^.?!]*\?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bconfirm\b[^.?!\n]*\band\b[^.?!\n]*\bi(?:'ll| will)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:let me know if|just let me know)\b[^.?!\n]*\b(?:you'?d "
        r"like|want|prefer|should)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwould you like me to\b[^.?!]*\?", re.IGNORECASE
    ),
    re.compile(
        r"\bdo you want me to\b[^.?!]*\?", re.IGNORECASE
    ),
)

# How many trailing non-blank lines count as the "closing region". A
# permission-ask is a CLOSING-line phenomenon — the last thing the
# reply says. Two lines covers "...did the work.\nWant me to X?" without
# reaching back into mid-reply clarifying questions (which are
# legitimate and must NOT trip the contributor).
_CLOSING_REGION_LINES = 2


def _closing_region(text: str) -> str:
    """The last few non-blank lines of the reply (the closing region)."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines[-_CLOSING_REGION_LINES:])


def permission_ask_contributor(
    *, outbound_reply: str, context: dict[str, Any]
) -> StopAdvisory | None:
    """AC.PFSE.4 — flag a closing-line permission-ask on authorized work.

    Scans the reply's closing region for a permission-ask pattern. On a
    match, returns an advisory naming the matched ask + the rewrite
    direction (state the recommendation as a decision). Returns None on
    a clean reply.

    Conservative: matches only the closing region (a permission-ask is a
    closing-line phenomenon) so a mid-reply question to the user (a
    genuine clarifying question, which is legitimate) does not trip it.
    """
    if not isinstance(outbound_reply, str) or not outbound_reply.strip():
        return None
    region = _closing_region(outbound_reply)
    for pat in _PERMISSION_ASK_PATTERNS:
        m = pat.search(region)
        if m is not None:
            matched = m.group(0).strip()
            return StopAdvisory(
                name="permission-ask",
                message=(
                    f"closing-line permission-ask detected "
                    f"({matched!r}). On in-scope authorized work, state "
                    f"the recommendation as a decision (e.g. "
                    f"'Dispatching X now') rather than asking permission "
                    f"(feedback_no_closing_line_permission_asks). If the "
                    f"work is genuinely critical-call / public-action / "
                    f"financial, the ask is correct — otherwise rewrite."
                ),
            )
    return None


# =====================================================================
# AC.PFSE.7 — terminology / dossier-vs-git drift contributor
# =====================================================================

# A built/sealed/merged/published CLAIM in the reply that names a SHA.
# The contributor checks the named SHA against the workspace git ref
# graph: a claim that "X is sealed/merged at <sha>" when <sha> is not a
# real commit (or the claim's verb disagrees with the ref graph) is
# drift. PARTIAL: bounded to the claim-names-a-sha shape.
_CLAIM_WITH_SHA_RE = re.compile(
    r"\b(sealed|merged|published|committed|applied)\b[^.\n]{0,60}?"
    r"\b([0-9a-f]{7,40})\b",
    re.IGNORECASE,
)


def _sha_is_real_commit(workspace_root: Path, sha: str) -> bool | None:
    """True iff ``sha`` resolves to a commit object in the workspace
    repo; False iff it does not; None iff git is unavailable / the
    check cannot run (so the caller fails open on None)."""
    try:
        proc = subprocess.run(
            ["git", "cat-file", "-t", sha],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        # git ran but the object does not exist -> not a real commit.
        # Distinguish "not found" from "not a git repo": a non-repo
        # prints a fatal to stderr and we cannot trust the verdict.
        if "not a git repository" in (proc.stderr or "").lower():
            return None
        return False
    return proc.stdout.strip() == "commit"


def terminology_drift_contributor(
    *, outbound_reply: str, context: dict[str, Any]
) -> StopAdvisory | None:
    """AC.PFSE.7 — flag a built/sealed/merged/published claim whose named
    SHA the git ref graph contradicts.

    Scans the reply for a ``<verb> ... <sha>`` claim; for each, checks
    the SHA against the workspace git ref graph. A claim naming a SHA
    that is NOT a real commit is drift (the persona asserted a
    sealed/merged state from prose, not the ref graph —
    feedback_published_state_only_from_git_refs). Returns None on a
    clean reply OR when git is unavailable (fail-open).

    PARTIAL enforcement (plan §5): bounded to the claim-names-a-sha
    shape, not arbitrary semantic drift.
    """
    if not isinstance(outbound_reply, str) or not outbound_reply.strip():
        return None
    workspace_root = context.get("workspace_root")
    if not isinstance(workspace_root, Path):
        return None

    drifted: list[str] = []
    seen: set[str] = set()
    for m in _CLAIM_WITH_SHA_RE.finditer(outbound_reply):
        verb = m.group(1).lower()
        sha = m.group(2).lower()
        if sha in seen:
            continue
        seen.add(sha)
        # Skip obvious non-SHA hex words (all-digit short tokens like a
        # year fragment); require at least one a-f hex letter for the
        # 7-char case to reduce false positives on numbers.
        if len(sha) < 8 and not re.search(r"[a-f]", sha):
            continue
        verdict = _sha_is_real_commit(workspace_root, sha)
        if verdict is False:
            drifted.append(f"{verb} {sha}")

    if drifted:
        return StopAdvisory(
            name="terminology-drift",
            message=(
                "built/sealed/merged claim names a SHA the git ref "
                "graph does not contain: "
                + "; ".join(drifted)
                + ". Verify built/sealed/merged/published state from "
                "the git ref graph, not prose "
                "(feedback_published_state_only_from_git_refs). The SHA "
                "may be a typo or a stale-doc carry-forward."
            ),
        )
    return None
