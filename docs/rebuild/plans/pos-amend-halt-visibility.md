# pos-amend halt visibility — plan

Dev-discipline work. **NOT** a sealed-component amendment. `tools/pos-amend/`
is not a sealed component (no `tests/SEAL_COMMIT` sidecar). No
`pos-amend` manifest, no seal commit. Plan-before-code per the dev CDC.

**Status:** plan (pre-build). 2026-04-26.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Companions:** `harness-usage-audit-2026-04-26.md` cleanup dispatch (item #5).
**Ancestor record:** dispatched 2026-04-26 by main session for canonical
working-tree cleanup.

---

## 1. Summary / TLDR

`pos-amend`'s halt sites already emit non-zero exit codes. The
`seal` command's halt diagnostics already emit to **stdout** with
the prefix `halt: <klass>` (verified empirically: `pos-amend seal …
2>/dev/null` still shows the halt body and exits with rc=3).

The remaining gaps:

1. `tools/pos-amend/src/pos_amend/commands/template.py` and
   `tools/pos-amend/src/pos_amend/commands/new_plan.py`'s
   `_emit_diagnostic` write **only** to stderr. In stderr-dropped
   contexts (Bash-tool eval-wrapper, some CI redirections) those
   halts are invisible.
2. The `halt:`/`error:` prefix is inconsistent across commands
   (seal: `halt:`; template/new_plan: `<kind> error [<klass>]:`).
   A consistent uppercase `HALT:` prefix makes halts grep-/scan-
   friendly across all subcommands.

The fix is small: add a stdout `HALT: <klass>` line at every
diagnostic site (defense-in-depth alongside any existing stderr
emission), and add one regression test that asserts the halt
visibility shape under a stderr-dropped invocation.

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

`tools/pos-amend/` is a dev-discipline tool — not part of pos-v2's
runtime spec. Halt-visibility consistency is a quality-of-life
fix for the dispatcher (Lens 2: harness toolkit). Cite: ODD §1.1
(method-level choices builder's call), CLAUDE.md design lenses.

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

The dispatcher (primary persona / Claude agents) reads pos-amend
output through the Bash tool. Stdout is reliably captured;
stderr is sometimes dropped by harness wrappers. Emitting halts
on stdout aligns with the harness's reliable channel.

### Lens 2 — Harness + primary-persona value

The harness's pos-amend tool is one of the primary persona's most-
used surfaces (every amendment cycle). A halt that appears as
silent rc=0 wastes a dispatch round and forces the persona to
re-investigate. Visible halts = lower dispatch friction.

### Lens 3 — ODD authoring

- Objective: every halt produced by `pos-amend` is visible on
  stdout regardless of stderr handling.
- Acceptance criteria: see §4. Method (where to add the print
  line, exact prefix capitalisation): builder's call.
- Behaviour count: see §5.

## 4. Acceptance criteria (AC.PA-hv — dev-discipline plan)

- **AC.PA-hv.1** — every `_emit_diagnostic` callsite in pos-amend
  produces a `HALT: <klass>` (or equivalently scannable) line on
  **stdout** in addition to whatever else it currently emits.
- **AC.PA-hv.2** — stdout-only context (caller redirects 2>/dev/null)
  still shows the halt class + body for every documented halt
  (dirty-tree, plan-doc-missing-section-14, invalid-slug,
  refuse-overwrite, etc.).
- **AC.PA-hv.3** — exit codes for halt paths are unchanged
  (non-zero per existing taxonomy: 1 / 2 / 3).
- **AC.PA-hv.4** — backwards compat: existing test assertions
  about diagnostic content (e.g. test_AC_D_np_4 checks `failure_class`
  in stderr or stdout) pass without modification or with a
  trivial assertion-broadening.
- **AC.PA-hv.5** — one regression test in
  `tools/pos-amend/tests/test_halt_visibility.py` exercises a
  representative seal halt (dirty-tree) under captured-stdout-only,
  asserts the `HALT:` prefix appears on stdout and rc != 0.

## 5. Behaviour-count check

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Halt diagnostic visible on stdout | AC.PA-hv.1 / AC.PA-hv.2 |
| 2 | Exit codes preserved | AC.PA-hv.3 |
| 3 | Existing tests still pass | AC.PA-hv.4 |
| 4 | Regression-guard test exists | AC.PA-hv.5 |

## 6. Hard constraints

1. **No `--amend`.** Corrective new commits only.
2. **Scope fence.** Only `tools/pos-amend/src/pos_amend/commands/seal.py`,
   `…/commands/new_plan.py`, `…/commands/template.py`, and
   `tools/pos-amend/tests/test_halt_visibility.py` (new file).
3. **No new third-party dependency.** Stdlib only.
4. **Backward-compat preserved.** Existing test file assertions
   continue to pass; existing diagnostic content is preserved
   (HALT line is purely additive).
5. **No source edits outside pos-amend.**

## 7. Out of scope (explicit)

- Refactoring `_emit_diagnostic` into a shared helper across
  commands (the three sites are small enough; cross-file
  refactor would expand scope unnecessarily).
- Changing exit-code taxonomy.
- Removing existing stderr emissions (defense-in-depth: keep
  both).
- Anything related to plan-doc skeleton §14 / §15 (already
  delivered by amendment #51).

## 8. Implementation order

1. Read seal.py + template.py + new_plan.py `_emit_diagnostic`
   sites.
2. Edit seal.py: change `print(f"halt: {checkpoint.klass}")` to
   `print(f"HALT: {checkpoint.klass}")` (uppercase consistency).
3. Edit template.py + new_plan.py: prepend a stdout `HALT:
   <failure_class>` line in `_emit_diagnostic`, keep the
   existing stderr emission unchanged.
4. Write `tools/pos-amend/tests/test_halt_visibility.py` with
   one test exercising the dirty-tree halt (uses tmp git tree
   + dirty file; runs seal subcommand via subprocess capturing
   stdout only; asserts `HALT:` line + rc != 0).
5. Run pos-amend test suite — must remain green.
6. Commit.

## 9. Impact / motivation

Captured in FUTURE_IDEAS_DRAFT.md (Bash-tool eval-wrapper drops
stderr) and in this dispatch (item 5). The fix removes a
recurring dispatcher friction.

## 10. Halt triggers

1. Test suite regresses on existing assertions. Halt; investigate.
2. A halt site can't easily emit to stdout (e.g. context where
   stdout is also unavailable). Halt; surface.
3. Wall-time exceeds 30 minutes. Halt with current state.

## 11. Decisions remaining for owner

(none — scope and AC set are tight; method choices belong to
the builder per ODD §1.1.)

## 12. Summary of named decisions

(no decisions surfaced for owner ruling.)

## 13. Halt-and-surface findings encountered during plan authoring

- **Item 4 (plan-doc skeleton §14 / §15 auto-emission) is
  already complete** by amendment #51 (`tools/pos-amend/templates/
  plan/dev-discipline.md` already emits §14 + §15; verified via
  `pos-amend new-plan --render` mid-dispatch). Surfaced here so
  the dispatcher does not re-do work.
- **Empirical observation contradicts a part of the dispatch's
  premise:** seal halts already emit to stdout (verified live
  via `pos-amend seal <manifest> 2>/dev/null` showing rc=3 +
  visible halt body). The "silent rc=0" symptom in the
  FUTURE_IDEAS entry was likely a different code path or
  Bash-tool quirk; this plan still adds defense-in-depth +
  regression guard to prevent future regression.

## 14. Method-decision record (builder, post-build)

(populated post-build)

### Commit SHA

(populated post-build)

## 15. References

- CLAUDE.md (project + global)
- `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- `docs/rebuild/FUTURE_IDEAS_DRAFT.md` (Bash-tool eval-wrapper
  stderr-drop entry, 2026-04-26)
- `tools/pos-amend/src/pos_amend/commands/seal.py`
- `tools/pos-amend/src/pos_amend/commands/template.py`
- `tools/pos-amend/src/pos_amend/commands/new_plan.py`
