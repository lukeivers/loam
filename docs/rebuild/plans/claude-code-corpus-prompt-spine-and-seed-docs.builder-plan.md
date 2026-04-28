# Builder-plan — Claude-Code-corpus prompt-spine + seed docs (amendment α)

**Amendment:** #68 (assigned at dispatch, next free after #67).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**BASELINE:** `ab4cb12610cf25f82258feb5718bb868160f06f3` (HEAD~1 at amendment-commit time; the chore commit immediately preceding α absorbs #67's leftover FUTURE_IDEAS_DRAFT captures so α's diff window is clean).
**Plan:** `docs/rebuild/plans/claude-code-corpus-prompt-spine-and-seed-docs.md`.
**Manifest:** `docs/rebuild/plans/claude-code-corpus-prompt-spine-and-seed-docs.manifest.yaml`.
**Locked research:** `docs/rebuild/plans/research/persona-capability-knowledge-grounding-research.md`.

## §0. Build context (D-shape path translation)

The plan was authored 2026-04-26, mid-D-migration. Plan paths
of the form `primary-persona/templates/...` translate to
`framework/primary-persona/templates/...` under the post-D
shape (commit `8842042` sealed the single-framework restructure
on 2026-04-28). All plan-AC trace-targets are translated
identically: `<sealed-comp>/...` → `framework/<sealed-comp>/...`.

L plan (`primary-persona-conversational-onboarding-and-default-archetype.md`)
is **sealed** at SEAL_COMMIT `040e577`. Its eleven named sections
exist in `framework/primary-persona/templates/persona-template/prompt.md`:

- five top-value-trait headings: `### Autonomy`,
  `### Asymmetric problem solving`, `### Parallelism`,
  `### Test theories before acting on them`, `### Self-correction`.
- six operational-rule headings: `### Lean on the harness`,
  `### Use the right tool`, `### Codify what repeats`,
  `### Structural enforcement default`, `### ODD-shaped internal model`,
  `### Light-touch narration on choices`.

α composes additively: a new `## Capability leverage spine`
top-level section + a new `### Lean on the corpus` operational
rule sibling to L's six.

D-OWNER.1 ruling: **L first, then α** (L is sealed; α slots
in additively).
D-OWNER.2 ruling: **strict off-limits** on
`framework/primary-persona/src/` — halt-trigger §9.1.
D-OWNER.3 ruling: **(a) populated `source_fetch_ts` at
α-author-time** — the build agent fetches each canonical
source once and records the fetch timestamp.
D-OWNER.4 ruling: **(a) directory layout matches β's URI
partition exactly** — `claude-code/` (Class A),
`harness/` (Class A-prime), `best-practice/` (Class B).

## §1. Selected seed primitives (Class A) — selection rationale

Per AC.α.3, ≥ 5 seed Class A docs. Per locked research §2.1
the highest-leverage primitives the persona reaches for daily
are: `/schedule`, `/loop`, background-agent dispatch, hook
events, MCP server registration, subagent / Task dispatch,
skills, settings.json hooks, plus the pos-v2 harness primitives
named in §2.3. The builder selects **5 seeds** balancing
Claude-Code (4) + Class A-prime harness (1):

1. **`claude-code/schedule.md`** — `/schedule` cron-shaped
   scheduler skill. Highest-frequency Lens-1 trigger ("daily
   briefing" / "every Monday" / "remind me each morning").
   Source: the in-session skill description for `/schedule`
   (carried in this session's available-skills list, ts
   2026-04-28). Pre-β, the on-disk source-of-truth for the
   skill is the user's `~/.claude/skills/` (not in the
   canonical pos-v2 tree); `source_url` records this.
2. **`claude-code/loop.md`** — `/loop` self-pacing recurring
   skill. Sibling to `/schedule`; the spine's
   recurring-work index entry routes between them. Source:
   in-session skill description.
3. **`claude-code/background-agents.md`** — Task tool +
   `run_in_background` Bash + Monitor. Highest-leverage
   parallelism primitive; user has ruled "background agents
   by default" (MEMORY.md feedback rule). Source: the Task
   tool surface visible in this agent dispatch + the Bash
   tool's `run_in_background` parameter docs.
4. **`claude-code/hooks.md`** — settings.json hook event
   surface (`SessionStart`, `UserPromptSubmit`,
   `PreToolUse`, `Stop`, `SubagentStop`, etc.). Lens-2
   structural-enforcement reach. Source: the
   `update-config` skill description visible in this
   session's skill list + pos-v2's
   `framework/hands-off-lifecycle/` settings.json fragments.
