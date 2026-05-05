"""Provenance-traceable PR description template installer + renderer.

Per AC.PRSI.7 (v0.1.9 Cycle 2). Plan-doc §3 + §4 + §5 Surface #6
(--render-pr-description gate-mode flag) + Surface #7 (body-overflow
truncation strategy).

The template file at ``.github/pull_request_template.md`` carries
placeholder slots; the gate's ``--render-pr-description`` flag
expands them when invoked in a CI context.

Sections (per AC.PRSI.7):
  - Gate decision (action + reason + provenance: commit/repo SHA,
    diff range)
  - ACs touched (one bullet per touched AC with band + touch-kind +
    text + provenance)
  - Novel candidates (per-file)
  - Override history (from approved overlays at
    <workspace>/.loam/pr-safety/contract-overrides/<repo-id>/)
  - Audit-log excerpt (last 3 entries)

Body-overflow strategy (Surface #7):
  60,000 char ceiling (vs GitHub's 65,536); deterministic ordered
  truncation; truncation footer always includes audit-log path.
"""

from __future__ import annotations

import yaml
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from loam_pr_safety.audit import list_entries
from loam_pr_safety.installers.conflicts import (
    InstallConflictError,
    InstallResult,
    LOAM_PR_SAFETY_VERSION,
    detect_loam_managed,
)


if TYPE_CHECKING:
    from loam_pr_safety.spec import GateDecision


# Body-overflow ceiling (Surface #7). 60K chars leaves 5,536 char
# headroom under GitHub's 65,536 limit for surface-specific encoding.
_PR_DESCRIPTION_CHAR_CEILING = 60_000

# Per-AC provenance truncation length under overflow (Surface #7
# step 1).
_PROVENANCE_TRUNCATE_CHARS = 200


def _read_template(template_rel_path: str) -> str:
    """Path-based template resolution."""
    base = (
        Path(resources.files("loam_pr_safety.templates").joinpath("."))
    )
    return (base / template_rel_path).read_text(encoding="utf-8")


def _render_template_content(content: str, *, version: str) -> str:
    return content.replace("{LOAM_PR_SAFETY_VERSION}", version)


def _audit_install(
    workspace_root: Path,
    result: InstallResult,
    repo_path: Path,
) -> None:
    from loam_pr_safety.audit import write_audit_entry
    from loam_pr_safety.profile import read_safety_profile
    from loam_pr_safety.state import compute_repo_id

    event_kind = (
        "install_conflict"
        if result.is_conflict
        else "install_pr_template"
    )
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


