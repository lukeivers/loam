# adversarial-review — loam's standing adversarial-review capability

A genuinely harsh, evidence-bound adversarial review for every produced artifact that
crosses a consequence boundary. Built to defeat the ways AI review goes soft
(sycophancy, agreement bias, self-preference, generic critique, hallucinated flaws,
panel consensus-collapse, performed harshness) **structurally** — by how the review is
constructed — never behaviorally by telling a model to "be brutal".

**Status: v1, ready but INACTIVE.** The automatic/blocking gate ships dormant behind an
explicit activation switch (default OFF, owner-gated — same discipline as loam's
frame-kernel activation). The **manual on-demand** path is the usable surface today.

## The two entry points

### 1. Manual, on-demand (usable now — no gate, no blocking)

Point it at ONE artifact + its stated objective, get the full harsh review back:

```bash
# The package is not pip-installed; run it in place with PYTHONPATH=src.
cd /Users/lukeivers/loam/framework/adversarial-review
PYTHONPATH=src /Users/lukeivers/loam/.venv/bin/python -m adversarial_review \
    /abs/path/to/artifact.md \
    --objective "what this artifact is supposed to accomplish"
# DEEP tier (parallel per-axis critics + merge judge) for high-stakes artifacts:
PYTHONPATH=src /Users/lukeivers/loam/.venv/bin/python -m adversarial_review \
    /abs/path/to/proposal.md --objective "..." --deep
```

(Any Python 3.9+ works — the engine is stdlib-only and reaches the sealed spawn
surface by absolute path; the loam venv is used above because it is known-present.)

**Running from INSIDE a Claude session? Use the in-session backend instead.**
The one-shot command above spawns its critic legs as nested `claude` print-mode
subprocesses, which HANG when driven from an interactive session (interactive-slot
contention) — the review then fail-softs to `REVIEW INCONCLUSIVE` with no findings.
The in-session backend routes around the subprocess: the calling agent supplies each
critic phase from a FRESH isolated subagent (a clean, artifact-blind context), so the
two-phase falsification guarantee holds and no subprocess is spawned. It is a three-step
handshake (`insession derive` → dispatch a fresh subagent → `insession diff` → dispatch a
fresh subagent → `insession finalize`); the `adversarial-review` SKILL drives it. The
default one-shot command is correct only when NOT run interactively (e.g. from a
background/dispatched agent, where the subprocess returns fine — as the calibration run
confirms).

Library:

```python
from adversarial_review import review_file, render_report
result = review_file("proposal.md", objective="...", tier="DEEP")
print(render_report(result, "proposal.md"))
```

### 2. The boundary gate (built, INACTIVE)

`adversarial_review.gate.gate_review(...)` fires at a consequence boundary and blocks on
a BLOCK verdict — but is a **no-op while the activation switch is OFF** (the default). It
never blocks a real ship/seal/send until an owner explicitly activates it. Activation
wiring (hooks on seal/send) is a separate owner step.

## How it defeats soft review (the pins → the modules)

| Pin | Guarantee | Module |
|-----|-----------|--------|
| P1  | Isolation seed = artifact + objective + methodology + protocol ONLY; author's world excluded | `seed.py` |
| P2  | Derivation BEFORE reading — two separate isolated spawns; the derive phase is artifact-blind | `seed.py`, `critic.py` |
| P3  | Validation before surfacing — ground-truth re-check; unvalidated findings quarantined, non-blocking | `validation.py` |
| P4  | Verdict blocks by default; owner override is an explicit, recorded act | `verdict.py`, `gate.py` |
| P5  | A PASS names its strongest surviving objection + what it couldn't check; zero findings on a nontrivial artifact ⇒ suspect the review | `verdict.py` |
| P6  | Domain methodology is KEPT + indexed + reused; corpus checked before any pull | `corpus.py` |
| P7  | DEEP-tier critics never share context; a separate merge judge preserves disagreement | `tiers.py` |
| P8  | Seeded-flaw calibration — the reviewer measures its own catch rate | `calibration.py` |
| P9  | Every spawn routes through loam's sealed `spawn_isolated_claude` (no telegram-kill vector) | `spawn.py` |
| P10 | Internal QA lens only — never a prediction of a real stakeholder's reaction | `critic.py` |

