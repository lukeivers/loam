"""Adapter — memory system (sidecar launcher + health probe).

Phase: before_orchestrator_start.
Role (per Luke's ruling #2): launch the memory-system FastAPI sidecar
in a subprocess and poll `/health` until 200 or timeout.

Config (`memory.yaml` under host.config_dir):
    launch: bool (default: False — many test workspaces skip the
        sidecar; the adapter becomes a no-op when `launch: False`)
    command: list[str] — argv for the sidecar process. When absent,
        defaults to `["python3", "-m", "memory_system.service"]`.
    host: str (default: "127.0.0.1")
    port: int (default: 8765)
    health_path: str (default: "/health")
    startup_timeout_s: float (default: 30.0) — total time to wait for
        the first 200 response.
    poll_interval_s: float (default: 0.5)

Eve-inference #3 challenged: the default timeout is 30s. Eve did not
specify a value; this default is informed by the sidecar's actual
startup (Graphiti + Neo4j connection + FastAPI warm-up empirically
takes 3–10s). 30s accommodates a cold NVMe-backed Neo4j start.

Fails-closed with -32086 (AdapterRaisedError) if the sidecar does not
become healthy within the timeout.
"""

from __future__ import annotations

import logging
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, ClassVar

import yaml

from ..errors import AdapterRaisedError
from ..spec import BaseContribution, ContributionMetadata, Phase


_LOGGER = logging.getLogger(__name__)


class MemorySystemContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="memory_system",
        phase=Phase.before_orchestrator_start,
        after=("observability_aggregator",),
    )

    def contribute(self, host) -> None:
        cfg_path = host.config_dir / "memory.yaml"
        cfg: dict[str, Any] = {}
        if cfg_path.exists():
            loaded = yaml.safe_load(cfg_path.read_text()) or {}
            if isinstance(loaded, dict):
                cfg = loaded

        launch = bool(cfg.get("launch", False))
        host_ = str(cfg.get("host") or "127.0.0.1")
        port = int(cfg.get("port") or 8765)
        health_path = str(cfg.get("health_path") or "/health")
        timeout = float(cfg.get("startup_timeout_s") or 30.0)
        poll_s = float(cfg.get("poll_interval_s") or 0.5)

        url = f"http://{host_}:{port}{health_path}"
        proc: subprocess.Popen | None = None

        if launch:
            command = cfg.get("command") or ["python3", "-m", "memory_system.service"]
            if not isinstance(command, list):
                raise AdapterRaisedError(
                    "memory_system: command must be a list",
                    data={"command": command},
                )
            proc = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Probe until success or timeout.
        deadline = time.monotonic() + timeout
        last_err: str = "no probe yet"
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=2.0) as resp:
                    if resp.status == 200:
                        host.memory_sidecar_url = url

                        if proc is not None:
                            def _shutdown() -> None:
                                try:
                                    proc.terminate()
                                    proc.wait(timeout=5.0)
                                except Exception:
                                    # Amendment #26 — teardown CDC 2:
                                    # surface terminate-path exception
                                    # via logger.debug before falling
                                    # back to SIGKILL.
                                    _LOGGER.debug(
                                        "memory_system_adapter_terminate_failed",
                                        exc_info=True,
                                    )
                                    try:
                                        proc.kill()
                                    except Exception:
                                        _LOGGER.debug(
                                            "memory_system_adapter_kill_failed",
                                            exc_info=True,
                                        )

                            host.register_shutdown("memory_system", _shutdown)
                        return
                    last_err = f"HTTP {resp.status}"
            except (urllib.error.URLError, OSError) as e:
                last_err = f"{type(e).__name__}: {e}"
            time.sleep(poll_s)

        # Clean up subprocess if we launched one but it never became healthy.
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=2.0)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

        raise AdapterRaisedError(
            f"memory_system: sidecar did not become healthy at {url} "
            f"within {timeout}s (last error: {last_err})",
            data={"url": url, "timeout": timeout, "last_error": last_err},
        )
