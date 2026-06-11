"""AC.RFPR.2 — Release-integration plan-doc naming.

Release-notes generation for a version whose plan-doc is named
``release-integration-v<X-Y-Z>.md`` produces real §1 + §13 content —
no "(unavailable)" placeholders — via both the implicit lookup
(D-RFPR.1: release-side fallback; shared loam_amend locator untouched)
and an explicit ``--plan-doc`` path threaded through to notes
generation (D-RFPR.2 — the v1.5.0 incident ran WITH ``--plan-doc``
and notes still degraded because the flag never reached
``generate_notes``).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.release import notes, runner


_S1_SENTINEL = "RFPR2-OUTCOME-SENTINEL: the release integrates the cycle."
_S13_SENTINEL = "RFPR2-STATUS-SENTINEL: AC.FIXTURE.1 GREEN."


@pytest.fixture
def release_integration_repo(
    staged_repo: Path, fixture_version: str, fixture_slug: str
) -> Path:
    """Replace the slug-named plan-doc with the
    ``release-integration-v<X-Y-Z>.md`` naming (the shape the v1.5.0
    incident hit: nine such docs exist under canonical docs/plans/),
    carrying extractable §1 + §13 sections."""
    plans = staged_repo / "docs" / "plans"
    (plans / f"{fixture_slug}-release-process.md").unlink()
    (plans / f"release-integration-{fixture_slug}.md").write_text(
        f"# release-integration {fixture_version}\n\n"
        "## §1 Objective / TL;DR\n\n"
        f"{_S1_SENTINEL}\n\n"
        "## §4 Acceptance criteria\n\n"
        "### AC.FIXTURE.1 — fixture AC\n\nDoes a thing.\n\n"
        "## §13 §status\n\n"
        f"{_S13_SENTINEL}\n",
        encoding="utf-8",
    )
    # Hard-smoke writeup under the plan-doc stem (the explicit-path
    # gate derives the experiments path from the stem per AC.SDPD.3).
    (
        staged_repo
        / "docs"
        / "experiments"
        / f"release-integration-{fixture_slug}-hard-smoke.md"
    ).write_text(
        f"# {fixture_version} HARD smoke\n\n**Verdict: GREEN.**\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "docs/"], cwd=staged_repo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "rename plan-doc to release-integration naming"],
        cwd=staged_repo,
        check=True,
    )
    return staged_repo


def test_implicit_lookup_resolves_release_integration_naming(
    release_integration_repo: Path, fixture_version: str
) -> None:
    """AC.RFPR.2 implicit path: bare ``generate_notes`` finds the
    release-integration-named plan-doc; real §1/§13 content lands."""
    body = notes.generate_notes(release_integration_repo, fixture_version)
    assert _S1_SENTINEL in body
    assert _S13_SENTINEL in body
    assert "(unavailable" not in body


def test_explicit_plan_doc_path_reaches_notes(
    release_integration_repo: Path, fixture_version: str, fixture_slug: str
) -> None:
    """AC.RFPR.2 explicit-path variant: a repo-relative plan-doc path
    passed explicitly yields the same real content."""
    body = notes.generate_notes(
        release_integration_repo,
        fixture_version,
        plan_doc=Path("docs/plans") / f"release-integration-{fixture_slug}.md",
    )
    assert _S1_SENTINEL in body
    assert _S13_SENTINEL in body
    assert "(unavailable" not in body


def test_runner_threads_explicit_plan_doc_into_notes(
    release_integration_repo: Path,
    fixture_version: str,
    fixture_slug: str,
    tmp_path: Path,
    monkeypatch,
) -> None:
    """AC.RFPR.2 / D-RFPR.2: a full ``--release --plan-doc`` publish
    run feeds the explicit plan-doc through to the generated notes
    body handed to ``gh release create`` (runner threading — the
    leg the v1.5.0 incident proved missing)."""
    repo = release_integration_repo
    bare = tmp_path / "origin.git"
    subprocess.run(
        ["git", "init", "--bare", "-q", "-b", "main", str(bare)],
        check=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", str(bare)], cwd=repo, check=True
    )
    subprocess.run(
        ["git", "push", "-q", "origin", "main"], cwd=repo, check=True
    )
    captured: list[list[str]] = []
    real_run = subprocess.run

    def fake_run(args, *posargs, **kwargs):
        if isinstance(args, list) and args and args[0] == "gh":
            captured.append(list(args))
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="", stderr=""
            )
        return real_run(args, *posargs, **kwargs)

    monkeypatch.setattr("loam_cli.release.runner.subprocess.run", fake_run)
    monkeypatch.setattr(
        "loam_cli.release.runner.shutil.which", lambda _: "/usr/bin/gh"
    )
    out = runner.run(
        repo,
        fixture_version,
        dry_run=False,
        create_release=True,
        plan_doc=Path("docs/plans") / f"release-integration-{fixture_slug}.md",
    )
    assert out.rc == 0
    creates = [c for c in captured if c[1:3] == ["release", "create"]]
    assert len(creates) == 1
    notes_body = creates[0][creates[0].index("--notes") + 1]
    assert _S1_SENTINEL in notes_body
    assert _S13_SENTINEL in notes_body
    assert "(unavailable" not in notes_body
