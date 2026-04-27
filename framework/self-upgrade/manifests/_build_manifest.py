"""One-shot scaffold to materialise pos-v2-v0.2.0.yaml.

Run from canonical root::

    .venv/bin/python self-upgrade/manifests/_build_manifest.py

Enumerates every ``*.py`` file under each sealed component's ``src/``
directory, marks each as ``change_kind=new`` (initial release: no
prior installed sha to compare against), computes sha256, and writes
the manifest at ``self-upgrade/manifests/pos-v2-v0.2.0.yaml``.

Initial-release rationale: ``pos-v2-v0.2.0`` is the FIRST tagged
release; no v0.1.0 was ever installed, so every framework file is
``new`` from the upgrade machinery's point of view. ``expected_pre_sha``
must be ``None`` and ``expected_post_sha`` must be the canonical sha.

Framework-code scope: framework code = python sources under each
sealed component's ``src/`` directory. Tests, docs, plans, scripts,
seals/, templates/ are NOT installed by the upgrade swap and are
therefore out-of-manifest. ``tools/`` is also out-of-scope (tools
are workspace-side; merge-resolver-module + pos-amend live there).
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_CANONICAL = _HERE.parent.parent

# Insert self-upgrade src so we can import manifest helpers.
sys.path.insert(0, str(_CANONICAL / "self-upgrade" / "src"))

from self_upgrade.manifest import (  # noqa: E402
    ChangeKind,
    FileEntry,
    Manifest,
    save_manifest,
    sha256_of_file,
)


SEALED_COMPONENTS = (
    "cost-governance",
    "graceful-degradation",
    "hands-off-lifecycle",
    "memory-system",
    "objective-tracker",
    "observability-aggregator",
    "orchestrator",
    "primary-persona",
    "reversibility-primitive",
    "safety-layer",
    "scope-of-work",
    "self-correction",
    "self-upgrade",
    "telegram-interface",
    "workspace-bootstrap",
)


def main() -> int:
    head_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=_CANONICAL, text=True
    ).strip()

    files: list[FileEntry] = []
    for component in SEALED_COMPONENTS:
        src_root = _CANONICAL / component / "src"
        if not src_root.exists():
            continue
        for py_file in sorted(src_root.rglob("*.py")):
            rel = py_file.relative_to(_CANONICAL)
            files.append(
                FileEntry(
                    path=str(rel),
                    expected_pre_sha=None,
                    expected_post_sha=sha256_of_file(py_file),
                    change_kind=ChangeKind.NEW,
                )
            )

    manifest = Manifest(
        release_tag="pos-v2-v0.2.0",
        commit_sha=head_sha,
        files=files,
        component_schemas=[],
        breaking_changes=[],
        migrations=[],
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    target = _HERE / "pos-v2-v0.2.0.yaml"
    save_manifest(manifest, target)
    print(f"wrote {target}")
    print(f"  release_tag:  {manifest.release_tag}")
    print(f"  commit_sha:   {manifest.commit_sha}")
    print(f"  files:        {len(manifest.files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
