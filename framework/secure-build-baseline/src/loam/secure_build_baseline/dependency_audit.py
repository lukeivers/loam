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

"""AC.SBB.2 — the dependency-hygiene audit gate.

On a build of a supported-ecosystem artifact (Node/Next + Python first),
this composes on the ecosystem's OWN audit tool (``npm audit`` /
``pip-audit``) — Lens 1: we shell out to the tool that already owns the
vulnerability database, never re-implement one. The raw audit JSON is
parsed, vulnerabilities at or above a configured severity floor are
counted, and the gate decision is returned. A clean audit passes silently;
a vuln at/above floor blocks-or-surfaces per the configured strictness.

Honesty (Lens 0): when the ecosystem's audit tool is NOT available, the
result is marked ``tool_available=False`` and the gate SURFACES that the
audit could not run — it never silently reports "clean" for an audit that
did not actually execute.

The ecosystem audit is invoked through an injectable *runner* so the gate
decision logic is testable without the network / a globally-installed
tool; the default runner shells out to the real tool.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


# Severity ladder, low → high. ``unknown`` sorts as meeting any floor
# (conservative: a vuln whose severity the tool did not report is treated
# as floor-meeting so it surfaces rather than silently passing).
_SEVERITY_ORDER: dict[str, int] = {
    "info": 0,
    "low": 1,
    "moderate": 2,
    "medium": 2,
    "high": 3,
    "critical": 4,
    "unknown": 99,
}

DEFAULT_SEVERITY_FLOOR = "high"

# Ecosystem markers — which files declare a supported ecosystem.
_ECOSYSTEM_MARKERS: dict[str, tuple[str, ...]] = {
    "node": ("package.json",),
    "python": ("requirements.txt", "pyproject.toml", "Pipfile"),
}


@dataclass(frozen=True)
class AuditRun:
    """Raw result of invoking an ecosystem audit tool."""

    available: bool
    raw: str = ""
    error: str | None = None


@dataclass(frozen=True)
class AuditResult:
    """The gate-relevant outcome of a dependency audit for one ecosystem."""

    ecosystem: str
    tool_available: bool
    floor: str
    findings_at_or_above_floor: tuple[str, ...] = field(default_factory=tuple)
    parse_error: str | None = None

    @property
    def is_clean(self) -> bool:
        """True iff the audit ran AND found nothing at/above the floor."""
        return (
            self.tool_available
            and self.parse_error is None
            and not self.findings_at_or_above_floor
        )

    @property
    def must_surface_unavailable(self) -> bool:
        """True iff the audit could not actually run (tool absent / parse
        failure) — the gate must SURFACE this, never silently pass."""
        return (not self.tool_available) or (self.parse_error is not None)


Runner = Callable[[str, Path], AuditRun]


def detect_ecosystems(project_dir: Path) -> list[str]:
    """Return the supported ecosystems whose marker files exist in
    *project_dir* (deterministic order: node, python)."""
    found: list[str] = []
    for eco in ("node", "python"):
        markers = _ECOSYSTEM_MARKERS[eco]
        if any((project_dir / m).exists() for m in markers):
            found.append(eco)
    return found


def _severity_rank(severity: str) -> int:
    return _SEVERITY_ORDER.get(severity.strip().lower(), _SEVERITY_ORDER["unknown"])


def _default_runner(ecosystem: str, project_dir: Path) -> AuditRun:
    """Shell out to the ecosystem's real audit tool. Lens 1 compose."""
    if ecosystem == "node":
        cmd = ["npm", "audit", "--json"]
    elif ecosystem == "python":
        cmd = ["pip-audit", "-f", "json"]
    else:
        return AuditRun(available=False, error=f"unsupported ecosystem {ecosystem!r}")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        # The audit tool is not installed — honestly surface, never fake.
        return AuditRun(available=False, error=f"{cmd[0]} not found on PATH")
    except (OSError, subprocess.SubprocessError) as exc:
        return AuditRun(available=False, error=f"{cmd[0]} failed: {exc}")
    # npm audit / pip-audit exit NON-zero when vulnerabilities are present;
    # that is a successful run with findings, not a tool failure — the JSON
    # on stdout is authoritative.
    return AuditRun(available=True, raw=proc.stdout or "")


def _parse_findings(ecosystem: str, raw: str, floor_rank: int) -> tuple[list[str], str | None]:
    """Parse audit JSON into the list of finding labels at/above the floor.

    Returns ``(findings, parse_error)``. A parse error surfaces (the gate
    treats an unparseable audit as must-surface, never as clean)."""
    raw = raw.strip()
    if not raw:
        return [], "empty audit output"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [], f"unparseable audit JSON: {exc}"

    findings: list[str] = []
    if ecosystem == "node":
        # npm audit v7+: {"vulnerabilities": {"<pkg>": {"severity": ...}}}
        vulns = data.get("vulnerabilities")
        if isinstance(vulns, dict):
            for pkg, info in vulns.items():
                sev = "unknown"
                if isinstance(info, dict) and isinstance(info.get("severity"), str):
                    sev = info["severity"]
                if _severity_rank(sev) >= floor_rank:
                    findings.append(f"{pkg} ({sev})")
        else:
            return [], "npm audit JSON missing 'vulnerabilities'"
    elif ecosystem == "python":
        # pip-audit -f json: {"dependencies": [{"name":..,"vulns":[{...}]}]}
        deps = data.get("dependencies")
        items = deps if isinstance(deps, list) else data if isinstance(data, list) else []
        for dep in items:
            if not isinstance(dep, dict):
                continue
            name = dep.get("name", "?")
            vlist = dep.get("vulns") or []
            for v in vlist if isinstance(vlist, list) else []:
                if not isinstance(v, dict):
                    continue
                sev = "unknown"
                # pip-audit may carry severity under 'fix_versions'/'aliases';
                # severity is frequently absent — unknown sorts floor-meeting.
                for key in ("severity", "Severity"):
                    if isinstance(v.get(key), str):
                        sev = v[key]
                        break
                if _severity_rank(sev) >= floor_rank:
                    vid = v.get("id", "vuln")
                    findings.append(f"{name}:{vid} ({sev})")
    else:
        return [], f"unsupported ecosystem {ecosystem!r}"
    return sorted(set(findings)), None


def run_ecosystem_audit(
    project_dir: Path,
    ecosystem: str,
    *,
    severity_floor: str = DEFAULT_SEVERITY_FLOOR,
    runner: Runner | None = None,
) -> AuditResult:
    """Run the dependency audit for *ecosystem* in *project_dir*.

    *runner* is the injection seam: it returns an ``AuditRun`` (the raw
    tool result). The default shells out to the real ``npm audit`` /
    ``pip-audit``. The returned ``AuditResult`` carries the findings at or
    above *severity_floor*, or marks ``tool_available=False`` /
    ``parse_error`` so the gate can SURFACE an audit that did not run."""
    run = (runner or _default_runner)(ecosystem, project_dir)
    if not run.available:
        return AuditResult(
            ecosystem=ecosystem,
            tool_available=False,
            floor=severity_floor,
            parse_error=run.error,
        )
    floor_rank = _severity_rank(severity_floor)
    findings, parse_error = _parse_findings(ecosystem, run.raw, floor_rank)
    return AuditResult(
        ecosystem=ecosystem,
        tool_available=True,
        floor=severity_floor,
        findings_at_or_above_floor=tuple(findings),
        parse_error=parse_error,
    )
