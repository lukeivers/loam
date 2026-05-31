"""The STATE-OF-LOAM operative-reality record (AC.SOL-RECORD.*).

GENERATED FRESH from ground truth on every read (D1 = generate-fresh).
There is no persisted prose source the record is copied from — the
whole failure class this slice fixes is "a persisted record drifted
from reality", so a persisted record would reintroduce exactly that
surface. Editing a rendered record by hand has no effect on the next
generation: it regenerates from the git ref graph + seal sidecars +
live config + real probes.

The record is a list of :class:`ComponentState` rows, each carrying a
component name + its derived :class:`probe.Liveness` class + the
ground-truth EVIDENCE that produced the class (the seal SHA, the config
marker, the probe outcome). The renderer (:func:`render_record`)
produces a terse always-loadable summary (AC.SOL-RECORD.3), not an
unwieldy dump.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from loam_cli.audit.probe import (
    Liveness,
    classify_backend_liveness,
    classify_build_status,
    classify_hook_wired,
)


@dataclass(frozen=True)
class ComponentState:
    """One derived row of the STATE-OF-LOAM record.

    *name* identifies the component / hook / backend; *liveness* is the
    ground-truth-derived class; *evidence* is the human-readable trail
    that produced it (the seal SHA + ancestry, the config marker, the
    real-probe outcome) — so the record carries WHY, not a bare verdict.
    *kind* is ``"component"`` / ``"hook"`` / ``"backend"`` for the
    renderer's grouping.
    """

    name: str
    liveness: Liveness
    kind: str
    evidence: str


@dataclass(frozen=True)
class StateOfLoam:
    """The full derived record — a generated-fresh snapshot.

    Carries the component rows + the HEAD SHA the snapshot was derived
    against (so a consumer can tell which ground-truth point produced
    it). Never persisted as prose; regenerated on every read.
    """

    head_sha: str
    components: tuple[ComponentState, ...]

    def by_name(self, name: str) -> ComponentState | None:
        for row in self.components:
            if row.name == name:
                return row
        return None


# A backend-class probe spec: a name, the static-config verdict, and a
# cheap real-probe callable. The default registry below carries the
# loam-internal backend(s) whose liveness is NOT config-derivable and so
# needs a real probe (the load-bearing F2). Callers may pass their own.
@dataclass(frozen=True)
class BackendProbeSpec:
    name: str
    config_says_wired: bool
    real_probe: Callable[[], bool]


# A hook probe spec: a name + the marker substring that identifies the
# hook's command in settings.json.
@dataclass(frozen=True)
class HookProbeSpec:
    name: str
    marker: str


# A component (build-class) probe spec: a name + its seal sidecar path
# (relative to repo root).
@dataclass(frozen=True)
class ComponentProbeSpec:
    name: str
    seal_sidecar_relpath: str


def _head_sha(repo_root: Path) -> str:
    import subprocess

    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "UNKNOWN"


def _load_settings(settings_path: Path | None) -> dict:
    if settings_path is None or not settings_path.is_file():
        return {}
    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def generate_record(
    repo_root: Path,
    *,
    component_specs: tuple[ComponentProbeSpec, ...] = (),
    hook_specs: tuple[HookProbeSpec, ...] = (),
    backend_specs: tuple[BackendProbeSpec, ...] = (),
    settings_path: Path | None = None,
) -> StateOfLoam:
    """Generate the STATE-OF-LOAM record FRESH from ground truth.

    This is the D1 generate-fresh entry point: every call re-derives
    each row from the git ref graph (component build status), the live
    ``settings.json`` (hook wired/dark), and the real backend probes
    (backend wired/dark). Nothing is read from a persisted record — so
    the result cannot have drifted (AC.SOL-RECORD.1).

    A change in ground truth (a new seal merged, a hook added to
    ``settings.json``, a backend going live) is reflected on the NEXT
    call with no manual edit (AC.SOL-RECORD.2).
    """
    rows: list[ComponentState] = []

    for cspec in component_specs:
        sidecar = repo_root / cspec.seal_sidecar_relpath
        liveness = classify_build_status(repo_root, seal_sidecar=sidecar)
        if liveness is Liveness.MERGED:
            ev = f"seal sidecar {cspec.seal_sidecar_relpath} ancestor of HEAD"
        elif liveness is Liveness.SEALED:
            ev = (
                f"seal sidecar {cspec.seal_sidecar_relpath} sealed but not "
                f"reachable from HEAD"
            )
        elif liveness is Liveness.UNBUILT:
            ev = f"no seal sidecar at {cspec.seal_sidecar_relpath}"
        else:
            ev = (
                f"seal sidecar {cspec.seal_sidecar_relpath} SHA not a known "
                f"git object (indeterminate — fail-safe)"
            )
        rows.append(
            ComponentState(
                name=cspec.name,
                liveness=liveness,
                kind="component",
                evidence=ev,
            )
        )

    settings = _load_settings(settings_path)
    for hspec in hook_specs:
        liveness = classify_hook_wired(settings, marker=hspec.marker)
        if liveness is Liveness.WIRED:
            ev = f"settings.json carries a hook command matching {hspec.marker!r}"
        else:
            ev = f"no settings.json hook command matches {hspec.marker!r}"
        rows.append(
            ComponentState(
                name=hspec.name,
                liveness=liveness,
                kind="hook",
                evidence=ev,
            )
        )

    for bspec in backend_specs:
        liveness = classify_backend_liveness(
            config_says_wired=bspec.config_says_wired,
            real_probe=bspec.real_probe,
        )
        if liveness is Liveness.WIRED:
            ev = "config wired AND real probe succeeded (live end-to-end)"
        elif bspec.config_says_wired:
            ev = (
                "config says wired but the REAL probe FAILED — dark in "
                "reality (the graphiti class)"
            )
        else:
            ev = "config does not declare the backend (not even wired)"
        rows.append(
            ComponentState(
                name=bspec.name,
                liveness=liveness,
                kind="backend",
                evidence=ev,
            )
        )

    return StateOfLoam(head_sha=_head_sha(repo_root), components=tuple(rows))


def render_record(record: StateOfLoam) -> str:
    """Render the record as a TERSE always-loadable summary
    (AC.SOL-RECORD.3) — grouped by kind, one line per component,
    bounded. Not a full dump.
    """
    lines: list[str] = [
        f"# STATE-OF-LOAM (derived @ {record.head_sha[:12]})",
        "",
    ]
    for kind, header in (
        ("component", "Components (built/sealed/merged from refs)"),
        ("hook", "Hooks (wired/dark from live config)"),
        ("backend", "Backends (wired/dark from real probe)"),
    ):
        kind_rows = [r for r in record.components if r.kind == kind]
        if not kind_rows:
            continue
        lines.append(f"## {header}")
        for r in kind_rows:
            lines.append(f"  {r.name}: {r.liveness.value}  — {r.evidence}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
