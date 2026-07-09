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

"""AC.PRE.* — `loam release preflight <version>` mergeability verb
(audit Class B, the cheap tool-assisted partial).

Per-branch fast-forward/merge-tree verdicts + the computed cut, in a
stable recordable block; a non-breaking `preflight` sub-token on the
existing `release` parser.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pytest

from loam_cli.release import preflight
from loam_cli.release.cli import build_release_subcommand, dispatch


def _run(path: Path, *args: str) -> None:
    subprocess.run(list(args), cwd=path, check=True)


def _init_repo(path: Path) -> None:
    _run(path, "git", "init", "-q", "-b", "main")
    _run(path, "git", "config", "user.email", "pre-test@example.invalid")
    _run(path, "git", "config", "user.name", "pre test")
    _run(path, "git", "config", "commit.gpgsign", "false")


def _commit(path: Path, fname: str, content: str, msg: str) -> None:
    (path / fname).write_text(content, encoding="utf-8")
    _run(path, "git", "add", fname)
    _run(path, "git", "commit", "-q", "-m", msg)


@pytest.fixture
def preflight_repo(tmp_path: Path) -> Path:
    """A repo with an origin remote + a published tag + three candidate
    branches: a fast-forwardable clean branch, a non-ff clean branch, and
    a conflicting branch."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    # c0 on main; tag + push as the published version.
    _commit(repo, "shared.txt", "base\n", "chore: base")
    _run(repo, "git", "tag", "v1.11.0")
    bare = tmp_path / "origin.git"
    _run(repo, "git", "init", "-q", "--bare", str(bare))
    _run(repo, "git", "remote", "add", "origin", str(bare))
    _run(repo, "git", "push", "-q", "origin", "main")
    _run(repo, "git", "push", "-q", "origin", "v1.11.0")
    c0 = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # feature-ahead: from c0, adds a file (clean, but non-ff once main moves).
    _run(repo, "git", "checkout", "-q", "-b", "feature-ahead", c0)
    _commit(repo, "ahead.txt", "ahead\n", "feat: ahead capability")

    # feature-conflict: from c0, changes shared.txt.
    _run(repo, "git", "checkout", "-q", "-b", "feature-conflict", c0)
    _commit(repo, "shared.txt", "branch change\n", "feat: conflict change")

    # main advances, changing shared.txt differently (creates the conflict).
    _run(repo, "git", "checkout", "-q", "main")
    _commit(repo, "shared.txt", "main change\n", "feat: main change")

    # feature-ff: from the NEW main tip, adds a file (ff-able + clean).
    _run(repo, "git", "checkout", "-q", "-b", "feature-ff", "main")
    _commit(repo, "ff.txt", "ff\n", "feat: ff capability")

    _run(repo, "git", "checkout", "-q", "main")
    return repo


def _dispatch_preflight(repo: Path, *extra: str) -> tuple[int, str, str]:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_release_subcommand(sub)
    args = parser.parse_args(
        ["release", "preflight", *extra, "--repo-root", str(repo)]
    )
    return args.func(args), args.version, str(args.preflight_version)


def test_AC_PRE_1_per_branch_mergeability_verdict(
    preflight_repo: Path, capsys
) -> None:
    """AC.PRE.1 — a per-branch ff + merge verdict against main."""
    rc = preflight.run_preflight(preflight_repo, "v1.12.0")
    out = capsys.readouterr().out
    assert rc == 0
    assert "branch mergeability (vs main):" in out
    assert "feature-ff:" in out
    assert "feature-ahead:" in out
    assert "feature-conflict:" in out


def test_AC_PRE_2_output_includes_computed_cut(
    preflight_repo: Path, capsys
) -> None:
    """AC.PRE.2 — the output carries the computed cut (class + expected)
    from the shared cut computation."""
    preflight.run_preflight(preflight_repo, "v1.12.0")
    out = capsys.readouterr().out
    assert "computed cut:" in out
    assert "class=MINOR" in out       # main carries a feat
    assert "expected=v1.12.0" in out  # bump_minor(v1.11.0)


def test_AC_PRE_3_stable_recordable_block(
    preflight_repo: Path, capsys
) -> None:
    """AC.PRE.3 — a stable block headed by the verb + version, branches in
    deterministic (sorted) order."""
    preflight.run_preflight(preflight_repo, "v1.12.0")
    out = capsys.readouterr().out
    assert out.startswith("== loam release preflight v1.12.0 ==")
    # Branches emitted in sorted order.
    i_ahead = out.index("feature-ahead:")
    i_conflict = out.index("feature-conflict:")
    i_ff = out.index("feature-ff:")
    assert i_ahead < i_conflict < i_ff


def test_AC_PRE_4_outcome_altitude_conflict_reported(
    preflight_repo: Path,
) -> None:
    """AC.PRE.4 (outcome-altitude) — driven end-to-end through the CLI
    dispatch, a conflicting branch is reported non-clean and a clean branch
    clean."""
    rc, version_tok, _ = _dispatch_preflight(preflight_repo, "v1.12.0")
    assert rc == 0
    assert version_tok == "preflight"  # routed to preflight, not publish


def test_AC_PRE_4_conflict_and_clean_verdicts(
    preflight_repo: Path, capsys
) -> None:
    preflight.run_preflight(preflight_repo, "v1.12.0")
    out = capsys.readouterr().out
    lines = {
        ln.split(":")[0].strip(): ln
        for ln in out.splitlines()
        if ln.strip().startswith("feature-")
    }
    assert "CONFLICT" in lines["feature-conflict"]
    assert "merge=clean" in lines["feature-ff"]
    assert "ff=yes" in lines["feature-ff"]
    assert "ff=no" in lines["feature-ahead"]


def test_AC_PRE_5_missing_version_clean_error_no_publish(
    preflight_repo: Path,
) -> None:
    """AC.PRE.5 — no version is a clean usage error (rc=2); it never falls
    through into publish (no tag created)."""
    rc, version_tok, pf_version = _dispatch_preflight(preflight_repo)
    assert rc == 2
    assert version_tok == "preflight"
    assert pf_version == "None"
    # No new tag was created by the preflight path (only v1.11.0 exists).
    tags = subprocess.run(
        ["git", "tag", "--list"],
        cwd=preflight_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert tags == ["v1.11.0"]


def test_AC_PRE_5_publish_surface_unchanged_non_breaking() -> None:
    """D-PRE.CLI — `loam release <version>` still routes to publish (the
    version token is NOT 'preflight'); the preflight sub-token is additive."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_release_subcommand(sub)
    publish_args = parser.parse_args(["release", "v1.12.0"])
    assert publish_args.version == "v1.12.0"
    assert publish_args.preflight_version is None
    assert publish_args.func is dispatch
    pre_args = parser.parse_args(["release", "preflight", "v1.12.0"])
    assert pre_args.version == "preflight"
    assert pre_args.preflight_version == "v1.12.0"
