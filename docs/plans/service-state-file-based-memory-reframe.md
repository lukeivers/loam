# service-state-file-based-memory-reframe — PATCH

**Slug:** `service-state-file-based-memory-reframe`
**Class (preliminary):** PATCH — prose-only reframe of the session-start `service_state` `memory` entry's *modelling language* (docstrings + Pydantic `Field` description + inline comments). NO wire-contract change: the `service_state` dict, the `memory` key, and the value set (`up` / `down` / `unknown` / `not_expected`) are SEALED and asserted by tests — they are preserved byte-identically. No behaviour change crosses any boundary; the only diff is the language the code uses to *model* what the `memory` entry means. D-SSMR.1 ratifies PATCH; the build halts and surfaces if the reword turns out to require any contract change (it does not — confirmed in §2).

**Predecessor:** `amend/memory-session-continuity` seal `77e3bd7` (memory-session-continuity MINOR; backfill tip `5957073`). This amendment STACKS on that branch as the BASELINE. Load-bearing sealed predecessors: `SEAL_COMMIT.m-fbm-operational-health` (the M-FBM file-based pivot — graphiti out of the runtime path; the source of the modelling correction), `SEAL_COMMIT.v0-1-2-V11-E-graphiti-probe-skip` (the `not_expected` sentinel — already the correct M-FBM signal; this amendment does NOT touch it), `SEAL_COMMIT.session-start-context-load-gate` (#32 D8 composer — `SessionPayload.service_state` field).

---

## §1 — Objective

The session-start `service_state` `memory` entry's *modelling language* describes a file-based memory store using service-liveness vocabulary ("session-level **services**", "memory **sidecar**", "**HTTP health port**"); under the v0.1.0 M-FBM file-based pivot (D-Q.MFBM.6) memory is a file-based store with no daemon and no port, so the language mis-models what the entry represents. **Outcome:** the docstrings, the Pydantic `Field` description, and the inline comments that govern the `memory` entry of `service_state` model it as *file-based-store reachability* (a present/readable episode store), not *service liveness* (a daemon answering a health port) — while the wire contract (dict shape, `memory` key, value set including `not_expected`) is preserved byte-identically and the `orchestrator` entry (a genuine UNIX-socket service) keeps its service-liveness framing.

This is the Kill-#3 item the memory-session-continuity builder correctly left out-of-fence (its §12 halt-trigger 2 — sealed-component widening: it touched the M-FBM *signal* only where #45/#46 substrate required, and explicitly named the `service_state` framing as the *correct M-FBM signal, not a fault* in its §10 F2 item 1 while NOT rewording the surrounding service-model prose, which is a separate concern).

## §2 — Predecessors / context (the modelling defect, located from source)

Root-cause located by reading source (not prior-agent reports):

1. **`framework/primary-persona/src/loam/primary_persona/session_start_gate.py:177–198`** — `probe_service_state` docstring: *"Quick, cheap probe of session-level **services**. Probes: memory-system: **HTTP health port** as recorded on `<workspace>/.pos/memory-port`…"*. Under M-FBM there is no memory daemon and no health port for the file-based store; the `_probe_memory` body (line 221–249) *already* returns `not_expected` when the graphiti plist is absent (V11.E, SEALED) — i.e. the code's *behaviour* is M-FBM-correct, but the docstring still *describes* memory as an HTTP-health-port service. The model-prose lags the sealed behaviour.

2. **`framework/primary-persona/src/loam/primary_persona/context_composer.py:165–172`** — `SessionPayload.service_state` `Field(...)` description: *"Service-state fields for the memory **sidecar**, orchestrator, and any other session-level **services**."* "memory sidecar" + "session-level services" frames the file-based store as a sidecar service. The orchestrator IS a UNIX-socket service (`_probe_orchestrator`, `session_start_gate.py:252`) — its framing is correct and is preserved.

**Why this is prose-only (the in-fence proof):** the wire contract is exercised by `test_D8_1_session_start_emission.py:121-129`, `test_D8_4_cold_start_budget.py:112`, `test_AC46_1_session_start_cli_emits_structured_payload.py:137-141`, `test_AC_V11_E_2_probe_memory_skips_when_plist_absent.py`. Each asserts the dict key `memory`, membership in `{up,down,unknown,not_expected}`, or rendered-string presence — NONE asserts the docstring text, the `Field` description text, or any comment (verified: `grep -rn "sidecar|session-level service|Service-state fields|Quick, cheap probe|HTTP health" framework/primary-persona/tests/` returns only seal-machinery sidecar matches, zero prose pins). Rewording the prose therefore changes no asserted behaviour. The reword keeps every value the value set already admits (it does NOT introduce a new value — `not_expected` already exists and is the M-FBM signal).

## §3 — Scope

**In scope:**
- Reword the `probe_service_state` docstring (`session_start_gate.py`) so the `memory` line models file-based-store reachability under M-FBM (no daemon / no health port); keep the `orchestrator` line as a socket-service probe.
- Reword the `_probe_memory` / V11.E comment block only where it still calls memory a port-probed service in a way that contradicts the M-FBM file-based model — minimal, only the mis-modelling sentences.
- Reword the `SessionPayload.service_state` `Field(...)` description (`context_composer.py`) — "memory sidecar … session-level services" → file-based-store-reachability framing for the `memory` entry while keeping the orchestrator-service framing.
- Module-header docstring line `session_start_gate.py:20` ("session-level services") only if it materially mis-models — minimal touch.

**Out of scope (do NOT absorb):**
- Any change to the `service_state` dict shape, the `memory`/`orchestrator` keys, or the value set (`up`/`down`/`unknown`/`not_expected`). SEALED contract; unchanged byte-for-byte.
- The `not_expected` sentinel logic (V11.E, already the correct M-FBM signal).
- The `_probe_memory` TCP-probe code path itself (it correctly engages only when the graphiti plist is present, i.e. M-GMP installed).
- Any other deferred plan-doc in `docs/plans/` (the concurrent plan-author's territory) or unrelated changes.
- Renaming `service_state` → a file-based name (that IS a behaviour/contract change; halt-trigger if it appears required — it is not).

## §4 — Acceptance criteria (`AC.SSMR.*`)

All ACs outcome-shape + deterministic. Method-in-AC test applied to each.

### AC.SSMR.1 — `memory` entry modelled as file-based-store reachability, not service liveness

**Outcome:** the `probe_service_state` docstring (`session_start_gate.py`) describes the `memory` entry as a file-based memory store under the M-FBM pivot (no memory daemon / no HTTP health port for the file-based store; the TCP probe engages only when the graphiti/M-GMP plist is present), and does not describe the file-based store itself as an HTTP-health-port service.

**Verification:** a test reads the `probe_service_state.__doc__` string and asserts (a) it references the file-based memory store / M-FBM framing for the `memory` entry, and (b) it does NOT describe the file-based store as reached via an HTTP health port. The wire-contract tests (D8.1 / D8.4 / AC46.1 / V11.E.2) continue to pass unchanged.

**Method-in-AC test:** PASS — satisfiable by any phrasing that models file-based-store reachability without service-liveness language for the file-based store; exact wording is the builder's call.

### AC.SSMR.2 — `SessionPayload.service_state` field description no longer calls memory a sidecar service

**Outcome:** the `SessionPayload.service_state` Pydantic `Field` description (`context_composer.py`) does not call the `memory` entry a "sidecar" or model the file-based store as a session-level service; the `orchestrator` entry's service framing (a genuine UNIX-socket service) is preserved.

**Verification:** a test imports `SessionPayload`, reads `model_fields["service_state"].description`, asserts (a) it does NOT contain "sidecar" framing for memory and (b) it still acknowledges the orchestrator as a service. Pydantic model construction + the wire-contract tests pass unchanged.

**Method-in-AC test:** PASS — satisfiable by any description that drops the sidecar/service mis-model for memory while keeping the orchestrator framing; wording is the builder's call.

### AC.SSMR.3 — Wire contract preserved byte-for-byte (no behaviour change crosses any boundary)

**Outcome:** the `service_state` dict, the `memory` and `orchestrator` keys, and the value set (`up` / `down` / `unknown` / `not_expected`) are unchanged; every pre-existing test that exercises the session-start payload's `service_state` passes without modification.

**Verification:** the full pre-existing session-start test set (`test_D8_1_session_start_emission.py`, `test_D8_4_cold_start_budget.py`, `test_AC46_1_session_start_cli_emits_structured_payload.py`, `test_AC_V11_E_2_probe_memory_skips_when_plist_absent.py`) runs GREEN with zero edits to those test files in this amendment.

**Method-in-AC test:** PASS — this is a preservation AC; satisfied iff the reword is prose-only. Any method that changes the contract fails it (the halt-trigger surface).

### AC.SSMR.S — Seal-diff single-component scope

**Outcome:** the amendment's seal-diff window touches only `framework/primary-persona/` source (plus universal admissions: plan-doc, manifest, STATE/roadmap backfill). The `primary-persona` seal-test passes against the advanced BASELINE..SEAL_COMMIT window.

**Verification:** `framework/primary-persona/tests/test_no_sealed_amendments.py` GREEN post-seal; post-seal `loam amend apply --dry-run` clean.

**Method-in-AC test:** PASS — structural seal invariant; the loam amend machinery is the only method.

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | `probe_service_state` docstring models memory as file-based-store reachability under M-FBM | AC.SSMR.1 |
| 2 | `SessionPayload.service_state` field description drops the memory-sidecar/service mis-model, keeps orchestrator service framing | AC.SSMR.2 |
| 3 | Wire contract (dict shape / keys / value set) preserved byte-for-byte; all pre-existing session-start tests GREEN unmodified | AC.SSMR.3 |
| 4 | Seal-diff single-component scope; seal-test GREEN | AC.SSMR.S |

## §5 — Sealed-component fence

Single component: **`primary-persona`**. Seal-test `framework/primary-persona/tests/test_no_sealed_amendments.py`; sidecar `framework/primary-persona/tests/SEAL_COMMIT`. BASELINE = the memory-session-continuity backfill tip (`5957073`) — this amendment stacks on `amend/memory-session-continuity`. Source touched: `framework/primary-persona/src/loam/primary_persona/session_start_gate.py`, `framework/primary-persona/src/loam/primary_persona/context_composer.py`. New AC tests under `framework/primary-persona/tests/`. Universal admissions per amendment #22 ruling #3 (plan-doc, manifest, STATE.md, roadmap).

## §6 — Build steps (the order the builder follows)

1. Reword `context_composer.py` `SessionPayload.service_state` `Field` description (AC.SSMR.2).
2. Reword `session_start_gate.py` `probe_service_state` docstring + the V11.E comment-block mis-modelling sentences + the module-header line if it materially mis-models (AC.SSMR.1).
3. Author `test_AC_SSMR_1_*`, `test_AC_SSMR_2_*`, `test_AC_SSMR_3_*` under `framework/primary-persona/tests/`.
4. Run the new AC tests + the pre-existing session-start tests (D8.1 / D8.4 / AC46.1 / V11.E.2) locally; all GREEN.
5. `loam amend validate` → `loam amend apply` → `loam amend seal`.
6. §14 backfill (STATE.md + roadmap §8 + this register).

## §7 — Halt triggers (the builder obeys these in-flight)

1. **Contract-change creep.** If the reword turns out to require changing the `service_state` dict shape / a key / the value set / the `not_expected` logic to satisfy an AC, HALT and surface — it then needs a wider (behaviour-change) amendment, not a prose reframe.
2. **Sealed-component widening.** If the reword requires touching a sealed component beyond `primary-persona/`, HALT and surface.
3. **ODD violation in surrounding code.** If an ODD §2.5 violation surfaces in the surrounding session-start code, surface it — do not silently extend (`feedback_subagent_odd_violation_halt`).
4. **Pre-existing test regresses.** If any pre-existing session-start test goes RED from a prose-only edit, that means the edit was not prose-only — HALT, re-scope.
5. **Public/external step.** Any step that would push to a public/external remote, flip visibility, or publish to an external registry — HALT and surface; ship is LOCAL only.

## §8 — F2 Ruthless Feedback (honest doubts named)

1. **The dispatch frames this as a Kill-#3 the prior builder "correctly left out-of-fence" — confirmed, with the precise evidence.** *Claim:* the memory-session-continuity §10 F2 item 1 says `service_state: memory: not_expected` is the *correct M-FBM signal, not a fault*. That statement is about the *behaviour* (the sentinel value) and is correct. *The residual:* the prior builder did NOT (and per its fence should NOT have) reworded the *surrounding service-model prose* (docstrings/field-description) that still models the file-based store as a port-probed sidecar service. So "the signal is correct" and "the modelling prose is wrong" are both true and non-contradictory — this amendment closes only the second, prose-only, which is the correctly-scoped follow-on. *No disagreement with the dispatch framing.*
2. **Class is PATCH, not docs-only-noop — named.** Although prose-only, the edit is to *source files* inside a sealed component, so it routes through `loam amend apply`/`seal` (the seal-diff window must advance to admit the source-file diff). It is PATCH (no behaviour change, no contract change) — not "docs/" universal-admission, because the files are `src/` not `docs/`. The seal machinery is the correct (and only) mechanism; this is named so the register reflects PATCH, not a free doc edit.
3. **Residual risk — "prose-only" is verified by test-grep, not by proof.** The in-fence proof rests on no test asserting the prose. AC.SSMR.3 makes this structural: the pre-existing tests run unmodified and must stay GREEN; if any goes RED the edit was not prose-only and halt-trigger 4 fires. The risk is named, not silently accepted; the structural guard is AC.SSMR.3.

## §9 — Bookkeeping surface (manifest)

`loam amend` manifest at `docs/plans/service-state-file-based-memory-reframe.manifest.yaml` (schema_version 3). BASELINE = `5957073` (memory-session-continuity backfill tip — this amendment stacks on `amend/memory-session-continuity`). Single component `primary-persona`, sidecar `framework/primary-persona/tests/SEAL_COMMIT`, narrative `framework/primary-persona/seals/SEAL_COMMIT.service-state-file-based-memory-reframe`. Universal admissions mirror the prior cycle's manifest.

## §10 — Halt findings

Per `feedback_subagent_odd_violation_halt`: halt and surface any ODD violation observed in surrounding code/docs.

**(none observed during plan authoring — the mis-modelling is a documented-language lag behind sealed M-FBM behaviour, not an unnamed code path; every touched line maps to AC.SSMR.{1,2}.)**

## §11 — §status

**Build cycle:** BUILT + SEALED + SHIPPED LOCAL (loam-builder, 2026-05-15). D-SSMR.{1,2} builder-autonomous (methodology-answered — §2 empirically proves prose-only; no owner-gated options); both stuck at build time. Source edits + AC.SSMR.* tests + `loam amend apply` + `loam amend seal` complete; merged to local `main` (`dac03ee`) + dogfood verified (full primary-persona suite 611 passed / 1 skipped on merged `main`; baseline post-memory-session-continuity 601/1; +10 = the 10 new AC.SSMR cases; zero regressions). LOCAL only — NO push, NO tag, NO public action (owner vocabulary lock: ship=LOCAL; owner said "ship it", not "publish").

**AC verdict matrix (GREEN vs real test output):**

| AC | Verdict | Evidence |
|---|---|---|
| AC.SSMR.1 | GREEN | `test_AC_SSMR_1_*` 3/3 — `probe_service_state.__doc__` models the memory entry as the file-based store under M-FBM; no HTTP-health-port service framing for the file-based store; orchestrator keeps socket-service framing. |
| AC.SSMR.2 | GREEN | `test_AC_SSMR_2_*` 3/3 — `SessionPayload.model_fields["service_state"].description` drops the memory "sidecar" mis-model, models file-based store, keeps orchestrator service framing. |
| AC.SSMR.3 | GREEN | `test_AC_SSMR_3_*` 4/4 — `service_state` dict keys exactly `{memory, orchestrator}`; values ⊆ sealed set `{up,down,unknown,not_expected}`; V11.E `not_expected` signal byte-identical; field type contract `dict[str,str]` unchanged. Pre-existing session-start suites (D8.1/D8.4/AC46.1/V11.E.2 — 22 cases) GREEN, ZERO test files modified by this amendment. |
| AC.SSMR.S | GREEN | `test_no_sealed_amendments.py` + `test_AC_A_S_seal_diff_single_component_scope.py` GREEN post-seal; post-seal `loam amend apply --dry-run` clean (`primary-persona ok`). |

## §12 — Decisions

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-SSMR.1 — Class is PATCH (prose-only reframe of source-file modelling language; no contract change) | PATCH | Determines version-derivation + seal narrative; builder-autonomous because §2 empirically proves no behaviour/contract change (no owner-gated options). |
| D-SSMR.2 — Stack on `amend/memory-session-continuity` (BASELINE = `5957073`) rather than branch off `main` | Stack | The memory-session-continuity work is unmerged; the reword composes on its tip and ships together. Stacking keeps one linear seal ladder. |

## §13 — Authority chain

Plan-author authors plan + named decisions WITH recommendations. Both D-SSMR.1 and D-SSMR.2 are methodology-answered (PATCH proven by source-evidence; stacking dictated by the unmerged-predecessor state) — builder-autonomous, no owner ruling gates the build. Fail-closed: §8 risk 3 is the named residual; AC.SSMR.3 is its structural guard.

## §14 — SHA register

| Item | SHA |
|---|---|
| Plan-doc + manifest (this cycle) | `ccd00c0` |
| Source edits + AC.SSMR.* tests (pre-amendment tip / BASELINE) | `0430954` |
| Manifest baseline backfill (→ `0430954`) | `49f2436` |
| `loam amend apply` (BASELINE+sidecar bump to `0430954`) | `0556d7f` |
| `loam amend seal` (deterministic seal commit) | `4e8c41f` |
| Ship LOCAL — merge `amend/memory-session-continuity` → `main` (no-ff; carries memory-session-continuity seal `77e3bd7` + this seal `4e8c41f`) | `dac03ee` |
| §11 §status + §14 backfill + STATE.md + roadmap | (this commit) |

Seal-diff window: `BASELINE=0430954..SEAL_COMMIT=0556d7f` (sidecar `tests/SEAL_COMMIT` = `0430954...`). Narrative: `framework/primary-persona/seals/SEAL_COMMIT.service-state-file-based-memory-reframe`. Stacked on `amend/memory-session-continuity` (memory-session-continuity backfill tip `5957073`); both amendments shipped together to local `main`.

### Build-time corrections (F2-surfaced)

- **`smoke_outcome` > 200-char schema cap.** Initial manifest `smoke_outcome` was 247 chars; schema caps at 200. Tightened to 197 chars before the plan-doc+manifest commit (mirrors the memory-session-continuity `b694a07` precedent). `loam amend validate` → ok.
- **Halt-and-surface (test-prose, NOT extended).** `test_D8_1_session_start_emission.py:115` + `test_D8_4_cold_start_budget.py:18` carry the same "memory sidecar" mis-model in their test docstrings/comments (prose, no behaviour). Per `feedback_subagent_odd_violation_halt` this is SURFACED but NOT absorbed — it is out of this amendment's plan-§3 fence (the fence is the two `src/` files). Recommend a follow-on prose-only sweep of the test-side modelling language; not blocking (no behaviour, all 22 pre-existing tests GREEN).
