# loam — Shared-Artefact Quality Catalogue

**Date:** 2026-06-01
**Status:** READ-ONLY research + catalogue (1.1+ roadmap pillar; nothing built — every guard below is an owner-gated follow-on build)
**Owner:** Luke Ivers
**Author:** `loam-researcher` (Opus), dispatched per Telegram 13378
**Working tree:** `/Users/lukeivers/loam` (main)
**Doc class:** planning + analysis (design catalogue)
**Trigger:** owner directive (TG 13378) — enumerate everything loam should automatically own when it builds shared artefacts FOR users, so output is high-quality, secure, well-designed, and adoption-driving.

**Reads this composes on (Tier-0 verified on disk 2026-06-01):**
- `CLAUDE.md` Lens 0–7 — the prime lens (per-user-tuned translation) is this catalogue's spine; every item translates an expert concern into a layperson question.
- `docs/VALUE_PROPOSITION.md` — §83 "the harness-as-builder owes the user the same token discipline the harness-as-runtime owes them" + §85 the verified ~25,000-tokens-per-run leak observation. The anchor for the Maintainability / token-hygiene category.
- `docs/design/adaptive-interaction-model.md` — the learning-engine spine. The "learned per-user quality profile" the dispatch names IS this model's matrix, extended from interaction axes to output-quality axes.

**External standards verified (claim-or-cite, fetch date 2026-06-01):**
- WCAG 2.2 — W3C Recommendation 5 Oct 2023 (update 12 Dec 2024); Level AA = 32 Level-A + 24 Level-AA = 56 success criteria; AA is the legal-compliance target (EAA, UK Equality Act, US §508). https://www.w3.org/TR/WCAG22/
- OWASP Top 10:2025 — final release Jan 2026. Injection = A05:2025 (SQLi, XSS, command injection); SSRF folded into A01; two NEW categories: Software Supply Chain Failures + Mishandling of Exceptional Conditions. https://owasp.org/Top10/2025/
- OAuth 2.0 Authorization Code Flow + PKCE (RFC 7636); OpenID Connect standardizes endpoint discovery via `.well-known/openid-configuration` — the mechanism enabling email-domain→provider inference. https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow-with-pkce
- Vercel: sensitive (non-readable) env-vars; Standard Protection + Password/Vercel-Authentication for preview deployments (publicly accessible by default otherwise). https://vercel.com/docs/deployment-protection

---

## Executive summary (non-technical)

When loam builds something for you that you then hand to other people — a web app, a document, a small tool, a shared link — there's a long list of things that make the difference between "works on my machine" and "polished, safe, and good enough that other people want it too." Most of that list is invisible expert work: not leaking passwords, making it usable by people with screen readers, loading fast, looking consistent with the rest of your stuff, not collecting more personal data than it needs.

The point of this catalogue is: **loam should own all of that automatically, and only ever ask you a question you can actually answer.** Not "which identity provider?" — but "what's your work email?", and loam figures out the rest. Every item follows that pattern: an expert concern, translated into one plain question (or inferred with no question), with loam doing the hard part underneath.

Two bigger ideas wrap the list:

1. **This is marketing.** Every shared thing loam builds carries loam's fingerprints. If they're all secure, polished, accessible, and consistent, the quality itself is the advertisement — people who receive a loam-built artefact are the next people who want loam. The catalogue is a quality list AND a growth engine.

2. **loam learns your taste once and reuses it forever.** The first time you correct a color, set a brand, or tell loam your company's compliance situation, that becomes part of a living per-user profile that every future build reads from — the same learning engine already designed for how loam talks to you (`adaptive-interaction-model.md`), now pointed at what loam builds. Your edits at review time flow back into the profile, so loam gets more "you" with every artefact.

**The catalogue:** 11 categories (9 from the seed, 2 added), **58 catalogue items**. A **7-item security FLOOR** is flagged conditionally-1.0-blocking (only if 1.0 can build-and-share an artefact at all); everything else is 1.1+. The single highest-leverage adoption item: the **per-artefact "made-with-loam" quality mark gated on passing the floor** (§13) — it's the flywheel's flywheel.

