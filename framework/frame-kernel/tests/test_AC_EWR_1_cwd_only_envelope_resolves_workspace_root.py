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

"""AC.EWR.1 — an envelope carrying ONLY ``cwd`` (no ``workspace`` dict —
the REAL observed Claude Code SubagentStart shape, Tier-0 2026-06-10)
resolves ``workspace_root``, and the composed bundle is identical to the
bundle composed from a ``workspace.project_dir`` envelope naming the same
root. Priority order: ``workspace.project_dir`` when present wins.

The fail-soft contract (AC.SACH.4) is untouched: an envelope carrying
NEITHER field still yields ``workspace_root=None`` and the degraded
markers exactly as before — asserted here as the unchanged-contract
guard, not a new contract.
"""

from __future__ import annotations

from pathlib import Path

from loam.frame_kernel.bundle import (
    MICROKERNEL_PRIME_MARKER,
    MISSING_KERNEL_MARKER,
    compose_bundle,
    parse_envelope,
)


def test_AC_EWR_1_cwd_only_envelope_resolves_workspace_root(
    real_kernel_workspace: Path,
) -> None:
    """The real observed envelope shape — ``cwd`` only, no ``workspace``
    dict — resolves workspace_root from ``cwd``."""
    envelope = {
        "hook_event_name": "SubagentStart",
        "cwd": str(real_kernel_workspace),
        "prompt": "scoped sub-task",
    }
    ctx = parse_envelope(envelope)
    assert ctx.workspace_root == real_kernel_workspace
    assert ctx.task_text == "scoped sub-task"


def test_AC_EWR_1_bundle_from_cwd_envelope_equals_project_dir_bundle(
    real_kernel_workspace: Path,
) -> None:
    """The composed bundle from a cwd-only envelope is byte-identical to
    the bundle from a workspace.project_dir envelope naming the same
    root — all three tiers resolve identically (the microkernel tier is
    populated, not the missing-marker)."""
    cwd_envelope = {
        "hook_event_name": "SubagentStart",
        "cwd": str(real_kernel_workspace),
        "prompt": "scoped sub-task",
    }
    project_dir_envelope = {
        "hook_event_name": "SubagentStart",
        "workspace": {"project_dir": str(real_kernel_workspace)},
        "prompt": "scoped sub-task",
    }
    cwd_bundle = compose_bundle(cwd_envelope)
    project_dir_bundle = compose_bundle(project_dir_envelope)
    assert cwd_bundle == project_dir_bundle
    # The microkernel tier actually populated from the cwd-resolved root.
    assert MICROKERNEL_PRIME_MARKER in cwd_bundle
    assert MISSING_KERNEL_MARKER not in cwd_bundle


def test_AC_EWR_1_project_dir_wins_over_cwd(tmp_path: Path) -> None:
    """Priority order: ``workspace.project_dir`` when present wins over
    ``cwd``."""
    project_dir = tmp_path / "project"
    other_cwd = tmp_path / "elsewhere"
    project_dir.mkdir()
    other_cwd.mkdir()
    envelope = {
        "workspace": {"project_dir": str(project_dir)},
        "cwd": str(other_cwd),
    }
    ctx = parse_envelope(envelope)
    assert ctx.workspace_root == project_dir


def test_AC_EWR_1_neither_field_still_degrades_failsoft() -> None:
    """Unchanged AC.SACH.4 contract: neither ``workspace.project_dir``
    nor ``cwd`` present → workspace_root stays None and the bundle
    degrades to the structured markers (never raises)."""
    ctx = parse_envelope({"hook_event_name": "SubagentStart"})
    assert ctx.workspace_root is None
    bundle = compose_bundle({"hook_event_name": "SubagentStart"})
    assert MISSING_KERNEL_MARKER in bundle


def test_AC_EWR_1_blank_or_nonstring_cwd_is_ignored() -> None:
    """A blank / non-string ``cwd`` does not resolve a root (the same
    type-guard discipline the project_dir read applies — AC.SACH.4)."""
    assert parse_envelope({"cwd": "   "}).workspace_root is None
    assert parse_envelope({"cwd": 42}).workspace_root is None
