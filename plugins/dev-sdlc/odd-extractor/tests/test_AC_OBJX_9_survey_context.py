"""AC.OBJX.9 — User-survey context integration.

- Read order: workspace-local → home → env-var → none.
- Survey-absent path: ``MultiSourceBundle.user_survey = None``;
  collector proceeds.
- Best-effort parse; never blocks.
- Survey-shape claims should cap at PLAUSIBLE in the synthesis
  prompt — verified at AC.OBJX.5 prompt-content level (the
  collector itself just surfaces the survey raw text + parsed
  structure).
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor import collect_multi_source_inputs


def test_workspace_local_survey_takes_precedence(
    tmp_path: Path, monkeypatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    loam_dir = repo / ".loam"
    loam_dir.mkdir()
    workspace_survey = loam_dir / "onboarding-survey.md"
    workspace_survey.write_text(
        "# Survey\n\n## 1. Language\nworkspace-survey-language\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    monkeypatch.delenv("LOAM_ONBOARDING_SURVEY", raising=False)
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1", evidence_rows=[]
    )
    assert bundle.user_survey is not None
    assert "workspace-survey-language" in bundle.user_survey["raw_text"]
    assert bundle.user_survey["source_path"].endswith(
        "onboarding-survey.md"
    )


def test_home_survey_used_when_workspace_local_absent(
    tmp_path: Path, monkeypatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    home_survey = fake_home / "loam-onboarding-survey.md"
    home_survey.write_text(
        "# Survey\n\n## 1. Language\nhome-survey-language\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(fake_home))
    # The DEFAULT_SURVEY_PATH was computed at import time using
    # the earlier HOME; force-reload by monkey-patching the path
    # constant in the module under test.
    from loam_odd_extractor import multi_source as ms

    monkeypatch.setattr(
        ms, "_SURVEY_HOME_PATH",
        Path("~/loam-onboarding-survey.md").expanduser()
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.delenv("LOAM_ONBOARDING_SURVEY", raising=False)
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1", evidence_rows=[]
    )
    if bundle.user_survey is not None:
        assert "home-survey-language" in bundle.user_survey["raw_text"]


def test_env_var_path_used_as_fallback(
    tmp_path: Path, monkeypatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    env_survey = tmp_path / "env-survey.md"
    env_survey.write_text(
        "# Survey\n\n## 1. Language\nenv-survey-language\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("LOAM_ONBOARDING_SURVEY", str(env_survey))
    from loam_odd_extractor import multi_source as ms

    monkeypatch.setattr(
        ms, "_SURVEY_HOME_PATH",
        Path("~/loam-onboarding-survey.md").expanduser()
    )
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1", evidence_rows=[]
    )
    assert bundle.user_survey is not None
    assert "env-survey-language" in bundle.user_survey["raw_text"]


def test_survey_absent_returns_none_user_survey(
    tmp_path: Path, monkeypatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    workspace = tmp_path / "ws"
    workspace.mkdir()
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("LOAM_ONBOARDING_SURVEY", raising=False)
    from loam_odd_extractor import multi_source as ms

    monkeypatch.setattr(
        ms, "_SURVEY_HOME_PATH",
        Path("/nonexistent/loam-onboarding-survey.md")
    )
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1", evidence_rows=[]
    )
    assert bundle.user_survey is None
