"""Per-gate pre-publish verification (AC.V060.2).

Six structural gates, each returning a :class:`GateResult` carrying
a verdict + a corrective hint on RED. The orchestrator
(:mod:`loam_cli.release.runner`) runs every gate (does NOT short-
circuit on first RED) so the operator sees the full state in one
report rather than chasing one failure at a time. Per AC.V060.2
spec each gate has its own corrective hint (not a generic error).

Default Path A per D-V060.2: single module, per-gate functions, no
plugin registry. Each ``check_*`` function takes ``(repo_root,
version)`` plus any extra context and returns ``GateResult``.

Gates:
  1. ``check_hard_smoke`` — ``docs/experiments/<version>-hard-smoke.md``
     exists + contains the literal ``GREEN`` token.
  2. ``check_acs_verified`` — ``docs/plans/<version-slug>.md`` plan-doc
     §status / §verdict-matrix marks each AC GREEN.
  3. ``check_state_shipped`` — ``docs/STATE.md`` mentions the version
     followed by ``SHIPPED``.
  4. ``check_clean_tree`` — ``git status --porcelain`` returns empty.
  5. ``check_branch_main`` — ``git branch --show-current`` returns
     ``main`` (revised from ``pos-v2`` per the plan-doc revision).
  6. ``check_seal_commit_reachable`` — the seal SHA from
     ``docs/release-roadmap.md`` §2 row is reachable from HEAD.

Each gate is independently testable; per-gate test pairs (one passing,
one failing) live in
``framework/tools/loam/tests/test_AC_V060_2_*.py``.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GateResult:
    """Verdict for a single pre-publish gate.

    ``ok`` carries the boolean verdict; ``message`` carries either a
    one-line success summary or a multi-line corrective hint on
    failure. ``name`` is the short gate identifier used in report
    headers (``hard-smoke`` / ``acs-verified`` / ``state-shipped`` /
    ``clean-tree`` / ``branch-main`` / ``seal-reachable``).
    """

    name: str
    ok: bool
    message: str


# --------------------------------------------------------------------
# Gate 1 — HARD smoke GREEN (AC.V060.2 #1)
# --------------------------------------------------------------------


def _version_to_slug(version: str) -> str:
    """``v0.6.0`` → ``v0-6-0``; preserves any 4-digit hot-patch form
    such as ``v0.2.5.1`` → ``v0-2-5-1``.
    """
    return version.replace(".", "-")


def check_hard_smoke(repo_root: Path, version: str) -> GateResult:
    """Verify ``docs/experiments/<version-slug>-hard-smoke.md`` exists
    + contains the literal ``GREEN`` verdict token.

    Pattern matches the established v0.4.x hard-smoke writeups (see
    ``docs/experiments/v0-4-3-hard-smoke.md`` for the canonical
    template; the file's first heading + verdict line carry ``GREEN``).
    """
    slug = _version_to_slug(version)
    path = repo_root / "docs" / "experiments" / f"{slug}-hard-smoke.md"
    if not path.exists():
        return GateResult(
            name="hard-smoke",
            ok=False,
            message=(
                f"missing HARD smoke writeup at {path.relative_to(repo_root)}; "
                f"per `feedback_hard_smoke_per_minor_before_publish` every "
                f"minor's last cycle runs HARD smoke against rd-automation "
                f"BEFORE publish gate. Author the writeup + record the "
                f"verdict; re-run `loam release {version}` once GREEN."
            ),
        )
    body = path.read_text(encoding="utf-8")
    # Look for the verdict token. Existing writeups carry "Verdict:
    # GREEN" or "GREEN." in the opening line; either matches the
    # token-presence check.
    if "GREEN" not in body:
        return GateResult(
            name="hard-smoke",
            ok=False,
            message=(
                f"HARD smoke writeup at {path.relative_to(repo_root)} does "
                f"not contain the GREEN verdict token. Re-run the smoke "
                f"against rd-automation; record the verdict line "
                f"(`Verdict: GREEN.`); re-run `loam release {version}` once "
                f"GREEN."
            ),
        )
    return GateResult(
        name="hard-smoke",
        ok=True,
        message=f"HARD smoke GREEN at {path.relative_to(repo_root)}",
    )


# --------------------------------------------------------------------
# Gate 2 — ACs verified per plan-doc (AC.V060.2 #2)
# --------------------------------------------------------------------


def _find_plan_doc(repo_root: Path, version: str) -> Path | None:
    """Locate ``docs/plans/<version-slug>*.md`` for the named version.

    Plan-doc filenames vary slightly: ``v0-6-0-release-process.md`` /
    ``v0-5-0-subagent-personas-routing-and-priming.md``. The lookup
    uses the version's slug as a prefix glob so the filename's
    descriptive tail is permitted.
    """
    slug = _version_to_slug(version)
    plans_dir = repo_root / "docs" / "plans"
    if not plans_dir.is_dir():
        return None
    matches = sorted(plans_dir.glob(f"{slug}-*.md")) + sorted(
        plans_dir.glob(f"{slug}.md")
    )
    return matches[0] if matches else None


def _extract_section_4_body(body: str) -> str | None:
    """Slice the plan-doc body to its `## §4 — Acceptance criteria`
    section.

    Returns the substring between the §4 heading and the next
    ``## §<n>`` boundary (or end-of-doc if §4 is the final section).
    Returns ``None`` if no §4 heading is found.

    Heading-recognition is permissive across the three observed
    forms in the existing plan-doc corpus (verified at v0.7.2
    plan-time across 88 plan-docs):
      - ``## §4 — Acceptance criteria`` (em-dash separator; v0.6.0+)
      - ``## §4. Acceptance criteria`` (period separator; older shape)
      - ``## §4 Acceptance criteria`` (space separator; conftest fixture)

    Per AC.READYP.1: the AC-ID scan is restricted to this slice, so
    cross-reference AC IDs in §6 (out-of-scope), §8 (dependencies),
    §11 (authority chain), §13 (§status), etc. are not flagged as
    in-scope ACs requiring §status verdicts.
    """
    # Match `## §4` followed by an optional separator (em-dash, hyphen,
    # period, or whitespace) and then any heading text. Case-insensitive
    # so a future ``Acceptance Criteria`` capitalisation still resolves.
    heading_match = re.search(
        r"(?im)^##\s*§4\b[^\n]*$",
        body,
    )
    if heading_match is None:
        return None
    section_start = heading_match.end()
    # Next `## §<n>` heading (any digit) bounds the section. End-of-doc
    # is the implicit terminator if §4 is the final ``## §`` block.
    next_section = re.search(
        r"(?m)^##\s*§\d+\b",
        body[section_start:],
    )
    if next_section is None:
        return body[section_start:]
    return body[section_start : section_start + next_section.start()]


def check_acs_verified(repo_root: Path, version: str) -> GateResult:
    """Verify the plan-doc's §status / §verdict-matrix marks each AC
    declared in §4 GREEN.

    Per AC.READYP.1 (v0.7.2 fix): the AC-ID scan is restricted to
    the plan-doc's ``## §4 — Acceptance criteria`` section body
    (between the §4 heading and the next ``## §<n>`` boundary).
    AC IDs appearing in any other section (§1 prime-objective ladder,
    §6 out-of-scope, §8 dependencies, §11 authority chain, §13
    §status, etc.) are NOT treated as in-scope ACs requiring
    §status verdicts. This fixes the v0.7.1 publish-time defect
    where cross-reference AC IDs in §6 + §8 were flagged as missing-
    from-§status.

    A plan-doc passes the gate when the §status / §13 section names
    each §4-declared AC ID alongside a GREEN marker (within 240 chars
    on the same logical span — accommodates table rows + prose
    verdicts).

    For the dogfood self-publish (this very plan-doc), the §status
    backfill is appended at end-of-build; the gate runs against the
    backfilled doc.
    """
    plan_doc = _find_plan_doc(repo_root, version)
    if plan_doc is None:
        return GateResult(
            name="acs-verified",
            ok=False,
            message=(
                f"no plan-doc found at docs/plans/{_version_to_slug(version)}-*.md "
                f"or {_version_to_slug(version)}.md. Plan-before-code per "
                f"`feedback_plan_before_code` requires the plan-doc as the "
                f"AC source-of-truth; author it, backfill §status with each "
                f"AC verdict, then re-run."
            ),
        )
    body = plan_doc.read_text(encoding="utf-8")
    # Per AC.READYP.1 (v0.7.2): scope the AC-ID scan to §4 only.
    # Cross-references in §6 / §8 / §11 / §13 are NOT in-scope ACs.
    section_4 = _extract_section_4_body(body)
    if section_4 is None:
        return GateResult(
            name="acs-verified",
            ok=False,
            message=(
                f"plan-doc at {plan_doc.relative_to(repo_root)} has no "
                f"`## §4 — Acceptance criteria` heading; the `acs-verified` "
                f"gate scopes the AC-ID scan to §4 per the plan-doc "
                f"convention. Add the heading + author the in-scope ACs "
                f"there; re-run."
            ),
        )
    # Find every named AC id in §4 (`AC.V060.1`, `AC.V050.S`, ...).
    ac_ids = sorted(set(re.findall(r"AC\.[A-Z][A-Z0-9_-]*\.[A-Za-z0-9_-]+", section_4)))
    if not ac_ids:
        return GateResult(
            name="acs-verified",
            ok=False,
            message=(
                f"plan-doc at {plan_doc.relative_to(repo_root)} declares no "
                f"AC IDs in §4. Verify the doc is the right shape (§4 "
                f"Acceptance criteria block per ODD §2.5; AC IDs of the "
                f"form `AC.<scope>.<n>`)."
            ),
        )
    # Locate the §status / §13 section (the post-build backfill block).
    status_match = re.search(
        r"(?ms)^##\s*§(?:13|status)\b.*?(?=^##\s|\Z)",
        body,
    )
    status_body = status_match.group(0) if status_match else ""
    missing: list[str] = []
    for ac in ac_ids:
        # An AC counts as verified when the status section names it
        # alongside a GREEN marker on the same logical span (within
        # 240 chars — accommodates table rows + prose verdicts).
        if not status_body:
            missing.append(ac)
            continue
        # Re-search the status body for AC near GREEN.
        ac_pattern = re.compile(
            re.escape(ac) + r".{0,240}?GREEN", re.DOTALL
        )
        if not ac_pattern.search(status_body):
            missing.append(ac)
    if missing:
        return GateResult(
            name="acs-verified",
            ok=False,
            message=(
                f"plan-doc {plan_doc.relative_to(repo_root)} §status does "
                f"not mark these ACs GREEN: {', '.join(missing)}. Backfill "
                f"§status (or §13) with the verdict matrix; each AC must "
                f"appear with a GREEN marker. Re-run once backfilled."
            ),
        )
    return GateResult(
        name="acs-verified",
        ok=True,
        message=(
            f"all {len(ac_ids)} AC(s) marked GREEN in "
            f"{plan_doc.relative_to(repo_root)} §status"
        ),
    )


# --------------------------------------------------------------------
# Gate 3 — STATE.md SHIPPED (AC.V060.2 #3)
# --------------------------------------------------------------------


def check_state_shipped(repo_root: Path, version: str) -> GateResult:
    """Verify ``docs/STATE.md`` mentions the version followed by
    ``SHIPPED``.

    Pattern matches existing STATE.md rollup phrasing — entries take
    the shape ``v0.4.3 SHIPPED 2026-05-09`` / ``v0.5.0 SHIPPED LOCAL``
    / similar. The gate accepts any ``<version> ... SHIPPED`` proximity
    (within 120 chars to allow ``SHIPPED LOCAL`` vs ``SHIPPED PUBLIC``
    qualifiers).
    """
    path = repo_root / "docs" / "STATE.md"
    if not path.exists():
        return GateResult(
            name="state-shipped",
            ok=False,
            message=(
                f"missing {path.relative_to(repo_root)}; canonical "
                f"shipped-state record. Author or restore."
            ),
        )
    body = path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(version) + r"\b.{0,120}?SHIPPED", re.DOTALL
    )
    if not pattern.search(body):
        return GateResult(
            name="state-shipped",
            ok=False,
            message=(
                f"docs/STATE.md does not mark {version} as SHIPPED. Append "
                f"the version's rollup to STATE.md (objective sentence + "
                f"seal SHA + cycle anchors) so future operators find it. "
                f"Re-run once the rollup line is present."
            ),
        )
    return GateResult(
        name="state-shipped",
        ok=True,
        message=f"{version} marked SHIPPED in docs/STATE.md",
    )


# --------------------------------------------------------------------
# Gate 4 — clean tree (AC.V060.2 #4)
# --------------------------------------------------------------------


def check_clean_tree(repo_root: Path, version: str) -> GateResult:
    """Verify ``git status --porcelain`` returns empty at *repo_root*.

    Defensive against half-committed work landing in a publish window.
    """
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    out = proc.stdout.strip()
    if out:
        return GateResult(
            name="clean-tree",
            ok=False,
            message=(
                "uncommitted changes in canonical tree:\n"
                + "\n".join(f"  {line}" for line in out.splitlines())
                + "\nCommit, stash, or revert; re-run."
            ),
        )
    return GateResult(
        name="clean-tree",
        ok=True,
        message="working tree clean",
    )


# --------------------------------------------------------------------
# Gate 5 — branch == main (AC.V060.2 #5)
# --------------------------------------------------------------------


_EXPECTED_BRANCH = "main"


def check_branch_main(repo_root: Path, version: str) -> GateResult:
    """Verify ``git branch --show-current`` returns ``main``.

    The split-worktrees move (2026-05-09) retired the prior
    ``pos-v2`` branch name; canonical post-split is ``main``.
    """
    proc = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    branch = proc.stdout.strip()
    if branch != _EXPECTED_BRANCH:
        return GateResult(
            name="branch-main",
            ok=False,
            message=(
                f"current branch is {branch!r}, expected {_EXPECTED_BRANCH!r}. "
                f"Publish flows from {_EXPECTED_BRANCH} only (the split-"
                f"worktrees move retired the pos-v2 branch). Switch with "
                f"`git switch {_EXPECTED_BRANCH}`; re-run."
            ),
        )
    return GateResult(
        name="branch-main",
        ok=True,
        message=f"on branch {_EXPECTED_BRANCH}",
    )


# --------------------------------------------------------------------
# Gate 6 — seal commit reachable (AC.V060.2 #6)
# --------------------------------------------------------------------


def _extract_seal_sha(roadmap_body: str, version: str) -> str | None:
    """Pull the seal SHA from the §2-shipped table row for *version*.

    §2 rows take the shape::

        | v0.4.3 | <objective sentence> | Single-cycle PATCH: ...
          seal `7bff3817`; ... |

    The seal is a 7+ hex-char token following ``seal``. Prefer the
    last seal in the row when multiple exist (the most-recent
    cycle's seal anchors the version's HEAD).
    """
    # Find the row whose first cell starts with the version.
    row_pattern = re.compile(
        r"^\|\s*" + re.escape(version) + r"\s*\|.*$",
        re.MULTILINE,
    )
    match = row_pattern.search(roadmap_body)
    if match is None:
        return None
    row = match.group(0)
    # All seal tokens in the row.
    seals = re.findall(r"seal[s]?\s*[`']?([0-9a-f]{7,40})", row)
    if not seals:
        return None
    return seals[-1]


def check_seal_commit_reachable(
    repo_root: Path, version: str
) -> GateResult:
    """Verify ``docs/release-roadmap.md`` §2 row carries a seal SHA
    for *version* + that SHA is reachable from HEAD.

    Reachability means ``git merge-base --is-ancestor <seal> HEAD``
    succeeds (rc=0). On RED, surface the seal SHA + the commit it
    anchors so the operator can resolve.
    """
    path = repo_root / "docs" / "release-roadmap.md"
    if not path.exists():
        return GateResult(
            name="seal-reachable",
            ok=False,
            message=(
                f"missing {path.relative_to(repo_root)}; canonical "
                f"forward-looking roadmap. Restore."
            ),
        )
    body = path.read_text(encoding="utf-8")
    seal = _extract_seal_sha(body, version)
    if seal is None:
        return GateResult(
            name="seal-reachable",
            ok=False,
            message=(
                f"docs/release-roadmap.md §2 row for {version} carries no "
                f"seal SHA. Append the seal anchor to the row (cycle SHA "
                f"after `seal `) and re-run."
            ),
        )
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", seal, "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return GateResult(
            name="seal-reachable",
            ok=False,
            message=(
                f"seal commit {seal} declared for {version} in "
                f"docs/release-roadmap.md is NOT reachable from HEAD. "
                f"Either checkout the branch containing the seal, or "
                f"correct the roadmap row to point at the actual seal "
                f"SHA on HEAD's history."
            ),
        )
    return GateResult(
        name="seal-reachable",
        ok=True,
        message=f"seal {seal} reachable from HEAD",
    )


# --------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------


ALL_GATES = (
    check_hard_smoke,
    check_acs_verified,
    check_state_shipped,
    check_clean_tree,
    check_branch_main,
    check_seal_commit_reachable,
)


def run_all(repo_root: Path, version: str) -> list[GateResult]:
    """Run every gate; return the verdict list in declaration order.

    Does NOT short-circuit on first RED — the operator sees every
    failure in one pass.
    """
    return [gate(repo_root, version) for gate in ALL_GATES]


def format_report(results: list[GateResult]) -> str:
    """Pretty-print a list of GateResults for terminal display."""
    lines: list[str] = []
    for r in results:
        marker = "GREEN" if r.ok else "RED"
        lines.append(f"  [{marker}] {r.name}: {r.message}")
    return "\n".join(lines)
