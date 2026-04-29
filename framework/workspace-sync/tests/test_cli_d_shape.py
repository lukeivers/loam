"""D-migration D.3 (amendment #64) — pos-sync CLI shape tests.

Verifies AC.D.3.1 through AC.D.3.6 against synthetic
workspace+canonical fixtures. The CLI is invoked via
``cli.main([...])``; the working directory is set explicitly via
``--workspace`` to avoid cwd-derivation noise.

HC#4 binding (byte-content match): assertions in
``test_AC_D_3_2_*`` and ``test_AC_D_3_4_*`` compare ``framework/``
file bytes against canonical's HEAD bytes.

HC#6 binding (structural guard): ``test_AC_D_3_4_*`` asserts every
file under ``<fixture-ws>/workspace/`` is byte-identical pre/post
``pos-sync``.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

# The stub-resolver module is loaded by the CLI via
# `--merge-resolver-module`. Import the module here so canned-verdict
# config + invocation-log access is available to tests.
import _stub_resolver
from loam.workspace_sync.cli import main as cli_main
from loam.workspace_sync.merge_resolver import MergeVerdict
from loam.workspace_sync.state import SyncOutcome, load_state


def _git(args: list[str], *, cwd: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _sha256_of_path(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _snapshot_tree_sha(root: Path) -> dict[str, str]:
    """Return {relpath -> sha256} for every regular file under root."""
    out: dict[str, str] = {}
    for p in root.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(root))
            out[rel] = _sha256_of_path(p)
    return out


# ---- AC.D.3.1 — git fetch advances remote ref ---------------------


def test_AC_D_3_1_git_fetch_advances_remote_ref(
    make_framework_workspace, advance_canonical
):
    """The CLI runs `git fetch canonical`; refs/remotes/canonical/<branch>
    advances post-fetch."""
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={
            "README.md": "# canonical\n",
            "src/foo.py": "x = 1\n",
        },
    )
    framework = fixture_ws / "framework"
    pre_fetch_remote_sha = _git(
        ["rev-parse", "refs/remotes/origin/pos-v2"], cwd=framework
    )
    advanced_sha = advance_canonical(
        canonical_root,
        {"src/foo.py": "x = 2\n"},
        message="bump x",
    )
    assert advanced_sha != pre_fetch_remote_sha

    rc = cli_main(["--workspace", str(fixture_ws)])
    assert rc == 0

    post_fetch_remote_sha = _git(
        ["rev-parse", "refs/remotes/canonical/pos-v2"], cwd=framework
    )
    assert post_fetch_remote_sha == advanced_sha


# ---- AC.D.3.2 — fast-forward happy path ---------------------------


def test_AC_D_3_2_fast_forward_advances_workspace_HEAD(
    make_framework_workspace, advance_canonical
):
    """Fast-forward case: framework/HEAD advances to canonical's HEAD;
    CLI exits 0; SyncState records FAST_FORWARD."""
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={
            "README.md": "# canonical v1\n",
            "src/foo.py": "x = 1\n",
        },
    )
    framework = fixture_ws / "framework"
    pre_head = _git(["rev-parse", "HEAD"], cwd=framework)
    new_canonical = advance_canonical(
        canonical_root,
        {"src/foo.py": "x = 2\n", "src/bar.py": "y = 1\n"},
        message="add bar; bump x",
    )
    assert new_canonical != pre_head

    rc = cli_main(["--workspace", str(fixture_ws)])
    assert rc == 0

    new_head = _git(["rev-parse", "HEAD"], cwd=framework)
    assert new_head == new_canonical, (
        "framework/HEAD must advance to canonical's HEAD on fast-forward"
    )

    state = load_state(fixture_ws)
    assert state is not None
    assert state.last_synced_sha == new_canonical
    assert state.last_outcome is SyncOutcome.FAST_FORWARD
    assert state.last_branch == "pos-v2"


def test_AC_D_3_2_byte_content_match_post_ff(
    make_framework_workspace, advance_canonical
):
    """HC#4 binding: post-fast-forward, every framework/<file> byte-
    equals canonical's HEAD bytes."""
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={
            "README.md": "# v1\n",
            "src/foo.py": "x = 1\n",
            "src/keep.py": "k = 0\n",
        },
    )
    framework = fixture_ws / "framework"
    advance_canonical(
        canonical_root,
        {
            "src/foo.py": "x = 42\n",
            "src/added.py": "added = True\n",
            "src/keep.py": None,  # delete
        },
        message="advance",
    )
    rc = cli_main(["--workspace", str(fixture_ws)])
    assert rc == 0

    # Each file in framework/ matches canonical's HEAD byte-for-byte.
    for rel in ["README.md", "src/foo.py", "src/added.py"]:
        framework_bytes = (framework / rel).read_bytes()
        canonical_bytes = (canonical_root / rel).read_bytes()
        assert framework_bytes == canonical_bytes, (
            f"{rel} bytes diverge post-FF"
        )
    # The deleted file is absent.
    assert not (framework / "src/keep.py").exists()


