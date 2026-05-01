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


# Set of substrings that mark a command as pos-v2-owned (per
# amendment #45's multi-contributor SessionStart shape). Any inner
# hook whose ``command`` contains one of these substrings is
# considered shipped by pos-v2 and does NOT trigger the user-stanza
# backup path. The set grows when a future amendment registers a
# new SessionStart contributor under hands-off-lifecycle's wiring.
_LOAM_COMMAND_MARKERS: tuple[str, ...] = (
    "first-run.sh",
    "pos_session_start.py",
    # Amendment #45 (sub-plan B): loam-mode SessionStart emitter
    # composed onto the shipped stanza by ``build_*_stanza`` when the
    # caller passes ``extra_inner_hooks``. Recognised here so a
    # re-run of merge_session_start over a stanza we wrote does not
    # treat the loam-mode inner hook as "user-authored".
    "loam_mode.cli session-start",
    "loam_mode.cli session_start",
    "-m loam_mode",
    # Amendment #46: primary-persona session-start emitter composed
    # onto the SessionStart envelope alongside loam-mode (probe →
    # persona → loam-mode ordering per umbrella plan §6 D5).
    # Recognised here so re-merge over a stanza we wrote does not
    # back up the persona inner hook as user-authored.
    "primary_persona.cli session-start",
    "primary_persona.cli session_start",
    "-m loam.primary_persona",
    # Structural-enforcement A1 substrate (AC.SE.4): the corpus-load
    # sentinel SessionStart inner hook composes onto the multi-
    # contributor envelope alongside loam-mode and primary-persona.
    # Path substring is the canonical marker (the script lives at
    # hands-off-lifecycle/hooks/corpus_load_session_start.py).
    "corpus_load_session_start.py",
    # Amendment 73 (AC.CI.7): the corpus-inlining SessionStart inner
    # hook composes onto the multi-contributor envelope alongside the
    # A1 corpus-load sentinel + loam-mode + primary-persona. Path
    # substring is the canonical marker (the script lives at
    # hands-off-lifecycle/hooks/corpus_inline_session_start.py).
    "corpus_inline_session_start.py",
)


# Set of substrings that mark a UserPromptSubmit inner hook as pos-v2-
# owned. Single-contributor for now (AC46.6 defers multi-contributor
# generalisation analogous to amendment #45's SessionStart registry).
# When a future amendment introduces additional UserPromptSubmit
# contributors, generalise this set + the merge function the same way
# amendment #45 generalised the SessionStart counterparts.
_LOAM_USER_PROMPT_SUBMIT_COMMAND_MARKERS: tuple[str, ...] = (
    "primary_persona.cli user-prompt-submit",
    "primary_persona.cli user_prompt_submit",
    "-m loam.primary_persona",
)


# Set of substrings that mark a Stop inner hook as pos-v2-owned.
# Single-contributor for now (amendment #48 plan §9 defers the multi-
# contributor Stop registry generalisation analogous to amendment
# #45's SessionStart registry). When a future amendment introduces
# additional Stop contributors, generalise this set + ``merge_stop``
# the same way.
_LOAM_STOP_COMMAND_MARKERS: tuple[str, ...] = (
    "primary_persona.cli stop",
    "-m loam.primary_persona",
)


# Set of substrings that mark a top-level ``statusLine`` value as
# pos-v2-owned. The renderer script's path is the canonical marker.
# Per amendment #49 plan §6 D-build.3.
_LOAM_STATUS_LINE_COMMAND_MARKERS: tuple[str, ...] = (
    "hands-off-lifecycle/hooks/statusline.py",
)


