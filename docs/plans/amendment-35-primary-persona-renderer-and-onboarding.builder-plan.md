# Builder-plan — Amendment #35: primary-persona renderer + onboarding + is_starter

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-25 (build dispatch).
**Plan:** `docs/plans/amendment-35-primary-persona-renderer-and-onboarding.md`.
**BASELINE pattern:** HEAD~1 of the amendment commit (per #34 precedent at
`045f6db`). Captured at amendment-commit time once the amendment commit
SHA is known; manifest written before `pos-amend apply --dry-run`.
**Scope:** `primary-persona/` only. No edits to any other sealed component.

---

## D-build choices made (refined from plan §11)

### D-build.1 — Renderer module location: **new module `primary-persona/src/agent_md.py`**

`agent_md.py` co-located with the rest of the persona-layer source. The
function `to_agent_md(contract: PersonaContract) -> str` is the primary
public symbol. Re-exported from `src/__init__.py` if the package
publishes a public surface (verify; if not, import path is
`src.agent_md.to_agent_md`).

**Rationale:** master plan §6.2 + plan §11 D-build.1 cite ~30 lines of
projection logic; co-location with `contract.py` would couple the
persona-data shape with its Claude-Code projection surface. A separate
module keeps `contract.py`'s surface unchanged for the contract suite
and lets AC35.2 / AC35.5 / AC35.6 tests target a single import path.

### D-build.2 — Onboarding question count + wording: **3 questions**

Picked the lower bound of master plan D2(d)'s 3–5 range. The questions:

1. *"What should I call you?"* (maps to `given_name` plus `handle`-default
   derivation hint; the `handle` itself is workspace-bootstrap's call
   per AC36.4 — this onboarding asks for human-name only)
2. *"What should I call myself? (You can also pick a different name later.)"*
   (maps to a write-back to `given_name` of the persona; the persona
   character itself, not the user's own name)
3. *"What kinds of work do you most want me to handle?"* (maps to a
   write-back into `responsibilities.single_point_of_contact` —
   one-sentence prose)

**Rationale:** AC35.4 measures persistence + `is_starter` flip on
complete answers, not which questions ran. Three questions is the
minimum that exercises (a) given_name write-back, (b) responsibility
prose write-back, (c) the elicitation transcript→`to_yaml()` path. Any
fewer skips one of the three; any more dilutes the AC's "incomplete
transcript leaves contract starter-flagged" negative case (AC35.4
explicitly bounds the negative path).

The question **shape** lives in `onboarding.py` as a constant tuple of
question-shape templates (no persona prose) — STATE.md rule 4 holds:
the questions are framework-level template scaffolding, the answers
are workspace-supplied content.

### D-build.3 — Identity-anchor block content: **structural marker + contract-derived prose**

The `to_agent_md()` body follows this shape:

```
---
name: <handle>
description: <one-line derived from responsibilities.single_point_of_contact>
model: inherit
---

# Identity anchor (compaction-resilience)

I am <given_name> (<handle>). I serve as the workspace's primary
persona, single point of contact for the responsibilities declared in
my contract at `personas/<handle>/contract.yaml`. If this anchor block
is absent or contradicted by recent context, defer to the contract
file as the authoritative source.

# Persona prompt

<contents of personas/<handle>/prompt.md>
```

The "Identity anchor" block content is **derived** from the contract
fields (`given_name`, `handle`); the literal sentences around them
(*"I am ... primary persona ..."*) are framework-level template
scaffolding (the same status as the question-shape templates in
onboarding.py — about the contract, not about the workspace's
content).

**Rationale:** master plan §4.1 references ivers-corp's compaction-
resilience anchor pattern. The shape above is structural (not lifted
prose); the workspace's contract supplies all addressing tokens. A
test fixture with sentinel `given_name` + `handle` produces an
output containing those sentinels, satisfying AC35.6's framework-not-
content sentinel-trace test.

### D-build.4 — Starter-pending marker wording: **structurally detectable prefix**

The starter-pending contributor returns:

```
[primary-persona/onboarding starter-pending]
The workspace's persona contract is in starter state. <given_name>
opens elicitation on the next user turn (3 questions, ~2 minutes,
skippable).
```

The first line begins with the literal prefix `[primary-persona/onboarding starter-pending]` —
structurally detectable for AC35.3's marker assertion. The body line
is plain-language guidance that the persona's first response will pick
up; exact wording is method but the AC measures presence of the
marker, not the body.

**Rationale:** matches the existing `_serialise_session` /
`_serialise_turn` pattern in `context_composer.py` where
contributor blocks open with a `[name]` header. The marker prefix is
discriminable; the body is one sentence the persona's first turn can
naturally extend.

---

## Files expected to change

