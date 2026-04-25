# Sub-plan B — Two-mode loading mechanism

**Status:** authored 2026-04-25. Research-and-planning only. **Dev-
discipline plan** — NOT a sealed-component amendment. No
`pos-amend` manifest, no `SEAL_COMMIT` bump.

**Master plan:** `MASTER.md`.

---

## 1. Summary / TLDR

When the workspace's `dev_intent` answer (sub-plan A) is `"yes"`, the
session-start surface auto-loads the dev-time machinery (pos-amend's
read paths, plan docs, methodology docs, dev CDCs, sealed-component
seal narratives). When the answer is `"no"` (or absent — defensive
default per locked owner ruling 4), the session-start surface loads
only runtime-harness artefacts and end-user-facing docs.

The mechanism:

1. A `.claude/settings.json` SessionStart hook (or equivalent settings
   surface) calls a small selector that reads `dev_intent_storage_path`
   (sub-plan A's resolver) and chooses between two CLAUDE.md fragments
   (or assembles one from a base + dev-extension).
2. The session-start corpus is mode-aware: in user mode it contains
   F's `always_loaded`; in dev mode it contains `always_loaded ∪
   dev_only`. Mechanism is the builder's call (CLAUDE.md fragment
   composition, hook-time wrap-around, settings.json field, etc.) —
   sealed-component code (including `primary-persona/src/session_start_gate.py`)
   is unchanged per B's dev-discipline §2 framing.
3. Mode is read at session-start time — no live mid-session toggle in
   v1 (per D-MASTER.4 (a)). Re-running onboarding (A's flow) is the
   change path.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

§2.5 reads: *"Before scoping anything as a sealed-component amendment,
name the specific spec objective ... If I can't name one, the work is
dev-discipline (CLAUDE.md, docs, CDCs, tools/), not a sealed-component
cycle."*

**No spec v1.x objective names "two-mode CLAUDE.md auto-load."** The
mechanism is operational developer-tooling: it composes against
Claude Code's settings + hook surfaces and against the workspace-
bootstrap scaffold's existing CLAUDE.md template (the scaffold owns
CLAUDE.md authoring; this plan changes what the scaffold writes).

Dev-discipline territory by every property §2.5 names:

- The selector lives under `tools/` (proposed: `tools/loam-mode-selector/`
  or — more likely — a small Python module shipped under
  `workspace-bootstrap/src/workspace_bootstrap/dev_mode/` that the
  hook calls; selecting the right home is a method choice in §11
  below).
- No spec objective backs "CLAUDE.md splits into two."
- Sealed-component code is not modified by B; the scaffold's CLAUDE.md
  template is workspace-supplied content per STATE.md rule #4 (the
  framework template sources the dev-extension fragment from the repo's
  own CLAUDE.md sections, but the scaffold writes whichever fragment
  the user's mode dictates).

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage

This sub-plan is the highest-leverage Claude-composition in the
programme:

- **`.claude/settings.json` + SessionStart hooks.** Already in use by
  hands-off-lifecycle's first-run wiring. The same shape applies here:
  a tiny shell or Python entry-point reads `dev_intent`, returns the
  CLAUDE.md path (or composes the CLAUDE.md content) for that session.
- **Slash commands as toggle UX (deferred per D-MASTER.4 (a)).** The
  v1 toggle path is "re-run onboarding"; future iteration may add a
  slash command, composing on Claude Code's slash-command primitive.
- **The `update-config` skill (already declared in this thread's skill
  surface).** The skill is the natural agent for end-user tweaks to
  `.claude/settings.json` once the hook is registered; it does not
  re-implement the registration but lets the user reach for it
  directly.

If at design time it turns out CLAUDE.md cannot be loaded conditionally
without changes to Claude Code itself (master halt trigger 4), the
fallback is two static CLAUDE.md files (`CLAUDE.md` always loaded;
`CLAUDE.dev.md` injected via SessionStart hook's `additionalContext`).

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden
between the user's natural-language intent and AI-effective execution?*

Yes — the load shape is now driven by the user's stated intent.
Today the user implicitly accepts dev-mode load by virtue of cloning
the repo and running session-start; B inverts that — the load tracks
the user's stated answer.

**Harness test.** *Does this add to the toolkit the primary persona
can draw from?*

Yes — the persona gains a deterministic "is this a dev session?"
signal and a deterministic auto-load partition (sub-plan F) it can
name in dispatches and slash commands. Future ideas (Idea 2 light-
touch education's "you're doing dev work; here's what `pos-amend`
does" surfacing) compose against B.

### Lens 3 — ODD authoring

ACs below are outcome-shaped. Method (the selector's exact location,
the hook's exact shape, the CLAUDE.md fragment-assembly mechanism) is
the builder's call.

---

## 4. Acceptance criteria (AC.B1–AC.B6)

Each AC maps to at least one test in
`tools/loam-mode/tests/` or
`workspace-bootstrap/tests/test_dev_mode.py` (location is a method
decision; AC.B6 names test discoverability, not location).

### AC.B1 — Mode-selector reads `dev_intent` from the workspace-local resolver

A pure function `compute_session_mode(workspace_root) -> Literal["dev",
"user"]` returns `"dev"` iff `read_dev_intent(workspace_root) == "yes"`,
else `"user"` (`"absent"` and `"no"` both map to `"user"`).

**Test shape:** unit test invokes the selector against three fixture
workspaces — dev_intent yes, no, absent — and asserts the mapping.

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.B2 — SessionStart hook installs the selector at first-run

When workspace-bootstrap's first-run scaffold runs, the resulting
`.claude/settings.json` includes a SessionStart hook entry that calls
the selector and emits its output as `additionalContext` (or
configures `read_data` so the persona consumes the mode-flag). The
exact surface (hook command, env-var passthrough) is the builder's
call.

**Test shape:** scaffold a fixture workspace, read its written
`.claude/settings.json`, assert a SessionStart hook entry exists whose
target invokes the selector. (Not asserting the selector runs in the
test — that's covered by AC.B1.)

**Maps to:** AC.PO.1 (translation burden absorbed at first-run scaffold
time) + AC.PO.2 (extends the settings.json scaffold primitive).

### AC.B3 — Dev-mode CLAUDE.md fragment is loaded only in dev sessions

Two CLAUDE.md surfaces exist:

- The base CLAUDE.md (always loaded by Claude Code per its built-in
  behaviour).
- A dev-extension surface that auto-loads only when the selector
  returns `"dev"`.

The dev-extension surface is loaded via the SessionStart hook's
`additionalContext` channel in `"dev"` sessions and is silently absent
in `"user"` sessions. Implementation note (builder's call): the
extension may be a separate `CLAUDE.dev.md` file, an inlined section
of the base file with conditional rendering, or any other shape that
satisfies the AC.

**Test shape:** integration-style — given a fixture workspace with
`dev_intent="yes"`, assert the SessionStart payload contains the dev-
extension content. With `dev_intent="no"`, assert it does not.

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.B4 — Mode-aware session-start corpus

The persona's session-start corpus is mode-aware. In user mode the
persona receives only F's `always_loaded` partition. In dev mode the
persona additionally receives F's `dev_only` partition. Mechanism is
the builder's call (CLAUDE.md fragment composition, hook-time
context-injection wrapper, settings.json field, or any other shape
that achieves the outcome). The existing
`primary-persona/src/session_start_gate.py` is unchanged — B's
mechanism composes around it rather than modifying it. (Note: B is
dev-discipline per §2; sealed-component code is not modified.)

**Test shape:** end-to-end test fires the SessionStart hook flow
against fixture workspaces of each mode and asserts the persona's
`additionalContext` (or equivalent loaded-corpus surface) contains
F's `always_loaded` paths in both modes and F's `dev_only` paths only
in dev mode. The exact mechanism observable in the test is
method-level (whichever shape the builder chose for the wrap-around
composition).

**AC text precision note (post-#42 tightening 2026-04-25):** the
original AC.B4 text named the specific function
`session_start_gate.discover_baseline_corpus` as the mode-aware
surface, which (a) prescribed method, (b) required modifying a
sealed Phase-2 component contradicting B's dev-discipline §2 framing.
Per `feedback_loose_AC_text_fix_AC_not_implementation`, the AC was
tightened to outcome-shape (this version). Implementation behaviour
is unchanged in spirit; the mechanism is the builder's call within
the dev-discipline scope.

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.B5 — Selector failure is fail-soft to user-mode

If the selector raises (storage missing, JSON parse error, schema
mismatch), the SessionStart hook returns `"user"` and emits a
diagnostic via OTel (`pos.dev_mode.selector_failed`). The session
proceeds in user-mode rather than blocking on selector error.

**Test shape:** unit test injects a corrupt storage file; assert
selector returns `"user"` and emits the diagnostic event.

**Maps to:** AC.PO.1 (the persona never has to translate selector
errors to user) + AC.PO.2 (observability primitive extended).

### AC.B6 — Mode shift requires re-running onboarding (v1)

The amendment does NOT ship a slash-command toggle for `dev_intent`.
A documentation note (in user-facing help / README) names the change
path: re-run the persona's onboarding flow (or, until A's owner-ruled
shape ships, manually edit the contract field).

**Test shape:** docs-only — asserts a documented path exists. (This
AC is testable as "the documented note exists at the named location";
no Python test required.)

**Maps to:** AC.PO.1 (sub-plan A is the toggle path; B inherits its
discipline).

---

## 5. Out of scope

- Slash-command toggle (D-MASTER.4 (b)/(c)). Deferred.
- Auto-detecting dev-intent from environment. Forbidden by locked
  owner ruling 4.
- Cross-workspace mode hints. Forbidden by locked owner ruling 4.
- Per-component mode toggles ("memory-system in dev mode but
  scope-of-work in user mode"). Mode is a single boolean per
  workspace.
- Reading mode at any time other than session-start. v1.

---

## 6. Halt triggers

1. **CLAUDE.md cannot be loaded conditionally without modifying Claude
   Code itself.** Halt and surface (master halt trigger 4); the
   workaround is two static CLAUDE.md files + SessionStart-hook
   injection of the dev extension.
2. **The settings.json SessionStart hook surface conflicts with
   amendment #37's first-run-default-agent-wiring.** Halt and surface;
   this is a #37 re-extension that needs owner approval.
3. **AC.B4's mode-aware-corpus mechanism requires modifying any sealed
   component.** Halt — sub-plan B is dev-discipline; if it needs
   sealed-component code, the design is wrong (the AC was tightened
   2026-04-25 to outcome-shape; mechanism is the builder's call within
   dev-discipline scope and must compose around sealed code, not modify
   it).
4. **The selector's storage read introduces a circular dependency**
   (e.g. the selector reads from a state file the SessionStart hook is
   responsible for writing). Halt and surface; the design needs
   reshaping.

---

## 7. Bookkeeping

Dev-discipline plan; no `pos-amend` manifest. The work lives at:

- `tools/loam-mode/` (proposed; method-level — builder chooses) OR
  `workspace-bootstrap/src/workspace_bootstrap/dev_mode/` if the
  selector is most naturally a workspace-bootstrap submodule.
- `.claude/settings.json` fragment update: workspace-bootstrap's
  scaffold writes the selector hook entry.
- `CLAUDE.md` (the dev-extension content): sourced from the existing
  CLAUDE.md sections labeled dev-only (per F's partition).

If the work creates a new `tools/` subdir:
- Plan-doc skeleton: `tools/loam-mode/README.md` (one-pager).
- Tests: `tools/loam-mode/tests/`.

If the work lives inside workspace-bootstrap:
- The amendment becomes a sealed-component amendment to
  workspace-bootstrap. **HALT TRIGGER:** that contradicts the §2
  framing here. If the builder concludes the work is sealed-component,
  re-author this sub-plan with the corresponding spec-objective
  framing.

---

## 8. Dispatch-time additions

When B's brief is drafted:

- WD: canonical.
- Plan-before-code: builder writes `loam-mode-selector.builder-plan.md`
  first.
- Sub-plan F is a hard dependency input (its `always_loaded` and
  `dev_only` partition data is what B's mechanism consumes). F MUST
  land before B's build dispatches; ordering revised 2026-04-25 from
  the original A → E → B → F to A → E → F → B per the AC.B4 tightening
  + #43 build's halt finding (B's mechanism is small once F's data is
  fixed).
- ODD §2.4 + §2.5 audit run on every diff line.
- No `git commit --amend`.

---

## 9. Lens-2 trace blocks

| AC | AC.PO.1 | AC.PO.2 |
|----|---------|---------|
| AC.B1 | Mode is computed once, persona reads it. | Pure-function selector — toolkit primitive. |
| AC.B2 | Hook installs at scaffold time; user does not configure it. | Extends the .claude/settings.json scaffold surface. |
| AC.B3 | Dev artefacts never reach a user session. | Composes on existing additionalContext channel. |
| AC.B4 | Corpus is mode-aware without user-facing filtering. | Composes around amendment #32's gate (sealed code unchanged); F's partition consumed at composition time. |
| AC.B5 | Selector failure does not propagate to the user. | Observability extended. |
| AC.B6 | Toggle path is the existing onboarding surface. | Composes on sub-plan A. |

---

## 10. Decision register (sub-plan-local)

| Code | Question | Recommendation |
|------|----------|----------------|
| D-B.1 | Selector home: standalone `tools/loam-mode/` or `workspace-bootstrap` submodule? | Standalone tool. The selector is dev-discipline tooling per §2; living inside workspace-bootstrap forces a sealed-component amendment which the §2 framing forbids. |
| D-B.2 | Dev-extension delivery: separate `CLAUDE.dev.md` or inline + filtered? | Separate file. Tested via simple file-presence check; filtering complicates the test surface. |
| D-B.3 | Mode caching: per-session or recompute every read? | Per-session. The dev_intent answer changes only via onboarding, which is once-per-session work; caching avoids repeated I/O. |
| D-B.4 | If a future amendment moves dev_intent storage (D-MASTER.1 (b)), does the selector need a code change? | No — the selector reads through sub-plan A's `read_dev_intent` resolver, not the storage file directly. AC.A5 and AC.A6 give the seam. |

---

## 11. Builder freedom (method-only notes)

Builder chooses: the selector's exact CLI surface (subcommand, env-
var, hook-payload), the dev-extension delivery (file injection vs.
inlined section), the test fixture's tmp-fs shape, the hook
registration order in `.claude/settings.json`, the OTel event names
(beyond AC.B5's `pos.dev_mode.selector_failed`).

---

## 12. Test register

| AC | Suggested test file | Suggested test function |
|----|---------------------|--------------------------|
| AC.B1 | `tools/loam-mode/tests/test_selector.py` | `test_AC_B1_compute_session_mode` |
| AC.B2 | `workspace-bootstrap/tests/test_dev_mode_scaffold.py` | `test_AC_B2_scaffold_writes_session_start_hook` |
| AC.B3 | `workspace-bootstrap/tests/test_dev_mode_scaffold.py` | `test_AC_B3_dev_extension_loaded_iff_dev_mode` |
| AC.B4 | `tools/loam-mode/tests/test_corpus_mode_aware.py` (or wherever the builder lands the mode-aware composition test — outside any sealed component) | `test_AC_B4_corpus_mode_aware_end_to_end` |
| AC.B5 | `tools/loam-mode/tests/test_selector.py` | `test_AC_B5_selector_failure_fail_soft_to_user` |
| AC.B6 | docs-only | `docs/rebuild/help/dev-mode.md` (path is a method decision) |

---

## 13. Asymmetric observations

1. **The selector being three lines of Python is the asymmetric win.**
   `read_dev_intent(workspace_root) == "yes"` collapses the entire
   mechanism to a function call. Effort: low. Leverage: high.

2. **AC.B6's "no slash-command toggle" is an inverse-asymmetric win.**
   A slash command is medium cost (registration, settings.json
   surface, persona-voice integration) for low marginal leverage
   (re-running onboarding is already the v1 toggle path). Dropped
   from v1 per D-MASTER.4 (a).

3. **The fail-soft default to user-mode is asymmetric.** A failed
   selector defaulting to dev-mode would silently leak dev artefacts
   to end users; defaulting to user-mode silently denies dev
   artefacts to a developer (recoverable: re-run onboarding). The
   asymmetry is in the cost of being wrong; AC.B5 codifies the safer
   direction.
