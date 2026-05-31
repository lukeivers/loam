# Publish assessment — 2026-05-29

**Task:** #18 — assess loam publish state, propose publish scope.
**Method:** all "published/sealed" claims Tier-0 from git refs (tags, merge-base,
`git ls-remote`), NOT from STATE.md prose, per `feedback_published_state_only_from_git_refs`.
**Tree:** `/Users/lukeivers/loam` (canonical). **HEAD:** `f23deda` (2026-05-29 17:09).
**Mode:** read-only assessment. No edits/commits/tags/pushes performed.

---

## 1. Last published version (Tier-0, git refs)

**`v0.13.0` — SHIPPED PUBLIC 2026-05-24.**

| Fact | Value | Verified by |
|---|---|---|
| Latest release tag | `v0.13.0` | `git tag --list 'v*' --sort=-v:refname \| head` |
| Annotated tag object | `787ff75` | `git rev-list -n1 v0.13.0` |
| Tag dereferences to seal commit | `d2176cf` | `git rev-parse v0.13.0^{}` |
| Tag is ON origin remote | yes — `787ff75 refs/tags/v0.13.0` | `git ls-remote --tags origin` |
| `origin/main` HEAD | `c88bd0b` (= v0.13.0 P3 backfill, one commit past the seal) | `git ls-remote origin main` |
| `docs/ACTIVE_MINOR` | `0.13.0` | file read |

**What "published" means here (confirmed from `docs/release-process.md` + `docs/release-versioning-policy.md`):**
publish = annotated git tag at the seal commit + `git push origin main` + `git push origin <tag>`
(+ optional `gh release`). The mechanism is the `loam release <version>` CLI verb, which runs
**seven structural pre-publish gates** first. There is no separate registry; the GitHub remote
tag graph IS the published-state source of truth. Publish is an **ASK-FIRST public action** —
owner authorization required; the CLI never auto-publishes (`docs/release-process.md` §2, §5).

---

## 2. Unpublished sealed work since v0.13.0

`git rev-list --count v0.13.0..HEAD` = **31 commits** (HEAD is 30 ahead of `origin/main`).
Two coherent sealed work-streams + one already-public predecessor's tail. Sealed amendments
(`chore(seals)` anchors) in the range:

| Amendment | Work-stream | Component fence | One-line what | Seal SHA |
|---|---|---|---|---|
| #149 (KP0) | keep-pace MVP | hands-off-lifecycle | Hook chain wired, fail-open-whole-chain proven, per-turn latency budget | `ccfdc22` |
| #150 (KP5+KP1) | keep-pace MVP | primary-persona | `OBJECTIVES.md` register + work-anchored (BM25/FTS5) per-prompt retrieval | `aadf2b7` |
| #151 (KP9) | keep-pace MVP | hands-off-lifecycle | Abstraction-voice jargon lint + draft-vs-active-constraint draft-to-send gate | `6b37490` |
| #152 (KP7) | keep-pace MVP | orchestrator | SessionStart objective + last-state surface (plain-language "last X / next Y") | `07d3b59` |
| (wiring) | keep-pace MVP | hands-off-lifecycle | In-tree contributor wiring (activation prep) | `58b6255` |
| #154 (FBM Cycle 1) | FBM activation | primary-persona | Fix doubled-nesting write-path (D1) + unify FBM/KP1 retrieval surface (D2); D3 live-activation owner-gated/out-of-seal | `4b25821` / `8e9b496` |

Plus `c88bd0b` (the v0.13.0 P3 backfill, already the content of `origin/main`) and several
`docs(plans)` / `fix` bookkeeping commits in the same lineage.

