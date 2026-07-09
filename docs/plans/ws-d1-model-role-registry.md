# WS-D1 — model-role registry (adversarial-review, SEALED amend)

**Slug:** `ws-d1-model-role-registry`
**Working directory (build):** `/Users/lukeivers/loam-ws-d1-wt` (isolated worktree of
`/Users/lukeivers/loam`, branch `feat/ws-d1-model-role-registry`, base `c53458da`).
**Component:** `framework/adversarial-review/` — **SEALED**. Full `loam amend` cycle
(apply + seal), never free edits.
**Source:** `workspace/strategy/ai-shop-backplane/BACKPLANE-PLAN.md` §5 WS-D1.
**Model:** Sonnet (well-specified build, not an open design problem).

## 0. Why an isolated worktree (build-method note, not a scope change)

The canonical shared dir `/Users/lukeivers/loam` was observed cycling branches under
concurrent sibling backplane builds (WS-A1/A2/A3/B1) with untracked spillover in the
working tree — the live `feedback_serialize_amendment_builds` hazard (two builds in one
tree race on `index.lock` / loam-amend / tests). The plan's §5 rule authorises the
resolution: *"units in the same working tree either serialize or run in isolated
worktrees."* WS-D1 has zero dependency on the siblings, so it builds in its own worktree
off clean `main` (`c53458da`), which also gives the narrowest `BASELINE..seal` fence
window (no sibling commits inside it).

## 1. Objective

Writer / critic / judge roles resolve to **named model legs** from config at dispatch
time, so any role can point at any backend (Claude default, `codex exec`, local) as a
**config entry rather than a code change**, and every finding is tagged with the model
that produced it. This is the seam WS-D2 (Codex critic leg) lands its first non-default
entry on.

The seam already exists: `critic.py:55` `ModelFn = Callable[[str], Optional[str]]`,
injectable end-to-end (`run_standard_review → run_critic → call = model_fn or
run_isolated_critic`). This amendment generalises the one-off `model_fn` into a
`{role: [model_leg, ...]}` registry.

## 2. Named decisions (builder's call, recorded)

- **D-MRR.1 — registry shape.** A `Role` str-enum (`WRITER`/`CRITIC`/`JUDGE`) + a
  `ModelLeg(name, fn)` dataclass (`fn=None` ⇒ the default isolated Claude spawn) + a
  `ModelRoleRegistry` mapping each role to a **tuple of legs**. A role maps to a *list*
  (not a single leg) because AC.MRR.3 requires "proceeds with remaining legs" and WS-D2
  adds Codex as a *second* critic leg. Dict + resolver only — **NOT** a gateway (no HTTP,
  no proxy, no provider SDK; the §3-row-26/27 verdict stands).
- **D-MRR.2 — default reproduces current behaviour exactly.** `DEFAULT_REGISTRY` maps
  all three roles → one leg `ModelLeg("claude", None)`. `run_critic` is **unchanged** (a
  2-tuple; `test_AC_AR_3:61` unpacks two values — load-bearing). The new multi-leg loop
  lives in a **new** wrapper `run_critic_registry` that *reuses* `run_critic` once per
  leg. When no registry is passed, `run_standard_review` builds the single-default-leg
  registry carrying the caller's `model_fn` ⇒ exactly the pre-amendment 2 calls, byte
  -identical output.
- **D-MRR.3 — leg tagging + render gating.** `Finding` gains `leg: str = ""`.
  `ReviewResult` gains `legs_used: tuple[str,...]` + `missing_legs: tuple[str,...]`,
  sourced **from the run** (which legs produced output vs returned `None`), not from
  post-validation surviving findings. `render_report` emits per-finding leg annotations
  + a missing-leg line **only when a non-default leg NAME appears in
  `legs_used ∪ missing_legs`** (i.e. any name ≠ `"claude"`). The default single-Claude
  path — ran OR unavailable — emits **zero** new bytes (byte-identity). Gating on the
  NAME, not on `bool(missing_legs)`, is deliberate: the default-unavailable path has
  `missing_legs=("claude",)` and must stay identical.
- **D-MRR.4 — writer/judge are data, not code branches.** `WRITER`/`JUDGE` are resolvable
  config vocabulary (the objective names all three roles) but have **no `if role == …`
  call site** in this pipeline — only `CRITIC` is wired (the critic pass). Adding a
  writer/judge dispatch branch would be untested ⇒ an ODD violation; deferred until a
  call site exists (the DEEP merge-judge; WS-D2 wires critic). Tested only for
  resolution.
- **D-MRR.5 — judge-family guidance is docs.** The "judge should not be the writer's
  family, or self-preference re-enters at arbitration" guidance is encoded in the
  `registry.py` module docstring + README — guidance, not a code guard (no AC asserts a
  runtime family check; that would be method-in-AC).

## 3. Fence

Single sealed component: `framework/adversarial-review/`. The sealed
`loam-spawn-isolation` surface is imported/named only (never edited). No SKILL change
(`plugins/loam-skills/` untouched — WS-D1 needs no doc surface). `gate.py` untouched
(inactive by default; no AC touches it). Universal admissions: `docs/plans/`,
`docs/design/`, `CLAUDE.md`, `docs/STATE.md`, `docs/release-roadmap.md`,
`docs/FUTURE_IDEAS_DRAFT.md`.

