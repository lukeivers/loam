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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Reader for the machine-read principle-manifest
(``docs/design/principle-manifest.yaml``).

AC.PFSE.1 names a code-side artefact a checker can ENUMERATE the
frame-rules (FR.1 / FR.2 / FR.3) + M5 from — not prose. This module is
that reader: it parses the manifest into typed rows and exposes the
enumeration + the cross-checks the coverage guard
(``test_AC_PFSE_1_principle_manifest.py``) asserts.

This is the manifest analog of ``primitive_check_matchers`` (the
matcher-data side of the dispatch-time guard): the manifest is the
single declaration surface, this reader is the typed view of it, and
the coverage guard makes manifest <-> derivation-map drift observable.

The fire path of the dev-sdlc manifest-checker (the guard sibling) and
the TEST-time coverage guard both consume this reader. The reader makes
NO network/LLM call; it reads two repo-local files (the manifest YAML +
the derivation-map markdown) deterministically.

Stdlib + PyYAML (already a dev-sdlc test dependency). Falls back to a
minimal hand-parser only if PyYAML is unavailable, so a system-Python
invocation still resolves the rows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


# The repo-relative paths the reader binds to.
PRINCIPLE_MANIFEST_PATH = "docs/design/principle-manifest.yaml"
DERIVATION_MAP_PATH = "docs/design/principle-derivation-map.md"

# The frame-rule ids AC.PFSE.1 requires present as rows.
REQUIRED_FRAME_RULE_IDS: tuple[str, ...] = ("FR.1", "FR.2", "FR.3")

# The cross-cutting id AC.PFSE.1 + AC.PFSE.2 require present.
REQUIRED_M5_ID = "M5"

# The legal enforcement values.
ENFORCEMENT_VALUES: frozenset[str] = frozenset(
    {"enforced", "advisory", "partial"}
)


@dataclass(frozen=True)
class PrincipleRow:
    """One declared principle / frame-rule row.

    ``id`` is the stable short id (FR.1 / M5 / a scope-slug).
    ``enforcement`` is one of ENFORCEMENT_VALUES. ``memory_basename`` is
    the ``feedback_*.md`` corpus file (or None for frame-rule tiers).
    ``section`` names which manifest block the row came from
    (``frame_rules`` / ``principles`` / ``enforced_primitives``).
    """

    id: str
    name: str
    memory_basename: str | None
    doc: str | None
    enforcement: str
    mechanism: str
    f4_relationship: str
    ac: str | None
    section: str


class ManifestError(ValueError):
    """Raised when the manifest is structurally invalid (a row missing a
    required key, an unknown enforcement value, a required id absent)."""


def _load_yaml(text: str) -> dict:
    """Parse the manifest text. Prefer PyYAML; fall back to a minimal
    block parser sufficient for this file's flat-list-of-mappings shape
    so a system-Python invocation without PyYAML still resolves rows."""
    try:
        import yaml  # type: ignore[import-untyped]

        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ManifestError(
                "principle-manifest root must be a mapping"
            )
        return data
    except ModuleNotFoundError:
        return _fallback_parse(text)


def _fallback_parse(text: str) -> dict:
    """Minimal parser for the manifest's section -> list-of-mappings
    shape. Handles the `key: value` + `- key: value` + folded `>-`
    scalar forms this file uses. Not a general YAML parser; scoped to
    this artefact so the reader degrades gracefully without PyYAML.
    """
    sections: dict[str, list[dict]] = {}
    current_section: str | None = None
    current_row: dict | None = None
    pending_fold_key: str | None = None
    fold_lines: list[str] = []

    def _flush_fold(row: dict | None) -> None:
        nonlocal pending_fold_key, fold_lines
        if row is not None and pending_fold_key is not None:
            row[pending_fold_key] = " ".join(
                s.strip() for s in fold_lines if s.strip()
            )
        pending_fold_key = None
        fold_lines = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            # Inside a fold, blank/comment lines end nothing; outside,
            # ignore.
            if pending_fold_key is not None and not stripped:
                continue
            continue
        indent = len(line) - len(line.lstrip(" "))

        # Continuation of a folded scalar (indented deeper than the key).
        if pending_fold_key is not None and indent >= 6 and not (
            stripped.startswith("- ") or re.match(r"^[a-z_]+:", stripped)
        ):
            fold_lines.append(stripped)
            continue
        else:
            _flush_fold(current_row)

        # Top-level section header `name:` with no value.
        m_section = re.match(r"^([a-z_]+):\s*$", line)
        if indent == 0 and m_section:
            current_section = m_section.group(1)
            sections[current_section] = []
            current_row = None
            continue

        # Top-level scalar (e.g. schema_version: 1) — ignore for rows.
        if indent == 0:
            continue

        # New list item.
        if stripped.startswith("- "):
            current_row = {}
            if current_section is not None:
                sections[current_section].append(current_row)
            stripped = stripped[2:].strip()

        # key: value within the current row.
        m_kv = re.match(r"^([a-z0-9_]+):\s*(.*)$", stripped)
        if m_kv and current_row is not None:
            key = m_kv.group(1)
            val = m_kv.group(2).strip()
            if val in (">-", ">", "|", "|-"):
                pending_fold_key = key
                fold_lines = []
            elif val in ("null", "~", ""):
                current_row[key] = None
            else:
                current_row[key] = val.strip().strip('"')
    _flush_fold(current_row)
    return sections  # type: ignore[return-value]


