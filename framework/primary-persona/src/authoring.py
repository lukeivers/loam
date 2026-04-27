"""Autonomous authoring pipeline (D6).

Four-step Claude-via-Max pipeline that produces a new persona
directory passing the D1 contract by construction:

    1. style_harvest    — read existing personas for voice consistency
    2. domain_research  — web / memory query on the target domain
    3. contract_synthesis — fill in the Pydantic schema + prompt.md
    4. self_review      — four dimensions, up to two retries

Up to two self-review iterations. On the third failure, the authoring
scope terminates with a failure record; the primary persona decides
whether to log and stop or retry with an adjusted scope.

The pipeline runs inside a scope-of-work with a declared budget so
runaway generation is impossible (spec/policy for the authoring
scope is the caller's responsibility — this module assumes the scope
exists and debits against it for each LLM call).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Sequence

from scope_of_work.runtime import ScopeRuntime  # type: ignore[import-not-found]
from scope_of_work.spec import BudgetAxis  # type: ignore[import-not-found]

from . import observability as obs
from .contract import (
    AuthorityBoundary,
    EscalationTaxonomy,
    PersonaContract,
    Responsibilities,
    SeverityVocabulary,
    TierAction,
)
from .creation_triggers import TriggerSignal
from .loader import LoadedPersona


# ---- LLM callable --------------------------------------------------


@dataclass(frozen=True)
class LLMResult:
    """Result of one LLM call.

    - `text` is the primary output the pipeline consumes.
    - `input_tokens` / `output_tokens` / `money_cents` flow into the
      scope-of-work ledger so budget is tracked.
    - `prompt_name` and `model` are attribution — surface in the
      per-prompt cost view (v1.1 R12).
    """

    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    money_cents: int = 0
    prompt_name: str | None = None
    model: str | None = None


# Every LLM call in the pipeline routes through a callable of this
# shape. Workspaces wire Claude-via-Max here; tests wire a fake.
LLMCallable = Callable[[str, str], Awaitable[LLMResult]]
# args: (prompt_name, prompt_text)


# ---- self-review types ---------------------------------------------


class SelfReviewDimension(str, Enum):
    voice_distinctiveness = "voice_distinctiveness"  # the "not-generic" test
    scope_fit = "scope_fit"
    redundancy = "redundancy"
    contract_correctness = "contract_correctness"


@dataclass(frozen=True)
class SelfReviewVerdict:
    passed: bool
    dimensions: dict[SelfReviewDimension, bool]
    issues: tuple[str, ...]
    iteration: int

    def issues_joined(self) -> str:
        return "; ".join(self.issues) if self.issues else ""


# ---- pipeline outcome ----------------------------------------------


class AuthoringOutcome(str, Enum):
    persisted = "persisted"
    rejected_after_retries = "rejected_after_retries"
    failed = "failed"


@dataclass(frozen=True)
class AuthoringResult:
    outcome: AuthoringOutcome
    handle: str | None
    persona_dir: Path | None
    iterations: int
    verdicts: tuple[SelfReviewVerdict, ...]
    reason: str | None = None


# ---- pipeline ------------------------------------------------------


@dataclass
class AuthoringPipeline:
    """The four-step pipeline (proposal §D6).

    Usage:
        pipeline = AuthoringPipeline(
            llm=my_llm_callable,
            runtime=scope_runtime,
            workspace_root=Path("/workspaces/personal"),
        )
        result = await pipeline.author(
            trigger_signal=TriggerSignal.request_decline,
            domain="cooking",
            existing_personas=loaded_personas,
            authoring_scope_id="scope-xyz",
        )

    The `authoring_scope_id` must already exist in the runtime; the
    caller is responsible for declaring its budget. The pipeline
    debits tokens/money against it for each LLM call.
    """

    llm: LLMCallable
    runtime: ScopeRuntime
    workspace_root: Path
    max_review_iterations: int = 2
    # Pipeline steps are small; each call is one prompt.
    model: str = "claude-haiku-4-5"  # attribution; actual routing is in `llm`

    async def author(
        self,
        *,
        trigger_signal: TriggerSignal,
        domain: str,
        existing_personas: Sequence[LoadedPersona],
        authoring_scope_id: str,
        proposed_handle: str | None = None,
    ) -> AuthoringResult:
        with obs.authoring_span(
            signal=trigger_signal.value,
            **{
                "pos.persona.authoring.domain": domain,
                "pos.persona.authoring.scope_id": authoring_scope_id,
            },
        ):
            try:
                style_context = await self._style_harvest(
                    existing_personas, authoring_scope_id
                )
                domain_notes = await self._domain_research(
                    domain, authoring_scope_id
                )
                verdicts: list[SelfReviewVerdict] = []
                last_contract: PersonaContract | None = None
                last_prompt: str | None = None

                iteration = 0
                feedback: str | None = None
                while iteration <= self.max_review_iterations:
                    iteration += 1
                    contract, prompt_text = await self._contract_synthesis(
                        trigger_signal=trigger_signal,
                        domain=domain,
                        existing_personas=existing_personas,
                        style_context=style_context,
                        domain_notes=domain_notes,
                        authoring_scope_id=authoring_scope_id,
                        proposed_handle=proposed_handle,
                        revision_feedback=feedback,
                    )
                    last_contract = contract
                    last_prompt = prompt_text
                    verdict = await self._self_review(
                        contract=contract,
                        prompt_text=prompt_text,
                        existing_personas=existing_personas,
                        iteration=iteration,
                        authoring_scope_id=authoring_scope_id,
                    )
                    verdicts.append(verdict)
                    obs.self_review_verdict_event(
                        iteration=iteration,
                        verdict="passed" if verdict.passed else "failed",
                        reasons=verdict.issues_joined(),
                    )
                    if verdict.passed:
                        break
                    if iteration > self.max_review_iterations:
                        break
                    feedback = verdict.issues_joined()

                if not verdicts or not verdicts[-1].passed:
                    return AuthoringResult(
                        outcome=AuthoringOutcome.rejected_after_retries,
                        handle=last_contract.handle if last_contract else None,
                        persona_dir=None,
                        iterations=iteration,
                        verdicts=tuple(verdicts),
                        reason=(
                            f"self-review failed after {self.max_review_iterations + 1} "
                            f"iterations: {verdicts[-1].issues_joined()}"
                            if verdicts
                            else "no iterations ran"
                        ),
                    )

                # Persist the passing persona directory.
                assert last_contract is not None and last_prompt is not None
                persona_dir = self._persist_directory(last_contract, last_prompt)
                return AuthoringResult(
                    outcome=AuthoringOutcome.persisted,
                    handle=last_contract.handle,
                    persona_dir=persona_dir,
                    iterations=iteration,
                    verdicts=tuple(verdicts),
                )
            except Exception as e:
                return AuthoringResult(
                    outcome=AuthoringOutcome.failed,
                    handle=None,
                    persona_dir=None,
                    iterations=0,
                    verdicts=(),
                    reason=f"pipeline exception: {type(e).__name__}: {e}",
                )

    # ---- step 1: style harvest ------------------------------------

    async def _style_harvest(
        self,
        existing_personas: Sequence[LoadedPersona],
        authoring_scope_id: str,
    ) -> str:
        with obs.authoring_step_span("style_harvest"):
            summary = "\n".join(
                f"- {p.given_name} ({p.handle}): "
                f"voice_markers={list(p.contract.voice_markers)}"
                for p in existing_personas
            )
            prompt = (
                "You are authoring a new persona. Summarise the voice / tone "
                "shared across the existing personas below so the new one "
                "fits the workspace's register.\n\n"
                f"Existing personas:\n{summary}\n"
            )
            result = await self._call_llm("style_harvest", prompt, authoring_scope_id)
            return result.text

    async def _domain_research(
        self, domain: str, authoring_scope_id: str
    ) -> str:
        with obs.authoring_step_span("domain_research"):
            prompt = (
                f"Research the domain {domain!r}. Enumerate (a) the 5-10 things "
                "a practitioner in this domain attends to, (b) the failure modes "
                "they catch, (c) the positive heuristics they apply. Be concrete."
            )
            result = await self._call_llm("domain_research", prompt, authoring_scope_id)
            return result.text

    async def _contract_synthesis(
        self,
        *,
        trigger_signal: TriggerSignal,
        domain: str,
        existing_personas: Sequence[LoadedPersona],
        style_context: str,
        domain_notes: str,
        authoring_scope_id: str,
        proposed_handle: str | None,
        revision_feedback: str | None,
    ) -> tuple[PersonaContract, str]:
        """Step 3: fill in the contract schema + prompt.md.

        Returns (validated PersonaContract, prompt.md text). The LLM
        is asked to return a JSON document conforming to the contract
        schema; we parse + validate. If validation fails, the pipeline
        re-runs (bounded by max_review_iterations).
        """
        with obs.authoring_step_span("contract_synthesis"):
            schema_hint = self._schema_hint()
            taken_handles = sorted(p.handle for p in existing_personas)
            prompt = (
                f"Author a new specialist persona for domain {domain!r}, "
                f"triggered by signal {trigger_signal.value!r}.\n\n"
                f"Workspace voice:\n{style_context}\n\n"
                f"Domain notes:\n{domain_notes}\n\n"
                f"Existing personas (do not duplicate): {taken_handles}\n"
                f"Proposed handle (you may choose another): {proposed_handle or '—'}\n\n"
                f"Return strictly two parts separated by a line containing '---PROMPT---':\n"
                f"Part 1: valid JSON matching this schema:\n{schema_hint}\n\n"
                f"Part 2: a prompt.md (free prose). 150–600 words is typical.\n"
            )
            if revision_feedback:
                prompt += (
                    f"\nRevise based on self-review feedback: {revision_feedback}\n"
                )
            result = await self._call_llm(
                "contract_synthesis", prompt, authoring_scope_id
            )
            contract, prompt_md = self._parse_synthesis_output(result.text)
            # Ensure uniqueness against existing personas:
            if contract.handle in taken_handles:
                contract = contract.model_copy(
                    update={"handle": f"{contract.handle}-{uuid.uuid4().hex[:6]}"}
                )
            return contract, prompt_md

    async def _self_review(
        self,
        *,
        contract: PersonaContract,
        prompt_text: str,
        existing_personas: Sequence[LoadedPersona],
        iteration: int,
        authoring_scope_id: str,
    ) -> SelfReviewVerdict:
        """Step 4: four-dimension self-review via LLM judgment.

        Acceptance: voice-distinctiveness ("not-generic" test),
        scope-fit, redundancy with existing personas, contract
        correctness (which is largely handled deterministically
        during synthesis but re-confirmed here).
        """
        with obs.authoring_step_span("self_review"):
            existing_summary = [
                {
                    "handle": p.handle,
                    "given_name": p.given_name,
                    "home_persona_for": list(p.contract.home_persona_for),
                }
                for p in existing_personas
            ]
            prompt = (
                "You are the self-review step for a newly authored persona. "
                "Judge four dimensions independently; each is pass/fail.\n\n"
                "DIMENSIONS:\n"
                "1. voice_distinctiveness — the persona must NOT read as a "
                "generic assistant. Reject if it sounds like a helpful AI.\n"
                "2. scope_fit — the domain is genuinely useful, not redundant.\n"
                "3. redundancy — does not significantly overlap an existing "
                "persona's home_persona_for.\n"
                "4. contract_correctness — the YAML contract has every "
                "mandatory field populated with substantive content.\n\n"
                f"Existing personas: {json.dumps(existing_summary)}\n\n"
                f"New persona contract:\n{contract.to_yaml()}\n\n"
                f"New persona prompt.md:\n{prompt_text}\n\n"
                "Return strictly a JSON object with keys: "
                "'voice_distinctiveness' (bool), 'scope_fit' (bool), "
                "'redundancy' (bool, true = passes i.e. NOT redundant), "
                "'contract_correctness' (bool), 'issues' (list of strings)."
            )
            result = await self._call_llm(
                f"self_review_iter_{iteration}", prompt, authoring_scope_id
            )
            parsed = self._parse_review(result.text)
            return SelfReviewVerdict(
                passed=all(parsed["dimensions"].values()),
                dimensions=parsed["dimensions"],
                issues=tuple(parsed.get("issues", ())),
                iteration=iteration,
            )

    # ---- helpers --------------------------------------------------

    async def _call_llm(
        self, prompt_name: str, prompt: str, scope_id: str
    ) -> LLMResult:
        result = await self.llm(prompt_name, prompt)
        # Track cost against the authoring scope.
        await self.runtime.debit(
            scope_id,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            money_cents=result.money_cents,
            prompt_name=prompt_name,
            model=result.model or self.model,
        )
        return result

    def _schema_hint(self) -> str:
        """Human-readable hint of the contract schema for the LLM.

        We deliberately do not ship Pydantic's generated JSON schema
        verbatim — it is noisy and changes shape with dependency
        updates. Instead, an authoring-stable summary.
        """
        return json.dumps(
            {
                "handle": "lowercase-ascii-like-this",
                "given_name": "Human Name",
                "contract_version": "1.0.0",
                "responsibilities": {
                    "single_point_of_contact": "...",
                    "context_holder": "...",
                    "escalation_judge": "...",
                },
                "authority_boundary": {
                    "tier_a": "defer | execute | not_applicable",
                    "tier_b": "defer | execute | not_applicable",
                    "tier_c": "defer | execute | not_applicable",
                    "tier_d": "defer | execute | not_applicable",
                },
                "escalation_taxonomy": {
                    "categories": ["at-least-one-named-category"]
                },
                "severity_vocabulary": {
                    "labels": ["most-severe-first", "..."]
                },
                "delegates_to": [],
                "home_persona_for": ["domain-label"],
                "voice_markers": ["short characteristic phrase"],
                "is_primary": False,
            },
            indent=2,
        )

    def _parse_synthesis_output(self, text: str) -> tuple[PersonaContract, str]:
        """Parse the two-part output: JSON contract then prompt.md."""
        if "---PROMPT---" not in text:
            raise ValueError("synthesis output missing '---PROMPT---' delimiter")
        json_part, prompt_part = text.split("---PROMPT---", 1)
        # Tolerate fenced JSON.
        json_str = json_part.strip()
        if json_str.startswith("```"):
            # Strip fences.
            json_str = "\n".join(
                line for line in json_str.splitlines() if not line.startswith("```")
            )
        raw = json.loads(json_str)
        # Force pending_introduction/is_addressable defaults regardless
        # of what the LLM returned.
        raw["pending_introduction"] = True
        raw["is_addressable"] = False
        contract = PersonaContract.model_validate(raw)
        return contract, prompt_part.strip()

    def _parse_review(self, text: str) -> dict[str, Any]:
        """Extract the review JSON from the LLM text."""
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = "\n".join(
                line for line in stripped.splitlines() if not line.startswith("```")
            )
        raw = json.loads(stripped)
        dims = {
            SelfReviewDimension.voice_distinctiveness: bool(
                raw.get("voice_distinctiveness", False)
            ),
            SelfReviewDimension.scope_fit: bool(raw.get("scope_fit", False)),
            SelfReviewDimension.redundancy: bool(raw.get("redundancy", False)),
            SelfReviewDimension.contract_correctness: bool(
                raw.get("contract_correctness", False)
            ),
        }
        return {"dimensions": dims, "issues": list(raw.get("issues", []))}

    def _persist_directory(
        self, contract: PersonaContract, prompt_text: str
    ) -> Path:
        """Write the new persona directory. Contract has
        pending_introduction=True, is_addressable=False already (set
        during synthesis parse)."""
        from workspace_bootstrap.workspace_paths import (
            personas_dir as _personas_dir,
        )

        personas_dir = _personas_dir(self.workspace_root)
        persona_dir = personas_dir / contract.handle
        persona_dir.mkdir(parents=True, exist_ok=False)
        (persona_dir / "contract.yaml").write_text(contract.to_yaml())
        (persona_dir / "prompt.md").write_text(prompt_text)
        return persona_dir
