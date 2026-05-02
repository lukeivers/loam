# OSS v0.1.0 publish — M11 — synthesis dry-run + private-staging review — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-05-02.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2 / future loam).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` — §5 row M11 + §6 sequencing rule 8 ("M11 is the integration gate") + §7 Gate G2 (synthesis dry-run review) + §3 prime ACs (AC.OSS.1 / AC.OSS.2 sweep / AC.OSS.3 sweep / AC.OSS.5 sweep).
**Predecessor sealed milestones:** M-FBM (memory-substrate pivot) + M7 (public docs) + M8 (license/governance) + M9 (synth-time substitution mechanism, commit `2161cb1`). Canonical HEAD `eb00b46` (post-Q.G1.2 CoC personal-email fix). Tree clean.
**Owner ruling 2026-05-02:** Gate G1 cleared; **M10 BYPASSED for v0.1.0 publish** (owner explicit clarification: "skip" was literal-not-deferral); M11 still splits into M11a (mechanical, autonomous; runs now) + M11b (owner-review only; review-circle dropped). M12 publish-flip gated on M11b owner GO; master plan §8 halt-trigger #10 explicitly overridden.
**Predicted AI-time:** M11a 30–60 min wall-clock, midpoint ~45 min (synthesis run + four sweeps + report authoring). M11b is owner-time + reviewer-time, NOT AI-time. Log actuals at §14.

**Authority documents:**

- Master plan §5 row M11: `docs/rebuild/plans/oss-v0-1-0-publish.md` — synthesis dry-run + private-staging review + automated sweep + owner gate G2 (rename master-plan numbering: G2 = "M8" in audit numbering).
- Master plan §6 sequencing rule 8: M11 is the integration gate; halt-and-surface fold-back to prior amendments if findings warrant.
- Master plan §6 sequencing rule 9: M12 publish-flip requires M11b GO + M10 closed.
- Master plan §3 prime ACs: AC.OSS.1 (stranger-bootable) + AC.OSS.2 (every shipping component wired; sweep) + AC.OSS.3 (no dev machinery in synthesis; sweep) + AC.OSS.5 (documentary rebrand; sweep).
- Master plan §13 D-Q.OSS.4: `loam-staging` repo lifecycle — recommendation persist as private repo for v0.x reuse.
- Memory-pivot precedent (recent landed sub-plan; format reference): `docs/rebuild/plans/oss-v0-1-0-publish-memory-pivot.md`.
- M9 scrub precedent (synth-substitution mechanism this sweep verifies): `docs/rebuild/plans/oss-v0-1-0-publish-scrub.md` — sealed `2161cb1` 2026-04-29; landed the four-entry SUBSTITUTION_TABLE the M11 AC.OSS.5 sweep checks.
- M7 docs lane precedent (verify-first / rewrite-only-on-fail pattern reference): `docs/rebuild/plans/oss-v0-1-0-publish-public-docs.md`.
- Synthesis tool: `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/{synth.py,partition.py,substitution.py,cli.py}`.
- Partition manifest (post-M-FBM): `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` — `framework/memory-system/**` reclassified `dev_only`; `framework/hands-off-lifecycle/tests/test_AC_AG_*.py` + `test_AC_BAG_*.py` reclassified `dev_only`; `plugins/dev-sdlc/**` reclassified `dev_only`.
- Feature-usage audit (AC.OSS.2 source): `.scratch/claude-output/feature-usage-audit.md`.
- VALUE_PROPOSITION (prime objective): `docs/rebuild/VALUE_PROPOSITION.md` — AC.PO.1 + AC.PO.2.
- CLAUDE.md design lenses: `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md` §1.

---

## 1. Summary / TL;DR

**Two-phase integration gate** verifying that everything sealed up to canonical HEAD synthesises into a clean, stranger-bootable v0.1.0 of loam, then exposed for human review.

- **M11a (mechanical, autonomous; v0.1.0 critical-path; runs now).** Synthesise canonical HEAD via the M2-extended `pos-publish-framework-only` pipeline → produce synthetic `framework-only` branch locally → push to private `lukeivers/loam-staging:main` (recommended; gh CLI authenticated to lukeivers) → run four automated sweeps:
  1. **AC.OSS.3 literal-match grep** on the named excluded artefact list (pos-amend / loam-amend / A1-A4 / loam-mode / docs/rebuild / pos-publish-framework-only / odd-methodology / odd-in-loam / duration-estimation-rubric).
  2. **AC.OSS.5 substitution sweep** on the four locked SUBSTITUTION_TABLE source-side entries (`/Users/lukeivers/ivers-corp-pos-v2/`, `lukeivers/pos-v2`, `Luke Ivers`) + zero-pre-rebrand-strings on M7 docs corpus.
  3. **AC.OSS.2 wired-component re-run** of the feature-usage-audit's test-only-caller detection sweep against the synthetic tree.
  4. **AC.MFBM.3 dependency sweep** — synthetic tree's `pyproject.toml` deps grep returns zero `graphiti / kuzu / ollama / sentence-transformers / fastmcp / BGE` matches.
  5. **AC.OSS.1 stranger-clone smoke** — bare-clone the synthetic into a tmp dir + a minimal first-run check.
  6. **Authored report** at a workspace-canonical path summarising every sweep's pass/fail + halt-conditions tripped.
- **M11b (human-review; M10-gated; runs after M10 review-circle is recruited).** Owner ~30 min browse staging repo (or local synthetic if push deferred) + 3-5 reviewers each ~30 min independently + collect notes privately + Gate G2 ruling (ship-or-foldback). NOT AI-time; calendar-parallel; max-of, not sum-of.

**Hard cutover:** if M11a's sweeps trip a halt clause, the build halts and surfaces; foldback to the offending milestone (M-FBM / M7 / M9 corrective amendment) — does NOT auto-author the foldback (per §11 D-Q.M11.4 below). Halt-clauses are named-deviation-shape; owner rules each.

**Estimated AI-time for M11a:** 30–60 min (synthesis run ~5 min + four sweeps ~15 min + stranger-clone smoke ~10 min + authored report ~10 min + push to staging if scoped here ~5 min).

---

## 2. Owner ruling captured (2026-05-02)

- **Gate G1 cleared.** License + governance scaffold accepted as-authored with one fix (Q.G1.2 CoC personal-email replaced with GitHub-private-channel pattern, sealed `eb00b46`).
- **M10 BYPASSED for v0.1.0** (clarification 2026-05-02 21:22Z, owner literal): "skip for now" was bypass-not-defer. v0.1.0 publishes without 3-5-person review circle. **Bus-factor-1 risk explicitly accepted at v0.1.0.** M10 stays available as a post-publish improvement (owner can recruit reviewers anytime; their feedback feeds v0.1.x). Master plan §8 halt-trigger #10 explicitly overridden by owner ruling.
- **M11 splits (with M10 bypass).** M11a = autonomous mechanical synthesis + sweep + (optional) staging push; runs against canonical HEAD now. M11b = OWNER browse + ruling ONLY (no review circle). AC.M11b.2 (reviewer notes) is **DELETED per bypass ruling**; AC.M11b.1 + AC.M11b.3 stay.
- **Programme sequencing.** M12 (publish + tag) is gated on M11b owner GO ONLY (per bypass ruling). M11a does NOT block on anything; M11b runs as soon as M11a's sweep report is authored.

