"""Stop-hook turn-close emitter (amendment #48 / D2 / D3 / D4 / D7 / D8 / D11).

The Stop hook is Claude Code's once-per-turn-close trigger. This
module is the persona-side handler:

  - :func:`cli_stop` reads Claude Code's Stop envelope from stdin,
    recovers the user message + assistant reply from the envelope's
    ``transcript_path``, derives a stable per-turn id, deduplicates
    on a workspace-local marker, and detaches the actual
    ``add_episode`` write to a background subprocess.
    Returns 0 unconditionally (AC.M.4 + AC.M.7 — a non-zero exit
    blocks Claude Code's normal stop behaviour, the OPPOSITE of
    what we want).

  - :func:`cli_memory_write` is the detached subprocess's entry
    point. It constructs the live MCP client, drives one
    ``add_episode`` synchronously to completion, logs a structured
    diagnostic to ``<workspace>/.pos/memory-writes.log``, and
    returns 0. AC.M.6 + AC.M.10.

Per the locked plan §6:
  - D3: detachment via ``subprocess.Popen(..., start_new_session=True,
    stdin/stdout/stderr=DEVNULL)`` from inside ``cli_stop``. Tests
    monkeypatch the Popen call site to assert detachment shape.
  - D4: turn id = ``f"{session_id}:{user_message_sha256[:12]}"``;
    idempotency via ``<workspace>/.pos/last-turn-id``.
  - D7: detached child catches connection failure, logs, exits.
  - D8: diagnostic log at ``<workspace>/.pos/memory-writes.log``;
    NDJSON.
  - D11: ``/compact`` and ESC interrupt produce empty user_message
    or empty assistant_reply; both are graceful no-ops (AC.M.9).

Per ODD §2.5 every code path traces back to AC.M.4–AC.M.10. Defensive
``if``s without an AC anchor are not introduced.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---- public dataclasses + parsing -----------------------------------


@dataclass
class StopEnvelope:
    """Decoded Claude Code Stop envelope (AC.M.4 / AC.M.5)."""

    session_id: str
    transcript_path: str
    cwd: str | None
    stop_hook_active: bool


@dataclass
class TurnContent:
    """Content recovered from the Stop envelope's transcript_path
    (AC.M.5). When either field is empty, the AC.M.9 graceful-no-op
    branch fires upstream.
    """

    user_message: str
    assistant_reply: str
    turn_id: str


def parse_stop_envelope(raw: str) -> StopEnvelope | None:
    """Parse a Stop envelope JSON blob.

    AC.M.4: returns ``None`` on every malformed-stdin path
    (empty / non-JSON / non-dict / missing required field). The
    caller's fail-soft contract maps ``None`` to a no-op exit-0.
    """
    if not raw or not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    session_id = data.get("session_id")
    transcript_path = data.get("transcript_path")
    if not isinstance(session_id, str) or not session_id:
        return None
    if not isinstance(transcript_path, str) or not transcript_path:
        return None
    cwd_value = data.get("cwd")
    cwd = cwd_value if isinstance(cwd_value, str) else None
    stop_hook_active = bool(data.get("stop_hook_active", False))
    return StopEnvelope(
        session_id=session_id,
        transcript_path=transcript_path,
        cwd=cwd,
        stop_hook_active=stop_hook_active,
    )


# ---- transcript walk (AC.M.5 / AC.M.9 / D11) ------------------------


def _walk_transcript_for_turn(
    transcript_path: Path,
) -> tuple[str, str]:
    """Return ``(user_message, assistant_reply)`` from the transcript.

    Walks the JSONL backwards (newest first) and returns the most
    recent assistant reply paired with the most recent user message
    that precedes it. Per Claude Code's transcript shape (research
    §): each line is a JSON object carrying a ``message`` field
    whose ``role`` is ``user`` or ``assistant`` and whose
    ``content`` is a string OR a list of typed parts.

    AC.M.9: returns ``("", "")`` on every unrecoverable shape —
    file missing, unreadable, malformed JSONL, no user message,
    no assistant reply, empty content. D11 absorbs ``/compact``
    and ESC-interrupt shapes via this same branch.
    """
    try:
        lines = transcript_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return ("", "")

    # Walk backwards: pick the latest assistant, then the latest user
    # whose index is strictly before that assistant.
    assistant_idx: int | None = None
    assistant_text = ""
    for i in range(len(lines) - 1, -1, -1):
        ln = lines[i].strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except (ValueError, TypeError):
            continue
        if not isinstance(obj, dict):
            continue
        role, text = _extract_role_and_text(obj)
        if role == "assistant" and text:
            assistant_idx = i
            assistant_text = text
            break

    if assistant_idx is None:
        return ("", "")

    user_text = ""
    for i in range(assistant_idx - 1, -1, -1):
        ln = lines[i].strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except (ValueError, TypeError):
            continue
        if not isinstance(obj, dict):
            continue
        role, text = _extract_role_and_text(obj)
        if role == "user" and text:
            user_text = text
            break

    return (user_text, assistant_text)


def _extract_role_and_text(obj: dict[str, Any]) -> tuple[str, str]:
    """Pull ``(role, text)`` from a transcript line dict.

    Tolerates two common shapes per Claude Code transcript JSONL:

      1. ``{"type": "user"|"assistant", "message": {...}}`` — the
         shape current Claude Code emits.
      2. ``{"role": "user"|"assistant", "content": ...}`` — the
         flatter shape some transcript variants carry.

    Returns ``("", "")`` on unrecognised shape; the caller skips.
    """
    # Shape 1: nested under ``message``.
    msg = obj.get("message")
    if isinstance(msg, dict):
        role_value = msg.get("role")
        content = msg.get("content")
        if isinstance(role_value, str):
            return (role_value, _extract_content_text(content))

    # Shape 2: flat.
    role_value = obj.get("role")
    if isinstance(role_value, str):
        content = obj.get("content")
        return (role_value, _extract_content_text(content))

    # Top-level "type" sometimes carries the role flag too.
    type_value = obj.get("type")
    if isinstance(type_value, str) and type_value in ("user", "assistant"):
        content = obj.get("content")
        return (type_value, _extract_content_text(content))

    return ("", "")


def _extract_content_text(content: Any) -> str:
    """Render a transcript ``content`` field as a single text blob.

    Claude Code's transcripts encode content as either a plain
    string or a list of typed parts. Tool-use / tool-result parts
    are excluded — only ``text`` parts contribute to the recovered
    message. Empty result is an explicit AC.M.9 / D11 trigger.
    """
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        chunks: list[str] = []
        for part in content:
            if isinstance(part, dict):
                ptype = part.get("type")
                ptext = part.get("text")
                if ptype == "text" and isinstance(ptext, str):
                    chunks.append(ptext)
        return "\n".join(c.strip() for c in chunks if c.strip()).strip()
    return ""


# ---- turn-id derivation + dedupe (D4 / AC.M.8) ----------------------


def derive_turn_id(*, session_id: str, user_message: str) -> str:
    """Compute the stable per-turn id used for dedupe (D4).

    Hash of the user message keeps the id stable across
    ``/compact`` and ESC-interrupt re-fires (the reply may differ
    or be empty on re-fire, but the user message is invariant for
    a given turn).
    """
    digest = hashlib.sha256(user_message.encode("utf-8")).hexdigest()
    return f"{session_id}:{digest[:12]}"


def _last_turn_id_path(workspace_root: Path) -> Path:
    """Workspace-local marker file (D4)."""
    return Path(workspace_root) / ".pos" / "last-turn-id"


def _read_last_turn_id(workspace_root: Path) -> str:
    path = _last_turn_id_path(workspace_root)
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return ""


def _write_last_turn_id(workspace_root: Path, turn_id: str) -> None:
    path = _last_turn_id_path(workspace_root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic via tmp+rename so an interrupted write does not
        # corrupt the marker.
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(turn_id + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        # Best-effort. Failure to write the marker is non-fatal —
        # AC.M.8's dedupe degrades to "double-write may occur once",
        # which the diagnostic log surfaces. Keeping the Stop hook
        # exit-0 + fast is more important than guaranteed dedupe.
        pass


# ---- diagnostic log (D8 / AC.M.10) ----------------------------------


def _diag_log_path(workspace_root: Path) -> Path:
    """Workspace-local NDJSON diagnostic log (D8).

    One line per write attempt (success or failure). Outside any
    sealed-component source tree (lives under ``<workspace>/.pos/``,
    by convention since amendment #28).
    """
    return Path(workspace_root) / ".pos" / "memory-writes.log"


def _append_diag(workspace_root: Path, entry: dict[str, Any]) -> None:
    """Append one NDJSON entry to the diagnostic log (D8).

    Best-effort; failure to log is silent — the alternative would be
    a tracebacks-on-stderr that bleeds into Claude Code's debug log.
    """
    try:
        log_path = _diag_log_path(workspace_root)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        return


# ---- background-write detachment (D3 / AC.M.7) ----------------------


def _spawn_memory_write(
    *,
    workspace_root: Path,
    turn_id: str,
    session_id: str,
    user_message: str,
    assistant_reply: str,
) -> None:
    """Detach a background subprocess driving ``cli_memory_write``.

    D3: ``Popen(..., start_new_session=True, stdin=DEVNULL,
    stdout=DEVNULL, stderr=DEVNULL)`` produces a child detached
    from the Stop subprocess; the child outlives the Stop hook
    even when the Stop subprocess returns immediately. The child
    invokes the persona CLI's ``memory-write`` subcommand with the
    recovered turn content as argv.

    The Python interpreter is resolved as ``sys.executable`` so the
    child runs under the same venv this Stop subprocess does — the
    venv has the ``mcp`` runtime dep declared by amendment #48.
    """
    # ``-Xfrozen_modules=off`` is not needed; the persona CLI is a
    # standard package import.
    cmd = [
        sys.executable,
        "-m",
        "primary_persona.cli",
        "memory-write",
        "--workspace",
        str(workspace_root),
        "--turn-id",
        turn_id,
        "--session-id",
        session_id,
        "--user-message",
        user_message,
        "--assistant-reply",
        assistant_reply,
    ]
    subprocess.Popen(  # noqa: S603 — intentional detached child
        cmd,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )


# ---- envelope handling (AC.M.4 / AC.M.5 / AC.M.7 / AC.M.8 / AC.M.9) -


def handle_stop_envelope(
    envelope: StopEnvelope,
    workspace_root: Path,
) -> None:
    """Drive the recover → dedupe → detach pipeline for one Stop firing.

    AC.M.5 + AC.M.9: recover content from the transcript; if either
    half is empty, log "skipped:<reason>" and return.

    AC.M.8: read the last-turn-id marker; if equal, log
    "skipped:duplicate" and return.

    AC.M.7: write the new last-turn-id BEFORE detaching the child,
    then ``Popen(..., start_new_session=True, ...)``. The Stop
    subprocess returns in milliseconds; the child carries the
    long-running ``add_episode`` work.
    """
    user_message, assistant_reply = _walk_transcript_for_turn(
        Path(envelope.transcript_path)
    )
    if not user_message:
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "stop-skip",
                "reason": "no-user-message",
                "session_id": envelope.session_id,
            },
        )
        return
    if not assistant_reply:
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "stop-skip",
                "reason": "no-assistant-reply",
                "session_id": envelope.session_id,
            },
        )
        return
    turn_id = derive_turn_id(
        session_id=envelope.session_id, user_message=user_message
    )
    if _read_last_turn_id(workspace_root) == turn_id:
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "stop-skip",
                "reason": "duplicate",
                "turn_id": turn_id,
            },
        )
        return
    _write_last_turn_id(workspace_root, turn_id)
    _spawn_memory_write(
        workspace_root=workspace_root,
        turn_id=turn_id,
        session_id=envelope.session_id,
        user_message=user_message,
        assistant_reply=assistant_reply,
    )


def cli_stop(workspace_root: Path | None = None) -> int:
    """Read a Stop envelope from stdin and dispatch the turn-close.

    AC.M.4 + AC.M.7: returns 0 unconditionally and returns fast (the
    actual ``add_episode`` work is detached). Every internal
    exception is caught — a Stop hook that exits non-zero blocks
    Claude Code's normal stop behaviour (per Stop-hook contract).

    Plan §7 constraint 12: stdout is debug-log-only per Claude Code
    docs; the Stop subprocess writes nothing visible to the model.
    We do not print on success.
    """
    root = workspace_root if workspace_root is not None else Path.cwd()
    raw = ""
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — AC.M.4 fail-soft
        raw = ""
    envelope = parse_stop_envelope(raw)
    if envelope is None:
        return 0
    try:
        handle_stop_envelope(envelope, Path(root))
    except Exception:  # noqa: BLE001 — AC.M.4 fail-soft
        # Catch every internal exception; nothing reaches stderr.
        # AC.M.10's diagnostic surface is the workspace-local log,
        # not Claude Code's debug log.
        try:
            _append_diag(
                Path(root),
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "kind": "stop-error",
                    "session_id": envelope.session_id,
                },
            )
        except Exception:  # noqa: BLE001
            pass
    return 0


# ---- detached-child entry point (D3 / AC.M.6 / AC.M.10) -------------


def cli_memory_write(
    *,
    workspace_root: Path,
    turn_id: str,
    session_id: str,
    user_message: str,
    assistant_reply: str,
) -> int:
    """Drive one ``add_episode`` write synchronously.

    AC.M.6: when the live MCP client constructs successfully, this
    function performs exactly one ``add_episode`` call against the
    memory-graphiti service. The episode body contains both the user
    message and the assistant reply; ``group_id`` equals the
    workspace slug.

    AC.M.10: every failure path — live client unavailable, MCP
    transport failure, exception inside ``add_episode`` — is caught,
    logged to ``<workspace>/.pos/memory-writes.log`` as a structured
    diagnostic, and the function returns 0. The detached subprocess
    exits cleanly.

    The detached child carries no real-time pressure (the Stop
    subprocess has long since returned). We drive the async write
    via ``asyncio.run`` from the synchronous entry point.
    """
    workspace_root = Path(workspace_root)
    try:
        from .mcp_memory_client import (  # noqa: WPS433
            build_live_mcp_memory_client,
        )
    except Exception as exc:  # noqa: BLE001
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "write-error",
                "stage": "import",
                "turn_id": turn_id,
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
        return 0

    client = build_live_mcp_memory_client(workspace_root)
    if client is None:
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "write-skip",
                "reason": "no-live-client",
                "turn_id": turn_id,
            },
        )
        return 0

    try:
        from .memory_consumer import (  # noqa: WPS433
            TurnAggregator,
            resolve_workspace_slug,
        )
    except Exception as exc:  # noqa: BLE001
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "write-error",
                "stage": "import-consumer",
                "turn_id": turn_id,
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
        return 0

    try:
        slug = resolve_workspace_slug(workspace_root)
    except Exception as exc:  # noqa: BLE001
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "write-error",
                "stage": "slug",
                "turn_id": turn_id,
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
        return 0

    async def _drive() -> dict[str, Any]:
        aggregator = TurnAggregator(
            memory_client=client,
            workspace_slug=slug,
        )
        task = aggregator.close_turn(
            turn_id=turn_id,
            user_message=user_message,
            persona_reply=assistant_reply,
        )
        # ``close_turn`` returned an asyncio.Task on the running loop;
        # await it here in the detached child to ensure the write
        # actually completes before the process exits. AC.M.6 measures
        # the observable count: exactly one add_episode call.
        return await task

    try:
        result = asyncio.run(_drive())
    except Exception as exc:  # noqa: BLE001 — AC.M.10 fail-soft
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "write-error",
                "stage": "add_episode",
                "turn_id": turn_id,
                "session_id": session_id,
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
        return 0

    _append_diag(
        workspace_root,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": "write-ok",
            "turn_id": turn_id,
            "session_id": session_id,
            "episode_uuid": (
                result.get("episode_uuid")
                if isinstance(result, dict)
                else None
            ),
        },
    )
    return 0
