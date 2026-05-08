# v0.1.2 item 5 sub-plan — ack-first persona contract amendment

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/plans/v0-1-x-roadmap.md` (§2 v0.1.2 item 5 + §8 method-decision register + §5 Decision B).
**Programme master:** `docs/plans/v0-1-x-roadmap.md` (v0.1.x roadmap).
**Predecessors:** v0.1.0 shipped; FBE.1–FBE.11 + FBE.6{b,c,d} foldback ladder closed; V11.A sealed at `9d58062` (orchestrator runtime fix); V11.E sealed at `7d19a7e` (graphiti probe graceful-skip on `framework/orchestrator/` + `framework/primary-persona/` two-component fence); §8 backfill at `18e708c`.
**BASELINE (pre-build tip):** `18e708c` — current canonical pos-v2 HEAD.
**Status-file target:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/ack-first-persona-contract-status-2026-05-03.md`.

---

## 1. Summary / TLDR

v0.1.2 item 5 lands the ack-first behavioural default in the loam primary-persona contract / prompt template. The behaviour was repeatedly captured as in-session calibration corrections from the owner; the FIDRAFT entry "Acknowledge-first on complex requests" (2026-05-03) records the rationale and recommends a hard rule with five explicit triggers. Decision B in the v0.1.x roadmap §5 locked the rule shape: **hard rule with explicit triggers** (mirrors F3's `model-rationale` absence-as-violation pattern — observable habit, no structural enforcement hook).

**What this lands:**

1. A new `### Acknowledge first on non-trivial requests` rule subsection in the `## Operational rules` section of `framework/primary-persona/templates/persona-template/prompt.md`. The rule names: (a) the 5 triggers (≥3 tool calls expected, ≥1 background dispatch, decision/judgment vs pure execution, file authoring vs reading, multi-paragraph/multi-question message); (b) the trivial-back-and-forth carve-out; (c) the ack-shape ("got it — doing X"); (d) absence on a clearly-complex request as observable violation.
2. New tests in `framework/primary-persona/tests/test_AC_O_1_default_archetype_prompt_md.py` (or a sibling AC-VPC.5.* test file — see §6 decision) verifying the rule text is present, the 5 triggers are named, and the carve-out is named.
3. The pre-existing "six operational-rule sections" assertion in `test_AC_O_1_six_operational_rule_sections_present` + the "named-section count is eleven" assertion in `test_AC_O_1_named_section_count_is_eleven` are widened from 6→7 operational rules and 11→12 total named sections (the addition is structural; the existing tests fail unless updated).
4. Sidecar bumps + seal commit for `framework/primary-persona/`.
5. Parent plan §8 backfill with v0.1.2-item-5 apply + seal SHAs.

Sealed-component fence: **single component — `framework/primary-persona/`**.

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; persona prompt has a clear "Operational rules" section that is the right home)

