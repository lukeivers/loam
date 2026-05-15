# Paper HTML regeneration — HARD smoke writeup

**Cycle:** v0.10.6 PATCH (`paper-html-regeneration`).
**Date:** 2026-05-14.
**Slug:** `paper-html-regeneration` (per `F-CYCLE-ARTEFACT-SLUG-NAMING`).
**Plan-doc:** `docs/plans/paper-html-regeneration.md`.
**Predecessor sealed:** v0.10.5 (seal `da53584`; published `33ee5cb`).

---

## §1 — Stage 1: pandoc install verification

**Pre-source-edit baseline:**

```
$ which pandoc
(exit 1: pandoc not found)
```

Pandoc was absent from the dispatcher's machine at cycle-start (matches the v0.9.0 D-ODDPAPER.5.2 Path C trigger condition). Homebrew available at `/opt/homebrew/bin/brew`.

**Install:**

```
$ brew install pandoc
```

(Standard brew install; pulls pandoc + dependencies.)

**Post-install verification:**

```
$ which pandoc
/opt/homebrew/bin/pandoc

$ pandoc --version | head -3
pandoc 3.9.0.2
Features: +server +lua
Scripting engine: Lua 5.4
```

Pandoc 3.9.0.2 installed. Stage 1 GREEN.

---

## §2 — Stage 2: regen invocation + structural verification

### §2.1 — CSS template extraction

The CSS template was extracted verbatim from the deleted HTML at `cfcb03f`:

```
$ git show cfcb03f:docs/papers/odd-methodology.html | awk '/<style>/,/<\/style>/' > /tmp/css-block.html
$ wc -l /tmp/css-block.html
     165 /tmp/css-block.html
```

The extracted block contains: opening `<style>` tag; `:root` block defining 13 CSS variables for light-mode (`--bg`, `--bg-card`, `--bg-table-alt`, `--bg-quote`, `--fg`, `--fg-secondary`, `--fg-muted`, `--accent`, `--accent-strong`, `--link`, `--link-hover`, `--border`, `--border-strong`); `@media (prefers-color-scheme: dark)` block redefining all 13 variables for dark-mode; element selectors for `body`, `.container`, `h1`/`h2`/`h3`, `p`/`li`, `.abstract`, `a`/`a:hover`, `hr`, `table`/`thead`/`tbody`/`th`/`td`, `code`, `ol`/`ul`, `blockquote`, `strong`/`em`, `.references`, `.ref-tail`; responsive `@media (max-width: 640px)` mobile breakpoint; closing `</style>` tag.

The CSS template content is reproduced verbatim at §6 of this writeup so future regens can re-extract it without replaying the git-archaeology step.

### §2.2 — Canonical pandoc invocation

```
pandoc \
  --from gfm+pipe_tables \
  --to html5 \
  --standalone \
  --metadata pagetitle="Objective-Driven Design: Methodology Description and Case-Study Observations from LLM-Authored Software" \
  --include-in-header=/tmp/css-block.html \
  docs/papers/odd-methodology.md \
  --output docs/papers/odd-methodology.html
```

**Notes on flags:**

- `--from gfm+pipe_tables` — GitHub-flavored Markdown reader with pipe-tables extension (the markdown source uses pipe tables, no other GFM-specific features per pre-cycle grep: 0 code fences, 0 footnotes, 0 task lists).
- `--to html5` — HTML5 output.
- `--standalone` — produce a complete document with `<head>` + `<body>` (not just a fragment).
- `--metadata pagetitle="..."` — sets the `<title>` element directly without injecting an `<h1 class="title">` block (pandoc's default `--metadata title=...` injects BOTH `<title>` and `<h1 class="title">`, which would duplicate the markdown's first H1; see §2.4 for the duplication-fix history).
- `--include-in-header=/tmp/css-block.html` — injects the CSS `<style>` block inside `<head>` between pandoc's default styles and the `</head>` closer (cascade order means the custom CSS overrides any conflicting pandoc default).

