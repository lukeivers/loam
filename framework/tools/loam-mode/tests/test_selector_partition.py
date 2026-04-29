"""AC.F2 — selector reads the partition.

The selector returns ``always_loaded`` only for ``mode="user"`` and
``always_loaded ∪ dev_only`` for ``mode="dev"``. Tested against a
tiny fixture manifest so behaviour is independent of the real
workspace tree (per F's plan §12 test register).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_mode.manifest import load_manifest
from loam_mode.selector import select_corpus


def _write_fixture_manifest(tmp_path: Path) -> Path:
    """A tiny fixture: 3 always-loaded paths, 2 dev-only paths."""
    data = {
        "roots": ["src/", "docs/"],
        "audit_excludes": [],
        "always_loaded": [
            {"path": "CLAUDE.md"},
            {"path": "src/main.py"},
            {"path": "docs/help.md"},
        ],
        "dev_only": [
            {"path": "docs/dev.md"},
            {"path": "docs/methodology.md"},
        ],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


def test_AC_F2_selector_reads_partition(tmp_path: Path) -> None:
    """The selector returns ``always_loaded`` for user mode and
    ``always_loaded ∪ dev_only`` for dev mode."""
    manifest_path = _write_fixture_manifest(tmp_path)
    manifest = load_manifest(manifest_path)

    user_paths = select_corpus(manifest, tmp_path, "user")
    dev_paths = select_corpus(manifest, tmp_path, "dev")

    assert user_paths == sorted(
        ["CLAUDE.md", "src/main.py", "docs/help.md"]
    )
    assert dev_paths == sorted(
        [
            "CLAUDE.md",
            "src/main.py",
            "docs/help.md",
            "docs/dev.md",
            "docs/methodology.md",
        ]
    )


def test_AC_F2_selector_user_mode_excludes_dev_only(tmp_path: Path) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)
    manifest = load_manifest(manifest_path)
    user_paths = select_corpus(manifest, tmp_path, "user")
    assert "docs/dev.md" not in user_paths
    assert "docs/methodology.md" not in user_paths


def test_AC_F2_selector_dev_mode_is_strict_superset(tmp_path: Path) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)
    manifest = load_manifest(manifest_path)
    user_paths = set(select_corpus(manifest, tmp_path, "user"))
    dev_paths = set(select_corpus(manifest, tmp_path, "dev"))
    assert user_paths < dev_paths


def test_AC_F2_selector_rejects_invalid_mode(tmp_path: Path) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)
    manifest = load_manifest(manifest_path)
    with pytest.raises(ValueError, match="mode must be"):
        select_corpus(manifest, tmp_path, "bogus")  # type: ignore[arg-type]


def test_AC_F2_selector_handles_glob_entries(tmp_path: Path) -> None:
    """Selector resolves glob entries via the candidate-paths shape."""
    data = {
        "roots": ["src/"],
        "audit_excludes": [],
        "always_loaded": [{"glob": "src/**"}],
        "dev_only": [{"glob": "tools/**"}],
    }
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    manifest = load_manifest(p)
    candidates = [
        "src/main.py",
        "src/sub/util.py",
        "tools/loam/src/loam_cli/amend/cli.py",
    ]
    user = select_corpus(manifest, tmp_path, "user", candidate_paths=candidates)
    dev = select_corpus(manifest, tmp_path, "dev", candidate_paths=candidates)
    assert user == ["src/main.py", "src/sub/util.py"]
    assert dev == sorted(candidates)
