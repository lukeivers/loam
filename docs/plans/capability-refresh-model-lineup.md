# Capability-refresh model-lineup extension (sub-plan-doc)

> **Status:** sub-plan-doc (buildable; manifest paired at
> `docs/plans/capability-refresh-model-lineup.manifest.yaml`).
> **WD:** `/Users/lukeivers/loam` (canonical loam).
> **Parent:** `docs/plans/claude-leverage-program-s1-currency.md` (the
> sealed component this amendment extends).
> **Fence:** `framework/tools/capability-refresh/` + universal paths
> (`docs/plans/`, `docs/capability-corpus/`, `docs/STATE.md`,
> `docs/release-roadmap.md`). No fence widening: all paths fall inside
> the existing `allowed_prefixes`/`allowed_files` of the
> `test_no_sealed_amendments.py` at BASELINE `266aa93c`.
> **BASELINE candidate:** `6a57ea488afc1cc428232c4b04c04cc2a7635b43`
> (HEAD at plan authoring, 2026-07-01). Builder confirms at apply.
> **Quality bar:** every AC outcome-shaped; ★ AC.CLP-MDL.2 is the
> outcome-altitude AC; method is the builder's call per ODD §1.1;
> no version numbers pre-assigned.
> **PUBLIC-ACTION NOTE: no public-action steps.** The new sources
> are fetched from Anthropic's public docs but nothing is published.
> Live URL verified at plan-author time (models overview and pricing
> pages both return HTTP 200; models overview at the .md URL returns
> machine-readable Markdown with Claude API IDs in backtick form).

---

## §1 Summary / TL;DR

**The gap:** the capability-refresh tool (claude-leverage-program Slice 1,
sealed `c41f9473`) tracks Claude Code capability docs (hooks / subagents /
changelog / loop / schedule). It never tracked the Claude **model lineup
or pricing**. "Sonnet 5 shipped" (`claude-sonnet-5` — live on
`platform.claude.com/docs/en/about-claude/models/overview.md` at plan
authoring) was never caught by the automated refresh; the owner reported
it manually. This extension closes that gap.

**What ships:**
1. Two new sources in `docs/capability-corpus/sources.yaml`:
   `anthropic-models-overview` (Markdown page with backtick-quoted Claude
   API IDs; `model_parse: true` flag) and `anthropic-pricing` (HTML
   pricing page; standard watch source).
2. A new `models.py` module in the existing component: deterministic
   regex extraction of model IDs from the overview page, per-source
   lineup stored at `.refresh/model-lineup/<id>.json`, delta computation
   (added / removed model IDs vs the prior run), structured delta surfaced
   in `last-run.json` + human-readable stdout.
3. A `model_parse` boolean flag on the `Source` datatype (optional, defaults
   `false`; no existing source is affected). When true: the watch source's
   existing snapshot/diff behavior runs unchanged, AND the model-lineup
   tracking layer runs on top of it.
4. `cadence/routine-spec.md` updated to name the model-data pull + delta
   in the scheduled-run prompt.

**AC families:** AC.CLP-MDL.1–4 (this extension). ★ = AC.CLP-MDL.2
(a prior-lineup-vs-current delta emits the exact real-world miss).

---

## §2 Placement decisions

| Surface | Placement | Rationale |
|---|---|---|
| New model tracking logic | New `models.py` module in the existing `framework/tools/capability-refresh/src/capability_refresh/` package | Peer to existing modules (`fetch.py`, `partition.py`, `corpus.py`). Keeps the component self-contained; no new component needed. |
| `model_parse` flag | Added to the `Source` dataclass in `sources.py`; loaded from sources YAML | Sources are data (D-CUR.3). The flag is method-neutral — how the model page is fetched and parsed is the builder's call. |
| Model-lineup artifact | `.refresh/model-lineup/<source-id>.json` inside the corpus root | Already a valid `resolve_state_path` target (`.refresh` is a `STATE_DIR`). Machine state, not a reference doc. |
| New sources | `docs/capability-corpus/sources.yaml` (two new entries) | Same home as all existing sources. Cadence: `high-velocity` (daily) — model lineup can change without warning. |
| AUTHORING.md | Update the "Refresh machinery" section with model-lineup tracking | In `docs/capability-corpus/`, covered by `universal_paths`. Documents the new `.refresh/model-lineup/` artifact for future maintainers. |

---

## §3 Halt-and-surface BEFORE build

1. **Live URL verification done (2026-07-01):**
   - `https://platform.claude.com/docs/en/about-claude/models/overview.md`
     → HTTP 200, Markdown with IDs including `claude-fable-5`,
     `claude-sonnet-5`, `claude-opus-4-6`, etc. in backtick form.
   - `https://platform.claude.com/docs/en/about-claude/pricing`
     → HTTP 200, HTML (the existing `normalize()` HTML path handles it).
   If either URL goes away mid-build, that is a live halt trigger (§8.1).
2. **No fence widening needed.** All changed paths fall inside the
   existing `allowed_prefixes`/`allowed_files` of the component's
   `test_no_sealed_amendments.py` (BASELINE `266aa93c`). The fence test
   does not need modification.
