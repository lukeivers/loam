"""Workspace-state path resolution for loam-pr-safety.

Per Surface #5 (plan-doc §5) — every workspace gets its own
``<workspace>/.loam/pr-safety/`` directory with sub-paths:

  - ``audit-log/<YYYY-MM-DD>-<NNNN>.yaml`` — SOC-2 audit-trail
    floor entries (Decision P; AC.PRSG.7).
  - ``contract-overrides/<repo-id>/<override-N>.yaml`` — additive
    overlays for approved overrides (per Surface #4; AC.PRSG.5).

Repo-id derivation matches odd-extractor's exactly (Surface #6) —
re-uses :func:`loam_odd_extractor.state.compute_repo_id` so a repo
extracted by ``loam odd-extract`` and gated by ``loam pr-safety``
share the same id.
"""

from __future__ import annotations

from pathlib import Path

# Re-export the odd-extractor's compute_repo_id so callers don't
# have to know the upstream module path.
from loam_odd_extractor.state import compute_repo_id  # noqa: F401


def pr_safety_dir(workspace_root: Path) -> Path:
    """Return ``<workspace>/.loam/pr-safety/``."""
    return (
        workspace_root.expanduser().resolve() / ".loam" / "pr-safety"
    )


def audit_log_dir(workspace_root: Path) -> Path:
    """Return ``<workspace>/.loam/pr-safety/audit-log/``."""
    return pr_safety_dir(workspace_root) / "audit-log"


def overrides_dir(workspace_root: Path, repo_id: str) -> Path:
    """Return ``<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/``."""
    return pr_safety_dir(workspace_root) / "contract-overrides" / repo_id


def extractions_dir(workspace_root: Path, repo_id: str) -> Path:
    """Return ``<workspace>/.loam/extractions/<repo-id>/`` — the
    odd-extractor's per-repo state directory the gate reads from.

    Mirrors :func:`loam_odd_extractor.state.extraction_dir` but kept
    here as a convenience wrapper so pr-safety's call sites don't
    have to import two state modules.
    """
    return (
        workspace_root.expanduser().resolve()
        / ".loam"
        / "extractions"
        / repo_id
    )
