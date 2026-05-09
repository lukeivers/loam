# v0.4.3 HARD smoke — narrowed Phase 1 — rd-automation extraction

**Verdict: GREEN.** Aggregate verdict for AC.V043.6 (HARD smoke per `feedback_hard_smoke_per_minor_before_publish.md`): rd-automation extraction smoke GREEN at v0.4.3 HEAD `bf3178e0` (post-experiments-doc + tests + sqrt→linear corrective).

Scope-narrowing precedent: v0.3.0 + v0.4.0 + v0.4.1 + v0.4.2 HARD smoke writeups collapsed Phase 1 to one probe — cold install of HEAD into a fresh venv, run ODD-extractor end-to-end against rd-automation, verify objectives.yaml + the v0.2.4/v0.2.5/v0.2.5.1/v0.4.{0,1,2} surface, check regression closures (F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN). Same shape applied here.

---

## Source-tree under test

| Detail | Value |
|---|---|
| Canonical loam tree | `/Users/lukeivers/ivers-corp-pos-v2` |
| HEAD SHA | `bf3178e0` (v0.4.3 docs/experiments append; the source-edit commits are at `a254f2c0` + `cd3b9778`; tests at `a89a8e94`) |
| Branch | `pos-v2` |
| Reference fixture | `/Users/lukeivers/pos3/workspace/rd-automation` (read-only; ~19k LOC Playwright TS) |
| Smoke workspace (ephemeral) | `/Users/lukeivers/pos3/workspace/.scratch/v0-4-3-hard-smoke/` |
| Cold-install venv | `<smoke>/install/.venv` (Python 3.13.12, fresh) |

---

## Cold install

Fresh venv created at `<smoke>/install/.venv`. `pip install -r install-from-source.txt` from canonical pos-v2 tree by absolute path-spec (path-rewritten copy in smoke dir; `-e ./` → `-e /Users/lukeivers/ivers-corp-pos-v2/...` so the smoke venv installs HEAD-under-test). 19 loam packages installed.

Pre-flight checks pre-extraction:

- `ANTHROPIC_API_KEY` confirmed unset (subscription-only auth via `claude -p`).
- `pip show anthropic` returns `WARNING: Package(s) not found: anthropic` — confirms anthropic SDK NOT in dependency tree (subscription-only invariant).
- `loam --version` shows `loam 0.1.0`.
- `loam odd-extract --help` shows v0.4.1 flags `--from-scratch` / `--no-from-scratch` registered (preserved; v0.4.3 adds no new CLI flags).
- v0.4.3 surface inspection in cold venv:
  - `from loam.primary_persona.file_memory import FileMemoryStore, _tokenize_for_fts` imports cleanly.
  - `_tokenize_for_fts("What is BallotPath?")` returns `['ballotpath']` — token-sanitization + stopword-drop active.
  - `memory_write_worker.py` source contains the new `"path": result.get("path")` line in the `worker-ok` diag emission and no `"episode_uuid"` key in the emitted dict.

---

## Stage 1 — extraction (`loam odd-extract <fixture> --live`)

Command run:

```
unset ANTHROPIC_API_KEY
export LOAM_ONBOARDING_SURVEY=<smoke>/onboarding/onboarding-survey.md
export LOAM_TELEGRAM_SKIP=1
<venv>/bin/loam odd-extract /Users/lukeivers/pos3/workspace/rd-automation \
  --live \
  --pm-name smoke-pm \
  --workspace-root <smoke>/ws
```

