# v0.3.0 Cycle 6 — Feature-honesty audit + memory FBE.7 verification + claude -p discipline + ODD-conformance sweep + first_run_scaffold.py F821 closures

**Status:** sub-plan-doc, FINALIZED at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-6-feature-honesty-audit-and-verification`
**Date finalized:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 6.
**Predecessor cycles:** Cycles 1–5 (sealed).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

Verify documented surface against operational reality. Stranger-perspective. Last cycle to validate everything else landed correctly. Bundles four verification ACs (V030.1 / V030.3 / V030.4 / V030.5) plus first_run_scaffold.py F821 closure because each is a verification pass against already-shipped surface and they share the audit-altitude theme. Stranger cloning loam at v0.3.0 can run every named capability + verify it operates per docs; this cycle is the meta-evidence v0.3.0 ships.

## §3 — Component fence

PRIMARY: `docs/v0-3-0-feature-honesty-audit.md` (NEW); `docs/odd-conformance-allowlist.md` (NEW).

Source edits (sealed-component scope):
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` — F821 closure (TYPE_CHECKING guard).
- `framework/tools/upgrade-merge-resolver/src/loam/upgrade_merge_resolver/__init__.py` — claude -p MCP-isolation flags.

Test additions:
- `framework/primary-persona/tests/test_AC_FHA_6_stranger_clone_fbe7_outcome.py` — FBE.7 outcome-altitude probe.
- `framework/tools/upgrade-merge-resolver/tests/test_AC_FHA_3_mcp_isolation.py` — claude -p invariant.

Read-only across:
- `README.md`, `docs/getting-started.md`, `docs/dev-mode-getting-started.md` — every named capability.
- Sealed-component surface — `framework/` components + `plugins/` source.
- `claude -p` invocations in `framework/` + `plugins/` source.
- Workspace state on stranger-clone (FBE.7 cross-session verification).

Tertiary: per-component `objectives.yaml` or named exemption; tracked-allowlist for ODD-orphans.

## §4 — AC family — `AC.FHA.*` (FINAL)

| AC | Description | Verification | Verdict |
|---|---|---|---|
| AC.FHA.1 | Feature-honesty audit deliverable exists at `docs/v0-3-0-feature-honesty-audit.md`; named-capability count maps to sealed-component surface (or named exemption). | Audit doc §3 (CLI verbs / runtime components / hook surfaces / file-based memory / plugin protocol / onboarding ritual / architecture-doc claims). | PASS-WITH-OWNER-ACTION-LINE (3 docs-drift findings surfaced; recommendations in audit §9). |
| AC.FHA.2 | Memory FBE.7 stranger-clone verification — cold install / fresh process simulating /clear / next session retrieves prior. | Tractable substitute (production-CLI altitude tempdir probe) + Docker-only gap surfaced for owner-action-line per stub §10. | PASS-WITH-OWNER-ACTION-LINE (Docker daemon down at AI-time; substitute green; owner-action-line for fresh-machine probe). |
| AC.FHA.3 | `claude -p --strict-mcp-config` invariant — every loam-source subprocess invocation carries the flag. | Repo-wide grep + 2-test invariant suite at `test_AC_FHA_3_mcp_isolation.py` mirroring `test_resolver_client_mcp_isolation.py`. | PASS (3 production sources; 1 gap closed in-cycle: upgrade-merge-resolver). |
| AC.FHA.4 | ODD-conformance sweep — every `framework/` component declares `objectives.yaml` or named exemption. | Sweep + tracked-allowlist at `docs/odd-conformance-allowlist.md` (18 entries; v0.7.0 structural-enforcement scope-lift). | PASS (allowlist authored; per-component objectives.yaml deferred to v0.7.0). |
| AC.FHA.5 | `first_run_scaffold.py` F821 bugs closed (2 lines: 853 + 879). | TYPE_CHECKING guard at module head; import-time check; ruff F821 sweep clean across framework/ + plugins/. | PASS (F821 count: framework + plugins = 0). |
| AC.FHA.6 | Outcome-altitude — full audit cross-references resolve + FBE.7 cross-session passes end-to-end. | Production-CLI probe (`cli_stop` → `drain_once` → `cli_user_prompt_submit`) emits retrieval block citing prior turn. | PASS. |

**Outcome-altitude AC:** AC.FHA.6 (per `feedback_test_outcome_altitude_required`).

## §5 — Build dispatch brief

Authored inline by dispatcher at cycle-6 dispatch turn (this turn).

## §7 — Out of scope

