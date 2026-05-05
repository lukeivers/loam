"""Audit-log writer for the odd-extractor.

Per AC.OREK.7 (D6 telemetry-floor) — every extraction run writes
``extraction_start`` + ``extraction_end`` bookend entries; every
stage writes one ``stage_complete`` entry; budget overrides write a
``budget_override`` entry. SOC-2 audit-trail floor (Decision P).

Per Surface #8 (plan-doc §5) — schema mirrors per-project-pm's
audit-log entry shape. Filenames use ``<NNNN>.yaml`` with monotonic
sequence per extraction-run (since extractions are bounded — the
NNNN counter doesn't need date-scoped buckets the way per-project-pm's
does).
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any

import yaml


_AUDIT_LOG_SCHEMA_VERSION = 1
_FILENAME_RE = re.compile(r"^(\d{4})\.yaml$")


# Per v0.2.4 Cycle 1 AC.COMPINT.8 — completeness-interview event_kinds.
# Structured payload uses the existing ``estimate`` field (no schema
# bump). Listed here as a module-level constant so tests + downstream
# consumers can introspect the canonical set.
COMPLETENESS_INTERVIEW_EVENT_KINDS: tuple[str, ...] = (
    "completeness_interview_start",
    "objective_confirmed",
    "objective_adjusted",
    "objective_flagged_out_of_scope",
    "objective_added_by_user",
    "objective_flagged_by_persona",
    "completeness_interview_end",
)


def audit_log_dir(extraction_dir_: Path) -> Path:
    """``<extraction_dir>/audit-log/``."""
    return extraction_dir_ / "audit-log"


def _next_counter(audit_dir: Path) -> int:
    """Return the next 1-based monotonic counter.

    Scans ``audit-dir`` for files matching ``\\d{4}\\.yaml`` and
    returns ``max(seen) + 1`` (or ``1`` if empty / missing).
    """
    if not audit_dir.exists():
        return 1
    seen: list[int] = []
    for entry in audit_dir.iterdir():
        m = _FILENAME_RE.match(entry.name)
        if m:
            seen.append(int(m.group(1)))
    return (max(seen) if seen else 0) + 1


def _now_iso() -> str:
    """ISO 8601 timestamp in UTC with explicit ``+00:00`` offset."""
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def write_audit_entry(
    extraction_dir_: Path,
    *,
    event_kind: str,
    extraction_id: str,
    stage: str | None = None,
    artefact_path: str | None = None,
    estimate: dict[str, Any] | None = None,
    notes: str = "",
    timestamp: str | None = None,
) -> Path:
    """Append one audit-log entry; return the entry's path.

    ``event_kind`` ∈ {``extraction_start``, ``stage_complete``,
    ``extraction_end``, ``extraction_failed``, ``budget_override``,
    ``synthesis_complete`` (v0.2.3 AC.OBJX.12),
    ``altitude_check_complete`` (v0.2.3 AC.OBJX.12),
    plus the v0.2.4 Cycle 1 completeness-interview kinds in
    :data:`COMPLETENESS_INTERVIEW_EVENT_KINDS`:
    ``completeness_interview_start``, ``objective_confirmed``,
    ``objective_adjusted``, ``objective_flagged_out_of_scope``,
    ``objective_added_by_user``, ``objective_flagged_by_persona``,
    ``completeness_interview_end``}.

    ``stage`` is one of ``init`` / ``analyze`` / ``generate`` /
    ``verify`` for ``stage_complete`` and ``synthesis_complete`` /
    ``altitude_check_complete`` (which both anchor at ``generate``);
    ``None`` otherwise.

    ``timestamp`` is injectable for deterministic tests; defaults to
    ``_now_iso()``.
    """
    audit_dir = audit_log_dir(extraction_dir_)
    audit_dir.mkdir(parents=True, exist_ok=True)
    counter = _next_counter(audit_dir)
    entry_path = audit_dir / f"{counter:04d}.yaml"
    payload = {
        "schema_version": _AUDIT_LOG_SCHEMA_VERSION,
        "event_kind": event_kind,
        "timestamp": timestamp if timestamp is not None else _now_iso(),
        "extraction_id": extraction_id,
        "stage": stage,
        "artefact_path": artefact_path,
        "estimate": estimate,
        "notes": notes,
    }
    entry_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    return entry_path


def list_entries(extraction_dir_: Path) -> list[Path]:
    """Return every audit-log entry path, sorted by counter."""
    audit_dir = audit_log_dir(extraction_dir_)
    if not audit_dir.exists():
        return []
    entries = [
        p for p in audit_dir.iterdir() if _FILENAME_RE.match(p.name)
    ]
    entries.sort(key=lambda p: int(_FILENAME_RE.match(p.name).group(1)))
    return entries
