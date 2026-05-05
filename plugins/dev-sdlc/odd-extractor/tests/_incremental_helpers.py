"""Shared helpers for v0.2.0 Cycle 1 incremental-mode tests.

Authors: factory functions for synthetic banded ACs + repo-states +
prior-contract sidecars. Tests build their fixtures programmatically
rather than from on-disk YAML so each test is self-contained +
deterministic.
"""

from __future__ import annotations

import datetime as _dt
import os
import subprocess
from pathlib import Path

import yaml

from loam_odd_extractor.bands import (
    BandedAC,
    ConfidenceBand,
    Evidence,
)
from loam_odd_extractor.state import compute_repo_id, extraction_dir


# ---- AC factories ---------------------------------------------------


def make_plausible_ac(
    *,
    ac_id: str,
    backing_files: list[str],
    citations: list[str] | None = None,
    text: str = "Plausible AC",
) -> BandedAC:
    return BandedAC(
        ac_id=ac_id,
        text=text,
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(
            kind="source",
            citations=citations or [f"{backing_files[0]}:1-10"],
            repo_sha=None,
        ),
        backing_files=backing_files,
    )


def make_verified_ac(
    *,
    ac_id: str,
    backing_files: list[str],
    citations: list[str],
    repo_sha: str = "abc1234567890def",
    text: str = "Verified AC",
) -> BandedAC:
    return BandedAC(
        ac_id=ac_id,
        text=text,
        confidence=ConfidenceBand.VERIFIED,
        evidence=Evidence(
            kind="test",
            citations=citations,
            repo_sha=repo_sha,
        ),
        backing_files=backing_files,
    )


def make_hypothesised_ac(
    *,
    ac_id: str,
    backing_files: list[str],
    rationale: str = "inferred",
    text: str = "Hypothesised AC",
) -> BandedAC:
    return BandedAC(
        ac_id=ac_id,
        text=text,
        confidence=ConfidenceBand.HYPOTHESISED,
        evidence=Evidence(
            kind="inference",
            citations=[],
            rationale=rationale,
        ),
        backing_files=backing_files,
    )


# ---- Repo + workspace setup ----------------------------------------


def init_git_repo(repo_path: Path, *, files: dict[str, str]) -> str:
    """Create a tmp git repo at `repo_path` with `files` contents.
    Returns the SHA of the initial commit.

    `files` is a mapping {relative_path: content_str}. The function
    creates each file (with parent dirs), `git init`, sets author
    info via env vars, `git add .`, and `git commit -m initial`.
    """
    repo_path.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        full = repo_path / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
        env=env,
    )
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return out.stdout.strip()


def commit_changes(
    repo_path: Path, *, files: dict[str, str | None], message: str = "edit"
) -> str:
    """Modify or delete files in an existing git repo + commit.

    `files` mapping: value=None deletes the file; value=str writes it.
    Returns the SHA of the new HEAD commit.
    """
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    for rel, content in files.items():
        full = repo_path / rel
        if content is None:
            if full.exists():
                full.unlink()
        else:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")
    subprocess.run(
        ["git", "add", "-A"],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
        env=env,
    )
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return out.stdout.strip()


# ---- Workspace + prior-contract setup ------------------------------


def write_prior_contract(
    *,
    workspace_root: Path,
    repo_path: Path,
    acs: list[BandedAC],
    created_at: str | None = None,
) -> Path:
    """Write a prior contract sidecar at the canonical path.

    Returns the sidecar path.
    """
    repo_id = compute_repo_id(repo_path)
    ext_dir = extraction_dir(workspace_root, repo_id)
    ext_dir.mkdir(parents=True, exist_ok=True)
    sidecar_path = ext_dir / "contract-draft.yaml"
    payload = {
        "schema_version": 1,
        "extraction_id": repo_id,
        "repo_path": str(repo_path),
        "ac_count": len(acs),
        "unhandled_count": 0,
        "dry_run": True,
        "created_at": (
            created_at
            or _dt.datetime(
                2026, 4, 1, tzinfo=_dt.timezone.utc
            ).isoformat()
        ),
        "acs": [ac.model_dump(mode="json") for ac in acs],
    }
    sidecar_path.write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    return sidecar_path


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


# ---- Stub PMRuntime for tests --------------------------------------


class StubPMRuntime:
    """Minimal in-memory stub of `PMRuntime.enqueue_decision`.

    Avoids the v0.1.7 PM contract YAML requirements for unit tests
    that only need to verify enqueue + provenance ordering.
    Implements just enough of the PMRuntime surface that
    `enqueue_incremental_proposals` exercises.
    """

    def __init__(self, pm_dir: Path) -> None:
        self._pm_dir = pm_dir
        self._pm_dir.mkdir(parents=True, exist_ok=True)
        self.calls: list[tuple[str, str]] = []
        self._queue_path = self._pm_dir / "decision-queue.yaml"

    def enqueue_decision(
        self, question_text: str, *, provenance: str | None = None
    ) -> int:
        self.calls.append((question_text, provenance or ""))
        # Mirror real PM's persistence so duplicate-skip detection
        # in incremental_ratify reads it.
        existing: list[dict] = []
        if self._queue_path.exists():
            payload = (
                yaml.safe_load(
                    self._queue_path.read_text(encoding="utf-8")
                )
                or {}
            )
            existing = list(payload.get("queue") or [])
        existing.append(
            {
                "text": question_text,
                "provenance": provenance,
                "enqueued_at": now_iso(),
            }
        )
        self._queue_path.write_text(
            yaml.safe_dump(
                {"schema_version": 1, "queue": existing},
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return len(existing)
