"""``pos-amend validate`` — schema-lint a manifest."""

from __future__ import annotations

from pathlib import Path

from pos_amend.manifest import ManifestError, load_manifest


def run(manifest_path: Path) -> int:
    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        print(f"invalid: {exc}")
        return 2
    print(
        f"ok: amendment #{manifest.number} '{manifest.slug}' — "
        f"{len(manifest.components)} components, baseline {manifest.baseline}"
    )
    return 0
