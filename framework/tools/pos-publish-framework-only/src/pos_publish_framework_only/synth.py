"""Synthesise the ``framework-only`` branch from a ``pos-v2`` commit.

The synthesis is a pure git-plumbing composition: read the source
commit's tree, build a new tree by promoting ``framework/<entry>``
entries to root and overlaying the top-level docs (``CLAUDE.md``,
``CLAUDE.dev.md``, ``README.md``, ``docs/``), then ``commit-tree`` +
``update-ref``. No working-tree mutation; runs against a bare clone or
a working tree indifferently.

The synthesis is deterministic: given the same input commit + the
same ref-tip, the output commit's tree-SHA is stable. Re-running on a
ref already pointing at the latest synthesis is a no-op (the tip's
parent + tree already match).

For ``framework-only`` to share a fast-forward graph with its prior
tip across successive ``pos-v2`` commits, the synthesis chains
parents: each new ``framework-only`` commit's parent is the previous
``framework-only`` tip (when present), so ``git merge --ff-only`` from
a workspace that tracks ``framework-only`` succeeds.

The first synthesis (no prior ``framework-only`` ref) creates a
parent-less commit; subsequent syntheses chain on it.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


# Top-level entries on the ``pos-v2`` branch that are carried verbatim
# into the ``framework-only`` branch root. Order matters only for
# determinism of the assembled tree (git sorts internally; this list
# documents intent).
TOP_LEVEL_DOCS: tuple[str, ...] = (
    "CLAUDE.md",
    "CLAUDE.dev.md",
    "README.md",
    "docs",
)

# The subdir under canonical's ``pos-v2`` whose contents promote to
# the synthetic-branch root.
FRAMEWORK_PREFIX = "framework"


class SynthesisError(Exception):
    """Base exception for synthesis failures."""


@dataclass(frozen=True)
class SynthesisResult:
    """Outcome of a successful synthesis.

    ``framework_only_sha`` is the new (or unchanged, if no-op) tip of
    the ``framework-only`` ref. ``no_op`` is True when the synthesis
    detected the source commit's tree was already represented by the
    current ``framework-only`` tip.
    """

    source_sha: str
    framework_only_sha: str
    target_ref: str
    no_op: bool


def _git(args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    """Run a git command; raise ``SynthesisError`` on non-zero exit.

    Returns stdout (stripped). Empty stderr is captured for the error
    message but discarded on success.
    """
    completed = subprocess.run(  # noqa: S603 — argv constructed
        ["git", *args],
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
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
    return _git(["rev-parse", "--verify", f"{source}^{{commit}}"], cwd=repo)


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
    return _git(["rev-parse", "--verify", f"{ref}^{{commit}}"], cwd=repo)


def _ls_tree(repo: Path, tree_ish: str, *, path: str = "") -> list[str]:
    """Return raw ``ls-tree`` lines for ``tree_ish`` (optionally
    scoped to ``path``).

    Each line has the shape ``<mode> <type> <sha>\\t<name>`` (tab
    separator before name). Suitable for direct piping back into
    ``git mktree``.
    """
    args = ["ls-tree", tree_ish]
    if path:
        args.append(path)
    out = _git(args, cwd=repo)
    if not out:
        return []
    return out.split("\n")


def _entry_name(line: str) -> str:
    """Extract the entry-name from an ls-tree line.

    ``<mode> <type> <sha>\\t<name>``
    """
    return line.split("\t", 1)[1]


def _entry_with_renamed_path(line: str, new_name: str) -> str:
    """Rewrite an ls-tree line's name to ``new_name``."""
    head, _name = line.split("\t", 1)
    return f"{head}\t{new_name}"


