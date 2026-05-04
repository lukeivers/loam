---
description: Author every fallback / graceful-degradation path with a detection clause that surfaces when the fallback fires. Plain graceful-fallthrough (try-the-best-path-then-degrade-silently) hides regressions; the detection clause makes silent failures observable. Pattern applies to code (try/except returning a default + log), to skills (graceful-degradation section + a surface-on-firing line), to dispatch (halt-and-surface when the agent finds an unexpected path), and to ops (alerting on fallback frequency). Use whenever authoring code, SKILLs, dispatch briefs, or operational runbooks that include a degraded path; never ship a fallback without a detection clause.
---

# graceful-fallthrough-with-detection

The graceful-degradation pattern is universally good (a
system that survives one missing dependency is more robust
than one that crashes). But graceful-degradation WITHOUT
detection is the failure mode this skill prevents:

- Code returns a sensible default when an upstream service
  is down → the service stays down for days because nobody
  noticed.
- A SKILL's graceful-degradation section says "substitute X
  for Y" → fresh personas use the substitution forever
  without realizing they're degraded.
- A dispatch's halt-trigger fires → the agent silently
  routes around it because the brief said "find another
  way" without saying "and surface that you did so."
- An op runbook says "if metric A is missing, fall back to
  metric B" → metric A stays broken because the fallback
  hides the gap.

The detection clause makes the fallback OBSERVABLE: it logs,
audit-trails, surfaces inline, alerts on frequency, OR
fires a halt-and-surface — whichever surface the layer
supports. Without the clause, graceful-degradation is
silent-failure-with-extra-steps.

## What this skill captures

The graceful-fallthrough-with-detection pattern, layer by
layer:

```
[Primary path attempt]
        ↓
[Fails / unavailable / missing]
        ↓
[Fallback path]                    ← graceful-degradation
        ↓
[Detection clause]                 ← THIS SKILL
        ↓                          ← (the load-bearing piece)
   ┌────┴────┐
   ↓         ↓
[Surface]  [Audit-log / metric / alert]
```

The required parts:

1. **Primary path attempt named.** What's the system
   designed-to-do path? Without a named primary, "fallback"
   is just "default" and there's no degradation to
   detect.
2. **Failure mode named.** What conditions trigger the
   fallback? Network timeout? File-not-found? Service-
   unavailable? Each named condition is a candidate for the
   detection surface.
3. **Fallback path defined.** What does the system DO when
   the primary fails? Default value? Substitute method?
   Alternative service? Skip-and-continue?