---

## §1 Current state

Verified on disk 2026-06-01:
- **No existing output-quality machinery.** `docs/design/` holds the doctrine, the adaptive-interaction-model, and no shared-artefact quality catalogue, no design-token system, no a11y/security guard for built artefacts. This is net-new design surface.
- **The learning engine exists in design, not yet pointed at output.** `adaptive-interaction-model.md` (2026-05-31) has an MVP marked BUILT at N4 — but its matrix carries *interaction* axes (exposure/autonomy/tone/learning-appetite), not *output-quality* axes. Extending it to a quality profile is the unifying mechanism this catalogue proposes; it is unbuilt.
- **The token-hygiene concern is already canon.** VALUE_PROPOSITION §83–85 already obligates the harness-as-builder to owe built artefacts the same token discipline — with a concrete verified leak (~25k tokens/run). The one catalogue category already a stated loam principle.

Risk: building output-quality guards ad hoc per artefact-type instead of against one profile, which would re-create the "single cell value frozen as a global default" anti-pattern the interaction-model already names.

---

## §2 Ruthless Feedback on the seed taxonomy (Lens 7)

The dispatch's seed list is 9 categories and substantially right. Three structural notes:

1. **The seed is missing two categories.** (a) **Internationalization / localization** — shared artefacts cross locales (date/number/currency formats, RTL layout, translatable strings, Unicode handling); devs skip it constantly and it's hard to retrofit. (b) **Content safety / moderation & abuse-resistance** — anything a user shares that accepts *other people's* input (a form, a comment box, an upload) inherits a content-safety surface. Placed i18n as its own category (§11) and folded abuse-resistance into Security + Distribution.

2. **"Trust signals" is not a peer category — it's the *output* of every other category.** A "made-with-loam" mark is only meaningful if it *attests* to the floors the other categories enforce; standing alone it's a sticker. Kept as §13 but reframed as the **attestation layer** — a badge that means "this passed loam's floors." This reframing turns it into the actual flywheel (the highest-leverage item).

3. **The right organizing axis is not category — it's profile-class × blast-radius.** The most important instruction is the profile classification (learned / per-build / always-on floor), and the 1.0-blocking flag is a blast-radius cut. Categories are the reading order; every item carries both decision axes, and §14 re-indexes the catalogue by profile-class.

Net: seed accepted with 2 additions and the trust-signal reframing. 11 categories total.

---

## How to read each item

Every item carries: **Concern** · **Why even devs miss it** · **User-understandable ask** (the layperson question, or "inferred — no ask") · **Automatic build-time guard** (default-on mechanism + Lens 1 primitive) · **Profile class** (LEARNED-PROFILE / PER-BUILD / ALWAYS-ON-FLOOR) · **1.0-blocking?** (FLOOR-conditional-1.0 / 1.1+). Lens-4 confidence inline: **[HIGH→default-on]** / **[OPEN→fork]** (forks collected in §15).

---

## §3 Security & auth

**S1 — Identity provider selection.**
- Concern: choosing and wiring the right auth provider for a gated artefact.
- Why devs miss it: they hardcode one provider or roll their own session auth (the classic source of auth bugs).
- Ask: *"What's the email you'll sign in with?"* — loam infers the provider from the domain (gmail/googleworkspace → Google, outlook/a tenant domain → Microsoft Entra) via the OIDC `.well-known/openid-configuration` discovery endpoint, no provider question ever asked. (The dispatch's canonical example, made precise.)
- Guard: OAuth 2.0 Authorization Code Flow **+ PKCE (RFC 7636)** by default — never implicit flow, never password grant. Lens 1: composes on the provider's OIDC discovery + a host-native auth integration (NextAuth/Auth.js, Clerk, or the host's built-in).
- Profile: domain→provider mapping is LEARNED-PROFILE; the PKCE-flow choice is ALWAYS-ON-FLOOR.
- 1.0: **FLOOR-conditional-1.0** (secure-auth-by-default). [HIGH→default-on]

