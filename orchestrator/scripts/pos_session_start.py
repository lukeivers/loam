"""Session-start helper script (Amendment 2 — hands-off-lifecycle).

Invoked by the Claude Code ``SessionStart`` hook (type: ``command``).
Probes the memory sidecar + orchestrator; if either is down, asks
``launchctl``/``systemctl --user`` to bring it up (non-blocking, FD-
safe); reports a one-line additionalContext to Claude.

**Critical: the v2.1.87 FD-inheritance bug mitigation.** This script
NEVER spawns a long-lived background process inheriting Claude Code's
stdin/stdout/stderr. The service manager (launchd / systemd-user) is
the thing that actually supervises the long-lived process. The hook
is a trigger — short-lived, synchronous, exits promptly.

Exit code convention:
    0 → services up (either were already up, or came up within budget)
    2 → platform unsupported (no launchctl/systemd --user)
    3 → services did not come up within the budget; supervisor will
        escalate loudly once running

The script is importable so tests can exercise it without subprocess.
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
    if s.startswith("linux"):
        return "linux"
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
    systemd_user_labels: tuple[str, str] = (
        "pos-v2-memory-graphiti",
        "pos-orchestrator",
    ),
) -> list[str]:
    """Ask the platform service manager to bring services up.

    Non-blocking: these commands *request* the service manager to
    launch; they do NOT themselves spawn a child inheriting Claude's
    FDs. This is the v2.1.87 issue #43123 mitigation — FD safety is
    delegated to the service manager layer.

    Returns a list of warning messages (empty on success). Does not
    raise on service-manager error; the caller's probe-again step
    catches that case.
    """
    warnings: list[str] = []
    if plat == "macos":
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
    if plat == "linux":
        binary = _which("systemctl") or "/bin/systemctl"
        try:
            subprocess.run(
                [binary, "--user", "daemon-reload"],
                check=False,
                capture_output=True,
                timeout=10,
            )
        except Exception as e:
            warnings.append(f"systemctl daemon-reload: {e}")
        for label in systemd_user_labels:
            try:
                subprocess.run(
                    [binary, "--user", "start", label],
                    check=False,
                    capture_output=True,
                    timeout=15,
                )
            except Exception as e:
                warnings.append(f"systemctl --user start {label}: {e}")
        return warnings
    warnings.append(f"platform-unsupported:{plat}")
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

    if plat not in ("macos", "linux"):
        return {
            "status": "platform-unsupported",
            "memory_up": False,
            "orchestrator_up": False,
            "additional_context": (
                f"pos v2 session-start: platform-unsupported:{plat} — "
                "launchd or systemd-user required. See "
                "docs/platforms.md for the supported-platform matrix."
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


def main(argv: list[str] | None = None) -> int:
    result = run_session_start()
    # Stdout becomes additionalContext per Claude Code convention.
    print(result["additional_context"])
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
