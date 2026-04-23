"""``pos-amend seal`` — advance sidecars to HEAD + append narrative."""

from __future__ import annotations

import subprocess
from pathlib import Path

from pos_amend.manifest import ManifestError, load_manifest
from pos_amend.narrative import append_narrative
from pos_amend.paths import find_repo_root
from pos_amend.sidecar import write_sidecar


def _head_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def run(manifest_path: Path) -> int:
    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        print(f"invalid manifest: {exc}")
        return 2
    try:
        repo_root = find_repo_root(manifest_path.parent)
    except RuntimeError as exc:
        print(f"repo error: {exc}")
        return 3
    sha = _head_sha(repo_root)
    changes: list[str] = []
    for comp in manifest.components:
        sidecar_path = repo_root / comp.sidecar
        if write_sidecar(sidecar_path, sha):
            changes.append(f"{comp.name}: SEAL_COMMIT → {sha}")
    if manifest.narrative is not None:
        target = repo_root / manifest.narrative.target
        if append_narrative(target, manifest.narrative.body):
            changes.append(f"narrative appended to {manifest.narrative.target}")
    if not changes:
        print("no changes (idempotent re-seal)")
    else:
        print("sealed:")
        for c in changes:
            print(f"  - {c}")
    return 0
