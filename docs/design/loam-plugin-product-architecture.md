# loam — Plugin / Product Architecture (forward design)

**Date:** 2026-06-01
**Status:** FORWARD / EXPLORATORY design (1.1+) — options + recommendations, no code, no amend, nothing built. Every tier and plugin below is an owner-gated follow-on.
**Owner:** Luke Ivers
**Author:** `loam-plan-author` (Opus)
**Working tree:** `/Users/lukeivers/loam` (main)
**Doc class:** architecture / strategy (design)
**Trigger:** owner directive (Telegram 13383–13388) — what should loam build as plugins, what is default vs opt-in, and how does dev-sdlc generalize into the build-publish substrate.

**Reads this composes on (Tier-0 verified on disk 2026-06-01):**
- `docs/VALUE_PROPOSITION.md` — the prime objective (per-user-tuned translation: user brings WHAT, loam owns HOW) + the protection floor (§52–58) + the harness-as-builder token discipline (§83–85). This is the north star every tier ladders to.
- `docs/design/shared-artefact-quality-catalogue.md` — the WHAT-quality. Its **profile-class axis** (`ALWAYS-ON-FLOOR / LEARNED-PROFILE / PER-BUILD`, §14) is the organizing axis this architecture reuses for the default-vs-opt-in rule. 11 categories, 58 items, 7-item security floor.
- `docs/design/dev-sdlc-1.0-readiness-and-roadmap.md` — the build-engine. Its header (lines 1–14) declares the Layer-1 / Layer-2 split: Layer 1 = internal-machinery fixes; **Layer 2 = the generalization into the build-and-publish substrate**, which is this doc's Layer 2.
- `docs/design/adaptive-interaction-model.md` — the learning engine. The matrix (`{value, confidence, evidence}` per `component × axis`, §1) is the store that holds the design profile AND drives the opt-in-plugin suggestion engine. §6 composition map is the spine.
- `CLAUDE.md` Lens 0–7 — applied throughout; Lens 4 confidence marked inline, Lens 7 ruthless-feedback on the seed in §2.

---

## Executive summary (non-technical)

When loam builds something for you — a script, a widget, a small tool, a whole app — three different kinds of thing are at work, and they should be organized differently:

1. **The floors** are the things you must never be able to turn off, because turning them off betrays you: don't leak passwords, don't ship something a blind person can't use, don't quietly burn your tokens. These aren't features you pick — they're the ground everything stands on. They live in the **build-publish substrate** (a generalized dev-sdlc), always-on and invisible.
2. **The "good by default" layer** is the stuff that's on for everyone but tunable to you — most importantly your **design language**, so everything loam makes for you comes out beautiful AND looks like it came from the same place. This is the **Design plugin**, on by default.
3. **The capabilities** are domain-specific powers you opt into — writing a book series, coordinating a cause, crunching data. Off by default; loam's learning engine *suggests* the right ones for you as it watches how you work.

The rule that decides which bucket anything goes in is one test, borrowed from the quality catalogue: **can a user safely opt out? If no → it's a substrate floor. If it's a positive capability you'd choose → it's a plugin.** That single test draws the whole map.

**This doc produces:** the refined three-tier model with the floor-vs-plugin line drawn explicitly; dev-sdlc's generalization into the substrate (with the new verbs it must expose); the Design plugin's scope; an exhaustive 18-candidate plugin list each tagged by tier; the codified default-vs-opt-in rule; and the single highest-leverage plugin to build first.

**The seed survives with one structural correction** (§2): the dispatcher's 3-tier model is right, but "tier" and "default-vs-opt-in" are two axes that the seed collapses into one. Keeping them separate (tier = *where the capability lives*; default-state = *is it on*) makes Publish and a few floors classify cleanly where the collapsed model forced an awkward call.

---

## §1 The refined tier model

The seed's three tiers are correct. The refinement: **tier is the architectural placement (where the capability lives + who owns it); default-state is an orthogonal property (on/off/can't-disable).** They correlate but are not identical — and forcing them to be identical is where the seed strained (§2). The model:

