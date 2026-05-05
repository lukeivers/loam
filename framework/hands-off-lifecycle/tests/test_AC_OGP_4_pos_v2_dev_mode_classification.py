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

"""AC.OGP.4 — Pos-v2-shaped DEV-MODE workspace classifies as ``"dev-mode"``.

Per v0.2.2 sub-plan-doc §3 AC.OGP.4: this is a verification AC (no
edit). The plan-doc commits that a pos-v2-shaped workspace whose
primary-persona contract carries ``dev_intent: yes`` resolves to
``"dev-mode"`` via ``loam_mode.compute_session_mode`` /
``corpus_load_sentinel.workspace_mode``.

Implementation note (build-agent judgment call surfaced in §14
backfill): a literal ``workspace_mode("/Users/lukeivers/
ivers-corp-pos-v2")`` test would fail today because the canonical
pos-v2 persona contract carries ``dev_intent: unanswered`` (the
onboarding flow that sets ``yes`` has not been completed in the
canonical pos-v2 tree itself). The sub-plan-doc's own framing —
"the structural sanity check is verified by the existing fact that
ODD methodology auto-loads" — implies the AC is testing the
*mechanism* (pos-v2-shaped contracts with ``dev_intent: yes``
classify as ``dev-mode``), not literally the canonical pos-v2 root.
This file mirrors the AC.SE.1 / AC.CI.* fixture-based pattern and
verifies the mechanism with a pos-v2-shaped workspace fixture.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"


def _import_workspace_mode():
    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))
    from corpus_load_sentinel import workspace_mode  # noqa: E402

    return workspace_mode


def _make_pos_v2_shaped_workspace(
    tmp_path: Path,
    *,
    dev_intent: str = "yes",
    is_primary: bool = True,
) -> Path:
    """Build a minimal pos-v2-shaped DEV-MODE workspace.

    Mirrors the AC.CI.* fixture pattern: persona contract at
    ``<workspace>/workspace/personas/<handle>/contract.yaml`` with
    ``is_primary: true`` and the parameterised ``dev_intent``.
    """
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    is_primary_str = "true" if is_primary else "false"
    (persona_dir / "contract.yaml").write_text(
        f"is_primary: {is_primary_str}\ndev_intent: {dev_intent}\n",
        encoding="utf-8",
    )
    return tmp_path


def test_AC_OGP_4_pos_v2_shaped_workspace_resolves_to_dev_mode(
    tmp_path: Path,
) -> None:
    """A pos-v2-shaped workspace with ``dev_intent: yes`` →
    ``workspace_mode`` returns ``"dev-mode"``."""
    workspace_mode = _import_workspace_mode()
    workspace = _make_pos_v2_shaped_workspace(tmp_path, dev_intent="yes")
    assert workspace_mode(workspace) == "dev-mode", (
        "AC.OGP.4: a pos-v2-shaped workspace with persona contract "
        "carrying dev_intent: yes must classify as dev-mode."
    )


def test_AC_OGP_4_unanswered_dev_intent_resolves_to_normal_use(
    tmp_path: Path,
) -> None:
    """A pos-v2-shaped workspace with ``dev_intent: unanswered`` →
    ``workspace_mode`` returns ``"normal-use"`` (fail-closed-to-
    permissive per AC.SE.1)."""
    workspace_mode = _import_workspace_mode()
    workspace = _make_pos_v2_shaped_workspace(
        tmp_path, dev_intent="unanswered"
    )
    assert workspace_mode(workspace) == "normal-use", (
        "AC.OGP.4: pos-v2-shaped workspace with unanswered dev_intent "
        "classifies normal-use (fail-closed-to-permissive)."
    )


def test_AC_OGP_4_dev_intent_no_resolves_to_normal_use(
    tmp_path: Path,
) -> None:
    """``dev_intent: no`` → ``"normal-use"`` (explicit user mode)."""
    workspace_mode = _import_workspace_mode()
    workspace = _make_pos_v2_shaped_workspace(tmp_path, dev_intent="no")
    assert workspace_mode(workspace) == "normal-use"
