"""Shared fixtures for loam-pr-safety tests."""

from __future__ import annotations

import datetime as _dt
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Return a fresh tmp workspace root with `.loam/` initialised."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / ".loam").mkdir()
    return ws


@pytest.fixture
def synthetic_contract_dict() -> dict[str, Any]:
    """A 3-AC banded contract — VERIFIED + PLAUSIBLE + HYPOTHESISED.

    Mirrors the odd-extractor's existing
    ``tests/fixtures/synthetic-banded-contract.yaml`` shape.
    """
    return {
        "schema_version": 1,
        "extraction_id": "synthetic-prsafety-v0-1-9-c1",
        "repo_path": "/synthetic/test-repo",
        "ac_count": 3,
        "unhandled_count": 0,
        "dry_run": True,
        "created_at": "2026-05-04T00:00:00+00:00",
        "acs": [
            {
                "ac_id": "AC.SYNTH.1",
                "text": (
                    "User authentication validates password length >= 8."
                ),
                "confidence": "VERIFIED",
                "evidence": {
                    "kind": "test",
                    "citations": [
                        "tests/test_auth.py::test_password_length",
                        "app/auth.py:42-58",
                    ],
                    "repo_sha": "abc1234567890def",
                    "rationale": None,
                },
                "backing_files": [
                    "app/auth.py",
                    "tests/test_auth.py",
                ],
            },
            {
                "ac_id": "AC.SYNTH.2",
                "text": (
                    "Order has-many LineItems with cascade-delete."
                ),
                "confidence": "PLAUSIBLE",
                "evidence": {
                    "kind": "source",
                    "citations": [
                        "app/models/order.rb:12-25",
                    ],
                    "repo_sha": None,
                    "rationale": None,
                },
                "backing_files": [
                    "app/models/order.rb",
                ],
            },
            {
                "ac_id": "AC.SYNTH.3",
                "text": (
                    "Payment gateway retries failed charges 3x with "
                    "exponential backoff."
                ),
                "confidence": "HYPOTHESISED",
                "evidence": {
                    "kind": "inference",
                    "citations": [],
                    "repo_sha": None,
                    "rationale": (
                        "Inferred from a comment in the Stripe "
                        "integration; no application-level retry "
                        "code visible."
                    ),
                },
                "backing_files": [
                    "app/services/payments.rb",
                ],
            },
        ],
    }


@pytest.fixture
def workspace_with_contract(
    tmp_workspace: Path,
    synthetic_contract_dict: dict[str, Any],
) -> tuple[Path, str]:
    """Place the synthetic contract under the workspace's
    `.loam/extractions/<repo-id>/contract-draft.yaml`. Returns
    `(workspace_root, repo_id)`.
    """
    repo_id = "synth-test-repo-12345678"
    ext_dir = tmp_workspace / ".loam" / "extractions" / repo_id
    ext_dir.mkdir(parents=True)
    sidecar = ext_dir / "contract-draft.yaml"
    sidecar.write_text(
        yaml.safe_dump(synthetic_contract_dict, sort_keys=False),
        encoding="utf-8",
    )
    # Also write a stub contract-draft.md so the directory looks
    # complete.
    (ext_dir / "contract-draft.md").write_text(
        "# Synthetic contract for tests\n", encoding="utf-8"
    )
    return (tmp_workspace, repo_id)


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create an empty initialised git repo at a tmp path with a
    starter commit. Returns the repo path.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "-C", str(repo), "init", "-q"], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email",
         "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Test User"],
        check=True,
    )
    # Starter commit so git has a HEAD.
    (repo / "README.md").write_text("# repo\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repo), "add", "README.md"], check=True
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "commit",
            "-q",
            "-m",
            "initial",
        ],
        check=True,
    )
    return repo


def _add_file(repo: Path, rel_path: str, content: str) -> None:
    p = repo / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repo), "add", rel_path], check=True
    )


def _commit(repo: Path, message: str) -> str:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "commit",
            "-q",
            "-m",
            message,
        ],
        check=True,
    )
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "HEAD",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


