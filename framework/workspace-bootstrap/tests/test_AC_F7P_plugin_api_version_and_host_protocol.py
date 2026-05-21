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

"""F7-PLUGIN-VERSION — plugin-contract `api_version` field + `BootstrapHostProtocol`.

ACs:
  - AC.F7P.1: `ContributionMetadata.api_version: int` exists, defaults to 1.
  - AC.F7P.2: bootstrap raises `MetadataInvalidError` with a clear message
    naming expected vs received api_version when a contributor declares a
    mismatched value.
  - AC.F7P.3: `BootstrapHostProtocol` is a typing.Protocol; the concrete
    `BootstrapHost` instance structurally conforms.
  - AC.F7P.4 is satisfied by the presence of the three tests below
    (one per AC.F7P.{1,2,3}).
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Protocol, get_type_hints, runtime_checkable

import pytest

from loam.workspace_bootstrap import (
    BaseContribution,
    BootstrapHost,
    BootstrapHostProtocol,
    ContributionMetadata,
    MetadataInvalidError,
    Phase,
    SUPPORTED_API_VERSION,
)
from loam.workspace_bootstrap.discovery import read_metadata


# --- AC.F7P.1 — field presence + default ----------------------------------


def test_AC_F7P_1_api_version_field_defaults_to_one() -> None:
    """`ContributionMetadata.api_version: int` exists and defaults to 1.

    Backward-compat anchor: existing contributions that never set
    api_version still construct successfully via the default.
    """
    md = ContributionMetadata(name="x", phase=Phase.before_orchestrator_start)
    assert md.api_version == 1
    # Default matches the bootstrap-side constant — they must move together.
    assert SUPPORTED_API_VERSION == 1
    # Explicitly typed as int (Pydantic enforces this; check round-trip).
    md_explicit = ContributionMetadata(
        name="x", phase=Phase.before_orchestrator_start, api_version=1
    )
    assert md_explicit.api_version == 1


def test_AC_F7P_1_api_version_rejects_zero_and_negative() -> None:
    """api_version is constrained `ge=1`; non-positive values fail validation."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ContributionMetadata(
            name="x", phase=Phase.before_orchestrator_start, api_version=0
        )
    with pytest.raises(ValidationError):
        ContributionMetadata(
            name="x", phase=Phase.before_orchestrator_start, api_version=-1
        )


# --- AC.F7P.2 — rejection with clear message ------------------------------


class _FutureVersionContribution(BaseContribution):
    """Stand-in contribution declaring an api_version newer than supported."""

    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="future_version_test",
        phase=Phase.before_orchestrator_start,
        api_version=999,
    )

    def contribute(self, host: BootstrapHostProtocol) -> None:  # pragma: no cover
        return None


def test_AC_F7P_2_mismatched_api_version_raises_metadata_invalid() -> None:
    """read_metadata raises MetadataInvalidError when api_version != SUPPORTED.

    Error message must name expected and received versions.
    """
    with pytest.raises(MetadataInvalidError) as excinfo:
        read_metadata(_FutureVersionContribution, ref_label="future_version_test")

    msg = excinfo.value.message
    # Message must surface both versions so the plugin author can act.
    assert str(SUPPORTED_API_VERSION) in msg, (
        f"expected SUPPORTED_API_VERSION={SUPPORTED_API_VERSION} in error "
        f"message, got: {msg!r}"
    )
    assert "999" in msg, f"expected received api_version 999 in error: {msg!r}"
    # Structured data payload carries both versions for programmatic callers.
    assert excinfo.value.data["expected_api_version"] == SUPPORTED_API_VERSION
    assert excinfo.value.data["received_api_version"] == 999


def test_AC_F7P_2_default_api_version_one_accepted_by_read_metadata() -> None:
    """Contributions with the default api_version=1 load successfully.

    Backward-compat: contributions written before F7P (no api_version
    keyword in their ContributionMetadata literal) still resolve.
    """

    class _LegacyContribution(BaseContribution):
        metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
            name="legacy_test",
            phase=Phase.before_orchestrator_start,
            # No api_version — defaults to 1 → matches SUPPORTED_API_VERSION.
        )

        def contribute(self, host: BootstrapHostProtocol) -> None:  # pragma: no cover
            return None

    md = read_metadata(_LegacyContribution, ref_label="legacy_test")
    assert md.api_version == 1
    assert md.name == "legacy_test"


# --- AC.F7P.3 — BootstrapHostProtocol typing the host surface --------------


def test_AC_F7P_3_bootstrap_host_protocol_is_a_typing_protocol() -> None:
    """`BootstrapHostProtocol` is a typing.Protocol class."""
    # Protocol-ness: subclasses of typing.Protocol have _is_protocol True.
    assert getattr(BootstrapHostProtocol, "_is_protocol", False) is True
    # Sanity: it is a class.
    assert isinstance(BootstrapHostProtocol, type)


def test_AC_F7P_3_concrete_bootstrap_host_structurally_conforms(
    tmp_path: Path,
) -> None:
    """A real `BootstrapHost` instance satisfies `BootstrapHostProtocol`.

    Structural subtyping verification via runtime_checkable isinstance.
    """
    host = BootstrapHost(
        config_dir=tmp_path / "config",
        workspace_root=tmp_path,
        manifest_path=tmp_path / "bootstrap.yaml",
    )
    # runtime_checkable Protocol — isinstance is the structural check.
    assert isinstance(host, BootstrapHostProtocol)


def test_AC_F7P_3_protocol_types_documented_attribute_surface() -> None:
    """The Protocol exposes the documented attribute names.

    Sanity-anchor: if the host gains/loses attributes contributions rely
    on, this test points at the Protocol-update obligation.
    """
    hints = get_type_hints(BootstrapHostProtocol)
    # Group 1 — framework-owned singletons.
    for attr in (
        "config_dir",
        "workspace_root",
        "manifest_path",
        "tracer",
        "channel_registry",
    ):
        assert attr in hints, f"BootstrapHostProtocol missing attribute {attr!r}"
    # Group 2 — orchestrator-linked.
    for attr in (
        "orchestrator",
        "ipc_server",
        "scope_runtime",
        "objective_tracker",
        "monitor",
        "dormancy",
    ):
        assert attr in hints, f"BootstrapHostProtocol missing attribute {attr!r}"
    # Group 3 — per-adapter outputs.
    for attr in (
        "observability_provider",
        "loaded_persona",
        "reversibility_controller",
        "safety_controller",
        "cost_controller",
        "self_correction_controller",
        "memory_sidecar_url",
    ):
        assert attr in hints, f"BootstrapHostProtocol missing attribute {attr!r}"
