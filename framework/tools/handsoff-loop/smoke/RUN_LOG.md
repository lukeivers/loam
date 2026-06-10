# Build-from-intent honest run log (S6 — AC.SMK.*)

Unfiltered log of general-path proof runs. Contract: every run is
logged whatever its result (fails included); every number carries its
run-of-origin (the entry it appears in names the ask verbatim, the
workspace, the loam commit, and the timestamp); any logged run is
reproducible from the documented command inside its entry.

All archetypes — the back-office trio AND every off-vertical probe —
flow through the IDENTICAL underlying command (it is printed in each
entry; the harness has no per-archetype branching). To run one more
case from a prompt no builder has seen:

```
python3.13 framework/tools/handsoff-loop/smoke/run_smoke.py \
    --archetype off-vertical --prompt-file <sealed-prompt-file>
```

---
