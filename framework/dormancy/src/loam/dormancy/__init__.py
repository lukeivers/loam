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

"""Dormancy policy layer for loam.

Public surface (exports here are stable):

    ClaudeClient          — adapter wrapping Claude API calls; passive detection
    DegradationSignal     — enum of observed failure classes
    DegradationMode       — the six tracked failure modes
    FSMState              — closed / open / half_open / gated
    Policy                — P1 / P2 / P3 / P4
    DegradationConfig     — pydantic model (YAML-backed)
    DegradationComponent  — the composed runtime that the orchestrator wires
    NotificationTier      — 1 (audible) or 2 (silent) per decision
    DegradationChannel    — subclass of primary_persona.OneOnOneChannel reusing invariant

See docs/architecture.md for the full design.
"""

from __future__ import annotations

from .adapter import ClaudeClient, ProbeResult, LLMResult, ClaudeCallable
from .config import DegradationConfig, load_config
from .errors import (
    DegradationSignal,
    ClaudeAPIError,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    OverloadedError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    GarbageResponseError,
    classify_exception,
)
from .fsm import FSMState, DegradationMode, ModeFSM
from .policy import Policy, PolicyDispatcher
from .notification import (
    DegradationChannel,
    DegradationNotifier,
    NotificationTier,
    DegradationNotification,
)
from .component import DegradationComponent

__all__ = [
    "ClaudeClient",
    "ClaudeCallable",
    "ProbeResult",
    "LLMResult",
    "DegradationSignal",
    "ClaudeAPIError",
    "APIConnectionError",
    "APITimeoutError",
    "RateLimitError",
    "OverloadedError",
    "AuthenticationError",
    "BadRequestError",
    "InternalServerError",
    "GarbageResponseError",
    "classify_exception",
    "FSMState",
    "DegradationMode",
    "ModeFSM",
    "Policy",
    "PolicyDispatcher",
    "DegradationChannel",
    "DegradationNotifier",
    "NotificationTier",
    "DegradationNotification",
    "DegradationConfig",
    "load_config",
    "DegradationComponent",
]