3. **`model_parse` does not add a new YAML `kind`.** The existing
   `KINDS = ("entry", "watch")` stays stable. `model_parse` is an
   optional boolean field; `watch` sources without it remain unaffected.
   This avoids touching the kind-dispatch logic in `refresh.py`.
4. **Pricing page: no model-ID extraction needed.** The pricing page is
   HTML; the existing `normalize()` HTML path works; its content changes
   surface as review-class pending-deltas via the existing watch mechanism.
   `model_parse: false` (default) on the pricing source.

---

## §4 Spec-objective placement

- **Binds:** AC.CLP.1 ★ (via tighter AC.CLP-MDL.2 — the model-lineup
  delta is the machine that catches a new-model event with no manual
  trigger, which is the same class of failure AC.CLP.1 addresses for
  capability docs).
- **Ladders to:** AC.PO.2 (protection floor — a stale/missing model-lineup
  reference is the "inventing things / no real memory" betrayal class).
- **Lens 1:** the tool already runs on Anthropic's own infrastructure
  (cloud routine, no API key); this extension keeps the same pattern.

---

## §5 Acceptance criteria (`AC.CLP-MDL.*`)

★ = outcome-altitude. Every AC passes the method-in-AC test.

| AC | Outcome | Verification |
|---|---|---|
| AC.CLP-MDL.1 | After a run that includes `model_parse: true` sources, `.refresh/snapshots/<id>.txt` contains the fetched content (Markdown/HTML), AND `.refresh/model-lineup/<id>.json` exists with a non-empty `ids` list. | Fixture run: file:// upstream with `claude-x-y` IDs in backtick form; assert both files exist and `ids` is non-empty. |
| AC.CLP-MDL.2 ★ | Given a prior run with model IDs {claude-opus-4-8, claude-sonnet-4-6} and a current upstream that adds claude-sonnet-5, the tool emits a delta naming claude-sonnet-5 in the `added` list. This is the exact real-world miss. | Two-run fixture: run 1 upstream has {opus-4-8, sonnet-4-6}; run 2 upstream adds sonnet-5; assert last-run.json per-source `model_delta.added == ["claude-sonnet-5"]`. Production path via `run_refresh()`. |
| AC.CLP-MDL.3 | Regression: existing `fixture_repo` (no model_parse sources) produces identical run behavior — no `model_delta` in the report, no `.refresh/model-lineup/` directory created. | Run the existing conftest `fixture_repo` through `run_refresh()`; assert no `model_delta` key in the per-source record and no model-lineup directory. |
| AC.CLP-MDL.4 | `cadence/routine-spec.md` contains text covering model-data pull + delta in the routine prompt. | Read the file; assert the phrase "model" or "model-lineup" appears in both the daily and weekly prompt blocks. |

---

## §6 Build steps (method-level guidance; builder's call per ODD §1.1)

Manifest: `docs/plans/capability-refresh-model-lineup.manifest.yaml`.
`loam amend apply` then `loam amend seal` per the amendment-cycle
convention (named explicitly per `feedback_dispatch_explicit_loam_amend_apply`).

1. **Plan-doc + manifest** (this doc + paired YAML) committed first.
2. **`models.py`**: `extract_model_ids(text)` → deterministic regex over
   raw Markdown; `compute_model_delta(old, new)` → added/removed sets;
   `load_model_lineup` / `save_model_lineup` using `resolve_state_path`
   for containment. No LLM call (D-CUR.4 — hallucination cannot enter).
3. **`sources.py`**: `model_parse: bool = False` on `Source`; `load_sources`
   reads it as optional; validation rejects `model_parse: true` on
   `kind: entry` sources (model-ID extraction is only valid for watch
   sources — entries project into corpus docs, not raw markdown pages).
4. **`refresh.py`**: after `norm = normalize(raw)` for a `model_parse`
   source, call model-tracking logic (raw text, not norm — backtick IDs
   are in the raw Markdown). Write lineup + compute delta. Add
   `model_delta` to the per-source report record (None for non-model_parse).
5. **`cli.py`**: print model delta in human-readable output when non-empty
   (added/removed counts + ID names).
6. **`docs/capability-corpus/sources.yaml`**: add `anthropic-models-overview`
   (model_parse: true, high-velocity) and `anthropic-pricing` (watch,
   high-velocity). Verify URLs live at build (AC halt trigger §8.1).
7. **`cadence/routine-spec.md`**: update the daily + weekly prompt blocks
   to name the model-data pull + delta step.
8. **Tests** (`tests/test_AC_CLP_MDL_1_4_model_lineup.py`): one file,
   parametrize or separate functions per AC. Fixture uses file:// upstreams;
   no live network in tests.
9. Run tests: `pytest framework/tools/capability-refresh/tests/ -v`.
   If any fail, fix before applying — never loosen tests.
10. Commit source + tests (feat commit); clean `git status`.
11. `loam amend validate` (schema lint).
12. `loam amend apply <manifest>`.
13. `loam amend seal <manifest>`.
14. Backfill `docs/STATE.md` + `docs/release-roadmap.md` §8.

