# workspace-sync — A.2: LLM-as-classifier + deterministic-merge + LLM-as-verifier — plan

Sealed-component amendment extending `framework/workspace-sync/`.
Replaces the LLM-as-generator pattern inside `MergeResolver.resolve()`
with a four-stage flow: classify → deterministic-merge → verify →
accept-or-fallback. The LLM-as-generator path remains as the
verify-fail / classifier-says-no fallback.

**Status:** plan (pre-dispatch). 2026-05-21.
**Working directory:** `/Users/lukeivers/loam/`
**Companions:**
- **FUTURE_IDEAS_DRAFT.md Bundle A.2 (QQ-refined)** — the design seed.
- **`framework/workspace-sync/src/loam/workspace_sync/merge_resolver.py`** — the class whose `.resolve()` body is rewritten.
- **`framework/workspace-sync/src/loam/workspace_sync/_resolver_client.py`** — kept untouched (subprocess-spawn isolation lives here).
- **`framework/workspace-sync/tests/test_merge_resolver.py`** — existing tests that MUST keep passing.

---

## 1. Summary / TLDR

`MergeResolver.resolve()` currently sends the full file (canonical
text + workspace text + prior text) to the LLM and expects a
`MergeVerdict` carrying full merged content. That call costs
60-120s wall-clock per file because the LLM regenerates the entire
merged body.

The replacement keeps the same external API (still returns
`MergeVerdict` with `resolution`/`merged_content`/`rationale`/
`confidence`) but rewires the body:

1. **Classifier call** (~50-token output). Asks: "is this
   structurally-mergeable by a deterministic primitive?" Returns
   `(mergeable: bool, strategy: 'text-3way' | 'yaml-key-merge' |
   'append-only' | 'none', reason: str)`.

2. **Deterministic merge** (free, no LLM). When the classifier
   says yes, dispatch to one of the three primitives:
   - `text-3way` — `git merge-file` against `prior_text` as base.
   - `yaml-key-merge` — for YAML config files: parse each side,
     three-way-merge keys (canonical-wins on overlap by default,
     workspace-wins for workspace-only keys).
   - `append-only` — for changelog-shaped files: detect common
     prefix, append the union of unique tail lines preserving
     order.

3. **Verifier call** (~200-token output). Asks: "did the
   deterministic merge lose meaning relative to the source content?"
   Returns `(verified: bool, concerns: list[str])`.

4. **Decision.**
   - Classifier-says-no OR verifier-says-fail → fall back to the
     existing LLM-as-generator path (preserved verbatim).
   - Verifier-pass → return a `MergeVerdict` with
     `resolution='inferred-merged'`, the deterministic merge's
     output, a rationale describing the classifier strategy +
     verifier confirmation.

External callers see no change.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

This composes under **VALUE_PROPOSITION's AC.PO.1
(translation-burden absorption)**. The operator says "pull the
latest"; today the persona translates that to `pos-sync`, which
on conflict spends 60-120s/file in LLM-as-generator. The cost
deters operator use. Post-A.2: 3-8× faster on the
classifier-mergeable cases, with a safety-net verifier on every
deterministic output. No new top-level objective.

---

## 3. Three-lens analysis

### Lens 1 — Claude leverage
Uses the existing `_ClaudePrintResolverClient` (claude -p
subprocess) for classifier + verifier calls. No new Claude
primitive; smarter use of the existing one (smaller prompts,
smaller outputs, more targeted questions).

### Lens 2 — Harness + primary-persona value
Translation burden: pre-A.2, the persona must explain that
sync "may take 5-10 minutes on conflict-heavy syncs"; post-A.2,
that wall-clock drops to under a minute on most cases. Harness
test: adds three deterministic-merge primitives the persona
can also reach for outside the resolver (text-3way, yaml-key,
append-only) — toolkit grows.

### Lens 3 — ODD
Five ACs (AC.LMV.1 through .5). Every line of new code maps
to one. The classifier prompt + verifier prompt + each
deterministic primitive + the orchestration in `.resolve()`
each tie to a named AC.

### Lens 4 — Prompt scope ↔ confidence
High confidence on the shape (classifier → primitive → verifier
→ fallback); the plan is tight on what + constraints, but
leaves builder method discretion on prompt wording and primitive
internals. The fallback is preserved exactly so the worst case
is no regression.

### Lens 5 — Swarming
Not applicable — single sealed-component amendment, no
decomposition into subtasks.

### Lens 6 — Conflict resolution
No principle conflict surfaced. ODD §2.5 + locked external API
both honored.

### Lens 7 — Ruthless feedback (T1)
Surface to dispatcher: the dispatch brief's AC.LMV list says
"deterministic merge primitives produce correct output on
synthetic three-way merge cases" — that's three primitives, not
one. The plan adopts three (text-3way, yaml-key-merge,
append-only) per the brief's explicit list.

---

## 4. ACs

- **AC.LMV.1** — classifier returns the expected verdict on at
  least three representative file shapes (a YAML config, a
  changelog-shaped file, a Python source file).
- **AC.LMV.2** — each of the three deterministic merge primitives
  produces correct output on synthetic three-way merge cases.
