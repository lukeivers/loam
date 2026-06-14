# principle-foundation-structural-enforcement — loam's principle foundation becomes named primitives + mechanical enforcement

**Status:** Sub-plan-doc (roadmap §4 Candidate 1). **Class:** MINOR (META-FRAMEWORK) — version derives at release time (`feedback_version_numbers_at_release_time`; do NOT pre-assign).

**Working directory:** `/Users/lukeivers/loam` (canonical loam, `main`).

**Parent / source of truth:** `docs/release-roadmap.md` Candidate 1 (lines 257–303) — objective, the `AC.PFSE.*` family, source items, AI-time, dependencies. This plan honours that AC family verbatim and partitions it into enforceable vs advisory.

**Predecessors (load-bearing prior seals):**
- `f308b398` — Slice-2 doctrine cycle: `primitive_check_guard.py` + `primitive_check_matchers.py` (the two-tier deny/warn PreToolUse guard this plan reuses as the enforcement-shape precedent), the graduated `plugins/loam-skills/` skills, the REQUIRED Primitive-check plan-section convention.
- `f7c1cc29` — seal-guard-sweep-floor: the cross-component guard-floor + repo-local pattern registry (`docs/plans/guard-floor.yaml`) with loud staleness — the precedent for "doctrine → repo-read registry → mechanical check".
- `02a65e2d` — `docs/plans/foundation-revision-rebuild.md` (plan-doc only; the FR.1/FR.2/FR.3 deliverables are NOT yet built — verified: `framework/docs/principles/` does not exist on disk).

**Predecessors (research artefacts consulted at authoring):** the `Explore` sweep recorded in this plan's §11; `docs/design/principle-derivation-map.md` (the canonical map this enforces, at `docs/design/`, NOT `framework/docs/design/` — the roadmap objective's path is stale, corrected here).

