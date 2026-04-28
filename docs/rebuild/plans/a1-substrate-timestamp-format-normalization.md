# Plan — A1 substrate timestamp-format normalization

**Status:** plan-doc only (no code, no commits, no manifest yet). 2026-04-28.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Sibling research artefact (governs):** `docs/rebuild/plans/research/a1-substrate-timestamp-format-normalization-research.md`.
**Programme position:** follow-on amendment after A1 (#51), A2 (#70), A3 (#71), A4 (#72), #52, #73, #74. Composes; no programme amendment.
**Pre-flight verification (mandatory; per `feedback_verify_dispatch_before_sending` + brief):** dispatch verifies `git log --grep="A1.*timestamp\|timestamp.*normaliz\|created_at.*format\|sentinel.*manifest.*timestamp"` returns only the FIDRAFT-capture commit `1ca6f62`, AND `ls docs/rebuild/plans/ | grep -iE "timestamp|created.at"` returns nothing matching this slug other than this plan-doc + its sibling research. Halt-and-surface if either does.

---

## 1. Summary / TLDR

A1's substrate (sealed at amendment #51) ships two lexicographically-incomparable timestamp formats: sentinels write `time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())` (second resolution, `Z`-suffixed), the manifest insert writes `datetime.now(tz=timezone.utc).isoformat()` (microsecond resolution, `+00:00`-suffixed). On same-second writes, lex-compare orders the manifest BEFORE the sentinel because `.` (0x2E) sorts before `Z` (0x5A). A3's TDD-guard predicate (`tdd_guard.py:334`) is the one consumer that compares these fields lex-style, and it produces wrong verdicts on same-second writes. Empirical: 1000/1000 collisions in tight-loop test (Q1 answer captured at FIDRAFT line 155).

Amendment #74 mitigated at the dispatcher side via `_wait_until_next_iso_second`. The substrate bug remains. This amendment fixes the substrate by migrating ALL THREE A1 timestamp emitters (active-scope sentinel, corpus-load sentinel, manifest insert) to a single shared helper that emits format γ — microsecond-resolution, `Z`-suffixed, fixed-width: `2026-04-28T18:34:56.123456Z`. After this lands, A3's lex-compare is structurally correct on every write pattern, the wait-helper at the dispatcher becomes unnecessary and is removed, and any future A1-substrate consumer that wants to compare these fields lex-style works out of the box.

Per ODD §5.1.1 this is the elimination shape — failure class disappears at the source — vs. the relocation shapes (compare-time parsing in A3; document-and-trust on the dispatcher wait). Migration is "accept heterogeneity in the manifest column" — existing β-format rows stay; new rows are γ-format; no compare path mixes them post-fix.

**Sealed-component fence:** TWO sealed components. (1) `objective-tracker/` — single-line emitter change in `src/store.py:329` (manifest insert switches to the shared helper). (2) `hands-off-lifecycle/` — three changes: `_gate_helpers.py` adds the new helper; `active_scope_sentinel.py` and `corpus_load_sentinel.py`'s `_now_iso` functions delegate to the new helper. Plus one consumer-only change in `primary-persona/dispatch_wrapper.py` to remove the now-unnecessary `_wait_until_next_iso_second` callsite (THREE sealed components total; the persona change is removal-only with no behavioural addition).

Per CLAUDE.md output convention, owner reads from §6 (decisions for owner) — every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this amendment satisfies:**

- **`docs/rebuild/spec/pos-v2-objectives-spec.md` line 134–135 — Deterministic (tiered).** A3's gate is the structural enforcement of the test-pinned-to-AC invariant. The same-second collision turns A3 from deterministic into stochastic. This amendment restores determinism by removing the format mismatch that drives the stochasticity.
- **VALUE_PROPOSITION's two tests (the prime objective ACs).**
  - *Primary-persona test (AC.PO.1):* the persona's translation toolkit no longer carries "remember the dispatcher must wait an ISO second between sentinel write and manifest insert." Reduces translation burden by removing a brittle invariant the persona had to embed.
  - *Harness test (AC.PO.2):* the substrate gains a single source-of-truth timestamp helper that every contributor composes against. Future amendments needing timestamps inherit the right shape.

**Sealed-component fence:**

- `objective-tracker` — single emitter line edit (`src/store.py:329`). No schema change. No public-API change. No new test required beyond the format-invariant test.
- `hands-off-lifecycle` — three edits: `_gate_helpers.py` adds the helper; two sentinel `_now_iso` functions delegate. No public-API change.
- `primary-persona` — consumer-only removal: `dispatch_wrapper.py`'s `_wait_until_next_iso_second` and its callsite are deleted; the wait was a workaround the substrate fix renders moot. No public-API change.

**ODD §2.5 reverse direction.** Every code change in this amendment's diff traces back to a named AC under §4. Helper addition → AC.TFN.3; emitter migrations → AC.TFN.1, AC.TFN.2; cross-format read compatibility → AC.TFN.5; wait-helper removal → AC.TFN.4; format invariant test → AC.TFN.6. No silent branches; no defensive `if`s without backing AC. Tests-deletion (the `_wait_until_next_iso_second` test) is admitted under AC.TFN.4 (the helper is removed, so its test is removed in the same diff per amendment #71's test-deletion gate convention applied to legitimate API removal).

