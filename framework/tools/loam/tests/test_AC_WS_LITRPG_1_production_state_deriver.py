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

"""AC.WS.LITRPG.1 — LitRPG is registered as an FBM project with a
workspace-derived production-state deriver (mirrors the cairn_state
pattern, keyed to LitRPG's OWN markers: production-pipeline layer
presence + introducing-commit ancestry). A present-and-merged layer
classifies MERGED; an absent layer UNBUILT; the record reuses the engine
types (no litrpg-specific record type). litrpg resolves through the
registry (AC.WS.LIVE.1's litrpg binding)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.audit.litrpg_state import (
    LayerProbeSpec,
    classify_layer_production_status,
    litrpg_state_record,
)
from loam_cli.audit.probe import Liveness
from loam_cli.audit.registry import (
    derive_project_state,
    registered_project_names,
    resolve_project,
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def litrpg_like_repo(tmp_path: Path) -> Path:
    """A throwaway repo shaped like the LitRPG production workspace:
    ``layer-N/`` dirs carrying content ``.md`` files, introduced by real
    merged commits, on ``main``. Keyed to LitRPG's OWN markers (layer
    presence + introducing commit), no seal sidecar anywhere."""
    repo = tmp_path / "litrpg-like"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "litrpg-test@example.invalid")
    _git(repo, "config", "user.name", "litrpg test")
    _git(repo, "config", "commit.gpgsign", "false")

    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "seed")

    # A produced layer: present with a content .md, introduced on main.
    produced = repo / "layer-4" / "book-1"
    produced.mkdir(parents=True)
    (produced / "chapter-01.md").write_text("# Ch1\n", encoding="utf-8")
    _git(repo, "add", "layer-4")
    _git(repo, "commit", "-q", "-m", "feat: layer-4 chapter drafts")

    return repo


def test_AC_WS_LITRPG_1_produced_layer_classifies_merged(
    litrpg_like_repo: Path,
) -> None:
    assert not list(litrpg_like_repo.rglob("SEAL_COMMIT"))  # no seal sidecar
    liveness, evidence = classify_layer_production_status(
        litrpg_like_repo, "layer-4"
    )
    assert liveness is Liveness.MERGED, evidence
    assert "content files" in evidence
    assert "ancestor of HEAD" in evidence
    assert "SEAL_COMMIT" not in evidence


def test_AC_WS_LITRPG_1_absent_layer_classifies_unbuilt(
    litrpg_like_repo: Path,
) -> None:
    liveness, _ = classify_layer_production_status(litrpg_like_repo, "layer-7")
    assert liveness is Liveness.UNBUILT


def test_AC_WS_LITRPG_1_record_reuses_engine_types(
    litrpg_like_repo: Path,
) -> None:
    record = litrpg_state_record(
        litrpg_like_repo,
        layer_specs=(
            LayerProbeSpec(name="chapter-drafts", layer_relpath="layer-4"),
            LayerProbeSpec(name="final-pass", layer_relpath="layer-7"),
        ),
    )
    assert record.by_name("chapter-drafts").liveness is Liveness.MERGED
    assert record.by_name("final-pass").liveness is Liveness.UNBUILT
    assert record.head_sha != "UNKNOWN"


def test_AC_WS_LITRPG_1_registered_in_project_registry() -> None:
    # litrpg resolves through the registry (the AC.WS.LIVE.1 binding).
    assert "litrpg" in registered_project_names()
    spec = resolve_project("litrpg")
    assert spec is not None and spec.name == "litrpg"


def test_AC_WS_LITRPG_1_derive_through_registry_uses_fixture_root(
    litrpg_like_repo: Path,
) -> None:
    # The production derive entry point routes a fixture root to the
    # litrpg deriver (repo_root override) — proving the registration is
    # wired, not just the module.
    rec = derive_project_state("litrpg", repo_root=litrpg_like_repo)
    assert rec is not None
    # Default specs include layer-4 (present in the fixture) => a merged row.
    drafts = rec.by_name("chapter-drafts")
    assert drafts is not None and drafts.liveness is Liveness.MERGED