def _row_from_mapping(mapping: dict, section: str) -> PrincipleRow:
    """Build a PrincipleRow from a raw mapping; validate required keys."""
    required = ("id", "name", "enforcement", "mechanism", "f4_relationship")
    for key in required:
        if key not in mapping:
            raise ManifestError(
                f"principle-manifest row in {section!r} missing "
                f"required key {key!r}: {mapping!r}"
            )
    enforcement = str(mapping["enforcement"]).strip()
    if enforcement not in ENFORCEMENT_VALUES:
        raise ManifestError(
            f"principle-manifest row {mapping.get('id')!r} has unknown "
            f"enforcement {enforcement!r} (legal: "
            f"{sorted(ENFORCEMENT_VALUES)})"
        )
    mb = mapping.get("memory_basename")
    mb_val = None if mb in (None, "null", "") else str(mb).strip()
    doc = mapping.get("doc")
    doc_val = None if doc in (None, "null", "") else str(doc).strip()
    ac = mapping.get("ac")
    ac_val = None if ac in (None, "null", "") else str(ac).strip()
    return PrincipleRow(
        id=str(mapping["id"]).strip(),
        name=str(mapping["name"]).strip(),
        memory_basename=mb_val,
        doc=doc_val,
        enforcement=enforcement,
        mechanism=str(mapping["mechanism"]).strip(),
        f4_relationship=str(mapping["f4_relationship"]).strip(),
        ac=ac_val,
        section=section,
    )


def load_rows(repo_root: Path) -> list[PrincipleRow]:
    """Load every declared row from the principle-manifest.

    Reads ``<repo_root>/docs/design/principle-manifest.yaml`` and returns
    the union of the ``frame_rules``, ``principles``, and
    ``enforced_primitives`` blocks as typed rows. Raises ManifestError
    on a structurally invalid manifest.
    """
    manifest_path = repo_root / PRINCIPLE_MANIFEST_PATH
    text = manifest_path.read_text(encoding="utf-8")
    data = _load_yaml(text)
    rows: list[PrincipleRow] = []
    for section in ("frame_rules", "principles", "enforced_primitives"):
        block = data.get(section) or []
        if not isinstance(block, list):
            raise ManifestError(
                f"principle-manifest section {section!r} must be a list"
            )
        for mapping in block:
            if not isinstance(mapping, dict):
                raise ManifestError(
                    f"principle-manifest section {section!r} has a "
                    f"non-mapping entry: {mapping!r}"
                )
            rows.append(_row_from_mapping(mapping, section))
    return rows


def row_ids(rows: list[PrincipleRow]) -> set[str]:
    """The set of declared ids."""
    return {r.id for r in rows}


def memory_basenames(rows: list[PrincipleRow]) -> set[str]:
    """The set of non-null ``memory_basename`` values across ALL rows.

    Includes ``enforced_primitives`` provenance basenames. For the
    bidirectional coverage guard use ``coverage_basenames`` instead —
    only the declared-principle surface (``frame_rules`` +
    ``principles``) is bound by the manifest <-> map consistency
    contract; an ``enforced_primitives`` row names a corpus file as the
    PROVENANCE of the principle its check operationalises, which may be
    a newer feedback memory not yet in the derivation-map's 30-row
    table.
    """
    return {r.memory_basename for r in rows if r.memory_basename}


# The manifest sections whose ``memory_basename`` participates in the
# bidirectional manifest <-> derivation-map coverage contract. The
# derivation-map IS the F4/M5 table for the declared-principle corpus;
# the enforced-primitives section names mechanisms (provenance, not a
# corpus-principle claim) and is excluded.
COVERAGE_SCOPED_SECTIONS: frozenset[str] = frozenset(
    {"frame_rules", "principles"}
)


def coverage_basenames(rows: list[PrincipleRow]) -> set[str]:
    """The set of non-null ``memory_basename`` values on the declared-
    principle surface (``frame_rules`` + ``principles``) — the rows the
    bidirectional coverage guard binds to the derivation-map."""
    return {
        r.memory_basename
        for r in rows
        if r.memory_basename and r.section in COVERAGE_SCOPED_SECTIONS
    }


def derivation_map_basenames(repo_root: Path) -> set[str]:
    """Every ``feedback_*.md`` basename referenced by the derivation-map.

    The coverage guard uses this to assert that each manifest row whose
    ``memory_basename`` names a corpus file is consistent with the
    derivation-map (the map is the human-readable companion; a manifest
    memory_basename absent from the map is observable drift).
    """
    text = (repo_root / DERIVATION_MAP_PATH).read_text(encoding="utf-8")
    return set(re.findall(r"feedback_[a-z0-9_]+\.md", text))


def missing_required_ids(rows: list[PrincipleRow]) -> list[str]:
    """The required ids (FR.1/FR.2/FR.3 + M5) NOT present as rows."""
    have = row_ids(rows)
    needed = list(REQUIRED_FRAME_RULE_IDS) + [REQUIRED_M5_ID]
    return [rid for rid in needed if rid not in have]
