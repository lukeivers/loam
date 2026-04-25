# Amendment #45 — `merge_session_start` multi-contributor generalisation

**Status:** drafted 2026-04-25 mid-session as the unblock for sub-plan B (two-modes loading mechanism). Re-extension of amendment #37 (hands-off-lifecycle default-agent wiring).

**Companion:** sub-plan B (`docs/rebuild/plans/two-modes-and-multi-workspace/B-mode-loading.md`); halt-finding at `.scratch/claude-output/B-mode-loading-halt-finding-2.md`.

---

## 1. Summary / TLDR

Sub-plan B's mode-aware corpus delivery requires installing a SessionStart hook contributor that emits the dev-mode-conditional CLAUDE.md fragment composition. The current `hands-off-lifecycle/hooks/first_run_settings.merge_session_start` overwrites `hooks["SessionStart"]` with a single-entry list at scaffold time + at supervisor-stanza self-retire, blocking any second contributor. The five non-sealed mechanism shapes the prior B-build agent enumerated all hit this same wall.

The fix is structural and asymmetric: generalise `merge_session_start` to compose multiple SessionStart-contributor stanzas via a contributor registry, and have `build_first_run_stanza` + `build_supervisor_stanza` emit two-inner-hook envelopes (existing first-run/supervisor inner hook + a new "loam-mode-selector" inner hook). The generalisation pays leverage for every future SessionStart contributor (light-touch education in Idea 2, mode-aware prompts, future plugin hooks, etc.).

Sub-plan B's emitter (`tools/loam-mode/src/loam_mode/session_start.py`) + AC.B1/B2/B3/B4/B5 tests land in the same amendment commit. The generalisation is sealed-component change to `hands-off-lifecycle`; B's emitter + tests are dev-discipline (`tools/loam-mode/`).

## 2. Spec-objective placement (per CLAUDE.md §2.5)

Re-extension of amendment #37's surface (hands-off-lifecycle default-agent wiring). v1.0 Architectural — "the harness composes multiple capabilities at session-start without per-capability bespoke wiring" — re-extension of objective-tracker-style D6 integration applied to SessionStart hooks. No new spec v1.x clause; this is a structural generalisation enabling sub-plan B's dev-discipline scope.

## 3. Three-lens analysis

**Lens 1 (Claude-leverage):** SessionStart hook is a Claude Code primitive. The amendment makes pos-v2's SessionStart wiring composable with that primitive's natural list-of-hooks shape, removing a self-imposed single-contributor restriction.

**Lens 2 (Harness + primary-persona value):**
- AC.PO.1: every future SessionStart contributor (mode-aware corpus delivery, light-touch education prompts, plugin hooks) installs cleanly without a bespoke amendment to merge logic. Translation burden absorbed at the harness.
- AC.PO.2: `merge_session_start` becomes a multi-contributor primitive — toolkit expansion. Every contributor reads from a list, all contributors compose at scaffold + supervisor stanza emission.

**Lens 3 (ODD authoring):** five non-sealed mechanisms enumerated and falsified (per halt-finding-2.md §3); sixth path (this amendment) is the structural fix. AC re-extension applied (AC.B2 was originally over-specified; this amendment provides the seam AC.B2 needs).

## 4. Acceptance criteria (AC.45.x)