**S2 — Secrets never in the repo.**
- Concern: API keys, tokens, DB credentials committed to source.
- Why devs miss it: a `.env` gets staged once and lives in git history forever; the leak is invisible until scraped.
- Ask: none — inferred and enforced silently. If the user pastes a key, loam routes it to a secret store, never a tracked file.
- Guard: `.gitignore` for `.env*` by default + pre-commit secret scanning (gitleaks/`git-secrets`) + host secret store (Vercel sensitive env-vars, non-readable once set). Lens 1: host env-var system + a PreToolUse guard mirroring loam's own never-commit-secrets hook.
- Profile: ALWAYS-ON-FLOOR. 1.0: **FLOOR-conditional-1.0**. [HIGH→default-on]

**S3 — HTTPS/TLS everywhere.** Concern: artefact served/transmitted in cleartext. Devs miss: localhost dev is HTTP; the prod default gets forgotten. Ask: none. Guard: deploy targets that terminate TLS by default (Vercel/Netlify/Cloudflare auto-provision certs); HSTS header; no mixed content. Profile: ALWAYS-ON-FLOOR. 1.0: **FLOOR-conditional-1.0** (free on default hosts). [HIGH→default-on]

**S4 — Injection / XSS / CSRF defaults.**
- Concern: untrusted input executing as code/markup/requests — OWASP **A05:2025 Injection** (incl. XSS) + CSRF.
- Why devs miss it: string-concatenated SQL and `innerHTML` are the path of least resistance.
- Ask: none — inferred from the artefact shape (does it take input? render user content? mutate state?).
- Guard: parameterized queries / ORM by default; framework auto-escaping left on (React/Svelte escape by default); CSRF tokens on state-changing routes; Content-Security-Policy header. Lens 1: framework built-in escaping + CSRF middleware; cite OWASP Top 10:2025 A05.
- Profile: ALWAYS-ON-FLOOR. 1.0: **FLOOR-conditional-1.0**. [HIGH→default-on]

**S5 — Rate-limiting & abuse-resistance.** Concern: public endpoints hammered / scraped / brute-forced. Devs miss: fine until shared. Ask: *"Roughly how many people will use this?"* → sizes the limit. Guard: default per-IP rate limit on public mutating routes; CAPTCHA/turnstile on open forms. Lens 1: host edge-middleware rate-limit. Profile: limit value PER-BUILD; "a limit exists" ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]

**S6 — Least-privilege.** Concern: tokens scoped to everything. Devs miss: broad scopes "just work." Ask: none — inferred from what the artefact calls. Guard: narrowest OAuth scopes / API permissions; separate keys per environment. Profile: posture ALWAYS-ON-FLOOR; scope set PER-BUILD. 1.0: 1.1+. [HIGH→default-on]

**S7 — Encryption at rest.** Concern: stored data unencrypted on disk. Devs miss: default DB is often unencrypted local. Ask: *"Does this store anything personal about people?"* Guard: managed datastores with at-rest encryption on by default; no plaintext PII at rest. Profile: storage posture LEARNED-PROFILE; per-artefact PER-BUILD. 1.0: 1.1+ (escalates toward floor if PII). [HIGH→default-on]

**S8 — Dependency vulnerability scanning.**
- Concern: a shipped dependency with a known CVE — OWASP A06-class + the NEW **Software Supply Chain Failures** category (2025 final release).
- Ask: none — inferred and run automatically.
- Guard: `npm audit` / `pip-audit` / Dependabot-equivalent at build; block-on-critical; lockfile pinned. Lens 1: package-manager audit + Dependabot. Cite OWASP 2025 supply-chain category.
- Profile: ALWAYS-ON-FLOOR (scan runs); block-threshold PER-BUILD. 1.0: **FLOOR-conditional-1.0 for critical/known-exploited**. [HIGH→default-on]

**S9 — Secure host config.**
- Concern: deployment exposes preview/staging URLs, debug endpoints, or admin routes publicly. Vercel preview deployments are **publicly accessible by default** (verified) — a staging URL leaks pre-release data unless protected.
- Ask: *"Is this ready for everyone, or still just for you and your team?"* → maps to deployment-protection level.
- Guard: preview/staging behind Vercel Standard/Password Protection; debug off in prod; security headers (HSTS, X-Content-Type-Options, frame-ancestors). Lens 1: host deployment-protection + `vercel.json` headers.
- Profile: team-vs-public default LEARNED-PROFILE; per-artefact gate PER-BUILD. 1.0: 1.1+ (see §15 F2). [HIGH→default-on]

