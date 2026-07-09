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

"""``loam release preflight <version>`` — build-time mergeability verb
(AC.PRE.*; audit Class B, the cheap tool-assisted partial).

Emits, for each candidate merge branch, a fast-forward + merge-tree
verdict against ``main``, plus the computed cut (class + expected number)
from the SAME computation the deterministic-cut gate uses
(:mod:`loam_cli.release.cut`; AC.PRE.2 — one mechanism, two entry points).
The output is a stable, structured block a dispatcher pastes verbatim into
the ratification artefact it Tier-0-verifies before dispatch (AC.PRE.3).

HONESTY (D-PRE.PARTIAL): this is a tool-assisted PARTIAL. It only helps if
something runs it — it is NOT the fully-structural pre-dispatch hook that
scans an outgoing brief and blocks the dispatch. That hook is a SEPARATE,
scheduled item, OUT of this cycle (audit Class B). The verb does NOT dress
itself up as structural enforcement.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from loam_cli.release import cut as _cut


@dataclass(frozen=True)
class BranchVerdict:
    """Mergeability verdict for one branch vs ``main``."""

    branch: str
    fast_forwardable: bool
    merge_clean: bool
    detail: str


def _git(*args: str, repo_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )


def _candidate_branches(
    repo_root: Path, main_ref: str, branches: tuple[str, ...] | None
) -> list[str]:
    """The branches to check: the explicit *branches* if given, else every
    local branch not already merged into *main_ref* (the candidate merge
    sources for the cut)."""
    if branches:
        return list(branches)
    proc = _git(
        "branch", "--no-merged", main_ref, "--format=%(refname:short)",
        repo_root=repo_root,
    )
    if proc.returncode != 0:
        return []
    return [b.strip() for b in proc.stdout.splitlines() if b.strip()]


def _verdict_for(
    repo_root: Path, main_ref: str, branch: str
) -> BranchVerdict:
    """Fast-forwardability + merge-tree cleanliness of *branch* onto
    *main_ref*.

    - fast-forwardable: ``main`` is an ancestor of ``branch`` (the branch
      is ahead of main with no divergence), so ``main`` can fast-forward
      to it.
    - merge_clean: ``git merge-tree --write-tree <main> <branch>`` reports
      no conflict (rc==0 on git >= 2.38). A non-zero rc signals conflicts.
    """
    ff = _git(
        "merge-base", "--is-ancestor", main_ref, branch, repo_root=repo_root
    )
    fast_forwardable = ff.returncode == 0

    mt = _git(
        "merge-tree", "--write-tree", main_ref, branch, repo_root=repo_root
    )
    # git >= 2.38: rc 0 = clean, rc 1 = conflicts, rc >1 = error. Treat any
    # non-zero as not-clean (conservative — a preflight advisory).
    merge_clean = mt.returncode == 0
    if mt.returncode == 0:
        detail = "merges cleanly onto main"
    elif mt.returncode == 1:
        detail = "MERGE CONFLICT with main (merge-tree reports conflicts)"
    else:
        detail = f"merge-tree could not evaluate (rc={mt.returncode})"
    if not fast_forwardable:
        detail += "; not fast-forwardable (branch has diverged from main)"
    return BranchVerdict(
        branch=branch,
        fast_forwardable=fast_forwardable,
        merge_clean=merge_clean,
        detail=detail,
    )


def format_preflight(
    version: str,
    cut_result: _cut.CutResult,
    verdicts: list[BranchVerdict],
) -> str:
    """The stable, recordable output block (AC.PRE.3).

    Deterministic ordering (branches sorted) so the block is diff-stable
    when pasted into the ratification artefact.
    """
    lines: list[str] = []
    lines.append(f"== loam release preflight {version} ==")
    if cut_result.determinate and cut_result.expected_version is not None:
        lines.append(
            f"computed cut: class={cut_result.klass} "
            f"expected={cut_result.expected_version} "
            f"(published={cut_result.published}, "
            f"{cut_result.commit_count} unreleased commit(s); "
            f"breaking-markers={'yes' if cut_result.has_breaking else 'no'})"
        )
        if version != cut_result.expected_version:
            lines.append(
                f"  ! target {version} != computed {cut_result.expected_version} "
                f"— the deterministic-cut gate will RED this at publish "
                f"unless {version} is a MAJOR owner-escalation."
            )
    else:
        lines.append(f"computed cut: INDETERMINATE ({cut_result.detail})")
    lines.append("branch mergeability (vs main):")
    if not verdicts:
        lines.append("  (no candidate merge branches — main is the cut)")
    for v in sorted(verdicts, key=lambda x: x.branch):
        ff = "yes" if v.fast_forwardable else "no"
        mc = "clean" if v.merge_clean else "CONFLICT"
        lines.append(f"  {v.branch}: ff={ff} merge={mc} — {v.detail}")
    lines.append(
        "note: preflight is a tool-assisted check (it must be run); it is "
        "NOT a structural pre-dispatch guarantee."
    )
    return "\n".join(lines)


def run_preflight(
    repo_root: Path,
    version: str | None,
    *,
    branches: tuple[str, ...] | None = None,
    main_ref: str = "main",
) -> int:
    """Execute the preflight verb. Returns 0 when it ran, 2 on usage error.

    AC.PRE.5: a missing version is a clean usage error that returns 2 and
    NEVER falls through into the publish/tag path (this function does no
    tagging or pushing whatsoever).
    """
    if not version:
        print(
            "usage: loam release preflight <version>",
            file=sys.stderr,
        )
        return 2
    # Detect candidates first so the computed cut reflects "unreleased
    # seals on main + merging branches" (audit Class A), not main alone.
    candidates = _candidate_branches(repo_root, main_ref, branches)
    cut_result = _cut.compute_cut(
        repo_root, extra_refs=tuple(candidates)
    )
    verdicts = [_verdict_for(repo_root, main_ref, b) for b in candidates]
    print(format_preflight(version, cut_result, verdicts))
    return 0
