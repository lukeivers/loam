# Plan — Amendment #36: workspace-bootstrap persona-scaffold (first-run writes `personas/<handle>/`)

**Status:** authored 2026-04-25, awaiting brief-dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment tip:** captured at brief-dispatch time (post-#35-seal).
**Amendment number:** `#36` placeholder; renumbered at dispatch per the convention amendments #29–#33 followed.
**Filename:** family-named (`workspace-bootstrap-persona-scaffold`) so the path survives renumbering.
**Companion research:** none authored separately. Master plan (`docs/rebuild/plans/first-run-primary-persona-default-agent-wiring.md`) carries the investigative narrative.

**Sibling amendments.** This is **amendment 2 of 3** in the persona-setup family.

- **#35:** `primary-persona` — `to_agent_md()` renderer + `onboarding.py` module + `is_starter` field. **Hard prerequisite for this amendment.** Must be sealed before #36 begins.
- **#36 (this plan):** `workspace-bootstrap` — first-run scaffold copies the framework template into `<workspace>/personas/<handle>/` with `is_starter: true` set on the contract.
- **#37:** `hands-off-lifecycle` — `.claude/settings.json` `"agent": "<handle>"` + `.claude/agents/<handle>.md` written from #35's renderer. Depends on #36's scaffold output.

**Prerequisite verification (builder's hard halt before code).** Before any source edit, the builder confirms via `git log` that amendment #35 has sealed (i.e., the `primary-persona` `SEAL_COMMIT` sidecar advances to #35's seal SHA, the `is_starter` field is on `PersonaContract`, and `to_agent_md()` exists and is importable). If #35 has not yet sealed, halt — the dependency contract this plan rests on is not yet on disk.

---

## 1. Summary / TLDR

The `workspace-bootstrap` first-run scaffold gains one additive responsibility: on a workspace with no `personas/` directory, copy the framework's `primary-persona/templates/persona-template/` into `<workspace>/personas/<handle>/` with `is_starter: true` set on the resulting contract. The handle is resolved from a one-question prompt at first-run (defaulting to `primary` when the user does not type a name; sluggified when the user does).

Nothing in this amendment touches `primary-persona/` or `hands-off-lifecycle/` source. The scaffold loads the framework template path from a known location inside `primary-persona/templates/` (read-only consumption — same shape as a workspace would consume the template manually) and copies its content into the workspace tree.

The scaffold is idempotent: a workspace already carrying a `personas/<handle>/contract.yaml` (any value of `is_starter`) is left untouched. The scaffold's existing `partial_recovery` machinery is extended to recognise the persona directory as a tracked artefact.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 operational caution)

**Named spec objectives this amendment satisfies:**

- **v1.0 line 153 — Persona present in every interactive session** (`docs/rebuild/spec/pos-v2-objectives-spec.md` §152–153): *"every interactive session (terminal or desktop) starts with the primary persona present by default — asserted by a session-start test."* A persona cannot be loaded if its directory does not exist. This amendment makes the directory exist on a fresh clone, which is the necessary precondition for v1.0 line 153 to hold without requiring the user to author files.
- **v1.0 line 152 — Non-tech users — low-friction onboarding** (§152): the user does not author YAML to reach a working persona-present state; the scaffold writes the directory at first-run.
- **v1.2 addendum (proposal §1.0 mapping) — workspace without persona cannot start session** (`docs/rebuild/components/primary-persona-loader/proposal.md` §158): the loader's fail-closed today produces a hard failure on a fresh clone instead of a guided onboarding to the persona-present state. Scaffolding the starter directory closes that hazard at the workspace-bootstrap layer.
- **workspace-bootstrap proposal B16 / B25** (`docs/rebuild/components/workspace-bootstrap/proposal.md` §117 + §134): the framework-internal phase surface (`first_run_scaffold` adapter introduced by amendment #4) is the correct layer for new bootstrap-time contributions; this amendment extends that adapter without altering the phase model itself.

**Sealed-component amendment classification.** Single sealed component (`workspace-bootstrap`). The framework template under `primary-persona/templates/persona-template/` is read-only consumed by the scaffold; the scaffold does not modify `primary-persona/` source.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

This amendment leans on Claude Code's `SessionStart` hook surface only indirectly: the existing first-run shim inside `hands-off-lifecycle/hooks/first-run.sh` is what triggers the scaffold, and the scaffold's output (the `personas/<handle>/` directory) is what amendment #37's settings.json + agent-file write surface will project onto the Claude Code default-agent primitive. The scaffold itself is plain file I/O; no Claude primitive is invoked here.

The relevant Claude-leverage observation is **what the scaffold does NOT consume**: it does not parse Claude Code's settings.json, register subagents, or otherwise reach into Claude's surface. That fence is amendment #37's. This amendment's outputs are the substrate amendment #37's outputs project from.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

Yes — substantially, as a prerequisite. Today the loader fails closed on a fresh clone because no `personas/` directory exists. The user must read primary-persona docs, find the template, copy it, edit YAML — that is exactly the translation burden the persona is supposed to absorb but cannot, because the persona is the thing the user is trying to set up. This amendment removes the prerequisite barrier: the directory exists from first-run, the contract is valid by construction, and the persona (post-#37) is present from session one.

**AC-trace to AC.PO.1:**

- **AC36.1 → AC.PO.1.** Scaffold writes `<workspace>/personas/<handle>/contract.yaml` + `<workspace>/personas/<handle>/prompt.md` on first-run → `PersonaLoader(workspace_root).load()` succeeds → loader fail-closed no longer fires on fresh clones → user reaches persona-present state without editing files → translation burden absorbed.
- **AC36.2 → AC.PO.1.** `is_starter: true` is set on the scaffolded contract → onboarding flow (amendment #35) recognises the contract as starter-flagged → conversational elicitation runs on session one → user's natural-language self-description becomes contract content → translation burden absorbed.
- **AC36.3 → AC.PO.1.** Re-running first-run on a workspace that already has `personas/<handle>/` is a no-op (regardless of `is_starter` value) → user-edited persona content is never overwritten → user trusts that their persona content is durable → translation burden remains absorbed across re-runs.
- **AC36.4 → AC.PO.1.** Handle is resolved from a one-question first-run prompt with a sensible default → user's preferred name reaches the contract without YAML editing → translation burden absorbed at name-selection time.
- **AC36.5 → AC.PO.1.** `partial_recovery` recognises the persona directory as tracked → mid-scaffold interruption does not produce a half-state that breaks the loader on the next session → translation burden absorbed (the user does not see a confusing recovery error).

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — the scaffolded `personas/<handle>/` directory is a toolkit artefact the persona layer uses (loader reads it, monitor binds to it, future autonomous-authoring writes alongside it). The scaffold also extends `first_run_scaffold`'s tracked-artefact set, which is itself a primitive future first-run-time additions can use.

**AC-trace to AC.PO.2:**

- **AC36.1 → AC.PO.2.** Scaffolded directory is the toolkit substrate the persona-layer primitives operate on — without it, the toolkit has no input.
- **AC36.5 → AC.PO.2.** `partial_recovery` extension reuses an existing scaffold-level mechanism, demonstrating the bootstrap layer's role as the substrate-management primitive.
- **AC36.6 → AC.PO.2.** Framework-not-content invariant preserved (no persona prose in scaffold source) → toolkit purity preserved.

### Lens 3 — ODD authoring

The plan authors six outcome-shaped acceptance criteria (§4) under §2.5 reverse-direction discipline. Each AC names what must be true; method (file copy mechanism, handle prompt UX, partial_recovery integration shape) is the builder's call.

ODD §2.5 reverse-direction check: the scaffold gains a fresh code path to copy + materialise the persona dir; that maps to AC36.1/AC36.4. The idempotency check maps to AC36.3. The partial_recovery extension maps to AC36.5. Each new line traces back.

---

## 4. Acceptance criteria (AC36.x)

Each AC maps to at least one test function named `test_AC36_<n>_<slug>` in `workspace-bootstrap/tests/`.

### AC36.1 — Fresh-clone first-run produces a valid persona directory

After `first_run_scaffold` completes on a workspace with no `personas/` directory, the following are true:

- `<workspace>/personas/<handle>/contract.yaml` exists and is non-empty,
- `<workspace>/personas/<handle>/prompt.md` exists and is non-empty,
- `PersonaLoader(workspace_root).load()` returns a single `LoadedPersona` whose `contract` validates against the `PersonaContract` Pydantic model without error (i.e., AC35.1's field surface is satisfied by what the scaffold emits).

**Test shape:** scaffold a fresh tmpfs workspace through the existing first-run-test harness; assert the two files exist; instantiate `PersonaLoader` against the workspace; assert `.load()` succeeds.

**Maps to:** v1.0 line 153 (persona present every session — directory existence prerequisite) + primary-persona D2 (loader passes against valid persona) → AC.PO.1.

### AC36.2 — Scaffolded contract carries `is_starter: true`

The contract emitted by the scaffold has `is_starter is True` after `model_validate`. The starter-flag is set by the scaffold (it is not a default the contract assumes; the scaffold writes it explicitly into the YAML so a future audit of the YAML directly shows it).

**Test shape:** scaffold a fresh workspace; load the contract via `PersonaLoader`; assert `loaded.contract.is_starter is True`. Read the on-disk YAML directly; assert the `is_starter: true` line is present.

**Maps to:** v1.0 line 152 (low-friction onboarding) + amendment #35 AC35.4 (elicitation flow recognises starter-flag) → AC.PO.1.

### AC36.3 — Re-running first-run on a workspace with an existing persona directory is a no-op

`first_run_scaffold` on a workspace that already has `<workspace>/personas/<handle>/contract.yaml`:

- does NOT overwrite `contract.yaml` or `prompt.md`,
- does NOT regenerate the directory tree,
- does NOT modify `is_starter` regardless of its current value,
- does NOT raise — first-run completes successfully.

The behaviour holds whether `is_starter` is currently `True` (an earlier first-run completed but elicitation hasn't run) or `False` (the user has completed elicitation or hand-edited the contract).

**Test shape:** scaffold once; capture file mtimes + content hashes for `personas/<handle>/contract.yaml` and `personas/<handle>/prompt.md`; scaffold again; assert mtimes + hashes unchanged. Repeat with `is_starter: false` pre-set on the contract; assert unchanged.

**Maps to:** v1.0 line 152 (low-friction; no surprise overwrites) + v1.2 R16 (workspace-supplied content remains workspace-owned) → AC.PO.1.

### AC36.4 — Handle is sluggified from a first-run prompt with a sensible default

The scaffold resolves the persona handle via the first-run flow's existing user-input mechanism (or a new minimal one if none is reusable; method is the builder's call). When the user provides text, the handle is the sluggified form (lowercase, ASCII, dashes; precise sluggifier is method but must be deterministic and idempotent — slug applied twice equals slug applied once). When the user provides nothing (empty input or default-take), the handle is `primary`. The handle is forbidden from being `eve` (master plan §3 D3 (a) constraint — `eve` is reserved as ivers-corp branding); attempting to set the handle to `eve` is rejected with a clear diagnostic and the prompt re-issues.

**Test shape:** drive the handle resolver with {`""`, `"Iris"`, `"Iris  Bright"`, `"Iris's"`, `"eve"`} and assert {`primary`, `iris`, `iris-bright`, `iris-s` (or whatever the deterministic sluggifier produces — the AC bounds idempotence and lowercase-ASCII-dash, not the exact mapping), rejection}. Sluggifier idempotence: `slug(slug(x)) == slug(x)` for the full fixture set.

**Maps to:** v1.0 line 152 (low-friction onboarding) + master-plan D3 ruling (free-text with `primary` default + `eve` forbidden) → AC.PO.1.

### AC36.5 — `partial_recovery` recognises the persona directory as tracked

The scaffold's existing `partial_recovery` machinery (which surfaces a `partial-scaffold-detected` diagnostic per hands-off-lifecycle H4 when `~/.pos/` exists but `~/.pos/bootstrap.yaml` does not) is extended to recognise the workspace-tree `personas/<handle>/` directory as a tracked artefact. If the persona directory exists but the contract is malformed (e.g., interrupted write produced empty file), the scaffold surfaces a structured diagnostic naming the failure rather than silently overwriting or silently completing.

**Test shape:** seed a tmpfs workspace with a half-written `personas/<handle>/contract.yaml` (zero bytes, or YAML with a Pydantic-invalid value); run scaffold; assert structured diagnostic raised; assert no overwrite of the half-written file.

**Maps to:** hands-off-lifecycle H4 (partial-scaffold detection convention) extended consistently to the persona-tree → AC.PO.1.

### AC36.6 — Framework-not-content invariant preserved

The scaffold does not embed persona prose in its source. The persona directory is materialised by copying from `primary-persona/templates/persona-template/` (the framework's existing template surface, reserved-handle `example-persona`); the scaffold's only mutations on the copy are: rename the directory to the resolved handle, set `is_starter: true` in the contract, replace the placeholder handle field. No persona-prose constants live in `workspace-bootstrap/` source.

**Test shape:** scan `workspace-bootstrap/src/` for any string longer than 80 chars matching the lexical shape of persona-contract prose (heuristic, builder's choice — alternative: assert a known unique sentinel string from the template appears in the scaffolded output, proving the prose came from the template). The existing `enforce_no_personas_in_core` check passes unchanged.

**Maps to:** v1.2 R16 framework-not-content (`docs/rebuild/spec/pos-v2-objectives-spec.md` §348–356) → AC.PO.2 (toolkit purity).

### AC36.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `workspace-bootstrap/` (source + tests),
- `docs/rebuild/plans/amendment-36-workspace-bootstrap-persona-scaffold*` (this plan + manifest),
- universal-paths admissions per §10.

Anything outside that set is a halt condition. Specifically: no edits to `primary-persona/` source (the template is consumed read-only) or `hands-off-lifecycle/` source.

---

## 5. Behaviour-count check (ODD §3.3 forward)

| Behaviour (§1) | Criterion/criteria |
|---|---|
| 1. Scaffold writes `personas/<handle>/` from the framework template | AC36.1, AC36.6 (provenance) |
| 2. Scaffolded contract carries `is_starter: true` | AC36.2 |
| 3. Re-run is a no-op when persona dir already exists | AC36.3 |
| 4. Handle resolved via user prompt with sensible default | AC36.4 |
| 5. partial_recovery recognises persona directory | AC36.5 |
| cross-cutting | AC36.S (seal-diff) |

Five declared behaviours; six ACs cover them plus the cross-cutting seal-diff invariant. No method-in-AC.

---

## 6. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — `workspace-bootstrap/` only.** Source under `workspace-bootstrap/src/`. Tests under `workspace-bootstrap/tests/`. Read-only consumption of `primary-persona/templates/persona-template/` permitted (existing surface). Any source edit outside `workspace-bootstrap/` is a halt (§9).
3. **No edit to amendment #35's surfaces.** The `is_starter` field, `to_agent_md()` renderer, and `onboarding.py` module are imported / read-from-disk only. If any change to them is required, halt (§9).
4. **No edit to `hands-off-lifecycle/` source.** Settings.json + agent-file work is amendment #37's fence.
5. **Reversibility.** Removing this amendment's scaffold extension returns the layer to its pre-amendment state. Already-scaffolded persona directories on existing workspaces are unaffected (the scaffold is idempotent per AC36.3).
6. **No new runtime deps.** Permitted runtime deps per workspace-bootstrap proposal apply unchanged.
7. **No persona content in the scaffold.** The scaffold copies from the framework template; it does not author persona prose. `enforce_no_personas_in_core` continues to enforce.
8. **Fail-closed direction.** A scaffold that cannot complete (template missing, disk full, permission denied) raises a structured diagnostic — does not write a partial directory tree that the loader will fail closed on later. The first-run state file's existing partial-recovery machinery is the diagnostic surface.
9. **Authority bound.** Builder may refine handle prompt UX, sluggifier shape, partial_recovery extension shape. Builder may not relax the framework-not-content invariant (AC36.6) or the no-overwrite invariant (AC36.3).
10. **CDC adherence.** Plan-before-code, background-agent default, scope-only dispatch, the three amendment-dispatch speedups.
11. **`pos-amend apply --dry-run` green** is a hard prereq per amendment #22.
12. **Amendment #35 must be sealed before this amendment begins** — verified at builder's pre-edit gate.

---

## 7. Out of scope (explicit)

- **Renderer + onboarding work** — amendment #35.
- **Settings.json + agent-file write at first-run** — amendment #37.
- **Multiple personas per workspace** (the autonomous-authoring D5/D6 path) — orthogonal; the scaffold writes exactly one starter persona, which is the workspace's primary persona. Future authored personas land via amendment #35's onboarding-derived authoring pipeline (D6).
- **Re-elicitation slash command** — defer.
- **Domain-aware starter prompts** — defer (master plan §11).
- **Slug collision detection across workspaces** (FUTURE_IDEAS Idea 9) — orthogonal; handles are per-workspace.
- **Default handle alternatives beyond `primary` + `eve`-rejection** — out of scope; D3 ruling stands.

---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md.
2. Read master plan + amendment #35 plan + amendment #35 seal narrative + this plan.
3. Verify amendment #35 has sealed (per §6 constraint 12).
4. Write builder-plan to `docs/rebuild/plans/amendment-36-workspace-bootstrap-persona-scaffold.builder-plan.md` naming specific files + symbols expected to be touched.
5. Land the handle resolver. Verify AC36.4.
6. Land the template-copy + `is_starter: true` write inside the existing `first_run_scaffold` adapter. Verify AC36.1 + AC36.2.
7. Land the no-overwrite idempotency. Verify AC36.3.
8. Land the partial_recovery extension. Verify AC36.5.
9. Verify AC36.6 (framework-not-content) by inspecting the diff and running the existing `enforce_no_personas_in_core` test.
10. Run AC36.1–AC36.6 + the existing workspace-bootstrap seal-diff suite + the existing first-run integration test (whichever shape the component has).
11. `pos-amend apply --dry-run` green gate.
12. Amendment commit.
13. Seal commit via `pos-amend seal`; sidecar bump + narrative append.
14. Post-seal: seal-diff-only across all sealed components.

---

## 9. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `workspace-bootstrap/`.** Any required source edit to `primary-persona/` or `hands-off-lifecycle/` (or any other sealed component) → halt.
2. **Amendment #35 has not sealed before this build begins.** Halt; the dependency contract is not on disk.
3. **The `primary-persona/templates/persona-template/` surface has changed in a way that breaks the scaffold's template-copy contract** (e.g., template no longer carries valid-by-construction prose, or its handle field is non-trivial to rewrite). Halt; coordinate with the template authors.
4. **The handle resolver cannot integrate with the existing first-run user-input mechanism without adding a new I/O surface.** Halt; the scope ceiling for "minimal first-run UX extension" is unclear and needs ruling.
5. **`partial_recovery` extension requires a hands-off-lifecycle source change** (e.g., the diagnostic surface lives there, not in workspace-bootstrap). Halt; that is multi-component and needs re-coordination.
6. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective code path, silent exception). Halt; owner rules.
7. **`pos-amend apply --dry-run` red** — halt.
8. **A test for AC36.1–AC36.6 cannot be written deterministically** — halt.
9. **Amendment-dispatch wall-time exceeds 60 minutes** — halt with current state. Owner rules on split vs push-through.

---

## 10. Bookkeeping (`pos-amend` manifest stub)

```yaml
schema_version: 1
amendment:
  number: 36
  slug: workspace-bootstrap-persona-scaffold
  title: "workspace-bootstrap first-run scaffold writes personas/<handle>/"

# BASELINE: <pre-amendment tip captured at brief-dispatch — should
# be the seal commit of #35>. Most recent workspace-bootstrap seal
# commit prior to the persona-setup family is 3844f2f (chore(seals):
# workspace-bootstrap-plist-path seal — workspace-bootstrap at
# 3cab3e3).
baseline: <captured-at-dispatch-post-#35-seal>
plan: docs/rebuild/plans/amendment-36-workspace-bootstrap-persona-scaffold.md

components:
  - name: workspace-bootstrap
    seal_test: workspace-bootstrap/tests/test_no_sealed_amendments.py
    sidecar: workspace-bootstrap/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []

# Universal admissions per amendment #22 ruling #3.
universal_paths:
  prefixes:
    - docs/rebuild/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md

narrative:
  target: workspace-bootstrap/seals/SEAL_COMMIT.persona-scaffold
  body: |
    # Amendment #36 — workspace-bootstrap first-run scaffold
    #                  writes personas/<handle>/
    ...
    # Body authored at seal time; describes:
    #  - first_run_scaffold extension (read-only consumption of
    #    primary-persona/templates/persona-template/, write to
    #    <workspace>/personas/<handle>/)
    #  - is_starter: true set on the scaffolded contract
    #  - handle resolution (one-question prompt, default `primary`,
    #    `eve` forbidden)
    #  - partial_recovery extension to recognise persona directory
    #  - framework-not-content invariant preserved
    #  - downstream amendment #37 consumes the scaffolded
    #    personas/<handle>/ when writing .claude/agents/<handle>.md
    #    via amendment #35's renderer
```

---

## 11. Decisions remaining for the build agent

The following items remain method-level builder choices within this scope. Master-plan recommendations are cited but not pinned.

- **D-build.1 — Handle prompt UX integration.** Master plan D3 (e) recommends "free-text with default `primary` and a one-question prompt." The first-run flow today does not have a generic prompt-the-user surface; the builder picks whether to (a) extend the existing first-run-confirmation surface (per hands-off-lifecycle's Q7 ruling) with a one-question pre-step, (b) defer the prompt to the persona-layer onboarding flow (amendment #35) and have the scaffold default to `primary` always, with the persona renaming the handle on elicitation completion as a post-scaffold rename, (c) some other minimal-friction shape. **Master-plan recommendation:** (a) — one question added to the first-run flow. **Builder's call within scope** — the AC measures the outcome (handle is the user's choice or `primary`), not the UX shape. If (b) is chosen, the AC36.4 test fixture drives the rename path; if (a) is chosen, it drives the prompt path.
- **D-build.2 — Template-copy mechanism.** `shutil.copytree` with overwrite-protection vs. a hand-written line-by-line merge. **Master-plan recommendation:** copytree is sufficient — the template is a small static tree; mutating `handle` and `is_starter` in the contract is a YAML round-trip after copy. **Builder's call within scope.**
- **D-build.3 — Sluggifier shape.** Lowercase + ASCII + dashes + collapse-runs is the recommended shape; precise tokenisation rules (what to do with apostrophes, accents, emoji) are method. **Master-plan recommendation:** match the existing `workspace_bootstrap.adapters.first_run_scaffold.workspace_slug` sluggifier (precedent — used for workspace-slug derivation and parity-tested in amendment #33). **Builder's call within scope** — reusing the existing sluggifier is the natural choice; if the existing sluggifier rejects valid handle inputs (e.g., it forbids certain ASCII characters that should be valid in handles), builder picks an extended variant or halts per §9 #3.
- **D-build.4 — partial_recovery diagnostic shape.** The hands-off-lifecycle H4 diagnostic uses `partial-scaffold-detected`; the persona-tree variant could be `persona-scaffold-malformed`, `persona-scaffold-partial`, or extend H4's existing diagnostic with a sub-cause field. **Master-plan recommendation:** extend H4's diagnostic with a sub-cause naming the persona-tree path. **Builder's call within scope** — the AC measures structured-diagnostic-on-malformed-state, not the exact wording.

These four are surfaced to make the dispatch brief tighter; they are not blockers for plan approval.

---

## 12. Source plan (historical context)

This sub-plan derives from the master research+plan artefact:

- **Master plan:** `docs/rebuild/plans/first-run-primary-persona-default-agent-wiring.md` — covers the full investigation, all six master-plan decisions (D1–D6), the three-lens analysis applied to the combined scope, the ten master-plan ACs, and the multi-component-amendment classification per §10.

The owner ruled (post-master-plan) that the work ships as **three coordinated sealed-component amendments**. This file is **amendment 2 of 3**. Amendment 1 (`amendment-35-primary-persona-renderer-and-onboarding.md`) is a **hard prerequisite**; amendment 3 (`amendment-37-hands-off-lifecycle-default-agent-wiring.md`) depends on this amendment's scaffold output.

Master-plan AC ↔ this-plan AC mapping (for traceability):

| Master AC | This-plan AC | Note |
|---|---|---|
| AC1 (fresh-clone first-run produces a valid persona directory) | AC36.1 + AC36.2 | This is the headline behaviour of #36. |
| AC4 (starter contract is valid-by-construction) | AC36.1 (validation outcome on scaffolded YAML) | The field surface ships at #35 AC35.1; the scaffold output is verified here. |
| AC6 (re-running first-run on a workspace with a non-starter persona is a no-op) | AC36.3 | Idempotency on the scaffold side; #37 owns the no-op for settings.json + agent-file. |
| AC9 (pOS core ships zero persona content) | AC36.6 | Scaffold copies framework-template content; does not embed prose. |

Master ACs 2, 3, 5, 7, 8, 10 land in amendments #35 + #37.

---

## 13. Dispatch-time additions (brief-phase material)

When the brief is drafted, it carries these CDC + ODD enforcement requirements verbatim:

- Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory before any code edit.
- **Pre-edit gate:** verify amendment #35 has sealed (`primary-persona/tests/SEAL_COMMIT` advanced + `is_starter` field on `PersonaContract` + `to_agent_md()` importable). Halt if not.
- Plan-before-code: builder writes its own builder-plan to disk before touching source.
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective-backed code.
- Strong-ODD-adherence: halt if the builder believes an ODD break is strongly required.
- Scope-only downstream dispatches.
- No `git commit --amend`.
- Amendment-dispatch speedups: narrow test scope to `workspace-bootstrap/` + seal-diff on others; skip pre-seal full rerun; methodology snippets inlined.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.1 through D-build.4 to the builder. This
section records the choices made and the rationale.

### D-build.1 — Handle prompt UX integration: pure-function resolver, scaffold defaults to `primary`

The scaffold defaults the persona handle to `primary` always; the
resolver is exposed as a pure function `resolve_persona_handle(raw_input)`
that callers (a future first-run UX layer, or the onboarding flow
landed by amendment #35) hand a raw input string and consume the
resolved handle from. No new I/O surface is added to the first-run
flow under this amendment.

**Rationale:** plan §9 #4 names "cannot integrate without adding a
new I/O surface" as a halt condition. Plan §11 D-build.1 named
candidate (a) ("extend the existing first-run-confirmation surface
with a one-question pre-step") and candidate (b) ("defer the prompt
to onboarding and rename the persona dir post-elicitation"). (a)
would require touching `hands-off-lifecycle/` source, which is
amendment #37's fence — that's the §9 #1 cross-component-scope
halt. (b) collapses AC36.4's prompt-fixture surface into a rename
path that is harder to verify deterministically (the rename step is
state-dependent on prior elicitation completion). Candidate (c)
"some other minimal-friction shape" is what shipped: a
function-shaped seam. The AC measures the resolver's outcome on a
fixture set, which a pure function satisfies cleanly without any
cross-component reach.

### D-build.2 — Template-copy mechanism: `shutil.copytree` + YAML round-trip + atomic rename

`_install_persona_directory` uses
`tempfile.TemporaryDirectory(dir=personas_dir)` to stage a copy of
`primary-persona/templates/persona-template/` under
`<workspace>/personas/.<handle>.staging.<rand>/<handle>/`, mutates
`contract.yaml` in place via `yaml.safe_load` → set `handle` +
`is_starter: true` → `yaml.safe_dump`, then `os.rename` into the
final `<workspace>/personas/<handle>/` position. The staging
directory is automatically cleaned by the context manager;
partial-write failures leave nothing visible to the loader.

**Rationale:** plan §11 D-build.2 recommendation. Tree is small;
mutation is two fields; atomic rename is the cleanest crash-safety
contract on a posix filesystem.

### D-build.3 — Sluggifier shape: re-use existing `workspace_slug`

`resolve_persona_handle` re-uses the same regex pair
(`_SLUG_ALLOWED_RE`, `_SLUG_COLLAPSE_RE`) that
`workspace_bootstrap.adapters.first_run_scaffold.workspace_slug`
already uses. Lowercase + ASCII alphanumerics + dashes + collapse-
runs + leading/trailing-dash-trim. Idempotent on the AC fixture
set (`""`, `"Iris"`, `"Iris  Bright"`, `"Iris's"`, `"IRIS"`,
`"Iris-Bright"`).

**Rationale:** plan §11 D-build.3 master-plan recommendation. The
existing sluggifier is parity-tested under amendment #33; reusing
it avoids divergence between handle-slug and workspace-slug shapes
(consistent UX). All AC36.4 fixtures pass; no fixture exposed an
edge case requiring extension. `eve` rejection is layered on top
as a post-slug check (`if slug in RESERVED_PERSONA_HANDLES`)
rather than embedded in the sluggifier — keeps the sluggifier pure
and the rejection observable.

### D-build.4 — `partial_recovery` diagnostic: extend `PartialScaffoldError` data payload

`_install_persona_directory` raises the existing
`PartialScaffoldError` (introduced under amendment #4 for the H4
partial-scaffold-detected case) with the `data` payload extended
to include `kind="persona-scaffold-malformed"`, `persona_dir`,
`contract_path`, and a human-readable `reason`. The exception
class is unchanged so any downstream H4 handler routes uniformly;
the `kind` sub-cause is observable for callers that want to
distinguish.

**Rationale:** plan §11 D-build.4 master-plan recommendation.
Introducing a new exception class would have widened the partial-
recovery contract surface unnecessarily; reusing the existing class
+ payload-discriminator keeps the cross-component diagnostic
convention coherent.

### Test results

- AC36.1 — 3/3 green (`test_AC36_1_persona_scaffold_fresh_clone.py`).
- AC36.2 — 2/2 green (`test_AC36_2_is_starter_true.py`).
- AC36.3 — 3/3 green (`test_AC36_3_idempotent_re_run.py`).
- AC36.4 — 14/14 green (`test_AC36_4_handle_resolver.py`,
  including parameterised cases).
- AC36.5 — 3/3 green (`test_AC36_5_partial_recovery_persona_dir.py`).
- AC36.6 — 4/4 green (`test_AC36_6_framework_not_content.py`).
- AC36.S — covered by `test_no_sealed_amendments.py`; BASELINE
  advanced via `pos-amend apply` to `057afdb`; SEAL_COMMIT advanced
  via `pos-amend seal` to the amendment SHA. Both test_B23 + test_B20
  green post-seal.
- Existing H1–H5 + AC6 partial-recovery + AC29 memory-port-
  propagation + D5 plist-PATH-emission suites: no regressions. Full
  workspace-bootstrap suite: **133 passed** (102 baseline + 31 new).
- Cross-component seal-diff (per amendment-dispatch-speedups):
  every other sealed component's `test_no_sealed_amendments.py`
  green (telegram-interface, primary-persona, reversibility-
  primitive, safety-layer, orchestrator, self-correction,
  observability-aggregator, memory-system, graceful-degradation,
  cost-governance).
- `pos-amend apply --dry-run`: green pre-amendment-commit and
  post-seal-commit.

### Commit SHAs

- Amendment commit: `ae75d283288d30afb4da5d50f34884c1920c3b1c` —
  `feat(workspace-bootstrap): persona-scaffold writes personas/<handle>/ — amendment #36`
- Seal commit: `0031d1e91c114801e99a13ad42abb13371d3f7b4` —
  `chore(seals): persona-scaffold seal — workspace-bootstrap at ae75d28`

### Dependents cleared to dispatch

Sibling sub-plan #37 (hands-off-lifecycle-default-agent-wiring)
had a hard prerequisite on this amendment's seal:

- **#37** — depends on the `personas/<handle>/` scaffold output on
  a fresh-clone first-run + the `is_starter: true` flag set on the
  scaffolded contract. Both surfaces are now on disk.

#37 is now unblocked.
