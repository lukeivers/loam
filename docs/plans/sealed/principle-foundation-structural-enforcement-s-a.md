# principle-foundation-structural-enforcement — Slice A — DECLARATION SUBSTRATE — apply ladder

First of four ordered slices under the candidate plan
`docs/plans/principle-foundation-structural-enforcement.md` (roadmap §4
Candidate 1, MINOR/META). Delivers the declaration substrate: loam's
design principles stop being advisory prose and become a machine-read
named-primitive registry plus a mechanical integrity check.

This amendment:
  1. Ships docs/design/principle-manifest.yaml (NEW, universal-paths) —
     the code-side declaration surface a checker enumerates the
     frame-rules (FR.1/FR.2/FR.3) + M5 from. Each row carries an
     `enforcement` field (enforced|advisory|partial). M5 is declared
     `advisory` per the load-bearing D-PFSE.1 partition: the four-step
     conflict process is interior cognition with no observable artefact,
     and an LLM-per-action judge collides with the hook-latency budget —
     behavioural enforcement is explicitly OUT (HALT-SURFACED, plan
     §3.1/§10 RF-1). (AC.PFSE.1, AC.PFSE.2-manifest-leg)
  2. Ships the typed reader (principle_manifest_reader.py) + the
     PreToolUse manifest-checker (principle_manifest_guard.py, a
     WARN-tier sibling of primitive_check_guard reusing the
     _gate_helpers NDJSON-audit + dev-mode short-circuit + fail-open
     envelope, D-PFSE.4) + a bidirectional manifest<->derivation-map
     coverage guard scoped to the declared-principle surface
     (frame_rules + principles; enforced-primitives provenance is
     excluded — it may name a newer feedback memory not yet in the map's
     table). A manifest row naming a corpus file the map omits, OR a
     structurally invalid manifest, turns the dev-sdlc suite red — the
     observable-drift contract (D-PFSE.2 / RF-4). (AC.PFSE.1)
  3. Ships framework/docs/principles/odd-principles.md (NEW) — FR.1 REAL
     authoring (framework/docs/principles/ did not exist on disk, the
     verified plan correction). Anthropic-publish-grade principles tier;
     cross-references the manifest. (AC.PFSE.1)
  4. FR.2/FR.3 docs (the one sealed fence, plugins/dev-sdlc/docs/) gain a
     one-line manifest cross-reference; the derivation-map gains a
     one-line pointer to the manifest. The full publish-grade re-author
     of FR.2/FR.3 is tracked separately under foundation-revision-rebuild
     — AC.PFSE.1 requires the prose docs EXIST + cross-reference the
     manifest, NOT a re-author. The CLAUDE.md Lens consolidation
     (foundation-revision-rebuild §3.5) is already present in this tree
     (Lens 0-7), so that sub-deliverable is a no-op here (surfaced).

Out with named handoffs: the FR.2/FR.3 publish-grade re-author
(foundation-revision-rebuild owns it); the research-question gate +
context-load gate (Slice B); the Stop-hook contributor framework + the
permission-ask/terminology-drift contributors + the AC.PFSE.2★
outcome-altitude fire (Slice C); slug-collision + the meta-decision-haiku
arbiter SKILL (Slice D).

NO public-action steps; NO Anthropic API key anywhere (every check is
deterministic YAML/regex/git-read). BASELINE e4c4734f — HEAD at Slice A
source-edit start; counter 188 next free; builder confirms both at apply
time. LOCAL only.
