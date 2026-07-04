---
name: adversarial-review
description: >-
  Run a genuinely harsh, evidence-bound adversarial review of an artifact and
  hand the findings back in plain English. Invoke whenever the owner asks to
  "do an adversarial review of <x>", "tear this apart", "red-team this", "poke
  holes in this", "review this hard before it goes out", "how would a hostile
  reviewer break this", or any request to stress-test a document / plan /
  proposal / piece of code for survivability against a skeptical reader. The
  <x> can be a file path, pasted text, or a named artifact the session must
  locate. This SKILL WRAPS the existing adversarial-review tool at
  framework/adversarial-review — it does NOT re-implement review
  logic. Do NOT use for routine copy-editing (that is document-trust-review's
  lighter document pass), for conformance/gate review of a sealed loam
  amendment (loam-reviewer), or for visual UI QA (visual-qa).
---

# adversarial-review

Point loam's standing adversarial-review capability at ONE artifact plus what
it is supposed to accomplish, and return the harsh review in plain language.
The owner says WHAT to review; this SKILL owns the HOW (paths, flags, the run
command) and translates the raw tool output into findings a person can act on.

The tool already exists and is stdlib-only. This SKILL is the invocation
wrapper — never rebuild the reviewer.

## When this fires

Any owner request to stress-test / red-team / tear apart / poke holes in / hard-
review a concrete artifact. Trigger examples:

- "do an adversarial review of this proposal"
- "red-team my plan doc at <path>"
- "tear this apart before I send it" (with pasted text or a file)
- "how would a hostile reviewer break this argument"
- "poke holes in <named artifact>"

## The three input shapes — resolve to ONE file first

The reviewer takes a single file path. Resolve whatever the owner gave you into
one absolute path before running:

1. **A file path** (absolute or relative) — use it directly. If relative,
   resolve it against the session's working directory; confirm it exists.
2. **Pasted text** — the owner pasted the content into the message instead of
   a path. Save the paste verbatim to a temp file FIRST, then review that file.
   Use the scratch path:
   `workspace/.scratch/claude-output/adversarial-review-input-<short-slug>.md`
   (create the dir if missing). Review the saved file.
3. **A named artifact** ("the Alan proposal", "yesterday's plan doc") — locate
   it (Glob/Grep by the name + likely dirs such as `workspace/strategy/`,
   `docs/plans/`, `workspace/products/`). If exactly one clear match, use it.
   If several plausible matches, ask ONCE which one (numbered list), then run.

## Infer the objective — ask at most ONCE

The reviewer needs `--objective "<what the artifact is supposed to accomplish>"`.
Infer it from context: the artifact's own title/intro, the surrounding
conversation, or what the owner said when asking. A wrong objective produces a
weak review, so make it specific ("win Alan as a paying design partner", not
"a business doc"). Only if the objective is genuinely unclear AND cannot be
inferred, ask ONE short question. Otherwise proceed on the inferred objective
and state the objective you used in your reply so the owner can correct it.

## Depth tier

- Default to **STANDARD** (the non-skippable floor: one two-phase falsification
  critic + validation + verdict).
- Use **`--deep`** for high-stakes artifacts — anything going to a real
  external stakeholder (a proposal to a partner/investor, a public post, a
  legal/financial/medical document, an irreversible ship). DEEP runs parallel
  per-axis isolated critics + a separate merge judge that preserves
  disagreement. When in doubt on a consequence-crossing artifact, prefer
  `--deep`.

## Run it — pick the backend by WHERE you are running

The package is not pip-installed — run it in place with `PYTHONPATH=src`. The
engine is stdlib-only; the loam venv is used because it is known-present (any
Python 3.9+ works). All commands assume:

```bash
cd /Users/lukeivers/loam/framework/adversarial-review
```

There are two backends. **Which one you use is not a style choice — it is
forced by where you are running:**

- The default backend spawns its critic legs as nested `claude -p`
  subprocesses. That **HANGS when run from inside an interactive Claude
  session** (interactive-slot contention) — and a SKILL invocation is exactly
  that case. Do NOT use it in-session.
- The **in-session backend** runs the critic legs as FRESH Task subagents you
  dispatch yourself. No nested subprocess, so no hang. **This is the path you
  use when the owner triggers this SKILL.**

### In-session (DEFAULT for this SKILL) — the derive→diff→finalize handshake

Run STANDARD tier as a three-step handshake. Between the steps you dispatch a
FRESH subagent (the Task tool, `general-purpose`) as each critic leg. Using a
fresh subagent per leg is LOAD-BEARING: you (the calling agent) have already
read the artifact to invoke this review, so your own context is NOT
artifact-blind. The derive leg MUST run in a clean context that has never seen
the artifact, or the two-phase falsification guarantee is silently defeated.
Never answer the derive/diff prompts yourself — always dispatch a fresh subagent.