**BASELINE candidate:** the plan-doc commit (the commit immediately preceding the first slice's source-edits), per the house pattern. The builder confirms against the predecessor tip at apply time.

**Quality bar:** Anthropic-publish-grade for any new shipped doc (`odd-principles.md`); guard-floor-grade (p95 ≪ 100 ms, fail-open, dev-mode short-circuit, NDJSON audit) for every new hook.

---

## §1 Summary / TL;DR

loam's design principles stop being advisory prose and become **named declarations a checker reads** + **mechanical checks on the production path** for the subset that is genuinely machine-checkable. Drift from an *enforced* principle becomes a hook DENY/WARN, not a discipline ask.

**The load-bearing decision — the enforced-vs-advisory partition (D-PFSE.1).** Not all eight `AC.PFSE.*` are mechanically checkable without an LLM-judge on every action, and an LLM-per-action check collides with the hook-latency budget (the responsiveness work's ~2 ms PreToolUse precedent; an LLM tier needs `claude -p`, seconds not milliseconds). The partition:

| AC | Principle | Enforceable mechanically? | Mechanism |
|---|---|---|---|
| AC.PFSE.1 | FR.1/FR.2/FR.3 named primitives | **YES (presence + manifest)** | Principle declarations land in a machine-read registry (`docs/design/principle-manifest.yaml`) + a checker that reads it; the prose docs (FR.1–FR.3) ship as the human-readable side. |
| AC.PFSE.2 | F6 / M5 four-step conflict resolution | **NO (behavioural) → advisory + arbiter** | Cannot regex "did the agent run the four-step process." Ships as: (a) M5 declared in the manifest; (b) the meta-decision-haiku SKILL (AC.PFSE.8) as the borderline arbiter; (c) template-presence check where a conflict is *recorded*. **HALT-SURFACED — see §3.1 + §10.** |
| AC.PFSE.3 | Four research-question gate | **YES (section presence, non-empty)** | Research-plan template requires all four questions; a gate refuses to advance if any is empty. |
| AC.PFSE.4 | Persona own-behaviour (permission-asking) | **YES (regex on outbound)** | Stop-hook contributor scans the turn's outbound reply for permission-asking patterns → WARN/rewrite-prompt. |
| AC.PFSE.5 | Structural context-load gate | **YES (was-doc-loaded predicate)** | PreToolUse gate: the persona cannot dispatch/author until the relevant design docs are loaded. |
| AC.PFSE.6 | Workspace-slug collision detection | **YES (install/bootstrap check)** | Install-time + bootstrap-time slug-collision check + disambiguation knob. |
| AC.PFSE.7 | Terminology drift detection | **PARTIAL (claim vs git/plan)** | Stop-hook contributor WARNs on dossier-claims that disagree with git log / plan-doc §14 / manifest. |
| AC.PFSE.8 | Meta-decision-haiku SKILL | **YES (the arbiter itself)** | A SKILL invoking Haiku via `claude -p` as impartial third-party for borderline rule-application calls; tightly-scoped trigger list. |

**AC families:** `AC.PFSE.{1..8}` (honoured from the roadmap) plus one outcome-altitude AC `AC.PFSE.2★`-bypass observable (a dispatch/edit that violates an *enforced* declared principle triggers the mechanical check through the production path with no pre-arranged state).

**Key decisions baked (recommendations = law, see §3):** D-PFSE.1 partition (above); D-PFSE.2 the principle-manifest is a NEW machine-read YAML artefact at `docs/design/principle-manifest.yaml` (not the prose map made executable); D-PFSE.3 build a **Stop-hook contributor framework** in `framework/primary-persona/` (one does not exist — the current Stop emitter is single-purpose memory-write); D-PFSE.4 each new hook is a sibling of the proven `primitive_check_guard.py` envelope (two-tier deny/warn, `_gate_helpers` NDJSON audit, dev-mode short-circuit, fail-open); D-PFSE.5 slice the cycle (see §6).

**F2 RF on scope realism (see §10):** this candidate is the largest MINOR in the queue (roadmap: 9–17 h AI-time, midpoint ~13 h, "touches many surfaces"). Authoring it as a single seal is not realistic and not safe. The plan partitions into **four ordered slices**, each its own seal; the build dispatches them serially (`feedback_serialize_amendment_builds` — same tree). Treating the eight ACs as one cycle would violate the swarming stopping criterion (each slice has a strictly tighter AC than the parent) and risk a giant un-reviewable seal-diff.

---

## §2 Placement decisions

| Item | Placement | Rationale |
|---|---|---|
| Principle prose (FR.1 `odd-principles.md`, FR.2 methodology re-author, FR.3 CLAUDE.md Lens consolidation) | `framework/docs/principles/` (NEW, unsealed) + `plugins/dev-sdlc/docs/` (FR.2/FR.3 re-author, **sealed dev-sdlc fence**) + `CLAUDE.md` (universal) | Per `foundation-revision-rebuild.md` §3 — the one sealed fence FR.1–3 touches is `plugins/dev-sdlc/`. FR.1's new dir is universal-paths admission. |
| Principle-manifest (machine-read) | `docs/design/principle-manifest.yaml` (NEW, universal-paths) | Deliberately in universally-admitted space (the guard-floor-registry precedent, `f7c1cc29`) so future principle-row edits never breach a fence. |
| Principle-manifest checker | `plugins/dev-sdlc/hooks/` (the guard family home) | Same envelope as the five existing dev-sdlc guards; reuses `_gate_helpers`. |
| Four-question research-plan gate | `plugins/dev-sdlc/` (template + gate) | Research-plan template + the plan-advance gate are dev-discipline; dev-sdlc is their home. |
| Stop-hook contributor framework + permission-ask contributor + terminology-drift contributor | `framework/primary-persona/src/loam/primary_persona/` | The Stop CLI (`stop_emitter.py`, `cli stop`) lives here; the contributor framework extends it. Persona own-behaviour is a primary-persona concern. |
| Context-load gate | `plugins/dev-sdlc/hooks/` (PreToolUse) wired via `framework/hands-off-lifecycle/hooks/first_run_settings.py` | PreToolUse guard sibling; wired into bootstrapped workspaces by the A4 marker+stanza precedent. |
| Slug-collision detection | `framework/workspace-bootstrap/` + install path | Install/bootstrap-time check belongs with the bootstrap machinery. |
| meta-decision-haiku SKILL | `plugins/loam-skills/skills/meta-decision-haiku/` (dir exists, no SKILL.md — per the lsk1 ruling) | Authoring the SKILL.md fills the planned-not-yet-packaged slot; invokes Haiku via the `claude -p` client (no API key). |

---

## §3 Halt-and-surface BEFORE build (recorded + ruled at plan-authoring)

These are autonomous rulings I recorded; the builder respects them as gates, not re-litigations.

### 3.1 — D-PFSE.1 — the enforced-vs-advisory partition (RULING; the load-bearing call)

**Ruling:** AC.PFSE.{1,3,4,5,6,7,8} ship as mechanical enforcement; **AC.PFSE.2 (F6/M5 four-step conflict resolution) does NOT ship as a behavioural check** — it is genuinely not mechanically verifiable without an LLM-judge on every conflict, and that collides with the hook-latency budget. **HALT-SURFACED to dispatcher (§10 RF-1).** AC.PFSE.2 is instead satisfied by: (a) M5 declared as a row in the principle-manifest (named primitive — meets "declared in code, not prose-only"); (b) the meta-decision-haiku SKILL (AC.PFSE.8) standing as the borderline-arbiter that operationalises "is this a conflict that needs the four-step process?"; (c) a template-presence check that a *recorded* conflict (in a plan §16 or a decision-ledger entry) carries the four named steps. The behavioural act of running M5 in-head stays advisory. **Evidence:** the four-step process is "name conflict / name signals / make call / surface if non-obvious" — steps 1–3 are interior cognition with no observable artefact unless the agent chooses to write one; only step 4 (surface) has an artefact, and that artefact is already covered by F2 surfacing. Test of method-in-AC passed: the AC "M5 is a named primitive" can be satisfied by a manifest row OR a SKILL OR a template — method stays open.

### 3.2 — D-PFSE.2 — principle-manifest is a NEW machine-read artefact, not the prose map made executable (RULING)

**Ruling:** ship `docs/design/principle-manifest.yaml` (schema: `{id, name, memory_basename, enforcement: enforced|advisory|partial, mechanism, f4_relationship}`) as the machine-read declaration surface. The existing `docs/design/principle-derivation-map.md` (prose) stays as the human-readable companion and gains a one-line pointer to the manifest. **Evidence:** the derivation-map is a Markdown table tuned for human reading + M5 lookup; parsing Markdown tables for enforcement is brittle, and the map explicitly disclaims being an "override list." A purpose-built YAML is the durable machine surface; a checker reads YAML, never the prose. A bidirectional coverage guard (the `primitive_check_matchers` precedent) keeps manifest ↔ map drift observable — a map row without a manifest row turns the suite red.

### 3.3 — D-PFSE.3 — build a Stop-hook contributor framework (RULING; named scope-add)

**Ruling:** AC.PFSE.{4,7} both say "Stop-hook contributor." **Verified at authoring: no general contributor framework exists** — `stop_emitter.py`'s `cli stop` is single-purpose (parse envelope → detached memory-write), and the Stop-hook contract requires rc=0-always + fast-return. The framework to build: a registry of contributors each given the turn's outbound text + workspace context, each returning an optional `systemMessage` / advisory line, composed into the Stop output without breaking the rc=0-always + fail-soft contract. AC.PFSE.4 (permission-ask) + AC.PFSE.7 (terminology-drift) are the first two contributors. **Evidence:** `stop_emitter.py:478` `cli_stop` catches every exception and returns 0; the contributor framework must preserve that. This is a real scope-add over "attach a contributor" — surfaced (§10 RF-2) but ruled in-scope because both ACs name the surface and it cannot be skipped.

### 3.4 — D-PFSE.4 — every new hook is a `primitive_check_guard.py` sibling (RULING)

**Ruling:** the manifest-checker, the context-load gate, and any PreToolUse leg reuse the proven envelope: two-tier deny/warn posture, `_gate_helpers.append_audit_line` NDJSON audit, `_gate_helpers.read_workspace_mode_or_normal_use` dev-mode short-circuit, fail-open-on-error (rc=0). No new observability mechanism, no new audit format. **Evidence:** `f308b398` shipped this envelope; `_gate_helpers` exports `is_carve_out_path / read_workspace_mode_or_normal_use / append_audit_line / now_iso_z` (verified). Matcher-data rows each name their source entry → the coverage guard makes drift observable.

### 3.5 — D-PFSE.5 — slice the cycle into four ordered seals (RULING; see §6)

**Ruling:** Slice A (principle-manifest + checker + FR.1 prose) → Slice B (research-question gate + context-load gate) → Slice C (Stop-hook contributor framework + permission-ask + terminology-drift contributors) → Slice D (slug-collision + meta-decision-haiku SKILL). FR.2/FR.3 (the sealed dev-sdlc methodology re-author) ride with Slice A or land as a sub-seal within it (builder's call; same fence). **Evidence:** `feedback_serialize_amendment_builds` (one tree, no parallel builds) + the swarming stopping criterion (each slice's AC strictly tighter than the parent). A single seal across all eight ACs is an un-reviewable diff.

### 3.6 — no-API-key gate (RECORDED)

No mechanism here touches the Anthropic API directly. The meta-decision-haiku SKILL invokes Haiku **only** via `claude -p` (the `claude_print_synthesis_client.py` / `claude_print_client.py` subscription path — `feedback_no_anthropic_api_key`). Every other check is deterministic regex/YAML/git-read.

---

## §4 Spec-objective placement

Binds to roadmap §4 Candidate 1 objective (docs/release-roadmap.md:263). Ladders up to **AC.PO.1 (harness test)** + **AC.PO.2 (primary-persona test)** in `docs/VALUE_PROPOSITION.md` (`feedback_value_proposition_as_prime_objective`): structural enforcement of the principle foundation *adds to the toolkit the primary persona draws from* (harness test — new guards + contributor framework + arbiter SKILL) and *reduces translation burden* (primary-persona test — the persona no longer carries the principle corpus as fragile in-context discipline; drift is caught mechanically). This is the structural-enforcement substrate — `feedback_structural_enforcement_on_recurrence` applied to the principle system itself ("a rule violated more than once despite being in the corpus → the fix is a hook, not another memory rule").

---

## §5 Acceptance criteria

AC IDs scope-descriptive (`AC.PFSE.*`), honoured from the roadmap. Each outcome-shape; method-in-AC test passed (each can be met by ≥1 method other than any I have in mind).

| AC | Outcome (NOT method) | Verification surface |
|---|---|---|
| **AC.PFSE.1** | The three frame-rules FR.1/FR.2/FR.3 are declared as machine-read named primitives (a checker can enumerate them from a code-side artefact), not documents-only. | A test reads the principle-manifest and asserts FR.1/FR.2/FR.3 (and M5) are present as rows with an `enforcement` field; the prose docs exist and cross-reference the manifest. |
| **AC.PFSE.2** | M5 (the lens-conflict four-step process) is a named primitive with a structural surface; the borderline-conflict arbiter exists. **Behavioural enforcement explicitly out (§3.1).** | Manifest row for M5 with `enforcement: advisory`; the meta-decision-haiku SKILL present + invocable; a recorded-conflict template carries the four named steps. |
| **AC.PFSE.3** | A research-plan that omits any of the four research questions cannot advance — the gate refuses. | A research-plan fixture missing one question is rejected by the gate through its production entry-point; a complete one passes. |
| **AC.PFSE.4** | An outbound reply containing a permission-asking pattern on authorized work is caught (warned/flagged for rewrite) by a Stop-hook contributor. | The contributor, given a turn whose reply says "want me to X?" on authorized work, emits the rewrite/flag; a clean reply emits nothing. |
| **AC.PFSE.5** | The persona cannot dispatch/author work until the relevant design docs are loaded — the gate blocks otherwise. | A dispatch attempted without the required docs loaded is blocked by the gate through the production path; with them loaded, it proceeds. |
| **AC.PFSE.6** | Two workspaces colliding on the same slug are detected at install + bootstrap time, with a disambiguation knob available. | A bootstrap against a colliding slug raises the collision + the disambiguation path resolves it. |
| **AC.PFSE.7** | A dossier/narrative claim that disagrees with git log / plan-doc §14 / manifest is warned by a Stop-hook contributor. | The contributor, given a claim contradicting a git-log fact, emits the drift warning; a consistent claim emits nothing. |
| **AC.PFSE.8** | A SKILL invokes Haiku (subscription path, no API key) as an impartial arbiter for a tightly-scoped borderline-rule list, returning a decision. | The SKILL, invoked on a borderline case (e.g. plan-doc-needed?), produces a Haiku-arbitrated verdict via `claude -p`; trigger list is bounded (no death-by-latency). |
| **AC.PFSE.2★** *(outcome-altitude)* | A dispatch/edit that violates an **enforced declared principle** triggers the observable mechanical check through the production hook path, with no pre-arranged state. | A real subprocess fire (venv interpreter, real dev-mode contract, stdin envelope) of an enforced-principle violation → deny/warn payload + NDJSON audit line on disk; no fixture state seeded. (`feedback_test_outcome_altitude_required`.) |

---

## §6 Build steps (per-slice; method-level guidance only — builder's call per ODD §1.1)

Four ordered seals, serial in one tree. Each slice: own manifest section, source edits, AC-scoped tests, `loam amend apply`, `loam amend seal`, pre-seal guard-floor ride-along (the `f7c1cc29` lesson).

- **Slice A — declaration substrate (AC.PFSE.1, AC.PFSE.2-manifest-leg).** Author `docs/design/principle-manifest.yaml` + the dev-sdlc manifest-checker (sibling guard) + the bidirectional manifest↔map coverage guard. FR.1 (`framework/docs/principles/odd-principles.md`) + FR.2/FR.3 (dev-sdlc methodology re-author + CLAUDE.md Lens consolidation) ride here or as a sub-seal — the one sealed fence is `plugins/dev-sdlc/`.
- **Slice B — research-question gate + context-load gate (AC.PFSE.3, AC.PFSE.5).** Research-plan template gains the four required questions + a gate that refuses on any empty. PreToolUse context-load gate (sibling guard) + first_run_settings wiring.
- **Slice C — Stop-hook contributor framework (AC.PFSE.4, AC.PFSE.7, AC.PFSE.2★).** Build the contributor framework in `framework/primary-persona/` (preserving rc=0-always + fail-soft); land permission-ask + terminology-drift as the first two contributors. The outcome-altitude fire lands here.
- **Slice D — slug-collision + arbiter SKILL (AC.PFSE.6, AC.PFSE.8).** Slug-collision check at install/bootstrap + disambiguation knob; author `meta-decision-haiku/SKILL.md` with a bounded trigger list invoking Haiku via `claude -p`.

Each slice's manifest names the seal_test + sidecar for its touched components and confirms the global counter at apply time (`feedback_version_numbers_at_release_time`).

---

## Primitive check (REQUIRED — Slice-2 D-DOC.3 convention)

Native Claude / Claude Code primitives considered for each new mechanism:

- **Principle declarations → a machine-read YAML registry + a checker.** Not CLAUDE.md prose (doctrine-as-text already failed — `feedback_structural_enforcement_on_recurrence`), not the Markdown map made executable (brittle parse). A repo-local registry is the `f7c1cc29` guard-floor precedent.
- **Manifest-checker / context-load gate → Claude Code PreToolUse hook.** Native hook event; sibling of `primitive_check_guard.py`. Alternatives considered + rejected in-cycle: `prompt`/`agent` LLM-judge hook handlers (fire-path latency + subscription-only) — named as the explicit OUT for the behavioural M5 check (§3.1).
- **Persona own-behaviour + terminology-drift → Claude Code Stop hook (contributor framework on top of the existing `cli stop`).** Native Stop event; extends `stop_emitter.py`. Not a memory rule (own-behaviour failures already recur 4+ times per Idea 21).
- **Research-question gate → plan-template + a deterministic section-presence gate.** No LLM; section-presence is regex/parse.
- **Borderline arbiter → a SKILL invoking Haiku via `claude -p`.** Auto-discoverable SKILL (Lens 1); the `claude_print_client` subscription path (no API key). The ONE place an LLM is in the loop — deliberately, and scoped to a bounded borderline-call trigger list, off the per-action hot path.
- **Audit trail → the existing `_gate_helpers` NDJSON pattern.** No new observability mechanism.
- **Slug-collision → install/bootstrap-time deterministic check.** No primitive needed beyond the existing bootstrap path.

---

## §7 Out of scope

- **Behavioural verification of M5 four-step in-head** — out by §3.1 ruling (LLM-per-action collides with the latency budget); M5 ships as a named manifest primitive + arbiter SKILL + recorded-conflict template only.
- **Runtime/persona-path enforcement for NORMAL-USE workspaces** — the PreToolUse/Stop legs land on the dev-mode dispatch path first; the NORMAL-USE persona-path port is a named follow-on (mirrors the Slice-2 master §7.2 split).
- **Installer onboarding for principles-distribution (D9 universal-vs-local install)** — `foundation-revision-rebuild.md` §D9 names it a separate future feature; not pulled in here.
- **Publish** — LOCAL only; owner gates publish (`feedback_build_forward_on_publish_pending`).

---

## §8 Halt triggers (in-flight; abort the build + surface)

1. The Stop-hook contributor framework cannot be added without breaking the rc=0-always / fail-soft Stop contract (`stop_emitter.py:478`) → halt; the contract is non-negotiable.
2. The context-load gate (AC.PFSE.5) would require an LLM to decide "is THIS doc relevant" rather than a deterministic loaded-set predicate → halt (collides with the §3.1 latency ruling; re-scope to an explicit required-doc-set check).
3. Any slice's seal-diff exceeds reviewable size or its AC is not strictly tighter than the parent → halt; re-slice (swarming stopping criterion).
4. FR.2/FR.3 re-author would change the *meaning* of a Lens rather than enforce it as written → halt (the dispatch's own halt-and-surface: "scope that would edit the Lenses' meaning").
5. An enforced check would need to fire an LLM on every action → halt + surface the latency cost (the dispatch's primary halt trigger).

---

## §9 Bookkeeping

- `docs/STATE.md` — append a dated entry per sealed slice (the per-minor convention).
- `docs/release-roadmap.md` Candidate-1 row — mark slices SHIPPED-LOCAL as they seal; the candidate closes when Slice D seals.
- `docs/design/principle-derivation-map.md` — add the one-line pointer to the new `principle-manifest.yaml` (Slice A).
- Each slice's plan §14 register backfilled at seal via `loam amend seal --plan-doc`.

---

## §10 F2 Ruthless Feedback (honest doubts; named design risks)

- **RF-1 (the load-bearing surface). The roadmap implies AC.PFSE.2 must become a Stop-hook contributor that enforces the four-step conflict process; I am ruling it CANNOT be behaviourally enforced without an LLM-per-action judge.** Evidence: M5's steps 1–3 are interior cognition with no observable artefact; only step 4 (surface) is observable, and F2 already covers surfacing. Alternative (the ruling): M5 ships as a named manifest primitive + the meta-decision-haiku arbiter + a recorded-conflict template. **This is the one place my plan deviates from a literal reading of the AC, and the dispatch named exactly this halt trigger ("a principle… genuinely not mechanically checkable without an LLM-judge on every action"). Dispatcher should confirm the partition before Slice C builds.**
- **RF-2. The "Stop-hook contributor" surface the roadmap assumes already exists does not** — the current Stop emitter is single-purpose memory-write. AC.PFSE.{4,7} therefore carry a real framework-build cost (Slice C), not a thin attach. Evidence: `stop_emitter.py` `cli_stop`/`handle_stop_envelope` have no contributor registry. Alternative: build the framework once in Slice C; the two contributors are cheap on top. Surfaced so the AI-time for Slice C is not under-counted.
- **RF-3. Scope realism.** Roadmap's own estimate is 9–17 h AI-time, "largest MINOR in the queue." Four slices is the right decomposition, but the dispatcher should expect four serial seals, not one. A single-seal attempt risks an un-reviewable diff and a serialize-amendment-builds violation.
- **RF-4. The principle-manifest is a second declaration surface alongside the prose map** — a drift risk. Mitigation baked: the bidirectional coverage guard (manifest ↔ map) turns drift red, exactly as `primitive_check_matchers` does for corpus ↔ check. Without that guard, RF-4 would be a real objection.

---

## §11 Provenance trail

- `docs/release-roadmap.md:257-303` — Candidate 1 block (objective, `AC.PFSE.*` family, source items, AI-time, dependencies). Source of truth for scope.
- `docs/design/principle-derivation-map.md` — the canonical principle map (at `docs/design/`; the roadmap objective's `framework/docs/design/` path is **stale** — corrected throughout this plan).
- `docs/plans/foundation-revision-rebuild.md:95-160` — FR.1/FR.2/FR.3 explicit deliverables (odd-principles.md NEW; methodology + project-bridge re-author under the `plugins/dev-sdlc/` fence; CLAUDE.md Lens consolidation). Verified `framework/docs/principles/` does NOT exist → FR.1–3 unbuilt.
- `plugins/dev-sdlc/hooks/primitive_check_guard.py` + `primitive_check_matchers.py` (seal `f308b398`) — the two-tier deny/warn envelope + matcher-data + bidirectional coverage guard this plan reuses.
- `framework/hands-off-lifecycle/hooks/_gate_helpers.py` — exports `is_carve_out_path / workspace_relative / read_workspace_mode_or_normal_use / append_audit_line / now_iso_z` (verified line refs 135/156/185/266/300).
- `framework/primary-persona/src/loam/primary_persona/stop_emitter.py:478` — `cli_stop` rc=0-always fail-soft contract; the surface the contributor framework extends. No contributor registry exists today (verified).
- `docs/plans/sealed/seal-guard-sweep-floor.manifest.yaml` (seal `f7c1cc29`) — schema-v3 manifest shape (slug-identified, no number pre-allocation) + repo-local registry-in-universal-paths precedent.
- `plugins/dev-sdlc/docs/conventions/plan-docs.md` — plan-doc shape + the REQUIRED Primitive-check section convention (Slice-2 D-DOC.3).
- `feedback_structural_enforcement_on_recurrence` — the doctrinal basis (hooks over memory rules); this candidate is that pattern applied to the principle foundation itself.