- **AC.45.1** — `merge_session_start` accepts a list of SessionStart-contributor stanzas (zero or more) and composes them into the resulting `.claude/settings.json` such that the final `hooks["SessionStart"]` list contains all contributor inner-hooks in the order supplied. Existing single-contributor callers remain byte-identical (regression-safe).
- **AC.45.2** — `build_first_run_stanza` emits a multi-inner-hook envelope: the existing first-run shim AS the first inner hook, the loam-mode-selector AS the second inner hook (when sub-plan B's emitter is registered). Both invoke at SessionStart; the first-run shim retains its self-retire path; the loam-mode-selector remains across self-retire.
- **AC.45.3** — `build_supervisor_stanza` emits a multi-inner-hook envelope: the supervisor entry AS the first inner hook, the loam-mode-selector AS the second inner hook (when registered). Existing supervisor-stanza tests remain green for the single-contributor case (when no extra contributor registered).
- **AC.45.4** — Sub-plan B's AC.B1-B5 are satisfied by this amendment's seam. Specifically: B's emitter at `tools/loam-mode/src/loam_mode/session_start.py` (~140 lines per halt-finding-2.md) produces the inner-hook stanza; the contributor registry surface is consumed by `merge_session_start`'s new composition logic.
- **AC.45.5** — Backwards-compat: amendment #32 (session-start context-load gate) and amendment #37 (default-agent wiring) test suites stay green. The contributor registry preserves their existing inner-hook semantics.
- **AC.45.S** — Seal-diff: changes confined to `hands-off-lifecycle/` source + tests, `tools/loam-mode/` (within H19's `tools` admission), and the relevant plan docs. No surface change to other sealed components.

## 5. Behaviour-count check (ODD §3.3 forward)

| # | Declared behaviour | AC |
|---|--------------------|----|
| 1 | merge_session_start composes multiple contributors | AC.45.1 |
| 2 | first-run stanza emits multi-inner-hook envelope | AC.45.2 |
| 3 | supervisor stanza emits multi-inner-hook envelope | AC.45.3 |
| 4 | sub-plan B's AC.B1-B5 are satisfied | AC.45.4 |
| 5 | amendments #32 + #37 stay green | AC.45.5 |
| 6 | seal-diff window respected | AC.45.S |

## 6. Hard constraints

- Single coherent amendment; sealed touch is hands-off-lifecycle only.
- `tools/loam-mode/` extension (B's emitter + tests) lands in same commit (within H19's `tools` admission per amendment #23 convention).
- Backwards-compat is non-negotiable: zero or one contributor must produce IDENTICAL output to the pre-amendment code path.
- No `--amend`. New commits.
- `pos-amend apply` runs BEFORE the amendment commit (per #41/#42 tooling findings).
- Use ABSOLUTE PATH for `pos-amend seal --plan-doc`.
- Pre-author §14 method-decision register heading.
- One test file per AC.

## 7. Out of scope

- Other SessionStart contributors (light-touch-education, plugin hooks etc.) — those compose against the new registry but are separate future work.
- The mode-aware-corpus selector logic itself — that lives in B's emitter (`tools/loam-mode/src/loam_mode/session_start.py`) which lands in this amendment but is dev-discipline within `tools/`.
- Multi-workspace state-file migration (sub-plan C, deferred per master plan).

## 8. Implementation order (suggested — builder's call to refine)

1. Read halt-finding-2.md fully for the constraint analysis.
2. Generalise `merge_session_start` to accept a list of contributor stanzas; verify zero/one-contributor backwards-compat via the existing #37 test suite.
3. Generalise `build_first_run_stanza` + `build_supervisor_stanza` to emit multi-inner-hook envelopes (loam-mode-selector hook is added when registered).
4. Author B's emitter at `tools/loam-mode/src/loam_mode/session_start.py` per F's `select_corpus(mode)` API + halt-finding-2.md's design sketch.
5. Tests: AC.45.1-5 + AC.45.S + AC.B1-B5 (one file per AC).
6. Manifest YAML for the amendment.
7. `pos-amend apply` → amendment commit → `pos-amend seal --plan-doc <abs-path>`.

## 9. Halt triggers

1. Generalising `merge_session_start` would require contributor-stanza schema changes that break amendment #32's test fixtures — halt; #32 fixture amendment is mechanical-and-AC-preserving (per `feedback_loose_AC_text_fix_AC_not_implementation`) but worth surfacing if more than schema-shape extension.
2. The contributor registry shape collides with amendment #37's stanza-emission semantics in unexpected ways — halt; surface the collision.
3. Sub-plan B's emitter requires sealed-component access beyond what `tools/loam-mode/` admits — halt; surface for owner approval.
4. The seal-diff sweep finds a sealed component touched outside hands-off-lifecycle — halt; manifest scope drift.
5. Backwards-compat (AC.45.5) cannot hold for both #32 and #37 simultaneously — halt; the generalisation needs reshaping.

## 10. Bookkeeping (`pos-amend` manifest stub)

Single manifest at `docs/rebuild/plans/amendment-45-merge-session-start-multi-contributor.manifest.yaml` (authored by builder), declaring:
- Component: `hands-off-lifecycle` (sealed; advance SEAL_COMMIT)
- Allowed-prefixes: `hands-off-lifecycle/`, `tools/loam-mode/`, `docs/rebuild/plans/amendment-45-*`
- Frozen-baseline: `false` for hands-off-lifecycle (advance SEAL_COMMIT to amendment SHA per #34/#35/#36/#37 pattern; H19 frozen separately)
- Cross-component: tools/loam-mode (within H19's tools admission)
- Seal-description: `merge_session_start multi-contributor generalisation`

## 11. Decisions for owner ruling (none — autonomous-rulable per session autonomy directive)

The five mechanism shapes the prior B-build agent falsified all hit the same `[new_entry]` wall. Generalisation is the structural fix; the prior agent's recommendation (A) is corpus-grounded; the alternative (B, lighter-touch defer) leaves the programme structurally incomplete. Per the asymmetric memory: this is right-direction asymmetric — small surface change, big downstream win. Per the prime-objective framing: sealed-component touch alone isn't critical-risk when PO ACs are served. Dispatching autonomously per the user's AFK directive.

## 12. Source plan (historical context)

- Master plan: `docs/rebuild/plans/two-modes-and-multi-workspace/MASTER.md`
- Sub-plan B: `docs/rebuild/plans/two-modes-and-multi-workspace/B-mode-loading.md` (post-AC.B4-tightening at commit `d4dc93d`)
- Halt-finding-2: `.scratch/claude-output/B-mode-loading-halt-finding-2.md`
- Predecessor: amendment #37 (default-agent wiring; sealed `c97472e`)

## 13. Dispatch-time additions (brief-phase material)

- WD: canonical (`/Users/lukeivers/ivers-corp-pos-v2/`).
- Plan-before-code: this plan.
- ODD §2.4 + §2.5 audit on every diff line.
- No `git commit --amend`.
- Use `pos-amend apply` BEFORE amendment commit; absolute path on `pos-amend seal --plan-doc`.

## 14. Method-decision record (builder, post-build)

Builder choices made during the build of amendment #45. Section 11
listed no rulings for the owner; the choices below are method-only
decisions per ODD §1.1 (AC text governs outcome; method is the
builder's call).

### D-build.1 — `merge_session_start` generalisation shape

**Choice (a):** Add an optional `extra_inner_hooks: list[dict] | None
= None` parameter to `merge_session_start`, `build_first_run_stanza`,
and `build_supervisor_stanza`. When `None` or empty, behaviour is
byte-identical to the pre-amendment-#45 code path (single inner
hook). When non-empty, additional inner-hook entries are appended to
the outer `{matcher, hooks: [...]}` envelope's `hooks` array.

**Rationale:** Minimal blast radius. Backwards-compat is structural
(zero-or-one contributor literally produces the same JSON bytes via
the `extra_inner_hooks=None` default branch). AC.45.5's #32 and #37
test suites call the pre-amendment signature unchanged. Mirrors
amendment #37's `agent_handle: str | None = None` pattern.

### D-build.2 — Loam-mode contributor home

**Choice:** B's emitter at `tools/loam-mode/src/loam_mode/session_start.py`.
Exposes:
- `compute_session_mode(dev_intent_value)` — pure mapping `"yes" →
  "dev"` else `"user"` (AC.B1).
- `read_dev_intent_safe(workspace_root)` — local YAML-aware fail-
  soft reader (AC.B5). Does NOT import `primary-persona`'s
  `read_dev_intent` to keep the cross-component import surface
  zero (primary-persona is sealed; tools/loam-mode reading the
  same on-disk shape via `personas/<handle>/contract.yaml` is
  by-convention parity, not by-import).
- `emit_session_start_context(workspace_root)` — reads `dev_intent`,
  in user mode returns `""`, in dev mode reads `CLAUDE.dev.md` and
  returns its contents (or fail-soft diagnostic line if absent).
- `build_loam_mode_inner_hook(pos_v2_root)` — pure function
  returning the inner-hook dict (`{type: command, command:
  <python> -m loam_mode.cli session-start, async: False, timeout:
  5}`) for hands-off-lifecycle's stanza builders to compose.

**Rationale:** D-B.1 already locked the standalone-tool home for
B's selector mechanism; this places the SessionStart emitter in the
same package. Keeps sealed-component touch confined to hands-off-
lifecycle (the registry seam) — the tools/loam-mode side is dev-
discipline.

### D-build.3 — `_is_pos_v2_owned` recognition under multi-contributor

**Choice:** Recognise an existing stanza as pos-v2-owned when ANY
inner hook's command points at `first-run.sh`, `pos_session_start.py`,
or `loam_mode.cli session-start`. Pre-amendment behaviour required
EVERY command to match; the new shape requires AT LEAST ONE to match
plus all OTHER commands to also be pos-v2-owned (a wholly user-
authored stanza with one pos-v2-shaped command in it is still backed
up). This preserves backup-on-displacement (T13) for genuinely user-
authored stanzas while admitting the new multi-inner-hook envelopes
amendment #45 ships.

**Rationale:** The function's contract is "is this our stanza?" — a
multi-inner-hook envelope our scaffold writes is still ours. Adding
loam-mode's command to the recognised-set keeps the predicate
correct.

### D-build.4 — Helper-side wiring

**Choice:** `first_run_helper.py` Phase 3d + Phase 6 self-retire +
Phase 4c re-merge call sites pass `extra_inner_hooks=
[loam_mode_hook]` to the stanza builders, where `loam_mode_hook` is
sourced via a lazy `from loam_mode.session_start import
build_loam_mode_inner_hook` import. The import is wrapped in a
try/except so a missing loam-mode install is fail-soft (the helper
emits a diagnostic via `_advance_state` and falls back to the
single-inner-hook path).

**Rationale:** `tools/loam-mode/` is installed in the workspace venv
per F's install convention (mirrors pos-amend's). The helper runs
under that venv; the import resolves at runtime. Fail-soft preserves
AC.45.5 backwards-compat in the degraded "loam-mode missing"
scenario.

### D-build.5 — Dev-intent fail-soft reader

**Choice:** `read_dev_intent_safe` walks `<workspace_root>/personas/`
for any `<handle>/contract.yaml` and reads the `dev_intent` field
via stdlib `yaml`-or-line-scan parser. Returns `"yes"`, `"no"`, or
`"absent"` (the latter on any failure path). Mirrors primary-
persona's `read_dev_intent` semantics without importing it.

**Rationale:** AC.B5's "fail-soft to user-mode" requires the emitter
never raise; encapsulated read with `try/except Exception` returning
`"absent"` satisfies that. Local YAML parser keeps the import
surface light (PyYAML is already a dep).

---

### Post-build commit SHAs

- Plan-doc commit (this addendum): _to be backfilled by `pos-amend
  seal --plan-doc <abs-path>`_.
- Amendment commit: _to be backfilled_.
- Seal commit: _to be backfilled_.
