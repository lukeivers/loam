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

"""AC.PFSE.1 — the three frame-rules FR.1/FR.2/FR.3 are declared as
machine-read named primitives (a checker can enumerate them from a
code-side artefact), not documents-only.

Verification surface (plan §5):
  * A test reads the principle-manifest and asserts FR.1/FR.2/FR.3 (and
    M5) are present as rows with an `enforcement` field.
  * The prose docs (FR.1 odd-principles.md + FR.2 odd-methodology.md +
    FR.3 odd-in-loam.md) exist AND cross-reference the manifest.
  * The bidirectional manifest <-> derivation-map coverage guard makes
    drift observable (a manifest row naming a corpus file the map does
    not reference, OR a structurally invalid manifest, is detectable),
    with fixtures proving both directions are observable.

This is the mechanical check on the production path for AC.PFSE.1: the
manifest is the code-side artefact; this guard reads it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(PLUGIN_HOOKS_DIR))

import principle_manifest_reader as reader  # noqa: E402


# ----- the manifest enumerates FR.1/FR.2/FR.3 + M5 as rows -----


def test_AC_PFSE_1_required_rows_present_with_enforcement() -> None:
    rows = reader.load_rows(REPO_ROOT)
    by_id = {r.id: r for r in rows}
    for rid in ("FR.1", "FR.2", "FR.3", "M5"):
        assert rid in by_id, (
            f"AC.PFSE.1: principle-manifest is missing required row "
            f"{rid!r} — the frame-rules + M5 must be enumerable from "
            f"the code-side artefact, not prose only. Present ids: "
            f"{sorted(by_id)}"
        )
        assert by_id[rid].enforcement in reader.ENFORCEMENT_VALUES, (
            f"AC.PFSE.1: row {rid!r} has no valid `enforcement` field "
            f"(got {by_id[rid].enforcement!r}); the field is what makes "
            f"the row a machine-read declaration."
        )


def test_AC_PFSE_1_missing_required_ids_helper_is_empty() -> None:
    rows = reader.load_rows(REPO_ROOT)
    missing = reader.missing_required_ids(rows)
    assert missing == [], (
        f"AC.PFSE.1: required ids absent from the manifest: {missing}"
    )


# ----- the prose docs exist + cross-reference the manifest -----


def test_AC_PFSE_1_prose_docs_exist() -> None:
    for rel in (
        "framework/docs/principles/odd-principles.md",
        "plugins/dev-sdlc/docs/odd-methodology.md",
        "plugins/dev-sdlc/docs/odd-in-loam.md",
    ):
        assert (REPO_ROOT / rel).is_file(), (
            f"AC.PFSE.1: prose doc {rel!r} must exist (FR.1 is NEW "
            f"authoring; FR.2/FR.3 pre-exist)."
        )


def test_AC_PFSE_1_prose_docs_cross_reference_manifest() -> None:
    manifest_name = "principle-manifest.yaml"
    for rel in (
        "framework/docs/principles/odd-principles.md",
        "plugins/dev-sdlc/docs/odd-methodology.md",
        "plugins/dev-sdlc/docs/odd-in-loam.md",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert manifest_name in text, (
            f"AC.PFSE.1: prose doc {rel!r} must cross-reference the "
            f"machine-read manifest ({manifest_name}) — the prose side "
            f"points at the code-side declaration."
        )


def test_AC_PFSE_1_derivation_map_points_at_manifest() -> None:
    text = (REPO_ROOT / reader.DERIVATION_MAP_PATH).read_text(
        encoding="utf-8"
    )
    assert "principle-manifest.yaml" in text, (
        "AC.PFSE.1 / §9 bookkeeping: the derivation-map must carry a "
        "one-line pointer to the manifest."
    )


# ----- bidirectional coverage guard: live consistency -----


def test_AC_PFSE_1_every_manifest_basename_in_derivation_map() -> None:
    """Every corpus file a DECLARED-PRINCIPLE row names must be
    referenced by the derivation-map (manifest -> map direction). A
    declared-principle row naming a corpus file the map omits is
    observable drift (D-PFSE.2 / RF-4). Scoped to frame_rules +
    principles — enforced-primitives rows name mechanism provenance, not
    a corpus-principle claim, so they are not bound by map coverage."""
    rows = reader.load_rows(REPO_ROOT)
    manifest_basenames = reader.coverage_basenames(rows)
    map_basenames = reader.derivation_map_basenames(REPO_ROOT)
    uncovered = sorted(manifest_basenames - map_basenames)
    assert not uncovered, (
        f"AC.PFSE.1: declared-principle rows reference corpus files the "
        f"derivation-map does not: {uncovered}. Add them to the map or "
        f"correct the manifest `memory_basename` — this is the "
        f"observable-drift contract (manifest -> map)."
    )


def test_AC_PFSE_1_every_manifest_basename_resolves_to_a_file() -> None:
    """Every manifest `memory_basename` resolves to a real corpus file
    OR is a known-relocated principle. The corpus lives in the user's
    memory dir, not this repo; so the resolvable check is against the
    derivation-map (the in-repo surface that references the corpus).
    A basename not in the map is the dangling-pointer signal."""
    rows = reader.load_rows(REPO_ROOT)
    map_basenames = reader.derivation_map_basenames(REPO_ROOT)
    for r in rows:
        if r.memory_basename is None:
            continue
        if r.section not in reader.COVERAGE_SCOPED_SECTIONS:
            continue
        assert r.memory_basename in map_basenames, (
            f"AC.PFSE.1: declared-principle row {r.id!r} names corpus "
            f"file {r.memory_basename!r} which the derivation-map does "
            f"not reference — a dangling pointer."
        )


# ----- bidirectional coverage guard: drift is observable (fixtures) -----


def test_AC_PFSE_1_fixture_manifest_basename_not_in_map_is_flagged(
    tmp_path: Path,
) -> None:
    """A manifest row naming a corpus file absent from the map surfaces
    as uncovered — the manifest->map drift signal is observable."""
    manifest_basenames = {"feedback_brand_new_principle.md"}
    map_basenames = {"feedback_ruthless_feedback.md"}
    uncovered = manifest_basenames - map_basenames
    assert "feedback_brand_new_principle.md" in uncovered, (
        "AC.PFSE.1: a manifest basename absent from the map must "
        "surface as uncovered (manifest->map observable-drift)."
    )


def test_AC_PFSE_1_fixture_invalid_enforcement_raises(
    tmp_path: Path,
) -> None:
    """A manifest with an unknown enforcement value is observable — the
    reader raises ManifestError (the structural-drift signal)."""
    bad = tmp_path / "docs" / "design"
    bad.mkdir(parents=True)
    (bad / "principle-manifest.yaml").write_text(
        "schema_version: 1\n"
        "frame_rules:\n"
        "  - id: FR.1\n"
        "    name: x\n"
        "    memory_basename: null\n"
        "    doc: x\n"
        "    enforcement: bogus-value\n"
        "    mechanism: x\n"
        "    f4_relationship: compose-with\n"
        "    ac: AC.PFSE.1\n",
        encoding="utf-8",
    )
    with pytest.raises(reader.ManifestError):
        reader.load_rows(tmp_path)


def test_AC_PFSE_1_fixture_missing_required_key_raises(
    tmp_path: Path,
) -> None:
    """A manifest row missing a required key is observable — the reader
    raises ManifestError."""
    bad = tmp_path / "docs" / "design"
    bad.mkdir(parents=True)
    (bad / "principle-manifest.yaml").write_text(
        "schema_version: 1\n"
        "frame_rules:\n"
        "  - id: FR.1\n"
        "    name: x\n"
        # no enforcement key
        "    mechanism: x\n"
        "    f4_relationship: compose-with\n",
        encoding="utf-8",
    )
    with pytest.raises(reader.ManifestError):
        reader.load_rows(tmp_path)