4. **Detection clause.** The piece this skill exists for.
   At least ONE of:
   - **Inline surface.** The fallback firing surfaces in
     the user-visible reply (e.g., "memory-system service
     unreachable; fell back to file-based store").
   - **Audit-log entry.** The fallback writes an event
     (event_kind: `fallback_<from>_<to>`) with timestamp +
     condition + degradation level.
   - **Metric / counter increment.** Fallback frequency
     is observable in monitoring (e.g.,
     `loam_fallback_rate{primary=memory_system,
     fallback=file_store}`).
   - **Halt-and-surface.** For load-bearing fallbacks,
     the fallback firing IS a halt condition (the work
     pauses for owner ruling on whether to continue
     degraded).
5. **Frequency-aware surfacing.** If the fallback fires
   once per hour, inline-surface every time is noise. If
   once per week, every-time inline is right. Frequency
   guides the surface choice:
   - High-frequency + low-stake → metric only.
   - Low-frequency + high-stake → inline + audit-log + alert.
   - Mid-frequency + mid-stake → audit-log + periodic
     summary (daily / weekly).
6. **Recovery-acknowledgement.** When the primary path
   recovers (service back up, file present again), the
   detection surface MUST log the recovery too —
   asymmetric logging (firing-only) makes monitoring
   noisier than it needs to be.

## When to use

Trigger conditions:

- Authoring code that includes a try/except + fallback /
  default-return.
- Authoring a SKILL whose `## Graceful degradation` section
  describes a substitution path.
- Authoring a dispatch brief whose halt-trigger says "find
  another way" or "fall back to <approach>".
- Authoring an op runbook with conditional metric / alert /
  recovery paths.
- Reviewing existing code / SKILL / dispatch / runbook for
  silent-failure risk — every fallback path is a
  candidate for this skill's audit.
- An incident retrospective surfaces "we didn't notice X
  was broken for N days because the fallback hid it" — the
  retrospective informs the detection-clause author.

Skip when:

- The fallback is a UX micro-optimization (e.g., "if image
  is loading, show placeholder") — detection adds no value;
  the user observes directly.
- The primary path is genuinely optional (e.g., "if config
  file exists, load it; else use defaults") and the
  defaults ARE the production path — no degradation to
  detect.
- The system is explicitly "best-effort with no
  reliability requirement" (rare in loam; more common in
  experimental research surfaces).

## How the persona applies it

1. **Identify every fallback path in the work being
   authored.** Each `try/except`, each "if missing then
   default", each "if service down then alternative", each
   "graceful-degradation" section.
2. **For each fallback, name the primary + failure mode
   + fallback path.** Before adding the detection clause,
   the primary-mode → degraded-mode transition must be
   named.
3. **Choose the detection surface.** Match the layer:
   - Code → log statement / structured audit-log entry +
     metric increment.
   - SKILL → `## Graceful degradation` section with a
     "if detection fires, surface inline" subclause.
   - Dispatch → halt-trigger that fires on fallback;
     status-file logs the firing.
   - Op runbook → metric + alert + dashboard panel.
4. **Decide frequency-aware surface.** High-frequency low-
   stake → metric only. Low-frequency high-stake → inline +
   audit + alert.
5. **Add the recovery-acknowledgement.** Same surface logs
   the recovery (primary path back up).
6. **Test the detection.** Simulate the failure mode (kill
   the upstream, remove the file, mock the service-down
   condition); verify the detection surface fires.
7. **Test the recovery.** Restore the upstream; verify the
   detection surface logs recovery.
8. **For SKILL authoring specifically.** Every SKILL's
   `## Graceful degradation` section ends with a sentence
   like: "Detection on fallback: if [the substitution
   condition] fires, surface the gap inline — don't
   silently degrade." This skill IS that sentence's
   meta-rule.
9. **For dispatch brief authoring specifically.** When a
   halt-trigger says "find another way," it MUST also say
   "and surface in the status file that you did so." The
   "find another way" phrase without the surface clause
   is the silent-fallback pattern.

### Examples by layer

**Code example (Python):**

```python
def get_memory(query: str) -> list[Result]:
    try:
        return memory_system.query(query)
    except MemoryServiceUnavailable as e:
        # graceful-fallthrough-with-detection
        log.warning(
            "memory_system unavailable; falling back to "
            "file_store",
            extra={
                "fallback_from": "memory_system",
                "fallback_to": "file_store",
                "reason": str(e),
            },
        )
        metrics.increment(
            "loam_fallback_rate",
            tags={
                "from": "memory_system",
                "to": "file_store",
            },
        )
        return file_store.query(query)
```

**SKILL example (graceful-degradation section):**

```markdown
## Graceful degradation

When raw Claude Code without loam dev-sdlc plugin:

- Substitute `loam amend seal` with manual sidecar update
  + `chore(seals): pin <feature> at <SHA>` commit.
- Substitute the audit-log surface with `CHANGELOG.md`
  rollup.
- Detection on fallback: if the project lacks ANY persistent
  paper-trail surface (no CHANGELOG, no GitHub release notes,
  no Notion doc), the fallback is silently degraded;
  surface this gap inline rather than degrading further.
```

**Dispatch brief example:**

```markdown
## Halt triggers

- WD drifts → halt + surface.
- Plan-doc not authored before code → halt + surface.
- Source-edit feat fails to compile → halt + surface +
  `find another way` only AFTER surfacing the failure to
  the dispatcher (not silently re-attempt).
```

The "after surfacing" clause is the detection surface in
dispatch-brief-authoring shape.

## Graceful degradation

When raw Claude Code without loam dev-sdlc plugin:

- The pattern (every fallback has a detection clause)
  applies universally. Substitute loam-specific surfaces
  (audit-log, metrics) with the project's available
  surfaces (Sentry, Datadog, Slack alerts, GitHub issues).
- Detection on fallback: if a project genuinely has NO
  observability surface for fallbacks, the right answer
  is to add one before shipping the fallback path. The
  silent-fallback shipping itself is the regression this
  skill prevents.

(Yes, this skill's own graceful-degradation section
applies the pattern to itself. Recursion.)

## Composition

- **Every other SKILL** — every SKILL's
  `## Graceful degradation` section composes with this
  skill. This skill IS the meta-rule that applies to all
  graceful-degradation sections.
- **`hook-violation-recovery` skill** — the bypass-and-
  forget failure mode IS the silent-fallback pattern; this
  skill is what makes "audit-trail entry on every override"
  load-bearing.
- **`audit-finding-triage` skill** — when an agent
  surfaces a fallback firing, the triage routes the
  finding (in-scope-resolve / in-scope-defer / out-of-
  scope-FIDRAFT / owner-escalate).
- **`feedback_subagent_odd_violation_halt`** — agents must
  halt and surface ODD violations; surfacing IS the
  detection clause for the agent's "find another way"
  fallback.
- **`feedback_specific_claims_verified_or_marked_guess`** —
  related discipline: the detection surface must
  distinguish "primary path succeeded" from "fallback fired
  + degraded result"; conflating them is the asymmetric
  logging the recovery-acknowledgement clause prevents.
- **`feedback_durable_capture_for_planned_work`** —
  durable capture is the detection clause for "I'll
  remember next session" fallbacks; this skill captures
  the meta-rule.
- **PR-safety gate (v0.1.9 Cycle 1, sealed `790807d`)** —
  the audit-log surface IS a detection surface for
  override-commit fallbacks; the gate's audit-log floor
  applies this pattern.
- **`loam-amend-status-quick` skill** — the diagnostic
  surface that observes when fallbacks are firing across
  cycles.
- **`feedback_locked_design_not_license_for_bad_outcomes`**
  — if a fallback's existence reveals the locked design
  is producing bad outcomes (e.g., the fallback fires more
  often than the primary), surface the revisit question.

## Out of scope

- The specific monitoring surface (Sentry / Datadog /
  Prometheus / OpenTelemetry) — implementation choice;
  this skill captures the discipline, not the tool.
- Frequency-aware surfacing thresholds (when does
  high-frequency become low-frequency?) — application-
  specific; the persona authors per the system's
  observability budget.
- Recovery-detection patterns for transient failures
  (e.g., circuit breaker reset thresholds) — broader
  pattern; circuit-breakers compose ON TOP OF this
  skill's discipline but aren't enumerated here.
- Distributed-system consensus failure modes — different
  shape; CAP-theorem fallbacks have observability concerns
  this skill names but doesn't enumerate.
- Performance-driven graceful-degradation (e.g., quality-
  reduction under load) — the detection clause still
  applies but the surface is usually metric-only;
  application-specific.
- The `--no-verify` git-hook bypass detection — covered
  by `hook-violation-recovery` skill; this skill is the
  meta-rule, that skill is the application.
