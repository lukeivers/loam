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

"""SOC-2 audit-log emitter for the onboarding ritual.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.11 + Decision P SOC-2 floor.
Schema mirrors the odd-extractor's ``observability.py`` shape from
v0.2.0 Cycle 1 (schema_version + event_kind + timestamp + notes +
artefact_path) so audit-log readers can compose across components.

Audit-log location: ``<workspace_root>/.loam/audit-log/onboarding-
<YYYY-MM-DD>.yaml`` per the plan-doc method-decision register.
Append-only YAML stream — each call writes one new entry document
delimited by ``---`` separator (so multi-event days remain a single
file).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml


_AUDIT_LOG_SCHEMA_VERSION = 1


# AC.ONBOARD.11 — event_kind enumeration. Closed set; new event-kinds
# require a plan-doc / AC update. Mirrors the odd-extractor's
# event-kind discipline from v0.2.0 Cycle 1.
EventKind = Literal[
    "onboarding_question_asked",
    "onboarding_response_recorded",
    "onboarding_capability_activated",
    "onboarding_default_flip",
    "onboarding_skipped",
    "onboarding_completed",
    "onboarding_started",
]


@dataclass(frozen=True)
class AuditEntry:
    """One audit-log entry. Returned by :func:`emit_audit_entry` so
    callers can carry the timestamp into the completion summary.
    """

    schema_version: int
    event_kind: str
    timestamp: str
    notes: str
    artefact_path: str | None


def audit_log_dir(workspace_root: Path) -> Path:
    """``<workspace_root>/.loam/audit-log/`` per AC.ONBOARD.11."""
    return workspace_root / ".loam" / "audit-log"


def audit_log_path(
    workspace_root: Path, *, today: str | None = None
) -> Path:
    """``<workspace_root>/.loam/audit-log/onboarding-<YYYY-MM-DD>.yaml``."""
    today_iso = today or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    return audit_log_dir(workspace_root) / f"onboarding-{today_iso}.yaml"


def emit_audit_entry(
    workspace_root: Path,
    *,
    event_kind: EventKind,
    notes: str = "",
    artefact_path: str | None = None,
    today: str | None = None,
    timestamp: str | None = None,
) -> AuditEntry:
    """Append one audit-log entry to today's onboarding log.

    Per AC.ONBOARD.11. The log is a multi-document YAML file (each
    entry is its own ``---``-delimited document) so concurrent
    appenders don't corrupt structure.
    """
    target = audit_log_path(workspace_root, today=today)
    target.parent.mkdir(parents=True, exist_ok=True)

    ts = timestamp or _dt.datetime.now(_dt.timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "schema_version": _AUDIT_LOG_SCHEMA_VERSION,
        "event_kind": event_kind,
        "timestamp": ts,
        "notes": notes,
        "artefact_path": artefact_path,
    }

    document = "---\n" + yaml.safe_dump(payload, sort_keys=False)
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        target.write_text(existing + document, encoding="utf-8")
    else:
        target.write_text(document, encoding="utf-8")

    return AuditEntry(
        schema_version=_AUDIT_LOG_SCHEMA_VERSION,
        event_kind=event_kind,
        timestamp=ts,
        notes=notes,
        artefact_path=artefact_path,
    )


def read_audit_entries(workspace_root: Path, *, today: str | None = None) -> list[dict[str, Any]]:
    """Read today's audit-log entries as a list of dicts.

    Returns empty list when the log file does not exist (fresh
    workspace pre-onboarding). Used by D2 idempotent-rerun detection
    + D3 mid-onboarding restart resume + per-AC tests.
    """
    target = audit_log_path(workspace_root, today=today)
    if not target.exists():
        return []
    text = target.read_text(encoding="utf-8")
    return [doc for doc in yaml.safe_load_all(text) if isinstance(doc, dict)]
