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

"""pOS v2 Workspace Bootstrap — framework + foundational-adapter bundle.

Public surface:

    BaseContribution           — convenience base class for adapters
    BootstrapHost              — shared singletons + per-adapter outputs
    Bootstrapper               — top-level composition engine
    Contribution               — structural protocol
    ContributionMetadata       — Pydantic metadata record (frozen)
    Manifest                   — loaded `bootstrap.yaml`
    Phase                      — three-value enum
    PHASE_ORDER                — deterministic phase order
    load_manifest              — parse `bootstrap.yaml`
    topological_order          — ordering-engine entry point

Extension protocol: Phase 4+ components ship a `Contribution` subclass
in their own package, register it under the `loam.bootstrap.contributions`
entry-point group, and add one manifest line to enable it. **Bootstrap's
code does not change.** See `docs/extension_protocol.md`.

Error codes (reserved range -32080..-32089):
    -32080 BOOTSTRAP_MISSING_CONFIG
    -32081 BOOTSTRAP_CONTRIBUTION_NOT_FOUND
    -32082 BOOTSTRAP_METADATA_INVALID
    -32083 BOOTSTRAP_NAME_COLLISION
    -32084 BOOTSTRAP_ORDERING_CYCLE
    -32085 BOOTSTRAP_UNKNOWN_REFERENCE
    -32086 BOOTSTRAP_ADAPTER_RAISED
"""

from __future__ import annotations

from .discovery import read_metadata, resolve_ref
from .errors import (
    IPC_BOOTSTRAP_ADAPTER_RAISED,
    IPC_BOOTSTRAP_CONTRIBUTION_NOT_FOUND,
    IPC_BOOTSTRAP_METADATA_INVALID,
    IPC_BOOTSTRAP_MISSING_CONFIG,
    IPC_BOOTSTRAP_NAME_COLLISION,
    IPC_BOOTSTRAP_ORDERING_CYCLE,
    IPC_BOOTSTRAP_UNKNOWN_REFERENCE,
    AdapterRaisedError,
    BootstrapError,
    ContributionNotFoundError,
    MetadataInvalidError,
    MissingConfigError,
    NameCollisionError,
    OrderingCycleError,
    UnknownReferenceError,
)
from .host import BootstrapHost, HostAttributeNotYetAvailable
from .main import Bootstrapper, ResolvedContribution, cli_main
from .manifest import (
    ContributionRef,
    Manifest,
    load_manifest,
    write_onboarding_fields,
)
from .onboarding import (
    OnboardingResult,
    QUESTION_SLUGS,
    SKIP_ENV_VAR,
    run_onboarding,
)
from .ordering import topological_order
from .spec import (
    PHASE_ORDER,
    BaseContribution,
    Contribution,
    ContributionMetadata,
    Phase,
)

__all__ = [
    "AdapterRaisedError",
    "BaseContribution",
    "BootstrapError",
    "BootstrapHost",
    "Bootstrapper",
    "Contribution",
    "ContributionMetadata",
    "ContributionNotFoundError",
    "ContributionRef",
    "HostAttributeNotYetAvailable",
    "IPC_BOOTSTRAP_ADAPTER_RAISED",
    "IPC_BOOTSTRAP_CONTRIBUTION_NOT_FOUND",
    "IPC_BOOTSTRAP_METADATA_INVALID",
    "IPC_BOOTSTRAP_MISSING_CONFIG",
    "IPC_BOOTSTRAP_NAME_COLLISION",
    "IPC_BOOTSTRAP_ORDERING_CYCLE",
    "IPC_BOOTSTRAP_UNKNOWN_REFERENCE",
    "Manifest",
    "MetadataInvalidError",
    "MissingConfigError",
    "NameCollisionError",
    "OnboardingResult",
    "OrderingCycleError",
    "PHASE_ORDER",
    "Phase",
    "QUESTION_SLUGS",
    "ResolvedContribution",
    "SKIP_ENV_VAR",
    "UnknownReferenceError",
    "cli_main",
    "load_manifest",
    "read_metadata",
    "resolve_ref",
    "run_onboarding",
    "topological_order",
    "write_onboarding_fields",
]
