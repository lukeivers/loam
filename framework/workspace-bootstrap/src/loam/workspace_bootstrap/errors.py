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

"""Bootstrap error codes — reserved range -32080..-32089.

No overlap with safety (-32040s), reversibility (-32050s), cost (-32060s),
or self-correction (-32070s). See proposal §3.4.

Every error carries a structured `data` payload when raised via an
ApplicationError on the IPC boundary (bootstrap itself generally raises
these as Python exceptions because boot happens before IPC is up;
callers that care about the code inspect `e.code`).
"""

from __future__ import annotations


# Proposal §3.4 assignments.
IPC_BOOTSTRAP_MISSING_CONFIG: int = -32080
IPC_BOOTSTRAP_CONTRIBUTION_NOT_FOUND: int = -32081
IPC_BOOTSTRAP_METADATA_INVALID: int = -32082
IPC_BOOTSTRAP_NAME_COLLISION: int = -32083
IPC_BOOTSTRAP_ORDERING_CYCLE: int = -32084
IPC_BOOTSTRAP_UNKNOWN_REFERENCE: int = -32085
IPC_BOOTSTRAP_ADAPTER_RAISED: int = -32086
# -32087..-32089 reserved for future expansion.


class BootstrapError(Exception):
    """Base class for bootstrap errors. Carries a JSON-RPC-style code
    so callers can surface the same taxonomy across exception raise and
    IPC reply paths."""

    code: int = -32080

    def __init__(self, message: str, *, data: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.data = data or {}


class MissingConfigError(BootstrapError):
    code = IPC_BOOTSTRAP_MISSING_CONFIG


class ContributionNotFoundError(BootstrapError):
    code = IPC_BOOTSTRAP_CONTRIBUTION_NOT_FOUND


class MetadataInvalidError(BootstrapError):
    code = IPC_BOOTSTRAP_METADATA_INVALID


class NameCollisionError(BootstrapError):
    code = IPC_BOOTSTRAP_NAME_COLLISION


class OrderingCycleError(BootstrapError):
    code = IPC_BOOTSTRAP_ORDERING_CYCLE


class UnknownReferenceError(BootstrapError):
    code = IPC_BOOTSTRAP_UNKNOWN_REFERENCE


class AdapterRaisedError(BootstrapError):
    code = IPC_BOOTSTRAP_ADAPTER_RAISED
