"""AC.PRSG.3 — diff classifier with line-overlap + symbol-overlap heuristic."""

from __future__ import annotations

from pathlib import Path

from loam_pr_safety import (
    BandedContract,
    ClassificationResult,
    Diff,
    DiffEntry,
    Hunk,
    classify,
    parse_diff,
    read_contract,
)
from loam_pr_safety.diff import parse_unified_diff


# ---- parse_unified_diff helpers --------------------------------------


def _diff_with_hunk(
    file_path: str,
    new_start: int,
    new_lines: int,
    *,
    old_start: int | None = None,
    old_lines: int | None = None,
    added: list[str] | None = None,
    removed: list[str] | None = None,
) -> Diff:
    """Construct a synthetic Diff with one entry, one hunk."""
    return Diff(
        from_sha=None,
        to_sha=None,
        entries=[
            DiffEntry(
                file_path=Path(file_path),
                hunks=[
                    Hunk(
                        old_start=old_start if old_start is not None else new_start,
                        old_lines=old_lines if old_lines is not None else 1,
                        new_start=new_start,
                        new_lines=new_lines,
                        added_lines=added or [],
                        removed_lines=removed or [],
                    )
                ],
            )
        ],
    )


# ---- Line-overlap classification -------------------------------------


def test_classifier_line_overlap_verified(workspace_with_contract):
    """Diff intersecting a VERIFIED AC's cited line range → touched."""
    workspace_root, repo_id = workspace_with_contract
    contract = read_contract(repo_id, workspace_root)
    # AC.SYNTH.1's citation: app/auth.py:42-58.
    diff = _diff_with_hunk("app/auth.py", new_start=50, new_lines=5)
    result = classify(diff, contract)
    assert not result.untouched
    assert len(result.touched_acs) == 1
    assert result.touched_acs[0].ac.ac_id == "AC.SYNTH.1"
    assert result.touched_acs[0].touch_kind == "citation_line"


def test_classifier_line_overlap_plausible(workspace_with_contract):
    """Diff hitting AC.SYNTH.2's cited range → touched (PLAUSIBLE)."""
    workspace_root, repo_id = workspace_with_contract
    contract = read_contract(repo_id, workspace_root)
    diff = _diff_with_hunk(
        "app/models/order.rb", new_start=15, new_lines=3
    )
    result = classify(diff, contract)
    assert not result.untouched
    assert len(result.touched_acs) == 1
    assert result.touched_acs[0].ac.ac_id == "AC.SYNTH.2"


def test_classifier_no_line_overlap_falls_back_to_backing_file(
    workspace_with_contract,
):
    """Diff in a covered file but outside any cited range →
    backing-file touch fires (not novel; not untouched).

    Per AC.PRSG.3 — backing-files are the symbol-overlap softer match.
    File touched but outside line-range → still counted as touched
    via the backing-file path, with touch_kind="backing_file".
    """
    workspace_root, repo_id = workspace_with_contract
    contract = read_contract(repo_id, workspace_root)
    # AC.SYNTH.1 cites app/auth.py:42-58 with backing_files [app/auth.py].
    # Diff at lines 100-110 — outside the citation but inside the file.
    diff = _diff_with_hunk("app/auth.py", new_start=100, new_lines=10)
    result = classify(diff, contract)
    # File is in backing_files; backing-file match fires.
    assert not result.untouched
    assert len(result.touched_acs) == 1
    assert result.touched_acs[0].ac.ac_id == "AC.SYNTH.1"
    assert result.touched_acs[0].touch_kind == "backing_file"
    assert len(result.novel) == 0


def test_classifier_backing_file_match(workspace_with_contract):
    """File in backing_files but no line overlap → backing_file touch.

    AC.SYNTH.3 (HYPOTHESISED) has backing_files=[app/services/payments.rb]
    with NO citations — line-overlap can't fire; backing-file matches.
    """
    workspace_root, repo_id = workspace_with_contract
    contract = read_contract(repo_id, workspace_root)
    diff = _diff_with_hunk(
        "app/services/payments.rb", new_start=10, new_lines=5
    )
    result = classify(diff, contract)
    assert not result.untouched
    # AC.SYNTH.3 is touched via backing-file path.
    found = [t for t in result.touched_acs if t.ac.ac_id == "AC.SYNTH.3"]
    assert len(found) == 1
    assert found[0].touch_kind == "backing_file"


