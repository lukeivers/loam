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

"""AC.MFBM-OPS.5 — Generated plist Label is workspace-slug-namespaced.

Plan ref: ``docs/rebuild/plans/m-fbm-operational-health.md`` §4
AC.MFBM-OPS.5.

Diagnosis trigger (2026-05-04): the dispatch's diagnosis hypothesised
a generic ``com.loam.ws.memory-write-worker`` Label was hijackable
across workspaces. Empirical finding (Surface #2 of the plan):
namespacing was already in place via ``service_label`` (amendment #6).
The companion contract-level test
``framework/primary-persona/tests/test_AC_MFBM_OPS_2_worker_liveness_label_contract.py``
pins ``service_label``'s function-level contract; this test pins the
**scaffold-output level** — the actual plist file written to disk by
``run_first_run_scaffold`` carries the namespaced Label string.

Two distinct regression surfaces:

  - AC.MFBM-OPS.2 (contract): a future change to ``service_label``
    that returns a generic Label.
  - AC.MFBM-OPS.5 (scaffold-output): a future change that bypasses
    ``service_label`` and hardcodes a generic Label in the plist
    template.

Both are needed.

The existing ``test_AC_J_5_distinct_workspaces_get_distinct_worker_labels``
covers Label-distinctness implicitly via ``service_label`` indirection.
This test pins the literal namespaced Label string + the negative
"generic Label MUST NOT appear" assertion explicitly.

Per ODD §2.5 every assertion below maps to AC.MFBM-OPS.5.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    run_first_run_scaffold,
    service_label,
)


def test_AC_MFBM_OPS_5_pos3_workspace_yields_pos3_namespaced_plist_label(
    tmp_path: Path,
) -> None:
    """First-run-scaffold against a workspace named ``pos3`` produces
    a plist whose Label is exactly ``com.loam.pos3.memory-write-worker``."""
    workspace = tmp_path / "pos3"
    workspace.mkdir()
    pos_root = tmp_path / "pos"
    agents = tmp_path / "LaunchAgents"

    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )

    expected_label = "com.loam.pos3.memory-write-worker"
    assert expected_label == service_label("memory-write-worker", "pos3")
    plist_path = agents / f"{expected_label}.plist"
    assert plist_path.exists(), f"namespaced plist missing: {plist_path}"

    text = plist_path.read_text(encoding="utf-8")
    assert (
        f"<key>Label</key><string>{expected_label}</string>" in text
    ), f"Label string not in plist: {text!r}"

    # Negative regression-pin: the generic legacy shape MUST NOT
    # appear anywhere in the plist content. (Verifies a hardcoded-
    # Label-template regression couldn't slip through unnoticed.)
    assert "com.loam.ws.memory-write-worker" not in text, (
        "generic com.loam.ws.memory-write-worker Label found in "
        "namespaced plist content"
    )


def test_AC_MFBM_OPS_5_alpha_ws_workspace_yields_alpha_ws_namespaced_plist_label(
    tmp_path: Path,
) -> None:
    """A second workspace name yields a different namespaced Label —
    confirming the namespacing tracks the workspace, not a constant."""
    workspace = tmp_path / "alpha-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos"
    agents = tmp_path / "LaunchAgents"

    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )

    expected_label = "com.loam.alpha-ws.memory-write-worker"
    plist_path = agents / f"{expected_label}.plist"
    assert plist_path.exists()

    text = plist_path.read_text(encoding="utf-8")
    assert f"<key>Label</key><string>{expected_label}</string>" in text
    assert "com.loam.ws.memory-write-worker" not in text


def test_AC_MFBM_OPS_5_no_generic_ws_plist_filename_is_written(
    tmp_path: Path,
) -> None:
    """No file named ``com.loam.ws.memory-write-worker.plist`` is
    ever produced by the scaffold — regardless of workspace name.
    This is the literal regression the diagnosis worried about."""
    workspace = tmp_path / "test-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos"
    agents = tmp_path / "LaunchAgents"

    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )

    forbidden = agents / "com.loam.ws.memory-write-worker.plist"
    assert not forbidden.exists(), (
        f"generic plist should not exist: {forbidden}"
    )

    # And confirm the namespaced one DOES exist (otherwise we proved
    # nothing — a scaffold that wrote zero plists would also satisfy
    # the negative).
    expected = agents / "com.loam.test-ws.memory-write-worker.plist"
    assert expected.exists(), f"namespaced plist missing: {expected}"
