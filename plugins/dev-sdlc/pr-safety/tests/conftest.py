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


# ====================================================================
# v0.2.3 Cycle 3 — objective-altitude fixtures
# ====================================================================


@pytest.fixture
def synthetic_objectives_dict() -> dict[str, Any]:
    """A 3-objective banded contract — VERIFIED + PLAUSIBLE + HYPOTHESISED.

    Per AC.PRGATE.1 — at objective altitude. Mirrors the rebuild's
    Objective + multi-source evidence shape.
    """
    return {
        "schema_version": 1,
        "extraction_id": "synth-cycle-3-test",
        "repo_path": "/synthetic/test-repo",
        "created_at": "2026-05-04T00:00:00+00:00",
        "objectives": [
            {
                "objective_id": "O.auth.1",
                "text": (
                    "Operators authenticate against the system with "
                    "password-length validation enforced."
                ),
                "confidence": "VERIFIED",
                "domain": "auth",
                "evidence": {
                    "readme_excerpts": [
                        "Auth supports password length >= 8."
                    ],
                    "design_doc_refs": [],
                    "test_name_refs": [
                        "tests/test_auth.py::test_password_length"
                    ],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": "abc1234567890def",
                    "rationale": None,
                },
            },
            {
                "objective_id": "O.orders.1",
                "text": (
                    "Operators place orders with line items that cascade-"
                    "delete on order removal."
                ),
                "confidence": "PLAUSIBLE",
                "domain": "orders",
                "evidence": {
                    "readme_excerpts": [],
                    "design_doc_refs": [
                        "docs/orders.md#cascade-delete"
                    ],
                    "test_name_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            },
            {
                "objective_id": "O.payments.1",
                "text": (
                    "Operators retry failed charges with exponential "
                    "backoff; reliability target inferred from comments."
                ),
                "confidence": "HYPOTHESISED",
                "domain": "payments",
                "evidence": {
                    "readme_excerpts": [],
                    "design_doc_refs": [],
                    "test_name_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": (
                        "Inferred from a comment in the payment "
                        "integration; no application-level retry "
                        "code visible."
                    ),
                },
            },
        ],
        "constraints": [],
        "capabilities": [],
    }


@pytest.fixture
def synthetic_backing_map_dict() -> dict[str, Any]:
    """A backing-map covering the 3 synthetic objectives.

    Per AC.PRGATE.1 — Cycle 2 :class:`BackingMap` shape.
    """
    return {
        "schema_version": 1,
        "extraction_id": "synth-cycle-3-test",
        "created_at": "2026-05-04T00:00:00+00:00",
        "model_id": "stub-test",
        "cost_actual_cents": 0.0,
        "total_evidence_rows": 3,
        "objective_count": 3,
        "unmatched_objective_ids": [],
        "entries": [
            {
                "objective_id": "O.auth.1",
                "match_rationale": "test asserts password length",
                "evidence_rows": [
                    {
                        "evidence_row_id": "test:tests/test_auth.py:42-58",
                        "kind": "test",
                        "path": "tests/test_auth.py",
                        "line_range": [42, 58],
                        "symbol_name": "test_password_length",
                        "language": "python",
                        "confidence": "STRONG",
                    },
                    {
                        "evidence_row_id": "route:app/auth.py:10-25",
                        "kind": "route",
                        "path": "app/auth.py",
                        "line_range": [10, 25],
                        "symbol_name": "validate_password",
                        "language": "python",
                        "confidence": "STRONG",
                    },
                ],
            },
            {
                "objective_id": "O.orders.1",
                "match_rationale": "model has-many cascade-delete",
                "evidence_rows": [
                    {
                        "evidence_row_id": "model:app/models/order.rb:12-25",
                        "kind": "model",
                        "path": "app/models/order.rb",
                        "line_range": [12, 25],
                        "symbol_name": "Order",
                        "language": "ruby",
                        "confidence": "STRONG",
                    },
                ],
            },
            {
                "objective_id": "O.payments.1",
                "match_rationale": "(none — HYPOTHESISED)",
                "evidence_rows": [],
            },
        ],
        "orphan_rows": [],
    }


@pytest.fixture
def workspace_with_objectives(
    tmp_workspace: Path,
    synthetic_objectives_dict: dict[str, Any],
    synthetic_backing_map_dict: dict[str, Any],
) -> tuple[Path, str]:
    """Place objectives.yaml + backing-map.yaml under
    ``.loam/extractions/<repo-id>/``. Returns
    ``(workspace_root, repo_id)``.

    Per AC.PRGATE.1 — Cycle 3 source layout.
    """
    repo_id = "synth-cycle-3-test"
    ext_dir = tmp_workspace / ".loam" / "extractions" / repo_id
    ext_dir.mkdir(parents=True)
    (ext_dir / "objectives.yaml").write_text(
        yaml.safe_dump(synthetic_objectives_dict, sort_keys=False),
        encoding="utf-8",
    )
    (ext_dir / "backing-map.yaml").write_text(
        yaml.safe_dump(synthetic_backing_map_dict, sort_keys=False),
        encoding="utf-8",
    )
    # Top-level summary file (Cycle 3 shape).
    (ext_dir / "contract-draft.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 2,
                "extraction_id": repo_id,
                "repo_path": "/synthetic/test-repo",
                "ac_count": 3,
                "objective_count": 3,
                "constraint_count": 0,
                "capability_count": 0,
                "unhandled_count": 0,
                "dry_run": True,
                "created_at": "2026-05-04T00:00:00+00:00",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return (tmp_workspace, repo_id)


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