The template prompt at `framework/primary-persona/templates/persona-template/prompt.md` carries a `## Operational rules` heading at line 249 with six subsections (`### Lean on the harness`, `### Use the right tool`, `### Codify what repeats`, `### Structural enforcement default`, `### ODD-shaped internal model`, `### Light-touch narration on choices`, `### Lean on the corpus` — actually 7 subsections; see Surface #2 below for the count discrepancy with the existing AC.O.1 test).

The dispatcher's halt trigger named option (b) "create new Default behaviors section" as the default if no clear (a) match. **A clearly-matched (a) exists**: the `## Operational rules` section is exactly the home for "always-on behavioural-posture rules I run on every turn" (the section's own self-description at line 251). Ack-first is a behavioural-posture rule — adding it as a new `### ` subsection under `## Operational rules` is the natural placement. **Decision (autonomous, builder's call):** option (a) — add `### Acknowledge first on non-trivial requests` as a new subsection under `## Operational rules`, alphabetically/logically positioned (placed first or after `### Lean on the harness` — see §6).

### Surface #2 (HALT-AND-SURFACE — observable violation in the existing AC.O.1 test relative to the live template; ODD §2.5)

`test_AC_O_1_six_operational_rule_sections_present` asserts six operational rules. The template currently carries **seven** operational-rule subsections — the seventh is `### Lean on the corpus` at line 313 of `prompt.md`. Test counts say 6; live template carries 7. `test_AC_O_1_named_section_count_is_eleven` asserts the eleven-section count (5 traits + 6 rules); live template carries 12 (5 traits + 7 rules).

Per `feedback_subagent_odd_violation_halt`: this is a pre-existing AC drift that v0.1.2 item 5 surfaces but did not introduce. Per `feedback_loose_AC_text_fix_AC_not_implementation`: when implementation matches intent and AC text is loose/wrong, **tighten the AC**. The implementation (template at line 313) is correct; the test count is stale relative to a prior amendment that landed the seventh rule.

**Resolution (in-band — same fence):** v0.1.2 item 5 widens the operational-rule count from 6→8 (adds `### Acknowledge first on non-trivial requests` + acknowledges the pre-existing `### Lean on the corpus`) and the total named-section count from 11→13 (5 traits + 8 rules). Test text + assertions both update in lock-step. This composes:
- The intended landing: `### Acknowledge first on non-trivial requests` is added.
- The pre-existing drift: `### Lean on the corpus` is acknowledged in the test surface (the `eleven` tuple becomes a `thirteen` tuple, test name updates, assertion message updates).

Both edits are within the `framework/primary-persona/` fence; both edits land in the same test file (sidecar-class). The widening is the minimum-surface fix consistent with both the dispatcher's scope (add ack-first) and the ODD §2.5 halt-and-surface rule (do not silently extend the pre-existing violation; surface it and resolve in-band where the resolution is trivial). The pre-existing-drift fix is captured as Surface #2 in the build status file.

**Why in-band rather than separate amendment:** the test would fail post-build if v0.1.2 item 5 only adds the new rule; the build-cycle requires the test pass. Splitting into two amendments serializes 2 sealed-component cycles for what is one test-text update. ODD §2.5 names both ACs explicitly (AC-VPC.5.1 = ack-first rule landed; AC-VPC.5.2 = test count widened to reflect actual rule count).

### Surface #3 (no halt — recorded; AC family namespace check)

AC family `AC.VPC.5.*` chosen (Value Proposition Contract item 5 — distinguishes from `AC.V11.A.*` / `AC.V11.E.*` series). Pre-grep for collisions:

```bash
grep -rn "AC\.VPC\.5\." framework/ tests/ docs/ 2>/dev/null | head -5
```

Will be verified pre-build; expected zero hits. If collision, alternate prefix `AC.AF.*` (Ack-First) used.

### Surface #4 (no halt — recorded; substitution-token `{user_preferred_name}` reference in rule text)

The rule text references the user generically ("on user input requiring..."). The persona template uses `{user_preferred_name}` for first-person reference to the user. The ack rule text **does not need to use `{user_preferred_name}`** — it's a meta-rule about the persona's behaviour, not a sentence the persona speaks to the user. Plain "the user" is correct in the rule text. The test for `str.format` compatibility (`test_AC_O_1_template_is_str_format_compatible`) requires no escaping work since no new `{` / `}` literals appear in the new rule.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/VALUE_PROPOSITION.md`) — closes the perceived-latency gap between user message and persona response. Reduces translation burden ("did my message land?" → silence-then-90s-of-tool-calls). Stranger experience is part of the harness's surface area.
- **v0.1.x roadmap §2 v0.1.2 item 5** — ack-first persona contract amendment as defined by the dispatcher.
- **v0.1.x roadmap §5 Decision B** — hard rule with explicit triggers (locked).
- **AC.VPC.5.* per this sub-plan §4** — every AC ladders to the same parent.
- **Composes with:** Telegram-only channel rule (the ack lands on whatever channel is active — Telegram primary, terminal fallback per pause-on-outage); critical-thinking-on-deviations (ack pattern is tested against deviations like "this looks complex but is actually trivial"); summarize-and-surface-decisions (the ack is one of those surfaces).

**Ladders to:** AC.VPC.5.* → v0.1.2 release (alongside V11.A done + V11.E done + remaining v0.1.2 items pending) → v0.1.5 V2.B subagent personas (the ack-first rule is part of the methodology fluency that subagent personas inherit) → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (VPC.5.*)

AC family `AC.VPC.5.*` — collision-safe (pre-grep §2 Surface #3).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.VPC.5.1** | `framework/primary-persona/templates/persona-template/prompt.md` carries a new `### Acknowledge first on non-trivial requests` subsection under the `## Operational rules` section. The subsection text names: (a) the 5 explicit triggers from FIDRAFT — `≥3 tool calls`, `≥1 background dispatch`, `decision/judgment vs pure execution`, `file authoring vs reading`, `multi-paragraph/multi-question` (or each trigger's plain-language equivalent); (b) the trivial-back-and-forth carve-out (yes/no, single-fact lookup, simple status — at least one of these named); (c) the ack-shape literal ("got it — doing X" or equivalent quoted example); (d) the absence-as-observable-violation framing (mirrors F3's model-rationale absence-as-violation pattern). | New test in `framework/primary-persona/tests/test_AC_VPC_5_ack_first_rule.py` (the file authored by this amendment) covering all four checklists. |
| **AC.VPC.5.2** | The pre-existing `test_AC_O_1_six_operational_rule_sections_present` test widens to **eight** operational-rule sections (the prior six + `### Lean on the corpus` + `### Acknowledge first on non-trivial requests`); the `test_AC_O_1_named_section_count_is_eleven` test renames to `test_AC_O_1_named_section_count_is_thirteen` (or equivalent name reflecting the new count) and asserts 13 (5 traits + 8 rules). Both tests' tuples and assertion messages reflect the new counts. The widening composes the v0.1.2 item 5 addition with the pre-existing AC-text drift fix (Surface #2). | `pytest framework/primary-persona/tests/test_AC_O_1_default_archetype_prompt_md.py` passes post-build. |
| **AC.VPC.5.3** | The rule's hard-rule shape is observable in the prompt text: the rule name uses imperative voice; the trigger list is explicit (not "use judgment"); the carve-out is explicit; the absence-as-violation framing is explicit. The persona reading the rule cannot reasonably interpret it as a heuristic where ack is optional on complex requests. | New test in same file as AC.VPC.5.1; checks for hard-rule-marker keywords ("ALWAYS"/"first"/"required"/"observable violation") and absence of softening language (no "consider", no "may", no "if appropriate" near the rule). |
| **AC.VPC.5.4** | `str.format` compatibility preserved: `test_AC_O_1_template_is_str_format_compatible` continues to pass; no new unescaped `{` / `}` literals introduced by the new rule subsection. | Existing test passes post-build. |
| **AC.VPC.5.5** | Smoke: a tmp workspace scaffolded via the workspace-bootstrap persona-scaffold pathway (or via direct copy of `templates/persona-template/`) carries the ack-first rule text verbatim in its scaffolded `prompt.md`. | Smoke per §7. |
| **AC.VPC.5.S** | Sealed-component fence: `framework/primary-persona/` only. Edits limited to: `templates/persona-template/prompt.md` + `tests/test_AC_O_1_default_archetype_prompt_md.py` (modified) + `tests/test_AC_VPC_5_ack_first_rule.py` (new) + sidecar bumps. Plan-doc + manifest under `docs/plans/` (universal prefix). No edits outside fence. | `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under: (a) `framework/primary-persona/`, (b) `docs/plans/`. No file outside these prefixes. |

**ACs deliberately out of scope (NOT in v0.1.2 item 5):**
- A UserPromptSubmit hook that emits an automatic ack template (FIDRAFT names this as the "hardening path if drift observed"; out of scope per the dispatcher's locked Decision B — persona-level discipline is the right first cut).
- Other captured principles or persona-prompt rewrites (each is a separate amendment per Decision B and scope discipline).
- Updating subagent persona files (`.claude/agents/<name>.md`) — those land in v0.1.5 per the V2.B scope; this amendment touches only the primary-persona template.
- Updating any non-template prompt artefacts (e.g., a workspace's already-scaffolded `personas/<handle>/prompt.md`) — those are user-edited workspace-local copies, not framework-owned; the ack-first rule lands in new workspaces via the template, but pre-existing workspaces opt in by re-scaffolding or by manual copy from the template.

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
No new Claude-leverage shape introduced (the rule encodes a behavioural discipline, not a new primitive). The rule itself is built on top of the persona prompt — Claude's persona-prompt-as-system-prompt primitive is the leverage point. The hardening path (UserPromptSubmit hook) is named and deferred (FIDRAFT names "hook implementation is non-trivial — 'complex thought' requires LLM judgment that hooks don't have access to"; the simpler hook would be over-noisy). Persona-level discipline is the right first cut per Decision B.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The translation burden between user intent ("I sent a complex prompt and want to know it landed") and AI-effective execution (the persona reads files, dispatches, does the work) is reduced — the ack is the explicit acknowledgment that the message landed and work has begun.
- **Harness test:** PASS. The rule is the toolkit the persona draws from for every non-trivial input. Adds to the persona's behavioural-posture rule set; composes with all existing operational rules (Lean on the harness, Use the right tool, etc.).

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (where exactly within `## Operational rules` the new subsection lands; exact sentence ordering inside the rule subsection) inferable from constraints + the existing operational-rule subsection format precedent. No "options to rule on" beyond the rule-vs-heuristic question already locked in Decision B.

### Lens 4 — Prompt scope ↔ confidence
Very high confidence in outcome shape: dispatcher locked Decision B (hard rule with 5 explicit triggers); roadmap quoted the rule scope verbatim; FIDRAFT entry recorded the rationale + composition. Tight scope. Method inferable from constraints + prior FBE.x sub-plan format precedent.

### Lens 5 — Swarming
v0.1.2 item 5 is a leaf in the v0.1.2 release bundle. ACs partition lightly into (rule-text addition, test widening, smoke verification) but each binds to the same observable outcome (ack-first rule present in new-workspace persona prompts) and the work is single-shell-session shape. No sub-decomposition; coordination overhead would exceed any tighter-AC payoff.

---

## 6. File-by-file map

### Source-side delta (in fence, post-`loam amend apply`):

**Component — `framework/primary-persona/`:**

- `framework/primary-persona/templates/persona-template/prompt.md` (~25–40 LOC added):
  - New subsection `### Acknowledge first on non-trivial requests` under `## Operational rules`. Placement: **first subsection under `## Operational rules`** (positioned before `### Lean on the harness`) — rationale: ack-first fires on every non-trivial request before any other operational rule engages; placement reflects the temporal precedence (the persona reads the rule list top-down and the ack is the first move). Alternative placement (after `### Lean on the harness`) is acceptable; first-position chosen for clarity.
  - Subsection content (~25 lines of prose):
    - Opening sentence naming the rule as a hard rule (imperative voice).
    - The five triggers, named explicitly as a bullet list.
    - The carve-out (trivial back-and-forth).
    - The ack-shape literal example.
    - The absence-as-observable-violation framing.
- `framework/primary-persona/tests/test_AC_O_1_default_archetype_prompt_md.py` (~15–25 LOC modified):
  - `test_AC_O_1_six_operational_rule_sections_present` widens to **eight** rules (prior six + `### Lean on the corpus` + `### Acknowledge first on non-trivial requests`); rename to `test_AC_O_1_eight_operational_rule_sections_present`.
  - `test_AC_O_1_named_section_count_is_eleven` renames to `test_AC_O_1_named_section_count_is_thirteen`; tuple expands to 13 entries; assertion message updates to 13.
  - The module docstring updates to reflect the new operational-rule count and explicitly name `### Lean on the corpus` and `### Acknowledge first on non-trivial requests`.
- `framework/primary-persona/tests/test_AC_VPC_5_ack_first_rule.py` (NEW; ~80–120 LOC):
  - `test_AC_VPC_5_1_subsection_heading_present` — checks `### Acknowledge first on non-trivial requests` header is present under `## Operational rules`.
  - `test_AC_VPC_5_1_five_triggers_named` — checks each of the 5 triggers is named (substring markers per the FIDRAFT verbatim).
  - `test_AC_VPC_5_1_carve_out_named` — checks the trivial-back-and-forth carve-out is named (substring markers).
  - `test_AC_VPC_5_1_ack_shape_literal_present` — checks the "got it — doing X" literal example (or equivalent quoted ack-shape).
  - `test_AC_VPC_5_1_absence_as_violation_framed` — checks the absence-as-observable-violation framing.
  - `test_AC_VPC_5_3_hard_rule_imperative_voice` — checks for hard-rule-marker keywords AND absence of softening language near the rule.

### Sidecar bumps within sealed-component fence (1 component):

- `framework/primary-persona/tests/SEAL_COMMIT` — advances from `2416661` to v0.1.2-item-5 seal SHA via `loam amend seal`.
- `framework/primary-persona/tests/test_no_sealed_amendments.py` — BASELINE literal advances from `"c3b74b2"` to v0.1.2-item-5 pre-apply tip via `loam amend apply`.
- `framework/primary-persona/tests/SEAL_COMMIT.notes` — narrative target.

### Plan-doc + manifest (`universal_paths.prefixes: docs/plans/`):

- `docs/plans/v0-1-2-ack-first-persona-contract.md` (this file).
- `docs/plans/v0-1-2-ack-first-persona-contract.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/plans/v0-1-x-roadmap.md` — §8 method-decision register: add a v0.1.2-item-5 subsection with apply commit SHA + seal commit SHA + verification summary; update the v0.1.2 status row to add v0.1.2-item-5's seal SHA.

**TOTAL fence diff:** 1 source edit (`prompt.md`) + 1 modified test file + 1 new test file + 3 sidecar bumps + plan-doc + manifest YAML + parent §8 backfill (universal prefix).

---

## 7. Smoke verification

**Smoke A — direct template read (AC.VPC.5.1, AC.VPC.5.3):**

```bash
grep -A 30 "### Acknowledge first on non-trivial requests" \
    /Users/lukeivers/ivers-corp-pos-v2/framework/primary-persona/templates/persona-template/prompt.md
```

Expect post-fix: the subsection prints with all five triggers, the carve-out, the ack-shape, and the absence-as-violation framing visible.

**Smoke B — scaffold a tmp workspace (AC.VPC.5.5):**

```bash
SMOKE_DIR=/tmp/ack-first-smoke-$$
rm -rf "$SMOKE_DIR"
mkdir -p "$SMOKE_DIR"

cd /Users/lukeivers/ivers-corp-pos-v2/
.venv/bin/python -c "
from pathlib import Path
import sys
sys.path.insert(0, 'framework/workspace-bootstrap/src')
from loam.workspace_bootstrap.adapters.first_run_scaffold import _install_persona_directory
ws = Path('$SMOKE_DIR')
ws.mkdir(parents=True, exist_ok=True)
installed, persona_dir = _install_persona_directory(workspace_root=ws, handle='smoke-test')
print('installed:', installed)
print('persona_dir:', persona_dir)
prompt = (persona_dir / 'prompt.md').read_text()
assert '### Acknowledge first on non-trivial requests' in prompt, 'ack-first heading missing in scaffolded prompt'
assert 'got it' in prompt.lower(), 'ack-shape literal missing in scaffolded prompt'
assert 'trivial' in prompt.lower(), 'carve-out missing in scaffolded prompt'
print('PASS: ack-first rule present in scaffolded prompt at', persona_dir / 'prompt.md')
"
```

Expect post-fix:
- `installed: True`.
- `persona_dir: /tmp/ack-first-smoke-.../personas/smoke-test`.
- `PASS: ack-first rule present in scaffolded prompt at ...`.

**Smoke C — touched-only test rerun (AC.VPC.5.2 + AC.VPC.5.3 + AC.VPC.5.4):**

```bash
cd /Users/lukeivers/ivers-corp-pos-v2/
.venv/bin/pytest framework/primary-persona/tests/test_AC_O_1_default_archetype_prompt_md.py \
                  framework/primary-persona/tests/test_AC_VPC_5_ack_first_rule.py -v
```

Expect: all tests pass. `test_AC_O_1_*` widening is internally consistent; `test_AC_VPC_5_*` new tests pass against the new rule subsection.

**Failure modes:**
- Smoke A returns no match → ack-first heading missing; halt + surface.
- Smoke B's `assert` raises → scaffold pathway broken or template not picked up; halt + surface.
- Smoke C any failure → AC violated; halt + surface (per HT-1 below).

The smokes run **pre-seal** to confirm runtime contract before bookkeeping. Re-run post-seal is unnecessary (no source edits between).

---

## 8. Hard constraints

- 1 sealed-component sidecar bump in fence (`framework/primary-persona/`).
- No new external runtime deps (pure prose addition + test text).
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply` AND per FIDRAFT entry: the apply step does NOT auto-commit by design — manual commit via `git commit -m "chore(amend): ack-first persona contract apply ..."`.
- AC-prefix `AC.VPC.5.*` (collision-safe — verified pre-build).
- Auto-memory `MEMORY.md` NOT touched.
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`: only `framework/primary-persona/tests/` must pass post-seal.
- Smoke runs against an isolated `/tmp/ack-first-smoke-*` directory; no live workspace mutation.

---

## 9. Out of scope (per ODD §2.5)

- UserPromptSubmit hook for automated ack emission (deferred per Decision B; FIDRAFT names as "hardening path if drift observed").
- Subagent persona files (`.claude/agents/<name>.md`) — v0.1.5 V2.B scope.
- Updating any pre-existing workspace's local `personas/<handle>/prompt.md` — opt-in by user re-scaffold.
- Other v0.1.2 items (gh-create→push race docs, two-copies hedge, loam-amend ergonomics) — sequenced separately per dispatcher.
- Other captured principles or persona-prompt rewrites (each a separate amendment).
- Documentation updates beyond the new subsection itself + the touched test file's docstring.

---

## 10. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not silently extend) on:

- **HT-1:** Touched-files post-fix smoke fails any of §7 scenarios. Halt; surface; capture observation in status file.
- **HT-2:** `loam amend apply` rejects the manifest. Halt; surface; manifest shape may need adjustment or BASELINE pin is wrong.
- **HT-3:** `loam amend seal` rejects the seal. Halt; surface; usually means a touched-file lives outside the fence + universal admissions.
- **HT-4:** A file outside `framework/primary-persona/` + `docs/plans/` shows non-sidecar diff post-seal. Halt; surface; AC.VPC.5.S violation.
- **HT-5:** Surrounding-code ODD §2.5 violation discovered in any touched file beyond the Surface #2 already-named pre-existing AC drift. Halt; surface; do NOT silently extend or fix in-band.
- **HT-6:** AC family `AC.VPC.5.*` collides with prior amendment usage (per Surface #3 pre-build grep). Halt; surface; use alternate prefix `AC.AF.*`.
- **HT-7:** Test breakage in `framework/primary-persona/tests/` beyond the touched files (existing test asserts on the ack-first rule's absence, or pins the operational-rule count to 6 elsewhere). Halt; surface; investigate before in-band tightening.
- **HT-8:** Wall-time exceeds 60 min (dispatch hard cap). Halt with partial findings.
- **HT-9:** WD drifts to pos3. Halt immediately.
- **HT-10:** Sealed-component fence breach beyond `framework/primary-persona/`. Halt; surface.
- **HT-11:** Surface #2's pre-existing-drift in-band fix turns out to require touching a second test file (`test_AC_O_1_*` is not the only test pinning the operational-rule count). Halt; surface; the in-band scope widens beyond what this sub-plan §6 enumerated.

---

## 11. Risks

- **Risk: `### Acknowledge first on non-trivial requests` chosen heading conflicts with another test or downstream consumer that pattern-matches operational-rule headings.** Mitigation: pre-grep `framework/primary-persona/` for `### ` heading enumerations + `re_match` patterns on heading text. Verified pre-build; expected zero hits beyond `test_AC_O_1_*`.
- **Risk: the existing AC.O.1 test's "named-section count" assertion is also pinned in another test file or in module-level prose.** Mitigation: pre-grep `framework/primary-persona/tests/` for `count_is_eleven` / `eleven` / `six_operational` literals; verify no second site pins the count. Pre-build verification: `test_AC_alpha_6_L_eleven_sections_unchanged.py` asserts **presence** of L's eleven sections (additive-friendly) — does NOT pin the total count. The new `### Acknowledge first on non-trivial requests` heading lands additively without displacing L's eleven, so AC.α.6 continues to pass without modification. Per HT-11; HT-11 verified pre-build to NOT trigger.
- **Risk: rule text ordering within the subsection drifts from FIDRAFT verbatim and the test substring markers don't match.** Mitigation: test substring markers chosen for the FIDRAFT-named trigger labels (`≥3 tool calls`, `≥1 background dispatch`, etc.) which are stable; test passes regardless of subsection-internal ordering.
- **Risk: `_install_persona_directory` smoke fails due to copy-then-mutate logic touching the rule text.** Mitigation: Smoke B's assertion checks the rule text post-scaffold; if the scaffold mutates the prompt body (it should not — only `contract.yaml` mutates per `_install_persona_directory` docstring), the assertion catches it. Verified pre-build by reading `_install_persona_directory` source: it copies the template to a staging dir then mutates only `contract.yaml`'s `handle` + `is_starter`; `prompt.md` is byte-identical.
- **Risk: hard-rule keyword test (AC.VPC.5.3) is too strict and rejects natural-voice prose that satisfies the intent.** Mitigation: test checks for **at least one** of `ALWAYS`/`first`/`required` (imperative-voice signal) AND **absence** of softening words `consider`/`may`/`if appropriate` only **in close proximity** (same paragraph as the rule), not anywhere in the prompt; reasonable prose that uses imperative verbs without those exact keywords passes.

---

## 12. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Pre-grep validations** — AC.VPC.5.* collision check; operational-rule count pinning check (HT-11).
3. **Source edits** — `prompt.md` new subsection added; existing test (`test_AC_O_1_*`) widened in lock-step; new test file (`test_AC_VPC_5_*`) authored.
4. **Touched-only test rerun** — `pytest framework/primary-persona/tests/test_AC_O_1_default_archetype_prompt_md.py framework/primary-persona/tests/test_AC_VPC_5_ack_first_rule.py`.
5. **Smoke A + B + C** — execute §7 smokes; capture output to status file scratch.
6. **Source-edit commit** — `feat(v0.1.2): ack-first persona contract amendment — new operational rule under primary-persona template`.
7. **Manifest commit** — author `docs/plans/v0-1-2-ack-first-persona-contract.manifest.yaml`.
8. **`loam amend apply`** — invoke against the manifest. Produces apply-bookkeeping changes (BASELINE bump in `tests/test_no_sealed_amendments.py`).
9. **Manual apply commit** — `git commit -m "chore(amend): ack-first persona contract apply ..."`.
10. **`loam amend seal`** — produces deterministic seal commit; sidecar `SEAL_COMMIT` advances; narrative file written.
11. **Parent plan-doc backfill** — `docs/plans/v0-1-x-roadmap.md` §8 backfill v0.1.2-item-5 subsection (separate NEW commit; admitted via universal prefix).
12. **Status file write** — `/Users/lukeivers/pos3/workspace/.scratch/claude-output/ack-first-persona-contract-status-2026-05-03.md`.

NO `git commit --amend` at any point. NO push to any remote.

---

## 13. References

- **Parent plan / programme master:** `docs/plans/v0-1-x-roadmap.md` (§2 v0.1.2 item 5 + §5 Decision B + §8 register).
- **FIDRAFT entry:** `docs/FUTURE_IDEAS_DRAFT.md` line 143 ("Acknowledge-first on complex requests").
- **V11.E sub-plan precedent (sub-plan format mirrored here):** `docs/plans/v0-1-2-V11-E-graphiti-probe-skip.md`.
- **V11.A sub-plan precedent (single-component-fence shape):** `docs/plans/v0-1-2-V11-A-orchestrator-fix.md`.
- **Template source-of-truth:** `framework/primary-persona/templates/persona-template/prompt.md`.
- **Existing AC.O.1 test (the test that widens in lock-step per Surface #2):** `framework/primary-persona/tests/test_AC_O_1_default_archetype_prompt_md.py`.
- **Workspace-bootstrap scaffold pathway (smoke target):** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:_install_persona_directory`.
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no source edit yet beyond the plan itself).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §12).
  - `feedback_subagent_odd_violation_halt` (HT-1 through HT-11; Surface #2 explicit halt-and-surface).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to fence component only).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1–4 explicit; each surfaces a decision the dispatcher could review).
  - `feedback_specific_claims_verified_or_marked_guess` (every claim has a path/line citation or pre-build empirical observation).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (Surface #2's pre-existing-drift fix tightens the AC text, not the implementation).
  - `feedback_critical_thinking_on_deviations` (Surface #2's in-band-vs-separate-amendment trade-off enumerates outcome × cost × risk).
  - `feedback_always_specify_wd_in_dispatches` (WD pinned at top: `/Users/lukeivers/ivers-corp-pos-v2/`).
  - `feedback_value_proposition_as_prime_objective` (binds to AC.PO.1 + AC.PO.2 in §3).
  - `feedback_strict_autonomy_no_pause_for_authorized_work` (in-band Surface #2 fix is authorized scope per "halt and surface ODD violations in your work OR surrounding code"; resolution proceeds without re-asking).

---

## 14. AI-time band

- Predicted: **20–35 min, midpoint 27 min**; dispatch hard cap 60 min.
- Justification: per duration-estimation rubric — single-component-amendment band lower edge (the change is small + bounded; only one source file edited, two test files touched, no new external deps). Compared to V11.E's 1.5–2× V11.A wall-clock (two-fence + source edits + tests in both), v0.1.2 item 5 is 1× V11.A class (single fence, one source edit, two test files in the same fence). V11.A observed at ~15 min; v0.1.2 item 5 estimated 1.3–2.3× V11.A's pace due to the in-band Surface #2 widening (extra test edits) and the smoke against the scaffold pathway (extra verification step).

---

## 15. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Source-edit commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit (manual `chore(amend): ack-first persona contract apply ...`): `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of v0.1.2 item 5 sub-plan-doc. Ready to build.*