## 4. Acceptance criteria (AC.MRR family — scope-descriptive)

- **AC.MRR.1 (outcome-altitude) — default config is byte-identical.** With no registry
  configured, a review through the production entry (`review_text`) produces output
  byte-identical to pre-amendment. Proof: (a) a render-golden captured from the current
  tree before any edit (613 bytes, SHA256 `533e4d90…`) equals the post-change render for
  the same fixture; (b) the full pre-existing suite (`test_AC_AR_*` + `test_AR_S` +
  insession) passes unchanged. The default path also tags findings `leg="claude"`
  internally, but the render suppresses the annotation (single default leg).
- **AC.MRR.2 (outcome-altitude) — a non-default leg tags every finding.** With the
  `CRITIC` role configured to a single non-default stub leg (`name="stub-critic"`),
  the critic phases call the stub, every produced `Finding` carries `leg="stub-critic"`,
  and `render_report` surfaces the producing leg's name per finding. Verified through the
  real `review_text` entry at STANDARD **and** DEEP tiers (DEEP forwards the registry).
- **AC.MRR.3 (outcome-altitude) — a configured-but-unavailable leg is named; review
  proceeds.** With `CRITIC` configured to two legs — one available (produces a finding),
  one unavailable (`fn` returns `None`, e.g. the Codex leg absent) — the review proceeds
  on the available leg, every surfaced finding is tagged with its producing leg, and the
  output **names the missing leg**. It is never an unmarked clean bill: the missing leg
  is surfaced; if *all* configured legs are unavailable the verdict is SUSPECT / REVIEW
  INCONCLUSIVE (the existing floor). Also asserts the registry resolves all three named
  roles (`WRITER`/`CRITIC`/`JUDGE`) — the role vocabulary the objective names.
- **AC.MRR.S — seal-fence.** `BASELINE..seal` diff touches only
  `framework/adversarial-review/` + admitted universal paths (verified by the component's
  `test_no_sealed_amendments.py`); no other sealed component's surface moves.

ODD §2.5 map: `registry.py`(`Role`/`ModelLeg`/`ModelRoleRegistry`/`DEFAULT_REGISTRY`) →
AC.MRR.1/2/3; `run_critic_registry` (critic.py) → AC.MRR.2/3; `Finding.leg` (findings.py)
→ AC.MRR.2; `ReviewResult.legs_used/missing_legs` + registry threading (pipeline.py,
tiers.py) → AC.MRR.2/3; `render_report` leg gating (manual.py) → AC.MRR.1/2/3.

## 5. Build steps

1. `registry.py` — `Role`, `ModelLeg`, `ModelRoleRegistry` (with `legs_for(role)`,
   `resolve(role)`, `single_default(model_fn)` classmethod), `DEFAULT_REGISTRY`,
   `DEFAULT_LEG_NAME = "claude"`. Judge-family guidance in the docstring.
2. `findings.py` — add `leg: str = ""` to `Finding` (additive; `score`/`calibrate` match
   on location/scenario text, not object identity — safe).
3. `critic.py` — `parse_findings(..., leg="")` sets the field; add
   `run_critic_registry(inputs, *, axis, registry)` looping legs via the unchanged
   `run_critic`, tagging findings, returning `(findings, ran, missing_legs)`. Leave
   `run_critic` a 2-tuple.
4. `pipeline.py` — `ReviewResult` gains `legs_used`/`missing_legs` (defaults `()`);
   `run_standard_review(..., registry=None)` builds the single-default-leg registry when
   `registry is None`, calls `run_critic_registry`, populates the new fields.
5. `tiers.py` — thread `registry` through `run_deep_review`; aggregate axis
   `legs_used`/`missing_legs` (union) onto the DEEP `ReviewResult`.
6. `manual.py` — `review_text`/`review_file` gain `registry=None`; `render_report`
   emits leg annotations + missing-leg naming only when a non-default leg name is present.
7. `__init__.py` — export `Role`, `ModelLeg`, `ModelRoleRegistry`, `DEFAULT_REGISTRY`.
8. README — a "Model-role registry" section (mechanism + judge-family guidance + WS-D2
   forward pointer).
9. Tests: `test_AC_MRR_1_default_byte_identical.py`,
   `test_AC_MRR_2_nondefault_leg_tags_findings.py`,
   `test_AC_MRR_3_unavailable_leg_named_proceeds.py`. All hit `review_text`.
10. Run touched suite; commit `feat(adversarial-review):`; `loam amend validate`; then
    `loam amend apply` + `loam amend seal`; §14/STATE backfill.

## 6. Halt triggers

- Guard-sweep at seal trips on a **pre-existing** red fence test from a sibling build →
  halt-and-surface (not mine to fix).
- The concurrent shared-dir race corrupts the worktree → halt.
- Any AC would ship partial → halt, name the gap.
- Out-of-fence drift discovered mid-edit → halt.

## 7. Owner ratification

WS-D1 is pre-ratified in BACKPLANE-PLAN §5 (dispatched to build exactly to its ACs). No
new owner decision surfaced. D2 (Codex auth) is WS-D2's concern, not WS-D1's.
