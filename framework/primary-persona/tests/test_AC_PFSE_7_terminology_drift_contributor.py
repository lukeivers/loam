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

"""AC.PFSE.7 — a dossier/narrative claim that disagrees with git log /
plan-doc / manifest is warned by a Stop-hook contributor.

Verification surface (plan §5): the contributor, given a claim
contradicting a git-log fact, emits the drift warning; a consistent
claim emits nothing.

The contributor checks a built/sealed/merged/published claim's named
SHA against the workspace git ref graph
(feedback_published_state_only_from_git_refs). PARTIAL enforcement:
bounded to the claim-names-a-sha shape.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam.primary_persona.stop_contributors_builtin import (
    terminology_drift_contributor,
)
from loam.primary_persona.stop_contributor import run_stop_contributors


def _init_repo(tmp_path: Path) -> tuple[Path, str]:
    """Init a git repo with one commit; return (root, real_sha)."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t.t"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "t"], cwd=tmp_path, check=True
    )
    (tmp_path / "f.txt").write_text("hi", encoding="utf-8")
    subprocess.run(["git", "add", "f.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return tmp_path, sha


# ----- a claim naming a non-existent SHA is flagged -----


def test_AC_PFSE_7_fake_sha_claim_flagged(tmp_path: Path) -> None:
    root, _real = _init_repo(tmp_path)
    advisory = terminology_drift_contributor(
        outbound_reply="Slice A sealed at deadbeef1234567.",
        context={"workspace_root": root},
    )
    assert advisory is not None
    assert advisory.name == "terminology-drift"
    assert "deadbeef1234567" in advisory.message


# ----- a claim naming the real SHA emits nothing -----


def test_AC_PFSE_7_real_sha_claim_clean(tmp_path: Path) -> None:
    root, real = _init_repo(tmp_path)
    advisory = terminology_drift_contributor(
        outbound_reply=f"The init work committed at {real[:12]}.",
        context={"workspace_root": root},
    )
    assert advisory is None


# ----- a reply with no SHA-claim emits nothing -----


def test_AC_PFSE_7_no_claim_clean(tmp_path: Path) -> None:
    root, _real = _init_repo(tmp_path)
    advisory = terminology_drift_contributor(
        outbound_reply="Did some work. It went well.",
        context={"workspace_root": root},
    )
    assert advisory is None


# ----- fail-open when git is unavailable (non-repo dir) -----


def test_AC_PFSE_7_non_repo_fails_open(tmp_path: Path) -> None:
    # tmp_path is not a git repo -> the verdict is None -> fail-open
    # (no false drift on a SHA we cannot check).
    advisory = terminology_drift_contributor(
        outbound_reply="Slice A sealed at deadbeef1234567.",
        context={"workspace_root": tmp_path},
    )
    assert advisory is None


# ----- through the framework compose path -----


def test_AC_PFSE_7_via_run_stop_contributors(tmp_path: Path) -> None:
    root, _real = _init_repo(tmp_path)
    out = run_stop_contributors(
        outbound_reply="Sealed at cafebabe9999999.",
        workspace_root=root,
    )
    assert out is not None
    assert "terminology-drift" in out["systemMessage"].lower()


# ----- missing workspace_root in context emits nothing -----


def test_AC_PFSE_7_no_workspace_root_clean() -> None:
    advisory = terminology_drift_contributor(
        outbound_reply="Sealed at deadbeef1234567.",
        context={},
    )
    assert advisory is None
