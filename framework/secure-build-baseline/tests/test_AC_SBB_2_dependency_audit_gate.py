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

A build of a supported-ecosystem artifact runs the ecosystem audit and, on
a known vuln at or above a configured severity floor, blocks-or-surfaces;
a clean audit passes silently; an unavailable audit tool is surfaced
honestly (never faked clean — Lens 0). The audit is composed on the
ecosystem's OWN tool via an injectable runner (Lens 1)."""

from __future__ import annotations

import json
from pathlib import Path

from loam.secure_build_baseline.dependency_audit import (
    AuditRun,
    detect_ecosystems,
    run_ecosystem_audit,
)


def _npm_json(severity_counts: dict[str, int]) -> str:
    vulns = {}
    for sev, n in severity_counts.items():
        for i in range(n):
            vulns[f"pkg-{sev}-{i}"] = {"severity": sev}
    return json.dumps({"vulnerabilities": vulns})


def _runner_for(raw: str):
    def _run(ecosystem: str, project_dir: Path) -> AuditRun:
        return AuditRun(available=True, raw=raw)

    return _run


def test_detect_ecosystems_node_and_python(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("flask\n", encoding="utf-8")
    assert detect_ecosystems(tmp_path) == ["node", "python"]


def test_detect_ecosystems_none(tmp_path: Path) -> None:
    assert detect_ecosystems(tmp_path) == []


def test_high_vuln_at_floor_blocks(tmp_path: Path) -> None:
    """A high-severity vuln with a high floor is reported as a finding (the
    gate will block-or-surface on it)."""
    raw = _npm_json({"high": 1, "low": 3})
    result = run_ecosystem_audit(
        tmp_path, "node", severity_floor="high", runner=_runner_for(raw)
    )
    assert result.tool_available
    assert not result.is_clean
    assert len(result.findings_at_or_above_floor) == 1
    assert "high" in result.findings_at_or_above_floor[0]


def test_below_floor_passes_silently(tmp_path: Path) -> None:
    """Vulns strictly below the floor do not produce findings — a clean
    pass at that floor."""
    raw = _npm_json({"low": 5, "moderate": 2})
    result = run_ecosystem_audit(
        tmp_path, "node", severity_floor="high", runner=_runner_for(raw)
    )
    assert result.tool_available
    assert result.is_clean
    assert result.findings_at_or_above_floor == ()


def test_severity_floor_is_configurable(tmp_path: Path) -> None:
    """Lowering the floor to moderate catches the moderate vulns the high
    floor passed."""
    raw = _npm_json({"moderate": 2})
    high = run_ecosystem_audit(
        tmp_path, "node", severity_floor="high", runner=_runner_for(raw)
    )
    moderate = run_ecosystem_audit(
        tmp_path, "node", severity_floor="moderate", runner=_runner_for(raw)
    )
    assert high.is_clean
    assert not moderate.is_clean
    assert len(moderate.findings_at_or_above_floor) == 2


def test_clean_audit_is_clean(tmp_path: Path) -> None:
    raw = json.dumps({"vulnerabilities": {}})
    result = run_ecosystem_audit(
        tmp_path, "node", severity_floor="high", runner=_runner_for(raw)
    )
    assert result.is_clean


def test_unavailable_tool_surfaces_never_faked_clean(tmp_path: Path) -> None:
    """When the audit tool is unavailable the result is NOT reported clean —
    it is marked must-surface so the gate names the unverified state (Lens 0
    honesty: never claim a guarantee that did not run)."""
    def _absent(ecosystem: str, project_dir: Path) -> AuditRun:
        return AuditRun(available=False, error="npm not found on PATH")

    result = run_ecosystem_audit(
        tmp_path, "node", severity_floor="high", runner=_absent
    )
    assert not result.tool_available
    assert result.must_surface_unavailable
    assert not result.is_clean  # an un-run audit is NOT clean


def test_unparseable_audit_output_surfaces(tmp_path: Path) -> None:
    """A tool that ran but returned unparseable output surfaces a parse
    error rather than silently passing."""
    result = run_ecosystem_audit(
        tmp_path, "node", severity_floor="high",
        runner=_runner_for("this is ::: not json"),
    )
    assert result.tool_available
    assert result.parse_error is not None
    assert result.must_surface_unavailable
    assert not result.is_clean


def test_python_pip_audit_parsing(tmp_path: Path) -> None:
    """pip-audit-shaped JSON parses; a vuln with explicit high severity is a
    finding at the high floor."""
    raw = json.dumps(
        {
            "dependencies": [
                {
                    "name": "requests",
                    "vulns": [{"id": "PYSEC-2024-1", "severity": "high"}],
                },
                {"name": "flask", "vulns": []},
            ]
        }
    )
    result = run_ecosystem_audit(
        tmp_path, "python", severity_floor="high", runner=_runner_for(raw)
    )
    assert result.tool_available
    assert not result.is_clean
    assert any("requests" in f for f in result.findings_at_or_above_floor)