---

## §4 Compliance & legal

**C1 — Regulatory regime inference.** Concern: which laws apply (GDPR / CCPA-CPRA / HIPAA / SOC 2). Devs miss: "later/legal's problem" until a shared artefact collects EU or health data. Ask: *"What industry are you in, and will people outside the US use this?"* → infers GDPR (EU), CCPA/CPRA (CA), HIPAA (US health PII), SOC 2 expectations (B2B SaaS). Guard: regime → applied control set (consent capture, data-subject-rights surface, BAA awareness). **Honesty floor: loam never *asserts* compliance — that's an org-level audited state, not an artefact property; loam applies the *controls* and says so honestly.** Profile: LEARNED-PROFILE. 1.0: 1.1+. [OPEN→fork F3]

**C2 — Privacy policy + ToS generation.** Concern: a shared app collecting data legally needs a privacy policy. Devs miss: boilerplate nobody wants to write. Ask: *"What does this collect from people, and how do they contact you?"* Guard: auto-generate policy + ToS from the artefact's real data flows; footer links; stamped "generated, review with counsel," never legal advice. Profile: contact details LEARNED-PROFILE; collection surface PER-BUILD. 1.0: 1.1+. [HIGH→default-on with disclaimer]

**C3 — Cookie / tracking consent.** Concern: GDPR/ePrivacy require consent before non-essential cookies. Devs miss: analytics drop cookies on load with no banner. Ask: none beyond C1. Guard: consent banner auto-injected when tracking present AND EU-reachable audience inferred; essential-only default. Profile: PER-BUILD under LEARNED jurisdiction. 1.0: 1.1+. [HIGH→default-on]

**C4 — Data residency.** Concern: data stored in a forbidden region. Devs miss: default cloud region is the dev's account default. Ask: covered by C1. Guard: region-pin the datastore to the inferred jurisdiction. Profile: LEARNED-PROFILE. 1.0: 1.1+. [OPEN→fork F3]

**C5 — PII handling & minimization.** Concern: collecting more personal data than needed. Devs miss: "collect everything, decide later." Ask: *"What's the least you need to know about each person to make this work?"* Guard: collect-minimum scaffolding; PII fields flagged + access-restricted. Profile: LEARNED-PROFILE. 1.0: 1.1+ (overlaps S7 floor for at-rest PII). [HIGH→default-on]

**C6 — License selection.** Concern: shared artefact with no license = legally unusable by recipients (or over-permissive). Devs miss: nobody picks a license until asked. Ask: *"Do you want other people to be able to use this freely, or keep it yours?"* → MIT/Apache-2.0 vs proprietary vs copyleft, never "which SPDX identifier." Guard: `LICENSE` file + header stamps. Profile: LEARNED-PROFILE; override PER-BUILD. 1.0: 1.1+. [HIGH→default-on]

---

## §5 Design language & brand consistency

The category where the **learned per-user profile is most load-bearing** — the dispatch's "design tweaks flow back into the core design language," generalized.

**D1 — Design tokens (color / type / spacing).** Concern: a coherent visual system instead of ad-hoc styling. Devs miss: each project reinvents colors/spacing. Ask: *"Got a brand color or a logo? Or want me to pick a clean default?"* — one question, then inferred forever. Guard: a persisted design-token set (color scales, type ramp, spacing, radius) every build consumes. Lens 1: a design-token file (CSS custom properties / Tailwind config / Style Dictionary), structurally the same shape as the interaction-model cells. **This is the engine the dispatch describes.** Profile: **LEARNED-PROFILE** (the spine). 1.0: 1.1+. [HIGH→default-on]

**D2 — Cross-build consistency.** Concern: artefact #5 looks like the same maker as #1. Devs miss: no shared system across one-offs. Ask: none — inferred from D1 tokens. Guard: every build reads the same tokens + component library. Profile: LEARNED-PROFILE. 1.0: 1.1+. [HIGH→default-on]

