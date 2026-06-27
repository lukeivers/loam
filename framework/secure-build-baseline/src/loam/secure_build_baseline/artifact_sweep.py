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

"""AC.SBB.3 (part 2) — the pre-commit sweep.

A correct ``.gitignore`` (``gitignore_template``) is necessary but not
sufficient: a broad-stage command (``git add -A`` / ``git add .`` /
``git commit -a``) can still pull harness runtime state into the artifact
if the ``.gitignore`` is incomplete or a path was force-added. The sweep
is the runtime enforcement: it inspects the repository the command targets
and reports any harness-runtime-state / secret path that is present AND
NOT ignored by git — i.e. a path that WOULD enter the artifact under a
broad stage. The hook turns a non-empty offending list into a block (or a
surface notice, per strictness).

Stdlib only (the helper is imported by the bare-script hook). Every git
invocation fails SOFT (an error yields an empty offending list) so a git
read failure never blocks a build.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


# Path globs the sweep treats as harness-runtime-state / secret class —
# the set that must never enter a generated artifact. Kept in lockstep
# with ``gitignore_template`` (the ``.gitignore`` floor declares the same
# set; the sweep enforces it at the boundary).
RUNTIME_STATE_GLOBS: tuple[str, ...] = (
    ".scratch",
    ".pos",
    ".loam/memory/queue",
    "*.sqlite",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    ".npmrc",
    ".pypirc",
)

# Sample/example secret files are explicitly NOT offending.
_ALLOWED_SECRET_SAMPLES = re.compile(r"\.(?:example|sample|template)$")

# A broad-stage command: stages the whole tree, so .gitignore is the only
# thing between runtime state and the artifact.
_BROAD_STAGE_RE = re.compile(
    r"\bgit\b(?:\s+-{1,2}\S+)*\s+add\b(?:(?!\b--?(?:patch|interactive|p|i)\b).)*"
    r"(?:\s(?:-A|--all|\.|:/|\*))",
)
_COMMIT_ALL_RE = re.compile(r"\bgit\b(?:\s+-{1,2}\S+)*\s+commit\b[^\n]*\s-\w*a")


def is_broad_stage_command(command: str) -> bool:
    """True iff *command* stages the whole tree (``git add -A`` / ``.`` /
    ``--all``) or commits everything (``git commit -a``) — the boundary the
    sweep guards."""
    return bool(_BROAD_STAGE_RE.search(command) or _COMMIT_ALL_RE.search(command))


def _git_check_ignored(repo_root: Path, candidate: str) -> bool | None:
    """Return True iff *candidate* is git-ignored in *repo_root*.

    ``None`` when git could not answer (not a repo / git missing) — the
    caller treats ``None`` as "cannot prove, fail soft, do not flag"."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "check-ignore", "-q", candidate],
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    # exit 0 => ignored; exit 1 => NOT ignored; exit 128 => error.
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    return None


def _present_runtime_state_paths(repo_root: Path) -> list[str]:
    """Return the runtime-state-class paths that actually exist in the tree."""
    found: list[str] = []
    for glob in RUNTIME_STATE_GLOBS:
        if any(ch in glob for ch in "*?[]"):
            for match in repo_root.rglob(glob):
                rel = match.relative_to(repo_root).as_posix()
                found.append(rel)
        else:
            target = repo_root / glob
            if target.exists():
                found.append(glob)
    # Deterministic, de-duplicated.
    return sorted(set(found))


def offending_paths(repo_root: Path) -> list[str]:
    """Return runtime-state paths present in *repo_root* that are NOT
    git-ignored — the paths that would enter the artifact under a broad
    stage. Sample/example secret files are excluded. Fail-soft: a git read
    failure for a path drops it from the offending list (cannot prove it
    would leak, so do not block)."""
    offending: list[str] = []
    for rel in _present_runtime_state_paths(repo_root):
        if _ALLOWED_SECRET_SAMPLES.search(rel):
            continue
        ignored = _git_check_ignored(repo_root, rel)
        if ignored is False:
            offending.append(rel)
    return sorted(set(offending))
