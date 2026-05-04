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

"""PM workspace-state loader + atomic-write helpers.

Per cycle-2 plan §4 Surface #5 + Surface #7:

  - :func:`workspace_state_dir_for` — resolves
    ``<workspace>/workspace/.loam/pms/<handle>/`` via the canonical
    ``WORKSPACE_STATE_SUBDIR`` helper from workspace-bootstrap.
  - :func:`load_contract` — reads + validates ``contract.yaml``.
    Raises :class:`PMNotFoundError` when absent;
    :class:`PMStateCorruptedError` on schema mismatch.
  - :func:`load_state_yaml` — reads + validates ``state.yaml``.
    Returns a dict (Cycle 2 minimal shape); raises
    :class:`PMStateCorruptedError` on schema mismatch.
  - :func:`load_decision_queue` — reads + validates ``decision-queue.yaml``.
    Returns the list of queue entries.
  - :func:`atomic_write_yaml` — tmp+rename atomic write helper.

Per AC.PPM.4. Schema_version 1 is the only accepted version at Cycle 2;
any other value raises :class:`PMStateCorruptedError` for forward-compat
(future schema bumps register a migrator + bump the accepted version).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from loam.per_project_pm.contract import PMContract
from loam.per_project_pm.errors import (
    PMNotFoundError,
    PMStateCorruptedError,
)


# Cycle 2 only accepts schema_version=1. Future versions register
# migrators (out of scope for Cycle 2).
ACCEPTED_SCHEMA_VERSION = 1


def workspace_state_dir_for(workspace_root: Path | str, pm_name: str) -> Path:
    """Resolve ``<workspace>/workspace/.loam/pms/<pm_name>/``.

    Routes through ``loam.workspace_bootstrap.workspace_paths.workspace_state_dir``
    so the HC#6 structural guard (refuse workspace_root basename
    'framework') applies. Per cycle-2 plan §4 F2.A + Surface #2.

    The directory is NOT created here — the loader is read-only;
    creation happens lazily in :class:`PMRuntime.enqueue_decision` /
    :class:`PMRuntime.surface_next_question`.
    """
    # Lazy import keeps the dependency direction one-way: per-project-pm
    # depends on workspace-bootstrap; workspace-bootstrap doesn't know
    # about per-project-pm.
    from loam.workspace_bootstrap.workspace_paths import workspace_state_dir

    if not pm_name:
        raise ValueError("pm_name must be a non-empty string")
    return workspace_state_dir(workspace_root) / ".loam" / "pms" / pm_name


def load_contract(pm_dir: Path) -> PMContract:
    """Load + validate ``<pm_dir>/contract.yaml``.

    Per AC.PPM.4:

      - Raises :class:`PMNotFoundError` when ``contract.yaml`` is
        absent (PM not authored yet).
      - Raises :class:`PMStateCorruptedError` on:
          * malformed YAML,
          * missing required field (Pydantic ValidationError),
          * invalid ``project_kind`` / non-absolute ``workspace_root``
            / any other Pydantic validation failure,
          * unexpected ``schema_version``.
    """
    contract_path = pm_dir / "contract.yaml"
    if not contract_path.exists():
        raise PMNotFoundError(
            f"PM contract.yaml not found at {contract_path!s}. "
            "The PM has not been authored yet."
        )

    raw_text = contract_path.read_text(encoding="utf-8")
    try:
        raw = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise PMStateCorruptedError(
            f"contract.yaml at {contract_path!s} is not valid YAML: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise PMStateCorruptedError(
            f"contract.yaml at {contract_path!s} must be a mapping at "
            f"top level; got: {type(raw).__name__}"
        )

    schema_version = raw.pop("schema_version", None)
    if schema_version != ACCEPTED_SCHEMA_VERSION:
        raise PMStateCorruptedError(
            f"contract.yaml at {contract_path!s} has "
            f"schema_version={schema_version!r}; expected "
            f"{ACCEPTED_SCHEMA_VERSION}."
        )

    try:
        return PMContract.model_validate(raw)
    except ValidationError as exc:
        raise PMStateCorruptedError(
            f"contract.yaml at {contract_path!s} failed validation: {exc}"
        ) from exc


def load_state_yaml(pm_dir: Path) -> dict[str, Any]:
    """Load + minimally validate ``<pm_dir>/state.yaml``.

    Returns a dict with keys: ``in_flight`` (list), ``last_surfaced_at``
    (str | None), ``notes`` (str). If the file is absent, returns the
    empty default (``in_flight=[]``, ``last_surfaced_at=None``,
    ``notes=""``) — state.yaml is optional at PM-creation; the runtime
    creates it lazily.

    Raises :class:`PMStateCorruptedError` on malformed YAML / missing
    schema_version / unexpected schema_version.
    """
    state_path = pm_dir / "state.yaml"
    if not state_path.exists():
        return {"in_flight": [], "last_surfaced_at": None, "notes": ""}

    try:
        raw = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PMStateCorruptedError(
            f"state.yaml at {state_path!s} is not valid YAML: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise PMStateCorruptedError(
            f"state.yaml at {state_path!s} must be a mapping at top "
            f"level; got: {type(raw).__name__}"
        )

    schema_version = raw.get("schema_version")
    if schema_version != ACCEPTED_SCHEMA_VERSION:
        raise PMStateCorruptedError(
            f"state.yaml at {state_path!s} has "
            f"schema_version={schema_version!r}; expected "
            f"{ACCEPTED_SCHEMA_VERSION}."
        )

    return {
        "in_flight": raw.get("in_flight") or [],
        "last_surfaced_at": raw.get("last_surfaced_at"),
        "notes": raw.get("notes") or "",
    }


def load_decision_queue(pm_dir: Path) -> list[dict[str, Any]]:
    """Load + minimally validate ``<pm_dir>/decision-queue.yaml``.

    Returns the list of queue entries. Each entry has keys ``text``
    (str, required), ``provenance`` (str | None), ``enqueued_at``
    (str, ISO 8601). If the file is absent, returns ``[]`` — no
    decisions queued is the empty default.

    Raises :class:`PMStateCorruptedError` on malformed YAML / missing
    schema_version / unexpected schema_version / queue entry missing
    required ``text`` field.
    """
    queue_path = pm_dir / "decision-queue.yaml"
    if not queue_path.exists():
        return []

    try:
        raw = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PMStateCorruptedError(
            f"decision-queue.yaml at {queue_path!s} is not valid YAML: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise PMStateCorruptedError(
            f"decision-queue.yaml at {queue_path!s} must be a mapping "
            f"at top level; got: {type(raw).__name__}"
        )

    schema_version = raw.get("schema_version")
    if schema_version != ACCEPTED_SCHEMA_VERSION:
        raise PMStateCorruptedError(
            f"decision-queue.yaml at {queue_path!s} has "
            f"schema_version={schema_version!r}; expected "
            f"{ACCEPTED_SCHEMA_VERSION}."
        )

    queue = raw.get("queue") or []
    if not isinstance(queue, list):
        raise PMStateCorruptedError(
            f"decision-queue.yaml at {queue_path!s} 'queue' field "
            f"must be a list; got: {type(queue).__name__}"
        )

    entries: list[dict[str, Any]] = []
    for idx, entry in enumerate(queue):
        if not isinstance(entry, dict):
            raise PMStateCorruptedError(
                f"decision-queue.yaml entry {idx} must be a mapping; "
                f"got: {type(entry).__name__}"
            )
        text = entry.get("text")
        if not isinstance(text, str) or not text:
            raise PMStateCorruptedError(
                f"decision-queue.yaml entry {idx} missing required "
                f"non-empty 'text' field"
            )
        entries.append(
            {
                "text": text,
                "provenance": entry.get("provenance"),
                "enqueued_at": entry.get("enqueued_at", ""),
            }
        )
    return entries


def atomic_write_yaml(path: Path, payload: dict[str, Any]) -> None:
    """Write ``payload`` to ``path`` atomically via tmp+rename.

    Mirrors the M-FBM atomic-write convention. The tmp file lives in
    the same directory as the target so ``rename`` is atomic on
    POSIX (Linux/macOS); cross-filesystem renames would fall back
    to a copy and lose atomicity. Per cycle-2 plan-doc §4 Surface #5
    "atomic write via tmp+rename".

    fsync is called on the tmp file before rename so a crash between
    rename and dirent flush doesn't leave the new contents partially
    written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(payload, fh, sort_keys=False, default_flow_style=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except Exception:
        # Cleanup on any error so we don't leak tmp files.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
