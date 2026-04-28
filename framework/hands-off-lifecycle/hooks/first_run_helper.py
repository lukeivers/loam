"""pos-v2 first-run helper (Phase 3 onward).

Invoked from ``first-run.sh`` once the top-level venv exists. Stdlib-only.

Phases implemented here (proposal §3.1):
  * Phase 3 — per-component pip install (shared + dedicated venvs).
  * Phase 3e — per-component editable install (``pip install -e``) for
    every workspace component that ships a ``pyproject.toml``, in a
    topological order derived from each ``[project].dependencies``
    block. Added 2026-04-22 by the editable-install amendment; without
    this step, cross-component imports (``import pos_orchestrator``,
    ``import workspace_bootstrap``, etc.) fail on a fresh clone.
  * Phase 4 — plist/unit substitution + service bootstrap + health poll.
  * Phase 5 — confirmation sentence emission.
  * Phase 6 — self-retire: rewrite settings.json's SessionStart stanza
    to invoke the sealed supervisor path, delete first-run.sh.
  * Phase 7 — final-state verification.

Error-code range: -32091..-32099 (inside hands-off-lifecycle's block).

  -32091  platform-unsupported:no-compatible-python-found (Phase 1;
          claimed by first-run.sh — this helper never enters that path)
  -32091  platform-unsupported:<label> (Phase 4 if OS is not macos —
          reuses the existing workspace-bootstrap code point)
  -32097  pip-install-failed:<component>:<tail>
  -32097  pip-install-failed:editable:<component>:<tail> (Phase 3e)
  -32098  service-health-timeout:<label>
  -32099  hands-off-lifecycle-internal:<phase>:<detail>
  -32099  hands-off-lifecycle-internal:editable-topological-cycle:<components>
          (Phase 3e — pyproject ``dependencies`` declare a cycle)

Runs in two modes:
  bootstrap — invoked on truly fresh clone; runs Phases 3..7 linearly.
  resume    — invoked when ``.venv/bin/python`` already exists; verifies
              completion state and either no-ops (if self-retire already
              happened elsewhere and we are here due to partial re-run)
              or continues from the first non-complete phase.

Both modes write progress to stdout; Claude Code surfaces stdout as
``additionalContext`` for the SessionStart hook.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Import sibling modules from the hooks directory. When invoked as a
# script via ``first-run.sh``, __file__'s parent is the hooks dir; add
# it to sys.path before importing siblings.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from first_run_inventory import (  # noqa: E402
    InventoryParseError,
    load_inventory,
    resolve_service_labels,
    validate_inventory,
)
from first_run_progress import get_progress  # noqa: E402
from first_run_settings import (  # noqa: E402
    SettingsMergeResult,
    build_first_run_stanza,
    build_supervisor_stanza,
    merge_pre_tool_use,
    merge_session_start,
    merge_status_line,
    merge_stop,
    merge_user_prompt_submit,
)
from first_run_state import (  # noqa: E402
    FirstRunState,
    DEFAULT_POS_ROOT,
    append_log,
    read_state,
    write_state,
)
from agent_file_authoring import (  # noqa: E402
    AgentFileWriteResult,
    write_agent_file,
)


# ---- amendment #45 — multi-contributor SessionStart composition ------
#
# The workspace's loam-mode session-start command is registered as a
# second inner hook on the SessionStart envelope (per amendment #45's
# generalisation of ``build_first_run_stanza`` /
# ``build_supervisor_stanza``). The import of
# ``loam_mode.session_start.build_loam_mode_inner_hook`` is wrapped so
# a missing or broken loam-mode install degrades gracefully to the
# pre-amendment-#45 single-inner-hook shape (AC.45.5 backwards-compat
# in the degraded path). When the import succeeds the inner hook is
# composed into the stanza; when it fails the helper logs nothing and
# proceeds — Claude Code's SessionStart fan-out simply does not get
# the loam-mode emit.


def _loam_mode_inner_hooks(pos_v2_root: Path) -> list[dict]:
    """Return the extra inner-hook list for the SessionStart envelope.

    Imports are lazy; ImportError or any unexpected exception yields
    an empty list (the stanza degrades to single-inner-hook shape).
    """
    try:
        # Prefer the workspace venv's site-packages so a workspace
        # whose loam-mode install differs from the host's is resolved
        # correctly. The shared venv is at ``<root>/.venv``.
        venv_site = (
            pos_v2_root / ".venv" / "lib"
        )
        if venv_site.is_dir():
            for site_dir in venv_site.iterdir():
                site_pkgs = site_dir / "site-packages"
                if site_pkgs.is_dir() and str(site_pkgs) not in sys.path:
                    sys.path.insert(0, str(site_pkgs))
        from loam_mode.session_start import (  # type: ignore[import-not-found]
            build_loam_mode_inner_hook,
        )
        return [build_loam_mode_inner_hook(pos_v2_root)]
    except Exception:  # noqa: BLE001 — fail-soft per AC.45.5
        return []


# ---- amendment #46 — primary-persona session-start + UserPromptSubmit --
#
# The persona's session-start emitter is registered as an inner hook on
# the SessionStart envelope alongside loam-mode (AC46.5). Ordering per
# umbrella plan §6 D5: probe (first-run.sh / pos_session_start.py) →
# persona emit → loam-mode emit. Both helpers are independently fail-
# soft; a missing primary-persona install degrades only the persona
# inner hook (loam-mode still composes).
#
# The persona's user-prompt-submit emitter lands as a single inner hook
# under hooks.UserPromptSubmit via merge_user_prompt_submit (AC46.5).
# Single-contributor for now; AC46.6 defers multi-contributor
# generalisation analogous to amendment #45's SessionStart registry.


def _persona_inner_hooks(pos_v2_root: Path) -> list[dict]:
    """Return the persona's SessionStart inner-hook entry as a list.

    Lazy import + fail-soft per AC46.4. Mirrors ``_loam_mode_inner_hooks``
    shape: missing or broken primary-persona install yields an empty
    list and the SessionStart envelope falls back to omitting only the
    persona inner hook (probe + loam-mode still compose).
    """
    try:
        venv_site = pos_v2_root / ".venv" / "lib"
        if venv_site.is_dir():
            for site_dir in venv_site.iterdir():
                site_pkgs = site_dir / "site-packages"
                if site_pkgs.is_dir() and str(site_pkgs) not in sys.path:
                    sys.path.insert(0, str(site_pkgs))
        from primary_persona.session_start_emitter import (  # type: ignore[import-not-found]
            build_persona_session_start_inner_hook,
        )
        return [build_persona_session_start_inner_hook(pos_v2_root)]
    except Exception:  # noqa: BLE001 — fail-soft per AC46.4
        return []


def _corpus_load_inner_hooks(pos_v2_root: Path) -> list[dict]:
    """Return the corpus-load sentinel SessionStart inner-hook entry.

    Structural-enforcement A1 substrate (AC.SE.4). The CLI lives at
    ``hands-off-lifecycle/hooks/corpus_load_session_start.py``; the
    inner hook invokes it under the workspace's shared venv Python so
    the optional ``loam_mode`` import inside the sentinel module is
    resolvable. The CLI is fail-soft — every exception path returns
    exit 0 — so this helper is fire-and-forget at session-start.
    """
    venv_python = pos_v2_root / ".venv" / "bin" / "python"
    script = (
        pos_v2_root
        / "framework"
        / "hands-off-lifecycle"
        / "hooks"
        / "corpus_load_session_start.py"
    )
    return [
        {
            "type": "command",
            "command": f"{venv_python} {script}",
            "async": False,
            # 5s matches loam-mode + persona inner-hook timeouts (the
            # established A1 substrate budget per plan-doc §5
            # constraint 3).
            "timeout": 5,
        }
    ]


def _extra_session_start_hooks(pos_v2_root: Path) -> list[dict]:
    """Return the SessionStart envelope's ``extra_inner_hooks`` list.

    Order per umbrella plan §6 D5 (D-build.6 in the builder plan):
    persona → loam-mode → corpus-load. The base inner hook
    (first-run.sh in `build_first_run_stanza`; supervisor in
    `build_supervisor_stanza`) composes BEFORE these via the stanza
    builder; the final order at Claude Code's hook fan-out is:
    probe (base) → persona → loam-mode → corpus-load.

    Each contributor independently fail-soft; one returning ``[]`` is
    graceful (the envelope simply omits that hook).
    """
    return (
        _persona_inner_hooks(pos_v2_root)
        + _loam_mode_inner_hooks(pos_v2_root)
        + _corpus_load_inner_hooks(pos_v2_root)
    )


def _persona_user_prompt_submit_stanza(pos_v2_root: Path) -> dict | None:
    """Return the persona's UserPromptSubmit envelope, or ``None`` when
    the persona's emitter is unavailable.

    Lazy import + fail-soft per AC46.4. Returning ``None`` signals the
    caller to skip ``merge_user_prompt_submit`` entirely (the
    UserPromptSubmit hook is simply not registered — pre-amendment-#46
    behaviour preserved).
    """
    try:
        venv_site = pos_v2_root / ".venv" / "lib"
        if venv_site.is_dir():
            for site_dir in venv_site.iterdir():
                site_pkgs = site_dir / "site-packages"
                if site_pkgs.is_dir() and str(site_pkgs) not in sys.path:
                    sys.path.insert(0, str(site_pkgs))
        from primary_persona.session_start_emitter import (  # type: ignore[import-not-found]
            build_persona_user_prompt_submit_inner_hook,
        )
        return {
            "matcher": "",
            "hooks": [build_persona_user_prompt_submit_inner_hook(pos_v2_root)],
        }
    except Exception:  # noqa: BLE001 — fail-soft per AC46.4
        return None


def _maybe_merge_user_prompt_submit(
    *, pos_v2_root: Path, settings_path: Path
) -> None:
    """Invoke ``merge_user_prompt_submit`` when the persona's emitter
    is available; no-op otherwise.

    Wraps the merge so call sites can fire-and-forget; settings.json
    write failures are caught (matching the surrounding Phase-3d /
    Phase-4c / Phase-6 settings.json handling — those phases also
    tolerate transient I/O errors).
    """
    stanza = _persona_user_prompt_submit_stanza(pos_v2_root)
    if stanza is None:
        return
    try:
        merge_user_prompt_submit(
            settings_path=settings_path,
            new_entry=stanza,
        )
    except Exception:  # noqa: BLE001 — fail-soft per AC46.4
        # Settings.json write failure or merge exception. The
        # SessionStart hook still fires; the workspace simply lacks
        # the UserPromptSubmit hook this run. A subsequent first-run
        # / supervisor cycle re-attempts the merge.
        return


# ---- amendment #48 — Stop hook merge --------------------------------
#
# The persona's Stop emitter is registered as a single inner hook
# under hooks.Stop via merge_stop (AC.M.11). Single-contributor for
# now (plan §9 defers multi-contributor generalisation). At each of
# the three SessionStart-merge call sites where
# _maybe_merge_user_prompt_submit already runs (Phase 3d, Phase 4c,
# Phase 6), an additional _maybe_merge_stop call lands so the
# settings.json gains hooks.Stop alongside hooks.SessionStart and
# hooks.UserPromptSubmit. Lazy-imported with fail-soft — missing or
# broken primary-persona install degrades to no-Stop-hook behaviour
# (pre-amendment-#48 behaviour preserved).


def _persona_stop_stanza(pos_v2_root: Path) -> dict | None:
    """Return the persona's Stop envelope, or ``None`` when the
    persona's emitter is unavailable.

    Lazy import + fail-soft per AC.M.4. Returning ``None`` signals
    the caller to skip ``merge_stop`` entirely (the Stop hook is
    simply not registered — pre-amendment-#48 behaviour preserved).
    """
    try:
        venv_site = pos_v2_root / ".venv" / "lib"
        if venv_site.is_dir():
            for site_dir in venv_site.iterdir():
                site_pkgs = site_dir / "site-packages"
                if site_pkgs.is_dir() and str(site_pkgs) not in sys.path:
                    sys.path.insert(0, str(site_pkgs))
        from primary_persona.session_start_emitter import (  # type: ignore[import-not-found]
            build_persona_stop_inner_hook,
        )
        return {
            "matcher": "",
            "hooks": [build_persona_stop_inner_hook(pos_v2_root)],
        }
    except Exception:  # noqa: BLE001 — fail-soft per AC.M.4
        return None


def _maybe_merge_stop(
    *, pos_v2_root: Path, settings_path: Path
) -> None:
    """Invoke ``merge_stop`` when the persona's emitter is available;
    no-op otherwise.

    Mirrors ``_maybe_merge_user_prompt_submit`` shape exactly: lazy-
    import + fail-soft so call sites can fire-and-forget; settings.json
    write failures are caught (matching the surrounding Phase-3d /
    Phase-4c / Phase-6 settings.json handling — those phases also
    tolerate transient I/O errors).
    """
    stanza = _persona_stop_stanza(pos_v2_root)
    if stanza is None:
        return
    try:
        merge_stop(
            settings_path=settings_path,
            new_entry=stanza,
        )
    except Exception:  # noqa: BLE001 — fail-soft per AC.M.4
        return


# ---- amendment #49 — top-level ``statusLine`` registration ----------
#
# The renderer script at ``hands-off-lifecycle/hooks/statusline.py``
# is registered at the top-level ``statusLine`` field of
# ``.claude/settings.json`` so Claude Code spawns it every ~1 s
# during first-run. Per locked plan §6 D-build.5, the merge fires
# from the same call sites as the SessionStart / UserPromptSubmit /
# Stop merges (Phase 3d settings authorship + Phase 6 self-retire).
# Fail-soft (D-build.3 mirror): a settings.json write failure must
# not block first-run, since the status-line install is additive UX
# on top of the SessionStart `additionalContext` channel that
# already conveys the structured failure path.


def _status_line_stanza(pos_v2_root: Path) -> dict[str, Any]:
    """Return the canonical ``statusLine`` envelope for pos-v2.

    Per locked plan §6 D-build.1: the renderer is invoked under the
    interpreter ``sys.executable`` resolves to (the dispatch's
    detection chain already validated ≥ 3.13). Post-completion the
    supervisor's settings-touch path may rewrite the command to use
    the workspace venv's Python for cold-start latency reduction —
    that's method, not AC, and lives on the supervisor side.
    """
    pos_v2_root = Path(pos_v2_root)
    script = pos_v2_root / "framework" / "hands-off-lifecycle" / "hooks" / "statusline.py"
    return {
        "type": "command",
        "command": f"{sys.executable} {script}",
        "refreshInterval": 1,
    }


def _maybe_merge_status_line(
    *, pos_v2_root: Path, settings_path: Path
) -> None:
    """Invoke ``merge_status_line`` fail-soft.

    The renderer is co-located with the rest of hands-off-lifecycle's
    hooks; no lazy-import probe is needed (unlike persona helpers
    which depend on a workspace-bootstrap-time install). Settings.json
    write failures are caught — the locked plan §5 fail-closed
    direction applies here as well: a transient I/O error during
    Phase 3d / Phase 6 must not regress first-run.
    """
    try:
        merge_status_line(
            settings_path=settings_path,
            new_entry=_status_line_stanza(pos_v2_root),
        )
    except Exception:  # noqa: BLE001 — fail-soft per locked plan §5
        return


# ---- structural-enforcement A2 — PreToolUse objective-binding gate --
#
# The objective-binding gate is registered as a single inner hook
# under ``hooks.PreToolUse`` via ``merge_pre_tool_use``. Single-
# contributor for now (A3 TDD-guard / A4 Bash/Agent-context guards
# will compose alongside via the same merge function once they ship,
# generalised the same way amendment #45 generalised the SessionStart
# counterparts). Matchers ``Edit|Write|MultiEdit`` per locked plan
# D-A2.1. The gate is co-located with the rest of hands-off-lifecycle's
# hooks; no lazy-import probe is needed. Fail-soft mirrors the locked
# plan §5 fail-closed direction: a transient I/O error must not
# regress first-run.


def _objective_binding_gate_stanza(pos_v2_root: Path) -> dict[str, Any]:
    """Return the PreToolUse envelope for the objective-binding gate.

    Per locked plan §6 D-A2.1: matcher ``Edit|Write|MultiEdit`` (the
    three textual-modification tools the gate covers). The gate script
    is invoked under ``sys.executable``; per the existing convention
    (amendment #49's status-line stanza) the interpreter path is
    resolved at registration time. The gate is stdlib-only at import
    so cold-start cost is the Python-startup envelope alone.
    """
    pos_v2_root = Path(pos_v2_root)
    script = (
        pos_v2_root
        / "framework"
        / "hands-off-lifecycle"
        / "hooks"
        / "objective_binding_gate.py"
    )
    return {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
            {
                "type": "command",
                "command": f"{sys.executable} {script}",
                "async": False,
                "timeout": 5,
            }
        ],
    }


def _tdd_guard_stanza(pos_v2_root: Path) -> dict[str, Any]:
    """Return the PreToolUse envelope for A3's TDD-guard.

    Per locked plan §6 D-A3.1: matcher ``Edit|Write|MultiEdit`` (same
    set A2 covers — A3 inherits A2's matcher contract). Per D-A3.8 A3
    runs AFTER A2 in the hook chain; this stanza is appended second
    in the multi-contributor outer list.
    """
    pos_v2_root = Path(pos_v2_root)
    script = (
        pos_v2_root
        / "framework"
        / "hands-off-lifecycle"
        / "hooks"
        / "tdd_guard.py"
    )
    return {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
            {
                "type": "command",
                "command": f"{sys.executable} {script}",
                "async": False,
                "timeout": 5,
            }
        ],
    }


def _maybe_merge_pre_tool_use(
    *, pos_v2_root: Path, settings_path: Path
) -> None:
    """Invoke ``merge_pre_tool_use`` fail-soft.

    Multi-contributor as of structural-enforcement A3 (D-A3.8): the
    outer PreToolUse list carries A2's objective-binding gate FIRST
    and A3's TDD-guard SECOND. Claude Code admits multiple matcher
    entries under one event and evaluates them sequentially; A2 deny
    short-circuits A3.

    Both gate scripts are co-located with hands-off-lifecycle's hooks;
    no lazy-import probe is needed. A settings.json write failure
    must not regress first-run (locked plan §5 fail-closed direction
    mirrors here).
    """
    try:
        merge_pre_tool_use(
            settings_path=settings_path,
            new_entries=[
                _objective_binding_gate_stanza(pos_v2_root),
                _tdd_guard_stanza(pos_v2_root),
            ],
        )
    except Exception:  # noqa: BLE001 — fail-soft per locked plan §5
        return


# ---- error codes -----------------------------------------------------


ERR_PIP_INSTALL_FAILED = -32097
ERR_SERVICE_HEALTH_TIMEOUT = -32098
ERR_HANDS_OFF_INTERNAL = -32099
ERR_PLATFORM_UNSUPPORTED = -32091


# ---- workspace-slug derivation (amendment #6) ------------------------
#
# Duplicated from workspace_bootstrap.adapters.first_run_scaffold.
# The worker runs under the system Python interpreter at the moment it
# needs a slug (for inventory label resolution in Phase 4b), before the
# shared venv is on this process's path — so a stdlib-only local copy
# is needed. Both implementations must stay in lock-step; the amendment
# ships a parity test (tests/test_workspace_slug_parity.py) asserting
# they agree on a fixture set. Any change to sanitisation semantics
# must land in both files in the same commit.


_SLUG_ALLOWED_RE = re.compile(r"[^a-z0-9-]+")
_SLUG_COLLAPSE_RE = re.compile(r"-+")


def _workspace_slug(workspace_root: Path | str) -> str:
    """Derive the workspace slug used in namespaced service labels."""
    basename = Path(workspace_root).name
    lowered = basename.lower()
    slug = _SLUG_ALLOWED_RE.sub("-", lowered)
    slug = _SLUG_COLLAPSE_RE.sub("-", slug)
    slug = slug.strip("-")
    if not slug:
        # Propagate as ERR_HANDS_OFF_INTERNAL; the scaffold subprocess
        # would normally refuse first, but the helper defends the
        # health-poll path as well so a misconfigured harness does not
        # silently degrade to probing the wrong labels.
        raise ValueError(
            f"workspace-slug-unrepresentable:{basename!r}"
        )
    return slug


# ---- state-file integration (detachment amendment) ------------------
#
# Module-level handles, set by ``main()`` when invoked as the detached
# worker.
#
# ``_STATE_POS_ROOT`` determines where the host-global ``first-run.log``
# lives (still host-global — it is a tailable narrative surface, not a
# state artefact).
#
# ``_STATE_WORKSPACE_ROOT`` (amendment #28) determines where
# ``first-run.state`` lives — inside the workspace, at
# ``<workspace>/.pos/first-run.state`` — routing state by workspace
# identity so first-run completion for workspace A does not short-
# circuit workspace B.
#
# ``_STATE_GENERATION`` tags each worker spawn so log lines from a
# respawn are distinguishable from the original run. Tests can point
# these at a tmp_path without reaching into the module.
_STATE_POS_ROOT: Path = DEFAULT_POS_ROOT
_STATE_WORKSPACE_ROOT: Path = Path.cwd()
_STATE_GENERATION: int = 1
# Guard flag: only write state-file / log entries when main() has
# explicitly enabled it. Without this guard, unit tests that exercise
# _emit_diag() directly would scribble into the developer's real
# ``~/.pos/`` directory on every test run — an unacceptable side
# effect. main() flips this on once; test fixtures use the state
# module's API directly when they need to exercise the state path.
_STATE_WRITES_ENABLED: bool = False


# Per-phase progress percentage (0-100) the worker writes alongside
# every recognised ``_advance_state`` call. Per amendment #49 plan
# §6 D-build.6 / D-build.7: builder calibrates the values; co-located
# with the worker's ``_advance_state`` so a phase introduction
# without a pct update is visible in the same diff (plan §13 risk
# mitigation). Phases not present here leave the prior progress_pct
# untouched.
_PHASE_PCT: dict[str, int] = {
    "phase-2-venv-creation": 5,
    "phase-3a-inventory": 10,
    "phase-3b-shared-deps": 25,
    "phase-3e-editable-installs": 55,
    "phase-3c-dedicated-venvs": 70,
    "phase-4a-scaffold": 80,
    "phase-4c-agent-file-authorship": 85,
    "phase-4b-health-poll": 90,
    "phase-5-confirmation": 95,
    "phase-6-self-retire": 98,
    "complete": 100,
}


def _advance_state(
    status: str,
    *,
    phase: str = "",
    detail: str = "",
    error_code: int = 0,
    remediation: str = "",
) -> None:
    """Persist a state-file update, also mirrors to the plain-language log.

    Called at every phase boundary and on every halt. The state file is
    the authoritative handoff channel between this process and the next
    SessionStart hook firing; the log file is the user's live view.
    Both are written — one is structured, one is narrative. Neither is
    optional.

    Amendment #49: when ``phase`` matches a recognised key in
    ``_PHASE_PCT``, ``state.progress_pct`` is bumped to the mapped
    value. The status-line renderer reads this field as one input
    to the rendered progress line (AC.SL.1).

    No-op when ``_STATE_WRITES_ENABLED`` is False (unit-test path) —
    the caller never wants a stray ~/.pos/ write from a test run.
    """
    if not _STATE_WRITES_ENABLED:
        return
    existing = read_state(_STATE_WORKSPACE_ROOT)
    state = existing or FirstRunState()
    state.status = status
    state.pid = os.getpid()
    state.generation = _STATE_GENERATION
    if phase:
        state.phase = phase
        if phase in _PHASE_PCT:
            state.progress_pct = _PHASE_PCT[phase]
    if detail:
        state.detail = detail
    if error_code:
        state.error_code = error_code
    if remediation:
        state.remediation = remediation
    write_state(state, _STATE_WORKSPACE_ROOT)
    log_line = f"{status}"
    if phase:
        log_line += f" — {phase}"
    if detail:
        log_line += f" — {detail}"
    append_log(log_line, _STATE_POS_ROOT, generation=_STATE_GENERATION)


# ---- diagnostic emission --------------------------------------------


def _emit_diag(
    code: int,
    kind: str,
    detail: str,
    remediation: str,
    *,
    user_what: str | None = None,
    user_remediation: str | None = None,
) -> None:
    """Emit a loud-escalation diagnostic and exit 0.

    Two surfaces: (a) stdout holds the structured payload Claude Code
    surfaces to the model as ``additionalContext`` (error code, kind,
    detail, long-form remediation) — unchanged from the pre-amendment
    contract; (b) /dev/tty holds the plain-language failure the human
    can act on.

    The TTY surface receives ``user_what`` (one-sentence plain-English
    description of what broke) and ``user_remediation`` (plain-English,
    step-by-step, no jargon), with the error code appended as a
    reference — not the primary surface. Callers may omit the user_*
    parameters; when absent, we fall back to synthesising from ``kind``
    and ``remediation`` so the TTY never falls silent on a failure
    path (AC4 — user always sees *something* actionable, not just a
    -32xxx code in isolation).
    """
    if user_what is None:
        # Derive a best-effort plain sentence from the kind label.
        # Anything of the form "category:label" gets the label half
        # with dashes turned into spaces — enough to read aloud.
        tail = kind.split(":", 1)[1] if ":" in kind else kind
        user_what = tail.replace("-", " ").replace("_", " ")
    if user_remediation is None:
        # Pass through the long-form remediation; it's still readable
        # prose even if slightly denser than the ideal user surface.
        user_remediation = remediation
    get_progress().fail(
        what=user_what,
        remediation=user_remediation,
        error_code=code,
    )
    # Persist the failure to the state file so the next SessionStart
    # hook can surface the plain-language remediation in its
    # additionalContext block. Without this step the user only sees
    # silence on the next launch — the exact failure mode this
    # amendment closes.
    _advance_state(
        "failed",
        detail=f"{kind}: {detail}",
        error_code=code,
        remediation=user_remediation,
    )
    print(
        "\npos v2 first-run: halted.\n"
        f"Error code: {code} {kind}\n"
        f"Detail:     {detail}\n\n"
        f"{remediation}\n"
    )


# ---- platform detection ----------------------------------------------


def _detect_platform() -> str:
    s = sys.platform.lower()
    if s == "darwin":
        return "macos"
    return s


# ---- pip install -----------------------------------------------------


@dataclass
class PipOutcome:
    ok: bool
    component: str
    venv_python: Path
    requirements_path: Path | None
    returncode: int = 0
    stderr_tail: str = ""


def _run_pip_install(
    *,
    venv_python: Path,
    requirements: Path,
    component: str,
    timeout_s: int = 600,
) -> PipOutcome:
    """Run ``pip install -r requirements`` in the given venv."""
    try:
        result = subprocess.run(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-r",
                str(requirements),
            ],
            check=False,
            capture_output=True,
            timeout=timeout_s,
            text=True,
        )
    except subprocess.TimeoutExpired:
        return PipOutcome(
            ok=False,
            component=component,
            venv_python=venv_python,
            requirements_path=requirements,
            returncode=-1,
            stderr_tail="pip install timed out",
        )
    except Exception as e:  # pragma: no cover
        return PipOutcome(
            ok=False,
            component=component,
            venv_python=venv_python,
            requirements_path=requirements,
            returncode=-1,
            stderr_tail=f"{type(e).__name__}: {e}",
        )
    tail = (result.stderr or "").splitlines()[-10:]
    return PipOutcome(
        ok=(result.returncode == 0),
        component=component,
        venv_python=venv_python,
        requirements_path=requirements,
        returncode=result.returncode,
        stderr_tail="\n".join(tail),
    )


def _install_shared_components(
    *,
    pos_v2_root: Path,
    shared_venv_python: Path,
    component_names: list[str],
) -> list[PipOutcome]:
    """Install requirements.txt for each shared-venv component that has one."""
    progress = get_progress()
    outcomes: list[PipOutcome] = []
    # Filter down to components that actually have a requirements.txt
    # before counting, so the user-facing "X of Y" matches what they
    # will actually see run.
    installable = [
        name for name in component_names
        if (pos_v2_root / "framework" / name / "requirements.txt").exists()
    ]
    total = len(installable)
    seq = 0
    for name in component_names:
        comp_dir = pos_v2_root / "framework" / name
        req = comp_dir / "requirements.txt"
        if not req.exists():
            # Component has no requirements.txt; nothing to install here.
            # Editable installs (pyproject.toml) are out of first-run's
            # scope per research §4.4 — the shared venv is expected to
            # already have the tooling it needs from the workspace's
            # common base.
            continue
        seq += 1
        progress.step(f"installing component dependencies [{seq} of {total}]: {name}")
        outcomes.append(
            _run_pip_install(
                venv_python=shared_venv_python,
                requirements=req,
                component=name,
            )
        )
    return outcomes


def _install_dedicated_venv(
    *,
    pos_v2_root: Path,
    shared_python: Path,
    entry: dict[str, Any],
) -> tuple[Path, PipOutcome]:
    """Create a dedicated venv and install its requirements.

    Uses the shared venv's Python to create the dedicated venv (they
    share the system 3.13 interpreter reference, which stdlib ``venv``
    follows via the --symlinks default).
    """
    venv_path = pos_v2_root / entry["venv_path"]
    req_path = pos_v2_root / entry["requirements"]
    component = entry["component"]

    if not (venv_path / "bin" / "python").exists():
        # Create the dedicated venv using the shared venv's Python.
        # The new venv inherits the system 3.13 interpreter.
        try:
            subprocess.run(
                [str(shared_python), "-m", "venv", str(venv_path)],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except subprocess.CalledProcessError as e:
            return venv_path, PipOutcome(
                ok=False,
                component=component,
                venv_python=venv_path / "bin" / "python",
                requirements_path=req_path,
                returncode=e.returncode,
                stderr_tail=(e.stderr or b"").decode("utf-8", errors="replace")[-500:],
            )
        except subprocess.TimeoutExpired:
            return venv_path, PipOutcome(
                ok=False,
                component=component,
                venv_python=venv_path / "bin" / "python",
                requirements_path=req_path,
                returncode=-1,
                stderr_tail="dedicated venv creation timed out",
            )

    outcome = _run_pip_install(
        venv_python=venv_path / "bin" / "python",
        requirements=req_path,
        component=component,
        timeout_s=1800,  # Graphiti install can legitimately run long.
    )
    return venv_path, outcome


# ---- editable-install discovery + topological ordering ---------------
#
# Added by the 2026-04-22 editable-install amendment.
#
# Failure class: missing editable-install phase — cross-component
# imports fail on fresh clone.
# Systemic cause: component packages were installed at build time
# outside first-run scope, never wired into the shipped first-run flow.
# Structural remedy: discover components via pyproject walk, topological
# order from declared deps, idempotent on re-run.


# Directories that are not workspace components and must never be
# considered by the pyproject walk. Kept short so adding a new
# component does not require editing this list.
_EDITABLE_DISCOVERY_EXCLUDES = frozenset(
    {
        ".venv",
        ".git",
        ".pytest_cache",
        "__pycache__",
        "data",
        "docs",
        "node_modules",
        ".claude",
    }
)


def _discover_components(pos_v2_root: Path) -> list[dict[str, Any]]:
    """Walk ``pos_v2_root/framework/`` for ``*/pyproject.toml`` and return component specs.

    Each returned mapping has:
      * ``dir``       — Path to the component directory (child of framework/)
      * ``name``      — the ``[project].name`` declared in pyproject
      * ``deps``      — raw ``[project].dependencies`` list (verbatim)

    Only immediate children of ``pos_v2_root/framework/`` are considered
    (post-D.1 directory restructure: framework code lives under
    ``framework/`` and workspace state lives outside it). Nested
    pyprojects (tests, fixtures) are ignored — first-run installs one
    editable package per component directory, not arbitrary subprojects.

    Discovery is deliberately not a hardcoded list: adding a new
    component directory under ``framework/`` with a ``pyproject.toml``
    pulls it into the first-run install automatically. A hardcoded
    list is a regression vector — the next new component would be
    silently missed.
    """
    components: list[dict[str, Any]] = []
    framework_root = pos_v2_root / "framework"
    if not framework_root.is_dir():
        # Pre-D.1 layout fallback: framework code lived at the
        # workspace root. Returning an empty list here would silently
        # break first-run on a pre-migrated tree; the structural
        # contract of D.1 is that the workspace HAS a framework/
        # directory. Surface clearly via empty return — caller's
        # downstream behaviour (no editable installs, no failures)
        # mirrors a workspace with no components, which is the
        # most defensive degraded state.
        return components
    for child in sorted(framework_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name in _EDITABLE_DISCOVERY_EXCLUDES:
            continue
        if child.name.startswith("."):
            continue
        pyproject = child / "pyproject.toml"
        if not pyproject.exists():
            continue
        try:
            with open(pyproject, "rb") as fh:
                data = tomllib.load(fh)
        except (OSError, tomllib.TOMLDecodeError):
            # Malformed or unreadable pyproject — skip silently; the
            # underlying component's own test suite will catch it.
            continue
        project = data.get("project") or {}
        name = project.get("name")
        if not isinstance(name, str) or not name:
            continue
        deps_raw = project.get("dependencies") or []
        deps = [d for d in deps_raw if isinstance(d, str)]
        components.append({"dir": child, "name": name, "deps": deps})
    return components


def _extract_dep_name(dep_spec: str) -> str:
    """Return the bare distribution name from a PEP 508 requirement string.

    Only the prefix up to the first version/marker/extras punctuation is
    returned. ``pydantic>=2`` → ``pydantic``; ``scope_of_work`` → ``scope_of_work``.
    Dashes and underscores are normalised to underscores for comparison
    with ``[project].name`` (which uses underscores in pos-v2).
    """
    # Punctuation that terminates the name portion of a PEP 508 spec.
    terminators = ("<", ">", "=", "!", "~", ";", "[", " ", "@")
    name = dep_spec
    for t in terminators:
        idx = name.find(t)
        if idx >= 0:
            name = name[:idx]
    return name.strip().replace("-", "_")


def _topological_order(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return ``components`` sorted so each item's sibling deps come first.

    A component's ``deps`` list may contain both external deps (pydantic,
    pyee, …) and sibling component names (``scope_of_work``,
    ``pos_orchestrator``, …). Only sibling names participate in the
    topological sort; external deps are ignored (pip resolves them).

    Raises ``RuntimeError`` on a declared cycle — pos-v2's component
    graph is a DAG by design and a cycle is a shipped-artifact defect.
    """
    name_to_component: dict[str, dict[str, Any]] = {
        c["name"]: c for c in components
    }
    sibling_names = set(name_to_component.keys())

    # Adjacency: component_name -> set of sibling names it depends on.
    adj: dict[str, set[str]] = {}
    for c in components:
        siblings: set[str] = set()
        for dep in c["deps"]:
            bare = _extract_dep_name(dep)
            if bare in sibling_names and bare != c["name"]:
                siblings.add(bare)
        adj[c["name"]] = siblings

    # Kahn's algorithm — stable output via sorted() on each level.
    ordered: list[dict[str, Any]] = []
    remaining = dict(adj)
    while remaining:
        ready = sorted(name for name, deps in remaining.items() if not deps)
        if not ready:
            cycle_members = sorted(remaining.keys())
            raise RuntimeError(
                "editable-topological-cycle:" + ",".join(cycle_members)
            )
        for name in ready:
            ordered.append(name_to_component[name])
            del remaining[name]
        for name in list(remaining.keys()):
            remaining[name] = {d for d in remaining[name] if d in remaining}
    return ordered


def _is_component_installed(
    venv_python: Path, component_name: str, component_dir: Path
) -> bool:
    """Return True iff ``component_name`` (distribution name) is already editable-installed.

    Distribution name (``[project].name`` in pyproject) is not always
    equal to the top-level import module name. Example: safety-layer's
    dist name is ``pos_safety_layer`` but its importable module is
    ``safety_layer``. Idempotency must therefore check by *distribution*
    identity, not by import name.

    Uses ``importlib.metadata.distribution()`` to resolve the dist, then
    reads the ``direct_url.json`` dist-info file to confirm the install
    is editable and rooted at ``component_dir`` (PEP 610). If the dist
    is installed from a different source, we reinstall rather than
    short-circuit — the user may have moved their workspace and a stale
    editable-install would import from the wrong path.
    """
    probe_script = (
        "import json, sys\n"
        "from importlib.metadata import distribution, PackageNotFoundError\n"
        "name = sys.argv[1]\n"
        "try:\n"
        "    d = distribution(name)\n"
        "except PackageNotFoundError:\n"
        "    print(json.dumps({'found': False}))\n"
        "    raise SystemExit(0)\n"
        "try:\n"
        "    raw = d.read_text('direct_url.json') or ''\n"
        "except Exception:\n"
        "    raw = ''\n"
        "info = json.loads(raw) if raw else {}\n"
        "print(json.dumps({'found': True, 'direct_url': info}))\n"
    )
    result = subprocess.run(
        [str(venv_python), "-c", probe_script, component_name],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return False
    try:
        payload = json.loads(result.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return False
    if not payload.get("found"):
        return False
    info = payload.get("direct_url") or {}
    # PEP 610: editable install has dir_info.editable == true.
    dir_info = info.get("dir_info") or {}
    if not dir_info.get("editable"):
        # Non-editable install — reinstall to make it editable.
        return False
    url = info.get("url") or ""
    if not url.startswith("file://"):
        return False
    installed_path = Path(url[len("file://"):])
    try:
        return installed_path.resolve() == component_dir.resolve()
    except (ValueError, OSError):
        return str(installed_path) == str(component_dir)


def _install_editable(
    *,
    venv_python: Path,
    component_dir: Path,
    component_name: str,
    timeout_s: int = 300,
) -> PipOutcome:
    """Run ``pip install -e <component_dir>`` in the shared venv.

    Uses ``--no-deps`` because all declared siblings are installed in
    topological order by the caller (sibling deps are file-refs, not
    PyPI releases — without ``--no-deps`` pip would try to resolve them
    against PyPI and fail). External deps (pydantic, pyee, etc.) were
    installed during the earlier shared-requirements phase, so pip
    does not need to resolve them here either.
    """
    try:
        result = subprocess.run(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-deps",
                "-e",
                str(component_dir),
            ],
            check=False,
            capture_output=True,
            timeout=timeout_s,
            text=True,
        )
    except subprocess.TimeoutExpired:
        return PipOutcome(
            ok=False,
            component=component_name,
            venv_python=venv_python,
            requirements_path=None,
            returncode=-1,
            stderr_tail=f"pip install -e {component_dir} timed out",
        )
    except Exception as e:  # pragma: no cover
        return PipOutcome(
            ok=False,
            component=component_name,
            venv_python=venv_python,
            requirements_path=None,
            returncode=-1,
            stderr_tail=f"{type(e).__name__}: {e}",
        )
    tail_src = result.stderr or result.stdout or ""
    tail = "\n".join(tail_src.splitlines()[-10:])
    return PipOutcome(
        ok=(result.returncode == 0),
        component=component_name,
        venv_python=venv_python,
        requirements_path=None,
        returncode=result.returncode,
        stderr_tail=tail,
    )


def _install_editable_components(
    *,
    pos_v2_root: Path,
    shared_venv_python: Path,
) -> list[PipOutcome]:
    """Discover components, topologically order them, and editable-install each.

    Idempotent: already-installed components short-circuit without
    invoking pip. The pip ``-e`` install is itself idempotent but
    short-circuiting keeps the fresh-clone/re-run time difference
    observable (and prevents rebuilding editable metadata pointlessly).
    """
    progress = get_progress()
    components = _discover_components(pos_v2_root)
    ordered = _topological_order(components)
    outcomes: list[PipOutcome] = []
    total = len(ordered)
    for seq, comp in enumerate(ordered, 1):
        name: str = comp["name"]
        cdir: Path = comp["dir"]
        if _is_component_installed(shared_venv_python, name, cdir):
            progress.step(f"component package [{seq} of {total}]: {name} (already installed)")
            outcomes.append(
                PipOutcome(
                    ok=True,
                    component=name,
                    venv_python=shared_venv_python,
                    requirements_path=None,
                    returncode=0,
                    stderr_tail="already-installed",
                )
            )
            continue
        progress.step(f"installing component package [{seq} of {total}]: {name}")
        outcomes.append(
            _install_editable(
                venv_python=shared_venv_python,
                component_dir=cdir,
                component_name=name,
            )
        )
    return outcomes


# ---- plist substitution via Amendment 4 ------------------------------


def _invoke_first_run_scaffold(
    *,
    pos_v2_root: Path,
    shared_venv_python: Path,
    service_manager_dir_override: Path | None = None,
    service_bootstrap: bool = True,
    pos_root: Path | None = None,
) -> None:
    """Invoke Amendment 4's run_first_run_scaffold() via a subprocess
    under the shared venv's Python.

    ## Why a subprocess (amendment #5 rewrite)

    The detached first-run worker runs under the system interpreter
    that ``first-run.sh`` detected on PATH — intentionally stdlib-only,
    because the shared venv does not exist at the moment the shell hook
    fires. ``run_first_run_scaffold`` lives inside the ``workspace-
    bootstrap`` component whose ``__init__.py`` transitively imports
    ``yaml`` (pyyaml), ``pydantic``, and ``opentelemetry``. Those are
    installed only in the shared venv (Phase 3b). An in-process import
    of the adapter under the worker's system interpreter crashed with
    ``ModuleNotFoundError: No module named 'yaml'`` (and later
    ``pydantic``, then ``opentelemetry``) before the scaffold function
    body — which uses only stdlib — could run.

    Rather than lazy-importing every transitive dep across the
    workspace-bootstrap package (structural refactor crossing a sealed
    component) or installing all three into the system interpreter
    (explicitly excluded by the amendment brief), the scaffold is
    invoked as a subprocess under the shared venv's Python. The venv
    by Phase 4a is fully populated and contains every transitive dep
    the adapter needs. The hands-off-lifecycle surface is the *only*
    component touched by this fix.

    ## Contract with the runner

    ``first_run_scaffold_runner.py`` exits 0 on success, 1 on scaffold
    exception, 2 on runner-internal failure. On exit 1 the runner
    writes a single JSON line to stderr with the exception type +
    message + code; this function parses that and raises a
    ``RuntimeError`` whose ``args[0]`` carries a recognisable string.
    The caller (``_run_bootstrap`` at the Phase 4a call site) already
    has a ``try/except`` that routes any raised exception through
    ``_emit_diag`` with a scaffold-failed diagnostic — the surfacing
    semantics are preserved.

    ## Parameters

    Mirrors the adapter's own signature one-for-one so the call-site
    change is minimal. ``pos_root`` defaults to ``Path.home() / ".pos"``
    to match the adapter's own default for the production path, and
    can be overridden for tests.
    """
    runner = _HOOKS_DIR / "first_run_scaffold_runner.py"
    if not runner.exists():
        raise RuntimeError(
            f"scaffold-runner-missing: {runner} not on disk. "
            "This is a shipped-artifact defect — file an issue."
        )
    if not shared_venv_python.exists():
        raise RuntimeError(
            f"scaffold-runner-venv-missing: {shared_venv_python} not on "
            "disk. Phase 3 did not complete; re-running next session."
        )
    effective_pos_root = pos_root or (Path.home() / ".pos")
    cmd = [
        str(shared_venv_python),
        "-u",  # unbuffered — progress lines hit the worker's log promptly
        str(runner),
        "--pos-root",
        str(effective_pos_root),
        "--workspace-root",
        str(pos_v2_root),
        "--service-bootstrap",
        "true" if service_bootstrap else "false",
        "--partial-recovery",
        "true",  # detachment amendment: always recover rather than halt
        "--dry-run",
        "false",
    ]
    if service_manager_dir_override is not None:
        cmd.extend(
            [
                "--service-manager-dir-override",
                str(service_manager_dir_override),
            ]
        )

    # Capture stderr so we can re-raise with the adapter's own
    # exception-type/message info; stdout (scaffold's success marker)
    # is routed to the worker log via the same fd inheritance as every
    # other subprocess in this module. A 600s timeout is generous —
    # the scaffold itself is file writes and launchctl invocations
    # that finish in seconds; the cap is a safety net against a hung
    # launchctl.
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=600,
    )
    # Mirror stdout to our own stdout for log visibility — the worker
    # has its fds redirected to ~/.pos/first-run.log, so this lands
    # there for the user to tail.
    if result.stdout:
        sys.stdout.write(result.stdout)
        sys.stdout.flush()
    if result.returncode == 0:
        return

    # Parse the first line of stderr as JSON; fall back to a generic
    # error if the runner died before emitting the structured payload.
    stderr_text = result.stderr or ""
    first_line = stderr_text.split("\n", 1)[0].strip()
    parsed: dict[str, Any] = {}
    if first_line.startswith("{"):
        try:
            parsed = json.loads(first_line)
        except json.JSONDecodeError:
            parsed = {}

    # Preserve the full stderr (including the traceback the runner
    # appended) in the worker log so post-mortem debugging works.
    if stderr_text:
        sys.stderr.write(stderr_text)
        sys.stderr.flush()

    exc_type = parsed.get("type") or "ScaffoldSubprocessFailure"
    exc_msg = parsed.get("message") or (
        f"scaffold runner exited {result.returncode}; stderr head: "
        f"{stderr_text[:200]!r}"
    )
    # Raise as a plain RuntimeError whose message is
    # "<exc_type>: <message>" so the caller's exception-stringifier
    # (``_emit_diag`` with ``f"{type(e).__name__}: {e}"``) naturally
    # surfaces the scaffold's own class name, e.g.
    # "PartialScaffoldError: partial-scaffold-detected". That matches
    # the pre-amendment surfacing for the same failure modes.
    raise RuntimeError(f"{exc_type}: {exc_msg}")


# ---- health verification --------------------------------------------


def _probe_http(host: str, port: int, path: str, timeout_s: float) -> bool:
    url = f"http://{host}:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            return resp.status == 200
    except (urllib.error.URLError, socket.error, TimeoutError):
        return False
    except Exception:  # pragma: no cover
        return False


def _probe_http_with_identity(
    host: str,
    port: int,
    path: str,
    timeout_s: float,
    *,
    expected_workspace_root: str,
) -> bool:
    """Return True iff the HTTP probe returns 200 AND the response
    body's ``workspace_root`` field matches ``expected_workspace_root``.

    Amendment #29 (AC29.5): the memory-sidecar's /health response
    carries a ``workspace_root`` field (populated from the process's
    ``POS_V2_WORKSPACE_ROOT`` env var, which the first-run scaffold
    injects via the launchd plist's ``EnvironmentVariables`` dict).
    The phase-4b probe verifies the responding sidecar's workspace
    identity equals the dispatching workspace's own root; mismatch
    or missing field is reported as not-healthy so the probe cannot
    be satisfied by an orphan sidecar or another workspace's sidecar.
    """
    url = f"http://{host}:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            if resp.status != 200:
                return False
            body = resp.read()
    except (urllib.error.URLError, socket.error, TimeoutError):
        return False
    except Exception:  # pragma: no cover
        return False
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    return payload.get("workspace_root") == expected_workspace_root


def _probe_unix_socket(socket_path: str, timeout_s: float) -> bool:
    resolved = Path(socket_path).expanduser()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout_s)
        s.connect(str(resolved))
        s.sendall(
            (
                json.dumps(
                    {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}
                )
                + "\n"
            ).encode("utf-8")
        )
        data = s.recv(4096)
        s.close()
        return bool(data)
    except (socket.error, FileNotFoundError, OSError):
        return False


def _service_health(
    svc: dict[str, Any],
    *,
    expected_workspace_root: str | None = None,
) -> bool:
    """Probe a single service and return whether it is healthy.

    Amendment #29 (AC29.5): when ``expected_workspace_root`` is
    provided and the service is HTTP-probed, verify the response
    body's ``workspace_root`` equals that value. The orchestrator's
    unix-socket probe is unaffected — its workspace identity is
    enforced by the socket path (workspace-local by construction)
    rather than by a payload field, so the identity gate is narrowly
    scoped to the HTTP path.
    """
    health = svc.get("health") or {}
    kind = health.get("kind")
    if kind == "http":
        if expected_workspace_root is not None:
            return _probe_http_with_identity(
                host=health.get("host", "127.0.0.1"),
                port=int(health.get("port", 0)),
                path=health.get("path", "/health"),
                timeout_s=float(health.get("timeout_s", 2.0)),
                expected_workspace_root=expected_workspace_root,
            )
        return _probe_http(
            host=health.get("host", "127.0.0.1"),
            port=int(health.get("port", 0)),
            path=health.get("path", "/health"),
            timeout_s=float(health.get("timeout_s", 2.0)),
        )
    if kind == "unix_socket":
        return _probe_unix_socket(
            socket_path=health.get("socket_path", ""),
            timeout_s=float(health.get("timeout_s", 2.0)),
        )
    return False


def _poll_services_healthy(
    services: list[dict[str, Any]],
    *,
    timeout_s: float,
    poll_interval_s: float,
    expected_workspace_root: str | None = None,
) -> tuple[bool, list[str]]:
    """Poll services until all healthy, up to ``timeout_s``.

    Amendment #29 (AC29.5): ``expected_workspace_root`` is passed
    through to ``_service_health`` so the HTTP probe verifies the
    responding sidecar belongs to the probing workspace.

    Returns (all_healthy, pending_labels).
    """
    deadline = time.monotonic() + float(timeout_s)
    while True:
        pending = [
            svc["label"]
            for svc in services
            if not _service_health(
                svc, expected_workspace_root=expected_workspace_root
            )
        ]
        if not pending:
            return True, []
        if time.monotonic() >= deadline:
            return False, pending
        time.sleep(max(0.05, float(poll_interval_s)))


# ---- self-retire -----------------------------------------------------


def _self_retire(
    *,
    pos_v2_root: Path,
    settings_path: Path,
    agent_handle: str | None = None,
) -> tuple[SettingsMergeResult, Path, bool]:
    """Rewrite settings.json to invoke the supervisor directly; delete first-run.sh.

    Returns (merge_result, removed_script_path, script_removed).

    Amendment #37: when ``agent_handle`` is provided, the post-retire
    ``settings.json`` carries the top-level ``"agent": <agent_handle>``
    field so a fresh Claude Code session selects the workspace persona
    as its default subagent (AC37.1). When ``None`` (the unwiring
    path or a degraded re-run), the field is left untouched —
    backwards-compat with every pre-amendment-#37 caller.
    """
    supervisor_stanza = build_supervisor_stanza(
        pos_v2_root,
        extra_inner_hooks=_extra_session_start_hooks(pos_v2_root),
    )
    merge_result = merge_session_start(
        settings_path=settings_path,
        new_entry=supervisor_stanza,
        agent_handle=agent_handle,
    )
    # Amendment #46: register the persona's UserPromptSubmit hook
    # alongside the supervisor SessionStart merge. Fail-soft per
    # AC46.4 — missing or broken primary-persona install degrades to
    # no-UserPromptSubmit-hook (pre-amendment-#46 behaviour).
    _maybe_merge_user_prompt_submit(
        pos_v2_root=pos_v2_root, settings_path=settings_path
    )
    # Amendment #48: register the persona's Stop hook alongside the
    # supervisor SessionStart + UserPromptSubmit merges. Fail-soft per
    # AC.M.4 — missing or broken primary-persona install degrades to
    # no-Stop-hook (pre-amendment-#48 behaviour).
    _maybe_merge_stop(
        pos_v2_root=pos_v2_root, settings_path=settings_path
    )
    # Amendment #49: register the renderer at top-level ``statusLine``
    # so Claude Code spawns it every ~1 s post-completion (the AC.SL.2
    # steady-state window) and on every future session that starts in
    # this workspace. Fail-soft — a settings.json I/O failure here
    # must not regress self-retire.
    _maybe_merge_status_line(
        pos_v2_root=pos_v2_root, settings_path=settings_path
    )
    # Structural-enforcement A2: register the objective-binding gate
    # under ``hooks.PreToolUse`` so every Edit/Write/MultiEdit fires
    # the gate before the model can author text. Fail-soft per locked
    # plan §5 fail-closed direction.
    _maybe_merge_pre_tool_use(
        pos_v2_root=pos_v2_root, settings_path=settings_path
    )

    script_path = pos_v2_root / "framework" / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    removed = False
    if script_path.exists():
        try:
            script_path.unlink()
            removed = True
        except OSError:
            removed = False
    else:
        removed = True  # already gone
    return merge_result, script_path, removed


def _verify_self_retire(
    *,
    pos_v2_root: Path,
    settings_path: Path,
) -> tuple[bool, list[str]]:
    """Phase 7: confirm Phase 6 landed."""
    problems: list[str] = []
    script_path = pos_v2_root / "framework" / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    if script_path.exists():
        problems.append(f"first-run.sh still exists at {script_path}")

    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        problems.append(f"cannot read settings.json after rewrite: {e}")
        return False, problems

    hooks = settings.get("hooks") or {}
    ss = hooks.get("SessionStart") or []
    if not isinstance(ss, list) or not ss:
        problems.append("SessionStart stanza is empty after rewrite")
        return False, problems
    first = ss[0]
    if not isinstance(first, dict):
        problems.append("SessionStart stanza first entry is not a mapping")
        return False, problems
    # Current Claude Code schema: SessionStart[i] is {matcher, hooks: [...]}.
    # Pull the first inner command entry out for verification.
    inner = first.get("hooks")
    if not isinstance(inner, list) or not inner or not isinstance(inner[0], dict):
        problems.append(
            "SessionStart stanza missing inner hooks array (schema regression)"
        )
        return False, problems
    cmd = inner[0].get("command", "")
    if "pos_session_start.py" not in cmd:
        problems.append(
            f"SessionStart command does not point at supervisor: {cmd!r}"
        )
    if "first-run.sh" in cmd:
        problems.append(
            f"SessionStart command still references first-run.sh: {cmd!r}"
        )
    return not problems, problems


# ---- state detection -------------------------------------------------


def _is_already_retired(pos_v2_root: Path, settings_path: Path) -> bool:
    """Truthy when first-run has already completed self-retire.

    Signature: ``first-run.sh`` gone AND settings.json SessionStart
    stanza points at the supervisor.
    """
    script_path = pos_v2_root / "framework" / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    if script_path.exists():
        return False
    if not settings_path.exists():
        return False
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    hooks = settings.get("hooks") or {}
    ss = hooks.get("SessionStart") or []
    if not isinstance(ss, list) or not ss:
        return False
    first = ss[0]
    if not isinstance(first, dict):
        return False
    # Current Claude Code schema: SessionStart[i] is {matcher, hooks: [...]}.
    inner = first.get("hooks")
    if not isinstance(inner, list) or not inner or not isinstance(inner[0], dict):
        return False
    cmd = inner[0].get("command", "")
    return "pos_session_start.py" in cmd and "first-run.sh" not in cmd


# ---- confirmation sentence ------------------------------------------


def _confirmation_sentence(
    *,
    merge_result: SettingsMergeResult,
    service_labels: list[str],
) -> str:
    """Per proposal Q2 — extend Amendment 4's sentence with first-run bits.

    The first-run extensions:
      * names the venvs created (shared + dedicated)
      * names the services that came up healthy
      * notes any displaced user SessionStart stanza (Tier-A-analogue
        surfacing of a potentially-impactful autonomous decision)
    """
    parts = [
        "pos v2 first-run complete: Python 3.13 venv ready,",
        "twelve components installed, memory sidecar and orchestrator",
        f"launched as user services ({', '.join(service_labels)}),",
        "~/.pos/ scaffolded.",
    ]
    if merge_result.prior_session_start_displaced and merge_result.backup_path:
        parts.append(
            "Your pre-existing .claude/settings.json SessionStart hook"
            f" was backed up to {merge_result.backup_path.name}"
            " — pos-v2's hook is authoritative going forward; restore"
            " manually if needed."
        )
    parts.append(
        "Edit ~/.pos/*.yaml to adjust any default. Proceeding."
    )
    return " ".join(parts)


# ---- top-level orchestration ----------------------------------------


def _ensure_shared_venv(pos_v2_root: Path) -> Path:
    """Create ``pos_v2_root/.venv`` with the currently-running Python.

    Added by the 2026-04-22 session-start-detachment amendment. Prior
    to this amendment, venv creation happened inline in ``first-run.sh``
    before handing off to this helper. With the shell hook now thin
    (returns in <5s), the heavy work — including the initial venv
    creation — moves here.

    Returns the absolute path to the venv's python interpreter. No-op
    when the venv already exists and has a usable interpreter.

    We intentionally use ``sys.executable`` (the interpreter currently
    running the helper) rather than re-detecting ``python3.13`` on
    PATH: the dispatch already found and validated the correct
    interpreter, passed it on the command line, and exec'd us with it.
    The venv should inherit from the same interpreter for
    cross-platform consistency.
    """
    venv_dir = pos_v2_root / ".venv"
    venv_python = venv_dir / "bin" / "python"
    if venv_python.exists():
        return venv_python

    _advance_state(
        "running",
        phase="phase-2-venv-creation",
        detail=f"creating shared virtual environment at {venv_dir}",
    )
    # Use sys.executable so the venv is built from the same interpreter
    # that the dispatch detected. Short timeout — venv creation is
    # cheap (~5-10s); a minute is a generous ceiling.
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
            capture_output=True,
            timeout=60,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"venv-creation-failed: {(e.stderr or b'').decode('utf-8', errors='replace')[-500:]}"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("venv-creation-failed: timed out after 60s")

    if not venv_python.exists():
        raise RuntimeError(
            f"venv-creation-failed: no python at {venv_python} after create"
        )
    return venv_python


def _run_bootstrap(*, pos_v2_root: Path, inventory_path: Path) -> int:
    """Phases 2..7 in order. Returns a process exit code (always 0).

    Phase 2 (venv creation) was previously handled inline in
    first-run.sh but moved here with the 2026-04-22 detachment
    amendment — the shell hook is now thin and only resolves the
    Python interpreter; venv creation is part of the detached worker's
    responsibility.
    """

    progress = get_progress()
    # Announce "running" before any heavy work: the hook's reader sees
    # this promptly and knows the worker is alive past the spawn line.
    _advance_state("running", phase="phase-2-venv-creation")

    # ---- Phase 2: shared venv --------------------------------------
    try:
        _ensure_shared_venv(pos_v2_root)
    except RuntimeError as e:
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            f"hands-off-lifecycle-internal:{e}",
            str(e),
            "Venv creation failed. Check disk space and permissions on\n"
            f"{pos_v2_root}, then reopen claude to retry.",
            user_what="could not create the shared Python virtual environment.",
            user_remediation=(
                "check disk space and permissions on your pos-v2 directory, "
                "then reopen claude to retry."
            ),
        )
        return 0

    # ---- Phase 3a: parse inventory --------------------------------
    _advance_state("running", phase="phase-3a-inventory")
    try:
        inventory = load_inventory(inventory_path)
        validate_inventory(inventory)
    except InventoryParseError as e:
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            "hands-off-lifecycle-internal:inventory-parse-failed",
            str(e),
            "This is a shipped-artifact defect in pos-v2 itself. File\n"
            "an issue against the repo with the inventory file content\n"
            "and the error text above.",
            user_what="pos-v2's bundled install manifest is corrupt.",
            user_remediation=(
                "this is a bug in pos-v2 itself, not in your machine.\n"
                "re-clone the repo or file an issue; next reopen retries."
            ),
        )
        return 0

    # Amendment #6: resolve the per-workspace slug in service labels
    # before anything downstream consumes them. Invalid slug = refuse
    # structurally rather than probe unnamespaced labels.
    try:
        slug = _workspace_slug(pos_v2_root)
    except ValueError as e:
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            f"hands-off-lifecycle-internal:{e}",
            str(e),
            "The pos-v2 workspace directory name contains no characters\n"
            "that survive slug sanitisation. Rename the workspace\n"
            "directory to something matching [a-z0-9-]+, then reopen.",
            user_what="workspace directory name cannot be turned into a service slug.",
            user_remediation=(
                "rename the workspace directory to use letters, digits, and\n"
                "hyphens (e.g. `pos-v2`), then reopen claude."
            ),
        )
        return 0
    try:
        inventory = resolve_service_labels(inventory, slug)
    except InventoryParseError as e:
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            f"hands-off-lifecycle-internal:inventory-label-template:{e}",
            str(e),
            "The first-run inventory declares a service label template\n"
            "with an unknown placeholder. This is a shipped-artifact\n"
            "defect — file an issue.",
            user_what="pos-v2's bundled install manifest has a bad label template.",
            user_remediation=(
                "this is a bug in pos-v2 itself. file an issue with the error above."
            ),
        )
        return 0

    shared = inventory["shared_venv"]
    shared_venv_path = pos_v2_root / shared["path"]
    shared_python = shared_venv_path / "bin" / "python"

    # ---- Phase 3b: shared-venv pip installs -----------------------
    # AC2 bound: advertise the phase's expected duration up front so
    # the per-component lines below arrive in a context the user has
    # already been told to expect.
    _advance_state(
        "running",
        phase="phase-3b-shared-deps",
        detail="installing per-component requirements.txt (longest: memory-system, 3-5 minutes)",
    )
    progress.step(
        "installing component dependencies — this takes 1-3 minutes on first run..."
    )
    print("pos v2 first-run: installing shared-venv components...")
    shared_outcomes = _install_shared_components(
        pos_v2_root=pos_v2_root,
        shared_venv_python=shared_python,
        component_names=list(shared["components"]),
    )
    for outcome in shared_outcomes:
        if not outcome.ok:
            _emit_diag(
                ERR_PIP_INSTALL_FAILED,
                f"pip-install-failed:{outcome.component}",
                outcome.stderr_tail or f"returncode {outcome.returncode}",
                "Next session will retry from this component. If this is a\n"
                "network or proxy issue, resolve it before reopening. If a\n"
                "dependency cannot resolve, inspect\n"
                f"{outcome.requirements_path} and adjust the pin.",
                user_what=(
                    f"could not install dependencies for {outcome.component}."
                ),
                user_remediation=(
                    "check your network or proxy settings, then reopen claude — "
                    "the next session picks up from this component automatically."
                ),
            )
            return 0

    # ---- Phase 3e: per-component editable installs ----------------
    # Discover every component shipping a pyproject.toml, topologically
    # order by declared sibling dependencies, and ``pip install -e``
    # each into the shared venv. Without this, cross-component imports
    # (``import pos_orchestrator`` etc.) fail on fresh clone and the
    # Phase 4 scaffold raises ``ImportError`` → -32099 scaffold-failed.
    _advance_state(
        "running",
        phase="phase-3e-editable-installs",
        detail="registering component packages (pip install -e)",
    )
    progress.step(
        "registering component packages — this takes about a minute..."
    )
    print("pos v2 first-run: installing component packages (editable)...")
    try:
        editable_outcomes = _install_editable_components(
            pos_v2_root=pos_v2_root,
            shared_venv_python=shared_python,
        )
    except RuntimeError as e:
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            f"hands-off-lifecycle-internal:{e}",
            "The component dependency graph declared a cycle — this is a\n"
            "shipped-artifact defect in pos-v2 pyproject.toml files.",
            "File an issue with the component names reported above; fix\n"
            "the cycle by breaking one of the declared sibling deps.",
            user_what="pos-v2's bundled components form a dependency cycle.",
            user_remediation=(
                "this is a bug in pos-v2 itself, not in your machine.\n"
                "file an issue with the component names in the error payload above."
            ),
        )
        return 0
    for outcome in editable_outcomes:
        if not outcome.ok:
            _emit_diag(
                ERR_PIP_INSTALL_FAILED,
                f"pip-install-failed:editable:{outcome.component}",
                outcome.stderr_tail or f"returncode {outcome.returncode}",
                "Next session will retry from this component. This is the\n"
                "editable-install phase (pip install -e) — failures here\n"
                "usually indicate a malformed pyproject.toml or missing\n"
                "build-system requirements. Inspect the component's\n"
                "pyproject.toml and adjust accordingly.",
                user_what=(
                    f"could not register the {outcome.component} package."
                ),
                user_remediation=(
                    "reopen claude to retry. if the failure repeats, this is\n"
                    "a shipped-artifact defect in pos-v2 — file an issue."
                ),
            )
            return 0

    # ---- Phase 3c: dedicated-venv pip installs --------------------
    _advance_state(
        "running",
        phase="phase-3c-dedicated-venvs",
        detail="installing dedicated-venv components (heavy deps — graphiti, kuzu)",
    )
    service_labels: list[str] = []
    for entry in inventory.get("dedicated_venvs", []):
        print(f"pos v2 first-run: installing dedicated-venv component {entry['component']}...")
        _, outcome = _install_dedicated_venv(
            pos_v2_root=pos_v2_root,
            shared_python=shared_python,
            entry=entry,
        )
        if not outcome.ok:
            _emit_diag(
                ERR_PIP_INSTALL_FAILED,
                f"pip-install-failed:{outcome.component}",
                outcome.stderr_tail or f"returncode {outcome.returncode}",
                "Next session will retry. Heavy deps (Graphiti, Kuzu)\n"
                "can take 60-90s on a cold cache — if this was a timeout,\n"
                "try again with a warm cache. If the failure is a\n"
                "resolution issue, inspect the requirements file and\n"
                "adjust the pin.",
            )
            return 0

    # ---- Phase 3d: settings.json authorship -----------------------
    # While first-run is still live, keep the stanza pointing at
    # first-run.sh. Phase 6 rewrites this to the supervisor path.
    settings_path = pos_v2_root / ".claude" / "settings.json"
    first_run_stanza = build_first_run_stanza(
        pos_v2_root,
        extra_inner_hooks=_extra_session_start_hooks(pos_v2_root),
    )
    merge_result = merge_session_start(
        settings_path=settings_path,
        new_entry=first_run_stanza,
    )
    # Amendment #46: register the persona's UserPromptSubmit hook at
    # Phase 3d so the workspace's first user-prompt after first-run
    # gets memory retrieval. Fail-soft per AC46.4.
    _maybe_merge_user_prompt_submit(
        pos_v2_root=pos_v2_root, settings_path=settings_path
    )
    # Amendment #48: register the persona's Stop hook at Phase 3d so
    # every turn-close after first-run drives the per-turn aggregated
    # episode write. Fail-soft per AC.M.4.
    _maybe_merge_stop(
        pos_v2_root=pos_v2_root, settings_path=settings_path
    )
    # Amendment #49: register the renderer at top-level ``statusLine``
    # at Phase 3d so the live first-run progress is visible in the
    # current session's terminal — not just on subsequent sessions
    # post-self-retire. Fail-soft per locked plan §5.
    _maybe_merge_status_line(
        pos_v2_root=pos_v2_root, settings_path=settings_path
    )
    # Structural-enforcement A2: register the objective-binding gate
    # at Phase 3d so the gate is live for the current session's first
    # PreToolUse fire (not just subsequent sessions post-self-retire).
    # Fail-soft per locked plan §5.
    _maybe_merge_pre_tool_use(
        pos_v2_root=pos_v2_root, settings_path=settings_path
    )

    # ---- Phase 4a: plist / unit substitution + service bootstrap --
    plat = _detect_platform()
    if plat != "macos":
        _emit_diag(
            ERR_PLATFORM_UNSUPPORTED,
            f"platform-unsupported:{plat}",
            "launchd is required for service bootstrap.",
            "pos-v2 supports macOS. Other platforms are out of scope.",
        )
        return 0

    _advance_state(
        "running",
        phase="phase-4a-scaffold",
        detail="substituting service-manager files and bootstrapping services",
    )
    print("pos v2 first-run: substituting service-manager files and bootstrapping services...")
    try:
        _invoke_first_run_scaffold(
            pos_v2_root=pos_v2_root,
            shared_venv_python=shared_python,
            service_bootstrap=True,
        )
    except Exception as e:
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            "hands-off-lifecycle-internal:scaffold-failed",
            f"{type(e).__name__}: {e}",
            "The workspace-bootstrap first-run scaffold raised. This is\n"
            "a shipped-artifact defect; re-running next session may\n"
            "succeed if the cause is transient.",
        )
        return 0

    # ---- Phase 4c: agent-file authorship (amendment #37) ----------
    #
    # AC37.1 + AC37.2: render
    # ``<workspace>/.claude/agents/<handle>.md`` from amendment #35's
    # ``to_agent_md(contract)`` against the persona-directory the
    # workspace-bootstrap scaffold (Phase 4a; amendment #36) just
    # materialised, then merge ``"agent": "<handle>"`` into
    # ``<workspace>/.claude/settings.json`` so a fresh Claude Code
    # session selects the workspace persona as its default subagent.
    #
    # Graceful-degradation contract (AC37.4): any failure here is
    # non-fatal — the persona scaffold is already in place, the
    # session can proceed as generic-Claude with the context-load
    # gate's additionalContext (amendment #32). We surface a
    # structured diagnostic via ``_advance_state`` and continue.
    #
    # Method (D-build.1 / D-build.2 / D-build.3 / D-build.4 — see
    # amendment-37 plan §11):
    #  - Render via ``agent_file_runner.py`` subprocess under the
    #    shared venv (the renderer needs pydantic + pyyaml +
    #    opentelemetry; the worker is stdlib-only).
    #  - Write atomically via ``write_agent_file()`` with write-only-
    #    if-different policy.
    #  - Merge the ``"agent"`` field into settings.json via the
    #    generalised ``merge_session_start(agent_handle=...)``.
    #  - Diagnostic via ``_advance_state`` (status=running, phase=
    #    phase-4c-agent-file-authorship, detail names the failure
    #    class).
    _advance_state(
        "running",
        phase="phase-4c-agent-file-authorship",
        detail="rendering .claude/agents/<handle>.md from persona contract",
    )
    print(
        "pos v2 first-run: rendering .claude/agents/<handle>.md from persona contract..."
    )
    agent_handle: str | None = None
    try:
        agent_runner = _HOOKS_DIR / "agent_file_runner.py"
        run_result = subprocess.run(
            [
                str(shared_python),
                "-u",
                str(agent_runner),
                "--workspace-root",
                str(pos_v2_root),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if run_result.returncode == 0:
            try:
                envelope = json.loads(run_result.stdout)
            except json.JSONDecodeError as e:
                _advance_state(
                    "running",
                    phase="phase-4c-agent-file-authorship",
                    detail=(
                        "agent-file-render-output-malformed: "
                        f"{type(e).__name__}: {e}"
                    ),
                )
                envelope = None
            if isinstance(envelope, dict):
                handle = envelope.get("handle")
                body = envelope.get("body")
                if isinstance(handle, str) and handle and isinstance(body, str):
                    write_result = write_agent_file(
                        workspace_root=pos_v2_root,
                        handle=handle,
                        body=body,
                    )
                    if write_result.wrote or write_result.reason == "skipped-identical":
                        agent_handle = handle
                        _advance_state(
                            "running",
                            phase="phase-4c-agent-file-authorship",
                            detail=(
                                f"agent-file {write_result.reason} at "
                                f"{write_result.path}"
                            ),
                        )
                    else:
                        _advance_state(
                            "running",
                            phase="phase-4c-agent-file-authorship",
                            detail=(
                                f"agent-file-write-failed:{write_result.reason}: "
                                f"{write_result.error_detail}"
                            ),
                        )
                else:
                    _advance_state(
                        "running",
                        phase="phase-4c-agent-file-authorship",
                        detail=(
                            "agent-file-render-envelope-missing-fields: "
                            f"keys={sorted(envelope) if isinstance(envelope, dict) else type(envelope).__name__}"
                        ),
                    )
        else:
            # Render failure — JSON payload on stderr line 1, traceback
            # in plain text after. Capture the JSON for the diagnostic.
            stderr_text = run_result.stderr or ""
            first_line = stderr_text.split("\n", 1)[0].strip()
            parsed: dict[str, Any] = {}
            if first_line.startswith("{"):
                try:
                    parsed = json.loads(first_line)
                except json.JSONDecodeError:
                    parsed = {}
            _advance_state(
                "running",
                phase="phase-4c-agent-file-authorship",
                detail=(
                    "agent-file-render-failed: "
                    f"rc={run_result.returncode} "
                    f"type={parsed.get('type', 'Unknown')} "
                    f"message={parsed.get('message', stderr_text[:200])!r}"
                ),
            )
    except subprocess.TimeoutExpired:
        _advance_state(
            "running",
            phase="phase-4c-agent-file-authorship",
            detail="agent-file-render-timeout: subprocess exceeded 60s",
        )
    except Exception as e:  # noqa: BLE001 — graceful-degradation per AC37.4
        # Any unexpected failure — surface as a diagnostic and proceed.
        # Hard-halt would defeat the v1.0 line 153 contract by making a
        # transient environmental issue take down session-start.
        _advance_state(
            "running",
            phase="phase-4c-agent-file-authorship",
            detail=(
                "agent-file-render-unexpected: "
                f"{type(e).__name__}: {e}"
            ),
        )

    # Re-merge settings.json now that we have the resolved agent
    # handle (AC37.1). This is additive over the Phase 3d merge; the
    # SessionStart stanza is left in place (still pointing at first-
    # run.sh until Phase 6 rewrites it). When ``agent_handle`` is
    # None (Phase 4c failure path) the merge is a no-op for the
    # ``"agent"`` field — the previous Phase 3d state is preserved.
    if agent_handle is not None:
        try:
            merge_result = merge_session_start(
                settings_path=settings_path,
                new_entry=build_first_run_stanza(
                    pos_v2_root,
                    extra_inner_hooks=_extra_session_start_hooks(pos_v2_root),
                ),
                agent_handle=agent_handle,
            )
            # Amendment #46: re-merge the UserPromptSubmit hook
            # alongside the Phase 4c re-merge. Idempotent — the
            # merge writes the same envelope shape every time.
            _maybe_merge_user_prompt_submit(
                pos_v2_root=pos_v2_root, settings_path=settings_path
            )
            # Amendment #48: re-merge the Stop hook alongside the
            # Phase 4c re-merge. Idempotent.
            _maybe_merge_stop(
                pos_v2_root=pos_v2_root, settings_path=settings_path
            )
            # Amendment #49: re-merge the statusLine entry alongside
            # the Phase 4c re-merge. Idempotent — same envelope
            # shape every time.
            _maybe_merge_status_line(
                pos_v2_root=pos_v2_root, settings_path=settings_path
            )
            # Structural-enforcement A2: re-merge the objective-binding
            # gate alongside the Phase 4c re-merge. Idempotent — same
            # envelope shape every time.
            _maybe_merge_pre_tool_use(
                pos_v2_root=pos_v2_root, settings_path=settings_path
            )
        except OSError as e:
            # Settings.json unwriteable — surface a diagnostic. The
            # supervisor stanza rewrite at Phase 6 will retry the
            # merge and may succeed if the failure is transient.
            _advance_state(
                "running",
                phase="phase-4c-agent-file-authorship",
                detail=(
                    "agent-field-merge-failed: "
                    f"{type(e).__name__}: {e}"
                ),
            )

    # ---- Phase 4b: health poll ------------------------------------
    services = list(inventory.get("services", []))
    service_labels = [svc["label"] for svc in services]
    _advance_state(
        "running",
        phase="phase-4b-health-poll",
        detail=f"polling services for health: {', '.join(service_labels)}",
    )
    print(f"pos v2 first-run: polling services for health ({', '.join(service_labels)})...")
    healthy, pending = _poll_services_healthy(
        services=services,
        timeout_s=60.0,  # < the 120s hook ceiling, room for self-retire below.
        poll_interval_s=0.5,
        # Amendment #29 (AC29.5): identity-aware probe — only the
        # dispatching workspace's own sidecar can satisfy phase-4b.
        # An orphan sidecar, or another workspace's sidecar reached
        # via port collision, carries a mismatched
        # ``POS_V2_WORKSPACE_ROOT`` env and cannot complete the probe.
        expected_workspace_root=str(pos_v2_root),
    )
    if not healthy:
        _emit_diag(
            ERR_SERVICE_HEALTH_TIMEOUT,
            f"service-health-timeout:{','.join(pending)}",
            f"services did not report healthy within budget: {pending}",
            "Next session will retry. Check service logs:\n"
            "  ~/.pos/logs/ and ~/.pos/logs/*.err\n"
            "Inspect the launchd status:\n"
            "  launchctl print gui/$(id -u)/<LABEL>",
        )
        return 0

    # ---- Phase 5: confirmation sentence ---------------------------
    _advance_state(
        "running",
        phase="phase-5-confirmation",
        detail="all phases succeeded; writing confirmation",
    )
    confirmation = _confirmation_sentence(
        merge_result=merge_result,
        service_labels=service_labels,
    )
    print(confirmation)

    # ---- Phase 6: self-retire -------------------------------------
    _advance_state(
        "running",
        phase="phase-6-self-retire",
        detail="rewriting .claude/settings.json to supervisor stanza",
    )
    # Amendment #37: thread the resolved agent handle through self-
    # retire so the post-retire settings.json carries the
    # ``"agent": "<handle>"`` field (AC37.1). When Phase 4c failed to
    # resolve a handle (graceful-degradation path), ``agent_handle``
    # is None and the retire merge leaves the field untouched —
    # whatever Phase 3d / Phase 4c last wrote remains.
    retire_merge, script_path, removed = _self_retire(
        pos_v2_root=pos_v2_root,
        settings_path=settings_path,
        agent_handle=agent_handle,
    )
    if not removed:
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            "hands-off-lifecycle-internal:self-retire-script-remove-failed",
            f"could not delete {script_path}",
            "Remove the file manually and restart the session. The\n"
            "settings.json stanza has been rewritten to invoke the\n"
            "supervisor directly — only the stale first-run.sh needs\n"
            "manual cleanup.",
        )
        return 0

    # ---- Phase 7: final-state verification ------------------------
    ok, problems = _verify_self_retire(
        pos_v2_root=pos_v2_root,
        settings_path=settings_path,
    )
    if not ok:
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            "hands-off-lifecycle-internal:self-retire-verification-failed",
            "; ".join(problems),
            "First-run believed it retired but the final-state check\n"
            "failed. Inspect .claude/settings.json and\n"
            "hands-off-lifecycle/hooks/ manually. This is a bug in\n"
            "first-run; file an issue with the output above.",
        )
        return 0

    # Terminal state — tell the next SessionStart hook it can short-
    # circuit straight to the supervisor.
    _advance_state(
        "completed",
        phase="complete",
        detail="first-run finished; supervisor stanza active",
    )
    return 0


