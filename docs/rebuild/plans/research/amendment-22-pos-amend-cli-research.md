# pos-v2 sealed-component amendment-cycle rituals — streamlining research

**Author:** design-research agent, 2026-04-22 (commissioned on pos-v2 @ `ff21e18`).
**Canonical tree inspected:** `/Users/lukeivers/ivers-corp-pos-v2/` (read-only).
**Status:** research artefact for Luke to rule on; no amendment authored.

---

## 1. Executive summary

**Biggest streamlining win:** a tiny `pos-amend` CLI driven by a per-amendment **manifest** (components touched + declared allowed-prefix extensions). The manifest lets the tool mechanically (a) advance every affected component's `BASELINE` constant and `tests/SEAL_COMMIT` sidecar to the right SHA at the right time, (b) extend each component's `allowed_prefixes`/`allowed_files` tuple with the *cross-product* of partner components in the same amendment — which is what corrective commits like `8bdf194` are doing by hand — and (c) append a single canonical amendment-cycle block to `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`. Humans still author plan + code + commit messages; the tool only does bookkeeping. A dry-run mode simulates the seal-diff and surfaces missing widenings before the amendment commit lands, eliminating the two-commit "amendment + corrective" pattern that burned a whole commit (`8bdf194`) on amendment #18.

**Biggest trap:** do **not** centralise the per-component `BASELINE` constant into a single file. The per-component pin is the invariant — it is what proves each sealed component's surface has not drifted since its named prior state. A unified manifest can *generate* those constants at ritual time, but the constants must still land in the per-component test file as discrete literals, because that is where the proof is reviewable.

---

## 2. Current-state inventory

I walked amendment #18 (commits `4c385ed`, `8bdf194`, `f1ff28b`) plus #13, #15, #16, #17, #19, #20, #21 for comparison.

### 2.1 Per-amendment file touches (amendment #18 anatomy)

Amendment #18 shipped in **three commits** touching **19 distinct files**:

**Commit `4c385ed` (amendment commit, 19 files):**

| File | Classification | Reason |
|---|---|---|
| 7 × `docs/rebuild/components/<comp>/brief.md` (deletions) | (a) AC-fulfilment | the amendment's intent |
| `docs/odd-in-pos.md` (§7.4 edit) | (a) AC-fulfilment | the amendment's intent |
| `docs/rebuild/plans/delete-method-in-brief-dispatch-docs.md` (new, 302 lines) | (b) structural bookkeeping | plan-before-code CDC |
| 5 × `tests/test_no_sealed_amendments.py` OR `test_cross_cutting.py` | (b) structural bookkeeping | BASELINE advance + allowed-prefix extensions |
| 5 × `tests/SEAL_COMMIT` | (b) structural bookkeeping | set to BASELINE SHA for empty-diff window |

Ratio: **8 fidelity-producing touches / 11 bookkeeping touches** = 0.73× productive.

**Commit `8bdf194` (corrective commit, 5 files):** 100% reactive bookkeeping. The multi-component cross-reference widening that should have been in `4c385ed` but wasn't, because the seal-diff test in each component sees the **whole-repo** diff and needs to admit its partners' surfaces too. This commit exists only because the first commit's widenings were insufficient.

**Commit `f1ff28b` (seal commit, 6 files):** 5 × `tests/SEAL_COMMIT` sidecar advances from BASELINE → seal SHA; 1 × `seals/SEAL_COMMIT.true-first-run` narrative append (70 lines for this cycle).

**Ratio across the whole amendment:** 8 productive / 22 bookkeeping. That's a **2.75× bookkeeping-to-productive ratio**, or inverse 36% productive. That is the cost of the ritual on a multi-component amendment, and is the number to beat.

### 2.2 BASELINE + SEAL_COMMIT pattern

Each sealed component has two or three files enforcing the invariant:

1. `tests/test_no_sealed_amendments.py` with a literal `BASELINE = "<sha>"` constant — the **pin**: the SHA the diff window starts from. Reviewable in the test file itself.
2. `tests/SEAL_COMMIT` — the **endpoint**: the SHA the diff window ends at. Falls back to `HEAD` if the file holds "HEAD" or is missing, so the test passes during amendment authoring.
3. `seals/SEAL_COMMIT.<narrative>` (only on 2 components — hands-off-lifecycle and telegram-interface) — the **story**: human-readable amendment-cycle record, appended per amendment.

