# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Workspace manifest loader.

`bootstrap.yaml` format (v1):

    version: 1
    config_dir: ~/.loam/config          # optional; default = workspace_root/config
    workspace_root: ~/.my-workspace    # optional; default = parent of manifest
    contributions:
      - observability_aggregator       # name → entry-point group lookup
      - name: custom_adapter           # workspace-local escape hatch
        path: ./adapters/my_adapter.py
        attr: MyContribution           # class attribute name in file
      - name: remote_package
        module: my_pkg.bootstrap_adapter
        attr: MyContribution           # dotted module import

Three entry forms per list item:

  1. Bare string — looked up in the `loam.bootstrap.contributions`
     entry-point group. Installed-but-not-listed packages are inert.

  2. Dict with `path` + `attr` — workspace-local file. `path` is
     relative to the manifest's parent directory (absolute paths also
     accepted).

  3. Dict with `module` + `attr` — dotted module import. Not all
     Phase 4+ components need to register an entry-point; `module`
     allows direct reference even if the package didn't declare one.

In all three forms, the resolved object is a `Contribution` class
(a class, not an instance). The framework instantiates it and reads
`ContributionMetadata` off it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

import yaml

from .errors import (
    ContributionNotFoundError,
    MissingConfigError,
)


@dataclass(frozen=True)
class ContributionRef:
    """A reference to a contribution as listed in the manifest.

    Exactly one of `entrypoint_name`, `path_attr`, or `module_attr` is
    set. The loader resolves the reference to a `Contribution` class.
    """

    kind: str  # "entrypoint" | "path" | "module"
    entrypoint_name: str | None = None
    path: Path | None = None
    path_attr: str | None = None
    module: str | None = None
    module_attr: str | None = None
    display_name: str | None = None  # for diagnostics

    @property
    def label(self) -> str:
        return self.display_name or (
            self.entrypoint_name
            or (self.path and f"{self.path}:{self.path_attr}")
            or f"{self.module}:{self.module_attr}"
            or "<unresolved>"
        )


@dataclass(frozen=True)
class Manifest:
    version: int
    config_dir: Path
    workspace_root: Path
    manifest_path: Path
    refs: tuple[ContributionRef, ...]


def load_manifest(manifest_path: Union[str, Path]) -> Manifest:
    """Load and validate `bootstrap.yaml`. Raises MissingConfigError
    on any missing/parse/schema error — fail-closed per brief §4.
    """
    p = Path(manifest_path).expanduser()
    if not p.exists():
        raise MissingConfigError(
            f"bootstrap manifest not found at {p}",
            data={"path": str(p)},
        )
    try:
        raw = yaml.safe_load(p.read_text())
    except yaml.YAMLError as e:
        raise MissingConfigError(
            f"bootstrap manifest parse error at {p}: {e}",
            data={"path": str(p), "parse_error": str(e)},
        ) from e

    if not isinstance(raw, dict):
        raise MissingConfigError(
            f"bootstrap manifest at {p} must be a YAML mapping; got "
            f"{type(raw).__name__}",
            data={"path": str(p)},
        )

    version = raw.get("version")
    if version != 1:
        raise MissingConfigError(
            f"bootstrap manifest at {p} must declare version: 1; got {version!r}",
            data={"path": str(p), "version": version},
        )

    workspace_root = _resolve_path(raw.get("workspace_root"), default=p.parent)
    config_dir = _resolve_path(
        raw.get("config_dir"), default=workspace_root / "config"
    )

    contributions = raw.get("contributions")
    if not isinstance(contributions, list):
        raise MissingConfigError(
            f"bootstrap manifest at {p} must declare a 'contributions' list",
            data={"path": str(p)},
        )

    refs: list[ContributionRef] = []
    for idx, entry in enumerate(contributions):
        ref = _parse_entry(entry, idx, manifest_parent=p.parent)
        refs.append(ref)

    return Manifest(
        version=version,
        config_dir=config_dir,
        workspace_root=workspace_root,
        manifest_path=p,
        refs=tuple(refs),
    )


def _resolve_path(value: Any, *, default: Path) -> Path:
    if value is None:
        return Path(default).expanduser().resolve()
    return Path(str(value)).expanduser().resolve()


def _parse_entry(
    entry: Any, idx: int, *, manifest_parent: Path
) -> ContributionRef:
    if isinstance(entry, str):
        return ContributionRef(
            kind="entrypoint",
            entrypoint_name=entry,
            display_name=entry,
        )
    if not isinstance(entry, dict):
        raise MissingConfigError(
            f"contributions[{idx}] must be a string or mapping; "
            f"got {type(entry).__name__}",
            data={"index": idx},
        )

    name_for_display = entry.get("name")

    if "path" in entry:
        attr = entry.get("attr")
        if not isinstance(attr, str) or not attr:
            raise MissingConfigError(
                f"contributions[{idx}] path-form entry must declare "
                f"'attr' (the Contribution class name)",
                data={"index": idx, "entry": entry},
            )
        raw_path = str(entry["path"])
        p = Path(raw_path).expanduser()
        if not p.is_absolute():
            p = (manifest_parent / p).resolve()
        return ContributionRef(
            kind="path",
            path=p,
            path_attr=attr,
            display_name=name_for_display or f"{p}:{attr}",
        )

    if "module" in entry:
        attr = entry.get("attr")
        if not isinstance(attr, str) or not attr:
            raise MissingConfigError(
                f"contributions[{idx}] module-form entry must declare "
                f"'attr' (the Contribution class name)",
                data={"index": idx, "entry": entry},
            )
        module = str(entry["module"])
        return ContributionRef(
            kind="module",
            module=module,
            module_attr=attr,
            display_name=name_for_display or f"{module}:{attr}",
        )

    if "entrypoint" in entry:
        return ContributionRef(
            kind="entrypoint",
            entrypoint_name=str(entry["entrypoint"]),
            display_name=name_for_display or str(entry["entrypoint"]),
        )

    raise MissingConfigError(
        f"contributions[{idx}] must specify one of "
        f"'path+attr', 'module+attr', or 'entrypoint'",
        data={"index": idx, "entry": entry},
    )