**Headline:** the **keep-pace-with-user MVP** (4-cycle arc #149–#152 + wiring) and **FBM Cycle 1**
(#154 — write-path fix + retrieval unify). Both are **SEALED LOCAL but UNWIRED by construction** —
the live `~/.claude/settings.json` activation is owner-gated and deliberately out of the seal diffs
(keep-pace §3 entry + #154 D3). So nothing in this range turns itself on for an end user on install.

---

## 3. Recommended publish scope + version bump

**Recommended version: `v0.14.0` (MINOR).** Derived at release time per
`feedback_version_numbers_at_release_time` + versioning-policy §"Number derivation":
`current_published = v0.13.0`, dominant `work_class = MINOR` → `next_MINOR(v0.13.0) = v0.14.0`.
**Not pre-assigned — this is the build-commence derivation, recorded here, not baked into any slug.**

**Why MINOR (new outcome shape):** the keep-pace MVP names ONE new user-achievable outcome —
the persona surfaces relevant on-file context (active objective / subgoal / last-turn topic) while
actively working a related topic, instead of forgetting it; plus a draft-to-send gate that suppresses
leaking surfaces. That is a new outcome shape (versioning-policy §"What goes in a minor"), not a defect
closure. FBM Cycle 1 rides in the same MINOR: its write-path fix (D1) is a defect closure, but D2
(unified retrieval surface) is an additive capability serving the same "persona remembers across the
session" objective. Single objective sentence both halves ladder to:

> v0.14.0 — Loam's persona surfaces on-file context relevant to what the user is actively working on,
> instead of forgetting it mid-session.

**Class tag: END-USER** (or MIXED) — the user-visible delta is nameable per versioning-policy
§"Quality gate," so the END-USER value-delta gate is satisfiable at plan time.

**What rides in v0.14.0:** keep-pace MVP (#149–#152 + wiring) and FBM Cycle 1 (#154). These are the
two coherent sealed streams since v0.13.0 and they share one objective. No unrelated work to split out.

---

## 4. Pre-publish HARD smoke plan (required — gate is currently unmet)

Per `feedback_hard_smoke_per_minor_before_publish`, **every MINOR needs a HARD smoke before publish.**
v0.14.0 is a MINOR, so it is required. **Tier-0 finding: no HARD-smoke writeup exists for this scope.**
`docs/experiments/` has no keep-pace / FBM-Cycle-1 smoke writeup; the only `fbm` smokes there are from
2026-05-18 (a different, pre-v0.13.0 "fbm" — session-clear-safety). **Release gate 1 (`hard-smoke`:
writeup exists + contains literal `GREEN`) cannot pass today.**

Smoke steps (model on the v0.13.0 writeup `docs/experiments/release-integration-v0-13-0-hard-smoke.md`):

1. **Cold clone / fresh workspace** — scaffold a fresh workspace from the release candidate; confirm
   first-run completes without the keep-pace/FBM hooks breaking the SessionStart chain (fail-open).
2. **Real `claude -p`** — subscription-only invariant (`feedback_no_anthropic_api_key`); spawn isolated
   per `feedback_spawned_claude_must_isolate_telegram_plugin` (`--strict-mcp-config`).
3. **Real fixture exercise** — drive the keep-pace retrieval chain end-to-end: seed an OBJECTIVES.md
   objective → vague "continue" prompt → confirm the work-anchored surface returns the right pointer
   (the cold-walk outcome-altitude AC.KP1.6 / AC.FBM1.S production chain, no pre-seeded episodes).
4. **Regression ride-alongs** — F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN, per every prior loam minor smoke.
5. **Gate-7 evidence** — `which loam` resolves + `loam --help` lists all subcommands (operator-verified
   per release-process gate 7).
6. **Write the GREEN verdict** to `docs/experiments/<v0-14-0-slug>-hard-smoke.md` with the literal
   `GREEN` token (gate 1 reads it).

---

## 5. Blockers / must-fix-first

### B1 — Stale first-run messaging: "pos-v2" + retired graphiti/neo4j/kuzu (USER-VISIBLE) — MUST FIX
`framework/hands-off-lifecycle/hooks/first_run_dispatch.py` shows fresh users, on first run:
- 8+ references to **"pos-v2"** (the old project name; the product is "loam" now) — lines 98, 121, 134,
  147, 161, 418, 441, 443, 459 (+ `agent_file_runner.py:57`).
- A message claiming the install **"pulls graphiti-core, neo4j, and kuzu"** (line 98–110). But
  `framework/first-run-inventory.yaml` (lines 60–66) confirms the **graphiti/neo4j/kuzu memory-system
  was RETIRED at v0.1.0** (AC.MFBM.7); file-based memory is the default substrate. So the message tells
  a fresh user it is installing heavy deps that no longer install.

This is the **task #19 graphiti residue** and it IS user-visible on first-run — it would ship in a publish.
Most other graphiti hits in the tree are intentional (tests asserting the label is *retired*, archive/seal
records) and are NOT blockers; this first-run message is the live, shipping one. Fix = a small string sweep
in the first-run hooks (own cycle/PATCH or fold into the v0.14.0 plan as a named sub-fix). **Surfaced per
Lens 7 — out of this read-only scope; owner-gated whether to fix-then-publish or publish-then-fix.**

### B2 — Clean-tree gate (gate 4) is RED — owner WIP in the canonical tree
`git status --porcelain` is non-empty: 5 modified (incl. `docs/CLAUDE_CAPABILITIES.md`,
`docs/FUTURE_IDEAS_DRAFT.md`, `framework/scope-of-work/*`) + untracked design drafts (this file's siblings:
`keep-pace-*`, `fbm-state-and-memory-roadmap-*`). These are owner WIP, not part of the v0.14.0 scope.
**Resolution (precedent): worktree-isolated release build** — v0.13.0 was published from
`/Users/lukeivers/loam-release-v0-13-0` exactly so owner WIP in the canonical tree stayed untouched
(roadmap §3 v0.13.0 entry). Same shape applies here. Without isolation, gate 4 blocks the CLI.

### B3 — Doubled-nesting write-path: FIXED in code, not a blocker
#154 D1 corrects the resolver so episode writes land at the single-`workspace` live queue (was landing in
a doubled `workspace/workspace` shadow dir, stranding ~17 JSONs). No doubled `workspace/workspace` dir or
stranded JSONs found on disk now. The operator stranded-JSON migration is D3 (owner-gated/runtime),
correctly out of the seal. Not a publish blocker; noted because the dispatch named it.

### B4 — Live activation is owner-gated, NOT a ship surprise — informational
Both work-streams are sealed-local-but-UNWIRED by construction. Publishing v0.14.0 ships the *capability*
(code + hooks-as-contributors + tests), but the live `~/.claude/settings.json` wiring + OBJECTIVES.md seed
remain owner-gated runtime steps. So a fresh end-user install does not auto-activate keep-pace/FBM — fail-open
is guaranteed pre-wiring. This is consistent with v0.13.0's "installed-by-default" framing only for the
always-on pieces; keep-pace's live wiring stays operator-gated. Worth stating in the release notes so the
"new outcome" claim is honest: the capability ships; one owner step turns it live.

### B5 — Un-promoted hooks — none found blocking
No evidence of un-promoted hooks gating this publish. The keep-pace hook contributors are wired in-tree
(amendment #149 + the wiring seal `58b6255`); the structural-enforcement promotions tracked elsewhere are
not in this scope. Not a blocker.

---

## RECOMMENDATION: NOT-YET (gateable, not far)

Do **not** publish today. v0.14.0 is the right scope + bump, but two hard gates are unmet and one
user-visible blocker would ship as-is:

**Gates to clear before a GO:**
1. **HARD smoke** (§4) — no GREEN writeup exists for this scope; gate 1 fails. **Primary blocker.**
2. **Clean tree** (B2) — gate 4 fails on owner WIP; clear via a **worktree-isolated release build**
   (v0.13.0 precedent), not by committing/stashing owner drafts.
3. **B1 first-run "pos-v2" + graphiti message** (task #19) — owner ruling: fix-then-publish (fold the
   string sweep into v0.14.0) vs publish-then-fix as a follow-on PATCH. It is user-visible on first run,
   so the default recommendation is **fix-first**.

**Owner decisions to surface (one at a time, criticality order):**
1. Authorize v0.14.0 scope + MINOR bump (keep-pace MVP + FBM Cycle 1, objective sentence above)?
2. Fold the B1 first-run string sweep into v0.14.0, or ship it as a separate PATCH after?
3. Confirm worktree-isolated build (B2) for the publish.

Once HARD smoke is GREEN + tree is clean (via worktree) + B1 ruling is made, this flips to GO and the
publish is the standard `loam release v0.14.0 --dry-run` → owner-authorize → `loam release v0.14.0`.
The actual publish is a PUBLIC action — owner authorization required; this assessment performs none of it.
