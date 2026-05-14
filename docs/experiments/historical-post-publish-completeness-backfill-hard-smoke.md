# HARD smoke — historical post-publish-completeness backfill PATCH

**Build slug:** `historical-post-publish-completeness-backfill`.
**Build class:** PATCH (defect-closure on v0.7.x publish outcome shape).
**Version derived at build:** `v0.10.1` (per `next_PATCH(v0.10.0) = v0.10.1`).
**Date:** 2026-05-13.
**State:** SEALED LOCAL — awaiting dispatcher dogfood publish per ASK-FIRST.

This is a doc-only PATCH cycle. Per v0.5.0 / v0.5.1 / v0.6.0 / v0.10.0 doc-only-smoke precedent, the smoke writeup verifies repository invariants at the post-source-edit commit + AC.HPPCB.S seal-diff allow-list. No cold-clone, no LLM-judge probe, no rd-automation ride-along (orthogonal to rd-automation by inspection — no `framework/` source or test touched).

---

## Stage 1 — Repository invariants (post-source-edit commit)

Verified at the post-source-edit commit before apply:

### AC.HPPCB.1 — v0.7.3 STATE.md trailing seal placeholder

**Probe (post-edit grep):**
```
$ grep -c "seal TBD-AT-SEAL\." docs/STATE.md
0

$ grep -n "seal \`39170e6\`" docs/STATE.md
133:- **2026-05-10** — **v0.7.3 PATCH SHIPPED PUBLIC** — release-CLI ... seal `39170e6`. **v0.7.3 SHIPPED PUBLIC 2026-05-10 at tag `v0.7.3` (annotated `72de0da`)**.
```

The v0.7.3 STATE.md row's trailing `seal TBD-AT-SEAL.` literal (the only such occurrence) is resolved to `seal \`39170e6\`.`. The seal SHA `39170e6` matches the canonical v0.7.3 seal commit (verified via `git log --all --oneline | grep 39170e6` → `chore(seals): v0-7-3-release-cli-auto-backfill — dev-sdlc at 527698b`) AND matches the existing v0.7.3 row in `docs/release-roadmap.md` §2 (`seal \`39170e6\``), which was already correct pre-PATCH.

