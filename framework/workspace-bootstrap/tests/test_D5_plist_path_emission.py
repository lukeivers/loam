"""Amendment #31 — D5 acceptance tests for workspace-bootstrap
plist PATH emission.

Each test function maps 1:1 to a D5 criterion named in
`docs/rebuild/plans/amendment-31-workspace-bootstrap-plist-path.md`:

D5.1 — memory-graphiti emitted plist reaches `/health` → 200 end-to-end
       under a real `launchctl bootstrap` in the user's gui domain,
       using a UUID-unique sandbox label with bootout-in-teardown.

D5.2 — the orchestrator plist's PATH emission is parse-back equivalent
       to the memory-graphiti plist's PATH emission (same helper →
       identical string, research §7.3 ruling).

D5.3 — each emitted plist's `EnvironmentVariables` dict contains
       exactly the amendment-declared key set (memory-graphiti = 5
       keys; orchestrator = 2 keys). Structural anti-creep guard.

Method-level choices (builder's call per ODD §1.1):

  - D5.1 uses a UUID-unique Label sandbox with bootout-in-teardown
    to avoid colliding with any currently-registered service on the
    dispatch host. It clean-skips when the `claude` binary or the
    memory-system venv are absent — these are platform prereqs of
    the memory-graphiti service itself, not of the plist-emission
    contract this amendment widens.
  - D5.2/D5.3 use stdlib `plistlib` for parse-back; the AC names
    the observable (PATH equivalence; exact key set), not the
    parsing mechanism.
"""

from __future__ import annotations

import json
import os
import plistlib
import shutil
import socket
import subprocess
import time
import uuid
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    run_first_run_scaffold,
    service_label,
)


# Repo root — for the D5.1 service-spawn the canonical tree's
# `memory-system/.venv/bin/python` must exist on this host.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _scaffold_fresh_sandbox(
    *,
    tmp_path: Path,
    workspace_root: Path,
    port: int = 8765,
) -> tuple[Path, Path]:
    """Run a fresh scaffold against `tmp_path`-local pos_root + agents.

    Returns (memory_graphiti_plist, orchestrator_plist) absolute paths.
    """
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"
    # Pre-seed memory.yaml on partial-recovery path so the test can
    # pin a free port without racing the scaffold's default 8765.
    pos_root.mkdir(parents=True, exist_ok=True)
    (pos_root / "memory.yaml").write_text(
        "launch: true\n"
        "host: 127.0.0.1\n"
        f"port: {port}\n"
        "health_path: /health\n"
        "startup_timeout_s: 30\n"
        "poll_interval_s: 0.5\n"
    )
    (pos_root / "bootstrap.yaml").write_text("contributions: []\n")
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace_root,
        partial_recovery=True,
    )
    slug = workspace_root.name
    mg = agents / f"{service_label('memory-graphiti', slug)}.plist"
    orch = agents / f"{service_label('orchestrator', slug)}.plist"
    return mg, orch


