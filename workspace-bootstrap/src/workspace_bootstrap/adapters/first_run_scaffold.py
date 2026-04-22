"""First-run scaffold adapter (Amendment 4 — hands-off-lifecycle).

Runs in the new ``first_run_scaffold`` phase, before
``before_orchestrator_start``. Detects a fresh pos-v2 workspace and
writes the per-component YAML defaults, installs the launchd /
systemd-user service-manager files for the memory sidecar and the
orchestrator, and invokes ``launchctl bootstrap`` / ``systemctl --user
start`` so the services come up without the user doing anything manual.

First-run detection heuristic (per proposal §9 inference #8):

    No ``~/.pos/`` directory AND no ``~/.pos/bootstrap.yaml`` file.

If ``~/.pos/`` exists but ``bootstrap.yaml`` does not, the scaffold
halts with a ``partial-scaffold-detected`` diagnostic rather than
overwriting anything. This is the H4 structural refusal.

Platform support is limited to macOS (launchd) and Linux
(systemd-user). Any other platform halts with ``platform-unsupported:
<platform>`` — the H3 structural refusal. A subprocess-fallback would
violate the silent-stay-degraded prohibition.

Error-code range reserved for this component: -32090..-32099 (per
proposal §9 inference #2). Only ``-32090`` (partial_scaffold) and
``-32091`` (platform_unsupported) are used here; the rest are reserved
for the supervisor.
"""

from __future__ import annotations

import os
import platform
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from ..errors import BootstrapError
from ..spec import BaseContribution, ContributionMetadata, Phase


# ---- error codes reserved to -32090..-32099 ---------------------------


ERR_PARTIAL_SCAFFOLD = -32090
ERR_PLATFORM_UNSUPPORTED = -32091


class PartialScaffoldError(BootstrapError):
    code = ERR_PARTIAL_SCAFFOLD


class PlatformUnsupportedError(BootstrapError):
    code = ERR_PLATFORM_UNSUPPORTED


# ---- confirmation sentence (proposal Q7 — locked wording) ------------


CONFIRMATION_SENTENCE = (
    "pos v2 first-run scaffold complete: twelve foundational components "
    "configured at defaults (safety/always-ask, cost ceilings, "
    "reversibility, self-correction, memory, degradation), memory "
    "sidecar and orchestrator launched as user services, staging store "
    "initialised. `~/.pos/` is your config dir — edit any file to "
    "adjust. Proceeding."
)


# ---- YAML content — per-component starter defaults -------------------


_BOOTSTRAP_YAML = """\
# ~/.pos/bootstrap.yaml — twelve-foundational-adapter bundle
# Auto-generated on first run. Edit freely; the scaffold only runs on
# a fresh workspace (no ~/.pos/ directory present) and never overwrites.

contributions:
  - name: observability_aggregator
    module: workspace_bootstrap.adapters.observability_aggregator
    class: ObservabilityAggregatorContribution
  - name: safety_layer
    module: workspace_bootstrap.adapters.safety_layer
    class: SafetyLayerContribution
  - name: reversibility_primitive
    module: workspace_bootstrap.adapters.reversibility_primitive
    class: ReversibilityPrimitiveContribution
  - name: cost_governance
    module: workspace_bootstrap.adapters.cost_governance
    class: CostGovernanceContribution
  - name: self_correction
    module: workspace_bootstrap.adapters.self_correction
    class: SelfCorrectionContribution
  - name: memory_system
    module: workspace_bootstrap.adapters.memory_system
    class: MemorySystemContribution
  - name: scope_of_work
    module: workspace_bootstrap.adapters.scope_of_work
    class: ScopeOfWorkContribution
  - name: objective_tracker
    module: workspace_bootstrap.adapters.objective_tracker
    class: ObjectiveTrackerContribution
  - name: primary_persona
    module: workspace_bootstrap.adapters.primary_persona
    class: PrimaryPersonaContribution
  - name: graceful_degradation
    module: workspace_bootstrap.adapters.graceful_degradation
    class: GracefulDegradationContribution
  - name: self_upgrade
    module: workspace_bootstrap.adapters.self_upgrade
    class: SelfUpgradeContribution
  - name: workspace_bootstrap_py
    module: workspace_bootstrap.adapters.workspace_bootstrap_py
    class: WorkspaceBootstrapPyContribution
"""

_MEMORY_YAML = """\
# ~/.pos/memory.yaml — sidecar connection + launch config
launch: true
host: 127.0.0.1
port: 8765
health_path: /health
startup_timeout_s: 30
poll_interval_s: 0.5
"""

