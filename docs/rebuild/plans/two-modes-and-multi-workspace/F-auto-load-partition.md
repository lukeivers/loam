# Sub-plan F — Dev-mode auto-load partition

**Status:** authored 2026-04-25. Research-and-planning only. **Dev-
discipline plan** — NOT a sealed-component amendment.

**Master plan:** `MASTER.md`.

---

## 1. Summary / TLDR

F declares the partition between always-loaded artefacts (NORMAL USE
+ DEV MODE) and dev-only auto-loaded artefacts (DEV MODE only). The
partition is owned by a small machine-readable manifest (path TBD;
recommended `docs/rebuild/dev-mode-manifest.yaml`) that sub-plan B's
selector consumes. Sub-plan B is the mechanism; F is the data.

The partition mirrors the locked owner rulings 4–6:

**Always loaded (NORMAL USE + DEV MODE):**

- Runtime harness: every Phase 1–4 sealed component's source surface
  (memory-system, scope-of-work, primary-persona, objective-tracker,
  orchestrator, graceful-degradation, observability-aggregator,
  self-upgrade, safety-layer, reversibility-primitive,
  cost-governance, self-correction, workspace-bootstrap,
  hands-off-lifecycle, telegram-interface).
- `docs/rebuild/VALUE_PROPOSITION.md` (still tracker-root-load-bearing
  per amendment #39 + sub-plan E's preserved value-prop loader path).
- `CLAUDE.md` (the always-load fragment).
- End-user-facing help docs (TBD path; sub-plan F catalogues them).
- Basic settings / configuration scaffold (workspace-bootstrap manifest
  surface, `<workspace>/.pos/` config files).

**Dev-only auto-loaded (DEV MODE only):**

- `tools/pos-amend/` (CLI, manifests, BASELINE conventions, SEAL_COMMIT
  sidecars, plan-doc + dispatch templates).
- `docs/rebuild/plans/` (every plan doc; in-flight amendment-N plans).
- `docs/rebuild/components/<name>/proposal.md` and seal narratives
  (component-scoped artefacts).
- `docs/rebuild/spec/pos-v2-objectives-spec.md` and
  `docs/rebuild/spec/pos-v2-rebuild-proposal.md`.
- `docs/odd-methodology.md` and `docs/odd-in-pos.md`.
- `docs/rebuild/STATE.md`.
- `docs/rebuild/FUTURE_IDEAS.md` (the dev CDCs live here per the
  parking convention; they migrate to the future Dev/SDLC plugin per
  Idea 3).
- `docs/rebuild/FUTURE_IDEAS_DRAFT.md`.
- The dev-extension fragment of `CLAUDE.md` (sub-plan B's AC.B3
  surface).

---

## 2. Spec-objective placement

§2.5 framing: **No spec v1.x objective names "what auto-loads in dev
mode."** This is dev-discipline territory — a partition declaration
that exists to drive sub-plan B's selector. The work is operational
developer-tooling: a YAML / Python file enumerating paths, plus
tests that check the partition is internally consistent (no path
appears in both lists; no path is missing if it should be present).

If F ends up requiring sealed-component edits at design time, halt
— the partition is wrong.

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage

F leans on the same SessionStart hook surface sub-plan B leans on.
The partition manifest is consumed by B's selector; it is not itself
a Claude-leveraging primitive.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden?*

Yes — the persona's "what should I read at session-start" question
is answered by the partition file rather than by reading
`CLAUDE.md`'s session-start section + applying domain knowledge.

**Harness test.** *Does this add to the toolkit the primary persona
can draw from?*

Yes — the partition is a toolkit primitive: future contributors that
care about "is this a dev artefact" (e.g. a search-suppression layer
that hides pos-amend results from end-user sessions) compose against
the same manifest.

### Lens 3 — ODD authoring

ACs are outcome-shaped; method (the manifest's exact format and
location) is the builder's call.

---

## 4. Acceptance criteria (AC.F1–AC.F5)

### AC.F1 — Partition manifest enumerates every path

A machine-readable partition manifest at a stable path (recommended
`docs/rebuild/dev-mode-manifest.yaml`, but builder's call) declares two
disjoint sets: `always_loaded` and `dev_only`. Every path under the
declared roots is one or the other.

**Test shape:** load the manifest; assert the two sets are disjoint
(intersection empty); assert every entry is a stable path (not a
glob) OR a glob whose match-set is well-defined (under tests).

**Maps to:** AC.PO.2.

### AC.F2 — Sub-plan B's selector reads the partition

Sub-plan B's selector (AC.B1's `compute_session_mode` or its data-
plane sibling) reads the partition manifest to select the corpus.
Mode `"user"` → `always_loaded` set; mode `"dev"` →
`always_loaded ∪ dev_only`.

**Test shape:** unit test in B's test tree that mocks the partition
manifest with a tiny fixture; assert the selector returns the
expected paths for each mode.

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.F3 — No always-loaded artefact references a dev-only artefact

The session-start corpus discovery (sub-plan B's AC.B4 + amendment
#32's `discover_baseline_corpus`) does not require any path under
`dev_only` to function in NORMAL USE. Specifically: `VALUE_PROPOSITION.md`
must NOT reference `docs/odd-methodology.md`, `docs/rebuild/STATE.md`,
or any dev-only path in a way that would be load-bearing for a
non-dev session. (Today the `CLAUDE.md` always-load fragment may
reference dev-only docs; F's amendment is to scrub those references
out of the always-load surface.)

**Test shape:** static check — every Markdown reference (link,
backtick-quoted path) inside any `always_loaded` artefact is itself
an `always_loaded` path or an external URL.

**HALT TRIGGER:** if scrubbing the references requires changes to
sealed-component-owned docs (e.g. a sealed component's README), halt
and surface — this might be a sealed amendment in disguise.

**Maps to:** AC.PROG.2 + AC.PO.1.

### AC.F4 — Dev-only artefacts inside always-loaded paths are explicitly tagged

Some dev-only artefacts live inside otherwise-always-loaded directories
(e.g. `tools/pos-amend/` lives under `tools/`, but `tools/` may host
end-user CLIs in the future). The manifest accepts path globs OR
sub-tree exclusions to disambiguate.

**Test shape:** unit test of the manifest parser that handles a glob
with an exclusion (e.g. `tools/**` minus `tools/pos-amend/`).

**Maps to:** AC.PO.2.

### AC.F5 — Partition is auditable

A `tools/loam-mode/audit` (or similar) command lists every path in
each set, prints any orphans (paths under the declared roots not
covered by either set), and exits non-zero if orphans exist or the
two sets intersect.

**Test shape:** integration test in tools/loam-mode/tests/ that runs
the audit against a fixture; asserts exit-zero on a clean fixture and
non-zero on a dirty one.

**Maps to:** AC.PO.2.

---

## 5. Out of scope

- Per-file fine-grained mode selection ("this method is dev, that
  method is user"). Mode is per-path.
- Auto-classifying paths via heuristic. Locked owner ruling 4 — no
  heuristic; the manifest is owner-authored.
- Mode propagation to spawned subprocesses (e.g. `pos-amend` running
  in DEV MODE knowing the parent session was DEV MODE). Subprocesses
  inherit env vars; that's enough.
- Telemetry on which paths get read in which mode. Not in v1.

---

## 6. Halt triggers

1. **AC.F3's reference-scrubbing requires sealed-component edits.**
   Halt and surface; the partition or the always-load surface is
   wrong.
2. **The partition discovers a circular dependency** (e.g. dev-only
   files needed for non-dev startup — master halt trigger 3). Halt
   and revise.
3. **The owner-authored partition disagrees with the proposed
   set above.** Halt; the master plan's locked rulings 4–6 list is
   the source of truth, but discovery during F may surface a path
   that needs categorisation. Surface to owner.

---

## 7. Bookkeeping

Dev-discipline plan; no `pos-amend` manifest. The work lives at:

- `docs/rebuild/dev-mode-manifest.yaml` (the partition data — recommended).
- `tools/loam-mode/` (B's selector + F's audit; method-level).

If F is split into research + plan + audit-tool: that's three plan
docs (B's selector + F's manifest + F's audit). Recommendation: one
sub-plan (this one) covers the manifest + audit; B owns the selector.

---

## 8. Dispatch-time additions

When F's brief is drafted:

- WD: canonical.
- F runs after A and E land (A supplies `dev_intent`; E supplies the
  classifier; F supplies the corpus).
- Plan-before-code.
- ODD §2.4 + §2.5 audit.
- No `git commit --amend`.

---

## 9. Lens-2 trace blocks

| AC | AC.PO.1 | AC.PO.2 |
|----|---------|---------|
| AC.F1 | Partition is structural; persona doesn't translate ad hoc. | Manifest is a toolkit primitive. |
| AC.F2 | Selector reads the partition; persona reads the selector's output. | Selector + manifest compose. |
| AC.F3 | NORMAL USE never resolves a broken reference. | Reference-integrity primitive. |
| AC.F4 | Disambiguation rules are documented and tested. | Glob-exclusion shape is reusable. |
| AC.F5 | Audit catches drift before the user does. | Audit primitive — toolkit. |

---

## 10. Decision register (sub-plan-local)

| Code | Question | Recommendation |
|------|----------|----------------|
| D-F.1 | Manifest format: YAML, JSON, Python, TOML? | YAML. Matches existing pos-v2 conventions (manifest.yaml, memory.yaml, etc.). Schema is small; YAML's readability wins. |
| D-F.2 | Manifest path: `docs/rebuild/dev-mode-manifest.yaml` or `tools/loam-mode/manifest.yaml` or `<workspace>/.pos/dev-mode-manifest.yaml`? | `docs/rebuild/dev-mode-manifest.yaml`. The manifest is design data, lives with the design corpus, edited via PRs not by the operator. |
| D-F.3 | Should the manifest carry per-path rationale ("why is this dev-only")? | No, in v1. Rationale lives in the master plan. Adding it would inflate the manifest without adding mechanical value. Reconsider if a future contributor needs it. |
| D-F.4 | Should the partition include `seals/` directories? | Yes, dev-only. Seal narratives are dev-discipline artefacts. |
| D-F.5 | Should `bootstrap.yaml` (the workspace's own composition manifest) be always-loaded or dev-only? | Always. It's the workspace's runtime config, not dev tooling. |

---

## 11. Builder freedom

Builder chooses: the manifest format details (key names beyond the
two sets), the audit command's exact output shape, the glob library
(stdlib `pathlib` vs `fnmatch` vs `pathspec`).

---

## 12. Test register

| AC | Suggested test file | Suggested test function |
|----|---------------------|--------------------------|
| AC.F1 | `tools/loam-mode/tests/test_partition_manifest.py` | `test_AC_F1_partition_disjoint` |
| AC.F2 | `tools/loam-mode/tests/test_selector_partition.py` | `test_AC_F2_selector_reads_partition` |
| AC.F3 | `tools/loam-mode/tests/test_partition_references.py` | `test_AC_F3_always_loaded_no_dev_refs` |
| AC.F4 | `tools/loam-mode/tests/test_partition_manifest.py` | `test_AC_F4_glob_with_exclusion` |
| AC.F5 | `tools/loam-mode/tests/test_partition_audit.py` | `test_AC_F5_audit_finds_orphans` |

---

## 13. Asymmetric observations

1. **The partition is data, not code.** Storing the partition as a
   YAML file rather than a Python module means a future contributor
   can rotate paths without a code review on a method change. Effort:
   trivial. Leverage: medium-high (cuts code-review noise on every
   future plan addition).

2. **The audit (AC.F5) is the asymmetric protection.** It catches
   drift before the operator hits a missing-reference at session-
   start. Effort: low (one walk over the workspace tree). Leverage:
   high (every future amendment that adds files gets free
   classification-correctness checking).

3. **Inverse-asymmetric: per-method classification.** Tempting to
   say "this function in this module is dev-only," but
   path-granularity is sufficient and the per-method shape is medium
   cost (parser, AST analysis) for low leverage (no real use case
   today). Dropped.

4. **Inverse-asymmetric: cross-amendment drift detection that auto-
   updates the partition.** Tempting because it would close the gap
   automatically when a new amendment adds a file, but the manifest
   is owner-authored per design (the partition is intent, not
   discovery). Auto-update would erode that property. Dropped.
