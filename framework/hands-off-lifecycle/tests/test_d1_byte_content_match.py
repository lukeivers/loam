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
    #
    # M1e (amendment #80, sub-plan oss-v0-1-0-publish-rename-1e.md):
    # path entries updated for the per-component framework/<comp>/src/
    # loam/<comp>/ namespace pivot per D-RNM.2 ruling. Where the file's
    # content was preserved by `git mv` (content-preserving rename),
    # the original SHA-256 is preserved verbatim. Where content was
    # also touched by Phase C import rebrand (`from <pkg>` →
    # `from loam.<pkg>`) or Phase D entry-point group rebrand
    # (`pos.bootstrap.contributions` → `loam.bootstrap.contributions`)
    # or pyproject restructure, SHAs are bumped. ODD §4 in-band
    # retire-and-rebaseline applied per M1e sub-plan §5 hard-constraint
    # + §11 finding #3 + dispatch's named carve-out.
    ("framework/primary-persona/src/loam/primary_persona/cli.py",
     # M1c launchd-label rebrand SHA preserved (content unchanged by
     # M1e — pure rename via git mv).
     "ed2398283ae6259baff172f4eb629f5a38041d8a14e45c8f8f3da3b08efdc5d2"),
    ("framework/primary-persona/src/loam/primary_persona/__init__.py",
     "8301c65db74060d1cfb7f6ed4caf3bfbcd734d9b430700dffa862ac8ad6728c3"),
    ("framework/primary-persona/src/loam/primary_persona/onboarding.py",
     # M1e SHA bump: Phase C import rebrand
     # (`from workspace_bootstrap.workspace_paths` →
     # `from loam.workspace_bootstrap.workspace_paths`).
     "965534c9eb02c7e8ba7ae6a78fe4e830c682f44b3e0556950841c5e016ffed52"),
    ("framework/primary-persona/src/loam/primary_persona/session_start_emitter.py",
     # M1e SHA bump: Phase E internal-decoration rebrand (legacy
     # `loam_root` predecessor identifier callsites) plus Phase C `-m`
     # shell-command shape rebrand for primary_persona.cli emission
     # helper.
     "f97595479e5e45e4a461541fb662d5cff0ac87537797bc93b69f312d47fd4b10"),
    ("framework/primary-persona/pyproject.toml",
     # M1e SHA bump: Phase B pyproject restructure
     # (project name `primary_persona` → `loam-primary-persona`,
     # package-dir entry, dependencies list rewrite).
     "0181ab99319a19bd70f262d030d60f0fe74ab325d833706ba33c1bc656cb1ca2"),
    # workspace-bootstrap — high-fan-in component.
    ("framework/workspace-bootstrap/src/loam/workspace_bootstrap/__init__.py",
     # M1e SHA bump: Phase D entry-point group rebrand in docstring
     # (`pos.bootstrap.contributions` → `loam.bootstrap.contributions`).
     "5624b151efc0d324d735eb767dd2f44b15c0cc031a44f81842461bf06aeae170"),
    ("framework/workspace-bootstrap/src/loam/workspace_bootstrap/spec.py",
     "d3ce250ccc76974da7301cff2b1342a24b97c20f19287a109fed2cd7162fa5c8"),
    ("framework/workspace-bootstrap/src/loam/workspace_bootstrap/host.py",
     # M1d OTel rebrand SHA preserved (content unchanged by M1e —
     # pure rename via git mv).
     "3ae99ddd80c0a7c39154491388b322aa504bb0d1220ed5734b77e75e8775b8ba"),
    ("framework/workspace-bootstrap/src/loam/workspace_bootstrap/errors.py",
     "e1aa52137a62d551501e6da23071e414a6b0ed40236517a826ae98531434cbaf"),
    ("framework/workspace-bootstrap/src/loam/workspace_bootstrap/discovery.py",
     # M1e SHA bump: Phase D `_ENTRYPOINT_GROUP` value rebrand.
     "cc07afbd9f21c2c19775c1973099888c061dd32b96c5b62d97a456e08c067ead"),
    # scope-of-work — leaf component (no test_no_sealed sidecar; the
    # leaf shape is the cleanest regression target for HC#4).
    ("framework/scope-of-work/src/loam/scope_of_work/spec.py",
     "4abc338b7b1a4041fbc0afe73ad0e19d8a6cf4a166010493129b4e04d01fd667"),
    ("framework/scope-of-work/src/loam/scope_of_work/events.py",
     "e39dccf0f8dfe81cc977bbe66518c1d3d786a7b85989428d52a78d51f2c4ef7b"),
    ("framework/scope-of-work/src/loam/scope_of_work/projection.py",
     "eee352633bc498c80f613b247d769bcb193d008a48b249b1245719405fd70375"),
    ("framework/scope-of-work/src/loam/scope_of_work/triggers.py",
     "ea9060d65e3d6946ba0b3ea77ad9a58a9026fefc62954d92cdff1f7c300d525e"),
    ("framework/scope-of-work/pyproject.toml",
     # M1e SHA bump: Phase B pyproject restructure
     # (project name `scope_of_work` → `loam-scope-of-work`).
     "1f97cf7a380d1876b416b8a88f06264398296ae176c797ccb0695d8bc6f481cc"),
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
