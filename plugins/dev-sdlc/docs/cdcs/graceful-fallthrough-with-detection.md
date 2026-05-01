# Core Development Convention — graceful fallthrough must include detection + surface

> **Graceful fallthrough must include detection + surface, not silent swallow.** A failure inside a runtime path that is "handled" by `try: ... except: pass` (or any equivalent silent-swallow) violates ODD §2.5 — no acceptance criterion says "swallow and continue silently." Every catch in a runtime path must (1) **identify** the failure when it happens, (2) **surface** it to the persona (and the user when relevant), (3) leave a forensic trail that supports **research** (root-cause), and (4) enable **repair** (auto-recovery if possible; surfaced-for-fix otherwise). Test against the non-tech-user persona: they would never have noticed memory was broken; the system has to do this for them.

Rationale. The 2026-04-29 memory-sidecar incident motivated this CDC. The graphiti MCP had been stuck in "graphiti not initialised (lifespan not entered)" for an unknown duration. The wiring (UPS hook → primary_persona.cli → memory_consumer → MCP) was firing on every user message and failing silently with graceful fallthrough — by design, no observable user impact. But "silent graceful fallthrough" is structurally insufficient: failures need to be identified, surfaced, researched, and repaired. The non-tech user would never have noticed; the system has to do this for them. This is symmetric to (and tighter than) `shutdown-path-broad-catch.md` — that CDC tightened bare `pass` in teardown paths to require observability emission; this CDC extends the same principle to every runtime fallthrough where the silent-handling shape was the design intent.

Connection to ODD §2.5. Silent-except branches are **non-objective by construction**. No AC declares "swallow this failure and continue silently"; if the AC ladder named the failure-handling outcome, the catch would surface it — that's what the AC requires. Silent-handling re-extends UP the objective chain. **Graceful fallthrough IS an objective**; **silent-graceful-fallthrough ISN'T**. The objective form is "on failure, the system continues operating in a degraded mode AND surfaces the degradation to observability AND attempts auto-recovery (where possible) AND surfaces a fix-path to the persona/user (where auto-recovery is not possible)." Anything narrower fails the §2.5 outcome-shaped test.

How to apply. Every `try: ... except: pass` (or equivalent silent-swallow — `except Exception: return None`, `except: continue`, etc.) in a runtime path is an ODD §2.5 violation. The catch must include detection + surface. Minimum: `logger.warning("<event_name>", exc_info=True)` plus an observability span event (`span.add_event("<event_name>", {"exception": type(exc).__name__, ...})`) when an open span is in scope at the catch site. For surfaceable degradation (the failure changes what the persona/user can rely on), additionally emit a structured health event readable by the UPS hook contributor for the affected component. Pattern:

```python
try:
    result = mcp_client.send(payload)
except MCPNotInitialisedError as exc:
    logger.warning("memory_consumer_mcp_not_ready", exc_info=True)
    span.add_event("memory_degraded", {"exception": type(exc).__name__, "component": "graphiti"})
    health_emit("memory-system", "degraded", reason=str(exc))
    return None  # graceful fallthrough preserved; caller observes None
```

Structural-enforcement candidates (post-v0.1.0 implementation; surfaced for FIDRAFT graduation, not blocking M6c). (a) Periodic-health-monitor scope-of-work entries for every MCP / sidecar / external dependency the harness consumes — checks + emits structured event when degraded. (b) UPS hook contributor that reads each component's most-recent-health-event and surfaces degraded-state into `additionalContext`, so the persona always knows what's working and what isn't. (c) Auto-recovery primitives (restart attempt + bounded retry) co-located with the degradation observer. (d) Systematic audit-pass across existing components for silent-swallow patterns — every component currently shipping has paths that would silently degrade today; the audit identifies them for retrofit. Composes with: graceful-degradation/dormancy component (which already covers some of this for memory specifically), the A4 structural-enforcement programme, and observability-aggregator.

Applied immediately to every new runtime path from M6c forward, and surfaced as the methodology rule against which the post-v0.1.0 audit-pass evaluates the existing shipping code.