**Methodology heads-up.** Shape (split into mechanical + human phases) preserves the integration-gate semantics: M11a verifies the synthesis tool + partition manifest + substitution mechanism + dependency-strip composability against the actual canonical HEAD; M11b verifies the human-review surface (does the public artefact read as "loam" not "rebuild of someone's machine"). Both phases must close GO before M12 publish.

---

## 3. Spec-objective placement (per CLAUDE.md §2.5)

The series binds to programme prime ACs:

- **AC.OSS.1 (stranger-bootable).** M11a's stranger-clone smoke verifies the synthetic tree's `git clone` + minimal-first-run path resolves; M11b's human review verifies the cognitive surface ("can a stranger orient without internal vocabulary?").
- **AC.OSS.2 (every shipping component wired).** M11a's wired-component sweep re-runs the feature-usage audit's test-only-caller detection against the synthetic tree.
- **AC.OSS.3 (no dev machinery in public synthesis).** M11a's literal-match grep verifies the excluded artefact list does not appear in the synthetic tree.
- **AC.OSS.5 (documentary rebrand).** M11a's substitution sweep verifies the four SUBSTITUTION_TABLE source-side tokens do not appear in the synthetic tree (the M9 substitution pass should have rewritten them all).
- **AC.MFBM.3 (no graphiti runtime dep at v0.1.0).** M11a's dependency sweep verifies the M-FBM partition reclassification has stripped graphiti / kuzu / Ollama / sentence-transformers / FastMCP / BGE from the synthetic tree.
- **AC.PO.1 (translation-burden absorption).** Stranger never sees pos-v2 vocabulary or canonical-host paths in the synthetic tree. M11a verifies mechanically; M11b verifies cognitively.
- **AC.PO.2 (toolkit-primitive growth).** The M11 sweep is itself a new toolkit primitive — a programmable integration gate that future v0.x releases compose against (rerun for v0.1.1, v0.2, etc.). Authored as a re-runnable shape, not a one-shot script.

**ODD §2.5 reverse-direction commitment.** Every AC below is outcome-shape only; method-shape (which exact grep flags, which exact sweep order, which exact stranger-clone smoke depth) is the per-amendment builder's call inside the AC outcome bound.

---

## 4. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

M11a's sweeps are pure git plumbing + grep + pytest re-runs — no LLM in the loop, deterministic, idempotent. The synthesis tool itself is a non-Claude artefact (per audit §7 observation; correct). M11b's human-review phase composes against Claude's existing review-skills surface (the loam-attached primary persona at the staging repo's clone can answer reviewer questions about the harness without reviewer needing to learn pos-v2-internal vocabulary — translation-burden absorption in action). The authored sweep report (§5 below) is markdown that the user opens with `open` / `bat` / Telegram attachment per the loam output convention. **No new Claude-Code primitive composition required at M11a; M11b composes against existing reviewer-as-Claude-user pattern. Pass.**

### Lens 2 — Harness + primary-persona value

- **Primary-persona test (translation burden):** M11a's authored report presents pass/fail per AC + halt-conditions tripped + recommendations — the persona summarises mechanical findings; owner rules from the summary per `feedback_summarize_and_surface_decisions`. M11b's reviewer experience: clone the staging repo + read README + run `claude` + ask the persona "what is loam?" → persona answers from the public artefact's docs. Zero pos-v2-internal vocabulary needed.
- **Harness test (toolkit primitive):** the M11a sweep mechanism is a re-runnable integration gate the harness gains as a primitive. Future v0.x releases (v0.1.1, v0.2, etc.) re-run the same sweep against new canonical HEADs to verify regression-freedom. The sweep is parameterised by the partition manifest + SUBSTITUTION_TABLE + the AC.OSS.3 excluded-artefact list — all of which compose forward.

**Pass on both tests.**

### Lens 3 — ODD authoring

Each AC below is outcome-shape, observable, deterministic. Method-shape (which exact grep regex flags, which exact stranger-clone smoke depth, which exact sweep order, whether the sweeps run as a single script or as separate per-AC pytest cases) is the M11a builder's call inside the AC outcome bound. The split between M11a (mechanical) and M11b (human) is itself an outcome-shape decision: M11a's outcome is "mechanical sweep report exists at known path + every named AC is pass-or-named-deviation"; M11b's outcome is "owner Gate G2 ruling captured + reviewer notes collected + foldback amendments named if any". Method (does M11a author the report inline or via a sub-script; does M11b use a private GitHub PR's review surface or a private gist; etc.) is the builder's / owner's call.

**Pass.**

---

## 5. Acceptance criteria — AC.M11a.* and AC.M11b.*

Outcome-shape only. Method-shape decisions are the per-amendment builder's call. Each AC carries a deterministic verification.

### AC.M11a.1 — Synthesise canonical HEAD via the pipeline; stable identifier recorded

`pos-publish-framework-only` (CLI from `framework/tools/pos-publish-framework-only/`) runs successfully against `--repo .` `--source HEAD`, producing a synthetic `framework-only` branch on disk in canonical pos-v2's repo. The synthesis returns a stable identifier (the framework-only branch HEAD SHA + the source-commit SHA it was built from). Both SHAs are recorded in the M11a authored report (§5 below) and in §14 below.

**Verification.** The CLI exits 0 (no `SynthesisError`); `git rev-parse refs/heads/framework-only` produces a non-empty SHA; the recorded SHA-pair is committed to the M11a report at `docs/rebuild/plans/oss-v0-1-0-publish-dry-run.md` §14 (post-build).

### AC.M11a.2 — AC.OSS.3 literal-match grep returns zero matches in synthetic tree

For every literal in the AC.OSS.3 excluded-artefact list (master plan §3 AC.OSS.3 plus the dispatch's named extension):

- `pos-amend`
- `loam-amend` (the post-rename CLI; should appear in dev-only paths only — NOT in synthesis)
- `A1` / `A2` / `A3` / `A4` (gate-prefix patterns; see §6 D-Q.M11.5 for false-positive carve-out)
- `loam-mode`
- `docs/rebuild/`
- `framework/tools/pos-publish-framework-only/`
- `odd-methodology`
- `odd-in-loam`
- `duration-estimation-rubric`

…literal-match grep against the synthetic `framework-only` tree returns ZERO matches in shipping-surface files.

**Verification.** `git ls-tree -r framework-only` → for each leaf, `git cat-file blob <sha>` | `grep -F <literal>` produces zero hits across the entire excluded-artefact list. Allowed residuals: zero. Halt-clause §9.1 fires if any literal hits; foldback to the offending milestone (M2 partition manifest gap, or M9 substitution table gap).

### AC.M11a.3 — AC.OSS.5 substitution-table source-side grep returns zero matches in synthetic tree

For every source-side token in the M9-locked SUBSTITUTION_TABLE:

- `/Users/lukeivers/ivers-corp-pos-v2/` (with trailing slash)
- `/Users/lukeivers/ivers-corp-pos-v2` (no trailing slash)
- `lukeivers/pos-v2`
- `Luke Ivers`

…literal-match grep against the synthetic `framework-only` tree returns ZERO matches.

**Verification.** Same grep mechanism as AC.M11a.2; zero hits per source-side token. Allowed residuals: zero (the M9 substitution pass should have rewritten every shipping-surface occurrence). Halt-clause §9.2 fires if any source-side token hits; foldback to M9-corrective (substitution-table extension).

### AC.M11a.4 — AC.OSS.2 wired-component re-run shows zero shipping-set components with only test-callers

The feature-usage-audit's test-only-caller detection sweep re-runs against the synthetic `framework-only` tree (all components in the partition's `dev_and_public` class). For every shipping component, at least one production caller exists in the synthetic tree (i.e. the component is not exercised only by test fixtures).