def install_pr_template(
    repo_path: Path,
    *,
    workspace_root: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    """Install the PR description template (AC.PRSI.7).

    Targets:
      - ``<repo>/.github/pull_request_template.md`` (canonical)
      - ``<repo>/.loam/pr-safety/pr_description.template.md``
        (generic-markdown variant the caller can pipe into other
        surfaces)

    Both written; conflict detected only on the canonical
    ``.github/pull_request_template.md`` (the second is loam-internal).
    """
    repo_path = repo_path.expanduser().resolve()
    workspace_root = (
        workspace_root.expanduser().resolve()
        if workspace_root is not None
        else Path.cwd().resolve()
    )
    target = repo_path / ".github" / "pull_request_template.md"
    secondary = repo_path / ".loam" / "pr-safety" / "pr_description.template.md"
    rendered = _render_template_content(
        _read_template("pr/pr_description.md.template"),
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
    elif not existing_content.strip():
        # For markdown files, `#` is a header (content), not a
        # comment. Don't use is_effectively_empty here — only treat
        # whitespace-only files as truly empty.
        action = "created"
    elif force:
        action = "force-replaced"
    else:
        result = InstallResult(
            surface="pr-template",
            target_path=target,
            action="conflict-halted",
            detail=(
                f"existing PR template at {target} has non-loam "
                f"content; pass --force to replace with backup"
            ),
            conflict_excerpt=existing_content[:200],
        )
        _audit_install(workspace_root, result, repo_path)
        raise InstallConflictError(result)

    if dry_run:
        return InstallResult(
            surface="pr-template",
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

    secondary.parent.mkdir(parents=True, exist_ok=True)
    secondary.write_text(rendered, encoding="utf-8")

    result = InstallResult(
        surface="pr-template",
        target_path=target,
        action=action,  # type: ignore[arg-type]
        prior_version=prior_version,
        new_version=LOAM_PR_SAFETY_VERSION,
        backup_path=backup_path,
        detail=(
            f"{action} {target} (+ secondary at {secondary})"
            + (f"; backup at {backup_path}" if backup_path else "")
        ),
    )
    _audit_install(workspace_root, result, repo_path)
    return result


# ---- render_pr_description (gate-mode rendering) -------------------


def _render_section_gate_decision(decision: "GateDecision") -> str:
    """Section: gate decision + reason + provenance."""
    lines = [
        f"### Gate decision: {decision.action.value}",
        "",
        f"- requires_ratification: {decision.requires_ratification}",
        f"- safety_profile: {decision.safety_profile}",
    ]
    if decision.reason:
        lines.append(f"- reason: {decision.reason}")
    return "\n".join(lines)


def _render_section_touched_acs(
    decision: "GateDecision",
    *,
    truncate: bool = False,
) -> str:
    """Section: per-objective bullets with band + touch-kind +
    backing rows.

    Per AC.PRGATE.5 — at objective altitude. Renders objective TEXT
    + domain + band + backing rows path:line. AC.* IDs DO NOT appear.
    """
    if not decision.touched_objectives:
        return "### Touched objectives: none"
    lines = [
        f"### Touched objectives ({len(decision.touched_objectives)})"
    ]
    lines.append("")
    for t in decision.touched_objectives:
        obj = t.objective
        # Backing-row provenance (path:line-range).
        rows_str_parts: list[str] = []
        for row in t.touched_evidence_rows[:3]:
            if row.line_range:
                start, end = row.line_range
                if start == end:
                    rows_str_parts.append(f"{row.path}:{start}")
                else:
                    rows_str_parts.append(f"{row.path}:{start}-{end}")
            else:
                rows_str_parts.append(row.path)
        rows_str = ", ".join(rows_str_parts) if rows_str_parts else ""
        if len(t.touched_evidence_rows) > 3:
            rows_str += f", … ({len(t.touched_evidence_rows) - 3} more)"

        obj_text = obj.text
        if truncate:
            obj_text = obj_text[:_PROVENANCE_TRUNCATE_CHARS]
            if len(obj.text) > _PROVENANCE_TRUNCATE_CHARS:
                obj_text += "…"
            rows_str = rows_str[:_PROVENANCE_TRUNCATE_CHARS]

        lines.append(
            f"- **{obj.objective_id}** [`{obj.confidence.value}`] "
            f"({obj.domain}; touch={t.touch_kind}) — {obj_text}"
            + (f"\n  - backing rows: {rows_str}" if rows_str else "")
        )
    return "\n".join(lines)


def _render_section_novel(
    decision: "GateDecision",
    *,
    include_section: bool = True,
) -> str:
    """Section: novel diff hunks (per-file).

    Per AC.PRGATE.5 — Cycle 3 surfaces audit-only; v0.2.4 gap-analysis
    extracts structured proposals.
    """
    if not include_section:
        return ""
    if not decision.novel:
        return ""
    lines = [f"### Novel diffs ({len(decision.novel)})", ""]
    for c in decision.novel:
        lines.append(
            f"- `{c.file_path}` ({len(c.hunks)} hunk(s))"
        )
    return "\n".join(lines)


def _render_section_override_history(
    workspace_root: Path,
    repo_id: str,
) -> str:
    """Section: override history from approved overlays."""
    from loam_pr_safety.state import overrides_dir

    od = overrides_dir(workspace_root, repo_id)
    if not od.exists():
        return ""
    overlays = sorted(od.glob("override-*.yaml"))
    if not overlays:
        return ""
    lines = [f"### Override audit trail ({len(overlays)})", ""]
    for ovl_path in overlays:
        try:
            data = yaml.safe_load(
                ovl_path.read_text(encoding="utf-8")
            )
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        kind = data.get("kind", "")
        rationale = data.get("rationale", "")
        owner = data.get("owner", "")
        applied_at = data.get("applied_at", "")
        commit_sha = data.get("commit_sha", "")
        # Cycle 3 overlay shape carries original_objective_id +
        # replacement_objective. Legacy migrated overlays carry
        # legacy_original_ac_id.
        obj_id = (
            data.get("original_objective_id")
            or data.get("replacement_objective", {}).get("objective_id")
            or data.get("legacy_original_ac_id")
            or "(unknown objective)"
        )
        lines.append(
            f"- **{obj_id}** [{kind}] — {owner} at "
            f"{applied_at}; commit `{commit_sha[:8]}`; rationale: "
            f"{rationale[:200]}"
        )
    return "\n".join(lines)


def _render_section_audit_excerpt(
    workspace_root: Path,
    repo_id: str,
    *,
    n_entries: int = 3,
) -> str:
    """Section: last N audit-log entries pertaining to this repo."""
    entries = list_entries(workspace_root)
    if not entries:
        return "### Audit-log excerpt: (no entries)"
    matching: list[Path] = []
    # Iterate newest-first.
    for p in reversed(entries):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("repo_id") == repo_id:
            matching.append(p)
        if len(matching) >= n_entries:
            break
    if not matching:
        return "### Audit-log excerpt: (no entries for this repo)"
    lines = [f"### Audit-log excerpt (last {len(matching)})", ""]
    for p in matching:
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        ts = data.get("timestamp", "")
        ek = data.get("event_kind", "")
        dec = data.get("decision", "")
        reason = (data.get("reason") or "")[:200]
        lines.append(
            f"- `{p.name}` — {ts} — {ek} — {dec}"
            + (f" — {reason}" if reason else "")
        )
    return "\n".join(lines)


def render_pr_description(
    decision: "GateDecision",
    *,
    workspace_root: Path,
    repo_id: str,
) -> str:
    """Render a markdown PR description from a gate decision.

    Per AC.PRSI.7. Surface #6 — invoked by the gate's
    ``--render-pr-description`` flag.

    Output is markdown with all five sections; if it exceeds
    ``_PR_DESCRIPTION_CHAR_CEILING`` chars, the deterministic
    truncation strategy from Surface #7 is applied.
    """
    sections = [
        _render_section_gate_decision(decision),
        _render_section_touched_acs(decision, truncate=False),
        _render_section_novel(decision, include_section=True),
        _render_section_override_history(workspace_root, repo_id),
        _render_section_audit_excerpt(
            workspace_root, repo_id, n_entries=3
        ),
    ]
    body = "\n\n".join(s for s in sections if s)
    truncated_footer = (
        f"\n\n---\n\n_(truncated; full audit-log at "
        f"`{workspace_root}/.loam/pr-safety/audit-log/`)_"
    )

    if len(body) <= _PR_DESCRIPTION_CHAR_CEILING:
        return body

    # Step 1: truncate per-AC provenance.
    sections[1] = _render_section_touched_acs(decision, truncate=True)
    body = "\n\n".join(s for s in sections if s)
    if len(body) + len(truncated_footer) <= _PR_DESCRIPTION_CHAR_CEILING:
        return body + truncated_footer

    # Step 2: truncate audit-log excerpt to 1 entry.
    sections[4] = _render_section_audit_excerpt(
        workspace_root, repo_id, n_entries=1
    )
    body = "\n\n".join(s for s in sections if s)
    if len(body) + len(truncated_footer) <= _PR_DESCRIPTION_CHAR_CEILING:
        return body + truncated_footer

    # Step 3: drop novel-candidates section.
    sections[2] = ""
    body = "\n\n".join(s for s in sections if s)
    if len(body) + len(truncated_footer) <= _PR_DESCRIPTION_CHAR_CEILING:
        return body + truncated_footer

    # Step 4: hard-truncate body to ceiling-headroom and footer.
    headroom = _PR_DESCRIPTION_CHAR_CEILING - len(truncated_footer)
    return body[:headroom] + truncated_footer
