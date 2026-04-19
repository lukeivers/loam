"""pOS v2 Safety Layer.

Public surface (stable exports):

    FrameworkFloorCategory  — enum of the seven framework-fixed ask categories
    AlwaysAskList           — Pydantic-validated ask-list schema
    AskDecisionState        — approved / refused / pending / expired
    DangerousOpGate         — stricter gate composed on top of the ask gate
    GateOutcome             — PASS / BLOCK
    SafetyConfig            — safety.yaml loader with tunable threshold
    SafetyStore             — SQLite persistence for ask decisions + kill events
    SafetyController        — composed runtime the workspace bootstrap wires
    KillEngine              — three-level kill dispatcher (scope/session/system)
    KillLevel               — scope / session / system
    SafetyNotifier          — dispatches asks + gate-fires via OneOnOneChannel
    SafetyChannel           — subclass of OneOnOneChannel (is_group inheritance)
    structural_hash         — deterministic hash of a ScopeSpec (approval binding)

Error codes (IPC):
    -32040 ask_gate_pending
    -32041 dangerous_op_gate_blocked
    -32042 system_kill_active
    -32043 safety_gate_channel_unavailable

See docs/architecture.md for the full design and
context/pos-rebuild/components/safety-layer/ for the governing documents.
"""

from __future__ import annotations

from .action_class import FrameworkFloorCategory
from .ask_list import (
    AlwaysAskList,
    AskDecisionState,
    AskListEntry,
    DEFAULT_FRAMEWORK_FLOOR,
    DEFAULT_DANGEROUS_OP_SUBSET,
    parse_duration_spec,
)
from .config import SafetyConfig, MONEY_THRESHOLD_FLOOR_CENTS, DEFAULT_MONEY_THRESHOLD_CENTS
from .controller import SafetyController, GateOutcome, GateRefusal
from .dangerous_op import DangerousOpGate
from .events import (
    AskDecisionRecord,
    KillEventRecord,
    KillLevel,
    SystemKillStateRecord,
    structural_hash,
)
from .kill import KillEngine
from .notification import SafetyChannel, SafetyNotification, SafetyNotifier
from .store import SafetyStore

__all__ = [
    "AlwaysAskList",
    "AskDecisionRecord",
    "AskDecisionState",
    "AskListEntry",
    "DEFAULT_DANGEROUS_OP_SUBSET",
    "DEFAULT_FRAMEWORK_FLOOR",
    "DEFAULT_MONEY_THRESHOLD_CENTS",
    "DangerousOpGate",
    "FrameworkFloorCategory",
    "GateOutcome",
    "GateRefusal",
    "KillEngine",
    "KillEventRecord",
    "KillLevel",
    "MONEY_THRESHOLD_FLOOR_CENTS",
    "SafetyChannel",
    "SafetyConfig",
    "SafetyController",
    "SafetyNotification",
    "SafetyNotifier",
    "SafetyStore",
    "SystemKillStateRecord",
    "parse_duration_spec",
    "structural_hash",
]