**Verification.** Builder's call on exact mechanism: re-run the feature-usage audit's grep + import-graph script (per `.scratch/claude-output/feature-usage-audit.md` methodology), or extract the named components from the partition manifest and run a per-component caller count via stdlib `ast` + `grep` against the synthetic tree. Result: zero components fail the production-caller bar. Allowed exception: operator-driven CLIs that are dev-only and excluded by partition (already not in synthetic tree). Halt-clause §9.3 fires if any shipping component fails; foldback to M3/M4/M5 wire-amendment corrective.

### AC.M11a.5 — Synthetic tree pyproject deps grep returns zero `graphiti / kuzu / ollama / sentence-transformers / fastmcp / BGE` matches

`pyproject.toml` files in the synthetic tree (root + every per-component) carry zero references to:

- `graphiti`
- `kuzu`
- `ollama`
- `sentence-transformers`
- `fastmcp`
- `BGE` (case-insensitive; covers `bge-reranker`, `BGE-M3`, etc.)

**Verification.** `git ls-tree -r framework-only -- '*pyproject.toml'` → for each, `git cat-file blob <sha>` | `grep -iE '<token>'` produces zero hits. Allowed residuals: zero (M-FBM partition reclassification should have stripped memory-system entirely from the synthetic tree). Halt-clause §9.4 fires if any token hits; foldback to M-FBM-corrective (partition manifest gap — likely a missed `dev_only` entry or a mistakenly-shipped dep declaration in another component).

### AC.M11a.6 — Stranger-clone smoke succeeds against synthetic tree

A stranger-clone smoke test exercises the AC.OSS.1 path against the synthetic tree:

```sh
git clone <local-bare-or-staging-url> /tmp/loam-test
cd /tmp/loam-test
# minimal first-run check appropriate to the loam CLI's init verb
# (exact shape is M11a builder's call per D-Q.M11.3)
```

…and reaches a recordable success state (per the chosen smoke depth in D-Q.M11.3) without manual intervention.

**Verification.** Builder's call on exact smoke shape (lightweight tmp-dir vs container-based vs full clean-machine simulation; D-Q.M11.3 below). The chosen shape's success criterion is named in the M11a report; the report records pass/fail. Halt-clause §9.5 fires if the smoke fails because the stranger-bootstrap path can't run without internal-vocabulary knowledge; surfaces as workspace-bootstrap first-run-path corrective.

### AC.M11a.7 — Staging push to `lukeivers/loam-staging` (if scoped to M11a per D-Q.M11.1)

If owner rules D-Q.M11.1 = staging push lands in M11a:

- Private repo `lukeivers/loam-staging` exists on github.com (created via `gh repo create lukeivers/loam-staging --private` if not already present).
- `lukeivers/loam-staging:main` carries a squashed initial commit; post-push tree is byte-identical to the local synthetic `framework-only` tree.
- Owner can `git clone https://github.com/lukeivers/loam-staging.git` against the private repo (gh CLI authenticated to lukeivers; verified at dispatch-time per dispatch-side gate).

**Verification.** `gh api repos/lukeivers/loam-staging` returns 200; `git ls-remote https://github.com/lukeivers/loam-staging.git` includes `refs/heads/main`; `git diff <local-framework-only-tree> <remote-staging-main-tree>` produces zero output. If owner rules D-Q.M11.1 = defer to M11b or skip-entirely-until-M12, this AC is omitted from M11a's authored report and recorded as deferred.

### AC.M11a.8 — Authored sweep report exists at canonical path

The M11a sweep produces an authored report at `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md` containing:

- Source-commit SHA + framework-only branch HEAD SHA (per AC.M11a.1).
- Per-AC pass/fail (AC.M11a.1..7).
- Named-deviation list (any AC that passed but with a known carve-out, e.g. the AC.M11a.2 `A1`/`A2`/`A3`/`A4` carve-out per D-Q.M11.5).
- Halt-clauses tripped (zero if all green).
- Recommendation: GO-to-M11b-and-M12 or fold-back-to-<milestone>.

**Verification.** File exists at the named path; content matches the authored shape; commit ladder tracks the sweep run. Per loam output convention (CLAUDE.md §3): the sweep report is a >40-line artefact written to disk; the sweep run's chat-output is a brief inline description plus the path.

### AC.M11a.S — Sealed-component fence

M11a is **NOT a sealed-component-source-changing amendment** in the canonical sense — it does not edit `framework/<comp>/` source. The fence is:

1. The synthesis tool (`framework/tools/pos-publish-framework-only/`) runs but does NOT change source.
2. The partition manifest (`framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`) is read but NOT edited at M11a. Any edit needed (e.g. partition manifest gap surfaced by AC.M11a.5) is foldback-to-M-FBM-corrective, not in-M11a edit.
3. The substitution module (`framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/substitution.py`) is read but NOT edited at M11a. Any edit needed is foldback-to-M9-corrective.
4. The synthesis tool's local `refs/heads/framework-only` branch advances; this is a tracked commit but on a synthetic branch (the source partition is intact).
5. The optional staging-repo push (AC.M11a.7) creates remote state at `lukeivers/loam-staging:main`; this is NOT in canonical pos-v2's seal-fence.
6. The M11a authored report at `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md` is `.scratch/` (gitignored); no commit-fence implications.
7. This plan-doc + the post-build §14 method-decision register update IS in the seal-fence (single doc-only commit).

`loam amend apply` runs BEFORE the seal commit per dispatch §Constraints if the sweep authoring graduates beyond `.scratch/`. If M11a only writes to `.scratch/` and updates this plan-doc's §14, the amendment is a doc-only commit + plan-doc commit pair (no `loam amend apply` required because nothing in the dev-mode-manifest's tracked corpus changes).

### AC.M11b.1 — Owner browses staging repo for ~30 min and rules

Owner clones the staging repo (or local synthetic tree if AC.M11a.7 was deferred) and spends ~30 min reviewing the public surface: README + positioning + getting-started + architecture + per-component refs + the loam CLI's `--help` output + a `claude` session against the public artefact's persona. Owner records findings + Gate G2 ruling (ship-or-foldback) at `docs/rebuild/plans/oss-launch-decisions.md` (per master plan §11).

**Verification.** `oss-launch-decisions.md` carries an M11b owner-ruling entry with timestamp + GO/foldback decision + named findings if foldback. Halt-clause §9.6 fires if owner finds "still looks like a rebuild of pos-v2" or "too obscure for a stranger to follow".

### AC.M11b.2 — DELETED per owner ruling 2026-05-02 (M10 bypass)

