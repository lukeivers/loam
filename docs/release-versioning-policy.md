# Loam Release Versioning Policy

**Effective:** 2026-05-08.
**Scheme:** SemVer (semver.org), explicit commitment.

---

## What the digits mean

`MAJOR.MINOR.PATCH` (e.g., `0.3.0`, `0.2.5.1`).

- **MAJOR** — breaking changes to the public surface. Stays at `0` until loam declares stability (see §1.0.0 below). A bump to `1` is a one-way commitment.
- **MINOR** — new outcome-shape capability. Each minor release names ONE outcome a user can newly achieve with loam. Backwards-compatible additions only.
- **PATCH** — backwards-compatible fixes for the named outcome of the current minor. Same-shape behavior; bug closures only.

A four-digit form (`MAJOR.MINOR.PATCH.HOTFIX`) is allowed for hot patches that ship before the next planned PATCH (e.g., `v0.2.5.1` corrects three production-path defects in v0.2.5 without introducing a new outcome). Hot patches do not introduce new capability; they close defects in the most-recent minor's named outcome.

---

## What goes in a minor

Each minor release is shaped around an **objective target** — a single sentence stating what a user can now do with loam that they could not do before. Multiple ideas, fixes, and components can land under one minor as long as they ladder up to that one objective.

The objective sentence is the version's name. Example:

> v0.3.0 — Loam's documented features work as advertised.

Everything in v0.3.0 must serve that objective. Anything that doesn't gets pushed to a later minor or to backlog.

---

## What goes in a patch

Patches close defects in the current minor's outcome. Patches do NOT introduce new capability. If a "patch" requires new capability to fix, it's a minor.

Patches are named by the defects they close, not by an outcome (e.g., "v0.2.5.1 — patch: off-limits leak, synthesis timeout, verify-orphan").

---

## Quality gate — END-USER vs META-FRAMEWORK minors

Each minor in the roadmap carries a class tag (END-USER / META-FRAMEWORK / MIXED) declared at plan time. The class drives a different quality gate at planning:

- **END-USER minors** must demonstrate meaningful end-user value-prop advancement at plan time. The plan-doc names the specific translation-burden delta (per `docs/leverage-discipline.md` §5.1) the user gains from the minor — not "internal coherence improved" but "user can now do X they could not do before." If the plan cannot name a specific user-visible delta, the minor is not END-USER and either re-tags or re-shapes.
- **MIXED minors** carry the same gate as END-USER for the user-visible portion plus an explicit foundational-investment portion; both halves are named in the plan-doc.
- **META-FRAMEWORK minors** are exempt from the user-value-delta gate but MUST explicitly tag as such AND name the foundational-investment rationale at plan time — what future end-user work this enables, why it has to land before that work, and the trigger that makes the foundational investment necessary now rather than later.

The class tag is not advisory: an END-USER minor that ships without a named user-visible delta is a leverage failure (per the anti-leverage signals in `docs/leverage-discipline.md` §6); a META-FRAMEWORK minor without named foundational-investment rationale is a discipline failure (the exempt path becomes the default escape hatch).

---

## When 1.0.0 ships

The MAJOR jump from `0` to `1` happens when ALL of the following are true:

1. **All documented features work as advertised.** A stranger cloning loam and following the README + install instructions can verify every named capability is operational. No drift between docs and behavior.
2. **One real user has shipped real software with loam.** Not a smoke-test fixture; a user with a real codebase + real maintenance burden has used loam to ship work they would not have shipped without it.
3. **Backwards-compatibility commitment.** Loam commits to no breaking changes for 6 months minimum from the 1.0.0 ship date. Breaking changes after that bump to 2.0.0 with deprecation warnings shipped in the prior minor.
4. **Plugin contract is stable.** Third-party plugins authored against 1.0.0 continue to work through the 0.x compatibility window.

The bump is named explicitly when it lands. It is not a calendar event; it is a quality-bar event.

**Pre-1.0 majors are not cut.** SemVer convention: pre-1.0 is "in development; breaking changes allowed within minor bumps." Loam follows that convention. The first major release IS the 1.0.0 quality-bar event above; no MAJOR bumps before that.

---

## Post-1.0 majors — emergent, not pre-themed

After 1.0.0 ships, MAJOR releases are emergent rather than pre-planned. The release process's post-ship review (per `loam release` CLI's AC.V045.6 step) checks at every release boundary: "does the cumulative state since the last major indicate a major-release-worthy boundary?" Triggers:

1. **Accumulated breaking changes** that warrant an API contract reset. If the deprecation cycle for major-public-surface changes has run its course in the prior minors, the next release cuts MAJOR.
2. **Significant capability shift** that re-shapes how loam is used (not just adds new outcome — fundamentally changes the user's mental model of the tool).
3. **Plugin contract revision** that breaks the prior major's third-party plugin compatibility window.

The post-ship review surfaces a major-eval verdict to owner; owner decides whether to cut. Default is no — MINOR bumps continue absorbing changes — until the cumulative weight of triggers makes a major release the right shape. Same shape as the 1.0.0 quality-bar event: it is not a calendar event; it is a quality-bar event.

---

## Number derivation at build-commence time

Per `feedback_version_numbers_at_release_time` (captured 2026-05-13) + the priority-queue restructure (`docs/plans/release-roadmap-priority-queue-restructure.md`), the version number for a forward-looking candidate is **derived at build-commence time** from two inputs, not pre-assigned at queue-authoring time. The recipe:

```
Given: current_version   — the most-recent shipped tag on the public
                            remote at the time of build-commence (e.g.,
                            v0.9.0). NOT the highest-numbered-locally;
                            the rule pins against published state.
Given: candidate_class   — PATCH | MINOR | MAJOR — from the queue
                            entry being built; the class is suggestive
                            on the roadmap but plan-author rules
                            authoritatively at build-time (Q2 2026-05-09).

if candidate_class == PATCH:
    next_number = bump_patch(current_version)   # v0.9.0 → v0.9.1
elif candidate_class == MINOR:
    next_number = bump_minor(current_version)   # v0.9.0 → v0.10.0
elif candidate_class == MAJOR:
    next_number = bump_major(current_version)   # v0.9.0 → v1.0.0
                                                  # (only post-1.0
                                                  # commitment; see
                                                  # §"When 1.0.0 ships"
                                                  # for the gate)
```

**Where the recipe applies.** At build-commence time, when a candidate moves from the priority queue (§4 of `docs/release-roadmap.md`) into an active build. Plan-doc filenames stay scope-descriptive (no version pre-baked); the version number gets assigned to the seal commit, the tag, and the §status verdict block at build-time + recorded in `docs/STATE.md` + `docs/release-roadmap.md` §2 at ship-time.

**What `current_version` means precisely.** The highest-numbered shipped tag on the canonical `loam` remote (`origin`) at the time of build-commence. If local and remote disagree (a tag sealed locally but not yet pushed), the local-but-unpushed version becomes a HARD HALT trigger — the recipe is ambiguous; surface to owner for the disambiguation ruling before proceeding. The build-forward discipline (`feedback_build_forward_on_publish_pending`) governs queue advancement when publish is pending; the **number-derivation** rule pins against published-remote state to prevent two parallel builds racing on the same derived number.

**Hot-patch case (`v0.X.Y.Z` four-digit form).** When a hot patch is needed before the next planned PATCH, the existing four-digit convention applies + the recipe extends with `bump_hotfix(current_version)`. Example: `v0.2.5.1` was a hot patch on `v0.2.5` correcting three production-path defects; `next_HOTFIX(v0.2.5) = v0.2.5.1`. Hot patches do not introduce new capability; they close defects in the most-recent minor's named outcome (same shape as PATCHes; see "What goes in a patch" above).

**Edge case: in-flight PATCH not yet shipped.** If the queue's first item is MINOR but there's an in-flight PATCH that hasn't yet been published, the candidate-class drives the choice independently. The in-flight PATCH bumps PATCH from the current published version; the MINOR after it bumps MINOR from the new PATCH-bumped version once the PATCH ships. Build-forward applies — both can be authored in parallel on the priority queue, but build serialization (per `feedback_serialize_amendment_builds`) applies in the same worktree.

**Implementation choice (documented manual rule).** Per the priority-queue restructure plan-doc's D-RR.5.4 builder ruling (2026-05-13): the recipe is documented as a manual rule in this policy doc (this section). The maintainer reads the recipe at build-commence-time and applies it. A future opt-in Python helper exposing `next_number(current, candidate_class)` for `loam release` CLI consumption can land as a follow-on patch if the manual-application cost rises; current state is single-maintainer + low frequency, so the manual rule is sufficient.

---

## Pre-release tags

Optional. When used: `v0.4.0-rc.1`, `v0.4.0-beta.2`. The unsuffixed `v0.4.0` is the canonical release.

---

## Tagging

Every shipped minor and patch gets an annotated git tag. The tag annotation is the GitHub Release notes verbatim. Local tag → push to public remote → create GitHub Release marked `--latest` for the most-recent canonical version.

---

## Per-component pyproject version anchor — `docs/ACTIVE_MINOR`

`docs/ACTIVE_MINOR` is the single-line machine-readable source-of-truth file containing the current shipped MINOR (e.g., `0.12.0`). Component `pyproject.toml` `version` fields track this anchor per AC.HONEST.1 (established v0.8.0) + AC.PCVR.{1,3} (regression-closure structural enforcement). The anchor advances at every MINOR's source-edit batch; PATCHes never touch it per D-NFCLEAN.4 (v0.8.1) + D-SDPD (v0.8.2) precedents — per-component-version discipline advances with MINORs only; PATCHes ride predecessor MINOR.

The anchor is consumed by `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`, which fails CI when any in-scope component pyproject's `version` drifts from the anchor. The in-scope set EXCLUDES measurement/experimental harnesses with deliberate `version = "0.0.0"` semantics (handsoff-loop, loam-spawn-isolation; two retired benchmark-harness pyprojects left the set at the 2026-06-11 retirement) — these are not versioned runtime components shipped to end-users.

At the **v1.0.0 release cut (2026-06-01)** the two runtime components that had ridden off-lockstep as documented intentional outliers — `state-migration-engine` (was 0.13.0) and `protection-matrix` (was 0.1.0) — were FOLDED INTO the in-scope lockstep set and bumped to `1.0.0`. Both ship user-facing entry-point verbs (`loam migrate` / `loam guards`), are sealed, and live in the install graph, so by this policy's "shipped runtime components" criterion they belong in-scope; they were simply tree-added after the in-scope set's last enumeration. The user-facing `pipx install loam` meta-package (`framework/loam-init/meta/pyproject.toml`) was likewise advanced to `1.0.0` at the cut so its declared version is honest about the release it corresponds to.

---

## Authority

This file overrides any version-numbering convention that pre-dates it. Disputes between this file and other planning docs resolve in favor of this file.
