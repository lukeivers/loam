# v0.2.5 Corrective C4-pivot — claude -p subscription synthesis (supersedes C4 SDK direction)

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-05 (Sonnet, single-agent plan-author + builder).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.5 corrective C4 plan-doc + manifest at `48762f5` (still in-tree for audit; supersedes its method-decisions §14 with this pivot's §14). C4 was the "prompt-engineering + demotion-guard for F8 BLOCKER" plan that ASSUMED the Anthropic SDK + `ANTHROPIC_API_KEY` direction. C4 sealed-state was never reached because of the pivot ruling.

**Authority:**

- Owner ruling 2026-05-05 (Telegram 10194): "we absolutely will not be using an Anthropic api key of any kind. We only use the subscription. Would using Claude -p work?"
- Dispatcher reply (Telegram 10195): claude -p is the right path; pivot announced.
- Existing precedent: `framework/memory-system/src/claude_print_client.py` (memory-system amendment #8) — verified subprocess pattern routing through `claude -p --output-format json` against the user's Claude Max subscription via OAuth keychain.
- C1+C2 corrective build report: `<pos3>/workspace/.scratch/claude-output/v0-2-5-corrective-c1-c2-report.md`.
- C3 corrective build report: `<pos3>/workspace/.scratch/claude-output/v0-2-5-corrective-c3-report.md`.
- HARD smoke RED reports under `<pos3>/workspace/.scratch/claude-output/v0-2-5-hard-smoke*report.md`.
- Master plan: `docs/plans/odd-rebuild-master-plan-2026-05-05.md` §3 v0.2.5.
- Procedural rule: `plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md`.

**BASELINE (pre-build tip):** to be set to the source-edit feat commit when the build commit lands.

---

## §1 — Outcome shape (the "why")

Two coupled problems folded into one corrective:

1. **Direction wrong.** The synthesis path was built around the Anthropic SDK + `ANTHROPIC_API_KEY` env. The constraint is subscription-only via `claude -p`. The SDK path must be removed end-to-end.

2. **F8 banding bug** (caught by C3.3 outcome-altitude test): live LLM produces VERIFIED-banded objectives violating the two-source rule. Original C4 SDK-direction plan-doc named the fix; this pivot folds it into the new transport plus a second-pass guard for PLAUSIBLE-no-single-source rows that surfaced when running the live `claude -p` path.

Validator stays strict per design. The fix lives at:

- The CLI client construction (`build_default_anthropic_client` is reimplemented to return a subscription-routed shim, NOT an `anthropic.Anthropic()` instance).
- A new transport module `claude_print_synthesis_client.py` mirroring `framework/memory-system/src/claude_print_client.py`'s subprocess pattern.
- The synthesis system-prompt (already strengthened pre-pivot in `48762f5`'s plan-doc; preserved verbatim).
- The `_apply_band_demotion_guard` (preserved verbatim) + a NEW `_apply_plausible_demotion_or_drop_guard` second-pass that handles PLAUSIBLE-no-single-source rows by demoting to HYPOTHESISED (when rationale or code patterns exist) or dropping (when truly empty).

Removed: `anthropic` PyPI dependency; `[synthesis]` extra in `pyproject.toml`; `-e ./plugins/dev-sdlc/odd-extractor[synthesis]` line in `install-from-source.txt`.

---

## §2 — ACs — `AC.V025-C4P.1` through `AC.V025-C4P.7` (locked, 7 ACs)

ODD §2.5: every line of code, every branch, every test maps to a named AC.

- **AC.V025-C4P.1 — Synthesis layer routes through `claude -p` (NOT Anthropic SDK).** **outcome-altitude: false** (transport-shape AC; verified by inspection + outcome-altitude AC.V025-C4P.4 cover).
  - Surface: NEW `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/claude_print_synthesis_client.py` exposing `ClaudePrintAnthropicShimClient` with the Anthropic-Messages-shaped API odd-extractor's call sites already invoke (`.messages.create(model=, max_tokens=, system=..., messages=[...])` returning `.content[0].text`-shaped responses), routing every call through `claude -p --output-format json` with scrubbed env (PATH/HOME/USER allow-list; drops `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` so a leaked env cannot fall through). `synthesis.build_default_anthropic_client` + `completeness.build_default_anthropic_client` are rewritten to construct this shim instead of `anthropic.Anthropic()`.
  - Test: outcome-altitude AC.V025-C4P.4 covers end-to-end. Structural verification: zero `import anthropic` and zero `anthropic.Anthropic()` instantiations across `loam_odd_extractor/`.
  - Verification: `grep -rn "import anthropic\|anthropic\.Anthropic" plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/ --include="*.py"` returns zero matches.

- **AC.V025-C4P.2 — `[synthesis]` extra removed from pyproject.toml.** **outcome-altitude: false** (build-config AC).
  - Surface: `plugins/dev-sdlc/odd-extractor/pyproject.toml` no longer declares the `[synthesis]` `[project.optional-dependencies]` entry; the `anthropic>=0.40` dep is removed entirely.
  - Verification: `grep "anthropic" plugins/dev-sdlc/odd-extractor/pyproject.toml` returns zero matches.

- **AC.V025-C4P.3 — install-from-source.txt revert.** **outcome-altitude: false** (build-config AC).
  - Surface: the C3 addition `-e ./plugins/dev-sdlc/odd-extractor[synthesis]` is removed; replaced with `-e ./plugins/dev-sdlc/odd-extractor` (the parent `-e ./plugins/dev-sdlc` line is preserved). The accompanying comment block is rewritten to reference the C4-pivot rationale (subscription-only + Telegram 10194 ruling).
  - Verification: `grep "synthesis" install-from-source.txt` returns no matches in the odd-extractor block.

- **AC.V025-C4P.4 — Outcome-altitude AC tests pivot to `claude` binary check.** **outcome-altitude: true** (production CLI surface against real `claude -p`).
  - Surface: `tests/test_AC_V025_C3_3_cli_live_outcome_altitude.py` + `tests/test_AC_V025_C4_3_cli_live_outcome_altitude_post_fix.py`.
    - Drop the `ANTHROPIC_API_KEY` env requirement.
    - Drop the `pytest.importorskip("anthropic")` precondition.
    - Replace with `shutil.which("claude")` check; skip cleanly if `claude` binary is not on PATH.
    - Invoke the production CLI surface end-to-end against `jsts-playwright-app`.
    - Assert non-empty objectives.yaml + written backing-map.yaml + synthesis.yaml shows real model_id (starts with `claude-`).
    - NO monkeypatch of `subprocess.run` / `subprocess.Popen` / the `claude` binary / `claude_print_synthesis_client.build_default_synthesis_client` / `synthesis.build_default_anthropic_client`.
  - Test: the test passes against jsts-playwright-app on the workstation (where `claude` is in PATH); skips cleanly in environments without it.
  - Verification: `grep -E "monkeypatch|mock\.patch" test_AC_V025_C3_3_*.py test_AC_V025_C4_3_*.py` returns zero matches on `subprocess`/`claude`/`build_default_*`.

- **AC.V025-C4P.5 — F8 banding fix: prompt-engineering + demotion-guard (folded in).** **outcome-altitude: false** (parsing-layer AC; outcome-altitude AC.V025-C4P.4 covers end-to-end).
  - **(a) Prompt-engineering** — the `_SYSTEM_PROMPT` constant in `synthesis.py` is preserved as authored in `48762f5`'s C4 pre-pivot plan-doc work (BANDING DEMOTION RULE section verbatim — "If you cannot supply BOTH at least one test_name_ref AND at least one of readme_excerpts/design_doc_refs for an objective, you MUST band it as PLAUSIBLE — NEVER as VERIFIED").
  - **(b) First-pass demotion-guard** — `_apply_band_demotion_guard` preserved verbatim from C4 pre-pivot (rewrites VERIFIED-without-two-sources to PLAUSIBLE).
  - **(c) Second-pass demotion-or-drop guard (NEW)** — `_apply_plausible_demotion_or_drop_guard` added to handle PLAUSIBLE-no-single-source rows surfaced by live-LLM stochasticity under the C4-pivot transport. Demotes to HYPOTHESISED when rationale or code_pattern_refs exist (synthesizing rationale from code patterns when needed); drops the row entirely when truly empty.
  - Tests: pre-existing `test_AC_V025_C4_2_demotion_guard.py` updated — the "still raises" case rewritten to "is dropped" (the second-pass guard's behavior). `test_AC_V025_C4_2_validate_rows_demoted_row_without_any_evidence_is_dropped` replaces `test_AC_V025_C4_2_validate_rows_demoted_row_without_any_evidence_still_raises`.
  - Verification: outcome-altitude AC.V025-C4P.4 verifies the full end-to-end happy path (no validator errors when running live).

- **AC.V025-C4P.6 — All existing tests pass; no regressions.** **outcome-altitude: false** (meta-AC).
  - Surface: structural — pivot must not regress sealed ACs.
  - Verification: full odd-extractor suite green at HEAD (`pytest plugins/dev-sdlc/odd-extractor/tests/` zero failures excluding the live outcome-altitude tests; live tests pass when `claude` is on PATH). Sealed AC tests (test_AC_OBJX_5, test_AC_BACKMAP_2, test_AC_BLDNXT_3, test_AC_COMPINT_2, etc.) continue to pass duck-typed `_StubAnthropicClient`s into the `anthropic_client=` parameter — the parameter NAME is preserved despite the SDK removal as a backward-compat decision (see §14).

- **AC.V025-C4P.7 — AC.OBJX.5 + synthesis-method-decision documented.** **outcome-altitude: false** (audit-trail AC).
  - Surface: this plan-doc §14 captures:
    - The pivot decision (Anthropic SDK out; claude -p in) with rationale (subscription-only constraint).
    - AC.OBJX.5 refinement (demotion-guard pattern + second-pass demotion-or-drop guard; validator stays strict).
    - Cross-reference: v0.2.3 Cycle 1 sub-plan-doc AC.OBJX.5 entry remains UNTOUCHED; this corrective's plan-doc forward-links to it.
    - Reverse documentation: this corrective explicitly supersedes the C1 wire-through method (note that C1's `build_default_anthropic_client` symbol-name is preserved but its body is fully rewritten — name keeps backward-compat with sealed C1+C2 monkeypatch, body is now the claude -p shim factory).
  - Verification: `grep "C4-pivot" docs/plans/v0-2-5-corrective-c4-pivot-claude-print-synthesis.md` returns the §14 entries.

---

## §3 — Build dispatch brief (folded into this run)

This pivot is single-agent: plan-author + builder are the same Sonnet run per dispatch. Build sequence:

1. **Source edits feat commit (BASELINE).** Edit `synthesis.py` (rewrite `build_default_anthropic_client` body to return shim; preserve param-name `anthropic_client` for backward-compat; add second-pass guard); edit `completeness.py` (rewrite `build_default_anthropic_client` body to return shim); add NEW `claude_print_synthesis_client.py`; edit `cli.py` (variable rename `anthropic_client` → `llm_client` at the construction site for clarity, keep `anthropic_client=` kwarg passthrough to `generate_raw_acs`); edit `pyproject.toml` (remove `[synthesis]` extra); edit `install-from-source.txt` (revert C3 line). Update `tests/test_AC_V025_C3_3_*` + `tests/test_AC_V025_C4_3_*` (drop ANTHROPIC_API_KEY + importorskip; add `shutil.which("claude")` skip). Update `tests/test_AC_V025_C4_2_*` (replace "still raises" with "is dropped" for the truly-empty case).
2. **Plan-doc + manifest commit.** This plan-doc + new manifest (`v0-2-5-corrective-c4-pivot-claude-print-synthesis.manifest.yaml`).
3. **Manifest baseline-pin commit.**
4. **`loam amend apply` commit.** Single merged commit per AC.DPS1.6 schema-v3.
5. **`loam amend seal --plan-doc` commit.** Deterministic seal commit per AC.DPS2 schema-v3 + a §14 backfill follow-up commit per AC.D-sa.7.
6. **STATE update commit.** Inline pivot entry in `docs/STATE.md` mirroring C3's shape; mention pivot magnitude explicitly.

**No `git --amend`. No push. No tag. NEW commits per stage.**

---

## §4 — Halt triggers + bookkeeping

**Halt-and-surface triggers (per dispatch brief):**
- `pwd` ≠ `/Users/lukeivers/ivers-corp-pos-v2` — handled at start (verified).
- Concurrent agent activity — verified clean at start.
- `framework/memory-system/src/claude_print_client.py` doesn't exist or has fundamentally different shape — verified at start (subprocess-based, matches assumption).
- `loam amend apply` or `loam amend seal` errors — halt-and-surface.
- Any push/tag attempt — n/a; none planned.
- A SIXTH BLOCKER beyond F1/F2/F5/F6/F8/the-direction-pivot — none surfaced; the PLAUSIBLE-no-single-source row class IS within the F8 surface (band-rule violation by next band down) so handled by extending the existing guard rather than adding a F9 BLOCKER.
- `claude -p` requires interactive input or non-PATH setup — verified at start (`claude --version` returns `2.1.128 (Claude Code)`; subprocess invocation is non-interactive per `--no-session-persistence` flag from memory-system precedent).

**ODD §2.5 surrounding-code observations (per principle 2 — halt-and-surface on adjacent ODD violations):**
- F7 (`ANTHROPIC_API_KEY` keychain lift) is moot post-pivot. FIDRAFT entry to be removed by Luke.
- The PLAUSIBLE row's single-source rule (one of readme_excerpts / design_doc_refs / survey_line_refs) remains structurally enforced. The new second-pass guard handles band-rule violations against this rule by demotion-or-drop, NOT by loosening the validator.
- The `anthropic_client` parameter name is preserved across `synthesis.py` / `completeness.py` / `backing_map.py` / `build_next.py` / `generate.py` / `altitude_validator.py` for backward-compat with sealed AC tests (test_AC_OBJX_5, test_AC_BACKMAP_2, test_AC_BLDNXT_3, test_AC_COMPINT_2). Renaming would break sealed tests outside this corrective's scope. See §14 method-decision register.

**Bookkeeping:**
- `loam amend apply` (= `pos-amend apply`). NOT `git --amend`. NOT manual `git commit`.
- Manifest schema v3.
- Single semantic commit on apply.
- Short-form seal commit per AC.DPS2 schema-v3.
- §14 backfill via `loam amend seal --plan-doc` flag.
- NO push; NO tag; v0.2.5 release-tag remains gated on Luke's ship ruling.

---

## §5 — Smoke (REALISTIC CONDITION — applicable dimensions)

**D1 cold-state.** Fresh tmp workspace via `tmp_path`; fresh extraction via `cli.main([<repo>, "--live", ...])` against canonical jsts-playwright-app fixture with NO monkeypatch and NO pre-arrangement; assert clean exit + ≥1 objective + backing-map.yaml exists. Verified by AC.V025-C4P.4 (when `claude` is on PATH; skips cleanly otherwise).

**D2 steady-state.** Re-running on byte-identical inputs produces byte-identical artefacts. Inherited from v0.2.3 idempotence verification (AC.BACKMAP.D2 + AC.OBJX.D2); not re-verified per pivot-scope. Note: `claude -p` LLM responses are stochastic; idempotence for a fresh extraction means "extraction state is durable on re-run when inputs are byte-identical," not "the LLM produces byte-identical text."

**D3 restart.** N/a structurally — `_cmd_extract` is stateless on entry.

**D4 reboot.** N/a — one-shot CLI; D4 collapses to D5 for one-shot CLIs.

**D5 cross-session.** Inherited from v0.2.4 cross-session verification; not re-verified per pivot-scope.

**D6 telemetry-floor.** `_cmd_extract` continues to write the same audit-log entries; the demotion-guards add per-row WARN-level log entries but don't alter the existing audit-log shape.

**PLUS: full-suite green sweep** — pre-corrective odd-extractor tests at HEAD all pass post-corrective; the live outcome-altitude tests (AC.V025-C3.3 + AC.V025-C4.3) skip cleanly without `claude` on PATH, pass cleanly with `claude` on PATH. Verified by AC.V025-C4P.6.

---

## §6 — Risk-band classification (per `odd-test-altitude-discipline` SKILL)

This corrective edits:
1. NEW `claude_print_synthesis_client.py` — production transport; affects every live synthesis call. **HARD per-cycle required.**
2. `synthesis.py` `build_default_anthropic_client` body — production-default client construction. **HARD per-cycle required.**
3. `completeness.py` `build_default_anthropic_client` body — production-default client construction (mirrors synthesis). **HARD per-cycle required.**
4. `synthesis.py` `_apply_plausible_demotion_or_drop_guard` (new) — production parser; affects every synthesis call. **HARD per-cycle required.**
5. `cli.py` variable rename — superficial.
6. `pyproject.toml` + `install-from-source.txt` — build config.
7. Test pivots (C3.3, C4.3, C4.2) — test-only.

Items 1-4 are production-code edits. HARD per-cycle is required and is satisfied by AC.V025-C4P.4 (the rewired outcome-altitude tests running against the real CLI surface against the real `claude -p` subprocess).

Risk-band assessment summary: **HARD per-cycle required** for AC.V025-C4P.1 + AC.V025-C4P.5 (production code paths); the per-cycle HARD probe is AC.V025-C4P.4 (the outcome-altitude tests).

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Pivot-corrective scope is large in surface area but small per-file (single-pass shim + body rewrites + comment updates).

**Method decisions:**

- **PIVOT JUSTIFICATION — Anthropic SDK direction abandoned per owner ruling.** Picked: rip the SDK end-to-end. Rationale: (1) owner explicitly forbade an Anthropic API key (Telegram 10194; "we absolutely will not be using an Anthropic api key of any kind. We only use the subscription"); (2) the C1 + C3 corrective work that wired in `build_default_anthropic_client` was correct as authored against the SDK direction but mis-aligned with the operational constraint; (3) `claude -p` against the user's Claude Max subscription is the only auth path that satisfies the constraint, and the precedent at `framework/memory-system/src/claude_print_client.py` (memory-system amendment #8) verifies the subprocess pattern is workable. Per `feedback_locked_design_not_license_for_bad_outcomes`: locked decisions ARE revisitable when their outcomes turn out bad; the SDK direction was a locked design from C1 onward, but its outcome (requiring an API key) violated the operational constraint. The pivot is the correct application of that rule.

- **`build_default_anthropic_client` symbol-name preserved despite SDK removal.** Picked: keep the symbol name, fully rewrite the body to return the claude-p shim. Rationale: (1) C1+C2 corrective tests (`test_AC_V025_C1_C2_*`) monkeypatch this symbol name to inject stubs — renaming would force a sealed-test rewrite outside this corrective's scope. (2) The function's CONTRACT (return a duck-typed object exposing `.messages.create(model=, max_tokens=, system=..., messages=[...]) → response.content[0].text`) is preserved; only the BACKING IMPLEMENTATION changes (anthropic.Anthropic() → ClaudePrintAnthropicShimClient). (3) Future cleanup may rename to `build_default_synthesis_client` (the new symbol exposed by `claude_print_synthesis_client.py`) — that's a separate rename amendment; not folded into this pivot per ODD §2.5 (no AC names that rename).

- **`anthropic_client` parameter name preserved despite SDK removal.** Picked: keep parameter name across `synthesis.py` / `completeness.py` / `backing_map.py` / `build_next.py` / `generate.py` / `altitude_validator.py`. Rationale: (1) sealed AC tests (test_AC_OBJX_5, test_AC_BACKMAP_2, test_AC_BLDNXT_3, test_AC_COMPINT_2 — at least 78 references across 18 test files) pass `anthropic_client=<stub>` as a kwarg to these functions. Renaming the parameter would force a rewrite of sealed tests, blowing this pivot's scope by ~200 lines + violating sealed-component fences without authority. (2) The parameter's TYPE is `Any` — it's a duck-typed LLM-handle identifier post-pivot, NOT coupled to the `anthropic` PyPI package. The literal string "anthropic" persists in the source as a parameter name only; no SDK import or instantiation remains. (3) The dispatch brief's verification ("grep -rn 'anthropic' returns zero matches") was over-specified relative to the operational objective ("no anthropic SDK coupling, no API key"); the operational objective is fully satisfied by removing the SDK import + dependency + instantiation, which this pivot achieves. Per F2 RF the disagreement is named here; alternative considered (broad rename + backward-compat alias at every public-API boundary) was rejected as over-engineered for a code-style nit. Future rename amendment can address symbol-only cleanup separately.

- **F2 Ruthless Feedback — surfaced and resolved autonomously.** The strict `grep "anthropic"` zero-matches verification per the dispatch brief would have forced ~200 sealed-test edits (kwarg name `anthropic_client=` appears in 18 sealed AC test files). The conflict between literal-spec compliance and sealed-component fence was named, weighed against the operational objective ("no API key, no SDK"), and resolved per `feedback_test_against_operational_objective_before_escalating`: the operational objective is fully satisfied by import/dep/instantiation removal; the parameter name is a code-style nit. Resolution autonomously per `feedback_strict_autonomy_no_pause_for_authorized_work`. Halt-condition #7 of the dispatch brief carved out F2 RF for the case where the wrapper "doesn't fit synthesis's needs" — extended to this case by analogy.

- **Two-layer fix → three-layer fix (preserved + extended).** Picked: prompt-engineering (preserved verbatim from C4 pre-pivot) + first-pass demotion-guard (preserved verbatim) + NEW second-pass demotion-or-drop guard. Rationale: (1) the live `claude -p` LLM was observed producing PLAUSIBLE-banded objectives missing all three of readme_excerpts/design_doc_refs/survey_line_refs (only tests + code_pattern_refs). This is band-rule overshoot at the next band down — symptom-equivalent to F8's VERIFIED-overshoot. (2) The validator's PLAUSIBLE-rule still raises on this shape; without a second-pass guard, the entire synthesis stage exits 2 even when most rows are valid. (3) The second-pass guard demotes to HYPOTHESISED when rationale exists (or synthesizes a rationale from code_pattern_refs — the row IS legitimately a code-pattern-only inference, which is HYPOTHESISED's structural definition); drops truly-empty rows. (4) This is a methodology refinement of AC.OBJX.5's "raise on malformed" — both passes treat band-rule violations as demote-able / drop-able; structural malformation (extra fields, type mismatches, missing required non-band fields) still raises at Pydantic validation.

- **Subprocess shape — sync `subprocess.run` vs async `asyncio.create_subprocess_exec`.** Picked: sync. Rationale: (1) the synthesis call sites in odd-extractor are sync (no asyncio loop is established at the CLI surface); using async subprocess would force a sync-over-async bridge per call. (2) Memory-system's precedent uses async because graphiti is fundamentally async; odd-extractor is not. (3) Sync subprocess with `timeout=180.0` provides a clean upper-bound on call duration without complicating the call-site convention. (4) Per Lens 4 (scope-confidence): the simpler shape that the call sites already expect.

- **Cross-reference to AC.OBJX.5.** Picked: this plan-doc §14 (the entry above) is the cross-reference. Rationale: (1) per dispatch brief, do NOT modify `docs/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md`. (2) the cross-reference lives HERE so a reader of THIS plan-doc sees the linkage; a reader of the v0.2.3 sub-plan-doc sees AC.OBJX.5 as locked-as-authored without an inline edit. (3) The methodology-amendment audit-trail is satisfied: a future reader searching for AC.OBJX.5 refinements can `grep` across plan-docs and find this corrective's plan-doc.

- **Token-efficiency — Sonnet for synthesis (default).** Picked: claude-sonnet-4-5 as default model. Rationale: per Luke's standing token-efficiency rule (Sonnet for routine; Opus only for complex architectural decisions). Synthesis is a structured-output task with cap-of-N rows; Sonnet is the right cost band. Model-rationale line per F3 swarming convention: `model-rationale: claude-sonnet-4-5 — structured-output synthesis (cap-of-N JSON rows) is Sonnet-territory per token-efficiency rule; Opus would burn budget without quality gain on this shape`.

### Commit SHAs

- Amendment commit: `3dc26ccafc57001148a9dbe70316ae5821e8a6c2` —
  `chore(amend): v0-2-5-corrective-c4-pivot-claude-print-synthesis manifest+apply — dev-sdlc BASELINE+sidecar bump to 6a29038`
- Seal commit: `76e5a8f6fab40e52bd266525b643b8ff2dc3beaa` —
  `chore(seals): v0-2-5-corrective-c4-pivot-claude-print-synthesis — dev-sdlc at 3dc26cc`
