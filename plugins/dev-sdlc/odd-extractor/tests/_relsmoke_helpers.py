"""Shared helpers for AC.RELSMOKE.* tests + the integration smoke."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import yaml

from loam_odd_extractor.state import compute_repo_id, extraction_dir


FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "jsts-playwright-app"
)


def setup_repo_from_fixture(tmp_path: Path) -> tuple[Path, str]:
    """Copy the canonical jsts-playwright-app fixture into a tmp git repo."""
    repo = tmp_path / "jsts-app"
    shutil.copytree(FIXTURE_PATH, repo)
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "t@e.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "T"],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "initial fixture"],
        check=True,
    )
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return (repo, proc.stdout.strip())


def write_canned_objectives_and_map(
    workspace: Path, repo_id: str, repo_sha: str
) -> None:
    """Write canned objectives.yaml + backing-map.yaml for the fixture."""
    ext_dir = extraction_dir(workspace, repo_id)
    ext_dir.mkdir(parents=True, exist_ok=True)
    objs = {
        "schema_version": 1,
        "extraction_id": repo_id,
        "repo_path": str(workspace),
        "created_at": "2026-05-04T00:00:00+00:00",
        "objectives": [
            {
                "objective_id": "O.users.1",
                "text": (
                    "Operators retrieve user records via an HTTP endpoint "
                    "and the system enforces request validation."
                ),
                "confidence": "VERIFIED",
                "domain": "users",
                "evidence": {
                    "readme_excerpts": [
                        "Express user routes under /users."
                    ],
                    "design_doc_refs": [],
                    "test_name_refs": [
                        "tests/unit/users.test.ts::user retrieval"
                    ],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": repo_sha,
                    "rationale": None,
                },
            },
            {
                "objective_id": "O.auth.1",
                "text": (
                    "Operators authenticate before accessing admin routes; "
                    "the system rejects unauthenticated callers."
                ),
                "confidence": "PLAUSIBLE",
                "domain": "auth",
                "evidence": {
                    "readme_excerpts": [
                        "Module-level admin gate via requireAuth middleware."
                    ],
                    "design_doc_refs": [],
                    "test_name_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            },
            {
                "objective_id": "O.dashboard.1",
                "text": (
                    "Authenticated operators see a dashboard page with their "
                    "session-scoped data."
                ),
                "confidence": "HYPOTHESISED",
                "domain": "dashboard",
                "evidence": {
                    "readme_excerpts": [],
                    "design_doc_refs": [],
                    "test_name_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": (
                        "Inferred from page-object dashboard-page.ts; no "
                        "explicit test asserting outcome."
                    ),
                },
            },
        ],
        "constraints": [],
        "capabilities": [],
    }
    bm = {
        "schema_version": 1,
        "extraction_id": repo_id,
        "created_at": "2026-05-04T00:00:00+00:00",
        "model_id": "stub-canned",
        "cost_actual_cents": 0.0,
        "total_evidence_rows": 3,
        "objective_count": 3,
        "unmatched_objective_ids": [],
        "entries": [
            {
                "objective_id": "O.users.1",
                "match_rationale": "Express route + unit test",
                "evidence_rows": [
                    {
                        "evidence_row_id": "route:src/routes/users.js:1-20",
                        "kind": "route",
                        "path": "src/routes/users.js",
                        "line_range": [1, 20],
                        "symbol_name": "router",
                        "language": "jsts",
                        "confidence": "STRONG",
                    }
                ],
            },
            {
                "objective_id": "O.auth.1",
                "match_rationale": "auth middleware",
                "evidence_rows": [
                    {
                        "evidence_row_id": "callback:src/middleware/auth.js:1-15",
                        "kind": "callback",
                        "path": "src/middleware/auth.js",
                        "line_range": [1, 15],
                        "symbol_name": "requireAuth",
                        "language": "jsts",
                        "confidence": "STRONG",
                    }
                ],
            },
            {
                "objective_id": "O.dashboard.1",
                "match_rationale": "page object hint",
                "evidence_rows": [],
            },
        ],
        "orphan_rows": [],
    }
    (ext_dir / "objectives.yaml").write_text(
        yaml.safe_dump(objs, sort_keys=False), encoding="utf-8"
    )
    (ext_dir / "backing-map.yaml").write_text(
        yaml.safe_dump(bm, sort_keys=False), encoding="utf-8"
    )
    (ext_dir / "contract-draft.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 2,
                "extraction_id": repo_id,
                "repo_path": str(workspace),
                "objective_count": 3,
                "constraint_count": 0,
                "capability_count": 0,
                "unhandled_count": 0,
                "dry_run": False,
                "created_at": "2026-05-04T00:00:00+00:00",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
