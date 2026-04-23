"""First-run scaffold adapter (Amendment 4 — hands-off-lifecycle).

Runs in the new ``first_run_scaffold`` phase, before
``before_orchestrator_start``. Detects a fresh pos-v2 workspace and
writes the per-component YAML defaults, installs the launchd
service-manager files for the memory sidecar and the orchestrator, and
invokes ``launchctl bootstrap`` so the services come up without the
user doing anything manual.

First-run detection heuristic (per proposal §9 inference #8):

    No ``~/.pos/`` directory AND no ``~/.pos/bootstrap.yaml`` file.

If ``~/.pos/`` exists but ``bootstrap.yaml`` does not, the scaffold
halts with a ``partial-scaffold-detected`` diagnostic rather than
overwriting anything. This is the H4 structural refusal.

Platform support is limited to macOS (launchd). Any other platform
halts with ``platform-unsupported:<platform>`` — the H3 structural
refusal. A subprocess-fallback would violate the silent-stay-degraded
prohibition. Amendment #10 (linux-removal) removed the Linux/systemd-
user branch per docs/odd-methodology.md §2.5 — Linux was never a
named supported-platform objective.

Error-code range reserved for this component: -32090..-32099 (per
proposal §9 inference #2). Only ``-32090`` (partial_scaffold) and
``-32091`` (platform_unsupported) are used here; the rest are reserved
for the supervisor.
"""

from __future__ import annotations

import os
import platform
import re
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
# -32099 is the hands-off-lifecycle-internal catch-all per the
# lifecycle README's error-code table. The amendment-#6 (namespaced-
# labels-and-bootout) failure modes are scaffold-internal conditions
# and share this code; callers distinguish by the kind: prefix on the
# message payload.
ERR_HANDS_OFF_INTERNAL = -32099


class PartialScaffoldError(BootstrapError):
    code = ERR_PARTIAL_SCAFFOLD


class PlatformUnsupportedError(BootstrapError):
    code = ERR_PLATFORM_UNSUPPORTED


class WorkspaceSlugUnrepresentableError(BootstrapError):
    """Raised when the workspace-root basename has no valid slug form.

    Introduced by amendment #6 (namespaced-labels-and-bootout). A slug
    must match `^[a-z0-9][a-z0-9-]*$` after sanitisation; an empty slug
    means the scaffold has no stable identity to name services under.
    Refuse structurally rather than write unnamespaced service files.
    """

    code = ERR_HANDS_OFF_INTERNAL


class ServiceManagerBootoutError(BootstrapError):
    """Raised when launchctl bootout fails for reasons other than
    `service not loaded`.

    Introduced by amendment #6. Bootout must succeed (or be benignly
    "not loaded") before we attempt bootstrap — otherwise the service
    manager is in an ambiguous state and pushing a bootstrap through
    would resurrect the exact failure class this amendment closes.
    """

    code = ERR_HANDS_OFF_INTERNAL


# ---- workspace-slug + service-label derivation (amendment #6) --------
#
# Slugs are derived deterministically from the workspace root's
# directory basename so two clones on one host do not collide on
# launchd labels. The sanitisation is deliberately conservative —
# disallowed characters become '-', runs collapse, leading/trailing
# '-' trim — matching reverse-DNS label conventions on macOS.


_SLUG_ALLOWED_RE = re.compile(r"[^a-z0-9-]+")
_SLUG_COLLAPSE_RE = re.compile(r"-+")


def workspace_slug(workspace_root: Path | str) -> str:
    """Return a stable, launchd-safe slug for a workspace root.

    Raises ``WorkspaceSlugUnrepresentableError`` if the basename
    contains no characters that survive sanitisation.
    """
    basename = Path(workspace_root).name
    lowered = basename.lower()
    slug = _SLUG_ALLOWED_RE.sub("-", lowered)
    slug = _SLUG_COLLAPSE_RE.sub("-", slug)
    slug = slug.strip("-")
    if not slug:
        raise WorkspaceSlugUnrepresentableError(
            f"workspace-slug-unrepresentable:{basename!r}",
            data={"basename": basename},
        )
    return slug


# Service "kinds" installed by the first-run scaffold. The full label
# is `com.pos-v2.<slug>.<kind>`; the plist filename matches the label.
_SERVICE_KINDS: tuple[str, ...] = ("memory-graphiti", "orchestrator")


def service_label(kind: str, slug: str) -> str:
    """Compose the reverse-DNS launchd label for a kind + workspace slug."""
    if kind not in _SERVICE_KINDS:
        raise ValueError(f"unknown service kind: {kind!r}")
    return f"com.pos-v2.{slug}.{kind}"


# ---- confirmation sentence (proposal Q7 — locked wording) ------------


CONFIRMATION_SENTENCE = (
    "pos v2 first-run scaffold complete: thirteen foundational components "
    "configured at defaults (safety/always-ask, cost ceilings, "
    "reversibility, self-correction, memory, degradation), memory "
    "sidecar and orchestrator launched as user services, staging store "
    "initialised. `~/.pos/` is your config dir — edit any file to "
    "adjust. Proceeding."
)


