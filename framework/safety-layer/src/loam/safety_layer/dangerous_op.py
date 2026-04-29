"""Dangerous-op gate — stricter gate composed on top of the ask gate.

Decision procedure (proposal §4.3, research §6):
  1. Scope declares reversibility_class=irreversible, OR
  2. Scope declares an action_class in ask_list.dangerous_op_subset, OR
  3. Scope's money_cents cap meets-or-exceeds the configured threshold.
Any of (1/2/3) fires the gate. If no prior approved-for-this-spec-hash
decision exists, the gate returns BLOCK.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from loam.scope_of_work import ReversibilityClass, ScopeSpec

from .ask_list import AlwaysAskList
from .events import structural_hash
from .store import SafetyStore


@dataclass(frozen=True)
class DangerousOpDecision:
    """Output of a single dangerous-op check."""

    fired: bool
    blocked: bool
    reasons: tuple[str, ...]
    spec_hash: str
    action_classes: tuple[str, ...]


def _extract_action_classes(constraints: Iterable[str]) -> tuple[str, ...]:
    """Parse `action_class=<value>` entries from a scope spec's
    `constraints` tuple. Same pattern graceful-degradation uses for
    `degradation_policy`; no scope-of-work amendment."""
    out: list[str] = []
    for c in constraints:
        if not isinstance(c, str):
            continue
        s = c.strip()
        if s.startswith("action_class=") or s.startswith("action_class:"):
            _, _, val = s.partition("=") if "=" in s else s.partition(":")
            val = val.strip().strip('"').strip("'")
            if val:
                out.append(val)
    return tuple(out)


class DangerousOpGate:
    """Pure-function gate over ScopeSpec + AlwaysAskList + threshold."""

    def __init__(
        self,
        *,
        ask_list: AlwaysAskList,
        store: SafetyStore,
        money_threshold_cents: int,
    ) -> None:
        self._ask_list = ask_list
        self._store = store
        self._money_threshold_cents = money_threshold_cents

    @property
    def money_threshold_cents(self) -> int:
        return self._money_threshold_cents

    def classify(self, spec: ScopeSpec) -> DangerousOpDecision:
        """Return whether the gate fires for a given spec + whether it
        blocks (no unexpired approval for the spec's structural hash)."""
        classes = _extract_action_classes(spec.constraints)
        spec_hash = structural_hash(spec)

        reasons: list[str] = []
        if spec.reversibility_class == ReversibilityClass.irreversible:
            reasons.append("irreversible")
        dangerous_values = self._ask_list.dangerous_op_values()
        dangerous_hits = [c for c in classes if c in dangerous_values]
        if dangerous_hits:
            reasons.append(f"dangerous_action_class:{','.join(dangerous_hits)}")
        money_cents = spec.budget.money_cents or 0
        if money_cents >= self._money_threshold_cents:
            reasons.append(
                f"money_cents_ge_threshold:{money_cents}>={self._money_threshold_cents}"
            )

        if not reasons:
            return DangerousOpDecision(
                fired=False,
                blocked=False,
                reasons=(),
                spec_hash=spec_hash,
                action_classes=classes,
            )

        # Gate fires — look up a prior approval.
        approval = self._store.find_active_approval(spec_hash)
        blocked = approval is None
        return DangerousOpDecision(
            fired=True,
            blocked=blocked,
            reasons=tuple(reasons),
            spec_hash=spec_hash,
            action_classes=classes,
        )
