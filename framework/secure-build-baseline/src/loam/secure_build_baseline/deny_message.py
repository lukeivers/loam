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

"""Plain-words deny / surface reasons for the secure-build baseline.

Translation discipline (Lens 0 / translate-outbound): the reasons name the
ACTUAL consequence and the repair in the vocabulary a non-technical owner
knows — not ``is_production`` / ``CVE`` / internal flag names."""

from __future__ import annotations


def artifact_cleanliness_reason(offending: list[str], *, blocking: bool) -> str:
    paths = ", ".join(f"`{p}`" for p in offending) or "(none)"
    verb = "blocked" if blocking else "flagged"
    return (
        f"AC.SBB.3 (artifact-cleanliness, secure-build baseline) — {verb}: "
        f"this broad ``git add``/``commit -a`` would sweep harness working "
        f"state or a secret into the project you are building: {paths}. "
        f"These are runtime scratch / memory / database / credential files "
        f"that should never live in the shipped artifact. Repair: add them "
        f"to the project's `.gitignore` (the secure-build baseline provides "
        f"the floor `.gitignore` content) and stage only the source you "
        f"intend to ship. Strictness for this guarantee is tunable "
        f"(block | surface) via `<workspace>/.loam/secure-build.yaml`; it "
        f"defaults to block."
    )


def dependency_audit_reason(
    ecosystem: str, findings: list[str], floor: str, *, blocking: bool
) -> str:
    listed = ", ".join(f"`{f}`" for f in findings) or "(none)"
    verb = "blocked" if blocking else "flagged"
    return (
        f"AC.SBB.2 (dependency-hygiene, secure-build baseline) — {verb}: the "
        f"{ecosystem} dependencies of the project you are building carry "
        f"known security problems at or above the `{floor}` severity floor: "
        f"{listed}. The build floor runs the ecosystem's own audit "
        f"(`npm audit` / `pip-audit`) and stops a build that would ship a "
        f"known-vulnerable dependency. Repair: update or replace the flagged "
        f"package(s), then rebuild. Strictness for this guarantee is tunable "
        f"(block | surface) via `<workspace>/.loam/secure-build.yaml`; it "
        f"defaults to block."
    )


def dependency_audit_unavailable_reason(ecosystem: str, detail: str | None) -> str:
    why = f" ({detail})" if detail else ""
    return (
        f"AC.SBB.2 (dependency-hygiene, secure-build baseline) — could NOT "
        f"verify {ecosystem} dependency safety{why}. The ecosystem audit "
        f"tool did not run, so the build floor cannot confirm the "
        f"dependencies are free of known vulnerabilities. This is surfaced "
        f"honestly rather than reported as clean: install the audit tool "
        f"(`npm` / `pip-audit`) to arm this guarantee for this ecosystem."
    )
