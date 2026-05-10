# v0.7.3 HARD smoke — release-CLI post-publish auto-backfill

**Date:** 2026-05-10. **Version:** v0.7.3 (PATCH). **Verdict: GREEN** for AC.BACKFL.{1-6,S}; full release-CLI dry-run gates are partially RED at this writeup capture-time (clean-tree + acs-verified + seal-reachable + hard-smoke gates RED pre-seal — these clear at apply + seal time).

This writeup covers AC.BACKFL.6 — the outcome-altitude probe that runs the production CLI binary against the live state to verify the post-publish auto-backfill function correctly identifies the v0.7.3 row + would apply the expected edits.

## §1 — AC.BACKFL.6 outcome-altitude probe

### Probe 1 — function-altitude dry-run against live state

The full `loam release v0.7.3 --dry-run` invocation aborts on pre-publish gates RED (HARD smoke writeup not yet committed; §13 not yet backfilled; tree dirty; seal SHA not yet in roadmap row — all expected at this build-stage). To exercise the AC.BACKFL.6 probe at this stage, invoke the function directly with `dry_run=True` against the live `/Users/lukeivers/loam/` state. The probe is a structural verification that the parser correctly identifies every backfill target.

**Invocation:**

```bash
cd /Users/lukeivers/loam && python3.13 -c "
from pathlib import Path
import datetime
from loam_cli.release import post_publish_backfill
result = post_publish_backfill.apply_backfill(
    Path('/Users/lukeivers/loam'),
    'v0.7.3',
    'v0.7.3',
    'PROBESHA1234567890abcdef',  # placeholder; real tag SHA at publish
    today=datetime.date(2026, 5, 10),
    dry_run=True,
)
print(post_publish_backfill.format_backfill_preview(result))
"
```

**Output (verbatim, captured 2026-05-10):**

```
DRY-RUN: would apply post-publish backfill — 3 edit(s):
  - STATE.md: replaced 'v0.7.3 SHIPPED LOCAL — owner gates publish.' → '**v0.7.3 SHIPPED PUBLIC 2026-05-10 at tag `v0.7.3` (annotated `PROBESH`)**.'
  - roadmap §2 row: backfilled placeholders: TBD-AT-TAG + appended SHIPPED-PUBLIC marker
  - §3 Active Version: appended "**v0.7.3 PATCH (release-CLI post-publish auto-backfill PATCH (defect-closure for v0.6.0's release-process).) SHIPPED PUBLIC 2026-05-10** (tag `v0.7.3`, annotated `PROBESH`; seal `?`)."
  hint: roadmap §2 row for v0.7.3: seal SHA not extractable; §3 entry's seal-cite will read '?' (TBD-AT-SEAL backfill also skipped)
```

**Verdict:** GREEN. The function:

