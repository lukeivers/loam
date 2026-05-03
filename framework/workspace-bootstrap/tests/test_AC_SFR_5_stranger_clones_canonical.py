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

Single-framework restructure (amendment #67). The synthesis pipeline
runs on canonical-side, but the stranger-clones-canonical property
must hold: a `git clone <canonical-url>` (no `--branch`, no
`--recurse-submodules`) produces a working tree byte-identical to
canonical's primary `pos-v2` branch. No bootstrap script required to
make canonical browseable / clone-able.

The `framework-only` branch is a sibling; reachable via
`git fetch origin framework-only` or `git clone --branch
framework-only <canonical-url>` but NOT required for canonical-side
inspection.
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


def test_AC_SFR_5_stranger_clone_byte_identical_to_pos_v2(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """A no-flag `git clone <canonical>` produces a tree byte-identical
    to canonical's `pos-v2` (post-synthesis).

    AC.SFR.5: the synthesis runs against canonical, advancing only
    `framework-only`. The default branch (`pos-v2`) is unchanged. A
    stranger cloning canonical's URL (no `--branch`) sees the full
    pos-v2 tree — `framework/<comp>/` + top-level docs + everything
    else — without needing to know about `framework-only`.
    """
    # The fixture publishes framework-only by default.
    canonical = make_fixture_canonical(tmp_path / "canonical")

    # AC.SFR.5: pos-v2's HEAD + tree are unchanged by the synthesis.
    canonical_pos_v2_sha = _git(["rev-parse", "pos-v2"], cwd=canonical)
    canonical_default_sha = _git(["rev-parse", "HEAD"], cwd=canonical)
    assert canonical_pos_v2_sha == canonical_default_sha, (
        "AC.SFR.5: canonical's HEAD must remain on pos-v2 post-synthesis"
    )

    # AC.SFR.5: a no-branch clone defaults to canonical's primary
    # branch (pos-v2). The cloned tree is byte-identical to pos-v2.
    stranger = tmp_path / "stranger"
    _git(["clone", str(canonical), str(stranger)], cwd=tmp_path)

    # Stranger's HEAD == canonical's pos-v2.
    stranger_head = _git(["rev-parse", "HEAD"], cwd=stranger)
    assert stranger_head == canonical_pos_v2_sha

    # Stranger's checked-out branch == pos-v2 (default).
    stranger_branch = _git(
        ["rev-parse", "--abbrev-ref", "HEAD"], cwd=stranger
    )
    assert stranger_branch == "pos-v2"

    # Tree byte-identity: every file in the stranger's tree byte-equals
    # canonical's pos-v2 tree (excluding .git/).
    canonical_tree = _git(
        ["ls-tree", "-r", "--name-only", "pos-v2"], cwd=canonical
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
        canonical_bytes = _git(["show", f"pos-v2:{rel}"], cwd=canonical)
        stranger_bytes = (stranger / rel).read_text()
        assert canonical_bytes + "\n" == stranger_bytes or (
            canonical_bytes == stranger_bytes
        )


def test_AC_SFR_5_framework_only_reachable_via_explicit_branch(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """The `framework-only` branch is reachable via explicit fetch /
    clone-with-branch — but not required for canonical inspection.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")

    # Explicit fetch.
    bare_clone = tmp_path / "bare-clone"
    _git(
        ["clone", "--branch", "framework-only", str(canonical),
         str(bare_clone)],
        cwd=tmp_path,
    )
    bare_branch = _git(
        ["rev-parse", "--abbrev-ref", "HEAD"], cwd=bare_clone
    )
    assert bare_branch == "framework-only"

    # The framework-only clone has the synthetic shape: post-FBE.2b
    # (amendment #109) the synth pipeline preserves canonical's
    # `framework/` prefix on shipped paths verbatim, so component
    # leaves on the framework-only branch live at
    # `framework/<comp>/...`. Top-level docs (CLAUDE.md, docs/...)
    # remain at synth-tree root because they were never under
    # `framework/` in pos-v2. AC.FBE.2c.4 (amendment #111): this
    # assertion mirrors the FBE.2b synth contract; the workspace-
    # bootstrap-side mirror of the path-shape inversion FBE.2b
    # applied to the synth-pipeline tests inside
    # `framework/tools/pos-publish-framework-only/tests/`.
    bare_tree = _git(
        ["ls-tree", "-r", "--name-only", "HEAD"], cwd=bare_clone
    )
    paths = bare_tree.split("\n")
    # AC.FBE.2c.4: at-least-one framework-prefixed leaf for shipping
    # components (the inversion of the pre-FBE.2b strip-shape
    # assertion).
    assert any(p.startswith("framework/") for p in paths), (
        "AC.FBE.2c.4: at least one framework/-prefixed leaf required "
        "post-FBE.2b synth (prefix-preserving shape); none found in "
        f"{paths!r}"
    )
    # Top-level docs at root.
    assert "CLAUDE.md" in paths
