# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""D-migration D.4 (amendment #65) — `pos-new-workspace` tests.

Verifies AC.D.4.1, AC.D.4.2, AC.D.4.3 against synthetic-fixture
canonical sources. HC#4 binding: byte-content-match for every
``<new-ws>/framework/<file>`` against canonical's HEAD bytes.
HC#6 binding: workspace-state lives under ``<new-ws>/workspace/``
exclusively (apart from ``.claude/`` per D-Q.A4 lock).

Test isolation:

- Fixture canonical built per-test via ``make_fixture_canonical`` (no
  shared state).
- Cache-clone tests redirect ``Path.home()`` via monkeypatch so
  ``ensure_cache_clone`` writes inside ``tmp_path`` instead of the
  operator's actual home dir.
- Tracker-seed runner stubbed to a no-op so D.4 tests don't couple to
  the objective-tracker subsystem.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from loam.workspace_bootstrap.adapters import tracker_seed
from loam.workspace_bootstrap.new_workspace import (
    BootstrapResult,
    CanonicalSourceInvalidError,
    CloneFailedError,
    NewWorkspaceError,
    TargetNotEmptyError,
    bootstrap_new_workspace,
    build_parser,
    cli_main,
)
from loam.workspace_bootstrap.workspace_paths import (
    POS_SUBDIR,
    WORKSPACE_STATE_SUBDIR,
)


# ---- helpers -------------------------------------------------------


def _stub_tracker_seed_runner(**_kwargs: Any) -> Any:
    """No-op tracker-seed runner. Mirrors test_AC47_1's helper."""
    return tracker_seed.TrackerSeedResult(
        seeded=False,
        reason="skipped_test_stub",
        classification="user",
        root_id=None,
        descendants_seeded=(),
        value_prop_source=None,
    )


def _read_canonical_blob(canonical_root: Path, rel_path: str) -> str:
    """Return canonical's ``HEAD:<rel_path>`` content via git show.

    Used for byte-content-match against the bootstrapped framework/
    subtree (HC#4). Reading via git ensures the comparison is against
    the committed bytes, not whatever happens to be in the canonical
    working tree at test time.
    """
    completed = subprocess.run(  # noqa: S603 — argv constructed
        ["git", "show", f"HEAD:{rel_path}"],
        cwd=str(canonical_root),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
    )
    return completed.stdout


# ---- AC.D.4.1 — local canonical creates working workspace ----------


