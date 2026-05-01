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

"""Shared fixtures for the primary-persona test suite."""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

import pytest

# Make `src` importable as `src.*` and `primary_persona.*`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Make test-local helpers importable (e.g. ``_helpers_d7``). Non-test
# helper modules live alongside tests but pytest doesn't add the tests/
# directory to sys.path automatically.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Install an in-memory OTel exporter at the process level BEFORE any
# tracer is created. Once a tracer is obtained, the provider cannot be
# swapped — so this must be the first thing the test session does.
from opentelemetry import trace  # noqa: E402
from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (  # noqa: E402
    InMemorySpanExporter,
)

_IN_MEMORY_EXPORTER = InMemorySpanExporter()
_PROVIDER = TracerProvider()
_PROVIDER.add_span_processor(SimpleSpanProcessor(_IN_MEMORY_EXPORTER))
trace.set_tracer_provider(_PROVIDER)


@pytest.fixture
def span_exporter_clean():
    """Clear the in-memory exporter before each test and return it."""
    _IN_MEMORY_EXPORTER.clear()
    return _IN_MEMORY_EXPORTER


from loam.primary_persona import contract as _contract  # noqa: E402
from loam.primary_persona import loader as _loader  # noqa: E402


VALID_CONTRACT_YAML = dedent(
    """\
    handle: eve
    given_name: Eve
    contract_version: 1.0.0
    responsibilities:
      single_point_of_contact: Sole coordinator for personal-life operations.
      context_holder: Carries ongoing context across sessions.
      escalation_judge: Decides when to surface matters to Luke.
    authority_boundary:
      tier_a: defer
      tier_b: defer
      tier_c: execute
      tier_d: execute
    escalation_taxonomy:
      categories:
        - external-funds-commitment
        - strategy-pivot
    severity_vocabulary:
      labels:
        - crisis
        - urgent
        - material
        - advisory
    delegates_to:
      - financial-advisor
    home_persona_for:
      - personal
    voice_markers:
      - "Lead with the answer."
    is_primary: true
    pending_introduction: false
    is_addressable: true
    """
)


def write_persona_dir(
    personas_dir: Path,
    handle: str,
    *,
    yaml_override: str | None = None,
    prompt: str = "# persona prompt\n\nPlain prose.\n",
    voice: str | None = None,
) -> Path:
    persona_dir = personas_dir / handle
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        yaml_override
        if yaml_override is not None
        else VALID_CONTRACT_YAML.replace("handle: eve", f"handle: {handle}")
    )
    (persona_dir / "prompt.md").write_text(prompt)
    if voice:
        (persona_dir / "voice.md").write_text(voice)
    return persona_dir


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A scratch workspace directory with `workspace/personas/` ready.

    D-migration D.2 (amendment #63): personas live under
    ``<workspace>/workspace/personas/`` post-D.2.
    """
    personas = tmp_path / "workspace" / "personas"
    personas.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def workspace_with_primary(workspace: Path) -> Path:
    """Workspace containing exactly one primary persona, `eve`."""
    write_persona_dir(workspace / "workspace" / "personas", "eve")
    return workspace


@pytest.fixture
def loader_no_core_check(workspace: Path) -> _loader.PersonaLoader:
    """PersonaLoader with the core-check disabled (used by most tests
    that don't exercise the check itself)."""
    return _loader.PersonaLoader(workspace, enforce_no_personas_in_core=False)
