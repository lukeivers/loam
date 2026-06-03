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

"""AC-CAIRN-MARKER-2 (C2) — Cairn's build classifier keys on Cairn's
REAL markers (module presence + introducing-commit ancestry) with NO
loam seal-sidecar dependency.

A fixture repo is built with present modules introduced by real merged
commits and NO ``SEAL_COMMIT`` file anywhere. The classifier must derive
MERGED for a present-and-merged module and UNBUILT for an absent one —
proving the engine generalizes to a separate repo's markers, not a
second loam-shaped hardcode keyed to seal sidecars.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.audit.cairn_state import (
    ModuleProbeSpec,
    cairn_state_record,
    classify_module_build_status,
)
from loam_cli.audit.probe import Liveness


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def cairn_like_repo(tmp_path: Path) -> Path:
    """A throwaway repo shaped like Cairn: ``src/pkg/<module>/`` dirs
    with impl files, introduced by real merged commits, on ``main``.

    Crucially: NO ``SEAL_COMMIT`` sidecar exists anywhere — the
    classifier must work off presence + introducing-commit ancestry
    alone.
    """
    repo = tmp_path / "cairn-like"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "cairn-test@example.invalid")
    _git(repo, "config", "user.name", "cairn test")
    _git(repo, "config", "commit.gpgsign", "false")

    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "seed")

    # A built module: present with an impl file, introduced on main.
    built = repo / "src" / "pkg" / "built_mod"
    built.mkdir(parents=True)
    (built / "__init__.py").write_text("", encoding="utf-8")
    (built / "core.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    _git(repo, "add", "src/pkg/built_mod")
    _git(repo, "commit", "-q", "-m", "feat: built_mod")

    return repo


def test_present_and_merged_module_classifies_merged_with_no_seal_sidecar(
    cairn_like_repo: Path,
) -> None:
    # No seal sidecar exists in the fixture — assert that explicitly.
    assert not list(cairn_like_repo.rglob("SEAL_COMMIT"))

    liveness, evidence = classify_module_build_status(
        cairn_like_repo, "src/pkg/built_mod"
    )
    assert liveness is Liveness.MERGED, evidence
    # Evidence cites the REAL markers (presence + introducing commit),
    # never a seal sidecar.
    assert "impl files" in evidence
    assert "ancestor of HEAD" in evidence
    assert "SEAL_COMMIT" not in evidence


def test_absent_module_classifies_unbuilt(cairn_like_repo: Path) -> None:
    liveness, evidence = classify_module_build_status(
        cairn_like_repo, "src/pkg/does_not_exist"
    )
    assert liveness is Liveness.UNBUILT, evidence


def test_stub_only_init_module_classifies_unbuilt(cairn_like_repo: Path) -> None:
    # A dir with only __init__.py is a stub, not a built module.
    stub = cairn_like_repo / "src" / "pkg" / "stub_mod"
    stub.mkdir(parents=True)
    (stub / "__init__.py").write_text("", encoding="utf-8")
    _git(cairn_like_repo, "add", "src/pkg/stub_mod")
    _git(cairn_like_repo, "commit", "-q", "-m", "stub")

    liveness, _ = classify_module_build_status(cairn_like_repo, "src/pkg/stub_mod")
    assert liveness is Liveness.UNBUILT


def test_record_assembles_rows_for_each_spec(cairn_like_repo: Path) -> None:
    record = cairn_state_record(
        cairn_like_repo,
        module_specs=(
            ModuleProbeSpec(name="built", module_relpath="src/pkg/built_mod"),
            ModuleProbeSpec(name="missing", module_relpath="src/pkg/missing_mod"),
        ),
    )
    assert record.by_name("built").liveness is Liveness.MERGED
    assert record.by_name("missing").liveness is Liveness.UNBUILT
    # The record reuses the engine's StateOfLoam type (no Cairn-specific
    # record type — the generalization reuses the engine).
    assert record.head_sha != "UNKNOWN"