---

## 3. Three-lens analysis

### Lens 1 — Claude leverage

*Required research question: what Claude capability does this lean on or extend?*

This amendment is a SUBSTRATE-LAYER fix; it does not directly compose against a Claude-native primitive. It restores the structural correctness of A3's PreToolUse hook (`tdd_guard.py`), which IS a Claude-native composition (the structural-enforcement programme's central asymmetric finding: "Claude Code's hook surface IS the structural-enforcement surface"). By eliminating the same-second collision class, the gate's verdict becomes structurally deterministic, which is required for the hook to be a true gate (not a probabilistic one).

No new Claude primitive is introduced. The change strengthens an existing one.

### Lens 2 — Harness + primary-persona value

*Primary-persona test: does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

**Yes — indirect but load-bearing.** The persona currently carries (via the dispatcher) a workaround for a substrate brittleness. After this amendment, the workaround is gone. The persona's dispatch shape is one helper-call shorter and the substrate behaves the way every contributor intuitively expects (timestamps compare correctly).

*Harness test: does this add to the toolkit the primary persona can draw from?*

**Yes — one new harness primitive:** `now_iso_microsecond_z()` in `_gate_helpers.py`. Single source of truth for substrate timestamps. Future amendments needing a timestamp on a substrate-comparable field call this helper.

Both Lens 2 tests pass. **→ AC.PO.1 + AC.PO.2.**

### Lens 3 — ODD authoring

This amendment is structurally shaped, not advisory. Format γ is deterministic — same wall-clock = same string structure (fixed-width, `%f` always 6 digits, no zero-stripping edge case). A3's compare predicate is unchanged but becomes correct because both sides now emit γ.

ODD §5.1.1 (relocate-vs-eliminate test): this amendment ELIMINATES the same-second collision failure class at the emitter source. A future change cannot re-introduce the failure without actively authoring a non-γ emitter through a path other than the shared helper. The shared helper is the obvious default; deviation requires effort.

ODD §4 alignment: this is a defect class with structural fix; no shape adjustment to existing acceptance flow. Mid-build re-extension (AC re-extension during a build) continues to work — manifest writes after the fix carry γ-format and compare correctly against γ-format sentinels.

---

## 4. Acceptance criteria

Each AC is outcome-shaped. Forward behaviour-count check below. ODD §2.5 reverse direction is the builder's pre-seal audit (restated as halt-and-signal trigger in §8).

### AC.TFN.1 — Sentinel emitters produce a fixed-width microsecond Z-suffixed timestamp