**D3 — Review-edits flow back to the core spec.**
- Concern: when the user tweaks a color/spacing at review time, that edit should *teach the profile*, not just patch this artefact.
- Ask: none — the edit IS the signal.
- Guard: a review-time edit to a token-governed property writes back to the profile with confidence/evidence (the interaction-model evidence→update mechanism: a one-off tweak is provisional; a repeated pattern updates the token). Lens 1: the interaction-model's evidence-counter + write-back path, pointed at design tokens. **The single mechanism that makes the design system *compound*.**
- Profile: LEARNED-PROFILE. 1.0: 1.1+ (write-back threshold OPEN→fork F4). [HIGH→default-on]

**D4 — Light/dark theming.** Concern: artefact looks intentional in both system themes. Devs miss: dark mode an afterthought. Ask: none — always-on. Guard: `prefers-color-scheme` dual-theme, both meeting the named dark-mode quality bar. **Already a Luke-tuned default** (`feedback_dynamic_theme_for_generated_documents.md`) — promote from "generated documents" to all shared artefacts. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]

**D5 — Responsive layout.** Concern: works on phone/tablet/desktop. Devs miss: built on desktop, never checked on mobile. Ask: none. Guard: responsive-by-default primitives; mobile-first breakpoints. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]

**D6 — Component reuse.** Concern: shared component vocabulary across builds. Devs miss: re-authored per project. Ask: none — inferred from profile. Guard: a per-user component library the profile points at. Profile: LEARNED-PROFILE. 1.0: 1.1+. [OPEN→fork F1]

---

## §6 Accessibility

**A1 — WCAG 2.2 Level AA conformance.** Concern: usable by people with disabilities — **WCAG 2.2 Level AA** (W3C Recommendation, the legal target). Devs miss: invisible to a non-disabled dev. Ask: none — always-on floor. Guard: a11y linting at build (axe-core / Lighthouse) targeting the 56 AA criteria; block-on-violation. Lens 1: axe-core/Lighthouse. Cite WCAG 2.2 AA. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+ (strong floor claim for shared artefacts — §15 F5). [HIGH→default-on]

**A2 — Keyboard navigation.** WCAG 2.1.1. Devs miss: they use a mouse; tab-order never tested. Ask: none. Guard: focus management + visible focus + logical tab order, linted. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]

**A3 — Color contrast.** WCAG 1.4.3 AA = 4.5:1 normal text. Devs miss: brand colors chosen for looks. Ask: none — and this *constrains D1*: loam picks token colors that already pass AA, so brand and accessibility don't fight. Guard: contrast-check the token palette at profile-creation; auto-adjust to pass 4.5:1. Profile: ALWAYS-ON-FLOOR (constrains the LEARNED token set). 1.0: 1.1+. [HIGH→default-on]

**A4 — Screen-reader semantics.** Concern: landmarks, ARIA, semantic HTML. Devs miss: `<div>`-soup works visually, fails audibly. Ask: none. Guard: semantic-HTML-first scaffolding; ARIA only where needed; linted. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]

**A5 — Alt text & media descriptions.** WCAG 1.1.1. Devs miss: alt text empty or skipped. Ask: none — loam can *generate* alt text from image content. Guard: auto-generate alt text via Claude vision at build; flag decorative vs informative. Lens 1: **Claude vision** — a strong Claude-leverage item; loam does what a human author skips. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]

---

## §7 Performance & cost

**P1 — Bundle size & lazy-loading.** Devs miss: dev machine + fast network hides bloat. Ask: none. Guard: code-splitting + lazy-load by default; bundle-size budget with a build warning on regression. Profile: ALWAYS-ON-FLOOR (budget exists); value PER-BUILD. 1.0: 1.1+. [HIGH→default-on]

**P2 — Caching.** Guard: cache-control headers + CDN defaults from the host. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]

**P3 — Image optimization.** Guard: auto optimization (next/image-equivalent, modern formats, responsive sizes). Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]

