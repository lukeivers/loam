# Research — VALUE_PROPOSITION as the prime objective: Heavy-B migration into the live tracker

**Status:** research only. Pre-proposal. No code, no AC numbering, no
implementation plan. This document answers the question set the owner
posed for the "lift VALUE_PROPOSITION + everything below it into the
sealed objective-tracker" body of work.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2`.

**Owner rulings already locked (do not re-litigate):**

1. Heavy-B chosen — tracker becomes the source of truth for pos-v2 dev
   work; plan docs become projections.
2. Single tree. `VALUE_PROPOSITION` is the root. `authored_by="user"`.
3. AC.PO.1 (translation-burden reduction) and AC.PO.2 (toolkit
   expansion) are CRITERIA on the root, not separate child objectives.
4. Everything else descends from the value prop as user-authored
   sub-objectives (spec v1.0/v1.1/v1.2, ODD adoption, the 13 sealed
   component objectives, the ~37 amendment ACs, in-flight work).
5. Future workspace-user objectives slot under the same root.

The research below frames *what would have to be true* to land Heavy-B
cleanly. It does not prescribe ACs or files.

---

## Executive recommendation (read this first)

**Land Heavy-B as a multi-amendment programme, not a single big-bang.
Migration mechanics are hybrid (automated extractor for already-
structured ACs, manual seeding for the value-prop root and
spec-derived nodes). The tracker schema fits with one targeted
widening (a `lifted_from` provenance pointer) rather than a new
criterion variant. Plan docs become projections rendered on demand
from a new read-side query API, but already-landed plan docs stay as
historical artefacts. The minimum amendment set is four sealed
components (objective-tracker, pos-amend, primary-persona,
workspace-bootstrap) plus dev-discipline updates to the CDCs.**

**Six halt-and-surface decisions** are at the bottom (§Decisions).
The research did not turn up evidence requiring re-litigation of any
locked ruling.

---

## A — Schema fit

### A.1 Does the live `ObjectiveSpec` accommodate the value prop as root?

**Yes, with one structural caveat.**

The Pydantic model at `objective-tracker/src/spec.py` (read in full)
has these required fields on `ObjectiveSpec`: `goal` (non-empty str),
`parent_id` (`str | None`), `acceptance_criteria` (`tuple[Criterion,
...]`), `time_bound` (`TimeBound`), `authored_by` (non-empty str),
`owner` (optional), `parent_close_policy` (default `notify`). The
forest invariant is enforced by `parent_id is None ⇒ root`, and the
`bind_scope` enforcement reads `authored_by == "user"` on the terminal
ancestor (`runtime.py` lines 466–516).

The value prop maps cleanly:

- `goal` — the one-sentence statement of the value prop ("close the
  gap between what the AI can do and what the user can get it to do
  via a translation layer + harness").
- `parent_id = None` — root.
- `authored_by = "user"` — Luke authored VALUE_PROPOSITION.md.
- `time_bound = TimeBound(evergreen=True, review_cadence=...)` — the
  value prop is evergreen by construction (see `VALUE_PROPOSITION.md`
  — "captured as a durable design principle"). The `review_cadence`
  field is permitted only when `evergreen=True` (`spec.py` line 213).
  This is a clean fit; cadence string can be "amendment-driven" or
  similar prose.
- `acceptance_criteria = (AC.PO.1, AC.PO.2)` — see §A.2 below.

The single caveat: **there is no `lifted_from` / source-document
pointer field on the spec**. The current schema has nowhere to record
"this objective record was extracted from VALUE_PROPOSITION.md
section X" or "this objective record corresponds to amendment
plan-doc Y, AC `AC-D7.3`." That provenance is what makes plan-docs-
as-projections work bidirectionally and lets the migration be
re-runnable / verifiable. See §B.3 below.

### A.2 Do the four criterion variants cover AC.PO.1 and AC.PO.2?

**Yes, via the `prose` variant — which the schema already treats as a
first-class evaluation kind.**

The four variants (`spec.py` lines 110–164):

- `prose` — free-text criterion; caller-dispatched evaluation.
- `scope_success` — pointer at a scope; auto-evaluates.
- `child_closure` — N-of-M children achieved.
- `external_predicate` — registered predicate evaluated externally.

AC.PO.1 ("translation burden reduced") and AC.PO.2 ("toolkit
expanded") are qualitative — they cannot be deterministically machine-
evaluated. The `ProseCriterion` shape is exactly the variant authored
for this case. The proposal is explicit (proposal.md §"Criterion
discriminated union"): "prose — free-text descriptive criterion
(evaluated manually or by LLM)." `evaluate_criterion` accepts results
from any caller including LLM harnesses (`runtime.py` lines 383–434).

A `child_closure` criterion could *also* be added on the root —
"AC.PO.2 is met when ≥ N of the harness-toolkit child objectives have
reached `achieved`" — which would give the value prop a partial
automated-evaluation surface alongside its prose form. This is an
additive design choice for the proposal, not a schema gap.

**No new criterion variant is required.** The prose variant fits.

### A.3 Depth/breadth of the implied hierarchy

The deepest path under the locked rulings:

```
VALUE_PROPOSITION (root, user)
  └─ spec v1.0 / v1.1 / v1.2 phase objective (user)
      └─ sealed component objective, e.g. memory-system (user)
          └─ component AC, e.g. memory D1 (user)
              └─ amendment AC extending D1, e.g. AC34.x (user)
                  └─ test_function backing the AC (user/odd-harness)
```

That's six levels. Walking the runtime: `trace_to_root()` at
`runtime.py:599` walks parent-pointers iteratively with a `visited`
set for cycle detection — there is no recursion-depth limit and no
breadth limit. SQLite's `objective_state` table indexes on
`parent_id` (`store.py:51`), so child enumeration is an indexed
lookup at every level. `list_by_root()` (`runtime.py:558`) walks the
full descendant set with an iterative DFS using a stack and a
`visited: set[str]` — no recursion-depth issue.

**Depth is fine.** Breadth is fine for the cardinalities at issue
(see §A.5 below).

Cycle prevention: `create()` rejects only the trivial self-parent
case (`runtime.py:134`). The proposal flags this as deliberate — a
new objective cannot be ancestor of its parent because it didn't
exist before the call. `trace_to_root()` raises `DAGRejected` if a
cycle is encountered on read. Under Heavy-B, this is the right shape
— the migration tooling cannot accidentally introduce cycles
because every record is created with a parent that already exists.

### A.4 Authored_by provenance

The schema records `authored_by` as a free string with no validation
against any registry (`spec.py:240–242`, proposal assumption #1
confirmed in Luke's decisions). This matches the locked ruling that
sub-objectives are "mostly user (Luke's spec authoring) but some may
be the primary persona's inferences."

For the migration, the provenance discipline is:

- Records lifted from `VALUE_PROPOSITION.md`, `pos-v2-objectives-spec.md`
  v1.0/v1.1/v1.2, and the 13 sealed component proposals → `"user"`
  (Luke authored those documents).
- Records lifted from amendment plan docs → `"user"` if the
  amendment plan was authored or approved by Luke (the dominant case
  in `docs/rebuild/plans/amendment-*.md`); `"primary-persona"` (or a
  more specific handle) if the amendment was authored by an agent on
  Luke's behalf and approved retroactively.
- Records lifted from research/foundation-audit findings that turned
  into ACs → whichever actor authored the AC text in the source
  artefact.

The schema tracks this cleanly. **No provenance-model change
required.**

### A.5 Cardinality / scale

Order-of-magnitude record count for the post-migration tree:

| Tier | Source | Approx record count |
|------|--------|---------------------|
| 0 — root | VALUE_PROPOSITION | 1 |
| 1 — spec versions / phases | spec v1.0/v1.1/v1.2 + 4 phases | 7–10 |
| 2 — sealed components | 13 sealed components | 13 |
| 3 — component proposal ACs | safety-layer A1–A20, memory D1–D9, scope-of-work, etc. | ≈ 130–200 |
| 4 — amendment ACs | 26 amendment-*.md plan files × ~4–6 ACs each (counted: ≈ 51 AC headers across all amendment plans) | ≈ 51–100 |
| 5 — test functions backing ACs | ~ one test func per AC | ≈ 250–350 |

Total: **on the order of 500–700 ObjectiveSpec records** at full
migration, plus an event-log row per state transition (initial create
+ start + criterion evaluation + scope-bind events). The SQLite event
log is sized for ≤10⁴ events/year per the proposal §"Persistence";
500 records ingested in one migration produce ~500 `objective_created`
events plus ~500 `start` transitions plus criterion evaluations.

**Initial event log size: ≈ 1500–3000 events.** That's well under the
10⁴/year design target and well under SQLite's practical write-burst
ceiling. No scale concern.

The `objective_state` projection table is row-per-objective; ~700
rows is trivial. The `list_by_root()` DFS over 700 records with a
fan-out under 50 is sub-millisecond. **Scale is fine.**

### A.6 Schema fit — summary

- Schema accommodates the root + AC.PO.1/2 prose criteria as-is.
- Schema accommodates the depth (6 levels typical, no recursion
  limit).
- Schema accommodates the breadth (~700 records, well under design
  target).
- One structural gap surfaces under Heavy-B: **no field carries
  back-pointer provenance to the source document** (the markdown
  section, the amendment plan, the proposal AC). That gap is the
  load-bearing piece for "plan docs become projections of tracker
  state, not the source." See §B.3 for migration mechanics that
  handle this and §Decisions D-1 for the schema-widening question.

---

## B — Migration mechanics

### B.1 How is the corpus extracted into ObjectiveSpec records?

**Recommended shape: hybrid extractor + manual seeding.**

Three plausible shapes evaluated against the corpus structure:

**Shape 1 — Fully automated extraction** (parse markdown headers,
AC IDs, reach into proposals via regex). Rejected because the corpus
is not uniform — VALUE_PROPOSITION.md has prose; the spec doc has
v1.0 lock + addenda; component proposals follow a five-gate format
but vary; amendment plans have Au-D7.x or AC29.5 or AC-D7.S
identifiers with inconsistent prefixes. A pure extractor would either
miss records or mis-shape them, and it would not capture the
authored_by provenance reliably (e.g. an amendment plan authored by
an agent vs Luke).

**Shape 2 — Fully manual seeding** (someone authors each ObjectiveSpec
record by hand with the correct goal, parent_id, time_bound, criteria,
authored_by). Rejected because of cardinality — 500–700 records by
hand is multi-week ceremony work, error-prone, and explicitly the
shape "writing plan files" is on the main-session allowlist for
*authoring*, but **multi-artefact authoring "ALWAYS go to background
agents"** per Luke's auto-memory `feedback_background_default_for_authoring`.
Six hundred individual records is the worst case of multi-artefact
authoring.

**Shape 3 — Hybrid (RECOMMENDED).** Two mechanical paths plus one
manual path:

1. **Automated extractor** for the well-structured content:
   - Component proposals where AC IDs follow the conventional shape
     (A1–A20, D1–D9, B18–B25, etc.) — extract via section-header
     parsing, lift into `ObjectiveSpec` records with `parent_id` set
     to the parent component objective, `acceptance_criteria` as
     `prose` variants citing the AC text verbatim, `authored_by =
     "user"`, `time_bound` defaulted to evergreen with
     `review_cadence = "amendment-driven"` (the AC is alive until
     the component reseals or an amendment supersedes it).
   - Amendment plan docs that follow the post-amendment-#22 layout
     (every plan file from amendment-22 onward has structured AC
     sections, behaviour-count tables, and seal-diff discipline
     blocks).
   - Test files where `test_<ID>_*` names match a known AC.
2. **Manual seeding** for the root + close-to-root nodes:
   - The `VALUE_PROPOSITION` root itself, with `prose` criteria
     transcribed from the document's Primary-persona test and Harness
     test sections (ipsis verbis from VALUE_PROPOSITION.md lines
     58–69 — "Does this reduce the translation burden..." and "Does
     this add to the toolkit...").
   - The spec v1.0/v1.1/v1.2 phase objectives — these are
     prose-shaped goals that benefit from human authorship to land
     the right `goal` string.
   - The sealed component roots (one per component) — phrasing
     should match the existing component proposal §"Summary" lines
     where possible, to preserve human-readability when projected.
   - ODD methodology adoption objective (§A.6 maps it as a
     dev-discipline objective, not a sealed-component objective).
3. **Build-time seeding for the dev CDCs.** Each Core Development
   Convention in `FUTURE_IDEAS.md` is itself an objective under the
   value prop's "harness toolkit" branch (per locked ruling #4). The
   CDC body becomes the goal text; the rationale becomes the prose
   criterion; `time_bound = evergreen`. Manual seeding because the
   CDC bodies are hand-authored prose and the structural pattern
   isn't regular.

**Bound on the work:** ~700 records total. Automated extraction
covers ~70% (the 13 component proposals + 26 amendment plans + ~250
test functions); manual seeding covers ~30% (the root, the spec
phases, the CDCs, the foundation-audit findings). Estimated wall-
clock for the migration build: 1–2 days of background-agent work for
the extractor + 1 day of manual seeding (delegable to a background
authoring agent against a structured seeding manifest).

### B.2 Big-bang vs incremental

**Recommended: phased, not big-bang.** Three phases:

- **Phase α: Root + spec + components.** Manually seed the root, the
  spec phases, and the 13 component objectives. ~30 records.
  Validates the schema fit empirically.
- **Phase β: Component AC backfill.** Automated extractor populates
  the ~130–200 component ACs. The migration is now load-bearing for
  **new** amendments (any amendment after this lands must register
  ObjectiveSpec records as part of its bookkeeping; the pos-amend
  CLI changes are part of this phase).
- **Phase γ: Amendment AC backfill.** Automated extractor lifts the
  ~51–100 amendment ACs. Test-function backing pointers added in a
  scripted second pass.

ODD methodology §2.5 is the relevant lens: "build only what the
objectives require." A big-bang seeding amendment would author 700
records in one commit, which is the same scope-creep failure mode
§2.5 names. Phasing the migration matches §4 re-extension — each
phase is a discrete amendment with its own ACs (e.g. "Phase α: 30
manually-seeded records persist correctly through restart") and the
work landed in that phase is exactly what its ACs verify.

The companion question: **do legacy plan-docs get back-extracted?**
Two options surface under §4 re-extension precedent:

- **(a) Back-extract:** every amendment plan from #1 onwards becomes
  ObjectiveSpec records, the existing test functions are bound to
  them. Complete coverage, but produces records for completed,
  sealed work that can never be re-evaluated. Cost: extractor must
  handle pre-amendment-#22 plans whose structure was not standardised.
- **(b) Cutoff date:** records exist only for amendments after a
  declared cutoff (e.g. amendment N onwards). Pre-cutoff amendments
  remain as plan docs only. Lower migration cost; loses retroactive
  Heavy-B coverage of legacy ACs.

**Recommendation: (a), with the extractor authored leniently** (best-
effort parsing of pre-#22 plans, and any plan that fails extraction
gets manually seeded as a single objective-per-plan placeholder with
a prose criterion citing the file path). This matches the locked
ruling #4 ("everything else descends from the value prop") — partial
back-extraction creates a tree where some sealed components are
fully lifted and others are stubs, which is the failure mode §2.5's
audit-finding-triage CDC was authored against.

### B.3 Idempotency and primary key

The migration must be re-runnable without producing duplicate
records. The natural primary key for "amendment #29 AC29.5" is the
**(source-document path, AC identifier within that document)** pair.

The current schema does not carry these. The `objective_id` is a
caller-supplied UUID (or auto-generated `obj-<uuid>`); there is no
deterministic key. Two paths forward:

- **Caller-supplied stable IDs.** The migration script computes a
  deterministic ID like `obj-amend-29-ac29.5` and passes it to
  `create()`'s `objective_id=` param (`runtime.py:121` accepts this).
  Re-running the script: `create()` would write a duplicate
  `objective_created` event because the existence check at
  `runtime.py:147` (`read_state(...) is None and not events_for(...)`)
  is on the *parent_id*, not the new ID. **Gap.** A re-run must check
  whether the objective ID already has events and skip.
- **Schema widening.** Add a `lifted_from` field — `Optional[dict]`
  with `{source_doc: str, source_ac: str, source_commit: str}`. The
  migration becomes idempotent because the script can query
  `list(authored_by="user")` and skip any record whose `lifted_from`
  matches.

Recommended: **schema widening.** Reasons:

- `lifted_from` is structurally meaningful for plan-docs-as-
  projections: when the projection renderer walks the tracker to
  produce `docs/rebuild/plans/amendment-29-*.md`, it groups records
  by `lifted_from.source_doc`. Without this field, the projection
  has to reverse-engineer the grouping from prose conventions.
- It makes the migration auditable from outside: `lifted_from` rows
  in the `objective_state` table prove which records came from
  which document, satisfying the §3.1 deterministic-check property.
- It's additive (the field is `Optional`); existing records stay
  valid.

This is the schema change behind §Decisions D-1.

### B.4 Migration mechanics — summary

- Hybrid extractor + manual seeding; ~700 records total.
- Phased build (α: root + spec + components; β: component ACs;
  γ: amendment ACs + test bindings).
- Back-extract legacy plans best-effort; un-extractable plans get
  one-record-per-plan placeholders with prose criteria.
- Schema gains a `lifted_from` provenance pointer for idempotency
  and projection grouping. **§Decisions D-1.**

---

## C — Component-amendment sequence

### C.1 Which sealed components must be amended?

The minimum amendment set the research surfaces:

1. **objective-tracker.** Required IF the schema needs widening for
   `lifted_from`. The widening is additive (new optional field,
   existing tests pass), but the tracker is sealed and the change is
   structural so it goes through the amendment cycle. The tracker
   also gains a thin `query_projection_view(filter)` API for
   plan-doc rendering (see §D below) — this is the ODD-aligned
   shape because the renderer does not need a new mechanism, just a
   query surface that's currently latent in `list_by_root()`.

2. **pos-amend.** Required. The CLI today widens `BASELINE`, manages
   `allowed_prefixes`/`allowed_files`, advances `SEAL_COMMIT`
   sidecars, and appends narratives (`tools/pos-amend/README.md` §
   "Subcommand surface"). Heavy-B adds: every `pos-amend apply`
   run registers ObjectiveSpec records for the amendment's
   declared ACs against the existing tree (idempotent via
   `lifted_from`). `pos-amend seal` writes a `lifted_from.source_commit`
   field so the projection can show "this AC sealed at commit X."

3. **primary-persona.** Required for Lens 2 win. The persona
   layer's contributor registry (introduced by amendment #33's
   D7 / amendment #32's D8) is the natural seam to add a
   `tracker-context` contributor that surfaces "what objectives
   are in flight under the workspace" on `SessionStart` or
   `UserPromptSubmit`. Without this, the tracker is data-on-disk
   that the persona cannot reach — the harness test fails (per
   `VALUE_PROPOSITION.md`: "A capability that cannot be invoked
   by the primary persona is a capability outside the harness").

4. **workspace-bootstrap.** Required, but the work is small. The
   first-run scaffold needs to produce a tracker DB seeded with
   the value-prop root and immediate descendants. **There is a
   tension here with the "zero personas / zero content" governing
   rule** — see §F.4 and §Decisions D-4.

The research did NOT find a hard requirement for amendment to:

- scope-of-work — no schema change; D6 already exists; the binding
  sidecar already enforces the user-authored-root invariant.
- self-correction — already subscribes to abandonment events; no
  schema change.
- memory-system — orthogonal; the tracker does not feed the memory
  graph.
- safety-layer / cost-governance / reversibility / observability /
  graceful-degradation / self-upgrade / session-resilient-
  orchestrator / hands-off-lifecycle — orthogonal.

**Total sealed-component amendments: 4.** Plus dev-discipline
updates (CLAUDE.md, FUTURE_IDEAS.md CDC blocks) which are NOT
sealed-component amendments per CLAUDE.md operational caution §2.5.

### C.2 Dependency order

```
1. objective-tracker schema widening (lifted_from) + query API
        ↓
2. pos-amend integration (registers ObjectiveSpec on amendment commit)
        ↓
3. workspace-bootstrap first-run seed (value-prop root + spec + components)
        ↓
4. primary-persona contributor (tracker-context on UserPromptSubmit / SessionStart)
        ↓
5. Phase α / β / γ migration amendments (records seeded, projection
   renderer authored as a tool)
```

Step 1 unblocks 2; step 2 unblocks 3 (because workspace-bootstrap's
first-run uses the new schema); steps 3 and 4 are parallelisable
once 2 lands. The migration phases are not themselves
sealed-component amendments — they are dev-discipline data work
that consumes the amended primitives.

### C.3 Dev-discipline vs sealed-component split

CLAUDE.md operational caution §2.5: "Before scoping anything as a
sealed-component amendment, name the specific spec objective
(v1.0/v1.1/v1.2) the code will satisfy. If I can't name one, the
work is dev-discipline (CLAUDE.md, docs, CDCs, tools/), not a
sealed-component cycle."

Mapping:

| Work | Spec objective satisfied | Class |
|------|---|---|
| objective-tracker schema widening | v1.0 Objective primitive (parentage, criterion, time-bound); v1.1 R1 (semantic round-trip preserved) | sealed-component amendment |
| pos-amend integration | (no spec objective) | dev-discipline (`tools/`) |
| workspace-bootstrap first-run seed | v1.0 Architectural — "no workflow / task / scope without objective trace"; this primitive is what enforces it for dev work | sealed-component amendment |
| primary-persona contributor | v1.2 R14 (autonomous authoring of specialist personas) is adjacent; v1.1 R13 (channel-agnostic interaction) is the interactive-channel parent — but the *fit* is for the harness test, not a single spec line. **Borderline.** | sealed-component amendment if a spec objective can be named; dev-discipline otherwise |
| Phase α/β/γ data migration | (no spec objective) | dev-discipline |
| CDC updates (plan-before-code → register-objectives-before-code) | (no spec objective) | dev-discipline |

The primary-persona work is **borderline** under §2.5 — it satisfies
the harness test (Lens 2) cleanly, but no single spec objective
maps. Two paths: (a) authoring a v1.3 addendum to the spec naming
"the persona has access to the objective tree as a tool" as a new
clause under R14/R15; (b) doing the work as dev-discipline. **§Decisions D-2.**

### C.4 Component-amendment sequence — summary

- 4 sealed-component amendments minimum
  (objective-tracker, pos-amend [if ruled sealed], workspace-
  bootstrap, primary-persona [if ruled sealed]). Pos-amend lives
  in `tools/`, so the strict reading puts it as dev-discipline
  even though it carries an apply --dry-run hard prereq.
- Schema widening ships first; consumers integrate after.
- Primary-persona inclusion is a §2.5 borderline decision.

---

## D — Doc-as-projection

### D.1 What gets rendered, when, by whom?

**Recommended shape: a `pos-amend project` (or `loam project`)
subcommand renders plan docs on demand from tracker state.** Reasons:

- `pos-amend` already owns the dispatch-layer surface for amendments
  (manifest, BASELINE, sidecars, narratives). Adding `project` to
  the same CLI keeps the dev tooling cohesive.
- Lens 1 (Claude-leverage): Claude's hook events (the SessionStart
  hook used by amendment #32) can be configured to run `pos-amend
  project --check` at session start to verify the on-disk plan
  docs match the projected output, surfacing drift as a structured
  warning. This is a structural-over-advisory pattern that matches
  ODD §5.
- The render pass is pure (tracker DB → markdown), so it composes
  with `subprocess.check_call` from any harness.

Auto-rendering on file-read is rejected — file-read is a hot path
and the render is non-trivial (700 records into a 26-amendment doc
set).

The query API the projector consumes:

```
tracker.list_by_root(root_id, ...) → walk descendants
tracker.get(objective_id)           → resolve any node
trace_to_root(...)                  → ancestor chain
list(authored_by=..., lifted_from_doc=...) → grouped by source doc
```

The first three already exist (`runtime.py:558`, `:527`, `:599`).
The fourth needs a small extension: filter by `lifted_from.source_doc`
once the field lands.

### D.2 What about legacy plan docs that already exist?

**Recommended: legacy plans stay as historical artefacts; only NEW
plans are projected.**

The ODD §4 re-extension precedent supports this: prior amendments
preserve their authored shape; new work follows the new mechanism.
Concretely:

- A "legacy" plan is one authored before the projector lands.
- A "new" plan is one whose ACs are authored as ObjectiveSpec records
  first (in tracker), then projected to disk via `pos-amend project`.
- The projector writes only files that don't yet exist OR files
  whose tracker-derived content differs from the on-disk content
  (drift detection).
- Migration phase γ back-extracts legacy plans into ObjectiveSpec
  records, but the projector does NOT overwrite the legacy file
  unless explicitly invoked with `--rebuild-legacy`. This preserves
  audit-trail integrity.

Alternative considered and rejected: rebuild every plan doc from
projection on every render. Rejected because (a) it would erase
human-authored prose subtleties in legacy plans (e.g. amendment-23's
detailed BASELINE-frozen rationale is plan-doc prose, not AC-shaped
content), and (b) git diffs would be enormous and meaningless.

### D.3 The spec doc

`pos-v2-objectives-spec.md` v1.0 is locked ("v1.0 LOCKED 2026-04-17
16:31 CDT; v1.0 text below is preserved unchanged per the lock
rule"). The v1.1 and v1.2 addenda are also locked.

**Recommended: the spec doc stays authored, NOT projected.**
Reasons:

- The lock rule is structural — the doc body is preserved
  unchanged; later addenda are appended. A projection that
  rewrote the doc would violate the lock.
- The spec doc carries prose that supplies context for the AC
  list (e.g. the addendum-explanation prose at the top of v1.1).
  That prose is human-authored and not extractable from the tree.
- The spec doc IS, however, the *source* the migration extractor
  reads to seed the spec-tier objectives.

Future spec versions (v1.3+, if landed) follow the same pattern:
authored as markdown, then extracted into ObjectiveSpec records by
the migration tooling.

### D.4 Doc-as-projection — summary

- New `pos-amend project` subcommand renders plan docs on demand.
- Legacy plans stay as artefacts; only NEW plans are projected.
- Spec doc stays authored, not projected (lock rule).

---

## E — Workflow integration

### E.1 Plan-before-code CDC under Heavy-B

The CDC today (FUTURE_IDEAS.md): "Plans live at
`docs/rebuild/plans/<work-item-name>.md`. Plan writes-to-disk
happen before any source edit."

Under Heavy-B, the CDC mutates to:

> "Register ObjectiveSpec records before any source edit;
> projection of the plan doc (if needed for human review) is
> rendered from the tracker state via `pos-amend project`."

The substance is preserved (no source edit without a contract
naming the ACs the source satisfies); the mechanism shifts (the
contract's primary form is tracker records, not markdown).

### E.2 Are the dev CDCs themselves objectives in the tree?

**Yes, per locked ruling #4.** Each CDC body becomes an objective
under a "harness toolkit / dev disciplines" branch under the value
prop. Concretely:

- "plan-before-code" → objective with `goal = "every build writes
  a plan to the tracker before any source edit"` and a prose
  criterion citing the rationale paragraph.
- "scope-only-dispatch" → objective with `goal = "a dispatch from
  delegator to builder carries scope only, never method"`.
- All-execution-through-background-agents, etc. — same shape.

This makes the CDCs structurally enforceable rather than advisory
(ODD §5.1) — a future amendment-time check could verify that every
sealed-component build has a corresponding ObjectiveSpec under the
plan-before-code branch. **Lens 3 alignment.**

### E.3 pos-amend integration mechanics

Two questions: (a) does the integration require an objective-tracker
amendment, or just a pos-amend amendment? (b) what's the registration
surface?

(a) — depends on §A.6 schema widening:
- If the schema gains `lifted_from` (recommended), objective-tracker
  amendment lands first. pos-amend amendment lands second.
- If the schema stays as-is, pos-amend can register records using
  caller-supplied stable IDs (`obj-amend-29-ac29.5` shape) and skip
  via existing-events check — but loses the projection grouping
  property (§D.1 needs `lifted_from` to render plan-grouped output).

(b) — pos-amend's manifest schema (v1) gets a v2 addition: an
`objectives` block listing the amendment's declared ACs in
ObjectiveSpec shape. `pos-amend apply` parses the block and calls
`tracker.create(...)` for each missing record. `pos-amend seal`
updates `lifted_from.source_commit` on each record. This is a
schema-version bump per the README's "Schema-version compatibility"
clause.

### E.4 Workflow integration — summary

- Plan-before-code CDC mutates to register-objectives-before-code.
- All CDCs become objectives under the harness-toolkit branch
  (Lens 3 win — structural enforcement).
- pos-amend's manifest schema gains an `objectives` block;
  schema-version bumps to v2.

---

## F — Risks

### F.1 Tracker as single point of failure

**Risk:** if the tracker DB is corrupted, lost, or unreachable, the
harness-toolkit branch under the value prop becomes unreliable —
AC.PO.2 is at risk.

**Mitigation surfaces in the existing component:**

- Event-sourced persistence (`runtime.py` + `store.py`) — the event
  log is the source of truth; the projection cache is rebuildable
  from events.
- D8 upgrade-fidelity harness already captures pre/post probe sets
  and verifies semantic round-trip.
- SQLite WAL mode is configured (`store.py:89`) — write-ahead
  logging gives crash-consistency guarantees.
- `snapshot_to(target_path)` (`store.py:263`) does a `VACUUM INTO`
  — physical-reversibility snapshots are cheap.

Additional mitigation Heavy-B should add:
- Daily snapshot to a workspace-local `.scratch/tracker-snapshot.db`
  (the gitignored `.scratch/` directory exists per CLAUDE.md
  output-conventions section).
- Drift report surfaced via the persona's UserPromptSubmit
  contributor — if the tracker fails health-check, the persona
  surfaces it to the user before any tracker-dependent operation.

### F.2 Plan-doc drift

**Risk:** projected plan docs drift from tracker state if the
renderer is buggy or stale.

**Mitigation:**
- `pos-amend project --check` exits non-zero on drift; runs as part
  of `pos-amend apply --dry-run` (already a hard prereq for
  amendment commits per amendment #22).
- The projector is deterministic (tracker DB → markdown); a golden-
  file test in `tools/pos-amend/tests/` catches regressions.

### F.3 Migration produces a giant initial event log

**Discussed in §A.5.** ~1500–3000 events for the full migration is
well under the 10⁴/year design target. **Not a concern.**

### F.4 Workspace-bootstrap composability — the "zero content" tension

**Risk surface:** STATE.md rule #4 — "pOS core ships zero personas.
Primary-persona primitive is contract + loader + validator;
workspaces supply the content." The same governing rule extends by
analogy: pOS core ships zero objective content; workspaces supply
their own.

But the locked ruling #5 says: "future workspace-user objectives
slot under the same root." The root IS the value prop — which is
pOS-core content (the document is in `docs/rebuild/VALUE_PROPOSITION.md`).
**Tension.**

Two resolutions:

- **(a) Resolution by separation-of-concerns.** The pOS-core
  objective-tracker ships an empty DB. Workspace-bootstrap's
  first-run scaffold (a workspace concern, not a core concern) seeds
  the value-prop root and dev-tier descendants ONLY for workspaces
  that are *pos-v2 dev workspaces*. A pos-v2-derived workspace
  (memory-system runtime, primary-persona runtime, etc.) bootstraps
  its OWN root authored by its own user. Two trees, not one. This
  contradicts locked ruling #5.

- **(b) Resolution by re-reading ruling #5.** Re-read: "future
  workspace-user objectives slot under the same root." The "same
  root" is the workspace-user's own value prop — which they author
  themselves at first-run. The pos-v2 dev workspace happens to have
  Luke's value prop as its root because Luke is the pos-v2 dev
  user. A different workspace has a different user; that user's
  value prop is THEIR root.

**(b) is the consistent reading.** Under (b):
- pos-v2 core ships NO objective content.
- workspace-bootstrap's first-run prompts the user (or templates)
  for their value prop, seeds it as the root with `authored_by =
  "user"`, and seeds dev-tier descendants (the CDCs, the plan-
  before-code mechanism, the spec versions) only IF the workspace
  is configured as a pos-v2 dev workspace.
- pos-v2 dev workspaces (this workspace, the `loam` rename target,
  the future evaluation workspace) have a seeded dev-tier sub-tree;
  derived workspaces have only their own root.

**This shape preserves both ruling #4 (zero core content) and
ruling #5 (single tree).** §Decisions D-4 surfaces it for the
owner's confirmation since the reading depends on which "user" the
ruling references.

### F.5 The chicken-and-egg problem

**Risk:** the migration amendment(s) need ACs in the tracker to be
ODD-compliant under §2.5, but the tracker doesn't have the value-
prop root before the migration runs.

**Resolution:** the first migration amendment (Phase α) seeds the
root manually as part of its build. Its own ACs cite the
just-created root as their parent — which is fine because
`tracker.create()` accepts a parent_id that exists (the root is
created in the same migration script before the amendment ACs).
The amendment's ACs are thus authored against records they
themselves seeded. This is unusual but not contradictory: the
amendment's ACs are tested against the tracker state *after* the
seed runs, not against the tracker state before.

The secondary risk: Phase α's ACs are not retroactively in the
tree before Phase α runs. The fix is identical to how the first-
run pattern handles bootstrap — the amendment plan describes the
ACs in the plan doc (today's mechanism), AND the seed script
registers them on first run. After Phase α, all subsequent
amendments use the new mechanism (objectives-first) exclusively.

### F.6 Risks — summary

- Tracker SPOF mitigated by existing event-sourcing + D8 + WAL +
  snapshots; add daily snapshot + persona-surfaced health.
- Plan-doc drift mitigated by `--check` exit code in pos-amend
  apply --dry-run.
- Initial event-log size is fine.
- Workspace-bootstrap composability is consistent under reading
  (b) of ruling #5; surfaced as **§Decisions D-4** for the owner.
- Chicken-and-egg resolved by Phase α's seed script running
  before its own AC tests run.

---

## G — ODD methodology coherence

### G.1 §10 BASELINE convention

Heavy-B touches multiple sealed components in a coordinated way
(objective-tracker schema, possibly pos-amend, workspace-
bootstrap, possibly primary-persona). The §10 distinction:

- **Frozen BASELINE** — for cumulative-admissibility checks. e.g.
  hands-off-lifecycle's H19. NOT relevant here; the migration is
  not a project-wide whole-repo invariant.
- **Floating BASELINE** — for per-component contamination checks.
  Each affected sealed component advances its own BASELINE on each
  amendment touching it. **This is the right pattern for Heavy-B's
  sealed-component amendments.**
- **Per-invariant BASELINE** — for point-in-time invariant proofs.
  e.g. the Phase α "value-prop root and 30 spec/component records
  exist post-seed" invariant could ship as a per-invariant pinned
  pair (`amendment_α_baseline` + `amendment_α_seal`) so subsequent
  Phase β / γ amendments don't widen the diff window for the
  Phase α proof.

Recommendation: **per-invariant pins on phase-α through γ
invariants; floating BASELINE on the underlying sealed
components.** This is the same shape amendment #21 used for AC7 on
telegram-interface (cited in `odd-in-pos.md` §10.3).

### G.2 §2.5 reverse direction under Heavy-B

§2.5 today: "for every code block, every branch, every dependency,
every test, point at the acceptance criterion it satisfies."

Under Heavy-B, this becomes structurally enforceable: every code
file in a sealed-component diff has a backing ObjectiveSpec record
(via `lifted_from.source_doc + source_ac` pointing at the AC the
file satisfies). A new audit tool (`pos-amend audit-coverage`)
walks the diff and queries the tracker for backing — no backing,
no merge.

**Migration friction:** code that pre-dates the tracker is
currently AC-backed via plan docs only. Phase γ's back-extraction
gives that code its tracker record. Until Phase γ completes, the
audit tool runs in "warn-only" mode. This is the Lens 3 win the
locked rulings imply but don't name explicitly.

### G.3 §4 re-extension under Heavy-B

§4 today: a builder discovers a gap, promotes it to a new
acceptance criterion in the proposal, writes a test, cites the
rationale.

Under Heavy-B: same flow, but the new criterion goes into the
tracker first (via `tracker.create()` with `parent_id` pointing at
the relevant ancestor), then projection renders the updated plan
doc. The audit trail lives in the tracker's event log
(`objective_created` event with `lifted_from.source_commit` =
the commit that re-extended). This is *better* than today's prose-
audit pattern because the re-extension event is queryable.

### G.4 ODD coherence — summary

- §10: floating BASELINE on sealed-component amendments;
  per-invariant pins on phase-α/β/γ invariants.
- §2.5: structurally enforceable post-migration via
  `pos-amend audit-coverage`; warn-only until Phase γ completes.
- §4: re-extension event lives in the tracker's event log;
  audit trail improves.

---

## H — Lens trace

Every recommendation traces upward to AC.PO.1 (translation-burden
reduction) or AC.PO.2 (toolkit expansion).

| Recommendation | AC.PO.1 trace | AC.PO.2 trace |
|---|---|---|
| `lifted_from` schema widening | — (internal) | The tracker becomes a queryable surface the persona can compose with — toolkit expanded. |
| Hybrid extractor + manual seeding migration | The user no longer translates "what is amendment-29 verifying" into a memory of which plan doc to read; the persona queries the tree directly. | Tree-walk becomes a tool the persona invokes — toolkit expanded. |
| `pos-amend project` subcommand | The user reads a plan doc when they want to; the doc is always current with tracker state — translation burden of "is this plan doc stale" disappears. | The renderer is part of the persona's toolkit. |
| Primary-persona contributor | The persona surfaces in-flight objectives at session start without the user asking — translation burden of "what was I working on" disappears. | Direct addition to persona's toolkit. |
| Phased migration | The user is not surprised by tracker state at any phase; phases land discretely with their own ACs — translation burden of "what state is the migration in" is structural, not prose-tracked. | Each phase adds a queryable surface. |
| Floating BASELINE per amendment + per-invariant pins on phases | — (internal) | Audit tooling can verify cleanly; toolkit reliability up. |
| `pos-amend audit-coverage` (post-Phase γ) | Translation-burden of "is this code AC-backed?" disappears — the tool answers. | Direct addition to dev-discipline toolkit. |

Every recommendation passes the trace.

---

## Halt-and-surface findings

The research did not turn up evidence requiring re-litigation of any
locked ruling. The schema fits with one widening; migration is
tractable in 4 sealed amendments + dev-discipline; risks are
manageable. **No halt triggers fired.**

One observed but non-blocking finding: the `pos-amend` tool lives
in `tools/`, which by CLAUDE.md operational caution §2.5 is
dev-discipline territory. Heavy-B's pos-amend integration is thus
arguably dev-discipline rather than a sealed-component amendment,
which would lower the "minimum 4 sealed amendments" count by one.
This is a §2.5 reading question rather than a halt. **Surfaced as
§Decisions D-3.**

The research observed but did NOT halt on: the borderline §2.5
question for the primary-persona contributor (surfaced as
**§Decisions D-2**) and the workspace-bootstrap "zero core content"
tension (surfaced as **§Decisions D-4**).

---

## Decisions for the owner to rule on

Six decisions surfaced. Each carries a recommendation, one-line
rationale, and lens trace.

### D-1 — Schema widening: add `lifted_from` provenance pointer?

**Question:** add `lifted_from: Optional[dict]` to `ObjectiveSpec`
to carry source-document/source-AC/source-commit pointers, OR keep
the schema as-is and rely on caller-supplied stable IDs for
idempotency.

**Recommendation:** **add `lifted_from`.**

**Rationale:** without it, the projection cannot group records by
source doc; idempotency relies on a brittle ID convention; audit
of "which records came from which document" requires reverse-
engineering. Additive change, existing tests pass.

**Lens trace:** AC.PO.2 (toolkit reliability — the projection is
the persona's tool for plan-doc rendering and needs to be
deterministic).

### D-2 — Primary-persona contributor: sealed-component amendment or dev-discipline?

**Question:** the primary-persona layer needs a `tracker-context`
contributor on `UserPromptSubmit` / `SessionStart`. Under §2.5, no
single spec objective names "the persona reads the tracker tree."
Path (a): land a v1.3 spec addendum naming the clause; ship the
contributor as a sealed-component amendment. Path (b): ship the
contributor as dev-discipline, no spec addendum; the persona's
contributor registry is method-shaped enough that the addition
isn't load-bearing for the spec's structural surface.

**Recommendation:** **Path (a).** Author a v1.3 addendum naming
"the persona has read access to the workspace's objective tree as
a session-start primitive." Ship as a sealed-component amendment.

**Rationale:** the contributor IS the harness-test win for Heavy-B
(Lens 2) — without it, the tracker is data-on-disk the persona
cannot reach. That's the kind of property the spec was authored to
contain. Dev-discipline is for tooling that doesn't have a spec
shape; this has one.

**Lens trace:** AC.PO.1 (the persona surfaces in-flight objectives
without the user asking — translation burden down) AND AC.PO.2
(direct toolkit expansion).

### D-3 — pos-amend integration: sealed-component or dev-discipline?

**Question:** pos-amend's tracker integration (the `objectives`
manifest block, the `pos-amend project` subcommand, the
`audit-coverage` subcommand) lives under `tools/`. Under CLAUDE.md
operational caution §2.5, `tools/` is dev-discipline territory.
But pos-amend has a hard prereq for amendment commits (`apply
--dry-run` green) and is thus load-bearing for the sealed-component
amendment cycle.

**Recommendation:** **dev-discipline, with pos-amend's manifest
schema-version bump treated as a CDC-level commitment.**

**Rationale:** §2.5's reading is "no spec objective named, no
sealed-component amendment." pos-amend doesn't have a spec
objective; its load-bearing-ness is operational, not specified.
This matches how amendment #22 itself was treated.

**Lens trace:** AC.PO.2 (toolkit expansion via dev-discipline).

### D-4 — workspace-bootstrap seed: who owns the value-prop root in derived workspaces?

**Question:** STATE.md rule #4 says pOS core ships zero personas /
zero content. Locked ruling #5 says future workspace-user
objectives slot under "the same root." Reading (a): the root is
Luke's value prop; pOS core ships it with the workspace-bootstrap
seed. Reading (b): the root is "whatever value prop the workspace
user authors at first-run"; pos-v2 dev workspaces happen to have
Luke's because Luke is the dev user; derived workspaces have
their user's.

**Recommendation:** **Reading (b).** workspace-bootstrap's first-
run prompts (or templates) the user for a value-prop statement.
pos-v2 dev workspaces are a special case where the value prop is
templated to Luke's text from VALUE_PROPOSITION.md (which lives in
docs, not in the bootstrap-seed payload).

**Rationale:** preserves both rule #4 (zero core content) and
ruling #5 (single tree per workspace, with the workspace-user as
the root author). Avoids the violating-rule-#4 path of shipping
Luke's value-prop content as a hard-coded scaffold.

**Lens trace:** AC.PO.2 (the tracker is workspace-portable —
toolkit expansion to non-pos-v2 workspaces) AND AC.PO.1 (the user
authors their own root — translation between user-intent and
tracker-state is direct).

### D-5 — Legacy plan-doc back-extraction: best-effort or cutoff?

**Question:** Phase γ extracts amendment plan docs into
ObjectiveSpec records. (a) best-effort across all 26 amendments
(pre-#22 plans have inconsistent structure; un-extractable plans
get one-record placeholders). (b) cutoff date — only post-#22 plans
get extracted; pre-#22 amendments stay as plan-doc-only.

**Recommendation:** **(a) best-effort + placeholders.**

**Rationale:** matches locked ruling #4 ("everything else descends
from the value prop"). Partial coverage creates a tree where some
sealed components are fully lifted and others are stubs — the
audit-finding-triage CDC was authored against exactly that failure
mode.

**Lens trace:** AC.PO.2 (the tracker covers the full dev history
— complete toolkit, not partial).

### D-6 — Migration phasing: 3 phases vs single big-bang?

**Question:** (a) Phase α (root + spec + components, ~30 records),
Phase β (component ACs, ~150–200 records), Phase γ (amendment ACs +
test bindings, ~500 records). Three discrete sealed-component
amendments + dev-discipline data work. (b) one big-bang seeding
amendment that lifts ~700 records in one commit.

**Recommendation:** **(a) three phases.**

**Rationale:** big-bang violates §2.5 — it authors records the
amendment's ACs do not require. Phasing lets each amendment's ACs
verify exactly what that phase landed.

**Lens trace:** AC.PO.2 (Lens-3 / ODD discipline preserved during
migration; toolkit reliability up).

---

## References

- `CLAUDE.md` — three lenses, §2.5 spec-objective rule, output
  conventions.
- `docs/odd-methodology.md` — §1.1, §2.5, §3, §4, §10.
- `docs/odd-in-pos.md` — five-gate chain, §10.
- `docs/rebuild/VALUE_PROPOSITION.md` — primary-persona test, harness
  test (lines 58–69).
- `docs/rebuild/STATE.md` — rule #4 (zero core personas), rule #5
  (nothing worked unless against), rule #7 (background-work
  awareness).
- `docs/rebuild/FUTURE_IDEAS.md` — three lenses, dev CDCs (research-
  before-plan, plan-before-code, all-execution-through-background-
  agents, scope-only-dispatch).
- `docs/rebuild/spec/pos-v2-objectives-spec.md` — v1.0 / v1.1 / v1.2.
- `docs/rebuild/components/objective-tracker/proposal.md` — D1–D9.
- `objective-tracker/src/spec.py` — `ObjectiveSpec`, `Criterion`
  union, `TimeBound`.
- `objective-tracker/src/store.py` — event-sourced SQLite + sidecar.
- `objective-tracker/src/runtime.py` — async public API,
  `bind_scope`, `list_by_root`, `trace_to_root`.
- `objective-tracker/src/upgrade.py` — D8 semantic round-trip.
- `objective-tracker/docs/{overview,architecture,data-flow,relationship-map,api-reference}.md`.
- `objective-tracker/tests/test_d{1,2,3,4,5,6,7,8}_*.py` — AC harness.
- `tools/pos-amend/README.md` — manifest schema v1, subcommands.
- `docs/rebuild/plans/amendment-{29,30,31,32,33,34}-*.md` — recent
  amendment AC structure.
