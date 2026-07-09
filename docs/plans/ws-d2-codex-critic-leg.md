# WS-D2 — Codex adversarial-critic leg + calibration (adversarial-review, SEALED amend)

**Slug:** `ws-d2-codex-critic-leg`
**Working directory (build):** `/Users/lukeivers/loam-ws-d2-wt` (isolated worktree of
`/Users/lukeivers/loam`, branch `feat/ws-d2-codex-critic-leg`, base `a4c08928` — the
WS-D1 seal).
**Component:** `framework/adversarial-review/` — **SEALED**. Full `loam amend` cycle
(apply + seal), never free edits, never `git commit --amend`.
**Source:** `workspace/strategy/ai-shop-backplane/BACKPLANE-PLAN.md` §5 WS-D2.
**Depends on:** WS-D1 (model-role registry, seal `a4c08928`). This leg is the registry's
first non-default entry.
**Model:** Sonnet (well-specified build, not an open design problem).
**model-rationale (codex leg):** `codex — different model family de-correlates reviewer
blind spots vs a same-family critic` (the objective's own rationale; not an Opus dispatch).

## 0. Why an isolated worktree (build-method note, not a scope change)

Same reasoning as WS-D1 §0: the shared canonical dir `/Users/lukeivers/loam` cycles
branches under concurrent sibling backplane builds (WS-A1/A2/A3/B1) with untracked
spillover — the live `feedback_serialize_amendment_builds` hazard. WS-D2 builds in its
own worktree off the WS-D1 seal (`a4c08928`), the **narrowest** `BASELINE..seal` fence
window that still contains the registry this leg extends. Basing off `main` (`c53458da`)
instead would swallow WS-D1's three commits into the diff window; basing off WS-D1's seal
keeps the window to WS-D2's own delta.

## 1. Objective

The adversarial-review pipeline can run a **second critic leg on a different model
family** (OpenAI Codex), running in **parallel** with the default Claude critic
(author=Claude / adversary=Codex — error de-correlation across families), and it
**demonstrably catches a planted defect**. The leg **fails soft**: `codex` absent or auth
dead ⇒ the leg returns `None`, the review proceeds Claude-only with the leg **named
missing**, never a false clean bill. Every finding is tagged with its producing model
(Lens 0: expose the substance — the review says which model found which flaw).

The seam is WS-D1's registry: the `CRITIC` role resolves to an ordered tuple of
`ModelLeg`s, and `run_critic_registry` already runs the unchanged two-phase `run_critic`
once per leg, tagging each finding with the leg name and naming any leg that returned
`None`. WS-D2 adds one new `ModelLeg("codex", run_codex_critic)` and a factory that puts
`(claude, codex)` on the `CRITIC` role. No pipeline rewrite: the leg is data.

## 2. Named decisions (builder's call, recorded)

- **D-CDX.1 — the leg is a plain text `ModelFn`, routed through the UNCHANGED two-phase
  `run_critic`.** `run_codex_critic(prompt) -> str | None` slots into WS-D1's
  `run_critic_registry`, which calls it for BOTH the DERIVE phase (free-form spec) and the
  DIFF phase (`FINDING…END` blocks). Reuses the sealed critic primitive rather than
  re-implementing a parallel single-phase codex pass (ODD: compose, do not re-roll).

- **D-CDX.2 — DROP `--output-schema` from the codex argv (deviation from the plan's
  literal hint, named per F2).** The §5 WS-D2 constraint text says shell `codex exec
  --json --output-schema <findings-schema> --sandbox read-only`. A fixed findings schema
  is **incompatible** with D-CDX.1: the same `ModelFn` serves both the DERIVE phase (must
  emit a free-form spec, NOT findings) and the DIFF phase, and a `ModelFn` cannot know
  which phase it is in. Forcing a findings schema would break DERIVE. No AC binds the
  schema (all three ACs are satisfiable via the existing `FINDING…END` text parse in
  `parse_findings`). Resolution: keep `--sandbox read-only` (required — a critic reads,
  never mutates) and `--json` (parseable event stream), and extract the model text
  tolerantly with a raw-stdout fallback (`spawn.py:_unwrap_json` is the model). The
  downstream `parse_findings` regex is format-agnostic, which is what makes the leg robust
  to whatever `codex` actually emits.

- **D-CDX.3 — env scrub by DELETION, not whitelist (AC.CDX.3).** The codex child env is
  `dict(os.environ)` with the sensitive keys **removed** (`OPENAI_API_KEY` per D2,
  `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` — a non-claude subprocess has no business
  with them). Deletion (not a minimal whitelist) because D2's ratified auth is **ChatGPT
  sign-in**, which is **file-based** (`~/.codex/…`): the child still needs `HOME`/`PATH`
  to find that credential. Whitelisting a minimal env would break sign-in. A
  `allow_openai_key=True` escape hatch relaxes the `OPENAI_API_KEY` scrub for THIS
  subprocess only (D2's "if the metered-key variant is ever enabled" clause), never
  globally — default is `False` (sign-in only).

- **D-CDX.4 — the leg is a LIBRARY factory, not a new CLI flag (scope boundary).**
  `codex_critic_registry()` (operator constructs it) + the existing `registry=` param on
  `review_text` / `calibrate` IS the operator trigger (D2: operator-triggered only). No
  `--with-codex` CLI flag is added: no AC names one, and an unnamed CLI branch would be
  non-objective code (ODD §2.5). The library API fully delivers "the pipeline CAN run the
  leg."

- **D-CDX.5 — live-codex proof is owner-gated; the deterministic outcome-altitude proof
  stubs the process boundary.** `codex` is not installed in the build environment (the
  plan's own dependency line gates install on the owner, ~5 min, + D2 sign-in). This
  MIRRORS the sealed component's existing calibration posture EXACTLY: AC.AR.10 ships a
  deterministic injected-boundary test as its outcome-altitude proof, and gates the
  real-model run behind an opt-in skip (`test_AR_S_real_calibration_smoke`,
  `AR_REAL_CALIBRATION=1`). WS-D2 does the same: AC.CDX.1 patches `codex.py`'s **lowest
  process boundary** (`subprocess.run` + `shutil.which`) so the REAL argv-build, env-scrub,
  and text-extraction execute and only the actual `codex` process output is canned; a
  separate opt-in smoke (`AR_REAL_CODEX=1`, skipped when `codex` absent) is the live proof
  the owner runs once signed in. This is NOT an AC downgrade — the leg's wiring, tagging,
  fail-soft, and env-scrub are all verified through the production pipeline; only the
  model-quality claim ("a live codex, given the prompt, emits a finding for the anchor")
  is deferred, and it is a model-quality claim, not an architectural one.

## 3. Fence

Single-component amendment: `framework/adversarial-review/` only (EXISTING sealed
component; the sidecar advances, not a first-seal). Surface touched:

- **NEW** `src/adversarial_review/codex.py` — the leg + env-scrub + registry factory.
- **EDIT** `src/adversarial_review/calibration.py` — add a `registry=` param threaded to
  `review_text` (default `None` ⇒ unchanged behaviour). One additive kwarg.
- **NEW** `tests/test_AC_CDX_1_codex_leg_calibration.py`,
  `tests/test_AC_CDX_2_codex_absent_fail_soft.py`,
  `tests/test_AC_CDX_3_codex_env_scrub.py`,
  `tests/test_AR_S_real_codex_smoke.py` (opt-in).
- **DOC** this plan-doc + the manifest under `docs/plans/`.

Composed-on but NOT edited: the sealed `loam-spawn-isolation` surface (the codex leg is a
DIFFERENT binary spawned directly — it reaches nothing sealed, so no `loam_spawn_isolation`
import; the dispatch's "reuse `probe_liveness()` / copy the `__file__` sys.path pattern"
note is **inapplicable** to WS-D2, those are fleet/lease boilerplate). `critic.py`,
`registry.py`, `pipeline.py`, `manual.py`, `gate.py`, `spawn.py` — UNCHANGED. The
`plugins/loam-skills/` SKILL partner — UNCHANGED. `.claude/settings.json` — UNTOUCHED (no
hook; single-writer resource owned by Track F).

## 4. Acceptance criteria

- **AC.CDX.1 (outcome-altitude)** — n=1 calibration: a seeded-flaw artifact run through
  the Codex leg via the production pipeline (`calibrate(... registry=codex_registry)` and
  `review_text(... registry=codex_registry)`) surfaces the planted defect, tagged
  `leg="codex"`, and `calibrate` reads back a nonzero catch rate. Deterministic: only the
  `codex` process boundary (`subprocess.run` + `shutil.which`) is stubbed; the real
  argv-build, env-scrub, `--json` extraction, `parse_findings`, and calibration scoring
  all execute.
- **AC.CDX.2** — with `codex` uninstalled (`shutil.which` → `None`, the real fail-soft
  path), a review whose `CRITIC` role is `(claude, codex)` completes on the claude leg and
  the rendered output NAMES the missing `codex` leg (`missing_legs == ("codex",)`); never
  an unmarked clean bill.
- **AC.CDX.3** — the leg's subprocess env (the `env=` actually handed to `subprocess.run`)
  contains no `OPENAI_API_KEY` and no `ANTHROPIC_API_KEY` under the default (sign-in) auth,
  while `HOME`/`PATH` survive; `allow_openai_key=True` relaxes the `OPENAI_API_KEY` scrub
  for that subprocess only.
- **Regression** — the full pre-existing `AC.AR.{1-13}` + `AC.MRR.{1-3}` + `AR.S` suite
  passes unchanged (the sealed default path is byte-identical; the added `calibrate`
  kwarg defaults to `None`).

Traceability: AC.CDX.1 → `codex.run_codex_critic` + `codex_critic_registry` +
`calibration.calibrate(registry=)`; AC.CDX.2 → `codex.run_codex_critic` `shutil.which`
fail-soft + WS-D1's `run_critic_registry` missing-leg naming + `render_report`; AC.CDX.3 →
`codex.codex_env`.

## 5. Build steps

1. Write this plan-doc + manifest (plan-before-code). ✔
2. `codex.py`: `codex_env`, `build_codex_argv`, `_extract_text`, `run_codex_critic`,
   `codex_leg`, `codex_critic_registry`, module constants.
3. `calibration.py`: add `registry` kwarg, thread to `review_text`.
4. Tests AC.CDX.1/2/3 + the opt-in real-codex smoke.
5. Run the component suite (touched + full sweep). Fix to green; never loosen a test.
6. Commit source as `feat(adversarial-review): …` BEFORE `loam amend apply` (apply runs
   against committed HEAD).
7. `loam amend validate` → `loam amend apply` → `loam amend seal`.
8. Backfill STATE + roadmap + this plan's SHA register.

## 6. Halt triggers (in-flight)

- WD drift from `/Users/lukeivers/loam-ws-d2-wt`.
- Out-of-fence drift discovered mid-edit (any sealed surface outside
  `framework/adversarial-review/` moves).
- The seal-test fails for a reason unrelated to this cycle's edits (a pre-existing fence
  breach surfaced by the build).
- A design need for a `.claude/settings.json` hook (single-writer resource, Track F) —
  HALT, do not touch it.
- An AC that cannot be met through the production pipeline (would force a `-lite`
  downgrade) — HALT + surface, never ship a weaker variant.

## 7. ODD §2.5 map (every symbol → a named AC)

- `codex.codex_env` → AC.CDX.3 (env scrub).
- `codex.build_codex_argv` → AC.CDX.1 (the read-only codex argv the leg spawns).
- `codex._extract_text` → AC.CDX.1 (tolerant `--json`/raw text extraction feeding
  `parse_findings`).
- `codex.run_codex_critic` → AC.CDX.1 (the `ModelFn` that catches the defect) + AC.CDX.2
  (fail-soft `None` when `codex` absent) + AC.CDX.3 (spawns with the scrubbed env).
- `codex.codex_leg` / `codex.codex_critic_registry` → AC.CDX.1/2 (the `(claude, codex)`
  parallel-critic registry — the registry's first non-default entry).
- `calibration.calibrate(registry=)` → AC.CDX.1 (calibration through the codex leg).
- `test_AR_S_real_codex_smoke` → the owner-gated live proof (D-CDX.5), opt-in / skipped.