- **AC.LMV.3** — verifier catches a synthetic known-corrupt merge
  output (e.g., a merge that drops a section).
- **AC.LMV.4** — full pipeline integration test: a representative
  case runs classify → merge → verify → accept and returns a
  well-formed `MergeVerdict`.
- **AC.LMV.5** — fallback to LLM-as-generator triggers correctly
  on verify-fail (and is exercised end-to-end via a stub client
  that returns verifier-fail).

Outcome-altitude AC: **AC.LMV.4** (full pipeline, production
entry point `MergeResolver.resolve()`, no pre-arranged
internal state — only the test's stub LLM client is arranged).

---

## 5. Files modified/added

**Modified:**
- `framework/workspace-sync/src/loam/workspace_sync/merge_resolver.py`
  — adds `ClassifierVerdict`, `VerifierVerdict`, three
  deterministic-merge functions, classifier-prompt and
  verifier-prompt builders, and a rewritten `.resolve()` body
  that wires the four-stage flow. The existing LLM-as-generator
  call path is preserved verbatim as `_resolve_with_generator`
  (renamed but unchanged in body) and invoked from `.resolve()`
  as the fallback.

**Added:**
- `framework/workspace-sync/tests/test_merge_resolver_classifier_verifier.py`
  — AC.LMV.1 through .5 tests.

**Not touched:**
- `_resolver_client.py` (per dispatch brief out-of-scope).
- `MergeResolver` external API (`.resolve()` signature, return
  type, exceptions).
- Existing `test_merge_resolver.py` tests — they must continue
  to pass; the verdict-shape contracts they cover are preserved.

---

## 6. Method (builder-discretion summary)

- The classifier prompt is small (~5 lines + 1-line file
  preview) and asks for a structured `ClassifierVerdict` Pydantic
  model with `mergeable`, `strategy`, `reason`. The classifier
  receives the file path's extension hint and the first ~500
  chars of each side so it can decide structurally without
  reading the full body.

- Each deterministic primitive is a pure function `(canonical,
  workspace, prior) -> (merged_text, ok: bool)` where `ok=False`
  means the primitive itself bailed (e.g., YAML failed to parse;
  text-3way had unresolvable hunks). On `ok=False`, the
  orchestrator behaves as if the classifier had said no.

- `text-3way` uses `git merge-file --stdout` invoked via
  `subprocess.run`, falling back to `ok=False` when git exits
  with conflicts (returncode > 0 indicates conflict count; we
  treat any > 0 as bail).

- `yaml-key-merge` uses `yaml.safe_load` from PyYAML
  (already a transitive dep; verified below) and a key-level
  three-way merge: keys present in both diffs go canonical;
  workspace-only adds go through; canonical-only deletions
  apply.

- `append-only` finds the longest common prefix of lines
  between canonical and workspace, then emits prefix + union of
  unique tail lines (canonical first, then workspace's unique).

- The verifier is shown the deterministic merge output + a
  one-line summary of what was merged (e.g., "yaml-key-merge
  applied: canonical added keys X, Y; workspace added Z").
  Asks: "Does this output preserve the meaning of both sides?"
  Returns `VerifierVerdict(verified, concerns)`. Threshold for
  acceptance: `verified=True AND concerns is empty or only
  trivial`.

- Token-cost bookkeeping: classifier + verifier calls EACH
  count against the cumulative budget the same way the
  generator call did. Per-conflict budget is still enforced
  pre-flight as today.

---

## 7. Empirical cost comparison (estimate)

**Before (LLM-as-generator only):**
- Wall-clock: ~60-120s/file (full file regenerated).
- Tokens: ~3,000-8,000 in + ~3,000-8,000 out (= 6,000-16,000
  total per call).

**After (classifier + det-merge + verifier):**
- Wall-clock: classifier ~5-10s; det-merge near-instant;
  verifier ~5-15s. Total ~10-25s when classifier says yes
  AND verifier passes (the common case).
- Tokens: classifier ~200 in + ~50 out; verifier ~500 in +
  ~200 out. Total ~950 tokens.
- On classifier-says-no or verifier-fails: classifier (+
  optional verifier) + the original generator call. Worst
  case is generator-cost + ~10s overhead — about 10% slower
  than today's worst case.

**Net (assuming 70% classifier-mergeable + 95% verifier-pass
on those):**
- Wall-clock: 0.665 × ~15s + 0.335 × ~75s = ~35s/file average.
- Vs ~90s/file average today. **~2.6× faster average**,
  3-8× on the common case as the brief estimated.

---

## 8. Halt triggers

- `_ClaudePrintResolverClient` cannot be reached without a real
  `claude` binary → tests use a stub LLM client; production
  path stays unchanged. No new halt.
- PyYAML not on workspace-sync's deps → halt + surface (would
  need a deps amendment). Verified below: `pyyaml` is a
  transitive dep already.
- The deterministic merge of YAML loses key-order on the
  written file → acceptable; verifier catches if it causes
  semantic loss; YAML semantics are key-order-independent.

---

## 9. Tag

Proposed: `workspace-sync-A2-llm-classifier-deterministic-verifier`
or the next-available amendment tag per the dispatcher's
amendment-numbering convention.

---
