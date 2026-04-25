# Sub-plan A — Persona-onboarding dev-intent question

**Status:** authored 2026-04-25. Research-and-planning only. Sealed-
component amendment to `primary-persona`. Spec objective: re-extension
of amendment #35's first-run elicitation surface (v1.1 — first-run
conversational elicitation extends to carry the dev-intent answer).

**Master plan:** `MASTER.md` (this directory).

---

## 1. Summary / TLDR

Extend the existing `ONBOARDING_QUESTIONS` tuple in
`primary-persona/src/onboarding.py` with a fourth question that
elicits the user's dev-intent. Persist the answer to a stable
workspace-local location the consumers (E, B, F) read. The answer
gates `classify_workspace`'s output (sub-plan E), the auto-load
partition (sub-plan F), and the CLAUDE.md-fragment selection (sub-plan
B).

The question is asked once at first-run, alongside the existing
user_name / persona_given_name / domain_focus. The shape mirrors them
exactly: a framework-scaffolding prompt (workspace-relateable), a
contract-field write-back, an OTel event per question/answer, and a
starter-flag transition that takes the contract out of starter state
once all required questions are answered.

The recommendation in the master plan's D-MASTER.1 places the answer
on the `PersonaContract` itself — one new field, `dev_intent: str`,
with values `"yes" | "no"`. Schema-validator at the contract level
refuses other values structurally (per ODD §5.3 — Pydantic +
`@model_validator` is the reach-for default). The field is stored
alongside `is_starter` and follows the same lifecycle.

The starter-pending contributor (`build_starter_pending_contributor`)
treats the dev-intent question as one more required answer; the
existing four-question flow (`user_name`, `persona_given_name`,
`domain_focus`, `dev_intent`) is the new shape.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

This is a sealed-component amendment to `primary-persona`. The spec
objective is the same one amendment #35 satisfied — **v1.1 — first-
run conversational elicitation refines a starter-flagged contract via
a small set of question-shape templates**. The new question is one
more shape inside the existing surface; the contract write-back path,
the observability events, and the starter-pending marker are all
inherited unchanged. The re-extension is structural (one new field on
the contract, one new question in the tuple, one new branch in the
write-back) and stays inside amendment #35's spec contract.

§2.5 forward audit: every line of new code in the amendment ladders
to AC.A1–AC.A7 below.
§2.5 reverse audit (run at build-review time): every diff line in
`primary-persona/src/onboarding.py` and `primary-persona/src/contract.py`
traces back to AC.A1–AC.A7.

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage

The amendment leans on Claude Code's existing additionalContext
session-start primitive (already in use via amendment #35's starter-
pending marker + amendment #32's session-start gate). No new Claude
primitive is invoked; the existing channel carries the question
prompts to the user, the user types the answer in chat, the persona
calls `persist_elicitation_transcript` to write the answer back. The
loop is the one amendment #35 already ships.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden
between the user's natural-language intent and AI-effective execution?*

Yes — at two layers. (1) The user's natural-language statement of
"I'm here to develop pos-v2" or "I'm here to use pos-v2" is captured
once and structurally honoured thereafter; the user never has to
re-state it, never has to navigate "is this a dev-only doc I should
read?" decisions session after session, never has to debug why their
session-start corpus contains methodology docs they don't care about.
(2) The persona itself stops translating between "the user said yes
to dev work earlier in this session" (volatile) and "the user is a
dev" (durable); the contract holds the durable answer.

**Harness test.** *Does this add to the toolkit the primary persona
can draw from?*

Yes — `dev_intent` is the new contract field every downstream
component composes on. Sub-plan E reads it through a path-resolver;
sub-plans B/F read it via the contract-loader. The persona's existing
`load_persona` returns a `LoadedPersona` whose `contract.dev_intent`
is the read surface; no new loader, no new schema, no new parse.

### Lens 3 — ODD authoring

ACs below are outcome-shaped. Method (the exact prompt prose, the
field's storage shape if the owner rules D-MASTER.1 (b), the OTel
event names) is the builder's call.

---

## 4. Acceptance criteria (AC.A1–AC.A7)

Each AC maps to at least one test function in
`primary-persona/tests/test_onboarding_dev_intent.py` (or equivalent).

### AC.A1 — `ONBOARDING_QUESTIONS` carries a dev-intent question

The canonical question tuple includes a fourth question (id =
`"dev_intent"`) marked `required=True`. The prompt's content is
sourced from the persona template (workspace-supplied content per
STATE.md rule #4); the framework-level scaffolding piece is the id +
required flag + contract-field mapping.

**Test shape:** import `ONBOARDING_QUESTIONS`; assert exactly one
entry has `id == "dev_intent"`, `required=True`, `contract_field` is
the new `PersonaContract` field's name (D-MASTER.1 (a)) or the
sentinel resolved by the path-resolver (D-MASTER.1 (b)).

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.A2 — `PersonaContract` carries a `dev_intent` field with structural validation

Under D-MASTER.1 (a): the contract Pydantic model has a `dev_intent`
field whose type is constrained to a small enum (`"yes"`, `"no"`,
or — defensive — `""` denoting unanswered, with a `@model_validator`
that refuses any other string).

**Test shape:** construct a `PersonaContract` with `dev_intent="yes"`
and `dev_intent="no"` — both succeed. Construct with `dev_intent="maybe"`
— Pydantic raises validation error. Construct without specifying —
field defaults to the unanswered sentinel.

**Maps to:** AC.PO.1 (structural refusal: the persona cannot end up
in an undefined dev-mode state) + AC.PO.2 (toolkit primitive: the
contract field is the canonical signal).

### AC.A3 — `persist_elicitation_transcript` writes `dev_intent` back

When the transcript carries a `"yes"` or `"no"` value at key
`"dev_intent"`, the contract on disk has the corresponding field set;
when the transcript omits the question, the field stays at its prior
value (or the unanswered sentinel on first scaffold). The starter-
flag transition path (lines 233–253 of current onboarding.py) is
extended to consider `dev_intent` as a required answer for completion.

**Test shape:** in a tmp-fs fixture, scaffold a fresh persona, run
`persist_elicitation_transcript` with all four answers; assert the
written contract has `dev_intent="yes"` (or "no"), `is_starter=False`,
and an OTel event `pos.persona.onboarding.answer` with
`question_id="dev_intent"`. Then run with three answers (omit
dev_intent); assert `is_starter=True` (incomplete) and the contract
is written without dev_intent set.

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.A4 — Starter-pending contributor reflects the dev-intent question

The contributor returned by `build_starter_pending_contributor`
includes `dev_intent` in the question count it surfaces in its
additionalContext block (the body that today says "3 questions, ~2
minutes, skippable" — now "4 questions"). The
`STARTER_PENDING_MARKER` prefix is unchanged.

**Test shape:** invoke the contributor against a starter-flagged
contract; assert the body text mentions four questions (or whatever
count the new tuple length yields). The exact prose is workspace-
supplied; the framework-level test asserts shape — number ≥ tuple
length.

**Maps to:** AC.PO.1.

### AC.A5 — Workspace-local storage location is exposed via a path-resolver

A pure function (e.g. `dev_intent_storage_path(workspace_root)`)
returns the on-disk location of the dev-intent answer. Under
D-MASTER.1 (a) this is the persona contract path; under (b) this is
`<workspace>/.pos/dev_intent.yaml`. Sub-plans E, B, F consume this
resolver, not the contract directly, so the storage shape is
substitutable without re-reading those sub-plans.

**Test shape:** call the resolver against two distinct workspace_roots;
assert the returned paths are workspace-rooted (not host-rooted) and
distinct. Assert `dev_intent_storage_path(workspace).is_relative_to(workspace)`.

**Maps to:** AC.PO.2 (toolkit primitive: a deterministic accessor
sub-plans E/B/F compose on).

### AC.A6 — Reading the answer when absent yields the documented default

A pure function `read_dev_intent(workspace_root) -> Literal["yes",
"no", "absent"]` returns `"absent"` when the contract has not yet had
the question answered (e.g. before onboarding completes; on a workspace
whose contract is mid-starter). The defensive default per locked owner
ruling 4 is: **`"absent"` is treated as "no" by E** (sub-plan E names
this in its ACs).

**Test shape:** in a tmp-fs fixture with a starter-pending contract,
call `read_dev_intent`; assert `"absent"`. After running
`persist_elicitation_transcript` with `"yes"`, call again; assert `"yes"`.

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.A7 — OTel event surface for the dev-intent answer

The amendment emits two new event types: `pos.persona.onboarding.dev_intent_question`
(once per starter session at question time) and
`pos.persona.onboarding.dev_intent_answer` (once when the answer is
recorded). Both carry the persona handle + workspace_slug attributes
(consistent with amendment #35's existing event shape).

**Test shape:** capture OTel events during a transcript persist; assert
exactly one of each type with the expected attributes.

**Maps to:** AC.PO.2 (observability is a toolkit primitive).

---

## 5. Out of scope

- Mode-toggle UX (covered by D-MASTER.4 — recommendation: deferred).
- Slash-command surface for dev_intent. No new slash command.
- Reading the answer cross-workspace (locked owner ruling 4 forbids
  cross-workspace hints).
- Auto-detecting dev intent from environment (locked owner ruling 4 —
  no heuristic).
- Surfacing the dev-intent answer in `additionalContext` after
  onboarding (sub-plan F decides whether DEV MODE annotates the
  session-start payload; A only writes/reads).

---

## 6. Halt triggers

1. **Existing AC35.x tests would need amendment** (e.g. the test
   asserting "exactly three questions"). Halt and surface — that is
   a re-extension of #35 needing owner approval (master halt trigger
   5).
2. **Pydantic model_validator pattern is incompatible with the
   existing contract serialiser.** Halt and surface; D-MASTER.1
   re-rules.
3. **The persona template's prompt-prose change requires a separate
   amendment to the framework template directory.** This is workspace-
   supplied content per STATE.md rule #4; if framework code changes,
   surface — that's outside this sub-plan.
4. **Dispatch budget overrun (>90 min of background-agent wall-time).**
   Halt and signal per `feedback_amendment_dispatch_speedups.md`.

---

## 7. Bookkeeping (`pos-amend` manifest)

Single-component manifest: `primary-persona`.

- `seal_test`: `primary-persona/tests/test_no_sealed_amendments.py`
- `sidecar`: `primary-persona/tests/SEAL_COMMIT`
- `frozen_baseline: false`

Universal paths (per `pos-amend` convention): `docs/rebuild/plans/`,
`CLAUDE.md`.

Narrative target: `primary-persona/seals/SEAL_COMMIT.dev-intent-onboarding`
(or equivalent). Body cites D-MASTER.1, D-MASTER.3 rulings and notes
the AC.A* surface maps to AC.PO.1 + AC.PO.2.

Cross-reference: this sub-plan is part of programme
`two-modes-and-multi-workspace`; master plan path
`docs/rebuild/plans/two-modes-and-multi-workspace/MASTER.md`.

---

## 8. Dispatch-time additions

When the brief is drafted:

- WD: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory.
- Plan-before-code: builder writes `amendment-XX-dev-intent-onboarding.builder-plan.md` first.
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective code.
- Strong-ODD-adherence halt.
- Scope-only downstream dispatches.
- No `git commit --amend`.
- Amendment-dispatch speedups apply (narrow tests, skip pre-seal full
  rerun, methodology snippets inlined).

---

## 9. Lens-2 trace blocks

| AC | AC.PO.1 (translation burden) | AC.PO.2 (toolkit primitive) |
|----|------------------------------|------------------------------|
| AC.A1 | The persona doesn't have to translate "is this a dev user" — it just asks. | New question shape extends an existing toolkit. |
| AC.A2 | Structural refusal of unrecognised values; the persona never has to translate ambiguous answers. | Contract field is the canonical signal. |
| AC.A3 | One write-back, one source of truth. | Write-back path extends the existing toolkit. |
| AC.A4 | Marker shape unchanged; the persona's session-start signal is durable. | Existing additionalContext primitive composed unchanged. |
| AC.A5 | Sub-plans E/B/F compose on a single resolver, not the contract layout. | Pure-function resolver — toolkit primitive. |
| AC.A6 | Defensive default is documented; the persona never has to translate "what does absent mean." | Read-API extends the existing toolkit. |
| AC.A7 | Observability surface lets the persona notice when onboarding is incomplete. | New event types extend the existing toolkit. |

---

## 10. Decision register (sub-plan-local)

| Code | Question | Recommendation |
|------|----------|----------------|
| D-A.1 | Field default for unanswered state — empty string `""` or explicit `"unanswered"` literal? | Empty string — matches `is_starter`'s False default and the existing PersonaContract conventions. Tested via AC.A2's negative branch. |
| D-A.2 | Should the prompt be authored in the framework's persona template, or supplied by the workspace? | Framework template ships a starter prompt; workspace overrides via the existing template-override mechanic per amendment #36. Preserves STATE.md rule #4. |
| D-A.3 | Does AC.A4's question-count text ("4 questions") get hard-coded or derived from `len(ONBOARDING_QUESTIONS)`? | Derived. Removes drift if a future amendment adds a fifth question. |

---

## 11. Builder freedom (method-only notes)

Builder chooses: the exact Pydantic field type (Literal vs StrEnum vs
custom validator), the prompt prose (in the persona template), the
exact event attribute keys, the test fixture's tmp-fs shape, the
default ordering of the question (between domain_focus and the end of
the tuple, or before user_name — owner is indifferent; recommendation
"after domain_focus" so existing question 1–3 flow is unchanged).

---

## 12. Test register (per AC)

| AC | Test file | Test function (suggested name) |
|----|-----------|--------------------------------|
| AC.A1 | `tests/test_onboarding_dev_intent.py` | `test_AC_A1_questions_tuple_carries_dev_intent` |
| AC.A2 | `tests/test_contract_dev_intent.py` | `test_AC_A2_dev_intent_validator_refuses_unknown_values` |
| AC.A3 | `tests/test_onboarding_dev_intent.py` | `test_AC_A3_persist_writes_dev_intent` |
| AC.A4 | `tests/test_onboarding_dev_intent.py` | `test_AC_A4_starter_pending_contributor_count` |
| AC.A5 | `tests/test_onboarding_dev_intent.py` | `test_AC_A5_storage_path_resolver_workspace_local` |
| AC.A6 | `tests/test_onboarding_dev_intent.py` | `test_AC_A6_read_dev_intent_default` |
| AC.A7 | `tests/test_onboarding_dev_intent.py` | `test_AC_A7_otel_events_emitted` |

---

## 13. Asymmetric observations

1. **Re-using `is_starter`'s lifecycle is the highest-leverage move.**
   The contract already has a starter-flag, a transition, an OTel
   event, a contributor that surfaces it. Adding `dev_intent` as a
   sibling field rides on all of that with no new infrastructure.
   Effort: low. Leverage: high.

2. **Resolver-as-API is the seam that lets E/B/F evolve without
   touching A.** AC.A5's pure-function resolver lets D-MASTER.1's
   choice between (a) and (b) move without breaking downstream. If
   the owner later moves the storage to (b), only A's resolver
   internals change.

3. **Inverse-asymmetric warning:** a separate "intent capture" surface
   distinct from onboarding is medium cost (new contributor, new
   trigger) for low leverage (the answer is one question; tying it to
   an existing flow saves the surface). Dropped.
