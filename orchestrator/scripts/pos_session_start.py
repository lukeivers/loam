"""Session-start helper script (Amendment 2 — hands-off-lifecycle).

Invoked by the Claude Code ``SessionStart`` hook (type: ``command``).
Probes the memory sidecar + orchestrator; if either is down, asks
``launchctl`` to bring it up (non-blocking, FD-safe); reports a
one-line additionalContext to Claude.

**Critical: the v2.1.87 FD-inheritance bug mitigation.** This script
NEVER spawns a long-lived background process inheriting Claude Code's
stdin/stdout/stderr. launchd is the thing that actually supervises
the long-lived process. The hook is a trigger — short-lived,
synchronous, exits promptly.

Exit code convention:
    0 → services up (either were already up, or came up within budget)
    2 → platform unsupported (no launchctl)
    3 → services did not come up within the budget; supervisor will
        escalate loudly once running

The script is importable so tests can exercise it without subprocess.
Amendment #10 (linux-removal) dropped the systemd-user branch.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---- platform detection ---------------------------------------------


def detect_platform() -> str:
    s = sys.platform.lower()
    if s == "darwin":
        return "macos"
    return s


def _which(binary: str) -> str | None:
    for d in (os.environ.get("PATH") or "").split(os.pathsep):
        p = Path(d) / binary
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
    return None


# ---- probes ----------------------------------------------------------


@dataclass(frozen=True)
class ProbeOutcome:
    memory_up: bool
    orchestrator_up: bool
    memory_latency_ms: float = 0.0
    errors: tuple[str, ...] = ()


def probe_memory(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    health_path: str = "/health",
    timeout_s: float = 2.0,
) -> tuple[bool, float, str | None]:
    url = f"http://{host}:{port}{health_path}"
    start = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            ok = resp.status == 200
            latency_ms = (time.monotonic() - start) * 1000.0
            return ok, latency_ms, None
    except (urllib.error.URLError, socket.error, TimeoutError) as e:
        return False, (time.monotonic() - start) * 1000.0, f"{type(e).__name__}: {e}"
    except Exception as e:  # pragma: no cover
        return False, (time.monotonic() - start) * 1000.0, f"{type(e).__name__}: {e}"


def probe_orchestrator(
    *,
    socket_path: str | Path = Path.home() / ".pos" / "orchestrator.sock",
    timeout_s: float = 2.0,
) -> tuple[bool, str | None]:
    path = Path(socket_path).expanduser()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout_s)
        s.connect(str(path))
        # Send a JSON-RPC ping; the orchestrator's IPC responds with pong.
        s.sendall(
            (
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "ping",
                        "params": {},
                    }
                )
                + "\n"
            ).encode("utf-8")
        )
        data = s.recv(4096)
        s.close()
        return bool(data), None
    except (socket.error, FileNotFoundError, OSError) as e:
        return False, f"{type(e).__name__}: {e}"


# ---- service-manager bring-up (FD-safe) ----------------------------


def ask_service_manager_to_start(
    *,
    plat: str,
    memory_label: str = "com.pos-v2.memory-graphiti",
    orchestrator_label: str = "com.pos.orchestrator",
    launch_agents_dir: Path | None = None,
) -> list[str]:
    """Ask launchd to bring services up.

    Non-blocking: these commands *request* launchd to launch; they do
    NOT themselves spawn a child inheriting Claude's FDs. This is the
    v2.1.87 issue #43123 mitigation — FD safety is delegated to
    launchd.

    Returns a list of warning messages (empty on success). Does not
    raise on launchd error; the caller's probe-again step catches
    that case.
    """
    warnings: list[str] = []
    if plat != "macos":
        warnings.append(f"platform-unsupported:{plat}")
        return warnings
    binary = _which("launchctl") or "/bin/launchctl"
    uid = os.getuid()
    dir_ = launch_agents_dir or (Path.home() / "Library" / "LaunchAgents")
    for label in (memory_label, orchestrator_label):
        plist = dir_ / f"{label}.plist"
        if not plist.exists():
            warnings.append(f"{label}.plist not installed at {plist}")
            continue
        try:
            subprocess.run(
                [binary, "bootstrap", f"gui/{uid}", str(plist)],
                check=False,
                capture_output=True,
                timeout=15,
            )
        except Exception as e:
            warnings.append(f"launchctl bootstrap {label}: {e}")
    return warnings


# ---- top-level orchestration ---------------------------------------


def run_session_start(
    *,
    probe_memory_fn: Any | None = None,
    probe_orchestrator_fn: Any | None = None,
    service_manager_fn: Any | None = None,
    platform_override: str | None = None,
    bring_up_timeout_s: float = 15.0,
    bring_up_poll_interval_s: float = 0.5,
) -> dict[str, Any]:
    """Main entry. Returns a dict for caller consumption.

    Shape:
        {
          "status": "ready" | "partial" | "platform-unsupported",
          "memory_up": bool,
          "orchestrator_up": bool,
          "additional_context": "pos v2 ready" | <named diagnostic>,
          "exit_code": int,
        }
    """
    plat = platform_override or detect_platform()
    pm = probe_memory_fn or (lambda: probe_memory())
    po = probe_orchestrator_fn or (lambda: probe_orchestrator())

    if plat != "macos":
        return {
            "status": "platform-unsupported",
            "memory_up": False,
            "orchestrator_up": False,
            "additional_context": (
                f"pos v2 session-start: platform-unsupported:{plat} — "
                "launchd is required. See docs/platforms.md for the "
                "supported-platform matrix."
            ),
            "exit_code": 2,
        }

    m_ok, m_lat, m_err = pm()
    o_ok, o_err = po()
    if m_ok and o_ok:
        return {
            "status": "ready",
            "memory_up": True,
            "orchestrator_up": True,
            "additional_context": "pos v2 ready",
            "exit_code": 0,
        }

    # Ask the service manager to bring things up (non-blocking).
    smf = service_manager_fn or (lambda: ask_service_manager_to_start(plat=plat))
    warnings = smf()

    # Poll for them to become healthy, up to the budget.
    deadline = time.monotonic() + float(bring_up_timeout_s)
    while time.monotonic() < deadline:
        m_ok, m_lat, m_err = pm()
        o_ok, o_err = po()
        if m_ok and o_ok:
            return {
                "status": "ready",
                "memory_up": True,
                "orchestrator_up": True,
                "additional_context": "pos v2 ready",
                "exit_code": 0,
            }
        time.sleep(max(0.01, float(bring_up_poll_interval_s)))

    # Did not come up within the budget — return partial but keep
    # additionalContext helpful; the supervisor will escalate loudly.
    return {
        "status": "partial",
        "memory_up": m_ok,
        "orchestrator_up": o_ok,
        "additional_context": (
            "pos v2 session-start: services did not come up within "
            f"{bring_up_timeout_s:.0f}s "
            f"(memory_up={m_ok}, orchestrator_up={o_ok}). Supervisor "
            "will escalate loudly on start. "
            f"Warnings: {', '.join(warnings) if warnings else 'none'}."
        ),
        "exit_code": 3,
    }


# ---- amendment #49 — existing-workspace statusLine retrofit ---------
#
# Per locked plan `docs/rebuild/plans/bootstrap-progress-statusline.md`
# §6 D-build.5 + decision D5 (LOCKED 2026-04-26): the supervisor's
# settings-touch path calls `merge_status_line` so a workspace whose
# first-run already completed before amendment #49 landed picks up
# the top-level `statusLine` entry on its next supervisor session-
# start (AC.SL.8). Fail-soft: any failure here must NOT block the
# supervisor's main path — the retrofit is additive UX, not load-
# bearing.


def _maybe_install_status_line(pos_v2_root: Path) -> None:
    """Existing-workspace retrofit for the top-level ``statusLine`` entry.

    Mirrors the ``_maybe_merge_status_line`` shape used by the worker
    side (``first_run_helper.py``) but lives on the supervisor path
    so workspaces already past first-run gain the entry without re-
    bootstrapping. Lazy-imports `merge_status_line` from the hooks
    directory; any exception is swallowed so the supervisor's main
    path is never blocked.

    Per locked plan §5 fail-closed direction.
    """
    try:
        hooks_dir = pos_v2_root / "hands-off-lifecycle" / "hooks"
        if not hooks_dir.is_dir():
            return
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))
        # Lazy import — the supervisor must not crash on a workspace
        # whose hooks directory is in an unexpected shape.
        from first_run_settings import merge_status_line  # type: ignore[import-not-found]

        settings_path = pos_v2_root / ".claude" / "settings.json"
        script = hooks_dir / "statusline.py"
        new_entry: dict[str, Any] = {
            "type": "command",
            "command": f"{sys.executable} {script}",
            "refreshInterval": 1,
        }
        merge_status_line(
            settings_path=settings_path,
            new_entry=new_entry,
        )
    except Exception:  # noqa: BLE001 — fail-soft per locked plan §5
        return


def main(argv: list[str] | None = None) -> int:
    result = run_session_start()
    # Stdout becomes additionalContext per Claude Code convention.
    print(result["additional_context"])
    # Amendment #49: best-effort retrofit of the top-level statusLine
    # entry for workspaces already past first-run. Fail-soft so a
    # transient settings.json I/O error never blocks the supervisor.
    pos_v2_root = Path(__file__).resolve().parents[2]
    _maybe_install_status_line(pos_v2_root)
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
