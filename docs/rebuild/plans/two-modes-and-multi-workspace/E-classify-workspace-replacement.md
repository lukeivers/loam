# Sub-plan E — `classify_workspace` replacement

**Status:** authored 2026-04-25. Research-and-planning only. Sealed-
component amendment to `workspace-bootstrap`. Spec objective: re-
extension of amendment #39 (the dev-marker source-of-truth changes
shape).

**Master plan:** `MASTER.md`.

---

## 1. Summary / TLDR

Amendment #39's `classify_workspace(workspace_root)` returns
`"pos-v2-dev"` when `docs/rebuild/VALUE_PROPOSITION.md` is present at
the workspace root, `"user"` otherwise. Locked owner ruling 1 (single
GitHub-distributed repo) breaks that heuristic — every fresh-clone
end user has `VALUE_PROPOSITION.md` and is misclassified as
`"pos-v2-dev"`.

E replaces the heuristic with a read of the dev-intent answer (sub-
plan A's resolver). Mapping:

- `read_dev_intent(workspace_root) == "yes"` → `"pos-v2-dev"`.
- `read_dev_intent(workspace_root) == "no"` → `"user"`.
- `read_dev_intent(workspace_root) == "absent"` → `"user"` (defensive
  default per locked owner ruling 4 — "shouldn't happen but defensively").

The downstream consumer (the seed's `value-prop` source loader) is
unchanged: dev workspaces still read `docs/rebuild/VALUE_PROPOSITION.md`,
non-dev workspaces still read `<workspace>/value-prop.md`. Only the
classification SOURCE OF TRUTH moves.

This sub-plan is the smallest in the programme — one function changes,
one set of tests adds.

---

## 2. Spec-objective placement

Sealed-component amendment to `workspace-bootstrap`. Spec objective:
amendment #39's existing contract (the seed seeds the workspace's
tracker tree from a value-prop source). The classification is the
gate that decides which value-prop source. E rotates the gate's
input source from `is_file()` to `read_dev_intent()` while preserving
the gate's contract.

§2.5 forward+reverse audit per the standard cycle.

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage

E composes on sub-plan A's storage resolver. No new Claude primitive.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden?*

Yes. `VALUE_PROPOSITION.md` is shipping in every clone (locked owner
ruling 1); using its presence as a dev-marker translates to "the file
is a dev-marker AND a value-prop content source," which is two
meanings the persona has to reconcile. After E, the file is
content-only and the dev-marker is the user's own answer.

**Harness test.** *Does this add to the toolkit the primary persona
can draw from?*

Yes — `classify_workspace` becomes a deterministic dev-mode signal
the persona's downstream contributors can compose on (sub-plan B's
selector reads it; sub-plan F's partition gates on it).

### Lens 3 — ODD authoring

ACs are outcome-shaped; method (the exact import path of the
`read_dev_intent` resolver, the exact mapping function shape) is the
builder's call.

---

## 4. Acceptance criteria (AC.E1–AC.E5)

### AC.E1 — `classify_workspace` returns "pos-v2-dev" iff dev_intent is "yes"

Given a workspace fixture where `read_dev_intent` returns `"yes"`,
`classify_workspace(workspace_root)` returns `"pos-v2-dev"`.

**Test shape:** unit test in `workspace-bootstrap/tests/test_classify_workspace.py`
that mocks `read_dev_intent` to return `"yes"` and asserts the return
value.

**Maps to:** AC.PO.1 + AC.PO.2 + AC.PROG.3.

### AC.E2 — `classify_workspace` returns "user" when dev_intent is "no"

Given `read_dev_intent` returns `"no"`, `classify_workspace` returns
`"user"`.

**Test shape:** unit test mirror of AC.E1.

**Maps to:** AC.PO.1 + AC.PO.2 + AC.PROG.3.

### AC.E3 — `classify_workspace` returns "user" when dev_intent is "absent"

Given `read_dev_intent` returns `"absent"` (no contract field set
yet), `classify_workspace` returns `"user"` — defensive default per
locked owner ruling 4.

**Test shape:** unit test with the absent fixture.

**Maps to:** AC.PO.1 + AC.PO.2 + AC.PROG.3.

### AC.E4 — `classify_workspace` does NOT inspect `VALUE_PROPOSITION.md`

For the purpose of classification, `classify_workspace` does not call
`Path.is_file()` (or any other read) on
`docs/rebuild/VALUE_PROPOSITION.md`. The function's body's I/O is
limited to `read_dev_intent`'s call (which itself reads sub-plan A's
storage location).

**Test shape:** static AST check OR a fixture where
`VALUE_PROPOSITION.md` is present AND `dev_intent` is `"no"` — assert
classification returns `"user"`. (The negative case proves the
function is reading `dev_intent`, not the file.)

**Maps to:** AC.PROG.3.

### AC.E5 — Downstream value-prop loader still reads
`docs/rebuild/VALUE_PROPOSITION.md` on dev workspaces

