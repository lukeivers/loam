"""AC.F5 — partition is auditable.

The ``loam-mode audit`` CLI walks the workspace tree under
``manifest.roots`` (with ``manifest.audit_excludes`` subtracted) and
reports orphans (files in neither set), overlap (files in both sets),
and cross-mode references. Exit non-zero if any of those are present.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_mode.audit import audit_partition
from loam_mode.cli import main as cli_main
from loam_mode.manifest import load_manifest


def _write_clean_fixture(root: Path) -> Path:
    """Build a clean fixture: every workspace path is classified."""
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("# main\n", encoding="utf-8")
    (root / "src" / "util.py").write_text("# util\n", encoding="utf-8")
    (root / "tools").mkdir()
    (root / "tools" / "dev_cli.py").write_text("# cli\n", encoding="utf-8")
    (root / "README.md").write_text("# Readme\n", encoding="utf-8")
    data = {
        "roots": ["src/", "tools/", "README.md"],
        "audit_excludes": [],
        "always_loaded": [
            {"glob": "src/**"},
            {"path": "README.md"},
        ],
        "dev_only": [{"glob": "tools/**"}],
    }
    p = root / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


def _write_dirty_fixture(root: Path) -> Path:
    """Build a dirty fixture: an orphan file under a declared root."""
    p = _write_clean_fixture(root)
    (root / "src" / "orphan.txt").write_text("\n", encoding="utf-8")
    # Adjust manifest so .py files are classified but .txt isn't.
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    data["always_loaded"] = [
        {"glob": "src/*.py"},  # only .py
        {"path": "README.md"},
    ]
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


def test_AC_F5_audit_clean_fixture_exits_zero(tmp_path: Path) -> None:
    """A fixture with no orphans / overlap / cross-mode refs reports
    clean and exits 0 from the CLI."""
    manifest_path = _write_clean_fixture(tmp_path)
    manifest = load_manifest(manifest_path)
    report = audit_partition(manifest, tmp_path)
    assert report.is_clean
    assert report.orphans == []
    assert report.overlap == []
    assert report.cross_mode_refs == []

    rc = cli_main(
        [
            "audit",
            "--workspace",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
        ]
    )
    assert rc == 0


def test_AC_F5_audit_finds_orphans(tmp_path: Path) -> None:
    """A fixture with an unclassified path under a declared root
    reports an orphan and exits non-zero."""
    manifest_path = _write_dirty_fixture(tmp_path)
    manifest = load_manifest(manifest_path)
    report = audit_partition(manifest, tmp_path)
    assert not report.is_clean
    assert "src/orphan.txt" in report.orphans

    rc = cli_main(
        [
            "audit",
            "--workspace",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
        ]
    )
    assert rc != 0


def test_AC_F5_audit_finds_overlap(tmp_path: Path) -> None:
    """A fixture where a path appears in both sets reports overlap
    and exits non-zero."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("\n", encoding="utf-8")
    data = {
        "roots": ["src/"],
        "audit_excludes": [],
        "always_loaded": [{"glob": "src/**"}],
        "dev_only": [{"path": "src/main.py"}],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    manifest = load_manifest(p)
    report = audit_partition(manifest, tmp_path)
    assert not report.is_clean
    assert "src/main.py" in report.overlap


def test_AC_F5_audit_excludes_apply(tmp_path: Path) -> None:
    """``audit_excludes`` patterns prevent paths from appearing as
    orphans."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("\n", encoding="utf-8")
    (tmp_path / "src" / "ignore.tmp").write_text("\n", encoding="utf-8")
    data = {
        "roots": ["src/"],
        "audit_excludes": ["**/*.tmp"],
        "always_loaded": [{"glob": "src/**"}],
        "dev_only": [],
    }
    p = tmp_path / "manifest.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    manifest = load_manifest(p)
    report = audit_partition(manifest, tmp_path)
    assert report.is_clean
    assert "src/ignore.tmp" not in report.orphans


def test_AC_F5_real_manifest_audit_runs(real_manifest_path: Path, repo_root: Path) -> None:
    """The shipped manifest audits without crashing.

    This test does NOT assert clean — orphans + cross-mode refs are
    handled by the dedicated AC tests; this one just exercises the
    audit on the real workspace."""
    manifest = load_manifest(real_manifest_path)
    report = audit_partition(manifest, repo_root)
    # Diagnostic always renders.
    text = report.format_diagnostic()
    assert isinstance(text, str)
    assert text.strip() != ""


def test_AC_F5_cli_select_subcommand(tmp_path: Path) -> None:
    """The ``select`` subcommand prints the corpus for a mode."""
    manifest_path = _write_clean_fixture(tmp_path)

    rc = cli_main(
        [
            "select",
            "--workspace",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
            "user",
        ]
    )
    assert rc == 0
