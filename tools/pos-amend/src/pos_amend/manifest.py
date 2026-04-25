"""Per-amendment manifest schema (v1) + loader.

See plan doc (amendment-22-pos-amend-cli.md) for the schema rationale.
The manifest is the formalised scope declaration for an amendment: which
components are touched, which baseline to pin to, which extra admissions
the diff window needs, and where the seal narrative lands.

T2 requires ``UnknownSchemaVersion`` surfaces explicitly when the tool
encounters an unrecognised schema version.
T3 requires missing required fields surface with the field name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = 1
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


class ManifestError(Exception):
    """Base class for manifest parsing/validation errors."""


class UnknownSchemaVersion(ManifestError):
    """Raised when the manifest declares an unsupported schema version."""


class MissingField(ManifestError):
    """Raised when a required field is absent."""


class InvalidField(ManifestError):
    """Raised when a field's value fails validation."""


@dataclass(frozen=True)
class ComponentEntry:
    name: str
    seal_test: str
    sidecar: str
    extra_allowed_prefixes: tuple[str, ...] = ()
    extra_allowed_files: tuple[str, ...] = ()
    # When True, ``apply`` skips the module-top ``BASELINE = "<sha>"``
    # literal bump for this component. Everything else (sidecar
    # advance, tuple widening, narrative append) still runs. Introduced
    # in amendment #23 so hands-off-lifecycle's frozen-H19 BASELINE
    # is expressible in the manifest. Backward-compatible default
    # preserves the amendment-#22 behaviour for all existing manifests.
    frozen_baseline: bool = False


@dataclass(frozen=True)
class UniversalPaths:
    prefixes: tuple[str, ...] = ()
    files: tuple[str, ...] = ()


@dataclass(frozen=True)
class NarrativeSpec:
    target: str
    body: str


@dataclass(frozen=True)
class Manifest:
    schema_version: int
    number: int
    slug: str
    title: str
    baseline: str
    plan: str
    components: tuple[ComponentEntry, ...]
    universal_paths: UniversalPaths = field(default_factory=UniversalPaths)
    narrative: NarrativeSpec | None = None
    # Optional human-readable seal description used as the
    # `<description>` slot in the deterministic seal-commit subject
    # (per AC.D-sa.2). When absent, the seal step falls back to
    # ``slug``. Backward-compatible — pre-extension manifests omit
    # the field and the slug-fallback applies. No schema-version
    # bump required.
    seal_description: str | None = None


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise MissingField(f"{where}: missing required field '{key}'")
    return mapping[key]


def _require_str(mapping: dict[str, Any], key: str, where: str) -> str:
    value = _require(mapping, key, where)
    if not isinstance(value, str) or not value:
        raise InvalidField(f"{where}: '{key}' must be a non-empty string")
    return value


def _optional_str_list(mapping: dict[str, Any], key: str, where: str) -> tuple[str, ...]:
    value = mapping.get(key, [])
    if value is None:
        return ()
    if not isinstance(value, list):
        raise InvalidField(f"{where}: '{key}' must be a list of strings")
    for item in value:
        if not isinstance(item, str):
            raise InvalidField(f"{where}: '{key}' list entries must be strings")
    return tuple(value)


def load_manifest(path: Path) -> Manifest:
    """Parse the YAML manifest at *path* and return a validated ``Manifest``.

    Raises ``UnknownSchemaVersion`` if the declared schema version is not
    supported; ``MissingField`` if a required field is absent;
    ``InvalidField`` if a value fails validation.
    """
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ManifestError(f"YAML parse error in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise InvalidField(f"{path}: top-level YAML must be a mapping")

    schema_version = data.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise UnknownSchemaVersion(
            f"{path}: unsupported schema_version {schema_version!r}; "
            f"this tool supports {SCHEMA_VERSION}"
        )

    amendment = _require(data, "amendment", str(path))
    if not isinstance(amendment, dict):
        raise InvalidField(f"{path}: 'amendment' must be a mapping")
    where = f"{path}:amendment"
    number = _require(amendment, "number", where)
    if not isinstance(number, int):
        raise InvalidField(f"{where}: 'number' must be an integer")
    slug = _require_str(amendment, "slug", where)
    title = _require_str(amendment, "title", where)

    baseline = _require_str(data, "baseline", str(path))
    if not _SHA_RE.match(baseline):
        raise InvalidField(
            f"{path}: 'baseline' must be a 7-40 char lowercase hex SHA; got {baseline!r}"
        )

    plan = _require_str(data, "plan", str(path))

    components_raw = _require(data, "components", str(path))
    if not isinstance(components_raw, list) or not components_raw:
        raise InvalidField(f"{path}: 'components' must be a non-empty list")
    components: list[ComponentEntry] = []
    for idx, entry in enumerate(components_raw):
        if not isinstance(entry, dict):
            raise InvalidField(f"{path}: components[{idx}] must be a mapping")
        where = f"{path}:components[{idx}]"
        frozen_raw = entry.get("frozen_baseline", False)
        if not isinstance(frozen_raw, bool):
            raise InvalidField(
                f"{where}: 'frozen_baseline' must be a boolean if present"
            )
        components.append(
            ComponentEntry(
                name=_require_str(entry, "name", where),
                seal_test=_require_str(entry, "seal_test", where),
                sidecar=_require_str(entry, "sidecar", where),
                extra_allowed_prefixes=_optional_str_list(
                    entry, "extra_allowed_prefixes", where
                ),
                extra_allowed_files=_optional_str_list(
                    entry, "extra_allowed_files", where
                ),
                frozen_baseline=frozen_raw,
            )
        )

    universal_raw = data.get("universal_paths", {}) or {}
    if not isinstance(universal_raw, dict):
        raise InvalidField(f"{path}: 'universal_paths' must be a mapping if present")
    universal = UniversalPaths(
        prefixes=_optional_str_list(universal_raw, "prefixes", f"{path}:universal_paths"),
        files=_optional_str_list(universal_raw, "files", f"{path}:universal_paths"),
    )

    narrative: NarrativeSpec | None = None
    narrative_raw = data.get("narrative")
    if narrative_raw is not None:
        if not isinstance(narrative_raw, dict):
            raise InvalidField(f"{path}: 'narrative' must be a mapping if present")
        where = f"{path}:narrative"
        narrative = NarrativeSpec(
            target=_require_str(narrative_raw, "target", where),
            body=_require_str(narrative_raw, "body", where),
        )

    seal_description_raw = data.get("seal_description")
    seal_description: str | None = None
    if seal_description_raw is not None:
        if not isinstance(seal_description_raw, str) or not seal_description_raw:
            raise InvalidField(
                f"{path}: 'seal_description' must be a non-empty string if present"
            )
        seal_description = seal_description_raw

    return Manifest(
        schema_version=schema_version,
        number=number,
        slug=slug,
        title=title,
        baseline=baseline,
        plan=plan,
        components=tuple(components),
        universal_paths=universal,
        narrative=narrative,
        seal_description=seal_description,
    )
