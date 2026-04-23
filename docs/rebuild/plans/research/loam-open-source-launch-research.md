# loam — Open-Source Launch Research

**Working directory (read-only):** `/Users/lukeivers/ivers-corp-pos-v2/`
**Target brand:** `loam`
**Status:** research document. Not a commitment. No code edits. Every recommendation is the owner's call.
**Sources consulted:** `CLAUDE.md`, `docs/odd-in-pos.md`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/VALUE_PROPOSITION.md`, `docs/rebuild/spec/pos-v2-objectives-spec.md`, `docs/rebuild/STATE.md`, `README.md`, `.scratch/claude-output/pos-v2-rename-brainstorm.md`, `.scratch/claude-output/loam-rename-migration-plan.md`, component.md files for primary-persona-loader, memory-system, scope-of-work.

---

## 1. Executive summary

loam is not ready to launch. It is architecturally ready to be shown. Fifteen sealed components, an explicit methodology (ODD), a named value proposition, and a design-lens discipline together produce the rarest thing in open-source AI tooling: a codebase where every behaviour has a named acceptance criterion and every criterion has a test. That is a real asset. But the public-facing surface — installation story, README-as-pitch, plugin ecosystem, the Dev/SDLC plugin that carries the ODD methodology into users' own projects — is not built. Shipping loam the day the rename lands would burn the asset: reviewers would evaluate the wrong thing (a half-documented personal framework) and the methodology pitch would not get heard. The honest shape is a six-to-nine-month runway: finish the rename, ship the Dev/SDLC plugin as the v1 "example plugin" that proves both the ecosystem and the methodology, author a coherent public documentation set, do a silent founder-circle preview, then a soft HN Show HN, then a launch proper. loam's differentiator is "Claude-attached, outcome-governed, safety-first, plugin-extensible" — four words that none of its competitors (LangChain, CrewAI, AutoGen, Claude Agent SDK, MCP servers) collectively occupy. The launch's job is to make those four words land in thirty seconds.

**Top-3 concrete next actions** (verbatim — these are the actions to take in the next 7–14 days):

1. **Author the Dev/SDLC plugin research plan.** It is both a must-ship-at-v1 plugin (per FUTURE_IDEAS Idea 3) and the vehicle that makes loam's ODD pitch visible to the developer audience who is the most receptive early market. No plugin, no v1.
2. **Write a single-page positioning document** (working title: `docs/positioning.md`) naming the one-sentence pitch, the three-paragraph description, the target personas, and the explicit non-goals. This is the doc every downstream artefact (README, launch blog post, HN title, conference abstract) quotes from. Authoring it first keeps the rebrand coherent.
3. **Adopt Apache-2.0 and write LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md.** These four files signal "this is a real project" to the first reviewer who clicks the repo and decides whether to read further. They cost a day; not having them costs the first impression.

---

## 2. What IS loam (as stated to the world)

### One-sentence positioning

> **loam is a Claude-attached, outcome-governed harness for autonomous work — the substrate in which your own AI collaborator grows.**

The sentence is deliberately shaped to land three things: *Claude-attached* (not model-agnostic — a feature per the non-goal in spec v1.0); *outcome-governed* (the ODD methodology's public face — this is what makes loam different from every LangChain-shaped framework); *substrate* (the seed metaphor from the rename brainstorm — loam is not the agent, it's what the agent roots in). The word "harness" is retained because the design corpus uses it; readers who don't know the word will infer it from context in the next paragraph.

### Three-paragraph description

> *loam is a Python-native harness for Claude-attached autonomous workflows. A long-running orchestrator, a semantic memory, a three-gate safety chain, a primary persona that translates natural-language intent into AI-effective execution, and a supervisor that keeps the whole system healthy compose into a foundation that runs quietly beneath every session. You open a Claude Code session in a loam workspace and the primary persona greets you with what needs attention — no sidecar to start, no terminal to tend, no context to re-establish. Work dispatched during a session survives the session; the orchestrator carries it through until it finishes or needs you.*
>
> *The methodology is deliberate. Every unit of delegated work — owner to persona, persona to specialist, specialist to background agent — is authored as an objective (what must be true when the work is done), bounded by constraints (budget, reversibility class, authority surface), and verified by deterministic acceptance criteria. Method is the builder's call. This is **Objective-Driven Design**, and it is the structural bet that distinguishes loam from the frameworks that give an agent a tool-belt and hope for the best. When you fail, loam's self-correction loop tracks the failure to its originating objective, not to a line of code. When you extend, the plugin protocol lets you add contributions without amending the sealed foundation.*
>
> *loam is a scaffolding — a seed from which users develop their own implementations on top of the core. It ships with foundational layers (safety, reversibility, cost governance, memory, scopes, observability, self-correction, bootstrap) and no vertical-specific plugins; domain workflows are plugins you install, not conceits baked into the harness. The first plugin — Dev/SDLC — replaces the ad-hoc workflow machinery most AI-coding setups reach for with an ODD-shaped pipeline. Everything else is yours to cultivate.*

### Who it's FOR — target user personas

1. **The technically-fluent autodidact.** Builds their own tools, keeps sessions open for days, curates a personal workflow stack, has been burned by LangChain-complexity-tax. Adopts loam because the primary-persona layer gives them one coherent surface to manage, the plugin protocol gives them the extensibility they always end up needing, and the ODD methodology gives them a project-organisation primitive they haven't found elsewhere. Luke is exactly this persona; every other target user scales out from here.
2. **The Claude Code power user.** Uses the Claude CLI daily, has hit the "this is powerful but my sessions keep resetting" wall, wants persistent orchestration without surrendering the Claude-native ergonomics they like. loam keeps them inside Claude Code while adding memory, scopes, safety, and cross-session continuity.
3. **The indie AI-tooling builder.** Writing their own agent framework, has made the specific mistakes loam's foundation already solves (safety gates, cost ceilings, reversibility, observability), wants to stop rebuilding these and start building the product. Adopts loam as infrastructure the way they might adopt FastAPI — not because they want to be told how to work, but because the primitives are right.
4. **The autism/ADHD-aware tooling builder.** Noise-averse, context-loss-averse, values systems that compose predictably. The always-on primary persona + the foundation's structural-over-advisory discipline + the hands-off lifecycle read as features, not quirks. This is a real sub-audience and a non-trivial share of the open-source-AI practitioner population.
5. **Eventually (not at launch): the curious non-technical user.** The spec names non-technical accessibility as a design priority, but the first twelve months of community building happen with technical users whose feedback will stress-test the harness layer. The non-technical door opens in phase two, after the Dev/SDLC plugin and maybe one more plugin have landed and proven the plugin ecosystem.

### What problem does it solve

The gap between what an LLM can do and what a user can get it to do. Raw Claude is powerful; raw Claude is also transient, tool-less, context-free, and one misread away from the user redoing the same request seven times in one session. loam closes the gap by adding — through an explicit, Claude-composing harness — persistence across sessions, autonomous continuity between them, structural governance on what autonomous work is allowed to do, integration with real tools, role specialisation via personas, audit trails, process structure, and composition. These are the eight capabilities the harness adds (enumerated in VALUE_PROPOSITION.md). None of them are LLM features; all of them are harness features. Raw Claude + loam = a collaborator. Raw Claude alone = a chat window.

### What it's explicitly NOT

- **Not model-agnostic.** Claude-only. No abstraction layer for OpenAI, Gemini, local models, or future Claude vendors. This is a feature and will be messaged as one. Vendor-neutral agent frameworks pay a correctness tax; loam refuses that trade.
- **Not domain-aligned.** The core ships zero vertical content — no dev-first, no PM, no ops-first, no creator-first tooling. Verticals are plugins. This keeps the core stable as the plugin surface grows.
- **Not a single-session tool.** loam is not a Claude-Code-clone, not a "better interactive REPL," not a prompt library. It is infrastructure that runs between sessions, not only during them.
- **Not a managed service.** loam is installed per-workspace on your machine. No hosted control plane, no cloud account, no telemetry sent upstream.
- **Not a drop-in replacement for LangChain / CrewAI / AutoGen.** loam does not try to compete on agent-graph expressiveness or multi-agent orchestration primitives; those frameworks optimise for different shapes of work. loam optimises for long-lived, owner-centric, one-user workflows — and trades the "let me express any agent topology" power for a coherent primary-persona interface.
- **Not a plugin marketplace.** loam ships a plugin protocol; it does not ship a store, a curation pipeline, a payment rail, or a signing authority. The plugin ecosystem grows by convention and by in-repo examples, not by a platform play.
- **Not production-grade at v1.** The foundation is sealed and tested, but loam has been used by exactly one person (Luke) in exactly one workspace. The v1 release is "foundation-complete, early-access, Claude power users welcome," not "enterprise-ready."

---

## 3. Release-readiness checklist

### Features the core must ship with

Inventory of sealed components from `docs/rebuild/STATE.md` plus what's still in motion:

| Component | State | v1 launch-readiness |
|---|---|---|
| memory-system | Sealed 2026-04-18 | Production-ready. Some follow-ons non-blocking (real scope adapter already wired, observability-aggregator already wired). Stress test at 250k edges is a nice-to-have, not a blocker. |
| scope-of-work primitive | Sealed 2026-04-18 | Production-ready. |
| primary-persona layer | Sealed 2026-04-18 | Production-ready. |
| objective-tracker | Sealed 2026-04-18 | Production-ready. |
| session-resilient orchestrator | Sealed 2026-04-19 | Production-ready. |
| graceful-degradation | Sealed 2026-04-19 | Production-ready. |
| observability-aggregator | Sealed 2026-04-19 | Production-ready. |
| self-upgrade framework | Sealed 2026-04-19 | Production-ready. |
| safety-layer | Sealed 2026-04-19 | Production-ready. |
| reversibility-primitive | Sealed 2026-04-20 | Production-ready. |
| cost-governance | Sealed 2026-04-20 | Production-ready. |
| self-correction | Sealed 2026-04-20 | Production-ready. |
| workspace-bootstrap | Sealed 2026-04-20 | Production-ready (the composition engine — this is what makes v1 installable at all). |
| telegram-interface | Sealed (amendment-complete) | Production-ready; optional channel. |
| hands-off-lifecycle | Sealed + multiple amendments (currently at amendment #22+) | Production-ready; several amendments since 2026-04-22 are stabilising this layer. |

**Critical gaps that must close before v1 ships:**

1. **loam rename landed and stable.** Per `loam-rename-migration-plan.md`: Tier 1 (brand + package prefix + paths + launchd + OTel + CLI) must be shipped; Tier 2 (dormancy rename — the one strong component rename) is the owner's call but should land if it's going to land, because doing it post-v1 creates a visible breaking change. Tier 3 is nice-to-have.
2. **Unified `loam` CLI.** Today there's no top-level CLI — `pos-amend` is a dev-tool, not a user-facing command. `loam init`, `loam status`, `loam scope new`, `loam plot create`, `loam amend` must exist as a coherent CLI surface.
3. **`loam init` scaffolds a working workspace.** Today there's a first-run scaffold that assumes an existing checkout. A user who `pip install`s and runs `loam init ~/my-workspace` must get a workspace that starts a Claude Code session cleanly — with a primary persona template they can edit, with `~/.loam/` populated, with the launchd supervisor installed on macOS. This is the single biggest installation-UX blocker.
4. **A shipped primary-persona template.** The spec explicitly forbids pOS core shipping persona content. But loam ships a *template* (`example-persona` per the loader's enforcement path) that the user fills in. That template must be designed and shipped — not as a mandatory persona but as a starting-point. Without it, `loam init` lands the user in "your workspace requires a primary persona to start a session" with no guidance. Per the loader's rules, `example-persona` is permitted as a reserved placeholder handle.
5. **Cross-platform story, scoped honestly.** Today loam is macOS-only (launchd). Linux and Windows are explicit non-goals at v1 per the §2.5 violation that surfaced Linux code and was removed. Launch messaging must say "macOS-only at v1; Linux coming via community" or similar — not "works on Mac/Linux/Windows" which overpromises.

**Plugins that must ship at v1**

- **Dev/SDLC plugin (required).** Per FUTURE_IDEAS Idea 3, this is "the first and most-needed plugin because building pOS itself uses it." More important for launch: it's the visible proof that the plugin protocol (B18/B19 seal) works on a real plugin, not just a synthetic test fixture. It's also the vehicle that carries ODD into users' own projects — the plugin is what makes loam's ODD pitch concrete for developers. Without it, loam is foundation-only and the plugin ecosystem claim is aspirational. With it, loam is foundation-plus-one-real-plugin-that-proves-the-ecosystem.

- **No other plugins at v1.** FUTURE_IDEAS lists eight plugin candidates and explicitly names "plugin selection discipline: do not ship all eight. Pick the two or three that maximise early pOS-v2 value." At launch, one plugin (Dev/SDLC) is enough — it proves the protocol, ships a useful vertical, and keeps the surface area small enough to document and maintain. Shipping two plugins at v1 risks diluting the message and stretching maintenance thin. Additional plugins come in v1.1, v1.2, etc., and/or from the community.

### Documentation completeness

| Doc | Purpose | Status | Required for v1? |
|---|---|---|---|
| `README.md` | 30-second pitch + install + first-session | exists; needs complete rewrite around the loam brand + one-sentence pitch + QUICKSTART | **Yes** |
| `QUICKSTART.md` | 10-minute "install → first session → first scope" walkthrough | does not exist | **Yes** |
| `docs/architecture.md` | One-page diagram + component tour | partial (per-component docs exist; need synthesis) | **Yes** |
| `docs/odd-methodology.md` | ODD spec | exists | **Yes** (rename from odd-methodology.md stays; odd-in-pos.md renames to odd-in-loam.md) |
| `docs/odd-in-loam.md` | Worked examples of ODD inside loam | exists as odd-in-pos.md; renames | **Yes** |
| `CONTRIBUTING.md` | How to propose + author a contribution | does not exist | **Yes** |
| `docs/plugin-author-guide.md` | How to author a plugin against the B18 protocol | does not exist | **Yes** (the pitch depends on this being credible) |
| `docs/api-reference/` | Per-component API | scattered across component docs | **v1.1 acceptable** — link to per-component READMEs at v1 |
| `CHANGELOG.md` | Release notes | does not exist | **Yes** (even a minimal one) |
| `docs/cookbook/` | Recipes: "how do I do X with loam" | does not exist | **v1.1 acceptable** — but 3-5 recipes in the launch post would be high-value |
| `docs/faq.md` | Expected reviewer objections answered | does not exist | **Yes** (pre-empts the "why not just use Claude Code directly" etc. questions) |
| `SECURITY.md` | Vulnerability reporting | does not exist | **Yes** |

### Installation / onboarding

The gold-standard install flow:

```
pip install loam
loam init ~/my-workspace
cd ~/my-workspace
# edit personas/primary/prompt.md to describe yourself
claude  # or open the workspace in Claude Code GUI
# primary persona greets you
```

Five commands to first session. Anything more is a loss. Constraints that must hold:

- `pip install loam` pulls every production runtime dep (Python 3.13, graphiti-core pin, pyee, pydantic, asyncio extensions, pytest only as extras).
- `loam init` scaffolds the workspace with `~/.loam/` populated, launchd supervisor installed, example primary-persona template, a `docs/` folder pre-seeded with a workspace-local CLAUDE.md pointing at the loam defaults.
- The first session explicitly says "your primary persona is a placeholder; edit `personas/primary/prompt.md` to personalise." It does not silently use a stub.
- Opt-in: Telegram channel, self-upgrade auto-apply, memory retention defaults. Surface these in onboarding as numbered choices; default each to a safe value; user dismisses.

### Testing + CI

A contributor landing on the repo should see: green CI badges, `pytest` running cleanly, the `pos-amend apply --dry-run` tool mechanising the amendment discipline. Today the testing and amendment machinery exists; CI does not.

Minimum viable CI for v1:
- GitHub Actions workflow (`test.yml`) running full pytest on every PR and main push; macOS-latest and ubuntu-latest (even though loam is macOS-only at runtime, the test suite should run on Linux too — most pytest targets are platform-neutral).
- Amendment-seal validation: a workflow that runs the seal-diff check on PRs touching `docs/rebuild/plans/<amendment>.yaml` files.
- Ruff + mypy as separate workflow jobs, non-blocking at launch, progressively blocking over v1.x.
- Coverage report surfaced but not gated — aiming above 80% (memory-system is already at 100% for acceptance tests by ODD's test-to-criterion rule).

### Security + safety

loam is a harness that enables autonomous agents on a user's machine with access to their filesystem, their Claude account, and potentially external services. Security is not optional.

Launch security posture:
- **Safety layer is load-bearing.** The kill-switch (scope/session/system), the always-ask list, the dangerous-op gate, the approval-binds-to-structural-hash semantics — these are not nice-to-haves. They are the reason a user can trust autonomous operation. The launch messaging must lean on this.
- **SECURITY.md declares the reporting surface.** A GitHub Security Advisories workflow + an email address (security@<domain> or Luke's) for coordinated disclosure. 90-day coordinated-disclosure policy.
- **No user data leaves the machine by default.** Observability is local (DuckDB + local JSONL); memory is local (Kuzu); no telemetry to any server. Launch messaging explicitly says this. Opt-in telemetry *can* be a future feature, but not at v1.
- **Known sharp edges named publicly.** The workspace-slug collision hazard (Idea 9) is real — two workspaces with the same basename boot each other out silently. At v1 the messaging says "run one loam workspace per basename" with a known-limitation link; the collision detection component lands in v1.1.
- **Plugin trust model v0.** v1 ships no formal plugin signing. Plugins are installed from the user's filesystem or from GitHub URLs via pip. The trust model is "the user is installing their own plugin or a plugin they've audited." Launch messaging must say this. v1.1+ introduces signed-plugin conventions.

### Observability defaults

Out of the box, a new user sees:
- A `~/.loam/logs/` directory with structured JSON logs per component.
- An `~/.loam/observability/` DuckDB file with all OTel spans accumulated locally.
- A `loam status` command that reports: orchestrator health, memory staging queue depth, recent failed scopes, last self-correction event, cost ledger summary, kill-switch state.
- A natural-language query over the observability store via the primary persona: *"why did my last scope fail?"* answers by querying the span store, not by guessing.

### Polish / rough edges to smooth pre-launch

1. **The `pos-v2` → `loam` rename must be 100% done before any external messaging.** Not 90%. Reviewers will screenshot inconsistencies.
2. **`~/.pos/` → `~/.loam/` migration script** for existing users — scoped tight, tested, and opt-in-by-prompt rather than silent.
3. **The foundation-audit's RED findings must be GREEN or documented as known-and-accepted.** The 2026-04-22 audit surfaced three RED components (workspace-bootstrap, hands-off-lifecycle, session-resilient-orchestrator); subsequent amendments have been addressing these. Pre-launch: run a fresh audit, show GREEN majority in the README.
4. **Error messages.** Audit every raise/log for a user-facing first-person voice. "Error: scope_of_work_budget_exhausted" is fine for a dev; "I hit the budget ceiling on this scope — the scope paused. Run `loam scope resume <id>` to request an extension" is what a launch-ready CLI says.
5. **First-session narration.** The single sentence on first-run scaffold is good. The second-session greeting from the primary persona needs to be shaped — "Welcome back. Three scopes running, one needs your attention." Today, that's persona-implementation-dependent; loam should ship a template that does this consistently.
6. **`loam doctor`** — a diagnostic command that checks install integrity, dependency versions, launchd supervisor health, memory service, and surfaces any known-bad-config. Missing from today's surface; first thing reviewers run when something's broken.

---

## 4. Repository hygiene

### LICENSE

**Recommendation: Apache-2.0.**

Rationale (shortest version):

- **MIT** is maximally permissive but provides no explicit patent grant. For an AI-tooling project where the methodology (ODD) could plausibly be patented by a bad actor who files ahead of the project, a permissive-without-patent-grant license is a mild risk.
- **Apache-2.0** is permissive, includes an explicit patent grant (license to use patented methods that the contributor holds, revocable on patent litigation), includes a NOTICE mechanism for attribution, and is the default license for the majority of the Python / AI-tooling ecosystem loam sits next to (LangChain, LlamaIndex, Anthropic SDK, MCP SDK are all Apache-2.0 or MIT).
- **AGPL-3.0** is copyleft with a network-use clause — it forces anyone running a modified loam as a service to open-source their modifications. This would protect loam from closed-source forks being offered as a competing hosted service, but it also (a) kills adoption inside corporations that refuse AGPL on principle, (b) creates friction for every plugin author who has to think about license compatibility, (c) is philosophically misaligned with the "seed for users to grow their own" framing — copyleft is a leash, and loam's pitch is agency.
- **MPL-2.0** is a middle-ground file-scoped copyleft. Interesting theoretically; almost nobody picks it in 2026 for new projects; wrong ecosystem signal.

Apache-2.0 is the default recommendation. If Luke has specific ideological reasons to prefer one of the alternatives, they override.

### README.md — structure and opening paragraphs

The README is the 30-second pitch. Structure (priority order):

1. **H1 + tagline** — one line.
2. **Opening two paragraphs** — what loam is, why it exists.
3. **Status** — foundation-complete, early-access, macOS-only at v1.
4. **Quickstart** — five commands (`pip install loam`; `loam init`; `cd workspace`; edit persona; open in Claude Code). Links to full QUICKSTART.md.
5. **Differentiators** — four bullets: Claude-attached, outcome-governed, safety-first, plugin-extensible.
6. **Architecture diagram** — one ASCII or SVG diagram.
7. **Documentation links** — architecture.md, odd-methodology.md, plugin-author-guide.md, CONTRIBUTING.md.
8. **Community** — where to ask questions (GitHub Discussions initially; Discord later).
9. **License** — Apache-2.0.

Skeleton for the opening:

```markdown
# loam

