"""Main composition engine — reads manifest, orders contributions,
constructs host, runs contributions by phase, coordinates shutdown.

The entry point here is `Bootstrapper.run()` (async). CLI wrappers
may call `run_sync()` which manages the asyncio loop.

Phase sequencing:

  1. `before_orchestrator_start` contributions run first. These install
     the OTel tracer provider, launch the memory sidecar, load the
     persona, and register names for declaration-only adapters.

  2. Orchestrator is started (via its `_startup()` as a coroutine).
     Its constructed attributes (scope_runtime, objective_tracker,
     monitor, ipc_server) are copied onto the host so later
     contributions see them.

  3. `wrap_activate_scope` contributions run — each wraps
     `host.ipc_server`'s `activate_scope` handler. Registration order
     matches the topological sort, which yields dispatch order
     safety → reversibility → cost → orig_activate (per the sealed
     integration test in cost-governance).

  4. `after_orchestrator_ready` contributions run — self-correction
     subscribes, self-upgrade probes, the escape-hatch
     `~/.loam/bootstrap.py` loader fires.

Shutdown reverses startup: registered shutdown hooks run in LIFO
order; then the orchestrator's `_shutdown()` runs.
"""

from __future__ import annotations

import asyncio
import inspect
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from .discovery import read_metadata, resolve_ref
from .errors import (
    AdapterRaisedError,
    BootstrapError,
    ContributionNotFoundError,
    MetadataInvalidError,
    NameCollisionError,
)
from .host import BootstrapHost
from .manifest import Manifest, load_manifest
from .ordering import topological_order
from .spec import PHASE_ORDER, ContributionMetadata, Phase


@dataclass
class ResolvedContribution:
    name: str
    metadata: ContributionMetadata
    instance: Any
    display: str