**P4 — Token-leak discipline (the artefact doesn't bleed loam's context).**
- Concern: a built artefact that quietly inherits loam's context or makes unnecessary runtime LLM calls, leaking tokens/cost — **VALUE_PROPOSITION §83–85, the verified ~25k-tokens/run leak.**
- Why devs miss it: an AI-harness-specific failure no general dev has a name for.
- Guard: built artefacts are **deterministic and self-contained by default**; runtime LLM calls scoped narrowly and only where deterministic code genuinely can't replace them; no loam-context inheritance. **The one category already a stated loam principle.**
- Profile: ALWAYS-ON-FLOOR. 1.0: **FLOOR-conditional-1.0 if 1.0 builds runnable artefacts** (owner-betrayal class). [HIGH→default-on]

**P5 — Cost ceilings on hosted artefacts.** Concern: a shared hosted thing running up a bill. Ask: *"What's the most you'd want to spend a month on this?"* Guard: host spend-limit/alert; serverless-scale-to-zero defaults. Lens 1: host billing-limit + loam's cost-governance component. Profile: LEARNED-PROFILE. 1.0: 1.1+. [HIGH→default-on]

---

## §8 Reliability & observability

**R1 — Error handling & graceful degradation.** Guard: error boundaries + fallback UI + sensible defaults on failure. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]
**R2 — Logging.** Guard: structured logging at sensible levels; **no PII/secrets in logs** (ties to S2/C5). Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]
**R3 — Monitoring & uptime.** Ask: *"Want me to tell you if this ever goes down?"* → uptime check + alert to the user's channel (e.g. Telegram). Profile: PER-BUILD. 1.0: 1.1+. [OPEN→fork F6]
**R4 — Backups.** Ask: *"Is the data in here something you'd be upset to lose?"* Guard: managed-DB automated backups on by default for data-bearing artefacts. Profile: LEARNED-PROFILE. 1.0: 1.1+. [HIGH→default-on]

---

## §9 Data handling & privacy

(Distinct from §4: §4 is *legal regimes*, §9 is the *engineering posture* that satisfies them.)

**H1 — Collection minimization.** Ask: covered by C5. Guard: minimum-schema scaffolding. Profile: LEARNED-PROFILE. 1.0: 1.1+.
**H2 — Retention limits.** Ask: *"How long should this remember each person's info?"* Guard: TTL/retention defaults + scheduled purge. Profile: LEARNED-PROFILE. 1.0: 1.1+.
**H3 — Deletion (right-to-erasure, GDPR Art. 17).** Ask: none — default when PII present. Guard: a data-subject-deletion surface auto-scaffolded. Profile: PER-BUILD under LEARNED regime. 1.0: 1.1+.
**H4 — Export (data portability, GDPR Art. 20).** Ask: none — default when PII present. Guard: export endpoint auto-scaffolded. Profile: PER-BUILD. 1.0: 1.1+.

---

## §10 Distribution / sharing pre-flight

**X1 — "Ready to share?" checklist (the pre-flight gate).**
- Concern: one gate that confirms no-secrets, floors-passed, clean-state before a shareable link/artefact goes out.
- Ask: loam runs it and reports in plain language: *"Before you share this — checked: no passwords leaked, works on phones, usable with a screen reader, loads fast. One thing to confirm: it'll cost up to $X/mo. Good to share?"*
- Guard: a pre-flight scope that runs the floor checks (S2/S4/S8 + A1 + P4) and blocks-or-surfaces. Lens 1: **a Claude-native scope / subagent that runs the gate** (the harness composition VALUE_PROPOSITION §155 describes). **This is the consumer that makes the whole catalogue operational** — without it, the items are advisory.
- Profile: the *gate* is ALWAYS-ON-FLOOR; *which* checks block is PER-BUILD. 1.0: the no-secrets + obvious-injection subset is **FLOOR-conditional-1.0**. [HIGH→default-on]

**X2 — Clean README / onboarding for THEIR users.** Ask: *"Who's going to receive this, and what do they need to do first?"* Guard: auto-generated README + first-run/onboarding path tuned to the recipient audience. Profile: PER-BUILD. 1.0: 1.1+. [HIGH→default-on]

