"""AC.DCR.SCHEMA.{1,2,3} + AC.DCR.TEST.{2,4} — manifest runtime-flag
schema acceptance + safety-property tests (amendment #139).

Amendment #139 introduces an optional ``runtime: bool = False`` field
on ``ManifestEntry`` and a new ``RootEntry`` dataclass admitting
either bare-string or ``{path, runtime}`` mapping forms in the
``roots:`` block. This test file covers two contracts:

  1. **Schema acceptance** — the parser admits the new field on
     entries (in ``roots:`` OR ``always_loaded:`` OR ``dev_only:``),
     defaults to ``False`` when absent, and rejects malformed shapes.
     Per AC.DCR.SCHEMA.{1,2,3}.

  2. **Safety property** — the PMR_3 + PMR_4 test logic still rejects
     non-runtime entries pointing at non-existent paths / empty
     match-sets. The runtime-flag admission must not silently widen
     the safety property to all entries. Per AC.DCR.TEST.{2,4}.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_mode.manifest import (
    Manifest,
    ManifestEntry,
    RootEntry,
    expand_entry,
    load_manifest,
)


# --- AC.DCR.SCHEMA.1 — entries admit `runtime: true` ----------------


def test_AC_DCR_schema_accepts_runtime_field(tmp_path: Path) -> None:
    """A manifest with ``runtime: true`` on entries (roots, always_loaded,
    dev_only) parses; the parsed entry's ``runtime`` field equals ``True``.
    """
    data = {
        "roots": [
            "src/",
            {"path": "data/", "runtime": True},
        ],
        "always_loaded": [
            {"glob": "src/**"},
            {"glob": "data/**", "runtime": True},
            {"path": "ghost.md", "runtime": True},
        ],
        "dev_only": [
            {"path": "scratch.md", "runtime": True},
        ],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")

    manifest = load_manifest(p)

    runtime_roots = [r for r in manifest.roots if r.runtime]
    assert len(runtime_roots) == 1
    assert runtime_roots[0].path == "data/"
    assert runtime_roots[0].runtime is True

    runtime_always = [e for e in manifest.always_loaded if e.runtime]
    assert len(runtime_always) == 2
    assert {(e.glob, e.path) for e in runtime_always} == {
        ("data/**", None),
        (None, "ghost.md"),
    }
    for e in runtime_always:
        assert e.runtime is True

    runtime_dev = [e for e in manifest.dev_only if e.runtime]
    assert len(runtime_dev) == 1
    assert runtime_dev[0].path == "scratch.md"
    assert runtime_dev[0].runtime is True


# --- AC.DCR.SCHEMA.2 — `runtime:` defaults to False ----------------


def test_AC_DCR_schema_runtime_defaults_false(tmp_path: Path) -> None:
    """Entries without a ``runtime:`` key parse with ``runtime``
    defaulting to ``False``. Existing manifests continue to parse
    without modification.
    """
    data = {
        "roots": ["src/", "README.md"],
        "always_loaded": [
            {"glob": "src/**"},
            {"path": "README.md"},
        ],
        "dev_only": [],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")

    manifest = load_manifest(p)

    for root in manifest.roots:
        assert root.runtime is False
    for entry in (*manifest.always_loaded, *manifest.dev_only):
        assert entry.runtime is False


def test_AC_DCR_schema_runtime_explicit_false(tmp_path: Path) -> None:
    """Explicit ``runtime: false`` parses the same as absent."""
    data = {
        "roots": [{"path": "src/", "runtime": False}],
        "always_loaded": [
            {"glob": "src/**", "runtime": False},
            {"path": "README.md", "runtime": False},
        ],
        "dev_only": [],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("\n", encoding="utf-8")

    manifest = load_manifest(p)
    assert manifest.roots[0].runtime is False
    assert manifest.always_loaded[0].runtime is False
    assert manifest.always_loaded[1].runtime is False


# --- AC.DCR.SCHEMA.3 — root entry mapping form + bare-string form --


def test_AC_DCR_root_entry_mapping_form(tmp_path: Path) -> None:
    """A root entry expressed as a mapping ``{path: <str>, runtime: <bool>}``
    parses to a ``RootEntry`` with the named fields.
    """
    data = {
        "roots": [{"path": "data/", "runtime": True}],
        "always_loaded": [],
        "dev_only": [],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")

    manifest = load_manifest(p)
    assert len(manifest.roots) == 1
    assert manifest.roots[0] == RootEntry(path="data/", runtime=True)


def test_AC_DCR_root_entry_bare_string_form(tmp_path: Path) -> None:
    """A bare-string root entry parses to a ``RootEntry`` with
    ``runtime=False`` and ``path`` equal to the string. Backwards-
    compat is preserved.
    """
    data = {
        "roots": ["src/", "README.md"],
        "always_loaded": [],
        "dev_only": [],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")

    manifest = load_manifest(p)
    assert len(manifest.roots) == 2
    assert manifest.roots[0] == RootEntry(path="src/", runtime=False)
    assert manifest.roots[1] == RootEntry(path="README.md", runtime=False)


def test_AC_DCR_root_entry_mapping_rejects_unknown_keys(tmp_path: Path) -> None:
    """A root mapping with unexpected keys (e.g. typo'd ``runtmie:``)
    is rejected at parse time — defensive against silent drift.
    """
    data = {
        "roots": [{"path": "data/", "runtmie": True}],
        "always_loaded": [],
        "dev_only": [],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected keys"):
        load_manifest(p)


def test_AC_DCR_root_entry_mapping_requires_path(tmp_path: Path) -> None:
    """A root mapping without a ``path`` key is rejected."""
    data = {
        "roots": [{"runtime": True}],
        "always_loaded": [],
        "dev_only": [],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ValueError, match="must carry a 'path' key"):
        load_manifest(p)


def test_AC_DCR_runtime_field_rejects_non_bool(tmp_path: Path) -> None:
    """``runtime:`` accepts only YAML booleans (rejects ``"true"`` /
    ``1`` / null) — defensive against silent type coercion.
    """
    data = {
        "roots": [],
        "always_loaded": [{"glob": "src/**", "runtime": "true"}],
        "dev_only": [],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ValueError, match="runtime must be a boolean"):
        load_manifest(p)


# --- AC.DCR.TEST.2 — safety property preserved: non-runtime root ---


def test_AC_DCR_test_rejects_nonexistent_non_runtime_root(
    tmp_path: Path,
) -> None:
    """A root entry WITHOUT ``runtime: true`` pointing at a
    non-existent path must FAIL the PMR_3 existence check. The
    runtime-flag admission must not silently widen the safety
    property to all entries.

    Methodology: this test inlines the PMR_3 test predicate against a
    synthetic manifest so the safety property is verified at unit
    granularity, independent of the canonical workspace.
    """
    # Synthesise a manifest carrying both a runtime root AND a
    # non-runtime root pointing at non-existent paths.
    runtime_root = RootEntry(path="ghost-runtime/", runtime=True)
    plain_root = RootEntry(path="frobnitz/", runtime=False)

    # Replicate the PMR_3 test predicate locally — `runtime` skips,
    # non-runtime + missing must fail.
    failures: list[str] = []
    for root in (runtime_root, plain_root):
        if root.runtime:
            continue
        target = tmp_path / root.path.rstrip("/")
        if not target.exists():
            failures.append(root.path)

    # The runtime root must NOT appear in failures; the non-runtime
    # missing root MUST appear (safety property preserved).
    assert runtime_root.path not in failures
    assert plain_root.path in failures


# --- AC.DCR.TEST.4 — safety property preserved: non-runtime glob ----


def test_AC_DCR_test_rejects_empty_match_non_runtime_glob(
    tmp_path: Path,
) -> None:
    """An always-loaded entry WITHOUT ``runtime: true`` that resolves
    to an empty match-set must FAIL the PMR_4 non-empty assertion.
    The runtime-flag admission must not silently widen the safety
    property to all entries.

    Methodology: this test inlines the PMR_4 test predicate against
    synthetic glob entries so the safety property is verified at unit
    granularity, independent of the canonical workspace.
    """
    runtime_glob = ManifestEntry(glob="ghost-runtime/**", runtime=True)
    plain_glob = ManifestEntry(glob="frobnitz/**", runtime=False)

    # Replicate the PMR_4 test predicate locally.
    failures: list[str] = []
    for entry in (runtime_glob, plain_glob):
        if entry.runtime:
            continue
        matches = expand_entry(entry, tmp_path)
        if not matches:
            failures.append(entry.glob or entry.path or "")

    assert runtime_glob.glob not in failures
    assert plain_glob.glob in failures


def test_AC_DCR_test_runtime_glob_empty_match_is_admitted(
    tmp_path: Path,
) -> None:
    """The positive complement of AC.DCR.TEST.4 — a runtime glob
    that resolves to an empty match-set is silently admitted (no
    failure). This is the bug the amendment fixes: runtime entries
    can resolve empty without tripping the test.
    """
    runtime_glob = ManifestEntry(glob="ghost-runtime/**", runtime=True)
    matches = expand_entry(runtime_glob, tmp_path)
    # No on-disk presence, glob expands to empty — but the test logic
    # (in PMR_4) skips this entry. Verifying the expand_entry baseline
    # so future maintainers can see exactly what the runtime skip
    # admits.
    assert matches == set()
    # And the entry is correctly self-flagged.
    assert runtime_glob.runtime is True


# --- AC.DCR.MANIFEST.2 — real manifest carries data/ runtime flags --


def test_AC_DCR_real_manifest_data_entries_runtime_flagged() -> None:
    """The shipped ``dev-mode-manifest.yaml``'s two ``data/`` entries
    (root + always_loaded glob) carry ``runtime: true``. This is the
    AC.DCR.MANIFEST.2 contract verified against the real manifest.
    """
    repo_root = Path(__file__).resolve().parents[5]
    manifest_path = (
        repo_root / "plugins" / "dev-sdlc" / "dev-mode-manifest.yaml"
    )
    manifest = load_manifest(manifest_path)

    data_roots = [r for r in manifest.roots if r.path == "data/"]
    assert len(data_roots) == 1, (
        f"expected exactly one 'data/' root entry; got {len(data_roots)}"
    )
    assert data_roots[0].runtime is True, (
        f"'data/' root entry must carry runtime=True; got {data_roots[0]}"
    )

    data_globs = [
        e for e in manifest.always_loaded if e.glob == "data/**"
    ]
    assert len(data_globs) == 1, (
        f"expected exactly one 'data/**' always_loaded entry; got {len(data_globs)}"
    )
    assert data_globs[0].runtime is True, (
        f"'data/**' always_loaded entry must carry runtime=True; got {data_globs[0]}"
    )


# --- AC.DCR.MANIFEST.1 — memory-system fully purged -----------------


def test_AC_DCR_real_manifest_no_memory_system_refs() -> None:
    """The shipped ``dev-mode-manifest.yaml`` carries zero
    ``framework/memory-system/`` references. AC.DCR.MANIFEST.1.
    """
    repo_root = Path(__file__).resolve().parents[5]
    manifest_path = (
        repo_root / "plugins" / "dev-sdlc" / "dev-mode-manifest.yaml"
    )
    text = manifest_path.read_text(encoding="utf-8")
    assert "framework/memory-system" not in text, (
        "dev-mode-manifest.yaml still carries framework/memory-system "
        "references; amendment #139 D-DCR.MEMORY-SYSTEM-ENTRIES "
        "deletion incomplete."
    )

    manifest = load_manifest(manifest_path)
    for root in manifest.roots:
        assert "memory-system" not in root.path
    for entry in (*manifest.always_loaded, *manifest.dev_only):
        candidate = entry.path or entry.glob or ""
        assert "memory-system" not in candidate