# ---- YAML content — per-component starter defaults -------------------


_BOOTSTRAP_YAML = """\
# ~/.pos/bootstrap.yaml — thirteen-foundational-adapter bundle
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
  - name: telegram_interface
    module: workspace_bootstrap.adapters.telegram_interface
    class: TelegramInterfaceContribution
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

# Amendment #9 (telegram-interface-framework-integration) — per-workspace
# Telegram channel config. The framework adapter boots degraded-alive
# without this file; it exists so workspaces can flip `required: true`
# (fail-close boot if creds absent) and override the default paths the
# telegram-interface component already recognises.
# Credentials (bot token) live in ~/.claude/channels/telegram/.env per
# proposal §5 #5 — never duplicated here.
_TELEGRAM_YAML = """\
# ~/.pos/telegram.yaml — per-workspace Telegram channel config.
# Most fields are optional. Leaving this whole file out is fine;
# the adapter boots in degraded-alive mode and the setup
# walkthrough runs on session two.
required: false                       # set true to fail-close boot if creds absent
env_path: ~/.claude/channels/telegram/.env
access_path: ~/.claude/channels/telegram/access.json
default_tier: 2                       # degradation-config default
probe_interval_s: 60                  # overrides telegram-interface default
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
    "telegram.yaml": _TELEGRAM_YAML,
}


# ---- platform detection ----------------------------------------------