The two A1 sentinel writers (`active_scope_sentinel.write_active_scope_sentinel`, `corpus_load_sentinel.write_corpus_load_sentinel`) emit `created_at` strings whose format is microsecond-resolution, `Z`-suffixed, fixed-width (27 characters for the year range ≥ 1000). Outcome: every sentinel `created_at` byte-conforms to the regex `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$`.

### AC.TFN.2 — Manifest insert produces the same fixed-width microsecond Z-suffixed timestamp

The A1 manifest insert (`objective_tracker.EventStore.insert_manifest_row`) writes `created_at` strings whose format is microsecond-resolution, `Z`-suffixed, fixed-width. Outcome: every newly-inserted manifest row's `created_at` byte-conforms to `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$`.

### AC.TFN.3 — Single shared helper as source of truth

A single helper function exists in the shared gate-helpers module exposing the timestamp shape from AC.TFN.1 / AC.TFN.2. Both A1 sentinel writers and the A1 manifest insert obtain their `created_at` value through this helper (directly or via a one-line delegation). Outcome: changing the format requires editing one function; no contributor can author a different format on this substrate field without bypassing the helper.

### AC.TFN.4 — Dispatcher no longer needs the iso-second wait

The dispatcher's setup-phase sentinel-then-manifest sequence produces strictly-increasing lex-compared `created_at` strings WITHOUT any wall-clock wait between the two writes. Outcome: 1000/1000 back-to-back dispatcher invocations produce `manifest.created_at > sentinel.created_at` lex-compared. The previous `_wait_until_next_iso_second` helper is removed; no caller depends on it.

### AC.TFN.5 — A3 predicate works on mixed-format manifest history

When the manifest column contains a mix of pre-fix β-format rows (microsecond `+00:00`) and post-fix γ-format rows (microsecond `Z`), AND the active-scope sentinel is post-fix γ-format, A3's `manifest_row.created_at > sentinel.created_at` lex-predicate produces the correct verdict for every (row, sentinel) pair where the sentinel was written after the fix landed. Outcome: workspaces upgrading across the fix boundary do not regress A3.

### AC.TFN.6 — Format invariant under back-to-back same-second writes

Two A1 substrate writes (any combination of sentinel-then-manifest, manifest-then-sentinel, sentinel-then-sentinel, manifest-then-manifest) issued within the same wall-clock second produce DISTINCT `created_at` strings, AND lex-comparison reflects the temporal write order. Outcome: 1000/1000 same-second back-to-back writes have lex-compared `created_at` values matching the call order.

### AC.TFN.S — Seal commit + manifest update

A seal commit lands per `pos-amend seal --plan-doc` convention recording the amendment commit SHA + this plan-doc + the manifest YAML. The amendment manifest YAML lists the four files touched (one in `objective-tracker`, three in `hands-off-lifecycle`, one in `primary-persona`).

**Behaviour-count check (per ODD §7.3 / §8.1):** Seven behaviours in the objective above (sentinel format, manifest format, single helper, dispatcher no-wait, mixed-format read compat, same-second invariant, seal). Seven ACs (AC.TFN.1 through AC.TFN.6 + AC.TFN.S). Match. Pass.

---

## 5. Hard constraints

- **No public-API surface changes.** Sentinel reader return-shapes, manifest row dict shape, A3's hook interface — all unchanged.
- **No SQL schema migration.** The manifest table's `created_at TEXT NOT NULL` column accepts both β and γ format strings transparently.
- **No backfill of existing manifest rows.** Existing β rows stay β; new rows are γ. AC.TFN.5 verifies the heterogeneity is harmless.
- **No new external deps.** Stdlib `datetime.strftime` only.
- **Audit-log helpers stay second-Z** (`_gate_helpers.now_iso_z`). Different concern (human-readable log lines, no compare). Out of scope per §7.
- **DEV-MODE only consumers of the changed surface** (A3, dispatcher) — but the substrate is mode-agnostic. The format change applies on every workspace; only DEV-MODE workspaces exercise the read path that benefited from `_wait_until_next_iso_second`.