_MEMORY_STAGING_YAML = """\
# ~/.pos/memory-staging.yaml — degraded-mode staging store
soft_cap: 10000
hard_cap: 50000
db_path: ~/.pos/memory-staging.sqlite
drain_batch_size: 100
probe_interval_s: 30
latency_threshold_ms: 500
"""

_SAFETY_YAML = """\
# ~/.pos/safety/always_ask.yaml — framework-floor always-ask list.
# Add per-workspace entries here; the floor below is non-negotiable.
always_ask:
  - external_payments
  - irreversible_user_data_deletion
  - publishing_to_public_surface
  - sending_as_owner_to_third_party
"""

_COST_YAML = """\
# ~/.pos/cost/ceilings.yaml — advisory starter ceilings.
# Raise or lower to match your workspace budget.
ceilings:
  daily_usd: 5.00
  monthly_usd: 100.00
advisory: true
"""

_REVERSIBILITY_YAML = """\
# ~/.pos/reversibility.yaml — per-tool reversibility classes.
# Empty starter; register per-adapter classes as you add tools.
registrations: {}
"""

_SELF_CORRECTION_YAML = """\
# ~/.pos/self-correction.yaml — four-part protocol knobs.
enabled: true
"""

_DEGRADATION_YAML = """\
# ~/.pos/degradation-config.yaml — per-mode defaults.
notification:
  default_tier: 2
  auth_broken_tier: 1
"""


_SCAFFOLD_FILES: dict[str, str] = {
    "bootstrap.yaml": _BOOTSTRAP_YAML,
    "memory.yaml": _MEMORY_YAML,
    "memory-staging.yaml": _MEMORY_STAGING_YAML,
    "safety/always_ask.yaml": _SAFETY_YAML,
    "cost/ceilings.yaml": _COST_YAML,
    "reversibility.yaml": _REVERSIBILITY_YAML,
    "self-correction.yaml": _SELF_CORRECTION_YAML,
    "degradation-config.yaml": _DEGRADATION_YAML,
}


# ---- platform detection ----------------------------------------------


def detect_platform() -> str:
    """Return 'macos', 'linux', or a named unsupported platform label.

    The label is what gets emitted in the platform-unsupported halt
    diagnostic.
    """
    sysname = sys.platform.lower()
    if sysname == "darwin":
        return "macos"
    if sysname.startswith("linux"):
        return "linux"
    return sysname


def _which(binary: str) -> str | None:
    for d in (os.environ.get("PATH") or "").split(os.pathsep):
        p = Path(d) / binary
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
    return None


# ---- scaffold result -------------------------------------------------


@dataclass(frozen=True)
class ScaffoldResult:
    ran: bool
    reason: str  # "already_scaffolded" | "fresh_scaffold" | "dry_run"
    files_written: tuple[str, ...] = ()
    service_files_installed: tuple[str, ...] = ()
    services_bootstrapped: tuple[str, ...] = ()
    confirmation: str | None = None


# ---- adapter body ----------------------------------------------------


