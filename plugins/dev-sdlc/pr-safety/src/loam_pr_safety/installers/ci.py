"""CI template installers for loam-pr-safety.

Per AC.PRSI.{4,5,6} (v0.1.9 Cycle 2). Plan-doc §3 + §4 + §5 Surface
#3 (sentinel-block delimiter for files where loam content co-exists
with non-loam content).

Three CI providers shipped (production-polish per Eric synthesis §2
v0.1.9 "ship for the three most common"):

  - GitHub Actions (.github/workflows/loam-pr-safety.yml — separate
    file; no co-existence concerns)
  - GitLab CI (.gitlab-ci.yml — sentinel-block-delimited region; may
    co-exist with non-loam jobs)
  - CircleCI (.circleci/config.yml — sentinel-block-delimited region;
    may co-exist)

GitHub Actions uses a dedicated file so install is a clean overwrite.
GitLab CI + CircleCI use sentinel-block-delimited insertion to
preserve non-loam content; the block is rewritten in-place on
refresh.
"""

from __future__ import annotations

import yaml
from importlib import resources
from pathlib import Path
from typing import Literal

from loam_pr_safety.installers.conflicts import (
    InstallConflictError,
    InstallResult,
    LOAM_PR_SAFETY_VERSION,
    detect_loam_managed,
    detect_loam_managed_block,
    is_effectively_empty,
)


def _read_template(template_rel_path: str) -> str:
    """Path-based template resolution. See hooks._read_template."""
    base = (
        Path(resources.files("loam_pr_safety.templates").joinpath("."))
    )
    return (base / template_rel_path).read_text(encoding="utf-8")


def _render_template(content: str, *, version: str) -> str:
    return content.replace("{LOAM_PR_SAFETY_VERSION}", version)


def _audit_install(
    workspace_root: Path,
    result: InstallResult,
    repo_path: Path,
) -> None:
    """Write an install-action audit-log entry."""
    from loam_pr_safety.audit import write_audit_entry
    from loam_pr_safety.profile import read_safety_profile
    from loam_pr_safety.state import compute_repo_id

    event_map = {
        "ci/github-actions": "install_ci_github_actions",
        "ci/gitlab-ci": "install_ci_gitlab_ci",
        "ci/circleci": "install_ci_circleci",
    }
    base = event_map.get(result.surface, "install_unknown")
    event_kind = "install_conflict" if result.is_conflict else base
    write_audit_entry(
        workspace_root,
        event_kind=event_kind,
        repo_id=compute_repo_id(repo_path),
        repo_sha="",
        diff_range="",
        safety_profile=read_safety_profile(workspace_root),
        decision=result.action,
        requires_ratification=False,
        touched_acs=[],
        novel_count=0,
        reason=result.detail,
        owner=None,
        rationale=None,
        target_path=str(result.target_path),
    )


