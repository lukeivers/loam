"""pos-v2 first-run helper (Phase 3 onward).

Invoked from ``first-run.sh`` once the top-level venv exists. Stdlib-only.

Phases implemented here (proposal §3.1):
  * Phase 3 — per-component pip install (shared + dedicated venvs).
  * Phase 4 — plist/unit substitution + service bootstrap + health poll.
  * Phase 5 — confirmation sentence emission.
  * Phase 6 — self-retire: rewrite settings.json's SessionStart stanza
    to invoke the sealed supervisor path, delete first-run.sh.
  * Phase 7 — final-state verification.

Error-code range: -32091..-32099 (inside hands-off-lifecycle's block).

  -32091  platform-unsupported:no-compatible-python-found (Phase 1;
          claimed by first-run.sh — this helper never enters that path)
  -32091  platform-unsupported:<label> (Phase 4 if OS not macos/linux —
          reuses the existing workspace-bootstrap code point)
  -32097  pip-install-failed:<component>:<tail>
  -32098  service-health-timeout:<label>
  -32099  hands-off-lifecycle-internal:<phase>:<detail>

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
import socket
import subprocess
import sys
import time
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
    validate_inventory,
)
from first_run_settings import (  # noqa: E402
    SettingsMergeResult,
    build_first_run_stanza,
    build_supervisor_stanza,
    merge_session_start,
)


# ---- error codes -----------------------------------------------------


ERR_PIP_INSTALL_FAILED = -32097
ERR_SERVICE_HEALTH_TIMEOUT = -32098
ERR_HANDS_OFF_INTERNAL = -32099
ERR_PLATFORM_UNSUPPORTED = -32091


# ---- diagnostic emission --------------------------------------------


def _emit_diag(code: int, kind: str, detail: str, remediation: str) -> None:
    """Emit a loud-escalation diagnostic and exit 0."""
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
    if s.startswith("linux"):
        return "linux"
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
    outcomes: list[PipOutcome] = []
    for name in component_names:
        comp_dir = pos_v2_root / name
        req = comp_dir / "requirements.txt"
        if not req.exists():
            # Component has no requirements.txt; nothing to install here.
            # Editable installs (pyproject.toml) are out of first-run's
            # scope per research §4.4 — the shared venv is expected to
            # already have the tooling it needs from the workspace's
            # common base.
            continue
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


# ---- plist substitution via Amendment 4 ------------------------------


def _invoke_first_run_scaffold(
    *,
    pos_v2_root: Path,
    service_manager_dir_override: Path | None = None,
    service_bootstrap: bool = True,
) -> Any:
    """Call Amendment 4's run_first_run_scaffold() as a library.

    Per Eve inference #4 in the research (§10.4 Option A): consume the
    scaffold adapter rather than reimplement. The adapter handles YAML
    scaffold, plist/systemd-unit substitution, and service bootstrap.

    Requires the workspace-bootstrap component to be importable from the
    shared venv, which it is after Phase 3's shared-component install.
    """
    # Add workspace-bootstrap's src dir to sys.path so the adapter is
    # importable regardless of editable-install state.
    wb_src = pos_v2_root / "workspace-bootstrap" / "src"
    if wb_src.is_dir() and str(wb_src) not in sys.path:
        sys.path.insert(0, str(wb_src))

    from workspace_bootstrap.adapters.first_run_scaffold import (  # type: ignore
        run_first_run_scaffold,
    )

    return run_first_run_scaffold(
        pos_root=Path.home() / ".pos",
        dry_run=False,
        service_bootstrap=service_bootstrap,
        service_manager_dir_override=service_manager_dir_override,
        workspace_root=pos_v2_root,
    )


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


def _service_health(svc: dict[str, Any]) -> bool:
    health = svc.get("health") or {}
    kind = health.get("kind")
    if kind == "http":
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
) -> tuple[bool, list[str]]:
    """Poll services until all healthy, up to ``timeout_s``.

    Returns (all_healthy, pending_labels).
    """
    deadline = time.monotonic() + float(timeout_s)
    while True:
        pending = [svc["label"] for svc in services if not _service_health(svc)]
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
) -> tuple[SettingsMergeResult, Path, bool]:
    """Rewrite settings.json to invoke the supervisor directly; delete first-run.sh.

    Returns (merge_result, removed_script_path, script_removed).
    """
    supervisor_stanza = build_supervisor_stanza(pos_v2_root)
    merge_result = merge_session_start(
        settings_path=settings_path,
        new_entry=supervisor_stanza,
    )

    script_path = pos_v2_root / "hands-off-lifecycle" / "hooks" / "first-run.sh"
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
    script_path = pos_v2_root / "hands-off-lifecycle" / "hooks" / "first-run.sh"
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
    script_path = pos_v2_root / "hands-off-lifecycle" / "hooks" / "first-run.sh"
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


def _run_bootstrap(*, pos_v2_root: Path, inventory_path: Path) -> int:
    """Phases 3..7 in order. Returns a process exit code (always 0)."""

    # ---- Phase 3a: parse inventory --------------------------------
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
        )
        return 0

    shared = inventory["shared_venv"]
    shared_venv_path = pos_v2_root / shared["path"]
    shared_python = shared_venv_path / "bin" / "python"

    # ---- Phase 3b: shared-venv pip installs -----------------------
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
            )
            return 0

    # ---- Phase 3c: dedicated-venv pip installs --------------------
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
    first_run_stanza = build_first_run_stanza(pos_v2_root)
    merge_result = merge_session_start(
        settings_path=settings_path,
        new_entry=first_run_stanza,
    )

    # ---- Phase 4a: plist / unit substitution + service bootstrap --
    plat = _detect_platform()
    if plat not in ("macos", "linux"):
        _emit_diag(
            ERR_PLATFORM_UNSUPPORTED,
            f"platform-unsupported:{plat}",
            "launchd or systemd-user is required for service bootstrap.",
            "pos-v2 supports macOS and Linux. Windows is out of scope.\n"
            "On WSL2, the Linux path works; run from inside the WSL2\n"
            "shell.",
        )
        return 0

    print("pos v2 first-run: substituting service-manager files and bootstrapping services...")
    try:
        _invoke_first_run_scaffold(
            pos_v2_root=pos_v2_root,
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

    # ---- Phase 4b: health poll ------------------------------------
    services = list(inventory.get("services", []))
    service_labels = [svc["label"] for svc in services]
    print(f"pos v2 first-run: polling services for health ({', '.join(service_labels)})...")
    healthy, pending = _poll_services_healthy(
        services=services,
        timeout_s=60.0,  # < the 120s hook ceiling, room for self-retire below.
        poll_interval_s=0.5,
    )
    if not healthy:
        _emit_diag(
            ERR_SERVICE_HEALTH_TIMEOUT,
            f"service-health-timeout:{','.join(pending)}",
            f"services did not report healthy within budget: {pending}",
            "Next session will retry. Check service logs:\n"
            "  ~/.pos/logs/ and ~/.pos/logs/*.err\n"
            "Inspect the launchd / systemd status:\n"
            "  macOS: launchctl print gui/$(id -u)/<LABEL>\n"
            "  Linux: systemctl --user status <LABEL>",
        )
        return 0

    # ---- Phase 5: confirmation sentence ---------------------------
    confirmation = _confirmation_sentence(
        merge_result=merge_result,
        service_labels=service_labels,
    )
    print(confirmation)

    # ---- Phase 6: self-retire -------------------------------------
    retire_merge, script_path, removed = _self_retire(
        pos_v2_root=pos_v2_root,
        settings_path=settings_path,
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
    args = parser.parse_args(argv)

    pos_v2_root = Path(args.pos_v2_root).resolve()
    inventory_path = Path(
        args.inventory or (pos_v2_root / "first-run-inventory.yaml")
    ).resolve()

    if not pos_v2_root.is_dir():
        _emit_diag(
            ERR_HANDS_OFF_INTERNAL,
            "hands-off-lifecycle-internal:pos-v2-root-not-a-directory",
            str(pos_v2_root),
            "First-run was invoked with a non-existent workspace root.\n"
            "This is a bug; file an issue.",
        )
        return 0

    if args.mode == "bootstrap":
        return _run_bootstrap(
            pos_v2_root=pos_v2_root, inventory_path=inventory_path
        )
    return _run_resume(pos_v2_root=pos_v2_root, inventory_path=inventory_path)


if __name__ == "__main__":
    raise SystemExit(main())