| Tier | Name | Default-state | Visible? | Owns | Profile-class home |
|---|---|---|---|---|---|
| **0** | **Substrate** (the build-publish engine + the floors) | always-on, **can't disable** | invisible | the floors + the build/publish verbs | `ALWAYS-ON-FLOOR` |
| **1** | **Default plugins** | on by default, **tunable** | visible | the "good by default" promise (design, and possibly publish-surface) | `LEARNED-PROFILE` |
| **2** | **Opt-in capability plugins** | off by default, **suggested** | visible | domain-specific powers | `PER-BUILD` capability + its own `LEARNED-PROFILE` rows |

**The axis correspondence is the elegance the dispatcher saw, made precise:** the catalogue's profile-class axis (`FLOOR / LEARNED-PROFILE / PER-BUILD`) maps almost one-to-one onto the tier's default-state. `ALWAYS-ON-FLOOR` ⇒ Tier 0 (can't-disable). `LEARNED-PROFILE` ⇒ Tier 1 (on, tunable — it's *learned*, so it must be on to learn). `PER-BUILD` ⇒ a Tier-2 capability's per-invocation surface. This is end-to-end coherent: the same axis that classifies a *quality concern* classifies a *plugin*. **[HIGH→default-on]**

**Where Tier 0 is not just floors.** The dispatcher's seed framed Tier 0 as "dev-sdlc generalized + the floors live here." Correct, but Tier 0 holds two distinct things that must not be conflated: (a) **the build-publish engine** (the verbs — build, publish, gate) which is *mechanism*, always-on because it's how everything else runs; and (b) **the quality floors** which are *policy* the engine enforces. The engine is the loom; the floors are the minimum-quality cloth it refuses to weave below. Both are Tier 0, both can't-disable, but they answer different questions (HOW to build vs WHAT-minimum to guarantee). §3 designs (a); the catalogue already designed (b).

---

## §2 Ruthless feedback on the seed (Lens 7) — kept, with one correction

**Disagreement (named):** the seed treats "tier" and "default-vs-opt-in" as a single axis ("substrate = always-on; default plugin = on; opt-in = off"). That collapse forces two genuine cases into awkward positions.