**What each enforces:**
- `BASELINE` + `SEAL_COMMIT` together define the diff window. The test asserts: across this window, only paths matching `allowed_prefixes` / `allowed_files` changed.
- `seals/SEAL_COMMIT.*` encodes nothing the test reads; it's documentation for humans.

**Collapse analysis:**
- Collapse `BASELINE` + `tests/SEAL_COMMIT` into one file: **no** — BASELINE is the pin, SEAL_COMMIT is the moving endpoint. The test needs both literals visibly in-tree at different times (BASELINE stable across the whole window; SEAL_COMMIT flipping from "HEAD"/BASELINE at amendment-commit time to the final SHA at seal-commit time). Collapsing would require the endpoint to either come from git (breaks determinism) or overwrite the pin on seal (destroys the audit trail).
- Collapse `tests/SEAL_COMMIT` + `seals/SEAL_COMMIT.*`: **yes, in principle**, because only hands-off-lifecycle and telegram-interface have the narrative sidecar at all, and `tests/SEAL_COMMIT` holds just the SHA. But they serve different audiences — the tests one is machine-consumed, the seals one is human-readable multi-paragraph narrative. Keeping them separate at different paths is cleaner than keeping them separate via YAML frontmatter in one file.

**Minimum sufficient shape:** 2 files per sealed component — the test constant + the sidecar. The narrative sidecar (`seals/SEAL_COMMIT.*`) is optional documentation, and only `hands-off-lifecycle` actively uses it as the canonical amendment-cycle log (998 lines spanning 21 amendments — that is where the ritual's history lives).

### 2.3 allowed_prefixes / allowed_files tuples

Each seal-diff test carries a hand-maintained tuple of admitted path prefixes. Looking at `cost-governance/tests/test_no_sealed_amendments.py` lines 108–124 after amendment #18, the tuple grew from 4 entries to 14. Of those 14:

- **Universal** (in *every* component's tuple eventually): `docs/rebuild/plans/`, own-component dir, `data/`.
- **Per-amendment**: each amendment's partner components get added reactively.
- **Per-amendment docs**: the plan doc, the edited `docs/odd-in-pos.md`, occasionally `CLAUDE.md`.

**The reactive-widening pattern is the #1 source of corrective commits.** Amendment #13 shipped as a two-commit pattern for exactly this reason (`9e3776b` widened the cost-governance tuple with `hands-off-lifecycle/` after `2654053` shipped); amendment #18 shipped with three commits for the same reason (`8bdf194` cross-referenced the seven brief-owning components after `4c385ed` shipped). This pattern is entirely pre-computable.

**Pre-computability analysis:** for a multi-component amendment with set C of touched components, each component c ∈ C needs to admit:
1. Its own dir.
2. `docs/rebuild/plans/` (universal).
3. `data/` (universal — observability runtime artefacts).
4. `hands-off-lifecycle/` (always touched — the cross-cutting seal counterpart rides on every amendment).
5. The top-level dir of every other c' ∈ C (multi-component cross-reference).
6. `docs/rebuild/components/<c'>/` for every c' ∈ C whose doc dir is touched.
7. Any `docs/odd-*.md` or repo-root doc the amendment declares.

Items 1–6 are **100% derivable from the component set C plus universal conventions**. Item 7 is the only thing a human needs to declare, and only when the amendment actually touches those files.

**Universal-path proposal:** admitting `docs/rebuild/plans/`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/odd-*.md`, `CLAUDE.md`, and `data/` globally by default across every component's seal-diff test would remove roughly **one tuple-edit per amendment**. Trade-off: this widens every component's *theoretical* drift surface, but the admitted paths are docs/plan/artefact paths that cannot violate the sealed-component invariant — no runtime behaviour lives there. This is a safe widening.

### 2.4 Multi-component amendment cost

Amendment #18 touched 9 components for bookkeeping to land 7 source changes + 1 doc rewrite (call it 8 productive units). The bookkeeping touched 5 × `tests/test_*.py`, 5 × `tests/SEAL_COMMIT`, 5 × second-pass tuple widenings (corrective commit), 1 × narrative append. That's 16 bookkeeping touches to support 8 productive changes — the exact 1.3–2× ratio the prompt named, and in the worst case (post-corrective) closer to 2.75× as I calculated in §2.1.

**Manifest proposal:** a single top-level file (e.g. `.amendment/manifest.yaml` created per amendment, deleted after) declaring:

```yaml
amendment: 18
number: 18
slug: delete-method-in-brief-dispatch-docs
components: [primary-persona-loader, session-resilient-orchestrator,
             graceful-degradation, observability-aggregator,
             cost-governance, scope-of-work, objective-tracker,
             orchestrator, hands-off-lifecycle]
baseline: e8f704c
extra_allowed_files: [docs/odd-in-pos.md]
plan: docs/rebuild/plans/delete-method-in-brief-dispatch-docs.md
```

A `pos-amend apply` tool reads the manifest, propagates BASELINE advances to every sealed component in `components`, extends each component's `allowed_prefixes` with the cross-product of top-level partners plus every `docs/rebuild/components/<c>/` dir, and extends `allowed_files` with `extra_allowed_files`. At seal time, `pos-amend seal <sha>` flips every sidecar to the new SHA and appends the narrative block. The human writes the plan, the code, the commit message. The tool writes the bookkeeping.

### 2.5 Plan / research / seal-narrative doc proliferation

Current state for amendment #18:
- **Plan doc** (`docs/rebuild/plans/delete-method-in-brief-dispatch-docs.md`, 302 lines): authored before code.
- **No research doc** — #18 is trivial enough.
- **Seal narrative append** (~70 lines to `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`): authored at seal time.
- **Commit messages** (3 × long-form): each re-summarises the amendment.

**Duplication:** the seal narrative block is roughly 60% derivable from the commit message + the manifest (amendment slug, touched components, BASELINE advance, seal SHA). The remaining 40% is the WHY — the intent-layer prose that the plan doc already contains.

**Proposal:** have the `pos-amend seal` command auto-assemble the narrative block from (plan-doc intent-section + amendment commit message subject + manifest components + SHA pair), leaving the human to edit-in nuance if desired. This saves ~50 lines of re-stated prose per amendment, keeps the narrative's canonical location (the `seals/SEAL_COMMIT.*` file), and lets the intent live in exactly one place (the plan doc).

Small amendments (like #14 — skip-launchctl-dead-code-removal, single-component, no cross-reference) arguably don't need a separate plan doc at all. The commit message's body paragraph *is* the plan. **Recommend: a plan doc is required if (components > 1) OR (lines changed > 100); otherwise the commit message body stands in for the plan.** This matches the plan-before-code CDC's intent (non-trivial amendments get a plan artefact on disk) without forcing 100-line plan docs for 3-line deletions.

### 2.6 The empty-window-then-advance pattern

From amendment #18's commit messages:
> SEAL_COMMIT sidecars set to e8f704c at this commit (matching BASELINE, per amendment #17 / #13 pattern: empty-diff at amendment-commit time; follow-on chore(seals) commit pins SEAL_COMMIT to the amendment SHA).

This works because during the amendment commit, `BASELINE..SEAL_COMMIT = BASELINE..BASELINE = empty`, so the allowed-prefix check trivially passes. The seal commit then advances SEAL_COMMIT to the amendment SHA, narrowing the window to only the amendment's surface.

This is **correct and defensible**. The only friction is that each sealed component's sidecar needs to be individually pinned to BASELINE at amendment time, then individually re-pinned to the amendment SHA at seal time. With the `pos-amend` tool, this becomes two tool invocations (`pos-amend apply` sets all sidecars to BASELINE; `pos-amend seal <sha>` advances them all to the seal SHA). No change to the pattern itself; just mechanisation of the file edits.

**Do not collapse the two-commit structure** — the separation (amendment = the work, seal = the proof that tests pass with the diff window narrowed) is the audit trail the prompt flagged as non-negotiable.

---

## 3. Proposed streamlinings (leverage-ordered)

### 3.1 **[HIGHEST LEVERAGE] `pos-amend` CLI driven by per-amendment manifest**

**What changes:** a new tool under e.g. `tools/pos-amend/` (Python, stdlib-only, no runtime deps outside what's already in the tree). Two subcommands:
- `pos-amend apply <manifest.yaml>` — reads the manifest, edits every affected component's `BASELINE` constant + `tests/SEAL_COMMIT` sidecar + tuple extensions; runs all seal-diff tests in dry-run mode and reports any missing admissions before the commit.
- `pos-amend seal <sha>` — reads the last-applied manifest (cached in `.amendment/`), flips every sidecar to `<sha>`, appends the narrative block to `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`, and runs all seal-diff tests to verify green.

**What's preserved:**
- Per-component `BASELINE` literal in each test file (reviewable in-tree).
- Per-component `tests/SEAL_COMMIT` sidecar (reviewable in-tree).
- Two-commit amendment/seal structure (human does the commits, tool just edits the files).
- AC ↔ test mapping (tool touches no test logic, only constants/tuples).
- Narrative sidecar on hands-off-lifecycle (tool appends the block; human can edit before committing).

**Structural migration path:**
1. Write the tool in an amendment of its own (call it #22). No existing component changes.
2. Author one test-drive amendment using the tool, alongside an old-style backup procedure, to verify the tool produces byte-identical output to a hand-rolled amendment.
3. Adopt the tool as the default from the next amendment onward.

**Trade-offs:** adds ~300–500 LOC of ritual tooling. Introduces a new file class (the manifest). If the tool has a bug, an amendment could ship with wrong tuples and the seal-diff test would catch it — the tool's bugs are detectable, but corrective commits become tool-bugs rather than human-oversights. Net: bug-class shifts from reactive to deterministic.

**What this commits to:** the manifest schema becomes an artefact the project maintains. Changing the manifest shape would itself require an amendment. This is a worthwhile commitment — the schema is exactly the scope-declaration the amendment CDCs already encourage humans to articulate up-front.

### 3.2 **Universal admitted paths**

**What changes:** every component's seal-diff test `allowed_prefixes` implicitly admits the universal set:
```python
UNIVERSAL_ADMITTED_PREFIXES = (
    "docs/rebuild/plans/",
    "docs/rebuild/FUTURE_IDEAS.md",
    "docs/odd-methodology.md",
    "docs/odd-in-pos.md",
    "CLAUDE.md",
    "data/",
)
```
Imported from a shared `tests/seal_helpers.py` module (itself sealed against unauthorised edits by its own presence in every component's tuple). Each per-component tuple then carries only the **non-universal** admissions.

**What's preserved:** per-component `allowed_prefixes` still reviewable in each test file; the universal set is pulled in explicitly by name; each component can opt out of the universal set if needed (by not importing it).

**Migration path:** one seal-retrofit amendment touching all 10 sealed components. Non-trivial but mechanical.

**Trade-offs:** widens every component's theoretical drift surface by the universal set. These paths are documentation + plan artefacts + runtime-generated data, not source; there is no sealed-component invariant violation that could hide there. Safe.

**What this commits to:** the universal set becomes a canonical constant. Adding to it requires an amendment. Luke would need to approve first additions (e.g. `docs/rebuild/components/`? I'd argue no — the component-doc dirs should stay per-amendment, because they *do* get touched by multi-component amendments in informative ways).

### 3.3 **Conditional plan-doc requirement**

**What changes:** codify in CLAUDE.md or the plan-before-code CDC doc that a plan doc is required if (components > 1) OR (lines > 100); otherwise, the commit message body substitutes.

**What's preserved:** the plan-before-code intent — non-trivial amendments get a plan artefact on disk. Trivial amendments (like #14, #15 pattern) don't need 302-line plan docs the commit message duplicates 80% of.

**Migration path:** one CLAUDE.md edit + one CDC doc edit. No code changes.

**Trade-offs:** some amendments will be on the edge and cost 30 seconds of "does this need a plan doc?" adjudication. Acceptable.

### 3.4 **Derived seal narrative block**

**What changes:** the narrative block appended to `seals/SEAL_COMMIT.true-first-run` is assembled by `pos-amend seal` from (plan-doc `## Intent` section + commit message body + manifest components + BASELINE/SEAL pair). Human edits before committing if the auto-assembled version misses a subtlety.

**What's preserved:** the narrative itself, its canonical location, the audit trail of every amendment.

**Migration path:** implement in `pos-amend seal`. No existing narrative edits.

**Trade-offs:** risk of the derived narrative losing nuance the human would have added. Mitigated by the edit-before-commit step. Over time, the manual edits decrease as the template gets tuned.

### 3.5 **Dry-run seal-diff pre-flight**

**What changes:** `pos-amend apply --dry-run` simulates the seal-diff test against the currently-staged changes (before the commit lands), reports missing prefix-widenings, and exits non-zero if anything's wrong.

**What's preserved:** the seal-diff invariant itself.

**Migration path:** part of the `pos-amend` tool.

**Trade-offs:** catches what corrective commits catch, but at build-time instead of post-commit. Fewer corrective commits = cleaner history.

---

## 4. Rejected proposals

- **Eliminate per-component `BASELINE` literal, compute from git.** Rejected: the pin is the invariant. A computed BASELINE breaks determinism (tree state at test time drifts) and destroys reviewability.
- **Merge `tests/SEAL_COMMIT` + `seals/SEAL_COMMIT.*` into one YAML file.** Rejected: separation of machine-read (short) vs human-read (narrative) is clean. Different paths keep the purposes legible.
- **Auto-generate the plan doc from a template.** Rejected: the plan doc is where intent lives. Templating would hollow it out. The only mechanisation should be narrative-block derivation at seal-time (§3.4).
- **Collapse the amendment + seal into one commit.** Rejected: the prompt named this a non-negotiable; I agree — the two-commit structure is the audit proof.
- **Pre-compute universal `docs/rebuild/components/<comp>/` cross-reference into every tuple by default.** Rejected: over-admission. Only the partners *in the current amendment* should be admitted. The manifest encodes this cleanly per amendment.
- **Drop the narrative sidecar entirely.** Rejected: `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` is the canonical ritual history — 998 lines across 21 amendments of institutional memory. It is high-value.
- **Replace seal-diff test with a pre-commit hook.** Rejected: the seal-diff test runs in CI / pytest, is reviewable in git history, and its BASELINE constant is the in-tree invariant. A pre-commit hook would be evadable and wouldn't land in the git audit trail.

---

## 5. Recommended next step

**Author amendment #22 as the `pos-amend` tool introduction + one universal-paths retrofit** as a bundled multi-component amendment. Reason:
- The tool itself is the leverage point. Every streamlining proposal downstream hinges on the tool existing.
- The universal-paths retrofit is a single multi-component amendment that benefits from the tool on its very first invocation (it touches every sealed component for the `allowed_prefixes` import).
- Bundling the two creates a self-demonstrating amendment: the tool ships in commit 1, and the universal-paths retrofit uses the tool to propagate its own BASELINE advances in commit 2 + seal commit 3.

The test-drive from §3.1 becomes implicit: the universal-paths retrofit *is* the test drive. If the tool produces a clean amendment that passes all 10 sealed components' seal-diff tests, the tool is validated.

**Estimated cost:** one dispatched agent working for ~4–8 hours — the tool is stdlib-only, well-scoped, with a precisely-defined input schema (manifest) and output space (file-edit operations bounded to `BASELINE`, `SEAL_COMMIT`, tuple literals). Plan doc would run 200–300 lines; research doc probably not needed.

If the answer to "is this worth doing now?" is uncertain, **keep as-is and revisit after amendments #22–25 land**. The ritual cost is real but tolerable: ~11 bookkeeping files per multi-component amendment is a fixed tax, not a growing one. If amendment velocity stays at ~2/week, the tool saves ~1–2 hours/week; at ~1/month, it saves ~15 minutes/month and may not be worth the investment. Luke should weigh expected amendment pace against the tool's one-time build cost.

---

## 6. Open questions for Luke

1. **Is the tool's investment worth it at current amendment pace?** 21 amendments in roughly the last 30 days suggests yes; if the pace slows, the break-even moves out.
2. **Manifest schema — YAML vs. TOML vs. Python dict in a `.amendment.py` module?** YAML is readable; Python lets the manifest encode logic (e.g. computed allowed paths). I lean YAML for the first version; Python is over-engineering until a need surfaces.
3. **Should the manifest file be committed, or deleted after the seal commit?** Two options: (a) commit it into `docs/rebuild/plans/<slug>-manifest.yaml` alongside the plan — becomes part of the audit trail; (b) scratch-file under `.amendment/`, deleted after seal. I lean (a) — the manifest is the formalised scope declaration, and committing it alongside the plan is symmetrical with how plans work. But (a) adds one more file to the commit; (b) is cheaper but loses an auditable artefact.
4. **Universal-paths scope — does `docs/rebuild/components/` belong?** I argued no (keep per-amendment); Luke's ruling needed. Similarly `first-run-inventory.yaml` is universal in hands-off-lifecycle's H19 set but nowhere else; would the universal list include it?
5. **Narrative-block destination — stays in `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` forever, or migrate to a new top-level `AMENDMENT_LOG.md`?** The current location is a historical accident (first narrative-owning component happened to be hands-off-lifecycle). A top-level log would be more discoverable but would need its own sealing story. Probably not worth a separate amendment; keep where it is.
6. **Conditional-plan-doc thresholds — 1 component and <100 lines?** Thresholds are arbitrary; Luke's feel for them matters more than my proposed numbers.
7. **Corrective-commit policy after the tool lands.** If the tool's dry-run prevents the amendment #18-style corrective commit, do we still allow correctives at all — or make the dry-run green a hard prerequisite for the amendment commit? I'd argue the latter is stricter but also likelier to catch bugs before the git audit trail acquires them.

---

*End of research document.*
