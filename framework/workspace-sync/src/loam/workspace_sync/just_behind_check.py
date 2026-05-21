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

"""Workspace-sync content-vs-canonical-history fast-path
(Bundle A.1 of `docs/FUTURE_IDEAS_DRAFT.md`).

When a conflicted file's workspace-side content byte-equals the
file's content at SOME ancestor commit reachable from canonical's
HEAD, the workspace is "just behind" canonical for that file — not
actually divergent. Accepting canonical's version is structurally
safe and reduces first-sync cost from
``O(diverged-files × LLM)`` to ``O(diverged-files × git-rev-walk)``.

Public entry-point:

    is_just_behind(framework_root, file_path, workspace_content,
                   canonical_head_sha, *, max_depth=200)
        -> (matched: bool, matching_ancestor_sha: str | None)

The walk is bounded by ``max_depth`` (default 200 commits along the
file's first-parent-aware history) so a deeply-rooted file does not
turn the fast-path into an unbounded computation.

ACs (per dispatch brief 2026-05-21):

* AC.JBC.1 — true-positive: when ``workspace_content`` byte-equals
  the file's content at some ancestor of ``canonical_head_sha``,
  return ``(True, <ancestor-sha>)``.
* AC.JBC.2 — true-negative: when the workspace content matches
  nothing in canonical's history for the file, return
  ``(False, None)``.
* AC.JBC.3 — bounded depth: the walk inspects at most ``max_depth``
  commits before giving up; on a longer file history, return
  ``(False, None)`` rather than walking indefinitely.
* AC.JBC.4 — integration: a synthetic sync with one just-behind
  file and one truly-divergent file uses the fast-path for the
  former and falls through to the LLM resolver for the latter
  (covered by the CLI-side test, not in this module).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


_DEFAULT_MAX_DEPTH = 200


def _git_capture(
    framework_root: Path, args: list[str]
) -> subprocess.CompletedProcess[bytes]:
    """Run git with -C framework_root capturing bytes (no text decode).

    Bytes mode is load-bearing for AC.JBC.1: file content comparison
    must compare raw bytes so encoding fidelity is preserved.
    """
    argv = ["git", "-C", str(framework_root), *args]
    return subprocess.run(  # noqa: S603 — argv constructed from typed args
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def is_just_behind(
    framework_root: Path,
    file_path: str,
    workspace_content: bytes,
    canonical_head_sha: str,
    *,
    max_depth: int = _DEFAULT_MAX_DEPTH,
) -> tuple[bool, str | None]:
    """Return ``(True, ancestor_sha)`` when ``workspace_content`` byte-
    equals ``file_path``'s blob at some ancestor commit reachable from
    ``canonical_head_sha``; ``(False, None)`` otherwise.

    Algorithm:
      1. ``git log <canonical_head_sha> -n <max_depth> --pretty=%H
         -- <file_path>`` to enumerate commits in canonical's history
         that touched the file.
      2. For each commit (in order, newest → oldest), compare
         ``git show <commit_sha>:<file_path>`` bytes against
         ``workspace_content``.
      3. Return ``(True, <sha>)`` on the first match; ``(False,
         None)`` if no match within the bounded window.

    AC.JBC.1: matching ancestor → True path. AC.JBC.2: no match →
    False path. AC.JBC.3: ``-n <max_depth>`` enforces the upper
    bound.
    """
    # AC.JBC.3 — bounded walk: -n caps git log output at max_depth.
    log_result = _git_capture(
        framework_root,
        [
            "log",
            canonical_head_sha,
            f"-n{max_depth}",
            "--pretty=%H",
            "--",
            file_path,
        ],
    )
    if log_result.returncode != 0:
        return (False, None)
    # AC.JBC.2 default: no commits touched the file → no match.
    candidate_shas = [
        ln.decode("ascii", errors="replace").strip()
        for ln in log_result.stdout.splitlines()
        if ln.strip()
    ]
    if not candidate_shas:
        return (False, None)

    for sha in candidate_shas:
        # AC.JBC.1 — byte-content equality is the match predicate.
        show_result = _git_capture(
            framework_root, ["show", f"{sha}:{file_path}"]
        )
        if show_result.returncode != 0:
            # File absent at this commit (e.g., pre-add); skip.
            continue
        if show_result.stdout == workspace_content:
            return (True, sha)

    # AC.JBC.2 — exhausted the bounded window with no match.
    return (False, None)
