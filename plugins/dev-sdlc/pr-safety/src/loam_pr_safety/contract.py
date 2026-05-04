"""Banded-contract reader for loam-pr-safety.

Per AC.PRSG.2 — reads the odd-extractor's
``<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml``
sidecar and reconstructs a typed :class:`BandedContract`.

Per Surface #4 (plan-doc §5) — composes any approved-override
overlays at
``<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml``
on top, in sorted order. Each overlay replaces an
original-VERIFIED-AC's BandedAC entry with a new (potentially
different-band) entry, or extends the contract with a promoted novel
candidate.

Round-trip: every ``ac`` dict in the sidecar is fed through
:meth:`BandedAC.model_validate`; the per-band evidence rules from
``loam_odd_extractor.bands`` raise :class:`pydantic.ValidationError`
on any malformed entry, which is wrapped into
:class:`ContractMalformedError`.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from loam_odd_extractor.bands import BandedAC

from loam_pr_safety.errors import (
    ContractMalformedError,
    ContractMissingError,
)
from loam_pr_safety.spec import BandedContract
from loam_pr_safety.state import (
    extractions_dir,
    overrides_dir,
)


def _build_bandedac(ac_dict: dict[str, Any], idx: int) -> BandedAC:
    """Validate one banded-AC dict, wrapping ValidationError."""
    try:
        return BandedAC.model_validate(ac_dict)
    except ValidationError as exc:
        raise ContractMalformedError(
            f"Contract sidecar AC at index {idx} failed banded-AC "
            f"validation: {exc}"
        ) from exc


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ContractMalformedError(
            f"Sidecar at {path!s} is not a YAML mapping at top level."
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


def _apply_overlay(
    acs: list[BandedAC],
    overlay_dict: dict[str, Any],
) -> list[BandedAC]:
    """Apply one overlay to the AC list.

    Overlay shape (Surface #4):

      schema_version: 1
      kind: replace_verified | promote_novel
      original_ac_id: <id|null>      # for replace_verified
      replacement_ac: <BandedAC dict>

    For ``replace_verified``: find the AC with matching ``ac_id`` in
    ``acs`` and replace it with the overlay's ``replacement_ac``.
    For ``promote_novel``: append the overlay's ``replacement_ac``.

    Per AC.PRSG.5 — the replacement AC goes through BandedAC
    validation (per-band evidence rules enforced).
    """
    kind = overlay_dict.get("kind")
    replacement_dict = overlay_dict.get("replacement_ac")
    if not isinstance(replacement_dict, dict):
        raise ContractMalformedError(
            f"Overlay missing or malformed 'replacement_ac' field "
            f"(got {type(replacement_dict).__name__})"
        )
    try:
        replacement = BandedAC.model_validate(replacement_dict)
    except ValidationError as exc:
        raise ContractMalformedError(
            f"Overlay replacement_ac failed banded-AC validation: {exc}"
        ) from exc

    if kind == "replace_verified":
        original_id = overlay_dict.get("original_ac_id")
        if not isinstance(original_id, str) or not original_id:
            raise ContractMalformedError(
                "Overlay kind=replace_verified requires non-empty "
                "'original_ac_id' field."
            )
        new_acs: list[BandedAC] = []
        replaced = False
        for ac in acs:
            if ac.ac_id == original_id and not replaced:
                new_acs.append(replacement)
                replaced = True
            else:
                new_acs.append(ac)
        if not replaced:
            # The overlay references an AC that doesn't exist; treat
            # as a promote (additive) rather than failing — this can
            # happen when the underlying contract is re-extracted
            # and the original AC's id changed.
            new_acs.append(replacement)
        return new_acs

    if kind == "promote_novel":
        return [*acs, replacement]

    raise ContractMalformedError(
        f"Overlay 'kind' must be 'replace_verified' or 'promote_novel'; "
        f"got {kind!r}"
    )


def read_contract(
    repo_id: str,
    workspace_root: Path,
) -> BandedContract:
    """Read the banded contract for ``repo_id`` from
    ``workspace_root``.

    Per AC.PRSG.2:

      1. Resolve the odd-extractor's contract-draft.yaml at
         ``<workspace_root>/.loam/extractions/<repo-id>/contract-draft.yaml``.
      2. Parse + validate every AC dict against
         :class:`BandedAC` (per-band evidence rules enforced).
      3. Apply any overrides at
         ``<workspace_root>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml``
         in sorted order.
      4. Return :class:`BandedContract`.

    Raises:

      :class:`ContractMissingError` — sidecar absent.
      :class:`ContractMalformedError` — sidecar present but
        malformed (subclass of ContractMissingError).
    """
    workspace_root = workspace_root.expanduser().resolve()
    sidecar = (
        extractions_dir(workspace_root, repo_id) / "contract-draft.yaml"
    )
    if not sidecar.exists():
        raise ContractMissingError(
            f"Contract sidecar not found at {sidecar!s}. Run "
            f"`loam odd-extract <repo>` first."
        )

    sidecar_data = _load_yaml_dict(sidecar)

    extraction_id = str(sidecar_data.get("extraction_id") or repo_id)
    repo_path = Path(str(sidecar_data.get("repo_path", "")))
    raw_acs = sidecar_data.get("acs") or []
    if not isinstance(raw_acs, list):
        raise ContractMalformedError(
            f"Sidecar 'acs' field must be a list; got "
            f"{type(raw_acs).__name__}"
        )
    acs: list[BandedAC] = []
    inferred_repo_sha: str | None = None
    for idx, ac_dict in enumerate(raw_acs):
        if not isinstance(ac_dict, dict):
            raise ContractMalformedError(
                f"Sidecar 'acs[{idx}]' must be a mapping; got "
                f"{type(ac_dict).__name__}"
            )
        ac = _build_bandedac(ac_dict, idx)
        acs.append(ac)
        if (
            inferred_repo_sha is None
            and ac.evidence.repo_sha is not None
        ):
            inferred_repo_sha = ac.evidence.repo_sha

    unhandled_paths_raw = sidecar_data.get("unhandled_paths") or []
    unhandled_paths: list[Path] = []
    if isinstance(unhandled_paths_raw, list):
        for p in unhandled_paths_raw:
            unhandled_paths.append(Path(str(p)))

    created_at = str(sidecar_data.get("created_at") or _utc_now_iso())

    # Apply overlays.
    overlay_paths = _list_sorted_overlays(
        overrides_dir(workspace_root, repo_id)
    )
    override_count = 0
    for overlay_path in overlay_paths:
        overlay_data = _load_yaml_dict(overlay_path)
        acs = _apply_overlay(acs, overlay_data)
        override_count += 1

    return BandedContract(
        extraction_id=extraction_id,
        repo_path=repo_path,
        repo_sha=inferred_repo_sha,
        acs=acs,
        unhandled_paths=unhandled_paths,
        created_at=created_at,
        override_count=override_count,
    )


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()
