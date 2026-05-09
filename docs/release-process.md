# Loam Release Process

**Status:** canonical (v0.6.0+).
**Authority:** `docs/plans/v0-6-0-release-process.md` (concrete release process plan-doc).
**Composes with:** `docs/release-versioning-policy.md` (SemVer commitment), `docs/release-roadmap.md` (forward-looking objective targets), `feedback_hard_smoke_per_minor_before_publish` (HARD smoke pre-publish gate), `feedback_no_public_action_during_build` (publish is dispatcher action, never builder action).

This is the runbook a dispatcher (or a future session, or another persona) can read end-to-end in five minutes to publish a sealed loam version. The structural mechanism is the `loam release <version>` CLI verb (added in v0.6.0); the runbook documents what that verb checks, how to invoke it, and the manual fallback when the CLI is unavailable.

---

## 1. Pre-publish gates (what `loam release` checks)

Every publish goes through six structural gates before any tag or push happens. The CLI's `--dry-run` flag runs the full gate set + reports verdicts without acting; use it to verify state without committing to publish.

| # | Gate | What it checks | Where it reads |
|---|------|----------------|----------------|
| 1 | `hard-smoke` | HARD smoke writeup exists + contains the literal `GREEN` verdict token | `docs/experiments/<version-slug>-hard-smoke.md` |
| 2 | `acs-verified` | Plan-doc §status / §13 marks every named AC GREEN | `docs/plans/<version-slug>*.md` |
| 3 | `state-shipped` | `STATE.md` mentions the version followed by `SHIPPED` | `docs/STATE.md` |
| 4 | `clean-tree` | `git status --porcelain` returns empty | working tree |
| 5 | `branch-main` | `git branch --show-current` returns `main` | local branch state |
| 6 | `seal-reachable` | `release-roadmap.md` §2 row for the version contains a seal SHA + that SHA is reachable from HEAD | `docs/release-roadmap.md` |

**Gates run all six before reporting.** No short-circuit on first RED — the operator sees the full state in one pass and addresses every failure together rather than chasing them one at a time.

**Each RED gate emits a specific corrective hint.** Generic errors are forbidden by AC.V060.2; if a gate fails with vague guidance, file a defect against `framework/tools/loam/src/loam_cli/release/gates.py`.

---

## 2. The `loam release` invocation

Canonical command sequence after a cycle seals + the publish gate (ASK-FIRST: owner authorization required for any public action):

```bash
# 1. From the canonical loam tree at /Users/lukeivers/loam (or your clone).
cd /Users/lukeivers/loam

# 2. Verify pre-publish state without acting.
loam release v0.X.Y --dry-run

# 3. If gates GREEN + dispatcher has owner authorization, publish.
loam release v0.X.Y

# 4. (Optional) Add a GitHub Release with auto-generated notes.
loam release v0.X.Y --release
```

**Flags:**

- `--dry-run` — runs every gate + reports verdicts; emits the post-ship-review block as a preview; no tag, no push, no `gh release`.
- `--release` — after tag + push, invokes `gh release create <tag>` with notes auto-generated from plan-doc §1 outcome shape + plan-doc §status verdicts + commit log between previous version's seal and this version's seal.

**Idempotency:** re-running `loam release v0.X.Y` against an already-published version (the tag exists on the `origin` remote) emits `v0.X.Y already on origin remote at <SHA>; nothing to do.` and returns rc=0. Safe to re-run.

**Outcome on success:**

1. Annotated tag `v0.X.Y` created at the seal commit (the seal SHA is read from `release-roadmap.md` §2 row); tag message = `v0.X.Y — <objective sentence from §2>`.
2. `git push origin main` + `git push origin v0.X.Y`.
3. (If `--release`) GitHub Release page created at `https://github.com/lukeivers/loam/releases/tag/v0.X.Y`.
4. Post-ship review block emitted to stdout naming the next-scope proposal (read from `release-roadmap.md` §4 priority queue + recent FUTURE_IDEAS_DRAFT captures + major-release eval).

---

## 3. Post-publish state

After a successful `loam release` invocation:

