---
description: "Dev-discipline plan-doc skeleton (13 sections + §14 method-decision register placeholder + §15 references)."
required:
  - TITLE
  - TLDR
  - AC_PREFIX
  - SPEC_PLACEMENT
  - LENS_ANALYSIS
  - ACCEPTANCE_CRITERIA
  - BEHAVIOUR_COUNT
  - HARD_CONSTRAINTS
  - OUT_OF_SCOPE
  - IMPLEMENTATION_ORDER
  - SECTION_9_HEADING
  - SECTION_9_BODY
  - HALT_TRIGGERS
  - DECISIONS_DETAIL
  - DECISIONS_SUMMARY
  - HALT_FINDINGS
optional:
  COMPANIONS: ""
  ANCESTOR_RECORD: ""
  STATUS_LINE: ""
  RESEARCH_PATH: ""
  WORKING_DIRECTORY: "/Users/lukeivers/loam/"
  REFERENCES: |
    - CLAUDE.md (project + global)
    - `plugins/dev-sdlc/docs/odd-methodology.md`, `plugins/dev-sdlc/docs/odd-in-loam.md`
    - `docs/VALUE_PROPOSITION.md`, `docs/STATE.md`, `docs/FUTURE_IDEAS.md`
---
# {{TITLE}} — plan

Dev-discipline work. **NOT** a sealed-component amendment. No `loam amend` manifest, no `SEAL_COMMIT` bump, no seal commit. Plan-before-code per the dev CDC; corrective new commits land the change.

**Status:** {{STATUS_LINE}}
**Working directory:** {{WORKING_DIRECTORY}}
**Companions:** {{COMPANIONS}}
**Ancestor record:** {{ANCESTOR_RECORD}}
**Research:** {{RESEARCH_PATH}}

---

## 1. Summary / TLDR

{{TLDR}}

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

{{SPEC_PLACEMENT}}

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

{{LENS_ANALYSIS}}

---

## 4. Acceptance criteria ({{AC_PREFIX}} — dev-discipline plan)

{{ACCEPTANCE_CRITERIA}}

---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

{{BEHAVIOUR_COUNT}}

---

## 6. Hard constraints

{{HARD_CONSTRAINTS}}

---

## 7. Out of scope (explicit)

{{OUT_OF_SCOPE}}

---

## 8. Implementation order (suggested — builder's call to refine)

{{IMPLEMENTATION_ORDER}}

---

## 9. {{SECTION_9_HEADING}}

{{SECTION_9_BODY}}

---

## 10. Halt triggers (builder halts + signals owner)

{{HALT_TRIGGERS}}

---

## 11. Decisions remaining for the owner to rule on

{{DECISIONS_DETAIL}}

---

## 12. Summary of named decisions (owner-readable)

{{DECISIONS_SUMMARY}}

---

## 13. Halt-and-surface findings encountered during plan authoring

{{HALT_FINDINGS}}

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.x method choices to the builder within the
ACs' outcome bounds. This section is populated post-build.

### D-build.x — (placeholder for the build agent's method choices)

### Test breakdown

(placeholder)

### Backwards-compat verification

(placeholder)

### Commit SHAs

(placeholder; auto-filled by `loam amend seal --plan-doc <ABSOLUTE PATH>` per the seal-automation extension. Pass an ABSOLUTE path to avoid the `Path.relative_to` crash documented at commit `75c4d73`. The amendment commit + seal commit + plan-SHA backfill commit each appear here on completion.)

### Commit SHAs

(populated by `loam amend seal --plan-doc <this-file> ...` after build, or appended manually for dev-discipline plans)

### Dependents cleared to dispatch

(placeholder)

---

## 15. References

{{REFERENCES}}
