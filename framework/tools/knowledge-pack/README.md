# knowledge-pack — the weekly knowledge pack is a RENDERING from the corpus

Claude-leverage program **Slice 4a (RENDER)**. This component
deterministically projects `docs/capability-corpus/` into a
marketplace-shaped skills-pack tree IN-REPO, behind a curation gate, with
**no LLM authorship in the pack body** — a hallucinated leverage claim
cannot enter by construction (D-PUSH.1 protection floor; the same shape as
Slice-1's `capability-refresh`). The pack is a **rendering** of the
corpus, never a fork (master §2).

**LOCAL — no public action.** This component stages the pack in-repo. The
public marketplace repo, the first publish, and the real-arrival
observation are **S4c (⛔OWNER)** — they are NOT in this component.

## What it does

```
knowledge-pack render
```

1. Reads the corpus (Class A `claude-code/` + Class A-prime `harness/` +
   Class B `best-practice/`) **read-only** — it never writes corpus
   source (a corpus discrepancy surfaces as a Slice-1 pending-delta, never
   a silent edit; plan §8.3).
2. Projects each entry into `SKILL.md` form under the live-verified
   marketplace shape:
   ```
   <pack-root>/
     .claude-plugin/marketplace.json
     plugins/<plugin>/.claude-plugin/plugin.json
     plugins/<plugin>/skills/<skill>/SKILL.md
     pack-manifest.json
     gate-record.json
   ```
   One plugin per corpus class; a skills-only pack is valid (plan §3.1.5).
3. Carries every pack claim's corpus citation: each skill gets a
   **Provenance** footer naming the corpus path it was projected from,
   the upstream `source_url`, the entry status, and the entry's
   `[primitive: <class>:<name>]` cross-references (RENDER.2).
4. Stamps a `pack-manifest.json` with a `generated_ts` + a deterministic
   `content_hash` (over the projected skill bodies) + a derived
   `version` (`<date>+<hash12>`, never pre-assigned — D-PUSH.5) +
   per-entry `source_fetch_ts` / `source_status` passthrough, so a stale
   corpus entry is never rendered as silently current (RENDER.5).
5. Emits a **curation-gate record** (`gate-record.json`). A freshly
   rendered pack is `pending` — NOT publish-eligible until a curator
   records a `pass` bound to the pack's content-hash (RENDER.3).

## The publish-path gate (AC.CLP-PUSH.5)

```
knowledge-pack assert-publish-eligible --pack-root <dir>
```

Exits non-zero (refusal) when the pack has no gate record, a `pending` or
`fail` verdict, or a content-hash mismatch (the pack changed after the
gate pass). **Nothing publishes without a recorded gate pass** — the
egress-consent floor's local test surface. The S4c ⛔OWNER publish runbook
calls this before any push.

## Cadence — reuse, no second scheduler (D-PUSH.4)

The render is an added STEP in Slice-1's existing cadence binding, not a
new scheduler. See `cadence/INTEGRATION.md` and
`scripts/run-cadence-step.sh`. This component owns no cron, no launchd
agent, no `/schedule` routine of its own.

## Tests

Run against the project venv (never bare `python`):

```
.venv/bin/python -m pytest framework/tools/knowledge-pack/tests/ -q
```
