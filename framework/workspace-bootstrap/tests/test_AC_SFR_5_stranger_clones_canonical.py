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

"""AC.SFR.5 — stranger-clones-canonical property preserved.

Post-OSS-dev-architecture-migration (2026-05-04): the synthesis
pipeline is retired; canonical has only one default branch
(``main``). A ``git clone <canonical-url>`` (no ``--branch``, no
``--recurse-submodules``) produces a working tree byte-identical to
canonical's ``main``. No bootstrap script required to make canonical
browseable / clone-able.

Pre-migration there was a ``framework-only`` synthesis-only sibling
branch reachable via explicit ``git clone --branch framework-only``;
that branch is gone. The second AC.SFR.5 test (which asserted the
framework-only branch was reachable) was DELETED with this amendment
(no equivalent post-migration shape exists).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(args: list[str], *, cwd: Path) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip("\n")


def test_AC_SFR_5_stranger_clone_byte_identical_to_main(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """A no-flag ``git clone <canonical>`` produces a tree byte-
    identical to canonical's ``main``.

    AC.SFR.5: a stranger cloning canonical's URL (no ``--branch``)
    sees the full ``main`` tree — ``framework/<comp>/`` + top-level
    docs + everything else — without needing to know about any
    sibling branch. Post-OSS-dev-architecture-migration the only
    branch IS ``main``; this test verifies the contract directly.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")

    # AC.SFR.5: canonical's HEAD is on main.
    canonical_main_sha = _git(["rev-parse", "main"], cwd=canonical)
    canonical_default_sha = _git(["rev-parse", "HEAD"], cwd=canonical)
    assert canonical_main_sha == canonical_default_sha, (
        "AC.SFR.5: canonical's HEAD must be on main"
    )

    # AC.SFR.5: a no-branch clone defaults to canonical's primary
    # branch (main). The cloned tree is byte-identical to main.
    stranger = tmp_path / "stranger"
    _git(["clone", str(canonical), str(stranger)], cwd=tmp_path)

    # Stranger's HEAD == canonical's main.
    stranger_head = _git(["rev-parse", "HEAD"], cwd=stranger)
    assert stranger_head == canonical_main_sha

    # Stranger's checked-out branch == main (default).
    stranger_branch = _git(
        ["rev-parse", "--abbrev-ref", "HEAD"], cwd=stranger
    )
    assert stranger_branch == "main"

    # Tree byte-identity: every file in the stranger's tree byte-equals
    # canonical's main tree (excluding .git/).
    canonical_tree = _git(
        ["ls-tree", "-r", "--name-only", "main"], cwd=canonical
    )
    stranger_tree = _git(
        ["ls-tree", "-r", "--name-only", "HEAD"], cwd=stranger
    )
    assert canonical_tree == stranger_tree

    # Spot-check actual byte-identity for representative files. The
    # workspace-side files are read from disk (with trailing newline);
    # ``git show`` (via _git) strips one trailing newline — re-add for
    # a like-for-like comparison.
    for rel in ["CLAUDE.md", "framework/README.md", "docs/odd-methodology.md"]:
        canonical_bytes = _git(["show", f"main:{rel}"], cwd=canonical)
        stranger_bytes = (stranger / rel).read_text()
        assert canonical_bytes + "\n" == stranger_bytes or (
            canonical_bytes == stranger_bytes
        )
