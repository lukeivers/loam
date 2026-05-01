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

"""Session-resilient orchestrator for pOS v2.

Public surface:

    from loam.orchestrator import Orchestrator, OrchestratorConfig
    from loam.orchestrator.errors import (
        BindRefused,
        ScopeNotPending,
        BootstrapMissing,
        BootstrapError,
    )

The orchestrator is a single long-lived Python asyncio process.
It is instantiated once per pOS installation and is started via
`await Orchestrator(config).run()`. It hosts:

  1. The local-state store (~/.loam/orchestrator.sqlite) for
     process-lifecycle events and compaction flags.
  2. A Unix-domain-socket JSON-RPC server for peer sessions.
  3. The primary-persona layer's BackgroundWorkMonitor coroutine.
  4. The `activate_scope` dispatch-layer enforcement of bind_scope.
  5. Pause/resume hooks for the (future, separate) graceful-
     degradation component.

pOS core ships zero personas here — this package is framework only.
A build-time assertion enforces this; see `core_purity.py`.
"""

from __future__ import annotations

from .config import OrchestratorConfig, load_config
from .errors import (
    BindRefused,
    BootstrapError,
    BootstrapMissing,
    OrchestratorError,
    ScopeNotPending,
)
from .orchestrator import Orchestrator

__all__ = [
    "BindRefused",
    "BootstrapError",
    "BootstrapMissing",
    "Orchestrator",
    "OrchestratorConfig",
    "OrchestratorError",
    "ScopeNotPending",
    "load_config",
]
