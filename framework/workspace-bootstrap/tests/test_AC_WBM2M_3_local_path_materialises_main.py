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

"""AC.WBM2M.3 — _materialise_canonical_branch is idempotent on the
typical case where ``main`` is already a local branch on the source.

Post-OSS-dev-architecture-migration (2026-05-04): with ``main`` as
canonical's default branch, ``git clone <canonical>`` propagates
``main`` as a LOCAL branch on the stranger-clone (not just as a
remote-tracking ref). The materialise helper's ``git update-ref``
operation is therefore a no-op idempotency on this typical case —
the local ref already points at the same SHA the materialise call
would set it to.

The helper is retained for symmetry with cache-clone scenarios + as
defense against any future scenario where ``CANONICAL_BRANCH`` is a
non-default branch on the source.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam.workspace_bootstrap.new_workspace import (
    _materialise_canonical_branch,
)


def _git(args: list[str], *, cwd: Path) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip("\n")


def test_AC_WBM2M_3_materialise_is_idempotent_on_local_main(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """The materialise helper is idempotent when ``main`` is already
    a LOCAL branch on the path (the typical post-migration case).

    Steps:
      1. Build a fixture canonical (initialised on ``main``).
      2. Clone it (the stranger-clone has ``main`` as a LOCAL branch
         because ``main`` was the source's default).
      3. Capture the SHA of ``refs/heads/main`` pre-materialise.
      4. Call ``_materialise_canonical_branch`` against the clone.
      5. Verify ``refs/heads/main`` SHA is unchanged (no-op idempotency).
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")
    stranger_clone = tmp_path / "stranger-clone"
    _git(["clone", str(canonical), str(stranger_clone)], cwd=tmp_path)

    # Pre-condition: main IS a local branch (canonical's default).
    pre_sha = _git(
        ["rev-parse", "refs/heads/main"], cwd=stranger_clone
    )
    assert pre_sha, "fixture pre-condition: main must exist as a local ref"

    # Materialise (no-op idempotency on this case).
    _materialise_canonical_branch(stranger_clone)

    # Post: SHA unchanged.
    post_sha = _git(
        ["rev-parse", "refs/heads/main"], cwd=stranger_clone
    )
    assert post_sha == pre_sha, (
        f"AC.WBM2M.3: materialise should be a no-op on local-main "
        f"case; pre={pre_sha!r}, post={post_sha!r}"
    )


def test_AC_WBM2M_3_materialise_fails_soft_on_missing_remote_tracking(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """The materialise helper is fail-soft (non-zero exit ignored).

    When the remote-tracking ref is absent (e.g. the source has no
    ``origin/main`` remote-tracking ref configured), ``git update-ref``
    exits non-zero. The materialise helper does NOT raise — the
    downstream ``_clone_canonical`` checkout step diagnoses any
    actual breakage with a structured ``CloneFailedError``.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")

    # Note: canonical is an `init`d repo (no `origin` remote configured).
    # So `refs/remotes/origin/main` does NOT exist on canonical.
    # The materialise call should be fail-soft — no exception.
    _materialise_canonical_branch(canonical)

    # Verify no exception bubbled up. Implicit assertion: the prior
    # line did not raise.
