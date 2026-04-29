"""AC.D-sa.1 – AC.D-sa.7 — `loam amend seal` finalisation extension.

Each AC has at least one test function. See
``docs/rebuild/plans/pos-amend-seal-automation-extension.md`` §4.

Fixture shape: a tmpfs git repo with one or more fake "sealed
components" — each is a top-level dir carrying ``tests/SEAL_COMMIT``
(the convention `_discover_sealed_components` uses) plus a stub
``tests/test_no_sealed_amendments.py`` (the seal-diff test). The
amendment commit lands a no-op file under the component to model
the post-amendment-commit state. ``loam amend seal`` is then
invoked against a manifest pointing at the fixture component(s).
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from loam_cli.amend.cli import main as cli_main
from loam_cli.amend.commands.seal import _discover_sealed_components
from loam_cli.amend.manifest import load_manifest


# ----------------------------------------------------------------------
# Fixture builders
# ----------------------------------------------------------------------


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=check,
    )


def _make_fake_component(
    repo: Path, name: str, *, with_passing_seal_diff: bool = True
) -> None:
    """Create a fake sealed-component directory layout under *repo*.

    Post-D.1: components live at ``<repo>/framework/<name>/``. The
    fixture mirrors the production layout so ``_discover_sealed_components``
    finds them at ``framework/*/tests/SEAL_COMMIT``.
    """
    comp_dir = repo / "framework" / name
    (comp_dir / "tests").mkdir(parents=True, exist_ok=True)
    (comp_dir / "src").mkdir(exist_ok=True)
    (comp_dir / "src" / "__init__.py").write_text("\n", encoding="utf-8")
    (comp_dir / "tests" / "__init__.py").write_text("\n", encoding="utf-8")
    # Sidecar — the marker `_discover_sealed_components` looks for.
    (comp_dir / "tests" / "SEAL_COMMIT").write_text(
        "0000000000000000000000000000000000000000\n", encoding="utf-8"
    )
    # Seal-diff test — needs ``allowed_prefixes`` + ``allowed_files``
    # tuple literals so `loam amend apply --dry-run` finds the
    # admission bindings (per dry_run.py's read_entries lookup). The
    # admissions widen to admit the component's own top-level dir +
    # universal docs paths so a fixture amendment touching
    # `<comp>/src/...` plus `docs/rebuild/plans/...` and `CLAUDE.md`
    # validates clean against the dry-run gate.
    header = textwrap.dedent(
        f"""
        # Fixture seal-diff test for {name}.
        # Post-D.1: components live at framework/{{name}}/.
        allowed_prefixes = (
            "framework/{name}/",
            "docs/rebuild/plans/",
        )
        allowed_files = (
            "CLAUDE.md",
        )
        """
    ).lstrip()
    if with_passing_seal_diff:
        body = header + textwrap.dedent(
            """
            def test_seal_diff_ok():
                assert True
            """
        ).lstrip()
    else:
        body = header + textwrap.dedent(
            """
            def test_seal_diff_fails():
                assert False, "fixture-injected sweep regression"
            """
        ).lstrip()
    (comp_dir / "tests" / "test_no_sealed_amendments.py").write_text(
        body, encoding="utf-8"
    )
    # An ordinary component test that should pass — the
    # touched-component pytest run (step (d) in seal._finalize)
    # invokes pytest on `<comp>/tests/`.
    (comp_dir / "tests" / "test_basic.py").write_text(
        textwrap.dedent(
            """
            def test_component_ok():
                assert True
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _write_manifest(
    repo: Path,
    *,
    components: list[str],
    number: int,
    slug: str,
    seal_description: str | None = None,
    narrative_target: str | None = None,
) -> Path:
    plans_dir = repo / "docs" / "rebuild" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = plans_dir / f"amendment-{number}-{slug}.manifest.yaml"
    # Read baseline as the current HEAD (pre-amendment tip equivalent)
    head_proc = _git(repo, "rev-parse", "HEAD")
    baseline = head_proc.stdout.strip()
    lines = [
        "schema_version: 1",
        "amendment:",
        f"  number: {number}",
        f"  slug: {slug}",
        f'  title: "fixture amendment {number}"',
        f"baseline: {baseline}",
        f"plan: docs/rebuild/plans/amendment-{number}-{slug}.md",
        "components:",
    ]
    for c in components:
        lines.append(f"  - name: {c}")
        # Post-D.1: components live at framework/<name>/.
        lines.append(
            f"    seal_test: framework/{c}/tests/test_no_sealed_amendments.py"
        )
        lines.append(f"    sidecar: framework/{c}/tests/SEAL_COMMIT")
    if seal_description is not None:
        lines.append(f'seal_description: "{seal_description}"')
    if narrative_target is not None:
        lines.append("narrative:")
        lines.append(f"  target: {narrative_target}")
        lines.append("  body: |")
        lines.append(f"    # fixture narrative for amendment {number}")
        lines.append("    fixture body line.")
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Commit the manifest immediately so the working tree is clean
    # at amendment-time (mirrors real workflow: manifest is committed
    # alongside the plan doc before the amendment commit lands).
    rel = manifest_path.relative_to(repo)
    _git(repo, "add", "--", str(rel))
    _git(
        repo,
        "commit",
        "-q",
        "-m",
        f"fixture: amendment-{number} manifest",
    )
    return manifest_path


def _make_amendment_commit(repo: Path, comp: str, payload: str = "edit") -> str:
    """Land a fake amendment commit under *comp*. Returns the SHA.

    Post-D.1: components live at framework/<comp>/.
    """
    edit_path = repo / "framework" / comp / "src" / "amendment.py"
    edit_path.write_text(f"# {payload}\n", encoding="utf-8")
    _git(repo, "add", "--", f"framework/{comp}/src/amendment.py")
    _git(repo, "commit", "-m", f"feat({comp}): fixture amendment edit")
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def sealed_repo(tmp_path: Path) -> Path:
    """Build a tmpfs repo with two fake sealed components + initial commit."""
    repo = tmp_path / "workspace"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "loam amend test")
    # `.gitignore` so pytest's __pycache__ artefacts don't show up
    # as untracked dirt during the seal step's pre-flight check.
    (repo / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n", encoding="utf-8"
    )
    # Universal-paths admission file — needed so dry-run validates.
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    _make_fake_component(repo, "alpha")
    _make_fake_component(repo, "beta")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: initial sealed components")
    return repo


# ----------------------------------------------------------------------
# AC.D-sa.1 — single-invocation finalisation
# ----------------------------------------------------------------------


def test_AC_D_sa_1_single_invocation_finalises(sealed_repo, monkeypatch) -> None:
    """`loam amend seal <manifest>` finalises in one process: sidecar
    advance, narrative append, tests, sweep, commit, dry-run verify."""
    repo = sealed_repo
    monkeypatch.chdir(repo)
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=900,
        slug="single-invocation",
        seal_description="single invocation",
        narrative_target="framework/alpha/seals/SEAL_COMMIT.fixture",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac1")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc == 0, "seal must exit 0 on the happy path"

    # (a) sidecar advanced to amendment SHA
    sidecar = (repo / "framework" / "alpha" / "tests" / "SEAL_COMMIT").read_text().strip()
    assert sidecar == amendment_sha

    # (b) narrative file written
    narrative = repo / "framework" / "alpha" / "seals" / "SEAL_COMMIT.fixture"
    assert narrative.exists()
    assert "fixture narrative" in narrative.read_text()

    # (c) HEAD is the seal commit and is distinct from amendment SHA
    seal_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert seal_sha != amendment_sha

    # (d) seal-commit subject matches deterministic template
    subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert subject == (
        f"chore(seals): single invocation — alpha at {amendment_sha[:7]}"
    )

    # (e) post-seal `loam amend apply --dry-run` exits 0
    dry_rc = cli_main(["apply", "--dry-run", str(manifest_path)])
    assert dry_rc == 0

    # (f) working tree clean
    status = _git(repo, "status", "--porcelain").stdout
    assert status == ""


# ----------------------------------------------------------------------
# AC.D-sa.2 — deterministic commit-message template
# ----------------------------------------------------------------------


def test_AC_D_sa_2_commit_message_deterministic_template(sealed_repo) -> None:
    """The seal-commit message body carries every required component
    section per AC.D-sa.2 (subject + amendment-number + bumped sidecars
    + narrative target + diff window + sweep result)."""
    repo = sealed_repo
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=905,
        slug="template-test",
        seal_description="my description",
        narrative_target="framework/alpha/seals/SEAL_COMMIT.fixture",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac2")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc == 0

    full_body = _git(repo, "log", "-1", "--format=%B").stdout
    # Subject line
    assert (
        f"chore(seals): my description — alpha at {amendment_sha[:7]}"
        in full_body
    )
    # Amendment-number reference
    assert "Amendment #905 seal commit." in full_body
    # Bumped sidecar paths
    assert "framework/alpha/tests/SEAL_COMMIT" in full_body
    # Narrative target
    assert "framework/alpha/seals/SEAL_COMMIT.fixture" in full_body
    # Baseline-to-amendment-SHA window
    manifest = load_manifest(manifest_path)
    assert manifest.baseline in full_body
    assert amendment_sha in full_body
    # Cross-component sweep result
    assert "Cross-component sweep:" in full_body


def test_AC_D_sa_2_seal_description_falls_back_to_slug(sealed_repo) -> None:
    """When manifest has no seal_description, the slug fills the slot."""
    repo = sealed_repo
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=906,
        slug="my-slug-fallback",
        seal_description=None,
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac2b")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc == 0

    subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert subject == (
        f"chore(seals): my-slug-fallback — alpha at {amendment_sha[:7]}"
    )


def test_AC_D_sa_2_multi_component_subject(sealed_repo) -> None:
    """Multi-component manifests join component names with `+`."""
    repo = sealed_repo
    manifest_path = _write_manifest(
        repo,
        components=["alpha", "beta"],
        number=907,
        slug="multi-comp",
        seal_description="multi case",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac2c")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc == 0

    subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert subject == (
        f"chore(seals): multi case — alpha+beta at {amendment_sha[:7]}"
    )


def test_AC_D_sa_2_co_authored_trailer_env_gated(
    sealed_repo, monkeypatch
) -> None:
    """The Co-Authored-By trailer appears only under a Claude-attributed
    environment (env-var detected)."""
    repo = sealed_repo
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=908,
        slug="env-gated-trailer",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac2d")

    # No env var set → no trailer.
    for v in ("CLAUDECODE", "CLAUDE_CODE_SDK", "CLAUDE_AGENT_RUN"):
        monkeypatch.delenv(v, raising=False)
    rc = cli_main(["seal", str(manifest_path)])
    assert rc == 0
    body = _git(repo, "log", "-1", "--format=%B").stdout
    assert "Co-Authored-By" not in body

    # Reset for second invocation: revert the seal commit, and
    # set the env var.
    seal_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "reset", "--hard", f"{seal_sha}~1")

    monkeypatch.setenv("CLAUDECODE", "1")
    rc2 = cli_main(["seal", str(manifest_path)])
    assert rc2 == 0
    body2 = _git(repo, "log", "-1", "--format=%B").stdout
    assert "Co-Authored-By: Claude" in body2


# ----------------------------------------------------------------------
# AC.D-sa.3 — cross-component sweep (default full; --scoped-sweep opt-in)
# ----------------------------------------------------------------------


def test_AC_D_sa_3_full_sweep_default_runs_every_sealed_component(
    sealed_repo, capsys
) -> None:
    """Default behaviour invokes every sealed component's seal-diff
    test; the sweep summary names the count."""
    repo = sealed_repo
    # Add a third component so we have 3 in workspace.
    _make_fake_component(repo, "gamma")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add gamma")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],  # only alpha listed
        number=910,
        slug="full-sweep-default",
        seal_description="full sweep",
    )
    _make_amendment_commit(repo, "alpha", payload="ac3a")

    # Direct discovery confirms 3 sealed components.
    discovered = _discover_sealed_components(repo)
    assert set(discovered) == {"alpha", "beta", "gamma"}

    rc = cli_main(["seal", str(manifest_path)])
    assert rc == 0
    body = _git(repo, "log", "-1", "--format=%B").stdout
    # 3 components green in sweep summary
    assert "3 components green" in body


def test_AC_D_sa_3_scoped_sweep_runs_manifest_listed_only(
    sealed_repo,
) -> None:
    """`--scoped-sweep` restricts the sweep to manifest-listed
    components; sweep summary names only that count."""
    repo = sealed_repo
    _make_fake_component(repo, "gamma")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add gamma")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=911,
        slug="scoped-sweep",
        seal_description="scoped",
    )
    _make_amendment_commit(repo, "alpha", payload="ac3b")

    rc = cli_main(["seal", "--scoped-sweep", str(manifest_path)])
    assert rc == 0
    body = _git(repo, "log", "-1", "--format=%B").stdout
    # Scoped sweep: only the manifest-listed component is run.
    assert "1 components green" in body


def test_AC_D_sa_3_sweep_failure_halts_before_commit(sealed_repo) -> None:
    """A failing seal-diff test in any swept component prevents the
    seal commit from being created (case (b) of AC.D-sa.5)."""
    repo = sealed_repo
    # Inject a failing seal-diff test in beta.
    _make_fake_component(repo, "beta", with_passing_seal_diff=False)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: beta seal-diff fails")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=912,
        slug="sweep-fail",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac3c")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc != 0
    # HEAD must still be the amendment commit — no seal commit.
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head == amendment_sha


# ----------------------------------------------------------------------
# AC.D-sa.4 — `--no-finalize` preserves pre-extension behaviour
# ----------------------------------------------------------------------


def test_AC_D_sa_4_no_finalize_preserves_pre_extension_behaviour(
    sealed_repo,
) -> None:
    """`--no-finalize` advances sidecars + appends narrative ONLY:
    no commit, no test invocation, no sweep, no dry-run gate."""
    repo = sealed_repo
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=920,
        slug="no-finalize",
        seal_description="legacy path",
        narrative_target="framework/alpha/seals/SEAL_COMMIT.fixture",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac4")

    # Run with --no-finalize.
    rc = cli_main(["seal", "--no-finalize", str(manifest_path)])
    assert rc == 0

    # Sidecar advanced + narrative written, but NO new commit was made.
    sidecar = (repo / "framework" / "alpha" / "tests" / "SEAL_COMMIT").read_text().strip()
    assert sidecar == amendment_sha

    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head == amendment_sha, (
        "with --no-finalize, no commit is created"
    )

    # Sidecar + narrative changes are present in the working tree
    # (not staged by the legacy path). The narrative file lands in a
    # new directory; git porcelain reports the dir as untracked.
    status = _git(repo, "status", "--porcelain").stdout
    assert "framework/alpha/tests/SEAL_COMMIT" in status
    narrative_file = repo / "framework" / "alpha" / "seals" / "SEAL_COMMIT.fixture"
    assert narrative_file.exists(), (
        "narrative file must be written even on --no-finalize path"
    )
    assert "fixture body line." in narrative_file.read_text(encoding="utf-8")


# ----------------------------------------------------------------------
# AC.D-sa.5 — failure-mode halt-and-checkpoint
# ----------------------------------------------------------------------


def test_AC_D_sa_5_failing_component_test_halts_before_commit(
    sealed_repo,
) -> None:
    """A failing component pytest run (step (d)) halts before the
    seal commit is created (case (a) of AC.D-sa.5). Sidecar +
    narrative changes are left for the operator to inspect."""
    repo = sealed_repo
    # Inject a failing component-level test.
    (repo / "framework" / "alpha" / "tests" / "test_basic.py").write_text(
        textwrap.dedent(
            """
            def test_will_fail():
                assert False, "fixture-injected component failure"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: alpha test fails")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=930,
        slug="component-test-fail",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac5a")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc != 0
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head == amendment_sha, "no seal commit was created"


def test_AC_D_sa_5_dirty_tree_halts(sealed_repo) -> None:
    """An unrelated dirty path at invocation time halts (case (c))."""
    repo = sealed_repo
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=931,
        slug="dirty-tree",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac5b")

    # Inject unrelated dirty file.
    (repo / "scratch_unrelated.txt").write_text("dirt\n", encoding="utf-8")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc != 0
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head == amendment_sha


# ----------------------------------------------------------------------
# AC.D-sa.6 — pre-existing loam amend tests + invocations remain green
# ----------------------------------------------------------------------


def test_AC_D_sa_6_existing_test_suite_still_green(tmp_path: Path) -> None:
    """The pre-existing loam amend test suite — every test except this
    one — still exits 0. AC.D-sa.6's regression gate.

    Method: invoke pytest as a subprocess against the existing
    test files in the source tree, deselecting this AC.D-sa-prefixed
    new module to avoid recursion.
    """
    loam_tool_root = Path(__file__).parent.parent
    tests_dir = loam_tool_root / "tests"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--ignore",
            str(tests_dir / "test_seal.py"),
            str(tests_dir),
        ],
        cwd=loam_tool_root,
        capture_output=True,
        text=True,
    )
    # Existing suite must remain green; if a regression slips in,
    # this test reports it loudly.
    assert proc.returncode == 0, (
        "existing loam amend tests regressed:\n"
        + proc.stdout
        + proc.stderr
    )


def test_AC_D_sa_6_legacy_seal_signature_idempotent(sealed_repo) -> None:
    """The legacy `--no-finalize` path is idempotent against the same
    HEAD (re-invoking produces no additional diff beyond the first
    run). Mirrors the prior `loam amend seal` idempotency contract."""
    repo = sealed_repo
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=940,
        slug="legacy-idempotent",
        narrative_target="framework/alpha/seals/SEAL_COMMIT.fixture",
    )
    _make_amendment_commit(repo, "alpha", payload="ac6")

    rc1 = cli_main(["seal", "--no-finalize", str(manifest_path)])
    assert rc1 == 0
    # Snapshot the working-tree state after the first run.
    status_after_run1 = _git(repo, "status", "--porcelain").stdout

    # Re-invoke against the same HEAD. The legacy path must NOT
    # produce any additional change (sidecar already at HEAD;
    # narrative already appended).
    rc2 = cli_main(["seal", "--no-finalize", str(manifest_path)])
    assert rc2 == 0
    status_after_run2 = _git(repo, "status", "--porcelain").stdout
    assert status_after_run1 == status_after_run2, (
        "second --no-finalize run must produce no additional diff"
    )


# ----------------------------------------------------------------------
# AC.D-sa.7 — plan-doc §14 SHA-backfill
# ----------------------------------------------------------------------


def _write_plan_doc_with_section_14(plan_path: Path) -> None:
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        textwrap.dedent(
            """
            # Fixture plan doc

            ## 1. Summary

            placeholder.

            ## 14. Method-decision record (builder, post-build)

            ### D-build.1 — placeholder
            placeholder rationale.
            """
        ).lstrip(),
        encoding="utf-8",
    )


def test_AC_D_sa_7_plan_doc_backfill_appends_subsection_and_commits(
    sealed_repo,
) -> None:
    """`--plan-doc <path>` appends `### Commit SHAs` under §14 and
    creates a deterministic follow-up commit naming both SHAs."""
    repo = sealed_repo
    plan_path = (
        repo / "docs" / "rebuild" / "plans" / "amendment-950-fixture.md"
    )
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", str(plan_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc with §14")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=950,
        slug="plan-doc-backfill",
        seal_description="backfill",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac7a")

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0

    # (a) Plan doc carries `### Commit SHAs` under §14
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "### Commit SHAs" in plan_text
    assert amendment_sha in plan_text

    # (b) HEAD is the follow-up commit with deterministic subject
    head_subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert (
        head_subject
        == "docs(plans): record amendment #950 commit SHAs in method-decision register"
    )

    # The commit before HEAD is the seal commit
    second_subject = _git(
        repo, "log", "-2", "--format=%s"
    ).stdout.strip().splitlines()[1]
    assert second_subject.startswith("chore(seals):")

    # Working tree clean
    status = _git(repo, "status", "--porcelain").stdout
    assert status == ""


def test_AC_D_sa_7_no_plan_doc_flag_no_followup_commit(sealed_repo) -> None:
    """Without `--plan-doc`, behaviour is byte-identical to AC.D-sa.1
    — no plan-doc edit, no follow-up commit (HEAD is the seal commit)."""
    repo = sealed_repo
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=951,
        slug="no-plan-doc-flag",
    )
    _make_amendment_commit(repo, "alpha", payload="ac7b")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc == 0

    head_subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert head_subject.startswith("chore(seals):"), (
        "without --plan-doc, HEAD is the seal commit (no follow-up)"
    )


def test_AC_D_sa_7_missing_section_14_halts_with_diagnostic(
    sealed_repo, capsys
) -> None:
    """A plan-doc without `## 14.` heading triggers a halt; the seal
    commit is left in place, no follow-up is committed."""
    repo = sealed_repo
    plan_path = (
        repo
        / "docs"
        / "rebuild"
        / "plans"
        / "amendment-952-no-section-14.md"
    )
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "# Fixture plan doc with no §14 section\n\n## 1. Summary\n\nbody.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(plan_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc no §14")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=952,
        slug="no-section-14",
    )
    _make_amendment_commit(repo, "alpha", payload="ac7c")

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc != 0

    # Seal commit is present (one above the amendment commit); no
    # follow-up commit was created.
    head_subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert head_subject.startswith("chore(seals):")

    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "plan-doc-missing-section-14" in combined or "## 14" in combined


def test_AC_D_sa_7_plan_doc_accepts_relative_path(
    sealed_repo, monkeypatch
) -> None:
    """`--plan-doc <relative-path>` resolves cleanly without
    crashing on `Path.relative_to`.

    Pre-fix behaviour: passing a relative path crashes inside
    `_finalize` at the post-backfill `plan_doc.relative_to(repo_root)`
    call (relative paths don't carry the repo root as an ancestor).
    Post-fix: the CLI dispatch normalises `--plan-doc` to its
    resolved absolute form before handing off to the subcommand,
    so the same backfill walk works against any cwd.
    """
    repo = sealed_repo
    plan_path = (
        repo / "docs" / "rebuild" / "plans" / "amendment-953-relpath.md"
    )
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", str(plan_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc for relpath test")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=953,
        slug="relpath",
        seal_description="relpath",
    )
    amendment_sha = _make_amendment_commit(
        repo, "alpha", payload="ac7d-relpath"
    )

    # Invoke `cli_main` from inside the repo with a RELATIVE plan-doc
    # path. Pre-fix this crashed; post-fix the CLI resolves the path
    # before passing it to the subcommand.
    monkeypatch.chdir(repo)
    rel_plan_str = str(plan_path.relative_to(repo))
    rel_manifest_str = str(manifest_path.relative_to(repo))
    assert not Path(rel_plan_str).is_absolute(), (
        "fixture sanity: rel_plan_str must be a relative path"
    )

    rc = cli_main(
        ["seal", "--plan-doc", rel_plan_str, rel_manifest_str]
    )
    assert rc == 0, "relative --plan-doc must not crash relative_to"

    # Plan doc carries `### Commit SHAs` under §14
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "### Commit SHAs" in plan_text
    assert amendment_sha in plan_text

    # HEAD is the deterministic follow-up commit
    head_subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert (
        head_subject
        == "docs(plans): record amendment #953 commit SHAs in method-decision register"
    )
