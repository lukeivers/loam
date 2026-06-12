# Claude-leverage program — Slice 2: DOCTRINE (sub-plan-doc)

> **Status:** sub-plan-doc (buildable; manifest paired at
> `docs/plans/claude-leverage-program-s2-doctrine.manifest.yaml`).
> **WD:** `/Users/lukeivers/loam` (canonical loam).
> **Parent plan:** `docs/plans/claude-leverage-program.md` (master; Slice 2
> section + §2 rows 3–4 + D-CLP.1 + AC.CLP-DOC.\* family are the source of
> truth).
> **Build-model note (per the 2026-06-12 model-tier policy):** this plan is
> authored to OPUS-EXECUTABLE tightness — every named decision is RULED with
> a recommendation the builder inherits as law; no open judgment calls are
> left for build time. **No FABLE-REQUIRED carve-outs**: the one genuinely
> judgment-shaped surface (matcher precision, D-DOC.2/D-DOC.4) is bounded
> structurally (warn-tier default for low confidence + one-line escape hatch
> + coverage guard + the master's trigger-6 redesign tripwire), so its
> residual judgment is tuning inside a fence, not open design.
> **Predecessors (load-bearing):**
> - Master plan ratified 2026-06-11; D-CLP.1 RULED at master: **layered
>   enforcement (plan-time named section + dispatch-time structural check +
>   corpus-fed catalogue)** — doctrine text alone has already failed in this
>   workspace (`feedback_structural_enforcement_on_recurrence`).
> - Slice 1 CURRENCY sealed `c41f9473` (2026-06-11):
>   `framework/tools/capability-refresh/` + `docs/capability-corpus/` is the
>   live, refresh-kept catalogue this slice's check consults. Slice-1 §14
>   D-CUR.5 handoffs land HERE: gap-analysis §3.2 (stale
>   `claude-feature-awareness`) + §3.3 (loam-skills README count mismatch).
> - pos3 prototype skills (READ-ONLY reference; graduation = loam-proper
>   equivalents, pos3 is NOT edited):
>   `/Users/lukeivers/pos3/.claude/skills/{claude-feature-awareness,tool-selection-rubric,primitive-rationale-check}/SKILL.md`.
> - Research artefact: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/claude-primitives-gap-analysis-2026-06-11.md`
>   (§3.2/§3.3 discrepancies; §6 the unused-primitive gap table the doctrine
>   exists to close).
> - Hook-latency precedent (Tier-0, measured):
>   `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-responsiveness-analysis-2026-06-11.md`
>   §1.2 — PreToolUse chain total 1.7–2.9 ms measured from
>   `workspace/.scratch/keep-pace/hook-latency.log`; the "~2 ms budget"
>   precedent. §3 below resolves how this slice's check honours it.
> **BASELINE candidate:** `a8bbc3f7c74dfb35b6d4443ebc15535a206560fe` (HEAD of
> main at sub-plan authoring; builder CONFIRMS at `loam amend apply`).
> **Status-file target:** `docs/STATE.md` change-log + `docs/release-roadmap.md`
> §8 register row + master plan §2/§10 backfill.
> **Quality bar:** every AC outcome-shaped; ★ AC.CLP-DOC.2 is the
> outcome-altitude AC; scope-descriptive AC IDs; NO version numbers
> pre-assigned; LOCAL only (commit, never push).
> **PUBLIC-ACTION NOTE: this slice has NO public-action steps and NO
> Anthropic-API-key dependency anywhere** (the check's fire path is
> file-reads only — D-DOC.2; any LLM-routed follow-on is explicitly out of
> scope, §7.5).

---

## §1 Summary / TL;DR

**What ships:** D-CLP.1's layered enforcement made real — when loam (persona
or dispatched agent) is about to do work directly or build a bespoke
equivalent of a catalogued Claude primitive, an observable check fires on
the production path. Three deliverables, dependency-ordered:

1. **The graduated skills (the advisory layer + the user-facing catalogue
   surface).** The three pos3 prototypes graduate into
   `plugins/loam-skills/skills/` under their existing names —
   `claude-feature-awareness` (thin catalogue-lookup over
   `docs/capability-corpus/`; carries NO independently-maintained capability
   claims — the structural fix for gap-analysis §3.2),
   `tool-selection-rubric` (the seven-decision framework, facts re-verified
   live at build, capability facts replaced by corpus pointers), and
   `primitive-rationale-check` (the `primitive-rationale:` audit-trail
   discipline the structural check enforces). One canonical copy ends the
   pos3/loam dual-surface risk (master F2.6); pos3-local retirement is a
   named out-of-fence handoff. The loam-skills README is rewritten during
   graduation (gap-analysis §3.3 fix — counts re-derived from disk;
   `meta-decision-haiku` labeled planned-not-yet-packaged per the sealed
   lsk1 F3 ruling, NOT deleted).
2. **The dispatch-time structural check (the enforcement layer).** A new
   PreToolUse hook in `plugins/dev-sdlc/hooks/` (sibling to
   `agent_guard.py`; matcher `Task`) inspects every Agent dispatch prompt
   for bespoke-equivalent work-shapes traced to corpus entries. Two-tier
   posture: high-precision bespoke-shape match with no
   `primitive-rationale:` line → DENY with a reason that names the matched
   primitive and the one-line fix; lower-confidence match → allow +
   `systemMessage` warn. The `primitive-rationale:` line IS the escape
   hatch and IS the audit record. Every fire NDJSON-logged (agent-guard log
   pattern). Wired into bootstrapped workspaces via the
   `first_run_settings.py` marker+stanza mechanism (A4 precedent) — hence
   the hands-off-lifecycle fence admission.
3. **The plan-time leg.** `plugins/dev-sdlc/docs/conventions/plan-docs.md`
   (+ the plan template) gains a REQUIRED named "Primitive check" item in
   the plan-doc shape: every plan that introduces a new mechanism names the
   native primitives considered. This plan-doc itself carries the first
   conforming instance (§2bis).

**AC families:** AC.CLP-DOC.1–4 (carried from master, outcomes verbatim) +
AC.CLP-DOC.5–8 (slice-tighter: skill-currency, README-truth, check-latency,
catalogue-coverage) + AC.CLP-DOC.S (seal-diff). ★ = AC.CLP-DOC.2.

**Key decisions baked (full register §10):** D-DOC.1 plan-time shape
(convention-doc REQUIRED section; no plan-lint hook in-slice); D-DOC.2
check mechanism (dev-sdlc PreToolUse `Task` hook, two-tier deny/warn,
NDJSON audit, first_run_settings wiring); D-DOC.3 escape hatch
(`primitive-rationale:` line = hatch = audit record; env/sentinel
emergency-off); D-DOC.4 catalogue consultation (matchers trace to corpus
entries, bidirectional coverage guard, no live fetch/LLM at fire time);
D-DOC.5 graduation shape (three skills, names kept, claims live in corpus);
D-DOC.6 currency handoffs (§3.2 fixed structurally in-slice; §3.3 in-fence);
D-DOC.7 fence (three components).

**F2 on scope realism:** honest single-to-double cycle (master band
45–120 min AI-time; with the three-component fence + hook tests, estimate
60–150 min, midpoint ~100 min — estimate-grade). The genuinely uncertain
part is matcher precision (F2.1) — bounded by posture + hatch + the
master's trigger-6 redesign tripwire, not by more plan-time design.

---

## §2 Placement decisions

| Surface | Placement | Rationale |
|---|---|---|
| Graduated skills ×3 | **EXTEND `plugins/loam-skills/skills/`** — `claude-feature-awareness/`, `tool-selection-rubric/`, `primitive-rationale-check/` (names kept) | Master §2 row 3 (locked: extend loam-skills; skills are the auto-discoverable primitive, Lens 1). Names kept per D-DOC.5 — the trio (catalog → decide → record) is referenced by name across the memory corpus + gap analysis; renaming buys nothing and breaks references. |
| loam-skills README + tests | **In-fence** (loam-skills component) | §3.3 handoff: counts re-derived from disk during graduation; existing `test_AC_LSK_*` suites are in-fence and updated only where their own AC text requires (derived-from-disk tests should absorb the three new skills without edit — builder verifies). |
| Dispatch-time check | **NEW hook `plugins/dev-sdlc/hooks/`** (sibling to `agent_guard.py`; matcher `Task`) + its tests under `plugins/dev-sdlc/tests/` | Master §2 row 4 (locked: hook surface, dev-mode dispatch path first). The dev-sdlc PreToolUse guard family (objective-binding / tdd / bash / agent) is the proven envelope + NDJSON-audit pattern; the new check is a fifth sibling, same contract. |
| Check matcher data | **Data file inside `plugins/dev-sdlc/`** (exact path/format = method) — every row names its corpus entry | D-DOC.4. Matchers are pointers + regexes, NOT capability claims — no second claims surface (D-CLP.5 lesson honoured); coverage guard keeps it from drifting against the refresh-kept corpus. |
| Settings wiring for the new hook | **`framework/hands-off-lifecycle/hooks/first_run_settings.py`** (+ its tests) — marker string + PreToolUse stanza entry, exactly as `agent_guard.py` is wired (A4 precedent) | Verified at plan-author time: `_LOAM_PRE_TOOL_USE_COMMAND_MARKERS` in first_run_settings.py is the single wiring surface for every shipped PreToolUse guard; there is no dev-sdlc-local alternative that reaches freshly-bootstrapped workspaces. This is the third fence component — admitted ONLY for this wiring + its tests (D-DOC.7). |
| Plan-time leg | **`plugins/dev-sdlc/docs/conventions/plan-docs.md`** §1/§2 + `plugins/dev-sdlc/templates/plan/dev-discipline.md` | In dev-sdlc fence. AC.CLP-DOC.3's convention-doc requirement; the template carries the section so generated plans inherit it. |
| pos3 prototype retirement | **OUT of fence — named handoff** (master §7.6: workspace-side chore) | pos3 is read-only reference for this cycle. One canonical copy is achieved by shipping the canonical copy; deleting the pos3 copies is a pos3-workspace chore tracked dispatcher-side. |
| Runtime/persona-path check (NORMAL-USE workspaces) | **OUT of scope — named follow-on** (§7.2) | Master §2 row 4: "dev-mode dispatch path first, persona/runtime path second." The runtime path needs a non-dev-sdlc home (normal users don't load dev-sdlc) — its own cycle. |

## §2bis Primitive check (self-application — first conforming instance)

Native primitives considered for each new mechanism this plan introduces:

- **Dispatch-time check → Claude Code PreToolUse hook (`Task` matcher).**
  Native hook event; no bespoke interception layer. Alternatives considered:
  `prompt`/`agent` hook handler types (LLM-judge in the hook) — rejected
  in-slice: fire-path latency + subscription-only constraint;
  named as possible coverage-widening follow-on (master F2.2).
- **Advisory layer → SKILLs** (auto-discoverable, Lens 1) — not CLAUDE.md
  prose, not a memory rule (doctrine-as-text already failed).
- **Catalogue → the existing Slice-1 corpus** — no new catalogue built; the
  check consumes what `capability-refresh` keeps current.
- **Audit trail → the existing NDJSON guard-log pattern** — no new
  observability mechanism.

## §3 Halt-and-surface BEFORE build (recorded at sub-plan authoring)

1. **Hook-latency halt trigger RESOLVED at plan time (dispatch-named).** The
   ~2 ms PreToolUse precedent (responsiveness analysis §1.2, measured from
   `hook-latency.log`) applies to broad-matcher (`*`) per-tool-call hooks.
   This check is **matcher-scoped to `Task`** — it fires only on Agent
   dispatches (rare, inherently minutes-long operations), adds ZERO latency
   to every other tool call by Claude Code's matcher primitive (not by our
   code), and its fire path is file-reads only (no network, no LLM —
   D-DOC.2 constraint). AC.CLP-DOC.7 pins the bound. This is the same
   envelope as the existing `agent_guard.py` (same event, same matcher),
   which is live today without a responsiveness finding against it. NOT a
   violation of the budget; recorded so the builder doesn't re-litigate.
2. **No-API-key halt trigger RESOLVED at plan time (dispatch-named).** No
   candidate mechanism in this plan touches the Anthropic API. The deny/warn
   logic is deterministic regex/string matching; the skills are static
   content. (An LLM-judge tier would require `claude -p` at minimum — out of
   scope, §7.5.)
3. **Sealed-guard collision risk, named:** primary-persona's AC.α.8 test
   (`test_AC_alpha_8_no_capability_content_outside_admitted_paths.py`)
   greps the repo for corpus schema markers (`Capability leverage spine`,
   `[user-intent phrasings]`, `No-cross-class-write`) and admits only named
   prefixes — `plugins/loam-skills/` and `plugins/dev-sdlc/` are NOT
   admitted. **Constraint baked into D-DOC.5/D-DOC.2: graduated skill
   bodies + hook + matcher data MUST NOT contain the schema-marker strings**
   (they point at corpus entries by path/name, they don't replicate the
   schema). Builder runs the AC.α.8 test as a pre-seal ride-along (the
   F-SEAL-GUARD-SWEEP-FLOOR lesson from Slice 1's two post-seal
   correctives). If it trips and the wording fix is not obvious → halt
   trigger §8.5; NEVER widen into primary-persona.
4. **`meta-decision-haiku` is intentional, not garbage.** Verified at
   plan-author time: the sealed `loam-skills-ac-lsk1-root-cause` plan (its
   F3 finding) ruled the dir "intentionally referenced in master plans but
   not yet a SKILL package — no action required"; roadmap v0.7.0 still names
   it. The §3.3 README fix therefore labels it planned-not-yet-packaged
   rather than deleting the row or the dir (D-DOC.6). The gap analysis's
   "README claims a skill that doesn't exist" finding is real; the fix is
   truthful labeling, not removal.
5. **One master-plan wording note:** master AC.CLP-DOC.3's verification
   ("inspect ... the next sealed plan-doc") is partially post-seal by
   construction. In-slice verification: the convention doc + template carry
   the requirement AND this plan-doc itself is the first conforming
   instance (§2bis). The "next sealed plan-doc conforms" observation rides
   the roadmap row as a checkpoint, mirroring Slice 1's AC.CLP-CUR.4
   pending-observation pattern. Not a contradiction; recorded as the
   loose-AC-text reading this plan adopts (fix-the-AC-not-the-implementation
   does not apply — the master text already permits this reading).

## §4 Spec-objective placement

- **Binds:** master AC.CLP.2 (the slice that delivers leg 1 is sealed,
  family green) and operationalises the guard side of master AC.CLP.1's
  machinery. AC.CLP-DOC.\* is the strictly-tighter per-slice family
  (Lens 5).
- **Ladders to:** AC.PO.2 (protection floor — re-implementing a worse
  bespoke equivalent of a maintained primitive is a default AI betrayal;
  master §4 names legs 1–3 as the AC.PO.2 instance) and AC.PO.1 (the
  persona reaches for the right primitive without the user knowing
  primitives exist).
- **Lens 1, squared:** this slice IS Lens 1 made structural — and its own
  build prefers the primitives (§2bis): native hook event, native skill
  discovery, the existing corpus, the existing guard-log pattern.
- **Lens 2:** primary-persona test — the persona stops hand-deriving
  "is there a primitive for this" (the catalogue skill + check carry it).
  Harness test — three skills + one guard added to the toolkit. Pass/pass.

## §5 Acceptance criteria (`AC.CLP-DOC.*`)

★ = outcome-altitude. Every AC passes the method-in-AC test (a method other
than the recommended one can satisfy it).

| AC | Outcome | Verification |
|---|---|---|
| AC.CLP-DOC.1 | A loam-shipped, auto-discoverable surface exists that maps work-shapes to native Claude primitives (the catalogue/rubric the pos3 prototypes prove out), kept current by Slice 1's machinery or sourced from the corpus. | Skills present in the shipped loam-skills plugin (discoverable: valid frontmatter per the existing LSK suite); every capability claim in their bodies points at a corpus entry or carries a build-time live-verification record; no claim contradicts the corpus. |
| AC.CLP-DOC.2 ★ | On the production dispatch path, work that builds a bespoke equivalent of a catalogued primitive without a recorded primitive-consideration produces an observable check event, with no pre-arranged state. | Author a deliberately-bespoke test dispatch (e.g. "build a polling loop that re-checks X every hour" with no `primitive-rationale:` line) through the production PreToolUse path (the hook invoked exactly as Claude Code invokes it, envelope on stdin); observe the deny/warn event + its audit record. Production entry-point, no pre-arranged state. |
| AC.CLP-DOC.3 | Plan-docs authored after the seal carry a named primitive-check section (the plan-time leg of the layered enforcement), and the convention doc says so. | Convention doc + plan template carry the REQUIRED section; this plan-doc's §2bis is the first conforming instance; "next sealed plan-doc conforms" rides the roadmap row as a post-seal checkpoint (§3.5). |
| AC.CLP-DOC.4 | The check has an explicit escape hatch for the cases where bespoke IS correct, and using it leaves an audit-visible record. | Exercise the hatch (a bespoke-shaped dispatch WITH a `primitive-rationale:` line) → allowed; find the record (the line in the dispatch prompt + the NDJSON fire log naming hatch-use). Exercise the emergency-off → allowed + logged. |
| AC.CLP-DOC.5 | The graduated skills carry no stale or unverifiable capability claims: every capability fact is either a pointer to a corpus entry or was re-verified live at build time, and the specific stale items named in gap-analysis §3.2 do not appear in the canonical copies. | Read the three skill bodies; trace each capability fact; grep for the §3.2 stale claims (e.g. the pre-2.1.172 recursion framing, the "29 events as of v2.1.141" snapshot framing presented as current). |
| AC.CLP-DOC.6 | The loam-skills README matches disk: the skill count derives from what exists, every named skill either exists as a package or is explicitly labeled planned-not-yet-packaged, and gap-analysis §3.3's mismatch is gone. | Re-derive counts from `plugins/loam-skills/skills/`; read the README; `meta-decision-haiku` labeled per the lsk1 F3 ruling. |
| AC.CLP-DOC.7 | The check adds no observable latency cost outside its target: tool calls other than Agent dispatches are unaffected (matcher-scoped), the fire path performs no network I/O and no LLM invocation, and a standalone fire on a representative envelope completes within 100 ms p95 on the dev machine. | Inspect the registered matcher; code-audit + test-assert no network/LLM on the fire path; time ≥20 standalone fixture fires, assert p95 ≤ 100 ms. (Bound rationale: §3.1 — the ~2 ms budget governs broad-matcher hooks; `Task`-scoped fires are rare and gate minutes-long operations; 100 ms is invisible at that grain and ~30× tighter than dispatch setup itself.) |
| AC.CLP-DOC.8 | The check's primitive knowledge cannot silently drift from the corpus: every catalogued claude-code corpus entry has corresponding check coverage or a named exclusion, every coverage element names an existing corpus entry, and a corpus entry added later without coverage is observable (a test or run flags it). | Run the coverage guard against the live corpus tree; add a fixture corpus entry in a test → observe the flag; remove a referenced entry in a fixture → observe the flag. |
| AC.CLP-DOC.S | Seal-diff discipline: only `plugins/dev-sdlc/`, `plugins/loam-skills/`, `framework/hands-off-lifecycle/` + universal paths changed in BASELINE..seal; the AC.α.8 ride-along is green at seal. | `test_no_sealed_amendments.py` per component at the confirmed BASELINE + the primary-persona AC.α.8 test run as ride-along (§3.3). |

## §6 Build steps (method-level guidance; builder's call per ODD §1.1, decisions in §10 are LAW)

Manifest: `docs/plans/claude-leverage-program-s2-doctrine.manifest.yaml`.
`loam amend apply` → build → `loam amend seal` per the amendment-cycle
convention (named explicitly per
`feedback_dispatch_explicit_loam_amend_apply`).

1. **Graduate the skills** (loam-skills fence): author the three SKILL.md
   packages from the pos3 prototypes per D-DOC.5 — re-verify every carried
   capability fact live against the changelog/docs FIRST (§8.1); replace
   catalogue facts with corpus pointers; strip pos3-local paths and the
   schema-marker strings (§3.3). Rewrite the README per D-DOC.6. Existing
   LSK/SKTRI derived-from-disk tests run; tests-first for any new assertion
   surface.
2. **The check** (dev-sdlc fence): tests-first against the AC.CLP-DOC.2/4/7/8
   behaviours with fixture envelopes (the agent_guard test corpus is the
   shape precedent); then the hook + matcher data per D-DOC.2/3/4; NDJSON
   audit per the `_gate_helpers.append_audit_line` sibling format.
3. **The wiring** (hands-off-lifecycle fence): marker string + stanza entry
   in `first_run_settings.py` exactly as `agent_guard.py` is wired
   (idempotent re-merge precedent); extend the existing first-run-settings
   tests minimally.
4. **The plan-time leg** (dev-sdlc fence): convention-doc §1/§2 gain the
   REQUIRED "Primitive check" item per D-DOC.1; plan template updated.
5. **Pre-seal ride-alongs:** primary-persona AC.α.8 test (§3.3) + the
   touched components' full suites. Seal; bookkeeping per §9.

## §7 Out of scope

1. **pos3 prototype retirement** — workspace-side chore (master §7.6);
   named handoff to the dispatcher; the canonical copies shipping is this
   slice's whole contribution to it.
2. **Runtime/persona-path check for NORMAL-USE workspaces** — master §2
   row 4 "second"; needs a non-dev-sdlc home; own cycle, named follow-on.
3. **Plan-lint hook for the plan-time leg** — D-DOC.1 ships the convention
   requirement advisory-at-plan-time; a lint hook is the named escalation
   IF plan-time non-adherence is observed (structural-enforcement-on-
   recurrence applies to the convention itself).
4. **Wider gap-table adoptions** (`/btw`, `/fork`, Notification hook, …) —
   master §7.4; the doctrine surfaces them organically.
5. **LLM-judge coverage tier** (master F2.2 coverage-widening) — possible
   follow-on; would use `claude -p` + spawn isolation, never an API key.
6. **Slice 3 surfaces** (`/goal`/`/loop` adoption rulings) — parallel
   slice; this slice's rubric content references those primitives but the
   bespoke-vs-native RULING on `autonomy_continuation.py` is Slice 3's.

## §8 Halt triggers (in-flight)

1. Any capability claim about to be carried into skill content fails live
   re-fetch at build time → halt only if the discrepancy implicates corpus
   correctness (that is Slice-1 machinery territory — surface as a
   pending-delta question, don't silently edit the corpus: it is OUT of
   this fence); otherwise correct the skill draft and proceed.
2. Any mechanism turns out to require an Anthropic API key → halt, surface
   (dispatch-named; §3.2 says no mechanism should).
3. The check cannot meet AC.CLP-DOC.7's bound on the fire path → halt,
   surface (do NOT ship a slower check or widen its matcher; the latency
   constraint is a protection-floor term, dispatch-named).
4. Satisfying an AC requires editing any component not in this manifest
   (primary-persona per §3.3 is the predicted instance) → halt, surface;
   never silently widen.
5. The AC.α.8 ride-along trips and no wording-level fix inside the fence
   resolves it → halt with the proposed resolution; never add admitted
   prefixes to primary-persona's guard from this cycle.
6. An existing sealed loam-skills test (LSK/SKTRI/SKILLCAP families)
   fails against the graduated skills in a way its own AC text does not
   license updating → halt, surface (loose-AC-vs-implementation is a
   dispatcher ruling, `feedback_loose_AC_text_fix_AC_not_implementation`).
7. (Standing, from master trigger 6, carries past the seal:) the check
   blocks legitimate work twice in real use without the hatch resolving
   it → redesign the check; over-tight enforcement is its own failure
   mode (F4).

## §9 Bookkeeping

- `docs/STATE.md` change-log entry at seal.
- `docs/release-roadmap.md` §8 register row (with the "next sealed
  plan-doc conforms to the primitive-check convention" post-seal
  checkpoint marker, §3.5).
- Master plan backfill: §2 rows 3–4 placement finalised; §10 D-CLP.1
  marked delivered-by-this-slice; Slice-1 §14 D-CUR.5 handoff items
  (§3.2/§3.3) marked landed.
- pos3-retirement handoff surfaced to the dispatcher at completion
  (NOT performed by this cycle).
- §14 register populated at build + seal (SHA backfill via
  `loam amend seal --plan-doc`).

## §10 Named decisions + F2 Ruthless Feedback

### Named decisions (RULED — the builder inherits these as law; deviation = halt trigger 4-class surface, not a silent re-decision)

**D-DOC.1 — Plan-time check shape.**
Alternatives: (a) required named plan-doc section, convention + template
(advisory at plan-time); (b) a plan-doc lint hook on Write/Edit to
`docs/plans/`; (c) both.
**RULING: (a).** Evidence: the layered design (D-CLP.1) already has its
structural leg at dispatch time — the last gate before work executes; a
plan that skipped the section but dispatches with a rationale line is
caught, a plan with the section but a rationale-less bespoke dispatch is
also caught. A plan-lint (b) adds a second always-on Write-path hook (the
in-thread-guard precedent shows Write-path hooks accrete cost) for a
violation the dispatch gate already catches downstream. (b) becomes the
named escalation on observed recurrence (§7.3 —
`feedback_structural_enforcement_on_recurrence` applied to the convention
itself). Mechanically: `plan-docs.md` §1 gains a "Primitive check" required
section (one short table or bullet list: each new mechanism the plan
introduces → native primitive chosen or bespoke + why); §2 sub-plan shape
inherits it; `templates/plan/dev-discipline.md` gains the slot. F4: HIGH.

**D-DOC.2 — Dispatch-time check mechanism.**
`primitive-rationale: PreToolUse hook (Task matcher) — the native
last-gate on the production dispatch path; sibling envelope to the four
existing dev-sdlc guards.`
Alternatives: (a) PreToolUse hook, matcher `Task`, deterministic
prompt-inspection; (b) PreToolUse `prompt`/`agent` LLM-judge handler;
(c) Stop-hook retrospective audit; (d) UserPromptSubmit-side injection.
**RULING: (a)**, with this pinned shape:
- **Home:** `plugins/dev-sdlc/hooks/` (new file, sibling to
  `agent_guard.py`); tests under `plugins/dev-sdlc/tests/`. Same stdin
  envelope contract, same dev-mode short-circuit-allow as the sibling
  guards, same fail-open posture on internal error (a broken check must
  never block all dispatches).
- **Inspects:** `tool_input.prompt` (+ `description`) of every `Task`
  call: (i) bespoke-equivalent work-shape detection via the D-DOC.4
  matcher data; (ii) presence of a `primitive-rationale:` line anywhere in
  the prompt.
- **Posture (two-tier):** HIGH-precision match (bespoke-build verb +
  primitive-shape pattern, per matcher row tier) AND no
  `primitive-rationale:` line → **DENY**, reason text names the matched
  primitive + corpus entry + the one-line fix ("add `primitive-rationale:
  <primitive or bespoke> — <reason>` or use the primitive"). LOWER-tier
  match → **allow + `systemMessage` warn** naming the same. No match →
  no-op allow. Rationale-line present → allow (hatch, D-DOC.3), fire
  logged as hatch-use.
- **Audit:** every fire (deny / warn / hatch / off / no-op) appends one
  NDJSON line to a workspace-local log per the `_gate_helpers`
  sibling format (AC.AG.5 precedent).
- **Wiring:** marker + stanza in
  `framework/hands-off-lifecycle/hooks/first_run_settings.py`, exactly the
  A4 agent-guard mechanism (idempotent re-merge).
Evidence for (a) over (b): fire-path determinism keeps AC.CLP-DOC.7
satisfiable and needs no model call (no API key, no `claude -p` latency in
a synchronous gate); (c) fires after the turn — too late, the bespoke
thing is already built (D-CLP.1's argument against structural-only applies
inside the turn too); (d) inspects the user's words, not the dispatch —
wrong altitude: the failure being prevented is the AGENT's bespoke-build,
which is visible only in the dispatch prompt. Deny-tier justification:
warn-only is doctrine-as-text wearing a hook costume (the named failed
pattern); the deny costs exactly one line to clear, and that line is the
audit record the doctrine wants anyway. F4: HIGH on mechanism, MEDIUM on
matcher precision (bounded — see posture, hatch, §8.7).

**D-DOC.3 — Escape-hatch policy.**
Alternatives: (a) env-var/sentinel off-switch only; (b) the
`primitive-rationale:` line as the sanctioned hatch + env/sentinel
emergency-off; (c) no hatch (hard block).
**RULING: (b).** The rationale line is simultaneously the hatch AND the
audit record (master AC.CLP-DOC.4 wants exactly this pair): a dispatcher
who consciously chooses bespoke writes one line saying why, the dispatch
proceeds, and the line persists in the dispatch prompt + the NDJSON log.
`primitive-rationale: bespoke — <reason>` is explicitly valid (bespoke IS
sometimes correct; the doctrine demands consideration, not surrender).
Emergency-off: `LOAM_PRIMITIVE_CHECK=off` env var OR a workspace sentinel
file (the in-thread-guard hatch style), both logged when exercised. (c)
violates master trigger 6's lesson before the first fire. F4: HIGH.

**D-DOC.4 — Catalogue-consultation mechanism.**
Alternatives: (a) hook parses `docs/capability-corpus/` entries at fire
time to derive matchers; (b) matcher data file inside dev-sdlc, every row
naming its corpus entry, with a bidirectional coverage guard; (c) frozen
keyword list in the hook source.
**RULING: (b).** Evidence: (a) is attractive (zero derived surfaces) but
corpus entries are prose + `[user-intent phrasings]` are USER-voice
phrasings — dispatch prompts are work-brief voice; deriving high-precision
DISPATCH-shape regexes from user-voice prose at fire time is the kind of
silent-quality judgment a deterministic gate shouldn't make per-fire. (c)
is the frozen list the master explicitly forbids ("must read the *current*
corpus... not a frozen list" — master §6.2) and recreates the staleness
failure. (b) keeps claims in exactly one place (rows carry NO capability
claims — only regexes + a corpus-entry pointer + tier), and the coverage
guard makes drift OBSERVABLE: a test asserts every `claude-code/` corpus
entry has a matcher row or a named exclusion AND every row's pointer
resolves — so when Slice-1's refresh lands a NEW corpus entry, the
dev-sdlc suite goes red at its next run and the gap is surfaced rather
than silent (AC.CLP-DOC.8; layered-pipeline traceability discipline).
Fire path stays file-reads-only. F4: HIGH.

**D-DOC.5 — Graduation shape for the three pos3 prototypes.**
Alternatives: (a) copy the three verbatim; (b) merge into one
"primitive-selection" skill; (c) three skills, names kept, contracts
re-cut: awareness = thin catalogue-lookup over the corpus (no
independently-maintained claims), rubric = decision framework with
capability facts replaced by corpus pointers + remaining facts
live-verified at build, rationale-check = the audit-trail discipline whose
structural enforcement is now the D-DOC.2 hook (the skill documents the
shape the hook enforces — the rubric's own decision-B "hard invariant →
both" applied to itself).
**RULING: (c).** Evidence: (a) ships gap-analysis §3.2's staleness into
the canonical surface on day one (claude-feature-awareness self-describes
as "going stale fast"; its catalogue body is the 2026-05-14 snapshot) —
recreating the exact failure Slice 1 fixed; (b) destroys the
catalog → decide → record trigger separation the pos3 dogfood validated
(three different fire moments) and breaks corpus-wide by-name references.
Names kept. Hard constraints riding this ruling: skill bodies carry NO
pos3-local paths, NO schema-marker strings (§3.3), and NO `/goal`-vs-
bespoke RULINGS (that's Slice 3 — the rubric may name both, ruling-free).
F4: HIGH.

**D-DOC.6 — The two deferred currency handoffs (Slice-1 §14 D-CUR.5).**
- **§3.2 (`claude-feature-awareness` stale): IN-SLICE, structurally.** The
  graduated canonical copy carries no independently-maintained claims
  (D-DOC.5), so it cannot go stale the way the prototype did; the pos3
  copy's deletion is the out-of-fence handoff (§7.1). RULED: this fully
  discharges the handoff — the fix vehicle named by Slice 1 §7.3 is
  exactly this graduation.
- **§3.3 (loam-skills README mismatch): IN-SLICE, in-fence.** README
  rewritten during graduation: counts re-derived from disk (22 SKILL.md
  pre-graduation, 25 after — builder re-derives, never copies these
  numbers), `meta-decision-haiku` row kept but labeled
  planned-not-yet-packaged (the sealed lsk1 F3 ruling + live roadmap
  references make deletion wrong — §3.4); the stray `__pycache__`-only dir
  content may be cleaned, the dir's row stays. RULED.
F4: HIGH on both.

**D-DOC.7 — Fence shape.**
Alternatives: (a) two components (dev-sdlc + loam-skills), wiring deferred;
(b) three components (+ hands-off-lifecycle for the settings wiring);
(c) wide fence (+ primary-persona for guard-list pre-extension).
**RULING: (b).** Evidence: without the first_run_settings wiring the hook
never reaches a bootstrapped workspace's settings — AC.CLP-DOC.2's
"production path, no pre-arranged state" fails by construction (a)
(verified: `_LOAM_PRE_TOOL_USE_COMMAND_MARKERS` is the single shipped
wiring surface; there is no dev-sdlc-local path to settings). (c) violates
the Slice-1 §3.3 precedent — primary-persona stays OUT; the AC.α.8
interaction is handled by content constraints + ride-along, not fence
admission (§3.3). hands-off-lifecycle admission is scoped by intent to
`first_run_settings.py` + its tests; any other hands-off-lifecycle edit is
out-of-intent (the fence can't mechanically subdivide a component — the
seal-diff review enforces the intent). F4: HIGH.

### F2 — honest doubts, named

1. **Matcher precision is the weakest joint.** Deterministic regexes over
   free-prose dispatch briefs WILL have both false negatives (a bespoke
   build phrased unrecognisably sails through — master F2.2 already names
   the in-turn evasion) and false positives (deny-tier on a legitimate
   non-bespoke dispatch). The structure bounds the damage — false positive
   costs one line via the hatch; trigger §8.7 forces redesign on
   recurrence; warn-tier absorbs the low-confidence middle — but the
   matchers themselves are tuning, and the first weeks of fires are the
   real calibration data. Named, not closable at plan time.
2. **The check watches dispatches, not in-thread work.** A bespoke
   equivalent built directly in-thread (persona grinding it out without a
   Task call) bypasses the Task matcher entirely. Partially mitigated
   elsewhere (the in-thread work-budget guard pushes heavy authoring INTO
   dispatches, where this check sees it), but the gap is real and is the
   master's F2.2 restated at this slice's altitude.
3. **AC.CLP-DOC.3's full claim matures post-seal.** The "next sealed
   plan-doc conforms" observation can't precede the next plan-doc; the
   roadmap checkpoint (§3.5) keeps it honest, mirroring Slice 1's
   AC.CLP-CUR.4 pattern. The in-slice green is convention + template +
   this plan's own §2bis.
4. **Three-component fences widen the seal window.** Three sealed
   components in one cycle is more surface than Slice 1 carried. The
   hands-off-lifecycle leg is deliberately minimal (one marker + one
   stanza + tests), but the F-SEAL-GUARD-SWEEP-FLOOR lesson says sibling
   guards bite at seals — hence the explicit ride-along list in §6.5
   rather than hoping.
5. **Dev-mode-first means loam's normal users get the skills but not the
   gate this cycle.** The advisory layer ships to everyone; the structural
   layer guards the dev dispatch path where the proven failures live.
   That's the master's own sequencing (§2 row 4), but it means the
   doctrine is enforcement-backed for us and advisory-only for users until
   the follow-on (§7.2). Named so nobody mistakes this slice for the
   whole leg.

## §11 Provenance trail

- Master plan: `docs/plans/claude-leverage-program.md` (Slice 2 section,
  §2 rows 3–4, §5 AC.CLP-DOC.\*, §6.2, §10 D-CLP.1; trigger 6).
- Slice 1 sealed: `docs/plans/claude-leverage-program-s1-currency.md`
  (seal `c41f9473`; §7.3/§7.4 + §14 D-CUR.5 handoffs; §13 post-seal
  correctives = the F-SEAL-GUARD-SWEEP-FLOOR lesson this plan's
  ride-alongs encode).
- pos3 prototypes (read 2026-06-12, read-only):
  `/Users/lukeivers/pos3/.claude/skills/{claude-feature-awareness,tool-selection-rubric,primitive-rationale-check}/SKILL.md`.
- Gap analysis: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/claude-primitives-gap-analysis-2026-06-11.md`.
- Hook-latency precedent: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-responsiveness-analysis-2026-06-11.md`
  §1.2 (PreToolUse 1.7–2.9 ms measured; UserPromptSubmit ~220–260 ms
  dominant) — basis of §3.1 + AC.CLP-DOC.7.
- Live verifications (sub-plan-author, 2026-06-12): canonical HEAD
  `a8bbc3f7` clean on main; highest manifest counter on disk = 184
  (claude-leverage-program-s1-currency) → 185 next free;
  `plugins/loam-skills/skills/` = 23 dirs / 22 SKILL.md
  (`meta-decision-haiku/` = `__pycache__` only); loam-skills README:45
  names meta-decision-haiku; sealed lsk1 F3 ruling at
  `docs/plans/sealed/loam-skills-ac-lsk1-root-cause.md` ("no action
  required", intentional); AC.α.8 guard markers + ADMITTED_PREFIXES read
  from `framework/primary-persona/tests/test_AC_alpha_8_*.py`;
  `_LOAM_PRE_TOOL_USE_COMMAND_MARKERS` read from
  `framework/hands-off-lifecycle/hooks/first_run_settings.py` (the five
  guards + three ECC hooks all wire there); agent_guard envelope/audit
  contract read from `plugins/dev-sdlc/hooks/agent_guard.py`; corpus
  overlay sections confirmed in all four `claude-code/` entries;
  conventions read from `plugins/dev-sdlc/docs/conventions/plan-docs.md`;
  plan template at `plugins/dev-sdlc/templates/plan/dev-discipline.md`.
- Manifest precedents: `docs/plans/sealed/loam-doc-consistency-batch-a.manifest.yaml`
  (loam-skills entry), `docs/plans/sealed/amendment-137-legacy-pos-amend-name-docs-corpus-sweep.manifest.yaml`
  (dev-sdlc entry), Slice-1 manifest (counter-confirm-at-apply pattern).
- Memory corpus: `feedback_structural_enforcement_on_recurrence`,
  `feedback_scope_descriptive_ac_ids`,
  `feedback_test_outcome_altitude_required`,
  `feedback_version_numbers_at_release_time`,
  `feedback_no_anthropic_api_key`,
  `feedback_dispatch_explicit_loam_amend_apply`,
  `feedback_loose_AC_text_fix_AC_not_implementation`,
  `feedback_layered_pipeline_traceability_discipline`.

## §13 §status (recorded at build)

_Populated by the builder: per-AC verdict table + evidence._

## §14 Method-decision register (populated at build + seal)

| ID | Decision | Builder narrative (at build) | SHA (at seal) |
|---|---|---|---|
| D-DOC.1 | Plan-time leg: convention + template section | _at build_ | _at seal_ |
| D-DOC.2 | Dispatch-time hook shape + posture | _at build_ | _at seal_ |
| D-DOC.3 | Escape hatch + emergency-off | _at build_ | _at seal_ |
| D-DOC.4 | Matcher data + coverage guard | _at build_ | _at seal_ |
| D-DOC.5 | Three-skill graduation + content re-cut | _at build_ | _at seal_ |
| D-DOC.6 | §3.2 discharged structurally; §3.3 README fix | _at build_ | _at seal_ |
| D-DOC.7 | Three-component fence; hands-off-lifecycle minimal admission | _at build_ | _at seal_ |