**The substrate your Claude agent grows in.**

loam is a Python-native harness for Claude-attached autonomous workflows.
A long-running orchestrator, semantic memory, three-gate safety chain,
and an ODD-driven methodology compose into a foundation that runs
quietly beneath every Claude Code session — so work outlives the session,
scopes stay bounded, and your primary persona keeps context you no longer
have to carry.

Opinionated where it matters (Claude-only, outcome-governed, safety-first)
and extensible where it counts (plugin protocol, primary-persona
contract). A seed from which you grow your own AI collaborator, not a
finished product you adopt.
```

### CONTRIBUTING.md

What it must establish:
- **Who can contribute.** Anyone. Reasonable-person standard. Anthropic employees welcome (some of the pitch is about composition with Claude's roadmap).
- **How work is structured.** Every non-trivial change is ODD-shaped: objective + constraints + acceptance criteria. The five-gate chain (research plan → research → proposal → brief → build) applies to new components and significant amendments; small fixes use a short plan doc only.
- **Review process.** PRs are reviewed against ODD compliance (tests map 1:1 to criteria; no method-in-acceptance; no silent exception branches; no code for cases no AC names). The repo-owner (Luke) is the final reviewer at v1; a contributors-group forms over v1.x.
- **Plan-before-code discipline.** Plans live at `docs/rebuild/plans/<name>.md` (to migrate to `docs/plans/` post-launch for clarity). PRs without a plan doc get nudged back.
- **Amendment-seal discipline.** Changes to sealed components go through the amendment machinery; `pos-amend apply --dry-run` (renamed: `loam amend apply --dry-run`) must exit 0.
- **Testing expectation.** Tests are test-shaped per criterion; criterion IDs appear in test function names (`test_A7_*`). New criteria added during build are re-extended up the chain, not buried as branches.
- **Code style.** Python 3.13; ruff/mypy configs in-tree; file-length judgment call with documented rationale.
- **Commit messages.** Cite acceptance-criterion IDs ("A7: kill-switch bounded-time"; "B18: extension-protocol verification"). Commit prose is the builder's call; the dispatch prompt does not prescribe it.

### CODE_OF_CONDUCT.md

**Recommendation: Contributor Covenant v2.1, unmodified.** Industry-standard, well-understood, community-accepted. No need to reinvent. Attach Luke's email as the reporting address (or a dedicated conduct@ alias).

### SECURITY.md

Must answer: *who do I email if I find a vulnerability, and what happens next?*

Minimum contents:
- **Supported versions.** v1.x. (Before v1: "no supported versions; do not deploy to production.")
- **Reporting.** Email security@<domain> (or GitHub Security Advisories). 72-hour acknowledgement target.
- **Disclosure timeline.** 90-day coordinated disclosure. Advisory published on fix-release or at 90 days, whichever first.
- **Scope.** What counts as a security vulnerability (safety-layer bypass, sandbox escape, unauthorised external-funds commitment, data leak through memory or observability). What doesn't (dependency CVEs that don't affect loam's usage — triaged, not treated as incident).

### Issue templates, PR templates, labels

- **Issue templates:** three — bug report, feature request, question. All three nudge toward ODD shape ("what outcome did you expect / observe") without forcing jargon.
- **PR template:** short — "what does this change (outcome), how is it verified (test / criterion), what's the amendment manifest (if touching sealed)."
- **Labels:** `needs-research`, `needs-proposal`, `needs-review`, `needs-amendment-seal`, `good-first-issue`, `help-wanted`, `bug`, `enhancement`, `documentation`, `breaking-change`, `plugin`, `component:<name>`. Per-component labels help triage.

### .github/workflows/

- `test.yml` — pytest on macos-latest + ubuntu-latest, every push and PR.
- `lint.yml` — ruff + mypy, non-blocking initially.
- `amendment-seal.yml` — runs `loam amend apply --dry-run` on any PR touching amendment manifests.
- `coverage.yml` — uploads coverage report.
- `release.yml` — manual-trigger release workflow that tags + pushes to PyPI + drafts a GitHub release.

---

## 5. Positioning and messaging

### Competitive landscape

Where loam sits and how it differs:

- **Claude Code.** Not a competitor; loam runs *inside* Claude Code via SessionStart hooks. Pitch: "Claude Code gives you the interactive UX; loam gives it persistence, scopes, safety, plugins."
- **Claude Agent SDK.** loam is built on it, composes with it. Plugin authors may touch the SDK directly; most users don't.
- **LangChain / LangGraph.** Most similar-shaped project. Differentiators: loam is Claude-only (correctness trade vs. LangChain's flexibility trade); loam has built-in ODD methodology; loam has a first-class primary-persona layer; loam has sealed-foundation discipline. Positioning: "what you reach for when LangChain's flexibility is actually a cost."
- **CrewAI / AutoGen.** Multi-agent orchestration. Different target — crews express "agent A talks to B, B dispatches to C." loam is owner-centric: "one user, one primary persona, structured work surfaces."
- **MCP servers.** Protocol for giving LLMs tools; loam consumes MCP servers (Google Calendar, Drive) as integrations. Not competing; composing.
- **Aider / Cline / Cursor.** AI-coding tools — closest to the Dev/SDLC plugin (not loam itself). Messaging: "Dev/SDLC complements an IDE-shaped tool; loam operates at the session + orchestration layer."
- **Dust / Zapier AI.** No-code agent platforms. Different audience (biz users). Not competition.
- **SWE-agent / similar research projects.** Closest-in-ethos to Dev/SDLC's eventual capabilities; messaging: "inspired by their autonomy-first posture but grounded in ODD rather than end-task-only evaluation."

### Differentiators (the four-word pitch expanded)

1. **Claude-attached, not model-agnostic.** loam assumes Claude and exploits Claude's specific primitives (sub-agents, SessionStart hooks, skills, MCP, compaction-survival). The "Claude-leverage-first" design lens is the rule, not a feature.

2. **Outcome-governed, via ODD.** Every unit of delegated work is authored as an outcome, bounded by constraints, verified by deterministic acceptance criteria. This is structurally enforced; the amendment-seal tooling mechanises it. No other harness ships with a methodology as the load-bearing spine.

3. **Safety-first, structurally.** Three-gate chain (always-ask + dangerous-op + kill-switch). Reversibility class per action. Cost ceilings per scope. Structural-over-advisory preference everywhere. The safety story is the reason a non-technical user could, eventually, trust autonomous operation.

4. **Plugin-extensible, without core amendment.** The B18/B19 proven protocol — Phase 4+ contributions register without touching the sealed foundation. Plugins are first-class, not duct-taped.

### Messaging traps to counter

- **"Why not just use Claude Code directly?"** Claude Code is a session; loam runs *between* sessions. Lead: persistence + orchestration + plugins.
- **"Why Claude-only? That's limiting."** Vendor-neutrality is a correctness tax. Claude has specific primitives (sub-agents, hooks, compaction) loam exploits. Answer: we made the bet; the bet is the feature.
- **"This looks like another LangChain."** Three answers: methodology is built in (not optional); primary-persona is first-class (not a primitive you assemble); sealed-foundation discipline (built on a frozen base, not a moving target).
- **"Too much methodology. I just want the code."** ODD is inward-facing — for authors, not users. Users never see "acceptance criterion"; the primary persona handles natural-language translation.
- **"What if Anthropic breaks the SDK?"** Self-upgrade framework clause (e): breaking changes surfaced with explicit migration paths, not silently absorbed.
- **"Why should I trust my filesystem / Claude account to this?"** Safety-layer: three gates, reversibility, everything local by default. Structural trust, not marketing.
- **"Non-technical users, really?"** Not at v1. Undersell. It's a v2+ aspiration; say so.
- **"This is just Luke's personal tool that he open-sourced."** Partly true, and fine — Aider, Cursor, Obsidian all started that way. The methodology generalises; link to ODD docs.

### Tagline / hero candidates

1. **"The substrate your Claude agent grows in."** — metaphor-forward, matches the rename brainstorm, quietly invokes the seed theme. Best for website hero.
2. **"A Claude-attached harness for autonomous work."** — plain-language, precise, safe for README H1. Good if the tagline wants to be quickly-parseable by reviewers who don't want metaphors.
3. **"Outcome-governed autonomy, built on Claude."** — methodology-forward, names ODD without naming it, signals to the audience that appreciates that framing.
4. **"Where your Claude work outlives the session."** — temporal-first, emphasises the single biggest functional differentiator (persistence). Good for a launch blog post headline.
5. **"Seed it. Grow it. Ship it."** — three-word rhythm, metaphor-consistent, punchy. Good for merch / conference-talk slide but weak as a functional pitch.

**Recommendation: #1 for the website hero; #2 for the README tagline; #4 for the launch blog post.** Carrying three slightly-different framings across surfaces is fine — the audience each surface reaches is different, and the core message is consistent across all three.

---

## 6. Launch strategy

### Pre-launch (silent)

Audience: 10-30 individuals stress-testing the pitch before it goes public. Duration: 4-6 weeks. Format: small Discord / private GitHub org / email thread.

Targets:

1. **Anthropic dev-rel team** (Claude Code team, MCP team). loam is downstream of their work and complimentary; their awareness is valuable. Outcome: early-access walkthrough, positioning feedback, possibly a joint blog post at launch.
2. **Known Claude Code power-users** — 5-10 names identifiable via public Twitter/X threads and Anthropic-repo stars. Install v1 early-access, report on install UX; some become early advocates.
3. **Agent-framework adjacent builders** — authors of LangChain, CrewAI, AutoGen, swe-agent, Aider, Cline. Peers, not adversaries. Respectful outreach. Most won't engage; the one or two who do matter.
4. **3-5 specific writers** — Simon Willison, Swyx / Latent Space, a couple of substack-native AI writers. Awareness, not amplification; amplification comes at launch-proper.
5. **PKM-adjacent crowd** — Obsidian plugin authors, Logseq community. loam composes with these (via future plugins); "substrate you cultivate" framing resonates with PKM values.

### Soft launch

First public presence. Not a megaphone event; a "the project exists now and you can find it" event.

Sequence (over 2-3 weeks):

1. **GitHub repo goes public** (`ivers-corp-loam` or `lukeivers/loam` — naming is Luke's call). Repo is clean: README rewritten, CONTRIBUTING.md, LICENSE, SECURITY.md, CI green, one recent release tagged `v1.0.0`.
2. **A personal website or project page** — `loam.dev` or similar — lands with the hero, the three-paragraph description, a link to the repo, a "sign up for launch updates" email capture (for the launch-proper announcement).
3. **A Twitter/X thread from Luke's account** — 8-12 tweets, telling the story: why it exists, what's different, what the plugin protocol proves, a link to the repo. No aggressive promotion; a founder sharing a project that's ready for eyes.
4. **A Show HN post** — title tested first ("Show HN: loam — a Claude-attached harness for autonomous work" or similar). Pinned to the top of the website for the HN period. Launches on a Tuesday/Wednesday morning Pacific. First comments in the HN thread are Luke answering questions thoughtfully (not Luke reading canned responses).
5. **An Anthropic Discord / community post** (if the community has a "showcase" channel; if not, whatever the contextually-right equivalent is).

Duration: soft-launch lasts 2-3 weeks from the repo-goes-public moment. Metric of "soft launch is complete": the first round of feedback has come in, any critical bugs from early adopters are fixed, the README has been iterated based on what confused people.

### Launch proper

Target: 3-6 weeks after soft-launch. The goal is to convert the early-awareness into sustained engagement.

Options (probably pick two, not all):

1. **Launch blog post.** Long-form, 3000-5000 words. Titled something like "Introducing loam: outcome-governed autonomy on Claude." Structure: the problem, the insight (ODD), the architecture, the plugin protocol, the v1 capabilities, the roadmap. Published on Luke's blog, cross-posted on dev.to, referenced in a Hacker News Ask HN or Show HN update.

2. **A Product Hunt launch.** Possibly worth doing, but the PH audience skews less-technical than loam's launch audience, and the dynamics of that ranking system reward "startup-shape" projects. Marginal call. **Recommendation: skip PH at v1; reconsider at v1.x when the non-technical plugin story is real.**

3. **A conference talk.** If AI Engineer Summit / LangChain conference / similar falls in the launch window, submit. A 25-minute talk telling the "why I built loam" story is a high-leverage artefact; the recording gets shared for months afterward. **Recommendation: author the talk regardless; submit if a fit conference is timed right; otherwise record it as a YouTube video and publish.**

4. **A "how we built it" companion post.** This is the post for the builder audience — methodology-forward, architecture-forward, honest about what went wrong during the rebuild. Published 4-6 weeks after the launch post, when the launch post's momentum is fading and a follow-up keeps the conversation going.

5. **Documentation site launch.** `docs.loam.dev` or `docs/` on `loam.dev`. Hosted docs are more discoverable than in-repo docs; they also signal "real project." Use MkDocs or Docusaurus. **Recommendation: ship at launch-proper; not needed at soft-launch.**

### Content marketing

**Launch blog post outline** (~2500-3500 words total): problem (AI-tooling usability gap, correctness vs flexibility); insight (ODD summarised); architecture (sealed foundation + plugin protocol + primary persona + safety layer, with diagrams); what v1 ships; why Claude-only (non-goal as feature); roadmap bullet; get-started; thanks.

**Follow-up "how we built it" post** — methodology-forward: why rebuild from v1, the five-gate chain, sealed-components discipline, amendments, honest retrospective on what went wrong (§2.5 violations, RED audit findings, recovery).

Posture: **launch post + how-we-built-it post as a paired release; decide on further instalments based on engagement.** A planned series under-delivers; reactive preserves optionality.

### Community seeding

**Minimum viable community space at launch: GitHub Discussions.** Not Discord yet, not Slack. Reasons:

- Discussions are in-repo, searchable, indexable by Google, archived permanently. They're the closest-to-asynchronous surface for a small-to-medium community.
- Discord/Slack add operational overhead (moderation, channel structure, continuous presence) that at loam's launch scale is cost not yet earned.
- If Discussions fills up, Discord becomes warranted. That's the upgrade path.

At v1.x when the community has 100+ active participants, spin up a Discord server — probably on the Anthropic community Discord's loam channel rather than a freestanding server initially.

---

## 7. Engagement + retention

### What post-launch engagement looks like

**Issue response cadence:** target 48-hour first-response on issues during v1.x. Not 48-hour-resolve; 48-hour-acknowledge. Even "I've seen this; will look at it next week" is a valid response.

**Release cadence:** v1.x minor releases every 4-8 weeks. Patch releases (v1.0.1, v1.0.2) as needed for critical bugs. v2 is a year-plus away.

**Roadmap transparency:** `docs/roadmap.md` in-repo, updated monthly. Lists near-term (next release), medium-term (next 3-6 months), and long-term (12+ months). Explicitly says "aspirational, not commitments."

### Plugin ecosystem

Authoring flow: read `docs/plugin-author-guide.md`; subclass `Contribution`; declare metadata (name, phase, after/before); implement `contribute(host)`; register in workspace's `bootstrap.yaml`. Follow ODD for the plugin's own components (five-gate chain optional but encouraged).

DX targets:
- **Hot-reload in development.** v1.1 target; v1 requires session restart.
- **`loam plugin create <name>`** — scaffolds plugin repo (pyproject.toml, contribution.py, tests, plans, README). Essential for the first 100 plugin authors.
- **`loam.testing.PluginHarness`** — B18's synthetic-contribution fixture exposed as a public primitive for plugin test suites.

Marketplace posture:
- **v1: no marketplace.** Plugins live in their own GitHub repos; `pip install <plugin-name>` + enable in `bootstrap.yaml`.
- **v1.x: community-curated list** at `docs/ecosystem.md` or a website page. Directory, not platform.
- **v2+: maybe a marketplace primitive** (signing, registry, curation) only if ecosystem scale warrants. Premature marketplace is worse than none.

### Documentation as an engagement surface

- **Tutorials.** "Your first loam workspace in 10 minutes." "Writing your primary persona." "Installing the Dev/SDLC plugin and shipping your first scope with ODD."
- **Cookbook.** 10-15 short recipes: "how do I schedule a recurring task," "how do I have the primary persona email me," "how do I integrate with my Obsidian vault (via MCP)," "how do I add cost ceilings per scope."
- **Examples repo.** `lukeivers/loam-examples` or `loamharness/examples` — full worked examples of plugins, personas, workspace configurations. Lower barrier to entry than reading the docs cold.
- **Video walkthroughs.** Two or three 5-15 minute videos. Not a whole channel — just "here's what a loam session looks like" and "here's the plugin protocol in practice."

### Community health signals

Watch:
- **Stars / forks.** Vanity metrics, but stars-per-week after week 3 matters more than week-1 HN spike.
- **Active issue authors (non-Luke).** More important than total issues.
- **PR cadence.** A PR every 2 weeks from anyone-other-than-Luke is a healthy signal at v1.x scale.
- **Plugin authoring.** The single best signal of ecosystem traction. First third-party plugin = first validation of the protocol.
- **Community contributors vs core-team commits.** Ratio creeping toward 30-70 or better by month 6 is healthy; staying at 5-95 is a bus-factor risk.

Don't over-read:
- **HN day-of rank.** Noise.
- **Twitter follower growth.** Not the same population as loam's audience.
- **Reddit /r/MachineLearning mentions.** Different audience; loam is infra, not research.

---

## 8. Success criteria + risks

### What "the launch worked" looks like

**1 month:**
- 500-2000 GitHub stars (order-of-magnitude; the exact number depends on HN dynamics).
- 10-30 issues opened by non-Luke users, with at least half of them being substantive (bug reports, feature requests, config questions) rather than spam.
- 1-3 PRs from non-Luke contributors (most will be small — typo fixes, README nits — and that's fine; they're the entry point).
- 50-200 `pip install loam` events (measurable via PyPI stats).
- 1-5 blog posts or Twitter threads from non-Luke users describing their loam experience.

**3 months:**
- First third-party plugin announced. If this hasn't happened, the plugin story hasn't landed; rework the plugin-author-guide.
- 2000-10000 stars.
- 5-20 active contributors (have authored at least one PR).
- 100-500 installs/week.
- The first plugin that isn't from Luke or a close collaborator — this is the milestone that says the ecosystem is real.
- A non-Luke maintainer appointed for a specific area (docs, testing, platform support).

**6 months:**
- Second and third third-party plugins.
- A stable release cadence (v1.1, v1.2 shipped).
- A conference talk delivered (by Luke or a community member).
- Stars plateau becomes an engaged-user base — PyPI weekly installs > stars-growth-per-week indicates product-used-not-just-saved.
- The Dev/SDLC plugin is in daily use by at least 5-10 developers other than Luke.

### Failure modes

1. **Niche adoption.** loam attracts a small, devoted following of 50-200 users who love it, but no broader traction. Revenue to Luke: zero (open-source; fine), visibility: low. Mitigation: this is the default outcome for most open-source projects; the question is whether that small following is the right people. If 50 people are agent-framework builders who integrate loam's ideas into their own work, niche adoption is successful. If 50 people are hobbyists who don't contribute back, the project dies slowly.

2. **Negative HN reception.** "Yet another agent framework." "Why Claude-only?" "This is just Luke's personal OS." The HN comment section turns hostile; the project gets a reputation as over-engineered or naïve. Mitigation: the "not for everyone" framing in the positioning doc inoculates somewhat. The ODD methodology is defensible on first-principles; the Claude-only decision is explicit; the sealed-foundation discipline is demonstrable. A bad HN reception hurts for two weeks and then fades; the project survives on sustained engagement from the right users.

3. **Tooling-bloat criticism.** "The Python ecosystem doesn't need another framework." Legitimate concern. Mitigation: the pitch is not "another framework" — it's "a harness with a methodology." Lead with methodology; the framework is the mechanism, not the pitch.

4. **AI-fatigue backlash.** By late 2026 / early 2027, the AI-tooling space is crowded and some audiences are exhausted. Launch timing matters. Mitigation: position loam as "the serious, disciplined, opinionated alternative" rather than "the next exciting thing." Fatigue hurts excitement-seekers; it helps signal-seekers.

5. **Misalignment with Anthropic's direction.** Anthropic ships a feature that obsoletes a loam primitive (e.g., native session-resilience, native primary-persona contract, native ODD enforcement). Mitigation: the design lenses are structurally compositional — "lean on Claude primitives; compose on top." If Anthropic ships the primitive, loam's composition advantage doesn't disappear; loam now composes on a more-capable base. The risk is reduced by being Claude-attached rather than Claude-competing.

6. **Dependency abandonment.** graphiti-core loses active maintenance; pyee has a breaking-change update; Claude SDK deprecates something loam depends on. Mitigation: vendor the deps where reasonable (loam already pins graphiti-core + applies local patches); the self-upgrade framework's clause (e) is the migration-path discipline.

7. **Maintainer burnout.** Luke, one person, maintains the foundation. Personal circumstances change (the user's health and life-circumstances are named in the global CLAUDE.md as design inputs; they are also realistic maintenance-capacity inputs). Mitigation: see §8 Governance risks.

### Governance risks

**Bus-factor mitigation.** At v1, the bus factor is 1 (Luke). At v1.x:
- Identify 2-3 trusted contributors and formalise them as maintainers (can merge PRs, can triage issues).
- Document the amendment-seal discipline so that any maintainer can apply the ODD process unaided.
- Publish the roadmap publicly; if Luke is hit by a bus, the roadmap is the continuity surface.
- Ensure the critical components (memory-system, orchestrator, safety-layer) have multiple people who understand them — via code reviews, via recorded walkthroughs, via the bundled docs.

**Governance model.** At v1: Luke is the benevolent dictator. At v1.x, move toward a small steering committee (3-5 people) for major decisions; Luke retains veto on foundation-breaking changes. At v2+ (if the community scales), consider a foundation or a more formal governance structure. **Recommendation: don't over-engineer governance at launch;** most projects that do end up dissolving their governance under usage weight anyway.

### Legal / IP risks

- **Dependency licenses.** Audit pre-launch:
  - `graphiti-core`: Apache-2.0. OK.
  - `pyee`: MIT. OK.
  - `pydantic`: MIT. OK.
  - `duckdb`: MIT. OK.
  - `kuzu`: MIT. OK.
  - `anthropic` (SDK): MIT. OK.
  - Others: verify each. No GPL/AGPL deps (would contaminate loam's Apache-2.0).
- **Anthropic branding.** loam uses "Claude" in its marketing and docs; that's allowed under Anthropic's trademark guidelines for descriptive use ("works with Claude"), not for confusable use ("Claude OS"). Pre-launch: read Anthropic's trademark policy and ensure compliance; probably worth a courtesy email to their legal team saying what we're doing.
- **Name collision.** `loam` — unclear commercial rights. Loam Bio exists (ag biotech). Check trademark databases (USPTO, EU, UK IPO) pre-launch; if a collision exists in software, either file a trademark or fall back to a secondary name. **Action: trademark search before public launch.**
- **Patent risks.** ODD as a methodology is not novel enough to patent (outcome-based delegation is prior art going back decades). The specific combination of primitives in loam's foundation might be novel, but patenting them defensively would be expensive and off-brand. Apache-2.0's patent clause provides adequate community protection.

---

## 9. Open-source AI-tooling specifics

### Lessons from similar recent launches

- **LangChain** (late 2022). Exploded because of a novel primitive (chain-of-LLM-calls) released into a hungry market; paid for it later with technical debt and fragmenting API surface. **Lesson: ship early but seal the foundation.** loam's sealed-component discipline is the explicit antidote.
- **LlamaIndex** (late 2022). Narrower initial focus (RAG), better API stability. **Lesson: narrow is a feature.** v1 is foundation + Dev/SDLC plugin, not foundation + six plugins.
- **CrewAI** (2024). Strong opinionated metaphor worked well early, became limiting when workflows didn't fit the crew shape. **Lesson: opinions are assets until they become cages.** loam's plugin protocol is the escape hatch.
- **AutoGen** (Microsoft, 2023). Credible research backing, strong examples, muddled positioning against Microsoft's own counterparts. **Lesson: corporate backing is not a guarantee if positioning is muddled.** loam's independent, Luke-led positioning is simpler.
- **Aider** (2023). Laser-focused scope, high-quality execution, honest benchmarks, small-big engagement. **Lesson: the Dev/SDLC plugin should aspire to be Aider-shaped** — narrow, excellent, honest.
- **SWE-agent** (Princeton 2024). Strong benchmarks, limited real-world usage. **Lesson: benchmarks persuade; sustained usage requires product polish research projects don't prioritise.**
- **MCP** (Anthropic 2024). Clear spec; ecosystem grew slower than expected because most servers are Anthropic-built. **Lesson: a protocol alone is not an ecosystem.** loam ships plugins (Dev/SDLC) alongside the protocol.

### Anthropic-ecosystem positioning

loam composes with, does not replace, the Anthropic stack. Explicitly:

- **Built on the Claude Agent SDK.** Every agent dispatch inside loam is a Claude Agent SDK call. No custom model wrappers. Full compatibility with Claude updates.
- **Uses Claude Code primitives.** SessionStart hooks, sub-agents, skills, slash commands, background tasks, compaction-survival. loam's value-add is composition on top of these, not replacement of any of them.
- **MCP-compatible.** loam's plugins can consume MCP servers. loam does not publish MCP servers itself (at v1); that's a potential v1.x direction.
- **Respects Claude Max's cost model.** The memory-system amendment #8 explicitly routed LLM calls through the user's Claude Max subscription rather than a metered API key. This is a recurring pattern: where a user has a subscription, loam uses it.

Framing for messaging: **"loam is to Claude what rails was to ruby — not a replacement, not a competitor, but the opinionated application framework that makes the underlying runtime more productive for a specific kind of work."**

### Model-dependency storytelling

Claude-attached is a feature. The story:

1. **Vendor-neutral is expensive.** Supporting OpenAI + Anthropic + Gemini + local pays a correctness tax at every integration (prompt shapes, tool-use semantics, context sizes, safety defaults differ). Abstractions end up as lowest-common-denominator APIs.
2. **Claude has the right primitives** loam needs (sub-agents, SessionStart hooks, MCP, compaction-survival, Max subscription). Other models lack these or shape them differently.
3. **Anthropic's safety discipline aligns.** A different safety culture would require a different framework shape.
4. **Commitment signals investment.** "We picked Claude and exploited it" means Claude users get a better product; others know to look elsewhere. Clarity is a gift.
5. **The non-goal is the feature.** Multi-vendor is an explicit non-goal in spec v1.0. Naming it upfront builds trust.

README sentence: *"loam is Claude-attached, not Claude-compatible. This is a feature. We exploit Claude's specific primitives — sub-agents, SessionStart hooks, MCP, compaction-survival — instead of abstracting over a lowest-common-denominator model API. The trade-off is vendor lock-in to Claude; we think the correctness gain is worth it."*

---

## 10. Timeline and sequencing

### Rough timeline, today → public launch

- **Phase A (weeks 1-4)** — Rename completion (Tier 1 + maybe Tier 2 dormancy); Dev/SDLC plugin research plan + research dispatch; positioning doc; LICENSE/CONTRIBUTING/COC/SECURITY drafted.
- **Phase B (weeks 5-12)** — Dev/SDLC plugin proposal/brief/build via five-gate chain (largest pre-launch work); documentation quartet (README rewrite, QUICKSTART, architecture, plugin-author-guide, faq); CHANGELOG; CI workflows shipped.
- **Phase C (weeks 13-16)** — Polish: cross-platform story messaged; sharp edges addressed (slug-collision, `loam doctor`, error-message voice); foundation-audit re-run published; trademark search; domain registration; landing page; v1.0.0-rc tagged and tested on clean machine; walkthrough video.
- **Phase D (weeks 17-22)** — Silent pre-launch: 10-30 founder-circle reviews; iteration; Anthropic dev-rel contact; writer outreach; Twitter thread + HN title drafted.
- **Phase E (weeks 23-24)** — Soft launch: repo public; website live; Twitter thread; Show HN; Anthropic Discord; Discussions activated.
- **Phase F (weeks 25-30)** — Launch proper: long-form launch blog post; docs site live; conference talk (if timed); first community PR merged; v1.1 roadmap public.

Total: ~6-7 months (24-30 weeks). Optimistic but plausible given the foundation is built. Critical path is the Dev/SDLC plugin (Phase B); if that slips 4-8 weeks, everything shifts by the same amount.

### Critical path

1. **Rename completion** blocks everything (no public messaging with brand inconsistencies).
2. **Dev/SDLC plugin** blocks launch messaging (without it, the plugin-ecosystem claim is vaporware).
3. **Documentation set** (README, QUICKSTART, architecture, plugin-author-guide) blocks soft launch (without these, the first reviewer bounces).
4. **CI green** blocks any credible "production-ready foundation" messaging.

### Parallelizable

- LICENSE + CONTRIBUTING + CODE_OF_CONDUCT + SECURITY can be drafted in parallel with the Dev/SDLC plugin build.
- Positioning document can be drafted in parallel with rename migration.
- Website can be built in parallel with Phase B+C.
- Writer outreach happens during Phase D, orthogonal to tech work.

### Dependencies that must resolve before launch

- **Legal:** trademark search clear on `loam`; Anthropic trademark compliance confirmed.
- **Technical:** all RED foundation-audit findings resolved or documented as accepted.
- **Product:** Dev/SDLC plugin production-ready on the same quality bar as sealed foundational components.
- **Personal:** Luke has bandwidth for 2-4 weeks of intense launch activity (responding to HN, writing posts, handling first PRs). This is a non-trivial commitment; plan accordingly.

---

## 11. Specific next-action recommendations

### Next 30 days (ordered)

1. **Write `docs/positioning.md`.** One-sentence pitch, three-paragraph description, target personas, explicit non-goals, four-word differentiators. Everything else quotes from this document. (1-2 days, solo.)

2. **Finish the loam Tier 1 rename.** Package prefix, paths, env vars, launchd, OTel, CLI. One coordinated amendment. Dormancy rename (Tier 2) included if owner rules to rename. (1-2 weeks, dispatched as one amendment.)

3. **Adopt Apache-2.0; write `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1), `SECURITY.md`.** These four files signal "real project" to every drive-by reviewer. (2-3 days, solo.)

