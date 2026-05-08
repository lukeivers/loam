# Research — corpus-inlining SessionStart hook

**Author:** plan-research dispatch (canonical pos-v2)
**Date:** 2026-04-28
**FIDRAFT origin:** `docs/FUTURE_IDEAS_DRAFT.md` entry "SessionStart corpus_gate should inline corpus content into additionalContext, not just verify presence." (captured 2026-04-28; relocated from pos3/framework dirty FIDRAFT during post-#68 sync recovery).
**Working directory of record:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Spec binding:** ODD §5.1.1 (relocate-vs-eliminate); CLAUDE.md Lens 1 (Claude-leverage-first); the recurring-failure-class motivation captured in the FIDRAFT entry.
**Composes on:** A1 substrate (`framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` + `corpus_load_session_start.py`); #45 `extra_inner_hooks` registry; #46 persona session-start emitter; #67 `_resolve_corpus_path` reader fall-through.

**Pre-flight staleness check (verified 2026-04-28):** `git log --grep="corpus-inlining\|corpus.load.inline\|corpus.gate.inline"` returns only the FIDRAFT-capture commit (`76cec04`, docs-only). A1's `corpus_load_sentinel.py` and `corpus_load_session_start.py` are substrate-only — the CLI's docstring explicitly notes *"The hook does not emit any `additionalContext` — the sentinel is consumed by future gates, not by the model directly. Should the future composition surface the sentinel into `additionalContext` (per the plan-doc Lens 1 note), this CLI's stdout becomes the surface; today it is empty."* No corpus-inlining hook has shipped. Proceed.

---

## 1. Executive summary

1. **The recurring failure class.** The pOS v2 session-start corpus-load discipline is structurally enforced *for sentinel presence* (A1's `corpus_load_session_start.py` writes the per-(workspace, session) sentinel; the persona's `compose_session_fields` emits a `[present]` / `[MISSING]` dossier into `additionalContext`). It is **not structurally enforced for *reading*** — the obligation to actually load the file contents into the model's context window lives in MEMORY.md prose ("always read corpus at session-start") and CLAUDE.md §1 / §2 advisory. Per ODD §5.1.1, the substrate has *relocated* the failure class (rule moved from CLAUDE.md to MEMORY.md to dossier-presence) but not *eliminated* it: every new session opens against fresh context with the corpus paths *referenced*, not *loaded*. Luke flagged the resulting miss explicitly today ("you haven't read the session corpus yet... you literally never do it").

2. **The structural-elimination shape.** A new SessionStart inner hook reads the always-load corpus and emits its content into `additionalContext`. The persona observes the corpus *already in context* on every session-start. "Read the corpus" stops being a discipline and becomes a substrate property — the model cannot bypass it, because the bypass requires the substrate to fail. Per ODD §5.1.1 this is elimination (the failure class becomes unrepresentable), not relocation.

3. **Token-budget infeasibility forces a tier-based partition (HALT-equivalent finding).** The full set of 6 corpus files Luke cited (CLAUDE.md, odd-methodology, odd-in-pos, VALUE_PROPOSITION, STATE, FUTURE_IDEAS) totals **~195 k chars ≈ 49 k tokens** — **19.5× the persona's 10 k-char `additionalContext` cap** and a non-trivial fraction of a 200 k-token model context. Strategy (a) full-inline-verbatim is **structurally infeasible** at the persona-cap layer and **prohibitively expensive** at the model-context layer. The dispatch named tier-based partition as one of three candidates; the math forces it from "candidate" to "required". Recommendation: **strategy (b) with explicit always-load partition + on-demand tier**, partition derived from the existing `dev-mode-manifest.yaml`'s `always_loaded` (mode-aware via A1's `compute_corpus_paths_required`).

4. **Composition is clean.** A1's substrate already computes the mode-aware required-corpus path set; the new hook *reads the same paths* and emits content. Path resolution reuses #67's `_resolve_corpus_path` fall-through (workspace-root → `<workspace>/framework/<rel>`). The hook registers through #45's `extra_inner_hooks` registry as the fourth concrete consumer (loam-mode #45 + persona #46 + corpus-load-sentinel A1 + this hook). The hook also writes `corpus_paths_loaded` into the existing A1 sentinel — turning A1's empty-list field into an active record of what the new hook actually inlined this session.

5. **Mode default.** DEV MODE only. The Lens 2 harness test favours universal (every workspace benefits from corpus context), but the Lens 1 + token-economy reality is that NORMAL USE workspaces *have no shared corpus to read* (no `docs/odd-methodology.md`, no `docs/STATE.md`). Inlining what doesn't exist degrades to no-op; emitting CLAUDE.md alone in NORMAL USE is the existing #46 persona-emitter's job. **Default DEV MODE; NORMAL USE no-op via A1's mode bit.** This matches A1 D4 (ODD-discipline gates DEV-MODE-only) — corpus-load discipline IS an ODD-discipline gate's source signal.

6. **Decisions surfaced for owner ruling: 4** (numbered §11 below). Highest-stakes: **D-CI.1** (always-load partition: full `dev-mode-manifest.yaml` always-load set vs. a tighter "session-start essentials" subset) — drives the per-session token cost. **D-CI.2** (corpus content shape: full-content verbatim vs. headers + first-N-lines vs. structured digest) — drives both token cost and recall fidelity. **D-CI.3** (caching across sessions: re-emit every session vs. content-hash skip optimisation) — premature-vs-justified. **D-CI.4** (path-resolver reuse: lift `_resolve_corpus_path` to a shared util vs. duplicate the 3-line helper inside hands-off-lifecycle, matching A1's `WORKSPACE_STATE_SUBDIR` precedent).

---

## 2. Background — the failure class today

### 2.1 What ships now

- **A1 corpus-load sentinel** (`framework/hands-off-lifecycle/hooks/corpus_load_session_start.py`) — fires on SessionStart, writes `<workspace>/workspace/.pos/session-state/<session_id>.json` with shape `{session_id, corpus_paths_required, corpus_paths_loaded: [], state ∈ {loaded, partial, missing}, created_at}`. The CLI's stdout is empty (no `additionalContext` emission).
- **#46 persona session-start emitter** (`framework/primary-persona/src/session_start_emitter.py` + `session_start_gate.py::compose_session_fields`) — emits text under the 10 k-char `ADDITIONAL_CONTEXT_CAP` containing `corpus_gate_state`, a `corpus_paths` list with `[present]`/`[MISSING]` markers, missing-paths diagnostic, amendments-in-flight list, service state, cost headroom. **The text mentions the paths; it does not contain their contents.**
- **MEMORY.md** carries `feedback_session_start_discipline` ("always read corpus at session-start before any non-trivial pos-v2 turn"). Advisory only.
- **CLAUDE.md** session-start-discipline section names the corpus paths in backticks; `discover_baseline_corpus` parses the section and returns those paths to the persona's gate. The names are structural; the **read-into-context** is not.

### 2.2 The miss, in ODD §5.1.1 framing

§5.1.1 test: *"Can a future code change re-introduce the same failure class without active discipline?"* For corpus-loading today: every new session can re-introduce the failure with zero code change — the persona simply opens, observes the dossier, sees `[present]` markers, and acts on the user's prompt without firing the Read tool against the named files. The substrate guarantees the *paths* are present; it does not guarantee the *contents* enter context.

The mechanism (sentinel write; dossier emission with presence markers) is structurally correct. The failure class it addresses is "did the corpus *exist*?" The failure class Luke flagged today is "did the corpus *enter context*?" — an adjacent, distinct failure class the existing substrate does not target.

§5.1.1 sharpening: structural over advisory is necessary; *eliminating the failure class* over *relocating it* is sufficient. Inlining the corpus content into `additionalContext` makes the failed state unrepresentable (the model literally has the bytes; it cannot operate without them being in context). This is the eliminate path.

### 2.3 Why this hook is the right surface

- **Claude Code's SessionStart `additionalContext` channel** is the canonical place to seed model context at session-start. Every other contributor (loam-mode mode-routing, persona dossier, A1 sentinel-write) already lives there. Adding corpus content is the same shape, one more contributor.
- **The hook fires once per session.** Token cost is paid at session-start, not per-turn. Compaction discards it, so repeat-reads on long sessions still need work, but that's compaction-adjacent territory (out of scope).
- **The substrate (A1) already names the path set.** The new hook reads what A1 says is required; no new manifest, no new corpus list.

---

## 3. Token budget — the load-bearing constraint

### 3.1 Measured costs (2026-04-28, canonical pos-v2 HEAD)

| File | bytes | approx tokens (4 chars/token) |
|------|------:|------:|
| `CLAUDE.md` | 4,758 | 1,189 |
| `docs/odd-methodology.md` | 35,116 | 8,779 |
| `docs/odd-in-pos.md` | 50,205 | 12,551 |
| `docs/VALUE_PROPOSITION.md` | 11,429 | 2,857 |
| `docs/STATE.md` | 10,762 | 2,690 |
| `docs/FUTURE_IDEAS.md` | 82,864 | 20,716 |
| **TOTAL** | **195,134** | **48,783** |

The 4-chars-per-token approximation is conservative for prose-heavy English markdown; real BPE token counts run ~5-15% lower for Claude's tokeniser. Even at 0.85× = ~41 k tokens, the cost is the same order of magnitude.

### 3.2 Per-stanza caps observed in the substrate

- **Persona's `ADDITIONAL_CONTEXT_CAP` = 10,000 chars (~2.5 k tokens).** A model_validator on `SessionPayload` raises `AdditionalContextCapExceededError` at construction. The cap is per-stanza, applied to the persona's emitted text only.
- **No global cap surfaced in `hands-off-lifecycle/hooks/`.** Each SessionStart inner hook has its own stdout; Claude Code merges them. The new hook is not bound by the persona's 10 k cap, but the *cumulative* cost is what burns context tokens.

### 3.3 What full-inline (strategy a) would cost

49 k tokens × every session-start = 49 k tokens of pre-prompt context per session. On a 200 k-context model that's ~25% of the window dedicated to corpus before the first user turn. Compaction will discard it later in the session anyway. The cost is structurally infeasible at the persona-cap layer (cap exceeded by 19.5×) and prohibitively expensive at the model-context layer (no ceiling defined for cumulative inner-hook output, but 49 k is order-of-magnitude wrong for a session-start contributor).

### 3.4 What tier-based partition (strategy b) costs

Always-load tier candidates with the dispatch's "always-load" + manifest data:

- **CLAUDE.md** (1.2 k tokens) — design-lenses + output conventions; load-bearing for every turn. **always-load.**
- **VALUE_PROPOSITION.md** (2.9 k tokens) — prime-objective-of-pos-v2 per `feedback_value_proposition_as_prime_objective`; every dispatch ladders up to it. **always-load.**
- **STATE.md** (2.7 k tokens) — current cycle status; refreshed every amendment. **always-load** (DEV MODE) — orientation requires it.
- **odd-methodology.md** (8.8 k tokens) — methodology reference; load-bearing for ODD §2.5/§4/§5 reasoning that fires on most turns. **on-demand or always-load** (decision D-CI.1).
- **odd-in-pos.md** (12.6 k tokens) — pos-v2-specific ODD application. **on-demand or always-load** (decision D-CI.1).
- **FUTURE_IDEAS.md** (20.7 k tokens) — strategic future captures; rarely turn-load-bearing. **on-demand.**

**Always-load minimum (CLAUDE.md + VALUE_PROPOSITION.md + STATE.md):** ~6.8 k tokens. Within reason for a session-start contributor.

**Always-load with both ODD docs:** ~28 k tokens. Acceptable on a 200 k context but bordering on the line where a session-start contributor stops being cheap.

**On-demand tier:** persona reads via Read tool when the turn requires it. The dossier already names the paths; the user observes "the corpus is here, on-demand for the rest." Latency cost is ~1 Read tool call when needed; lossless.

### 3.5 What headers-plus-first-N-lines (strategy c) costs

Approximation: each file's first 50 lines + section headings only.

- 6 files × ~50 lines × ~80 chars = ~24 k chars ≈ 6 k tokens.

Comparable to strategy (b)'s lean always-load tier; but **lossy** on content the persona actually needs (§5.1.1 reasoning is in odd-methodology §5, not §1; line 408 not line 50). Recall fidelity for "what does ODD say about X" plummets when the actual prose is absent. Strategy (c) is a compromise that **buys a per-file cost ceiling at the price of recall fidelity**; (b) gets recall fidelity right for the always-load set + lossless on-demand for the rest.

**Recommendation: strategy (b)**, with the always-load tier defaulting to the lean set (CLAUDE.md + VALUE_PROPOSITION.md + STATE.md) and the methodology docs surfaced as on-demand pointers in the dossier (already the existing surface).

### 3.6 The "always-load" surface already exists

Critical finding: `docs/rebuild/dev-mode-manifest.yaml` already declares the `always_loaded` partition. A1's `compute_corpus_paths_required(workspace_root, mode)` already computes it via `loam_mode.selector.select_corpus`. The new hook does not need to invent a partition — it consumes what A1 names. This is the cleanest composition shape and obviates a chunk of D-CI.1 (the manifest IS the answer; the only open question is "should the always-load partition's manifest itself be tightened post-hook to keep token costs sane?").

---

## 4. Composition with the substrate

### 4.1 With A1's corpus-load sentinel

A1's sentinel write contract reserves `corpus_paths_loaded: list[str]` (empty at session-start; *"future hooks may append"*). The new corpus-inlining hook is exactly that future hook:

1. New hook fires AFTER A1's sentinel writer in the SessionStart fan-out (ordering: A1 writes empty `corpus_paths_loaded`; corpus-inlining reads required-corpus from A1's sentinel — or recomputes via `compute_corpus_paths_required` directly — emits content; updates `corpus_paths_loaded` with what it actually inlined).
2. A1's sentinel becomes a record of *both* what was required *and* what was loaded into context. Future gates (A2 / A3 / A4 family) can consult `state == "loaded" AND corpus_paths_loaded == corpus_paths_required` to assert "the model has the corpus in context for this session."
3. The proof-of-read shape elevates A1's substrate from passive (paths required) to active (content emitted + recorded). No A1 contract change required — A1's docstring already anticipates this composition.

Open question (D-CI.5, see §11): does the new hook update A1's sentinel directly, or does the new hook write its own sentinel and a future amendment unifies them? Recommendation: update A1's sentinel — the field is reserved for it, the file is the single source of truth.

### 4.2 With #45's `extra_inner_hooks` registry

The new hook is the **fourth** concrete consumer of `merge_session_start`'s `extra_inner_hooks` parameter. Registration is a one-line addition to `hands-off-lifecycle/hooks/first_run_helper.py` (or wherever the SessionStart stanza is composed for first-run / supervisor registration). The marker substring (`corpus_inline_session_start.py` or similar) joins `_POS_V2_COMMAND_MARKERS` in `first_run_settings.py` so the merge function recognises it as pos-v2-owned on re-merge.

Order matters for the `corpus_paths_loaded` write: **after** A1's sentinel writer (so the file exists), **before** persona's session-start emitter (so the persona's dossier can include `corpus_inlined: true|partial|missing` metadata if desired in a later pass). Today's order (A1 → persona) becomes (A1 → corpus-inline → persona) or (A1 → persona → corpus-inline) depending on whether the persona's dossier should carry the inlined-marker. **Recommendation:** A1 → corpus-inline → persona, so the persona's dossier reflects the inlined state. Builder confirms exact ordering.

### 4.3 With #67's `_resolve_corpus_path` reader fall-through

The new hook reads corpus content; path resolution must support workspace-root override (D-shape: `<workspace>/CLAUDE.md`) AND fall-through to `<workspace>/framework/CLAUDE.md` (canonical-clone shape) per amendment #67's binding.

`_resolve_corpus_path` is currently a private helper in `framework/primary-persona/src/session_start_gate.py`. Two reuse shapes:

- **(i)** Lift to a shared util (e.g. `framework/orchestrator/scripts/path_resolver.py` or a new shared module) — clean DRY, but adds a sealed-component boundary crossing.
- **(ii)** Duplicate the 3-line helper inside `framework/hands-off-lifecycle/hooks/`, matching the precedent A1 set with `WORKSPACE_STATE_SUBDIR` (canonical home: `workspace_paths.py`; A1 duplicated the constant rather than cross the boundary). The helper is small enough (10 LOC) that duplication does not generate maintenance debt.

**Recommendation: (ii) duplicate**, matching A1's precedent. The seal-diff stays clean. D-CI.4 surfaces this for owner ruling because it is the only meaningful method-shape choice; both shapes are correct.

### 4.4 With persona's #46 emitter (cap composition)

The new hook's emitted text is independent of the persona's 10 k cap (separate stdout). But the persona's dossier could **mention** the inlined-corpus state once the new hook updates A1's sentinel — the dossier reads the sentinel via A1's `read_corpus_load_sentinel` and includes a one-line `corpus_inlined: true` marker. This is a follow-on to the new hook, not the new hook itself.

---

## 5. Inline-strategy candidates (the dispatch's three)

### 5.1 Strategy (a) — full content inlined verbatim

**Token cost:** ~49 k tokens per session.
**Pros:** maximal recall fidelity; "the corpus is in context" is literally true for every named file.
**Cons:** structurally infeasible at persona-cap (19.5× cap); prohibitively expensive at model-context (~25% of 200 k window pre-prompt); compaction wastes the cost; long-sessions need re-emit anyway.
**Verdict:** **REJECTED** on token economy.

### 5.2 Strategy (b) — partition into always-load + on-demand tiers, inline always-load only

**Token cost (lean always-load set):** ~6.8 k tokens per session.
**Token cost (always-load + ODD docs):** ~28 k tokens per session.
**Pros:** token cost bounded; recall fidelity preserved for the always-load files; on-demand pointer-shape for the rest is the existing dossier behaviour (no regression). The partition source already exists (`dev-mode-manifest.yaml`).
**Cons:** "always-load" decision is owner-discretion (D-CI.1); some recall loss for on-demand files vs. (a).
**Verdict:** **RECOMMENDED**.

### 5.3 Strategy (c) — headers + first-N-lines inlined

**Token cost:** ~6 k tokens for first-50-lines × 6 files; comparable to (b) lean.
**Pros:** uniform per-file ceiling; no "tier" decision required.
**Cons:** lossy by construction — section headings + first 50 lines miss most of the content the persona actually needs (e.g. ODD §5.1.1 lives at line 408 of odd-methodology.md, not in the first 50 lines). Recall fidelity is materially worse than (b).
**Verdict:** **REJECTED** in favour of (b)'s tier-shape.

### 5.4 Hybrid candidate — strategy (b) for always-load tier + section-anchor pointers for on-demand tier

**Variation on (b):** always-load tier inlines full content; on-demand tier emits a structured pointer-block listing the file + its top-level section anchors (extracted via existing markdown-heading regex), so the persona can call Read with line-ranges directly.

**Token cost:** lean always-load (~6.8 k) + ~500 chars of structured section-anchor pointers per on-demand file × 3 files = ~7 k tokens total.
**Pros:** persona has *exact section anchors* to read on-demand without scanning the file head; matches the FIDRAFT entry's "or always-load partition + heads" wording. Cheaper than (b)+ODD-docs always-load while preserving recall efficiency.
**Cons:** more substrate to author (heading-extractor); risk of stale section-anchors if a corpus doc's headings drift.
**Verdict:** **viable extension to (b)**; surfaces in D-CI.2 as a refinement.

---

## 6. Mode partition — DEV MODE only vs. universal

**Lens 2 harness test:** does this add to the toolkit the persona draws from? In DEV MODE workspaces (canonical pos-v2; pos3-derived clones with the dev_intent flag), the persona's toolkit is the corpus. In NORMAL USE workspaces, the persona's toolkit is whatever `pos-new-workspace` scaffolded — which today does NOT include `docs/odd-methodology.md` etc.

**A1 D4 lock:** "ODD-discipline gates DEV-MODE-only; structural-enforcement gates universal where blast-radius matters." The corpus-inlining hook is read-only emission, no refusal — it doesn't fit the structural-enforcement-blast-radius axis. It IS an ODD-discipline gate's source signal: "the model has read the corpus" is the precondition the future ODD-discipline gates (A2 binding-gate, A3 TDD-guard) want.

**Argument for DEV MODE only:** (i) NORMAL USE workspaces have no shared corpus to read; (ii) inlining what doesn't exist degrades to no-op anyway; (iii) consistency with A1 D4. **Recommendation: DEV MODE only**, via A1's `workspace_mode(workspace_root)` helper. NORMAL USE → no-op (hook fires, observes mode, exits 0 with empty stdout).

**Argument for universal:** (i) every workspace benefits from CLAUDE.md being inlined (it's always-load even in NORMAL USE per `dev-mode-manifest.yaml`). **Counter:** the persona's #46 emitter already inlines a CLAUDE.md-derived dossier in NORMAL USE; the new hook would duplicate. **Verdict: DEV MODE only**, with the option to widen to "universal where there's a corpus to load" via a later amendment if NORMAL USE workspaces evolve to have shared docs.

---

## 7. Caching across sessions — premature?

**The question:** SessionStart fires on every new session. Re-reading 6 files every session is fine if cheap (it is — 195 k chars on local SSD reads in ~5-20 ms). The token cost (~7 k tokens for lean always-load × every session) accumulates across days but is paid in additionalContext tokens, not in disk I/O.

**Skip-inline-if-content-unchanged optimisation:** hash the always-load set's contents; cache the hash + the rendered text in `<workspace>/workspace/.pos/session-state/corpus-inline.cache.json`; on next session, recompute hash, skip inline if hash matches AND the persona has been signalled the corpus is already loaded somehow.

**Verdict: PREMATURE.** The signal "persona already has corpus loaded" cannot be derived from a previous session's cache — sessions are isolated context windows. The model on session N+1 has no memory of session N. Skipping the inline because the content hashed the same on session N saves zero tokens for session N+1's model context. The only optimisation that buys real cost is "don't read 6 files from disk" — at <20 ms total, this is below the SessionStart 5 s envelope by 250×. Not worth implementing. **Skip caching; re-emit every session.**

If a future "compaction-resilient corpus-load" amendment lands (e.g. via Claude Code's PreCompact hook or a long-context-session checkpoint), caching becomes meaningful. Today, premature.

---

## 8. Failure modes

### 8.1 Corpus file missing (one of the always-load set)

**Soft-fail-with-warning:** emit the inlinable subset; mark the missing file's slot with a structured marker (`[missing] docs/STATE.md`); update A1's sentinel `state` accordingly (`partial` if some present, `missing` if none).

**Hard-fail:** refuse to emit any inline (exit 0, empty stdout); rely on persona's existing `[MISSING]` dossier markers to surface the absence.

**Recommendation: soft-fail-with-warning.** Hard-fail throws away useful context for an environmental issue. The persona's existing dossier already surfaces missingness; the new hook's job is content emission, and partial content > no content.

### 8.2 Corpus file exceeds expected size

**Truncate:** apply a per-file ceiling (e.g. 50 k chars); truncate at ceiling with a visible `[truncated at N chars]` marker.
**Skip:** drop the file from the inline; mark `[skipped: size N chars exceeds ceiling]`.
**Fail:** exit 0, empty stdout.

**Recommendation: per-file ceiling + truncate-with-marker.** A surprise large file (e.g. FUTURE_IDEAS.md grew to 500 k chars) shouldn't blow the SessionStart budget; truncation is cheaper than failing entirely.

The lean always-load tier (CLAUDE.md + VALUE_PROPOSITION.md + STATE.md) caps natural file sizes well under any reasonable ceiling (largest is 11 k chars). The truncate-marker is a defensive cap, not a routine code path.

### 8.3 SessionStart envelope unparseable / workspace_root absent

A1's CLI already handles every parse-failure path with `return 0`. The new hook follows the same pattern (mirror A1's `main()` exactly).

### 8.4 Hook exceeds 5 s SessionStart envelope

Reading 6 files from disk on a modern SSD: <20 ms. Even with worst-case rotational disk + cold cache: <500 ms. The envelope is not at risk for the lean always-load tier. If a future refinement adds heading-extraction (strategy hybrid §5.4), regex-parsing 6 files of total ~195 k chars: <100 ms. Still safe. The envelope risk is theoretical.

---

## 9. Lens 1 — Claude-leverage

The hook leans on three Claude Code primitives:

1. **SessionStart inner-hook surface** + **`additionalContext` channel** — the canonical place to seed model context at session-start. Same surface A1 / #45 / #46 already use.
2. **`extra_inner_hooks` registry (#45)** — the harness registry. Fourth concrete consumer.
3. **A1's mode bit** + **A1's sentinel** — workspace-mode partition + the proof-of-read record. The hook composes on the substrate, does not re-invent it.

The hook is a recursive instance of the structural-enforcement programme research's asymmetric finding: *Claude Code's hook surface IS the structural-enforcement surface.* Corpus-load discipline becomes structural by being expressed as a SessionStart contributor — exactly the pattern A1/A2/A3/A4 already use. No new substrate; one more consumer of an existing one.

---

## 10. Lens 2 — Harness + primary-persona value

**Primary-persona test (does this reduce translation burden?).** Today the persona must remember the rule "always read the corpus before any non-trivial pos-v2 turn." The reduction is direct: *the corpus is in context already* — no rule to remember, no Read tool calls to dispatch at session-start, no failure mode if the rule is forgotten.

**Harness test (does this add to the toolkit?).** Yes — *the corpus is in context* is a new harness primitive: every dispatch the persona makes can rely on the always-load corpus being available without a per-dispatch Read call. The dispatch overhead drops; the per-dispatch corpus-read cost is paid once at session-start, not N times across the session.

The hook satisfies both Lens 2 tests. Harness-shaped.

---

## 11. Decisions surfaced for owner ruling

### D-CI.1 — Always-load partition (token-cost / recall trade-off)

The lean always-load tier (CLAUDE.md + VALUE_PROPOSITION.md + STATE.md) costs ~6.8 k tokens; widening to include both ODD docs costs ~28 k tokens.

**Options:**
- **(a)** Lean always-load only (~6.8 k tokens). Methodology docs on-demand via dossier pointer (today's behaviour, persona reads on-demand).
- **(b)** Lean always-load + odd-methodology + odd-in-pos (~28 k tokens). Both ODD docs always available.
- **(c)** Reuse the existing `dev-mode-manifest.yaml` `always_loaded` set verbatim — but the manifest's `always_loaded` set today includes whole component-source globs (cost-governance/**, hands-off-lifecycle/**, etc.) which is wildly wrong for inlining. Strategy (c) requires manifest tightening or a new "session-start essentials" subset field.

**Recommendation: (a) lean.** ODD docs are referenced by the persona on most turns but not every turn; reading-on-demand via dossier pointers preserves the persona's existing pattern and keeps session-start cost ~15% of (b). When a turn requires methodology, the Read call is one tool call ~5-50 ms; the persona absorbs the latency once per relevant turn vs. paying ~21 k tokens every session.

### D-CI.2 — Corpus content shape

**Options:**
- **(a)** Full content verbatim for always-load tier; pointer (just the path) for on-demand tier (today's dossier shape).
- **(b)** Full content for always-load tier; structured section-anchor pointers (markdown headings + line ranges) for on-demand tier (hybrid §5.4).
- **(c)** Headers + first-50-lines for everything (strategy c).

**Recommendation: (b) hybrid** — always-load full content; on-demand section-anchor pointers. Adds ~1.5 k tokens for the heading-extractor output (3 on-demand files × ~500 chars each); buys precise Read line-ranges for the persona. Marginal cost, large recall benefit.

### D-CI.3 — Caching across sessions

**Options:**
- **(a)** Re-emit every session. Disk I/O ~20 ms; token cost paid every session.
- **(b)** Hash-skip cache.

**Recommendation: (a) re-emit every session.** Caching saves zero model-context tokens; sessions are isolated context windows; the only saving is disk I/O which is sub-millisecond per file. Premature.

### D-CI.4 — Path-resolver reuse

**Options:**
- **(a)** Lift `_resolve_corpus_path` to a shared util (orchestrator or new shared module).
- **(b)** Duplicate the 3-line helper inside `framework/hands-off-lifecycle/hooks/`, matching A1's `WORKSPACE_STATE_SUBDIR` precedent.

**Recommendation: (b) duplicate.** Matches A1's established convention; keeps the seal-diff window clean (no cross-component edit); the helper is small enough that duplication is not maintenance debt. Path-resolver fall-through logic is identical at call sites; correctness is verified by tests in BOTH components, not by symbol identity.

---

## 12. Open questions (non-blocking; surface for owner attention)

### D-CI.5 — Sentinel update target

Does the new hook update **A1's sentinel** (`<workspace>/workspace/.pos/session-state/<session_id>.json`, append to `corpus_paths_loaded`), or does it write its own sentinel?

**Recommendation: update A1's sentinel.** The field is reserved for it; the file is the single source of truth; future gates have one place to consult. Builder plan handles the contract — A1's `write_corpus_load_sentinel` accepts the loaded list optionally; if today's signature doesn't, a minor A1 surface extension (additive, non-breaking) lands alongside the new hook. **If A1's surface cannot extend without a contract change → halt-trigger 2 of A1's contract**, and an A1.1 corrective lands first.

### D-CI.6 — Hook ordering vs. persona emitter

Order in the SessionStart fan-out:

- **(a)** A1 → corpus-inline → persona — persona's dossier reflects the inlined state.
- **(b)** A1 → persona → corpus-inline — persona dossier as today; corpus content emitted last.

**Recommendation: (a)** so the persona's dossier can grow a `corpus_inlined: true|partial` marker in a later micro-amendment without a re-ordering. Today the marker is absent; (a) preserves the option.

### D-CI.7 — Per-file size ceiling for truncate-on-overflow

**Recommendation: 50 k chars per file.** Largest current always-load file is 11 k (FUTURE_IDEAS at 83 k is on-demand only). Ceiling at 50 k buys headroom and surfaces the truncate path if a corpus file ever grows that large. Builder picks the literal value; recommendation is not load-bearing.

### D-CI.8 — Mode-partition refinement (NORMAL USE behaviour)

DEV MODE only is the recommendation; NORMAL USE no-ops. If the user later wants NORMAL USE workspaces to inline a CLAUDE.md-only payload (mirroring the persona's NORMAL USE dossier), that's a follow-on amendment, not this hook's scope. Surfaced for the record.

---

## 13. Risks

- **R-CI.1 — Token-cost creep.** Always-load tier expansion across amendments balloons session-start cost. Mitigation: every always-load addition gates through a new amendment (no implicit-add); the lean default makes the cost visible.
- **R-CI.2 — Corpus drift outpaces inlining.** A new corpus file is added (e.g. a new always-load doc) without the manifest update. Hook silently misses it; persona doesn't notice; failure class re-introduces. Mitigation: existing AC.F1/F3 manifest-coverage tests already enforce manifest consistency for always-load globs; the new hook reads the manifest, not a hardcoded list, so manifest expansion is the only update needed.
- **R-CI.3 — Inlined content masks dossier missingness signal.** Today persona's dossier says `[MISSING] docs/foo.md`; if the new hook also emits content from the file when present, a future contributor might assume content presence implies file presence. Mitigation: new hook's output explicitly marks `[missing]` slots and updates A1's sentinel `state`; downstream consumers read the sentinel, not the inlined text shape.
- **R-CI.4 — A1 sentinel surface gap.** If A1's `write_corpus_load_sentinel` doesn't accept a `corpus_paths_loaded` argument cleanly, the new hook either (i) writes a separate sentinel (D-CI.5 option), or (ii) surfaces an A1 substrate gap (halt-trigger). Mitigation: builder plan resolves before code lands.
- **R-CI.5 — Persona session-start emitter coupling.** The persona dossier today reads the sentinel and emits `[present]` markers; if the new hook's ordering moves the dossier to AFTER content emission, the dossier could be outdated relative to content state. Mitigation: D-CI.6 surfaces the ordering; the recommended (a) ordering matches the contract direction.

---

## 14. Halt signals encountered during research

None of the dispatch's six halt-and-surface triggers fired in a way that blocks the plan from authoring:

1. **Pre-flight surfaces hook already shipped:** ✗ — only the FIDRAFT-capture commit; substrate is sentinel-only as documented.
2. **A1 substrate gap:** ✗ — A1's `corpus_paths_loaded` field is reserved for exactly this composition; the contract anticipates it. (Open Q-CI.5 — if the surface can't extend additively, it becomes a halt during build; surfaced for the plan.)
3. **ODD violations:** ✗ — no method-in-acceptance or other §8.1 violations surfaced.
4. **Token-budget infeasibility:** ✓ **partial** — strategy (a) full-inline is infeasible. The dispatch named this halt-trigger explicitly with the framing *"surface the tier-based partition is REQUIRED, not optional."* Surfaced — strategy (b) is required, not optional. Plan reflects this as a constraint, not a decision.
5. **Architecture creep:** ✗ — "always-load" is well-defined by the existing `dev-mode-manifest.yaml` `always_loaded` field and A1's `compute_corpus_paths_required`. No deeper architectural question surfaced. (D-CI.1 names a possible refinement of the always-load partition; that's a tighten-the-existing-surface decision, not a new architecture.)
6. **Fence ambiguity:** ✗ — fence is `hands-off-lifecycle/{hooks,tests,seals}/` only (single sealed component). A1 admitted this fence at A1 plan-doc time.

---

## 15. Cross-references

- A1 plan: `docs/plans/structural-enforcement-a1-substrate.md` (§4 AC.SE.4 / AC.SE.5; §6 D-A1.1 / D-A1.4).
- A1 substrate: `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` + `corpus_load_session_start.py`.
- #45 registry: `framework/hands-off-lifecycle/hooks/first_run_settings.py::merge_session_start` + `_compose_inner_hooks`.
- #46 persona emitter: `framework/primary-persona/src/session_start_emitter.py` + `session_start_gate.py::compose_session_fields`.
- #67 reader fall-through: `framework/primary-persona/src/session_start_gate.py::_resolve_corpus_path` (private helper).
- Manifest source: `docs/rebuild/dev-mode-manifest.yaml` (always_loaded / dev_only partition).
- Failure-class motivation: `docs/FUTURE_IDEAS_DRAFT.md` entry "SessionStart corpus_gate should inline corpus content" (captured 2026-04-28).
- ODD §5.1.1 relocate-vs-eliminate: `docs/odd-methodology.md` lines 408–434.

---

*End of research artefact. Plan-doc at `docs/plans/corpus-inlining-session-start-hook.md`.*