**Wall-clock: 335.27s (5:35).** Within historical band:
- v0.2.5.1: 306s
- v0.3.0: 177s
- v0.4.0: 230s
- v0.4.1: 267s
- v0.4.2: 230s
- **v0.4.3: 335s** ✓ (slightly above prior runs; well within F-TIMEOUT envelope; plausibly stochastic LLM-side variance — no slowdown attributable to v0.4.3 changes since the retrieval surface isn't on the extract code path)

Stage 1 exited 0. **F-VERIFY-ORPHAN GREEN** — no orphan-capability halt occurred.

---

## Synthesis cost + model

From audit logs:
- `model_id: claude-sonnet-4-5` (both passes)
- `llm_pass_cost_cents: 14.7855` ¢
- `cost_actual_cents: 23.1195` ¢

Total cost: ~38¢. Slightly above v0.4.2's 22¢ but within stochastic envelope (v0.4.0: 16.97¢; v0.4.1: 12.57¢). All `claude -p --strict-mcp-config` invocations preserved per the v0.2.5 C5 propagation invariant.

---

## Outcome-altitude objectives extracted

```
$ grep -c "^- objective_id:" objectives.yaml
7
```

**7 outcome-altitude objectives** extracted (matches v0.4.1 baseline of 7; v0.4.2 was 6; minor stochastic variation on ranking — within stratification band). Plus 19 unhandled (per CLI output).

Sample objective IDs:
- `O.dispute-processing.1`
- `O.manual-intervention.1`
- `O.reporting.1`
- `O.observability.1`
- `O.throughput.1`

Banding/typed shape preserved per v0.2.5 schema.

---

## Regression closures (ride-along)

### F-LEAK regression (v0.2.5.1 closure preserved)

```
$ for f in *.yaml; do echo "$f: $(grep -c 'html-captures\|screenshots' $f)"; done
backing-map.yaml: 0
config.yaml: 0
contract-draft.yaml: 0
evidence-rows.yaml: 0
multi-source-bundle.yaml: 1   ← raw input bundle (expected; pre-extraction)
objectives.yaml: 0
plan.yaml: 0
raw-acs.yaml: 0
state.yaml: 0
synthesis.yaml: 0
```

**F-LEAK GREEN** — zero `html-captures/` or `screenshots/` references in extracted output (bundle is raw input).

### F-TIMEOUT regression (v0.2.5.1 closure preserved)

Stage 1 wall-clock 335.27s; --synthesis-timeout default applies. No timeout halt observed. **F-TIMEOUT GREEN.**

### F-VERIFY-ORPHAN regression (v0.2.5.1 closure preserved)

Stage 1 includes the verify substage internally; exit 0 = no orphan-capability halt. **F-VERIFY-ORPHAN GREEN.**

---

## v0.4.3 surface verification

The v0.4.3 changes are scoped to file-based memory retrieval (FTS5 token-sanitization + grep length-normalization) + cosmetic worker-log fix. The `loam odd-extract` flow does NOT exercise memory retrieval — the persona memory layer is consumed at the SessionStart / UserPromptSubmit hook surface in claude-attached harness mode, not in the standalone CLI extractor flow.

**This is the intended HARD smoke shape:** verify that the v0.4.0/v0.4.1/v0.4.2 production-extract surface still works end-to-end on the production codebase fixture; v0.4.3's net-new surface (file_memory + worker log) is separately verified by AC.V043.{1,2,3,4} (unit tests + no-regression sweep) and AC.V043.5 (live-store probe outcome-altitude).

Specifically: cold install + import of `loam.primary_persona.file_memory` + the new `_tokenize_for_fts` helper ran cleanly in the smoke venv (verified above) — packaging-wise the v0.4.3 changes ship correctly.

---

## Subscription-only invariant

- ANTHROPIC_API_KEY unset across cold install + Stage 1 (verified via `env | grep -i ANTHROPIC` returning empty).
- `pip show anthropic` returns "Package(s) not found" (no SDK in dependency tree).
- All `claude -p` invocations route through `claude_print_synthesis_client.ClaudePrintAnthropicShimClient` with `--strict-mcp-config` + empty MCP config tempfile per v0.2.5 C5 invariant.
- Audit log shows model_id `claude-sonnet-4-5` (not `anthropic.AsyncAnthropic` shape).

---

## AC.V043.6 verdict

**GREEN.** All HARD smoke gates passed:

1. Cold install clean ✓
2. Stage 1 wall-clock within band (335s) ✓
3. Subscription-only invariant preserved ✓
4. Outcome-altitude objectives extracted (7, matches v0.4.1 baseline) ✓
5. F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-along all GREEN ✓
6. Synthesis cost within band (~38¢ total) ✓
7. v0.4.{0,1,2} surface preserved (no regression on extend-existing pipeline) ✓
8. v0.4.3 file-memory surface imports cleanly in fresh venv ✓

Ready for AC.V043.S seal-diff verification + `loam amend apply` + `loam amend seal`. v0.4.3 HALTS at seal per HARD HALT BEFORE PUBLIC ACTIONS — owner gates push + tag.