4. **Author the Dev/SDLC plugin research plan.** Follow the five-gate chain. The research plan is a short doc naming the questions research must answer. Dispatch research agent after owner approval. (1-2 days for plan; 1-2 weeks for research dispatch to return.)

5. **Trademark search for `loam`.** USPTO, EU IPO, UK IPO basic searches. If conflict found in software class, fall back to backup name (cultivar as the rename brainstorm's #2). (1 day, solo.)

6. **Register `loam.dev` (or similar domain).** Park with a placeholder page. (1 hour.)

7. **Set up GitHub Actions CI.** Three workflows: test (pytest on macos+ubuntu), lint (ruff+mypy non-blocking), amendment-seal (runs `loam amend apply --dry-run`). (1-2 days, solo or dispatched.)

8. **Identify and list the 10-30 silent-launch reviewers.** Real names, contact methods, what loam you want them to try, what feedback you want. (Half a day, solo.)

9. **Anthropic dev-rel outreach.** Email the Claude Code team announcing the project exists and asking for a 30-minute intro call when v1-rc is ready. (1 hour.)

10. **Start a `CHANGELOG.md`** and backfill the last 4-6 months of sealed components and amendments. (2-3 hours, solo.)

### Next 30-60 days (ordered)

1. **Dev/SDLC plugin proposal + brief.** Once research returns, author the proposal and brief for build dispatch. (2-3 days for proposal; 1-2 days for brief.)

2. **Dev/SDLC plugin build.** Single dispatch (or two if the scope warrants it). This is the largest piece of work. (3-6 weeks, dispatched.)

3. **README rewrite.** Lean on `docs/positioning.md`. Add QUICKSTART section, architecture diagram, differentiators. (2-3 days, solo.)

4. **`QUICKSTART.md`, `docs/architecture.md`, `docs/plugin-author-guide.md`, `docs/faq.md`.** The documentation quartet that turns "interesting project" into "a project I can use." (1-2 weeks, solo or split between Luke + a doc-focused contributor.)

5. **Build the landing page at `loam.dev`.** Static site (Hugo, Astro, or MkDocs). Hero + three-paragraph description + quickstart + link to repo + email capture for launch updates. (2-3 days.)

6. **Foundation-audit re-run.** Follow up on the 2026-04-22 RED findings and confirm all are resolved or explicitly accepted. Document results. (1-2 days.)

7. **Address the known sharp edges.** Workspace-slug collision detection (at least a warning if not a full solution), `loam doctor` command, error-message voice-pass. (1-2 weeks, dispatched.)

8. **Issue + PR templates, labels, GitHub project board for v1 launch.** (1 day.)

9. **Draft the launch blog post.** Doesn't publish yet; drafting now means it's ready when the launch date lands. (3-5 days of writing, iterated with reviewers.)

10. **Record a 5-minute "what is loam" video.** Screen capture of a loam session, narrated. Not polished; genuine. (1 day.)

### Pre-90-day gate items (must happen before public launch)

1. **All sealed components GREEN in the current foundation-audit.** No known RED findings. YELLOW findings documented and accepted.
2. **Dev/SDLC plugin sealed and shipping.** Pytest green. ODD-compliant. Used by Luke in daily work for at least 2 weeks before launch.
3. **Rename 100% complete.** No `pos-v2` strings in any user-facing doc, CLI, code path, or error message.
4. **Documentation quartet complete** (README, QUICKSTART, architecture, plugin-author-guide).
5. **CI green on main.** All three workflows passing.
6. **LICENSE + CONTRIBUTING + CODE_OF_CONDUCT + SECURITY** all in place.
7. **Trademark clear.** No blocking conflict.
8. **Anthropic dev-rel has been told.** Not "asked for permission" — told. Courtesy.
9. **Silent launch feedback iterated in.** At least 10 reviewers have tried loam and given feedback; the README / quickstart have been revised based on what confused them.
10. **Luke has a personal commitment scheduled for the launch period** — blocked time for responding to HN, handling first PRs, fixing first critical issues. Launch is non-trivial labour; don't underestimate it.

---

## 12. Open questions that require Luke's ruling

1. **Dormancy rename yes/no?** The rename-migration-plan's single strong Tier 2 candidate. Renaming `graceful-degradation/` to `dormancy/` is the one component-level metaphor rename worth doing — but it's also a breaking change for anyone already running pos-v2. Do it pre-launch (lands with v1.0.0) or skip? Recommendation: **do it pre-launch** because doing it post-launch is a bigger deal, but owner calls.

2. **License — Apache-2.0 confirmed, or one of the alternatives?** Recommendation is Apache-2.0. If there's a specific ideological or legal reason to prefer MIT, AGPL, or MPL, surface it now before LICENSE lands.

3. **CLI surface — unified `loam` CLI with subcommands, or a collection of binaries?** The migration plan recommends unified `loam init`, `loam amend`, `loam scope new`, `loam plot create`, `loam status`. The alternative is keeping tools as independent binaries (`loam-amend`, `orchestrator-status`, etc.). Owner calls; recommendation is unified.

4. **Plugin v1 — just Dev/SDLC, or Dev/SDLC + one more?** FUTURE_IDEAS names eight plugin candidates. v1 discipline says "not all eight"; the question is whether v1 is strictly Dev/SDLC or whether one more (trellis, arbor) lands at launch. Recommendation: **Dev/SDLC only.** Shipping two plugins doubles the launch scope and risks the message "we're a plugin platform" dominating "we're an outcome-governed harness." Owner calls.

5. **Launch timing — chase a conference window, or launch when ready?** Chasing a conference window (e.g., an AI Engineer Summit) gives a natural launch moment and amplifier. Launching when ready means whenever Phase E is ready regardless of calendar. Recommendation: **launch when ready; submit a talk afterward.** Owner calls.

6. **Non-technical user messaging — include at launch, or defer?** The spec names non-technical accessibility as a priority. But v1 isn't there yet. Do we messaging-flavour the launch toward non-tech users (risking over-promising) or explicitly defer to v2 (risking under-promising)? Recommendation: **defer explicitly;** say in the README "the v1 audience is technical; the non-technical surface is a v2+ direction." Owner calls — this shapes a chunk of the launch-post narrative.

7. **Domain strategy — `loam.dev`, `loam.sh`, `loam.harness`, or something else?** Availability, vibe, cost. Recommendation: `loam.dev` if available; `loam.sh` as backup. Owner calls.

8. **Public repo location — `lukeivers/loam`, `loamharness/loam`, `iverscorp/loam`?** Brand implications differ. Personal-brand (`lukeivers/loam`) vs product-brand (`loamharness/loam`) vs corporate-brand (`iverscorp/loam`). Recommendation: `loamharness/loam` or similar product-brand — scales better if the project grows; Luke is the founder, but the project isn't Luke.

9. **Anthropic relationship — co-launch, independent, or adversarial?** loam is complimentary to Anthropic's direction (Claude Code + Agent SDK + MCP). Anthropic might (a) bless the launch, (b) politely ignore it, (c) later build a competing first-party thing. All three are survivable; the first is strongest. Recommendation: **pursue the blessing; design for survival if it's not forthcoming.** Owner's call on how hard to pursue.

10. **Maintainer governance — sole-maintainer at launch and grow later, or appoint 2-3 co-maintainers at launch?** Sole-maintainer is simpler but bus-factor-1; co-maintainer at launch is stronger governance but requires recruiting and aligning. Recommendation: **sole at launch; actively recruit co-maintainers during v1.x** (months 3-12). Owner calls.

---

## 13. Appendix: external references + projects to study

### Primary references (read these before launch planning further)

- **LangChain launch retrospective (Harrison Chase's blog posts, 2023-2024).** What went right, what went wrong. Especially the posts on the LangChain Expression Language rewrite — a cautionary tale about API debt.
- **LlamaIndex documentation.** Reference-class example of AI-tooling docs done right. Structure, progression, cookbook depth.
- **CrewAI's README.** Short, opinionated, metaphor-forward. Good model for the loam README's tone.
- **Aider's GitHub.** Small-project excellence. Read every commit message and issue template for style.
- **Obsidian's community handbook.** PKM-adjacent community governance; good model for a technical-community that ships quality at a sustainable pace.
- **The Anthropic Claude Agent SDK docs.** loam sits on top of these; anyone building a loam plugin will read these.
- **Anthropic's MCP documentation.** For plugin authors integrating external tools.
- **Anthropic's Claude Code documentation.** For the hook-events surface loam exploits.

### Launch / marketing + community references

- **Simon Willison's launch posts for Datasette / LLM / related projects** — reference-class single-maintainer open-source that actually grew.
- **Patrick McKenzie's "How to write a software launch announcement."**
- **Contributor Covenant v2.1** (contributor-covenant.org).
- **CHAOSS metrics** — community health signals for open-source.
- **Nadia Eghbal, "Working in Public"** — sustained-maintainer dynamics.

### AI-tooling landscape to study

- **LangChain** (github.com/langchain-ai/langchain): the dominant agent framework; study API surface + docs structure + community engagement patterns.
- **LlamaIndex** (github.com/run-llama/llama_index): RAG-focused; study narrow-scope execution.
- **CrewAI** (github.com/joaomdmoura/crewai): opinionated multi-agent; study metaphor-as-product.
- **AutoGen** (github.com/microsoft/autogen): Microsoft-backed; study how corporate-backing shapes community dynamics.
- **SWE-agent** (github.com/princeton-nlp/SWE-agent): research-project shape; study what research-projects get wrong for real usage.
- **Aider** (github.com/paul-gauthier/aider): indie AI-coding tool; study small-project excellence.
- **Cline** (github.com/cline/cline): Claude-native coding; study Claude-ecosystem positioning.
- **MCP SDK** (github.com/modelcontextprotocol): protocol-first tooling; study protocol-vs-platform trade-offs.
- **Dust** (dust.tt, github.com/dust-tt/dust): no-code agent platform; different audience but useful for contrast.
- **CopilotKit** (github.com/CopilotKit/CopilotKit): framework-vs-SDK trade-offs; study embedded-agent patterns.

### Competitive / adjacent projects to watch during launch

- Anthropic's Claude Code and Agent SDK release notes (anything that overlaps with loam's primitives).
- LangChain's LangGraph — the closest API-shape to loam's primary-persona + scope-of-work primitives.
- Swyx's AI-tooling posts — leading indicator for what the dev-tooling AI community values.
- Simon Willison's weekly notes — captures AI-tooling landscape shifts early.

---

*Research authored 2026-04-22. Read-only: no canonical commits, no code edits, no changes outside `.scratch/claude-output/`.*