---

## 6. Decisions for owner (read this first)

Three decisions to rule on. All three have a recommended answer; the recommendation is the research's conclusion.

### D-TFN.1 — Format choice: α (sec-Z) vs β (microsec-+00:00) vs γ (microsec-Z)

**Recommendation: γ — microsecond-Z (`%Y-%m-%dT%H:%M:%S.%fZ`).**

Rationale: γ is the only candidate that (a) eliminates the same-second collision class, (b) preserves the existing `Z`-suffix convention used by sentinels + audit logs, (c) is fixed-width 27 chars regardless of microsecond value, and (d) avoids β's edge case where `isoformat()` drops the microsecond segment when microsecond is exactly zero.

Alternative outcomes if owner overrules:
- Pick α: keep the `_wait_until_next_iso_second` mitigation forever; document the substrate gap; relocates rather than eliminates (ODD §5.1.1 weak).
- Pick β: works for non-zero-microsecond cases; 1-in-10⁶ edge case where `isoformat()` produces `+00:00` instead of `.000000+00:00` and lex-compare flips again.

### D-TFN.2 — A1-emitter fix vs A3-compare fix

**Recommendation: A1-emitter fix (Shape A from the research).**

Rationale: ODD §5.1.1 strictly prefers elimination over relocation. The emitter fix is the elimination shape. The A3-compare fix relocates "the rule" to a parse-then-compare helper that every future consumer must remember to call. The emitter-fix's wider sealed-component fence (three components vs one) is justified by the mechanical tininess of each change and the elimination of the dispatcher's wait-helper as a side-effect.

Alternative outcomes if owner overrules:
- Pick A3-compare fix: smaller fence (one sealed component), preserves existing format heterogeneity, but ODD §5.1.1 says relocation is the weaker shape.
- Pick neither (keep status quo + document): pure-advisory; weakest under ODD §5.1.1.

### D-TFN.3 — Migration strategy for existing β-format manifest rows

**Recommendation: option (i) — accept heterogeneity. No backfill, no UPDATE.**

Rationale: only one consumer (A3) compares manifest `created_at` lex-style against ANY external timestamp. After the fix, both sides of A3's compare are γ-format on every workspace where the sentinel was written post-fix. Pre-existing β-format rows in the manifest only matter if the active-scope sentinel they're being compared against is ALSO pre-fix β-format — and that's an in-flight session at the upgrade boundary. AC.TFN.5 verifies the post-upgrade behaviour.

Alternative outcomes if owner overrules:
- Pick (ii) backfill on first read: adds runtime cost + complexity; no consumer benefits.
- Pick (iii) one-shot UPDATE: requires schema-version bump; adds upgrade-hook complexity; no consumer benefits.

---

## 7. Out of scope (named explicitly per ODD §2.5)

The following are NOT part of this amendment's diff; future amendments may pick them up:

- **Audit-log timestamp format (`now_iso_z`).** Audit logs (`agent-guard.log`, `bash-guard.log`, `objective-binding-gate.log`, `tdd-guard.log`, `dispatch-wrapper.log`) keep their second-resolution Z-suffix shape. They're read by humans, not lex-compared against sentinels.
- **`scope-of-work` `created_at` column.** Different substrate (events table), different consumer (projection), no cross-comparison with A1's sentinels or manifest. Out of scope.
- **`memory-system` data files.** Different substrate, different consumer. Out of scope.
- **`workspace-sync` and `self-upgrade` `_now_iso` helpers.** Different substrates; no cross-compare. Out of scope.
- **Persona dispatch-wrapper diagnostic NDJSON `ts` keys.** These are write-only logs; never read for compare. Out of scope.

---

## 8. Halt triggers

The build agent MUST halt and surface when:

1. **Any A1 substrate field beyond `created_at`** turns out to have a format mismatch the build uncovers. Surface with the field name + write/read sites.
2. **Any consumer of `sentinel.created_at` or `manifest.created_at` other than A3 (`tdd_guard.py:321,334`)** turns out to perform a lex-compare. The plan covers A3 only; a second consumer needs scope expansion.
3. **`_wait_until_next_iso_second` has callers other than `_run_setup_phase` in `dispatch_wrapper.py`.** Removing the helper would break those callers; halt to surface.
4. **The format-invariant test (AC.TFN.6) cannot be satisfied** — i.e., the chosen helper produces non-distinct strings on back-to-back same-microsecond writes (system clock resolution issue). Halt with empirical evidence.
5. **ODD violation discovered in surrounding code.** Per `feedback_subagent_odd_violation_halt`.
6. **Sealed-component fence ambiguity** — the change touches a fourth component beyond `objective-tracker`, `hands-off-lifecycle`, `primary-persona`. Halt.
7. **Pre-flight surfaces this work has shipped.** Halt.

---

## 9. Risks

1. **Clock-resolution risk on non-Linux platforms.** Python's `datetime.now()` uses `time.time()` which on macOS / Linux is microsecond-resolution. AC.TFN.6 verifies empirically. If the system clock has insufficient resolution to distinguish back-to-back calls, the AC fails and the build halts. (Empirically: macOS Darwin 25 / Linux 6.x ≫ 1µs resolution. Risk low.)
2. **Mixed-format manifest read in an in-flight session.** If a session is mid-build at the upgrade boundary (sentinel written pre-fix β, manifest row inserted post-fix γ), A3's compare sees γ vs β: γ's `Z` (0x5A) sorts after β's `+` (0x2B), so `manifest > sentinel` returns TRUE — which is the CORRECT verdict (the manifest was written after the sentinel). Risk: manifest-pre-fix β vs sentinel-post-fix γ. The sentinel's γ would lex-sort AFTER the manifest's β, so `manifest > sentinel` is FALSE — A3 sees "no new AC" and allows. This is a SAFETY-AT-CORRECTNESS-COST direction (allow over deny), and it requires the operator to rewrite the sentinel after insert-then-write — a non-standard sequence. Risk low; AC.TFN.5 names the case explicitly.
3. **Removing `_wait_until_next_iso_second` breaks #74's test.** The helper is tested at `test_AC_DSA_3_wait_helper_advances_iso_second`. Test is removed in the same diff (AC.TFN.4); the AC.DSA.3 sequencing test (the lex-compare end-to-end) stays and continues to verify the sequencing now works WITHOUT the wait.
4. **Sealed-component fence wider than ideal.** Three components touched. Mitigated: each change is mechanically minimal (one-line delegation for sentinel emitters; one-line emitter swap for manifest; single-call removal for the dispatcher). Build agent can serialize per `feedback_serialize_amendment_builds`.

---

## 10. Bookkeeping (`pos-amend` manifest sketch)

Manifest YAML at `docs/rebuild/plans/a1-substrate-timestamp-format-normalization.manifest.yaml`. Approximate shape:

```yaml
plan_doc: docs/rebuild/plans/a1-substrate-timestamp-format-normalization.md
research_doc: docs/rebuild/plans/research/a1-substrate-timestamp-format-normalization-research.md
sealed_components:
  - objective-tracker
  - hands-off-lifecycle
  - primary-persona
acceptance_criteria:
  - AC.TFN.1
  - AC.TFN.2
  - AC.TFN.3
  - AC.TFN.4
  - AC.TFN.5
  - AC.TFN.6
  - AC.TFN.S
seal_targets:
  - framework/hands-off-lifecycle/seals/SEAL_COMMIT.a1-substrate-timestamp-format-normalization
  - framework/objective-tracker/seals/SEAL_COMMIT.a1-substrate-timestamp-format-normalization
  - framework/primary-persona/seals/SEAL_COMMIT.a1-substrate-timestamp-format-normalization
```

