"""AC.PMR.1 — Gate-test files (test_AC_AG_*, test_AC_BAG_*) classify
`dev_only` post-realignment.

Per post-M6 partition realignment plan §4 AC.PMR.1: 12 gate-test
files at `framework/hands-off-lifecycle/tests/test_AC_AG_*.py` (5
files) + `test_AC_BAG_*.py` (7 files) reclassify from `dev_and_public`
(via the broad `framework/hands-off-lifecycle/**` glob) to `dev_only`
via explicit globs in the M2 partition manifest. Per partition-
precedence rule #2 (`dev_only` checked before `dev_and_public`), the
explicit globs win.

This test exercises BOTH branches:
  - Positive: each of the 12 gate-test files classifies `dev_only`.
  - Negative-control: a non-gate test file in the same dir continues
    to classify `dev_and_public`.

Closes M9 plan-doc §7 finding #1 (the partition completeness gap).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.publish_framework_only.partition import (
    PartitionClass,
    classify_path,
    load_manifest,
)


CANONICAL_REPO = Path(__file__).resolve().parents[4]
CANONICAL_MANIFEST = (
    CANONICAL_REPO
    / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml"
)


GATE_AG_TESTS = (
    "framework/hands-off-lifecycle/tests/test_AC_AG_1_wrong_wd_dispatch.py",
    "framework/hands-off-lifecycle/tests/test_AC_AG_2_method_enumerated_prompt.py",
    "framework/hands-off-lifecycle/tests/test_AC_AG_3_stale_dispatch.py",
    "framework/hands-off-lifecycle/tests/test_AC_AG_4_no_op_normal_use.py",
    "framework/hands-off-lifecycle/tests/test_AC_AG_5_audit_log.py",
)

GATE_BAG_TESTS = (
    "framework/hands-off-lifecycle/tests/test_AC_BAG_1_secret_commit.py",
    "framework/hands-off-lifecycle/tests/test_AC_BAG_2_blast_radius.py",
    "framework/hands-off-lifecycle/tests/test_AC_BAG_3_amend_in_subagent.py",
    "framework/hands-off-lifecycle/tests/test_AC_BAG_4_loam_amend_dry_run.py",
    "framework/hands-off-lifecycle/tests/test_AC_BAG_5_wrong_tree_write.py",
    "framework/hands-off-lifecycle/tests/test_AC_BAG_6_no_op_non_matching.py",
    "framework/hands-off-lifecycle/tests/test_AC_BAG_7_audit_log.py",
)


def _load_canonical_manifest():
    if not CANONICAL_MANIFEST.exists():
        pytest.skip("canonical manifest not at expected location")
    return load_manifest(CANONICAL_MANIFEST)


@pytest.mark.parametrize("path", GATE_AG_TESTS + GATE_BAG_TESTS)
def test_AC_PMR_1_gate_test_classifies_dev_only(path: str) -> None:
    """Each of the 12 gate-test files classifies `dev_only`."""
    manifest = _load_canonical_manifest()
    cls = classify_path(manifest, path)
    assert cls == PartitionClass.DEV_ONLY, (
        f"{path} expected DEV_ONLY; got {cls}"
    )


def test_AC_PMR_1_non_gate_test_classifies_dev_and_public() -> None:
    """Negative-control: a non-gate test file in the same dir
    continues to classify `dev_and_public` via the broad
    `framework/hands-off-lifecycle/**` glob."""
    manifest = _load_canonical_manifest()
    # corpus_load_sentinel tests do NOT match the AG/BAG patterns.
    candidate = (
        "framework/hands-off-lifecycle/tests/test_corpus_load_sentinel.py"
    )
    cls = classify_path(manifest, candidate)
    assert cls == PartitionClass.DEV_AND_PUBLIC, (
        f"{candidate} expected DEV_AND_PUBLIC (broad glob); got {cls}"
    )


def test_AC_PMR_1_gate_test_count_matches_expected() -> None:
    """Sanity: the AG + BAG file lists in this test match what
    actually exists on disk (defensive — protects against the file
    list drifting without the AC being updated)."""
    tests_dir = (
        CANONICAL_REPO / "framework/hands-off-lifecycle/tests"
    )
    if not tests_dir.exists():
        pytest.skip("tests dir not at expected location")
    on_disk_ag = sorted(
        f"framework/hands-off-lifecycle/tests/{p.name}"
        for p in tests_dir.glob("test_AC_AG_*.py")
    )
    on_disk_bag = sorted(
        f"framework/hands-off-lifecycle/tests/{p.name}"
        for p in tests_dir.glob("test_AC_BAG_*.py")
    )
    assert on_disk_ag == sorted(GATE_AG_TESTS)
    assert on_disk_bag == sorted(GATE_BAG_TESTS)
