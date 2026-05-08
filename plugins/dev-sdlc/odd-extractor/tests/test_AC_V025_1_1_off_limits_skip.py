"""AC.V025-1.1 — Analyze step honors off-limits zones from contract.

Per v0.2.5.1 corrective (F-LEAK closure): the analyze step's
``_walk_repo`` honors off-limits directory names from two sources:

1. Static ``_SKIP_DIR_NAMES`` extended with common artefact dir
   names (``html-captures``, ``screenshots``, ``html-output``,
   ``test-results``, ``coverage``, ``playwright-report``).
2. Dynamic per-run extra-skip set parsed from the user-survey
   markdown's ``## 10. Off-limits zones`` section
   (best-effort; never blocks on parse failure).

Three unit tests cover:

- ``test_extended_skip_list_blocks_html_captures_with_no_survey``
  — repo with ``html-captures/foo.html`` and NO survey; the static
  skip-list extension catches it.
- ``test_survey_off_limits_extracted_and_skipped``
  — repo with ``screenshots/foo.png`` plus a survey containing
  ``screenshots/`` in §10; survey-parsed extra-skip catches it.
- ``test_malformed_survey_falls_back_to_default_skip_list``
  — repo with ``html-captures/foo.html`` plus a malformed survey
  (binary garbage / missing §10); analyze does NOT raise + the
  static skip-list extension still catches the file.

Plus the off-limits parser itself is covered with three unit tests
in this file:

- ``test_off_limits_parser_returns_empty_on_none_input``
- ``test_off_limits_parser_extracts_basenames_from_eric_survey_shape``
- ``test_off_limits_parser_returns_empty_on_no_section``
"""

from __future__ import annotations

from pathlib import Path


from loam_odd_extractor.analyze import (
    _SKIP_DIR_NAMES,
    _extract_off_limits_dirs,
    _walk_repo,
    analyze_repo,
)
from loam_odd_extractor.budget import default_budget
from loam_odd_extractor.init import init_extraction


def _setup_repo(repo_root: Path) -> None:
    """Create a tiny multi-dir repo for analyze-walk verification."""
    (repo_root / "src").mkdir()
    (repo_root / "src" / "app.js").write_text("// app")
    (repo_root / "html-captures").mkdir()
    (repo_root / "html-captures" / "01-login-page.html").write_text(
        "<html>off-limits</html>"
    )
    (repo_root / "screenshots").mkdir()
    (repo_root / "screenshots" / "shot1.png").write_text("png-bytes")
    (repo_root / "tests").mkdir()
    (repo_root / "tests" / "test_app.js").write_text("// test")


def _init_workspace_and_config(
    repo_root: Path, workspace: Path
):
    """Run init_extraction so analyze_repo has a populated extraction
    dir + state.yaml (the precondition the production CLI provides)."""
    workspace.mkdir(parents=True, exist_ok=True)
    return init_extraction(
        repo_path=repo_root,
        workspace_root=workspace,
        budget=default_budget(),
        dry_run=True,
    )


# ----------------------------------------------------------------------
# Off-limits parser unit tests
# ----------------------------------------------------------------------


def test_off_limits_parser_returns_empty_on_none_input() -> None:
    """Best-effort contract: None input yields empty set, never raises."""
    assert _extract_off_limits_dirs(None) == frozenset()
    assert _extract_off_limits_dirs("") == frozenset()


def test_off_limits_parser_extracts_basenames_from_eric_survey_shape() -> (
    None
):
    """Real-shape: Eric's survey §10 prose. Verify dir basenames."""
    survey = """## 9. Tooling

Some tooling discussion.

## 10. Off-limits zones

Off-limits — never read or modify:

- /Users/eric/Developer/checkmateapp/rd-automation/.env
- credentials.json
- Anything under public/uploads/, public/data/, /logs/, screenshots/,
  html-captures/, /test-results/ — local artifacts.
- S3 keys in uploads/ and uploads/screenshots/

## 11. First task

Refactoring."""
    result = _extract_off_limits_dirs(survey)
    # Verify the §10 dir-name basenames are extracted; .env / dotfiles
    # filtered out (file-level extension filter handles those).
    assert "uploads" in result
    assert "data" in result
    assert "logs" in result
    assert "screenshots" in result
    assert "html-captures" in result
    assert "test-results" in result


def test_off_limits_parser_returns_empty_on_no_section() -> None:
    """Survey missing the off-limits heading → empty set."""
    survey = """## 1. Language

Python.

## 2. Channel

Telegram."""
    assert _extract_off_limits_dirs(survey) == frozenset()


