"""Synthesise the ``framework-only`` branch from a ``pos-v2`` commit.

The synthesis is a pure git-plumbing composition: read the source
commit's tree; build a working index that promotes
``framework/<entry>`` paths to root and drops paths classified as
``dev_only`` / ``excluded_from_publish`` per the publish-mode
partition manifest (amendment #83 — M2). The resulting tree is
written via ``git write-tree``; a new commit is composed via
``git commit-tree`` and ``git update-ref`` advances the
``framework-only`` ref.

The synthesis is deterministic: given the same input commit + the
same partition manifest + the same ref-tip, the output commit's
tree-SHA is stable. Re-running on a ref already pointing at the
latest synthesis is a no-op (the tip's parent + tree already
match).

For ``framework-only`` to share a fast-forward graph with its prior
tip across successive ``pos-v2`` commits, the synthesis chains
parents: each new ``framework-only`` commit's parent is the
previous ``framework-only`` tip (when present), so
``git merge --ff-only`` from a workspace that tracks
``framework-only`` succeeds.

The first synthesis (no prior ``framework-only`` ref) creates a
parent-less commit; subsequent syntheses chain on it.

Partition (amendment #83 — M2). The synthesis is manifest-driven:
the publish-mode partition manifest at
``<repo>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml``
(or the path passed via the ``manifest_path`` parameter) classifies
every workspace-relative leaf path. Paths classified as
``DEV_ONLY`` or ``EXCLUDED_FROM_PUBLISH`` drop from the synthetic
tree; ``PUBLIC_ONLY`` and ``DEV_AND_PUBLIC`` ship.
``audit_excludes`` patterns drop silently (transient state). A
non-audit-excluded leaf that doesn't classify into any of the four
classes raises ``SynthesisError`` — the manifest must cover every
shipping path (AC.OSS-M2.4).

Substitution pass (M9). After the partition filter, every shipping
leaf's blob content is read, the M9-locked substitution table is
applied (canonical-host paths → ``<workspace>/loam/...``,
``lukeivers/pos-v2`` → ``lukeivers/loam``, ``Luke Ivers`` →
``Alice Anderson``), and IFF a token was replaced the rewritten
content is written as a new blob via ``git hash-object -w``; the new
SHA replaces the source SHA in the synthetic tree. Binary blobs
preserve the source SHA verbatim. Determinism + idempotence per
AC.OSS-M9.3 / AC.OSS-M9.4 — see
``loam.publish_framework_only.substitution`` for the table + helper.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from loam.publish_framework_only.partition import (
    ManifestError,
    PartitionClass,
    PartitionManifest,
    classify_path,
    is_audit_excluded,
    is_publishable,
    load_manifest,
)
from loam.publish_framework_only.substitution import (
    SUBSTITUTION_TABLE,
    apply_substitutions,
)


# The subdir under canonical's ``pos-v2`` whose contents promote to
# the synthetic-branch root. Manifest-driven synthesis preserves
# this promotion convention; the constant documents intent.
FRAMEWORK_PREFIX = "framework"


class SynthesisError(Exception):
    """Base exception for synthesis failures."""


@dataclass(frozen=True)
class SynthesisResult:
    """Outcome of a successful synthesis.

    ``framework_only_sha`` is the new (or unchanged, if no-op) tip
    of the ``framework-only`` ref. ``no_op`` is True when the
    synthesis detected the source commit's tree was already
    represented by the current ``framework-only`` tip.
    """

    source_sha: str
    framework_only_sha: str
    target_ref: str
    no_op: bool


def _git(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
) -> str:
    """Run a git command; raise ``SynthesisError`` on non-zero exit.

    Returns stdout (stripped of one trailing newline). Empty stderr
    is captured for the error message but discarded on success.
    """
    completed = subprocess.run(  # noqa: S603 — argv constructed
        ["git", *args],
        cwd=str(cwd),
        stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
        input=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
        env=env,
    )
    if completed.returncode != 0:
        raise SynthesisError(
            f"git {' '.join(args)} (cwd={cwd}) "
            f"failed (exit {completed.returncode}): "
            f"{(completed.stderr or '').strip()!r}"
        )
    return completed.stdout.rstrip("\n")


def _resolve_source_sha(repo: Path, source: str) -> str:
    """Resolve a user-facing ref/SHA to a full commit SHA."""
    return _git(
        ["rev-parse", "--verify", f"{source}^{{commit}}"], cwd=repo
    )


def _ref_exists(repo: Path, ref: str) -> bool:
    """True iff ``ref`` resolves to a commit."""
    completed = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=str(repo),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    return completed.returncode == 0


def _resolve_ref_sha(repo: Path, ref: str) -> str | None:
    """Resolve ``ref`` to its commit SHA, or None if it does not exist."""
    if not _ref_exists(repo, ref):
        return None
    return _git(
        ["rev-parse", "--verify", f"{ref}^{{commit}}"], cwd=repo
    )


@dataclass(frozen=True)
class _LeafEntry:
    """A single leaf path under the source tree.

    ``mode`` is the git filemode (``100644``, ``100755``, ``120000``,
    ``160000``); ``object_type`` is ``blob`` or ``commit`` (for
    submodules); ``sha`` is the object SHA; ``source_path`` is the
    canonical's tree-relative path (with the ``framework/`` prefix
    intact for component paths); ``synthetic_path`` is the path the
    leaf takes in the synthetic tree (``framework/<rel>`` rewritten
    to ``<rel>`` at root; top-level paths verbatim).
    """

    mode: str
    object_type: str
    sha: str
    source_path: str
    synthetic_path: str


def _ls_tree_recursive(
    repo: Path, source_sha: str
) -> list[tuple[str, str, str, str]]:
    """Return ``[(mode, type, sha, posix_path), ...]`` for every leaf
    under ``source_sha``'s tree.

    ``git ls-tree -r <sha>`` emits leaves only (recursive; trees
    skipped). Each output line has shape::

        <mode> SP <type> SP <sha> TAB <name>

    where TAB separates the SHA from the path. The path is
    workspace-relative, POSIX-style.
    """
    out = _git(["ls-tree", "-r", source_sha], cwd=repo)
    if not out:
        return []
    leaves: list[tuple[str, str, str, str]] = []
    for line in out.split("\n"):
        if not line:
            continue
        head, _, name = line.partition("\t")
        parts = head.split(" ")
        if len(parts) != 3:
            raise SynthesisError(
                f"unexpected ls-tree line shape: {line!r}"
            )
        mode, object_type, sha = parts
        leaves.append((mode, object_type, sha, name))
    return leaves


def _cat_blob(repo: Path, blob_sha: str) -> bytes:
    """Return the raw bytes of ``blob_sha`` via ``git cat-file blob``.

    Used by the M9 substitution pass: shipping leaves have their blob
    bytes read, the substitution table is applied, and IFF a token was
    replaced a new blob is written via ``_hash_object_w`` and the new
    SHA replaces the source SHA in the synthetic tree.
    """
    completed = subprocess.run(  # noqa: S603 — argv constructed
        ["git", "cat-file", "blob", blob_sha],
        cwd=str(repo),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise SynthesisError(
            f"git cat-file blob {blob_sha} (cwd={repo}) "
            f"failed (exit {completed.returncode}): "
            f"{(completed.stderr or b'').decode('utf-8', 'replace').strip()!r}"
        )
    return completed.stdout


def _hash_object_w(repo: Path, content: bytes) -> str:
    """Write ``content`` as a new blob via ``git hash-object -w --stdin``.

    Returns the new blob SHA. Used by the M9 substitution pass (per
    AC.OSS-M9.2): a rewritten blob is hashed and the new SHA replaces
    the source SHA in the synthetic tree's index.
    """
    completed = subprocess.run(  # noqa: S603
        ["git", "hash-object", "-w", "--stdin"],
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        input=content,
        check=False,
    )
    if completed.returncode != 0:
        raise SynthesisError(
            f"git hash-object -w --stdin (cwd={repo}) "
            f"failed (exit {completed.returncode}): "
            f"{(completed.stderr or b'').decode('utf-8', 'replace').strip()!r}"
        )
    return completed.stdout.decode("ascii").rstrip("\n")


def _build_synthetic_tree(
    repo: Path,
    source_sha: str,
    manifest: PartitionManifest,
) -> str:
    """Build the synthetic ``framework-only`` tree.

    Walks every leaf under ``source_sha``'s tree, classifies each
    via the partition manifest, drops non-publishable + audit-
    excluded leaves, rewrites ``framework/<rel>`` → ``<rel>`` at
    root, and assembles the resulting paths into a tree via a
    temporary git index (``read-tree`` + ``update-index`` +
    ``write-tree``).

    Raises ``SynthesisError`` if any non-audit-excluded leaf doesn't
    classify into any of the four partition classes (the manifest
    must cover every shipping path per AC.OSS-M2.4).
    """
    leaves = _ls_tree_recursive(repo, source_sha)
    if not leaves:
        raise SynthesisError(
            f"source commit {source_sha} has an empty tree; "
            "nothing to synthesise"
        )

    publishable: list[_LeafEntry] = []
    unclassified: list[str] = []
    saw_framework_leaf = False
    for mode, object_type, sha, source_path in leaves:
        # Audit-excluded paths drop silently (transient state).
        if is_audit_excluded(manifest, source_path):
            continue
        klass = classify_path(manifest, source_path)
        if klass is None:
            unclassified.append(source_path)
            continue
        if not is_publishable(klass):
            continue
        # Promote framework/<rel> to root; top-level entries verbatim.
        framework_prefix = f"{FRAMEWORK_PREFIX}/"
        if source_path.startswith(framework_prefix):
            synthetic_path = source_path[len(framework_prefix):]
            saw_framework_leaf = True
        elif source_path == FRAMEWORK_PREFIX:
            # Bare framework path (unlikely — ls-tree -r emits leaves);
            # safety branch — drop, the children handle it.
            continue
        else:
            synthetic_path = source_path

        # M9 substitution pass (AC.OSS-M9.2). Applied AFTER the
        # partition filter (this loop reaches here only for shipping
        # leaves) and BEFORE _LeafEntry construction. For blob leaves,
        # read the blob content, apply the substitution table, and
        # IFF the substitution changed the content, write a new blob
        # and use the new SHA. Binary blobs (UnicodeDecodeError) and
        # non-blob entries (submodules etc.) preserve the source SHA.
        leaf_sha = sha
        if object_type == "blob":
            blob_content = _cat_blob(repo, sha)
            sub_result = apply_substitutions(
                blob_content, SUBSTITUTION_TABLE
            )
            if sub_result.changed:
                leaf_sha = _hash_object_w(repo, sub_result.content)

        publishable.append(
            _LeafEntry(
                mode=mode,
                object_type=object_type,
                sha=leaf_sha,
                source_path=source_path,
                synthetic_path=synthetic_path,
            )
        )

    if unclassified:
        sample = unclassified[:3]
        raise SynthesisError(
            f"partition incomplete: {len(unclassified)} unclassified "
            f"path(s); samples: {sample!r}. Update the publish-mode "
            "partition manifest to cover every workspace path."
        )

    if not saw_framework_leaf:
        raise SynthesisError(
            f"source commit {source_sha} has no entries under "
            f"{FRAMEWORK_PREFIX}/; nothing to synthesise"
        )

    # Collision check: two distinct source_paths must not map to the
    # same synthetic_path (e.g. a top-level ``cost-governance.md``
    # would collide with the promoted ``framework/cost-governance/``
    # entry — same name at synthetic root). Halt explicitly.
    by_synthetic: dict[str, str] = {}
    for entry in publishable:
        existing = by_synthetic.get(entry.synthetic_path)
        if existing is not None and existing != entry.source_path:
            raise SynthesisError(
                f"name collision while synthesising {source_sha}: "
                f"{entry.synthetic_path!r} appears under both "
                f"{existing!r} and {entry.source_path!r}"
            )
        by_synthetic[entry.synthetic_path] = entry.source_path

    return _write_tree_from_entries(repo, publishable)


def _write_tree_from_entries(
    repo: Path, entries: list[_LeafEntry]
) -> str:
    """Compose a tree SHA from a list of ``(mode, type, sha,
    synthetic_path)`` leaves.

    Uses a temp index file (``GIT_INDEX_FILE``) to avoid disturbing
    the real index. Each leaf is added via
    ``git update-index --add --cacheinfo <mode>,<sha>,<path>``;
    ``git write-tree`` then produces the assembled tree SHA.

    Submodule entries (``object_type == "commit"``, mode 160000) are
    not expected in canonical's tree (no submodules in pos-v2);
    raise ``SynthesisError`` if encountered to surface unexpected
    shape.
    """
    # Use a temp index path that does NOT exist on disk. ``git update-
    # index --add`` creates a fresh empty index when GIT_INDEX_FILE
    # points at a non-existent path; an empty file (as
    # ``NamedTemporaryFile`` produces) is rejected as malformed.
    tmp_dir = Path(tempfile.mkdtemp(prefix="framework-only-index-"))
    tmp_index_path = tmp_dir / "index"
    try:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(tmp_index_path)
        for entry in entries:
            if entry.object_type != "blob":
                # Symlinks come through as blobs with mode 120000;
                # filemode 160000 is submodule (object_type=commit).
                # M2 supports blobs only; raise on anything else for
                # forward-strict behaviour.
                raise SynthesisError(
                    "unsupported tree entry type "
                    f"{entry.object_type!r} for path "
                    f"{entry.source_path!r}"
                )
            _git(
                [
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    f"{entry.mode},{entry.sha},{entry.synthetic_path}",
                ],
                cwd=repo,
                env=env,
            )
        return _git(["write-tree"], cwd=repo, env=env)
    finally:
        try:
            if tmp_index_path.exists():
                tmp_index_path.unlink()
            tmp_dir.rmdir()
        except OSError:
            pass


def synthesise_framework_only(
    repo: Path | str,
    *,
    manifest_path: Path | str,
    source: str = "HEAD",
    target_ref: str = "refs/heads/framework-only",
    author_name: str | None = None,
    author_email: str | None = None,
    commit_message: str | None = None,
) -> SynthesisResult:
    """Synthesise / advance ``target_ref`` from ``source``.

    Composes git plumbing (``rev-parse``, ``ls-tree``,
    ``read-tree`` / ``update-index`` / ``write-tree``,
    ``commit-tree``, ``update-ref``) under the publish-mode
    partition manifest at ``manifest_path``. Idempotent: when the
    existing ``target_ref`` already points at a commit whose tree
    matches the synthesised tree AND whose source-tracking trailer
    matches the source SHA, no new commit is created and ``no_op``
    is True.

    Parameters
    ----------
    repo:
        Path to the canonical pos-v2 git repo (working tree or bare).
    manifest_path:
        Path to the publish-mode partition manifest YAML. Required
        per AC.OSS-M2.5 + plan §10 D-build.M2.4 (callers must
        supply it explicitly; the CLI defaults the value from
        ``<repo>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml``).
    source:
        Ref or SHA to synthesise from (default ``HEAD``).
    target_ref:
        Fully-qualified ref to advance (default
        ``refs/heads/framework-only``).
    author_name / author_email:
        Override author identity in the synthesised commit. When
        None, falls back to the source commit's author.
    commit_message:
        Override commit message. When None, uses
        ``"framework-only synthesis of <source-sha-short>"`` (with
        the original source commit's subject appended on a separate
        line).

    Returns
    -------
    SynthesisResult
        Carries the source SHA, the synthesised SHA (== existing
        tip when no-op), the target_ref name, and the ``no_op``
        flag.

    Raises
    ------
    SynthesisError
        When git plumbing fails, the partition manifest fails to
        load, or the source tree shape is invalid (empty tree,
        no ``framework/`` entries, partition incompleteness, name
        collision between framework and top-level docs, etc.).
    """
    repo = Path(repo).resolve()
    if not (repo / ".git").exists() and not (repo / "HEAD").exists():
        raise SynthesisError(
            f"repo {repo!s} is not a git working tree or bare repo"
        )

    manifest_path = Path(manifest_path).resolve()
    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        raise SynthesisError(
            f"failed to load partition manifest at {manifest_path!s}: "
            f"{exc}"
        ) from exc
    except FileNotFoundError as exc:
        raise SynthesisError(str(exc)) from exc

    source_sha = _resolve_source_sha(repo, source)
    target_tree_sha = _build_synthetic_tree(repo, source_sha, manifest)

    parent_sha = _resolve_ref_sha(repo, target_ref)

    # Idempotency: if target_ref already points at a commit whose
    # tree-SHA matches AND whose source-tracking trailer matches the
    # source SHA, this is a no-op.
    if parent_sha is not None:
        existing_tree = _git(
            ["rev-parse", f"{parent_sha}^{{tree}}"], cwd=repo
        )
        if existing_tree == target_tree_sha:
            existing_message = _git(
                ["log", "-1", "--format=%B", parent_sha], cwd=repo
            )
            if f"Source-Commit: {source_sha}" in existing_message:
                return SynthesisResult(
                    source_sha=source_sha,
                    framework_only_sha=parent_sha,
                    target_ref=target_ref,
                    no_op=True,
                )

    # Compose author / committer identity. Default to the source
    # commit's identity for traceability.
    if author_name is None:
        author_name = _git(
            ["log", "-1", "--format=%an", source_sha], cwd=repo
        )
    if author_email is None:
        author_email = _git(
            ["log", "-1", "--format=%ae", source_sha], cwd=repo
        )
    if commit_message is None:
        source_subject = _git(
            ["log", "-1", "--format=%s", source_sha], cwd=repo
        )
        commit_message = (
            f"framework-only synthesis of {source_sha[:7]}\n"
            f"\n"
            f"Source: {source_subject}\n"
            f"Source-Commit: {source_sha}\n"
        )
    elif f"Source-Commit: {source_sha}" not in commit_message:
        commit_message = (
            commit_message.rstrip("\n")
            + f"\n\nSource-Commit: {source_sha}\n"
        )

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = author_name
    env["GIT_AUTHOR_EMAIL"] = author_email
    env["GIT_COMMITTER_NAME"] = author_name
    env["GIT_COMMITTER_EMAIL"] = author_email

    commit_args = ["commit-tree", target_tree_sha, "-m", commit_message]
    if parent_sha is not None:
        commit_args.extend(["-p", parent_sha])
    new_commit_sha = _git(commit_args, cwd=repo, env=env)

    _git(
        [
            "update-ref",
            target_ref,
            new_commit_sha,
            parent_sha if parent_sha is not None else "0" * 40,
        ],
        cwd=repo,
    )

    return SynthesisResult(
        source_sha=source_sha,
        framework_only_sha=new_commit_sha,
        target_ref=target_ref,
        no_op=False,
    )
