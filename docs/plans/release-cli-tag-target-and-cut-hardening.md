# Release-CLI tag-target + deterministic-cut + mergeability hardening

**Component (fence):** `loam-cli` (`framework/tools/loam/`) — single-component sealed fence.
**Working directory:** `/Users/lukeivers/loam` (canonical).
**Amendment:** #195 (confirm against live counter at `loam amend apply`; highest on disk = 194).
**Plan class:** sealed-component amendment plan (plan-before-code).
**Cycle:** 1 of a 3-cycle fix program. This cycle lands the **release-CLI-resident** half of the near-miss audit (Class D + Class A + the Class-B cheap partial). Classes C and E are separate cycles, out of scope here.

## §1 — Prime-objective ladder

Ladders to VALUE_PROPOSITION via loam's protection floor: a release that tags a broken tree or ships a mis-numbered cut is the "breaks the surrounding work / the original goal" AI-betrayal this floor exists to stop. The three outcomes convert three docs-only / discretion-only rules into machine chokepoints (D, A) plus one honest tool-assisted partial (B).

## §2 — Audit citation (design ground truth)

This cycle implements `workspace/.scratch/claude-output/release-seal-near-miss-audit-2026-07-08.md` (persisted in pos3), specifically **Class D**, **Class A**, **Class B (cheap partial only)**, §3 (composite map), and the **Dispatcher verification appendix**. Where this plan and the audit agree, the audit governs. Tier-0 confirmations run during planning:

