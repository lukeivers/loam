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
    "AuthorityBoundary",
    "AuthoringOutcome",
    "AuthoringPipeline",
    "AuthoringResult",
    "AwarenessBlock",
    "AwarenessCategory",
    "BackgroundWorkMonitor",
    "CompactionSurvivor",
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
    "Responsibilities",
    "RetirementReason",
    "SURVIVAL_LIST",
    "SelfReviewVerdict",
    "SeverityVocabulary",
    "TierAction",
    "TriggerSignal",
    "load_contract",
    "retire_persona",
]