def test_AC_D_4_1_local_canonical_creates_working_workspace(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """Bootstrap from a local-path canonical produces the D-shape
    layout with HC#4 byte-content match for framework/ files.
    """
    canonical = make_fixture_canonical(tmp_path / "fixture-canonical")
    new_ws = tmp_path / "new-ws"
    agents = tmp_path / "LaunchAgents"

    result = bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(canonical),
        service_manager_dir_override=agents,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    # AC.D.4.1: framework/ exists + cloned.
    assert result.framework_dir == new_ws / "framework"
    assert result.framework_dir.is_dir()
    assert (result.framework_dir / ".git").exists()

    # AC.D.4.1 (HC#4) + AC.SFR.1: byte-content-match for every fixture
    # file. Post single-framework restructure (amendment #67) the
    # bootstrap clones the `framework-only` branch; canonical's
    # `framework/<entry>` lands at `<new-ws>/framework/<entry>` (single
    # level). Top-level docs land at `<new-ws>/framework/<doc>` because
    # framework-only carries them at the synthetic-branch root.
    #
    # Each tuple is (canonical-pos-v2-path, workspace-side-path).
    fixture_pairs = [
        # framework entries: pos-v2 has `framework/X`, framework-only
        # promotes to `X` at root, workspace-side lives at
        # `<new-ws>/framework/X`.
        ("framework/workspace-sync/src/workspace_sync/__init__.py",
         "framework/workspace-sync/src/workspace_sync/__init__.py"),
        ("framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py",
         "framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py"),
        ("framework/README.md", "framework/README.md"),
        # Top-level docs: pos-v2 has them at root; framework-only
        # carries them at root verbatim; workspace-side they land at
        # `<new-ws>/framework/<doc>` (the readers fall through per
        # AC.SFR.3).
        ("docs/odd-methodology.md", "framework/docs/odd-methodology.md"),
        ("CLAUDE.md", "framework/CLAUDE.md"),
    ]
    for canonical_rel, workspace_rel in fixture_pairs:
        canonical_bytes = _read_canonical_blob(canonical, canonical_rel)
        on_disk = (new_ws / workspace_rel).read_text()
        assert on_disk == canonical_bytes, (
            f"HC#4 byte-content-match failed for "
            f"{canonical_rel!r} → {workspace_rel!r}: "
            f"on_disk={on_disk!r} vs canonical={canonical_bytes!r}"
        )

    # AC.SFR.1: no doubling — `<new-ws>/framework/framework/` MUST NOT
    # exist (the failure class the restructure eliminates).
    assert not (new_ws / "framework" / "framework").exists(), (
        f"AC.SFR.1: doubling failure class re-introduced; "
        f"<new-ws>/framework/framework/ exists at "
        f"{new_ws / 'framework' / 'framework'}"
    )

    # AC.SFR.1: workspace's framework/ tracks framework-only as origin
    # (so subsequent pos-sync operates against the synthetic branch,
    # AC.SFR.4 binding).
    head_branch = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(new_ws / "framework"),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert head_branch == "framework-only", (
        f"AC.SFR.1: cloned branch is {head_branch!r}, expected "
        f"'framework-only'"
    )

    # AC.D.4.1: workspace/ scaffolded.
    workspace_state = new_ws / WORKSPACE_STATE_SUBDIR
    assert workspace_state.is_dir(), (
        f"AC.D.4.1: <new-ws>/workspace/ must exist; got {workspace_state}"
    )

    # AC.D.4.1: workspace/.pos/sync-config.yaml carries canonical_source.
    sync_config = workspace_state / POS_SUBDIR / "sync-config.yaml"
    assert sync_config.exists()
    assert result.sync_config_path == sync_config
    payload = sync_config.read_text()
    assert f"canonical_source: {canonical}" in payload, (
        f"sync-config.yaml does not carry canonical_source; got:\n{payload}"
    )

    # AC.D.4.1: .claude/ at workspace root (D-Q.A4).
    # The scaffold doesn't create .claude/ directly today (it's part of
    # workspace-bootstrap's separate path); verify .claude_dir is named
    # at the right location even if the directory itself isn't yet
    # populated — the BootstrapResult records the location.
    assert result.claude_dir == new_ws / ".claude"

    # AC.D.4.1: .gitignore declares framework/ as the only tracked subtree.
    gitignore = new_ws / ".gitignore"
    assert gitignore.exists(), (
        "AC.D.4.1: <new-ws>/.gitignore must be scaffolded; "
        "missing (D.2 work carry-forward)"
    )
    gi_text = gitignore.read_text()
    assert "!framework" in gi_text
    assert "!.claude" in gi_text

    # AC.D.4.1: persona scaffolded.
    persona_contract = (
        workspace_state / "personas" / "primary" / "contract.yaml"
    )
    assert persona_contract.exists(), (
        f"AC.D.4.1: persona scaffold missing at {persona_contract}"
    )

    # FBE.7 (v0.1.0 foldback): .mcp.json is no longer scaffolded at
    # v0.1.0 (memory-graphiti retired from _SERVICE_KINDS per Luke's
    # 2026-05-03 ruling). The path is reserved for M-GMP's post-v0.1.0
    # re-admission. See
    # docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.md.
    mcp_json = workspace_state / ".mcp.json"
    assert not mcp_json.exists(), (
        "FBE.7: .mcp.json should NOT be scaffolded at v0.1.0; "
        f"unexpected file at {mcp_json}"
    )


# ---- AC.D.4.1 — refusal-on-non-empty target -------------------------


def test_AC_D_4_1_target_non_empty_refuses(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """Pre-existing non-empty target halts BEFORE any side effect.

    Asserts: (a) raises TargetNotEmptyError, (b) framework/ NOT
    created, (c) the pre-existing file remains untouched.
    """
    canonical = make_fixture_canonical(tmp_path / "fixture-canonical")
    new_ws = tmp_path / "new-ws"
    new_ws.mkdir()
    pre_existing = new_ws / "some-file.txt"
    pre_existing.write_text("operator content; do not clobber")

    with pytest.raises(TargetNotEmptyError):
        bootstrap_new_workspace(
            new_ws_path=new_ws,
            canonical_source=str(canonical),
            tracker_seed_runner=_stub_tracker_seed_runner,
        )

    # No partial-bootstrap residue: framework/ NOT created.
    assert not (new_ws / "framework").exists(), (
        "AC.D.4.1: refusal must not produce partial-bootstrap state; "
        f"<new-ws>/framework/ exists at {new_ws / 'framework'}"
    )

    # Pre-existing file preserved.
    assert pre_existing.read_text() == "operator content; do not clobber"


# ---- AC.D.4.1 — URL form routes through cache clone -----------------


def test_AC_D_4_1_url_form_routes_through_cache_clone(
    tmp_path: Path,
    make_fixture_canonical,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """URL-form canonical_source clones via cache; canonical_source
    recorded in sync-config.yaml as the original URL.
    """
    # Construct a fixture canonical exposed via file:// URL.
    canonical = make_fixture_canonical(tmp_path / "fixture-canonical")
    canonical_url = f"https://test-host/lukeivers/loam-fixture"

    # Redirect the cache to tmp_path/home/.pos/canonical-cache/ so we
    # don't pollute the operator's actual home dir.
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    # Patch ensure_cache_clone to just clone canonical to a deterministic
    # cache path in fake_home (avoiding real network I/O for the URL).
    from loam.workspace_sync import canonical_cache as cc_mod

    real_ensure = cc_mod.ensure_cache_clone

    def _stub_ensure_cache_clone(url: str, ref: str = "HEAD") -> Path:
        # Mimic the production cache layout in our fake home.
        cache_path = fake_home / ".loam" / "canonical-cache" / cc_mod.derive_repo_id(url)
        if not cache_path.exists():
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(  # noqa: S603 — argv constructed
                ["git", "clone", str(canonical), str(cache_path)],
                check=True,
                capture_output=True,
                text=True,
            )
        return cache_path

    monkeypatch.setattr(cc_mod, "ensure_cache_clone", _stub_ensure_cache_clone)

    new_ws = tmp_path / "new-ws"
    agents = tmp_path / "LaunchAgents"
    result = bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=canonical_url,
        service_manager_dir_override=agents,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    # AC.D.4.1: framework/ cloned + byte-matches canonical.
    # Post single-framework restructure (amendment #67) the cloned
    # branch is `framework-only`; canonical's `framework/README.md`
    # lands at `<new-ws>/framework/README.md` (framework/ promoted to
    # root on the synthetic branch).
    assert (new_ws / "framework" / ".git").exists()
    canonical_readme = _read_canonical_blob(canonical, "framework/README.md")
    assert (new_ws / "framework" / "README.md").read_text() == (
        canonical_readme
    )

    # AC.D.4.1: sync-config.yaml records the ORIGINAL URL (not the cache path).
    sync_config = result.sync_config_path
    assert sync_config.exists()
    payload = sync_config.read_text()
    assert f"canonical_source: {canonical_url}" in payload
    # Cache path must NOT leak into sync-config.yaml.
    assert str(fake_home) not in payload

    assert result.canonical_source == canonical_url
    assert result.canonical_source_kind == "url"


# ---- AC.D.4.2 — init-existing is idempotent -------------------------


def test_AC_D_4_2_init_existing_is_idempotent(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """Running with --init-existing on an already-bootstrapped
    workspace produces no further mtime/content changes.
    """
    canonical = make_fixture_canonical(tmp_path / "fixture-canonical")
    new_ws = tmp_path / "new-ws"
    agents = tmp_path / "LaunchAgents"

    # First bootstrap: clone + scaffold.
    bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(canonical),
        service_manager_dir_override=agents,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    # Capture mtimes of every workspace-state file.
    workspace_state = new_ws / WORKSPACE_STATE_SUBDIR
    pre_mtimes: dict[Path, float] = {}
    for path in workspace_state.rglob("*"):
        if path.is_file():
            pre_mtimes[path] = path.stat().st_mtime_ns

    # Re-invoke with --init-existing.
    result = bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(canonical),
        init_existing=True,
        service_manager_dir_override=agents,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    # AC.D.4.2: no file content changed (mtime equality is the strongest
    # idempotency signal because the scaffold's contract is "skip if
    # present").
    post_mtimes = {
        p: p.stat().st_mtime_ns
        for p in workspace_state.rglob("*")
        if p.is_file()
    }

    # The set of files must be identical.
    assert set(pre_mtimes.keys()) == set(post_mtimes.keys()), (
        f"AC.D.4.2: file set changed between runs; "
        f"added={set(post_mtimes) - set(pre_mtimes)!r}, "
        f"removed={set(pre_mtimes) - set(post_mtimes)!r}"
    )

    # And every file's mtime + content must be unchanged. We allow the
    # sync-config.yaml file to be re-written if its content is byte-
    # identical (the writer compares-then-writes; idempotent re-writes
    # are skipped).
    for path, pre_mt in pre_mtimes.items():
        post_mt = post_mtimes[path]
        assert post_mt == pre_mt, (
            f"AC.D.4.2: mtime changed for {path}: "
            f"pre={pre_mt}, post={post_mt} — idempotency violated."
        )

    assert result.init_existing is True


# ---- AC.D.4.1 — HC#6 structural promise carries forward -------------


def test_AC_D_4_1_HC6_workspace_state_inside_workspace_subdir(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """Every workspace-state path lives under <new-ws>/workspace/.

    HC#6 carries forward from D.2: a freshly bootstrapped workspace
    must satisfy the structural promise that workspace-state cannot
    accidentally write into framework/ or workspace root (apart from
    .claude/ per D-Q.A4 lock).
    """
    canonical = make_fixture_canonical(tmp_path / "fixture-canonical")
    new_ws = tmp_path / "new-ws"
    agents = tmp_path / "LaunchAgents"

    bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(canonical),
        service_manager_dir_override=agents,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    # Every name in {.pos, personas, .mcp.json, objective_tracker.sqlite}
    # must NOT appear at <new-ws>/<name> (workspace root). Must appear
    # inside <new-ws>/workspace/<name>.
    workspace_state_names = {
        ".pos",
        "personas",
        ".mcp.json",
        "objective_tracker.sqlite",
    }
    for name in workspace_state_names:
        # Workspace root must NOT carry these names (apart from .claude/).
        assert not (new_ws / name).exists(), (
            f"HC#6: workspace-state name {name!r} must NOT live at "
            f"workspace root <new-ws>/{name}; got "
            f"{new_ws / name}"
        )

    # The scaffold creates these inside workspace/ (.pos + personas
    # are guaranteed; .mcp.json was guaranteed pre-FBE.7 but post-FBE.7
    # is NOT written at v0.1.0 since memory-graphiti is retired from
    # _SERVICE_KINDS; objective_tracker.sqlite depends on tracker_seed
    # which we stubbed out).
    assert (new_ws / "workspace" / ".pos").is_dir()
    assert (new_ws / "workspace" / "personas").is_dir()
    # FBE.7: .mcp.json is intentionally NOT scaffolded at v0.1.0; M-GMP
    # restores the writer's invocation post-v0.1.0. See
    # docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.md.
    assert not (new_ws / "workspace" / ".mcp.json").exists()

    # framework/ must not contain workspace-state files.
    framework = new_ws / "framework"
    for name in workspace_state_names:
        assert not (framework / name).exists(), (
            f"HC#6: workspace-state name {name!r} must NOT live "
            f"under framework/; got {framework / name}"
        )


# ---- AC.D.4.3 — help text discoverability ---------------------------


def test_AC_D_4_3_help_text_describes_from_flag_and_target() -> None:
    """`pos-new-workspace --help` describes --from + positional + shape."""
    parser = build_parser()
    help_text = parser.format_help()

    # The --from flag is named.
    assert "--from" in help_text

    # The new-ws-path positional is named.
    assert "new_ws_path" in help_text or "new-ws-path" in help_text.lower()

    # The directory-shape description references framework/, workspace/,
    # and .claude/ (per the parser description).
    assert "framework/" in help_text
    assert "workspace/" in help_text
    assert ".claude/" in help_text

    # The --init-existing flag is documented.
    assert "--init-existing" in help_text


def test_AC_D_4_3_workspace_bootstrap_readme_exists() -> None:
    """`framework/workspace-bootstrap/README.md` exists and references
    both console scripts.

    Plan §4 D.4 AC.D.4.3 binding: the verb is discoverable without
    reading source.
    """
    # Locate the workspace-bootstrap component dir from this test file.
    component_root = Path(__file__).resolve().parent.parent
    readme = component_root / "README.md"
    assert readme.exists(), (
        f"AC.D.4.3: framework/workspace-bootstrap/README.md must exist "
        f"as the discoverability surface; missing at {readme}"
    )
    text = readme.read_text()
    assert "pos-new-workspace" in text, (
        "AC.D.4.3: README must reference pos-new-workspace"
    )
    assert "pos-bootstrap" in text, (
        "AC.D.4.3: README must reference pos-bootstrap (the existing verb)"
    )


# ---- canonical-source validation ------------------------------------


def test_canonical_source_relative_path_rejected(tmp_path: Path) -> None:
    """Relative paths produce a structured CanonicalSourceInvalidError."""
    new_ws = tmp_path / "new-ws"
    with pytest.raises(CanonicalSourceInvalidError):
        bootstrap_new_workspace(
            new_ws_path=new_ws,
            canonical_source="./not-absolute",
            tracker_seed_runner=_stub_tracker_seed_runner,
        )


def test_canonical_source_local_path_must_be_git_tree(
    tmp_path: Path,
) -> None:
    """An absolute path that is not a git working tree is rejected."""
    new_ws = tmp_path / "new-ws"
    not_a_git_tree = tmp_path / "not-git"
    not_a_git_tree.mkdir()
    (not_a_git_tree / "README.md").write_text("# not a repo")

    with pytest.raises(CanonicalSourceInvalidError) as excinfo:
        bootstrap_new_workspace(
            new_ws_path=new_ws,
            canonical_source=str(not_a_git_tree),
            tracker_seed_runner=_stub_tracker_seed_runner,
        )
    assert "not a git working tree" in str(excinfo.value)


# ---- cli_main exit codes --------------------------------------------


def test_cli_main_target_not_empty_returns_exit_1(
    tmp_path: Path,
    make_fixture_canonical,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`cli_main` maps TargetNotEmptyError → exit code 1."""
    canonical = make_fixture_canonical(tmp_path / "fixture-canonical")
    new_ws = tmp_path / "new-ws"
    new_ws.mkdir()
    (new_ws / "preexisting").write_text("x")

    rc = cli_main([str(new_ws), "--from", str(canonical)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "not empty" in captured.err.lower()


def test_cli_main_invalid_canonical_returns_exit_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`cli_main` maps CanonicalSourceInvalidError → exit code 2."""
    new_ws = tmp_path / "new-ws"
    rc = cli_main([str(new_ws), "--from", "./relative-path"])
    assert rc == 2
    captured = capsys.readouterr()
    # The structured message names the accepted forms.
    assert "absolute POSIX path" in captured.err or "URL" in captured.err
