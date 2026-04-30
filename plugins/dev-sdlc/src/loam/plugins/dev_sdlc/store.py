"""Per-project state in workspace-local SQLite.

Per plan §4 AC.OSS-M6.2 + §10 D-build.M6.8: SQLite at
`<workspace>/.loam/dev-sdlc.sqlite` is the single source of truth;
`<project>/.dev-sdlc.yaml` is a derived human-readable mirror.

Schema:

  projects(
    slug TEXT PRIMARY KEY,
    methodology TEXT NOT NULL,
    current_stage TEXT NOT NULL,
    project_scope_id TEXT,
    project_objective_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )

  stage_history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug TEXT NOT NULL REFERENCES projects(slug),
    from_stage TEXT,
    to_stage TEXT NOT NULL,
    advanced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )

WAL mode is enabled (per plan §8 risk #4 mitigation). Concurrency
is not a v0.1.0 concern — the plugin is invoked synchronously from
the persona's tool-call path.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


DEFAULT_DB_DIR = ".loam"
DEFAULT_DB_NAME = "dev-sdlc.sqlite"


def db_path(workspace_root: Path) -> Path:
    """Return the canonical SQLite path for *workspace_root* (per
    plan §1 capability #8)."""
    return workspace_root / DEFAULT_DB_DIR / DEFAULT_DB_NAME


@dataclass(frozen=True)
class ProjectRow:
    """One row of the `projects` table."""

    slug: str
    methodology: str
    current_stage: str
    project_scope_id: str | None
    project_objective_id: str | None


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
          slug TEXT PRIMARY KEY,
          methodology TEXT NOT NULL,
          current_stage TEXT NOT NULL,
          project_scope_id TEXT,
          project_objective_id TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stage_history (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          project_slug TEXT NOT NULL REFERENCES projects(slug),
          from_stage TEXT,
          to_stage TEXT NOT NULL,
          advanced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()


@contextmanager
def open_store(workspace_root: Path) -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection against the workspace's dev-sdlc
    store. Creates the parent directory + applies schema on first
    open.

    Caller is responsible for committing — the context manager closes
    the connection but does NOT auto-commit.
    """
    path = db_path(workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_schema(conn)
        yield conn
    finally:
        conn.close()


def insert_project(
    conn: sqlite3.Connection,
    *,
    slug: str,
    methodology: str,
    current_stage: str,
    project_scope_id: str | None = None,
    project_objective_id: str | None = None,
) -> None:
    """Insert a new project row. Caller commits."""
    conn.execute(
        """
        INSERT INTO projects(
          slug, methodology, current_stage,
          project_scope_id, project_objective_id
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            slug,
            methodology,
            current_stage,
            project_scope_id,
            project_objective_id,
        ),
    )


def get_project(
    conn: sqlite3.Connection, slug: str
) -> ProjectRow | None:
    """Return the project row for *slug*, or None when absent."""
    row = conn.execute(
        "SELECT slug, methodology, current_stage, "
        "project_scope_id, project_objective_id "
        "FROM projects WHERE slug = ?",
        (slug,),
    ).fetchone()
    if row is None:
        return None
    return ProjectRow(
        slug=row["slug"],
        methodology=row["methodology"],
        current_stage=row["current_stage"],
        project_scope_id=row["project_scope_id"],
        project_objective_id=row["project_objective_id"],
    )


def list_all_projects(conn: sqlite3.Connection) -> list[ProjectRow]:
    """Return every project row, ordered by created_at ascending."""
    out: list[ProjectRow] = []
    for row in conn.execute(
        "SELECT slug, methodology, current_stage, "
        "project_scope_id, project_objective_id "
        "FROM projects ORDER BY created_at ASC, slug ASC"
    ):
        out.append(
            ProjectRow(
                slug=row["slug"],
                methodology=row["methodology"],
                current_stage=row["current_stage"],
                project_scope_id=row["project_scope_id"],
                project_objective_id=row["project_objective_id"],
            )
        )
    return out


def advance_project_stage(
    conn: sqlite3.Connection,
    *,
    slug: str,
    from_stage: str,
    to_stage: str,
) -> None:
    """Update the project's current_stage + append a stage_history
    row. Caller commits."""
    conn.execute(
        "UPDATE projects SET current_stage = ? WHERE slug = ?",
        (to_stage, slug),
    )
    conn.execute(
        "INSERT INTO stage_history(project_slug, from_stage, to_stage) "
        "VALUES (?, ?, ?)",
        (slug, from_stage, to_stage),
    )


def project_history(
    conn: sqlite3.Connection, slug: str
) -> list[tuple[str | None, str]]:
    """Return [(from_stage, to_stage), ...] in chronological order."""
    out: list[tuple[str | None, str]] = []
    for row in conn.execute(
        "SELECT from_stage, to_stage FROM stage_history "
        "WHERE project_slug = ? ORDER BY id ASC",
        (slug,),
    ):
        out.append((row["from_stage"], row["to_stage"]))
    return out