1. Located the canonical SHIPPED-LOCAL trailing claim in `docs/STATE.md` (`v0.7.3 SHIPPED LOCAL — owner gates publish.`) and proposed the correct SHIPPED-PUBLIC replacement (with the placeholder SHA truncated to 7 chars per spec).
2. Located the §2 row for v0.7.3 in `docs/release-roadmap.md` and proposed (a) backfill of `TBD-AT-TAG` placeholder, (b) append of the SHIPPED-PUBLIC marker.
3. Proposed a new §3 Active Version bold entry naming the correct CLASS (PATCH), the truncated objective sentence (first `.` outside backticks AND followed by whitespace — the bug-fix that prevented the truncation from tripping on `v0.6.0`'s decimal points), and the placeholder SHA + missing-seal sentinel.
4. Honestly surfaced the missing seal SHA in the hints field (the seal isn't yet present in the §2 row; it will be added at the apply step). The function did NOT crash, did NOT make up a SHA, did NOT silently substitute. The hint is the structural-correctness signal — a downstream operator sees the missing-seal note + knows to verify post-apply.

The summary-line update was correctly skipped at this probe-stage (the §2 table doesn't yet have a SHIPPED-PUBLIC marker for v0.7.3, so the published-version count is unchanged; the function correctly defers the summary update to a state where the row IS marked published).

### Probe 2 — full release-CLI dry-run (gates pre-status)

For completeness, the full `loam release v0.7.3 --dry-run` invocation captured at this build-stage:

```
== Pre-publish gates ==
  [RED] hard-smoke: missing HARD smoke writeup at docs/experiments/v0-7-3-hard-smoke.md; per `feedback_hard_smoke_per_minor_before_publish` every minor's last cycle runs HARD smoke against rd-automation BEFORE publish gate. Author the writeup + record the verdict; re-run `loam release v0.7.3` once GREEN.
  [RED] acs-verified: plan-doc docs/plans/v0-7-3-release-cli-auto-backfill.md §status does not mark these ACs GREEN: AC.BACKFL.1, AC.BACKFL.2, AC.BACKFL.3, AC.BACKFL.4, AC.BACKFL.5, AC.BACKFL.6, AC.BACKFL.S. Backfill §status (or §13) with the verdict matrix; each AC must appear with a GREEN marker. Re-run once backfilled.
  [GREEN] state-shipped: v0.7.3 marked SHIPPED in docs/STATE.md
  [RED] clean-tree: uncommitted changes in canonical tree:
  M docs/FUTURE_IDEAS_DRAFT.md
   M docs/STATE.md
   M docs/release-process.md
   M docs/release-roadmap.md
   M framework/tools/loam/src/loam_cli/release/runner.py
  ?? framework/tools/loam/src/loam_cli/release/post_publish_backfill.py
  ?? framework/tools/loam/tests/test_AC_BACKFL.py
Commit, stash, or revert; re-run.
  [GREEN] branch-main: on branch main
  [RED] seal-reachable: docs/release-roadmap.md §2 row for v0.7.3 carries no seal SHA. Append the seal anchor to the row (cycle SHA after `seal `) and re-run.

FAIL: 4 gate(s) RED; aborting. Address the corrective hints above + re-run.
```

The 4 RED gates are the expected pre-seal state:

- **hard-smoke RED** — this writeup itself; clears once committed.
- **acs-verified RED** — §13 §status not yet backfilled; clears at end-of-build §13 backfill commit.
- **clean-tree RED** — uncommitted source-edit batch; clears at apply commit.
- **seal-reachable RED** — seal SHA not yet in §2 row; backfilled at apply per existing v0.7.2-style precedent.

Once the build cycle seals (and the §13 backfill lands + STATE/roadmap §2-row seal SHA backfill lands), all four flip GREEN and the dispatcher's publish invocation hits the post-publish backfill step.

### Probe 3 — gate-7 system-binary-operational manual verification

Per the operator-verified gate 7 (system-binary-operational) at v0.7.1:

```
$ which loam
/opt/homebrew/bin/loam

$ loam --help | head -10
usage: loam [-h] [--version]
            {init,amend,release,odd-extract,onboard,pr-safety,project} ...

loam — unified top-level CLI. The framework's daily-driver shell-surface;
subcommand routing via argparse subparsers.

positional arguments:
  {init,amend,release,odd-extract,onboard,pr-safety,project}
    init                Bootstrap a fresh loam workspace from a canonical
                        source
```

All 7 documented subcommands present (`init / amend / release / odd-extract / onboard / pr-safety / project`); binary resolves; help exits 0. Gate 7 GREEN.

## §2 — Test surface verification

Full release-CLI test suite at v0.7.3:

```bash
$ cd /Users/lukeivers/loam/framework/tools/loam && \
  /opt/homebrew/opt/python@3.13/bin/python3.13 -m pytest tests/ --tb=short
```

**Result:** 60 passed in ~8 seconds.

Breakdown:
- 11 new `test_AC_BACKFL.py` tests (AC.BACKFL.{1-5} positive + idempotence + dry-run + runner integration)
- 49 prior tests (all v0.6.0 + v0.7.2 + OSS-M6 substrate) preserved without regression

## §3 — Aggregate verdict

**AC.BACKFL.HS aggregate verdict: GREEN.**

- AC.BACKFL.1 — auto-backfill function: GREEN per Probe 1 (3 edits proposed + 1 honest hint surfaced).
- AC.BACKFL.2 — aggregate-count summary: GREEN per fixture-altitude test `test_apply_backfill_updates_aggregate_count_summary` (Probe 1 correctly skipped this update for v0.7.3 because v0.7.3's row isn't yet marked PUBLIC; post-edit the count would update).
- AC.BACKFL.3 — §3 Active Version entry: GREEN per Probe 1 (entry proposed + objective sentence correctly truncated).
- AC.BACKFL.4 — idempotence: GREEN per `test_apply_backfill_is_noop_on_re_run` + `test_runner_idempotent_re_run_skips_backfill_commit`.
- AC.BACKFL.5 — test fixture: GREEN per 11/11 new tests passing.
- AC.BACKFL.6 — outcome-altitude probe: GREEN per Probe 1 (this writeup's §1 captures the dry-run preview against live state).

The full `loam release v0.7.3 --dry-run` end-to-end probe will GREEN at the dispatcher publish-time once the build cycle seals + STATE/roadmap §2 SHA backfill lands. The function-altitude probe in §1 verifies the post-publish backfill logic is structurally correct against live state today.

**No regressions**, **no F2 RUTHLESS FEEDBACK findings**, **no HARD HALTs hit**.
