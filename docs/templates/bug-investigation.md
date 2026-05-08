# Bug investigation — `<short-title-kebab-case>`

> **Template usage:** copy to a workspace-appropriate path. Ephemeral
> investigations live in `<workspace>/.scratch/claude-output/`. Persistent
> investigations that produce durable findings (e.g. graduated to a
> FIDRAFT entry, plan, or amendment) live in
> `docs/investigations/<title>.md`. Replace every `<placeholder>`.
> Sections marked **(required)** must be filled. Sections marked
> **(optional)** are omitted when not applicable — say so explicitly
> rather than leaving the heading with empty body.

---

## 1. Header / metadata (required)

- **Title:** `<short descriptive title>`
- **Date opened:** `YYYY-MM-DD`
- **Severity:** `low | medium | high | critical` — use the rubric:
  - critical: blocks all work; data loss risk
  - high: blocks a workflow; recurrent
  - medium: degrades a workflow; intermittent
  - low: cosmetic / annoyance
- **Observed by:** `<owner | agent-id | both>`
- **Reproduction available:** `yes | partial | no`
- **Status:** `open | investigating | root-caused | fix-proposed | resolved | wont-fix`
- **Related:** `<paths to FIDRAFT entries, memory feedback files, plans, amendments>`

## 2. Observation (required)

> What was observed empirically? Cite logs, transcripts, file states.
> Include exact reproductions when available. Distinguish what was
> directly observed vs what was inferred. Avoid root-cause guesses
> here — they belong in §7.

`<empirical observations with file:line citations or transcript indices>`

## 3. Symptom timeline (required)

> When did it start? Frequency? Pattern (intermittent / consistent /
> triggered by specific event)? Did anything change immediately
> before? If the symptom is binary (works / doesn't), say so.

- **First observed:** `<when, evidence>`
- **Frequency:** `<count, rate, pattern>`
- **Trigger pattern:** `<what events precede the symptom>`
- **Stable vs intermittent:** `<which>`
- **Recent changes that may correlate:** `<config edits, version bumps, env changes>`

## 4. Hypothesis space (required)

> Enumerate candidate causes BEFORE digging into investigation.
> Initial confidence is a guess at this stage — it gets updated in §6.
> The discipline is: name the hypotheses up front so investigation
> doesn't drift toward the first plausible answer.

| # | Hypothesis | Initial confidence | Rationale |
|---|---|---|---|
| H1 | `<one-sentence hypothesis>` | `<low / medium / high>` | `<why this is plausible>` |
| H2 | `<...>` | `<...>` | `<...>` |
| H3 | `<...>` | `<...>` | `<...>` |

## 5. External research (required)

> Search for similar reports / reported bugs / discussions / prior art.
> Cite sources as markdown links. Required surfaces:
> - Vendor / official issue trackers (GitHub issues, vendor docs)
> - Stack Overflow / Discord / Reddit / community forums
> - Blog posts, papers, postmortems
> - Vendor changelogs / release notes for the relevant version
>
> No-prior-art findings are also valuable — record them: "searched
> X, Y, Z — nothing found." Negative evidence narrows hypothesis space.

### 5.1 Search queries used
- `<query 1>`
- `<query 2>`

### 5.2 Findings
- **`<source title>`** ([link](URL)) — `<one-paragraph summary of what
  was found and how it relates to the bug>`
- **`<source title>`** ([link](URL)) — `<...>`
- **No prior art for `<specific angle>`** — searched `<surfaces>`,
  nothing matching `<criteria>`.

### 5.3 Synthesis
> One paragraph: what does the external research collectively say?
> Does it confirm a hypothesis, rule one out, surface a new one?

`<synthesis>`

## 6. Internal investigation (required)

> Code reads, log dives, repro attempts. Cite paths + line numbers
> + commit SHAs. Update hypothesis confidences as evidence accumulates.

### 6.1 Repro attempts
- **Attempt 1:** `<setup>` → `<result>` — confirms / contradicts which hypotheses?
- **Attempt 2:** `<...>`

### 6.2 Code / log walk
- `<file:line>` — `<what was found, how it relates>`
- `<file:line>` — `<...>`

### 6.3 Hypothesis update

| # | Hypothesis | Updated confidence | Evidence-for | Evidence-against |
|---|---|---|---|---|
| H1 | `<...>` | `<low / medium / high / ruled-out / confirmed>` | `<cite>` | `<cite>` |
| H2 | `<...>` | `<...>` | `<...>` | `<...>` |

## 7. Root cause (required)

> What actually causes the bug. Distinguish:
> - **Proximate cause** — the broken thing (e.g. "function returns None
>   when X happens").
> - **Root cause** — the upstream "why is the broken thing broken"
>   (e.g. "the contract doesn't specify behavior for X, so the impl
>   defaults to None").
> - **Class** — the broader pattern this bug belongs to (e.g.
>   "implicit-default-on-unspecified-input"). Useful for §8.3.

- **Proximate cause:** `<...>`
- **Root cause:** `<...>`
- **Class:** `<...>`
- **Confidence:** `<low / medium / high>` — `<why this confidence level>`

If root cause cannot be confidently named after investigation,
say so explicitly. Halt-and-surface beats guessing.

## 8. Recommended fixes (required)

> Categorize. Each option gets cost / risk / blast-radius / who-decides.

### 8.1 Patch the symptom
> Fast, narrow, may not survive the next instance. Use when the root
> cause needs more investigation but the symptom is hurting.

- **Option A:** `<description>` — cost `<low/med/high>` — risk `<low/med/high>` — owner-decides? `<yes/no>`

### 8.2 Fix the root cause
> Slower, broader. Use when root cause is confidently named.

- **Option B:** `<description>` — cost — risk — owner-decides?

### 8.3 Prevent the class
> Slowest, broadest. Adds a structural mechanism that makes the bug
> class hard to recur (e.g. type system, lint rule, hook, schema
> validation). Use when the class is broader than the single bug.

- **Option C:** `<description>` — cost — risk — owner-decides?

### 8.4 Recommendation
> One paragraph. Which option (or combination) does the investigator
> recommend, and why? This is the F2 Ruthless Feedback move — name
> the recommendation, don't punt to "owner decides everything."

`<recommendation>`

## 9. Status + next-action (required)

- **Done in this investigation:** `<...>`
- **Deferred / awaiting owner ruling:** `<...>`
- **New tasks created:** `<TaskCreate IDs or task-list refs>`
- **Memory feedback / FIDRAFT capture:** `<paths if anything was captured>`

## 10. Provenance (optional)

> Links into the broader corpus this investigation composes with.

- **Plan-doc(s):** `<paths>`
- **FIDRAFT entry/entries:** `<paths>`
- **Memory feedback rule(s):** `<paths>`
- **Prior related investigations:** `<paths>`
- **Session transcript reference:** `<session-id, line-ranges if relevant>`

---

*Investigator:* `<who-or-which-agent>` · *Closed:* `<YYYY-MM-DD or "open">`
