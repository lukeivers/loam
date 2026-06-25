# Release integration — deliberate-reasoning + memory-supersession (next minor over v1.6.0)

**Status:** RATIFIED FOR PREP+SMOKE — owner (Luke) cleared single **v1.7.0 MINOR** 2026-06-25 (Discord msg 1519492799681134714: "Ratify"). The prep + HARD-smoke cycle is authorized off this commit. **PUBLISH (tag + push + `loam release`) REMAINS a gated public action requiring a SEPARATE explicit owner word AFTER the smoke is GREEN** (`feedback_no_public_action_during_build`).
**Working tree:** `/Users/lukeivers/loam` (branch `main`; the unpublished
work is already a clean linear fast-forward stack on the published v1.6.0
baseline — no isolated release worktree needed).
**Version (derived NOW at release-planning time):** **v1.7.0** — MINOR
increment derived from the published `v1.6.0` per
`docs/release-versioning-policy.md` §"Number derivation at build-commence
time" (`next_MINOR(v1.6.0) = v1.7.0`). New outcome-shape capability,
zero BREAKING → MINOR, not MAJOR. **ONE consolidated MINOR** recommended
over a 2-or-3-way split — see §3 named decisions.
**Last published (Tier-0, git ref):** `v1.6.0` annotated tag (`d94312f`) →
commit `4aafc29f`; `origin/main` at `fd6d34b2` (the three v1.6.0
post-publish release/backfill commits sit between the tag and
`origin/main` and are already public).
**Release window (Tier-0):** `origin/main..main` = `fd6d34b2..7a6a1671`,
**43 commits**, oldest `c0c584f4` (slice-1 ratified plan), newest
`7a6a1671` (memory-supersession seal). `git rev-list --left-right --count
origin/main...main` = `0 43` — `main` is a clean linear fast-forward, zero
commits behind, zero merge commits, no squash, no amend. The feat / apply /
seal commits are the audit trail.

---

## §1 — What v1.7.0 ships

v1.7.0 is a single MINOR shaped around one objective sentence:

> **loam can deliberately reason — a metacognitive gate decides per-turn
> when a task warrants escalated reasoning and runs an evidence-bound
> re-entrant loop, triggered by the situation rather than conversation
> keywords and wired live (default-OFF) — and loam's memory keeps the
> current truth current: a superseded ruling is filtered out of recall by
> validity interval while its history stays queryable.**

Two new outcome families ladder up to that sentence, plus the Tilth-side
hands-off-loop slices and release-internal housekeeping.

### A. deliberate-reasoning — NEW top-level component (the headline)

`framework/deliberate-reasoning/` does not exist at the v1.6.0 tag
(Tier-0: `git ls-tree v1.6.0 framework/` has no `deliberate-reasoning`
entry); it is introduced whole inside this window. Two sequenced slices:

1. **Slice 1 — metacognitive gate + evidence-bound re-entrant loop**
   (feat `01acd52d`, apply `d8b71827`, sealed at `a6156590` —
   `metacognitive-gate-reentrant-loop-slice1`). A deterministic, LLM-free
   per-turn escalate decision (`gate.py`), an adversarial evidence-bound
   re-entrant loop (`loop.py`), a `process_turn` production entry-point
   under a default-OFF gate (`turn.py`), and a frozen pre-registered
   experiment (`experiment/PRE_REGISTRATION.md` + `task_set.json` + blind
   `judge.py` + `runner.py`). ACs AC.MGRL.{1-5} + AC.MGRL.OA
   (outcome-altitude). **Predecessor of Slice 3 — must order first.**