def detect_platform() -> str:
    """Return 'macos' or a named unsupported platform label.

    The label is what gets emitted in the platform-unsupported halt
    diagnostic. Amendment #10 (linux-removal) dropped the Linux branch;
    any non-macOS label routes to structural refusal.
    """
    sysname = sys.platform.lower()
    if sysname == "darwin":
        return "macos"
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
    partial_recovery: bool = False,
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
        Force a platform label for tests. ``"macos"`` is the only
        supported value; anything else routes to the platform-
        unsupported halt.
    service_bootstrap:
        If False, service-manager files are written but the
        ``launchctl bootstrap`` call is skipped. Tests default to
        False.
    service_manager_dir_override:
        Override for the ``~/Library/LaunchAgents`` destination so
        tests can inspect written plists without touching the user's
        real agent dir.
    workspace_root:
        Absolute path to the pos-v2 workspace (used when templating
        service-manager files). Defaults to the pos-v2 repo root if
        detectable; else left as ``{WORKSPACE}`` for the user to fill
        in.
    service_runner:
        Injection hook that tests replace to avoid spawning real
        launchctl.
    partial_recovery:
        Added by the 2026-04-22 session-start-detachment amendment.
        When False (legacy default), a partial ``~/.pos/`` state
        (directory exists without ``bootstrap.yaml``) raises
        ``PartialScaffoldError`` — the original H4 structural refusal.
        When True, the scaffold repairs the partial state by writing any
        missing files on top of the existing directory, leaving
        user-modified files untouched. Invoked by the detached first-run
        worker on resume when the previous run crashed mid-scaffold —
        the ``partial-scaffold-detected`` halt with "retry next session"
        guidance was itself the terminal user-facing failure mode Luke
        hit on his fresh-clone attempt, which this amendment closes.
    """
    plat = platform_override or detect_platform()
    if plat != "macos":
        raise PlatformUnsupportedError(
            f"platform-unsupported:{plat}",
            data={"platform": plat, "pos_root": str(pos_root)},
        )

    # Amendment #6 structural refusal: derive (and validate) the
    # workspace slug before any file write. A workspace whose basename
    # has no valid slug form cannot be named in service labels; we refuse
    # here rather than land unnamespaced service files.
    ws = _resolve_workspace_root(workspace_root)
    slug = workspace_slug(ws)

    pos_root = Path(pos_root).expanduser()
    bootstrap_yaml = pos_root / "bootstrap.yaml"

    # First-run detection (Q6 heuristic), with optional partial-recovery
    # path (Phase-6 detachment amendment).
    if pos_root.exists() and not bootstrap_yaml.exists():
        if not partial_recovery:
            # Partial prior state — structural refusal (H4).
            raise PartialScaffoldError(
                "partial-scaffold-detected",
                data={
                    "pos_root": str(pos_root),
                    "missing": str(bootstrap_yaml),
                },
            )
        # partial_recovery=True: fall through to the write loop; it is
        # idempotent per file (missing → write, present → leave alone).

    if bootstrap_yaml.exists() and not partial_recovery:
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

    # Write the nine YAML files. Under partial_recovery we skip files
    # that already exist on disk so the user's edits survive; under a
    # normal fresh scaffold this is the first time any file is written
    # so the check is a no-op.
    written: list[str] = []
    for rel, content in _SCAFFOLD_FILES.items():
        dest = pos_root / rel
        if partial_recovery and dest.exists():
            # File survived from a prior partial run; keep whatever the
            # user or the prior run left there. The scaffold's contract
            # is "all files present," not "all files pristine."
            continue
        _write_file(dest, content)
        written.append(rel)

    # Install service-manager files. The workspace root + slug were
    # resolved at the top of this function (before any file write);
    # reuse them here.
    service_runner = service_runner or ServiceManagerRunner(platform_label=plat)
    service_files = _install_service_manager_files(
        plat=plat,
        workspace_root=ws,
        slug=slug,
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
        reason="partial_recovery" if partial_recovery else "fresh_scaffold",
        files_written=tuple(written),
        service_files_installed=tuple(p for _, p in service_files),
        services_bootstrapped=tuple(bootstrapped),
        confirmation=CONFIRMATION_SENTENCE,
    )


# ---- service-manager file templating ---------------------------------


_LAUNCHD_TEMPLATES: dict[str, str] = {
    "memory-graphiti": """\
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
    "orchestrator": """\
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


def _install_service_manager_files(
    *,
    plat: str,
    workspace_root: str,
    slug: str,
    override_dir: Path | None,
) -> list[tuple[str, Path]]:
    """Write launchd plist files into the macOS LaunchAgents dir.

    Labels are computed per workspace slug (amendment #6):
    ``com.pos-v2.<slug>.<kind>``. The filename matches the label; the
    {label} placeholder in templates is substituted with the full
    label string.

    Returns (label, absolute-path) pairs the caller can bootstrap.
    Amendment #10 (linux-removal) removed the systemd-user branch;
    ``plat`` must equal ``"macos"`` — other values are rejected
    upstream by the platform-unsupported halt.
    """
    if plat != "macos":
        raise PlatformUnsupportedError(
            f"platform-unsupported:{plat}",
            data={"platform": plat},
        )
    dest_dir = override_dir or (Path.home() / "Library" / "LaunchAgents")
    dest_dir.mkdir(parents=True, exist_ok=True)
    out: list[tuple[str, Path]] = []
    for kind, tmpl in _LAUNCHD_TEMPLATES.items():
        label = service_label(kind, slug)
        path = dest_dir / f"{label}.plist"
        path.write_text(tmpl.format(label=label, workspace=workspace_root))
        path.chmod(0o644)
        out.append((label, path))
    return out


# ---- service-manager runner ------------------------------------------


class ServiceManagerRunner:
    """Wraps ``launchctl`` for testability."""

    def __init__(self, *, platform_label: str) -> None:
        self._plat = platform_label

    # Amendment #6 constants: stderr fragments launchctl emits when the
    # target label is not currently loaded. Treating these as benign
    # (not a bootout failure) lets the first-ever bootstrap on a fresh
    # host succeed without the label needing to already exist.
    _BENIGN_BOOTOUT_STDERR_FRAGMENTS = (
        "Could not find specified service",
        "No such process",
        "Boot-out failed: 5: Input/output error",
        "not loaded",
    )

    def bootstrap(self, *, label: str, service_file: Path) -> None:
        """Bring a service up, replacing any cached configuration.

        Amendment #6 (namespaced-labels-and-bootout) behaviour:
        always ``bootout`` the label first so launchd drops any stale
        in-memory config, then install the fresh plist. Without this,
        launchd's ``bootstrap`` is a no-op when the label is already
        loaded — the exact failure class that broke pos3's first-run
        on 2026-04-22.

        Non-fatal when bootout reports "service not loaded" (the
        normal first-ever-bootstrap case); a structural refusal
        otherwise via ``ServiceManagerBootoutError``.

        This never launches a child process itself — the
        ``SessionStart`` hook's FD-inheritance bug (Claude Code
        v2.1.87, issue #43123) is avoided by delegating to launchd,
        which is FD-safe. Amendment #10 (linux-removal) dropped the
        systemd-user branch; non-macOS platforms are rejected
        structurally.
        """
        if self._plat != "macos":
            raise PlatformUnsupportedError(
                f"platform-unsupported:{self._plat}",
                data={"platform": self._plat},
            )
        uid = os.getuid()
        binary = _which("launchctl") or "/bin/launchctl"
        bootout = subprocess.run(
            [binary, "bootout", f"gui/{uid}/{label}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if bootout.returncode != 0:
            stderr = bootout.stderr or ""
            if not any(
                frag in stderr
                for frag in self._BENIGN_BOOTOUT_STDERR_FRAGMENTS
            ):
                raise ServiceManagerBootoutError(
                    f"service-manager-bootout-failed:{label}:"
                    f"{stderr.strip()[-200:]}",
                    data={
                        "label": label,
                        "returncode": bootout.returncode,
                        "stderr_tail": stderr.strip()[-200:],
                    },
                )
        subprocess.run(
            [binary, "bootstrap", f"gui/{uid}", str(service_file)],
            check=False,
            capture_output=True,
            timeout=15,
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
            # Don't invoke launchctl from within a pytest-managed
            # bootstrap run; the session-start hook invokes it
            # separately. Workspaces that want bootstrap-time
            # service-bootstrap can override this by subclassing.
            service_bootstrap=False,
        )
        # Surface the confirmation sentence so downstream layers can
        # include it in the session-start hook's additionalContext.
        if result.confirmation is not None:
            host.first_run_confirmation = result.confirmation