def test_AC_D_3_2_idempotent_on_already_synced(
    make_framework_workspace,
):
    """Re-running pos-sync against an already-up-to-date workspace
    is a no-op (UP_TO_DATE outcome)."""
    fixture_ws, _ = make_framework_workspace(
        canonical_files={"README.md": "# v1\n"},
    )
    rc1 = cli_main(["--workspace", str(fixture_ws)])
    assert rc1 == 0
    state1 = load_state(fixture_ws)
    assert state1 is not None
    rc2 = cli_main(["--workspace", str(fixture_ws)])
    assert rc2 == 0
    state2 = load_state(fixture_ws)
    assert state2 is not None
    assert state2.last_outcome is SyncOutcome.UP_TO_DATE
    assert state2.last_synced_sha == state1.last_synced_sha


# ---- AC.D.3.3 — non-FF fallback to LLM resolver -------------------


def test_AC_D_3_3_non_ff_falls_through_to_resolver(
    make_framework_workspace,
    advance_canonical,
    workspace_commit,
):
    """When the workspace has commits ahead of canonical AND canonical
    has commits with a real conflict, falls back to LLM resolver,
    which produces merged content; resulting git log shows a merge
    commit; framework/<file> carries resolver's merged content."""
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={
            "src/foo.py": "x = 1\n",
        },
    )
    framework = fixture_ws / "framework"
    # Workspace-side commit: edit foo.py.
    workspace_commit(
        fixture_ws,
        {"src/foo.py": "x = 99  # workspace edit\n"},
        message="ws bump",
    )
    # Canonical-side commit: edit foo.py differently.
    advance_canonical(
        canonical_root,
        {"src/foo.py": "x = 2  # canonical edit\n"},
        message="canon bump",
    )

    # Canned verdict — resolver produces merged content.
    _stub_resolver.reset()
    _stub_resolver.set_canned_verdicts(
        [
            MergeVerdict(
                resolution="inferred-merged",
                merged_content="x = 50  # merged\n",
                rationale="took the midpoint",
                confidence=0.95,
            )
        ]
    )

    rc = cli_main(
        [
            "--workspace",
            str(fixture_ws),
            "--merge-resolver-module",
            "_stub_resolver",
            "--auto-accept",
        ]
    )
    assert rc == 0, "non-FF fallback path should resolve cleanly + commit"

    # Resolver was invoked once on src/foo.py.
    invocations = _stub_resolver.invocations()
    assert len(invocations) == 1
    assert invocations[0]["path"] == "src/foo.py"

    # Resulting framework/<file> carries the resolver's merged content.
    assert (framework / "src/foo.py").read_text() == "x = 50  # merged\n"

    # git log shows a merge commit.
    log_out = _git(["log", "--oneline", "-3"], cwd=framework)
    # The most-recent commit is the merge.
    first_line = log_out.splitlines()[0]
    assert "Merge canonical" in first_line, (
        f"expected merge commit at HEAD, got: {first_line}"
    )

    state = load_state(fixture_ws)
    assert state is not None
    assert state.last_outcome is SyncOutcome.CONFLICT_FALLBACK


