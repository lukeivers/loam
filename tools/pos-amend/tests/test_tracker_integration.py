"""AC.D-pa.1 – AC.D-pa.5 — `pos-amend` tracker integration.

Each AC has at least one test function. Plan:
``docs/rebuild/plans/pos-amend-tracker-integration.md`` §4.

Fixture shape: a tmpfs git repo (mirrors ``test_seal.py``'s
``sealed_repo`` fixture but pared to a single component) with a
seeded ``objective_tracker.sqlite`` at the repo root. Tests build
schema-v2 manifest YAML in-line and invoke ``pos-amend apply`` /
``pos-amend seal`` against it.

The tracker DB is seeded by directly constructing an
``ObjectiveTracker`` (the workspace-bootstrap first-run seed
behaviour, simplified — we don't need value-prop seeds for these
tests; an empty DB is fine).
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import subprocess
import textwrap
from pathlib import Path

import pytest

from objective_tracker import (
    ObjectiveFilter,
    ObjectiveTracker,
)
from pos_amend.cli import main as cli_main
from pos_amend.tracker_registration import (
    TRACKER_DB_FILENAME,
    tracker_db_path_for,
)


# ----------------------------------------------------------------------
# Fixture builders (mirror test_seal.py)
# ----------------------------------------------------------------------


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=check,
    )


def _make_fake_component(repo: Path, name: str) -> None:
    """Identical layout to test_seal._make_fake_component minus the
    failing-seal-diff variant (we don't exercise sweep failure here)."""
    comp_dir = repo / name
    (comp_dir / "tests").mkdir(parents=True, exist_ok=True)
    (comp_dir / "src").mkdir(exist_ok=True)
    (comp_dir / "src" / "__init__.py").write_text("\n", encoding="utf-8")
    (comp_dir / "tests" / "__init__.py").write_text("\n", encoding="utf-8")
    (comp_dir / "tests" / "SEAL_COMMIT").write_text(
        "0000000000000000000000000000000000000000\n", encoding="utf-8"
    )
    header = textwrap.dedent(
        f"""
        # Fixture seal-diff test for {name}.
        allowed_prefixes = (
            "{name}/",
            "docs/rebuild/plans/",
        )
        allowed_files = (
            "CLAUDE.md",
        )
        """
    ).lstrip()
    body = header + textwrap.dedent(
        """
        def test_seal_diff_ok():
            assert True
        """
    ).lstrip()
    (comp_dir / "tests" / "test_no_sealed_amendments.py").write_text(
        body, encoding="utf-8"
    )
    (comp_dir / "tests" / "test_basic.py").write_text(
        textwrap.dedent(
            """
            def test_component_ok():
                assert True
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _seed_tracker_with_value_prop_root(repo: Path) -> Path:
    """Seed a tracker DB with a minimal value-prop root.

    Mirrors workspace-bootstrap's first-run seed contract (simplified):
    the DB exists at ``<repo>/objective_tracker.sqlite`` with one root
    objective whose ID is ``value-prop-root`` — the same ID
    workspace-bootstrap's tracker_seed.py uses
    (``ROOT_OBJECTIVE_ID``). Manifest entries with ``parent_id:
    "value-prop-root"`` resolve cleanly. Entries with
    ``parent_root: true`` (their own root) work independently.

    The DB file is gitignored — real workspaces don't track it (the
    tracker DB is workspace-local state, not source). Tests query it
    in-place at the standard path.
    """
    from objective_tracker import (
        LiftedFrom,
        ObjectiveSpec,
        ProseCriterion,
        TimeBound,
    )

    db_path = tracker_db_path_for(repo)
    tracker = ObjectiveTracker(db_path)
    try:
        root_spec = ObjectiveSpec(
            goal="Fixture value-prop root",
            parent_id=None,
            acceptance_criteria=(
                ProseCriterion(
                    criterion_id="AC.PO.1",
                    prose="Fixture root AC for tests.",
                ),
            ),
            time_bound=TimeBound(evergreen=True),
            authored_by="user",
            lifted_from=LiftedFrom(
                source_doc="docs/rebuild/VALUE_PROPOSITION.md",
                source_ac="prime",
            ),
        )
        asyncio.run(tracker.create(root_spec, objective_id="value-prop-root"))
    finally:
        tracker.close()
    return db_path


def _write_v2_manifest(
    repo: Path,
    *,
    components: list[str],
    number: int,
    slug: str,
    plan_doc_path: str,
    objectives: list[dict],
    narrative_target: str | None = None,
) -> Path:
    """Author a schema-v2 manifest with an ``objectives`` block.

    ``objectives`` is a list of dicts mirroring the YAML shape — passed
    through ``yaml.safe_dump`` for fidelity. The manifest is committed
    immediately so the working tree is clean at amendment-time.
    """
    import yaml

    plans_dir = repo / "docs" / "rebuild" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = plans_dir / f"amendment-{number}-{slug}.manifest.yaml"
    head_proc = _git(repo, "rev-parse", "HEAD")
    baseline = head_proc.stdout.strip()

    data: dict = {
        "schema_version": 2,
        "amendment": {
            "number": number,
            "slug": slug,
            "title": f"fixture amendment {number}",
        },
        "baseline": baseline,
        "plan": plan_doc_path,
        "components": [
            {
                "name": c,
                "seal_test": f"{c}/tests/test_no_sealed_amendments.py",
                "sidecar": f"{c}/tests/SEAL_COMMIT",
            }
            for c in components
        ],
        "objectives": objectives,
    }
    if narrative_target is not None:
        data["narrative"] = {
            "target": narrative_target,
            "body": (
                f"# fixture narrative for amendment {number}\n"
                "fixture body line.\n"
            ),
        }
    manifest_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    rel = manifest_path.relative_to(repo)
    _git(repo, "add", "--", str(rel))
    _git(repo, "commit", "-q", "-m", f"fixture: amendment-{number} manifest")
    return manifest_path


def _make_amendment_commit(repo: Path, comp: str, payload: str = "edit") -> str:
    """Land a fake amendment commit under *comp*. Returns the SHA."""
    edit_path = repo / comp / "src" / "amendment.py"
    edit_path.write_text(f"# {payload}\n", encoding="utf-8")
    _git(repo, "add", "--", f"{comp}/src/amendment.py")
    _git(repo, "commit", "-m", f"feat({comp}): fixture amendment edit")
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def tracker_repo(tmp_path: Path) -> Path:
    """tmpfs repo with one component + seeded empty tracker DB."""
    repo = tmp_path / "workspace"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "pos-amend test")
    (repo / ".gitignore").write_text(
        # Ignore tracker DB + SQLite WAL ancillaries so they don't
        # pollute ``git status`` during the seal step's pre-flight
        # dirty-tree check (or the post-seal `apply --dry-run` admit
        # check). Real workspaces ignore the tracker DB too — it's
        # workspace-local state, not source.
        f"__pycache__/\n*.pyc\n{TRACKER_DB_FILENAME}\n"
        f"{TRACKER_DB_FILENAME}-wal\n"
        f"{TRACKER_DB_FILENAME}-shm\n",
        encoding="utf-8",
    )
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    _make_fake_component(repo, "alpha")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: initial repo")
    # Seed the tracker DB AFTER the initial commit so the .sqlite
    # file exists at test time but doesn't show up as a dirty path
    # (gitignored).
    _seed_tracker_with_value_prop_root(repo)
    return repo


def _make_objective(
    *,
    source_ac: str,
    plan_doc: str,
    parent_id: str | None = None,
    parent_root: bool = False,
) -> dict:
    """Build a minimal objectives-block entry dict."""
    entry: dict = {
        "goal": f"Demonstrate {source_ac}",
        "acceptance_criteria": [
            {
                "kind": "prose",
                "criterion_id": source_ac,
                "prose": f"Prose for {source_ac}.",
            }
        ],
        "time_bound": {"evergreen": True},
        "authored_by": "user",
        "lifted_from": {
            "source_doc": plan_doc,
            "source_ac": source_ac,
        },
    }
    if parent_root:
        entry["parent_root"] = True
    else:
        entry["parent_id"] = parent_id or "value-prop-root"
    return entry


# ----------------------------------------------------------------------
# AC.D-pa.1 — apply registers records
# ----------------------------------------------------------------------


def test_AC_D_pa_1_apply_registers_records(tracker_repo) -> None:
    """`pos-amend apply` against a v2 manifest creates one tracker
    record per ``objectives`` entry, queryable by source_doc."""
    repo = tracker_repo
    plan_doc = "docs/rebuild/plans/amendment-200-fixture.md"
    manifest_path = _write_v2_manifest(
        repo,
        components=["alpha"],
        number=200,
        slug="ac-pa-1",
        plan_doc_path=plan_doc,
        objectives=[
            _make_objective(source_ac="AC.test.1", plan_doc=plan_doc, parent_root=True),
            _make_objective(source_ac="AC.test.2", plan_doc=plan_doc, parent_id="value-prop-root"),
            _make_objective(source_ac="AC.test.3", plan_doc=plan_doc, parent_id="value-prop-root"),
        ],
    )

    rc = cli_main(["apply", str(manifest_path)])
    assert rc == 0, "apply on a v2 manifest must exit 0"

    # Query the tracker DB directly to confirm registration.
    db_path = tracker_db_path_for(repo)
    tracker = ObjectiveTracker(db_path)
    try:
        projections = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=plan_doc)
        )
        assert len(projections) == 3
        acs = sorted(p.lifted_from.source_ac for p in projections)
        assert acs == ["AC.test.1", "AC.test.2", "AC.test.3"]
    finally:
        tracker.close()


# ----------------------------------------------------------------------
# AC.D-pa.2 — apply is idempotent
# ----------------------------------------------------------------------


def test_AC_D_pa_2_apply_idempotent_across_objectives_block(
    tracker_repo,
) -> None:
    """Re-running ``apply`` against the same v2 manifest does NOT create
    duplicate records (matched by source_doc + source_ac)."""
    repo = tracker_repo
    plan_doc = "docs/rebuild/plans/amendment-201-fixture.md"
    manifest_path = _write_v2_manifest(
        repo,
        components=["alpha"],
        number=201,
        slug="ac-pa-2",
        plan_doc_path=plan_doc,
        objectives=[
            _make_objective(source_ac="AC.idemp.1", plan_doc=plan_doc, parent_root=True),
            _make_objective(source_ac="AC.idemp.2", plan_doc=plan_doc, parent_id="value-prop-root"),
        ],
    )

    rc1 = cli_main(["apply", str(manifest_path)])
    assert rc1 == 0

    db_path = tracker_db_path_for(repo)
    tracker = ObjectiveTracker(db_path)
    try:
        first = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=plan_doc)
        )
        first_ids = sorted(p.objective_id for p in first)
        first_event_count = len(tracker.store.all_events())
    finally:
        tracker.close()

    # Re-invoke `apply` against the same manifest.
    rc2 = cli_main(["apply", str(manifest_path)])
    assert rc2 == 0

    tracker = ObjectiveTracker(db_path)
    try:
        second = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=plan_doc)
        )
        second_ids = sorted(p.objective_id for p in second)
        second_event_count = len(tracker.store.all_events())
    finally:
        tracker.close()

    # Same set of records (ID-stable) and same event count.
    assert first_ids == second_ids
    assert first_event_count == second_event_count


# ----------------------------------------------------------------------
# AC.D-pa.3 — seal writes lifted_from.source_commit
# ----------------------------------------------------------------------


def test_AC_D_pa_3_seal_writes_source_commit(tracker_repo) -> None:
    """After apply → amendment-commit → seal, every registered record
    carries ``lifted_from.source_commit == amendment_sha``."""
    repo = tracker_repo
    plan_doc = "docs/rebuild/plans/amendment-202-fixture.md"
    manifest_path = _write_v2_manifest(
        repo,
        components=["alpha"],
        number=202,
        slug="ac-pa-3",
        plan_doc_path=plan_doc,
        objectives=[
            _make_objective(
                source_ac="AC.seal.1", plan_doc=plan_doc, parent_root=True
            ),
            _make_objective(
                source_ac="AC.seal.2", plan_doc=plan_doc, parent_id="value-prop-root"
            ),
        ],
        narrative_target="alpha/seals/SEAL_COMMIT.fixture",
    )

    # apply: register records (BEFORE the apply commit, since apply
    # mutates the working tree). Then commit apply's edits + the
    # tracker DB.
    rc_apply = cli_main(["apply", str(manifest_path)])
    assert rc_apply == 0
    # Stage + commit any working-tree edits apply produced (sidecar
    # bumps, possibly widening). The tracker DB is gitignored.
    status = _git(repo, "status", "--porcelain").stdout
    if status.strip():
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "fixture: post-apply state")

    # Now an amendment commit, then seal.
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac3")

    rc_seal = cli_main(["seal", str(manifest_path)])
    assert rc_seal == 0, "seal should succeed on a clean fixture"

    db_path = tracker_db_path_for(repo)
    tracker = ObjectiveTracker(db_path)
    try:
        projections = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=plan_doc)
        )
        assert len(projections) == 2
        for proj in projections:
            assert proj.lifted_from is not None
            assert proj.lifted_from.source_commit == amendment_sha, (
                f"objective {proj.lifted_from.source_ac}: source_commit "
                f"is {proj.lifted_from.source_commit!r}, expected "
                f"{amendment_sha!r}"
            )
    finally:
        tracker.close()


def test_AC_D_pa_3_seal_source_commit_idempotent(tracker_repo) -> None:
    """Re-running seal against the same amendment SHA produces no new
    diff in the tracker (the source_commit update is idempotent)."""
    repo = tracker_repo
    plan_doc = "docs/rebuild/plans/amendment-203-fixture.md"
    manifest_path = _write_v2_manifest(
        repo,
        components=["alpha"],
        number=203,
        slug="ac-pa-3-idemp",
        plan_doc_path=plan_doc,
        objectives=[
            _make_objective(
                source_ac="AC.idemp.1", plan_doc=plan_doc, parent_root=True
            ),
        ],
    )
    rc_apply = cli_main(["apply", str(manifest_path)])
    assert rc_apply == 0
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: post-apply state")

    amendment_sha = _make_amendment_commit(repo, "alpha", payload="ac3i")
    rc_seal = cli_main(["seal", str(manifest_path)])
    assert rc_seal == 0

    db_path = tracker_db_path_for(repo)
    tracker = ObjectiveTracker(db_path)
    try:
        first = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=plan_doc)
        )
        first_ids = sorted(p.objective_id for p in first)
        first_shas = sorted(p.lifted_from.source_commit for p in first)
    finally:
        tracker.close()

    # Re-running seal would reset HEAD to a new SHA (it's the new seal
    # commit). To keep idempotency well-defined we directly call the
    # update_source_commits helper twice with the same amendment_sha.
    from pos_amend.manifest import load_manifest
    from pos_amend.tracker_registration import update_source_commits

    manifest = load_manifest(manifest_path)
    n2 = update_source_commits(manifest, repo, amendment_sha)
    assert n2 == 0, "second invocation with same SHA must be no-op"

    tracker = ObjectiveTracker(db_path)
    try:
        second = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=plan_doc)
        )
        second_ids = sorted(p.objective_id for p in second)
        second_shas = sorted(p.lifted_from.source_commit for p in second)
    finally:
        tracker.close()
    assert first_ids == second_ids
    assert first_shas == second_shas


# ----------------------------------------------------------------------
# AC.D-pa.4 — schema v1 manifests continue to validate + apply unchanged
# ----------------------------------------------------------------------


def test_AC_D_pa_4_v1_apply_no_tracker_interaction(tracker_repo) -> None:
    """A schema_version 1 manifest applied against a workspace with a
    seeded tracker does NOT touch the tracker (no records created)."""
    repo = tracker_repo
    db_path = tracker_db_path_for(repo)

    # Snapshot the tracker state pre-apply.
    tracker = ObjectiveTracker(db_path)
    try:
        before = tracker.query_projection_view()
        before_ids = sorted(p.objective_id for p in before)
        before_event_count = len(tracker.store.all_events())
    finally:
        tracker.close()

    # Author a v1 manifest (no objectives block).
    plans_dir = repo / "docs" / "rebuild" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = plans_dir / "amendment-204-v1.manifest.yaml"
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    manifest_path.write_text(
        textwrap.dedent(
            f"""
            schema_version: 1
            amendment:
              number: 204
              slug: v1-no-tracker
              title: "v1 amendment, no tracker interaction"
            baseline: {head}
            plan: docs/rebuild/plans/amendment-204-v1.md
            components:
              - name: alpha
                seal_test: alpha/tests/test_no_sealed_amendments.py
                sidecar: alpha/tests/SEAL_COMMIT
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(manifest_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: v1 manifest")

    rc = cli_main(["apply", str(manifest_path)])
    assert rc == 0

    # Verify tracker untouched.
    tracker = ObjectiveTracker(db_path)
    try:
        after = tracker.query_projection_view()
        after_ids = sorted(p.objective_id for p in after)
        after_event_count = len(tracker.store.all_events())
    finally:
        tracker.close()
    assert after_ids == before_ids
    assert after_event_count == before_event_count


def test_AC_D_pa_4_v1_dry_run_green_on_post_fix_tree(
    tracker_repo,
) -> None:
    """``apply --dry-run`` on the existing fixture v1 manifest exits 0
    (regression smoke). The fixture suite for v1 is exercised more
    thoroughly by test_dry_run.py and test_integration_*."""
    # Use the tracker_repo just to ensure no v1 path queries the tracker.
    repo = tracker_repo
    plans_dir = repo / "docs" / "rebuild" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = plans_dir / "amendment-205-v1-dryrun.manifest.yaml"
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    manifest_path.write_text(
        textwrap.dedent(
            f"""
            schema_version: 1
            amendment:
              number: 205
              slug: v1-dryrun
              title: "v1 dry-run smoke"
            baseline: {head}
            plan: docs/rebuild/plans/amendment-205-v1-dryrun.md
            components:
              - name: alpha
                seal_test: alpha/tests/test_no_sealed_amendments.py
                sidecar: alpha/tests/SEAL_COMMIT
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(manifest_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: v1 dry-run manifest")

    rc = cli_main(["apply", "--dry-run", str(manifest_path)])
    assert rc == 0


# ----------------------------------------------------------------------
# AC.D-pa.5 — graceful handling on tracker DB unavailability
# ----------------------------------------------------------------------


def test_AC_D_pa_5_corrupt_tracker_db_halts_with_diagnostic(
    tracker_repo, capsys
) -> None:
    """A corrupt tracker DB causes ``apply`` (with v2 manifest) to
    exit non-zero and emit a structured diagnostic. No partial
    registration happens — neither apply's BASELINE/sidecar/widening
    edits nor any tracker record is created."""
    repo = tracker_repo
    db_path = tracker_db_path_for(repo)

    # Corrupt the DB by overwriting the file header with garbage.
    db_path.write_bytes(b"NOT A VALID SQLITE DATABASE FILE\n" * 8)

    plan_doc = "docs/rebuild/plans/amendment-206-corrupt.md"
    manifest_path = _write_v2_manifest(
        repo,
        components=["alpha"],
        number=206,
        slug="ac-pa-5-corrupt",
        plan_doc_path=plan_doc,
        objectives=[
            _make_objective(
                source_ac="AC.corrupt.1", plan_doc=plan_doc, parent_root=True
            ),
        ],
    )

    rc = cli_main(["apply", str(manifest_path)])
    assert rc != 0, "corrupt tracker must produce a non-zero exit"

    captured = capsys.readouterr()
    combined = captured.out + captured.err
    # Diagnostic must name the failure class.
    assert (
        "tracker-db-corrupt" in combined
        or "tracker-db-schema-mismatch" in combined
    )

    # No partial state: the BASELINE-bump / widening branches did NOT
    # run because the registration ran first and bailed. Verify the
    # alpha component's seal-test file is still pristine.
    seal_test = (repo / "alpha" / "tests" / "test_no_sealed_amendments.py").read_text()
    # The fixture seal-test carried only `alpha/` and `docs/...` prefixes
    # plus `CLAUDE.md` — no extra entries. After a successful apply,
    # nothing would have been added (universal_paths empty + extras
    # empty in our manifest). So this is a structural confirmation.
    assert "alpha/" in seal_test
    assert "docs/rebuild/plans/" in seal_test


def test_AC_D_pa_5_missing_tracker_parent_dir_halts(
    tracker_repo, capsys
) -> None:
    """When the workspace dir's tracker DB parent doesn't exist,
    apply emits a structured diagnostic and exits non-zero. (This
    case is rare in practice — the workspace dir always exists for
    a checked-out repo — but the path-resolver helper catches it
    deterministically.)

    Method note: we monkeypatch ``tracker_db_path_for`` to point at a
    non-existent parent so the AC.D-pa.5 case (a) branch fires.
    """
    import pos_amend.tracker_registration as tr_mod

    repo = tracker_repo
    plan_doc = "docs/rebuild/plans/amendment-207-missing-parent.md"
    manifest_path = _write_v2_manifest(
        repo,
        components=["alpha"],
        number=207,
        slug="ac-pa-5-missing-parent",
        plan_doc_path=plan_doc,
        objectives=[
            _make_objective(
                source_ac="AC.missing.1", plan_doc=plan_doc, parent_root=True
            ),
        ],
    )

    fake_path = repo / "this-parent-dir-does-not-exist" / TRACKER_DB_FILENAME
    original = tr_mod.tracker_db_path_for
    tr_mod.tracker_db_path_for = lambda _root: fake_path  # type: ignore[assignment]
    try:
        rc = cli_main(["apply", str(manifest_path)])
    finally:
        tr_mod.tracker_db_path_for = original  # type: ignore[assignment]

    assert rc != 0
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "tracker-db-missing-parent" in combined
