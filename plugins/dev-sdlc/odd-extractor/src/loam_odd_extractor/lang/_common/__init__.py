"""Cross-language shared helpers for ``loam_odd_extractor.lang.*``
adapters (v0.1.8 Cycle 4b).

Per Cycle 4a §10 RF #6 / Cycle 4b AC.DRY.{1..4} — symbols that are
byte-identical (or structurally identical) between the Ruby and
JS/TS adapters live here so future adapters (Python in v0.2.2+;
others later) inherit the consolidated shape rather than the
local-copy precedent.

Modules:

- :mod:`._common.repo_sha` — :func:`resolve_repo_sha` shells out to
  ``git rev-parse HEAD`` (one canonical implementation; was
  duplicated as ``lang/ruby/repo_sha.py`` + ``lang/jsts/repo_sha.py``
  pre-4b).
- :mod:`._common.slugs` — :func:`slugify` + :func:`file_slug`
  helpers (used to derive deterministic AC IDs from arbitrary text
  + file-relative-path slug suffixes for cross-slice ``ac_id``
  uniqueness).
- :mod:`._common.heuristic_helpers` —
  :func:`make_inferred_banded_ac` constructor for HYPOTHESISED-band
  ACs derived from a source PLAUSIBLE AC; per-language regex tables
  + orchestration stay in ``lang/<name>/heuristic_inferences.py``.

This subpackage is intentionally underscore-prefixed (``_common``)
to mark it as internal-to-the-lang-subtree; no public stability
contract beyond Cycle 4b's seal.
"""