2. **Slice 3 — situation/behavior triggers + live PreToolUse wiring**
   (feat `e68cd687`, apply `565d7ae4`, sealed at `4fcbdec4` —
   `deliberate-reasoning-situation-triggers-and-live-wiring`). Replaces
   the conversation-keyword gate substrate with situation/behavior
   triggers (`signals.py`, `escalation.py`), adds live PreToolUse wiring
   (`wiring.py`), and ships a NOVELTY self-assessment behind its own
   independent switch. **Default-OFF, zero-collateral** (Tier-0 from the
   feat body: "default-OFF pure no-op; zero-collateral (gate fires on
   ZERO …)"; keyword triggers retained behind an opt-in deprecation path).
   ACs AC.TRIG.{1-4} + AC.WIRE.1, with AC.MGRL.OA carried forward.

   (There is no "slice 2" in this window. Slice 2a was a self-model plan
   ratified at `89b12806` but did NOT seal into this release window — it
   is out of scope, §6.)

The component ships at its own `0.1.0` (new-component convention, mirrors
how v1.6.0 shipped `capability-refresh`/`knowledge-pack` at 0.1.0 out of
the lockstep set). **Not in the install graph / not lockstep-bumped this
cut** — see AC.REL.2 and §3 D-LOCK.

### B. memory-supersession + salience-eval — extends sealed primary-persona

(feat `e0eff95e` + pre-registration anchor `90f42515`, apply `8ced8737`,
register backfill `b7dfa02c`, sealed at `7a6a1671` —
`memory-supersession-and-salience-eval`; fence `primary-persona`.)

- **SUP (committed core, proven):** validity-interval supersession —
  recall FILTERS superseded records out (current-over-stale, AC.SUP.1)
  instead of merely demoting them; an explicit `as_of` query returns
  history (AC.SUP.2); the prior record's interval closes at the new
  record's creation (AC.SUP.3); reversible via un-mark (AC.SUP.5).
  Composes on the predecessor seals rather than a new schema.
- **E2E answer-correctness gate (proven):** `framework/primary-persona/
  eval/harness.py` + AC.E2E.{1,2,3} — answer-level correctness-up,
  blind-judge, frozen QA probe.
