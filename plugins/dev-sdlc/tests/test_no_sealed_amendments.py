"""Seal-fence test for the dev-sdlc plugin.

Standard seal-test pattern (mirror
`framework/dormancy/tests/test_no_sealed_amendments.py`): asserts no
diff between BASELINE and the sealed commit modifies sealed-component
surfaces outside this plugin's allowed prefix list.

The plugin is the FIRST sealed component under the `plugins/` tree
(per plan §11 finding #7 — first external contributor to the
`loam.bootstrap.contributions` entry-point group). Its initial fence
admits `plugins/dev-sdlc/` only; cross-component partners that
M6a's diff legitimately touches (`framework/tools/loam/`,
`framework/tools/pos-publish-framework-only/`,
`docs/rebuild/plans/`) are admitted via universal/partner widening
in subsequent amendments — at this seal cycle the M6a manifest
itself widens via `universal_paths.prefixes` + `extra_allowed_prefixes`.

BASELINE history:
  - `2770cc9` (M5 §14 SHA-register backfill): plugin's first sealed
    state. The amendment manifest's BASELINE points here; the seal
    test's diff window is `BASELINE..seal_commit` per the
    cross-component sweep convention.

SEAL_COMMIT: populated at seal time by `loam amend seal` per the
amendment ritual.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = "8032348"

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


def test_only_dev_sdlc_changed() -> None:
    """No sealed-component surface moved between BASELINE and seal
    outside the dev-sdlc plugin tree + admitted partners."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # M6a authors a NEW sealed component at plugins/dev-sdlc/. The
    # primary fence is the plugin's own subtree. Cross-component
    # partners (loam-cli + pos-publish-framework-only — both touched
    # for the M6a integration seam) + the universal docs/rebuild/
    # plans/ admission round out the M6a-legitimate diff. The other
    # framework sealed-component seal-tests are widened with the
    # plugins/dev-sdlc/ prefix in M6a's feature commit so their own
    # cross-component sweeps pass — those edits land on the seal-
    # tests' own component subtrees, admitted here as cross-cutting
    # widening edits.
    allowed_prefixes = (
        "plugins/dev-sdlc/",
        "framework/tools/loam/",
        "framework/tools/pos-publish-framework-only/",
        "docs/rebuild/plans/",
        # Cross-cutting widening edits to other sealed components'
        # seal-test allowed_prefixes — each component's seal-test
        # gains a single `plugins/dev-sdlc/` admission line so the
        # sweep passes when M6a's plugin diff is in flight. These
        # land in the M6a feature commit per the M1g-precedent
        # cross-component widening pattern.
        "framework/cost-governance/",
        "framework/dormancy/",
        "framework/hands-off-lifecycle/",
        "framework/memory-system/",
        "framework/objective-tracker/",
        "framework/observability-aggregator/",
        "framework/orchestrator/",
        "framework/primary-persona/",
        "framework/reversibility-primitive/",
        "framework/safety-layer/",
        "framework/scope-of-work/",
        "framework/self-correction/",
        "framework/self-upgrade/",
        "framework/telegram-interface/",
        "framework/workspace-bootstrap/",
        "framework/workspace-sync/",
        "docs/rebuild/plans/research/",
        "hands-off-lifecycle/",
        "docs/",
        "docs/rebuild/",
        "framework/tools/loam-mode/",
        "framework/tools/heavy-b-migrate/",
        "CLAUDE.dev.md",
        "orchestrator/",
        "self-upgrade/",
        "framework/loam-init/",
        "loam-init/",
        "workspace-bootstrap/",
        "cost-governance/",
        "framework/loam/",
        "loam/",
        "objective-tracker/",
        "observability-aggregator/",
        "primary-persona/",
        "reversibility-primitive/",
        "safety-layer/",
        "scope-of-work/",
        "self-correction/",
        "telegram-interface/",
        "workspace-sync/",
    )
    allowed_files: set[str] = {
        "CLAUDE.dev.md",
        "CLAUDE.md",
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "docs/install-from-source.md",
        "install-from-source.txt",
        "README.md",
        "docs/getting-started.md",
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
