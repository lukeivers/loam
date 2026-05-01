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

"""Contribution discovery — resolve ContributionRefs to classes.

Availability vs enablement (proposal §3.1):
  - Entry-points supply availability — installed-but-not-listed packages
    are inert; bootstrap does not iterate the full entry-point group
    and activate every member. Availability is queried lazily, once
    per listed reference.
  - The manifest supplies enablement — only listed contributions run.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .errors import (
    ContributionNotFoundError,
    MetadataInvalidError,
)
from .manifest import ContributionRef
from .spec import ContributionMetadata


_ENTRYPOINT_GROUP = "loam.bootstrap.contributions"


def resolve_ref(ref: ContributionRef) -> type[Any]:
    """Resolve a reference to a contribution class. Raises
    ContributionNotFoundError if the reference cannot be imported.
    """
    if ref.kind == "entrypoint":
        return _resolve_entrypoint(ref)
    if ref.kind == "module":
        return _resolve_module(ref)
    if ref.kind == "path":
        return _resolve_path(ref)
    raise ContributionNotFoundError(
        f"unsupported ref kind {ref.kind!r}",
        data={"ref": ref.label},
    )


def _resolve_entrypoint(ref: ContributionRef) -> type[Any]:
    assert ref.entrypoint_name is not None
    eps = importlib.metadata.entry_points(group=_ENTRYPOINT_GROUP)
    matches = [ep for ep in eps if ep.name == ref.entrypoint_name]
    if not matches:
        raise ContributionNotFoundError(
            f"no entry-point {ref.entrypoint_name!r} in group "
            f"{_ENTRYPOINT_GROUP!r}",
            data={"entrypoint": ref.entrypoint_name, "group": _ENTRYPOINT_GROUP},
        )
    ep = matches[0]
    try:
        obj = ep.load()
    except Exception as e:
        raise ContributionNotFoundError(
            f"entry-point {ref.entrypoint_name!r} failed to load: {e}",
            data={"entrypoint": ref.entrypoint_name, "error": str(e)},
        ) from e
    if not isinstance(obj, type):
        raise ContributionNotFoundError(
            f"entry-point {ref.entrypoint_name!r} did not resolve to a class; "
            f"got {type(obj).__name__}",
            data={"entrypoint": ref.entrypoint_name},
        )
    return obj


def _resolve_module(ref: ContributionRef) -> type[Any]:
    assert ref.module is not None and ref.module_attr is not None
    try:
        module = importlib.import_module(ref.module)
    except Exception as e:
        raise ContributionNotFoundError(
            f"module {ref.module!r} could not be imported: {e}",
            data={"module": ref.module, "error": str(e)},
        ) from e
    obj = getattr(module, ref.module_attr, None)
    if obj is None:
        raise ContributionNotFoundError(
            f"module {ref.module!r} has no attribute {ref.module_attr!r}",
            data={"module": ref.module, "attr": ref.module_attr},
        )
    if not isinstance(obj, type):
        raise ContributionNotFoundError(
            f"{ref.module}:{ref.module_attr} is not a class",
            data={"module": ref.module, "attr": ref.module_attr},
        )
    return obj


def _resolve_path(ref: ContributionRef) -> type[Any]:
    assert ref.path is not None and ref.path_attr is not None
    p: Path = ref.path
    if not p.exists():
        raise ContributionNotFoundError(
            f"path-form contribution file not found: {p}",
            data={"path": str(p), "attr": ref.path_attr},
        )
    # Synthesise a module name. Use a stable prefix so repeated loads
    # hit the same sys.modules entry and don't double-execute module
    # body side effects. The abs(hash(...)) is not cryptographic — it
    # is a file-identity key for sys.modules.
    mod_name = f"_pos_workspace_bootstrap_path_{abs(hash(str(p)))}"
    if mod_name in sys.modules:
        module = sys.modules[mod_name]
    else:
        spec = importlib.util.spec_from_file_location(mod_name, p)
        if spec is None or spec.loader is None:
            raise ContributionNotFoundError(
                f"could not load module spec from {p}",
                data={"path": str(p)},
            )
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            # Clean up on failure so a later re-resolution retries.
            sys.modules.pop(mod_name, None)
            raise ContributionNotFoundError(
                f"path-form contribution {p} failed to import: {e}",
                data={"path": str(p), "error": str(e)},
            ) from e
    obj = getattr(module, ref.path_attr, None)
    if obj is None:
        raise ContributionNotFoundError(
            f"file {p} has no attribute {ref.path_attr!r}",
            data={"path": str(p), "attr": ref.path_attr},
        )
    if not isinstance(obj, type):
        raise ContributionNotFoundError(
            f"{p}:{ref.path_attr} is not a class",
            data={"path": str(p), "attr": ref.path_attr},
        )
    return obj


def read_metadata(cls: type[Any], *, ref_label: str) -> ContributionMetadata:
    """Extract and validate metadata off a contribution class.

    The class must expose `metadata: ContributionMetadata` either as a
    class attribute or as an instance attribute on an arg-free instance.
    """
    md = getattr(cls, "metadata", None)
    if md is None:
        # Try constructing to get an instance attribute. Many adapters
        # use the BaseContribution pattern with metadata at class level;
        # this branch supports the alternative.
        try:
            inst = cls()
        except Exception as e:
            raise MetadataInvalidError(
                f"{ref_label}: cannot instantiate to read metadata: {e}",
                data={"ref": ref_label, "error": str(e)},
            ) from e
        md = getattr(inst, "metadata", None)
    if md is None:
        raise MetadataInvalidError(
            f"{ref_label}: contribution class must expose "
            f"`metadata: ContributionMetadata`",
            data={"ref": ref_label},
        )
    if isinstance(md, ContributionMetadata):
        return md
    # Accept a dict and validate.
    if isinstance(md, dict):
        try:
            return ContributionMetadata(**md)
        except ValidationError as e:
            raise MetadataInvalidError(
                f"{ref_label}: metadata failed validation: {e.errors()!r}",
                data={"ref": ref_label, "errors": e.errors()},
            ) from e
    raise MetadataInvalidError(
        f"{ref_label}: metadata must be a ContributionMetadata or dict; "
        f"got {type(md).__name__}",
        data={"ref": ref_label},
    )
