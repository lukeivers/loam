"""Pre-commit + pre-push hook installers + hook-fire dispatcher for
loam-pr-safety.

Per AC.PRSI.{1,2,3} (v0.1.9 Cycle 2). Plan-doc §3 + §4 + §5 Surface
#4 (husky detection) + Surface #5 (env-var bypass under dev profile).

Idempotency model (Surface #2):

  - Read the existing target file.
  - If sentinel present + version matches → noop.
  - If sentinel present + version differs → refresh (rewrite).
  - If sentinel absent + file empty (or comment-only) → write.
  - If sentinel absent + file non-empty → conflict-halt (or
    force-replaced if `force=True`).

Husky routing (Surface #4):

  - Detect husky via ``<repo>/.husky/_/husky.sh`` (v6+) OR
    ``<repo>/package.json`` top-level ``"husky"`` key (v4-v5).
  - When detected, install at ``<repo>/.husky/<hook>`` with the
    husky-shaped variant template.

Hook-fire dispatch (AC.PRSI.3):

  - ``fire_hook(repo_path, hook_name)`` is invoked by both standard
    and husky-shaped hook scripts.
  - Reads workspace ``safety_profile``; honours
    ``LOAM_PR_SAFETY_BYPASS=1`` ONLY under dev/research profiles.
  - Audit-logs every fire (event_kind: hook_fired) and every bypass
    attempt (event_kind: hook_bypass | hook_bypass_attempt_rejected).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path
from typing import Literal

from loam_pr_safety.audit import write_audit_entry
from loam_pr_safety.classifier import classify
from loam_pr_safety.contract import read_contract
from loam_pr_safety.diff import parse_diff
from loam_pr_safety.errors import (
    ContractMissingError,
    GateError,
    PRSafetyError,
)
from loam_pr_safety.gate import decide
from loam_pr_safety.installers.conflicts import (
    InstallConflictError,
    InstallResult,
    LOAM_PR_SAFETY_VERSION,
    detect_loam_managed,
    is_effectively_empty,
)
from loam_pr_safety.profile import (
    is_production_stake,
    read_safety_profile,
)
from loam_pr_safety.spec import GateAction
from loam_pr_safety.state import compute_repo_id


HookName = Literal["pre-commit", "pre-push"]


def detect_husky(repo_path: Path) -> bool:
    """Return ``True`` iff husky is installed in ``repo_path``.

    Per Surface #4 — detection rule is:
      - ``<repo>/.husky/_/husky.sh`` exists (v6+ runner-file path), OR
      - ``<repo>/package.json`` has a top-level ``"husky"`` key
        (v4-v5 config).
    """
    repo_path = repo_path.expanduser().resolve()
    husky_runner = repo_path / ".husky" / "_" / "husky.sh"
    if husky_runner.exists():
        return True
    pkg_json = repo_path / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
        if isinstance(data, dict) and "husky" in data:
            return True
    return False


def _read_template(template_rel_path: str) -> str:
    """Read a template file from the package's templates/ resource.

    ``template_rel_path`` is relative to ``loam_pr_safety/templates/``,
    e.g. ``"hooks/pre-commit.sh.template"``.

    Path-based resolution (rather than importlib.resources package
    walking) — sub-paths like ``ci/github-actions/`` use hyphens
    which aren't valid Python package names but ARE valid filesystem
    paths.
    """
    base = (
        Path(resources.files("loam_pr_safety.templates").joinpath("."))
    )
    return (base / template_rel_path).read_text(encoding="utf-8")


def _render_template(content: str, *, version: str) -> str:
    """Substitute placeholders in a template body."""
    return content.replace("{LOAM_PR_SAFETY_VERSION}", version)


def _resolve_hook_target(
    repo_path: Path,
    hook_name: HookName,
    husky: bool,
) -> Path:
    """Return the path the hook should be installed at."""
    repo_path = repo_path.expanduser().resolve()
    if husky:
        return repo_path / ".husky" / hook_name
    return repo_path / ".git" / "hooks" / hook_name


def _select_hook_template(
    hook_name: HookName, husky: bool
) -> str:
    """Return the rendered hook script for ``hook_name`` + husky flag."""
    if husky:
        rel = f"hooks/husky-{hook_name}.sh.template"
    else:
        rel = f"hooks/{hook_name}.sh.template"
    raw = _read_template(rel)
    return _render_template(raw, version=LOAM_PR_SAFETY_VERSION)


def _backup_existing(target_path: Path) -> Path:
    """Move the existing file to ``<target>.bak.<N>`` and return the
    backup path.

    Counter is monotonic (highest existing N + 1).
    """
    parent = target_path.parent
    stem_pat = f"{target_path.name}.bak."
    existing = [
        p
        for p in parent.iterdir()
        if p.name.startswith(stem_pat)
    ]
    nums: list[int] = []
    for p in existing:
        suffix = p.name[len(stem_pat):]
        try:
            nums.append(int(suffix))
        except ValueError:
            continue
    n = (max(nums) if nums else 0) + 1
    backup = parent / f"{target_path.name}.bak.{n}"
    shutil.move(str(target_path), str(backup))
    return backup


def _install_hook(
    repo_path: Path,
    hook_name: HookName,
    *,
    workspace_root: Path,
    force: bool,
    dry_run: bool,
) -> InstallResult:
    """Shared installer body for pre-commit + pre-push.

    Per AC.PRSI.{1,2,3}.
    """
    repo_path = repo_path.expanduser().resolve()
    husky = detect_husky(repo_path)
    target = _resolve_hook_target(repo_path, hook_name, husky)
    surface_label: Literal["pre-commit", "pre-push"] = hook_name
    rendered = _select_hook_template(hook_name, husky)

    # Ensure parent directory exists for husky case (`.husky/`).
    if husky and not dry_run:
        (repo_path / ".husky").mkdir(parents=True, exist_ok=True)

    # Read existing content.
    existing_content = ""
    if target.exists():
        try:
            existing_content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            existing_content = "<binary content>"

    prior_version = detect_loam_managed(existing_content)

    # Decide action.
    if not target.exists() or not existing_content.strip():
        action: Literal[
            "created",
            "refreshed",
            "noop",
            "conflict-halted",
            "force-replaced",
            "dry-run",
        ] = "created"
    elif prior_version is not None:
        if prior_version == LOAM_PR_SAFETY_VERSION and existing_content == rendered:
            action = "noop"
        else:
            action = "refreshed"
    else:
        # Non-loam content present.
        if is_effectively_empty(existing_content):
            action = "created"
        elif force:
            action = "force-replaced"
        else:
            # Conflict-halt.
            result = InstallResult(
                surface=surface_label,
                target_path=target,
                action="conflict-halted",
                husky_routed=husky,
                prior_version=None,
                new_version=LOAM_PR_SAFETY_VERSION,
                detail=(
                    f"existing {hook_name} hook at {target} has "
                    f"non-loam content; pass --force to replace with "
                    f"backup"
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
            husky_routed=husky,
            prior_version=prior_version,
            detail=f"would {action} {target}",
        )

    # Apply.
    backup_path: Path | None = None
    if action == "force-replaced":
        backup_path = _backup_existing(target)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    # chmod +x.
    target.chmod(target.stat().st_mode | 0o111)

    result = InstallResult(
        surface=surface_label,
        target_path=target,
        action=action,
        husky_routed=husky,
        prior_version=prior_version,
        new_version=LOAM_PR_SAFETY_VERSION,
        backup_path=backup_path,
        detail=(
            f"{action} {target}"
            + (f" (husky)" if husky else "")
            + (f"; backup at {backup_path}" if backup_path else "")
        ),
    )
    _audit_install(workspace_root, result, repo_path)
    return result


def _audit_install(
    workspace_root: Path,
    result: InstallResult,
    repo_path: Path,
) -> None:
    """Write an install-action audit-log entry per AC.PRSG.7 schema."""
    event_map = {
        "pre-commit": "install_pre_commit",
        "pre-push": "install_pre_push",
        "ci/github-actions": "install_ci_github_actions",
        "ci/gitlab-ci": "install_ci_gitlab_ci",
        "ci/circleci": "install_ci_circleci",
        "pr-template": "install_pr_template",
    }
    base = event_map.get(result.surface, "install_unknown")
    if result.is_conflict:
        event_kind = "install_conflict"
    else:
        event_kind = base
    repo_id = compute_repo_id(repo_path)
    write_audit_entry(
        workspace_root,
        event_kind=event_kind,
        repo_id=repo_id,
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


def install_pre_commit(
    repo_path: Path,
    *,
    workspace_root: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    """Install the pre-commit hook (AC.PRSI.1)."""
    workspace_root = (
        workspace_root.expanduser().resolve()
        if workspace_root is not None
        else Path.cwd().resolve()
    )
    return _install_hook(
        repo_path,
        "pre-commit",
        workspace_root=workspace_root,
        force=force,
        dry_run=dry_run,
    )


def install_pre_push(
    repo_path: Path,
    *,
    workspace_root: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    """Install the pre-push hook (AC.PRSI.2)."""
    workspace_root = (
        workspace_root.expanduser().resolve()
        if workspace_root is not None
        else Path.cwd().resolve()
    )
    return _install_hook(
        repo_path,
        "pre-push",
        workspace_root=workspace_root,
        force=force,
        dry_run=dry_run,
    )


# ---- Hook-fire dispatcher (AC.PRSI.3) -------------------------------


def _resolve_workspace_for_repo(repo_path: Path) -> Path:
    """Resolve the workspace root for a repo path.

    Convention: the workspace root is the dir containing the
    ``.loam/`` directory the gate reads. If the repo IS the workspace
    (canonical pos-v2 case), repo == workspace.

    Resolution order:
      1. ``LOAM_WORKSPACE_ROOT`` env var if set.
      2. Walk up from ``repo_path`` looking for ``.loam/`` directory;
         first hit wins.
      3. Fallback: ``repo_path`` itself.
    """
    env_ws = os.environ.get("LOAM_WORKSPACE_ROOT")
    if env_ws:
        return Path(env_ws).expanduser().resolve()
    cur = repo_path.expanduser().resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / ".loam").is_dir():
            return candidate
    return cur


def fire_hook(
    repo_path: Path,
    hook_name: HookName,
    *,
    workspace_root: Path | None = None,
) -> int:
    """Fire the gate from a hook script context.

    Per AC.PRSI.3 — honours ``LOAM_PR_SAFETY_BYPASS=1`` only under
    dev/research profiles. Under production-stake the env var is
    ignored; the bypass attempt is audit-logged.

    Returns the exit code for the hook script to propagate:

      0 PASS (or honoured bypass under dev)
      2 HARD-BLOCK
      3 SURFACE-DECISION
      4 OVERRIDE-REJECTED
      5 GateError / ContractMissing
    """
    repo_path = repo_path.expanduser().resolve()
    workspace_root = (
        workspace_root.expanduser().resolve()
        if workspace_root is not None
        else _resolve_workspace_for_repo(repo_path)
    )

    bypass_attempted = os.environ.get("LOAM_PR_SAFETY_BYPASS") == "1"
    prodstake = is_production_stake(workspace_root)
    safety_profile = read_safety_profile(workspace_root)
    repo_id = compute_repo_id(repo_path)

    # Resolve diff range for the hook context.
    if hook_name == "pre-commit":
        # Working-tree-vs-HEAD.
        from_sha, to_sha = (None, None)
        diff_range_str = "(working-tree vs HEAD)"
    else:  # pre-push
        # Read pre-push stdin (if any); fall back to HEAD-vs-upstream.
        # Pre-push protocol: lines of
        #   "<local-ref> <local-sha> <remote-ref> <remote-sha>"
        # For Cycle 2 simplicity, we gate the most-recent change set:
        # HEAD vs upstream tracking branch (resolved below).
        from_sha, to_sha = _resolve_pre_push_range(repo_path)
        diff_range_str = (
            f"{from_sha or '?'}..{to_sha or 'HEAD'}"
        )

    # Bypass-honour decision (Surface #5).
    if bypass_attempted:
        if prodstake:
            # Production-stake — bypass IGNORED. Audit-log + run gate.
            write_audit_entry(
                workspace_root,
                event_kind="hook_bypass_attempt_rejected",
                repo_id=repo_id,
                repo_sha="",
                diff_range=diff_range_str,
                safety_profile=safety_profile,
                decision="bypass_rejected",
                requires_ratification=True,
                touched_acs=[],
                novel_count=0,
                reason=(
                    f"LOAM_PR_SAFETY_BYPASS=1 ignored under "
                    f"production-stake; gate runs as normal "
                    f"(hook={hook_name})"
                ),
                owner=None,
                rationale=None,
                hook=hook_name,
            )
            # Continue to gate.
        else:
            # dev/research — bypass honoured. Audit + skip gate.
            write_audit_entry(
                workspace_root,
                event_kind="hook_bypass",
                repo_id=repo_id,
                repo_sha="",
                diff_range=diff_range_str,
                safety_profile=safety_profile,
                decision="bypass_honoured",
                requires_ratification=False,
                touched_acs=[],
                novel_count=0,
                reason=(
                    f"LOAM_PR_SAFETY_BYPASS=1 honoured under "
                    f"{safety_profile} profile (hook={hook_name})"
                ),
                owner=None,
                rationale=None,
                hook=hook_name,
            )
            sys.stderr.write(
                f"loam-pr-safety: bypass honoured under "
                f"{safety_profile} profile (hook={hook_name}); "
                f"audit-log entry written\n"
            )
            return 0

    # Run gate.
    try:
        contract = read_contract(repo_id, workspace_root)
        diff = parse_diff(repo_path, from_sha=from_sha, to_sha=to_sha)
        classification = classify(diff, contract)
        decision = decide(
            classification,
            safety_profile=safety_profile,
            extraction_id=contract.extraction_id,
            require_ratification=False,
        )

        # Audit-log the hook fire.
        write_audit_entry(
            workspace_root,
            event_kind="hook_fired",
            repo_id=repo_id,
            repo_sha=contract.repo_sha or "",
            diff_range=diff_range_str,
            safety_profile=safety_profile,
            decision=decision.action.value,
            requires_ratification=decision.requires_ratification,
            touched_acs=[t.ac.ac_id for t in decision.touched_acs],
            novel_count=len(decision.novel),
            reason=decision.reason,
            owner=None,
            rationale=None,
            hook=hook_name,
        )

        # Surface decision to stderr for the user.
        sys.stderr.write(
            f"loam pr-safety [{hook_name}]: {decision.action.value} "
            f"({len(decision.touched_acs)} touched ACs, "
            f"{len(decision.novel)} novel)\n"
        )
        if decision.reason:
            sys.stderr.write(f"  {decision.reason}\n")

        if decision.action is GateAction.HARD_BLOCK:
            return 2
        if decision.action is GateAction.SURFACE_DECISION:
            # Hooks DO NOT block on SURFACE-DECISION (PM batch is
            # async); return 0 so the commit/push proceeds; the
            # decision is queued for ratification.
            return 0
        return 0
    except ContractMissingError as exc:
        sys.stderr.write(
            f"loam pr-safety [{hook_name}]: contract missing "
            f"({exc}); skipping gate\n"
        )
        # Audit-log the missing contract too.
        write_audit_entry(
            workspace_root,
            event_kind="hook_fired",
            repo_id=repo_id,
            repo_sha="",
            diff_range=diff_range_str,
            safety_profile=safety_profile,
            decision="contract_missing",
            requires_ratification=False,
            touched_acs=[],
            novel_count=0,
            reason=str(exc),
            owner=None,
            rationale=None,
            hook=hook_name,
        )
        # Contract-missing is not a hook failure — let the user
        # commit/push (the gate has nothing to enforce).
        return 0
    except PRSafetyError as exc:
        sys.stderr.write(f"loam pr-safety [{hook_name}]: error: {exc}\n")
        return 5


def _resolve_pre_push_range(
    repo_path: Path,
) -> tuple[str | None, str | None]:
    """Resolve the diff range for a pre-push fire.

    Cycle 2 simplification: HEAD vs upstream tracking branch
    (``@{u}``) if it exists; else HEAD vs origin/main; else
    None,None (working-tree-vs-HEAD).

    Reading pre-push stdin (the ref-spec lines) is feasible but
    Cycle 2 ships the simpler "gate the most-recent change set"
    semantics; full ref-iteration is a v0.2.x candidate.
    """
    repo_path = repo_path.expanduser().resolve()
    # Try @{u}.
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "@{u}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            upstream = proc.stdout.strip()
            return (upstream, "HEAD")
    except FileNotFoundError:
        pass
    # Fallback: origin/main.
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(repo_path),
                "rev-parse",
                "origin/main",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            return (proc.stdout.strip(), "HEAD")
    except FileNotFoundError:
        pass
    return (None, None)
