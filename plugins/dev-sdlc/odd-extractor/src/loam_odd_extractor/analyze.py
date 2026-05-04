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


# Per Cycle 3 plan-doc Surface #6 — language-hint routing table.
# Initial mapping; later cycles extend (Cycle 4 adds Python; modern
# Rails apps with .js / .ts / .haml are RF gap §10 #3).
_LANGUAGE_HINTS: dict[str, frozenset[str]] = {
    "ruby": frozenset(
        {".rb", ".rake", ".gemspec"}
    ),
    "python": frozenset(
        {".py"}
    ),
}
_LANGUAGE_HINT_NAMES: dict[str, frozenset[str]] = {
    "ruby": frozenset(
        {"Rakefile", "Gemfile", "config.ru"}
    ),
}


def _adapter_handles_file(adapter, file_path: Path) -> bool:
    """Return True if ``adapter`` claims ``file_path`` per the
    language-hint table.

    The check is a pure-Python lookup; adapters can override by
    declaring a ``handles_file(path: Path) -> bool`` method (Cycle 4+
    extension hook). Cycle 3 uses the static table.
    """
    # Adapter-supplied hook overrides the static table.
    handles_file = getattr(adapter, "handles_file", None)
    if callable(handles_file):
        try:
            return bool(handles_file(file_path))
        except Exception:
            return False

    suffixes = _LANGUAGE_HINTS.get(adapter.name, frozenset())
    if file_path.suffix in suffixes:
        return True
    names = _LANGUAGE_HINT_NAMES.get(adapter.name, frozenset())
    if file_path.name in names:
        return True
    return False


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
        # Cycle 3 (per-file routing): partition files among adapters
        # by language hint. Per v0-1-8-cycle-3 plan-doc Surface #6 —
        # the all-or-nothing claim model from Cycle 1 is replaced by
        # per-file dispatch so multi-adapter repos (e.g., Rails app
        # with a Python data-science script under tools/) don't
        # collapse onto the first adapter that supports() the repo.
        #
        # Routing rule: each adapter sees the repo root via
        # supports(); for adapters that claim the repo, files are
        # routed by the language hint table (file extension /
        # filename). Files matching no claiming adapter's hint land
        # in unhandled_paths.
        claiming_adapters = []
        for adapter in adapters:
            try:
                claimed = bool(adapter.supports(config.repo_path))
            except Exception:
                claimed = False
            if claimed:
                claiming_adapters.append(adapter)

        if not claiming_adapters:
            unhandled = files
        else:
            adapter_files: dict[str, list[Path]] = {
                a.name: [] for a in claiming_adapters
            }
            for f in files:
                routed = False
                for adapter in claiming_adapters:
                    if _adapter_handles_file(adapter, f):
                        adapter_files[adapter.name].append(f)
                        routed = True
                        break
                if not routed:
                    unhandled.append(f)

            for adapter in claiming_adapters:
                claimed_files = adapter_files[adapter.name]
                if claimed_files:
                    slices.append(
                        Slice(
                            slice_id=f"{adapter.name}-root",
                            adapter_name=adapter.name,
                            paths=claimed_files,
                        )
                    )

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
