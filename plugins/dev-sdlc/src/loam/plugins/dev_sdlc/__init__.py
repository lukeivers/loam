"""Dev/SDLC plugin — first plugin under loam's contribution-based
extension protocol.

Public surfaces (per plan §4 ACs):

- `loam.plugins.dev_sdlc.api` — persona-invocable Python API
  (AC.OSS-M6.7).
- `loam.plugins.dev_sdlc.cli` — `loam project ...` subcommand
  builder (AC.OSS-M6.6).
- `loam.plugins.dev_sdlc.contribution` — workspace-bootstrap
  contribution class (AC.OSS-M6.1).

The plugin establishes the `plugins/<name>/` tree pattern at v0.1.0
(per plan §10 D-Q.M6.1). v0.2+ plugins inherit cheaper landing.
"""

from __future__ import annotations

from .api import (
    GateResult,
    ProjectHandle,
    ProjectStatus,
    StageAdvanceResult,
    advance_stage,
    gate_check,
    list_projects,
    project_status,
    start_project,
)

__all__ = [
    "GateResult",
    "ProjectHandle",
    "ProjectStatus",
    "StageAdvanceResult",
    "advance_stage",
    "gate_check",
    "list_projects",
    "project_status",
    "start_project",
]