- New feature additions surfaced during audit (those go to FIDRAFT or future minor).
- New ODD-conformance enforcement mechanisms (those are v0.7.0 structural enforcement).
- Audit of plugin-specific capabilities beyond dev-sdlc (other plugins land in v0.10.0+).
- Per-component `objectives.yaml` authoring (v0.7.0 lift).
- Author of `framework/loam-init/` + `framework/per-project-pm/` reference pages under `docs/components/` (PATCH-class to v0.3.1 OR in-cycle if owner rules Path A on audit §9 finding 1).
- `docs/components/memory.md` post-C2 reframe (PATCH-class to v0.3.1 OR in-cycle if owner rules Path A on audit §9 finding 2).
- Other 85 ruff errors (F841 / E402 / E741 / E731) — out of scope per brief; this cycle closes only the 2 F821s in first_run_scaffold.py per master plan §3 C6.

## §10 — F2 RF gaps to surface at dispatch

- **Stranger-clone verification mechanism** — Docker daemon DOWN at AI-time (installed but not running); fresh-machine verification requires owner-action. AC.FHA.2 closed via tractable production-CLI substitute; Docker-only gaps surfaced as owner-action-line.
- **100% match standard** — three docs-vs-reality gaps surfaced in §3.2 + §3.3 of audit doc:
  - Component-count "fifteen" wording is honest under one reading + drifted under another.
  - `loam-init` + `per-project-pm` undocumented but real components.
  - `docs/components/memory.md` references graphiti-as-v0.1.x-plugin (now backlog per Luke 2026-05-08).
  - All three are DOCS-DRIFT (rewrite docs); not feature gaps. Recommended in-cycle close per Path A; owner ruling required.
- **ODD-conformance sweep** — 18 ODD-orphans, all moved to allowlist. v0.7.0 lifts.

## §11 — Provenance trail

- Master plan §3 C6.
- Release-roadmap §3 v0.3.0 AC.V030.{1,3,4,5}.
- `feedback_test_outcome_altitude_required.md` (AC.FHA.6 binding).
- Predecessor cycles: C1 `459c7fc`, C2 `013553e`, C3 `be48b34`, C4 `7afb648`, C5 `542b939`.

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

| Decision | Choice | Rationale |
|---|---|---|
| Stranger-clone verification mechanism | Tractable production-CLI substitute (tempdir-isolated) | Docker daemon down at AI-time (owner-action gate); substitute exercises FBE.7 contract end-to-end at production-CLI altitude. Gap surfaced as owner-action-line per stub §10. |
| Component-count finding close path | Surface to owner (Path A vs Path B in audit §9) | Audit's "100% match standard" is the C6 quality bar; trade-off between in-cycle docs-rewrite (Path A) vs PATCH-carry (Path B) is owner-class because it touches release-roadmap §6 carry-forward. |
| ODD-conformance sweep close | Tracked-allowlist (`docs/odd-conformance-allowlist.md`) | Authoring 18 `objectives.yaml` files exceeds C6 scope (audit/verify, not bulk-spec author); v0.7.0 structural-enforcement lift is the named entry-point. |
| F821 fix mechanism | `if TYPE_CHECKING:` guard at module head | Preserves the lazy-import discipline the helpers' docstrings document; zero runtime cost; ruff's forward-reference resolver consumes the typing-layer names. Alternative considered (rewrite annotations as quoted dotted strings) — rejected because the import-graph rationale is load-bearing. |
| upgrade-merge-resolver MCP-isolation pattern | Mirror workspace-sync `_resolver_client.py` byte-for-byte | One discipline; one test shape; minimum cognitive overhead for future readers comparing the two surfaces. |
| Test placement | `framework/primary-persona/tests/test_AC_FHA_6_*.py` (outcome) + `framework/tools/upgrade-merge-resolver/tests/test_AC_FHA_3_*.py` (invariant) | Per-component testpath conventions; tests live next to the code they probe. |
| Build report path | `workspace/.scratch/claude-output/v0-3-0-cycle-6-build-report.md` (per dispatch brief) | Per dispatch instruction; ephemeral scratch surface; gitignored under workspace's `.scratch/.gitignore`. |
| §14 backfill SHAs | Recorded post-seal in master plan §11 SHA register + this section's table | Per `feedback_no_amend_in_agent_dispatches`; backfill commits are NEW commits, not `--amend`. Seal commit + apply commit + backfill commit lands as separate commits. |
| Sealing component anchor | dev-sdlc (mirroring C1/C2/C3/C4/C5 precedent) | Cross-cutting cycle; multi-component fence (workspace-bootstrap source + tools/upgrade-merge-resolver source + primary-persona tests + docs); dev-sdlc is the methodology-surface owner per the precedent. |

### Post-seal SHA register (backfill)

| Commit | SHA |
|---|---|
| Plan-doc finalization commit | `44403a5` |
| Source-edit + audit + allowlist BASELINE | `98f4e1c` |
| Manifest commit | `c40ded9` |
| `loam amend apply` commit | `f8beeaa` |
| `loam amend seal` commit | `0734ea9` |
| §14 backfill commit | (this commit) |
