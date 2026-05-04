"""AC.PRSG.1 — component scaffold present.

The pr-safety sub-package exists with the expected directory shape,
pyproject.toml parses, and the CLI subcommand entry-point is
declared.
"""

from __future__ import annotations

from pathlib import Path

import tomllib


_ROOT = Path(__file__).resolve().parent.parent


def test_directory_layout() -> None:
    """src/, tests/ exist; pyproject.toml + README.md present.

    Seal-narrative sidecars land in the parent dev-sdlc plugin's
    seals/ directory (plugins/dev-sdlc/seals/SEAL_COMMIT.<slug>),
    not under pr-safety/seals/ — the dev-sdlc plugin is the
    sealed-component fence and its seals/ is the canonical
    narrative location.
    """
    assert (_ROOT / "pyproject.toml").exists()
    assert (_ROOT / "README.md").exists()
    assert (_ROOT / "src" / "loam_pr_safety" / "__init__.py").exists()
    assert (_ROOT / "tests").is_dir()
    # Parent plugin's seals dir is the canonical seal-narrative
    # location for this sub-tree.
    assert (_ROOT.parent / "seals").is_dir()


def test_pyproject_parses_and_declares_required_metadata() -> None:
    """pyproject.toml parses; declares name, version, requires-python."""
    pp_path = _ROOT / "pyproject.toml"
    data = tomllib.loads(pp_path.read_text(encoding="utf-8"))
    assert data["project"]["name"] == "loam-pr-safety"
    assert data["project"]["version"] == "0.1.0"
    assert data["project"]["requires-python"].startswith(">=3.")
    deps = data["project"]["dependencies"]
    for required in (
        "loam-cli",
        "loam-odd-extractor",
        "loam-per-project-pm",
        "loam-workspace-bootstrap",
    ):
        assert required in deps, (
            f"pyproject.toml missing required dep: {required}"
        )
    assert any(d.startswith("PyYAML") for d in deps)
    assert any(d.startswith("pydantic") for d in deps)


def test_cli_entry_point_declared() -> None:
    """`pr-safety` is registered under loam.cli.subcommands."""
    pp_path = _ROOT / "pyproject.toml"
    data = tomllib.loads(pp_path.read_text(encoding="utf-8"))
    eps = data["project"]["entry-points"]["loam.cli.subcommands"]
    assert eps["pr-safety"] == (
        "loam_pr_safety.cli:build_pr_safety_subcommand"
    )


def test_required_modules_present() -> None:
    """Every named module in plan-doc §3 exists under src/."""
    src = _ROOT / "src" / "loam_pr_safety"
    expected = {
        "__init__.py",
        "errors.py",
        "spec.py",
        "state.py",
        "profile.py",
        "contract.py",
        "diff.py",
        "classifier.py",
        "gate.py",
        "override.py",
        "audit.py",
        "cli.py",
    }
    actual = {p.name for p in src.iterdir() if p.suffix == ".py"}
    missing = expected - actual
    assert not missing, f"missing modules: {missing}"
