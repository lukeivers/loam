"""AC.WSα.1 + AC.WSα.2 — α.1 ancestor-detection fast-path + cache.

Pre-resolver pass: when a workspace file's content matches the blob
recorded for the same path at some ancestor commit reachable from
the canonical ref's HEAD, the conflict resolves as
INFERRED_ACCEPT_CANONICAL with confidence 1.0 and the resolver is
NOT invoked. Walk is depth-capped (D-1 LOCKED 200) and cached
per-conflict.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
import yaml

from workspace_sync.ancestor_detection import (
    AncestorCache,
    AncestorMatch,
    cache_path,
    load_cache,
    save_cache,
    walk_ancestors,
)
from workspace_sync.conflict_report import (
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    Resolution,
)
from workspace_sync.merge_helper import resolve_inferred_conflicts
from workspace_sync.merge_resolver import (
    MergeResolver,
    MergeVerdict,
    ResolverFailure,
)
from workspace_sync.sync_protected import default_sync_protected


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(cwd), *args],
        text=True,
    ).strip()


def _make_repo_with_history(repo: Path, framework_path: str, contents: list[str]) -> list[str]:
    """Create a git repo with a series of commits, each one writing
    `contents[i]` to `framework_path`. Returns the SHA list (oldest
    last as Git emits)."""
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "commit.gpgsign", "false"],
        check=True,
    )
    shas: list[str] = []
    for i, body in enumerate(contents):
        target = repo / framework_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-q", "-m", f"step {i}"],
            check=True,
        )
        sha = _git(repo, "rev-parse", "HEAD")
        shas.append(sha)
    return shas


# ----------------------------------------------------------------------
# Direct walk_ancestors tests
# ----------------------------------------------------------------------


def test_workspace_matches_ancestor_walk_returns_match(tmp_path: Path) -> None:
    """AC.WSα.1: direct walker returns a match when content equals an ancestor blob."""
    repo = tmp_path / "canon"
    shas = _make_repo_with_history(
        repo,
        "framework.py",
        ["v1", "v2", "v3", "v4"],
    )
    target_sha = _sha256(b"v2")  # workspace content = blob from middle commit
    match, walk_depth, walk_short = walk_ancestors(
        canonical_path=repo,
        ref="HEAD",
        conflict_path="framework.py",
        target_sha256=target_sha,
        depth_cap=200,
    )
    assert match is not None
    # Should match on commit "v2" (3rd from end → 2nd from HEAD)
    assert match.commit_sha == shas[1]
    assert walk_depth >= 1


def test_workspace_genuinely_diverged_returns_no_match(tmp_path: Path) -> None:
    """AC.WSα.1: workspace content matching no historical commit declines."""
    repo = tmp_path / "canon"
    _make_repo_with_history(
        repo,
        "framework.py",
        ["alpha", "beta", "gamma"],
    )
    target_sha = _sha256(b"workspace-edited-not-in-history")
    match, walk_depth, walk_short = walk_ancestors(
        canonical_path=repo,
        ref="HEAD",
        conflict_path="framework.py",
        target_sha256=target_sha,
        depth_cap=200,
    )
    assert match is None
    # walk_short=True because the repo only has 3 commits (< depth_cap 200)
    # AND no match was found.
    assert walk_short is True


def test_walk_short_when_history_smaller_than_depth_cap(tmp_path: Path) -> None:
    """AC.WSα.2: walk_short=True when fewer commits exist than depth_cap."""
    repo = tmp_path / "canon"
    _make_repo_with_history(repo, "f.py", ["only"])
    target_sha = _sha256(b"never-existed")
    match, walk_depth, walk_short = walk_ancestors(
        canonical_path=repo,
        ref="HEAD",
        conflict_path="f.py",
        target_sha256=target_sha,
        depth_cap=200,
    )
    assert match is None
    assert walk_short is True
    assert walk_depth == 1  # we visited the only commit


def test_walk_terminates_at_depth_cap(tmp_path: Path) -> None:
    """AC.WSα.2: walk respects depth_cap; declines when match is beyond it."""
    repo = tmp_path / "canon"
    # 5 commits.
    _make_repo_with_history(repo, "f.py", ["a", "b", "c", "d", "e"])
    # Match would land at commit "a" (depth 5 from HEAD); cap at 3.
    target_sha = _sha256(b"a")
    match, walk_depth, walk_short = walk_ancestors(
        canonical_path=repo,
        ref="HEAD",
        conflict_path="f.py",
        target_sha256=target_sha,
        depth_cap=3,
    )
    # Walked 3 commits (e, d, c) — none match "a" → decline.
    assert match is None
    assert walk_depth == 3
    assert walk_short is False  # walked exactly cap → not a short walk


# ----------------------------------------------------------------------
# Cache tests
# ----------------------------------------------------------------------


def test_load_cache_returns_empty_when_missing(tmp_path: Path) -> None:
    """AC.WSα.2: missing cache file → empty cache."""
    cache = load_cache(tmp_path, "abc123", "fff111")
    assert cache.canonical_ref_sha == "fff111"
    assert cache.entries == {}


def test_load_cache_invalidates_on_canonical_advance(tmp_path: Path) -> None:
    """AC.WSα.2: cache from prior canonical SHA is wholesale invalidated."""
    # Save a cache claiming canonical=AAAA.
    cache = AncestorCache(canonical_ref_sha="AAAA")
    save_cache(cache, tmp_path, "ref1")
    assert cache_path(tmp_path, "ref1").exists()

    # Load with current_canonical_sha=BBBB → returns empty.
    loaded = load_cache(tmp_path, "ref1", "BBBB")
    assert loaded.canonical_ref_sha == "BBBB"
    assert loaded.entries == {}


def test_save_and_round_trip_cache(tmp_path: Path) -> None:
    """AC.WSα.2: cache round-trips through YAML."""
    from workspace_sync.ancestor_detection import AncestorCacheEntry

    cache = AncestorCache(canonical_ref_sha="HEAD-SHA")
    cache.put(
        AncestorCacheEntry(
            path="a.py",
            workspace_sha256="aaa",
            ancestor_sha="111",
            walk_depth=3,
            walk_short=False,
        )
    )
    save_cache(cache, tmp_path, "ref1")
    loaded = load_cache(tmp_path, "ref1", "HEAD-SHA")
    e = loaded.get("a.py", "aaa")
    assert e is not None
    assert e.ancestor_sha == "111"
    assert e.walk_depth == 3


# ----------------------------------------------------------------------
# Integration tests via resolve_inferred_conflicts
# ----------------------------------------------------------------------


class _StubLLMClient:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, prompt: str, response_model):
        self.calls += 1
        # Should never be called when α.1 fast-paths.
        raise ResolverFailure("stub: should not be called when α.1 hits")


def _make_report(*entries: ConflictEntry) -> ConflictReport:
    return ConflictReport(
        sync_ref="testref",
        detected_at="2026-04-26T00:00:00Z",
        conflicts=list(entries),
    )


def test_alpha1_ancestor_match_skips_resolver(tmp_path: Path) -> None:
    """AC.WSα.1: workspace content matching canonical-ancestor blob fast-paths
    INFERRED_ACCEPT_CANONICAL without invoking the resolver."""
    canonical = tmp_path / "canon"
    workspace = tmp_path / "ws"
    _make_repo_with_history(
        canonical,
        "framework.py",
        ["v1-content", "v2-content", "v3-content"],
    )
    # Workspace's framework.py mirrors v2-content (a historical ancestor blob).
    workspace.mkdir()
    (workspace / "framework.py").write_text("v2-content")

    # Build a Class-C conflict entry with installed_sha256 = sha256("v2-content").
    workspace_sha = _sha256(b"v2-content")
    canonical_sha = _sha256(b"v3-content")
    entry = ConflictEntry(
        path="framework.py",
        prior_release_sha256=None,
        installed_sha256=workspace_sha,
        new_release_sha256=canonical_sha,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.PENDING,
    )

    stub = _StubLLMClient()
    resolver = MergeResolver(stub)
    report = _make_report(entry)

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
        canonical_ref="HEAD",
    )

    assert stub.calls == 0, "resolver must NOT be invoked when α.1 hits"
    e = report.conflicts[0]
    assert e.resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    assert e.confidence == 1.0
    assert e.ancestor_match_sha is not None
    assert "ancestor" in (e.rationale or "").lower()


def test_alpha1_no_match_falls_through_to_resolver(tmp_path: Path) -> None:
    """AC.WSα.1: genuinely diverged workspace declines fast-path; resolver IS invoked."""
    canonical = tmp_path / "canon"
    workspace = tmp_path / "ws"
    _make_repo_with_history(
        canonical,
        "f.py",
        ["a", "b", "c"],
    )
    workspace.mkdir()
    (workspace / "f.py").write_text("workspace-edited-not-in-history")

    workspace_sha = _sha256(b"workspace-edited-not-in-history")
    canonical_sha = _sha256(b"c")
    entry = ConflictEntry(
        path="f.py",
        prior_release_sha256=None,
        installed_sha256=workspace_sha,
        new_release_sha256=canonical_sha,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.PENDING,
    )

    # Stub returns a valid verdict so the existing path completes.
    # Type-aware: classify call → unknown (forces fall-through);
    # verify call → fail; generator call → workspace-accept.
    class _OkClient:
        def __init__(self):
            self.calls = 0

        def invoke(self, prompt, response_model):
            self.calls += 1
            from workspace_sync.merge_primitives import (
                MergeClassification,
                MergeVerification,
            )
            if response_model is MergeClassification:
                return (
                    MergeClassification(
                        merge_class="unknown",
                        confidence=0.0,
                        reasoning="stub default",
                    ),
                    50,
                )
            if response_model is MergeVerification:
                return (
                    MergeVerification(
                        passed=False,
                        class_mismatch=False,
                        concerns=None,
                        confidence=0.0,
                    ),
                    100,
                )
            return (
                MergeVerdict(
                    resolution="inferred-accept-workspace",
                    rationale="stub generator output",
                    confidence=0.7,
                ),
                123,
            )

    client = _OkClient()
    resolver = MergeResolver(client)
    report = _make_report(entry)

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
        canonical_ref="HEAD",
    )

    # client.calls counts: classify (unknown) → fall-through →
    # generator. So we expect at least 1 generator-shaped call;
    # _OkClient wires classify to "unknown" so the generator path
    # runs. Total call count is 2 (classify + generator).
    assert client.calls >= 1, "resolver MUST be invoked when α.1 declines"
    e = report.conflicts[0]
    assert e.resolution is Resolution.INFERRED_ACCEPT_WORKSPACE
    assert e.ancestor_match_sha is None
    # Either fall-back through α.2 stub or direct generator path; either
    # way fallback_reason is present (α.2 stub raises
    # _FallthroughToGenerator → fallback_reason set).
    assert e.fallback_reason is not None


def test_alpha1_cache_hit_avoids_re_walk(tmp_path: Path) -> None:
    """AC.WSα.2: second run against unchanged state hits cache, zero git calls."""
    canonical = tmp_path / "canon"
    workspace = tmp_path / "ws"
    _make_repo_with_history(canonical, "f.py", ["v1", "v2"])
    workspace.mkdir()
    (workspace / "f.py").write_text("v1")

    workspace_sha = _sha256(b"v1")
    canonical_sha = _sha256(b"v2")
    entry = ConflictEntry(
        path="f.py",
        prior_release_sha256=None,
        installed_sha256=workspace_sha,
        new_release_sha256=canonical_sha,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.PENDING,
    )

    stub = _StubLLMClient()
    resolver = MergeResolver(stub)
    report = _make_report(entry)

    # First invocation: walks.
    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
        canonical_ref="HEAD",
    )
    assert report.conflicts[0].resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    assert cache_path(workspace, "testref").exists()

    # Reset the entry to PENDING (simulate re-run).
    entry2 = ConflictEntry(
        path="f.py",
        prior_release_sha256=None,
        installed_sha256=workspace_sha,
        new_release_sha256=canonical_sha,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.PENDING,
    )
    report2 = _make_report(entry2)

    # Spy on walk_ancestors itself. Cache-hit short-circuit means
    # walk_ancestors must NOT be invoked on the second run.
    import workspace_sync.merge_helper as mhm
    from unittest import mock

    walk_calls: list[tuple] = []
    original_walk = mhm.walk_ancestors

    def _spy_walk(*args, **kwargs):
        walk_calls.append((args, kwargs))
        return original_walk(*args, **kwargs)

    with mock.patch.object(mhm, "walk_ancestors", side_effect=_spy_walk):
        resolve_inferred_conflicts(
            report=report2,
            sync_protected=default_sync_protected(),
            canonical_root=canonical,
            workspace_root=workspace,
            resolver=resolver,
            canonical_ref="HEAD",
        )

    assert walk_calls == [], (
        f"cache hit must avoid the walk; got walk_ancestors calls: {len(walk_calls)}"
    )
    assert report2.conflicts[0].resolution is Resolution.INFERRED_ACCEPT_CANONICAL


def test_alpha1_cache_invalidates_on_canonical_advance(tmp_path: Path) -> None:
    """AC.WSα.2: when canonical-HEAD SHA changes, cache is wholesale invalidated."""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    # Pre-seed a stale cache claiming a different canonical SHA.
    stale = AncestorCache(canonical_ref_sha="STALE-CANONICAL-SHA")
    save_cache(stale, workspace, "testref")

    # Fresh canonical with new history.
    canonical = tmp_path / "canon"
    _make_repo_with_history(canonical, "f.py", ["v1"])
    workspace_sha = _sha256(b"v1")
    canonical_sha = _sha256(b"v1")  # same; trivial

    entry = ConflictEntry(
        path="f.py",
        prior_release_sha256=None,
        installed_sha256=workspace_sha,
        new_release_sha256=canonical_sha,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.PENDING,
    )
    (workspace / "f.py").write_text("v1")

    stub = _StubLLMClient()
    resolver = MergeResolver(stub)
    report = _make_report(entry)

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
        canonical_ref="HEAD",
    )

    # Cache should have been invalidated and rebuilt; the entry is
    # fresh-walked.
    assert report.conflicts[0].resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    cache_after = load_cache(
        workspace,
        "testref",
        report.conflicts[0].ancestor_match_sha or "x",
    )
    # The cache file post-run carries the new canonical SHA, not the stale one.
    raw = yaml.safe_load(cache_path(workspace, "testref").read_text())
    assert raw["canonical_ref_sha"] != "STALE-CANONICAL-SHA"