1. **Emit the artifact-blind derive prompt:**

   ```bash
   PYTHONPATH=src /Users/lukeivers/loam/.venv/bin/python -m adversarial_review \
       insession derive --objective "<inferred objective>"
   ```

   Dispatch a FRESH `general-purpose` subagent whose task is EXACTLY the printed
   prompt (do not add the artifact — the blindness is the point). Save its final
   message verbatim to a file, e.g. `workspace/.scratch/claude-output/ar-derived.txt`.

2. **Emit the diff prompt (derivation + artifact):**

   ```bash
   PYTHONPATH=src /Users/lukeivers/loam/.venv/bin/python -m adversarial_review \
       insession diff --objective "<...>" \
       --artifact "<ABS_PATH_TO_ARTIFACT>" \
       --derived-file workspace/.scratch/claude-output/ar-derived.txt
   ```

   Dispatch ANOTHER FRESH `general-purpose` subagent whose task is EXACTLY the
   printed prompt. Save its final message verbatim to
   `workspace/.scratch/claude-output/ar-diffraw.txt`.

3. **Finalize — the real pipeline (parse → validate → verdict → render):**

   ```bash
   PYTHONPATH=src /Users/lukeivers/loam/.venv/bin/python -m adversarial_review \
       insession finalize --objective "<...>" \
       --artifact "<ABS_PATH_TO_ARTIFACT>" \
       --derived-file workspace/.scratch/claude-output/ar-derived.txt \
       --diff-raw-file workspace/.scratch/claude-output/ar-diffraw.txt
   ```

   This prints the structured review. No nested `claude -p` runs — all the
   validation/verdict/lint/zero-findings-suspicion logic is preserved; only the
   model legs came from your fresh subagents.

### Background / out-of-session, and DEEP tier — the subprocess backend

The default one-shot command works fine when NOT run from an interactive
session (e.g. dispatched to a background agent). For a high-stakes artifact
that needs `--deep` (parallel per-axis critics + merge judge), **dispatch a
background agent** to run it — do not run `--deep` in-session:

```bash
# Run from a BACKGROUND agent, never in the interactive session:
PYTHONPATH=src /Users/lukeivers/loam/.venv/bin/python -m adversarial_review \
    "<ABS_PATH_TO_ARTIFACT>" --objective "<...>" [--deep]
```

Notes:
- If the in-session handshake's `finalize` prints `REVIEW INCONCLUSIVE`, a
  fresh subagent leg returned nothing usable — re-dispatch that leg; do NOT
  grind a hand-written review in-thread.
- If you ever see a nested-spawn hang, you are on the wrong backend for
  in-session — switch to the handshake above.

## Translate the output — findings in plain English

The tool emits a structured report (verdict + findings + validated/quarantined
split + named residual risk). Do NOT dump the raw report at the owner. Per loam
doctrine, translate:

- Lead with the verdict in plain words: does this survive a hostile read, or
  does it need work — and the single most important reason.
- List the findings that survived validation, each as: what's wrong, why it
  matters for the stated objective, and what would fix it. Plain sentences, not
  the tool's internal axis labels.
- State the review's own honesty markers the tool guarantees: the strongest
  surviving objection even on a PASS, and what the review could NOT check
  (its named residual risk). A "zero findings" result on a nontrivial artifact
  is itself suspicious — say so if it happens.
- Keep quarantined/unvalidated findings clearly separate (flagged as "not
  confirmed") so the owner does not act on an unverified flaw.
- If the full report is long, write it to
  `workspace/.scratch/claude-output/adversarial-review-<slug>.md` and give the
  owner a short plain-English summary plus the path (per the output convention).

## Graceful degradation

Without loam's adversarial-review capability installed (a stranger running
raw Claude Code, or a workspace where `framework/adversarial-review/` is
absent), the fallback is a hand-driven review: ask a FRESH Claude context —
one that has not seen the artifact or your reasoning — to attack the
artifact against its stated objective ("this shipped and failed;
reconstruct why"), then re-check each claimed flaw against the artifact
before you act on it. This preserves the two guarantees that matter most —
an artifact-blind critic and validation before a finding blocks — but it
does NOT enforce them structurally: the isolation, the two-spawn
derivation, the quarantine of unvalidated findings, the zero-findings
suspicion, and the seeded-flaw calibration are all on you rather than the
tool. Treat the raw-Claude result as advisory, never as a measured harsh
review.

## What this SKILL is NOT

- Not a rebuild of the reviewer — it wraps `framework/adversarial-review`.
- Not the document copy/trust pass — that is `document-trust-review` (lighter,
  document-domain). This is the survivability axis (would a hostile reviewer
  break it).
- Not the loam sealed-amendment conformance gate — that is `loam-reviewer`.
- Not visual UI QA — that is `visual-qa`.
