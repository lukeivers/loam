# Claude-leverage program Slice 4a — RENDER — apply ladder

First buildable sub-cycle of Slice 4 (KNOWLEDGE CORPUS, PUSHED) under the
thin-parent `docs/plans/claude-leverage-program-s4-push.md` and the master
`docs/plans/claude-leverage-program.md` (D-CLP.4 owner-RATIFIED Discord
1514753768175042771, 2026-06-11: distribution = plugin-marketplace
auto-update). The payoff leg — closest to loam's prime objective (master
§4): loam learns the *how* (best-current leverage knowledge) and renders it
for distribution so no user has to learn how to leverage AI themselves
(AC.PO.1).

This amendment (LOCAL — NO public surface):
  1. Lands framework/tools/knowledge-pack/ (NEW component, first-seal):
     deterministic projection FROM docs/capability-corpus/ into a
     marketplace-shaped skills-pack tree (.claude-plugin/marketplace.json
     + plugins/<name>/ with SKILL.md entries — the live-verified shape,
     plan §3.1.5). NO LLM authorship in the pack body — a hallucinated
     leverage claim cannot enter by construction (D-PUSH.1 protection
     floor). (AC.CLP-PUSH.1, AC.CLP-PUSH-RENDER.1/.2)
  2. Emits a curation-gate record; the pack is publish-eligible ONLY on a
     recorded gate pass. Builds + tests the ungated-publish-REFUSAL rig
     LOCALLY (AC.CLP-PUSH.5 adversarial leg). (AC.CLP-PUSH-RENDER.3)
  3. Stamps pack generated-ts + content-hash + per-entry source_fetch_ts /
     source_status passthrough — a stale corpus entry never renders as
     silently-current (D-PUSH.5; the AUTHORING stale rule propagated).
     (AC.CLP-PUSH-RENDER.5)
  4. Reuses Slice-1's sealed cadence binding as the render trigger — the
     pack-render is an added step in the same routine, NO second scheduler
     (D-PUSH.4, Lens 1). (AC.CLP-PUSH-RENDER.6)
  5. ★ AC.CLP-PUSH-RENDER.4 (outcome-altitude): a production-CLI render
     against the live corpus with no pre-arranged state produces a
     well-formed, validating marketplace tree.

The corpus is READ-ONLY input: NO docs/capability-corpus/ source edits; a
discrepancy found at render surfaces as a Slice-1 pending-delta (plan
§8.3), never a silent corpus edit. The public marketplace repo + first
publish are S4c ⛔OWNER (NOT this cycle). NO Anthropic API key anywhere
(any LLM-routed step — none needed for the deterministic render — would use
claude -p via the house client with spawn isolation).

BASELINE c77a2447 — HEAD at parent-authoring; counter 186 next free;
builder confirms both at apply time.
