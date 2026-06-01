# foundation-polish cluster — SUB-ITEM 1a: conventional install / packaging readiness — apply ladder

Foundation-polish cluster per `docs/plans/foundation-polish-cluster.md`.
The 1.0-load-bearing install path: a non-technical user reaches a working
loam through a documented, normal command — NOT a dev-tree checkout.

SUB-ITEM 1a (this amendment — AUTONOMOUS, no public action):
  1. ONE documented install surface — a meta-package OR the README's
     already-named published-set (`pip install loam-cli loam-init …`) —
     composing the EXISTING per-component loam-* pyproject dependency
     graph into a single documented install command (AC.PYPKG.1). The
     meta-package shape is the builder's call (plan §10.3); the AC pins
     the OUTCOME (one command resolves the graph), not the method.
  2. The dependency graph LOCKS + BUILDS — every loam-* wheel builds from
     its pyproject; the inter-component bounds (already declared in each
     component's `dependencies` block per the install-from-source header)
     resolve into a consistent install set (AC.PYPKG.2).
  3. PROVEN against a LOCAL artefact index (a wheelhouse / --find-links
     dir) with ZERO push to any public registry (AC.PYPKG.3) — packaging
     readiness is decoupled from + precedes the owner-gated public flip.
  4. ★ outcome-altitude AC.INST.S: a genuinely CLEAN environment (a
     throwaway venv / fresh container, no source clone on PATH, no
     pre-arranged loam state) installs from the unified surface, then
     `loam init <tmpdir>` produces a WORKING freshly-initialized workspace
     (the REAL `loam init` entry-point → scaffolded `.loam/` + persona
     greeting), NO step requiring a framework-tree clone or edit. Drives
     the real install + the real `loam init`, not packaging metadata in
     isolation (feedback_test_outcome_altitude_required).

Composes on (Lens 1, NO re-implementation, NO new CI): pip/pipx; the
existing per-component pyproject graph + install-from-source.txt
constraints; the `loam.cli.subcommands` entry-point discovery loop
(loam --help must list the real subcommands post-install); the existing
`loam release` gate chain as the pre-flight for the later public flip.

SEPARABILITY VERDICT (plan F-FLATTEN / §10.1): the structure flatten is
SEPARABLE — NOT a prerequisite for this install path — and the roadmap's
named `framework/framework` doubling DOES NOT EXIST on disk (components sit
one level deep under framework/). Install ships on the CURRENT layout; the
flatten is DEFERRED pending an owner ruling and bundling it here is an
explicit scope error this plan prevents.

OWNER-GATED, NOT in this amendment: SUB-ITEM 1b (the public PyPI flip +
name claim — a public action, F-PUBLISH); the README source-only caveat
(lines 84-87) is superseded for the published surface only after the flip.

BASELINE cc512b1f — HEAD of main at plan-authoring; confirm at apply time.
Counter 161 is the next free slot; confirm at apply time. Two-component
fence head (loam-init + loam-cli); the builder admits the specific
per-component pyproject paths it locks via extra_allowed_prefixes at
EXAMINE once the meta-package home is chosen.