Originally: "3-5 reviewers each spend ~30 min and submit notes privately." Per owner clarification 21:22Z, M10 bus-factor mitigation is bypassed for v0.1.0; review circle is not part of the v0.1.0 publish gate. AC.M11b.2 is **DELETED**; reviewer notes are not required for M12 publish-flip. M10 remains available as a post-publish improvement (any feedback feeds v0.1.x), but does not gate v0.1.0.

**No verification required.** Halt-clause §9.7 explicitly does not fire under the bypass.

### AC.M11b.3 — Foldback amendments authored if findings warrant

If M11b findings (owner + reviewer) name a blocking issue, the foldback amendment(s) follow the same plan-before-code + sealed-component-amendment shape as the milestone they fold back to. Examples:

- "graphiti residual ref in public README" → foldback amendment in M-FBM corrective family.
- "Apache-license headers missing on N runtime files" → foldback amendment in M8 corrective family.
- "loam-staging README still says pos-v2" → foldback amendment in M7 corrective family + M9 SUBSTITUTION_TABLE extension if a new token surfaces.

Each foldback amendment lands sealed; M11b re-runs the affected M11a sweep against the new canonical HEAD; M11b's owner ruling re-issues.

**Verification.** Each foldback amendment carries its own sub-plan-doc + manifest + commit ladder + seal commit. M11b's owner ruling at `oss-launch-decisions.md` updates with each foldback iteration's GO ruling.

### AC.M11.S — Programme-level seal: M11 ruled GO or fold-back-and-rerun

After M11a + M11b both close GO, the M11 programme is sealed. Master plan §14 records every commit SHA. M12 publish proceeds.

**Verification.** §14 below carries every SHA. Master plan §14 entry for M11 reads "GO". M12's go-no-go gate G3 sees M11 as closed.

---

## 6. Sequencing — slot in master plan §5

Master plan §5 currently sequences M5 → M-FBM → M6 → M7 (parallel) → M8 (parallel) → M9 → M11 → M12. The split into M11a + M11b adjusts §6 sequencing rules:

**Rule 8a (NEW):** M11a runs autonomously after M9 seals (canonical HEAD now at `eb00b46`, post-Q.G1.2 fix). M11a does NOT block on M10. Build dispatch lands a single autonomous agent.

**Rule 8b (NEW; updated 2026-05-02 21:22Z):** M11b runs as soon as M11a's sweep report is authored (no M10 wait per owner bypass ruling). M11a's sweep report is the artefact owner browses alongside the staging repo. M11b's owner ruling is recorded at `oss-launch-decisions.md`.

**Rule 9 (CLARIFIED; updated 2026-05-02 21:22Z):** M12 publish-flip requires M11b owner GO only (M10 bypass per owner ruling). M11a GO is necessary but not sufficient; M11b owner GO is the hard requirement. Master plan §6 rule 9 + §8 halt-trigger #10's "M10 closing required" both explicitly overridden by bypass ruling.

**Concrete sequencing inside M11a:**

