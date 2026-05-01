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

"""Primary-persona layer for pOS v2.

This package implements three tightly-coupled halves that share a
persona contract:

  1. Loader + validator — reads a workspace-supplied persona directory,
     validates against the Pydantic contract, fails closed on invalidity.
  2. Background-work monitor — long-lived asyncio coroutine subscribing
     to scope-of-work's pyee emitter, producing a structured awareness
     block injected on every UserPromptSubmit.
  3. Autonomous-authoring framework — creation-trigger detector plus a
     four-step Claude-via-Max pipeline that produces a new persona
     directory with a mandatory user-introduction gate.

pOS core ships zero persona content. The authoring framework, contract,
template, and quality checks live here; `contract.yaml` / `prompt.md`
files never appear under pOS-core paths. A build-time check in
`loader.py` enforces this.

Permitted runtime dependencies: stdlib, pydantic, pyee, opentelemetry-*,
PyYAML. Anything else requires halt-and-signal per STATE.md rule 8.
"""

from .contract import (
    AuthorityBoundary,
    EscalationTaxonomy,
    PersonaContract,
    PersonaState,
    PersonaTier,
    Responsibilities,
    SeverityVocabulary,
    TierAction,
    load_contract,
)
from .loader import (
    LoadedPersona,
    PersonaDirectoryNotFoundError,
    PersonaInCoreError,
    PersonaLoader,
    PersonaValidationError,
)
from .monitor import AwarenessBlock, BackgroundWorkMonitor, AwarenessCategory
from .compaction import CompactionSurvivor, SURVIVAL_LIST
from .context_composer import (
    ADDITIONAL_CONTEXT_CAP,
    AdditionalContextCapExceededError,
    ComposedContextPayload,
    ContributorRegistrationError,
    CorpusGateState,
    RegisteredContributor,
    SessionPayload,
    SessionPayloadMissingError,
    TriggerKind,
    TurnPayload,
)
from .session_start_gate import compose_session_fields
from .session_start_emitter import (
    build_persona_session_start_inner_hook,
    build_persona_stop_inner_hook,
    build_persona_user_prompt_submit_inner_hook,
    build_session_composer,
    cli_session_start,
    cli_user_prompt_submit,
    emit_session_start_context,
    emit_user_prompt_submit_context,
)
from .stop_emitter import (
    StopEnvelope,
    TurnContent,
    cli_memory_write,
    cli_stop,
    derive_turn_id,
    handle_stop_envelope,
    parse_stop_envelope,
)
# M-FBM (2026-05-01): MCP-backed memory client retired from runtime
# path per AC.MFBM.5. The ``mcp_memory_client`` module stays on disk
# (not removed) so M-GMP can relocate it to the graphiti plugin
# without history loss. Re-exports retired from the package surface
# so importers cannot accidentally bind against the MCP path.
from .file_memory import (
    FileMemoryRetrievalConfig,
    FileMemoryStore,
    MemoryProvider,
    build_file_memory_retrieval_contributor,
    memory_dir_for_workspace,
    register_file_memory_retrieval,
)
from .dispatch_wrapper import (
    DispatchOutcome,
    DispatchRefusal,
    DispatchShape,
    NewACSpec,
    dispatch_with_scope,
    write_dispatcher_stub,
)
from .creation_triggers import CreationTrigger, CreationTriggerDetector, TriggerSignal
from .authoring import (
    AuthoringOutcome,
    AuthoringPipeline,
    AuthoringResult,
    LLMCallable,
    SelfReviewVerdict,
)
from .introduction import (
    IntroductionDispatcher,
    IntroductionOutcome,
    OneOnOneChannel,
)
from .retirement import retire_persona, RetirementReason

__all__ = [
    "ADDITIONAL_CONTEXT_CAP",
    "AdditionalContextCapExceededError",
    "AuthorityBoundary",
    "AuthoringOutcome",
    "AuthoringPipeline",
    "AuthoringResult",
    "AwarenessBlock",
    "AwarenessCategory",
    "BackgroundWorkMonitor",
    "CompactionSurvivor",
    "ComposedContextPayload",
    "ContributorRegistrationError",
    "CorpusGateState",
    "CreationTrigger",
    "CreationTriggerDetector",
    "EscalationTaxonomy",
    "IntroductionDispatcher",
    "IntroductionOutcome",
    "LLMCallable",
    "LoadedPersona",
    "OneOnOneChannel",
    "PersonaContract",
    "PersonaDirectoryNotFoundError",
    "PersonaInCoreError",
    "PersonaLoader",
    "PersonaState",
    "PersonaTier",
    "PersonaValidationError",
    "RegisteredContributor",
    "Responsibilities",
    "RetirementReason",
    "SURVIVAL_LIST",
    "SelfReviewVerdict",
    "SessionPayload",
    "SessionPayloadMissingError",
    "SeverityVocabulary",
    "TierAction",
    "TriggerKind",
    "TriggerSignal",
    "TurnPayload",
    "DispatchOutcome",
    "DispatchRefusal",
    "DispatchShape",
    "FileMemoryRetrievalConfig",
    "FileMemoryStore",
    "MemoryProvider",
    "NewACSpec",
    "StopEnvelope",
    "TurnContent",
    "build_file_memory_retrieval_contributor",
    "build_persona_session_start_inner_hook",
    "build_persona_stop_inner_hook",
    "build_persona_user_prompt_submit_inner_hook",
    "build_session_composer",
    "cli_memory_write",
    "cli_session_start",
    "cli_stop",
    "cli_user_prompt_submit",
    "compose_session_fields",
    "derive_turn_id",
    "dispatch_with_scope",
    "emit_session_start_context",
    "emit_user_prompt_submit_context",
    "handle_stop_envelope",
    "load_contract",
    "memory_dir_for_workspace",
    "parse_stop_envelope",
    "register_file_memory_retrieval",
    "retire_persona",
    "write_dispatcher_stub",
]
