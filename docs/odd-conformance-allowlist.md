# ODD-conformance allowlist

**Authored:** 2026-05-08 (v0.3.0 Cycle 6 — feature-honesty audit).
**Authority:** `docs/v0-3-0-feature-honesty-audit.md` §6 (AC.FHA.4 sweep).
**Cross-reference:** `docs/release-roadmap.md` §3 v0.3.0 AC.V030.5; master plan `docs/plans/v0-3-0-master-plan.md` §3 C6.

---

## §1 — Purpose

`framework/` ships 18 directories. The strict ODD-conformance reading per master plan §3 C6 ("every `framework/` component declares `objectives.yaml` or named exemption") would require authoring 18 per-component objective specs in this audit cycle. The cycle's quality bar is **feature-honesty**, not bulk-spec-authoring; per-component ODD authoring is a v0.7.0 scope item per master plan §7 ("structural enforcement of principles via hooks/skills/Stop-hook contributors").

This allowlist establishes the named-exemption convention so:

1. The audit's AC.FHA.4 closes with a documented disposition.
2. v0.7.0's planner has a load-bearing artefact to extend (replace exemptions with real `objectives.yaml` files; remove allowlist entries one component at a time).
3. The convention is discoverable via the `framework/` tree's session-start grounding corpus.

---

## §2 — The allowlist

Every `framework/` directory listed below has **no `objectives.yaml`** and is **named-exempt** under the rationale recorded.

| Component | Type | Rationale |
|---|---|---|
| `framework/cost-governance/` | runtime component | Token / time / money ceilings + drift detection. ODD spec deferred to v0.7.0 structural enforcement (named in release-roadmap §3 v0.7.0). |
| `framework/dormancy/` | runtime component | Pause / resume / fail-loud policy. ODD spec deferred to v0.7.0. |
| `framework/hands-off-lifecycle/` | runtime component | SessionStart hook + supervisor + drain/recovery. Owns the SessionStart greeting + first-run scaffold contributor. ODD spec deferred to v0.7.0. |
| `framework/loam-init/` | CLI subcommand registrant | Registers `loam init <path>` via `loam.cli.subcommands` entry-point group. Single-purpose; minimal AC family. ODD spec deferred to v0.7.0. |
| `framework/objective-tracker/` | runtime component | Forest-of-trees objective tracking with event-sourced persistence. Ironically: the component that BUILDS objective trees has no objectives.yaml of its own. ODD spec deferred to v0.7.0 (where structural enforcement makes the recursive case load-bearing). |
| `framework/observability-aggregator/` | runtime component | Single-user local trace store. ODD spec deferred to v0.7.0. |
| `framework/orchestrator/` | runtime component | Session-resilient asyncio process host; Unix-socket JSON-RPC; bind-scope dispatch. ODD spec deferred to v0.7.0. |
| `framework/per-project-pm/` | onboarding-ritual API server | Six-question onboarding ritual + per-project state. AC.ONBOARD.* family covers the surface; component-level ODD spec deferred to v0.7.0. |
| `framework/primary-persona/` | runtime component | The single voice; loader + monitor + autonomous-authoring contract; owns FBE.7 file-backed memory implementation. **The largest component**; ODD spec deferred to v0.7.0 because the per-component objective surface is large and benefits from structural-enforcement tooling that doesn't yet exist. |
| `framework/reversibility-primitive/` | runtime component | Compensation-ledger + irreversibility classification. ODD spec deferred to v0.7.0. |
| `framework/safety-layer/` | runtime component | Three-gate refusal chain + structural floor. ODD spec deferred to v0.7.0. |
| `framework/scope-of-work/` | runtime component | Event-sourced FSM for named units of work. ODD spec deferred to v0.7.0. |
| `framework/self-correction/` | runtime component | Four-part self-correction loop after refusal or budget cap. ODD spec deferred to v0.7.0. |
| `framework/self-upgrade/` | runtime component | Per-component upgrade fidelity coordinator. ODD spec deferred to v0.7.0. |
| `framework/telegram-interface/` | runtime component | Telegram channel adapter. ODD spec deferred to v0.7.0. |
| `framework/tools/` | maintenance utilities | Holds the `loam` top-level CLI binary + 7 maintenance scripts (`upgrade-merge-resolver`, `loam-memory-inspect`, etc.). Not a component; meta-directory. Per-tool ODD spec deferred to v0.7.0 if a tool becomes user-facing. |
| `framework/workspace-bootstrap/` | runtime component | Composition engine; first-run scaffolding; plugin extension protocol. ODD spec deferred to v0.7.0. |
| `framework/workspace-sync/` | runtime component | Canonical-to-workspace git-shaped sync; LLM-mediated semantic-merge gate. ODD spec deferred to v0.7.0. |

**Total: 18 entries.**

---

## §3 — Lifting the allowlist (v0.7.0 entry-point)

Per master plan §7, v0.7.0 ships:

- FR.1/FR.2/FR.3 named primitives (structural-enforcement primitive surface).
- F6 Stop-hook contributor (post-turn ODD-conformance check).
- meta-decision-haiku SKILL (per-decision conformance probe).

When v0.7.0 lands, the planner replaces this allowlist progressively:

1. Pick a component.
2. Author its `framework/<component>/objectives.yaml` against the v0.7.0 schema.
3. Remove the corresponding row from §2 above.
4. Verify the structural-enforcement primitive accepts the spec.
5. Repeat per component.

Until then, this allowlist is the named-exemption surface.

---

## §4 — Adding a new component

When v0.4.0+ adds a new `framework/<name>/` directory:

- **Default (during v0.4.0 → v0.6.x):** add a row here with rationale "v0.7.0 ODD-spec deferred (per project-policy)."
- **After v0.7.0 ships the structural-enforcement primitive:** the new component MUST author `objectives.yaml` in the same commit; this allowlist tracks only the v0.7.0-pre-existing 18 entries.

---

## §5 — Provenance

- **Audit ruling:** `docs/v0-3-0-feature-honesty-audit.md` §6 (this artefact's parent).
- **Cycle plan-doc:** `docs/plans/v0-3-0-cycle-6-feature-honesty-audit-and-verification.md` §4 + §10.3.
- **Source-of-truth release-roadmap entry:** `docs/release-roadmap.md` §3 v0.3.0 AC.V030.5.
- **Future-lift release-roadmap entry:** `docs/release-roadmap.md` §3 v0.7.0 (FR.1/FR.2/FR.3 + F6 + meta-decision-haiku SKILL).