class Bootstrapper:
    """Top-level boot coordinator. Holds the manifest and host; runs
    contributions in order; coordinates shutdown."""

    def __init__(self, manifest: Manifest) -> None:
        self.manifest = manifest
        self.host = BootstrapHost(
            config_dir=manifest.config_dir,
            workspace_root=manifest.workspace_root,
            manifest_path=manifest.manifest_path,
        )
        self._ordered_by_phase: dict[Phase, list[ResolvedContribution]] = {}
        self._completed_contributions: list[ResolvedContribution] = []

    # ------------------------------------------------------------------
    # Resolution + ordering (synchronous)
    # ------------------------------------------------------------------

    def resolve_and_order(self) -> None:
        """Resolve every manifest entry, validate metadata, detect
        name collisions, and topologically sort within each phase."""
        resolved: list[ResolvedContribution] = []
        seen_names: dict[str, str] = {}

        for ref in self.manifest.refs:
            cls = resolve_ref(ref)
            md = read_metadata(cls, ref_label=ref.label)
            if md.name in seen_names:
                raise NameCollisionError(
                    f"two contributions declare name {md.name!r}: "
                    f"{seen_names[md.name]!r} and {ref.label!r}",
                    data={
                        "name": md.name,
                        "prior": seen_names[md.name],
                        "new": ref.label,
                    },
                )
            seen_names[md.name] = ref.label
            try:
                instance = cls()
            except TypeError as e:
                raise MetadataInvalidError(
                    f"{ref.label}: contribution class must be "
                    f"instantiable with no args (got {e})",
                    data={"ref": ref.label, "error": str(e)},
                ) from e
            resolved.append(
                ResolvedContribution(
                    name=md.name,
                    metadata=md,
                    instance=instance,
                    display=ref.label,
                )
            )

        # Group by phase then topo-sort each phase.
        by_phase: dict[Phase, list[ResolvedContribution]] = {
            p: [] for p in PHASE_ORDER
        }
        for rc in resolved:
            by_phase[rc.metadata.phase].append(rc)

        all_names = {rc.name: rc.metadata.phase for rc in resolved}

        ordered: dict[Phase, list[ResolvedContribution]] = {}
        for phase in PHASE_ORDER:
            items = by_phase[phase]
            intra_triples: list[
                tuple[str, tuple[str, ...], tuple[str, ...]]
            ] = []
            for rc in items:
                # Validate cross-phase references exist in the manifest
                # somewhere (not in arbitrary other Python); strip them
                # from the intra-phase triples because cross-phase
                # ordering is handled by the fixed phase order.
                intra_after = tuple(
                    n for n in rc.metadata.after if _validate_and_keep(
                        name=n, referrer=rc.name, referrer_phase=phase,
                        all_names=all_names, kind="after",
                    )
                )
                intra_before = tuple(
                    n for n in rc.metadata.before if _validate_and_keep(
                        name=n, referrer=rc.name, referrer_phase=phase,
                        all_names=all_names, kind="before",
                    )
                )
                intra_triples.append((rc.name, intra_after, intra_before))
            name_order = topological_order(
                intra_triples, phase_label=phase.value
            )
            by_name = {rc.name: rc for rc in items}
            ordered[phase] = [by_name[n] for n in name_order]
        self._ordered_by_phase = ordered

    # ------------------------------------------------------------------
    # Run contributions by phase (async)
    # ------------------------------------------------------------------

    async def run_contributions(self) -> None:
        """Execute contributions phase by phase. `before` phase runs
        first, then `wrap`, then `after`. Shutdown hooks registered
        during these runs fire in reverse on teardown."""
        with self.host.tracer.start_as_current_span(
            "loam.bootstrap.ordering_resolved",
            attributes={
                "loam.bootstrap.phase_counts": _phase_counts_str(
                    self._ordered_by_phase
                ),
            },
        ):
            pass

        for phase in PHASE_ORDER:
            await self._run_phase(phase)

    async def _run_phase(self, phase: Phase) -> None:
        contributions = self._ordered_by_phase.get(phase, [])
        self.host._enter_phase(phase)
        tracer = self.host.tracer
        with tracer.start_as_current_span(
            "loam.bootstrap.phase",
            attributes={
                "loam.bootstrap.phase": phase.value,
                "loam.bootstrap.contribution_count": len(contributions),
            },
        ) as phase_span:
            for rc in contributions:
                await self._run_one(rc, phase_span=phase_span)
        # Emit phase_complete on a FRESH span AFTER the phase span
        # closes, so it records even when the enclosing phase span
        # was NonRecording (e.g. before observability_aggregator's
        # contribution registers the TracerProvider).
        with tracer.start_as_current_span(
            "loam.bootstrap.phase_complete_marker",
            attributes={"loam.bootstrap.phase": phase.value},
        ) as done_span:
            done_span.add_event(
                "loam.bootstrap.phase_complete",
                {"loam.bootstrap.phase": phase.value},
            )

    async def _run_one(self, rc: ResolvedContribution, *, phase_span: Any) -> None:
        # Emit started / completed events on fresh spans AFTER each
        # contribute() call completes. Reason: the
        # observability_aggregator contribution itself registers the
        # OTel TracerProvider. A span opened BEFORE that call is a
        # no-op NonRecordingSpan; events/attributes added to it are
        # discarded. Opening spans AFTER contribute() returns lets
        # the events land in the aggregator once the provider is set.
        tracer = self.host.tracer

        try:
            result = rc.instance.contribute(self.host)
            if inspect.isawaitable(result):
                await result
        except BootstrapError:
            with tracer.start_as_current_span(
                "loam.bootstrap.contribution_failed_marker",
                attributes={"loam.bootstrap.contribution_name": rc.name},
            ) as fail_span:
                fail_span.add_event(
                    "loam.bootstrap.contribution_failed",
                    {"loam.bootstrap.contribution_name": rc.name},
                )
            raise
        except Exception as e:
            with tracer.start_as_current_span(
                "loam.bootstrap.contribution_failed_marker",
                attributes={
                    "loam.bootstrap.contribution_name": rc.name,
                    "loam.bootstrap.exception_type": type(e).__name__,
                },
            ) as fail_span:
                fail_span.add_event(
                    "loam.bootstrap.contribution_failed",
                    {
                        "loam.bootstrap.contribution_name": rc.name,
                        "loam.bootstrap.exception_type": type(e).__name__,
                    },
                )
            raise AdapterRaisedError(
                f"contribution {rc.name!r} raised: "
                f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
                data={
                    "contribution": rc.name,
                    "exception_type": type(e).__name__,
                    "message": str(e),
                },
            ) from e

        with tracer.start_as_current_span(
            "loam.bootstrap.contribution_completed_marker",
            attributes={"loam.bootstrap.contribution_name": rc.name},
        ) as done_span:
            # Emit both started and completed on the same post-contribute
            # span — start/complete pair is captured atomically after
            # the TracerProvider has been installed.
            done_span.add_event(
                "loam.bootstrap.contribution_started",
                {"loam.bootstrap.contribution_name": rc.name},
            )
            done_span.add_event(
                "loam.bootstrap.contribution_completed",
                {"loam.bootstrap.contribution_name": rc.name},
            )
        self._completed_contributions.append(rc)

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    async def shutdown(self) -> None:
        """Reverse-order teardown. Exceptions are caught and logged as
        span events; shutdown continues so no adapter is left orphaned.
        """
        tracer = self.host.tracer
        with tracer.start_as_current_span(
            "loam.bootstrap.shutdown",
            attributes={
                "loam.bootstrap.hook_count": len(self.host._shutdown_hooks),
            },
        ) as span:
            for name, hook in reversed(self.host._shutdown_hooks):
                try:
                    result = hook()
                    if inspect.isawaitable(result):
                        await result
                except Exception as e:
                    span.add_event(
                        "loam.bootstrap.shutdown_hook_failed",
                        {
                            "loam.bootstrap.hook_name": name,
                            "loam.bootstrap.exception_type": type(e).__name__,
                            "loam.bootstrap.message": str(e),
                        },
                    )
        self.host._exit_all_phases()

    # ------------------------------------------------------------------
    # Top-level convenience
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Full boot: resolve, order, run, then wait for stop. Callers
        that need a programmatic stop hook should use `start()` +
        `shutdown()` directly; this helper is for non-test usage."""
        self.resolve_and_order()
        await self.run_contributions()
        # The orchestrator, when present, owns its own event loop via
        # `Orchestrator.run()`. Bootstrap does NOT `await` it here
        # because tests compose in a context manager; the workspace
        # deployment script (entry-point script below) handles that.

    async def start(self) -> None:
        """Resolve + run phases only. Does not own the orchestrator's
        event loop. Returns once all contributions have run."""
        self.resolve_and_order()
        await self.run_contributions()


def _phase_counts_str(by_phase: dict[Phase, list[ResolvedContribution]]) -> str:
    return ", ".join(f"{p.value}={len(v)}" for p, v in by_phase.items())


def _validate_and_keep(
    *,
    name: str,
    referrer: str,
    referrer_phase: Phase,
    all_names: dict[str, Phase],
    kind: str,
) -> bool:
    """Return True if the reference should be kept for intra-phase
    topo-sort; False if it is satisfied by cross-phase ordering.

    Raises UnknownReferenceError if the referenced name does not exist
    anywhere in the manifest (catches typos).

    Raises UnknownReferenceError if `before` points at an earlier-phase
    contribution (logically impossible — a later-phase item cannot
    precede an earlier-phase one).
    """
    from .errors import UnknownReferenceError

    if name not in all_names:
        raise UnknownReferenceError(
            f"contribution {referrer!r} declares {kind}={name!r} "
            f"but no such contribution is listed in the manifest",
            data={"contribution": referrer, "reference": name, "kind": kind},
        )

    ref_phase = all_names[name]
    if ref_phase == referrer_phase:
        return True  # intra-phase — keep for topo-sort.

    # Cross-phase reference: validate consistency with fixed phase order.
    referrer_idx = PHASE_ORDER.index(referrer_phase)
    ref_idx = PHASE_ORDER.index(ref_phase)
    if kind == "after" and ref_idx > referrer_idx:
        raise UnknownReferenceError(
            f"contribution {referrer!r} (phase {referrer_phase.value!r}) "
            f"declares after={name!r} (phase {ref_phase.value!r}) — but "
            f"{name!r}'s phase runs LATER than {referrer!r}'s. Cross-phase "
            f"after-reference must point to an earlier or same phase.",
            data={
                "contribution": referrer,
                "reference": name,
                "kind": kind,
                "referrer_phase": referrer_phase.value,
                "ref_phase": ref_phase.value,
            },
        )
    if kind == "before" and ref_idx < referrer_idx:
        raise UnknownReferenceError(
            f"contribution {referrer!r} (phase {referrer_phase.value!r}) "
            f"declares before={name!r} (phase {ref_phase.value!r}) — but "
            f"{name!r}'s phase runs EARLIER than {referrer!r}'s.",
            data={
                "contribution": referrer,
                "reference": name,
                "kind": kind,
                "referrer_phase": referrer_phase.value,
                "ref_phase": ref_phase.value,
            },
        )
    # Cross-phase reference is consistent with phase order — drop from
    # intra-phase topo input (phase order handles the ordering).
    return False


# ----------------------------------------------------------------------
# CLI / deployment helpers
# ----------------------------------------------------------------------


def cli_main(argv: Optional[list[str]] = None) -> int:
    """`pos-bootstrap` entry point.

    Usage: `pos-bootstrap [--manifest PATH]`. Resolves the manifest,
    runs all contributions, and — when the orchestrator has been
    constructed — awaits its `run()` until SIGTERM/SIGINT.
    """
    import argparse

    parser = argparse.ArgumentParser(prog="pos-bootstrap")
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to bootstrap.yaml (default: $POS_BOOTSTRAP_MANIFEST "
        "or ~/.loam/bootstrap.yaml)",
    )
    args = parser.parse_args(argv)

    manifest_path = args.manifest
    if manifest_path is None:
        import os

        env = os.environ.get("POS_BOOTSTRAP_MANIFEST")
        if env:
            manifest_path = env
        else:
            manifest_path = str(Path.home() / ".loam" / "bootstrap.yaml")

    try:
        manifest = load_manifest(manifest_path)
        bs = Bootstrapper(manifest)
        asyncio.run(_deploy(bs))
    except BootstrapError as e:
        print(
            f"bootstrap refused ({e.code}): {e.message}", file=sys.stderr
        )
        return 2
    return 0


async def _deploy(bs: Bootstrapper) -> None:
    await bs.start()
    # If an orchestrator was installed, run its event loop until signal.
    orch = bs.host.orchestrator
    try:
        if orch is not None and hasattr(orch, "_stop_event"):
            # The orchestrator-contribution calls `_startup()` directly
            # during `wrap_activate_scope`, so the event loop only needs
            # to wait for the stop event.
            # Install signal handlers so SIGTERM/SIGINT cleanly stop.
            import signal

            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                try:
                    loop.add_signal_handler(sig, orch.request_stop)
                except NotImplementedError:
                    pass
            await orch._stop_event.wait()
    finally:
        await bs.shutdown()