def _free_port() -> int:
    """Bind-to-0 then close; return the kernel-assigned free port.

    Small race between close and subsequent bind-by-service; in
    practice OK for a single-service sandbox test.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# =====================================================================
# D5.1 — memory-graphiti emitted plist reaches /health → 200 end-to-end
# =====================================================================


def test_D5_1_memory_graphiti_scaffold_plist_reaches_health_200(
    tmp_path: Path,
) -> None:
    """Given a fresh scaffold invocation, bootstrap the emitted memory-
    graphiti plist into launchd's gui domain under a UUID-unique
    sandbox label. Poll `/health`; assert HTTP 200 within the
    memory.yaml-declared `startup_timeout_s`. Bootout in teardown
    regardless of outcome."""
    # Platform + prereq gates — these are prereqs of the memory-
    # graphiti service itself, not of the plist-emission contract
    # this amendment widens. A clean skip keeps the test honest on
    # CI hosts without the service's runtime prereqs.
    if not (_REPO_ROOT / "framework" / "memory-system" / ".venv" / "bin" / "python").exists():
        pytest.skip("memory-system venv absent on this host")
    if shutil.which("claude") is None:
        pytest.skip("`claude` binary not on host PATH")
    if shutil.which("launchctl") is None:
        pytest.skip("launchctl absent (non-macOS host)")

    # Scaffold emits a plist whose ProgramArguments / WorkingDirectory
    # must resolve to the canonical memory-system venv + importable
    # src.service module. D5.1 asserts the *emitted* plist (modulo
    # Label + stdout redirection for sandbox isolation) brings up
    # /health — the PATH emission is the load-bearing edit.
    #
    # To keep the scaffold's side-effect writes (personas/, .mcp.json,
    # tracker DB) out of the canonical tree, the scaffold runs against
    # a tmp workspace whose ``memory-system`` is symlinked to the
    # canonical one. The plist emits paths under tmp_workspace; the
    # symlink redirects ProgramArguments/WorkingDirectory through to
    # the canonical venv at runtime. Personas + auxiliary writes land
    # under tmp_workspace and are reaped with tmp_path.
    port = _free_port()
    tmp_workspace = tmp_path / "ws"
    tmp_workspace.mkdir()
    # Post-D.1: plist templates reference {workspace}/framework/memory-system/...
    # so the symlink must land at framework/memory-system/ inside tmp_workspace.
    (tmp_workspace / "framework").mkdir()
    (tmp_workspace / "framework" / "memory-system").symlink_to(
        _REPO_ROOT / "framework" / "memory-system"
    )
    mg_plist_path, _orch_plist_path = _scaffold_fresh_sandbox(
        tmp_path=tmp_path,
        workspace_root=tmp_workspace,
        port=port,
    )

    # Load, parse, and rewrite Label + stdout paths for sandbox
    # isolation. We do NOT rewrite EnvironmentVariables — the PATH
    # emission under test must be the scaffold-emitted one verbatim.
    with open(mg_plist_path, "rb") as f:
        plist = plistlib.load(f)
    sandbox_token = f"d5-sandbox-{uuid.uuid4().hex[:12]}"
    sandbox_label = f"com.loam.{sandbox_token}.memory-graphiti"
    plist["Label"] = sandbox_label
    plist["StandardOutPath"] = str(tmp_path / "mg.out.log")
    plist["StandardErrorPath"] = str(tmp_path / "mg.err.log")
    sandbox_plist = tmp_path / f"{sandbox_label}.plist"
    with open(sandbox_plist, "wb") as f:
        plistlib.dump(plist, f)
    sandbox_plist.chmod(0o644)

    uid = os.getuid()
    launchctl = shutil.which("launchctl") or "/bin/launchctl"
    target = f"gui/{uid}/{sandbox_label}"

    def _bootout() -> None:
        subprocess.run(
            [launchctl, "bootout", target],
            check=False,
            capture_output=True,
            timeout=15,
        )

    # Pre-emptive bootout in case of leftover from a prior aborted run
    # under the same token (UUID makes this extremely unlikely; cheap
    # to do anyway).
    _bootout()
    try:
        bootstrap = subprocess.run(
            [launchctl, "bootstrap", f"gui/{uid}", str(sandbox_plist)],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert bootstrap.returncode == 0, (
            f"launchctl bootstrap failed: rc={bootstrap.returncode} "
            f"stderr={bootstrap.stderr!r}"
        )

        # Poll /health until 200 or startup_timeout_s elapses.
        #
        # The service's FastMCP `lifespan` (which builds Graphiti and
        # sets `_graphiti` — the non-None condition for /health = 200)
        # only fires when the first MCP session is established. An
        # MCP `initialize` POST against `/mcp` is sufficient to trigger
        # it; no real MCP traffic is required beyond that. Once
        # lifespan has fired, subsequent `/health` probes return 200.
        # The method of triggering lifespan is builder's call per
        # ODD §1.1; the AC names the outcome (`/health` = 200 within
        # the configured startup timeout), not the trigger mechanism.
        deadline = time.time() + 30.0  # matches memory.yaml default
        base = f"http://127.0.0.1:{port}"
        mcp_init_body = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "d5-test", "version": "0.0"},
            },
        }).encode("utf-8")
        mcp_init = Request(
            f"{base}/mcp",
            data=mcp_init_body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            method="POST",
        )
        lifespan_triggered = False
        last_err: str | None = None
        while time.time() < deadline:
            # Trigger lifespan via MCP initialize (once the server is
            # listening; retry until the socket accepts).
            if not lifespan_triggered:
                try:
                    with urlopen(mcp_init, timeout=2.0) as resp:
                        # 200 = server up + lifespan fired. We don't
                        # read or validate the MCP response body.
                        if resp.status == 200:
                            lifespan_triggered = True
                except URLError as e:
                    last_err = f"MCP init URLError: {e}"
                except Exception as e:  # pragma: no cover - defensive
                    last_err = f"MCP init {type(e).__name__}: {e}"
            # Probe /health — the outcome under test.
            try:
                with urlopen(f"{base}/health", timeout=2.0) as resp:
                    if resp.status == 200:
                        # Outcome asserted: /health = 200 under the
                        # scaffold-emitted plist. PATH emission is the
                        # load-bearing edit; without it the service
                        # would have crashed at ClaudePrintLLMClient
                        # construction with ClaudeBinaryMissingError.
                        return
                    last_err = f"/health status={resp.status}"
            except URLError as e:
                # 503 raises URLError with code=503; capture and keep
                # polling.
                last_err = f"/health URLError: {e}"
            except Exception as e:  # pragma: no cover - defensive
                last_err = f"/health {type(e).__name__}: {e}"
            time.sleep(0.5)

        # Timeout — drain stderr for diagnostic.
        err_tail = ""
        err_log = Path(plist["StandardErrorPath"])
        if err_log.exists():
            err_tail = err_log.read_text()[-2000:]
        pytest.fail(
            f"/health did not return 200 within 30s; last_err={last_err!r}; "
            f"stderr_tail={err_tail!r}"
        )
    finally:
        _bootout()


# =====================================================================
# D5.2 — orchestrator plist carries the same PATH emission
# =====================================================================


def test_D5_2_orchestrator_plist_carries_same_path_as_memory_graphiti(
    tmp_path: Path,
) -> None:
    """Parse back both emitted plists; assert their
    `EnvironmentVariables.PATH` strings are identical and non-empty.
    Outcome: parse-back equivalence — the same helper produces both,
    so the latent-same-class PATH hazard on the orchestrator plist
    is closed by construction."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    mg_path, orch_path = _scaffold_fresh_sandbox(
        tmp_path=tmp_path,
        workspace_root=workspace,
    )
    with open(mg_path, "rb") as f:
        mg_plist = plistlib.load(f)
    with open(orch_path, "rb") as f:
        orch_plist = plistlib.load(f)
    mg_path_str = mg_plist["EnvironmentVariables"]["PATH"]
    orch_path_str = orch_plist["EnvironmentVariables"]["PATH"]
    assert mg_path_str, "memory-graphiti plist emitted empty PATH"
    assert orch_path_str, "orchestrator plist emitted empty PATH"
    assert mg_path_str == orch_path_str, (
        "memory-graphiti and orchestrator PATH emissions diverged; "
        f"mg={mg_path_str!r} orch={orch_path_str!r}"
    )


