# Sealed-component invariants — HC#4 + per-invariant baselines + ODD §4

> **A sealed component carries a stable diff window: changes outside the window violate the seal. Per-invariant baselines pin specific properties (file lists, byte content, frozen-baseline flags) at SEAL_COMMIT time; the seal-test asserts the invariant holds against the BASELINE..SEAL_COMMIT range. Retire-and-rebaseline (ODD §4) is the in-band mechanism for advancing a baseline within an amendment that touches the underlying invariant.**

This document is the concise codification of the sealed-component invariant conventions. The exhaustive narrative — including HC#1..HC#5 history, per-invariant rationale, and the cross-component widening protocol — lives in `../odd-in-loam.md` §10. The implementation lives in `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/` (the seal-diff machinery + per-component `tests/test_no_sealed_amendments.py`).

## 1. HC#4 — byte-content sample paths invariant

A sealed component's `tests/SEAL_COMMIT` sidecar pins the SHA of the seal commit. The seal-test reads the sidecar + diffs against BASELINE; if any path under the component's subtree changes between BASELINE and SEAL_COMMIT outside the `allowed_prefixes` window, the seal-test fails.

**HC#4 specifically** addresses byte-content pinning of explicitly-sampled paths. Some components (typically those carrying schema-stable fixtures) declare a byte-content invariant: a list of paths whose hashed content must remain stable across amendments unless explicitly retired-and-rebaselined.

## 2. Per-invariant baselines

A sealed component's manifest declares `frozen_baseline: true|false` per component:

- `frozen_baseline: true` — the BASELINE SHA is pinned at component-creation time + advances only via explicit retire-and-rebaseline. Used for components whose seal-diff history is forensically valuable (e.g. `framework/hands-off-lifecycle/` H19 pinned at project-start per amendment #23).
- `frozen_baseline: false` — the BASELINE SHA advances opportunistically (typically to the predecessor amendment's §14 SHA-register backfill). Used for most components.

The frozen-baseline flag is a per-component decision recorded at the amendment that introduces the component.

## 3. ODD §4 retire-and-rebaseline

When an amendment legitimately needs to advance a frozen baseline (e.g. an HC#4 sample path's content needs to change because the schema underneath legitimately advanced), the in-band mechanism is:

1. The amendment's plan-doc names the retire-and-rebaseline explicitly (e.g. "this amendment retires HC#4 invariant for path X and rebaselines to the new content").
2. The amendment commits the new content + advances the BASELINE SHA in the manifest YAML.
3. The seal-test passes against the new BASELINE; the old BASELINE's invariant is "retired" in the §14 narrative.

**Retire-and-rebaseline is rare.** Most amendments leave HC#4 GREEN trivially (no sample paths impacted). When required, it is named explicitly + ratified at plan time; never silent.

## 4. Cross-component widening

When an amendment legitimately touches multiple sealed components (e.g. M6a's plugin + loam_cli + pos-publish-framework-only), each touched component's seal-test gains a one-line widening admission for the cross-cutting prefix. The widening lands in the same feature commit as the cross-cutting work.

Per-component `extra_allowed_prefixes` in the manifest enumerate the cross-cutting prefixes for each component; `loam amend apply` propagates these into the seal-tests' `allowed_prefixes` tuples.

## 5. Cross-references

- Long-form invariant history: `../odd-in-loam.md` §10.
- Implementation: `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/seal_diff.py` + per-component `tests/test_no_sealed_amendments.py`.
- Per-component baseline data: `<component>/tests/SEAL_COMMIT` sidecar + `<component>/seals/SEAL_COMMIT.<slug>` narrative files (STAYS at the per-component subtree; not migrated by M6b.0).
- Cross-component widening protocol: amendment #22's universal-paths admission + `feedback_serialize_amendment_builds`.

## 6. Applied-immediately footer

These invariant conventions are applied to every sealed component from project-start forward. Per-component baseline data lives at each component's subtree; the conventions for authoring + advancing baselines live here in the plugin.