| Path | Change | Behaviour |
|---|---|---|
| `primary-persona/src/contract.py` | add `is_starter: bool = False` field | AC35.1 |
| `primary-persona/src/agent_md.py` | new module — `to_agent_md(contract)` | AC35.2, AC35.5, AC35.6 |
| `primary-persona/src/onboarding.py` | new module — questions, contributor factory, transcript→write-back | AC35.3, AC35.4 |
| `primary-persona/src/observability.py` | add onboarding-event helpers | AC35.7 |
| `primary-persona/tests/test_AC35_1_is_starter_field.py` | parametric round-trip + rejection | AC35.1 |
| `primary-persona/tests/test_AC35_2_to_agent_md_projection.py` | frontmatter shape + idempotence + structural rejection | AC35.2 |
| `primary-persona/tests/test_AC35_3_starter_pending_contributor.py` | starter-flag → contribution; non-starter → empty | AC35.3 |
| `primary-persona/tests/test_AC35_4_elicitation_writeback.py` | full transcript → flip; partial → no flip | AC35.4 |
| `primary-persona/tests/test_AC35_5_renderer_regenerates_on_change.py` | mutation → output diff | AC35.5 |
| `primary-persona/tests/test_AC35_6_framework_not_content.py` | sentinel prose → output contains sentinels; no hardcoded persona prose | AC35.6 |
| `primary-persona/tests/test_AC35_7_observability.py` | spans + events emitted on each lifecycle path | AC35.7 |
| `primary-persona/tests/test_no_sealed_amendments.py` | BASELINE advance + allowed-prefixes unchanged (still `primary-persona/` + `docs/plans/` + universal files) | AC35.S |
| `primary-persona/templates/persona-template/contract.yaml` | optional — leave `is_starter` absent (defaults to False); template is non-starter by virtue of default | nothing functionally |
| `docs/plans/amendment-35-*.manifest.yaml` | new manifest file | bookkeeping |
| `docs/plans/amendment-35-*.builder-plan.md` | this file | bookkeeping |
| `docs/plans/amendment-35-*.md` | already exists; append §14 method-decision record + commit SHAs | bookkeeping |
| `docs/plans/amendment-36-*.md` | already exists; no edit unless explicitly required | n/a |
| `docs/plans/amendment-37-*.md` | already exists; no edit unless explicitly required | n/a |
| `docs/plans/first-run-*.md` | already exists; no edit | n/a |
| `primary-persona/seals/SEAL_COMMIT.renderer-and-onboarding` | seal narrative authored by `pos-amend seal` | bookkeeping |

**Surfaces NOT touched:** `loader.py`, `monitor.py`, `compaction.py`,
`context_composer.py`, `session_start_gate.py`, `memory_consumer.py`,
`creation_triggers.py`, `authoring.py`, `introduction.py`,
`retirement.py`. Per plan §6 constraint 3.

---

## Implementation sequence

1. Build the manifest stub (BASELINE = HEAD at brief-dispatch — i.e.
   current `bea9f47`). The manifest's BASELINE will be updated to
   HEAD~1 once the amendment commit lands (matching #34's pattern).
2. Land `is_starter` field on `PersonaContract`. Run `test_d1_contract`
   green. Run `test_no_sealed_amendments`-style scoped checks to
   ensure no other module breaks.
3. Land `agent_md.py` + `test_AC35_2`, `test_AC35_5`, `test_AC35_6`.
4. Land `onboarding.py` + `test_AC35_3`, `test_AC35_4`.
5. Extend `observability.py` with onboarding events; add
   `test_AC35_7`.
6. Add `test_AC35_1` for the new field's round-trip + rejection.
7. Update `test_no_sealed_amendments.py` BASELINE to the post-amendment
   commit OR leave at current BASELINE — pos-amend manages BASELINE
   advancement on the seal commit. The allowed-prefixes set is already
   correct.
8. Run primary-persona test suite: target `pytest primary-persona/tests/`.
9. Seal-diff cross-check: every other sealed component's
   `test_no_sealed_amendments.py` must remain green. Per plan §6
   constraint 12 + the dispatch's amendment-dispatch-speedups.
10. Author manifest yaml at
    `docs/plans/amendment-35-primary-persona-renderer-and-onboarding.manifest.yaml`.
11. `pos-amend apply --dry-run` — must exit 0.
12. Amendment commit — message body cites D-build choices + lists
    sub-plan dependents (#36, #37 cleared to dispatch).
13. Update manifest BASELINE to HEAD~1 of the amendment commit (mirrors
    #34 pattern); commit the manifest update if it materially differs
    from the placeholder.
14. `pos-amend apply --dry-run` — re-run, must still exit 0.
15. `pos-amend seal` — advance sidecar + append narrative.
16. Append §14 method-decision record + commit SHAs to the plan doc.

---

## Halt triggers (this dispatch)

- Manifest scope-drift (paths outside `primary-persona/` or universal
  admissions) → halt.
- AC test cannot be written deterministically → halt.
- §2.5 violation found in surrounding code → halt and surface.
- 529 / API overload mid-build → halt; surface partial state per
  feedback_amendment_dispatch_speedups.
- `pos-amend apply --dry-run` red → halt.
- ODD §3.3 forward count mismatch (behaviours vs ACs) → halt.

---

## ODD §2.5 reverse-direction self-check (pre-commit gate)

Before the amendment commit, walk every new line:

- `is_starter` field add → AC35.1.
- `to_agent_md()` body → AC35.2 (frontmatter), AC35.5 (regen), AC35.6
  (sentinel-trace).
- `onboarding.py`'s contributor factory → AC35.3.
- `onboarding.py`'s transcript→write-back → AC35.4.
- `observability.py`'s onboarding events → AC35.7.
- `test_no_sealed_amendments.py` BASELINE → AC35.S.

No defensive `if`s without an AC backing. No platform branches. No
"might-be-useful" surface.