- **Real-row dominance verified.** `git rev-list -1 v1.10.0` = `99a1be9` = the row's sole `seal`-labelled SHA (the post-seal `lockstep bump d4c24839` is NOT `seal`-labelled, so the regex never captures it, and it is correctly excluded). `git rev-list -1 v1.11.0` = `badd2d6f` = the row's sole `seal`-labelled SHA. Both real published tags equal the dominating-seal resolver's output. The dominating-seal mechanism matches ground truth on both real rows.
- **Straggler tag-target sites confirmed.** `_extract_seal_sha` / `seals[-1]` selects the tag target in FOUR places, not one: `runner.py:405` (tag creation), `gates.py:628` (seal-reachable gate), `notes.py:205` (release-notes anchor) + `notes.py:77` (prior-version range endpoint), `post_publish_backfill.py:952,1035` (backfill marker). A complete Class-D fix rewires all of them; leaving any is a non-objective inconsistency (ODD).
- **Seal staging is file-specific** (`git add -- <sidecar> <narrative>`), so the two stray untracked `docs/plans/per-session-resume-handoff.*` files (another session's; brief said nothing in flight) are inert and are left untouched.

## §3 — Halt-and-surface (before + during build)

- Policy recipe ambiguous for a real case **beyond** the named D-CUT.CLASS operationalization → surface, do not guess.
- Adding gates breaks an existing V060.2 gate-count assertion in a way implying a real contract (not a trivial count bump) → surface.
- Any breaking change to the release CLI public surface (would flip the eventual cut to MAJOR) → surface.
- ODD violation in this work OR surrounding code → surface.
- No stable ratification-artefact format to record the preflight verdict into → build the verb, surface the recording-integration gap (do not fake structural enforcement).

## §4 — Fence

Single component: `framework/tools/loam/` (loam-cli). All source + test edits land under this prefix. Universal admissions: `docs/plans/` (this plan, the manifest, the sealed narrative). The fence test `framework/tools/loam/tests/test_no_sealed_amendments.py` gates the seal; its `BASELINE` advances to the pre-build tip at build-time and its `SEAL_COMMIT` sidecar advances at apply-time (standard pattern).

## §5 — Acceptance criteria (outcome-shape; method is the builder's call)

### Family DOM — right tag target (audit Class D)

#### AC.DOM.1
The release tool resolves a version's tag target as the seal that **dominates** every other seal named in that version's roadmap §2 row — each other seal is its ancestor (`git merge-base --is-ancestor <other> <target>` rc=0).

#### AC.DOM.2
When the row's seal set has no single dominating seal, the resolver signals a halt (no tag target) and a `loam release` run REDs instead of tagging.

#### AC.DOM.3
A row naming exactly one seal resolves to that seal — no false halt for the well-formed single-seal rows that are today's norm (backward-compat; verified against both real rows).

#### AC.DOM.4 (outcome-altitude: true)
Given a §2 row naming multiple seals where a NON-dominating SHA appears first (the `seals[-1]` / first-physical-line fragility shape), the resolver returns the dominating seal — never the early first SHA. Additionally, against the canonical tree's real rows, the resolver's target equals `git rev-list -1 <tag>` for each published version. Verified by driving the resolver the runner tag-target path + `gates.run_all` use.

#### AC.DOM.5
The dominance check is enforced at publish: a dedicated gate inside the mandatory `gates.run_all` pass RETURNS RED when dominance fails — not merely a helper the operator can skip.

#### AC.DOM.6
Every tag-target resolution site in the release package (tag creation, seal-reachability gate, release-notes anchor, post-publish backfill marker, and the notes prior-version range endpoint) resolves through the single dominating-seal resolver; no site selects the tag target via `seals[-1]`. Enforced by a source-scan intent-guard.

### Family CUT — deterministic cut, machine-enforced (audit Class A)

#### AC.CUT.1
A gate in `gates.run_all` recomputes the release from repo state: the class from the conventional-commit prefixes of the unreleased commits (`<current-published-tag>..HEAD`) and the expected version number = bump(current published version, class), per `docs/release-versioning-policy.md`.

#### AC.CUT.2
The gate REDs when the recomputed expected version ≠ the version being cut, with a corrective hint naming BOTH the computed cut and the target (the policy's "halt-and-surface, never silent re-number" event).

#### AC.CUT.3
The gate passes when the recomputed expected version == the version being cut.

#### AC.CUT.4 (outcome-altitude: true)
Given a cut whose unreleased content warrants MINOR (a `feat:` present) but the target is a PATCH bump — AND the inverse (only fixes, target MINOR) — a `loam release` gate run REDs with a hint naming the mismatch. Driven through `run_all`.

#### AC.CUT.5
When the highest local published tag and the highest origin published tag disagree (a locally-sealed-but-unpushed higher version), the gate REDs/HALTs (the policy's HARD-HALT for local/remote tag disagreement) rather than silently choosing one. When it cannot determine published state at all (no tags reachable), it degrades to pass-with-caveat (fail-safe — never a false RED that blocks a legitimate publish on the gate's own inability, mirroring gates 8/9).

#### AC.CUT.6
A MAJOR target is treated as an owner-gated escalation: the gate does NOT auto-RED a MAJOR target, and surfaces any breaking-change markers found in the unreleased content as a NOTE rather than forcing MAJOR (D-CUT.MAJOR).

### Family PRE — mergeability check verb (audit Class B — cheap partial only)

#### AC.PRE.1
`loam release preflight <version>` emits a per-branch mergeability verdict against current `main` (fast-forwardable and/or merge-tree-clean vs conflicting) for each candidate merge branch.

#### AC.PRE.2
The preflight output includes the computed cut (class + expected number) from the SAME computation the deterministic-cut gate uses (one mechanism, two entry points).

#### AC.PRE.3
The preflight emits a stable, structured block suitable for pasting verbatim into the ratification artefact a dispatcher Tier-0-verifies before dispatch.

#### AC.PRE.4 (outcome-altitude: true)
Given a fixture repo containing a branch that conflicts with / does not fast-forward onto `main`, `loam release preflight <version>` reports that branch as non-clean; a clean branch reports clean. Driven end-to-end through the CLI dispatch.

#### AC.PRE.5
`loam release preflight` invoked with no version (or a malformed sub-invocation) exits with a clear error and NEVER falls through into the publish/tag path.

## §6 — Named decisions

- **D-DOM.SIDECAR** — dominance uses ONLY the roadmap §2 row's seal SHAs, NOT component `SEAL_COMMIT.*` sidecars. Sidecars track each component's LATEST seal regardless of version; a component sealed after a version's content tip is not an ancestor of that version's tag target, so including sidecars would false-RED. The row's seals are the version-scoped set. (F2 divergence from the audit's optional "hardened, every sidecar" suggestion — named + justified; the audit marked it optional "if you judge it worth the hardening.")
- **D-CUT.CLASS** — "content class" is mechanized as a conventional-commit-prefix scan over `<published>..HEAD`: any `feat` → MINOR-capability; a breaking marker (`!` after type, or `BREAKING CHANGE` in the body) → breaking-note; else PATCH. This operationalizes the policy's semantic "class from content." It diverges from perfect semantic classification in edge cases (an internal-only `feat` → false MINOR; a capability landing under `fix`/`chore` → missed under-cut). Judged acceptable because the corrective hint is human-reconcilable and the gate is a tripwire, not an authority. Surfaced as F2.
- **D-CUT.MAJOR** — MAJOR is owner-gated (never auto-RED); breaking markers surface as a note. Evidence: `docs/release-versioning-policy.md` §MAJOR is a quality-bar owner event; breaking changes ride minors with deprecation cycles.
- **D-PRE.PARTIAL** — the preflight verb is a tool-assisted PARTIAL (relies on being run), NOT structural enforcement. The fully-structural pre-dispatch hook is a SEPARATE, scheduled item, OUT of this cycle (audit Class B honesty).
- **D-PRE.CLI** — `preflight` is added as a leading sub-token on the existing `release` parser via a second optional positional, preserving `loam release <version>` unchanged (no public-CLI break).

## §7 — Build steps

1. Advance the fence test `BASELINE` to the pre-build tip; author `cut.py` (version parse/bump + `compute_cut` + conventional-commit class scan + published-tag reads with injection hooks).
2. Rewire tag-target resolution: replace `_extract_seal_sha`/`seals[-1]` selection with `_all_seal_shas` + `resolve_tag_target` (dominating-seal) in `gates.py`, `runner.py`, `notes.py`, `post_publish_backfill.py`.
3. Add `check_seal_dominance` + `check_deterministic_cut` gates to `ALL_GATES` + `run_all` (fail-safe degradation for indeterminate state).
4. Add `preflight.py` + wire the `preflight` sub-token in `cli.py`/`runner.py`.
5. Author one test file per AC (`test_AC_DOM_*.py`, `test_AC_CUT_*.py`, `test_AC_PRE_*.py`); run touched tests + the existing V060.2 suite locally.
6. Commit source (feat/fix), `loam amend validate`, `loam amend apply`, `loam amend seal`. STOP at sealed-local.

## §8 — In-flight halt triggers

Per §3. Additionally: 5-hour wall-clock cycle ceiling; if the existing V060.2 gate-count test encodes a real contract broken by the two new gates, surface rather than force.

## §status

(backfilled at cycle close)