- The version tag is live on `origin/main` — third-party consumers can pin against it.
- `git ls-remote --tags origin` shows the new tag.
- The post-ship review block surfaced a "Next-scope proposal" — the operator ratifies (or revises) the next scope BEFORE the next cycle's first commit. **Pre-1.0 always returns PATCH or MINOR per `release-versioning-policy.md` §1.0.0.** The v1.0 quality-bar event is a separate ratification, not a post-publish-trigger event.

**Things to check next:**

- If the next-scope proposal looks wrong (priorities shifted; a higher-leverage item surfaced in `FUTURE_IDEAS_DRAFT.md`), re-rank the §4 queue + edit the roadmap before authoring the next plan-doc.
- If post-ship review surfaced a `post-1.0-review-needed` verdict (only after v1.0 ships), inspect the accumulated commits since the last major for breaking-change markers + plugin-contract revision evidence per `release-versioning-policy.md` triggers.

---

## 4. Manual fallback (when the CLI is unavailable)

When `loam release` is broken (e.g., during the CLI's own dogfood publish if AC.V060.7 RED) or unavailable, the manual ritual that the CLI mechanises is:

```bash
# 1. Verify each gate manually (mirrors §1 above).
test -f docs/experiments/v0-X-Y-hard-smoke.md && grep -q GREEN docs/experiments/v0-X-Y-hard-smoke.md
# (plan-doc §status check is a manual read)
grep "v0.X.Y SHIPPED" docs/STATE.md
git status --porcelain  # empty?
git branch --show-current  # 'main'?
SEAL_SHA=$(grep "v0.X.Y" docs/release-roadmap.md | grep -oE 'seal `[0-9a-f]+`' | tr -d '`' | awk '{print $2}' | tail -1)
git merge-base --is-ancestor "$SEAL_SHA" HEAD  # rc=0?

# 2. Create annotated tag at the seal commit.
OBJECTIVE=$(grep "| v0.X.Y |" docs/release-roadmap.md | awk -F '|' '{print $3}' | sed 's/^ *//;s/ *$//')
git tag -a v0.X.Y "$SEAL_SHA" -m "v0.X.Y — $OBJECTIVE"

# 3. Push branch + tag.
git push origin main
git push origin v0.X.Y

# 4. (Optional) GitHub Release.
gh release create v0.X.Y --title v0.X.Y --notes "$(cat <<'EOF'
# v0.X.Y

## Outcome shape (the "why")

(paste from plan-doc §1)

## AC verdicts

(paste from plan-doc §status)

## Commits

(paste output from `git log --oneline <prev-seal>..<this-seal>`)
EOF
)"

# 5. Post-ship review (manual): re-read docs/release-roadmap.md §4 + recent
# FUTURE_IDEAS_DRAFT.md captures; ratify (or revise) the next scope before
# the next cycle's first commit.
```

---

## 5. Composes with

- **`loam amend apply` + `loam amend seal`** — the seal commit IS the publish input. No new seal mechanism; `loam release` consumes the seal anchor recorded in `release-roadmap.md` §2.
- **`feedback_hard_smoke_per_minor_before_publish`** — the HARD smoke gate is structural enforcement of the rule; smoke must be GREEN before publish. The gate verifies the writeup's GREEN token; smoke execution itself happens during the cycle (not at publish-time).
- **`feedback_no_public_action_during_build`** — `loam release` is dispatcher action, never builder action. Build agents must NOT invoke `git tag` / `git push` / `loam release` directly; they land their work locally and surface the seal SHA + readiness for publish.
- **ASK-FIRST on public actions** — even the dispatcher invokes `loam release` only after explicit owner authorization. The CLI does NOT auto-publish.

---

## 6. Cross-references

- `loam release --help` — argparse-generated usage summary.
- `docs/plans/v0-6-0-release-process.md` — the plan-doc this runbook implements.
- `docs/release-versioning-policy.md` — SemVer commitment; defines what counts as PATCH / MINOR / MAJOR / hot-patch.
- `docs/release-roadmap.md` — §2 (shipped) + §4 (priority queue); the structural source-of-truth the CLI reads from.
- `docs/STATE.md` — shipped-state record; gate 3 enforces synchronization.