**Evidence (named):**
1. **Publish/deploy doesn't classify cleanly under the collapsed model.** The seed hedges — "Possibly a Publish/deploy plugin here too" (Tier 1). But publishing has a *floor* component (the no-leak final scan, X3/X1 in the catalogue §17, which is `FLOOR-conditional-1.0` and can't-disable) AND a *capability* component (which host, custom domain, deployment-protection level — `PER-BUILD`). Under one collapsed axis, Publish is either "always-on" (wrong — you don't auto-deploy everything) or "opt-in" (wrong — the no-leak scan is non-negotiable). Under two axes it's clean: **the publish *gate* is a Tier-0 floor; the publish *act* is a Tier-1 default-on convenience the persona offers, tunable per build.**
2. **The catalogue already proved the two axes are separate.** Catalogue §14 indexes by profile-class (FLOOR/LEARNED/PER-BUILD) — a *placement* axis — and *separately* carries a `1.0-blocking?` flag — a *blast-radius* axis. The catalogue's §2.3 explicitly says "the right organizing axis is profile-class × blast-radius," i.e. two axes. The plugin architecture should mirror that, not flatten it.

**Alternative (named):** keep the three tiers exactly as seeded, but make **default-state an explicit second property** of each plugin (on/off/can't-disable), correlated-with-but-not-identical-to tier. This is the §1 table. It changes nothing about the seed's intent; it removes the one place the seed had to say "possibly."

**Net: seed accepted, 3 tiers kept, one axis split out.** No better organizing axis exists — the profile-class reuse is genuinely the right spine, and the dispatcher's instinct to reuse it is correct. **[HIGH-confidence]**

---

## §3 dev-sdlc as the build-publish substrate (Tier 0, Layer 2)

This is the load-bearing generalization and the honest gap. The dev-sdlc readiness review (Layer 1) is about making the *internal* machinery correct — three small fixes (tracked-status seal assertion, install source-ref, fence-prune). **Layer 2 is not those fixes. It is a new role for the same machinery**, and the doc must name that honestly (the review's header already declares the owner is doing this eyes-open, lines 12–14).

### 3a. What dev-sdlc is today vs what the substrate must be

| | dev-sdlc today (Layer 1) | The build-publish substrate (Layer 2) |
|---|---|---|
| **Who it serves** | loam contributors building loam | the primary persona building artefacts FOR the end user |
| **What it builds** | sealed Python components of loam | arbitrary end-user artefacts at every scale (scripts, widgets, tools, docs, apps) |
| **Visibility** | behind the dev-mode partition | invisible substrate the persona always has |
| **Quality contract** | ODD + CDC + seal-fence (correctness of loam) | ODD + the **shared-artefact quality floors** (correctness AND safety of the user's output) |
| **Method** | the amendment-cycle ritual (heavyweight, plan-doc, seal) | **scaled to artefact size** — a one-file widget does not get the full amendment ritual |

**The generalization gap, named honestly (Lens 7):** dev-sdlc's ritual is calibrated for big sealed Python builds. A user asking for "a little tool that renames my photos" must NOT trigger a plan-doc + seal + CDC ceremony — that would be the catalogue's anti-pattern (over-structuring a one-off, VALUE_PROPOSITION §38–41 "don't meet every do-this-once with shouldn't-this-be-a-framework"). The substrate's hardest design problem is **method-scaling**: the same ODD principles (objective + acceptance, method is the builder's call) and the same floors apply at every size, but the *ceremony* scales down to nothing for small artefacts. This is genuinely OPEN (§7 F1).

### 3b. What the substrate exposes to the persona (the verbs)

The harness test (VALUE_PROPOSITION §119): a capability the persona can't invoke is outside the harness. So the substrate must expose **persona-invokable verbs**, not just a methodology document. Three verbs, each marked with its Claude-leverage primitive (Lens 1):

1. **`build`** — turn an objective + acceptance into a working artefact, with the floors enforced inline. *Claude-leverage:* this is the **`handsoff-loop` SKILL generalized** — that skill already exists (decompose fuzzy ask → checkable done → dispatch sub-agents → independent judge). The substrate's `build` verb IS handsoff-loop with the quality floors wired into its judge step. **Compose, don't reinvent.** **[HIGH→default-on]**
2. **`gate`** — run the floor checks (no-secrets, a11y-lint, injection-scan, token-hygiene, no-leak) and block-or-surface in plain language. *Claude-leverage:* a **Claude-native subagent/scope** running the gate (catalogue X1, VALUE_PROPOSITION §155 composition). This is the catalogue's pre-flight gate, promoted to a substrate verb. The floors (catalogue §17) are its policy. **[HIGH→default-on]**
3. **`publish`** — take a gated artefact to where its recipients can reach it (a hosted URL, a shared file, an installed package, a sent doc). *Claude-leverage:* composes on host platforms' deploy APIs (Vercel/Netlify/Cloudflare) + their built-in TLS/secret-store/deployment-protection (catalogue S3/S2/S9). The persona owns *which* mechanism; the user never picks. **[OPEN→fork F2 — publish surface is genuinely open]**

**The verb that makes it a *substrate* and not three loose tools:** `build` always calls `gate` before it returns "done," and `publish` always calls `gate` before it emits a link. The floors are not opt-in steps the persona remembers — they are wired into the verbs' control flow, so a floor can't be skipped by forgetting. This is the structural-enforcement principle (`feedback_structural_enforcement_on_recurrence.md`) applied to the build engine: the floor is enforced by the verb's wiring, not by the persona's discipline. **[HIGH→default-on]**

### 3c. How the floors live in the substrate (the floor-vs-plugin line, drawn)

**The test (the dispatcher's, codified):** *can a user safely opt out? If no → substrate floor. If it's a positive capability the user would choose → plugin.*

Applying the test to the catalogue's `ALWAYS-ON-FLOOR` set (~24 items, catalogue §14) confirms they ALL land in Tier 0 as substrate floors, because each fails the opt-out test — a user cannot safely choose to leak secrets (S2), ship inaccessible output (A1–A5), bleed loam's tokens (P4/M5), or skip the no-leak scan (X3). These are the engine's policy, enforced by `gate`. **The 7-item security floor (catalogue §17) is the conditionally-1.0-blocking subset of this.**

Conversely, the catalogue's `LEARNED-PROFILE` and `PER-BUILD` items are NOT substrate — they're either the Design plugin's territory (the design-token rows, §4) or a capability plugin's per-build surface. **The line: floors enforce a *minimum the user can't waive*; plugins add *capability the user chooses*.** Drawn item-by-item in §6.

---

## §4 The Design plugin (Tier 1, default-on)

Per owner 13387: the Design plugin is **its own plugin, not part of dev-sdlc.** This is correct and the doc affirms it — dev-sdlc is the *engine* (mechanism); design is *taste* (learned content). Conflating them would put learned per-user taste inside the always-on can't-disable substrate, which is wrong: taste is tunable, the engine is not.

### 4a. Scope

The Design plugin **owns the design-token profile and the "make it beautiful" generation.** Concretely it owns catalogue §5 (design language, D1–D6) plus the accessibility constraints that bind it (A3 color-contrast constrains D1's palette — catalogue §6 A3). It consumes:
- **The catalogue's §5** as its WHAT (design tokens, cross-build consistency, review-edits-flow-back, theming, responsive, component reuse).
- **The learned per-user profile** as its store — specifically the `adaptive-interaction-model.md` matrix, **extended with output-quality rows** (catalogue §14 recommendation: "do not build a second profile store — add output-quality rows to the existing interaction-model matrix"). The Design plugin reads/writes design-token cells in that same `{value, confidence, evidence}` matrix.

### 4b. The compounding mechanism (why it's a plugin and not a static theme)

The Design plugin's load-bearing feature is catalogue D3: **a review-time edit to a token-governed property writes back to the profile** via the interaction-model's evidence→update path (hysteresis: one tweak is provisional, a repeated pattern updates the token). This is *why* it's default-on and learned, not opt-in: it can only learn your taste if it's on for every build. The "good by default" promise (the dispatcher's phrase) IS this compounding — artefact #5 looks like the same maker as #1 because the tokens carried forward, and got more "you" with each edit.

### 4c. How it composes with the substrate

The Design plugin is a **Tier-1 default-on input to the Tier-0 `build` verb.** When `build` generates any visual artefact, it reads the Design plugin's tokens for styling and the substrate's a11y floor (A1–A5) constrains them — A3 contrast-checks the token palette so brand and accessibility never fight (catalogue §6 A3, "constrains D1"). *Claude-leverage (Lens 1):* the design-token store is a CSS-custom-properties / Tailwind-config / Style-Dictionary file, structurally identical to the interaction-model cells — composes on the same FBM write path, no new store. **[HIGH→default-on]**

**Lens 2 check:** reduces translation burden (the user never specifies styling per-build — "got a brand color, or want me to pick a clean default?" once, then inferred forever, catalogue D1) ✓; adds to the persona's toolkit (a `style(artefact)` capability the persona invokes) ✓.

---

## §5 The default-vs-opt-in decision logic (the codified rule)

The reusable rule, stated once, applied in §6:

> **Step 1 — Opt-out test (places it in a tier).** Can a user *safely* opt out of this?
> - **No** (opting out betrays the user — leaks, inaccessibility, token-bleed, breakage) → **Tier 0 substrate floor**, can't-disable.
> - **Yes, but it's the "good by default" baseline** (a quality/taste default everyone benefits from, tunable to them, must be on to *learn* them) → **Tier 1 default plugin**, on + tunable.
> - **Yes, and it's a positive domain capability** (a power the user would actively choose, irrelevant to users who don't do that kind of work) → **Tier 2 capability plugin**, off + suggested.
>
> **Step 2 — Profile-class confirm (cross-checks the placement).** Read the item's catalogue profile-class. `ALWAYS-ON-FLOOR` must land Tier 0; `LEARNED-PROFILE` must land Tier 1 (it's learned, so on-by-default); `PER-BUILD` is a Tier-2 capability's per-invocation surface. A mismatch between the opt-out test and the profile-class is a design smell to resolve before shipping.
>
> **Step 3 — Suggestion (Tier 2 only).** A Tier-2 plugin is *suggested* by the learning engine, never force-installed. The `adaptive-interaction-model.md` matrix watches the user's work-areas (§2e "new rows appear by demand"); when a sustained signal shows the user doing domain-X work, the engine surfaces "want the X plugin?" — the same demand-paging shape, pointed at plugins. **This is the engine that makes opt-in not mean "the user has to know it exists."**

The Lens-4 read on the rule itself: **HIGH-confidence.** It's a direct reuse of an axis the catalogue already validated end-to-end, and Step 3 reuses the interaction-model's already-designed demand-paging. The only OPEN piece is the suggestion *threshold* (how much signal before suggesting), which inherits the interaction-model's dark-launch-then-calibrate discipline rather than importing a number (§7 F3).

---

## §6 The exhaustive candidate-plugin list

Every plugin loam plausibly ships, each tagged: **tier** · **default-state** · **catalogue categories / capabilities owned** · **Lens-1 primitive** · **one-line rationale**. Floors are shown as substrate, NOT plugins, to make the line visible.

### Tier 0 — Substrate (NOT plugins; shown to draw the line)

These are the floors + the engine. They are listed here so the floor-vs-plugin line is explicit: **none of these is a plugin** — they're the ground.

| # | Substrate element | Default-state | Catalogue categories owned | Lens-1 primitive | Rationale (fails opt-out test) |
|---|---|---|---|---|---|
| 0a | **Build-publish engine** (`build`/`gate`/`publish` verbs) | can't-disable | — (mechanism) | `handsoff-loop` SKILL generalized + Claude subagent scopes | how everything runs; not a capability, the engine |
| 0b | **Security floor** | can't-disable | S2,S3,S4,S8 + posture of S1/S5/S6/S7 (catalogue §3) | host TLS/secret-store + PreToolUse secret-guard + OWASP-cite | a user can't safely opt into leaking secrets/injection |
| 0c | **Accessibility floor** | can't-disable | A1–A5 (catalogue §6) | axe-core/Lighthouse lint + Claude-vision alt-text | a shared inaccessible artefact excludes people + legal exposure |
| 0d | **Token-hygiene floor** | can't-disable | P4, M5 (catalogue §7/§12) | context-hygiene check | owner-betrayal class — VALUE_PROPOSITION §83–85, the verified leak |
| 0e | **No-leak pre-flight gate** | can't-disable | X1-no-secrets, X3 (catalogue §10) | Claude-native gate subagent | the `gate` verb's policy; can't ship a leak |
| 0f | **Correctness floor** | can't-disable | M2 (smoke/outcome-altitude test), R1 (error handling), I3 (UTF-8) | ODD outcome-altitude discipline | "perfect translation that breaks what it built is worthless" (VP §47) |

### Tier 1 — Default plugins (on by default, tunable, visible)

| # | Plugin | Default-state | Catalogue / capability owned | Lens-1 primitive | Rationale |
|---|---|---|---|---|---|
| 1 | **Design** | on, tunable | §5 design language D1–D6 (+ A3 constraint) | design-token file + interaction-model matrix write-back | the "good by default" beauty + cross-build consistency promise; must be on to learn taste (owner 13387) |
| 2 | **Publish-surface** | on, tunable | publish *act* (host choice, domain, deploy-protection level — S9, P5 cost-ceiling) | host deploy APIs (Vercel/Netlify/CF) | the persona offers "want me to put this somewhere people can reach it?" by default; the *gate* is Tier-0, the *act* is here. **[OPEN→fork F2]** |

**Note on Publish placement:** this is the one genuine fork the §2 axis-split resolved. Publish-surface is Tier-1 default-on *as an offer* (the persona proactively offers to publish a finished artefact), but never auto-publishes without the user's go — the interaction-model's "open on talk, cautious on actions" asymmetry (`adaptive-interaction-model.md` §2d) means *offering* is open, *acting* (a real deploy) is surface-first. **[OPEN→fork F2]**

### Tier 2 — Opt-in capability plugins (off by default, suggested, visible)

| # | Plugin | Catalogue / capability owned | Lens-1 primitive | Rationale (positive domain capability) |
|---|---|---|---|---|
| 3 | **Writing / book-production** (litrpg pipeline → generalized) | long-form narrative production, canon-store, chapter-loop, continuity-regression | `claude -p` synthesis client + canon-store component (in-flight: `workspace/products/litrpg-writer`) | already in flight; generalizes from litrpg to any long-form writing — a clear opt-in power |
| 4 | **Cause-coordination (Cairn)** | distributed cause/volunteer/campaign coordination | in-flight: `workspace/products/distributed-cause-coordination` | already in flight; domain-specific coordination, irrelevant to non-organizers |
| 5 | **Data / analytics** | data-analysis, charts, dashboards, notebook workflows | Claude analysis-tool / code-execution + chart primitives | a power for data-doers; off for everyone else |
| 6 | **Compliance pack** | catalogue §4 C1–C6 (regime inference, privacy-policy gen, license) | regime→control-set mapping + policy generation | *positive capability* (apply controls) but **never asserts compliance** (catalogue F3); opt-in because most artefacts don't need it |
| 7 | **Auth / identity** | catalogue S1 provider-wiring + gated-access flows | OIDC `.well-known` discovery + host-native auth (NextAuth/Clerk) | a capability for *gated* artefacts; the PKCE-floor is Tier-0, the *provider-wiring* is opt-in per build |
| 8 | **i18n / localization** | catalogue §11 I1–I2 (locale formatting, RTL, translatable strings) | `Intl` + logical-property CSS | opt-in scaled to inferred audience (catalogue F6); I3/UTF-8 is the Tier-0 floor, the rest is capability |
| 9 | **Data-handling / privacy ops** | catalogue §9 H1–H4 (retention, deletion, export, right-to-erasure) | scaffolded deletion/export endpoints | opt-in for data-bearing artefacts; PII-at-rest escalates toward the S7 floor |
| 10 | **Observability / monitoring** | catalogue §8 R3 uptime, R4 backups | host uptime-check + alert to user's channel (Telegram) | opt-in "tell me if it goes down"; R1/R2 (error-handling, no-PII-logs) are the Tier-0 floor |
| 11 | **Documents / publishing (prose)** | styled docs, reports, slide-decks, themed HTML | dynamic-theme generated-docs (`feedback_dynamic_theme_for_generated_documents.md`) | a non-app artefact pipeline; composes with the Design plugin's tokens |
| 12 | **Scheduling / automation** | recurring tasks, cron, background monitors for the user's *own* workflows | CronCreate / launchd / `/loop` / Routines (per `claude-feature-awareness`) | the 12-hour-example capability (VP §96–103) as a user-facing plugin |
| 13 | **Integrations** (email/calendar/finance) | real-tool integration (VP toolkit #4) | dedicated MCPs (Gmail/Calendar) | opt-in per integration; each composes on a Claude MCP |
| 14 | **Research** | multi-source fact-checked synthesis | `deep-research` SKILL | already a SKILL; a packaged opt-in research capability |
| 15 | **Personal-life / logging** (visit-log, entity tracking) | structured life-logging (restaurants/places/events) | `log-visit` SKILL + entity tables | a Luke-specific in-flight capability; clean opt-in example |
| 16 | **Trust-mark / attestation** | catalogue §13 T1/T2 (made-with-loam quality mark) | the `gate` verb as attestation source | opt-in badge gated on floors passing; the adoption flywheel (catalogue §16) |
| 17 | **Cost-governance** | catalogue P5 spend-ceilings on hosted artefacts | host billing-limit + loam cost-governance | opt-in for hosted artefacts that could run a bill |
| 18 | **Voice / channel** (Telegram-style interfaces for built artefacts) | give a built artefact a conversational channel | Telegram plugin / MCP | opt-in; lets a user's artefact talk to *its* users the way loam talks to Luke |

**Count:** 6 substrate elements (NOT plugins) + **18 candidate plugins** (2 default-on, 16 opt-in capability). **2 default-on plugins: Design + Publish-surface.**

**Provenance of the in-flight ones (Tier-0 verified on disk):** Writing (#3) = `workspace/products/litrpg-writer/`; Cause-coordination (#4) = `workspace/products/distributed-cause-coordination/`. Both real, both confirmed 2026-06-01. Research (#14), visit-log (#15), scheduling (#12) exist today as SKILLs — the architecture's claim is they *graduate into plugins* when a user opts in, not that they're net-new.

---

## §7 Open design forks (Lens 4 — surface to owner)

The genuine forks where confidence drops and the owner should rule. (Distinct from the catalogue's forks F1–F6, which are quality-item forks; these are architecture forks.)

- **F1 — Method-scaling: does the substrate's `build` verb run the full amendment ritual, or a scaled-down ceremony for small artefacts?** The hardest substrate problem (§3a). A one-file widget must NOT get a plan-doc + seal + CDC. **Recommendation:** a **size-tiered ceremony** — tiny artefacts get objective + acceptance + the floors only (no seal, no plan-doc); large/recurring artefacts get the full ODD cycle. The size-classifier is the open piece; inherit the interaction-model's "scale structure to what this person has shown they want" (VP §39). **[OPEN — genuinely uncertain where the size cut is]**
- **F2 — Publish-surface: which hosts, and is publishing a Tier-1 default-on offer or a Tier-2 opt-in?** (§3b verb 3, §6 Tier-1 note.) **Recommendation:** Tier-1 *offer* (persona proactively offers), Tier-0 *gate* (the no-leak scan is non-negotiable), Tier-2 *advanced host config* (custom domains, multi-region). Start with one host (Vercel — its TLS/secret-store/deploy-protection give S2/S3/S9 nearly free) and generalize on demand. **[OPEN — host strategy + default-vs-opt-in line both open]**
- **F3 — Opt-in suggestion threshold: how much signal before the learning engine suggests a Tier-2 plugin?** **Recommendation:** inherit the interaction-model's dark-launch-then-calibrate discipline (`adaptive-interaction-model.md` §3); don't import a number. A too-eager suggester re-creates the "shouldn't-this-be-a-framework" anti-pattern (VP §38). **[OPEN — calibration, not architecture]**
- **F4 — Do capability plugins carry their own floors, or only consume the substrate's?** A writing plugin has domain-specific quality concerns (continuity, canon-consistency) that look floor-shaped within that domain. **Recommendation:** the substrate floors are universal (every plugin gets them free); a plugin MAY add *domain floors* enforced by its own `gate` extension, but cannot weaken a substrate floor. **[OPEN — the plugin-extends-gate contract is undesigned]**
- **F5 — Plugin packaging: Claude-plugin, SKILL, MCP, or workspace-product?** The candidate list spans all four shapes (Design = plugin; Research = SKILL today; Integrations = MCP; Writing = workspace-product). **Recommendation:** the *tier* is the architectural truth; the *packaging* follows the `tool-selection-rubric` per plugin (a recurring auto-discoverable capability → Claude-plugin/SKILL; a real-tool bridge → MCP; a large stateful build → workspace-product). Don't force one packaging shape. **[OPEN — per-plugin, not global]**

---

## §8 Decision summary + the single highest-leverage first build

### The tier model (refined)
Three tiers kept from the seed; **default-state split out as a second axis** so Publish and the floors classify cleanly. Tier 0 = substrate (the build-publish engine + the floors, can't-disable, invisible); Tier 1 = default plugins (Design + Publish-surface, on + tunable); Tier 2 = opt-in capability plugins (off + suggested). The catalogue's profile-class axis (`FLOOR/LEARNED/PER-BUILD`) maps onto the tiers — end-to-end coherent.

### The floor-vs-plugin line
**Test: can a user safely opt out? No → substrate floor; positive capability → plugin.** All 24 catalogue `ALWAYS-ON-FLOOR` items land in Tier 0 (security, a11y, token-hygiene, no-leak, correctness — §6 elements 0b–0f). Everything `LEARNED-PROFILE` or `PER-BUILD` is a plugin (Tier 1 design, Tier 2 capabilities).

### Counts
6 substrate elements (not plugins) + **18 candidate plugins**; **2 default-on (Design, Publish-surface)**, 16 opt-in.

### The single highest-leverage plugin to build FIRST
**The build-publish substrate's `gate` verb (Tier 0, element 0e) — the catalogue's pre-flight gate promoted to a persona-invokable verb.** Rationale: it is the consumer that makes the entire quality catalogue *operational* (catalogue §10 X1: "without it, the items are advisory"); it is the policy seam every other tier depends on (the Design plugin's a11y constraint, every capability plugin's domain floors, the trust-mark's attestation all run through it); and it composes on an existing primitive (a Claude subagent scope + the `handsoff-loop` judge). It's cheap relative to leverage — a gate + the floor checks, not new infrastructure. **It is the foundation the trust-mark flywheel (catalogue §16, the catalogue's highest-leverage *adoption* item) is gated on** — so building `gate` first lights up both the quality floor AND the adoption engine's foundation.

*Caveat (Lens 7):* the *plugin* the dispatcher asked to rank is, strictly, the **Design plugin** (the highest-leverage Tier-1 *plugin*, since `gate` is substrate not a plugin). If the question is "first **plugin**," it's **Design** — it delivers the visible "good by default" promise and the compounding learned-taste mechanism. If the question is "first thing to build in this architecture," it's the substrate's **`gate` verb**, because Design (and every capability plugin) consumes the substrate, and the substrate must exist first. **Recommendation: build `gate` (substrate) first, Design (plugin) second** — dependency order forces it, and `gate` unlocks the flywheel.

### Seed verdict
**Kept.** The 3-tier seed is right-shaped and the profile-class-axis reuse is the correct spine. One correction: split default-state out as a second axis (§2), which removes the seed's only "possibly" (Publish) and matches the catalogue's own profile-class × blast-radius dual-axis structure.

---

## §9 Provenance trail

- `docs/VALUE_PROPOSITION.md` — prime objective (§9–58), harness-as-builder token discipline (§83–85), harness test (§119), toolkit composition (§144–155), the 12-hour example (§96–103). Read 2026-06-01.
- `docs/design/shared-artefact-quality-catalogue.md` — profile-class axis (§14), security floor (§17), design language (§5), pre-flight gate (§10 X1), trust-mark flywheel (§13/§16), forks (§15). Read 2026-06-01.
- `docs/design/dev-sdlc-1.0-readiness-and-roadmap.md` — Layer-1/Layer-2 header (lines 1–14), internal-machinery state (§2–§5). Read 2026-06-01.
- `docs/design/adaptive-interaction-model.md` — matrix shape (§1), demand-paging new rows (§2e), open-on-talk-cautious-on-action asymmetry (§2d), composition map (§6), dark-launch calibration (§3). Read 2026-06-01.
- In-flight products verified on disk: `workspace/products/litrpg-writer/`, `workspace/products/distributed-cause-coordination/`. Existing plugins: `plugins/dev-sdlc/`, `plugins/loam-skills/`. Existing SKILLs (handsoff-loop, deep-research, log-visit, schedule/loop) per the session SKILL list. Verified 2026-06-01.
- `CLAUDE.md` Lens 0–7; `feedback_structural_enforcement_on_recurrence.md`, `feedback_dynamic_theme_for_generated_documents.md`, `feedback_version_numbers_at_release_time.md`, `feedback_test_outcome_altitude_required.md`.
</content>
</invoke>