def test_AC_D_3_3_resolver_run_recorded_under_workspace_state(
    make_framework_workspace, advance_canonical, workspace_commit
):
    """AC.D.3.5 fallback variant: resolver-runs persist at
    <ws>/workspace/.pos/sync/resolver-runs/<sha>/<sanitised>.yaml."""
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={"src/foo.py": "x = 1\n"},
    )
    workspace_commit(
        fixture_ws,
        {"src/foo.py": "x = 99\n"},
        message="ws edit",
    )
    canon_sha = advance_canonical(
        canonical_root,
        {"src/foo.py": "x = 2\n"},
        message="canon edit",
    )

    _stub_resolver.reset()
    _stub_resolver.set_canned_verdicts(
        [
            MergeVerdict(
                resolution="inferred-accept-canonical",
                merged_content=None,
                rationale="canonical wins",
                confidence=0.92,
            )
        ]
    )

    rc = cli_main(
        [
            "--workspace",
            str(fixture_ws),
            "--merge-resolver-module",
            "_stub_resolver",
            "--auto-accept",
        ]
    )
    assert rc == 0

    runs_dir = (
        fixture_ws
        / "workspace"
        / ".pos"
        / "sync"
        / "resolver-runs"
        / canon_sha
    )
    assert runs_dir.exists(), (
        f"resolver-runs dir {runs_dir} must exist after fallback"
    )
    yaml_files = list(runs_dir.glob("*.yaml"))
    assert len(yaml_files) == 1
    # Sanitised path: src/foo.py -> src__foo.py
    assert yaml_files[0].name == "src__foo.py.yaml"
    import yaml as _yaml

    raw = _yaml.safe_load(yaml_files[0].read_text())
    assert raw["path"] == "src/foo.py"
    assert raw["verdict"]["resolution"] == "inferred-accept-canonical"
    assert raw["verdict"]["confidence"] == 0.92


# ---- AC.D.3.4 — Class-A protection structural ---------------------


def test_AC_D_3_4_workspace_state_byte_identical_pre_post_sync(
    make_framework_workspace, advance_canonical
):
    """HC#6 binding: every file under <fixture-ws>/workspace/ is
    byte-identical pre/post pos-sync. The merge operates exclusively
    inside framework/."""
    workspace_state = {
        ".pos/foo.txt": "operator-edited workspace state\n",
        ".pos/sync/state.yaml": "(seeded; will be overwritten by sync)\n",
        "personas/handle/contract.yaml": (
            "handle: handle\nis_starter: true\n"
        ),
        "memory.yaml": "operator preference data\n",
        ".scratch/notes.md": "ephemeral notes\n",
    }
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={
            "src/foo.py": "x = 1\n",
            "README.md": "# canonical\n",
        },
        workspace_files=workspace_state,
    )
    workspace_dir = fixture_ws / "workspace"
    pre_sync_snapshot = _snapshot_tree_sha(workspace_dir)

    advance_canonical(
        canonical_root,
        {"src/foo.py": "x = 2\n"},
        message="advance",
    )
    rc = cli_main(["--workspace", str(fixture_ws)])
    assert rc == 0

    post_sync_snapshot = _snapshot_tree_sha(workspace_dir)

    # The state.yaml under .pos/sync/ IS allowed to change (the CLI
    # writes the new SyncState there). Every OTHER workspace-state
    # file must be byte-identical pre/post.
    state_yaml_rel = ".pos/sync/state.yaml"
    pre_sans_state = {
        k: v for k, v in pre_sync_snapshot.items() if k != state_yaml_rel
    }
    post_sans_state = {
        k: v for k, v in post_sync_snapshot.items() if k != state_yaml_rel
    }

    assert pre_sans_state == post_sans_state, (
        "every workspace-state file (except state.yaml) must be byte-"
        "identical pre/post pos-sync"
    )


def test_AC_D_3_4_pos_sync_does_not_touch_workspace_subtree(
    make_framework_workspace, advance_canonical
):
    """Direct structural check: every git operation pos-sync runs
    targets framework/. workspace/ is not under git control via
    framework/'s .git, so pos-sync's git operations cannot reach it."""
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={"src/foo.py": "x = 1\n"},
        workspace_files={"personas/h/contract.yaml": "v: 1\n"},
    )
    framework = fixture_ws / "framework"
    advance_canonical(
        canonical_root,
        {"src/foo.py": "x = 2\n"},
        message="advance",
    )
    rc = cli_main(["--workspace", str(fixture_ws)])
    assert rc == 0

    # framework/'s git toplevel must be framework/, not fixture_ws/.
    toplevel = _git(["rev-parse", "--show-toplevel"], cwd=framework)
    assert Path(toplevel).resolve() == framework.resolve()

    # framework/.git/ does not contain any reference to workspace/ files.
    contracts_in_index = subprocess.run(
        ["git", "-C", str(framework), "ls-files", "--", "../workspace"],
        capture_output=True,
        text=True,
    )
    assert contracts_in_index.returncode != 0 or not contracts_in_index.stdout.strip(), (
        "framework/.git must not have workspace/ paths under control"
    )