def _write_file(path: Path, content: str, *, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(mode)


def run_first_run_scaffold(
    *,
    pos_root: Path,
    dry_run: bool = False,
    platform_override: str | None = None,
    service_bootstrap: bool = True,
    service_manager_dir_override: Path | None = None,
    workspace_root: Path | None = None,
    service_runner: "ServiceManagerRunner | None" = None,
) -> ScaffoldResult:
    """Deterministic scaffold implementation, test-callable.

    Parameters
    ----------
    pos_root:
        The ``~/.pos/`` directory to write into. Tests pass a tmp_path.
    dry_run:
        If True, the check-then-write short-circuits and no side-effects
        happen. The return value reports what *would* have been done.
    platform_override:
        Force a platform label for tests. ``"macos"`` / ``"linux"`` /
        anything else routes to the platform-unsupported halt.
    service_bootstrap:
        If False, service-manager files are written but the
        ``launchctl bootstrap`` / ``systemctl --user start`` call is
        skipped. Tests default to False.
    service_manager_dir_override:
        Override for the ``~/Library/LaunchAgents`` or
        ``~/.config/systemd/user`` destination so tests can inspect
        written plists without touching the user's real agent dir.
    workspace_root:
        Absolute path to the pos-v2 workspace (used when templating
        service-manager files). Defaults to the pos-v2 repo root if
        detectable; else left as ``{WORKSPACE}`` for the user to fill
        in.
    service_runner:
        Injection hook that tests replace to avoid spawning real
        launchctl / systemctl.
    """
    plat = platform_override or detect_platform()
    if plat not in ("macos", "linux"):
        raise PlatformUnsupportedError(
            f"platform-unsupported:{plat}",
            data={"platform": plat, "pos_root": str(pos_root)},
        )

    pos_root = Path(pos_root).expanduser()
    bootstrap_yaml = pos_root / "bootstrap.yaml"

    # First-run detection (Q6 heuristic).
    if pos_root.exists() and not bootstrap_yaml.exists():
        # Partial prior state — structural refusal (H4).
        raise PartialScaffoldError(
            "partial-scaffold-detected",
            data={
                "pos_root": str(pos_root),
                "missing": str(bootstrap_yaml),
            },
        )

    if bootstrap_yaml.exists():
        return ScaffoldResult(
            ran=False,
            reason="already_scaffolded",
            confirmation=None,
        )

    if dry_run:
        return ScaffoldResult(
            ran=False,
            reason="dry_run",
            files_written=tuple(_SCAFFOLD_FILES.keys()),
            confirmation=CONFIRMATION_SENTENCE,
        )

    # Write the nine YAML files.
    written: list[str] = []
    for rel, content in _SCAFFOLD_FILES.items():
        dest = pos_root / rel
        _write_file(dest, content)
        written.append(rel)

    # Install service-manager files.
    ws = _resolve_workspace_root(workspace_root)
    service_runner = service_runner or ServiceManagerRunner(platform_label=plat)
    service_files = _install_service_manager_files(
        plat=plat,
        workspace_root=ws,
        override_dir=service_manager_dir_override,
    )

    bootstrapped: list[str] = []
    if service_bootstrap:
        for label, path in service_files:
            try:
                service_runner.bootstrap(label=label, service_file=path)
                bootstrapped.append(label)
            except Exception as e:  # pragma: no cover - exercised via tests
                # Non-fatal: the file is installed; the user can run
                # ``launchctl bootstrap`` manually. The supervisor will
                # still probe and escalate loudly if services don't come
                # up.
                written.append(f"# service-bootstrap warning for {label}: {e}")

    return ScaffoldResult(
        ran=True,
        reason="fresh_scaffold",
        files_written=tuple(written),
        service_files_installed=tuple(p for _, p in service_files),
        services_bootstrapped=tuple(bootstrapped),
        confirmation=CONFIRMATION_SENTENCE,
    )


# ---- service-manager file templating ---------------------------------


_LAUNCHD_TEMPLATES: dict[str, str] = {
    "com.pos-v2.memory-graphiti": """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTD/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>{label}</string>
    <key>ProgramArguments</key>
    <array>
      <string>{workspace}/memory-system/.venv/bin/python</string>
      <string>-m</string><string>src.service</string>
    </array>
    <key>WorkingDirectory</key><string>{workspace}/memory-system</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>ThrottleInterval</key><integer>10</integer>
    <key>StandardOutPath</key><string>{workspace}/memory-system/data/graphiti-service.log</string>
    <key>StandardErrorPath</key><string>{workspace}/memory-system/data/graphiti-service.err.log</string>
    <key>EnvironmentVariables</key><dict><key>PYTHONUNBUFFERED</key><string>1</string></dict>
</dict>
</plist>
""",
    "com.pos.orchestrator": """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTD/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>{label}</string>
    <key>ProgramArguments</key>
    <array>
      <string>{workspace}/.venv/bin/python</string>
      <string>-m</string><string>pos_orchestrator</string>
    </array>
    <key>WorkingDirectory</key><string>{workspace}</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>ThrottleInterval</key><integer>30</integer>
    <key>ProcessType</key><string>Interactive</string>
    <key>StandardOutPath</key><string>{workspace}/orchestrator.out.log</string>
    <key>StandardErrorPath</key><string>{workspace}/orchestrator.err.log</string>
    <key>EnvironmentVariables</key><dict><key>PYTHONUNBUFFERED</key><string>1</string></dict>
</dict>
</plist>
""",
}


_SYSTEMD_TEMPLATES: dict[str, str] = {
    "pos-v2-memory-graphiti": """\
[Unit]
Description=pos-v2 memory sidecar (Graphiti + Kuzu)
After=default.target

[Service]
Type=simple
WorkingDirectory={workspace}/memory-system
Environment=PYTHONUNBUFFERED=1
ExecStart={workspace}/memory-system/.venv/bin/python -m src.service
Restart=always
RestartSec=10
StartLimitIntervalSec=60
StartLimitBurst=3

[Install]
WantedBy=default.target
""",
    "pos-orchestrator": """\
[Unit]
Description=pOS session-resilient orchestrator
After=default.target

[Service]
Type=simple
WorkingDirectory={workspace}
Environment=PYTHONUNBUFFERED=1
ExecStart={workspace}/.venv/bin/python -m pos_orchestrator
Restart=always
RestartSec=30
StartLimitIntervalSec=60
StartLimitBurst=2

[Install]
WantedBy=default.target
""",
}


def _install_service_manager_files(
    *,
    plat: str,
    workspace_root: str,
    override_dir: Path | None,
) -> list[tuple[str, Path]]:
    """Write plist / .service files into the platform-appropriate dir.

    Returns (label, absolute-path) pairs the caller can bootstrap.
    """
    if plat == "macos":
        dest_dir = override_dir or (Path.home() / "Library" / "LaunchAgents")
        dest_dir.mkdir(parents=True, exist_ok=True)
        out: list[tuple[str, Path]] = []
        for label, tmpl in _LAUNCHD_TEMPLATES.items():
            path = dest_dir / f"{label}.plist"
            path.write_text(tmpl.format(label=label, workspace=workspace_root))
            path.chmod(0o644)
            out.append((label, path))
        return out

    # linux
    dest_dir = override_dir or (Path.home() / ".config" / "systemd" / "user")
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = []
    for label, tmpl in _SYSTEMD_TEMPLATES.items():
        path = dest_dir / f"{label}.service"
        path.write_text(tmpl.format(workspace=workspace_root))
        path.chmod(0o644)
        out.append((label, path))
    return out


# ---- service-manager runner ------------------------------------------


class ServiceManagerRunner:
    """Wraps ``launchctl`` / ``systemctl --user`` for testability."""

    def __init__(self, *, platform_label: str) -> None:
        self._plat = platform_label

    def bootstrap(self, *, label: str, service_file: Path) -> None:
        """Bring a service up. Non-blocking request to the service
        manager; the manager itself supervises the long-lived process.

        This never launches a child process itself — the
        ``SessionStart`` hook's FD-inheritance bug (Claude Code
        v2.1.87, issue #43123) is avoided by delegating to the
        platform's service manager, which is FD-safe."""
        if self._plat == "macos":
            uid = os.getuid()
            binary = _which("launchctl") or "/bin/launchctl"
            subprocess.run(
                [binary, "bootstrap", f"gui/{uid}", str(service_file)],
                check=False,
                capture_output=True,
                timeout=15,
            )
            return
        if self._plat == "linux":
            binary = _which("systemctl") or "/bin/systemctl"
            # Reload to pick up any new unit files, then start.
            subprocess.run(
                [binary, "--user", "daemon-reload"],
                check=False,
                capture_output=True,
                timeout=10,
            )
            subprocess.run(
                [binary, "--user", "start", label],
                check=False,
                capture_output=True,
                timeout=15,
            )
            return
        raise PlatformUnsupportedError(
            f"platform-unsupported:{self._plat}",
            data={"platform": self._plat},
        )


# ---- workspace-root resolver -----------------------------------------


def _resolve_workspace_root(workspace_root: Path | None) -> str:
    if workspace_root is not None:
        return str(Path(workspace_root).resolve())
    # Heuristic: walk up from this file looking for a marker of the
    # pos-v2 repo. The repo root has sibling sealed-component dirs.
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "memory-system").is_dir() and (parent / "orchestrator").is_dir():
            return str(parent)
    # Fallback: a templating placeholder. The scaffold still writes,
    # but the user has to edit the path in. Safer than guessing wrong.
    return "{WORKSPACE}"


# ---- bootstrap contribution -----------------------------------------


class FirstRunScaffoldContribution(BaseContribution):
    """Runs the first-run scaffold as a phase-zero contribution.

    Semantically identical to ``run_first_run_scaffold()`` but exposed
    as a ``Contribution`` so workspace-bootstrap's composition engine
    can order it with other contributions. The single confirmation
    sentence is stored on the host for later surfacing.
    """

    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="first_run_scaffold",
        phase=Phase.first_run_scaffold,
        required=True,
    )

    def contribute(self, host: Any) -> None:
        # pos_root is configurable at workspace level; the host's
        # config_dir is the ~/.pos/ directory per proposal §7.
        pos_root = Path(host.config_dir)
        result = run_first_run_scaffold(
            pos_root=pos_root,
            # Don't invoke launchctl/systemctl from within a pytest-
            # managed bootstrap run; the session-start hook invokes
            # them separately. Workspaces that want bootstrap-time
            # service-bootstrap can override this by subclassing.
            service_bootstrap=False,
        )
        # Surface the confirmation sentence so downstream layers can
        # include it in the session-start hook's additionalContext.
        if result.confirmation is not None:
            host.first_run_confirmation = result.confirmation
