# Claude-leverage program Slice 4b — WIRE — apply ladder

Second buildable sub-cycle of Slice 4 under the thin-parent
`docs/plans/claude-leverage-program-s4-push.md`. Baselines on S4a's seal
(the pack must exist before the wiring points at it). Delivers the
bootstrap-wiring contract (D-PUSH.2) — the IN-FENCE buildable half of
distribution — and the persona surfacing (AC.CLP-PUSH.4).

This amendment (LOCAL — NO public surface):
  1. EXTENDS framework/workspace-bootstrap/: a bootstrapped workspace's
     .claude/settings.json gains an extraKnownMarketplaces stanza carrying
     autoUpdate:true (the §3.1.2 live-verified mechanism — third-party
     marketplaces default auto-update OFF, so the stanza is what delivers
     TRUE zero-user-action-after-the-bootstrap). Idempotent on re-run.
     (AC.CLP-PUSH-WIRE.1/.4)
  2. Adds the persona knowledge-surfacing rule: arrived leverage knowledge
     surfaced per the Lens 0 substance/vocabulary rule, not a raw changelog
     dump. Builder's call whether this is a primary-persona spine edit
     (the conditional component above) or a corpus-lean-hook route (no
     spine edit — remove that component at apply). (AC.CLP-PUSH.4,
     AC.CLP-PUSH-WIRE.3)
  3. ★ AC.CLP-PUSH-WIRE.2 (outcome-altitude = the AC.CLP-PUSH.3 LOCAL
     leg): a second fixture workspace, after one-time setup ONLY, receives
     a re-rendered S4a pack via a LOCAL-path marketplace with zero further
     user action. The real-publish leg is S4c ⛔OWNER.

The ★ AC is satisfied LOCALLY against a file://-path / local-clone
marketplace (plan §3.1.3 — local-path marketplaces are first-class add
targets); NO public surface is created or required by this cycle. The
`/reload-plugins` post-auto-update prompt is the platform's behavior, NOT
a loam step — named as the §10 F2.2 caveat, not owned.

NO Anthropic API key anywhere. BASELINE = S4a seal (confirmed at apply);
counter 187 next free; builder confirms both at apply time. If the
primary-persona conditional component is not needed, the builder removes
it at apply (no fence wider than the work).
