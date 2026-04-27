"""SessionStart emitter for loam-mode (sub-plan B).

This module is the dev-discipline counterpart to amendment #45's
hands-off-lifecycle multi-contributor generalisation. It delivers
the SessionStart payload that Claude Code consumes via the second
inner hook of ``build_first_run_stanza`` / ``build_supervisor_stanza``.

Public API:

  - :func:`compute_session_mode` — pure mapping ``"yes" → "dev"`` else
    ``"user"`` (AC.B1).
  - :func:`read_dev_intent_safe` — fail-soft reader of the workspace
    persona contract's ``dev_intent`` field (AC.B5). Returns
    ``"yes" | "no" | "absent"``.
  - :func:`emit_session_start_context` — produce the SessionStart
    additionalContext payload for the workspace's current mode
    (AC.B3 + AC.B4).
  - :func:`build_loam_mode_inner_hook` — return the inner-hook dict
    that hands-off-lifecycle's stanza builders compose into the
    SessionStart envelope (AC.B2).

The module deliberately avoids importing ``primary-persona``'s
``read_dev_intent`` at runtime: ``primary-persona`` is sealed and
``tools/loam-mode`` is dev-discipline; reading the same on-disk
contract shape via local YAML parsing is convention-parity, not
import-coupling.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Literal

import yaml


SessionMode = Literal["dev", "user"]
DevIntent = Literal["yes", "no", "absent"]


# Default dev-extension filename. AC.B3 names ``CLAUDE.dev.md`` as the
# dev-only fragment; F's manifest lists it under ``dev_only``.
DEFAULT_DEV_EXTENSION_FILENAME = "CLAUDE.dev.md"


def compute_session_mode(dev_intent_value: str | None) -> SessionMode:
    """Map a dev-intent answer to a session mode (AC.B1).

    ``"yes"`` → ``"dev"``; everything else (``"no"``, ``"absent"``,
    ``None``, any unexpected token) → ``"user"``. Per locked owner
    ruling D-MASTER.4 the absent / unknown cases default to user mode.
    """
    if dev_intent_value == "yes":
        return "dev"
    return "user"


def _personas_dir(workspace_root: Path) -> Path:
    """Mirror primary-persona's ``dev_intent_storage_path`` semantics.

    Per sub-plan A AC.A.5 the dev-intent answer lives on the persona
    contract at ``<workspace>/workspace/personas/<handle>/contract.yaml``
    post-D.2 (amendment #63). Pre-D.2 it lived at
    ``<workspace>/personas/<handle>/contract.yaml``. The standalone
    resolver here intentionally does NOT import primary-persona
    (sealed); per AC.B.S it also does NOT import workspace-bootstrap
    (sealed). Path constants duplicated inline per D.2-build.B
    pattern (mirrors hands-off-lifecycle hooks). Canonical source:
    ``framework/workspace-bootstrap/src/workspace_bootstrap/
      workspace_paths.py`` (``WORKSPACE_STATE_SUBDIR``,
    ``PERSONAS_SUBDIR``).
    """
    return Path(workspace_root) / "workspace" / "personas"


def read_dev_intent_safe(
    workspace_root: Path,
    *,
    reader: Callable[[Path], str] | None = None,
) -> DevIntent:
    """Return the workspace's dev-intent answer, fail-soft (AC.B5).

    Walks ``<workspace_root>/personas/<handle>/contract.yaml`` for
    each candidate persona; prefers a contract carrying
    ``is_primary: true``; falls back to the alphabetically-first
    contract. Returns the parsed ``dev_intent`` value when it is
    ``"yes"`` or ``"no"``; returns ``"absent"`` for any other value or
    on any failure path (missing file, parse error, schema mismatch,
    unexpected exception).

    The optional ``reader`` callable allows tests to inject a
    deterministic file-reader; production callers leave it ``None``
    and the function uses ``Path.read_text``.

    AC.B5 contract: never raises. The SessionStart hook proceeds in
    user mode rather than blocking on selector error.
    """
    try:
        return _read_dev_intent_inner(workspace_root, reader=reader)
    except Exception:  # noqa: BLE001 — fail-soft per AC.B5
        return "absent"


def _read_dev_intent_inner(
    workspace_root: Path,
    *,
    reader: Callable[[Path], str] | None,
) -> DevIntent:
    personas_dir = _personas_dir(workspace_root)
    if not personas_dir.is_dir():
        return "absent"
    candidates: list[Path] = []
    for child in sorted(personas_dir.iterdir()):
        if not child.is_dir():
            continue
        contract_path = child / "contract.yaml"
        if contract_path.is_file():
            candidates.append(contract_path)
    if not candidates:
        return "absent"

    # Prefer is_primary: true; otherwise first alphabetical.
    parsed: list[tuple[Path, dict]] = []
    for candidate in candidates:
        try:
            text = (
                reader(candidate)
                if reader is not None
                else candidate.read_text(encoding="utf-8")
            )
            data = yaml.safe_load(text)
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(data, dict):
            continue
        parsed.append((candidate, data))

    if not parsed:
        return "absent"

    chosen: dict | None = None
    for _, data in parsed:
        if data.get("is_primary") is True:
            chosen = data
            break
    if chosen is None:
        chosen = parsed[0][1]

    answer = chosen.get("dev_intent")
    # YAML 1.1 implicit-bool semantics map ``yes`` / ``no`` to Python
    # ``True`` / ``False`` when unquoted. The contract author intent
    # is a yes/no string answer; accept either form (string-quoted
    # ``"yes"``, unquoted ``yes`` parsed as bool True, etc.). Per
    # AC.B5 unrecognised tokens fail-soft to ``"absent"``.
    if answer is True:
        return "yes"
    if answer is False:
        return "no"
    if isinstance(answer, str):
        token = answer.strip().lower()
        if token == "yes":
            return "yes"
        if token == "no":
            return "no"
    return "absent"


def emit_session_start_context(
    workspace_root: Path,
    *,
    dev_extension_filename: str = DEFAULT_DEV_EXTENSION_FILENAME,
    reader: Callable[[Path], str] | None = None,
) -> str:
    """Produce the loam-mode SessionStart additionalContext payload.

    Per AC.B3 + AC.B4 the payload is empty in user mode and contains
    the dev-extension content (``CLAUDE.dev.md`` by default) in dev
    mode. When the dev-extension file is missing on a dev workspace
    the function returns a fail-soft diagnostic line rather than
    raising — Claude Code's SessionStart hook never blocks on
    selector error (AC.B5 generalised to emitter).

    The function never raises: any unexpected error converts to the
    user-mode empty-payload outcome (defensive AC.B5 application).
    """
    try:
        intent = read_dev_intent_safe(workspace_root, reader=reader)
        mode = compute_session_mode(intent)
        if mode == "user":
            return ""
        dev_path = Path(workspace_root) / dev_extension_filename
        try:
            if reader is not None:
                return reader(dev_path)
            return dev_path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            return (
                f"[loam-mode] dev mode active but {dev_extension_filename} "
                f"is unavailable; proceeding without dev-extension context."
            )
    except Exception:  # noqa: BLE001 — defensive AC.B5
        return ""


def build_loam_mode_inner_hook(pos_v2_root: Path) -> dict:
    """Return the inner-hook dict for the loam-mode SessionStart command.

    Composed by hands-off-lifecycle's ``build_first_run_stanza`` /
    ``build_supervisor_stanza`` via the amendment #45
    ``extra_inner_hooks`` parameter (AC.B2). Invokes the workspace
    venv's Python with ``-m loam_mode.cli session-start``; the CLI
    routes to :func:`emit_session_start_context` and prints the
    payload to stdout for Claude Code's SessionStart fan-out to
    consume as ``additionalContext``.

    Timeout is 5 seconds per AC.B5 fail-soft + halt-finding-2 §3
    sketch — loam-mode's emit is sub-second I/O; 5s caps a hung
    filesystem without dragging the SessionStart wall-clock.
    """
    pos_v2_root = Path(pos_v2_root)
    python = pos_v2_root / ".venv" / "bin" / "python"
    return {
        "type": "command",
        "command": f"{python} -m loam_mode.cli session-start",
        "async": False,
        "timeout": 5,
    }


# ---------------------------------------------------------------------
# CLI helper for the loam-mode session-start subcommand. Wired into
# loam_mode.cli.main via a ``session-start`` subparser.
# ---------------------------------------------------------------------


def cli_session_start(workspace_root: Path | None = None) -> int:
    """Run ``emit_session_start_context`` and print to stdout.

    AC.B5 fail-soft contract: the function returns 0 on every path —
    a non-zero exit would block Claude Code's SessionStart fan-out;
    the empty-payload + diagnostic-line outcomes both satisfy
    "session proceeds in user mode rather than blocking on selector
    error".

    Side-effect (heavy-b-migrate lazy-projection trigger, dev-discipline,
    plan ``heavy-b-phase-alpha-beta-gamma-migration.md`` D-build.6):
    if ``heavy_b_migrate`` is importable AND the workspace's
    ``dev_intent`` answer is ``"yes"`` AND the dev-objective tree has
    not yet been fully projected, the trigger runs Phase α / β / γ
    against the workspace's tracker DB. The trigger is itself fail-
    soft (every exception is swallowed inside ``run_if_dev_intent``);
    its outcome does NOT modify the SessionStart payload returned to
    Claude Code. Idempotency-by-`lifted_from` makes re-runs cheap on
    already-projected workspaces (the phases short-circuit per-record
    on the existing-key set).
    """
    root = workspace_root if workspace_root is not None else Path.cwd()
    _invoke_lazy_projection(root)
    try:
        payload = emit_session_start_context(root)
    except Exception:  # noqa: BLE001 — defensive AC.B5
        payload = ""
    if payload:
        sys.stdout.write(payload)
        if not payload.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def _invoke_lazy_projection(workspace_root: Path) -> None:
    """Fire-and-forget heavy-b-migrate trigger; never raises.

    Late import keeps loam-mode independent at install time; an
    ``ImportError`` (heavy-b-migrate not on path in this workspace)
    is swallowed silently so the SessionStart hook proceeds normally.
    Per plan §6 constraints 13/14 the trigger is a read-only consumer
    of ``dev_intent`` + idempotent via ``lifted_from``.
    """
    try:
        from heavy_b_migrate.trigger import run_if_dev_intent
    except ImportError:
        return
    try:
        run_if_dev_intent(workspace_root)
    except Exception:  # noqa: BLE001 — defensive AC.B5
        return
