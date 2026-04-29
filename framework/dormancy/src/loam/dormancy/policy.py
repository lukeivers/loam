"""Response-policy dispatch (D4).

Four declared policies:

    P1. pause_all             — orchestrator.pause_activation(reason)
    P2. pause_llm_only        — pause_activation + rt.pause per LLM scope
    P3. fall_through_to_fail  — pause_activation + rt.fail per LLM scope
    P4. request_user_decision — pause_activation + notify + wait

Per-mode defaults come from config. Per-scope overrides ride on
scope-of-work's `ScopeSpec.constraints` field — the detector reads a
constraint entry of shape `degradation_policy=<policy_name>`. This is
metadata the workspace supplies; no amendment to scope-of-work.

The dispatcher is responsible for:

    - Translating mode trips to policy calls
    - Iterating active scopes and applying per-scope overrides
    - Calling the orchestrator's pause_activation hook
    - Calling scope-runtime's pause / fail per scope
    - Recording paused-scope IDs on the active episode for resume
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable, Protocol, Sequence

from . import observability as obs
from .fsm import DegradationMode, FSMState, FSMTransition


# ---- policy enum -------------------------------------------------------


class Policy(str, Enum):
    pause_all = "pause_all"
    pause_llm_only = "pause_llm_only"
    fall_through_to_fail = "fall_through_to_fail"
    request_user_decision = "request_user_decision"


# ---- integration protocols ---------------------------------------------


class OrchestratorHooks(Protocol):
    """What the policy dispatcher needs from the orchestrator.

    Only `pause_activation` / `resume_activation` are used. No amendment
    to the orchestrator's surface.
    """

    def pause_activation(self, reason: str) -> None: ...
    def resume_activation(self) -> None: ...


class ScopeRuntimeLike(Protocol):
    """Subset of scope-of-work's public API we consume."""

    def list(self, *, states: Sequence[Any] | None = None, **kwargs: Any) -> list[Any]: ...
    async def pause(self, scope_id: str, reason: str | None = None) -> Any: ...
    async def resume(self, scope_id: str) -> Any: ...
    async def fail(self, scope_id: str, reason: str) -> Any: ...


# ---- per-scope override extraction ------------------------------------


def scope_has_llm_dependency(scope: Any) -> bool:
    """A scope is LLM-dependent if its constraints or owner_persona
    name any LLM-related concern, OR if it carries a budget with
    non-zero tokens. The default is conservative (treat as LLM-
    dependent unless deterministic explicitly declared)."""
    # Constraint-marker opt-out: `deterministic_only=true` in constraints.
    for c in getattr(scope, "constraints", ()):  # type: ignore[attr-defined]
        if isinstance(c, str) and c.strip().lower() in (
            "deterministic_only=true",
            "deterministic-only",
        ):
            return False
    # Budget-marker: if tokens cap is 0 and money cap is 0, it's
    # declared deterministic.
    budget = getattr(scope, "budget", None)
    if budget is not None:
        tokens = getattr(budget, "tokens", None)
        money = getattr(budget, "money_cents", None)
        if (tokens == 0 or tokens is None) and (money == 0 or money is None):
            return False
    return True


def scope_policy_override(scope: Any) -> Policy | None:
    """Extract per-scope `degradation_policy=X` from constraints, if
    any. Returns None if no override declared."""
    for c in getattr(scope, "constraints", ()):  # type: ignore[attr-defined]
        if not isinstance(c, str):
            continue
        stripped = c.strip()
        if not stripped.startswith("degradation_policy="):
            continue
        val = stripped.split("=", 1)[1].strip()
        try:
            return Policy(val)
        except ValueError:
            continue
    return None


def scope_has_user_relevant_escalation(scope: Any) -> bool:
    """True if the scope carries an `escalation_trigger` flagged as
    user-relevant. Heuristic: a constraint of form
    `user_relevant_on_degradation=true` opts in."""
    for c in getattr(scope, "constraints", ()):  # type: ignore[attr-defined]
        if isinstance(c, str) and "user_relevant_on_degradation=true" in c.lower():
            return True
    return False


# ---- dispatcher --------------------------------------------------------


@dataclass
class PolicyApplication:
    """Record of a policy application — useful for tests and episode
    bookkeeping."""

    policy: Policy
    mode: DegradationMode
    reason: str
    paused_scope_ids: list[str]
    failed_scope_ids: list[str]


