"""Installer surfaces for loam-pr-safety (v0.1.9 Cycle 2).

Per plan-doc §3 + §4 — pre-commit + pre-push hook installers, three
CI templates (GitHub Actions / GitLab CI / CircleCI), and the
provenance-traceable PR description template.

Public API:

  - :class:`InstallResult` — typed return from each installer.
  - :class:`InstallConflictError` — raised when target file has
    non-loam content and ``force=False``.
  - :func:`install_pre_commit` — AC.PRSI.1
  - :func:`install_pre_push` — AC.PRSI.2
  - :func:`install_ci_github_actions` — AC.PRSI.4
  - :func:`install_ci_gitlab_ci` — AC.PRSI.5
  - :func:`install_ci_circleci` — AC.PRSI.6
  - :func:`install_pr_template` — AC.PRSI.7
  - :func:`install_all` — AC.PRSI.8 (--all aggregator)
  - :func:`render_pr_description` — AC.PRSI.7 (gate-mode rendering)
  - :func:`fire_hook` — AC.PRSI.{1,2,3} (called by hook scripts)
  - :func:`detect_husky` — Surface #4

The CLI surface lives in :mod:`loam_pr_safety.cli`.
"""

from __future__ import annotations

from loam_pr_safety.installers.conflicts import (
    InstallConflictError,
    InstallResult,
    LOAM_PR_SAFETY_VERSION,
    detect_loam_managed,
    detect_loam_managed_block,
)
from loam_pr_safety.installers.hooks import (
    fire_hook,
    install_pre_commit,
    install_pre_push,
    detect_husky,
)
from loam_pr_safety.installers.ci import (
    install_ci_circleci,
    install_ci_github_actions,
    install_ci_gitlab_ci,
)
from loam_pr_safety.installers.pr_template import (
    install_pr_template,
    render_pr_description,
)


def install_all(
    repo_path,
    *,
    workspace_root=None,
    force: bool = False,
    dry_run: bool = False,
) -> list[InstallResult]:
    """Install every Cycle 2 surface against ``repo_path``.

    Per AC.PRSI.8 — aggregates :class:`InstallResult` across all six
    surfaces; continues past surface-specific conflicts (audit-logged
    via each installer); caller's exit code reflects worst-case.

    Conflicts are surfaced via the returned ``InstallResult.action ==
    "conflict-halted"`` entries; the caller (CLI) translates these to
    exit code 6 + audit-log entries.
    """
    from pathlib import Path

    repo_path = Path(repo_path).expanduser().resolve()
    workspace_root = (
        Path(workspace_root).expanduser().resolve()
        if workspace_root is not None
        else Path.cwd().resolve()
    )

    results: list[InstallResult] = []
    install_funcs = [
        install_pre_commit,
        install_pre_push,
        install_ci_github_actions,
        install_ci_gitlab_ci,
        install_ci_circleci,
        install_pr_template,
    ]
    for fn in install_funcs:
        try:
            results.append(
                fn(
                    repo_path,
                    workspace_root=workspace_root,
                    force=force,
                    dry_run=dry_run,
                )
            )
        except InstallConflictError as exc:
            results.append(exc.to_result())
    return results


__all__ = [
    "InstallConflictError",
    "InstallResult",
    "LOAM_PR_SAFETY_VERSION",
    "detect_husky",
    "detect_loam_managed",
    "detect_loam_managed_block",
    "fire_hook",
    "install_all",
    "install_ci_circleci",
    "install_ci_github_actions",
    "install_ci_gitlab_ci",
    "install_pr_template",
    "install_pre_commit",
    "install_pre_push",
    "render_pr_description",
]
