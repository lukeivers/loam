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

"""BB-feat (#54) synthetic validation — integration tests for the six
milestone-critical scenarios for Luke's "upgrade on pos3 doesn't lose
workspace-specific content" before the manual upgrade test.

Each test sets up a tmpdir-shaped synthetic workspace + a synthetic
canonical git working tree, invokes via the actual CLI surface, and
asserts outcomes against AC.H.* and the dispatch's stated milestone.

The six validation areas:

1. Class A workspace-data preservation (.pos/, .mcp.json, personas/)
2. Class B mixed-customisation merge (memory.yaml override semantics)
3. Class C framework-only updates (delegated to existing tests)
4. Audit log written (conflict report on disk after upgrade)
5. Idempotency (re-running converges)
6. Backward-compat (--staging-dir byte-identical to pre-#54)

Halt-and-surface findings are documented in the test-plan and noted
inline against the AS-BUILT behavior the tests pin.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest
import yaml
from pydantic import BaseModel

from loam.self_upgrade.canonical import resolve_canonical_to_staging
from loam.self_upgrade.cli import build_parser, main
from loam.self_upgrade.clause_checks import resolve_clause_h_inferred
from loam.self_upgrade.conflict_report import (
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    Resolution,
    load_conflict_report,
    save_conflict_report,
)
from loam.self_upgrade.manifest import Manifest, save_manifest
from loam.self_upgrade.merge_resolver import (
    MergeResolver,
    MergeVerdict,
    ResolverFailure,
)
from loam.self_upgrade.paths import Paths
from loam.self_upgrade.sync_protected import (
    FRAMEWORK_FLOOR,
    FileClass,
    SyncProtected,
    SyncProtectedRule,
    default_sync_protected,
    save_sync_protected,
)


# ---- helpers --------------------------------------------------------


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class _StubLLM:
    """Records call paths and returns canned verdicts for Class C."""

    def __init__(self, queued: list[tuple[MergeVerdict, int]]) -> None:
        self.queued = list(queued)
        self.call_count = 0
        self.invoked_paths: list[str] = []

    def invoke(
        self, prompt: str, response_model: type[BaseModel]
    ) -> tuple[BaseModel, int]:
        self.call_count += 1
        # Best-effort: extract path from prompt for assertion convenience.
        for line in prompt.splitlines():
            if line.startswith("File path:"):
                self.invoked_paths.append(line.split(":", 1)[1].strip())
                break
        if not self.queued:
            raise ResolverFailure("stub: out of canned verdicts")
        return self.queued.pop(0)


def _make_canonical(root: Path, tag: str = "pos-v2-v0.2.0") -> Path:
    """Build a synthetic canonical git working tree with a manifest."""
    root.mkdir(parents=True, exist_ok=True)
    (root / ".git").mkdir()  # marker for is-git-tree check
    manifest_dir = root / "self-upgrade" / "manifests"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / f"{tag}.yaml").write_text(
        yaml.safe_dump(
            {
                "release_tag": tag,
                "commit_sha": "abc1234",
                "files": [],
                "component_schemas": [],
                "breaking_changes": [],
                "migrations": [],
            }
        )
    )
    return root


# ---- 2. Class B mixed-customisation merge --------------------------


def test_class_b_workspace_modified_keeps_local(tmp_path: Path) -> None:
    """AC.H.3: Class B with workspace-side modification → KEEP_LOCAL.

    Fills the gap: existing `test_classify_class_b_operator_pref`
    only covers the classify() lookup, not the resolve helper's
    branch dispatch on change_kind.
    """
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "workspace").mkdir()
    (workspace / "workspace").mkdir()
    (canonical / "workspace" / "memory.yaml").write_text("default: 5\nfresh: true\n")
    (workspace / "workspace" / "memory.yaml").write_text("default: 99\nuser_pref: yes\n")

    entry = ConflictEntry(
        path="workspace/memory.yaml",
        prior_release_sha256="a" * 64,
        installed_sha256="b" * 64,
        new_release_sha256="c" * 64,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.PENDING,
    )
    report = ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        detected_at="2026-04-26T00:00:00+00:00",
        conflicts=[entry],
    )
    resolver = MergeResolver(_StubLLM([]))  # not invoked for B

    resolve_clause_h_inferred(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )

    e = report.conflicts[0]
    assert e.resolution is Resolution.KEEP_LOCAL
    assert e.confidence == 1.0
    assert "Class B" in (e.rationale or "")
    assert "workspace-modified" in (e.rationale or "")
    assert resolver.call_count == 0


def test_class_b_workspace_unmodified_accepts_canonical(tmp_path: Path) -> None:
    """AC.H.3: Class B with workspace untouched → ACCEPT_UPSTREAM.

    Fills the second branch of the Class B switch in
    `resolve_clause_h_inferred`. Triggered by ConflictChangeKind.
    LOCAL_MODIFIED_EQUALS_UPSTREAM (workspace's content matches
    upstream — i.e. workspace did not diverge from prior).
    """
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "workspace").mkdir()
    (workspace / "workspace").mkdir()
    (canonical / "workspace" / "memory.yaml").write_text("v: 2\n")
    (workspace / "workspace" / "memory.yaml").write_text("v: 2\n")

    entry = ConflictEntry(
        path="workspace/memory.yaml",
        prior_release_sha256="a" * 64,
        installed_sha256="b" * 64,
        new_release_sha256="b" * 64,
        change_kind=ConflictChangeKind.LOCAL_MODIFIED_EQUALS_UPSTREAM,
        resolution=Resolution.PENDING,
    )
    report = ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        detected_at="2026-04-26T00:00:00+00:00",
        conflicts=[entry],
    )
    resolver = MergeResolver(_StubLLM([]))

    resolve_clause_h_inferred(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )

    e = report.conflicts[0]
    assert e.resolution is Resolution.ACCEPT_UPSTREAM
    assert e.confidence == 1.0
    assert "Class B" in (e.rationale or "")
    assert "workspace unchanged" in (e.rationale or "")


# ---- 1. Class A preservation through CLI surface --------------------


def test_cli_canonical_pending_writes_audit_yaml(
    tmp_path: Path, capsys
) -> None:
    """AC.H.5 (as-built): CLI invocation with --canonical writes the
    conflict report to disk when conflicts remain pending.

    Sets up a workspace with Class-A and Class-C divergence vs canonical.
    Without `--merge-resolver-module` wired, clause-(h) is inactive so
    the existing conflict-detection path emits a pending conflict and
    writes the audit YAML at `paths.conflicts_yaml(tag)`. Asserts the
    audit shape + Class-A file is byte-identical pre-/post- the
    invocation.

    NOTE: amendment #55 (BB-feat bugfix) closes the AC.H.5 path
    divergence — when invoked via --canonical, the audit lands at
    `<workspace>/.pos/upgrade/<tag>/audit.yaml` per plan §2.
    """
    pos_base = tmp_path / "pos-base"
    workspace_canonical = tmp_path / "canonical"
    workspace_canonical.mkdir()
    (workspace_canonical / ".git").mkdir()

    tag = "pos-v2-v0.2.0"

    # Build canonical: framework file 'framework/a.py' that diverges
    # from workspace's installed copy.
    (workspace_canonical / "framework").mkdir()
    canonical_a_content = b"# canonical version 2\nprint('hello v2')\n"
    (workspace_canonical / "framework" / "a.py").write_bytes(
        canonical_a_content
    )

    # Class A file in canonical (would be Class-A protected).
    (workspace_canonical / "workspace" / ".pos").mkdir(parents=True)
    (workspace_canonical / "workspace" / ".pos" / "objective_tracker.sqlite").write_bytes(
        b"canonical-state"
    )

    # Manifest at conventional canonical location. Use change_kind=new
    # (only post_sha required) since sha-tracking the prior release in
    # a synthetic fixture is overkill for the audit-write assertion.
    manifest_dict = {
        "release_tag": tag,
        "commit_sha": "abc1234",
        "files": [
            {
                "path": "framework/a.py",
                "expected_pre_sha": None,
                "expected_post_sha": _sha(canonical_a_content),
                "change_kind": "new",
            }
        ],
    }
    manifest_dir = workspace_canonical / "self-upgrade" / "manifests"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / f"{tag}.yaml").write_text(yaml.safe_dump(manifest_dict))

    # Build the live framework tree at pos-base/framework/releases/<prior>
    # and symlink current → it. The "live" file at framework/a.py has
    # workspace-side content that diverges from the manifest's
    # expected_post_sha → triggers a conflict.
    paths = Paths(pos_base)
    prior = paths.release_dir("pos-v2-v0.1.0")
    prior.mkdir(parents=True)
    (prior / "framework").mkdir()
    workspace_a_content = b"# workspace-edited\nprint('local-edit')\n"
    (prior / "framework" / "a.py").write_bytes(workspace_a_content)
    paths.current_link.parent.mkdir(parents=True, exist_ok=True)
    if paths.current_link.exists() or paths.current_link.is_symlink():
        paths.current_link.unlink()
    os.symlink(str(prior), str(paths.current_link))

    # Class A workspace file (in the live tree); the upgrade must NOT
    # overwrite it. We snapshot its content before the upgrade.
    (prior / "workspace" / ".pos").mkdir(parents=True)
    workspace_pos_content = b"workspace-tracker-state-byte-identical"
    (prior / "workspace" / ".pos" / "objective_tracker.sqlite").write_bytes(
        workspace_pos_content
    )

    # Invoke CLI: --canonical mode WITHOUT --merge-resolver-module.
    # Clause-(h) helper does NOT run (gated on both flags); legacy
    # conflict-detection path writes the audit on pending.
    rc = main(
        [
            "--pos-base-dir", str(pos_base),
            "upgrade", tag,
            "--canonical", str(workspace_canonical),
            "--prior-tag", "pos-v2-v0.1.0",
        ]
    )
    captured = capsys.readouterr()
    # Pending conflict → rc=3, audit written.
    assert rc == 3, captured.out + captured.err
    # AC.HFX.3: workspace-local audit path under --canonical.
    audit_path = prior / "workspace" / ".pos" / "upgrade" / tag / "audit.yaml"
    assert audit_path.exists(), f"audit YAML not written at {audit_path}"
    # Legacy global path is NOT used in --canonical mode.
    legacy_path = paths.conflicts_yaml(tag)
    assert not legacy_path.exists(), (
        f"unexpected legacy audit YAML at {legacy_path} under --canonical mode"
    )

    audit = load_conflict_report(audit_path)
    assert audit.upgrade_tag == tag
    # framework/a.py is the conflict.
    paths_in = {c.path for c in audit.conflicts}
    assert "framework/a.py" in paths_in

    # Class A file untouched: the workspace's .pos sqlite content
    # matches what we wrote pre-invocation.
    after = (prior / "workspace" / ".pos" / "objective_tracker.sqlite").read_bytes()
    assert after == workspace_pos_content, (
        "Class A workspace file was modified by the upgrade halt path"
    )


def test_cli_canonical_pending_writes_audit_yaml_with_class_a_passthrough(
    tmp_path: Path, capsys
) -> None:
    """AC.H.2 + AC.H.5: with --merge-resolver-module wired, clause-h
    pre-stage helper resolves Class-A as KEEP_LOCAL automatically.

    Sets up a workspace whose live tree contains a Class-A path
    (.mcp.json) with workspace-side content. Canonical also has a
    .mcp.json with different content + a Class-C framework file that
    needs LLM resolution. Builds an explicit ConflictReport (skipping
    detect_conflicts since manifest is small), calls
    resolve_clause_h_inferred directly. Then asserts the audit can be
    persisted via save_conflict_report.

    Explicitly tests the milestone outcome: Class-A content survives.
    """
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    workspace_mcp_content = (
        '{"mcpServers": {"workspace-only": {"command": "magic"}}}'
    )
    canonical_mcp_content = '{"mcpServers": {}}'
    (canonical / "workspace").mkdir()
    (workspace / "workspace").mkdir()
    (canonical / "workspace" / ".mcp.json").write_text(canonical_mcp_content)
    (workspace / "workspace" / ".mcp.json").write_text(workspace_mcp_content)

    # Class-C: framework code conflict that needs LLM.
    canonical_framework = "# canonical fw\n"
    workspace_framework = "# workspace-tweaked fw\n"
    (canonical / "self-upgrade" / "src").mkdir(parents=True)
    (canonical / "self-upgrade" / "src" / "x.py").write_text(
        canonical_framework
    )
    (workspace / "self-upgrade" / "src").mkdir(parents=True)
    (workspace / "self-upgrade" / "src" / "x.py").write_text(
        workspace_framework
    )

    report = ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        detected_at="2026-04-26T00:00:00+00:00",
        conflicts=[
            ConflictEntry(
                path="workspace/.mcp.json",
                prior_release_sha256="a" * 64,
                installed_sha256="b" * 64,
                new_release_sha256="c" * 64,
                change_kind=(
                    ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED
                ),
                resolution=Resolution.PENDING,
            ),
            ConflictEntry(
                path="self-upgrade/src/x.py",
                prior_release_sha256="d" * 64,
                installed_sha256="e" * 64,
                new_release_sha256="f" * 64,
                change_kind=(
                    ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED
                ),
                resolution=Resolution.PENDING,
            ),
        ],
    )

    resolver = MergeResolver(
        _StubLLM(
            [
                (
                    MergeVerdict(
                        resolution="inferred-accept-canonical",
                        rationale="canonical's framework refactor supersedes the workspace tweak",
                        confidence=0.92,
                    ),
                    400,
                )
            ]
        )
    )

    resolve_clause_h_inferred(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )

    # AC.H.2: Class A → KEEP_LOCAL with confidence 1.0.
    a_entry = next(c for c in report.conflicts if c.path == "workspace/.mcp.json")
    assert a_entry.resolution is Resolution.KEEP_LOCAL
    assert a_entry.confidence == 1.0
    assert "Class A" in (a_entry.rationale or "")

    # AC.H.4: Class C → resolver verdict applied.
    c_entry = next(
        c for c in report.conflicts if c.path == "self-upgrade/src/x.py"
    )
    assert c_entry.resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    assert c_entry.confidence == 0.92
    assert "supersedes" in (c_entry.rationale or "")

    # AC.H.5 audit-log shape: the report can be persisted + reloaded.
    audit_target = tmp_path / "audit.yaml"
    save_conflict_report(report, audit_target)
    reloaded = load_conflict_report(audit_target)
    # rationale + confidence + user_override fields round-trip.
    assert reloaded.conflicts[0].rationale is not None
    assert reloaded.conflicts[0].confidence is not None
    assert reloaded.conflicts[0].user_override is False

    # Class A file still byte-identical to its pre-resolve state.
    assert (
        (workspace / "workspace" / ".mcp.json").read_text() == workspace_mcp_content
    ), "Class A workspace .mcp.json content drifted during clause-h"


# ---- 5. Idempotency on re-invocation --------------------------------


def test_cli_canonical_idempotent_rerun_no_resolver_calls(
    tmp_path: Path,
) -> None:
    """AC.H.8: Re-running clause-h with already-resolved entries is a
    no-op; no resolver calls fire.

    Convergent idempotency: feed `resolve_clause_h_inferred` a report
    where every Class-C entry was already resolved (e.g. by a prior
    successful run). The resolver MUST NOT be invoked.
    """
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "x.py").write_text("CANON")
    (workspace / "x.py").write_text("WORK")

    # Pre-resolved: prior run set INFERRED_ACCEPT_CANONICAL.
    pre_resolved = ConflictEntry(
        path="x.py",
        prior_release_sha256="a" * 64,
        installed_sha256="b" * 64,
        new_release_sha256="c" * 64,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
        rationale="prior run resolved",
        confidence=0.9,
    )
    report = ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        detected_at="2026-04-26T00:00:00+00:00",
        conflicts=[pre_resolved],
    )

    stub = _StubLLM([])  # empty queue → would ResolverFailure if called
    resolver = MergeResolver(stub)

    # Should not raise — already-resolved entries skip the resolver.
    resolve_clause_h_inferred(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )

    assert stub.call_count == 0
    # Verdict preserved.
    e = report.conflicts[0]
    assert e.resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    assert e.rationale == "prior run resolved"


def test_cli_user_override_idempotent_across_runs(tmp_path: Path) -> None:
    """AC.H.9: user_override=True entry is honoured + not re-resolved.

    A second invocation with the same canonical + workspace content
    sees the user_override flag and skips resolver invocation.
    """
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "x.py").write_text("CANON")
    (workspace / "x.py").write_text("WORK")

    overridden = ConflictEntry(
        path="x.py",
        prior_release_sha256="a" * 64,
        installed_sha256="b" * 64,
        new_release_sha256="c" * 64,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.KEEP_LOCAL,
        user_override=True,
        override_rationale="operator: keep workspace version unconditionally",
    )
    report = ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        detected_at="2026-04-26T00:00:00+00:00",
        conflicts=[overridden],
    )
    stub = _StubLLM(
        [
            (
                MergeVerdict(
                    resolution="inferred-accept-canonical",
                    rationale="resolver would say accept-canonical",
                    confidence=0.99,
                ),
                100,
            )
        ]
    )
    resolver = MergeResolver(stub)

    resolve_clause_h_inferred(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )

    # Override honoured: KEEP_LOCAL preserved, not flipped to canonical.
    e = report.conflicts[0]
    assert e.resolution is Resolution.KEEP_LOCAL
    assert e.user_override is True
    assert stub.call_count == 0


# ---- 6. Backward-compat with --staging-dir --------------------------


def test_cli_staging_dir_only_no_clause_h_path(
    tmp_path: Path, capsys
) -> None:
    """Hard Constraint #5: A --staging-dir invocation without
    --canonical does NOT invoke clause-(h). Behaviour byte-identical
    to pre-#54 (legacy conflict path).

    This is the dispatch's "Backward-compat" gate. We invoke the CLI
    with --staging-dir + a manifest, induce a conflict, and assert the
    pending audit YAML has no INFERRED_* entries (clause-h didn't run).
    """
    pos_base = tmp_path / "pos-base"
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "framework").mkdir()
    canonical_content = b"# upstream new\n"
    (staging / "framework" / "a.py").write_bytes(canonical_content)

    tag = "pos-v2-v0.2.0"
    manifest_path = tmp_path / "pos-release.yml"
    manifest_dict = {
        "release_tag": tag,
        "commit_sha": "abcdef1234",
        "files": [
            {
                "path": "framework/a.py",
                "expected_pre_sha": None,
                "expected_post_sha": _sha(canonical_content),
                "change_kind": "new",
            }
        ],
    }
    manifest = Manifest.model_validate(manifest_dict)
    save_manifest(manifest, manifest_path)

    paths = Paths(pos_base)
    prior = paths.release_dir("pos-v2-v0.1.0")
    prior.mkdir(parents=True)
    (prior / "framework").mkdir()
    (prior / "framework" / "a.py").write_bytes(b"# workspace edit\n")
    paths.current_link.parent.mkdir(parents=True, exist_ok=True)
    if paths.current_link.exists() or paths.current_link.is_symlink():
        paths.current_link.unlink()
    os.symlink(str(prior), str(paths.current_link))

    rc = main(
        [
            "--pos-base-dir", str(pos_base),
            "upgrade", tag,
            "--manifest", str(manifest_path),
            "--staging-dir", str(staging),
            "--prior-tag", "pos-v2-v0.1.0",
        ]
    )
    assert rc == 3  # pending conflict
    audit_path = paths.conflicts_yaml(tag)
    assert audit_path.exists()
    audit = load_conflict_report(audit_path)
    # Legacy path: no INFERRED_* resolutions emitted.
    assert all(
        c.resolution is Resolution.PENDING for c in audit.conflicts
    ), (
        "clause-h leaked into legacy --staging-dir path "
        f"(unexpected non-PENDING entries: {[c.resolution for c in audit.conflicts]})"
    )
    # No clause-h resolver state on entries.
    assert all(c.rationale is None for c in audit.conflicts)
    assert all(c.confidence is None for c in audit.conflicts)


def test_cli_canonical_without_merge_resolver_module_skips_clause_h(
    tmp_path: Path, capsys
) -> None:
    """--canonical without --merge-resolver-module is a valid pull
    mode — clause-(h) helper is gated on BOTH flags being present.

    Asserts the CLI accepts --canonical alone, falls through to the
    legacy conflict-detection path, and produces a PENDING-only audit.
    Important for the "Luke runs `pos upgrade --canonical` first to
    inspect what would happen" workflow.
    """
    pos_base = tmp_path / "pos-base"
    canonical = tmp_path / "canonical"
    _make_canonical(canonical, tag="pos-v2-v0.2.0")
    # Add a framework file to canonical for the manifest to reference.
    (canonical / "framework").mkdir()
    canonical_content = b"# upstream\n"
    (canonical / "framework" / "a.py").write_bytes(canonical_content)
    # Update the canonical manifest to include the file.
    manifest_path = (
        canonical / "self-upgrade" / "manifests" / "pos-v2-v0.2.0.yaml"
    )
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "release_tag": "pos-v2-v0.2.0",
                "commit_sha": "abc1234",
                "files": [
                    {
                        "path": "framework/a.py",
                        "expected_pre_sha": None,
                        "expected_post_sha": _sha(canonical_content),
                        "change_kind": "new",
                    }
                ],
            }
        )
    )

    paths = Paths(pos_base)
    prior = paths.release_dir("pos-v2-v0.1.0")
    prior.mkdir(parents=True)
    (prior / "framework").mkdir()
    (prior / "framework" / "a.py").write_bytes(b"# workspace edit\n")
    paths.current_link.parent.mkdir(parents=True, exist_ok=True)
    if paths.current_link.exists() or paths.current_link.is_symlink():
        paths.current_link.unlink()
    os.symlink(str(prior), str(paths.current_link))

    rc = main(
        [
            "--pos-base-dir", str(pos_base),
            "upgrade", "pos-v2-v0.2.0",
            "--canonical", str(canonical),
            "--prior-tag", "pos-v2-v0.1.0",
        ]
    )
    assert rc == 3  # pending conflict
    # AC.HFX.3: workspace-local audit path under --canonical.
    audit_path = prior / "workspace" / ".pos" / "upgrade" / "pos-v2-v0.2.0" / "audit.yaml"
    assert audit_path.exists()
    audit = load_conflict_report(audit_path)
    # Without --merge-resolver-module, clause-h skipped → all PENDING.
    assert all(
        c.resolution is Resolution.PENDING for c in audit.conflicts
    )


# ---- 4. Audit-log path / fresh-clone first-run --------------------


def test_cli_canonical_seeds_default_sync_protected_on_first_run(
    tmp_path: Path,
) -> None:
    """AC.H.10: A fresh-clone workspace with no .pos/sync-protected.yaml
    receives the default envelope on first clause-(h) invocation.

    The CLI's `_load_or_seed_sync_protected` path is exercised by
    invoking `resolve_clause_h_inferred` indirectly via the CLI on a
    workspace that lacks the envelope. We use the helper directly here
    since wiring the full CLI requires --merge-resolver-module which
    in turn requires the staging-dir pre-existing (the CLI doesn't yet
    write the seed without a real run).
    """
    from loam.self_upgrade.cli import _load_or_seed_sync_protected

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "workspace" / ".pos" / "sync-protected.yaml"
    assert not target.exists()

    sp = _load_or_seed_sync_protected(workspace)
    assert target.exists(), (
        "first-run failed to seed default sync-protected.yaml"
    )
    floor = {(r.pattern, r.klass) for r in sp.framework_floor}
    expected = {(p, k) for p, k in FRAMEWORK_FLOOR}
    assert floor == expected


# ---- Halt-and-surface marker tests --------------------------------


def test_halt_surface_audit_not_written_on_clean_clause_h_pass(
    tmp_path: Path,
) -> None:
    """AC.HFX.1 (closes #54 AC.H.5 success-path gap): every clause-(h)
    execution writes the workspace-local audit YAML, including the
    clean-pass terminus where every conflict was resolved.

    Pre-amendment-#55 behaviour pinned by this test as a halt-surface
    marker (commit `90246dc`): the helper did not write the audit on
    success. Amendment #55 lands the in-helper finally-block writer
    so audit.yaml exists after every helper invocation; this test is
    flipped to assert the spec'd behaviour.
    """
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "x.py").write_text("CANON")
    (workspace / "x.py").write_text("WORK")

    report = ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        detected_at="2026-04-26T00:00:00+00:00",
        conflicts=[
            ConflictEntry(
                path="x.py",
                prior_release_sha256="a" * 64,
                installed_sha256="b" * 64,
                new_release_sha256="c" * 64,
                change_kind=(
                    ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED
                ),
                resolution=Resolution.PENDING,
            )
        ],
    )
    resolver = MergeResolver(
        _StubLLM(
            [
                (
                    MergeVerdict(
                        resolution="inferred-accept-canonical",
                        rationale="superseded",
                        confidence=0.91,
                    ),
                    300,
                )
            ]
        )
    )

    resolve_clause_h_inferred(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )

    # All entries resolved in-memory.
    assert report.has_pending() is False
    e = report.conflicts[0]
    assert e.resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    assert e.confidence == 0.91
    assert e.rationale == "superseded"

    # AC.HFX.1 + AC.HFX.3: audit YAML exists at the workspace-local
    # path AFTER the helper's clean-pass terminus.
    audit_path = (
        workspace / "workspace" / ".pos" / "upgrade" / "pos-v2-v0.2.0" / "audit.yaml"
    )
    assert audit_path.exists(), (
        f"audit YAML not written at {audit_path} on clean clause-(h) pass"
    )
    persisted = load_conflict_report(audit_path)
    assert persisted.upgrade_tag == "pos-v2-v0.2.0"
    assert len(persisted.conflicts) == 1
    persisted_e = persisted.conflicts[0]
    assert persisted_e.resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    assert persisted_e.confidence == 0.91
    assert persisted_e.rationale == "superseded"


def test_halt_surface_state_yaml_not_implemented(tmp_path: Path) -> None:
    """AC.HFX.2 (closes #54 AC.H.8 idempotency gap): every clause-(h)
    execution writes `<workspace>/.pos/upgrade/state.yaml`.

    Pre-amendment-#55 behaviour pinned by this test as a halt-surface
    marker (commit `90246dc`): no code path wrote state.yaml.
    Amendment #55 lands the helper-side writer; this test is flipped
    to assert the spec'd behaviour.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    (canonical / "x.py").write_text("CANON")
    (workspace / "x.py").write_text("WORK")

    report = ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        detected_at="2026-04-26T00:00:00+00:00",
        conflicts=[
            ConflictEntry(
                path="x.py",
                prior_release_sha256="a" * 64,
                installed_sha256="b" * 64,
                new_release_sha256="c" * 64,
                change_kind=(
                    ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED
                ),
                resolution=Resolution.PENDING,
            )
        ],
    )
    resolver = MergeResolver(
        _StubLLM(
            [
                (
                    MergeVerdict(
                        resolution="inferred-accept-canonical",
                        rationale="r",
                        confidence=0.9,
                    ),
                    100,
                )
            ]
        )
    )
    resolve_clause_h_inferred(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )

    state_path = workspace / "workspace" / ".pos" / "upgrade" / "state.yaml"
    # AC.HFX.2: state.yaml exists + Pydantic-loadable + status=success.
    assert state_path.exists(), (
        f"state.yaml not written at {state_path} after clause-(h) pass"
    )

    from loam.self_upgrade.state import StateRecord, UpgradeStatus

    raw = yaml.safe_load(state_path.read_text())
    record = StateRecord.model_validate(raw)
    assert record.upgrade_tag == "pos-v2-v0.2.0"
    assert record.status is UpgradeStatus.SUCCESS
    assert record.total_conflicts == 1
    assert record.resolved_count == 1
    assert record.deferred_count == 0
    assert record.cumulative_tokens_used == 100
    assert record.halt_reason is None
    # audit_path points at the sibling workspace-local audit YAML.
    assert record.audit_path.endswith(
        "/.pos/upgrade/pos-v2-v0.2.0/audit.yaml"
    )
    assert Path(record.audit_path).exists()


def test_cli_auto_discovers_prior_state_yaml_on_canonical_rerun(
    tmp_path: Path, capsys
) -> None:
    """AC.HFX.2 auto-discovery: re-running `pos upgrade --canonical`
    against a workspace with a prior state.yaml resumes from the
    prior audit without operator-supplied --conflicts-from.

    Pre-amendment-#55, idempotency required passing `--conflicts-from
    <prior-yaml>` by hand. This test exercises the auto-discovery
    branch added in `cmd_upgrade` (load prior state.yaml; if it
    matches the current tag, load the prior audit as the starting
    report).
    """
    pos_base = tmp_path / "pos-base"
    canonical = tmp_path / "canonical"
    _make_canonical(canonical, tag="pos-v2-v0.2.0")
    (canonical / "framework").mkdir()
    canonical_content = b"# upstream\n"
    (canonical / "framework" / "a.py").write_bytes(canonical_content)
    manifest_path = (
        canonical / "self-upgrade" / "manifests" / "pos-v2-v0.2.0.yaml"
    )
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "release_tag": "pos-v2-v0.2.0",
                "commit_sha": "abc1234",
                "files": [
                    {
                        "path": "framework/a.py",
                        "expected_pre_sha": None,
                        "expected_post_sha": _sha(canonical_content),
                        "change_kind": "new",
                    }
                ],
            }
        )
    )
    paths = Paths(pos_base)
    prior = paths.release_dir("pos-v2-v0.1.0")
    prior.mkdir(parents=True)
    (prior / "framework").mkdir()
    (prior / "framework" / "a.py").write_bytes(b"# workspace edit\n")
    paths.current_link.parent.mkdir(parents=True, exist_ok=True)
    if paths.current_link.exists() or paths.current_link.is_symlink():
        paths.current_link.unlink()
    os.symlink(str(prior), str(paths.current_link))

    # Seed a prior state.yaml + audit.yaml mimicking a prior
    # successful clause-(h) run that resolved framework/a.py
    # via INFERRED_ACCEPT_CANONICAL.
    audit_dir = prior / "workspace" / ".pos" / "upgrade" / "pos-v2-v0.2.0"
    audit_dir.mkdir(parents=True)
    audit_target = audit_dir / "audit.yaml"
    seeded = ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        detected_at="2026-04-26T00:00:00+00:00",
        conflicts=[
            ConflictEntry(
                path="framework/a.py",
                prior_release_sha256="a" * 64,
                installed_sha256="b" * 64,
                new_release_sha256="c" * 64,
                change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="seeded from prior run",
                confidence=0.95,
            )
        ],
    )
    save_conflict_report(seeded, audit_target)

    from loam.self_upgrade.state import (
        StateRecord,
        UpgradeStatus,
        save_state,
    )

    save_state(
        StateRecord(
            upgrade_tag="pos-v2-v0.2.0",
            timestamp="2026-04-26T01:00:00+00:00",
            audit_path=str(audit_target.resolve()),
            total_conflicts=1,
            resolved_count=1,
            deferred_count=0,
            cumulative_tokens_used=200,
            status=UpgradeStatus.SUCCESS,
        ),
        prior,
    )

    # Re-invoke the CLI WITHOUT --conflicts-from. The auto-discovery
    # branch loads the prior audit as the starting report; the
    # already-resolved entry stays non-PENDING; rc != 3 (no pending
    # block).
    rc = main(
        [
            "--pos-base-dir", str(pos_base),
            "upgrade", "pos-v2-v0.2.0",
            "--canonical", str(canonical),
            "--prior-tag", "pos-v2-v0.1.0",
        ]
    )
    captured = capsys.readouterr()
    # rc == 2 (no --adapters-module) is acceptable here — the
    # important assertion is that the pending-block (rc=3) is NOT
    # entered, because the prior audit pre-resolved the conflict.
    assert rc != 3, (
        f"auto-discovery did not resume from prior state.yaml "
        f"(rc={rc}): {captured.out}{captured.err}"
    )
