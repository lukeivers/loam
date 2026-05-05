"""SOC-2 audit-trail floor for loam-pr-safety.

Per AC.PRSG.7 + Decision P — every gate decision (PASS / HARD-BLOCK
/ SURFACE-DECISION / DOCS-ONLY / dry-run / override-proposed /
override-approved / override-rejected) writes one entry under
``<workspace>/.loam/pr-safety/audit-log/<YYYY-MM-DD>-<NNNN>.yaml``.

Schema mirrors per-project-pm + odd-extractor precedent (Surface #8).
Per-day NNNN counter (gate runs are unbounded; date-bucketing keeps
the directory tidy).
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any

import yaml

from loam_pr_safety.state import audit_log_dir as _audit_log_dir


_AUDIT_LOG_SCHEMA_VERSION = 1
_FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{4})\.yaml$")


def audit_log_dir(workspace_root: Path) -> Path:
    """Return the workspace's audit-log directory.

    Re-exports :func:`loam_pr_safety.state.audit_log_dir` for
    callers that want the audit module as the single import.
    """
    return _audit_log_dir(workspace_root)


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _utc_today() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


def _next_audit_seq(audit_dir: Path, ymd: str) -> int:
    """Return the next 1-based monotonic counter for ``ymd``.

    Scans ``audit_dir`` for files matching
    ``<ymd>-\\d{4}\\.yaml`` and returns ``max(seen) + 1`` (or
    ``1`` if no entries exist for the day).
    """
    if not audit_dir.exists():
        return 1
    seen: list[int] = []
    for entry in audit_dir.iterdir():
        m = _FILENAME_RE.match(entry.name)
        if m and m.group(1) == ymd:
            seen.append(int(m.group(2)))
    return (max(seen) if seen else 0) + 1


def write_audit_entry(
    workspace_root: Path,
    *,
    event_kind: str,
    repo_id: str,
    repo_sha: str = "",
    diff_range: str = "",
    safety_profile: str = "",
    decision: str | None = None,
    requires_ratification: bool = False,
    touched_acs: list[str] | None = None,
    novel_count: int = 0,
    reason: str = "",
    owner: str | None = None,
    rationale: str | None = None,
    timestamp: str | None = None,
    today_ymd: str | None = None,
    target_path: str | None = None,
    hook: str | None = None,
    objective_ids_touched: list[str] | None = None,
    objective_bands_touched: dict[str, str] | None = None,
    backing_rows_overlapped: dict[str, list[str]] | None = None,
    extraction_id: str | None = None,
) -> Path:
    """Append one audit-log entry; return the entry's path.

    Per AC.PRGATE.6 (v0.2.3 Cycle 3) — payload extends additively
    with objective-altitude fields (``objective_ids_touched`` +
    ``objective_bands_touched`` + ``backing_rows_overlapped`` +
    ``extraction_id``). No schema-version bump per master plan
    direction; SOC-2 floor (Decision P) preserved.

    ``event_kind`` ∈ {``gate_decision``, ``override_proposed``,
    ``override_approved``, ``override_rejected``, ``dry_run``,
    ``install_pre_commit``, ``install_pre_push``,
    ``install_ci_github_actions``, ``install_ci_gitlab_ci``,
    ``install_ci_circleci``, ``install_pr_template``,
    ``install_conflict``, ``hook_fired``, ``hook_bypass``,
    ``hook_bypass_attempt_rejected``, ``pr_description_rendered``}.

    Backward compat: legacy callers passing only ``touched_acs``
    continue to work; the field name is preserved (``touched_acs``
    holds objective_ids in Cycle 3).

    ``timestamp`` and ``today_ymd`` are injectable for deterministic
    tests.
    """
    audit_dir = audit_log_dir(workspace_root)
    audit_dir.mkdir(parents=True, exist_ok=True)
    ymd = today_ymd if today_ymd is not None else _utc_today()
    seq = _next_audit_seq(audit_dir, ymd)
    entry_path = audit_dir / f"{ymd}-{seq:04d}.yaml"
    payload: dict[str, Any] = {
        "schema_version": _AUDIT_LOG_SCHEMA_VERSION,
        "event_kind": event_kind,
        "timestamp": (
            timestamp if timestamp is not None else _utc_now_iso()
        ),
        "repo_id": repo_id,
        "repo_sha": repo_sha,
        "diff_range": diff_range,
        "safety_profile": safety_profile,
        "decision": decision,
        "requires_ratification": requires_ratification,
        "touched_acs": list(touched_acs or []),
        "novel_count": int(novel_count),
        "reason": reason,
        "owner": owner,
        "rationale": rationale,
        "target_path": target_path,
        "hook": hook,
        # AC.PRGATE.6 — objective-altitude additive fields.
        "objective_ids_touched": list(objective_ids_touched or []),
        "objective_bands_touched": dict(objective_bands_touched or {}),
        "backing_rows_overlapped": dict(backing_rows_overlapped or {}),
        "extraction_id": extraction_id,
    }
    entry_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    return entry_path


def list_entries(workspace_root: Path) -> list[Path]:
    """Return every audit-log entry path, sorted by (date, counter)."""
    audit_dir = audit_log_dir(workspace_root)
    if not audit_dir.exists():
        return []
    entries = [
        p for p in audit_dir.iterdir() if _FILENAME_RE.match(p.name)
    ]

    def _sort_key(p: Path) -> tuple[str, int]:
        m = _FILENAME_RE.match(p.name)
        # _FILENAME_RE.match is guaranteed non-None by the iterdir
        # filter above.
        assert m is not None
        return (m.group(1), int(m.group(2)))

    entries.sort(key=_sort_key)
    return entries