def _run_resume(*, pos_v2_root: Path, inventory_path: Path) -> int:
    """Resume or verify-already-complete path.

    Called by first-run.sh when the shared venv already exists. Three
    outcomes:
      * self-retire already landed → we should not have been invoked;
        exit silently (the stale hook will not fire again after
        session close).
      * venv exists but setup is incomplete → re-run bootstrap phases.
      * full completion → emit a short 'already-complete' marker and
        schedule self-retire (same as bootstrap's Phase 6..7).
    """
    settings_path = pos_v2_root / ".claude" / "settings.json"
    if _is_already_retired(pos_v2_root, settings_path):
        # Defensive silence — we should not be running.
        return 0
    # The venv exists but the stanza still points at first-run.sh. This
    # means a prior first-run ran partially and exited before Phase 6.
    # Re-invoke the full bootstrap; Phase 3 pip installs are idempotent,
    # Phase 4 service bootstrap is idempotent, Phase 6 is the point of
    # the re-run.
    return _run_bootstrap(pos_v2_root=pos_v2_root, inventory_path=inventory_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="pos-v2 first-run helper (Phase 3 onward).",
    )
    parser.add_argument("--pos-v2-root", required=True)
    parser.add_argument(
        "--mode",
        choices=("bootstrap", "resume"),
        default="bootstrap",
    )
    parser.add_argument(
        "--inventory",
        default=None,
        help="Override path to first-run-inventory.yaml (default: <root>/first-run-inventory.yaml).",
    )
    # Detachment-amendment arguments (2026-04-22). The SessionStart
    # hook spawns this helper detached; these flags let the spawned
    # worker know which pos-root to write state into and which
    # generation counter to tag log lines with.
    parser.add_argument(
        "--pos-root",
        default=None,
        help="Override ~/.pos/ for state/log files (test/override hook).",
    )
    parser.add_argument(
        "--generation",
        type=int,
        default=1,
        help="Worker generation counter (for log-line tagging across respawns).",
    )
    args = parser.parse_args(argv)

    pos_v2_root = Path(args.pos_v2_root).resolve()
    inventory_path = Path(
        args.inventory or (pos_v2_root / "first-run-inventory.yaml")
    ).resolve()

    # Wire state-file location into module globals so _advance_state()
    # picks them up without threading the config through every helper.
    # The ENABLED flag flips on here so tests that import + call
    # _emit_diag directly do not pollute ~/.pos/ or any workspace tree.
    #
    # Amendment #28: state is per workspace
    # (``<workspace>/.pos/first-run.state``); the host-global
    # ``_STATE_POS_ROOT`` continues to own the progress log path.
    global _STATE_POS_ROOT, _STATE_WORKSPACE_ROOT
    global _STATE_GENERATION, _STATE_WRITES_ENABLED
    if args.pos_root:
        _STATE_POS_ROOT = Path(args.pos_root).expanduser().resolve()
    _STATE_WORKSPACE_ROOT = pos_v2_root
    _STATE_GENERATION = int(args.generation)
    _STATE_WRITES_ENABLED = True

    if not pos_v2_root.is_dir():
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            "hands-off-lifecycle-internal:pos-v2-root-not-a-directory",
            str(pos_v2_root),
            "First-run was invoked with a non-existent workspace root.\n"
            "This is a bug; file an issue.",
        )
        return 0

    try:
        if args.mode == "bootstrap":
            return _run_bootstrap(
                pos_v2_root=pos_v2_root, inventory_path=inventory_path
            )
        return _run_resume(pos_v2_root=pos_v2_root, inventory_path=inventory_path)
    except Exception as e:
        # Belt-and-suspenders: any uncaught exception inside the
        # worker must land a "failed" state so the next SessionStart
        # hook surfaces it instead of the user seeing pure silence.
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            f"hands-off-lifecycle-internal:uncaught-exception:{type(e).__name__}",
            repr(e),
            "An unexpected exception escaped the first-run worker.\n"
            "Inspect ~/.pos/first-run.log for the last recorded phase,\n"
            "then reopen claude to retry. If this repeats, file an issue\n"
            "with the log contents.",
            user_what="first-run worker crashed unexpectedly.",
            user_remediation=(
                "reopen claude to retry. the next session will pick up\n"
                "where this left off; if the same failure repeats, this\n"
                "is a bug — file an issue with ~/.pos/first-run.log."
            ),
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
