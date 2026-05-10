---
description: "Memory-doc skeleton (front-matter + Definition + How-to-apply + Composes-with sections). Third member of the template family alongside dispatch + plan templates."
required:
  - NAME
  - DESCRIPTION
  - DEFINITION_BODY
  - HOW_TO_APPLY_BODY
optional:
  TYPE: "feedback"
  ORIGIN_SESSION_ID: ""
  CAPTURED_DATE: ""
  COMPOSES_WITH: |
    (named principles this composes with; one line per derivation/relationship per the M5 procedural rule)
  STATUS: "active"
  SOURCE: |
    (citation: telegram message id / build report path / commit SHA / equivalent)
  WHY_BODY: |
    (one to three paragraphs naming the failure mode this rule prevents and the underlying mechanism)
---
---
name: {{NAME}}
description: {{DESCRIPTION}}
type: {{TYPE}}
originSessionId: {{ORIGIN_SESSION_ID}}
captured: {{CAPTURED_DATE}}
status: {{STATUS}}
---

# {{NAME}}

{{DEFINITION_BODY}}

## Why

{{WHY_BODY}}

## How to apply

{{HOW_TO_APPLY_BODY}}

## Composes with

{{COMPOSES_WITH}}

## Source

{{SOURCE}}
