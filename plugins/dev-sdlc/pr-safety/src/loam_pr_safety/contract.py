"""Banded-contract reader for loam-pr-safety.

Per AC.PRGATE.1 (v0.2.3 Cycle 3) — reads the odd-extractor's
``objectives.yaml`` + ``backing-map.yaml`` directly. Legacy
``contract-draft.yaml.acs:`` retired per master plan §6.2.

Per AC.PRGATE.4 — composes any approved-override overlays at
``<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml``
on top, in sorted order. Each overlay either:

  - Replaces an original-VERIFIED-objective with a new (typically
    PLAUSIBLE) Objective row (kind=replace_verified_objective), or
  - Records audit-only state (kind=audit_only) — Cycle 3 simplification
    for novel-diff cases; v0.2.4 gap-analysis owns objective
    creation.

v1→v2 overlay migration: legacy v0.1.9 overlays
(``kind: replace_verified``, ``original_ac_id``, ``replacement_ac``)
are auto-migrated on read into the v2 shape with a ``.v1.bak``
sidecar preserved for audit. Mirrors Cycle 2's RatificationStateV2
migration pattern.

Round-trip: every Objective dict is fed through
:meth:`Objective.model_validate`; per-band evidence rules raise
``pydantic.ValidationError`` on malformed entries, wrapped into
:class:`ContractMalformedError`.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from loam_odd_extractor.backing_map import load_backing_map
from loam_odd_extractor.spec import (
    Objective,
)

from loam_pr_safety.errors import (
    ContractMalformedError,
    ContractMissingError,
)
from loam_pr_safety.spec import BandedContract
from loam_pr_safety.state import (
    extractions_dir,
    overrides_dir,
)


def _build_objective(obj_dict: dict[str, Any], idx: int) -> Objective:
    """Validate one Objective dict, wrapping ValidationError."""
    try:
        return Objective.model_validate(obj_dict)
    except ValidationError as exc:
        raise ContractMalformedError(
            f"objectives.yaml entry at index {idx} failed Objective "
            f"validation: {exc}"
        ) from exc


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ContractMalformedError(
            f"YAML file at {path!s} is not a mapping at top level."
        )
    return data


def _list_sorted_overlays(repo_overrides_dir: Path) -> list[Path]:
    """Return overlay files sorted by name (override-1, override-2, ...)."""
    if not repo_overrides_dir.exists():
        return []
    overlays = [
        p
        for p in repo_overrides_dir.iterdir()
        if p.is_file() and p.suffix == ".yaml"
    ]
    overlays.sort(key=lambda p: p.name)
    return overlays


def _migrate_v1_overlay_in_place(
    overlay_path: Path, overlay_dict: dict[str, Any]
) -> dict[str, Any] | None:
    """Detect a v0.1.9-shape overlay; back it up + migrate to v2 shape.

    Per AC.PRGATE.4 — read-time auto-migration. A v0.1.9 overlay has
    ``kind`` ∈ {``replace_verified``, ``promote_novel``} and
    ``replacement_ac`` (BandedAC dict). We can't faithfully migrate the
    BandedAC dict to an Objective dict at read-time (the altitudes
    differ structurally); we record the audit-only intent so the
    overlay still composes (no-op) and the original is preserved at
    ``<overlay>.v1.bak``.

    Returns the migrated dict (or ``None`` if no migration needed).
    """
    kind = overlay_dict.get("kind")
    if kind not in {"replace_verified", "promote_novel"}:
        return None
    # Back up the v1 overlay.
    backup = overlay_path.with_suffix(overlay_path.suffix + ".v1.bak")
    if not backup.exists():
        backup.write_text(
            yaml.safe_dump(overlay_dict, sort_keys=False),
            encoding="utf-8",
        )
    # Replace with an audit-only marker so the overlay composes as
    # a no-op against the objective-altitude contract.
    migrated = {
        "schema_version": 2,
        "kind": "audit_only",
        "rationale": (
            f"Auto-migrated from v0.1.9 overlay (kind={kind}); "
            f"original preserved at {backup.name}. Re-create the "
            f"override against the objective-altitude contract if "
            f"the original intent still applies."
        ),
        "owner": str(overlay_dict.get("owner", "")),
        "commit_sha": str(overlay_dict.get("commit_sha", "")),
        "repo_sha": str(overlay_dict.get("repo_sha", "")),
        "applied_at": str(
            overlay_dict.get("applied_at")
            or _dt.datetime.now(_dt.timezone.utc).isoformat()
        ),
        "legacy_kind": kind,
        "legacy_original_ac_id": overlay_dict.get("original_ac_id"),
    }
    overlay_path.write_text(
        yaml.safe_dump(migrated, sort_keys=False),
        encoding="utf-8",
    )
    return migrated


def _apply_overlay(
    objectives: list[Objective],
    overlay_dict: dict[str, Any],
) -> list[Objective]:
    """Apply one overlay to the Objective list.

    Overlay shape (Cycle 3):

      schema_version: 2
      kind: replace_verified_objective | audit_only
      original_objective_id: <id>            # for replace_verified_objective
      replacement_objective: <Objective dict>

    For ``replace_verified_objective``: find the objective with
    matching ``objective_id`` in ``objectives`` and replace it with
    the overlay's ``replacement_objective``.
    For ``audit_only``: no-op against the objective list (the overlay
    is preserved on disk for audit; doesn't mutate the in-memory
    contract).
    """
    kind = overlay_dict.get("kind")
    if kind == "audit_only":
        # No mutation; overlay records audit trail only.
        return objectives

    if kind != "replace_verified_objective":
        raise ContractMalformedError(
            f"Overlay 'kind' must be 'replace_verified_objective' or "
            f"'audit_only'; got {kind!r}"
        )

    replacement_dict = overlay_dict.get("replacement_objective")
    if not isinstance(replacement_dict, dict):
        raise ContractMalformedError(
            f"Overlay missing or malformed 'replacement_objective' "
            f"field (got {type(replacement_dict).__name__})"
        )
    try:
        replacement = Objective.model_validate(replacement_dict)
    except ValidationError as exc:
        raise ContractMalformedError(
            f"Overlay replacement_objective failed Objective "
            f"validation: {exc}"
        ) from exc

    original_id = overlay_dict.get("original_objective_id")
    if not isinstance(original_id, str) or not original_id:
        raise ContractMalformedError(
            "Overlay kind=replace_verified_objective requires "
            "non-empty 'original_objective_id' field."
        )
    new_objectives: list[Objective] = []
    replaced = False
    for o in objectives:
        if o.objective_id == original_id and not replaced:
            new_objectives.append(replacement)
            replaced = True
        else:
            new_objectives.append(o)
    if not replaced:
        # Treat as additive when underlying contract was re-extracted
        # and the original ID changed — preserves audit visibility
        # without losing the override.
        new_objectives.append(replacement)
    return new_objectives


def read_contract(
    repo_id: str,
    workspace_root: Path,
) -> BandedContract:
    """Read the banded contract for ``repo_id`` from
    ``workspace_root``.

    Per AC.PRGATE.1:

      1. Resolve ``<workspace_root>/.loam/extractions/<repo-id>/objectives.yaml``
         + ``<workspace_root>/.loam/extractions/<repo-id>/backing-map.yaml``.
      2. Parse + validate every Objective dict against
         :class:`Objective` (per-band evidence rules enforced).
      3. Apply overrides at
         ``<workspace_root>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml``
         in sorted order. v0.1.9 overlays are auto-migrated to v2
         shape on read.
      4. Return :class:`BandedContract`.

    Raises:

      :class:`ContractMissingError` — objectives.yaml or backing-map.yaml absent.
      :class:`ContractMalformedError` — present but malformed
        (subclass of ContractMissingError).
    """
    workspace_root = workspace_root.expanduser().resolve()
    ext_dir = extractions_dir(workspace_root, repo_id)
    objectives_path = ext_dir / "objectives.yaml"
    if not objectives_path.exists():
        raise ContractMissingError(
            f"objectives.yaml not found at {objectives_path!s}. "
            f"Run `loam odd-extract <repo>` first."
        )

    objectives_data = _load_yaml_dict(objectives_path)
    extraction_id = str(objectives_data.get("extraction_id") or repo_id)
    repo_path = Path(str(objectives_data.get("repo_path", "")))
    raw_objs = objectives_data.get("objectives") or []
    if not isinstance(raw_objs, list):
        raise ContractMalformedError(
            f"objectives.yaml 'objectives' field must be a list; got "
            f"{type(raw_objs).__name__}"
        )
    objectives: list[Objective] = []
    inferred_repo_sha: str | None = None
    for idx, obj_dict in enumerate(raw_objs):
        if not isinstance(obj_dict, dict):
            raise ContractMalformedError(
                f"objectives.yaml 'objectives[{idx}]' must be a "
                f"mapping; got {type(obj_dict).__name__}"
            )
        o = _build_objective(obj_dict, idx)
        objectives.append(o)
        if (
            inferred_repo_sha is None
            and o.evidence.repo_sha is not None
        ):
            inferred_repo_sha = o.evidence.repo_sha

    # Backing-map is REQUIRED — Cycle 2 produces it as part of
    # post-synthesis pipeline. ContractMissingError if absent.
    backing_map = load_backing_map(ext_dir)
    if backing_map is None:
        raise ContractMissingError(
            f"backing-map.yaml not found at "
            f"{ext_dir / 'backing-map.yaml'}. Cycle 2 backing-map "
            f"population is required; run `loam odd-extract <repo>` "
            f"with the synthesis pipeline (LLM-pass) to populate."
        )

    created_at = str(objectives_data.get("created_at") or _utc_now_iso())

    # Apply overlays (with v1→v2 migration on read).
    overlay_paths = _list_sorted_overlays(
        overrides_dir(workspace_root, repo_id)
    )
    override_count = 0
    for overlay_path in overlay_paths:
        overlay_data = _load_yaml_dict(overlay_path)
        # v1→v2 migration if needed.
        migrated = _migrate_v1_overlay_in_place(overlay_path, overlay_data)
        effective = migrated if migrated is not None else overlay_data
        objectives = _apply_overlay(objectives, effective)
        override_count += 1

    return BandedContract(
        extraction_id=extraction_id,
        repo_path=repo_path,
        repo_sha=inferred_repo_sha,
        objectives=objectives,
        backing_map=backing_map,
        unhandled_paths=[],
        created_at=created_at,
        override_count=override_count,
    )


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()
