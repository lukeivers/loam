# Builder-plan — primary-persona conversational onboarding + default archetype

**Status:** builder-plan, pre-build. 2026-04-26.
**Authoring directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment HEAD:** `383a7fc` (docs(plans): record amendment #49
commit SHAs in method-decision register).
**Amendment number:** assigned at dispatch; next available after #49
is **#50**. Files renamed/refloated only if Luke rules otherwise.
**Locked plan governs:**
`docs/plans/primary-persona-conversational-onboarding-and-default-archetype.md`.
**Companion design research (locked):**
`/Users/lukeivers/pos3/.scratch/claude-output/onboarding-conversation-design-research.md`.

This builder-plan names files, symbol shapes, and AC test names per
the locked plan's ACs (AC.O.1–AC.O.S). Method per ODD §1.1 is the
builder's call; this plan is paper-trail for the build.

---

## 1. AC → file-and-symbol map

| AC | Files touched | Symbols added/changed/removed |
|---|---|---|
| AC.O.1 | `primary-persona/templates/persona-template/prompt.md` (full rewrite) | content: archetype + playbook + 11 named sections (5 traits + 6 rules) + `{user_preferred_name}` + `{persona_given_name}` tokens |
| AC.O.2 | `primary-persona/src/onboarding.py` | rewritten `build_starter_pending_contributor` body — points at playbook + `persist_grounding`, no question list, no question ids |
| AC.O.3 | `primary-persona/src/onboarding.py` | new `GroundingCapture` dataclass + new `persist_grounding(...)` function + new `OnboardingGroundingError` |
| AC.O.4 | `primary-persona/src/onboarding.py` | `persist_grounding` writes contract.yaml + prompt.md (with token substitution) + `.claude/agents/<handle>.md` (via `to_agent_md`) |
| AC.O.5 | `primary-persona/src/onboarding.py` | `persist_grounding` accepts `memory_client_factory` param; writes one `add_episode` with `source_description="onboarding-grounding"`; fail-soft |
| AC.O.6 | `primary-persona/templates/persona-template/contract.yaml` | replace placeholder responsibilities prose with non-placeholder archetype-aligned defaults; `dev_intent: unanswered`; `tier_d: defer` |
| AC.O.7 | (template content only) | tested via `run_first_run_scaffold` against tmpfs — no source edit required |
| AC.O.8 | `primary-persona/src/onboarding.py` (delete obsolete symbols), `primary-persona/src/__init__.py` (drop re-exports if any), `primary-persona/tests/` (delete obsolete tests) | removed: `OnboardingQuestion`, `ONBOARDING_QUESTIONS`, `persist_elicitation_transcript`, `OnboardingTranscriptError`, `_normalise_dev_intent`, `_DEV_INTENT_YES`, `_DEV_INTENT_NO`, `_is_complete_transcript`, `_validate_transcript_shape` |
| AC.O.S | manifest at `docs/plans/primary-persona-conversational-onboarding-and-default-archetype.manifest.yaml`; pos-amend apply | seal-diff fence enforced |

### Files to be edited (source)

1. `primary-persona/src/onboarding.py` — full rewrite. Keeps:
   `dev_intent_storage_path`, `_primary_contract_path`,
   `read_dev_intent`, `STARTER_PENDING_MARKER`. Replaces the rest.
2. `primary-persona/src/__init__.py` — review re-export list,
   drop names of removed symbols, add re-exports for `GroundingCapture`,
   `persist_grounding`, `OnboardingGroundingError`.
3. `primary-persona/templates/persona-template/prompt.md` — full
   content rewrite (default archetype prose).
4. `primary-persona/templates/persona-template/contract.yaml` —
   replace placeholder responsibilities prose; preserve structural
   shape; set `tier_d: defer`.

### Tests to be added

- `primary-persona/tests/test_AC_O_1_default_archetype_prompt_md.py`
- `primary-persona/tests/test_AC_O_2_starter_pending_contributor_playbook.py`
- `primary-persona/tests/test_AC_O_3_persist_grounding_contract_writeback.py`
- `primary-persona/tests/test_AC_O_4_persist_grounding_three_artefacts.py`
- `primary-persona/tests/test_AC_O_5_persist_grounding_memory_episode.py`
- `primary-persona/tests/test_AC_O_6_default_contract_loadable.py`
- `primary-persona/tests/test_AC_O_7_workspace_scaffold_lands_template.py`
- `primary-persona/tests/test_AC_O_8_removed_surfaces_no_orphan.py`

### Tests to be deleted (per AC.O.8: any test importing a removed symbol)