5. **`harness/scope-of-work.md`** — pos-v2's scope-of-work
   primitive (Class A-prime). Highest-leverage harness
   primitive — every plan/objective the persona authors
   binds to a scope. Source: `framework/scope-of-work/docs/api-reference.md`
   (component's own contract) + `framework/scope-of-work/docs/architecture.md`.

Counted: 5 seeds total ≥ 5 minimum. AC.α.3 satisfied.

Selection rationale per AC.α.3 (substitution allowed if
equal-or-greater leverage with rationale): the four Claude
Code picks cover the four most-common Lens 1 dispatch
shapes (recurring, self-paced, parallel, automated); the
harness pick covers the most-common Lens 2 primitive
(scope-binding). Other candidates from the plan §4 list
(MCP registration, Agent tool, skills marketplace,
settings.json, Telegram, memory-system MCP) are deferred
to subsequent corpus authoring (β / δ accrual) — α's seed
count is a demonstration of the pattern, not full coverage
(plan §11 risk #5).

## §2. Selected seed patterns (Class B) — selection rationale

Per AC.α.4, ≥ 3 seed Class B docs. Per locked research §2.6
+ MEMORY.md, owner-articulated patterns ladder cleanly to
Class B entries. The builder selects **3 seeds**:

1. **`best-practice/background-agents-by-default.md`** —
   "background agents by default for multi-artefact
   authoring or ~30 s+ generation." Cross-references
   `[primitive: claude-code:background-agents]`. MEMORY.md
   feedback rule; Luke's directive 2026-04-26. Trust
   marker: `sources_count: 1` (Luke directive);
   `validation_count: 8+` (every dispatched amendment in
   the program follows this rule); `owner_acked: true`.
2. **`best-practice/scope-only-dispatch.md`** —
   "agent prompts: scope only, no method prescription."
   Cross-references `[primitive: claude-code:background-agents]`.
   MEMORY.md feedback rule; Luke's directive 2026-04-26.
   Trust marker: `sources_count: 1`; `validation_count: 5+`
   (multiple amendment dispatches follow it);
   `owner_acked: true`.
3. **`best-practice/verify-dispatch-before-sending.md`** —
   "verify the dispatch is the right action before sending
   it." Cross-references
   `[primitive: claude-code:background-agents]` +
   `[primitive: harness:scope-of-work]`. MEMORY.md feedback
   rule. Trust marker: `sources_count: 1`;
   `validation_count: 3+`; `owner_acked: true`.

Counted: 3 seeds total ≥ 3 minimum. AC.α.4 satisfied.

Selection rationale: all three are top-of-mind owner
directives Luke has explicitly named in MEMORY.md feedback
files; all three pair with seed Class A entries from §1,
demonstrating the cross-class fetch pattern.

## §3. File layout

New files:

```
docs/rebuild/capability-corpus/
  AUTHORING.md
  claude-code/
    schedule.md
    loop.md
    background-agents.md
    hooks.md
  harness/
    scope-of-work.md
  best-practice/
    background-agents-by-default.md
    scope-only-dispatch.md
    verify-dispatch-before-sending.md
```

Edited file:

```
framework/primary-persona/templates/persona-template/prompt.md
  + ## Capability leverage spine    (new top-level section)
  + ### Lean on the corpus           (new entry under existing
                                      ## Operational rules section)
```

New tests under `framework/primary-persona/tests/` (one per AC):

```
test_AC_alpha_1_capability_leverage_spine.py
test_AC_alpha_2_authoring_guide_present.py
test_AC_alpha_3_class_a_seed_count_and_schema.py
test_AC_alpha_4_class_b_seed_count_and_schema.py
test_AC_alpha_5_schema_discipline_all_seed_docs.py
test_AC_alpha_6_L_eleven_sections_unchanged.py
test_AC_alpha_7_scaffold_passthrough.py
test_AC_alpha_8_no_capability_content_outside_admitted_paths.py
```

(AC.α.S is verified by the existing `test_no_sealed_amendments.py`
seal-diff harness — no new test file needed.)

## §4. AC test mapping (one test file per AC)

| AC | Test file |
|----|-----------|
| AC.α.1 | `test_AC_alpha_1_capability_leverage_spine.py` |
| AC.α.2 | `test_AC_alpha_2_authoring_guide_present.py` |
| AC.α.3 | `test_AC_alpha_3_class_a_seed_count_and_schema.py` |
| AC.α.4 | `test_AC_alpha_4_class_b_seed_count_and_schema.py` |
| AC.α.5 | `test_AC_alpha_5_schema_discipline_all_seed_docs.py` |
| AC.α.6 | `test_AC_alpha_6_L_eleven_sections_unchanged.py` |
| AC.α.7 | `test_AC_alpha_7_scaffold_passthrough.py` |
| AC.α.8 | `test_AC_alpha_8_no_capability_content_outside_admitted_paths.py` |
| AC.α.S | `test_no_sealed_amendments.py` (existing; advanced by `pos-amend apply`) |

ODD §8.2.14 byte-content discipline: `test_AC_alpha_5` reads a
sample seed doc and asserts named-section schema (not just
file existence) — the cross-cutting structural check is a
byte-content verification on the on-disk content.

## §5. Order of operations

1. Author manifest (DONE).
2. Author this builder-plan (DONE).
3. Land authoring guide → `docs/rebuild/capability-corpus/AUTHORING.md` (AC.α.2).
4. Land seed Class A docs (AC.α.3, AC.α.5).
5. Land seed Class B docs (AC.α.4, AC.α.5).
6. Land prompt.md spine + new operational rule (AC.α.1, AC.α.6).
7. Land tests AC.α.1..AC.α.8.
8. Run touched-component test scope (`framework/primary-persona/tests/`).
9. `pos-amend apply --dry-run` — must exit 0.
10. `pos-amend apply <manifest>` — advances BASELINE + sidecar +
    widens admissions (BEFORE the amendment commit so changes
    bundle into the feature commit).
11. Stage everything; create amendment commit (no `--amend`).
12. `pos-amend seal --plan-doc <abs-path>` — backfill SHAs + create
    seal commit.
13. Final `pos-amend apply --dry-run` — must exit 0.

## §6. Halt-and-surface budget

Per plan §9 + dispatch brief, halt triggers monitored throughout:
1, 2, 3, 4, 5, 6 (β/δ/γ scope creep), 7, 8, 9, 10, 11, 12.
60-min wall-time budget per §9.12.