def test_off_limits_parser_returns_empty_on_malformed_input() -> None:
    """Best-effort contract: malformed input never raises."""
    # Binary-ish noise + half-formed markdown.
    assert _extract_off_limits_dirs("\x00\x01\xff garbage") == frozenset()
    assert _extract_off_limits_dirs("# malformed [unclosed") == frozenset()


# ----------------------------------------------------------------------
# Static skip-list extension tests
# ----------------------------------------------------------------------


def test_extended_skip_list_blocks_html_captures_with_no_survey(
    tmp_path: Path,
) -> None:
    """Repo with html-captures/ + screenshots/ + NO survey: the static
    skip-list extension blocks both directories at the analyze walk."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _setup_repo(repo)

    # No survey authored. Walk should still skip artefact dirs by
    # default skip-list extension.
    files = _walk_repo(repo)
    file_strs = [str(f) for f in files]

    assert any("src/app.js" in s for s in file_strs), (
        f"src/app.js must be present in the walk; got files: {file_strs}"
    )
    assert any("tests/test_app.js" in s for s in file_strs), (
        f"tests/test_app.js must be present; got files: {file_strs}"
    )
    assert not any("html-captures" in s for s in file_strs), (
        f"html-captures/ must be skipped by static skip-list "
        f"extension; got files: {file_strs}"
    )
    assert not any("screenshots" in s for s in file_strs), (
        f"screenshots/ must be skipped; got files: {file_strs}"
    )


def test_static_skip_list_includes_v0_2_5_1_artefact_dirs() -> None:
    """The static _SKIP_DIR_NAMES must include the v0.2.5.1
    belt-and-suspenders artefact dir names."""
    for name in (
        "html-captures",
        "screenshots",
        "html-output",
        "test-results",
        "coverage",
        "playwright-report",
    ):
        assert name in _SKIP_DIR_NAMES, (
            f"_SKIP_DIR_NAMES missing v0.2.5.1 artefact dir: {name}"
        )


# ----------------------------------------------------------------------
# Survey-parsed extra-skip integration tests
# ----------------------------------------------------------------------


def test_survey_off_limits_extracted_and_skipped(tmp_path: Path) -> None:
    """analyze_repo reads the survey at <repo>/.loam/onboarding-survey.md
    and unions parsed off-limits dirs into the walk skip-set.

    Verification: place a custom dir in the repo (one NOT in the static
    skip-list — e.g., ``custom-artefacts/``) + a survey mentioning
    that dir name in §10 + a normal source file. Run analyze_repo and
    verify the custom dir is skipped while the source file is walked.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "app.js").write_text("// app")
    # Custom artefact dir NOT in the static skip-list.
    (repo / "custom-artefacts").mkdir()
    (repo / "custom-artefacts" / "secret.txt").write_text("secret")

    # Author a survey at <repo>/.loam/onboarding-survey.md naming
    # the custom-artefacts dir in §10.
    survey_dir = repo / ".loam"
    survey_dir.mkdir()
    survey_content = """## 9. Tooling

Stuff.

## 10. Off-limits zones

- Anything under custom-artefacts/ — local artefacts.

## 11. First task

Build."""
    (survey_dir / "onboarding-survey.md").write_text(survey_content)

    workspace = tmp_path / "ws"
    config = _init_workspace_and_config(repo, workspace)

    plan = analyze_repo(config=config)
    plan_paths = [str(p) for p in plan.unhandled_paths] + [
        str(p) for s in plan.slices for p in s.paths
    ]
    assert any("src/app.js" in s for s in plan_paths), (
        f"src/app.js must be walked; got: {plan_paths}"
    )
    assert not any("custom-artefacts" in s for s in plan_paths), (
        f"custom-artefacts/ must be skipped via survey-parsed "
        f"extra-skip; got: {plan_paths}"
    )


def test_malformed_survey_falls_back_to_default_skip_list(
    tmp_path: Path,
) -> None:
    """A malformed survey must NOT cause analyze_repo to raise;
    the default skip-list still catches html-captures/."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _setup_repo(repo)

    # Malformed survey — binary garbage in the off-limits section.
    survey_dir = repo / ".loam"
    survey_dir.mkdir()
    (survey_dir / "onboarding-survey.md").write_bytes(
        b"\x00\xff\xfe garbage [unclosed bracket"
    )

    workspace = tmp_path / "ws"
    config = _init_workspace_and_config(repo, workspace)

    # Must not raise.
    plan = analyze_repo(config=config)

    plan_paths = [str(p) for p in plan.unhandled_paths] + [
        str(p) for s in plan.slices for p in s.paths
    ]
    # Static skip-list still catches html-captures/.
    assert not any("html-captures" in s for s in plan_paths), (
        f"html-captures/ must be skipped by static skip-list even on "
        f"malformed survey; got: {plan_paths}"
    )