@dataclass
class PolicyDispatcher:
    """Applies the right policy when a mode FSM trips.

    Usage:

        dispatcher = PolicyDispatcher(
            orchestrator=orch,
            scope_runtime=rt,
            defaults={DegradationMode.down: Policy.pause_all, ...},
        )
        app = await dispatcher.apply(mode, episode_id)

    The dispatcher does NOT decide when to apply; callers (the
    component) drive it in response to transitions.
    """

    orchestrator: OrchestratorHooks
    scope_runtime: ScopeRuntimeLike
    defaults: dict[DegradationMode, Policy]

    async def apply(
        self,
        mode: DegradationMode,
        episode_id: str,
        *,
        signal: str = "",
    ) -> PolicyApplication:
        default_policy = self.defaults[mode]
        reason = f"claude_upstream_degraded:{mode.value}:{episode_id}"

        self.orchestrator.pause_activation(reason)

        # Active, non-deterministic scopes are candidates for pause/fail.
        paused: list[str] = []
        failed: list[str] = []
        try:
            from loam.scope_of_work.spec import ScopeState  # lazy import

            states_filter = [ScopeState.active]
        except Exception:  # pragma: no cover — only needed in tests without the pkg
            states_filter = None

        active_scopes = self.scope_runtime.list(states=states_filter)
        for scope in active_scopes:
            if not scope_has_llm_dependency(scope):
                continue
            per_scope = scope_policy_override(scope) or default_policy
            scope_id = getattr(scope, "scope_id", None) or getattr(scope, "id", None)
            if scope_id is None:
                continue
            if per_scope == Policy.pause_all:
                # P1 leaves in-flight scopes running under default — but
                # any LLM-dependent scope with P1 per-scope override
                # should still pause, since pause_all means "stop
                # everything". Pause.
                await self.scope_runtime.pause(
                    scope_id, reason=f"degradation:{episode_id}"
                )
                paused.append(scope_id)
            elif per_scope == Policy.pause_llm_only:
                await self.scope_runtime.pause(
                    scope_id, reason=f"degradation:{episode_id}"
                )
                paused.append(scope_id)
            elif per_scope == Policy.fall_through_to_fail:
                await self.scope_runtime.fail(
                    scope_id,
                    reason=f"degradation:{episode_id}:no_auto_resume",
                )
                failed.append(scope_id)
            elif per_scope == Policy.request_user_decision:
                await self.scope_runtime.pause(
                    scope_id,
                    reason=f"degradation:{episode_id}:awaiting_user",
                )
                paused.append(scope_id)

        obs.policy_decision(
            policy=default_policy.value,
            episode_id=episode_id,
            mode=mode.value,
            reason=signal,
        )

        return PolicyApplication(
            policy=default_policy,
            mode=mode,
            reason=reason,
            paused_scope_ids=paused,
            failed_scope_ids=failed,
        )

    async def release(
        self,
        mode: DegradationMode,
        episode_id: str,
        paused_scope_ids: Sequence[str],
    ) -> list[str]:
        """Resume phase: resume each paused scope and call
        resume_activation. Returns the list of successfully resumed
        scopes."""
        resumed: list[str] = []
        for sid in paused_scope_ids:
            try:
                await self.scope_runtime.resume(sid)
                resumed.append(sid)
            except Exception:
                # Scope may already be in a terminal state — not fatal.
                continue
        self.orchestrator.resume_activation()
        return resumed


def build_defaults_from_config(cfg: Any) -> dict[DegradationMode, Policy]:
    """Extract default-policy-per-mode from a DegradationConfig."""
    return {
        DegradationMode.down: Policy(cfg.modes.down.default_policy),
        DegradationMode.overloaded: Policy(cfg.modes.overloaded.default_policy),
        DegradationMode.rate_limited: Policy(cfg.modes.rate_limited.default_policy),
        DegradationMode.garbage: Policy(cfg.modes.garbage.default_policy),
        DegradationMode.auth_broken: Policy(cfg.modes.auth_broken.default_policy),
        # latency is advisory; a dummy default is never applied.
        DegradationMode.latency_sustained: Policy.pause_llm_only,
        # Amendment 3 (hands-off-lifecycle) — memory sidecar mode.
        DegradationMode.memory_sidecar: Policy(
            cfg.modes.memory_sidecar.default_policy
        ),
    }
