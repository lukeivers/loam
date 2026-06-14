# Claude-leverage program — Slice 4: KNOWLEDGE CORPUS, PUSHED (thin-parent sub-plan-doc)

> **Status:** sub-plan-doc, THIN PARENT (this slice decomposes into three
> sub-cycles S4a/S4b/S4c per master §10 F2.5 + Lens 5; each sub-cycle carries
> its own tighter AC family + its own manifest. This parent settles the
> program-level decisions D-PUSH.\*, the local-buildable vs ⛔OWNER-gated
> split, and the AC ladder; the sub-cycles are buildable off their own
> sub-plans.)
> **WD:** `/Users/lukeivers/loam` (canonical loam).
> **Parent plan:** `docs/plans/claude-leverage-program.md` (master; Slice 4
> section + §2 "Weekly knowledge pack" + "Distribution channel" rows +
> AC.CLP-PUSH.\* family + D-CLP.4 register are the source of truth).
> **Predecessors (load-bearing):**
> - **D-CLP.4 owner-RATIFIED** 2026-06-11 (Discord 1514753768175042771,
>   "I'm good with the plugin marketplace auto update thing"): distribution =
>   plugin-marketplace auto-update. Carried into this slice unchanged.
> - **Slice 1 sealed** (`c41f9473`, 2026-06-11): the capability-refresh
>   currency engine (`framework/tools/capability-refresh/`) keeps
>   `docs/capability-corpus/` current. The weekly pack is a RENDERING FROM
>   the corpus, never a fork (master §2 placement). Slice 1's source manifest
>   + `.refresh/last-run.json` + `pending-deltas/` are the freshness signal
>   the pack rendering consumes.
> - **Slice 2 sealed** (`f308b398`, 2026-06-12): graduated the three doctrine
>   skills into `plugins/loam-skills/`. The pack is the same SKILL.md form —
>   the marketplace plugin is a skills-pack, Lens 1.
> - Corpus contract: `docs/capability-corpus/AUTHORING.md` (Class A/A-prime
>   deterministic projection; Class B synthesis; no-cross-class-write).
> - `framework/workspace-bootstrap/` — the in-fence surface that wires a user
>   to the marketplace (the buildable half of distribution).
> - **Live marketplace mechanism re-verification (2026-06-14, plan-author,
>   WebFetch `code.claude.com/docs/en/discover-plugins` +
>   `/plugin-marketplaces` + the changelog raw):** see §3.1 — the mechanism is
>   confirmed and the D-CLP.4 assumption is SHARPENED (not contradicted).
> **BASELINE candidate:** `c77a2447` (HEAD of main at parent-authoring; each
> sub-cycle's manifest walks its own baseline at apply time — the sub-cycles
> are dependency-ordered S4a → S4b → S4c, so S4b baselines on S4a's seal and
> S4c on S4b's).
> **Status-file target:** `docs/STATE.md` change-log + `docs/release-roadmap.md`
> §8 register rows (one per sub-cycle) + master plan §2/§10 backfill.
> **Quality bar:** every AC outcome-shaped; ★ outcome-altitude AC per the
> consuming sub-cycle; method stays the builder's call per ODD §1.1; NO
> version numbers pre-assigned (`feedback_version_numbers_at_release_time`).
>
> **⛔ PUBLIC-ACTION BOUNDARY (the load-bearing constraint of this slice).**
> Slice 4 contains the program's ONLY off-machine steps. They are isolated
> into S4c and are EVERY ONE an ⛔OWNER gate — the persona/builder NEVER
> creates a public repo, NEVER pushes off-machine, NEVER first-publishes.
> S4a + S4b are entirely LOCAL and buildable with no public surface in
> existence: the pack renders into the repo tree, and the wiring + the ★
> outcome-altitude AC are verified against a LOCAL/simulated marketplace
> (a `file://`-path or local-clone marketplace `/plugin marketplace add`s
> from a local path — confirmed valid in §3.1). The real-publish leg is the
> ⛔OWNER observation in S4c. ASK-FIRST-on-public is the governing principle;
> the egress-consent floor + AC.CLP-PUSH.5 is its test.

---

## §1 Summary / TL;DR

**What this slice ships (the payoff leg — closest to loam's prime objective,
master §4):** a continuously-curated body of best-current LLM/Claude/Claude-Code
leverage knowledge, rendered from `docs/capability-corpus/` into a
distributable skills-pack, delivered TO loam users ~weekly with ZERO user
action after one-time setup. The owner's framing — users "do better at
leveraging AI without having to learn how to do it themselves" — IS
AC.PO.1 restated; the knowledge pack is translation-at-scale (loam learns the
*how*, the user never has to). §4 ladders this explicitly.

**Decomposition (Lens 5 — three sub-cycles, each tighter than this parent):**

1. **S4a — RENDER** (`AC.CLP-PUSH-RENDER.*`; LOCAL, in-fence). A deterministic
   pipeline projects the corpus (Class A currency + Class B synthesis) into a
   marketplace-shaped skills-pack tree IN-REPO, every externally-sourced claim
   carrying its corpus citation, behind a curation gate that nothing crosses
   without a recorded pass. Delivers AC.CLP-PUSH.1. **The bulk of the
   buildable work.** HIGH-MEDIUM confidence.
2. **S4b — WIRE** (`AC.CLP-PUSH-WIRE.*`; LOCAL, in-fence). `workspace-bootstrap`
   gains the bootstrap-wiring contract: it writes the `extraKnownMarketplaces`
   stanza (with `autoUpdate: true`) into a bootstrapped workspace's
   `.claude/settings.json`, AND the persona surfaces newly-arrived knowledge
   per the Lens 0 vocabulary rule. Delivers AC.CLP-PUSH.3 ★ + .4, verified
   against a LOCAL/simulated marketplace. MEDIUM confidence (the ★ AC's
   real-publish leg is observed in S4c).
3. **S4c — PUBLISH** (`AC.CLP-PUSH-PUBLISH.*`; ⛔OWNER, NO builder code). An
   ordered owner-runbook: create the public marketplace repo → first-publish
   the rendered pack → observe real arrival on a second workspace. Delivers
   AC.CLP-PUSH.2 ⛔OWNER + .5, and closes the ★ AC.CLP-PUSH.3 real-publish
   observation. The build that executes S4a/S4b stays entirely LOCAL until the
   owner opens each gate here.

**Sub-cycle order:** S4a → S4b → S4c. Rationale: the pack must exist (S4a)
before the wiring can point at it (S4b); both must be local-verified before
the owner is asked to publish (S4c). S4c's owner gates are the LAST step and
gate nothing buildable — a NO at any S4c gate strands no in-fence work.

**Named decisions (full register §10; recommendation IS the decision unless
dispatcher/owner overrides):**
- **D-PUSH.1 — pack rendering mechanism** → **deterministic projection from
  the corpus** (no LLM authorship in the pack body; the same protection-floor
  shape as Slice 1's refresh). New tools-adjacent component
  `framework/tools/knowledge-pack/` (S4a).
- **D-PUSH.2 — bootstrap-wiring contract** → **an `extraKnownMarketplaces`
  stanza with `autoUpdate: true` written by `workspace-bootstrap` into the
  workspace's `.claude/settings.json`** (the §3.1 live finding makes this the
  zero-user-action mechanism). S4b.
- **D-PUSH.3 — owner-gate sequence** → the exact ordered ⛔OWNER list (§6 +
  S4c): (1) create public repo → (2) seed marketplace.json + first pack →
  (3) first publish (push) → (4) observe arrival. S4c.
- **D-PUSH.4 — weekly cadence binding** → **REUSE Slice 1's cadence
  machinery** (the refresh routine already runs ~weekly; the pack render is an
  added step in the same cadence, not a second scheduler). S4a.
- **D-PUSH.5 — pack staleness/versioning** → **the pack carries a generated-ts
  + a content-hash + per-entry corpus `source_fetch_ts` passthrough; pack
  version derives at publish time from (date, content-hash), never
  pre-assigned.** S4a.

**F2 on scope realism (master band 120–300 min build + owner-gate latency):**
S4a is the real build (a rendering pipeline + curation gate + tests). S4b is a
focused bootstrap extension (one stanza-writer + a persona-surfacing rule +
tests). S4c is NO build — it is an owner-runbook + the observation AC. The
honest caveat the live verification surfaced: "zero user action after setup"
is true for content *arrival*, but Claude Code prompts `/reload-plugins` after
an auto-update lands new components (§3.1 finding 4) — a one-keystroke
in-session activation, not a setup ritual. Named in §10 F2.2, not papered over.

**AI-time bands (estimate-grade, per duration rubric):** S4a 60–150 min;
S4b 30–75 min; S4c 0 build min + owner-gate latency (owner-availability-bound,
separate line item).

---

## §2 Placement decisions (final placement at each sub-cycle's sub-plan)

| Surface | Placement (recommended) | Rationale |
|---|---|---|
| Pack rendering pipeline (S4a) | **NEW tools-adjacent component `framework/tools/knowledge-pack/`** (`new_component: true`, first-seal) | Same weight class + precedent as Slice 1's `capability-refresh` (master §2 "the pack is a rendering" — a fetch-from-corpus → project → emit contract). It WRITES a distributable artefact, so it gets a real fence + seal test. Final new-vs-tools call is S4a's first decision (mirrors D-CUR.1). |
| Rendered pack tree (the marketplace source) (S4a) | **In-repo at `docs/capability-corpus/.pack/` (machine-generated, gitignored-or-tracked — builder's call) OR a dedicated `dist/knowledge-pack/` staging path** | The pack is GENERATED from the corpus (single source of truth, master §2). It is staged IN the canonical repo by S4a; it is NOT yet a public marketplace (that is S4c, ⛔OWNER). The public marketplace repo is a SEPARATE repo the owner creates — never a subtree pushed from here without an owner gate. |
| Curation gate (S4a) | **Inside the new component** — a gate record artefact (pass/fail + reviewer + ts) the pipeline emits and the publish path checks | AC.CLP-PUSH.1 + .5: nothing leaves the machine without a recorded gate pass. The gate is local; the publish that consults it is ⛔OWNER (S4c). |
| Bootstrap-wiring contract (S4b) | **EXTEND `framework/workspace-bootstrap/`** — a stanza-writer that adds `extraKnownMarketplaces` + `autoUpdate:true` to the bootstrapped workspace's `.claude/settings.json` | Master §2 "Distribution channel" row: bootstrap extension is INSIDE the existing `workspace-bootstrap` fence (the buildable half). The §3.1 live finding pins the exact stanza. |
| Persona knowledge-surfacing (S4b) | **EXTEND `framework/primary-persona/`** OR a corpus-routed surfacing rule — builder's call at S4b sub-plan | AC.CLP-PUSH.4 (Lens 0 vocabulary rule). If it needs a persona-spine edit, S4b's fence carries `primary-persona`; if it routes through the existing corpus-lean hook, it may not — S4b decides, halts if a sealed-component edit isn't in its manifest (mirrors Slice 1 §3.3). |
| Public marketplace repo (S4c) | **NEW PUBLIC repo — ⛔OWNER creates** (per D-CLP.4). Outside ANY sealed fence; outside this repo entirely. | Master §2 "Distribution channel" row. The agent/persona CANNOT create public repos (ASK-FIRST-on-public). S4c is an owner-runbook, not a build. |
| First publish (S4c) | **⛔OWNER pushes** the rendered pack + marketplace.json to the public repo | Egress-consent floor; AC.CLP-PUSH.5. Per-publish owner gate initially (master §3.4); standing-approval is the owner's explicit future option, never assumed. |

## §2bis Primitive check (REQUIRED — this slice introduces new mechanisms)

Per the plan-docs convention (`plugins/dev-sdlc/docs/conventions/plan-docs.md`
§1, the plan-time leg of the prefer-the-primitive doctrine this very program
installs — Slice 2 D-CLP.1) — and consulting `claude-feature-awareness` +
`tool-selection-rubric`:

| New mechanism (sub-cycle) | Native primitive considered + chosen | Rationale |
|---|---|---|
| Distribution channel (S4c) | **`/plugin marketplace` auto-update (native)** — chosen | Lens 1; the program's own distribution choosing the native primitive is the doctrine eating its own cooking (master D-CLP.4). The §3.1 live verification CONFIRMS user-level auto-update for a third-party marketplace exists. NOT bespoke — alternative (d), a per-workspace fetch routine, is "a bespoke pull loop wearing a push costume" (master D-CLP.4) and is the named fallback only if the native channel fails. |
| Weekly cadence for the pack render (S4a) | **REUSE Slice 1's scheduled cloud routine / launchd binding (native `/schedule`, already chosen + sealed)** — chosen | `primitive-rationale: reuse-existing scheduled binding — the refresh routine already runs the cadence; adding the pack-render step to it avoids a second scheduler (Lens 1, D-PUSH.4).` Authoring a NEW scheduler would be the rubric's named anti-pattern (duplicate primitive). |
| Pack-arrival activation (S4b consumer side) | **`/reload-plugins` (native)** — the platform's own post-auto-update activation | Not a loam mechanism; named so the F2.2 "one keystroke" caveat traces to the real primitive, not a loam gap. |
| Pack rendering transform (S4a) | **bespoke — deterministic structural projection** | `bespoke — <reason>`: a corpus→pack rendering is a structural transform with no native equivalent (the same shape as Slice 1's projection, which is also a deterministic in-house transform). No LLM authorship in the pack body (protection-floor — a hallucinated leverage claim cannot enter by construction). This is the ONE deliberately-bespoke element; it is bespoke because no catalogued primitive renders a domain corpus into a skills-pack. |

## §3 Halt-and-surface BEFORE build (recorded at parent-authoring)

### §3.1 Live marketplace-mechanism re-verification (information-trust; master §8.3 + halt-trigger-3) — the load-bearing finding

Master §11 carried a v2.1.140-vs-.142 discrepancy and flagged the user-level
semantics as "to verify live." I re-verified live at parent-authoring
(2026-06-14, WebFetch `code.claude.com/docs/en/discover-plugins`,
`/en/plugin-marketplaces`, and the changelog raw — latest **2.1.176**). Findings:

1. **User-level auto-update for a third-party marketplace EXISTS and is NOT
   enterprise-only.** A non-enterprise individual user toggles it via `/plugin`
   → **Marketplaces** → select marketplace → **Enable auto-update**. When ON,
   "Claude Code refreshes the marketplace data and updates installed plugins to
   their latest versions" at startup (verbatim, discover-plugins
   §"Configure auto-updates"). The `extraKnownMarketplaces` + `"autoUpdate":
   true` managed setting is the ORG-WIDE convenience layer, NOT the only path.
2. **DEFAULT for third-party marketplaces is auto-update DISABLED** (verbatim:
   "Third-party and local development marketplaces have auto-update disabled by
   default"). → zero-user-action-after-setup REQUIRES one of: (a) the user
   toggles auto-update ON once during setup, OR (b) an `extraKnownMarketplaces`
   stanza carrying `"autoUpdate": true` in the workspace's
   `.claude/settings.json` — which `workspace-bootstrap` CAN write (D-PUSH.2,
   the in-fence wiring). This is the exact mechanism that makes AC.CLP-PUSH.3 ★
   genuinely satisfiable.
3. **A LOCAL marketplace is a first-class add target** — "`/plugin marketplace
   add ./my-marketplace`" + "Local paths: directories or direct paths to
   `marketplace.json` files" (verbatim). → the ★ outcome-altitude AC is
   satisfiable in the LOCAL/pre-public build against a local-path marketplace,
   exactly as the dispatch constraint requires.
4. **Post-auto-update, Claude Code prompts `/reload-plugins`** (verbatim: "If
   any plugins were updated, you'll see a notification prompting you to run
   `/reload-plugins`"). → "zero user action" is true for content *arrival* +
   *delivery to the workspace*; activating the newly-arrived components into
   the live session is a one-keystroke prompt. Named honestly in §10 F2.2; it
   does NOT defeat AC.CLP-PUSH.3 (arrival with no setup ritual is the test).
5. **Marketplace = a git repo with `.claude-plugin/marketplace.json` at root +
   `plugins/<name>/` (each with `.claude-plugin/plugin.json` +
   `skills/*/SKILL.md`); a skills-only pack is valid** (verbatim walkthrough).
   Updating = push to the repo. → the pack form is settled; S4a renders exactly
   this tree.

**Ruling (Lens 6 / information-trust):** the live mechanism CONFIRMS D-CLP.4 —
marketplace auto-update is real, native, user-level, and decoupled from loam's
release cadence. The change vs the master's assumption is a SHARPENING (the
default-off → setup-toggle-or-stanza detail), NOT a material contradiction of
the ratified mechanism. Per the dispatch halt rule ("a CHANGED mechanism is a
re-ratification trigger"), this is NOT a changed mechanism — it is the same
mechanism with its setup step pinned. **Therefore: proceed on D-CLP.4; do NOT
trip the re-ratification halt.** The sharpening is recorded here + surfaced in
the owner-facing summary so the owner sees the one-time-setup detail before S4c.
The master's v2.1.140/.142 discrepancy is re-pinned: the user-level toggle is
documented current (≤2.1.176); `extraKnownMarketplaces autoUpdate` managed
behavior landed by 2.1.160; the .142 line was the persistence FIX. Slice 4
rests on today's fetch, not training data or either inherited number.

### §3.2 Other recorded surfaces

1. **All five AC.CLP-PUSH.\* passed the method-in-AC test** at master level
   (master §5); each sub-cycle's family below is strictly tighter (Lens 5) and
   re-passes the test in §5.
2. **Public-action isolation verified clean.** Every off-machine step factors
   into S4c; S4a + S4b have NO public surface and NO step that requires the
   public repo to exist. The ★ AC is satisfied LOCALLY in S4b and re-observed
   for-real in S4c. This is the dispatch's central structural requirement and
   it splits cleanly — no step resists the local/owner-gated partition (the
   named halt for "cannot be cleanly split" does NOT fire).
3. **No Slice-1/2 contradiction.** S4a consumes the sealed corpus + refresh as
   a read-only content source (`docs/capability-corpus/` + the refresh's
   `.refresh/last-run.json` freshness signal); it does not edit Slice-1/2
   fences. A corpus-content question found at build surfaces as a Slice-1
   pending-delta, never a silent edit (mirrors Slice 2 §8.1).
4. **`/reload-plugins` caveat surfaced** (§3.1.4) — recorded in the
   owner-facing summary so the "zero user action" claim is honest before S4c.

## §4 Spec-objective placement — how Slice 4 ladders to the prime objective

- **Binds:** master **AC.CLP.1 ★** (a wrong/missing capability fact gets
  corrected by loam's own machinery within one cadence) is delivered for the
  DISTRIBUTION dimension here — Slice 1 made the corpus current; Slice 4 makes
  that currency REACH users. AC.CLP-PUSH.\* is the tighter family (Lens 5).
- **Ladders to AC.PO.1 (primary-persona test) — DIRECTLY; this is the leg
  master §4 names "closest to loam's prime objective."** AC.PO.1 asks: *does
  this reduce the translation burden between the user's natural-language intent
  and AI-effective execution?* (`docs/VALUE_PROPOSITION.md:117`). The knowledge
  pack is translation-at-scale: loam continuously learns the *how* (best-current
  leverage knowledge) and pushes it to every user's persona, so NO user has to
  learn how to leverage AI themselves — the owner's exact framing (Discord
  1514741531687256226). AC.CLP-PUSH.4 (persona surfaces it per the Lens 0
  substance/vocabulary rule) is the AC.PO.1 instance made checkable: substance
  exposed, wording tuned to the user, never a raw changelog dump.
- **Ladders to AC.PO.2 (harness test):** the pack channel + bootstrap wiring
  ADD to the persona's toolkit (the persona now reaches for current leverage
  knowledge the user never configured). The distribution choosing the native
  marketplace primitive (Lens 1) keeps the capability inside the harness's
  reach — not a user-orchestrated action (AC.PO.2's failure mode avoided).
- **Lens 0 protection floor:** the curation gate + deterministic render + the
  ⛔OWNER publish gates guard the betrayal classes — inventing things (no LLM
  authorship in the pack; every claim cites its corpus entry), and acting
  without consent (every off-machine step owner-gated).

## §5 Acceptance criteria (parent `AC.CLP-PUSH.*`, decomposed per sub-cycle)

★ = outcome-altitude (production entry-point, no pre-arranged state). Every AC
passes the method-in-AC test. The parent ACs below are the master's verbatim
outcomes; each sub-cycle's sub-plan carries a STRICTLY TIGHTER family
(`AC.CLP-PUSH-RENDER.*` / `-WIRE.*` / `-PUBLISH.*`) — named here, fully
specified in each sub-plan.

### Parent-level (master verbatim — the slice is green when all are met)

| AC | Outcome | Owning sub-cycle | Verification |
|---|---|---|---|
| AC.CLP-PUSH.1 | A curation pipeline produces a candidate weekly pack from the corpus (Class A currency + Class B synthesis), every externally-sourced claim carrying a real citation, with a curation gate before anything leaves the machine. | S4a | Run the pipeline; inspect a candidate pack + its gate record. |
| AC.CLP-PUSH.2 ⛔OWNER | The distribution channel exists publicly (per D-CLP.4) — created only on recorded owner approval. | S4c | Channel exists + the approval record predates it. |
| AC.CLP-PUSH.3 ★ | A loam workspace on another machine/user that performed no action beyond one-time setup has the updated knowledge available to its persona within one distribution cycle of an owner-approved publish. | S4b (LOCAL leg) + S4c (real-publish leg) | LOCAL: second workspace adds a local-path marketplace once, then a re-render+local-publish arrives with zero further action. REAL: S4c observation post owner-publish. |
| AC.CLP-PUSH.4 | The persona surfaces newly-arrived leverage knowledge per the Lens 0 vocabulary rule (substance exposed, wording tuned to the user), not a raw changelog dump. | S4b | Observe the persona's surfacing on a fixture user profile. |
| AC.CLP-PUSH.5 | Nothing publishes off-machine without a recorded owner approval (per-publish initially; standing approval only if the owner explicitly ratifies it). | S4a (gate) + S4c (publish path) | Audit the publish path for the gate; attempt an ungated publish in a test rig and observe refusal. |

### Sub-cycle AC families (tighter; fully specified in each sub-plan)

- **S4a — RENDER (`AC.CLP-PUSH-RENDER.*`):** RENDER.1 deterministic
  corpus→pack projection (no LLM body authorship); RENDER.2 every pack claim
  carries its corpus `[primitive:<class>:<name>]` / source citation; RENDER.3
  curation-gate record emitted, pack marked publish-eligible only on gate pass;
  RENDER.4 ★ a production-CLI render against the live corpus produces a
  well-formed marketplace tree (`.claude-plugin/marketplace.json` +
  `plugins/<name>/` skills) with no pre-arranged state; RENDER.5 pack carries
  generated-ts + content-hash + per-entry fetch-ts passthrough (D-PUSH.5);
  RENDER.6 the render reuses Slice-1's cadence binding (no second scheduler,
  D-PUSH.4); RENDER.S seal-diff.
- **S4b — WIRE (`AC.CLP-PUSH-WIRE.*`):** WIRE.1 bootstrap writes the
  `extraKnownMarketplaces` + `autoUpdate:true` stanza into a bootstrapped
  workspace's `.claude/settings.json` (idempotent); WIRE.2 ★ a second
  fixture workspace, after one-time setup only, receives a re-rendered pack via
  a LOCAL-path marketplace with zero further user action (the AC.CLP-PUSH.3
  local leg); WIRE.3 persona surfaces arrived knowledge per Lens 0
  (AC.CLP-PUSH.4); WIRE.4 setup is genuinely one-time (re-run is idempotent;
  no per-cycle user step beyond the platform's `/reload-plugins` prompt, named
  not owned); WIRE.S seal-diff.
- **S4c — PUBLISH (`AC.CLP-PUSH-PUBLISH.*`; ⛔OWNER, NO builder code):**
  PUBLISH.1 ⛔OWNER public repo created on a recorded approval that predates it
  (AC.CLP-PUSH.2); PUBLISH.2 ⛔OWNER first-publish pushes the gate-passed pack;
  PUBLISH.3 the real-publish observation of AC.CLP-PUSH.3 ★ (second real
  workspace receives it, zero user action post-setup); PUBLISH.4 the publish
  path refuses an ungated publish (AC.CLP-PUSH.5 adversarial leg — testable
  LOCALLY in a rig in S4a, re-affirmed here).

## §6 Build steps + the ⛔OWNER-gate sequence (method-level; builder's call per ODD §1.1)

Each sub-cycle: sub-plan-doc + manifest authored first (plan-before-code), then
`loam amend apply` → build → `loam amend seal` per the amendment-cycle
convention (named per `feedback_dispatch_explicit_loam_amend_apply`).

**LOCAL-buildable (the build executes these with NO public surface):**

1. **S4a — RENDER.** Scaffold `framework/tools/knowledge-pack/` (tests-first);
   read the corpus (Class A `claude-code/` + `harness/` + Class B
   `best-practice/`) + the refresh freshness signal; project into a
   marketplace tree (skills-pack form per §3.1.5); emit the curation-gate
   record; stamp generated-ts + content-hash. Wire the render as a step in
   Slice-1's existing cadence binding (D-PUSH.4 — no new scheduler). The
   ungated-publish-refusal rig (AC.CLP-PUSH.5 adversarial) is built + tested
   here, LOCALLY.
2. **S4b — WIRE.** Extend `workspace-bootstrap` with the stanza-writer
   (D-PUSH.2; the exact `extraKnownMarketplaces`/`autoUpdate` shape from
   §3.1.2). Add the persona knowledge-surfacing rule (Lens 0). Verify the ★
   AC.CLP-PUSH.3 LOCAL leg: a second fixture workspace + a `file://`/local-path
   marketplace + a re-render → arrival with zero further action.

**⛔OWNER-gated (NOT the builder — an owner-runbook in S4c; named, not executed):**

3. **S4c — PUBLISH — the exact ordered ⛔OWNER sequence (D-PUSH.3):**
   - **⛔OWNER gate 1 — CREATE PUBLIC REPO.** The owner creates the new PUBLIC
     marketplace repo (e.g. `github.com/lukeivers/loam-knowledge` — name
     owner's call). The persona/builder CANNOT do this (ASK-FIRST-on-public).
     Recorded-approval-predates-creation is AC.CLP-PUSH.2's test.
   - **⛔OWNER gate 2 — SEED.** The owner (or the persona, ON the owner's
     explicit go, into the owner-created repo) places `.claude-plugin/
     marketplace.json` + the S4a-rendered, gate-passed pack at the repo root.
   - **⛔OWNER gate 3 — FIRST PUBLISH.** The owner pushes. This is the first
     off-machine exposure; per-publish owner gate (master §3.4). AC.CLP-PUSH.5.
   - **⛔OWNER gate 4 — OBSERVE.** With the channel live, observe a second real
     workspace (auto-update ON via the S4b wiring or one-time toggle) receive
     the pack with zero user action — the AC.CLP-PUSH.3 ★ real-publish leg.
   - **(Owner's explicit future option, NOT assumed) — STANDING APPROVAL.** The
     owner MAY later ratify "auto-publish packs that pass the curation gate,"
     converting per-publish gating to gate-pass gating. Surfaced as an owner
     decision when S4c dispatches; never pre-decided (master §3.4).
4. **Seal + smoke + bookkeeping** per §9, per sub-cycle.

## §7 Out of scope

1. **β MCP knowledge-server + γ dynamic contributor** — master §7.1/7.2.
2. **Standing-approval auto-publish** — the owner's explicit future option, not
   built here; per-publish gating is the floor (master §3.4 + §10 F2.3).
3. **Class B community-survey background-agent machinery at full locked-δ
   scope** — master §7.5: Slice 4 curates best-current knowledge into the pack,
   but the weekly community-survey accrual ships only to the extent S4a finds
   it affordable; otherwise it's the named follow-on.
4. **Multi-pack / per-audience tailoring** — the first pack is one corpus-wide
   pack; per-user-profile pack tailoring (deeper Lens 0) is a follow-on once
   the channel is proven.
5. **The public repo's own CI/release automation** — the owner's repo; S4c
   ships a runbook, not the public repo's pipeline.
6. **pos3 prototype cleanup** — workspace chore, master §7.6.

## §8 Halt triggers (in-flight, per sub-cycle)

1. **Any step about to perform a public action** (repo creation, push,
   off-machine publish, feed exposure) **without a recorded owner approval →
   HARD STOP** (egress-consent floor; AC.CLP-PUSH.5 is the test). This is the
   governing trigger; S4a/S4b must never reach it (they are local by
   construction); S4c reaches each gate only WITH the owner.
2. The marketplace mechanism on any build-time re-verification differs
   MATERIALLY from §3.1's findings (e.g. user-level auto-update is removed, or
   a local-path marketplace stops being addable) → halt; the §3.1 sharpening
   becomes a changed mechanism → re-ratification trigger, owner rules (master
   halt-trigger 3; D-CLP.4 falls to its named fallback (d)).
3. A corpus-content discrepancy found during render → surface as a Slice-1
   pending-delta question, NEVER a silent corpus edit (§3.2.3).
4. Satisfying an AC requires editing a sealed component not in the sub-cycle's
   manifest (e.g. `primary-persona` for the S4b surfacing rule) → halt with the
   proposed fence widening, never silently widen (mirrors Slice-1 §8.5).
5. Any candidate mechanism turns out to require an Anthropic API key → halt,
   surface (constraint corpus is subscription-only via `claude -p`).
6. The S4a render cannot be made deterministic without an LLM authoring the
   pack body → halt; an LLM-authored pack body is a protection-floor breach
   (D-PUSH.1) — surface for a re-scope, don't ship a hallucination surface.

## §9 Bookkeeping

- `docs/STATE.md` change-log entry per sealed sub-cycle.
- `docs/release-roadmap.md` §8 register: Slice-4 program row + per-sub-cycle
  rows (S4c carries a ⛔OWNER-pending marker until each gate is observed).
- Master plan backfill (at sub-cycle seal): §2 "Weekly knowledge pack" +
  "Distribution channel" rows finalised; §10 D-CLP.4 marked
  delivered-by-Slice-4 with the §3.1 sharpening noted.
- FIDRAFT graduation of F-CLAUDE-LEVERAGE-PROGRAM remains dispatcher-owned —
  flagged, NOT edited by this plan's authoring.
- Each sub-cycle's manifest + §14 register per the plan-docs convention.

## §10 Named decisions + F2 Ruthless Feedback

### Named decisions (recommendation IS the decision unless dispatcher/owner overrides)

**D-PUSH.1 — Pack rendering mechanism.**
Alternatives: (a) LLM authors the pack from the corpus (max polish); (b)
deterministic structural projection from the corpus (no LLM body authorship);
(c) hand-curate each pack.
**Recommendation: (b).** Evidence: the corpus is ALREADY the curated,
refresh-kept truth (Slice 1 + 2); the pack is a RENDERING of it (master §2
"never a fork"). An LLM body-author (a) reintroduces the exact betrayal the
program exists to prevent — a hallucinated leverage claim entering the
user-facing surface; deterministic projection makes that impossible by
construction (same protection-floor shape as Slice-1's refresh, D-CUR.4).
Hand-curation (c) is the "never ships" failure mode wearing a quality costume.
Curation/judgement lives in the corpus authoring (Class B synthesis) + the
gate, NOT in a per-pack LLM pass. New component `framework/tools/knowledge-pack/`.
F4: HIGH.

**D-PUSH.2 — Bootstrap-wiring contract (the in-fence buildable half of
distribution).**
`primitive-rationale: extraKnownMarketplaces + autoUpdate:true settings stanza
— native Claude Code zero-user-action auto-update wiring (Lens 1), no bespoke
fetch loop.`
Alternatives: (a) document a manual "run `/plugin marketplace add` +
toggle auto-update" setup for each user; (b) `workspace-bootstrap` writes an
`extraKnownMarketplaces` stanza with `"autoUpdate": true` into the workspace's
`.claude/settings.json`; (c) a bespoke per-workspace fetch routine (master
D-CLP.4 alternative (d)).
**Recommendation: (b).** Evidence: §3.1.2 — third-party marketplaces default to
auto-update OFF, so zero-user-action REQUIRES either a one-time user toggle (a)
or the settings stanza (b); (b) is the only one that delivers TRUE
zero-user-action-after-the-bootstrap (the bootstrap IS the one-time setup, and
the doc-confirms the project-scope `extraKnownMarketplaces` stanza is the
sanctioned mechanism — discover-plugins §"Configure team marketplaces"). (a)
pushes translation burden onto the user (AC.PO.1 failure). (c) is the bespoke
pull loop the doctrine leg exists to prevent. F4: HIGH on the mechanism, MEDIUM
on whether bootstrap writes project- vs user-scope settings — builder's call at
S4b (the stanza shape is pinned; the scope target is method).

**D-PUSH.3 — Owner-gate sequence (the ASK-FIRST-on-public ordered list).**
**Recommendation (the exact ordered ⛔OWNER list, §6 S4c):** (1) owner creates
the PUBLIC marketplace repo → (2) seed `marketplace.json` + the gate-passed
pack → (3) owner first-publishes (push) → (4) observe arrival on a second
workspace. Each is ⛔OWNER; the persona NAMES each, executes NONE. Evidence:
the agent/persona cannot create public repos or push off-machine
(ASK-FIRST-on-public; egress-consent floor); every gate is reversible only
before publish (published content is mirrored/cached — master §3.4 low
reversibility), so the gate sits BEFORE each irreversible step. Standing
approval is the owner's explicit future option (§6), never assumed. F4: HIGH.

**D-PUSH.4 — Weekly cadence binding (reuse vs separate).**
Alternatives: (a) a NEW scheduler for the pack render; (b) reuse Slice 1's
sealed cadence binding (the refresh routine) and add the pack-render as a step
in the same cadence.
**Recommendation: (b).** Evidence: Slice 1 already ships + (owner-gate-pending)
a scheduled binding that runs the refresh ~weekly (`c41f9473`,
`framework/tools/capability-refresh/cadence/`); a SECOND scheduler is the
duplicate-primitive anti-pattern the doctrine leg flags (Lens 1 +
tool-selection-rubric). The pack render consumes the refresh's output — they
are the same cadence, one after the other. F4: HIGH.

**D-PUSH.5 — Pack staleness / versioning.**
Alternatives: (a) pre-assign pack version numbers; (b) derive at publish time
from (date, content-hash) + carry per-entry corpus `source_fetch_ts`
passthrough + a pack-level generated-ts; (c) no version, latest-wins only.
**Recommendation: (b).** Evidence: `feedback_version_numbers_at_release_time`
forbids pre-assignment (a); (c) loses the staleness signal Slice 1 worked to
create (an entry's `source_status: stale` must survive into the pack so the
user-facing surface never silently presents stale-as-current — the §AUTHORING
stale rule, propagated). The content-hash makes "did the pack actually change"
deterministic (drives whether a publish is even warranted). F4: HIGH.

### F2 — honest doubts, named

1. **"Pushed without pulling" is an approximation (master §10 F2.1, re-affirmed
   by the live verification).** Marketplace auto-update IS an automated fetch at
   startup under the hood. The defensible claim is zero-user-action-after-setup,
   and AC.CLP-PUSH.3 tests exactly that. §3.1 confirms the mechanism delivers
   it; no current Claude-native channel provides true server-push, and that gap
   is named, not papered over.
2. **The `/reload-plugins` prompt is a real, named one-keystroke caveat**
   (§3.1.4). Content ARRIVES with zero action; activating newly-arrived
   components into the live session is a platform-prompted single keystroke.
   This is the platform's behavior (`/reload-plugins`), not a loam gap, and it
   is surfaced to the owner before S4c. If the owner considers even one
   keystroke too much, that is an upstream platform constraint with no
   loam-side fix — named honestly rather than hidden behind "zero action."
3. **The pack is rendered from a small corpus (master §10 F2 / Slice-1 F2.4 —
   4 Class A entries).** The render contract is built against a corpus an order
   of magnitude smaller than its eventual load; pack ergonomics at 40 entries
   (context cost of the installed skills-pack — the platform shows a "Context
   cost" estimate per §3.1) are untested. Named for the first-pack scope; the
   deterministic render scales, but pack-size-vs-context-cost is a real future
   tuning surface.
4. **Per-publish owner gate puts the owner on a weekly cadence (master §10
   F2.3).** Right floor for a public action; the standing-approval option
   exists but is deliberately not pre-decided (§6, §7.2).
5. **Self-application / dual-surface risk (master §10 F2.6, applied to the
   pack).** The pack is corpus-derived; if the render ever diverges from the
   corpus (a manual pack edit), the program recreates the dual-surface failure
   D-CLP.5 fixed. The deterministic render + content-hash guard this: the pack
   is regenerated, never hand-edited (S4a halt-trigger 6).
6. **S4c verification depends on owner action + a second real workspace.** The
   ★ AC.CLP-PUSH.3 real-publish leg cannot be machine-verified before the owner
   publishes; the LOCAL leg (S4b, local-path marketplace) is the strongest
   pre-publish evidence. The roadmap row carries a ⛔OWNER-pending marker until
   the real observation lands (mirrors Slice-1's post-seal ★ pattern).

## §11 Provenance trail

- Master plan: `docs/plans/claude-leverage-program.md` (Slice 4 section; §2
  "Weekly knowledge pack" + "Distribution channel" rows; §5 AC.CLP-PUSH.\*;
  §6.4; §10 D-CLP.4 + F2.1/.5; D-CLP.4 owner ratification Discord
  1514753768175042771, 2026-06-11).
- Slice 1 sealed: `docs/plans/claude-leverage-program-s1-currency.md` +
  `.manifest.yaml` (seal `c41f9473`; the corpus + refresh + cadence binding
  this slice renders FROM and reuses).
- Slice 2 sealed: `docs/plans/claude-leverage-program-s2-doctrine.md` (seal
  `f308b398`; the skills-pack form + the doctrine this slice obeys).
- Corpus contract: `docs/capability-corpus/AUTHORING.md` (Class A/A-prime/B;
  no-cross-class-write; stale-never-silently-current rule the pack propagates).
- Bootstrap surface: `framework/workspace-bootstrap/README.md` + `src/loam/
  workspace_bootstrap/` (the in-fence wiring half; `.claude/settings.json` is
  written at scaffold).
- **Live marketplace re-verification (plan-author, 2026-06-14, WebFetch):**
  `https://code.claude.com/docs/en/discover-plugins` (user-level auto-update
  toggle; default-off for third-party; local-path marketplace addable;
  `/reload-plugins` post-update prompt; `extraKnownMarketplaces` team-settings
  stanza); `https://code.claude.com/docs/en/plugin-marketplaces`
  (marketplace.json + plugin.json + skills-pack walkthrough);
  `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
  (latest 2.1.176; `extraKnownMarketplaces` managed `autoUpdate` by 2.1.160;
  v2.1.142 persistence fix — re-pins master's .140/.142 discrepancy).
- Prime objective: `docs/VALUE_PROPOSITION.md` (AC.PO.1 line 117; AC.PO.2 line
  127; the leg-4 framing).
- Conventions + shape exemplars: `plugins/dev-sdlc/docs/conventions/plan-docs.md`
  (sub-plan + manifest shape; §2bis Primitive-check requirement);
  Slice-1/Slice-2 manifests (new_component + counter-confirm-at-apply pattern).
- Memory corpus: `feedback_version_numbers_at_release_time`,
  `feedback_scope_descriptive_ac_ids`, `feedback_test_outcome_altitude_required`,
  `feedback_no_anthropic_api_key`, `feedback_record_ratification_before_dispatch`,
  `feedback_dispatch_explicit_loam_amend_apply`,
  `feedback_published_state_only_from_git_refs` (S4c publish-state verified from
  git refs, never artefact prose).
