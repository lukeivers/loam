"""Seal-fence test for the loam-skills plugin.

Standard seal-test pattern (mirror
`plugins/dev-sdlc/tests/test_no_sealed_amendments.py`): asserts no
diff between BASELINE and the sealed commit modifies sealed-component
surfaces outside this plugin's allowed prefix list.

The plugin is the SECOND sealed component under the `plugins/` tree
(first was dev-sdlc at v0.1.0 M6a; loam-skills lands at v0.1.3 item 1
per docs/rebuild/plans/v0-1-3-skill-packages.md). Its initial fence
admits `plugins/loam-skills/` only; cross-component partners (none
needed at this seal cycle — loam-skills is a leaf plugin with no
runtime dependency on other components) + the universal docs/rebuild/
plans/ admission for the sub-plan + manifest + the install-from-source
admissions for the Tier K append round out the legitimate diff.

BASELINE history:
  - `2c95507` (v0.1.3 item 1 sub-plan-doc): plugin's first seeded
    state. The amendment manifest's BASELINE will be set to the
    source-edit commit (NEXT commit landing the plugin tree); the
    seal test's diff window is `BASELINE..seal_commit` per the
    cross-component sweep convention.

SEAL_COMMIT: populated at seal time by `loam amend seal` per the
amendment ritual.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = "fafd2898"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_seal_commit_pinning_pattern() -> None:
    """The test file exposes BASELINE + SEAL_COMMIT_PATH and does not
    diff against ..HEAD literally. Post-seal, tests/SEAL_COMMIT
    contains the SHA."""
    source = Path(__file__).read_text()
    assert "BASELINE = " in source
    assert "SEAL_COMMIT_PATH" in source
    assert "{BASELINE}..{seal}" in source, (
        "the diff call must route through _seal_commit()"
    )


def test_only_loam_skills_changed() -> None:
    """No sealed-component surface moved between BASELINE and seal
    outside the loam-skills plugin tree + admitted partners."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # v0.1.3 item 1 authored a NEW sealed component at
    # plugins/loam-skills/. The primary fence is the plugin's own
    # subtree. The Tier K append to the install-from-source flow is
    # admitted via allowed_files (the two install paths sit at the
    # repo root + docs/install-from-source.md respectively). The
    # universal docs/rebuild/plans/ admission carries the sub-plan-
    # doc + manifest.
    #
    # v0.2.0 Cycle 2 admits two compose-points (per
    # docs/rebuild/plans/v0-2-0-cycle-2-auto-skill-creation.md §3
    # two-component fence + §10 universal admissions):
    #   - framework/workspace-bootstrap/ — the SECONDARY co-shipping
    #     fence; the new manifest field `enable_auto_skill_capture`
    #     lives there. The reverse seal-fence (workspace-bootstrap's
    #     test) already admits docs/design/ + plugins/loam-skills/
    #     prefixes (extensive list at line ~70 of that test).
    #   - docs/design/ — the TERTIARY universal admission for the
    #     new design note (auto-skill-capture-shape.md). Mirrors the
    #     v0.1.7 Cycle 3 pattern (layered-skill-architecture.md was
    #     admitted via the same prefix at workspace-bootstrap's
    #     seal-fence).
    allowed_prefixes = (
        "plugins/loam-skills/",
        "docs/rebuild/plans/",
        "docs/design/",
        "framework/workspace-bootstrap/",
        "docs/",
        "docs/plans/",
        "framework/hands-off-lifecycle/",
        "plugins/dev-sdlc/",
        "docs/capability-corpus/",
    )
    allowed_files: set[str] = {
        "install-from-source.txt",
        "docs/install-from-source.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "CLAUDE.md",
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/rebuild/STATE.md",
        "README.md",
        "docs/STATE.md",
        "docs/plans/loam-roadmap.md",
        "docs/release-roadmap.md",
    }

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified: {offending}. "
        "Halt-signal condition."
    )
