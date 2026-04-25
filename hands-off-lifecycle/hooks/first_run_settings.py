"""Stanza-specific .claude/settings.json merge logic.

Per proposal Q5 and §6.2: pos-v2 wins only for the SessionStart stanza;
user-authored keys elsewhere are preserved. A pre-existing user-authored
SessionStart stanza is moved aside to a timestamped backup and the user
is notified in the confirmation sentence.

Stdlib only (json, pathlib, datetime, shutil). No external dependencies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SettingsMergeResult:
    """Outcome of a merge — carries the narrative the helper surfaces."""

    wrote: bool
    backup_path: Path | None = None
    prior_session_start_displaced: bool = False
    preserved_user_keys: tuple[str, ...] = field(default_factory=tuple)


def _now_utc_iso_for_filename() -> str:
    """UTC timestamp suitable for a filename (no ':')."""
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_existing(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Malformed — treat as empty and let the write overwrite (the
        # user's prior content is still on disk via git/backup; we do
        # not attempt to preserve invalid JSON).
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _iter_commands(stanza_entries: list[Any]) -> list[str]:
    """Return every command string reachable within a SessionStart stanza list.

    Accepts the current Claude Code hook envelope shape
    (``{matcher, hooks: [{type: command, command: ...}, ...]}``) and
    walks the inner ``hooks`` array. Returns an empty list when the
    shape is malformed so callers treat the stanza as non-pos-v2-owned.
    """
    commands: list[str] = []
    for entry in stanza_entries:
        if not isinstance(entry, dict):
            return []
        inner = entry.get("hooks")
        if not isinstance(inner, list):
            return []
        for cmd_entry in inner:
            if not isinstance(cmd_entry, dict):
                return []
            cmd = cmd_entry.get("command")
            if not isinstance(cmd, str):
                return []
            commands.append(cmd)
    return commands


def _is_pos_v2_owned(stanza_entries: list[Any]) -> bool:
    """Identify whether an existing SessionStart stanza is pos-v2's own.

    pos-v2's shipped stanza contains a command ending in
    ``first-run.sh`` or ``pos_session_start.py``. Anything else is
    treated as user-authored and backed up before replacement.
    """
    commands = _iter_commands(stanza_entries)
    if not commands:
        return False
    for cmd in commands:
        if "first-run.sh" not in cmd and "pos_session_start.py" not in cmd:
            return False
    return True


def build_first_run_stanza(pos_v2_root: Path) -> dict[str, Any]:
    """The SessionStart stanza Claude Code runs while first-run is live.

    Returns the full ``{matcher, hooks: [...]}`` envelope required by
    the current Claude Code hook schema. Absolute path; no env-var
    substitution at this point.
    """
    script = Path(pos_v2_root) / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    # timeout is in seconds per Claude Code hook docs. 60s is a generous
    # cap for the thin shim — the 2026-04-22 detachment amendment made
    # first-run.sh return in under a second by spawning a detached
    # worker. Pre-amendment callers had 120000 here, which at seconds is
    # ~33 hours; the 2026-04-22 pyyaml-reachability amendment (#5)
    # tightens the unit to be unambiguous and sets a realistic cap.
    return {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": str(script),
                "async": False,
                "timeout": 60,
            }
        ],
    }


def build_supervisor_stanza(pos_v2_root: Path) -> dict[str, Any]:
    """The SessionStart stanza Claude Code runs after first-run self-retires.

    Invokes pos_session_start.py directly with the shared venv's Python.
    Matches the sealed hook fragment's intent (venv-python + supervisor
    script) with a resolved absolute path. Returns the full
    ``{matcher, hooks: [...]}`` envelope required by the current
    Claude Code hook schema.
    """
    pos_v2_root = Path(pos_v2_root)
    python = pos_v2_root / ".venv" / "bin" / "python"
    script = pos_v2_root / "orchestrator" / "scripts" / "pos_session_start.py"
    # timeout is in seconds per Claude Code hook docs. The supervisor
    # itself finishes well under 5s; 20s is a generous cap. Pre-
    # amendment callers had 20000 here — ambiguous units — which the
    # 2026-04-22 pyyaml-reachability amendment (#5) tightens to the
    # documented seconds unit.
    return {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": f"{python} {script}",
                "async": False,
                "timeout": 20,
            }
        ],
    }


def merge_session_start(
    *,
    settings_path: Path,
    new_entry: dict[str, Any],
    now_iso: str | None = None,
    agent_handle: str | None = None,
) -> SettingsMergeResult:
    """Merge ``new_entry`` into settings.json's SessionStart stanza.

    Preserves:
      * all top-level keys other than ``hooks.SessionStart`` and the
        ``"agent"`` key (when ``agent_handle`` is provided)
      * all ``hooks.*`` keys other than ``SessionStart``
      * the top-level ``_comment`` field if present (documentation)

    Behaviour on the SessionStart stanza itself:
      * no prior stanza: write ``[new_entry]``.
      * prior stanza is pos-v2's own (command points at first-run.sh or
        pos_session_start.py): replace with ``[new_entry]``, no backup.
      * prior stanza is user-authored: write the whole prior settings.json
        to ``<settings_path>.user-backup-<timestamp>.json`` and replace
        the SessionStart stanza with ``[new_entry]``. The caller surfaces
        the displacement in the confirmation sentence.

    Top-level ``"agent": <agent_handle>`` merge (amendment #37,
    AC37.1):
      * When ``agent_handle`` is non-None, set
        ``existing["agent"] = agent_handle`` after the SessionStart
        merge so a fresh Claude Code session selects the workspace
        persona as its default subagent. Any pre-existing ``"agent"``
        value is overwritten — the workspace's resolved handle is the
        authoritative source. Other top-level keys remain untouched
        (the AC37.1 outcome is "agent merged, prior keys preserved").
      * When ``agent_handle`` is None, the ``"agent"`` field is left
        untouched — preserves backwards compatibility with every
        pre-amendment-#37 call site that did not pass the parameter.

    Writes atomically via a .tmp sibling and rename.
    """
    settings_path = Path(settings_path)
    existing = _load_existing(settings_path)

    backup_path: Path | None = None
    displaced = False

    hooks = existing.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        existing["hooks"] = hooks

    prior = hooks.get("SessionStart")
    if isinstance(prior, list) and prior and not _is_pos_v2_owned(prior):
        # User-authored; back up the whole file (preserves all user keys
        # inside one restorable artifact) and replace the stanza.
        ts = now_iso or _now_utc_iso_for_filename()
        backup_path = settings_path.with_name(
            f"{settings_path.name}.user-backup-{ts}.json"
        )
        backup_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        displaced = True

    hooks["SessionStart"] = [new_entry]
    existing["hooks"] = hooks

    # Amendment #37 (AC37.1): merge the top-level "agent" field when
    # the caller has resolved a handle. The merge is additive over a
    # pre-existing settings.json — every other top-level key remains
    # in place. When ``agent_handle`` is None this branch is skipped
    # entirely (backwards-compat for pre-amendment-#37 callers).
    if agent_handle is not None:
        existing["agent"] = agent_handle

    # Atomic write.
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings_path.with_suffix(settings_path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(settings_path)

    preserved_keys = tuple(
        k for k in existing.keys() if k not in ("hooks", "agent")
    ) + tuple(f"hooks.{k}" for k in hooks.keys() if k != "SessionStart")

    return SettingsMergeResult(
        wrote=True,
        backup_path=backup_path,
        prior_session_start_displaced=displaced,
        preserved_user_keys=preserved_keys,
    )