**Narrative-safety check (prose `TBD-AT-SEAL` / `TBD-AT-TAG` references inside the v0.7.3 row's body description of the v0.7.3 helper):**
```
$ grep -o "\`TBD-AT-SEAL\` / \`TBD-AT-TAG\`" docs/STATE.md
`TBD-AT-SEAL` / `TBD-AT-TAG`
```

Prose narrative preserved. The surgical Edit's `old_string` (`seal TBD-AT-SEAL. **v0.7.3 SHIPPED PUBLIC ...`) used the unique trailing-context anchor (`seal TBD-AT-SEAL.` immediately followed by ` **v0.7.3 SHIPPED PUBLIC`) which never appears elsewhere in the row's body. The embedded prose-narrative `TBD-AT-SEAL` / `TBD-AT-TAG` references (describing what the v0.7.3 helper does — backticked, mid-sentence) stay intact because they don't match the unique anchor.

This is the same finding the Path-A predecessor halted on: the helper's non-boundary-aware `str.replace("TBD-AT-SEAL", ...)` would have corrupted the prose. The manual-Edit Path-B path closes the trailing-placeholder gap without exercising the buggy helper.

**Verdict:** GREEN. Trailing placeholder resolved; prose preserved.

### AC.HPPCB.2 — §3 Active version section gains v0.7.2 entry

**Probe (post-edit grep):**
```
$ grep -n "v0.7.2 PATCH.*SHIPPED PUBLIC.*0e67135.*91ee1fe" docs/release-roadmap.md
90:**v0.7.2 PATCH (release-CLI `acs-verified` gate parser-scoping fix PATCH (defect-closure for v0.6.0's shipped release-CLI substrate).) SHIPPED PUBLIC 2026-05-10** (tag `v0.7.2`, annotated `0e67135`; seal `91ee1fe`).
```

The v0.7.2 entry is inserted at line 90, between the v0.4-v0.5 prose roll-up paragraph (which already covers v0.7.1 in-line) and the standalone v0.7.3 entry. The entry format matches the existing standalone §3 entries (bold version header + class + parenthetical objective + SHIPPED PUBLIC marker + tag + annotated + seal). Section bounds verified: §3 starts at line 84 (`## §3 Active version`); §4 starts at line 114 (post-PATCH; was line 112 pre-PATCH due to v0.10.1 §3 entry addition). Line 90 is comfortably inside §3.

The SHAs match canonical:
- Tag `v0.7.2` annotated `0e67135` — verified via `git rev-parse v0.7.2` → `0e67135c19238b...`
- Seal `91ee1fe` — verified via `git log --all --oneline | grep 91ee1fe` → `chore(seals): v0-7-2-release-cli-parser-fix — dev-sdlc at 925e773`
- Publish date 2026-05-10 — verified via the v0.7.2 STATE.md row body (`docs/STATE.md:132`).

**Verdict:** GREEN. §3 entry present with correct SHAs.

### AC.HPPCB.3 — FIDRAFT F-FUNC-3 entry

**Probe (post-edit grep):**
```
$ grep -c "^- \*\*F-FUNC-3 " docs/FUTURE_IDEAS_DRAFT.md
1

$ grep -o "F-FUNC-3 — Scope \`_backfill_state_md_placeholders\` to known trailing-position placeholders only" docs/FUTURE_IDEAS_DRAFT.md
F-FUNC-3 — Scope `_backfill_state_md_placeholders` to known trailing-position placeholders only
```

F-FUNC-3 entry exists with all 6 required elements:

1. **Empirical finding** — `_backfill_state_md_placeholders` at `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py:415-416` uses non-boundary-aware `new_row.replace("TBD-AT-SEAL", ...)`.
2. **Corruption shape** — rows whose prose narrative contains literal `TBD-AT-*` strings (e.g., v0.7.3 STATE.md row) cannot be retroactively backfilled without corrupting the narrative.
3. **Proposed safety extension** — scope `TBD-AT-*` replacement to canonical trailing-position context via regex anchor.
4. **Composes-with** — F-FUNC-1 (sibling regex-shape extension), F-FUNC-2 (different shape, same module), F-NFCLEAN-FOLLOWON (this PATCH closes 2 of 3 deferred items; the 3rd is precisely what F-FUNC-3 would unblock).
5. **Status** — capture-only.
6. **AI-time band** — 30-60 min midpoint ~45 min for regex anchors + 4 test cases.

Plan-time investigation against F-FUNC-2's existing scope (interim SHIPPED-LOCAL-sentence removal mode) confirmed F-FUNC-2 covers a different shape; F-FUNC-3 added as a new entry per D-HPPCB.3 ruling.

**Verdict:** GREEN. F-FUNC-3 captured with all 6 elements.

---

## Stage 2 — AC.HPPCB.S seal-diff allow-list

**Probe (at seal commit):** `git diff --name-only <plan-doc-commit>~..<seal-commit>` is expected to show:

- `docs/STATE.md` (AC.HPPCB.1 + v0.10.1 §2 row admin)
- `docs/release-roadmap.md` (AC.HPPCB.2 + v0.10.1 §2 row admin + v0.10.1 §3 entry admin)
- `docs/FUTURE_IDEAS_DRAFT.md` (AC.HPPCB.3 F-FUNC-3 entry)
- `docs/experiments/historical-post-publish-completeness-backfill-hard-smoke.md` (this file)
- `docs/plans/historical-post-publish-completeness-backfill.md` (plan-doc)
- `docs/plans/historical-post-publish-completeness-backfill.manifest.yaml` (manifest)
- `plugins/dev-sdlc/seals/SEAL_COMMIT.historical-post-publish-completeness-backfill` (seal narrative)
- `plugins/dev-sdlc/tests/SEAL_COMMIT` (seal sidecar bump)
- `framework/per-project-pm/state/SEAL_COMMIT.dev-sdlc` (per-project-pm sidecar; if applicable)

**NOT in the diff:**
- ANY entry under `framework/tools/loam/` (the helper is explicitly out of fence per HARD HALT #1)
- ANY `.py`, `.toml`, test file, or other framework/plugin source
- ANY pyproject.toml version bump (PATCH rides predecessor MINOR per D-HPPCB.4)

**Verdict:** GREEN (verified at seal commit; backfilled to §status post-seal).

---

## Stage 3 — rd-automation orthogonality

Doc-only PATCH; no `framework/` or `plugins/` source touched (except seal narrative + sidecar bumps, which are seal-cycle artefacts not rd-automation surfaces). By inspection: orthogonal to rd-automation. No ride-along needed.

---

## Notes

- The Path-A predecessor dispatch produced no commits (halted before any edit). Its halt-and-surface return preserved the working tree state and let Path-B re-dispatch with the corrected manual-edit shape. The Path-A halt is the load-bearing input that surfaced F-FUNC-3 — captured in this cycle's FIDRAFT for the next docs-admin / helper-extension cycle.
- The 3rd F-NFCLEAN-FOLLOWON deferred item (v0.7.3 STATE.md + roadmap §2 row `TBD-AT-COMMIT` / `TBD-AT-APPLY` placeholders) stays deferred. Closing it requires either F-FUNC-3 (narrative-safety helper extension) OR per-placeholder surgical-edit treatment with row-bounded `old_string` anchors. The latter would be 4 more Edit calls; the former is a future cycle with structural close + test coverage. Deferred to next docs-admin cycle.
- The `**Total shipped:**` aggregate-count summary line in `docs/STATE.md` + `docs/release-roadmap.md` is out of scope per HARD HALT #2 strict-scope discipline; helper-driven sweep would regress per the v0.8.1 walker fix; manual correction would touch a separate cycle's responsibility.
