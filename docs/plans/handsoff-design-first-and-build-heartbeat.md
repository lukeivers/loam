# Plan-doc — handsoff-loop: design-first front stage + build-time progress heartbeat

**Slug (scope-descriptive):** `handsoff-design-first-and-build-heartbeat`
**Status:** sub-plan-doc (two buildable slices under one objective).
**Class:** MINOR — two additive front-/mid-pipeline subsystems on the existing
`build_from_intent` path; no breaking change to the sealed S1–S5 spine. Version
derives at release time — NOT pre-assigned.
**Working directory:** `/Users/lukeivers/loam/`.
**Authored:** 2026-06-24.
**Owner greenlight:** Luke — directed both subsystems (design-first front stage
with a user-validation gate; build-time progress heartbeat) and ruled the
accounting-back-office demo quality is a genuine BUILD TARGET, not an over-claim.

**BASELINE (build time):** `bad861e0` (current canonical main tip). The
handsoff-loop family seals against the **workspace-bootstrap** component anchor
(the source lives under `framework/tools/handsoff-loop/`, inside the
workspace-bootstrap seal-test's admitted `framework/tools/` prefix). The seal-diff
window is `bad861e0..<seal>` per slice.

**Status-file target:** `framework/hands-off-lifecycle/seals/` (the handsoff-loop
family's narrative anchor, per the Slice-2 manifest exemplar).

**Predecessors / load-bearing context:**
- General build-from-intent pipeline (SEALED — the S1–S5 spine this plan extends):
  `docs/plans/sealed/handsoff-loop-real-build.md`; the assembled path is
  `framework/tools/handsoff-loop/src/handsoff_loop/build_from_intent.py`
  (`run_build_from_intent`, the S6 entry point). Last full run logged in
  `framework/tools/handsoff-loop/smoke/RUN_LOG.md`.
- Slice 2 (SEALED — the in-session-dispatcher seam pattern; shipped public v1.1.0):
  `docs/plans/claude-p-to-insession-subagent-fanout-slice2-swarm.md`; seam is
  `set_swarm_in_session_dispatcher` / `get_swarm_in_session_dispatcher` /
  `clear_swarm_in_session_dispatcher` in
  `framework/tools/handsoff-loop/src/handsoff_loop/orchestrator.py`.
- Existing in-loop progress surface (SEALED — AC.PRG.*; the heartbeat substrate
  this plan routes to channels): `progress.py` (`RunRecord`, `start_heartbeat`,
  `audit_progress`, `HEARTBEAT_INTERVAL_S = 120.0`) +
  `convergence.probe_liveness` (the artifact-mtime probe).
- Shared channel module + silent-turn-death alerting (workspace-level, commit
  `3db9360` in pos3): `.claude/hooks/channel_notify.py` —
  `post_to_active_channel(active, body_text, prefix)`,
  `_detect_active_channel(entries)`, `_post_discord` / `_post_telegram`. The
  refusal/turn-death watchdog is `.claude/tools/refusal_watchdog.py`. **These
  live in the pos3 workspace, not canonical loam (port deferred per `3db9360`
  body).**

**Quality bar:** (1) the design stage's per-candidate output reaches the polish
level of the accounting-back-office demo
(`pos3 .../tmc-whitepaper-analysis/response-paper/assets/demo/`) — a genuine
build target, not an over-claim; (2) the heartbeat surfaces real artifact-probe
liveness evidence (never a bare "still working") to whatever channel the user is
actually on, and never weakens any sealed S1–S5 honesty control; (3) the sealed
AC.REQ.* / AC.GEN.* / AC.PRG.* / AC.CVG.* suites stay green.

---

## §1. Summary / TL;DR

Two additive subsystems on the existing `build_from_intent` path:

**Slice DF (design-first front stage).** Today the pipeline runs
`understanding → [single approval] → researching → planning → building`. The
single approval gate (`approve_fn`) fires on the *intent-confirm text* — BEFORE
research and BEFORE any design exists. There is exactly ONE design
(`generate_design` → one `GeneratedDesign`), produced AFTER the approval, with no
user review of the design itself. Slice DF reshapes the front into:

> `vague ask → understand → research → produce N implementation-agnostic
> candidate designs → user reviews / tweaks / SELECTS one → THEN the existing
> build loop runs on the chosen design.`

The validation gate moves to AFTER design generation and operates on the design
artifacts (not the bare intent text). The build loop (freeze → converge → verify)
is **untouched in substance** — it simply receives a user-settled design instead
of the first machine-generated one.

**Slice HB (build-time progress heartbeat).** The heartbeat substrate already
exists (`start_heartbeat` emits artifact-probe liveness to the run record + a
`say` callable). Today `say` defaults to `print` (terminal). Slice HB makes the
heartbeat **channel-aware**: a main-thread-resident monitor that (a) probes
artifact-mtime / output growth for genuine PROGRESS (not mere aliveness), (b)
detects stall and surfaces it, (c) routes periodic plain-language status to the
user's ACTIVE channel (Discord/Telegram) by composing the existing shared channel
module + silent-turn-death alerting, falling back to the main thread when no
channel is enabled.

**AC families:** AC.DF.* (design-first) + AC.HB.* (heartbeat).

**Key decisions baked (recommendations in §3):** N=3 candidate designs; design
artifact = plain-language spec + a representative sample-output rendering per
candidate; validation gate is a new pipeline stage between `planning` and the
freeze; heartbeat composes the channel module (does NOT reinvent); "progress" =
artifact-mtime advance OR run-record growth since last beat; channel detection
reuses `_detect_active_channel`.

**F2 RF on scope realism (see §10):** the demo-quality bar is reachable but it is
**not free** — it is a property of the design PROMPT + a rendering step, not of
the pipeline wiring. SAL-DF-1 names where the real work is. The heartbeat's
canonical-port question (the channel module lives in pos3, not loam) is the one
genuine cross-repo halt-and-surface — SAL-HB-1.

**Demo framing (acceptance-relevant, per owner):** the design stage IS the on-site
TMC demo centerpiece — fast, interactive, room-safe (no 30-minute wait in front of
a prospect: you show N polished candidate designs, the prospect picks/tweaks one
live, and THAT is the visible "loam understood me" moment). The heartbeat is what
makes the slow async build presentable — instead of a dead terminal for 7–32
minutes, the prospect's phone pings with plain-language progress. Both are demo
acceptance criteria, not just product features.

---

## §2. Placement decisions

| Item | Placement | Rationale |
|---|---|---|
| N candidate-design generation | `generative.py` — a new `generate_candidate_designs(intent, grounding, *, n, ...)` alongside the existing `generate_design` | Reuses the domain-blind generation contract (AC.GEN.2); the existing single-design path stays as the n=1 degenerate / non-interactive default. |
| Per-candidate sample-output rendering | `generative.py` (or a sibling `design_render.py`) | The demo-quality bar is a rendering concern, separable from the gate-authoring concern. Keeps `generate_design`'s gate logic untouched. |
| Design-validation gate | `build_from_intent.py` — a new stage between `planning` and the freeze, driven by an injected `choose_design_fn(candidates) -> ChosenDesign` (mirrors the existing `approve_fn`/`answer_fn` intake-surface injection) | The gate belongs to the intake surface, exactly as the sealed single-approval gate. A `None` `choose_design_fn` = standing hands-off → auto-pick candidate 0 (preserves the current non-interactive S6 behaviour byte-for-byte). |
| Design-tweak application | `build_from_intent.py` — the chosen `ChosenDesign` may carry user edits the gate folds into the `GeneratedDesign` before freeze | Tweaks are a property of the chosen design, applied before the (untouched) freeze. |
| Channel-aware heartbeat surface | `progress.py` — a `say` factory `channel_say(...)` that routes through the shared channel module when a channel is detected, else `print` | The heartbeat substrate (`start_heartbeat`) already takes `say`; the composition point is the `say` callable, not the heartbeat loop. Zero change to the loop. |
| Progress (not just liveness) detection | `progress.py` / `convergence.probe_liveness` — extend the probe state with a `progressed_since_last` signal (newest-mtime delta + run-record line-count delta across beats) | `probe_liveness` already reports `artifact_age_s`; progress is the DELTA between consecutive probes. A stall = alive-but-not-progressed for ≥K beats. |
| Stall surface | `progress.py` — the channel-aware `say` emits a distinct stall message when the progress signal flatlines | Stall is a heartbeat-message variant, not a new mechanism. |
| Channel module (loam port) | **DEFERRED — see SAL-HB-1.** Slice HB composes the channel module via an injected `notify_fn`; the actual pos3→loam port of `channel_notify.py` is a separate coordinate-later item (`3db9360` body; tasks #19/#81) | The heartbeat must not hard-depend on a pos3-only file. It takes `notify_fn` (the workspace injects `post_to_active_channel`); loam ships a terminal-default. |

---

## §3. Named decisions (each with a recommendation — owner rules from these)

> Per `feedback_summarize_and_surface_decisions`: each decision carries a
> recommendation. The recommendation IS the decision unless the owner overrides.

- **D-1 — How many candidate designs (N)?** **Recommend N=3.** Three is the
  swarming-literature default for "enough genuine alternatives to make a choice
  meaningful without choice-overload"; it reads well in a demo (a tight row of
  three cards). N is a parameter (`n=3` default) so a demo can dial it. *Method
  note:* the three must be genuinely different design directions (e.g. for "clean
  up my client list": a one-shot CLI vs an interactive review-queue app vs a
  scheduled background normalizer), not three phrasings of one design.

- **D-2 — Design artifact format: spec vs mockup vs sample-output?**
  **Recommend: plain-language spec + a representative SAMPLE-OUTPUT rendering per
  candidate** (NOT a clickable mockup). Rationale: the demo-quality bar IS a
  polished *output* (the accounting demo is a rendered report, not a Figma mock).
  A sample-output rendering is (a) implementation-agnostic (it shows what the
  thing PRODUCES, not how it is coded), (b) the exact thing the prospect cares
  about, (c) reachable by the same generative primitive. A clickable mockup is
  more demo-dazzle but is method-heavy (UI scaffolding) and risks implying a
  shape the build can't honor. *Surfaced alternative:* a lightweight static HTML
  preview of the sample output (dynamic-theme per
  `feedback_dynamic_theme_for_generated_documents`) is the demo-grade upgrade if
  the owner wants the on-screen polish — recommend it as a Slice-DF stretch, gated
  behind the spec+sample core.

- **D-3 — Where does the validation gate live?** **Recommend: a new pipeline
  stage between `planning` (design generation) and the freeze**, driven by an
  injected `choose_design_fn`. Rationale: the freeze + build loop must not start
  until the user settles a design — that is the prime-directive verify-before-
  commit move made concrete. Placing it post-design (not on the current
  pre-research intent-confirm) is the substantive change. The existing
  intent-confirm approval gate is KEPT (it is a cheaper, earlier "am I even
  building the right category of thing" check); the new design gate is the
  expensive-commit gate. *Two gates, two purposes — surfaced explicitly so a
  reviewer does not read it as redundancy.*

- **D-4 — Heartbeat cadence?** **Recommend: keep `HEARTBEAT_INTERVAL_S = 120.0`
  as the on-disk/run-record bound, but throttle CHANNEL posts to a longer
  interval (recommend 300s / 5 min) with an immediate post on stage-transition
  and on stall-detection.** Rationale: a Discord/Telegram ping every 2 minutes for
  32 minutes is 16 pings — notification fatigue. The run-record keeps the 120s
  fidelity (audit-grade); the channel gets a calmer cadence + event-driven posts
  (stage change, stall, done). *Method note:* this is two cadences, one substrate.

- **D-5 — What is "progress" measured as?** **Recommend: progress =
  (newest-artifact-mtime advanced) OR (run-record gained ≥1 line) since the last
  probe.** Honors `feedback_dead_agent_detection_via_artifact_probe` — probe the
  artifact, never the poller's "still running." A build that is alive (process up)
  but has written nothing new for K consecutive beats (recommend K=3 → ~6 min at
  the 120s probe) is a STALL, surfaced distinctly. *This is the dead-agent-probe
  pattern applied to progress-not-liveness — the dispatch named it; it is honored
  by construction.*

- **D-6 — Channel-detection mechanism?** **Recommend: reuse
  `_detect_active_channel(entries)` from the shared channel module via an injected
  `notify_fn` — do NOT reinvent.** The heartbeat takes a `notify_fn(text)` the
  workspace wires to `post_to_active_channel`; loam ships a terminal-default
  `notify_fn=print`. No channel state is read inside loam source (keeps loam free
  of the pos3-only channel files; SAL-HB-1).

- **D-7 — Does Slice DF or Slice HB ship first?** **Recommend: Slice DF first.**
  It is the demo centerpiece and the higher-value prime-directive move; the
  heartbeat is the async-presentability layer that matters most once a real
  build runs in front of a prospect. They are independent (no shared fence beyond
  the `build_from_intent.py` orchestration function) and can build in either
  order; DF-first maximizes demo readiness soonest.

---

## §4. Spec-objective placement

**Binds to AC.PO.1 + AC.PO.2** (prime objective, `docs/VALUE_PROPOSITION.md`):

- **Slice DF → AC.PO.1 (translation):** design-first IS the Lens-0 four-step loop
  made concrete on the build path — infer the end-intent (understand) → design a
  healthy way to enable it (N candidate designs) → SURFACE IT BACK to the user to
  verify (the validation gate) → learn from the answer (the chosen+tweaked
  design). It is the "surface the inferred intent for verification before
  committing the expensive build" commitment, literally.
- **Slice HB → AC.PO.1 (protection floor) + AC.PO.2 (harness toolkit):** the
  heartbeat guards the "no real memory / goes silent" betrayal — the user is never
  left in the dark during a 7–32 min build; it adds a reusable progress-surface to
  the primary-persona toolkit (Lens 2 harness-test).

**Ladders to:** AC.DF.* / AC.HB.* → this minor → the handsoff-loop's
"vague ask → finished product" promise → AC.PO.

---

## §5. Acceptance criteria

> AC IDs scope-descriptive. All ACs outcome-shape — they state the observable
> outcome, never the method. Method-in-AC test applied to each: *can this AC be
> satisfied by a method other than the one I have in mind?* — yes for every AC
> below (noted inline), so each is outcome-shape.

### Slice DF — AC.DF.* (design-first front stage)

- **AC.DF.1 — the pipeline produces MULTIPLE candidate designs before any build
  starts.** A `run_build_from_intent` run over one ask, with a design-choice
  surface reachable, generates ≥2 (default 3) materially-distinct candidate
  designs and surfaces them for choice BEFORE the acceptance gate is frozen and
  BEFORE any build sub-task dispatches. *Outcome, not method:* asserts ≥2
  candidates exist + are surfaced pre-freeze; does not prescribe how they are
  generated or rendered. *Satisfiable other ways:* one dispatch returning N
  designs, or N dispatches — both pass.

- **AC.DF.2 — the build loop does NOT start until the user settles on a design.**
  When a `choose_design_fn` is provided and returns no choice (user declines /
  abandons), NO acceptance gate is frozen and NO build sub-task dispatches — the
  run terminates with a distinct non-built terminal (`design-not-chosen`). When a
  choice IS returned, the build proceeds on exactly the chosen (optionally tweaked)
  design. *Outcome, not method:* asserts the freeze+build is gated on a settled
  design; does not prescribe the choice UI. *Satisfiable other ways:* numbered
  terminal prompt, a channel reply, a test double — all pass.

- **AC.DF.3 — the chosen design carries the user's tweaks into the frozen build.**
  When the chosen design includes a user edit (a changed objective sentence, an
  added/removed gate criterion, a changed output shape), the frozen acceptance gate
  and the build briefs reflect the EDITED design, not the original machine
  candidate. *Outcome, not method:* asserts the edit propagates to the freeze; does
  not prescribe the edit mechanism.

- **AC.DF.4 — non-interactive runs are byte-behaviour-preserved (no regression).**
  A `run_build_from_intent` run with NO design-choice surface (`choose_design_fn=None`,
  the standing-hands-off path the sealed S6 proof + smoke use) reaches the same
  terminal set and the same freeze→build→verdict spine as before this slice — the
  design-first stage degrades to "auto-pick candidate 0" and the sealed AC.REQ.* /
  AC.GEN.* / AC.PRG.* / AC.CVG.* suites stay green. *Outcome, not method:* asserts
  no behavioural regression on the non-interactive path.

- **AC.DF.5 — a candidate design's sample-output rendering reaches the named
  quality bar (outcome-altitude).** **Marked `outcome-altitude: true`.** Invoking
  the candidate-design generation on a real ask (the accounting-back-office ask, or
  an equivalent) with no pre-arranged state produces, for at least one candidate, a
  sample-output rendering that satisfies a checkable quality rubric derived from the
  accounting demo (e.g. ≥N named output sections, a populated tabular result, a
  plain-language summary, a review-queue-equivalent) — verified by a check the
  generator never saw. *Outcome, not method:* asserts the rendered output meets a
  rubric; does not prescribe the prompt or renderer. *This is the owner's "demo
  quality is a real build target" ruling, made into a falsifiable AC.*

- **AC.DF.6 — candidate designs are framed for the user's tech level
  (defaulting NON-TECHNICAL); a non-tech user is never offered a candidate whose
  primary interaction is developer machinery.** Candidate generation infers /
  assumes the user's tech level and constrains the candidate space accordingly,
  defaulting to a NON-TECHNICAL user when the level is not established. For a
  non-technical user, every surfaced candidate is something the user can
  personally SEE and USE without developer skill — a visible/interactive
  experience (a page/screen/app they open) OR a sensible automated delivery (e.g.
  the finished result is emailed to them on a schedule) — and NO surfaced
  candidate's primary interaction is a command-line tool, a daemon /
  background-watch service the user must manage, a drop-folder to configure, or
  any surface that presumes the user can operate developer machinery. *Outcome,
  not method:* asserts the surfaced candidate set for a non-tech user contains
  only see-and-use / sensible-delivery shapes and excludes CLI/daemon-primary
  shapes; does not prescribe how the tech level is inferred or how the
  constraint is applied (a prompt constraint, a seed partition, a post-filter, or
  any combination all satisfy it). *Satisfiable other ways:* a generation prompt
  that forbids the technical surfaces, OR a held-out classifier that drops a
  CLI/daemon candidate, OR both — all pass. *This is the owner ruling
  (`2026-06-24-design-first-non-tech-user-visible-outputs`) made into a
  falsifiable AC: rehearsal-1 generated a CLI candidate (option 1) and a
  "file-watch daemon" candidate (option 3) for a non-technical accounting-firm
  owner — meaningless to that user; AC.DF.6 fails any candidate set that hands a
  non-tech user a CLI/daemon-primary option.* **Mark: tech-level inference
  beyond the non-tech default (so a confirmed TECHNICAL user gets technical
  candidates) is a surfaced follow-up — the demo case is non-tech and is fully
  covered by the default; AC.DF.6 closes on the non-tech guarantee.*

### Slice HB — AC.HB.* (build-time progress heartbeat)

- **AC.HB.1 — the build leg surfaces periodic progress to the user's active
  channel.** During a long build leg, with a `notify_fn` wired to a channel, the
  user receives periodic plain-language status posts on the channel they are
  actually on (Discord OR Telegram, per the active-channel detection), at the
  channel cadence (D-4). With no channel wired, the status surfaces on the main
  thread (terminal). *Outcome, not method:* asserts the user sees periodic status
  on the right surface; does not prescribe the post mechanism.

- **AC.HB.2 — heartbeats carry artifact-probe PROGRESS evidence, not bare
  aliveness.** Every surfaced heartbeat message carries evidence derived from the
  artifact probe (newest-artifact age + whether new work landed since the last
  beat) — never a bare "still working" with no probe state behind it. *Outcome, not
  method:* asserts the evidence is probe-derived; honors
  `feedback_dead_agent_detection_via_artifact_probe`. *Satisfiable other ways:*
  any probe that reads disk artifacts (mtime, size, line-count) passes.

- **AC.HB.3 — a stall (alive-but-not-progressing) is detected and surfaced
  distinctly.** When the build process is alive but no new artifact / run-record
  line has landed for ≥K consecutive probes, the heartbeat surfaces a DISTINCT
  stall message (different from the normal progress beat), so the user can tell
  "moving" from "stuck." *Outcome, not method:* asserts a distinct stall surface on
  flatlined progress; does not prescribe the threshold mechanism.

- **AC.HB.4 — the heartbeat composes the existing alerting infra; no sealed honesty
  control weakens.** The heartbeat routes through an injected `notify_fn` (the
  workspace wires the shared channel module) rather than a reinvented channel path,
  AND the sealed AC.PRG.* write-then-say contract is intact (every channel-surfaced
  line still exists in the run record before it is shown), AND no sealed S1–S5
  control (frozen-acceptance isolation, independent-verify, the bounded re-drive) is
  touched. *Outcome, not method:* asserts composition + zero honesty regression.

- **AC.HB.5 — a real build run surfaces a real progress signal end-to-end
  (outcome-altitude).** **Marked `outcome-altitude: true`.** Invoking the build leg
  on a real run dir with real artifacts landing on disk (no pre-arranged
  run-record state), with a capturing `notify_fn`, yields ≥1 captured progress post
  whose evidence reflects an actual artifact that landed during the run, AND the
  post-run `audit_progress` reports `gap_within_bound: true`. *Outcome, not
  method:* asserts a genuine end-to-end progress signal against a live run.

**Slice DF seal closes on:** AC.DF.1–.5.
**Slice DF amendment (non-tech candidate framing) seal closes on:** AC.DF.6.
**Slice HB seal closes on:** AC.HB.1–.5.

---

## §6. Build steps (method-level guidance — builder's call per ODD §1.1)

### Slice DF

1. Manifest: `docs/plans/handsoff-design-first-and-build-heartbeat.manifest.yaml`
   (shared across both slices, OR a per-slice manifest if built separately —
   builder's call; single-component anchor = `workspace-bootstrap`; narrative
   under `framework/hands-off-lifecycle/seals/`; BASELINE `bad861e0`).
2. Add `generate_candidate_designs(...)` in `generative.py` (N-design generation;
   the existing `generate_design` stays as the n=1 path). Add per-candidate
   sample-output rendering (recommend a sibling concern, D-2).
3. Add the design-validation stage to `build_from_intent.py` between `planning`
   and the freeze, driven by an injected `choose_design_fn`. `None` → auto-pick
   candidate 0 (preserves AC.DF.4). Fold user tweaks into the chosen
   `GeneratedDesign` before the (untouched) freeze.
4. Author tests for AC.DF.1–.5 (AC.DF.5 outcome-altitude: real ask, no
   pre-arranged state, rubric check the generator never saw).
5. `loam amend apply` → tests green → `loam amend seal` → LOCAL only (no push).

### Slice HB

1. Manifest as above (or per-slice). BASELINE `bad861e0` (or Slice-DF's apply tip
   if DF sealed first — builder reconciles per `feedback_serialize_amendment_builds`).
2. Add the channel-aware `say`/`notify_fn` factory + progress-delta + stall logic
   in `progress.py`. Loam ships `notify_fn=print` default; the channel wiring is an
   injection point (SAL-HB-1 — no pos3-only import in loam source).
3. Wire the build leg's `start_heartbeat` to the channel cadence (D-4) + immediate
   stage-transition / stall / done posts.
4. Author tests for AC.HB.1–.5 (AC.HB.5 outcome-altitude: real run dir, real
   artifacts, capturing `notify_fn`).
5. `loam amend apply` → tests green → `loam amend seal` → LOCAL only (no push).

---

## §7. Out of scope

1. **Auto-retry on stall** — Slice HB is alert-only (mirrors `3db9360`'s
   alert-only-this-cycle discipline). A stall is surfaced, not auto-killed/retried.
2. **The pos3→loam port of `channel_notify.py` / the watchdog** — coordinate-later
   (tasks #19/#81); Slice HB composes via injection, does not port (SAL-HB-1).
3. **A clickable interactive mockup** — D-2 recommends spec+sample-output; a
   clickable mock is method-heavy and out of scope (the static-HTML preview is a
   surfaced Slice-DF stretch, gated).
4. **Changing the build loop / freeze / verify spine** — design-first feeds the
   spine a settled design; it does not alter freeze→converge→verify.
5. **Multi-round design negotiation** (the user iterating designs across multiple
   turns) — Slice DF is single-round (review N → pick/tweak one). Multi-round is a
   surfaced follow-up.
6. **Pushing the minor to origin** — owner-gated release later.

---

## §8. Halt triggers (in-flight conditions that abort the build)

- **H-1 — a sealed honesty control would weaken.** If the design-first stage or the
  channel heartbeat cannot be added without weakening frozen-acceptance isolation,
  the independent-verify gate, the bounded re-drive, or the AC.PRG write-then-say
  contract, HALT.
- **H-2 — the no-API-key invariant is at risk.** If candidate-design generation or
  the heartbeat reaches for the `anthropic` SDK / `ANTHROPIC_API_KEY` instead of the
  sealed `claude -p` primitive, HALT (`feedback_no_anthropic_api_key`).
- **H-3 — loam source would hard-depend on a pos3-only file.** If Slice HB cannot
  be built without importing `channel_notify.py` (a pos3 workspace file) into loam
  source, HALT and surface — the injection seam (D-6) is the contract; a hard import
  is a fence violation.
- **H-4 — non-interactive regression.** If the design-first stage cannot preserve
  the sealed non-interactive S6 path byte-behaviour (AC.DF.4), HALT — the standing-
  hands-off proof + smoke must stay green.
- **H-5 — the demo-quality bar proves unreachable by the generative primitive
  alone.** If AC.DF.5's rubric cannot be met without a method outside the
  domain-blind generation contract (e.g. a hand-built vertical renderer that would
  reintroduce the June-8 faked-demo shape), HALT and surface rather than faking it.

---

## §9. Bookkeeping (post-build backfill)

- STATE.md: add the minor's entry (per-slice seal SHAs).
- Roadmap (`docs/plans/loam-roadmap.md` or the live roadmap): note the design-first
  + heartbeat subsystems against the handsoff-loop track.
- §14 register: backfill D-build.* + commit SHAs at seal time.
- Tasks: open the pos3→loam channel-module port follow-up (SAL-HB-1) + the
  static-HTML-preview stretch (D-2) + the multi-round-design follow-up (§7.5), each
  with a durable capture per `feedback_durable_capture_for_planned_work`.

---

## §10. F2 Ruthless Feedback (honest doubts + named risks)

- **SAL-DF-1 — the demo-quality bar is reachable but the work is in the PROMPT +
  a rendering step, NOT the pipeline wiring; do not under-scope it.**
  *Disagreement:* it would be easy to read "add N candidate designs + a gate" as
  pure plumbing and assume the accounting-demo polish falls out. It will not.
  *Evidence:* the accounting demo
  (`pos3 .../response-paper/assets/demo/`) is a multi-section rendered report
  (overview, pipeline, results, review-queue, summary) — that polish is a property
  of (a) a generation prompt that asks for a rich sample output and (b) a renderer
  that lays it out, neither of which exists today (`generative.py`'s current prompt
  asks only for a `gate_plain` "done-when" sentence + a verification script, not a
  polished sample output). *Alternative:* scope AC.DF.5 as a falsifiable rubric
  check (done — §5) and budget the prompt+render work explicitly; treat the
  static-HTML preview (D-2 stretch) as the demo-grade finish only after the
  spec+sample core passes the rubric. The risk if ignored: a slice that "works"
  (N designs, a gate) but whose designs look like terse spec bullets, missing the
  owner's actual bar.

- **SAL-DF-2 — the current single approval gate fires on the WRONG artifact for
  the prime-directive move; keep both gates, name their purposes.**
  *Disagreement:* one could "move" the existing approval gate to the design and
  call it done. *Evidence:* the existing gate (`build_from_intent.py` L204–218)
  fires on `build_confirm_text(intent)` — the intent inference, BEFORE research,
  BEFORE any design. That is a useful cheap "right category?" check but it is NOT
  the verify-before-expensive-commit gate the prime directive wants. *Alternative:*
  KEEP the intent-confirm gate (cheap, early) AND add the design gate (expensive-
  commit, post-design) — two gates, two purposes (D-3). Surfaced so a reviewer does
  not flag the second gate as redundant or "move the existing one" as the simpler
  path — it is not equivalent.

- **SAL-HB-1 — the heartbeat's channel surface lives in pos3, not loam; the port
  is the one genuine cross-repo decision.** *Disagreement:* the dispatch says
  "compose with the silent-turn-death alerting + shared channel module" — but those
  (`3db9360`) are pos3 workspace files, and `3db9360`'s own body says "Canonical
  loam port of all three pieces deferred (coordinate-later with #19/#81 — do not
  port from here)." *Evidence:* `channel_notify.py`, `stopfailure_alert.py`,
  `refusal_watchdog.py` are under `pos3/.claude/`, not `loam/`. A loam slice cannot
  hard-import them. *Alternative:* Slice HB composes via an injected `notify_fn`
  (the workspace wires `post_to_active_channel`); loam ships a terminal default and
  the actual port stays a separate coordinate-later item (H-3 makes a hard import a
  halt). This keeps the loam slice clean AND honors the explicit "do not port from
  here" instruction. *This is the item most likely to need an owner ruling if the
  owner actually wants the channel code IN loam now — surfaced, not silently
  resolved.*

- **SAL-HB-2 — "progress" vs "liveness" is a real distinction the existing probe
  does NOT yet make.** *Evidence:* `convergence.probe_liveness` reports
  `artifact_age_s` (how long since the newest file changed) — that is LIVENESS
  (is anything fresh?), not PROGRESS (did something NEW land since last I looked?).
  The dispatch explicitly asks for progress-not-aliveness. *Alternative:* compute
  progress as the DELTA between consecutive probes (newest-mtime advanced OR
  run-record gained a line) — D-5. The existing probe is the input; the delta is
  the new signal. Honors `feedback_dead_agent_detection_via_artifact_probe` by
  construction (probe artifacts, never poller cadence).

- **SAL-DF-3 — N genuinely-distinct designs is a generation-quality risk, not a
  wiring risk.** *Evidence:* `generate_design` today produces ONE design from one
  prompt; asking for N risks N-phrasings-of-one-design (the cheap failure). *
  Alternative:* AC.DF.1 requires "materially-distinct" candidates; the generation
  prompt must demand distinct DIRECTIONS (form-factor / workflow), and the test
  asserts distinctness (e.g. different form_factor or non-trivial edit distance).
  Surfaced so the builder does not satisfy AC.DF.1 with three trivial variants.

---

## §11. Primitive check (REQUIRED — new mechanisms introduced)

| New mechanism | Native primitive considered | Chosen |
|---|---|---|
| N candidate-design generation | `claude -p` via the sealed `intake._claude_json` (subscription-routed, no API key) | **The sealed `claude -p` primitive** — same dispatch every other generative leg uses; one dispatch returning N designs (or N dispatches), builder's call. No new spawn surface. |
| Design-validation gate (user choice) | The existing injected intake-surface callable pattern (`approve_fn` / `answer_fn`) | **An injected `choose_design_fn` callable** — mirrors the sealed single-approval injection; the channel/terminal surface is the caller's, not loam's. |
| Channel-routed heartbeat | The shared channel module (`post_to_active_channel` / `_detect_active_channel`) + the Discord/Telegram MCP reply path it wraps | **Compose via injected `notify_fn`** — loam does not reinvent channel routing; the workspace wires the shared module (Lens 1: compose on the platform primitive; the channel MCP reply is the underlying Claude-native surface). |
| Progress-delta / stall signal | The existing `convergence.probe_liveness` artifact probe | **Extend the probe with a cross-beat delta** — bespoke-minimal (a delta over the existing probe), no new primitive; honors the dead-agent-probe pattern. |

---

## §12. Provenance trail (Tier-0 — verified against the code this session)

- `framework/tools/handsoff-loop/src/handsoff_loop/build_from_intent.py` —
  CONFIRMED: `run_build_from_intent` (L129–355) runs understanding (L165) →
  asking (L183) → the SINGLE approval gate on `build_confirm_text(intent)` (L204–218,
  fires on the intent inference, pre-research) → researching (L220) → planning =
  ONE `generate_design` (L268) → freeze (L297) → build (L326) → verdict. **No
  design-choice gate exists; exactly one design is generated, post-approval.**
- `framework/tools/handsoff-loop/src/handsoff_loop/generative.py` — CONFIRMED:
  `generate_design` (L210) produces ONE `GeneratedDesign`; the prompt (L111–167)
  asks for `gate_plain` (one "done-when" sentence) + a verification script + 1–3
  sub-tasks — NOT a polished multi-section sample output. The demo-quality bar
  needs prompt + render work (SAL-DF-1).
- `framework/tools/handsoff-loop/src/handsoff_loop/progress.py` — CONFIRMED:
  `start_heartbeat` (L108) emits artifact-probe liveness to the run record + a
  `say` callable; `say` defaults to `print` (terminal). The docstring (L24–30)
  already NAMES "channel reply/edit when a channel is connected" as the intended
  surface — but the channel routing is NOT wired. `HEARTBEAT_INTERVAL_S = 120.0`
  (L42). `audit_progress` (L146) enforces the write-then-say + gap-within-bound
  contract.
- `framework/tools/handsoff-loop/src/handsoff_loop/convergence.py` — CONFIRMED:
  `probe_liveness` (L157) reports `artifact_age_s` (LIVENESS, newest-mtime age) —
  NOT a cross-probe PROGRESS delta (SAL-HB-2).
- `framework/tools/handsoff-loop/src/handsoff_loop/orchestrator.py` — CONFIRMED:
  `set_swarm_in_session_dispatcher` / `get_` / `clear_` (L92–113) — the
  in-session-dispatcher seam; the build leg runs in the same process as
  `run_build_from_intent` (heartbeat thread is already main-thread-resident).
- `pos3/.claude/hooks/channel_notify.py` — CONFIRMED:
  `post_to_active_channel(active, body_text, prefix)` (L241),
  `_detect_active_channel(entries)` (L77), `_post_discord` (L159) / `_post_telegram`
  (L199) — the shared channel module Slice HB composes via injection. **In pos3,
  not loam** (SAL-HB-1).
- pos3 commit `3db9360` — CONFIRMED: "two-layer silent-turn-death alerting + shared
  channel module"; body states "Canonical loam port of all three pieces deferred
  (coordinate-later with #19/#81 — do not port from here)."
- `pos3 .../tmc-whitepaper-analysis/response-paper/assets/demo/` — CONFIRMED the
  accounting-back-office demo assets (rendered report + raw-outputs JSON/CSV) — the
  AC.DF.5 quality bar.
- `plugins/dev-sdlc/docs/conventions/plan-docs.md` — CONFIRMED the plan-doc +
  manifest shape this doc follows (§1–§7 + §14 register + Primitive check).
- `docs/plans/claude-p-to-insession-subagent-fanout-slice2-swarm.md` — CONFIRMED the
  shape exemplar + the workspace-bootstrap seal anchor / `framework/hands-off-lifecycle/seals/`
  narrative target this plan reuses.

---

## §14. Method-decision register (builder's call — populated at build/seal time)

- **D-build.1 — candidate-design generation mechanism** (per D-1/SAL-DF-3): one
  dispatch returning N or N dispatches; distinctness enforced. *(narrate at build)*
- **D-build.2 — sample-output rendering mechanism** (per D-2/SAL-DF-1): spec +
  sample-output core; static-HTML preview gated stretch. *(narrate at build)*
- **D-build.3 — design-validation gate wiring** (per D-3): injected
  `choose_design_fn`; `None` → auto-pick candidate 0; tweaks folded pre-freeze.
  *(narrate at build)*
- **D-build.4 — channel-aware `say` / `notify_fn` injection** (per D-6/SAL-HB-1):
  loam ships terminal default; workspace wires the shared channel module; no
  pos3-only import in loam source. *(narrate at build)*
- **D-build.5 — progress-delta + stall detection** (per D-5/SAL-HB-2): cross-beat
  delta over `probe_liveness`; stall = flatline ≥K beats. *(narrate at build)*

### Commit SHAs

- BASELINE: `bad861e0` (canonical main tip at plan-authoring).
- Slice DF — code / apply / seal: `e5ff74b4` / `f7f78d2a` / `014dd9ad`.
- Slice HB — code / apply / seal: `cf34067d` / `2efda4ba` / `1a094701`.
- Slice DF amendment (AC.DF.6 — non-tech candidate framing) — baseline
  `65c1f27d`; code / apply / seal: `3050e0e5` / `6ba1a60f` / `f4b7e079`. Manifest
  `docs/plans/handsoff-df6-nontech-visible-candidates.manifest.yaml`. LOCAL seal
  only — not pushed.

### Method-decision register (Slice DF, narrated at build)

- **D-build.1 — candidate-design generation mechanism:** N per-candidate
  dispatches (the §11 "N dispatches" alternative), NOT one batched N-object
  response. Empirical driver: a single batched N=3 dispatch carrying full
  gate_files timed out at the 900s ceiling; a batched N=3 *lightweight* dispatch
  returned in ~170s but the model mis-nested trailing braces on the deeply-nested
  sample_output ~1-in-3 (a structural corruption, not a recoverable escaping
  issue, so a parse-repair heuristic was rejected as unsafe). Per-candidate
  dispatch is ~half the JSON size and parsed 3/3 clean. A rotating
  `_DIRECTION_SEEDS` bias + accrue-time distinctness give materially-distinct
  directions (SAL-DF-3). Each call carries a finite parse-retry bound
  (`CANDIDATES_PARSE_ATTEMPTS=3`).
- **D-build.2 — sample-output rendering mechanism:** spec + a structured
  `sample_output` dict (the rendering substrate; a caller lays it out as text or
  HTML). The heavy buildable gate (gate_files, verification scripts) is generated
  for the CHOSEN direction only via the UNCHANGED `generate_design` — the
  budget-safe split. The static-HTML preview (D-2 stretch) stays gated/unbuilt.
- **D-build.3 — design-validation gate wiring:** injected
  `choose_design_fn(candidates) -> ChosenDesign | None`; `None` (standing
  hands-off) keeps the single-design path byte-for-byte (AC.DF.4); a returned
  `ChosenDesign` conditions a `generate_design` call on the chosen direction and
  folds tweaks (`apply_design_tweaks`) into the gate before the unchanged freeze
  (AC.DF.3); `None` back from the fn = `design-not-chosen` terminal, no freeze,
  no dispatch (AC.DF.2).

### Verification (Tier-0)

- AC.DF.1–.5 tests authored at AC altitude (`tests/test_AC_DF_*.py`), one file
  per AC. AC.DF.5 marked outcome-altitude.
- Offline DF suite: 17 passed (the AC.DF.5 live test env-gated/skipped offline).
- AC.DF.5 outcome-altitude LIVE: PASS 2/2 — real `claude -p`, no pre-arranged
  state, a real candidate's sample-output met the held-out `design_rubric_check`
  the generator never saw. The owner's "demo quality is a real build target"
  ruling is a verified, non-hollow pass.
- Sealed-suite regression (AC.DF.4 / H-4): 89 passed, 2 skipped — the sealed
  AC.REQ/GEN/PRG/CVG spine stays green; the non-interactive path is byte-preserved.
- AC.GEN.2 zero-vertical-code sweep: zero domain-vocabulary hits in pipeline
  source (the rubric's accounting-demo provenance is named only here + in the
  AC.DF.5 test, never in source).
- Seal: `014dd9ad`; post-seal `apply --dry-run` clean. LOCAL only — not pushed.

### Method-decision register (Slice HB, narrated at build)

- **D-build.4 — channel-aware `say` / `notify_fn` injection (per D-6 /
  SAL-HB-1 / H-3):** the injection seam is `channel_say(notify_fn, *, prefix)`
  in `progress.py` — wraps an injected channel-post callable as a `say`-shaped
  callable; loam ships `print` as the terminal default. `start_heartbeat` was
  extended ADDITIVELY (new kwargs `notify_fn` / `channel_interval_s` /
  `stall_after_beats` / `run_record_path`, all defaulting to the sealed
  behaviour) rather than forked — with `notify_fn=None` the loop is
  byte-behaviour-identical to the sealed heartbeat, so the AC.PRG suites stay
  green by construction (AC.HB.4). `run_build_from_intent` gained a `notify_fn`
  param threaded to the long build-leg heartbeat; the research + planning legs
  keep the terminal-only `start_heartbeat` (the build leg is the long async
  leg AC.HB.5 targets). NO pos3-only channel file is imported anywhere in loam
  source — verified by a fence test scanning import-statement shapes for
  `channel_notify` / `stopfailure_alert` / `refusal_watchdog` /
  `post_to_active_channel` / `_detect_active_channel` (AC.HB.4 / H-3).
- **D-build.5 — progress-delta + stall detection (per D-5 / SAL-HB-2):**
  `convergence.probe_progress(run_dir, *, prev, run_record_path)` — a cross-beat
  delta over `probe_liveness`: progress = newest BUILD-artifact mtime advanced
  (or a build artifact appeared where there was none) OR the run record gained a
  build-meaningful line. **The run record's OWN heartbeat churn is EXCLUDED**
  from both signals (the newest-artifact scan skips `run_record.jsonl`; the
  line-count signal skips `heartbeat`-stage events) — without this exclusion the
  heartbeat's own narration writes would look like progress and mask every
  stall in the real pipeline (the beat that asks "did anything move?" would
  itself be the movement). Stall = `stall_beats >= STALL_AFTER_BEATS` (default
  3) consecutive non-progressing beats; any progress resets the counter. The
  stall surfaces a DISTINCT message and fires an IMMEDIATE channel post on onset,
  bypassing the channel throttle (AC.HB.3). Channel cadence `CHANNEL_INTERVAL_S`
  (default 300s) throttles channel posts while the run record keeps the full
  `HEARTBEAT_INTERVAL_S` (120s) audit fidelity (D-4). Honors
  `feedback_dead_agent_detection_via_artifact_probe` by construction (the delta
  is computed from disk artifacts, never poller cadence).

### Verification (Tier-0, Slice HB)

- AC.HB.1–.5 tests authored at AC altitude (`tests/test_AC_HB_*.py`), one file
  per AC. AC.HB.5 marked outcome-altitude.
- HB suite: 14 passed (offline). AC.HB.5 outcome-altitude PASSES OFFLINE — it
  invokes the production heartbeat entry point (`start_heartbeat`) against a
  live run dir where a REAL worker thread writes REAL artifacts to disk over
  time (no pre-arranged run-record state), captures the channel surface via a
  real `notify_fn`, and the held-out sealed `audit_progress` verifier (which
  never saw the emission) reports `gap_within_bound: true` with zero
  write-then-say breaches. Not a stub: a genuine end-to-end progress signal off
  real disk activity.
- Sealed-suite regression (AC.HB.4 / H-1): full offline handsoff-loop suite
  93 passed, 2 skipped (the 2 skips are env-gated live OA tests) — the sealed
  AC.REQ/GEN/PRG/CVG/DF spine stays green; the non-interactive heartbeat path is
  byte-preserved with `notify_fn=None`.
- SAL-HB-1 / H-3 honored: no workspace channel module imported in loam source
  (the `channel_notify.py` / watchdog stay in pos3; loam composes via the
  `notify_fn` injection seam only). The pos3→loam port stays a coordinate-later
  follow-up (§9 / tasks #19/#81).
- Seal: `1a094701`; post-seal `apply --dry-run` clean; workspace-bootstrap
  fence seal-test green (`bad861e0..2efda4ba` contains only admitted prefixes).
  LOCAL only — not pushed (owner-gated).

---

## §16. Halt-and-surface findings (raised at plan-authoring)

1. **The dispatch's "compose with the silent-turn-death alerting + shared channel
   module" instruction points at pos3 files that `3db9360` explicitly says NOT to
   port from.** Resolved (Lens 6) by composing via injection (SAL-HB-1 / D-6 / H-3);
   surfaced for owner ruling if the owner actually wants the channel code IN loam
   now.
2. **The current single approval gate is NOT the prime-directive verify-before-
   commit gate** (it fires pre-research on the intent inference). Resolved by
   keeping both gates with named distinct purposes (SAL-DF-2 / D-3); surfaced so
   the second gate is not read as redundant.
3. **The pipeline already has a "planning"/design stage and a heartbeat substrate
   — neither subsystem is greenfield.** Design-first EXTENDS the single-design
   stage (N candidates + a post-design gate); the heartbeat ROUTES the existing
   substrate to channels (channel-aware `say` + progress-delta). Stated precisely
   so the builder does not rebuild what exists (§12 grounds every claim in code).
4. **No conflict found between the owner's directed shape and the existing
   architecture** beyond items 1–3 — both subsystems are additive on the sealed
   spine. No hard-halt-class contradiction surfaced.
