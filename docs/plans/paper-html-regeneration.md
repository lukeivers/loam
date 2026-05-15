# Paper HTML regeneration PATCH

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner ratification: dispatch brief from dispatcher 2026-05-14 explicitly authorises closure of FIDRAFT F-PAPER-HTML-REGEN (captured 2026-05-13 from v0.9.0 ODD paper publish build-time decision D-ODDPAPER.5.2 Path C; activation gate: next paper-edit cycle OR pre-v1.0 surface cleanup). This PATCH executes that closure.
**Slug:** `paper-html-regeneration` (scope-descriptive; no version pre-baked per `feedback_version_numbers_at_release_time`).
**Date authored:** 2026-05-14.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. Doc-asset addition (`docs/papers/odd-methodology.html`) regenerating a previously-staged file that was deleted at v0.9.0 publish (D-ODDPAPER.5.2 Path C); no public API change; no new outcome capability — restores the HTML reader-surface that was deferred at v0.9.0 publish. Trace-data layer (operator/reader-facing artefact) only.
**Predecessor:** v0.10.5 PATCH SHIPPED PUBLIC (sealed `da53584`; published `33ee5cb`). Build-forward per `feedback_build_forward_on_publish_pending`.
**Working directory:** `/Users/lukeivers/loam/`.
**Version derivation:** at release-time per `feedback_version_numbers_at_release_time`: `next_PATCH(v0.10.5) = v0.10.6`. Plan-doc slug scope-descriptive (no version pre-baked); AC family scope-descriptive (`AC.PHRG.*` for `paper-html-regeneration`).

---

## §1 — Outcome shape (the "why")

The v0.9.0 ODD methodology paper publish (sealed `4a4535f`; published `af57cff`) shipped the markdown source-of-truth at `docs/papers/odd-methodology.md` (629 lines, ~15,200 words) but did NOT ship the previously-staged HTML render at `docs/papers/odd-methodology.html`. The HTML had been committed at `cfcb03f` ("docs(papers): polish §6 to name Claude Code primitives + add HTML render", 2026-05-07, 443 insertions / 32KB) but was deleted at v0.9.0 source-edit time per build-time decision D-ODDPAPER.5.2 Path C, because:

1. The HTML's `<title>` + `<h1>` read "Objective-Driven Design — Outcome-Altitude Acceptance for LLM-Authored Software" (an earlier paper iteration's title) while v19's title is "Objective-Driven Design: Methodology Description and Case-Study Observations from LLM-Authored Software".
2. The HTML's body content was substantively different from v19 (the v19 markdown went through 12 reviewer-pass iterations between the HTML's authoring 2026-05-07 and v19's finalization 2026-05-12).
3. pandoc was not installed on the v0.9.0 dispatcher's machine.
4. HTML regen was non-trivial-at-the-moment for the v0.9.0 cycle scope.

Path C dropped the stale HTML from the publish (`git rm` + `git commit`) and shipped markdown-only — GitHub renders the markdown natively for external readers, so no reader-facing surface was strictly missing. The HTML regen was captured as FIDRAFT F-PAPER-HTML-REGEN at `docs/FUTURE_IDEAS_DRAFT.md:278` with activation gate: "next paper-edit cycle OR pre-v1.0 surface cleanup."

This PATCH activates the FIDRAFT against the second activation gate (pre-v1.0 surface cleanup). After this PATCH, the HTML render is back in-tree at `docs/papers/odd-methodology.html`, regenerated from the v19 markdown source-of-truth, with the existing custom-CSS template preserved (the `prefers-color-scheme` dynamic theming from `cfcb03f` is structurally functional + intentional in both light + dark modes).

**Pre-source-edit baseline (empirical, captured 2026-05-14):**

- `which pandoc` → exit code 1 (`pandoc not found`).
- `ls docs/papers/` → only `odd-methodology.md` present (HTML absent post-v0.9.0).
- `git show cfcb03f --stat -- docs/papers/odd-methodology.html` → 443-line HTML, full custom-CSS template embedded in `<style>` block (`:root` light-mode variables + `@media (prefers-color-scheme: dark)` redefinition + responsive `@media (max-width: 640px)` mobile breakpoint).
- `wc -l docs/papers/odd-methodology.md` → 629 lines.
- Markdown structural features (grep counts): 81 `^|` lines (5 tables); 0 code fences (`^\`\`\``); 0 footnotes (`^\[\^`); 0 task lists; ordered + unordered lists; emphasis + strong + code spans throughout.

