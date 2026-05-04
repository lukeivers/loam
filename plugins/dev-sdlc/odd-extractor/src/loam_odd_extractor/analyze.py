"""Stage 2 — analyze.

Per AC.OREK.3 — input :class:`ExtractionConfig` → output
:class:`AnalysisPlan` written to
``<workspace>/.loam/extractions/<repo-id>/plan.yaml``.

Walks the repo via :class:`pathlib.Path` recursion. Each file is
classified by its extension hint, then offered to each registered
language adapter's :meth:`LanguageAdapter.supports` predicate. Files
that no adapter supports go into :attr:`AnalysisPlan.unhandled_paths`.
Cycle 1 ships zero adapters → every file lands in unhandled_paths.

Hidden directories (``.git``, ``.loam``, ``.scratch``, ``.venv``,
``__pycache__``, etc.) are skipped to avoid extracting against
metadata. The skip list is intentionally minimal — a real repo
walk needs ``.gitignore`` parsing in Cycles 3+4.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import yaml

from .observability import write_audit_entry
from .registry import discover_adapters
from .spec import AnalysisPlan, ExtractionConfig, Slice
from .state import extraction_dir, load_state, save_state


_SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".loam",
        ".scratch",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        "node_modules",
        "build",
        "dist",
        ".eggs",
    }
)


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _walk_repo(repo_path: Path) -> list[Path]:
    """Yield every regular file under ``repo_path``, skipping hidden +
    dependency directories.

    Returns absolute paths sorted lexicographically for deterministic
    ordering across runs (D2 idempotency).
    """
    out: list[Path] = []
    if not repo_path.exists():
        return out
    if repo_path.is_file():
        return [repo_path]

    def _recurse(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir(), key=lambda p: p.name)
        except (OSError, PermissionError):
            return
        for entry in entries:
            if entry.is_dir():
                if entry.name in _SKIP_DIR_NAMES:
                    continue
                if entry.name.startswith(".") and entry.name not in {".github"}:
                    continue
                _recurse(entry)
            elif entry.is_file():
                out.append(entry)

    _recurse(repo_path)
    return out


def analyze_repo(
    *,
    config: ExtractionConfig,
    timestamp: str | None = None,
) -> AnalysisPlan:
    """Run Stage 2 — analyze.

    Returns :class:`AnalysisPlan`; writes ``plan.yaml`` artefact;
    appends a ``stage_complete`` audit-log entry; updates
    ``state.yaml``.

    ``timestamp`` is injectable for deterministic tests.
    """
    ext_dir = extraction_dir(config.workspace_root, config.repo_id)
    ts = timestamp if timestamp is not None else _now_iso()

    files = _walk_repo(config.repo_path)
    adapters = discover_adapters()

    slices: list[Slice] = []
    unhandled: list[Path] = []
    if not adapters:
        # Cycle 1 path — every file is unhandled.
        unhandled = files
    else:
        # Cycles 3+4 path — partition files among adapters.
        # An adapter "claims" the repo if its supports() returns
        # True; per Cycle 1, the adapter is offered the repo
        # root (per-file dispatch is a Cycle-3 refinement).
        for adapter in adapters:
            try:
                claimed = bool(adapter.supports(config.repo_path))
            except Exception:
                claimed = False
            if claimed:
                slices.append(
                    Slice(
                        slice_id=f"{adapter.name}-root",
                        adapter_name=adapter.name,
                        paths=files,
                    )
                )
                # Cycle 1's contract: an adapter that claims gets
                # ALL files; subsequent adapters see nothing. Cycle 3
                # tightens this to per-file routing.
                files = []
                break
        unhandled = files

    plan = AnalysisPlan(
        extraction_id=config.repo_id,
        slices=slices,
        unhandled_paths=unhandled,
        created_at=ts,
    )

    plan_path = ext_dir / "plan.yaml"
    plan_payload = plan.model_dump(mode="json")
    plan_path.write_text(
        yaml.safe_dump(plan_payload, sort_keys=False),
        encoding="utf-8",
    )

    state = load_state(ext_dir)
    if state is None:
        # Should not happen — init must have run before analyze. Be
        # defensive: synthesize state rather than crash.
        from .state import ExtractionState

        state = ExtractionState(
            extraction_id=config.repo_id,
            repo_path=str(config.repo_path),
            workspace_root=str(config.workspace_root),
            init_complete=True,
        )
    state.analyze_complete = True
    state.last_updated_at = ts
    state.artefacts["plan"] = plan_path.relative_to(ext_dir).as_posix()
    save_state(ext_dir, state)

    write_audit_entry(
        ext_dir,
        event_kind="stage_complete",
        extraction_id=config.repo_id,
        stage="analyze",
        artefact_path=plan_path.relative_to(ext_dir).as_posix(),
        notes=(
            f"slices={len(slices)} unhandled={len(unhandled)} "
            f"adapters={len(adapters)}"
        ),
        timestamp=ts,
    )

    return plan
