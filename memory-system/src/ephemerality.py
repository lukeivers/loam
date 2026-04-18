"""D5 — Ephemerality filter.

Discriminate at ingest: is the episode worth remembering, or is it
transient telemetry that should never land in the graph?

Spec v1.1 R2 ("Accrual behaviour refined"): `extremely ephemeral` is a
narrow enumerated exclusion set (current-CPU readings, ticking clocks,
volatile UI state, transient telemetry). Everything else is saved —
conversations, decisions, research, work, observations. The rubric
lists what is EXCLUDED; anything unlisted is accrued.

Implementation philosophy: deterministic-first (quality-standards.md
rule 4). The rubric is a list of exclusion rules in `config/memory.yml`
under `ephemerality.exclude`. Each rule has `sources` (substring match
against episode source) and optional `body_patterns` (regex match
against body). An episode matching any rule is discarded at ingest.
No LLM call on the fast path; no judgment at the edge; the rubric is
the policy and it is editable without code change.

This module is the fast gate at the front of the ingest pipeline.
It emits a span on every evaluation (observability D7) so audits can
reconstruct what was discarded and why.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from .config import section


@dataclass(frozen=True)
class EphemeralityDecision:
    """Result of applying the rubric to a candidate episode.

    `is_ephemeral=True` means the episode is excluded from storage.
    `rule_name` identifies the matched rule (or None for an accrual).
    `reason` is a short explanation for audit purposes.
    """

    is_ephemeral: bool
    rule_name: str | None
    reason: str


@dataclass(frozen=True)
class _CompiledRule:
    name: str
    sources: tuple[str, ...]
    body_patterns: tuple[re.Pattern[str], ...]


@lru_cache(maxsize=4)
def _load_rules() -> tuple[_CompiledRule, ...]:
    cfg = section("ephemerality")
    raw_rules = cfg.get("exclude") or []
    compiled: list[_CompiledRule] = []
    for rule in raw_rules:
        name = str(rule.get("name", "unnamed"))
        sources = tuple(str(s).lower() for s in rule.get("sources") or [])
        patterns = tuple(
            re.compile(p, flags=re.IGNORECASE | re.MULTILINE)
            for p in rule.get("body_patterns") or []
        )
        compiled.append(_CompiledRule(name=name, sources=sources, body_patterns=patterns))
    return tuple(compiled)


def reload_rules() -> None:
    """Drop the compiled-rule cache; used after config reload."""
    _load_rules.cache_clear()


def classify(
    *,
    source: str | None,
    source_description: str | None,
    body: str,
) -> EphemeralityDecision:
    """Apply the rubric. Case-insensitive source match; regex body match.

    Returns a decision with is_ephemeral True/False plus audit fields.
    The caller (ingest pipeline) short-circuits on True: the episode is
    NOT passed to Graphiti, nothing is persisted, an observability span
    records the decision.
    """
    haystack = " ".join(
        s.lower() for s in (source or "", source_description or "") if s
    )
    for rule in _load_rules():
        if any(marker and marker in haystack for marker in rule.sources):
            return EphemeralityDecision(
                is_ephemeral=True,
                rule_name=rule.name,
                reason=f"source matched rule {rule.name!r}",
            )
        if rule.body_patterns and body:
            for pattern in rule.body_patterns:
                if pattern.search(body):
                    return EphemeralityDecision(
                        is_ephemeral=True,
                        rule_name=rule.name,
                        reason=(
                            f"body matched rule {rule.name!r} "
                            f"pattern {pattern.pattern!r}"
                        ),
                    )
    return EphemeralityDecision(
        is_ephemeral=False,
        rule_name=None,
        reason="no ephemeral rule matched; default=accrue",
    )


def rubric_summary() -> dict[str, Any]:
    """Human-readable dump of the current rubric — useful in service
    /health and in the bundled documentation.
    """
    return {
        "default": section("ephemerality").get("default", "accrue"),
        "rules": [
            {
                "name": rule.name,
                "sources": list(rule.sources),
                "body_patterns": [p.pattern for p in rule.body_patterns],
            }
            for rule in _load_rules()
        ],
    }
