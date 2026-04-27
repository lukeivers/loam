"""Per-amendment manifest schema (v1, v2) + loader.

See plan doc (amendment-22-pos-amend-cli.md) for the v1 schema rationale
and ``pos-amend-tracker-integration.md`` for the v2 ``objectives`` block.
The manifest is the formalised scope declaration for an amendment: which
components are touched, which baseline to pin to, which extra admissions
the diff window needs, where the seal narrative lands, and (v2) which
objective records the amendment authors into the workspace tracker.

T2 requires ``UnknownSchemaVersion`` surfaces explicitly when the tool
encounters an unrecognised schema version.
T3 requires missing required fields surface with the field name.

Schema v2 (per pos-amend-tracker-integration plan) adds an optional
``objectives`` block. Per plan §6 constraint 6:

- ``schema_version: 1`` MUST NOT carry an ``objectives`` block.
- ``schema_version: 2`` MUST carry an ``objectives`` block.

Mismatched cases raise ``InvalidField``. v1 manifests continue to parse
and apply unchanged (AC.D-pa.4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = 1
SUPPORTED_SCHEMA_VERSIONS = (1, 2)
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
class CleanupDirective:
    """One-shot retroactive BASELINE/SEAL_COMMIT revert for a
    rename-only component classified retrospectively (i.e. the prior
    amendment ran without the rename-only-aware bump path and bumped
    the fence anyway). Introduced in amendment #62 (D.1.5) to revert
    D.1's spurious bumps on rename-only components.

    See ``docs/rebuild/plans/d-migration-1-5.md`` AC.D.1.5.5.

    The directive's ``comp_name`` references a corresponding entry in
    the manifest's ``components:`` list — apply uses that entry's
    ``seal_test`` + ``sidecar`` paths to write the pre-bump values
    back. The seal step ALSO consults this list and SKIPS its
    standard sidecar bump for components that carry a cleanup
    directive (so the revert isn't clobbered by the seal step's
    "advance every listed component to amendment SHA" behaviour).

    v1-compatible additive optional field — pre-D.1.5 manifests omit
    this block (default empty tuple) and apply behaves byte-identically
    to pre-D.1.5.
    """

    comp_name: str
    pre_baseline: str
    pre_seal_commit: str


@dataclass(frozen=True)
class LiftedFromEntry:
    """Minimal provenance pointer for a manifest objective entry.

    Mirrors the public ``objective_tracker.LiftedFrom`` shape but is
    declared inside pos-amend so the manifest loader has no
    objective_tracker import. The registration helper translates this
    plain dataclass into the runtime ``LiftedFrom`` model when calling
    ``ObjectiveTracker.create``. Schema v2 introduction.

    ``source_commit`` is intentionally omitted from the manifest YAML —
    the seal step writes it after the fact (AC.D-pa.3 / D-build.3).
    """

    source_doc: str
    source_ac: str


@dataclass(frozen=True)
class ObjectiveEntry:
    """A single ``objectives`` block entry (schema v2).

    The shape mirrors ``ObjectiveSpec``'s authoring fields verbatim
    (D-build.1 option (a)). Acceptance criteria are carried as a list
    of plain dicts with the discriminator key ``kind``; the
    registration helper hands them to the runtime ``Criterion`` union
    for validation. Missing/invalid values surface as
    ``InvalidField`` / ``MissingField`` at parse time.
    """

    goal: str
    parent_id: str | None
    parent_root: bool
    acceptance_criteria: tuple[dict[str, Any], ...]
    time_bound: dict[str, Any]
    authored_by: str
    lifted_from: LiftedFromEntry


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
    # Schema v2 only: the ``objectives`` block, parsed into a tuple
    # of ``ObjectiveEntry``. v1 manifests carry the empty tuple. The
    # presence of entries is what the apply / seal commands key on
    # for tracker registration (AC.D-pa.1, AC.D-pa.3).
    objectives: tuple[ObjectiveEntry, ...] = ()
    # Optional retroactive cleanup directives — see ``CleanupDirective``.
    # v1-compatible additive optional field; pre-D.1.5 manifests omit
    # this block. Apply processes these AFTER the standard component
    # loop, writing pre-bump BASELINE + SEAL_COMMIT values back into
    # the named components' seal-tests + sidecars.
    cleanup_directives: tuple[CleanupDirective, ...] = ()


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


def _parse_objectives_block(
    block_raw: Any, where: str
) -> tuple[ObjectiveEntry, ...]:
    """Parse the ``objectives`` block (schema v2) into ``ObjectiveEntry``.

    Each entry must declare:

    - ``goal`` (str)
    - exactly one of ``parent_id`` (str) or ``parent_root: true`` (bool)
    - ``acceptance_criteria`` (non-empty list of mapping with ``kind``)
    - ``time_bound`` (mapping; passed through to the runtime
      ``TimeBound`` model for validation at registration time)
    - ``authored_by`` (str)
    - ``lifted_from`` (mapping with ``source_doc`` + ``source_ac``)

    Validation is structural: the runtime tracker re-validates every
    field at ``ObjectiveTracker.create`` time. We catch shape errors
    here so manifest authors get fast feedback at ``validate`` time.
    """
    if not isinstance(block_raw, list) or not block_raw:
        raise InvalidField(
            f"{where}: 'objectives' must be a non-empty list when present"
        )
    out: list[ObjectiveEntry] = []
    for idx, entry in enumerate(block_raw):
        if not isinstance(entry, dict):
            raise InvalidField(f"{where}[{idx}]: must be a mapping")
        ewhere = f"{where}[{idx}]"
        goal = _require_str(entry, "goal", ewhere)

        parent_id_raw = entry.get("parent_id")
        parent_root_raw = entry.get("parent_root", False)
        if not isinstance(parent_root_raw, bool):
            raise InvalidField(
                f"{ewhere}: 'parent_root' must be a boolean if present"
            )
        if parent_id_raw is not None and parent_root_raw:
            raise InvalidField(
                f"{ewhere}: declare exactly one of 'parent_id' or "
                "'parent_root: true', not both"
            )
        if parent_id_raw is None and not parent_root_raw:
            raise MissingField(
                f"{ewhere}: must declare either 'parent_id' (str) or "
                "'parent_root: true'"
            )
        if parent_id_raw is not None:
            if not isinstance(parent_id_raw, str) or not parent_id_raw:
                raise InvalidField(
                    f"{ewhere}: 'parent_id' must be a non-empty string"
                )

        ac_raw = entry.get("acceptance_criteria")
        if not isinstance(ac_raw, list) or not ac_raw:
            raise InvalidField(
                f"{ewhere}: 'acceptance_criteria' must be a non-empty list"
            )
        criteria: list[dict[str, Any]] = []
        for cidx, c in enumerate(ac_raw):
            if not isinstance(c, dict):
                raise InvalidField(
                    f"{ewhere}.acceptance_criteria[{cidx}]: must be a mapping"
                )
            if "kind" not in c:
                raise MissingField(
                    f"{ewhere}.acceptance_criteria[{cidx}]: 'kind' is required"
                )
            criteria.append(dict(c))

        tb_raw = entry.get("time_bound")
        if not isinstance(tb_raw, dict):
            raise InvalidField(
                f"{ewhere}: 'time_bound' must be a mapping (deadline=... "
                "or evergreen=true [+ review_cadence])"
            )

        authored_by = _require_str(entry, "authored_by", ewhere)

        lf_raw = entry.get("lifted_from")
        if not isinstance(lf_raw, dict):
            raise InvalidField(
                f"{ewhere}: 'lifted_from' is required and must be a mapping "
                "with 'source_doc' + 'source_ac'"
            )
        lf_where = f"{ewhere}.lifted_from"
        source_doc = _require_str(lf_raw, "source_doc", lf_where)
        source_ac = _require_str(lf_raw, "source_ac", lf_where)
        # ``source_commit`` is reserved — manifest authors never set it
        # at authoring time; the seal step writes it (AC.D-pa.3).
        if "source_commit" in lf_raw:
            raise InvalidField(
                f"{lf_where}: 'source_commit' is written by `pos-amend "
                "seal`; do not set it in the manifest"
            )

        out.append(
            ObjectiveEntry(
                goal=goal,
                parent_id=parent_id_raw if parent_id_raw is not None else None,
                parent_root=parent_root_raw,
                acceptance_criteria=tuple(criteria),
                time_bound=dict(tb_raw),
                authored_by=authored_by,
                lifted_from=LiftedFromEntry(
                    source_doc=source_doc, source_ac=source_ac
                ),
            )
        )
    return tuple(out)


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
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnknownSchemaVersion(
            f"{path}: unsupported schema_version {schema_version!r}; "
            f"this tool supports {SUPPORTED_SCHEMA_VERSIONS}"
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

    # Schema v2 only: parse the ``objectives`` block. The schema-version
    # gate is bidirectional (plan §6 constraint 6 / D-build.2 (a)):
    #   - v1 manifests MUST NOT carry an ``objectives`` key
    #   - v2 manifests MUST carry an ``objectives`` key
    # Mismatches reject as ``InvalidField`` — explicit beats implicit.
    objectives_raw = data.get("objectives")
    objectives: tuple[ObjectiveEntry, ...] = ()
    if schema_version == 1:
        if objectives_raw is not None:
            raise InvalidField(
                f"{path}: 'objectives' is a schema_version 2 field; "
                "either remove it or bump 'schema_version: 2'"
            )
    elif schema_version == 2:
        if objectives_raw is None:
            raise MissingField(
                f"{path}: schema_version 2 requires the 'objectives' "
                "block; either author the block or downgrade "
                "'schema_version: 1'"
            )
        objectives = _parse_objectives_block(objectives_raw, str(path))

    # Optional cleanup_directives block (D.1.5 / amendment #62).
    # v1-compatible: missing block defaults to empty tuple. Each
    # entry carries the pre-bump BASELINE + SEAL_COMMIT values for
    # a rename-only component whose prior-amendment bumps need
    # reverting.
    cleanup_directives_raw = data.get("cleanup_directives", []) or []
    if not isinstance(cleanup_directives_raw, list):
        raise InvalidField(
            f"{path}: 'cleanup_directives' must be a list when present"
        )
    cleanup_directives: list[CleanupDirective] = []
    for idx, entry in enumerate(cleanup_directives_raw):
        if not isinstance(entry, dict):
            raise InvalidField(
                f"{path}: cleanup_directives[{idx}] must be a mapping"
            )
        cwhere = f"{path}:cleanup_directives[{idx}]"
        comp_name = _require_str(entry, "comp_name", cwhere)
        pre_baseline = _require_str(entry, "pre_baseline", cwhere)
        if not _SHA_RE.match(pre_baseline):
            raise InvalidField(
                f"{cwhere}: 'pre_baseline' must be a 7-40 char "
                f"lowercase hex SHA; got {pre_baseline!r}"
            )
        pre_seal_commit = _require_str(entry, "pre_seal_commit", cwhere)
        if not _SHA_RE.match(pre_seal_commit):
            raise InvalidField(
                f"{cwhere}: 'pre_seal_commit' must be a 7-40 char "
                f"lowercase hex SHA; got {pre_seal_commit!r}"
            )
        cleanup_directives.append(
            CleanupDirective(
                comp_name=comp_name,
                pre_baseline=pre_baseline,
                pre_seal_commit=pre_seal_commit,
            )
        )

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
        objectives=objectives,
        cleanup_directives=tuple(cleanup_directives),
    )