Anti-sham floor (non-negotiable): zero-findings suspicion + named-residual-risk on every
PASS + seeded-flaw calibration. A review that cannot prove it is genuinely harsh is the
core failure mode this capability exists to prevent.

## Depth tiers

- **STANDARD** (floor, non-skippable): one two-phase falsification critic + validation +
  verdict.
- **DEEP** (high-stakes): parallel per-axis isolated critics (no shared context) + a
  separate merge judge that preserves disagreement. Symmetric free-form panel debate is
  never the mechanism.

## Model-role registry (writer / critic / judge → named model legs)

The critic model is injectable, and a `{role: [model_leg]}` registry (`registry.py`)
makes every role's backend a **config entry, not a code change**. Each of `Role.WRITER`,
`Role.CRITIC`, `Role.JUDGE` resolves to an ordered tuple of `ModelLeg(name, fn)` (a
`fn=None` leg is the default isolated Claude spawn). It is a dict + resolver — **not a
gateway** (no HTTP, no proxy, no provider SDK).

```python
from adversarial_review import ModelLeg, ModelRoleRegistry, Role, review_text

# Point the critic at a second model family alongside Claude (WS-D2 lands the
# Codex leg as the first non-default entry). A leg whose fn returns None is
# treated as unavailable: the review proceeds on the remaining legs and NAMES
# the missing one — never an unmarked clean bill.
reg = ModelRoleRegistry(legs={Role.CRITIC: (ModelLeg("claude"), ModelLeg("codex", codex_fn))})
result = review_text(artifact, objective, registry=reg)
# result.legs_used / result.missing_legs carry the provenance; every finding
# is tagged with its producing leg, and render_report surfaces it.
```

- **Default is byte-identical.** With no registry (or `DEFAULT_REGISTRY`, all roles →
  `claude`), a review is unchanged from before the seam existed; the per-finding leg
  annotation only renders when a non-default leg is present.
- **Judge-role guidance:** when a JUDGE leg is wired (a future arbitration / merge-judge
  step), it should **not** be the writer's model family — a same-family judge re-imports
  model self-preference at arbitration. Cross-family judging is the de-correlation the
  multi-model design exists for. Only `CRITIC` has a live call site today; `WRITER` /
  `JUDGE` are resolvable config vocabulary for when theirs exist.

## Composition (does not duplicate existing loam machinery)

- `loam-reviewer` stays the conformance gate; this checks *survivability*, a different axis.
- The critic (`persona/adversarial-critic.md`) generalizes `loam-external-reviewer`'s core.
- Isolation reuses the sealed `spawn_isolated_claude` path — no new spawn machinery.
- The corpus seeds from the two kept, cited methodology docs; `document-trust-review`
  is the document-domain instance of this same stage.

## Tests

```bash
python -m pytest tests/ -q          # deterministic, offline (model leg stubbed)
```

The seeded-flaw calibration real-run (opt-in, makes real isolated `claude -p` spawns):

```bash
AR_REAL_CALIBRATION=1 python -m pytest tests/test_AR_S_real_calibration_smoke.py -q -s
```

## Build home + status

Built pos3-local + unsealed (v1 is INACTIVE, staged, first-under-new-doctrine — sealing
an evolving surface is premature). It composes on the sealed loam surfaces cross-repo via
their documented reach. Migration to canonical loam + sealing is the activation step.

**Staged (follow-up):** structured opposing-sides-debate escalation; automated
research-pull-and-keep for a brand-new domain (the corpus keep/reuse interface ships; the
live WebSearch/WebFetch pull is a seam); live boundary-hook wiring + the calibration
cadence scheduler (both are activation, owner-gated).
