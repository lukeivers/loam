# capability-refresh

Deterministic currency for the Class A capability corpus
(`docs/capability-corpus/`) — the root-cause fix for the
7-weeks-stale / factually-wrong reference-surface failure
(claude-leverage-program Slice 1; plan:
`docs/plans/claude-leverage-program-s1-currency.md`).

## What it does

```
sources.yaml (data)  ->  fetch canonical upstreams  ->  normalise
  ->  diff against per-source snapshots  ->  partition (D-CUR.4)
  ->  AUTO-LAND:  same-statement body re-projections, source_fetch_ts
                  stamps, stale-markings
  ->  REVIEW:     new claims, removals, [user-intent phrasings] overlay
                  touches, contradiction-suspects, curated divergences
                  -> docs/capability-corpus/pending-deltas/<date>-<id>.md
  ->  structured delta: docs/capability-corpus/.refresh/last-run.json
```

The body projection is **deterministic** — no LLM authors corpus
content, so a hallucinated claim cannot enter by construction. The
refresh **never** writes outside Class A (`claude-code/`) / Class
A-prime (`harness/`) + its own state dirs (`.refresh/`,
`pending-deltas/`); `best-practice/` (Class B) is structurally out of
reach (the locked no-cross-class-write invariant — AUTHORING.md).
A failed fetch marks the entry `source_status: stale (...)` — never
silently current.

## Run it

```
PYTHONPATH=framework/tools/capability-refresh/src \
    python3 -m capability_refresh --cadence-class high-velocity
```

(or `pip install -e framework/tools/capability-refresh/` and use the
`capability-refresh` console script.) Flags: `--sources` (workspace
override — sources are data), `--corpus-root`, `--cadence-class
{all,high-velocity,long-form,on-merge}`, `--dry-run`, `--json`.
Exit codes: 0 OK (fetch failures are handled outcomes — stale marks),
2 config error, 3 cross-class-write refusal.

## Unattended cadence

Locked classes (research doc §7bis.1, 2026-04-26): high-velocity ≈
daily, long-form ≈ weekly, on-merge for A-prime. The shipped binding is
in `cadence/`: cloud routine spec (primary, `routine-spec.md`) +
launchd plists (fallback) + `ACTIVATION.md` (one command per
mechanism). **Activation is owner-gated — nothing is live until the
owner says so.**

## Tests

`tests/test_AC_CLP_CUR_*.py` — one file per AC family
(AC.CLP-CUR.1/2 reference-surface, .3 refresh cycle at the production
CLI, .5 fetch-ts/stale, .6 D-CUR.4 partition, .7 no-cross-class-write)
+ `test_no_sealed_amendments.py` (AC.CLP-CUR.S seal fence).
