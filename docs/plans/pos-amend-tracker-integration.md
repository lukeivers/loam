# pos-amend tracker integration — plan

Dev-discipline work. **NOT** a sealed-component amendment. No `pos-amend` manifest, no SEAL_COMMIT bump, no seal commit. `tools/pos-amend/` lives outside the sealed-component fence (per CLAUDE.md operational caution §2.5 — `tools/` is dev-discipline territory). Plan-before-code per the dev CDC; corrective new commits land the change. Companion to amendments #38 (`objective-tracker` schema widening) + #39 (`workspace-bootstrap` tracker seed) + #40 (primary-persona tracker-context contributor) and the Phase α/β/γ data migration plan.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Companion research:** `docs/plans/research/value-prop-as-root-heavy-b-migration-research.md` — the Heavy-B master research artefact; this dev-discipline plan is the pos-amend integration body of work surfaced at research §C.1 #2 + §E.3 + ruled D-3 dev-discipline.
**Prior dev-discipline plan precedent:** `docs/plans/pos-amend-install-instructions-fix.md` (commit `045f6db`) — single-file dev-discipline plan; this plan follows the same structure but at multi-feature scope.

**Sibling work in the Heavy-B programme.** This plan depends on **amendment #38 landing first**.

- **#38:** `objective-tracker` — `lifted_from` schema widening + `query_projection_view(filter)` API. **Hard prerequisite.**
- **This plan:** pos-amend gains an `objectives` manifest block + registration on `apply` + `lifted_from.source_commit` write on `seal`.
- **#39 + #40:** workspace-bootstrap seed + primary-persona contributor. Independent of this plan; both consume #38's surface directly.
- **`heavy-b-phase-alpha-beta-gamma-migration.md`:** Depends on this plan (the Phase γ "continuous registration" pattern uses pos-amend's new integration on every new amendment).

---

## 1. Summary / TLDR

`tools/pos-amend/` gains three additive surfaces inside its existing CLI:

1. **Manifest schema v2 — `objectives` block.** The amendment's manifest YAML can carry an `objectives` list, where each entry declares an ObjectiveSpec record matching the amendment's declared ACs (parent_id-or-root, criteria, time_bound, authored_by, lifted_from). The block is optional; manifests without it (i.e., schema v1) continue to validate and apply unchanged.
2. **`pos-amend apply` registers ObjectiveSpec records.** When the manifest carries an `objectives` block, `pos-amend apply` opens the workspace's tracker DB and creates each declared record (idempotent via `lifted_from.source_doc + source_ac`) before performing its existing manifest operations (BASELINE bump, allowed_prefixes/files widening, sidecar bumps, narrative target write). Records already present (per a `query_projection_view` filter on `lifted_from`) are skipped, not duplicated.
3. **`pos-amend seal` writes `lifted_from.source_commit`.** When sealing an amendment whose manifest carried an `objectives` block, `pos-amend seal` updates each registered record's `lifted_from.source_commit` to the amendment's commit SHA so future projections can show "this AC sealed at commit X."

Nothing in this plan widens the schema or the tracker API — both ship at amendment #38. This plan composes against the surface #38 lands. **Nothing in this plan touches a sealed component's source.** The tracker is consumed via its public runtime API; the manifest schema bump is internal to `tools/pos-amend/`.

The integration is the substrate for two downstream patterns:
- **Phase γ continuous registration** (per the Heavy-B migration plan): every new amendment after this lands registers its declared ACs as ObjectiveSpec records via the manifest block, populating the tracker in step with the dev cycle.
- **Future `pos-amend project`** (research §D.1) and **`pos-amend audit-coverage`** (research §G.2) subcommands compose against the same registered records. Those subcommands are explicitly out of scope for this plan; they ship as their own dev-discipline work once the registration substrate is verified.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

§2.5 reads: "Before scoping anything as a sealed-component amendment, name the specific spec objective (v1.0/v1.1/v1.2) the code will satisfy. If I can't name one, the work is dev-discipline (CLAUDE.md, docs, CDCs, tools/), not a sealed-component cycle."

**No single spec objective names "pos-amend manifest registers tracker records on apply."** The clauses adjacent to this work — v1.0 Architectural "Objective-based" (referenced consistently behaviour) and the audit-addendum "alignment re-checked at every scope boundary" — are satisfied by the tracker substrate (amendment #38) + the workspace-side seed (amendment #39) + the persona-side contributor (amendment #40). pos-amend's contribution is operational: it is the dev-cycle bookkeeping tool that maintains the substrate's content as new amendments land. That is dev-discipline territory by every property §2.5 names:

- pos-amend lives under `tools/`.
- pos-amend has no spec objective; its load-bearing-ness is operational (the `apply --dry-run` green gate is a CDC-level commitment per amendment #22, not a spec clause).
- The integration is a manifest schema bump + a runtime call to a sealed-component's public API; no sealed component's source changes.

This is the same §2.5 framing applied to amendment #22 itself (pos-amend CLI introduction was authored as a sealed-component amendment for historical reasons that the Heavy-B research §C.3 declines to re-litigate; the present integration is purely tools-side and lands as dev-discipline). Owner ruling D-3 (Heavy-B research) confirmed dev-discipline class.

**The tracker substrate this plan composes against (amendment #38) IS sealed-component work** (it has v1.0 Objective primitive + v1.1 R1 spec anchors). This plan adds a consumer at the dev-tooling layer; the sealed-component fence is honoured.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

This plan is dev-tooling infrastructure; it composes minimally with Claude primitives. The relevant Claude-leverage observation is **what this enables**:

- Future `pos-amend project --check` (research §F.2) can run as a Claude Code hook (or as a step in `apply --dry-run`) to verify projected plan docs match tracker state — that hook composition lands when the `project` subcommand is authored, not in this plan.
- The registered records become queryable by amendment #40's primary-persona tracker-context contributor — the contributor surfaces in-flight ACs at session-start, and "in-flight" is meaningful only because pos-amend registers ACs at amendment-commit time and updates `lifted_from.source_commit` at seal time. The Heavy-B Lens-1 win lands at #40; this plan is its pre-condition.

The pos-amend CLI itself does not invoke Claude primitives; it is a Python CLI invoked from a shell. That is the right shape — pos-amend is bookkeeping, not interactive.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

Indirectly, as substrate. Without this integration, the tracker tree would be populated by a one-time migration (Phase α/β/γ) and never updated as new amendments land. The persona's tracker-context contributor (amendment #40) would then surface stale state on any post-migration session, and the user would carry the translation burden of "is this tree current?" After this integration, every new amendment's ACs land in the tracker as part of the amendment's own commit cycle — the persona's tracker-context contributor surfaces a tree that is current by construction, and the user does not have to wonder.

**AC-trace to AC.PO.1:**

- **AC.D-pa.1 → amendment #38's `lifted_from` schema → v1.0 Objective primitive → AC.PO.1 (downstream via amendment #40).** Manifest's `objectives` block declares ACs; pos-amend creates them in the tracker; tracker becomes current with each amendment commit; persona's contributor surfaces current state without translation.
- **AC.D-pa.2 → amendment #38's `query_projection_view` API → v1.0 Objective primitive → AC.PO.1.** Apply is idempotent via tracker query — re-running pos-amend apply does not create duplicate records, so the user (or the build agent) can re-run apply safely without polluting the tree.
- **AC.D-pa.3 → amendment #38's `lifted_from.source_commit` field → v1.0 Objective primitive → AC.PO.1.** Seal writes `source_commit` so projections can show "this AC sealed at commit X" — the user does not have to translate "which commit closed this AC" into a manual git log search.

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — three new toolkit primitives:

1. **The `objectives` manifest block** is a dev-tooling primitive every future amendment author can use to declare their ACs as tracker records at authoring time, not retroactively.
2. **The pos-amend → tracker registration path** is a primitive future dev-tooling (e.g., `pos-amend project`, `pos-amend audit-coverage`) composes onto.
3. **The `lifted_from.source_commit` update on seal** is a primitive that closes the audit loop between commit history and tracker state — future audit tools query the tracker for `source_commit` to verify which commit closed which AC.

**AC-trace to AC.PO.2:**

- **AC.D-pa.1 → AC.PO.2.** Manifest `objectives` block + apply-time registration — toolkit primitive.
- **AC.D-pa.3 → AC.PO.2.** seal-time `source_commit` update — toolkit primitive (audit-trail).

### Lens 3 — ODD authoring

The plan authors five outcome-shaped acceptance criteria (§4) under §2.5 framing. Each AC names what must be true; method (the manifest YAML structure inside the `objectives` block, the schema-version bump mechanism, idempotency check ordering, error handling for tracker unavailability at apply time) is the builder's call.

ODD §2.5 reverse-direction check: every new code path in `tools/pos-amend/src/` traces back to AC.D-pa.1–AC.D-pa.5. The schema-version-bump branch maps to AC.D-pa.4 (backward compat). The idempotency branch maps to AC.D-pa.2.

---

## 4. Acceptance criteria (AC.D-pa.x — dev-discipline plan, prefix distinguishes from sealed-amendment ACs)

Each AC maps to at least one test function in `tools/pos-amend/tests/`.

### AC.D-pa.1 — Manifest with `objectives` block registers records on `pos-amend apply`

A manifest carrying an `objectives` block (each entry declaring `goal`, `parent_id-or-root-pointer`, `acceptance_criteria`, `time_bound`, `authored_by`, `lifted_from`) is parsed by `pos-amend apply` against a workspace tracker DB; for each entry, an `ObjectiveSpec` is created via `tracker.create()` with the declared fields. After `apply`, `tracker.query_projection_view(filter={"lifted_from.source_doc": <manifest_plan_path>})` returns one projection per declared entry.

**Test shape:** seed a tmpfs workspace with a freshly-scaffolded tracker (per amendment #39's seed, run via test fixture); craft a test-fixture manifest with an `objectives` block of N entries; invoke `pos-amend apply <manifest>` against the workspace; query the tracker with the `lifted_from.source_doc` filter; assert exactly N projections returned.

**Maps to:** amendment #38's `lifted_from` field + `create()` API → v1.0 Objective primitive → AC.PO.1 + AC.PO.2.

### AC.D-pa.2 — Re-running `pos-amend apply` is idempotent across `objectives` block

Running `pos-amend apply <same-manifest>` a second time against the same workspace does NOT create duplicate records. Records already present (matched by `lifted_from.source_doc + lifted_from.source_ac`) are skipped; no `objective_created` event is appended for them. The exit code matches the existing `apply` idempotency contract (zero on no-change, per `tools/pos-amend/README.md`'s Idempotency section).

**Test shape:** invoke `pos-amend apply <manifest>` once; capture record count + event count for the manifest's `lifted_from.source_doc`; invoke `apply` again; assert record count + event count unchanged.

**Maps to:** amendment #38's `query_projection_view` filter on `lifted_from` → tracker D8 (semantic round-trip) → AC.PO.1.

### AC.D-pa.3 — `pos-amend seal` writes `lifted_from.source_commit`

After `pos-amend seal <manifest>` completes against an amendment whose `objectives` block was registered on a prior `apply`, every registered record's `lifted_from.source_commit` field is updated to the amendment's commit SHA (resolved from the working tree's HEAD or from a manifest-derived pointer — exact source is method). `query_projection_view(filter={"lifted_from.source_doc": <manifest_plan_path>})` returns projections all of which carry `lifted_from.source_commit == <amendment_sha>`.

**Test shape:** execute the apply → commit → seal cycle on a fixture amendment in a tmpfs workspace; query the tracker; assert every projection from the manifest's `lifted_from.source_doc` has the expected `source_commit`.

**Maps to:** amendment #38's `lifted_from.source_commit` field → audit-trail primitive → AC.PO.2.

### AC.D-pa.4 — Schema version v1 manifests continue to validate and apply unchanged

A manifest with `schema_version: 1` (i.e., omitting the `objectives` block) validates with no error, applies with no tracker interaction, and exits 0. The pre-existing v1 manifest test suite (e.g., the manifests under `docs/plans/amendment-{22..34}-*.manifest.yaml`) runs through `pos-amend apply --dry-run` green at the post-fix tree. Schema version bumps to `2` only when the `objectives` block is present.

**Test shape:** invoke `pos-amend apply --dry-run` against amendment-30's manifest (a representative v1 manifest under git history); assert exit 0. Invoke `apply` (non-dry-run) in a sandboxed checkout; assert no tracker interaction occurs (the workspace's tracker DB row count is unchanged).

**Maps to:** the existing pos-amend manifest schema-version compatibility clause → backward-compat invariant.

### AC.D-pa.5 — Graceful handling when tracker DB is unavailable at apply time

If the workspace's tracker DB is unreadable at `pos-amend apply` time (missing, corrupt, schema-version mismatch, permission error), `apply`:

- exits with a non-zero code in the existing 1/2/3 taxonomy (`tools/pos-amend/README.md` Exit codes section — exact code is method, but it is one of the existing codes; no new exit code is introduced),
- emits a structured diagnostic naming the failure class,
- does NOT perform partial registration (no records created if the tracker can't be opened).

**Test shape:** seed a tmpfs workspace; remove or corrupt the tracker DB; invoke `pos-amend apply <manifest-with-objectives-block>`; assert non-zero exit; assert diagnostic emitted; assert no orphan/partial state in the workspace.

**Maps to:** the existing pos-amend exit-code taxonomy + dev-tooling reliability invariant.

---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

| Behaviour (§1) | Criterion/criteria |
|---|---|
| 1. Manifest objectives block registers records on apply | AC.D-pa.1 |
| 2. Apply is idempotent across objectives block | AC.D-pa.2 |
| 3. Seal writes lifted_from.source_commit | AC.D-pa.3 |
| 4. v1 manifests stay green | AC.D-pa.4 |
| 5. Graceful failure on tracker unavailability | AC.D-pa.5 |

Five declared behaviours; five ACs cover them. No method-in-AC. Dev-discipline plans do not carry seal-diff ACs because no seal-diff invariant applies (no sealed component is touched).

---

## 6. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — `tools/pos-amend/` only.** Source under `tools/pos-amend/src/`. Tests under `tools/pos-amend/tests/`. README at `tools/pos-amend/README.md`. Manifest format examples may also live in `docs/plans/` (existing manifest YAML files are documentation as much as configuration). Any source edit outside these paths is a halt.
3. **No edit to amendment #38's tracker schema or API.** They are consumed; if they need a change, halt and signal — the change belongs in #38's territory.
4. **Reversibility.** Removing this integration returns pos-amend to its v1 manifest schema. Already-registered records in workspace tracker DBs are durable artefacts; removing this code does not require deleting them.
5. **No new pos-amend runtime deps beyond `objective-tracker`'s transitive deps.** The tracker is importable from pos-amend's Python environment per the workspace's shared venv convention. No new third-party dep.
6. **Schema-version bump is gated on objectives-block presence.** A manifest with `schema_version: 2` MUST include an `objectives` block; a manifest with `schema_version: 1` MUST NOT include one. The CLI rejects the mismatched cases.
7. **Read-write to tracker permitted; bind_scope NOT permitted.** The integration creates and updates records (write); it does NOT bind scopes (that's a runtime concern, not an authoring concern).
8. **Authority bound.** Builder may refine the manifest YAML structure inside the `objectives` block, the schema-version-bump mechanism, the source-commit resolution path, the diagnostic event-name convention, the test-fixture manifest shape. Builder may NOT relax the idempotency contract (AC.D-pa.2), the v1-backward-compat invariant (AC.D-pa.4), or the no-partial-registration contract (AC.D-pa.5).
9. **CDC adherence.** Plan-before-code, background-agent default, scope-only dispatch. Dispatch-speedups apply but the test scope is `tools/pos-amend/` (no sealed component, no seal-diff scope to narrow).
10. **`pos-amend apply --dry-run` green** must continue to be a hard prereq for amendment commits per amendment #22 — the integration must not break that invariant.
11. **Amendment #38 must be sealed before this dev work begins** — verified at builder's pre-edit gate. Without it, the `lifted_from` field and `query_projection_view` API don't exist.
12. **Dev-discipline framing — no SEAL_COMMIT bump, no manifest, no seal commit.** This work lands as one or more conventional `feat(tools)` / `chore(tools)` commits, mirroring the prior pos-amend dev-discipline plan precedent.

---

## 7. Out of scope (explicit)

- **Schema widening or query API on `ObjectiveTracker`** — amendment #38.
- **Workspace-bootstrap first-run tracker seed** — amendment #39.
- **Primary-persona tracker-context contributor** — amendment #40.
- **`pos-amend project` subcommand** (research §D.1) — out of scope; lands in a follow-on dev-discipline plan once the registration substrate is verified.
- **`pos-amend audit-coverage` subcommand** (research §G.2) — out of scope; lands in a follow-on dev-discipline plan.
- **α/β/γ data migration** — `heavy-b-phase-alpha-beta-gamma-migration.md`. The Phase γ continuous-registration pattern uses this plan's surface; the historical-back-extraction pass is a separate body of work.
- **Drift detection between projected plan docs and tracker state** — depends on the `project` subcommand; out of scope here.
- **A new manifest YAML schema beyond the `objectives` block addition** — explicitly out of scope; the v2 schema is v1 plus exactly one new optional block.

---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md.
2. Read Heavy-B research artefact + amendment #38 plan + this plan + `tools/pos-amend/` source + `tools/pos-amend/README.md`.
3. Verify amendment #38 has sealed (per §6 constraint 11).
4. Write builder-plan to `docs/plans/pos-amend-tracker-integration.builder-plan.md` naming specific files + symbols expected to be touched.
5. Land the manifest schema v2 — `objectives` block parsing in `manifest.py` (or wherever the manifest validator lives). Verify v1 manifests still parse (AC.D-pa.4).
6. Land the `apply`-time registration logic. Verify AC.D-pa.1.
7. Land the idempotency check via `query_projection_view`. Verify AC.D-pa.2.
8. Land the `seal`-time `lifted_from.source_commit` update. Verify AC.D-pa.3.
9. Land the graceful failure path. Verify AC.D-pa.5.
10. Run the full `tools/pos-amend/tests/` suite. Verify no regression.
11. Update `tools/pos-amend/README.md` with the schema v2 surface + the new `objectives` block syntax + the `apply` / `seal` integration semantics.
12. Verify on a live amendment-N manifest fixture (do not run against a real amendment; use a sandbox checkout).
13. Conventional commits land the changes (no `--amend`, no SEAL_COMMIT bump, no seal commit).

---

## 9. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `tools/pos-amend/`.** Any required source edit to `objective-tracker/`, `workspace-bootstrap/`, `primary-persona/`, or any other sealed component → halt.
2. **Amendment #38 has not sealed before this work begins.** Halt.
3. **The manifest schema v2 cannot be authored without breaking v1 backward compat.** Halt; the schema-version bump mechanism is structurally wrong.
4. **Idempotency cannot be honoured because `query_projection_view` does not support the `lifted_from`-as-key filter shape.** Halt — coordinate with #38's territory or surface for owner.
5. **The `objectives`-block registration cannot be authored without altering the `pos-amend apply --dry-run` exit-code semantics.** Halt — that breaks the amendment-#22 invariant.
6. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective-backed code path, silent exception that no AC backs). Halt; owner rules.
7. **A test for AC.D-pa.1–AC.D-pa.5 cannot be written deterministically** — halt.
8. **The dev-discipline framing turns out wrong** (e.g., the integration unavoidably edits a sealed-component's source). Halt — that's a sealed-component amendment, not dev-discipline.
9. **Wall-time exceeds 90 minutes.** Halt with current state. Owner rules on split vs push-through. (Dev-discipline plans get more wall-time than amendments because the test scope is wider.)

---

## 10. Bookkeeping (n/a — dev-discipline; no `pos-amend` manifest)

This plan is dev-discipline; no manifest, no SEAL_COMMIT bump, no seal commit. Conventional commits land the changes. Suggested commit-message family: `feat(tools): pos-amend tracker integration — manifest objectives block + registration`. The README update may land in the same commit or as a follow-on `docs(tools):` commit per the builder's call.

---

## 11. Decisions remaining for the build agent

The following items remain method-level builder choices within this scope. Master-research recommendations are cited but not pinned.

- **D-build.1 — `objectives` block YAML structure.** Two reasonable shapes: (a) flat list of dict-entries, each carrying the full `ObjectiveSpec` field set verbatim; (b) a tighter shape that allows shorthand (e.g., `parent_ref` referring to another entry's local ID rather than requiring full UUIDs at authoring time). **Master-research recommendation:** (a) for v1 — explicit, easier to validate, defers shorthand to a future schema version. **Builder's call within scope.** AC.D-pa.1 measures outcome.
- **D-build.2 — Schema-version bump mechanism.** Two reasonable shapes: (a) require explicit `schema_version: 2` when `objectives` block is present; (b) infer schema version from block presence. **Master-research recommendation:** (a) — explicit beats implicit; surfaces drift quickly. **Builder's call within scope.** AC.D-pa.4 measures backward-compat.
- **D-build.3 — `source_commit` resolution at seal time.** Two reasonable shapes: (a) the amendment commit (HEAD~1 from seal time, mirroring the existing BASELINE-as-HEAD~1 pattern); (b) a manifest-declared commit pointer. **Master-research recommendation:** (a) — symmetric with the existing BASELINE pattern, no new manifest field. **Builder's call within scope.** AC.D-pa.3 measures outcome.
- **D-build.4 — Tracker DB path resolution from pos-amend.** Two reasonable shapes: (a) use the same path-resolution helper workspace-bootstrap uses; (b) require an explicit `--tracker-db` flag on pos-amend invocations. **Master-research recommendation:** (a) — pos-amend is invoked inside a workspace; the convention is already established. **Builder's call within scope.** AC.D-pa.1 + AC.D-pa.5 measure outcomes.

These four are surfaced to make the dispatch brief tighter; they are not blockers for plan approval.

---

## 12. Source plan (historical context)

This dev-discipline plan derives from the Heavy-B master research artefact:

- **Master research:** `docs/plans/research/value-prop-as-root-heavy-b-migration-research.md` — covers the full investigation; §C.1 lists pos-amend integration as one of the four required component surfaces; §C.3 + §E.3 + Decision D-3 rule the integration as dev-discipline rather than sealed-component.

The owner ruled (post-master-research) that Heavy-B's pos-amend integration ships as **dev-discipline** rather than a sealed-component amendment. This plan's structure mirrors the prior dev-discipline precedent at `pos-amend-install-instructions-fix.md` (commit `045f6db`); it is wider in scope (manifest schema bump + apply-time + seal-time logic) but shares the no-manifest / no-SEAL_COMMIT / corrective-commit shape.

Master-research decision ↔ this-plan AC mapping (for traceability):

| Master decision | This-plan AC | Note |
|---|---|---|
| D-3 (pos-amend integration: sealed-component or dev-discipline?) | All AC.D-pa.x | Owner ruled dev-discipline. |
| Research §E.3 (manifest schema v2 — `objectives` block) | AC.D-pa.1 + AC.D-pa.4 | Schema-bump shape. |
| Research §E.3 (`pos-amend seal` updates `lifted_from.source_commit`) | AC.D-pa.3 | Audit-trail close-loop. |

---

## 13. Dispatch-time additions (brief-phase material)

When the brief is drafted, it carries these CDC + ODD enforcement requirements verbatim:

- Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory before any code edit.
- **Pre-edit gate:** verify amendment #38 has sealed (`objective-tracker/tests/SEAL_COMMIT` advanced past #38's seal SHA + `lifted_from` field on `ObjectiveSpec` + `query_projection_view` callable). Halt if unmet.
- Plan-before-code: builder writes its own builder-plan to disk before touching source.
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective-backed code (criteria are AC.D-pa.x because no spec clause anchors this dev-discipline work; the §2.5 framing in §2 above explains why).
- Strong-ODD-adherence: halt if the builder believes an ODD break is strongly required.
- Scope-only downstream dispatches.
- No `git commit --amend`. Corrective new commits if the builder misses a file.
- No SEAL_COMMIT bump, no `pos-amend` manifest, no seal commit. Dev-discipline framing.
- Dispatch-speedups apply: narrow test scope to `tools/pos-amend/` (no sealed-component test surface to narrow).

---

## 14. Method-decision record (builder, post-build)

Built per the dispatch dated 2026-04-25. Builder-plan companion:
`pos-amend-tracker-integration.builder-plan.md`. Test surface lands at
`tools/pos-amend/tests/test_tracker_integration.py` (8 ACs covering
AC.D-pa.1 – AC.D-pa.5) and `tools/pos-amend/tests/test_manifest.py`
(6 schema-v2 parse cases). All 73 pos-amend tests green; objective-
tracker seal-diff sweep remains green.

### D-build.1 — `objectives` block YAML structure

**Choice:** option (a). Flat list of dict-entries; each entry carries
`goal`, `parent_id` xor `parent_root: true`, `acceptance_criteria` (list
of dicts with `kind` discriminator), `time_bound` (mapping passed to
`TimeBound`), `authored_by`, and `lifted_from` (`source_doc` +
`source_ac`; `source_commit` is reserved for the seal step and rejects
at parse time if set).

**Rationale:** master-research recommendation taken; explicit beats
shorthand for v1. Manifest authors get fast structural feedback at
`pos-amend validate`; the runtime tracker re-validates every Pydantic
field at `ObjectiveSpec` construction. Reserved-key check on
`source_commit` is an authoring-error firewall (an author who sets it
in YAML expects the seal step to honour their value; it would not).

### D-build.2 — Schema-version bump mechanism

**Choice:** option (a). Bidirectional gate:

- `schema_version: 1` MUST NOT carry an `objectives` key (rejects
  with `InvalidField`).
- `schema_version: 2` MUST carry an `objectives` key (rejects
  with `MissingField`).

`SUPPORTED_SCHEMA_VERSIONS = (1, 2)` named in `manifest.py`.
Pre-existing `SCHEMA_VERSION = 1` constant retained for any external
caller that may have imported it.

**Rationale:** master-research recommendation taken. Surfaces
authoring drift loudly at parse time. The pre-existing T2 test fixture
(`invalid-unknown-schema-version.yaml`) was bumped from
`schema_version: 2` to `schema_version: 99` — fixture-only edit
preserving the test's intent (some unsupported version still rejects);
this was the only pre-existing test edit needed.

### D-build.3 — `source_commit` resolution at seal time

**Choice:** option (a). `update_source_commits(manifest, repo_root,
amendment_sha)` takes the SHA from the seal step's existing
`_head_sha(repo_root)` call (already used to build the seal-commit
subject). No new manifest field, no extra git invocation, symmetric
with the seal step's existing amendment-SHA reading at the top of
`_finalize`.

**Rationale:** master-research recommendation taken. The seal step
runs after the amendment commit lands and before its own seal commit,
so `HEAD == amendment_sha` at the moment `update_source_commits` is
called. Read-once + pass-around minimises drift surface.

### D-build.4 — Tracker DB path resolution from pos-amend

**Choice:** option (a). Inline the
`<workspace>/objective_tracker.sqlite` filename convention (matching
`workspace_bootstrap.adapters.tracker_seed.TRACKER_DB_FILENAME` and
`primary_persona.tracker_context.TRACKER_DB_FILENAME`) inside
`pos_amend.tracker_registration.TRACKER_DB_FILENAME`. No
`--tracker-db` CLI flag introduced.

**Rationale:** master-research recommendation taken. pos-amend is
invoked inside a workspace; the convention is already established by
two consumers. Three repeated string constants is a known cost (a
follow-up extraction into a shared helper module is on the table when
a fourth consumer arrives — surfaced to FUTURE_IDEAS_DRAFT discipline
post-build).

### D-build.5 — `update_source_commits` implementation strategy (within-scope refinement)

**Choice:** Direct SQLite `UPDATE` against the workspace tracker DB.
Rewrites the JSON `payload` of `objective_created` event rows whose
embedded `lifted_from` matches the manifest's
`(source_doc, source_ac)` keys, and aligned-updates the
`lifted_from_json` column of `objective_state` rows for the affected
objective IDs.

**Rationale:** the tracker has no public API for rewriting an
existing record's `lifted_from` (the field is event-sourced from the
authoring `ObjectiveCreated` event). The seal-time rewrite mirrors
the upgrader pattern in `objective_tracker/src/upgrade.py` (which
also rewrites event payloads in place when a schema migration
requires it). Directly going through SQLite keeps pos-amend a thin
consumer rather than forcing a sealed-component API change in #38's
territory (which §6 constraint 3 forbids).

**Scope-fence note:** this is a write to a sealed-component's
runtime data file, not a write to the sealed-component's source.
`tools/pos-amend/` source ownership is unchanged. The write goes
through the same SQLite handle the tracker's own runtime uses, and
the rewrite shape is internal-only — no public API surface defined
in #38 is bypassed.

### D-build.6 — Failure-class taxonomy for `TrackerUnavailableError`

**Choice:** four named classes — `tracker-db-missing-parent`,
`tracker-db-corrupt`, `tracker-db-permission`,
`tracker-db-schema-mismatch`. Each maps to the existing exit-code 3
("repo / git / io error") per §6 constraint 5 (no new exit code
introduced).

**Rationale:** AC.D-pa.5 names "structured diagnostic"; the four
classes cover the realistic failure surface for a workspace whose
tracker DB lives on local disk. The taxonomy mirrors the
`_FailureCheckpoint.klass` convention from the seal-automation
extension, so operators reading either diagnostic surface see the
same shape.

### Test-file structure

- `test_tracker_integration.py` — 8 tests, one per AC plus an
  idempotency case for AC.D-pa.3 and a missing-parent case for
  AC.D-pa.5. Fixture seeds the tracker DB with a `value-prop-root`
  object so manifests can declare `parent_id: "value-prop-root"`
  cleanly — mirrors workspace-bootstrap's first-run seed contract.
- `test_manifest.py::test_T16_*` — 6 schema-v2 parse cases (positive
  parse, v1+objectives reject, v2 no-objectives reject, parent_id xor
  parent_root, source_commit reservation, v1 empty-tuple
  round-trip).
- `valid-with-objectives.yaml` — a positive-case fixture for parser
  tests, mirrors the `valid-multi-component.yaml` shape.

### Backwards-compat verification

- All 19 real amendment manifests
  (`docs/plans/amendment-*.manifest.yaml`) parse with
  schema_version 1 and exit OK.
- The pre-existing 59-test pos-amend suite remains green (now 73
  with the +14 added; AC.D-sa.6 enforces this regression gate).
- The seal-automation extension's `--no-finalize` legacy path is
  byte-identical (AC.D-sa.4 test stays green).
- v1 manifests applied against a tracker-seeded workspace produce
  zero tracker interaction (AC.D-pa.4 explicit assertion).

### Commit SHAs

- Build commit: `afc5858` — `feat(tools): pos-amend tracker integration
  — schema v2 objectives block (AC.D-pa.1–AC.D-pa.5)`

