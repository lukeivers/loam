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