- `test_AC35_3_starter_pending_contributor.py` — imports
  `STARTER_PENDING_MARKER` (kept) AND `build_starter_pending_contributor`
  (kept). NOTE: the imports of `STARTER_PENDING_MARKER` and
  `build_starter_pending_contributor` are NOT removed; both remain.
  But the test asserts the *old* body shape (4-question list). The
  new body shape contradicts the old assertions. Remove the file
  per AC.O.8 (its replacements are AC.O.2's tests).
- `test_AC35_4_elicitation_writeback.py` — imports
  `persist_elicitation_transcript`, `OnboardingTranscriptError`
  (both removed). Delete.
- `test_AC_A_1_questions_tuple_carries_dev_intent.py` — imports
  `ONBOARDING_QUESTIONS`, `OnboardingQuestion` (both removed). Delete.
- `test_AC_A_3_persist_writes_dev_intent.py` — imports
  `persist_elicitation_transcript`, `OnboardingTranscriptError`. Delete.
- `test_AC_A_4_starter_pending_contributor_count.py` — imports
  `ONBOARDING_QUESTIONS`. Delete (its expectation that body lists
  questions is contradicted by AC.O.2's negative invariant).
- `test_AC_A_7_otel_events_emitted.py` — imports
  `persist_elicitation_transcript`. Delete (the dev-intent question /
  answer events are replaced by AC.O.5's onboarding-grounding
  episode write event).
- `test_AC46_7_starter_pending_body_widening.py` — imports
  `ONBOARDING_QUESTIONS`, asserts body lists question ids/prompts
  (contradicts AC.O.2). Delete; the 2,000-char budget assertion
  migrates to AC.O.2's test shape.
- `test_AC46_8_end_to_end_starter_interview_path.py` — imports
  `ONBOARDING_QUESTIONS`, `persist_elicitation_transcript`. Delete;
  end-to-end coverage migrates to AC.O.7 (scaffold lands template) +
  AC.O.3 (persist_grounding round-trip) + AC.O.4 (three-artefact
  closure).

### Tests to be rewritten (re-target old removed-write-surface)

- `test_AC_A_6_read_dev_intent_default.py` — currently uses
  `persist_elicitation_transcript` to set `dev_intent`. Rewrite to
  use `persist_grounding` instead. Read surface
  (`read_dev_intent`, `dev_intent_storage_path`,
  `_primary_contract_path`) is unchanged per locked plan §8.

### Tests preserved unchanged

All other tests under `primary-persona/tests/` (D7/D8/D9 etc.,
AC35.1, AC35.2, AC35.5, AC35.6, AC35.7, AC.A.2, AC.A.5, AC.A.S,
AC40.*, AC46.{1,2,3,4,5,6}, AC_M_*, etc.) remain unchanged. Spot-
check AC.A.S confirmed: it tests presence of the sub-plan A manifest
file (independent of onboarding-source surface), so its assertions
survive — but its manifest path
`docs/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.manifest.yaml`
must continue to exist. Verified by file listing.

---

## 2. New onboarding.py shape

### Public surface (post-rewrite)

```python
# Module: primary_persona.onboarding

# Preserved (read-side dev-intent surface — locked plan §8):
STARTER_PENDING_MARKER: str
def dev_intent_storage_path(workspace_root: Path) -> Path: ...
def read_dev_intent(workspace_root: Path) -> Literal["yes", "no", "absent"]: ...

# New (AC.O.2/AC.O.3/AC.O.4/AC.O.5):
class OnboardingGroundingError(ValueError): ...

@dataclass(frozen=True)
class GroundingCapture:
    user_preferred_name: str
    persona_given_name: str
    single_point_of_contact: str
    context_holder: str
    escalation_judge: str
    dev_intent: Literal["yes", "no"]
    captured_summary: tuple[str, ...]   # non-empty bullets

def build_starter_pending_contributor(loaded_persona) -> Callable[[dict], str]: ...

MemoryClientFactory = Callable[[], "MemoryClient | None"]   # lazy

def persist_grounding(
    *,
    loaded_persona,
    grounding: GroundingCapture,
    contract_path: Path,
    workspace_slug: str | None = None,
    memory_client_factory: MemoryClientFactory | None = None,
) -> PersonaContract: ...
```

### Removed (AC.O.8)

- `class OnboardingQuestion`
- `ONBOARDING_QUESTIONS` tuple
- `persist_elicitation_transcript(...)`
- `class OnboardingTranscriptError`
- `_normalise_dev_intent(...)`
- `_DEV_INTENT_YES`, `_DEV_INTENT_NO`
- `_is_complete_transcript`, `_validate_transcript_shape`

### `build_starter_pending_contributor` body shape (AC.O.2)

```
[primary-persona/onboarding starter-pending]
The workspace's persona contract is in starter state. <given_name>
opens conversational onboarding on the next user turn — see the
playbook in personas/<handle>/prompt.md.

write-back:
  When ready to commit captured grounding, call
  primary_persona.onboarding.persist_grounding(
      loaded_persona=<persona>,
      grounding=GroundingCapture(...),
      contract_path=Path('<workspace>/personas/<handle>/contract.yaml'),
  ). The call writes the contract, regenerates prompt.md and
  .claude/agents/<handle>.md, flips is_starter to False, and
  records an onboarding-grounding memory episode.
```

Body must:
- start with `STARTER_PENDING_MARKER` first line (preserves AC35.3
  marker discipline — that test is deleted but the marker itself
  remains in use in the broader hook surface);
- reference `prompt.md` and "playbook" (AC.O.2 assertion);
- name `persist_grounding` (AC.O.2 assertion);
- name the resolved `contract.yaml` path (AC.O.2 assertion);
- contain neither the strings `user_name`, `persona_given_name`,
  `domain_focus`, `dev_intent` as bare ids (AC.O.2 negative);
- length ≤ 2000 chars (AC.O.2 assertion).

Non-starter contract → empty string (AC.O.2 assertion).

### `persist_grounding` semantics (AC.O.3 / AC.O.4 / AC.O.5)

Input validation (AC.O.3 negative):
- All seven `GroundingCapture` string fields non-empty after `.strip()`.
- `dev_intent in {"yes", "no"}`.
- `captured_summary` is a non-empty tuple of non-empty strings.
- Failure → `OnboardingGroundingError`; no file is written.

On success:

1. Build the new contract payload from `loaded_persona.contract`'s
   serialised form, applying the captured fields:
   - `given_name = grounding.persona_given_name`
   - `responsibilities.single_point_of_contact = grounding.single_point_of_contact`
   - `responsibilities.context_holder = grounding.context_holder`
   - `responsibilities.escalation_judge = grounding.escalation_judge`
   - `dev_intent = grounding.dev_intent`
   - `is_starter = False`
2. Validate via `PersonaContract.model_validate(payload)`. If the
   resulting contract fails validation, raise
   `OnboardingGroundingError` (no file written).
3. Write `contract_path.write_text(new_contract.to_yaml())`.
4. Determine `<workspace_root>` and `<persona_dir>`:
   - `persona_dir = contract_path.parent`
   - `workspace_root = persona_dir.parent.parent` (the
     `<workspace>` part of `<workspace>/personas/<handle>/contract.yaml`)
5. Render prompt.md from the framework template:
   - Locate framework template via the same `_resolve_persona_template_dir`-shaped
     helper internal to `onboarding.py` (read-only); we can re-implement
     a tiny resolver: walk `Path(__file__).parents` to find
     `primary-persona/templates/persona-template/prompt.md`.
   - Read its body; substitute via `body.format(
        user_preferred_name=grounding.user_preferred_name,
        persona_given_name=grounding.persona_given_name,
     )`.
   - Write `persona_dir / "prompt.md"`.
6. Render `.claude/agents/<handle>.md` via
   `to_agent_md(new_contract, prompt_text=<rendered prompt body>)`
   and write to `<workspace>/.claude/agents/<handle>.md` (mkdir
   parents).
7. Memory episode (AC.O.5):
   - If `memory_client_factory is None` → no-op (no episode write).
   - Else `client = memory_client_factory()`. If `None` → no-op.
   - Else attempt `client.add_episode(name=..., episode_body=<body>,
     source_description="onboarding-grounding", source=<...>)`
     (signature matched against `LiveMCPMemoryClient.add_episode`'s
     existing surface — verified in build).
   - Wrap in try/except; on raise, emit a
     `pos.persona.onboarding.grounding_episode_failed` event and
     swallow; the disk write-back is unaffected.
8. Emit `pos.persona.onboarding.grounding_persisted` event with
   handle + workspace_slug + completed=True.
9. Return the new contract.

The `is_starter: True → False` transition is observable (we can
emit `onboarding_starter_flag_transition_event` if available;
verifying current observability surface during build).

### Token-substitution conflict guard (halt trigger §9.3)

If `prompt.md` body contains `{` or `}` characters that aren't part
of `{user_preferred_name}` / `{persona_given_name}`, `str.format`
will raise. Mitigation: write the prompt.md content with literal
`{` escaped as `{{` and `}` as `}}` everywhere except the two
substitution points. Verify in test (AC.O.4 confirms the expected
substituted output matches given name).

---

## 3. New prompt.md content shape (AC.O.1)

Eleven named-section markers (headings, structurally detectable):

```
# Persona prompt — default archetype

> Provenance note: This file was scaffolded from the framework's
> default persona archetype. You can edit any of it. The
> conversation rules below are battle-tested defaults — read
> before changing.

## Identity / Archetype

I am {persona_given_name}, an eager-new-hire chief-of-staff for
{user_preferred_name}. ...

## Voice

...

## Seed questions

The three seed questions I open with on session 1:

1. Walk me through your day — when do you feel like the work is
   getting the right attention, and when does it feel like it's
   slipping?
2. ...
3. ...

## Funnel + OARS + reflections

I run a funnel from broad to specific, applying OARS (open
questions, affirmations, reflections, summaries) with a
2-reflections-per-question ratio. ...

## Pivot rule (3-of-5)

I pivot from listening to proposing when at least 3 of these 5
conditions are met:

1. ...
2. ...
3. ...
4. ...
5. ...

## Proposal moment

When the pivot fires:

1. Reflect back what I heard ...
2. Offer 2–3 concrete deliverables ...
3. Close with: "which of these feels closest to where you want me
   to start?"

## Failure-mode guards

- Don't let listening become interrogation — pivot when 3-of-5.
- Don't pivot before listening — at least one full funnel cycle.
- ...

## No-expertise-user variant

If the user signals they're new to AI / pOS / chief-of-staff
delegation entirely: ...

## Top-value traits

### Autonomy

I don't pause for permission on authorised work. ...

### Asymmetric problem solving

I evaluate leverage-vs-cost on every move. ...

### Parallelism

I don't serialize work that doesn't need serializing. ...

### Test theories before acting on them

When a tool returns an unexpected result, my first move is to
verify the cause. ...

### Self-correction

When I notice something didn't work as planned, that observation
auto-triggers capture-or-fix. ...

## Operational rules

### Lean on the harness

Before acting on almost anything, I pause and consider what Claude
Code / hook / MCP / skill / plugin / scheduled-routine primitive
does the work better than inference alone. ...

### Use the right tool

Determinism-first. Where inference's value-props ... aren't
load-bearing, I prefer scripts, deterministic tools, and named
rubrics. ...

### Codify what repeats

Auto-skilling. I watch for repetition and either codify the work
or surface the repetition. ...

### Structural enforcement default

When authoring or accepting a critical guard or hard requirement,
my first move is "what structural check would catch a violation?"
— hook, Pydantic validator, manifest check, CI lint — and only
after structure is ruled out do I accept an advisory rule. ...

### ODD-shaped internal model

I internally restate every user request as objective + constraints
+ acceptance before acting. ...

### Light-touch narration on choices

When I make a non-obvious choice between modalities, I surface the
choice and its reason in one sentence, ambient-style. At most one
narration per turn. ...
```

The actual prose will be richer per builder discretion (per plan
§7 authority bound — refine wording, register, prose phrasing,
provided every named-section header is present).

### AC.O.1 detection markers

The test asserts presence of these heading strings (exact, line-
prefixed with `## ` or `### `):

- `## Identity / Archetype` (or `## Identity` AND/OR `## Archetype` —
  builder picks; spec says "Identity / Archetype section naming...")
- `## Voice`
- `## Seed questions` (containing the three seed questions; presence
  detected by counting numbered list items)
- `## Funnel + OARS + reflections` OR equivalent named section that
  contains "funnel" + "OARS" + "2 reflections" (per D3)
- `## Pivot rule (3-of-5)` AND the test asserts all five rules
  appear as a list in that section
- `## Proposal moment` AND test asserts presence of the three
  parts (reflect-back, 2–3 candidates, closing question)
- `## Failure-mode guards` (per D7)
- `## No-expertise-user variant` (per D6)
- `### Autonomy`
- `### Asymmetric problem solving`
- `### Parallelism`
- `### Test theories before acting on them`
- `### Self-correction`
- `### Lean on the harness`
- `### Use the right tool`
- `### Codify what repeats`
- `### Structural enforcement default`
- `### ODD-shaped internal model`
- `### Light-touch narration on choices`

That's 11 named sections (5 traits + 6 rules) + 8 structural
sections (identity, voice, seed questions, funnel, pivot, proposal,
failure guards, no-expertise variant) = 19 markers in total.

The `{user_preferred_name}` and `{persona_given_name}` tokens must
appear at least once in the body.

Five pivot conditions (per companion design research D4):

1. The user has named a friction or pain point.
2. The user has named at least one specific responsibility / domain.
3. The user has stated (explicitly or by implication) that they
   want help.
4. There's enough material to draft 2–3 concrete deliverables.
5. The conversation has produced at least one signal that listening-
   only is starting to feel circular (a repeat, a sigh, a "yeah, I
   already said that," or 3+ exchanges with no new information).

Three seed questions (per D1):

1. Walk me through your day — when does the work feel like it's
   getting the attention you want, and when does it feel like
   it's slipping?
2. What kind of help would actually take pressure off — not just
   in the abstract, but if I were sitting next to you for a week,
   what would I be picking up?
3. Anything else you want me to know about how you operate, what
   you care about, or what tends to go wrong when you delegate?

(Builder may refine phrasing; the test uses substring match on the
distinctive phrases "Walk me through your day", "take pressure off",
"how you operate" or equivalent — builder picks the exact substring
markers and locks them in the test.)

---

## 4. New contract.yaml content shape (AC.O.6)

```yaml
# Default persona contract — chief-of-staff archetype.
# The workspace-bootstrap scaffold (amendment #36) copies this file
# into <workspace>/personas/<handle>/contract.yaml, mutating only the
# `handle` field and `is_starter`. Every other value is the default
# the conversational onboarding flow will refine.

handle: example-persona
given_name: Example
contract_version: "1.0.0"

responsibilities:
  single_point_of_contact: >
    Sole coordinator for your day-to-day operations — the one
    address you go to for any work that's not yet clearly someone
    else's, and the one that decides which specialist (or which
    direct action) handles it from there.
  context_holder: >
    Carries ongoing context across sessions — what's in flight,
    what's stalled, what you've decided, what you've deferred —
    so that today's conversation builds on yesterday's instead of
    restarting it.
  escalation_judge: >
    Decides what to surface to you and what to handle quietly,
    using the boundary you've set: irreversible, high-leverage,
    or off-pattern moves come to you; routine and reversible
    moves get done.

authority_boundary:
  tier_a: defer
  tier_b: defer
  tier_c: execute
  tier_d: defer

escalation_taxonomy:
  categories:
    - external-funds-commitment
    - irreversible-action
    - strategy-pivot

severity_vocabulary:
  labels:
    - crisis
    - urgent
    - material
    - advisory

is_primary: true

pending_introduction: false
is_addressable: true

dev_intent: unanswered
```

AC.O.6 test asserts:
- file parses through `load_contract` (after mutating handle to a
  fixture value + is_starter=True);
- responsibilities prose for all three fields is non-empty AND
  doesn't start with "Describe, in one sentence" (negative
  placeholder check);
- `dev_intent == "unanswered"`;
- `tier_d == TierAction.defer`;
- `is_primary is True`;
- `to_agent_md(...)` renders without raising and produces non-empty
  output.

---

## 5. AC test sketches (compact)

### AC.O.1 — `test_AC_O_1_default_archetype_prompt_md.py`

```python
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "persona-template"
PROMPT_MD = TEMPLATE_DIR / "prompt.md"

def test_AC_O_1_named_sections_present():
    body = PROMPT_MD.read_text()
    sections = [
        "## Identity",       # Identity OR Archetype OR both
        "## Voice",
        "## Seed questions",
        "Funnel",            # within a section header (case-flexible)
        "Pivot rule",
        "Proposal moment",
        "Failure-mode guards",
        "No-expertise-user",
        "### Autonomy",
        "### Asymmetric problem solving",
        "### Parallelism",
        "### Test theories",
        "### Self-correction",
        "### Lean on the harness",
        "### Use the right tool",
        "### Codify what repeats",
        "### Structural enforcement default",
        "### ODD-shaped internal model",
        "### Light-touch narration on choices",
    ]
    for marker in sections: assert marker in body

def test_AC_O_1_substitution_tokens_present():
    body = PROMPT_MD.read_text()
    assert "{user_preferred_name}" in body
    assert "{persona_given_name}" in body

def test_AC_O_1_three_seed_questions_present():
    body = PROMPT_MD.read_text()
    # builder commits to three substring markers; assert all three
    seed_markers = [<exact strings the builder writes into the
    template, locked at build time and copied here verbatim>]
    for m in seed_markers: assert m in body

def test_AC_O_1_pivot_rule_lists_five_conditions():
    body = PROMPT_MD.read_text()
    # locate the Pivot rule section, count enumerated items 1–5
    # under it; assert 5 numbered items present
    ...
```

### AC.O.2 — `test_AC_O_2_starter_pending_contributor_playbook.py`

```python
def test_AC_O_2_marker_first_line():
    persona = _starter_fixture()
    body = build_starter_pending_contributor(persona)({})
    assert body.splitlines()[0] == STARTER_PENDING_MARKER

def test_AC_O_2_body_references_playbook():
    persona = _starter_fixture()
    body = build_starter_pending_contributor(persona)({})
    assert "playbook" in body or "prompt.md" in body

def test_AC_O_2_body_names_persist_grounding():
    body = ...
    assert "persist_grounding" in body

def test_AC_O_2_body_names_contract_path():
    persona = _starter_fixture(directory=Path("/x/personas/iris"))
    body = build_starter_pending_contributor(persona)({})
    assert "contract.yaml" in body
    assert "/x/personas/iris" in body or "iris" in body

def test_AC_O_2_body_omits_question_id_strings():
    body = ...
    for q_id in ("user_name", "persona_given_name", "domain_focus", "dev_intent"):
        # bare 'dev_intent' could appear in a different context — we
        # actually want "no numbered question list with these ids" —
        # so assert no "id=user_name" or "id=persona_given_name"
        # patterns (the AC35.3 shape).
        assert f"id={q_id}" not in body

def test_AC_O_2_body_within_2000_char_budget():
    body = ...
    assert len(body) <= 2000

def test_AC_O_2_non_starter_returns_empty():
    persona = _non_starter_fixture()
    body = build_starter_pending_contributor(persona)({})
    assert body == ""
```

### AC.O.3 — `test_AC_O_3_persist_grounding_contract_writeback.py`

```python
def test_AC_O_3_well_formed_grounding_writes_contract(tmp_path):
    contract = ...
    persona = _FakeLoadedPersona(contract=contract)
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())
    grounding = GroundingCapture(...)
    new_contract = persist_grounding(
        loaded_persona=persona, grounding=grounding,
        contract_path=contract_path,
    )
    reloaded = load_contract(contract_path)
    assert reloaded.given_name == grounding.persona_given_name
    assert reloaded.responsibilities.single_point_of_contact == grounding.single_point_of_contact
    assert reloaded.responsibilities.context_holder == grounding.context_holder
    assert reloaded.responsibilities.escalation_judge == grounding.escalation_judge
    assert reloaded.dev_intent == grounding.dev_intent
    assert reloaded.is_starter is False

def test_AC_O_3_malformed_grounding_raises_no_file_write(tmp_path):
    # empty single_point_of_contact
    bad = GroundingCapture(..., single_point_of_contact="")
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text("placeholder")
    mtime_before = contract_path.stat().st_mtime_ns
    with pytest.raises(OnboardingGroundingError):
        persist_grounding(...)
    assert contract_path.stat().st_mtime_ns == mtime_before
    assert contract_path.read_text() == "placeholder"

def test_AC_O_3_unknown_dev_intent_raises():
    bad = GroundingCapture(..., dev_intent="maybe")  # type: ignore
    with pytest.raises(OnboardingGroundingError): ...
```

(All malformed-payload negative cases.)

### AC.O.4 — `test_AC_O_4_persist_grounding_three_artefacts.py`

Seeds a workspace (`<tmp>/personas/<handle>/contract.yaml` + the
framework template's prompt.md as starter prompt), `<tmp>/.claude/`
exists. Calls `persist_grounding`. Asserts:

- `prompt.md` contains "Luke" and "Mara" and no `{user_preferred_name}`
  literal.
- `.claude/agents/<handle>.md` exists and contains "Mara".
- Re-call with `persona_given_name="Aria"` regenerates both
  files; "Aria" present, "Mara" absent.

### AC.O.5 — `test_AC_O_5_persist_grounding_memory_episode.py`

```python
class _FakeMemoryClient:
    def __init__(self): self.calls = []
    def add_episode(self, **kwargs): self.calls.append(kwargs)

def test_AC_O_5_factory_returns_client_writes_one_episode(tmp_path):
    client = _FakeMemoryClient()
    persist_grounding(..., memory_client_factory=lambda: client)
    assert len(client.calls) == 1
    assert client.calls[0]["source_description"] == "onboarding-grounding"
    # body contains captured-summary text
    body = client.calls[0]["episode_body"]  # or "body" — match actual API
    assert "<summary bullet excerpt>" in body

def test_AC_O_5_factory_returns_none_no_episode_succeeds(tmp_path):
    persist_grounding(..., memory_client_factory=lambda: None)
    # no exception; disk write-back succeeded (verified via reload)

def test_AC_O_5_no_factory_no_episode(tmp_path):
    persist_grounding(...)  # factory omitted
    # no exception; disk write-back succeeded

def test_AC_O_5_raising_client_does_not_propagate(tmp_path, span_exporter_clean):
    class Raising:
        def add_episode(self, **kw): raise RuntimeError("boom")
    persist_grounding(..., memory_client_factory=lambda: Raising())
    # disk write succeeded
    # observability event for failure emitted
    spans = span_exporter_clean.get_finished_spans()
    names = [ev.name for sp in spans for ev in sp.events]
    assert "pos.persona.onboarding.grounding_episode_failed" in names
```

### AC.O.6 — `test_AC_O_6_default_contract_loadable.py`

```python
def test_AC_O_6_template_loads_with_handle_and_starter_mutation(tmp_path):
    template_dir = REPO_ROOT / "primary-persona" / "templates" / "persona-template"
    raw = yaml.safe_load((template_dir / "contract.yaml").read_text())
    raw["handle"] = "iris"
    raw["is_starter"] = True
    contract = PersonaContract.model_validate(raw)
    assert contract.handle == "iris"
    assert contract.is_starter is True
    for field in ("single_point_of_contact", "context_holder", "escalation_judge"):
        prose = getattr(contract.responsibilities, field)
        assert prose.strip()  # non-empty
        assert not prose.lstrip().lower().startswith("describe, in one sentence")
    assert contract.dev_intent == "unanswered"
    assert contract.authority_boundary.tier_d == TierAction.defer

def test_AC_O_6_renders_through_to_agent_md():
    ...
    rendered = to_agent_md(contract)
    assert rendered  # non-empty
```

### AC.O.7 — `test_AC_O_7_workspace_scaffold_lands_template.py`

```python
def test_AC_O_7_scaffold_lands_template_unchanged(tmp_path):
    pos_root = tmp_path / "pos_root"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    result = run_first_run_scaffold(
        pos_root=pos_root,
        workspace_root=workspace,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "agents",
    )
    assert result.persona_installed
    persona_dir = workspace / "personas" / "primary"
    assert (persona_dir / "prompt.md").exists()
    assert (persona_dir / "contract.yaml").exists()
    # Template's prompt.md body equals the workspace's prompt.md
    template_prompt = (REPO_ROOT / "primary-persona" / "templates" /
                      "persona-template" / "prompt.md").read_text()
    assert (persona_dir / "prompt.md").read_text() == template_prompt
    # contract.yaml only differs by handle + is_starter
    raw_template = yaml.safe_load(
        (REPO_ROOT / "primary-persona" / "templates" /
         "persona-template" / "contract.yaml").read_text()
    )
    raw_workspace = yaml.safe_load((persona_dir / "contract.yaml").read_text())
    assert raw_workspace["handle"] == "primary"
    assert raw_workspace["is_starter"] is True
    # Every other key matches
    for k in raw_template:
        if k in ("handle", "is_starter"): continue
        assert raw_workspace.get(k) == raw_template[k]
```

The "no source edit to workspace-bootstrap" portion is verified by
AC.O.S (seal-diff). No additional assertion needed in this test.

### AC.O.8 — `test_AC_O_8_removed_surfaces_no_orphan.py`

```python
import importlib
import pkgutil

REMOVED_NAMES = {
    "OnboardingQuestion", "ONBOARDING_QUESTIONS",
    "persist_elicitation_transcript", "OnboardingTranscriptError",
    "_normalise_dev_intent", "_DEV_INTENT_YES", "_DEV_INTENT_NO",
    "_is_complete_transcript", "_validate_transcript_shape",
}

def test_AC_O_8_removed_names_not_importable():
    import primary_persona
    import primary_persona.onboarding
    for name in REMOVED_NAMES:
        assert not hasattr(primary_persona.onboarding, name), \
            f"removed symbol {name} still on primary_persona.onboarding"
        assert not hasattr(primary_persona, name), \
            f"removed symbol {name} still on primary_persona"

def test_AC_O_8_no_test_imports_removed_name():
    tests_dir = Path(__file__).resolve().parent
    for py in tests_dir.glob("test_*.py"):
        text = py.read_text()
        for name in REMOVED_NAMES:
            assert name not in text, \
                f"test file {py.name} still references removed symbol {name}"

def test_AC_O_8_no_src_module_references_removed_name():
    src_dir = Path(__file__).resolve().parent.parent / "src"
    for py in src_dir.glob("*.py"):
        text = py.read_text()
        for name in REMOVED_NAMES:
            assert name not in text, \
                f"src file {py.name} still references removed symbol {name}"
```

NB: `primary_persona` is the package name in `primary-persona/src/__init__.py`,
imported via `pyproject.toml`'s package config (see existing
`from primary_persona.onboarding import ...` patterns). The tests
in this layer use `from src.onboarding import ...` (per conftest's
`sys.path.insert`); both forms must be checked.

---

## 6. Manifest

`docs/plans/primary-persona-conversational-onboarding-and-default-archetype.manifest.yaml`:

```yaml
schema_version: 1
amendment:
  number: 50  # or next available; verified at amendment-commit time
  slug: primary-persona-conversational-onboarding-and-default-archetype
  title: "primary-persona conversational onboarding rewrite + default archetype content"

# BASELINE captured at amendment-commit time = HEAD~1 of amendment commit
# = 383a7fc (the docs(plans) commit recording amendment #49 SHAs).
baseline: 383a7fc...   # full 40-char SHA — locked at amendment-commit time

plan: docs/plans/primary-persona-conversational-onboarding-and-default-archetype.md

components:
  - name: primary-persona
    seal_test: primary-persona/tests/test_no_sealed_amendments.py
    sidecar: primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []

universal_paths:
  prefixes:
    - docs/plans/
    - docs/plans/research/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/FUTURE_IDEAS.md
    - docs/STATE.md
    - docs/VALUE_PROPOSITION.md

narrative:
  target: primary-persona/seals/SEAL_COMMIT.conversational-onboarding
  body: |
    # Amendment #50 — primary-persona conversational onboarding +
    #                  default archetype content + write-back
    #                  closure
    # (full narrative authored at seal time; see locked plan §10)
```

---

## 7. Build sequence

1. Read corpus + plan + research (done).
2. `git status` (done — clean except whitelisted parallel artefacts).
3. Write builder-plan to disk (this file).
4. Pre-amendment narrow-scope test: run
   `primary-persona/tests/` baseline. Expect pass.
5. Implement source edits in this order (build-friendly):
   a. `primary-persona/templates/persona-template/contract.yaml`
      replacement.
   b. `primary-persona/templates/persona-template/prompt.md`
      replacement.
   c. `primary-persona/src/onboarding.py` rewrite.
   d. `primary-persona/src/__init__.py` re-export adjustments.
6. Delete obsolete tests per §1 list.
7. Add new AC.O.* tests per §5.
8. Rewrite `test_AC_A_6_read_dev_intent_default.py` to use
   `persist_grounding` instead of `persist_elicitation_transcript`.
9. Run full `primary-persona/` suite, fix until green.
10. Author manifest at
    `docs/plans/primary-persona-conversational-onboarding-and-default-archetype.manifest.yaml`.
11. `pos-amend apply --dry-run <manifest>` — must exit 0.
12. Stage + create amendment commit (descriptive subject, AC list
    in body).
13. Run `primary-persona/tests/` post-amendment.
14. Cross-component seal-diff sweep (run every other sealed
    component's `test_no_sealed_amendments.py`).
15. `pos-amend seal --plan-doc docs/plans/primary-persona-conversational-onboarding-and-default-archetype.md`.
16. Confirm seal commit + sidecar + narrative landed.
17. Final `pos-amend apply --dry-run` confirmation.
18. Backfill SHAs into plan §14.

---

## 8. Halt conditions (per locked plan §9)

Triggers that force a halt:
- Any required source edit outside `primary-persona/`.
- `persist_grounding` cannot satisfy AC.O.4 without scaffold edit.
- Token-substitution conflicts with existing convention.
- AC.O.5 tag conflict (Stop-hook plan has different tag namespace).
- An ODD-violating shape strongly required.
- `pos-amend apply --dry-run` red.
- A test for AC cannot be written deterministically.
- D1–D8 contradicted by something the build surfaces.
- A test the rewrite is "supposed to remove" turns out to be load-
  bearing for an unnoticed objective.
- Wall time exceeds 90 minutes.

---

## 9. Sequencing note (D-OWNER.1)

Per locked plan: Stop-hook first, then this. Verify at build time
whether `memory-system-live-client-and-stop-hook-write.md` has
sealed.

If yes: read its sealed memory-write tag namespace; AC.O.5 tag
must compose with it (or halt).

If no: AC.O.5 ships with the recommended `"onboarding-grounding"`
tag and a fake memory client for tests. The production path uses
`memory_client_factory=None` semantics — no episode write attempted.

Verified at build dispatch: per `git log --oneline | head -10` the
most recent seal is amendment #49 (bootstrap-progress-statusline,
seal `5f235c7`). The Stop-hook plan has NOT yet sealed (no commit
referencing its slug visible). Therefore: AC.O.5 ships with the
default tag + fake memory client; production path uses `None`
factory.
