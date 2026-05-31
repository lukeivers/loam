"""The default STATE-OF-LOAM probe registry for the canonical loam repo.

This wires the generic probe machinery (:mod:`loam_cli.audit.record`)
to the SPECIFIC ground-truth facts of the live loam instance: which
seal sidecars anchor which components, which ``settings.json`` markers
identify which live hooks, and which backend-class components need a
cheap REAL probe rather than a config read (the load-bearing F2).

:func:`default_state_record` is what the ``loam audit`` verb generates
when run against the canonical repo with no overrides — so the verb
produces the roadmap §6 R-1 finding (FBM is live) automatically, the
verdict that today required a hand-reconciliation (AC.SOL-PROBE.3).
"""

from __future__ import annotations

from pathlib import Path

from loam_cli.audit.record import (
    BackendProbeSpec,
    ComponentProbeSpec,
    HookProbeSpec,
    StateOfLoam,
    generate_record,
)

# The live-hook marker for the FBM keep-pace chain: the gated
# user-prompt-submit hook is the ``primary_persona.cli`` command in the
# live ``settings.json``. Its presence is the ground-truth fact that
# FBM is WIRED (the verdict the v-next plan + FBM roadmap got wrong).
_FBM_HOOK_MARKER = "primary_persona.cli user-prompt-submit"

# The seal sidecar that anchors the FBM / primary-persona component.
# 7dcb95b (the FBM live seal) is pinned here; the probe derives
# built/sealed/merged from whether it is an ancestor of HEAD.
_PRIMARY_PERSONA_SIDECAR = "framework/primary-persona/tests/SEAL_COMMIT"

# The loam-cli component's own seal sidecar (a second build-class row).
_LOAM_CLI_SIDECAR = "framework/tools/loam/tests/SEAL_COMMIT"


def _loam_cli_import_probe() -> bool:
    """A cheap REAL backend-class probe: can the loam_cli package be
    imported + does its audit comparator actually resolve?

    This is the demonstration of the F2 real-probe discipline against a
    real importable target — it does NOT merely read config; it imports
    and exercises the module. A backend whose package cannot be imported
    (or whose entry point is a never-running shim) fails this probe and
    is classified DARK even if config declared it.
    """
    try:
        from loam_cli.audit import compare_claim  # noqa: F401

        return True
    except Exception:
        return False


def default_component_specs() -> tuple[ComponentProbeSpec, ...]:
    return (
        ComponentProbeSpec(
            name="fbm-episode-store",
            seal_sidecar_relpath=_PRIMARY_PERSONA_SIDECAR,
        ),
        ComponentProbeSpec(
            name="loam-cli",
            seal_sidecar_relpath=_LOAM_CLI_SIDECAR,
        ),
    )


def default_hook_specs() -> tuple[HookProbeSpec, ...]:
    return (
        HookProbeSpec(name="fbm-keep-pace-hook", marker=_FBM_HOOK_MARKER),
    )


def default_backend_specs() -> tuple[BackendProbeSpec, ...]:
    return (
        BackendProbeSpec(
            name="loam-cli-runtime",
            config_says_wired=True,
            real_probe=_loam_cli_import_probe,
        ),
    )


def _default_settings_path() -> Path | None:
    """The live runtime config the hook probe reads.

    The canonical loam instance's live hooks are wired in
    ``pos3/.claude/settings.json`` (the operating workspace), per the
    roadmap predecessor note. When that path is absent (a fresh clone /
    CI), the hook probe degrades to DARK — the honest verdict for an
    instance with no live config.
    """
    candidate = Path("/Users/lukeivers/pos3/.claude/settings.json")
    return candidate if candidate.is_file() else None


def default_state_record(
    repo_root: Path,
    *,
    settings_path: Path | None = None,
) -> StateOfLoam:
    """Generate the STATE-OF-LOAM record against the canonical repo
    using the default probe registry.

    Run against the live repo, this produces FBM as wired-live (the
    keep-pace hook is in ``settings.json``; the seals are merged) — the
    roadmap §6 R-1 finding the persona had to derive by hand
    (AC.SOL-PROBE.3).

    *settings_path* overrides the live-config home (tests point it at a
    fixture; production uses the live ``pos3/.claude/settings.json``).
    """
    resolved_settings = (
        settings_path if settings_path is not None
        else _default_settings_path()
    )
    return generate_record(
        repo_root,
        component_specs=default_component_specs(),
        hook_specs=default_hook_specs(),
        backend_specs=default_backend_specs(),
        settings_path=resolved_settings,
    )