# =====================================================================
# D5.3 — per-plist exact-set env surface guard
# =====================================================================


def test_D5_3_scaffold_plists_emit_exact_env_key_sets(
    tmp_path: Path,
) -> None:
    """Parse back both emitted plists; assert each
    `EnvironmentVariables` dict's key set is exactly the amendment-
    declared set for that plist kind. Any unauthored key added in
    a later edit fails this test — this is the §2.5 structural
    anti-creep guard against defensive future widening."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    mg_path, orch_path = _scaffold_fresh_sandbox(
        tmp_path=tmp_path,
        workspace_root=workspace,
    )
    with open(mg_path, "rb") as f:
        mg_plist = plistlib.load(f)
    with open(orch_path, "rb") as f:
        orch_plist = plistlib.load(f)

    mg_keys = set(mg_plist["EnvironmentVariables"].keys())
    orch_keys = set(orch_plist["EnvironmentVariables"].keys())

    # memory-graphiti: amendment #29 added GRAPHITI_SERVICE_HOST +
    # GRAPHITI_SERVICE_PORT + LOAM_WORKSPACE_ROOT (three workspace-
    # identity / port-binding keys); this amendment adds PATH. With
    # the pre-existing PYTHONUNBUFFERED that is five keys, exactly.
    assert mg_keys == {
        "PYTHONUNBUFFERED",
        "GRAPHITI_SERVICE_HOST",
        "GRAPHITI_SERVICE_PORT",
        "LOAM_WORKSPACE_ROOT",
        "PATH",
    }, f"memory-graphiti plist key set drifted: {mg_keys!r}"

    # orchestrator: amendment #29 did NOT add workspace-identity env
    # vars (orchestrator uses a UNIX-socket supervisor probe, not
    # an HTTP /health with workspace identity). This amendment adds
    # PATH alongside the pre-existing PYTHONUNBUFFERED — two keys,
    # exactly.
    assert orch_keys == {
        "PYTHONUNBUFFERED",
        "PATH",
    }, f"orchestrator plist key set drifted: {orch_keys!r}"
