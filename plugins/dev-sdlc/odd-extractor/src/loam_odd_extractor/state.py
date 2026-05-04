"""Workspace-scoped extraction state.

Per Surface #4 (plan-doc §5) — every extraction has its own
``<workspace>/.loam/extractions/<repo-id>/`` directory, with a
``state.yaml`` snapshotting the run's status across the four stages.

Per AC.OREK.7 (D5 cross-session) — the state.yaml file IS the
cross-session continuity surface: a fresh process reads it and
either resumes (if mid-run) or reports complete (if all four
stages have artefacts).

State schema is intentionally minimal in Cycle 1 — the per-slice
status fields named in ODD-RE research §3.4 land when adapters do
in Cycles 3+4. Cycle 1 tracks one boolean per stage.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ---- repo-id derivation --------------------------------------------


def compute_repo_id(repo_path: Path) -> str:
    """Derive a deterministic id for ``repo_path``.

    Format: ``<basename>-<8-char-sha256-hex>``. Same absolute path
    always produces the same id; different absolute paths produce
    different ids (per Surface #5 — collision-resistant within
    reasonable workspace sizes; human-readable prefix).

    The basename is sanitised — non-alphanumeric / non-dash / non-
    underscore characters become ``_``. Empty basename (e.g.,
    ``/``) becomes ``root``.
    """
    abs_path = repo_path.expanduser().resolve()
    basename = abs_path.name or "root"
    safe_basename = "".join(
        c if (c.isalnum() or c in "-_") else "_" for c in basename
    )
    digest = hashlib.sha256(str(abs_path).encode("utf-8")).hexdigest()
    return f"{safe_basename}-{digest[:8]}"


# ---- extraction directory ------------------------------------------


def extraction_dir(workspace_root: Path, repo_id: str) -> Path:
    """Return the per-extraction directory under the workspace.

    ``<workspace_root>/.loam/extractions/<repo-id>/``. Caller is
    responsible for creating it if absent.
    """
    return (
        workspace_root.expanduser().resolve()
        / ".loam"
        / "extractions"
        / repo_id
    )


# ---- ExtractionState ------------------------------------------------


@dataclass
class ExtractionState:
    """Per-extraction state snapshot.

    Stored at ``<extraction_dir>/state.yaml``. Cross-session
    continuity (D5) reads this; resume reads this.
    """

    schema_version: int = 1
    extraction_id: str = ""
    repo_path: str = ""
    workspace_root: str = ""
    init_complete: bool = False
    analyze_complete: bool = False
    generate_complete: bool = False
    verify_complete: bool = False
    last_updated_at: str = ""
    notes: str = ""
    # Per-stage artefact paths recorded for resume / status.
    artefacts: dict[str, str] = field(default_factory=dict)

    def to_yaml_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "extraction_id": self.extraction_id,
            "repo_path": self.repo_path,
            "workspace_root": self.workspace_root,
            "init_complete": self.init_complete,
            "analyze_complete": self.analyze_complete,
            "generate_complete": self.generate_complete,
            "verify_complete": self.verify_complete,
            "last_updated_at": self.last_updated_at,
            "notes": self.notes,
            "artefacts": dict(self.artefacts),
        }

    @classmethod
    def from_yaml_dict(cls, data: dict[str, Any]) -> "ExtractionState":
        return cls(
            schema_version=int(data.get("schema_version", 1)),
            extraction_id=str(data.get("extraction_id", "")),
            repo_path=str(data.get("repo_path", "")),
            workspace_root=str(data.get("workspace_root", "")),
            init_complete=bool(data.get("init_complete", False)),
            analyze_complete=bool(data.get("analyze_complete", False)),
            generate_complete=bool(data.get("generate_complete", False)),
            verify_complete=bool(data.get("verify_complete", False)),
            last_updated_at=str(data.get("last_updated_at", "")),
            notes=str(data.get("notes", "")),
            artefacts=dict(data.get("artefacts") or {}),
        )

    @property
    def all_stages_complete(self) -> bool:
        return (
            self.init_complete
            and self.analyze_complete
            and self.generate_complete
            and self.verify_complete
        )


# ---- state.yaml IO -------------------------------------------------


def state_path(extraction_dir_: Path) -> Path:
    return extraction_dir_ / "state.yaml"


def load_state(extraction_dir_: Path) -> ExtractionState | None:
    """Read ``state.yaml`` from ``extraction_dir_``.

    Returns the parsed :class:`ExtractionState` if the file exists,
    else ``None``. Missing state.yaml means "no prior extraction" —
    the caller initialises a fresh state.
    """
    sp = state_path(extraction_dir_)
    if not sp.exists():
        return None
    text = sp.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    return ExtractionState.from_yaml_dict(data)


def save_state(extraction_dir_: Path, state: ExtractionState) -> None:
    """Write ``state`` to ``state.yaml``.

    Creates ``extraction_dir_`` if needed. Atomic write via
    ``write_text`` (overwrites).
    """
    extraction_dir_.mkdir(parents=True, exist_ok=True)
    sp = state_path(extraction_dir_)
    sp.write_text(
        yaml.safe_dump(state.to_yaml_dict(), sort_keys=False),
        encoding="utf-8",
    )
