# F1a installer — pos3 draft (Cycle 3 superseded design)

**Archived:** 2026-05-09. **Status:** SUPERSEDED — design will not ship.

## What this is

Two pos3-dirty files captured before reconciliation discard:

- `first_run_scaffold.py.diff` — diff vs canonical HEAD `11f78e64` showing the F1a installer additions: `_PRINCIPLES_INSTALL_MARKER` constant, `resolve_principles_install_choice()` resolver, `_principles_install_block()` helper, `install_principles_reference_universal()` action. ~189 lines.
- `test_F1a_principles_install_resolver.py` — 17 test functions covering AC.F1a.1–10 (CLI prompt resolution, install-location precedence, idempotency).

The installer's intent: at first-run, offer the user a choice ("install loam's principles spec as a reference into your CLAUDE.md, or copy locally, or skip") and resolve it into a concrete install action targeting `framework/docs/principles/odd-principles.md`.

## Why archived

The target file (`framework/docs/principles/odd-principles.md`) does not exist on canonical and was deliberately not created. v0.3.0 Cycle 3 (canonical commit `17d238e9`, 2026-05-08) ran a per-principle audit on the pos3 principles draft and ruled: "33 covered-as-is by canonical odd-methodology.md + memory feedback corpus; 2 gap-filled to CLAUDE.md as Lens 6 + Lens 7. Zero new principles tier document." Without a target file to install, the installer is orphan code.

Subsequent persona-prompt amendment (`docs(persona)`, 2026-05-09) added the two missing persona traits (Calibration + Pruning) to canonical's `personas/primary/prompt.md`, closing the dispersal gap that motivated the pos3 principles draft in the first place. The dispersal across existing surfaces (CLAUDE.md, odd-methodology.md, persona prompt, memory feedback corpus) is now complete; no tier doc is needed.

## Reactivation gate

Re-author from this archive only if a future decision creates a canonical principles tier document. Trigger: explicit owner ratification to author such a doc, naming the gap that motivated revisit.

## Authority chain

- Foundation-revision-rebuild plan §D9 (May 3) — explicit out-of-scope ruling.
- v0.3.0 Cycle 3 commit `17d238e9` (May 8) — dispersal audit.
- Persona-prompt amendment (May 9) — closed dispersal gap.
- Reconciliation report `<workspace>/.scratch/claude-output/pos3-framework-dirty-reconciliation-categorization-2026-05-09.md` — archive decision.