@pytest.fixture
def make_repo_commit(tmp_git_repo: Path):
    """Convenience factory — make a commit modifying given files.

    Usage:
      sha = make_repo_commit(
          {"app/auth.py": "def f():\n    return 'long enough now'\n"},
          "fix: tighten password validation",
      )
    """

    def _factory(
        files: dict[str, str], message: str
    ) -> str:
        for rel_path, content in files.items():
            _add_file(tmp_git_repo, rel_path, content)
        return _commit(tmp_git_repo, message)

    return _factory


@pytest.fixture
def workspace_with_contract_and_repo(
    workspace_with_contract: tuple[Path, str],
    tmp_path: Path,
) -> tuple[Path, str, Path]:
    """Workspace + contract + a fresh git repo at the contract's
    repo-id'd path. Returns ``(workspace_root, repo_id, repo_path)``.

    The repo is initialised with a starter commit; tests can then
    introduce diffs via :func:`make_repo_commit`-style helpers.
    """
    workspace_root, repo_id = workspace_with_contract
    repo_path = tmp_path / "test-target-repo"
    repo_path.mkdir()
    subprocess.run(
        ["git", "-C", str(repo_path), "init", "-q", "-b", "main"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "config",
            "user.email",
            "test@example.com",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "config",
            "user.name",
            "Test User",
        ],
        check=True,
    )
    (repo_path / "README.md").write_text(
        "# test-target-repo\n", encoding="utf-8"
    )
    subprocess.run(
        ["git", "-C", str(repo_path), "add", "README.md"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "commit",
            "-q",
            "-m",
            "initial",
        ],
        check=True,
    )
    return (workspace_root, repo_id, repo_path)


@pytest.fixture
def repo_with_husky(tmp_path: Path) -> Path:
    """Create a tmp repo with husky v6+ runner-file present."""
    repo = tmp_path / "husky-repo"
    repo.mkdir()
    subprocess.run(
        ["git", "-C", str(repo), "init", "-q"], check=True
    )
    husky_dir = repo / ".husky" / "_"
    husky_dir.mkdir(parents=True)
    (husky_dir / "husky.sh").write_text(
        "# husky runner shim\n", encoding="utf-8"
    )
    return repo


@pytest.fixture
def repo_with_husky_via_pkgjson(tmp_path: Path) -> Path:
    """Create a tmp repo with husky v4-v5 config via package.json."""
    repo = tmp_path / "husky-pkgjson-repo"
    repo.mkdir()
    subprocess.run(
        ["git", "-C", str(repo), "init", "-q"], check=True
    )
    pkg = {
        "name": "test-pkg",
        "version": "1.0.0",
        "husky": {
            "hooks": {"pre-commit": "echo from husky"}
        },
    }
    import json as _json
    (repo / "package.json").write_text(
        _json.dumps(pkg, indent=2), encoding="utf-8"
    )
    return repo


@pytest.fixture
def fixed_clock(monkeypatch):
    """Freeze ``datetime.datetime.now(tz)`` to a fixed timestamp.

    Returns the frozen dt object so tests can derive expected
    timestamps deterministically.
    """
    frozen = _dt.datetime(2026, 5, 4, 12, 0, 0, tzinfo=_dt.timezone.utc)

    class _FrozenDateTime(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return frozen.replace(tzinfo=None)
            return frozen.astimezone(tz)

    # Targeted monkeypatch — only affects modules that import
    # datetime.datetime.now via the same path. The pr-safety modules
    # import via `import datetime as _dt; _dt.datetime.now(...)` so we
    # need to patch the module-level reference.
    import loam_pr_safety.audit as audit_mod
    import loam_pr_safety.contract as contract_mod
    import loam_pr_safety.override as override_mod

    monkeypatch.setattr(audit_mod._dt, "datetime", _FrozenDateTime)
    monkeypatch.setattr(contract_mod._dt, "datetime", _FrozenDateTime)
    monkeypatch.setattr(override_mod._dt, "datetime", _FrozenDateTime)
    return frozen
