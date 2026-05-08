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

---

## Pre-release tags

Optional. When used: `v0.4.0-rc.1`, `v0.4.0-beta.2`. The unsuffixed `v0.4.0` is the canonical release.

---

## Tagging

Every shipped minor and patch gets an annotated git tag. The tag annotation is the GitHub Release notes verbatim. Local tag → push to public remote → create GitHub Release marked `--latest` for the most-recent canonical version.

---

## Authority

This file overrides any version-numbering convention that pre-dates it. Disputes between this file and other planning docs resolve in favor of this file.