# ---- AC.D.3.5 — audit derives from git log ------------------------


def test_AC_D_3_5_audit_summary_references_git_log(
    make_framework_workspace, advance_canonical, capsys
):
    """Fast-forward summary references the canonical commit subjects."""
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={"README.md": "# v1\n"},
    )
    advance_canonical(
        canonical_root,
        {"README.md": "# v2\n"},
        message="distinctive-commit-subject-marker-XYZ",
    )
    rc = cli_main(["--workspace", str(fixture_ws)])
    assert rc == 0

    captured = capsys.readouterr()
    # The CLI prints the git-log lines on stderr.
    assert "distinctive-commit-subject-marker-XYZ" in captured.err
    assert "fast-forwarded" in captured.err


# ---- AC.D.3.6 — pre-D.3 code retired ------------------------------


def test_AC_D_3_6_retired_modules_absent():
    """Smoke test: the retired modules are gone from disk."""
    src = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "loam" / "workspace_sync"
    )
    retired = [
        "ancestor_detection.py",
        "conflict_detection.py",
        "conflict_report.py",
        "merge_helper.py",
        "merge_primitives.py",
        "staging.py",
    ]
    for name in retired:
        path = src / name
        assert not path.exists(), (
            f"retired module {name} must be absent post-D.3 "
            f"(found at {path})"
        )


def test_AC_D_3_6_retained_modules_present():
    """The retained surface is still present."""
    src = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "loam" / "workspace_sync"
    )
    retained = [
        "__init__.py",
        "_audit.py",
        "_resolver_client.py",
        "canonical.py",
        "canonical_cache.py",
        "cli.py",
        "merge_resolver.py",
        "observability.py",
        "state.py",
        "sync_config.py",
        "sync_protected.py",
    ]
    for name in retained:
        path = src / name
        assert path.exists(), f"retained module {name} must exist post-D.3"


def test_AC_D_3_6_cli_does_not_import_retired_modules():
    """cli.py source does not reference the retired modules."""
    cli_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "loam" / "workspace_sync"
        / "cli.py"
    )
    text = cli_path.read_text()
    forbidden = [
        "from .ancestor_detection",
        "from .conflict_detection",
        "from .conflict_report",
        "from .merge_helper",
        "from .merge_primitives",
        "from .staging",
        "import ancestor_detection",
        "import conflict_detection",
        "import conflict_report",
        "import merge_helper",
        "import merge_primitives",
        "import staging",
    ]
    for forbidden_substr in forbidden:
        assert forbidden_substr not in text, (
            f"cli.py must not import retired module: {forbidden_substr!r}"
        )


# ---- supporting tests for CLI shape ------------------------------


def test_workspace_root_derivation_post_D(tmp_path: Path):
    """derive_workspace_root accepts framework/.git/ marker (post-D)."""
    from loam.workspace_sync.cli import derive_workspace_root

    ws = tmp_path / "ws"
    (ws / "framework" / ".git").mkdir(parents=True)
    derived = derive_workspace_root(workspace_arg=None, cwd=ws)
    assert derived == ws


def test_workspace_root_derivation_post_D2(tmp_path: Path):
    """derive_workspace_root accepts workspace/.pos/sync-protected.yaml
    marker (post-D.2)."""
    from loam.workspace_sync.cli import derive_workspace_root

    ws = tmp_path / "ws"
    sp = ws / "workspace" / ".pos" / "sync-protected.yaml"
    sp.parent.mkdir(parents=True)
    sp.write_text("framework_floor: []\nworkspace_rules: []\n")
    derived = derive_workspace_root(workspace_arg=None, cwd=ws)
    assert derived == ws