1. **Synthesise canonical HEAD** via the pipeline (AC.M11a.1). Builder's call: invoke CLI vs use the Python module directly.
2. **Run AC.OSS.3 literal-match grep** (AC.M11a.2) — fastest sweep; surfaces partition gaps first.
3. **Run AC.OSS.5 substitution sweep** (AC.M11a.3) — second-fastest; surfaces M9 SUBSTITUTION_TABLE gaps.
4. **Run AC.MFBM.3 dependency sweep** (AC.M11a.5) — third sweep; surfaces M-FBM partition gaps.
5. **Run AC.OSS.2 wired-component sweep** (AC.M11a.4) — fourth sweep; needs partition manifest + import-graph; longest single-sweep step.
6. **Run AC.OSS.1 stranger-clone smoke** (AC.M11a.6) — exercises clone path + minimal first-run.
7. **Optional: push to staging** (AC.M11a.7) — if D-Q.M11.1 rules staging-push lands in M11a; gh CLI auth verified before push.
8. **Author sweep report** (AC.M11a.8) — markdown summary at `.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md`.
9. **Plan-doc §14 update** (this file's §14, post-build).

**Concrete sequencing inside M11b (owner-time + reviewer-time, NOT AI-time):**

1. **M10 closes** — review circle of 3-5 recruited per AC.OSS.7. Calendar-driven; owner-driven.
2. **Owner browse + ruling** (~30 min owner time). Owner clones staging repo (or local synthetic if D-Q.M11.1 = defer) and rules.
3. **Reviewers each browse + submit notes** (~30 min × 3-5 reviewers; calendar-parallel; max-of, not sum-of).
4. **Owner aggregates findings + Gate G2 ruling**: GO or foldback.
5. **If foldback:** foldback amendments authored sealed; M11a re-runs against new canonical HEAD; M11b re-runs.
6. **§14 register fills** as foldback iterations land.

**Programme total impact.** M11a 30-60 min wall midpoint 45 min adds to v0.1.0 critical path — was 11-17 h post-M-FBM; now 11.5-18 h midpoint ~13.75 h. M11b is owner-time + reviewer-time + calendar-parallel; not counted toward AI-time.

**Safety property.** M11a is read-only against canonical (no source edits); the synthesis tool's `refs/heads/framework-only` branch is synthetic state, not canonical state. M11a does NOT edit the partition manifest, the SUBSTITUTION_TABLE, or any sealed-component source. Foldback amendments are authored AFTER M11a halts and surfaces — never silently extended.

---

## 7. Hard constraints (M11a-specific; series-wide constraints from master §5/§7 inherit)

1. **Plan-before-code** — this doc; §14 anchor present.
2. **Read-only on canonical at M11a.** No source edits, no partition manifest edits, no SUBSTITUTION_TABLE edits at M11a; foldback edits land in dedicated corrective amendments.
3. **No `git commit --amend`** — corrective commits are NEW commits per `feedback_no_amend_in_agent_dispatches`.
4. **Determinism + idempotence** — the M11a sweeps are idempotent: re-running on the same canonical HEAD produces identical sweep results. Per AC.OSS-M9.3 invariant.
5. **No third-party deps** — sweeps use stdlib `re` / `ast` / `subprocess` + git plumbing + pytest re-runs. No new pypi deps.
6. **`gh` CLI auth verified at dispatch-time** (AC.M11a.7) — if staging-push is scoped to M11a per D-Q.M11.1, the dispatcher verifies `gh auth status` reports lukeivers as active before the push. Halt-clause §9.8 fires if not authenticated.
7. **Sweep report at canonical `.scratch/` path** — the M11a authored report writes to `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md` (gitignored; survives session boundaries; per loam output convention CLAUDE.md §3).
8. **Halt-and-surface on ODD §2.5 violations** in any code/doc/manifest the M11a sweep surfaces (per `feedback_subagent_odd_violation_halt`). Sweep findings that look like ODD violations in surrounding code surface separately to the dispatcher.
9. **Auto-memory MEMORY.md is NOT touched.** Same series-wide constraint as M-FBM: the auto-memory corpus is Claude-managed; M11 does not edit, mirror, or re-survey it.
10. **No silent foldback authoring.** If a sweep trips a halt-clause, M11a stops and surfaces; the foldback amendment is authored as its own dispatch (not in-band by the M11a agent) per D-Q.M11.4 below.

---

## 8. Out of scope (named explicitly per ODD §2.5)

- **Authoring foldback amendments inline.** M11a is a verification phase; it does NOT auto-author corrective amendments for findings. Per D-Q.M11.4 + halt-and-surface §10. Foldback amendments are dispatched as their own scope.
- **Editing the partition manifest, the SUBSTITUTION_TABLE, or any sealed-component source.** M11a is read-only.
- **Reviewer recruitment.** That's M10's scope (calendar-parallel; owner-driven).
- **The publish-and-tag step.** That's M12's scope. M11 closing GO (both M11a + M11b) is M12's prerequisite.
- **HN / blog post / community-channel announcement.** That's the audit's "M10" (decoupled out-of-band item; not this plan's lane).
- **Long-tail v0.1.x integration-gate framework** (e.g. running M11 sweep on every PR). Surface as FUTURE_IDEAS_DRAFT capture post-M11; v0.2 lane.
- **Merging the framework-only branch back into pos-v2.** Synthetic branch is synthetic; not merged.
- **Git-history rewrite of canonical pos-v2 at M11a.** Per master plan §1.1 audit: no history rewrite. M12's squash-at-publish-time only.
- **Token-cost or resource budget surfacing for M11a synthesis.** Out of M11a; FUTURE_IDEAS_DRAFT capture if synthesis tool grows expensive.
- **Stranger-clone smoke at clean-VM granularity.** Per D-Q.M11.3 recommendation: lightweight tmp-dir simulation at M11a; container or clean-VM is M11b's owner-driven environment if owner wants extra rigor.
- **Hardening the sweep against future canonical-pos-v2 evolution.** M11a sweeps are parameterised by the partition manifest + SUBSTITUTION_TABLE + the AC.OSS.3 excluded-artefact list; if the source-of-truth shifts, the sweep follows. v0.2 may add new sweeps; out of M11 scope.

---

## 9. Halt-and-surface conditions

Per `feedback_subagent_odd_violation_halt` + `feedback_critical_thinking_on_deviations`. The M11a builder halts + surfaces to dispatcher on any of:

1. **AC.M11a.2 grep finds residual `pos-amend` / `loam-amend` / `A1-A4` / `loam-mode` / `docs/rebuild/` / `framework/tools/pos-publish-framework-only/` / `odd-methodology` / `odd-in-loam` / `duration-estimation-rubric` literal in synthetic tree.** Means the M2 partition manifest reclassification + M9 scrub didn't fully strip; foldback to M-FBM-corrective or M2-corrective amendment.
2. **AC.M11a.3 grep finds residual `/Users/lukeivers/ivers-corp-pos-v2/` / `lukeivers/pos-v2` / `Luke Ivers` literal in synthetic tree.** Means the M9 SUBSTITUTION_TABLE has a gap (e.g. a new token type not in the four-entry table; a binary-blob carve-out missed; a code-path that bypasses the substitution pass). Foldback to M9-corrective; SUBSTITUTION_TABLE extension.
3. **AC.M11a.4 wired-component sweep finds shipping-set component with only test-callers.** Means a component shipped at v0.1.0 isn't actually wired into production code-paths. Foldback to M3/M4/M5 wire-amendment corrective; or partition-manifest reclassification to `dev_only`.
4. **AC.M11a.5 dependency sweep finds `graphiti` / `kuzu` / `ollama` / `sentence-transformers` / `fastmcp` / `BGE` in synthetic pyproject.** Means M-FBM partition reclassification has a gap. Foldback to M-FBM-corrective.
5. **AC.M11a.6 stranger-clone smoke fails.** Means the workspace-bootstrap first-run path can't bootstrap without internal-vocabulary knowledge or external-network state the bootstrap hasn't named explicitly. Foldback to workspace-bootstrap-corrective.
6. **AC.M11b.1 owner / AC.M11b.2 reviewer finds "still looks like a rebuild of pos-v2" / "too obscure for a stranger to follow" / blocking-AC violation.** Foldback to the named milestone (M7 docs / M9 substitution / M-FBM partition / M8 license). Owner records named findings; foldback amendment(s) authored sealed; M11a re-runs; M11b re-runs.
7. **~~M10 has not closed when M11b is dispatched.~~** EXPLICITLY OVERRIDDEN per owner ruling 2026-05-02 21:22Z. M10 is bypassed for v0.1.0; this halt-clause does NOT fire under the bypass. Master plan §8 halt-trigger #10 ("delay public-flip 2 weeks") is also overridden. Bus-factor-1 risk explicitly accepted at v0.1.0.
8. **`gh` CLI not authenticated to lukeivers when AC.M11a.7 runs.** Surfaces as owner-action-shaped: dispatcher pauses M11a's staging-push step, surfaces to owner; M11a continues with AC.M11a.7 deferred to M11b (or M12). Owner authenticates separately; M11a re-runs the AC.M11a.7 step on next dispatch.
9. **Synthesis tool errors during pipeline run** (M11a step 1; AC.M11a.1). Means M2 partition manifest extension is broken, or M9 substitution module is broken, or some other mechanic in the synthesis tool. Foldback to M2-corrective or M9-corrective per the surfaced error.
10. **`pos-amend apply` (or post-rename `loam amend apply`) was not run before the M11a seal commit.** Per dispatch §Constraints + `feedback_dispatch_explicit_pos_amend_apply`. The M11a builder confirms `loam amend apply` was invoked OR confirms M11a is a doc-only commit (no `loam amend apply` required) before sealing. Halt if neither is true.
11. **ODD §2.5 violation surfaces in surrounding code/docs.** Per `feedback_subagent_odd_violation_halt`. M11a halts + surfaces; foldback amendment authored separately.
12. **Wall-time exceeds estimate by >50%.** Per programme master §8 halt trigger 8. Halt with current-state report; owner triages whether to continue, split, or pause.
13. **AC.M11a.7 staging push fails with auth or quota error after gh-CLI-auth verified.** Means a transient GitHub error (rate limit, network, auth-token-scope mismatch). Halt; surface error; owner triages retry vs defer.
14. **AC.M11a.8 sweep report cannot be authored at canonical `.scratch/` path** (e.g. workspace-bootstrap missed a `.scratch/` directory creation). Halt; surface workspace-bootstrap gap; foldback to workspace-bootstrap-corrective.

---

## 10. Risks (M11a-specific)

1. **Synthesis tool slow on a large canonical tree.** Mitigation: profile during M11a's first run; if synthesis dominates wall-clock, FUTURE_IDEAS_DRAFT capture for batched-blob optimisation per M9 §14 D-build.M9.3 builder's discretion.
2. **AC.M11a.4 wired-component sweep produces false positives** (e.g. flags a component as test-only because its production caller is in a renamed namespace post-M1.rename-series). Mitigation: re-use the feature-usage audit's already-validated mechanic; document any false-positive in §14 method-register.
3. **AC.M11a.6 stranger-clone smoke depth ambiguity** — what constitutes a "successful first-run"? Mitigation: D-Q.M11.3 recommends lightweight depth (smoke = clone + import + minimal CLI invocation); M11b owner-time can run deeper environments.
4. **AC.M11a.2 grep produces false positives on `A1-A4`** (e.g. `A1` literal appears in a fixture string for `--A1` argparse option). Mitigation: D-Q.M11.5 recommends carve-out — gate-prefix patterns are matched as `pos-amend`-class CLI args, not bare literal `A1`. Builder refines regex shape.
5. **AC.M11a.7 staging-push creates a private repo without owner expectation.** Mitigation: D-Q.M11.2 recommends owner pre-approves the staging repo creation as part of M11a dispatch; the dispatch itself surfaces the staging-repo-name + creation-step explicitly so owner can defer if not yet ready.
6. **M11b reviewer recruitment lag** — M10 closes weeks-to-months after M11a; M11a's sweep report becomes stale if canonical pos-v2 evolves in the interim. Mitigation: M11a re-runs on the canonical-HEAD-at-M11b-dispatch-time, not on a stale snapshot. Cost: ~45 min re-run per M11b iteration; cheap.
7. **Foldback iterations cascade.** A finding in M11b might fold back to M9, but the M9 corrective might surface a new partition gap that requires M-FBM corrective. Mitigation: sequential foldback; each iteration closes its own GO before next iteration runs. Owner rules at each Gate G2 mini-cycle.

---

## 11. Decisions remaining for owner ruling

Per `feedback_summarize_and_surface_decisions` — five named decisions with recommendations. Owner rules from this summary.

### D-Q.M11.1 — Staging-push placement (M11a or M11b or M12)

**Q.** Does AC.M11a.7's push to private `lukeivers/loam-staging` land in M11a (autonomous; runs now), or M11b (gated on M10 closing), or M12 (final-step at publish flip; skip staging entirely)?

**Rec.** **M11a — staging-push lands as part of the autonomous mechanical sweep.** Rationale: (a) `gh` CLI is verified authenticated to lukeivers (verified at dispatch-time per dispatch fence); (b) the staging repo is a useful artefact for future v0.x dry-runs per master plan §13 D-Q.OSS.4 (recommended persist as a private repo); (c) M11b's reviewers benefit from a `git clone` URL to share, not "ssh into Luke's machine"; (d) cheap (~5 min push); (e) no public exposure (private repo).

If owner rules **defer to M11b**: the M11a authored report names the local synthetic tree path; M11b's reviewer-experience is "ssh into Luke's machine OR receive a git bundle". Cost: friction for reviewers.

If owner rules **skip until M12**: M11b runs against local synthetic + a git bundle owner shares with reviewers; staging repo is created at M12 publish-flip time. Cost: M11b reviewer experience is suboptimal; loses the v0.x-reuse value.

### D-Q.M11.2 — `lukeivers/loam-staging` repo lifecycle

**Q.** Per master plan §13 D-Q.OSS.4: persist as private repo for v0.x reuse, or delete after M11/M12, or skip creation entirely?

**Rec.** **Persist as private repo.** Rationale: (a) zero cost (free for personal account); (b) future v0.x integration-gate runs (v0.1.1, v0.2, etc.) re-use the same staging URL; (c) owner can audit "what does the previous release look like" via `git log lukeivers/loam-staging`; (d) preserves the toolkit-primitive value of the M11 sweep mechanism. Master plan §13 D-Q.OSS.4 already recommends this; surface here for completeness.

### D-Q.M11.3 — Stranger-clone smoke depth

**Q.** AC.M11a.6's stranger-clone smoke shape: full clean-machine simulation (heavy; container or VM) vs container-based isolated-env (medium; Docker/podman) vs lightweight tmp-dir simulation (lightweight; `git clone` to `/tmp/loam-test` + minimal CLI check).

**Rec.** **Lightweight tmp-dir simulation at M11a; deeper environments at M11b owner-time.** M11a smoke = `git clone <staging-or-local> /tmp/loam-test && cd /tmp/loam-test && git log -1 && ls -la && python -c "import loam.primary_persona"` (or builder-equivalent). M11b owner-time can run a container-based env if owner wants extra rigor. Rationale: (a) M11a is the mechanical sweep; full clean-VM is high-cost-low-marginal-yield at this phase; (b) M11b's human review is where deep environment fidelity pays off — owner clones to a fresh laptop or container and walks through; (c) lightweight smoke catches the most common failure mode (broken Python import-path, missing deps not declared in pyproject.toml) without the container ceremony.

### D-Q.M11.4 — Sweep findings: auto-foldback or always-halt-and-surface

**Q.** When AC.M11a.2..6 sweeps trip a halt-clause, does M11a auto-author a small foldback fix (e.g. extend SUBSTITUTION_TABLE, add a partition entry) and commit it, or always halt-and-surface and let owner dispatch a corrective amendment?

**Rec.** **Always halt-and-surface.** Rationale: (a) per `feedback_critical_thinking_on_deviations`, foldback decisions warrant owner ruling — what looks like a small SUBSTITUTION_TABLE extension might surface a deeper pattern; (b) per `feedback_dispatch_explicit_pos_amend_apply`, sealed-component fences need explicit dispatch authoring; M11a auto-foldback would silently extend a fence; (c) M11a's outcome is verification, not corrective — keeping the role narrow preserves the integration-gate semantics; (d) the cost of halt-and-surface is one extra dispatch cycle per finding (~30-90 min for the corrective amendment); cheap.

### D-Q.M11.5 — Sweep mechanism: single agent vs split per-AC

**Q.** Does M11a run all sweeps in one agent (single dispatch; ~45 min), or split per-AC (one agent per sweep; ~5-10 agents in parallel; ~15 min critical path)?

**Rec.** **Single agent at M11a v0.1.0.** Rationale: (a) sweeps are sequential by nature (synthesis must complete before grep-against-tree; report must be authored after sweeps complete); the parallel speedup is small for one canonical HEAD; (b) `feedback_serialize_amendment_builds` flags two amendment-build agents racing on `pos-amend`/index.lock — even though M11a doesn't write to canonical, the per-sweep variants each call `git ls-tree` against canonical, and multiple agents introduce coordination overhead for small marginal speedup; (c) single-agent simpler to author + simpler to read in `oss-v0-1-0-publish-m11a-sweep-report.md`; (d) Idea C from FUTURE_IDEAS_DRAFT (loam-sweeper subagent persona) is a v0.2-class composition — a parameterised sweep-runner that takes a partition manifest + SUBSTITUTION_TABLE + excluded-artefact list and produces the report. Surface as FUTURE_IDEAS_DRAFT capture; not in M11 scope.

If owner rules **split per-AC**: dispatch 5 parallel agents (AC.M11a.2..6); each writes its own sub-report; the M11a parent agent assembles the final report. Cost: more coordination; faster wall-clock. Benefit: parallel-safe per-AC reporting + clearer per-sweep ownership.

---

## 12. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit / methodology / surrounding-code / surrounding-docs ODD violations encountered while authoring this plan.

**Findings (none triggers a halt):**

1. **`gh` CLI is verified authenticated to lukeivers.** Dispatch-time check at plan authoring: `gh auth status` reports lukeivers as active account with `repo` scope. AC.M11a.7 staging-push is feasible at M11a (recommendation D-Q.M11.1 stands). **NOT a halt.**
2. **Partition manifest current state verified post-M-FBM + M6b.0 + M9 + post-G1 fix.** `framework/memory-system/**` reclassified `dev_only` (line 184); `plugins/dev-sdlc/**` reclassified `dev_only` (line 237); gate-test files reclassified `dev_only` (lines 211-212); SUBSTITUTION_TABLE 4-entry locked at `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/substitution.py`. M11a sweeps will exercise these against canonical HEAD. **NOT a halt.**
3. **Master plan §6 sequencing rule 9 ("M12 publish-flip requires M10 closing") was implicit; this sub-plan formalises rule 8a + 8b + 9 (clarified) split.** Master plan doc-only update is owner-action-shaped (master plan edit sequenced as separate doc-only commit per memory-pivot precedent §13). **NOT a halt** — observation surfaced for owner action post-M11a-plan-doc seal.
4. **No new audit-table entries needed beyond what's named in §5.** Post-M9 substitution-table audit was already complete (M9 §7 finding 4); M11a's sweep is verification, not extension. **NOT a halt.**
5. **No ODD §2.5 violations encountered in surrounding code/docs during the M11 plan authoring.** The synthesis tool source + partition manifest + substitution module are clean; the previously-surfaced gate-test-partition-completeness gap (M9 §7 finding 1) was already resolved at amendment AC.PMR.1 per partition manifest comments lines 197-209. **NOT a halt.**
6. **Idea-C-shape FUTURE_IDEAS_DRAFT capture flagged.** A `loam-sweeper` subagent persona that parameterises the M11 sweep mechanism for v0.x reuse is a natural composition-target. Surface as FUTURE_IDEAS_DRAFT post-M11; not in M11 scope. **NOT a halt.**
7. **M11a outcome is partly observable via .scratch/** (the sweep report). Per CLAUDE.md §3 output convention: ephemeral artefacts go to `<workspace>/.scratch/claude-output/<subject>.md`; persistent state goes to canonical paths. M11a sweep report at `.scratch/` is correct (gitignored; survives session boundaries; doesn't bloat canonical tree). The M11 plan-doc itself (this file) IS canonical (`docs/rebuild/plans/`). **NOT a halt** — captures the convention correctly.

**Halt summary.** None of the above triggers a halt. All findings surfaced; plan authorised pending owner sign-off on §11 D-Q.M11.1..5.

---

## 13. Out-of-band: master programme plan §6 rule update

The master plan `oss-v0-1-0-publish.md` §6 sequencing rule 8 currently reads "M11 (dry-run) is the integration gate". Post-this-plan, rule 8 splits into 8a (M11a autonomous; runs now) + 8b (M11b owner-driven; runs after M10). Rule 9 ("M12 publish-flip is gated on M10") clarifies to "M12 publish-flip requires M11b GO + M10 closed; M11a GO is necessary but not sufficient". **This plan-doc commit does NOT edit the master plan §6** — separate doc-only commit at next dispatch, mirroring M-FBM's master-plan-update protocol (M-FBM §13). Programme total re-prices: was 11-17 h AI wall midpoint ~13 h; post-M11a-split 11.5-18 h midpoint ~13.75 h. Master plan §13 D-Q.OSS.4 register entry for `loam-staging` lifecycle is preserved (recommendation persist; D-Q.M11.2 here references it).

---

## 14. Method-decision register (post-build, per phase)

Filled by each phase's builder post-build per existing precedent (M9 §14 D-build.M9.*).

### M11a — OSS-build.M11a.x — (post-build)

**M11a dispatch 1 of N — HALTED at synthesis step (2026-05-01).** Per plan §9.9 (synthesis tool errors during pipeline run); single finding F-M11a.1 (partition manifest does not classify `docs/plugins/dev-sdlc.md`, added by M7 commit `2fefd8b`). Foldback to M2-corrective (partition manifest extension) required before M11a re-dispatches. Full halt narrative + RCA + foldback recommendation: `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md` (overwritten by dispatch 2). Source-commit at halt: `47cbea7`. Framework-only branch SHA: N/A (synthesis errored; branch not advanced). Foldback amendment #98 (M7-partition-fix) sealed `d983f94`; M8-corrective amendment #99 sealed `5271091` (separate halt detected by amendment #98 build).

- D-build.M11a.1 (dispatch 1): Synthesis invocation shape — Python module via console-script entry point `pos-publish-framework-only` from a fresh `python3.13 -m venv` at `/tmp/m11a-venv` with `pyyaml` + editable-install of `loam-publish-framework-only`. Rationale: project requires Python ≥3.11 + yaml; system Python defaults required workarounds.
- D-build.M11a.2..9: NOT REACHED in dispatch 1 (synthesis errored before sweeps could run). Carried forward to M11a re-dispatch.

**M11a dispatch 2 of N — HALTED at AC.M11a.2 (AC.OSS.3 literal-match grep) (2026-05-01, post-recovery).** Per plan §9.1 (AC.OSS.3 grep finds residual literal). Source-commit `78417c5`; framework-only branch advanced to `947ebe2`. AC.M11a.1 / .3 / .4 / .5 / .6 PASS; AC.M11a.2 FAIL with three named root-cause classes (Class A: seals ship publicly under `<comp>/seals/**` carrying dev-historical narrative; Class B: dev-only meta-tests like `tests/test_no_sealed_amendments.py` and `tests/test_AC_*_seal_diff_*.py` ship publicly; Class C: production source/docs in 21+ files reference dev-only paths `docs/rebuild/`, `plugins/dev-sdlc/docs/odd-methodology.md`, etc., which do not exist in synthetic tree). AC.M11a.7 staging push DEFERRED (D-Q.M11.4 halt-before-push). Full halt narrative + per-class root-cause + foldback recommendations: `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md`.

- D-build.M11a.2 (dispatch 2): AC.M11a.2 grep mechanism — `git grep -F -l <literal> framework-only` + `awk` bucketing by top-level component; distinguishes seals/tests from production source via path filter.
- D-build.M11a.3 (dispatch 2): AC.M11a.3 grep mechanism — `git grep -F -c` per source-side token; zero hits across all 4 SUBSTITUTION_TABLE source-side entries.
- D-build.M11a.4 (dispatch 2): AC.M11a.4 wired-component sweep mechanism — per-component module-name regex (`loam.<snake_case>`) + production-vs-test path partitioning (`*.py ':!*/tests/*'` vs `'*/tests/*.py'`); every shipping component has ≥1 production caller.
- D-build.M11a.5 (dispatch 2): AC.M11a.5 deps sweep mechanism — `git ls-tree` enumerated 14 pyproject.toml files; per-file `git show <path> | grep -ic <token>` summed; zero hits across graphiti/kuzu/ollama/sentence-transformers/fastmcp/BGE.
- D-build.M11a.6 (dispatch 2): stranger-clone smoke — local-bare clone + unbare clone + fresh venv + `pip install -e ./scope-of-work -e ./primary-persona` + `import loam.primary_persona`; lightweight depth per D-Q.M11.3; PASS with caveat (stranger needs to know to install in-workspace siblings together).
- D-build.M11a.7 (dispatch 2): AC.M11a.7 staging push — DEFERRED per AC.M11a.2 halt; `lukeivers/loam-staging` not created; no GitHub state written.
- D-build.M11a.8 (dispatch 2): report authoring — overwrites dispatch-1 halt narrative with full dispatch-2 results at canonical `.scratch/` path.
- D-build.M11a.9..N: builder-discovered method decisions (re-dispatch + future dispatches).

**M11a dispatch 3 of N — CLOSED GO (2026-05-01, post-recovery).** All 8 ACs PASS. Source-commit `710ea4d`; framework-only branch at `c4f24bf` (synthesis was a no-op idempotent re-run on already-current branch — dispatch 2 had advanced framework-only to `947ebe2`, but the recovery cycle (#100/#101/#102) re-synthesised against the corrected manifest+SUBSTITUTION_TABLE; the branch was already at `c4f24bf` from the C2-prime build smoke-check). Eight named AC.OSS.3 literals scan to ZERO files in synthetic tree (`pos-amend`, `loam-amend`, `loam-mode`, `docs/rebuild/`, `odd-methodology`, `odd-in-loam`, `duration-estimation-rubric`, `pos-publish-framework-only`). Four AC.OSS.5 source-side tokens scan to zero. Six AC.MFBM.3 deps scan to zero across 14 pyproject.toml files. Wired-component sweep: every shipping component has ≥1 production caller (tests/ stripped from synthesis surface per amendment #101). Stranger-clone smoke succeeded (clone + pip install -e + `import loam.primary_persona` + `import loam.scope_of_work` all green). Staging push: `lukeivers/loam-staging` created private; `main` at `c4f24bf`; byte-identical to local synthetic. Full sweep narrative: `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md`. **Hand-off to M11b READY.**

- D-build.M11a.9 (dispatch 3): Synthesis re-run — confirmed idempotent on unchanged canonical (`710ea4d` → `c4f24bf` no-op exit 0). When dispatch-2-era framework-only SHA is upstaged by recovery-cycle re-synthesis at amendment build time, M11a-3 sees the post-recovery branch as already-current; CLI no-op guard short-circuits.
- D-build.M11a.10 (dispatch 3): AC.M11a.7 staging push mechanism — `gh repo create lukeivers/loam-staging --private` (single call) + `git push https://github.com/lukeivers/loam-staging.git framework-only:main` (single call); verification via `git ls-remote` (remote main SHA matches local `framework-only` SHA) + `gh api repos/...` (200 OK; private:true; default_branch:main).
- D-build.M11a.11..N: builder-discovered method decisions (M11b dispatch + future re-runs).

### M11b — OSS-build.M11b.x — (post-build, post-M10)

- D-build.M11b.1: Owner-browse mechanism (clone staging vs use local synthetic).
- D-build.M11b.2: Reviewer-aggregation channel (email / DM / private gist; per-reviewer's choice).
- D-build.M11b.3: Foldback-amendment dispatch shape (per finding; named-deviation-shape).
- D-build.M11b.4..N: builder-discovered method decisions.

### Commit SHAs

- M11a plan-doc commit (this plan, original authoring): `47cbea7` (post-M10-bypass-edits inclusive).
- Master-plan §6 rule-update doc-only commit: `<TBD>` (next dispatch).
- **M11a dispatch-1 halt-pointer commit (doc-only; appends §14 D-build.M11a.1 + halt narrative pointer):** `b1dc662`.
- **M11a foldback amendment #98 (M7-partition-fix; partition manifest extension for `docs/plugins/**`):** sealed `d983f94`.
- **M8-corrective amendment #99 (HC#4 byte-content rebaseline post-Apache-header insertion):** sealed `5271091`.
- M11a sweep-execution commit (if any tracked artefacts beyond this plan-doc + .scratch/ report): N/A in dispatch 1 + dispatch 2 + dispatch 3 (M11a is read-only against canonical; staging push is to remote, not canonical-tracked).
- M11a `.scratch/` sweep report (NOT committed to git per .scratch/ gitignore): `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md` (dispatch 3 overwrites dispatch 1 + dispatch 2; dispatch 3 narrates GO).
- M11a synthetic `framework-only` branch HEAD SHA: dispatch 1 N/A (synthesis errored); dispatch 2: `947ebe2` (synthesis succeeded; branch advanced from source `78417c5`); **dispatch 3: `c4f24bf`** (canonical source `710ea4d`; synthesis no-op-on-current — branch already at `c4f24bf` from C2-prime smoke check).
- **M11a dispatch-3 staging push:** repo `lukeivers/loam-staging` created (private); `main` at `c4f24bf`; URL https://github.com/lukeivers/loam-staging. Per D-Q.M11.2: persists for v0.x reuse.
- **M11a dispatch-2 halt-pointer commit (doc-only; appended §14 D-build.M11a.2..8 + halt narrative pointer for dispatch 2):** `<TBD-D2>` (was filled by dispatch-2 wrap-up; review prior recovery-cycle commits if needed).
- **M11a dispatch-3 GO-pointer commit (this update; doc-only; appends §14 D-build.M11a.9..10 + dispatch-3 GO narrative):** `3c8e228`.
- M11a seal commit: N/A in dispatch 1 + dispatch 2 + dispatch 3 (M11a does not seal a sealed-component amendment per AC.M11a.S; doc-only commit pair is the M11a wrap).
- M11b owner-ruling entry at `oss-launch-decisions.md`: `<TBD>` (post-M11b owner browse + ruling).
- M11b foldback amendment commits (if any): `<TBD>` (none expected — M11a closed GO).
- M11.S programme-seal entry in master plan §14: `<TBD>` (post-M11b-GO).

---

## 15. References

- **Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
- **Memory-pivot sub-plan precedent:** `docs/rebuild/plans/oss-v0-1-0-publish-memory-pivot.md`.
- **M9 scrub precedent (substitution mechanism this sweep verifies):** `docs/rebuild/plans/oss-v0-1-0-publish-scrub.md`.
- **M7 docs-lane precedent (verify-first / rewrite-only-on-fail pattern):** `docs/rebuild/plans/oss-v0-1-0-publish-public-docs.md`.
- **Synthesis tool:** `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/{synth.py,partition.py,substitution.py,cli.py}`.
- **Partition manifest:** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- **Feature-usage audit (AC.OSS.2 source):** `.scratch/claude-output/feature-usage-audit.md`.
- **OSS-readiness audit:** `.scratch/claude-output/oss-readiness-audit.md`.
- **Master decisions dossier:** `.scratch/claude-output/oss-publish-master-dossier.md`.
- **VALUE_PROPOSITION (prime objective):** `docs/rebuild/VALUE_PROPOSITION.md` AC.PO.1 + AC.PO.2.
- **CLAUDE.md design lenses:** `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md` §1 (lenses 1/2/3) + §3 (output convention).
- **STATE.md:** `docs/rebuild/STATE.md` — governing rules + component table.
- **Owner-ruling-history:** `docs/rebuild/plans/oss-launch-decisions.md` — M0 + (forthcoming) M11b ruling.
- **First-run-inventory (post-M-FBM):** `framework/first-run-inventory.yaml` — graphiti-service retired from runtime.
- **Memory bullets carried forward (cited per dispatch corpus):**
  `feedback_plan_before_code`, `feedback_subagent_odd_violation_halt`,
  `feedback_summarize_and_surface_decisions`, `feedback_critical_thinking_on_deviations`,
  `feedback_serialize_amendment_builds`, `feedback_no_amend_in_agent_dispatches`,
  `feedback_dispatch_explicit_pos_amend_apply`, `feedback_value_proposition_as_prime_objective`,
  `feedback_duration_estimation_rubric`, `feedback_background_default_for_authoring`.

---

*End of plan.*