def install_ci_github_actions(
    repo_path: Path,
    *,
    workspace_root: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    """Install the GitHub Actions workflow (AC.PRSI.4).

    Target: ``<repo>/.github/workflows/loam-pr-safety.yml``.
    Dedicated file — no co-existence with non-loam content; a
    pre-existing non-loam file at the path is a conflict.
    """
    repo_path = repo_path.expanduser().resolve()
    workspace_root = (
        workspace_root.expanduser().resolve()
        if workspace_root is not None
        else Path.cwd().resolve()
    )
    target = repo_path / ".github" / "workflows" / "loam-pr-safety.yml"
    rendered = _render_template(
        _read_template("ci/github-actions/loam-pr-safety.yml.template"),
        version=LOAM_PR_SAFETY_VERSION,
    )

    existing_content = ""
    if target.exists():
        try:
            existing_content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            existing_content = "<binary content>"

    prior_version = detect_loam_managed(existing_content)

    if not target.exists() or not existing_content.strip():
        action = "created"
    elif prior_version is not None:
        if (
            prior_version == LOAM_PR_SAFETY_VERSION
            and existing_content == rendered
        ):
            action = "noop"
        else:
            action = "refreshed"
    elif is_effectively_empty(existing_content):
        action = "created"
    elif force:
        action = "force-replaced"
    else:
        result = InstallResult(
            surface="ci/github-actions",
            target_path=target,
            action="conflict-halted",
            detail=(
                f"existing file at {target} has non-loam content; "
                f"pass --force to replace with backup"
            ),
            conflict_excerpt=existing_content[:200],
        )
        _audit_install(workspace_root, result, repo_path)
        raise InstallConflictError(result)

    if dry_run:
        return InstallResult(
            surface="ci/github-actions",
            target_path=target,
            action="dry-run",
            prior_version=prior_version,
            detail=f"would {action} {target}",
        )

    backup_path: Path | None = None
    if action == "force-replaced":
        from loam_pr_safety.installers.hooks import _backup_existing
        backup_path = _backup_existing(target)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")

    result = InstallResult(
        surface="ci/github-actions",
        target_path=target,
        action=action,  # type: ignore[arg-type]
        prior_version=prior_version,
        new_version=LOAM_PR_SAFETY_VERSION,
        backup_path=backup_path,
        detail=(
            f"{action} {target}"
            + (f"; backup at {backup_path}" if backup_path else "")
        ),
    )
    _audit_install(workspace_root, result, repo_path)
    return result


def _install_block_ci(
    repo_path: Path,
    target_rel: str,
    template_rel: str,
    surface_label: Literal["ci/gitlab-ci", "ci/circleci"],
    *,
    workspace_root: Path,
    force: bool,
    dry_run: bool,
) -> InstallResult:
    """Shared installer body for GitLab CI + CircleCI.

    Per Surface #3 — sentinel-block-delimited insertion. The loam
    block lives between
        # loam-pr-safety:managed:start:<version>
        # loam-pr-safety:managed:end
    Existing non-loam content surrounding the block is preserved.
    """
    target = repo_path / target_rel
    rendered_block = _render_template(
        _read_template(template_rel),
        version=LOAM_PR_SAFETY_VERSION,
    )

    existing_content = ""
    if target.exists():
        try:
            existing_content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            existing_content = "<binary content>"

    block_info = detect_loam_managed_block(existing_content) if existing_content else None
    sentinel_version = detect_loam_managed(existing_content)

    # Decide action.
    if not existing_content.strip():
        # Empty file or no file — write the block alone.
        action = "created"
        new_content = rendered_block.rstrip() + "\n"
        prior_version: str | None = None
    elif block_info is not None:
        # Loam block present — refresh it in-place.
        start, end, prior_version = block_info
        # Normalize comparison — strip trailing whitespace/newlines
        # so cosmetic line-ending differences don't trigger refresh.
        block_in_file = existing_content[start:end].rstrip()
        block_canonical = rendered_block.rstrip()
        if (
            prior_version == LOAM_PR_SAFETY_VERSION
            and block_in_file == block_canonical
        ):
            action = "noop"
            new_content = existing_content
        else:
            action = "refreshed"
            new_content = (
                existing_content[:start]
                + block_canonical
                + existing_content[end:]
            )
    elif sentinel_version is not None:
        # Plain sentinel without block delimiters — treat as
        # whole-file loam-managed (legacy / no-co-existence install).
        canonical = rendered_block.rstrip() + "\n"
        if (
            sentinel_version == LOAM_PR_SAFETY_VERSION
            and existing_content == canonical
        ):
            action = "noop"
            new_content = existing_content
            prior_version = sentinel_version
        else:
            action = "refreshed"
            new_content = canonical
            prior_version = sentinel_version
    elif is_effectively_empty(existing_content):
        # File has only comments/whitespace — write the block.
        action = "created"
        new_content = rendered_block.rstrip() + "\n"
        prior_version = None
    elif force:
        # Non-loam content — append block; preserve existing.
        action = "force-replaced"
        new_content = (
            existing_content.rstrip("\n")
            + "\n\n"
            + rendered_block.rstrip()
            + "\n"
        )
        prior_version = None
    else:
        result = InstallResult(
            surface=surface_label,
            target_path=target,
            action="conflict-halted",
            detail=(
                f"existing file at {target} has non-loam content "
                f"and no loam-managed:start..end block; pass --force "
                f"to append the loam block"
            ),
            conflict_excerpt=existing_content[:200],
        )
        _audit_install(workspace_root, result, repo_path)
        raise InstallConflictError(result)

    if dry_run:
        return InstallResult(
            surface=surface_label,
            target_path=target,
            action="dry-run",
            prior_version=prior_version,
            detail=f"would {action} {target}",
        )

    backup_path: Path | None = None
    if action == "force-replaced":
        # In force-replaced mode we APPEND not OVERWRITE so no backup
        # is technically needed — but we save a snapshot for trust.
        from loam_pr_safety.installers.hooks import _backup_existing
        backup_path = _backup_existing(target)
        # _backup_existing moved the file; rewrite from scratch with
        # appended block.

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(new_content, encoding="utf-8")

    result = InstallResult(
        surface=surface_label,
        target_path=target,
        action=action,  # type: ignore[arg-type]
        prior_version=prior_version,
        new_version=LOAM_PR_SAFETY_VERSION,
        backup_path=backup_path,
        detail=(
            f"{action} {target}"
            + (f"; backup at {backup_path}" if backup_path else "")
        ),
    )
    _audit_install(workspace_root, result, repo_path)
    return result


def install_ci_gitlab_ci(
    repo_path: Path,
    *,
    workspace_root: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    """Install the GitLab CI snippet (AC.PRSI.5)."""
    repo_path = repo_path.expanduser().resolve()
    workspace_root = (
        workspace_root.expanduser().resolve()
        if workspace_root is not None
        else Path.cwd().resolve()
    )
    return _install_block_ci(
        repo_path,
        target_rel=".gitlab-ci.yml",
        template_rel="ci/gitlab-ci/.gitlab-ci.snippet.yml.template",
        surface_label="ci/gitlab-ci",
        workspace_root=workspace_root,
        force=force,
        dry_run=dry_run,
    )


def install_ci_circleci(
    repo_path: Path,
    *,
    workspace_root: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    """Install the CircleCI snippet (AC.PRSI.6)."""
    repo_path = repo_path.expanduser().resolve()
    workspace_root = (
        workspace_root.expanduser().resolve()
        if workspace_root is not None
        else Path.cwd().resolve()
    )
    return _install_block_ci(
        repo_path,
        target_rel=".circleci/config.yml",
        template_rel="ci/circleci/config.snippet.yml.template",
        surface_label="ci/circleci",
        workspace_root=workspace_root,
        force=force,
        dry_run=dry_run,
    )


def render_validates(content: str) -> bool:
    """Return ``True`` iff ``content`` parses as valid YAML.

    Per AC.PRSI.{4,5,6} — render-validation primitive used by tests.
    """
    try:
        yaml.safe_load(content)
        return True
    except yaml.YAMLError:
        return False
