---
description: "Dev-discipline plan-doc skeleton (13 sections + §14 method-decision register placeholder)."
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
  - HALT_TRIGGERS
  - DECISIONS_SUMMARY
  - HALT_FINDINGS
optional:
  COMPANIONS: ""
  ANCESTOR_RECORD: ""
  IMPACT_BLOCK: ""
  DECISIONS_DETAIL: ""
---
# {{TITLE}} — plan

Dev-discipline work. **NOT** a sealed-component amendment. No `pos-amend` manifest, no `SEAL_COMMIT` bump, no seal commit. Plan-before-code per the dev CDC; corrective new commits land the change.

**Companions:** {{COMPANIONS}}
**Ancestor record:** {{ANCESTOR_RECORD}}

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

## 9. Impact / motivation

{{IMPACT_BLOCK}}

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

(populated by `pos-amend seal --plan-doc <this-file> ...` after build, or appended manually for dev-discipline plans)

### Dependents cleared to dispatch

(placeholder)
