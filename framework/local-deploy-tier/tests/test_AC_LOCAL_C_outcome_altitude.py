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

"""OUTCOME-ALTITUDE (AC.LOCAL.C) — the real LOCAL build entry-point.

Invokes ``build_local`` against a real on-disk workspace with NO pre-arranged
state beyond the files written to a temp dir and NO internal function stubbed.
The independent check is a REAL subprocess (``python -c ...``) whose exit code —
not any in-test boolean — decides the Acceptance verdict. The assertions read
the produced result the way the owner would experience it.

``outcome-altitude: true``."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

from loam.local_deploy_tier.build import LocalBuildError, build_local


def _write_workspace(root: Path, *, verify_exit: int, local_kind: str) -> None:
    """A minimal but REAL deployable workspace on disk: a deploy config with a
    LOCAL env + a downstream env, and a LOCAL-tier file naming a real check
    command. No in-memory fixtures — everything is files."""
    (root / ".loam").mkdir(parents=True, exist_ok=True)
    (root / ".loam" / "environments.yaml").write_text(
        textwrap.dedent(
            f"""\
            environments:
              - name: dev
                id: 01JLOCALDEV0000000000000000
                is_production: false
                tier: local
                reversible: true
                gate: none
                security_profile: dev
                role: development
                backing_services:
                  - name: db
                    kind: {local_kind}
                    version: "16.3"
              - name: prod
                id: 01JLOCALPROD000000000000000
                is_production: true
                tier: staging
                reversible: true
                gate: high
                security_profile: prod
                role: production
                backing_services:
                  - name: db
                    kind: postgres
                    version: "16.3"
            active: dev
            """
        ),
        encoding="utf-8",
    )
    # A REAL check command run as a subprocess; its exit code is the verdict.
    py = sys.executable
    (root / ".loam" / "local-tier.yaml").write_text(
        f'verify_command: "{py} -c \\"import sys; sys.exit({verify_exit})\\""\n',
        encoding="utf-8",
    )


def test_real_build_local_green_check_matching_parity(tmp_path: Path) -> None:
    """A real build whose independent subprocess check PASSES, with the LOCAL
    backing service matching the downstream one: the Acceptance is met, the
    command set is proven floor-idle, no parity gap, plain-language status."""
    repo = tmp_path / "ws-green"
    _write_workspace(repo, verify_exit=0, local_kind="postgres")

    result = build_local(repo)

    # P0-shape Acceptance, verdict from the REAL subprocess (exit 0).
    assert result.acceptance.met is True
    assert result.acceptance.altitude is True
    assert result.acceptance.ladder == ("AC.PO.1", "AC.PO.2")

    # AC.LOCAL.2 — floor idles: no irreversible verb reachable.
    assert result.floor_idle is True
    assert result.irreversible_overlap == ()

    # AC.LOCAL.3 — matching service => no gap, but the honest caveat stands.
    assert result.parity is not None
    assert result.parity.has_gaps is False

    # D-SC.6 — LOCAL never crosses the deploy boundary.
    assert result.promotion_offered is False

    # Lens 0 — a plain-language status the owner can read.
    status = result.plain_language_status().lower()
    assert "this machine" in status or "on this machine" in status
    assert "public" in status


def test_real_build_local_failing_check_is_honest_negative(tmp_path: Path) -> None:
    """A real build whose subprocess check FAILS (exit 1) is reported as an
    honest 'not done yet' — never fabricated to a pass."""
    repo = tmp_path / "ws-red"
    _write_workspace(repo, verify_exit=1, local_kind="postgres")

    result = build_local(repo)
    assert result.acceptance.met is False
    assert result.acceptance.is_honest_negative is True


def test_real_build_local_surfaces_engine_parity_gap(tmp_path: Path) -> None:
    """A real build where LOCAL uses sqlite but downstream uses postgres
    surfaces the engine divergence in plain language before any promotion."""
    repo = tmp_path / "ws-paritygap"
    _write_workspace(repo, verify_exit=0, local_kind="sqlite")

    result = build_local(repo)
    assert result.parity is not None
    assert result.parity.has_gaps is True
    summary = result.plain_language_status().lower()
    assert "sqlite" in summary and "postgres" in summary
    assert result.promotion_offered is False


def test_real_build_local_without_config_is_inert(tmp_path: Path) -> None:
    """No deploy config on disk => the tier is inert, surfaced as an explicit
    error rather than a silent fake build."""
    repo = tmp_path / "ws-empty"
    repo.mkdir()
    with pytest.raises(LocalBuildError):
        build_local(repo)
