# NN ancestor-detection — empirical skippability check on pos3's 46 live-test conflicts

**Date:** 2026-04-27
**Author:** primary persona, autonomous experiment per Luke's "small experiments to resolve doubt" directive
**Audit source:** `/Users/lukeivers/pos3/.pos/sync/f6ca2ed286504ede115ea07f13efc2e3ae6ace8c/audit.yaml`
**Canonical source:** `/Users/lukeivers/ivers-corp-pos-v2/`

## Method

For each of the 46 Class-C conflicts produced by the milestone live-test on pos3:

1. Read pos3's `installed_sha256` (workspace content hash).
2. Walk canonical's `git log --all --follow -- <path>` — every commit that touched that path on any branch.
3. For each historical commit, compute `sha256(git show <commit>:<path>)` and compare to pos3's `installed_sha256`.
4. **Skippable** = workspace content matches some historical commit (workspace is just behind, not edited).
5. **Not skippable** = workspace content matches no historical canonical commit (genuinely diverged).

Script at `/tmp/nn_skip_check.py` (transient).

## Result

```
Total conflicts:        46
NN would SKIP:          45  (97.8%)
NN would NOT skip:       1
Errors:                  0
```

**The single not-skippable path:** `.claude/settings.json` — no match across 13 historical commits. This is the path the live-test resolver correctly verdicted as `inferred-accept-workspace` at 0.88 confidence with the rationale "this is pos3, a derived workspace running active amendments 32-35..."

## Implication for Bundle α scope

**α.1 NN ALONE closes the milestone live-test.**

Cost projection for milestone live-test retry with α.1 alone:
- 45 paths: fast-pathed to `inferred-accept-canonical` via ancestor-match. Zero LLM calls.
- 1 path (`.claude/settings.json`): goes to LLM resolver. Produces `inferred-accept-workspace` (0.88 confidence). ~1,175 tokens / ~30s.
- Total: **1 LLM call / ~1,175 tokens / well under 60s**.

Compare to today's actual live-test: 46 conflicts / timed out at conflict 3 / 50,000 token budget allocated / 2,351 tokens used before halt.

**α.2 (QQ-refined verify-gate) and α.3 (RR --bare flag) remain valuable for the general case** — workspaces with genuine workspace-side edits, where ancestor-detection misses but verify-gate / faster cold-start still help. But for the immediate milestone closure, **α.1 is sufficient and α.2 + α.3 are not on the critical path**.

## Recommendation to Bundle α plan-author

Structure the plan so:

1. **α.1 NN is independently buildable + dispatchable as a stand-alone amendment.** Its scope: ancestor-match in `conflict_detection.py` (or `merge_helper.py` — at the right pre-resolver hook point), with sha256 comparison vs `git log --all --follow` traversal. Integration test: synthetic workspace whose content matches a canonical-ancestor commit, assert resolver is NOT invoked.
2. **α.2 + α.3 remain bundled** as a follow-on if Luke wants them packaged together; OR each becomes its own small amendment.

The dispatch prompt already noted "if build reveals independence, builder splits then." This empirical data **strongly supports the split** — α.1's leverage on the actual milestone path vastly exceeds α.2 + α.3 for this specific case (workspaces just behind canonical).

## Implementation considerations for α.1

- **History walk depth.** `git log --all --follow` returns commits in reverse-chronological order. For most paths, ancestor-match found within 2-4 commits; max observed was 13 (for `.claude/settings.json` — and that one didn't match anywhere). Depth-cap of ~50 commits would catch every realistic case.
- **Caching.** Hashing `git show <commit>:<path>` is cheap (~20ms per shellout). For a 46-conflict pos3 case, total walk-time was ~10s. Could cache per-(commit, path) to avoid redundant lookups across runs of pos-sync.
- **`--all` vs `--first-parent`.** Using `--all` was important — some matches were on side-branches not reachable from HEAD. The script used `--all`.
- **`--follow` flag.** Catches renames; matters for paths that have moved across canonical's history.
- **Comparison shape.** sha256 of byte-content; could also use git's blob OID directly (each blob has a deterministic hash). Either works.
- **Fallback when canonical's git history is shallow / incomplete.** No matches found → fall through to existing resolver path. NN is a fast-path optimization, not a correctness change.

## Skippable conflicts — sample (for reference)

| Path | Matched ancestor commit | Commits checked |
|---|---|---|
| `.gitignore` | f7cb781 | 3 |
| `docs/FUTURE_IDEAS_DRAFT.md` | 19108ea | 3 |
| `primary-persona/src/__init__.py` | 6e1cb0c | 3 |
| `objective-tracker/src/runtime.py` | be7737b | 2 |
| `self-upgrade/src/self_upgrade/cli.py` | 8299d47 | 3 |
| `tools/pos-amend/templates/plan/dev-discipline.md` | 6f7e849 | 2 |

(Full list in the script's tail output; transient at `/tmp/nn_skip_check.py.out` if regenerated.)

## Composes with — pre-existing #56 surface

- `workspace-sync/src/workspace_sync/conflict_detection.py` — currently classifies a path as Class C when both sides differ. NN inserts a content-vs-canonical-history check before the LLM-classification path; if match, mark as `inferred-accept-canonical` directly with `rationale: "workspace path matches canonical-history ancestor at <sha>; not edited"` and `confidence: 1.0`.
- `workspace-sync/src/workspace_sync/merge_helper.py` — the `resolve_inferred_conflicts` helper iterates the report's PENDING entries; NN's ancestor-match can pre-resolve them at detection-time so this loop sees them already-resolved.
- The audit log shape is unchanged: NN-resolved entries get the same `resolution: inferred-accept-canonical` enum value, with rationale + confidence reflecting the ancestor-match path.

## Composes with — Idea 20 meta-pattern

NN is itself an instance of "use deterministic primitive when applicable, fall through to LLM when not" — same shape as Idea 20's classifier+verifier pattern but with a different deterministic primitive (git history lookup instead of structural-merge). NN at the entry-side (skip the resolver entirely); QQ-refined at the exit-side (deterministic-merge with verify-gate when resolver IS needed). They compose cleanly.

## Audit-trail note

This experiment was run autonomously per Luke's 2026-04-27 "small experiments to resolve doubt" directive while plan-authors were dispatched. The 97.8% skip rate empirical result was unexpected — earlier estimate was "90%+" with no data behind it. Calibration miss in the conservative direction (under-estimated NN's leverage). Captured here for the plan-author + future review.