### §2.3 — Output verification

```
$ ls -la docs/papers/odd-methodology.html
-rw-r--r--@ 1 lukeivers  staff  124236 May 14 20:02 docs/papers/odd-methodology.html

$ wc -l docs/papers/odd-methodology.html
2511 docs/papers/odd-methodology.html
```

124KB / 2511 lines. Compared to the deleted `cfcb03f` HTML (32KB / 443 lines), the regenerated file is ~3.9× larger because it carries pandoc's default styles in addition to the custom CSS template, and the v19 markdown is ~30% longer than the iteration that produced `cfcb03f` (629 lines vs the earlier draft).

**Title verification (AC.PHRG.1 #1):**

```
$ grep -nE '<title>' docs/papers/odd-methodology.html
7:  <title>Objective-Driven Design: Methodology Description and Case-Study
```

Continues on line 8: `Observations from LLM-Authored Software</title>`. Title text matches v19's `# ` heading verbatim (NOT the deleted HTML's stale "Outcome-Altitude Acceptance for LLM-Authored Software"). GREEN.

**First H1 verification (AC.PHRG.1 #1):**

```
$ grep -nE '<h1' docs/papers/odd-methodology.html | head -2
341:<h1
```

Continues with: `id="objective-driven-design-methodology-description-and-case-study-observations-from-llm-authored-software">Objective-Driven Design: Methodology Description and Case-Study Observations from LLM-Authored Software</h1>`. Single H1 (no duplication), correct title text. GREEN.

**H2 section count (AC.PHRG.1 #2):**

```
$ grep -cE '<h2' docs/papers/odd-methodology.html
10
$ grep -cE '^## ' docs/papers/odd-methodology.md
10
```

10 H2 sections in markdown → 10 `<h2>` elements in HTML. Match. GREEN.

**Table count (AC.PHRG.1 #4):**

```
$ grep -cE '<table' docs/papers/odd-methodology.html
12
$ grep -cE '^\|[ -:|]+\|$' docs/papers/odd-methodology.md
12
```

12 tables in markdown (counted via the `|---|` separator-row pattern) → 12 `<table>` elements in HTML. Match. GREEN.

**Style block + dark-mode block presence (AC.PHRG.2 #1, #2):**

```
$ grep -cE '<style>' docs/papers/odd-methodology.html
2
$ grep -cE 'prefers-color-scheme: dark' docs/papers/odd-methodology.html
1
$ grep -cE '@media \(max-width: 640px\)' docs/papers/odd-methodology.html
1
```

Two `<style>` blocks: pandoc's default (line 8-172) + the custom CSS template (line 173-337). Cascade order means custom-after-default, so custom wins for any conflicting selector. The `prefers-color-scheme: dark` block is present (line 184); the responsive mobile breakpoint is present. GREEN.

**CSS color value preservation (AC.PHRG.2 #1, #2):**

```
$ grep -nE 'fbfaf7|0c0a09|fcd34d|92400e' docs/papers/odd-methodology.html
175:      --bg: #fbfaf7;
182:      --accent: #92400e;
191:        --bg: #0c0a09;
198:        --accent: #fcd34d;
```

Light-mode `--bg: #fbfaf7` + `--accent: #92400e` preserved. Dark-mode `--bg: #0c0a09` + `--accent: #fcd34d` preserved. All 13 light-mode variables + 13 dark-mode variables verified by visual inspection of the embedded CSS block. GREEN.

### §2.4 — Title-duplication fix history

**First-pass invocation** used `--metadata title="..."` (the obvious choice from pandoc's docs). Result: pandoc auto-injected an `<h1 class="title">` block at the top of `<body>`, which duplicated the markdown's first `# ` H1 in the rendered output. Empirical observation: both H1 elements rendered visibly in the screenshots, with identical text.

**Fix:** switched to `--metadata pagetitle="..."` which sets the `<title>` element only (not the auto-injected title block). Result: single H1 in rendered output (from the markdown's `# ` heading); correct `<title>` element.

This is the canonical invocation per §2.2. The history is captured here for the next paper-edit cycle to avoid repeating the discovery.

Stage 2 GREEN.

---

## §3 — Stage 3: dynamic-theme behavior verification (both modes)

### §3.1 — Verification mechanism

Playwright + Chromium headless. Available at `/Users/lukeivers/.pyenv/shims/playwright`. Two browser contexts spawned with `color_scheme="light"` and `color_scheme="dark"` respectively; each loads `file:///Users/lukeivers/loam/docs/papers/odd-methodology.html`; each reads `getComputedStyle(document.body).backgroundColor`, `.color`, and `getComputedStyle(document.querySelectorAll('h2')[0]).color`. Screenshots captured at `viewport={width: 800, height: 600}` for visual verification.

Probe script captured at `/tmp/verify_theme.py` (referenced from this writeup; the script is inline below for reproducibility):

```python
"""Verify dynamic-theme prefers-color-scheme behavior in both modes via Playwright."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

html_path = Path("/Users/lukeivers/loam/docs/papers/odd-methodology.html").resolve()
url = f"file://{html_path}"

with sync_playwright() as p:
    browser = p.chromium.launch()
    for color_scheme in ["light", "dark"]:
        ctx = browser.new_context(color_scheme=color_scheme)
        page = ctx.new_page()
        page.goto(url)
        bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
        fg = page.evaluate("getComputedStyle(document.body).color")
        h2 = page.evaluate("getComputedStyle(document.querySelectorAll('h2')[0]).color")
        print(f"{color_scheme.upper()} bg={bg} fg={fg} h2-accent={h2}")
        ctx.close()
    browser.close()
```

### §3.2 — Light-mode probe

```
LIGHT bg=rgb(251, 250, 247) fg=rgb(28, 25, 23) h2-accent=rgb(120, 53, 15)
```

- `bg=rgb(251,250,247)` = `#fbfaf7` ← matches `--bg` light-mode value verbatim.
- `fg=rgb(28,25,23)` = `#1c1917` ← matches `--fg` light-mode value verbatim.
- `h2-accent=rgb(120,53,15)` = `#78350f` ← matches `--accent-strong` light-mode value verbatim (H2 selector uses `color: var(--accent-strong)`).

Light-mode rendering applies the light-mode CSS variables correctly. GREEN.

**Screenshot:** `docs/experiments/paper-html-regeneration-light-mode.png` (800×600 viewport, top of paper). Visually: cream `#fbfaf7` background, dark serif body text, brown-rust H2 accent ("On this artefact"), bold strong words rendered in the same accent tone, italic v19-draft subtitle in muted secondary color. Looks intentional — published-paper aesthetic.

### §3.3 — Dark-mode probe

```
DARK  bg=rgb(12, 10, 9) fg=rgb(245, 245, 244) h2-accent=rgb(253, 230, 138)
```

- `bg=rgb(12,10,9)` = `#0c0a09` ← matches `--bg` dark-mode value verbatim.
- `fg=rgb(245,245,244)` = `#f5f5f4` ← matches `--fg` dark-mode value verbatim.
- `h2-accent=rgb(253,230,138)` = `#fde68a` ← matches `--accent-strong` dark-mode value verbatim.

Dark-mode rendering applies the dark-mode CSS variables correctly. The `prefers-color-scheme: dark` media query fires when the browser context is set to dark color scheme, and all 13 CSS variables are redefined to their dark-mode values. GREEN.

**Screenshot:** `docs/experiments/paper-html-regeneration-dark-mode.png` (800×600 viewport, top of paper). Visually: near-black `#0c0a09` background, light off-white serif body text, golden-yellow H2 accent ("On this artefact"), bold strong words rendered in the lighter accent tone (`#fde68a`), italic v19-draft subtitle in muted dark-mode secondary color. Maintains contrast hierarchy + visual structure intentionally. Looks intentional — not muddy / not broken / not just "functional dark mode."

### §3.4 — Idempotence verification

```
$ shasum -a 256 docs/papers/odd-methodology.html
28ed1f1b0db4b07ef6de6e55af42df8442765bbe04665957e41ae4478f93e577  docs/papers/odd-methodology.html

$ pandoc --from gfm+pipe_tables --to html5 --standalone \
    --metadata pagetitle="Objective-Driven Design: Methodology Description and Case-Study Observations from LLM-Authored Software" \
    --include-in-header=/tmp/css-block.html \
    docs/papers/odd-methodology.md \
    --output /tmp/odd-methodology-rerun.html

$ shasum -a 256 /tmp/odd-methodology-rerun.html
28ed1f1b0db4b07ef6de6e55af42df8442765bbe04665957e41ae4478f93e577  /tmp/odd-methodology-rerun.html

$ diff -q docs/papers/odd-methodology.html /tmp/odd-methodology-rerun.html
(no output — files identical)
```

Hashes match: `28ed1f1b0db4b07ef6de6e55af42df8442765bbe04665957e41ae4478f93e577`. The pandoc invocation is deterministic given the same source markdown + CSS template. AC.PHRG.3 idempotence GREEN.

Stage 3 GREEN.

---

## §4 — AC verdict matrix (smoke summary)

| AC | Verdict | Evidence |
|---|---|---|
| AC.PHRG.1 — Regenerated HTML matches v19 markdown source-of-truth | GREEN | §2.3 — `<title>` + `<h1>` carry v19's title; 10/10 H2 sections match; 12/12 tables render as `<table>` elements; emphasis + strong + code spans rendered. |
| AC.PHRG.2 — Dynamic-theme `prefers-color-scheme` preserved + functional | GREEN | §2.3 — `<style>` block carries the full custom CSS template with `:root` light-mode variables + `@media (prefers-color-scheme: dark)` redefinition + responsive mobile breakpoint. §3.2 + §3.3 — Playwright probe confirms light-mode renders with `#fbfaf7` bg + `#1c1917` fg + `#78350f` accent; dark-mode renders with `#0c0a09` bg + `#f5f5f4` fg + `#fde68a` accent. Both modes look intentional per `feedback_dynamic_theme_for_generated_documents` quality bar. |
| AC.PHRG.3 — Reproducible regen mechanism documented + idempotent | GREEN | §2.2 — pandoc command line documented verbatim. §6 — CSS template stored verbatim. §3.4 — `sha256sum` before vs after second invocation match (`28ed1f1b...`). |
| AC.PHRG.4 — Outcome-altitude dogfood probe (browser-render verification) | GREEN | §3 — Playwright + Chromium headless probe across both color schemes; computed-style values match CSS variable definitions exactly; screenshots saved adjacent to this writeup. |
| AC.PHRG.S — Seal-diff discipline | TBD-AT-SEAL | Verified at seal-time via `git diff --name-only <plan-commit>..<seal-commit>`; expected allow-list matches plan-doc §3 + AC.PHRG.S enumeration. |

All 4 outcome ACs GREEN. AC.PHRG.S verified at seal-time per standard cycle convention.

---

## §5 — Halt-and-surface findings

**No HARD HALTs fired in-cycle.**

**Pandoc-not-installed pre-condition:** resolved via `brew install pandoc` (Stage 1). The v0.9.0 D-ODDPAPER.5.2 Path C trigger condition (pandoc absent → defer HTML) was the FIDRAFT capture's primary blocker; this PATCH dispatches the install + regen as the closure path.

**Dynamic-theme empirical-verification:** Playwright + Chromium headless was available; no fallback path needed. If Playwright had been absent, the fallback was `osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to true'` followed by manual screenshot capture via `screencapture` and visual inspection — captured here as the future-fallback note.

**Title-duplication discovery (§2.4):** pandoc's `--metadata title="..."` injects both `<title>` AND an `<h1 class="title">` block, which duplicated the markdown's first H1 in the rendered output. Fix: switched to `--metadata pagetitle="..."` which sets `<title>` only. Captured in §2.4 of this writeup so the next paper-edit cycle doesn't re-discover.

**Dual-`<style>`-block observation (§2.3):** pandoc's default `<style>` block stays in the output alongside the custom CSS template (which is included via `--include-in-header`). Cascade order resolves correctly (custom-after-default; custom wins for conflicting selectors). Output is functionally correct but ~3.9× larger than the deleted `cfcb03f` HTML which had only the custom CSS. A future optimization would strip pandoc's default `<style>` block via a Lua filter or a `--variable highlighting-css=""` approach; captured as informational here, not actionable for this PATCH.

**F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline verified:**

```
$ grep -rn "F-PAPER-HTML-REGEN" docs/
docs/FUTURE_IDEAS_DRAFT.md:278:- **F-PAPER-HTML-REGEN — Regenerate ...**
```

Single reference (the entry itself). No dependent FIDRAFT entries reference F-PAPER-HTML-REGEN as blocker / dep / unblocker; no flip-on-unblock action needed beyond the entry itself.

**One FIDRAFT entry flipped to RESOLVED:** F-PAPER-HTML-REGEN at `docs/FUTURE_IDEAS_DRAFT.md:278`; entry preserved with RESOLVED block citing this PATCH cycle's plan-doc + smoke writeup paths.

**No new FIDRAFT entries captured at AC-time;** D-PHRG.1 captured F-PAPER-REGEN-CUSTOM-SCRIPT (Path B follow-on if pandoc unavailable) + F-PAPER-CSS-EXTRACT-TO-FILE (CSS-to-standalone-file follow-on if a second paper enters the corpus) at plan-time as conditional captures. Neither activated this cycle. (Captured in plan-doc §5; not separately recorded in FUTURE_IDEAS_DRAFT.md unless the activation gate fires.)

**Empirical-recheck-before-halt discipline:** never fired (the regen had an unambiguous fix-target derivable from the FIDRAFT capture's proposed-shape line + plan-doc D-PHRG.{1,2,3,4,5,6,7} rulings).

**One AC text disambiguation at plan-time** (per `feedback_loose_AC_text_fix_AC_not_implementation`): AC.PHRG.1 was authored at outcome-shape ("matches v19 markdown source-of-truth") rather than implementation-shape ("pandoc converts markdown to HTML"). Method (pandoc + which flags) stays builder's call.

---

## §6 — CSS template (verbatim from `cfcb03f`)

The CSS block below is what `--include-in-header=/tmp/css-block.html` injects into the regenerated HTML. Reproduce verbatim into a `.html` (or `.css` with `<style>...</style>` wrapper if pandoc treats raw CSS differently in a future version) file before re-running the pandoc invocation. The block is also retrievable via `git show cfcb03f:docs/papers/odd-methodology.html | awk '/<style>/,/<\/style>/'`.

```html
<style>
  :root {
    --bg: #fbfaf7;
    --bg-card: #ffffff;
    --bg-table-alt: #f3f1ec;
    --bg-quote: #f5f5f4;
    --fg: #1c1917;
    --fg-secondary: #44403c;
    --fg-muted: #78716c;
    --accent: #92400e;
    --accent-strong: #78350f;
    --link: #1d4ed8;
    --link-hover: #1e40af;
    --border: #e7e5e4;
    --border-strong: #d6d3d1;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0c0a09;
      --bg-card: #1c1917;
      --bg-table-alt: #292524;
      --bg-quote: #1c1917;
      --fg: #f5f5f4;
      --fg-secondary: #d6d3d1;
      --fg-muted: #a8a29e;
      --accent: #fcd34d;
      --accent-strong: #fde68a;
      --link: #93c5fd;
      --link-hover: #bfdbfe;
      --border: #292524;
      --border-strong: #44403c;
    }
  }
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--fg);
    font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif;
    line-height: 1.62;
    font-size: 17px;
  }
  .container {
    max-width: 720px;
    margin: 0 auto;
    padding: 28px 22px 80px;
  }
  h1 {
    font-size: 1.55rem;
    margin: 0.2em 0 0.6em;
    color: var(--fg);
    line-height: 1.25;
    font-weight: 700;
    letter-spacing: -0.01em;
  }
  h2 {
    font-size: 1.18rem;
    margin: 2em 0 0.5em;
    color: var(--accent-strong);
    font-weight: 700;
    border-bottom: 1px solid var(--border-strong);
    padding-bottom: 5px;
  }
  h3 {
    font-size: 1.05rem;
    margin: 1.5em 0 0.4em;
    color: var(--fg);
    font-weight: 700;
  }
  p, li {
    color: var(--fg);
    margin: 0.7em 0;
  }
  .abstract {
    font-style: italic;
    color: var(--fg-secondary);
    border-left: 3px solid var(--border-strong);
    padding: 4px 0 4px 16px;
    margin: 1.4em 0;
  }
  .abstract::before {
    content: "Abstract";
    display: block;
    font-style: normal;
    font-weight: 700;
    color: var(--accent-strong);
    font-size: 0.92rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  a { color: var(--link); text-decoration: none; border-bottom: 1px solid transparent; transition: border-color 0.15s ease; }
  a:hover { color: var(--link-hover); border-bottom-color: currentColor; }
  hr {
    border: none;
    border-top: 1px solid var(--border-strong);
    margin: 2.4em 0;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.8em 0 1.6em;
    font-size: 0.96rem;
  }
  thead th {
    background: var(--bg-table-alt);
    color: var(--fg);
    font-weight: 700;
    text-align: left;
    padding: 10px 12px;
    border-bottom: 2px solid var(--border-strong);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  }
  tbody td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    color: var(--fg);
    vertical-align: top;
  }
  tbody td:first-child { font-weight: 700; color: var(--accent-strong); white-space: nowrap; }
  code {
    font-family: ui-monospace, "SF Mono", Menlo, Monaco, monospace;
    background: var(--bg-table-alt);
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 0.88em;
    color: var(--fg);
  }
  ol, ul { padding-left: 1.5em; }
  ol li, ul li { margin: 0.5em 0; }
  blockquote {
    border-left: 3px solid var(--border-strong);
    padding: 4px 0 4px 18px;
    margin: 1em 0;
    color: var(--fg-secondary);
    font-style: italic;
  }
  strong { color: var(--accent-strong); font-weight: 700; }
  em { color: var(--fg); }
  .references {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 16px 20px;
    font-size: 0.95rem;
    color: var(--fg-secondary);
  }
  .references ul { margin: 0.4em 0; padding-left: 1.2em; }
  .ref-tail {
    font-size: 0.92rem;
    color: var(--fg-muted);
    font-style: italic;
    margin-top: 1em;
  }
  @media (max-width: 640px) {
    .container { padding: 18px 14px 56px; }
    body { font-size: 16px; }
    h1 { font-size: 1.32rem; }
    h2 { font-size: 1.06rem; }
    h3 { font-size: 1rem; }
    table { font-size: 0.9rem; }
    thead th, tbody td { padding: 7px 8px; }
  }
</style>
```

---

## §7 — Reproducibility recipe (one-paragraph)

To regenerate the HTML in a future paper-edit cycle:

1. Ensure pandoc is installed: `brew install pandoc` (or system-equivalent).
2. Save the CSS template from §6 (or extract via `git show cfcb03f:docs/papers/odd-methodology.html | awk '/<style>/,/<\/style>/'`) to a temp file like `/tmp/css-block.html`.
3. Run the pandoc invocation from §2.2.
4. Verify idempotence via `sha256sum docs/papers/odd-methodology.html` before vs after a second invocation; the hashes match deterministically.
5. (Optional) Re-run the Playwright probe from §3.1 to verify dynamic-theme behavior in both modes.

Total wall-clock for a future regen: ~30 seconds (pandoc-already-installed case) to ~2 minutes (cold install).