After this PATCH:

1. pandoc installed via brew (homebrew available at `/opt/homebrew/bin/brew`).
2. `docs/papers/odd-methodology.html` regenerated from `docs/papers/odd-methodology.md` using pandoc + the CSS template extracted verbatim from `cfcb03f`.
3. Title reads v19's "Methodology Description and Case-Study Observations" (NOT the deleted HTML's stale "Outcome-Altitude Acceptance").
4. Dynamic-theme `prefers-color-scheme` preserved + verified working in both light + dark modes.
5. Reproducible-regen invocation documented in smoke writeup §3 + plan-doc D-PHRG.2 (the canonical pandoc command line a future author would type).
6. Smoke writeup at `docs/experiments/paper-html-regeneration-hard-smoke.md` captures the full regen + verification flow.

Closes F-PAPER-HTML-REGEN. Composes with v0.9.0 paper publish (the predecessor that deferred this) + `feedback_dynamic_theme_for_generated_documents` (the regen MUST preserve dynamic-theme behavior).

---

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised + documented-state
           matches actual-state (v1.0 quality-bar criterion #1)
             └─ docs/papers/ surface ships both source-of-truth
                (markdown) + reader-friendly render (HTML with
                custom theming) so external readers can read the
                paper in either form
                  └─ AC.PHRG.1 (regenerated HTML at canonical path
                                  matches v19 markdown source-of-truth —
                                  title corrected, body content
                                  correspondence verified, all sections
                                  + tables + lists rendered)
                  └─ AC.PHRG.2 (dynamic-theme prefers-color-scheme
                                  preserved + functional in both light +
                                  dark modes per
                                  feedback_dynamic_theme_for_generated_documents)
                  └─ AC.PHRG.3 (regen process is reproducible — pandoc
                                  invocation documented + idempotent)
                  └─ AC.PHRG.4 (outcome-altitude dogfood probe — smoke
                                  writeup confirms regen ran end-to-end +
                                  theme behavior verified in both modes)
                  └─ AC.PHRG.S (seal-diff: only the regenerated HTML +
                                  smoke writeup + plan-doc + manifest +
                                  STATE/roadmap/FIDRAFT admin + dev-sdlc
                                  seal anchor artefacts touched; markdown
                                  source-of-truth NOT edited)
```

The two VALUE_PROPOSITION tests:

- **Primary-persona test** — the HTML render IS the reader-facing translation surface that turns the GFM markdown source-of-truth into a styled, theme-adaptive document an external reader can open in a browser without GitHub-rendering context. Restoring it returns the published-paper surface to dual-form parity (markdown source + HTML render) that the v0.9.0 publish originally intended.
- **Harness test** — no harness extension; closes a defect within the existing `docs/papers/` surface (the HTML render that was deferred at v0.9.0 publish).

Composes with: v0.9.0 ODD methodology paper publish (the MINOR that surfaced this — D-ODDPAPER.5.2 Path C deferred the HTML; this PATCH closes the deferred work), `feedback_dynamic_theme_for_generated_documents` (the regen MUST preserve `prefers-color-scheme` adapt behavior), `feedback_loose_AC_text_fix_AC_not_implementation` (AC.PHRG.1 text was authored to specify outcome-shape — "matches v19 markdown source-of-truth" — rather than implementation-shape "pandoc converts markdown to HTML"; method stays builder's call), `feedback_principle_application_front_load_and_audit` (the dispatch-brief enumerates the principle set for this turn).

Composes with: F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline (verified empirically: only one reference to F-PAPER-HTML-REGEN exists in `docs/`, the entry itself at `docs/FUTURE_IDEAS_DRAFT.md:278`; no dependent FIDRAFT entries reference it as a blocker / dep / unblocker; no flip-on-unblock action needed beyond the entry itself).

---

## §3 — Component fence

**PATCH spans one regenerated HTML asset (`docs/papers/odd-methodology.html`) + one slug-named smoke writeup + universal-admission docs admin.** Seal anchor: dev-sdlc (matches v0.10.5 / v0.10.4 / v0.10.3 / v0.10.2 PATCH precedent; `docs/papers/` is admitted via the manifest's `extra_allowed_prefixes` since it's not in the universal-admission list — a deliberate addition for this PATCH's scope).

**PRIMARY (1 regenerated HTML asset):**

- `docs/papers/odd-methodology.html` — regenerated from `docs/papers/odd-methodology.md` via the pandoc invocation documented in D-PHRG.2 + smoke writeup §3. CSS template extracted verbatim from the deleted `cfcb03f` HTML (preserves the `:root` light-mode CSS variables + `@media (prefers-color-scheme: dark)` block + responsive mobile breakpoint).

**PRIMARY (smoke writeup):**

- `docs/experiments/paper-html-regeneration-hard-smoke.md` — slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`. Captures: Stage 1 (pandoc install verification + version captured); Stage 2 (regen invocation captured verbatim + output file size + HTML structural verification); Stage 3 (dynamic-theme behavior verification in both light + dark modes); Stage 4 (idempotence check via `sha256sum` before/after second invocation).

**SECONDARY (admin docs — universal-admission):**

- `docs/STATE.md` — append v0.10.6 row to §2 (Change log section).
- `docs/release-roadmap.md` — append v0.10.6 row to §2 + v0.10.6 standalone bold entry to §3 Active version.
- `docs/FUTURE_IDEAS_DRAFT.md` — flip F-PAPER-HTML-REGEN entry to RESOLVED (status flip; entry preserved for audit trail).

**TERTIARY (cycle bookkeeping):**

- `docs/plans/paper-html-regeneration.md` — this file.
- `docs/plans/paper-html-regeneration.manifest.yaml` — schema-v3 manifest.
- `plugins/dev-sdlc/seals/SEAL_COMMIT.paper-html-regeneration` — seal narrative.
- `plugins/dev-sdlc/tests/SEAL_COMMIT` — sidecar bump (auto at seal-time).
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — BASELINE pointer auto-bump (auto at seal-time per dev-sdlc-anchored amendment convention; pre-included in AC.PHRG.S allow-list per the plan-doc-template-auto-bump-fence convention).

**Out of fence:**

- The markdown source-of-truth `docs/papers/odd-methodology.md` itself (this PATCH regenerates the HTML; does NOT edit the markdown — D-PHRG.5).
- Any framework/* source (no Python code added, removed, or edited; no test added or removed).
- Any pyproject.toml bump (PATCH rides predecessor MINOR per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1-v0.10.5 precedent; D-PHRG.4).
- Adding a `framework/tools/loam/` script for markdown→HTML conversion (Path B; D-PHRG.1 ruled Path A pandoc; Path B captured as F-PAPER-REGEN-CUSTOM-SCRIPT for follow-on).
- Promoting the CSS to a standalone file under `docs/papers/` (out of scope; captured as F-PAPER-CSS-EXTRACT-TO-FILE for follow-on if a second paper enters the corpus).
- Adding paper content / sections / new citations (this PATCH ships a render of the existing v19 paper; not a content edit).
- `git commit --amend` (HARD HALT #4).
- Edits outside fence = halt.

---

## §4 — Acceptance criteria (`AC.PHRG.*`)

Each AC maps to a verifiable acceptance signal. Method stays builder's call.

### AC.PHRG.1 — Regenerated HTML matches v19 markdown source-of-truth

The regenerated `docs/papers/odd-methodology.html` is structurally and content-correspondingly aligned with the v19 markdown at `docs/papers/odd-methodology.md`:

1. **Title correct.** `<title>` element AND the first `<h1>` element both read "Objective-Driven Design: Methodology Description and Case-Study Observations from LLM-Authored Software" (matches v19 line 1) NOT the deleted HTML's stale "Outcome-Altitude Acceptance for LLM-Authored Software".
2. **All H2 sections present.** Every `## ` heading from the markdown (per `grep -E '^## ' docs/papers/odd-methodology.md`: "On this artefact", "Abstract", "1. Introduction", "2. ODD Methodology", "3. Reverse-Walk Pipeline", "4. The Outcome-Altitude Acceptance Requirement", "5. Motivating Example and Case Study", "6. Composition with LLM Toolchains", "7. Limitations and Future Work", "8. References") appears as an `<h2>` in the HTML.
3. **All H3 + H4 subsections present.** Every `### ` and `#### ` heading in the markdown appears as the corresponding HTML heading element (count match between markdown grep + HTML grep).
4. **Tables rendered.** All 5 tables from the markdown render as `<table>` elements with `<thead>` + `<tbody>` rows.
5. **Lists rendered.** Ordered + unordered list items from the markdown render as `<ol>` / `<ul>` + `<li>`.
6. **Emphasis + strong + code spans rendered.** `*italic*` → `<em>`; `**bold**` → `<strong>`; `` `code` `` → `<code>`.

**Verdict GREEN if:** the regenerated HTML's `<title>` text + first `<h1>` text both contain "Methodology Description and Case-Study Observations"; all 10 H2 headings from the markdown appear in the HTML; all 5 tables render as `<table>` elements; the regen-time pandoc invocation exits 0.

**Verdict YELLOW if:** title + structure correct but a single rendering edge-case slips (e.g., a code span containing a backslash escapes oddly; a table cell containing a pipe character renders weird); document the slip and address if material to reader experience.

**Verdict RED if:** title still reads "Outcome-Altitude Acceptance" (regen used wrong source OR pandoc cached the stale HTML); OR any H2 heading missing; OR any table fails to render as a `<table>` element; OR pandoc exits non-zero.

`outcome-altitude: false` (structural verification of the rendered artefact).

### AC.PHRG.2 — Dynamic-theme `prefers-color-scheme` preserved + functional in both modes

The regenerated HTML carries the full custom-CSS template extracted from the deleted `cfcb03f` HTML, with `prefers-color-scheme` dynamic theming functional in both light + dark modes:

1. **CSS variables defined for light-mode in `:root`.** `--bg`, `--bg-card`, `--bg-table-alt`, `--bg-quote`, `--fg`, `--fg-secondary`, `--fg-muted`, `--accent`, `--accent-strong`, `--link`, `--link-hover`, `--border`, `--border-strong` all present with the original light-mode hex values from `cfcb03f`.
2. **`@media (prefers-color-scheme: dark)` block redefines all variables for dark-mode.** Same variable names, dark-mode hex values from `cfcb03f` (`--bg: #0c0a09`, `--fg: #f5f5f4`, `--accent: #fcd34d`, etc.).
3. **Both modes look intentional per `feedback_dynamic_theme_for_generated_documents` quality bar.** Contrast hierarchy preserved (body fg vs bg vs secondary vs muted); accent + link tones distinguish from body text in both modes; borders + table-alt-bg readable in both modes; abstract block + blockquote + code spans visually distinct in both modes.
4. **Responsive mobile breakpoint preserved.** `@media (max-width: 640px)` block adjusts container padding + body font-size + heading font-sizes + table sizing.

**Verdict GREEN if:** the regenerated HTML's `<style>` block contains both the `:root` light-mode variable block AND the `@media (prefers-color-scheme: dark)` redefinition; opening the file in a browser with light-mode system theme renders with light backgrounds + dark text; toggling system theme to dark renders with dark backgrounds + light text; both modes look intentional (contrast + accent + borders all preserved).

**Verdict YELLOW if:** CSS template embedded but missing the responsive mobile breakpoint OR a single dark-mode variable shows muddy contrast (e.g., `--fg-muted` too close to `--bg-card`); document + fix before claiming GREEN.

**Verdict RED if:** `<style>` block missing the `@media (prefers-color-scheme: dark)` block entirely (dynamic theming gone); OR dark-mode renders with light-mode colors (theme-detection broken); OR the CSS template wasn't preserved (e.g., pandoc emitted its default styles instead of the custom CSS).

`outcome-altitude: true` (browser-rendered behavior in two distinct system theme states is the operator-visible outcome).

### AC.PHRG.3 — Reproducible regen mechanism documented + idempotent

The regen mechanism is documented + invokable + idempotent:

1. **Pandoc command line documented verbatim.** D-PHRG.2 ruling captures the canonical invocation; smoke writeup §3 also carries the verbatim invocation. A future author re-running the regen can copy-paste the command line.
2. **CSS template stored in-repo.** The CSS template is captured verbatim in the smoke writeup §3 (extracted from `cfcb03f`'s HTML); future regens use the same template.
3. **Idempotence.** Running the pandoc invocation twice produces byte-equal output (verified via `sha256sum` before vs after second invocation; smoke writeup §3.4 captures both hashes).

**Verdict GREEN if:** smoke writeup §3 contains: the pandoc command line; the CSS template (or a pointer to where it's stored); a `sha256sum docs/papers/odd-methodology.html` capture before + after re-running the regen, with matching hashes.

**Verdict YELLOW if:** invocation documented but re-run produces a non-content drift (e.g., trailing whitespace varies); document + address (likely a pandoc deterministic-output flag).

**Verdict RED if:** invocation not documented OR re-run produces materially different output (regen is not deterministic).

`outcome-altitude: false` (structural verification of the documented invocation).

### AC.PHRG.4 — Outcome-altitude dogfood probe (browser-render verification in both modes)

Live runtime probe verifies the regenerated HTML actually renders correctly in a real browser with system theme respected:

1. **Open the regenerated HTML in a browser.** `open docs/papers/odd-methodology.html` (macOS default browser).
2. **Light-mode render.** With system theme set to light (or default light browser theme), verify: light backgrounds (`#fbfaf7` body bg); dark text (`#1c1917` body fg); brown accent headings + tan-ish code-span backgrounds (`#f3f1ec`).
3. **Dark-mode render.** Toggle system theme to dark (System Settings → Appearance → Dark on macOS, OR `osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to true'`), reload the HTML, verify: dark backgrounds (`#0c0a09` body bg); light text (`#f5f5f4` body fg); golden-yellow accent headings (`#fcd34d`); blue-ish link tones (`#93c5fd`).
4. **Document at slug-named smoke writeup path.** `docs/experiments/paper-html-regeneration-hard-smoke.md` captures the verification process + observations + (optionally) before/after screenshots saved adjacent to the writeup.

The probe runs against the LIVE regenerated `docs/papers/odd-methodology.html` (not a synthetic fixture). The structural-correspondence verification path is AC.PHRG.1's domain (header + table grep); AC.PHRG.4 is the outcome-altitude check that the dynamic-theme actually works in a browser.

**Verdict GREEN if:** smoke writeup at the slug-named path documents both light-mode render + dark-mode render with observations consistent with the CSS variable values (light: `#fbfaf7` bg + `#1c1917` fg; dark: `#0c0a09` bg + `#f5f5f4` fg); both modes look intentional (not muddy/broken).

**Verdict YELLOW if:** writeup captures only one mode + a documented reason for not capturing the other (e.g., system theme can't be programmatically toggled in the test environment); fall-back verification via inspecting the rendered styles via curl/`open -a Safari` + manual observation acceptable.

**Verdict RED if:** writeup absent OR runtime render shows light-mode colors when system is dark (theme detection broken) OR text is unreadable in either mode (contrast failure).

`outcome-altitude: true` (browser-rendered behavior is the operator-visible surface).

### AC.PHRG.S — Seal-diff discipline

`git diff --name-only <plan-commit>..<seal-commit>` shows changes ONLY under:

- `docs/papers/odd-methodology.html` (regenerated HTML asset)
- `docs/experiments/paper-html-regeneration-hard-smoke.md` (slug-named smoke writeup)
- `docs/STATE.md`
- `docs/release-roadmap.md`
- `docs/FUTURE_IDEAS_DRAFT.md`
- `docs/plans/paper-html-regeneration.md`
- `docs/plans/paper-html-regeneration.manifest.yaml`
- `plugins/dev-sdlc/seals/SEAL_COMMIT.paper-html-regeneration`
- `plugins/dev-sdlc/tests/SEAL_COMMIT`
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` (BASELINE pointer auto-bump at seal-time — bookkeeping; pre-included in this allow-list per the plan-doc-template-auto-bump-fence convention)

NO entries in pyproject.toml; NO entries in any framework/* component; NO `__version__` updates; NO test file additions or removals; NO touch of the markdown source-of-truth (`docs/papers/odd-methodology.md`).

**Verdict GREEN if:** `git diff --name-only <plan-commit>..<seal-commit>` matches the allow-list above with zero unlisted entries.

**Verdict YELLOW if:** all entries match BUT a benign extra (e.g., a docs/ entry not in the allow-list) appears — tighten allow-list doc-only post-build per `feedback_loose_AC_text_fix_AC_not_implementation` if intent matched.

**Verdict RED if:** any entry outside fence appears (e.g., pyproject.toml bump, framework/* edit, markdown source-of-truth edit).

`outcome-altitude: false`.

---

## §5 — Decisions builder rules at build time

### D-PHRG.1 — Path A (pandoc) over Path B (custom markdown→HTML conversion script)

**Empirical context:** pandoc not installed at cycle-start (`which pandoc` → exit 1); homebrew available (`/opt/homebrew/bin/brew`). Markdown source-of-truth is structurally vanilla GFM (5 tables + ordered/unordered lists + emphasis + strong + code spans + headings + horizontal rules; NO code fences, NO footnotes, NO task lists per pre-source-edit grep). Path A requires ~30s install + ~2s regen. Path B requires authoring + maintaining a custom markdown→HTML conversion script in `framework/tools/loam/` (~1.5-3h authoring, plus future maintenance for any markdown feature the script doesn't cover).

**Ruling:** Path A. Cheaper to ship; uses standard tooling; markdown is structurally vanilla; pandoc is widely available across systems. Path B captured as new FIDRAFT F-PAPER-REGEN-CUSTOM-SCRIPT for follow-on if a future scenario surfaces value (e.g., system without pandoc; reproducibility gate needing zero system-tool dependencies).

### D-PHRG.2 — Canonical pandoc invocation

**Ruling:** the canonical invocation is:

```
pandoc \
  --from gfm+pipe_tables \
  --to html5 \
  --standalone \
  --metadata title="Objective-Driven Design: Methodology Description and Case-Study Observations from LLM-Authored Software" \
  --include-in-header=<css-template-file> \
  docs/papers/odd-methodology.md \
  --output docs/papers/odd-methodology.html
```

Where `<css-template-file>` is a file containing the CSS template block extracted verbatim from `cfcb03f`'s HTML `<style>...</style>` content (the `:root` + `@media (prefers-color-scheme: dark)` + responsive `@media (max-width: 640px)` block). The CSS template content is captured in the smoke writeup §3 so the invocation is reproducible from the committed artefacts alone.

The `--metadata title="..."` flag overrides pandoc's default behavior of using the first H1 as the document title; we set it explicitly to v19's title so the `<title>` element is correct even if pandoc's H1-extraction default behavior changes.

The `--include-in-header` flag injects the CSS template inside the `<head>` between the title and the `</head>` closer; pandoc wraps it in a `<style>` block automatically when the included content already starts with `<style>`. We pass a `.css` file with the raw CSS (no wrapping `<style>` tags); pandoc treats it as an HTML fragment and includes it as-is — we wrap the file's content in `<style>...</style>` ourselves before passing.

Idempotence is verified via `sha256sum docs/papers/odd-methodology.html` before vs after a second invocation (smoke writeup §3.4).

### D-PHRG.3 — Single dev-sdlc seal anchor (docs/single-component PATCH convention)

Matches v0.10.5 / v0.10.4 / v0.10.3 / v0.10.2 PATCH precedent for single-component PATCHes. `framework/tools/loam/` NOT touched; `docs/papers/` admitted via the manifest's `extra_allowed_prefixes` (a deliberate addition for this PATCH's scope; the existing universal-paths admission shape covers `docs/plans/`, `docs/experiments/`, `docs/design/`, `docs/examples/` but not `docs/papers/`).

**Ruling:** dev-sdlc seal anchor with `extra_allowed_prefixes: [docs/papers/]`.

### D-PHRG.4 — pyproject.toml versions stay at 0.10.0 (PATCH discipline)

Per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1 / v0.10.2 / v0.10.3 / v0.10.4 / v0.10.5 precedent: PATCHes ride the predecessor MINOR's per-component-version. v0.10.0 bumped all 30 component pyprojects from 0.9.0 → 0.10.0. v0.10.6 (this PATCH) does NOT touch any pyproject.toml.

**Ruling:** zero pyproject.toml edits.

### D-PHRG.5 — Markdown source-of-truth NOT edited

**Ruling:** scope to regen-only — `docs/papers/odd-methodology.md` is NOT edited. Any content drift between v19 markdown and the regenerated HTML is structural pandoc-rendering only (e.g., header-anchor IDs, ordered-list start numbers, smart-quote normalization); content correspondence is verified at AC.PHRG.1.

### D-PHRG.6 — CSS template extracted verbatim (no styling refresh)

**Ruling:** CSS template is extracted verbatim from `cfcb03f`'s `<style>` block. No styling refresh, no font-stack update, no spacing tweak. The deleted HTML's CSS template was authored alongside the original v0.9.0 staging and is the reference point for "what the HTML should look like." Any styling refresh is captured as a follow-on FIDRAFT (none captured at this PATCH cycle).

### D-PHRG.7 — Title metadata explicit (overrides pandoc's H1-extraction default)

**Ruling:** the `--metadata title="..."` flag is set explicitly to v19's title in the pandoc invocation. Belt-and-suspenders: pandoc's default behavior is to use the first H1 as the document title, which would also produce v19's correct title since the markdown's first H1 is v19's title; but explicit is better than implicit, and this guards against any future pandoc behavior change OR markdown front-matter addition.

---

## §6 — Out of scope (explicit)

- Editing the markdown source-of-truth (`docs/papers/odd-methodology.md`) — D-PHRG.5.
- Adding paper content / sections / new citations.
- Adding a `framework/tools/loam/` script for markdown→HTML conversion (Path B; D-PHRG.1).
- Promoting the CSS to a standalone file under `docs/papers/` (out of scope; captured as F-PAPER-CSS-EXTRACT-TO-FILE for follow-on if a second paper enters the corpus).
- Styling refresh (font-stack update, spacing tweak, color-palette refresh) — D-PHRG.6.
- Bumping any component's pyproject.toml version (D-PHRG.4).
- Adding a `--paper-regen` flag to `loam` CLI or any other CLI surface.
- Touching any framework/* source.
- Touching any test file.
- Bundling with the F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN cycle (separate scope per dispatch brief).
- `git commit --amend` (HARD HALT #4).
- Any other FIDRAFT entry beyond F-PAPER-HTML-REGEN (verified empirically: no other FIDRAFT references F-PAPER-HTML-REGEN as a blocker / dep / unblocker).

---

## §7 — HARD HALTs (build-time)

1. **Out-of-fence edit discovered as necessary mid-build.** If any line beyond the named files needs to change for correctness, halt and surface for owner ruling. Do NOT silently extend scope.
2. **Empirical-recheck-before-halt discipline.** If you reach a "this is impossible" / "structurally infeasible" conclusion (e.g., "pandoc can't handle this markdown feature" / "dynamic-theme can't be verified empirically"), run the 4-step discipline: state evidence; ≥3 alternative hypotheses; empirically test each; halt only after confirmation of structural infeasibility.
3. **Halt-and-surface ODD violations** including in surrounding code per `feedback_subagent_odd_violation_halt`. If a non-target line in the named files violates ODD §2.5 (non-objective code), surface as halt-and-surface finding in §status; do NOT silently fix.
4. **No `--amend`** per `feedback_no_amend_in_agent_dispatches`. If a corrective is needed post-source-edit, create a NEW commit. The collapse of audit trail via `--amend` is forbidden.
5. **Pandoc install fails AND custom-script path looks like >2h work.** Halt; surface for owner ruling on Path A vs B vs defer.
6. **Dynamic-theme behavior cannot be verified empirically.** No headless-browser tool, no Playwright, no system-theme programmatic toggle path → halt; surface for fallback verification path (manual inspection of CSS literal values + `osascript` automation if available).
7. **Regenerated HTML doesn't match the markdown source-of-truth in critical ways.** Title wrong, sections missing, code blocks corrupted → halt; surface diff.
8. **Test regression you cannot trace to your edit.** If the release-CLI test suite (98 tests baseline excluding 7 pre-existing Python-3.9 entry-point F-TF artefacts) fails post-edit and the failure mode is not obviously this PATCH's, halt and surface. (Note: this PATCH adds NO test files; failures should be impossible — regression check is purely defensive.)

---

## §8 — Dependencies

- v0.10.5 PATCH SHIPPED PUBLIC (sealed `da53584`; published `33ee5cb`; predecessor for build-forward per `feedback_build_forward_on_publish_pending`).
- v0.9.0 MINOR (`odd-paper-methodology-publish` — the MINOR that surfaced this defect by deferring the HTML render at D-ODDPAPER.5.2 Path C; sealed `4a4535f`; published `af57cff`).
- v0.6.0 release-CLI substrate (the `loam release` verb + post-ship review block; this PATCH ships through the release-CLI gates — AC.PHRG.S verifies the seal-diff allow-list).
- pandoc (system tool installed via `brew install pandoc` at source-edit time; first cycle-time dependency on pandoc).
- F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline (captured 2026-05-14 d9776ba) — verified empirically that no other FIDRAFT entries reference F-PAPER-HTML-REGEN as a blocker / dep / unblocker.
- `feedback_dynamic_theme_for_generated_documents` (the discipline the regenerated HTML's CSS preservation honors structurally).

---

## §9 — Estimated AI-time

| Stage | Estimated band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring | 15-25 min | ~20 min |
| Source-edit (pandoc install + CSS template extraction + regen + slug-named smoke writeup with both-modes dynamic-theme verification + STATE/roadmap admin + FIDRAFT flip) | 15-30 min | ~22 min |
| `loam amend validate` + manifest baseline backfill + `apply` + `seal` | 5-10 min | ~7 min |
| §13 §status backfill commit + roadmap-row seal-SHA backfill | 3-5 min | ~4 min |
| **Total** | **~38-70 min** | **~53 min** |

In-band against the FIDRAFT capture's 30-60 min band (~45 min midpoint). Slightly over-band on the upper edge because the dynamic-theme verification adds a discrete browser-render check that the FIDRAFT capture didn't enumerate. Per `feedback_duration_estimation_rubric`: tool-call estimate ~250-400 calls × 0.1-0.15 min/call = 25-60 min raw; ~53 min midpoint accounts for parallel tool calls reducing critical path.

Owner gate-review time is separate (depends on dispatcher availability for publish ratification per ASK-FIRST).

---

## §11 — Authority chain

1. `docs/release-versioning-policy.md` (PATCH classification)
2. `feedback_version_numbers_at_release_time` (version derived at build-commence-time; `next_PATCH(v0.10.5) = v0.10.6`)
3. `feedback_scope_descriptive_ac_ids` (AC family `AC.PHRG.*`; slug `paper-html-regeneration`)
4. `feedback_plan_before_code` (plan-doc + manifest BEFORE source edits)
5. v0.9.0 ODD methodology paper publish MINOR (the change that deferred this; `odd-paper-methodology-publish`)
6. F-PAPER-HTML-REGEN FIDRAFT (the entry this PATCH closes)
7. F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH (discipline for flipping dependent FIDRAFT entries when an unblocker lands; verified no dependents exist)
8. F-CYCLE-ARTEFACT-SLUG-NAMING (slug-named smoke writeup at `docs/experiments/paper-html-regeneration-hard-smoke.md`)
9. `feedback_dynamic_theme_for_generated_documents` (the discipline AC.PHRG.2 + D-PHRG.6 honor structurally)
10. `feedback_loose_AC_text_fix_AC_not_implementation` (AC.PHRG.1 outcome-shape framing rather than implementation-shape)
11. `feedback_subagent_odd_violation_halt` (HARD HALT #3)
12. `feedback_no_amend_in_agent_dispatches` (HARD HALT #4)
13. `feedback_duration_estimation_rubric` (§9)
14. `feedback_build_forward_on_publish_pending` (§8 — v0.10.5 sealed-public; v0.10.6 builds forward)
15. `feedback_principle_application_front_load_and_audit` (turn-start principle walk)

---

## §12 — Source items (FIDRAFT entries closed by this PATCH)

- **F-PAPER-HTML-REGEN** (`docs/FUTURE_IDEAS_DRAFT.md:278`) — captured 2026-05-13 from v0.9.0 ODD paper publish build-time decision D-ODDPAPER.5.2 Path C. Activation gate: "next paper-edit cycle OR pre-v1.0 surface cleanup." This PATCH dispatches against the second activation gate (pre-v1.0 surface cleanup). Status flips to RESOLVED in source-edit commit; entry preserved with RESOLVED block citing this plan-doc + smoke writeup paths.

---

## §13 — §status

**Build cycle:** TBD-AT-SEAL.

**Plan-doc commits:** plan-doc + manifest TBD-AT-COMMIT; source-edit TBD-AT-COMMIT; manifest baseline backfill TBD-AT-COMMIT; apply TBD-AT-COMMIT; seal TBD-AT-COMMIT.

### AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.PHRG.1 — Regenerated HTML matches v19 markdown source-of-truth | TBD | TBD-AT-SOURCE-EDIT |
| AC.PHRG.2 — Dynamic-theme prefers-color-scheme preserved + functional | TBD | TBD-AT-SOURCE-EDIT |
| AC.PHRG.3 — Reproducible regen mechanism documented + idempotent | TBD | TBD-AT-SOURCE-EDIT |
| AC.PHRG.4 — Outcome-altitude dogfood probe | TBD | TBD-AT-SOURCE-EDIT |
| AC.PHRG.S — Seal-diff discipline | TBD | TBD-AT-SEAL |

### AI-time actuals

| Stage | Estimated (§9) | Actual |
|---|---|---|
| Plan-doc + manifest authoring | 15-25 min | TBD-AT-SEAL |
| Source-edit | 15-30 min | TBD-AT-SEAL |
| `loam amend validate` + apply + seal | 5-10 min | TBD-AT-SEAL |
| §13 §status backfill | 3-5 min | TBD-AT-SEAL |
| **Total** | **~38-70 min** | TBD-AT-SEAL |

### Halt-and-surface findings

TBD-AT-SEAL.

---

## §14 — Method decisions

Plan-doc's §5 names the build-time decisions (D-PHRG.{1,2,3,4,5,6,7}). Each is a deterministic ruling at plan-time; no in-flight builder rulings expected unless a HARD HALT fires.
