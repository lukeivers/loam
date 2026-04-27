"""AC.WS.1, AC.WS.7, AC.WS.10 — CLI flow tests."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from workspace_sync.cli import (
    WorkspaceRootError,
    _ref_already_applied,
    _seed_default_envelope,
    derive_workspace_root,
    main,
)
from workspace_sync.merge_resolver import MergeVerdict, MergeResolver, ResolverBudget


def _git_head_sha(canonical: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(canonical), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def test_derive_workspace_root_from_pos_marker(tmp_path: Path) -> None:
    (tmp_path / ".pos").mkdir()
    (tmp_path / ".pos" / "sync-protected.yaml").write_text("framework_floor: []")
    assert derive_workspace_root(workspace_arg=None, cwd=tmp_path) == tmp_path


def test_derive_workspace_root_from_git_marker(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    assert derive_workspace_root(workspace_arg=None, cwd=tmp_path) == tmp_path


def test_derive_workspace_root_explicit_arg(tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    assert derive_workspace_root(workspace_arg=target, cwd=tmp_path) == target


def test_derive_workspace_root_halt_on_neither(tmp_path: Path) -> None:
    """AC.WS.1: structural argument-validation halt when no marker present."""
    with pytest.raises(WorkspaceRootError, match="not derivable"):
        derive_workspace_root(workspace_arg=None, cwd=tmp_path)


def test_derive_workspace_root_invalid_arg(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceRootError, match="not an existing directory"):
        derive_workspace_root(workspace_arg=tmp_path / "nope", cwd=tmp_path)


def test_seed_default_envelope_first_run(tmp_path: Path) -> None:
    """AC.WS.10: first-run writes the default envelope."""
    sp = _seed_default_envelope(tmp_path)
    target = tmp_path / ".pos" / "sync-protected.yaml"
    assert target.exists()
    # Class-A floor entries are present.
    assert any(r.pattern == ".mcp.json" for r in sp.framework_floor)


def test_ref_already_applied_no_state_returns_false(tmp_path: Path) -> None:
    assert _ref_already_applied(tmp_path, "abc123") is False


def test_main_halts_on_missing_canonical(tmp_path: Path, capsys, monkeypatch) -> None:
    """AC.WS.1: missing canonical produces structured error exit."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / ".git").mkdir()  # marker
    rc = main(
        [
            "--canonical",
            str(tmp_path / "nope"),
            "--workspace",
            str(workspace),
        ]
    )
    assert rc == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_main_dry_run_against_clean_canonical(
    make_canonical_repo, make_workspace, monkeypatch, capsys
) -> None:
    """AC.WS.1 + AC.WS.7: dry-run + identical content = no apply, no error."""
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)

    # Pre-stub the resolver factory so import doesn't try to load
    # a real claude binary.
    import workspace_sync.cli as cli_mod
    real_load = cli_mod._load_merge_resolver

    def fake_factory(module_spec: str, *, budget=None) -> MergeResolver:
        class NeverInvoked:
            def invoke(self, prompt, response_model):
                raise AssertionError("resolver should not be called for clean tree")
        return MergeResolver(NeverInvoked(), budget or ResolverBudget())

    monkeypatch.setattr(cli_mod, "_load_merge_resolver", fake_factory)

    rc = main(
        [
            "--canonical",
            str(canonical),
            "--workspace",
            str(workspace),
            "--dry-run",
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    # sync_ref printed in summary.
    assert "sync_ref" in captured.out


# ---- β.1 (AC.β.1) — config-file-driven canonical_source ------------


def _patch_home(monkeypatch, home: Path) -> None:
    """Redirect ``Path.home()`` to an isolated tmp dir (no real ~/.pos/)."""
    monkeypatch.setenv("HOME", str(home))


def _stub_resolver_factory(monkeypatch) -> None:
    """Stub the resolver factory the same way other tests do."""
    import workspace_sync.cli as cli_mod

    def fake_factory(module_spec: str, *, budget=None) -> MergeResolver:
        class NeverInvoked:
            def invoke(self, prompt, response_model):
                raise AssertionError("resolver should not be called for clean tree")
        return MergeResolver(NeverInvoked(), budget or ResolverBudget())

    monkeypatch.setattr(cli_mod, "_load_merge_resolver", fake_factory)


def test_main_no_canonical_no_config_halts(
    make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 fixture-3: no --canonical + no config file → halt with structured error.

    The error message names ALL THREE fall-through paths.
    """
    workspace = make_workspace(seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    with pytest.raises(SystemExit) as exc:
        main(["--workspace", str(workspace)])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    err = captured.err
    assert "no canonical source" in err
    assert "--canonical" in err
    assert "<workspace>/.pos/sync-config.yaml" in err
    assert "~/.pos/sync-config.yaml" in err


def test_main_canonical_via_workspace_config(
    make_canonical_repo, make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 fixture-1: workspace-local sync-config.yaml supplies canonical_source.

    Operator runs `pos-sync` with no flags; the CLI loads the workspace-local
    sync-config.yaml's canonical_source: <local-path> and proceeds.
    """
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    _stub_resolver_factory(monkeypatch)

    # Write workspace-local sync-config.yaml with canonical_source.
    sync_cfg_path = workspace / ".pos" / "sync-config.yaml"
    sync_cfg_path.parent.mkdir(parents=True, exist_ok=True)
    sync_cfg_path.write_text(f"canonical_source: {canonical}\n")

    rc = main(["--workspace", str(workspace), "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "sync_ref" in captured.out


def test_main_canonical_via_user_config(
    make_canonical_repo, make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1: ~/-rooted sync-config.yaml supplies canonical_source.

    No workspace-local file; ~/-rooted file's canonical_source is used.
    """
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    _stub_resolver_factory(monkeypatch)

    user_cfg_path = home / ".pos" / "sync-config.yaml"
    user_cfg_path.parent.mkdir(parents=True, exist_ok=True)
    user_cfg_path.write_text(f"canonical_source: {canonical}\n")

    rc = main(["--workspace", str(workspace), "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "sync_ref" in captured.out


def test_main_cli_flag_overrides_config(
    make_canonical_repo, make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 fixture-5: --canonical overrides workspace-local config_source.

    Workspace-local config points to /nonexistent; --canonical points to
    real canonical; the flag wins.
    """
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    _stub_resolver_factory(monkeypatch)

    sync_cfg_path = workspace / ".pos" / "sync-config.yaml"
    sync_cfg_path.parent.mkdir(parents=True, exist_ok=True)
    sync_cfg_path.write_text("canonical_source: /nonexistent/path\n")

    rc = main(
        [
            "--canonical",
            str(canonical),
            "--workspace",
            str(workspace),
            "--dry-run",
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "sync_ref" in captured.out


def test_main_back_compat_canonical_flag_no_config(
    make_canonical_repo, make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 fixture-4 / HC#1: workspace WITHOUT sync-config.yaml + --canonical
    flag = byte-identical to today's pos-sync flow.

    The original test_main_dry_run_against_clean_canonical above already
    covers this shape (no config file present, --canonical passed). This
    test additionally verifies the flow under an explicitly-isolated $HOME
    so any leftover ~/.pos/sync-config.yaml on the operator's real disk
    doesn't leak in.
    """
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    _stub_resolver_factory(monkeypatch)

    rc = main(
        [
            "--canonical",
            str(canonical),
            "--workspace",
            str(workspace),
            "--dry-run",
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "sync_ref" in captured.out


def test_main_canonical_url_form_invokes_cache(
    make_canonical_repo, make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 fixture-2: URL form triggers ensure_cache_clone.

    Mocks ensure_cache_clone to return the local canonical repo path so
    the rest of the flow proceeds normally.
    """
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    _stub_resolver_factory(monkeypatch)

    import workspace_sync.cli as cli_mod

    captured_calls: list[tuple[str, str]] = []

    def fake_ensure_cache_clone(url: str, ref: str = "HEAD"):
        captured_calls.append((url, ref))
        return canonical  # the test-real local repo stands in for the cache

    monkeypatch.setattr(cli_mod, "ensure_cache_clone", fake_ensure_cache_clone)

    rc = main(
        [
            "--canonical",
            "https://github.com/test/canonical",
            "--workspace",
            str(workspace),
            "--dry-run",
        ]
    )
    assert rc == 0
    assert captured_calls == [("https://github.com/test/canonical", "HEAD")]


def test_main_canonical_relative_path_halts(
    make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 / D-β.1 LOCKED: relative path halts at discrimination."""
    workspace = make_workspace(seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    rc = main(
        [
            "--canonical",
            "relative/path",
            "--workspace",
            str(workspace),
        ]
    )
    assert rc == 2
    captured = capsys.readouterr()
    assert "must be one of" in captured.err


# ---- α-hotfix #59 regression — NN-resolved entries actually overwrite -----


def test_alpha_hotfix_NN_resolved_paths_actually_overwrite_workspace_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """AC.α-hotfix.1 binding regression: an NN ancestor-detection
    accept-canonical entry must result in the workspace file's bytes
    matching canonical's HEAD blob byte-for-byte after pos-sync
    --auto-accept.

    Pre-α-hotfix: the NN cache-miss / cache-hit branches in
    merge_helper.py set the verdict but skipped write_merged. The
    apply step walked the staging tree, found no file for the
    NN-resolved path, silently no-op'd, and state.yaml advanced to
    "applied" while the workspace file stayed at pre-apply state.

    Post-α-hotfix: both NN branches read canonical's HEAD content
    via _read_canonical_blob_at_ref + call write_merged before
    sealing the verdict. apply_staging_atomically picks the file
    up via the existing staging tree machinery.

    Test shape (HC#4 binding):
      - Build a real two-commit canonical (ancestor + HEAD).
      - Seed a workspace with the ancestor's content for one path.
      - Run cli.main with --auto-accept.
      - Read the workspace file's bytes post-apply.
      - Assert byte-for-byte equality with canonical HEAD's blob
        (NOT just the verdict shape; NOT just state.yaml).
    """
    # ---- 1. Build a two-commit canonical -------------------------
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    subprocess.run(
        ["git", "-C", str(canonical), "init", "-q"], check=True
    )
    subprocess.run(
        ["git", "-C", str(canonical), "config", "user.email", "t@t"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(canonical), "config", "user.name", "t"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(canonical), "config", "commit.gpgsign", "false"],
        check=True,
    )

    # Commit 1 (ancestor): payload at v1-content. Commit a second
    # path so the bare-repo ls-tree still has content at HEAD.
    payload_path = "framework/payload.py"
    other_path = "framework/other.py"
    (canonical / "framework").mkdir()
    (canonical / payload_path).write_text("v1-content\n")
    (canonical / other_path).write_text("other-stable\n")
    subprocess.run(
        ["git", "-C", str(canonical), "add", "-A"], check=True
    )
    subprocess.run(
        ["git", "-C", str(canonical), "commit", "-q", "-m", "v1"],
        check=True,
    )

    # Commit 2 (HEAD): edit payload to v2-canonical-head.
    (canonical / payload_path).write_text("v2-canonical-head\n")
    subprocess.run(
        ["git", "-C", str(canonical), "add", "-A"], check=True
    )
    subprocess.run(
        ["git", "-C", str(canonical), "commit", "-q", "-m", "v2"],
        check=True,
    )

    canonical_head_blob = subprocess.check_output(
        ["git", "-C", str(canonical), "show", f"HEAD:{payload_path}"],
    )
    # Pre-condition: ancestor != HEAD (the bug only fires on actual
    # divergence between workspace and canonical HEAD).
    ancestor_blob = subprocess.check_output(
        ["git", "-C", str(canonical), "show", f"HEAD~1:{payload_path}"],
    )
    assert ancestor_blob != canonical_head_blob, (
        "test setup: ancestor and HEAD must differ"
    )

    # ---- 2. Build a workspace at the ancestor's content ----------
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "framework").mkdir()
    (workspace / payload_path).write_bytes(ancestor_blob)
    (workspace / other_path).write_bytes(
        subprocess.check_output(
            ["git", "-C", str(canonical), "show", f"HEAD:{other_path}"]
        )
    )
    # Seed default sync-protected envelope; framework/* is Class-C
    # (no rule matches → default Class C → resolver-handled).
    from workspace_sync.sync_protected import write_default_if_absent
    write_default_if_absent(workspace)

    # Pre-condition: the workspace file does NOT yet match canonical
    # HEAD (it matches the ancestor instead).
    assert (workspace / payload_path).read_bytes() != canonical_head_blob
    assert (workspace / payload_path).read_bytes() == ancestor_blob

    # ---- 3. Stub the resolver factory --------------------------
    # The α.1 NN ancestor-detection fast-path runs BEFORE the LLM
    # resolver and resolves to INFERRED_ACCEPT_CANONICAL with no
    # LLM call. The resolver should never be invoked for our
    # NN-matched entry. We supply a stub that errors if invoked
    # to make the test fail loudly if α.1 ever stops engaging.
    import workspace_sync.cli as cli_mod

    def fake_factory(module_spec: str, *, budget=None) -> MergeResolver:
        class NeverInvoked:
            def invoke(self, prompt, response_model):
                raise AssertionError(
                    "α.1 NN ancestor-detection should resolve our "
                    "entry without an LLM call"
                )

        return MergeResolver(NeverInvoked(), budget or ResolverBudget())

    monkeypatch.setattr(cli_mod, "_load_merge_resolver", fake_factory)

    # ---- 4. Run pos-sync with --auto-accept --------------------
    rc = main(
        [
            "--canonical",
            str(canonical),
            "--workspace",
            str(workspace),
            "--auto-accept",
            "--confidence-floor",
            "0.85",
        ]
    )
    assert rc == 0, (
        f"pos-sync exited non-zero (rc={rc}); "
        f"stdout/stderr=\n{capsys.readouterr()}"
    )

    # ---- 5. The binding HC#4 assertion -------------------------
    # Read the workspace file's bytes post-apply. Compare to
    # canonical HEAD's blob byte-for-byte. This is the assertion
    # that catches the α-hotfix bug class — verdict-shape only
    # tests would let the bug ship.
    workspace_payload_bytes = (workspace / payload_path).read_bytes()
    assert workspace_payload_bytes == canonical_head_blob, (
        f"AC.α-hotfix.1 violated: workspace file at "
        f"{workspace / payload_path} does not match canonical HEAD blob "
        f"byte-for-byte after --auto-accept apply.\n"
        f"  workspace bytes: {workspace_payload_bytes!r}\n"
        f"  canonical HEAD:  {canonical_head_blob!r}\n"
        f"  ancestor blob:   {ancestor_blob!r}\n"
        f"This is the original Bundle α (#57) bug shape: the NN "
        f"ancestor-detection fast-path set the verdict but did not "
        f"stage canonical's content."
    )

    # Also confirm the audit reports the entry as
    # INFERRED_ACCEPT_CANONICAL (verdict-shape correctness; the
    # supplementary check that our test exercised the NN path,
    # not some other resolution).
    import yaml as _yaml
    audit_dir = workspace / ".pos" / "sync"
    head_sha = _git_head_sha(canonical)
    audit_yaml = audit_dir / head_sha / "audit.yaml"
    assert audit_yaml.exists(), (
        f"audit.yaml not found at {audit_yaml}; sync did not persist "
        f"audit. dir contents: "
        f"{list(audit_dir.glob('*')) if audit_dir.exists() else '(missing)'}"
    )
    audit_data = _yaml.safe_load(audit_yaml.read_text())
    payload_entries = [
        c for c in audit_data["conflicts"]
        if c["path"] == payload_path
    ]
    assert len(payload_entries) == 1, (
        f"expected exactly one audit entry for {payload_path}; "
        f"got {len(payload_entries)}"
    )
    entry = payload_entries[0]
    assert entry["resolution"] == "inferred-accept-canonical", (
        f"expected resolution=inferred-accept-canonical (the α.1 NN "
        f"fast-path verdict); got {entry['resolution']}"
    )
    assert entry["resolved_content_path"] is not None, (
        "AC.α-hotfix.1 invariant: NN-resolved entries must carry "
        "resolved_content_path post-fix; the original bug left it "
        f"null. entry: {entry!r}"
    )


# ---- α-hotfix-2 #60 regressions — Bug A, Bug B, Bug D ---------------------
#
# All three are file-content-byte-match (or state-status) assertions that
# catch the verdict-set-without-content-staged fault-class on the three
# accept-canonical-flavored code paths α-hotfix #59 did not close
# (HC#1 named-scope binding) plus the state.yaml hygiene bug primary
# persona caught during post-#59 verification.
# ----------------------------------------------------------------------


def _build_canonical(canonical: Path) -> None:
    """Helper: initialize a git repo with `git init -q` + identity config.
    Tests below use it to build synthetic canonicals."""
    subprocess.run(["git", "-C", str(canonical), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(canonical), "config", "user.email", "t@t"], check=True
    )
    subprocess.run(
        ["git", "-C", str(canonical), "config", "user.name", "t"], check=True
    )
    subprocess.run(
        ["git", "-C", str(canonical), "config", "commit.gpgsign", "false"],
        check=True,
    )


def test_alpha_hotfix_2_LLM_accept_canonical_overwrites_workspace_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """AC.α-hotfix-2.1 / Bug A: when the LLM resolver returns
    inferred-accept-canonical (NOT via the α.1 NN fast-path), the
    workspace file's bytes must match canonical's HEAD blob byte-for-
    byte after pos-sync --auto-accept.

    Pre-α-hotfix-2: cli.py:271-274 read `pass` for INFERRED_ACCEPT_CANONICAL
    (the comment "do nothing extra" was wrong; clean_writes contains
    only conflict-detector-clean writes, not paths the resolver later
    resolved as accept-canonical). apply_staging_atomically silently
    no-op'd → false-success.

    Post-α-hotfix-2: cli.py post-resolve loop calls the centralized
    stage_canonical_at_ref primitive on these entries, dropping
    canonical's HEAD content into staging. apply picks it up.

    Test shape (HC#3 binding):
      - Build a single-commit canonical (no ancestor history → α.1 NN
        cannot match → falls through to LLM resolver).
      - Seed a workspace with different content for the same path.
      - Stub the resolver factory to return MergeVerdict
        (resolution="inferred-accept-canonical", confidence=0.9).
      - Run cli.main with --auto-accept.
      - Assert workspace file bytes equal canonical HEAD blob.
    """
    from workspace_sync.merge_primitives import (
        MergeClassification,
        MergeVerification,
    )

    # ---- 1. Single-commit canonical -----------------------------
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    _build_canonical(canonical)

    payload_path = "framework/payload.py"
    (canonical / "framework").mkdir()
    (canonical / payload_path).write_text("v1-canonical-head\n")
    subprocess.run(["git", "-C", str(canonical), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(canonical), "commit", "-q", "-m", "v1"], check=True
    )

    canonical_head_blob = subprocess.check_output(
        ["git", "-C", str(canonical), "show", f"HEAD:{payload_path}"]
    )

    # ---- 2. Workspace at unrelated content (NN won't match) ------
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "framework").mkdir()
    # Random unrelated content — NOT in any canonical-history ancestor.
    (workspace / payload_path).write_bytes(b"unrelated-workspace-content\n")

    from workspace_sync.sync_protected import write_default_if_absent
    write_default_if_absent(workspace)

    assert (workspace / payload_path).read_bytes() != canonical_head_blob

    # ---- 3. Stub the resolver factory --------------------------
    # Return INFERRED_ACCEPT_CANONICAL for the generator-path call.
    # α.2 classifier returns "unknown" by default → fallthrough to
    # the generator path which returns our verdict.
    import workspace_sync.cli as cli_mod

    class TypedStubLLM:
        def invoke(self, prompt, response_model):
            if response_model is MergeClassification:
                return MergeClassification(
                    merge_class="unknown",
                    confidence=0.0,
                    reasoning="test stub",
                ), 50
            if response_model is MergeVerification:
                return MergeVerification(
                    passed=False,
                    class_mismatch=False,
                    concerns="stub",
                    confidence=0.0,
                ), 100
            # MergeVerdict (legacy generator path).
            return MergeVerdict(
                resolution="inferred-accept-canonical",
                merged_content=None,
                rationale="LLM said accept canonical",
                confidence=0.95,
            ), 200

    def fake_factory(module_spec: str, *, budget=None) -> MergeResolver:
        return MergeResolver(TypedStubLLM(), budget or ResolverBudget())

    monkeypatch.setattr(cli_mod, "_load_merge_resolver", fake_factory)

    # ---- 4. Run pos-sync with --auto-accept --------------------
    rc = main(
        [
            "--canonical",
            str(canonical),
            "--workspace",
            str(workspace),
            "--auto-accept",
            "--confidence-floor",
            "0.85",
        ]
    )
    assert rc == 0, (
        f"pos-sync exited non-zero (rc={rc}); "
        f"stdout/stderr=\n{capsys.readouterr()}"
    )

    # ---- 5. Binding HC#3 assertion -----------------------------
    workspace_payload_bytes = (workspace / payload_path).read_bytes()
    assert workspace_payload_bytes == canonical_head_blob, (
        f"AC.α-hotfix-2.1 violated: workspace file at "
        f"{workspace / payload_path} does not match canonical HEAD blob "
        f"byte-for-byte after --auto-accept apply.\n"
        f"  workspace bytes: {workspace_payload_bytes!r}\n"
        f"  canonical HEAD:  {canonical_head_blob!r}\n"
        f"This is Bug A: the LLM-resolver INFERRED_ACCEPT_CANONICAL "
        f"verdict-without-stage shape."
    )


def test_alpha_hotfix_2_class_B_accept_upstream_overwrites_workspace_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """AC.α-hotfix-2.2 / Bug B: when the merge_helper's Class-B branch
    resolves to ACCEPT_UPSTREAM, the workspace file's bytes must match
    canonical's HEAD blob byte-for-byte after pos-sync --auto-accept.

    Pre-α-hotfix-2: cli.py:275-278 did clean_writes.append AFTER
    stage_canonical_clean_writes had already run; the append was a
    no-op. Class-B operator-prefers-canonical entries got the verdict
    set but never staged canonical's content → false-success.

    Post-α-hotfix-2: cli.py post-resolve loop calls
    stage_canonical_at_ref directly for ACCEPT_UPSTREAM entries.

    Test shape (HC#3 binding):
      - Build a canonical with a Class-B path
        (the default sync-protected.yaml's Class-B set; or a
        synthetic Class-B rule via patched sync-protected).
      - Patch detect_b_shape_conflicts to surface a Class-B PENDING
        entry with change_kind=LOCAL_MODIFIED_EQUALS_UPSTREAM
        (the natural conflict_detection flow filters convergent
        change kinds; we bypass via stub to exercise the cli.py
        post-resolve path).
      - Run cli.main with --auto-accept.
      - Assert workspace file bytes equal canonical HEAD blob.

    Note: because Class-B ACCEPT_UPSTREAM is structurally hard to
    reach from the natural conflict_detection flow (the change_kind
    classifier filters convergent identical content), we use
    monkeypatch on detect_b_shape_conflicts. The test exercises
    cli.py's post-resolve loop and the centralized
    stage_canonical_at_ref primitive — the binding bug-fix surface.
    """
    from workspace_sync.conflict_report import (
        ConflictChangeKind,
        ConflictEntry,
        ConflictReport,
        ConflictSummary,
        Resolution,
    )

    # ---- 1. Canonical with one path -----------------------------
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    _build_canonical(canonical)

    payload_path = "framework/class_b_path.py"
    (canonical / "framework").mkdir()
    (canonical / payload_path).write_text("canonical-class-b-content\n")
    subprocess.run(["git", "-C", str(canonical), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(canonical), "commit", "-q", "-m", "v1"], check=True
    )

    canonical_head_blob = subprocess.check_output(
        ["git", "-C", str(canonical), "show", f"HEAD:{payload_path}"]
    )

    # ---- 2. Workspace with different content --------------------
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "framework").mkdir()
    (workspace / payload_path).write_bytes(b"workspace-class-b-stale\n")

    from workspace_sync.sync_protected import write_default_if_absent
    write_default_if_absent(workspace)

    assert (workspace / payload_path).read_bytes() != canonical_head_blob

    # ---- 3. Patch detect_b_shape_conflicts --------------------
    # Return a ConflictReport with the Class-B path as PENDING with
    # change_kind=LOCAL_MODIFIED_EQUALS_UPSTREAM (so merge_helper's
    # Class-B branch resolves to ACCEPT_UPSTREAM).
    import workspace_sync.cli as cli_mod
    import hashlib as _hashlib

    canonical_bytes = (canonical / payload_path).read_bytes()
    workspace_bytes = (workspace / payload_path).read_bytes()
    canonical_sha = _hashlib.sha256(canonical_bytes).hexdigest()
    workspace_sha = _hashlib.sha256(workspace_bytes).hexdigest()

    def fake_detect(*, canonical_path, ref, workspace_root, sync_protected, prior_state=None):
        report = ConflictReport(
            sync_ref=ref,
            detected_at="2026-04-26T00:00:00Z",
            conflicts=[
                ConflictEntry(
                    path=payload_path,
                    prior_release_sha256=None,
                    installed_sha256=workspace_sha,
                    new_release_sha256=canonical_sha,
                    # The change_kind that routes Class-B → ACCEPT_UPSTREAM
                    # in the merge_helper's branch (line 462-468 today).
                    change_kind=ConflictChangeKind.LOCAL_MODIFIED_EQUALS_UPSTREAM,
                    resolution=Resolution.PENDING,
                ),
            ],
            summary=ConflictSummary(),
        )
        return report, []

    monkeypatch.setattr(cli_mod, "detect_b_shape_conflicts", fake_detect)

    # Patch sync_protected.classify to mark our path as Class-B.
    from workspace_sync.sync_protected import FileClass, SyncProtected
    orig_classify = SyncProtected.classify

    def patched_classify(self, path: str) -> FileClass:
        if path == payload_path:
            return FileClass.B
        return orig_classify(self, path)

    monkeypatch.setattr(SyncProtected, "classify", patched_classify)

    # Stub the resolver factory — Class-B doesn't invoke the resolver.
    def fake_factory(module_spec: str, *, budget=None) -> MergeResolver:
        class NeverInvoked:
            def invoke(self, prompt, response_model):
                raise AssertionError(
                    "Class-B branch should resolve without an LLM call"
                )

        return MergeResolver(NeverInvoked(), budget or ResolverBudget())

    monkeypatch.setattr(cli_mod, "_load_merge_resolver", fake_factory)

    # ---- 4. Run pos-sync with --auto-accept --------------------
    rc = main(
        [
            "--canonical",
            str(canonical),
            "--workspace",
            str(workspace),
            "--auto-accept",
            "--confidence-floor",
            "0.85",
        ]
    )
    assert rc == 0, (
        f"pos-sync exited non-zero (rc={rc}); "
        f"stdout/stderr=\n{capsys.readouterr()}"
    )

    # ---- 5. Binding HC#3 assertion -----------------------------
    workspace_payload_bytes = (workspace / payload_path).read_bytes()
    assert workspace_payload_bytes == canonical_head_blob, (
        f"AC.α-hotfix-2.2 violated: Class-B workspace file at "
        f"{workspace / payload_path} does not match canonical HEAD blob "
        f"byte-for-byte after --auto-accept apply.\n"
        f"  workspace bytes: {workspace_payload_bytes!r}\n"
        f"  canonical HEAD:  {canonical_head_blob!r}\n"
        f"This is Bug B: Class-B ACCEPT_UPSTREAM verdict-without-"
        f"stage shape."
    )


def test_alpha_hotfix_2_discard_path_does_not_advance_state_to_success(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """AC.α-hotfix-2.4 / Bug D: when --auto-accept's confidence floor is
    not met and the CLI discards staging, state.yaml status MUST NOT be
    SUCCESS. Otherwise next-run hits the convergent-idempotency
    fast-path in _ref_already_applied and silently no-ops via
    false-idempotency.

    Pre-α-hotfix-2: merge_helper.py's finally-block wrote
    status=SUCCESS unconditionally on clean-resolve, regardless of
    whether the apply step ran. CLI confirm-or-discard returning
    False → discard_staging → no apply. state.yaml stayed at
    SUCCESS. Subsequent runs short-circuited.

    Post-α-hotfix-2: merge_helper writes NEEDS_APPLY (new SyncStatus
    value) on clean-resolve. cli.py post-apply remains the
    authoritative SUCCESS writer. The idempotency fast-path requires
    SUCCESS → NEEDS_APPLY does NOT short-circuit.

    Test shape:
      - Build a canonical + workspace with one Class-C path that
        goes through LLM resolution at confidence=0.5.
      - Run cli.main with --auto-accept --confidence-floor 0.85
        → confirm gate returns False → discard_staging runs.
      - Read state.yaml; assert status is NEEDS_APPLY (NOT SUCCESS).
      - Bonus: invoke cli.main again with same args; assert it does
        NOT print "already applied" (i.e., does not short-circuit).
    """
    from workspace_sync.merge_primitives import (
        MergeClassification,
        MergeVerification,
    )
    from workspace_sync.state import SyncStatus, load_state

    # ---- 1. Canonical with one path ---------------------------
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    _build_canonical(canonical)

    payload_path = "framework/low_confidence_path.py"
    (canonical / "framework").mkdir()
    (canonical / payload_path).write_text("canonical-content\n")
    subprocess.run(["git", "-C", str(canonical), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(canonical), "commit", "-q", "-m", "v1"], check=True
    )

    # ---- 2. Workspace with different content (NN won't match) ---
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "framework").mkdir()
    (workspace / payload_path).write_bytes(b"workspace-stale-content\n")

    from workspace_sync.sync_protected import write_default_if_absent
    write_default_if_absent(workspace)

    pre_apply_workspace_bytes = (workspace / payload_path).read_bytes()

    # ---- 3. Stub the resolver to return low confidence -------
    import workspace_sync.cli as cli_mod

    class LowConfidenceStub:
        def invoke(self, prompt, response_model):
            if response_model is MergeClassification:
                return MergeClassification(
                    merge_class="unknown",
                    confidence=0.0,
                    reasoning="test stub",
                ), 50
            if response_model is MergeVerification:
                return MergeVerification(
                    passed=False,
                    class_mismatch=False,
                    concerns="stub",
                    confidence=0.0,
                ), 100
            # Returns inferred-merged with confidence below floor.
            return MergeVerdict(
                resolution="inferred-merged",
                merged_content="merged-content\n",
                rationale="low-confidence test merge",
                confidence=0.50,  # below 0.85 floor
            ), 200

    def fake_factory(module_spec: str, *, budget=None) -> MergeResolver:
        return MergeResolver(LowConfidenceStub(), budget or ResolverBudget())

    monkeypatch.setattr(cli_mod, "_load_merge_resolver", fake_factory)

    # ---- 4. Run pos-sync with --auto-accept; expect discard ---
    rc = main(
        [
            "--canonical",
            str(canonical),
            "--workspace",
            str(workspace),
            "--auto-accept",
            "--confidence-floor",
            "0.85",
        ]
    )
    assert rc == 0, (
        f"pos-sync should exit 0 on discard (the apply just doesn't "
        f"run); got rc={rc}; stdout/stderr=\n{capsys.readouterr()}"
    )

    # The workspace file was NOT updated (discard path).
    assert (workspace / payload_path).read_bytes() == pre_apply_workspace_bytes, (
        "discard path should leave the workspace file untouched"
    )

    # ---- 5. Binding assertion: state.yaml is NOT SUCCESS -------
    state = load_state(workspace)
    assert state is not None, "state.yaml should have been written"
    assert state.status is not SyncStatus.SUCCESS, (
        f"AC.α-hotfix-2.4 violated: state.yaml status is SUCCESS after "
        f"a discard path — re-runs would silently no-op via "
        f"false-idempotency. status={state.status!r}"
    )
    assert state.status is SyncStatus.NEEDS_APPLY, (
        f"expected status=needs-apply post-resolve-without-apply; "
        f"got {state.status!r}"
    )

    # ---- 6. Bonus: re-run does NOT short-circuit ---------------
    # Pre-fix, the second run would hit _ref_already_applied (which
    # required SUCCESS) and print "already applied at ref ...; no-op."
    # Post-fix, NEEDS_APPLY does NOT match the idempotency check, so
    # the second run re-resolves.
    capsys.readouterr()  # clear prior output
    rc2 = main(
        [
            "--canonical",
            str(canonical),
            "--workspace",
            str(workspace),
            "--auto-accept",
            "--confidence-floor",
            "0.85",
        ]
    )
    assert rc2 == 0
    captured = capsys.readouterr()
    assert "already applied" not in captured.err, (
        f"Bug D: NEEDS_APPLY state should NOT trigger the "
        f"already-applied fast-path. captured stderr:\n{captured.err}"
    )
