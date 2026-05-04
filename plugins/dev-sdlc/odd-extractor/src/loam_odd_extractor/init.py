"""Stage 1 — init.

Per AC.OREK.3 — input ``(repo_path, budget, workspace_root, dry_run)``
→ output :class:`ExtractionConfig` written to
``<workspace>/.loam/extractions/<repo-id>/config.yaml``.

Pure function: no global state; takes its inputs and returns the
config + writes the config.yaml side-effect at a deterministic path.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import yaml

from loam.cost_governance import BudgetEnvelope

from .observability import write_audit_entry
from .spec import ExtractionConfig
from .state import compute_repo_id, extraction_dir, load_state, save_state, ExtractionState


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def init_extraction(
    *,
    repo_path: Path,
    workspace_root: Path,
    budget: BudgetEnvelope,
    dry_run: bool,
    timestamp: str | None = None,
) -> ExtractionConfig:
    """Run Stage 1 — init.

    Side effects:

    1. Create ``<workspace>/.loam/extractions/<repo-id>/`` if absent.
    2. Write ``config.yaml`` (the :class:`ExtractionConfig` artefact).
    3. Initialise (or update) ``state.yaml`` with
       ``init_complete = True``.
    4. Append an ``extraction_start`` audit-log entry (if this is the
       first stage of the run) AND a ``stage_complete`` entry for
       ``init``.

    Returns the :class:`ExtractionConfig` for downstream stages /
    test inspection.

    ``timestamp`` is injectable for deterministic tests; defaults to
    ``_now_iso()``.
    """
    abs_repo = repo_path.expanduser().resolve()
    abs_workspace = workspace_root.expanduser().resolve()
    repo_id = compute_repo_id(abs_repo)
    ext_dir = extraction_dir(abs_workspace, repo_id)
    ext_dir.mkdir(parents=True, exist_ok=True)

    ts = timestamp if timestamp is not None else _now_iso()

    config = ExtractionConfig(
        repo_path=abs_repo,
        repo_id=repo_id,
        workspace_root=abs_workspace,
        budget=budget,
        dry_run=dry_run,
        created_at=ts,
    )

    config_path = ext_dir / "config.yaml"
    config_payload = config.model_dump(mode="json")
    config_path.write_text(
        yaml.safe_dump(config_payload, sort_keys=False),
        encoding="utf-8",
    )

    # State + audit-log bookkeeping. If state.yaml is absent or this
    # is a fresh run, write extraction_start. Otherwise this is a
    # resume / re-run; just record the stage completion.
    prior_state = load_state(ext_dir)
    is_fresh_run = prior_state is None
    if is_fresh_run:
        write_audit_entry(
            ext_dir,
            event_kind="extraction_start",
            extraction_id=repo_id,
            notes=f"dry_run={dry_run}",
            timestamp=ts,
        )
        state = ExtractionState(
            extraction_id=repo_id,
            repo_path=str(abs_repo),
            workspace_root=str(abs_workspace),
            last_updated_at=ts,
        )
    else:
        state = prior_state

    state.init_complete = True
    state.last_updated_at = ts
    state.artefacts["config"] = config_path.relative_to(ext_dir).as_posix()
    save_state(ext_dir, state)

    write_audit_entry(
        ext_dir,
        event_kind="stage_complete",
        extraction_id=repo_id,
        stage="init",
        artefact_path=config_path.relative_to(ext_dir).as_posix(),
        notes="",
        timestamp=ts,
    )

    return config
