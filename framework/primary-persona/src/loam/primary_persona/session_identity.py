"""Shared channel-session identity resolver (per-session-resume-handoff, D1).

A single source of truth for "which channel-session am I?" used by BOTH the
write side (``stop_emitter._spawn_memory_write`` captures the key AT ENQUEUE,
where ``CLAUDE_PERSONA`` is live in the Stop hook's env) and the read side
(``active_thread`` / ``keep_pace.retrieval`` / ``session_start_emitter`` resolve
the SAME key to scope the episode filter).

D1 anchor: ``CLAUDE_PERSONA`` — exported into every hook process, channel-session
bound, restart-stable. ``CLAUDE_CODE_SESSION_ID`` is deliberately NOT used: it is
fresh per process and would break the very resume this fixes.

Resolution chain (D1): ``CLAUDE_PERSONA`` → ``DISCORD_STATE_DIR`` basename →
``None``. The D1 chain names ``workspace_slug`` as the ultimate fallback; here that
is expressed as ``None`` — a ``None`` key means "no channel-session dimension",
which the store surfaces treat as no filter, i.e. today's workspace-global
behavior (``group_id=workspace_slug`` already scopes to the workspace). Returning
``None`` rather than the literal slug is load-bearing for AC.PSR.5: a reader that
cannot resolve its OWN identity must degrade to workspace-global (see everything),
NOT filter by ``workspace_slug`` — the latter would starve a reader in a workspace
whose episodes are persona-tagged.
"""

from __future__ import annotations

import os
from collections.abc import Mapping


def resolve_session_key(
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Resolve THIS process's channel-session key, or ``None`` if none.

    D1 chain: ``CLAUDE_PERSONA`` (stripped, non-empty) → ``DISCORD_STATE_DIR``
    basename (stripped, non-empty) → ``None``.

    ``None`` is the "no channel-session dimension" signal: the write side stamps
    an UNTAGGED episode (D5 age-out; single-session workspaces write as today) and
    the read side disables the filter (workspace-global — AC.PSR.3 no-op AND
    AC.PSR.5 fail-soft both collapse to this).

    Fail-soft: any error reading the environment returns ``None`` (never raises),
    so a read surface can call this without its own try/except and still degrade
    to workspace-global on a garbled env (AC.PSR.5).
    """
    try:
        source = os.environ if env is None else env
        persona = (source.get("CLAUDE_PERSONA") or "").strip()
        if persona:
            return persona
        state_dir = (source.get("DISCORD_STATE_DIR") or "").strip()
        if state_dir:
            basename = os.path.basename(state_dir.rstrip("/"))
            if basename:
                return basename
    except Exception:  # noqa: BLE001 — AC.PSR.5 fail-soft: env access never raises out
        return None
    return None
