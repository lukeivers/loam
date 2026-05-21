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

"""Bundle A.1 — workspace-sync just-behind integration test
(AC.JBC.4).

A genuine just-behind conflict requires a three-way state where:
  - workspace HEAD ≠ merge base (workspace touched the file),
  - canonical HEAD ≠ merge base (canonical advanced),
  - ours ≠ theirs (so git produces a conflict),
  - workspace's current bytes equal SOME ancestor of canonical HEAD
    (not the merge base — that would auto-resolve to theirs).

Concretely: canonical advances v1 → v2 → v3 on a file; workspace
sets the same file's bytes to v2's content. Three-way merge: ours
= "v2", base = "v1", theirs = "v3" → conflict markers. Fast-path
inspects ours = v2 and finds it byte-matches canonical's v2 commit
(an ancestor of canonical HEAD v3) → accept theirs without LLM
call.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import _stub_resolver
from loam.workspace_sync.cli import main as cli_main
from loam.workspace_sync.merge_resolver import MergeVerdict


def _git(args: list[str], *, cwd: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


# ---- AC.JBC.4 — integration ----------------------------------------


def test_AC_JBC_4_just_behind_fast_path_resolves_without_llm(
    make_framework_workspace, advance_canonical, workspace_commit
):
    """Pure just-behind: workspace commits an OLDER canonical version
    of a file; canonical advances past that version. The fast-path
    accepts canonical's HEAD version without invoking the LLM.

    Resolver invocation count == 0.
    """
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={"src/foo.py": "x = 1  # canonical v1\n"},
    )
    framework = fixture_ws / "framework"

    # Canonical advances v1 → v2 → v3 BEFORE the workspace touches
    # the file. The workspace's framework clone is still pinned at
    # v1 (the original clone point).
    advance_canonical(
        canonical_root,
        {"src/foo.py": "x = 2  # canonical v2\n"},
        message="canonical v2",
    )
    advance_canonical(
        canonical_root,
        {"src/foo.py": "x = 3  # canonical v3\n"},
        message="canonical v3",
    )

    # Workspace sets foo.py to v2's content (an ancestor-of-canonical-HEAD
    # version, but not equal to the merge base which is v1).
    workspace_commit(
        fixture_ws,
        {"src/foo.py": "x = 2  # canonical v2\n"},
        message="workspace pin to v2",
    )

    _stub_resolver.reset()

    rc = cli_main(
        [
            "--workspace",
            str(fixture_ws),
            "--merge-resolver-module",
            "_stub_resolver",
            "--auto-accept",
        ]
    )
    assert rc == 0, "sync should succeed via fast-path"

    # AC.JBC.4 critical assertion: the LLM resolver was never invoked.
    assert _stub_resolver.invocations() == [], (
        f"expected zero LLM invocations on pure just-behind; "
        f"got {_stub_resolver.invocations()}"
    )

    # File now holds canonical's HEAD (v3).
    assert (framework / "src/foo.py").read_text() == (
        "x = 3  # canonical v3\n"
    )

    # Working tree is clean.
    porcelain = _git(["status", "--porcelain"], cwd=framework)
    assert porcelain == "", (
        f"working tree should be clean post-merge; got {porcelain!r}"
    )


def test_AC_JBC_4_mixed_just_behind_and_divergent(
    make_framework_workspace, advance_canonical, workspace_commit
):
    """Mixed: one file is just-behind; one file is truly divergent.
    Fast-path handles the just-behind file (zero LLM invocations on
    its path); the divergent file falls through to the LLM resolver.

    Critical assertion: ``src/just_behind.py`` MUST NOT appear in
    the resolver's invocation log. The divergent file MAY trigger
    multiple LLM invocations (classifier + generator) — that
    accounting is out of scope for this AC; AC.JBC.4 cares only
    that the fast-path bypasses the LLM for the just-behind file.
    """
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={
            "src/just_behind.py": "x = 1  # canonical v1\n",
            "src/divergent.py": "y = 1  # canonical v1\n",
        },
    )
    framework = fixture_ws / "framework"

    # Canonical advances both files multiple commits.
    advance_canonical(
        canonical_root,
        {
            "src/just_behind.py": "x = 2  # canonical v2\n",
            "src/divergent.py": "y = 2  # canonical v2\n",
        },
        message="canonical v2",
    )
    advance_canonical(
        canonical_root,
        {
            "src/just_behind.py": "x = 3  # canonical v3\n",
            "src/divergent.py": "y = 3  # canonical v3\n",
        },
        message="canonical v3",
    )

    # Workspace commits:
    #  - just_behind.py: set to canonical's v2 content (an
    #    ancestor of canonical HEAD).
    #  - divergent.py: set to a content that exists nowhere in
    #    canonical's history.
    workspace_commit(
        fixture_ws,
        {
            "src/just_behind.py": "x = 2  # canonical v2\n",
            "src/divergent.py": "y = 99  # workspace-only\n",
        },
        message="workspace edits",
    )

    _stub_resolver.reset()

    rc = cli_main(
        [
            "--workspace",
            str(fixture_ws),
            "--merge-resolver-module",
            "_stub_resolver",
            "--auto-accept",
        ]
    )
    assert rc == 0, "sync should succeed with fast-path + LLM combo"

    invocation_paths = [inv["path"] for inv in _stub_resolver.invocations()]

    # AC.JBC.4 critical assertion: fast-path file is NEVER passed
    # to the LLM resolver.
    assert "src/just_behind.py" not in invocation_paths, (
        f"just_behind.py must not appear in resolver invocations; "
        f"got {invocation_paths}"
    )

    # The divergent file SHOULD have been passed to the resolver
    # at least once (the fast-path correctly rejected it).
    assert "src/divergent.py" in invocation_paths, (
        f"divergent.py must reach the LLM resolver; "
        f"got {invocation_paths}"
    )

    # Fast-path file: holds canonical's v3.
    assert (framework / "src/just_behind.py").read_text() == (
        "x = 3  # canonical v3\n"
    )

    # Clean tree post-merge.
    porcelain = _git(["status", "--porcelain"], cwd=framework)
    assert porcelain == ""


def test_AC_JBC_4_fast_path_verdict_recorded_in_audit(
    make_framework_workspace, advance_canonical, workspace_commit
):
    """Fast-path resolutions are recorded under the resolver-runs
    audit directory just like LLM resolutions — preserves audit
    parity between the two paths.
    """
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={"src/foo.py": "x = 1\n"},
    )
    advance_canonical(
        canonical_root,
        {"src/foo.py": "x = 2\n"},
        message="canonical v2",
    )
    canon_sha = advance_canonical(
        canonical_root,
        {"src/foo.py": "x = 3\n"},
        message="canonical v3",
    )
    workspace_commit(
        fixture_ws,
        {"src/foo.py": "x = 2\n"},  # ancestor-of-canonical content
        message="workspace pin to v2",
    )

    _stub_resolver.reset()

    rc = cli_main(
        [
            "--workspace",
            str(fixture_ws),
            "--merge-resolver-module",
            "_stub_resolver",
            "--auto-accept",
        ]
    )
    assert rc == 0
    assert _stub_resolver.invocations() == [], (
        "fast-path must not invoke the LLM"
    )

    runs_dir = (
        fixture_ws
        / "workspace"
        / ".pos"
        / "sync"
        / "resolver-runs"
        / canon_sha
    )
    assert runs_dir.exists()
    yaml_files = list(runs_dir.glob("*.yaml"))
    assert len(yaml_files) == 1
    assert yaml_files[0].name == "src__foo.py.yaml"

    import yaml as _yaml

    raw = _yaml.safe_load(yaml_files[0].read_text())
    assert raw["path"] == "src/foo.py"
    assert raw["verdict"]["resolution"] == "inferred-accept-canonical"
    assert raw["verdict"]["confidence"] == 1.0
    assert "just-behind fast-path" in raw["verdict"]["rationale"]