`load_value_prop_source` is unchanged: when the classification is
`"pos-v2-dev"`, it reads `docs/rebuild/VALUE_PROPOSITION.md` (or the
override). The decoupling is between classification source and
content source.

**Test shape:** existing amendment #39 tests (AC39.1, AC39.5) should
continue to pass; the test that needs amendment is the
classification-input fixture (it now seeds `dev_intent` rather than
file presence).

**HALT TRIGGER:** if any AC39.x test other than the classification-
input fixture needs amendment, surface — that's a #39 re-extension
needing owner approval.

**Maps to:** AC.PO.1 (preserve existing dev/user content path).

---

## 5. Out of scope

- Renaming `"pos-v2-dev"` to anything else (the classification string
  is a stable contract per AC39.x).
- Moving the value-prop loader's source path away from
  `docs/rebuild/VALUE_PROPOSITION.md`.
- Auto-detecting dev intent. Locked owner ruling 4 forbids.
- Removing `FRAMEWORK_VALUE_PROP_RELPATH` constant — the constant is
  still used by `load_value_prop_source` per AC.E5.

---

## 6. Halt triggers

1. **A pre-existing AC39.x test asserts the heuristic-based
   classification.** Halt and surface; AC39.x re-extension needs
   owner approval.
2. **`read_dev_intent` is not yet available** (sub-plan A hasn't
   landed). Halt — E depends on A. The dispatcher should land A
   first.
3. **The classifier ends up being called from a code path that runs
   BEFORE the persona contract exists** (e.g., before the persona
   scaffold runs in first-run sequence). Halt and surface; the
   classifier needs a different read path or the first-run sequence
   needs reordering.

---

## 7. Bookkeeping

`pos-amend` manifest: single component (`workspace-bootstrap`).

- `seal_test`: `workspace-bootstrap/tests/test_no_sealed_amendments.py`
- `sidecar`: `workspace-bootstrap/tests/SEAL_COMMIT`
- `frozen_baseline: false`

Universal paths: `docs/rebuild/plans/`, `CLAUDE.md`.

Narrative target:
`workspace-bootstrap/seals/SEAL_COMMIT.classify-workspace-dev-intent`.

---

## 8. Dispatch-time additions

When the brief is drafted:

- WD: canonical.
- A must have landed (sub-plan A's `read_dev_intent` exists in
  primary-persona's surface).
- Plan-before-code.
- ODD §2.4 + §2.5 audit.
- No `git commit --amend`.

---

## 9. Lens-2 trace blocks

| AC | AC.PO.1 | AC.PO.2 |
|----|---------|---------|
| AC.E1 | Dev users get dev classification structurally. | Resolver-API consumed. |
| AC.E2 | Non-dev users get user classification. | Resolver-API consumed. |
| AC.E3 | Defensive default protects pre-onboarding state. | Default is documented and tested. |
| AC.E4 | VALUE_PROPOSITION.md is content-only, not a marker. | Untangles two responsibilities. |
| AC.E5 | Existing dev/user content path preserved. | AC39.x contract unchanged. |

---

## 10. Decision register (sub-plan-local)

| Code | Question | Recommendation |
|------|----------|----------------|
| D-E.1 | Where does `read_dev_intent` live (workspace-bootstrap or primary-persona)? | primary-persona (sub-plan A's home). E imports from there. The cross-component import is one symbol; lazy-imported per amendment #40's pattern if needed. |
| D-E.2 | Should `classify_workspace` cache its read across calls in a single scaffold-run? | Yes. The first-run scaffold may call it multiple times; caching avoids redundant I/O. Method-level — builder's call. |
| D-E.3 | What if `read_dev_intent` raises (e.g., contract file unreadable)? | Map to `"absent"` (which then maps to `"user"` per AC.E3). Failure-case is fail-soft to user-mode. |

---

## 11. Builder freedom

Builder chooses: the import shape of `read_dev_intent` (top-level vs
lazy), the caching strategy, the test fixture's tmp-fs shape.

---

## 12. Test register

| AC | Suggested test file | Suggested test function |
|----|---------------------|--------------------------|
| AC.E1 | `workspace-bootstrap/tests/test_classify_workspace.py` | `test_AC_E1_classify_dev_when_dev_intent_yes` |
| AC.E2 | `workspace-bootstrap/tests/test_classify_workspace.py` | `test_AC_E2_classify_user_when_dev_intent_no` |
| AC.E3 | `workspace-bootstrap/tests/test_classify_workspace.py` | `test_AC_E3_classify_user_when_dev_intent_absent` |
| AC.E4 | `workspace-bootstrap/tests/test_classify_workspace.py` | `test_AC_E4_classify_does_not_read_value_prop_md` |
| AC.E5 | (existing AC39.x tests, unchanged in shape; classification fixture updated) | n/a |

---

## 13. Asymmetric observations

1. **One-function change, three-line replacement.** The current body
   reads `is_file()`; the new body calls `read_dev_intent` and maps.
   Effort: trivial. Leverage: closes the misclassification of every
   end-user clone.

2. **The constant `FRAMEWORK_VALUE_PROP_RELPATH` stays load-bearing**
   for `load_value_prop_source`. The decoupling is conceptual: one
   constant, two consumers, only one of them used to consume it for
   classification.

3. **Inverse-asymmetric: making `classify_workspace` a property of the
   contract.** Tempting to fold the classifier directly into
   `PersonaContract.classification`, but it would tangle persona-layer
   into workspace-bootstrap's contract. The seam-via-resolver shape
   (sub-plan A's `read_dev_intent` + this sub-plan's classifier
   wrapping it) keeps the layering clean. Dropped from this sub-plan.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left method choices to the builder. This section records
the choices made and the rationale, plus the test breakdown and
commit SHAs.

### Folded scope: path-mismatch (#39 ↔ #40) fix

Per master-plan §11.5, the path-mismatch fix folds into E because both
changes touch `tracker_seed.py`. E's AC suite extends to cover the fold:

- **AC.E.6** — `tracker_db_path_for(workspace_root)` returns
  `<workspace_root>/objective_tracker.sqlite` (workspace-rooted, not
  pos_root-rooted). Aligns with
  `primary_persona.tracker_context.tracker_db_path_for`.
- **AC.E.7** — `_run_tracker_seed` invokes `tracker_db_path_for` with
  `workspace_root`, not `pos_root`. The seed and the contributor read
  the same DB.
- **AC.E.S** — sub-plan E is single-component (workspace-bootstrap
  only). Manifest shape enforced.

The original AC.E1–AC.E5 retained as authored.

### D-build.E1 — Lazy import of `read_dev_intent`

`classify_workspace` lazily imports `read_dev_intent` from
`primary_persona.onboarding` inside the function body (not at module
load).

**Rationale:** Mirrors amendment #40's lazy-import pattern. Keeps
`tracker_seed`'s import graph acyclic against primary-persona's
loader chain. Plan §10 D-E.1 recommended this.

### D-build.E2 — No caching

`classify_workspace` performs the read-and-map on every call; no
in-process cache.

**Rationale:** Plan §10 D-E.2 recommended caching but D-build choice
is no-cache. The seed runs once per scaffold; the cost is one YAML
load. Marginal optimisation; defer to a profile-driven amendment if
ever needed.

### D-build.E3 — No defensive try/except in `classify_workspace`

`read_dev_intent` is itself fail-safe (returns `"absent"` on malformed
contracts per amendment #41 AC.A.6). `classify_workspace` simply maps
the three-value Literal to the two-value classification.

**Rationale:** Plan §10 D-E.3 said "fail-soft to user-mode";
`read_dev_intent` already enforces that. Wrapping again would dilute
the seam.

### D-build.E4 — `tracker_db_path_for` parameter rename

`tracker_db_path_for(workspace_root)` (was `pos_root`). Callers
updated:
- `_run_tracker_seed` — passes `workspace_root` (already in scope);
  `pos_root` parameter dropped from `_run_tracker_seed`'s signature
  (no longer needed for the tracker DB path).
- AC39.x test fixtures — `tracker_db_path_for(pos_root)` →
  `tracker_db_path_for(workspace)`. Mechanical, AC-preserving — the
  AC outcomes are about seed records inside the DB, not the literal
  path.

**Rationale:** Single source of truth — `primary_persona.tracker_context.tracker_db_path_for(workspace_root)`
already exists; aligning the seed surface closes the latent #39 ↔ #40
bug at the source.

### D-build.E5 — AC39 dev-fixture pre-creates persona contract with `dev_intent: yes`

AC39.1 / AC39.2 / AC39.3 / AC39.4 dev-workspace fixtures pre-create
`<workspace>/personas/primary/contract.yaml` carrying
`dev_intent: yes` BEFORE invoking `run_first_run_scaffold`. Scaffold's
`_install_persona_directory` is idempotent (AC36.3); pre-existing
contract is left alone. `classify_workspace` then reads the seeded
answer and returns "pos-v2-dev".

AC39.5 user-workspace fixtures unchanged (no contract → "absent" →
"user").

**Rationale:** Plan AC.E.5 explicitly says "the test that needs
amendment is the classification-input fixture (it now seeds
`dev_intent` rather than file presence)." Mechanical fixture update,
AC outcomes preserved.

### Test breakdown

(Filled at build completion.)

### Commit SHAs

- Amendment commit: `8b3933a44ef5dc614936975f97c1ecdd4ea667a8` —
  `feat(workspace-bootstrap): classify_workspace replacement + path-mismatch fold — sub-plan E (amendment #42)`
- Seal commit: `ad0d211d5e52b44f86d8e232e077d5ad2976bc83` —
  `chore(seals): workspace-bootstrap-classify-workspace-dev-intent — workspace-bootstrap at 8b3933a`
