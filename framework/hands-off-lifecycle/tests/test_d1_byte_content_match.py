"""HC#4 / AC.D.1.5 — byte-content-match regression for D-migration D.1.

The bug-class that triggered the D-migration architectural review was
test-shape-only verification: tests asserted "files are at the right
paths" but never verified file *content* survived the move byte-
identically. This test closes that gap structurally.

Method (per builder-plan D-build.D.1.H):
1. Pre-move (during build), SHA-256 hashes were computed for 15
   representative files spanning three components (5 each from
   primary-persona, workspace-bootstrap, scope-of-work — leaf,
   mid-graph, high-fan-in per AC.D.1.5).
2. The hashes are hardcoded below.
3. The test reads each file at its post-D.1 framework/<comp>/<...>
   path and asserts the SHA-256 matches.

A builder-side accidental edit during git-mv would break the test
because git mv preserves bytes by default (rename without content
edit gives byte-identical content). This is the structural binding
of HC#4 — pure-rename moves cannot silently corrupt content.

Note: files that ARE intentionally edited as part of D.1
(``first_run_helper.py``, ``first_run_scaffold.py``, ``seal.py``,
the seal-diff tests, and the renamed ``settings.dev-template.json``)
are deliberately EXCLUDED from this list — their content changes
are the amendment's intent, not regressions.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


# Pre-move SHA-256 hashes captured during the D.1 build.
# Each tuple: (repo-relative path post-D.1, expected SHA-256).
_SAMPLE_FILES = (
    # primary-persona — leaf component (no dependents in framework graph
    # for these files specifically; D-mig plan §4 names primary-persona
    # as mid-graph but the named files are pure module bodies).
    ("framework/primary-persona/src/cli.py",
     # M1c (amendment #78, sub-plan oss-v0-1-0-publish-rename-1c.md):
     # SHA updated post-M1c launchd-label rebrand. The cli.py docstring
     # at line ~147 referencing the memory-write-worker launchd label
     # rebranded its reverse-DNS prefix to `com.loam.` (the version
     # suffix was dropped concurrently per loam-rename-decisions Tier-1
     # #4). ODD §4 in-band retire-and-rebaseline applied per M1c
     # sub-plan §11 finding #9 (HC#4 byte-content breach surfaced at
     # touched-test rerun; the docstring rebrand is the AC-named work).
     "ed2398283ae6259baff172f4eb629f5a38041d8a14e45c8f8f3da3b08efdc5d2"),
    ("framework/primary-persona/src/__init__.py",
     "8301c65db74060d1cfb7f6ed4caf3bfbcd734d9b430700dffa862ac8ad6728c3"),
    ("framework/primary-persona/src/onboarding.py",
     # D-migration D.2 (amendment #63): SHA updated post-D.2 because
     # onboarding.py is one of the readers cut over to the
     # workspace-paths helper (per the locked wider-fence ruling).
     # The D.1 byte-content guarantee was for the rename window only;
     # subsequent amendment edits are tracked here as the canonical
     # post-edit hash.
     "e077c38790e2a41780a72e63fcf2e07691ee8c019f62897b6c77cabcfadd52c4"),
    ("framework/primary-persona/src/session_start_emitter.py",
     "772d3d77c9da675d70fedf4f887dfed15da7cc8abd1e2d7dd013b9a456f97099"),
    ("framework/primary-persona/pyproject.toml",
     "8780af2e075e36d07b57a8090c4ba462cab2c893b9df1ac8ab77e357fa3772c4"),
    # workspace-bootstrap — high-fan-in component. Excluded files:
    # adapters/first_run_scaffold.py (plist edits in D.1).
    ("framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py",
     "4da91df872ab2b41c95d2a5cd1a8341fabe310c59efd506ebd43c3e6c12f4bfc"),
    ("framework/workspace-bootstrap/src/workspace_bootstrap/spec.py",
     "d3ce250ccc76974da7301cff2b1342a24b97c20f19287a109fed2cd7162fa5c8"),
    ("framework/workspace-bootstrap/src/workspace_bootstrap/host.py",
     "91465ef9fcc61e9fceffc0da957f726ea776a1f9a7a127bb0711e73bee48e9a7"),
    # framework/workspace-bootstrap/pyproject.toml WAS in this list at
    # D.1 seal time. D-migration D.4 (amendment #65, sealed at
    # `8acdff5`) legitimately edited the file to add the
    # `pos-new-workspace` entry-point. The byte-match invariant for
    # this specific file no longer holds because D.4's intentional
    # content edit lands inside the post-D.1 window — the file is no
    # longer a pure-rename target. Replaced at amendment #67 (single-
    # framework-restructure) with errors.py — a leaf module untouched
    # since D.1 — to keep the workspace-bootstrap sample at ≥5 files
    # per AC.D.1.5. The remaining sample files still serve the HC#4
    # binding for D.1's git-mv discipline (no silent content-edit
    # during the rename).
    ("framework/workspace-bootstrap/src/workspace_bootstrap/errors.py",
     "e1aa52137a62d551501e6da23071e414a6b0ed40236517a826ae98531434cbaf"),
    ("framework/workspace-bootstrap/src/workspace_bootstrap/discovery.py",
     "b58ed5e31591c2f4bec3b0dbad3c60d22c23acfa0da8af12e967ecbbc4c43062"),
    # scope-of-work — leaf component (no test_no_sealed sidecar; the
    # leaf shape is the cleanest regression target for HC#4).
    ("framework/scope-of-work/src/spec.py",
     "4abc338b7b1a4041fbc0afe73ad0e19d8a6cf4a166010493129b4e04d01fd667"),
    ("framework/scope-of-work/src/events.py",
     "e39dccf0f8dfe81cc977bbe66518c1d3d786a7b85989428d52a78d51f2c4ef7b"),
    ("framework/scope-of-work/src/projection.py",
     "eee352633bc498c80f613b247d769bcb193d008a48b249b1245719405fd70375"),
    ("framework/scope-of-work/src/triggers.py",
     "ea9060d65e3d6946ba0b3ea77ad9a58a9026fefc62954d92cdff1f7c300d525e"),
    ("framework/scope-of-work/pyproject.toml",
     "7cb1a03ce82bb87ac5c560568348ba8d39198866dacd57f15cfb81e052e0ab7a"),
)


@pytest.mark.parametrize("relpath,expected_sha", _SAMPLE_FILES)
def test_AC_D_1_5_byte_content_match_post_move(
    relpath: str, expected_sha: str
) -> None:
    """The file at *relpath* (post-D.1 framework/<...> path) has the
    expected SHA-256 captured pre-move. ``git mv`` preserves bytes
    by default; any divergence indicates a builder-side content
    edit slipped into the rename window.
    """
    path = REPO_ROOT / relpath
    assert path.exists(), (
        f"D.1 byte-content regression: file missing post-move: {path}\n"
        "Expected SHA: {expected_sha}\n"
        "Possible causes: file was deleted during restructure, or the "
        "framework/ directory layout differs from D.1's locked design."
    )
    with open(path, "rb") as fh:
        actual_sha = hashlib.sha256(fh.read()).hexdigest()
    assert actual_sha == expected_sha, (
        f"D.1 byte-content regression: {relpath}\n"
        f"  expected SHA-256: {expected_sha}\n"
        f"  actual SHA-256:   {actual_sha}\n"
        "git mv was supposed to preserve bytes; a content-edit "
        "slipped into the rename window. HC#4 binding."
    )


def test_AC_D_1_5_test_carries_at_least_15_samples() -> None:
    """Structural check: the sample list must carry at least 15 entries
    (5 per component × 3 components per AC.D.1.5). Catches a regression
    where the list gets accidentally pruned."""
    assert len(_SAMPLE_FILES) >= 15, (
        f"AC.D.1.5 names ≥3 components × ≥5 files each. "
        f"Sample list has {len(_SAMPLE_FILES)} entries."
    )
