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

"""pOS v2 Self-Correction Loop.

Public surface:

    CauseDiagnosed              — Pydantic record (part 3 of four)
    CompletionPrecheck          — deterministic four-part enforcement
    CorrectionChannel           — subclassed one-on-one channel
    CorrectionConfig            — YAML-loaded knobs
    CorrectionEpisode           — sidecar episode record
    CorrectionNotification      — Tier-1 escalation payload
    CorrectionNotifier          — one-on-one dispatcher
    CorrectionStore             — SQLite persistence
    CorrectionTrigger           — normalised trigger across four sources
    EpisodeState                — running | completed | escalated | refused
    FailureClassIdentified      — Pydantic record (part 1 of four)
    IrreversibleCorrectionSpecError — spec-builder refusal at authoring
    InstanceFixed               — Pydantic record (part 2 of four)
    OTelAnomalyPoller           — aggregator poller (ruling #2)
    REQUIRED_RECORD_TYPES       — frozenset of the four record types
    RecordType                  — failure_class | instance_fix | cause_diagnosed | structural_remedy
    ScopeFailurePyeeSubscriber  — wired to ScopeRuntime.emitter.on('*')
    SelfCorrectionController    — composed runtime
    StructuralRemedyApplied     — Pydantic record (part 4 of four)
    TriggerSource               — scope_failure | otel_anomaly | review_verdict | user_reported
    build_correction_spec       — deterministic spec builder (ruling #3)
    build_trigger_from_review_verdict — ruling #1 shape
    build_trigger_from_user_report    — ruling #4 shape
    default_config              — built-in defaults
    load_config                 — YAML loader
    register_self_correction_ipc — bootstrap wiring (no activate_scope wrap)

Error codes (IPC, reserved range -32070..-32079):
    -32070 CORRECTION_INCOMPLETE_RECORDS
"""

from __future__ import annotations

from .completion_check import CompletionPrecheck
from .config import CorrectionConfig, default_config, load_config
from .controller import (
    CorrectionOpenResult,
    SelfCorrectionController,
)
from .ipc import register_self_correction_ipc
from .notification import (
    CorrectionChannel,
    CorrectionNotification,
    CorrectionNotifier,
    render_cascade_depth_text,
    render_cascade_same_class_text,
    render_cost_refusal_text,
)
from .spec import (
    IPC_CORRECTION_INCOMPLETE_RECORDS,
    REQUIRED_RECORD_TYPES,
    CauseDiagnosed,
    CorrectionCascadeEscalated,
    CorrectionEpisode,
    CorrectionTrigger,
    EpisodeState,
    FailureClassIdentified,
    InstanceFixed,
    RecordType,
    StructuralRemedyApplied,
    TriggerSource,
)
from .spec_builder import IrreversibleCorrectionSpecError, build_correction_spec
from .store import CorrectionStore
from .triggers import (
    GATE_REFUSAL_REASON_PATTERN,
    OTelAnomalyPoller,
    ScopeFailurePyeeSubscriber,
    build_trigger_from_review_verdict,
    build_trigger_from_span,
    build_trigger_from_state_transitioned,
    build_trigger_from_user_report,
)

# --- non-tech-user self-recovery (the protection floor's safety net) ---
# Four composable parts on four sealed primitives (plan
# docs/plans/non-tech-user-self-recovery.md). Detection feeds the EXISTING
# correction engine above; the safe-reset delegates the migration-safety
# envelope. These are NEW surfaces on the existing component, not a new
# engine.
from .recovery_surface import (
    RecoveryMessage,
    RecoverySituation,
    RecoverySurfaceLeak,
    contains_internal_vocabulary,
    find_internal_vocabulary,
    render_recovery,
)
from .safe_reset import (
    ResetNotConfirmed,
    SafeFbmReset,
    SafeResetResult,
    is_reset_confirmed,
    reset_would_fail_closed,
)
from .self_diagnosis import (
    ActionsVsClaimsFinding,
    ClaimCheck,
    CommsPathFinding,
    SelfDiagnosis,
    check_actions_vs_claims,
    check_comms_path,
    open_user_reported_correction,
    run_self_diagnosis,
)
from .watchdog import (
    ChannelVerdict,
    StallWatchdog,
    StuckVerdict,
    availability_probe_to_channel_probe,
    check_channel_and_self_heal,
    evaluate_stall,
)


__all__ = [
    "CauseDiagnosed",
    "CompletionPrecheck",
    "CorrectionCascadeEscalated",
    "CorrectionChannel",
    "CorrectionConfig",
    "CorrectionEpisode",
    "CorrectionNotification",
    "CorrectionNotifier",
    "CorrectionOpenResult",
    "CorrectionStore",
    "CorrectionTrigger",
    "EpisodeState",
    "FailureClassIdentified",
    "GATE_REFUSAL_REASON_PATTERN",
    "IPC_CORRECTION_INCOMPLETE_RECORDS",
    "InstanceFixed",
    "IrreversibleCorrectionSpecError",
    "OTelAnomalyPoller",
    "REQUIRED_RECORD_TYPES",
    "RecordType",
    "ScopeFailurePyeeSubscriber",
    "SelfCorrectionController",
    "StructuralRemedyApplied",
    "TriggerSource",
    "build_correction_spec",
    "build_trigger_from_review_verdict",
    "build_trigger_from_span",
    "build_trigger_from_state_transitioned",
    "build_trigger_from_user_report",
    "default_config",
    "load_config",
    "register_self_correction_ipc",
    "render_cascade_depth_text",
    "render_cascade_same_class_text",
    "render_cost_refusal_text",
    # --- non-tech-user self-recovery ---
    "ActionsVsClaimsFinding",
    "ChannelVerdict",
    "ClaimCheck",
    "CommsPathFinding",
    "RecoveryMessage",
    "RecoverySituation",
    "RecoverySurfaceLeak",
    "ResetNotConfirmed",
    "SafeFbmReset",
    "SafeResetResult",
    "SelfDiagnosis",
    "StallWatchdog",
    "StuckVerdict",
    "availability_probe_to_channel_probe",
    "check_actions_vs_claims",
    "check_channel_and_self_heal",
    "check_comms_path",
    "contains_internal_vocabulary",
    "evaluate_stall",
    "find_internal_vocabulary",
    "is_reset_confirmed",
    "open_user_reported_correction",
    "render_recovery",
    "reset_would_fail_closed",
    "run_self_diagnosis",
]