**X3 — No-leak final scan.** Concern: last-pass for secrets/PII/debug-state before the link is live (mirrors loam's own "last-line scan before send"). Ask: none. Guard: a final secret/PII/debug scan in X1's pre-flight. Profile: ALWAYS-ON-FLOOR. 1.0: **FLOOR-conditional-1.0**. [HIGH→default-on]

---

## §11 Internationalization (ADDED — §2 feedback)

**I1 — Locale-aware formatting.** Ask: *"Will people in other countries use this?"* Guard: `Intl`-based formatting by default. Profile: LEARNED-PROFILE. 1.0: 1.1+. [HIGH→default-on]
**I2 — RTL & translatable strings.** Guard: logical-property CSS (RTL-safe) + string externalization scaffolding. Profile: PER-BUILD. 1.0: 1.1+. [OPEN→fork F6]
**I3 — Unicode / encoding correctness.** Guard: UTF-8 end-to-end default. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]

---

## §12 Maintainability

**M1 — Docs.** Guard: inline + README docs auto-generated. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+.
**M2 — Tests.** Guard: a smoke/critical-path test scaffolded by default (loam's ODD/outcome-altitude discipline applied to built artefacts — `feedback_test_outcome_altitude_required.md`). Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+.
**M3 — Versioning.** Guard: semantic version + changelog scaffolded; **versions assigned at release time** (`feedback_version_numbers_at_release_time.md`). Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+.
**M4 — Dependency hygiene.** Guard: lockfile + minimal-deps default + scheduled update checks. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+.
**M5 — Artefact token-hygiene (no loam-context bleed).** Concern: the artefact carries none of loam's internal context/files — VALUE_PROPOSITION §83. Guard: build emits a clean, self-contained artefact with no loam internals; verified by a context-hygiene check. Profile: ALWAYS-ON-FLOOR. 1.0: arguably FLOOR (owner-betrayal class — see P4). [HIGH→default-on]

---

## §13 Trust signals (reframed per §2 — the attestation layer / the flywheel)

**T1 — The "made-with-loam" quality mark, gated on passing the floors.**
- Concern: a visible mark that *attests* the artefact passed loam's security/a11y/quality floors — not decoration, an attestation.
- Ask: *"Want a small 'built with loam' mark on this? It tells people it's been security- and accessibility-checked."* → opt-in, never forced.
- Guard: the mark is *only* emitted when X1's pre-flight floors pass — so the mark MEANS something. Every recipient of a marked artefact sees attested quality; that's the adoption signal. Lens 1: the pre-flight gate (X1) is the attestation source; the mark is its certificate.
- Profile: opt-in LEARNED-PROFILE; the attestation ALWAYS-ON-FLOOR (the mark can't appear on a floor-failing artefact). 1.0: 1.1+. **[HIGH→default-on — the single highest-leverage adoption item; see §16]**

**T2 — Quality badges (a11y / security attested).** Guard: per-floor badges derived from X1's checks. Profile: ALWAYS-ON-FLOOR. 1.0: 1.1+. [HIGH→default-on]

---

## §14 Re-index by profile class (the builder's consumption order)

**ALWAYS-ON-FLOOR (~24):** S2, S3, S4 + posture of S1/S5/S6/S7/S8, A1–A5, D4, D5, P1–P4, R1, R2, H-floors, I3, X1-gate, X3, M1–M5, T1-attestation, T2.
**LEARNED-PROFILE (~16):** S1 domain-map, S7 storage posture, S9 team-default, C1, C4, C5, C6, D1, D2, D3, D6, P5, R4, H1, H2, I1.
**PER-BUILD (remainder):** S5 limit value, S6 scope set, C2 surface, C3, H3, H4, R3, X2, I2, per-build thresholds.

The LEARNED-PROFILE set is the **output-quality extension of `adaptive-interaction-model.md`** — same `{value, confidence, evidence}` cell shape, same hysteresis write-back (D3 IS the evidence→update mechanism pointed at design tokens), same plain-language inspect-and-correct surface. **Recommendation: do not build a second profile store — add output-quality rows to the existing interaction-model matrix** (or a sibling `QUALITY-PROFILE.md` of identical shape sharing the write path).

---

## §15 Open design forks (Lens 4: genuinely-open, surface to owner)

- **F1 — Build-your-own component system vs adopt a base (shadcn/Radix/etc.).** [D6] Recommendation: **adopt an accessible base, theme it with the user's tokens** — gets A1–A4 floors nearly free while D1 tokens carry the brand.
- **F2 — Preview-protection default: team-private or public?** [S9] Recommendation: **private-by-default, one-question to open** (matches the interaction-model's "safe on actions, open on talk" asymmetry).
- **F3 — How far loam goes on legal claims.** [C1/C2/C4] loam can *apply controls* but must never *assert compliance*. Recommendation: **generate with a prominent "review with counsel" stamp.**
- **F4 — Review-edit write-back threshold.** [D3] How many repeated edits before a token updates the profile. Recommendation: **inherit the interaction-model's dark-launch-then-calibrate discipline; don't import a number.**
- **F5 — Is accessibility (A1) a 1.0 FLOOR for SHARED artefacts?** Strong case: a shared inaccessible artefact carries loam's mark to people it excludes — anti-adoption + legal exposure. Recommendation: **if 1.0 can share, A1 (WCAG-AA lint, block-on-violation) joins the floor.**
- **F6 — Proportionality of i18n + monitoring for small artefacts.** [I2/R3] Recommendation: **scale to inferred audience size; floor is correctness (I3, R1), not full coverage.**

---

## §16 The single highest-leverage item (adoption flywheel)

**T1 — the floor-gated "made-with-loam" quality mark, composed with X1 the pre-flight gate.** It's the one item that *converts quality into adoption*. Every other item makes the artefact good; T1+X1 makes the goodness *visible to the recipient* and *trustworthy* (the mark can't appear unless the floors passed). Each shared marked artefact is seen by N new people who experience attested security/a11y/polish — the self-reinforcing flywheel. Cheap relative to its leverage (a gate + a certificate, not new infrastructure). 1.1+, but the FLOOR subset it gates on (§17) is the conditional-1.0 work, so the foundation lands early.

---

## §17 The security-FLOOR subset — conditionally-1.0-blocking

Per the dispatch: **IF 1.0 can build-and-share an artefact, these are 1.0-blocking; otherwise all 1.1+.** The 7 floor items:

1. **S2** — secrets never in repo.
2. **S1** — secure-auth-by-default (OAuth Authcode+PKCE, never roll-your-own/implicit).
3. **S4** — no obvious injection/XSS (OWASP A05:2025), CSRF defaults.
4. **S3** — HTTPS/TLS (free on default hosts).
5. **S8** — block on critical/known-exploited dependency CVEs (OWASP supply-chain).
6. **X3 / X1-no-secrets-gate** — final no-leak scan before any share.
7. **P4/M5** — artefact token-hygiene / no loam-context bleed (owner-betrayal-class, VALUE_PROPOSITION §83–85).

Two borderlines flagged for owner ruling: **A1 accessibility** (§15 F5) and **S9 preview-protection** (§15 F2) — both 1.1+ as written but with a defensible floor claim on the adoption-and-exposure argument.

---

## §18 Provenance trail

- `CLAUDE.md` Lens 0–7; `docs/VALUE_PROPOSITION.md` §83–85 + §144–155; `docs/design/adaptive-interaction-model.md` (matrix shape, §2 evidence→update + hysteresis, §5 inspect/override, §6 composition) — verified 2026-06-01.
- WCAG 2.2 https://www.w3.org/TR/WCAG22/ · OWASP Top 10:2025 https://owasp.org/Top10/2025/ · OAuth-PKCE/OIDC discovery (auth0/okta) · Vercel deployment-protection https://vercel.com/docs/deployment-protection — all fetched 2026-06-01.
- loam feedback referenced: `feedback_dynamic_theme_for_generated_documents.md` (D4), `feedback_test_outcome_altitude_required.md` (M2), `feedback_version_numbers_at_release_time.md` (M3), `feedback_asymmetric_problem_solving.md` (§16).