def test_workspace_root_derivation_pre_D2_back_compat(tmp_path: Path):
    """derive_workspace_root accepts .pos/sync-protected.yaml marker
    (pre-D.2 back-compat)."""
    from loam.workspace_sync.cli import derive_workspace_root

    ws = tmp_path / "ws"
    sp = ws / ".pos" / "sync-protected.yaml"
    sp.parent.mkdir(parents=True)
    sp.write_text("framework_floor: []\nworkspace_rules: []\n")
    derived = derive_workspace_root(workspace_arg=None, cwd=ws)
    assert derived == ws


def test_workspace_root_derivation_no_marker_fails(tmp_path: Path):
    """derive_workspace_root halts with structured error when no marker
    is present."""
    from loam.workspace_sync.cli import (
        WorkspaceRootError,
        derive_workspace_root,
    )

    ws = tmp_path / "empty_ws"
    ws.mkdir()
    with pytest.raises(WorkspaceRootError):
        derive_workspace_root(workspace_arg=None, cwd=ws)


def test_cli_halts_when_framework_git_absent(
    make_workspace, make_canonical_repo, capsys
):
    """When <ws>/framework/ is absent or not a git tree, the CLI
    halts with structured error pointing at pos-new-workspace."""
    canonical = make_canonical_repo({"README.md": "# canon\n"})
    ws = make_workspace(
        files={
            "workspace/.pos/sync-config.yaml": (
                f"canonical_source: {canonical}\n"
            ),
            "workspace/.pos/sync-protected.yaml": (
                "framework_floor: []\nworkspace_rules: []\n"
            ),
        }
    )
    # Note: ws does NOT have a framework/ directory.
    rc = cli_main(["--workspace", str(ws)])
    assert rc == 2
    captured = capsys.readouterr()
    err = captured.err.lower()
    assert "framework" in err
    assert "pos-new-workspace" in err


def test_cli_halts_when_no_canonical_source(make_workspace, capsys):
    """When neither --canonical nor sync-config.yaml provides a
    canonical_source, the CLI halts with structured error."""
    ws = make_workspace(
        files={
            "framework/.git/HEAD": "ref: refs/heads/pos-v2\n",
        }
    )
    # SystemExit comes from argparse.error() — catch it.
    with pytest.raises(SystemExit):
        cli_main(["--workspace", str(ws)])
    captured = capsys.readouterr()
    assert "canonical" in captured.err.lower()


def test_cli_argparse_canonical_flag_overrides_config(
    make_framework_workspace, tmp_path
):
    """CLI --canonical flag overrides sync-config.yaml's canonical_source."""
    fixture_ws, primary_canonical = make_framework_workspace(
        canonical_files={"README.md": "# primary\n"},
    )
    # Build a SECOND canonical with different content.
    second_canonical = tmp_path / "second_canonical"
    subprocess.run(
        ["git", "init", "-q", "-b", "pos-v2", str(second_canonical)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(second_canonical), "config", "user.email", "t@t"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(second_canonical), "config", "user.name", "t"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(second_canonical),
            "config",
            "commit.gpgsign",
            "false",
        ],
        check=True,
    )
    (second_canonical / "README.md").write_text("# SECOND\n")
    subprocess.run(
        ["git", "-C", str(second_canonical), "add", "-A"], check=True
    )
    subprocess.run(
        ["git", "-C", str(second_canonical), "commit", "-q", "-m", "second"],
        check=True,
    )

    # The fixture's framework/ was cloned from primary_canonical (origin
    # remote). pos-sync sets up a 'canonical' remote pointing at the
    # passed --canonical path. The merge target ref is `canonical/HEAD`,
    # which on the second canonical points at the second's HEAD.
    # Fast-forward fails because the framework's HEAD shares no history
    # with second_canonical — the merge falls to the resolver path.
    # For this test we just verify the remote URL gets configured.
    rc = cli_main(
        [
            "--workspace",
            str(fixture_ws),
            "--canonical",
            str(second_canonical),
        ]
    )
    # Don't assert rc; the merge will fail (no shared history). But the
    # remote should have been configured.
    framework = fixture_ws / "framework"
    completed = subprocess.run(
        ["git", "-C", str(framework), "config", "--get", "remote.canonical.url"],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout.strip() == str(second_canonical)