- **RCT salience probe — dropped as NULL (honestly recorded):** the
  RCT-tie-break probe (AC.RCT.{1,2,3}) was pre-registered as a
  drop-if-null falsification probe; it came back null and was dropped,
  with the null recorded in the register (`b7dfa02c`, "D-RCT.1 null
  recorded"). This is an honest negative result, not a shipped capability.

### C. Tilth-side hands-off-loop slices — workspace-bootstrap fence

Three slices land in `framework/tools/handsoff-loop/` (the measurement-
class tool at deliberate `0.0.0`, lockstep-EXCLUDED by policy), sealed
under the `workspace-bootstrap` component fence:

- **Slice DF — design-first front stage** (feat `e5ff74b4`, sealed at
  `014dd9ad`): N candidate designs + a user-validation gate before build.
- **Slice HB — build-time progress heartbeat** (feat `cf34067d`, folded
  into the same seal anchor `1a094701`/`014dd9ad` window): channel-aware
  progress heartbeat via an injected `notify_fn`.
- **Slice DF6 — non-tech-user visible candidates** (feat `3050e0e5`,
  apply `6ba1a60f`, sealed at `f4b7e079`): frame candidate designs for the
  user's tech level — default non-tech, never offer CLI/daemon to a
  non-tech user (AC.DF.6). Directly serves Lens 0 (per-user translation).

This is the "between the work you've been doing and what Tilth has been
doing" half — the loam-core capability (A + B) and the workspace-bootstrap
hands-off work (C) ship together under one MINOR narrative.

### D. Release-internal housekeeping (no runtime capability)

- **dev-sdlc pbret-register** (feat `161816a4`, apply `fea022da`, sealed
  at `dfda5bbf`): registers two v1.6.0 retirement-record docs as
  ProgramBench-sweep keeps (D-K9/D-K11 class) + a retirement-sweep test.
  This is bookkeeping for an ALREADY-SHIPPED v1.6.0 retirement — it closes
  a test-registry gap, ships zero new user-visible behavior.
- **dev-sdlc seal-fence BASELINE correctives** (`708a66ec`, `052e23ff`,
  `80cd7705`, `1fdc2e02`) — advance interleaved-corrective baselines so
  the slice-1 seal fence is clean. Mechanical, audit-only.
- **§14 register backfills** (`7c0f2bbb`, `e978b35a`, `5c443c12`,
  `0e1a8bd4`, `3a696938`, `65c1f27d`, `66539a3b`, `46ad8e0c`) — per-
  decision SHA backfills into method-decision registers. Doc-only.

Housekeeping rides the MINOR; it does not warrant a separate PATCH because
there is no published-outcome defect being closed — it is in-window
bookkeeping for work that ships in THIS minor (or already shipped in
v1.6.0). Per `release-versioning-policy.md` §"What goes in a patch", a
PATCH closes defects in the CURRENT minor's named outcome; none of this is
a defect in v1.6.0's outcome.

### Minor-class tag (per policy §"Quality gate")

**MIXED** — END-USER for the deliberate-reasoning + memory halves (named
user-visible deltas below), with the named foundational portion being the
default-OFF substrate (the capability is built and proven but ships
gated). The user-visible deltas:

- A user can run the deliberate-reasoning `process_turn` entry-point and
  get an escalate-or-not decision + an evidence-bound re-entrant loop,
  triggered by situation rather than keywords (opt-in via the gate's
  enable switch).
- A user's superseded ruling no longer surfaces as current recall, while
  its history remains queryable `as_of` a past time — the "memory keeps
  the current truth current" delta.

No new install-graph component ships; deliberate-reasoning rides at 0.1.0
out-of-graph (§3 D-LOCK), so **per MINOR discipline the lockstep version
bump advances `docs/ACTIVE_MINOR` 1.6.0 → 1.7.0 + the in-scope pyprojects
+ the meta-package `loam --version` literal** in one source-of-truth
commit at release prep — see AC.REL.2.

---

## §2 — Reconcile + gate framing

Tier-0 verification before prep: `git merge-base origin/main main` ==
`origin/main` (`fd6d34b2`) — `main` is a clean linear fast-forward, zero
merge commits in the window (`--left-right --count` = `0 43`). A secret
scan over the full `origin/main..main` diff must run at prep and return
zero token/key/private-key matches before any push (mirrors the v1.4.0
prep gate); no `.env` / secret-bearing filenames in the window.

`loam release v1.7.0 --plan-doc docs/plans/release-integration-deliberate-reasoning-and-memory-supersession.md`
runs all seven pre-publish gates from the repo (`docs/release-process.md`
§1). The irreversible public tag + push + GitHub Release is the
owner-authorized step, run ONLY after a verified-GREEN HARD smoke — no
`--no-verify`, no force, no hand-edit to green a gate. Build agents do NOT
invoke `git tag` / `git push` / `loam release`
(`feedback_no_public_action_during_build`).

---

## §3 — Named decisions for the owner (recommendation on each)

**D-SPLIT — How many releases: ONE consolidated MINOR vs a split.**
*Recommendation: ONE consolidated v1.7.0 MINOR.* The window is entirely
additive — Tier-0: `git log --format=%s v1.6.0..HEAD | grep -iE
'breaking|!:'` is empty; the deliberate-reasoning component ships
default-OFF / zero-collateral; the memory change is filter-on-recall with
reversible un-mark and history preserved `as_of`. Nothing here breaks a
prior outcome, so nothing forces a split. Both capability families fit one
clean changelog narrative ("loam can deliberately reason, and its memory
keeps the current truth current"). Splitting into v1.7.0
(deliberate-reasoning) + v1.8.0 (memory) would buy two headlines at the
cost of two HARD smokes, two release runs, and two owner gates for work
that is one coherent reasoning-and-memory advance. F2: the only argument
FOR a split is marketing — if the deliberate-reasoning component is wanted
as a standalone headline release for external visibility, that is a real
reason, but it is an owner marketing call, not a release-discipline
requirement. Absent that, consolidate.

**D-VER — Version number + semver type.** *Recommendation: v1.7.0,
MINOR.* Derived NOW from published `v1.6.0` per the policy's
build-commence recipe (`next_MINOR(v1.6.0) = v1.7.0`). New outcome-shape
capability = MINOR; zero BREAKING rules out MAJOR; not a defect-closure so
not a PATCH. This is the sanctioned moment to assign the number
(`feedback_version_numbers_at_release_time` forbids PRE-allocating in
roadmaps, not assigning at release planning).

**D-MAJOR — Any breaking change forcing a MAJOR?** *Recommendation: no —
stay MINOR.* Tier-0 breaking-marker scan empty; deliberate-reasoning is a
new component (pure addition, default-OFF); memory-supersession composes
on existing seals with reversible un-mark and preserved history. No public
surface is removed or changed incompatibly. Post-1.0 majors are emergent
(policy §"Post-1.0 majors"); nothing in this window trips the
accumulated-breaking / mental-model-shift / plugin-contract-revision
triggers.

**D-LOCK — deliberate-reasoning version + lockstep treatment.**
*Recommendation: ship `deliberate-reasoning` at `0.1.0`, OUT of the
lockstep set this cut* (mirrors the v1.6.0 treatment of
`capability-refresh`/`knowledge-pack` at 0.1.0). It is a new component not
yet in the install graph; folding it into lockstep at 1.7.0 is premature
before it is wired into the install manifest. The MINOR lockstep bump
still advances `docs/ACTIVE_MINOR` 1.6.0 → 1.7.0 + the existing in-scope
pyprojects + the meta `loam --version` (because primary-persona, a
lockstep member, gained the memory capability). Re-evaluate folding
deliberate-reasoning into lockstep when it enters the install graph (a
named follow-on).

**D-CADENCE — Release now vs hold.** *Recommendation: release now (after
owner ratification + GREEN smoke).* Both capability families are sealed,
reachable, and stable; holding accrues no benefit and lets the unpublished
window keep growing (43 commits already). Build-forward discipline
(`feedback_build_forward_on_publish_pending`) keeps the next cycle moving
once this is sealed-local.

**D-HOUSEKEEP — Housekeeping: separate PATCH or ride the MINOR?**
*Recommendation: ride the MINOR.* The dev-sdlc pbret-register + baseline
correctives + register backfills close no published-outcome defect — they
are in-window bookkeeping. Per policy, a PATCH closes defects in the
current minor's named outcome; there is none, so a separate PATCH would be
a number with nothing to name.

---

## §4 — Acceptance criteria

### AC.REL.1 — Plan-doc authored
This doc exists with §1 inventory + §4 ACs + §13 §status gate matrix at a
scope-descriptive slug
(`release-integration-deliberate-reasoning-and-memory-supersession`),
reachable via `--plan-doc`.

### AC.REL.2 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` advances 1.6.0 → 1.7.0; the in-scope `pyproject.toml`
version fields bump 1.6.0 → 1.7.0; the per-component lockstep regression
test (`plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`)
stays GREEN with the bump. The meta-package `--version` literal folds in
(`loam --version` → `1.7.0`). `deliberate-reasoning` (0.1.0) and the
measurement-class `handsoff-loop` (0.0.0) are EXCLUDED from the in-scope
set per D-LOCK + policy §"Per-component pyproject version anchor".

### AC.REL.3 — HARD smoke GREEN (the per-minor gate)
`docs/experiments/release-integration-deliberate-reasoning-and-memory-supersession-hard-smoke.md`
authored; REAL cold-clone of the release HEAD + REAL editable install +
spawn-isolated `claude -p` (subscription-only, scrubbed
`ANTHROPIC_API_KEY`/`TELEGRAM_BOT_TOKEN`, `--strict-mcp-config`) + the two
outcome-altitude deltas reproduced from the cold install (see AC.REL.S) +
the touched-component regression ride-alongs; the writeup carries the
`GREEN` aggregate-verdict token and the gate-7 `which loam` + `loam --help`
evidence. (`feedback_hard_smoke_per_minor_before_publish`.)

### AC.REL.4 — Touched component suites GREEN (cold install)
From the cold install, all pass: `framework/deliberate-reasoning/tests/`
(slice-1 + slice-3 ACs incl. `test_AC_MGRL_OA_outcome_altitude_real_entrypoint`),
`framework/primary-persona/tests/` (SUP + E2E ACs),
`framework/tools/handsoff-loop/tests/` (DF / HB / DF6 incl. AC.DF.6),
`framework/workspace-bootstrap/tests/`, and
`plugins/dev-sdlc/tests/` (incl. the pbret retirement-sweep test). Any
failure is Tier-0-verified pre-existing on the published v1.6.0 tip
(`fd6d34b2`) — not a v1.7.0 regression — and documented in the smoke
writeup with the same-known-set discipline used at v1.5.0/v1.6.0.

### AC.REL.5 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` change-log carries a `**v1.7.0 ... SHIPPED LOCAL**` entry
naming the deliberate-reasoning component + the memory-supersession
amendment + the Tilth hands-off slices + the release-window tip. (The
`SHIPPED PUBLIC` flip is the post-publish backfill, done by the release
tool.)

### AC.REL.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a `| v1.7.0 |` row whose final seal
token (`7a6a1671` — the memory-supersession seal, the release-window
content tip) is reachable from HEAD; §3 Active-version updated.

### AC.REL.7 — migration declared
`docs/state-migrations/v1-7-0-deliberate-reasoning-and-memory-supersession.migration.yaml`
declares `version: v1.7.0` + `operation: no-op` (deliberate-reasoning
persists no user-state at default-OFF; supersession marks are created
lazily / derived at read time — no existing user `.loam/` state changes).

### AC.REL.S — Outcome-altitude (cold-install user-visible deltas)
The HARD smoke exercises the v1.7.0 user-visible deltas from a cold clone
with no pre-arranged state: (1) `loam --version` reports `loam 1.7.0`;
(2) the deliberate-reasoning `process_turn` production entry-point returns
an escalate-decision + evidence-bound loop result when enabled; (3) the
memory-supersession path filters a superseded record out of current recall
while an `as_of` query returns its history — all through production entry
points, no pre-arranged state. GREEN.

---

## §5 — Publish gates (what each release's HARD smoke must cover)

Single release (v1.7.0). The HARD smoke (AC.REL.3 / `feedback_hard_smoke_
per_minor_before_publish`) is the load-bearing pre-publish gate. It must
cover, AFTER local seal and BEFORE any tag/push:

1. **Cold install** — real `git clone` of the release HEAD into a fresh
   tmp dir + real editable install from the install manifest alone (catch
   any new-component install-graph gap, especially that
   `deliberate-reasoning` either installs cleanly or is correctly excluded
   from the graph).
2. **Real `claude -p`** — spawn-isolated (`--strict-mcp-config`, scrubbed
   `ANTHROPIC_API_KEY`/`TELEGRAM_BOT_TOKEN`) per `feedback_spawned_claude_
   must_isolate_telegram_plugin`; subscription-only per `feedback_no_
   anthropic_api_key`.
3. **Real fixtures — the two new capabilities at outcome altitude:**
   (a) deliberate-reasoning `process_turn` from the cold install returns
   an escalate decision + re-entrant loop result; (b) memory-supersession
   filters a superseded record out of current recall and returns history
   `as_of` — both from the cold install, no pre-arranged state.
4. **Regression ride-alongs** — the touched suites from AC.REL.4 swept
   from the cold install; every failure Tier-0-classified pre-existing on
   `fd6d34b2` or fixed, never waved through.
5. **Gate 7 evidence** — `which loam` resolves + `loam --help` exits 0 and
   lists every documented subcommand (operator-verified, recorded in the
   writeup).

All seven `loam release` gates (`docs/release-process.md` §1) run via
`loam release v1.7.0 --dry-run` and report GREEN before the owner-
authorized publish. The publish itself is owner-gated (ASK-FIRST).

---

## §6 — Out of scope

- **Self-model slice-2a** (`89b12806` ratified plan; `bad861e0` memory
  plan) — ratified but did NOT seal a runtime amendment into this window.
  Deferred to a future cycle.
- **deliberate-reasoning into the install graph + lockstep** — named
  follow-on once the component is wired into the install manifest
  (D-LOCK). Until then it ships at 0.1.0 out-of-graph.
- **RCT salience tie-break** — dropped as a null falsification probe
  (recorded `b7dfa02c`); not revived in this release.
- **Keyword-trigger substrate** — retained behind an opt-in deprecation
  path in slice-3; full removal is a future deprecation-cycle item.
- The v1.0 quality-bar event and any major-eval — not triggered by this
  window (no accumulated-breaking / mental-model-shift / plugin-contract
  trigger).

---

## §7 — Halt triggers (abort prep + surface to owner)

- **Local-but-unpushed version ambiguity** — if a tag `v1.7.0` already
  exists locally or on `origin` at prep time, HALT per policy §"What
  `current_version` means precisely".
- **`origin/main` moved** — if a re-fetch shows `main` no longer a clean
  fast-forward of `origin/main` (count not `0 N`), HALT and reconcile-first
  (`feedback_sync_check_before_build_on_checkout`).
- **Secret-scan hit** — any token/key/private-key match in the
  `origin/main..main` diff HALTS the publish.
- **HARD smoke RED** — any non-pre-existing failure in the smoke RED-gates
  the publish; fix at the source, never hand-green the gate.
- **Build collision** — an `index.lock` or in-progress `loam amend` in the
  tree means another session is building; HALT
  (`feedback_serialize_amendment_builds`).

---

## §8 — Bookkeeping (at prep close)

- `docs/STATE.md` — `**v1.7.0 ... SHIPPED LOCAL**` entry (AC.REL.5);
  post-publish flip to SHIPPED PUBLIC is the release tool's job.
- `docs/release-roadmap.md` §2 `| v1.7.0 |` row + §3 Active-version
  (AC.REL.6).
- `docs/ACTIVE_MINOR` 1.6.0 → 1.7.0 + in-scope pyproject lockstep bump +
  meta `--version` (AC.REL.2).
- `docs/state-migrations/v1-7-0-...migration.yaml` no-op (AC.REL.7).
- Owner ratification recorded durably in this doc's status line + a
  decision record BEFORE the build/prep dispatch
  (`feedback_record_owner_ratification_before_dispatch`).

---

## §9 — F2 Ruthless Feedback (honest doubts + named risks)

1. **The "slice 2" gap is real and worth naming.** This window has slice-1
   and slice-3 of deliberate-reasoning but no slice-2 runtime seal — slice-2a
   is a ratified PLAN (`89b12806`) that never sealed. The changelog must NOT
   imply a complete slice sequence shipped; it ships slice-1 + slice-3, and
   the self-model work is explicitly deferred (§6). Stating "slices 1 and 3"
   plainly avoids an over-claim.

2. **deliberate-reasoning ships default-OFF — the user-visible delta is
   gated.** The honest END-USER value is "the capability exists and is
   proven, opt-in"; it is not "on by default for every user." The MIXED
   class tag (§1) names this. Do not market it as an always-on behavior
   change — that would fail the END-USER value-delta gate's honesty bar
   (`release-versioning-policy.md` §"Quality gate").

3. **The RCT null is a strength, not a thing to hide.** A pre-registered
   probe that came back null and was dropped (recorded `b7dfa02c`) is
   exactly the falsification discipline working. The changelog should not
   list RCT as a feature; the smoke/plan records it as a recorded null.

4. **0.1.0-out-of-graph is the right call but accrues a debt.** Shipping a
   new component outside the install graph + lockstep (D-LOCK) repeats the
   v1.6.0 pattern (`capability-refresh`/`knowledge-pack` at 0.1.0). That is
   defensible per precedent, but the install-graph wiring is now a standing
   follow-on for TWO consecutive minors' worth of new components — worth a
   FUTURE_IDEAS capture so it does not become permanent drift.

5. **Consolidation is the F2-clean call.** With zero breaking changes and
   one coherent narrative, splitting into multiple releases would be
   over-engineering the cadence for work that is one additive advance. The
   only legitimate reason to split is an owner marketing preference for a
   standalone deliberate-reasoning headline — surfaced in D-SPLIT, owner's
   call, not a discipline requirement.

---

## §10 — Provenance trail (Tier-0 git refs)

- **Published baseline:** `v1.6.0` tag → commit `4aafc29f` (annotated
  `d94312f`); `origin/main` `fd6d34b2` (post-publish backfill, public).
- **Release window:** `origin/main..main` = `fd6d34b2..7a6a1671`, 43
  commits, `--left-right --count` `0 43` (clean fast-forward).
- **deliberate-reasoning slice-1 seal:** `a6156590`
  (feat `01acd52d`, apply `d8b71827`). Component absent at `v1.6.0`
  (Tier-0 `git ls-tree v1.6.0 framework/`) → NEW component.
- **deliberate-reasoning slice-3 seal:** `4fcbdec4`
  (feat `e68cd687`, apply `565d7ae4`). Predecessor: slice-1.
- **memory-supersession seal:** `7a6a1671` (feat `e0eff95e`, pre-reg
  `90f42515`, apply `8ced8737`, register backfill `b7dfa02c`); fence
  `primary-persona`.
- **Tilth hands-off slices:** DF `e5ff74b4`→seal `014dd9ad`; HB `cf34067d`
  →seal `1a094701`/`014dd9ad`; DF6 `3050e0e5`→seal `f4b7e079`; fence
  `workspace-bootstrap` (existing at v1.6.0); lands in `framework/tools/
  handsoff-loop/` (0.0.0, lockstep-excluded).
- **dev-sdlc pbret-register:** seal `dfda5bbf` (feat `161816a4`); fence
  `plugins/dev-sdlc`. Housekeeping.
- **Sources:** `docs/release-process.md`, `docs/release-versioning-policy.md`,
  `docs/release-roadmap.md` §2 (v1.6.0 row), format template
  `docs/plans/release-integration-v1-4-0.md`.

---

## §13 — §status (gate verdict matrix — PENDING build/prep)

All PENDING until owner ratifies + the prep cycle runs the smoke + bumps.

| AC | Verdict | Evidence (to be filled at prep close) |
|---|---|---|
| AC.REL.1 | GREEN | this doc exists with §1 + §4 + §13; resolved via `--plan-doc` |
| AC.REL.2 | PENDING | `docs/ACTIVE_MINOR` → 1.7.0; in-scope pyprojects → 1.7.0; lockstep test GREEN; `loam --version` → 1.7.0 |
| AC.REL.3 | PENDING | HARD smoke writeup GREEN aggregate verdict + gate-7 evidence |
| AC.REL.4 | PENDING | deliberate-reasoning / primary-persona / handsoff-loop / workspace-bootstrap / dev-sdlc suites GREEN from cold install |
| AC.REL.5 | PENDING | STATE.md `**v1.7.0 ... SHIPPED LOCAL**` entry |
| AC.REL.6 | PENDING | release-roadmap §2 `| v1.7.0 |` row; seal token `7a6a1671` reachable |
| AC.REL.7 | PENDING | `v1-7-0-...migration.yaml` declares `version: v1.7.0` + `operation: no-op` |
| AC.REL.S | PENDING | cold-install `loam --version` → 1.7.0 + deliberate-reasoning entry-point + supersession filter/as_of, no pre-arranged state |
