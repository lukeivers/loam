# SLICE 1a — SubagentStart auto-context handoff (the IN-handoff)

> **Status:** sub-plan-doc (loam-realignment SLICE 1a — the keystone's IN-handoff half).
> **WD:** `/Users/lukeivers/loam` (canonical loam product repo).
> **Parent plan:** `docs/plans/` predecessor pair — the SPINE (`loam-realignment-SPINE-and-PLAN-2026-06-08.md`, Part II.B slice 1) + the integrated design (`loam-frame-robustness-INTEGRATED-DESIGN-and-EVAL-PLAN-2026-06-08.md`, §2 K/P, §3 three-role, §8 SubagentStart push-down). Both currently live in pos3's plan tree (`/Users/lukeivers/pos3/docs/plans/`); this sub-plan is the canonical-loam build artefact derived from them.
> **Predecessors (load-bearing prior seals):** the `corpus-inlining-session-start-hook` amendment (#73) — the additionalContext-via-stdout injector pattern this build mirrors (`framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py`); the `keep-pace KP0` fragment model (`framework/hands-off-lifecycle/hooks/keep_pace/settings.fragment.json`) — the settings-fragment shape; `memory_consumer.py` (`framework/primary-persona/src/loam/primary_persona/memory_consumer.py`) — the `search(query, group_ids=[workspace_slug])` memory-retrieval interface this build composes the bundle's memory tier on.
> **BASELINE candidate:** the source-edit commit (backfilled post-source-edit per v0.10.x precedent; manifest carries the placeholder).
> **Status-file target:** `docs/STATE.md` (rollup) + `docs/release-roadmap.md` (slice tracking).
> **Quality bar:** outcome-altitude AC verified via a REAL subagent dispatch receiving the bundle (production entry-point, no pre-arranged state).

---

## §1 Summary / TL;DR

**What ships.** A `SubagentStart` hook that injects a single `additionalContext` bundle into every dispatched subagent's context, carrying three tiers: (a) the always-on **MICROKERNEL** — the prime directive (per-user translation) + the three-role identity (runtime / platform / product) + the protection floor + "pause if you lose your place," authored as **if-then implementation intentions**; (b) the **active workstream context**; (c) the **relevant memory**. Registered via a `settings.fragment.json` so it ships to ANY loam workspace through the existing fragment-composition path. This extends loam's governance from the human→persona boundary (where every governance hook fires today) DOWN to the persona→subagent boundary, lifts the currently-unused `SubagentStart` primitive, and retires the hand-written principle/context propagation block that every dispatch brief copies by hand today.

**AC families.** `AC.SACH.*` (Subagent Auto-Context Handoff) — bundle composition + tier presence + if-then microkernel form + fragment registration + fail-soft + the outcome-altitude real-dispatch probe.

**Key decisions baked (recommendations in §3; all autonomous, none owner-gated).** (1) New component `frame-kernel` housing the microkernel file + the hook. (2) Microkernel authored as if-then intentions in a version-pinned `kernel/loam-microkernel.md`. (3) "Active workstream context" resolves to the current workstream STATE; project-keying is **stubbed to "current workstream" for 1a**, pending the separate project-summary work (slice S). (4) Memory selected by reusing the existing `memory_consumer.search(query, group_ids=[workspace_slug])` path, seeded with the dispatch's task text as the query. (5) Fragment registered following the keep-pace `settings.fragment.json` shape; the SubagentStart matcher block is the unit.

**F2 RF on scope realism (full §10).** The natural shape needs a NEW component plus a fragment — it does not fit one file, and the plan says so (§2). The fragment-composition path in canonical loam is **hand-merge today** (keep-pace's own fragment is gated/hand-merged, NOT auto-composed by workspace-sync) — so "ships to ANY loam workspace" is true of the FRAGMENT ARTEFACT (it's the portable declaration), but the live-activation merge is a separate gated step exactly as keep-pace's is. The plan does not claim auto-propagation that the code does not yet do (§10 RF-1).

---

## §2 Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| Microkernel content | `kernel/loam-microkernel.md` (NEW top-level dir, owned by the new `frame-kernel` component) | The integrated design §2-K names this exact path. It is the Trusted Computing Base — tiny, version-pinned, identical for every user. A top-level `kernel/` makes it findable + signals its TCB status; it is NOT buried inside an existing component's `src/`. |
| SubagentStart hook | `framework/frame-kernel/hooks/subagent_start_context.py` | New component. The hook is the keystone of the whole realignment (slices 2-6 build on it); it is NOT a natural sub-feature of `hands-off-lifecycle` (lifecycle = session/first-run) or `primary-persona` (persona = the human→persona turn surface). A dedicated component keeps the three-role TCB cohesive + gives slice 1b (SubagentStop frame-check) a home. |
| `settings.fragment.json` | `framework/frame-kernel/hooks/settings.fragment.json` | Mirrors keep-pace's `framework/hands-off-lifecycle/hooks/keep_pace/settings.fragment.json` location convention (fragment sits beside the hook it registers). |
| Tests | `framework/frame-kernel/tests/` | New component's own test surface; seal anchor binds here. |
| Plan + manifest | `docs/plans/frame-kernel-subagent-context-handoff-1a.{md,manifest.yaml}` | loam plan convention (`docs/plans/<slug>.md` + paired manifest). |

**FENCE — RECOMMENDATION (named decision D-SACH.1):** a NEW `frame-kernel` component. NOT an extension of `primary-persona` or `hands-off-lifecycle`. Recommended because: (1) the realignment's slices 1b/4/5/6 all hang off this surface — a dedicated component is the natural home for the growing frame-robustness machinery; (2) the microkernel is a TCB and deserves an isolation boundary (its own seal_test, its own fence) rather than entangling with persona-turn or session-lifecycle code; (3) extending an existing sealed component would widen that component's fence for a function orthogonal to its charter. The cost is one new component's scaffolding (pyproject + tests dir + seal sidecar) — small, and the realignment amortizes it across five downstream slices.

---

## §3 Halt-and-surface BEFORE build (named decisions, recorded + recommended)

All five decisions below are **autonomous** (method-level, in-scope per the dispatch). Each carries a recommendation; none is owner-gated. Recorded here so the builder does not re-derive.

**D-SACH.1 — Component placement + fragment registration.**
*Recommendation:* NEW `frame-kernel` component (rationale in §2). Fragment registered as a `settings.fragment.json` beside the hook, declaring a `SubagentStart` matcher block whose `command` invokes the hook under the workspace venv Python (`${LOAM_REPO}/.venv/bin/python …/subagent_start_context.py`), mirroring the keep-pace fragment's `${LOAM_REPO}` placeholder + `timeout` shape. The fragment is the portable declaration; live merge into a workspace's `.claude/settings.json` is the same gated hand-merge step keep-pace uses (RF-1).

**D-SACH.2 — Microkernel content + if-then format.**
*Recommendation:* `kernel/loam-microkernel.md`, ~10 lines, version-pinned (a `version:` line in the file), identical for every user. Content = prime directive (per-user translation) + three-role identity (runtime / platform / product, per integrated-design §3) + protection floor + "pause if you lose your place." Each line authored as an if-then implementation intention ("IF about to assert something is broken, THEN verify first"), per Gollwitzer & Sheeran 2006 — the flat declarative form is the present-but-non-governing form goal-neglect predicts fails (integrated-design §2-K). The hook reads this file and emits its content verbatim as the bundle's first tier — content lives in the doc, not hardcoded in the hook (mirrors `corpus_inline_session_start.py`'s file-read pattern, so editing the kernel doesn't require a code change).

**D-SACH.3 — What "active workstream context" resolves to + project-keying scope.**
*Recommendation:* For 1a, resolve to the **current workstream STATE** (the work-streams register, #70/#84, already live). **Project-keying is STUBBED to "current workstream" for 1a** — full project-keyed selective loading (the `P` layer, integrated-design §2-P) is the separate project-summary work (SPINE slice S / slice 2's SKILL `paths:` wiring) and is explicitly OUT OF SCOPE here (§7). This keeps 1a bounded to the IN-handoff mechanism; the bundle carries a workstream-context tier whose RESOLVER is a stub that slice S replaces, but whose PRESENCE in the bundle is asserted now so the bundle shape is stable for downstream slices.

**D-SACH.4 — How relevant memory is selected for the bundle.**
*Recommendation:* REUSE the existing `memory_consumer` retrieval path — `memory_client.search(query=<dispatch task text>, group_ids=[workspace_slug])`, gather top-N, same as the live UserPromptSubmit memory-retrieval contributor. The query seed is the subagent's task/brief text (available in the SubagentStart envelope). NOT a new retrieval mechanism (Lens 1 — compose on the existing memory half loam already demand-pages). Augmenting the query with a project/workstream key is the `P`-layer delta and is OUT OF SCOPE for 1a (§7).

**D-SACH.5 — Bundle output envelope.**
*Recommendation:* Emit `hookSpecificOutput.additionalContext` as a JSON envelope (matching `principle_reminder.py`'s proven `{"hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext": <bundle>}}` shape) — NOT bare stdout. Rationale: the feature-awareness catalogue names `additionalContext` specifically as a field "in `hookSpecificOutput`"; the JSON-envelope form is the documented contract for subagent-targeted injection and the existing in-repo precedent (`principle_reminder.py`) uses it. The bundle is the three tiers concatenated under delimiter headers (mirrors `corpus_inline_session_start.py`'s `--- <name> ---` block format).

---

## §4 Spec-objective placement (ladder-up)

- Binds to **AC.PO.1 + AC.PO.2** (the prime objective in `docs/VALUE_PROPOSITION.md` — per-user-tuned translation + protection floor).
- The microkernel tier IS the prime directive made resident in every subagent's context → directly serves AC.PO.1 (translation) by carrying the per-user-translation charter DOWN to the subagent boundary, and AC.PO.2 (protection) by carrying the protection floor down.
- Ladders up through the realignment SPINE's slice-1 keystone objective ("close the governance asymmetry — governance must run at persona→subagent, not only human→persona") → the integrated design's R1 (core always in context) at the subagent boundary.

---

## §5 Acceptance criteria (AC.SACH.* — outcome-shaped; method-in-AC test passed on each)

| AC | Outcome (what is observably true) | Verification |
|---|---|---|
| **AC.SACH.1** | When a subagent is dispatched, its received context contains the microkernel content (prime directive + three-role identity + protection floor + pause-if-lost). | A test invokes the production hook entry-point with a SubagentStart envelope; the emitted `additionalContext` is asserted to contain each of the four microkernel elements. |
| **AC.SACH.2** | The microkernel content the bundle carries is in if-then implementation-intention form, not flat-declarative. | A test asserts the kernel-file lines (and thus the bundle's microkernel tier) match the if-then shape (each governing line has an antecedent + consequent); a flat-declarative line is a failure. |
| **AC.SACH.3** | The bundle carries a workstream-context tier reflecting the current workstream, and a memory tier reflecting workspace-scoped relevant memory. | A test dispatches with a known active workstream + known memory state and asserts both tiers are present + reflect that state (the workstream tier names the current workstream; the memory tier carries ≥0 retrieved entries from the workspace-scoped store, present as a tier even when empty). |
| **AC.SACH.4** | The hook never aborts a subagent dispatch: any internal error (missing kernel file, memory backend down, malformed envelope) still lets the subagent start. | A test feeds each degenerate input (absent kernel file, unreadable, malformed/empty envelope, memory error) and asserts the hook exits cleanly with the dispatch un-blocked (the bundle degrades — a `[missing]`-style marker — but never raises). |
| **AC.SACH.5** | The hook is registered for `SubagentStart` via a portable settings-fragment that any loam workspace can compose, with no per-workspace hand-authoring of the registration. | A test asserts the `settings.fragment.json` declares a `SubagentStart` matcher block invoking the hook, with the `${LOAM_REPO}` placeholder + venv-python command shape (parse the fragment + assert the event + command target). |
| **AC.SACH.S (outcome-altitude)** | A REAL subagent dispatch — through the production dispatch entry-point, with no pre-arranged in-test bundle — receives the microkernel in its context. | An outcome-altitude probe dispatches an actual subagent whose task is to report back the first lines of its own injected context; the returned report is asserted to contain the microkernel's prime-directive marker. Marked `outcome-altitude: true`. No STUB-class test satisfies this AC. |

**Method-in-AC test (run on each AC).** Each AC above states WHAT is observably true (microkernel present, if-then form, tiers present, fail-soft, fragment-registered, real-dispatch-receives), never HOW. Example check on AC.SACH.1: could it be satisfied by a method other than the one I have in mind (file-read + JSON-envelope emit)? YES — a hardcoded-string hook, a different injection field, an MCP-tool hook all satisfy "received context contains the microkernel content." Therefore AC.SACH.1 is outcome-shape, not method-in-AC. AC.SACH.5 names "portable settings-fragment" as the OUTCOME (workspace can compose without hand-authoring), not the file format as method — a different portable-registration mechanism that met the no-hand-authoring outcome would pass; the fragment is the recommended method, inferable from the constraint, not stated as the contract.

---

## §6 Build steps (method-level guidance only — builder's call per ODD §1.1)

Per-cycle shape (single component, single amendment):

1. **Manifest:** `docs/plans/frame-kernel-subagent-context-handoff-1a.manifest.yaml` (paired; shape per §11-manifest below).
2. **Source edits, in order:** (a) `kernel/loam-microkernel.md` — the version-pinned if-then microkernel; (b) `framework/frame-kernel/` scaffolding (pyproject + package init); (c) `framework/frame-kernel/hooks/subagent_start_context.py` — read kernel file + resolve workstream tier (stub) + query memory tier + compose + emit JSON `hookSpecificOutput.additionalContext`; (d) `framework/frame-kernel/hooks/settings.fragment.json` — SubagentStart registration.
3. **Tests authored:** one test per AC (`framework/frame-kernel/tests/test_AC_SACH_*.py`), including the outcome-altitude real-dispatch probe for AC.SACH.S.
4. **Apply:** `loam amend apply` against the manifest.
5. **Seal:** `loam amend seal --plan-doc` (backfills §14 SHA register + the `frame-kernel` seal sidecar).
6. **Smoke:** the outcome-altitude probe (AC.SACH.S) IS the smoke — a real subagent dispatch confirming the bundle lands in a real subagent's context.

Method (file-read vs hardcode, exact memory top-N, delimiter format, stub-resolver shape) is the builder's call — the constraints above pin the outcome, not the implementation.

---

## §7 Out of scope (deferred + when)

1. **SubagentStop frame-consistency check** — that is SLICE 1b (the OUT-handoff). Do NOT fold it in (explicit dispatch constraint).
2. **Project-keyed selective loading (the `P` layer)** — full project/workstream-keyed rule + memory paging. 1a stubs the workstream-context resolver to "current workstream"; project-keying lands with the project-summary work (SPINE slice S / slice 2 SKILL `paths:`).
3. **Memory query augmentation with a project key** — the `P`-layer delta on `memory_consumer`; 1a reuses the existing `group_ids=[workspace_slug]` query unchanged.
4. **Live activation merge into a workspace's `.claude/settings.json`** — the fragment is authored + tested; the gated hand-merge into a live workspace's settings is a separate dispatcher-timed step (same posture as keep-pace's gated activation), NOT part of this seal.
5. **Auto-composition of fragments by workspace-sync** — workspace-sync does not auto-compose fragments today (keep-pace's is hand-merged). Wiring auto-composition is a workspace-sync change, out of scope for 1a (RF-2).
6. **Replacing `principle_reminder.py`** — SPINE slice 5 (trigger-replacement before blob-deletion); depends on the trigger mechanism, not on 1a's IN-handoff.

---

## §8 Halt triggers (in-flight conditions that abort the build)

1. **Feasibility falsified at build time:** if, when wiring the hook, the `SubagentStart` event does NOT actually deliver `additionalContext` into the subagent's context (the AC.SACH.S real-dispatch probe comes back WITHOUT the microkernel), HALT — the mechanism is infeasible in the running Claude Code version; surface with the probe evidence + the alternative (a UserPromptSubmit-equivalent injected into the subagent's first turn, or brief-text injection via the dispatch wrapper).
2. **SubagentStart envelope lacks the dispatch task text** needed to seed the memory query (D-SACH.4) — if the envelope does not carry the brief/task text, HALT and surface; fall back to a workspace-scoped-only memory query (no task-text seed) as the named alternative, do not silently invent a query.
3. **Fence breach:** if the natural implementation needs to touch a SEALED component beyond `frame-kernel` (e.g. editing `memory_consumer.py` rather than calling it), HALT — that widens the fence; surface for a manifest entry rather than silently widening.
4. **New-component scaffolding collides** with an existing `frame-kernel` name or registration — HALT, surface (the SPINE noted a `Notification` dataclass name-collision hazard; check for analogous collisions before scaffolding).

---

## §9 Bookkeeping (backfill items)

- `docs/STATE.md` — rollup: SLICE 1a (frame-kernel IN-handoff) sealed-local.
- `docs/release-roadmap.md` — slice-1 keystone tracking; mark 1a (IN) done, 1b (OUT) pending.
- Parent plans (pos3 tree) — backfill a pointer from the SPINE slice-1 entry + the integrated-design §8 to this canonical-loam build artefact + its seal SHA.
- §14 method-decision register (this plan) — populated at build time (D-SACH.1..5 narratives) + seal time (SHA backfill).

---

## §10 F2 Ruthless Feedback (honest doubts; named design risks)

**RF-1 — "ships to ANY loam workspace" overstates the live wiring; the FRAGMENT is portable, the ACTIVATION is gated.** *Disagreement:* the dispatch frames the fragment as auto-shipping to any workspace via workspace-sync. *Evidence:* keep-pace's own `settings.fragment.json` carries an explicit `_comment` that it is "NOT merged automatically… the live activation is a GATED final step the dispatcher times"; workspace-sync's src has no fragment-composer (no `fragment` reference in `framework/workspace-sync/src/`). So fragments are NOT auto-composed into `.claude/settings.json` today. *Alternative:* scope 1a's AC.SACH.5 to the PORTABLE-DECLARATION outcome (the fragment exists + is correct + any workspace CAN compose it) — which is real and testable — and put live-activation merge + workspace-sync auto-composition in §7 out-of-scope. The plan does this. The realignment should separately decide whether auto-composition is worth building (it would make the "scale-free governance" claim true in code, not just in artefact).

**RF-2 — the workstream-context tier is a STUB in 1a; the bundle carries a tier whose resolver is a placeholder.** *Disagreement:* a reader could assume 1a delivers project-keyed context. *Evidence:* integrated-design §2-P names project-keying as a distinct layer with its own open question ("what is the in-session topic signal"), resolved by Luke 14221 to project/workstream — that resolution is the `P`-layer build, not 1a. *Alternative:* 1a asserts the tier's PRESENCE (so the bundle shape is frozen for downstream slices) while the resolver is honestly a "current workstream" stub. This is the right decomposition (tighter AC per slice, Lens 5) — but the plan must not let AC.SACH.3 imply a working project-keyer. AC.SACH.3 is written to assert tier-presence + current-workstream reflection only, not project discrimination.

**RF-3 — n=1 outcome-altitude probe is the right confidence level here, but name it.** *Disagreement:* one might want n=3 statistical confidence on AC.SACH.S. *Evidence:* per `feedback_n1_architectural_vs_n3_statistical`, AC.SACH.S asks an ARCHITECTURAL question ("does SubagentStart additionalContext reach the subagent AT ALL?") with a prior-informed hypothesis (the catalogue says yes), a large binary effect, and a binary verifier (microkernel marker present / absent). n=1 suffices for the architectural verdict. *Alternative:* none needed — n=1 is correct; the plan names the question-type so the builder doesn't over-engineer a statistical harness.

**RF-4 — feasibility rests on a catalogue claim, not a live probe; the build's first act de-risks it.** *Disagreement:* I confirmed feasibility from the feature-awareness catalogue (`SubagentStart` + `additionalContext` both listed), not from a live SubagentStart fire. *Evidence:* the catalogue (lines 25-58) lists `SubagentStart` among the 29 events and `additionalContext` "in `hookSpecificOutput`" as an injection field; `principle_reminder.py` proves the JSON-envelope additionalContext mechanism works at UserPromptSubmit; nothing in-repo exercises it at SubagentStart specifically. *Alternative:* the plan makes the AC.SACH.S real-dispatch probe the BUILD'S de-risking act + a §8 halt trigger — if SubagentStart doesn't deliver additionalContext to the subagent in the running version, the build halts with evidence rather than shipping a dead hook. This is the correct place to carry the residual feasibility risk (build-time empirical, not plan-time blocker).

---

## §11 Provenance trail (load-bearing sources)

- **Feasibility (CONFIRMED):** `/Users/lukeivers/pos3/.claude/skills/claude-feature-awareness/SKILL.md` §1 (line 27 — `SubagentStart`/`SubagentStop` in the 29-event catalogue; line 47 — "bracket every subagent dispatch") + §2 (line 58 — `additionalContext` in `hookSpecificOutput` "string injected into Claude's context").
- **Injector pattern (mirror):** `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py` (file-read → additionalContext, fail-soft exit-0, `[missing]` markers, per-file ceiling) + `/Users/lukeivers/pos3/.claude/hooks/principle_reminder.py` (the `hookSpecificOutput.additionalContext` JSON envelope — the exact subagent-targeting shape, D-SACH.5).
- **Fragment model:** `framework/hands-off-lifecycle/hooks/keep_pace/settings.fragment.json` (`${LOAM_REPO}` placeholder, matcher-block shape, gated-activation `_comment`).
- **Memory selection:** `framework/primary-persona/src/loam/primary_persona/memory_consumer.py` (`search(query, group_ids=[workspace_slug])`, lines 119-135, 274-333 — the retrieval-contributor this build's memory tier reuses).
- **Workspace-sync (fragment NOT auto-composed):** `framework/workspace-sync/README.md` + `framework/workspace-sync/src/` (no `fragment` composer — basis for RF-1 / §7-5).
- **Design WHAT:** integrated design `/Users/lukeivers/pos3/docs/plans/loam-frame-robustness-INTEGRATED-DESIGN-and-EVAL-PLAN-2026-06-08.md` §2-K (microkernel + if-then), §2-P (project-keying = the deferred layer), §3 (three-role identity), §8 (the SubagentStart push-down — the exact UNUSED home + IN/OUT split). SPINE `/Users/lukeivers/pos3/docs/plans/loam-realignment-SPINE-and-PLAN-2026-06-08.md` Part II.B (governance-asymmetry #1 finding, lines 110-126; slice-1 keystone, lines 158-161).
- **Orchestration finding (SubagentStart unused):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-primitive-lift-audit-2026-06-08.md` + `orchestration-primitive-analysis-2026-06-08.md` (zero subagent matchers in settings.json; SubagentStart additionalContext = the auto-context handoff recommendation).
- **Plan/manifest convention:** `plugins/dev-sdlc/docs/conventions/plan-docs.md`. **Scope-descriptive AC IDs + slug** (no version-packing): `feedback_scope_descriptive_ac_ids` + `feedback_version_numbers_at_release_time`.

---

## §14 Method-decision register (populated at build + seal time)

- **D-SACH.1** (component placement + fragment registration) — narrative TBD-AT-BUILD; SHA TBD-AT-SEAL.
- **D-SACH.2** (microkernel content + if-then format) — narrative TBD-AT-BUILD; SHA TBD-AT-SEAL.
- **D-SACH.3** (workstream-context resolution + project-keying stub) — narrative TBD-AT-BUILD; SHA TBD-AT-SEAL.
- **D-SACH.4** (memory selection) — narrative TBD-AT-BUILD; SHA TBD-AT-SEAL.
- **D-SACH.5** (bundle output envelope) — narrative TBD-AT-BUILD; SHA TBD-AT-SEAL.
- **D-build.\*** (builder-discovered method decisions) — TBD-AT-BUILD.

## §15 Backwards-compat verification

- No existing test touched (new component, new files only). The `frame-kernel` seal_test is new; no other component's seal anchor moves.
- The fragment is NOT merged into any live `.claude/settings.json` in this seal (out-of-scope §7-4) — so no existing hook wiring changes; existing SessionStart/UserPromptSubmit/Stop hooks are untouched.

## §16 Halt-and-surface findings (raised + ruled at plan-authoring)

- **Feasibility ruled FEASIBLE** from the catalogue (§11) — `SubagentStart` + `additionalContext`-in-`hookSpecificOutput` both first-class; residual live-version risk carried as the AC.SACH.S build-time probe + §8 halt trigger #1.
- **Component-placement ruled NEW `frame-kernel`** (D-SACH.1) — not owner-gated (method-level); recommendation in §2.
- **Project-keying ruled OUT (stubbed)** for 1a (D-SACH.3) — keeps 1a bounded to the IN-handoff per dispatch constraint; the `P`-layer is the separate project-summary build.
- **Fragment-auto-composition ruled OUT** (RF-1 / §7-5) — the dispatch's "ships to ANY workspace" is true of the artefact, not yet of live auto-merge; surfaced rather than silently claimed.