# Set of substrings that mark a PreToolUse inner hook as pos-v2-owned.
# Multi-contributor as of structural-enforcement A3 (extended by A4):
# A2's objective-binding gate, A3's TDD-guard, A4's Bash-guard, and
# A4's Agent-guard all ship under hooks.PreToolUse. A2 + A3 share the
# Edit|Write|MultiEdit matcher; A4_bash uses the Bash matcher; A4_task
# uses the Task matcher. Each matcher is independent — Claude Code
# fires only the inner hooks whose matcher value matches the tool
# name, so cross-matcher non-interference is a Claude Code primitive,
# not a property of this merge function.
_LOAM_PRE_TOOL_USE_COMMAND_MARKERS: tuple[str, ...] = (
    "objective_binding_gate.py",
    "tdd_guard.py",
    "bash_guard.py",
    "agent_guard.py",
    "dispatch_setup_hook.py",
)


def _is_pos_v2_owned(stanza_entries: list[Any]) -> bool:
    """Identify whether an existing SessionStart stanza is pos-v2's own.

    Pre-amendment-#45: pos-v2's shipped stanza contained a single
    inner-hook command ending in ``first-run.sh`` or
    ``pos_session_start.py``; the predicate required EVERY command
    to match.

    Amendment #45 (multi-contributor generalisation, AC.45.1 +
    AC.45.2 + AC.45.3): pos-v2 ships multi-inner-hook stanzas where
    additional contributors compose alongside the first-run /
    supervisor command. The predicate now treats a stanza as pos-v2-
    owned iff every inner-hook command matches one of the recognised
    pos-v2 command markers (``first-run.sh``, ``pos_session_start.py``,
    or the loam-mode session-start command). A wholly user-authored
    stanza or one that mixes user-authored and pos-v2 inner hooks is
    still treated as displaceable — backup behaviour is preserved.
    """
    commands = _iter_commands(stanza_entries)
    if not commands:
        return False
    for cmd in commands:
        if not any(marker in cmd for marker in _LOAM_COMMAND_MARKERS):
            return False
    return True