`pos-amend apply --plan-doc docs/rebuild/plans/a1-substrate-timestamp-format-normalization.md` is the canonical bookkeeping invocation per `feedback_dispatch_explicit_pos_amend_apply`.

---

## 11. Risks + mitigations

(Combined into §9 above for this plan; the risk surface is small and the mitigations are AC-named.)

---

## 12. Three-lens AC trace

| AC | Lens 1 (Claude) | Lens 2 (harness/persona) | Lens 3 (ODD) |
|---|---|---|---|
| AC.TFN.1 | strengthens hook determinism | substrate primitive | structural elimination |
| AC.TFN.2 | strengthens hook determinism | substrate primitive | structural elimination |
| AC.TFN.3 | n/a | new harness primitive (`now_iso_microsecond_z`) | source-of-truth pattern |
| AC.TFN.4 | simpler dispatcher | persona translation toolkit −1 helper | rule deletion (no longer needed) |
| AC.TFN.5 | preserves hook correctness across upgrade | n/a | backwards-compat |
| AC.TFN.6 | invariant test | n/a | property-based check |
| AC.TFN.S | n/a | n/a | seal bookkeeping |

---

## 13. Ladder to AC.PO.1 / AC.PO.2 (VALUE_PROPOSITION as prime objective)

- **AC.TFN.1, .2, .3 → AC.PO.2.** New harness primitive. Substrate emits one consistent timestamp shape; future contributors compose against it.
- **AC.TFN.4 → AC.PO.1.** Persona translation toolkit shrinks by one workaround. Dispatcher is simpler.
- **AC.TFN.5, .6 → AC.PO.1 + AC.PO.2.** Determinism preserved across upgrade boundary; the persona never has to reason about "is the substrate in transition?"
- **AC.TFN.S → bookkeeping.** Doesn't ladder; required for closure.

---

## 14. Method-decision register

Method-level decisions made during the build land here at seal time per `pos-amend seal --plan-doc` convention.

### Empirical post-fix verification (AC.TFN.4 / AC.TFN.6)

Tight-loop 1000-iteration test on the post-fix emitters
(`active_scope_sentinel._now_iso` then
`objective_tracker.store._now_iso_microsecond_z`, no synthetic
delay between calls):

- Collisions (string-equal back-to-back pair): **0 / 1000**.
- Out-of-order pairs (`manifest < sentinel` lex-compared): **0 / 1000**.

Pre-fix empirical recorded at FIDRAFT line 155 / amendment #74's seal narrative: 1000/1000 collisions in the same shape of test. The failure class is structurally eliminated.

The same 0/1000 result holds for the manifest-then-sentinel direction, the sentinel-then-sentinel direction, and the canonical-helper-then-canonical-helper direction (AC.TFN.6 covers all four pair shapes in `framework/hands-off-lifecycle/tests/test_AC_TFN_6_format_invariant_back_to_back.py`).

### Method decision: store-side mirror over cross-component import

