"""``loam amend validate`` — schema-lint a manifest."""

from __future__ import annotations

from pathlib import Path

from loam_amend.manifest import ManifestError, load_manifest


def run(manifest_path: Path) -> int:
    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        print(f"invalid: {exc}")
        return 2
    # Schema v3 makes ``amendment.number`` optional — degrade
    # gracefully so ``validate`` works for slug-only manifests.
    if manifest.number is None:
        ident = f"amendment '{manifest.slug}'"
    else:
        ident = f"amendment #{manifest.number} '{manifest.slug}'"
    print(
        f"ok: {ident} — "
        f"{len(manifest.components)} components, baseline {manifest.baseline}"
    )
    return 0
