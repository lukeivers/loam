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

"""AC-CAIRN-REG-1 (C1) — the project registry resolves loam + cairn to
distinct repo roots + derivations; an unregistered name returns a clean
"not registered" result (``None``), not a crash.

This proves the registry is a real generalization seam: a project name
resolves to ITS repo root + ITS ground-truth derivation, and an unknown
name is handled gracefully rather than blowing up.
"""

from __future__ import annotations

from loam_cli.audit.registry import (
    PROJECT_REGISTRY,
    ProjectStateSpec,
    derive_project_state,
    registered_project_names,
    resolve_project,
)


def test_registry_resolves_loam_and_cairn_to_distinct_specs() -> None:
    loam = resolve_project("loam")
    cairn = resolve_project("cairn")

    assert isinstance(loam, ProjectStateSpec)
    assert isinstance(cairn, ProjectStateSpec)
    assert loam.name == "loam"
    assert cairn.name == "cairn"

    # Distinct repo roots — each project points at its OWN repo.
    assert loam.repo_root != cairn.repo_root
    assert "cairn" in str(cairn.repo_root)

    # Distinct derivations — loam's seal-sidecar derivation is NOT
    # cairn's marker derivation.
    assert loam.derive is not cairn.derive


def test_resolution_is_case_insensitive_and_stripped() -> None:
    assert resolve_project("  Cairn  ") is not None
    assert resolve_project("LOAM") is not None


def test_unregistered_name_returns_none_not_crash() -> None:
    # A clean "not registered" result — never an exception.
    assert resolve_project("not-a-real-project") is None
    assert derive_project_state("not-a-real-project") is None


def test_registered_names_lists_both_projects() -> None:
    names = registered_project_names()
    assert "loam" in names
    assert "cairn" in names


def test_registry_is_a_real_mapping() -> None:
    assert set(PROJECT_REGISTRY.keys()) >= {"loam", "cairn"}
