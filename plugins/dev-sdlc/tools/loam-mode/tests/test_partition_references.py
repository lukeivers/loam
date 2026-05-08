"""AC.F3 — no always-loaded artefact references a dev-only artefact.

The reference scanner walks every Markdown file in ``always_loaded``
and flags any backtick-quoted path / Markdown-link target that
resolves to a ``dev_only`` path.

**Known-debt allowlist.** F surfaced one residual cross-mode reference
during build: ``memory-system/launchd/README.md`` references the
true-first-run component-narrative under ``docs/archive/component-research/``.
The README itself is inside the memory-system sealed-component fence
(touching it from F's amendment would be a sealed-amendment in
disguise — F's plan §6 halt trigger 1). The reference is recorded
here as known-debt; a future memory-system amendment that opens that
fence (e.g. a launchd-cleanup amendment) is the right home for the
scrub. The allowlist must shrink to empty when that amendment lands.
"""

from __future__ import annotations

from pathlib import Path


from loam_mode.audit import (
    _resolve_set,
    _walk_audit_tree,
    scan_cross_mode_references,
)
from loam_mode.manifest import load_manifest


# Known cross-mode references that this amendment is not authorised
# to scrub. Each entry: (source_path, target_path). Treat as a closed
# allowlist — any new entry surfacing here is a regression to be
# fixed, not an allowlist expansion.
#
# Post-D.1 (amendment #61): the prior known-debt entry
# (memory-system/launchd/README.md → docs/archive/component-research/...)
# became stale because memory-system moved under framework/.
#
# Post-M6 partition realignment (amendment #94 / AC.PMR.4 / HSF#3):
# the realignment rebased the manifest's `roots:` + `always_loaded:`
# from pre-M6b.0 top-level component refs to `framework/<comp>/`
# post-M6b.0 paths AND added the missing `framework/workspace-sync/`
# admission. Pre-realignment the stale top-level globs matched zero
# files, so AC.F3's always-loaded artefact set was empty and these
# pre-existing prose cross-mode refs were masked. Post-realignment
# the globs match the actual component sources and the pre-existing
# refs surface.
#
# Post-v0.1.9 Cycle 3 (audit-allowlist cleanup): empirical pre-flight
# at master-plan-author time + re-verification at cycle-build-time
# confirmed that 4 prior allowlist entries became stale (zero
# source-file matches): 1× primary-persona prompt template + 3×
# workspace-sync README. Those 4 entries graduated out of the
# allowlist. The remaining entry was the still-valid
# pending-debt: `framework/memory-system/launchd/README.md`
# referencing the true-first-run component-narrative under
# `docs/archive/component-research/`. FIDRAFT line 143
# (audit-allowlist drift) closed on the v0.1.9 Cycle 3 seal.
#
# Post-v0.3.0 Cycle 2 (graphiti rip-out): `framework/memory-system/`
# was deleted entirely (apply 39094ea, seal 013553e). The lone
# remaining allowlist entry's source path no longer exists on
# disk, so the cross-mode reference scanner reports zero
# residual cross-mode references. Per v0.3.0 Cycle 4 plan-doc
# AC.LDC (KNOWN_CROSS_MODE_DEBT strictly decreases; target zero):
# the allowlist shrinks to the empty set. The shrink-not-grow
# discipline below remains enforced — any future regression
# surfaces as `unexpected` and any new debt requires explicit
# allowlist authoring in a NEW commit, never an implicit append.
KNOWN_CROSS_MODE_DEBT: set[tuple[str, str]] = set()


def test_AC_F3_always_loaded_no_dev_refs(
    real_manifest_path: Path, repo_root: Path
) -> None:
    """No always-loaded markdown artefact references a dev-only path,
    except for the known-debt allowlist (captured at F's build time)."""
    manifest = load_manifest(real_manifest_path)
    candidates = _walk_audit_tree(
        repo_root, manifest.roots, manifest.audit_excludes
    )
    always = _resolve_set(manifest.always_loaded, repo_root, candidates)
    dev = _resolve_set(manifest.dev_only, repo_root, candidates)
    refs = scan_cross_mode_references(repo_root, always, dev)

    flagged = {(r.source_path, r.target_path) for r in refs}
    unexpected = flagged - KNOWN_CROSS_MODE_DEBT
    missing = KNOWN_CROSS_MODE_DEBT - flagged

    assert unexpected == set(), (
        "Unexpected cross-mode references in always-loaded artefacts: "
        f"{sorted(unexpected)}"
    )
    assert missing == set(), (
        "Known-debt entries no longer present (allowlist must shrink): "
        f"{sorted(missing)}. Remove them from KNOWN_CROSS_MODE_DEBT."
    )


def test_AC_F3_external_urls_are_ignored(tmp_path: Path) -> None:
    """External URLs inside always-loaded Markdown are not flagged."""
    (tmp_path / "main.md").write_text(
        "Read [Anthropic](https://www.anthropic.com) and "
        "`https://example.com/foo`.\n",
        encoding="utf-8",
    )
    refs = scan_cross_mode_references(
        tmp_path, {"main.md"}, {"docs/dev.md"}
    )
    assert refs == []


def test_AC_F3_inline_code_without_path_shape_is_ignored(
    tmp_path: Path,
) -> None:
    """Plain identifiers in backticks (e.g. function names) don't trip
    the scanner."""
    (tmp_path / "main.md").write_text(
        "Call `select_corpus` then `Manifest`.\n", encoding="utf-8"
    )
    refs = scan_cross_mode_references(
        tmp_path, {"main.md"}, {"docs/dev.md"}
    )
    assert refs == []


def test_AC_F3_dev_path_reference_is_flagged(tmp_path: Path) -> None:
    """A backtick-quoted dev-only path inside an always-loaded file
    is flagged."""
    (tmp_path / "main.md").write_text(
        "See `docs/dev.md` for details.\n", encoding="utf-8"
    )
    refs = scan_cross_mode_references(
        tmp_path, {"main.md"}, {"docs/dev.md"}
    )
    assert len(refs) == 1
    assert refs[0].source_path == "main.md"
    assert refs[0].target_path == "docs/dev.md"


def test_AC_F3_markdown_link_to_dev_path_is_flagged(tmp_path: Path) -> None:
    """A Markdown link target pointing at a dev-only path is flagged."""
    (tmp_path / "main.md").write_text(
        "See [the dev doc](docs/dev.md).\n", encoding="utf-8"
    )
    refs = scan_cross_mode_references(
        tmp_path, {"main.md"}, {"docs/dev.md"}
    )
    assert len(refs) == 1
    assert refs[0].target_path == "docs/dev.md"


def test_AC_F3_anchor_only_links_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "main.md").write_text(
        "[Section](#a-section).\n", encoding="utf-8"
    )
    refs = scan_cross_mode_references(
        tmp_path, {"main.md"}, {"docs/dev.md"}
    )
    assert refs == []


def test_AC_F3_directory_glob_in_dev_set_matches_subpath_refs(
    tmp_path: Path,
) -> None:
    """A reference like ``docs/plans/`` (trailing slash) is
    flagged when the dev-only set contains paths under that prefix."""
    (tmp_path / "main.md").write_text(
        "Plans live in `docs/plans/`.\n", encoding="utf-8"
    )
    refs = scan_cross_mode_references(
        tmp_path,
        {"main.md"},
        {
            "docs/plans/A.md",
            "docs/plans/B.md",
        },
    )
    assert len(refs) == 1
    assert refs[0].target_path == "docs/plans/"
