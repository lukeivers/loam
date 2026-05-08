# Archived synthesis tool (`pos-publish-framework-only`)

**Deprecated:** 2026-05-04
**Per:** `docs/rebuild/plans/oss-dev-architecture-survey-and-migration-2026-05-04.md`

This directory holds the source + tests for what used to live at
`framework/tools/pos-publish-framework-only/`. The synthesis tool was
the engine that produced a `framework-only` synthetic branch from the
canonical `pos-v2` history and dual-pushed it to a separate
`lukeivers/loam` repo as the public-facing release surface.

The tool, the partition manifest (`publish-mode-manifest.yaml`), the
`framework-only` branch, and the dual-ref push step were all retired
on 2026-05-04 when the loam dev architecture collapsed to the standard
single-repo OSS pattern (one repo, trunk-based on `main`, tag-driven
PyPI release).

The archive is preserved for two reasons:

1. **Future-proofing.** If loam ever needs a true closed-source-vs-public
   split (the Santillana use case — proprietary monorepo with a public
   subset), the synthesis machinery here is a working starting point.
2. **Audit trail.** The full FBE foldback amendment chain (FBE.1
   through FBE.11 plus the M6/M7/M8/M9 partition fixes) is encoded in
   this tool's commit history; archiving it preserves that record
   alongside the plans that drove it.

The tool is **not installed**, **not tested in CI**, and **not
referenced by any active component**. The `loam-amend` test
`test_no_sealed_amendments.py` references its old prefix
(`framework/tools/pos-publish-framework-only/`) in an `allowed_prefixes`
whitelist; that entry is dead-code and will be removed in the next
sealed-component amendment that touches that test.
