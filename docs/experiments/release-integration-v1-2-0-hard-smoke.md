# v1.2.0 HARD smoke writeup — the Work Management System MINOR

**Date:** 2026-06-04. **Release:** v1.2.0 — MINOR increment over published
v1.1.0 (`next_MINOR(v1.1.0) = v1.2.0`). Owner-greenlit publish: Luke — "Go".
**Reconcile:** the 7-increment WMS stack reconciled to `main` by FAST-FORWARD
(`c6afcd6d..9192d1d7`), bookkeeping commit on top.
**Release HEAD at smoke:** `de39c3f8` (the v1.2.0 pre-publish bookkeeping
commit on top of the reconciled WMS stack tip `9192d1d7`, seal `fde2b170`).
**Last published (Tier-0, git ref):** `v1.1.0` annotated tag → commit
`551ebada` (tag object `cb1993d9`).
**Window:** `v1.1.0..main` — the 30-commit linear WMS increment stack + the
release bookkeeping commit.
**`claude --version`:** `2.1.156 (Claude Code)`. **Subscription mode** — no
`ANTHROPIC_API_KEY`; no `anthropic` SDK (per `feedback_no_anthropic_api_key`).
**python:** 3.13.12 (host default `python3` is 3.9 — below the >=3.11 floor;
the cold install + every probe runs the 3.13 venv).

**Aggregate verdict: GREEN.** (One pre-existing, shipped-in-v1.0.1-AND-v1.1.0
test failure surfaced as a non-blocker finding — §6/§8.)

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

HARD bar: a REAL cold-clone + a REAL editable install with no API key + a REAL
spawn-isolated `claude -p` (per `feedback_spawned_claude_must_isolate_telegram_plugin`
— `--strict-mcp-config` + an empty `--mcp-config` file, `ANTHROPIC_API_KEY` +
`TELEGRAM_BOT_TOKEN` scrubbed) + an outcome-altitude exercise of the release's
user-visible deltas (`loam --version` → 1.2.0; a WMS lens at the production
entry point) + the touched/new-component test sweep.

## §2 — Cold clone

A fresh `git clone` of the loam tree into a temp dir + `checkout de39c3f8`.
Clone HEAD verified == `de39c3f8` (the release commit). No shared venv/state.

## §3 — Editable install from the manifest

`python3.13 -m venv .venv` + `pip install -r install-from-source.txt` in the
cold clone. Install exit 0. No new top-level component ships in v1.2.0 (the
WMS extends the already-listed `objective-tracker` + `primary-persona` +
`tools/loam`), so the manifest needs no v1.2.0 change.

## §4 — Outcome-altitude: `loam --version` (cold)

`loam --version` from the cold install → **`loam 1.2.0`**. GREEN — the
lockstep meta-package version delta proven at the production entry point with
no pre-arranged state.

## §5 — Outcome-altitude: a WMS lens at the production entry point (cold)

From the cold install, the WMS production surface imports clean
(`loam.objective_tracker.runtime`, `loam.primary_persona.keep_pace.analytics.render_analytics_block`,
`prioritize` / `plate` / `goals` / `relational`) and the on-demand analytics
render drives against a freshly-constructed real tracker store with no
pre-arranged state (honest-empty, no crash — the fail-soft contract). The
authoritative outcome-altitude exercises are the `WMS*.LIVE` tests in §6,
which drive the production entry points against REAL stores with REAL
transition histories and no mocks at the store/event-log boundary. GREEN.

## §6 — Touched + WMS suites (cold install)

| Suite | Result |
|---|---|
| `framework/objective-tracker/tests/` | all passed (176) |
| `framework/primary-persona/tests/` | all passed EXCEPT 1 pre-existing non-blocker (`test_AC_MSC_3`, see §8) |
| `framework/tools/loam/tests/` | 175 passed |

The `WMS*.LIVE` outcome-altitude tests (AC.WS.LIVE.1, AC.WMS2.LIVE.1,
AC.WMS4.LIVE.1, AC.WMS5.LIVE.1, AC.WMS6.LIVE.1, AC.WMS7.LIVE.1) are within the
primary-persona pass set — each exercises a WMS lens through the live
production entry point against a real store.

## §7 — Spawn-isolated `claude -p`

```
echo 'Reply with exactly the two words: SMOKE OK' | \
  env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN \
  claude -p --strict-mcp-config --mcp-config /tmp/empty-mcp.json
→ SMOKE OK   (exit 0)
```

A genuine model response, subscription-mode, with the telegram plugin NOT
loaded (`--strict-mcp-config` + an empty MCP config file) — the parent
Telegram bot slot is protected (per
`feedback_spawned_claude_must_isolate_telegram_plugin`). GREEN.

(Note: this claude version — 2.1.156 — parses `--mcp-config <file>` then
treats a trailing positional as another config path, so the prompt is passed
via stdin with bare `-p`; an inline-prompt form mis-parses the prompt as a
config filename. The stdin form is the correct spawn-isolated invocation here.)

## §8 — The one pre-existing finding (F2, NOT a blocker)

`test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface`
(`framework/primary-persona/tests/`) fails in the cold-clone harness — the
dev-mode session-start emitter returns empty when run from a bare cold clone
with no dev-workspace runtime markers (the gitignored
`workspace/personas/primary-persona/contract.yaml` is absent in a cold clone).

**Tier-0 proof it is pre-existing and NOT a v1.2.0 regression:**
- The test file is UNCHANGED by the WMS stack (`git diff c6afcd6d 9192d1d7` —
  no change to the test).
- Its source commit `91ebdee1` is an ancestor of BOTH the published `v1.0.1`
  tag (`deb85f6a`) AND the published `v1.1.0` tag (`551ebada`) — it shipped in
  the last TWO public releases.
- It fails IDENTICALLY in the cold-clone harness on those published tips. This
  is the SAME finding v1.1.0's own GREEN smoke documented (§6 there). It is
  tracked as task #52 (the `test_AC_MSC_3` FS-coupling test-isolation defect),
  scheduled for a separate isolation fix.

Established precedent (v1.0.1, v1.1.0): a pre-existing, shipped-already
cold-harness test-isolation failure that is named, Tier-0-proven pre-existing,
and not a regression does NOT block a minor's publish. Verdict GREEN holds.

## §9 — Reconcile health bonus (F2, in loam's favour)

The reconcile is strictly cleaner than the published base: the published
v1.1.0 tip `c6afcd6d` carries **15** hands-off-lifecycle test failures; the
reconciled tree carries **3** (the known-stale D.1 byte-content-match
hash-pin test — task #22, also Tier-0-proven red on `c6afcd6d`). The WMS
`session_start_emitter` rework FIXED the 12 AC37/SE_4 cold-clone failures. Net
test-health improvement, no new failures introduced by the reconcile.

## §10 — Verdict

**GREEN.** Cold clone + cold install + `loam --version` → 1.2.0 + the WMS
production-entry lenses + the touched/WMS suites + a real spawn-isolated
`claude -p` all pass, with one named pre-existing non-blocker (the same one
v1.0.1/v1.1.0 shipped with) and a net test-health improvement. Clear to run
the owner-greenlit public tag + push + GitHub Release.
