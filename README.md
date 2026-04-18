# pOS v2 — greenfield rebuild

This branch is the new pOS rebuild. Greenfield. Zero carryover from the
current pOS framework on `main`.

## Scope of the current branch state

This commit covers the **memory-system prototyping phase** only — see
`memory-system/` for the prototype code, synthetic test set, evaluation
harness, and bundled documentation. The full nine-adaptation-layer build
follows in a separate brief, gated on the prototype findings.

## What this branch is NOT

- Not a fork of `main`. Different history, different language, different scope.
- Not the production pOS. `main` continues to serve current pOS in maintenance
  mode.
- Not a commitment to ship. This is decision-input for the full-build brief.

## Layout

```
memory-system/   # Phase 1 — memory prototypes (D1–D4)
  src/           # Python source for prototypes
  tests/         # Round-trip tests, evaluation harness
  scripts/       # One-shot scripts (ingest, eval, snapshot)
  data/          # Synthetic test set + episodes (no current-pOS content)
  docs/          # Bundled documentation per spec v1.1 R4
  launchd/       # Local-service hosting plists
```

## Implementation language

Python 3.11+. Rebuild-wide decision (see brief).