def test_classifier_novel_candidate(workspace_with_contract):
    """Diff in a file outside any AC → novel candidate."""
    workspace_root, repo_id = workspace_with_contract
    contract = read_contract(repo_id, workspace_root)
    diff = _diff_with_hunk(
        "app/new_feature.py", new_start=1, new_lines=20,
        added=["def new_feature():"] * 5,
    )
    result = classify(diff, contract)
    assert not result.untouched
    assert len(result.touched_acs) == 0
    assert len(result.novel) == 1
    assert (
        str(result.novel[0].file_path) == "app/new_feature.py"
    )


def test_classifier_untouched_pure_clean(workspace_with_contract):
    """Empty diff → untouched=True, no touched_acs, no novel."""
    workspace_root, repo_id = workspace_with_contract
    contract = read_contract(repo_id, workspace_root)
    empty_diff = Diff(from_sha=None, to_sha=None, entries=[])
    result = classify(empty_diff, contract)
    assert result.untouched
    assert len(result.touched_acs) == 0
    assert len(result.novel) == 0


def test_classifier_mixed_verified_and_novel(workspace_with_contract):
    """Diff touching VERIFIED AC AND novel file → both surfaces."""
    workspace_root, repo_id = workspace_with_contract
    contract = read_contract(repo_id, workspace_root)
    diff = Diff(
        from_sha=None,
        to_sha=None,
        entries=[
            DiffEntry(
                file_path=Path("app/auth.py"),
                hunks=[
                    Hunk(
                        old_start=50, old_lines=2, new_start=50, new_lines=3
                    )
                ],
            ),
            DiffEntry(
                file_path=Path("app/totally_new.py"),
                hunks=[
                    Hunk(
                        old_start=1, old_lines=0, new_start=1, new_lines=10,
                        added_lines=["def x(): pass"] * 10,
                    )
                ],
            ),
        ],
    )
    result = classify(diff, contract)
    assert not result.untouched
    assert len(result.touched_acs) == 1
    assert result.touched_acs[0].ac.ac_id == "AC.SYNTH.1"
    assert len(result.novel) == 1


# ---- parse_diff (subprocess wrapper) ---------------------------------


def test_parse_diff_against_tmp_repo(tmp_git_repo, make_repo_commit):
    """parse_diff invokes git and returns a structured Diff."""
    sha = make_repo_commit(
        {"app/auth.py": "def f():\n    return 'long enough now'\n"},
        "feat: add auth.f",
    )
    diff = parse_diff(tmp_git_repo, from_sha="HEAD~1", to_sha="HEAD")
    assert diff.from_sha == "HEAD~1"
    assert diff.to_sha == "HEAD"
    assert len(diff.entries) == 1
    assert str(diff.entries[0].file_path) == "app/auth.py"
    assert diff.entries[0].is_new_file is True


# ---- parse_unified_diff (pure parser) --------------------------------


def test_parse_unified_diff_simple_modify():
    """Unified-diff text parses into typed Diff."""
    text = (
        "diff --git a/foo.py b/foo.py\n"
        "index abc..def 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -10,2 +10,3 @@\n"
        "-old line\n"
        "+new line A\n"
        "+new line B\n"
    )
    diff = parse_unified_diff(text)
    assert len(diff.entries) == 1
    assert str(diff.entries[0].file_path) == "foo.py"
    assert len(diff.entries[0].hunks) == 1
    h = diff.entries[0].hunks[0]
    assert h.old_start == 10
    assert h.old_lines == 2
    assert h.new_start == 10
    assert h.new_lines == 3
    assert h.removed_lines == ["old line"]
    assert h.added_lines == ["new line A", "new line B"]


def test_parse_unified_diff_omitted_count():
    """`@@ -10 +10 @@` defaults old/new lines to 1."""
    text = (
        "diff --git a/foo.py b/foo.py\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -10 +10 @@\n"
        "-old\n"
        "+new\n"
    )
    diff = parse_unified_diff(text)
    h = diff.entries[0].hunks[0]
    assert h.old_lines == 1
    assert h.new_lines == 1
