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

"""D1 — release-tag + manifest format.

Every pOS-v2 release ships a `pos-release.yml` manifest that declares:

- ``release_tag``: human-readable tag (``pos-v2-vX.Y.Z``)
- ``commit_sha``: git commit the release was tagged on
- ``files``: every framework file with expected pre- and post-upgrade
  sha256 and a ``change_kind`` enum
- ``component_schemas``: per-component pre/post schema versions
- ``breaking_changes``: explicit list (empty means no breaking changes)
- ``migrations``: ordered list of migration steps

The schema is Pydantic-validated; malformed manifests reject with
clear errors. YAML ↔ Python is a lossless round-trip via
:func:`load_manifest` and :func:`save_manifest`.

Clause (g) substrate: the ``files`` list is what the post-install
sha-verify pass checks against. A file in the installed tree that is
not in the manifest, or whose sha does not match, is a clause (g)
failure. There is no "skipped" path.

Clause (e) substrate: if any entry in ``component_schemas`` has
``version_post != version_pre`` and ``breaking_changes`` is empty,
clause (e) halts — schema bumps must be declared.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---- enums ----------------------------------------------------------


class ChangeKind(str, Enum):
    """How a file differs between prior and new release."""

    NEW = "new"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


# ---- field models ---------------------------------------------------


class FileEntry(BaseModel):
    """One framework file tracked across an upgrade.

    ``expected_pre_sha`` is ``None`` for a file newly introduced by
    this release (change_kind=new). ``expected_post_sha`` is ``None``
    for a file being removed (change_kind=deleted). The validator
    enforces the change_kind ↔ sha-presence consistency.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    expected_pre_sha: str | None = None
    expected_post_sha: str | None = None
    change_kind: ChangeKind

    @model_validator(mode="after")
    def _check_consistency(self) -> "FileEntry":
        ck = self.change_kind
        if ck is ChangeKind.NEW:
            if self.expected_pre_sha is not None:
                raise ValueError(
                    f"{self.path}: change_kind=new requires expected_pre_sha=None"
                )
            if self.expected_post_sha is None:
                raise ValueError(
                    f"{self.path}: change_kind=new requires expected_post_sha"
                )
        elif ck is ChangeKind.DELETED:
            if self.expected_post_sha is not None:
                raise ValueError(
                    f"{self.path}: change_kind=deleted requires expected_post_sha=None"
                )
            if self.expected_pre_sha is None:
                raise ValueError(
                    f"{self.path}: change_kind=deleted requires expected_pre_sha"
                )
        elif ck is ChangeKind.MODIFIED:
            if not (self.expected_pre_sha and self.expected_post_sha):
                raise ValueError(
                    f"{self.path}: change_kind=modified requires both sha fields"
                )
            if self.expected_pre_sha == self.expected_post_sha:
                raise ValueError(
                    f"{self.path}: change_kind=modified requires differing shas"
                )
        elif ck is ChangeKind.UNCHANGED:
            if not (self.expected_pre_sha and self.expected_post_sha):
                raise ValueError(
                    f"{self.path}: change_kind=unchanged requires both sha fields"
                )
            if self.expected_pre_sha != self.expected_post_sha:
                raise ValueError(
                    f"{self.path}: change_kind=unchanged requires matching shas"
                )
        return self

    @field_validator("expected_pre_sha", "expected_post_sha")
    @classmethod
    def _sha_shape(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if len(v) != 64 or any(c not in "0123456789abcdef" for c in v):
            raise ValueError(f"not a sha256 hex: {v!r}")
        return v


class ComponentSchema(BaseModel):
    """Per-component pre/post schema version for clause (e)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    component: str
    version_pre: int
    version_post: int

    @field_validator("version_pre", "version_post")
    @classmethod
    def _nonneg(cls, v: int) -> int:
        if v < 0:
            raise ValueError("schema versions must be non-negative")
        return v


class BreakingChange(BaseModel):
    """A declared breaking change with its named migration path."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    component: str
    description: str
    migration_path: str


class Migration(BaseModel):
    """Ordered migration step the framework runs pre-restart.

    ``entry`` is a ``package.module:callable`` reference the framework
    resolves via stdlib import discipline. The callable runs under a
    no-arg invocation and raises on failure.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    component: str
    order: int
    entry: str
    description: str = ""


# ---- top-level manifest ---------------------------------------------


class Manifest(BaseModel):
    """Root of `pos-release.yml`."""

    model_config = ConfigDict(extra="forbid")

    release_tag: str
    commit_sha: str
    files: list[FileEntry] = Field(default_factory=list)
    component_schemas: list[ComponentSchema] = Field(default_factory=list)
    breaking_changes: list[BreakingChange] = Field(default_factory=list)
    migrations: list[Migration] = Field(default_factory=list)
    generated_at: str | None = None

    @field_validator("release_tag")
    @classmethod
    def _tag_shape(cls, v: str) -> str:
        if not v.startswith("pos-v2-v"):
            raise ValueError(
                f"release_tag must start with 'pos-v2-v', got {v!r}"
            )
        return v

    @field_validator("commit_sha")
    @classmethod
    def _commit_shape(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) < 7 or any(c not in "0123456789abcdef" for c in v):
            raise ValueError(f"commit_sha looks wrong: {v!r}")
        return v

    @model_validator(mode="after")
    def _check_migration_order(self) -> "Manifest":
        seen: set[int] = set()
        for m in self.migrations:
            if m.order in seen:
                raise ValueError(
                    f"duplicate migration order {m.order} (ids must be unique)"
                )
            seen.add(m.order)
        return self

    def as_yaml(self) -> str:
        """Serialise to YAML preserving field order per schema."""
        return yaml.safe_dump(
            self.model_dump(mode="json"),
            default_flow_style=False,
            sort_keys=False,
        )

    def file_by_path(self, path: str) -> FileEntry | None:
        for f in self.files:
            if f.path == path:
                return f
        return None

    def schema_for(self, component: str) -> ComponentSchema | None:
        for s in self.component_schemas:
            if s.component == component:
                return s
        return None

    def has_breaking_for(self, component: str) -> bool:
        return any(bc.component == component for bc in self.breaking_changes)

    def silent_schema_bumps(self) -> list[str]:
        """Clause (e) substrate: components whose schema bumped without
        a declared breaking change.
        """
        out: list[str] = []
        for s in self.component_schemas:
            if s.version_post != s.version_pre and not self.has_breaking_for(
                s.component
            ):
                out.append(s.component)
        return out


# ---- round-trip helpers ---------------------------------------------


def load_manifest(path: str | Path) -> Manifest:
    """Read and validate a manifest YAML file."""
    p = Path(path)
    raw = yaml.safe_load(p.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{p}: top-level must be a mapping")
    return Manifest.model_validate(raw)


def save_manifest(manifest: Manifest, path: str | Path) -> None:
    """Write a manifest to YAML."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(manifest.as_yaml())


# ---- sha utilities --------------------------------------------------


def sha256_of_file(path: str | Path) -> str:
    """Stream sha256 over a file — stable across runs, memory-bounded."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def verify_file_against(entry: FileEntry, root: Path) -> tuple[bool, str | None]:
    """Return (matches, actual_sha). Expected means post-sha for
    anything except ``DELETED`` entries (which must be absent).
    """
    target = root / entry.path
    if entry.change_kind is ChangeKind.DELETED:
        return (not target.exists(), None)
    if not target.exists():
        return (False, None)
    actual = sha256_of_file(target)
    expected = entry.expected_post_sha
    return (actual == expected, actual)