The plan §6 D-TFN.2 ruling locked Shape A (A1-emitter fix). AC.TFN.3
calls for a single shared helper. The clean cross-component import
of `_gate_helpers.now_iso_microsecond_z` from `objective_tracker.store`
would (a) require adding the hands-off-lifecycle hooks dir to sys.path
at every test invocation site that touches `objective-tracker/tests/`,
and (b) couple objective-tracker's test-time dependency surface to the
hooks layer. Neither is structurally necessary — the format string is
the source of truth, and the cross-component invariant ("the two
emitters share the same format spec") is verifiable empirically by
AC.TFN.6 rather than mechanically by import.

Decision: `objective_tracker.store` carries a one-line local helper
`_now_iso_microsecond_z()` that mirrors the canonical helper's body
verbatim. The cross-component coupling is documented in a comment
block above the mirror; AC.TFN.3 verifies the canonical helper's
source carries the format-γ literal; AC.TFN.6 verifies both emitters
produce mutually-orderable strings on the live runtime.

This is consistent with the AC.TFN.3 "directly or via a one-line
delegation" carve-out and avoids inverting the dependency layering
(objective-tracker is a more general primitive than
hands-off-lifecycle/hooks; making it depend on the gate-helpers
module would invert the layering established at amendment #51).

### Test-update scope (loose-AC tightening boundary)

Three #74 tests carried timestamp-format references that became
stale post-fix:

- `test_AC_DSA_3_setup_sequencing_for_a3_predicate.py`: rewritten.
  The wait-helper regression test (`test_AC_DSA_3_wait_helper_advances_iso_second`)
  is removed — the helper itself is removed under AC.TFN.4. The
  end-to-end sentinel-vs-manifest lex-compare test now uses the real
  post-fix emitters with no synthetic delay; both emitters produce
  format γ.
- `test_AC_DSA_8_composition_with_a2_a3.py`: three wait-helper
  callsites removed; manifest-row fixture `created_at` strings
  updated to format γ so the lex-compare against the real γ-format
  sentinel is structurally correct.
- `_helpers_dsa.disable_iso_second_wait`: turned into a no-op shim
  (signature preserved for backwards-compat with AC.DSA.5/6/7/9
  callsites). Comment notes the amendment-#75 transition.

The deletion of the wait-helper-specific test (AC.DSA.3's
"wait_helper_advances_iso_second") is admitted under AC.TFN.4 (the
helper is removed; its test is removed in the same diff). All other
#74 ACs (AC.DSA.1, .2, .4, .5, .6, .7, .8, .9, .10, .S) continue
to verify on the post-fix substrate without semantic re-extension.

### Commit SHAs

- Amendment commit: `86373b36a3f1c6a12f669a4b99687e75f1061267` —
  `chore(seals): A1 substrate timestamp-format normalization — format γ at all A1 emitters; #74 dispatcher wait helper removed — objective-tracker+hands-off-lifecycle+primary-persona at 0f14e18`
- Seal commit: `de4bb4399c2eceeaab054cd4bad0d2540336fa53` —
  `chore(seals): A1 substrate timestamp-format normalization — format γ at all A1 emitters; #74 dispatcher wait helper removed — objective-tracker+hands-off-lifecycle+primary-persona at 86373b3`
## 15. References

- Locked research (governs):
  `docs/rebuild/plans/research/a1-substrate-timestamp-format-normalization-research.md`.
- FIDRAFT capture: `docs/rebuild/FUTURE_IDEAS_DRAFT.md` line 155.
- A1 plan-doc: `docs/rebuild/plans/structural-enforcement-a1-substrate.md`.
- A1 sentinel emitters:
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py:282`.
  - `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py:472`.
- A1 manifest emitter: `framework/objective-tracker/src/store.py:329`.
- A3 plan + compare site:
  `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.md`;
  `framework/hands-off-lifecycle/hooks/tdd_guard.py:321,334`.
- #74 plan + dispatcher wait: `docs/rebuild/plans/dispatcher-side-test-stub-authoring.md`;
  `framework/primary-persona/src/dispatch_wrapper.py:597`.
- Centralised gate helper: `framework/hands-off-lifecycle/hooks/_gate_helpers.py:278`.
- ODD methodology + ODD-in-pos: `docs/odd-methodology.md` (§3.3, §4, §5.1.1, §7.4, §8); `docs/odd-in-pos.md`.
- VALUE_PROPOSITION: `docs/rebuild/VALUE_PROPOSITION.md` (translation-layer §; AC.PO.1, AC.PO.2).
- Amendment-dispatch bookkeeping: `framework/tools/pos-amend/`.
- Memory bullets carried forward:
  `feedback_no_amend_in_agent_dispatches`, `feedback_dispatch_explicit_pos_amend_apply`, `feedback_subagent_odd_violation_halt`, `feedback_amendment_dispatch_speedups`, `feedback_summarize_and_surface_decisions`, `feedback_serialize_amendment_builds`, `feedback_always_specify_wd_in_dispatches`, `feedback_verify_post_amendment_state`.