---

## §7 Out of scope

1. **Pricing structured extraction** — the pricing page is HTML; structured
   price-per-token extraction would need regex over normalized HTML.
   Not a clear-enough pattern (pricing table markup can vary). Surfaced here
   as a named non-inclusion; the watch-source pending-delta is the signal.
2. **AUTHORING.md model-lineup section** — the AUTHORING.md "Refresh
   machinery" section names the existing `.refresh/` artifacts. Adding a
   mention of `.refresh/model-lineup/` is in-scope (covered by
   `docs/capability-corpus/` prefix) and is the right documentation.
   Included in build step 6 scope.
3. **Auto-update of `workspace/strategy/model-capability-tiers.md`** — the
   dispatch explicitly says "you are NOT auto-editing the registry." The
   delta is the signal; the registry update is owner-directed.
4. **Activation of the cadence** — owner-gated per the existing
   `cadence/ACTIVATION.md` ruling. This amendment updates the SPEC; it
   does not activate.

---

## §8 Halt triggers (in-flight)

1. Either live URL returns an error or non-200 during the build step 6
   live-verify → halt; the tool's whole point is live freshness, not
   hardcoded stale content.
2. The model-overview page's Markdown format changes so that
   backtick-quoted `claude-X` IDs are no longer present → halt + surface;
   the regex extractor would silently return zero IDs, which is a worse
   failure than an explicit halt.
3. An ODD violation is found in the surrounding code during edits → halt
   + surface (do not fix out of fence).
4. `loam amend validate` fails → fix before apply (never proceed with a
   schema error).
5. Any seal-test failure unrelated to this amendment → halt + surface.

---

## §9 Bookkeeping

- `docs/STATE.md` change-log entry at seal.
- `docs/release-roadmap.md` §8 register row.

---

## §10 Named decisions

**D-MDL.1 — `model_parse` as boolean flag vs new `kind` value.**
Alternatives: (a) add `kind: model-watch` to KINDS; (b) `model_parse: bool`
optional field on existing `watch` sources.
**Recommendation: (b).** Evidence: the existing watch machinery
(snapshot/diff/partition) already runs correctly for these sources —
only the structured model-ID extraction is new. A new kind would require
touching the kind-dispatch path in `refresh.py` and the kind-validation
in `sources.py` for what is essentially an additive behavior. (b) is
strictly additive: the flag defaults false so all existing sources are
unaffected; the flag is model-only (rejected on `entry` kind; entry sources
project into corpus docs, not raw markdown pages). F4: HIGH on (b).

**D-MDL.2 — Model-lineup artifact path.**
Alternatives: (a) `.refresh/model-lineup/<id>.json`; (b) a new top-level
state dir; (c) inline in `last-run.json` only.
**Recommendation: (a).** `.refresh` is already a STATE_DIR; `resolve_state_path`
accepts it by construction. (b) would require widening `STATE_DIRS`
(a corpus.py edit). (c) is ephemeral — no durable artifact means no
prior-lineup baseline for the next run's delta. F4: HIGH on (a).

**D-MDL.3 — ID extraction from raw text vs normalized text.**
`extract_model_ids` runs on `raw` (the fetched bytes decoded to string),
not on `norm` (the normalized form). Evidence: the existing `normalize()`
for non-HTML collapses blank runs and strips trailing whitespace — it
preserves backticks. BUT: the normalizer's HTML path strips `<code>` tags
(which wrap backtick IDs in a rendered HTML view). If the .md URL ever
returns HTML instead of Markdown, `raw` is the safe choice (raw has
literal backticks; norm might strip them via the tag stripper).
Using `raw` is strictly more robust. F4: HIGH.

---

## §11 Provenance

- Trigger: owner-reported 2026-07-01 — Sonnet 5 shipped; never caught by
  the refresh tool. `claude-sonnet-5` is live at
  `platform.claude.com/docs/en/about-claude/models/overview.md` (verified).
- Parent component: `framework/tools/capability-refresh/` (sealed `c41f9473`,
  plan `docs/plans/claude-leverage-program-s1-currency.md`).
- Live verifications 2026-07-01: models-overview URL HTTP 200 (Markdown);
  pricing URL HTTP 200 (HTML); model IDs extracted: claude-fable-5,
  claude-mythos-5, claude-mythos-preview, claude-opus-4-1-20250805,
  claude-opus-4-6, claude-sonnet-5.
- Memory: `feedback_plan_before_code`, `feedback_no_non_objective_code`,
  `feedback_test_outcome_altitude_required`, `feedback_odd_no_non_objective_code`.

---

## §13 Status

_Pending build._

---

## §14 Method-decision register

| ID | Decision | Builder narrative | SHA |
|---|---|---|---|
| D-MDL.1 | `model_parse` boolean vs new kind | _pending_ | _pending_ |
| D-MDL.2 | Lineup artifact path | _pending_ | _pending_ |
| D-MDL.3 | Extract from raw text | _pending_ | _pending_ |
