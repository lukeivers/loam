# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""First-run scaffold adapter (Amendment 4 — hands-off-lifecycle).

Runs in the new ``first_run_scaffold`` phase, before
``before_orchestrator_start``. Detects a fresh pos-v2 workspace and
writes the per-component YAML defaults, installs the launchd
service-manager files for the memory sidecar and the orchestrator, and
invokes ``launchctl bootstrap`` so the services come up without the
user doing anything manual.

First-run detection heuristic (per proposal §9 inference #8):

    No ``~/.loam/`` directory AND no ``~/.loam/bootstrap.yaml`` file.

If ``~/.loam/`` exists but ``bootstrap.yaml`` does not, the scaffold
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
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import yaml

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


class PersonaHandleRejectedError(BootstrapError):
    """Raised when ``resolve_persona_handle`` is asked for a handle
    that pOS reserves (master plan D3 (a): ``eve`` is ivers-corp
    branding and must not collide with the workspace's primary-
    persona handle).

    Introduced by amendment #36. The diagnostic carries the rejected
    raw input so a UX layer can re-prompt with a clear reason.
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


# ---- persona-handle resolution (amendment #36) -----------------------
#
# The first-run flow resolves the workspace primary-persona handle
# from a single user input (default empty → ``primary``). This pure
# function implements the resolution; UX layers (now or later) hand
# it the raw input string and consume the resolved handle.
#
# Master-plan D3 (a) constraint: ``eve`` is reserved as ivers-corp
# branding and must not become a workspace handle. This function
# rejects ``eve`` (and only ``eve``) with
# ``PersonaHandleRejectedError`` so the caller can re-prompt.

# Default handle when the user provides no input.
DEFAULT_PERSONA_HANDLE = "primary"

# Reserved handles — currently just ``eve`` per master plan D3 (a).
RESERVED_PERSONA_HANDLES: frozenset[str] = frozenset({"eve"})


def resolve_persona_handle(raw_input: str | None) -> str:
    """Return the resolved persona handle for a one-question prompt.

    - ``None`` or empty/whitespace → ``DEFAULT_PERSONA_HANDLE``
      (``primary``).
    - Otherwise → sluggified via the same shape as ``workspace_slug``
      (lowercase, ASCII-letters/digits/dashes, dashes collapsed,
      leading/trailing dashes trimmed). Idempotent:
      ``resolve_persona_handle(resolve_persona_handle(x)) ==
      resolve_persona_handle(x)``.
    - Resolved handle in ``RESERVED_PERSONA_HANDLES`` →
      ``PersonaHandleRejectedError`` (master plan D3 (a)).
    - Empty post-slug (e.g., ``"!!!"``) → falls back to
      ``DEFAULT_PERSONA_HANDLE``. The user gave non-blank input but
      every character was unrepresentable; the only stable contract
      we can offer is the default rather than refusing.
    """
    if raw_input is None or not raw_input.strip():
        return DEFAULT_PERSONA_HANDLE
    lowered = raw_input.strip().lower()
    slug = _SLUG_ALLOWED_RE.sub("-", lowered)
    slug = _SLUG_COLLAPSE_RE.sub("-", slug)
    slug = slug.strip("-")
    if not slug:
        return DEFAULT_PERSONA_HANDLE
    if slug in RESERVED_PERSONA_HANDLES:
        raise PersonaHandleRejectedError(
            f"persona-handle-reserved:{slug}",
            data={
                "raw_input": raw_input,
                "resolved": slug,
                "reason": (
                    "the handle 'eve' is reserved as ivers-corp "
                    "branding; please pick a different handle."
                ),
            },
        )
    return slug


# Service "kinds" installed by the first-run scaffold. The full label
# is `com.loam.<slug>.<kind>`; the plist filename matches the label.
#
# Amendment J (AC.J.5): ``memory-write-worker`` is the long-running
# drain process for the disk-backed memory-write queue. It composes
# on the same launchd-supervised pattern as ``orchestrator`` —
# workspace-bootstrap provisions the plist; launchd owns lifecycle
# (KeepAlive=true; RunAtLoad=true; ThrottleInterval).
#
# FBE.7 (v0.1.0 foldback) per Luke's 2026-05-03 ruling: ``memory-graphiti``
# is REMOVED from the auto-launched set. The M-FBM file-based memory
# substrate (``primary_persona.file_memory.FileMemoryStore``) is the
# v0.1.0 floor; graphiti returns post-v0.1.0 via the M-GMP plugin path.
# The ``_LAUNCHD_TEMPLATES["memory-graphiti"]`` template entry below is
# retained so M-GMP's re-admission is a one-line change here. See
# ``docs/plans/v0-1-0-foldback-scope-expansion-fbe7.md``.
_SERVICE_KINDS: tuple[str, ...] = (
    "orchestrator",
    "memory-write-worker",
)


def service_label(kind: str, slug: str) -> str:
    """Compose the reverse-DNS launchd label for a kind + workspace slug.

    FBE.7: ``"memory-graphiti"`` is no longer in ``_SERVICE_KINDS`` at
    v0.1.0 (the M-FBM floor); calls with that kind raise
    ``ValueError`` until M-GMP re-admits it.
    """
    if kind not in _SERVICE_KINDS:
        raise ValueError(f"unknown service kind: {kind!r}")
    return f"com.loam.{slug}.{kind}"


# ---- confirmation sentence (proposal Q7 — locked wording) ------------


CONFIRMATION_SENTENCE = (
    "pos v2 first-run scaffold complete: thirteen foundational components "
    "configured at defaults (safety/always-ask, cost ceilings, "
    "reversibility, self-correction, memory, degradation), memory "
    "sidecar and orchestrator launched as user services, staging store "
    "initialised. `~/.loam/` is your config dir — edit any file to "
    "adjust. Proceeding."
)


# ---- YAML content — per-component starter defaults -------------------


_BOOTSTRAP_YAML = """\
# ~/.loam/bootstrap.yaml — thirteen-foundational-adapter bundle
# Auto-generated on first run. Edit freely; the scaffold only runs on
# a fresh workspace (no ~/.loam/ directory present) and never overwrites.

# v0.1.6 AC.PSAFE.1 / AC.PSAFE.2 — workspace-level safety profile.
# Legal values: production-stake | dev | research. Default `dev`
# matches today's behavior. `production-stake` activates non-tunable
# floors (audit_trail on; cost_governance.warning_fraction floor at
# 0.6; always_ask floor extended) per Decision P (SOC-2 audit-trail
# floor RESOLVED YES — non-negotiable for SOC-2 compliance posture).
safety_profile: dev

# v0.1.6 AC.SKILLS-BUG.1 — discoverable plugins (filesystem-walk; no
# bootstrap.yaml `contributions:` entry required). Claude Code walks
# `<plugin>/skills/<name>/SKILL.md` natively when the plugin is on
# the Python path. The two plugins shipped with loam:
#   - plugins/loam-skills/  — base SKILLs (memory-recall,
#                              scope-decompose, dispatch-with-gates,
#                              onboarding-conversation, session-handoff,
#                              translation-discipline, audit-block-on-telegram,
#                              owner-decision-summary)
#   - plugins/dev-sdlc/     — dev-mode SKILLs (gated by loam-mode
#                              and plugins/dev-sdlc/dev-mode-manifest.yaml)
# Workspace-local skills land at <workspace>/.claude/skills/<name>/SKILL.md
# (the .gitkeep at scaffold time ensures the directory exists from
# session-zero so live-change-detection picks up new SKILLs without
# session restart).

contributions:
  - name: observability_aggregator
    module: loam.workspace_bootstrap.adapters.observability_aggregator
    class: ObservabilityAggregatorContribution
  - name: safety_layer
    module: loam.workspace_bootstrap.adapters.safety_layer
    class: SafetyLayerContribution
  - name: reversibility_primitive
    module: loam.workspace_bootstrap.adapters.reversibility_primitive
    class: ReversibilityPrimitiveContribution
  - name: cost_governance
    module: loam.workspace_bootstrap.adapters.cost_governance
    class: CostGovernanceContribution
  - name: self_correction
    module: loam.workspace_bootstrap.adapters.self_correction
    class: SelfCorrectionContribution
  - name: memory_system
    module: loam.workspace_bootstrap.adapters.memory_system
    class: MemorySystemContribution
  - name: scope_of_work
    module: loam.workspace_bootstrap.adapters.scope_of_work
    class: ScopeOfWorkContribution
  - name: objective_tracker
    module: loam.workspace_bootstrap.adapters.objective_tracker
    class: ObjectiveTrackerContribution
  - name: primary_persona
    module: loam.workspace_bootstrap.adapters.primary_persona
    class: PrimaryPersonaContribution
  - name: dormancy
    module: loam.workspace_bootstrap.adapters.dormancy
    class: DormancyContribution
  - name: self_upgrade
    module: loam.workspace_bootstrap.adapters.self_upgrade
    class: SelfUpgradeContribution
  - name: workspace_bootstrap_py
    module: loam.workspace_bootstrap.adapters.workspace_bootstrap_py
    class: WorkspaceBootstrapPyContribution
  - name: telegram_interface
    module: loam.workspace_bootstrap.adapters.telegram_interface
    class: TelegramInterfaceContribution
"""

_MEMORY_YAML = """\
# ~/.loam/memory.yaml — sidecar connection + launch config
launch: true
host: 127.0.0.1
port: 8765
health_path: /health
startup_timeout_s: 30
poll_interval_s: 0.5
"""

_MEMORY_STAGING_YAML = """\
# ~/.loam/memory-staging.yaml — degraded-mode staging store
soft_cap: 10000
hard_cap: 50000
db_path: ~/.loam/memory-staging.sqlite
drain_batch_size: 100
probe_interval_s: 30
latency_threshold_ms: 500
"""

_SAFETY_YAML = """\
# ~/.loam/safety/always_ask.yaml — framework-floor always-ask list.
# Add per-workspace entries here; the floor below is non-negotiable.
always_ask:
  - external_payments
  - irreversible_user_data_deletion
  - publishing_to_public_surface
  - sending_as_owner_to_third_party
"""

_COST_YAML = """\
# ~/.loam/cost/ceilings.yaml — advisory starter ceilings.
# Raise or lower to match your workspace budget.
ceilings:
  daily_usd: 5.00
  monthly_usd: 100.00
advisory: true
"""

_REVERSIBILITY_YAML = """\
# ~/.loam/reversibility.yaml — per-tool reversibility classes.
# Empty starter; register per-adapter classes as you add tools.
registrations: {}
"""

_SELF_CORRECTION_YAML = """\
# ~/.loam/self-correction.yaml — four-part protocol knobs.
enabled: true
"""

_DORMANCY_YAML = """\
# ~/.loam/dormancy-config.yaml — per-mode defaults.
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
# ~/.loam/telegram.yaml — per-workspace Telegram channel config.
# Most fields are optional. Leaving this whole file out is fine;
# the adapter boots in degraded-alive mode and the setup
# walkthrough runs on session two.
required: false                       # set true to fail-close boot if creds absent
env_path: ~/.claude/channels/telegram/.env
access_path: ~/.claude/channels/telegram/access.json
default_tier: 2                       # dormancy-config default
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
    "dormancy-config.yaml": _DORMANCY_YAML,
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


# ---- memory.yaml → plist EnvironmentVariables propagation (amendment #29)


def _resolve_memory_host_port(memory_yaml_path: Path) -> tuple[str, int]:
    """Return (host, port) from the workspace's ``memory.yaml``.

    Amendment #29 AC29.2: the plist's ``EnvironmentVariables`` dict
    must carry the workspace-local host + port so launchd starts the
    memory-sidecar with ``GRAPHITI_SERVICE_PORT`` set to the value the
    operator owns. The ``memory.yaml`` file is the source of truth
    (same seam ``adapters/memory_system.py`` already reads for the
    health-probe URL); this function is the read-back that wires the
    value into plist rendering.

    Fallback contract mirrors ``adapters/memory_system.py``'s own
    config-read shape: absent keys fall to the starter-template
    values, matching both the scaffolded ``_MEMORY_YAML`` defaults
    and the sidecar's own ``service.py`` env-var defaults. This
    matches the partial-recovery case where a user-edited
    ``memory.yaml`` remnant (e.g. a comments-only leftover from a
    crashed prior run) must survive the recovery per
    ``test_AC6_scaffold_partial_recovery_writes_missing_and_keeps_existing``.
    """
    loaded = yaml.safe_load(memory_yaml_path.read_text()) or {}
    if not isinstance(loaded, dict):
        loaded = {}
    host = str(loaded.get("host") or "127.0.0.1")
    port = int(loaded.get("port") or 8765)
    return host, port


# ---- scaffold result -------------------------------------------------


@dataclass(frozen=True)
class ScaffoldResult:
    ran: bool
    reason: str  # "already_scaffolded" | "fresh_scaffold" | "dry_run"
    files_written: tuple[str, ...] = ()
    service_files_installed: tuple[str, ...] = ()
    services_bootstrapped: tuple[str, ...] = ()
    confirmation: str | None = None
    # Amendment #36: persona-directory scaffold output. ``persona_dir``
    # is the absolute path to ``<workspace>/personas/<handle>/`` when
    # the scaffold either just installed it or detected it pre-existed
    # (idempotent no-op); ``persona_installed`` is True only when this
    # invocation wrote the directory.
    persona_dir: Path | None = None
    persona_installed: bool = False
    # Amendment #39: tracker-seed scaffold output. The first-run flow
    # seeds the workspace's objective-tracker DB with the value-prop
    # root + spec-tier descendants; ``tracker_seeded`` is True iff
    # this invocation created at least one tracker record. The other
    # fields surface the seed's structured outcome so tests + the
    # confirmation surface can observe what landed. ``classification``
    # is one of ``"pos-v2-dev" | "user"`` per
    # ``tracker_seed.classify_workspace``.
    tracker_seeded: bool = False
    tracker_seed_reason: str | None = None
    tracker_classification: str | None = None
    tracker_root_id: str | None = None
    tracker_descendants_seeded: tuple[str, ...] = ()
    tracker_value_prop_source: str | None = None
    # Amendment #47: workspace-local `.mcp.json` writer output.
    # ``mcp_json_path`` is the absolute path to the workspace's
    # ``.mcp.json`` (set whenever the writer ran, regardless of
    # whether it produced a write); ``mcp_json_wrote`` is True
    # only when this invocation actually changed the file's
    # bytes; ``mcp_json_reason`` is the structured outcome label
    # from ``mcp_json_writer.MCPJsonWriteResult``.
    mcp_json_path: Path | None = None
    mcp_json_wrote: bool = False
    mcp_json_reason: str | None = None


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
    persona_handle: str = DEFAULT_PERSONA_HANDLE,
    persona_template_override: Path | None = None,
    value_prop_path_override: Path | None = None,
    tracker_seed_runner: "Any | None" = None,
) -> ScaffoldResult:
    """Deterministic scaffold implementation, test-callable.

    Parameters
    ----------
    pos_root:
        The ``~/.loam/`` directory to write into. Tests pass a tmp_path.
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
        When False (legacy default), a partial ``~/.loam/`` state
        (directory exists without ``bootstrap.yaml``) raises
        ``PartialScaffoldError`` — the original H4 structural refusal.
        When True, the scaffold repairs the partial state by writing any
        missing files on top of the existing directory, leaving
        user-modified files untouched. Invoked by the detached first-run
        worker on resume when the previous run crashed mid-scaffold —
        the ``partial-scaffold-detected`` halt with "retry next session"
        guidance was itself the terminal user-facing failure mode Luke
        hit on his fresh-clone attempt, which this amendment closes.
    persona_handle:
        Amendment #36 — handle the workspace's primary-persona
        directory is materialised under
        (``<workspace>/personas/<handle>/``). Default
        ``"primary"`` per master-plan D3 (a). Pre-resolve via
        ``resolve_persona_handle`` if the value comes from user
        input. The scaffold itself does not solicit input; resolution
        is the caller's responsibility (today the default is always
        used; the resolver is exposed so future first-run UX layers
        can wire in a one-question prompt without touching this
        adapter).
    persona_template_override:
        Test-only override for the framework persona-template source
        directory. Defaults to ``<repo>/primary-persona/templates/
        persona-template/`` when ``None``.
    value_prop_path_override:
        Amendment #39 — test-only override for the value-prop source
        path the tracker-seed reads. On a workspace classified
        ``"pos-v2-dev"`` the seed reads
        ``<workspace>/docs/VALUE_PROPOSITION.md`` by default;
        on a non-dev workspace it reads
        ``<workspace>/value-prop.md``. The override substitutes
        whichever path applies.
    tracker_seed_runner:
        Amendment #39 — synchronous-callable injection seam for the
        tracker-seed step so tests can substitute a fault-injecting
        runner without touching ``asyncio``. The default invokes
        ``tracker_seed.run_seed_synchronously``. Signature:
        ``runner(*, workspace_root, tracker_db_path, classification,
        value_prop) -> TrackerSeedResult``.
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
    #
    # Amendment #29 (AC29.2 / AC29.3): resolve the per-workspace
    # memory-sidecar host + port from the scaffolded ``memory.yaml``
    # so the plist's ``EnvironmentVariables`` dict carries the
    # workspace-local values rather than the sidecar's built-in
    # defaults. The read-back path gives the starter-default on a
    # fresh scaffold (``_MEMORY_YAML`` declares ``port: 8765``); it
    # honours an operator-edited value on partial-recovery re-runs.
    memory_host, memory_port = _resolve_memory_host_port(pos_root / "memory.yaml")

    service_runner = service_runner or ServiceManagerRunner(platform_label=plat)
    service_files = _install_service_manager_files(
        plat=plat,
        workspace_root=ws,
        slug=slug,
        override_dir=service_manager_dir_override,
        memory_host=memory_host,
        memory_port=memory_port,
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

    # Amendment #36: install the workspace's primary-persona directory
    # from the framework template if it does not already exist. The
    # scaffold writes only when ``personas/<handle>/`` is absent
    # (idempotency per AC36.3); a malformed prior write surfaces a
    # structured diagnostic via ``_install_persona_directory``
    # (AC36.5). The framework-template surface is consumed read-only;
    # the scaffold's only mutations on the copy are setting the
    # ``handle`` field and ``is_starter: true`` (AC36.6).
    persona_installed, persona_dir = _install_persona_directory(
        workspace_root=Path(ws),
        handle=persona_handle,
        template_override=persona_template_override,
    )

    # FBE.7 (v0.1.0 foldback): the workspace-local ``.mcp.json``
    # registration of ``memory-graphiti`` is RETIRED at v0.1.0 per
    # Luke's 2026-05-03 ruling. The M-FBM file-based memory substrate
    # is the v0.1.0 floor; the persona's session-start retrieval path
    # already binds ``primary_persona.file_memory.FileMemoryStore``
    # directly (no MCP roundtrip). The ``mcp_json_writer`` module is
    # preserved on disk (its pure-function builders are imported by
    # AC47.x tests + will be re-wired by the M-GMP plugin post-v0.1.0)
    # but is NOT invoked from the v0.1.0 production scaffold path.
    # See ``docs/plans/v0-1-0-foldback-scope-expansion-fbe7.md``.
    from . import mcp_json_writer as _mcp_json_writer  # noqa: WPS433

    mcp_json_result = _mcp_json_writer.MCPJsonWriteResult(
        wrote=False,
        reason="skipped_v0_1_0_no_graphiti",
        path=None,
    )

    # Amendment J (AC.J.1 / AC.J.4): write the workspace-local
    # ``ollama-prewarm-recommended.txt`` + ``memory-worker.yaml``
    # under <workspace>/workspace/.pos/. Both are advisory + config
    # surfaces the persona/worker reads back; idempotent (won't
    # clobber user edits on partial-recovery or re-runs). Per Hard
    # Constraint 12, pos-v2 does NOT touch the operator's homebrew
    # Ollama plist — the advisory file names the operator-side
    # commands they run themselves.
    j_advisory_written, j_worker_cfg_written = (
        _write_amendment_j_workspace_files(Path(ws))
    )
    if j_advisory_written:
        written.append(f"<workspace>/workspace/.pos/{PREWARM_ADVISORY_FILENAME}")
    if j_worker_cfg_written:
        written.append(f"<workspace>/workspace/.pos/{WORKER_CONFIG_FILENAME}")

    # D-migration D.2 (amendment #63 / AC.D.2.1): scaffold a
    # ``<workspace>/.gitignore`` declaring ``framework/`` as the only
    # tracked subtree. Workspace-state under ``<workspace>/workspace/``
    # is per-workspace runtime state and must not be committed in a
    # derived workspace. Idempotent: existing ``.gitignore`` is left
    # untouched (operator-edits survive).
    workspace_gitignore_written = _write_workspace_gitignore(Path(ws))
    if workspace_gitignore_written:
        written.append("<workspace>/.gitignore")

    # v0.1.6 AC.SKILLS-BUG.2: pre-create ``<workspace>/.claude/skills/``
    # with a zero-byte ``.gitkeep`` so live-change-detection picks up
    # new SKILL.md files without requiring a Claude Code session
    # restart. Per Anthropic's documented live-change semantics, a NEW
    # top-level skills directory needs session restart but new files
    # within an EXISTING directory are picked up live. Pre-creating
    # the directory at scaffold time ensures the workspace is ready
    # for workspace-local skills from session-zero. Idempotent.
    skills_gitkeep_written = _write_skills_gitkeep(Path(ws))
    if skills_gitkeep_written:
        written.append("<workspace>/.claude/skills/.gitkeep")

    # v0.1.7 AC.PERSONAS.6 + AC.PERSONAS.7: symlink plugin-shipped
    # subagent personas (``plugins/<plugin>/agents/<name>.md``) into
    # ``<workspace>/.claude/agents/<name>.md`` so Claude Code's
    # project-agent discovery surface picks them up. Idempotent.
    # Collision (non-symlink file already at the target path) raises
    # ``PluginAgentCollisionError`` — operator-precedence per
    # AC.PERSONAS.7.
    plugin_agents_written = _symlink_plugin_agents(Path(ws))
    written.extend(plugin_agents_written)

    # v0.1.7 Cycle 3 AC.LAYERED.2 + AC.LAYERED.3 + AC.LAYERED.4: symlink
    # plugin-shipped skill directories (``plugins/<plugin>/skills/<name>/``)
    # into ``<workspace>/.claude/skills/<name>`` so Claude Code's
    # project-skill discovery (``<workspace>/.claude/skills/<name>/SKILL.md``
    # per Anthropic spec) picks them up uniformly. Symlink targets the
    # directory (not the SKILL.md file) so companion files in the skill
    # directory survive the discovery walk. Idempotent. Collision
    # (non-symlink file/dir at the target path = workspace-local
    # override, OR two plugins shipping the same skill name = cross-
    # plugin collision) raises ``PluginSkillCollisionError`` —
    # operator-precedence per AC.LAYERED.3 / AC.LAYERED.4.
    plugin_skills_written = _symlink_plugin_skills(Path(ws))
    written.extend(plugin_skills_written)

    # Amendment #39: seed the workspace's objective-tracker DB with
    # the value-prop root + spec-tier descendants. Idempotent by
    # query (the seed-runner uses ``query_projection_view`` to detect
    # already-seeded records and skip). On a workspace classified as
    # pos-v2 dev (``docs/VALUE_PROPOSITION.md`` present at
    # the workspace root), the seed reads that doc as the source of
    # the root's goal + criteria. On a workspace classified non-dev,
    # the seed reads ``<workspace>/value-prop.md`` if present, else
    # skips with a structured diagnostic. AC39.1 / AC39.5 measure
    # the two outcomes; AC39.6 enforces no-payload-in-source.
    tracker_seed_result = _run_tracker_seed(
        workspace_root=Path(ws),
        value_prop_path_override=value_prop_path_override,
        runner=tracker_seed_runner,
    )

    return ScaffoldResult(
        ran=True,
        reason="partial_recovery" if partial_recovery else "fresh_scaffold",
        files_written=tuple(written),
        service_files_installed=tuple(p for _, p in service_files),
        services_bootstrapped=tuple(bootstrapped),
        confirmation=CONFIRMATION_SENTENCE,
        persona_dir=persona_dir,
        persona_installed=persona_installed,
        tracker_seeded=tracker_seed_result.seeded,
        tracker_seed_reason=tracker_seed_result.reason,
        tracker_classification=tracker_seed_result.classification,
        tracker_root_id=tracker_seed_result.root_id,
        tracker_descendants_seeded=tracker_seed_result.descendants_seeded,
        tracker_value_prop_source=tracker_seed_result.value_prop_source,
        mcp_json_path=mcp_json_result.path,
        mcp_json_wrote=mcp_json_result.wrote,
        mcp_json_reason=mcp_json_result.reason,
    )


def _run_mcp_json_writer(
    *,
    workspace_root: Path,
    memory_host: str,
    memory_port: int,
) -> "mcp_json_writer.MCPJsonWriteResult":
    """Helper that invokes the amendment #47 ``.mcp.json`` writer.

    Imported lazily so the scaffold's import graph stays acyclic
    and matches the lazy-import pattern already used for
    ``tracker_seed`` (below). The writer module is stdlib-only,
    so the lazy import is purely structural — there is no
    optional-dependency reason. Returns the raw
    ``MCPJsonWriteResult``; the scaffold consumes its three fields
    and surfaces them on ``ScaffoldResult``. AC47.1 / AC47.2 /
    AC47.3 pivot on this seam.
    """
    from . import mcp_json_writer

    return mcp_json_writer.write_mcp_json(
        workspace_root=workspace_root,
        host=memory_host,
        port=memory_port,
    )


def _run_tracker_seed(
    *,
    workspace_root: Path,
    value_prop_path_override: Path | None,
    runner: Any | None,
) -> "tracker_seed.TrackerSeedResult":
    """Helper that classifies the workspace, loads the value-prop
    source, and dispatches the synchronous tracker-seed runner.

    Imported lazily so the scaffold's import graph stays acyclic
    against ``objective_tracker`` (the seed module imports from
    objective_tracker; importing it at module-load time would force
    every workspace-bootstrap consumer to install the tracker even
    when they're invoking unrelated scaffold code paths).

    Sub-plan E (amendment #42) — ``tracker_db_path_for`` now takes
    ``workspace_root`` (was ``pos_root``); the seed writes to the
    workspace-rooted DB path that amendment #40's contributor reads.
    The previous ``pos_root`` parameter is no longer needed by this
    helper (it was only used to compute the tracker DB path).
    """
    from . import tracker_seed

    classification = tracker_seed.classify_workspace(workspace_root)
    value_prop = tracker_seed.load_value_prop_source(
        workspace_root,
        classification,
        value_prop_path_override=value_prop_path_override,
    )
    tracker_db_path = tracker_seed.tracker_db_path_for(workspace_root)

    seed_runner = runner or tracker_seed.run_seed_synchronously
    return seed_runner(
        workspace_root=workspace_root,
        tracker_db_path=tracker_db_path,
        classification=classification,
        value_prop=value_prop,
    )


# ---- amendment J — workspace-local advisory + worker config helpers


# D.2 (amendment #63): the ``.pos/`` workspace-state directory now
# lives under ``<workspace>/workspace/.pos/`` (not ``<workspace>/.pos/``).
# ``WORKSPACE_POS_DIR`` is preserved as an exported constant for
# backwards compatibility with tests that previously joined it onto
# ``workspace_root``; tests should now use ``pos_subdir(workspace_root)``
# from ``workspace_bootstrap.workspace_paths``.
WORKSPACE_POS_DIR = ".pos"
PREWARM_ADVISORY_FILENAME = "ollama-prewarm-recommended.txt"
WORKER_CONFIG_FILENAME = "memory-worker.yaml"


def _write_amendment_j_workspace_files(
    workspace_root: Path,
) -> tuple[bool, bool]:
    """Write the amendment-J workspace-local advisory + worker config.

    Per Hard Constraint 12 + locked plan §11 D-1: workspace-bootstrap
    is the propagation surface for the operator-facing pre-warm
    recommendation. The file is advisory only — pos-v2 does NOT
    touch the operator's homebrew-installed Ollama plist. The
    persona reads this file on demand via
    ``primary_persona.memory_prewarm.read_prewarm_advisory`` and
    surfaces a recommendation when the env var remains unset
    (AC.J.6).

    Per locked D-3: the worker-config file scaffolds the retry-curve
    defaults; workspaces tune by editing the file. The worker's
    ``load_worker_config`` falls back to the same defaults when the
    file is absent.

    Idempotent: existing files are not overwritten (so user edits
    survive partial-recovery + re-runs). Returns
    ``(advisory_written, worker_config_written)`` — True iff the
    file was actually authored on this invocation.
    """
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    pos_dir = pos_subdir(workspace_root)
    pos_dir.mkdir(parents=True, exist_ok=True)
    advisory_path = pos_dir / PREWARM_ADVISORY_FILENAME
    worker_cfg_path = pos_dir / WORKER_CONFIG_FILENAME
    advisory_written = False
    worker_config_written = False
    if not advisory_path.exists():
        advisory_path.write_text(_OLLAMA_PREWARM_ADVISORY)
        advisory_path.chmod(0o644)
        advisory_written = True
    if not worker_cfg_path.exists():
        worker_cfg_path.write_text(_MEMORY_WORKER_YAML)
        worker_cfg_path.chmod(0o644)
        worker_config_written = True
    return advisory_written, worker_config_written


# ---- amendment J — workspace-local advisory + worker config ---------
#
# Per locked plan §11 D-1 + Hard Constraint 12: pos-v2 does NOT touch
# homebrew-installed files. The advisory file is the operator-facing
# surface that names the recommended OLLAMA_KEEP_ALIVE value (D-5
# locked at 24h) + the operator-side commands to apply it. The
# persona reads this surface back via
# ``primary_persona.memory_prewarm.read_prewarm_advisory`` (AC.J.6).
#
# The worker config file at ``<workspace>/.pos/memory-worker.yaml``
# carries the D-3 retry-curve defaults (5 retries, 2s→60s exp
# backoff). Workspaces tune by editing the file; the worker's
# ``load_worker_config`` helper falls back to the same defaults when
# the file is absent.

# D-migration D.2 (amendment #63 / AC.D.2.1): the scaffolded
# ``<workspace>/.gitignore`` declares ``framework/`` as the only
# tracked subtree. Workspace-state under ``workspace/`` is runtime
# state; ``.claude/`` carries Claude-Code-discoverable artefacts the
# operator may want versioned (per D-Q.A4); everything else is
# off-by-default. Operator can opt anything in by editing the file.
_WORKSPACE_GITIGNORE = """\
# Auto-scaffolded by pos-v2 workspace-bootstrap (D-migration D.2,
# amendment #63). framework/ is the only git-tracked subtree by
# default; everything else is workspace-state and gitignored.
# Operator may opt artefacts back in by adding `!<path>` lines.
*
!.gitignore
!framework
!framework/**
!.claude
!.claude/**
"""


def _write_workspace_gitignore(workspace_root: Path) -> bool:
    """Scaffold ``<workspace>/.gitignore`` if absent.

    Idempotent: existing ``.gitignore`` files are left untouched so
    operator edits survive partial-recovery + re-runs. Returns True
    iff the file was written on this invocation.
    """
    target = Path(workspace_root) / ".gitignore"
    if target.exists():
        return False
    target.write_text(_WORKSPACE_GITIGNORE)
    target.chmod(0o644)
    return True


def _write_skills_gitkeep(workspace_root: Path) -> bool:
    """v0.1.6 AC.SKILLS-BUG.2 — pre-create
    ``<workspace>/.claude/skills/.gitkeep`` so Claude Code's
    live-change-detection picks up new SKILL.md files without a
    session restart.

    Per Anthropic's published SKILL.md primitive (verified 2026-05-04):
    creating a NEW top-level skills directory requires Claude Code
    restart, but NEW files inside an existing directory are picked up
    live. Pre-creating the directory + a zero-byte sentinel at
    scaffold time guarantees the directory exists from session-zero,
    so the operator's first workspace-local SKILL.md drop is live
    without restart.

    Idempotent: an existing ``.gitkeep`` (even with non-zero bytes
    from operator edits) is left untouched. Returns True iff the
    file was authored on this invocation.
    """
    skills_dir = Path(workspace_root) / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    target = skills_dir / ".gitkeep"
    if target.exists():
        return False
    target.write_text("")
    target.chmod(0o644)
    return True


# ---- v0.1.7 Cycle 1: subagent persona registration ----------------------
#
# Plugin-shipped subagent personas live at
# ``plugins/<plugin>/agents/<name>.md`` in the source-of-truth tree. At
# first-run scaffold time, we symlink each into
# ``<workspace>/.claude/agents/<name>.md`` so Claude Code's
# project-agent discovery finds them.
#
# Source-tree resolution:
#   - canonical pos-v2:    <workspace>/plugins/<plugin>/agents/
#   - derived workspaces:  <workspace>/framework/plugins/<plugin>/agents/
# (the D-architecture nests the synced canonical tree under
# ``<workspace>/framework/``; canonical IS the source so plugins live
# at the workspace root.)
#
# Idempotence: existing symlinks pointing at the correct target are
# left untouched. Existing files (non-symlinks) are NOT overwritten —
# operator-precedence: a workspace-authored override at
# ``<workspace>/.claude/agents/<name>.md`` wins. Collision (non-
# symlink file with the same name as a plugin agent) raises
# ``PluginAgentCollisionError`` so the operator can resolve
# explicitly. Per AC.PERSONAS.6 + AC.PERSONAS.7.


class PluginAgentCollisionError(BootstrapError):
    """A plugin agent's target path is already a non-symlink file/dir.

    Operator-precedence: the existing file is preserved; the scaffold
    refuses to overwrite. The operator either renames their file or
    deletes it to accept the plugin agent. Per AC.PERSONAS.7.
    """

    code = ERR_HANDS_OFF_INTERNAL


def _resolve_plugins_root(workspace_root: Path) -> Path | None:
    """Locate the plugins/ directory for the active workspace.

    Two cases:
      - canonical pos-v2 (``<workspace>/plugins/<name>/`` directly)
      - derived workspace (``<workspace>/framework/plugins/<name>/``,
        the D-architecture's nested synced subtree)

    Returns the resolved plugins/ directory, or ``None`` if neither
    location holds a plugins/ directory (no plugin-shipped agents to
    register; not an error — the workspace may simply have no plugins
    enabled yet).
    """
    canonical_candidate = Path(workspace_root) / "plugins"
    if canonical_candidate.is_dir():
        return canonical_candidate
    derived_candidate = Path(workspace_root) / "framework" / "plugins"
    if derived_candidate.is_dir():
        return derived_candidate
    return None


def _symlink_plugin_agents(workspace_root: Path) -> tuple[str, ...]:
    """v0.1.7 AC.PERSONAS.6 — symlink plugin-shipped subagent personas
    from ``plugins/<plugin>/agents/<name>.md`` into
    ``<workspace>/.claude/agents/<name>.md``.

    Walks every plugin under the resolved plugins/ root; for each
    ``<plugin>/agents/<name>.md`` file, creates a symlink at
    ``<workspace>/.claude/agents/<name>.md`` pointing at the absolute
    path of the plugin agent file.

    Idempotent. Returns the tuple of relative paths written
    (or empty tuple when no plugins were present / no agents to
    register).

    Raises ``PluginAgentCollisionError`` when a non-symlink file
    already exists at a target path (operator-precedence: never
    overwrite operator artefacts).
    """
    plugins_root = _resolve_plugins_root(Path(workspace_root))
    if plugins_root is None:
        return ()

    agents_dir = Path(workspace_root) / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for plugin_dir in sorted(plugins_root.iterdir()):
        if not plugin_dir.is_dir():
            continue
        plugin_agents_dir = plugin_dir / "agents"
        if not plugin_agents_dir.is_dir():
            continue
        for agent_file in sorted(plugin_agents_dir.glob("*.md")):
            if not agent_file.is_file():
                continue
            target = agents_dir / agent_file.name
            absolute_source = agent_file.resolve()
            if target.is_symlink():
                # Already a symlink. Verify it points at the correct
                # source. If it does, leave alone (idempotent). If it
                # points elsewhere, treat as operator override and
                # leave alone (operator-precedence). Collision applies
                # only to non-symlink files.
                continue
            if target.exists():
                # Non-symlink collision. Halt-and-surface per
                # AC.PERSONAS.7. Operator resolves explicitly.
                raise PluginAgentCollisionError(
                    "kind=plugin_agent_collision "
                    f"plugin={plugin_dir.name!r} "
                    f"agent={agent_file.name!r} "
                    f"target_path={target!s} — non-symlink file "
                    "already exists; refuse to overwrite."
                )
            target.symlink_to(absolute_source)
            written.append(
                f"<workspace>/.claude/agents/{agent_file.name}"
            )
    return tuple(written)


# ---- v0.1.7 Cycle 3: layered-skill discovery ---------------------------
#
# Plugin-shipped skills live at ``plugins/<plugin>/skills/<name>/SKILL.md``
# in the source-of-truth tree. At first-run scaffold time, we symlink each
# *skill directory* (not the SKILL.md file alone) into
# ``<workspace>/.claude/skills/<name>/`` so Claude Code's project-skill
# discovery surface (``<workspace>/.claude/skills/<name>/SKILL.md`` per the
# Anthropic spec verified 2026-05-04) picks them up uniformly. The symlink
# targets the directory rather than the file because skills can ship
# companion files (scripts/, references/, templates/) that the discovery
# walk needs intact.
#
# Source-tree resolution reuses ``_resolve_plugins_root`` from the agent
# symlinking — same canonical/derived layout logic.
#
# Idempotence + operator-precedence mirror the agent surface: existing
# symlinks pointing at the correct target are left untouched; symlinks
# pointing elsewhere (operator manually retargeted) are left untouched;
# non-symlink collisions raise ``PluginSkillCollisionError`` so the
# operator can resolve explicitly. Per AC.LAYERED.2 / AC.LAYERED.3 /
# AC.LAYERED.4. Cross-plugin collisions (two plugins ship a skill with
# the same name) also raise ``PluginSkillCollisionError`` per AC.LAYERED.4.
#
# Flat-file ``<plugin>/skills/<name>.md`` shapes are NOT auto-symlinked —
# Anthropic discovery is per-directory; flat-file skills are out of fence
# for the auto-symlinking layer.


class PluginSkillCollisionError(BootstrapError):
    """A plugin skill's target path is already a non-symlink file/dir, OR
    two plugins ship a skill with the same name.

    Operator-precedence (workspace-local override case): the existing
    file/dir is preserved; the scaffold refuses to overwrite. The
    operator either renames their override or deletes it to accept the
    plugin skill.

    Cross-plugin case: the operator (or plugin maintainer) renames one
    of the colliding skills.

    Per AC.LAYERED.3 + AC.LAYERED.4.
    """

    code = ERR_HANDS_OFF_INTERNAL


def _symlink_plugin_skills(workspace_root: Path) -> tuple[str, ...]:
    """v0.1.7 AC.LAYERED.2 — symlink plugin-shipped skill directories
    from ``plugins/<plugin>/skills/<name>/`` into
    ``<workspace>/.claude/skills/<name>``.

    Walks every plugin under the resolved plugins/ root; for each
    ``<plugin>/skills/<name>/`` directory containing a ``SKILL.md`` file,
    creates a symlink at ``<workspace>/.claude/skills/<name>`` pointing
    at the absolute path of the plugin skill directory.

    Idempotent. Returns the tuple of relative paths written
    (or empty tuple when no plugins were present / no skills to
    register).

    Raises ``PluginSkillCollisionError`` when:
      - a non-symlink file/dir already exists at a target path
        (workspace-local operator override, AC.LAYERED.3); OR
      - two plugins ship a skill with the same name
        (cross-plugin collision, AC.LAYERED.4).
    """
    plugins_root = _resolve_plugins_root(Path(workspace_root))
    if plugins_root is None:
        return ()

    skills_dir = Path(workspace_root) / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Track which plugin claimed each skill name so we can raise on the
    # cross-plugin collision case (AC.LAYERED.4).
    claimed_by: dict[str, str] = {}

    written: list[str] = []
    for plugin_dir in sorted(plugins_root.iterdir()):
        if not plugin_dir.is_dir():
            continue
        plugin_skills_dir = plugin_dir / "skills"
        if not plugin_skills_dir.is_dir():
            continue
        for skill_dir in sorted(plugin_skills_dir.iterdir()):
            if not skill_dir.is_dir():
                # Skip flat-file <plugin>/skills/<name>.md shapes.
                # Anthropic discovery is per-directory; flat-file
                # skills are out of fence for auto-symlinking.
                continue
            if not (skill_dir / "SKILL.md").is_file():
                # Not a discoverable skill — skip silently.
                continue
            skill_name = skill_dir.name
            # AC.LAYERED.4 — cross-plugin collision. The first plugin
            # to claim the name (alphabetical sort order) holds the
            # symlink; the second raises so the operator (or plugin
            # maintainer) renames one of them.
            if skill_name in claimed_by:
                raise PluginSkillCollisionError(
                    "kind=plugin_skill_cross_plugin_collision "
                    f"skill={skill_name!r} "
                    f"plugin_first={claimed_by[skill_name]!r} "
                    f"plugin_second={plugin_dir.name!r} — two plugins "
                    "ship a skill with the same name; rename one."
                )
            target = skills_dir / skill_name
            absolute_source = skill_dir.resolve()
            if target.is_symlink():
                # Already a symlink. Verify it points at the correct
                # source. If it does, leave alone (idempotent). If it
                # points elsewhere, treat as operator override and
                # leave alone (operator-precedence). Collision applies
                # only to non-symlink files/dirs.
                claimed_by[skill_name] = plugin_dir.name
                continue
            if target.exists():
                # Non-symlink collision (workspace-local override).
                # Halt-and-surface per AC.LAYERED.3. Operator resolves
                # explicitly.
                raise PluginSkillCollisionError(
                    "kind=plugin_skill_workspace_override_collision "
                    f"plugin={plugin_dir.name!r} "
                    f"skill={skill_name!r} "
                    f"target_path={target!s} — non-symlink "
                    "file/directory already exists; refuse to overwrite."
                )
            target.symlink_to(absolute_source)
            claimed_by[skill_name] = plugin_dir.name
            written.append(
                f"<workspace>/.claude/skills/{skill_name}"
            )
    return tuple(written)


_OLLAMA_PREWARM_ADVISORY = """\
OLLAMA_KEEP_ALIVE=24h

# Amendment J / AC.J.1 / D-5 lock — OLLAMA_KEEP_ALIVE recommendation.
#
# pos-v2 cannot set this on the operator's behalf because the env var
# is read by the OLLAMA SERVER process (homebrew-managed launchd
# service), not by memory-system or any pos-v2 component. Per Hard
# Constraint 12, pos-v2 does not edit homebrew-installed files.
#
# To apply the recommendation on this machine, run ONE of:
#
#   # Session-scoped (cleared on logout):
#   launchctl setenv OLLAMA_KEEP_ALIVE 24h
#   brew services restart ollama
#
#   # Persistent across reboots — edit the homebrew Ollama plist:
#   #   /opt/homebrew/Cellar/ollama/<version>/homebrew.mxcl.ollama.plist
#   # Add to its EnvironmentVariables dict:
#   #   <key>OLLAMA_KEEP_ALIVE</key><string>24h</string>
#   # Then:
#   launchctl bootout gui/$(id -u)/homebrew.mxcl.ollama
#   launchctl bootstrap gui/$(id -u) /opt/homebrew/Cellar/ollama/<version>/homebrew.mxcl.ollama.plist
#
# Why 24h: spans typical session-pause envelopes (overnight resumption,
# afternoon breaks). Ollama's eviction logic frees the model from VRAM
# on memory pressure regardless of keep-alive — there is no
# memory-pressure cost.
"""


_MEMORY_WORKER_YAML = """\
# ~/.loam/memory-worker.yaml — amendment J / AC.J.4 retry-curve.
# Workspace-tunable defaults for the long-running memory-write
# worker (drains <workspace>/.pos/memory-write-queue/).

# How many failed attempts before a queue entry moves to the
# dead-letter log (<workspace>/.pos/memory-write-deadletter.log).
max_retries: 5

# Exponential backoff curve: delay_n = initial * 2^(n-1), capped
# at backoff_max_s. Default: 2, 4, 8, 16, 32, 60 (capped) seconds.
backoff_initial_s: 2.0
backoff_max_s: 60.0

# Worker drain-loop poll interval — how long to sleep between
# drain passes when the queue is empty. Lower = faster drain,
# higher CPU. Higher = batchier drain, lower CPU.
poll_interval_s: 1.0

# Stale .tmp file cleanup age — orphaned tmp files older than
# this are removed by the worker's periodic cleanup pass. Real
# enqueues complete the tmp+rename in milliseconds; anything
# older is a never-completed enqueue.
tmp_cleanup_age_s: 3600.0
"""


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
      <string>{workspace}/framework/memory-system/.venv/bin/python</string>
      <string>-m</string><string>src.service</string>
    </array>
    <key>WorkingDirectory</key><string>{workspace}/framework/memory-system</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>ThrottleInterval</key><integer>10</integer>
    <key>StandardOutPath</key><string>{workspace}/framework/memory-system/data/graphiti-service.log</string>
    <key>StandardErrorPath</key><string>{workspace}/framework/memory-system/data/graphiti-service.err.log</string>
    <key>EnvironmentVariables</key><dict><key>PYTHONUNBUFFERED</key><string>1</string><key>GRAPHITI_SERVICE_HOST</key><string>{memory_host}</string><key>GRAPHITI_SERVICE_PORT</key><string>{memory_port}</string><key>LOAM_WORKSPACE_ROOT</key><string>{workspace}</string><key>PATH</key><string>{path}</string></dict>
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
    <key>WorkingDirectory</key><string>{workspace}/workspace</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>ThrottleInterval</key><integer>30</integer>
    <key>ProcessType</key><string>Interactive</string>
    <key>StandardOutPath</key><string>{workspace}/workspace/orchestrator.out.log</string>
    <key>StandardErrorPath</key><string>{workspace}/workspace/orchestrator.err.log</string>
    <key>EnvironmentVariables</key><dict><key>PYTHONUNBUFFERED</key><string>1</string><key>PATH</key><string>{path}</string></dict>
</dict>
</plist>
""",
    # Amendment J / AC.J.5: long-running memory-write-worker drains
    # the per-workspace queue at <workspace>/.pos/memory-write-queue/.
    # Composes on the same launchd-supervised pattern as
    # ``memory-graphiti`` (KeepAlive=true; RunAtLoad=true). Throttle
    # matches the memory-graphiti shape (10s) — short enough that a
    # crash recovers within a typical user-perceived turn cadence,
    # long enough that a launchd-restart-storm cannot hammer the
    # MCP transport. The worker drives ``primary_persona.cli
    # memory-worker --workspace <ws>``; the {workspace} placeholder
    # binds to the per-workspace .venv whose ``primary_persona``
    # editable install carries the worker module.
    "memory-write-worker": """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTD/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>{label}</string>
    <key>ProgramArguments</key>
    <array>
      <string>{workspace}/.venv/bin/python</string>
      <string>-m</string><string>primary_persona.cli</string>
      <string>memory-worker</string>
      <string>--workspace</string><string>{workspace}</string>
    </array>
    <key>WorkingDirectory</key><string>{workspace}/workspace</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>ThrottleInterval</key><integer>10</integer>
    <key>StandardOutPath</key><string>{workspace}/workspace/memory-write-worker.out.log</string>
    <key>StandardErrorPath</key><string>{workspace}/workspace/memory-write-worker.err.log</string>
    <key>EnvironmentVariables</key><dict><key>PYTHONUNBUFFERED</key><string>1</string><key>LOAM_WORKSPACE_ROOT</key><string>{workspace}</string><key>PATH</key><string>{path}</string></dict>
</dict>
</plist>
""",
}


# Amendment #31 (D5.1/D5.2/D5.3): launchd's default PATH
# (``/usr/bin:/bin:/usr/sbin:/sbin``) does not resolve user-installed
# binaries — notably ``claude`` under ``~/.local/bin``. The scaffold
# emits a canonical PATH list into both plists' ``EnvironmentVariables``
# dict so the spawned services can `shutil.which("claude")` at
# construction. Single source of truth: both templates consume the same
# helper output, so D5.2's parse-back equivalence is structural.
#
# Ordering follows research §7.1 flagged-default: user-local bins
# first, Homebrew ARM path next, user-local Homebrew next, then the
# launchd defaults. Host-adaptive resolution (reading the scaffold-
# invoker's ``$PATH``) was rejected per amendment plan §7 inference 1
# because the invoker's env is non-deterministic under the first-run
# hook.
def _launchd_path() -> str:
    """Canonical PATH emitted into launchd plist EnvironmentVariables."""
    return ":".join([
        str(Path.home() / ".local" / "bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
    ])


def _install_service_manager_files(
    *,
    plat: str,
    workspace_root: str,
    slug: str,
    override_dir: Path | None,
    memory_host: str,
    memory_port: int,
) -> list[tuple[str, Path]]:
    """Write launchd plist files into the macOS LaunchAgents dir.

    Labels are computed per workspace slug (amendment #6 + M1c rename):
    ``com.loam.<slug>.<kind>``. The filename matches the label; the
    {label} placeholder in templates is substituted with the full
    label string.

    Amendment #29 (AC29.2 / AC29.3): the memory-graphiti template's
    ``EnvironmentVariables`` dict receives the per-workspace host +
    port values so launchd hands them to the sidecar process at
    service start. The orchestrator template does not carry memory
    port placeholders; its ``.format(...)`` ignores the extra kwargs.

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
    # FBE.7: iterate over ``_SERVICE_KINDS`` (the auto-launched set) not
    # ``_LAUNCHD_TEMPLATES`` (which retains the ``memory-graphiti``
    # entry as a dormant template for M-GMP re-admission post-v0.1.0).
    # This is the seam that makes the kind-removal at line ~227 take
    # effect — without iterating over ``_SERVICE_KINDS`` here, the
    # graphiti plist would still get written despite the kind being
    # absent from the auto-launched set.
    for kind in _SERVICE_KINDS:
        tmpl = _LAUNCHD_TEMPLATES[kind]
        label = service_label(kind, slug)
        path = dest_dir / f"{label}.plist"
        path.write_text(
            tmpl.format(
                label=label,
                workspace=workspace_root,
                memory_host=memory_host,
                memory_port=memory_port,
                path=_launchd_path(),
            )
        )
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


# ---- persona-template + persona-directory install (amendment #36) ----


# Filename for the persona contract emitted by the scaffold. The
# loader's `_load_one` reads `contract.yaml` + `prompt.md` from each
# persona-directory; this constant pins the contract filename so the
# scaffold and the loader agree.
_PERSONA_CONTRACT_FILENAME = "contract.yaml"
_PERSONA_PROMPT_FILENAME = "prompt.md"


def _resolve_persona_template_dir(
    template_override: Path | None = None,
) -> Path:
    """Locate the framework-shipped persona template directory.

    Returns ``<repo>/primary-persona/templates/persona-template/``.
    The scaffold consumes this as a read-only source. ``template_
    override`` is exposed for tests so a tmpfs template can be
    substituted without touching the framework copy.
    """
    if template_override is not None:
        return Path(template_override).resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = (
            parent
            / "primary-persona"
            / "templates"
            / "persona-template"
        )
        if candidate.is_dir():
            return candidate.resolve()
    raise BootstrapError(
        "persona-template-not-found",
        data={"searched_from": str(here)},
    )


def _install_persona_directory(
    *,
    workspace_root: Path,
    handle: str,
    template_override: Path | None = None,
) -> tuple[bool, Path]:
    """Materialise ``<workspace>/personas/<handle>/`` from the
    framework's persona template, with ``handle`` and
    ``is_starter: true`` set on the resulting contract.

    Returns ``(installed, persona_dir)``:

    - ``installed=True`` — this invocation wrote the directory.
    - ``installed=False`` — the directory pre-existed; left
      untouched (idempotency per AC36.3).

    Raises ``PartialScaffoldError`` (with ``kind=
    "persona-scaffold-malformed"`` in the data payload) when the
    persona directory exists but ``contract.yaml`` is empty (zero
    bytes) — the partial-state failure mode the AC36.5 diagnostic
    surfaces. Other malformed-but-non-empty contract content is
    left to the loader's own validator at session start; the
    scaffold's responsibility is the structural "did the prior run
    finish writing the file" check.

    Implementation: copytree to a sibling staging directory, mutate
    the contract YAML in place (handle + is_starter), then rename
    into ``personas/<handle>/``. Atomic-on-success; partial failure
    leaves the staging dir for partial-recovery to clean up.
    """
    from loam.workspace_bootstrap.workspace_paths import personas_dir as _personas_dir

    workspace_root = Path(workspace_root).resolve()
    personas_dir = _personas_dir(workspace_root)
    persona_dir = personas_dir / handle

    contract_path = persona_dir / _PERSONA_CONTRACT_FILENAME
    if persona_dir.exists():
        # Idempotent: if the contract file is present and non-empty,
        # leave the whole directory alone regardless of is_starter
        # value (AC36.3). If the contract is missing or zero-bytes,
        # treat the directory as half-written and surface the
        # AC36.5 diagnostic.
        if not contract_path.exists() or contract_path.stat().st_size == 0:
            raise PartialScaffoldError(
                "partial-scaffold-detected",
                data={
                    "kind": "persona-scaffold-malformed",
                    "persona_dir": str(persona_dir),
                    "contract_path": str(contract_path),
                    "reason": (
                        "persona directory exists but contract.yaml "
                        "is missing or empty — prior scaffold likely "
                        "interrupted mid-write."
                    ),
                },
            )
        return (False, persona_dir)

    template_dir = _resolve_persona_template_dir(template_override)

    personas_dir.mkdir(parents=True, exist_ok=True)
    # Stage into a sibling temp dir so the rename into place is the
    # only operation that makes the dir visible to the loader.
    with tempfile.TemporaryDirectory(
        prefix=f".{handle}.staging.", dir=personas_dir
    ) as staging_root:
        staging = Path(staging_root) / handle
        shutil.copytree(template_dir, staging)
        # Mutate the contract YAML — set handle + is_starter.
        staging_contract = staging / _PERSONA_CONTRACT_FILENAME
        contract_text = staging_contract.read_text()
        loaded = yaml.safe_load(contract_text)
        if not isinstance(loaded, dict):
            raise BootstrapError(
                "persona-template-malformed",
                data={
                    "template_dir": str(template_dir),
                    "contract_path": str(staging_contract),
                },
            )
        loaded["handle"] = handle
        loaded["is_starter"] = True
        staging_contract.write_text(
            yaml.safe_dump(loaded, sort_keys=False, default_flow_style=False)
        )
        # Atomic move into final position.
        os.rename(staging, persona_dir)

    return (True, persona_dir)


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
        # config_dir is the ~/.loam/ directory per proposal §7.
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