def _mktree(repo: Path, lines: list[str]) -> str:
    """``git mktree`` from ls-tree-shaped lines; return the tree SHA."""
    completed = subprocess.run(  # noqa: S603
        ["git", "mktree"],
        cwd=str(repo),
        input="\n".join(lines) + ("\n" if lines else ""),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise SynthesisError(
            f"git mktree (cwd={repo}) failed (exit "
            f"{completed.returncode}): "
            f"{(completed.stderr or '').strip()!r}"
        )
    return completed.stdout.strip()


def _build_synthetic_tree(repo: Path, source_sha: str) -> str:
    """Build the ``framework-only`` tree for ``source_sha``.

    Composition:

    1. Read the source commit's ``framework/`` subtree entries
       (one ls-tree call scoped to ``framework/``). These promote
       to root.
    2. Read the source commit's ``CLAUDE.md`` / ``CLAUDE.dev.md`` /
       ``README.md`` / ``docs/`` entries (one ls-tree call per top-
       level doc; missing entries are skipped silently).
    3. Combine: framework entries (renamed to drop the ``framework/``
       prefix at root) + top-level doc entries.
    4. ``git mktree`` to produce the new root tree.

    Collisions (e.g. a top-level doc with the same name as a
    promoted framework entry) raise ``SynthesisError`` — the source
    tree shape would be ambiguous and the synthesis must halt.
    """
    framework_entries_raw = _ls_tree(
        repo, source_sha, path=f"{FRAMEWORK_PREFIX}/"
    )
    promoted_entries: list[tuple[str, str]] = []
    for line in framework_entries_raw:
        if not line.strip():
            continue
        full_name = _entry_name(line)
        # ``ls-tree <sha> <prefix>/`` returns names like
        # ``framework/cost-governance``. Strip the prefix.
        prefix = f"{FRAMEWORK_PREFIX}/"
        if not full_name.startswith(prefix):
            raise SynthesisError(
                f"unexpected ls-tree entry name {full_name!r} "
                f"(expected prefix {prefix!r})"
            )
        bare_name = full_name[len(prefix):]
        promoted_entries.append((bare_name, _entry_with_renamed_path(line, bare_name)))

    if not promoted_entries:
        raise SynthesisError(
            f"source commit {source_sha} has no entries under "
            f"{FRAMEWORK_PREFIX}/; nothing to synthesise"
        )

    seen_names: dict[str, str] = {name: "framework" for name, _ in promoted_entries}
    final_lines: list[str] = [line for _, line in promoted_entries]

    # Top-level docs.
    for doc in TOP_LEVEL_DOCS:
        doc_lines = _ls_tree(repo, source_sha, path=doc)
        for line in doc_lines:
            if not line.strip():
                continue
            name = _entry_name(line)
            if name in seen_names:
                raise SynthesisError(
                    f"name collision while synthesising {source_sha}: "
                    f"{name!r} appears under both "
                    f"{seen_names[name]!r} and the top-level docs"
                )
            seen_names[name] = "top-level"
            final_lines.append(line)

    return _mktree(repo, final_lines)


def synthesise_framework_only(
    repo: Path | str,
    *,
    source: str = "HEAD",
    target_ref: str = "refs/heads/framework-only",
    author_name: str | None = None,
    author_email: str | None = None,
    commit_message: str | None = None,
) -> SynthesisResult:
    """Synthesise / advance ``target_ref`` from ``source``.

    Composes git plumbing (``rev-parse``, ``ls-tree``, ``mktree``,
    ``commit-tree``, ``update-ref``). Idempotent: when the existing
    ``target_ref`` already points at a commit whose tree matches the
    synthesised tree AND whose parent matches the prior ``source``
    parent, no new commit is created and ``no_op`` is True.

    Parameters
    ----------
    repo:
        Path to the canonical pos-v2 git repo (working tree or bare).
    source:
        Ref or SHA to synthesise from (default ``HEAD``).
    target_ref:
        Fully-qualified ref to advance (default
        ``refs/heads/framework-only``).
    author_name / author_email:
        Override author identity in the synthesised commit. When None,
        falls back to the source commit's author.
    commit_message:
        Override commit message. When None, uses
        ``"framework-only synthesis of <source-sha-short>"`` (with the
        original source commit's subject appended on a separate line).

    Returns
    -------
    SynthesisResult
        Carries the source SHA, the synthesised SHA (== existing tip
        when no-op), the target_ref name, and the ``no_op`` flag.

    Raises
    ------
    SynthesisError
        When git plumbing fails or the source tree shape is invalid
        (empty ``framework/``, name collision between framework and
        top-level docs, etc.).
    """
    repo = Path(repo).resolve()
    if not (repo / ".git").exists() and not (repo / "HEAD").exists():
        raise SynthesisError(
            f"repo {repo!s} is not a git working tree or bare repo"
        )

    source_sha = _resolve_source_sha(repo, source)
    target_tree_sha = _build_synthetic_tree(repo, source_sha)

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
        ["update-ref", target_ref, new_commit_sha,
         parent_sha if parent_sha is not None else "0" * 40],
        cwd=repo,
    )

    return SynthesisResult(
        source_sha=source_sha,
        framework_only_sha=new_commit_sha,
        target_ref=target_ref,
        no_op=False,
    )