def _compose_inner_hooks(
    base_inner_hook: dict[str, Any],
    extra_inner_hooks: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Compose the outer envelope's ``hooks`` array.

    Amendment #45 (AC.45.2 + AC.45.3): when ``extra_inner_hooks`` is
    None or empty, the resulting list is ``[base_inner_hook]`` —
    byte-identical to the pre-amendment single-inner-hook shape. When
    non-empty, the extras are appended in caller-supplied order so
    Claude Code's SessionStart fan-out invokes the base command (the
    first-run shim or supervisor) BEFORE the additional contributors.
    """
    if not extra_inner_hooks:
        return [base_inner_hook]
    return [base_inner_hook, *extra_inner_hooks]


def build_first_run_stanza(
    loam_root: Path,
    *,
    extra_inner_hooks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """The SessionStart stanza Claude Code runs while first-run is live.

    Returns the full ``{matcher, hooks: [...]}`` envelope required by
    the current Claude Code hook schema. Absolute path; no env-var
    substitution at this point.

    Amendment #45 (AC.45.2): accepts an optional
    ``extra_inner_hooks`` list of additional inner-hook entries to
    compose into the outer envelope. When ``None`` or empty (the
    pre-amendment-#45 default), the envelope is byte-identical to the
    legacy single-inner-hook shape. When non-empty, the extra inner
    hooks are appended after the first-run shim entry; Claude Code's
    SessionStart fan-out invokes them all in order.
    """
    script = Path(loam_root) / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    # timeout is in seconds per Claude Code hook docs. 60s is a generous
    # cap for the thin shim — the 2026-04-22 detachment amendment made
    # first-run.sh return in under a second by spawning a detached
    # worker. Pre-amendment callers had 120000 here, which at seconds is
    # ~33 hours; the 2026-04-22 pyyaml-reachability amendment (#5)
    # tightens the unit to be unambiguous and sets a realistic cap.
    base_inner_hook: dict[str, Any] = {
        "type": "command",
        "command": str(script),
        "async": False,
        "timeout": 60,
    }
    return {
        "matcher": "",
        "hooks": _compose_inner_hooks(base_inner_hook, extra_inner_hooks),
    }


def build_supervisor_stanza(
    loam_root: Path,
    *,
    extra_inner_hooks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """The SessionStart stanza Claude Code runs after first-run self-retires.

    Invokes pos_session_start.py directly with the shared venv's Python.
    Matches the sealed hook fragment's intent (venv-python + supervisor
    script) with a resolved absolute path. Returns the full
    ``{matcher, hooks: [...]}`` envelope required by the current
    Claude Code hook schema.

    Amendment #45 (AC.45.3): accepts an optional
    ``extra_inner_hooks`` list of additional inner-hook entries to
    compose into the outer envelope. ``None`` or empty preserves the
    pre-amendment-#45 single-inner-hook shape (AC.45.5 backwards-
    compat); non-empty appends contributors after the supervisor
    entry.
    """
    loam_root = Path(loam_root)
    python = loam_root / ".venv" / "bin" / "python"
    script = loam_root / "framework" / "orchestrator" / "scripts" / "pos_session_start.py"
    # timeout is in seconds per Claude Code hook docs. The supervisor
    # itself finishes well under 5s; 20s is a generous cap. Pre-
    # amendment callers had 20000 here — ambiguous units — which the
    # 2026-04-22 pyyaml-reachability amendment (#5) tightens to the
    # documented seconds unit.
    base_inner_hook: dict[str, Any] = {
        "type": "command",
        "command": f"{python} {script}",
        "async": False,
        "timeout": 20,
    }
    return {
        "matcher": "",
        "hooks": _compose_inner_hooks(base_inner_hook, extra_inner_hooks),
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
      * prior stanza is pos-v2's own (command points at first-run.sh,
        pos_session_start.py, or loam-mode session-start — see the
        amendment #45 multi-contributor extension to ``_is_pos_v2_owned``):
        replace with ``[new_entry]``, no backup.
      * prior stanza is user-authored: write the whole prior settings.json
        to ``<settings_path>.user-backup-<timestamp>.json`` and replace
        the SessionStart stanza with ``[new_entry]``. The caller surfaces
        the displacement in the confirmation sentence.

    Amendment #45 (multi-contributor generalisation, AC.45.1): the
    ``new_entry`` envelope ``{"matcher": ..., "hooks": [...]}`` may
    carry one OR many inner-hook entries. The function composes the
    OUTER SessionStart list as ``[new_entry]`` exactly as before; the
    composition of the inner-hook list is done by
    ``build_first_run_stanza`` / ``build_supervisor_stanza`` via
    their ``extra_inner_hooks`` parameter. Zero-or-one contributor
    produces output byte-identical to pre-amendment-#45 (AC.45.5
    backwards-compat).

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


# ---- amendment #46 — UserPromptSubmit hook merge --------------------


def _is_pos_v2_owned_user_prompt_submit(stanza_entries: list[Any]) -> bool:
    """Identify whether an existing UserPromptSubmit stanza is pos-v2's.

    AC46.5 + AC46.6: the persona's user-prompt-submit subcommand is
    the canonical pos-v2-owned UserPromptSubmit inner hook. A stanza
    whose every inner-hook command matches one of the recognised
    persona-side command markers is pos-v2-owned and may be replaced
    without a user-stanza backup. Any other shape (user-authored, mixed,
    malformed) triggers the backup path mirroring the SessionStart
    convention.
    """
    commands = _iter_commands(stanza_entries)
    if not commands:
        return False
    for cmd in commands:
        if not any(
            marker in cmd
            for marker in _LOAM_USER_PROMPT_SUBMIT_COMMAND_MARKERS
        ):
            return False
    return True


def merge_user_prompt_submit(
    *,
    settings_path: Path,
    new_entry: dict[str, Any],
    now_iso: str | None = None,
) -> SettingsMergeResult:
    """Merge ``new_entry`` into settings.json's UserPromptSubmit stanza.

    AC46.5: writes ``hooks.UserPromptSubmit = [new_entry]``. Single-
    contributor (AC46.6) — multi-contributor generalisation is a
    future amendment analogous to #45's SessionStart registry.

    Behaviour mirrors ``merge_session_start``:
      * no prior stanza: write ``[new_entry]``.
      * prior stanza is pos-v2's own (command matches the persona's
        user-prompt-submit markers): replace with ``[new_entry]``,
        no backup.
      * prior stanza is user-authored: write the whole prior
        settings.json to a timestamped backup and replace the
        UserPromptSubmit stanza with ``[new_entry]``.

    Other top-level keys (including ``hooks.SessionStart``,
    ``hooks.<other>``, ``agent``, etc.) are preserved unchanged.
    Atomic write via ``.tmp`` sibling + rename.
    """
    settings_path = Path(settings_path)
    existing = _load_existing(settings_path)

    backup_path: Path | None = None
    displaced = False

    hooks = existing.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        existing["hooks"] = hooks

    prior = hooks.get("UserPromptSubmit")
    if (
        isinstance(prior, list)
        and prior
        and not _is_pos_v2_owned_user_prompt_submit(prior)
    ):
        ts = now_iso or _now_utc_iso_for_filename()
        backup_path = settings_path.with_name(
            f"{settings_path.name}.user-backup-{ts}.json"
        )
        backup_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        displaced = True

    hooks["UserPromptSubmit"] = [new_entry]
    existing["hooks"] = hooks

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings_path.with_suffix(settings_path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(settings_path)

    preserved_keys = tuple(
        k for k in existing.keys() if k not in ("hooks", "agent")
    ) + tuple(
        f"hooks.{k}" for k in hooks.keys() if k != "UserPromptSubmit"
    )

    return SettingsMergeResult(
        wrote=True,
        backup_path=backup_path,
        prior_session_start_displaced=displaced,
        preserved_user_keys=preserved_keys,
    )


# ---- amendment #48 — Stop hook merge --------------------------------


def _is_pos_v2_owned_stop(stanza_entries: list[Any]) -> bool:
    """Identify whether an existing Stop stanza is pos-v2's own.

    AC.M.11: the persona's ``stop`` subcommand is the canonical
    pos-v2-owned Stop inner hook. A stanza whose every inner-hook
    command matches one of the recognised persona-side command
    markers is pos-v2-owned and may be replaced without a user-
    stanza backup. Any other shape (user-authored, mixed,
    malformed) triggers the backup path mirroring the SessionStart
    + UserPromptSubmit conventions.
    """
    commands = _iter_commands(stanza_entries)
    if not commands:
        return False
    for cmd in commands:
        if not any(
            marker in cmd
            for marker in _LOAM_STOP_COMMAND_MARKERS
        ):
            return False
    return True


def merge_stop(
    *,
    settings_path: Path,
    new_entry: dict[str, Any],
    now_iso: str | None = None,
) -> SettingsMergeResult:
    """Merge ``new_entry`` into settings.json's Stop stanza.

    AC.M.11: writes ``hooks.Stop = [new_entry]``. Single-contributor
    — multi-contributor generalisation deferred (plan §9).

    Behaviour mirrors ``merge_session_start`` /
    ``merge_user_prompt_submit``:
      * no prior stanza: write ``[new_entry]``.
      * prior stanza is pos-v2's own (command matches the persona's
        stop markers): replace with ``[new_entry]``, no backup.
      * prior stanza is user-authored: write the whole prior
        settings.json to a timestamped backup and replace the Stop
        stanza with ``[new_entry]``.

    Other top-level keys (``hooks.SessionStart``,
    ``hooks.UserPromptSubmit``, ``hooks.<other>``, ``agent``, etc.)
    are preserved unchanged. Atomic write via ``.tmp`` sibling +
    rename.
    """
    settings_path = Path(settings_path)
    existing = _load_existing(settings_path)

    backup_path: Path | None = None
    displaced = False

    hooks = existing.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        existing["hooks"] = hooks

    prior = hooks.get("Stop")
    if (
        isinstance(prior, list)
        and prior
        and not _is_pos_v2_owned_stop(prior)
    ):
        ts = now_iso or _now_utc_iso_for_filename()
        backup_path = settings_path.with_name(
            f"{settings_path.name}.user-backup-{ts}.json"
        )
        backup_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        displaced = True

    hooks["Stop"] = [new_entry]
    existing["hooks"] = hooks

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings_path.with_suffix(settings_path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(settings_path)

    preserved_keys = tuple(
        k for k in existing.keys() if k not in ("hooks", "agent")
    ) + tuple(
        f"hooks.{k}" for k in hooks.keys() if k != "Stop"
    )

    return SettingsMergeResult(
        wrote=True,
        backup_path=backup_path,
        prior_session_start_displaced=displaced,
        preserved_user_keys=preserved_keys,
    )


# ---- structural-enforcement A2 — PreToolUse hook merge --------------


def _is_pos_v2_owned_pre_tool_use(stanza_entries: list[Any]) -> bool:
    """Identify whether an existing PreToolUse stanza is pos-v2's.

    AC.OBG.7 / merge contract: a stanza whose every inner-hook command
    matches one of the recognised pos-v2 PreToolUse command markers is
    pos-v2-owned and may be replaced without a user-stanza backup.
    Any other shape (user-authored, mixed, malformed) triggers the
    backup path mirroring the SessionStart / UserPromptSubmit / Stop
    conventions exactly.
    """
    commands = _iter_commands(stanza_entries)
    if not commands:
        return False
    for cmd in commands:
        if not any(
            marker in cmd
            for marker in _LOAM_PRE_TOOL_USE_COMMAND_MARKERS
        ):
            return False
    return True


def merge_pre_tool_use(
    *,
    settings_path: Path,
    new_entry: dict[str, Any] | None = None,
    new_entries: list[dict[str, Any]] | None = None,
    now_iso: str | None = None,
) -> SettingsMergeResult:
    """Merge PreToolUse stanza(s) into settings.json.

    Multi-contributor as of structural-enforcement A3 (D-build.6):

      * pass ``new_entry=<stanza>`` for the single-contributor case
        (legacy A2 call shape). Output is byte-identical to pre-A3:
        the OUTER ``hooks.PreToolUse`` list becomes ``[new_entry]``.
      * pass ``new_entries=[stanza1, stanza2, ...]`` for multi-
        contributor cases (A2 + A3). The OUTER list becomes the
        supplied list in caller order.
      * passing both is permitted but ``new_entries`` wins (the
        single-contributor argument is treated as a backwards-compat
        convenience).
      * passing neither raises ``ValueError``.

    Behaviour on the existing stanza:

      * no prior stanza: write the supplied list.
      * prior stanza is pos-v2's own (every inner-hook command matches
        one of the recognised pos-v2 PreToolUse markers — A2 only,
        A2 + A3, or any subset): replace, no backup.
      * prior stanza is user-authored: write the whole prior
        settings.json to a timestamped backup and replace.

    Other top-level keys (``hooks.SessionStart``, ``hooks.<other>``,
    ``agent``, ``statusLine``, etc.) are preserved unchanged.
    Atomic write via ``.tmp`` sibling + rename.
    """
    if new_entries is None:
        if new_entry is None:
            raise ValueError(
                "merge_pre_tool_use requires either new_entry= or "
                "new_entries=; both were None"
            )
        outer_list: list[dict[str, Any]] = [new_entry]
    else:
        outer_list = list(new_entries)

    settings_path = Path(settings_path)
    existing = _load_existing(settings_path)

    backup_path: Path | None = None
    displaced = False

    hooks = existing.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        existing["hooks"] = hooks

    prior = hooks.get("PreToolUse")
    if (
        isinstance(prior, list)
        and prior
        and not _is_pos_v2_owned_pre_tool_use(prior)
    ):
        ts = now_iso or _now_utc_iso_for_filename()
        backup_path = settings_path.with_name(
            f"{settings_path.name}.user-backup-{ts}.json"
        )
        backup_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        displaced = True

    hooks["PreToolUse"] = outer_list
    existing["hooks"] = hooks

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings_path.with_suffix(settings_path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(settings_path)

    preserved_keys = tuple(
        k for k in existing.keys() if k not in ("hooks", "agent")
    ) + tuple(
        f"hooks.{k}" for k in hooks.keys() if k != "PreToolUse"
    )

    return SettingsMergeResult(
        wrote=True,
        backup_path=backup_path,
        prior_session_start_displaced=displaced,
        preserved_user_keys=preserved_keys,
    )


# ---- amendment #49 — top-level ``statusLine`` merge -----------------


def _is_pos_v2_owned_status_line(entry: Any) -> bool:
    """Identify whether an existing ``statusLine`` value is pos-v2's own.

    AC.SL.7: the top-level ``statusLine`` field is a single mapping
    (not a list of stanzas like ``hooks.<event>``). The pos-v2-owned
    shape carries a ``command`` substring naming the renderer script
    by path. Any other shape (user-authored, malformed, missing
    ``command``) is treated as user-authored and triggers the backup
    path.
    """
    if not isinstance(entry, dict):
        return False
    cmd = entry.get("command")
    if not isinstance(cmd, str):
        return False
    return any(
        marker in cmd for marker in _LOAM_STATUS_LINE_COMMAND_MARKERS
    )


def merge_status_line(
    *,
    settings_path: Path,
    new_entry: dict[str, Any],
    now_iso: str | None = None,
) -> SettingsMergeResult:
    """Merge ``new_entry`` into settings.json's top-level ``statusLine``.

    AC.SL.6: writes ``statusLine = new_entry`` at the top level (NOT
    under ``hooks.*``; Claude Code's status-line schema lives at the
    top level). AC.SL.7: backs up the entire prior ``settings.json``
    to a timestamped sibling when the prior ``statusLine`` is user-
    authored, mirroring the SessionStart / UserPromptSubmit / Stop
    backup convention exactly.

    Behaviour:
      * no prior ``statusLine``: write ``new_entry``.
      * prior is pos-v2's own (renderer-script command marker
        present): replace with ``new_entry``, no backup.
      * prior is user-authored: write the entire prior
        ``settings.json`` to a timestamped backup and replace the
        ``statusLine`` value with ``new_entry``.

    Other top-level keys (``hooks.SessionStart``,
    ``hooks.UserPromptSubmit``, ``hooks.Stop``, ``hooks.<other>``,
    ``agent``, ``_comment``, etc.) are preserved unchanged. Atomic
    write via ``.tmp`` sibling + rename.
    """
    settings_path = Path(settings_path)
    existing = _load_existing(settings_path)

    backup_path: Path | None = None
    displaced = False

    prior = existing.get("statusLine")
    if prior is not None and not _is_pos_v2_owned_status_line(prior):
        ts = now_iso or _now_utc_iso_for_filename()
        backup_path = settings_path.with_name(
            f"{settings_path.name}.user-backup-{ts}.json"
        )
        backup_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        displaced = True

    existing["statusLine"] = new_entry

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings_path.with_suffix(settings_path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(settings_path)

    hooks_existing = existing.get("hooks") if isinstance(
        existing.get("hooks"), dict
    ) else {}
    preserved_keys = tuple(
        k for k in existing.keys()
        if k not in ("hooks", "agent", "statusLine")
    ) + tuple(f"hooks.{k}" for k in hooks_existing.keys())

    return SettingsMergeResult(
        wrote=True,
        backup_path=backup_path,
        prior_session_start_displaced=displaced,
        preserved_user_keys=preserved_keys,
    )
